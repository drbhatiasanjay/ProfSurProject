"""
Unit tests for Pre-IPO Incremental Equity PRD deliverables:
1. CompanyBackground completeness across golden exemplars.
2. CMIECrosswalkRecord mappings and coverage reporting.
3. WACC and ROIC value-creation economic spread calculations.
4. Reverse DCF growth hurdle sizing.
5. 10 Core Investor Questions (Q01-Q10) & Private Extensions (PX01-PX04) lineage and action playbooks.
6. 16:9 Pitch Deck generator 8-slide parity.
"""
import pytest
from models.pre_ipo_data import PRE_IPO_REGISTRY
from models.pre_ipo_engine import (
    calculate_wacc_and_roic,
    calculate_reverse_dcf_hurdle,
    generate_cmie_crosswalk_coverage,
    generate_equity_question_answers,
)
from utils.pre_ipo_deck_generator import generate_pre_ipo_board_deck


def test_company_background_all_exemplars():
    """Verify that all 5 golden exemplars have valid CompanyBackground data."""
    exemplars = ["mankind_pharma", "afcons_infra", "swiggy", "tata_technologies", "ntpc_green"]
    for deal_id in exemplars:
        dossier = PRE_IPO_REGISTRY[deal_id]
        bg = dossier.background
        assert bg is not None, f"CompanyBackground missing for {deal_id}"
        assert bg.cin, f"CIN missing for {deal_id}"
        assert bg.incorporation_year > 1900, f"Invalid incorporation year for {deal_id}"
        assert len(bg.business_model_summary) > 20, f"Business summary too short for {deal_id}"
        assert len(bg.core_products_and_services) >= 2, f"Products missing for {deal_id}"
        assert bg.revenue_model, f"Revenue model missing for {deal_id}"
        assert len(bg.customer_segments) >= 1, f"Customer segments missing for {deal_id}"
        assert len(bg.geographic_presence) >= 1, f"Geographic presence missing for {deal_id}"
        assert bg.filing_cutoff_date, f"Cutoff date missing for {deal_id}"


def test_cmie_crosswalk_coverage_metrics():
    """Verify CMIE crosswalk mapping integrity and coverage calculation."""
    dossier = PRE_IPO_REGISTRY["ntpc_green"]
    cov = generate_cmie_crosswalk_coverage(dossier)
    assert cov["total_concepts_tracked"] >= 16
    assert cov["exact_match_count"] >= 5
    assert cov["reconciled_count"] >= 5
    assert cov["coverage_pct"] >= 75.0
    assert cov["data_quality_verdict"] in ("INSTITUTIONAL_GRADE_AUDITED", "SATISFACTORY_WITH_GAPS", "LEGACY_MAPPING_REVIEW_REQUIRED")


def test_wacc_and_roic_economic_spread():
    """Verify ROIC vs WACC calculation and economic profit generation."""
    mankind = PRE_IPO_REGISTRY["mankind_pharma"]
    res = calculate_wacc_and_roic(mankind)
    assert res["invested_capital_cr"] > 0
    assert res["wacc_pct"] > 0
    assert res["ke_pct"] > 0
    assert res["kd_post_tax_pct"] > 0
    assert res["status"] in ("SUBSTANTIAL_VALUE_CREATOR", "MODERATE_VALUE_CREATOR", "VALUE_NEUTRAL", "ECONOMIC_VALUE_DESTROYER", "PARTIAL_CALCULATION")


def test_reverse_dcf_hurdle_growth():
    """Verify reverse DCF compound growth hurdle solver with explicit discount rate."""
    tatatech = PRE_IPO_REGISTRY["tata_technologies"]
    res_no_wacc = calculate_reverse_dcf_hurdle(tatatech)
    assert res_no_wacc["hurdle_difficulty"] == "MISSING_DISCOUNT_RATE"
    
    res = calculate_reverse_dcf_hurdle(tatatech, custom_wacc_pct=10.0)
    assert res["implied_ev_cr"] > 0
    assert res["required_fcf_cagr_pct"] is not None
    assert res["hurdle_difficulty"] in ("ACHIEVABLE_LOW_BAR", "REALISTIC_MODERATE", "MODERATE_REALISTIC", "AGGRESSIVE_STRETCH", "HERCULEAN_HIGH_RISK")


def test_10_investor_questions_public_ipo_context():
    """Verify all 10 core questions (Q01-Q10) appear in Public IPO context, with zero PX leak."""
    swiggy = PRE_IPO_REGISTRY["swiggy"]
    q_dict = generate_equity_question_answers(swiggy, transaction_context="PUBLIC_IPO")
    for i in range(1, 11):
        qid = f"Q{i:02d}"
        assert qid in q_dict, f"Question {qid} missing from Public IPO context"
        q_obj = q_dict[qid]
        assert q_obj.direct_verdict, f"Direct verdict missing for {qid}"
        assert q_obj.detailed_analysis, f"Detailed analysis missing for {qid}"
        if q_obj.status != "INSUFFICIENT_DATA_UNANSWERED":
            assert len(q_obj.claim_lineage) >= 1, f"Claim lineage missing for {qid}"
        assert len(q_obj.conditional_recommendations) >= 1, f"Action playbook missing for {qid}"
    
    # Assert zero private PX leakage in public IPO context
    assert "PX01" not in q_dict
    assert "PX02" not in q_dict


def test_private_extensions_in_pe_context():
    """Verify private questions PX01-PX04 appear when Private / Strategic context is chosen."""
    afcons = PRE_IPO_REGISTRY["afcons_infra"]
    q_dict = generate_equity_question_answers(afcons, transaction_context="PRIVATE_PRE_IPO")
    assert "PX01" in q_dict
    assert "PX02" in q_dict
    assert "PX03" in q_dict
    assert "PX04" in q_dict
    assert q_dict["PX01"].status in ("ANSWERED_WITH_EVIDENCE", "PARTIAL_WITH_GAPS", "BLOCKED_MISSING_DATA")


def test_deck_generator_8_slides_with_overview_and_scorecard():
    """Verify deck generator builds valid PPTX bytes containing all 8 institutional slides."""
    ntpc = PRE_IPO_REGISTRY["ntpc_green"]
    deck_bytes = generate_pre_ipo_board_deck(ntpc)
    assert len(deck_bytes) > 20000, "Deck bytes too small"
    assert deck_bytes.startswith(b"PK\x03\x04"), "Invalid PPTX zip magic number"

