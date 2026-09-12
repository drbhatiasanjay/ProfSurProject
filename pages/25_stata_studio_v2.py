"""Stata Studio V2 — Variable-Aware Multi-Turn Econometric Workbench.

Provides full mathematical, syntax, and visual parity with Stata 17/18:
- Dynamic variable insertion palette & live syntax assist.
- Reverse-chronological multi-turn execution tree with individual and global collapse/expand controls.
- Default expansion of the active (latest) run with compact historical chips.
- Per-row [Re-run / Copy] and [Delete] actions with bidirectional AnalysisSession sync.
- Dynamic publication matrix (esttab) & coefficient forest plots (coefplot).
- Clean replication export (.dta & .do).
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
    resolve_panel_variable,
    parse_stata_command,
    COMMON_VAR_ALIASES,
    DOCX_AVAILABLE,
)
from models.rich_chat_renderer import (
    render_rich_terminal_html,
    render_detailed_economic_commentary_html,
    render_theory_scorecard_html,
    render_academic_vault_html,
)
from models.chart_switcher_engine import build_forest_plot, build_beta_rank_bars

# Ensure session state initialization
ensure_session_state()

db.log_page_visit("Stata Studio V2")

st.set_page_config(
    page_title="Stata Studio V2 — LifeCycle Leverage",
    page_icon="💻",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Accessible to all roles
require_role("admin", "researcher", "viewer", "cfo", "guest")

# ── Financial Commentary Translator ──────────────────────────────────────────
def get_financial_translation(cmd_str: str) -> str:
    """Translates a Stata command into executive corporate finance intent."""
    low = (cmd_str or "").lower().strip()
    if low.startswith("."):
        low = low[1:].strip()

    if low.startswith("xtreg") and (" fe" in low or ", fe" in low or ",fe" in low):
        return (
            "Estimates a within-firm <b>Fixed Effects panel regression</b> analyzing how corporate debt ratios (leverage) "
            "respond to firm profitability, asset tangibility, and size. By de-meaning data within each firm, "
            "it purges all unobserved time-invariant firm heterogeneity (governance heritage, founding culture), "
            "identifying within-firm associations. Evaluates <b>Pecking Order Theory</b> (profitability draining debt) vs. "
            "<b>Trade-Off Theory</b> (tangibility providing pledgeable debt capacity)."
        )
    if low.startswith("xtreg") and (" re" in low or ", re" in low or ",re" in low):
        return (
            "Estimates a <b>Random Effects panel regression</b> using Generalized Least Squares (GLS) to assess capital structure "
            "determinants across firms and over time, providing efficient parameter estimates under the assumption that firm-specific "
            "unobserved heterogeneity is uncorrelated with financial regressors."
        )
    if low.startswith("xtset"):
        return (
            "Declares and validates longitudinal panel dimensions (firm cross-section <code>i</code> and time series <code>t</code>). "
            "Verifies observations for duplicate firm-year keys and establishes panel balance and delta intervals for subsequent models."
        )
    if low.startswith("lgraph"):
        return (
            "Generates multi-series longitudinal trajectories over time across firms. "
            "Computes annual cross-sectional means to track corporate balance-sheet evolutions."
        )
    if low.startswith("tabulate") or low.startswith("tab "):
        return (
            "Computes one-way or two-way frequency distributions, percentage breakdowns, and cumulative shares "
            "across categorical dimensions (e.g. corporate life stages or industry sectors)."
        )
    if low.startswith("hausman"):
        return (
            "Executes the formal <b>Hausman specification test</b> contrasting Fixed Effects consistency against Random Effects efficiency. "
            "Determines whether individual firm endowments correlate with explanatory variables to verify whether within-firm "
            "Fixed Effects modeling is statistically required."
        )
    if low.startswith("summarize") or low.startswith("sum "):
        return (
            "Computes comprehensive descriptive statistics (mean, standard deviation, percentiles, skewness) "
            "to establish baseline parametric distributions across all panel covariates."
        )
    if low.startswith("pwcorr"):
        return (
            "Generates pairwise Pearson correlation coefficients with exact two-tailed significance levels "
            "to diagnose preliminary bivariate linkages and inspect for collinearity."
        )
    if low.startswith("estat vif"):
        return (
            "Calculates Variance Inflation Factors (VIF) and tolerance statistics to identify severe multicollinearity "
            "among explanatory variables."
        )
    if low.startswith("margins"):
        return (
            "Estimates post-estimation marginal effects (average derivative of predicted response), identifying "
            "how the sensitivity of debt changes across distinct corporate lifecycle stages."
        )
    if low.startswith("thesis"):
        return (
            "Executes the complete end-to-end dissertation empirical pipeline: estimating Pooled OLS, Fixed Effects, "
            "Random Effects, Dynamic Interactions, and Hausman specification tests in one unified replication run."
        )
    return f"Executes econometric evaluation for <code>.{html.escape(cmd_str)}</code>."


# ── Active Panel Dataset & Filters ───────────────────────────────────────────
panel_mode = st.session_state.get("panel_mode", "thesis")
filters = st.session_state.get("filters", {})
ft = db.filters_to_tuple(filters)
panel_df = db.get_active_panel_data(ft)

if panel_df is None or panel_df.empty:
    st.error("No active panel data loaded. Please check database connection.")
    st.stop()

# ── Session State for Multi-Turn History ─────────────────────────────────────
if "stata_v2_runs" not in st.session_state:
    st.session_state["stata_v2_runs"] = []

if "stata_v2_cmd_input" not in st.session_state:
    st.session_state["stata_v2_cmd_input"] = "summarize leverage profitability tangibility log_size, detail"

if "stata_v2_tree_mode" not in st.session_state:
    st.session_state["stata_v2_tree_mode"] = "active_only"  # 'active_only', 'expand_all', 'collapse_all'

if "stata_v2_var_category" not in st.session_state:
    st.session_state["stata_v2_var_category"] = "core"

# ── Metric Ribbons Header (Rendered ONCE) ────────────────────────────────────
n_obs = len(panel_df)
n_firms = panel_df["company_code"].nunique() if "company_code" in panel_df.columns else 0
years = (int(panel_df["year"].min()), int(panel_df["year"].max())) if "year" in panel_df.columns else (2001, 2025)
n_industries = panel_df["industry_group"].nunique() if "industry_group" in panel_df.columns else 104

col_m1, col_m2, col_m3, col_m4, col_m5 = st.columns(5)
is_dark = st.session_state.get("theme", "light") == "dark"
accent_blue = "#38BDF8" if is_dark else "#0284C7"
accent_indigo = "#818CF8" if is_dark else "#6366F1"
accent_green = "#34D399" if is_dark else "#059669"
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
        <div style="font-family:'Consolas','Courier New',monospace; font-size:0.82rem; font-weight:700; color:{accent_blue}; background:rgba(2,132,199,0.09); padding:3px 6px; border-radius:4px; white-space:nowrap; overflow:hidden; text-overflow:ellipsis;" title="xtset company_code year">xtset company_code year</div>
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
            <span style="font-size:0.75rem; color:{accent_indigo}; font-weight:600;">Firms</span>
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
            <span style="font-size:0.68rem; color:{accent_green}; font-weight:600; white-space:nowrap;">({n_yrs}Y)</span>
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

# ── Studio Header Title Block (Prototype parity) ─────────────────────────────
hdr_bg = "rgba(15,23,42,0.7)" if is_dark else "#FFFFFF"
hdr_border = "#334155" if is_dark else "#E2E8F0"
hdr_sub = "#94A3B8" if is_dark else "#64748B"
st.markdown(f"""
<div style="background:{hdr_bg}; border:1px solid {hdr_border}; border-radius:12px; padding:14px 20px; margin-bottom:16px; display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:12px;">
  <div>
    <div style="font-size:1.15rem; font-weight:800; color:{txt_col}; display:flex; align-items:center; gap:8px;">
      <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="{accent_blue}" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="M4 19.5v-15A2.5 2.5 0 0 1 6.5 2H20v20H6.5a2.5 2.5 0 0 1-2.5-2.5Z"/><path d="M6 6h10"/><path d="M6 10h10"/><path d="M6 14h6"/></svg>
      Stata Replication Studio
    </div>
    <div style="font-size:0.8rem; color:{hdr_sub}; margin-top:2px;">Panel Econometrics &amp; Capital Structure Empirical Lab — LifeCycle Leverage</div>
  </div>
  <div style="display:flex; gap:8px; flex-wrap:wrap;">
    <span style="font-size:0.72rem; font-weight:600; padding:3px 10px; border-radius:999px; background:{'rgba(2,132,199,0.15)' if is_dark else '#EFF6FF'}; border:1px solid {'#1e40af' if is_dark else '#BFDBFE'}; color:{accent_blue};">Dataset: panel_data.dta</span>
    <span style="font-size:0.72rem; font-weight:600; padding:3px 10px; border-radius:999px; background:{'rgba(30,41,59,0.5)' if is_dark else '#F1F5F9'}; border:1px solid {hdr_border}; color:{hdr_sub};">N = {n_firms} Firms</span>
    <span style="font-size:0.72rem; font-weight:600; padding:3px 10px; border-radius:999px; background:{'rgba(30,41,59,0.5)' if is_dark else '#F1F5F9'}; border:1px solid {hdr_border}; color:{hdr_sub};">T = {years[0]}–{years[1]}</span>
    <span style="font-size:0.72rem; font-weight:600; padding:3px 10px; border-radius:999px; background:{'rgba(30,41,59,0.5)' if is_dark else '#F1F5F9'}; border:1px solid {hdr_border}; color:{hdr_sub};">Obs = {n_obs:,}</span>
    <span style="font-size:0.72rem; font-weight:600; padding:3px 10px; border-radius:999px; background:{'rgba(16,185,129,0.15)' if is_dark else '#ECFDF5'}; border:1px solid {'#065f46' if is_dark else '#A7F3D0'}; color:{accent_green};">Balanced ✓</span>
  </div>
</div>
""", unsafe_allow_html=True)

st.markdown("---")

# ── Main Studio Tabs ─────────────────────────────────────────────────────────
_run_count = len(st.session_state.get("stata_v2_runs", []))
_run_badge = f" [{_run_count} Run{'s' if _run_count != 1 else ''}]" if _run_count > 0 else ""
tab_cli, tab_esttab, tab_coefplot, tab_export = st.tabs([
    f"💻 1. Command Console & Execution Tree{_run_badge}",
    "📑 2. Multi-Model Table (esttab)",
    "📈 3. Coefficient Plot (coefplot)",
    "💾 4. Replication Bundle Export",
])

# =============================================================================
# TAB 1: COMMAND CONSOLE & MULTI-TURN TREE (DRIVER)
# =============================================================================
with tab_cli:
    st.markdown("### ⚡ Interactive Stata Command Console & Workbench")
    st.caption("Select from supported commands or type custom syntax. Click variable chips to insert.")

    # 1. Categorized Variable Tray
    VAR_CATEGORIES = {
        "core": [
            ("leverage", "DEP", "Total Debt / Total Assets"),
            ("profitability", "INDEP", "Operating Profitability / ROA (prof)"),
            ("tangibility", "INDEP", "Net PPE / Total Assets (tang)"),
            ("log_size", "INDEP", "Logarithm of Total Assets (size)"),
            ("corplifestage", "FACTOR", "Life Stage 1-5 Dickinson (stage)"),
        ],
        "controls": [
            ("dividend", "INDEP", "Dividend Payout Ratio (dvnd)"),
            ("taxShield", "INDEP", "Non-Debt Tax Shield / Depreciation"),
            ("intRate", "INDEP", "Effective Borrowing Interest Rate"),
            ("promoter_share", "INDEP", "Promoter / Insider Shareholding %"),
            ("cash_holdings", "INDEP", "Cash & Equivalents / Total Assets"),
            ("borrowings", "INDEP", "Total Borrowings (Short + Long-Term)"),
        ],
        "shocks": [
            ("ibc_2016", "DUMMY", "Insolvency and Bankruptcy Code Dummy"),
            ("gfc", "DUMMY", "Global Financial Crisis Dummy (2008-09)"),
            ("covid_dummy", "DUMMY", "COVID Pandemic Dummy (2020-21)"),
            ("year", "TIME", "Calendar Time Period"),
            ("company_code", "ID", "Firm Cross-Section Identifier"),
        ],
        "all": [
            ("leverage", "DEP", "Total Debt / Total Assets"),
            ("profitability", "INDEP", "Operating Profitability / ROA"),
            ("tangibility", "INDEP", "Net PPE / Total Assets"),
            ("log_size", "INDEP", "Log Total Assets"),
            ("corplifestage", "FACTOR", "Life Stage 1-5 Dickinson"),
            ("dividend", "INDEP", "Dividend Payout Ratio"),
            ("taxShield", "INDEP", "Non-Debt Tax Shield"),
            ("intRate", "INDEP", "Interest Rate"),
            ("promoter_share", "INDEP", "Promoter Shareholding %"),
            ("cash_holdings", "INDEP", "Cash / Total Assets"),
            ("borrowings", "INDEP", "Total Borrowings"),
            ("ibc_2016", "DUMMY", "IBC 2016 Dummy"),
            ("gfc", "DUMMY", "GFC Dummy"),
            ("covid_dummy", "DUMMY", "COVID Dummy"),
            ("year", "TIME", "Calendar Year"),
            ("company_code", "ID", "Firm ID"),
        ],
    }

    # Tag color definitions
    _tag_colors = {
        "DEP":    ("#fee2e2", "#b91c1c"),
        "INDEP":  ("#e0e7ff", "#4338ca"),
        "FACTOR": ("#fef3c7", "#b45309"),
        "DUMMY":  ("#f0fdf4", "#16a34a"),
        "TIME":   ("#f0f9ff", "#0284c7"),
        "ID":     ("#f1f5f9", "#475569"),
    }

    _cur_cat = st.session_state["stata_v2_var_category"]
    c_cat1, c_cat2, c_cat3, c_cat4, c_cat5 = st.columns([1.1, 1.1, 1.3, 1.2, 2.4])
    with c_cat1:
        if st.button("Core Vars (5)", use_container_width=True, type="primary" if _cur_cat == "core" else "secondary"):
            st.session_state["stata_v2_var_category"] = "core"; st.rerun()
    with c_cat2:
        if st.button("Controls (6)", use_container_width=True, type="primary" if _cur_cat == "controls" else "secondary"):
            st.session_state["stata_v2_var_category"] = "controls"; st.rerun()
    with c_cat3:
        if st.button("Shocks & IDs (5)", use_container_width=True, type="primary" if _cur_cat == "shocks" else "secondary"):
            st.session_state["stata_v2_var_category"] = "shocks"; st.rerun()
    with c_cat4:
        if st.button("All Columns (16)", use_container_width=True, type="primary" if _cur_cat == "all" else "secondary"):
            st.session_state["stata_v2_var_category"] = "all"; st.rerun()
    with c_cat5:
        st.caption("Click chip to insert | Supports `i.var` & `c.v1##c.v2` interactions")

    active_var_list = VAR_CATEGORIES.get(_cur_cat, VAR_CATEGORIES["core"])

    # Render typed variable chips as styled HTML badges
    _chip_bg = "rgba(30,41,59,0.55)" if is_dark else "#FFFFFF"
    _chip_border = "#334155" if is_dark else "#CBD5E1"
    _chip_txt = "#E2E8F0" if is_dark else "#0F172A"
    _chips_html = ""
    for _vname, _vtag, _vdesc in active_var_list:
        _tbg, _tfg = _tag_colors.get(_vtag, ("#F1F5F9", "#475569"))
        _chips_html += f"""
        <span title="{_vtag}: {_vdesc}" style="display:inline-flex; align-items:center; gap:5px;
          font-family:'Fira Code',monospace; font-size:0.76rem; font-weight:600;
          padding:4px 9px; border-radius:5px; border:1px solid {_chip_border};
          background:{_chip_bg}; color:{_chip_txt}; margin:3px;
          cursor:default; user-select:none;">
          <span style="font-size:0.6rem; padding:1px 4px; border-radius:3px; font-weight:800;
            text-transform:uppercase; background:{_tbg}; color:{_tfg};">{_vtag}</span>
          {_vname}
        </span>"""
    st.markdown(f"""<div style="padding:8px 4px; display:flex; flex-wrap:wrap;">{_chips_html}</div>""", unsafe_allow_html=True)
    st.caption("⬆️ Hover chips to see descriptions — use the command box below to type variable names")

    # Clickable chip buttons (hidden below, functional — map each chip to an insert button)
    _click_cols = st.columns(len(active_var_list))
    for _ci, (_vname, _vtag, _vdesc) in enumerate(active_var_list):
        with _click_cols[_ci]:
            if st.button(_vname, key=f"vchip_{_vname}_{_cur_cat}", help=f"Insert '{_vname}'", use_container_width=True):
                cur = st.session_state["stata_v2_cmd_input"].strip()
                if cur:
                    st.session_state["stata_v2_cmd_input"] = f"{cur} {_vname}"
                else:
                    st.session_state["stata_v2_cmd_input"] = _vname
                st.rerun()

    # 2. Supported Commands Dropdown (Categorized & Ordered by Frequency)
    # Categorized command options (prototype parity: grouped by domain)
    SUPPORTED_COMMAND_OPTIONS = [
        "── 1. Data Exploration & Summaries ──────────────",
        "describe",
        "summarize leverage profitability tangibility log_size, detail",
        "tabstat leverage profitability tangibility, by(corplifestage) stat(mean sd p50 N)",
        "tabulate corplifestage",
        "lgraph leverage prof year, wide",
        "── 2. Panel Declaration & Diagnostics ───────────",
        "xtset company_code year",
        "pwcorr leverage profitability tangibility log_size, sig",
        "estat vif",
        "xttest0",
        "xtserial leverage profitability",
        "hausman fe re",
        "── 3. Baseline & Advanced Regressions ───────────",
        "regress leverage profitability tangibility log_size",
        "xtreg leverage profitability tangibility log_size, fe cluster(company_code)",
        "xtreg leverage profitability tangibility log_size, re",
        "reghdfe leverage profitability tangibility, absorb(company_code year)",
        "xtivreg leverage tangibility (profitability = taxShield), fe",
        "── 4. Life Stage & Interactions (Thesis Models) ─",
        "xtreg leverage i.corplifestage c.prof##c.tang c.prof##c.dvnd taxShield intRate i.year, fe",
        "margins, dydx(profitability) at(corplifestage=(1 2 3 4 5))",
        "thesis",
        "── 5. Publication Tables & Visuals ──────────────",
        "esttab m1 m2 m3, se r2 star(* 0.10 ** 0.05 *** 0.01)",
        "coefplot m1 m2 m3, drop(_cons) xline(0)",
        "scatter leverage profitability || lfit leverage profitability",
        "histogram leverage, normal",
        "graph box leverage, over(corplifestage)",
    ]
    # Section headers in dropdown (start with ──) should be non-selectable
    _DROPDOWN_HEADERS = {o for o in SUPPORTED_COMMAND_OPTIONS if o.startswith("──")}

    selected_cmd = st.selectbox(
        "Command Library — grouped by category:",
        options=SUPPORTED_COMMAND_OPTIONS,
        index=0,
        key="stata_v2_cmd_select",
        format_func=lambda x: f"  {x}" if not x.startswith("──") else x,
    )

    if selected_cmd and selected_cmd not in _DROPDOWN_HEADERS:
        if selected_cmd != st.session_state.get("_last_selected_cmd"):
            st.session_state["stata_v2_cmd_input"] = selected_cmd
            st.session_state["_last_selected_cmd"] = selected_cmd
            st.session_state["_trigger_stata_v2_run"] = True
            st.rerun()

    # 3. Command Input Prompt & Form
    with st.form("stata_v2_command_form", clear_on_submit=False):
        c_in1, c_in2 = st.columns([5.2, 1.4], vertical_alignment="center")
        with c_in1:
            typed_cmd = st.text_input(
                "Stata Command Prompt:",
                value=st.session_state.get("stata_v2_cmd_input", ""),
                placeholder=". xtreg leverage profitability tangibility log_size, fe cluster(company_code)",
                label_visibility="collapsed",
            )
        with c_in2:
            run_clicked = st.form_submit_button("▶ Execute", use_container_width=True, type="primary")

    # Syntax Assist Guide
    clean_cmd_str = (typed_cmd or "").strip().lstrip(". ")
    first_token = clean_cmd_str.split()[0].lower() if clean_cmd_str else ""
    syntax_hint = "Type any Stata command (e.g. summarize, tabulate, regress, xtreg, hausman, margins, esttab)"
    if "fe" in clean_cmd_str and "xtreg" in clean_cmd_str:
        syntax_hint = "xtreg depvar [indepvars] [i.factor] [c.var1##c.var2], fe [cluster(id) robust]"
    elif "re" in clean_cmd_str and "xtreg" in clean_cmd_str:
        syntax_hint = "xtreg depvar [indepvars], re [theta level(#) vce(robust)]"
    elif first_token in ("regress", "reg"):
        syntax_hint = "regress depvar [indepvars] [if] [in] [weight], [robust vce(cluster varname)]"
    elif first_token in ("summarize", "sum"):
        syntax_hint = "summarize [varlist] [if] [in] [weight] [, detail format]"
    elif first_token in ("tabstat",):
        syntax_hint = "tabstat varlist, by(groupvar) stat(mean sd min max p50 N)"
    elif first_token in ("hausman",):
        syntax_hint = "hausman consistent_model efficient_model [, constant]"
    elif first_token in ("margins",):
        syntax_hint = "margins [marginlist] [, dydx(varlist) at(varlist)]"
    elif first_token in ("describe", "des", "d", "codebook"):
        syntax_hint = "describe [varlist] [, simple short detail]"

    st.markdown(f"""
    <div style="font-size:0.78rem; color:{lbl_col}; background:rgba(2,132,199,0.06); border-left:3px solid {accent_blue}; padding:6px 12px; border-radius:0 6px 6px 0; margin-bottom:14px;">
        <strong>Syntax Assist:</strong> <span style="font-family:'Fira Code',monospace; color:{accent_blue}; font-weight:600;">{syntax_hint}</span>
    </div>
    """, unsafe_allow_html=True)

    trigger_run = st.session_state.pop("_trigger_stata_v2_run", False)
    should_run = (run_clicked or trigger_run) and bool(clean_cmd_str)

    # Trigger execution
    if should_run:
        st.session_state["stata_v2_cmd_input"] = clean_cmd_str
        with st.spinner(f"⏳ Processing Stata command `.{clean_cmd_str}`…"):
            t0 = time.time()
            res = execute_stata_command(clean_cmd_str, df=panel_df)
            elapsed = time.time() - t0

            run_item = {
                "id": f"run_{int(time.time()*1000)}",
                "command": clean_cmd_str,
                "result": res,
                "timestamp": time.strftime("%H:%M:%S"),
                "elapsed": f"{elapsed:.2f}s",
                "status": "success" if not (isinstance(res, dict) and res.get("error")) else "error",
            }
            st.session_state["stata_v2_runs"].append(run_item)

    # 4. Session Action Bar & Tree Controls
    c_tree_title, c_tree_exp, c_tree_col, c_tree_act, c_tree_clr = st.columns([3, 1, 1, 1.2, 1.2])
    with c_tree_title:
        total_runs = len(st.session_state["stata_v2_runs"])
        st.markdown(f"**Session Execution History** ({total_runs} Command{'s' if total_runs != 1 else ''} Run — *Newest First*)")

    with c_tree_exp:
        if st.button("+ Expand All", key="btn_expand_all", use_container_width=True):
            st.session_state["stata_v2_tree_mode"] = "expand_all"
            st.rerun()

    with c_tree_col:
        if st.button("- Collapse All", key="btn_collapse_all", use_container_width=True):
            st.session_state["stata_v2_tree_mode"] = "collapse_all"
            st.rerun()

    with c_tree_act:
        if st.button("⚡ Active Top Only", key="btn_active_only", use_container_width=True):
            st.session_state["stata_v2_tree_mode"] = "active_only"
            st.rerun()

    with c_tree_clr:
        if st.button("🗑️ Clear History", key="btn_clear_history", use_container_width=True, help="Clear all executed commands in this session"):
            st.session_state["stata_v2_runs"] = []
            st.session_state.pop("analysis_session_v2", None)
            st.rerun()

    # 5. Multi-Turn Tree Rendering (REVERSE CHRONOLOGICAL: Run N, N-1, ..., 1)
    runs_list = st.session_state["stata_v2_runs"]

    if not runs_list:
        st.info("No commands executed in this session yet. Type a command above or pick from the library to begin.")
    else:
        # Inject CSS for active-run blue border (prototype parity)
        st.markdown("""
        <style>
        [data-testid="stExpander"].active-run-card > div:first-child {
            border: 2px solid #2563EB !important;
            box-shadow: 0 0 0 2px rgba(37,99,235,0.18) !important;
            border-radius: 8px !important;
        }
        </style>
        """, unsafe_allow_html=True)

        # Enumerate in reverse order so latest run is at top
        for rev_idx, run_obj in enumerate(reversed(runs_list)):
            actual_run_num = len(runs_list) - rev_idx
            is_latest = (rev_idx == 0)

            # Determine expand state based on tree_mode
            if st.session_state["stata_v2_tree_mode"] == "expand_all":
                should_expand = True
            elif st.session_state["stata_v2_tree_mode"] == "collapse_all":
                should_expand = False
            else:  # 'active_only' (default)
                should_expand = is_latest

            run_cmd = run_obj["command"]
            res = run_obj["result"]
            r_id = run_obj["id"]
            r_status = run_obj.get("status", "success")

            # ── Rich Header Badges (prototype parity) ─────────────────────────
            r2_val = None
            f_stat_val = None
            model_type = "Command"
            _cmd_low = run_cmd.lower().strip()

            if isinstance(res, dict):
                r2_val = res.get("r2") or res.get("r2_within")
                f_stat_val = res.get("f_stat")

            if "xtreg" in _cmd_low and ", fe" in _cmd_low:
                model_type = "Fixed Effects (FE)"
            elif "xtreg" in _cmd_low and ", re" in _cmd_low:
                model_type = "Random Effects (RE)"
            elif "regress" in _cmd_low and "xtreg" not in _cmd_low:
                model_type = "Pooled OLS"
            elif "reghdfe" in _cmd_low:
                model_type = "HDFE Regression"
            elif "xtivreg" in _cmd_low:
                model_type = "IV / 2SLS (FE)"
            elif "summarize" in _cmd_low or "sum " in _cmd_low:
                model_type = "Descriptive Stats"
            elif "pwcorr" in _cmd_low:
                model_type = "Correlation Matrix"
            elif "hausman" in _cmd_low:
                model_type = "Hausman Test"
            elif "describe" in _cmd_low or _cmd_low == "des" or _cmd_low == "d":
                model_type = "Variable Codebook"
            elif "tabulate" in _cmd_low or "tab " in _cmd_low:
                model_type = "Frequency Table"
            elif "tabstat" in _cmd_low:
                model_type = "Summary by Group"
            elif "margins" in _cmd_low:
                model_type = "Marginal Effects"
            elif "thesis" in _cmd_low:
                model_type = "Full Thesis Pipeline"

            _active_border = "2px solid #2563EB" if is_latest else "1px solid #E2E8F0"
            _active_shadow = "0 0 0 2px rgba(37,99,235,0.18)" if is_latest else "none"
            _hdr_bg = "#EFF6FF" if is_latest else ("rgba(30,41,59,0.3)" if is_dark else "#F8FAFC")
            _run_badge_color = "#2563EB" if is_latest else ("#94A3B8" if is_dark else "#64748B")
            _status_icon = "●" if r_status == "success" else "✗"
            _status_color = "#059669" if r_status == "success" else "#DC2626"

            # Build header label for expander
            _r2_badge = f" | R² = {r2_val:.3f}" if r2_val is not None else ""
            header_label = f"{'★ LATEST ' if is_latest else ''}Run #{actual_run_num}: .{run_cmd[:60]}{'…' if len(run_cmd)>60 else ''}{_r2_badge} ({run_obj['elapsed']})"

            with st.expander(header_label, expanded=should_expand):
                # ── Rich header info strip inside expander ─────────────────
                _badge_html = f"""
                <div style="display:flex; flex-wrap:wrap; gap:6px; align-items:center; margin-bottom:12px;
                  padding:8px 12px; border-radius:6px; background:{'rgba(37,99,235,0.08)' if is_latest else ('rgba(30,41,59,0.3)' if is_dark else '#F1F5F9')};
                  border:1px solid {'#BFDBFE' if is_latest else ('#334155' if is_dark else '#E2E8F0')};">
                  <span style="font-size:0.72rem; font-weight:700; padding:2px 8px; border-radius:4px;
                    background:{'#2563EB' if is_latest else ('#475569' if is_dark else '#CBD5E1')};
                    color:{'white' if is_latest else ('#E2E8F0' if is_dark else '#475569')};">{'Run #'+str(actual_run_num)+' (Latest)' if is_latest else 'Run #'+str(actual_run_num)}</span>
                  <span style="font-size:0.72rem; font-weight:600; padding:2px 8px; border-radius:4px;
                    background:{'rgba(30,41,59,0.5)' if is_dark else '#E0E7FF'}; color:{'#818CF8' if is_dark else '#4338CA'};">{model_type}</span>
                  {f'<span style="font-size:0.72rem; font-weight:600; padding:2px 8px; border-radius:4px; background:{"rgba(30,41,59,0.5)" if is_dark else "#F0FDF4"}; color:{"#34D399" if is_dark else "#16A34A"};">R² = {r2_val:.3f}</span>' if r2_val is not None else ''}
                  {f'<span style="font-size:0.72rem; font-weight:600; padding:2px 8px; border-radius:4px; background:{"rgba(30,41,59,0.5)" if is_dark else "#FEF3C7"}; color:{"#FBBF24" if is_dark else "#B45309"};">F = {f_stat_val:.2f}</span>' if f_stat_val is not None else ''}
                  <span style="font-size:0.72rem; font-weight:600; padding:2px 8px; border-radius:999px;
                    background:{'rgba(16,185,129,0.15)' if is_dark else '#ECFDF5'}; color:{'#34D399' if is_dark else '#059669'};
                    margin-left:auto;">{_status_icon} {'Success' if r_status == 'success' else 'Error'} ({run_obj['elapsed']})</span>
                </div>
                """
                st.markdown(_badge_html, unsafe_allow_html=True)

                # Row-Level Action Buttons
                c_act1, c_act2, c_act3, _spacer = st.columns([1.4, 1.1, 1.1, 4])
                with c_act1:
                    if st.button("▶ Re-run", key=f"rerun_{r_id}", use_container_width=True, type="primary"):
                        st.session_state["stata_v2_cmd_input"] = run_cmd
                        st.session_state["_trigger_stata_v2_run"] = True
                        st.rerun()
                with c_act2:
                    if st.button("📋 Copy Cmd", key=f"copy_{r_id}", use_container_width=True):
                        st.session_state["stata_v2_cmd_input"] = run_cmd
                        st.toast(f"Copied `.{run_cmd[:40]}` to prompt", icon="📋")
                        st.rerun()
                with c_act3:
                    if st.button("🗑️ Delete", key=f"del_{r_id}", use_container_width=True):
                        st.session_state["stata_v2_runs"] = [r for r in st.session_state["stata_v2_runs"] if r["id"] != r_id]
                        st.rerun()

                st.divider()

                # ── Sub-Section 1: Stata Terminal Output ──────────────────
                with st.expander("📄 Stata Terminal Output", expanded=True):
                    if isinstance(res, dict) and "ascii_output" in res:
                        st.code(res["ascii_output"], language="text")
                    elif isinstance(res, str):
                        st.code(res, language="text")
                    elif isinstance(res, dict) and res.get("error"):
                        st.error(f"Execution Error: {res.get('error')}")
                    else:
                        st.info("No text output returned for this command.")

                # ── Sub-Section 2: Findings & Hypothesis Scorecard ────────
                fin_trans = get_financial_translation(run_cmd)
                _has_findings = bool(fin_trans) and fin_trans != f"Executes econometric evaluation for <code>.{html.escape(run_cmd)}</code>."

                with st.expander("💡 Empirical Findings & Hypothesis Scorecard", expanded=is_latest):
                    # Financial translation block
                    st.markdown(f"""
                    <div style="background:{'rgba(2,132,199,0.08)' if is_dark else '#F0F9FF'}; border:1px solid {'#1e40af' if is_dark else '#BAE6FD'}; padding:10px 14px; border-radius:7px; margin-bottom:10px; font-size:0.83rem; color:{'#e2e8f0' if is_dark else '#0C4A6E'};"><strong>📖 Econometric Translation:</strong> {fin_trans}</div>
                    """, unsafe_allow_html=True)

                    # Hypothesis metric grid (if regression result present)
                    if isinstance(res, dict) and r2_val is not None:
                        _coefs = res.get("coefficients", {})
                        _prof_sign = None
                        _tang_sign = None
                        for k, v in _coefs.items():
                            if "profitability" in k.lower() or k.lower() in ("profitability", "prof", "roa"):
                                _prof_sign = v
                            if "tangibility" in k.lower() or k.lower() in ("tangibility", "tang"):
                                _tang_sign = v

                        _m1, _m2, _m3, _m4 = st.columns(4)
                        with _m1:
                            _pot = "Supported" if (_prof_sign is not None and _prof_sign < 0) else "—"
                            _pot_color = accent_green if _pot == "Supported" else ("#F59E0B" if is_dark else "#D97706")
                            st.markdown(f"""<div style="background:{'rgba(30,41,59,0.5)' if is_dark else '#F8FAFC'}; border:1px solid {'#334155' if is_dark else '#E2E8F0'}; border-radius:6px; padding:10px; text-align:center;">
                            <div style="font-size:0.85rem; font-weight:700; color:{_pot_color};">{_pot}</div>
                            <div style="font-size:0.68rem; color:{lbl_col}; margin-top:2px;">Pecking Order (Prof &lt; 0)</div></div>""", unsafe_allow_html=True)
                        with _m2:
                            _stage_dynamic = "Non-Monotonic" if "corplifestage" in run_cmd.lower() else "—"
                            _sd_color = accent_indigo if _stage_dynamic != "—" else lbl_col
                            st.markdown(f"""<div style="background:{'rgba(30,41,59,0.5)' if is_dark else '#F8FAFC'}; border:1px solid {'#334155' if is_dark else '#E2E8F0'}; border-radius:6px; padding:10px; text-align:center;">
                            <div style="font-size:0.85rem; font-weight:700; color:{_sd_color};">{_stage_dynamic}</div>
                            <div style="font-size:0.68rem; color:{lbl_col}; margin-top:2px;">Life Stage Dynamic</div></div>""", unsafe_allow_html=True)
                        with _m3:
                            _r2_display = f"{r2_val:.3f}" if r2_val is not None else "—"
                            st.markdown(f"""<div style="background:{'rgba(30,41,59,0.5)' if is_dark else '#F8FAFC'}; border:1px solid {'#334155' if is_dark else '#E2E8F0'}; border-radius:6px; padding:10px; text-align:center;">
                            <div style="font-size:0.95rem; font-weight:800; color:{txt_col}; font-family:'JetBrains Mono',monospace;">{_r2_display}</div>
                            <div style="font-size:0.68rem; color:{lbl_col}; margin-top:2px;">R² (Within / Overall)</div></div>""", unsafe_allow_html=True)
                        with _m4:
                            _f_display = f"{f_stat_val:.2f}***" if f_stat_val is not None else "—"
                            st.markdown(f"""<div style="background:{'rgba(30,41,59,0.5)' if is_dark else '#F8FAFC'}; border:1px solid {'#334155' if is_dark else '#E2E8F0'}; border-radius:6px; padding:10px; text-align:center;">
                            <div style="font-size:0.85rem; font-weight:700; color:{accent_blue};">{_f_display}</div>
                            <div style="font-size:0.68rem; color:{lbl_col}; margin-top:2px;">F-Statistic</div></div>""", unsafe_allow_html=True)
                    else:
                        st.caption("Run a regression (`xtreg`, `regress`) to unlock the hypothesis scorecard.")

# =============================================================================
# TAB 2: ESTTAB MULTI-MODEL COMPARISON MATRIX
# =============================================================================
with tab_esttab:
    st.markdown("### 📑 Multi-Model Publication Comparison (esttab / outreg2)")
    st.caption("Side-by-side comparison of all regression models estimated in this active session.")

    df_models = get_stored_models_table()

    if df_models.empty:
        st.info("No regression models stored in active session yet. Run regression commands (e.g. `regress`, `xtreg fe`, `xtreg re`) in Tab 1 to compare.")
    else:
        st.dataframe(df_models, use_container_width=True)

        c_dl1, c_dl2, c_dl3 = st.columns(3)
        with c_dl1:
            latex_str = generate_esttab_latex()
            st.download_button(
                "📥 Download LaTeX (.tex)",
                data=latex_str,
                file_name="stata_publication_models.tex",
                mime="text/plain",
                use_container_width=True,
            )
        with c_dl2:
            tmp_docx = os.path.join(os.getcwd(), "scratch", "stata_publication_table.docx")
            os.makedirs(os.path.dirname(tmp_docx), exist_ok=True)
            docx_res = generate_esttab_docx(tmp_docx)
            if docx_res and os.path.exists(tmp_docx):
                with open(tmp_docx, "rb") as f_docx:
                    st.download_button(
                        "📥 Download Word (.docx)",
                        data=f_docx.read(),
                        file_name="stata_publication_table.docx",
                        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                        use_container_width=True,
                    )
            else:
                st.button("📥 Download Word (.docx) [Unavailable]", disabled=True, use_container_width=True)
        with c_dl3:
            csv_buf = io.StringIO()
            df_models.to_csv(csv_buf, index=True)
            st.download_button(
                "📥 Download CSV / Excel",
                data=csv_buf.getvalue(),
                file_name="stata_publication_models.csv",
                mime="text/csv",
                use_container_width=True,
            )


# =============================================================================
# TAB 3: COEFFICIENT FOREST PLOT (COEFPLOT)
# =============================================================================
with tab_coefplot:
    st.markdown("### 📈 Visual Coefficient Plots (coefplot)")
    st.caption("Point estimates and 95% confidence intervals across estimated models.")

    _df_models_coef = get_stored_models_table()
    if _df_models_coef.empty:
        st.info("No regression models estimated yet. Run `regress`, `xtreg fe`, or `xtreg re` commands in Tab 1 to generate coefficient plots.")
    else:
        coef_res = execute_stata_command("coefplot, drop(_cons) xline(0)", df=panel_df)
        spec = coef_res.get("chart_spec", {})

    if not _df_models_coef.empty and spec and spec.get("categories"):
        cats = spec["categories"]
        vals = spec["series"][0]["values"]
        lows = spec["error_bars"]["low"]
        highs = spec["error_bars"]["high"]

        # Calculate error bar deltas
        err_minus = [v - l for v, l in zip(vals, lows)]
        err_plus = [h - v for v, h in zip(vals, highs)]

        fig_coef = go.Figure()
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
                thickness=1.5,
                width=4,
            ),
        ))

        layout_func = plotly_layout_dark if is_dark else plotly_layout_light
        fig_coef.update_layout(**layout_func(title="Coefficient Estimates (95% Confidence Intervals)", height=450))
        st.plotly_chart(fig_coef, use_container_width=True)
    else:
        st.info("No estimated models available for visual comparison. Run models in Tab 1 to generate coefficient plots.")


# =============================================================================
# TAB 4: REPLICATION BUNDLE EXPORT (.DTA & .DO)
# =============================================================================
with tab_export:
    st.markdown("### 💾 1-Click Stata Replication Bundle (.dta & .do)")
    st.caption("Download the cleaned panel dataset and a self-contained master Stata do-file.")

    c_exp1, c_exp2 = st.columns(2)

    with c_exp1:
        st.markdown("#### 📜 Master Stata Do-File (`replication_master.do`)")
        do_code = f"""* ==============================================================================
* LifeCycle Leverage — Stata Empirical Master Replication Script
* Generated automatically on {time.strftime('%Y-%m-%d %H:%M:%S')}
* ==============================================================================
clear all
set more off

* 1. Load panel dataset
use "sample_manufacturing_panel.dta", clear

* 2. Set panel longitudinal structure
xtset company_code year

* 3. Descriptive Statistics & Diagnostics
summarize leverage profitability tangibility log_size, detail
pwcorr leverage profitability tangibility log_size, sig star(0.05)

* 4. Estimate Core Econometric Models
regress leverage profitability tangibility log_size
estimates store m1_ols

xtreg leverage profitability tangibility log_size, fe cluster(company_code)
estimates store m2_fe

xtreg leverage profitability tangibility log_size, re
estimates store m3_re

* 5. Model Selection Tests
hausman m2_fe m3_re

* 6. Export Publication Matrix
esttab m1_ols m2_fe m3_re using "table_results.tex", replace se r2 star(* 0.10 ** 0.05 *** 0.01)
"""
        st.code(do_code, language="stata")
        st.download_button(
            "📥 Download `replication_master.do`",
            data=do_code,
            file_name="replication_master.do",
            mime="text/plain",
            use_container_width=True,
        )

    with c_exp2:
        st.markdown("#### 📊 Cleaned Panel Dataset (`.dta`)")
        st.markdown("""
        Cleaned, balanced panel dataset formatted with 118 Stata schema parity.
        Contains all winsorized ratios, Dickinson lifecycle stages, and macroeconomic dummy indicators.
        """)
        dta_buf = io.BytesIO()
        try:
            df_stata = prepare_df_for_stata(panel_df)
            df_stata.to_stata(dta_buf, write_index=False, version=118)
            st.download_button(
                "📥 Download Stata `.dta` Dataset",
                data=dta_buf.getvalue(),
                file_name="sample_manufacturing_panel.dta",
                mime="application/x-stata-dta",
                use_container_width=True,
            )
        except Exception as e:
            st.warning(f"Could not convert to .dta: {e}")
