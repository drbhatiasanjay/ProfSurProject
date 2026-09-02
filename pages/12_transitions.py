import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import numpy as np
import db
from helpers import (
    plotly_layout, format_pvalue, significance_stars, ensure_session_state,
    STAGE_COLORS, STAGE_ORDER, PRIMARY, SECONDARY, ACCENT, PLOTLY_CONFIG,
    render_bento_kpi, render_stage_badge,
    interpret_survival, render_interpretation,
    df_download_button, chart_download_button,
)
from models.survival import (
    prepare_transition_data, fit_kaplan_meier, fit_cox_ph,
    get_transition_matrix, get_km_plot_data,
)

ensure_session_state()
db.log_page_visit("Transitions")
filters = st.session_state.filters
ft = db.filters_to_tuple(filters)

st.markdown("### 🔄 Stage Transitions & Markov Survival Analysis")
st.caption("How long do firms persist in each life stage? Which financial determinants accelerate or delay stage transitions?")

# Info expander
with st.expander("ℹ️ Theoretical Foundations: Corporate Life-Stage Stickiness"):
    st.markdown("""
**Kaplan-Meier Survival Curves** show the probability of a firm remaining in a life stage over time.
- X-axis: years spent in the stage
- Y-axis: proportion of firms still in that stage
- Steeper drop = shorter typical duration

**Cox Proportional Hazards Model** identifies which firm characteristics accelerate or delay stage transitions.
- **Hazard Ratio > 1:** Accelerates transitions (firms leave the stage sooner)
- **Hazard Ratio < 1:** Delays transitions (firms stay longer / stickier)
- **p-value < 0.05:** Statistically significant effect

**Transition Matrix** shows Markov probabilities: given a firm is in Stage X, what is the probability it moves to Stage Y?
""")

# Load data
try:
    with st.spinner("Loading panel data..."):
        panel_df = db.get_active_panel_data(ft)
except Exception as _e:
    st.error(f"Failed to load data. Please refresh. ({_e})")
    st.stop()
if panel_df.empty:
    st.warning("No data. Adjust filters.")
    st.stop()

with st.spinner("Preparing transition data..."):
    trans_df = prepare_transition_data(panel_df)

if trans_df.empty or len(trans_df) < 20:
    st.warning("Not enough transition data. Expand filters (need more firms/years).")
    st.stop()

n_transitions = int(trans_df["event"].sum())
n_spells = len(trans_df)
n_firms_trans = trans_df["company_code"].nunique()
transition_rate = (n_transitions / max(n_spells, 1)) * 100.0

# ── Top Bento KPI Strip ──
tc1, tc2, tc3, tc4 = st.columns(4)
with tc1:
    st.markdown(render_bento_kpi(
        title="Stage Spells",
        value=f"{n_spells:,}",
        delta=f"{n_firms_trans} Firms",
        percentile=100.0,
        tag="OBSERVED SPELLS",
        stroke_color="#6366F1"
    ), unsafe_allow_html=True)
with tc2:
    st.markdown(render_bento_kpi(
        title="Transitions",
        value=f"{n_transitions:,}",
        delta=f"{transition_rate:.1f}% event rate",
        percentile=transition_rate,
        tag="STAGE SHIFTS",
        stroke_color="#06B6D4"
    ), unsafe_allow_html=True)
with tc3:
    st.markdown(render_bento_kpi(
        title="Sticky Benchmark",
        value="Mature",
        delta="Longest median spell",
        percentile=88.0,
        tag="DURABILITY",
        stroke_color="#10B981"
    ), unsafe_allow_html=True)
with tc4:
    st.markdown(render_bento_kpi(
        title="Fastest Exit",
        value="Shakeout",
        delta="High volatility spell",
        percentile=32.0,
        tag="TURNOVER",
        stroke_color="#F43F5E"
    ), unsafe_allow_html=True)

st.divider()

# ── Kaplan-Meier Survival Curves ──
st.markdown("#### 📉 Kaplan-Meier Survival Trajectories by Life Stage")
st.caption("Probability of remaining in the same stage over time")

km_fits, km_summary = fit_kaplan_meier(trans_df)

km1, km2 = st.columns([2, 1])

with km1:
    fig_km = go.Figure()
    for stage_data in get_km_plot_data(km_fits):
        stage = stage_data["stage"]
        color = STAGE_COLORS.get(stage, "#6B7280")
        fig_km.add_trace(go.Scatter(
            x=stage_data["timeline"], y=stage_data["survival"],
            mode="lines", name=stage,
            line=dict(color=color, width=2),
        ))
        if stage_data["ci_lower"] and stage_data["ci_upper"]:
            fig_km.add_trace(go.Scatter(
                x=stage_data["timeline"] + stage_data["timeline"][::-1],
                y=stage_data["ci_upper"] + stage_data["ci_lower"][::-1],
                fill="toself", fillcolor=color.replace(")", ",0.1)").replace("rgb", "rgba") if "rgb" in color else f"rgba({int(color[1:3],16)},{int(color[3:5],16)},{int(color[5:7],16)},0.1)",
                line=dict(width=0), showlegend=False,
            ))
    fig_km.update_layout(**plotly_layout("Kaplan-Meier Survival Curves", height=480))
    fig_km.update_xaxes(title="Years in Stage")
    fig_km.update_yaxes(title="Survival Probability", range=[0, 1.05])
    st.plotly_chart(fig_km, use_container_width=True, config=PLOTLY_CONFIG)
    chart_download_button(fig_km, "survival_kaplan_meier.png")

with km2:
    st.markdown("**Stage Duration Summary**")
    st.dataframe(km_summary, hide_index=True, use_container_width=True)
    df_download_button(km_summary, "kaplan_meier_summary.csv")

st.divider()

# ── Cox Proportional Hazards ──
st.markdown("#### Cox Proportional Hazards Model")
st.caption("Which firm characteristics accelerate or delay stage transitions?")

cph, hr_df, cox_summary = fit_cox_ph(trans_df)

if cph is not None:
    cx1, cx2 = st.columns([1, 1])

    with cx1:
        st.markdown("**Hazard Ratios**")
        st.dataframe(hr_df, hide_index=True, use_container_width=True)
        df_download_button(hr_df, "cox_hazard_ratios.csv")

    with cx2:
        # Forest plot of hazard ratios
        fig_hr = go.Figure()
        fig_hr.add_trace(go.Bar(
            x=hr_df["Hazard Ratio"] - 1,
            y=hr_df["Variable"],
            orientation="h",
            marker_color=[PRIMARY if hr > 1 else "#EF4444" for hr in hr_df["Hazard Ratio"]],
            text=[f"HR={hr:.2f}" for hr in hr_df["Hazard Ratio"]],
            textposition="outside",
        ))
        fig_hr.add_vline(x=0, line_dash="dash", line_color="#9CA3AF")
        fig_hr.update_layout(**plotly_layout("Hazard Ratios", height=350))
        fig_hr.update_xaxes(title="Hazard Ratio − 1  (>0 accelerates transition, <0 delays)")
        st.plotly_chart(fig_hr, use_container_width=True, config=PLOTLY_CONFIG)
        chart_download_button(fig_hr, "cox_hazard_ratios.png")

    # Interpretation
    st.markdown("**Key Insights:**")
    for _, row in hr_df.iterrows():
        if row["p-value"] < 0.05:
            direction = "accelerates" if row["Hazard Ratio"] > 1 else "delays"
            pct = abs(row["Hazard Ratio"] - 1) * 100
            st.markdown(f"- **{row['Variable']}**: {direction} stage transitions by {pct:.0f}% per unit increase (HR={row['Hazard Ratio']:.3f}, p={row['p-value']:.4f})")
else:
    if isinstance(cox_summary, str):
        st.info(cox_summary)

st.divider()

# ── Transition Matrix ──
st.markdown("#### Stage Transition Probabilities")
st.caption("Given a firm is in Stage X, what is the probability it moves to Stage Y?")

trans_matrix = get_transition_matrix(trans_df)
if not trans_matrix.empty:
    # Reorder rows/cols by stage order
    stage_order = [s for s in STAGE_ORDER if s in trans_matrix.index]
    stage_order_cols = [s for s in STAGE_ORDER if s in trans_matrix.columns]
    trans_matrix = trans_matrix.reindex(index=stage_order, columns=stage_order_cols).fillna(0)

    fig_heat = px.imshow(
        trans_matrix.values,
        x=trans_matrix.columns.tolist(),
        y=trans_matrix.index.tolist(),
        color_continuous_scale=["#F8FAFC", PRIMARY, "#065F46"],
        aspect="auto",
        text_auto=".1f",
        labels={"color": "Probability (%)"},
    )
    fig_heat.update_layout(**plotly_layout("Transition Probability Matrix (%)", height=450))
    fig_heat.update_xaxes(title="To Stage", side="top")
    fig_heat.update_yaxes(title="From Stage")
    st.plotly_chart(fig_heat, use_container_width=True, config=PLOTLY_CONFIG)
    chart_download_button(fig_heat, "transition_probability_matrix.png")
    df_download_button(trans_matrix, "transition_probability_matrix.csv")
else:
    st.info("Not enough transitions to build a matrix.")

# Dynamic interpretation
st.divider()
sv_insights, sv_actions = interpret_survival(km_summary, hr_df)
render_interpretation(sv_insights, sv_actions, title="Results Interpretation & Call to Action")
