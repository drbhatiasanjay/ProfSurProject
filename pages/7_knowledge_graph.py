"""
Knowledge Graph Explorer — Interactive network visualization.

Answers: How are firms, stages, industries, and events connected?
Shows company → industry, company → life stage, and stage transition edges.
"""

import streamlit as st
import pandas as pd
import db
from graph_builder import (
    build_knowledge_graph, get_graph_stats,
    get_node_details, query_stage_transitions,
)
from graph_viz import graph_to_plotly_figure, build_drill_down_figure
from helpers import (
    STAGE_COLORS, PLOTLY_CONFIG,
    df_download_button, chart_download_button,
)

db.log_page_visit("Knowledge Graph")
st.markdown("### Knowledge Graph")
st.caption("Interactive network of life stages, industries, events, and companies")


# ── Build / cache the graph + source data ──
@st.cache_resource
def _build_graph(db_revision: int):
    _ = db_revision  # cache key only — busts graph when capital_structure.db mtime changes
    fin_df = db.get_graph_financials()
    own_df = db.get_graph_ownership()
    G = build_knowledge_graph(fin_df, own_df)
    return G, fin_df


try:
    with st.spinner("Loading..."):
        G, fin_df = _build_graph(db.db_cache_revision())
except Exception as _e:
    st.error(f"Failed to load graph data. Please refresh. ({_e})")
    st.stop()
stats = get_graph_stats(G)

# ── KPI strip ──
c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("Companies", f"{stats['node_types'].get('company', 0):,}")
c2.metric("Observations", f"{stats['node_types'].get('observation', 0):,}")
c3.metric("Transitions", f"{stats['edge_types'].get('TRANSITION', 0):,}")
avg_trans = stats['edge_types'].get('TRANSITION', 0) / max(stats['node_types'].get('company', 1), 1)
c4.metric("Avg Transitions/Firm", f"{avg_trans:.1f}")
c5.metric("Life Stages", stats["node_types"].get("life_stage", 0))

st.divider()

st.subheader("Knowledge Graph")
st.caption(
    "Nodes: Life Stages (◆), Industries (■), Events (▲), Companies (●). "
    "Edges show: company → industry, company → life stage, stage transitions."
)

# ── View selector ──────────────────────────────────────────────
kcol1, kcol2, kcol3 = st.columns([2, 2, 3])
with kcol1:
    kg_view = st.radio(
        "View",
        ["Stage + Industry overview", "With companies", "Company drill-down"],
        key="kg_view",
        horizontal=False,
    )
with kcol2:
    kg_show_obs = st.checkbox("Show observation nodes", value=False, key="kg_obs",
                               help="Adds 9,000+ year-level nodes — slower render.")

# ── Build filtered subgraph for the selected view ──────────────
if kg_view == "Stage + Industry overview":
    # Build an aggregate graph from fin_df: stage <-> industry edges
    # weighted by number of companies; stage <-> event edges by obs count.
    import networkx as nx
    from collections import defaultdict
    G_agg = nx.Graph()

    # Add stage nodes
    stage_colors = {n: G.nodes[n]["color"] for n in G.nodes if G.nodes[n].get("type") == "life_stage"}
    for n, d in G.nodes(data=True):
        if d.get("type") == "life_stage":
            G_agg.add_node(n, **d)

    # Add top 15 industries by company count
    ind_counts = fin_df.groupby("industry_group")["company_code"].nunique().nlargest(15)
    for ind, cnt in ind_counts.items():
        ind_id = f"industry:{ind}"
        if G.has_node(ind_id):
            node_attrs = dict(G.nodes[ind_id])
            node_attrs["label"] = f"{ind} ({cnt})"
            G_agg.add_node(ind_id, **node_attrs)

    # Add event nodes
    for n, d in G.nodes(data=True):
        if d.get("type") == "event":
            G_agg.add_node(n, **d)

    # Stage <-> Industry edges: # distinct companies in that stage+industry
    si = fin_df.groupby(["life_stage", "industry_group"])["company_code"].nunique().reset_index()
    si.columns = ["life_stage", "industry_group", "n_co"]
    for _, row in si.iterrows():
        s_id = f"stage:{row['life_stage']}"
        i_id = f"industry:{row['industry_group']}"
        if G_agg.has_node(s_id) and G_agg.has_node(i_id) and row["n_co"] >= 3:
            G_agg.add_edge(s_id, i_id, weight=int(row["n_co"]))

    # Stage <-> Event edges: # obs in that stage during event period
    for evt, meta in {"GFC": "gfc", "IBC": "ibc_2016", "COVID": "covid_dummy"}.items():
        evt_id = f"event:{evt}"
        if evt_id not in G_agg:
            continue
        if meta in fin_df.columns:
            se = fin_df[fin_df[meta] == 1].groupby("life_stage").size()
            for stage, cnt in se.items():
                s_id = f"stage:{stage}"
                if G_agg.has_node(s_id) and cnt > 0:
                    G_agg.add_edge(s_id, evt_id, weight=int(cnt))

    fig_kg = graph_to_plotly_figure(
        G_agg,
        title="Stage · Industry (top 15) · Event — aggregate view",
        height=620,
        show_observations=False,
    )
    st.plotly_chart(fig_kg, use_container_width=True, config=PLOTLY_CONFIG)
    chart_download_button(fig_kg, "knowledge_graph_stage_industry.png")
    st.caption("Edge thickness reflects number of companies. Showing top 15 industries by firm count.")

    # Legend / node-type guide
    with st.expander("Node types"):
        st.markdown(
            "| Symbol | Type | Description |\n"
            "|--------|------|-------------|\n"
            "| ◆ | **Life Stage** | Dickinson (2011) classification: Startup, Growth, Maturity, Shakeout1/2/3, Decline, Decay |\n"
            "| ■ | **Industry** | Industry group — top 15 by firm count (NIC classification) |\n"
            "| ▲ | **Event** | Macro event period: GFC (2008–09), IBC (2016+), COVID (2020–21) |"
        )

elif kg_view == "With companies":
    with kcol3:
        stage_filter = st.multiselect(
            "Filter companies by stage",
            options=sorted([d["label"] for n, d in G.nodes(data=True) if d.get("type") == "life_stage"]),
            default=[],
            key="kg_stage_filter",
            placeholder="All stages",
        )
    # Build company subset (limit to 80 for legibility)
    if stage_filter:
        stage_ids = {f"stage:{s}" for s in stage_filter}
        company_nodes = [
            n for n, d in G.nodes(data=True)
            if d.get("type") == "company"
            and any(
                G.has_edge(n, sid) or G.has_edge(sid, n)
                for sid in stage_ids
            )
        ]
    else:
        company_nodes = [n for n, d in G.nodes(data=True) if d.get("type") == "company"]
    # Cap at 80 companies for performance
    company_nodes = company_nodes[:80]
    stage_industry_event = [n for n, d in G.nodes(data=True)
                             if d.get("type") in ("life_stage", "industry", "event")]
    keep = set(company_nodes) | set(stage_industry_event)
    G_view = G.subgraph(keep).copy()
    st.info(f"Showing {len(company_nodes)} companies{' (capped at 80 for legibility)' if len(company_nodes) == 80 else ''}. Use stage filter to narrow down.")
    fig_kg = graph_to_plotly_figure(
        G_view,
        title="Companies + Stage + Industry + Events",
        height=700,
        show_observations=kg_show_obs,
    )
    st.plotly_chart(fig_kg, use_container_width=True, config=PLOTLY_CONFIG)
    chart_download_button(fig_kg, "knowledge_graph_with_companies.png")

else:  # Company drill-down
    # Company picker
    company_options = sorted(
        [(d["label"], n) for n, d in G.nodes(data=True) if d.get("type") == "company"],
        key=lambda x: x[0],
    )
    company_labels = [c[0] for c in company_options]
    company_node_ids = [c[1] for c in company_options]
    with kcol3:
        selected_label = st.selectbox(
            "Select company", company_labels, key="kg_drill_company",
        )
    selected_node = company_node_ids[company_labels.index(selected_label)]

    # Depth control
    drill_depth = st.slider("Hops from company", min_value=1, max_value=3, value=2, key="kg_depth")

    fig_drill = build_drill_down_figure(
        G, selected_node,
        depth=drill_depth,
        show_observations=kg_show_obs,
    )
    st.plotly_chart(fig_drill, use_container_width=True, config=PLOTLY_CONFIG)
    chart_download_button(fig_drill, "knowledge_graph_drilldown.png")

    # Node details panel
    node_data = get_node_details(G, selected_node)
    if node_data:
        st.markdown(f"**{node_data.get('label', selected_node)}**")
        dcol1, dcol2 = st.columns(2)
        dcol1.metric("Type", node_data.get("type", "—").replace("_", " ").title())
        dcol2.metric("Industry", node_data.get("industry", "—"))

        # Life stage transition history for this company
        transitions = query_stage_transitions(G, node_data.get("company_code"))
        if transitions:
            st.markdown("**Stage transition history:**")
            _trans_df = pd.DataFrame(transitions)[["year", "from_stage", "to_stage"]].rename(columns={"year": "Year", "from_stage": "From", "to_stage": "To"})
            st.dataframe(
                _trans_df,
                hide_index=True, use_container_width=True,
            )
            df_download_button(_trans_df, "company_stage_transitions.csv")
