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

# Load custom CSS
css_path = os.path.join(os.path.dirname(__file__), "assets", "style.css")
if os.path.exists(css_path):
    with open(css_path) as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

import db

# ── Initialize session state defaults ──
if "filters" not in st.session_state:
    yr_min, yr_max = db.get_year_range()
    st.session_state.filters = {
        "company_codes": [],
        "year_range": (yr_min, yr_max),
        "life_stages": [],
        "industry_groups": [],
        "events": {"gfc": False, "ibc": False, "covid": False},
    }

# ── Sidebar: Global filters ──
with st.sidebar:
    st.markdown("# LifeCycle Leverage")

    companies_df = db.get_companies()
    all_stages = db.get_life_stages()
    all_industries = db.get_industry_groups()
    yr_min, yr_max = db.get_year_range()

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
    col1, col2, col3 = st.columns(3)
    with col1:
        gfc = st.toggle("GFC", value=False, help="Global Financial Crisis 2008-09")
    with col2:
        ibc = st.toggle("IBC", value=False, help="Insolvency & Bankruptcy Code 2016+")
    with col3:
        covid = st.toggle("COVID", value=False, help="COVID-19 2020-21")
    st.session_state.filters["events"] = {"gfc": gfc, "ibc": ibc, "covid": covid}

    st.divider()
    meta = db.get_db_metadata()
    st.caption(f"{meta['total_firms']} firms | {meta['total_obs']:,} obs | {meta['year_min']}-{meta['year_max']}")

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

nav = st.navigation([dashboard, benchmarks, scenarios, bulk_upload, data_explorer, econometrics, ml_models, knowledge_graph, settings])
nav.run()
