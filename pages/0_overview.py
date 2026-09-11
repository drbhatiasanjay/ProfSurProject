"""
Overview — Research context and paradigm introduction for the LifeCycle Leverage dashboard.
"""
import streamlit as st
import db
from helpers import ensure_session_state, PLOTLY_CONFIG, render_bento_kpi
from models.researcher_slice import create_researcher_slice, apply_research_action

ensure_session_state()
db.log_page_visit("Overview")

_panel_mode = st.session_state.get("panel_mode", "latest")
_meta = db.get_db_metadata(_panel_mode)

_panel_label = {
    "bf2001_25_sept26": "bf2001-25_Sept26",
    "thesis":     "Original Thesis Data",
    "latest":     "Latest Panel (CMIE 2025)",
    "run3":       "(2001-25)_April26",
    "us_av_2024": "US S&P Sample",
}.get(_panel_mode, _panel_mode)

_n_obs   = int(_meta.get("total_obs",   0))
_n_firms = int(_meta.get("total_firms", 0))
_yr_min  = int(_meta.get("year_min",    2001))
_yr_max  = int(_meta.get("year_max",    2024))
_n_years = _yr_max - _yr_min + 1

# Wave 8: bounded, read-only researcher journey.  It is deliberately derived
# from the active public panel context and never promotes validation status.
_user = st.session_state.get("user", {})
if _user.get("role") in {"admin", "researcher"}:
    _slice = create_researcher_slice(
        workspace_id="public-panel",
        role=_user["role"],
        analysis_run_id=f"overview:{_panel_mode}",
        artifact_ids=("panel-context",),
        limitations=("This read-only slice is not an estimator validation release.",),
    )
    _slice_action = st.session_state.get("researcher_slice_action", "view")
    if _slice_action in {"challenge", "reproduce"}:
        _slice = apply_research_action(_slice, _slice_action)
    st.session_state["researcher_slice"] = _slice
    st.markdown("### 🔎 Researcher Evidence Slice")
    st.caption(
        "Read-only panel context. Reproduce and challenge actions preserve the "
        "same workspace/run binding and cannot release an unvalidated result."
    )
    _slice_c1, _slice_c2, _slice_c3 = st.columns([3, 2, 2])
    with _slice_c1:
        st.metric("Release status", _slice.release_status)
    with _slice_c2:
        if st.button("Reproduce", key="researcher_slice_reproduce"):
            st.session_state["researcher_slice_action"] = "reproduce"
            st.rerun()
    with _slice_c3:
        if st.button("Challenge", key="researcher_slice_challenge"):
            st.session_state["researcher_slice_action"] = "challenge"
            st.rerun()
    st.caption(
        f"Workspace: `{_slice.workspace_id}` · Run: `{_slice.analysis_run_id}` · "
        f"Action: `{_slice.action}`"
    )

# ── Hero ──────────────────────────────────────────────────────────────────────
st.markdown("""
<div style="
    background: linear-gradient(135deg, rgba(99, 102, 241, 0.9) 0%, rgba(6, 182, 212, 0.85) 100%);
    border-radius: 16px;
    padding: 2.2rem 2.5rem;
    margin-bottom: 1.8rem;
    color: #ffffff;
    box-shadow: 0 4px 20px -2px rgba(0, 0, 0, 0.25);
">
    <div style="font-size:0.75rem; letter-spacing:0.12em; text-transform:uppercase;
                font-weight:700; color:rgba(255,255,255,0.85); margin-bottom:0.4rem;">
        🎓 Research Platform & Econometric Lab
    </div>
    <h1 style="margin:0; font-size:2.1rem; font-weight:800; color:#ffffff; line-height:1.25; font-family:'Plus Jakarta Sans', sans-serif;">
        Life Stage Financial Leverage Strategist
    </h1>
    <p style="margin:0.75rem 0 0; font-size:1rem; color:rgba(255,255,255,0.92); max-width:820px; line-height:1.6;">
        A quantitative research engine connecting corporate life-stage dynamics with capital
        structure theory — built on the PhD thesis of Prof. Surendra Kumar, University of Delhi.
    </p>
</div>
""", unsafe_allow_html=True)

# ── Current Context Bento Grid ───────────────────────────────────────────────
st.markdown("### 🗺️ Active Panel Architecture & Context")

_c1, _c2, _c3, _c4 = st.columns(4)
with _c1:
    st.markdown(render_bento_kpi(
        title="Observations",
        value=f"{_n_obs:,}",
        delta="100% Balanced",
        percentile=100.0,
        tag="SAMPLE SIZE",
        stroke_color="#6366F1"
    ), unsafe_allow_html=True)
with _c2:
    st.markdown(render_bento_kpi(
        title="Covered Companies",
        value=f"{_n_firms:,}",
        delta="Nifty / CMIE",
        percentile=100.0,
        tag="UNIVERSE",
        stroke_color="#06B6D4"
    ), unsafe_allow_html=True)
with _c3:
    st.markdown(render_bento_kpi(
        title="Time Span",
        value=f"{_yr_min}–{_yr_max}",
        delta=f"{_n_years} Years",
        percentile=100.0,
        tag="LONG PANEL",
        stroke_color="#10B981"
    ), unsafe_allow_html=True)
with _c4:
    st.markdown(render_bento_kpi(
        title="Active Dataset",
        value=_panel_mode.upper(),
        delta=_panel_label,
        percentile=100.0,
        tag="VINTAGE",
        stroke_color="#8B5CF6"
    ), unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ── Three paradigm sections ───────────────────────────────────────────────────
st.markdown("### 🏛️ Theoretical Foundations & Research Paradigms")

col_p1, col_p2, col_p3 = st.columns(3)

with col_p1:
    st.markdown("""
    <div class="bento-card" style="height:100%; border-top: 3px solid #6366F1;">
        <div style="font-size:0.75rem; font-weight:700; text-transform:uppercase; color:#6366F1; margin-bottom:8px;">
            🌐 Global &amp; Western Paradigms
        </div>
        <p style="font-size:0.88rem; line-height:1.65; color:var(--text-secondary); margin:0;">
            Traditional corporate finance frameworks largely treat capital structure as a <em>static optimization problem</em> (balancing tax shields vs bankruptcy costs). In volatile markets, capital structure decisions are intrinsically bound to secular life-stage transitions.
        </p>
    </div>
    """, unsafe_allow_html=True)

with col_p2:
    st.markdown("""
    <div class="bento-card" style="height:100%; border-top: 3px solid #06B6D4;">
        <div style="font-size:0.75rem; font-weight:700; text-transform:uppercase; color:#06B6D4; margin-bottom:8px;">
            🌏 The Asian Corporate Matrix
        </div>
        <p style="font-size:0.88rem; line-height:1.65; color:var(--text-secondary); margin:0;">
            In emerging Asian economies, corporations face concentrated ownership and credit friction. Operational cash-flow volatility dictates corporate survival, turning capital structure management into an <em>active strategic defense mechanism</em>.
        </p>
    </div>
    """, unsafe_allow_html=True)

with col_p3:
    st.markdown("""
    <div class="bento-card" style="height:100%; border-top: 3px solid #10B981;">
        <div style="font-size:0.75rem; font-weight:700; text-transform:uppercase; color:#10B981; margin-bottom:8px;">
            🇮🇳 Indian Ecosystem &amp; IBC
        </div>
        <p style="font-size:0.88rem; line-height:1.65; color:var(--text-secondary); margin:0;">
            The <strong>Insolvency &amp; Bankruptcy Code (IBC 2016)</strong> has fundamentally transformed corporate risk-taking. By disaggregating panel dynamics into Dickinson life stages, this platform bridges theory and empirical debt reality.
        </p>
    </div>
    """, unsafe_allow_html=True)
