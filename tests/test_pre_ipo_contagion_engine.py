"""
Adversarial TDD Test Suite for Pre-IPO Contagion & Shock Simulation Engine
Milestone 14 - Phase 2A Verification

Tests:
1. Rule E.3 Zero-Truthiness preservation on numeric inputs (P=0.0, indemnity=0.0, bps=0.0).
2. 100% Parent Indemnity shield leaves Net Worth intact.
3. Unshielded CESTAT shock accurately reduces Net Worth by 45.6%.
4. Severe insolvency boundary triggers AVOID_HIGH_RISK and covenant breach.
5. Causal sub-graph generates valid @xyflow/react nodes and edges.
6. Preset scenarios return 5 calibrated stress test cases.
"""

import pytest
from models.pre_ipo_contagion_engine import (
    ContagionShockSimulator,
    ContagionShockRequest,
    ContagionShockResult,
    HCCH_BASE_METRICS
)


def test_rule_e3_zero_truthiness_preservation():
    """
    Rule E.3: 0.0, 0%, and 0 are valid numbers distinct from None.
    A probability of 0.0 must evaluate to zero loss, NOT fall back to default (1.0).
    """
    sim = ContagionShockSimulator()
    req = ContagionShockRequest(
        symbol="HCCH",
        fact_id="FACT_S06_01_CESTAT_INDIRECT_TAX",
        crystallization_prob=0.0,       # 0.0 loss
        parent_indemnity_pct=0.0,
        macro_rate_shock_bps=0.0
    )
    res = sim.simulate(req)

    assert res.crystallization_prob == 0.0
    assert res.net_crystallized_loss_cr == 0.0
    assert res.post_shock_net_worth_cr == HCCH_BASE_METRICS["tangible_net_worth_cr"]
    assert res.net_worth_erosion_pct == 0.0
    assert res.post_shock_ic_stance == "SUBSCRIBE"


def test_parent_indemnity_full_protection_shield():
    """
    When HoldCo parent provides 100% indemnity (indemnity=1.0),
    even a 100% crystallization (p=1.0) of ₹4,455.47 Cr results in 0 issuer balance sheet damage.
    """
    sim = ContagionShockSimulator()
    req = ContagionShockRequest(
        symbol="HCCH",
        fact_id="FACT_S06_01_CESTAT_INDIRECT_TAX",
        crystallization_prob=1.0,
        parent_indemnity_pct=1.0,       # 100% indemnified by Parent Coca-Cola Co.
        macro_rate_shock_bps=0.0
    )
    res = sim.simulate(req)

    assert res.gross_exposure_cr == 4455.47
    assert res.parent_indemnity_pct == 1.0
    assert res.net_crystallized_loss_cr == 0.0
    assert res.post_shock_net_worth_cr == HCCH_BASE_METRICS["tangible_net_worth_cr"]
    assert res.post_shock_ic_stance == "SUBSCRIBE"
    assert "quarantined or shielded" in res.ic_rationale.lower()


def test_unshielded_cestat_tax_shock():
    """
    Unshielded crystallization of CESTAT ₹4,455.47 Cr reduces Net Worth by ~45.6%.
    """
    sim = ContagionShockSimulator()
    req = ContagionShockRequest(
        symbol="HCCH",
        fact_id="FACT_S06_01_CESTAT_INDIRECT_TAX",
        crystallization_prob=1.0,
        parent_indemnity_pct=0.0,
        macro_rate_shock_bps=0.0
    )
    res = sim.simulate(req)

    assert res.gross_exposure_cr == 4455.47
    assert res.net_crystallized_loss_cr == 4455.47
    expected_nw = HCCH_BASE_METRICS["tangible_net_worth_cr"] - 4455.47
    assert abs(res.post_shock_net_worth_cr - expected_nw) < 0.1
    assert 45.0 < res.net_worth_erosion_pct < 46.5
    # Leverage jumps
    assert res.post_shock_debt_to_equity > res.base_debt_to_equity
    assert res.post_shock_ic_stance in ["SUBSCRIBE_WITH_COVENANTS", "AVOID_HIGH_RISK"]
    assert res.implied_valuation_haircut_pct > 15.0


def test_insolvency_boundary_cliff():
    """
    Extreme synthetic shock that exceeds total tangible net worth triggers technical insolvency.
    """
    synthetic_metrics = {
        "tangible_net_worth_cr": 2000.0,
        "total_debt_cr": 1500.0,
        "ebitda_cr": 500.0,
        "covenant_de_ceiling": 2.0,
        "base_wacc_pct": 11.2,
        "base_ev_ebitda": 20.0,
        "risk_free_rate_pct": 7.15,
        "equity_risk_premium_pct": 5.5,
        "tax_rate_pct": 25.17
    }
    sim = ContagionShockSimulator(base_metrics=synthetic_metrics)
    req = ContagionShockRequest(
        symbol="SYNTH",
        fact_id="FACT_S06_01_CESTAT_INDIRECT_TAX",  # Exposure 4455.47 > NW 2000
        crystallization_prob=1.0,
        parent_indemnity_pct=0.0,
        macro_rate_shock_bps=0.0
    )
    res = sim.simulate(req)

    assert res.post_shock_net_worth_cr < 0.0
    assert res.post_shock_ic_stance == "AVOID_HIGH_RISK"
    assert "CRITICAL: Complete Tangible Net Worth wipeout" in res.ic_rationale


def test_causal_subgraph_topology():
    """
    Asserts that the generated causal sub-graph is compliant with @xyflow/react node/edge contract.
    """
    sim = ContagionShockSimulator()
    req = ContagionShockRequest(fact_id="FACT_S06_01_CESTAT_INDIRECT_TAX")
    res = sim.simulate(req)

    graph = res.causal_subgraph
    assert "nodes" in graph
    assert "edges" in graph
    assert len(graph["nodes"]) == 5
    assert len(graph["edges"]) == 4

    node_ids = [n["id"] for n in graph["nodes"]]
    assert node_ids == ["node_fact", "node_solvency", "node_covenant", "node_valuation", "node_ic"]

    for edge in graph["edges"]:
        assert edge["source"] in node_ids
        assert edge["target"] in node_ids
        assert edge["animated"] is True


def test_preset_scenarios_structure():
    """
    Verifies that preset scenarios return 5 institutional cases.
    """
    sim = ContagionShockSimulator()
    scenarios = sim.get_preset_scenarios("HCCH")

    assert len(scenarios) == 5
    scenario_ids = [s["scenario_id"] for s in scenarios]
    assert "SCENARIO_BASE" in scenario_ids
    assert "SCENARIO_CESTAT_UNSHIELDED" in scenario_ids
    assert "SCENARIO_CESTAT_PARENT_INDEMNIFIED" in scenario_ids
    assert "SCENARIO_DISTRIBUTOR_DISTRESS" in scenario_ids
    assert "SCENARIO_COMBINED_TAIL_MACRO" in scenario_ids

    for s in scenarios:
        assert "parameters" in s
        assert "results" in s
        assert "causal_subgraph" in s["results"]
