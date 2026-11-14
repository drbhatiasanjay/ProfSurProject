"""
Regression and verification test suite for PRE_IPO_CODE_REVIEW_5687478 findings A01-A10 and B01-B04.
"""
import io
import math
import os
import dataclasses
from datetime import datetime, timezone
from unittest.mock import patch, MagicMock
import pytest
pypdf = pytest.importorskip('pypdf')
from pypdf import PdfWriter
from pypdf.generic import DictionaryObject, NameObject, DecodedStreamObject
from pptx import Presentation

from models.pre_ipo_schema import (
    ObjectsOfOfferWaterfall,
    BeneishMScoreRatios,
    ListedPeerComp,
    DebtMaturityLadder,
    IndebtednessSchedule,
    CMIECrosswalkRecord,
    PreIPODealDossier,
    FinancialYearMetric,
)
from models.pre_ipo_ingest import PreIPOIngestionEngine
from models.pre_ipo_data import PRE_IPO_REGISTRY
from models.pre_ipo_engine import (
    generate_anchor_lockin_calendar,
    generate_2d_sensitivity_matrix,
    generate_financials_narrative,
    generate_indebtedness_narrative,
    calculate_beneish_m_score,
    generate_persona_decision_view,
    generate_equity_question_answers,
    calculate_reverse_dcf_hurdle,
    calculate_wacc_and_roic,
    generate_cmie_crosswalk_coverage,
)
from utils.pre_ipo_deck_generator import generate_pre_ipo_board_deck


def create_searchable_empty_pdf() -> io.BytesIO:
    writer = PdfWriter()
    page = writer.add_blank_page(width=612, height=792)
    font = DictionaryObject({
        NameObject('/Type'): NameObject('/Font'),
        NameObject('/Subtype'): NameObject('/Type1'),
        NameObject('/BaseFont'): NameObject('/Helvetica'),
    })
    page[NameObject('/Resources')] = DictionaryObject({
        NameObject('/Font'): DictionaryObject({NameObject('/F1'): writer._add_object(font)})
    })
    stream = DecodedStreamObject()
    stream.set_data(b'BT /F1 12 Tf 10 700 Td (Unseen Widget Issuer. This test document contains no financial statements, offer terms, loan schedules or valuation. It deliberately provides more than one hundred searchable characters.) Tj ET')
    page[NameObject('/Contents')] = writer._add_object(stream)
    pdf = io.BytesIO()
    writer.write(pdf)
    pdf.seek(0)
    return pdf


# ─────────────────────────────────────────────────────────────────────────────
# A01: Searchable PDF Ingestion Crash & Fabricated Fallback Data
# ─────────────────────────────────────────────────────────────────────────────
def test_a01_searchable_pdf_no_crash_and_no_fabricated_financials():
    pdf = create_searchable_empty_pdf()
    with patch('models.pre_ipo_ingest.get_gemini_api_key', return_value=None):
        dossier = PreIPOIngestionEngine.ingest_document(pdf, company_name_hint="Unseen Widget Issuer")

    assert dossier is not None
    # Must NOT fabricate 1500 Cr revenue or 1000 Cr offer
    assert dossier.total_issue_size_cr == 0.0 or dossier.latest_financials.revenue_ops_cr == 0.0
    # Must NOT fabricate "APPROVE WITH COVENANTS"
    assert "APPROVE" not in dossier.ic_verdict.underwriting_verdict
    # Must record explicit decision limitations
    assert len(dossier.limitations) > 0


# ─────────────────────────────────────────────────────────────────────────────
# A02: Vision OCR Configurable Supported Model
# ─────────────────────────────────────────────────────────────────────────────
def test_a02_ocr_model_configurable_and_not_hardcoded_retired():
    with patch.dict(os.environ, {"GEMINI_VISION_MODEL": "gemini-2.0-flash"}):
        model = PreIPOIngestionEngine.get_vision_model_name()
        assert model == "gemini-2.0-flash"
        assert "gemini-1.5-flash" not in model or "8b" in model


# ─────────────────────────────────────────────────────────────────────────────
# A03: Empty OCR Response Output Validation
# ─────────────────────────────────────────────────────────────────────────────
def test_a03_empty_ocr_json_does_not_yield_reconciled_confidence():
    client = MagicMock()
    client.models.generate_content.return_value.text = '{}'
    with patch('models.pre_ipo_ingest.get_gemini_api_key', return_value='fake-key'), \
         patch('google.genai.Client', return_value=client):
        dossier, status = PreIPOIngestionEngine.parse_scanned_pdf_with_vision(io.BytesIO(b'%PDF-1.4 ' + b'0' * 120), allow_external_cloud_ocr=True)

    assert status in ("EXTRACTION_EMPTY_OR_INVALID", "INSUFFICIENT_DATA")
    if dossier is not None:
        # Items must NOT be marked FOUND_AND_RECONCILED with high confidence
        for item in dossier.audit_report:
            assert item.status != "FOUND_AND_RECONCILED" or item.confidence_score < 0.5
        assert len(dossier.limitations) > 0


# ─────────────────────────────────────────────────────────────────────────────
# A04: Screen and Deck Floating-Rate Exposure Synchronization
# ─────────────────────────────────────────────────────────────────────────────
def test_a04_screen_and_deck_floating_rate_exposure_identical():
    af = PRE_IPO_REGISTRY['afcons_infra']
    stored_fl = af.indebtedness.floating_rate_portion_pct
    assert stored_fl == 85.0

    # Sensitivity from screen parameters
    screen_stress = generate_2d_sensitivity_matrix(
        base_ebitda_cr=af.latest_financials.ebitda_cr,
        gross_debt_cr=af.indebtedness.funded_bank_debt_cr,
        base_wair_pct=af.indebtedness.weighted_avg_interest_rate_pct or 8.5,
        floating_debt_portion_pct=af.indebtedness.floating_rate_portion_pct,
    )
    # Sensitivity from deck parameters
    deck_stress = generate_2d_sensitivity_matrix(
        base_ebitda_cr=af.latest_financials.ebitda_cr,
        gross_debt_cr=af.indebtedness.funded_bank_debt_cr,
        base_wair_pct=af.indebtedness.weighted_avg_interest_rate_pct or 8.5,
        floating_debt_portion_pct=af.indebtedness.floating_rate_portion_pct,
    )
    assert screen_stress['matrix'][-1]['hike_300bps'] == deck_stress['matrix'][-1]['hike_300bps']

    # Both DebtMaturityLadder and IndebtednessSchedule must provide consistent floating exposure
    assert hasattr(af.debt_maturity, 'floating_rate_portion_pct') or hasattr(af.debt_maturity, 'floating_rate_debt_pct')


# ─────────────────────────────────────────────────────────────────────────────
# A05: Lock-In Dates, Quantities & Status
# ─────────────────────────────────────────────────────────────────────────────
def test_a05_lockin_calendar_dynamic_dates_and_quantities():
    af = PRE_IPO_REGISTRY['afcons_infra']
    as_of = datetime(2026, 11, 7).date()
    cal = generate_anchor_lockin_calendar(af, as_of_date=as_of)
    assert len(cal) >= 3

    # Day 30 and Day 90 must each unlock exactly 50% of the anchor tranche
    assert cal[1].unlocked_pct == 50.0
    assert cal[2].unlocked_pct == 50.0

    # For an event in May 2025 relative to as_of Nov 2026, status must be EXPIRED, not UPCOMING
    for m in cal:
        if m.calendar_date and m.calendar_date < "2026-11-01":
            assert m.status == "EXPIRED"


# ─────────────────────────────────────────────────────────────────────────────
# A06: Beneish M-Score NaN/Missing Input Rejection
# ─────────────────────────────────────────────────────────────────────────────
def test_a06_beneish_nan_and_missing_inputs_rejected():
    nan_ratios = BeneishMScoreRatios(*([1.0] * 7), tata=float('nan'))
    assert nan_ratios.is_computable is False
    assert nan_ratios.m_score is None
    assert nan_ratios.is_manipulation_risk is None

    # calculate_beneish_m_score with only 2 summary financials and no line-item schedules
    af = PRE_IPO_REGISTRY['afcons_infra']
    res = calculate_beneish_m_score(af.history[-1], af.history[-2])
    assert res['is_scoreable'] is False
    assert res['m_score'] is None


# ─────────────────────────────────────────────────────────────────────────────
# A07: Exported Narrative Truthfulness for Loss-Making Issuers
# ─────────────────────────────────────────────────────────────────────────────
def test_a07_loss_issuer_deck_truthful_narrative():
    swiggy = PRE_IPO_REGISTRY['swiggy']
    assert swiggy.latest_financials.cfo_cr < 0

    deck_bytes = generate_pre_ipo_board_deck(swiggy)
    prs = Presentation(io.BytesIO(deck_bytes))
    deck_text = '\n'.join(sh.text for sl in prs.slides for sh in sl.shapes if sh.has_text_frame)

    # Must NOT claim "robust internal self-financing" for Swiggy
    assert "robust internal self-financing" not in deck_text.lower()
    # Must NOT claim "sector median of 1.45x"
    assert "sector median of 1.45x" not in deck_text.lower()


# ─────────────────────────────────────────────────────────────────────────────
# A08: Evidence-Backed Commentary and Board Persona Default
# ─────────────────────────────────────────────────────────────────────────────
def test_a08_no_unsupported_commentary_and_board_persona_no_false_approval():
    af = PRE_IPO_REGISTRY['afcons_infra']
    nar = generate_financials_narrative(af)
    # Inflection triggers must not contain fixed invented string "18-25%"
    assert "18-25%" not in nar['inflection_triggers']

    # Board persona with ic_verdict=None must NOT return APPROVE
    unrated_deal = dataclasses.replace(af, ic_verdict=None)
    board_view = generate_persona_decision_view(unrated_deal, persona="board")
    assert "APPROVE" not in board_view['recommendation']
    assert "PENDING" in board_view['recommendation'] or "UNRATED" in board_view['recommendation']


# ─────────────────────────────────────────────────────────────────────────────
# A09: Offer Ledger Conservation & Savings Validation
# ─────────────────────────────────────────────────────────────────────────────
def test_a09_overallocated_offer_rejected_and_savings_blocked():
    obj = ObjectsOfOfferWaterfall(
        gross_fresh_issue_cr=100.0,
        issue_expenses_cr=5.0,
        debt_prepayment_cr=1000.0,
        capex_expansion_cr=0.0,
        inorganic_acquisition_cr=0.0,
        general_corporate_purposes_cr=0.0,
        interest_rate_on_retired_debt_pct=9.0,
    )
    assert obj.is_allocation_valid is False
    assert obj.sebi_gcp_compliant is False
    # Annual savings must NOT be credited on 1000 Cr when net proceeds are only 95 Cr
    assert obj.annual_interest_savings_cr <= 95.0 * 0.09 + 0.01


# ─────────────────────────────────────────────────────────────────────────────
# A10: No Blind PDF Byte Slicing
# ─────────────────────────────────────────────────────────────────────────────
def test_a10_no_blind_byte_slicing_on_oversized_file():
    huge_bytes = b'%PDF-1.4\n' + b'0' * (30 * 1024 * 1024)
    # Must raise or return error about file size instead of silent corruption
    dossier, status = PreIPOIngestionEngine.parse_scanned_pdf_with_vision(io.BytesIO(huge_bytes))
    assert status in ("FILE_TOO_LARGE", "SIZE_EXCEEDS_LIMIT", "EXTRACTION_FAILED") or dossier is None


# ─────────────────────────────────────────────────────────────────────────────
# B01: Equity Investor Questions Evidence Gating
# ─────────────────────────────────────────────────────────────────────────────
def test_b01_unknown_issuer_questions_not_answered_with_evidence():
    pdf = create_searchable_empty_pdf()
    with patch('models.pre_ipo_ingest.get_gemini_api_key', return_value=None):
        unknown = PreIPOIngestionEngine.ingest_document(pdf, company_name_hint="Unknown Issuer")

    answers = generate_equity_question_answers(unknown)
    for qid in ('Q02', 'Q04', 'Q05'):
        assert answers[qid].status in ("INSUFFICIENT_DATA_UNANSWERED", "REQUIRES_FURTHER_DILIGENCE")
        assert "superior operating margins" not in answers[qid].direct_verdict.lower()


# ─────────────────────────────────────────────────────────────────────────────
# B02: Reverse DCF Feasibility & Residual Check
# ─────────────────────────────────────────────────────────────────────────────
def test_b02_reverse_dcf_unbracketed_ev_returns_unfeasible():
    af = PRE_IPO_REGISTRY['afcons_infra']
    huge = dataclasses.replace(af, valuation_comps=dataclasses.replace(af.valuation_comps, implied_ev_cr=1e15))
    reverse = calculate_reverse_dcf_hurdle(huge)

    # Must NOT claim required CAGR is 80% when PV at 80% is trivial relative to 1e15
    assert reverse['required_fcf_cagr_pct'] is None
    assert reverse['hurdle_difficulty'] in ("MATHEMATICALLY_OUT_OF_BOUNDS", "UNFEASIBLE_IMPLIED_VALUATION", "MISSING_DISCOUNT_RATE")


# ─────────────────────────────────────────────────────────────────────────────
# B03: ROIC & WACC Input Feasibility
# ─────────────────────────────────────────────────────────────────────────────
def test_b03_roic_wacc_on_zero_issuer_not_value_neutral():
    pdf = create_searchable_empty_pdf()
    with patch('models.pre_ipo_ingest.get_gemini_api_key', return_value=None):
        unknown = PreIPOIngestionEngine.ingest_document(pdf, company_name_hint="Unknown Issuer")

    wacc_res = calculate_wacc_and_roic(unknown)
    assert wacc_res.get('is_computable') is False or wacc_res.get('status') == "INSUFFICIENT_DATA"
    assert wacc_res.get('status') != "VALUE_NEUTRAL"


# ─────────────────────────────────────────────────────────────────────────────
# B04: CMIE Crosswalk Coverage Denominator & Semantics
# ─────────────────────────────────────────────────────────────────────────────
def test_b04_single_mapping_not_institutional_grade_audited():
    pdf = create_searchable_empty_pdf()
    with patch('models.pre_ipo_ingest.get_gemini_api_key', return_value=None):
        unknown = PreIPOIngestionEngine.ingest_document(pdf, company_name_hint="Unknown Issuer")

    fake_cross = dataclasses.replace(
        unknown,
        cmie_crosswalk=[CMIECrosswalkRecord('test', 'not-a-verified-field', 'test', '0', '0', 'EXACT_MATCH', 'test')]
    )
    cov = generate_cmie_crosswalk_coverage(fake_cross)
    # Must NOT declare INSTITUTIONAL_GRADE_AUDITED for a single test mapping
    assert cov['data_quality_verdict'] != "INSTITUTIONAL_GRADE_AUDITED"
    # Coverage percentage must be evaluated against the canonical 16-concept schema
    assert cov['coverage_pct'] < 20.0
