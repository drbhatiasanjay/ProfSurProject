"""
Board Export — per-topic data builders for Page 17.

Each build_topic_N() function returns:
    {
        "figs":     [Plotly Figure, ...],
        "tables":   [pd.DataFrame, ...],
        "insights": ["bullet text", ...],
        "actions":  ["call-to-action text", ...],
        "title":    "Topic N — Name",
    }

All insights are derived strictly from actual data values — no LLM, no guessing.
Charts use the project-standard plotly_layout() + PLOTLY_CONFIG from helpers.py.
"""

import numpy as np
import pandas as pd
from scipy import stats
import plotly.graph_objects as go
import plotly.express as px

from helpers import (
    plotly_layout, PLOTLY_CONFIG, STAGE_COLORS, STAGE_ORDER,
    PRIMARY, SECONDARY, ACCENT, NEUTRAL,
)

# ── helpers ───────────────────────────────────────────────────────────────────

def _pct(series, value):
    """Percentile of value within series (0–100)."""
    clean = series.dropna()
    if clean.empty:
        return 50
    return int(stats.percentileofscore(clean, value, kind="rank"))


def _fmt(v, pct=True):
    """Format a ratio as percentage string."""
    if pd.isna(v):
        return "N/A"
    return f"{v * 100:.1f}%" if pct else f"{v:.2f}"


def _co_latest(company_df):
    """Latest row for a company as a Series."""
    return company_df.sort_values("year").iloc[-1]


def _last_n(company_df, n=10):
    return company_df.sort_values("year").tail(n)


def _peer_median(peers_df, col):
    if peers_df is None or peers_df.empty or col not in peers_df.columns:
        return np.nan
    return peers_df[col].median()


def _stage_median(stage_summary, stage, col):
    if stage_summary is None or stage_summary.empty:
        return np.nan
    row = stage_summary[stage_summary["life_stage"] == stage]
    agg_col = f"avg_{col}" if f"avg_{col}" in stage_summary.columns else col
    if row.empty or agg_col not in row.columns:
        return np.nan
    return row[agg_col].mean()


def _add_hline_zero(fig):
    fig.add_hline(y=0, line_dash="dot", line_color="#9CA3AF", line_width=1)


# ── Topic 1 — Executive Summary ───────────────────────────────────────────────

def build_topic_1(company_df, company_info, peers_df, full_panel, stage_summary):
    row = _co_latest(company_df)
    df5 = _last_n(company_df, 5)
    stage = company_info.get("current_stage", row.get("life_stage", "Unknown"))
    peer_lev = _peer_median(peers_df, "leverage")
    peer_prof = _peer_median(peers_df, "profitability")

    # KPI summary figure (indicator tiles)
    kpis = [
        ("Leverage", row.get("leverage"), None),
        ("Profitability", row.get("profitability"), None),
        ("Tangibility", row.get("tangibility"), None),
        ("Interest Cover", (row.get("pbit", 0) / row.get("interest_amt", 1))
         if row.get("interest_amt", 0) > 0 else None, None),
        ("Tax Rate", row.get("tax"), None),
        ("Tax Shield", row.get("tax_shield"), None),
    ]
    fig_kpi = go.Figure()
    for i, (label, val, _) in enumerate(kpis):
        fig_kpi.add_trace(go.Indicator(
            mode="number",
            value=round(val * 100, 2) if pd.notna(val) else 0,
            number={"suffix": "%", "font": {"size": 28}},
            title={"text": label, "font": {"size": 13}},
            domain={"row": 0, "column": i},
        ))
    fig_kpi.update_layout(
        grid={"rows": 1, "columns": len(kpis), "pattern": "independent"},
        **plotly_layout(f"{company_info['name']} — Key Metrics ({row.get('year', '')})", height=180),
    )

    # 5-year sparklines (multi-line)
    fig_spark = go.Figure()
    for col, label, color in [
        ("leverage", "Leverage", PRIMARY),
        ("profitability", "Profitability", SECONDARY),
        ("tangibility", "Tangibility", ACCENT),
    ]:
        if col in df5.columns:
            fig_spark.add_trace(go.Scatter(
                x=df5["year"], y=df5[col] * 100,
                mode="lines+markers", name=label,
                line=dict(color=color, width=2),
            ))
    lay = plotly_layout("5-Year Trend — Key Ratios", height=300)
    lay["yaxis_title"] = "Value (%)"
    fig_spark.update_layout(**lay)

    # Insights
    insights, actions = [], []
    if pd.notna(row.get("leverage")):
        lev_pct = _pct(peers_df["leverage"] if peers_df is not None and not peers_df.empty else pd.Series([row["leverage"]]), row["leverage"])
        insights.append(
            f"Leverage is **{_fmt(row['leverage'])}** — at the **{lev_pct}th percentile** "
            f"of {stage}-stage peers (peer median: {_fmt(peer_lev)})."
        )
    if pd.notna(row.get("profitability")):
        prof_pct = _pct(peers_df["profitability"] if peers_df is not None and not peers_df.empty else pd.Series([row["profitability"]]), row["profitability"])
        insights.append(
            f"Profitability is **{_fmt(row['profitability'])}** — at the **{prof_pct}th percentile** "
            f"of {stage}-stage peers (peer median: {_fmt(peer_prof)})."
        )
    if pd.notna(row.get("interest_amt")) and row.get("interest_amt", 0) > 0:
        cover = row.get("pbit", 0) / row["interest_amt"]
        flag = "healthy" if cover >= 3 else ("watch" if cover >= 1.5 else "**critical — below IBC threshold**")
        insights.append(f"Interest coverage is **{cover:.1f}x** ({flag}).")

    actions = [
        "Review leverage position relative to peer band before any debt raise.",
        "Monitor profitability trend — sustained improvement supports Pecking Order funding.",
        "Share interest coverage trend with lenders and rating agencies.",
    ]

    return {"figs": [fig_kpi, fig_spark], "tables": [], "insights": insights,
            "actions": actions, "title": "Topic 1 — Executive Summary"}


# ── Topic 2 — Corporate Life Cycle ────────────────────────────────────────────

def build_topic_2(company_df, company_info, peers_df, full_panel, stage_summary):
    df = company_df.sort_values("year")
    stage_col = "life_stage"

    # Stage timeline (colour-coded scatter with fill per stage)
    stage_colors_map = {s: STAGE_COLORS.get(s, PRIMARY) for s in df[stage_col].unique()}
    fig_tl = go.Figure()
    for stage in STAGE_ORDER:
        sub = df[df[stage_col] == stage]
        if sub.empty:
            continue
        fig_tl.add_trace(go.Scatter(
            x=sub["year"], y=[stage] * len(sub),
            mode="markers",
            marker=dict(color=stage_colors_map.get(stage, PRIMARY), size=14, symbol="square"),
            name=stage,
        ))
    lay = plotly_layout("Life-Stage Trajectory (2001–2024)", height=320)
    lay["yaxis"] = {"title": "Stage", "categoryorder": "array", "categoryarray": STAGE_ORDER[::-1]}
    lay["xaxis_title"] = "Year"
    fig_tl.update_layout(**lay)

    # Time distribution (% years per stage)
    stage_counts = df[stage_col].value_counts()
    total_yrs = len(df)
    fig_dist = go.Figure(go.Pie(
        labels=stage_counts.index.tolist(),
        values=stage_counts.values.tolist(),
        marker_colors=[STAGE_COLORS.get(s, PRIMARY) for s in stage_counts.index],
        textinfo="label+percent",
        hole=0.4,
    ))
    fig_dist.update_layout(**plotly_layout("Years Spent per Stage", height=300))

    # Peer cohort bar (how many firms in same stage per year from full_panel)
    if full_panel is not None and not full_panel.empty and stage_col in full_panel.columns:
        cohort = full_panel.groupby(["year", stage_col]).size().reset_index(name="n_firms")
        cur_stage = company_info.get("current_stage", df[stage_col].iloc[-1])
        cohort_stage = cohort[cohort[stage_col] == cur_stage]
        fig_cohort = go.Figure(go.Bar(
            x=cohort_stage["year"], y=cohort_stage["n_firms"],
            marker_color=STAGE_COLORS.get(cur_stage, PRIMARY), name=cur_stage,
        ))
        fig_cohort.update_layout(**plotly_layout(
            f"Firms in {cur_stage} Stage by Year (peer universe)", height=280
        ))
        figs = [fig_tl, fig_dist, fig_cohort]
    else:
        figs = [fig_tl, fig_dist]

    # Insights
    insights, actions = [], []
    cur_stage = company_info.get("current_stage", df[stage_col].iloc[-1])
    yrs_in_stage = int(stage_counts.get(cur_stage, 1))
    insights.append(f"Current life stage: **{cur_stage}** — in this stage for **{yrs_in_stage} year(s)**.")
    dominant = stage_counts.idxmax()
    dominant_pct = round(stage_counts.max() / total_yrs * 100)
    insights.append(
        f"Dominant historical stage: **{dominant}** ({dominant_pct}% of all years), "
        "indicating a characteristically stable trajectory."
    )
    if full_panel is not None and not full_panel.empty:
        peers_in_stage = full_panel[full_panel[stage_col] == cur_stage]["company_code"].nunique()
        insights.append(
            f"**{peers_in_stage} of 401 firms** are currently classified as {cur_stage} — "
            "your immediate peer universe for benchmarking."
        )
    actions = [
        f"Benchmark capital structure specifically against {cur_stage}-stage firms (see Topic 8).",
        "Review stage trajectory for signals of an upcoming transition (see Topic 10).",
        "Capital structure norms differ materially across stages — manage leverage to stage-appropriate targets.",
    ]

    return {"figs": figs, "tables": [], "insights": insights,
            "actions": actions, "title": "Topic 2 — Corporate Life Cycle"}


# ── Topic 3 — Capital Structure Profile ───────────────────────────────────────

def build_topic_3(company_df, company_info, peers_df, full_panel, stage_summary):
    df = _last_n(company_df, 10)
    row = _co_latest(company_df)
    cur_stage = company_info.get("current_stage", row.get("life_stage", ""))

    # Leverage trend vs stage median band
    stage_lev = stage_summary[stage_summary["life_stage"] == cur_stage] if stage_summary is not None and not stage_summary.empty else pd.DataFrame()
    fig_lev = go.Figure()
    if not stage_lev.empty and "avg_leverage" in stage_lev.columns:
        fig_lev.add_trace(go.Scatter(
            x=stage_lev["year"], y=stage_lev["avg_leverage"] * 100,
            mode="lines", name=f"{cur_stage} stage avg",
            line=dict(color=NEUTRAL, width=1.5, dash="dash"),
        ))
    fig_lev.add_trace(go.Scatter(
        x=df["year"], y=df["leverage"] * 100,
        mode="lines+markers", name=company_info["name"],
        line=dict(color=PRIMARY, width=2.5),
    ))
    lay = plotly_layout("Leverage Ratio Trend (10 years)", height=320)
    lay["yaxis_title"] = "Leverage (%)"
    fig_lev.update_layout(**lay)

    # Debt composition stacked bar
    fig_debt = go.Figure()
    if "borrowings" in df.columns:
        fig_debt.add_trace(go.Bar(x=df["year"], y=df["borrowings"],
                                   name="Borrowings", marker_color=PRIMARY))
    if "reserves_and_funds" in df.columns:
        fig_debt.add_trace(go.Bar(x=df["year"], y=df["reserves_and_funds"],
                                   name="Reserves & Funds", marker_color=SECONDARY))
    fig_debt.update_layout(barmode="stack",
                            **plotly_layout("Debt & Equity Composition (₹ Cr)", height=320))

    # Interest coverage trend
    if "pbit" in df.columns and "interest_amt" in df.columns:
        df = df.copy()
        df["coverage"] = df.apply(
            lambda r: r["pbit"] / r["interest_amt"] if r.get("interest_amt", 0) > 0 else np.nan,
            axis=1
        )
        fig_cov = go.Figure()
        fig_cov.add_hline(y=3, line_dash="dot", line_color=SECONDARY,
                           annotation_text="3x healthy", annotation_position="top right")
        fig_cov.add_hline(y=1.5, line_dash="dot", line_color=ACCENT,
                           annotation_text="1.5x IBC threshold", annotation_position="top right")
        fig_cov.add_trace(go.Scatter(
            x=df["year"], y=df["coverage"],
            mode="lines+markers", name="Interest Coverage",
            line=dict(color=PRIMARY, width=2.5),
        ))
        lay_cov = plotly_layout("Interest Coverage Ratio (PBIT / Interest)", height=300)
        lay_cov["yaxis_title"] = "Coverage (x)"
        fig_cov.update_layout(**lay_cov)
        figs = [fig_lev, fig_debt, fig_cov]
    else:
        figs = [fig_lev, fig_debt]

    # Insights
    insights, actions = [], []
    lev_now = row.get("leverage")
    if pd.notna(lev_now):
        stage_med = _stage_median(stage_summary, cur_stage, "leverage")
        rel = "above" if lev_now > stage_med else "below"
        insights.append(
            f"Leverage is **{_fmt(lev_now)}** — **{rel}** the {cur_stage}-stage average "
            f"({_fmt(stage_med)})."
        )
    lev_5 = _last_n(company_df, 5)["leverage"]
    delta_lev = lev_5.iloc[-1] - lev_5.iloc[0]
    trend_word = "rising" if delta_lev > 0.01 else ("falling" if delta_lev < -0.01 else "stable")
    insights.append(f"Leverage trend (5-year): **{trend_word}** ({delta_lev*100:+.1f}pp).")
    if "pbit" in df.columns and "interest_amt" in df.columns:
        latest_cov = df["coverage"].iloc[-1] if "coverage" in df.columns else np.nan
        if pd.notna(latest_cov):
            cov_flag = "healthy" if latest_cov >= 3 else ("borderline" if latest_cov >= 1.5 else "critical")
            insights.append(f"Interest coverage: **{latest_cov:.1f}x** ({cov_flag}).")
    actions = [
        "Ensure debt composition is aligned with maturity profile — short-term borrowings carry refinancing risk.",
        "If coverage < 3x, stress-test against a +200bp interest rate scenario (see Topic 11).",
        "Track leverage vs stage-peer band — a sustained breach of 75th percentile warrants board attention.",
    ]

    return {"figs": figs, "tables": [], "insights": insights,
            "actions": actions, "title": "Topic 3 — Capital Structure Profile"}


# ── Topic 4 — Profitability & Earnings ────────────────────────────────────────

def build_topic_4(company_df, company_info, peers_df, full_panel, stage_summary):
    df = _last_n(company_df, 10)
    row = _co_latest(company_df)
    cur_stage = company_info.get("current_stage", row.get("life_stage", ""))

    # Profitability trend vs peer median
    fig_prof = go.Figure()
    peer_prof_med = _peer_median(peers_df, "profitability")
    if pd.notna(peer_prof_med):
        fig_prof.add_hline(y=peer_prof_med * 100, line_dash="dash", line_color=NEUTRAL,
                            annotation_text=f"Peer median {_fmt(peer_prof_med)}")
    fig_prof.add_trace(go.Scatter(
        x=df["year"], y=df["profitability"] * 100,
        mode="lines+markers", name="Profitability",
        line=dict(color=PRIMARY, width=2.5),
    ))
    lay = plotly_layout("Profitability (PBIT/Sales) Trend", height=320)
    lay["yaxis_title"] = "Profitability (%)"
    fig_prof.update_layout(**lay)

    # PBIT vs PBT area (interest burden visual)
    if "pbit" in df.columns and "pbt" in df.columns:
        fig_earn = go.Figure()
        fig_earn.add_trace(go.Scatter(
            x=df["year"], y=df["pbit"],
            fill="tozeroy", mode="lines", name="PBIT",
            line=dict(color=PRIMARY, width=2), fillcolor=f"rgba(13,148,136,0.2)",
        ))
        fig_earn.add_trace(go.Scatter(
            x=df["year"], y=df["pbt"],
            fill="tozeroy", mode="lines", name="PBT",
            line=dict(color=ACCENT, width=2), fillcolor=f"rgba(249,115,22,0.2)",
        ))
        lay_earn = plotly_layout("PBIT vs PBT — Interest Burden", height=300)
        lay_earn["yaxis_title"] = "₹ Cr"
        fig_earn.update_layout(**lay_earn)
        figs = [fig_prof, fig_earn]
    else:
        figs = [fig_prof]

    # Insights
    insights, actions = [], []
    prof_now = row.get("profitability")
    if pd.notna(prof_now) and peers_df is not None and not peers_df.empty:
        p = _pct(peers_df["profitability"], prof_now)
        insights.append(
            f"Profitability ({_fmt(prof_now)}) is at the **{p}th percentile** of {cur_stage}-stage peers."
        )
    prof_5 = _last_n(company_df, 5)["profitability"]
    delta = prof_5.iloc[-1] - prof_5.iloc[0]
    if delta > 0.005:
        insights.append(
            f"5-year profitability trend is **improving** (+{delta*100:.1f}pp) — "
            "Pecking Order signal: growing internal funding capacity reduces debt dependence."
        )
    elif delta < -0.005:
        insights.append(
            f"5-year profitability trend is **declining** ({delta*100:.1f}pp) — "
            "monitor potential pressure on retained earnings and debt servicing capacity."
        )
    else:
        insights.append("Profitability has been broadly stable over 5 years.")
    actions = [
        "Declining profitability combined with rising leverage is a key board risk indicator.",
        "Improving profitability supports progressive deleveraging — communicate to credit analysts.",
        "Track PBIT vs PBT gap — widening gap indicates rising interest burden.",
    ]

    return {"figs": figs, "tables": [], "insights": insights,
            "actions": actions, "title": "Topic 4 — Profitability & Earnings"}


# ── Topic 5 — Asset Base & Tangibility ────────────────────────────────────────

def build_topic_5(company_df, company_info, peers_df, full_panel, stage_summary):
    df = _last_n(company_df, 10)
    row = _co_latest(company_df)
    cur_stage = company_info.get("current_stage", row.get("life_stage", ""))

    fig_tang = go.Figure()
    peer_tang = _peer_median(peers_df, "tangibility")
    if pd.notna(peer_tang):
        fig_tang.add_hline(y=peer_tang * 100, line_dash="dash", line_color=NEUTRAL,
                            annotation_text=f"Peer median {_fmt(peer_tang)}")
    fig_tang.add_trace(go.Scatter(
        x=df["year"], y=df["tangibility"] * 100,
        mode="lines+markers", name="Tangibility",
        line=dict(color=SECONDARY, width=2.5),
    ))
    lay = plotly_layout("Tangibility (Fixed Assets / Total Assets) Trend", height=320)
    lay["yaxis_title"] = "Tangibility (%)"
    fig_tang.update_layout(**lay)

    fig_ncfi = go.Figure()
    if "ncfi" in df.columns:
        colors = [ACCENT if v < 0 else PRIMARY for v in df["ncfi"]]
        fig_ncfi.add_trace(go.Bar(x=df["year"], y=df["ncfi"],
                                   marker_color=colors, name="NCFI"))
        _add_hline_zero(fig_ncfi)
        lay_ncfi = plotly_layout("Net Cash Flow from Investing (NCFI) — Capex Signal", height=300)
        lay_ncfi["yaxis_title"] = "₹ Cr"
        fig_ncfi.update_layout(**lay_ncfi)
        figs = [fig_tang, fig_ncfi]
    else:
        figs = [fig_tang]

    insights, actions = [], []
    tang_now = row.get("tangibility")

    # Always derive at least one insight from company's own trend (no peer dependency)
    tang_5 = _last_n(company_df, 5)["tangibility"]
    if len(tang_5) >= 2:
        delta_tang = tang_5.iloc[-1] - tang_5.iloc[0]
        direction_word = "improving" if delta_tang > 0.01 else ("declining" if delta_tang < -0.01 else "stable")
        insights.append(
            f"Tangibility trend (5-year): **{direction_word}** ({delta_tang*100:+.1f}pp) — "
            f"current level {_fmt(tang_now) if pd.notna(tang_now) else 'n/a'}."
        )
    elif pd.notna(tang_now):
        insights.append(f"Current tangibility: {_fmt(tang_now)} (fixed assets / total assets).")

    if pd.notna(tang_now) and peers_df is not None and not peers_df.empty:
        p = _pct(peers_df["tangibility"], tang_now)
        direction = "asset-heavy" if p > 60 else ("asset-light" if p < 40 else "average-asset-intensity")
        insights.append(
            f"Tangibility ({_fmt(tang_now)}) is at the **{p}th percentile** of peers — **{direction}**."
        )
        if p > 60:
            insights.append(
                "High tangibility provides stronger collateral coverage — "
                "Trade-Off theory supports higher leverage capacity."
            )
        else:
            insights.append(
                "Lower tangibility limits collateral — "
                "lenders may apply more conservative debt covenants."
            )
    actions = [
        "High tangibility firms can generally sustain higher leverage — validate against peer band.",
        "Negative NCFI (investment outflows) signals capital expansion — ensure funding mix is appropriate.",
        "If tangibility is declining, review asset disposal or depreciation-driven reduction.",
    ]

    return {"figs": figs, "tables": [], "insights": insights,
            "actions": actions, "title": "Topic 5 — Asset Base & Tangibility"}


# ── Topic 6 — Cash Flow Analysis ──────────────────────────────────────────────

def build_topic_6(company_df, company_info, peers_df, full_panel, stage_summary):
    df = _last_n(company_df, 10)
    row = _co_latest(company_df)

    # NCFO / NCFI / NCFF 3-line
    fig_cf = go.Figure()
    cf_cols = [("ncfo", "Operating (NCFO)", PRIMARY),
               ("ncfi", "Investing (NCFI)", SECONDARY),
               ("ncff", "Financing (NCFF)", ACCENT)]
    for col, label, color in cf_cols:
        if col in df.columns:
            fig_cf.add_trace(go.Scatter(
                x=df["year"], y=df[col],
                mode="lines+markers", name=label,
                line=dict(color=color, width=2),
            ))
    _add_hline_zero(fig_cf)
    lay = plotly_layout("Cash Flow Components (NCFO / NCFI / NCFF)", height=350)
    lay["yaxis_title"] = "₹ Cr"
    fig_cf.update_layout(**lay)

    # Dickinson sign pattern table
    if all(c in df.columns for c in ["ncfo", "ncfi", "ncff"]):
        sign_df = df[["year", "ncfo", "ncfi", "ncff", "life_stage"]].copy()
        sign_df["NCFO"] = sign_df["ncfo"].apply(lambda v: "+" if v >= 0 else "−")
        sign_df["NCFI"] = sign_df["ncfi"].apply(lambda v: "+" if v >= 0 else "−")
        sign_df["NCFF"] = sign_df["ncff"].apply(lambda v: "+" if v >= 0 else "−")
        sign_table = sign_df[["year", "NCFO", "NCFI", "NCFF", "life_stage"]].rename(
            columns={"life_stage": "Classified Stage"})
        tables = [sign_table]
    else:
        tables = []

    # FCF proxy bar
    if "ncfo" in df.columns and "ncfi" in df.columns:
        df = df.copy()
        df["fcf"] = df["ncfo"] + df["ncfi"]
        fcf_colors = [PRIMARY if v >= 0 else ACCENT for v in df["fcf"]]
        fig_fcf = go.Figure(go.Bar(x=df["year"], y=df["fcf"],
                                    marker_color=fcf_colors, name="Free Cash Flow"))
        _add_hline_zero(fig_fcf)
        lay_fcf = plotly_layout("Free Cash Flow Proxy (NCFO + NCFI)", height=280)
        lay_fcf["yaxis_title"] = "₹ Cr"
        fig_fcf.update_layout(**lay_fcf)
        figs = [fig_cf, fig_fcf]
    else:
        figs = [fig_cf]

    insights, actions = [], []
    ncfo_now = row.get("ncfo", 0)
    ncfi_now = row.get("ncfi", 0)
    ncff_now = row.get("ncff", 0)
    sign_pat = f"({'+'if ncfo_now >= 0 else '−'}, {'+'if ncfi_now >= 0 else '−'}, {'+'if ncff_now >= 0 else '−'})"
    stage = row.get("life_stage", "")
    insights.append(f"Current cashflow pattern: **{sign_pat}** (NCFO, NCFI, NCFF) → classified as **{stage}** stage.")
    fcf = ncfo_now + ncfi_now
    if fcf < 0:
        insights.append(
            f"Free cash flow proxy is **negative (₹{fcf:.0f} Cr)** — "
            "the firm is investing more than its operating cash generation; external financing may be required."
        )
    else:
        insights.append(
            f"Free cash flow proxy is **positive (₹{fcf:.0f} Cr)** — "
            "operating surplus exceeds investment outflow; internal funding capacity is intact."
        )
    actions = [
        "Negative NCFF (financing outflows) indicates net debt repayment — a deleveraging signal.",
        "Sustained negative NCFO is the primary IBC stress indicator — monitor closely.",
        "Review cashflow sign pattern year-over-year — a shift in NCFO sign triggers a stage reclassification.",
    ]

    return {"figs": figs, "tables": tables, "insights": insights,
            "actions": actions, "title": "Topic 6 — Cash Flow Analysis"}


# ── Topic 7 — Tax & Dividend Policy ───────────────────────────────────────────

def build_topic_7(company_df, company_info, peers_df, full_panel, stage_summary):
    df = _last_n(company_df, 10)
    row = _co_latest(company_df)
    cur_stage = company_info.get("current_stage", "")

    fig_tax = go.Figure()
    peer_tax = _peer_median(peers_df, "tax")
    if pd.notna(peer_tax):
        fig_tax.add_hline(y=peer_tax * 100, line_dash="dash", line_color=NEUTRAL,
                           annotation_text=f"Peer median {_fmt(peer_tax)}")
    fig_tax.add_trace(go.Scatter(
        x=df["year"], y=df["tax"] * 100,
        mode="lines+markers", name="Tax Rate",
        line=dict(color=PRIMARY, width=2.5),
    ))
    lay = plotly_layout("Effective Tax Rate Trend", height=300)
    lay["yaxis_title"] = "Tax Rate (%)"
    fig_tax.update_layout(**lay)

    fig_shield = go.Figure()
    if "tax_shield" in df.columns:
        fig_shield.add_trace(go.Bar(
            x=df["year"], y=df["tax_shield"] * 100,
            marker_color=SECONDARY, name="Tax Shield",
        ))
        lay_sh = plotly_layout("Tax Shield from Interest Deductibility", height=280)
        lay_sh["yaxis_title"] = "Tax Shield (%)"
        fig_shield.update_layout(**lay_sh)
        figs = [fig_tax, fig_shield]
    else:
        figs = [fig_tax]

    # Dividend classification
    df_d = df.copy()
    df_d["payer"] = df_d["dividend"].apply(lambda v: "Dividend Payer" if v > 0 else "Non-payer")
    payer_yrs = int((df_d["dividend"] > 0).sum())
    total_yrs = len(df_d)

    insights, actions = [], []
    tax_now = row.get("tax")
    if pd.notna(tax_now) and peers_df is not None and not peers_df.empty and "tax" in peers_df.columns:
        tp = _pct(peers_df["tax"], tax_now)
        insights.append(f"Effective tax rate ({_fmt(tax_now)}) is at the **{tp}th percentile** of {cur_stage} peers.")
    shield_now = row.get("tax_shield")
    if pd.notna(shield_now):
        insights.append(
            f"Tax shield value is **{_fmt(shield_now)}** — "
            f"{'above-average benefit from debt' if shield_now > 0.03 else 'modest debt tax benefit; scope to increase if leverage rises'}."
        )
    insights.append(
        f"Dividend paid in **{payer_yrs}/{total_yrs} years** ({round(payer_yrs/total_yrs*100)}% of period) — "
        f"{'consistent payer — signals earnings confidence' if payer_yrs > total_yrs*0.7 else 'intermittent — review payout policy consistency'}."
    )
    actions = [
        "Higher tax rate firms gain more from interest deductibility — review optimal leverage for tax shield.",
        "Consistent dividend payment alongside high leverage may strain free cash flow — review payout ratio.",
        "Tax shield quantifies the direct cost savings from debt — include in optimal structure calculation.",
    ]

    return {"figs": figs, "tables": [], "insights": insights,
            "actions": actions, "title": "Topic 7 — Tax & Dividend Policy"}


# ── Topic 8 — Peer Benchmarking ───────────────────────────────────────────────

def build_topic_8(company_df, company_info, peers_df, full_panel, stage_summary):
    row = _co_latest(company_df)
    cur_stage = company_info.get("current_stage", row.get("life_stage", ""))

    # Box plot — leverage distribution, focal firm highlighted
    fig_box = go.Figure()
    stage_firms = full_panel[full_panel["life_stage"] == cur_stage] if full_panel is not None and not full_panel.empty else pd.DataFrame()
    if not stage_firms.empty:
        latest_stage = stage_firms.sort_values("year").groupby("company_code").last().reset_index()
        fig_box.add_trace(go.Box(
            y=latest_stage["leverage"] * 100,
            name=f"{cur_stage} peers",
            marker_color=STAGE_COLORS.get(cur_stage, PRIMARY),
            boxpoints="outliers",
        ))
    co_lev = row.get("leverage")
    if pd.notna(co_lev):
        fig_box.add_trace(go.Scatter(
            x=[f"{cur_stage} peers"], y=[co_lev * 100],
            mode="markers",
            marker=dict(color=ACCENT, size=14, symbol="diamond"),
            name=company_info["name"],
        ))
    fig_box.update_layout(**plotly_layout(f"Leverage Distribution — {cur_stage} Stage Peers", height=360))

    # Radar chart — 6 metrics vs peer median
    radar_metrics = ["leverage", "profitability", "tangibility", "tax", "tax_shield", "dividend"]
    radar_labels = ["Leverage", "Profitability", "Tangibility", "Tax Rate", "Tax Shield", "Dividend"]
    if peers_df is not None and not peers_df.empty:
        co_vals, peer_vals = [], []
        for m in radar_metrics:
            co_v = row.get(m, 0)
            p_v = _peer_median(peers_df, m)
            co_vals.append(float(co_v) if pd.notna(co_v) else 0)
            peer_vals.append(float(p_v) if pd.notna(p_v) else 0)
        # Normalise 0–100 for spider
        max_v = [max(abs(c), abs(p), 1e-9) for c, p in zip(co_vals, peer_vals)]
        co_norm = [c / m * 100 for c, m in zip(co_vals, max_v)]
        peer_norm = [p / m * 100 for p, m in zip(peer_vals, max_v)]
        fig_radar = go.Figure()
        fig_radar.add_trace(go.Scatterpolar(r=co_norm + [co_norm[0]], theta=radar_labels + [radar_labels[0]],
                                             fill="toself", name=company_info["name"],
                                             line=dict(color=PRIMARY)))
        fig_radar.add_trace(go.Scatterpolar(r=peer_norm + [peer_norm[0]], theta=radar_labels + [radar_labels[0]],
                                             fill="toself", name="Peer Median",
                                             line=dict(color=NEUTRAL, dash="dash"),
                                             opacity=0.5))
        fig_radar.update_layout(**plotly_layout("Multi-Metric Profile vs Peer Median", height=380))
        figs = [fig_box, fig_radar]
    else:
        figs = [fig_box]

    # Peer table
    if peers_df is not None and not peers_df.empty:
        display_cols = ["company_name", "life_stage", "leverage", "profitability", "tangibility"]
        display_cols = [c for c in display_cols if c in peers_df.columns]
        peer_table = peers_df[display_cols].head(15).copy()
        for c in ["leverage", "profitability", "tangibility"]:
            if c in peer_table.columns:
                peer_table[c] = (peer_table[c] * 100).round(1).astype(str) + "%"
        tables = [peer_table]
    else:
        tables = []

    insights, actions = [], []
    if not stage_firms.empty and pd.notna(co_lev):
        latest_stage = stage_firms.sort_values("year").groupby("company_code").last().reset_index()
        p25 = latest_stage["leverage"].quantile(0.25)
        p75 = latest_stage["leverage"].quantile(0.75)
        lev_pct = _pct(latest_stage["leverage"], co_lev)
        if co_lev < p25:
            insights.append(f"Leverage ({_fmt(co_lev)}) is **below the peer 25th percentile** ({_fmt(p25)}) — under-leveraged relative to {cur_stage} peers.")
        elif co_lev > p75:
            insights.append(f"Leverage ({_fmt(co_lev)}) **exceeds the peer 75th percentile** ({_fmt(p75)}) — above the typical {cur_stage} range.")
        else:
            insights.append(f"Leverage ({_fmt(co_lev)}) is **within the optimal peer band** ({_fmt(p25)}–{_fmt(p75)}) — well-positioned.")
        insights.append(f"Leverage percentile rank among {cur_stage} peers: **{lev_pct}th**.")
    peer_n = len(peers_df) if peers_df is not None else 0
    insights.append(f"Peer set: **{peer_n} firms** in {cur_stage} stage with similar size (±1 decile).")
    actions = [
        "The top-quartile peer (lowest leverage in band) is your deleveraging benchmark.",
        "Radar divergence on profitability vs peers is a key value creation opportunity.",
        "Custom peer set: use the sidebar company filter to create a bespoke comparison set.",
    ]

    return {"figs": figs, "tables": tables, "insights": insights,
            "actions": actions, "title": "Topic 8 — Peer Benchmarking"}


# ── Topic 9 — Capital Structure Optimisation ──────────────────────────────────

def build_topic_9(company_df, company_info, peers_df, full_panel, stage_summary):
    row = _co_latest(company_df)
    cur_stage = company_info.get("current_stage", row.get("life_stage", ""))
    co_lev = row.get("leverage", np.nan)

    # Peer distribution for optimal band
    if full_panel is not None and not full_panel.empty:
        stage_latest = full_panel[full_panel["life_stage"] == cur_stage].sort_values("year").groupby("company_code").last().reset_index()
        p25 = stage_latest["leverage"].quantile(0.25)
        p50 = stage_latest["leverage"].quantile(0.50)
        p75 = stage_latest["leverage"].quantile(0.75)
    else:
        p25, p50, p75 = 0.25, 0.40, 0.55

    # Gauge chart
    gauge_val = float(co_lev * 100) if pd.notna(co_lev) else 0
    fig_gauge = go.Figure(go.Indicator(
        mode="gauge+number+delta",
        value=gauge_val,
        delta={"reference": float(p50 * 100), "valueformat": ".1f"},
        title={"text": f"Leverage vs {cur_stage} Optimal Band (%)"},
        gauge={
            "axis": {"range": [0, max(100, gauge_val * 1.2)]},
            "bar": {"color": PRIMARY},
            "steps": [
                {"range": [0, p25 * 100], "color": "#FEF3C7"},
                {"range": [p25 * 100, p75 * 100], "color": "#D1FAE5"},
                {"range": [p75 * 100, 100], "color": "#FEE2E2"},
            ],
            "threshold": {"line": {"color": SECONDARY, "width": 3},
                          "thickness": 0.75, "value": p75 * 100},
        },
    ))
    fig_gauge.update_layout(**plotly_layout("", height=300))

    # Scenario table
    scenarios = []
    for label, delta_lev in [("−20% debt", -0.20), ("−10% debt", -0.10),
                               ("Current", 0), ("+10% debt", 0.10), ("+20% debt", 0.20)]:
        new_lev = max(0, float(co_lev or 0) * (1 + delta_lev))
        pct_rank = _pct(stage_latest["leverage"] if full_panel is not None and not full_panel.empty else pd.Series([co_lev]), new_lev)
        in_band = "✓ In band" if p25 <= new_lev <= p75 else ("↓ Under" if new_lev < p25 else "↑ Over")
        scenarios.append({
            "Scenario": label,
            "Leverage": f"{new_lev*100:.1f}%",
            "Peer Percentile": f"{pct_rank}th",
            "vs Optimal Band": in_band,
        })
    scen_df = pd.DataFrame(scenarios)

    # Debt headroom bar
    headroom = max(0, (p75 - float(co_lev or 0)))
    headroom_cr = headroom * float(row.get("total_capital", 0) or 0) if row.get("total_capital") else None
    fig_head = go.Figure(go.Bar(
        x=["Current Leverage", "75th Percentile Threshold", "Headroom"],
        y=[float(co_lev or 0) * 100, p75 * 100, headroom * 100],
        marker_color=[PRIMARY, NEUTRAL, SECONDARY],
    ))
    fig_head.update_layout(**plotly_layout("Debt Headroom to 75th Peer Percentile", height=280))

    insights, actions = [], []
    if pd.notna(co_lev):
        if co_lev < p25:
            insights.append(f"Leverage ({_fmt(co_lev)}) is **below** the optimal peer band ({_fmt(p25)}–{_fmt(p75)}) — potential untapped debt capacity.")
        elif co_lev > p75:
            insights.append(f"Leverage ({_fmt(co_lev)}) **exceeds** the 75th peer percentile ({_fmt(p75)}) — above optimal range.")
        else:
            insights.append(f"Leverage is **within the optimal peer band** ({_fmt(p25)}–{_fmt(p75)}) — well-positioned.")
        headroom_pct = headroom * 100
        insights.append(f"Debt headroom to 75th percentile: **{headroom_pct:.1f}pp**" +
                         (f" (≈ ₹{headroom_cr:.0f} Cr)" if headroom_cr else "") + ".")
    actions = [
        "The ±20% scenario table provides the board with a clear range of feasible outcomes.",
        "Headroom calculation should be updated when peer panel is refreshed annually.",
        "For capital raise decisions: target leverage in the 40th–60th peer percentile range.",
    ]

    return {"figs": [fig_gauge, fig_head], "tables": [scen_df], "insights": insights,
            "actions": actions, "title": "Topic 9 — Capital Structure Optimisation"}


# ── Topic 10 — Forward View & Strategy ────────────────────────────────────────

def build_topic_10(company_df, company_info, peers_df, full_panel, stage_summary):
    from models.survival import prepare_transition_data, get_transition_matrix

    cur_stage = company_info.get("current_stage", _co_latest(company_df).get("life_stage", ""))
    figs, tables, insights, actions = [], [], [], []

    # Transition probability matrix
    if full_panel is not None and not full_panel.empty:
        try:
            trans_df = prepare_transition_data(full_panel)
            tmat = get_transition_matrix(trans_df)
            if not tmat.empty:
                ordered = [s for s in STAGE_ORDER if s in tmat.index]
                tmat = tmat.reindex(index=ordered, columns=[s for s in STAGE_ORDER if s in tmat.columns]).fillna(0)
                fig_tmat = px.imshow(
                    tmat * 100,
                    color_continuous_scale="Blues",
                    aspect="auto",
                    labels={"color": "Probability (%)"},
                    text_auto=".1f",
                )
                lay_tm = plotly_layout("Stage Transition Probability Matrix (%)", height=400)
                fig_tmat.update_layout(**lay_tm)
                figs.append(fig_tmat)
                tables.append(tmat.round(3).reset_index().rename(columns={"index": "From Stage"}))

                if cur_stage in tmat.index:
                    row_probs = tmat.loc[cur_stage].sort_values(ascending=False)
                    top_next = row_probs.index[0] if row_probs.index[0] != cur_stage else row_probs.index[1] if len(row_probs) > 1 else "Unknown"
                    top_prob = float(row_probs.iloc[0] if row_probs.index[0] != cur_stage else row_probs.iloc[1]) * 100
                    stay_prob = float(tmat.loc[cur_stage, cur_stage]) * 100 if cur_stage in tmat.columns else 0
                    insights.append(
                        f"Probability of **remaining in {cur_stage}** stage next year: **{stay_prob:.0f}%**."
                    )
                    insights.append(
                        f"Most likely transition: **{top_next}** ({top_prob:.0f}% historical base rate)."
                    )
        except Exception:
            pass

    # Next-stage capital norms
    if stage_summary is not None and not stage_summary.empty:
        norms = stage_summary.groupby("life_stage")[["avg_leverage", "avg_profitability", "avg_tangibility"]].mean().round(3)
        norms = norms.reindex([s for s in STAGE_ORDER if s in norms.index])
        tables.append(norms.reset_index().rename(columns={"life_stage": "Stage"}))

    if not insights:
        insights.append(f"Historical transition data analysed for all {full_panel['company_code'].nunique() if full_panel is not None and not full_panel.empty else 'N/A'} panel firms.")
    actions = [
        f"If transitioning from {cur_stage} to the next stage, review leverage targets vs that stage's peer band.",
        "Capital structure should lead the stage transition, not lag it — pre-position before reclassification.",
        "High stay-probability in current stage allows longer-term structural decisions.",
    ]

    return {"figs": figs, "tables": tables, "insights": insights,
            "actions": actions, "title": "Topic 10 — Forward View & Strategy"}


# ── Topic 11 — Risk & Stress Testing ──────────────────────────────────────────

def build_topic_11(company_df, company_info, peers_df, full_panel, stage_summary):
    row = _co_latest(company_df)
    df = company_df.sort_values("year")

    pbit = row.get("pbit", row.get("profitability", 0) * row.get("firm_size", 1))
    interest = row.get("interest_amt", 0)
    base_cover = pbit / interest if interest and interest > 0 else None

    # Interest rate shock scenarios
    shock_rows = []
    for label, bp_shock in [("Base (no shock)", 0), ("+200bp", 200), ("+400bp", 400)]:
        extra_cost = float(row.get("borrowings", 0) or 0) * bp_shock / 10000
        adj_interest = float(interest or 0) + extra_cost
        cover_adj = float(pbit) / adj_interest if adj_interest > 0 else None
        flag = "✓" if (cover_adj or 0) >= 3 else ("⚠" if (cover_adj or 0) >= 1.5 else "✗")
        shock_rows.append({
            "Scenario": label,
            "Extra Interest (₹ Cr)": f"{extra_cost:.1f}",
            "Adj. Coverage (x)": f"{cover_adj:.2f}" if cover_adj else "N/A",
            "Status": flag,
        })
    stress_df = pd.DataFrame(shock_rows)

    # Earnings stress
    earn_rows = []
    for label, pct_shock in [("Base", 0), ("PBIT −20%", -20), ("PBIT −40%", -40)]:
        adj_pbit = float(pbit) * (1 + pct_shock / 100)
        cover_e = adj_pbit / float(interest) if interest and interest > 0 else None
        flag = "✓" if (cover_e or 0) >= 3 else ("⚠" if (cover_e or 0) >= 1.5 else "✗")
        earn_rows.append({"Scenario": label, "Adj PBIT": f"₹{adj_pbit:.0f} Cr",
                          "Coverage (x)": f"{cover_e:.2f}" if cover_e else "N/A",
                          "Status": flag})
    earn_df = pd.DataFrame(earn_rows)

    # GFC / COVID resilience line
    fig_ev = go.Figure()
    for col, label, color in [("leverage", "Leverage", PRIMARY),
                                ("profitability", "Profitability", SECONDARY)]:
        if col in df.columns:
            fig_ev.add_trace(go.Scatter(x=df["year"], y=df[col] * 100,
                                         mode="lines+markers", name=label,
                                         line=dict(color=color, width=2)))
    for yr, name, color in [(2009, "GFC", "#EF4444"), (2020, "COVID", "#F59E0B")]:
        fig_ev.add_vline(x=yr, line_dash="dot", line_color=color,
                          annotation_text=name, annotation_position="top")
    fig_ev.update_layout(**plotly_layout("Key Metrics Through GFC & COVID", height=320))
    figs = [fig_ev]

    insights, actions = [], []
    if base_cover is not None:
        flag = "✓ healthy" if base_cover >= 3 else ("⚠ watch" if base_cover >= 1.5 else "✗ critical")
        insights.append(f"Current interest coverage: **{base_cover:.1f}x** ({flag}).")
        if base_cover < 3:
            insights.append(
                "Coverage below 3x — a +200bp rate shock or 20% PBIT decline could push coverage "
                "below the IBC threshold of 1.5x."
            )
    ibc_yrs = int(df.get("ibc_2016", pd.Series([0])).sum()) if "ibc_2016" in df.columns else 0
    if ibc_yrs > 0:
        insights.append(f"IBC stress flag active for **{ibc_yrs} year(s)** in historical record.")
    actions = [
        "Present the +200bp / +400bp scenario table to the board alongside any debt raise proposal.",
        "If any scenario results in ✗ (coverage < 1.5x), include covenant waiver contingency.",
        "GFC/COVID resilience analysis demonstrates institutional memory — include in investor presentations.",
    ]

    return {"figs": figs, "tables": [stress_df, earn_df], "insights": insights,
            "actions": actions, "title": "Topic 11 — Risk & Stress Testing"}


# ── Topic 12 — SEBI / Regulatory Compliance ───────────────────────────────────

def build_topic_12(company_df, company_info, peers_df, full_panel, stage_summary):
    df = company_df.sort_values("year").copy()
    # D/E ratio from leverage: leverage = D/(D+E) → D/E = leverage/(1-leverage)
    df["de_ratio"] = df["leverage"].apply(
        lambda v: v / (1 - v) if pd.notna(v) and v < 1 else np.nan
    )
    # SEBI LODR — general D/E guideline: typically ≤ 2:1 for most sectors
    SEBI_DE_THRESHOLD = 2.0
    df["de_status"] = df["de_ratio"].apply(
        lambda v: "✓ Compliant" if pd.notna(v) and v <= SEBI_DE_THRESHOLD
        else ("✗ Breach" if pd.notna(v) else "N/A")
    )
    df["coverage_status"] = df.apply(
        lambda r: "✓" if (r.get("pbit", 0) / r.get("interest_amt", 1) >= 1.5
                          if r.get("interest_amt", 0) > 0 else True)
        else "✗ IBC risk", axis=1
    )

    # D/E trend
    fig_de = go.Figure()
    fig_de.add_hline(y=SEBI_DE_THRESHOLD, line_dash="dot", line_color=ACCENT,
                     annotation_text=f"SEBI threshold {SEBI_DE_THRESHOLD}:1",
                     annotation_position="top right")
    colors = [PRIMARY if v <= SEBI_DE_THRESHOLD else ACCENT
              for v in df["de_ratio"].fillna(0)]
    fig_de.add_trace(go.Bar(x=df["year"], y=df["de_ratio"],
                             marker_color=colors, name="D/E Ratio"))
    fig_de.update_layout(**plotly_layout("Debt-to-Equity Ratio vs SEBI Threshold", height=320))

    # Compliance summary table
    comp_table = df[["year", "de_ratio", "de_status", "coverage_status"]].tail(10).copy()
    comp_table["de_ratio"] = comp_table["de_ratio"].round(2)
    comp_table.columns = ["Year", "D/E Ratio", "SEBI D/E Status", "IBC Coverage Status"]

    # Peer compliance %
    insights, actions = [], []
    recent_de = df["de_ratio"].iloc[-1] if not df.empty else np.nan
    if pd.notna(recent_de):
        status = "compliant" if recent_de <= SEBI_DE_THRESHOLD else "above SEBI threshold"
        insights.append(f"Current D/E ratio: **{recent_de:.2f}** — **{status}** (SEBI LODR guideline ≤ {SEBI_DE_THRESHOLD}).")
    breaches = int((df["de_ratio"] > SEBI_DE_THRESHOLD).sum())
    if breaches > 0:
        insights.append(f"D/E ratio breached the {SEBI_DE_THRESHOLD} threshold in **{breaches} year(s)** historically.")
    else:
        insights.append("D/E ratio has remained within SEBI LODR guidelines throughout the analysis period.")
    if peers_df is not None and not peers_df.empty and "leverage" in peers_df.columns:
        peers_de = peers_df["leverage"].apply(lambda v: v / (1 - v) if pd.notna(v) and v < 1 else np.nan)
        compliant_pct = int((peers_de <= SEBI_DE_THRESHOLD).mean() * 100)
        insights.append(f"**{compliant_pct}%** of {company_info.get('current_stage', '')} peers are currently SEBI-compliant on D/E.")
    actions = [
        "Include SEBI LODR D/E compliance status in every board risk register.",
        "If D/E is approaching 2:1, pre-approve an equity raise contingency before debt commitment.",
        "IBC coverage status should be monitored quarterly — flag any year below 1.5x immediately.",
    ]

    return {"figs": [fig_de], "tables": [comp_table], "insights": insights,
            "actions": actions, "title": "Topic 12 — SEBI / Regulatory Compliance"}


# ── Topic 13 — Recommendations ────────────────────────────────────────────────

def build_topic_13(company_df, company_info, peers_df, full_panel, stage_summary):
    """
    Data-driven recommendations synthesised from Topics 1–12.
    No LLM — all insights derived from actual computed values.
    """
    row = _co_latest(company_df)
    cur_stage = company_info.get("current_stage", row.get("life_stage", "Unknown"))
    co_lev = row.get("leverage", np.nan)
    co_prof = row.get("profitability", np.nan)
    co_tang = row.get("tangibility", np.nan)
    interest = row.get("interest_amt", 0)
    pbit = row.get("pbit", 0)
    base_cover = pbit / interest if interest and interest > 0 else None

    # Peer band
    if full_panel is not None and not full_panel.empty and "life_stage" in full_panel.columns:
        stage_latest = full_panel[full_panel["life_stage"] == cur_stage].sort_values("year").groupby("company_code").last().reset_index()
        p25 = stage_latest["leverage"].quantile(0.25)
        p75 = stage_latest["leverage"].quantile(0.75)
    else:
        p25, p75 = 0.25, 0.60

    insights, actions = [], []

    # Leverage position
    if pd.notna(co_lev):
        if co_lev < p25:
            insights.append(
                f"**Leverage ({_fmt(co_lev)}) is below the {cur_stage}-stage peer band** ({_fmt(p25)}–{_fmt(p75)}). "
                "The firm has unused debt capacity that could fund growth or enhance returns."
            )
            actions.append(f"Evaluate a controlled leverage increase towards the 40th–60th peer percentile.")
        elif co_lev > p75:
            insights.append(
                f"**Leverage ({_fmt(co_lev)}) exceeds the 75th peer percentile** ({_fmt(p75)}). "
                "Prioritise debt reduction to bring leverage within the optimal band."
            )
            actions.append("Develop a 2–3 year deleveraging roadmap targeting the peer median.")
        else:
            insights.append(
                f"Leverage ({_fmt(co_lev)}) is **within the optimal peer band** ({_fmt(p25)}–{_fmt(p75)}). "
                "Maintain current structure while monitoring for stage transitions."
            )
            actions.append("Maintain leverage within peer band; review if life stage changes.")

    # Profitability signal
    if pd.notna(co_prof):
        prof_5 = _last_n(company_df, 5)["profitability"]
        delta = prof_5.iloc[-1] - prof_5.iloc[0]
        if delta > 0.005:
            insights.append(
                f"Profitability **improved** by {delta*100:.1f}pp over 5 years — "
                "Pecking Order dynamics support reduced external debt reliance."
            )
            actions.append("Channel improving profitability into internal debt reduction before external equity.")
        elif delta < -0.005:
            insights.append(
                f"Profitability **declined** by {abs(delta)*100:.1f}pp over 5 years — "
                "review cost structure before committing to additional fixed-charge debt."
            )
            actions.append("Stabilise profitability before any further leverage increase.")

    # Interest coverage
    if base_cover is not None:
        if base_cover < 1.5:
            insights.append(
                f"**Interest coverage ({base_cover:.1f}x) is critical** — below the IBC threshold of 1.5x. "
                "Immediate board escalation recommended."
            )
            actions.append("Engage lenders on covenant relief; initiate emergency deleveraging plan.")
        elif base_cover < 3:
            insights.append(
                f"Interest coverage ({base_cover:.1f}x) is below the healthy 3x threshold. "
                "A +200bp rate shock or 20% PBIT decline could breach IBC threshold."
            )
            actions.append("Stress-test coverage quarterly; consider interest rate hedging.")

    # Tangibility & Trade-Off
    if pd.notna(co_tang) and peers_df is not None and not peers_df.empty and "tangibility" in peers_df.columns:
        tp = _pct(peers_df["tangibility"], co_tang)
        if tp > 65 and pd.notna(co_lev) and co_lev < p25:
            insights.append(
                f"High tangibility ({_fmt(co_tang)}, {tp}th peer percentile) provides strong collateral — "
                "Trade-Off theory supports higher leverage than current level."
            )

    if not insights:
        insights.append("Analysis complete. Review individual topic sections for detailed findings.")
    if not actions:
        actions.append("No urgent actions identified — maintain current capital structure policy.")

    # Summary figure (traffic light)
    status_items = []
    if pd.notna(co_lev):
        in_band = p25 <= co_lev <= p75
        status_items.append(("Leverage Position", "✓" if in_band else "⚠", PRIMARY if in_band else ACCENT))
    if base_cover is not None:
        cover_ok = base_cover >= 3
        status_items.append(("Interest Coverage", "✓" if cover_ok else "⚠", PRIMARY if cover_ok else ACCENT))
    if pd.notna(co_prof):
        prof_ok = co_prof > 0
        status_items.append(("Profitability", "✓" if prof_ok else "⚠", PRIMARY if prof_ok else ACCENT))

    fig_traffic = go.Figure()
    for i, (label, mark, color) in enumerate(status_items):
        fig_traffic.add_trace(go.Indicator(
            mode="number",
            value=1,
            number={"prefix": mark + " ", "font": {"size": 30, "color": color}},
            title={"text": label},
            domain={"row": 0, "column": i},
        ))
    if status_items:
        fig_traffic.update_layout(
            grid={"rows": 1, "columns": len(status_items), "pattern": "independent"},
            **plotly_layout("Capital Structure Health Check", height=160),
        )
        figs = [fig_traffic]
    else:
        figs = []

    return {"figs": figs, "tables": [], "insights": insights,
            "actions": actions, "title": "Topic 13 — Recommendations & Actions"}


def build_topic_13_ai(company_code: int, panel_mode: str = "thesis", backend: str = "ollama") -> dict:
    """Topic 13: AI Recommendations — four sub-topics via LLM with rule-based fallback.

    13.1 Capital structure positioning vs peers
    13.2 Determinants most relevant to this firm
    13.3 5-year leverage trajectory diagnosis
    13.4 Three actionable recommendations

    Returns dict: {figs: [], tables: [], insights: [(label, [bullets])], actions: [str], ai_offline: bool}
    """
    out = {"figs": [], "tables": [], "insights": [], "actions": [], "ai_offline": False}

    try:
        from models.llm_adapters import (
            build_company_context, stream_ollama, stream_anthropic,
        )
        ctx = build_company_context(company_code, panel_mode=panel_mode)
        sub_prompts = {
            "13.1 Positioning vs peers": (
                "Using ONLY the COMPANY and PEER GROUP data above, write 2 bullet "
                "points (max 30 words each) describing how this firm is positioned "
                "relative to its peer group on leverage and profitability. Cite exact numbers."
            ),
            "13.2 Relevant determinants": (
                "Using ONLY the data above, write 2 bullets identifying which "
                "balance-sheet drivers (firm_size, profitability, tangibility, age) are "
                "most relevant for this firm's capital-structure decisions. Cite values."
            ),
            "13.3 Trajectory diagnosis": (
                "Using ONLY the 5-Year Trend line above, write 2 bullets diagnosing "
                "the leverage trajectory (rising/falling/stable, magnitude, consistency)."
            ),
            "13.4 Three actions": (
                "Based ONLY on the data above, propose THREE specific, "
                "evidence-grounded recommendations the CFO could consider. Each "
                "recommendation: <=25 words, cite at least one figure."
            ),
        }
        bullets_per_topic = {}
        for label, prompt in sub_prompts.items():
            messages = [{"role": "user", "content": prompt}]
            if backend == "anthropic":
                chunks = list(stream_anthropic(messages, system=ctx))
            else:
                chunks = list(stream_ollama(
                    [{"role": "system", "content": ctx}] + messages
                ))
            text = "".join(chunks).strip()
            if text.startswith("[") and any(
                kw in text.lower() for kw in ("not installed", "not configured", "error")
            ):
                raise RuntimeError(f"LLM backend offline: {text}")
            lines = [
                l.lstrip("-*• \t").strip()
                for l in text.splitlines() if l.strip()
            ]
            bullets = [l for l in lines if len(l) >= 12][:4]
            if not bullets:
                bullets = [text[:300]]
            bullets_per_topic[label] = bullets

        out["insights"] = [
            ("13.1 Positioning vs peers", bullets_per_topic["13.1 Positioning vs peers"]),
            ("13.2 Relevant determinants", bullets_per_topic["13.2 Relevant determinants"]),
            ("13.3 Trajectory diagnosis", bullets_per_topic["13.3 Trajectory diagnosis"]),
        ]
        out["actions"] = bullets_per_topic["13.4 Three actions"]
        return out

    except Exception:
        out["ai_offline"] = True
        try:
            import db
            import pandas as pd
            conn = db.get_connection()
            vintage_sql, vintage_params = db._vintage_predicate(panel_mode)
            sql = f"""
                SELECT year, leverage, profitability, life_stage, industry_group
                FROM financials
                WHERE company_code = ? AND {vintage_sql}
                ORDER BY year DESC LIMIT 1
            """
            row = pd.read_sql_query(
                sql, conn, params=[int(company_code)] + vintage_params
            )
            if not row.empty:
                r = row.iloc[0]
                lev = float(r.get("leverage", 0) or 0)
                prof = float(r.get("profitability", 0) or 0)
                stage = str(r.get("life_stage", "Unknown"))
                ind = str(r.get("industry_group", "Unknown"))
                out["insights"] = [
                    ("13.1 Positioning vs peers", [
                        f"Current leverage: {lev:.3f} (industry {ind}, stage {stage}).",
                        f"Profitability at latest year: {prof:.3f}.",
                    ]),
                    ("13.2 Relevant determinants", [
                        "firm_size, profitability, tangibility, and age are the four core "
                        "regressors validated in this thesis panel.",
                    ]),
                    ("13.3 Trajectory diagnosis", [
                        "AI offline — refer to the leverage trend chart on the dashboard.",
                    ]),
                ]
                out["actions"] = [
                    f"Review leverage of {lev:.3f} against the {stage}-stage peer median.",
                    "Stress-test capital structure under +/-200bps interest-rate scenarios.",
                    "Consult Page 8 (Econometrics) for stage-specific OLS coefficients.",
                ]
            else:
                out["insights"] = [("13 AI Recommendations", [f"Company code {company_code} not found."])]
                out["actions"] = ["Verify company_code and try again."]
        except Exception:
            out["insights"] = [("13 AI Recommendations", ["AI offline; data unavailable."])]
            out["actions"] = ["Try again with LLM backend configured."]
        return out


# ── Dispatch table ─────────────────────────────────────────────────────────────

TOPIC_BUILDERS = {
    1:  build_topic_1,
    2:  build_topic_2,
    3:  build_topic_3,
    4:  build_topic_4,
    5:  build_topic_5,
    6:  build_topic_6,
    7:  build_topic_7,
    8:  build_topic_8,
    9:  build_topic_9,
    10: build_topic_10,
    11: build_topic_11,
    12: build_topic_12,
    13: build_topic_13,
}

TOPIC_LABELS = {
    1:  "Executive Summary",
    2:  "Corporate Life Cycle",
    3:  "Capital Structure Profile",
    4:  "Profitability & Earnings",
    5:  "Asset Base & Tangibility",
    6:  "Cash Flow Analysis",
    7:  "Tax & Dividend Policy",
    8:  "Peer Benchmarking",
    9:  "Capital Structure Optimisation",
    10: "Forward View & Strategy",
    11: "Risk & Stress Testing",
    12: "SEBI / Regulatory Compliance",
    13: "Recommendations & Actions",
}
