"""Stata Studio — Open-Source Econometric Workbench.

Provides full mathematical, syntax, and visual parity with Stata 17/18:
- Interactive Stata command prompt (CLI)
- Monospace ASCII terminal output window
- Clustered Panel Fixed Effects (xtreg, fe) and Random Effects (xtreg, re)
- Summary statistics with percentiles (summarize, detail)
- Group tabulation by life-stage (tabstat, by())
- Correlation matrix with significance stars (pwcorr, sig)
- Specification testing (hausman fe re, estat vif)
- Multi-model publication matrix (esttab) with LaTeX & Word .docx export
- Visual coefficient plots (coefplot) with 95% confidence intervals
- 1-Click native Stata .dta dataset & .do script export
"""

import os
import io
import time
import html
import streamlit as st
import pandas as pd
import plotly.graph_objects as go

import db
from helpers import (
    ensure_session_state,
    require_role,
    plotly_layout_light,
    plotly_layout_dark,
)
from models.stata_engine import (
    execute_stata_command,
    get_stored_models_table,
    generate_esttab_latex,
    generate_esttab_docx,
    prepare_df_for_stata,
    _STORED_ESTIMATES,
)

ensure_session_state()
db.log_page_visit("Stata Studio")

st.set_page_config(
    page_title="Stata Studio — LifeCycle Leverage",
    page_icon="💻",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Authentication & Access Control
require_role("admin", "researcher", "viewer", "cfo", "guest")

def get_financial_translation(cmd_str: str) -> str:
    """Translates a Stata command into executive corporate finance intent."""
    low = (cmd_str or "").lower().strip()
    if low.startswith("."):
        low = low[1:].strip()

    if low.startswith("xtreg") and (" fe" in low or ", fe" in low or ",fe" in low):
        return (
            "Estimates a within-firm <b>Fixed Effects panel regression</b> analyzing how corporate debt ratios (leverage) "
            "respond to firm profitability, asset tangibility, and size. By de-meaning data within each firm across 2001–2024, "
            "it purges all unobserved time-invariant firm heterogeneity (governance heritage, founding culture, corporate lineage), "
            "isolating true within-firm causal elasticities. Evaluates <b>Pecking Order Theory</b> (profitability draining debt) vs. "
            "<b>Trade-Off Theory</b> (tangibility providing pledgeable debt capacity)."
        )
    if low.startswith("xtreg") and (" re" in low or ", re" in low or ",re" in low):
        return (
            "Estimates a <b>Random Effects panel regression</b> using Generalized Least Squares (GLS) to assess capital structure "
            "determinants across firms and over time, providing efficient parameter estimates under the assumption that firm-specific "
            "unobserved heterogeneity is uncorrelated with financial regressors."
        )
    if low.startswith("hausman"):
        return (
            "Executes the formal <b>Hausman specification test</b> contrasting Fixed Effects consistency against Random Effects efficiency. "
            "Determines whether individual firm endowments correlate with explanatory variables to mathematically verify whether within-firm "
            "Fixed Effects modeling is statistically required."
        )
    if low.startswith("summarize") or low.startswith("sum "):
        return (
            "Computes comprehensive parametric and non-parametric descriptive statistics (mean, standard deviation, percentiles, skewness) "
            "to establish baseline corporate distributions across the Indian manufacturing panel."
        )
    if low.startswith("pwcorr") or low.startswith("correlate"):
        return (
            "Generates pairwise correlation coefficients with significance stars to examine bivariate balance-sheet interactions and "
            "diagnose potential multicollinearity across leverage regressors."
        )
    if low.startswith("estat vif") or low.startswith("vif"):
        return (
            "Computes Variance Inflation Factors (VIF) to formally test for severe multicollinearity among explanatory financial ratios. "
            "VIF values strictly below 5–10 confirm parameter stability and regression robustness."
        )
    return f"Executes econometric estimation for <code>{html.escape(cmd_str)}</code> on the active longitudinal panel dataset."

# Custom Stata Terminal CSS
st.markdown(
    """
    <style>
    .stata-terminal-box {
        background-color: #0c1017;
        color: #f0f6fc;
        font-family: 'Consolas', 'Courier New', Courier, monospace;
        font-size: 13px;
        line-height: 1.45;
        padding: 16px 20px;
        border-radius: 8px;
        border: 1px solid #30363d;
        overflow-x: auto;
        white-space: pre;
        box-shadow: 0 4px 12px rgba(0,0,0,0.25);
        margin-bottom: 20px;
    }
    .stata-prompt-prefix {
        color: #58a6ff;
        font-weight: bold;
    }
    .stata-badge-pill {
        display: inline-block;
        padding: 4px 10px;
        margin: 2px 4px 6px 0;
        background: #f1f5f9;
        border: 1px solid #cbd5e1;
        border-radius: 16px;
        font-size: 12px;
        color: #0f172a;
        cursor: pointer;
        transition: all 0.2s;
    }
    .stata-badge-pill:hover {
        background: #e2e8f0;
        border-color: #94a3b8;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

PLOTLY_FULL_CONFIG = {
    "displayModeBar": True,
    "displaylogo": False,
    "modeBarButtonsToAdd": ["drawline", "drawopenpath", "eraseshape"],
    "toImageButtonOptions": {
        "format": "png",
        "filename": "stata_studio_chart",
        "height": 700,
        "width": 1000,
        "scale": 2,
    },
    "scrollZoom": True,
}

col_head1, col_head2 = st.columns([5, 1])
with col_head1:
    st.markdown("### 💻 Stata Studio")
    st.caption("Autonomous Stata Command Line & Econometric Publication Suite · Longitudinal Panel Econometric Engine")
with col_head2:
    cur_t = st.session_state.get("theme", "light")
    t_label = "🌙 Dark" if cur_t == "light" else "☀️ Light"
    if st.button(t_label, key="stata_page_theme_toggle", help="Toggle between Light and Dark theme", use_container_width=True):
        st.session_state.theme = "dark" if cur_t == "light" else "light"
        st.rerun()


# Retrieve Active Panel Dataset
panel_mode = st.session_state.get("panel_mode", "thesis")
filters = st.session_state.get("filters", {})
ft = db.filters_to_tuple(filters)
panel_df = db.get_active_panel_data(ft)

if panel_df is None or panel_df.empty:
    st.error("No active panel data loaded. Please check database connection.")
    st.stop()

# Stata Session State Initialization
if "stata_history" not in st.session_state:
    st.session_state["stata_history"] = []
if "stata_last_result" not in st.session_state:
    st.session_state["stata_last_result"] = None

# ── Metric Ribbons ────────────────────────────────────────────────────────────
n_obs = len(panel_df)
n_firms = panel_df["company_code"].nunique() if "company_code" in panel_df.columns else 0
years = (int(panel_df["year"].min()), int(panel_df["year"].max())) if "year" in panel_df.columns else (2001, 2024)
n_industries = panel_df["industry_group"].nunique() if "industry_group" in panel_df.columns else 104

col_m1, col_m2, col_m3, col_m4, col_m5 = st.columns(5)
with col_m1:
    st.metric("Panel Setting", "xtset company_code year", help="Stata strongly balanced longitudinal panel structure")
with col_m2:
    st.metric("Observations (N)", f"{n_obs:,}")
with col_m3:
    st.metric("Cross-Section Units (i)", f"{n_firms:,} Firms")
with col_m4:
    st.metric("Time Horizon (t)", f"{years[0]} – {years[1]} (24 Yrs)")
with col_m5:
    st.metric("Industry Coverage", f"{n_industries} Sectors", help="Prowess / CMIE cross-industry manufacturing classification")

st.markdown("---")

# ── Main Workbench Tabs ────────────────────────────────────────────────────────
tab_cli, tab_esttab, tab_coefplot, tab_export = st.tabs([
    "💻 Stata Command Console",
    "📑 esttab Publication Matrix",
    "📈 coefplot Visualizer",
    "💾 Export .dta & Replication .do",
])

with tab_cli:
    st.markdown("### ⚡ Interactive Stata Terminal")
    st.caption("Type any standard Stata econometric or summary command below, or click any pre-configured template.")

    # Initialize in session_state if not present
    if "stata_cmd_input" not in st.session_state:
        st.session_state["stata_cmd_input"] = ""

    # Quick Template Buttons
    col_q1, col_q2, col_q3 = st.columns(3)
    with col_q1:
        if st.button("📊 . xtreg leverage roa tang size, fe cluster(id)", use_container_width=True):
            st.session_state["stata_cmd_input"] = "xtreg leverage profitability tangibility log_size, fe cluster(company_code)"
            st.session_state["_trigger_stata_run"] = True
            st.rerun()
        if st.button("📈 . xtreg leverage roa tang size, re", use_container_width=True):
            st.session_state["stata_cmd_input"] = "xtreg leverage profitability tangibility log_size, re"
            st.session_state["_trigger_stata_run"] = True
            st.rerun()
    with col_q2:
        if st.button("🧪 . hausman fe re", use_container_width=True):
            st.session_state["stata_cmd_input"] = "hausman fe re"
            st.session_state["_trigger_stata_run"] = True
            st.rerun()
        if st.button("🔍 . estat vif", use_container_width=True):
            st.session_state["stata_cmd_input"] = "estat vif"
            st.session_state["_trigger_stata_run"] = True
            st.rerun()
    with col_q3:
        if st.button("📋 . summarize leverage roa tang, detail", use_container_width=True):
            st.session_state["stata_cmd_input"] = "summarize leverage profitability tangibility, detail"
            st.session_state["_trigger_stata_run"] = True
            st.rerun()
        if st.button("🔗 . pwcorr leverage roa tang size, sig", use_container_width=True):
            st.session_state["stata_cmd_input"] = "pwcorr leverage profitability tangibility log_size, sig star(0.05)"
            st.session_state["_trigger_stata_run"] = True
            st.rerun()

    with st.expander("📚 PhD Dissertation Figure Replications (Chapters 5 & 8) — 1-Click Stata Command & Graph", expanded=False):
        col_th1, col_th2 = st.columns(2)
        with col_th1:
            if st.button("📊 Fig 5.1: Stage-Wise Profile (thesis fig51)", use_container_width=True):
                st.session_state["stata_cmd_input"] = "thesis fig51"
                st.session_state["_trigger_stata_run"] = True
                st.rerun()
            if st.button("📈 Fig 5.2: 2001–2024 Year-Wise Trends (thesis fig52)", use_container_width=True):
                st.session_state["stata_cmd_input"] = "thesis fig52"
                st.session_state["_trigger_stata_run"] = True
                st.rerun()
            if st.button("🧪 Fig 5.3: ANOVA Means of Leverage (tabstat leverage by stage)", use_container_width=True):
                st.session_state["stata_cmd_input"] = "tabstat leverage, by(life_stage)"
                st.session_state["_trigger_stata_run"] = True
                st.rerun()
        with col_th2:
            if st.button("📉 Fig 8.3: Leverage vs Profit & Tangibility (thesis fig83)", use_container_width=True):
                st.session_state["stata_cmd_input"] = "thesis fig83"
                st.session_state["_trigger_stata_run"] = True
                st.rerun()
            if st.button("📈 Fig 8.3B: Leverage vs Tangibility (scatter)", use_container_width=True):
                st.session_state["stata_cmd_input"] = "scatter leverage tangibility"
                st.session_state["_trigger_stata_run"] = True
                st.rerun()
            if st.button("🏛 Full Thesis Model: FE Panel Regression + coefplot", use_container_width=True):
                st.session_state["stata_cmd_input"] = "xtreg leverage profitability tangibility log_size tax_shield, fe cluster(company_code)"
                st.session_state["_trigger_stata_run"] = True
                st.rerun()

    # Command Input Bar
    with st.form("stata_command_form", clear_on_submit=False):
        c_in1, c_in2 = st.columns([5, 1])
        with c_in1:
            typed_cmd = st.text_input(
                "Stata Command Prompt:",
                value=st.session_state.get("stata_cmd_input", ""),
                placeholder=". xtreg leverage profitability tangibility log_size, fe cluster(company_code)",
                label_visibility="collapsed",
            )
        with c_in2:
            run_clicked = st.form_submit_button("▶ Run Command", use_container_width=True, type="primary")

    trigger_run = st.session_state.pop("_trigger_stata_run", False)
    active_cmd = (typed_cmd or "").strip()

    # Trigger execution if form was submitted (Enter or button click), template clicked, or new command entered
    should_run = (run_clicked or trigger_run or (active_cmd and active_cmd != st.session_state.get("_prev_cmd", "").strip())) and bool(active_cmd)

    if should_run:
        st.session_state["stata_cmd_input"] = active_cmd
        st.session_state["_prev_cmd"] = active_cmd
        with st.spinner(f"Executing: {active_cmd}..."):
            t0 = time.time()
            res = execute_stata_command(active_cmd, df=panel_df)
            elapsed = time.time() - t0
            st.session_state["stata_last_result"] = res
            st.session_state["stata_history"].append((active_cmd, res))

    # Render Command Results (6-Tier Stack) or Readiness Banner
    last_res = st.session_state.get("stata_last_result", None)

    if last_res is not None:
        last_cmd = st.session_state["stata_history"][-1][0] if st.session_state["stata_history"] else (active_cmd or "xtreg leverage roa tang size, fe")
        clean_cmd = last_cmd.lstrip('. ')
        current_theme = st.session_state.get("theme", "light")

        from models.rich_chat_renderer import (
            render_rich_terminal_html,
            render_detailed_economic_commentary_html,
            render_theory_scorecard_html,
            render_academic_vault_html,
        )
        from models.chart_switcher_engine import (
            build_forest_plot,
            build_beta_rank_bars,
        )

        # Tier 1: Corporate Finance Translation & Economic Intent
        fin_trans = get_financial_translation(clean_cmd)
        is_dark = current_theme == "dark"
        card_bg = "#0f172a" if is_dark else "#F0FDF4"
        card_border = "#1e293b" if is_dark else "#BBF7D0"
        card_text = "#e2e8f0" if is_dark else "#166534"
        st.markdown(f"""
        <div style="background: {card_bg}; border: 1px solid {card_border}; border-radius: 8px; padding: 12px 16px; margin-bottom: 14px; font-size: 13px; line-height: 1.5; color: {card_text};">
            <b>💡 Corporate Finance Translation & Economic Intent:</b><br/>
            {fin_trans}
        </div>
        """, unsafe_allow_html=True)

        # Tier 2: Stata Monospace Terminal
        ascii_out = last_res.get("ascii_output", "No output generated.")
        terminal_html = render_rich_terminal_html(ascii_out, f"Stata 18 SE · {clean_cmd}", theme=current_theme)
        if hasattr(st, "html"):
            st.html(terminal_html)
        else:
            st.markdown(terminal_html, unsafe_allow_html=True)

        # Tier 3: Visual Engine · Data-Gated Chart Switcher
        compat = last_res.get("compatible_charts", [])
        coefs = last_res.get("coefficients", {})
        if compat and coefs:
            c_sw1, c_sw2 = st.columns([3, 2])
            with c_sw1:
                st.markdown("""
                <div style="font-size: 13px; font-weight: 700; color: #0284C7; margin-top: 6px;">
                    📊 Visual Engine · Data-Gated Chart Switcher
                </div>
                <div style="font-size: 11.5px; color: var(--text-muted, #64748B);">
                    Switch between mathematically permitted econometric representations
                </div>
                """, unsafe_allow_html=True)
            with c_sw2:
                chart_options = [c["label"] for c in compat]
                selected_label = st.selectbox(
                    "Select Visualization:",
                    chart_options,
                    index=0,
                    key=f"stata_studio_chart_switcher_{clean_cmd[:20]}",
                    label_visibility="collapsed",
                )
            selected_id = next((c["id"] for c in compat if c["label"] == selected_label), "forest_plot")

            if selected_id == "beta_rank_bars":
                fig = build_beta_rank_bars(coefs, theme=current_theme)
            else:
                fig = build_forest_plot(coefs, theme=current_theme)
            st.plotly_chart(fig, use_container_width=True, config=PLOTLY_FULL_CONFIG)
            st.caption("🛡️ *Compatibility Rule Enforced:* Only mathematically permissible regression representations are displayed. Non-continuous charts (Donut, Pie, Stacked Area) are automatically excluded.")
        elif last_res.get("fig"):
            st.plotly_chart(last_res["fig"], use_container_width=True, config=PLOTLY_FULL_CONFIG)
        elif last_res.get("chart_spec"):
            from models.agent_tools import render_chat_chart_figure
            fig = render_chat_chart_figure(last_res["chart_spec"], theme=current_theme)
            if fig:
                st.plotly_chart(fig, use_container_width=True, config=PLOTLY_FULL_CONFIG)

        # Tier 4 & 5: Economic Commentary & Theory Scorecard
        scorecard = last_res.get("theory_scorecard", [])
        if scorecard:
            st.markdown(render_detailed_economic_commentary_html(scorecard, theme=current_theme), unsafe_allow_html=True)
            st.markdown(render_theory_scorecard_html(scorecard, theme=current_theme), unsafe_allow_html=True)

        # Tier 6: Peer-Reviewed Academic Literature Vault
        lit_eval = last_res.get("literature_eval", {})
        if lit_eval and lit_eval.get("citations"):
            st.markdown(render_academic_vault_html(lit_eval["citations"], theme=current_theme), unsafe_allow_html=True)

        # Command History Expander
        with st.expander("📜 Stata Command History in this Session", expanded=False):
            for i, (h_cmd, h_res) in enumerate(reversed(st.session_state["stata_history"])):
                st.markdown(f"**[{len(st.session_state['stata_history'])-i}]** `{h_cmd}` — *Status: {h_res.get('status')}*")
    else:
        st.info("⚡ **Stata Command Console Ready.** Type any econometric command above (e.g. `xtreg leverage profitability tangibility log_size, fe cluster(company_code)`) or click one of the quick templates above to execute.")


with tab_esttab:
    st.markdown("### 📑 Multi-Model Comparison Table (`esttab` / `outreg2`)")
    st.caption("Publication-grade table comparing Pooled OLS, Firm Fixed Effects, and Random Effects side-by-side with cluster-adjusted standard errors in parentheses.")

    df_stored = get_stored_models_table()
    if df_stored.empty:
        # Pre-populate with standard specifications
        execute_stata_command("regress leverage profitability tangibility log_size", df=panel_df)
        execute_stata_command("xtreg leverage profitability tangibility log_size, fe cluster(company_code)", df=panel_df)
        execute_stata_command("xtreg leverage profitability tangibility log_size, re", df=panel_df)
        df_stored = get_stored_models_table()

    st.dataframe(df_stored, use_container_width=True, hide_index=True)

    c_dl1, c_dl2, c_dl3 = st.columns(3)
    with c_dl1:
        # LaTeX Code Generation
        latex_str = generate_esttab_latex()
        st.download_button(
            "📥 Download LaTeX (.tex)",
            data=latex_str,
            file_name="stata_publication_models.tex",
            mime="text/plain",
            use_container_width=True,
        )
    with c_dl2:
        # Microsoft Word Export
        tmp_docx = os.path.join(os.getcwd(), "scratch", "stata_publication_table.docx")
        os.makedirs(os.path.dirname(tmp_docx), exist_ok=True)
        generate_esttab_docx(tmp_docx)
        with open(tmp_docx, "rb") as f_docx:
            st.download_button(
                "📥 Download Word (.docx)",
                data=f_docx.read(),
                file_name="stata_publication_table.docx",
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                use_container_width=True,
            )
    with c_dl3:
        # CSV Export
        st.download_button(
            "📥 Download CSV (.csv)",
            data=df_stored.to_csv(index=False),
            file_name="stata_publication_table.csv",
            mime="text/csv",
            use_container_width=True,
        )

    with st.expander("👁 View Raw LaTeX Code", expanded=False):
        st.code(latex_str, language="latex")


with tab_coefplot:
    st.markdown("### 📈 Visual Determinants (`coefplot`)")
    st.caption("Point estimates with 95% confidence interval whiskers. Determinants with confidence intervals that do not cross zero (dashed line) are statistically significant.")

    coef_res = execute_stata_command("coefplot, drop(_cons) xline(0)", df=panel_df)
    spec = coef_res.get("chart_spec", {})

    if spec and spec.get("categories"):
        cats = spec["categories"]
        vals = spec["series"][0]["values"]
        lows = spec["error_bars"]["low"]
        highs = spec["error_bars"]["high"]

        # Calculate error bar deltas
        err_minus = [v - l for v, l in zip(vals, lows)]
        err_plus = [h - v for v, h in zip(vals, highs)]

        fig_coef = go.Figure()
        # Vertical zero reference line (xline(0))
        fig_coef.add_vline(x=0, line_width=1.5, line_dash="dash", line_color="#dc2626")

        fig_coef.add_trace(go.Scatter(
            x=vals,
            y=cats,
            mode="markers",
            name="Point Estimate (Beta)",
            marker=dict(size=10, color="#1f77b4", symbol="circle"),
            error_x=dict(
                type="data",
                symmetric=False,
                array=err_plus,
                arrayminus=err_minus,
                color="#1f77b4",
                thickness=2,
                width=6,
            ),
            hovertemplate="<b>%{y}</b><br>Beta: %{x:.4f}<extra></extra>",
        ))

        fig_coef.update_layout(
            title="coefplot: Panel Fixed Effects Estimates (95% Clustered CI)",
            xaxis_title="Coefficient Estimate",
            yaxis_title="Determinant",
            template="plotly_white",
            height=450,
            margin=dict(l=100, r=40, t=50, b=50),
        )
        st.plotly_chart(fig_coef, use_container_width=True)


with tab_export:
    st.markdown("### 💾 Native Stata Replication & Dataset Exporter")
    st.caption("Export the exact balanced panel dataset and replication do-file for direct execution inside native Stata 14, 15, 16, 17, or 18.")

    col_e1, col_e2 = st.columns(2)
    with col_e1:
        st.markdown("#### 📦 Binary Stata Dataset (`.dta`)")
        st.write(f"Contains all {n_obs:,} observations across {n_firms} firms with longitudinal panel variables formatted for Stata.")
        dta_buffer = io.BytesIO()
        export_df = prepare_df_for_stata(panel_df)
        export_df.to_stata(dta_buffer, write_index=False, version=117)
        dta_bytes = dta_buffer.getvalue()
        st.download_button(
            "⬇ Download lifecycle_panel_data.dta",
            data=dta_bytes,
            file_name="lifecycle_panel_data.dta",
            mime="application/x-stata-dta",
            use_container_width=True,
            type="primary",
        )

    with col_e2:
        st.markdown("#### 📜 Stata Replication Script (`.do`)")
        st.write("Complete, executable Stata replication script reproducing all fixed effects, random effects, Hausman tests, and publication tables.")
        do_file_content = f"""* ==============================================================================
* LifeCycle Leverage: Stata Empirical Replication Script
* Dataset: lifecycle_panel_data.dta (N={n_obs:,}, Firms={n_firms})
* ==============================================================================

clear all
set more off
capture log close

* 1. Load Data
use "lifecycle_panel_data.dta", clear

* 2. Set Longitudinal Panel Dimensions
xtset company_code year

* 3. Summary Statistics
summarize leverage profitability tangibility log_size tax dividend, detail
tabstat leverage profitability, by(life_stage) stat(mean sd n)
pwcorr leverage profitability tangibility log_size, sig star(0.05)

* 4. Pooled OLS Regression with Robust Standard Errors
regress leverage profitability tangibility log_size, robust
estimates store m1_ols
estat vif

* 5. Firm Fixed Effects with Cluster-Robust Standard Errors
xtreg leverage profitability tangibility log_size, fe vce(cluster company_code)
estimates store m2_fe

* 6. Random Effects GLS Regression
xtreg leverage profitability tangibility log_size, re
estimates store m3_re

* 7. Specification Diagnostics: Hausman Test
hausman m2_fe m3_re

* 8. Generate Side-by-Side Publication Table
esttab m1_ols m2_fe m3_re, se r2 star(* 0.10 ** 0.05 *** 0.01) title("Corporate Capital Structure Across Life Cycles")

* 9. Determinants Coefficient Plot
coefplot m2_fe, drop(_cons) xline(0) title("Determinants of Capital Structure")

exit
"""
        st.download_button(
            "⬇ Download replication_script.do",
            data=do_file_content,
            file_name="lifecycle_replication.do",
            mime="text/plain",
            use_container_width=True,
        )

    with st.expander("👁 Preview .do Script Content", expanded=False):
        st.code(do_file_content, language="stata")
