"""
Settings — Theme, about section, database metadata.
"""

import streamlit as st
import db

st.markdown("### Settings")

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

st.divider()

# ── Credits ──
st.markdown("#### Credits")
st.caption("Built with Streamlit, Plotly, and SQLite. Data from CMIE Prowess.")
st.caption("Dashboard developed as a research visualization tool for the PhD thesis.")
