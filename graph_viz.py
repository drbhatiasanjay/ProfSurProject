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
