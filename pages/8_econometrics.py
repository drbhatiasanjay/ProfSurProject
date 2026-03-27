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
    plotly_layout, STAGE_COLORS, STAGE_ORDER, PRIMARY, SECONDARY, ACCENT, PLOTLY_CONFIG,
    interpret_econometric, render_interpretation,
)
from models.econometric import (
    run_pooled_ols, run_fixed_effects, run_random_effects,
    run_hausman_test, run_breusch_pagan_lm, run_anova_by_stage,
    run_all_and_compare,
)
from models.base import DEFAULT_X_COLS

filters = st.session_state.filters
ft = db.filters_to_tuple(filters)

st.markdown("### Econometrics Lab")
st.caption("Panel regression models replicating the thesis methodology. Auto-suggests the best model via diagnostic tests.")

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
        ["Auto-Suggest", "Pooled OLS", "Fixed Effects", "Random Effects", "ANOVA"],
        index=0,
    )

with col_right:
    # ── Load data ──
    with st.spinner("Loading panel data..."):
        panel_df = db.get_panel_data(ft)

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
        }
        with st.spinner(f"Running {model_choice}..."):
            best = model_map[model_choice](panel_df, x_cols=selected_x)

    # ── Display Results ──
    st.markdown(f"#### {best['type']} Results")

    # Metrics row
    mc1, mc2, mc3, mc4 = st.columns(4)
    with mc1:
        st.metric("R-squared", f"{best['r_squared']:.4f}")
    with mc2:
        r2w = best.get("r_squared_within")
        st.metric("Within R-squared" if r2w is not None else "Adj R-squared",
                  f"{r2w:.4f}" if r2w is not None else f"{best.get('adj_r_squared', 0):.4f}")
    with mc3:
        st.metric("Observations", f"{best['n_obs']:,}")
    with mc4:
        st.metric("Firms", f"{best['n_firms']}")

    st.divider()

    # Coefficient table and chart side by side
    coef_left, coef_right = st.columns([1, 1])

    with coef_left:
        st.markdown("**Coefficient Table**")
        display_coefs = format_coef_table(best["coef_table"])
        st.dataframe(display_coefs, hide_index=True, use_container_width=True)

    with coef_right:
        st.markdown("**Coefficient Plot**")
        ct = best["coef_table"]
        ct_no_const = ct[ct["Variable"] != "const"].copy()

        fig_coef = go.Figure()
        fig_coef.add_trace(go.Bar(
            x=ct_no_const["Coefficient"],
            y=ct_no_const["Variable"],
            orientation="h",
            marker_color=[PRIMARY if c > 0 else "#EF4444" for c in ct_no_const["Coefficient"]],
        ))
        if "CI Lower" in ct_no_const.columns and "CI Upper" in ct_no_const.columns:
            fig_coef.add_trace(go.Scatter(
                x=pd.concat([ct_no_const["CI Lower"], ct_no_const["CI Upper"][::-1]]),
                y=pd.concat([ct_no_const["Variable"], ct_no_const["Variable"][::-1]]),
                mode="lines", line=dict(width=0), fill="toself",
                fillcolor="rgba(13,148,136,0.15)", showlegend=False,
            ))
        fig_coef.add_vline(x=0, line_dash="dash", line_color="#9CA3AF")
        fig_coef.update_layout(**plotly_layout(height=350))
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
