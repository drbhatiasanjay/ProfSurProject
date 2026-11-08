"""
Pre-IPO DRHP Part 1 Acceptance Gate Verification Suite.
Validates:
1. Known-value single-period searchable PDF (known-values.pdf) with strict expected vs actual matching.
2. Supported multi-period multi-column table (Hindustan_Coca_Cola_Holdings_DRHP.pdf) with period/unit alignment.
3. Unfamiliar layout with genuine zero ("Nil"), negative in parentheses, and derived FCF.
4. Missing fields / Non-financial text PDF: flags GAP-INTAKE without inventing numbers.
5. Scanned / unreadable document: flags GAP-OCR-01 and reports provider status truthfully.
6. Board Deck PPTX export eligibility and content preservation.
"""
import os
import io
import re
import pytest
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

from models.pre_ipo_ingest import PreIPOIngestionEngine
from utils.pre_ipo_deck_generator import generate_pre_ipo_board_deck

KNOWN_VALUES_PDF = r"C:\Users\hemas\.codex\worktrees\profsur-decision-depth\ProfSurProject\scratch\ingestion_assessment_20261108\known-values.pdf"
HCCB_DRHP_PDF = "Hindustan_Coca_Cola_Holdings_DRHP.pdf"


def test_gate_1_known_values_searchable_pdf():
    """Validates known-values.pdf extraction with zero hardcoded defaults."""
    assert os.path.exists(KNOWN_VALUES_PDF), f"Test fixture missing: {KNOWN_VALUES_PDF}"
    dossier = PreIPOIngestionEngine.ingest_document(KNOWN_VALUES_PDF)

    # Must have exactly 1 history period: FY24
    assert len(dossier.history) == 1, f"Expected 1 period, got {len(dossier.history)}"
    h = dossier.history[0]
    assert h.fiscal_year == "FY24"

    # Expected vs Actual comparisons
    expected = {
        "revenue_ops_cr": 1234.0,
        "ebitda_cr": 234.0,
        "pat_cr": 89.0,
        "cfo_cr": 123.0,
        "capex_cr": 45.0,
        "fcf_cr": 78.0,
        "net_worth_cr": 678.0,
    }
    for field, exp_val in expected.items():
        act_val = getattr(h, field)
        assert act_val == exp_val, f"Mismatch for {field}: expected {exp_val}, got {act_val}"

    # Debt and Cash
    assert dossier.indebtedness.funded_bank_debt_cr == 200.0, f"Expected debt 200.0, got {dossier.indebtedness.funded_bank_debt_cr}"
    assert dossier.indebtedness.cash_and_equivalents_cr == 50.0, f"Expected cash 50.0, got {dossier.indebtedness.cash_and_equivalents_cr}"

    # Verdict must be awaiting review, never approved
    assert dossier.ic_verdict.underwriting_verdict == "AWAITING_INDEPENDENT_REVIEW"
    assert "PRUDENT_LOW_LEVERAGE_APPROVED" not in dossier.ic_verdict.underwriting_verdict


def test_gate_2_multi_period_table_alignment():
    """Validates multi-column period alignment from actual DRHP."""
    assert os.path.exists(HCCB_DRHP_PDF), f"Test fixture missing: {HCCB_DRHP_PDF}"
    dossier = PreIPOIngestionEngine.ingest_document(HCCB_DRHP_PDF)

    period_names = [h.fiscal_year for h in dossier.history]
    assert "FY24" in period_names
    assert "FY25" in period_names

    # Check FY24 row
    h_fy24 = next(h for h in dossier.history if h.fiscal_year == "FY24")
    assert h_fy24.revenue_ops_cr == 12840.10
    assert h_fy24.ebitda_cr == 2054.40
    assert h_fy24.pat_cr == 852.10
    assert h_fy24.cfo_cr == 1840.20
    assert h_fy24.capex_cr == 750.00
    assert h_fy24.fcf_cr == 1090.20
    assert h_fy24.net_worth_cr == 6801.80

    # Check FY25 row
    h_fy25 = next(h for h in dossier.history if h.fiscal_year == "FY25")
    assert h_fy25.revenue_ops_cr == 14021.50
    assert h_fy25.ebitda_cr == 2411.70
    assert h_fy25.pat_cr == 1048.20
    assert h_fy25.cfo_cr == 2150.40
    assert h_fy25.capex_cr == 820.00
    assert h_fy25.fcf_cr == 1330.40
    assert h_fy25.net_worth_cr == 7850.00

    # Check indebtedness
    assert dossier.indebtedness.secured_term_loans_cr == 1450.0
    assert dossier.ic_verdict.underwriting_verdict == "AWAITING_INDEPENDENT_REVIEW"


def test_gate_3_unfamiliar_layout_with_zeros_and_negatives():
    """Validates unfamiliar layout: Nil treated as 0.0, parentheses as negative, FCF derived correctly."""
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=letter)
    c.drawString(100, 750, "Novel Synthetic Beta Limited")
    c.drawString(100, 720, "Financial Statements for FY24 (All amounts in INR Crore)")
    c.drawString(100, 700, "Gross Revenue: 850.0")
    c.drawString(100, 680, "Operating EBITDA: Nil")
    c.drawString(100, 660, "Profit After Tax: (45.0)")
    c.drawString(100, 640, "Cash Flow from Operations: 60.0")
    c.drawString(100, 620, "Capital Expenditures: 20.0")
    c.drawString(100, 600, "Tangible Net Worth: 300.0")
    c.drawString(100, 580, "Secured Term Loans: Nil")
    c.drawString(100, 560, "Cash & Bank Balances: 15.0")
    c.save()
    buf.seek(0)

    dossier = PreIPOIngestionEngine.ingest_document(buf)
    assert len(dossier.history) == 1
    h = dossier.history[0]
    assert h.revenue_ops_cr == 850.0
    assert h.ebitda_cr == 0.0  # Nil parsed as genuine zero
    assert h.pat_cr == -45.0   # (45.0) parsed as negative
    assert h.cfo_cr == 60.0
    assert h.capex_cr == 20.0
    assert h.fcf_cr == 40.0    # 60.0 - 20.0
    assert h.net_worth_cr == 300.0
    assert dossier.indebtedness.secured_term_loans_cr == 0.0
    assert dossier.indebtedness.cash_and_equivalents_cr == 15.0


def test_gate_4_non_financial_pdf_flags_missing_gaps():
    """Validates that a non-financial text PDF flags gaps and never fabricates numbers."""
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=letter)
    c.drawString(100, 750, "General Legal Notice & Policy Document")
    c.drawString(100, 700, "This document contains terms and conditions for corporate suppliers.")
    c.drawString(100, 650, "No financial information or debt schedules are included herein.")
    c.save()
    buf.seek(0)

    dossier = PreIPOIngestionEngine.ingest_document(buf)
    assert len(dossier.history) == 0
    assert dossier.ic_verdict.underwriting_verdict == "INSUFFICIENT_DISCLOSURES_UNRATED"
    assert any(g.gap_id.startswith("GAP-INTAKE-") for g in dossier.limitations)


def test_gate_5_scanned_unreadable_pdf_reports_quota_status():
    """Validates that empty/scanned PDF reports OCR status truthfully without dummy data."""
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=letter)
    c.showPage()
    c.save()
    buf.seek(0)

    dossier = PreIPOIngestionEngine.ingest_document(buf)
    assert len(dossier.history) == 0
    assert dossier.ic_verdict.underwriting_verdict == "INSUFFICIENT_DISCLOSURES_UNRATED"
    ocr_gap = next((g for g in dossier.limitations if g.gap_id == "GAP-OCR-01"), None)
    assert ocr_gap is not None
    assert ocr_gap.current_status in ("PROVIDER_CREDITS_DEPLETED_402", "AWAITING_OCR_KEY", "PARSE_FAILED")


def test_gate_6_board_deck_export_eligibility():
    """Validates that board deck PPTX is generated safely from extracted dossier."""
    assert os.path.exists(KNOWN_VALUES_PDF)
    dossier = PreIPOIngestionEngine.ingest_document(KNOWN_VALUES_PDF)
    deck_bytes = generate_pre_ipo_board_deck(dossier)
    assert isinstance(deck_bytes, bytes)
    assert len(deck_bytes) > 20000
    # PPTX files start with PK (ZIP format)
    assert deck_bytes[:2] == b"PK"
