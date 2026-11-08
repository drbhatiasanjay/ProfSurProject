"""Unit tests for the 74-family field binding registry and model adapter.
"""
from models.pre_ipo_field_registry import (
    FIELD_REGISTRY,
    get_field_spec,
    list_fields_by_profile,
    PreIPOModelAdapter
)


def test_field_registry_loaded_and_complete():
    # Verify the register contains all 74 entries
    assert len(FIELD_REGISTRY) == 74

    # Check key profiles
    financial_fields = list_fields_by_profile("FINANCIAL")
    assert len(financial_fields) >= 20
    assert any(f.canonical_id == "financial.revenue_operations" for f in financial_fields)
    assert any(f.canonical_id == "financial.ebitda_reported" for f in financial_fields)

    debt_fields = list_fields_by_profile("DEBT")
    assert len(debt_fields) >= 3
    assert any(f.canonical_id == "debt.facilities" for f in debt_fields)

    lease_fields = list_fields_by_profile("LEASE")
    assert len(lease_fields) >= 3
    assert any(f.canonical_id == "lease.liability_movement" for f in lease_fields)


def test_model_adapter_from_observations():
    sample_obs = [
        {"metric_id": "financial.revenue_operations", "period": "FY24", "value": "1234.0"},
        {"metric_id": "financial.ebitda_reported", "period": "FY24", "value": "234.0"},
        {"metric_id": "financial.pat", "period": "FY24", "value": "89.0"},
        {"metric_id": "financial.equity_and_retained_earnings", "period": "FY24", "value": "678.0"},
        {"metric_id": "debt.facilities.secured_term_loans", "value": "200.0"},
        {"metric_id": "debt.cash_restrictions.cash_and_equivalents", "value": "50.0"},
    ]

    dossier = PreIPOModelAdapter.observations_to_dossier("Acme Test Corp", sample_obs)
    assert dossier.company_name == "Acme Test Corp"
    assert len(dossier.history) == 1
    assert dossier.history[0].revenue_ops_cr == 1234.0
    assert dossier.history[0].ebitda_cr == 234.0
    assert dossier.history[0].net_worth_cr == 678.0
    assert dossier.indebtedness.secured_term_loans_cr == 200.0
    assert dossier.indebtedness.cash_and_equivalents_cr == 50.0

    analytics = PreIPOModelAdapter.extract_analytical_inputs(sample_obs)
    assert analytics["revenue_ops_cr"] == 1234.0
    assert analytics["ebitda_cr"] == 234.0
    assert analytics["net_debt_cr"] == 150.0  # 200 - 50
    assert analytics["is_eligible_for_underwriting"] is True
