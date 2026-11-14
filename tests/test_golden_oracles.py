"""Adversarial Red-Team & Validation Suite for Pre-IPO Declarative Golden Oracles.

Tests Item 5:
1. All 6 prospectuses have a declarative golden oracle JSON file under data/golden_oracles/.
2. Oracles satisfy strict schema validation (types, required fields, numerical positivity).
3. Cryptographic SHA-256 hash validation detects file corruption or tampering.
4. Financial metrics in oracles reconcile with PRE_IPO_REGISTRY ground truth.
5. Fail-closed error handling when oracle is missing, malformed, or tampered.
"""

import json
import pytest
from pathlib import Path
from models.pre_ipo_golden_loader import (
    load_golden_oracle,
    validate_oracle_schema,
    verify_oracle_sha,
    get_all_oracles,
    GoldenOracleError,
    GOLDEN_ORACLE_DIR,
    EXPECTED_ORACLE_DEALS,
)


def test_all_expected_oracles_exist_and_load():
    """Verify all 6 canonical prospectuses have loadable golden oracles."""
    assert len(EXPECTED_ORACLE_DEALS) == 6
    for deal_id in EXPECTED_ORACLE_DEALS:
        oracle = load_golden_oracle(deal_id)
        assert oracle is not None
        assert oracle["deal_id"] == deal_id
        assert "company_name" in oracle
        assert "filing_type" in oracle
        assert "restated_financials" in oracle
        assert len(oracle["restated_financials"]) >= 3


def test_schema_validation_strict_types():
    """Test that schema validation enforces required keys and numeric types."""
    for deal_id in EXPECTED_ORACLE_DEALS:
        oracle = load_golden_oracle(deal_id)
        is_valid, errors = validate_oracle_schema(oracle)
        assert is_valid, f"Oracle {deal_id} failed schema validation: {errors}"


def test_statutory_corpus_reconciliation_and_semantic_absence():
    """Verify golden oracles conform to statutory filing citations and semantic absence (P0-03, P1-02)."""
    # 1. Independent validation: zero circular imports or dependency on unreviewed PRE_IPO_REGISTRY
    hcch = load_golden_oracle("hindustan_coca_cola")

    assert hcch["company_name"] == "Hindustan Coca-Cola Holdings Limited"
    assert hcch["filing_type"] == "DRHP"
    assert hcch["face_value_inr"] == 10.0

    # 2. Offer Details: Unpriced book-building under SEBI ICDR Reg 26(1)
    offer = hcch["offer_details"]
    assert offer["total_issue_size_cr"] is None, "HCCH total issue size must be None (unpriced book-built), never 0.0"
    assert offer["fresh_issue_cr"] == 0.0, "HCCH fresh issue is 0.0 (100% OFS)"
    assert offer["ofs_cr"] is None, "HCCH OFS size must be None (unpriced), never 0.0"
    assert offer["offered_shares_count"] == 997461456
    assert offer["fresh_issue_pct"] == 0.0
    assert offer["ofs_pct"] == 100.0

    # 3. Semantic absence disclosures
    disclosures = {d["metric_id"]: d for d in hcch.get("semantic_disclosures", [])}
    assert "pre_ipo_placement_price" in disclosures
    assert disclosures["pre_ipo_placement_price"]["presence"] == "NOT_DISCLOSED"
    assert disclosures["pre_ipo_placement_price"]["value"] is None

    assert "funded_bank_debt_cr" in disclosures
    assert disclosures["funded_bank_debt_cr"]["presence"] == "DISCLOSED_ZERO"
    assert disclosures["funded_bank_debt_cr"]["value"] == 0.0

    # 4. Restated Financials: Cash and cash equivalents are positive numbers, never false zeros
    fin_map = {f["period"]: f for f in hcch["restated_financials"]}
    assert fin_map["FY24"]["cash_and_equiv_cr"] == 138.95
    assert fin_map["FY25"]["cash_and_equiv_cr"] == 132.97
    assert fin_map["FY26"]["cash_and_equiv_cr"] == 431.96

    # 5. Citations point to authentic 513-page DRHP Annexures
    assert fin_map["FY26"]["physical_page"] == 275
    assert fin_map["FY26"]["printed_folio"] == "Page 270"
    assert "Annexure II" in fin_map["FY26"]["section"]


def test_adversarial_semantic_absence_rejects_false_zeros():
    """Adversarial check: Schema validation rejects NOT_DISCLOSED with numeric 0.0 or DISCLOSED_ZERO with non-zero."""
    # Fault 1: Setting value to 0.0 when presence is NOT_DISCLOSED
    bad_oracle_unpriced_zero = {
        "deal_id": "test_unpriced",
        "company_name": "Test Co",
        "filing_type": "DRHP",
        "restated_financials": [
            {"period": "FY26", "revenue_ops_cr": 100.0, "pat_cr": 10.0}
        ],
        "semantic_disclosures": [
            {
                "metric_id": "pre_ipo_placement_price",
                "presence": "NOT_DISCLOSED",
                "value": 0.0,  # ILLEGAL: NOT_DISCLOSED must have value None
                "citation": "Unpriced filing"
            }
        ]
    }
    is_valid, errors = validate_oracle_schema(bad_oracle_unpriced_zero)
    assert not is_valid
    assert any("NOT_DISCLOSED but value is not None" in e for e in errors)

    # Fault 2: Setting value to 15.0 when presence is DISCLOSED_ZERO
    bad_oracle_disclosed_zero = {
        "deal_id": "test_zero",
        "company_name": "Test Co",
        "filing_type": "DRHP",
        "restated_financials": [
            {"period": "FY26", "revenue_ops_cr": 100.0, "pat_cr": 10.0}
        ],
        "semantic_disclosures": [
            {
                "metric_id": "funded_bank_debt_cr",
                "presence": "DISCLOSED_ZERO",
                "value": 15.0,  # ILLEGAL: DISCLOSED_ZERO must be 0.0
                "citation": "Debt table"
            }
        ]
    }
    is_valid2, errors2 = validate_oracle_schema(bad_oracle_disclosed_zero)
    assert not is_valid2
    assert any("DISCLOSED_ZERO but value is not 0.0" in e for e in errors2)


def test_adversarial_tamper_detection(tmp_path):
    """Adversarial check: Modifying one byte in an oracle fails SHA verification."""
    test_deal = "hindustan_coca_cola"
    oracle_file = GOLDEN_ORACLE_DIR / f"{test_deal}_golden.json"
    
    # Read original hash
    original_sha = verify_oracle_sha(oracle_file)
    assert len(original_sha) == 64
    
    # Tamper with file copy
    tampered_file = tmp_path / f"{test_deal}_golden.json"
    content = oracle_file.read_text(encoding="utf-8")
    tampered_content = content.replace("14021.55", "99999.99")
    tampered_file.write_text(tampered_content, encoding="utf-8")
    
    # Assert hash verification against original hash fails
    with pytest.raises(GoldenOracleError, match="Cryptographic mismatch|tampered"):
        verify_oracle_sha(tampered_file, expected_sha=original_sha)


def test_adversarial_malformed_schema_fails_closed():
    """Adversarial check: Incomplete or malformed oracle dict raises GoldenOracleError."""
    # Missing required field 'deal_id'
    bad_oracle = {"company_name": "Ghost Corp"}
    is_valid, errors = validate_oracle_schema(bad_oracle)
    assert not is_valid
    assert any("deal_id" in err for err in errors)

    # Negative revenue
    bad_financials = {
        "deal_id": "ghost",
        "company_name": "Ghost",
        "filing_type": "DRHP",
        "restated_financials": [
            {"period": "FY24", "revenue_ops_cr": -50.0, "ebitda_cr": 10.0, "pat_cr": 5.0}
        ]
    }
    is_valid, errors = validate_oracle_schema(bad_financials)
    assert not is_valid
    assert any("negative" in err.lower() or "revenue" in err.lower() for err in errors)


def test_fail_closed_on_nonexistent_deal():
    """Verify non-existent deal ID raises FileNotFoundError / GoldenOracleError."""
    with pytest.raises(GoldenOracleError, match="not found|does not exist"):
        load_golden_oracle("nonexistent_deal_xyz")

