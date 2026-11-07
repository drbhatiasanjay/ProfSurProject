import pytest
from models.pre_ipo_ingest import PRE_IPO_REGISTRY
from models.pre_ipo_algorithms import (
    alg01_temporal_evidence_graph,
    alg02_falsifiable_thesis,
    alg03_sector_operating_drivers,
    alg04_dated_financing_feasibility,
    alg05_share_ledger_dilution,
    alg06_reverse_underwriting_valuation,
    alg07_reverse_stress_failure_frontier,
    alg08_diligence_priority_voi,
    alg09_comparable_ranking,
    alg10_forecast_accountability,
    alg11_revision_aware_monitoring,
    alg12_investor_returns_attribution,
    alg13_private_security_waterfall,
    alg14_method_governance,
)

def test_alg01_temporal_evidence_graph():
    dossier = PRE_IPO_REGISTRY["ntpc_green"]
    graph = alg01_temporal_evidence_graph(dossier)
    assert graph["eligible_evidence_count"] > 0
    assert "evidence_nodes" in graph
    assert graph["replay_cutoff"] == "LATEST"

def test_alg02_falsifiable_thesis():
    dossier = PRE_IPO_REGISTRY["ntpc_green"]
    thesis = alg02_falsifiable_thesis(dossier)
    assert thesis["total_propositions"] >= 2
    assert thesis["supported_count"] >= 1
    for p in thesis["propositions"]:
        assert "economic_mechanism" in p
        assert "counterevidence_hypothesis" in p

def test_alg03_sector_operating_drivers():
    # Renewable utility
    ntpc = PRE_IPO_REGISTRY["ntpc_green"]
    drivers_ntpc = alg03_sector_operating_drivers(ntpc)
    assert drivers_ntpc["sector_model"] == "UTILITY_RENEWABLE_POWER"
    assert "plant_load_factor_plf_pct" in drivers_ntpc["driver_tree"]

    # Digital platform
    swiggy = PRE_IPO_REGISTRY["swiggy"]
    drivers_swiggy = alg03_sector_operating_drivers(swiggy)
    assert drivers_swiggy["sector_model"] == "DIGITAL_PLATFORM_ECOSYSTEM"
    assert "gross_merchandise_value_gmv_cr" in drivers_swiggy["driver_tree"]

def test_alg04_dated_financing_feasibility():
    dossier = PRE_IPO_REGISTRY["ntpc_green"]
    res_base = alg04_dated_financing_feasibility(dossier, rate_shock_bps=0.0)
    res_shock = alg04_dated_financing_feasibility(dossier, rate_shock_bps=150.0)
    
    assert res_shock["annual_interest_burden_cr"] > res_base["annual_interest_burden_cr"]
    # NTPC Green pre-IPO has 15,235 Cr debt vs 1,480 Cr CFO -> pre-IPO debt service creates critical gap / tight liquidity
    assert res_base["feasibility_status"] in ("CRITICAL_CASH_GAP", "TIGHT_LIQUIDITY", "ADEQUATE_HEADROOM")
    assert res_base["monthly_runway_months"] > 0

def test_alg05_share_ledger_dilution():
    dossier = PRE_IPO_REGISTRY["ntpc_green"]
    ledger = alg05_share_ledger_dilution(dossier, price_inr=108.0, advisory_fee_pct=0.02, fixed_expense_cr=15.0)
    assert ledger["is_computable"] is True
    assert ledger["sources_uses_balanced"] is True
    assert ledger["gross_proceeds_cr"] > ledger["net_proceeds_cr"]
    assert ledger["promoter_dilution_pct"] > 0

def test_alg06_reverse_underwriting_valuation():
    dossier = PRE_IPO_REGISTRY["ntpc_green"]
    # Solvable case
    sol = alg06_reverse_underwriting_valuation(dossier, target_ev_cr=75000.0, terminal_growth_pct=4.0, wacc_pct=11.5)
    assert sol["is_feasible"] is True
    assert sol["status"] == "SOLVED"
    assert sol["implied_required_fcf_cagr_pct"] > 0

    # Unfeasible case (w <= g)
    unfeasible = alg06_reverse_underwriting_valuation(dossier, target_ev_cr=75000.0, terminal_growth_pct=12.0, wacc_pct=10.0)
    assert unfeasible["is_feasible"] is False
    assert unfeasible["status"] == "MATHEMATICALLY_OUT_OF_BOUNDS"

def test_alg07_reverse_stress_failure_frontier():
    dossier = PRE_IPO_REGISTRY["ntpc_green"]
    frontier = alg07_reverse_stress_failure_frontier(dossier)
    assert frontier["status"] == "FRONTIER_FOUND"
    assert frontier["severity_distance"] is not None
    assert frontier["minimal_revenue_shock_pct"] >= 0

def test_alg08_diligence_priority_voi():
    dossier = PRE_IPO_REGISTRY["ntpc_green"]
    voi = alg08_diligence_priority_voi(dossier)
    assert "tier1_mandatory_blockers" in voi
    assert "tier2_decision_reversals" in voi
    assert voi["executive_action"] in ("REJECT_OR_PAUSE", "CONDITIONAL_APPROVAL", "PROCEED")

def test_alg09_comparable_ranking():
    dossiers = [PRE_IPO_REGISTRY["ntpc_green"], PRE_IPO_REGISTRY["swiggy"], PRE_IPO_REGISTRY["tata_technologies"]]
    ranking = alg09_comparable_ranking(dossiers)
    assert ranking["candidate_count"] == 3
    assert ranking["pareto_frontier_count"] >= 1

def test_alg10_forecast_accountability():
    dossier = PRE_IPO_REGISTRY["ntpc_green"]
    # Guidance 1800 Cr vs reported 1746.5 Cr
    acc = alg10_forecast_accountability(dossier, guidance_ebitda_cr=1800.0, reported_ebitda_cr=1746.5)
    assert acc["status"] == "EVALUATED"
    assert acc["variance_cr"] == -53.5
    assert acc["bias_direction"] == "OPTIMISM_DEFICIT"

def test_alg11_revision_aware_monitoring():
    dossier = PRE_IPO_REGISTRY["ntpc_green"]
    mon = alg11_revision_aware_monitoring(dossier, observed_metrics={"net_debt_to_ebitda": 4.8})
    assert mon["total_active_alerts"] == 1
    assert mon["alerts"][0]["state"] == "CROSSED"

def test_alg12_investor_returns_attribution():
    # Price rises from 100 to 150 (50% return), EPS rises from 5.0 to 6.5
    attr = alg12_investor_returns_attribution(entry_price_inr=100.0, exit_price_inr=150.0, entry_eps_inr=5.0, exit_eps_inr=6.5)
    assert attr["is_computable"] is True
    assert attr["total_price_delta_inr"] == 50.0
    # Strict midpoint identity: conservation error == 0
    assert attr["conservation_error_inr"] < 0.001
    assert attr["earnings_growth_contribution_inr"] > 0
    assert attr["multiple_expansion_contribution_inr"] > 0

def test_alg13_private_security_waterfall():
    # 1000 Cr exit, 200 Cr debt, 300 Cr 1x preferred, 80% common
    wf = alg13_private_security_waterfall(
        exit_valuation_cr=1000.0,
        senior_debt_cr=200.0,
        preferred_investment_cr=300.0,
        liquidation_pref_multiple=1.0,
        is_participating=False,
        common_shares_pct=80.0,
    )
    assert wf["is_valid"] is True
    assert wf["senior_debt_proceeds_cr"] == 200.0
    assert wf["proceeds_conserved"] is True
    assert wf["total_distributed_cr"] == 1000.0

def test_alg14_method_governance():
    dossier = PRE_IPO_REGISTRY["ntpc_green"]
    gov = alg14_method_governance(dossier)
    assert gov["governance_rules"]["prohibit_spread_as_confidence_interval"] is True
    assert "DYNAMIC_PANEL_GMM" in gov["blocked_methods_justification"]
