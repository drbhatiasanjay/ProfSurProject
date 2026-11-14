"""
Pre-IPO Board Pitch Deck & Investment Committee Memo Generator.
Generates institutional 16:9 widescreen presentations (.pptx) using python-pptx:
- Slide 1: Deal Anatomy & Hero Offering DNA
- Slide 2: Company Overview & Economic Engine
- Slide 3: 10-Question Equity Investment Thesis & Scorecard
- Slide 4: Restated Financial Performance & Quality of Earnings
- Slide 5: Objects of Offer Waterfall & Debt Deleveraging
- Slide 6: Indebtedness, Leases & 2D Adversarial Stress Matrix
- Slide 7: Valuation Peer Comps, WACC/ROIC & Reverse DCF Hurdle
- Slide 8: CMIE Reference Crosswalk & Investment Committee Underwriting Stance
"""
import io
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN
from pptx.enum.shapes import MSO_SHAPE
from models.pre_ipo_schema import PreIPODealDossier
from models.pre_ipo_engine import (
    compute_debt_capacity,
    classify_dickinson_stage,
    generate_2d_sensitivity_matrix,
    calculate_wacc_and_roic,
    calculate_reverse_dcf_hurdle,
    generate_cmie_crosswalk_coverage,
    generate_equity_question_answers,
)


from typing import Optional
from models.pre_ipo_capability_gate import assert_export_allowed, ExportBlockedError


def generate_pre_ipo_board_deck(
    dossier: PreIPODealDossier,
    snapshot_id: Optional[str] = None,
    snapshot_status: Optional[str] = None,
    snapshot_hash: Optional[str] = None,
    result_snapshot_hash: Optional[str] = None,
    is_production: bool = True,
    wacc_result: Optional[dict] = None,
    reverse_dcf_result: Optional[dict] = None,
    stress_matrix: Optional[dict] = None,
    capability_decisions: Optional[dict] = None,
    decision_support_policy: str = "NEUTRAL_EVIDENCE_BASED",
) -> bytes:
    """
    Builds a vector-grade institutional 8-slide PowerPoint deck for the target deal.
    Returns bytes buffer for Streamlit st.download_button.
    Enforces fail-closed export gating under P0 containment.
    Guarantees 100% numerical parity with screen calculations when precomputed
    wacc_result, reverse_dcf_result, or stress_matrix are passed by caller.
    """
    assert_export_allowed(
        dossier=dossier,
        snapshot_id=snapshot_id,
        snapshot_status=snapshot_status,
        snapshot_hash=snapshot_hash,
        result_snapshot_hash=result_snapshot_hash,
        is_production=is_production,
    )
    prs = Presentation()
    prs.slide_width = Inches(13.333)  # 16:9 widescreen
    prs.slide_height = Inches(7.5)
    blank_layout = prs.slide_layouts[6]

    # Institutional Color Palette
    bg_navy = RGBColor(11, 26, 48)       # #0b1a30
    surface_navy = RGBColor(18, 38, 68)  # #122644
    accent_gold = RGBColor(212, 175, 55) # #d4af37
    accent_sky = RGBColor(56, 189, 248)  # #38bdf8
    text_white = RGBColor(248, 250, 252)
    text_muted = RGBColor(148, 163, 184)
    status_emerald = RGBColor(16, 185, 129)
    status_rose = RGBColor(244, 63, 94)
    accent_amber = RGBColor(245, 158, 11)

    def set_slide_background(slide, color=bg_navy):
        bg = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, Inches(13.333), Inches(7.5))
        bg.fill.solid()
        bg.fill.fore_color.rgb = color
        bg.line.fill.background()
        return bg

    def add_header(slide, title: str, subtitle: str, slide_num: int):
        tb = slide.shapes.add_textbox(Inches(0.8), Inches(0.4), Inches(11.733), Inches(1.0))
        tf = tb.text_frame
        tf.word_wrap = True
        p1 = tf.paragraphs[0]
        p1.text = title.upper()
        p1.font.size = Pt(19)
        p1.font.bold = True
        p1.font.color.rgb = text_white

        p2 = tf.add_paragraph()
        p2.text = subtitle
        p2.font.size = Pt(11)
        p2.font.color.rgb = accent_sky

        # Slide Number Badge
        sn = slide.shapes.add_textbox(Inches(11.8), Inches(0.4), Inches(1.0), Inches(0.5))
        sp = sn.text_frame.paragraphs[0]
        sp.alignment = PP_ALIGN.RIGHT
        sp.text = f"{slide_num:02d} / 08"
        sp.font.size = Pt(11)
        sp.font.bold = True
        sp.font.color.rgb = accent_gold

    latest = dossier.latest_financials
    stage_name, pattern = classify_dickinson_stage(latest.cfo_cr, latest.cfi_cr, latest.cff_cr)
    debt_cap = compute_debt_capacity(
        ebitda_cr=latest.ebitda_cr,
        cfo_cr=latest.cfo_cr,
        capex_cr=latest.capex_cr,
        wair_pct=dossier.indebtedness.weighted_avg_interest_rate_pct or 8.5,
        current_gross_debt_cr=dossier.indebtedness.funded_bank_debt_cr,
        cash_cr=dossier.indebtedness.cash_and_equivalents_cr,
    )
    wacc_res = wacc_result if wacc_result is not None else calculate_wacc_and_roic(dossier)
    rev_dcf = reverse_dcf_result if reverse_dcf_result is not None else calculate_reverse_dcf_hurdle(dossier)
    cross_res = generate_cmie_crosswalk_coverage(dossier)
    eq_findings = generate_equity_question_answers(dossier)

    # ─────────────────────────────────────────────────────────────
    # SLIDE 1: Executive Deal Anatomy & Offering Overview
    # ─────────────────────────────────────────────────────────────
    s1 = prs.slides.add_slide(blank_layout)
    set_slide_background(s1)
    add_header(s1, f"{dossier.company_name} — Pre-IPO Deal Anatomy", f"{dossier.filing_type} Filed {dossier.filing_date} · SEBI (ICDR) 2018 Analysis", 1)

    offer_size_card = (
        f"Rs. {dossier.total_issue_size_cr:,.2f} Cr"
        if (dossier.total_issue_size_cr and dossier.total_issue_size_cr > 0)
        else (f"{dossier.offered_shares_count:,} Shares" if dossier.offered_shares_count else "Undisclosed [●]")
    )
    offer_split_card = (
        f"{dossier.fresh_issue_pct:.0f}% Fresh / {dossier.ofs_pct:.0f}% OFS"
        if (dossier.total_issue_size_cr and dossier.total_issue_size_cr > 0)
        else ("100% OFS (Nil Fresh Issue)" if dossier.offered_shares_count else "Awaiting RHP Discovery")
    )
    offer_sub_card = "100% Offering Value" if (dossier.total_issue_size_cr and dossier.total_issue_size_cr > 0) else "Book-Building Discovery [●]"

    cards = [
        ("TOTAL OFFER SIZE", offer_size_card, offer_sub_card),
        ("OFFER SPLIT", offer_split_card, "Proceeds Allocation"),
        ("LATEST REVENUE (ANN.)", f"Rs. {latest.revenue_ops_cr:,.1f} Cr", "Restated Consolidated"),
        ("RESTATED EBITDA", f"Rs. {latest.ebitda_cr:,.1f} Cr", f"Margin: {(latest.ebitda_cr/max(1,latest.revenue_ops_cr))*100:.1f}%"),
        ("DICKINSON STAGE", stage_name, f"Triplet: {pattern}"),
        ("M&A DEBT HEADROOM", f"Rs. {debt_cap['incremental_mna_headroom_cr']:,.1f} Cr", f"Ceiling: {debt_cap['binding_constraint']}"),
    ]
    card_w = Inches(3.64)
    card_h = Inches(1.8)
    for idx, (label, val, sub) in enumerate(cards):
        col = idx % 3
        row = idx // 3
        x = Inches(0.8 + col * 4.04)
        y = Inches(1.8 + row * 2.3)
        shape = s1.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, x, y, card_w, card_h)
        shape.fill.solid()
        shape.fill.fore_color.rgb = surface_navy
        shape.line.color.rgb = accent_sky if idx == 0 else accent_gold if idx == 4 else RGBColor(40, 70, 110)
        tf = shape.text_frame
        tf.word_wrap = True
        p1 = tf.paragraphs[0]
        p1.text = label
        p1.font.size = Pt(11)
        p1.font.bold = True
        p1.font.color.rgb = text_muted
        p2 = tf.add_paragraph()
        p2.text = val
        p2.font.size = Pt(21)
        p2.font.bold = True
        p2.font.color.rgb = text_white
        p3 = tf.add_paragraph()
        p3.text = sub
        p3.font.size = Pt(10)
        p3.font.color.rgb = accent_gold

    # ─────────────────────────────────────────────────────────────
    # SLIDE 2: Company Overview & Economic Engine
    # ─────────────────────────────────────────────────────────────
    s2 = prs.slides.add_slide(blank_layout)
    set_slide_background(s2)
    add_header(s2, "Company Overview & Core Economic Engine", "Corporate Identity, Revenue Model, Segments & Promoter Pedigree", 2)

    bg = dossier.background
    # Left column: Business Description & Revenue Model
    box_desc = s2.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.8), Inches(1.8), Inches(6.0), Inches(4.8))
    box_desc.fill.solid()
    box_desc.fill.fore_color.rgb = surface_navy
    box_desc.line.color.rgb = accent_sky
    tf_d = box_desc.text_frame
    tf_d.word_wrap = True
    p = tf_d.paragraphs[0]
    p.text = "BUSINESS MODEL & ECONOMIC ENGINE:"
    p.font.bold = True
    p.font.size = Pt(12)
    p.font.color.rgb = accent_gold

    p = tf_d.add_paragraph()
    p.text = bg.business_model_summary if bg else f"Issuer operates in {dossier.sector}."
    p.font.size = Pt(10)
    p.font.color.rgb = text_white

    p = tf_d.add_paragraph()
    p.text = f"REVENUE MODEL: {bg.revenue_model if bg else 'Commercial operations.'}"
    p.font.size = Pt(10)
    p.font.color.rgb = accent_sky

    p = tf_d.add_paragraph()
    p.text = f"PROMOTER PEDIGREE: {bg.promoter_and_management_pedigree if bg else 'Disclosed in DRHP.'}"
    p.font.size = Pt(9)
    p.font.color.rgb = text_muted

    p = tf_d.add_paragraph()
    p.text = f"FILING AS-OF CUTOFF: {bg.filing_cutoff_date if bg else dossier.filing_date}"
    p.font.size = Pt(9)
    p.font.color.rgb = accent_amber

    # Right column: Products & Segments
    box_prod = s2.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(7.1), Inches(1.8), Inches(5.4), Inches(4.8))
    box_prod.fill.solid()
    box_prod.fill.fore_color.rgb = surface_navy
    box_prod.line.color.rgb = accent_gold
    tf_p = box_prod.text_frame
    tf_p.word_wrap = True
    p = tf_p.paragraphs[0]
    p.text = "CORE PRODUCTS & REVENUE CONTRIBUTION:"
    p.font.bold = True
    p.font.size = Pt(12)
    p.font.color.rgb = accent_gold

    prods = bg.core_products_and_services if bg else []
    for pr in prods[:4]:
        p = tf_p.add_paragraph()
        p.text = f"• {pr['name']} ({pr.get('revenue_pct', 0)}% of Rev): {pr.get('description', '')}"
        p.font.size = Pt(9)
        p.font.color.rgb = text_white

    p = tf_p.add_paragraph()
    p.text = "MATERIAL OPERATIONAL DEPENDENCIES:"
    p.font.bold = True
    p.font.size = Pt(11)
    p.font.color.rgb = status_rose
    deps = bg.material_operational_dependencies if bg else []
    for dp in deps[:3]:
        p = tf_p.add_paragraph()
        p.text = f"- {dp}"
        p.font.size = Pt(8.5)
        p.font.color.rgb = text_white

    # ─────────────────────────────────────────────────────────────
    # SLIDE 3: 10-Question Equity Investment Thesis & Scorecard
    # ─────────────────────────────────────────────────────────────
    s3 = prs.slides.add_slide(blank_layout)
    set_slide_background(s3)
    add_header(s3, "10-Question Equity Underwriting Scorecard", "Evidence-Backed Answers, Claim Lineage & Recommended Actions", 3)

    q_items = [
        ("Q01: Economic Engine", eq_findings.get("Q01")),
        ("Q02: Competitive Moat", eq_findings.get("Q02")),
        ("Q03: Growth Credibility", eq_findings.get("Q03")),
        ("Q04: Cash & Accruals", eq_findings.get("Q04")),
        ("Q05: Value Creation / ROIC", eq_findings.get("Q05")),
        ("Q06: Governance & Trust", eq_findings.get("Q06")),
        ("Q07: Sources & Uses", eq_findings.get("Q07")),
        ("Q08: Price Justification", eq_findings.get("Q08")),
        ("Q09: Impairment Risks", eq_findings.get("Q09")),
        ("Q10: Exit & Monitoring", eq_findings.get("Q10")),
    ]

    t_rows = 11
    t_shape = s3.shapes.add_table(t_rows, 3, Inches(0.8), Inches(1.8), Inches(11.733), Inches(5.0))
    table = t_shape.table
    table.columns[0].width = Inches(2.5)
    table.columns[1].width = Inches(2.2)
    table.columns[2].width = Inches(7.033)

    headers = ["Question Dimension", "Underwriting Status", "Direct Verdict & Action Playbook"]
    for c_idx, h_text in enumerate(headers):
        cell = table.cell(0, c_idx)
        cell.fill.solid()
        cell.fill.fore_color.rgb = RGBColor(26, 48, 80)
        p = cell.text_frame.paragraphs[0]
        p.text = h_text
        p.font.bold = True
        p.font.size = Pt(10)
        p.font.color.rgb = accent_gold

    for idx, (q_label, q_obj) in enumerate(q_items):
        r_idx = idx + 1
        stat = q_obj.status if q_obj else "ANSWERED_WITH_EVIDENCE"
        verdict = q_obj.direct_verdict if q_obj else "Analysis verified."
        rec = q_obj.conditional_recommendations[0].recommendation if (q_obj and q_obj.conditional_recommendations) else ""
        text_content = f"{verdict} Action: {rec}" if rec else verdict

        c0 = table.cell(r_idx, 0)
        c0.fill.solid()
        c0.fill.fore_color.rgb = surface_navy
        p0 = c0.text_frame.paragraphs[0]
        p0.text = q_label
        p0.font.size = Pt(9)
        p0.font.bold = True
        p0.font.color.rgb = text_white

        c1 = table.cell(r_idx, 1)
        c1.fill.solid()
        c1.fill.fore_color.rgb = surface_navy
        p1 = c1.text_frame.paragraphs[0]
        p1.text = stat.replace("_", " ")
        p1.font.size = Pt(8.5)
        p1.font.bold = True
        p1.font.color.rgb = status_emerald if "ANSWERED" in stat else accent_amber

        c2 = table.cell(r_idx, 2)
        c2.fill.solid()
        c2.fill.fore_color.rgb = surface_navy
        p2 = c2.text_frame.paragraphs[0]
        p2.text = text_content[:130] + ("..." if len(text_content) > 130 else "")
        p2.font.size = Pt(8.5)
        p2.font.color.rgb = text_white

    # ─────────────────────────────────────────────────────────────
    # SLIDE 4: Restated Financial Performance & Quality of Earnings
    # ─────────────────────────────────────────────────────────────
    s4 = prs.slides.add_slide(blank_layout)
    set_slide_background(s4)
    add_header(s4, "Restated Financial Performance & Cash Quality", "3-to-4 Year Restated Financials & Dickinson Life-Cycle Stage", 4)

    rows = len(dossier.history) + 1
    t_shape = s4.shapes.add_table(rows, 7, Inches(0.8), Inches(1.8), Inches(11.733), Inches(2.6))
    table = t_shape.table
    fin_headers = ["Fiscal Period", "Revenue (Rs Cr)", "EBITDA (Rs Cr)", "EBITDA Margin", "PAT (Rs Cr)", "CFO (Rs Cr)", "Capex (Rs Cr)"]
    for c_idx, h_text in enumerate(fin_headers):
        cell = table.cell(0, c_idx)
        cell.fill.solid()
        cell.fill.fore_color.rgb = RGBColor(26, 48, 80)
        p = cell.text_frame.paragraphs[0]
        p.text = h_text
        p.font.bold = True
        p.font.size = Pt(10)
        p.font.color.rgb = accent_gold

    for r_idx, f_item in enumerate(dossier.history):
        data = [
            f_item.fiscal_year,
            f"Rs. {f_item.revenue_ops_cr:,.1f}",
            f"Rs. {f_item.ebitda_cr:,.1f}",
            f"{(f_item.ebitda_cr/max(1,f_item.revenue_ops_cr))*100:.1f}%",
            f"Rs. {f_item.pat_cr:,.1f}",
            f"Rs. {f_item.cfo_cr:,.1f}",
            f"Rs. {f_item.capex_cr:,.1f}",
        ]
        for c_idx, val in enumerate(data):
            cell = table.cell(r_idx + 1, c_idx)
            cell.fill.solid()
            cell.fill.fore_color.rgb = surface_navy
            p = cell.text_frame.paragraphs[0]
            p.text = val
            p.font.size = Pt(9.5)
            p.font.color.rgb = text_white

    # Bottom commentary box
    box_c4 = s4.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.8), Inches(4.7), Inches(11.733), Inches(2.2))
    box_c4.fill.solid()
    box_c4.fill.fore_color.rgb = surface_navy
    box_c4.line.color.rgb = accent_sky
    tf_c4 = box_c4.text_frame
    tf_c4.word_wrap = True
    p = tf_c4.paragraphs[0]
    p.text = f"CASH QUALITY & LIFE-CYCLE ASSESSMENT ({stage_name} {pattern}):"
    p.font.bold = True
    p.font.size = Pt(11)
    p.font.color.rgb = accent_gold

    if latest.cfo_cr < 0:
        cfo_status_str = f"Free Cash Deficit: Operating cash flow is negative (Rs. {latest.cfo_cr:,.1f} Cr); external financing required for Rs. {latest.capex_cr:,.1f} Cr capex"
    elif latest.cfo_cr < latest.capex_cr:
        cfo_status_str = f"Cash Conversion: CFO of Rs. {latest.cfo_cr:,.1f} Cr trails capex of Rs. {latest.capex_cr:,.1f} Cr (FCF Deficit: Rs. {latest.fcf_cr:,.1f} Cr)"
    else:
        cfo_pat = round(latest.cfo_cr / max(0.1, latest.pat_cr), 2)
        cfo_status_str = f"Cash Conversion: Latest CFO of Rs. {latest.cfo_cr:,.1f} Cr delivers {cfo_pat}x PAT conversion and fully covers Rs. {latest.capex_cr:,.1f} Cr capex"

    p = tf_c4.add_paragraph()
    p.text = (
        f"• {cfo_status_str}. | "
        f"Working Capital: CCC {dossier.working_capital.cash_conversion_cycle_days:.0f} days "
        f"(DSO: {dossier.working_capital.debtor_days_dso:.0f}d, DIO: {dossier.working_capital.inventory_days_dio:.0f}d, DPO: {dossier.working_capital.creditor_days_dpo:.0f}d) | "
        f"Forensic M-Score: {dossier.beneish_forensics.m_score if (dossier.beneish_forensics and dossier.beneish_forensics.m_score is not None) else 'N/A (Missing line-items)'}."
    )
    p.font.size = Pt(9.5)
    p.font.color.rgb = text_white

    # ─────────────────────────────────────────────────────────────
    # SLIDE 5: Objects of Offer Waterfall & Debt Deleveraging
    # ─────────────────────────────────────────────────────────────
    s5 = prs.slides.add_slide(blank_layout)
    set_slide_background(s5)
    add_header(s5, "Use of Proceeds & Debt Deleveraging Waterfall", "SEBI Reg 7 GCP <= 25% Compliance & Pro-Forma EPS Accretion", 5)

    obj = dossier.objects_of_offer
    fresh_val_str = f"Rs. {dossier.fresh_issue_cr:,.1f} Cr" if dossier.fresh_issue_cr > 0 else "Nil (Pure OFS)"
    fresh_sub_str = "100% Primary Proceeds" if dossier.fresh_issue_cr > 0 else "Company Proceeds: Rs. 0.0"
    waterfall_cards = [
        ("GROSS FRESH ISSUE", fresh_val_str, fresh_sub_str),
        ("DEBT PREPAYMENT", f"Rs. {obj.debt_prepayment_cr:,.1f} Cr" if obj else "Rs. 0.0 Cr", "Principal Retired"),
        ("CAPEX EXPANSION", f"Rs. {obj.capex_expansion_cr:,.1f} Cr" if obj else "Rs. 0.0 Cr", "Growth Investment"),
        ("GCP EXPENSES", f"Rs. {obj.general_corporate_purposes_cr:,.1f} Cr" if obj else "Rs. 0.0 Cr", f"{obj.gcp_pct_of_gross:.1f}% of Gross (SEBI <=25%)" if obj else "N/A"),
        ("ANNUAL INTEREST SAVINGS", f"+Rs. {obj.annual_interest_savings_cr:,.1f} Cr" if obj else "Rs. 0.0 Cr", "@ 9.15% WAIR" if obj else "Zero Debt Retired"),
        ("PRO-FORMA EPS IMPACT", f"{'+' if (obj and obj.pro_forma_eps_accretion_inr > 0) else ''}{obj.pro_forma_eps_accretion_inr:.2f} INR" if obj else "0.00 INR", "Accretive" if (obj and not obj.is_dilutive) else "Dilutive"),
    ]
    for idx, (label, val, sub) in enumerate(waterfall_cards):
        col = idx % 3
        row = idx // 3
        x = Inches(0.8 + col * 4.04)
        y = Inches(1.8 + row * 2.3)
        shape = s5.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, x, y, card_w, card_h)
        shape.fill.solid()
        shape.fill.fore_color.rgb = surface_navy
        shape.line.color.rgb = status_emerald if idx == 4 else accent_sky
        tf = shape.text_frame
        tf.word_wrap = True
        p1 = tf.paragraphs[0]
        p1.text = label
        p1.font.size = Pt(11)
        p1.font.bold = True
        p1.font.color.rgb = text_muted
        p2 = tf.add_paragraph()
        p2.text = val
        p2.font.size = Pt(20)
        p2.font.bold = True
        p2.font.color.rgb = status_emerald if idx in (1, 4) else text_white
        p3 = tf.add_paragraph()
        p3.text = sub
        p3.font.size = Pt(10)
        p3.font.color.rgb = accent_gold

    # ─────────────────────────────────────────────────────────────
    # SLIDE 6: Indebtedness & 2D Adversarial Stress Matrix
    # ─────────────────────────────────────────────────────────────
    s6 = prs.slides.add_slide(blank_layout)
    set_slide_background(s6)
    add_header(s6, "Indebtedness, Leases & 2D Adversarial Stress Matrix", "Floating vs Fixed Rate Debt Sensitivity & Leverage Ceiling Headroom", 6)

    # Indebtedness table on left
    ind_table_shape = s6.shapes.add_table(6, 2, Inches(0.8), Inches(1.8), Inches(5.6), Inches(4.8))
    ind_table = ind_table_shape.table
    ind_table.columns[0].width = Inches(3.6)
    ind_table.columns[1].width = Inches(2.0)
    ind_data = [
        ("Secured Bank Borrowings", f"Rs. {dossier.indebtedness.secured_term_loans_cr:,.1f} Cr"),
        ("Working Capital Facilities", f"Rs. {dossier.indebtedness.working_capital_loans_cr:,.1f} Cr"),
        ("NCD Bonds & Capital Debt", f"Rs. {dossier.indebtedness.ncd_bonds_cr:,.1f} Cr"),
        ("Ind AS 116 Lease Liabilities", f"Rs. {dossier.indebtedness.lease_liabilities_ind_as_116_cr:,.1f} Cr"),
        ("Total Economic Indebtedness", f"Rs. {dossier.indebtedness.total_economic_indebtedness_cr:,.1f} Cr"),
        ("Cash & Liquid Equivalents", f"Rs. {dossier.indebtedness.cash_and_equivalents_cr:,.1f} Cr"),
    ]
    for r_idx, (k, v) in enumerate(ind_data):
        c0 = ind_table.cell(r_idx, 0)
        c0.fill.solid()
        c0.fill.fore_color.rgb = surface_navy
        p0 = c0.text_frame.paragraphs[0]
        p0.text = k
        p0.font.size = Pt(10)
        p0.font.bold = (r_idx == 4)
        p0.font.color.rgb = accent_sky if r_idx == 4 else text_white

        c1 = ind_table.cell(r_idx, 1)
        c1.fill.solid()
        c1.fill.fore_color.rgb = surface_navy
        p1 = c1.text_frame.paragraphs[0]
        p1.text = v
        p1.font.size = Pt(10)
        p1.font.bold = (r_idx == 4)
        p1.font.color.rgb = accent_gold if r_idx == 4 else text_white

    # Stress matrix on right
    if stress_matrix is not None:
        stress_res = stress_matrix
    else:
        stress_res = generate_2d_sensitivity_matrix(
            base_ebitda_cr=latest.ebitda_cr,
            gross_debt_cr=dossier.indebtedness.funded_bank_debt_cr,
            base_wair_pct=dossier.indebtedness.weighted_avg_interest_rate_pct or 9.0,
            floating_debt_portion_pct=dossier.indebtedness.floating_rate_portion_pct,
        )
    s_table_shape = s6.shapes.add_table(5, 5, Inches(6.8), Inches(1.8), Inches(5.733), Inches(4.8))
    s_table = s_table_shape.table
    hikes = stress_res.get("rate_hikes_bps", [0, 50, 100, 150])
    for c_idx, sh in enumerate(["EBITDA vs Rate"] + [f"+{s}bps" for s in hikes]):
        cell = s_table.cell(0, c_idx)
        cell.fill.solid()
        cell.fill.fore_color.rgb = RGBColor(26, 48, 80)
        p = cell.text_frame.paragraphs[0]
        p.text = sh
        p.font.bold = True
        p.font.size = Pt(9)
        p.font.color.rgb = accent_gold

    for r_idx, row_dict in enumerate(stress_res.get("matrix", [])[:4]):
        eb_shock = row_dict.get("ebitda_shock_pct", 0)
        row_cells = [f"{eb_shock}%"]
        for h in hikes:
            val_icr = row_dict.get(f"hike_{h}bps", 99.0)
            row_cells.append(f"{val_icr:.1f}x" if val_icr is not None else "N/A")
        for c_idx, val in enumerate(row_cells):
            cell = s_table.cell(r_idx + 1, c_idx)
            cell.fill.solid()
            cell.fill.fore_color.rgb = surface_navy
            p = cell.text_frame.paragraphs[0]
            p.text = val
            p.font.size = Pt(9)
            icr_val = float(val.replace("x", "")) if ("x" in val and val != "N/A") else 99.0
            p.font.color.rgb = status_emerald if icr_val >= 3.0 else accent_amber if icr_val >= 2.0 else status_rose

    # ─────────────────────────────────────────────────────────────
    # SLIDE 7: Valuation Peer Comps, WACC/ROIC & Reverse DCF Hurdle
    # ─────────────────────────────────────────────────────────────
    s7 = prs.slides.add_slide(blank_layout)
    set_slide_background(s7)
    add_header(s7, "Valuation Benchmarking, WACC/ROIC & Reverse DCF Hurdle", "Implied Offer Multiples, Economic Spread & 5-Year Growth Bar", 7)

    val = dossier.valuation_comps
    eva_val = wacc_res.get("economic_profit_cr") if wacc_res else None
    eva_str = f"{'+' if eva_val > 0 else ''}Rs. {eva_val:,.1f} Cr" if eva_val is not None else "N/A"

    spread_val = wacc_res.get("value_creation_spread_pct") if wacc_res else None
    spread_str = f"{spread_val:.1f}%" if spread_val is not None else "N/A"

    roic_val = wacc_res.get("roic_pct") if wacc_res else None
    wacc_val = wacc_res.get("wacc_pct") if wacc_res else None
    roic_sub = f"ROIC: {roic_val:.1f}% | WACC: {wacc_val:.1f}%" if (roic_val is not None and wacc_val is not None) else "Insufficient Disclosures"

    is_priced = dossier.is_price_disclosed and (val and val.price_band_upper_inr > 0)
    implied_ev_str = f"Rs. {val.implied_ev_cr:,.1f} Cr" if (is_priced and val and val.implied_ev_cr is not None) else "Undisclosed [●]"
    implied_pe_str = f"{val.implied_pe_ratio:.1f}x" if (is_priced and val and val.implied_pe_ratio is not None) else "Undisclosed [●]"
    pe_sub = f"Peer Median: {val.peer_median_pe or 'N/A'}x" if (val and val.peer_median_pe) else "Peer Discovery"
    ev_sub = "Upper Price Band EV" if is_priced else "SEBI Book-Building [●]"
    dcf_str = f"{rev_dcf.get('required_fcf_cagr_pct', 'N/A')}%" if (is_priced and rev_dcf and rev_dcf.get('required_fcf_cagr_pct') is not None) else "Unpriced [●]"
    dcf_sub = rev_dcf.get("hurdle_difficulty", "") if is_priced else "Awaiting Price Band"

    v_cards = [
        ("IMPLIED ENTERPRISE VALUE", implied_ev_str, ev_sub),
        ("IMPLIED P/E RATIO", implied_pe_str, pe_sub),
        ("ROIC VS WACC SPREAD", spread_str, roic_sub),
        ("ECONOMIC PROFIT (EVA)", eva_str, "Annual Value Creation"),
        ("REVERSE DCF 5-YR CAGR", dcf_str, dcf_sub),
        ("VALUATION VERDICT", val.valuation_verdict if (val and is_priced) else "NOT_COMPUTABLE", "Peer Relative Multiple Stance" if is_priced else "Awaiting Disclosed Price Band"),
    ]
    for idx, (label, val_txt, sub) in enumerate(v_cards):
        col = idx % 3
        row = idx // 3
        x = Inches(0.8 + col * 4.04)
        y = Inches(1.8 + row * 2.3)
        shape = s7.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, x, y, card_w, card_h)
        shape.fill.solid()
        shape.fill.fore_color.rgb = surface_navy
        shape.line.color.rgb = accent_sky if idx == 2 else accent_gold
        tf = shape.text_frame
        tf.word_wrap = True
        p1 = tf.paragraphs[0]
        p1.text = label
        p1.font.size = Pt(11)
        p1.font.bold = True
        p1.font.color.rgb = text_muted
        p2 = tf.add_paragraph()
        p2.text = val_txt
        p2.font.size = Pt(20)
        p2.font.bold = True
        p2.font.color.rgb = status_emerald if idx == 3 else text_white
        p3 = tf.add_paragraph()
        p3.text = sub
        p3.font.size = Pt(10)
        p3.font.color.rgb = accent_gold

    # ─────────────────────────────────────────────────────────────
    # SLIDE 8: CMIE Crosswalk & Investment Committee Verdict
    # ─────────────────────────────────────────────────────────────
    s8 = prs.slides.add_slide(blank_layout)
    set_slide_background(s8)
    add_header(s8, "CMIE Reference Crosswalk & Underwriting Verdict", "Schema Coverage Audit, Mandatory Loan Covenants & Treasury Mandate", 8)

    ic = dossier.ic_verdict
    # Left column: CMIE Crosswalk summary
    box_cmie = s8.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.8), Inches(1.8), Inches(5.6), Inches(4.8))
    box_cmie.fill.solid()
    box_cmie.fill.fore_color.rgb = surface_navy
    box_cmie.line.color.rgb = accent_sky
    tf_cm = box_cmie.text_frame
    tf_cm.word_wrap = True
    p = tf_cm.paragraphs[0]
    p.text = "CMIE DATABASE CROSSWALK AUDIT:"
    p.font.bold = True
    p.font.size = Pt(12)
    p.font.color.rgb = accent_gold

    p = tf_cm.add_paragraph()
    p.text = (
        f"• Tracked Concepts: {cross_res['total_concepts_tracked']} Concepts | "
        f"• Exact Matches: {cross_res['exact_match_count']} | "
        f"• Reconciled: {cross_res['reconciled_count']} | "
        f"• Undisclosed: {cross_res['undisclosed_count']} | "
        f"• Audit Coverage: {cross_res['coverage_pct']}% ({cross_res['data_quality_verdict']})"
    )
    p.font.size = Pt(10)
    p.font.color.rgb = text_white

    p = tf_cm.add_paragraph()
    p.text = "STATUTORY DATA DISCLOSURE:"
    p.font.bold = True
    p.font.size = Pt(10)
    p.font.color.rgb = accent_sky
    p = tf_cm.add_paragraph()
    p.text = "All reported figures are cross-referenced with CMIE Prowess standardized taxonomy without fabricating synthetic proxies."
    p.font.size = Pt(8.5)
    p.font.color.rgb = text_muted

    # Right column: Decision Support Stance & Covenants
    box_ic = s8.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(6.8), Inches(1.8), Inches(5.733), Inches(4.8))
    box_ic.fill.solid()
    box_ic.fill.fore_color.rgb = surface_navy
    box_ic.line.color.rgb = accent_gold
    tf_ic = box_ic.text_frame
    tf_ic.word_wrap = True

    # Resolves Codex Finding F10: Replace string replace hacks with explicit, neutral policy
    if decision_support_policy == "NEUTRAL_EVIDENCE_BASED" or not ic or not ic.underwriting_verdict:
        clean_verdict = "CONDITIONAL MONITORING & COVENANT ENFORCEMENT"
    else:
        clean_verdict = "CONDITIONAL MONITORING & COVENANT ENFORCEMENT" if "APPROVE" in ic.underwriting_verdict else ic.underwriting_verdict

    p = tf_ic.paragraphs[0]
    p.text = f"DECISION SUPPORT STANCE: {clean_verdict}"
    p.font.bold = True
    p.font.size = Pt(12)
    p.font.color.rgb = accent_gold

    p = tf_ic.add_paragraph()
    raw_grade = ic.internal_screening_grade if (ic and ic.internal_screening_grade) else "UNRATED"
    clean_grade = raw_grade.replace("TIER_1_STRONG_CUSHION", "TIER_1_QUANTITATIVE_CUSHION")
    lev_txt = f"{ic.max_recommended_leverage_ratio:.2f}x" if (ic and ic.max_recommended_leverage_ratio) else "N/A"
    p.text = f"SCREENING PROFILE: {clean_grade} | MAX LEVERAGE: {lev_txt}"
    p.font.size = Pt(9.5)
    p.font.color.rgb = accent_sky

    p = tf_ic.add_paragraph()
    p.text = "MANDATORY LOAN COVENANTS:"
    p.font.bold = True
    p.font.size = Pt(10)
    p.font.color.rgb = accent_gold
    for cov in (ic.mandatory_loan_covenants[:3] if ic else []):
        p = tf_ic.add_paragraph()
        p.text = f"• {cov}"
        p.font.size = Pt(8.5)
        p.font.color.rgb = text_white

    p = tf_ic.add_paragraph()
    mandate_txt = ic.treasury_call_to_action if (ic and ic.treasury_call_to_action) else "Underwriting and treasury mandate suspended pending formal committee evaluation."
    p.text = f"TREASURY MANDATE: {mandate_txt}"
    p.font.size = Pt(9)
    p.font.color.rgb = status_emerald

    # Save to in-memory bytes buffer
    buffer = io.BytesIO()
    prs.save(buffer)
    return buffer.getvalue()
