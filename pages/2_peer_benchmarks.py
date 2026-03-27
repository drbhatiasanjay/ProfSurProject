"""
Peer Benchmarks — Company vs industry/stage averages, box plots, radar chart.
"""

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import numpy as np
import db
from helpers import (
    winsorize, plotly_layout, event_bands, STAGE_COLORS, STAGE_ORDER,
    PRIMARY, SECONDARY, ACCENT, PLOTLY_CONFIG,
)

filters = st.session_state.filters
ft = db.filters_to_tuple(filters)

st.markdown("### Peer Benchmarks")
st.caption("Compare a company against its industry and life-stage peers.")

# ── Company selector ──
companies_df = db.get_companies()
selected = st.selectbox(
    "Select a company",
    options=companies_df["company_name"].tolist(),
    index=0,
)
company_row = companies_df[companies_df["company_name"] == selected].iloc[0]
company_code = int(company_row["company_code"])
company_industry = company_row["industry_group"]

st.info(f"**{selected}** | NSE: {company_row['nse_symbol']} | Industry: {company_industry}")

# ── Load data ──
with st.spinner("Loading benchmarks..."):
    company_df = db.get_company_detail(company_code)
    full_df = db.get_filtered_financials(ft)
    industry_df = full_df[full_df["industry_group"] == company_industry]

if company_df.empty:
    st.warning("No data available for this company.")
    st.stop()

st.divider()

# ── Row 1: Company vs Industry Avg (leverage over time) ──
left, right = st.columns(2)

with left:
    st.markdown("#### Leverage: Company vs Industry Average")
    industry_avg = industry_df.groupby("year")["leverage"].mean().reset_index()
    industry_avg.columns = ["year", "industry_avg"]

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=company_df["year"], y=company_df["leverage"],
        name=selected, mode="lines+markers",
        line=dict(color=PRIMARY, width=3),
        marker=dict(size=6),
    ))
    fig.add_trace(go.Scatter(
        x=industry_avg["year"], y=industry_avg["industry_avg"],
        name=f"Industry Avg ({company_industry})",
        mode="lines", line=dict(color=ACCENT, width=2, dash="dash"),
    ))
    fig.update_layout(**plotly_layout(height=380))
    fig = event_bands(fig)
    st.plotly_chart(fig, use_container_width=True, config=PLOTLY_CONFIG)

with right:
    st.markdown("#### Profitability: Company vs Industry Average")
    ind_prof_avg = industry_df.groupby("year")["profitability"].mean().reset_index()
    ind_prof_avg.columns = ["year", "industry_avg"]

    fig2 = go.Figure()
    fig2.add_trace(go.Scatter(
        x=company_df["year"], y=company_df["profitability"],
        name=selected, mode="lines+markers",
        line=dict(color=PRIMARY, width=3), marker=dict(size=6),
    ))
    fig2.add_trace(go.Scatter(
        x=ind_prof_avg["year"], y=ind_prof_avg["industry_avg"],
        name=f"Industry Avg",
        mode="lines", line=dict(color=ACCENT, width=2, dash="dash"),
    ))
    fig2.update_layout(**plotly_layout(height=380))
    fig2 = event_bands(fig2)
    st.plotly_chart(fig2, use_container_width=True, config=PLOTLY_CONFIG)

st.divider()

# ── Row 2: Box plots + Radar ──
left2, right2 = st.columns(2)

with left2:
    st.markdown("#### Leverage Distribution by Life Stage")
    box_df = full_df[["life_stage", "leverage"]].dropna()
    box_df["leverage"] = winsorize(box_df["leverage"])

    fig_box = px.box(
        box_df, x="life_stage", y="leverage",
        color="life_stage",
        color_discrete_map=STAGE_COLORS,
        category_orders={"life_stage": STAGE_ORDER},
        labels={"leverage": "Leverage (%)", "life_stage": ""},
    )

    # Mark the selected company's average
    comp_avg_lev = company_df["leverage"].mean()
    comp_stage = company_df["life_stage"].mode().iloc[0] if not company_df["life_stage"].mode().empty else None
    if comp_stage and comp_avg_lev is not None:
        fig_box.add_trace(go.Scatter(
            x=[comp_stage], y=[comp_avg_lev],
            mode="markers", name=selected,
            marker=dict(size=14, color="#111827", symbol="diamond", line=dict(width=2, color="white")),
        ))

    fig_box.update_layout(**plotly_layout(height=420))
    st.plotly_chart(fig_box, use_container_width=True, config=PLOTLY_CONFIG)

with right2:
    st.markdown("#### Multi-Determinant Profile (Radar)")

    metrics = ["profitability", "tangibility", "tax", "firm_size", "tax_shield", "cash_holdings"]
    labels = ["Profitability", "Tangibility", "Tax", "Firm Size", "Tax Shield", "Cash Holdings"]

    # Normalize 0-100 using full dataset min-max
    norms = {}
    for m in metrics:
        col = full_df[m].dropna()
        norms[m] = (col.min(), col.max())

    def normalize(val, m):
        mn, mx = norms[m]
        if mx == mn:
            return 50
        return max(0, min(100, (val - mn) / (mx - mn) * 100))

    # Company values
    comp_vals = [normalize(company_df[m].mean(), m) for m in metrics]
    # Industry avg
    ind_vals = [normalize(industry_df[m].mean(), m) for m in metrics]
    # Life stage avg
    if comp_stage:
        stage_df = full_df[full_df["life_stage"] == comp_stage]
        stage_vals = [normalize(stage_df[m].mean(), m) for m in metrics]
    else:
        stage_vals = [50] * len(metrics)

    fig_radar = go.Figure()
    fig_radar.add_trace(go.Scatterpolar(
        r=comp_vals + [comp_vals[0]], theta=labels + [labels[0]],
        fill="toself", name=selected, fillcolor="rgba(13,148,136,0.15)",
        line=dict(color=PRIMARY, width=2),
    ))
    fig_radar.add_trace(go.Scatterpolar(
        r=ind_vals + [ind_vals[0]], theta=labels + [labels[0]],
        fill="toself", name="Industry Avg", fillcolor="rgba(249,115,22,0.1)",
        line=dict(color=ACCENT, width=2, dash="dash"),
    ))
    fig_radar.add_trace(go.Scatterpolar(
        r=stage_vals + [stage_vals[0]], theta=labels + [labels[0]],
        fill="toself", name=f"Stage Avg ({comp_stage})", fillcolor="rgba(99,102,241,0.1)",
        line=dict(color=SECONDARY, width=2, dash="dot"),
    ))
    fig_radar.update_layout(**plotly_layout(height=420))
    fig_radar.update_layout(
        polar=dict(radialaxis=dict(visible=True, range=[0, 100])),
        legend=dict(orientation="h", y=-0.15),
    )
    st.plotly_chart(fig_radar, use_container_width=True, config=PLOTLY_CONFIG)
