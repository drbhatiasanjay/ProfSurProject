"""
Scenarios — Determinant sliders, predicted leverage, waterfall chart, company comparison.
"""

import streamlit as st
import plotly.graph_objects as go
import pandas as pd
import numpy as np
import db
from helpers import plotly_layout, format_pct, ensure_session_state, PRIMARY, SECONDARY, ACCENT, STAGE_COLORS, PLOTLY_CONFIG, _render_insight_box
from models.scenario_regression import compute_leverage_ols_coefs, leverage_predictor_sample_means

ensure_session_state()

# Reproducibility pin — scenario OLS coefficients come from the thesis panel.
filters = dict(st.session_state.filters)
filters["panel_mode"] = "thesis"
yr_min_t, yr_max_t = db.get_year_range("thesis")
yr_prev = filters.get("year_range", (yr_min_t, yr_max_t))
filters["year_range"] = (max(yr_prev[0], yr_min_t), min(yr_prev[1], yr_max_t))
ft = db.filters_to_tuple(filters)
_data_source = getattr(st.session_state, "data_source_mode", "sqlite")
_version_id = (
    db.get_current_api_version()
    if db.is_cmie_lab_enabled() and _data_source == "cmie"
    else None
)

st.markdown("### Scenario Analysis")
st.caption("Adjust firm characteristics to see predicted leverage based on panel regression coefficients.")

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


coefs = compute_coefficients(ft, _data_source, _version_id)
means = get_sample_means(ft, _data_source, _version_id)

if db.is_cmie_lab_enabled() and _data_source == "cmie" and _version_id:
    st.caption(f"Regression fit on **CMIE import** (version `{_version_id[:16]}…`, n={coefs.get('n_obs', 0):,}).")
elif coefs.get("n_obs", 0) == 0:
    st.caption("Insufficient observations for OLS after filters — using fallback coefficients.")

# ── Sliders ──
st.markdown("#### Adjust Firm Characteristics")
sc1, sc2, sc3 = st.columns(3)

with sc1:
    prof_val = st.slider("Profitability (%)", -20.0, 60.0, float(means.get("prof", 10.0)), 0.5)
    tang_val = st.slider("Tangibility (%)", 0.0, 95.0, float(means.get("tang", 30.0)), 0.5)

with sc2:
    tax_val = st.slider("Tax Rate (%)", -50.0, 80.0, float(means.get("tax", 20.0)), 0.5)
    size_val = st.slider("Log Firm Size", 0.0, 15.0, float(means.get("log_size", 7.0)), 0.1)

with sc3:
    ts_val = st.slider("Tax Shield", 0.0, 50.0, float(means.get("tax_shield", 5.0)), 0.5)
    dvnd_raw = means.get("dvnd", 2.0)
    dvnd_default = float(dvnd_raw) if dvnd_raw is not None and not (isinstance(dvnd_raw, float) and np.isnan(dvnd_raw)) else 2.0
    dvnd_val = st.slider("Dividend (%)", 0.0, 30.0, dvnd_default, 0.5)

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
    st.markdown("#### Predicted Leverage")
    st.metric("Predicted", format_pct(predicted), delta=f"{predicted - 21.0:+.1f}pp vs sample mean")

    st.markdown("**Model Info**")
    st.caption(f"R-squared: {coefs.get('r_squared', 0):.3f}")
    st.caption(f"Observations: {coefs.get('n_obs', 0):,}")

    st.markdown("**Equation**")
    eq_parts = [f"{coefs['intercept']:.2f}"]
    predictors = ["profitability", "tangibility", "tax", "log_size", "tax_shield", "dividend"]
    labels_map = {"profitability": "Prof", "tangibility": "Tang", "tax": "Tax",
                  "log_size": "LogSize", "tax_shield": "TaxShield", "dividend": "Dvnd"}
    for p in predictors:
        sign = "+" if coefs[p] >= 0 else ""
        eq_parts.append(f"{sign}{coefs[p]:.3f}*{labels_map[p]}")
    st.code("Lev = " + " ".join(eq_parts), language=None)

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

st.divider()

# ── Compare with real company ──
st.markdown("#### Compare with a Real Company")
companies_df = db.get_companies()
comp_name = st.selectbox("Select company to compare", companies_df["company_name"].tolist(), index=0)
comp_code = int(companies_df[companies_df["company_name"] == comp_name]["company_code"].iloc[0])
use_cmie_series = (
    db.is_cmie_lab_enabled()
    and getattr(st.session_state, "data_source_mode", "sqlite") == "cmie"
    and db.get_current_api_version()
)
if use_cmie_series:
    comp_df = db.get_active_financials(ft)
    comp_df = comp_df[comp_df["company_code"] == comp_code].sort_values("year")
else:
    comp_df = db.get_company_detail(comp_code)

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
