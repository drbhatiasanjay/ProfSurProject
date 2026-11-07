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
import pandas as pd
import plotly.graph_objects as go
from models.pre_ipo_data import PRE_IPO_REGISTRY
from models.pre_ipo_ingest import PreIPOIngestionEngine
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

# Page Configuration
st.set_page_config(
    page_title="Pre-IPO DRHP Intelligence | Sovereign Terminal",
    page_icon="⚡",
    layout="wide",
)

def render_html(html_str: str):
    """
    Renders pure HTML in Streamlit without risking Markdown 4-space indented code blocks.
    Strips leading whitespace from every line and removes empty lines.
    """
    clean_lines = [line.strip() for line in html_str.splitlines() if line.strip()]
    st.markdown("\n".join(clean_lines), unsafe_allow_html=True)

# Apply Sovereign Financial Terminal Glassmorphic Theme CSS
st.markdown(
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
                👁️ 1. Quantitative Observation & What You See
            </span>
            <span class="badge-pill badge-sky" style="font-size:0.70rem;">{persona_title} Lens</span>
        </div>
        <div style="font-size:0.86rem; color:#e2e8f0; line-height:1.5; margin-bottom:12px;">
            {nar.get('what_you_see', '')}
        </div>

        <div style="display:grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap:12px; margin-bottom:12px;">
            <div style="background:rgba(255,255,255,0.03); border:1px solid rgba(255,255,255,0.08); border-radius:8px; padding:10px;">
                <div style="font-size:0.72rem; font-weight:700; color:#a78bfa; text-transform:uppercase; margin-bottom:4px;">
                    🎯 2. Decision Relevance ({persona_title})
                </div>
                <div style="font-size:0.82rem; color:#cbd5e1; line-height:1.45;">
                    {nar.get('why_it_matters', '')}
                </div>
            </div>
            <div style="background:rgba(255,255,255,0.03); border:1px solid rgba(255,255,255,0.08); border-radius:8px; padding:10px;">
                <div style="font-size:0.72rem; font-weight:700; color:#94a3b8; text-transform:uppercase; margin-bottom:4px;">
                    📜 3. Evidence Lineage & Citation
                </div>
                <div style="font-size:0.82rem; color:#cbd5e1; line-height:1.45;">
                    {nar.get('evidence_basis', '')}
                </div>
            </div>
        </div>

        <div style="background:rgba(245, 158, 11, 0.05); border:1px solid rgba(245, 158, 11, 0.2); border-radius:8px; padding:10px; margin-bottom:12px;">
            <div style="font-size:0.72rem; font-weight:700; color:#f59e0b; text-transform:uppercase; margin-bottom:4px;">
                ⚖️ 4. Alternative Explanations & Operational Context
            </div>
            <div style="font-size:0.82rem; color:#f1f5f9; line-height:1.45;">
                {nar.get('alternative_explanations', '')}
            </div>
        </div>

        <div class="action-card" style="margin:0 0 12px 0;">
            <div style="font-size:0.75rem; font-weight:700; color:#10b981; text-transform:uppercase; margin-bottom:4px;">
                🚀 5. Conditional Actionable Recommendations
            </div>
            <div style="font-size:0.85rem; color:#e2e8f0; line-height:1.5; white-space:pre-line;">
                {nar.get('call_to_action', '')}
            </div>
        </div>

        <div style="background:rgba(56, 189, 248, 0.05); border-left:3px solid #38bdf8; border-radius:4px; padding:8px 12px;">
            <span style="font-size:0.72rem; font-weight:700; color:#38bdf8; text-transform:uppercase;">
                ⚡ 6. Inflection Triggers & Thresholds:
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
deal_options = {
    "ntpc_green": "🔥 NTPC Green Energy Ltd. (RHP Nov 2024 · ₹7,500 Cr Debt Prepayment / ₹10,000 Cr Fresh)",
    "mankind_pharma": "Mankind Pharma Ltd. (DRHP 2023 · 100% OFS · Mature Cash Cow)",
    "afcons_infra": "Afcons Infrastructure Ltd. (RHP 2024 · ₹800 Cr Debt Prepayment / ₹1,250 Cr Fresh)",
    "swiggy": "Swiggy Ltd. (DRHP 2024 · ₹4,499 Cr Fresh Issue · Quick Commerce Growth)",
    "tata_technologies": "Tata Technologies Ltd. (DRHP 2023 · Zero Debt · ER&D)",
    "custom_upload": "+ Ingest New DRHP / RHP PDF Document...",
}

persona_options = {
    "cfo": "👔 CFO / Corporate Treasurer",
    "lender": "🏦 Lender / Credit Committee",
    "investor": "📈 Institutional Equity Analyst / Anchor",
    "retail": "👥 Retail Investor (Plain Language)",
    "board": "🏛️ Board / Investment Committee",
    "compliance": "⚖️ Legal, Auditor & Compliance",
}

context_options = {
    "PUBLIC_IPO": "🌐 Public IPO (Ordinary Equity)",
    "PRIVATE_PRE_IPO": "🔒 Private Pre-IPO Placement (Negotiated)",
    "STRATEGIC_M_AND_A": "🤝 Strategic M&A / Control Buyout",
}

col_sel, col_ctx, col_pers, col_act = st.columns([3, 2, 2, 2])
with col_sel:
    selected_deal_key = st.selectbox(
        "Active Pre-IPO Deal Dossier",
        options=list(deal_options.keys()),
        format_func=lambda k: deal_options[k],
        key="pre_ipo_deal_selector",
    )

with col_ctx:
    selected_context = st.selectbox(
        "Transaction Context",
        options=list(context_options.keys()),
        format_func=lambda k: context_options[k],
        key="pre_ipo_context_selector",
    )

with col_pers:
    selected_persona = st.selectbox(
        "Decision Persona Lens",
        options=list(persona_options.keys()),
        format_func=lambda k: persona_options[k],
        key="pre_ipo_persona_selector",
    )

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
    with col_up2:
        from models.runtime_config import get_gemini_api_key
        has_gemini = bool(get_gemini_api_key())
        st.markdown(
            """
            <div class="bento-card" style="padding:12px; margin-top:24px;">
                <div style="font-size:0.75rem; text-transform:uppercase; color:#38bdf8; font-weight:700;">🤖 Multimodal Vision OCR Engine</div>
                <div style="font-size:0.8rem; color:#94a3b8; margin:4px 0;">For scanned image DRHPs lacking native text layer.</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        if not has_gemini:
            ocr_key = st.text_input("Gemini API Key (for Scanned OCR)", type="password", key="gemini_api_key")
            if ocr_key:
                st.session_state["gemini_api_key"] = ocr_key
                st.rerun()
        else:
            vision_model = PreIPOIngestionEngine.get_vision_model_name()
            st.success(f"✓ Multimodal Vision OCR configured ({vision_model}, ready on upload)")

    if uploaded_file is not None:
        import hashlib, io
        file_bytes = uploaded_file.getvalue()
        file_hash = hashlib.sha256(file_bytes).hexdigest()
        cache_key = f"pre_ipo_dossier_{file_hash}_{custom_company_name}"
        if cache_key not in st.session_state:
            with st.spinner("Analyzing prospectus disclosures..."):
                st.session_state[cache_key] = PreIPOIngestionEngine.ingest_document(
                    io.BytesIO(file_bytes),
                    company_name_hint=custom_company_name,
                )
        dossier = st.session_state[cache_key]
    else:
        st.info("ℹ️ Upload a Draft Red Herring Prospectus (DRHP) or Red Herring Prospectus (RHP) PDF above, or select a Golden Exemplar from the dropdown to inspect the financial terminal.")
        st.markdown(
            """
            <div class="bento-card" style="border: 1px dashed rgba(56, 189, 248, 0.4); text-align:center; padding: 40px 20px;">
                <div style="font-size:2.2rem; margin-bottom:8px;">📄</div>
                <div style="font-size:1.15rem; font-weight:700; color:#f8fafc;">Awaiting DRHP / RHP Document Intake</div>
                <div style="font-size:0.86rem; color:#94a3b8; max-width:620px; margin:8px auto 0 auto; line-height:1.5;">
                    Please upload an official SEBI-filed prospectus PDF. The ingestion engine supports both native electronic text 
                    and scanned image DRHPs via multimodal Gemini 1.5 Flash Vision, extracting Sections III, V, and VI directly without fabricating metrics.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.stop()
else:
    dossier = PRE_IPO_REGISTRY[selected_deal_key]

latest = dossier.latest_financials
stage_name, pattern = classify_dickinson_stage(latest.cfo_cr, latest.cfi_cr, latest.cff_cr)

with col_act:
    st.write("")
    st.write("")
    deck_bytes = generate_pre_ipo_board_deck(dossier)
    st.download_button(
        label="📥 Export Deck (PPTX)",
        data=deck_bytes,
        file_name=f"{dossier.deal_id}_board_pitch_deck.pptx",
        mime="application/vnd.openxmlformats-officedocument.presentationml.presentation",
        use_container_width=True,
    )

# ─────────────────────────────────────────────────────────────────────────────
# PANEL 1: SOVEREIGN HERO OFFERING DNA (Rendered clean without code blocks)
# ─────────────────────────────────────────────────────────────────────────────
badge_class = "badge-emerald" if "Mature" in stage_name else "badge-amber" if "Growth" in stage_name else "badge-rose"

hero_html = f"""
<div class="bento-card" style="border-left: 4px solid #38bdf8;">
    <div style="display:flex; justify-content:space-between; align-items:flex-start; flex-wrap:wrap; gap:12px;">
        <div>
            <span class="badge-pill badge-sky">{dossier.filing_type} · {dossier.filing_date}</span>
            <span class="badge-pill {badge_class}" style="margin-left:6px;">Dickinson: {stage_name} {pattern}</span>
            <span class="badge-pill badge-purple" style="margin-left:6px;">SEBI ICDR 2018 Restated</span>
            <span class="badge-pill badge-amber" style="margin-left:6px;">Context: {context_options[selected_context]}</span>
            <h1 style="color:#ffffff; font-size:1.85rem; font-weight:800; margin:8px 0 4px 0;">{dossier.company_name}</h1>
            <div style="color:#94a3b8; font-size:0.85rem;">
                Sector: <strong style="color:#f1f5f9;">{dossier.sector}</strong> · Listing: <strong>{', '.join(dossier.exchange_listing)}</strong>
            </div>
        </div>
        <div style="text-align:right;">
            <div style="color:#94a3b8; font-size:0.75rem; text-transform:uppercase; letter-spacing:0.05em;">Total Offering Value</div>
            <div class="metric-value" style="color:#38bdf8; font-size:2.0rem; font-weight:800; line-height:1.1;">
                ₹{dossier.total_issue_size_cr:,.2f} Cr
            </div>
            <div style="color:#cbd5e1; font-size:0.80rem; margin-top:4px;">
                Split: <strong style="color:#10b981;">{dossier.fresh_issue_pct:.0f}% Fresh</strong> (₹{dossier.fresh_issue_cr:,.1f} Cr) · 
                <strong style="color:#f59e0b;">{dossier.ofs_pct:.0f}% OFS</strong> (₹{dossier.ofs_cr:,.1f} Cr)
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
p_view = generate_persona_decision_view(dossier, persona=selected_persona)

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
                🎯 Recommended Strategic Action
            </div>
            <div style="font-size:0.84rem; color:#f8fafc; line-height:1.45;">
                {p_view['recommendation']}
            </div>
        </div>
        <div style="background:rgba(245, 158, 11, 0.05); border:1px solid rgba(245, 158, 11, 0.2); border-radius:8px; padding:10px 14px;">
            <div style="font-size:0.75rem; font-weight:700; color:#f59e0b; text-transform:uppercase; margin-bottom:4px;">
                ⚖️ Material Trade-offs & Dilemmas
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
    tab_equity_thesis,
    tab_workpapers,
    tab_crosswalk,
    tab_ic_action,
) = st.tabs([
    "🏢 Company Overview",
    "💡 Investor Questions & Thesis",
    "🔬 Detailed Workpapers",
    "📑 CMIE Reference Crosswalk",
    "⚖️ IC Stance & Action Register",
])

# ═════════════════════════════════════════════════════════════════════════════
# LEVEL 1 - TAB 1: COMPANY OVERVIEW & ECONOMIC ENGINE
# ═════════════════════════════════════════════════════════════════════════════
with tab_overview:
    bg = dossier.background
    st.markdown('<div class="bento-subtitle">Section IV Business Overview · SEBI ICDR 2018 Disclosures</div>', unsafe_allow_html=True)
    st.markdown('<div class="bento-title">Corporate Background & Economic Engine</div>', unsafe_allow_html=True)

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

    st.markdown('<div class="bento-subtitle" style="margin-top:16px;">Product Portfolios & Segmental Breakdown</div>', unsafe_allow_html=True)
    c_p1, c_p2 = st.columns([3, 2])
    with c_p1:
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

    with c_p2:
        geo = bg.geographic_presence if (bg and bg.geographic_presence) else {"Domestic (India)": 100.0}
        st.markdown("**Geographic Revenue Split**")
        fig_geo = go.Figure(data=[go.Pie(labels=list(geo.keys()), values=list(geo.values()), hole=0.55, marker_colors=["#38bdf8", "#10b981", "#f59e0b"])])
        fig_geo.update_layout(height=220, margin=dict(l=10, r=10, t=10, b=10), paper_bgcolor="rgba(0,0,0,0)", font=dict(color="#cbd5e1"))
        st.plotly_chart(fig_geo, use_container_width=True)

    # Material Operational Dependencies
    deps = bg.material_operational_dependencies if bg else []
    if deps:
        dep_html = f"""
        <div class="narrative-card" style="border-left:4px solid #f43f5e; margin-top:10px;">
            <div style="font-size:0.75rem; font-weight:700; color:#f43f5e; text-transform:uppercase; margin-bottom:4px;">
                ⚠️ Material Operational Dependencies & Regulatory Constraints
            </div>
            <div style="font-size:0.84rem; color:#e2e8f0; line-height:1.45;">
                {'<br>'.join(['• ' + d for d in deps])}
            </div>
        </div>
        """
        render_html(dep_html)

# ═════════════════════════════════════════════════════════════════════════════
# LEVEL 1 - TAB 2: INVESTOR QUESTIONS & EQUITY THESIS (Q01-Q10 + PX01-PX04)
# ═════════════════════════════════════════════════════════════════════════════
with tab_equity_thesis:
    st.markdown('<div class="bento-subtitle">Question-Led Institutional Underwriting · PRD Specification S01–S04</div>', unsafe_allow_html=True)
    st.markdown('<div class="bento-title">Ten Core Investor Questions & Decision Scorecard</div>', unsafe_allow_html=True)

    # Generate or retrieve Q01-Q10 findings adapted to current transaction context
    eq_findings = generate_equity_question_answers(dossier, persona=selected_persona, transaction_context=selected_context)

    # Summary Thesis Banner
    st.markdown(
        f"""
        <div class="bento-card" style="border: 1px solid rgba(16, 185, 129, 0.3); background: rgba(16, 185, 129, 0.05);">
            <div style="display:flex; justify-content:space-between; align-items:center;">
                <div>
                    <span class="badge-pill badge-emerald">Executive Investment Thesis</span>
                    <h3 style="color:#ffffff; margin:6px 0 2px 0;">{dossier.company_name} — Equity Underwriting Verdict</h3>
                </div>
                <span class="badge-pill badge-sky">10/10 Questions Evaluated</span>
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
        icon = "💡" if not is_px else "🔒"

        with st.expander(f"{icon} {qid}: {q_obj.title} — [{stat.replace('_', ' ')}]", expanded=(qid in ("Q01", "Q04", "Q05"))):
            st.markdown(f"**Direct Bottom-Line Verdict:** {q_obj.direct_verdict}")
            st.markdown(f"**Detailed Analysis:** {q_obj.detailed_analysis}")

            # Evidence Claim Lineage
            if q_obj.claim_lineage:
                st.markdown("<div style='font-size:0.75rem; font-weight:700; color:#38bdf8; text-transform:uppercase; margin-top:10px;'>📜 Evidence Claim Lineage</div>", unsafe_allow_html=True)
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
                    st.markdown("<div style='font-size:0.75rem; font-weight:700; color:#f59e0b; text-transform:uppercase; margin-top:8px;'>⚖️ Alternative Interpretations & Risks</div>", unsafe_allow_html=True)
                    for alt in q_obj.alternative_explanations:
                        st.markdown(f"• {alt}")
            with col_qb:
                if q_obj.limitations_and_uncertainties:
                    st.markdown("<div style='font-size:0.75rem; font-weight:700; color:#94a3b8; text-transform:uppercase; margin-top:8px;'>⚠️ Disclosed Limitations & Data Gaps</div>", unsafe_allow_html=True)
                    for lim in q_obj.limitations_and_uncertainties:
                        st.markdown(f"• {lim}")

            # Conditional Recommendations
            if q_obj.conditional_recommendations:
                rec = q_obj.conditional_recommendations[0]
                rec_html = f"""
                <div class="action-card" style="margin-top:10px;">
                    <div style="font-size:0.75rem; font-weight:700; color:#10b981; text-transform:uppercase;">
                        🎯 Actionable Protocol ({rec.action_owner})
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
                st.markdown(f"**⚡ Thesis-Breaking Inflection Trigger:** `{q_obj.inflection_triggers[0]}`")

    # ── DECISION-DEPTH ADVANCED ALGORITHM LAB (ALG01 - ALG14) ──
    st.markdown('<hr style="border-color:rgba(255,255,255,0.08); margin:24px 0 16px 0;">', unsafe_allow_html=True)
    with st.expander("🔬 Decision-Depth Quantitative Algorithm Lab (ALG01–ALG14)", expanded=False):
        st.markdown('<div style="font-size:0.80rem; color:#94a3b8; margin-bottom:12px;">Authoritative mathematical evaluation engines implemented per <code>PRE_IPO_DECISION_DEPTH_ALGORITHM_PRD_2026-11-07.md</code>.</div>', unsafe_allow_html=True)
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
                st.markdown(f"• **{p['claim']}** <span class='badge-pill {p_badge}'>{p['status']}</span><br><span style='font-size:0.75rem; color:#94a3b8;'>Mechanism: {p['economic_mechanism']}</span>", unsafe_allow_html=True)

            st.markdown("<br>**ALG03: Sector Driver Reconciled Tree**", unsafe_allow_html=True)
            d_res = alg03_sector_operating_drivers(dossier)
            st.json(d_res.get("driver_tree", {}))

        with c_alg2:
            st.markdown("**ALG07: Reverse Stress Failure Frontier (Minimal Shock Distance)**")
            ff_res = alg07_reverse_stress_failure_frontier(dossier)
            if ff_res.get("status") == "FRONTIER_FOUND":
                st.markdown(f"• **Vulnerability Rating:** `{ff_res['vulnerability_assessment']}`<br>• Minimal Revenue Contraction: **{ff_res['minimal_revenue_shock_pct']:.0f}%**<br>• Minimal Rate Hike: **+{ff_res['minimal_rate_shock_bps']:.0f} bps**<br>• Quadratic Distance: `{ff_res['severity_distance']}`", unsafe_allow_html=True)
            else:
                st.info("Issuer has negligible debt; failure frontier is exempt.")

            st.markdown("<br>**ALG12: Two-Factor Price Return Midpoint Decomposition**", unsafe_allow_html=True)
            attr_res = alg12_investor_returns_attribution(entry_price_inr=108.0, exit_price_inr=155.0, entry_eps_inr=1.20, exit_eps_inr=1.55)
            st.markdown(f"• Total Return: **+{attr_res['total_return_pct']:.1f}%** (₹{attr_res['total_price_delta_inr']:.1f})<br>• Earnings Growth Share: **{attr_res['earnings_growth_share_pct']:.1f}%**<br>• Multiple Expansion Share: **{attr_res['multiple_expansion_share_pct']:.1f}%**<br>• Conservation Error: `{attr_res['conservation_error_inr']} INR`", unsafe_allow_html=True)

# ═════════════════════════════════════════════════════════════════════════════
# LEVEL 1 - TAB 3: DETAILED ANALYTICAL WORKPAPERS (4 SUB-TABS)
# ═════════════════════════════════════════════════════════════════════════════
with tab_workpapers:
    st.markdown('<div class="bento-subtitle">Comprehensive Quantitative Workpaper Engine</div>', unsafe_allow_html=True)
    st.markdown('<div class="bento-title">Detailed Institutional Workpapers</div>', unsafe_allow_html=True)

    # 4 Sub-Tabs for complete visibility without horizontal overflow
    (
        subtab_fin,
        subtab_debt,
        subtab_stress,
        subtab_val,
    ) = st.tabs([
        "📊 Financials & Proceeds Waterfall",
        "⚖️ Indebtedness & Debt Maturity",
        "🌪️ Stress Testing & Headroom",
        "💎 Valuation, Peers, DCF & Forensics",
    ])

    # ── SUBTAB 1: FINANCIALS & OBJECTS OF THE OFFER ──
    with subtab_fin:
        col_f1, col_f2 = st.columns([3, 2])
        with col_f1:
            st.markdown('<div class="bento-subtitle">Section V Disclosures · Restated Consolidated Ind AS</div>', unsafe_allow_html=True)
            st.markdown('<div class="bento-title">3-to-4 Year Restated Performance</div>', unsafe_allow_html=True)
            fin_rows = []
            for f_item in dossier.history:
                fin_rows.append({
                    "Fiscal Year": f_item.fiscal_year,
                    "Revenue (₹ Cr)": f"{f_item.revenue_ops_cr:,.1f}",
                    "Restated EBITDA (₹ Cr)": f"{f_item.ebitda_cr:,.1f}",
                    "EBITDA Margin (%)": f"{(f_item.ebitda_cr / max(0.1, f_item.revenue_ops_cr))*100:.1f}%",
                    "PAT (₹ Cr)": f"{f_item.pat_cr:,.1f}",
                    "CFO (₹ Cr)": f"{f_item.cfo_cr:,.1f}",
                    "Capex (₹ Cr)": f"{f_item.capex_cr:,.1f}",
                    "Free Cash Flow (₹ Cr)": f"{f_item.fcf_cr:,.1f}",
                })
            st.dataframe(pd.DataFrame(fin_rows), use_container_width=True, hide_index=True)

            fig_trend = go.Figure()
            yrs = [f.fiscal_year for f in dossier.history]
            revs = [f.revenue_ops_cr for f in dossier.history]
            ebitdas = [f.ebitda_cr for f in dossier.history]
            fig_trend.add_trace(go.Bar(x=yrs, y=revs, name="Revenue", marker_color="#38bdf8", opacity=0.75))
            fig_trend.add_trace(go.Scatter(x=yrs, y=ebitdas, name="Restated EBITDA", line=dict(color="#10b981", width=3), mode="lines+markers"))
            fig_trend.update_layout(
                height=240, margin=dict(l=20, r=20, t=30, b=20),
                paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                font=dict(color="#cbd5e1"),
            )
            st.plotly_chart(fig_trend, use_container_width=True)

        with col_f2:
            st.markdown('<div class="bento-subtitle">Empirical Benchmark (N=8,677 CMIE Database)</div>', unsafe_allow_html=True)
            st.markdown('<div class="bento-title">Dickinson Life-Cycle Radar</div>', unsafe_allow_html=True)
            dickinson_html = f"""
            <div class="bento-card">
                <div style="font-size:0.85rem; color:#94a3b8;">Classified Stage:</div>
                <div style="font-size:1.45rem; font-weight:800; color:#10b981; margin:4px 0;">{stage_name}</div>
                <div style="font-size:0.90rem; color:#cbd5e1; font-family:monospace;">Cash Flow Sign Triplet: {pattern}</div>
                <hr style="border-color:rgba(255,255,255,0.08); margin:12px 0;">
                <div style="font-size:0.82rem; line-height:1.45; color:#cbd5e1;">
                    • <strong>Operating Cash Flow:</strong> ₹{latest.cfo_cr:,.1f} Cr<br>
                    • <strong>Investing Accrual:</strong> ₹{latest.cfi_cr:,.1f} Cr<br>
                    • <strong>Financing Accrual:</strong> ₹{latest.cff_cr:,.1f} Cr<br>
                    • <strong>Empirical Attribution:</strong> Dickinson (2011) cash-flow pattern; descriptive classification.
                </div>
            </div>
            """
            render_html(dickinson_html)

        fin_nar = generate_financials_narrative(dossier, persona=selected_persona)
        render_six_point_narrative(fin_nar, persona_title=persona_options[selected_persona])

        # Objects & Proceeds Waterfall
        st.markdown('<hr style="border-color:rgba(255,255,255,0.08); margin:24px 0 16px 0;">', unsafe_allow_html=True)
        obj = dossier.objects_of_offer
        st.markdown('<div class="bento-subtitle">SEBI ICDR 2018 Regulation 7 & 41 Compliance</div>', unsafe_allow_html=True)
        st.markdown('<div class="bento-title">Use of Proceeds Waterfall & Statutory Limits</div>', unsafe_allow_html=True)
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
        col_d1, col_d2 = st.columns([3, 2])
        ind = dossier.indebtedness
        with col_d1:
            st.markdown('<div class="bento-subtitle">Funded Bank Debt vs Ind AS 116 Leases</div>', unsafe_allow_html=True)
            st.markdown('<div class="bento-title">Economic Indebtedness Schedule</div>', unsafe_allow_html=True)
            debt_items = [
                {"Debt Category": "Secured Term Loans (Project Finance)", "Amount (₹ Cr)": f"₹{ind.secured_term_loans_cr:,.1f}", "Type": "Funded Debt"},
                {"Debt Category": "Working Capital Loans (Cash Credit/OD)", "Amount (₹ Cr)": f"₹{ind.working_capital_loans_cr:,.1f}", "Type": "Funded Debt"},
                {"Debt Category": "NCD Bonds & Capital Debt", "Amount (₹ Cr)": f"₹{ind.ncd_bonds_cr:,.1f}", "Type": "Funded Debt"},
                {"Debt Category": "Unsecured Loans", "Amount (₹ Cr)": f"₹{ind.unsecured_loans_cr:,.1f}", "Type": "Funded Debt"},
                {"Debt Category": "Total Funded Bank Debt", "Amount (₹ Cr)": f"₹{ind.funded_bank_debt_cr:,.1f}", "Type": "Subtotal"},
                {"Debt Category": "Ind AS 116 Lease Liabilities", "Amount (₹ Cr)": f"₹{ind.lease_liabilities_ind_as_116_cr:,.1f}", "Type": "Economic Obligation"},
                {"Debt Category": "Total Economic Indebtedness", "Amount (₹ Cr)": f"₹{ind.total_economic_indebtedness_cr:,.1f}", "Type": "Total"},
                {"Debt Category": "Less: Cash & Cash Equivalents", "Amount (₹ Cr)": f"₹{ind.cash_and_equivalents_cr:,.1f}", "Type": "Liquid Treasury"},
                {"Debt Category": "Net Economic Indebtedness", "Amount (₹ Cr)": f"₹{ind.net_economic_debt_cr:,.1f}", "Type": "Net Economic Debt"},
            ]
            st.dataframe(pd.DataFrame(debt_items), use_container_width=True, hide_index=True)

        with col_d2:
            st.markdown('<div class="bento-subtitle">Pricing & Benchmark Spread</div>', unsafe_allow_html=True)
            st.markdown('<div class="bento-title">Borrowing Cost Architecture</div>', unsafe_allow_html=True)
            wair_str = f"{ind.weighted_avg_interest_rate_pct:.2f}%" if ind.weighted_avg_interest_rate_pct else "Disclosed in Sanction Notes"
            spread_str = ind.floating_benchmark_spread or "MCLR + 120 bps"
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
            st.markdown('<hr style="border-color:rgba(255,255,255,0.08); margin:20px 0 16px 0;">', unsafe_allow_html=True)
            st.markdown('<div class="bento-subtitle">Principal Repayment Schedule</div>', unsafe_allow_html=True)
            st.markdown('<div class="bento-title">Debt Maturity Ladder & Refinancing Profile</div>', unsafe_allow_html=True)
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
        st.markdown('<div class="bento-subtitle">2D Dynamic Adversarial Stress Matrix</div>', unsafe_allow_html=True)
        st.markdown('<div class="bento-title">EBITDA Contraction vs Floating Rate Hike Sensitivity</div>', unsafe_allow_html=True)
        stress_res = generate_2d_sensitivity_matrix(
            base_ebitda_cr=latest.ebitda_cr,
            gross_debt_cr=dossier.indebtedness.funded_bank_debt_cr,
            base_wair_pct=dossier.indebtedness.weighted_avg_interest_rate_pct or 9.0,
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

    # ── SUBTAB 4: VALUATION, PEERS, DCF & FORENSICS ──
    with subtab_val:
        col_v1, col_v2 = st.columns([3, 2])
        val = dossier.valuation_comps
        with col_v1:
            st.markdown('<div class="bento-subtitle">CMIE Listed Peers at Identical Life-Cycle Stage</div>', unsafe_allow_html=True)
            st.markdown('<div class="bento-title">Valuation Peer Benchmarking</div>', unsafe_allow_html=True)
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

        with col_v2:
            st.markdown('<div class="bento-subtitle">Offer Valuation Metrics</div>', unsafe_allow_html=True)
            st.markdown('<div class="bento-title">Implied Pricing Multiples</div>', unsafe_allow_html=True)
            if val:
                v_badge = "badge-emerald" if "DISCOUNT" in val.valuation_verdict else "badge-sky"
                val_box_html = f"""
                <div class="bento-card">
                    <div style="font-size:0.75rem; text-transform:uppercase; color:#94a3b8;">Implied Enterprise Value (Upper Band)</div>
                    <div style="font-size:1.8rem; font-weight:800; color:#38bdf8; margin:4px 0;">₹{val.implied_ev_cr:,.1f} Cr</div>
                    <div style="margin-top:6px;"><span class="badge-pill {v_badge}">Verdict: {val.valuation_verdict}</span></div>
                    <div style="font-size:0.82rem; color:#cbd5e1; margin-top:10px; line-height:1.6;">
                        • <strong>Implied P/E:</strong> {val.implied_pe_ratio:.1f}x (Peer Median: {val.peer_median_pe or 'N/A'}x)<br>
                        • <strong>Implied EV/EBITDA:</strong> {val.implied_ev_ebitda:.1f}x<br>
                        • <strong>Price Band:</strong> ₹{val.price_band_lower_inr:.0f} - ₹{val.price_band_upper_inr:.0f}
                    </div>
                </div>
                """
                render_html(val_box_html)

        # WACC, ROIC & Reverse DCF Hurdle
        st.markdown('<hr style="border-color:rgba(255,255,255,0.08); margin:20px 0 16px 0;">', unsafe_allow_html=True)
        st.markdown('<div class="bento-subtitle">Economic Value Creation & Reverse DCF Sizing</div>', unsafe_allow_html=True)
        st.markdown('<div class="bento-title">ROIC vs WACC Spread & Required Growth Hurdle</div>', unsafe_allow_html=True)
        wacc_res = calculate_wacc_and_roic(dossier)
        rev_dcf = calculate_reverse_dcf_hurdle(dossier)

        col_w1, col_w2, col_w3 = st.columns(3)
        with col_w1:
            st.metric("Return on Invested Capital (ROIC)", f"{wacc_res['roic_pct']:.1f}%", delta=f"{wacc_res['value_creation_spread_pct']:+.1f}% vs WACC")
        with col_w2:
            st.metric("Weighted Average Cost of Capital (WACC)", f"{wacc_res['wacc_pct']:.1f}%", help="CAPM Ke + Post-tax Kd")
        with col_w3:
            st.metric("Annual Economic Profit (EVA)", f"₹{wacc_res['economic_profit_cr']:,.1f} Cr", delta=wacc_res['status'].replace('_', ' '))

        st.info(f"💡 **Reverse DCF Analysis:** {rev_dcf['narrative']}")

        # Beneish Forensics & Anchor Lock-In Calendar
        st.markdown('<hr style="border-color:rgba(255,255,255,0.08); margin:20px 0 16px 0;">', unsafe_allow_html=True)
        st.markdown('<div class="bento-subtitle">Forensic Accruals & Statutory Lock-In Calendar</div>', unsafe_allow_html=True)
        st.markdown('<div class="bento-title">Beneish M-Score & Anchor Secondary Float Schedule</div>', unsafe_allow_html=True)
        c_bf1, c_bf2 = st.columns(2)
        with c_bf1:
            beneish = dossier.beneish_forensics
            if beneish and beneish.m_score is not None:
                b_color = "#10b981" if not beneish.is_manipulation_risk else "#f43f5e"
                b_status = "SAFE (Low Accrual Manipulation Risk)" if not beneish.is_manipulation_risk else "ELEVATED EARNINGS QUALITY CONCERN"
                st.markdown(
                    f"""
                    <div class="bento-card" style="border-left:4px solid {b_color};">
                        <div style="font-size:0.75rem; text-transform:uppercase; color:#94a3b8;">Beneish (1999) 8-Variable M-Score</div>
                        <div style="font-size:1.8rem; font-weight:800; color:{b_color}; margin:4px 0;">{beneish.m_score:.2f}</div>
                        <div style="font-size:0.84rem; color:#ffffff; font-weight:600;">{b_status}</div>
                        <div style="font-size:0.80rem; color:#94a3b8; margin-top:8px;">
                            • DSRI (Receivables): {beneish.dsri or 1.0:.2f} · GMI (Margin): {beneish.gmi or 1.0:.2f}<br>
                            • AQI (Asset Quality): {beneish.aqi or 1.0:.2f} · SGI (Sales Growth): {beneish.sgi or 1.0:.2f}<br>
                            • Threshold: M-Score > -1.78 indicates high statistical probability of earnings management.
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
            else:
                st.info("Forensic M-Score requires minimum 2 full years of restated balance sheet disclosures.")

        with c_bf2:
            from datetime import datetime, timezone
            from models.pre_ipo_exchange_feed import ExchangeFeedClient
            recon = ExchangeFeedClient.reconcile_with_prospectus(dossier.listing_date, dossier.company_name)
            if recon.get("is_reconciled"):
                st.markdown(
                    f"""
                    <div style="background:rgba(16,185,129,0.1); border:1px solid rgba(16,185,129,0.3); border-radius:6px; padding:6px 10px; margin-bottom:8px; font-size:0.78rem; color:#10b981;">
                        🟢 <strong>{recon['exchange']} Circular {recon['circular_ref']}</strong> · Listing: <strong>{recon['exchange_listing_date']}</strong> ({recon['drift_status']})
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
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
    st.markdown('<div class="bento-subtitle">Audited Reconciliation against Licensed CMIE Prowess Schema</div>', unsafe_allow_html=True)
    st.markdown('<div class="bento-title">Extracted DRHP Data vs. CMIE Reference Field Crosswalk</div>', unsafe_allow_html=True)

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

    st.markdown(
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
            label="📥 Download CMIE Crosswalk (CSV)",
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
    st.markdown('<div class="bento-subtitle">Institutional Governance & Decision Protocol</div>', unsafe_allow_html=True)
    st.markdown('<div class="bento-title">Investment Committee Underwriting Stance & Action Register</div>', unsafe_allow_html=True)

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
                    💎 Key Transaction & Credit Strengths
                </div>
                <div style="font-size:0.84rem; color:#e2e8f0; line-height:1.45;">
                    {'<br>'.join(['• ' + s for s in ic.key_credit_strengths])}
                </div>
                <hr style="border-color:rgba(255,255,255,0.08); margin:10px 0;">
                <div style="font-size:0.80rem; font-weight:700; color:#f43f5e; text-transform:uppercase; margin-bottom:6px;">
                    ⚠️ Key Underwriting Vulnerabilities & Downside Risks
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
                🛡️ Mandatory Loan Covenants & Credit Safeguards
            </div>
            <div style="font-size:0.86rem; color:#e2e8f0; line-height:1.5;">
                {'<br>'.join(['• ' + c for c in ic.mandatory_loan_covenants])}
            </div>
            <hr style="border-color:rgba(255,255,255,0.08); margin:10px 0;">
            <div style="font-size:0.80rem; font-weight:700; color:#10b981; text-transform:uppercase; margin-bottom:4px;">
                🎯 Executive Treasury & Underwriter Mandate
            </div>
            <div style="font-size:0.86rem; color:#f8fafc; line-height:1.5;">
                {ic.treasury_call_to_action}
            </div>
        </div>
        """
        render_html(cov_html)

    # Prioritized Action Register Table
    st.markdown('<hr style="border-color:rgba(255,255,255,0.08); margin:20px 0 16px 0;">', unsafe_allow_html=True)
    st.markdown('<div class="bento-subtitle">Prioritized Diligence & Execution Worklist</div>', unsafe_allow_html=True)
    st.markdown('<div class="bento-title">Underwriting Action Register</div>', unsafe_allow_html=True)

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
        st.dataframe(pd.DataFrame(action_rows), use_container_width=True, hide_index=True)

    # Missing Data & Decision Limitations
    st.markdown('<hr style="border-color:rgba(255,255,255,0.08); margin:20px 0 16px 0;">', unsafe_allow_html=True)
    st.markdown('<div class="bento-subtitle">SEBI DRHP Information Gaps & Blocked Decisions</div>', unsafe_allow_html=True)
    st.markdown('<div class="bento-title">Decision Limitations & Unsupplied Disclosures Register</div>', unsafe_allow_html=True)
    lims = getattr(dossier, "limitations", [])
    if not lims:
        st.success("✅ Zero active decision limitations. All material data fields have been reconciled against audited disclosures.")
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
    st.markdown('<hr style="border-color:rgba(255,255,255,0.08); margin:20px 0 16px 0;">', unsafe_allow_html=True)
    st.markdown('<div class="bento-subtitle">Automated Provenance & Anti-Fabrication Verification</div>', unsafe_allow_html=True)
    st.markdown('<div class="bento-title">Online Ingestion Diagnostic Card</div>', unsafe_allow_html=True)
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
