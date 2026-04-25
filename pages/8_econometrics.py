"""
Econometrics Lab — Panel regression models with auto-suggest.
Replicates thesis methodology: OLS, FE, RE, Hausman, ANOVA.
"""

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import numpy as np
import db
from helpers import (
    format_coef_table, format_pvalue, significance_stars,
    plotly_layout, ensure_session_state, panel_label, STAGE_COLORS, STAGE_ORDER, PRIMARY, SECONDARY, ACCENT, PLOTLY_CONFIG,
    interpret_econometric, render_interpretation, _render_insight_box,
)
from models.econometric import (
    run_pooled_ols, run_fixed_effects, run_random_effects, run_robust_regression,
    run_hausman_test, run_breusch_pagan_lm, run_anova_by_stage, run_pairwise_comparison,
    run_all_and_compare,
)
from models.base import DEFAULT_X_COLS

ensure_session_state()

# Panel choice from the sidebar — regression results reflect whichever panel is active.
# (Previously pinned to thesis; now follows user selection so users can compare
# coefficients across thesis / latest / run3.)
filters = st.session_state.filters
ft = db.filters_to_tuple(filters)
_panel = st.session_state.get("panel_mode", "latest")

st.markdown("### Econometrics Lab")
st.caption(
    "Panel regression models replicating the thesis methodology. Auto-suggests the best model via diagnostic tests."
    f" · Active panel: **{panel_label(_panel)}**"
)
if _panel != "thesis":
    st.warning(
        f"Estimates use the **{panel_label(_panel)}** and will differ from the published thesis "
        "coefficients (Tables 5.10 / 5.11 / 5.12). Switch to **Thesis panel (2001–2024)** in the "
        "sidebar to reproduce thesis tables bit-for-bit.",
        icon="🔄",
    )

with st.expander("ℹ️ About these models — what do they mean?"):
    st.markdown("""
**Why Panel Econometrics for Capital Structure?**

Capital structure research studies the same firms over time — a **panel data** problem. Simple regression ignores that Tata Steel behaves differently from Infosys even with identical financials. Panel methods account for this.

**Models in this lab and what they measure:**

| Model | What it measures in capital structure context |
|-------|----------------------------------------------|
| **Pooled OLS** | "On average across all firms and years, how do profitability, tangibility, tax etc. affect leverage?" — Baseline, ignores firm identity. |
| **Fixed Effects** | "After controlling for each firm's unique DNA (brand, management, culture), which determinants still matter?" — The gold standard for causal inference in corporate finance. |
| **Random Effects** | "If firm-specific effects are random noise rather than systematic, can we get more precise estimates?" — More efficient than FE when assumptions hold. |
| **Hausman Test** | "Are firm effects correlated with the determinants? If yes → FE. If no → RE." — The referee between FE and RE. |
| **ANOVA** | "Is average leverage statistically different across Startup, Growth, Maturity, Decline stages?" — Tests the foundational claim of the thesis. |

**What intelligence this provides:**
- Coefficient signs validate/refute capital structure theories (Pecking Order, Trade-off, Agency Cost)
- Coefficient magnitudes quantify the economic impact: "A 1% increase in profitability reduces leverage by X percentage points"
- Diagnostic tests ensure you're using the right model — wrong model = wrong conclusions

**Significance stars:** \\*\\*\\* p<0.001 | \\*\\* p<0.01 | \\* p<0.05 | . p<0.1
""")

# ── Variable Selection ──
all_predictors = [
    "profitability", "tangibility", "tax", "log_size", "tax_shield", "dividend",
    "interest", "cash_holdings", "promoter_share", "non_promoters",
    "int_rate", "market_return", "index_pe",
]
predictor_labels = {
    "profitability": "Profitability", "tangibility": "Tangibility", "tax": "Tax Rate",
    "log_size": "Log Firm Size", "tax_shield": "Tax Shield", "dividend": "Dividend",
    "interest": "Interest", "cash_holdings": "Cash Holdings",
    "promoter_share": "Promoter Share", "non_promoters": "Non-Promoters",
    "int_rate": "Interest Rate (RBI)", "market_return": "Market Return (BSE)",
    "index_pe": "Market P/E Ratio",
}

col_left, col_right = st.columns([1, 3])

with col_left:
    st.markdown("#### Variables")
    selected_x = st.multiselect(
        "Determinants",
        options=all_predictors,
        default=DEFAULT_X_COLS,
        format_func=lambda x: predictor_labels.get(x, x),
    )
    if not selected_x:
        selected_x = DEFAULT_X_COLS

    model_choice = st.radio(
        "Model",
        ["Auto-Suggest", "Pooled OLS", "Fixed Effects", "Random Effects",
         "Robust (Huber M)", "ANOVA"],
        index=0,
        help=(
            "**Robust (Huber M)** — outlier-resistant OLS via iteratively-reweighted "
            "least squares (statsmodels.RLM). Down-weights extreme leverage values "
            "rather than fixing only the standard errors. Use this to test whether "
            "thesis findings hold under outlier downweighting."
        ),
    )

with col_right:
    # ── Load data ──
    with st.spinner("Loading panel data..."):
        panel_df = db.get_active_panel_data(ft)

    if panel_df.empty or len(panel_df) < 50:
        st.warning("Not enough data for regression. Adjust filters (need 50+ observations).")
        st.stop()

    n_firms = panel_df["company_code"].nunique()
    n_obs = len(panel_df)
    st.caption(f"Panel: {n_firms} firms, {n_obs:,} observations, {panel_df['year'].min()}-{panel_df['year'].max()}")

    # ── ANOVA (separate path) ──
    if model_choice == "ANOVA":
        st.markdown("#### ANOVA: Leverage Across Life Stages")
        anova = run_anova_by_stage(panel_df)

        ac1, ac2 = st.columns(2)
        with ac1:
            st.metric("F-statistic", f"{anova['f_stat']:.2f}")
            st.metric("p-value", format_pvalue(anova['p_value']))
            if anova["p_value"] < 0.05:
                st.success(anova["verdict"])
            else:
                st.info(anova["verdict"])

        with ac2:
            st.markdown("**Group Means**")
            st.dataframe(anova["group_stats"], hide_index=True, use_container_width=True)

        # Box plot
        fig = px.box(
            panel_df.dropna(subset=["leverage", "life_stage"]),
            x="life_stage", y="leverage", color="life_stage",
            color_discrete_map=STAGE_COLORS,
            category_orders={"life_stage": STAGE_ORDER},
            labels={"leverage": "Leverage (%)", "life_stage": ""},
        )
        fig.update_layout(**plotly_layout("Leverage Distribution by Life Stage", height=400))
        st.plotly_chart(fig, use_container_width=True, config=PLOTLY_CONFIG)

        # ── Pairwise Comparison (Table 5.9) ──
        st.divider()
        st.markdown("#### Pairwise Comparison")
        st.caption("Tukey's HSD post-hoc test — which specific stage pairs have significantly different mean leverage?")

        with st.spinner("Running pairwise comparisons across all life stages..."):
            pw = run_pairwise_comparison(panel_df)

        # KPI strip
        pw_c1, pw_c2, pw_c3 = st.columns(3)
        pw_c1.metric("Total Pairs Tested", pw["n_pairs"])
        pw_c2.metric("Significant Pairs", pw["n_significant"])
        pw_c3.metric("Significance Rate", f"{pw['n_significant'] / max(pw['n_pairs'], 1) * 100:.0f}%")

        # Heatmap: p-values with significance highlighting
        st.markdown("##### Mean Difference Heatmap")
        st.caption("Each cell shows the difference in mean leverage (row stage minus column stage). **Red border = statistically significant at 5%.**")

        import plotly.figure_factory as ff

        diff_matrix = pw["matrix_diff"]
        pval_matrix = pw["matrix_pval"]
        sig_matrix = pw["matrix_sig"]
        stages = list(diff_matrix.index)

        # Build annotated text: show mean diff + significance star
        annotations = []
        for i, row_stage in enumerate(stages):
            for j, col_stage in enumerate(stages):
                if row_stage == col_stage:
                    text = f"{pw['group_means'].get(row_stage, 0):.1f}"
                else:
                    diff_val = diff_matrix.loc[row_stage, col_stage]
                    pval = pval_matrix.loc[row_stage, col_stage]
                    star = significance_stars(pval)
                    text = f"{diff_val:+.1f}{star}"
                annotations.append(text)

        # Reshape annotations to 2D
        ann_matrix = [annotations[i*len(stages):(i+1)*len(stages)] for i in range(len(stages))]

        # Color: diverging scale centered at 0
        fig_pw = px.imshow(
            diff_matrix.values, x=stages, y=stages,
            color_continuous_scale="RdBu_r", zmin=-15, zmax=15,
            aspect="auto",
            labels=dict(x="Stage B", y="Stage A", color="Mean Diff (pp)"),
        )
        fig_pw.update_traces(
            text=ann_matrix, texttemplate="%{text}", textfont_size=11,
        )
        pw_layout = plotly_layout("", height=480)
        pw_layout["margin"] = dict(l=120, r=20, t=30, b=80)
        fig_pw.update_layout(**pw_layout)
        st.plotly_chart(fig_pw, use_container_width=True, config=PLOTLY_CONFIG)

        # Significant pairs table
        if pw["significant_pairs"]:
            st.markdown("##### Significant Pairs Detail")
            sig_df = pw["pairwise_df"][pw["pairwise_df"]["Significant"]].copy()
            sig_df["Stars"] = sig_df["p-value"].apply(significance_stars)
            sig_df["p-value"] = sig_df["p-value"].apply(format_pvalue)
            sig_df["Mean Diff"] = sig_df["Mean Diff"].round(2)
            sig_df["CI Lower"] = sig_df["CI Lower"].round(2)
            sig_df["CI Upper"] = sig_df["CI Upper"].round(2)
            st.dataframe(
                sig_df[["Stage A", "Stage B", "Mean Diff", "p-value", "Stars", "CI Lower", "CI Upper"]],
                use_container_width=True, hide_index=True,
            )

        # ── Detailed Explanation ──
        st.divider()
        st.markdown("#### Understanding Pairwise Comparison")

        st.markdown("""
**What is being tested?**

After ANOVA confirms that leverage differs significantly across life stages *as a group*, the natural follow-up question is: **which specific pairs of stages differ?** This is where pairwise comparison comes in.

For example, ANOVA tells us "at least one stage is different" — but it does not tell us whether Startup firms have significantly different leverage from Growth firms, or whether Maturity differs from Decline. Pairwise comparison answers this precisely.

**Method: Tukey's Honestly Significant Difference (HSD)**

Tukey's HSD is the gold standard post-hoc test for ANOVA. It compares the mean leverage of *every possible pair* of life stages while controlling for the **family-wise error rate** — the risk of false positives when making many comparisons simultaneously.

With 8 life stages, there are **28 unique pairs** (8×7/2). Without correction, testing 28 pairs at the 5% level would produce ~1.4 false positives by chance alone. Tukey's HSD adjusts for this, ensuring the overall false positive rate stays at 5%.

**How to read the heatmap:**

| Element | Meaning |
|---------|---------|
| **Diagonal cells** | Mean leverage (%) for that stage |
| **Off-diagonal cells** | Difference in mean leverage: Row stage minus Column stage |
| **Positive values (red)** | Row stage has *higher* leverage than column stage |
| **Negative values (blue)** | Row stage has *lower* leverage than column stage |
| **Stars (\\*\\*\\*, \\*\\*, \\*)** | Statistical significance: \\*\\*\\* p<0.001, \\*\\* p<0.01, \\* p<0.05 |
| **No stars** | Difference is *not* statistically significant — could be due to chance |
""")

        # Dynamic findings based on actual data
        findings = []
        actions = []

        if pw["significant_pairs"]:
            # Group findings
            sig_df_raw = pw["pairwise_df"][pw["pairwise_df"]["Significant"]].sort_values("Mean Diff", key=abs, ascending=False)

            top_pair = sig_df_raw.iloc[0]
            findings.append(
                f"The **largest significant difference** is between **{top_pair['Stage A']}** and **{top_pair['Stage B']}** "
                f"(mean difference: {top_pair['Mean Diff']:+.1f} percentage points, p={top_pair['p-value']:.4f}). "
                f"This means {top_pair['Stage A']} firms carry {'more' if top_pair['Mean Diff'] > 0 else 'less'} "
                f"debt relative to equity than {top_pair['Stage B']} firms, and this difference is not due to chance."
            )

            # Check thesis-specific pairs
            thesis_pairs = [("Startup", "Maturity"), ("Growth", "Maturity"), ("Maturity", "Decline"), ("Decline", "Decay")]
            for a, b in thesis_pairs:
                match = pw["pairwise_df"][
                    ((pw["pairwise_df"]["Stage A"] == a) & (pw["pairwise_df"]["Stage B"] == b)) |
                    ((pw["pairwise_df"]["Stage A"] == b) & (pw["pairwise_df"]["Stage B"] == a))
                ]
                if not match.empty:
                    row = match.iloc[0]
                    status = "**significantly different**" if row["Significant"] else "not significantly different"
                    findings.append(f"**{a} vs {b}**: {status} (mean diff: {row['Mean Diff']:+.1f}pp, p={row['p-value']:.4f})")

            # Count non-significant pairs
            n_nonsig = pw["n_pairs"] - pw["n_significant"]
            if n_nonsig > 0:
                nonsig_pairs = pw["pairwise_df"][~pw["pairwise_df"]["Significant"]]
                sample = nonsig_pairs.head(3)
                examples = ", ".join([f"{r['Stage A']}-{r['Stage B']}" for _, r in sample.iterrows()])
                findings.append(
                    f"**{n_nonsig} pairs** show no significant difference in leverage — "
                    f"for example: {examples}. These stages may have similar financing patterns."
                )

            actions.append(
                "**For researchers:** These pairwise results validate whether the thesis claim that 'capital structure varies across life stages' holds at the pair level, not just the group level. "
                "Report the significant pairs alongside the ANOVA F-test."
            )
            actions.append(
                "**For practitioners:** Stages with non-significant differences may be treated similarly for credit analysis. "
                "Focus lending criteria differentiation on stage pairs that ARE significantly different."
            )
            actions.append(
                "**For policy makers:** The magnitude of mean differences between stages (not just significance) indicates where intervention may be most impactful — "
                "large gaps suggest structural financing constraints at specific life stages."
            )

        st.markdown("**Key Findings from This Data:**")
        for f in findings:
            st.markdown(f"- {f}")

        if actions:
            st.markdown("**Actionable Insights:**")
            for a in actions:
                st.markdown(f"- {a}")

        st.stop()

    # ── Regression Models ──
    if model_choice == "Auto-Suggest":
        with st.spinner("Running all models + diagnostic tests..."):
            results = run_all_and_compare(panel_df, x_cols=selected_x)

        # Show recommendation
        rec = results["recommended"]
        hausman = results["hausman"]
        bp = results["bp_lm"]

        st.markdown("#### Auto-Suggestion Results")

        # Diagnostic test cards
        dc1, dc2, dc3 = st.columns(3)
        with dc1:
            st.markdown("**Breusch-Pagan LM**")
            st.metric("LM Statistic", f"{bp['lm_stat']:.2f}")
            st.caption(f"p = {format_pvalue(bp['lm_pvalue'])}")
            if bp["lm_pvalue"] < 0.05:
                st.success("Panel effects detected")
            else:
                st.info("No panel effects — OLS adequate")

        with dc2:
            st.markdown("**Hausman Test**")
            st.metric("Chi-squared", f"{hausman['chi2']:.2f}")
            st.caption(f"p = {format_pvalue(hausman['p_value'])}, df = {hausman['df']}")
            if hausman["p_value"] < 0.05:
                st.success("Fixed Effects preferred")
            else:
                st.info("Random Effects preferred")

        with dc3:
            st.markdown("**Recommendation**")
            st.metric("Best Model", rec)
            st.caption(hausman["verdict"])

        st.divider()

        # Model comparison table
        st.markdown("#### Model Comparison")
        st.dataframe(results["comparison"], hide_index=True, use_container_width=True)

        # Show the recommended model's coefficients
        best_key = "fe" if rec == "Fixed Effects" else ("re" if rec == "Random Effects" else "ols")
        best = results[best_key]

    else:
        # Run single model
        model_map = {
            "Pooled OLS": run_pooled_ols,
            "Fixed Effects": run_fixed_effects,
            "Random Effects": run_random_effects,
            "Robust (Huber M)": run_robust_regression,
        }
        with st.spinner(f"Running {model_choice}..."):
            best = model_map[model_choice](panel_df, x_cols=selected_x)

    # ── Display Results ──
    st.markdown(f"#### {best['type']} Results")

    # Metrics row — second cell adapts to whichever R² flavour the model exposes
    mc1, mc2, mc3, mc4 = st.columns(4)
    with mc1:
        # Robust regression returns a pseudo-R²; label it as such
        r2_label = "Pseudo R²" if best["type"].startswith("Robust M") else "R-squared"
        st.metric(r2_label, f"{best['r_squared']:.4f}")
    with mc2:
        r2w = best.get("r_squared_within")
        if r2w is not None:
            st.metric("Within R-squared", f"{r2w:.4f}")
        elif best["type"].startswith("Robust M"):
            # Show how many observations got downweighted by the M-estimator
            st.metric(
                "Downweighted obs",
                f"{best.get('n_downweighted', 0):,}",
                delta=f"min weight {best.get('weight_min', 1.0):.2f}",
                delta_color="off",
            )
        else:
            st.metric("Adj R-squared", f"{best.get('adj_r_squared', 0):.4f}")
    with mc3:
        st.metric("Observations", f"{best['n_obs']:,}")
    with mc4:
        st.metric("Firms", f"{best['n_firms']}")

    st.divider()

    # Coefficient table — full width so all columns visible
    st.markdown("**Coefficient Table**")
    display_coefs = format_coef_table(best["coef_table"])
    st.dataframe(display_coefs, hide_index=True, use_container_width=True)

    # Coefficient plot — full width below
    st.markdown("**Coefficient Plot**")
    ct = best["coef_table"]
    ct_no_const = ct[ct["Variable"] != "const"].copy()

    fig_coef = go.Figure()
    fig_coef.add_trace(go.Bar(
        x=ct_no_const["Coefficient"],
        y=ct_no_const["Variable"],
        orientation="h",
        marker_color=[PRIMARY if c > 0 else "#EF4444" for c in ct_no_const["Coefficient"]],
        text=[f"{c:.2f}" for c in ct_no_const["Coefficient"]],
        textposition="outside",
    ))
    fig_coef.add_vline(x=0, line_dash="dash", line_color="#9CA3AF")
    fig_coef.update_layout(**plotly_layout(height=320))
    st.plotly_chart(fig_coef, use_container_width=True, config=PLOTLY_CONFIG)

    # ── Dynamic Interpretation ──
    st.divider()
    hausman_data = results.get("hausman") if model_choice == "Auto-Suggest" else None
    insights, actions = interpret_econometric(best, hausman=hausman_data)
    render_interpretation(insights, actions, title="Results Interpretation & Call to Action")

    # ── Residual diagnostics ──
    with st.expander("Residual Diagnostics"):
        resid = best.get("residuals")
        fitted = best.get("fitted")
        if resid is not None and fitted is not None:
            resid_vals = np.asarray(resid).flatten()
            fitted_vals = np.asarray(fitted).flatten()

            rd1, rd2 = st.columns(2)
            with rd1:
                fig_rf = px.scatter(x=fitted_vals, y=resid_vals, opacity=0.3,
                                    labels={"x": "Fitted Values", "y": "Residuals"})
                fig_rf.add_hline(y=0, line_dash="dash", line_color="#9CA3AF")
                fig_rf.update_layout(**plotly_layout("Residuals vs Fitted", height=300))
                st.plotly_chart(fig_rf, use_container_width=True, config=PLOTLY_CONFIG)
            with rd2:
                fig_hist = px.histogram(x=resid_vals, nbins=50, opacity=0.7,
                                        labels={"x": "Residuals"})
                fig_hist.update_layout(**plotly_layout("Residual Distribution", height=300))
                fig_hist.update_traces(marker_color=PRIMARY)
                st.plotly_chart(fig_hist, use_container_width=True, config=PLOTLY_CONFIG)

    # ── Stage-Specific Regression Comparison ──
    st.divider()
    st.markdown("#### Stage-Specific Regression: How Do Determinants Differ by Life Stage?")
    st.caption("Runs the same regression separately for each stage — reveals which factors matter WHERE in the lifecycle.")

    if model_choice != "ANOVA":
        with st.spinner("Running stage-specific regressions..."):
            stage_coefs = []
            stages_available = [s for s in STAGE_ORDER if s in panel_df["life_stage"].unique()]
            for stage in stages_available:
                stage_df = panel_df[panel_df["life_stage"] == stage]
                if len(stage_df.dropna(subset=["leverage"] + selected_x)) < 30:
                    continue
                try:
                    sr = run_pooled_ols(stage_df, x_cols=selected_x)
                    for _, row in sr["coef_table"].iterrows():
                        if row["Variable"] != "const":
                            stage_coefs.append({
                                "Stage": stage,
                                "Variable": row["Variable"],
                                "Coefficient": row["Coefficient"],
                                "p-value": row["p-value"],
                                "Significant": "Yes" if row["p-value"] < 0.05 else "No",
                            })
                except Exception:
                    pass

        if stage_coefs:
            sc_df = pd.DataFrame(stage_coefs)

            # Heatmap of coefficients by stage
            pivot = sc_df.pivot(index="Variable", columns="Stage", values="Coefficient")
            stage_cols = [s for s in STAGE_ORDER if s in pivot.columns]
            pivot = pivot[stage_cols]

            fig_sc = px.imshow(
                pivot.values,
                x=pivot.columns.tolist(),
                y=pivot.index.tolist(),
                color_continuous_scale=["#EF4444", "#F8FAFC", PRIMARY],
                color_continuous_midpoint=0,
                aspect="auto",
                text_auto=".2f",
                labels={"color": "Coefficient"},
            )
            fig_sc.update_layout(**plotly_layout("Coefficient Comparison Across Life Stages", height=400))
            st.plotly_chart(fig_sc, use_container_width=True, config=PLOTLY_CONFIG)

            # Interpretation
            _sf, _sa = [], []
            _sf.append("Each cell shows the OLS coefficient for that determinant in that life stage. **Red = negative effect, Teal = positive effect** on leverage.")
            for var in pivot.index:
                row = pivot.loc[var].dropna()
                if len(row) >= 2:
                    max_stage = row.idxmax()
                    min_stage = row.idxmin()
                    spread = row.max() - row.min()
                    if spread > 5:
                        _sf.append(f"**{var}**: Effect varies significantly — strongest in **{max_stage}** ({row.max():.1f}), weakest in **{min_stage}** ({row.min():.1f}). Spread = {spread:.1f}pp.")

            sig_counts = sc_df.groupby("Variable")["Significant"].apply(lambda x: (x == "Yes").sum())
            always_sig = sig_counts[sig_counts == len(stage_cols)]
            if len(always_sig) > 0:
                _sf.append(f"**Always significant** across all stages: {', '.join(always_sig.index)}.")
            never_sig = sig_counts[sig_counts == 0]
            if len(never_sig) > 0:
                _sf.append(f"**Never significant** in any stage: {', '.join(never_sig.index)} — these may not drive capital structure decisions.")

            _sa.append("Use stage-specific coefficients for targeted advice: e.g., tangibility matters for Growth firms' borrowing, but not for Mature firms.")
            _sa.append("Variables that change sign across stages reveal lifecycle-dependent capital structure dynamics — a key thesis contribution.")
            _render_insight_box("Stage-Specific Coefficients — Lifecycle Dynamics", _sf, _sa,
                "Reveals how the same determinant has different effects depending on where a firm is in its lifecycle.")
