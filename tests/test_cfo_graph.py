"""
Tests for CFO-facing graph builder functions.

Data-layer only — no browser, no Streamlit, no PPTX.
Validates graph structure contracts for Company Navigator (page 18).
"""

import pytest
import pandas as pd
import networkx as nx
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import db
from graph_builder import (
    build_knowledge_graph,
    build_cfo_ego_graph,
    build_peer_cluster_graph,
    build_stage_map_graph,
    get_cfo_node_panel,
)
from graph_viz import build_pyvis_html

# ── Fixtures ──────────────────────────────────────────────────────────────────

ASIAN_PAINTS_CODE = 22859   # Maturity-stage firm, same as test_board_export


@pytest.fixture(scope="module")
def full_panel():
    ft = db.filters_to_tuple({
        "panel_mode": "thesis",
        "company_codes": [],
        "year_range": (2001, 2024),
        "life_stages": [],
        "industry_groups": [],
        "events": {"gfc": False, "ibc": False, "covid": False},
    })
    return db.get_active_financials(ft)


@pytest.fixture(scope="module")
def company_df():
    return db.get_company_detail(ASIAN_PAINTS_CODE)


@pytest.fixture(scope="module")
def stage_summary(full_panel):
    ft = db.filters_to_tuple({
        "panel_mode": "thesis",
        "company_codes": [],
        "year_range": (2001, 2024),
        "life_stages": [],
        "industry_groups": [],
        "events": {"gfc": False, "ibc": False, "covid": False},
    })
    return db.get_life_stage_summary(ft)


@pytest.fixture(scope="module")
def peers_df(full_panel):
    return db.get_company_peers(ASIAN_PAINTS_CODE, full_panel)


@pytest.fixture(scope="module")
def G_full():
    fin = db.get_graph_financials()
    own = db.get_graph_ownership()
    return build_knowledge_graph(fin, own)


@pytest.fixture(scope="module")
def G_ego(G_full, company_df, peers_df, stage_summary, full_panel):
    return build_cfo_ego_graph(
        G_full, ASIAN_PAINTS_CODE, peers_df, company_df, stage_summary
    )


# ── TestBuildCfoEgoGraph ──────────────────────────────────────────────────────

class TestBuildCfoEgoGraph:
    def test_returns_simple_graph(self, G_ego):
        assert isinstance(G_ego, nx.Graph)
        assert not isinstance(G_ego, nx.MultiGraph)

    def test_focal_node_present(self, G_ego):
        assert f"company:{ASIAN_PAINTS_CODE}" in G_ego.nodes

    def test_focal_node_is_focal(self, G_ego):
        data = G_ego.nodes[f"company:{ASIAN_PAINTS_CODE}"]
        assert data.get("is_focal") is True

    def test_peer_nodes_present(self, G_ego):
        focal_id = f"company:{ASIAN_PAINTS_CODE}"
        peer_edges = [
            (u, v) for u, v, d in G_ego.edges(data=True)
            if d.get("relation") == "IS_PEER_OF" and (u == focal_id or v == focal_id)
        ]
        assert len(peer_edges) >= 1

    def test_has_stage_norm_node(self, G_ego):
        norm_nodes = [n for n, d in G_ego.nodes(data=True) if d.get("node_type") == "stage_norm"]
        assert len(norm_nodes) >= 1

    def test_empty_peers_no_crash(self, G_full, company_df, stage_summary):
        empty_peers = pd.DataFrame()
        G = build_cfo_ego_graph(G_full, ASIAN_PAINTS_CODE, empty_peers, company_df, stage_summary)
        assert isinstance(G, nx.Graph)
        assert f"company:{ASIAN_PAINTS_CODE}" in G.nodes


# ── TestBuildPeerClusterGraph ─────────────────────────────────────────────────

class TestBuildPeerClusterGraph:
    def test_returns_graph(self, G_full, full_panel):
        G = build_peer_cluster_graph(G_full, "Maturity", full_panel)
        assert isinstance(G, nx.Graph)

    def test_all_nodes_are_companies(self, G_full, full_panel):
        G = build_peer_cluster_graph(G_full, "Maturity", full_panel)
        non_company = [n for n, d in G.nodes(data=True) if d.get("node_type") != "company"]
        assert len(non_company) == 0

    def test_focal_highlighted(self, G_full, full_panel):
        G = build_peer_cluster_graph(G_full, "Maturity", full_panel, focal_code=ASIAN_PAINTS_CODE)
        focal_id = f"company:{ASIAN_PAINTS_CODE}"
        if focal_id in G.nodes:
            assert G.nodes[focal_id].get("is_focal") is True


# ── TestBuildStageMapGraph ────────────────────────────────────────────────────

class TestBuildStageMapGraph:
    def test_returns_graph(self, G_full, full_panel):
        G = build_stage_map_graph(G_full, full_panel)
        assert isinstance(G, nx.Graph)

    def test_has_8_stage_nodes(self, G_full, full_panel):
        G = build_stage_map_graph(G_full, full_panel)
        stage_nodes = [n for n, d in G.nodes(data=True) if d.get("node_type") == "life_stage"]
        assert len(stage_nodes) == 8

    def test_transition_edges_have_probability(self, G_full, full_panel):
        G = build_stage_map_graph(G_full, full_panel)
        trans_edges = [(u, v, d) for u, v, d in G.edges(data=True) if d.get("relation") == "TRANSITIONS"]
        assert len(trans_edges) >= 1
        for _, _, d in trans_edges:
            prob = d.get("probability")
            assert prob is not None
            assert 0.0 <= prob <= 1.0


# ── TestGetCfoNodePanel ───────────────────────────────────────────────────────

class TestGetCfoNodePanel:
    def test_company_node_returns_metrics(self, G_ego, full_panel):
        focal_id = f"company:{ASIAN_PAINTS_CODE}"
        result = get_cfo_node_panel(G_ego, focal_id, full_panel)
        assert "leverage" in result
        assert "stage" in result

    def test_stage_node_returns_norm_band(self, G_full, full_panel, G_ego):
        stage_nodes = [n for n, d in G_ego.nodes(data=True) if d.get("node_type") == "life_stage"]
        assert len(stage_nodes) >= 1
        result = get_cfo_node_panel(G_ego, stage_nodes[0], full_panel)
        assert "p25" in result or "p50" in result or "p75" in result

    def test_unknown_node_returns_empty_dict(self, G_ego, full_panel):
        result = get_cfo_node_panel(G_ego, "nonexistent:99999", full_panel)
        assert result == {}


# ── TestBuildPyvisHtml ────────────────────────────────────────────────────────

class TestBuildPyvisHtml:
    def test_returns_html_string(self, G_ego):
        html = build_pyvis_html(G_ego)
        assert isinstance(html, str)
        assert len(html) > 100

    def test_focal_node_styled(self, G_ego):
        focal_id = f"company:{ASIAN_PAINTS_CODE}"
        html = build_pyvis_html(G_ego, focal_node=focal_id)
        assert isinstance(html, str)
        assert "F97316" in html
