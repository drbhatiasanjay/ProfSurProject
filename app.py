"""
LifeCycle Leverage Dashboard — Main entrypoint.
Streamlit multipage app for analyzing capital structure across corporate life stages.
"""

import os
import streamlit as st

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

# Phase 6: Chat assistant CSS
try:
    with open("assets/style_chat.css", "r", encoding="utf-8") as _f:
        st.markdown(f"<style>{_f.read()}</style>", unsafe_allow_html=True)
except FileNotFoundError:
    pass

# ── Authentication ────────────────────────────────────────────────────────────
import streamlit_authenticator as stauth

_creds = {"usernames": {
    k: dict(v) for k, v in st.secrets.get("credentials", {}).get("usernames", {}).items()
}}
_cookie = st.secrets.get("cookie", {})
authenticator = stauth.Authenticate(
    _creds,
    _cookie.get("name", "lclev_auth"),
    _cookie.get("key", "fallback-key"),
    int(_cookie.get("expiry_days", 7)),
)
authenticator.login()
if not st.session_state.get("authentication_status"):
    if st.session_state.get("authentication_status") is False:
        st.error("Username or password incorrect.")
    else:
        st.info("Please sign in to access the LifeCycle Leverage Dashboard.")
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

# ── Restore saved preferences before session state defaults are set ──
if "prefs_loaded" not in st.session_state:
    _saved = db.load_user_prefs(_username, "app")
    if _saved:
        if "panel_mode" in _saved:
            st.session_state["panel_mode"] = _saved["panel_mode"]
        if "filters" in _saved:
            st.session_state["filters"] = _saved["filters"]
        if "theme" in _saved:
            st.session_state["theme"] = _saved["theme"]
    st.session_state["prefs_loaded"] = True

if "login_logged" not in st.session_state:
    db.log_user_login(_username, _role, st.session_state["session_id"])
    st.session_state["login_logged"] = True

# ── Initialize session state defaults (shared with every page) ──
ensure_session_state()

# Phase 6: Chat assistant state
if "chat_open" not in st.session_state:
    st.session_state["chat_open"] = False
if "chat_history" not in st.session_state:
    st.session_state["chat_history"] = []  # list of {role, content}
if "chat_mode" not in st.session_state:
    st.session_state["chat_mode"] = "researcher"  # auto-set per page below
if "chat_backend" not in st.session_state:
    # Default Ollama in dev, Anthropic in Cloud Run (K_SERVICE is set by GCP)
    _default_backend = "anthropic" if os.environ.get("K_SERVICE") else "ollama"
    st.session_state["chat_backend"] = _default_backend
if "ai_recommendations" not in st.session_state:
    st.session_state["ai_recommendations"] = []

# ── Sidebar: Global filters ──
with st.sidebar:
    st.markdown("# LifeCycle Leverage")

    # Panel mode: switches the entire read-path across three independent vintage groups.
    # - latest = production panel (thesis 2001-2024 + cmie_2025 rollforward)
    # - thesis = frozen reproducibility panel (2001-2024 only)
    # - run3   = Stata replication panel (2001-2025, 400 firms; standalone — does NOT
    #            union with thesis or cmie_2025 because years overlap)
    vintages_df = db.get_data_vintages()
    from helpers import PANEL_LABELS as panel_label_map
    panel_options = ["latest", "thesis", "run3", "us_av_2024"]
    current_panel = st.session_state.get("panel_mode", "latest")
    if current_panel not in panel_options:
        current_panel = "latest"
    chosen_panel = st.radio(
        "Panel",
        options=panel_options,
        index=panel_options.index(current_panel),
        format_func=lambda m: panel_label_map.get(m, m),
        help=(
            "**Latest** — production panel (thesis + CMIE 2025 rollforward).\n\n"
            "**Thesis** — frozen 2001-2024 panel for reproducing published thesis tables.\n\n"
            "**Run 3** — Stata replication panel from initialResults.do (25 Apr 2026), "
            "9,031 obs × 400 firms × 2001-2025.\n\n"
            "**US S&P Sample** — 25 DJIA / S&P blue-chip firms via Alpha Vantage API; "
            "Dickinson life-stages from cash-flow signs. Load with "
            "`scripts/load_us_av_panel.py`."
        ),
    )
    if chosen_panel != current_panel:
        # Panel changed: reset to the new panel's full year range, then rerun so every
        # page's cached query recomputes with the new vintage predicate.
        # We intentionally do NOT carry over the prior selection because each panel has a
        # different natural start year (India: 2001, US: 2006) and a selection shaped by
        # one panel misleads the user on another.
        st.session_state.panel_mode = chosen_panel
        st.session_state.filters["panel_mode"] = chosen_panel
        yr_min_new, yr_max_new = db.get_year_range(chosen_panel)
        st.session_state.filters["year_range"] = (yr_min_new, yr_max_new)
        st.rerun()
    st.session_state.panel_mode = chosen_panel
    st.session_state.filters["panel_mode"] = chosen_panel

    companies_df = db.get_companies(chosen_panel)
    all_stages = db.get_life_stages()
    all_industries = db.get_industry_groups(chosen_panel)
    yr_min, yr_max = db.get_year_range(chosen_panel)

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
    # (Thesis: 2001-2024, Latest: 2001-2025, Run 3: 2001-2025).
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
    if is_india_panel(chosen_panel):
        ibc = st.checkbox("IBC (2016+)", value=False, help="Insolvency & Bankruptcy Code")
    else:
        ibc = False
        st.caption("_IBC dummy: India-only — not applicable for US panel_")
    covid = st.checkbox("COVID (2020-21)", value=False, help="COVID-19 pandemic")
    st.session_state.filters["events"] = {"gfc": gfc, "ibc": ibc, "covid": covid}

    st.divider()
    meta = db.get_db_metadata(chosen_panel)
    if chosen_panel == "latest":
        panel_suffix = " • includes CMIE 2025"
    elif chosen_panel == "us_av_2024":
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

    # Auto-save sidebar state for this user (panel, filters, theme)
    if _username:
        db.save_user_pref(_username, "app", {
            "panel_mode": st.session_state.get("panel_mode", "latest"),
            "filters":    st.session_state.get("filters", {}),
            "theme":      st.session_state.get("theme", "light"),
        })

# ── Navigation ──
dashboard = st.Page("pages/1_dashboard.py", title="Dashboard", icon=":material/dashboard:", default=True)
benchmarks = st.Page("pages/2_peer_benchmarks.py", title="Peer Benchmarks", icon=":material/compare_arrows:")
scenarios = st.Page("pages/3_scenarios.py", title="Scenarios", icon=":material/tune:")
bulk_upload = st.Page("pages/4_bulk_upload.py", title="Bulk Upload", icon=":material/upload_file:")
data_explorer = st.Page("pages/5_data_explorer.py", title="Data Explorer", icon=":material/table_chart:")
settings = st.Page("pages/6_settings.py", title="Settings", icon=":material/settings:")
knowledge_graph     = st.Page("pages/7_knowledge_graph.py",     title="Life Stage Dynamics", icon=":material/hub:")
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
company_navigator   = st.Page("pages/18_company_navigator.py", title="Company Navigator",   icon=":material/explore:")
ai_assistant        = st.Page("pages/19_ai_assistant.py",       title="AI Assistant",        icon=":material/smart_toy:")
nav = st.navigation([dashboard, benchmarks, scenarios, bulk_upload, data_explorer, econometrics, ml_models, forecasting, clustering, transitions, advanced_econ, workbench, interaction_effects, admin_activity, board_deck, company_navigator, ai_assistant, knowledge_graph, settings])

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

_header_bg   = "#ffffff" if _theme == "light" else "#0f1117"
_header_text = "#111827" if _theme == "light" else "#f3f4f6"
_header_sub  = "#6B7280" if _theme == "light" else "#9ca3af"

st.markdown(f"""
<div id="lc-navbar" style="
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    z-index: 1000001;
    height: 64px;
    background: {_header_bg};
    border-bottom: 3px solid #0D9488;
    box-shadow: 0 2px 6px rgba(0,0,0,0.07);
    padding: 0 1.5rem;
    display: flex;
    align-items: center;
    gap: 2rem;
    font-size: 15px;
    color: {_header_text};
    font-family: inherit;
">
    <span style="font-weight:700; color:#0D9488; font-size:18px; white-space:nowrap;">LifeCycle Leverage</span>
    <span style="color:{_header_sub}; white-space:nowrap;">Dataset:&nbsp;<strong style="color:{_header_text};">{_panel_display}</strong></span>
    <span style="white-space:nowrap;"><strong>{_display_name}</strong>&nbsp;&middot;&nbsp;{_role_display}</span>
    <span style="margin-left:auto; color:{_header_sub}; font-size:14px; white-space:nowrap;">{_now_str}</span>
    <button
        onclick="(function(){{var btns=document.querySelectorAll('section[data-testid=stSidebar] button');for(var b of btns){{if(b.innerText.includes('Sign out')){{b.click();return;}}}}}})()"
        style="
            background:#dc2626;
            color:white;
            font-weight:700;
            font-size:14px;
            border:none;
            border-radius:8px;
            padding:0 18px;
            height:40px;
            cursor:pointer;
            white-space:nowrap;
            box-shadow:0 2px 4px rgba(220,38,38,0.3);
        "
        onmouseover="this.style.background='#b91c1c'"
        onmouseout="this.style.background='#dc2626'"
    >&#9211;&nbsp; Sign out</button>
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
</style>
""", unsafe_allow_html=True)
# ── Phase 6: Chat assistant helpers ───────────────────────────────────────────

def _detect_chat_mode() -> str:
    """CFO mode for company-centric pages (17, 18); researcher mode otherwise."""
    try:
        if st.session_state.get("active_company_cin"):
            return "cfo"
        cur = st.session_state.get("__cur_page", "")
        if any(k in cur.lower() for k in ["board_export", "company_navigator", "17_", "18_"]):
            return "cfo"
    except Exception:
        pass
    return "researcher"


def render_chat_panel():
    """Chat panel rendered in sidebar — only when chat_open is True."""
    if not st.session_state.get("chat_open"):
        return
    from models.llm_adapters import (
        build_company_context, build_panel_context,
        stream_ollama, stream_anthropic,
        log_chat_query, count_tokens,
    )

    st.session_state["chat_mode"] = _detect_chat_mode()
    mode = st.session_state["chat_mode"]
    backend = st.session_state["chat_backend"]

    with st.sidebar:
        st.divider()
        col_a, col_b, col_c = st.columns([3, 2, 1])
        with col_a:
            st.markdown(
                f"**AI Assistant** &nbsp;"
                f'<span style="font-size:11px;padding:2px 8px;border-radius:999px;'
                f'background:rgba(13,148,136,0.15);color:#0D9488">{mode.upper()}</span>',
                unsafe_allow_html=True,
            )
        with col_b:
            new_backend = st.selectbox(
                "Backend", ["ollama", "anthropic"],
                index=["ollama", "anthropic"].index(backend),
                key="chat_backend_select", label_visibility="collapsed",
            )
            if new_backend != backend:
                st.session_state["chat_backend"] = new_backend
                st.rerun()
        with col_c:
            if st.button("✕", key="chat_close_btn", help="Close chat"):
                st.session_state["chat_open"] = False
                st.rerun()

        for turn in st.session_state["chat_history"][-6:]:
            with st.chat_message(turn["role"]):
                st.markdown(turn["content"])

        user_q = st.chat_input("Ask about your data...", key="chat_input_main")
        if user_q:
            if mode == "cfo" and st.session_state.get("active_company_cin"):
                ctx = build_company_context(
                    st.session_state["active_company_cin"],
                    panel_mode=st.session_state.get("panel_mode", "thesis"),
                )
            else:
                ctx = build_panel_context(
                    panel_mode=st.session_state.get("panel_mode", "thesis"),
                )

            st.session_state["chat_history"].append({"role": "user", "content": user_q})
            with st.chat_message("user"):
                st.markdown(user_q)

            messages = []
            for turn in st.session_state["chat_history"][-11:-1]:
                messages.append({"role": turn["role"], "content": turn["content"]})
            messages.append({"role": "user", "content": user_q})

            with st.chat_message("assistant"):
                if backend == "ollama":
                    full = st.write_stream(stream_ollama(
                        [{"role": "system", "content": ctx}] + messages
                    ))
                else:
                    full = st.write_stream(stream_anthropic(messages, system=ctx))
                if mode == "cfo" and full:
                    if st.button("➕ Add to Board Deck",
                                 key=f"add_brd_{len(st.session_state['chat_history'])}"):
                        st.session_state["ai_recommendations"].append(
                            {"question": user_q, "answer": full}
                        )
                        st.toast("Added to Board Deck")

            st.session_state["chat_history"].append({"role": "assistant", "content": full or ""})

            _user_info = st.session_state.get("user", {}) or {}
            log_chat_query(
                username=_user_info.get("username", "anonymous"),
                role=_user_info.get("role", "viewer"),
                backend=backend,
                token_count=count_tokens(ctx) + count_tokens(user_q) + count_tokens(full or ""),
                query=user_q,
                session_id=st.session_state.get("session_id", ""),
            )


# ─────────────────────────────────────────────────────────────────────────────

# Phase 6: FAB state bridge — must run BEFORE nav.run() so chat_open is correct when page renders
_chat_param = st.query_params.get("chat")
if _chat_param == "1":
    st.session_state["chat_open"] = True
    st.query_params.clear()
elif _chat_param == "0":
    st.session_state["chat_open"] = False
    st.query_params.clear()

render_chat_panel()

nav.run()

# Phase 6: Floating chat FAB (bottom-right, every page)
_fab_icon = "✕" if st.session_state["chat_open"] else "\U0001f4ac"
_next_chat = "0" if st.session_state["chat_open"] else "1"
st.markdown(
    f'<a id="lc-chat-fab" class="lc-chat-fab" href="?chat={_next_chat}" '
    f'title="AI Assistant" target="_self">{_fab_icon}</a>',
    unsafe_allow_html=True,
)
# ─────────────────────────────────────────────────────────────────────────────
