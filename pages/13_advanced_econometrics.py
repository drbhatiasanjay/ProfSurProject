"""
Advanced Econometrics — Dynamic GMM, Delta-Leverage models, Stage Comparisons.
Extends thesis methodology beyond the basic Econometrics Lab.
"""

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import numpy as np
import db
from helpers import (
    plotly_layout, format_pvalue, significance_stars, format_coef_table, ensure_session_state,
    STAGE_COLORS, STAGE_ORDER, PRIMARY, SECONDARY, ACCENT, PLOTLY_CONFIG,
    render_interpretation,
)
from models.econometric import (
    run_system_gmm, run_delta_leverage_all, run_delta_leverage_by_stage,
    run_stage_comparison, run_breusch_pagan_lm, run_pooled_ols,
    run_iv_regression,
)
from models.base import DEFAULT_X_COLS

ensure_session_state()

# Reproducibility pin — thesis-panel only.
filters = dict(st.session_state.filters)
filters["panel_mode"] = "thesis"
yr_min_t, yr_max_t = db.get_year_range("thesis")
yr_prev = filters.get("year_range", (yr_min_t, yr_max_t))
filters["year_range"] = (max(yr_prev[0], yr_min_t), min(yr_prev[1], yr_max_t))
ft = db.filters_to_tuple(filters)

st.markdown("### Advanced Econometrics")
st.caption("Dynamic panel GMM, change-in-leverage models, and stage comparison regressions — extending the thesis methodology.")
st.info("📌 **Pinned to Thesis panel (2001–2024)** for reproducibility.", icon="🔒")

with st.expander("About these models"):
    st.markdown("""
**Dynamic Panel GMM (System GMM)** estimates leverage with a lagged dependent variable, capturing the "stickiness" of capital structure.
The thesis (Table 5.12) shows leverage at time *t* depends on leverage at *t-1* — firms don't adjust instantly.
- **AR(1) test**: Should be significant (first-order autocorrelation expected)
- **AR(2) test**: Should NOT be significant (validates instrument choice)
- **Sargan/Hansen test**: Should NOT be significant (instruments are valid)

**Delta-Leverage Models** use the CHANGE in leverage as the dependent variable (Tables 5.11, 6.5, 7.2, 7.4, 8.4, 8.5).
This answers: *What drives changes in capital structure, not just its level?*

**Stage Comparisons** run separate regressions for two life stages and compare coefficients side-by-side (Table 7.5).
This reveals which determinants differ between stages — e.g., profitability matters more in Maturity than Growth.
""")

    panel_df = db.get_active_panel_data(ft)
if panel_df.empty:
    st.warning("No data. Adjust filters.")
    st.stop()

tab_gmm, tab_delta, tab_compare, tab_iv = st.tabs([
    "System GMM",
    "Delta-Leverage",
    "Stage Comparisons",
    "IV / 2SLS",
])


# ══════════════════════════════════════════════
# TAB 1: System GMM
# ══════════════════════════════════════════════
with tab_gmm:
    st.subheader("Dynamic Panel GMM")
    st.caption("Leverage with lagged dependent variable — captures capital structure persistence")

    if st.button("Run System GMM", type="primary", key="run_gmm"):
        with st.spinner("Estimating GMM model..."):
            gmm = run_system_gmm(panel_df)

        if "error" in gmm:
            st.error(gmm["error"])
        else:
            # Metrics
            mc1, mc2, mc3 = st.columns(3)
            mc1.metric("R-squared", f"{gmm['r_squared']:.4f}")
            mc2.metric("Observations", f"{gmm['n_obs']:,}")
            mc3.metric("Firms", f"{gmm['n_firms']:,}")

            # Coefficient table
            st.markdown("#### Coefficient Estimates")
            ct = format_coef_table(gmm["coef_table"])
            st.dataframe(ct, use_container_width=True, hide_index=True)

            # Diagnostic tests
            st.markdown("#### Diagnostic Tests")
            dc1, dc2, dc3 = st.columns(3)
            with dc1:
                ar1 = gmm["ar1"]
                st.markdown(f"**AR(1) Test**")
                st.metric("Correlation", f"{ar1['correlation']:.4f}")
                st.metric("p-value", f"{ar1['p_value']:.4f}")
                st.caption(ar1["verdict"])
            with dc2:
                ar2 = gmm["ar2"]
                st.markdown(f"**AR(2) Test**")
                st.metric("Correlation", f"{ar2['correlation']:.4f}")
                st.metric("p-value", f"{ar2['p_value']:.4f}")
                st.caption(ar2["verdict"])
            with dc3:
                sargan = gmm["sargan"]
                st.markdown(f"**Sargan/Hansen Test**")
                st.metric("J-statistic", f"{sargan['j_stat']:.4f}")
                st.metric("p-value", f"{sargan['p_value']:.4f}")
                st.caption(sargan["verdict"])

            # Interpretation
            insights = []
            lag_row = gmm["coef_table"][gmm["coef_table"]["Variable"].str.contains("lag")]
            if not lag_row.empty:
                lag_coef = lag_row.iloc[0]["Coefficient"]
                insights.append(f"Lagged leverage coefficient is **{lag_coef:.3f}** — capital structure is {'highly' if abs(lag_coef) > 0.5 else 'moderately'} persistent. A firm's leverage this year is strongly influenced by last year's.")
            if ar2["p_value"] > 0.05:
                insights.append("AR(2) is not significant (p > 0.05) — instruments are appropriately specified.")
            else:
                insights.append("AR(2) is significant — instrument validity is questionable. Interpret with caution.")
            if sargan["p_value"] > 0.05:
                insights.append("Sargan test passes — overidentifying restrictions are valid.")

            render_interpretation(insights, [
                "Compare the lag DV coefficient with thesis Table 5.12 results.",
                "A coefficient between 0.3-0.7 is typical for capital structure persistence.",
            ], title="GMM Interpretation")


# ══════════════════════════════════════════════
# TAB 2: Delta-Leverage
# ══════════════════════════════════════════════
with tab_delta:
    st.subheader("Determinants of Changes in Capital Structure")
    st.caption("What drives leverage CHANGES (not levels)? First-difference regressions.")

    delta_mode = st.radio("Mode", ["Full Panel", "By Life Stage"], horizontal=True, key="delta_mode")

    if st.button("Run Delta-Leverage Models", type="primary", key="run_delta"):
        if delta_mode == "Full Panel":
            with st.spinner("Running delta-leverage OLS/FE/RE + Hausman..."):
                result = run_delta_leverage_all(panel_df)

            st.markdown(f"**Recommended model: {result['recommended']}**")

            # Hausman test result
            h = result["hausman"]
            st.info(f"Hausman test: chi2={h['chi2']:.2f}, p={h['p_value']:.4f} — {h['verdict']}")

            # Show recommended model's coefficients
            rec = result["fe"] if result["recommended"] == "Fixed Effects" else result["re"]
            st.markdown("#### Coefficient Estimates (Recommended Model)")
            ct = format_coef_table(rec["coef_table"])
            st.dataframe(ct, use_container_width=True, hide_index=True)

            # Compare all three
            st.markdown("#### Model Comparison")
            comp_rows = []
            for key, label in [("ols", "Pooled OLS"), ("fe", "Fixed Effects"), ("re", "Random Effects")]:
                r = result[key]
                comp_rows.append({
                    "Model": label,
                    "R-squared": f"{r['r_squared']:.4f}",
                    "N Obs": r["n_obs"],
                })
            st.dataframe(pd.DataFrame(comp_rows), use_container_width=True, hide_index=True)

            insights = [
                "Delta-leverage models show what drives **changes** in leverage, complementing level regressions.",
                f"The {result['recommended']} model is preferred based on the Hausman test."
            ]
            render_interpretation(insights, [
                "Compare coefficient signs with the level regressions in the Econometrics Lab.",
                "If profitability is negative here too, the Pecking Order holds for both levels and changes.",
            ], title="Delta-Leverage Interpretation")

        else:
            with st.spinner("Running stage-specific delta-leverage regressions..."):
                results = run_delta_leverage_by_stage(panel_df)

            st.markdown("#### Delta-Leverage by Life Stage")

            # Summary table
            summary_rows = []
            for stage in STAGE_ORDER:
                if stage in results:
                    r = results[stage]
                    if "error" in r:
                        summary_rows.append({"Stage": stage, "Status": f"Skipped: {r['error']}", "R-sq": "", "N Obs": ""})
                    else:
                        summary_rows.append({
                            "Stage": stage, "Status": "OK",
                            "R-sq": f"{r['r_squared']:.4f}", "N Obs": r["n_obs"],
                        })

            st.dataframe(pd.DataFrame(summary_rows), use_container_width=True, hide_index=True)

            # Detail per stage
            for stage in STAGE_ORDER:
                if stage in results and "error" not in results[stage]:
                    with st.expander(f"{stage} — Delta-Leverage Coefficients"):
                        ct = format_coef_table(results[stage]["coef_table"])
                        st.dataframe(ct, use_container_width=True, hide_index=True)


# ══════════════════════════════════════════════
# TAB 3: Stage Comparisons
# ══════════════════════════════════════════════
with tab_compare:
    st.subheader("Stage Comparison Regressions")
    st.caption("Compare leverage determinants between two life stages — side-by-side coefficient analysis")

    col_a, col_b = st.columns(2)
    with col_a:
        stage_a = st.selectbox("Stage A", STAGE_ORDER, index=1, key="cmp_a")  # Growth
    with col_b:
        stage_b = st.selectbox("Stage B", STAGE_ORDER, index=2, key="cmp_b")  # Maturity

    compare_delta = st.checkbox("Compare delta-leverage (changes) instead of levels", key="cmp_delta")

    if st.button("Run Comparison", type="primary", key="run_cmp"):
        if stage_a == stage_b:
            st.warning("Select two different stages.")
        else:
            with st.spinner(f"Comparing {stage_a} vs {stage_b}..."):
                if compare_delta:
                    from models.econometric import _compute_delta_leverage
                    delta_df = _compute_delta_leverage(panel_df)
                    result = run_stage_comparison(delta_df, stage_a, stage_b,
                                                   y_col="delta_leverage")
                else:
                    result = run_stage_comparison(panel_df, stage_a, stage_b)

            if "error" in result:
                st.error(result["error"])
            else:
                # Summary metrics
                mc1, mc2, mc3 = st.columns(3)
                mc1.metric(f"{stage_a} R-sq", f"{result['result_a']['r_squared']:.4f}")
                mc2.metric(f"{stage_b} R-sq", f"{result['result_b']['r_squared']:.4f}")
                divergent_count = result["comparison"]["Divergent"].sum()
                mc3.metric("Divergent Variables", int(divergent_count))

                # Comparison table
                st.markdown("#### Side-by-Side Coefficients")
                comp = result["comparison"].copy()
                # Format p-values with stars
                for s in [stage_a, stage_b]:
                    p_col = f"{s} p"
                    if p_col in comp.columns:
                        comp[f"{s} Sig"] = comp[p_col].apply(significance_stars)
                        comp[p_col] = comp[p_col].apply(format_pvalue)

                st.dataframe(comp, use_container_width=True, hide_index=True)

                # Visual: coefficient comparison bar chart
                plot_data = result["comparison"][["Variable", f"{stage_a} Coef", f"{stage_b} Coef"]].melt(
                    id_vars="Variable", var_name="Stage", value_name="Coefficient"
                )
                fig = px.bar(plot_data, x="Variable", y="Coefficient", color="Stage", barmode="group",
                             color_discrete_map={f"{stage_a} Coef": STAGE_COLORS.get(stage_a, PRIMARY),
                                                  f"{stage_b} Coef": STAGE_COLORS.get(stage_b, SECONDARY)})
                fig.update_layout(**plotly_layout(f"{stage_a} vs {stage_b} — Coefficient Comparison", height=400))
                st.plotly_chart(fig, use_container_width=True, config=PLOTLY_CONFIG)

                # Interpretation
                insights = []
                divergent = result["comparison"][result["comparison"]["Divergent"]]
                if not divergent.empty:
                    for _, row in divergent.iterrows():
                        insights.append(f"**{row['Variable']}** has divergent behavior: {stage_a}={row[f'{stage_a} Coef']:.4f}, {stage_b}={row[f'{stage_b} Coef']:.4f}")
                else:
                    insights.append(f"No strongly divergent determinants between {stage_a} and {stage_b}.")

                render_interpretation(insights, [
                    f"Divergent variables indicate where {stage_a} and {stage_b} firms respond differently to the same determinant.",
                    "Compare with thesis Table 7.5 for Growth vs Maturity results.",
                ], title=f"{stage_a} vs {stage_b} — Key Differences")


# ══════════════════════════════════════════════
# TAB 4: IV / 2SLS (endogeneity correction)
# ══════════════════════════════════════════════
with tab_iv:
    st.subheader("Instrumental-Variables Regression (2SLS)")
    st.caption(
        "Address endogeneity by instrumenting a suspected-endogenous regressor with its lagged values. "
        "Default: instrument profitability with profitability_lag1 + profitability_lag2."
    )

    with st.expander("Why this matters", expanded=False):
        st.markdown("""
**Endogeneity in capital structure**: profitability and leverage are simultaneously determined.
A simple OLS coefficient on profitability is biased because *current-year residuals* feed
back into *current-year profitability* through retained earnings, dividend policy, and
managerial response to financing constraints.

**The 2SLS fix**: replace the endogenous regressor with its predicted value from a first-stage
regression on lagged values (which are pre-determined and therefore exogenous to current
residuals).

**Three diagnostics that decide whether the IV estimate is trustworthy:**
- **First-stage F-statistic** — instrument *strength*. Rule of thumb: F > 10 means lags are
  meaningful predictors of the current value. Below 10, instruments are weak and 2SLS is
  worse than just running OLS.
- **Sargan over-identification** (only when ≥ 2 instruments) — instrument *validity*.
  p > 0.05 means we cannot reject the moment conditions; instruments behave as exogenous.
- **Wu-Hausman** — *was the regressor actually endogenous?* p < 0.05 says yes, IV was needed.
  p > 0.05 says OLS would have given the same answer; you can quote the simpler model.
""")

    iv_col_left, iv_col_right = st.columns([1, 3])

    with iv_col_left:
        iv_endog = st.selectbox(
            "Endogenous regressor",
            options=DEFAULT_X_COLS,
            index=DEFAULT_X_COLS.index("profitability"),
            help="The regressor to instrument. Profitability is the canonical endogenous variable in capital structure.",
        )
        iv_lags = st.multiselect(
            "Instruments (lags of the endogenous regressor)",
            options=[1, 2, 3],
            default=[1, 2],
            format_func=lambda n: f"{iv_endog}_lag{n}",
        )
        run_iv_btn = st.button("Run 2SLS", type="primary", key="run_iv")

    with iv_col_right:
        if run_iv_btn:
            instruments = [f"{iv_endog}_lag{n}" for n in iv_lags] if iv_lags else None
            with st.spinner("Estimating 2SLS..."):
                iv = run_iv_regression(panel_df, x_endog=iv_endog, instruments=instruments)

            if "error" in iv:
                st.error(iv["error"])
            else:
                # Headline metrics
                m1, m2, m3, m4 = st.columns(4)
                m1.metric("R-squared", f"{iv['r_squared']:.4f}")
                m2.metric("Observations", f"{iv['n_obs']:,}")
                m3.metric("Firms", f"{iv['n_firms']:,}")
                m4.metric("Endogenous", iv["endogenous"])

                # Diagnostic strip — strength + validity + endogeneity tests
                st.markdown("#### Diagnostic Tests")
                d1, d2, d3 = st.columns(3)
                with d1:
                    st.markdown("**First-Stage F-stat**")
                    fs_f = iv.get("first_stage_f")
                    if fs_f is not None:
                        st.metric("F", f"{fs_f:.2f}")
                        if fs_f > 10:
                            st.success("Strong instruments (F > 10)")
                        else:
                            st.warning("Weak instruments — interpret IV cautiously")
                    else:
                        st.info("Not reported by linearmodels")
                with d2:
                    st.markdown("**Sargan over-id**")
                    sp = iv.get("sargan_pvalue")
                    if sp is not None:
                        st.metric("p-value", format_pvalue(sp))
                        if sp > 0.05:
                            st.success("Instruments appear valid (p > 0.05)")
                        else:
                            st.warning("Over-id rejected — moment conditions may not hold")
                    else:
                        st.caption("Needs ≥ 2 instruments")
                with d3:
                    st.markdown("**Wu-Hausman**")
                    wp = iv.get("wu_hausman_pvalue")
                    if wp is not None:
                        st.metric("p-value", format_pvalue(wp))
                        if wp < 0.05:
                            st.success("Endogeneity confirmed — IV was warranted")
                        else:
                            st.info("OLS and IV agree — endogeneity not detected")
                    else:
                        st.info("Not reported")

                # Coefficient table
                st.markdown("#### IV / 2SLS Coefficients")
                ct = format_coef_table(iv["coef_table"])
                st.dataframe(ct, hide_index=True, use_container_width=True)

                # Interpretation
                insights = []
                endog_row = iv["coef_table"][iv["coef_table"]["Variable"] == iv_endog]
                if not endog_row.empty:
                    iv_coef = endog_row.iloc[0]["Coefficient"]
                    iv_p = endog_row.iloc[0]["p-value"]
                    insights.append(
                        f"**IV coefficient on {iv_endog}**: {iv_coef:+.4f} "
                        f"(p={format_pvalue(iv_p)}). Compare against OLS — if magnitudes "
                        f"differ materially, OLS was biased by endogeneity."
                    )
                if iv.get("first_stage_f") is not None and iv["first_stage_f"] < 10:
                    insights.append(
                        "First-stage F-stat is below 10, so instruments are weak — "
                        "the 2SLS estimate inherits high standard errors. Try adding more lags."
                    )
                if iv.get("wu_hausman_pvalue") is not None and iv["wu_hausman_pvalue"] > 0.05:
                    insights.append(
                        "Wu-Hausman cannot reject exogeneity — OLS and IV give the same answer. "
                        "You can quote the simpler OLS estimate without bias concerns."
                    )

                render_interpretation(insights, [
                    "Run a Pooled OLS in the Econometrics Lab on the same panel and compare the "
                    f"coefficient on {iv_endog} against the IV value above.",
                    "If you suspect tangibility or dividend are also endogenous, re-run with "
                    "those as the endogenous regressor and the same lag structure.",
                ], title="2SLS Interpretation")
        else:
            st.info("Configure the spec on the left and click **Run 2SLS** to estimate.")
