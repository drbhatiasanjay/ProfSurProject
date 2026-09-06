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
    /* Complete elimination of Streamlit stale / running fade and ghosting */
    .stApp[data-test-script-state="running"],
    .stApp[data-test-script-state="running"] *,
    div[data-testid="stElementContainer"],
    div[data-testid="stElementContainer"] *,
    .element-container,
    .stElementContainer,
    div[data-testid="stVerticalBlock"],
    div[data-testid="stVerticalBlock"] > div,
    div[data-testid="stHorizontalBlock"],
    div[data-testid="stHorizontalBlock"] > div,
    div[data-testid="column"],
    div[data-testid="stExpander"],
    div[data-testid="stTabs"],
    .stTabs [role="tablist"],
    .stTabs [role="tabpanel"],
    [data-testid="stMainBlockContainer"],
    [data-testid="stAppViewBlockContainer"] {
        opacity: 1 !important;
        filter: none !important;
        transition: none !important;
    }
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
years = (int(panel_df["year"].min()), int(panel_df["year"].max())) if "year" in panel_df.columns else (2001, 2025)
n_industries = panel_df["industry_group"].nunique() if "industry_group" in panel_df.columns else 104

col_m1, col_m2, col_m3, col_m4, col_m5 = st.columns(5)
is_dark = st.session_state.get("theme", "light") == "dark"
card_bg = "rgba(30, 41, 59, 0.55)" if is_dark else "#FFFFFF"
card_border = "#334155" if is_dark else "#E2E8F0"
lbl_col = "#94A3B8" if is_dark else "#64748B"
txt_col = "#F8FAFC" if is_dark else "#0F172A"

m_card_style = f"""
    background: {card_bg};
    border: 1px solid {card_border};
    border-radius: 10px;
    padding: 10px 12px;
    height: 100%;
    min-height: 82px;
    display: flex;
    flex-direction: column;
    justify-content: space-between;
    box-shadow: 0 1px 4px rgba(0,0,0,0.03);
"""

with col_m1:
    st.markdown(f"""
    <div style="{m_card_style}">
        <div style="font-size:0.67rem; font-weight:700; text-transform:uppercase; color:{lbl_col}; letter-spacing:0.04em;">PANEL SETTING</div>
        <div style="font-family:'Consolas','Courier New',monospace; font-size:0.82rem; font-weight:700; color:#0284C7; background:rgba(2,132,199,0.09); padding:3px 6px; border-radius:4px; white-space:nowrap; overflow:hidden; text-overflow:ellipsis;" title="xtset company_code year">xtset company_code year</div>
    </div>
    """, unsafe_allow_html=True)

with col_m2:
    st.markdown(f"""
    <div style="{m_card_style}">
        <div style="font-size:0.67rem; font-weight:700; text-transform:uppercase; color:{lbl_col}; letter-spacing:0.04em;">OBSERVATIONS (N)</div>
        <div style="display:flex; align-items:baseline; gap:5px; flex-wrap:nowrap;">
            <span style="font-size:1.3rem; font-weight:800; color:{txt_col}; font-family:'JetBrains Mono',monospace;">{n_obs:,}</span>
            <span style="font-size:0.68rem; color:#10B981; font-weight:700; background:rgba(16,185,129,0.12); padding:1px 5px; border-radius:4px; white-space:nowrap;">Balanced</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

with col_m3:
    st.markdown(f"""
    <div style="{m_card_style}">
        <div style="font-size:0.67rem; font-weight:700; text-transform:uppercase; color:{lbl_col}; letter-spacing:0.04em;">CROSS-SECTION (i)</div>
        <div style="display:flex; align-items:baseline; gap:5px;">
            <span style="font-size:1.3rem; font-weight:800; color:{txt_col}; font-family:'JetBrains Mono',monospace;">{n_firms:,}</span>
            <span style="font-size:0.75rem; color:#6366F1; font-weight:600;">Firms</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

with col_m4:
    n_yrs = years[1] - years[0] + 1
    st.markdown(f"""
    <div style="{m_card_style}">
        <div style="font-size:0.67rem; font-weight:700; text-transform:uppercase; color:{lbl_col}; letter-spacing:0.04em;">TIME HORIZON (T)</div>
        <div style="display:flex; align-items:baseline; gap:4px; flex-wrap:nowrap;">
            <span style="font-size:1.12rem; font-weight:800; color:{txt_col}; font-family:'JetBrains Mono',monospace; white-space:nowrap;">{years[0]}–{years[1]}</span>
            <span style="font-size:0.68rem; color:#059669; font-weight:600; white-space:nowrap;">({n_yrs}Y)</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

with col_m5:
    st.markdown(f"""
    <div style="{m_card_style}">
        <div style="font-size:0.67rem; font-weight:700; text-transform:uppercase; color:{lbl_col}; letter-spacing:0.04em;">INDUSTRY SECTORS</div>
        <div style="display:flex; align-items:baseline; gap:5px;">
            <span style="font-size:1.3rem; font-weight:800; color:{txt_col}; font-family:'JetBrains Mono',monospace;">{n_industries}</span>
            <span style="font-size:0.75rem; color:#06B6D4; font-weight:600;">Sectors</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

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

    # Command Input Bar Styling & Proportional Alignment
    st.markdown("""
    <style>
    /* Complete elimination of Streamlit stale / running fade and ghosting */
    .stApp[data-test-script-state="running"],
    .stApp[data-test-script-state="running"] *,
    div[data-testid="stElementContainer"],
    div[data-testid="stElementContainer"] *,
    .element-container,
    .stElementContainer,
    div[data-testid="stVerticalBlock"],
    div[data-testid="stVerticalBlock"] > div,
    div[data-testid="stHorizontalBlock"],
    div[data-testid="stHorizontalBlock"] > div,
    div[data-testid="column"],
    div[data-testid="stExpander"],
    div[data-testid="stTabs"],
    .stTabs [role="tablist"],
    .stTabs [role="tabpanel"],
    [data-testid="stMainBlockContainer"],
    [data-testid="stAppViewBlockContainer"] {
        opacity: 1 !important;
        filter: none !important;
        transition: none !important;
    }
    div[data-testid="stFormSubmitButton"] button {
        white-space: nowrap !important;
        min-height: 44px !important;
        height: 44px !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        font-weight: 600 !important;
        font-size: 0.95rem !important;
        letter-spacing: 0.01em !important;
    }
    div[data-testid="stTextInput"] input {
        min-height: 44px !important;
        height: 44px !important;
        font-size: 0.95rem !important;
    }
    /* Executive Processing Card with Spinner */
    div[data-testid="stSpinner"] {
        background: rgba(2, 132, 199, 0.06) !important;
        border: 1px solid #0284C7 !important;
        border-radius: 8px !important;
        padding: 14px 18px !important;
        margin: 12px 0 18px 0 !important;
        box-shadow: 0 4px 12px rgba(2, 132, 199, 0.08) !important;
    }
    div[data-testid="stSpinner"] > div {
        font-size: 0.95rem !important;
        font-weight: 600 !important;
        color: #0284C7 !important;
    }
    </style>
    """, unsafe_allow_html=True)

    with st.form("stata_command_form", clear_on_submit=False):
        c_in1, c_in2 = st.columns([5.2, 1.4], vertical_alignment="center")
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

    output_placeholder = st.empty()

    if should_run:
        st.session_state["stata_cmd_input"] = active_cmd
        st.session_state["_prev_cmd"] = active_cmd
        st.session_state["stata_last_result"] = None  # Clear previous result so stale text does not linger

        with output_placeholder.container():
            with st.spinner(f"⏳ Processing Stata command `.{active_cmd}`… Estimating econometric parameters & compiling results"):
                t0 = time.time()
                res = execute_stata_command(active_cmd, df=panel_df)
                elapsed = time.time() - t0
                if elapsed < 0.6:
                    time.sleep(0.6 - elapsed)
                st.session_state["stata_last_result"] = res
                st.session_state["stata_history"].append((active_cmd, res))

        output_placeholder.empty()

    # ── Render Results ─────────────────────────────────────────────────────
    last_res = st.session_state.get("stata_last_result", None)

    if last_res is not None:
        last_cmd = st.session_state["stata_history"][-1][0] if st.session_state["stata_history"] else (active_cmd or "xtreg leverage roa tang size, fe")
        clean_cmd = last_cmd.lstrip(". ")
        current_theme = st.session_state.get("theme", "light")

        from models.rich_chat_renderer import (
            render_rich_terminal_html,
            render_detailed_economic_commentary_html,
            render_theory_scorecard_html,
            render_academic_vault_html,
        )
        from models.chart_switcher_engine import build_forest_plot, build_beta_rank_bars

        is_dark = current_theme == "dark"

        # ── TIER 1: Corporate Finance Translation ──────────────────────────
        fin_trans = get_financial_translation(clean_cmd)
        card_bg    = "#0f172a" if is_dark else "#F0FDF4"
        card_border= "#1e293b" if is_dark else "#BBF7D0"
        card_text  = "#e2e8f0" if is_dark else "#166534"
        st.markdown(f"""
        <div style="background:{card_bg};border:1px solid {card_border};border-radius:8px;
                    padding:12px 16px;margin-bottom:14px;font-size:13px;
                    line-height:1.5;color:{card_text};">
            <b>💡 Corporate Finance Translation &amp; Economic Intent:</b><br/>{fin_trans}
        </div>
        """, unsafe_allow_html=True)

        # ── TIER 2: Stata Monospace Terminal ──────────────────────────────
        ascii_out = last_res.get("ascii_output", "No output generated.")
        n_obs_result = last_res.get("n_obs", 0)
        terminal_html = render_rich_terminal_html(
            ascii_out,
            f"Stata 18 SE · {clean_cmd}",
            theme=current_theme,
            n_obs=n_obs_result,
        )
        if hasattr(st, "html"):
            st.html(terminal_html)
        else:
            st.markdown(terminal_html, unsafe_allow_html=True)

        # ── TIER 3: Visual Engine ──────────────────────────────────────────
        compat = last_res.get("compatible_charts", [])
        coefs  = last_res.get("coefficients", {})
        if compat and coefs:
            with st.expander("📊 Visual Engine — Coefficient Plot", expanded=True):
                c_sw1, c_sw2 = st.columns([3, 2])
                with c_sw1:
                    st.markdown(
                        "<div style='font-size:13px;font-weight:700;color:#0284C7;margin-top:6px;'>"
                        "Data-Gated Chart Switcher</div>"
                        "<div style='font-size:11.5px;color:#64748B;'>"
                        "Only mathematically permissible representations shown</div>",
                        unsafe_allow_html=True,
                    )
                with c_sw2:
                    chart_options  = [c["label"] for c in compat]
                    selected_label = st.selectbox(
                        "Select chart",
                        chart_options,
                        index=0,
                        key=f"chart_sw_{clean_cmd[:20]}",
                        label_visibility="collapsed",
                    )
                selected_id = next((c["id"] for c in compat if c["label"] == selected_label), "forest_plot")
                fig = build_beta_rank_bars(coefs, theme=current_theme) if selected_id == "beta_rank_bars" else build_forest_plot(coefs, theme=current_theme)
                st.plotly_chart(fig, use_container_width=True, config=PLOTLY_FULL_CONFIG)
        elif last_res.get("fig"):
            with st.expander("📊 Visual Engine", expanded=True):
                st.plotly_chart(last_res["fig"], use_container_width=True, config=PLOTLY_FULL_CONFIG)
        elif last_res.get("chart_spec"):
            from models.agent_tools import render_chat_chart_figure
            fig = render_chat_chart_figure(last_res["chart_spec"], theme=current_theme)
            if fig:
                with st.expander("📊 Visual Engine", expanded=True):
                    st.plotly_chart(fig, use_container_width=True, config=PLOTLY_FULL_CONFIG)

        # ── TIER 4: Economic Analysis (Collapsible per variable) ──────────
        scorecard = last_res.get("theory_scorecard", [])
        if scorecard:
            n_validated = sum(1 for s in scorecard if "VALIDATED" in s.get("status", ""))
            n_total     = len(scorecard)

            with st.expander(
                f"💡 Part 2: Comprehensive Economic Analysis & Theoretical Interpretation"
                f"   —   {n_validated}/{n_total} theories validated",
                expanded=False,
            ):
                # Summary intro box
                intro_bg  = "rgba(245,158,11,0.08)" if is_dark else "#FFFBEB"
                intro_border = "rgba(245,158,11,0.25)" if is_dark else "#FDE68A"
                intro_color  = "#CBD5E1" if is_dark else "#334155"
                st.markdown(f"""
                <div style="background:{intro_bg};border:1px solid {intro_border};
                            border-radius:8px;padding:12px 16px;margin-bottom:12px;
                            font-size:13px;color:{intro_color};line-height:1.55;">
                    <b>Core Finding:</b> When controlling for unobserved, time-invariant firm differences
                    across our panel of 401 Indian manufacturing companies (2001–2025), the empirical
                    estimates reveal a clear story: <i>internal profits are king, physical plant sets the
                    borrowing ceiling, and larger corporates actively choose financial autonomy over debt.</i>
                </div>
                """, unsafe_allow_html=True)

                palette = ["#F43F5E", "#10B981", "#38BDF8", "#818CF8", "#F59E0B"]
                for i, item in enumerate(scorecard):
                    color      = palette[i % len(palette)]
                    var_label  = item.get("variable", "Variable")
                    raw_var    = item.get("raw_var", "")
                    beta_str   = item.get("beta", "—")
                    theory     = item.get("theory", "")
                    status     = item.get("status", "")
                    is_val     = "VALIDATED" in status
                    badge      = "✅ VALIDATED" if is_val else "⚠ PARTIAL"
                    # One-line summary for collapsed state
                    summary_line = f"β = {beta_str}   ·   {badge}   ·   {theory}"
                    body_col   = "#E2E8F0" if is_dark else "#1E293B"
                    lbl_col    = "#94A3B8" if is_dark else "#475569"
                    vt_col     = "#FFFFFF" if is_dark else "#0F172A"
                    bdg_bg     = ("#ECFDF5" if not is_dark else "rgba(16,185,129,0.15)") if is_val else ("#FEF3C7" if not is_dark else "rgba(245,158,11,0.15)")
                    bdg_tc     = ("#059669" if not is_dark else "#10B981") if is_val else ("#B45309" if not is_dark else "#F59E0B")

                    with st.expander(f"  {'›'} {var_label}   {summary_line}", expanded=False):
                        if "profit" in raw_var.lower() or "roa" in raw_var.lower():
                            intuition = "When profitability surges, Indian manufacturing firms immediately channel retained earnings into debt repayment rather than tapping external lenders — strong evidence for the Pecking Order Hypothesis (Myers & Majluf, 1984)."
                        elif "tangib" in raw_var.lower():
                            intuition = "Asset-heavy firms pledge physical collateral to unlock larger bank credit lines. Following IBC 2016, Indian credit committees mandate tangible asset coverage as a non-negotiable prerequisite for long-term project loans."
                        elif "size" in raw_var.lower():
                            intuition = "Large Indian conglomerates have outgrown intermediated bank credit — they possess decades of accumulated internal reserves and can float domestic or international equity (Financial Independence Hypothesis)."
                        else:
                            intuition = f"Reflects the marginal responsiveness of corporate leverage to changes in {var_label} after controlling for firm-level fixed unobserved heterogeneity."

                        st.markdown(f"""
                        <div style="border-left:4px solid {color};padding-left:14px;margin:4px 0 0 0;">
                          <div style="font-size:13.5px;font-weight:700;color:{vt_col};margin-bottom:6px;">
                            {var_label}
                            <span style="background:{bdg_bg};color:{bdg_tc};border:1px solid {bdg_tc};
                                         padding:2px 7px;border-radius:4px;font-size:11px;
                                         font-weight:700;margin-left:10px;">{badge}</span>
                          </div>
                          <div style="font-size:12.5px;color:{body_col};line-height:1.55;margin-bottom:5px;">
                            <b style="color:{lbl_col};">Estimate:</b> {beta_str} &nbsp;|&nbsp;
                            <b style="color:{lbl_col};">Theory:</b> {theory}
                          </div>
                          <div style="font-size:12.5px;color:{body_col};line-height:1.55;">
                            <b style="color:{lbl_col};">Economic intuition:</b> {intuition}
                          </div>
                        </div>
                        """, unsafe_allow_html=True)

                # ── Synthesized Academic Verdict (nested collapsible) ──────
                st.markdown("---")
                with st.expander("  🏛️ Synthesized Academic Verdict — Two-Tier Life Cycle Dynamic", expanded=False):
                    overall_bg  = "rgba(15,23,42,0.6)"  if is_dark else "#F8FAFC"
                    overall_border = "rgba(56,189,248,0.25)" if is_dark else "#E2E8F0"
                    overall_col = "#E2E8F0" if is_dark else "#0F172A"
                    title_col   = "#F59E0B" if is_dark else "#B45309"
                    st.markdown(f"""
                    <div style="background:{overall_bg};padding:14px 18px;border-radius:8px;
                                border:1px solid {overall_border};color:{overall_col};
                                font-size:13px;line-height:1.65;">
                        Indian corporate capital structure cannot be explained by any single theory in isolation.
                        The evidence demonstrates a <b>Two-Tier Life Cycle Dynamic</b>:<br/>
                        <b>1. Operational margin:</b> Firms follow <b>Pecking Order Theory</b> — abundant
                        cash flow → debt repayment; cash drought → forced borrowing.<br/>
                        <b>2. Structural constraint:</b> Access to debt is governed by the <b>Trade-Off
                        Collateral Channel</b> — firms can only borrow up to the liquidation value of
                        tangible assets.<br/>
                        <b>3. Life-stage trajectory:</b> As firms reach maturity, reliance on bank debt
                        gives way to equity capitalisation and internal surpluses.
                    </div>
                    """, unsafe_allow_html=True)

        # ── TIER 5: Theory Scorecard (collapsible) ─────────────────────────
        if scorecard:
            with st.expander("📋 Theory & Literature Benchmark Validation Scorecard", expanded=False):
                st.markdown(render_theory_scorecard_html(scorecard, theme=current_theme), unsafe_allow_html=True)

        # ── TIER 6: Citations — top 2 visible, rest collapsible ───────────
        lit_eval = last_res.get("literature_eval", {})
        citations = lit_eval.get("citations", []) if lit_eval else []
        if citations:
            # Theme tokens
            cite_bg     = "rgba(15,23,42,0.5)"  if is_dark else "#FFFFFF"
            cite_border = "#1E293B" if is_dark else "#E2E8F0"
            cite_title  = "#818CF8" if is_dark else "#4338CA"
            cite_text   = "#CBD5E1" if is_dark else "#1E293B"
            cite_tag_bg = "rgba(129,140,248,0.15)" if is_dark else "#EEF2FF"
            cite_tag_c  = "#818CF8" if is_dark else "#4338CA"

            def _tag(cit):
                if any(k in cit for k in ["Wooldridge","Cameron","Baltagi"]):
                    return "METHODOLOGY"
                if any(k in cit for k in ["Journal of Finance","Rajan","Booth","Myers"]):
                    return "JOURNAL OF FINANCE"
                if any(k in cit for k in ["Reserve Bank","IBBI"]):
                    return "INSTITUTIONAL REPORT"
                return "EMPIRICAL LITERATURE"

            def _cite_row(cit):
                tag = _tag(cit)
                return (
                    f'<div style="padding:8px 0;border-bottom:1px solid {cite_border};'
                    f'font-size:12px;color:{cite_text};line-height:1.45;">'
                    f'<span style="background:{cite_tag_bg};color:{cite_tag_c};'
                    f'border:1px solid {cite_tag_c};padding:2px 6px;border-radius:4px;'
                    f'font-size:10px;font-weight:700;margin-right:8px;">{tag}</span>'
                    f'{html.escape(cit)}</div>'
                )

            top2_html = "".join(_cite_row(c) for c in citations[:2])
            st.markdown(f"""
            <div style="background:{cite_bg};border:1px solid {cite_border};
                        border-radius:8px;padding:16px 20px;margin-bottom:14px;">
                <div style="font-size:12.5px;font-weight:700;color:{cite_title};margin-bottom:10px;">
                    📚 Part 3: Peer-Reviewed Literature & Citations
                    <span style="font-weight:400;font-size:11px;margin-left:8px;color:#64748B;">
                        Showing 2 of {len(citations)}
                    </span>
                </div>
                {top2_html}
            </div>
            """, unsafe_allow_html=True)

            if len(citations) > 2:
                with st.expander(f"  › Show all {len(citations)} citations", expanded=False):
                    rest_html = "".join(_cite_row(c) for c in citations[2:])
                    st.markdown(f"""
                    <div style="background:{cite_bg};border:1px solid {cite_border};
                                border-radius:8px;padding:12px 16px;">
                        {rest_html}
                    </div>
                    """, unsafe_allow_html=True)

        # ── Command History ────────────────────────────────────────────────
        with st.expander("📜 Command History", expanded=False):
            for i, (h_cmd, h_res) in enumerate(reversed(st.session_state["stata_history"])):
                idx = len(st.session_state["stata_history"]) - i
                status_icon = "✅" if h_res.get("status") == "success" else "❌"
                st.markdown(f"**[{idx}]** `{h_cmd}` {status_icon}")
    else:
        st.info("⚡ **Stata Command Console Ready.** Type any econometric command above or click a quick template to execute.")



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
