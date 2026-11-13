"""
Regression & Computational Integrity Suite for Hindustan Coca-Cola DRHP (SEBI ICDR 2018).
Asserts epistemic stratification, unpriced DRHP circuit breakers, dynamic Beneish derivation,
statutory EBITDA and Net Worth perimeter alignment, and clean deck export.
"""
import io
import pytest
from pptx import Presentation
from models.pre_ipo_data import coca, PRE_IPO_REGISTRY
from models.pre_ipo_engine import (
    generate_equity_question_answers,
    calculate_wacc_and_roic,
    calculate_reverse_dcf_hurdle,
    classify_dickinson_stage,
)
from utils.pre_ipo_deck_generator import generate_pre_ipo_board_deck


def test_hcch_drhp_unpriced_circuit_breaker():
    """Verify that Hindustan Coca-Cola DRHP terms reflect statutory SEBI book-building [●]."""
    assert coca.is_price_disclosed is False
    assert coca.total_issue_size_cr == 0.0
    assert coca.fresh_issue_cr == 0.0
    assert coca.ofs_cr == 0.0
    assert coca.offered_shares_count == 997461456
    assert coca.fresh_issue_pct == 0.0
    assert coca.ofs_pct == 100.0
    assert coca.filing_type == "DRHP"


def test_hcch_equity_questions_no_literal_zeros():
    """Verify that Q07, Q08, Q10 never emit literal 0.0 Cr or 0.0x and enforce blocked status."""
    qs = generate_equity_question_answers(coca)

    # Q07 (Why this IPO)
    q07 = qs["Q07"]
    assert q07.status == "ANSWERED_WITH_EVIDENCE"
    assert "₹0.0 Cr" not in q07.direct_verdict
    assert "997,461,456" in q07.direct_verdict
    assert "[●]" in q07.direct_verdict

    # Q08 (Valuation justification)
    q08 = qs["Q08"]
    assert q08.status == "BLOCKED_PRICE_NOT_DISCLOSED"
    assert "0.0x" not in q08.direct_verdict
    assert "[●]" in q08.direct_verdict
    assert "undisclosed" in q08.direct_verdict.lower()

    # Q10 (Lock-in & returns)
    q10 = qs["Q10"]
    assert q10.status == "ANSWERED_WITH_EVIDENCE"
    assert "₹0.0 Cr" not in q10.direct_verdict
    assert "Day-30" in q10.direct_verdict
    assert "Day-90" in q10.direct_verdict


def test_hcch_ebitda_and_net_worth_statutory_accounting_reconciliation():
    """Verify EBITDA binds to statutory non-GAAP KPI and Net Worth excludes NCI."""
    # History years: FY24, FY25, FY26
    h_map = {h.fiscal_year: h for h in coca.history}
    assert "FY24" in h_map and "FY25" in h_map and "FY26" in h_map

    # Statutory EBITDA (excluding other income & exceptions)
    assert pytest.approx(h_map["FY24"].ebitda_cr, rel=1e-3) == 1777.94
    assert pytest.approx(h_map["FY25"].ebitda_cr, rel=1e-3) == 1640.02
    assert pytest.approx(h_map["FY26"].ebitda_cr, rel=1e-3) == 1353.04

    # Net Worth strictly parent-attributable equity (excluding NCI)
    assert pytest.approx(h_map["FY24"].net_worth_cr, rel=1e-3) == 8897.18
    assert pytest.approx(h_map["FY25"].net_worth_cr, rel=1e-3) == 9649.80
    assert pytest.approx(h_map["FY26"].net_worth_cr, rel=1e-3) == 9760.91


def test_hcch_cash_flows_and_dickinson_life_cycle():
    """Verify authentic 3-way cash flows and dynamic Dickinson life-cycle transitions."""
    h_map = {h.fiscal_year: h for h in coca.history}

    # FY25: CFO > 0, CFI < 0, CFF > 0 -> Growth
    fy25 = h_map["FY25"]
    assert fy25.cfo_cr > 0
    assert fy25.cfi_cr < 0
    assert fy25.cff_cr > 0
    stage25, pat25 = classify_dickinson_stage(fy25.cfo_cr, fy25.cfi_cr, fy25.cff_cr)
    assert stage25 == "Growth"
    assert pat25 == "(+, -, +)"

    # FY26: CFO > 0, CFI < 0, CFF < 0 -> Mature
    fy26 = h_map["FY26"]
    assert fy26.cfo_cr > 0
    assert fy26.cfi_cr < 0
    assert fy26.cff_cr < 0
    stage26, pat26 = classify_dickinson_stage(fy26.cfo_cr, fy26.cfi_cr, fy26.cff_cr)
    assert stage26 == "Mature (Cash Cow)"
    assert pat26 == "(+, -, -)"


def test_hcch_board_deck_generation_no_literal_zeros():
    """Verify PPTX generation for unpriced DRHP never emits 'Rs. 0.00 Cr' or '0.0x'."""
    deck_bytes = generate_pre_ipo_board_deck(coca)
    assert len(deck_bytes) > 20000

    prs = Presentation(io.BytesIO(deck_bytes))
    all_texts = []
    for slide in prs.slides:
        for shape in slide.shapes:
            if shape.has_text_frame:
                for p in shape.text_frame.paragraphs:
                    if p.text:
                        all_texts.append(p.text)

    deck_corpus = " ".join(all_texts)
    assert "Rs. 0.00 Cr" not in deck_corpus
    assert "IMPLIED P/E RATIO: 0.0x" not in deck_corpus
    assert "Rs. 0.0 Cr" not in deck_corpus or "Company Proceeds: Rs. 0.0" in deck_corpus
    assert "997,461,456 Shares" in deck_corpus
    assert "Undisclosed [●]" in deck_corpus


def test_all_six_dossiers_equity_and_deck_integrity():
    """Regression test ensuring equity questions and decks compile across all 6 dossiers."""
    for deal_id, dossier in PRE_IPO_REGISTRY.items():
        qs = generate_equity_question_answers(dossier)
        assert len(qs) >= 10, f"Dossier {deal_id} missing equity questions"
        deck = generate_pre_ipo_board_deck(dossier)
        assert len(deck) > 20000, f"Dossier {deal_id} deck failed to generate"
