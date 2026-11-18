"""
In-Process Property Graph Engine for Pre-IPO Intelligence
Milestone 11.2 - Phase 2 Hybrid Storage & Traversal Engine

Governed by:
- docs/PRD_FIBO_PRE_IPO_KNOWLEDGE_GRAPH.md
- docs/ARCHITECTURE_SPEC_FIBO_PRE_IPO_KG.md
- ADR-001: Embedded In-Process Property Graph Storage

Engine Architecture:
- Relational Persistence: In-process DuckDB tables (kg_nodes, kg_edges) with ACID atomicity.
- Graph Topology & Pathfinding: NetworkX MultiDiGraph for sub-millisecond multi-hop traversals,
  shortest path discovery, and centrality calculations.
- Frontend Projection: Direct export to @xyflow/react (React Flow) node/edge canvas schema.
"""

from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Dict, Any, List, Optional, Set, Tuple
import json
import logging
import duckdb
import networkx as nx

logger = logging.getLogger("PreIPOPropertyGraphEngine")

DB_DIR = Path(__file__).parent.parent / "data" / "kg"
DB_DIR.mkdir(parents=True, exist_ok=True)
DEFAULT_DB_PATH = DB_DIR / "pre_ipo_kg.duckdb"


@dataclass
class GraphNode:
    id: str
    label: str  # Company, Subsidiary, Promoter, Offering, Litigation, Territory, Contract, Risk
    properties: Dict[str, Any] = field(default_factory=dict)
    # W3C PROV-O metadata
    source_document: Optional[str] = None
    page_number: Optional[int] = None
    bounding_box: Optional[List[float]] = None
    confidence_score: Optional[float] = None
    verbatim_quote: Optional[str] = None


@dataclass
class GraphEdge:
    source_id: str
    target_id: str
    relationship: str  # OWNS, OFFERS_IN, DEFENDANT_IN, OPERATES_IN, PARTY_TO, EXPOSED_TO
    properties: Dict[str, Any] = field(default_factory=dict)
    weight: float = 1.0


class PreIPOPropertyGraphEngine:
    """
    In-process, zero-external-daemon Property Graph Engine.
    Combines DuckDB relational persistence with NetworkX multi-hop graph analytics.
    """

    def __init__(self, db_path: Optional[Path] = None, in_memory: bool = False):
        self.in_memory = in_memory
        self.db_path = str(db_path or DEFAULT_DB_PATH) if not in_memory else ":memory:"
        self.conn = duckdb.connect(self.db_path)
        self.graph = nx.MultiDiGraph()
        self._init_schema()

    def _init_schema(self):
        """Initializes relational tables for nodes and edges."""
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS kg_nodes (
                id VARCHAR PRIMARY KEY,
                label VARCHAR NOT NULL,
                properties JSON,
                source_document VARCHAR,
                page_number INTEGER,
                bounding_box VARCHAR,
                confidence_score DOUBLE,
                verbatim_quote VARCHAR
            );
        """)
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS kg_edges (
                source_id VARCHAR NOT NULL,
                target_id VARCHAR NOT NULL,
                relationship VARCHAR NOT NULL,
                properties JSON,
                weight DOUBLE DEFAULT 1.0,
                PRIMARY KEY (source_id, target_id, relationship)
            );
        """)

    def clear(self):
        """Clears all nodes and edges from memory and database."""
        self.conn.execute("DELETE FROM kg_edges;")
        self.conn.execute("DELETE FROM kg_nodes;")
        self.graph.clear()

    def add_node(self, node: GraphNode):
        """Persists a node to DuckDB and in-memory NetworkX graph."""
        bbox_str = json.dumps(node.bounding_box) if node.bounding_box else None
        props_str = json.dumps(node.properties)

        self.conn.execute("""
            INSERT OR REPLACE INTO kg_nodes (
                id, label, properties, source_document, page_number,
                bounding_box, confidence_score, verbatim_quote
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?);
        """, [
            node.id, node.label, props_str, node.source_document,
            node.page_number, bbox_str, node.confidence_score, node.verbatim_quote
        ])

        self.graph.add_node(
            node.id,
            label=node.label,
            properties=node.properties,
            source_document=node.source_document,
            page_number=node.page_number,
            bounding_box=node.bounding_box,
            confidence_score=node.confidence_score,
            verbatim_quote=node.verbatim_quote
        )

    def add_edge(self, edge: GraphEdge):
        """Persists an edge to DuckDB and in-memory NetworkX graph."""
        props_str = json.dumps(edge.properties)

        self.conn.execute("""
            INSERT OR REPLACE INTO kg_edges (
                source_id, target_id, relationship, properties, weight
            ) VALUES (?, ?, ?, ?, ?);
        """, [
            edge.source_id, edge.target_id, edge.relationship, props_str, edge.weight
        ])

        self.graph.add_edge(
            edge.source_id,
            edge.target_id,
            key=edge.relationship,
            relationship=edge.relationship,
            properties=edge.properties,
            weight=edge.weight
        )

    def get_node(self, node_id: str) -> Optional[GraphNode]:
        """Retrieves a single node by ID."""
        if node_id in self.graph:
            data = self.graph.nodes[node_id]
            return GraphNode(
                id=node_id,
                label=data.get("label", "Unknown"),
                properties=data.get("properties", {}),
                source_document=data.get("source_document"),
                page_number=data.get("page_number"),
                bounding_box=data.get("bounding_box"),
                confidence_score=data.get("confidence_score"),
                verbatim_quote=data.get("verbatim_quote")
            )
        return None

    def get_subgraph(self, start_node_id: str, max_depth: int = 2) -> Dict[str, Any]:
        """
        Extracts an egocentric subgraph up to max_depth hops.
        Returns dictionary formatted for @xyflow/react canvas rendering.
        """
        if start_node_id not in self.graph:
            if "HCCH" in self.graph:
                start_node_id = "HCCH"
            elif len(self.graph.nodes) > 0:
                return self._export_to_canvas(self.graph)
            else:
                return {"nodes": [], "edges": []}

        visited_nodes: Set[str] = {start_node_id}
        current_layer: Set[str] = {start_node_id}

        for _ in range(max_depth):
            next_layer: Set[str] = set()
            for n in current_layer:
                neighbors = set(self.graph.successors(n)) | set(self.graph.predecessors(n))
                next_layer.update(neighbors - visited_nodes)
            visited_nodes.update(next_layer)
            current_layer = next_layer

        sub = self.graph.subgraph(visited_nodes)
        return self._export_to_canvas(sub)

    def find_shortest_path(self, source_id: str, target_id: str) -> Optional[List[str]]:
        """Finds shortest topological path between two entities."""
        try:
            return nx.shortest_path(self.graph.to_undirected(), source=source_id, target=target_id)
        except (nx.NetworkXNoPath, nx.NodeNotFound):
            return None

    def query_multihop(
        self,
        start_label: str,
        rel_chain: List[str]
    ) -> List[List[Dict[str, Any]]]:
        """
        Executes bounded multi-hop relational pathfinding.
        Example: rel_chain = ['OWNS', 'DEFENDANT_IN']
        Traces (a:start_label) -[:OWNS]-> (b) -[:DEFENDANT_IN]-> (c)
        """
        paths: List[List[Dict[str, Any]]] = []

        start_nodes = [
            n for n, d in self.graph.nodes(data=True)
            if d.get("label") == start_label
        ]

        def _dfs(current_node: str, depth: int, current_path: List[Dict[str, Any]]):
            if depth == len(rel_chain):
                paths.append(list(current_path))
                return

            rel_target = rel_chain[depth]
            for _, succ, key, data in self.graph.out_edges(current_node, keys=True, data=True):
                if data.get("relationship") == rel_target or rel_target == "*":
                    succ_data = self.graph.nodes[succ]
                    step = {
                        "from": current_node,
                        "rel": data.get("relationship"),
                        "to": succ,
                        "to_label": succ_data.get("label"),
                        "to_props": succ_data.get("properties")
                    }
                    _dfs(succ, depth + 1, current_path + [step])

        for sn in start_nodes:
            sn_data = self.graph.nodes[sn]
            initial_step = [{"node": sn, "label": sn_data.get("label"), "props": sn_data.get("properties")}]
            _dfs(sn, 0, initial_step)

        return paths

    def _export_to_canvas(self, g: nx.MultiDiGraph) -> Dict[str, Any]:
        """Formats graph into @xyflow/react canvas JSON schema."""
        nodes = []
        for n, d in g.nodes(data=True):
            nodes.append({
                "id": n,
                "type": "financialCardNode",
                "data": {
                    "label": d.get("label"),
                    "name": d.get("properties", {}).get("name", n),
                    "properties": d.get("properties", {}),
                    "pageNumber": d.get("page_number"),
                    "confidence": d.get("confidence_score"),
                    "quote": d.get("verbatim_quote")
                }
            })

        edges = []
        for u, v, k, d in g.edges(keys=True, data=True):
            edges.append({
                "id": f"{u}->{v}:{k}",
                "source": u,
                "target": v,
                "label": d.get("relationship", k),
                "data": d.get("properties", {}),
                "animated": True if "LITIGATION" in str(k) or "RPT" in str(k) else False
            })

        return {"nodes": nodes, "edges": edges}


# Global engine instance
_GLOBAL_KG_ENGINE: Optional[PreIPOPropertyGraphEngine] = None

def get_kg_engine(in_memory: bool = False) -> PreIPOPropertyGraphEngine:
    global _GLOBAL_KG_ENGINE
    if _GLOBAL_KG_ENGINE is None or in_memory:
        _GLOBAL_KG_ENGINE = PreIPOPropertyGraphEngine(in_memory=in_memory)
    return _GLOBAL_KG_ENGINE
