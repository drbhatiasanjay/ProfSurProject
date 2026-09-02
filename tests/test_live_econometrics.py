"""Tests for Live On-The-Fly Econometric & CFO Stress Simulation Engine.

Verifies:
1. run_live_econometric_model: Panel OLS, Fixed Effects, Random Effects, Hausman test diagnostics.
2. run_cfo_stress_simulation: Dynamic covenant floors, ICR, debt headroom (₹ Cr), and credit rating mapping.
3. Strict guardrails and error isolation.
"""
import pytest
from models.agent_tools import run_live_econometric_model, run_cfo_stress_simulation


def test_run_live_econometric_model_full_panel():
    """Test default Fixed Effects estimation on the full panel."""
    res = run_live_econometric_model(
        dependent_var="leverage",
        independent_vars=["profitability", "tangibility"],
        model_type="auto",
        panel_mode="thesis",
    )
    assert res["status"] == "success"
    assert "Two-Way Fixed Effects" in res["selected_model"] or "Fixed Effects" in res["selected_model"]
    assert res["sample"]["n_obs"] > 5000
    assert res["sample"]["n_firms"] > 300

    # Verify coefficients
    table = res["coefficients_table"]
    var_names = [r["variable"] for r in table]
    assert any("profitability" in v for v in var_names)
    assert any("tangibility" in v for v in var_names)

    # Verify Pecking Order negative coefficient on profitability
    prof_row = next(r for r in table if "profitability" in r["variable"])
    assert prof_row["coef"] < 0, "Profitability should have a negative coefficient under Pecking Order Theory"
    assert prof_row["is_significant"] is True

    # Verify Trade-Off positive coefficient on tangibility
    tang_row = next(r for r in table if "tangibility" in r["variable"])
    assert tang_row["coef"] > 0, "Tangibility should have a positive coefficient under Trade-Off Collateral Theory"

    # Verify diagnostics and guardrails
    assert "r_squared_within" in res["diagnostics"]
    assert res["diagnostics"]["hausman_chi2"] is not None
    assert "strict_limitations" in res["strict_guardrails"]
    assert len(res["strict_guardrails"]["strict_limitations"]) >= 3


def test_run_live_econometric_model_industry_subsample():
    """Test on-the-fly panel regression for an industry subsample (e.g. Automobiles post-2018)."""
    res = run_live_econometric_model(
        dependent_var="leverage",
        independent_vars=["profitability", "tangibility"],
        industry_group="Automobiles & Auto Ancillaries",
        year_start=2018,
        year_end=2025,
        panel_mode="thesis",
    )
    assert res["status"] == "success"
    assert res["sample"]["n_obs"] >= 15
    assert res["sample"]["n_firms"] >= 2
    assert "Automobiles" in res["sample"]["industry"]

    # Verify structure
    assert len(res["coefficients_table"]) >= 2
    assert "what_is_proven" in res["strict_guardrails"]


def test_run_live_econometric_model_insufficient_sample_fails_gracefully():
    """Test that requesting an impossible subset fails safely without raising uncaught exceptions."""
    res = run_live_econometric_model(
        dependent_var="leverage",
        independent_vars=["profitability"],
        industry_group="NonExistentIndustry12345",
        panel_mode="thesis",
    )
    assert res["status"] == "error"
    assert "Insufficient sample size" in res["error"]


def test_run_cfo_stress_simulation_baseline_and_shock():
    """Test dynamic CFO stress simulation with rate hike and margin compression."""
    res = run_cfo_stress_simulation(
        company_name_or_code="Tata Motors",
        interest_rate_shock_bps=100.0,
        operating_margin_shock_pct=-15.0,
        collateral_tangibility_shock_pct=0.0,
    )
    assert res["status"] == "success"
    assert "Tata Motors" in res["company"]
    metrics = res["covenant_and_debt_metrics"]

    assert "baseline_leverage" in metrics
    assert "shocked_target_leverage" in metrics
    assert "interest_coverage_ratio" in metrics
    assert "available_debt_headroom_cr" in metrics
    assert "simulated_credit_rating" in metrics
    assert metrics["covenant_floor"] == "2.00x"

    # Verify 3-point playbook
    playbook = res["cfo_action_playbook"]
    assert len(playbook) == 3
    assert any("Commercial Paper" in p or "Refinance" in p for p in playbook)
    assert any("CapEx" in p for p in playbook)
    assert any("Working Capital" in p or "DSO" in p for p in playbook)


def test_run_cfo_stress_simulation_stage_migration():
    """Test life stage migration from Mature to Shakeout."""
    res = run_cfo_stress_simulation(
        company_name_or_code="2451",
        interest_rate_shock_bps=150.0,
        operating_margin_shock_pct=-20.0,
        new_life_stage="Shakeout",
    )
    assert res["status"] == "success"
    assert res["life_stage"] == "Shakeout"
    metrics = res["covenant_and_debt_metrics"]
    # Deleveraging expected in Shakeout stage
    assert float(metrics["shocked_target_leverage"].replace("%", "")) < float(metrics["baseline_leverage"].replace("%", ""))
