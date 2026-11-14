"""Comprehensive tests for PR 4: Correct HCCH Financial Semantics.

Validates:
- [●] parsed as NOT_DISCLOSED.
- Face value rejected as issue price in book-building offer.
- Missing price blocks offer valuation and market cap.
- Cash-flow operating profit before working capital rejected as EBITDA.
- Capex rejected as CFI proxy.
- Observed zero is preserved and not coerced to negative.
- FY25 Dickinson stage classified as Growth from (+, -, +).
- Total equity with NCI rejected for Net Worth contract.
- HCCH comparison target numbers verified against audited references.
"""

import pytest
from models.pre_ipo_financial_contracts import (
    parse_prospectus_token,
    validate_offer_contract,
    validate_ebitda_metric,
    validate_cash_flow_inputs,
    validate_net_worth_contract,
    MetricDefinition,
    DickinsonLifeCycle,
    HCCH_AUDITED_TARGETS,
)


def test_prospectus_bracket_dot_parsed_as_not_disclosed():
    """Asserts that [●] or '●' or 'undisclosed' are parsed as NOT_DISCLOSED."""
    val, pres = parse_prospectus_token("[●]")
    assert val is None
    assert pres == "NOT_DISCLOSED"

    val2, pres2 = parse_prospectus_token("●")
    assert val2 is None
    assert pres2 == "NOT_DISCLOSED"


def test_observed_zero_is_not_missing_or_negative():
    """Asserts that explicit nil/zero is preserved as 0.0 with EXPLICIT_NIL, not negative."""
    val, pres = parse_prospectus_token("-")
    assert val == 0.0
    assert pres == "EXPLICIT_NIL"

    val_zero, pres_zero = parse_prospectus_token("0.00")
    assert val_zero == 0.0
    assert pres_zero == "OBSERVED_VALUE"
    assert val_zero >= 0.0


def test_face_value_rejected_as_issue_price():
    """Asserts that face value (e.g. Rs 10.0 or Rs 1.0) cannot be substituted for offer price."""
    res = validate_offer_contract(
        face_value_inr=10.0,
        issue_price_inr=10.0,
        total_shares=997461456.0
    )
    assert res["valid"] is False
    assert "Face value cannot be used as issue price" in res["error"]


def test_no_price_blocks_offer_value_and_market_cap():
    """Asserts that an unpriced filing blocks offer valuation and market cap."""
    res = validate_offer_contract(
        face_value_inr=10.0,
        issue_price_inr=None,
        total_shares=997461456.0
    )
    assert res["valid"] is True
    assert res["is_priced"] is False
    assert res["offer_value_cr"] is None
    assert res["market_cap_cr"] is None


def test_cash_flow_subtotal_rejected_as_ebitda():
    """Asserts that cash flow profit before working capital changes is rejected as EBITDA."""
    res = validate_ebitda_metric(
        metric_id=MetricDefinition.CF_PROFIT_BEFORE_WC.value,
        value=1640.02
    )
    assert res["accepted"] is False
    assert "REJECTED" in res["error"]

    res_valid = validate_ebitda_metric(
        metric_id=MetricDefinition.ISSUER_EBITDA.value,
        value=1640.02
    )
    assert res_valid["accepted"] is True
    assert res_valid["value"] == 1640.02


def test_capex_rejected_as_cfi():
    """Asserts that capex cannot satisfy net CFI contract."""
    res = validate_cash_flow_inputs(
        cfo=1500.0,
        cfi=None,
        cff=-200.0,
        capex_proxy=450.0
    )
    assert res["valid"] is False
    assert "Capex proxy substitution" in res["error"]


def test_fy25_growth_stage_from_accepted_signs():
    """
    Asserts that HCCH FY25 cash flows (+, -, +) correctly classify as Growth:
    CFO > 0, CFI = -2071.558 (< 0), CFF = +492.878 (> 0).
    """
    res = validate_cash_flow_inputs(
        cfo=1450.0,
        cfi=-2071.558,
        cff=492.878
    )
    assert res["valid"] is True
    assert res["dickinson_stage"] == DickinsonLifeCycle.GROWTH.value


def test_total_equity_rejected_for_net_worth_when_nci_present():
    """Asserts that total equity with NCI is rejected when SEBI Net Worth is required."""
    res = validate_net_worth_contract(
        metric_id=MetricDefinition.TOTAL_EQUITY_WITH_NCI.value,
        value=9760.91,
        nci=150.0
    )
    assert res["accepted"] is False
    assert "Total equity including NCI cannot satisfy Net Worth" in res["error"]

    res_valid = validate_net_worth_contract(
        metric_id=MetricDefinition.SEBI_NET_WORTH.value,
        value=9610.91
    )
    assert res_valid["accepted"] is True
    assert res_valid["net_worth_cr"] == 9610.91


def test_hcch_audited_targets_consistency():
    """Verifies that audited reference gold expectations are correctly documented."""
    assert HCCH_AUDITED_TARGETS["EBITDA"]["FY24"] == 1777.936
    assert HCCH_AUDITED_TARGETS["EBITDA"]["FY25"] == 1640.019
    assert HCCH_AUDITED_TARGETS["EBITDA"]["FY26"] == 1353.040

    assert HCCH_AUDITED_TARGETS["CFI"]["FY25"] == -2071.558
    assert HCCH_AUDITED_TARGETS["CFF"]["FY25"] == 492.878
    assert HCCH_AUDITED_TARGETS["NET_WORTH"]["FY25"] == 9649.798
