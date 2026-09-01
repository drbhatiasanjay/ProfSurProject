"""LLM adapters for Phase 6 AI Financial Assistant.

Two backends: Ollama (local, zero-egress, default in dev) and Anthropic
(Claude Haiku 4.5, default in Cloud Run prod). Both expose a generator
yielding string chunks compatible with st.write_stream().

Context builders produce <=900 token grounded prompts — no hallucination
surface. CFO mode injects company + peer metrics; Researcher mode injects
panel OLS outputs + descriptive statistics.
"""

import json
import re
import os
import typing
from typing import Iterator, Generator, Literal, Optional, List, Dict, Union, Any

import pandas as pd

import db

# Import once at module load so provider tests and runtime calls do not import
# the SDK while a caller is temporarily patching process environment access.
try:
    from google import genai as _GENAI_SDK
    from google.genai import types as _GENAI_TYPES
except ImportError:
    _GENAI_SDK = None
    _GENAI_TYPES = None

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
    *,
    panel_mode: str = "thesis",
    filters: Optional[dict] = None,
    chart_requested: bool = False,
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
    panel_mode: str = "thesis",
    filters: Optional[dict] = None,
    chart_requested: bool = False,
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


def query_financial_database(
    sql_query: str,
    panel_mode: str = "thesis",
    filters: Optional[dict] = None,
) -> str:
    """Execute a safe, read-only SQL SELECT query on the capital structure database.

    Args:
        sql_query: A valid SQLite SELECT query against tables: financials, companies.
    """
    import json
    from models.agent_tools import query_financial_database as _qfd
    res = _qfd(sql_query, panel_mode=panel_mode, filters=filters)
    return json.dumps(res, default=str)


def generate_chat_chart(
    chart_type: str,
    title: str,
    x_axis_label: str,
    y_axis_label: str,
    categories_csv: str,
    series_name: str,
    series_values_csv: str,
) -> str:
    """Render an interactive Plotly visualization for the user in the UI.

    Args:
        chart_type: One of 'line', 'bar', 'scatter', 'box', 'histogram', 'area'.
        title: Chart title.
        x_axis_label: X-axis label.
        y_axis_label: Y-axis label.
        categories_csv: Comma-separated list of categories or years (e.g. '2001, 2002, 2003').
        series_name: Name of the data series.
        series_values_csv: Comma-separated list of numeric values (e.g. '0.161, 0.155, 0.158').
    """
    import json
    from models.agent_tools import generate_chat_chart as _gcc
    cats = [c.strip() for c in str(categories_csv).split(",") if c.strip()]
    vals = []
    for v in str(series_values_csv).split(","):
        try:
            vals.append(float(v.strip()))
        except (ValueError, TypeError):
            vals.append(0.0)

    s_name = series_name or y_axis_label or "Series"
    series = [{"name": s_name, "values": vals}]

    spec = _gcc(
        chart_type=chart_type,
        title=title,
        x_axis_label=x_axis_label,
        y_axis_label=y_axis_label,
        categories=cats,
        series=series,
    )
    if spec.get("status") != "success":
        return json.dumps(spec, default=str)
    return json.dumps({
        "status": "success",
        "message": "Chart rendered successfully in UI. Do not output error apologies.",
        "chart_spec": spec.get("chart_spec", {}),
    }, default=str)


def query_semantic_ontology(
    query_type: str,
    stage: str = "",
    metric: str = "",
) -> str:
    """Look up normative leverage ranges, cash flow patterns, and anomaly explanations from the KG2 life-cycle ontology.

    Args:
        query_type: One of 'normative_band', 'stage_definition', 'explain_anomaly', 'macro_summary'.
        stage: Specific life stage (e.g. 'Startup', 'Growth', 'Maturity', 'Decline', 'Decay').
        metric: Financial metric name (e.g. 'leverage', 'profitability', 'tangibility').
    """
    import json
    from models.agent_tools import query_semantic_ontology as _qso
    return json.dumps(_qso(query_type=query_type, stage=stage, metric=metric), default=str)


query_financial_database.__annotations__ = typing.get_type_hints(query_financial_database)
generate_chat_chart.__annotations__ = typing.get_type_hints(generate_chat_chart)
query_semantic_ontology.__annotations__ = typing.get_type_hints(query_semantic_ontology)


def extract_chart_tool_spec(payload: Any) -> Optional[dict]:
    """Extract a validated chart spec from common Gemini tool-response envelopes."""
    from models.agent_tools import generate_chat_chart as _gcc

    if isinstance(payload, str):
        try:
            payload = json.loads(payload)
        except (TypeError, json.JSONDecodeError):
            return None
    if not isinstance(payload, dict):
        return None

    if payload.get("status") == "success" and isinstance(payload.get("rows"), list):
        return payload

    if isinstance(payload.get("chart_spec"), dict):
        return payload["chart_spec"]

    for key in ("result", "response", "output"):
        if key in payload:
            found = extract_chart_tool_spec(payload[key])
            if found:
                return found

    if payload.get("status") == "success" and "chart_type" in payload:
        res = _gcc(
            chart_type=payload.get("chart_type", "line"),
            title=payload.get("title", ""),
            x_axis_label=payload.get("x_axis_label", ""),
            y_axis_label=payload.get("y_axis_label", ""),
            categories=payload.get("categories", []),
            series=payload.get("series", []),
        )
        return res.get("chart_spec") if res.get("status") == "success" else None
    return None


def build_chart_spec_from_rows(rows: list[dict], user_query: str = "") -> Optional[dict]:
    """Build a chart from validated query rows when Gemini omits chart tooling."""
    from models.agent_tools import generate_chat_chart as _gcc

    if not isinstance(rows, list) or len(rows) < 2 or not all(isinstance(r, dict) for r in rows):
        return None
    keys = list(rows[0].keys())
    if len(keys) < 2:
        return None

    category_key = next((k for k in keys if str(k).lower() in {
        "year", "company_name", "industry_group", "life_stage", "stage", "name"
    }), keys[0])
    numeric_candidates = []
    for key in keys:
        if key == category_key:
            continue
        values = []
        valid = True
        for row in rows:
            try:
                value = row.get(key)
                if value is None:
                    valid = False
                    break
                values.append(float(value))
            except (TypeError, ValueError):
                valid = False
                break
        if valid and len(values) >= 2:
            score = 1 if str(key).lower() in {
                "leverage", "profitability", "tangibility", "avg_leverage", "avg_profitability"
            } else 0
            numeric_candidates.append((score, key, values))
    if not numeric_candidates:
        return None

    query_lower = str(user_query).lower()
    wants_scatter = "scatter" in query_lower or "versus" in query_lower or " vs " in query_lower
    if wants_scatter and category_key == keys[0] and len(numeric_candidates) >= 2:
        # For x-versus-y rows, use the first numeric column as X and the
        # remaining numeric column(s) as Y series.
        x_key = numeric_candidates[0][1]
        categories = [str(row.get(x_key, "")) for row in rows]
        selected = [item for item in numeric_candidates if item[1] != x_key]
        chart_series = [{"name": str(key), "values": values} for _, key, values in selected]
        x_label = str(x_key)
        y_label = ", ".join(str(item[1]) for item in selected)
    else:
        selected = numeric_candidates
        categories = [str(row.get(category_key, "")) for row in rows]
        chart_series = [{"name": str(key), "values": values} for _, key, values in selected]
        x_label = str(category_key)
        y_label = ", ".join(str(item[1]) for item in selected)
    is_year = all(c.isdigit() and len(c) == 4 for c in categories)
    if "scatter" in query_lower or "versus" in query_lower or " vs " in query_lower:
        chart_type = "scatter"
    elif "area" in query_lower:
        chart_type = "area"
    elif "histogram" in query_lower or "distribution" in query_lower:
        chart_type = "histogram"
    elif "box" in query_lower or "quartile" in query_lower:
        chart_type = "box"
    else:
        chart_type = "bar" if "bar" in query_lower else ("line" if is_year or "trend" in query_lower else "bar")
    orientation = "h" if "horizontal" in query_lower else "v"
    result = _gcc(
        chart_type=chart_type,
        title=f"{y_label} by {x_label}",
        x_axis_label=x_label,
        y_axis_label=y_label,
        categories=categories,
        series=chart_series,
        orientation=orientation,
        show_trendline="trendline" in query_lower,
    )
    return result.get("chart_spec") if result.get("status") == "success" else None


def select_chart_rows_for_query(datasets: list[list[dict]], user_query: str = "") -> list[dict]:
    """Choose the current question's dataset from Gemini's accumulated tool history."""
    query = str(user_query or "").lower()
    if not datasets:
        return []
    preferred_keys = []
    if "industry" in query:
        preferred_keys.append("industry_group")
    if "life stage" in query or "lifestage" in query or "stage" in query:
        preferred_keys.extend(["life_stage", "stage"])
    if "company" in query or "firm" in query:
        preferred_keys.extend(["company_name", "company_code"])
    if any(term in query for term in ("over time", "by year", "annual", "yearly", "trend")):
        preferred_keys.append("year")
    for rows in reversed(datasets):
        keys = {str(key).lower() for row in rows if isinstance(row, dict) for key in row}
        if any(key in keys for key in preferred_keys):
            return rows
    return datasets[-1]


def normalize_assistant_chunk(chunk: Any) -> tuple[str, Optional[dict]]:
    """Normalize a provider stream item into text and an optional chart spec."""
    if isinstance(chunk, str):
        return chunk, None
    if not isinstance(chunk, dict):
        return "", None
    chart = chunk.get("spec") if chunk.get("type") == "chart" else chunk.get("chart_spec")
    if not isinstance(chart, dict):
        chart = None
    text = chunk.get("text") or chunk.get("content") or chunk.get("answer") or ""
    return str(text), chart


def stream_with_fallback(primary: Iterator[Any], fallback_factory) -> Iterator[Any]:
    """Use one fallback provider when the primary fails before yielding content."""
    yielded_content = False
    for chunk in primary:
        text, _chart = normalize_assistant_chunk(chunk)
        is_error = text.lstrip().startswith("[") and " error" in text[:80].lower()
        if is_error and not yielded_content:
            yield from fallback_factory()
            return
        if text or _chart:
            yielded_content = True
        yield chunk


def stream_with_cancellation(stream: Iterator[Any], stop_event) -> Iterator[Any]:
    """Stop a provider stream cooperatively when its cancellation event is set."""
    for chunk in stream:
        if stop_event is not None and stop_event.is_set():
            yield {"type": "status", "text": "[Generation stopped by user]"}
            return
        yield chunk


def should_generate_chart(user_query: str) -> bool:
    """Detect explicit and implicit requests where a visual comparison is useful."""
    query = str(user_query or "").lower()
    return any(term in query for term in (
        "chart", "graph", "plot", "visual", "bar", "trend", "illustrat",
        "diagram", "display", "interactive", "vary by", "varies by",
        "by industry", "by life stage", "by lifestage", "across industry",
        "across industries", "differ across", "differs across",
        "across different", "distribution", "compare", "comparison", "versus",
        "top ", "bottom ", "rank", "over time",
    ))


def _extract_markdown_table(text: str) -> list[dict]:
    """Parse provider-generated Markdown or tab-separated tables into rows."""
    lines = [line.strip() for line in str(text or "").splitlines()
             if line.strip().startswith("|") and line.strip().endswith("|")]
    if len(lines) >= 3:
        headers = [c.strip() for c in lines[0].strip("|").split("|")]
        if len(headers) < 2 or not re.match(r"^[\s|:\-]+$", lines[1]):
            lines = []
        else:
            data_lines = lines[2:]
    else:
        data_lines = []
    if not lines:
        candidates = [line.strip() for line in str(text or "").splitlines() if "\t" in line]
        header_index = next((i for i, line in enumerate(candidates)
                             if "industry" in line.lower() and
                             ("profit" in line.lower() or "roa" in line.lower())), None)
        if header_index is None:
            return []
        headers = [c.strip() for c in candidates[header_index].split("\t")]
        data_lines = candidates[header_index + 1:]
    rows = []
    for line in data_lines:
        cells = [c.strip() for c in (line.strip("|").split("|") if "|" in line else line.split("\t"))]
        if len(cells) >= len(headers):
            rows.append({headers[i]: cells[i] for i in range(len(headers))})
    return rows


def normalize_assistant_response(
    text: str,
    *,
    chart_spec: Optional[dict] = None,
    user_query: str = "",
    chart_requested: bool = False,
) -> dict:
    """Return the common answer/table/chart contract used by every backend."""
    from models.agent_tools import extract_chat_chart_spec, extract_table_chart_spec

    answer = str(text or "")
    embedded_chart, cleaned = extract_chat_chart_spec(answer)
    if embedded_chart:
        answer = cleaned
    else:
        # A provider can emit an incomplete/invalid chart JSON block. It must
        # never leak into the user-facing answer as a wide monospace block.
        answer = _remove_unrenderable_chart_blocks(answer)
    answer = _remove_repeated_sections(answer)
    resolved_chart = chart_spec or embedded_chart
    table = _extract_markdown_table(answer)
    if chart_requested and resolved_chart is None:
        resolved_chart = extract_table_chart_spec(answer, user_q=user_query)
    return {
        "answer": answer,
        "table": table,
        "chart_spec": resolved_chart,
        "sources": [],
    }


def _remove_unrenderable_chart_blocks(text: str) -> str:
    """Remove provider chart payloads that could not be parsed/rendered."""
    if not text or "chart_type" not in text:
        return text

    chart_block = re.compile(
        r"```(?:json|javascript|js)?\s*"
        r"(?=[\s\S]*?\"chart_type\")"
        r"[\s\S]*?(?:```|\Z)",
        flags=re.IGNORECASE,
    )
    cleaned = chart_block.sub("", text)
    return re.sub(r"\n{3,}", "\n\n", cleaned).strip()


def _remove_repeated_sections(text: str) -> str:
    """Collapse duplicated provider sections and headings caused by echoing."""
    paragraphs = re.split(r"\n\s*\n", str(text or ""))
    seen: set[str] = set()
    kept: list[str] = []
    for paragraph in paragraphs:
        lines = paragraph.splitlines()
        filtered_lines: list[str] = []
        for line in lines:
            normalized_line = re.sub(r"\s+", " ", line).strip().lower()
            is_heading = bool(re.match(r"^#{1,6}\s+", line.strip()))
            is_label = bool(re.match(r"^[^.!?]{2,80}:$", line.strip()))
            if (is_heading or is_label) and normalized_line in seen:
                continue
            if is_heading or is_label:
                seen.add(normalized_line)
            filtered_lines.append(line)
        paragraph = "\n".join(filtered_lines).strip()
        if not paragraph:
            continue
        normalized = re.sub(r"\s+", " ", paragraph).strip().lower()
        # Short repeated labels can be intentional; only suppress substantive blocks.
        if len(normalized) >= 80 and normalized in seen:
            continue
        if len(normalized) >= 80:
            seen.add(normalized)
        kept.append(paragraph.strip())
    return "\n\n".join(part for part in kept if part).strip()


def stream_gemini_agent(
    messages: List[Dict[str, Any]],
    system: str = "",
    model: str = "gemini-2.5-flash",
    max_tokens: int = 2048,
    *,
    role: str = "researcher",
    citations: bool = False,
    panel_mode: str = "thesis",
    filters: Optional[dict] = None,
    chart_requested: bool = False,
) -> Generator[Union[str, dict], None, None]:
    """Autonomous agentic streaming loop using Google GenAI SDK (google.genai).

    Equipped with three primary tool capabilities:
    - query_financial_database (safe read-only SQL querying on capital_structure.db)
    - generate_chat_chart (interactive Plotly spec generation)
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
        from models.agent_tools import get_database_schema_summary
        from models.agent_tools import query_financial_database as _qfd
    except ImportError as _imp_err:
        yield f"[Google GenAI SDK not installed. Run: pip install google-genai] Error: {_imp_err}"
        return
    genai = _GENAI_SDK
    types = _GENAI_TYPES
    if genai is None or types is None:
        yield "[Google GenAI SDK not installed. Run: pip install google-genai]"
        return

    try:
        client = genai.Client(api_key=api_key)

        # Bind scope in the closure so the model cannot omit or change it.
        def query_financial_database(sql_query: str) -> str:
            return json.dumps(_qfd(sql_query, panel_mode=panel_mode, filters=filters), default=str)

        query_financial_database.__annotations__ = {"sql_query": str, "return": str}

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
        clean_context = re.sub(r"INSTRUCTIONS:\s*Answer ONLY from.*?(?=\n\n|\Z)", "", system, flags=re.DOTALL).strip()
        clean_context = re.sub(r"If asked about something not in the context, say exactly:.*?(?=\n\n|\Z)", "", clean_context, flags=re.DOTALL).strip()

        agent_instructions = (
            "PANEL COVERAGE & CRITICAL RULES:\n"
            "1. The panel database covers annual corporate financial records from 2001 to 2025 inclusive (400 Indian listed firms, 9,031 observations).\n"
            "2. Whenever the user requests specific company lookups, top rankings, distributions (median, standard deviation, percentiles, min, max), Year-overYear (YoY) tables, or queries about specific years (e.g. 2024, 2025), YOU MUST call query_financial_database to query capital_structure.db.\n"
            "3. Join companies and financials on company_code: JOIN companies c ON f.company_code = c.company_code (Note: use company_code, not company_id).\n"
            "4. When the user requests a chart, plot, graph, or visual representation, query the database if needed, call generate_chat_chart, and accompany the interactive visualization with the complete data table and an insightful economic analysis. The UI automatically renders the interactive Plotly graph.\n"
            "5. Cite sources using [Source: Theory], [Source: Latest (2001-2025)], or [Source: OLS Model] where appropriate.\n"
            "6. The interactive charting system is fully supported and operational. NEVER output apologies or statements claiming you are unable to generate charts or graphs.\n"
        )

        effective_system = f"{role_preamble}\n\n{agent_instructions}\n\n{get_database_schema_summary()}\n\n{clean_context}"
        if citations:
            effective_system += (
                "\n\nSupport your analysis with relevant citations from capital structure literature "
                "(Modigliani & Miller 1958, Myers 1984, Rajan & Zingales 1995, Jensen & Meckling 1976, "
                "Fama & French 2002, Dickinson 2011). Format citations as Author (Year) inline."
            )

        formatted_contents = []
        for m in messages:
            content = str(m.get("content", "")).strip()
            if not content:
                continue
            # Filter out legacy tool errors / apologies from historical context
            if "internal tool error" in content or "INVALID_ARGUMENT" in content or "[Gemini error:" in content:
                continue
            role_val = "user" if m.get("role") == "user" else "model"
            formatted_contents.append(
                types.Content(
                    role=role_val,
                    parts=[types.Part.from_text(text=content)],
                )
            )
        if not formatted_contents:
            if messages:
                formatted_contents = [types.Content(role="user", parts=[types.Part.from_text(text=messages[-1].get("content", ""))])]
            else:
                return

        tool_config = None
        if chart_requested:
            tool_config = types.ToolConfig(
                function_calling_config=types.FunctionCallingConfig(
                    mode="ANY",
                    allowed_function_names=["query_financial_database"],
                )
            )

        config = types.GenerateContentConfig(
            system_instruction=effective_system,
            temperature=0.1,
            max_output_tokens=max_tokens,
            tools=[
                query_financial_database,
                generate_chat_chart,
                query_semantic_ontology,
            ],
            tool_config=tool_config,
        )

        response = client.models.generate_content(
            model=model,
            contents=formatted_contents,
            config=config,
        )

        def _extract_response_text(resp) -> str:
            if not resp:
                return ""
            parts_text = []
            # Prioritize candidates content (the completed final turn)
            for cand in (getattr(resp, "candidates", None) or []):
                content = getattr(cand, "content", None)
                if content:
                    for p in (getattr(content, "parts", None) or []):
                        t = getattr(p, "text", None)
                        if t and t.strip():
                            parts_text.append(t.strip())
            if parts_text:
                return "\n\n".join(parts_text)
            # If candidates was empty, inspect history turns
            for turn in (getattr(resp, "automatic_function_calling_history", None) or []):
                if getattr(turn, "role", "") == "model":
                    for p in (getattr(turn, "parts", None) or []):
                        if getattr(p, "function_call", None):
                            continue
                        t = getattr(p, "text", None)
                        if t and t.strip():
                            parts_text.append(t.strip())
            if parts_text:
                return "\n\n".join(parts_text)
            try:
                t = getattr(resp, "text", None)
                if t:
                    return t
            except Exception:
                pass
            return ""

        final_text = _extract_response_text(response)
        has_yielded_chart = False
        has_yielded_text = False
        query_datasets = []

        # 1. Check if generate_chat_chart was called in automatic_function_calling_history
        for item in (getattr(response, "automatic_function_calling_history", None) or []):
            for part in (getattr(item, "parts", None) or []):
                fn_resp = getattr(part, "function_response", None)
                if fn_resp and "query_financial_database" in getattr(fn_resp, "name", ""):
                    query_payload = extract_chart_tool_spec(getattr(fn_resp, "response", None))
                    if isinstance(query_payload, dict) and isinstance(query_payload.get("rows"), list):
                        query_datasets.append(query_payload["rows"])
                if fn_resp and "generate_chat_chart" in getattr(fn_resp, "name", ""):
                    spec = extract_chart_tool_spec(getattr(fn_resp, "response", None))
                    if spec:
                        yield {"type": "chart", "spec": spec}
                        has_yielded_chart = True

        query_rows = select_chart_rows_for_query(
            query_datasets, user_query=messages[-1].get("content", "")
        )
        if chart_requested and not has_yielded_chart and query_rows:
            fallback_spec = build_chart_spec_from_rows(
                query_rows, user_query=messages[-1].get("content", "")
            )
            if fallback_spec:
                yield {"type": "chart", "spec": fallback_spec}
                has_yielded_chart = True

        # 2. Also check if model embedded JSON chart spec in text
        from models.agent_tools import extract_chat_chart_spec
        chart_spec, cleaned_final = extract_chat_chart_spec(final_text)
        if chart_spec and not has_yielded_chart:
            yield {"type": "chart", "spec": chart_spec}
            has_yielded_chart = True
            final_text = cleaned_final

        if has_yielded_chart and final_text:
            disclaimer_patterns = [
                r"I apologize[^\n]*",
                r"I am (?:currently|still) (?:unable|experiencing)[^\n]*",
                r"\(Note:[^\)\n]*?(?:chart|graph|visual|tool)[^\)\n]*?\)",
                r"Note: There was an issue generating[^\n]*",
                r"However, I (?:have provided|can still provide)[^\n]*",
            ]
            cleaned = final_text
            for pat in disclaimer_patterns:
                cleaned = re.sub(pat, "", cleaned, flags=re.IGNORECASE)
            final_text = re.sub(r"\n\s*\n\s*\n", "\n\n", cleaned).strip()

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
