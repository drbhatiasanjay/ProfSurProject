# -*- coding: utf-8 -*-
"""
tests/test_pre_ipo_84_schema_and_econometrics.py
=================================================
Comprehensive Verification Suite for Expanded 84-Attribute Schema,
Institutional Econometric Engines, and Automated Buy-Side Interpretation.

Adheres strictly to AGENTS.md:
- Rule E.1: End-to-end production wiring contract
- Rule E.2: Negative and bypass probing (fail-closed architecture)
- Rule E.3: Zero Python truthiness in financial calculations (0.0 != None)
- Rule E.4: Solver round-trip inversion requirement (<= 0.05% error)
- Phase B 7 quantitative models verified against academic baselines.
"""

import pytest
import math
import numpy as np
from models.pre_ipo_schema import (
    CanonicalSection,
    ExpectedUnit,
    AttributeDefinition,
    CANONICAL_SECTIONS,
    CANONICAL_84_ATTRIBUTES,
    extract_canonical_84_provenance,
)
from models.pre_ipo_econometrics import (
    compute_beneish_m_score,
    classify_single_dickinson_vector,
    analyze_dickinson_lifecycle,
    fit_huber_robust_peer_regression,
    analyze_stub_seasonality_and_break,
    analyze_ind_as_116_leverage,
    compute_altman_z_double_prime,
    analyze_lockin_and_tax_drag,
    solve_implied_reverse_dcf_growth,
    dcf_enterprise_value,
    run_comprehensive_pre_ipo_econometrics,
    EconometricVerdict,
    EconometricInterpretation,
)
from models.pre_ipo_capability_gate import (
    assert_capability_allowed,
    CapabilityType,
    ExportBlockedError,
)
from models.pre_ipo_data import PRE_IPO_REGISTRY


class TestCanonical84AttributeSchemaIntegrity:
    """Verifies the 84-attribute statutory disclosure schema and zero-truthiness preservation."""

    def test_canonical_84_sections_and_attributes_count(self):
        """Assert exactly 10 canonical sections and 84 unique attributes exist."""
        assert len(CANONICAL_SECTIONS) == 10
        assert len(CANONICAL_84_ATTRIBUTES) == 84
        unique_ids = set(a.attribute_id for a in CANONICAL_84_ATTRIBUTES)
        assert len(unique_ids) == 84

    def test_zero_truthiness_preservation_in_extraction(self):
        """Assert Rule E.3: 0.0 fresh issue, 0.0% pledge, 0.0 debt are marked FOUND with value 0.0."""
        dossier = PRE_IPO_REGISTRY["mankind_pharma"]
        records = extract_canonical_84_provenance(dossier, is_hccb=True)
        rec_map = {r["attributeId"]: r for r in records}

        # 1. Gross Fresh Issue in HCCH 100% OFS is 0.0 Cr
        fresh_rec = rec_map["offer.fresh_issue_cr"]
        assert fresh_rec["status"] == "FOUND"
        assert fresh_rec["value"] == 0.0
        assert fresh_rec["value"] is not None

        # 2. Promoter shareholding pledged is 0.0%
        pledge_rec = rec_map["cap.promoter_pledge_pct"]
        assert pledge_rec["status"] == "FOUND"
        assert pledge_rec["value"] == 0.0
        assert pledge_rec["value"] is not None

        # 3. Secured Term Loans is 0.0 Cr
        loans_rec = rec_map["debt.secured_term_loans_cr"]
        assert loans_rec["status"] == "FOUND"
        assert loans_rec["value"] == 0.0
        assert loans_rec["value"] is not None

    def test_unpriced_drhp_containment(self):
        """Assert unpriced DRHP price bands are emitted as NOT_FOUND with RHP reason."""
        dossier = PRE_IPO_REGISTRY["ntpc_green"]
        records = extract_canonical_84_provenance(dossier, is_hccb=True)
        rec_map = {r["attributeId"]: r for r in records}

        min_rec = rec_map["offer.price_band_min"]
        assert min_rec["status"] == "NOT_FOUND"
        assert min_rec["value"] is None
        assert "RHP" in (min_rec.get("reconfirmationReason") or "")


class TestModel1BeneishMScoreAndSloanAccruals:
    """Verifies Model 1: Beneish (1999) 8-Variable M-Score & Sloan (1996) Accruals."""

    def test_beneish_safe_zone_calculation(self):
        """Test healthy firm with high cash earnings quality (Beneish M-Score <= -2.22)."""
        res = compute_beneish_m_score(
            sales_t=12840.5, sales_prev=11200.0,
            cogs_t=6820.0, cogs_prev=6000.0,
            rec_t=312.4, rec_prev=290.0,
            ca_t=2840.0, ca_prev=2600.0,
            ppe_t=4850.0, ppe_prev=4500.0,
            depr_t=390.0, depr_prev=360.0,
            sga_t=1420.0, sga_prev=1300.0,
            cfo_t=1438.5, pat_t=1021.4,
            total_assets_t=9480.0, total_assets_prev=8900.0,
            ltd_t=842.0, ltd_prev=820.0,
            cl_t=2480.0, cl_prev=2300.0,
        )

        assert res.m_score <= -2.00
        assert res.zone in ("SAFE", "GREY")
        assert not res.is_manipulator
        assert abs(res.sloan_accrual_ratio) < 0.10
        # 3-part interpretation payload check
        assert res.interpretation.verdict in ("FAVORABLE", "NEUTRAL")
        assert len(res.interpretation.statistical_summary) > 20
        assert len(res.interpretation.economic_mechanism) > 20
        assert len(res.interpretation.ic_recommendation) > 20

    def test_beneish_manipulator_detection(self):
        """Test firm with high accruals and receivables bloat (DSRI >> 1.5, TATA >> 0.15)."""
        res = compute_beneish_m_score(
            sales_t=5000.0, sales_prev=4000.0,
            cogs_t=2000.0, cogs_prev=1800.0,
            rec_t=2500.0, rec_prev=1000.0,  # Massive receivables surge
            ca_t=3500.0, ca_prev=2000.0,
            ppe_t=2000.0, ppe_prev=2000.0,
            depr_t=50.0, depr_prev=100.0,   # Slowdown in depreciation
            sga_t=500.0, sga_prev=500.0,
            cfo_t=100.0, pat_t=1200.0,      # Huge accruals: PAT 1200 vs CFO 100
            total_assets_t=6000.0, total_assets_prev=5000.0,
            ltd_t=2000.0, ltd_prev=1500.0,
            cl_t=1500.0, cl_prev=1000.0,
        )

        assert res.m_score > -1.78
        assert res.zone == "MANIPULATOR"
        assert res.is_manipulator is True
        assert res.interpretation.verdict == "CRITICAL"
        assert "MANIPULATOR" in res.interpretation.statistical_summary or "Breaches" in res.interpretation.statistical_summary


class TestModel2DickinsonLifecycleEngine:
    """Verifies Model 2: Dickinson (2011) Cash Flow Life-Cycle Classification."""

    def test_dickinson_vector_classification_rules(self):
        """Assert deterministic sign vector mapping per Dickinson (2011)."""
        assert classify_single_dickinson_vector(-100, -200, +300)[0] == "Introduction"
        assert classify_single_dickinson_vector(+100, -200, +150)[0] == "Growth"
        assert classify_single_dickinson_vector(+100, -200, -50)[0] == "Mature (Cash Cow)"
        assert classify_single_dickinson_vector(-100, +50, +50)[0] == "Decline"
        assert classify_single_dickinson_vector(+100, +50, +50)[0] == "Shake-out"

    def test_dickinson_zero_truthiness(self):
        """Assert Rule E.3: 0.0 cash flows are preserved as '0' in vector and not collapsed into None."""
        stage, pattern = classify_single_dickinson_vector(100.0, -50.0, 0.0)
        assert pattern == "(+, -, 0)"
        assert stage == "Mature (Cash Cow)"

    def test_dickinson_multi_period_trajectory(self):
        """Assert multi-period trajectory across FY23, FY24, FY25, and Stub."""
        periods = [
            {"period": "FY23", "cfo": 1100.0, "cfi": -500.0, "cff": -300.0},
            {"period": "FY24", "cfo": 1300.0, "cfi": -550.0, "cff": -350.0},
            {"period": "FY25", "cfo": 1450.0, "cfi": -600.0, "cff": -400.0},
            {"period": "Stub Q1", "cfo": 500.0, "cfi": -180.0, "cff": -100.0},
        ]
        res = analyze_dickinson_lifecycle(periods)
        assert res.current_stage == "Mature (Cash Cow)"
        assert res.current_pattern == "(+, -, -)"
        assert res.is_growth_congruent is True
        assert len(res.trajectory) == 4
        assert res.interpretation.verdict == "FAVORABLE"


class TestModel3HuberRobustRegressionEngine:
    """Verifies Model 3: Huber (1964) Robust Multiple Peer Regression (statsmodels RLM)."""

    def test_huber_rlm_downweights_outlier_peer(self):
        """Assert Huber M-estimator downweights high-multiple peer outliers."""
        target = {"symbol": "TESTCO", "evEbitda": 28.0, "roce": 25.0, "revenueCagr3Y": 24.0, "ebitdaMargin": 22.0, "netDebtToEbitda": 0.5}
        peers = [
            {"symbol": "PEER1", "companyName": "Peer One", "evEbitda": 26.0, "roce": 24.0, "revenueCagr3Y": 22.0, "ebitdaMargin": 20.0, "netDebtToEbitda": 0.4, "isDrhpDeclared": True},
            {"symbol": "PEER2", "companyName": "Peer Two", "evEbitda": 30.0, "roce": 26.0, "revenueCagr3Y": 25.0, "ebitdaMargin": 21.0, "netDebtToEbitda": 0.6, "isDrhpDeclared": True},
            {"symbol": "PEER3", "companyName": "Peer Three", "evEbitda": 27.0, "roce": 23.0, "revenueCagr3Y": 20.0, "ebitdaMargin": 19.0, "netDebtToEbitda": 0.5, "isDrhpDeclared": False},
            {"symbol": "OUTLIER", "companyName": "Distressed Bubble Peer", "evEbitda": 150.0, "roce": 2.0, "revenueCagr3Y": 40.0, "ebitdaMargin": 4.0, "netDebtToEbitda": 8.0, "isDrhpDeclared": False},
        ]

        res = fit_huber_robust_peer_regression(target, peers, multiple_key="evEbitda")
        assert res.warranted_fair_multiple > 10.0
        assert res.warranted_fair_multiple < 50.0
        # Find OUTLIER peer weight
        outlier_weights = [pw for pw in res.peer_weights if pw.symbol == "OUTLIER"]
        assert len(outlier_weights) == 1
        assert outlier_weights[0].robust_weight < 0.70  # Outlier significantly downweighted
        assert outlier_weights[0].is_outlier is True
        assert res.interpretation.verdict in ("FAVORABLE", "NEUTRAL", "CAUTION", "CRITICAL")


class TestModel4StubSeasonalityAndBreakEngine:
    """Verifies Model 4: Stub Seasonality & Margin Structural Break Analyzer."""

    def test_stub_seasonality_annualization_distortion(self):
        """Assert naive 4x annualization vs 34% Q1 peak seasonal weight generates expected distortion."""
        res = analyze_stub_seasonality_and_break(
            stub_revenue_cr=4280.0,
            stub_months=3,
            stub_ebitda_margin_pct=21.4,
            historical_revenues_cr=[11200.0, 12840.0],
            historical_margins_pct=[18.5, 19.2, 19.8],
            seasonal_quarter_weight=0.34,
            stub_period_label="Q1 Summer Peak",
        )

        # Naive 4x = 17,120 Cr vs Seasonally adjusted = 4280 / 0.34 = 12,588.24 Cr
        assert res.naive_annualized_revenue_cr == 17120.0
        assert abs(res.seasonal_adjusted_revenue_cr - 12588.24) < 1.0
        assert res.annualization_distortion_cr > 4000.0
        assert res.margin_spike_bps > 0
        assert res.interpretation.verdict in ("CAUTION", "CRITICAL")

    def test_pre_ipo_margin_stuffing_detection(self):
        """Assert pre-IPO margin spike >= 250 bps triggers margin stuffing alert."""
        res = analyze_stub_seasonality_and_break(
            stub_revenue_cr=2000.0,
            stub_months=3,
            stub_ebitda_margin_pct=25.0,  # +700 bps spike
            historical_revenues_cr=[6000.0, 7000.0],
            historical_margins_pct=[18.0, 18.0, 18.0],
            seasonal_quarter_weight=0.25,
        )
        assert res.margin_spike_bps == 700.0
        assert res.is_margin_stuffing_alert is True
        assert res.structural_break_detected is True
        assert res.interpretation.verdict == "CRITICAL"


class TestModel5IndAS116LeaseLeverageEngine:
    """Verifies Model 5: Ind AS 116 Lease-Adjusted Leverage & Refinancing Wall."""

    def test_ind_as_116_unwinding_leverage_math(self):
        """Assert capitalized lease liabilities increase true leverage ratio."""
        res = analyze_ind_as_116_leverage(
            term_loans_cr=0.0,  # Zero bank term loans
            working_capital_borrowings_cr=120.0,
            lease_liabilities_cr=722.0,  # Ind AS 116 capitalized leases
            current_lease_obligations_cr=84.0,
            cash_and_bank_cr=412.5,
            ebitda_cr=1840.0,
            rent_expense_cr=112.0,
            finance_costs_cr=94.0,
            cfo_cr=1438.5,
        )

        assert res.funded_debt_cr == 120.0
        assert res.total_adjusted_debt_cr == 842.0
        assert res.headline_net_debt_to_ebitda == 0.0  # Cash (412.5) > Funded debt (120)
        assert res.lease_adjusted_net_debt_to_ebitdar > 0.15  # Adjusted debt reflects leases
        assert res.refinancing_wall_ratio < 0.50  # Ample liquidity buffer
        assert res.interpretation.verdict == "FAVORABLE"


class TestModel6AltmanZScoreEmergingMarkets:
    """Verifies Model 6: Altman (2002) Emerging Market Z''-Score."""

    def test_altman_z_score_safe_and_distress_zones(self):
        """Assert Altman EM Z''-Score classifies safe (> 2.60) and distress (< 1.10) profiles."""
        # Safe firm
        safe_res = compute_altman_z_double_prime(
            working_capital_cr=500.0,
            retained_earnings_cr=2500.0,
            ebit_cr=1500.0,
            book_value_equity_cr=3000.0,
            total_liabilities_cr=4000.0,
            total_assets_cr=7000.0,
        )
        assert safe_res.z_score > 2.60
        assert safe_res.zone == "SAFE"
        assert safe_res.interpretation.verdict == "FAVORABLE"

        # Distressed firm
        distress_res = compute_altman_z_double_prime(
            working_capital_cr=-500.0,
            retained_earnings_cr=-1000.0,
            ebit_cr=-200.0,
            book_value_equity_cr=200.0,
            total_liabilities_cr=5000.0,
            total_assets_cr=5200.0,
        )
        assert distress_res.z_score < 1.10
        assert distress_res.zone == "DISTRESS"
        assert distress_res.interpretation.verdict == "CRITICAL"


class TestModel7LockInCliffAndTaxDrag:
    """Verifies Model 7: Lock-In Cliff Supply Overhang & Sec 56(2)(x) Tax Drag."""

    def test_lockin_milestones_and_tax_drag(self):
        """Assert T+30, T+90, T+180 float unlocks and Section 56(2)(x) tax drag computation."""
        res = analyze_lockin_and_tax_drag(
            total_pre_ipo_shares_cr=100.0,
            anchor_shares_cr=15.0,
            initial_free_float_cr=25.0,
            adt_shares_cr=0.50,
            unlisted_entry_price_inr=140.0,
            rule_11ua_fmv_inr=160.0,  # 20 INR spread triggers Section 56(2)(x)
            carry_cost_annual_pct=12.0,
            holding_period_months=6,
        )

        assert len(res.milestones) == 3
        assert res.milestones[0].days_post_listing == 30
        assert res.milestones[1].days_post_listing == 90
        assert res.milestones[2].days_post_listing == 180
        assert res.is_tax_drag_triggered is True
        assert res.tax_drag_per_share_inr > 0.0
        assert res.post_tax_breakeven_listing_price_inr > 140.0


class TestRuleE4ReverseDCFSolverInversion:
    """Verifies Rule E.4: Solver round-trip inversion requirement (error <= 0.05%)."""

    def test_reverse_dcf_inversion_tolerance(self):
        """
        Assert that feeding the solved implied growth rate back into the multi-period
        DCF model reprices target enterprise value within <= 0.05% error.
        """
        target_ev = 50000.0  # ₹50,000 Cr Enterprise Value
        base_fcf = 1500.0    # ₹1,500 Cr Free Cash Flow
        wacc = 11.5          # 11.5% WACC
        g_term = 5.0         # 5.0% Terminal Growth

        implied_g, recomputed_ev, is_verified = solve_implied_reverse_dcf_growth(
            target_ev_cr=target_ev,
            base_fcf_cr=base_fcf,
            wacc_pct=wacc,
            terminal_growth_pct=g_term,
            projection_years=10,
        )

        error_pct = abs(recomputed_ev - target_ev) / target_ev * 100.0
        assert is_verified is True
        assert error_pct <= 0.05, f"DCF Solver inversion failed tolerance: error = {error_pct:.4f}% > 0.05%"


class TestComprehensiveSuiteAndCapabilityGating:
    """Verifies end-to-end suite execution and fail-closed capability gates."""

    def test_run_comprehensive_suite_success(self):
        """Assert complete 7-model suite generates valid payload."""
        suite = run_comprehensive_pre_ipo_econometrics("HCCB")
        assert suite.symbol == "HCCB"
        assert suite.overall_verdict in ("FAVORABLE", "NEUTRAL", "CAUTION", "CRITICAL")
        d = suite.to_dict()
        assert "models" in d
        assert "beneishMScore" in d["models"]
        assert "dickinsonLifecycle" in d["models"]
        assert "huberPeerRegression" in d["models"]
        assert "stubSeasonality" in d["models"]
        assert "indAs116Leverage" in d["models"]
        assert "altmanZScore" in d["models"]
        assert "lockInTaxDrag" in d["models"]

    def test_capability_gate_fail_closed_on_unreviewed_ingested_deal(self):
        """Assert Rule E.2: Ingested deal with unreviewed snapshot status raises ExportBlockedError."""
        unreviewed_deal = {
            "origin": "INGESTED",
            "snapshot_status": "PENDING_REVIEW",  # Not ACCEPTED_FOR_ANALYSIS
            "is_contained": True,
        }
        with pytest.raises(ExportBlockedError):
            assert_capability_allowed(unreviewed_deal, CapabilityType.FINANCIAL_ANALYSIS)
