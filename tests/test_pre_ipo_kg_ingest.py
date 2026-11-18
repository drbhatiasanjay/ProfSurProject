"""
TDD Tests for Property Graph Engine & HCCH Benchmark Ingestion
Milestone 11.2 - Phase 2 Verification

Verifies:
1. Ingestion of HCCH DRHP entities and relationships into DuckDB/NetworkX engine.
2. Complete W3C PROV-O metadata coverage (page >= 1, bounding box, confidence >= 0.85).
3. Multi-hop forensic pathfinding (HCCH -> HCCB -> Cheque Bounces -> North Territories).
4. Export format conformance to @xyflow/react (React Flow) canvas schema.
"""

from models.pre_ipo_kg_engine import PreIPOPropertyGraphEngine
from models.pre_ipo_kg_ingest import ingest_hcch_benchmark_graph


def test_hcch_benchmark_ingestion():
    """Asserts that all HCCH entities and edges are populated in the in-process graph."""
    engine = PreIPOPropertyGraphEngine(in_memory=True)
    summary = ingest_hcch_benchmark_graph(engine)

    assert summary["status"] == "SUCCESS"
    assert summary["symbol"] == "HCCH"
    assert summary["nodesCount"] >= 9
    assert summary["edgesCount"] >= 8

    # Verify primary issuer node
    hcch_node = engine.get_node("HCCH")
    assert hcch_node is not None
    assert hcch_node.properties["isHoldco"] is True
    assert hcch_node.properties["role"] == "Issuer"

    # Verify material operating subsidiary node
    hccb_node = engine.get_node("HCCB")
    assert hccb_node is not None
    assert hccb_node.properties["isMaterial"] is True
    assert hccb_node.properties["operatingPlants"] == 14

    # Verify 100% OFS offering node
    offering_node = engine.get_node("OFFERING_2026")
    assert offering_node is not None
    assert offering_node.properties["freshIssueCr"] == 0.0  # Rule E.3 Zero-truthiness
    assert offering_node.properties["totalSizeCr"] == 12500.0


def test_w3c_provo_metadata_completeness():
    """Asserts that every node carries verified physical page, bounding box, and quote."""
    engine = PreIPOPropertyGraphEngine(in_memory=True)
    ingest_hcch_benchmark_graph(engine)

    for node_id in engine.graph.nodes:
        node = engine.get_node(node_id)
        assert node is not None
        assert node.source_document == "Hindustan_Coca_Cola_Holdings_DRHP.pdf"
        assert node.page_number is not None and node.page_number >= 1
        assert node.bounding_box is not None and len(node.bounding_box) == 4
        assert node.confidence_score is not None and node.confidence_score >= 0.85
        assert node.verbatim_quote is not None and len(node.verbatim_quote) > 10


def test_multihop_forensic_contagion_path():
    """Traces 3-hop contagion path: HCCB -> Cheque Bounces -> North Territories."""
    engine = PreIPOPropertyGraphEngine(in_memory=True)
    ingest_hcch_benchmark_graph(engine)

    # Multi-hop query: (Subsidiary) -> (Litigation) -> (Territory)
    paths = engine.query_multihop(start_label="Subsidiary", rel_chain=["DEFENDANT_IN", "CONCENTRATED_IN"])

    assert len(paths) >= 1
    found_contagion = False
    for p in paths:
        step1 = p[1]  # HCCB -[:DEFENDANT_IN]-> LIT_SEC_138_CLUSTER
        step2 = p[2]  # LIT_SEC_138_CLUSTER -[:CONCENTRATED_IN]-> TERRITORY_NORTH_5
        if step1["to"] == "LIT_SEC_138_CLUSTER" and step2["to"] == "TERRITORY_NORTH_5":
            found_contagion = True
            break

    assert found_contagion is True, "Multi-hop channel distress contagion path must exist!"


def test_shortest_path_litigation_to_offering():
    """Asserts shortest topological path between operating lawsuit and public offering."""
    engine = PreIPOPropertyGraphEngine(in_memory=True)
    ingest_hcch_benchmark_graph(engine)

    path = engine.find_shortest_path("LIT_HCCB_TAX", "OFFERING_2026")
    assert path is not None
    # Expected topological chain: LIT_HCCB_TAX <-> HCCB <-> HCCH ...
    assert path[0] == "LIT_HCCB_TAX"
    assert path[-1] == "OFFERING_2026"
    assert "HCCB" in path


def test_react_flow_canvas_export():
    """Asserts that subgraph export produces valid @xyflow/react node/edge schema."""
    engine = PreIPOPropertyGraphEngine(in_memory=True)
    ingest_hcch_benchmark_graph(engine)

    canvas_data = engine.get_subgraph("HCCH", max_depth=2)

    assert "nodes" in canvas_data and "edges" in canvas_data
    assert len(canvas_data["nodes"]) >= 5
    assert len(canvas_data["edges"]) >= 4

    # Verify first node structure
    sample_node = canvas_data["nodes"][0]
    assert "id" in sample_node
    assert "type" in sample_node and sample_node["type"] == "financialCardNode"
    assert "data" in sample_node
    assert "pageNumber" in sample_node["data"]
    assert "confidence" in sample_node["data"]

    # Verify first edge structure
    sample_edge = canvas_data["edges"][0]
    assert "source" in sample_edge
    assert "target" in sample_edge
    assert "label" in sample_edge
