"""
Scenarios — Determinant sliders, predicted leverage, waterfall chart, company comparison.
"""

import streamlit as st
import plotly.graph_objects as go
import pandas as pd
import numpy as np
import db
from helpers import (
    plotly_layout, format_pct, ensure_session_state, panel_label,
    PRIMARY, SECONDARY, ACCENT, STAGE_COLORS, PLOTLY_CONFIG,
    render_bento_kpi, render_stage_badge,
    _render_insight_box, df_download_button, chart_download_button, audit_trail_download_button,
)
from models.scenario_regression import compute_leverage_ols_coefs, leverage_predictor_sample_means
from models.llm_adapters import generate_page_insights

ensure_session_state()
db.log_page_visit("Scenarios")

_username = st.session_state.get("user", {}).get("username", "")
_sprefs   = db.load_user_prefs(_username, "scenarios") if _username else {}

# Panel choice from the sidebar — coefficients reflect whichever panel is active.
# (Previously pinned to thesis; now follows user selection so users can compare
# scenarios across thesis / latest / run3.)
filters = st.session_state.filters
ft = db.filters_to_tuple(filters)
_panel = st.session_state.get("panel_mode", "latest")
_data_source = getattr(st.session_state, "data_source_mode", "sqlite")
_version_id = (
    db.get_current_api_version()
    if db.is_cmie_lab_enabled() and _data_source == "cmie"
    else None
)

st.markdown("### Scenario Analysis")
st.caption(
    "Adjust firm characteristics to see predicted leverage based on panel regression coefficients."
    f" · Active panel: **{panel_label(_panel)}**"
)
if _panel != "thesis":
    st.warning(
        f"Coefficients are computed on the **{panel_label(_panel)}** and will differ from "
        "the published thesis values. Switch to **Thesis panel (2001–2024)** in the sidebar "
        "to reproduce thesis tables.",
        icon="🔄",
    )

# ── Compute OLS coefficients from the active panel (filters + CMIE version when applicable) ──
# Args must NOT use a leading underscore: Streamlit excludes those from the cache key.
@st.cache_data(ttl=3600)
def compute_coefficients(filters_tuple, data_source: str, version_id: str | None):
    """Run simple OLS on the filtered panel (SQLite or CMIE api_financials)."""
    if db.is_cmie_lab_enabled() and data_source == "cmie" and version_id:
        panel = db.get_api_panel_data(version_id, filters_tuple)
    else:
        panel = db.get_panel_data(filters_tuple)
    return compute_leverage_ols_coefs(panel)


@st.cache_data(ttl=3600)
def get_sample_means(filters_tuple, data_source: str, version_id: str | None):
    if db.is_cmie_lab_enabled() and data_source == "cmie" and version_id:
        panel = db.get_api_panel_data(version_id, filters_tuple)
    else:
        panel = db.get_panel_data(filters_tuple)
    return leverage_predictor_sample_means(panel)


try:
    with st.spinner("Loading..."):
        coefs = compute_coefficients(ft, _data_source, _version_id)
        means = get_sample_means(ft, _data_source, _version_id)
except Exception as _e:
    st.error(f"Failed to load data. Please refresh. ({_e})")
    st.stop()

if db.is_cmie_lab_enabled() and _data_source == "cmie" and _version_id:
    st.caption(f"Regression fit on **CMIE import** (version `{_version_id[:16]}…`, n={coefs.get('n_obs', 0):,}).")
elif coefs.get("n_obs", 0) == 0:
    st.caption("Insufficient observations for OLS after filters — using fallback coefficients.")

# ── Sliders ──
st.markdown("#### Adjust Firm Characteristics")
sc1, sc2, sc3 = st.columns(3)

with sc1:
    prof_val = st.slider("Profitability (%)", -20.0, 60.0, float(_sprefs.get("prof_val", means.get("prof", 10.0))), 0.5)
    tang_val = st.slider("Tangibility (%)", 0.0, 95.0, float(_sprefs.get("tang_val", means.get("tang", 30.0))), 0.5)

with sc2:
    tax_val  = st.slider("Tax Rate (%)", -50.0, 80.0, float(_sprefs.get("tax_val",  means.get("tax",  20.0))), 0.5)
    size_val = st.slider("Log Firm Size", 0.0, 15.0,  float(_sprefs.get("size_val", means.get("log_size", 7.0))), 0.1)

with sc3:
    ts_val   = st.slider("Tax Shield", 0.0, 50.0, float(_sprefs.get("ts_val", means.get("tax_shield", 5.0))), 0.5)
    dvnd_raw = means.get("dvnd", 2.0)
    dvnd_default = float(dvnd_raw) if dvnd_raw is not None and not (isinstance(dvnd_raw, float) and np.isnan(dvnd_raw)) else 2.0
    dvnd_val = st.slider("Dividend (%)", 0.0, 30.0, float(_sprefs.get("dvnd_val", dvnd_default)), 0.5)

# ── Prediction ──
contributions = {
    "Intercept": coefs["intercept"],
    "Profitability": coefs["profitability"] * prof_val,
    "Tangibility": coefs["tangibility"] * tang_val,
    "Tax": coefs["tax"] * tax_val,
    "Firm Size": coefs["log_size"] * size_val,
    "Tax Shield": coefs["tax_shield"] * ts_val,
    "Dividend": coefs["dividend"] * dvnd_val,
}
predicted = sum(contributions.values())
predicted = max(0, predicted)  # leverage can't be negative

st.divider()

# ── Results row ──
res_left, res_right = st.columns([1, 2])

with res_left:
    st.markdown("#### 🎯 Model Forecast")
    st.markdown(render_bento_kpi(
        title="Predicted Leverage",
        value=format_pct(predicted),
        delta=f"{predicted - 21.0:+.1f}pp vs sample mean",
        percentile=min(100.0, max(0.0, predicted * 2.0)),
        tag=f"R² = {coefs.get('r_squared', 0):.3f}",
        stroke_color="#6366F1" if predicted <= 35 else "#F43F5E"
    ), unsafe_allow_html=True)

    st.markdown("**Model Specification**")
    st.caption(f"Panel sample size: {coefs.get('n_obs', 0):,} observations")

    st.markdown("**Equation**")
    eq_parts = [f"{coefs['intercept']:.2f}"]
    predictors = ["profitability", "tangibility", "tax", "log_size", "tax_shield", "dividend"]
    labels_map = {"profitability": "Prof", "tangibility": "Tang", "tax": "Tax",
                  "log_size": "LogSize", "tax_shield": "TaxShield", "dividend": "Dvnd"}
    for p in predictors:
        sign = "+" if coefs[p] >= 0 else ""
        eq_parts.append(f"{sign}{coefs[p]:.3f}*{labels_map[p]}")
    st.code("Lev = " + " ".join(eq_parts), language=None)

    # ── Citation Generator ──
    _cite_yr = filters.get("year_range", (2001, 2024))
    _cite_panel = panel_label(_panel)
    _cite_obs = coefs.get("n_obs", 0)
    _cite_r2 = coefs.get("r_squared", 0)
    _cite_url = "https://lifecycle-leverage-779655496440.us-east1.run.app"

    _apa_text = (
        f"Kumar, S. (2024). Scenario analysis of capital structure determinants "
        f"[Dataset]. LifeCycle Leverage Dashboard. {_cite_url} "
        f"(OLS Pooled regression; panel: {_cite_panel}, "
        f"{_cite_yr[0]}–{_cite_yr[1]}, {_cite_obs:,} obs, R²={_cite_r2:.3f}; "
        f"predicted leverage: {predicted:.1f}%)"
    )
    _latex_text = (
        r"\cite{kumar2024lifecycle} scenario analysis, OLS, "
        f"{_cite_panel} {_cite_yr[0]}--{_cite_yr[1]}, "
        f"${_cite_obs:,}$ obs, $R^2={_cite_r2:.3f}$, "
        r"$\hat{\text{Lev}}=" + f"{predicted:.1f}" + r"\%$."
    )

    with st.expander("📋 Cite this result"):
        st.caption("Copy the citation in your preferred format:")
        st.markdown("**APA**")
        st.code(_apa_text, language=None)
        st.markdown("**LaTeX**")
        st.code(_latex_text, language=None)

    st.divider()
    audit_trail_download_button(
        page="Scenarios",
        filters=filters,
        model_spec={
            "estimator": "OLS",
            "dep_var": "leverage",
            "indep_vars": ["profitability", "tangibility", "tax", "log_size", "tax_shield", "dividend"],
            "r_squared": coefs.get("r_squared", 0),
            "coefficients": {k: coefs[k] for k in ["intercept", "profitability", "tangibility", "tax", "log_size", "tax_shield", "dividend"] if k in coefs},
        },
        n_obs=coefs.get("n_obs", 0),
        n_firms=0,
        username=_username,
    )

with res_right:
    st.markdown("#### Contribution Waterfall")
    names = list(contributions.keys()) + ["Predicted"]
    values = list(contributions.values()) + [predicted]
    measures = ["relative"] * len(contributions) + ["total"]

    fig_wf = go.Figure(go.Waterfall(
        name="", orientation="v",
        measure=measures,
        x=names, y=values,
        connector=dict(line=dict(color="#D1D5DB", width=1)),
        increasing=dict(marker_color=PRIMARY),
        decreasing=dict(marker_color="#EF4444"),
        totals=dict(marker_color=SECONDARY),
        text=[f"{v:+.1f}" if m != "total" else f"{v:.1f}" for v, m in zip(values, measures)],
        textposition="outside",
    ))
    fig_wf.update_layout(**plotly_layout("Determinant Contributions to Leverage", height=420))
    st.plotly_chart(fig_wf, use_container_width=True, config=PLOTLY_CONFIG)
    chart_download_button(fig_wf, "scenario_waterfall.png")

    # Dynamic scenario interpretation
    insights = []
    if predicted > 40:
        insights.append(f"Predicted leverage of **{predicted:.1f}%** is **high** — indicates elevated financial risk at these parameter settings.")
    elif predicted < 10:
        insights.append(f"Predicted leverage of **{predicted:.1f}%** is **very low** — the firm may have untapped debt capacity for growth financing.")
    else:
        insights.append(f"Predicted leverage of **{predicted:.1f}%** is within normal range for Indian corporates.")

    # Identify which factor contributes most
    contrib_abs = {k: abs(v) for k, v in contributions.items() if k != "Intercept"}
    top_factor = max(contrib_abs, key=contrib_abs.get)
    top_val = contributions[top_factor]
    insights.append(f"**{top_factor}** is the dominant driver ({top_val:+.1f}pp) — {'pushing leverage up' if top_val > 0 else 'pulling leverage down'}.")

    actions = []
    if top_factor == "Profitability" and top_val < -5:
        actions.append("High profitability is suppressing leverage. This firm can self-fund — avoid unnecessary debt.")
    elif top_factor == "Tangibility" and top_val > 5:
        actions.append("Tangible assets are driving leverage up via collateral availability. Ensure debt is productively deployed.")
    actions.append("Adjust sliders to simulate scenarios: 'What if profitability drops 5%?' or 'What if the firm doubles in size?'")

    _render_insight_box("Scenario Interpretation", insights, actions,
        "Dynamic analysis of the current slider settings and their leverage implications.")

    # ── AI Scenario Narrative ──
    with st.expander("🤖 AI Insights", expanded=False):
        _s_key = "scenario_ai"
        if st.button("Generate AI Analysis", key="p3_ai_gen"):
            _user_role = (st.session_state.get("user") or {}).get("role", "viewer")
            _citations = st.session_state.get("p19_citations", False)
            _summary = {
                "Predicted leverage": f"{pred_lev:.2f}%",
                "Top driver": top_factor,
                "Driver effect": f"{top_val:+.2f}pp",
                "Profitability input": f"{prof_val:.2f}",
                "Tangibility input": f"{tang_val:.2f}",
                "Size input": f"{size_val:.2f}",
            }
            with st.spinner("Generating scenario narrative..."):
                st.session_state[_s_key] = "".join(
                    generate_page_insights("scenarios", _summary, st.session_state.filters,
                                           role=_user_role, citations=_citations)
                )
        if st.session_state.get(_s_key):
            st.markdown(st.session_state[_s_key])

st.divider()

# ── Compare with real company ──
st.markdown("#### Compare with a Real Company")
try:
    with st.spinner("Loading..."):
        companies_df = db.get_companies()
except Exception as _e:
    st.error(f"Could not load companies: {_e}")
    st.stop()
comp_name = st.selectbox("Select company to compare", companies_df["company_name"].tolist(), index=0)
comp_code = int(companies_df[companies_df["company_name"] == comp_name]["company_code"].iloc[0])
use_cmie_series = (
    db.is_cmie_lab_enabled()
    and getattr(st.session_state, "data_source_mode", "sqlite") == "cmie"
    and db.get_current_api_version()
)
try:
    with st.spinner("Loading..."):
        if use_cmie_series:
            comp_df = db.get_active_financials(ft)
            comp_df = comp_df[comp_df["company_code"] == comp_code].sort_values("year")
        else:
            comp_df = db.get_company_detail(comp_code)
except Exception as _e:
    st.error(f"Could not load company data: {_e}")
    st.stop()

if not comp_df.empty:
    actual_avg = comp_df["leverage"].mean()
    cc1, cc2, cc3 = st.columns(3)
    with cc1:
        st.metric("Predicted (Scenario)", format_pct(predicted))
    with cc2:
        st.metric(f"Actual Avg ({comp_name})", format_pct(actual_avg))
    with cc3:
        diff = predicted - actual_avg
        st.metric("Difference", f"{diff:+.1f}pp",
                  delta="Over-predicted" if diff > 0 else "Under-predicted")

# ── Persist user widget state ─────────────────────────────────────────────
if _username:
    db.save_user_pref(_username, "scenarios", {
        "prof_val": prof_val, "tang_val": tang_val, "tax_val": tax_val,
        "size_val": size_val, "ts_val": ts_val,     "dvnd_val": dvnd_val,
    })
