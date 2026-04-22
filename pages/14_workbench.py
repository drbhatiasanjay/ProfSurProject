"""
Statistical Workbench — Stata-like regression builder UI.
Build custom models with variable transforms, subsample filters,
post-estimation diagnostics, and esttab-style comparison tables.
"""

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import numpy as np
from scipy import stats

import db
from helpers import (
    format_coef_table, significance_stars, plotly_layout, ensure_session_state,
    _render_insight_box, PRIMARY, SECONDARY, ACCENT, PLOTLY_CONFIG,
    format_pvalue,
)

ensure_session_state()
from models.workbench import (
    apply_transforms, apply_subsample_filter, fit_model,
    run_wald_test, compute_post_estimation, build_comparison_table,
    export_latex, export_comparison_csv, check_collinearity,
)
from models.data_ingest import list_available_datasets, get_dataset


# ── Helper Functions (defined early so UI code can reference them) ──

def _transform_label(t):
    """Human-readable label for a transform spec."""
    tt = t["type"]
    if tt == "interaction":
        return f"{t['var1']} x {t['var2']}"
    elif tt == "sq":
        return f"{t['var']}^2"
    elif tt == "log":
        return f"ln({t['var']})"
    elif tt == "lag":
        return f"L{t.get('order', 1)}.{t['var']}"
    elif tt == "diff":
        return f"D.{t['var']}"
    return str(t)


def _parse_filter_value(raw_str, op):
    """Parse user-entered filter value to the correct type."""
    raw_str = raw_str.strip()
    if op in ("in", "not_in"):
        parts = [p.strip() for p in raw_str.split(",")]
        try:
            return [float(p) for p in parts]
        except ValueError:
            return parts
    try:
        return float(raw_str)
    except ValueError:
        return raw_str


def _render_coefficient_interpretation(result):
    """Generate a dynamic interpretation expander for the current model."""
    coef_df = result.get("coef_table")
    if coef_df is None or coef_df.empty:
        return

    findings = []
    actions = []

    model_type = result.get("type", "")
    r2 = result.get("r_squared", 0)
    n_obs_val = result.get("n_obs", 0)

    findings.append(
        f"**{model_type}** with {n_obs_val:,} observations. "
        f"R-squared = {r2:.4f}."
    )

    sig_vars = coef_df[
        (coef_df["p-value"] < 0.05) & (coef_df["Variable"] != "const")
    ]
    nonsig_vars = coef_df[
        (coef_df["p-value"] >= 0.05) & (coef_df["Variable"] != "const")
    ]

    if len(sig_vars) > 0:
        for _, row in sig_vars.iterrows():
            direction = "positive" if row["Coefficient"] > 0 else "negative"
            stars = significance_stars(row["p-value"])
            findings.append(
                f"**{row['Variable']}**: {direction} effect "
                f"(coef={row['Coefficient']:.4f}{stars})."
            )
    else:
        findings.append("No variables are statistically significant at the 5% level.")

    if len(nonsig_vars) > 0:
        ns_list = ", ".join(nonsig_vars["Variable"].tolist())
        findings.append(f"Not significant: {ns_list}.")

    if r2 < 0.1:
        actions.append(
            "Low R-squared. Consider adding more predictors, "
            "variable transforms, or using Fixed Effects."
        )
    if len(sig_vars) == 0:
        actions.append(
            "No significant coefficients. Check for multicollinearity, "
            "try different functional forms, or expand the sample."
        )
    if len(sig_vars) > 0:
        top_var = sig_vars.loc[sig_vars["Coefficient"].abs().idxmax()]
        actions.append(
            f"Largest effect: **{top_var['Variable']}** "
            f"(coef={top_var['Coefficient']:.4f}). "
            "Investigate its economic mechanism."
        )

    _render_insight_box(
        "Regression Results Interpretation",
        findings, actions,
        context=f"Model: {model_type} | DV: {result.get('y_col', '?')}"
    )


# ── Session State ──

if "wb_saved_models" not in st.session_state:
    st.session_state.wb_saved_models = []
if "wb_transforms" not in st.session_state:
    st.session_state.wb_transforms = []
if "wb_conditions" not in st.session_state:
    st.session_state.wb_conditions = []
if "wb_current_result" not in st.session_state:
    st.session_state.wb_current_result = None

# ── Page Header ──

st.markdown("### Statistical Workbench")
st.caption(
    "Stata-like regression builder. Choose variables, add transforms, "
    "configure models, and compare results side-by-side."
)

# ── Data Source Selector ──

available = list_available_datasets()
ds_names = [d["name"] for d in available]
ds_choice = st.selectbox("Data Source", ds_names, key="wb_datasource")

# Load dataset
ds_meta = next(d for d in available if d["name"] == ds_choice)
try:
    filters = st.session_state.get("filters")
    if ds_meta["source"] == "database" and filters:
        raw_df = get_dataset(ds_choice, filters=filters)
    else:
        raw_df = get_dataset(ds_choice)
except Exception as e:
    st.error(f"Failed to load dataset: {e}")
    st.stop()

if raw_df.empty:
    st.warning("Selected dataset is empty. Choose another source or upload data.")
    st.stop()

# Summary caption
n_firms = raw_df["company_code"].nunique() if "company_code" in raw_df.columns else "?"
n_obs = len(raw_df)
if "year" in raw_df.columns:
    yr_min, yr_max = int(raw_df["year"].min()), int(raw_df["year"].max())
    yr_text = f"{yr_min}--{yr_max}"
else:
    yr_text = "unknown"
st.caption(f"{n_firms} firms, {n_obs:,} obs, years {yr_text}")

# ── Determine column lists ──

ENTITY_TIME_COLS = {"company_code", "company_name", "year", "life_stage", "industry_group"}
all_cols = list(raw_df.columns)
numeric_cols = sorted(
    raw_df.select_dtypes(include=[np.number]).columns
    .difference(ENTITY_TIME_COLS)
    .tolist()
)

# ── Layout: Left (model builder) | Right (results) ──

col_left, col_right = st.columns([3, 7], gap="medium")

# ==========================================================================
# LEFT COLUMN — Model Builder
# ==========================================================================
with col_left:
    st.markdown("#### Model Builder")

    # 1. Dependent Variable
    default_dv = "leverage" if "leverage" in numeric_cols else numeric_cols[0] if numeric_cols else None
    dv_idx = numeric_cols.index(default_dv) if default_dv in numeric_cols else 0
    dep_var = st.selectbox("Dependent Variable", numeric_cols, index=dv_idx, key="wb_dv")

    # 2. Independent Variables
    iv_defaults = [
        c for c in ["profitability", "tangibility", "tax", "log_size", "tax_shield", "dividend"]
        if c in numeric_cols and c != dep_var
    ]
    iv_options = [c for c in numeric_cols if c != dep_var]
    indep_vars = st.multiselect(
        "Independent Variables", iv_options, default=iv_defaults, key="wb_iv"
    )

    # 3. Transforms
    with st.expander("Add Variable Transforms"):
        transform_vars = [dep_var] + indep_vars if indep_vars else [dep_var]

        # Interaction
        st.markdown("**Interaction**")
        t_col1, t_col2, t_col3 = st.columns([4, 4, 2])
        with t_col1:
            int_var1 = st.selectbox("Var 1", transform_vars, key="wb_int_v1")
        with t_col2:
            int_var2 = st.selectbox("Var 2", transform_vars, key="wb_int_v2")
        with t_col3:
            if st.button("Add", key="wb_add_int"):
                spec = {"type": "interaction", "var1": int_var1, "var2": int_var2}
                if spec not in st.session_state.wb_transforms:
                    st.session_state.wb_transforms.append(spec)
                    st.rerun()

        # Squared
        st.markdown("**Squared**")
        sq_col1, sq_col2 = st.columns([8, 2])
        with sq_col1:
            sq_var = st.selectbox("Variable", transform_vars, key="wb_sq_v")
        with sq_col2:
            if st.button("Add", key="wb_add_sq"):
                spec = {"type": "sq", "var": sq_var}
                if spec not in st.session_state.wb_transforms:
                    st.session_state.wb_transforms.append(spec)
                    st.rerun()

        # Log
        st.markdown("**Log**")
        log_col1, log_col2 = st.columns([8, 2])
        with log_col1:
            log_var = st.selectbox("Variable", transform_vars, key="wb_log_v")
        with log_col2:
            if st.button("Add", key="wb_add_log"):
                spec = {"type": "log", "var": log_var}
                if spec not in st.session_state.wb_transforms:
                    st.session_state.wb_transforms.append(spec)
                    st.rerun()

        # Lag
        st.markdown("**Lag**")
        lag_c1, lag_c2, lag_c3 = st.columns([5, 3, 2])
        with lag_c1:
            lag_var = st.selectbox("Variable", transform_vars, key="wb_lag_v")
        with lag_c2:
            lag_order = st.number_input("Order", 1, 5, 1, key="wb_lag_ord")
        with lag_c3:
            if st.button("Add", key="wb_add_lag"):
                spec = {"type": "lag", "var": lag_var, "order": int(lag_order)}
                if spec not in st.session_state.wb_transforms:
                    st.session_state.wb_transforms.append(spec)
                    st.rerun()

        # Difference
        st.markdown("**Difference**")
        diff_c1, diff_c2 = st.columns([8, 2])
        with diff_c1:
            diff_var = st.selectbox("Variable", transform_vars, key="wb_diff_v")
        with diff_c2:
            if st.button("Add", key="wb_add_diff"):
                spec = {"type": "diff", "var": diff_var}
                if spec not in st.session_state.wb_transforms:
                    st.session_state.wb_transforms.append(spec)
                    st.rerun()

        # Show current transforms as removable tags
        if st.session_state.wb_transforms:
            st.markdown("---")
            st.markdown("**Active Transforms:**")
            for i, t in enumerate(st.session_state.wb_transforms):
                label = _transform_label(t)
                tc1, tc2 = st.columns([8, 2])
                with tc1:
                    st.code(label, language=None)
                with tc2:
                    if st.button("x", key=f"wb_rm_t_{i}"):
                        st.session_state.wb_transforms.pop(i)
                        st.rerun()

    # 4. Model Configuration
    st.markdown("#### Model Configuration")
    model_type = st.radio(
        "Model", ["OLS", "FE", "RE", "Quantile"], horizontal=True, key="wb_model"
    )

    cov_options_map = {
        "OLS": ["HC1", "HC3"],
        "FE": ["clustered_entity", "clustered_time", "two_way"],
        "RE": ["clustered_entity", "clustered_time", "two_way"],
        "Quantile": [],
    }
    cov_options = cov_options_map[model_type]

    if cov_options:
        cov_type = st.selectbox("Covariance", cov_options, key="wb_cov")
    else:
        cov_type = "kernel"
        st.caption("Covariance: kernel (default for quantile)")

    quantile_val = 0.5
    if model_type == "Quantile":
        quantile_val = st.slider(
            "Quantile", 0.10, 0.90, 0.50, 0.05, key="wb_quantile"
        )

    # 5. Subsample Filter
    with st.expander("Subsample Restrictions"):
        all_filter_cols = sorted(raw_df.columns.tolist())
        ops = [">", "<", ">=", "<=", "==", "!=", "in", "not_in"]

        fc1, fc2, fc3, fc4 = st.columns([3, 2, 3, 2])
        with fc1:
            filt_col = st.selectbox("Column", all_filter_cols, key="wb_fc")
        with fc2:
            filt_op = st.selectbox("Operator", ops, key="wb_fop")
        with fc3:
            filt_val = st.text_input("Value", key="wb_fv",
                                     help="Numeric or text. For 'in'/'not_in' use comma-separated values.")
        with fc4:
            if st.button("Add", key="wb_add_cond"):
                parsed = _parse_filter_value(filt_val, filt_op)
                cond = {"column": filt_col, "op": filt_op, "value": parsed}
                st.session_state.wb_conditions.append(cond)
                st.rerun()

        if st.session_state.wb_conditions:
            st.markdown("**Active Filters:**")
            for i, c in enumerate(st.session_state.wb_conditions):
                cc1, cc2 = st.columns([8, 2])
                with cc1:
                    val_display = c["value"]
                    st.code(f"{c['column']} {c['op']} {val_display}", language=None)
                with cc2:
                    if st.button("x", key=f"wb_rm_c_{i}"):
                        st.session_state.wb_conditions.pop(i)
                        st.rerun()

    # 6. Action Buttons
    st.markdown("---")
    btn_c1, btn_c2, btn_c3 = st.columns(3)
    with btn_c1:
        run_clicked = st.button("Run Model", type="primary", key="wb_run",
                                use_container_width=True)
    with btn_c2:
        save_clicked = st.button("Save to Comparison", key="wb_save",
                                 use_container_width=True)
    with btn_c3:
        clear_clicked = st.button("Clear All", key="wb_clear",
                                  use_container_width=True)



# ── Handle button actions ──

if clear_clicked:
    st.session_state.wb_transforms = []
    st.session_state.wb_conditions = []
    st.session_state.wb_current_result = None
    st.session_state.wb_saved_models = []
    st.rerun()

if run_clicked:
    if not indep_vars:
        st.toast("Select at least one independent variable.", icon="⚠️")
    else:
        with st.spinner("Fitting model..."):
            # Apply transforms
            working_df = raw_df.copy()
            transform_warnings = []
            new_transform_cols = []
            if st.session_state.wb_transforms:
                working_df, new_transform_cols, transform_warnings = apply_transforms(
                    working_df, st.session_state.wb_transforms
                )

            # Apply subsample filters
            if st.session_state.wb_conditions:
                working_df = apply_subsample_filter(working_df, st.session_state.wb_conditions)

            if working_df.empty:
                st.error("No observations remain after applying filters. Relax restrictions.")
            else:
                # Build final IV list: user-selected + generated transform columns
                final_ivs = list(indep_vars) + new_transform_cols

                result = fit_model(
                    working_df, dep_var, final_ivs,
                    model_type=model_type, cov_type=cov_type,
                    quantile=quantile_val,
                )

                if "error" in result:
                    st.error(result["error"])
                else:
                    result["_transform_warnings"] = transform_warnings
                    st.session_state.wb_current_result = result
                    st.toast("Model fitted successfully!", icon="✅")

if save_clicked:
    res = st.session_state.wb_current_result
    if res is None:
        st.toast("Run a model first before saving.", icon="⚠️")
    elif len(st.session_state.wb_saved_models) >= 5:
        st.toast("Maximum 5 saved models. Clear some first.", icon="⚠️")
    else:
        st.session_state.wb_saved_models.append(res)
        st.toast(
            f"Saved as Model {len(st.session_state.wb_saved_models)}",
            icon="💾"
        )


# ==========================================================================
# RIGHT COLUMN — Results
# ==========================================================================
with col_right:
    result = st.session_state.wb_current_result

    if result is None:
        st.info(
            "Configure your model on the left and click **Run Model** to see results."
        )
    else:
        # Show transform warnings
        tw = result.get("_transform_warnings", [])
        for w in tw:
            st.warning(w)

        tab_coef, tab_diag, tab_post = st.tabs(
            ["Coefficients", "Diagnostics", "Post-Estimation"]
        )

        # ==================================================================
        # TAB: Coefficients
        # ==================================================================
        with tab_coef:
            # Metric cards
            r2 = result.get("r_squared", 0)
            r2_within = result.get("r_squared_within")
            adj_r2 = result.get("adj_r_squared")
            n_obs_val = result.get("n_obs", 0)
            n_firms_val = result.get("n_firms", 0)

            m1, m2, m3, m4 = st.columns(4)
            m1.metric("R-squared", f"{r2:.4f}")
            if r2_within is not None:
                m2.metric("Within R-sq", f"{r2_within:.4f}")
            elif adj_r2 is not None:
                m2.metric("Adj R-sq", f"{adj_r2:.4f}")
            else:
                m2.metric("Adj R-sq", "N/A")
            m3.metric("N obs", f"{n_obs_val:,}")
            m4.metric("N firms", f"{n_firms_val:,}")

            # Coefficient table
            coef_df = result.get("coef_table")
            if coef_df is not None and not coef_df.empty:
                formatted = format_coef_table(coef_df)
                st.dataframe(formatted, use_container_width=True, hide_index=True)

                # Coefficient bar chart (exclude constant)
                plot_df = coef_df[coef_df["Variable"] != "const"].copy()
                if not plot_df.empty:
                    plot_df["color"] = plot_df["Coefficient"].apply(
                        lambda x: PRIMARY if x >= 0 else ACCENT
                    )
                    plot_df["abs_coef"] = plot_df["Coefficient"].abs()

                    fig = go.Figure()
                    for _, row in plot_df.iterrows():
                        error_x_val = None
                        if "CI Lower" in coef_df.columns and "CI Upper" in coef_df.columns:
                            ci_lo = row.get("CI Lower")
                            ci_hi = row.get("CI Upper")
                            if pd.notna(ci_lo) and pd.notna(ci_hi):
                                error_x_val = dict(
                                    type="data",
                                    symmetric=False,
                                    array=[ci_hi - row["Coefficient"]],
                                    arrayminus=[row["Coefficient"] - ci_lo],
                                )
                        fig.add_trace(go.Bar(
                            y=[row["Variable"]],
                            x=[row["Coefficient"]],
                            orientation="h",
                            marker_color=PRIMARY if row["Coefficient"] >= 0 else ACCENT,
                            error_x=error_x_val,
                            showlegend=False,
                            hovertemplate=(
                                f"<b>{row['Variable']}</b><br>"
                                f"Coef: {row['Coefficient']:.4f}<br>"
                                f"p-value: {format_pvalue(row['p-value'])}"
                                "<extra></extra>"
                            ),
                        ))

                    fig.update_layout(
                        **plotly_layout("Coefficient Estimates", height=max(250, len(plot_df) * 40)),
                        yaxis=dict(autorange="reversed"),
                        xaxis_title="Coefficient",
                    )
                    fig.add_vline(x=0, line_dash="dash", line_color="gray", line_width=1)
                    st.plotly_chart(fig, use_container_width=True, config=PLOTLY_CONFIG)

            # Formula
            formula_str = result.get("formula_str", "")
            if formula_str:
                st.code(formula_str, language=None)

            # Collinearity warning
            try:
                result_obj = result.get("result_obj")
                if (
                    result_obj is not None
                    and hasattr(result_obj, "model")
                    and hasattr(result_obj.model, "exog")
                ):
                    exog_names = (
                        result_obj.model.exog_names
                        if hasattr(result_obj.model, "exog_names")
                        else [f"X{i}" for i in range(result_obj.model.exog.shape[1])]
                    )
                    X_df = pd.DataFrame(result_obj.model.exog, columns=exog_names)
                    vif_list = check_collinearity(X_df)
                    high_vif = [v for v in vif_list if v["warning"]]
                    if high_vif:
                        st.warning(
                            "**Collinearity Warning:** "
                            + ", ".join(
                                f"{v['variable']} (VIF={v['vif']:.1f})"
                                for v in high_vif
                            )
                            + ". Consider removing or combining correlated variables."
                        )
            except Exception:
                pass

            # Dynamic interpretation
            _render_coefficient_interpretation(result)

        # ==================================================================
        # TAB: Diagnostics
        # ==================================================================
        with tab_diag:
            residuals = result.get("residuals")
            fitted = result.get("fitted")

            if residuals is None or fitted is None:
                st.info("Diagnostic plots are not available for this model type.")
            else:
                resid_arr = np.asarray(residuals).flatten()
                fitted_arr = np.asarray(fitted).flatten()

                # Residuals vs Fitted
                fig_rvf = go.Figure()
                fig_rvf.add_trace(go.Scatter(
                    x=fitted_arr, y=resid_arr,
                    mode="markers",
                    marker=dict(color=PRIMARY, size=3, opacity=0.4),
                    showlegend=False,
                    hovertemplate="Fitted: %{x:.2f}<br>Residual: %{y:.2f}<extra></extra>",
                ))
                fig_rvf.add_hline(y=0, line_dash="dash", line_color="gray")
                fig_rvf.update_layout(
                    **plotly_layout("Residuals vs Fitted", height=350),
                    xaxis_title="Fitted Values",
                    yaxis_title="Residuals",
                )
                st.plotly_chart(fig_rvf, use_container_width=True, config=PLOTLY_CONFIG)

                diag_c1, diag_c2 = st.columns(2)

                # QQ Plot
                with diag_c1:
                    sorted_resid = np.sort(resid_arr[~np.isnan(resid_arr)])
                    n = len(sorted_resid)
                    if n > 0:
                        theoretical = stats.norm.ppf(
                            (np.arange(1, n + 1) - 0.5) / n
                        )
                        fig_qq = go.Figure()
                        fig_qq.add_trace(go.Scatter(
                            x=theoretical, y=sorted_resid,
                            mode="markers",
                            marker=dict(color=SECONDARY, size=3, opacity=0.5),
                            showlegend=False,
                        ))
                        # Reference line
                        qq_min = min(theoretical.min(), sorted_resid.min())
                        qq_max = max(theoretical.max(), sorted_resid.max())
                        fig_qq.add_trace(go.Scatter(
                            x=[qq_min, qq_max], y=[qq_min, qq_max],
                            mode="lines",
                            line=dict(color="gray", dash="dash"),
                            showlegend=False,
                        ))
                        fig_qq.update_layout(
                            **plotly_layout("Q-Q Plot", height=300),
                            xaxis_title="Theoretical Quantiles",
                            yaxis_title="Sample Quantiles",
                        )
                        st.plotly_chart(fig_qq, use_container_width=True, config=PLOTLY_CONFIG)

                # Residual Histogram
                with diag_c2:
                    fig_hist = go.Figure()
                    fig_hist.add_trace(go.Histogram(
                        x=resid_arr[~np.isnan(resid_arr)],
                        nbinsx=50,
                        marker_color=PRIMARY,
                        opacity=0.7,
                    ))
                    fig_hist.update_layout(
                        **plotly_layout("Residual Distribution", height=300),
                        xaxis_title="Residual",
                        yaxis_title="Frequency",
                    )
                    st.plotly_chart(fig_hist, use_container_width=True, config=PLOTLY_CONFIG)

                # VIF Table
                st.markdown("**Variance Inflation Factors (VIF)**")
                post = compute_post_estimation(result)
                vif_data = post.get("vif")
                if vif_data:
                    vif_df = pd.DataFrame(vif_data)
                    vif_df.columns = ["Variable", "VIF", "High (>10)"]

                    def _vif_style(row):
                        if row["High (>10)"]:
                            return ["background-color: #FEE2E2"] * len(row)
                        return [""] * len(row)

                    st.dataframe(
                        vif_df.style.apply(_vif_style, axis=1),
                        use_container_width=True, hide_index=True,
                    )
                else:
                    st.caption("VIF not available for this model type.")

        # ==================================================================
        # TAB: Post-Estimation
        # ==================================================================
        with tab_post:
            post = compute_post_estimation(result)

            # Predicted vs Actual
            pva = post.get("pred_vs_actual")
            if pva is not None and not pva.empty:
                fig_pva = go.Figure()
                fig_pva.add_trace(go.Scatter(
                    x=pva["Actual"], y=pva["Predicted"],
                    mode="markers",
                    marker=dict(color=PRIMARY, size=3, opacity=0.4),
                    showlegend=False,
                    hovertemplate="Actual: %{x:.2f}<br>Predicted: %{y:.2f}<extra></extra>",
                ))
                # 45-degree line
                pva_min = min(pva["Actual"].min(), pva["Predicted"].min())
                pva_max = max(pva["Actual"].max(), pva["Predicted"].max())
                fig_pva.add_trace(go.Scatter(
                    x=[pva_min, pva_max], y=[pva_min, pva_max],
                    mode="lines",
                    line=dict(color=ACCENT, dash="dash", width=2),
                    name="Perfect Prediction",
                ))
                fig_pva.update_layout(
                    **plotly_layout("Predicted vs Actual", height=380),
                    xaxis_title="Actual",
                    yaxis_title="Predicted",
                )
                st.plotly_chart(fig_pva, use_container_width=True, config=PLOTLY_CONFIG)
            else:
                st.caption("Predicted vs actual plot not available.")

            # Wald Test
            st.markdown("**Wald Test**")
            wald_c1, wald_c2 = st.columns([7, 3])
            with wald_c1:
                wald_str = st.text_input(
                    "Restriction",
                    placeholder="e.g. profitability = 0  or  profitability = tangibility",
                    key="wb_wald_str",
                )
            with wald_c2:
                wald_run = st.button("Test", key="wb_wald_run", use_container_width=True)

            if wald_run and wald_str.strip():
                wald_result = run_wald_test(result, wald_str.strip())
                if "error" in wald_result:
                    st.error(wald_result["error"])
                else:
                    wc1, wc2, wc3 = st.columns(3)
                    wc1.metric("Chi-sq", f"{wald_result['chi2']:.3f}")
                    wc2.metric("p-value", format_pvalue(wald_result["p_value"]))
                    wc3.metric("Verdict", wald_result["verdict"])

            # Download residuals
            st.markdown("---")
            resid = result.get("residuals")
            fitted_vals = result.get("fitted")
            if resid is not None and fitted_vals is not None:
                resid_df = pd.DataFrame({
                    "fitted": np.asarray(fitted_vals).flatten(),
                    "residual": np.asarray(resid).flatten(),
                })
                st.download_button(
                    "Download Residuals (CSV)",
                    resid_df.to_csv(index=False).encode("utf-8"),
                    file_name="workbench_residuals.csv",
                    mime="text/csv",
                    key="wb_dl_resid",
                )


# ==========================================================================
# BOTTOM — Model Comparison (esttab)
# ==========================================================================
if st.session_state.wb_saved_models:
    st.markdown("---")
    st.markdown("### Model Comparison (esttab)")
    st.caption(
        f"{len(st.session_state.wb_saved_models)} model(s) saved. "
        "Maximum 5."
    )

    comp_df = build_comparison_table(st.session_state.wb_saved_models)
    if not comp_df.empty:
        st.dataframe(comp_df, use_container_width=True, hide_index=True)

        dl_c1, dl_c2 = st.columns(2)
        with dl_c1:
            csv_str = export_comparison_csv(comp_df)
            st.download_button(
                "Export CSV",
                csv_str.encode("utf-8"),
                file_name="model_comparison.csv",
                mime="text/csv",
                key="wb_dl_csv",
            )
        with dl_c2:
            latex_str = export_latex(comp_df)
            st.download_button(
                "Export LaTeX",
                latex_str.encode("utf-8"),
                file_name="model_comparison.tex",
                mime="text/plain",
                key="wb_dl_latex",
            )
