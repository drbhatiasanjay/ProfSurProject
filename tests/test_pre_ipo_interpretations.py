# -*- coding: utf-8 -*-
"""
tests/test_pre_ipo_interpretations.py
=====================================
Unit and adversarial tests for the Pre-IPO Narrative Interpretation & Decision Intelligence Framework.

Validates:
1. Dynamic polarity classification (POSITIVE_CONTRIBUTOR, NEGATIVE_CONTRIBUTOR, NEUTRAL_MONITOR, BLOCKING_RISK).
2. Evidentiary completeness: non-empty what_it_means, valid cited_inputs with page numbers, actionable CTA, and blind spots.
3. Contrasting deal scenario coverage (Priced froth vs Unpriced DRHP, Cash Cow vs Distress).
4. Complete synthesis of all 10 canonical interpretations.
"""

import pytest
from models.pre_ipo_interpretations import (
    Polarity,
    CitedInput,
    EvidenceBasis,
    AnalyticalInterpretation,
    synthesize_deal_interpretations,
    synthesize_valuation_multiple_interpretation,
    synthesize_beneish_interpretation,
    synthesize_dickinson_interpretation,
    synthesize_stub_seasonality_interpretation,
    synthesize_lease_leverage_interpretation,
    synthesize_altman_z_interpretation,
    synthesize_lockin_tax_interpretation,
    synthesize_provenance_gate_interpretation,
    synthesize_forensic_red_flags_interpretation,
    synthesize_ic_stance_interpretation,
)
from models.pre_ipo_schema import extract_canonical_84_provenance
from models.pre_ipo_data import PRE_IPO_REGISTRY


class TestPreIPOInterpretations:
    """Suite testing analytical interpretation synthesis and evidentiary invariants."""

    @pytest.fixture
    def hccb_provenance(self):
        dossier = PRE_IPO_REGISTRY["hindustan_coca_cola"]
        return extract_canonical_84_provenance(dossier, is_hccb=True)

    @pytest.fixture
    def ntpc_provenance(self):
        dossier = PRE_IPO_REGISTRY["ntpc_green"]
        return extract_canonical_84_provenance(dossier, is_hccb=False)

    def test_synthesis_returns_all_10_canonical_metrics(self, hccb_provenance):
        """Verify that synthesize_deal_interpretations outputs all 10 canonical keys."""
        offer = {
            "symbol": "HCCB",
            "companyName": "Hindustan Coca-Cola Beverages Limited",
            "priceBandMin": None,
            "priceBandMax": None,
            "isPriceUndisclosed": True,
            "isContained": True,
        }
        interps = synthesize_deal_interpretations(hccb_provenance, econometric_suite=None, offer_data=offer)

        expected_keys = [
            "valuation_multiple",
            "beneish_m_score",
            "dickinson_lifecycle",
            "stub_seasonality",
            "lease_adjusted_leverage",
            "altman_z_score",
            "lockin_supply_cliff",
            "provenance_gate",
            "forensic_red_flags",
            "ic_stance_mandate",
        ]
        for key in expected_keys:
            assert key in interps, f"Missing canonical interpretation key: {key}"
            it = interps[key]
            assert isinstance(it, AnalyticalInterpretation)
            assert it.polarity in [p.value for p in Polarity]
            assert len(it.headline) > 5
            assert len(it.what_it_means) > 20
            assert len(it.call_to_action) > 10
            assert len(it.evidence_basis.formula_or_method) > 5
            assert len(it.evidence_basis.cited_inputs) >= 1
            for ci in it.evidence_basis.cited_inputs:
                assert ci.page_number >= 1
                assert len(ci.value_display) > 0
                assert len(ci.label) > 0

    def test_unpriced_drhp_valuation_is_gated_neutral_monitor(self, hccb_provenance):
        """Assert unpriced DRHP (HCCB) classifies valuation as NEUTRAL_MONITOR with explicit DRHP warning."""
        offer = {
            "symbol": "HCCB",
            "priceBandMin": None,
            "priceBandMax": None,
            "isPriceUndisclosed": True,
            "isContained": True,
        }
        prov_map = {r["attributeId"]: r for r in hccb_provenance}
        it = synthesize_valuation_multiple_interpretation(
            huber_data={"warrantedFairMultiple": 34.2},
            prov_map=prov_map,
            offer_data=offer,
        )
        assert it.polarity == Polarity.NEUTRAL_MONITOR.value
        assert "Unpriced" in it.headline or "Gated" in it.headline
        assert "DRHP" in it.what_it_means
        assert any("Price Band undisclosed" in spot or "unpriced" in spot.lower() for spot in it.missing_data_and_blind_spots)
        assert "syndication discovery gate" in it.call_to_action.lower()

    def test_priced_froth_valuation_is_negative_contributor(self, ntpc_provenance):
        """Assert high valuation froth gap (+33.3%, +1.85 sigma) triggers NEGATIVE_CONTRIBUTOR with haircut CTA."""
        offer = {
            "symbol": "NTPCGREEN",
            "priceBandMin": 102,
            "priceBandMax": 108,
            "isPriceUndisclosed": False,
            "isContained": False,
        }
        prov_map = {r["attributeId"]: r for r in ntpc_provenance}
        it = synthesize_valuation_multiple_interpretation(
            huber_data={
                "askMultiple": 38.0,
                "warrantedFairMultiple": 28.5,
                "valuationFrothGapPct": 33.3,
                "frothZScore": 1.85,
            },
            prov_map=prov_map,
            offer_data=offer,
        )
        assert it.polarity == Polarity.NEGATIVE_CONTRIBUTOR.value
        assert "+33.3%" in it.headline
        assert "+1.85" in it.headline or "1.85" in it.headline
        assert "haircut" in it.call_to_action.lower()

    def test_beneish_safe_zone_is_positive_contributor(self, hccb_provenance):
        """Assert clean Beneish M-score (-2.84, Safe Zone) triggers POSITIVE_CONTRIBUTOR."""
        prov_map = {r["attributeId"]: r for r in hccb_provenance}
        it = synthesize_beneish_interpretation(
            beneish_data={"mScore": -2.84, "sloanAccrualRatio": 0.042, "zone": "SAFE"},
            prov_map=prov_map,
        )
        assert it.polarity == Polarity.POSITIVE_CONTRIBUTOR.value
        assert "Safe Zone" in it.headline
        assert "Beneish (1999)" in it.evidence_basis.formula_or_method
        assert "cleared" in it.call_to_action.lower() or "proceed" in it.call_to_action.lower()

    def test_beneish_manipulator_triggers_blocking_risk(self, hccb_provenance):
        """Assert manipulator zone M-score (-1.45 > -1.78) triggers BLOCKING_RISK."""
        prov_map = {r["attributeId"]: r for r in hccb_provenance}
        it = synthesize_beneish_interpretation(
            beneish_data={"mScore": -1.45, "sloanAccrualRatio": 0.18, "zone": "MANIPULATOR"},
            prov_map=prov_map,
        )
        assert it.polarity == Polarity.BLOCKING_RISK.value
        assert "Manipulator Zone" in it.headline or "Alert" in it.headline
        assert "forensic hold" in it.call_to_action.lower() or "audit" in it.call_to_action.lower()

    def test_dickinson_mature_is_positive_contributor(self, hccb_provenance):
        """Assert Dickinson Mature Cash Cow (+, -, -) triggers POSITIVE_CONTRIBUTOR."""
        prov_map = {r["attributeId"]: r for r in hccb_provenance}
        it = synthesize_dickinson_interpretation(
            dickinson_data={"currentStage": "MATURE", "currentVector": "(+, -, -)", "cfoToEbitdaRatio": 0.88},
            prov_map=prov_map,
        )
        assert it.polarity == Polarity.POSITIVE_CONTRIBUTOR.value
        assert "Mature" in it.headline
        assert "(+, -, -)" in it.headline
        assert "Dickinson (2011)" in it.evidence_basis.formula_or_method

    def test_dickinson_decline_triggers_blocking_risk(self, hccb_provenance):
        """Assert Dickinson Decline stage triggers BLOCKING_RISK."""
        prov_map = {r["attributeId"]: r for r in hccb_provenance}
        it = synthesize_dickinson_interpretation(
            dickinson_data={"currentStage": "DECLINE", "currentVector": "(-, +, +)", "cfoToEbitdaRatio": -0.40},
            prov_map=prov_map,
        )
        assert it.polarity == Polarity.BLOCKING_RISK.value
        assert "DECLINE" in it.headline
        assert "reject" in it.call_to_action.lower() or "caution" in it.call_to_action.lower()

    def test_stub_seasonality_distortion_is_negative_contributor(self, hccb_provenance):
        """Assert high annualization distortion (+28.5%) and margin spike triggers NEGATIVE_CONTRIBUTOR."""
        prov_map = {r["attributeId"]: r for r in hccb_provenance}
        it = synthesize_stub_seasonality_interpretation(
            stub_data={
                "annualizationDistortionPct": 28.5,
                "marginStuffingSpikeBps": 290.0,
                "marginStuffingDetected": True,
                "fStatistic": 4.15,
            },
            prov_map=prov_map,
        )
        assert it.polarity == Polarity.NEGATIVE_CONTRIBUTOR.value
        assert "+28.5%" in it.headline
        assert "Do not underwrite on naive annualized run-rate" in it.call_to_action

    def test_lease_adjusted_leverage_evaluates_correctly(self, hccb_provenance):
        """Assert low lease leverage (0.44x) is POSITIVE, while high leverage (>3.0x) is NEGATIVE."""
        prov_map = {r["attributeId"]: r for r in hccb_provenance}
        safe_it = synthesize_lease_leverage_interpretation(
            lease_data={"reportedNetDebtToEbitda": 0.22, "leaseAdjustedNetDebtToEbitda": 0.44, "leaseLiabilitiesCr": 722.0},
            prov_map=prov_map,
        )
        assert safe_it.polarity == Polarity.POSITIVE_CONTRIBUTOR.value
        assert "0.44x" in safe_it.headline

        distress_it = synthesize_lease_leverage_interpretation(
            lease_data={"reportedNetDebtToEbitda": 2.20, "leaseAdjustedNetDebtToEbitda": 3.85, "refinancingWallRatio": 0.45},
            prov_map=prov_map,
        )
        assert distress_it.polarity == Polarity.NEGATIVE_CONTRIBUTOR.value
        assert "3.85x" in distress_it.headline

    def test_altman_z_zones_classify_accurately(self, hccb_provenance):
        """Assert Safe (>2.60) is POSITIVE, while Distress (<1.10) is BLOCKING_RISK."""
        prov_map = {r["attributeId"]: r for r in hccb_provenance}
        safe_it = synthesize_altman_z_interpretation(
            altman_data={"zDoublePrimeScore": 4.12, "zone": "SAFE", "defaultProbabilityProxy": 0.015},
            prov_map=prov_map,
        )
        assert safe_it.polarity == Polarity.POSITIVE_CONTRIBUTOR.value

        distress_it = synthesize_altman_z_interpretation(
            altman_data={"zDoublePrimeScore": 0.88, "zone": "DISTRESS", "defaultProbabilityProxy": 0.35},
            prov_map=prov_map,
        )
        assert distress_it.polarity == Polarity.BLOCKING_RISK.value

    def test_ic_stance_mandate_aggregates_deal_balance(self, hccb_provenance):
        """Assert IC stance synthesizes constituent interpretations into overarching mandate."""
        offer = {
            "symbol": "HCCB",
            "companyName": "Hindustan Coca-Cola Beverages Limited",
            "priceBandMin": None,
            "priceBandMax": None,
            "isPriceUndisclosed": True,
        }
        all_interps = synthesize_deal_interpretations(hccb_provenance, econometric_suite=None, offer_data=offer)
        ic_it = all_interps["ic_stance_mandate"]
        assert ic_it.polarity in [p.value for p in Polarity]
        assert "IC Mandate" in ic_it.headline
        assert len(ic_it.missing_data_and_blind_spots) >= 1
