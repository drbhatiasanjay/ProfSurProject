import io
import sys
import os

# Add root directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from models.pre_ipo_data import PRE_IPO_REGISTRY
from models.pre_ipo_ingest import PreIPOIngestionEngine
from components.pre_ipo_provenance_ledger import _get_complete_extraction_ledger

def test_provenance_ledger_all_dossiers():
    print("--- [Step 2 Check] Verifying Provenance Ledger compilation for all 6 dossiers ---")
    for deal_id, dossier in PRE_IPO_REGISTRY.items():
        ledger = _get_complete_extraction_ledger(dossier)
        print(f"Deal {deal_id}: {len(ledger)} reconciled facts compiled.")
        assert len(ledger) >= 15, f"Expected at least 15 items in ledger, got {len(ledger)}"
        # Check coordinates and non-empty quotes
        for item in ledger:
            assert item["physical_page"] > 0
            assert len(item["raw_quote"]) > 0
            assert len(item["section"]) > 0
            assert len(item["status"]) > 0
    print("[SUCCESS] All 6 dossiers compiled complete, verified provenance ledgers!")

def test_stream_indexer_ingestion():
    print("--- [Step 1 Check] Verifying End-to-End PDF Ingestion Pipeline ---")
    # Generate minimal valid PDF with Section V and Section III
    from reportlab.lib.pagesizes import letter
    from reportlab.pdfgen import canvas
    
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=letter)
    
    # Page 1: Cover
    c.drawString(100, 750, "DRAFT RED HERRING PROSPECTUS")
    c.drawString(100, 730, "ACME TECH INNOVATIONS LIMITED")
    c.drawString(100, 710, "INITIAL PUBLIC OFFERING OF UP TO 50,000,000 EQUITY SHARES")
    c.showPage()
    
    # Page 2: Table of Contents
    c.drawString(100, 750, "TABLE OF CONTENTS")
    c.drawString(100, 700, "SECTION I: GENERAL ................................................... 5")
    c.drawString(100, 680, "SECTION III: INTRODUCTION ............................................ 15")
    c.drawString(100, 660, "SECTION V: FINANCIAL STATEMENTS ..................................... 25")
    c.showPage()
    
    # Pages 3-24: Filler
    for p in range(3, 25):
        c.drawString(100, 750, f"Section Content Page {p}")
        c.showPage()
        
    # Page 25: Financial Statements
    c.drawString(100, 750, "SECTION V - RESTATED FINANCIAL STATEMENTS")
    c.drawString(100, 720, "Summary Statement of Profit and Losses (Rs. in Millions)")
    c.drawString(100, 700, "Particulars FY24 FY25 FY26")
    c.drawString(100, 680, "Revenue from operations 140215.45 127512.93 115485.80")
    c.drawString(100, 660, "EBITDA 16422.30 15210.50 14100.20")
    c.drawString(100, 640, "Profit after tax 11650.00 10500.00 9800.00")
    c.drawString(100, 620, "Total Indebtedness 4500.00 4800.00 5200.00")
    c.drawString(100, 600, "Cash and bank balances 4320.00 3900.00 3500.00")
    c.showPage()
    c.save()
    
    pdf_bytes = buf.getvalue()
    print(f"Generated test PDF: {len(pdf_bytes)/1024:.1f} KB, 25 pages.")
    
    dossier = PreIPOIngestionEngine.ingest_document(
        io.BytesIO(pdf_bytes),
        company_name_hint="Acme Tech Innovations Limited",
        is_exemplar_mode=False
    )
    
    assert dossier.company_name == "Acme Tech Innovations Limited"
    assert len(dossier.history) >= 3, f"Expected 3 historical years, got {len(dossier.history)}"
    print(f"Extracted company: {dossier.company_name}")
    print(f"Extracted history count: {len(dossier.history)} years (FY24, FY25, FY26)")
    print(f"Audit report items: {len(dossier.audit_report)}")
    if dossier.beneish_forensics:
        print(f"Beneish DSRI: {dossier.beneish_forensics.dsri:.3f}, SGI: {dossier.beneish_forensics.sgi:.3f}")
    
    # Verify provenance ledger compiles for ingested document
    ledger = _get_complete_extraction_ledger(dossier)
    print(f"Ingested document compiled ledger count: {len(ledger)} facts.")
    assert len(ledger) >= 10
    print("[SUCCESS] Step 1 verification passed completely!")

if __name__ == "__main__":
    test_provenance_ledger_all_dossiers()
    test_stream_indexer_ingestion()
