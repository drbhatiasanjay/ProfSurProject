"""
Integration Tests for Pre-IPO Knowledge Graph Endpoints
Milestone 11.3 - Phase 3 Verification

Tests:
1. Ingestion endpoint returns SUCCESS with verified SHACL conformance.
2. Graph canvas endpoint exports @xyflow/react format.
3. Query router handles Tier 1, Tier 2, and Tier 3 with exact ground truth.
4. SHACL audit endpoint emits statutory compliance report.
5. Live valuation simulator recalculates football field fair multiple.
"""

import pytest
from models.pre_ipo_kg_engine import get_kg_engine, PreIPOPropertyGraphEngine
import models.pre_ipo_kg_engine as kg_engine_module
from api.server import (
    ingest_pre_ipo_knowledge_graph,
    get_pre_ipo_graph_canvas,
    query_pre_ipo_knowledge_graph,
    get_pre_ipo_shacl_audit,
    get_pre_ipo_valuation_simulation,
    KGQueryRequest
)


@pytest.fixture(autouse=True)
def isolated_in_memory_kg():
    """Ensures test suite uses an isolated in-memory DuckDB instance to avoid file locks."""
    engine = PreIPOPropertyGraphEngine(in_memory=True)
    kg_engine_module._GLOBAL_KG_ENGINE = engine
    yield engine
    try:
        engine.conn.close()
    except Exception:
        pass
    kg_engine_module._GLOBAL_KG_ENGINE = None


def test_kg_ingest_endpoint():
    """Asserts that the ingestion endpoint commits valid benchmark data."""
    res = ingest_pre_ipo_knowledge_graph("HCCH")
    assert res["status"] == "SUCCESS"
    assert res["symbol"] == "HCCH"
    assert res["nodesCount"] >= 9
    assert res["shaclConforms"] is True


def test_kg_graph_canvas_endpoint():
    """Asserts that canvas endpoint returns @xyflow/react node and edge arrays."""
    res = get_pre_ipo_graph_canvas("HCCH")
    assert res["symbol"] == "HCCH"
    assert "canvas" in res
    assert len(res["canvas"]["nodes"]) >= 5
    assert len(res["canvas"]["edges"]) >= 4


def test_kg_query_tier1_simple():
    """Verifies Tier 1 1-hop query returns 100% OFS offer anatomy."""
    req = KGQueryRequest(tier=1)
    res = query_pre_ipo_knowledge_graph(req)
    assert "verdict" in res
    assert "100% OFFER FOR SALE" in res["verdict"]["headline"]
    assert res["metrics"]["freshIssueCr"] == 0.0
    assert len(res["verdict"]["citations"]) >= 3


def test_kg_query_tier2_medium():
    """Verifies Tier 2 2-hop query correlates Q1 FY27 EBITDA margin jump to parent incentives."""
    req = KGQueryRequest(tier=2)
    res = query_pre_ipo_knowledge_graph(req)
    assert "verdict" in res
    assert "MARGIN EXPANSION" in res["verdict"]["headline"]
    assert res["metrics"]["reportedEbitdaMarginPct"] == 17.20
    assert res["metrics"]["hccbLitigationPctTNW"] == 45.60


def test_kg_query_tier3_complex():
    """Verifies Tier 3 3+ hop query detects channel distress & computes valuation haircut."""
    req = KGQueryRequest(tier=3, pruningThreshold=0.65)
    res = query_pre_ipo_knowledge_graph(req)
    assert "verdict" in res
    assert "RED RISK VETO" in res["verdict"]["headline"]
    assert res["valuation"]["peerMultiple"] == 45.0
    assert res["valuation"]["warrantedMultiple"] == 29.25
    assert res["valuation"]["discountPct"] == 35.0


def test_kg_query_natural_language_routing():
    """Verifies natural language query routes to appropriate tier."""
    req = KGQueryRequest(query="Where is the IPO money going?")
    res = query_pre_ipo_knowledge_graph(req)
    assert "100% OFFER FOR SALE" in res["verdict"]["headline"]


def test_kg_shacl_audit_endpoint():
    """Verifies SHACL audit endpoint confirms statutory closed-world conformity."""
    res = get_pre_ipo_shacl_audit("HCCH")
    assert res["symbol"] == "HCCH"
    assert res["conforms"] is True
    assert res["violationCount"] == 0


def test_kg_valuation_simulator_endpoint():
    """Verifies live valuation simulator dynamically reprices fair multiple."""
    res = get_pre_ipo_valuation_simulation("HCCH", territory_discount=25.0, channel_discount=10.0)
    assert res["symbol"] == "HCCH"
    assert res["totalHaircutPct"] == 35.0
    assert res["warrantedMultiple"] == 29.25
    assert len(res["footballField"]) == 3
