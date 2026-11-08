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
    generate_financials_narrative,
    generate_indebtedness_narrative,
    generate_stress_narrative,
    generate_objects_narrative,
    generate_cap_table_narrative,
    generate_forensics_narrative,
    generate_valuation_narrative,
    generate_anchor_lockin_calendar,
)


def test_pre_ipo_registry_loads_all_five_deals():
    assert len(PRE_IPO_REGISTRY) == 5
    expected_keys = {"mankind_pharma", "afcons_infra", "swiggy", "tata_technologies", "ntpc_green"}
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


def test_cap_table_dilution_and_lock_in():
    mankind = PRE_IPO_REGISTRY["mankind_pharma"]
    assert mankind.cap_table is not None
    assert mankind.cap_table.promoter_holding_pre_pct == 79.0
    assert mankind.cap_table.promoter_holding_post_pct == 76.5
    assert mankind.cap_table.promoter_dilution_pct == 2.5
    assert mankind.cap_table.promoter_min_contribution_lock_months == 18
    assert mankind.cap_table.anchor_lock_30d_pct == 50.0
    assert mankind.cap_table.anchor_lock_90d_pct == 50.0


def test_objects_of_offer_and_sebi_gcp_compliance():
    afcons = PRE_IPO_REGISTRY["afcons_infra"]
    assert afcons.objects_of_offer is not None
    assert afcons.objects_of_offer.gross_fresh_issue_cr == 1250.0
    assert afcons.objects_of_offer.debt_prepayment_cr == 800.0
    assert afcons.objects_of_offer.general_corporate_purposes_cr == 250.0
    assert afcons.objects_of_offer.gcp_pct_of_gross == 20.0
    assert afcons.objects_of_offer.sebi_gcp_compliant is True
    assert afcons.objects_of_offer.annual_interest_savings_cr == pytest.approx(78.4, rel=1e-2)
    assert afcons.objects_of_offer.pro_forma_pat_accretion_cr > 50.0


def test_beneish_forensics_and_m_score():
    mankind = PRE_IPO_REGISTRY["mankind_pharma"]
    assert mankind.beneish_forensics is not None
    assert mankind.beneish_forensics.m_score <= -1.78
    assert mankind.beneish_forensics.is_manipulation_risk is False

    tata = PRE_IPO_REGISTRY["tata_technologies"]
    assert tata.beneish_forensics is not None
    assert tata.beneish_forensics.m_score <= -1.78
    assert tata.beneish_forensics.is_manipulation_risk is False


def test_debt_maturity_ladder():
    afcons = PRE_IPO_REGISTRY["afcons_infra"]
    assert afcons.debt_maturity is not None
    assert afcons.debt_maturity.repayment_due_year_1_cr == 1240.0
    assert afcons.debt_maturity.total_repayment_profile_cr == pytest.approx(4188.0, rel=1e-3)
    assert afcons.debt_maturity.floating_rate_debt_pct == 85.0


def test_valuation_peer_benchmarking():
    tata = PRE_IPO_REGISTRY["tata_technologies"]
    assert tata.valuation_comps is not None
    assert tata.valuation_comps.implied_pe_ratio == 32.5
    assert tata.valuation_comps.peer_median_pe > 35.0
    assert tata.valuation_comps.pe_discount_to_peers_pct > 0  # Trading at discount to peers
    assert tata.valuation_comps.valuation_verdict == "ATTRACTIVE_DISCOUNT"


def test_investment_committee_verdict():
    mankind = PRE_IPO_REGISTRY["mankind_pharma"]
    assert mankind.ic_verdict is not None
    assert mankind.ic_verdict.underwriting_verdict == "APPROVE WITH COVENANTS"
    assert len(mankind.ic_verdict.key_credit_strengths) >= 3
    assert len(mankind.ic_verdict.mandatory_loan_covenants) >= 3

    afcons = PRE_IPO_REGISTRY["afcons_infra"]
    assert afcons.ic_verdict is not None
    assert afcons.ic_verdict.underwriting_verdict == "DELEVERAGING MANDATE"


def test_narrative_synthesis_and_calls_to_action():
    deal = PRE_IPO_REGISTRY["mankind_pharma"]
    
    fin_nar = generate_financials_narrative(deal)
    assert "CAGR" in fin_nar["what_you_see"]
    assert "Call to Action" not in fin_nar["what_you_see"]
    assert "working capital" in fin_nar["call_to_action"].lower()

    obj_nar = generate_objects_narrative(deal)
    assert len(obj_nar["what_you_see"]) > 20
    assert len(obj_nar["call_to_action"]) > 20

    ct_nar = generate_cap_table_narrative(deal)
    assert "Promoter shareholding transitions" in ct_nar["what_you_see"]
    assert "lock-in" in ct_nar["call_to_action"].lower()

    forensic_nar = generate_forensics_narrative(deal)
    assert "Beneish (1999)" in forensic_nar["what_you_see"]
    assert "receivables" in forensic_nar["call_to_action"].lower()


def test_even_count_peer_median():
    from models.pre_ipo_schema import ValuationPeerBenchmarking, ListedPeerComp
    bench = ValuationPeerBenchmarking(
        price_band_lower_inr=100.0,
        price_band_upper_inr=108.0,
        implied_mcap_cr=5000.0,
        implied_ev_cr=5200.0,
        implied_pe_ratio=12.0,
        implied_ev_ebitda=8.0,
        implied_ev_sales=2.0,
        implied_pb_ratio=3.0,
        sector_peer_group="Test Peers",
        valuation_verdict="FAIR_VALUE",
        peers=[
            ListedPeerComp(
                peer_name="Peer A",
                ticker="PEERA",
                mcap_cr=5000.0,
                pe_ratio=10.0,
                ev_ebitda=6.0,
                ev_sales=2.0,
                pb_ratio=2.5,
                pat_margin_pct=10.0,
                roe_pct=15.0,
                dickinson_stage="Mature",
            ),
            ListedPeerComp(
                peer_name="Peer B",
                ticker="PEERB",
                mcap_cr=8000.0,
                pe_ratio=20.0,
                ev_ebitda=14.0,
                ev_sales=3.0,
                pb_ratio=4.0,
                pat_margin_pct=12.0,
                roe_pct=18.0,
                dickinson_stage="Mature",
            ),
        ]
    )
    # Even count median for [10, 20] must be exactly (10+20)/2 = 15.0
    assert bench.peer_median_pe == 15.0
    assert bench.peer_median_ev_ebitda == 10.0


def test_persona_decision_views():
    from models.pre_ipo_engine import generate_persona_decision_view
    mankind = PRE_IPO_REGISTRY["mankind_pharma"]
    for p in ["cfo", "lender", "investor", "retail", "board", "compliance"]:
        view = generate_persona_decision_view(mankind, persona=p)
        assert "title" in view
        assert "focus" in view
        assert "decision_question" in view
        assert "recommendation" in view
        assert "trade_offs" in view
        assert len(view["key_metrics"]) >= 3

    # Verify CFO vs Lender lenses differ in decision framing while referencing same underlying facts
    cfo_view = generate_persona_decision_view(mankind, persona="cfo")
    lender_view = generate_persona_decision_view(mankind, persona="lender")
    assert "Liquidity" in cfo_view["focus"] or "Capital" in cfo_view["focus"]
    assert "Covenant" in lender_view["focus"] or "Default" in lender_view["focus"]


def test_decision_limitations_structure():
    afcons = PRE_IPO_REGISTRY["afcons_infra"]
    assert len(afcons.limitations) > 0
    first_lim = afcons.limitations[0]
    assert first_lim.gap_id.startswith("GAP-")
    assert first_lim.materiality_priority in ("HIGH", "MEDIUM", "LOW")
    assert len(first_lim.recommended_diligence_request) > 10


def test_invalid_pdf_bytes_safety():
    import io
    from models.pre_ipo_ingest import PreIPOIngestionEngine
    corrupted_stream = io.BytesIO(b"%PDF-1.4\ncorrupted content that has no searchable tables or text...")
    dossier = PreIPOIngestionEngine.ingest_document(corrupted_stream, company_name_hint="Unknown Target Corp")
    assert dossier.deal_id in ("unverified_upload", "unverified_scanned_upload")
    assert dossier.history[0].revenue_ops_cr == 0.0
    assert dossier.ic_verdict.underwriting_verdict in ("INSUFFICIENT DATA TO CONCLUDE", "INSUFFICIENT_DISCLOSURES_UNRATED")
    assert any(lim.current_status in ("PARSE_FAILED", "AWAITING_OCR_KEY", "NOT_EXTRACTED", "OCR_CONSENT_REQUIRED") for lim in dossier.limitations)


def test_ntpc_green_deal_structure():
    deal = PRE_IPO_REGISTRY["ntpc_green"]
    assert deal.company_name == "NTPC Green Energy Limited (NGEL)"
    assert deal.total_issue_size_cr == 10000.00
    assert deal.fresh_issue_cr == 10000.00
    assert deal.ofs_cr == 0.00
    assert deal.fresh_issue_pct == 100.0
    assert deal.ofs_pct == 0.0
    assert deal.objects_of_offer.debt_prepayment_cr == 7500.00
    assert deal.objects_of_offer.general_corporate_purposes_cr == 2350.00
    assert deal.objects_of_offer.sebi_gcp_compliant is True
    # Test EPS accretion math
    assert deal.objects_of_offer.is_dilutive is False
    assert deal.objects_of_offer.eps_accretion_dilution_inr > 0.0


def test_anchor_lockin_calendar():
    deal = PRE_IPO_REGISTRY["ntpc_green"]
    cal = generate_anchor_lockin_calendar(deal)
    assert len(cal) == 4
    # Day 0, Day 30, Day 90, Day 180
    assert cal[0].days_from_listing == 0
    assert cal[1].days_from_listing == 30
    assert cal[2].days_from_listing == 90
    assert cal[3].days_from_listing == 180
    # 50% unlock on Day 30 and remaining 50% on Day 90
    assert cal[1].unlocked_pct == 50.0
    assert cal[2].unlocked_pct == 50.0
    assert cal[1].unlocked_value_cr > 1000.0  # Massive anchor tranche
    assert cal[1].supply_risk_level == "HIGH"



