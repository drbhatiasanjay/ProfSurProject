"""LLM adapters for Phase 6 AI Financial Assistant.

Two backends: Ollama (local, zero-egress, default in dev) and Anthropic
(Claude Haiku 4.5, default in Cloud Run prod). Both expose a generator
yielding string chunks compatible with st.write_stream().

Context builders produce <=900 token grounded prompts — no hallucination
surface. CFO mode injects company + peer metrics; Researcher mode injects
panel OLS outputs + descriptive statistics.
"""
from __future__ import annotations

import json
import re
import os
from typing import Iterator, Literal, Optional

import pandas as pd

import db

# tiktoken for token counting; fall back to a rough char/4 heuristic if not installed
try:
    import tiktoken
    _ENC = tiktoken.get_encoding("cl100k_base")

    def count_tokens(text: str) -> int:
        return len(_ENC.encode(text))
except ImportError:
    def count_tokens(text: str) -> int:  # type: ignore[misc]
        return max(1, len(text) // 4)


_PANEL_DISPLAY_LABELS = {
    "run3":      "(2001-25)_April26",
    "thesis":    "Thesis (2001-2024)",
    "latest":    "Latest (2001-2025)",
    "cmie_2025": "CMIE 2025",
    "us_av_2024": "US S&P Sample",
}

def _grounding_footer(panel_label: str) -> str:
    return (
        "\n\nINSTRUCTIONS: Answer ONLY from the three knowledge blocks above.\n"
        "For every factual claim or interpretive point, append a citation in brackets "
        "using one of these three tags:\n"
        f"  [Source: Theory] — for theory, methodology, Dickinson classification, hypotheses\n"
        f"  [Source: {panel_label}] — for panel statistics, stage means, company KPIs, peer metrics\n"
        f"  [Source: OLS Model] — for regression coefficients, R², model outputs\n"
        "If asked about something not in the context, say exactly: "
        "'This data is not available in my current context.'\n"
        "Never fabricate numbers. Cite exact values from the context.\n"
        "For coefficient significance questions: always quote the exact coefficient "
        "AND the sample mean, then compute the marginal effect = coef × sample_mean."
    )

GROUNDING_FOOTER = _grounding_footer("DATA")

# ── Static thesis knowledge block (A) — injected into every context ───────────
# Covers: Dickinson life-stage classification, core theories, thesis scope,
# and directional hypotheses. Token cost ~160 tokens — well within 900 budget.
_THESIS_BLOCK = (
    "## [SOURCE: Theory] Theoretical & Methodological Framework\n"
    "**Life Stage Classification (Dickinson 2011) — cash-flow sign patterns:**\n"
    "- Startup: OCF−, ICF−, FCF+ → high external financing dependency, higher leverage expected\n"
    "- Growth: OCF+, ICF−, FCF− → heavy reinvestment, moderate-high leverage\n"
    "- Maturity: OCF+, ICF−, FCF− → internally self-funded, lower leverage expected\n"
    "- Shakeout (1/2/3): mixed OCF/ICF/FCF patterns → transitional instability\n"
    "- Decline: OCF−, ICF+ → disinvestment, leverage rises from distress\n"
    "- Decay: deeply negative OCF, ICF+ → severe deterioration, high distress risk\n\n"
    "**Theories & Hypothesised Directions:**\n"
    "- Pecking Order Theory (POT, Myers & Majluf 1984): firms prefer internal > debt > equity "
    "→ H: profitability ↑ = leverage ↓ (negative coef expected)\n"
    "- Trade-off Theory (ToT): balance tax shield vs distress costs "
    "→ H: tangibility ↑ = leverage ↑ (positive coef, collateral value)\n"
    "- Agency Theory (Jensen & Meckling 1976): debt disciplines free cash flow "
    "→ effect varies by life stage\n\n"
    "**Study scope:** Indian listed firms, multi-year panel. "
    "Dependent variable: leverage = Debt / Total Assets × 100.\n"
)

CONTEXT_BUDGET_TOKENS = 1500


def build_company_context(company_code: int, panel_mode: str = "thesis") -> str:
    """Build a token-bounded (<= 900 tokens) context string for a single company.

    Includes: latest 5-year KPIs, peer group benchmarks (same industry_group +
    life_stage + year), and delta vs peer median leverage. Uses raw SQL via
    db.get_connection() — never calls @st.cache_data functions so it's safe
    outside Streamlit (e.g. in pytest).

    Args:
        company_code: Integer company identifier (company_code column).
        panel_mode: One of 'thesis', 'latest', 'run3'. Passed to _vintage_predicate.

    Returns:
        Markdown string <= 900 tokens with GROUNDING_FOOTER appended.
    """
    try:
        conn = db.get_connection()
        vintage_sql, vintage_params = db._vintage_predicate(panel_mode)
        # 1. Company's last 5 years — JOIN companies for name + industry_group
        # (those columns live in companies table, not financials)
        company_sql = f"""
            SELECT c.company_name, c.industry_group, f.life_stage, f.size_decile, f.year,
                   f.leverage, f.profitability, f.tangibility, f.firm_size
            FROM financials f
            JOIN companies c ON c.company_code = f.company_code
            WHERE f.company_code = ? AND {vintage_sql}
            ORDER BY f.year DESC LIMIT 5
        """
        company_df = pd.read_sql_query(
            company_sql, conn, params=[company_code] + vintage_params
        )
        if company_df.empty:
            return (
                f"## COMPANY (code={company_code})\n"
                f"No rows found in panel_mode={panel_mode}."
                f"{GROUNDING_FOOTER}"
            )
        latest = company_df.iloc[0]
        # 2. Peers in same industry_group + life_stage, latest year
        # industry_group is in companies table — use subquery join
        peer_sql = f"""
            SELECT f.leverage, f.profitability
            FROM financials f
            JOIN companies c ON c.company_code = f.company_code
            WHERE c.industry_group = ? AND f.life_stage = ? AND f.year = ?
              AND f.company_code != ? AND {vintage_sql}
        """
        peer_df = pd.read_sql_query(
            peer_sql, conn,
            params=[latest["industry_group"], latest["life_stage"],
                    int(latest["year"]), int(company_code)] + vintage_params,
        )
        conn.close()
        # 3. Build markdown
        trend_csv = ", ".join(
            f"{int(r.year)}={float(r.leverage):.3f}"
            for r in company_df.sort_values("year").itertuples()
        )
        peer_n = len(peer_df)
        if peer_n:
            peer_mean_lev = float(peer_df["leverage"].mean())
            peer_med_lev = float(peer_df["leverage"].median())
            peer_mean_roa = float(peer_df["profitability"].mean())
            peer_med_roa = float(peer_df["profitability"].median())
        else:
            peer_mean_lev = peer_med_lev = peer_mean_roa = peer_med_roa = float("nan")
        delta_lev = float(latest["leverage"]) - peer_med_lev if peer_n else float("nan")
        panel_label = _PANEL_DISPLAY_LABELS.get(panel_mode, panel_mode)
        footer = _grounding_footer(panel_label)
        md = (
            _THESIS_BLOCK
            + f"## [SOURCE: {panel_label}] Company: {latest['company_name']} (code: {int(company_code)})\n"
            f"- Industry: {latest['industry_group']} | Life Stage: {latest['life_stage']} | Size Decile: {latest['size_decile']}\n"
            f"- Latest Year ({int(latest['year'])}): Leverage={float(latest['leverage']):.3f}, "
            f"Profitability={float(latest['profitability']):.3f}, "
            f"Tangibility={float(latest['tangibility']):.3f}, "
            f"FirmSize={float(latest['firm_size']):.3f}\n"
            f"- 5-Year Leverage Trend: {trend_csv}\n\n"
            f"## [SOURCE: {panel_label}] Peer Group ({peer_n} firms, same industry + life_stage, {int(latest['year'])})\n"
            f"- Peer Mean Leverage: {peer_mean_lev:.3f} | Peer Median: {peer_med_lev:.3f}\n"
            f"- Peer Mean Profitability: {peer_mean_roa:.3f} | Peer Median: {peer_med_roa:.3f}\n"
            f"- Company vs Peer Median (leverage delta): {delta_lev:+.3f}\n"
        )
        text = md + footer
        # Token-budget guard — drop trend line, then peer detail, if over budget
        if count_tokens(text) > CONTEXT_BUDGET_TOKENS:
            md_no_trend = re.sub(r"-\s*5-Year\s+Leverage\s+Trend:.*\n?", "", md, flags=re.IGNORECASE)
            text = md_no_trend + footer
        if count_tokens(text) > CONTEXT_BUDGET_TOKENS:
            parts = re.split(r"##\s*\[SOURCE:[^\]]*\]\s*Peer Group", md, flags=re.IGNORECASE)
            text = (parts[0].strip() + "\n\n" + footer) if parts else text
        return text
    except Exception as e:
        return f"Context unavailable: {type(e).__name__}: {e}{GROUNDING_FOOTER}"


def build_panel_context(panel_mode: str = "thesis") -> str:
    """Build a token-bounded (<= 900 tokens) panel-level context string.

    Includes: panel summary stats (firms, obs, year range), per-stage mean
    leverage, and OLS baseline coefficients from scenario_regression module.
    Uses raw SQL via db.get_connection() — never calls @st.cache_data functions.

    Args:
        panel_mode: One of 'thesis', 'latest', 'run3'.

    Returns:
        Markdown string <= 900 tokens with GROUNDING_FOOTER appended.
    """
    try:
        from models.scenario_regression import (
            compute_leverage_ols_coefs,
            leverage_predictor_sample_means,
            PREDICTORS,
        )
        conn = db.get_connection()
        vintage_sql, vintage_params = db._vintage_predicate(panel_mode)
        # Need predictor columns for OLS + life_stage + leverage for breakdown
        sql = f"""
            SELECT leverage, profitability, tangibility, tax, log_size,
                   tax_shield, dividend, life_stage, year, company_code
            FROM financials
            WHERE {vintage_sql}
        """
        df = pd.read_sql_query(sql, conn, params=vintage_params)
        # Industry leverage + tangibility breakdown (FIX-2) — keep conn open
        ind_sql = f"""
            SELECT c.industry_group,
                   AVG(f.leverage) AS avg_lev,
                   AVG(f.tangibility) AS avg_tang,
                   AVG(CASE WHEN f.year >= 2015 THEN f.leverage END) AS lev_post2015,
                   AVG(CASE WHEN f.year < 2015  THEN f.leverage END) AS lev_pre2015,
                   COUNT(DISTINCT f.company_code) AS n_firms
            FROM financials f
            JOIN companies c ON c.company_code = f.company_code
            WHERE {vintage_sql}
            GROUP BY c.industry_group
            HAVING n_firms >= 5
            ORDER BY avg_lev DESC
        """
        ind_df = pd.read_sql_query(ind_sql, conn, params=vintage_params)
        conn.close()
        panel_label = _PANEL_DISPLAY_LABELS.get(panel_mode, panel_mode)
        footer = _grounding_footer(panel_label)
        if df.empty:
            return f"## PANEL OVERVIEW (mode={panel_mode})\nNo rows.{footer}"
        # CRITICAL: compute stats from df directly — do NOT call db.get_db_metadata()
        # which has @st.cache_data and raises outside Streamlit (breaks pytest)
        total_firms = int(df["company_code"].nunique()) if "company_code" in df.columns else 0
        total_obs = len(df)
        year_min = int(df["year"].min()) if "year" in df.columns else 0
        year_max = int(df["year"].max()) if "year" in df.columns else 0
        coefs = compute_leverage_ols_coefs(df)
        means = leverage_predictor_sample_means(df)
        # leverage_predictor_sample_means uses abbreviated keys (prof, tang, dvnd)
        # while PREDICTORS uses full column names — map accordingly
        _means_key_map = {
            "profitability": "prof",
            "tangibility": "tang",
            "tax": "tax",
            "log_size": "log_size",
            "tax_shield": "tax_shield",
            "dividend": "dvnd",
        }
        # By-stage leverage means — use actual stage names from the DB
        stage_means = df.groupby("life_stage")["leverage"].mean().to_dict()
        order = ["Startup", "Growth", "Maturity", "Shakeout1", "Shakeout2", "Shakeout3", "Decline", "Decay"]
        present = [s for s in order if s in stage_means]
        stage_line = ", ".join(
            f"{s}={float(stage_means[s]):.3f}" for s in present
        )
        # Leverage distribution stats (FIX-3)
        lev = df["leverage"].dropna()
        lev_median = float(lev.median())
        lev_p90    = float(lev.quantile(0.90))
        lev_p99    = float(lev.quantile(0.99))
        lev_max    = float(lev.max())
        lev_over100 = int((lev > 100).sum())

        # Profitability distribution stats
        prof = df["profitability"].dropna()
        prof_mean   = float(prof.mean()) if len(prof) else 0.0
        prof_median = float(prof.median()) if len(prof) else 0.0
        prof_std    = float(prof.std()) if len(prof) else 0.0
        prof_p25    = float(prof.quantile(0.25)) if len(prof) else 0.0
        prof_p75    = float(prof.quantile(0.75)) if len(prof) else 0.0
        prof_p90    = float(prof.quantile(0.90)) if len(prof) else 0.0
        prof_min    = float(prof.min()) if len(prof) else 0.0
        prof_max    = float(prof.max()) if len(prof) else 0.0

        # Year-over-Year (YoY) Trajectory highlights
        yoy_df = (
            df.groupby("year")
            .agg(
                mean_prof=("profitability", "mean"),
                median_prof=("profitability", "median"),
            )
            .reset_index()
        )
        yoy_lines = ", ".join(
            f"{int(r.year)}: {r.mean_prof:.3f}/{r.median_prof:.3f}"
            for r in yoy_df.itertuples()
        )

        # Event-period leverage means (FIX-2a) — year-range buckets
        def _pm(mask):
            s = df.loc[mask, "leverage"].dropna()
            return float(s.mean()) if len(s) else float("nan")
        ep_pre    = _pm(df["year"] <= 2007)
        ep_gfc    = _pm(df["year"].between(2008, 2009))
        ep_mid    = _pm(df["year"].between(2010, 2015))
        ep_ibc    = _pm(df["year"].between(2016, 2019))
        ep_covid  = _pm(df["year"].between(2020, 2021))
        ep_post   = _pm(df["year"] >= 2022)

        # Industry block (FIX-2b) — top 6 by leverage, top 3 by tangibility
        ind_lev_top = (
            ind_df[["industry_group", "avg_lev", "lev_post2015", "lev_pre2015"]]
            .dropna(subset=["avg_lev"])
            .head(6)
        )
        ind_tang_top = (
            ind_df[["industry_group", "avg_tang"]]
            .dropna(subset=["avg_tang"])
            .sort_values("avg_tang", ascending=False)
            .head(3)
        )
        ind_lev_lines = "\n".join(
            f"  {r.industry_group}: avg={r.avg_lev:.1f}% "
            f"(post-2015={r.lev_post2015:.1f}%, pre-2015={r.lev_pre2015:.1f}%)"
            for r in ind_lev_top.itertuples()
        )
        ind_tang_lines = ", ".join(
            f"{r.industry_group} ({r.avg_tang:.2f})"
            for r in ind_tang_top.itertuples()
        )

        coef_lines = "\n".join(
            f"- {p}: coef={float(coefs.get(p, 0.0)):+.3f} (sample mean={float(means.get(_means_key_map.get(p, p), 0.0)):+.3f})"
            for p in PREDICTORS
        )
        md = (
            _THESIS_BLOCK
            + f"## [SOURCE: {panel_label}] Panel Statistics\n"
            f"- {total_firms} firms, "
            f"{total_obs} firm-year observations, "
            f"{year_min}-{year_max}\n"
            f"- Overall mean leverage: {float(df['leverage'].mean()):.3f}\n"
            f"- Leverage distribution: median={lev_median:.1f}%, p90={lev_p90:.1f}%, "
            f"p99={lev_p99:.1f}%, max={lev_max:.1f}% "
            f"({lev_over100} firm-years >100%, driven by negative-equity firms)\n"
            f"- Profitability (ROA) distribution: mean={prof_mean:.4f}, median={prof_median:.4f}, std={prof_std:.4f}, "
            f"p25={prof_p25:.4f}, p75={prof_p75:.4f}, p90={prof_p90:.4f}, min={prof_min:.4f}, max={prof_max:.4f}\n"
            f"- YoY Profitability Trajectory (mean/median): {yoy_lines}\n"
            f"- By Life Stage (mean leverage): {stage_line}\n\n"
            f"## [SOURCE: {panel_label}] Leverage by Event Period (panel mean %)\n"
            f"- Pre-GFC (2001-07): {ep_pre:.1f}% | GFC (2008-09): {ep_gfc:.1f}%"
            f" | Post-GFC (2010-15): {ep_mid:.1f}%\n"
            f"- Post-IBC (2016-19): {ep_ibc:.1f}% | COVID (2020-21): {ep_covid:.1f}%"
            f" | Post-COVID (2022+): {ep_post:.1f}%\n\n"
            f"## [SOURCE: {panel_label}] Industry Leverage (top 6 by avg, firms>=5)\n"
            f"{ind_lev_lines}\n"
            f"- Highest tangibility: {ind_tang_lines}\n\n"
            f"## [SOURCE: OLS Model] OLS Baseline (DV: leverage)\n"
            f"- intercept: {float(coefs.get('intercept', 0.0)):+.3f}\n"
            f"{coef_lines}\n"
            f"R²={float(coefs.get('r_squared', 0.0)):.3f}, N={int(coefs.get('n_obs', 0))}\n"
        )
        text = md + footer
        if count_tokens(text) > CONTEXT_BUDGET_TOKENS:
            short = "\n".join(
                f"- {p}: coef={float(coefs.get(p, 0.0)):+.3f}" for p in PREDICTORS
            )
            text = md.replace(coef_lines, short) + footer
        return text
    except Exception as e:
        return f"## PANEL OVERVIEW unavailable: {type(e).__name__}: {e}{GROUNDING_FOOTER}"


def classify_query(query: str) -> Literal["factual", "analytical", "hybrid"]:
    """Classify a user query intent to guide prompt engineering.

    Keyword-based heuristic: factual queries can be answered with lookup;
    analytical queries require interpretation. Hybrid (or neither) gets the
    full analytical treatment.

    Args:
        query: Raw user query string.

    Returns:
        One of 'factual', 'analytical', 'hybrid'.
    """
    q = query.lower()

    # Queries that need data + interpretation (always Sonnet)
    hybrid_triggers = [
        "compare", "contrast", "versus", " vs ", "between",
        "trends ", "trend between", "trend during", "trend in ",
        "diverge", "divergence", "post-ibc", "post ibc", "gfc", "covid",
        "driven by", "what drove", "why did", "correlat",
    ]
    if any(kw in q for kw in hybrid_triggers):
        return "hybrid"

    # Pure interpretation — no data lookup needed
    analytical_keywords = [
        "why", "explain", "analyze", "analyse", "interpret", "significance",
        "implication", "economic significance", "recommend", "should", "would",
        "suggest", "mechanism", "theory", "preferred over", "advantage of",
        "risk", "distress",  # risk/distress always need analytical interpretation
    ]

    # Lookup / counting / retrieval
    factual_keywords = [
        "what is", "how much", "what's the", "how many", "which ",
        "leverage of", "roa of", "value of", "show me", "list",
        "what year", "when did", "what years",
    ]

    has_factual = any(kw in q for kw in factual_keywords)
    has_analytical = any(kw in q for kw in analytical_keywords)

    if has_factual and not has_analytical:
        return "factual"
    if has_analytical:
        return "analytical"
    return "hybrid"


def generate_followup_suggestions(
    chat_history: list[dict],
    last_query: str,
    last_response: str,
    query_type: str,
    role: str = "researcher",
) -> list[str]:
    """Generate 3 context-aware follow-up questions via a separate Haiku call.

    Reads last 3 turns of chat_history to avoid repeating covered topics.
    Returns [] on any error — never crashes the chat.
    """
    try:
        import anthropic
    except ImportError:
        return []
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        try:
            import streamlit as st
            api_key = st.secrets.get("ANTHROPIC_API_KEY")
        except Exception:
            api_key = None
    if not api_key:
        return []

    recent = chat_history[-6:] if len(chat_history) > 6 else chat_history[:]
    history_text = "\n".join(
        f"{'User' if t['role'] == 'user' else 'AI'}: {t['content'][:200]}"
        for t in recent
        if t.get("content")
    )
    user_msg = (
        f"Recent conversation:\n{history_text}\n\n"
        f"Last question ({query_type}): {last_query}\n"
        f"Last response (first 300 chars): {last_response[:300]}"
    )
    system_msg = (
        "You are an expert financial economist. Generate exactly 3 follow-up questions "
        "to deepen a capital structure research conversation. Rules:\n"
        "- ONE factual: probe a specific number, stat, or comparison not yet discussed\n"
        "- ONE analytical: explore a theory, mechanism, or implication\n"
        "- ONE cross-cutting: connect to industry, time period, or peer firm dimension\n"
        "Output ONLY valid JSON, no prose, no markdown fences:\n"
        '{"followups": ["question 1?", "question 2?", "question 3?"]}'
    )
    try:
        client = anthropic.Anthropic(api_key=api_key)
        response = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=150,
            system=system_msg,
            messages=[{"role": "user", "content": user_msg}],
        )
        raw = response.content[0].text if response.content else ""
        try:
            parsed = json.loads(raw)
        except json.JSONDecodeError:
            m = re.search(r"\{.*\}", raw, re.DOTALL)
            parsed = json.loads(m.group()) if m else {}
        items = parsed.get("followups", [])
        if isinstance(items, list):
            return [str(q) for q in items[:3] if q]
        return []
    except Exception as _e:
        import logging as _logging
        _logging.warning("generate_followup_suggestions failed: %s: %s", type(_e).__name__, _e)
        return []


def stream_ollama(
    messages: list[dict],
    model: str = "llama3.1:8b",
) -> Iterator[str]:
    """Yield string chunks from Ollama streaming chat. Compatible with st.write_stream().

    CRITICAL: num_ctx default is 2048 — must override to 8192 for our
    ~1250-token prompts to leave room for response.

    Args:
        messages: List of {role, content} dicts (OpenAI message format).
        model: Ollama model tag (e.g. 'llama3.1:8b', 'finance-llama:8b').

    Yields:
        String chunks as they arrive from the model.
    """
    try:
        from ollama import chat as _ollama_chat
    except ImportError:
        yield "[Ollama backend not installed. Run: pip install ollama>=0.6.2]"
        return
    try:
        stream = _ollama_chat(
            model=model,
            messages=messages,
            stream=True,
            options={"num_ctx": 8192},
        )
        for chunk in stream:
            content = (
                (chunk.get("message", {}) or {}).get("content")
                if isinstance(chunk, dict)
                else getattr(chunk.message, "content", "")
            )
            if content:
                yield content
    except Exception as e:
        yield f"[Ollama error: {type(e).__name__}: {e}]"


def stream_anthropic(
    messages: list[dict],
    system: str = "",
    model: str = "claude-haiku-4-5-20251001",
    max_tokens: int = 1024,
    *,
    role: str = "viewer",
    citations: bool = False,
) -> Iterator[str]:
    """Yield string chunks from Anthropic streaming chat. Compatible with st.write_stream().

    Attempts prompt caching beta API first, falls back to standard API.
    API key resolution order: ANTHROPIC_API_KEY env var, then st.secrets.
    Streamlit is imported lazily inside this function (not at module level)
    so the module remains importable outside Streamlit (e.g. in pytest).

    Args:
        messages: List of {role, content} dicts.
        system: System prompt string.
        model: Anthropic model ID (default: claude-haiku-4-5-20251001).
        max_tokens: Maximum tokens in the response.
        role: User role for prompt engineering ('admin', 'researcher', 'viewer', 'cfo').
        citations: When True, append citations instruction to system prompt.

    Yields:
        String chunks as they arrive from the model.
    """
    try:
        import anthropic
    except ImportError:
        yield "[Anthropic backend not installed. Run: pip install anthropic>=0.25]"
        return
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        try:
            import streamlit as st  # safe inside function — not module-level
            api_key = st.secrets.get("ANTHROPIC_API_KEY")
        except Exception:
            api_key = None
    if not api_key:
        yield "[Anthropic backend not configured. Set ANTHROPIC_API_KEY in .streamlit/secrets.toml]"
        return
    try:
        client = anthropic.Anthropic(api_key=api_key)

        # Build effective system prompt with role preamble + citations instruction
        effective_system = system
        role_lower = role.lower()
        if role_lower in ("admin", "researcher"):
            role_preamble = (
                "You are an expert financial economist specialising in corporate capital structure. "
                "Respond with academic precision, use econometric terminology, and engage with theory rigorously."
            )
        else:  # CFO, viewer, or other
            role_preamble = (
                "You are a financial advisor providing clear, actionable insights to corporate executives. "
                "Use plain English, focus on practical recommendations, and avoid unnecessary jargon."
            )
        if effective_system:
            effective_system = role_preamble + "\n\n" + effective_system
        else:
            effective_system = role_preamble

        if citations:
            citations_instruction = (
                "\n\nSupport your analysis with relevant citations from capital structure literature "
                "(Modigliani & Miller 1958, Myers 1984, Rajan & Zingales 1995, Jensen & Meckling 1976, "
                "Fama & French 2002, IBC 2016). Format citations as Author (Year) inline."
            )
            effective_system += citations_instruction

        # Try prompt caching beta API first (may raise AttributeError if beta module not available).
        # Only fall back to the standard API if the beta stream fails before yielding anything —
        # otherwise a mid-stream beta failure would re-stream from the top and duplicate output.
        _yielded_any = False
        try:
            with client.beta.prompt_caching.messages.stream(
                model=model,
                max_tokens=max_tokens,
                system=[{"type": "text", "text": effective_system, "cache_control": {"type": "ephemeral"}}],
                messages=messages,
            ) as stream:
                for text in stream.text_stream:
                    _yielded_any = True
                    yield text
        except Exception:
            if _yielded_any:
                return
            # Fall back to standard API if prompt caching fails (beta not available, model mismatch, etc.)
            with client.messages.stream(
                model=model,
                max_tokens=max_tokens,
                system=effective_system,
                messages=messages,
            ) as stream:
                for text in stream.text_stream:
                    yield text
    except Exception as e:
        yield f"[Anthropic error: {type(e).__name__}: {e}]"


def stream_gemini_agent(
    messages: list[dict],
    system: str = "",
    model: str = "gemini-2.5-flash",
    max_tokens: int = 2048,
    *,
    role: str = "viewer",
    citations: bool = False,
    panel_mode: str = "thesis",
) -> Iterator[str | dict]:
    """Yield string chunks and structured action payloads (e.g. charts) from Google GenAI Agent.

    Equipped with Google ADK / GenAI tools:
    - query_financial_database (safe read-only SQL against capital_structure.db)
    - generate_chat_chart (interactive Plotly spec builder)
    - query_semantic_ontology (KG2 semantic ontology lookups)

    Args:
        messages: List of {role, content} dicts.
        system: System prompt string with grounded context.
        model: Gemini model ID (e.g. 'gemini-2.5-flash', 'gemini-2.5-pro').
        max_tokens: Maximum tokens in the output response.
        role: User role for prompt framing ('admin', 'researcher', 'viewer', 'cfo').
        citations: When True, append citations instruction to system prompt.
        panel_mode: Active panel dataset ('thesis', 'latest', 'run3', 'us_av_2024').

    Yields:
        String chunks and dict payloads (e.g. {"type": "chart", "spec": ...}).
    """
    try:
        from google import genai
        from google.genai import types
        from models.agent_tools import (
            query_financial_database,
            generate_chat_chart,
            query_semantic_ontology,
            get_database_schema_summary,
        )
    except ImportError as _imp_err:
        yield f"[Google GenAI SDK not installed. Run: pip install google-genai] Error: {_imp_err}"
        return

    api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        try:
            import streamlit as st
            api_key = st.secrets.get("GEMINI_API_KEY") or st.secrets.get("GOOGLE_API_KEY")
        except Exception:
            api_key = None

    if not api_key:
        yield "[Google Gemini backend not configured. Set GEMINI_API_KEY in .streamlit/secrets.toml]"
        return

    try:
        client = genai.Client(api_key=api_key)

        role_lower = role.lower()
        if role_lower in ("admin", "researcher"):
            role_preamble = (
                "You are an expert financial economist and autonomous data agent specialising in corporate capital structure. "
                "You have direct SQL access to the capital_structure.db database via the query_financial_database tool. "
                "Respond with econometric rigor and cite exact data."
            )
        else:
            role_preamble = (
                "You are an executive financial advisor and data agent providing actionable insights on capital structure. "
                "You have direct SQL access to the capital_structure.db database via the query_financial_database tool."
            )

        # Remove static-only context restrictions and grounding footers so the agent leverages its tools
        clean_context = re.sub(r"INSTRUCTIONS:\s*Answer ONLY from the three knowledge blocks above.*", "", system, flags=re.DOTALL).strip()
        clean_context = re.sub(r"If asked about something not in the context, say exactly:.*", "", clean_context, flags=re.DOTALL).strip()

        agent_instructions = (
            "AGENT INSTRUCTIONS:\n"
            "1. You are an autonomous financial econometric agent with tool access to the SQLite database (query_financial_database), interactive in-chat charting (generate_chat_chart), and semantic ontology (query_semantic_ontology).\n"
            "2. Whenever the user requests specific statistical metrics, distributions (median, standard deviation, percentiles, min, max), Year-over-Year (YoY) tables, or specific company metrics that are not fully detailed in the static context above, YOU MUST call query_financial_database to query capital_structure.db.\n"
            "3. When the user requests a chart, plot, graph, or visual representation, call query_financial_database if needed, and include the JSON chart specification block in your response:\n"
            "```json\n"
            '{\n  "chart_type": "line",\n  "title": "<Chart Title>",\n  "x_axis_label": "<X Axis>",\n  "y_axis_label": "<Y Axis>",\n  "categories": ["2001", "2002", "2003", ...],\n  "series": [\n    {"name": "<Series Name>", "values": [<val1>, <val2>, ...]}\n  ]\n}\n'
            "```\n"
            "or call generate_chat_chart, and accompany the chart with an insightful economic analysis.\n"
            "4. Cite sources using [Source: Theory], [Source: Latest (2001-2025)], or [Source: OLS Model] where appropriate.\n"
        )

        effective_system = f"{role_preamble}\n\n{clean_context}\n\n{get_database_schema_summary()}\n\n{agent_instructions}"
        if citations:
            effective_system += (
                "\n\nSupport your analysis with relevant citations from capital structure literature "
                "(Modigliani & Miller 1958, Myers 1984, Rajan & Zingales 1995, Jensen & Meckling 1976, "
                "Fama & French 2002, Dickinson 2011). Format citations as Author (Year) inline."
            )

        from models.agent_tools import (
            query_financial_database as _qfd,
            generate_chat_chart as _gcc,
            query_semantic_ontology as _qso,
        )

        def query_financial_database(sql_query: str) -> dict:
            """Execute a safe, read-only SQL SELECT query on the capital structure database.

            CRITICAL: ALWAYS use this tool whenever you need specific statistical aggregations
            (e.g. median, standard deviation, percentiles, min, max, count), company-specific records,
            or industry breakdowns that are not already present in the prompt context.

            Supported aggregate functions: AVG(x), COUNT(x), MIN(x), MAX(x), SUM(x), MEDIAN(x), STDEV(x), P25(x), P75(x), P90(x).

            Args:
                sql_query: A valid SQLite SELECT query against tables: financials, companies, cash_flows, econometric_results.
            """
            return _qfd(sql_query, panel_mode=panel_mode)

        def generate_chat_chart(
            chart_type: str,
            title: str,
            x_axis_label: str,
            y_axis_label: str,
            categories: list[str],
            series: list = None,
            series_json: str = "",
            **kwargs,
        ) -> dict:
            """Generate an interactive Plotly chart specification for in-chat rendering.

            Args:
                chart_type: One of 'line', 'bar', 'scatter', 'box', 'histogram'.
                title: Chart title.
                x_axis_label: X-axis label.
                y_axis_label: Y-axis label.
                categories: X-axis values as list of strings (e.g. ['2001', '2002', ...] or stage names).
                series: Optional list of series dicts (e.g. [{'name': 'Mean ROA', 'values': [0.16, 0.15]}]).
                series_json: Optional JSON string of series list. Example: '[{"name": "Mean ROA", "values": [0.16, 0.15]}]'
            """
            return _gcc(
                chart_type=chart_type,
                title=title,
                x_axis_label=x_axis_label,
                y_axis_label=y_axis_label,
                categories=categories,
                series=series,
                series_json=series_json,
                **kwargs,
            )

        def query_semantic_ontology(
            query_type: str,
            stage: str = "",
            metric: str = "",
        ) -> dict:
            """Look up normative leverage ranges, cash flow patterns, and anomaly explanations from the KG2 life-cycle ontology.

            Args:
                query_type: One of 'normative_band', 'stage_definition', 'explain_anomaly', 'macro_summary'.
                stage: Specific life stage (e.g. 'Startup', 'Growth', 'Maturity', 'Decline', 'Decay').
                metric: Financial metric name (e.g. 'leverage', 'profitability', 'tangibility').
            """
            return _qso(query_type=query_type, stage=stage, metric=metric)

        latest_user_prompt = messages[-1]["content"] if messages else ""
        if not latest_user_prompt:
            return

        chat = client.chats.create(
            model=model,
            config=types.GenerateContentConfig(
                system_instruction=effective_system,
                temperature=0.1,
                max_output_tokens=max_tokens,
                tools=[query_financial_database, generate_chat_chart, query_semantic_ontology],
            ),
        )

        response = chat.send_message(latest_user_prompt)

        tool_map = {
            "query_financial_database": query_financial_database,
            "generate_chat_chart": generate_chat_chart,
            "query_semantic_ontology": query_semantic_ontology,
        }

        has_yielded_text = False
        has_yielded_chart = False

        max_tool_turns = 5
        turn_count = 0
        while getattr(response, "function_calls", None) and turn_count < max_tool_turns:
            turn_count += 1
            function_responses = []
            for call in response.function_calls:
                fn_name = getattr(call, "name", "")
                fn_args = getattr(call, "args", {}) or {}
                if fn_name in tool_map:
                    tool_res = tool_map[fn_name](**fn_args)
                    if fn_name == "generate_chat_chart" and isinstance(tool_res, dict) and tool_res.get("status") == "success":
                        yield {"type": "chart", "spec": tool_res.get("chart_spec")}
                        has_yielded_chart = True
                    try:
                        function_responses.append(
                            types.Part.from_function_response(
                                name=fn_name,
                                response={"result": tool_res},
                            )
                        )
                    except Exception:
                        function_responses.append(str(tool_res))
            if function_responses:
                response = chat.send_message(function_responses[0] if len(function_responses) == 1 else function_responses)
            else:
                break

        def _extract_response_text(resp) -> str:
            if not resp:
                return ""
            parts_text = []
            for cand in (getattr(resp, "candidates", None) or []):
                content = getattr(cand, "content", None)
                for p in (getattr(content, "parts", None) or []):
                    t = getattr(p, "text", None)
                    if t:
                        parts_text.append(t)
            if parts_text:
                return "".join(parts_text)
            try:
                t = getattr(resp, "text", None)
                if t:
                    return t
            except Exception:
                pass
            return ""

        # Safely yield final text and extract embedded chart spec
        final_text = _extract_response_text(response)

        from models.agent_tools import extract_chat_chart_spec
        chart_spec, cleaned_final = extract_chat_chart_spec(final_text)
        if chart_spec and not has_yielded_chart:
            yield {"type": "chart", "spec": chart_spec}
            has_yielded_chart = True
            final_text = cleaned_final

        if final_text.strip():
            yield final_text
            has_yielded_text = True
        elif not has_yielded_text and has_yielded_chart:
            yield "Here is the interactive visualization based on the requested panel dataset."

    except Exception as e:
        yield f"[Gemini error: {type(e).__name__}: {e}]"



def generate_econometric_narrative(
    result: dict,
    model_type: str = "Pooled OLS",
    hausman: dict | None = None,
    panel_mode: str = "thesis",
    role: str = "viewer",
    citations: bool = False,
) -> "Iterator[str]":
    """Stream an AI interpretation of econometric regression results.

    Builds a ~600-token prompt from the coefficient table, diagnostic stats, and
    theoretical grounding. Uses claude-sonnet-4-6 for richer analytical output.
    Cached in SQLite ai_cache for 7 days (same regression = same response).

    Args:
        result: Dict from run_pooled_ols/run_fixed_effects/run_random_effects.
        model_type: Human label for the model specification.
        hausman: Optional Hausman test result dict.
        panel_mode: 'thesis' | 'latest' | 'run3'.
        role: User role for tone adaptation.
        citations: Whether to include academic citations.

    Yields:
        String chunks from the LLM.
    """
    import hashlib

    ct = result.get("coef_table")
    if ct is None:
        yield "[No coefficient table available for AI interpretation.]"
        return

    # Build markdown coefficient table
    rows = []
    for _, row in ct.iterrows():
        var = row.get("Variable", "")
        coef = row.get("Coefficient", "")
        se = row.get("Std Error", "")
        tstat = row.get("t-stat", row.get("t-value", ""))
        pval = row.get("p-value", "")
        sig = row.get("Sig", "")
        rows.append(f"| {var} | {coef:.4f} | {se:.4f} | {tstat:.3f} | {pval:.4f} | {sig} |" if all(
            isinstance(x, (int, float)) for x in [coef, se, pval]
        ) else f"| {var} | {coef} | {se} | {tstat} | {pval} | {sig} |")

    r2 = result.get("r_squared", "N/A")
    adj_r2 = result.get("adj_r_squared", "N/A")
    n_obs = result.get("n_obs", "N/A")
    f_stat = result.get("f_statistic", "N/A")
    f_pval = result.get("f_pvalue", "N/A")

    hausman_line = ""
    if hausman:
        hausman_line = (
            f"\n**Hausman test**: Chi²={hausman.get('chi2', 'N/A'):.2f}, "
            f"p={hausman.get('p_value', 'N/A'):.4f} — "
            f"{'Fixed Effects preferred' if hausman.get('p_value', 1) < 0.05 else 'Random Effects preferred'}"
        )

    coef_table_md = (
        "| Variable | Coef | SE | t | p | Sig |\n"
        "|---|---|---|---|---|---|\n"
        + "\n".join(rows)
    )

    prompt = (
        f"## Regression Results: {model_type} ({panel_mode} panel)\n\n"
        f"**Diagnostics**: R²={r2}, Adj-R²={adj_r2}, F={f_stat} (p={f_pval}), N={n_obs} obs{hausman_line}\n\n"
        f"{coef_table_md}\n\n"
        "**Task**: Interpret each statistically significant coefficient (p<0.05) in terms of capital structure theory "
        "(Pecking Order, Trade-off, Agency). Flag any sign violations vs theory. Assess model fit quality. "
        "Conclude with the most important policy implication for Indian listed firms.\n"
        "Be specific — quote exact coefficient values and p-values."
    )

    # Cache key
    cache_key = hashlib.sha256(prompt.encode()).hexdigest()
    ctx_key = hashlib.sha256(f"{model_type}:{panel_mode}".encode()).hexdigest()
    cached = db.ai_cache_get(cache_key, ctx_key, "claude-sonnet-4-6", ttl_hours=168)
    if cached:
        yield cached
        return

    full = ""
    for chunk in stream_anthropic(
        [{"role": "user", "content": prompt}],
        system=_THESIS_BLOCK,
        model="claude-sonnet-4-6",
        max_tokens=800,
        role=role,
        citations=citations,
    ):
        full += chunk
        yield chunk

    if full:
        db.ai_cache_set(cache_key, ctx_key, "claude-sonnet-4-6", full)


def generate_page_insights(
    page: str,
    data_summary: dict,
    filters: dict,
    role: str = "viewer",
    citations: bool = False,
) -> "Iterator[str]":
    """Stream AI insights for a specific dashboard page.

    Cached in SQLite ai_cache for 24 hours. Only fires when user clicks Generate.

    Args:
        page: Page identifier (e.g. 'dashboard', 'scenarios', 'ml', 'clustering').
        data_summary: Page-specific dict of computed stats to feed the AI.
        filters: Current sidebar filter state (for context).
        role: User role for tone adaptation.
        citations: Whether to include academic citations.

    Yields:
        String chunks from the LLM.
    """
    import hashlib
    import json as _json

    # Build prompt from data_summary
    summary_lines = "\n".join(f"- **{k}**: {v}" for k, v in data_summary.items() if v is not None)
    year_range = filters.get("year_range", ("?", "?"))
    panel_mode = filters.get("panel_mode", "thesis")
    stage_filter = ", ".join(filters.get("life_stages", [])) or "All stages"
    industry_filter = ", ".join(filters.get("industry_groups", [])) or "All industries"

    page_tasks = {
        "dashboard": (
            "Summarise the capital structure landscape shown in the KPIs. "
            "Identify the most significant trend, flag any anomaly vs theory, "
            "and suggest one actionable insight for the filtered cohort."
        ),
        "scenarios": (
            "Interpret the what-if scenario results. Explain what the predicted leverage "
            "implies given current macro conditions. Which coefficient is driving the outcome most? "
            "What should a CFO do given these inputs?"
        ),
        "ml": (
            "Explain why the ML model outperforms OLS. Which non-linear interactions "
            "are the SHAP values revealing? What does this mean for theory vs prediction?"
        ),
        "clustering": (
            "Name and characterise each cluster based on its financial profile. "
            "Which cluster is highest risk? How does this compare to Dickinson's classification? "
            "What does the ARI score imply about cash-flow-based life stage theory?"
        ),
    }
    task = page_tasks.get(page, "Provide key insights from the data shown above.")

    prompt = (
        f"## {page.title()} — Current Data Summary\n"
        f"**Filter context**: {year_range[0]}–{year_range[1]}, {stage_filter}, {industry_filter}, panel: {panel_mode}\n\n"
        f"{summary_lines}\n\n"
        f"**Task**: {task}"
    )

    cache_key = hashlib.sha256(prompt.encode()).hexdigest()
    ctx_key = hashlib.sha256(_json.dumps(data_summary, default=str, sort_keys=True).encode()).hexdigest()
    cached = db.ai_cache_get(cache_key, ctx_key, "claude-sonnet-4-6", ttl_hours=24)
    if cached:
        yield cached
        return

    full = ""
    for chunk in stream_anthropic(
        [{"role": "user", "content": prompt}],
        system=_THESIS_BLOCK,
        model="claude-sonnet-4-6",
        max_tokens=600,
        role=role,
        citations=citations,
    ):
        full += chunk
        yield chunk

    if full:
        db.ai_cache_set(cache_key, ctx_key, "claude-sonnet-4-6", full)


def parse_llm_json(raw: str) -> dict:
    """Parse LLM response as JSON. Falls back to plain-text answer. Never raises.

    Expected schema: {answer, citations, followup_questions, chart_request}.
    If the response is plain text (not JSON), wraps it in the answer key.

    Args:
        raw: Raw string from LLM (may be JSON, JSON-embedded-in-prose, or plain text).

    Returns:
        Dict with keys: answer (str), citations (list), followup_questions (list),
        chart_request (str | None).
    """
    default = {
        "answer": raw,
        "citations": [],
        "followup_questions": [],
        "chart_request": None,
    }
    if not isinstance(raw, str) or not raw.strip():
        return default
    try:
        parsed = json.loads(raw)
        if isinstance(parsed, dict):
            return {
                "answer": parsed.get("answer", raw),
                "citations": parsed.get("citations", []) or [],
                "followup_questions": parsed.get("followup_questions", []) or [],
                "chart_request": parsed.get("chart_request"),
            }
    except json.JSONDecodeError:
        pass
    # Fallback: extract first {...} block
    m = re.search(r"\{.*\}", raw, re.DOTALL)
    if m:
        try:
            parsed = json.loads(m.group())
            if isinstance(parsed, dict):
                return {
                    "answer": parsed.get("answer", raw),
                    "citations": parsed.get("citations", []) or [],
                    "followup_questions": parsed.get("followup_questions", []) or [],
                    "chart_request": parsed.get("chart_request"),
                }
        except json.JSONDecodeError:
            pass
    return default


_FOLLOWUP_MARKER_RE = re.compile(r"-{0,3}\s*\*{0,2}FOLLOWUPS_JSON\*{0,2}\s*:?", re.IGNORECASE)
_FENCE_RE = re.compile(r"^```(?:json)?\s*|\s*```$", re.MULTILINE)
_SALVAGE_Q_RE = re.compile(r'"([^"]{10,300}\?)"')


def _extract_balanced_object(text: str) -> Optional[str]:
    """Return the first balanced {...} substring in text, or None if unbalanced.

    Ignores braces inside JSON string literals so a stray '{' or '}' in a
    follow-up question does not break the scan.
    """
    start = text.find("{")
    if start == -1:
        return None
    depth = 0
    in_string = False
    escaped = False
    for i in range(start, len(text)):
        ch = text[i]
        if in_string:
            if escaped:
                escaped = False
            elif ch == "\\":
                escaped = True
            elif ch == '"':
                in_string = False
            continue
        if ch == '"':
            in_string = True
        elif ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                return text[start:i + 1]
    return None  # never closed — truncated response


def parse_followup_chips(text: str) -> tuple[str, list[str]]:
    """Split a streamed answer into (display_text, follow-up chips).

    The model is instructed to append a 'FOLLOWUPS_JSON: {...}' footer after
    its answer. This function must NEVER let that marker or its JSON leak
    into display_text, even when the model deviates from the instruction —
    truncated output (max_tokens cut-off), a markdown fence around the JSON,
    a bold marker, or trailing prose after the object. On any parse failure
    it falls back to regex-salvaging quoted questions from the tail, and
    worst case returns an empty chip list with a still-clean display_text.

    Args:
        text: Full accumulated response text from the LLM stream.

    Returns:
        (display_text, chips) — chips is a list of up to 3 non-empty strings.
    """
    m = _FOLLOWUP_MARKER_RE.search(text)
    if not m:
        return text.strip(), []

    display = text[:m.start()].strip()
    # Strip a trailing '---' separator the instruction's own template echoes
    display = re.sub(r"-{3,}\s*$", "", display).strip()

    tail = _FENCE_RE.sub("", text[m.end():]).strip()

    obj_str = _extract_balanced_object(tail)
    if obj_str is not None:
        try:
            parsed = json.loads(obj_str)
            raw_chips = parsed.get("followups") or parsed.get("followup_questions") or []
            if isinstance(raw_chips, list):
                chips = [str(q).strip() for q in raw_chips if isinstance(q, str) and q.strip()]
                if chips:
                    return display, chips[:3]
        except (json.JSONDecodeError, AttributeError):
            pass

    # Salvage: pull quoted question-like strings out of whatever tail we have
    salvaged = [q.strip() for q in _SALVAGE_Q_RE.findall(tail) if q.strip()]
    return display, salvaged[:3]


def log_chat_query(
    username: str,
    role: str,
    backend: str,
    token_count: int,
    query: str,
    session_id: Optional[str] = None,
) -> None:
    """Append a row to audit_log table for every chat query.

    Uses existing audit_log schema — no migration needed. Backend + token
    count + query preview live in the JSON details column. Silent no-op on
    any error so chat is never blocked by log failures.

    Args:
        username: Authenticated username or 'unknown'.
        role: User role ('admin', 'researcher', 'viewer', etc.).
        backend: LLM backend used ('ollama', 'anthropic', etc.).
        token_count: Approximate token count of context + query.
        query: User query string (truncated to 200 chars in details).
        session_id: Optional session identifier for correlation.
    """
    try:
        details = json.dumps({
            "llm_backend": backend,
            "token_count": int(token_count),
            "query_preview": (query or "")[:200],
        })
        # Use db.get_connection() — the public sqlite3 connection helper.
        # NOTE: db._connection (with leading underscore) does NOT exist; use get_connection.
        conn = db.get_connection()
        try:
            conn.execute(
                "INSERT INTO audit_log(username, role, page_name, action_type, details, session_id) "
                "VALUES (?,?,?,?,?,?)",
                (
                    username or "unknown",
                    role or "viewer",
                    "ai_assistant",
                    "ai_query",
                    details,
                    session_id or "",
                ),
            )
            conn.commit()
        finally:
            try:
                conn.close()
            except Exception:
                pass
    except Exception:
        # Never break user chat on log failure
        pass
