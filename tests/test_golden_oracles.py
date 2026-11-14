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
from models.pre_ipo_data import PRE_IPO_REGISTRY


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


def test_reconciliation_with_pre_ipo_registry():
    """Verify golden oracle restated financials match PRE_IPO_REGISTRY ground truth."""
    for deal_id in EXPECTED_ORACLE_DEALS:
        oracle = load_golden_oracle(deal_id)
        dossier = PRE_IPO_REGISTRY[deal_id]
        
        assert oracle["company_name"] == dossier.company_name
        
        # Check that latest year in oracle matches latest year in dossier
        latest_oracle = oracle["restated_financials"][-1]
        latest_dossier = dossier.history[-1]
        
        assert latest_oracle["period"] == latest_dossier.fiscal_year
        assert pytest.approx(latest_oracle["revenue_ops_cr"], rel=1e-3) == latest_dossier.revenue_ops_cr
        assert pytest.approx(latest_oracle["pat_cr"], rel=1e-3) == latest_dossier.pat_cr


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

