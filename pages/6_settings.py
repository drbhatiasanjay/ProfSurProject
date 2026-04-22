"""
Settings — Theme, about section, database metadata.
"""

import streamlit as st
import db
from helpers import ensure_session_state

ensure_session_state()

st.markdown("### Settings")

# ── Appearance ──
st.markdown("#### Appearance")
_theme_options = ["light", "dark"]
_theme_labels = {"light": "Light (default)", "dark": "Dark (mock-inspired)"}
_current = st.session_state.get("theme", "light")
_chosen = st.radio(
    "Theme",
    options=_theme_options,
    index=_theme_options.index(_current) if _current in _theme_options else 0,
    format_func=lambda t: _theme_labels[t],
    horizontal=True,
    help="Light keeps the original teal-on-white look. Dark matches the DataV2 mock palette.",
    key="settings_theme_radio",
)
if _chosen != _current:
    st.session_state.theme = _chosen
    st.rerun()
st.caption("Theme persists for the current session. Switching does not alter any data.")

st.divider()

# ── CMIE Lab (optional) ──
st.markdown("#### CMIE Economy API Lab")
if db.is_cmie_lab_enabled():
    from cmie.streamlit_import import render_cmie_sidebar_block

    st.caption(
        "CMIE lab is enabled. Use the block below to switch data source and import a new CMIE version "
        "(writes to SQLite `api_financials`)."
    )
    render_cmie_sidebar_block(key_prefix="cmie_settings")
else:
    st.caption(
        "CMIE lab UI is disabled unless **ENABLE_CMIE** is set (env or Streamlit secrets). "
        "Restart the app after setting it."
    )

st.divider()

# ── About ──
st.markdown("#### About LifeCycle Leverage Dashboard")
st.markdown("""
This dashboard visualizes the determinants of capital structure across corporate life stages
for Indian publicly listed companies, based on research by **Surendra Kumar** (University of Delhi, 2025).

**Thesis:** *Determinants of Capital Structure over Corporate Life Stages: A Study of Indian Corporates*

**Supervisors:** Dr. Varun Dawar & Dr. Chandra Prakash Gupta

**Methodology:**
- Life stage classification using **Dickinson (2011)** cash-flow patterns
- Panel data regression: Fixed Effects, Random Effects, System GMM
- Theoretical frameworks: Pecking Order Theory, Trade-off Theory, Agency Cost Theory
""")

st.divider()

# ── Database Metadata ──
st.markdown("#### Database Info")
meta = db.get_db_metadata()

mc1, mc2, mc3, mc4 = st.columns(4)
with mc1:
    st.metric("Total Firms", f"{meta['total_firms']}")
with mc2:
    st.metric("Observations", f"{meta['total_obs']:,}")
with mc3:
    st.metric("Year Range", f"{meta['year_min']}-{meta['year_max']}")
with mc4:
    st.metric("Industries", f"{meta['industries']}")

st.divider()

# ── Life Stage Reference ──
st.markdown("#### Life Stage Classification Reference")
st.markdown("""
| Stage | NCFo | NCFi | NCFf | Description |
|-------|------|------|------|-------------|
| **Startup** | - | - | + | Negative operating cash, investing heavily, funded by external financing |
| **Growth** | + | - | + | Generating cash from operations, heavy investment, supplemented by financing |
| **Maturity** | + | - | - | Positive operations, still investing, repaying debt |
| **Shakeout1** | - | - | - | All cash flows negative — distress |
| **Shakeout2** | + | + | + | All positive — liquidating assets |
| **Shakeout3** | + | + | - | Divesting and repaying debt |
| **Decline** | - | + | + | Selling assets, raising new financing |
| **Decay** | - | + | - | Selling assets, repaying obligations |
""")

st.divider()

# ── Data Sources ──
st.markdown("#### Data Sources")
st.markdown("""
- **Financial data:** CMIE Prowess database (2001-2024)
- **Market index:** S&P BSE data
- **Interest rates:** Reserve Bank of India
- **Shareholding:** NSE/BSE quarterly filings
""")

st.caption(
    "Optional CMIE Economy API lab UI is disabled unless **ENABLE_CMIE** is set "
    "(env or Streamlit secrets). Use a **GitHub fork** for CMIE development; see **FORK_WORKFLOW.md**."
)

st.divider()

# ── Credits ──
st.markdown("#### Credits")
st.caption("Built with Streamlit, Plotly, and SQLite. Data from CMIE Prowess.")
st.caption("Dashboard developed as a research visualization tool for the PhD thesis.")
