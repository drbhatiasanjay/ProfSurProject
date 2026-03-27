"""
Dashboard — KPI cards, lifecycle distribution, leverage trends, top 10, event impact.
"""

import streamlit as st
import plotly.express as px
import pandas as pd
import db
from helpers import (
    winsorize, format_pct, format_inr, format_number,
    plotly_layout, event_bands, STAGE_COLORS, STAGE_ORDER,
    PRIMARY, SECONDARY, ACCENT, PLOTLY_CONFIG,
)

filters = st.session_state.filters
ft = db.filters_to_tuple(filters)

# ── Load data ──
with st.spinner("Loading dashboard..."):
    df = db.get_filtered_financials(ft)
    stage_summary = db.get_life_stage_summary(ft)

if df.empty:
    st.warning("No data matches the current filters. Adjust the sidebar filters.")
    st.stop()

# ── Row 1: KPI Cards ──
st.markdown("### Key Metrics")
c1, c2, c3, c4 = st.columns(4)

n_companies = df["company_name"].nunique()
avg_lev = df["leverage"].mean()
med_lev = df["leverage"].median()
avg_prof = df["profitability"].mean()

# Compute deltas (current year vs prior year within range)
yr_min, yr_max = filters["year_range"]
if yr_max > yr_min:
    curr = df[df["year"] == yr_max]
    prev = df[df["year"] == yr_max - 1]
    lev_delta = curr["leverage"].mean() - prev["leverage"].mean() if not prev.empty and not curr.empty else None
    prof_delta = curr["profitability"].mean() - prev["profitability"].mean() if not prev.empty and not curr.empty else None
else:
    lev_delta = None
    prof_delta = None

with c1:
    st.metric("Companies", format_number(n_companies))
with c2:
    st.metric("Avg Leverage", format_pct(avg_lev),
              delta=f"{lev_delta:+.1f}pp" if lev_delta is not None else None)
with c3:
    st.metric("Median Leverage", format_pct(med_lev))
with c4:
    st.metric("Avg Profitability", format_pct(avg_prof),
              delta=f"{prof_delta:+.1f}pp" if prof_delta is not None else None)

c5, c6, c7, c8 = st.columns(4)
avg_tang = df["tangibility"].mean()
total_borr = df.sort_values("year").groupby("company_name")["borrowings"].last().sum()
dominant_stage = df["life_stage"].mode().iloc[0] if not df["life_stage"].mode().empty else "N/A"
n_obs = len(df)

with c5:
    st.metric("Avg Tangibility", format_pct(avg_tang))
with c6:
    st.metric("Total Borrowings", format_inr(total_borr))
with c7:
    st.metric("Dominant Stage", dominant_stage)
with c8:
    st.metric("Observations", format_number(n_obs))

st.divider()

# ── Row 2: Trend Line + Lifecycle Donut ──
left, right = st.columns([2, 1])

with left:
    st.markdown("### Leverage Trends by Life Stage")
    if not stage_summary.empty:
        # Sort by stage order for consistent coloring
        fig_trend = px.line(
            stage_summary,
            x="year", y="avg_leverage",
            color="life_stage",
            color_discrete_map=STAGE_COLORS,
            category_orders={"life_stage": STAGE_ORDER},
            labels={"avg_leverage": "Avg Leverage (%)", "year": "Year", "life_stage": "Life Stage"},
        )
        fig_trend.update_layout(**plotly_layout(height=420))
        fig_trend = event_bands(fig_trend)
        fig_trend.update_traces(line_width=2.5)
        st.plotly_chart(fig_trend, use_container_width=True, config=PLOTLY_CONFIG)
    else:
        st.info("No trend data available.")

with right:
    st.markdown("### Lifecycle Distribution")
    stage_counts = df["life_stage"].value_counts().reset_index()
    stage_counts.columns = ["life_stage", "count"]
    fig_pie = px.pie(
        stage_counts,
        names="life_stage", values="count",
        hole=0.45,
        color="life_stage",
        color_discrete_map=STAGE_COLORS,
        category_orders={"life_stage": STAGE_ORDER},
    )
    fig_pie.update_layout(**plotly_layout(height=420))
    fig_pie.update_traces(textinfo="percent+label", textposition="outside")
    st.plotly_chart(fig_pie, use_container_width=True, config=PLOTLY_CONFIG)

st.divider()

# ── Row 3: Top 10 + Event Impact ──
left2, right2 = st.columns([1, 1])

with left2:
    st.markdown("### Top 10 Most Leveraged Companies")
    top10 = db.get_top_leveraged(10, ft)
    if not top10.empty:
        top10["avg_leverage"] = winsorize(top10["avg_leverage"])
        top10 = top10.sort_values("avg_leverage", ascending=True)
        fig_bar = px.bar(
            top10,
            x="avg_leverage", y="company_name",
            orientation="h",
            color="life_stage",
            color_discrete_map=STAGE_COLORS,
            labels={"avg_leverage": "Avg Leverage (%)", "company_name": ""},
        )
        fig_bar.update_layout(**plotly_layout(height=400))
        st.plotly_chart(fig_bar, use_container_width=True, config=PLOTLY_CONFIG)
    else:
        st.info("No data.")

with right2:
    st.markdown("### Event Period Impact")
    overall_avg = df["leverage"].mean()

    # GFC impact
    gfc_df = df[df["gfc"] == 1]
    ibc_df = df[df["ibc_2016"] == 1]
    covid_df = df[df["covid_dummy"] == 1]

    ec1, ec2, ec3 = st.columns(3)
    with ec1:
        gfc_avg = gfc_df["leverage"].mean() if not gfc_df.empty else None
        st.metric(
            "GFC (2008-09)",
            format_pct(gfc_avg),
            delta=f"{gfc_avg - overall_avg:+.1f}pp" if gfc_avg is not None else None,
        )
        st.caption(f"{len(gfc_df)} obs")
    with ec2:
        ibc_avg = ibc_df["leverage"].mean() if not ibc_df.empty else None
        st.metric(
            "IBC (2016+)",
            format_pct(ibc_avg),
            delta=f"{ibc_avg - overall_avg:+.1f}pp" if ibc_avg is not None else None,
        )
        st.caption(f"{len(ibc_df)} obs")
    with ec3:
        covid_avg = covid_df["leverage"].mean() if not covid_df.empty else None
        st.metric(
            "COVID (2020-21)",
            format_pct(covid_avg),
            delta=f"{covid_avg - overall_avg:+.1f}pp" if covid_avg is not None else None,
        )
        st.caption(f"{len(covid_df)} obs")

    # Leverage by event period bar chart
    event_data = []
    event_data.append({"Period": "Overall", "Avg Leverage": overall_avg})
    if gfc_avg is not None:
        event_data.append({"Period": "GFC", "Avg Leverage": gfc_avg})
    if ibc_avg is not None:
        event_data.append({"Period": "IBC", "Avg Leverage": ibc_avg})
    if covid_avg is not None:
        event_data.append({"Period": "COVID", "Avg Leverage": covid_avg})

    if len(event_data) > 1:
        event_df = pd.DataFrame(event_data)
        fig_event = px.bar(
            event_df, x="Period", y="Avg Leverage",
            color="Period",
            color_discrete_map={"Overall": PRIMARY, "GFC": "#EF4444", "IBC": SECONDARY, "COVID": ACCENT},
        )
        fig_event.update_layout(**plotly_layout(height=280))
        fig_event.update_layout(showlegend=False)
        st.plotly_chart(fig_event, use_container_width=True, config=PLOTLY_CONFIG)
