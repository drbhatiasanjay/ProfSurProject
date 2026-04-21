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

# ── Initialize session state defaults ──
if "panel_mode" not in st.session_state:
    # Dashboard/Benchmarks/Explorer default to 'latest' (incl. CMIE 2025).
    # Econometrics/Forecasting/ML pages override to 'thesis' at their top for reproducibility.
    st.session_state.panel_mode = "latest"

if "filters" not in st.session_state:
    yr_min, yr_max = db.get_year_range(st.session_state.panel_mode)
    st.session_state.filters = {
        "company_codes": [],
        "year_range": (yr_min, yr_max),
        "life_stages": [],
        "industry_groups": [],
        "events": {"gfc": False, "ibc": False, "covid": False},
        "panel_mode": st.session_state.panel_mode,
    }

# ── Sidebar: Global filters ──
with st.sidebar:
    st.markdown("# LifeCycle Leverage")

    # Panel mode: switches the entire read-path between thesis-only and latest (thesis + CMIE).
    vintages_df = db.get_data_vintages()
    panel_label_map = {"thesis": "Thesis panel (2001–2024)", "latest": "Latest panel (2001–present)"}
    panel_options = ["latest", "thesis"]
    current_panel = st.session_state.get("panel_mode", "latest")
    chosen_panel = st.radio(
        "Panel",
        options=panel_options,
        index=panel_options.index(current_panel),
        format_func=lambda m: panel_label_map.get(m, m),
        help="Thesis panel freezes at 2001–2024 for reproducibility of the published thesis. "
             "Latest panel adds the CMIE 2025 rollforward.",
    )
    if chosen_panel != current_panel:
        # Panel changed: re-seed year range to match the new panel's bounds and rerun so
        # every page's cached query recomputes with the new vintage predicate.
        st.session_state.panel_mode = chosen_panel
        st.session_state.filters["panel_mode"] = chosen_panel
        yr_min_new, yr_max_new = db.get_year_range(chosen_panel)
        st.session_state.filters["year_range"] = (yr_min_new, yr_max_new)
        st.rerun()
    st.session_state.panel_mode = chosen_panel
    st.session_state.filters["panel_mode"] = chosen_panel

    companies_df = db.get_companies()
    all_stages = db.get_life_stages()
    all_industries = db.get_industry_groups()
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

    # Year range
    year_range = st.slider(
        "Year Range",
        min_value=yr_min,
        max_value=yr_max,
        value=st.session_state.filters["year_range"],
    )
    st.session_state.filters["year_range"] = year_range

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
    ibc = st.checkbox("IBC (2016+)", value=False, help="Insolvency & Bankruptcy Code")
    covid = st.checkbox("COVID (2020-21)", value=False, help="COVID-19 pandemic")
    st.session_state.filters["events"] = {"gfc": gfc, "ibc": ibc, "covid": covid}

    st.divider()
    meta = db.get_db_metadata(chosen_panel)
    panel_suffix = " • includes CMIE 2025" if chosen_panel == "latest" else " • thesis only"
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
