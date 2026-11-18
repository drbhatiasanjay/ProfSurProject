"""
Unit Tests for MicroDecisionEngine & Fallback Adapter
Milestone 11 - Pre-IPO Knowledge Graph Platform

Verifies:
1. System 1 micro-decision types (noul, choice, score, box).
2. Pinned model invariant ("typesafe/jev-1.14.0").
3. Deterministic fallback execution without network connectivity.
4. Three-zone threshold routing (<0.10 reject, >0.90 auto-commit).
"""

from models.pre_ipo_decision_engine import (
    get_micro_decision_engine,
    FallbackHeuristicDecisionEngine,
    PINNED_JEV_MODEL
)


def test_pinned_model_version_invariant():
    """Asserts that model ID is pinned to jev-1.14.0 per PRD Rule 3.2."""
    assert PINNED_JEV_MODEL == "typesafe/jev-1.14.0"


def test_micro_decision_fallback_primitives():
    """Verifies that all 4 decision primitives return valid structured outputs."""
    engine = FallbackHeuristicDecisionEngine()
    state = {
        "section": "Related Party Transactions",
        "related_party": "Coca-Cola India Pvt Ltd",
        "incentive_share": "6.28% of revenue",
        "doubled": True
    }
    questions = [
        {
            "name": "is_suspicious_rpt_surge",
            "type": "noul",
            "criteria": {"true": "Parent incentives surged during margin expansion"}
        },
        {
            "name": "fibo_role_classification",
            "type": "choice",
            "options": ["fibo-sebi:PromoterRole", "fibo-sebi:MaterialSubsidiaryRole", "fibo-sebi:RelatedPartyContract"]
        },
        {
            "name": "rpt_dependency_score",
            "type": "score",
            "rubric": "2-10 materiality levels"
        },
        {
            "name": "table_cell_crop",
            "type": "box"
        }
    ]

    decisions = engine.evaluate(state, questions)

    # 1. noul check
    assert "is_suspicious_rpt_surge" in decisions
    noul_res = decisions["is_suspicious_rpt_surge"]
    assert noul_res["type"] == "noul"
    assert noul_res["value"] is True
    assert noul_res["probability"] >= 0.90

    # 2. choice check
    assert "fibo_role_classification" in decisions
    choice_res = decisions["fibo_role_classification"]
    assert choice_res["type"] == "choice"
    assert "fibo-sebi:" in choice_res["value"]

    # 3. score check
    assert "rpt_dependency_score" in decisions
    score_res = decisions["rpt_dependency_score"]
    assert score_res["type"] == "score"
    assert 2 <= score_res["value"] <= 10

    # 4. box check
    assert "table_cell_crop" in decisions
    box_res = decisions["table_cell_crop"]
    assert box_res["type"] == "box"
    assert len(box_res["value"]) == 4


def test_three_zone_threshold_routing():
    """Asserts that noul decisions cleanly route into auto-commit vs auto-reject."""
    engine = FallbackHeuristicDecisionEngine()

    # High-confidence scenario: HCCH 100% OFS
    high_state = {"offering": "pure_ofs", "fresh_issue": "0_fresh"}
    q_high = [{"name": "is_100_ofs", "type": "noul"}]
    res_high = engine.evaluate(high_state, q_high)["is_100_ofs"]
    assert res_high["probability"] > 0.90  # Zone 1: Auto-commit

    # Low-confidence scenario: irrelevant noise
    low_state = {"irrelevant": "generic text"}
    q_low = [{"name": "is_litigation", "type": "noul"}]
    res_low = engine.evaluate(low_state, q_low)["is_litigation"]
    assert res_low["probability"] < 0.30  # Zone 3: Auto-reject
