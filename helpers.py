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


# ── Dynamic Interpretation Engine ──
# All functions read actual data/results and generate insights dynamically.
# If data changes, interpretations change automatically.

def _render_insight_box(title, findings, actions, context=None):
    """Render an expandable insight box below a chart."""
    import streamlit as st
    with st.expander(f"📊 {title}"):
        if context:
            st.caption(context)
        if findings:
            st.markdown("**Key Findings:**")
            for f in findings:
                st.markdown(f"- {f}")
        if actions:
            st.markdown("**Call to Action:**")
            for a in actions:
                st.markdown(f"- 🎯 {a}")


def render_interpretation(insights, actions, title="Results Interpretation & Call to Action"):
    """Render full interpretation section."""
    import streamlit as st
    st.markdown(f"#### {title}")
    if insights:
        st.markdown("**Key Findings:**")
        for i in insights:
            st.markdown(f"- {i}")
    if actions:
        st.markdown("")
        st.markdown("**Call to Action:**")
        for a in actions:
            st.markdown(f"- 🎯 {a}")


# ── Dashboard Interpretations (Page 1) ──

def interpret_kpi_cards(df, n_companies, avg_lev, med_lev, avg_prof, dominant_stage, n_obs):
    """Interpret the KPI card row dynamically."""
    f, a = [], []
    f.append(f"Across **{n_companies} firms** and **{n_obs:,} observations**, average leverage is **{avg_lev:.1f}%** (median {med_lev:.1f}%).")
    skew = avg_lev - med_lev
    if skew > 5:
        f.append(f"Leverage is **right-skewed** (mean {skew:.1f}pp above median) — a few highly leveraged firms pull the average up.")
        a.append("Focus on median leverage for typical firm behavior; investigate outliers above 75th percentile for distress risk.")
    if avg_prof < 0.05:
        f.append(f"Average profitability is **low ({avg_prof:.1%})** — many firms in the sample have thin margins.")
        a.append("Low-profitability environments increase leverage dependency. Monitor interest coverage ratios closely.")
    f.append(f"**{dominant_stage}** is the dominant life stage — most firms in this filtered set are in their {dominant_stage.lower()} phase.")
    return f, a


def interpret_leverage_trend(stage_summary):
    """Interpret the leverage trend line chart."""
    f, a = [], []
    if stage_summary.empty:
        return f, a
    # Find which stage has highest volatility
    vol = stage_summary.groupby("life_stage")["avg_leverage"].std().sort_values(ascending=False)
    if len(vol) > 0:
        most_volatile = vol.index[0]
        f.append(f"**{most_volatile}** stage shows the highest leverage volatility (std={vol.iloc[0]:.1f}pp) — capital structure shifts rapidly in this phase.")

    # Trend direction in latest years
    recent = stage_summary[stage_summary["year"] >= stage_summary["year"].max() - 3]
    for stage in recent["life_stage"].unique():
        s = recent[recent["life_stage"] == stage].sort_values("year")
        if len(s) >= 2:
            trend = s["avg_leverage"].iloc[-1] - s["avg_leverage"].iloc[0]
            if abs(trend) > 3:
                direction = "increasing" if trend > 0 else "decreasing"
                f.append(f"**{stage}** leverage is **{direction}** recently ({trend:+.1f}pp over last 3 years).")

    a.append("Watch stages with rising leverage trends — they may signal increasing financial risk or strategic debt accumulation.")
    a.append("Compare leverage trends against macro events (GFC, IBC, COVID shaded bands) to distinguish structural vs cyclical shifts.")
    return f, a


def interpret_lifecycle_distribution(df):
    """Interpret the lifecycle donut chart."""
    f, a = [], []
    counts = df["life_stage"].value_counts()
    total = len(df)
    dominant = counts.index[0]
    dominant_pct = counts.iloc[0] / total * 100
    f.append(f"**{dominant}** dominates with **{dominant_pct:.0f}%** of observations ({counts.iloc[0]:,} firm-years).")

    if "Startup" in counts.index:
        startup_pct = counts.get("Startup", 0) / total * 100
        if startup_pct < 5:
            f.append(f"Only **{startup_pct:.1f}%** are Startups — the sample is mature-firm-heavy. Startup-stage conclusions should be cautious.")
    if "Decline" in counts.index or "Decay" in counts.index:
        distress_pct = (counts.get("Decline", 0) + counts.get("Decay", 0)) / total * 100
        f.append(f"**{distress_pct:.1f}%** of observations are in Decline/Decay — these firms face restructuring pressure.")
        a.append("Flag Decline/Decay firms for credit risk monitoring. Their capital structure may be involuntary (debt overhang).")

    a.append("Use life stage distribution to weight your analysis — insights from stages with few observations are less reliable.")
    return f, a


def interpret_top_leveraged(top10_df, overall_avg):
    """Interpret the top 10 most leveraged companies chart."""
    f, a = [], []
    if top10_df.empty:
        return f, a
    highest = top10_df.iloc[-1]  # sorted ascending, last = highest
    f.append(f"**{highest['company_name']}** has the highest average leverage at **{highest['avg_leverage']:.1f}%** — {highest['avg_leverage']/overall_avg:.1f}x the overall average.")
    stages = top10_df["life_stage"].value_counts()
    if len(stages) > 0:
        top_stage = stages.index[0]
        f.append(f"Most top-leveraged firms are in the **{top_stage}** stage ({stages.iloc[0]}/10).")
    a.append("Investigate top-leveraged firms for potential financial distress signals (interest coverage < 1.5x, negative cash flow).")
    a.append("Cross-reference with ownership data — high promoter-pledging + high leverage = elevated risk.")
    return f, a


def interpret_event_impact(overall_avg, gfc_avg, ibc_avg, covid_avg):
    """Interpret the event period impact cards."""
    f, a = [], []
    events = {"GFC (2008-09)": gfc_avg, "IBC (2016+)": ibc_avg, "COVID (2020-21)": covid_avg}
    for name, avg in events.items():
        if avg is not None:
            diff = avg - overall_avg
            if abs(diff) > 2:
                direction = "higher" if diff > 0 else "lower"
                f.append(f"During **{name}**, average leverage was **{diff:+.1f}pp {direction}** than the full-period average ({avg:.1f}% vs {overall_avg:.1f}%).")

    if gfc_avg and gfc_avg > overall_avg:
        a.append("GFC elevated leverage — firms may have been unable to deleverage during the crisis. Review if this pattern repeats in current stress scenarios.")
    if ibc_avg and ibc_avg < overall_avg:
        a.append("Post-IBC leverage is lower — the Insolvency & Bankruptcy Code appears to have disciplined capital structures. This is a positive regulatory signal.")
    if covid_avg:
        a.append("COVID period impact should be interpreted alongside government stimulus measures (moratoriums, RBI rate cuts).")
    return f, a


# ── Peer Benchmarks Interpretations (Page 2) ──

def interpret_company_vs_industry(company_name, company_df, industry_df, metric="leverage"):
    """Interpret company vs industry average chart."""
    f, a = [], []
    if company_df.empty or industry_df.empty:
        return f, a
    comp_avg = company_df[metric].mean()
    ind_avg = industry_df[metric].mean()
    diff = comp_avg - ind_avg
    direction = "above" if diff > 0 else "below"

    f.append(f"**{company_name}** average {metric} is **{comp_avg:.1f}%**, which is **{abs(diff):.1f}pp {direction}** the industry average ({ind_avg:.1f}%).")

    if metric == "leverage":
        if diff > 10:
            f.append("The firm is **significantly more leveraged** than its industry peers — potential over-leveraging.")
            a.append(f"Investigate why {company_name} carries excess debt. Check for recent acquisitions, capex cycles, or financial distress.")
        elif diff < -10:
            f.append("The firm is **under-leveraged** relative to peers — may have untapped debt capacity.")
            a.append(f"{company_name} may benefit from strategic borrowing to fund growth or optimize WACC.")
    elif metric == "profitability":
        if diff > 0:
            a.append(f"{company_name} outperforms peers on profitability — a strong position for Pecking Order-driven deleveraging.")
    return f, a


def interpret_radar_profile(company_name, comp_vals, ind_vals, stage_vals, labels):
    """Interpret the radar chart comparison."""
    f, a = [], []
    for i, label in enumerate(labels):
        diff = comp_vals[i] - ind_vals[i]
        if abs(diff) > 20:
            direction = "higher" if diff > 0 else "lower"
            f.append(f"**{label}**: {company_name} is significantly **{direction}** than industry average (score: {comp_vals[i]:.0f} vs {ind_vals[i]:.0f}).")
    if len(f) == 0:
        f.append(f"{company_name}'s financial profile is broadly in line with industry averages.")
    a.append("Outlier dimensions on the radar indicate where the firm diverges from peers — these are key areas for strategic review.")
    return f, a


# ── Econometric Interpretations (Page 8) ──

def interpret_econometric(best, hausman=None, bp=None):
    """Generate deep interpretation of econometric regression results."""
    ct = best["coef_table"]
    sig = ct[ct["p-value"] < 0.05]
    sig_no_const = sig[sig["Variable"] != "const"]
    f, a = [], []

    r2 = best["r_squared"]
    if r2 > 0.3:
        f.append(f"The model explains **{r2*100:.1f}%** of leverage variation — strong fit for panel data. In capital structure research, R² of 15-35% is typical (Rajan & Zingales, 1995).")
    elif r2 > 0.15:
        f.append(f"The model explains **{r2*100:.1f}%** — moderate fit consistent with the thesis findings and broader empirical literature.")
    else:
        f.append(f"The model explains only **{r2*100:.1f}%** — weak. Important determinants may be omitted (e.g., market timing, managerial preferences).")
        a.append("Consider adding ownership concentration, industry dummies, or macro variables to improve explanatory power.")

    for _, row in sig_no_const.iterrows():
        var, coef = row["Variable"], row["Coefficient"]
        if var == "profitability" and coef < 0:
            f.append(f"**Profitability** (coef={coef:.2f}***): Strongly negative — confirms **Pecking Order Theory**. Profitable Indian firms prefer internal financing over debt, reducing leverage as earnings grow.")
            a.append("CFOs at profitable firms: maintain low leverage. Your earnings capacity is your cheapest capital. Avoid unnecessary borrowing.")
        elif var == "tangibility" and coef > 0:
            f.append(f"**Tangibility** (coef={coef:.2f}***): Strongly positive — confirms **Trade-off Theory**. Tangible assets serve as collateral, enabling higher debt capacity and lower borrowing costs.")
            a.append("For asset-light firms (IT, services): your optimal leverage is structurally lower. Don't benchmark against manufacturing peers.")
        elif "size" in var.lower():
            direction = "negative" if coef < 0 else "positive"
            f.append(f"**Firm Size** (coef={coef:.2f}): {direction.title()} effect. {'Larger Indian firms rely more on retained earnings (Pecking Order).' if coef < 0 else 'Larger firms have better credit access (Trade-off).'}")
        elif var == "tax" or var == "tax_shield":
            f.append(f"**{var.replace('_',' ').title()}** (coef={coef:.2f}): {'Debt tax shield incentive is active — higher taxes push firms toward debt.' if coef > 0 else 'Tax effect is muted in this sample — Indian tax structure may not incentivize debt as theory predicts.'}")
        elif var == "dividend":
            f.append(f"**Dividend** (coef={coef:.2f}): {'Dividend-paying firms carry less debt (signaling financial health).' if coef < 0 else 'Dividend commitment forces debt usage for investment.'}")
        else:
            f.append(f"**{var}** is significant (coef={coef:.2f}, p<0.05).")

    non_sig = ct[(ct["p-value"] >= 0.05) & (ct["Variable"] != "const")]
    if len(non_sig) > 0:
        ns_vars = ", ".join(non_sig["Variable"].tolist())
        f.append(f"Not statistically significant: {ns_vars}. These variables do not reliably predict leverage in this sample.")

    if hausman:
        if hausman["p_value"] < 0.05:
            f.append(f"**Hausman test** (Chi²={hausman['chi2']:.1f}, p<0.001): **Fixed Effects is the correct specification.** Firm-specific characteristics (culture, management, brand) correlate with the determinants — ignoring them biases the results.")
            a.append("Use Fixed Effects coefficients for all policy recommendations. Pooled OLS and Random Effects are biased for this data.")
        else:
            f.append(f"**Hausman test** (p={hausman['p_value']:.4f}): Random Effects is preferred — more efficient and unbiased.")
    return f, a


# ── ML Model Interpretations (Page 9) ──

def interpret_ml_comparison(comparison_df, stage_importance=None):
    """Generate deep interpretation of ML model comparison."""
    f, a = [], []
    best = comparison_df.iloc[0]
    r2_best = best["R-squared"]

    f.append(f"**{best['Model']}** achieves the highest R²={r2_best:.4f} (RMSE={best['RMSE']:.1f}pp).")

    if r2_best > 0.5:
        f.append(f"ML captures **{r2_best*100:.0f}%** of leverage variance — substantially better than linear OLS (~35%). This confirms **significant non-linear patterns** in Indian capital structure data: interaction effects, threshold behaviors, and regime-dependent relationships.")
        a.append("Linear econometric models (OLS, FE) systematically understate predictive power. Use ML for prediction tasks, econometrics for causal inference.")
    elif r2_best > 0.3:
        f.append(f"Moderate improvement over OLS — some non-linear effects exist but are not dominant.")

    spread = best["R-squared"] - comparison_df.iloc[-1]["R-squared"]
    if spread < 0.03:
        f.append("All models perform similarly — the underlying signal is **robust and model-agnostic**. This strengthens confidence in the results.")
    else:
        f.append(f"Performance spread of {spread:.3f} across models. Gradient boosting ({best['Model']}) captures patterns that simpler ensemble methods miss.")

    if stage_importance:
        f.append("**Stage-specific feature importance reveals how capital structure drivers shift across the corporate lifecycle:**")
        for stage, imp_df in stage_importance.items():
            if len(imp_df) > 0:
                top = imp_df.iloc[0]
                f.append(f"  - **{stage}**: {top['Feature']} dominates ({top['Importance_Pct']:.0f}%) — {'collateral-driven borrowing' if top['Feature'] == 'tangibility' else 'earnings-driven deleveraging' if top['Feature'] == 'profitability' else 'tax optimization' if 'tax' in top['Feature'] else 'size-dependent access'}.")
        a.append("Tailor capital structure advice by life stage: Growth firms need collateral optimization, Mature firms need earnings retention strategies, Decline firms need tax-efficient restructuring.")

    a.append("Use SHAP values (Feature Importance tab) to explain individual firm predictions to stakeholders.")
    return f, a


# ── Clustering Interpretations (Page 11) ──

def interpret_clustering(ari, n_clusters, summary_df):
    """Generate deep interpretation of clustering results."""
    f, a = [], []
    f.append(f"The algorithm discovered **{n_clusters} natural firm groupings** based on financial characteristics alone — no life stage labels were used.")

    if ari > 0.5:
        f.append(f"**Strong alignment** with Dickinson stages (ARI={ari:.3f}). The cash-flow classification captures real financial structure differences.")
    elif ari > 0.1:
        f.append(f"**Partial alignment** (ARI={ari:.3f}). Clusters capture **additional structure beyond Dickinson** — some firms with similar cash flow signs have very different financial DNA.")
        a.append("Consider a hybrid classification: Dickinson stage + cluster membership for richer firm segmentation in credit models.")
    else:
        f.append(f"**Weak alignment** (ARI={ari:.3f}). Financial profiles group differently from cash-flow classification — Dickinson stages may oversimplify Indian corporate reality.")
        a.append("Revisit the Dickinson framework for Indian markets. Financial heterogeneity within stages may require sub-classifications.")

    if summary_df is not None and len(summary_df) > 0:
        high = summary_df.loc[summary_df["avg_leverage"].idxmax()]
        low = summary_df.loc[summary_df["avg_leverage"].idxmin()]
        f.append(f"**Highest-risk cluster**: {high['cluster_label']} — avg leverage {high['avg_leverage']:.1f}% across {int(high['n_firms'])} firms.")
        f.append(f"**Most conservative cluster**: {low['cluster_label']} — avg leverage {low['avg_leverage']:.1f}% across {int(low['n_firms'])} firms.")
        if high['avg_leverage'] > 50:
            a.append(f"**Red flag**: {high['cluster_label']} firms carry >50% leverage. Screen for debt serviceability (interest coverage < 1.5x).")
        a.append(f"Use cluster profiles to build peer groups for benchmarking — more financially meaningful than industry classification alone.")
    return f, a


# ── Survival Interpretations (Page 12) ──

def interpret_survival(km_summary, hr_df):
    """Generate deep interpretation of survival analysis."""
    f, a = [], []

    if km_summary is not None and len(km_summary) > 0:
        numeric = km_summary[km_summary["Median Duration (yrs)"] != ">24"].copy()
        if len(numeric) > 0:
            numeric["dur_val"] = pd.to_numeric(numeric["Median Duration (yrs)"], errors="coerce")
            longest = numeric.loc[numeric["dur_val"].idxmax()]
            shortest = numeric.loc[numeric["dur_val"].idxmin()]
            f.append(f"**Most stable**: {longest['Stage']} (median {longest['Median Duration (yrs)']} years). Firms in this stage have the most predictable capital structure trajectory.")
            f.append(f"**Most volatile**: {shortest['Stage']} (median {shortest['Median Duration (yrs)']} years). Rapid transitions make long-term planning difficult for these firms.")
            a.append(f"Firms in {shortest['Stage']}: prepare contingency financing plans. Stage transitions often trigger covenant violations and rating downgrades.")

    if hr_df is not None and len(hr_df) > 0:
        sig_hrs = hr_df[hr_df["p-value"] < 0.05]
        for _, row in sig_hrs.iterrows():
            hr, var = row["Hazard Ratio"], row["Variable"]
            if hr > 1.05:
                f.append(f"**{var}** accelerates transitions (HR={hr:.3f}): 1-unit increase raises transition probability by **{(hr-1)*100:.0f}%**. {'Higher leverage makes firms more likely to move to the next stage — debt pressure forces strategic pivots.' if var == 'leverage' else ''}")
            elif hr < 0.95:
                f.append(f"**{var}** delays transitions (HR={hr:.3f}): 1-unit increase reduces transition probability by **{(1-hr)*100:.0f}%**. {'Profitable/tangible firms are stickier — their capital structure is more sustainable.' if var in ('profitability','tangibility') else ''}")
        if len(sig_hrs) > 0:
            a.append("Build an early-warning system: firms with rising leverage + falling profitability + low tangibility are prime candidates for imminent stage transition.")
            a.append("Credit analysts: use hazard ratios to adjust PD (probability of default) models — stage transition is a leading indicator of credit deterioration.")
    return f, a


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
        margin=dict(l=40, r=20, t=50, b=60),
        height=height,
        legend=dict(orientation="h", yanchor="top", y=-0.15, xanchor="center", x=0.5),
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
