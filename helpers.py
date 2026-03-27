"""
Shared utilities: winsorize, formatters, chart theme, export helpers.
"""

import io
import pandas as pd

# ── Color palette ──

PRIMARY = "#0D9488"       # teal
SECONDARY = "#6366F1"     # indigo
ACCENT = "#F97316"        # coral/orange
NEUTRAL = "#374151"       # gray-700
BG_LIGHT = "#F8FAFC"
BG_CARD = "#FFFFFF"

STAGE_COLORS = {
    "Startup":   "#F97316",
    "Growth":    "#22C55E",
    "Maturity":  "#0D9488",
    "Shakeout1": "#A78BFA",
    "Shakeout2": "#8B5CF6",
    "Shakeout3": "#7C3AED",
    "Decline":   "#EF4444",
    "Decay":     "#991B1B",
}

STAGE_ORDER = ["Startup", "Growth", "Maturity", "Shakeout1", "Shakeout2", "Shakeout3", "Decline", "Decay"]

STAGE_RANK = {
    "Startup": 1, "Growth": 2, "Maturity": 3,
    "Shakeout1": 4, "Shakeout2": 5, "Shakeout3": 6,
    "Decline": 7, "Decay": 8,
}


# ── Data helpers ──

def winsorize(series, lower=0.01, upper=0.99):
    low = series.quantile(lower)
    high = series.quantile(upper)
    return series.clip(lower=low, upper=high)


def format_pct(val):
    if val is None or pd.isna(val):
        return "N/A"
    return f"{val:.1f}%"


def format_inr(val):
    if val is None or pd.isna(val):
        return "N/A"
    if abs(val) >= 1e5:
        return f"{val/1e5:,.1f} L Cr"
    elif abs(val) >= 100:
        return f"{val:,.0f} Cr"
    return f"{val:,.1f} Cr"


def format_number(val):
    if val is None or pd.isna(val):
        return "N/A"
    return f"{val:,.0f}"


def format_pvalue(p):
    if p is None or pd.isna(p):
        return "N/A"
    if p < 0.001:
        return "<0.001"
    return f"{p:.4f}"


def significance_stars(p):
    if p is None or pd.isna(p):
        return ""
    if p < 0.001:
        return "***"
    if p < 0.01:
        return "**"
    if p < 0.05:
        return "*"
    if p < 0.1:
        return "."
    return ""


def format_coef_table(coef_df):
    """Format a coefficient DataFrame for display with significance stars."""
    display = coef_df.copy()
    if "p-value" in display.columns:
        display["Sig"] = display["p-value"].apply(significance_stars)
        display["p-value"] = display["p-value"].apply(format_pvalue)
    for col in ["Coefficient", "Std Error", "t-stat", "CI Lower", "CI Upper"]:
        if col in display.columns:
            display[col] = display[col].apply(lambda x: f"{x:.4f}" if pd.notna(x) else "")
    return display


# ── Plotly theme ──

PLOTLY_CONFIG = {
    "displayModeBar": True,
    "modeBarButtonsToRemove": ["lasso2d", "select2d"],
    "displaylogo": False,
}


def plotly_layout(title="", height=400):
    return dict(
        title=dict(text=title, font=dict(size=16, color=NEUTRAL)),
        font=dict(family="Inter, system-ui, sans-serif", size=12, color=NEUTRAL),
        plot_bgcolor=BG_LIGHT,
        paper_bgcolor=BG_CARD,
        margin=dict(l=40, r=20, t=80, b=40),
        height=height,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        modebar=dict(orientation="h", bgcolor="rgba(255,255,255,0.7)",
                     activecolor=PRIMARY, color=NEUTRAL),
        hovermode="x unified",
    )


def event_bands(fig, year_col="year"):
    """Add GFC, IBC, COVID shaded regions to a Plotly figure."""
    events = [
        {"x0": 2007.5, "x1": 2009.5, "label": "GFC", "color": "rgba(239,68,68,0.08)"},
        {"x0": 2015.5, "x1": 2020.5, "label": "IBC", "color": "rgba(99,102,241,0.08)"},
        {"x0": 2019.5, "x1": 2021.5, "label": "COVID", "color": "rgba(249,115,22,0.08)"},
    ]
    for e in events:
        fig.add_vrect(
            x0=e["x0"], x1=e["x1"],
            fillcolor=e["color"], line_width=0,
            annotation_text=e["label"],
            annotation_position="top left",
            annotation_font_size=10,
            annotation_font_color="#9CA3AF",
        )
    return fig


# ── Export helpers ──

def export_csv(df):
    return df.to_csv(index=False).encode("utf-8")


def export_excel(df):
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Data")
    return buf.getvalue()


# ── Dickinson life stage classifier ──

def classify_life_stage(ncfo, ncfi, ncff):
    """
    Dickinson (2011) cash-flow-based life stage classification.
    Signs: + = positive, - = negative
    """
    o = 1 if ncfo > 0 else (-1 if ncfo < 0 else 0)
    i = 1 if ncfi > 0 else (-1 if ncfi < 0 else 0)
    f = 1 if ncff > 0 else (-1 if ncff < 0 else 0)

    if o == -1 and i == -1 and f == 1:
        return "Startup"
    if o == 1 and i == -1 and f == 1:
        return "Growth"
    if o == 1 and i == -1 and f == -1:
        return "Maturity"
    # Shakeout patterns
    if o == -1 and i == -1 and f == -1:
        return "Shakeout1"
    if o == 1 and i == 1 and f == 1:
        return "Shakeout2"
    if o == 1 and i == 1 and f == -1:
        return "Shakeout3"
    # Decline
    if o == -1 and i == 1 and f == 1:
        return "Decline"
    if o == -1 and i == 1 and f == -1:
        return "Decay"
    return "Unclassified"
