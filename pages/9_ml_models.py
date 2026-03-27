"""
ML Models — Train, compare, and interpret RF/XGBoost/LightGBM models.
Panel-aware cross-validation with SHAP feature importance.
"""

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import numpy as np
import db
from helpers import (
    plotly_layout, format_pct, STAGE_COLORS, STAGE_ORDER,
    PRIMARY, SECONDARY, ACCENT, PLOTLY_CONFIG,
    interpret_ml_comparison, render_interpretation,
)
from models.base import DEFAULT_X_COLS
from models.ml_predict import (
    compare_all_models, get_feature_importance, get_shap_values,
    predict_leverage, get_stage_importance, cross_validate_model,
    _prepare_ml_data,
)

filters = st.session_state.filters
ft = db.filters_to_tuple(filters)

st.markdown("### ML Models")
st.caption("Train, compare, and interpret machine learning models for leverage prediction. Panel-aware cross-validation prevents data leakage.")

with st.expander("ℹ️ About these models — parameters & interpretation"):
    st.markdown("""
**Why Machine Learning for Capital Structure?**

Traditional econometrics (OLS, FE) assumes linear relationships: "profitability always reduces leverage by the same amount." In reality, capital structure decisions are **non-linear** — a firm with 5% profitability behaves very differently from one with 25%, and the effect of tangibility depends on firm size.

**Models and what they measure:**

| Model | What it captures in capital structure context |
|-------|----------------------------------------------|
| **Random Forest** | "Which combinations of firm characteristics lead to high/low leverage?" — Captures interaction effects (e.g., profitability matters more for small firms than large ones) |
| **XGBoost** | "What is the most accurate leverage prediction given all determinants?" — Best for identifying which firms are over/under-leveraged relative to their characteristics |
| **LightGBM** | "Same as XGBoost but faster" — Ideal for real-time what-if analysis and bulk screening |

**What intelligence ML provides that econometrics cannot:**
1. **Non-linear effects:** "The profitability-leverage relationship reverses at tangibility > 60%"
2. **Feature importance by stage:** "For Growth firms, collateral matters most; for Mature firms, earnings retention dominates"
3. **Anomaly detection:** "This firm's predicted leverage is 20% but actual is 55% — investigate over-leveraging"
4. **SHAP explanations:** "For THIS specific firm, profitability reduces predicted leverage by 8pp while tangibility adds 12pp"

**Overfitting guard:** With 401 firms, we use panel-aware cross-validation (split by firm, not row), conservative hyperparameters, and always compare against OLS baseline. If ML isn't meaningfully better, the simpler model wins.
""")

# ── Variable selection (shared across tabs) ──
all_predictors = [
    "profitability", "tangibility", "tax", "log_size", "tax_shield", "dividend",
    "interest", "cash_holdings", "promoter_share", "non_promoters",
]

with st.sidebar:
    st.markdown("**ML Features**")
    selected_x = st.multiselect(
        "Predictors",
        options=all_predictors,
        default=DEFAULT_X_COLS,
        key="ml_features",
    )
    if not selected_x:
        selected_x = DEFAULT_X_COLS

# ── Load data ──
panel_df = db.get_panel_data(ft)
if panel_df.empty or len(panel_df) < 100:
    st.warning("Not enough data. Adjust filters (need 100+ observations).")
    st.stop()

n_firms = panel_df["company_code"].nunique()
st.caption(f"Panel: {n_firms} firms, {len(panel_df):,} obs")

# ── Tabs ──
tab1, tab2, tab3 = st.tabs(["Train & Compare", "Feature Importance", "Predict"])

# ═══════════════════════════════════════════════
# TAB 1: Train & Compare
# ═══════════════════════════════════════════════
with tab1:
    st.markdown("#### Model Comparison")
    st.caption("5-fold panel-aware cross-validation (split by firm, not by row)")

    if "ml_results" not in st.session_state:
        st.session_state.ml_results = None
        st.session_state.ml_comparison = None

    # Pre-training guidance
    if st.session_state.ml_results is None:
        st.markdown("""
**How this works:**

1. Click **Train All Models** below to train 3 ML models (Random Forest, XGBoost, LightGBM) on the current dataset
2. Each model is cross-validated using 5-fold panel-aware splits (firms are never in both train and test)
3. After training (~15-20 seconds), you'll see:
   - **Comparison table** — RMSE, R-squared, and training time for each model
   - **Best model highlighted** with recommendation
   - **Actual vs Predicted scatter** — how well predictions match reality
   - **Dynamic interpretation** — what the results mean for capital structure decisions

Then explore the other tabs:
- **Feature Importance** — which determinants drive leverage for each life stage
- **Predict** — adjust sliders to get multi-model leverage predictions for any firm profile
""")

        st.markdown(f"**Current features:** {', '.join(selected_x)}")
        st.caption("Change features in the sidebar under 'ML Features'")

    col_btn, col_info = st.columns([1, 3])
    with col_btn:
        train_clicked = st.button("Train All Models", type="primary", use_container_width=True)

    if train_clicked:
        progress = st.progress(0, text="Starting...")
        def update_progress(pct, text):
            progress.progress(pct, text=text)

        results, comparison = compare_all_models(
            panel_df, x_cols=selected_x, progress_callback=update_progress
        )
        st.session_state.ml_results = results
        st.session_state.ml_comparison = comparison
        progress.empty()
        st.toast("Models trained successfully!", icon="✅")

    if st.session_state.ml_comparison is not None:
        comparison = st.session_state.ml_comparison
        results = st.session_state.ml_results

        # Highlight best model
        best_name = comparison.iloc[0]["Model"]

        # Results table
        st.dataframe(
            comparison,
            hide_index=True,
            use_container_width=True,
            column_config={
                "R-squared": st.column_config.ProgressColumn("R-squared", min_value=0, max_value=1, format="%.4f"),
                "RMSE": st.column_config.NumberColumn("RMSE", format="%.2f"),
            },
        )
        st.success(f"**Best model: {best_name}** (R² = {comparison.iloc[0]['R-squared']:.4f})")

        # Comparison bar chart
        cc1, cc2 = st.columns(2)
        with cc1:
            fig_r2 = px.bar(
                comparison, x="Model", y="R-squared",
                color="Model",
                color_discrete_map={"XGBoost": PRIMARY, "LightGBM": SECONDARY, "Random Forest": ACCENT},
                labels={"R-squared": "Cross-Validated R²"},
            )
            fig_r2.update_layout(**plotly_layout("Model R² Comparison", height=350))
            fig_r2.update_layout(showlegend=False)
            st.plotly_chart(fig_r2, use_container_width=True, config=PLOTLY_CONFIG)

        with cc2:
            fig_rmse = px.bar(
                comparison, x="Model", y="RMSE",
                color="Model",
                color_discrete_map={"XGBoost": PRIMARY, "LightGBM": SECONDARY, "Random Forest": ACCENT},
            )
            fig_rmse.update_layout(**plotly_layout("Model RMSE Comparison", height=350))
            fig_rmse.update_layout(showlegend=False)
            st.plotly_chart(fig_rmse, use_container_width=True, config=PLOTLY_CONFIG)

        # Actual vs Predicted scatter for best model
        st.markdown(f"#### Actual vs Predicted ({best_name})")
        best_result = results[0]
        mask = ~np.isnan(best_result["predictions"])
        fig_ap = px.scatter(
            x=best_result["actuals"][mask],
            y=best_result["predictions"][mask],
            opacity=0.3,
            labels={"x": "Actual Leverage (%)", "y": "Predicted Leverage (%)"},
        )
        fig_ap.add_trace(go.Scatter(
            x=[0, 80], y=[0, 80], mode="lines",
            line=dict(dash="dash", color="#9CA3AF"), showlegend=False,
        ))
        fig_ap.update_layout(**plotly_layout(height=400))
        st.plotly_chart(fig_ap, use_container_width=True, config=PLOTLY_CONFIG)

        # Warning for low R²
        if comparison.iloc[0]["R-squared"] < 0.15:
            st.warning("All models explain less than 15% of variance. Use results directionally, not for point predictions.")

        # Dynamic interpretation
        st.divider()
        ml_insights, ml_actions = interpret_ml_comparison(comparison)
        render_interpretation(ml_insights, ml_actions, title="Results Interpretation & Call to Action")

    else:
        if st.session_state.ml_results is None:
            pass  # Guidance already shown above the button

# ═══════════════════════════════════════════════
# TAB 2: Feature Importance
# ═══════════════════════════════════════════════
with tab2:
    st.markdown("#### Feature Importance Analysis")

    if st.session_state.ml_results is not None:
        results = st.session_state.ml_results

        # Model selector
        model_names = [r["model_name"] for r in results]
        sel_model = st.selectbox("Select model", model_names, index=0)
        sel_result = next(r for r in results if r["model_name"] == sel_model)

        # Native feature importance
        imp_df = get_feature_importance(sel_result["model"], sel_result["feature_names"])

        fi1, fi2 = st.columns([1, 1])
        with fi1:
            st.markdown(f"**{sel_model} — Feature Importance**")
            fig_imp = px.bar(
                imp_df, x="Importance_Pct", y="Feature",
                orientation="h",
                labels={"Importance_Pct": "Importance (%)", "Feature": ""},
                color="Importance_Pct",
                color_continuous_scale=["#E5E7EB", PRIMARY],
            )
            fig_imp.update_layout(**plotly_layout(height=350))
            fig_imp.update_layout(showlegend=False, coloraxis_showscale=False)
            st.plotly_chart(fig_imp, use_container_width=True, config=PLOTLY_CONFIG)

        with fi2:
            # SHAP values
            st.markdown(f"**SHAP Analysis**")
            X, _, fnames, _ = _prepare_ml_data(panel_df, x_cols=selected_x)
            shap_df, _ = get_shap_values(sel_result["model"], X, fnames)
            if "Mean |SHAP|" in shap_df.columns:
                fig_shap = px.bar(
                    shap_df, x="Mean |SHAP|", y="Feature",
                    orientation="h",
                    labels={"Mean |SHAP|": "Mean |SHAP value|", "Feature": ""},
                    color="Mean |SHAP|",
                    color_continuous_scale=["#E5E7EB", ACCENT],
                )
                fig_shap.update_layout(**plotly_layout(height=350))
                fig_shap.update_layout(showlegend=False, coloraxis_showscale=False)
                st.plotly_chart(fig_shap, use_container_width=True, config=PLOTLY_CONFIG)
            else:
                st.caption("SHAP not available — showing native importance")

        # Stage-specific importance
        st.divider()
        st.markdown("#### Feature Importance by Life Stage")
        st.caption("How do determinant effects differ across corporate life stages?")

        with st.spinner("Training stage-specific models..."):
            stage_imp = get_stage_importance(panel_df, sel_model, selected_x)

        if stage_imp:
            # Build a combined DataFrame for heatmap
            heatmap_data = []
            for stage, imp in stage_imp.items():
                for _, row in imp.iterrows():
                    heatmap_data.append({
                        "Stage": stage, "Feature": row["Feature"],
                        "Importance": row["Importance_Pct"],
                    })
            heat_df = pd.DataFrame(heatmap_data)

            if not heat_df.empty:
                pivot = heat_df.pivot(index="Feature", columns="Stage", values="Importance").fillna(0)
                # Order stages
                stage_order = [s for s in STAGE_ORDER if s in pivot.columns]
                pivot = pivot[stage_order]

                fig_heat = px.imshow(
                    pivot.values,
                    x=pivot.columns.tolist(),
                    y=pivot.index.tolist(),
                    color_continuous_scale=["#F8FAFC", PRIMARY, "#065F46"],
                    aspect="auto",
                    labels={"color": "Importance (%)"},
                )
                fig_heat.update_layout(**plotly_layout("Feature Importance Heatmap by Stage", height=400))
                st.plotly_chart(fig_heat, use_container_width=True, config=PLOTLY_CONFIG)

                # Auto-generated insight
                st.markdown("**Key Insights:**")
                for stage in stage_order:
                    if stage in stage_imp:
                        top_feat = stage_imp[stage].iloc[0]
                        st.markdown(f"- **{stage}**: Top predictor is **{top_feat['Feature']}** ({top_feat['Importance_Pct']}%)")
        else:
            st.info("Not enough data per stage for stage-specific analysis.")

    else:
        st.info("Train models in the **Train & Compare** tab first.")

# ═══════════════════════════════════════════════
# TAB 3: Predict
# ═══════════════════════════════════════════════
with tab3:
    st.markdown("#### Multi-Model Prediction")
    st.caption("Adjust firm characteristics and see predictions from all trained models simultaneously.")

    if st.session_state.ml_results is not None:
        results = st.session_state.ml_results

        # Get sample means for defaults
        means = panel_df[selected_x].mean()

        # Sliders
        sc1, sc2, sc3 = st.columns(3)
        slider_vals = {}
        for i, col in enumerate(selected_x):
            container = [sc1, sc2, sc3][i % 3]
            col_mean = float(means.get(col, 0))
            col_min = float(panel_df[col].quantile(0.05)) if col in panel_df else 0.0
            col_max = float(panel_df[col].quantile(0.95)) if col in panel_df else 100.0
            if np.isnan(col_mean):
                col_mean = 0.0
            if np.isnan(col_min):
                col_min = -50.0
            if np.isnan(col_max):
                col_max = 100.0
            with container:
                slider_vals[col] = st.slider(
                    col.replace("_", " ").title(),
                    min_value=float(col_min),
                    max_value=float(col_max),
                    value=float(col_mean),
                    step=0.5,
                    key=f"ml_slider_{col}",
                )

        feature_values = [slider_vals[c] for c in selected_x]

        st.divider()

        # Predictions from all models
        st.markdown("#### Predictions")
        pred_cols = st.columns(len(results))
        predictions = {}
        for i, result in enumerate(results):
            pred = predict_leverage(result["model"], feature_values, selected_x)
            predictions[result["model_name"]] = pred
            with pred_cols[i]:
                is_best = i == 0
                st.metric(
                    result["model_name"] + (" ★" if is_best else ""),
                    format_pct(pred),
                )

        # Compare with real company
        st.divider()
        st.markdown("#### Compare with Real Company")
        companies_df = db.get_companies()
        comp_name = st.selectbox("Select company", companies_df["company_name"].tolist(), index=0, key="ml_compare")
        comp_code = int(companies_df[companies_df["company_name"] == comp_name]["company_code"].iloc[0])
        comp_df = db.get_company_detail(comp_code)

        if not comp_df.empty:
            actual = comp_df["leverage"].mean()
            cmp1, cmp2, cmp3 = st.columns(3)
            with cmp1:
                best_pred = list(predictions.values())[0]
                st.metric("Best Model Prediction", format_pct(best_pred))
            with cmp2:
                st.metric(f"Actual ({comp_name})", format_pct(actual))
            with cmp3:
                diff = best_pred - actual
                st.metric("Difference", f"{diff:+.1f}pp",
                          delta="Over-predicted" if diff > 0 else "Under-predicted")
    else:
        st.info("Train models in the **Train & Compare** tab first.")
