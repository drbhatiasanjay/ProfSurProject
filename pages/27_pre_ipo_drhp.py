"""
Pre-IPO DRHP Intelligence & Sovereign Decision Support Terminal.
Comprehensive Institutional Architecture adhering to:
- SEBI ICDR 2018 Regulatory Standards & SEBI LODR Governance
- Dickinson (2011) Life-Cycle Calibration against 8,677 CMIE Database
- Dynamic 3-Constraint Debt Capacity Sizing (Lev Ceiling, DSCR Floor, ICR Floor)
- 2D Adversarial Stress Matrix & Ind AS 116 Lease Capitalization
- Objects of Offer & Use of Proceeds Waterfall (SEBI Reg 7 GCP <= 25% compliance)
- Cap Table Dilution & Statutory 18m/6m/Anchor Lock-In Schedules
- Beneish (1999) 8-Variable Forensic M-Score & Accrual Quality
- Debt Maturity Ladder & Refinancing Profile
- CMIE Listed Peer Multiples (P/E, EV/EBITDA) & Crosswalk Reconciliation
- 10 Core Investor Questions (Q01-Q10) & Private Extensions (PX01-PX04)
- Investment Committee (IC) Deal Memo & Prescriptive Underwriting Verdict
- One-Click 16:9 Vector Board Pitch Deck Generator
"""
import streamlit as st
from utils.html_blocks import render_html
import pandas as pd
import plotly.graph_objects as go
from models.pre_ipo_data import get_legacy_dossier
from models.pre_ipo_ingest import PreIPOIngestionEngine, assess_analysis_eligibility, ExtractionState
from models.pre_ipo_capability_gate import (
    CapabilityType,
    evaluate_capability_gate,
    assert_export_allowed,
    ExportBlockedError,
    is_hcch_entity,
)
from models.pre_ipo_financial_contracts import FinancialStatementsContract
from models.pre_ipo_engine import (
    classify_dickinson_stage,
    compute_debt_capacity,
    generate_2d_sensitivity_matrix,
    calculate_beneish_m_score,
    generate_financials_narrative,
    generate_indebtedness_narrative,
    generate_stress_narrative,
    generate_objects_narrative,
    generate_cap_table_narrative,
    generate_forensics_narrative,
    generate_valuation_narrative,
    generate_persona_decision_view,
    generate_anchor_lockin_calendar,
    calculate_wacc_and_roic,
    calculate_reverse_dcf_hurdle,
    generate_cmie_crosswalk_coverage,
    generate_equity_question_answers,
)
from utils.pre_ipo_deck_generator import generate_pre_ipo_board_deck
from components.pre_ipo_provenance_ledger import render_provenance_ledger_tab

# Page Configuration
st.set_page_config(
    page_title="Pre-IPO DRHP Intelligence | Sovereign Terminal",
    page_icon=":material/rocket_launch:",
    layout="wide",
)

# Independent additive workflow; the existing terminal remains the default.
if "pre_ipo_target_workspace" in st.session_state:
    st.session_state["pre_ipo_workspace"] = st.session_state.pop("pre_ipo_target_workspace")

with st.container(key="pre_ipo_workspace_switch"):
    if st.session_state.get("theme") == "light":
        render_html('''<style>
        .st-key-pre_ipo_workspace_switch label,
        .st-key-pre_ipo_workspace_switch label p,
        .st-key-pre_ipo_workspace_switch [data-testid="stWidgetLabel"] p { color: #0f172a !important; }
        </style>''')
    workspace = st.radio("Pre-IPO workspace", ["Existing Pre-IPO terminal", "Facts & evidence review", "Decision-depth workbench"], horizontal=True, key="pre_ipo_workspace")
if workspace == "Facts & evidence review":
    from components.pre_ipo_evidence_review import render
    render()
    st.stop()
if workspace == "Decision-depth workbench":
    from components.pre_ipo_decision_workbench import render
    render()
    st.stop()


# Apply Sovereign Financial Terminal Glassmorphic Theme CSS
render_html(
    """
    <style>
    /* Monospace Financial Numbers & Tabular Alignment */
    .metric-value, .financial-num {
        font-family: 'JetBrains Mono', 'SF Mono', 'Roboto Mono', monospace !important;
        font-variant-numeric: tabular-nums !important;
    }

    /* Glassmorphism Surface Tiles */
    .bento-card {
        background: rgba(17, 24, 39, 0.65);
        backdrop-filter: blur(20px) saturate(180%);
        -webkit-backdrop-filter: blur(20px) saturate(180%);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 12px;
        padding: 18px 22px;
        margin-bottom: 16px;
        box-shadow: 0 4px 20px -2px rgba(0, 0, 0, 0.35);
        transition: all 0.25s cubic-bezier(0.16, 1, 0.3, 1);
    }
    .bento-card:hover {
        border-color: rgba(56, 189, 248, 0.35);
        box-shadow: 0 8px 30px -4px rgba(56, 189, 248, 0.12);
    }

    /* Narrative Analytical Box */
    .narrative-card {
        background: rgba(15, 23, 42, 0.85);
        border-left: 4px solid #38bdf8;
        border-radius: 8px;
        padding: 14px 18px;
        margin-top: 14px;
        margin-bottom: 14px;
    }
    .action-card {
        background: rgba(16, 185, 129, 0.08);
        border-left: 4px solid #10b981;
        border-radius: 8px;
        padding: 14px 18px;
        margin-top: 14px;
        margin-bottom: 14px;
    }

    /* Status Badges */
    .badge-pill {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        padding: 3px 10px;
        border-radius: 9999px;
        font-size: 0.72rem;
        font-weight: 700;
        letter-spacing: 0.05em;
        text-transform: uppercase;
    }
    .badge-emerald {
        background: rgba(16, 185, 129, 0.15);
        color: #10b981;
        border: 1px solid rgba(16, 185, 129, 0.3);
    }
    .badge-amber {
        background: rgba(245, 158, 11, 0.15);
        color: #f59e0b;
        border: 1px solid rgba(245, 158, 11, 0.3);
    }
    .badge-rose {
        background: rgba(244, 63, 94, 0.15);
        color: #f43f5e;
        border: 1px solid rgba(244, 63, 94, 0.3);
    }
    .badge-sky {
        background: rgba(56, 189, 248, 0.15);
        color: #38bdf8;
        border: 1px solid rgba(56, 189, 248, 0.3);
    }
    .badge-purple {
        background: rgba(168, 85, 247, 0.15);
        color: #a855f7;
        border: 1px solid rgba(168, 85, 247, 0.3);
    }

    /* Section Subtitle Typography */
    .bento-subtitle {
        color: #94a3b8;
        font-size: 0.80rem;
        font-weight: 600;
        letter-spacing: 0.05em;
        text-transform: uppercase;
        margin-bottom: 8px;
    }
    .bento-title {
        color: #f8fafc;
        font-size: 1.25rem;
        font-weight: 800;
        letter-spacing: -0.02em;
        margin-bottom: 12px;
    }

    /* Multi-line stacked tabs with tactile border, depth & shadow */
    div[data-testid="stTabs"] [role="tablist"] {
        display: flex !important;
        flex-wrap: wrap !important;
        gap: 10px 12px !important;
        overflow-x: visible !important;
        border: none !important;
        border-bottom: none !important;
        padding: 6px 0 14px 0 !important;
        margin-bottom: 16px !important;
    }

    /* Suppress detached Streamlit underline bar in multi-row tabs */
    div[data-testid="stTabs"] [data-baseweb="tab-highlight"],
    div[data-testid="stTabs"] [data-baseweb="tab-border"] {
        display: none !important;
    }

    div[data-testid="stTabs"] [role="tab"] {
        white-space: normal !important;
        word-break: normal !important;
        height: auto !important;
        min-height: 42px !important;
        padding: 9px 18px !important;
        border-radius: 9px !important;
        background: linear-gradient(180deg, rgba(30, 41, 59, 0.75) 0%, rgba(15, 23, 42, 0.85) 100%) !important;
        border: 1px solid rgba(255, 255, 255, 0.12) !important;
        border-top: 1px solid rgba(255, 255, 255, 0.20) !important;
        box-shadow: 0 3px 8px -1px rgba(0, 0, 0, 0.45), inset 0 1px 0 rgba(255, 255, 255, 0.08) !important;
        font-size: 0.84rem !important;
        font-weight: 500 !important;
        color: #94a3b8 !important;
        flex: 0 1 auto !important;
        transition: all 0.2s cubic-bezier(0.16, 1, 0.3, 1) !important;
        cursor: pointer !important;
    }

    div[data-testid="stTabs"] [role="tab"]:hover {
        background: linear-gradient(180deg, rgba(51, 65, 85, 0.85) 0%, rgba(30, 41, 59, 0.95) 100%) !important;
        border-color: rgba(56, 189, 248, 0.45) !important;
        border-top: 1px solid rgba(125, 211, 252, 0.6) !important;
        color: #f8fafc !important;
        transform: translateY(-1px) !important;
        box-shadow: 0 6px 14px -2px rgba(0, 0, 0, 0.55), 0 0 12px rgba(56, 189, 248, 0.22), inset 0 1px 0 rgba(255, 255, 255, 0.18) !important;
    }

    div[data-testid="stTabs"] [role="tab"][aria-selected="true"] {
        background: linear-gradient(180deg, rgba(14, 165, 233, 0.25) 0%, rgba(2, 132, 199, 0.12) 100%) !important;
        border: 1px solid #38bdf8 !important;
        border-top: 1px solid #7dd3fc !important;
        color: #38bdf8 !important;
        font-weight: 700 !important;
        transform: translateY(-1px) !important;
        box-shadow: 0 4px 14px -2px rgba(0, 0, 0, 0.6), 0 0 16px rgba(56, 189, 248, 0.35), inset 0 1px 0 rgba(255, 255, 255, 0.30) !important;
    }

    /* Elevate Action Download Button with matching depth */
    div[data-testid="stDownloadButton"] button {
        background: linear-gradient(180deg, rgba(56, 189, 248, 0.16) 0%, rgba(14, 165, 233, 0.24) 100%) !important;
        border: 1px solid rgba(56, 189, 248, 0.45) !important;
        border-top: 1px solid rgba(125, 211, 252, 0.65) !important;
        border-radius: 9px !important;
        box-shadow: 0 3px 10px -1px rgba(0, 0, 0, 0.45), 0 0 12px rgba(56, 189, 248, 0.18), inset 0 1px 0 rgba(255, 255, 255, 0.22) !important;
        font-weight: 600 !important;
        transition: all 0.2s cubic-bezier(0.16, 1, 0.3, 1) !important;
    }
    div[data-testid="stDownloadButton"] button:hover {
        background: linear-gradient(180deg, rgba(56, 189, 248, 0.28) 0%, rgba(14, 165, 233, 0.38) 100%) !important;
        border-color: #38bdf8 !important;
        transform: translateY(-1px) !important;
        box-shadow: 0 6px 16px -2px rgba(0, 0, 0, 0.55), 0 0 18px rgba(56, 189, 248, 0.4), inset 0 1px 0 rgba(255, 255, 255, 0.35) !important;
    }

    /* Hide Streamlit horizontal scroll chevron buttons since tabs wrap */
    div[data-testid="stTabs"] button[data-testid*="stTabsScroll"],
    div[data-testid="stTabs"] [data-testid*="stTabsScroll"] {
        display: none !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

def render_six_point_narrative(nar: dict, persona_title: str = "Active Persona"):
    """
    Renders institutional 6-point structured findings for analytical depth & evidence-backed action.
    """
    html = f"""
    <div class="narrative-card" style="margin-top: 14px;">
        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:8px;">
            <span style="font-size:0.75rem; font-weight:700; color:#38bdf8; text-transform:uppercase; letter-spacing:0.05em;">
                <span class="material-symbols-rounded" style="font-size:15px; vertical-align:-2px; margin-right:4px;">visibility</span>1. Quantitative Observation & What You See
            </span>
            <span class="badge-pill badge-sky" style="font-size:0.70rem;">{persona_title} Lens</span>
        </div>
        <div style="font-size:0.86rem; color:#e2e8f0; line-height:1.5; margin-bottom:12px;">
            {nar.get('what_you_see', '')}
        </div>

        <div style="display:grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap:12px; margin-bottom:12px;">
            <div style="background:rgba(255,255,255,0.03); border:1px solid rgba(255,255,255,0.08); border-radius:8px; padding:10px;">
                <div style="font-size:0.72rem; font-weight:700; color:#a78bfa; text-transform:uppercase; margin-bottom:4px;">
                    <span class="material-symbols-rounded" style="font-size:15px; vertical-align:-2px; margin-right:4px;">psychology</span>2. Decision Relevance ({persona_title})
                </div>
                <div style="font-size:0.82rem; color:#cbd5e1; line-height:1.45;">
                    {nar.get('why_it_matters', '')}
                </div>
            </div>
            <div style="background:rgba(255,255,255,0.03); border:1px solid rgba(255,255,255,0.08); border-radius:8px; padding:10px;">
                <div style="font-size:0.72rem; font-weight:700; color:#94a3b8; text-transform:uppercase; margin-bottom:4px;">
                    <span class="material-symbols-rounded" style="font-size:15px; vertical-align:-2px; margin-right:4px;">account_tree</span>3. Evidence Lineage & Citation
                </div>
                <div style="font-size:0.82rem; color:#cbd5e1; line-height:1.45;">
                    {nar.get('evidence_basis', '')}
                </div>
            </div>
        </div>

        <div style="background:rgba(245, 158, 11, 0.05); border:1px solid rgba(245, 158, 11, 0.2); border-radius:8px; padding:10px; margin-bottom:12px;">
            <div style="font-size:0.72rem; font-weight:700; color:#f59e0b; text-transform:uppercase; margin-bottom:4px;">
                <span class="material-symbols-rounded" style="font-size:15px; vertical-align:-2px; margin-right:4px;">balance</span>4. Alternative Explanations & Operational Context
            </div>
            <div style="font-size:0.82rem; color:#f1f5f9; line-height:1.45;">
                {nar.get('alternative_explanations', '')}
            </div>
        </div>

        <div class="action-card" style="margin:0 0 12px 0;">
            <div style="font-size:0.75rem; font-weight:700; color:#10b981; text-transform:uppercase; margin-bottom:4px;">
                <span class="material-symbols-rounded" style="font-size:15px; vertical-align:-2px; margin-right:4px;">play_circle</span>5. Conditional Actionable Recommendations
            </div>
            <div style="font-size:0.85rem; color:#e2e8f0; line-height:1.5; white-space:pre-line;">
                {nar.get('call_to_action', '')}
            </div>
        </div>

        <div style="background:rgba(56, 189, 248, 0.05); border-left:3px solid #38bdf8; border-radius:4px; padding:8px 12px;">
            <span style="font-size:0.72rem; font-weight:700; color:#38bdf8; text-transform:uppercase;">
                <span class="material-symbols-rounded" style="font-size:15px; vertical-align:-2px; margin-right:4px;">bolt</span>6. Inflection Triggers & Thresholds:
            </span>
            <span style="font-size:0.82rem; color:#e2e8f0; margin-left:6px;">
                {nar.get('inflection_triggers', '')}
            </span>
        </div>
    </div>
    """
    render_html(html)

# ─────────────────────────────────────────────────────────────────────────────
# TOP HERO SLICER & DEAL SELECTION
# ─────────────────────────────────────────────────────────────────────────────
from models import pre_ipo_evidence as ledger
from datetime import date

user = st.session_state.get("user", {})
owner = user.get("username", "")
role = user.get("role", "")
owner_companies = ledger.companies(owner) if owner else {}

deal_options = {
    "hindustan_coca_cola": "Hindustan Coca-Cola Holdings Ltd. (DRHP 2024 · ₹9,975 Cr 100% OFS · Beverage Giant)",
    "ntpc_green": "NTPC Green Energy Ltd. (RHP Nov 2024 · ₹7,500 Cr Debt Prepayment / ₹10,000 Cr Fresh)",
    "mankind_pharma": "Mankind Pharma Ltd. (DRHP 2023 · 100% OFS · Mature Cash Cow)",
    "afcons_infra": "Afcons Infrastructure Ltd. (RHP 2024 · ₹800 Cr Debt Prepayment / ₹1,250 Cr Fresh)",
    "swiggy": "Swiggy Ltd. (DRHP 2024 · ₹4,499 Cr Fresh Issue · Quick Commerce Growth)",
    "tata_technologies": "Tata Technologies Ltd. (DRHP 2023 · Zero Debt · ER&D)",
}

for cid, prof in owner_companies.items():
    if "coca" not in prof.company_name.lower() and "coca" not in cid.lower():
        deal_options[cid] = f"{prof.company_name} (Private Evidence · {prof.filing_type})"

deal_options["custom_upload"] = "+ Ingest New DRHP / RHP PDF Document..."

# Sync deal selector if user was inspecting Coca-Cola in Facts & Evidence
active_ev = st.session_state.get("evidence_company", "") or st.session_state.get("ev_active_company", "")
if ("coca" in str(active_ev).lower()) and ("pre_ipo_deal_selector" not in st.session_state or st.session_state["pre_ipo_deal_selector"] == "ntpc_green"):
    st.session_state["pre_ipo_deal_selector"] = "hindustan_coca_cola"

# Handle programmatic deal routing (e.g. from Open Deal button or Extraction)
if "target_deal_selector" in st.session_state:
    target_k = st.session_state.pop("target_deal_selector")
    if target_k in deal_options:
        st.session_state["pre_ipo_deal_selector"] = target_k

# Guard against stale selectbox key in session state
if "pre_ipo_deal_selector" in st.session_state and st.session_state["pre_ipo_deal_selector"] not in deal_options:
    st.session_state["pre_ipo_deal_selector"] = list(deal_options.keys())[0]

persona_options = {
    "cfo": "CFO / Corporate Treasurer",
    "lender": "Lender / Credit Committee",
    "investor": "Institutional Equity Analyst / Anchor",
    "retail": "Retail Investor (Plain Language)",
    "board": "Board / Investment Committee",
    "compliance": "Legal, Auditor & Compliance",
}

context_options = {
    "PUBLIC_IPO": "Public IPO (Ordinary Equity)",
    "PRIVATE_PRE_IPO": "Private Pre-IPO Placement (Negotiated)",
    "STRATEGIC_M_AND_A": "Strategic M&A / Control Buyout",
}

col_sel, col_act = st.columns([3.2, 1.0])
with col_sel:
    selected_deal_key = st.selectbox(
        "Active Pre-IPO Deal Dossier",
        options=list(deal_options.keys()),
        format_func=lambda k: deal_options[k],
        key="pre_ipo_deal_selector",
    )
    st.caption(":material/domain: Drives prospectuses, financial models & diligence tabs")

col_ctx, col_pers = st.columns(2)
with col_ctx:
    selected_context = st.selectbox(
        "Transaction Context",
        options=list(context_options.keys()),
        format_func=lambda k: context_options[k],
        key="pre_ipo_context_selector",
    )
    st.caption(":material/lock_open: Unlocks PX01–PX04 Private Questions" if selected_context != "PUBLIC_IPO" else ":material/public: Evaluates 10 Core Public IPO Questions")

with col_pers:
    selected_persona = st.selectbox(
        "Decision Persona Lens",
        options=list(persona_options.keys()),
        format_func=lambda k: persona_options[k],
        key="pre_ipo_persona_selector",
    )
    st.caption(f":material/psychology: Focuses decision cockpit for {persona_options[selected_persona].split('/')[0].strip()}")

# If user selected a private company from the dropdown
if selected_deal_key.startswith("private-"):
    prof_label = deal_options.get(selected_deal_key, "").lower()
    if "coca" in selected_deal_key.lower() or "coca" in prof_label:
        selected_deal_key = "hindustan_coca_cola"
        st.session_state["pre_ipo_deal_selector"] = "hindustan_coca_cola"
    elif get_legacy_dossier(selected_deal_key) is not None:
        pass
    else:
        st.info(":material/info: This private company evidence dossier is reviewed under **Facts & evidence review**.")
        if st.button("Open Facts & Evidence Review", type="primary", key="btn_goto_evidence_review"):
            st.session_state["evidence_company"] = selected_deal_key
            st.session_state["ev_active_company"] = selected_deal_key
            st.session_state["pre_ipo_target_workspace"] = "Facts & evidence review"
            st.rerun()
        st.stop()

dossier = None
if selected_deal_key == "custom_upload":
    col_up1, col_up2 = st.columns([3, 2])
    with col_up1:
        uploaded_file = st.file_uploader(
            "Upload Draft Red Herring Prospectus (DRHP) PDF",
            type=["pdf"],
            help="Supports electronic searchable PDFs and scanned image DRHPs via multimodal AI vision.",
        )
        custom_company_name = st.text_input("Company Name / Filing Entity", value="Novel Enterprise Limited")
        col_m1, col_m2, col_m3 = st.columns(3)
        with col_m1:
            filing_type = st.selectbox("Filing Type", ["DRHP", "RHP", "Prospectus", "Draft Shelf Prospectus"], index=0)
        with col_m2:
            filing_version = st.text_input("Filing Version / Date", value=f"Draft 1.0 ({date.today().strftime('%b %Y')})")
        with col_m3:
            filing_rights = st.text_input("Retention Rights Declaration", value="Public Regulatory Filing (SEBI ICDR 2018)")
        filing_avail_date = date.today()
    with col_up2:
        from models.runtime_config import get_gemini_api_key
        has_gemini = bool(get_gemini_api_key())
        render_html(
            """
            <div class="bento-card" style="padding:12px; margin-top:24px; border:1px solid rgba(56,189,248,0.25);">
                <div style="font-size:0.75rem; text-transform:uppercase; color:#38bdf8; font-weight:700;"><span class="material-symbols-rounded" style="font-size:14px; vertical-align:-2px; margin-right:4px;">account_tree</span>Intake & Document Intelligence</div>
                <div style="font-size:0.8rem; color:#f8fafc; margin:4px 0; font-weight:600;">1. Native Table Parser &bull; 2. IBM Docling v2.48 &bull; 3. Cloud Vision</div>
                <div style="font-size:0.75rem; color:#94a3b8; line-height:1.4;">Zero synthetic numbers. Searchable PDFs extract natively without quotas. For non-searchable scans when cloud API quota is depleted, figures default to 0.0 with comments &apos;Not extracted&apos;.</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        if not has_gemini:
            st.caption(":material/lock: Optional Cloud OCR key not set. Local extraction active (zero external quota dependency).")
        else:
            vision_model = PreIPOIngestionEngine.get_vision_model_name()
            st.caption(f":material/cloud: Cloud Vision configured ({vision_model}). Quota issues (HTTP 402/429) fallback to 0.0 'Not extracted'.")
            cloud_ocr_consent = st.checkbox("Authorize Cloud OCR for Scanned Files (External Google API Egress)", value=False, key="cloud_ocr_consent_checkbox")

    if owner_companies:
        with st.expander(f":material/library_books: Your Private Ingested Prospectuses ({len(owner_companies)} in Evidence Ledger)", expanded=True):
            st.caption("Owner-scoped private filings. Manage or review facts against retained PDF sources.")
            for lib_id, lib_prof in list(owner_companies.items()):
                col_lib1, col_lib2, col_lib3 = st.columns([4, 1.2, 1.2])
                with col_lib1:
                    st.markdown(f"**{lib_prof.company_name}**")
                    periods_str = ", ".join(p.fiscal_year for p in lib_prof.history)
                    st.caption(f"{lib_prof.filing_type} · Sector: {lib_prof.sector} · Periods: {periods_str}")
                with col_lib2:
                    if st.button("Review Facts", icon=":material/fact_check:", key=f"lib_open_{lib_id}", use_container_width=True):
                        st.session_state["evidence_company"] = lib_id
                        st.session_state["ev_active_company"] = lib_id
                        st.session_state["pre_ipo_target_workspace"] = "Facts & evidence review"
                        st.rerun()
                with col_lib3:
                    is_viewer = role not in {"admin", "researcher"}
                    del_prompt_key = f"lib_del_prompt_{lib_id}"
                    if st.button("Delete…", icon=":material/delete:", key=f"lib_del_{lib_id}", use_container_width=True, disabled=is_viewer, help="Inspect impact preview and delete company" if not is_viewer else "Viewers cannot delete"):
                        st.session_state[del_prompt_key] = not st.session_state.get(del_prompt_key, False)
                if st.session_state.get(f"lib_del_prompt_{lib_id}", False):
                    impact = ledger.get_deletion_impact(owner, lib_id)
                    aff = impact.get("affected_counts", {})
                    st.warning(
                        f"**Deletion Impact Manifest for {lib_prof.company_name}:**\n"
                        f"- Retained Documents: {aff.get('sources', 0)}\n"
                        f"- Facts & Observations: {aff.get('observations', 0) + aff.get('facts', 0)}\n"
                        f"- Evidence Snapshots: {aff.get('snapshots', 0)}\n"
                        f"- Dependent Decision Cases: {aff.get('saved_decisions', 0)}\n\n"
                        f"Permanently erasing this company will revoke all associated evidence and unlinked decisions."
                    )
                    col_c1, col_c2 = st.columns([3, 1])
                    with col_c1:
                        conf_check = st.checkbox("I confirm permanent erasure of this company", key=f"conf_box_{lib_id}")
                    with col_c2:
                        if st.button("Confirm Delete", type="primary", key=f"do_del_{lib_id}", disabled=not conf_check):
                            try:
                                ledger.delete_company(owner, role, lib_id)
                                st.session_state.pop(f"lib_del_prompt_{lib_id}", None)
                                st.session_state.pop("evidence_company", None)
                                st.session_state.pop("ev_active_company", None)
                                st.success(f"{lib_prof.company_name} deleted.")
                                st.rerun()
                            except Exception as exc:
                                st.error(str(exc))

    if uploaded_file is not None:
        import hashlib, io, time
        file_bytes = uploaded_file.getvalue()
        file_hash = hashlib.sha256(file_bytes).hexdigest()
        PARSER_VERSION = "2.2.0"
        INTAKE_SCHEMA_VERSION = "2.1.0"
        cache_key = f"pre_ipo_dossier_{file_hash}_{PARSER_VERSION}_{INTAKE_SCHEMA_VERSION}"
        extracted_flag_key = f"pre_ipo_extracted_{file_hash}_v2_2"

        # If not yet extracted, show file readiness card and Extract button
        if not st.session_state.get(extracted_flag_key, False):
            render_html(
                f"""
                <div class="bento-card" style="border:1px solid rgba(56, 189, 248, 0.4); padding:16px 20px; margin: 16px 0; background:rgba(15,23,42,0.6);">
                    <div style="display:flex; justify-content:space-between; align-items:center;">
                        <div>
                            <div style="font-size:0.75rem; text-transform:uppercase; color:#38bdf8; font-weight:700;"><span class="material-symbols-rounded" style="font-size:14px; vertical-align:-2px; margin-right:4px;">description</span>Prospectus Loaded & Ready for Intake</div>
                            <div style="font-size:1.1rem; font-weight:700; color:#f8fafc; margin-top:2px;">{uploaded_file.name}</div>
                            <div style="font-size:0.8rem; color:#94a3b8; margin-top:2px;">File Size: {len(file_bytes)/1024:.1f} KB &bull; Format: Electronic Searchable PDF</div>
                        </div>
                        <div style="text-align:right;">
                            <span style="display:inline-block; padding:4px 12px; border-radius:12px; background:rgba(16,185,129,0.15); color:#10b981; font-size:0.75rem; font-weight:700; border:1px solid rgba(16,185,129,0.3);">READY FOR EXTRACTION</span>
                        </div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

            col_btn1, col_btn2 = st.columns([2, 1])
            with col_btn1:
                extract_trigger = st.button("Run Automated Prospectus Extraction & Forensic Audit", icon=":material/play_arrow:", type="primary", use_container_width=True)

            if extract_trigger:
                if not owner:
                    st.error("Please sign in to ingest filings into your private evidence workspace.")
                    st.stop()
                if role not in {"admin", "researcher"}:
                    st.error("Read-only profile: Viewers cannot ingest or upload private prospectuses.")
                    st.stop()

                with st.spinner("Extracting disclosures & persisting to owner evidence ledger..."):
                    cloud_consent_val = st.session_state.get("cloud_ocr_consent_checkbox", False)
                    from models.pre_ipo_docling import MultiEngineIngestionOrchestrator
                    # Execute multi-engine orchestrator with Docling benchmark and native fallback
                    struct_res = MultiEngineIngestionOrchestrator.ingest(
                        file_bytes,
                        company_name_hint=custom_company_name,
                        page_limit=20
                    )
                    dossier_res = PreIPOIngestionEngine.ingest_document(
                        io.BytesIO(file_bytes),
                        company_name_hint=custom_company_name,
                        allow_external_cloud_ocr=cloud_consent_val,
                    )
                    metadata = {
                        "title": f"{custom_company_name} {filing_type}",
                        "filing_type": filing_type,
                        "version": filing_version,
                        "available_by": str(filing_avail_date),
                        "rights": filing_rights,
                        "official_url": "Uploaded document",
                        "issuer": custom_company_name,
                        "retention_policy": "Retained for Pre-IPO diligence",
                        "engine": struct_res.engine,
                        "engine_version": struct_res.engine_version,
                        "extraction_status": struct_res.status,
                    }
                    company_id = ledger.import_dossier(
                        owner, role, custom_company_name, dossier_res, file_bytes, metadata
                    )

                st.session_state[cache_key] = dossier_res
                st.session_state[extracted_flag_key] = True
                st.session_state["ev_pending_company"] = company_id
                st.session_state["evidence_company"] = company_id
                st.session_state["ev_active_company"] = company_id
                st.session_state["pre_ipo_target_workspace"] = "Facts & evidence review"
                st.rerun()
            else:
                st.info("Click **'Run Automated Prospectus Extraction & Forensic Audit'** above to begin automated parsing and validation.", icon=":material/info:")
                st.stop()

        dossier = st.session_state[cache_key]

        # Calculate truthful confidence score based on verified items
        reconciled_count = len([it for it in dossier.audit_report if it.status in ("FOUND_AND_RECONCILED", "CONVERTED_AND_NORMALIZED")])
        total_audit_count = max(len(dossier.audit_report), 1)
        conf_pct = int(round((reconciled_count / total_audit_count) * 100))

        is_unrated = dossier.ic_verdict.underwriting_verdict == "INSUFFICIENT_DISCLOSURES_UNRATED"
        badge_label = "INSUFFICIENT DISCLOSURES (UNRATED)" if is_unrated else "CANDIDATES EXTRACTED · AWAITING REVIEW"
        badge_color = "#f43f5e" if is_unrated else "#38bdf8"
        badge_bg = "rgba(244,63,94,0.15)" if is_unrated else "rgba(56,189,248,0.15)"
        badge_border = "rgba(244,63,94,0.3)" if is_unrated else "rgba(56,189,248,0.3)"

        # Display Extraction & Validation Summary Card
        render_html(
            f"""
            <div class="bento-card" style="border: 1px solid {badge_border}; background: {badge_bg}; padding: 16px 20px; margin-bottom: 20px;">
                <div style="display:flex; justify-content:space-between; align-items:center;">
                    <div>
                        <span style="font-size:0.75rem; text-transform:uppercase; color:{badge_color}; font-weight:700;"><span class="material-symbols-rounded" style="font-size:14px; vertical-align:-2px; margin-right:4px;">fact_check</span>Extraction Candidates Loaded</span>
                        <div style="font-size:1.15rem; font-weight:700; color:#f8fafc; margin-top:2px;">{dossier.company_name}</div>
                        <div style="font-size:0.8rem; color:#94a3b8; margin-top:2px;">
                            Source: <b>{uploaded_file.name}</b> &bull; Filing: <b>{dossier.filing_type}</b> &bull; Extracted Items: <b style="color:{badge_color};">{reconciled_count}/{total_audit_count} ({conf_pct}% matched)</b>
                        </div>
                    </div>
                    <div style="text-align:right;">
                        <span style="display:inline-block; padding:4px 12px; border-radius:12px; background:{badge_bg}; color:{badge_color}; font-size:0.8rem; font-weight:700; border:1px solid {badge_border};">
                            {badge_label}
                        </span>
                    </div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        with st.expander(":material/checklist: View Extraction Summary & Verification Audit Trail", expanded=False):
            col_v1, col_v2 = st.columns(2)
            with col_v1:
                st.markdown("##### :material/check_circle: Extracted Metrics & Lineage")
                st.markdown(f"- **Reporting Periods:** {len(dossier.history)} period(s) extracted: {', '.join([h.fiscal_year for h in dossier.history]) if dossier.history else 'None'}.")
                if dossier.history:
                    lat = dossier.latest_financials
                    st.markdown(f"- **Section V ({lat.fiscal_year}):** Rev ₹{lat.revenue_ops_cr:,.1f} Cr, EBITDA ₹{lat.ebitda_cr:,.1f} Cr, PAT ₹{lat.pat_cr:,.1f} Cr, CFO ₹{lat.cfo_cr:,.1f} Cr.")
                ind = dossier.indebtedness
                st.markdown(f"- **Section VI Indebtedness:** Term Loans ₹{ind.secured_term_loans_cr:,.1f} Cr, WC ₹{ind.working_capital_loans_cr:,.1f} Cr, Leases ₹{ind.lease_liabilities_ind_as_116_cr:,.1f} Cr, Cash ₹{ind.cash_and_equivalents_cr:,.1f} Cr.")
                st.markdown(f"- **Governance Metrics:** Promoter Pledge {dossier.governance.promoter_pledge_pct:.1f}%, Independent Directors {dossier.governance.independent_directors_pct:.0f}%.")
            with col_v2:
                st.markdown("##### :material/warning: Identified Data Gaps & Limitations")
                if dossier.limitations:
                    for lim in dossier.limitations:
                        st.markdown(f"- **[{lim.gap_id}] {lim.item_name}:** {lim.why_it_matters}")
                else:
                    st.markdown("- No blocking data gaps identified. Values await human review and sign-off.")
    else:
        st.info("Upload a Draft Red Herring Prospectus (DRHP) or Red Herring Prospectus (RHP) PDF above, or select an existing deal from the dropdown.", icon=":material/info:")
        render_html(
            """
            <div class="bento-card" style="border: 1px dashed rgba(56, 189, 248, 0.4); text-align:center; padding: 30px 20px; margin-bottom: 20px;">
                <div style="font-size:2rem; margin-bottom:6px;"><span class="material-symbols-rounded" style="font-size:36px; color:#64748b;">upload_file</span></div>
                <div style="font-size:1.1rem; font-weight:700; color:#f8fafc;">Awaiting DRHP / RHP Document Intake</div>
                <div style="font-size:0.84rem; color:#94a3b8; max-width:620px; margin:6px auto 0 auto; line-height:1.5;">
                    Upload an official SEBI-filed prospectus PDF above to extract metrics and automatically add it to your dropdown registry.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.stop()
else:
    # HCCH Legacy Registry Disconnection & Dossier Boundary (P0-01 Containment)
    active_owner = (
        st.session_state.get("authenticated_user")
        or st.session_state.get("username")
        or (st.session_state.get("user", {}).get("username") if isinstance(st.session_state.get("user"), dict) else None)
    )
    if not active_owner:
        st.warning("Please sign in to access Pre-IPO DRHP Intelligence.")
        st.stop()

    active_snapshot_id = st.session_state.get("pre_ipo_active_snapshot_id")
    active_snapshot_status = st.session_state.get("pre_ipo_active_snapshot_status", "UNREVIEWED")
    active_snapshot_hash = st.session_state.get("pre_ipo_active_snapshot_hash")

    from models.pre_ipo_dossier_resolver import resolve_dossier, DossierResolutionStatus
    resolution = resolve_dossier(
        selected_deal_key=selected_deal_key,
        owner=active_owner,
        snapshot_id=active_snapshot_id,
        custom_dossier=dossier,
    )

    if resolution.status == DossierResolutionStatus.BLOCKED_EVIDENCE_NOT_ACCEPTED:
        render_html("""
        <div style="background: rgba(245, 158, 11, 0.08); border: 1px solid rgba(245, 158, 11, 0.3); border-radius: 12px; padding: 24px; margin: 20px 0;">
            <div style="display: flex; align-items: center; gap: 12px; margin-bottom: 12px;">
                <span class="material-symbols-rounded" style="color: #f59e0b; font-size: 28px;">gavel</span>
                <h3 style="color: #f8fafc; margin: 0; font-size: 1.25rem;">HCCH Statutory Evidence Containment Active (P0-01)</h3>
            </div>
            <p style="color: #cbd5e1; font-size: 0.92rem; line-height: 1.6; margin-bottom: 16px;">
                Hindustan Coca-Cola Beverages is strictly disconnected from the unreviewed built-in registry.
                Under SEBI ICDR regulations and P0-01 containment, production ratio calculations, Dickinson stage classification,
                and analytical deck export are <strong>blocked</strong> until an official filing snapshot is reviewed and accepted.
            </p>
            <div style="background: rgba(15, 23, 42, 0.6); border-radius: 8px; padding: 12px 16px; margin-bottom: 16px;">
                <div style="color: #94a3b8; font-size: 0.8rem; text-transform: uppercase; font-weight: 700; margin-bottom: 4px;">Next Required Action</div>
                <div style="color: #38bdf8; font-size: 0.88rem;">Open <strong>Tab 2 Provenance Ledger</strong> or upload the official 513-page DRHP to audit and accept source observations.</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        st.stop()
    elif resolution.status == DossierResolutionStatus.BLOCKED_EVIDENCE_DOSSIER_ADAPTER_UNAVAILABLE:
        render_html(f"""
        <div style="background: rgba(56, 189, 248, 0.08); border: 1px solid rgba(56, 189, 248, 0.3); border-radius: 12px; padding: 24px; margin: 20px 0;">
            <div style="display: flex; align-items: center; gap: 12px; margin-bottom: 12px;">
                <span class="material-symbols-rounded" style="color: #38bdf8; font-size: 28px;">construction</span>
                <h3 style="color: #f8fafc; margin: 0; font-size: 1.25rem;">HCCH Evidence-to-Dossier Adapter Pending (P0-01)</h3>
            </div>
            <p style="color: #cbd5e1; font-size: 0.92rem; line-height: 1.6; margin-bottom: 16px;">
                {resolution.reason}
            </p>
            <div style="background: rgba(15, 23, 42, 0.6); border-radius: 8px; padding: 12px 16px; margin-bottom: 16px;">
                <div style="color: #94a3b8; font-size: 0.8rem; text-transform: uppercase; font-weight: 700; margin-bottom: 4px;">Next Required Action</div>
                <div style="color: #38bdf8; font-size: 0.88rem;">{resolution.next_action}</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        st.stop()

    dossier = resolution.dossier
    dossier_origin = resolution.origin

# Evaluate analytical capability gate (PR 1 Containment)
is_hcch = is_hcch_entity(selected_deal_key, getattr(dossier, "company_name", ""), getattr(dossier, "cin", ""))
active_owner = (
    st.session_state.get("authenticated_user")
    or st.session_state.get("username")
    or (st.session_state.get("user", {}).get("username") if isinstance(st.session_state.get("user"), dict) else None)
)
if not active_owner:
    st.warning("Please sign in to access Pre-IPO DRHP Intelligence.")
    st.stop()

active_snapshot_id = st.session_state.get("pre_ipo_active_snapshot_id")
active_snapshot_status = st.session_state.get("pre_ipo_active_snapshot_status", "UNREVIEWED")
active_snapshot_hash = st.session_state.get("pre_ipo_active_snapshot_hash")

gate_decision = evaluate_capability_gate(
    owner=active_owner,
    company=selected_deal_key,
    capability=CapabilityType.FINANCIAL_ANALYSIS,
    snapshot_id=active_snapshot_id,
    snapshot_status=active_snapshot_status,
    origin=dossier_origin,
    is_production=True,
    is_unpriced=bool(dossier and (not dossier.total_issue_size_cr or dossier.total_issue_size_cr <= 0)),
)

if not gate_decision.allowed:
    st.warning(f"Analysis Blocked: {gate_decision.reason}")
    st.info(f"Required action: {gate_decision.next_action}")
    st.stop()

eligibility = assess_analysis_eligibility(dossier)
if not eligibility.allowed:
    with st.container(key="pre_ipo_intake_gate"):
        if st.session_state.get("theme") == "light":
            render_html('''<style>
            .st-key-pre_ipo_intake_gate [data-testid="stAlert"] p { color: #0f172a !important; }
            .st-key-pre_ipo_intake_gate summary { background: #fff !important; color: #0f172a !important; }
            .st-key-pre_ipo_intake_gate summary p { color: #0f172a !important; }
            </style>''')
        st.warning(f"Analysis Blocked ({eligibility.state.value}): Document intake is incomplete. Ratio calculations, underwriting conclusions and analytical deck export are strictly blocked.")
        if eligibility.gaps:
            st.dataframe([{"Gap ID": item.gap_id, "Status": item.current_status,
                           "Required action": item.recommended_diligence_request} for item in eligibility.gaps], hide_index=True)
        for r in eligibility.reasons:
            st.caption(f":material/block: {r}")
        with st.expander("Document intake diagnostics", expanded=True):
            st.dataframe([{"Field": item.field_name, "Status": item.status,
                           "Detail": item.raw_extracted_value} for item in dossier.audit_report], hide_index=True)
    st.stop()

latest = dossier.latest_financials
latest_contract = FinancialStatementsContract.from_financial_metric(latest, dossier.indebtedness)
stage_name, pattern = latest_contract.dickinson_classification

with col_act:
    render_html(
        "<label style='font-size:0.875rem; font-weight:500; color:#94a3b8; display:block; margin-bottom:4px; height:24px; line-height:24px;'>"
        "<span class='material-symbols-rounded' style='font-size:15px; vertical-align:-2px; margin-right:4px;'>slideshow</span>Pitch Deck Action"
        "</label>",
        unsafe_allow_html=True,
    )
    if is_hcch and not gate_decision.allowed:
        st.button(
            "Export Blocked (Awaiting Evidence)",
            icon=":material/block:",
            disabled=True,
            use_container_width=True,
            help="Export is strictly blocked under P0-01 containment until the official 513-page DRHP is reviewed and accepted."
        )
        st.caption(":material/block: P0-01 Containment Active")
    else:
        try:
            wacc_calc = calculate_wacc_and_roic(
                dossier,
                is_blocked=bool(is_hcch and not gate_decision.allowed),
                blocked_reason="P0-01 Containment active: awaiting official DRHP review and acceptance."
            )
            dcf_calc = calculate_reverse_dcf_hurdle(
                dossier,
                is_blocked=bool(is_hcch and not gate_decision.allowed),
                blocked_reason="P0-01 Containment active: awaiting official DRHP review and acceptance."
            )
            deck_bytes = generate_pre_ipo_board_deck(
                dossier=dossier,
                snapshot_id=active_snapshot_id,
                snapshot_status=active_snapshot_status,
                snapshot_hash=active_snapshot_hash,
                result_snapshot_hash=active_snapshot_hash,
                is_production=True,
                owner=active_owner,
                company=selected_deal_key,
                wacc_result=wacc_calc,
                reverse_dcf_result=dcf_calc,
                decision_support_policy="NEUTRAL_EVIDENCE_BASED",
            )
            st.download_button(
                label="Export Deck (PPTX)",
                icon=":material/download:",
                data=deck_bytes,
                file_name=f"{dossier.deal_id}_board_pitch_deck.pptx",
                mime="application/vnd.openxmlformats-officedocument.presentationml.presentation",
                use_container_width=True,
            )
            st.caption(":material/download: 1-Click Board PPTX Export")
        except ExportBlockedError as e:
            st.button("Export Blocked", icon=":material/block:", disabled=True, use_container_width=True)
            st.caption(f":material/block: {str(e)}")

# Feedback toasts on selection change
prev_deal = st.session_state.get("_prev_pre_ipo_deal")
prev_persona = st.session_state.get("_prev_pre_ipo_persona")
prev_context = st.session_state.get("_prev_pre_ipo_context")

if prev_deal and prev_deal != selected_deal_key:
    st.toast(f"Active deal: {dossier.company_name}", icon=":material/domain:")
if prev_persona and prev_persona != selected_persona:
    st.toast(f"Decision Lens: {persona_options[selected_persona]} active", icon=":material/psychology:")
if prev_context and prev_context != selected_context:
    st.toast(f"Context: {context_options[selected_context]} ({'14 Questions' if selected_context != 'PUBLIC_IPO' else '10 Core Questions'})", icon=":material/handshake:")

st.session_state["_prev_pre_ipo_deal"] = selected_deal_key
st.session_state["_prev_pre_ipo_persona"] = selected_persona
st.session_state["_prev_pre_ipo_context"] = selected_context

# Compact Scope Indicator Bar
scope_bar_html = f"""
<div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:8px; padding:6px 14px; margin-bottom:12px; background:rgba(255,255,255,0.03); border:1px solid rgba(255,255,255,0.08); border-radius:8px; font-size:0.78rem;">
    <div style="display:flex; align-items:center; gap:12px; flex-wrap:wrap;">
        <span style="color:#94a3b8;"><span class="material-symbols-rounded" style="font-size:14px; vertical-align:-2px; margin-right:4px;">business</span>Prospectus: <b style="color:#f8fafc;">{dossier.company_name}</b></span>
        <span style="color:#64748b;">•</span>
        <span style="color:#94a3b8;"><span class="material-symbols-rounded" style="font-size:14px; vertical-align:-2px; margin-right:4px;">handshake</span>Framework: <b style="color:#f59e0b;">{context_options[selected_context]}</b></span>
        <span style="color:#64748b;">•</span>
        <span style="color:#94a3b8;"><span class="material-symbols-rounded" style="font-size:14px; vertical-align:-2px; margin-right:4px;">psychology</span>Active Lens: <b style="color:#38bdf8;">{persona_options[selected_persona]}</b></span>
    </div>
    <div style="color:#64748b; font-size:0.72rem;">
        <span class="material-symbols-rounded" style="font-size:13px; vertical-align:-2px; margin-right:2px;">info</span>Persona focuses decision priorities & narrative; audited filing facts remain constant.
    </div>
</div>
"""
render_html(scope_bar_html)

if is_hcch and not gate_decision.allowed:
    st.warning(
        "⚠️ **CORRECTION & AUDIT NOTICE (P0-01 Containment):** "
        "Hindustan Coca-Cola Holdings Limited's built-in registry dossier has been contained and superseded. "
        "Under SEBI ICDR 2018 statutory guidelines, real analytical processing (Offer Valuation, WACC/ROIC, Reverse DCF, and Board Deck generation) "
        "is strictly **BLOCKED** until the 513-page parent DRHP is fully indexed and its evidence ledger reviewed and accepted in Tab 2 (Provenance Ledger). "
        "All values shown below are candidate unreviewed disclosures and cannot be used for investment, credit, or underwriting decisions."
    )
elif dossier_origin == "LEGACY_REGISTRY":
    st.info(
        "ℹ️ **SYNTHETIC BENCHMARK EXAMPLE — NOT VERIFIED FILING EVIDENCE:** "
        "This dossier is loaded from the legacy benchmark suite for interface evaluation. "
        "It is not accepted regulatory filing evidence."
    )

# ─────────────────────────────────────────────────────────────────────────────
# PANEL 1: SOVEREIGN HERO OFFERING DNA (Rendered clean without code blocks)
# ─────────────────────────────────────────────────────────────────────────────
badge_class = "badge-emerald" if "Mature" in stage_name else "badge-amber" if "Growth" in stage_name else "badge-rose"

containment_badge = (
    '<span class="badge-pill badge-rose" style="margin-left:6px;">⚠️ CONTAINED — AWAITING EVIDENCE REVIEW</span>'
    if (is_hcch and not gate_decision.allowed)
    else (
        '<span class="badge-pill badge-purple" style="margin-left:6px;">SYNTHETIC EXAMPLE</span>'
        if dossier_origin == "LEGACY_REGISTRY"
        else '<span class="badge-pill badge-purple" style="margin-left:6px;">SEBI ICDR 2018 Restated</span>'
    )
)

if dossier.total_issue_size_cr and dossier.total_issue_size_cr > 0:
    offering_title = "Total Offering Value"
    offering_main = f"₹{dossier.total_issue_size_cr:,.2f} Cr"
    offering_split = (
        f'Split: <strong style="color:#10b981;">{dossier.fresh_issue_pct:.0f}% Fresh</strong> (₹{dossier.fresh_issue_cr:,.1f} Cr) · '
        f'<strong style="color:#f59e0b;">{dossier.ofs_pct:.0f}% OFS</strong> (₹{dossier.ofs_cr:,.1f} Cr)'
    )
elif dossier.offered_shares_count:
    offering_title = "Offering Size (Equity Shares)"
    offering_main = f"{dossier.offered_shares_count:,} Shares"
    offering_split = (
        f'Structure: <strong style="color:#f59e0b;">100% OFS</strong> (₹[●] Undisclosed) · '
        f'<strong style="color:#10b981;">0% Fresh</strong> (Nil Issue)'
    )
else:
    offering_title = "Total Offering Value"
    offering_main = "Undisclosed [●]"
    offering_split = "Statutory Book-Building Discovery at RHP Stage"

hero_html = f"""
<div class="bento-card" style="border-left: 4px solid #38bdf8;">
    <div style="display:flex; justify-content:space-between; align-items:flex-start; flex-wrap:wrap; gap:12px;">
        <div>
            <span class="badge-pill badge-sky">{dossier.filing_type} · {dossier.filing_date}</span>
            <span class="badge-pill {badge_class}" style="margin-left:6px;">Dickinson: {stage_name} {pattern}</span>
            {containment_badge}
            <span class="badge-pill badge-amber" style="margin-left:6px;">Context: {context_options[selected_context]}</span>
            <h1 style="color:#ffffff; font-size:1.85rem; font-weight:800; margin:8px 0 4px 0;">{dossier.company_name}</h1>
            <div style="color:#94a3b8; font-size:0.85rem;">
                Sector: <strong style="color:#f1f5f9;">{dossier.sector}</strong> · Listing: <strong>{', '.join(dossier.exchange_listing)}</strong>
            </div>
        </div>
        <div style="text-align:right;">
            <div style="color:#94a3b8; font-size:0.75rem; text-transform:uppercase; letter-spacing:0.05em;">{offering_title}</div>
            <div class="metric-value" style="color:#38bdf8; font-size:2.0rem; font-weight:800; line-height:1.1;">
                {offering_main}
            </div>
            <div style="color:#cbd5e1; font-size:0.80rem; margin-top:4px;">
                {offering_split}
            </div>
        </div>
    </div>
    <div style="margin-top:14px; background:rgba(0,0,0,0.3); height:8px; border-radius:9999px; overflow:hidden; display:flex;">
        <div style="width:{dossier.fresh_issue_pct}%; background:#10b981;" title="Fresh Issue (Treasury Capital)"></div>
        <div style="width:{dossier.ofs_pct}%; background:#f59e0b;" title="Offer for Sale (Selling Shareholders)"></div>
    </div>
    <div style="margin-top:10px; font-size:0.75rem; color:#64748b;">
        BRLM Syndicate: {', '.join(dossier.brlm_bankers)}
    </div>
</div>
"""
render_html(hero_html)

# ─────────────────────────────────────────────────────────────────────────────
# EXECUTIVE PERSONA DECISION COCKPIT (Clean rendering with zero-indent lines)
# ─────────────────────────────────────────────────────────────────────────────
p_view = generate_persona_decision_view(
    dossier,
    persona=selected_persona,
    is_blocked=bool(is_hcch and not gate_decision.allowed),
    blocked_reason="Filing review incomplete under P0-01 containment." if (is_hcch and not gate_decision.allowed) else "",
)

metric_cards_html = "".join([
    f'<div style="background:rgba(255,255,255,0.03); border:1px solid rgba(255,255,255,0.07); border-radius:6px; padding:8px 12px;">'
    f'<div style="font-size:0.70rem; color:#94a3b8; text-transform:uppercase;">{m[0]}</div>'
    f'<div style="font-size:1.15rem; font-weight:700; color:#38bdf8; margin-top:2px;">{m[1]}</div>'
    f'</div>'
    for m in p_view['key_metrics']
])

cockpit_html = f"""
<div class="bento-card" style="margin-top:14px; border: 1px solid rgba(56, 189, 248, 0.3); background: linear-gradient(135deg, rgba(15, 23, 42, 0.8) 0%, rgba(30, 41, 59, 0.8) 100%);">
    <div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:8px; margin-bottom:10px;">
        <div>
            <span class="badge-pill badge-sky">{persona_options[selected_persona]}</span>
            <span style="color:#94a3b8; font-size:0.80rem; margin-left:8px;">Focus: <strong style="color:#f1f5f9;">{p_view['focus']}</strong></span>
        </div>
        <div style="font-size:0.75rem; color:#94a3b8;">
            Active Governance: Persona alters decision weighting & action playbooks; issuer facts remain immutable.
        </div>
    </div>

    <div style="background:rgba(0,0,0,0.25); border-left:3px solid #38bdf8; border-radius:6px; padding:10px 14px; margin-bottom:12px;">
        <div style="font-size:0.75rem; font-weight:700; color:#38bdf8; text-transform:uppercase;">Primary Decision Question</div>
        <div style="font-size:0.95rem; font-weight:600; color:#ffffff; margin-top:2px;">{p_view['decision_question']}</div>
    </div>

    <div style="display:grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap:10px; margin-bottom:12px;">
        {metric_cards_html}
    </div>

    <div style="display:grid; grid-template-columns: repeat(auto-fit, minmax(320px, 1fr)); gap:12px;">
        <div class="action-card" style="margin:0;">
            <div style="font-size:0.75rem; font-weight:700; color:#10b981; text-transform:uppercase; margin-bottom:4px;">
                <span class="material-symbols-rounded" style="font-size:14px; vertical-align:-2px; margin-right:4px;">ads_click</span>RECOMMENDED STRATEGIC ACTION
            </div>
            <div style="font-size:0.84rem; color:#f8fafc; line-height:1.45;">
                {p_view['recommendation']}
            </div>
        </div>
        <div style="background:rgba(245, 158, 11, 0.05); border:1px solid rgba(245, 158, 11, 0.2); border-radius:8px; padding:10px 14px;">
            <div style="font-size:0.75rem; font-weight:700; color:#f59e0b; text-transform:uppercase; margin-bottom:4px;">
                <span class="material-symbols-rounded" style="font-size:14px; vertical-align:-2px; margin-right:4px;">balance</span>MATERIAL TRADE-OFFS & DILEMMAS
            </div>
            <div style="font-size:0.84rem; color:#e2e8f0; line-height:1.45;">
                {p_view['trade_offs']}
            </div>
        </div>
    </div>
</div>
"""
render_html(cockpit_html)

# ─────────────────────────────────────────────────────────────────────────────
# MULTI-LEVEL LOGICAL TAB ARCHITECTURE (PRD SECTION 5 SPECIFICATION)
# ─────────────────────────────────────────────────────────────────────────────
(
    tab_overview,
    tab_provenance,
    tab_disclosures,
    tab_equity_thesis,
    tab_workpapers,
    tab_crosswalk,
    tab_ic_action,
) = st.tabs([
    ":material/domain: Company Overview",
    ":material/verified: Extracted Disclosures & Provenance Ledger",
    ":material/fact_check: Lineage Audit Card",
    f":material/quiz: Investor Questions & Thesis ({'14 Questions' if selected_context != 'PUBLIC_IPO' else '10 Core'})",
    ":material/analytics: Detailed Workpapers",
    ":material/sync_alt: CMIE Reference Crosswalk",
    ":material/gavel: IC Stance & Action Register",
])

# ═════════════════════════════════════════════════════════════════════════════
# LEVEL 1 - TAB 1: COMPANY OVERVIEW & ECONOMIC ENGINE
# ═════════════════════════════════════════════════════════════════════════════
with tab_overview:
    bg = dossier.background
    render_html('<div class="bento-subtitle">Section IV Business Overview · SEBI ICDR 2018 Disclosures</div>', unsafe_allow_html=True)
    render_html('<div class="bento-title">Corporate Background & Economic Engine</div>', unsafe_allow_html=True)

    c_ov1, c_ov2 = st.columns([3, 2])
    with c_ov1:
        desc_text = bg.business_model_summary if bg else f"Issuer operates as a premier enterprise in {dossier.sector}."
        rev_engine = bg.revenue_model if bg else "Commercial operational revenue."
        pedigree = bg.promoter_and_management_pedigree if bg else "Disclosed in DRHP Section VI."
        cutoff = bg.filing_cutoff_date if bg else dossier.filing_date

        ov_card_html = f"""
        <div class="bento-card" style="border-left:4px solid #38bdf8;">
            <div style="font-size:0.75rem; font-weight:700; color:#38bdf8; text-transform:uppercase;">Core Economic Engine</div>
            <div style="font-size:1.15rem; font-weight:700; color:#ffffff; margin:6px 0 10px 0;">{dossier.company_name}</div>
            <div style="font-size:0.88rem; color:#e2e8f0; line-height:1.5; margin-bottom:12px;">{desc_text}</div>
            <hr style="border-color:rgba(255,255,255,0.08); margin:10px 0;">
            <div style="font-size:0.80rem; color:#94a3b8;">
                <strong style="color:#f1f5f9;">Revenue Model:</strong> {rev_engine}<br>
                <strong style="color:#f1f5f9;">Promoter Pedigree:</strong> {pedigree}<br>
                <strong style="color:#f59e0b;">Filing Cutoff Date:</strong> {cutoff} (Filing-time facts separated from subsequent events)
            </div>
        </div>
        """
        render_html(ov_card_html)

    with c_ov2:
        cin_text = bg.cin if (bg and bg.cin) else "Undisclosed / Not Applicable"
        inc_year = bg.incorporation_year if bg else 2000
        hq_loc = bg.headquarters if bg else "India"
        l_form = bg.legal_form if bg else "Public Limited Company"
        
        corp_id_html = f"""
        <div class="bento-card">
            <div style="font-size:0.75rem; font-weight:700; color:#a78bfa; text-transform:uppercase;">Corporate Identity & Governance Profile</div>
            <div style="margin-top:10px; font-size:0.84rem; color:#cbd5e1; line-height:1.7;">
                • <strong>CIN:</strong> <span class="financial-num">{cin_text}</span><br>
                • <strong>Incorporation Year:</strong> {inc_year}<br>
                • <strong>Corporate Headquarters:</strong> {hq_loc}<br>
                • <strong>Legal Structure:</strong> {l_form}<br>
                • <strong>Listed Exchanges:</strong> {', '.join(dossier.exchange_listing)}<br>
                • <strong>Lead Bankers (BRLMs):</strong> {len(dossier.brlm_bankers)} Tier-1 Investment Banks
            </div>
        </div>
        """
        render_html(corp_id_html)

    render_html('<div class="bento-subtitle" style="margin-top:16px;">Product Portfolios & Segmental Breakdown</div>', unsafe_allow_html=True)
    render_html('<div class="bento-title">Core Operating Lines & Segmental Revenue Contribution</div>', unsafe_allow_html=True)
    prods = bg.core_products_and_services if bg else []
    if prods:
        p_rows = []
        for pr in prods:
            p_rows.append({
                "Product / Service Line": pr.get("name", ""),
                "Revenue Contribution (%)": f"{pr.get('revenue_pct', 0):.1f}%",
                "Operational Description & Market Position": pr.get("description", ""),
            })
        st.dataframe(pd.DataFrame(p_rows), use_container_width=True, hide_index=True)
    else:
        st.info("Product breakdown detailed in Section V restated notes.")

    # Dedicated full-row Geographic Revenue Split with regional commentary
    geo = bg.geographic_presence if (bg and bg.geographic_presence) else {"Domestic (India)": 100.0}
    c_geo1, c_geo2 = st.columns([1.5, 2.5])
    with c_geo1:
        render_html('<div class="bento-subtitle" style="margin-top:14px;">Market Dispersion</div>', unsafe_allow_html=True)
        render_html('<div class="bento-title">Geographic Revenue Split</div>', unsafe_allow_html=True)
        fig_geo = go.Figure(data=[go.Pie(labels=list(geo.keys()), values=list(geo.values()), hole=0.55, marker_colors=["#38bdf8", "#10b981", "#f59e0b"])])
        fig_geo.update_layout(height=210, margin=dict(l=10, r=10, t=10, b=10), paper_bgcolor="rgba(0,0,0,0)", font=dict(color="#cbd5e1"))
        st.plotly_chart(fig_geo, use_container_width=True)
    with c_geo2:
        render_html('<div class="bento-subtitle" style="margin-top:14px;">Domestic vs Export Territory Exposure</div>', unsafe_allow_html=True)
        geo_summary = "".join([f"<li style='margin-bottom:6px;'><strong>{k}:</strong> {v:.1f}% of total consolidated revenue</li>" for k, v in geo.items()])
        render_html(f"""
        <div class="bento-card" style="margin-top:10px;">
            <div style="font-size:0.75rem; text-transform:uppercase; color:#94a3b8; font-weight:700;">Jurisdictional Footprint</div>
            <ul style="color:#f8fafc; font-size:0.85rem; line-height:1.6; margin:8px 0 0 16px; padding:0;">
                {geo_summary}
            </ul>
            <div style="font-size:0.78rem; color:#94a3b8; margin-top:8px;">SEBI ICDR 2018 Section IV geographic concentration risk profile.</div>
        </div>
        """, unsafe_allow_html=True)

    # Material Operational Dependencies
    deps = bg.material_operational_dependencies if bg else []
    if deps:
        dep_html = f"""
        <div class="narrative-card" style="border-left:4px solid #f43f5e; margin-top:10px;">
            <div style="font-size:0.75rem; font-weight:700; color:#f43f5e; text-transform:uppercase; margin-bottom:4px;">
                <span class="material-symbols-rounded" style="font-size:14px; vertical-align:-2px; margin-right:4px;">warning</span>MATERIAL OPERATIONAL DEPENDENCIES & REGULATORY CONSTRAINTS
            </div>
            <div style="font-size:0.84rem; color:#e2e8f0; line-height:1.45;">
                {'<br>'.join(['• ' + d for d in deps])}
            </div>
        </div>
        """
        render_html(dep_html)

# ═════════════════════════════════════════════════════════════════════════════
# LEVEL 1 - TAB 2: EXTRACTED DISCLOSURES & STATUTORY PROVENANCE LEDGER
# ═════════════════════════════════════════════════════════════════════════════
with tab_provenance:
    render_provenance_ledger_tab(dossier)

# ═════════════════════════════════════════════════════════════════════════════
# LEVEL 1 - TAB 3: EXTRACTED CANDIDATE DISCLOSURES & LINEAGE AUDIT CARD
# ═════════════════════════════════════════════════════════════════════════════
with tab_disclosures:
    render_html('<div class="bento-subtitle">Automated Provenance & Anti-Fabrication Verification · SEBI ICDR 2018</div>', unsafe_allow_html=True)
    render_html('<div class="bento-title">Extracted Candidate Disclosures & Lineage Audit Card</div>', unsafe_allow_html=True)

    col_ad1, col_ad2 = st.columns([3, 1])
    with col_ad1:
        st.caption("All extracted financial metrics are candidates until verified by an authorized independent credit reviewer. Citation anchors reflect exact source statements.")
    with col_ad2:
        rev_count = len([it for it in dossier.audit_report if it.status in ("FOUND_AND_RECONCILED", "CONVERTED_AND_NORMALIZED")])
        tot_count = max(len(dossier.audit_report), 1)
        st.metric("Extraction Confidence", f"{int(round(rev_count/tot_count*100))}%", f"{rev_count}/{tot_count} verified")

    st.markdown("##### :material/table_chart: Line-Item Audit & Citation Provenance")
    if dossier.audit_report:
        audit_rows = []
        for it in dossier.audit_report:
            audit_rows.append({
                "Financial Variable": it.field_name,
                "Raw Extracted Text": it.raw_extracted_value,
                "Normalized Metric": it.normalized_metric,
                "Audit Status": it.status,
                "Citation / Anchor": it.citation,
                "Confidence Score": f"{it.confidence_score*100:.0f}%",
            })
        st.table(audit_rows)
    else:
        st.info("No audit items recorded for this document.", icon=":material/info:")

    st.markdown("##### :material/report_problem: Statutory Disclosures & Data Gaps Register")
    if dossier.limitations:
        gap_rows = []
        for g in dossier.limitations:
            gap_rows.append({
                "Gap ID": g.gap_id,
                "Affected Dimension": g.affected_dimension,
                "Status": g.current_status,
                "Why It Matters": g.why_it_matters,
                "Blocked Action": g.blocked_decision_or_recommendation,
                "Recommended Diligence Request": g.recommended_diligence_request,
            })
        st.table(gap_rows)
    else:
        st.success("Zero statutory data gaps identified for this filing.", icon=":material/check_circle:")

    st.markdown("##### :material/account_balance: Indebtedness & Working Capital Candidates")
    col_dw1, col_dw2 = st.columns(2)
    with col_dw1:
        st.markdown("**Indebtedness Schedule**")
        st.dataframe([
            {"Line Item": "Secured Rupee Term Loans", "Amount (₹ Cr)": f"₹{dossier.indebtedness.secured_term_loans_cr:,.2f} Cr"},
            {"Line Item": "Working Capital Demand Loans / CC", "Amount (₹ Cr)": f"₹{dossier.indebtedness.working_capital_loans_cr:,.2f} Cr"},
            {"Line Item": "Ind AS 116 Lease Liabilities", "Amount (₹ Cr)": f"₹{dossier.indebtedness.lease_liabilities_ind_as_116_cr:,.2f} Cr"},
            {"Line Item": "Cash & Liquid Balances", "Amount (₹ Cr)": f"₹{dossier.indebtedness.cash_and_equivalents_cr:,.2f} Cr"},
            {"Line Item": "Total Funded Bank Debt", "Amount (₹ Cr)": f"₹{dossier.indebtedness.funded_bank_debt_cr:,.2f} Cr"},
            {"Line Item": "Total Economic Indebtedness", "Amount (₹ Cr)": f"₹{dossier.indebtedness.total_economic_indebtedness_cr:,.2f} Cr"},
        ], use_container_width=True, hide_index=True)
    with col_dw2:
        st.markdown("**Working Capital & Governance**")
        st.dataframe([
            {"Metric": "Days Sales Outstanding (DSO)", "Value": f"{dossier.working_capital.debtor_days_dso:.1f} days"},
            {"Metric": "Days Inventory Outstanding (DIO)", "Value": f"{dossier.working_capital.inventory_days_dio:.1f} days"},
            {"Metric": "Days Payable Outstanding (DPO)", "Value": f"{dossier.working_capital.creditor_days_dpo:.1f} days"},
            {"Metric": "Cash Conversion Cycle (CCC)", "Value": f"{dossier.working_capital.cash_conversion_cycle_days:.1f} days"},
            {"Metric": "Promoter Shareholding Pledged", "Value": f"{dossier.governance.promoter_pledge_pct:.1f}%"},
            {"Metric": "Independent Board Representation", "Value": f"{dossier.governance.independent_directors_pct:.0f}%"},
        ], use_container_width=True, hide_index=True)

with tab_equity_thesis:
    render_html('<div class="bento-subtitle">Question-Led Institutional Underwriting · PRD Specification S01–S04</div>', unsafe_allow_html=True)
    render_html('<div class="bento-title">Ten Core Investor Questions & Decision Scorecard</div>', unsafe_allow_html=True)

    # Generate or retrieve Q01-Q10 findings adapted to current transaction context
    eq_findings = generate_equity_question_answers(dossier, persona=selected_persona, transaction_context=selected_context)

    # Summary Thesis Banner
    render_html(
        f"""
        <div class="bento-card" style="border: 1px solid rgba(16, 185, 129, 0.3); background: rgba(16, 185, 129, 0.05);">
            <div style="display:flex; justify-content:space-between; align-items:center;">
                <div>
                    <span class="badge-pill badge-emerald">Executive Investment Thesis</span>
                    <h3 style="color:#ffffff; margin:6px 0 2px 0;">{dossier.company_name} — Equity Underwriting Verdict</h3>
                </div>
                <span class="badge-pill badge-sky">{len(eq_findings)} Questions Evaluated ({'10 Core + 4 Private Extensions' if selected_context != 'PUBLIC_IPO' else '10 Core'})</span>
            </div>
            <div style="font-size:0.86rem; color:#e2e8f0; line-height:1.5; margin-top:8px;">
                Structured evaluation connects observable operating drivers to financial consequences and investor trade-offs. 
                All material claims are anchored to SEBI ICDR 2018 restated disclosures with distinct claim lineage.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    for qid, q_obj in eq_findings.items():
        is_px = qid.startswith("PX")
        stat = q_obj.status
        s_badge = "badge-emerald" if "ANSWERED" in stat else "badge-amber" if "PARTIAL" in stat else "badge-rose" if "BLOCKED" in stat else "badge-sky"
        exp_icon = ":material/quiz:" if not is_px else ":material/lock:"

        with st.expander(f"{qid}: {q_obj.title} — [{stat.replace('_', ' ')}]", icon=exp_icon, expanded=(qid in ("Q01", "Q04", "Q05"))):
            st.markdown(f"**Direct Bottom-Line Verdict:** {q_obj.direct_verdict}")
            st.markdown(f"**Detailed Analysis:** {q_obj.detailed_analysis}")

            # Evidence Claim Lineage
            if q_obj.claim_lineage:
                render_html("<div style='font-size:0.75rem; font-weight:700; color:#38bdf8; text-transform:uppercase; margin-top:10px;'><span class='material-symbols-rounded' style='font-size:14px; vertical-align:-2px; margin-right:4px;'>table_chart</span>Evidence Claim Lineage</div>", unsafe_allow_html=True)
                c_rows = []
                for cl in q_obj.claim_lineage:
                    c_rows.append({
                        "Claim Statement": cl.statement,
                        "Claim Classification": cl.claim_type,
                        "Verified Provenance": cl.verified_source,
                        "Confidence": cl.confidence,
                    })
                st.dataframe(pd.DataFrame(c_rows), use_container_width=True, hide_index=True)

            col_qa, col_qb = st.columns(2)
            with col_qa:
                if q_obj.alternative_explanations:
                    render_html("<div style='font-size:0.75rem; font-weight:700; color:#f59e0b; text-transform:uppercase; margin-top:8px;'><span class='material-symbols-rounded' style='font-size:14px; vertical-align:-2px; margin-right:4px;'>balance</span>Alternative Interpretations & Risks</div>", unsafe_allow_html=True)
                    for alt in q_obj.alternative_explanations:
                        st.markdown(f"• {alt}")
            with col_qb:
                if q_obj.limitations_and_uncertainties:
                    render_html("<div style='font-size:0.75rem; font-weight:700; color:#94a3b8; text-transform:uppercase; margin-top:8px;'><span class='material-symbols-rounded' style='font-size:14px; vertical-align:-2px; margin-right:4px;'>info</span>Disclosed Limitations & Data Gaps</div>", unsafe_allow_html=True)
                    for lim in q_obj.limitations_and_uncertainties:
                        st.markdown(f"• {lim}")

            # Conditional Recommendations
            if q_obj.conditional_recommendations:
                rec = q_obj.conditional_recommendations[0]
                rec_html = f"""
                <div class="action-card" style="margin-top:10px;">
                    <div style="font-size:0.75rem; font-weight:700; color:#10b981; text-transform:uppercase;">
                        <span class="material-symbols-rounded" style="font-size:14px; vertical-align:-2px; margin-right:4px;">verified_user</span>Actionable Protocol ({rec.action_owner})
                    </div>
                    <div style="font-size:0.85rem; color:#ffffff; margin:4px 0;">{rec.recommendation}</div>
                    <div style="font-size:0.78rem; color:#cbd5e1;">
                        • <strong>Preconditions:</strong> {rec.preconditions}<br>
                        • <strong>Completion Evidence:</strong> {rec.completion_evidence}<br>
                        • <strong>Monitoring Trigger:</strong> {rec.monitoring_trigger}
                    </div>
                </div>
                """
                render_html(rec_html)

            if q_obj.inflection_triggers:
                st.markdown(f"**:material/bolt: Thesis-Breaking Inflection Trigger:** `{q_obj.inflection_triggers[0]}`")

    # ── DECISION-DEPTH ADVANCED ALGORITHM LAB (ALG01 - ALG14) ──
    render_html('<hr style="border-color:rgba(255,255,255,0.08); margin:24px 0 16px 0;">', unsafe_allow_html=True)
    st.caption("The optional prototype lab contains illustrative assumptions and synthetic return examples. It does not establish empirical support or production acceptance of ALG01–ALG14. Use the Decision-depth workbench for explicit inputs, evidence states and saved decisions.")
    show_prototypes = st.checkbox("Show experimental algorithm diagnostics", value=False)
    with st.expander(":material/science: Experimental Algorithm Lab (ALG01–ALG14)", expanded=False):
        st.warning("Unvalidated research prototypes. Supplied defaults and synthetic examples must not be interpreted as issuer findings or investment recommendations.")
        if not show_prototypes:
            st.caption("Enable experimental diagnostics above to inspect the prototype outputs.")
        else:
            st.caption("Prototype results are conditional illustrations only.")
            from models.pre_ipo_algorithms import (
                alg02_falsifiable_thesis,
                alg03_sector_operating_drivers,
                alg04_dated_financing_feasibility,
                alg06_reverse_underwriting_valuation,
                alg07_reverse_stress_failure_frontier,
                alg12_investor_returns_attribution,
                alg13_private_security_waterfall,
            )
            c_alg1, c_alg2 = st.columns(2)
            with c_alg1:
                st.markdown("**ALG02: Falsifiable Proposition Engine**")
                f_res = alg02_falsifiable_thesis(dossier)
                for p in f_res.get("propositions", []):
                    p_badge = "badge-emerald" if p["status"] == "SUPPORTED" else "badge-amber" if p["status"] == "PARTIAL" else "badge-rose"
                    render_html(f"• **{p['claim']}** <span class='badge-pill {p_badge}'>{p['status']}</span><br><span style='font-size:0.75rem; color:#94a3b8;'>Mechanism: {p['economic_mechanism']}</span>", unsafe_allow_html=True)

                render_html("<br>**ALG03: Sector Driver Reconciled Tree**", unsafe_allow_html=True)
                d_res = alg03_sector_operating_drivers(dossier)
                st.json(d_res.get("driver_tree", {}))

            with c_alg2:
                st.markdown("**ALG07: Reverse Stress Failure Frontier (Minimal Shock Distance)**")
                ff_res = alg07_reverse_stress_failure_frontier(dossier)
                if ff_res.get("status") == "FRONTIER_FOUND":
                    render_html(f"• **Vulnerability Rating:** `{ff_res['vulnerability_assessment']}`<br>• Minimal Revenue Contraction: **{ff_res['minimal_revenue_shock_pct']:.0f}%**<br>• Minimal Rate Hike: **+{ff_res['minimal_rate_shock_bps']:.0f} bps**<br>• Quadratic Distance: `{ff_res['severity_distance']}`", unsafe_allow_html=True)
                else:
                    st.info("Issuer has negligible debt; failure frontier is exempt.")

                render_html("<br>**ALG12: Two-Factor Price Return Midpoint Decomposition**", unsafe_allow_html=True)
                attr_res = alg12_investor_returns_attribution(entry_price_inr=108.0, exit_price_inr=155.0, entry_eps_inr=1.20, exit_eps_inr=1.55)
                render_html(f"• Total Return: **+{attr_res['total_return_pct']:.1f}%** (₹{attr_res['total_price_delta_inr']:.1f})<br>• Earnings Growth Share: **{attr_res['earnings_growth_share_pct']:.1f}%**<br>• Multiple Expansion Share: **{attr_res['multiple_expansion_share_pct']:.1f}%**<br>• Conservation Error: `{attr_res['conservation_error_inr']} INR`", unsafe_allow_html=True)

# ═════════════════════════════════════════════════════════════════════════════
# LEVEL 1 - TAB 3: DETAILED ANALYTICAL WORKPAPERS (4 SUB-TABS)
# ═════════════════════════════════════════════════════════════════════════════
with tab_workpapers:
    render_html('<div class="bento-subtitle">Comprehensive Quantitative Workpaper Engine</div>', unsafe_allow_html=True)
    render_html('<div class="bento-title">Detailed Institutional Workpapers</div>', unsafe_allow_html=True)

    # 4 Sub-Tabs for complete visibility without horizontal overflow
    (
        subtab_fin,
        subtab_debt,
        subtab_stress,
        subtab_val,
    ) = st.tabs([
        ":material/waterfall_chart: Financials & Proceeds Waterfall",
        ":material/account_balance: Indebtedness & Debt Maturity",
        ":material/speed: Stress Testing & Headroom",
        ":material/query_stats: Valuation, Peers, DCF & Forensics",
    ])

    # ── SUBTAB 1: FINANCIALS & OBJECTS OF THE OFFER ──
    with subtab_fin:
        render_html('<div class="bento-subtitle">Section V Disclosures · Restated Consolidated Ind AS</div>', unsafe_allow_html=True)
        render_html('<div class="bento-title">3-to-4 Year Restated Performance</div>', unsafe_allow_html=True)
        fin_rows = []
        for f_item in dossier.history:
            fc = FinancialStatementsContract.from_financial_metric(f_item, dossier.indebtedness)
            fin_rows.append({
                "Fiscal Year": fc.fiscal_year,
                "Revenue (₹ Cr)": f"₹{fc.revenue_ops_cr:,.1f}",
                "Restated EBITDA (₹ Cr)": f"₹{fc.statutory_ebitda_cr:,.1f}",
                "EBITDA Margin (%)": f"{fc.ebitda_margin_pct:.1f}%",
                "PAT (₹ Cr)": f"₹{fc.pat_cr:,.1f}",
                "CFO (₹ Cr)": f"₹{fc.cfo_cr:,.1f}" if fc.cfo_cr is not None else "N/A",
                "Capex (₹ Cr)": f"₹{fc.capex_cr:,.1f}" if fc.capex_cr is not None else "N/A",
                "Free Cash Flow (₹ Cr)": f"₹{fc.fcf_cr:,.1f}" if fc.fcf_cr is not None else "N/A",
            })
        st.dataframe(pd.DataFrame(fin_rows), use_container_width=True, hide_index=True)

        col_f1, col_f2 = st.columns([3, 2])
        with col_f1:
            render_html('<div class="bento-subtitle" style="margin-top:14px;">Historical Trend Trajectory</div>', unsafe_allow_html=True)
            fig_trend = go.Figure()
            yrs = [f.fiscal_year for f in dossier.history]
            revs = [f.revenue_ops_cr for f in dossier.history]
            ebitdas = [FinancialStatementsContract.from_financial_metric(f, dossier.indebtedness).statutory_ebitda_cr for f in dossier.history]
            fig_trend.add_trace(go.Bar(x=yrs, y=revs, name="Revenue", marker_color="#38bdf8", opacity=0.75))
            fig_trend.add_trace(go.Scatter(x=yrs, y=ebitdas, name="Restated EBITDA", line=dict(color="#10b981", width=3), mode="lines+markers"))
            fig_trend.update_layout(
                height=220, margin=dict(l=20, r=20, t=20, b=20),
                paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                font=dict(color="#cbd5e1"),
            )
            st.plotly_chart(fig_trend, use_container_width=True)

        with col_f2:
            render_html('<div class="bento-subtitle" style="margin-top:14px;">Empirical Benchmark (N=8,677 CMIE Database)</div>', unsafe_allow_html=True)
            cfo_val_str = f"₹{latest_contract.cfo_cr:,.1f} Cr" if latest_contract.cfo_cr is not None else "N/A"
            cfi_val_str = f"₹{latest_contract.cfi_cr:,.1f} Cr" if latest_contract.cfi_cr is not None else "N/A"
            cff_val_str = f"₹{latest_contract.cff_cr:,.1f} Cr" if latest_contract.cff_cr is not None else "N/A"
            dickinson_html = f"""
            <div class="bento-card" style="margin-top:4px;">
                <div style="font-size:0.85rem; color:#94a3b8;">Classified Stage:</div>
                <div style="font-size:1.45rem; font-weight:800; color:#10b981; margin:2px 0;">{stage_name}</div>
                <div style="font-size:0.90rem; color:#cbd5e1; font-family:monospace;">Cash Flow Sign Triplet: {pattern}</div>
                <hr style="border-color:rgba(255,255,255,0.08); margin:10px 0;">
                <div style="font-size:0.82rem; line-height:1.45; color:#cbd5e1;">
                    • <strong>Operating Cash Flow:</strong> {cfo_val_str}<br>
                    • <strong>Investing Accrual:</strong> {cfi_val_str}<br>
                    • <strong>Financing Accrual:</strong> {cff_val_str}<br>
                    • <strong>Statutory EBITDA:</strong> ₹{latest_contract.statutory_ebitda_cr:,.1f} Cr<br>
                    • <strong>Attributable Net Worth:</strong> ₹{latest_contract.net_worth_cr:,.1f} Cr<br>
                    • <strong>Empirical Attribution:</strong> Dickinson (2011) cash-flow pattern; descriptive classification.
                </div>
            </div>
            """
            render_html(dickinson_html)

        fin_nar = generate_financials_narrative(dossier, persona=selected_persona)
        render_six_point_narrative(fin_nar, persona_title=persona_options[selected_persona])

        # Objects & Proceeds Waterfall
        render_html('<hr style="border-color:rgba(255,255,255,0.08); margin:24px 0 16px 0;">', unsafe_allow_html=True)
        obj = dossier.objects_of_offer
        render_html('<div class="bento-subtitle">SEBI ICDR 2018 Regulation 7 & 41 Compliance</div>', unsafe_allow_html=True)
        render_html('<div class="bento-title">Use of Proceeds Waterfall & Statutory Limits</div>', unsafe_allow_html=True)
        if obj:
            c_ob1, c_ob2 = st.columns(2)
            with c_ob1:
                obj_rows = [
                    {"Deployment Line Item": "Gross Fresh Issue Proceeds", "Allocated (₹ Cr)": f"₹{obj.gross_fresh_issue_cr:,.2f}", "% of Fresh": "100.0%"},
                    {"Deployment Line Item": "Estimated Issue Expenses", "Allocated (₹ Cr)": f"₹{obj.issue_expenses_cr:,.2f}", "% of Fresh": f"{(obj.issue_expenses_cr/max(1,obj.gross_fresh_issue_cr))*100:.1f}%"},
                    {"Deployment Line Item": "Net Fresh Proceeds Available", "Allocated (₹ Cr)": f"₹{obj.net_fresh_proceeds_cr:,.2f}", "% of Fresh": f"{(obj.net_fresh_proceeds_cr/max(1,obj.gross_fresh_issue_cr))*100:.1f}%"},
                    {"Deployment Line Item": "• Repayment / Prepayment of Debt", "Allocated (₹ Cr)": f"₹{obj.debt_prepayment_cr:,.2f}", "% of Fresh": f"{(obj.debt_prepayment_cr/max(1,obj.gross_fresh_issue_cr))*100:.1f}%"},
                    {"Deployment Line Item": "• Capital Expenditure (Capacity Expansion)", "Allocated (₹ Cr)": f"₹{obj.capex_expansion_cr:,.2f}", "% of Fresh": f"{(obj.capex_expansion_cr/max(1,obj.gross_fresh_issue_cr))*100:.1f}%"},
                    {"Deployment Line Item": "• General Corporate Purposes (GCP)", "Allocated (₹ Cr)": f"₹{obj.general_corporate_purposes_cr:,.2f}", "% of Fresh": f"{obj.gcp_pct_of_gross:.1f}%"},
                ]
                st.dataframe(pd.DataFrame(obj_rows), use_container_width=True, hide_index=True)
            with c_ob2:
                gcp_status = "COMPLIANT" if obj.sebi_gcp_compliant else "STATUTORY BREACH"
                gcp_badge = "badge-emerald" if obj.sebi_gcp_compliant else "badge-rose"
                gcp_html = f"""
                <div class="bento-card">
                    <div style="font-size:0.75rem; text-transform:uppercase; color:#94a3b8;">SEBI GCP Compliance (Reg 7(1))</div>
                    <div style="font-size:1.6rem; font-weight:800; color:{'#10b981' if obj.sebi_gcp_compliant else '#f43f5e'}; margin:4px 0;">
                        {obj.gcp_pct_of_gross:.1f}% of Gross <span class="badge-pill {gcp_badge}">{gcp_status}</span>
                    </div>
                    <div style="font-size:0.82rem; color:#cbd5e1; margin-top:8px;">
                        • Statutory Limit: GCP ≤ 25.0% of Gross Fresh Issue Proceeds.<br>
                        • Debt Prepayment Interest Savings: <strong style="color:#10b981;">₹{obj.annual_interest_savings_cr:,.1f} Cr/yr</strong> (@ {obj.interest_rate_on_retired_debt_pct}% WAIR).<br>
                        • Pro-Forma EPS Accretion: <strong style="color:#38bdf8;">{'+' if obj.pro_forma_eps_accretion_inr > 0 else ''}{obj.pro_forma_eps_accretion_inr:.2f} INR</strong> per share.
                    </div>
                </div>
                """
                render_html(gcp_html)
        else:
            st.info("Pure OFS transaction — 100% of proceeds accrue to selling shareholders.")

    # ── SUBTAB 2: INDEBTEDNESS & DEBT MATURITY ──
    with subtab_debt:
        # 3 Canonical Debt Cards (P0-05: Strict separation of funded bank debt and Ind AS 116 leases)
        c_d1, c_d2, c_d3 = st.columns(3)
        with c_d1:
            render_html(f"""
            <div class="bento-card" style="margin-bottom:12px;">
                <div style="font-size:0.75rem; text-transform:uppercase; color:#94a3b8;">Funded Bank Borrowings</div>
                <div style="font-size:1.6rem; font-weight:800; color:#38bdf8; margin:2px 0;">₹{latest_contract.funded_bank_debt_cr:,.1f} Cr</div>
                <div style="font-size:0.75rem; color:#64748b;">Term Loans + WC Facilities + NCDs + Unsecured</div>
            </div>
            """)
        with c_d2:
            render_html(f"""
            <div class="bento-card" style="margin-bottom:12px;">
                <div style="font-size:0.75rem; text-transform:uppercase; color:#94a3b8;">Ind AS 116 Lease Liabilities</div>
                <div style="font-size:1.6rem; font-weight:800; color:#f59e0b; margin:2px 0;">₹{latest_contract.lease_liabilities_cr:,.1f} Cr</div>
                <div style="font-size:0.75rem; color:#64748b;">Operating lease contractual payment obligations</div>
            </div>
            """)
        with c_d3:
            render_html(f"""
            <div class="bento-card" style="margin-bottom:12px;">
                <div style="font-size:0.75rem; text-transform:uppercase; color:#94a3b8;">Total Economic Indebtedness</div>
                <div style="font-size:1.6rem; font-weight:800; color:#10b981; margin:2px 0;">₹{latest_contract.total_economic_indebtedness_cr:,.1f} Cr</div>
                <div style="font-size:0.75rem; color:#64748b;">Funded bank debt + Capitalized lease obligations</div>
            </div>
            """)

        col_d1, col_d2 = st.columns([3, 2])
        ind = dossier.indebtedness
        with col_d1:
            render_html('<div class="bento-subtitle">Funded Bank Debt vs Ind AS 116 Leases</div>', unsafe_allow_html=True)
            render_html('<div class="bento-title">Economic Indebtedness Schedule</div>', unsafe_allow_html=True)
            debt_items = [
                {"Debt Category": "Secured Term Loans (Project Finance)", "Amount (₹ Cr)": f"₹{ind.secured_term_loans_cr:,.1f}", "Type": "Funded Debt"},
                {"Debt Category": "Working Capital Loans (Cash Credit/OD)", "Amount (₹ Cr)": f"₹{ind.working_capital_loans_cr:,.1f}", "Type": "Funded Debt"},
                {"Debt Category": "NCD Bonds & Capital Debt", "Amount (₹ Cr)": f"₹{ind.ncd_bonds_cr:,.1f}", "Type": "Funded Debt"},
                {"Debt Category": "Unsecured Loans", "Amount (₹ Cr)": f"₹{ind.unsecured_loans_cr:,.1f}", "Type": "Funded Debt"},
                {"Debt Category": "Total Funded Bank Debt", "Amount (₹ Cr)": f"₹{latest_contract.funded_bank_debt_cr:,.1f}", "Type": "Subtotal"},
                {"Debt Category": "Ind AS 116 Lease Liabilities", "Amount (₹ Cr)": f"₹{latest_contract.lease_liabilities_cr:,.1f}", "Type": "Economic Obligation"},
                {"Debt Category": "Total Economic Indebtedness", "Amount (₹ Cr)": f"₹{latest_contract.total_economic_indebtedness_cr:,.1f}", "Type": "Total"},
                {"Debt Category": "Less: Cash & Cash Equivalents", "Amount (₹ Cr)": f"₹{latest_contract.cash_and_equivalents_cr:,.1f}", "Type": "Liquid Treasury"},
                {"Debt Category": "Net Economic Indebtedness", "Amount (₹ Cr)": f"₹{latest_contract.net_economic_debt_cr:,.1f}", "Type": "Net Economic Debt"},
            ]
            st.dataframe(pd.DataFrame(debt_items), use_container_width=True, hide_index=True)

        with col_d2:
            render_html('<div class="bento-subtitle">Pricing & Benchmark Spread</div>', unsafe_allow_html=True)
            render_html('<div class="bento-title">Borrowing Cost Architecture</div>', unsafe_allow_html=True)
            wair_str = f"{ind.weighted_avg_interest_rate_pct:.2f}%" if ind.weighted_avg_interest_rate_pct else "Disclosed in Sanction Notes"
            spread_str = (
                ind.floating_benchmark_spread
                if ind.floating_benchmark_spread is not None
                else "Not established from reviewed filing evidence"
            )
            cost_html = f"""
            <div class="bento-card">
                <div style="font-size:0.75rem; text-transform:uppercase; color:#94a3b8;">Weighted Average Interest Rate (WAIR)</div>
                <div style="font-size:1.8rem; font-weight:800; color:#38bdf8; margin:4px 0;">{wair_str}</div>
                <div style="font-size:0.82rem; color:#cbd5e1; margin-top:8px;">
                    • <strong>Benchmark Spread:</strong> {spread_str}<br>
                    • <strong>Fixed vs Floating:</strong> {ind.fixed_rate_portion_pct:.0f}% Fixed / {ind.floating_rate_portion_pct:.0f}% Floating<br>
                    • <strong>Post-Deleveraging Net Debt:</strong> ₹{max(0.0, ind.net_economic_debt_cr - (dossier.objects_of_offer.debt_prepayment_cr if dossier.objects_of_offer else 0)):,.1f} Cr
                </div>
            </div>
            """
            render_html(cost_html)

        # Debt Maturity Ladder
        mat = dossier.debt_maturity
        if mat:
            render_html('<hr style="border-color:rgba(255,255,255,0.08); margin:20px 0 16px 0;">', unsafe_allow_html=True)
            render_html('<div class="bento-subtitle">Principal Repayment Schedule</div>', unsafe_allow_html=True)
            render_html('<div class="bento-title">Debt Maturity Ladder & Refinancing Profile</div>', unsafe_allow_html=True)
            c_m1, c_m2 = st.columns([3, 2])
            with c_m1:
                mat_df = pd.DataFrame([
                    {"Tenor Period": "Year 1 (Current Maturities)", "Principal Due (₹ Cr)": mat.repayment_due_year_1_cr},
                    {"Tenor Period": "Year 2", "Principal Due (₹ Cr)": mat.repayment_due_year_2_cr},
                    {"Tenor Period": "Year 3", "Principal Due (₹ Cr)": mat.repayment_due_year_3_cr},
                    {"Tenor Period": "Year 4", "Principal Due (₹ Cr)": mat.repayment_due_year_4_cr},
                    {"Tenor Period": "Year 5+", "Principal Due (₹ Cr)": mat.repayment_due_year_5_plus_cr},
                ])
                fig_mat = go.Figure(data=[go.Bar(x=mat_df["Tenor Period"], y=mat_df["Principal Due (₹ Cr)"], marker_color="#38bdf8")])
                fig_mat.update_layout(height=220, margin=dict(l=20, r=20, t=10, b=10), paper_bgcolor="rgba(0,0,0,0)", font=dict(color="#cbd5e1"))
                st.plotly_chart(fig_mat, use_container_width=True)
            with c_m2:
                r_badge = "badge-emerald" if mat.refinancing_risk_rating == "LOW" else "badge-amber"
                mat_html = f"""
                <div class="bento-card">
                    <div style="font-size:0.75rem; text-transform:uppercase; color:#94a3b8;">Weighted Average Tenor</div>
                    <div style="font-size:1.6rem; font-weight:800; color:#ffffff; margin:4px 0;">{mat.weighted_average_maturity_years:.1f} Years</div>
                    <div style="margin-top:6px;"><span class="badge-pill {r_badge}">Refinancing Risk: {mat.refinancing_risk_rating}</span></div>
                    <div style="font-size:0.80rem; color:#94a3b8; margin-top:10px;">
                        Total Repayment Profile: <strong style="color:#ffffff;">₹{mat.total_repayment_profile_cr:,.1f} Cr</strong>
                    </div>
                </div>
                """
                render_html(mat_html)

    # ── SUBTAB 3: STRESS TESTING & HEADROOM ──
    with subtab_stress:
        render_html('<div class="bento-subtitle">2D Dynamic Adversarial Stress Matrix</div>', unsafe_allow_html=True)
        render_html('<div class="bento-title">EBITDA Contraction vs Floating Rate Hike Sensitivity</div>', unsafe_allow_html=True)
        wair_val = dossier.indebtedness.weighted_avg_interest_rate_pct if dossier.indebtedness.weighted_avg_interest_rate_pct is not None else 9.0
        stress_res = generate_2d_sensitivity_matrix(
            base_ebitda_cr=latest_contract.statutory_ebitda_cr,
            gross_debt_cr=latest_contract.funded_bank_debt_cr,
            base_wair_pct=wair_val,
            floating_debt_portion_pct=dossier.indebtedness.floating_rate_portion_pct,
        )
        hikes = stress_res.get("rate_hikes_bps", [0, 50, 100, 150, 200])
        st_rows = []
        for r_dict in stress_res.get("matrix", []):
            eb_shock = r_dict.get("ebitda_shock_pct", 0)
            row_data = {"EBITDA Shock (%)": f"{eb_shock:+d}%"}
            for h in hikes:
                val_icr = r_dict.get(f"hike_{h}bps")
                row_data[f"+{h} bps Hike"] = f"{val_icr:.2f}x" if val_icr is not None else "N/A"
            st_rows.append(row_data)
        st.dataframe(pd.DataFrame(st_rows), use_container_width=True, hide_index=True)
        stress_nar = generate_stress_narrative(dossier, stress_res, persona=selected_persona)
        render_six_point_narrative(stress_nar, persona_title=persona_options[selected_persona])

        # ── Item 2: 3D Multi-Parameter Covenant Sensitivity Grid & Page 28 Bridge ──
        st.markdown("---")
        render_html("""
        <div class="bento-subtitle">3D Multi-Parameter Covenant Headroom Grid</div>
        <div class="bento-title">EBITDA Margin Shock × Benchmark Rate Hike × Fresh Issue Prepayment Tensor</div>
        """, unsafe_allow_html=True)

        c_3d1, c_3d2 = st.columns([1.5, 2.5])
        with c_3d1:
            sel_prepay_pct = st.select_slider(
                "Fresh Issue Allocated to Debt Prepayment (%):",
                options=[0, 25, 50, 75, 100],
                value=50,
                key=f"slider_prepay_{dossier.deal_id}",
                help="Models balance sheet repair by channeling primary IPO proceeds directly into retiring interest-bearing bank debt."
            )
        with c_3d2:
            fresh_cap = dossier.fresh_issue_cr if dossier.fresh_issue_cr is not None else 0.0
            retired_debt = fresh_cap * (sel_prepay_pct / 100.0)
            st.caption(f"💡 **Balance Sheet Sizing:** At **{sel_prepay_pct}%** allocation of **₹{fresh_cap:,.1f} Cr** fresh issue, **₹{retired_debt:,.1f} Cr** of funded debt is retired.")

        from models.pre_ipo_engine import compute_3d_covenant_sensitivity_matrix
        rev_cr = latest_contract.revenue_ops_cr if latest_contract.revenue_ops_cr else max(0.01, latest_contract.statutory_ebitda_cr)
        sens_3d = compute_3d_covenant_sensitivity_matrix(
            base_ebitda_cr=latest_contract.statutory_ebitda_cr,
            base_revenue_cr=rev_cr,
            base_gross_debt_cr=latest_contract.funded_bank_debt_cr,
            base_wair_pct=wair_val,
            fresh_issue_cr=fresh_cap,
            debt_prepay_allocations_pct=[sel_prepay_pct],
            covenant_threshold=3.0,
        )

        slice_data = sens_3d["slices"][0]
        remaining_debt = slice_data["remaining_debt_cr"]
        st.markdown(f"**Effective Post-Issue Funded Debt:** `₹{remaining_debt:,.1f} Cr` (Reduced from `₹{dossier.indebtedness.funded_bank_debt_cr:,.1f} Cr`)")

        rate_cols = sens_3d["rate_shocks_bps"]
        grid_rows = []
        for r_entry in slice_data["matrix"]:
            m_bps = r_entry["margin_shock_bps"]
            m_pct = r_entry["shocked_margin_pct"]
            row_dict = {"Margin Shock (bps)": f"{m_bps:+d} bps ({m_pct:.1f}%)"}
            for r_res in r_entry["rate_results"]:
                r_bps = r_res["rate_shock_bps"]
                icr_val = r_res["icr"]
                status = r_res["status"]
                import math
                if math.isinf(icr_val):
                    display_val = "∞ (Exempt)"
                elif status == "NEGATIVE_EBITDA":
                    display_val = "0.00x (Loss)"
                else:
                    display_val = f"{icr_val:.2f}x"
                row_dict[f"+{r_bps} bps Rate"] = display_val
            grid_rows.append(row_dict)

        st.dataframe(pd.DataFrame(grid_rows), use_container_width=True, hide_index=True)

        br_col1, br_col2 = st.columns([2, 1])
        with br_col1:
            st.caption("🛡️ **Bank Covenant Benchmark: 3.00x ICR**. Headroom reflects distance above minimum loan covenants.")
        with br_col2:
            if st.button("🚀 Bridge to Page 28: 12-Qtr CFADS Engine", key=f"btn_bridge_p28_{dossier.deal_id}", use_container_width=True):
                st.session_state["covenant_bridge_scenario"] = {
                    "company_name": dossier.company_name,
                    "base_ebitda": latest_contract.statutory_ebitda_cr,
                    "funded_debt": remaining_debt,
                    "wair_pct": wair_val,
                    "prepay_pct": sel_prepay_pct,
                }
                st.success("Scenario parameters primed for Page 28. Switch to '28 Covenant Headroom' in sidebar.")

    # ── SUBTAB 4: VALUATION, PEERS, DCF & FORENSICS ──
    with subtab_val:
        val = dossier.valuation_comps
        if not dossier.is_price_disclosed or (val and val.price_band_upper_inr <= 0):
            render_html("""
            <div class="bento-card" style="border-left:4px solid #38bdf8; margin-bottom:16px;">
                <div style="font-size:0.75rem; text-transform:uppercase; color:#38bdf8; font-weight:700;">
                    <span class="material-symbols-rounded" style="font-size:14px; vertical-align:-2px; margin-right:4px;">info</span>STATUTORY PRICING NOTICE · SEBI ICDR 2018 (BOOK BUILDING PROCESS)
                </div>
                <div style="font-size:0.86rem; color:#e2e8f0; line-height:1.6; margin-top:6px;">
                    This filing is a <strong>Draft Red Herring Prospectus (DRHP)</strong>. Under statutory SEBI regulations, the 
                    <strong>Offer Price, Price Band, and aggregate Offer Value are explicitly left blank [●]</strong> and will be determined through 
                    the book-building bidding process at the Red Herring Prospectus (RHP) stage.<br>
                    Use the <strong>Interactive Scenario Valuation Sandbox</strong> below to simulate enterprise multiples, dilution, and DCF hurdles.
                </div>
            </div>
            """, unsafe_allow_html=True)

            st.markdown("##### :material/tune: Interactive Scenario Valuation Sandbox")
            c_sc1, c_sc2 = st.columns([1.5, 2.5])
            with c_sc1:
                scenario_price = st.slider(
                    "Hypothetical Issue Price (₹ / share)",
                    min_value=100.0,
                    max_value=1000.0,
                    value=390.0,
                    step=5.0,
                    key=f"scenario_slider_{dossier.deal_id}"
                )
            with c_sc2:
                # Derive shares count safely from dossier without hardcoded constants
                shares_pre_cr = getattr(dossier.objects_of_offer, 'shares_pre_issue_cr', None) if dossier.objects_of_offer else None
                if not shares_pre_cr and getattr(dossier, 'cap_table', None) and getattr(dossier.cap_table, 'pre_offer_equity_shares_cr', None):
                    shares_pre_cr = dossier.cap_table.pre_offer_equity_shares_cr
                if not shares_pre_cr and dossier.offered_shares_count:
                    shares_pre_cr = dossier.offered_shares_count / 1e7

                latest_pat = latest_contract.pat_cr if latest_contract.pat_cr is not None else None
                latest_ebitda = latest_contract.statutory_ebitda_cr if latest_contract.statutory_ebitda_cr is not None else None

                sc_debt = latest_contract.total_economic_indebtedness_cr
                sc_cash = latest_contract.cash_and_equivalents_cr

                if shares_pre_cr and shares_pre_cr > 0:
                    sc_mcap = shares_pre_cr * scenario_price
                    sc_ev = sc_mcap + sc_debt - sc_cash
                    sc_mcap_str = f"₹{sc_mcap:,.1f} Cr"
                    sc_ev_str = f"₹{sc_ev:,.1f} Cr"
                    sc_pe_str = f"{sc_mcap / latest_pat:.1f}x" if (latest_pat and latest_pat > 0) else "N/A"
                    sc_ev_ebitda_str = f"{sc_ev / latest_ebitda:.1f}x" if (latest_ebitda and latest_ebitda > 0) else "N/A"
                else:
                    sc_mcap_str = "Undisclosed"
                    sc_ev_str = "Undisclosed"
                    sc_pe_str = "N/A"
                    sc_ev_ebitda_str = "N/A"

                render_html(f"""
                <div style="display:flex; gap:16px; flex-wrap:wrap; background:rgba(30,41,59,0.7); border-radius:8px; padding:12px; border:1px solid rgba(56,189,248,0.2);">
                    <div><span style="font-size:0.75rem; color:#94a3b8;">SCENARIO MCAP:</span><br><strong style="font-size:1.1rem; color:#38bdf8;">{sc_mcap_str}</strong></div>
                    <div><span style="font-size:0.75rem; color:#94a3b8;">SCENARIO EV:</span><br><strong style="font-size:1.1rem; color:#38bdf8;">{sc_ev_str}</strong></div>
                    <div><span style="font-size:0.75rem; color:#94a3b8;">SCENARIO P/E:</span><br><strong style="font-size:1.1rem; color:#f8fafc;">{sc_pe_str}</strong></div>
                    <div><span style="font-size:0.75rem; color:#94a3b8;">SCENARIO EV/EBITDA:</span><br><strong style="font-size:1.1rem; color:#f8fafc;">{sc_ev_ebitda_str}</strong></div>
                    <div><span class="badge-pill badge-amber" style="font-size:0.75rem;">USER SCENARIO ASSUMPTION</span></div>
                </div>
                """, unsafe_allow_html=True)
        elif val:
            v_badge = "badge-emerald" if "DISCOUNT" in val.valuation_verdict else "badge-sky"
            val_box_html = f"""
            <div class="bento-card" style="margin-bottom:16px;">
                <div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:12px;">
                    <div>
                        <div style="font-size:0.75rem; text-transform:uppercase; color:#94a3b8; font-weight:700;">Offer Valuation Summary & Multiples Overview</div>
                        <div style="font-size:1.85rem; font-weight:800; color:#38bdf8; margin:2px 0;">₹{val.implied_ev_cr:,.1f} Cr <span style="font-size:0.9rem; font-weight:500; color:#94a3b8;">Implied Enterprise Value (Upper Band)</span></div>
                    </div>
                    <div>
                        <span class="badge-pill {v_badge}" style="font-size:0.82rem; padding:6px 14px;">Verdict: {val.valuation_verdict}</span>
                    </div>
                </div>
                <div style="display:grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap:12px; margin-top:12px; border-top:1px solid rgba(255,255,255,0.08); padding-top:10px; font-size:0.84rem;">
                    <div><span style="color:#94a3b8;">Implied P/E:</span> <strong style="color:#ffffff;">{val.implied_pe_ratio:.1f}x</strong> <span style="color:#64748b;">(Peer Median: {val.peer_median_pe or 'N/A'}x)</span></div>
                    <div><span style="color:#94a3b8;">Implied EV/EBITDA:</span> <strong style="color:#ffffff;">{val.implied_ev_ebitda:.1f}x</strong></div>
                    <div><span style="color:#94a3b8;">Price Band:</span> <strong style="color:#10b981;">₹{val.price_band_lower_inr:.0f} - ₹{val.price_band_upper_inr:.0f}</strong></div>
                    <div><span style="color:#94a3b8;">Peer Comps Sizing:</span> <strong style="color:#f8fafc;">{len(val.peers) if val.peers else 0} Listed Competitors</strong></div>
                </div>
            </div>
            """
            render_html(val_box_html)

        render_html('<div class="bento-subtitle">CMIE Listed Peers at Identical Life-Cycle Stage</div>', unsafe_allow_html=True)
        render_html('<div class="bento-title">Valuation Peer Benchmarking</div>', unsafe_allow_html=True)
        if val and val.peers:
            p_comps = []
            for p in val.peers:
                p_comps.append({
                    "Peer Name": p.peer_name,
                    "Ticker": p.ticker,
                    "Market Cap (₹ Cr)": f"₹{p.mcap_cr:,.1f}",
                    "P/E Ratio": f"{p.pe_ratio:.1f}x" if p.pe_ratio else "Loss",
                    "EV/EBITDA": f"{p.ev_ebitda:.1f}x" if p.ev_ebitda else "Loss",
                    "ROE (%)": f"{p.roe_pct:.1f}%",
                    "Life Stage": p.dickinson_stage,
                })
            st.dataframe(pd.DataFrame(p_comps), use_container_width=True, hide_index=True)
        else:
            st.info("Peer comparison table configured in DRHP Section III.")

        # WACC, ROIC & Reverse DCF Hurdle
        render_html('<hr style="border-color:rgba(255,255,255,0.08); margin:20px 0 16px 0;">', unsafe_allow_html=True)
        render_html('<div class="bento-subtitle">Economic Value Creation & Reverse DCF Sizing</div>', unsafe_allow_html=True)
        render_html('<div class="bento-title">ROIC vs WACC Spread & Required Growth Hurdle</div>', unsafe_allow_html=True)
        wacc_res = calculate_wacc_and_roic(
            dossier,
            is_blocked=bool(is_hcch and not gate_decision.allowed),
            blocked_reason="Unreviewed under P0-07 containment" if (is_hcch and not gate_decision.allowed) else "",
        )
        rev_dcf = calculate_reverse_dcf_hurdle(
            dossier,
            is_blocked=bool(is_hcch and not gate_decision.allowed),
            blocked_reason="Unpriced / unreviewed under P0-07 containment" if (is_hcch and not gate_decision.allowed) else "",
        )

        col_w1, col_w2, col_w3 = st.columns(3)
        with col_w1:
            roic_val = wacc_res.get('roic_pct') if wacc_res else None
            spread_val = wacc_res.get('value_creation_spread_pct') if wacc_res else None
            roic_str = f"{roic_val:.1f}%" if roic_val is not None else "N/A"
            delta_str = f"{spread_val:+.1f}% vs WACC" if spread_val is not None else None
            st.metric("Return on Invested Capital (ROIC)", roic_str, delta=delta_str)
        with col_w2:
            wacc_val = wacc_res.get('wacc_pct') if wacc_res else None
            wacc_str = f"{wacc_val:.1f}%" if wacc_val is not None else "N/A"
            st.metric("Weighted Average Cost of Capital (WACC)", wacc_str, help="CAPM Ke + Post-tax Kd")
        with col_w3:
            eva_val = wacc_res.get('economic_profit_cr') if wacc_res else None
            eva_str = f"₹{eva_val:,.1f} Cr" if eva_val is not None else "N/A"
            eva_status = (wacc_res.get('status') or 'UNCOMPUTED').replace('_', ' ') if wacc_res else "UNCOMPUTED"
            st.metric("Annual Economic Profit (EVA)", eva_str, delta=eva_status)

        dcf_narrative = rev_dcf.get('narrative', 'Reverse DCF hurdle calculation requires audited financial statements.') if rev_dcf else "Awaiting disclosures."
        st.info(f"**Reverse DCF Analysis:** {dcf_narrative}", icon=":material/info:")

        # Beneish Forensics & Anchor Lock-In Calendar
        render_html('<hr style="border-color:rgba(255,255,255,0.08); margin:20px 0 16px 0;">', unsafe_allow_html=True)
        render_html('<div class="bento-subtitle">Forensic Accruals & Statutory Lock-In Calendar</div>', unsafe_allow_html=True)
        render_html('<div class="bento-title">Beneish M-Score & Anchor Secondary Float Schedule</div>', unsafe_allow_html=True)

        beneish = dossier.beneish_forensics
        if beneish and beneish.m_score is not None:
            b_color = "#10b981" if not beneish.is_manipulation_risk else "#f43f5e"
            b_status = "SAFE (Low Accrual Manipulation Risk)" if not beneish.is_manipulation_risk else "ELEVATED EARNINGS QUALITY CONCERN"
            render_html(
                f"""
                <div class="bento-card" style="border-left:4px solid {b_color}; margin-bottom:16px;">
                    <div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:8px;">
                        <div>
                            <div style="font-size:0.75rem; text-transform:uppercase; color:#94a3b8; font-weight:700;">Beneish (1999) 8-Variable M-Score Model</div>
                            <div style="font-size:1.85rem; font-weight:800; color:{b_color}; margin:2px 0;">{beneish.m_score:.2f} <span style="font-size:0.88rem; font-weight:600; color:{b_color}; margin-left:8px;">[{b_status}]</span></div>
                        </div>
                        <div style="font-size:0.80rem; color:#94a3b8; max-width:420px; text-align:right;">
                            Threshold: M-Score &gt; -1.78 indicates high statistical probability of earnings management.
                        </div>
                    </div>
                    <div style="display:grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap:10px; margin-top:10px; border-top:1px solid rgba(255,255,255,0.08); padding-top:10px; font-size:0.82rem; color:#cbd5e1;">
                        <div>• DSRI (Days Sales in Receivables): <strong style="color:#ffffff;">{beneish.dsri if beneish.dsri is not None else 1.0:.2f}</strong></div>
                        <div>• GMI (Gross Margin Index): <strong style="color:#ffffff;">{beneish.gmi if beneish.gmi is not None else 1.0:.2f}</strong></div>
                        <div>• AQI (Asset Quality Index): <strong style="color:#ffffff;">{beneish.aqi if beneish.aqi is not None else 1.0:.2f}</strong></div>
                        <div>• SGI (Sales Growth Index): <strong style="color:#ffffff;">{beneish.sgi if beneish.sgi is not None else 1.0:.2f}</strong></div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        else:
            st.info("Forensic M-Score requires minimum 2 full years of restated balance sheet disclosures.")

        # Full-width Statutory Lock-In Schedule
        render_html('<div class="bento-subtitle">Statutory Anchor & Promoter Lock-in Expiry Calendar</div>', unsafe_allow_html=True)
        from datetime import datetime, timezone
        from models.pre_ipo_exchange_feed import ExchangeFeedClient
        recon = ExchangeFeedClient.reconcile_with_prospectus(dossier.listing_date, dossier.company_name)
        if recon.get("is_reconciled"):
            render_html(
                f"""
                <div style="background:rgba(16,185,129,0.1); border:1px solid rgba(16,185,129,0.3); border-radius:6px; padding:6px 10px; margin-bottom:8px; font-size:0.78rem; color:#10b981;">
                    <span class="material-symbols-rounded" style="font-size:14px; color:#10b981; vertical-align:-2px; margin-right:2px;">check_circle</span> <strong>{recon['exchange']} Circular {recon['circular_ref']}</strong> · Listing: <strong>{recon['exchange_listing_date']}</strong> ({recon['drift_status']})
                </div>
                """,
                unsafe_allow_html=True,
            )
        if not recon.get("is_reconciled"):
            st.info(recon["notes"])
        as_of_today = datetime.now(timezone.utc).date()
        lockin_sched = generate_anchor_lockin_calendar(dossier, as_of_date=as_of_today)
        if lockin_sched:
            l_rows = []
            for l in lockin_sched:
                l_rows.append({
                    "Unlock Milestone": l.milestone_name,
                    "Target Date": l.calendar_date,
                    "Unlocked (₹ Cr)": f"₹{l.unlocked_value_cr:,.1f}",
                    "Free Float (%)": f"{l.cumulative_free_float_pct:.1f}%",
                    "Risk Level": l.supply_risk_level,
                    "Status": l.status,
                    "Exchange Circular": l.exchange_notice_ref,
                })
            st.dataframe(pd.DataFrame(l_rows), use_container_width=True, hide_index=True)

# ═════════════════════════════════════════════════════════════════════════════
# LEVEL 1 - TAB 4: CMIE REFERENCE CROSSWALK & DATA COVERAGE
# ═════════════════════════════════════════════════════════════════════════════
with tab_crosswalk:
    render_html('<div class="bento-subtitle">Audited Reconciliation against Licensed CMIE Prowess Schema</div>', unsafe_allow_html=True)
    render_html('<div class="bento-title">Extracted DRHP Data vs. CMIE Reference Field Crosswalk</div>', unsafe_allow_html=True)

    cross_res = generate_cmie_crosswalk_coverage(dossier)

    # Coverage KPI Cards
    c_cw1, c_cw2, c_cw3, c_cw4, c_cw5 = st.columns(5)
    with c_cw1:
        st.metric("Total Concepts Tracked", cross_res["total_concepts_tracked"])
    with c_cw2:
        st.metric("Exact Matches", cross_res["exact_match_count"], delta="SEBI Restated")
    with c_cw3:
        st.metric("Reconciled Norms", cross_res["reconciled_count"], delta="Accounting Bridge")
    with c_cw4:
        st.metric("Undisclosed in DRHP", cross_res["undisclosed_count"], delta="Diligence Gaps" if cross_res["undisclosed_count"] > 0 else "None", delta_color="inverse")
    with c_cw5:
        st.metric("Audit Coverage", f"{cross_res['coverage_pct']}%", delta=cross_res["data_quality_verdict"].replace("_", " "))

    render_html(
        """
        <div style="font-size:0.80rem; color:#94a3b8; margin:8px 0 14px 0;">
            *Reconciliation Methodology: Standardizes DRHP restated financial metrics against canonical CMIE field definitions. 
            Lease adjustments under Ind AS 116, capitalized R&D, and non-operating treasury items are explicitly reconciled.
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Interactive Table with Status Filter
    records = dossier.cmie_crosswalk
    if records:
        status_filter = st.selectbox("Filter Crosswalk by Status", options=["ALL", "EXACT_MATCH", "RECONCILED", "UNDISCLOSED_IN_DRHP"], index=0)
        filtered_records = [r for r in records if status_filter == "ALL" or r.status == status_filter]

        cw_rows = []
        for r in filtered_records:
            cw_rows.append({
                "Canonical Concept": r.canonical_concept,
                "CMIE Field Code": r.cmie_field_code,
                "CMIE Standardization Definition": r.cmie_definition,
                "DRHP Restated Figure": r.drhp_raw_value,
                "CMIE Normalized Figure": r.cmie_normalized_value,
                "Reconciliation Status": r.status,
                "Audit Reconciliation Note": r.reconciliation_note,
            })
        st.dataframe(pd.DataFrame(cw_rows), use_container_width=True, hide_index=True)

        cw_df = pd.DataFrame(cw_rows)
        st.download_button(
            label="Download CMIE Crosswalk (CSV)",
            icon=":material/download:",
            data=cw_df.to_csv(index=False).encode("utf-8"),
            file_name=f"{dossier.deal_id}_cmie_crosswalk.csv",
            mime="text/csv",
        )
    else:
        st.info("No crosswalk records configured for this custom dossier.")

# ═════════════════════════════════════════════════════════════════════════════
# LEVEL 1 - TAB 5: IC STANCE, ACTION REGISTER & LIMITATIONS
# ═════════════════════════════════════════════════════════════════════════════
with tab_ic_action:
    render_html('<div class="bento-subtitle">Institutional Governance & Decision Protocol</div>', unsafe_allow_html=True)
    render_html('<div class="bento-title">Investment Committee Underwriting Stance & Action Register</div>', unsafe_allow_html=True)

    # P0-08 Containment: Evaluate recommendation capability gate
    gate_ic = evaluate_capability_gate(
        owner=active_owner,
        company=getattr(dossier, "company_name", selected_deal_key),
        capability=CapabilityType.RECOMMENDATIONS,
        snapshot_id=active_snapshot_id,
        snapshot_status=active_snapshot_status,
        origin=dossier_origin,
        is_production=True,
    )

    if not gate_ic.allowed:
        render_html(f"""
        <div class="bento-card" style="border:1px solid #ef4444; background:rgba(239, 68, 68, 0.08); padding:16px; border-radius:8px; margin-bottom:16px;">
            <div style="font-size:0.85rem; font-weight:700; color:#f87171; text-transform:uppercase; margin-bottom:6px;">
                <span class="material-symbols-rounded" style="font-size:16px; vertical-align:-3px; margin-right:4px;">gavel</span>
                P0-08 Containment Active: Automated IC Verdict & Agency Ratings Prohibited
            </div>
            <div style="font-size:0.86rem; color:#cbd5e1; line-height:1.5;">
                {gate_ic.reason}
                <br><em>Policy Directive:</em> {gate_ic.next_action}
            </div>
        </div>
        """, unsafe_allow_html=True)

        col_ic1, col_ic2 = st.columns([2, 3])
        with col_ic1:
            neutral_box_html = f"""
            <div class="bento-card" style="border:2px solid #3b82f6; text-align:center;">
                <div style="font-size:0.75rem; color:#94a3b8; text-transform:uppercase;">Institutional Governance Protocol</div>
                <div style="font-size:1.3rem; font-weight:800; color:#60a5fa; margin:8px 0; line-height:1.2;">
                    DECISION-SUPPORT ONLY
                </div>
                <div style="font-size:0.85rem; color:#cbd5e1; margin-top:8px;">
                    Underwriting Verdict: <strong style="color:#ffffff;">MANUAL_IC_DELIBERATION_REQUIRED</strong><br>
                    External Rating: <strong style="color:#ffffff;">NO_AUTOMATED_SYNTHESIS (SEBI CRA 1999)</strong>
                </div>
                <div style="font-size:0.70rem; color:#94a3b8; margin-top:6px;">
                    *Statutory Mandate: No automated committee approval or synthetic credit agency rating is provided.
                </div>
            </div>
            """
            render_html(neutral_box_html)
        with col_ic2:
            ic = dossier.ic_verdict if dossier else None
            strengths = (
                getattr(ic, "key_credit_strengths", None) or
                getattr(ic, "strengths", None) or
                [
                    "Track record of cash operating profitability across evaluated fiscal periods.",
                    "Established market footprint in domestic consumer categories.",
                    "Parentage and brand support from established institutional sponsors."
                ]
            )
            risks = (
                getattr(ic, "key_downside_risks", None) or
                getattr(ic, "key_underwriting_risks", None) or
                getattr(ic, "key_credit_risks", None) or
                [
                    "Execution risks on planned capital expenditure expansion.",
                    "Working capital fluctuations and raw material commodity pricing exposure.",
                    "Competitive dynamics from both organized and unorganized sector participants."
                ]
            )
            neutral_str_html = f"""
            <div class="bento-card">
                <div style="font-size:0.80rem; font-weight:700; color:#10b981; text-transform:uppercase; margin-bottom:6px;">
                    <span class="material-symbols-rounded" style="font-size:14px; vertical-align:-2px; margin-right:4px;">verified</span>Diligence Observations & Transaction Strengths
                </div>
                <div style="font-size:0.84rem; color:#e2e8f0; line-height:1.45;">
                    {'<br>'.join(['• ' + s for s in strengths])}
                </div>
                <hr style="border-color:rgba(255,255,255,0.08); margin:10px 0;">
                <div style="font-size:0.80rem; font-weight:700; color:#f43f5e; text-transform:uppercase; margin-bottom:6px;">
                    <span class="material-symbols-rounded" style="font-size:14px; vertical-align:-2px; margin-right:4px;">warning</span>Key Diligence Vulnerabilities & Downside Considerations
                </div>
                <div style="font-size:0.84rem; color:#cbd5e1; line-height:1.45;">
                    {'<br>'.join(['• ' + r for r in risks])}
                </div>
            </div>
            """
            render_html(neutral_str_html)
    else:
        ic = dossier.ic_verdict
        if ic:
            col_ic1, col_ic2 = st.columns([2, 3])
            with col_ic1:
                v_color = "#10b981" if "APPROVE" in ic.underwriting_verdict else "#f59e0b"
                rating_display = (
                    f"External Rating: <strong style='color:#ffffff;'>{ic.external_rating_symbol} ({ic.external_rating_agency})</strong>"
                    if (ic.external_rating_symbol and ic.external_rating_agency)
                    else f"Internal Screening Grade: <strong style='color:#ffffff;'>{ic.internal_screening_grade or 'UNRATED'}</strong>"
                )
                ic_box_html = f"""
                <div class="bento-card" style="border:2px solid {v_color}; text-align:center;">
                    <div style="font-size:0.75rem; color:#94a3b8; text-transform:uppercase;">IC Underwriting Verdict</div>
                    <div style="font-size:1.5rem; font-weight:800; color:{v_color}; margin:8px 0; line-height:1.2;">
                        {ic.underwriting_verdict}
                    </div>
                    <div style="font-size:0.85rem; color:#cbd5e1; margin-top:8px;">
                        {rating_display}<br>
                        Max Rec. Leverage Ceiling: <strong style="color:#ffffff;">{ic.max_recommended_leverage_ratio:.2f}x EBITDA</strong>
                    </div>
                    <div style="font-size:0.70rem; color:#94a3b8; margin-top:6px;">
                        *Statutory Notice: Internal screening grade is derived from financial metrics, not a Credit Rating Agency opinion under SEBI CRA Regulations 1999.
                    </div>
                </div>
                """
                render_html(ic_box_html)
            with col_ic2:
                ic_str_html = f"""
            <div class="bento-card">
                <div style="font-size:0.80rem; font-weight:700; color:#10b981; text-transform:uppercase; margin-bottom:6px;">
                    <span class="material-symbols-rounded" style="font-size:14px; vertical-align:-2px; margin-right:4px;">verified</span>Key Transaction & Credit Strengths
                </div>
                <div style="font-size:0.84rem; color:#e2e8f0; line-height:1.45;">
                    {'<br>'.join(['• ' + s for s in ic.key_credit_strengths])}
                </div>
                <hr style="border-color:rgba(255,255,255,0.08); margin:10px 0;">
                <div style="font-size:0.80rem; font-weight:700; color:#f43f5e; text-transform:uppercase; margin-bottom:6px;">
                    <span class="material-symbols-rounded" style="font-size:14px; vertical-align:-2px; margin-right:4px;">warning</span>Key Underwriting Vulnerabilities & Downside Risks
                </div>
                <div style="font-size:0.84rem; color:#e2e8f0; line-height:1.45;">
                    {'<br>'.join(['• ' + r for r in ic.key_downside_risks])}
                </div>
            </div>
            """
            render_html(ic_str_html)

        cov_html = f"""
        <div class="bento-card" style="border-left:4px solid #38bdf8;">
            <div style="font-size:0.80rem; font-weight:700; color:#38bdf8; text-transform:uppercase; margin-bottom:6px;">
                <span class="material-symbols-rounded" style="font-size:14px; vertical-align:-2px; margin-right:4px;">shield</span>Mandatory Loan Covenants & Credit Safeguards
            </div>
            <div style="font-size:0.86rem; color:#e2e8f0; line-height:1.5;">
                {'<br>'.join(['• ' + c for c in ic.mandatory_loan_covenants])}
            </div>
            <hr style="border-color:rgba(255,255,255,0.08); margin:10px 0;">
            <div style="font-size:0.80rem; font-weight:700; color:#10b981; text-transform:uppercase; margin-bottom:4px;">
                <span class="material-symbols-rounded" style="font-size:14px; vertical-align:-2px; margin-right:4px;">policy</span>Executive Treasury & Underwriter Mandate
            </div>
            <div style="font-size:0.86rem; color:#f8fafc; line-height:1.5;">
                {ic.treasury_call_to_action}
            </div>
        </div>
        """
        render_html(cov_html)

    # Prioritized Action Register Table
    render_html('<hr style="border-color:rgba(255,255,255,0.08); margin:20px 0 16px 0;">', unsafe_allow_html=True)
    render_html('<div class="bento-subtitle">Prioritized Diligence & Execution Worklist</div>', unsafe_allow_html=True)
    render_html('<div class="bento-title">Underwriting Action Register</div>', unsafe_allow_html=True)

    action_rows = []
    # Collect all actions from equity questions
    eq_findings = generate_equity_question_answers(dossier, persona=selected_persona, transaction_context=selected_context)
    for qid, qf in eq_findings.items():
        for act in qf.conditional_recommendations:
            action_rows.append({
                "Source Dimension": f"{qid}: {qf.title}",
                "Action Owner": act.action_owner,
                "Recommended Action": act.recommendation,
                "Precondition Required": act.preconditions,
                "Completion Evidence": act.completion_evidence,
                "Monitoring Tripwire": act.monitoring_trigger,
            })
    if action_rows:
        col_reg_pill, col_reg_dl = st.columns([3.2, 1.0])
        owners = ["All Owners"] + sorted(list({r["Action Owner"] for r in action_rows}))
        with col_reg_pill:
            selected_owner = st.pills(
                "Filter by Committee Member / Owner",
                options=owners,
                default="All Owners",
                key="action_reg_owner_pill",
            )
        with col_reg_dl:
            render_html("<div style='height: 28px;'></div>", unsafe_allow_html=True)
            st.download_button(
                label="Export Actions (CSV)",
                icon=":material/download:",
                data=pd.DataFrame(action_rows).to_csv(index=False),
                file_name=f"{dossier.deal_id}_underwriting_action_register.csv",
                mime="text/csv",
                use_container_width=True,
                key="dl_action_reg_csv",
            )

        filtered_rows = action_rows if selected_owner == "All Owners" else [r for r in action_rows if r["Action Owner"] == selected_owner]
        st.caption(f"Displaying **{len(filtered_rows)}** prioritized underwriting mandates ({selected_owner}):")

        for r in filtered_rows:
            card_html = f"""
            <div style="background:rgba(15,23,42,0.75); border:1px solid rgba(255,255,255,0.10); border-top:1px solid rgba(255,255,255,0.18); border-radius:10px; padding:16px 18px; margin-bottom:14px; box-shadow:0 3px 10px -2px rgba(0,0,0,0.5);">
                <div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:8px; margin-bottom:10px; border-bottom:1px solid rgba(255,255,255,0.06); padding-bottom:8px;">
                    <div style="font-size:0.92rem; font-weight:700; color:#38bdf8; display:flex; align-items:center; gap:6px;">
                        <span class="material-symbols-rounded" style="font-size:16px; color:#38bdf8;">task_alt</span>
                        {r['Source Dimension']}
                    </div>
                    <div style="display:flex; gap:8px; align-items:center;">
                        <span style="display:inline-block; padding:3px 10px; border-radius:6px; background:rgba(56,189,248,0.12); color:#38bdf8; border:1px solid rgba(56,189,248,0.3); font-size:0.75rem; font-weight:600;">
                            {r['Action Owner']}
                        </span>
                        <span style="display:inline-block; padding:3px 8px; border-radius:6px; background:rgba(16,185,129,0.12); color:#10b981; border:1px solid rgba(16,185,129,0.3); font-size:0.72rem; font-weight:700;">
                            MANDATE
                        </span>
                    </div>
                </div>
                <div style="font-size:0.88rem; color:#f8fafc; line-height:1.55; margin-bottom:14px;">
                    <strong style="color:#e2e8f0;">Action Mandate:</strong> {r['Recommended Action']}
                </div>
                <div style="display:grid; grid-template-columns: repeat(auto-fit, minmax(240px, 1fr)); gap:10px;">
                    <div style="background:rgba(245,158,11,0.05); border-left:3px solid #f59e0b; border-radius:6px; padding:10px 12px;">
                        <div style="font-size:0.72rem; font-weight:700; text-transform:uppercase; color:#f59e0b; margin-bottom:4px; display:flex; align-items:center; gap:4px;">
                            <span class="material-symbols-rounded" style="font-size:13px;">lock</span> Precondition Required
                        </div>
                        <div style="font-size:0.80rem; color:#cbd5e1; line-height:1.4;">
                            {r['Precondition Required']}
                        </div>
                    </div>
                    <div style="background:rgba(16,185,129,0.05); border-left:3px solid #10b981; border-radius:6px; padding:10px 12px;">
                        <div style="font-size:0.72rem; font-weight:700; text-transform:uppercase; color:#10b981; margin-bottom:4px; display:flex; align-items:center; gap:4px;">
                            <span class="material-symbols-rounded" style="font-size:13px;">verified</span> Completion Evidence
                        </div>
                        <div style="font-size:0.80rem; color:#cbd5e1; line-height:1.4;">
                            {r['Completion Evidence']}
                        </div>
                    </div>
                    <div style="background:rgba(244,63,94,0.05); border-left:3px solid #f43f5e; border-radius:6px; padding:10px 12px;">
                        <div style="font-size:0.72rem; font-weight:700; text-transform:uppercase; color:#f43f5e; margin-bottom:4px; display:flex; align-items:center; gap:4px;">
                            <span class="material-symbols-rounded" style="font-size:13px;">warning</span> Monitoring Tripwire
                        </div>
                        <div style="font-size:0.80rem; color:#cbd5e1; line-height:1.4;">
                            {r['Monitoring Tripwire']}
                        </div>
                    </div>
                </div>
            </div>
            """
            render_html(card_html, unsafe_allow_html=True)

    # Missing Data & Decision Limitations
    render_html('<hr style="border-color:rgba(255,255,255,0.08); margin:20px 0 16px 0;">', unsafe_allow_html=True)
    render_html('<div class="bento-subtitle">SEBI DRHP Information Gaps & Blocked Decisions</div>', unsafe_allow_html=True)
    render_html('<div class="bento-title">Decision Limitations & Unsupplied Disclosures Register</div>', unsafe_allow_html=True)
    lims = getattr(dossier, "limitations", [])
    if not lims:
        st.success("Zero active decision limitations. All material data fields have been reconciled against audited disclosures.", icon=":material/check_circle:")
    else:
        lim_rows = []
        for l in lims:
            lim_rows.append({
                "Gap ID": l.gap_id,
                "Information Item": l.item_name,
                "Affected Dimension": l.affected_dimension,
                "Status": l.current_status,
                "Priority": l.materiality_priority,
                "Blocked Decision": l.blocked_decision_or_recommendation,
                "Recommended Diligence Request": l.recommended_diligence_request,
            })
        st.dataframe(pd.DataFrame(lim_rows), use_container_width=True, hide_index=True)

    # Online Ingestion Diagnostic
    render_html('<hr style="border-color:rgba(255,255,255,0.08); margin:20px 0 16px 0;">', unsafe_allow_html=True)
    render_html('<div class="bento-subtitle">Automated Provenance & Anti-Fabrication Verification</div>', unsafe_allow_html=True)
    render_html('<div class="bento-title">Online Ingestion Diagnostic Card</div>', unsafe_allow_html=True)
    audit_rows = []
    for item in dossier.audit_report:
        audit_rows.append({
            "Financial Variable": item.field_name,
            "Raw Extracted Text": item.raw_extracted_value,
            "Normalized Metric": item.normalized_metric,
            "Audit Status": item.status,
            "SEBI ICDR Citation Anchor": item.citation,
            "Confidence": f"{item.confidence_score * 100:.0f}%",
        })
    st.dataframe(pd.DataFrame(audit_rows), use_container_width=True, hide_index=True)
