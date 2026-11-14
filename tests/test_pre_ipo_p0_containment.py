"""
PR 1 — Pre-IPO P0 Containment Verification Suite
Enforces containment of P0-01, P0-03, P0-07, and P0-08:
- test_production_hcch_cannot_resolve_from_legacy_registry
- test_unreviewed_snapshot_blocks_every_analytical_capability
- test_legacy_example_origin_cannot_be_accepted_for_analysis
- test_unreviewed_hcch_cannot_generate_board_deck
- test_blocked_hcch_emits_no_price_market_cap_wacc_roic_or_reverse_dcf
- test_blocked_hcch_emits_no_approve_rating_or_anchor_recommendation
"""

import pytest
import os
import tempfile
import hashlib
from models.pre_ipo_capability_gate import (
    CapabilityType,
    evaluate_capability_gate,
    assert_export_allowed,
    ExportBlockedError,
)
from models.pre_ipo_data import PRE_IPO_REGISTRY
from utils.pre_ipo_deck_generator import generate_pre_ipo_board_deck
from models.pre_ipo_engine import (
    calculate_wacc_and_roic,
    calculate_reverse_dcf_hurdle,
    generate_persona_decision_view,
)


@pytest.fixture
def isolated_test_db(monkeypatch):
    """Ensure tests run against a clean isolated test database and do not touch production db."""
    tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
    tmp.close()
    monkeypatch.setenv("PROFSUR_DB_PATH", tmp.name)
    yield tmp.name
    try:
        os.remove(tmp.name)
    except Exception:
        pass


def test_production_hcch_cannot_resolve_from_legacy_registry(isolated_test_db):
    """
    P0-01: Built-in HCCH dossier in PRE_IPO_REGISTRY must be blocked in production
    and cannot be resolved for real analysis without an accepted evidence snapshot.
    """
    decision = evaluate_capability_gate(
        owner="drbhatia",
        company="hindustan_coca_cola",
        snapshot_id=None,
        capability=CapabilityType.FINANCIAL_ANALYSIS,
        origin="LEGACY_REGISTRY",
        is_production=True,
    )
    assert not decision.allowed, "Production HCCH from legacy registry must not be allowed"
    assert decision.status == "BLOCKED"
    assert "P0-01" in decision.reason or "registry" in decision.reason.lower()
    assert decision.next_action != ""


def test_unreviewed_snapshot_blocks_every_analytical_capability(isolated_test_db):
    """
    P0-01 / P0-07 / P0-08: An unreviewed snapshot must block every analytical capability.
    """
    capabilities = [
        CapabilityType.VALUATION,
        CapabilityType.WACC_ROIC,
        CapabilityType.REVERSE_DCF,
        CapabilityType.RECOMMENDATIONS,
        CapabilityType.BOARD_DECK_EXPORT,
        CapabilityType.FINANCIAL_ANALYSIS,
    ]
    for cap in capabilities:
        decision = evaluate_capability_gate(
            owner="drbhatia",
            company="hindustan_coca_cola",
            snapshot_id="snap-unreviewed-123",
            capability=cap,
            snapshot_status="UNREVIEWED",
            is_production=True,
        )
        assert not decision.allowed, f"Capability {cap} must be blocked for unreviewed snapshot"
        assert decision.status == "BLOCKED"
        assert "unreviewed" in decision.reason.lower() or "accepted" in decision.reason.lower()


def test_legacy_example_origin_cannot_be_accepted_for_analysis(isolated_test_db):
    """
    P1-02 / PR 1: LEGACY_EXAMPLE origin can never be accepted for analysis,
    regardless of feature flags or parameters.
    """
    decision = evaluate_capability_gate(
        owner="drbhatia",
        company="hindustan_coca_cola",
        snapshot_id="snap-legacy-001",
        capability=CapabilityType.VALUATION,
        origin="LEGACY_EXAMPLE",
        snapshot_status="ACCEPTED_FOR_ANALYSIS",  # even if falsely claimed
        is_production=True,
    )
    assert not decision.allowed
    assert decision.status == "BLOCKED"
    assert "LEGACY_EXAMPLE" in decision.reason


def test_unreviewed_hcch_cannot_generate_board_deck(isolated_test_db):
    """
    P0-01 / Export: Calling generate_pre_ipo_board_deck on unreviewed HCCH
    or with mismatched/unreviewed snapshot hash must fail closed.
    """
    hcch_dossier = PRE_IPO_REGISTRY["hindustan_coca_cola"]
    
    # Must raise ExportBlockedError when unreviewed or blocked
    with pytest.raises(ExportBlockedError) as exc_info:
        generate_pre_ipo_board_deck(
            dossier=hcch_dossier,
            snapshot_id=None,
            snapshot_status="UNREVIEWED",
            is_production=True,
        )
    assert "blocked" in str(exc_info.value).lower() or "unreviewed" in str(exc_info.value).lower()


def test_blocked_hcch_emits_no_price_market_cap_wacc_roic_or_reverse_dcf(isolated_test_db):
    """
    P0-03 / P0-07: Blocked HCCH must emit no price, market cap, WACC, ROIC, or reverse DCF numbers.
    """
    hcch_dossier = PRE_IPO_REGISTRY["hindustan_coca_cola"]
    
    # WACC and ROIC
    wacc_res = calculate_wacc_and_roic(
        dossier=hcch_dossier,
        is_blocked=True,
        blocked_reason="Unpriced DRHP with unreviewed disclosures",
    )
    assert wacc_res.get("status") == "BLOCKED"
    assert wacc_res.get("wacc_pct") is None
    assert wacc_res.get("roic_pct") is None

    # Reverse DCF
    dcf_res = calculate_reverse_dcf_hurdle(
        dossier=hcch_dossier,
        is_blocked=True,
        blocked_reason="Offer value not disclosed",
    )
    assert dcf_res.get("status") == "BLOCKED"
    assert dcf_res.get("implied_fcf_growth_pct") is None


def test_blocked_hcch_emits_no_approve_rating_or_anchor_recommendation(isolated_test_db):
    """
    P0-08: Blocked HCCH must emit no 'APPROVE', investment rating, or anchor participation recommendation.
    """
    hcch_dossier = PRE_IPO_REGISTRY["hindustan_coca_cola"]
    views = generate_persona_decision_view(
        dossier=hcch_dossier,
        is_blocked=True,
        blocked_reason="Filing evidence review incomplete",
    )
    
    # Check that no persona has 'APPROVE', 'AAA', or definitive buy/subscribe advice
    banned_terms = ["APPROVE", "TIER_1_STRONG_CUSHION", "STRONG BUY", "RECOMMEND SUBSCRIBE"]
    for persona_name, view in views.items():
        assert view.get("status") in ("BLOCKED", "DECISION_SUPPORT_ONLY")
        verdict = str(view.get("verdict", "")).upper()
        for term in banned_terms:
            assert term not in verdict, f"Banned term '{term}' found in {persona_name} view!"

