"""
Scenarios — Determinant sliders, predicted leverage, waterfall chart, company comparison.
"""

import streamlit as st
import plotly.graph_objects as go
import pandas as pd
import numpy as np
import db
from helpers import plotly_layout, format_pct, PRIMARY, SECONDARY, ACCENT, STAGE_COLORS, PLOTLY_CONFIG

filters = st.session_state.filters
ft = db.filters_to_tuple(filters)

st.markdown("### Scenario Analysis")
st.caption("Adjust firm characteristics to see predicted leverage based on panel regression coefficients.")

# ── Compute OLS coefficients from the data ──
@st.cache_data(ttl=3600)
def compute_coefficients():
    """Run simple OLS on the full dataset to get coefficients."""
    conn = db.get_connection()
    df = pd.read_sql("""
        SELECT leverage, profitability, tangibility, tax, log_size, tax_shield, dividend
        FROM financials
        WHERE leverage IS NOT NULL
          AND profitability IS NOT NULL
          AND tangibility IS NOT NULL
          AND tax IS NOT NULL
          AND log_size IS NOT NULL
    """, conn)
    conn.close()
    df = df.dropna()

    # Simple OLS using numpy (no statsmodels dependency)
    y = df["leverage"].values
    predictors = ["profitability", "tangibility", "tax", "log_size", "tax_shield", "dividend"]
    X = df[predictors].fillna(0).values
    X = np.column_stack([np.ones(len(X)), X])  # add intercept

    # OLS: beta = (X'X)^-1 X'y
    try:
        beta = np.linalg.lstsq(X, y, rcond=None)[0]
        coefs = {"intercept": beta[0]}
        for i, name in enumerate(predictors):
            coefs[name] = beta[i + 1]
        # R-squared
        y_hat = X @ beta
        ss_res = np.sum((y - y_hat) ** 2)
        ss_tot = np.sum((y - np.mean(y)) ** 2)
        coefs["r_squared"] = 1 - ss_res / ss_tot
        coefs["n_obs"] = len(df)
    except np.linalg.LinAlgError:
        coefs = {
            "intercept": 21.0, "profitability": -0.3, "tangibility": 0.15,
            "tax": -0.05, "log_size": 2.0, "tax_shield": 0.1, "dividend": -0.02,
            "r_squared": 0.0, "n_obs": 0,
        }
    return coefs

coefs = compute_coefficients()

# ── Get sample means for defaults ──
@st.cache_data(ttl=3600)
def get_sample_means():
    conn = db.get_connection()
    df = pd.read_sql("""
        SELECT AVG(profitability) as prof, AVG(tangibility) as tang,
               AVG(tax) as tax, AVG(log_size) as log_size,
               AVG(tax_shield) as tax_shield, AVG(dividend) as dvnd
        FROM financials
        WHERE leverage IS NOT NULL
    """, conn)
    conn.close()
    return df.iloc[0].to_dict()

means = get_sample_means()

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

st.divider()

# ── Compare with real company ──
st.markdown("#### Compare with a Real Company")
companies_df = db.get_companies()
comp_name = st.selectbox("Select company to compare", companies_df["company_name"].tolist(), index=0)
comp_code = int(companies_df[companies_df["company_name"] == comp_name]["company_code"].iloc[0])
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
