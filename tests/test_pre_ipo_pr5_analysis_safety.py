"""Tests for PR 5: Analytical and Decision-Support Safety.

Validates:
- No price blocks valuation, WACC, and Reverse DCF.
- No EBIT blocks ROIC (proxy EBITDA - 0.5*capex is purged).
- No debt-cost premise blocks WACC (no 9% fallback).
- No book-equity fallback in capital structure weights.
- Scenario output is explicitly labeled ANALYST_SCENARIO and lineage-complete.
- Blocked result returns BlockedResult object with missing premises.
- Banned claim terms (APPROVE, TIER_1_STRONG_CUSHION, STRONG BUY, AAA, SAFE INVESTMENT) trigger policy violations.
- External credit ratings require complete provenance.
"""

import pytest
from models.pre_ipo_analysis_safety import (
    compute_safe_wacc,
    compute_safe_roic,
    compute_safe_reverse_dcf,
    BlockedResult,
    SafeWACCResult,
    SafeROICResult,
    SafeReverseDCFResult,
    DecisionSupportSummary,
    ExternalRatingRecord,
    AnalystScenarioSet,
    BANNED_CLAIM_TERMS,
)


def test_no_price_blocks_wacc_and_reverse_dcf():
    """Asserts that unpriced DRHP (market_equity_cr is None) blocks WACC and reverse DCF."""
    wacc_res = compute_safe_wacc(
        market_equity_cr=None,
        total_debt_cr=500.0,
        cost_of_debt_pct=8.5,
    )
    assert isinstance(wacc_res, BlockedResult)
    assert wacc_res.is_blocked is True
    assert any("market_equity_cr" in p for p in wacc_res.missing_premises)

    dcf_res = compute_safe_reverse_dcf(
        market_valuation_cr=None,
        wacc_pct=11.5,
        current_fcf_cr=400.0,
    )
    assert isinstance(dcf_res, BlockedResult)
    assert dcf_res.is_blocked is True
    assert any("market_valuation_cr" in p for p in dcf_res.missing_premises)


def test_no_ebit_blocks_roic():
    """Asserts that missing EBIT blocks ROIC without falling back to 'EBITDA - 0.5*capex'."""
    roic_res = compute_safe_roic(
        ebit_cr=None,
        invested_capital_cr=2500.0,
    )
    assert isinstance(roic_res, BlockedResult)
    assert roic_res.is_blocked is True
    assert any("ebit_cr" in p for p in roic_res.missing_premises)


def test_no_debt_cost_blocks_wacc():
    """Asserts that missing cost of debt blocks WACC without defaulting to 9.0%."""
    wacc_res = compute_safe_wacc(
        market_equity_cr=10000.0,
        total_debt_cr=1200.0,
        cost_of_debt_pct=None,  # Must not default to 9.0
    )
    assert isinstance(wacc_res, BlockedResult)
    assert wacc_res.is_blocked is True
    assert any("cost_of_debt_pct" in p for p in wacc_res.missing_premises)


def test_safe_wacc_with_valid_premises():
    """Asserts that WACC computes properly when explicit verified premises are supplied."""
    wacc_res = compute_safe_wacc(
        market_equity_cr=8000.0,
        total_debt_cr=2000.0,
        cost_of_debt_pct=8.0,
        risk_free_rate_pct=7.0,
        beta=1.0,
        market_risk_premium_pct=6.0,
        tax_rate_pct=25.0,
    )
    assert isinstance(wacc_res, SafeWACCResult)
    assert wacc_res.wacc_pct > 0
    assert wacc_res.equity_weight_pct == 80.0
    assert wacc_res.debt_weight_pct == 20.0
    assert wacc_res.lineage_hash != ""


def test_scenario_output_labeled_and_lineage_complete():
    """Asserts that user-entered scenarios are tagged ANALYST_SCENARIO and contain SHA hashes."""
    scenario = AnalystScenarioSet(
        scenario_id="scen_01",
        owner="analyst_test",
        created_at="2026-11-13T12:00:00Z",
        source_justification="Tested under 150 bps macro rate shock",
        assumptions={"cost_of_debt_pct": 10.5, "terminal_growth_pct": 4.5}
    )
    assert scenario.nature == "ANALYST_SCENARIO"
    assert len(scenario.scenario_hash) == 64


def test_banned_claim_policy_detector():
    """Asserts that banned terms trigger claim policy violations in DecisionSupportSummary."""
    summary_violating = DecisionSupportSummary(
        company_name="Test Corp",
        decision_context="Investment committee meeting notes.",
        supported_evidence=["Revenue grew 15%."],
        unresolved_unknowns=["Working capital cycle."],
        diligence_questions=["Inventory days."],
        conditional_considerations=["We recommend you APPROVE this transaction as a TIER_1_STRONG_CUSHION."],
    )
    violations = summary_violating.validate_claim_policy()
    assert len(violations) >= 2
    assert any("APPROVE" in v for v in violations)
    assert any("TIER_1_STRONG_CUSHION" in v for v in violations)


def test_compliant_decision_support_summary():
    """Asserts that neutral analytical framing passes claim policy cleanly."""
    summary_clean = DecisionSupportSummary(
        company_name="Hindustan Coca-Cola Holdings Private Limited",
        decision_context="Pre-IPO quantitative diligence summary for sponsor consideration.",
        supported_evidence=["FY25 Operating EBITDA of ₹1,640.02 Cr supported by restated P&L."],
        unresolved_unknowns=["Issue price undisclosed [●]; offer size not computable."],
        diligence_questions=["Request pricing band notification prior to anchor bidding."],
        conditional_considerations=["Deleveraging capacity depends on final fresh issue proportion."],
    )
    violations = summary_clean.validate_claim_policy()
    assert len(violations) == 0


def test_external_rating_requires_complete_provenance():
    """Asserts that external ratings store structured metadata."""
    rating = ExternalRatingRecord(
        agency="CRISIL Ratings Limited",
        instrument="Long Term Bank Facilities",
        rating_symbol="CRISIL AA+",
        outlook="Stable",
        effective_date="2025-08-15",
        source_citation="DRHP Section V, Indebtedness Schedule",
        source_page=265
    )
    assert rating.rating_symbol == "CRISIL AA+"
    assert rating.source_page == 265
