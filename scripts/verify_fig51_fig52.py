"""
Standalone verification script -- Thesis Figure 5.1 & 5.2
==========================================================
Builds the two thesis infographics directly from the SQLite DB (no Streamlit).
Outputs:
  verify_frames/thesis_fig51.html   -- stage-wise  (8 bars per row)
  verify_frames/thesis_fig52.html   -- year-wise  (25 bars per row)

Run:
    py -3.12 scripts/verify_fig51_fig52.py

Open both HTML files in a browser and compare against the thesis screenshots.
"""

import os
import math
import sqlite3
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import plotly.colors as pc

# ── Config ────────────────────────────────────────────────────────────────────
DB_PATH  = "capital_structure.db"
OUT_DIR  = "verify_frames"
VINTAGE  = "thesis"
YEAR_MIN = 2001
YEAR_MAX = 2024

STAGE_ORDER = ["Startup", "Growth", "Maturity", "Shakeout1",
               "Shakeout2", "Shakeout3", "Decline", "Decay"]

METRICS = [
    ("leverage",      "Avg. Leverage"),
    ("log_size",      "Avg. Logsize"),
    ("profitability", "Avg. Profitability"),
    ("dividend",      "Avg. Dividend Payout"),
]

THESIS_STAGE_COLORS = {
    "Startup":    "#EF4444",
    "Growth":     "#14B8A6",
    "Maturity":   "#22C55E",
    "Shakeout1":  "#EAB308",
    "Shakeout2":  "#A855F7",
    "Shakeout3":  "#EC4899",
    "Decline":    "#16A34A",
    "Decay":      "#DC2626",
}

THESIS_VALUES = {
    "Startup":    dict(leverage=34.20, log_size=7.14, profitability=0.06,  dividend=19.72),
    "Growth":     dict(leverage=29.68, log_size=7.58, profitability=0.14,  dividend=22.93),
    "Maturity":   dict(leverage=18.96, log_size=7.87, profitability=0.19,  dividend=29.64),
    "Shakeout1":  dict(leverage=15.20, log_size=7.76, profitability=0.11,  dividend=32.25),
    "Shakeout2":  dict(leverage=32.50, log_size=4.20, profitability=0.10,  dividend=14.36),
    "Shakeout3":  dict(leverage=16.45, log_size=8.11, profitability=0.17,  dividend=48.83),
    "Decline":    dict(leverage=37.77, log_size=6.43, profitability=-0.13, dividend=20.93),
    "Decay":      dict(leverage=24.19, log_size=8.00, profitability=0.10,  dividend=38.61),
}

TEXT_FONT_SIZE  = 9   # uniform across all rows and both figures
TEXT_COLOR      = "#1f2937"
LABEL_FONT_SIZE = 10
TICK_FONT_SIZE  = 9
ROW_BG_COLOR    = "rgba(255,200,200,0.25)"   # alternating pink rows
BORDER_COLOR    = "#C026D3"


# ── Load data ─────────────────────────────────────────────────────────────────
def load_df() -> pd.DataFrame:
    con = sqlite3.connect(DB_PATH)
    query = """
        SELECT f.life_stage, f.year,
               f.leverage, f.profitability, f.dividend, f.firm_size
        FROM   financials f
        WHERE  f.vintage = ?
          AND  f.year BETWEEN ? AND ?
          AND  f.leverage    IS NOT NULL
          AND  f.profitability IS NOT NULL
          AND  f.dividend    IS NOT NULL
          AND  f.firm_size   IS NOT NULL
          AND  f.firm_size   > 0
    """
    df = pd.read_sql_query(query, con, params=(VINTAGE, YEAR_MIN, YEAR_MAX))
    con.close()
    df["log_size"] = df["firm_size"].apply(math.log)
    return df


# ── Console comparison table ───────────────────────────────────────────────────
def print_comparison(stage_means: pd.DataFrame) -> None:
    print("\n-- Stage-wise means vs thesis values --")
    print(f"{'Stage':<12} {'Metric':<22} {'Computed':>10} {'Thesis':>10} {'Delta':>8} {'OK?':>5}")
    print("-" * 70)
    for stage in STAGE_ORDER:
        if stage not in stage_means.index:
            print(f"{stage:<12}  *** NOT IN DATA ***")
            continue
        for col, label in METRICS:
            computed = stage_means.loc[stage, col]
            expected = THESIS_VALUES.get(stage, {}).get(col)
            if expected is None:
                continue
            delta = computed - expected
            ok = "OK" if abs(delta) < 0.5 else "DIFF"
            print(f"{stage:<12} {label:<22} {computed:>10.2f} {expected:>10.2f} {delta:>+8.2f} {ok:>5}")
    print()


# ── Y-axis range helper ────────────────────────────────────────────────────────
def _set_row_yrange(fig: go.Figure, row: int, vals: list, headroom: float = 0.30) -> None:
    """
    Set an explicit y-axis range so 'outside' text labels are never clipped.
    headroom: fraction of value span added above the tallest bar (default 30%).
    """
    valid = [v for v in vals if v is not None and not math.isnan(v)]
    if not valid:
        return
    hi = max(valid)
    lo = min(valid)
    span = (hi - lo) if hi != lo else (abs(hi) + 0.5)
    top_pad = span * headroom
    # For rows that include negative values (e.g. profitability), keep some space below too
    if lo < 0:
        bot_pad = span * 0.20
        ymin = lo - bot_pad
    else:
        ymin = 0.0
    ymax = hi + top_pad
    fig.update_yaxes(range=[ymin, ymax], row=row, col=1)


# ── Alternating row backgrounds ───────────────────────────────────────────────
def _add_row_backgrounds(fig: go.Figure) -> None:
    """Shade rows 1 and 3 (Leverage, Profitability) with light pink."""
    for ax_key in ("yaxis", "yaxis3"):
        ax = getattr(fig.layout, ax_key, None)
        if ax is None:
            continue
        domain = ax.domain
        if domain:
            fig.add_shape(
                type="rect", xref="paper", yref="paper",
                x0=0, x1=1, y0=domain[0], y1=domain[1],
                fillcolor=ROW_BG_COLOR, line_width=0, layer="below",
            )


# ── Common layout ─────────────────────────────────────────────────────────────
def _apply_layout(fig: go.Figure, title: str, height: int, bargap: float) -> None:
    fig.update_layout(
        title=dict(
            text=title,
            font=dict(size=11, color="#1f2937", family="Inter, sans-serif"),
            x=0.5, xanchor="center",
        ),
        height=height,
        showlegend=False,
        paper_bgcolor="white",
        plot_bgcolor="white",
        font=dict(family="Inter, sans-serif", size=TEXT_FONT_SIZE),
        bargap=bargap,
        margin=dict(l=120, r=30, t=70, b=60),
        # Prevent ANY subplot from clipping bar text that overflows the plot area
        uniformtext=dict(mode=None),
    )
    for i, (_, label) in enumerate(METRICS, 1):
        ax = "yaxis" if i == 1 else f"yaxis{i}"
        fig.update_layout({ax: dict(
            title=dict(text=label, font=dict(size=LABEL_FONT_SIZE), standoff=12),
            tickfont=dict(size=TICK_FONT_SIZE),
            showgrid=True,
            gridcolor="#E5E7EB",
            zeroline=False,
            # automargin gives axis title room but does NOT fix text-above-bar clipping
            automargin=True,
        )})
    # Magenta border
    fig.add_shape(
        type="rect", xref="paper", yref="paper",
        x0=0, x1=1, y0=0, y1=1,
        line=dict(color=BORDER_COLOR, width=2),
        fillcolor="rgba(0,0,0,0)",
        layer="above",
    )


# ── Figure 5.1 — Stage-wise (8 bars × 4 rows) ────────────────────────────────
def build_fig51(df: pd.DataFrame):
    cols = ["leverage", "log_size", "profitability", "dividend"]
    stage_means = (
        df.groupby("life_stage")[cols].mean()
          .reindex([s for s in STAGE_ORDER if s in df["life_stage"].unique()])
    )
    stages = list(stage_means.index)

    fig = make_subplots(
        rows=4, cols=1,
        shared_xaxes=True,
        vertical_spacing=0.09,   # generous gap so top-of-bar text never bleeds into row above
        row_heights=[1, 1, 1, 1],
    )

    for row, (col, _) in enumerate(METRICS, 1):
        vals   = [stage_means.loc[s, col] for s in stages]
        colors = [THESIS_STAGE_COLORS.get(s, "#6B7280") for s in stages]
        fig.add_trace(go.Bar(
            x=stages,
            y=vals,
            marker_color=colors,
            text=[f"{v:.2f}" for v in vals],
            textposition="outside",
            textfont=dict(size=TEXT_FONT_SIZE, color=TEXT_COLOR),
            cliponaxis=False,           # KEY: text is never clipped at subplot boundary
            showlegend=False,
            hovertemplate="<b>%{x}</b><br>%{y:.2f}<extra></extra>",
        ), row=row, col=1)
        _set_row_yrange(fig, row, vals, headroom=0.30)

    _add_row_backgrounds(fig)
    _apply_layout(
        fig,
        "STAGE WISE -- MEAN LEVERAGE, MEAN LOG SIZE OF ASSETS,<br>"
        "MEAN PROFITABILITY AND DIVIDEND PAY OUT",
        height=950,
        bargap=0.30,
    )
    # X-axis labels only needed on bottom row (shared_xaxes=True hides them above)
    fig.update_xaxes(tickfont=dict(size=TICK_FONT_SIZE), tickangle=0, row=4, col=1)
    return fig, stage_means


# ── Figure 5.2 — Year-wise (25 bars × 4 rows) ────────────────────────────────
def build_fig52(df: pd.DataFrame):
    cols  = ["leverage", "log_size", "profitability", "dividend"]
    years = sorted(df["year"].unique())
    year_means = df.groupby("year")[cols].mean().reindex(years)

    palette     = pc.qualitative.Light24
    year_colors = {yr: palette[i % len(palette)] for i, yr in enumerate(years)}

    fig = make_subplots(
        rows=4, cols=1,
        shared_xaxes=True,
        vertical_spacing=0.09,
        row_heights=[1, 1, 1, 1],
    )

    for row, (col, _) in enumerate(METRICS, 1):
        vals   = [year_means.loc[yr, col] for yr in years]
        colors = [year_colors[yr] for yr in years]
        fig.add_trace(go.Bar(
            x=years,
            y=vals,
            marker_color=colors,
            text=[f"{v:.2f}" for v in vals],
            textposition="outside",
            textangle=-90,              # vertical text — prevents overlap on narrow bars
            textfont=dict(size=TEXT_FONT_SIZE, color=TEXT_COLOR),
            cliponaxis=False,
            showlegend=False,
            hovertemplate="<b>%{x}</b><br>%{y:.2f}<extra></extra>",
        ), row=row, col=1)
        # Extra headroom for vertical text: 60% of span (text is taller than horizontal)
        _set_row_yrange(fig, row, vals, headroom=0.60)

    _add_row_backgrounds(fig)
    _apply_layout(
        fig,
        "YEAR WISE -- MEAN LEVERAGE, MEAN LOG SIZE OF ASSETS,<br>"
        "MEAN PROFITABILITY AND DIVIDEND PAY OUT",
        height=1100,
        bargap=0.20,
    )
    # Show every year on x-axis, angled so they don't overlap
    fig.update_xaxes(
        tickmode="array",
        tickvals=years,
        ticktext=[str(yr) for yr in years],
        tickangle=-45,
        tickfont=dict(size=8),
        row=4, col=1,
    )
    return fig, year_means


# ── Main ──────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    os.makedirs(OUT_DIR, exist_ok=True)

    print(f"Loading thesis panel ({VINTAGE}, {YEAR_MIN}-{YEAR_MAX})...")
    df = load_df()
    print(f"  {len(df):,} rows  |  {df['life_stage'].nunique()} stages  |  {df['year'].nunique()} years")

    # Figure 5.1
    print("\nBuilding Figure 5.1 (stage-wise)...")
    fig51, stage_means = build_fig51(df)
    print_comparison(stage_means)
    out51 = os.path.join(OUT_DIR, "thesis_fig51.html")
    fig51.write_html(out51, include_plotlyjs="cdn")
    print(f"  Saved: {out51}")

    # Figure 5.2
    print("Building Figure 5.2 (year-wise)...")
    fig52, year_means = build_fig52(df)
    print("\n-- Year-wise spot check (thesis Fig 5.2) --")
    for yr, lev, logz in [(2001, 31.56, 6.03), (2024, 16.19, 9.00)]:
        if yr in year_means.index:
            c_lev  = year_means.loc[yr, "leverage"]
            c_logz = year_means.loc[yr, "log_size"]
            print(f"  {yr}: leverage {c_lev:.2f} (thesis {lev})  logsize {c_logz:.2f} (thesis {logz})")
    out52 = os.path.join(OUT_DIR, "thesis_fig52.html")
    fig52.write_html(out52, include_plotlyjs="cdn")
    print(f"  Saved: {out52}")

    print("\nDone. Open both files in a browser and compare against the thesis images.")
    print(f"  {out51}")
    print(f"  {out52}")
