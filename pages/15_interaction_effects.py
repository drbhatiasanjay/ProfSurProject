"""
Interaction Effects — Profitability × Tangibility and Stage Moderation.

Two complementary analyses:
  Tab 1 — Cross-Term: Profitability × Tangibility as a single interaction predictor
           in the base leverage regression. Tests whether the joint effect is more than additive.
  Tab 2 — Stage Moderation: Stage-dummy × profitability and stage-dummy × tangibility terms
           in one pooled model to reveal per-stage marginal effects.

Pinned to Thesis panel (2001–2024) for reproducibility.
"""

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import numpy as np
import db
from helpers import (
    plotly_layout, format_pvalue, format_coef_table,
    ensure_session_state, panel_label,
    STAGE_COLORS, STAGE_ORDER, PRIMARY, SECONDARY, ACCENT, PLOTLY_CONFIG,
    render_interpretation, new_badge, df_download_button, chart_download_button,
)
from models.interaction import run_cross_term_ols, simple_slopes, run_stage_moderation_ols

ensure_session_state()
db.log_page_visit("Interaction Effects")

# Pin to thesis panel for reproducibility — matches the approach used on pages 8, 9, 10, 13.
_PANEL = "thesis"
st.session_state.panel_mode = _PANEL

filters = st.session_state.filters
ft = db.filters_to_tuple(filters)

st.markdown(f"### Interaction Effects {new_badge()}", unsafe_allow_html=True)
st.caption(
    "Tests whether profitability and tangibility jointly shape leverage (cross-term model) "
    "and whether life stage moderates each variable's marginal effect on leverage (stage moderation). "
    f" · {panel_label(_PANEL)}"
)

with st.expander("About these analyses"):
    st.markdown("""
**Cross-Term Model** augments the base OLS with a Profitability × Tangibility interaction term.
Both variables are mean-centred before multiplication so that the main-effect coefficients
remain interpretable at the sample mean and multicollinearity is reduced.

- **H₀**: β(Prof × Tang) = 0 — the joint effect is purely additive.
- If β₃ < 0: firms that are *both* highly profitable *and* highly tangible reduce leverage more
  than either characteristic alone predicts — consistent with Pecking Order and Trade-Off theories
  operating simultaneously.
- The **Simple Slopes Plot** shows predicted leverage vs profitability at three tangibility levels
  (mean − 1SD, mean, mean + 1SD). Diverging lines signal a real interaction; parallel lines signal
  additivity.

**Stage Moderation Model** includes stage-dummy × profitability and stage-dummy × tangibility
interaction terms in one pooled regression (reference stage: **Maturity**).

- Marginal effect of profitability at stage k = β(profitability) + β(Stage_k × profitability)
- Standard errors computed via the delta method:
  Var(β + γₖ) = Var(β) + Var(γₖ) + 2·Cov(β, γₖ)
- The **Heatmap** shows marginal effects across all 8 stages for both variables.
""")

try:
    with st.spinner("Loading..."):
        panel_df = db.get_active_panel_data(ft)
except Exception as _e:
    st.error(f"Failed to load data. Please refresh. ({_e})")
    st.stop()
if panel_df.empty:
    st.warning("No data. Adjust sidebar filters.")
    st.stop()

tab_cross, tab_stage = st.tabs([
    "Cross-Term (Prof × Tang)",
    "Stage Moderation",
])


# ══════════════════════════════════════════════════════════════════════════════
# TAB 1 — Cross-Term Model
# ══════════════════════════════════════════════════════════════════════════════
with tab_cross:
    st.subheader("Cross-Term Model: Profitability × Tangibility")
    st.caption(
        "Does tangibility amplify or dampen the effect of profitability on leverage? "
        "Variables are mean-centred; HC1 robust standard errors."
    )

    with st.expander("Advanced options", expanded=False):
        st.markdown("**Interaction specification**")
        st.caption(
            "This model regresses leverage on: Profitability (mean-centred), "
            "Tangibility (mean-centred), their cross-term (Prof x Tang), and the "
            "base controls (log_size, tax_shield, dividend). Mean-centring is always "
            "applied to reduce multicollinearity and keep main-effect coefficients "
            "interpretable at the sample mean."
        )
        st.info(
            "Cross-term interaction: Profitability x Tangibility (fixed specification — "
            "see Stage Moderation tab for per-stage marginal effects).",
            icon="ℹ️",
        )

    if st.button("Run Cross-Term OLS", type="primary", key="run_cross"):
        with st.spinner("Fitting cross-term model…"):
            ct = run_cross_term_ols(panel_df)

        # ── Metrics ──────────────────────────────────────────────────────────
        mc1, mc2, mc3, mc4 = st.columns(4)
        mc1.metric("R²", f"{ct['r_squared']:.4f}")
        mc2.metric("Adj R²", f"{ct['adj_r_squared']:.4f}")
        mc3.metric("Observations", f"{ct['n_obs']:,}")
        mc4.metric("Firms", f"{ct['n_firms']:,}")
        st.caption(f"F-stat = {ct['f_stat']:.2f},  p = {format_pvalue(ct['f_pvalue'])}")

        # ── Coefficient Table ─────────────────────────────────────────────────
        st.markdown("#### Coefficient Estimates (HC1 Robust SEs)")
        _ct_formatted = format_coef_table(ct["coef_table"])
        st.dataframe(
            _ct_formatted,
            use_container_width=True,
            hide_index=True,
        )
        df_download_button(_ct_formatted, "cross_term_coefficients.csv")

        # ── Simple Slopes Plot ────────────────────────────────────────────────
        st.markdown("#### Simple Slopes Plot")
        st.caption(
            "Predicted leverage vs profitability at three tangibility levels "
            "(controls fixed at sample means)."
        )

        slopes_df = simple_slopes(ct)
        color_map = {
            "Low (mean−1SD)": ACCENT,
            "Mean": PRIMARY,
            "High (mean+1SD)": SECONDARY,
        }
        fig_ss = go.Figure()
        for level, color in color_map.items():
            sub = slopes_df[slopes_df["tang_level"] == level]
            fig_ss.add_trace(go.Scatter(
                x=sub["profitability"],
                y=sub["predicted_leverage"],
                mode="lines",
                name=level,
                line=dict(color=color, width=2.5),
            ))
        layout_ss = plotly_layout(
            "Predicted Leverage by Profitability (Simple Slopes)", height=420
        )
        layout_ss.update({
            "xaxis_title": "Profitability (%)",
            "yaxis_title": "Predicted Leverage (%)",
            "legend": {"title": "Tangibility Level", "orientation": "h",
                       "yanchor": "bottom", "y": 1.02, "xanchor": "right", "x": 1},
        })
        fig_ss.update_layout(**layout_ss)
        st.plotly_chart(fig_ss, use_container_width=True, config=PLOTLY_CONFIG)
        chart_download_button(fig_ss, "cross_term_simple_slopes.png")

        # ── Interpretation ────────────────────────────────────────────────────
        int_row = ct["coef_table"][
            ct["coef_table"]["Variable"] == "Profitability × Tangibility"
        ]
        insights, actions = [], [
            "Check if the simple-slope lines diverge (interaction present) or are parallel (additive).",
            "Compare β₃ significance across Thesis vs Latest panels for robustness.",
            "A significant negative β₃ supports simultaneous operation of Pecking Order and Trade-Off theories.",
        ]
        if not int_row.empty:
            b3 = float(int_row.iloc[0]["Coefficient"])
            p3 = float(int_row.iloc[0]["p-value"])
            direction = "negative" if b3 < 0 else "positive"
            sig_label = "statistically significant" if p3 < 0.10 else "not statistically significant"
            insights.append(
                f"The interaction coefficient β₃ = **{b3:.4f}** is {direction} and {sig_label} "
                f"(p = {format_pvalue(p3)})."
            )
            if b3 < 0 and p3 < 0.10:
                insights.append(
                    "Firms that are both highly profitable and asset-rich reduce leverage more aggressively "
                    "than either characteristic alone predicts — Pecking Order and Trade-Off theories reinforce each other."
                )
            elif b3 > 0 and p3 < 0.10:
                insights.append(
                    "High tangibility amplifies the positive leverage effect when profitability rises — "
                    "collateral-driven borrowing dominates the retained-earnings (Pecking Order) channel for asset-rich firms."
                )
            else:
                insights.append(
                    "A non-significant interaction suggests the effects of profitability and tangibility on leverage "
                    "are additive in this panel — no amplification or dampening between the two variables."
                )

        render_interpretation(insights, actions, title="Cross-Term Interpretation")


# ══════════════════════════════════════════════════════════════════════════════
# TAB 2 — Stage Moderation Model
# ══════════════════════════════════════════════════════════════════════════════
with tab_stage:
    st.subheader("Stage Moderation Model")
    st.caption(
        "Do the marginal effects of profitability and tangibility on leverage vary across life stages? "
        "Reference stage: **Maturity**. HC1 robust SEs; delta-method marginal-effect SEs."
    )

    if st.button("Run Stage Moderation OLS", type="primary", key="run_stage_mod"):
        with st.spinner("Fitting stage moderation model…"):
            sm_res = run_stage_moderation_ols(panel_df)

        # ── Metrics ──────────────────────────────────────────────────────────
        mc1, mc2, mc3, mc4 = st.columns(4)
        mc1.metric("R²", f"{sm_res['r_squared']:.4f}")
        mc2.metric("Adj R²", f"{sm_res['adj_r_squared']:.4f}")
        mc3.metric("Observations", f"{sm_res['n_obs']:,}")
        mc4.metric("Firms", f"{sm_res['n_firms']:,}")
        st.caption(f"F-stat = {sm_res['f_stat']:.2f},  p = {format_pvalue(sm_res['f_pvalue'])}")

        # ── Full Coefficient Table (collapsible) ──────────────────────────────
        with st.expander("Full Coefficient Table (all interaction terms)"):
            _sm_ct_formatted = format_coef_table(sm_res["coef_table"])
            st.dataframe(
                _sm_ct_formatted,
                use_container_width=True,
                hide_index=True,
            )
            df_download_button(_sm_ct_formatted, "stage_moderation_coefficients.csv")

        # ── Marginal Effects Heatmap ──────────────────────────────────────────
        st.markdown("#### Marginal Effects Heatmap")
        st.caption(
            "Each cell = dLeverage/dVariable at that life stage. "
            "Significance: *** p<0.01, ** p<0.05, * p<0.1"
        )

        mdf = sm_res["marginal_df"]
        pivot_me = mdf.pivot(index="stage", columns="variable", values="marginal_effect")
        pivot_sig = mdf.pivot(index="stage", columns="variable", values="sig")

        # Reorder rows to canonical stage order
        ordered_stages = [s for s in STAGE_ORDER if s in pivot_me.index]
        pivot_me = pivot_me.reindex(ordered_stages)
        pivot_sig = pivot_sig.reindex(ordered_stages)

        # Build annotation text: value + significance stars
        annot_text = []
        for r in pivot_me.index:
            row_ann = []
            for c in pivot_me.columns:
                val = pivot_me.loc[r, c]
                sig = pivot_sig.loc[r, c] if pd.notna(pivot_sig.loc[r, c]) else ""
                row_ann.append(f"{val:.3f}{sig}")
            annot_text.append(row_ann)

        fig_hm = px.imshow(
            pivot_me,
            color_continuous_scale="RdYlGn",
            color_continuous_midpoint=0,
            aspect="auto",
            labels={"color": "Marginal Effect"},
        )
        # Overlay annotation text
        for i, row_idx in enumerate(pivot_me.index):
            for j, col_idx in enumerate(pivot_me.columns):
                fig_hm.add_annotation(
                    x=j, y=i,
                    text=annot_text[i][j],
                    showarrow=False,
                    font=dict(size=12, color="black"),
                )
        layout_hm = plotly_layout("Marginal Effects of Profitability & Tangibility by Life Stage", height=400)
        fig_hm.update_layout(**layout_hm)
        st.plotly_chart(fig_hm, use_container_width=True, config=PLOTLY_CONFIG)
        chart_download_button(fig_hm, "stage_moderation_heatmap.png")
        df_download_button(mdf, "stage_moderation_marginal_effects.csv")

        # ── Per-variable bar charts ───────────────────────────────────────────
        for var_name in ["Profitability", "Tangibility"]:
            sub = (
                mdf[mdf["variable"] == var_name]
                .set_index("stage")
                .reindex([s for s in STAGE_ORDER if s in mdf["stage"].values])
                .reset_index()
            )
            error_bars = (1.96 * sub["se"]).tolist()
            colors = [STAGE_COLORS.get(s, PRIMARY) for s in sub["stage"]]
            text_labels = [
                f"{me:.3f}{sig}"
                for me, sig in zip(sub["marginal_effect"], sub["sig"])
            ]

            fig_bar = go.Figure()
            fig_bar.add_trace(go.Bar(
                x=sub["stage"],
                y=sub["marginal_effect"],
                error_y=dict(type="data", array=error_bars, visible=True, color="#6B7280"),
                marker_color=colors,
                text=text_labels,
                textposition="outside",
                name=var_name,
            ))
            fig_bar.add_hline(y=0, line_dash="dot", line_color="#9CA3AF", line_width=1)

            layout_bar = plotly_layout(
                f"Marginal Effect of {var_name} on Leverage by Life Stage", height=400
            )
            layout_bar.update({
                "xaxis_title": "Life Stage",
                "yaxis_title": f"dLeverage / d{var_name}",
                "showlegend": False,
            })
            fig_bar.update_layout(**layout_bar)
            st.plotly_chart(fig_bar, use_container_width=True, config=PLOTLY_CONFIG)
            chart_download_button(fig_bar, f"marginal_effect_{var_name.lower()}_by_stage.png")

        # ── Interpretation ────────────────────────────────────────────────────
        prof_df = mdf[mdf["variable"] == "Profitability"]
        tang_df = mdf[mdf["variable"] == "Tangibility"]

        sig_prof = prof_df[prof_df["pval"] < 0.10]["stage"].tolist()
        sig_tang = tang_df[tang_df["pval"] < 0.10]["stage"].tolist()

        insights, actions = [], [
            "Stages where the marginal effect switches sign indicate competing theories (Trade-off vs Pecking Order).",
            "Compare with the per-stage OLS results on page 13 (Advanced Econometrics) for consistency.",
            "Use the heatmap to identify which stages are most sensitive to changes in capital structure determinants.",
        ]

        if sig_prof:
            insights.append(
                f"Profitability has a statistically significant marginal effect on leverage at: "
                f"**{', '.join(sig_prof)}** (p < 0.10)."
            )
        else:
            insights.append("No stage shows a statistically significant marginal effect of profitability at p < 0.10.")

        if sig_tang:
            insights.append(
                f"Tangibility has a statistically significant marginal effect on leverage at: "
                f"**{', '.join(sig_tang)}** (p < 0.10)."
            )
        else:
            insights.append("No stage shows a statistically significant marginal effect of tangibility at p < 0.10.")

        # Sign reversal check — profitability
        neg_prof = prof_df[prof_df["marginal_effect"] < 0]["stage"].tolist()
        pos_prof = prof_df[prof_df["marginal_effect"] > 0]["stage"].tolist()
        if neg_prof and pos_prof:
            insights.append(
                f"Profitability shows a **sign reversal** across stages: "
                f"negative at {', '.join(neg_prof)} and positive at {', '.join(pos_prof)}. "
                "This suggests Pecking Order dominates in some stages while Trade-off dominates in others."
            )

        # Sign reversal check — tangibility
        neg_tang = tang_df[tang_df["marginal_effect"] < 0]["stage"].tolist()
        pos_tang = tang_df[tang_df["marginal_effect"] > 0]["stage"].tolist()
        if neg_tang and pos_tang:
            insights.append(
                f"Tangibility shows a **sign reversal** across stages: "
                f"negative at {', '.join(neg_tang)} and positive at {', '.join(pos_tang)}."
            )

        render_interpretation(insights, actions, title="Stage Moderation Interpretation")
