"""
LifeCycle Leverage Dashboard — Main entrypoint.
Streamlit multipage app for analyzing capital structure across corporate life stages.
"""

import os
import streamlit as st

_APP_VERSION = open("VERSION").read().strip() if os.path.exists("VERSION") else "dev"

st.set_page_config(
    page_title="LifeCycle Leverage",
    page_icon=":material/analytics:",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Theme: light (default) or dark. Toggle lives on the Settings page.
if "theme" not in st.session_state:
    st.session_state.theme = "light"

# Load theme CSS. style_light.css is the original; style_dark.css is the DataV2-era refresh.
_theme = st.session_state.theme if st.session_state.theme in ("light", "dark") else "light"
_css_filename = f"style_{_theme}.css"
css_path = os.path.join(os.path.dirname(__file__), "assets", _css_filename)
if os.path.exists(css_path):
    with open(css_path) as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# ── Authentication ────────────────────────────────────────────────────────────
import bcrypt as _bcrypt

try:
    _creds = {"usernames": {
        k: dict(v) for k, v in st.secrets.get("credentials", {}).get("usernames", {}).items()
    }}
except Exception:
    _creds = {"usernames": {}}

def _login():
    st.markdown("### LifeCycle Leverage — Sign In")
    with st.form("login_form"):
        _u = st.text_input("Username")
        _p = st.text_input("Password", type="password")
        if st.form_submit_button("Login", type="primary"):
            _user = _creds["usernames"].get(_u)
            if _user:
                try:
                    _ok = _bcrypt.checkpw(_p.encode(), _user["password"].encode())
                except Exception:
                    _ok = False
            else:
                _ok = False
            if _ok:
                st.session_state["authentication_status"] = True
                st.session_state["username"] = _u
                st.session_state["name"] = _user.get("name", _u)
                st.rerun()
            else:
                st.error("Username or password incorrect.")

if not st.session_state.get("authentication_status"):
    _login()
    st.stop()

_username = st.session_state.get("username", "")
_role = _creds["usernames"].get(_username, {}).get("role", "viewer")
st.session_state["user"] = {
    "name": st.session_state.get("name", _username),
    "username": _username,
    "role": _role,
}

import uuid as _uuid
if "session_id" not in st.session_state:
    st.session_state["session_id"] = _uuid.uuid4().hex[:12]

# Guest self-identification — blocks page render until viewer enters their name
if _role == "viewer" and "guest_display_name" not in st.session_state:
    st.markdown("### Welcome to LifeCycle Leverage")
    with st.form("guest_id_form"):
        st.info("Please enter your name so your session is identifiable in the activity log.")
        _dname = st.text_input("Your name or initials", placeholder="e.g. Prof. Dawar")
        if st.form_submit_button("Continue to Dashboard") and _dname.strip():
            st.session_state["guest_display_name"] = _dname.strip()
            st.rerun()
    st.stop()
# ─────────────────────────────────────────────────────────────────────────────

import db
from cmie.streamlit_import import render_cmie_sidebar_block
from helpers import ensure_session_state, is_india_panel

db.ensure_app_tables()  # idempotent — creates audit_log / user_preferences / user_model_runs if missing

# ── Panel options ──
_panel_opts = ["run3", "latest", "thesis", "us_av_2024"]
_panel_labels_map = {
    "run3":       "(2001-25)_April26",
    "latest":     "Latest (2001–present)",
    "thesis":     "Thesis (2001–2024)",
    "us_av_2024": "US S&P Sample",
}
# Honour ?panel= URL param on first load (shareability); sidebar selectbox owns it after that.
if "panel_mode" not in st.session_state:
    _url_panel = st.query_params.get("panel", "run3")
    st.session_state["panel_mode"] = _url_panel if _url_panel in _panel_opts else "run3"
# _qp_panel is defined after the sidebar selectbox renders (see sidebar block below)

# ── Restore saved preferences (theme only — panel is URL-driven, filters are panel-derived) ──
if "prefs_loaded" not in st.session_state:
    _saved = db.load_user_prefs(_username, "app")
    if _saved:
        if "theme" in _saved:
            st.session_state["theme"] = _saved["theme"]
    st.session_state["prefs_loaded"] = True

if "login_logged" not in st.session_state:
    db.log_user_login(_username, _role, st.session_state["session_id"])
    st.session_state["login_logged"] = True

# ── Initialize session state defaults (shared with every page) ──
ensure_session_state()

# ── Sidebar: Global filters ──
from helpers import PANEL_LABELS as panel_label_map
with st.sidebar:
    _sb_hcol1, _sb_hcol2 = st.columns([3, 1])
    with _sb_hcol1:
        st.markdown("# LifeCycle Leverage")
    with _sb_hcol2:
        _cur_t = st.session_state.get("theme", "light")
        _t_icon = "🌙" if _cur_t == "light" else "☀️"
        if st.button(_t_icon, key="quick_theme_toggle", help=f"Switch to {'Dark' if _cur_t == 'light' else 'Light'} theme"):
            _next_t = "dark" if _cur_t == "light" else "light"
            st.session_state.theme = _next_t
            if _username:
                db.save_user_pref(_username, "app", {"theme": _next_t})
            st.rerun()
    st.divider()

    # Dataset selectbox — native Streamlit widget triggers proper rerun + state propagation
    _panel_display_opts = ["(2001-25)_April26", "Latest (2001–present)", "Thesis (2001–2024)", "US S&P Sample"]
    _panel_keys         = ["run3",               "latest",                "thesis",              "us_av_2024"]
    _cur_idx = _panel_keys.index(st.session_state.get("panel_mode", "run3"))
    _selected_label = st.selectbox(
        "Dataset",
        options=_panel_display_opts,
        index=_cur_idx,
        key="panel_selectbox",
    )
    _qp_panel = _panel_keys[_panel_display_opts.index(_selected_label)]
    st.session_state["panel_mode"] = _qp_panel

    # Sync year_range BEFORE the year slider (must happen after selectbox sets _qp_panel)
    if st.session_state.filters.get("_last_panel") != _qp_panel:
        _yr_init_min, _yr_init_max = db.get_year_range(_qp_panel)
        st.session_state.filters["year_range"] = (_yr_init_min, _yr_init_max)
        st.session_state.filters["_last_panel"] = _qp_panel
    st.session_state.filters["panel_mode"] = _qp_panel

    companies_df = db.get_companies(_qp_panel)
    all_stages = db.get_life_stages()
    all_industries = db.get_industry_groups(_qp_panel)
    yr_min, yr_max = db.get_year_range(_qp_panel)

    # Company search
    selected_companies = st.multiselect(
        "Companies",
        options=companies_df["company_name"].tolist(),
        default=[],
        placeholder="All companies",
    )
    if selected_companies:
        codes = companies_df[companies_df["company_name"].isin(selected_companies)]["company_code"].tolist()
        st.session_state.filters["company_codes"] = codes
    else:
        st.session_state.filters["company_codes"] = []

    # Year range — bounds derived from the active panel's vintage range
    # (Thesis: 2001-2024, Latest: 2001-2025, (2001-25)_April26: 2001-2025).
    year_range = st.slider(
        "Year Range",
        min_value=yr_min,
        max_value=yr_max,
        value=st.session_state.filters["year_range"],
        help=f"Bounds reflect the active panel's data range ({yr_min}-{yr_max}). "
             "Changing panel preserves your narrower selection where possible.",
    )
    st.session_state.filters["year_range"] = year_range
    if year_range[0] > yr_min or year_range[1] < yr_max:
        st.caption(f"_Panel range: {yr_min}-{yr_max}_ (currently filtered to {year_range[0]}-{year_range[1]})")

    # Life stage
    selected_stages = st.multiselect(
        "Life Stages",
        options=all_stages,
        default=[],
        placeholder="All stages",
    )
    st.session_state.filters["life_stages"] = selected_stages

    # Industry group
    selected_industries = st.multiselect(
        "Industries",
        options=all_industries,
        default=[],
        placeholder="All industries",
    )
    st.session_state.filters["industry_groups"] = selected_industries

    # Event period toggles
    st.markdown("**Event Periods**")
    gfc = st.checkbox("GFC (2008-09)", value=False, help="Global Financial Crisis")
    if is_india_panel(_qp_panel):
        ibc = st.checkbox("IBC (2016+)", value=False, help="Insolvency & Bankruptcy Code")
    else:
        ibc = False
        st.caption("_IBC dummy: India-only — not applicable for US panel_")
    covid = st.checkbox("COVID (2020-21)", value=False, help="COVID-19 pandemic")
    st.session_state.filters["events"] = {"gfc": gfc, "ibc": ibc, "covid": covid}

    st.markdown("**AI Settings**")
    st.session_state["p19_citations"] = st.checkbox(
        "Academic citations in AI responses",
        value=st.session_state.get("p19_citations", False),
        key="global_citations",
        help="When on, all AI analysis (chat, interpretations, board deck) cites Rajan & Zingales, Myers, Jensen & Meckling, etc.",
    )

    st.divider()
    meta = db.get_db_metadata(_qp_panel)
    if _qp_panel == "latest":
        panel_suffix = " • includes CMIE 2025"
    elif _qp_panel == "us_av_2024":
        panel_suffix = " • US S&P Sample"
    else:
        panel_suffix = " • thesis only"
    st.caption(f"{meta['total_firms']} firms | {meta['total_obs']:,} obs | {meta['year_min']}–{meta['year_max']}{panel_suffix}")
    _theme = st.session_state.get("theme", "light")
    st.caption(f"Theme: **{_theme}** · change in Settings")

    # CMIE API Live sidebar hidden — API integration is a separate capability handled in its own track.
    # To re-enable: uncomment the two lines below.
    # if db.is_cmie_lab_enabled():
    #     render_cmie_sidebar_block(key_prefix="cmie_sidebar")

    # Auto-save theme preference (panel is URL-driven; filters are panel-derived, not saved)
    if _username:
        db.save_user_pref(_username, "app", {
            "theme": st.session_state.get("theme", "light"),
        })

# ── Navigation ──
overview  = st.Page("pages/0_overview.py",  title="Overview",   icon=":material/info:", default=True)
dashboard = st.Page("pages/1_dashboard.py", title="Dashboard", icon=":material/dashboard:")
benchmarks = st.Page("pages/2_peer_benchmarks.py", title="Peer Benchmarks", icon=":material/compare_arrows:")
scenarios = st.Page("pages/3_scenarios.py", title="Scenarios", icon=":material/tune:")
bulk_upload = st.Page("pages/4_bulk_upload.py", title="Bulk Upload", icon=":material/upload_file:")
data_explorer = st.Page("pages/5_data_explorer.py", title="Data Explorer", icon=":material/table_chart:")
settings = st.Page("pages/6_settings.py", title="Settings", icon=":material/settings:")
# knowledge_graph   = st.Page("pages/7_knowledge_graph.py",     title="Know. GraphV1 (WIP)", icon=":material/hub:")  # temporarily hidden
life_stage_dynamics = st.Page("pages/20_life_stage_dynamics.py", title="Life Stage Dynamics", icon=":material/timeline:")
econometrics        = st.Page("pages/8_econometrics.py",         title="Econometrics Lab",    icon=":material/functions:")
ml_models           = st.Page("pages/9_ml_models.py",           title="ML Models",           icon=":material/model_training:")
forecasting         = st.Page("pages/10_forecasting.py",        title="Forecasting",         icon=":material/trending_up:")
clustering          = st.Page("pages/11_clustering.py",         title="Clustering",          icon=":material/bubble_chart:")
transitions         = st.Page("pages/12_transitions.py",        title="Transitions",         icon=":material/swap_horiz:")
advanced_econ       = st.Page("pages/13_advanced_econometrics.py", title="Advanced Econometrics", icon=":material/science:")
workbench           = st.Page("pages/14_workbench.py",          title="Workbench",           icon=":material/construction:")
interaction_effects = st.Page("pages/15_interaction_effects.py", title="Interaction Effects", icon=":material/join_inner:")

admin_activity      = st.Page("pages/16_admin_activity.py",    title="Activity Log",        icon=":material/monitoring:")
board_deck          = st.Page("pages/17_board_export.py",      title="Board Deck",          icon=":material/description:")
# company_navigator = st.Page("pages/18_company_navigator.py", title="Company Navigator", icon=":material/explore:")  # temporarily hidden
ai_assistant        = st.Page("pages/19_ai_assistant.py",       title="AI Assistant",        icon=":material/smart_toy:")
# knowledge_graph2  = st.Page("pages/21_knowledge_graph2.py",  title="Know. GraphV2 (WIP)", icon=":material/account_tree:")  # temporarily hidden
nav = st.navigation({
    "": [
        overview, dashboard, data_explorer, benchmarks,
        life_stage_dynamics, transitions,
        scenarios, econometrics, advanced_econ, interaction_effects,
        ml_models, forecasting, clustering,
        ai_assistant, board_deck,
    ],
    "Admin & Tools": [
        admin_activity, settings,
        workbench, bulk_upload,
    ],
})

# ── Fixed top header bar — pure HTML overlay, no CSS selector fragility ──
from datetime import datetime, timezone as _tz
_panel_display = panel_label_map.get(st.session_state.get("panel_mode", "latest"), "Latest")
_user_obj     = st.session_state.get("user", {})
_display_name = _user_obj.get("name", _user_obj.get("username", ""))
if _user_obj.get("role") == "viewer":
    _guest_name = st.session_state.get("guest_display_name", "")
    if _guest_name:
        _display_name = _guest_name
_role_display = _user_obj.get("role", "viewer").title()
_now_str      = datetime.now(_tz.utc).strftime("%a %d %b %Y · %H:%M UTC")

_header_bg   = "rgba(255, 255, 255, 0.9)" if _theme == "light" else "rgba(16, 20, 30, 0.9)"
_header_text = "#0F172A" if _theme == "light" else "#F8FAFC"
_header_sub  = "#64748B" if _theme == "light" else "#94A3B8"
_accent_grad = "linear-gradient(135deg, #4F46E5, #0891B2)" if _theme == "light" else "linear-gradient(135deg, #6366F1, #06B6D4)"

st.markdown(f"""
<div id="lc-navbar" style="
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    z-index: 1000001;
    height: 64px;
    background: {_header_bg};
    backdrop-filter: blur(16px);
    -webkit-backdrop-filter: blur(16px);
    border-bottom: 1px solid {'rgba(226, 232, 240, 0.8)' if _theme == 'light' else 'rgba(255, 255, 255, 0.08)'};
    box-shadow: {'0 2px 10px rgba(0,0,0,0.04)' if _theme == 'light' else '0 4px 20px rgba(0,0,0,0.35)'};
    padding: 0 1.75rem;
    display: flex;
    align-items: center;
    gap: 1.5rem;
    font-size: 14px;
    color: {_header_text};
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
">
    <span style="font-family:'Plus Jakarta Sans', sans-serif; font-weight:800; background:{_accent_grad}; -webkit-background-clip:text; -webkit-text-fill-color:transparent; font-size:18px; white-space:nowrap; display:flex; align-items:center; gap:6px;">
        💎 LifeCycle Leverage<span style="font-size:11px;color:{_header_sub};font-weight:600;margin-left:6px;border:1px solid {'#e2e8f0' if _theme == 'light' else 'rgba(255,255,255,0.1)'};padding:2px 6px;border-radius:6px;-webkit-text-fill-color:initial;">v{_APP_VERSION}</span>
    </span>
    <span style="background:{'rgba(79, 70, 229, 0.1)' if _theme == 'light' else 'rgba(99, 102, 241, 0.15)'};color:{'#4F46E5' if _theme == 'light' else '#818CF8'};border:1px solid {'rgba(79, 70, 229, 0.3)' if _theme == 'light' else 'rgba(99, 102, 241, 0.3)'};border-radius:8px;padding:4px 10px;font-size:13px;font-weight:600;white-space:nowrap;">
        🏷️&nbsp;{_panel_labels_map.get(_qp_panel, _qp_panel)}
    </span>
    <span style="white-space:nowrap; color:{_header_sub};"><strong>{_display_name}</strong> &middot; <span style="text-transform:capitalize;">{_role_display}</span></span>
    <span style="margin-left:auto; color:{_header_sub}; font-size:13px; font-family:'JetBrains Mono', monospace; white-space:nowrap;">{_now_str}</span>
    <button
        onclick="(function(){{var btns=document.querySelectorAll('section[data-testid=stSidebar] button');for(var b of btns){{if(b.innerText.includes('Sign out')){{b.click();return;}}}}}})()"
        style="
            background: {'rgba(244,63,94,0.08)' if _theme == 'light' else 'rgba(244,63,94,0.12)'};
            color: {'#E11D48' if _theme == 'light' else '#FB7185'};
            border: 1px solid {'rgba(225,29,72,0.25)' if _theme == 'light' else 'rgba(244,63,94,0.3)'};
            font-weight: 600;
            font-size: 13px;
            border-radius: 8px;
            padding: 0 14px;
            height: 34px;
            cursor: pointer;
            white-space: nowrap;
            transition: all 0.2s ease;
        "
        onmouseover="this.style.background='rgba(244,63,94,0.2)'"
        onmouseout="this.style.background={'\"rgba(244,63,94,0.08)\"' if _theme == 'light' else '\"rgba(244,63,94,0.12)\"'}"
    >Sign Out</button>
</div>
<style>
/* ROW 2: Streamlit native header pushed below our 64px navbar */
header[data-testid="stHeader"] {{
    position: fixed !important;
    top: 64px !important;
    height: 48px !important;
    min-height: 48px !important;
    left: 0 !important;
    right: 0 !important;
    z-index: 1000000 !important;
    background: {_header_bg} !important;
    border-bottom: 1px solid #E5E7EB !important;
    padding: 0 !important;
    overflow: visible !important;
}}
/* Sidebar starts below both rows (64 + 48 = 112px) */
section[data-testid="stSidebar"] {{
    top: 112px !important;
    height: calc(100vh - 112px) !important;
}}
/* Main content below both rows */
.block-container {{
    padding-top: 130px !important;
}}
/* Sidebar collapse arrow (<<) — positioned below both rows, above everything */
button[data-testid="stSidebarCollapseButton"] {{
    top: calc(112px + 0.5rem) !important;
    z-index: 1000002 !important;
}}
/* Sidebar expand arrow (>>) — positioned below both rows, above everything */
button[data-testid="collapsedControl"] {{
    top: calc(112px + 0.5rem) !important;
    z-index: 1000002 !important;
    left: 0.5rem !important;
}}
/* Ensure any popover/dropdown appears above the fixed navbar */
[data-baseweb="popover"] {{
    z-index: 1000010 !important;
}}
/* Move our sidebar filter widgets (Dataset, Companies, etc.) ABOVE the nav links */
[data-testid="stSidebarUserContent"] {{
    display: flex !important;
    flex-direction: column !important;
}}
[data-testid="stSidebarUserContent"] > div:has(nav) {{
    order: 100 !important;
}}
[data-testid="stSidebarUserContent"] > div:not(:has(nav)) {{
    order: 1 !important;
}}
</style>
""", unsafe_allow_html=True)

# Re-affirm panel in session_state and filters after sidebar may have touched year_range.
st.session_state["panel_mode"] = _qp_panel
st.session_state.filters["panel_mode"] = _qp_panel

nav.run()
