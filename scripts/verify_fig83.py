"""
Standalone verification script -- Thesis Figure 8.3
====================================================
Two side-by-side scatter plots for Decline and Decay stages:
  Left : Leverage vs Profitability  (with OLS regression line per stage)
  Right: Leverage vs Tangibility    (with OLS regression line per stage)

Output: verify_frames/thesis_fig83.html

Run:
    py -3.12 scripts/verify_fig83.py

Open in browser and compare against thesis Figure 8.3 screenshot.
"""

import os
import math
import sqlite3
import sys

import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

# ── Config ────────────────────────────────────────────────────────────────────
DB_PATH  = "capital_structure.db"
OUT_DIR  = "verify_frames"
VINTAGE  = "thesis"
YEAR_MIN = 2001
YEAR_MAX = 2024

STAGES = ["Decline", "Decay"]

STAGE_CFG = {
    "Decline": {"color": "#22C55E", "label": "DECLINE STAGE"},
    "Decay":   {"color": "#EF4444", "label": "DECAY STAGE"},
}

BORDER_COLOR    = "#C026D3"
TEXT_COLOR      = "#1f2937"
TICK_FONT_SIZE  = 9
LABEL_FONT_SIZE = 10

# Axis visual ranges — match thesis figure
Y_RANGE    = [0, 150]          # leverage %
X_PROF     = [-1.0, 1.0]       # profitability (outliers clipped visually)
X_TANG     = [0.0,  1.0]       # tangibility


# ── Load data ─────────────────────────────────────────────────────────────────
def load_df() -> pd.DataFrame:
    con = sqlite3.connect(DB_PATH)
    query = """
        SELECT life_stage, leverage, profitability, tangibility
        FROM   financials
        WHERE  vintage = ?
          AND  year BETWEEN ? AND ?
          AND  life_stage IN ('Decline', 'Decay')
          AND  leverage      IS NOT NULL
          AND  profitability IS NOT NULL
          AND  tangibility   IS NOT NULL
    """
    df = pd.read_sql_query(query, con, params=(VINTAGE, YEAR_MIN, YEAR_MAX))
    con.close()
    return df


# ── OLS helper ────────────────────────────────────────────────────────────────
def ols_line(x: np.ndarray, y: np.ndarray, x_range: list) -> tuple:
    """Return (slope, intercept, x_line, y_line) for plotting."""
    slope, intercept = np.polyfit(x, y, 1)
    x_line = np.array(x_range)
    y_line = slope * x_line + intercept
    return slope, intercept, x_line, y_line


# ── Build figure ──────────────────────────────────────────────────────────────
def build_fig83(df: pd.DataFrame) -> go.Figure:
    # horizontal_spacing=0.22 → left domain [0,0.39], right domain [0.61,1.0]
    # gap centre is at paper x=0.50 — used for the separator line below
    fig = make_subplots(
        rows=1, cols=2,
        shared_yaxes=True,
        horizontal_spacing=0.22,
        subplot_titles=[
            "LEVERAGE vs PROFITABILITY",
            "LEVERAGE vs TANGIBILITY",
        ],
    )

    subplot_specs = [
        ("profitability", X_PROF),
        ("tangibility",   X_TANG),
    ]

    # Decline = circle,  Decay = diamond  (distinct when overlapping)
    MARKER_SYMBOL = {"Decline": "circle", "Decay": "diamond"}

    print("\n-- OLS fit summary --")
    print(f"{'Stage':<10} {'Metric':<14} {'Slope':>10} {'Intercept':>10}")
    print("-" * 46)

    for col_idx, (x_col, x_range) in enumerate(subplot_specs, 1):
        for stage in STAGES:
            cfg   = STAGE_CFG[stage]
            color = cfg["color"]
            label = cfg["label"]
            sub = df[df["life_stage"] == stage][[x_col, "leverage"]].apply(pd.to_numeric, errors="coerce").dropna()
            x = sub[x_col].values
            y = sub["leverage"].values

            # Scatter — thin dark outline makes individual dots readable
            fig.add_trace(go.Scatter(
                x=x, y=y,
                mode="markers",
                name=label,
                marker=dict(
                    size=7,
                    color=color,
                    opacity=0.65,
                    symbol=MARKER_SYMBOL[stage],
                    line=dict(width=0.8, color="rgba(0,0,0,0.25)"),
                ),
                showlegend=(col_idx == 1),
                hovertemplate=(
                    f"<b>{stage}</b><br>"
                    f"{x_col}: %{{x:.3f}}<br>"
                    f"Leverage: %{{y:.1f}}%<extra></extra>"
                ),
            ), row=1, col=col_idx)

            # OLS regression line — dashed so it reads as a trend, not a data series
            if len(x) >= 2:
                slope, intercept, x_line, y_line = ols_line(x, y, x_range)
                fig.add_trace(go.Scatter(
                    x=x_line, y=y_line,
                    mode="lines",
                    line=dict(color=color, width=2.5, dash="dash"),
                    showlegend=False,
                ), row=1, col=col_idx)
                print(f"{stage:<10} {x_col:<14} {slope:>+10.3f} {intercept:>+10.3f}")

    # ── Axis styling — boxed subplot borders via mirror=True ──────────────────
    _axis_common = dict(
        tickfont=dict(size=TICK_FONT_SIZE),
        showgrid=True, gridcolor="#E5E7EB", gridwidth=1,
        showline=True, linewidth=1.5, linecolor="#9CA3AF", mirror=True,
        ticks="outside", ticklen=4,
    )

    # Y — left subplot carries the title; right is shared (no duplicate title)
    fig.update_yaxes(
        **_axis_common,
        range=Y_RANGE,
        zeroline=False,
        ticksuffix="%",
        dtick=25,
        title_text="<b>Leverage %</b>",
        title_font=dict(size=LABEL_FONT_SIZE),
        row=1, col=1,
    )
    fig.update_yaxes(
        **_axis_common,
        range=Y_RANGE,
        zeroline=False,
        ticksuffix="%",
        dtick=25,
        row=1, col=2,
    )

    # Left X: profitability — vertical zero-line marks the axis origin clearly
    fig.update_xaxes(
        **_axis_common,
        range=X_PROF,
        dtick=0.2,
        title_text="<b>Profitability  r</b>",
        title_font=dict(size=LABEL_FONT_SIZE),
        zeroline=True, zerolinecolor="#6B7280", zerolinewidth=1.5,
        row=1, col=1,
    )

    # Right X: tangibility
    fig.update_xaxes(
        **_axis_common,
        range=X_TANG,
        zeroline=False,
        dtick=0.1,
        title_text="<b>Tangibility</b>",
        title_font=dict(size=LABEL_FONT_SIZE),
        row=1, col=2,
    )

    # ── Global layout ─────────────────────────────────────────────────────────
    fig.update_layout(
        title=dict(
            text=(
                "<b>Figure 8.3 — Relation of Leverage with Profitability "
                "and Tangibility</b><br>"
                "<sup>Decline and Decay Stages  |  Thesis Panel 2001–2024  "
                "|  n=329 firm-year observations</sup>"
            ),
            font=dict(size=12, color=TEXT_COLOR, family="Inter, sans-serif"),
            x=0.5, xanchor="center",
        ),
        height=700,
        paper_bgcolor="white",
        plot_bgcolor="#F8FAFC",      # light blue-gray inside each subplot box
        font=dict(family="Inter, sans-serif", size=TICK_FONT_SIZE, color=TEXT_COLOR),
        legend=dict(
            x=0.96, y=0.97,
            xanchor="right", yanchor="top",
            bgcolor="rgba(255,255,255,0.92)",
            bordercolor="#9CA3AF",
            borderwidth=1.5,
            font=dict(size=10),
            itemsizing="constant",
            tracegroupgap=4,
        ),
        margin=dict(l=80, r=40, t=115, b=70),
    )

    # ── Subplot titles — nudge up and bold ────────────────────────────────────
    for ann in fig.layout.annotations:
        ann.font = dict(size=10, color=TEXT_COLOR, family="Inter, sans-serif")
        ann.y    = ann.y + 0.015

    # ── Vertical separator between the two subplots ───────────────────────────
    # With h_spacing=0.22 and 2 cols the domains are [0,0.39] and [0.61,1.0].
    # The gap midpoint in paper coords is 0.50.
    # y0/y1 are in paper coords: approximately the plot area, clear of subplot titles.
    fig.add_shape(
        type="line", xref="paper", yref="paper",
        x0=0.50, x1=0.50, y0=0.06, y1=0.85,
        line=dict(color="#CBD5E1", width=2.5),
        layer="below",
    )

    # ── Stage labels inside each subplot (top-left annotation) ───────────────
    for col_idx, x_ref, y_ref in [(1, "x", "y"), (2, "x2", "y")]:
        x_pos = X_PROF[0] + 0.03 if col_idx == 1 else X_TANG[0] + 0.02
        fig.add_annotation(
            x=x_pos, y=142,
            xref=x_ref, yref=y_ref,
            text="<b>Decline</b> ● circle  |  <b>Decay</b> ◆ diamond",
            showarrow=False,
            font=dict(size=8, color="#6B7280"),
            align="left",
            bgcolor="rgba(255,255,255,0.85)",
            bordercolor="#E5E7EB",
            borderwidth=1,
        )

    # ── Magenta border ────────────────────────────────────────────────────────
    fig.add_shape(
        type="rect", xref="paper", yref="paper",
        x0=0, x1=1, y0=0, y1=1,
        line=dict(color=BORDER_COLOR, width=2),
        fillcolor="rgba(0,0,0,0)",
        layer="above",
    )

    return fig


# ── Main ──────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    os.makedirs(OUT_DIR, exist_ok=True)

    print(f"Loading thesis panel ({VINTAGE}, {YEAR_MIN}-{YEAR_MAX}, Decline+Decay)...")
    df = load_df()
    counts = df["life_stage"].value_counts()
    for stage in STAGES:
        print(f"  {stage}: {counts.get(stage, 0)} rows")

    print("\nBuilding Figure 8.3...")
    fig = build_fig83(df)

    out = os.path.join(OUT_DIR, "thesis_fig83.html")
    fig.write_html(out, include_plotlyjs="cdn")
    print(f"\nSaved: {out}")

    import subprocess
    subprocess.Popen(["start", "", out], shell=True)
    print("Opening in browser...")
