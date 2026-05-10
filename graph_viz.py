"""
Convert networkx knowledge graph to interactive Plotly figure.
Uses spring layout for node positioning and typed styling.
"""

import networkx as nx
import plotly.graph_objects as go
from helpers import plotly_layout

# Node sizes by entity type (pixels)
NODE_SIZE = {
    "company": 14,
    "life_stage": 20,
    "industry": 18,
    "event": 18,
    "observation": 6,
}

# Node symbols by type
NODE_SYMBOL = {
    "company": "circle",
    "life_stage": "diamond",
    "industry": "square",
    "event": "triangle-up",
    "observation": "circle",
}

# Default colors by type (overridden by node's own color attr)
DEFAULT_COLOR = {
    "company": "#0D9488",
    "life_stage": "#22C55E",
    "industry": "#374151",
    "event": "#F97316",
    "observation": "#CBD5E1",
}


def graph_to_plotly_figure(G, title="Knowledge Graph", height=650,
                           highlight_node=None, show_observations=False):
    """
    Render a networkx graph as an interactive Plotly figure.

    Args:
        G: networkx.Graph with typed nodes.
        title: Chart title.
        height: Figure height in pixels.
        highlight_node: Optional node ID to highlight.
        show_observations: If False, filter out observation nodes for cleaner view.

    Returns:
        plotly.graph_objects.Figure
    """
    # Filter observations if requested
    if not show_observations:
        visible_nodes = [n for n, d in G.nodes(data=True)
                         if d.get("type") != "observation"]
        G = G.subgraph(visible_nodes).copy()

    if G.number_of_nodes() == 0:
        fig = go.Figure()
        fig.update_layout(**plotly_layout(title, height))
        fig.add_annotation(text="No nodes to display", showarrow=False,
                           font=dict(size=16, color="#9CA3AF"))
        return fig

    # Compute layout
    pos = nx.spring_layout(G, k=2.0, iterations=50, seed=42)

    # ── Edge traces ──
    edge_x, edge_y = [], []
    for u, v in G.edges():
        x0, y0 = pos[u]
        x1, y1 = pos[v]
        edge_x += [x0, x1, None]
        edge_y += [y0, y1, None]

    edge_trace = go.Scatter(
        x=edge_x, y=edge_y,
        mode="lines",
        line=dict(width=0.8, color="#D1D5DB"),
        hoverinfo="none",
        showlegend=False,
    )

    # ── Node traces (one per type for legend) ──
    node_traces = []
    nodes_by_type = {}
    for node, data in G.nodes(data=True):
        t = data.get("type", "unknown")
        if t not in nodes_by_type:
            nodes_by_type[t] = []
        nodes_by_type[t].append((node, data))

    for node_type, nodes in nodes_by_type.items():
        x_vals, y_vals, texts, hover_texts, colors, sizes = [], [], [], [], [], []

        for node_id, data in nodes:
            x, y = pos[node_id]
            x_vals.append(x)
            y_vals.append(y)
            label = data.get("label", node_id)
            texts.append(label if node_type != "observation" else "")
            colors.append(data.get("color", DEFAULT_COLOR.get(node_type, "#94A3B8")))

            # Hover text
            hover = f"<b>{label}</b><br>Type: {node_type}"
            if data.get("leverage") is not None:
                hover += f"<br>Leverage: {data['leverage']:.3f}"
            if data.get("profitability") is not None:
                hover += f"<br>Profitability: {data['profitability']:.3f}"
            if data.get("year") is not None:
                hover += f"<br>Year: {data['year']}"
            hover_texts.append(hover)

            size = NODE_SIZE.get(node_type, 10)
            if node_id == highlight_node:
                size *= 2
            sizes.append(size)

        trace = go.Scatter(
            x=x_vals, y=y_vals,
            mode="markers+text",
            marker=dict(size=sizes, color=colors,
                        symbol=NODE_SYMBOL.get(node_type, "circle"),
                        line=dict(width=1, color="white")),
            text=texts,
            textposition="top center",
            textfont=dict(size=9, color="#374151"),
            hovertext=hover_texts,
            hoverinfo="text",
            name=node_type.replace("_", " ").title(),
            customdata=[n[0] for n in nodes],
        )
        node_traces.append(trace)

    # ── Assemble figure ──
    fig = go.Figure(data=[edge_trace] + node_traces)
    layout = plotly_layout(title, height)
    layout.update(
        xaxis=dict(showgrid=False, zeroline=False, showticklabels=False, visible=False),
        yaxis=dict(showgrid=False, zeroline=False, showticklabels=False, visible=False),
        hovermode="closest",
        clickmode="event+select",
    )
    fig.update_layout(**layout)
    return fig


def build_drill_down_figure(G, center_node, depth=1, show_observations=False):
    """
    Build a focused subgraph figure centered on a specific node.

    Args:
        G: Full knowledge graph.
        center_node: Node ID to center the view on.
        depth: Hops outward from center.
        show_observations: Include observation-level nodes.

    Returns:
        plotly.graph_objects.Figure
    """
    from graph_builder import get_subgraph
    sub = get_subgraph(G, center_node, depth=depth)
    label = G.nodes[center_node].get("label", center_node)
    return graph_to_plotly_figure(
        sub,
        title=f"Drill-down: {label}",
        highlight_node=center_node,
        show_observations=show_observations,
    )


def build_pyvis_html(G, focal_node=None, height="600px"):
    """
    Convert NetworkX graph to a pyvis self-contained HTML string.
    Render via streamlit.components.v1.html(html_str, height=...).

    Focal node (is_focal=True or matching focal_node param) gets orange border + larger size.
    Node shapes: company=dot, life_stage=diamond, industry=square, event=triangle, stage_norm=ellipse.
    Physics: forceAtlas2Based spring layout.

    Returns HTML string, or error HTML string if pyvis not installed.
    """
    try:
        from pyvis.network import Network
    except ImportError:
        return ("<html><body style='font-family:sans-serif;padding:20px'>"
                "<p><b>pyvis not installed.</b> Run: <code>pip install pyvis&gt;=0.3.2</code></p>"
                "</body></html>")

    _NODE_COLOR = {
        "company": "#0D9488", "life_stage": "#22C55E", "industry": "#374151",
        "event": "#F97316", "stage_norm": "#6366F1",
    }
    _NODE_SIZE = {
        "company": 20, "life_stage": 35, "industry": 25,
        "event": 20, "stage_norm": 30,
    }
    _NODE_SHAPE = {
        "company": "dot", "life_stage": "diamond", "industry": "square",
        "event": "triangle", "stage_norm": "ellipse",
    }
    _EDGE_COLOR = {
        "IS_PEER_OF": "#5EEAD4", "IN_STAGE": "#22C55E", "IN_INDUSTRY": "#374151",
        "HAS_NORM": "#6366F1", "EXPERIENCED_EVENT": "#F97316",
        "IS_SIMILAR": "#94A3B8", "TRANSITIONS": "#22C55E",
    }

    net = Network(height=height, width="100%", notebook=False,
                  directed=False, bgcolor="#ffffff", font_color="#374151")
    net.set_options("""{
      "physics": {
        "forceAtlas2Based": {
          "springLength": 120,
          "gravitationalConstant": -50,
          "springConstant": 0.05,
          "damping": 0.4
        },
        "solver": "forceAtlas2Based",
        "stabilization": {"iterations": 150}
      },
      "interaction": {"hover": true, "tooltipDelay": 100}
    }""")

    for node_id, data in G.nodes(data=True):
        node_type = data.get("node_type", data.get("type", "company"))
        label = data.get("label", str(node_id))
        is_focal = data.get("is_focal", False) or (node_id == focal_node)
        color = data.get("color", _NODE_COLOR.get(node_type, "#9CA3AF"))
        size = _NODE_SIZE.get(node_type, 20)
        shape = _NODE_SHAPE.get(node_type, "dot")

        if is_focal:
            size = 45
            border = "#F97316"
            label = f"★ {label}"
        else:
            border = color

        parts = [f"<b>{data.get('label', node_id)}</b>", f"Type: {node_type}"]
        for k in ("stage", "leverage", "profitability", "p50", "company_count"):
            v = data.get(k)
            if v is not None:
                parts.append(f"{k.replace('_', ' ').title()}: {v:.3f}" if isinstance(v, float) else f"{k.replace('_', ' ').title()}: {v}")
        title = "<br>".join(parts)

        net.add_node(
            node_id, label=label, title=title, shape=shape, size=size,
            color={"background": color, "border": border,
                   "highlight": {"background": "#FEF3C7", "border": "#F97316"}},
            font={"size": 11},
        )

    for u, v, data in G.edges(data=True):
        relation = data.get("relation", "")
        weight = data.get("similarity_score", data.get("probability", 1.0)) or 1.0
        width = max(1.0, min(5.0, float(weight) * 3))
        edge_color = _EDGE_COLOR.get(relation, "#D1D5DB")
        net.add_edge(u, v, color=edge_color, width=width, title=relation)

    return net.generate_html(notebook=False)
