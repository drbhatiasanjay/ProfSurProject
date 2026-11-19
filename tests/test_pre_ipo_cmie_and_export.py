"""
Adversarial Unit Test Suite for CMIE Macro Linkage & Post-IPO Export
Milestone 16 & 17 (Phase 2C & Phase 2D)

Verifies:
- Peer relative valuation differentials and ROCE gap vs Varun Beverages (VBL)
- Macro crude and repo rate transmission elasticity and Zero-Truthiness (Rule E.3)
- Anchor investor 30-day and 90-day supply cliff calculations
- W3C RDF Turtle, Neo4j Cypher, and JSON-LD institutional export fidelity
- SHA-256 cryptographic compliance audit manifest
"""

import pytest
from models.pre_ipo_cmie_macro_engine import CMIEMacroEngine, CMIE_BEVERAGE_PEERS
from models.pre_ipo_post_ipo_simulator import PostIPOSimulator
from models.pre_ipo_institutional_exporter import PreIPOInstitutionalExporter


@pytest.fixture
def cmie_engine():
    return CMIEMacroEngine()


@pytest.fixture
def post_ipo_sim():
    return PostIPOSimulator()


@pytest.fixture
def exporter():
    return PreIPOInstitutionalExporter("HCCH")


def test_cmie_peer_comparison_and_vbl_spread(cmie_engine):
    """Verifies peer comparison metrics and relative discount vs Varun Beverages."""
    res = cmie_engine.get_peer_comparison()
    assert "issuer" in res
    assert "peers" in res
    assert len(res["peers"]) >= 3

    spread = res["relative_spread"]
    assert spread["hccb_ask_multiple"] == 24.5
    assert spread["vbl_trading_multiple"] == 38.5
    # (38.5 - 24.5) / 38.5 = 36.36%
    assert spread["multiple_discount_pct"] == 36.36
    assert spread["roce_differential_pct"] == 8.6  # 28.4% - 19.8%


def test_rule_e3_macro_shock_zero_truthiness(cmie_engine):
    """Rule E.3: Preserves zero values without fallback defaults."""
    res = cmie_engine.simulate_macro_shock(brent_crude_shift_usd=0.0, rbi_repo_shift_bps=0.0)
    assert res.base_crude_usd == 78.0
    assert res.shocked_crude_usd == 78.0
    assert res.pet_resin_inflation_pct == 0.0
    assert res.gross_margin_compression_bps == 0.0
    assert res.post_shock_gross_margin_pct == 51.4
    assert res.incremental_borrowing_cost_cr == 0.0
    assert len(res.macro_causal_nodes) == 6
    assert len(res.macro_causal_edges) == 5


def test_severe_crude_and_repo_shock_compression(cmie_engine):
    """Simulates +$25/bbl crude surge and +150 bps RBI repo hike."""
    res = cmie_engine.simulate_macro_shock(brent_crude_shift_usd=25.0, rbi_repo_shift_bps=150.0)
    assert res.shocked_crude_usd == 103.0
    assert res.pet_resin_inflation_pct > 15.0
    assert res.gross_margin_compression_bps > 0.0
    assert res.post_shock_gross_margin_pct < 51.4
    assert res.incremental_borrowing_cost_cr > 20.0
    assert "SUBSCRIBE" in res.ic_guidance or "AVOID" in res.ic_guidance


def test_anchor_lockin_cliff_schedule(post_ipo_sim):
    """Verifies anchor 30-day and 90-day supply wall tranches."""
    res = post_ipo_sim.simulate_anchor_cliff(fpi_momentum_share_pct=50.0)
    assert res.total_offering_shares == 997_500_000
    assert res.anchor_allocation_shares == 299_250_000
    assert res.tranche_30d_shares == 149_625_000
    assert res.tranche_90d_shares == 149_625_000
    assert res.t30_float_expansion_pct > 20.0
    assert len(res.cliff_schedule) == 4
    assert res.cliff_schedule[1]["milestone"] == "T+30 Days"


def test_listing_day_discovery_and_bhar(post_ipo_sim):
    """Verifies Day 1 retail flipping and 12-month BHAR decay generation."""
    listing = post_ipo_sim.simulate_listing_discovery(gmp_inr=25.0, qib_multiple=8.5)
    assert listing.estimated_listing_price_inr == 125.0
    assert listing.estimated_listing_gain_pct == 25.0
    assert listing.first_120min_retail_flip_shares > 100_000_000
    assert listing.order_book_depth_resilience == "DEEP"

    bhar = post_ipo_sim.generate_bhar_decay(shock_active=True)
    assert len(bhar) == 12
    assert bhar[0]["stressed_alpha_pct"] < bhar[0]["base_alpha_pct"] or bhar[11]["stressed_alpha_pct"] < bhar[11]["base_alpha_pct"]


def test_institutional_w3c_rdf_turtle_export(exporter):
    """Verifies W3C RDF Turtle format validity."""
    ttl = exporter.export_w3c_rdf_turtle()
    assert "@prefix fibo-fnd-pty:" in ttl
    assert "@prefix sebi:" in ttl
    assert "inst:SEC_06_LEGAL_LITIGATION" in ttl
    assert "inst:FACT_S06_01_CESTAT_INDIRECT_TAX" in ttl
    assert "4455.47" in ttl


def test_institutional_neo4j_cypher_export(exporter):
    """Verifies Neo4j Cypher ingestion script syntax and constraints."""
    cypher = exporter.export_neo4j_cypher_script()
    assert "CREATE CONSTRAINT" in cypher
    assert "MERGE (s:StatutorySection" in cypher
    assert "MERGE (f:VerbatimFact" in cypher
    assert "[:DISCLOSES_FACT]" in cypher


def test_institutional_json_ld_export(exporter):
    """Verifies FIBO-compliant JSON-LD linked data tree."""
    jsonld = exporter.export_fibo_json_ld()
    assert "@context" in jsonld
    assert "@graph" in jsonld
    assert len(jsonld["@graph"]) >= 25


def test_sebi_audit_manifest_cryptographic_checksum(exporter):
    """Verifies SHA-256 cryptographic compliance audit manifest."""
    manifest = exporter.generate_sebi_audit_manifest()
    assert manifest["symbol"] == "HCCH"
    assert manifest["sebi_icdr_schedule_vi_compliant"] is True
    assert manifest["shacl_closed_world_conforms"] is True
    assert len(manifest["sha256_checksum"]) == 64
    assert manifest["total_statutory_sections"] == 8
    assert manifest["total_verbatim_facts_verified"] == 19
