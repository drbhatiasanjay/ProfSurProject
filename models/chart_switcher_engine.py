"""
Chart Switcher Engine for LifeCycle Leverage.

Provides:
1. Canonical Variable Labeling with formal econometric titles, symbols, formulas, and units.
2. Data-to-Graph Compatibility Matrix: restricts chart alternatives exclusively to mathematically sound representations.
3. Plotly Figure Builders for all compatible alternative charts (Forest Plot, Fitted vs Actual, Residuals, Beta Rank, etc.).
"""

from typing import Dict, List, Any, Optional
import numpy as np
import plotly.graph_objects as go
from helpers import plotly_layout

# ── 1. Canonical Variable Labels Dictionary ───────────────────────────────────
CANONICAL_VARIABLE_LABELS: Dict[str, Dict[str, str]] = {
    "leverage": {
        "symbol": "LEV",
        "short_name": "Leverage (%)",
        "full_name": "Debt-to-Equity Leverage",
        "formula": "Total Debt / Total Equity",
        "unit": "%",
        "display_label": "Debt / Equity Leverage (%)",
    },
    "profitability": {
        "symbol": "ROA",
        "short_name": "ROA (%)",
        "full_name": "Return on Assets (Operating Profitability)",
        "formula": "Operating EBITDA / Total Assets",
        "unit": "%",
        "display_label": "Return on Assets (ROA, %)",
    },
    "tangibility": {
        "symbol": "TANG",
        "short_name": "Tangibility (%)",
        "full_name": "Asset Tangibility (Collateral Capacity)",
        "formula": "Net Plant, Property & Equipment / Total Assets",
        "unit": "%",
        "display_label": "Asset Tangibility (PPE / Assets, %)",
    },
    "log_size": {
        "symbol": "SIZE",
        "short_name": "Firm Size",
        "full_name": "Firm Asset Scale",
        "formula": "ln(Total Assets in ₹ Cr)",
        "unit": "ln(Assets)",
        "display_label": "Firm Scale (ln Total Assets)",
    },
    "ibc_2016": {
        "symbol": "IBC",
        "short_name": "IBC Post-2016",
        "full_name": "Insolvency and Bankruptcy Code Regime",
        "formula": "Dummy: 1 if Year >= 2016, 0 otherwise",
        "unit": "Binary Indicator",
        "display_label": "IBC 2016 Reform Dummy [0, 1]",
    },
    "gfc": {
        "symbol": "GFC",
        "short_name": "GFC 2008-09",
        "full_name": "Global Financial Crisis Shock",
        "formula": "Dummy: 1 if Year in (2008, 2009), 0 otherwise",
        "unit": "Binary Indicator",
        "display_label": "GFC 2008 Crisis Dummy [0, 1]",
    },
    "covid_dummy": {
        "symbol": "COVID",
        "short_name": "COVID 2020-21",
        "full_name": "COVID-19 Pandemic Shock",
        "formula": "Dummy: 1 if Year in (2020, 2021), 0 otherwise",
        "unit": "Binary Indicator",
        "display_label": "COVID-19 Shock Dummy [0, 1]",
    },
    "tax": {
        "symbol": "TAX",
        "short_name": "Tax Rate (%)",
        "full_name": "Effective Corporate Tax Rate",
        "formula": "Tax Expense / Pre-Tax Income",
        "unit": "%",
        "display_label": "Effective Tax Rate (%)",
    },
    "tax_shield": {
        "symbol": "NDTS",
        "short_name": "Non-Debt Tax Shield",
        "full_name": "Non-Debt Tax Shield",
        "formula": "Depreciation / Total Assets",
        "unit": "%",
        "display_label": "Non-Debt Tax Shield (%)",
    },
    "dividend": {
        "symbol": "DIV",
        "short_name": "Dividend Payout",
        "full_name": "Dividend Payout Ratio",
        "formula": "Dividends Paid / Net Income",
        "unit": "%",
        "display_label": "Dividend Payout Ratio (%)",
    },
    "icr": {
        "symbol": "ICR",
        "short_name": "ICR (x)",
        "full_name": "Interest Coverage Ratio",
        "formula": "EBITDA / Total Interest Expense",
        "unit": "x",
        "display_label": "Interest Coverage Ratio (x)",
    },
    "life_stage": {
        "symbol": "STAGE",
        "short_name": "Life Stage",
        "full_name": "Dickinson (2011) Life-Cycle Stage",
        "formula": "Cash Flow Sign Signature (CFO, CFI, CFF)",
        "unit": "Categorical (8 Stages)",
        "display_label": "Dickinson Life-Cycle Stage",
    },
    "industry_group": {
        "symbol": "IND",
        "short_name": "Industry Sector",
        "full_name": "Manufacturing Industry Classification",
        "formula": "Sector Group",
        "unit": "Categorical",
        "display_label": "Manufacturing Industry Sector",
    },
}

def get_canonical_label(var_key: str) -> str:
    """Resolve raw variable name or alias to full canonical label."""
    clean_k = var_key.lower().replace("c.", "").split("#")[0].strip()
    # Map common aliases (prof -> profitability, tang -> tangibility, size -> log_size)
    alias_map = {
        "prof": "profitability",
        "profit": "profitability",
        "roa": "profitability",
        "roe": "profitability",
        "tang": "tangibility",
        "tangible": "tangibility",
        "ppe": "tangibility",
        "size": "log_size",
        "logsize": "log_size",
        "lnsize": "log_size",
        "assets": "log_size",
        "lev": "leverage",
        "debtratio": "leverage",
        "td_ta": "leverage",
        "stage": "life_stage",
    }
    resolved_key = alias_map.get(clean_k, clean_k)
    entry = CANONICAL_VARIABLE_LABELS.get(resolved_key)
    if entry:
        return entry["display_label"]
    return var_key.replace("_", " ").title()

# ── 2. Data-to-Graph Compatibility Matrix ─────────────────────────────────────
def get_compatible_chart_types(chart_category: str, payload: Optional[Dict[str, Any]] = None) -> List[Dict[str, str]]:
    """
    Deterministically returns only the chart types that are mathematically valid
    for the specific data structure. Incompatible charts (e.g. donut for regression)
    are strictly excluded.
    """
    cat = (chart_category or "").lower().strip()

    if cat in ("regression", "panel_regression", "ols", "fe", "re", "coefplot"):
        options = [
            {"id": "forest_plot", "label": "🌲 Forest Plot (Coefplot 95% CI)", "description": "Point estimates with cluster-robust 95% confidence intervals against zero benchmark."},
            {"id": "beta_rank_bars", "label": "📊 Standardized Beta Ranking", "description": "Horizontal bar chart of determinants ranked by absolute t-statistic magnitude."},
        ]
        # Include Fitted vs Actual and Residuals only if fitted/actual data is present
        if payload and (payload.get("y_fitted") is not None or payload.get("fitted_values") is not None):
            options.append({"id": "fitted_vs_actual", "label": "🎯 Fitted vs. Actual Scatter", "description": "Actual dependent variable vs fitted values with 45-degree parity line."})
            options.append({"id": "residuals_plot", "label": "📉 Residuals vs. Fitted Dispersion", "description": "Evaluation of heteroskedasticity and residual symmetry around zero."})
        return options

    elif cat in ("time_series", "trend", "longitudinal"):
        return [
            {"id": "connected_lines", "label": "📈 Connected Time-Series (with Crisis Bands)", "description": "Annual longitudinal trajectory with shaded bands for GFC (2008), IBC (2016), and COVID (2020)."},
            {"id": "annual_bars", "label": "📊 Grouped Annual Bars", "description": "Direct year-by-year discrete comparison across selected financial variables."},
            {"id": "area_trend", "label": "🌊 Cumulative Volume Area", "description": "Filled area chart displaying cumulative multi-variable trajectory over time."},
        ]

    elif cat in ("categorical", "cohort", "life_stage", "industry"):
        options = [
            {"id": "grouped_bars", "label": "📊 Grouped Bar Comparison", "description": "Side-by-side metric comparison across stages or industry groups."},
            {"id": "quantile_box", "label": "📦 Quantile Boxplot Spread", "description": "Median, interquartile range (IQR), and outlier dispersion across categories."},
            {"id": "rank_horizontal", "label": "🏆 Horizontal Ranking Bars", "description": "Ranked ascending or descending bars highlighting leaders vs laggards."},
        ]
        # Allow Donut chart ONLY if data represents mutually exclusive proportions/shares
        if payload and payload.get("is_share_composition"):
            options.append({"id": "composition_donut", "label": "🍩 Composition Share (Donut)", "description": "Relative percentage distribution of sample observations."})
        return options

    elif cat in ("distribution", "histogram", "summary"):
        return [
            {"id": "histogram_density", "label": "📊 Histogram with Density Overlay", "description": "Binned empirical frequency distribution with continuous density smoothing."},
            {"id": "quantile_box", "label": "📦 Quantile Dispersion Boxplot", "description": "Five-number summary (Min, P25, Median, P75, Max) highlighting skewness."},
            {"id": "cdf_curve", "label": "📈 Cumulative Distribution (CDF)", "description": "Cumulative percentile curve indicating percentile cut-offs."},
        ]

    elif cat in ("correlation", "pwcorr"):
        return [
            {"id": "corr_heatmap", "label": "🔥 Correlation Heatmap Matrix", "description": "Color-coded Pearson correlation coefficients with statistical significance stars."},
            {"id": "rank_horizontal", "label": "📊 Ranked Correlation Bars", "description": "Bar chart of pairwise correlations with dependent variable sorted by magnitude."},
        ]

    # Default fallback
    return [
        {"id": "grouped_bars", "label": "📊 Grouped Bar Chart", "description": "Default bar comparison."},
        {"id": "connected_lines", "label": "📈 Line Trend Plot", "description": "Default line trend."},
    ]

# ── 3. Plotly Figure Builders with Rigorous Academic Labelling ─────────────────
def build_forest_plot(
    coef_data: Dict[str, Dict[str, float]],
    depvar: str = "leverage",
    model_type: str = "Fixed-Effects",
    n_obs: int = 8673,
    n_groups: int = 401,
    r2: float = 0.0339,
    theme: str = "dark"
) -> go.Figure:
    """Build a publication-grade Stata-style Forest Plot (coefplot) with 95% CIs."""
    dep_label = get_canonical_label(depvar)
    vars_list = [v for v in coef_data.keys() if v != "_cons"]
    if not vars_list:
        vars_list = list(coef_data.keys())

    display_names = [get_canonical_label(v) for v in vars_list]
    coefs = [coef_data[v].get("coef", 0.0) for v in vars_list]
    ci_lows = [coef_data[v].get("ci_low", coef - 1.96 * coef_data[v].get("se", 1.0)) for v, coef in zip(vars_list, coefs)]
    ci_highs = [coef_data[v].get("ci_high", coef + 1.96 * coef_data[v].get("se", 1.0)) for v, coef in zip(vars_list, coefs)]
    err_plus = [high - c for high, c in zip(ci_highs, coefs)]
    err_minus = [c - low for low, c in zip(ci_lows, coefs)]

    # Dynamic point colors: Emerald if positive, Rose if negative
    colors = ["#10B981" if c >= 0 else "#F43F5E" for c in coefs]

    fig = go.Figure()

    # Zero Impact Reference Line
    fig.add_vline(
        x=0, line_dash="dash", line_color="#94A3B8", line_width=1.5,
        annotation_text="Zero Impact: β = 0", annotation_position="top left",
        annotation_font=dict(size=10, color="#94A3B8")
    )

    fig.add_trace(go.Scatter(
        x=coefs,
        y=display_names,
        mode="markers",
        marker=dict(size=9, color=colors, line=dict(color="#FFFFFF", width=1)),
        error_x=dict(
            type="data",
            symmetric=False,
            array=err_plus,
            arrayminus=err_minus,
            color="#38BDF8",
            thickness=2,
            width=6,
        ),
        name="Estimated Parameter (β)",
        hovertemplate="<b>%{y}</b><br>Coefficient: %{x:.4f}<br>95% CI: [%{customdata[0]:.4f}, %{customdata[1]:.4f}]<extra></extra>",
        customdata=list(zip(ci_lows, ci_highs)),
    ))

    fig.update_layout(
        title=dict(
            text=f"<b>{model_type} Regression Determinants</b><br><span style='font-size:12px; color:#94A3B8;'>Dependent Variable: {dep_label} | Sample: N = {n_obs:,} across {n_groups} firms</span>",
            x=0.02, y=0.96
        ),
        xaxis=dict(
            title=dict(
                text=f"Estimated Coefficient (Δ {dep_label} per unit change)",
                standoff=14,
            ),
            showgrid=True,
            gridcolor="rgba(148, 163, 184, 0.15)",
            zeroline=False,
        ),
        yaxis=dict(
            title="Econometric Determinant",
            showgrid=True,
            gridcolor="rgba(148, 163, 184, 0.15)",
            autorange="reversed",
        ),
        height=350,
        margin=dict(l=20, r=20, t=55, b=85),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#E2E8F0"),
        showlegend=False,
    )

    # Footnote with model diagnostics - placed cleanly below the axis title
    fig.add_annotation(
        text=f"Footnote: Within R² = {r2:.4f} · Standard errors clustered by company_code · Whiskers denote 95% Confidence Intervals",
        xref="paper", yref="paper", x=0, y=-0.36,
        yanchor="top",
        showarrow=False, font=dict(size=10, color="#64748B"), align="left"
    )

    return fig


def build_beta_rank_bars(
    coef_data: Dict[str, Dict[str, float]],
    depvar: str = "leverage",
    model_type: str = "Fixed-Effects",
    theme: str = "dark"
) -> go.Figure:
    """Build a horizontal bar chart of determinants ranked by absolute t-statistic magnitude."""
    dep_label = get_canonical_label(depvar)
    vars_list = [v for v in coef_data.keys() if v != "_cons"]
    if not vars_list:
        vars_list = list(coef_data.keys())

    # Sort by absolute t-statistic descending
    sorted_vars = sorted(vars_list, key=lambda v: abs(coef_data[v].get("t", 0.0)), reverse=True)
    labels = [get_canonical_label(v) for v in sorted_vars]
    t_stats = [coef_data[v].get("t", 0.0) for v in sorted_vars]
    coefs = [coef_data[v].get("coef", 0.0) for v in sorted_vars]
    colors = ["#10B981" if t >= 0 else "#F43F5E" for t in t_stats]

    fig = go.Figure()
    fig.add_vline(x=0, line_dash="solid", line_color="#94A3B8", line_width=1)
    fig.add_vline(x=1.96, line_dash="dash", line_color="#FBBF24", line_width=1, annotation_text="+1.96 (p<0.05)", annotation_position="top right")
    fig.add_vline(x=-1.96, line_dash="dash", line_color="#FBBF24", line_width=1, annotation_text="-1.96 (p<0.05)", annotation_position="top left")

    fig.add_trace(go.Bar(
        y=labels,
        x=t_stats,
        orientation="h",
        marker_color=colors,
        hovertemplate="<b>%{y}</b><br>t-Statistic: %{x:.2f}<br>Coefficient β: %{customdata:.4f}<extra></extra>",
        customdata=coefs,
    ))

    fig.update_layout(
        title=dict(
            text=f"<b>Determinant Significance Ranking (t-Statistics)</b><br><span style='font-size:12px; color:#94A3B8;'>Dependent Variable: {dep_label} | Ranked by Explanatory Strength</span>",
            x=0.02, y=0.96
        ),
        xaxis_title="t-Statistic (|t| > 1.96 confirms statistical significance at 5% level)",
        yaxis_title="Determinant",
        height=300,
        margin=dict(l=20, r=20, t=55, b=45),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#E2E8F0"),
        showlegend=False,
    )
    fig.update_yaxes(autorange="reversed", showgrid=True, gridcolor="rgba(148, 163, 184, 0.15)")
    fig.update_xaxes(showgrid=True, gridcolor="rgba(148, 163, 184, 0.15)")
    return fig


def build_fitted_vs_actual(
    y_actual: List[float],
    y_fitted: List[float],
    depvar: str = "leverage",
    r2: float = 0.0339,
    theme: str = "dark"
) -> go.Figure:
    """Build a fitted vs actual scatter plot with 45-degree line."""
    dep_label = get_canonical_label(depvar)
    min_v = min(min(y_actual), min(y_fitted))
    max_v = max(max(y_actual), max(y_fitted))

    fig = go.Figure()
    # 45 degree line of perfect prediction
    fig.add_trace(go.Scatter(
        x=[min_v, max_v], y=[min_v, max_v],
        mode="lines",
        line=dict(color="#94A3B8", dash="dash", width=1.5),
        name="Parity Line (y = ŷ)",
        hoverinfo="skip",
    ))

    fig.add_trace(go.Scatter(
        x=y_fitted, y=y_actual,
        mode="markers",
        marker=dict(color="#38BDF8", size=5, opacity=0.6),
        name="Firm-Year Observations",
        hovertemplate="Fitted (ŷ): %{x:.4f}<br>Actual (y): %{y:.4f}<extra></extra>",
    ))

    fig.update_layout(
        title=dict(
            text=f"<b>Fitted vs. Actual Values Diagnostic</b><br><span style='font-size:12px; color:#94A3B8;'>Model Fit Evaluation | Within R² = {r2:.4f}</span>",
            x=0.02, y=0.96
        ),
        xaxis_title=f"Fitted Values ŷ ({dep_label})",
        yaxis_title=f"Actual Values y ({dep_label})",
        height=320,
        margin=dict(l=20, r=20, t=55, b=45),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#E2E8F0"),
        showlegend=True,
    )
    fig.update_xaxes(showgrid=True, gridcolor="rgba(148, 163, 184, 0.15)")
    fig.update_yaxes(showgrid=True, gridcolor="rgba(148, 163, 184, 0.15)")
    return fig


def build_residuals_plot(
    residuals: List[float],
    y_fitted: List[float],
    depvar: str = "leverage",
    theme: str = "dark"
) -> go.Figure:
    """Build a residual vs fitted plot with zero line for heteroskedasticity check."""
    dep_label = get_canonical_label(depvar)

    fig = go.Figure()
    fig.add_hline(y=0, line_dash="solid", line_color="#EF4444", line_width=1.5, annotation_text="Zero Residual Benchmark", annotation_position="top left")

    fig.add_trace(go.Scatter(
        x=y_fitted, y=residuals,
        mode="markers",
        marker=dict(color="#818CF8", size=5, opacity=0.6),
        name="Residuals (e_it)",
        hovertemplate="Fitted (ŷ): %{x:.4f}<br>Residual (e): %{y:.4f}<extra></extra>",
    ))

    fig.update_layout(
        title=dict(
            text=f"<b>Residuals vs. Fitted Values Diagnostic</b><br><span style='font-size:12px; color:#94A3B8;'>Checking Homoskedasticity & Residual Symmetry</span>",
            x=0.02, y=0.96
        ),
        xaxis_title=f"Fitted Values ŷ ({dep_label})",
        yaxis_title=f"Idiosyncratic Residuals e_it ({dep_label})",
        height=320,
        margin=dict(l=20, r=20, t=55, b=45),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#E2E8F0"),
        showlegend=False,
    )
    fig.update_xaxes(showgrid=True, gridcolor="rgba(148, 163, 184, 0.15)")
    fig.update_yaxes(showgrid=True, gridcolor="rgba(148, 163, 184, 0.15)")
    return fig


def build_time_series_chart(
    years: List[int],
    series_dict: Dict[str, List[float]],
    title: str = "Longitudinal Time-Series Trajectory",
    theme: str = "dark"
) -> go.Figure:
    """Build a time-series plot with standardized macro crisis bands (GFC, IBC, COVID)."""
    fig = go.Figure()

    # Macro Crisis Bands
    fig.add_vrect(x0=2007.5, x1=2008.5, fillcolor="#F59E0B", opacity=0.18, line_width=0, annotation_text="GFC 2008", annotation_position="top left", annotation_font=dict(size=10, color="#F59E0B"))
    fig.add_vrect(x0=2015.5, x1=2016.5, fillcolor="#6366F1", opacity=0.18, line_width=0, annotation_text="IBC 2016", annotation_position="top left", annotation_font=dict(size=10, color="#818CF8"))
    fig.add_vrect(x0=2019.5, x1=2020.5, fillcolor="#F43F5E", opacity=0.18, line_width=0, annotation_text="COVID 2020", annotation_position="top left", annotation_font=dict(size=10, color="#F43F5E"))

    colors = ["#38BDF8", "#10B981", "#F59E0B", "#A855F7", "#EC4899"]
    for i, (var_name, vals) in enumerate(series_dict.items()):
        color = colors[i % len(colors)]
        label = get_canonical_label(var_name)
        fig.add_trace(go.Scatter(
            x=years, y=vals,
            mode="lines+markers",
            line=dict(color=color, width=2.5),
            marker=dict(size=6, color=color),
            name=label,
            hovertemplate=f"<b>{label}</b><br>Year: %{{x}}<br>Mean: %{{y:.2f}}%<extra></extra>",
        ))

    fig.update_layout(
        title=dict(text=f"<b>{title}</b><br><span style='font-size:12px; color:#94A3B8;'>Sample Horizon: 2001–2025 · Vertical Bands Mark Structural Macro Shocks</span>", x=0.02, y=0.96),
        xaxis_title="Panel Horizon (Financial Year)",
        yaxis_title="Annual Mean Value (%)",
        height=320,
        margin=dict(l=20, r=20, t=55, b=45),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#E2E8F0"),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )
    fig.update_xaxes(showgrid=True, gridcolor="rgba(148, 163, 184, 0.15)")
    fig.update_yaxes(showgrid=True, gridcolor="rgba(148, 163, 184, 0.15)")
    return fig
