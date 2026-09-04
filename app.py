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

# ── Secure LeverageDebtAI authentication ───────────────────────────────────────
import auth as _auth

try:
    _legacy_creds = {
        k: dict(v) for k, v in st.secrets.get("credentials", {}).get("usernames", {}).items()
    }
except Exception:
    _legacy_creds = {}

_auth.ensure_auth_tables()
_auth.bootstrap_legacy_users(_legacy_creds)


def _complete_login(user):
    st.session_state["authentication_status"] = True
    st.session_state["auth_user"] = user
    st.session_state["username"] = user["username"]
    st.session_state["name"] = user.get("name") or user["username"]
    st.session_state["user"] = {
        "name": user.get("name") or user["username"],
        "username": user["username"],
        "role": user.get("role", "viewer"),
    }
    st.session_state.pop("auth_step", None)
    st.rerun()


def _login():
    st.markdown(
        """
        <style>
        /* Sleek Ultra-Compact Centered Auth Frame (Zero Scroll) */
        html, body, .stApp, [data-testid="stAppViewContainer"], [data-testid="stMain"], section.main {
            background: #060b13 !important;
            background-image: 
                radial-gradient(at 50% 0%, rgba(56, 189, 248, 0.14) 0px, transparent 55%),
                radial-gradient(at 100% 100%, rgba(99, 102, 241, 0.12) 0px, transparent 50%),
                radial-gradient(at 0% 100%, rgba(16, 185, 129, 0.08) 0px, transparent 50%) !important;
            color: #f1f5f9 !important;
            height: 100vh !important;
            max-height: 100vh !important;
            overflow: hidden !important;
        }
        [data-testid="stSidebar"], [data-testid="collapsedControl"], [data-testid="stSidebarNav"], header[data-testid="stHeader"] {
            display: none !important;
        }
        section.main {
            display: flex !important;
            align-items: center !important;
            justify-content: center !important;
        }
        html body .stApp div[data-testid="stMainBlockContainer"],
        html body .stApp div[data-testid="block-container"],
        html body .stApp .main .block-container,
        [data-testid="stMainBlockContainer"] {
            max-width: 390px !important;
            width: 390px !important;
            margin: auto !important;
            padding: 22px 24px 16px 24px !important;
            background: #0d1527 !important;
            border: 1px solid rgba(56, 189, 248, 0.25) !important;
            border-radius: 16px !important;
            box-shadow: 0 20px 50px -10px rgba(0, 0, 0, 0.85), 0 0 30px rgba(56, 189, 248, 0.08) !important;
        }
        .auth-brand-badge {
            display: inline-flex;
            align-items: center;
            gap: 6px;
            padding: 2px 10px;
            background: rgba(56, 189, 248, 0.12);
            border: 1px solid rgba(56, 189, 248, 0.3);
            border-radius: 16px;
            color: #38bdf8;
            font-size: 0.68rem;
            font-weight: 700;
            letter-spacing: 0.08em;
            text-transform: uppercase;
            margin-bottom: 6px;
        }
        .auth-title,
        html body .stApp h1.auth-title,
        html body .stApp .auth-title {
            font-size: 1.35rem !important;
            font-weight: 800 !important;
            letter-spacing: -0.03em !important;
            color: #ffffff !important;
            margin: 0 0 2px 0 !important;
            line-height: 1.15 !important;
        }
        .auth-subtitle,
        html body .stApp .auth-subtitle {
            color: #94a3b8 !important;
            font-size: 0.78rem !important;
            line-height: 1.35 !important;
            margin-bottom: 12px !important;
        }
        /* Pill Segmented Switcher for Sign In / Create Account */
        div[data-testid="stRadio"] div[role="radiogroup"] {
            display: flex !important;
            width: 100% !important;
            gap: 6px !important;
            background: #020617 !important;
            padding: 3px !important;
            border-radius: 10px !important;
            border: 1px solid rgba(148, 163, 184, 0.2) !important;
            margin-bottom: 12px !important;
        }
        div[data-testid="stRadio"] div[role="radiogroup"] > label {
            flex: 1 !important;
            text-align: center !important;
            padding: 6px 10px !important;
            border-radius: 7px !important;
            background: transparent !important;
            cursor: pointer !important;
            margin: 0 !important;
            justify-content: center !important;
            border: 1px solid transparent !important;
            white-space: nowrap !important;
        }
        div[data-testid="stRadio"] div[role="radiogroup"] > label:has(input:checked) {
            background: rgba(56, 189, 248, 0.18) !important;
            border: 1px solid rgba(56, 189, 248, 0.45) !important;
            box-shadow: 0 2px 6px rgba(0, 0, 0, 0.3) !important;
        }
        div[data-testid="stRadio"] div[role="radiogroup"] > label span,
        div[data-testid="stRadio"] div[role="radiogroup"] > label p,
        div[data-testid="stRadio"] div[role="radiogroup"] > label div {
            color: #94a3b8 !important;
            font-size: 0.80rem !important;
            font-weight: 600 !important;
            white-space: nowrap !important;
        }
        div[data-testid="stRadio"] div[role="radiogroup"] > label:has(input:checked) span,
        div[data-testid="stRadio"] div[role="radiogroup"] > label:has(input:checked) p,
        div[data-testid="stRadio"] div[role="radiogroup"] > label:has(input:checked) div {
            color: #38bdf8 !important;
            font-weight: 700 !important;
        }
        div[data-testid="stRadio"] div[role="radiogroup"] input[type="radio"],
        div[data-testid="stRadio"] div[role="radiogroup"] > label > div:first-child:not(:only-child) {
            display: none !important;
        }
        [data-testid="stForm"] {
            background: transparent !important;
            border: none !important;
            padding: 0 !important;
            box-shadow: none !important;
        }
        [data-testid="stForm"] label, [data-testid="stTextInput"] label {
            color: #e2e8f0 !important;
            font-size: 0.78rem !important;
            font-weight: 600 !important;
            margin-bottom: 2px !important;
        }
        [data-testid="stTextInput"] input {
            background: #020617 !important;
            color: #f8fafc !important;
            border: 1px solid rgba(148, 163, 184, 0.28) !important;
            border-radius: 8px !important;
            padding: 7px 11px !important;
            font-size: 0.86rem !important;
        }
        [data-testid="stTextInput"] input::placeholder {
            color: #64748b !important;
            opacity: 1 !important;
        }
        [data-testid="stTextInput"] input:focus {
            border-color: #38bdf8 !important;
            box-shadow: 0 0 0 1px #38bdf8 !important;
        }
        [data-testid="stButton"] button, [data-testid="stFormSubmitButton"] button {
            border-radius: 8px !important;
            font-weight: 700 !important;
            font-size: 0.86rem !important;
            min-height: 2.3rem !important;
            margin-top: 6px !important;
            background: linear-gradient(135deg, #0284c7 0%, #0369a1 100%) !important;
            border: 1px solid rgba(56, 189, 248, 0.4) !important;
            color: #ffffff !important;
            transition: all 0.2s ease !important;
        }
        [data-testid="stButton"] button:hover, [data-testid="stFormSubmitButton"] button:hover {
            transform: translateY(-1px);
            box-shadow: 0 6px 18px rgba(2, 132, 199, 0.35) !important;
            border-color: #38bdf8 !important;
        }
        .auth-footer-note {
            text-align: center;
            font-size: 0.70rem;
            color: #64748b;
            margin-top: 10px;
            letter-spacing: 0.02em;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        <div style="text-align:center;">
            <div class="auth-brand-badge">⚡ LeverageDebtAI · Powered by EOLABS.IN</div>
            <h1 class="auth-title">Welcome Back</h1>
            <div class="auth-subtitle">Evidence-led debt &amp; capital structure intelligence</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    step = st.session_state.get("auth_step", "auth_card")

    if step == "auth_card":
        auth_tab = st.radio(
            "Access Mode",
            ["Sign In", "Create Account"],
            horizontal=True,
            label_visibility="collapsed",
        )

        if auth_tab == "Sign In":
            with st.form("login_form"):
                identifier = st.text_input("Username or email", placeholder="username or user@domain.com", autocomplete="off")
                password = st.text_input("Password", type="password", placeholder="Enter password", autocomplete="off")
                submitted = st.form_submit_button("Sign In →", type="primary", use_container_width=True)
            if submitted:
                user = _auth.authenticate(identifier, password)
                if user:
                    _complete_login(user)
                else:
                    st.error("Invalid credentials. Please verify your username/email and password.")

        else:
            with st.form("enrollment_form"):
                username = st.text_input("Username", placeholder="e.g. jsmith", help="3–30 lowercase letters, numbers, dots, dashes.", autocomplete="off")
                email = st.text_input("Email address", placeholder="name@domain.com", autocomplete="off")
                phone = st.text_input("Phone number", placeholder="+1 (555) 019-2834", autocomplete="off")
                submitted = st.form_submit_button("Send Verification Code →", type="primary", use_container_width=True)
            if submitted:
                try:
                    user = _auth.enroll_user(username, email, phone)
                    _auth.issue_email_code(user["id"])
                    st.session_state["pending_auth_user"] = user
                    st.session_state["auth_step"] = "verify"
                    st.rerun()
                except _auth.AuthValidationError as error:
                    st.error(str(error))
                except RuntimeError:
                    st.error("Email delivery service temporarily unavailable. Please try again.")

        st.markdown('<div class="auth-footer-note">🔒 Confidential Platform · ISO-27001 · <strong style="color:#38bdf8;">Powered by EOLABS.IN</strong></div>', unsafe_allow_html=True)
        return

    # Multi-step Verification sub-flows
    if st.button("← Return to Sign In"):
        st.session_state["auth_step"] = "auth_card"
        st.rerun()

    if step == "verify":
        pending = st.session_state.get("pending_auth_user", {})
        st.markdown(
            f"""
            <div style="background:rgba(56,189,248,0.1);border:1px solid rgba(56,189,248,0.25);border-radius:10px;padding:14px;margin-bottom:16px;">
                <div style="font-size:0.82rem;font-weight:700;color:#38bdf8;">ONE-TIME CODE SENT</div>
                <div style="font-size:0.86rem;color:#cbd5e1;margin-top:4px;">We emailed a 6-digit code to <strong>{pending.get('email', 'your email')}</strong>.</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        with st.form("verification_form"):
            code = st.text_input("Verification code (OTP)", max_chars=6, placeholder="6-digit code", autocomplete="off")
            submitted = st.form_submit_button("Verify Email Code →", type="primary", use_container_width=True)
        if submitted:
            if _auth.verify_email_code(pending.get("id", ""), code):
                st.session_state["auth_step"] = "password"
                st.rerun()
            st.error("That code is invalid or expired.")
        return

    if step == "password":
        pending = st.session_state.get("pending_auth_user", {})
        st.markdown('<div style="font-size:0.92rem;color:#cbd5e1;margin-bottom:12px;">Create a secure password for your account:</div>', unsafe_allow_html=True)
        with st.form("password_form"):
            password = st.text_input("Password (min 8 chars)", type="password", placeholder="Minimum 8 characters", autocomplete="off")
            confirmation = st.text_input("Confirm password", type="password", placeholder="Re-enter password", autocomplete="off")
            submitted = st.form_submit_button("Complete Setup & Enter →", type="primary", use_container_width=True)
        if submitted:
            try:
                if password != confirmation:
                    raise _auth.AuthValidationError("Passwords do not match.")
                _auth.set_password(pending["id"], password)
                _complete_login(_auth.authenticate(pending["username"], password))
            except _auth.AuthValidationError as error:
                st.error(str(error))
        return


if not st.session_state.get("authentication_status"):
    _login()
    st.stop()

_auth_user = st.session_state.get("auth_user", {})
_username = _auth_user.get("username", st.session_state.get("username", ""))
_role = _auth_user.get("role", "viewer")
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
ai_assistant        = st.Page("pages/19_ai_assistant.py",       title="AI Assistant",        icon=":material/smart_toy:")
stata_studio        = st.Page("pages/23_stata_studio.py",       title="Stata Studio",        icon=":material/terminal:")
ai_chat_guide       = st.Page("pages/24_ai_chat_guide.py",      title="AI Chat Guide",       icon=":material/menu_book:")
# knowledge_graph2  = st.Page("pages/21_knowledge_graph2.py",  title="Know. GraphV2 (WIP)", icon=":material/account_tree:")  # temporarily hidden
nav = st.navigation({
    "": [
        overview, dashboard, data_explorer, benchmarks,
        life_stage_dynamics, transitions,
        scenarios, econometrics, advanced_econ, interaction_effects,
        stata_studio,
        ml_models, forecasting, clustering,
        ai_assistant, board_deck,
    ],
    "Admin & Tools": [
        admin_activity, settings,
        workbench, bulk_upload,
        ai_chat_guide,
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

_nav_border = "rgba(226, 232, 240, 0.8)" if _theme == "light" else "rgba(255, 255, 255, 0.08)"
_nav_shadow = "0 2px 10px rgba(0,0,0,0.04)" if _theme == "light" else "0 4px 20px rgba(0,0,0,0.35)"
_version_border = "#e2e8f0" if _theme == "light" else "rgba(255,255,255,0.1)"
_tag_bg = "rgba(79, 70, 229, 0.1)" if _theme == "light" else "rgba(99, 102, 241, 0.15)"
_tag_color = "#4F46E5" if _theme == "light" else "#818CF8"
_tag_border = "rgba(79, 70, 229, 0.3)" if _theme == "light" else "rgba(99, 102, 241, 0.3)"
_signout_bg = "rgba(244, 63, 94, 0.08)" if _theme == "light" else "rgba(244, 63, 94, 0.12)"
_signout_color = "#E11D48" if _theme == "light" else "#FB7185"
_signout_border = "rgba(225, 29, 72, 0.25)" if _theme == "light" else "rgba(244, 63, 94, 0.3)"
_panel_title = _panel_labels_map.get(_qp_panel, _qp_panel)

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
    border-bottom: 1px solid {_nav_border};
    box-shadow: {_nav_shadow};
    padding: 0 1.75rem;
    display: flex;
    align-items: center;
    gap: 1.5rem;
    font-size: 14px;
    color: {_header_text};
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
">
    <span style="font-family:'Plus Jakarta Sans', sans-serif; font-weight:800; background:{_accent_grad}; -webkit-background-clip:text; -webkit-text-fill-color:transparent; font-size:18px; white-space:nowrap; display:flex; align-items:center; gap:6px;">
        💎 LifeCycle Leverage<span style="font-size:11px;color:{_header_sub};font-weight:600;margin-left:6px;border:1px solid {_version_border};padding:2px 6px;border-radius:6px;-webkit-text-fill-color:initial;">v{_APP_VERSION}</span>
    </span>
    <span style="background:{_tag_bg};color:{_tag_color};border:1px solid {_tag_border};border-radius:8px;padding:4px 10px;font-size:13px;font-weight:600;white-space:nowrap;">
        🏷️&nbsp;{_panel_title}
    </span>
    <span style="white-space:nowrap; color:{_header_sub};"><strong>{_display_name}</strong> &middot; <span style="text-transform:capitalize;">{_role_display}</span></span>
    <span style="margin-left:auto; color:{_header_sub}; font-size:13px; font-family:'JetBrains Mono', monospace; white-space:nowrap;">{_now_str}</span>
    <button
        onclick="(function(){{var btns=document.querySelectorAll('section[data-testid=stSidebar] button');for(var b of btns){{if(b.innerText.includes('Sign out')){{b.click();return;}}}}}})()"
        style="
            background: {_signout_bg};
            color: {_signout_color};
            border: 1px solid {_signout_border};
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
        onmouseout="this.style.background='{_signout_bg}'"
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
