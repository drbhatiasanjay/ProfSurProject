"""
Verification Script: Two-Pass Stream Prospectus Indexer End-to-End Test.
Simulates a 513-page statutory DRHP conforming to SEBI ICDR 2018 layout
and verifies section-bounded stream extraction at page 68+ with exact page coordinates.
"""
import io
import os
import sys
import time
import tracemalloc

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, PageBreak, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

from models.prospectus_indexer import ProspectusSectionIndexer
from models.pre_ipo_ingest import PreIPOIngestionEngine


def build_synthetic_513_page_drhp() -> bytes:
    """Generates an authentic-structured 513-page DRHP PDF in memory."""
    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf,
        pagesize=letter,
        rightMargin=36,
        leftMargin=36,
        topMargin=36,
        bottomMargin=36,
    )
    styles = getSampleStyleSheet()

    body_style = ParagraphStyle(
        'DRHPBody',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9,
        leading=12,
    )

    heading_style = ParagraphStyle(
        'DRHPHeading',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=12,
        leading=15,
        textColor=colors.HexColor('#0f172a'),
    )

    story = []

    # Page 1: Cover Page
    story.append(Paragraph("DRAFT RED HERRING PROSPECTUS", heading_style))
    story.append(Paragraph("DATED NOVEMBER 6, 2026", body_style))
    story.append(Spacer(1, 10))
    story.append(Paragraph("INITIAL PUBLIC OFFERING OF UP TO 997,461,456 EQUITY SHARES OF HINDUSTAN COCA-COLA HOLDINGS LIMITED ('COMPANY' OR 'ISSUER')", heading_style))
    story.append(Paragraph("THROUGH AN OFFER FOR SALE OF UP TO 997,461,456 EQUITY SHARES BY SELLING SHAREHOLDERS.", body_style))
    story.append(Paragraph("FACE VALUE OF RS. 10 EACH AT AN OFFER PRICE OF RS. [●] PER EQUITY SHARE AGGREGATING UP TO RS. [●] CRORES.", body_style))
    story.append(PageBreak())

    # Pages 2 to 11: Preliminary Disclosures
    for p in range(2, 12):
        story.append(Paragraph(f"Preliminary General Information Page {p}", body_style))
        story.append(PageBreak())

    # Page 12: Table of Contents (Statutory Pattern)
    story.append(Paragraph("TABLE OF CONTENTS", heading_style))
    story.append(Spacer(1, 8))
    story.append(Paragraph("SECTION I - GENERAL INFORMATION .................................................... 1", body_style))
    story.append(Paragraph("SECTION II - RISK FACTORS ........................................................... 20", body_style))
    story.append(Paragraph("SECTION III - OBJECTS OF THE OFFER .................................................. 45", body_style))
    story.append(Paragraph("SECTION IV - CAPITAL STRUCTURE ...................................................... 52", body_style))
    story.append(Paragraph("SECTION V - RESTATED CONSOLIDATED FINANCIAL INFORMATION ............................. 68", body_style))
    story.append(Paragraph("SECTION VI - STATEMENT OF FINANCIAL INDEBTEDNESS .................................... 140", body_style))
    story.append(Paragraph("SECTION VII - MANAGEMENT'S DISCUSSION AND ANALYSIS .................................. 180", body_style))
    story.append(PageBreak())

    # Pages 13 to 44: Intervening Section Pages
    for p in range(13, 45):
        story.append(Paragraph(f"Section Content Page {p}", body_style))
        story.append(PageBreak())

    # Page 45: Objects of the Offer
    story.append(Paragraph("SECTION III - OBJECTS OF THE OFFER", heading_style))
    story.append(Paragraph("Requirement of Funds: 100% Offer for Sale by the Selling Shareholders.", body_style))
    story.append(Paragraph("The Company will not receive any proceeds from the Offer (Nil Fresh Issue).", body_style))
    story.append(PageBreak())

    # Pages 46 to 51: Intervening Pages
    for p in range(46, 52):
        story.append(Paragraph(f"General Disclosures Page {p}", body_style))
        story.append(PageBreak())

    # Page 52: Capital Structure
    story.append(Paragraph("SECTION IV - CAPITAL STRUCTURE", heading_style))
    story.append(Paragraph("The equity share capital of the Company before the Offer is 997,461,456 equity shares of face value Rs. 10 each.", body_style))
    story.append(Paragraph("Total offered shares count is 997,461,456 equity shares in 100% OFS.", body_style))
    story.append(PageBreak())

    # Pages 53 to 67: Intervening Pages
    for p in range(53, 68):
        story.append(Paragraph(f"Legal and Other Information Page {p}", body_style))
        story.append(PageBreak())

    # Page 68: Section V - Restated Consolidated Financial Information (Page 68)
    story.append(Paragraph("SECTION V - RESTATED CONSOLIDATED FINANCIAL INFORMATION", heading_style))
    story.append(Paragraph("(All amounts in INR Million unless otherwise stated)", body_style))
    story.append(Spacer(1, 6))
    story.append(Paragraph("Restated Summary Statement of Profit and Loss", heading_style))
    story.append(Paragraph("Metric (INR Mn)    FY24    FY25    FY26", body_style))
    story.append(Paragraph("Revenue from operations    140215.45    127512.93    115485.80", body_style))
    story.append(Paragraph("Operating EBITDA    17779.36    16400.19    13530.40", body_style))
    story.append(Paragraph("Profit after tax    28121.00    7599.00    11650.50", body_style))
    story.append(Paragraph("Cash flow from operations    2846.90    15727.00    22901.90", body_style))
    story.append(Paragraph("Net worth    88971.80    96498.00    97609.10", body_style))
    story.append(PageBreak())

    # Pages 69 to 513: Notes and Statutory Schedules to reach exactly 513 pages
    for p in range(69, 514):
        story.append(Paragraph(f"Restated Financial Notes, Accounting Policies and Schedules - Page {p}", body_style))
        if p < 513:
            story.append(PageBreak())

    doc.build(story)
    buf.seek(0)
    return buf.read()


def main():
    print("=" * 70)
    print("VERIFYING TWO-PASS STREAM PROSPECTUS INDEXER (513 PAGES)")
    print("=" * 70)

    tracemalloc.start()
    t0 = time.time()

    print("[Step 1] Synthesizing authentic 513-page statutory DRHP...")
    pdf_bytes = build_synthetic_513_page_drhp()
    t_gen = time.time()
    print(f"         Generated 513-page PDF in {t_gen - t0:.2f}s | Size: {len(pdf_bytes) / 1024:.1f} KB")

    print("[Step 2] Executing Pass 1: Outline and TOC Section Discovery...")
    indexer = ProspectusSectionIndexer(pdf_bytes)
    t_idx = time.time()
    print(f"         Indexed total pages: {indexer.total_pages} in {t_idx - t_gen:.2f}s")

    # Assertions on Section Discovery
    assert indexer.total_pages == 513, f"Expected 513 pages, got {indexer.total_pages}"

    fin_pages = indexer.get_section_pages("FINANCIALS")
    print(f"         Discovered FINANCIALS pages count: {len(fin_pages)} | Start page index: {fin_pages[0] if fin_pages else None}")
    assert fin_pages, "FINANCIALS section must be discovered in TOC"
    assert fin_pages[0] == 67, f"Expected Section V Financials to start at physical page index 67 (Page 68), got {fin_pages[0]}"

    obj_pages = indexer.get_section_pages("OBJECTS")
    print(f"         Discovered OBJECTS pages count: {len(obj_pages)} | Start page index: {obj_pages[0] if obj_pages else None}")
    assert obj_pages, "OBJECTS section must be discovered in TOC"
    assert obj_pages[0] == 44, f"Expected Section III Objects to start at physical page index 44 (Page 45), got {obj_pages[0]}"

    cap_pages = indexer.get_section_pages("CAPITAL_STRUCTURE")
    print(f"         Discovered CAPITAL_STRUCTURE pages count: {len(cap_pages)} | Start page index: {cap_pages[0] if cap_pages else None}")
    assert cap_pages, "CAPITAL_STRUCTURE section must be discovered in TOC"
    assert cap_pages[0] == 51, f"Expected Section IV Capital Structure to start at physical page index 51 (Page 52), got {cap_pages[0]}"

    print("\n[Step 3] Executing Pass 2: Targeted Extraction via PreIPOIngestionEngine...")
    dossier = PreIPOIngestionEngine.ingest_document(
        io.BytesIO(pdf_bytes),
        company_name_hint="Hindustan Coca-Cola Holdings Limited",
        is_exemplar_mode=False,
    )
    t_ext = time.time()
    print(f"         Completed section-bounded ingestion in {t_ext - t_idx:.2f}s")

    # Assertions on Extracted Facts
    print(f"         Extracted Company Name: {dossier.company_name}")
    assert "Hindustan Coca-Cola" in dossier.company_name, "Company name must be recognized"

    print(f"         Extracted History Periods: {[h.fiscal_year for h in dossier.history]}")
    assert len(dossier.history) >= 3, f"Expected at least 3 historical periods, got {len(dossier.history)}"

    latest = dossier.latest_financials
    print(f"         Latest Financials ({latest.fiscal_year}): Rev = ₹{latest.revenue_ops_cr:,.2f} Cr, EBITDA = ₹{latest.ebitda_cr:,.2f} Cr, PAT = ₹{latest.pat_cr:,.2f} Cr")
    # FY26 values in INR Million -> converted to INR Cr (scale = 0.1)
    assert abs(latest.revenue_ops_cr - 11548.58) < 1.0, f"Expected FY26 Revenue ~11548.58 Cr, got {latest.revenue_ops_cr}"
    assert abs(latest.ebitda_cr - 1353.04) < 1.0, f"Expected FY26 EBITDA ~1353.04 Cr, got {latest.ebitda_cr}"
    assert abs(latest.pat_cr - 1165.05) < 1.0, f"Expected FY26 PAT ~1165.05 Cr, got {latest.pat_cr}"

    # Verify Page Coordinates in Audit Ledger
    print(f"         Audit Ledger items count: {len(dossier.audit_report)}")
    section_v_citations = [item for item in dossier.audit_report if "Page 68" in (item.citation or "")]
    print(f"         Found {len(section_v_citations)} audit entries explicitly anchored to Page 68!")
    assert len(section_v_citations) > 0, "Audit report must contain exact citations to Page 68"

    for item in section_v_citations[:4]:
        print(f"            - [{item.field_name}]: {item.raw_extracted_value} -> {item.normalized_metric} ({item.citation})")

    # Dynamic Beneish verification on extracted dossier
    assert dossier.beneish_forensics is not None, "Dossier must have beneish_forensics computed dynamically"
    print(f"         Dynamically Computed Beneish M-Score: {dossier.beneish_forensics.m_score} (is_risk={dossier.beneish_forensics.is_manipulation_risk})")

    current_mem, peak_mem = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    print(f"\n[Step 4] Memory Footprint Check:")
    print(f"         Peak memory consumed: {peak_mem / (1024 * 1024):.2f} MB")
    print(f"         Cloud Run 150 MB boundary headroom: {150.0 - (peak_mem / (1024 * 1024)):.2f} MB")
    assert peak_mem < 150 * 1024 * 1024, f"Peak memory {peak_mem / 1e6} MB exceeded 150 MB boundary"

    print("\n" + "=" * 70)
    print("SUCCESS: 513-PAGE STREAM INDEXER AND SECTION V EXTRACTION VERIFIED 100%!")
    print("=" * 70)


if __name__ == "__main__":
    main()
