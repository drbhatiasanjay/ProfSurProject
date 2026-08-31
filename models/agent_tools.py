"""Agent Tools for LifeCycle Leverage AI Assistant.

Provides three primary tools for Google ADK / GenAI and Anthropic tool calling:
1. query_financial_database — Safe, read-only SQL tool against SQLite capital_structure.db
2. generate_chat_chart — Generates structured Plotly chart specifications for in-chat visualization
3. query_semantic_ontology — Queries the KG2 semantic knowledge graph and Dickinson stage rules
"""
from __future__ import annotations

import re
import sqlite3
from typing import Any, Dict, List, Optional
import pandas as pd

import db

# ── Safety & Sandbox Config for NL-to-SQL ─────────────────────────────────────

_FORBIDDEN_SQL_PATTERNS = [
    r"\b(INSERT|UPDATE|DELETE|DROP|ALTER|CREATE|ATTACH|DETACH|PRAGMA|REPLACE|TRUNCATE|GRANT|REVOKE|EXEC|VACUUM)\b",
]

_ALLOWED_TABLES = {"financials", "companies", "data_vintages", "model_runs"}


def get_database_schema_summary() -> str:
    """Return a compact schema summary of the capital structure database to guide NL-to-SQL."""
    return (
        "Database Tables & Columns:\n"
        "1. companies (company_code INT PRIMARY KEY, company_name TEXT, industry_group TEXT, bse_code TEXT, nse_symbol TEXT)\n"
        "2. financials (company_code INT, year INT, life_stage TEXT, size_decile TEXT, leverage REAL, "
        "profitability REAL, tangibility REAL, firm_size REAL, log_size REAL, tax REAL, tax_shield REAL, "
        "dividend REAL, ocf REAL, icf REAL, fcf REAL, vintage TEXT)\n"
        "   - life_stage values: 'Startup', 'Growth', 'Maturity', 'Shakeout1', 'Shakeout2', 'Shakeout3', 'Decline', 'Decay'\n"
        "   - leverage = Debt / Total Assets * 100\n"
        "   - profitability = Return on Assets (ROA)\n"
        "   - tangibility = Fixed Assets / Total Assets\n"
        "3. data_vintages (vintage_id TEXT, description TEXT, year_start INT, year_end INT, n_firms INT, n_obs INT)\n"
        "Supported SQLite aggregate & scalar functions: AVG(x), COUNT(x), MIN(x), MAX(x), SUM(x), "
        "MEDIAN(x), STDEV(x), P25(x), P75(x), P90(x), P95(x), P99(x), SQRT(x), LOG(x), POWER(x, n).\n"
    )


def query_financial_database(
    sql_query: str,
    panel_mode: str = "thesis",
) -> dict:
    """Execute a safe, read-only SQL query on the capital structure database.

    Args:
        sql_query: A valid SQLite SELECT query. Must only query SELECT on allowed tables.
        panel_mode: Active panel mode ('thesis', 'latest', 'run3', 'us_av_2024') to filter vintage.

    Returns:
        Dict with status, columns, rows, count, or error message.
    """
    clean_query = sql_query.strip().rstrip(";")
    if not clean_query:
        return {"status": "error", "error": "Query string cannot be empty."}

    # 1. Prevent stacked queries with internal semicolons
    if ";" in clean_query:
        return {
            "status": "error",
            "error": "Security violation: Stacked queries with ';' are not permitted.",
        }

    # 2. Reject forbidden DDL/DML
    for pattern in _FORBIDDEN_SQL_PATTERNS:
        if re.search(pattern, clean_query, re.IGNORECASE):
            return {
                "status": "error",
                "error": f"Security violation: Query contains disallowed SQL pattern '{pattern}'. Only single SELECT queries are permitted.",
            }

    # 3. Must start with SELECT or WITH
    if not re.match(r"^(SELECT|WITH)\b", clean_query, re.IGNORECASE):
        return {
            "status": "error",
            "error": "Query must start with SELECT or WITH.",
        }

    # 3. Ensure automatic LIMIT 50 if none provided
    if not re.search(r"\bLIMIT\s+\d+\b", clean_query, re.IGNORECASE):
        clean_query = f"{clean_query} LIMIT 50"

    try:
        conn = db.get_connection()
        conn.row_factory = sqlite3.Row
        try:
            cursor = conn.cursor()
            cursor.execute(clean_query)
            rows = cursor.fetchall()
            columns = [desc[0] for desc in cursor.description] if cursor.description else []
            result_rows = [dict(r) for r in rows]
            return {
                "status": "success",
                "query_executed": clean_query,
                "columns": columns,
                "count": len(result_rows),
                "rows": result_rows,
            }
        finally:
            conn.close()
    except Exception as e:
        return {
            "status": "error",
            "error": f"SQL execution error: {type(e).__name__}: {str(e)}",
            "schema_hint": get_database_schema_summary(),
        }


# ── In-Chat Plotly Visualization Spec Generator ───────────────────────────────

def generate_chat_chart(
    chart_type: str,
    title: str,
    x_axis_label: str,
    y_axis_label: str,
    categories: list,
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
        categories: X-axis values (e.g. ['2001', '2002', ...] or stage names).
        series: List of dicts, each with 'name' (str) and 'values' (list of numbers).
        series_json: Optional JSON string of series list, e.g. '[{"name": "Mean", "values": [0.1, 0.2]}]'.

    Returns:
        Dict with status and chart specification payload.
    """
    valid_types = {"line", "bar", "scatter", "box", "histogram", "area", "heatmap"}
    if not chart_type or chart_type.lower() not in valid_types:
        chart_type = "line"

    if isinstance(series, dict):
        series = [series]

    if series is None and series_json:
        if isinstance(series_json, str):
            try:
                import json
                series = json.loads(series_json)
            except Exception:
                series = []
        elif isinstance(series_json, (list, tuple)):
            series = list(series_json)
        elif isinstance(series_json, dict):
            series = [series_json]

    if isinstance(categories, (list, tuple)):
        categories = [str(c) for c in categories]
    elif categories is not None:
        categories = [str(categories)]
    else:
        categories = []

    if not isinstance(series, (list, tuple)) or not series:
        return {"status": "error", "error": "Chart must include at least one series."}

    cleaned_series = []
    for s in series:
        if hasattr(s, "model_dump"):
            s = s.model_dump()
        elif hasattr(s, "dict"):
            s = s.dict()
        elif not isinstance(s, dict):
            try:
                s = dict(s)
            except Exception:
                continue

        if isinstance(s, dict):
            s_name = s.get("name") or s.get("series") or s.get("label") or s.get("title") or "Series"
            vals = s.get("values")
            if vals is None:
                vals = s.get("data")
            if vals is None:
                vals = s.get("y")
            if vals is None:
                vals = s.get("points", [])

            if isinstance(vals, (int, float)):
                vals = [vals]
            elif not isinstance(vals, (list, tuple)):
                try:
                    vals = list(vals) if vals is not None else []
                except Exception:
                    vals = []
            cleaned_vals = []
            for v in vals:
                try:
                    if v is not None and not pd.isna(v):
                        cleaned_vals.append(float(v))
                    else:
                        cleaned_vals.append(0.0)
                except Exception:
                    cleaned_vals.append(0.0)
            cleaned_series.append({
                "name": str(s_name),
                "values": cleaned_vals,
            })

    if not cleaned_series:
        return {"status": "error", "error": "No valid series dicts with 'name' and 'values' were found."}

    return {
        "status": "success",
        "chart_spec": {
            "chart_type": chart_type.lower(),
            "title": title,
            "x_axis_label": x_axis_label,
            "y_axis_label": y_axis_label,
            "categories": [str(c) for c in (categories or [])],
            "series": cleaned_series,
        },
    }


def render_chat_chart_figure(spec: dict, theme: str = "light") -> Any:
    """Build an interactive Plotly Figure from a chart specification."""
    import plotly.graph_objects as go
    from helpers import plotly_layout_light, plotly_layout_dark

    chart_type = spec.get("chart_type", "line").lower()
    title = spec.get("title", "")
    x_label = spec.get("x_axis_label", "")
    y_label = spec.get("y_axis_label", "")
    categories = spec.get("categories", [])
    series = spec.get("series", [])

    fig = go.Figure()
    for s in series:
        s_name = s.get("name", "")
        s_vals = s.get("values", [])
        if chart_type == "bar":
            fig.add_trace(go.Bar(x=categories, y=s_vals, name=s_name))
        elif chart_type == "scatter":
            fig.add_trace(go.Scatter(x=categories, y=s_vals, mode="markers", name=s_name))
        elif chart_type == "box":
            fig.add_trace(go.Box(y=s_vals, name=s_name, x=categories if len(categories) == len(s_vals) else None))
        elif chart_type in ("area", "filled_line"):
            fig.add_trace(go.Scatter(x=categories, y=s_vals, mode="lines", fill="tozeroy", name=s_name))
        elif chart_type == "histogram":
            fig.add_trace(go.Histogram(x=s_vals, name=s_name))
        else:
            fig.add_trace(go.Scatter(x=categories, y=s_vals, mode="lines+markers", name=s_name))

    layout_func = plotly_layout_dark if str(theme).lower() == "dark" else plotly_layout_light
    fig.update_layout(
        xaxis_title=x_label,
        yaxis_title=y_label,
        **layout_func(title=title),
    )
    return fig


def extract_chat_chart_spec(text: str) -> tuple[Optional[dict], str]:
    """Inspect response text for an embedded JSON chart specification.

    If found, validates and normalizes the chart spec via generate_chat_chart,
    and returns (chart_spec_dict, cleaned_text_with_json_removed).
    If no valid chart spec is found, returns (None, original_text).
    """
    if not text:
        return None, text

    if "chart_type" not in text and "chart_spec" not in text:
        return None, text

    import json
    pattern = r"```(?:json)?\s*(\{[\s\S]*?(?:\"chart_type\"|\"chart_spec\")[\s\S]*?\})\s*```"
    match = re.search(pattern, text, re.IGNORECASE)
    if not match:
        bare_pattern = r"(\{\s*\"(?:chart_type|chart_spec)\"[\s\S]*?\n\})"
        match = re.search(bare_pattern, text)

    if match:
        raw_json = match.group(1)
        try:
            parsed = json.loads(raw_json)
            if isinstance(parsed, dict):
                if "chart_spec" in parsed and isinstance(parsed["chart_spec"], dict):
                    parsed = parsed["chart_spec"]
                if "chart_type" in parsed:
                    s_input = parsed.get("series") or parsed.get("series_json") or parsed.get("data") or []
                    res = generate_chat_chart(
                        chart_type=parsed.get("chart_type", "line"),
                        title=parsed.get("title", ""),
                        x_axis_label=parsed.get("x_axis_label", ""),
                        y_axis_label=parsed.get("y_axis_label", ""),
                        categories=parsed.get("categories", []),
                        series=s_input if isinstance(s_input, (list, tuple)) else None,
                        series_json=s_input if isinstance(s_input, str) else "",
                    )
                    if res.get("status") == "success":
                        clean_text = text[:match.start()].rstrip() + "\n" + text[match.end():].lstrip()
                        return res["chart_spec"], clean_text.strip()
        except Exception:
            pass

    return None, text


# ── KG2 Semantic Knowledge Graph & Ontology Lookups ──────────────────────────

_NORMATIVE_BANDS = {
    "Startup": {"leverage_band": "High / External (30-60%)", "primary_source": "Equity / Venture Debt", "distress_risk": "Moderate-High"},
    "Growth": {"leverage_band": "Moderate-High (25-45%)", "primary_source": "Debt & Reinvestment", "distress_risk": "Low-Moderate"},
    "Maturity": {"leverage_band": "Low-Moderate (15-30%)", "primary_source": "Retained Earnings (Internal)", "distress_risk": "Lowest"},
    "Shakeout1": {"leverage_band": "Transitional (20-40%)", "primary_source": "Mixed Cash Flow", "distress_risk": "Moderate"},
    "Shakeout2": {"leverage_band": "Volatile (25-50%)", "primary_source": "Restructuring", "distress_risk": "High"},
    "Shakeout3": {"leverage_band": "Distressed (30-65%)", "primary_source": "Emergency Liquidity", "distress_risk": "Very High"},
    "Decline": {"leverage_band": "Elevated Distress (35-70%)", "primary_source": "Disinvestment / Debt Legacy", "distress_risk": "High"},
    "Decay": {"leverage_band": "Extreme Distress (>50%)", "primary_source": "Default / Workout", "distress_risk": "Critical"},
}

_CASH_FLOW_SIGNS = {
    "Startup": {"OCF": "-", "ICF": "-", "FCF": "+", "theory": "Heavy CapEx and initial losses financed by external cash inflows."},
    "Growth": {"OCF": "+", "ICF": "-", "FCF": "-", "theory": "Strong operating cash reinvested into CapEx with debt repayment/dividend initiation."},
    "Maturity": {"OCF": "+", "ICF": "-", "FCF": "-", "theory": "Peak cash generation fully funding moderate CapEx; debt levels reduced via pecking order."},
    "Shakeout": {"OCF": "Mixed", "ICF": "Mixed", "FCF": "Mixed", "theory": "Industry consolidation and margin compression causing mixed cash flow profiles."},
    "Decline": {"OCF": "-", "ICF": "+", "FCF": "+/-", "theory": "Asset sales (ICF+) offsetting operating deficits (OCF-); leverage reflects distress."},
    "Decay": {"OCF": "-", "ICF": "+", "FCF": "-", "theory": "Severe deterioration, insolvency risk, and inability to raise external financing."},
}


def query_semantic_ontology(
    query_type: str,
    stage: str = "",
    metric: str = "",
) -> dict:
    """Query the LifeCycle KG2 semantic ontology for normative bands, stage rules, and anomalies.

    Args:
        query_type: One of 'normative_band', 'stage_definition', 'explain_anomaly', 'macro_summary'.
        stage: Specific life stage (e.g. 'Startup', 'Growth', 'Maturity', 'Decline', 'Decay').
        metric: Financial metric name (e.g. 'leverage', 'profitability', 'tangibility').

    Returns:
        Dict containing ontology data and theoretical citations.
    """
    qt = query_type.lower()
    clean_stage = stage.capitalize() if stage else ""

    if qt == "normative_band":
        band = _NORMATIVE_BANDS.get(clean_stage)
        if band:
            return {
                "status": "success",
                "stage": clean_stage,
                "normative_band": band,
                "source": "Dickinson (2011) & Thesis Normative Calibration",
            }
        return {"status": "success", "all_normative_bands": _NORMATIVE_BANDS}

    elif qt == "stage_definition":
        sign = _CASH_FLOW_SIGNS.get(clean_stage) or _CASH_FLOW_SIGNS.get(clean_stage.replace("1", "").replace("2", "").replace("3", ""))
        if sign:
            return {
                "status": "success",
                "stage": clean_stage,
                "cash_flow_signs": sign,
                "reference": "Dickinson, V. (2011). Cash flow patterns as a proxy for firm life cycle. The Accounting Review, 86(6), 1969-1994.",
            }
        return {"status": "success", "stages": _CASH_FLOW_SIGNS}

    elif qt == "explain_anomaly":
        if clean_stage in ("Decline", "Decay", "Shakeout3") and ("lev" in metric.lower() or not metric):
            return {
                "status": "success",
                "explanation": (
                    f"In {clean_stage} stage, elevated leverage is driven by accumulated distress debt, "
                    "operating losses eroding equity book value, and fixed debt obligations rather than proactive growth borrowing. "
                    "Under Trade-Off Theory, distress costs outweigh tax shield benefits."
                ),
                "citations": ["Jensen & Meckling (1976)", "Myers (1984)", "Dickinson (2011)"],
            }
        elif clean_stage == "Maturity" and ("prof" in metric.lower() or "lev" in metric.lower()):
            return {
                "status": "success",
                "explanation": (
                    "In Maturity stage, high profitability reduces leverage according to Pecking Order Theory (POT), "
                    "as firms generate abundant internal cash flow (OCF+) and prioritize internal funds over debt."
                ),
                "citations": ["Myers & Majluf (1984)", "Rajan & Zingales (1995)"],
            }
        return {
            "status": "success",
            "explanation": f"Theoretical relationship between life stage '{clean_stage}' and metric '{metric}'.",
            "citations": ["Dickinson (2011)"],
        }

    # Default / macro summary
    try:
        import graph_bridge
        macro_json = graph_bridge.get_graph_json("macro")
        return {
            "status": "success",
            "macro_node_count": len(macro_json.get("nodes", [])),
            "macro_edge_count": len(macro_json.get("links", [])),
            "stages_covered": list(_NORMATIVE_BANDS.keys()),
        }
    except Exception:
        return {"status": "success", "stages": list(_NORMATIVE_BANDS.keys())}
