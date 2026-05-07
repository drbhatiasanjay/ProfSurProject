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


GROUNDING_FOOTER = (
    "\n\nAnswer ONLY from the data above. If asked about something not in "
    "the context, say 'This data is not available in my current context.' "
    "Cite specific figures by their exact values. Never fabricate numbers."
)

CONTEXT_BUDGET_TOKENS = 900


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
        md = (
            f"## COMPANY: {latest['company_name']} (code: {int(company_code)})\n"
            f"- Industry: {latest['industry_group']} | Life Stage: {latest['life_stage']} | Size Decile: {latest['size_decile']}\n"
            f"- Latest Year ({int(latest['year'])}): Leverage={float(latest['leverage']):.3f}, "
            f"Profitability={float(latest['profitability']):.3f}, "
            f"Tangibility={float(latest['tangibility']):.3f}, "
            f"FirmSize={float(latest['firm_size']):.3f}\n"
            f"- 5-Year Trend (leverage): {trend_csv}\n\n"
            f"## PEER GROUP ({peer_n} firms, same industry_group + life_stage, year {int(latest['year'])})\n"
            f"- Peer Mean Leverage: {peer_mean_lev:.3f} | Median: {peer_med_lev:.3f}\n"
            f"- Peer Mean Profitability: {peer_mean_roa:.3f} | Median: {peer_med_roa:.3f}\n"
            f"- Company vs Peer Median (leverage): {delta_lev:+.3f}\n"
        )
        text = md + GROUNDING_FOOTER
        # Token-budget guard — drop trend line, then peer detail, if over budget
        if count_tokens(text) > CONTEXT_BUDGET_TOKENS:
            md_no_trend = re.sub(r"- 5-Year Trend.*\n", "", md)
            text = md_no_trend + GROUNDING_FOOTER
        if count_tokens(text) > CONTEXT_BUDGET_TOKENS:
            text = (md.split("## PEER GROUP")[0] + GROUNDING_FOOTER)
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
        conn.close()
        if df.empty:
            return f"## PANEL OVERVIEW (mode={panel_mode})\nNo rows.{GROUNDING_FOOTER}"
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
        # By-stage leverage means
        stage_means = df.groupby("life_stage")["leverage"].mean().to_dict()
        order = ["Birth", "Growth", "Mature", "Decline"]
        stage_line = ", ".join(
            f"{s}={float(stage_means.get(s, float('nan'))):.3f}" for s in order
        )
        coef_lines = "\n".join(
            f"- {p}: coef={float(coefs.get(p, 0.0)):+.3f} (sample mean={float(means.get(_means_key_map.get(p, p), 0.0)):+.3f})"
            for p in PREDICTORS
        )
        md = (
            f"## PANEL OVERVIEW (mode={panel_mode})\n"
            f"- {total_firms} firms, "
            f"{total_obs} firm-year observations, "
            f"{year_min}-{year_max}\n"
            f"- Overall mean leverage: {float(df['leverage'].mean()):.3f}\n"
            f"- By Life Stage (mean leverage): {stage_line}\n\n"
            f"## OLS BASELINE (DV: leverage)\n"
            f"- intercept: {float(coefs.get('intercept', 0.0)):+.3f}\n"
            f"{coef_lines}\n"
            f"R^2 = {float(coefs.get('r_squared', 0.0)):.3f}, N = {int(coefs.get('n_obs', 0))}\n"
        )
        text = md + GROUNDING_FOOTER
        if count_tokens(text) > CONTEXT_BUDGET_TOKENS:
            # Truncate by dropping per-predictor sample means
            short = "\n".join(
                f"- {p}: coef={float(coefs.get(p, 0.0)):+.3f}" for p in PREDICTORS
            )
            text = md.replace(coef_lines, short) + GROUNDING_FOOTER
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
    factual_keywords = [
        "what is", "how much", "what's the", "leverage of", "roa of",
        "value of", "show me", "list", "year",
    ]
    analytical_keywords = [
        "why", "explain", "compare", "analyze", "interpret",
        "recommend", "should", "would", "suggest",
    ]
    has_factual = any(kw in q for kw in factual_keywords)
    has_analytical = any(kw in q for kw in analytical_keywords)

    if has_factual and not has_analytical:
        return "factual"
    if has_analytical and not has_factual:
        return "analytical"
    return "hybrid"


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
) -> Iterator[str]:
    """Yield string chunks from Anthropic streaming chat. Compatible with st.write_stream().

    API key resolution order: ANTHROPIC_API_KEY env var, then st.secrets.
    Streamlit is imported lazily inside this function (not at module level)
    so the module remains importable outside Streamlit (e.g. in pytest).

    Args:
        messages: List of {role, content} dicts.
        system: System prompt string.
        model: Anthropic model ID (default: claude-haiku-4-5-20251001).
        max_tokens: Maximum tokens in the response.

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
        with client.messages.stream(
            model=model,
            max_tokens=max_tokens,
            system=system,
            messages=messages,
        ) as stream:
            for text in stream.text_stream:
                yield text
    except Exception as e:
        yield f"[Anthropic error: {type(e).__name__}: {e}]"


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
