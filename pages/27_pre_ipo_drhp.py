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
- CMIE Listed Peer Multiples (P/E, EV/EBITDA) at identical Dickinson Life-Cycle Stage
- Investment Committee (IC) Deal Memo & Prescriptive Underwriting Verdict
- One-Click 16:9 Vector Board Pitch Deck Generator
"""
import streamlit as st
from utils.html_blocks import render_html
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
)
from utils.pre_ipo_deck_generator import generate_pre_ipo_board_deck

# Page Configuration
st.set_page_config(
    page_title="Pre-IPO DRHP Intelligence | Sovereign Terminal",
    page_icon="⚡",
    layout="wide",
)

# Independent additive workflow; legacy terminal remains the default.
if st.radio("Pre-IPO workspace", ["Existing Pre-IPO terminal", "Decision-depth workbench"], horizontal=True, key="pre_ipo_workspace") == "Decision-depth workbench":
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
    </style>
    """,
    unsafe_allow_html=True,
)

def render_six_point_narrative(nar: dict, persona_title: str = "Active Persona"):
    """
    Renders institutional 6-point structured findings for analytical depth & evidence-backed action.
    """
    render_html(
        f"""
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
        """,
        unsafe_allow_html=True,
    )

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

col_sel, col_pers, col_act = st.columns([2, 2, 1])
with col_sel:
    selected_deal_key = st.selectbox(
        "Active Pre-IPO Deal Dossier",
        options=list(deal_options.keys()),
        format_func=lambda k: deal_options[k],
        key="pre_ipo_deal_selector",
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
        render_html(
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
            st.success("✓ Gemini 1.5 Flash Vision OCR active")

    if uploaded_file is not None:
        dossier = PreIPOIngestionEngine.ingest_document(
            uploaded_file,
            company_name_hint=custom_company_name,
        )
    else:
        st.info("ℹ️ Upload a Draft Red Herring Prospectus (DRHP) or Red Herring Prospectus (RHP) PDF above, or select a Golden Exemplar from the dropdown to inspect the financial terminal.")
        render_html(
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
        label="📥 Export Board Deck (PPTX)",
        data=deck_bytes,
        file_name=f"{dossier.deal_id}_board_pitch_deck.pptx",
        mime="application/vnd.openxmlformats-officedocument.presentationml.presentation",
        use_container_width=True,
    )

# ─────────────────────────────────────────────────────────────────────────────
# PANEL 1: SOVEREIGN HERO OFFERING DNA
# ─────────────────────────────────────────────────────────────────────────────
badge_class = "badge-emerald" if "Mature" in stage_name else "badge-amber" if "Growth" in stage_name else "badge-rose"

render_html(
    f"""
    <div class="bento-card" style="border-left: 4px solid #38bdf8;">
        <div style="display:flex; justify-content:space-between; align-items:flex-start; flex-wrap:wrap; gap:12px;">
            <div>
                <span class="badge-pill badge-sky">{dossier.filing_type} · {dossier.filing_date}</span>
                <span class="badge-pill {badge_class}" style="margin-left:6px;">Dickinson: {stage_name} {pattern}</span>
                <span class="badge-pill badge-purple" style="margin-left:6px;">SEBI ICDR 2018 Restated</span>
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
    """,
    unsafe_allow_html=True,
)

# ─────────────────────────────────────────────────────────────────────────────
# EXECUTIVE PERSONA DECISION COCKPIT
# ─────────────────────────────────────────────────────────────────────────────
p_view = generate_persona_decision_view(dossier, persona=selected_persona)

metric_cards_html = "".join([
    f'<div style="background:rgba(255,255,255,0.03); border:1px solid rgba(255,255,255,0.07); border-radius:6px; padding:8px 12px;">'
    f'<div style="font-size:0.70rem; color:#94a3b8; text-transform:uppercase;">{m[0]}</div>'
    f'<div style="font-size:1.15rem; font-weight:700; color:#38bdf8; margin-top:2px;">{m[1]}</div>'
    f'</div>'
    for m in p_view['key_metrics']
])

render_html(
    f"""
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
    """,
    unsafe_allow_html=True,
)

# ─────────────────────────────────────────────────────────────────────────────
# TABS FOR 11 INSTITUTIONAL BENTO PANELS
# ─────────────────────────────────────────────────────────────────────────────
(
    tab_fin,
    tab_objects,
    tab_debt,
    tab_stress,
    tab_captable,
    tab_forensics,
    tab_maturity,
    tab_valuation,
    tab_governance,
    tab_ic,
    tab_limitations,
    tab_audit,
) = st.tabs([
    "📊 Restated Financials",
    "🎯 Objects & Proceeds Waterfall",
    "⚖️ Indebtedness & Leases",
    "🌪️ Stress Testing & Headroom",
    "🧬 Cap Table & Dilution",
    "🔬 Forensic Accruals (Beneish)",
    "⏳ Debt Maturity Ladder",
    "💎 Valuation & Peer Comps",
    "🛡️ Governance & Working Capital",
    "📋 IC Deal Memo & Verdict",
    "⚠️ Missing Data & Limitations",
    "🔍 Online Ingestion Diagnostic",
])

# ── TAB 1: RESTATED FINANCIALS & DICKINSON BENCHMARK ──
with tab_fin:
    col_f1, col_f2 = st.columns([3, 2])
    with col_f1:
        render_html('<div class="bento-subtitle">Section V Disclosures · Restated Consolidated Ind AS</div>', unsafe_allow_html=True)
        render_html('<div class="bento-title">3-to-4 Year Restated Performance</div>', unsafe_allow_html=True)
        
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
            height=260,
            margin=dict(l=20, r=20, t=30, b=20),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            font=dict(color="#cbd5e1"),
        )
        st.plotly_chart(fig_trend, use_container_width=True)

    with col_f2:
        render_html('<div class="bento-subtitle">Empirical Benchmark (N=8,677 CMIE Database)</div>', unsafe_allow_html=True)
        render_html('<div class="bento-title">Dickinson Life-Cycle Radar</div>', unsafe_allow_html=True)
        
        render_html(
            f"""
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
            """,
            unsafe_allow_html=True,
        )

    # Narrative Synthesis & Prescriptive Call to Action (6-Point Standard)
    fin_nar = generate_financials_narrative(dossier, persona=selected_persona)
    render_six_point_narrative(fin_nar, persona_title=persona_options[selected_persona])

# ── TAB 2: OBJECTS OF THE OFFER & PROCEEDS WATERFALL ──
with tab_objects:
    obj = dossier.objects_of_offer
    render_html('<div class="bento-subtitle">SEBI ICDR 2018 Regulation 7 & 41 Compliance</div>', unsafe_allow_html=True)
    render_html('<div class="bento-title">Use of Proceeds Waterfall & Statutory Limits</div>', unsafe_allow_html=True)

    if obj and obj.gross_fresh_issue_cr > 0:
        c_obj1, c_obj2, c_obj3, c_obj4 = st.columns(4)
        with c_obj1:
            st.metric("Gross Fresh Issue", f"₹{obj.gross_fresh_issue_cr:,.1f} Cr")
        with c_obj2:
            st.metric("Scheduled Debt Prepayment", f"₹{obj.debt_prepayment_cr:,.1f} Cr")
        with c_obj3:
            st.metric("Capex & Inorganic Growth", f"₹{(obj.capex_expansion_cr + obj.inorganic_acquisition_cr):,.1f} Cr")
        with c_obj4:
            gcp_status = "✅ COMPLIANT" if obj.sebi_gcp_compliant else "❌ BREACH (>25%)"
            st.metric("GCP Share of Gross", f"{obj.gcp_pct_of_gross:.1f}%", delta=gcp_status)

        # Proceeds Waterfall Chart
        fig_waterfall = go.Figure(go.Waterfall(
            name="Proceeds Deployment",
            orientation="v",
            measure=["absolute", "relative", "relative", "relative", "relative", "total"],
            x=["Gross Fresh", "Issue Expenses", "Debt Prepayment", "Capex", "General Corporate", "Net Deployed"],
            textposition="outside",
            text=[f"₹{obj.gross_fresh_issue_cr:,.0f}", f"-₹{obj.issue_expenses_cr:,.0f}", f"-₹{obj.debt_prepayment_cr:,.0f}", f"-₹{obj.capex_expansion_cr:,.0f}", f"-₹{obj.general_corporate_purposes_cr:,.0f}", f"₹{obj.net_fresh_proceeds_cr:,.0f}"],
            y=[obj.gross_fresh_issue_cr, -obj.issue_expenses_cr, -obj.debt_prepayment_cr, -obj.capex_expansion_cr, -obj.general_corporate_purposes_cr, 0],
            connector={"line": {"color": "rgba(255,255,255,0.2)"}},
            decreasing={"marker": {"color": "#f59e0b"}},
            increasing={"marker": {"color": "#38bdf8"}},
            totals={"marker": {"color": "#10b981"}}
        ))
        fig_waterfall.update_layout(
            height=280,
            margin=dict(l=20, r=20, t=30, b=20),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font=dict(color="#cbd5e1"),
        )
        st.plotly_chart(fig_waterfall, use_container_width=True)

        # Pro-Forma Accretion Summary
        if obj.debt_prepayment_cr > 0:
            render_html(
                f"""
                <div class="bento-card" style="border:1px solid #10b981;">
                    <div style="font-size:0.75rem; color:#94a3b8; text-transform:uppercase;">Pro-Forma Debt Retirement & Financial Accretion</div>
                    <div style="display:flex; justify-content:space-between; flex-wrap:wrap; gap:16px; margin-top:8px;">
                        <div>
                            <div style="font-size:0.80rem; color:#94a3b8;">Annual Interest Cost Savings (Δ Finance Cost)</div>
                            <div class="metric-value" style="font-size:1.5rem; font-weight:800; color:#10b981;">+₹{obj.annual_interest_savings_cr:,.1f} Cr/yr</div>
                        </div>
                        <div>
                            <div style="font-size:0.80rem; color:#94a3b8;">Pro-Forma PAT Expansion (post 25.17% tax)</div>
                            <div class="metric-value" style="font-size:1.5rem; font-weight:800; color:#10b981;">+₹{obj.pro_forma_pat_accretion_cr:,.1f} Cr</div>
                        </div>
                        <div>
                            <div style="font-size:0.80rem; color:#94a3b8;">Pro-Forma EPS Impact</div>
                            <div class="metric-value" style="font-size:1.5rem; font-weight:800; color:{'#f43f5e' if obj.is_dilutive else '#38bdf8'};">
                                {f"-₹{abs(obj.eps_accretion_dilution_inr):.2f}" if obj.is_dilutive else f"+₹{obj.eps_accretion_dilution_inr:.2f}"} / share
                            </div>
                        </div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
    else:
        st.info("This offering is structured as a 100% Offer for Sale (OFS). All proceeds are received by selling shareholders; zero primary capital is raised for debt prepayment or capex.")

    obj_nar = generate_objects_narrative(dossier, persona=selected_persona)
    render_six_point_narrative(obj_nar, persona_title=persona_options[selected_persona])

# ── TAB 3: INDEBTEDNESS & LEASES ──
with tab_debt:
    render_html('<div class="bento-subtitle">Section VI Disclosures · Ind AS 116 Lease Analysis</div>', unsafe_allow_html=True)
    render_html('<div class="bento-title">Capital Structure & Indebtedness Breakdown</div>', unsafe_allow_html=True)

    include_leases = st.toggle("Include Ind AS 116 Lease Liabilities in Total Leverage", value=True)
    
    ind = dossier.indebtedness
    gross_debt = ind.total_economic_indebtedness_cr if include_leases else ind.funded_bank_debt_cr
    net_debt = max(0.0, gross_debt - ind.cash_and_equivalents_cr)
    
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric("Gross Indebtedness", f"₹{gross_debt:,.1f} Cr", help="Includes leases if toggled")
    with c2:
        st.metric("Cash & Equivalents", f"₹{ind.cash_and_equivalents_cr:,.1f} Cr")
    with c3:
        st.metric("Net Indebtedness", f"₹{net_debt:,.1f} Cr")
    with c4:
        ratio = round(net_debt / latest.ebitda_cr, 2) if latest.ebitda_cr > 0 else "N/A"
        st.metric("Net Debt / EBITDA", f"{ratio}x" if ratio != "N/A" else "Operating Loss")

    fig_indebt = go.Figure()
    fig_indebt.add_trace(go.Bar(name="Secured Term Loans", x=["Indebtedness"], y=[ind.secured_term_loans_cr], marker_color="#38bdf8"))
    fig_indebt.add_trace(go.Bar(name="Working Capital Loans", x=["Indebtedness"], y=[ind.working_capital_loans_cr], marker_color="#0284c7"))
    fig_indebt.add_trace(go.Bar(name="Unsecured / Other", x=["Indebtedness"], y=[ind.unsecured_loans_cr], marker_color="#818cf8"))
    if include_leases:
        fig_indebt.add_trace(go.Bar(name="Ind AS 116 Leases", x=["Indebtedness"], y=[ind.lease_liabilities_ind_as_116_cr], marker_color="#f59e0b"))
    fig_indebt.update_layout(
        barmode="stack",
        height=200,
        margin=dict(l=20, r=20, t=30, b=20),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#cbd5e1"),
    )
    st.plotly_chart(fig_indebt, use_container_width=True)

    debt_cap_prelim = compute_debt_capacity(
        ebitda_cr=latest.ebitda_cr,
        cfo_cr=latest.cfo_cr,
        capex_cr=latest.capex_cr,
        wair_pct=dossier.indebtedness.weighted_avg_interest_rate_pct or 8.5,
        current_gross_debt_cr=dossier.indebtedness.funded_bank_debt_cr,
        cash_cr=dossier.indebtedness.cash_and_equivalents_cr,
    )
    ind_nar = generate_indebtedness_narrative(dossier, debt_cap_prelim, persona=selected_persona)
    render_six_point_narrative(ind_nar, persona_title=persona_options[selected_persona])

# ── TAB 4: ADVERSARIAL STRESS & M&A CAPACITY ──
with tab_stress:
    col_s1, col_s2 = st.columns([3, 2])
    with col_s1:
        render_html('<div class="bento-subtitle">Quantitative Stress Testing</div>', unsafe_allow_html=True)
        render_html('<div class="bento-title">2D Interest Coverage Ratio (ICR) Sensitivity</div>', unsafe_allow_html=True)
        
        floating_pct = getattr(dossier.indebtedness, "floating_rate_debt_pct", 75.0)
        sens = generate_2d_sensitivity_matrix(
            base_ebitda_cr=latest.ebitda_cr,
            gross_debt_cr=dossier.indebtedness.funded_bank_debt_cr,
            base_wair_pct=dossier.indebtedness.weighted_avg_interest_rate_pct or 8.5,
            floating_debt_portion_pct=floating_pct,
        )
        s_df = pd.DataFrame(sens["matrix"])
        s_df = s_df.rename(columns={
            "ebitda_shock_pct": "EBITDA Shock (%)",
            "shocked_ebitda_cr": "Shocked EBITDA (₹ Cr)",
            "hike_0bps": "+0 bps (Base)",
            "hike_100bps": "+100 bps",
            "hike_200bps": "+200 bps",
            "hike_300bps": "+300 bps",
        })
        st.dataframe(s_df, use_container_width=True, hide_index=True)

    with col_s2:
        render_html('<div class="bento-subtitle">OakNorth Treasury Standard Sizing</div>', unsafe_allow_html=True)
        render_html('<div class="bento-title">Post-IPO M&A Headroom</div>', unsafe_allow_html=True)
        
        target_lev = st.slider("Target Max Leverage Ceiling (Net Debt / EBITDA)", min_value=1.5, max_value=4.0, value=2.5, step=0.25)
        debt_cap = compute_debt_capacity(
            ebitda_cr=latest.ebitda_cr,
            cfo_cr=latest.cfo_cr,
            capex_cr=latest.capex_cr,
            wair_pct=dossier.indebtedness.weighted_avg_interest_rate_pct or 8.5,
            current_gross_debt_cr=dossier.indebtedness.funded_bank_debt_cr,
            cash_cr=dossier.indebtedness.cash_and_equivalents_cr,
            target_leverage_ceiling=target_lev,
        )
        
        render_html(
            f"""
            <div class="bento-card" style="border:1px solid #10b981;">
                <div style="font-size:0.75rem; color:#94a3b8; text-transform:uppercase;">Unutilized Incremental M&A Headroom</div>
                <div class="metric-value" style="font-size:2.1rem; font-weight:800; color:#10b981; margin:6px 0;">
                    ₹{debt_cap['incremental_mna_headroom_cr']:,.1f} Cr
                </div>
                <div style="font-size:0.82rem; color:#cbd5e1;">
                    • <strong>Max Sustainable Debt:</strong> ₹{debt_cap['max_sustainable_debt_cr']:,.1f} Cr<br>
                    • <strong>Binding Constraint:</strong> {debt_cap['binding_constraint']}<br>
                    • <strong>Current Funded Net Debt / EBITDA:</strong> {debt_cap['current_net_debt_ebitda']}x<br>
                    • <strong>Current Interest Coverage Ratio (ICR):</strong> {debt_cap['current_icr']}x
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    stress_nar = generate_stress_narrative(dossier, sens, persona=selected_persona)
    render_six_point_narrative(stress_nar, persona_title=persona_options[selected_persona])

# ── TAB 5: CAP TABLE & DILUTION ──
with tab_captable:
    ct = dossier.cap_table
    render_html('<div class="bento-subtitle">SEBI ICDR 2018 Regulation 14 & 16 Disclosures</div>', unsafe_allow_html=True)
    render_html('<div class="bento-title">Cap Table, Ownership Dilution & Lock-in Schedule</div>', unsafe_allow_html=True)

    if ct:
        col_c1, col_c2, col_c3, col_c4 = st.columns(4)
        with col_c1:
            st.metric("Promoter Holding Pre-Offer", f"{ct.promoter_holding_pre_pct:.1f}%")
        with col_c2:
            st.metric("Promoter Holding Post-Offer", f"{ct.promoter_holding_post_pct:.1f}%")
        with col_c3:
            st.metric("Promoter Dilution", f"{ct.promoter_dilution_pct:.1f}%")
        with col_c4:
            st.metric("Public & Institutional Post", f"{ct.public_holding_post_pct:.1f}%")

        # Visual Cap Table Comparison
        fig_cap = go.Figure()
        fig_cap.add_trace(go.Bar(
            name="Promoter Group",
            x=["Pre-Offer", "Post-Offer"],
            y=[ct.promoter_holding_pre_pct, ct.promoter_holding_post_pct],
            marker_color="#38bdf8",
        ))
        fig_cap.add_trace(go.Bar(
            name="Public & Institutional",
            x=["Pre-Offer", "Post-Offer"],
            y=[100.0 - ct.promoter_holding_pre_pct, ct.public_holding_post_pct],
            marker_color="#10b981",
        ))
        fig_cap.update_layout(
            barmode="stack",
            height=220,
            margin=dict(l=20, r=20, t=30, b=20),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font=dict(color="#cbd5e1"),
        )
        st.plotly_chart(fig_cap, use_container_width=True)

        # Statutory Lock-In & Secondary Floating Supply Calendar
        render_html('<div class="bento-subtitle" style="margin-top:20px;">NSE / BSE Secondary Float Dynamics & Lock-In Timeline</div>', unsafe_allow_html=True)
        render_html('<div class="bento-title">Anchor Lock-in Expiry & Supply Overhang Calendar</div>', unsafe_allow_html=True)

        lock_schedule = generate_anchor_lockin_calendar(dossier)
        if lock_schedule:
            col_l1, col_l2, col_l3, col_l4 = st.columns(4)
            with col_l1:
                st.metric("Listing Date (T0)", lock_schedule[0].calendar_date, f"{lock_schedule[0].cumulative_free_float_pct:.1f}% Initial Float")
            with col_l2:
                m30 = lock_schedule[1]
                st.metric("30-Day Anchor Unlock (50%)", m30.calendar_date, f"₹{m30.unlocked_value_cr:,.1f} Cr Released")
            with col_l3:
                m90 = lock_schedule[2]
                st.metric("90-Day Full Unlock (100%)", m90.calendar_date, f"₹{m90.unlocked_value_cr:,.1f} Cr Released")
            with col_l4:
                st.metric("Post-90D Public Float", f"{lock_schedule[2].cumulative_free_float_pct:.1f}%", f"+{lock_schedule[2].cumulative_free_float_pct - lock_schedule[0].cumulative_free_float_pct:.1f}% Free Float Expansion")

            cal_rows = []
            for item in lock_schedule:
                cal_rows.append({
                    "Milestone Event": item.milestone_name,
                    "Trading Date": item.calendar_date,
                    "Days (T+)": f"T+{item.days_from_listing}",
                    "Unlocked %": f"{item.unlocked_pct:.1f}%",
                    "Unlocked Shares": f"{item.unlocked_shares_cr:,.2f} Cr",
                    "Unlocked Value (₹ Cr)": f"₹{item.unlocked_value_cr:,.1f}",
                    "Cumulative Free Float": f"{item.cumulative_free_float_pct:.1f}%",
                    "Supply Overhang Risk": item.supply_risk_level,
                    "Status": item.status,
                    "Statutory Citation": item.exchange_notice_ref,
                })
            st.dataframe(pd.DataFrame(cal_rows), use_container_width=True, hide_index=True)

            if selected_persona in ["investor", "retail"]:
                st.warning(
                    f"⚠️ **Secondary Supply Alert for {persona_options[selected_persona]}**: "
                    f"Day-30 ({m30.calendar_date}) and Day-90 ({m90.calendar_date}) expiries release a combined ₹{m30.unlocked_value_cr * 2:,.1f} Cr "
                    "of anchor stock into secondary circulation. Historical Indian primary market data shows institutional block placements "
                    "frequently create short-term price discovery pressure within 3 to 5 trading sessions around unlock dates."
                )
            elif selected_persona == "cfo":
                st.info(
                    f"💡 **Treasury & IR Liquidity Guidance**: "
                    f"Coordinate with syndicate BRLMs ahead of {m30.calendar_date} (Day 30) and {m90.calendar_date} (Day 90) "
                    "to assess institutional anchor rollover sentiment and mitigate secondary market liquidity volatility."
                )

    ct_nar = generate_cap_table_narrative(dossier, persona=selected_persona)
    render_six_point_narrative(ct_nar, persona_title=persona_options[selected_persona])

# ── TAB 6: FORENSIC ACCRUALS (BENEISH M-SCORE) ──
with tab_forensics:
    b = dossier.beneish_forensics
    render_html('<div class="bento-subtitle">Beneish (1999) & Roychowdhury (2006) Forensic Econometrics</div>', unsafe_allow_html=True)
    render_html('<div class="bento-title">Forensic Accruals & Window-Dressing Audit</div>', unsafe_allow_html=True)

    if b and b.is_computable and b.m_score is not None:
        col_b1, col_b2 = st.columns([1, 2])
        with col_b1:
            risk_color = "#10b981" if not b.is_manipulation_risk else "#f43f5e"
            risk_badge = "LOW PROBABILITY" if not b.is_manipulation_risk else "ELEVATED RISK FLAG"
            render_html(
                f"""
                <div class="bento-card" style="border:2px solid {risk_color}; text-align:center;">
                    <div style="font-size:0.75rem; color:#94a3b8; text-transform:uppercase;">Beneish Aggregate M-Score</div>
                    <div class="metric-value" style="font-size:2.8rem; font-weight:800; color:{risk_color}; margin:8px 0;">
                        {b.m_score:.2f}
                    </div>
                    <span class="badge-pill" style="background:{risk_color}22; color:{risk_color}; border:1px solid {risk_color};">
                        {risk_badge}
                    </span>
                    <div style="font-size:0.75rem; color:#94a3b8; margin-top:12px;">
                        Benchmark Critical Threshold: <strong>-1.78</strong><br>
                        (Scores &gt; -1.78 signal earnings manipulation)
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        with col_b2:
            render_html('<div class="bento-subtitle">8-Ratio Forensic Diagnostic Breakdown</div>', unsafe_allow_html=True)
            ratio_breakdown = [
                {"Ratio Variable": "Days Sales in Receivables (DSRI)", "Formula": "Receivables_t / Receivables_{t-1}", "Observed": f"{b.dsri:.2f}", "Normal Range": "< 1.25", "Status": "PASS" if b.dsri < 1.25 else "FLAG"},
                {"Ratio Variable": "Gross Margin Index (GMI)", "Formula": "GM_{t-1} / GM_t", "Observed": f"{b.gmi:.2f}", "Normal Range": "< 1.20", "Status": "PASS" if b.gmi < 1.20 else "FLAG"},
                {"Ratio Variable": "Asset Quality Index (AQI)", "Formula": "Non-CA PPE / Tot Assets", "Observed": f"{b.aqi:.2f}", "Normal Range": "< 1.25", "Status": "PASS" if b.aqi < 1.25 else "FLAG"},
                {"Ratio Variable": "Sales Growth Index (SGI)", "Formula": "Sales_t / Sales_{t-1}", "Observed": f"{b.sgi:.2f}", "Normal Range": "< 1.60", "Status": "PASS" if b.sgi < 1.60 else "FLAG"},
                {"Ratio Variable": "Depreciation Index (DEPI)", "Formula": "DeprRate_{t-1} / DeprRate_t", "Observed": f"{b.depi:.2f}", "Normal Range": "< 1.15", "Status": "PASS" if b.depi < 1.15 else "FLAG"},
                {"Ratio Variable": "Sales & Admin Expense (SGAI)", "Formula": "SGA%_t / SGA%_{t-1}", "Observed": f"{b.sgai:.2f}", "Normal Range": "< 1.20", "Status": "PASS" if b.sgai < 1.20 else "FLAG"},
                {"Ratio Variable": "Leverage Index (LVGI)", "Formula": "Lev_t / Lev_{t-1}", "Observed": f"{b.lvgi:.2f}", "Normal Range": "< 1.30", "Status": "PASS" if b.lvgi < 1.30 else "FLAG"},
                {"Ratio Variable": "Total Accruals to Assets (TATA)", "Formula": "(PAT - CFO) / Assets", "Observed": f"{b.tata:.3f}", "Normal Range": "< 0.05", "Status": "PASS" if b.tata < 0.05 else "FLAG"},
            ]
            st.dataframe(pd.DataFrame(ratio_breakdown), use_container_width=True, hide_index=True)
    else:
        st.warning("⚠️ Beneish (1999) 8-variable forensic score is currently UNAVAILABLE: multi-year balance sheet notes and standalone asset components are not supplied in this prospectus draft.")

    b_nar = generate_forensics_narrative(dossier, persona=selected_persona)
    render_six_point_narrative(b_nar, persona_title=persona_options[selected_persona])

# ── TAB 7: DEBT MATURITY LADDER ──
with tab_maturity:
    dm = dossier.debt_maturity
    render_html('<div class="bento-subtitle">Ind AS 107 Disclosures · Contractual Principal Cash Flows</div>', unsafe_allow_html=True)
    render_html('<div class="bento-title">Debt Maturity Ladder & Refinancing Profile</div>', unsafe_allow_html=True)

    if dm:
        col_m1, col_m2, col_m3, col_m4 = st.columns(4)
        with col_m1:
            st.metric("Year 1 Due (Current)", f"₹{dm.repayment_due_year_1_cr:,.1f} Cr")
        with col_m2:
            st.metric("Total Contractual Repayments", f"₹{dm.total_repayment_profile_cr:,.1f} Cr")
        with col_m3:
            st.metric("Weighted Avg Maturity", f"{dm.weighted_average_maturity_years:.1f} Yrs")
        with col_m4:
            st.metric("Refinancing Risk", dm.refinancing_risk_rating)

        # Repayment Ladder Chart
        fig_ladder = go.Figure()
        ladder_years = ["Within 1 Yr", "Year 2", "Year 3", "Year 4", "Year 5 & Beyond"]
        ladder_vals = [
            dm.repayment_due_year_1_cr,
            dm.repayment_due_year_2_cr,
            dm.repayment_due_year_3_cr,
            dm.repayment_due_year_4_cr,
            dm.repayment_due_year_5_plus_cr,
        ]
        fig_ladder.add_trace(go.Bar(
            x=ladder_years,
            y=ladder_vals,
            marker_color=["#f43f5e", "#f59e0b", "#38bdf8", "#38bdf8", "#10b981"],
            text=[f"₹{v:,.1f} Cr" for v in ladder_vals],
            textposition="auto",
        ))
        fig_ladder.update_layout(
            height=260,
            margin=dict(l=20, r=20, t=30, b=20),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font=dict(color="#cbd5e1"),
            yaxis_title="Principal Repayment (₹ Cr)",
        )
        st.plotly_chart(fig_ladder, use_container_width=True)

    render_html(
        f"""
        <div class="narrative-card">
            <div style="font-size:0.80rem; font-weight:700; color:#38bdf8; text-transform:uppercase; margin-bottom:4px;">
                💡 Quantitative Interpretation & What You Are Seeing
            </div>
            <div style="font-size:0.88rem; color:#e2e8f0; line-height:1.5;">
                The repayment schedule shows ₹{dm.repayment_due_year_1_cr if dm else 0:,.1f} Cr falling due within the next 12 months,
                representing immediate refinancing or debt retirement requirements.
                With a floating interest exposure of {dm.floating_rate_debt_pct if dm else 0:.0f}%,
                treasury liquidity reserves must match at least 100% of Year 1 maturities to avert liquidity squeeze.
            </div>
        </div>
        <div class="action-card">
            <div style="font-size:0.80rem; font-weight:700; color:#10b981; text-transform:uppercase; margin-bottom:4px;">
                🎯 Prescriptive Call to Action (Refinancing Playbook)
            </div>
            <div style="font-size:0.88rem; color:#e2e8f0; line-height:1.5;">
                1. <strong>Prepay Near-Term Maturities:</strong> Earmark primary IPO proceeds or operational cash to eliminate Year 1 maturities.<br>
                2. <strong>Tenor Extension:</strong> Approach syndicate lead banks to negotiate a 3-year extension on Year 2 & Year 3 maturities.<br>
                3. <strong>Benchmark Optimization:</strong> Swap 1-year MCLR benchmarked term loans for repo-linked or commercial paper spreads post-listing.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

# ── TAB 8: VALUATION & LISTED PEER COMPS ──
with tab_valuation:
    val = dossier.valuation_comps
    render_html('<div class="bento-subtitle">CMIE Database Peer Calibration at Identical Dickinson Stage</div>', unsafe_allow_html=True)
    render_html('<div class="bento-title">Valuation Multiples & Listed Sector Comps</div>', unsafe_allow_html=True)

    if val:
        col_v1, col_v2, col_v3, col_v4 = st.columns(4)
        with col_v1:
            st.metric("Price Band (INR)", f"₹{val.price_band_lower_inr:.0f} - ₹{val.price_band_upper_inr:.0f}")
        with col_v2:
            st.metric("Implied Market Cap", f"₹{val.implied_mcap_cr:,.1f} Cr")
        with col_v3:
            st.metric("Implied P/E Multiple", f"{val.implied_pe_ratio:.1f}x" if val.implied_pe_ratio > 0 else "Negative")
        with col_v4:
            st.metric("Implied EV / EBITDA", f"{val.implied_ev_ebitda:.1f}x" if val.implied_ev_ebitda > 0 else "Negative")

        render_html(f'<div class="bento-subtitle">Peer Universe: {val.sector_peer_group}</div>', unsafe_allow_html=True)
        peer_rows = []
        for p in val.peers:
            peer_rows.append({
                "Company Name": p.peer_name,
                "Ticker": p.ticker,
                "Market Cap (₹ Cr)": f"{p.mcap_cr:,.0f}",
                "P/E (x)": f"{p.pe_ratio:.1f}" if p.pe_ratio > 0 else "Loss",
                "EV/EBITDA (x)": f"{p.ev_ebitda:.1f}" if p.ev_ebitda > 0 else "Loss",
                "EV/Sales (x)": f"{p.ev_sales:.1f}",
                "P/B (x)": f"{p.pb_ratio:.1f}",
                "PAT Margin (%)": f"{p.pat_margin_pct:.1f}%",
                "RoE (%)": f"{p.roe_pct:.1f}%",
                "Dickinson Stage": p.dickinson_stage,
            })
        st.dataframe(pd.DataFrame(peer_rows), use_container_width=True, hide_index=True)

    val_nar = generate_valuation_narrative(dossier, persona=selected_persona)
    render_six_point_narrative(val_nar, persona_title=persona_options[selected_persona])

# ── TAB 9: SEBI GOVERNANCE & WORKING CAPITAL ──
with tab_governance:
    col_g1, col_g2 = st.columns(2)
    with col_g1:
        render_html('<div class="bento-subtitle">SEBI LODR & ICDR Governance Disclosures</div>', unsafe_allow_html=True)
        render_html('<div class="bento-title">Non-Financial Risk Profile</div>', unsafe_allow_html=True)
        gov = dossier.governance
        
        render_html(
            f"""
            <div class="bento-card">
                <div style="display:flex; justify-content:space-between; margin-bottom:8px;">
                    <span style="color:#cbd5e1;">Promoter Share Pledging:</span>
                    <strong style="color:{'#10b981' if gov.promoter_pledge_pct == 0 else '#f43f5e'};">{gov.promoter_pledge_pct:.1f}%</strong>
                </div>
                <div style="display:flex; justify-content:space-between; margin-bottom:8px;">
                    <span style="color:#cbd5e1;">Related Party Transactions (RPT) / Revenue:</span>
                    <strong>{gov.related_party_transactions_pct_rev:.1f}%</strong>
                </div>
                <div style="display:flex; justify-content:space-between; margin-bottom:8px;">
                    <span style="color:#cbd5e1;">Top 5 Customer Concentration:</span>
                    <strong>{gov.top_5_customer_concentration_pct:.1f}%</strong>
                </div>
                <div style="display:flex; justify-content:space-between; margin-bottom:8px;">
                    <span style="color:#cbd5e1;">Customer HHI Index:</span>
                    <span class="financial-num">{gov.herfindahl_hhi_index:.0f}</span>
                </div>
                <div style="display:flex; justify-content:space-between;">
                    <span style="color:#cbd5e1;">Contingent Liabilities / Net Worth:</span>
                    <strong>{gov.contingent_liabilities_pct_networth:.1f}%</strong>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with col_g2:
        render_html('<div class="bento-subtitle">Cash Conversion Dynamics</div>', unsafe_allow_html=True)
        render_html('<div class="bento-title">Working Capital Cycle</div>', unsafe_allow_html=True)
        wc = dossier.working_capital
        
        render_html(
            f"""
            <div class="bento-card">
                <div style="font-size:0.75rem; color:#94a3b8; text-transform:uppercase;">Net Cash Conversion Cycle (CCC)</div>
                <div class="metric-value" style="font-size:2.0rem; font-weight:800; color:#38bdf8; margin:4px 0;">
                    {wc.cash_conversion_cycle_days:.1f} Days
                </div>
                <div style="font-size:0.82rem; color:#cbd5e1; margin-top:8px;">
                    • <strong>Days Sales Outstanding (DSO):</strong> {wc.debtor_days_dso:.1f} days<br>
                    • <strong>Days Inventory Outstanding (DIO):</strong> {wc.inventory_days_dio:.1f} days<br>
                    • <strong>Days Payable Outstanding (DPO):</strong> {wc.creditor_days_dpo:.1f} days<br>
                    • <strong>Net Working Capital / Sales:</strong> {wc.net_working_capital_pct_sales:.1f}%
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    render_html(
        f"""
        <div class="narrative-card">
            <div style="font-size:0.80rem; font-weight:700; color:#38bdf8; text-transform:uppercase; margin-bottom:4px;">
                💡 Quantitative Interpretation & What You Are Seeing
            </div>
            <div style="font-size:0.88rem; color:#e2e8f0; line-height:1.5;">
                Promoter share encumbrance is at {gov.promoter_pledge_pct:.1f}%, indicating
                {'zero promoter margin loan vulnerability.' if gov.promoter_pledge_pct == 0 else 'pledged share collateral risk requiring monitoring.'}
                Top 5 customer concentration stands at {gov.top_5_customer_concentration_pct:.1f}% with an HHI score of {gov.herfindahl_hhi_index:.0f}.
                The Net Cash Conversion Cycle of {wc.cash_conversion_cycle_days:.1f} days indicates
                {'disciplined working capital velocity.' if wc.cash_conversion_cycle_days <= 60 else 'elongated collections requiring lender credit enhancement.'}
            </div>
        </div>
        <div class="action-card">
            <div style="font-size:0.80rem; font-weight:700; color:#10b981; text-transform:uppercase; margin-bottom:4px;">
                🎯 Prescriptive Call to Action (Governance & Vendor Terms Playbook)
            </div>
            <div style="font-size:0.88rem; color:#e2e8f0; line-height:1.5;">
                1. <strong>Covenant Safeguard:</strong> Require an undertaking that promoter encumbrances remain strictly zero post-listing.<br>
                2. <strong>RPT Scrutiny:</strong> Enforce audit committee pre-approval per SEBI LODR Regulation 23 for related party transactions.<br>
                3. <strong>Working Capital Financing:</strong> Structure supply chain vendor discounting facilities to reduce creditor DPO stress.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

# ── TAB 10: INVESTMENT COMMITTEE (IC) DEAL MEMO & VERDICT ──
with tab_ic:
    ic = dossier.ic_verdict
    render_html('<div class="bento-subtitle">Sovereign Credit Underwriting Standard</div>', unsafe_allow_html=True)
    render_html('<div class="bento-title">Investment Committee (IC) Deal Memo & Underwriting Stance</div>', unsafe_allow_html=True)

    if ic:
        col_ic1, col_ic2 = st.columns([1, 2])
        with col_ic1:
            verdict_colors = {
                "APPROVE WITH COVENANTS": "#10b981",
                "UNLEVERAGED M&A ACCRETION": "#38bdf8",
                "DELEVERAGING MANDATE": "#f59e0b",
                "RESTRICTED LEVERAGE": "#f43f5e",
            }
            v_color = verdict_colors.get(ic.underwriting_verdict, "#38bdf8")
            rating_display = (
                f"External Rating: <strong style='color:#ffffff;'>{ic.external_rating_symbol} ({ic.external_rating_agency})</strong>"
                if (ic.external_rating_symbol and ic.external_rating_agency)
                else f"Internal Screening Grade: <strong style='color:#ffffff;'>{ic.internal_screening_grade or 'UNRATED'}</strong>"
            )
            render_html(
                f"""
                <div class="bento-card" style="border:2px solid {v_color}; text-align:center;">
                    <div style="font-size:0.75rem; color:#94a3b8; text-transform:uppercase;">IC Underwriting Verdict</div>
                    <div style="font-size:1.6rem; font-weight:800; color:{v_color}; margin:8px 0; line-height:1.2;">
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
                """,
                unsafe_allow_html=True,
            )
        with col_ic2:
            render_html(
                f"""
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
                """,
                unsafe_allow_html=True,
            )

        render_html(
            f"""
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
            """,
            unsafe_allow_html=True,
        )

# ── TAB 11: MISSING DATA & DECISION LIMITATIONS ──
with tab_limitations:
    render_html('<div class="bento-subtitle">SEBI DRHP Information Gaps & Diligence Worklist</div>', unsafe_allow_html=True)
    render_html('<div class="bento-title">Decision Limitations & Unsupplied Disclosures Register</div>', unsafe_allow_html=True)
    
    lims = getattr(dossier, "limitations", [])
    if not lims:
        st.success("✅ Zero active decision limitations. All material data fields have been reconciled against audited disclosures.")
    else:
        c_lim1, c_lim2, c_lim3 = st.columns(3)
        high_gaps = len([l for l in lims if l.materiality_priority == "HIGH"])
        med_gaps = len([l for l in lims if l.materiality_priority == "MEDIUM"])
        with c_lim1:
            st.metric("Total Tracked Limitations", len(lims))
        with c_lim2:
            st.metric("High Materiality Blockers", high_gaps, delta="Underwriting Blocked" if high_gaps > 0 else "Clear", delta_color="inverse")
        with c_lim3:
            st.metric("Medium Diligence Gaps", med_gaps)

        lim_rows = []
        for l in lims:
            lim_rows.append({
                "Gap ID": l.gap_id,
                "Information Item": l.item_name,
                "Affected Dimension": l.affected_dimension,
                "Status": l.current_status,
                "Materiality": l.materiality_priority,
                "Blocked Decision": l.blocked_decision_or_recommendation,
                "Recommended Diligence Request": l.recommended_diligence_request,
            })
        st.dataframe(pd.DataFrame(lim_rows), use_container_width=True, hide_index=True)

        render_html(
            """
            <div class="narrative-card" style="margin-top:14px; border-left:4px solid #f59e0b;">
                <div style="font-size:0.80rem; font-weight:700; color:#f59e0b; text-transform:uppercase; margin-bottom:4px;">
                    📋 Diligence Action Protocol for Investment Committee & Lenders
                </div>
                <div style="font-size:0.86rem; color:#e2e8f0; line-height:1.5;">
                    Per institutional diligence standards (CFA V(A) and SEBI ICDR 2018), unsupplied or inconsistent prospectus items 
                    must not be filled with default assumptions or peer averages. The items flagged above require formal written requisition 
                    to the Book Running Lead Managers (BRLMs) or issuer management before final underwriting commitment.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

# ── TAB 12: ONLINE INGESTION DIAGNOSTIC ──
with tab_audit:
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
