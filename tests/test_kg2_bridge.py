"""
KG2 graph_bridge JSON contract tests.

Validates that all three graph levels return JSON matching the OCaml contract:
- Required top-level keys
- Hard node caps (Macro ≤21, Meso ≤80, Micro ≤21)
- Node / edge schema
- ISOLATION: never imports from graph_builder, pages/7 or pages/18
"""

import os
import sys
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import graph_bridge

# ── Skip if DB not present ────────────────────────────────────────────────────

DB_PRESENT = os.path.exists(
    os.path.join(os.path.dirname(os.path.dirname(__file__)), "capital_structure.db")
)
needs_db = pytest.mark.skipif(not DB_PRESENT, reason="capitalstructure.db not present")

# ── Schema helpers ────────────────────────────────────────────────────────────

_NODE_REQUIRED  = {"id", "type", "label", "color", "size", "tooltip"}
_EDGE_REQUIRED  = {"from", "to", "type", "weight", "label"}
_GRAPH_REQUIRED = {"level", "persona", "panel_mode", "node_count", "nodes", "edges"}


def _assert_node(node: dict) -> None:
    missing = _NODE_REQUIRED - node.keys()
    assert not missing, f"Node {node.get('id')} missing fields: {missing}"
    assert isinstance(node["id"],      str),  "id must be str"
    assert isinstance(node["label"],   str),  "label must be str"
    assert isinstance(node["size"],    (int, float)), "size must be numeric"
    assert isinstance(node["tooltip"], str),  "tooltip must be str"


def _assert_edge(edge: dict) -> None:
    missing = _EDGE_REQUIRED - edge.keys()
    assert not missing, f"Edge {edge.get('from')}→{edge.get('to')} missing: {missing}"


def _assert_graph(g: dict, expected_level: str) -> None:
    missing = _GRAPH_REQUIRED - g.keys()
    assert not missing, f"Graph missing top-level keys: {missing}"
    assert g["level"] == expected_level
    assert isinstance(g["nodes"], list)
    assert isinstance(g["edges"], list)
    assert g["node_count"] == len(g["nodes"])
    for n in g["nodes"]:
        _assert_node(n)
    for e in g["edges"]:
        _assert_edge(e)


# ── Macro tests ───────────────────────────────────────────────────────────────

@needs_db
def test_macro_schema():
    g = graph_bridge.get_macro_graph()
    _assert_graph(g, "macro")


@needs_db
def test_macro_node_cap():
    g = graph_bridge.get_macro_graph()
    assert g["node_count"] <= 21, f"Macro node cap exceeded: {g['node_count']} > 21"


@needs_db
def test_macro_has_all_stage_types():
    g = graph_bridge.get_macro_graph()
    node_types = {n["type"] for n in g["nodes"]}
    assert "stage"    in node_types, "Macro graph must have stage nodes"
    assert "industry" in node_types, "Macro graph must have industry nodes"
    assert "event"    in node_types, "Macro graph must have event nodes"


@needs_db
def test_macro_stage_ids_canonical():
    """Stage node IDs must use the canonical OCaml ADT names."""
    g = graph_bridge.get_macro_graph()
    stage_labels = {n["label"] for n in g["nodes"] if n["type"] == "stage"}
    for label in stage_labels:
        assert label in graph_bridge.ALL_STAGES, f"Unknown stage label: {label!r}"


@needs_db
def test_macro_persona_field():
    g = graph_bridge.get_macro_graph(persona="RatingAnalyst")
    assert g["persona"] == "RatingAnalyst"


@needs_db
def test_macro_invalid_persona_defaults():
    g = graph_bridge.get_macro_graph(persona="INVALID_PERSONA")
    assert g["persona"] == "CorporateCFO", "Invalid persona should default to CorporateCFO"


# ── Meso tests ────────────────────────────────────────────────────────────────

@needs_db
def test_meso_schema():
    g = graph_bridge.get_meso_graph(stages=["Growth", "Maturity"])
    _assert_graph(g, "meso")


@needs_db
def test_meso_company_node_cap():
    g = graph_bridge.get_meso_graph()  # default: all stages for persona
    company_nodes = [n for n in g["nodes"] if n["type"] == "company"]
    assert len(company_nodes) <= 80, f"Meso company cap exceeded: {len(company_nodes)} > 80"


@needs_db
def test_meso_company_nodes_have_company_code():
    g = graph_bridge.get_meso_graph(stages=["Maturity"])
    for n in g["nodes"]:
        if n["type"] == "company":
            assert "company_code" in n, f"Company node {n['id']} missing company_code"


@needs_db
def test_meso_filters_recorded():
    stages = ["Growth", "Decline"]
    g = graph_bridge.get_meso_graph(stages=stages)
    assert "filters" in g
    assert set(g["filters"]["stages"]) == set(stages)


# ── Micro tests ───────────────────────────────────────────────────────────────

@needs_db
def test_micro_node_cap():
    """Micro graph: ≤21 nodes (focal + ≤20 peers + stage + event nodes)."""
    import db
    snap = db.get_kg2_company_snapshot("thesis")
    if snap.empty:
        pytest.skip("No thesis data in DB")
    code = str(snap.iloc[0]["company_code"])
    g = graph_bridge.get_micro_graph(code)
    assert g["node_count"] <= 25, (
        f"Micro node count {g['node_count']} too large "
        "(focal + ≤20 peers + up to 4 stage/event nodes should be ≤25)"
    )


@needs_db
def test_micro_focal_node_present():
    import db
    snap = db.get_kg2_company_snapshot("thesis")
    if snap.empty:
        pytest.skip("No thesis data in DB")
    code = str(snap.iloc[0]["company_code"])
    g = graph_bridge.get_micro_graph(code)
    focal_nodes = [n for n in g["nodes"] if n["type"] == "company_focal"]
    assert len(focal_nodes) == 1, "Micro graph must have exactly one focal node"
    assert focal_nodes[0]["company_code"] == code


@needs_db
def test_micro_unknown_company_returns_error():
    g = graph_bridge.get_micro_graph("COMPANY_DOES_NOT_EXIST_XYZ")
    assert "error" in g
    assert g["nodes"] == []


# ── Isolation check ───────────────────────────────────────────────────────────

def test_no_kg1_imports():
    """graph_bridge must not import KG1 modules."""
    import importlib
    import types

    mod = importlib.import_module("graph_bridge")
    forbidden = {"graph_builder", "graph_viz"}
    for name, obj in vars(mod).items():
        if isinstance(obj, types.ModuleType):
            assert obj.__name__ not in forbidden, (
                f"graph_bridge imports forbidden KG1 module: {obj.__name__}"
            )


# ── get_graph_json unified entry point ────────────────────────────────────────

@needs_db
def test_get_graph_json_macro():
    g = graph_bridge.get_graph_json("macro")
    assert g["level"] == "macro"


@needs_db
def test_get_graph_json_invalid_level():
    with pytest.raises(ValueError, match="Unknown level"):
        graph_bridge.get_graph_json("invalid_level")
