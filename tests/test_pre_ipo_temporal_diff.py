"""
Adversarial Unit Test Suite for Bi-Temporal Knowledge Graph & Filing Diff Engine
Milestone 19 - Temporal Knowledge Graph & Multi-DRHP Filing Comparison Diff Engine

Governed by:
- Rule E.1: Zero Dead Helpers / End-to-End Production Wiring
- Rule E.2: Fail-Closed Architecture (FilingNotFoundError)
- Rule E.3: Zero-Truthiness Financial Calculations
- Rule E.4: Solver Round-Trip Inversion Requirement (<= 0.05% tolerance)
"""

import pytest
import math

from models.pre_ipo_temporal_schema import (
    FilingNotFoundError,
    TemporalBoundingBox,
    TemporalGraphMutation,
    TemporalGraphDiffResult
)
from models.pre_ipo_temporal_diff_engine import (
    PreIPOTemporalDiffEngine,
    AVAILABLE_FILING_VERSIONS
)


def test_fail_closed_on_missing_or_invalid_filing_version():
    """Rule E.2: Engine must fail closed with FilingNotFoundError for invalid filing versions."""
    engine = PreIPOTemporalDiffEngine("HCCH")

    # Nonexistent version string
    with pytest.raises(FilingNotFoundError) as exc_info:
        engine.compute_temporal_diff("DRHP", "NONEXISTENT_VERSION")
    assert "NONEXISTENT_VERSION" in str(exc_info.value)

    # None version
    with pytest.raises(FilingNotFoundError):
        engine.compute_temporal_diff(None, "RHP")

    # Empty string
    with pytest.raises(FilingNotFoundError):
        engine.compute_temporal_diff("   ", "RHP")


def test_diff_identity_same_version_returns_zero_mutations():
    """Diffing identical filing versions must yield zero mutations and zero drift (identity law)."""
    engine = PreIPOTemporalDiffEngine("HCCH")
    res = engine.compute_temporal_diff("DRHP", "DRHP")

    assert res.total_mutations == 0
    assert len(res.mutations) == 0
    assert res.net_valuation_impact_inr == 0.0
    assert res.net_wacc_spread_shift_bps == 0.0
    assert res.overall_obfuscation_index == 0.0
    assert all(score == 0.0 for score in res.chapter_drift_scores.values())


def test_bi_temporal_diff_mutation_count_and_types():
    """Verifies that mutations cover official SEBI ICDR chapters and mutation classifications."""
    engine = PreIPOTemporalDiffEngine("HCCH")
    res = engine.compute_temporal_diff("DRHP", "RHP")

    assert res.symbol == "HCCH"
    assert res.base_version == "DRHP"
    assert res.target_version == "RHP"
    assert res.total_mutations >= 8

    types = {m.change_type for m in res.mutations}
    assert "BRACKET_RESOLVED" in types
    assert "MUTATED_PROPERTY" in types
    assert "ENTITY_ADDED" in types
    assert "QUALIFIER_WATERED_DOWN" in types


def test_rule_e3_zero_truthiness_preservation():
    """Rule E.3: 0.0, 0%, and 0 are valid financial values distinct from absence (None)."""
    engine = PreIPOTemporalDiffEngine("HCCH")
    res = engine.compute_temporal_diff("DRHP", "RHP")

    # Mutation 1 has 0.0 valuation impact and 0.0 wacc shift
    m1 = next(m for m in res.mutations if m.mutation_id == "MUT_01_PRICE_BAND")
    assert m1.valuation_impact_inr == 0.0
    assert m1.wacc_spread_shift_bps == 0.0
    assert m1.drhp_value is not None

    # Mutation 6 has 0.0 valuation impact and 0.0 wacc shift
    m6 = next(m for m in res.mutations if m.mutation_id == "MUT_06_ANCHOR_LOCKIN")
    assert m6.valuation_impact_inr == 0.0
    assert m6.wacc_spread_shift_bps == 0.0


def test_rule_e4_solver_round_trip_inversion():
    """Rule E.4: Repricing fair value and inverting back must reprice within <= 0.05% tolerance."""
    engine = PreIPOTemporalDiffEngine("HCCH")
    res = engine.compute_temporal_diff("DRHP", "RHP")

    base_fair_value = 1480.00
    shares_cr = 85.0

    # 1. Forward repricing
    recalculated_price = engine.reprice_with_mutations(base_fair_value, res, shares_outstanding_cr=shares_cr)

    # Expected per-share delta: net_valuation_impact_inr / shares_cr
    expected_delta = res.net_valuation_impact_inr / shares_cr
    expected_price = round(base_fair_value + expected_delta, 2)
    assert recalculated_price == expected_price

    # 2. Inversion round-trip
    implied_impact = engine.invert_reprice_delta(recalculated_price, base_fair_value, shares_outstanding_cr=shares_cr)

    # 3. Assert relative tolerance <= 0.05% (0.0005)
    pct_error = abs(implied_impact - res.net_valuation_impact_inr) / abs(res.net_valuation_impact_inr)
    assert pct_error <= 0.0005, f"Inversion error {pct_error * 100:.4f}% exceeds 0.05% tolerance!"


def test_cohen_malloy_obfuscation_coordinate_drift():
    """Tests detection of physical displacement / strategic evasion between chapters."""
    engine = PreIPOTemporalDiffEngine("HCCH")
    res = engine.compute_temporal_diff("DRHP", "RHP")

    # Mutation 8 (Groundwater NOC) moved from Chapter I (p. 22) to Chapter XI (p. 392)
    m8 = next(m for m in res.mutations if m.mutation_id == "MUT_08_CGWA_NOC_PENALTY")
    assert m8.drhp_bbox.page_number == 22
    assert m8.rhp_bbox.page_number == 392
    assert m8.obfuscation_severity >= 0.70
    assert "Displaced +370 pages" in m8.w3c_prov_citation

    # Overall obfuscation index should reflect aggregate evasion severity
    assert 0.30 <= res.overall_obfuscation_index <= 0.80


def test_parent_indemnity_shield_offset():
    """Verifies that parent indemnity economically ring-fences unshielded litigation demands."""
    engine = PreIPOTemporalDiffEngine("HCCH")
    res = engine.compute_temporal_diff("DRHP", "RHP")

    cestat_mut = next(m for m in res.mutations if m.mutation_id == "MUT_03_CESTAT_EXCISE_DEMAND")
    indemnity_mut = next(m for m in res.mutations if m.mutation_id == "MUT_04_PARENT_INDEMNITY")

    assert cestat_mut.valuation_impact_inr == -431.18
    assert indemnity_mut.valuation_impact_inr == 431.18

    net_litigation_impact = cestat_mut.valuation_impact_inr + indemnity_mut.valuation_impact_inr
    assert net_litigation_impact == 0.0


def test_sebi_11_chapter_drift_distribution():
    """Verifies that chapter drift scores are accurately aggregated for all 11 statutory chapters."""
    engine = PreIPOTemporalDiffEngine("HCCH")
    res = engine.compute_temporal_diff("DRHP", "RHP")

    assert len(res.chapter_drift_scores) == 11
    assert "CHAPTER_I_RISK_FACTORS" in res.chapter_drift_scores
    assert "CHAPTER_II_CAPITAL_STRUCTURE" in res.chapter_drift_scores
    assert "CHAPTER_X_LEGAL_OUTSTANDING_LITIGATION" in res.chapter_drift_scores

    # Chapters with heavy mutations should have positive drift scores
    assert res.chapter_drift_scores["CHAPTER_II_CAPITAL_STRUCTURE"] > 0.0
    assert res.chapter_drift_scores["CHAPTER_X_LEGAL_OUTSTANDING_LITIGATION"] > 0.0


def test_serialization_and_w3c_prov_citations():
    """Verifies JSON serializability and W3C PROV-O compliance."""
    engine = PreIPOTemporalDiffEngine("HCCH")
    res = engine.compute_temporal_diff("DRHP", "RHP")
    d = res.to_dict()

    assert d["symbol"] == "HCCH"
    assert len(d["mutations"]) == res.total_mutations
    for m in d["mutations"]:
        assert m["w3c_prov_citation"] != ""
        assert m["rhp_bbox"]["page_number"] > 0


def test_diff_identity_when_base_equals_target():
    """Comparing an identical filing to itself must yield zero mutations and zero drift."""
    engine = PreIPOTemporalDiffEngine("HCCH")
    res = engine.compute_temporal_diff("DRHP", "DRHP")

    assert res.total_mutations == 0
    assert len(res.mutations) == 0
    assert res.net_valuation_impact_inr == 0.0
    assert res.net_wacc_spread_shift_bps == 0.0
    assert res.overall_obfuscation_index == 0.0
    assert all(score == 0.0 for score in res.chapter_drift_scores.values())


def test_api_temporal_endpoints_wiring_and_fail_closed():
    """Rule E.1 & E.2: Verify FastAPI routes wire through and fail closed with 404."""
    from fastapi import HTTPException
    from api.server import (
        get_temporal_filing_versions,
        get_temporal_graph_diff,
        get_verbatim_redline_snippet
    )

    # 1. Versions endpoint
    versions = get_temporal_filing_versions("HCCH")
    assert len(versions) == 3
    assert any(v["key"] == "DRHP" for v in versions)

    # 2. Diff endpoint happy path
    diff_data = get_temporal_graph_diff(symbol="HCCH", base_version="DRHP", target_version="RHP")
    assert diff_data["symbol"] == "HCCH"
    assert diff_data["total_mutations"] >= 8

    # 3. Diff endpoint fail closed (HTTPException 404)
    with pytest.raises(HTTPException) as exc_info:
        get_temporal_graph_diff(symbol="HCCH", base_version="INVALID_VERSION", target_version="RHP")
    assert exc_info.value.status_code == 404
    assert "not indexed" in exc_info.value.detail

    # 4. Redline snippet happy path
    redline_data = get_verbatim_redline_snippet(mutation_id="MUT_01_PRICE_BAND", symbol="HCCH")
    assert redline_data["mutation_id"] == "MUT_01_PRICE_BAND"
    assert redline_data["rhp_bbox"]["page_number"] > 0

    # 5. Redline snippet fail closed (HTTPException 404)
    with pytest.raises(HTTPException) as exc_info2:
        get_verbatim_redline_snippet(mutation_id="NONEXISTENT_ID", symbol="HCCH")
    assert exc_info2.value.status_code == 404
    assert "not found" in exc_info2.value.detail


