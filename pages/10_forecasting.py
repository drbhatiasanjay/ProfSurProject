"""
Leverage Forecasting — LSTM/GRU time-series prediction per firm.
"""

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import numpy as np
import db
from helpers import plotly_layout, format_pct, PRIMARY, SECONDARY, ACCENT
try:
    from models.timeseries import run_full_forecast, forecast_firm
    HAS_TORCH = True
except ImportError:
    HAS_TORCH = False

filters = st.session_state.filters
ft = db.filters_to_tuple(filters)

st.markdown("### Leverage Forecasting")
st.caption("LSTM/GRU neural networks trained on 5-year firm sequences. Temporal split: train ≤2018, validate 2019-2021, test 2022+.")

if not HAS_TORCH:
    st.warning("PyTorch is not installed. Forecasting requires `pip install torch` to run LSTM/GRU models.")
    st.stop()

with st.expander("ℹ️ About these models — parameters & interpretation"):
    st.markdown("""
**Why Neural Network Forecasting for Capital Structure?**

Capital structure evolves over time — a firm's leverage this year depends on its trajectory over the past 3-5 years. LSTM/GRU networks are designed to learn these **sequential patterns**: how profitability trends, investment cycles, and debt repayment schedules create momentum in leverage.

**What these models measure:**
- **LSTM** reads the last N years of a firm's financials and predicts next year's leverage. It learns patterns like "3 consecutive years of declining profitability typically precede a leverage spike."
- **GRU** is a lighter variant — often equally accurate for short sequences with small sample sizes.

**Parameters and why they're set conservatively:**
- *Hidden dim = 32*: Small to prevent memorizing 401 firms
- *Dropout = 0.3*: Forces generalization
- *Temporal split*: Train ≤2018, test 2022+ — no future leakage

**Intelligence this provides:**
1. **Forward-looking leverage estimates**: "Based on Tata Steel's last 5 years, we predict 38% leverage in 2025"
2. **Trend detection**: The model learns if a firm is on a deleveraging or leveraging-up trajectory
3. **Early warning**: Rising predicted leverage signals emerging financial stress before it shows in ratios

**Critical caveat:** With 401 firms, neural networks are data-hungry models in a data-scarce setting. Always compare against the naive baseline (predicting the mean). If improvement is < 5%, the forecast adds minimal value.
""")

st.warning("**Small sample caveat:** With 401 firms, neural network predictions should be interpreted directionally. Always compare against the naive baseline.", icon="⚠️")

# Settings
col_set, col_info = st.columns([1, 2])
with col_set:
    model_type = st.radio("Model", ["LSTM", "GRU"], index=0, horizontal=True)
    seq_len = st.slider("Sequence Length (years)", 3, 8, 5)

panel_df = db.get_panel_data(ft)
if panel_df.empty:
    st.warning("No data. Adjust filters.")
    st.stop()

# Train model
if "forecast_result" not in st.session_state:
    st.session_state.forecast_result = None

if st.session_state.forecast_result is None:
    st.markdown(f"""
**How this works:**

1. The model reads each firm's **last {seq_len} years** of financials (profitability, tangibility, size, tax shield, leverage)
2. It learns sequential patterns: "3 years of declining profitability usually precedes a leverage spike"
3. **Temporal split**: Train on 2001-2018, validate 2019-2021, test 2022+ (no future data leakage)
4. After training (~30-60 seconds), you'll see:
   - **RMSE comparison** vs naive baseline (predicting the mean)
   - **Training curve** — did the model learn or overfit?
   - **Actual vs Predicted** scatter on the test set
   - **Firm-level forecast** — select any company to see 1-3 year leverage projections
""")

if st.button("Train Forecast Model", type="primary"):
    progress = st.progress(0, "Starting...")
    result = run_full_forecast(
        panel_df, seq_len=seq_len, model_type=model_type,
        progress_callback=lambda p, t: progress.progress(p, t),
    )
    st.session_state.forecast_result = result
    progress.empty()

result = st.session_state.forecast_result
if result is None:
    st.stop()

if "error" in result:
    st.error(result["error"])
    st.stop()

# ── Results ──
st.divider()

# Metrics comparison
mc1, mc2, mc3, mc4 = st.columns(4)
with mc1:
    st.metric(f"{result['model_type']} RMSE", f"{result['test_metrics']['rmse']:.2f}")
with mc2:
    st.metric("Naive RMSE", f"{result['naive_metrics']['rmse']:.2f}")
with mc3:
    improvement = (1 - result['test_metrics']['rmse'] / result['naive_metrics']['rmse']) * 100
    st.metric("Improvement", f"{improvement:+.1f}%")
with mc4:
    st.metric("Test R²", f"{result['test_metrics']['r2']:.4f}")

if result['test_metrics']['rmse'] >= result['naive_metrics']['rmse']:
    st.warning("Model does NOT beat naive baseline. Use with extreme caution.")

# Training curves
tc1, tc2 = st.columns(2)
with tc1:
    loss_df = pd.DataFrame({
        "Epoch": list(range(len(result["train_losses"]))),
        "Train": result["train_losses"],
        "Validation": result["val_losses"],
    }).melt(id_vars="Epoch", var_name="Set", value_name="MSE Loss")
    fig_loss = px.line(loss_df, x="Epoch", y="MSE Loss", color="Set",
                       color_discrete_map={"Train": PRIMARY, "Validation": ACCENT})
    fig_loss.update_layout(**plotly_layout("Training Curve", height=350))
    fig_loss.add_vline(x=result["best_epoch"], line_dash="dash", line_color="#9CA3AF",
                       annotation_text=f"Best epoch: {result['best_epoch']}")
    st.plotly_chart(fig_loss, use_container_width=True)

with tc2:
    # Actual vs predicted
    fig_ap = px.scatter(x=result["test_actuals"], y=result["test_preds"],
                        opacity=0.4, labels={"x": "Actual (%)", "y": "Predicted (%)"})
    fig_ap.add_trace(go.Scatter(x=[0, 80], y=[0, 80], mode="lines",
                                line=dict(dash="dash", color="#9CA3AF"), showlegend=False))
    fig_ap.update_layout(**plotly_layout("Actual vs Predicted (Test Set)", height=350))
    st.plotly_chart(fig_ap, use_container_width=True)

# ── Firm-level forecast ──
st.divider()
st.markdown("#### Firm-Level Forecast")
companies_df = db.get_companies()
sel_firm = st.selectbox("Select company", companies_df["company_name"].tolist(), index=0, key="fc_firm")
firm_code = int(companies_df[companies_df["company_name"] == sel_firm]["company_code"].iloc[0])
firm_df = db.get_company_detail(firm_code)

if not firm_df.empty and result.get("model"):
    features = result["features"]
    available_feats = [f for f in features if f in firm_df.columns]
    if len(available_feats) == len(features):
        forecasts = forecast_firm(result["model"], firm_df, features, seq_len=result["seq_len"], n_steps=3)

        if forecasts:
            # Plot historical + forecast
            hist = firm_df[["year", "leverage"]].dropna()
            fc_df = pd.DataFrame(forecasts)

            fig_fc = go.Figure()
            fig_fc.add_trace(go.Scatter(
                x=hist["year"], y=hist["leverage"],
                mode="lines+markers", name="Historical",
                line=dict(color=PRIMARY, width=2), marker=dict(size=5),
            ))
            fig_fc.add_trace(go.Scatter(
                x=fc_df["year"], y=fc_df["predicted_leverage"],
                mode="lines+markers", name="Forecast",
                line=dict(color=ACCENT, width=2, dash="dash"), marker=dict(size=8, symbol="diamond"),
            ))
            fig_fc.update_layout(**plotly_layout(f"{sel_firm} — Leverage Forecast", height=400))
            st.plotly_chart(fig_fc, use_container_width=True)

            st.dataframe(fc_df, hide_index=True, use_container_width=True)
        else:
            st.info(f"Not enough historical data for {sel_firm} (need {seq_len}+ years).")
    else:
        st.info("Missing required features for this firm.")
