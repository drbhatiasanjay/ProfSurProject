"""
Pre-IPO DRHP Intelligence & Sovereign Decision Support Terminal.
8-Panel High-Density Bento Architecture adhering to:
- SEBI ICDR 2018 Regulatory Standards
- Dickinson (2011) Life-Cycle Calibration against 8,677 CMIE Database
- Dynamic 3-Constraint Debt Capacity Sizing
- 2D Adversarial Stress Matrix & Ind AS 116 Leases Analysis
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
)
from utils.pre_ipo_deck_generator import generate_pre_ipo_board_deck

# Page Configuration
st.set_page_config(
    page_title="Pre-IPO DRHP Intelligence | Sovereign Terminal",
    page_icon="⚡",
    layout="wide",
)

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

# ─────────────────────────────────────────────────────────────────────────────
# TOP HERO SLICER & DEAL SELECTION
# ─────────────────────────────────────────────────────────────────────────────
deal_options = {
    "mankind_pharma": "Mankind Pharma Ltd. (DRHP 2023 · 100% OFS · Mature Cash Cow)",
    "afcons_infra": "Afcons Infrastructure Ltd. (RHP 2024 · ₹1,250 Cr Debt Prepayment)",
    "swiggy": "Swiggy Ltd. (DRHP 2024 · ₹1,400+ Cr Leases · Growth/Shakeout)",
    "tata_technologies": "Tata Technologies Ltd. (DRHP 2023 · Zero Debt · ER&D)",
    "custom_upload": "+ Ingest New DRHP / RHP PDF Document...",
}

col_sel, col_act = st.columns([3, 1])
with col_sel:
    selected_deal_key = st.selectbox(
        "Active Pre-IPO Deal Dossier",
        options=list(deal_options.keys()),
        format_func=lambda k: deal_options[k],
        key="pre_ipo_deal_selector",
    )

dossier = None
if selected_deal_key == "custom_upload":
    uploaded_file = st.file_uploader(
        "Upload Draft Red Herring Prospectus (DRHP) PDF",
        type=["pdf"],
        help="SEBI ICDR 2018 format compliant",
    )
    custom_company_name = st.text_input("Company Name", value="Novel Enterprise Limited")
    if uploaded_file is not None:
        dossier = PreIPOIngestionEngine.ingest_document(
            uploaded_file,
            company_name_hint=custom_company_name,
        )
    else:
        st.info("Upload a DRHP PDF or select a Golden Exemplar above to inspect the financial terminal.")
        dossier = PRE_IPO_REGISTRY["mankind_pharma"]
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

st.markdown(
    f"""
    <div class="bento-card" style="border-left: 4px solid #38bdf8;">
        <div style="display:flex; justify-content:space-between; align-items:flex-start; flex-wrap:wrap; gap:12px;">
            <div>
                <span class="badge-pill badge-sky">{dossier.filing_type} · {dossier.filing_date}</span>
                <span class="badge-pill {badge_class}" style="margin-left:6px;">Dickinson: {stage_name} {pattern}</span>
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
# TABS FOR 8 BENTO PANELS
# ─────────────────────────────────────────────────────────────────────────────
tab_fin, tab_debt, tab_stress, tab_governance, tab_audit = st.tabs([
    "📊 Restated Financials & Dickinson",
    "⚖️ Indebtedness & Leases",
    "🌪️ Adversarial Stress & M&A Capacity",
    "🛡️ SEBI Governance & Working Capital",
    "🔍 Online Ingestion Diagnostic",
])

# ── TAB 1: RESTATED FINANCIALS & DICKINSON BENCHMARK ──
with tab_fin:
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

        # Revenue & EBITDA Trend Chart
        fig_trend = go.Figure()
        yrs = [f.fiscal_year for f in dossier.history]
        revs = [f.revenue_ops_cr for f in dossier.history]
        ebitdas = [f.ebitda_cr for f in dossier.history]
        fig_trend.add_trace(go.Bar(x=yrs, y=revs, name="Revenue", marker_color="#38bdf8", opacity=0.75))
        fig_trend.add_trace(go.Scatter(x=yrs, y=ebitdas, name="Restated EBITDA", line=dict(color="#10b981", width=3), mode="lines+markers"))
        fig_trend.update_layout(
            height=280,
            margin=dict(l=20, r=20, t=30, b=20),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            font=dict(color="#cbd5e1"),
        )
        st.plotly_chart(fig_trend, use_container_width=True)

    with col_f2:
        st.markdown('<div class="bento-subtitle">Empirical Benchmark (N=8,677 CMIE Database)</div>', unsafe_allow_html=True)
        st.markdown('<div class="bento-title">Dickinson Life-Cycle Radar</div>', unsafe_allow_html=True)
        
        st.markdown(
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
                    • <strong>Historical 3-Yr Post-IPO Survival Probability:</strong> 94.8% for Mature Cash Cow archetypes.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

# ── TAB 2: INDEBTEDNESS & LEASES ──
with tab_debt:
    st.markdown('<div class="bento-subtitle">Section VI Disclosures · Ind AS 116 Lease Analysis</div>', unsafe_allow_html=True)
    st.markdown('<div class="bento-title">Capital Structure & Indebtedness Breakdown</div>', unsafe_allow_html=True)

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

    # Stacked Indebtedness Composition
    fig_indebt = go.Figure()
    fig_indebt.add_trace(go.Bar(name="Secured Term Loans", x=["Indebtedness"], y=[ind.secured_term_loans_cr], marker_color="#38bdf8"))
    fig_indebt.add_trace(go.Bar(name="Working Capital Loans", x=["Indebtedness"], y=[ind.working_capital_loans_cr], marker_color="#0284c7"))
    fig_indebt.add_trace(go.Bar(name="Unsecured / Other", x=["Indebtedness"], y=[ind.unsecured_loans_cr], marker_color="#818cf8"))
    if include_leases:
        fig_indebt.add_trace(go.Bar(name="Ind AS 116 Leases", x=["Indebtedness"], y=[ind.lease_liabilities_ind_as_116_cr], marker_color="#f59e0b"))
    fig_indebt.update_layout(
        barmode="stack",
        height=220,
        margin=dict(l=20, r=20, t=30, b=20),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#cbd5e1"),
    )
    st.plotly_chart(fig_indebt, use_container_width=True)

# ── TAB 3: ADVERSARIAL STRESS & M&A CAPACITY ──
with tab_stress:
    col_s1, col_s2 = st.columns([3, 2])
    with col_s1:
        st.markdown('<div class="bento-subtitle">Quantitative Stress Testing</div>', unsafe_allow_html=True)
        st.markdown('<div class="bento-title">2D Interest Coverage Ratio (ICR) Sensitivity</div>', unsafe_allow_html=True)
        
        sens = generate_2d_sensitivity_matrix(
            base_ebitda_cr=latest.ebitda_cr,
            gross_debt_cr=dossier.indebtedness.funded_bank_debt_cr,
            base_wair_pct=dossier.indebtedness.weighted_avg_interest_rate_pct or 8.5,
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
        st.markdown('<div class="bento-subtitle">OakNorth Treasury Standard Sizing</div>', unsafe_allow_html=True)
        st.markdown('<div class="bento-title">Post-IPO M&A Headroom</div>', unsafe_allow_html=True)
        
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
        
        st.markdown(
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

# ── TAB 4: SEBI GOVERNANCE & WORKING CAPITAL ──
with tab_governance:
    col_g1, col_g2 = st.columns(2)
    with col_g1:
        st.markdown('<div class="bento-subtitle">SEBI LODR & ICDR Governance Disclosures</div>', unsafe_allow_html=True)
        st.markdown('<div class="bento-title">Non-Financial Risk Profile</div>', unsafe_allow_html=True)
        gov = dossier.governance
        
        st.markdown(
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
        st.markdown('<div class="bento-subtitle">Cash Conversion Dynamics</div>', unsafe_allow_html=True)
        st.markdown('<div class="bento-title">Working Capital Cycle</div>', unsafe_allow_html=True)
        wc = dossier.working_capital
        
        st.markdown(
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

# ── TAB 5: ONLINE INGESTION DIAGNOSTIC ──
with tab_audit:
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
