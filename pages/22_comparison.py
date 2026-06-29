"""
Comparison — Side-by-side analysis of two companies or two life stages on the same axes.
"""

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import numpy as np
import db
from helpers import (
    winsorize, plotly_layout, event_bands, ensure_session_state,
    STAGE_COLORS, PRIMARY, SECONDARY, PLOTLY_CONFIG,
    _render_insight_box, df_download_button, chart_download_button,
)

ensure_session_state()
db.log_page_visit("Comparison")

_panel = st.session_state.get("panel_mode", "latest")
filters = st.session_state.filters
ft = db.filters_to_tuple(filters)
_year_range = filters.get("year_range")

st.markdown("### Comparison")
st.caption("Place two companies or two life stages side-by-side on the same axes.")

_KEY_METRICS = [
    ("leverage",      "Avg Leverage (%)"),
    ("profitability", "Avg Profitability (%)"),
    ("tangibility",   "Avg Tangibility (%)"),
    ("firm_size",     "Avg Firm Size"),
]
_SUMMARY_METRICS = [
    ("leverage",      "Leverage (%)"),
    ("profitability", "Profitability (%)"),
    ("tangibility",   "Tangibility (%)"),
    ("tax_shield",    "Tax Shield (%)"),
    ("dividend",      "Dividend (%)"),
    ("firm_size",     "Firm Size"),
]
_RADAR_COLS   = ["leverage", "profitability", "tangibility", "firm_size", "tax_shield", "cash_holdings"]
_RADAR_LABELS = ["Leverage", "Profitability", "Tangibility", "Firm Size", "Tax Shield", "Cash"]


def _apply_year(df: pd.DataFrame) -> pd.DataFrame:
    if _year_range and "year" in df.columns:
        return df[(df["year"] >= _year_range[0]) & (df["year"] <= _year_range[1])]
    return df


def _norm_vals(df_list: list[pd.DataFrame], cols: list[str]) -> dict:
    combined = pd.concat(df_list)
    return {c: (combined[c].min(), combined[c].max()) for c in cols}


def _norm(val, m, norms):
    mn, mx = norms[m]
    return 50 if mx == mn else max(0, min(100, (val - mn) / (mx - mn) * 100))


def _radar(vals_a, vals_b, name_a, name_b, color_a, color_b):
    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(
        r=vals_a + [vals_a[0]], theta=_RADAR_LABELS + [_RADAR_LABELS[0]],
        fill="toself", name=name_a,
        fillcolor="rgba(13,148,136,0.15)",
        line=dict(color=color_a, width=2),
    ))
    fig.add_trace(go.Scatterpolar(
        r=vals_b + [vals_b[0]], theta=_RADAR_LABELS + [_RADAR_LABELS[0]],
        fill="toself", name=name_b,
        fillcolor="rgba(99,102,241,0.15)",
        line=dict(color=color_b, width=2, dash="dash"),
    ))
    fig.update_layout(**plotly_layout(height=400))
    fig.update_layout(
        polar=dict(radialaxis=dict(visible=True, range=[0, 100])),
        legend=dict(orientation="h", y=-0.18),
    )
    return fig


def _summary_table(df_a, df_b, name_a, name_b):
    rows = []
    for col, label in _SUMMARY_METRICS:
        if col not in df_a.columns:
            continue
        va = df_a[col].mean()
        vb = df_b[col].mean()
        rows.append({
            "Metric": label,
            name_a[:22]: f"{va:.2f}" if pd.notna(va) else "—",
            name_b[:22]: f"{vb:.2f}" if pd.notna(vb) else "—",
        })
    return pd.DataFrame(rows)


# ─────────────────────────────────────────────────────────────────────────────
# TABS
# ─────────────────────────────────────────────────────────────────────────────

tab_co, tab_st = st.tabs(["🏢 Company vs Company", "📊 Stage vs Stage"])

# ─────────────────────────────────────────────────────────────────────────────
# TAB 1 — Company vs Company
# ─────────────────────────────────────────────────────────────────────────────

with tab_co:
    try:
        with st.spinner("Loading companies…"):
            companies_df = db.get_companies(_panel)
    except Exception as _e:
        st.error(f"Failed to load company list. ({_e})")
        st.stop()

    names = companies_df["company_name"].tolist()
    col_a, col_b = st.columns(2)
    with col_a:
        a_name = st.selectbox("Company A", names, index=0, key="cmp_a")
    with col_b:
        default_b = min(1, len(names) - 1)
        b_name = st.selectbox("Company B", names, index=default_b, key="cmp_b")

    if a_name == b_name:
        st.warning("Select two different companies to compare.")
        st.stop()

    a_code = int(companies_df.loc[companies_df["company_name"] == a_name, "company_code"].iloc[0])
    b_code = int(companies_df.loc[companies_df["company_name"] == b_name, "company_code"].iloc[0])

    try:
        with st.spinner("Loading data…"):
            df_a = _apply_year(db.get_company_detail(a_code))
            df_b = _apply_year(db.get_company_detail(b_code))
    except Exception as _e:
        st.error(f"Failed to load company data. ({_e})")
        st.stop()

    if df_a.empty or df_b.empty:
        st.warning("No data available for one or both companies in the selected date range.")
        st.stop()

    # ── KPI row ──────────────────────────────────────────────────────────────
    kpi_cols = st.columns(4)
    for i, (col_key, label) in enumerate(_KEY_METRICS):
        va = df_a[col_key].mean()
        vb = df_b[col_key].mean()
        kpi_cols[i].metric(label, f"{va:.1f}", delta=f"{va - vb:+.1f} vs {b_name[:14]}")

    st.divider()

    # ── Row 1: Leverage + Profitability over time ─────────────────────────────
    c1, c2 = st.columns(2)

    with c1:
        st.markdown("#### Leverage over Time")
        fig_lev = go.Figure()
        fig_lev.add_trace(go.Scatter(
            x=df_a["year"], y=df_a["leverage"], name=a_name,
            mode="lines+markers", line=dict(color=PRIMARY, width=3), marker=dict(size=6),
        ))
        fig_lev.add_trace(go.Scatter(
            x=df_b["year"], y=df_b["leverage"], name=b_name,
            mode="lines+markers", line=dict(color=SECONDARY, width=3, dash="dash"), marker=dict(size=6),
        ))
        fig_lev.update_layout(**plotly_layout(height=380, year_range=_year_range))
        fig_lev = event_bands(fig_lev)
        st.plotly_chart(fig_lev, use_container_width=True, config=PLOTLY_CONFIG)
        chart_download_button(fig_lev, "comparison_leverage.png")

    with c2:
        st.markdown("#### Profitability over Time")
        fig_prof = go.Figure()
        fig_prof.add_trace(go.Scatter(
            x=df_a["year"], y=df_a["profitability"], name=a_name,
            mode="lines+markers", line=dict(color=PRIMARY, width=3), marker=dict(size=6),
        ))
        fig_prof.add_trace(go.Scatter(
            x=df_b["year"], y=df_b["profitability"], name=b_name,
            mode="lines+markers", line=dict(color=SECONDARY, width=3, dash="dash"), marker=dict(size=6),
        ))
        fig_prof.update_layout(**plotly_layout(height=380, year_range=_year_range))
        fig_prof = event_bands(fig_prof)
        st.plotly_chart(fig_prof, use_container_width=True, config=PLOTLY_CONFIG)
        chart_download_button(fig_prof, "comparison_profitability.png")

    # ── Row 2: Radar + Summary table ─────────────────────────────────────────
    c3, c4 = st.columns(2)

    with c3:
        st.markdown("#### Multi-Metric Profile (Radar)")
        _norms = _norm_vals([df_a, df_b], _RADAR_COLS)
        vals_a = [_norm(df_a[m].mean(), m, _norms) for m in _RADAR_COLS]
        vals_b = [_norm(df_b[m].mean(), m, _norms) for m in _RADAR_COLS]
        fig_r = _radar(vals_a, vals_b, a_name, b_name, PRIMARY, SECONDARY)
        st.plotly_chart(fig_r, use_container_width=True, config=PLOTLY_CONFIG)
        chart_download_button(fig_r, "comparison_radar.png")

    with c4:
        st.markdown("#### Key Metrics Summary")
        tbl = _summary_table(df_a, df_b, a_name, b_name)
        st.dataframe(tbl, hide_index=True, use_container_width=True)
        df_download_button(tbl, "comparison_company_summary.csv")

    # ── Interpretation ────────────────────────────────────────────────────────
    lev_a, lev_b = df_a["leverage"].mean(), df_b["leverage"].mean()
    prof_a, prof_b = df_a["profitability"].mean(), df_b["profitability"].mean()

    co_insights = []
    if abs(lev_a - lev_b) < 2:
        co_insights.append(
            f"**{a_name}** and **{b_name}** carry nearly identical average leverage "
            f"({lev_a:.1f}% vs {lev_b:.1f}%)."
        )
    elif lev_a > lev_b:
        co_insights.append(
            f"**{a_name}** carries {lev_a - lev_b:.1f}pp more leverage than **{b_name}** "
            f"({lev_a:.1f}% vs {lev_b:.1f}%)."
        )
    else:
        co_insights.append(
            f"**{b_name}** carries {lev_b - lev_a:.1f}pp more leverage than **{a_name}** "
            f"({lev_b:.1f}% vs {lev_a:.1f}%)."
        )

    if prof_a > prof_b and lev_a < lev_b:
        co_insights.append(
            f"**{a_name}** is more profitable and less leveraged — consistent with Pecking Order Theory."
        )
    elif prof_b > prof_a and lev_b < lev_a:
        co_insights.append(
            f"**{b_name}** is more profitable and less leveraged — consistent with Pecking Order Theory."
        )
    else:
        co_insights.append(
            f"Profitability: **{a_name}** = {prof_a:.1f}%, **{b_name}** = {prof_b:.1f}%."
        )

    _render_insight_box(
        f"Comparison: {a_name} vs {b_name}",
        co_insights,
        [
            "Check if leverage divergence maps to life-stage differences between the two firms.",
            "Compare tangibility — asset-heavy firms typically support higher leverage (Trade-Off Theory).",
            "Look for structural breaks around GFC 2008 and COVID 2020 in the time-series charts.",
        ],
    )

# ─────────────────────────────────────────────────────────────────────────────
# TAB 2 — Stage vs Stage
# ─────────────────────────────────────────────────────────────────────────────

with tab_st:
    try:
        with st.spinner("Loading panel…"):
            stages = db.get_life_stages()
            full_df = db.get_active_financials(ft)
    except Exception as _e:
        st.error(f"Failed to load stage data. ({_e})")
        st.stop()

    col_sa, col_sb = st.columns(2)
    with col_sa:
        stage_a = st.selectbox("Stage A", stages, index=0, key="cmp_sa")
    with col_sb:
        stage_b = st.selectbox("Stage B", stages, index=min(2, len(stages) - 1), key="cmp_sb")

    df_sa = full_df[full_df["life_stage"] == stage_a]
    df_sb = full_df[full_df["life_stage"] == stage_b]

    if df_sa.empty or df_sb.empty:
        st.warning("No data for one or both life stages.")
        st.stop()

    # ── KPI row ──────────────────────────────────────────────────────────────
    sm_cols = st.columns(4)
    for i, (col_key, label) in enumerate(_KEY_METRICS):
        va = df_sa[col_key].mean()
        vb = df_sb[col_key].mean()
        sm_cols[i].metric(label, f"{va:.1f}", delta=f"{va - vb:+.1f} vs {stage_b}")

    st.divider()

    agg_a = df_sa.groupby("year")[["leverage", "profitability", "tangibility"]].mean().reset_index()
    agg_b = df_sb.groupby("year")[["leverage", "profitability", "tangibility"]].mean().reset_index()
    color_a = STAGE_COLORS.get(stage_a, PRIMARY)
    color_b = STAGE_COLORS.get(stage_b, SECONDARY)

    # ── Row 1: Leverage + Distribution ───────────────────────────────────────
    c1, c2 = st.columns(2)

    with c1:
        st.markdown("#### Leverage over Time (Mean)")
        fig_sl = go.Figure()
        fig_sl.add_trace(go.Scatter(
            x=agg_a["year"], y=agg_a["leverage"], name=stage_a,
            mode="lines+markers", line=dict(color=color_a, width=3), marker=dict(size=6),
        ))
        fig_sl.add_trace(go.Scatter(
            x=agg_b["year"], y=agg_b["leverage"], name=stage_b,
            mode="lines+markers", line=dict(color=color_b, width=3, dash="dash"), marker=dict(size=6),
        ))
        fig_sl.update_layout(**plotly_layout(height=380, year_range=_year_range))
        fig_sl = event_bands(fig_sl)
        st.plotly_chart(fig_sl, use_container_width=True, config=PLOTLY_CONFIG)
        chart_download_button(fig_sl, "comparison_stage_leverage.png")

    with c2:
        st.markdown("#### Leverage Distribution (Box Plot)")
        box_df = (
            full_df[full_df["life_stage"].isin([stage_a, stage_b])][["life_stage", "leverage"]]
            .dropna()
            .copy()
        )
        box_df["leverage"] = winsorize(box_df["leverage"])
        fig_bx = px.box(
            box_df, x="life_stage", y="leverage",
            color="life_stage",
            color_discrete_map=STAGE_COLORS,
            category_orders={"life_stage": [stage_a, stage_b]},
            labels={"leverage": "Leverage (%)", "life_stage": ""},
        )
        fig_bx.update_layout(**plotly_layout(height=380))
        st.plotly_chart(fig_bx, use_container_width=True, config=PLOTLY_CONFIG)
        chart_download_button(fig_bx, "comparison_stage_distribution.png")

    # ── Row 2: Profitability + Summary table ──────────────────────────────────
    c3, c4 = st.columns(2)

    with c3:
        st.markdown("#### Profitability over Time (Mean)")
        fig_sp = go.Figure()
        fig_sp.add_trace(go.Scatter(
            x=agg_a["year"], y=agg_a["profitability"], name=stage_a,
            mode="lines+markers", line=dict(color=color_a, width=3), marker=dict(size=6),
        ))
        fig_sp.add_trace(go.Scatter(
            x=agg_b["year"], y=agg_b["profitability"], name=stage_b,
            mode="lines+markers", line=dict(color=color_b, width=3, dash="dash"), marker=dict(size=6),
        ))
        fig_sp.update_layout(**plotly_layout(height=380, year_range=_year_range))
        fig_sp = event_bands(fig_sp)
        st.plotly_chart(fig_sp, use_container_width=True, config=PLOTLY_CONFIG)
        chart_download_button(fig_sp, "comparison_stage_profitability.png")

    with c4:
        st.markdown("#### Key Metrics Summary")
        st_tbl = _summary_table(df_sa, df_sb, stage_a, stage_b)
        st.dataframe(st_tbl, hide_index=True, use_container_width=True)
        df_download_button(st_tbl, "comparison_stage_summary.csv")

    # ── Interpretation ────────────────────────────────────────────────────────
    lev_sa, lev_sb = df_sa["leverage"].mean(), df_sb["leverage"].mean()
    n_a = df_sa["company_code"].nunique()
    n_b = df_sb["company_code"].nunique()

    st_insights = []
    if abs(lev_sa - lev_sb) < 2:
        st_insights.append(
            f"**{stage_a}** and **{stage_b}** stages carry nearly identical average leverage "
            f"({lev_sa:.1f}% vs {lev_sb:.1f}%)."
        )
    elif lev_sa > lev_sb:
        st_insights.append(
            f"**{stage_a}** stage carries {lev_sa - lev_sb:.1f}pp more leverage than **{stage_b}** "
            f"({lev_sa:.1f}% vs {lev_sb:.1f}%)."
        )
    else:
        st_insights.append(
            f"**{stage_b}** stage carries {lev_sb - lev_sa:.1f}pp more leverage than **{stage_a}** "
            f"({lev_sb:.1f}% vs {lev_sa:.1f}%)."
        )
    st_insights.append(f"Sample: **{stage_a}** = {n_a} firms · **{stage_b}** = {n_b} firms.")

    _render_insight_box(
        f"Stage Comparison: {stage_a} vs {stage_b}",
        st_insights,
        [
            "Higher profitability in one stage may explain lower leverage — Pecking Order effect.",
            "Asset intensity (tangibility) differences drive Trade-Off Theory optimal leverage divergence.",
            "Year-on-year trends reveal which stage deleveraged faster post-GFC and post-COVID.",
        ],
    )
