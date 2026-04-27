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

import db
from cmie.streamlit_import import render_cmie_sidebar_block
from helpers import ensure_session_state, is_india_panel

# ── Initialize session state defaults (shared with every page) ──
ensure_session_state()

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
        # Panel changed: clamp the user's existing year selection into the new panel's
        # bounds (preserve their narrower window where possible) and rerun so every
        # page's cached query recomputes with the new vintage predicate.
        st.session_state.panel_mode = chosen_panel
        st.session_state.filters["panel_mode"] = chosen_panel
        yr_min_new, yr_max_new = db.get_year_range(chosen_panel)
        prev_lo, prev_hi = st.session_state.filters.get("year_range", (yr_min_new, yr_max_new))
        new_lo = max(int(prev_lo), yr_min_new)
        new_hi = min(int(prev_hi), yr_max_new)
        if new_lo > new_hi:
            # Edge case: prior range entirely outside new panel's bounds — reset to full.
            new_lo, new_hi = yr_min_new, yr_max_new
        st.session_state.filters["year_range"] = (new_lo, new_hi)
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

# ── Navigation ──
dashboard = st.Page("pages/1_dashboard.py", title="Dashboard", icon=":material/dashboard:", default=True)
benchmarks = st.Page("pages/2_peer_benchmarks.py", title="Peer Benchmarks", icon=":material/compare_arrows:")
scenarios = st.Page("pages/3_scenarios.py", title="Scenarios", icon=":material/tune:")
bulk_upload = st.Page("pages/4_bulk_upload.py", title="Bulk Upload", icon=":material/upload_file:")
data_explorer = st.Page("pages/5_data_explorer.py", title="Data Explorer", icon=":material/table_chart:")
settings = st.Page("pages/6_settings.py", title="Settings", icon=":material/settings:")
knowledge_graph = st.Page("pages/7_knowledge_graph.py", title="Knowledge Graph", icon=":material/hub:")
econometrics = st.Page("pages/8_econometrics.py", title="Econometrics Lab", icon=":material/functions:")
ml_models = st.Page("pages/9_ml_models.py", title="ML Models", icon=":material/model_training:")
forecasting = st.Page("pages/10_forecasting.py", title="Forecasting", icon=":material/trending_up:")
clustering = st.Page("pages/11_clustering.py", title="Clustering", icon=":material/bubble_chart:")
transitions = st.Page("pages/12_transitions.py", title="Transitions", icon=":material/swap_horiz:")
advanced_econ = st.Page("pages/13_advanced_econometrics.py", title="Advanced Econometrics", icon=":material/science:")

nav = st.navigation([dashboard, benchmarks, scenarios, bulk_upload, data_explorer, econometrics, ml_models, forecasting, clustering, transitions, advanced_econ, knowledge_graph, settings])
nav.run()
