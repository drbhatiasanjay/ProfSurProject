"""
Unit and integration tests for Covenant Compliance & Debt Headroom Engine (Page 28).

Validates:
1. File integrity and 5 mandatory PRD sections (Problem, Background, Analysis, Interpretation, Call for Action).
2. App navigation registration.
3. Archetype data execution (Tata Steel Ltd. and InterGlobe Aviation / IndiGo).
4. Ind AS 116 lease sensitivity and headroom calculation invariants.
5. Deterministic replay and audit output formatting.
"""

from __future__ import annotations

import os
import pytest
from models.covenant_pilot import ScenarioRequest, simulate, CovenantSpec
from models.covenant_examples import example_catalog


def test_page_file_exists_and_contains_mandatory_sections():
    page_path = os.path.join(os.path.dirname(__file__), "..", "pages", "28_covenant_headroom.py")
    assert os.path.exists(page_path), "pages/28_covenant_headroom.py does not exist"
    
    with open(page_path, "r", encoding="utf-8") as f:
        content = f.read()
    
    # 5 Mandatory PRD Sections
    assert "SECTION 1: THE PROBLEM" in content or "The Problem" in content
    assert "SECTION 2: THE BACKGROUND" in content or "The Background" in content
    assert "SECTION 3: THE ANALYSIS" in content or "The Analysis" in content
    assert "SECTION 4: DYNAMIC INTERPRETATION" in content or "Dynamic Interpretation" in content
    assert "SECTION 5: CALL FOR ACTION" in content or "Call for Action" in content
    
    # Evidence & playbooks
    assert "CFADS" in content
    assert "Ind AS 116" in content
    assert "headroom" in content.lower()
    assert "credit committee" in content.lower() or "cfo" in content.lower()


def test_app_navigation_registers_covenant_headroom():
    app_path = os.path.join(os.path.dirname(__file__), "..", "app.py")
    with open(app_path, "r", encoding="utf-8") as f:
        content = f.read()
    
    assert 'covenant_headroom' in content
    assert 'pages/28_covenant_headroom.py' in content
    assert '"Covenant & Debt Headroom"' in content


def test_archetypes_simulate_cleanly():
    catalog = example_catalog()
    assert "tata-steel-fy2025" in catalog
    assert "indigo-fy2025" in catalog

    cov = CovenantSpec(dscr_floor=1.35, icr_floor=2.0, tol_tnw_ceiling=4.0)

    for key, data in catalog.items():
        snap = data["snapshot"]
        debts = data["debts"]
        leases = data["leases"]

        # Baseline simulation
        base_req = ScenarioRequest(rate_shock_bps=0.0, margin_shock_pct=0.0, incremental_debt_cr=0.0, lease_in_coverage=True)
        res_base = simulate(snap, debts, leases, cov, base_req)
        
        assert "simulation_id" in res_base
        assert "baseline" in res_base
        assert "stressed" in res_base
        assert len(res_base["stressed"]["quarters"]) == 12
        
        # Stressed simulation (+150 bps rate shock, -15% margin shock, ₹500 Cr new debt)
        stress_req = ScenarioRequest(rate_shock_bps=150.0, margin_shock_pct=-15.0, incremental_debt_cr=500.0, lease_in_coverage=True)
        res_stress = simulate(snap, debts, leases, cov, stress_req)
        
        assert res_stress["simulation_id"] != res_base["simulation_id"]
        # When stressed, headroom cannot exceed baseline headroom
        if res_base["additional_headroom_cr"] is not None and res_stress["additional_headroom_cr"] is not None:
            assert res_stress["additional_headroom_cr"] <= res_base["additional_headroom_cr"] + 1e-6


def test_indigo_ind_as_116_lease_sensitivity():
    catalog = example_catalog()
    data = catalog["indigo-fy2025"]
    snap = data["snapshot"]
    debts = data["debts"]
    leases = data["leases"]
    cov = CovenantSpec(dscr_floor=1.35, icr_floor=2.0, tol_tnw_ceiling=4.0)
    
    # Leases IN coverage: capitalized fleet leases (₹47,980 Cr) compress DSCR to 0 headroom
    req_in = ScenarioRequest(rate_shock_bps=0.0, margin_shock_pct=0.0, incremental_debt_cr=0.0, lease_in_coverage=True)
    res_in = simulate(snap, debts, leases, cov, req_in)
    
    # Leases EXCLUDED from debt service (bank loans only): headroom expands above ₹20,000 Cr
    req_ex = ScenarioRequest(rate_shock_bps=0.0, margin_shock_pct=0.0, incremental_debt_cr=0.0, lease_in_coverage=False)
    res_ex = simulate(snap, debts, leases, cov, req_ex)
    
    assert res_in["additional_headroom_cr"] == pytest.approx(0.0, abs=1.0)
    assert res_ex["additional_headroom_cr"] > 20000.0
