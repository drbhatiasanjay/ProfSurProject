"""
Dashboard — KPI cards, leverage over time, stage comparison, determinant decomposition, events.
"""

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import numpy as np
from scipy import stats
import db
from helpers import (
    winsorize, format_pct, format_inr, format_number, format_pvalue,
    plotly_layout, event_bands, new_badge, ensure_session_state, is_india_panel, STAGE_COLORS, STAGE_ORDER,
    PRIMARY, SECONDARY, ACCENT, PLOTLY_CONFIG,
    _render_insight_box, interpret_kpi_cards, interpret_leverage_trend,
    interpret_lifecycle_distribution, interpret_top_leveraged, interpret_event_impact,
)

ensure_session_state()
filters = st.session_state.filters
ft = db.filters_to_tuple(filters)
_india = is_india_panel(st.session_state.get("panel_mode", "latest"))

# ── Load data ──
with st.spinner("Loading dashboard..."):
    df = db.get_active_financials(ft)
    stage_summary = db.get_active_life_stage_summary(ft)

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

# ── Row 3: DataV2-era KPIs (NEW badge on each) ─────────────────────────────
# Introduced in DataV2 vintage ingest (2026-04-21). Hidden when panel_mode='thesis'.
_panel_mode = st.session_state.get("panel_mode", "latest")
if _panel_mode == "latest":
    c9, c10, c11, c12 = st.columns(4)
    latest_yr = int(df["year"].max()) if not df.empty else None
    try:
        n_indices = len(db.get_available_indices())
    except Exception:
        n_indices = 0
    _cmie_2025_rows = df[df.get("vintage", "").eq("cmie_2025")] if "vintage" in df.columns else df[df["year"] == 2025]
    n_cmie_firms = _cmie_2025_rows["company_name"].nunique() if not _cmie_2025_rows.empty else 0
    with c9:
        st.markdown(new_badge(), unsafe_allow_html=True)
        st.metric("Latest year", str(latest_yr) if latest_yr else "—",
                  delta="CMIE Mar-2025 close" if latest_yr == 2025 else None)
    with c10:
        st.markdown(new_badge(), unsafe_allow_html=True)
        st.metric("Market indices", format_number(n_indices),
                  delta="was 1 (Sensex only)" if n_indices > 1 else None)
    with c11:
        st.markdown(new_badge(), unsafe_allow_html=True)
        st.metric("CMIE 2025 firms", format_number(n_cmie_firms),
                  delta="from DataV2 rollforward" if n_cmie_firms else None)
    with c12:
        st.markdown(new_badge(), unsafe_allow_html=True)
        st.metric("Data vintages", "2", delta="thesis + cmie_2025")

insights, actions = interpret_kpi_cards(df, n_companies, avg_lev, med_lev, avg_prof, dominant_stage, n_obs)
_render_insight_box("KPI Overview — What do these numbers tell us?", insights, actions,
    "Dynamic summary of the current filtered dataset's capital structure profile.")

st.divider()

# ═══════════════════════════════════════════════
# CHANGE 1: Overall Average Leverage Over Time
# ═══════════════════════════════════════════════
st.markdown("### How Has Financial Leverage Changed Over Time?")

overall_yearly = df.groupby("year")["leverage"].agg(["mean", "median", "count"]).reset_index()
overall_yearly.columns = ["year", "mean_leverage", "median_leverage", "n_firms"]

fig_overall = go.Figure()
fig_overall.add_trace(go.Scatter(
    x=overall_yearly["year"], y=overall_yearly["mean_leverage"],
    mode="lines+markers", name="Mean Leverage",
    line=dict(color=PRIMARY, width=3), marker=dict(size=6),
))
fig_overall.add_trace(go.Scatter(
    x=overall_yearly["year"], y=overall_yearly["median_leverage"],
    mode="lines", name="Median Leverage",
    line=dict(color=SECONDARY, width=2, dash="dash"),
))
fig_overall.update_layout(**plotly_layout("Average Financial Leverage Over Time (All Firms)", height=380))
fig_overall = event_bands(fig_overall)
fig_overall.update_yaxes(title="Leverage (%)")
st.plotly_chart(fig_overall, use_container_width=True, config=PLOTLY_CONFIG)

# Interpretation
_f, _a = [], []
trend_start = overall_yearly.iloc[0]["mean_leverage"] if len(overall_yearly) > 0 else 0
trend_end = overall_yearly.iloc[-1]["mean_leverage"] if len(overall_yearly) > 0 else 0
trend_change = trend_end - trend_start
_f.append(f"Average leverage moved from **{trend_start:.1f}%** ({int(overall_yearly.iloc[0]['year'])}) to **{trend_end:.1f}%** ({int(overall_yearly.iloc[-1]['year'])}), a change of **{trend_change:+.1f}pp**.")
if trend_change < -3:
    _f.append("Indian corporates have **deleveraged** over this period — consistent with improved profitability and regulatory pressure (IBC 2016).")
    _a.append("The deleveraging trend suggests firms prefer internal financing (Pecking Order behavior).")
elif trend_change > 3:
    _f.append("Leverage has **increased** — firms may be taking on more debt for growth or facing earnings pressure.")
peak_year = overall_yearly.loc[overall_yearly["mean_leverage"].idxmax()]
_f.append(f"Peak leverage was **{peak_year['mean_leverage']:.1f}%** in **{int(peak_year['year'])}**.")
_render_insight_box("Leverage Over Time — Trend Analysis", _f, _a)

st.divider()

# ═══════════════════════════════════════════════
# CHANGE 2: Leverage by Stage + ANOVA
# ═══════════════════════════════════════════════
st.markdown("### Is Leverage Significantly Different Across Life Stages?")

stage_left, stage_right = st.columns([2, 1])

with stage_left:
    # Stage-level trend lines
    if not stage_summary.empty:
        fig_trend = px.line(
            stage_summary,
            x="year", y="avg_leverage",
            color="life_stage",
            color_discrete_map=STAGE_COLORS,
            category_orders={"life_stage": STAGE_ORDER},
            labels={"avg_leverage": "Avg Leverage (%)", "year": "Year", "life_stage": "Life Stage"},
        )
        fig_trend.update_layout(**plotly_layout("Leverage Over Time by Life Stage", height=420))
        fig_trend = event_bands(fig_trend)
        fig_trend.update_traces(line_width=2.5)
        st.plotly_chart(fig_trend, use_container_width=True, config=PLOTLY_CONFIG)

with stage_right:
    # ANOVA test result
    st.markdown("#### Statistical Test (ANOVA)")
    stage_groups = [g["leverage"].dropna().values for _, g in df.groupby("life_stage")]
    stage_groups = [g for g in stage_groups if len(g) >= 5]
    if len(stage_groups) >= 2:
        f_stat, p_val = stats.f_oneway(*stage_groups)
        st.metric("F-statistic", f"{f_stat:.2f}")
        st.metric("p-value", format_pvalue(p_val))
        if p_val < 0.05:
            st.success("**Yes** — leverage is significantly different across stages (p < 0.05)")
        else:
            st.info("No significant difference found")

    # Stage-means bar chart. When the Latest panel is active AND 2025 rows are in scope,
    # surface the vintage comparison as tabs (mock-inspired). Otherwise fall back to a
    # single "All years" view so the thesis panel reads cleanly.
    # The `stage_means` variable is kept (computed from the full df) so the interpretation
    # narrative below still references the overall highest/lowest stages.
    stage_means = df.groupby("life_stage")["leverage"].mean().reset_index()
    stage_means.columns = ["life_stage", "avg_leverage"]
    stage_means = stage_means.sort_values("avg_leverage", ascending=True)

    _panel = st.session_state.get("panel_mode", "latest")
    _has_2025 = bool((df.get("vintage", pd.Series(dtype=str)) == "cmie_2025").any()) if "vintage" in df.columns else (df["year"] == 2025).any()

    def _stage_bar(df_slice, title_suffix: str):
        if df_slice.empty:
            st.info(f"No rows available for {title_suffix}.")
            return
        sm = df_slice.groupby("life_stage")["leverage"].mean().reset_index()
        sm.columns = ["life_stage", "avg_leverage"]
        sm = sm.sort_values("avg_leverage", ascending=True)
        fig = px.bar(
            sm, x="avg_leverage", y="life_stage", orientation="h",
            color="life_stage", color_discrete_map=STAGE_COLORS,
            labels={"avg_leverage": "Avg Leverage (%)", "life_stage": ""},
        )
        fig.update_layout(**plotly_layout(height=300))
        fig.update_layout(showlegend=False)
        st.plotly_chart(fig, use_container_width=True, config=PLOTLY_CONFIG)

    if _panel == "latest" and _has_2025:
        tab_all, tab_thesis, tab_2025 = st.tabs(["All years", "Thesis only (2001–2024)", "2025 snapshot"])
        with tab_all:
            _stage_bar(df, "all years")
        with tab_thesis:
            if "vintage" in df.columns:
                _stage_bar(df[df["vintage"] == "thesis"], "thesis vintage")
            else:
                _stage_bar(df[df["year"] <= 2024], "pre-2025 rows")
        with tab_2025:
            if "vintage" in df.columns:
                _stage_bar(df[df["vintage"] == "cmie_2025"], "2025 snapshot")
            else:
                _stage_bar(df[df["year"] == 2025], "2025 snapshot")
    else:
        _stage_bar(df, "all years")

# Interpretation
_f2, _a2 = [], []
if len(stage_groups) >= 2 and p_val < 0.05:
    highest = stage_means.iloc[-1]
    lowest = stage_means.iloc[0]
    _f2.append(f"ANOVA confirms leverage is **significantly different** across stages (F={f_stat:.1f}, p<0.001).")
    _f2.append(f"**{highest['life_stage']}** firms have the highest avg leverage ({highest['avg_leverage']:.1f}%), while **{lowest['life_stage']}** have the lowest ({lowest['avg_leverage']:.1f}%).")
    _f2.append(f"The spread is **{highest['avg_leverage'] - lowest['avg_leverage']:.1f}pp** — a substantial difference in capital structure across life stages.")
    _a2.append("Capital structure advice must be stage-specific. A one-size-fits-all leverage target is inappropriate.")
    _a2.append("Decline-stage firms may carry high leverage involuntarily (debt overhang) — different from Growth-stage strategic borrowing.")
_render_insight_box("Stage Comparison — Is Leverage Different?", _f2, _a2,
    "Tests the thesis's core hypothesis: capital structure varies systematically across corporate life stages.")

st.divider()

# ═══════════════════════════════════════════════
# CHANGE 3: What Explains the Differences?
# ═══════════════════════════════════════════════
st.markdown("### What Explains the Leverage Differences Across Stages?")

determinants = ["profitability", "tangibility", "tax_shield", "firm_size", "cash_holdings"]
det_labels = {"profitability": "Profitability", "tangibility": "Tangibility",
              "tax_shield": "Tax Shield", "firm_size": "Firm Size", "cash_holdings": "Cash Holdings"}

# Heatmap: determinant means by stage
heat_data = df.groupby("life_stage")[determinants].mean()
stage_order_present = [s for s in STAGE_ORDER if s in heat_data.index]
heat_data = heat_data.reindex(stage_order_present)

# Normalize each column 0-100 for comparable heatmap
heat_norm = heat_data.copy()
for col in determinants:
    mn, mx = heat_norm[col].min(), heat_norm[col].max()
    if mx > mn:
        heat_norm[col] = (heat_norm[col] - mn) / (mx - mn) * 100

fig_heat = px.imshow(
    heat_norm.values,
    x=[det_labels.get(c, c) for c in determinants],
    y=stage_order_present,
    color_continuous_scale=["#F8FAFC", PRIMARY, "#065F46"],
    aspect="auto",
    text_auto=".0f",
    labels={"color": "Relative Level (0-100)"},
)
fig_heat.update_layout(**plotly_layout("Determinant Profiles by Life Stage (Normalized)", height=380))
st.plotly_chart(fig_heat, use_container_width=True, config=PLOTLY_CONFIG)

# Interpretation
_f3, _a3 = [], []
_f3.append("The heatmap shows **how key determinants vary** across life stages (darker = higher relative value).")
for det in determinants:
    col_data = heat_data[det]
    high_stage = col_data.idxmax()
    low_stage = col_data.idxmin()
    if col_data.max() > col_data.min() * 1.5:
        _f3.append(f"**{det_labels[det]}**: Highest in **{high_stage}** ({col_data.max():.2f}), lowest in **{low_stage}** ({col_data.min():.2f}).")
_a3.append("Stages with high tangibility can support more debt (Trade-off Theory). Stages with high profitability carry less debt (Pecking Order).")
_a3.append("Use these profiles to understand WHY leverage differs — it's driven by fundamental firm characteristics that shift across the lifecycle.")
_render_insight_box("Determinant Decomposition — What Drives Leverage?", _f3, _a3,
    "Shows how profitability, tangibility, tax shield, firm size, and cash holdings differ by stage.")

st.divider()

# ═══════════════════════════════════════════════
# Interest Rate & Market Context
# ═══════════════════════════════════════════════
st.markdown("### Macro Context: Interest Rates & Market Returns vs Leverage")

macro_df = db.get_market_index(yr_min, yr_max)
int_rate_yearly = df.groupby("year")["int_rate"].mean().reset_index() if "int_rate" in df.columns else None

macro_left, macro_right = st.columns(2)

with macro_left:
    # Leverage vs Interest Rate dual-axis
    fig_ir = go.Figure()
    fig_ir.add_trace(go.Scatter(
        x=overall_yearly["year"], y=overall_yearly["mean_leverage"],
        mode="lines+markers", name="Avg Leverage (%)",
        line=dict(color=PRIMARY, width=2.5), marker=dict(size=5),
    ))
    if int_rate_yearly is not None and not int_rate_yearly.empty:
        fig_ir.add_trace(go.Scatter(
            x=int_rate_yearly["year"], y=int_rate_yearly["int_rate"],
            mode="lines+markers", name="Interest Rate (%)",
            line=dict(color=ACCENT, width=2, dash="dash"), marker=dict(size=4),
            yaxis="y2",
        ))
    fig_ir.update_layout(
        **plotly_layout("Leverage vs Interest Rate Over Time", height=380),
        yaxis2=dict(title="Interest Rate (%)", overlaying="y", side="right", showgrid=False),
    )
    fig_ir = event_bands(fig_ir)
    st.plotly_chart(fig_ir, use_container_width=True, config=PLOTLY_CONFIG)

with macro_right:
    # Leverage vs Market P/E
    if not macro_df.empty and "index_pe" in macro_df.columns:
        fig_pe = go.Figure()
        fig_pe.add_trace(go.Scatter(
            x=overall_yearly["year"], y=overall_yearly["mean_leverage"],
            mode="lines+markers", name="Avg Leverage (%)",
            line=dict(color=PRIMARY, width=2.5), marker=dict(size=5),
        ))
        fig_pe.add_trace(go.Scatter(
            x=macro_df["year"], y=macro_df["index_pe"],
            mode="lines+markers", name="BSE P/E Ratio",
            line=dict(color=SECONDARY, width=2, dash="dash"), marker=dict(size=4),
            yaxis="y2",
        ))
        fig_pe.update_layout(
            **plotly_layout("Leverage vs Market P/E Ratio", height=380),
            yaxis2=dict(title="P/E Ratio", overlaying="y", side="right", showgrid=False),
        )
        fig_pe = event_bands(fig_pe)
        st.plotly_chart(fig_pe, use_container_width=True, config=PLOTLY_CONFIG)

# Interpretation
_fm, _am = [], []
if int_rate_yearly is not None and not int_rate_yearly.empty:
    corr_ir = overall_yearly.merge(int_rate_yearly, on="year", how="inner")
    if len(corr_ir) > 5:
        r = corr_ir["mean_leverage"].corr(corr_ir["int_rate"])
        _fm.append(f"Correlation between leverage and interest rate: **r = {r:.2f}**. {'Positive — higher rates coincide with higher leverage (firms locked into debt).' if r > 0.1 else 'Negative — higher rates discourage borrowing.' if r < -0.1 else 'Weak — interest rates alone do not drive leverage trends.'}")
if not macro_df.empty and "index_pe" in macro_df.columns:
    corr_pe = overall_yearly.merge(macro_df[["year", "index_pe"]].dropna(), on="year", how="inner")
    if len(corr_pe) > 5:
        r2 = corr_pe["mean_leverage"].corr(corr_pe["index_pe"])
        _fm.append(f"Correlation between leverage and market P/E: **r = {r2:.2f}**. {'High market valuations coincide with lower leverage — firms issue equity instead of debt (market timing).' if r2 < -0.1 else 'Weak relationship — market conditions do not directly drive leverage.'}")
_am.append("Include interest rate and market P/E as controls in regression models (available in Econometrics Lab) to isolate firm-level determinant effects from macro trends.")
_render_insight_box("Macro Context — Interest Rates & Market Conditions", _fm, _am,
    "Shows how macro-level factors (RBI rates, BSE valuations) co-move with aggregate leverage.")

# ─── Sector / Index benchmark (T623, ~749 series from DataV2 CMIE load) ──────
# T623 series are India-specific (BSE / Nifty). Hidden for the US panel.
if _india:
    _idx_header_cols = st.columns([4, 1])
    with _idx_header_cols[0]:
        st.markdown("### Compare leverage to a sector / market index")
    with _idx_header_cols[1]:
        st.markdown(f'<div style="text-align:right;">{new_badge()}</div>', unsafe_allow_html=True)
    st.caption("Overlay any of the ~749 CMIE T623 index series (BSE / Nifty / sector / industry) against the aggregate leverage line.")

    indices_df = db.get_available_indices()
    if indices_df.empty:
        st.info("No T623 index series loaded. Run `py -3.12 -m cmie.load_vintage ./DataV2 --vintage cmie_2025` to populate.")
    else:
        _pick_col, _chart_col = st.columns([1, 3])
        with _pick_col:
            default_name = "Bse 500" if (indices_df["index_name"] == "Bse 500").any() else indices_df["index_name"].iloc[0]
            chosen_name = st.selectbox(
                "Benchmark index",
                options=indices_df["index_name"].tolist(),
                index=int(indices_df.index[indices_df["index_name"] == default_name][0]),
                key="dashboard_index_picker",
                help=f"Search {len(indices_df):,} series — BSE / Nifty / CMIE sector / CMIE industry.",
            )
            chosen_code = int(indices_df.loc[indices_df["index_name"] == chosen_name, "index_code"].iloc[0])
            _row = indices_df.loc[indices_df["index_code"] == chosen_code].iloc[0]
            st.caption(f"`index_code={chosen_code}`")
            st.caption(f"Coverage: {int(_row['year_min'])}–{int(_row['year_max'])} ({int(_row['n_years'])} yrs)")
        with _chart_col:
            series_df = db.get_market_index(yr_min, yr_max, index_code=chosen_code)
            if series_df.empty or series_df["index_closing"].dropna().empty:
                st.warning(f"No closing data for {chosen_name} in {yr_min}–{yr_max}.")
            else:
                fig_idx = go.Figure()
                fig_idx.add_trace(go.Scatter(
                    x=overall_yearly["year"], y=overall_yearly["mean_leverage"],
                    mode="lines+markers", name="Avg Leverage (%)",
                    line=dict(color=PRIMARY, width=2.5), marker=dict(size=5),
                ))
                fig_idx.add_trace(go.Scatter(
                    x=series_df["year"], y=series_df["index_closing"],
                    mode="lines+markers", name=chosen_name,
                    line=dict(color=SECONDARY, width=2, dash="dash"), marker=dict(size=4),
                    yaxis="y2",
                ))
                fig_idx.update_layout(
                    **plotly_layout(f"Leverage vs {chosen_name}", height=380),
                    yaxis2=dict(title=f"{chosen_name} closing", overlaying="y", side="right", showgrid=False),
                )
                fig_idx = event_bands(fig_idx)
                st.plotly_chart(fig_idx, use_container_width=True, config=PLOTLY_CONFIG)

st.divider()

# ═══════════════════════════════════════════════
# Event x Stage Interaction
# ═══════════════════════════════════════════════
st.markdown("### How Did Events Affect Leverage Differently by Stage?")

evt_left, evt_right = st.columns([1, 1])

with evt_left:
    # Build event x stage data
    event_stage_data = []
    for event_name, col in [("GFC", "gfc"), ("IBC", "ibc_2016"), ("COVID", "covid_dummy")]:
        for stage in stage_order_present:
            stage_df = df[df["life_stage"] == stage]
            during = stage_df[stage_df[col] == 1]["leverage"].mean()
            outside = stage_df[stage_df[col] == 0]["leverage"].mean()
            if pd.notna(during) and pd.notna(outside):
                event_stage_data.append({
                    "Event": event_name, "Stage": stage,
                    "During Event": during, "Outside Event": outside,
                    "Difference (pp)": during - outside,
                })

    if event_stage_data:
        es_df = pd.DataFrame(event_stage_data)
        fig_es = px.bar(
            es_df, x="Stage", y="Difference (pp)", color="Event",
            barmode="group",
            color_discrete_map={"GFC": "#EF4444", "IBC": SECONDARY, "COVID": ACCENT},
            labels={"Difference (pp)": "Leverage Change (pp)", "Stage": ""},
            category_orders={"Stage": stage_order_present},
        )
        fig_es.add_hline(y=0, line_dash="dash", line_color="#9CA3AF")
        fig_es.update_layout(**plotly_layout("Leverage Change During Events vs Normal (by Stage)", height=400))
        st.plotly_chart(fig_es, use_container_width=True, config=PLOTLY_CONFIG)

with evt_right:
    # Event impact summary cards
    st.markdown("#### Event Period Summary")
    overall_avg = df["leverage"].mean()
    for event_name, col in [("GFC (2008-09)", "gfc"), ("IBC (2016+)", "ibc_2016"), ("COVID (2020-21)", "covid_dummy")]:
        evt_df = df[df[col] == 1]
        evt_avg = evt_df["leverage"].mean() if not evt_df.empty else None
        if evt_avg is not None:
            diff = evt_avg - overall_avg
            st.metric(event_name, format_pct(evt_avg),
                      delta=f"{diff:+.1f}pp vs overall", delta_color="inverse" if diff > 0 else "normal")

# Interpretation
_f5, _a5 = [], []
if event_stage_data:
    es_df_temp = pd.DataFrame(event_stage_data)
    most_affected = es_df_temp.loc[es_df_temp["Difference (pp)"].abs().idxmax()]
    _f5.append(f"**{most_affected['Stage']}** firms were most affected by **{most_affected['Event']}** ({most_affected['Difference (pp)']:+.1f}pp leverage change).")
    gfc_data = es_df_temp[es_df_temp["Event"] == "GFC"]
    if not gfc_data.empty:
        gfc_up = gfc_data[gfc_data["Difference (pp)"] > 0]
        if not gfc_up.empty:
            _f5.append(f"During GFC, leverage **increased** for {', '.join(gfc_up['Stage'].tolist())} stages — credit constraints forced higher borrowing.")
    ibc_data = es_df_temp[es_df_temp["Event"] == "IBC"]
    if not ibc_data.empty:
        ibc_down = ibc_data[ibc_data["Difference (pp)"] < 0]
        if not ibc_down.empty:
            _f5.append(f"Post-IBC, leverage **decreased** for {', '.join(ibc_down['Stage'].tolist())} — regulatory discipline worked.")
    _a5.append("Events affect stages differently — Decline firms are more vulnerable to credit shocks than Maturity firms.")
    _a5.append("Factor macro events into credit risk models: same firm in different macro regimes carries different risk.")
_render_insight_box("Event x Stage Interaction — Differential Impact", _f5, _a5,
    "Shows how GFC, IBC, and COVID affected leverage differently across life stages.")

st.divider()

# ── Lifecycle Distribution + Top 10 ──
bottom_left, bottom_right = st.columns([1, 1])

with bottom_left:
    st.markdown("### Lifecycle Distribution")
    stage_counts = df["life_stage"].value_counts().reset_index()
    stage_counts.columns = ["life_stage", "count"]
    fig_pie = px.pie(
        stage_counts, names="life_stage", values="count", hole=0.45,
        color="life_stage", color_discrete_map=STAGE_COLORS,
        category_orders={"life_stage": STAGE_ORDER},
    )
    fig_pie.update_layout(**plotly_layout(height=400))
    fig_pie.update_traces(textinfo="percent+label", textposition="outside")
    st.plotly_chart(fig_pie, use_container_width=True, config=PLOTLY_CONFIG)

with bottom_right:
    st.markdown("### Top 10 Most Leveraged Companies")
    top10 = db.get_top_leveraged(10, ft)
    if not top10.empty:
        top10["avg_leverage"] = winsorize(top10["avg_leverage"])
        top10 = top10.sort_values("avg_leverage", ascending=True)
        fig_bar = px.bar(
            top10, x="avg_leverage", y="company_name", orientation="h",
            color="life_stage", color_discrete_map=STAGE_COLORS,
            labels={"avg_leverage": "Avg Leverage (%)", "company_name": ""},
        )
        fig_bar.update_layout(**plotly_layout(height=400))
        st.plotly_chart(fig_bar, use_container_width=True, config=PLOTLY_CONFIG)
