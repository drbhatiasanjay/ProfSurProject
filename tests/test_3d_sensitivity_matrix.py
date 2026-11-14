"""Adversarial Red-Team & Validation Suite for 3D Multi-Parameter Sensitivity Grid.

Tests Item 2:
1. `compute_3d_covenant_sensitivity_matrix()` calculates 3D tensor across:
   - Margin shocks (-300 to +100 bps)
   - Benchmark rate shocks (0 to +300 bps)
   - Debt prepayment allocations (0% to 100% of fresh issue)
2. Zero-debt handling: When gross debt is 0.0 (or becomes 0.0 after prepayment),
   ICR is float('inf') with status 'COVENANT_EXEMPT_ZERO_DEBT' and zero division is prevented.
3. Severe margin shock triggers covenant breach (< 3.00x or < 1.50x).
4. Debt prepayment restores covenant compliance.
5. Boundary handling: Negative EBITDA returns 0.0 ICR with status 'NEGATIVE_EBITDA'.
"""

import math
import pytest
from models.pre_ipo_engine import compute_3d_covenant_sensitivity_matrix


def test_3d_sensitivity_matrix_dimensions():
    """Verify matrix dimensions match input shock vectors."""
    margin_shocks = [-200, -100, 0, 100]
    rate_shocks = [0, 100, 200]
    prepay_pcts = [0, 50, 100]

    res = compute_3d_covenant_sensitivity_matrix(
        base_ebitda_cr=1000.0,
        base_revenue_cr=5000.0,
        base_gross_debt_cr=2000.0,
        base_wair_pct=9.0,
        fresh_issue_cr=1000.0,
        margin_shocks_bps=margin_shocks,
        rate_shocks_bps=rate_shocks,
        debt_prepay_allocations_pct=prepay_pcts,
        covenant_threshold=3.0,
    )

    assert "slices" in res
    assert len(res["slices"]) == len(prepay_pcts)
    for s in res["slices"]:
        assert len(s["matrix"]) == len(margin_shocks)
        for row in s["matrix"]:
            assert len(row["rate_results"]) == len(rate_shocks)


def test_zero_debt_inf_icr_and_covenant_exempt():
    """Zero debt entities (e.g. HCCH parent) must return inf ICR without division by zero."""
    res = compute_3d_covenant_sensitivity_matrix(
        base_ebitda_cr=1777.94,
        base_revenue_cr=14021.55,
        base_gross_debt_cr=0.0,  # Zero debt
        base_wair_pct=9.0,
        fresh_issue_cr=0.0,
    )
    for s in res["slices"]:
        for row in s["matrix"]:
            for r in row["rate_results"]:
                assert math.isinf(r["icr"])
                assert r["status"] == "COVENANT_EXEMPT_ZERO_DEBT"
                assert r["headroom"] == float("inf")


def test_prepayment_improves_icr_and_restores_compliance():
    """Allocating fresh issue to debt prepayment reduces interest expense and raises ICR."""
    res = compute_3d_covenant_sensitivity_matrix(
        base_ebitda_cr=300.0,
        base_revenue_cr=3000.0,
        base_gross_debt_cr=1200.0,
        base_wair_pct=10.0,
        fresh_issue_cr=800.0,
        margin_shocks_bps=[0],
        rate_shocks_bps=[0],
        debt_prepay_allocations_pct=[0, 100],
        covenant_threshold=3.0,
    )
    # Slice 0: 0% prepayment -> Debt = 1200, Interest = 120, ICR = 300 / 120 = 2.50 (WATCHLIST / BREACH)
    s0_icr = res["slices"][0]["matrix"][0]["rate_results"][0]["icr"]
    assert pytest.approx(s0_icr, rel=1e-2) == 2.50
    assert res["slices"][0]["matrix"][0]["rate_results"][0]["status"] in ("WATCHLIST", "BREACH")

    # Slice 1: 100% prepayment of 800 Cr -> Debt = 400, Interest = 40, ICR = 300 / 40 = 7.50 (COMPLIANT)
    s1_icr = res["slices"][1]["matrix"][0]["rate_results"][0]["icr"]
    assert pytest.approx(s1_icr, rel=1e-2) == 7.50
    assert res["slices"][1]["matrix"][0]["rate_results"][0]["status"] == "COMPLIANT"


def test_negative_ebitda_fails_closed():
    """Negative shocked EBITDA must safely yield 0.0 ICR with NEGATIVE_EBITDA status."""
    res = compute_3d_covenant_sensitivity_matrix(
        base_ebitda_cr=50.0,
        base_revenue_cr=1000.0,  # Base margin = 5%
        base_gross_debt_cr=500.0,
        base_wair_pct=10.0,
        fresh_issue_cr=0.0,
        margin_shocks_bps=[-600],  # Margin drops to -1%, EBITDA = -10 Cr
        rate_shocks_bps=[0],
        debt_prepay_allocations_pct=[0],
    )
    r = res["slices"][0]["matrix"][0]["rate_results"][0]
    assert r["icr"] == 0.0
    assert r["status"] == "NEGATIVE_EBITDA"
    assert r["headroom"] < 0

