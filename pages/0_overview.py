"""
Overview — Research context and paradigm introduction for the LifeCycle Leverage dashboard.
"""
import streamlit as st
import db
from helpers import ensure_session_state, PLOTLY_CONFIG

ensure_session_state()
db.log_page_visit("Overview")

_panel_mode = st.session_state.get("panel_mode", "latest")
_meta = db.get_db_metadata(_panel_mode)

_panel_label = {
    "thesis":     "Original Thesis Data",
    "latest":     "Latest Panel (CMIE 2025)",
    "run3":       "Run 3 – Stata",
    "us_av_2024": "US S&P Sample",
}.get(_panel_mode, _panel_mode)

_n_obs   = int(_meta.get("total_obs",   0))
_n_firms = int(_meta.get("total_firms", 0))
_yr_min  = int(_meta.get("year_min",    2001))
_yr_max  = int(_meta.get("year_max",    2024))
_n_years = _yr_max - _yr_min + 1

# ── Hero ──────────────────────────────────────────────────────────────────────
st.markdown("""
<div style="
    background: linear-gradient(135deg, #0D9488 0%, #065F46 100%);
    border-radius: 12px;
    padding: 2.5rem 2.8rem 2rem;
    margin-bottom: 1.8rem;
    color: #ffffff;
">
    <div style="font-size:0.85rem; letter-spacing:0.12em; text-transform:uppercase;
                font-weight:600; color:#99f6e4; margin-bottom:0.5rem;">
        Research Dashboard
    </div>
    <h1 style="margin:0; font-size:2rem; font-weight:800; color:#ffffff; line-height:1.25;">
        Life Stage Financial Leverage Strategist
    </h1>
    <p style="margin:0.75rem 0 0; font-size:1rem; color:#ccfbf1; max-width:780px; line-height:1.6;">
        A data-driven research engine connecting corporate life-stage dynamics with capital
        structure theory — built on the PhD thesis of Prof. Surendra Kumar, University of Delhi.
    </p>
</div>
""", unsafe_allow_html=True)

# ── Three paradigm sections ───────────────────────────────────────────────────
_SECTION_STYLE = """
    border-left: 4px solid {color};
    background: {bg};
    border-radius: 0 8px 8px 0;
    padding: 1.2rem 1.5rem;
    margin-bottom: 1.2rem;
"""

st.markdown(f"""
<div style="{_SECTION_STYLE.format(color='#0D9488', bg='#F0FDFA')}">
    <div style="font-size:0.78rem; font-weight:700; letter-spacing:0.1em;
                text-transform:uppercase; color:#0D9488; margin-bottom:0.5rem;">
        Global &amp; Developed Economy Paradigms
    </div>
    <p style="margin:0; color:#1f2937; font-size:0.97rem; line-height:1.75;">
        In an increasingly interconnected and volatile global economy, a firm's capital structure
        functions as a primary driver of its macroeconomic resilience and competitive agility.
        While traditional corporate finance frameworks — pioneered in developed Western markets —
        largely treat capital structure as a <em>static optimization problem</em> balancing tax
        shields against bankruptcy overheads, modern market realities demand a more fluid
        perspective. In highly mature corporate ecosystems, capital structure decisions are
        intrinsically bound to secular shifts, supply chain reorganizations, and shifting monetary
        policies, proving that static debt-to-equity formulas fail to safeguard long-term
        shareholder value.
    </p>
</div>
""", unsafe_allow_html=True)

st.markdown(f"""
<div style="{_SECTION_STYLE.format(color='#6366F1', bg='#EEF2FF')}">
    <div style="font-size:0.78rem; font-weight:700; letter-spacing:0.1em;
                text-transform:uppercase; color:#6366F1; margin-bottom:0.5rem;">
        The Asian Corporate Landscape
    </div>
    <p style="margin:0; color:#1f2937; font-size:0.97rem; line-height:1.75;">
        Translating these theories into the dynamic Asian business context reveals a unique matrix
        of <em>institutional constraints</em> and corporate behaviors. Across emerging Asian
        economies, corporations face distinct capital allocation challenges, characterized by
        localized credit friction, concentrated ownership structures, and a historical reliance on
        relationship-based banking systems. In these environments, business growth and
        entrepreneurial survival are fundamentally dictated by a firm's operational cash flow
        volatility, turning capital structure management into an <em>active, strategic defense
        mechanism</em> rather than a passive accounting exercise.
    </p>
</div>
""", unsafe_allow_html=True)

st.markdown(f"""
<div style="{_SECTION_STYLE.format(color='#F97316', bg='#FFF7ED')}">
    <div style="font-size:0.78rem; font-weight:700; letter-spacing:0.1em;
                text-transform:uppercase; color:#F97316; margin-bottom:0.5rem;">
        The Indian Scenario &amp; The IBC Framework
    </div>
    <p style="margin:0; color:#1f2937; font-size:0.97rem; line-height:1.75;">
        Within this regional context, the Indian corporate ecosystem stands out as a highly
        compelling testing ground for financial theory. The formal operationalization of rigorous
        regulatory frameworks — most notably the <strong>Insolvency and Bankruptcy Code
        (IBC)</strong> — has fundamentally transformed the default landscape and rewritten the
        rules of corporate risk-taking in India. By disaggregating capital structure dynamics into
        sequential corporate life stages, this research engine bridges the gap between traditional
        accounting abstractions and the real-world operational strains of Indian enterprises,
        providing a <em>systemic toolkit for corporate survival and credit risk forecasting</em>.
    </p>
</div>
""", unsafe_allow_html=True)

st.divider()

# ── Current Context ───────────────────────────────────────────────────────────
st.markdown("#### Current Context")

_c1, _c2, _c3, _c4 = st.columns(4)
with _c1:
    st.metric("Observations", f"{_n_obs:,}")
with _c2:
    st.metric("Companies", f"{_n_firms:,}")
with _c3:
    st.metric("Time Span", f"{_yr_min}–{_yr_max}", delta=f"{_n_years} years")
with _c4:
    st.metric("Active Panel", _panel_label)

st.markdown(
    f"<p style='color:#6B7280; font-size:0.88rem; margin-top:0.5rem;'>"
    f"Analyzing <strong>{_n_obs:,}</strong> observations from <strong>{_panel_label}</strong> "
    f"({_n_years} years · {_yr_min}–{_yr_max}) across <strong>{_n_firms}</strong> companies "
    f"using the <code>corplifestage</code> life-stage classification.</p>",
    unsafe_allow_html=True,
)
