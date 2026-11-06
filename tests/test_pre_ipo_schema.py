"""
Unit tests for Pre-IPO DRHP Schemas, Data Registry, and Econometric Engine.
Verifies first-time-right contracts and defensive mathematical edge cases.
"""
import pytest
from models.pre_ipo_data import PRE_IPO_REGISTRY
from models.pre_ipo_engine import (
    classify_dickinson_stage,
    compute_debt_capacity,
    calculate_beneish_m_score,
    generate_2d_sensitivity_matrix,
)


def test_pre_ipo_registry_loads_all_four_deals():
    assert len(PRE_IPO_REGISTRY) == 4
    expected_keys = {"mankind_pharma", "afcons_infra", "swiggy", "tata_technologies"}
    assert set(PRE_IPO_REGISTRY.keys()) == expected_keys


def test_mankind_pharma_deal_structure():
    deal = PRE_IPO_REGISTRY["mankind_pharma"]
    assert deal.company_name == "Mankind Pharma Limited"
    assert deal.total_issue_size_cr == 4326.36
    assert deal.fresh_issue_cr == 0.0
    assert deal.ofs_cr == 4326.36
    assert deal.fresh_issue_pct == 0.0
    assert deal.ofs_pct == 100.0
    assert len(deal.history) >= 3

    # Indebtedness
    assert deal.indebtedness.funded_bank_debt_cr == pytest.approx(1568.42, rel=1e-3)
    assert deal.indebtedness.lease_liabilities_ind_as_116_cr == 242.0
    assert deal.indebtedness.total_economic_indebtedness_cr == pytest.approx(1810.42, rel=1e-3)
    assert deal.indebtedness.net_funded_debt_cr == pytest.approx(308.42, rel=1e-3)


def test_afcons_infra_debt_prepayment():
    deal = PRE_IPO_REGISTRY["afcons_infra"]
    assert deal.fresh_issue_cr == 1250.0
    assert deal.indebtedness.funded_bank_debt_cr == pytest.approx(4188.0, rel=1e-3)
    # Post debt prepayment
    post_debt = deal.indebtedness.funded_bank_debt_cr - deal.fresh_issue_cr
    assert post_debt == pytest.approx(2938.0, rel=1e-3)


def test_dickinson_stage_classification():
    # Mature Cash Cow (+, -, -)
    stage, pattern = classify_dickinson_stage(1488.23, -384.01, -412.05)
    assert stage == "Mature (Cash Cow)"
    assert pattern == "(+, -, -)"

    # Introduction / Burn (-, -, +)
    stage_swiggy, pattern_swiggy = classify_dickinson_stage(-1050.2, -450.0, 1840.0)
    assert stage_swiggy == "Introduction"
    assert pattern_swiggy == "(-, -, +)"


def test_compute_debt_capacity_mankind():
    deal = PRE_IPO_REGISTRY["mankind_pharma"]
    latest = deal.latest_financials
    res = compute_debt_capacity(
        ebitda_cr=latest.ebitda_cr,
        cfo_cr=latest.cfo_cr,
        capex_cr=latest.capex_cr,
        wair_pct=deal.indebtedness.weighted_avg_interest_rate_pct or 8.5,
        current_gross_debt_cr=deal.indebtedness.funded_bank_debt_cr,
        cash_cr=deal.indebtedness.cash_and_equivalents_cr,
        target_leverage_ceiling=2.5,
    )
    assert res["max_sustainable_debt_cr"] > 0
    assert res["incremental_mna_headroom_cr"] >= 1800.0  # Proves Mankind's massive M&A buffer
    assert res["current_net_debt_ebitda"] is not None
    assert res["current_icr"] is not None


def test_compute_debt_capacity_negative_ebitda_defensive():
    # Negative EBITDA company should not crash or produce invalid ratios
    res = compute_debt_capacity(
        ebitda_cr=-2208.0,
        cfo_cr=-1050.0,
        capex_cr=310.0,
        wair_pct=10.2,
        current_gross_debt_cr=210.0,
        cash_cr=3420.0,
    )
    assert res["max_sustainable_debt_cr"] == 0.0
    assert res["incremental_mna_headroom_cr"] == 0.0
    assert res["current_net_debt_ebitda"] is None
    assert res["current_icr"] is None


def test_2d_sensitivity_matrix_generation():
    matrix = generate_2d_sensitivity_matrix(
        base_ebitda_cr=1913.24,
        gross_debt_cr=1568.42,
        base_wair_pct=8.45,
    )
    assert len(matrix["matrix"]) == 6
    assert matrix["rate_hikes_bps"] == [0, 100, 200, 300]
    base_row = next(r for r in matrix["matrix"] if r["ebitda_shock_pct"] == 0)
    assert base_row["hike_0bps"] > 10.0  # Base ICR > 10x
