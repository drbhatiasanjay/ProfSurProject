"""
KG2 — Knowledge Graph 2 (page 21)

Semantic lifecycle graph backed by graph_bridge.py (Phase 0: Python stub;
Phase 5: OCaml HTTP service).  Three zoom levels: Macro → Meso → Micro.

ISOLATION: never imports from graph_builder, pages/7_knowledge_graph,
           or pages/18_company_navigator. Reads from graph_bridge only.
"""

import streamlit as st

try:
    from streamlit_agraph import agraph, Node, Edge, Config
    _HAS_AGRAPH = True
except ImportError:
    _HAS_AGRAPH = False

import graph_bridge
import db

# ── Page header ───────────────────────────────────────────────────────────────

st.markdown("## Knowledge Graph 2")
st.caption(
    "Semantic lifecycle graph — OCaml ontology layer (Phase 0: Python stub). "
    "Three zoom levels: Macro (system-wide) → Meso (stage/industry filter) → Micro (company ego)."
)

if not _HAS_AGRAPH:
    st.error(
        "**`streamlit-agraph` not installed.** "
        "Run `pip install streamlit-agraph` and restart the app."
    )
    st.stop()

# ── Sidebar controls ──────────────────────────────────────────────────────────

panel_mode = st.session_state.get("panel_mode", "latest")

with st.sidebar:
    st.markdown("---")
    st.markdown("### KG2 Controls")

    persona = st.selectbox(
        "Persona",
        options=graph_bridge.VALID_PERSONAS,
        index=graph_bridge.VALID_PERSONAS.index("CorporateCFO"),
        help="Changes default stage focus and tooltip emphasis",
        key="kg2_persona",
    )

    level = st.radio(
        "Zoom level",
        options=["Macro", "Meso", "Micro"],
        index=0,
        key="kg2_level",
        help="Macro ≤21 nodes · Meso ≤80 companies · Micro: ego graph",
    )

    # Meso-specific filters
    meso_stages:     list = []
    meso_industries: list = []
    if level == "Meso":
        meso_stages = st.multiselect(
            "Stages",
            options=graph_bridge.ALL_STAGES,
            default=graph_bridge.PERSONA_STAGE_DEFAULTS.get(persona, graph_bridge.ALL_STAGES[:3]),
            key="kg2_meso_stages",
        )
        all_inds = db.get_industry_groups(panel_mode)
        meso_industries = st.multiselect(
            "Industries",
            options=all_inds,
            default=[],
            placeholder="All industries",
            key="kg2_meso_industries",
        )

    # Micro-specific: company picker
    micro_code: str = ""
    micro_name: str = ""
    if level == "Micro":
        companies_df = db.get_companies(panel_mode)
        company_names = companies_df["company_name"].sort_values().tolist()
        selected_name = st.selectbox(
            "Company",
            options=company_names,
            key="kg2_micro_company",
            help="Focal company for the ego graph",
        )
        match = companies_df[companies_df["company_name"] == selected_name]
        if not match.empty:
            micro_code = str(match.iloc[0]["company_code"])
            micro_name = selected_name

# ── Graph config ──────────────────────────────────────────────────────────────

_graph_config = Config(
    width="100%",
    height=580,
    directed=True,
    physics=True,
    hierarchical=False,
    nodeHighlightBehavior=True,
    highlightColor="#F7A7A6",
    collapsible=False,
    node={"labelProperty": "label"},
    link={"labelProperty": "label", "renderLabel": False},
)

# ── Build and render the graph ────────────────────────────────────────────────

@st.cache_data(ttl=300, show_spinner=False)
def _cached_macro(panel_mode: str, persona: str) -> dict:
    return graph_bridge.get_macro_graph(panel_mode, persona)


@st.cache_data(ttl=300, show_spinner=False)
def _cached_meso(
    stages_key:     tuple,
    industries_key: tuple,
    panel_mode:     str,
    persona:        str,
) -> dict:
    return graph_bridge.get_meso_graph(
        list(stages_key), list(industries_key), panel_mode, persona
    )


@st.cache_data(ttl=300, show_spinner=False)
def _cached_micro(company_code: str, panel_mode: str, persona: str) -> dict:
    return graph_bridge.get_micro_graph(company_code, panel_mode, persona)


def _to_agraph(graph_data: dict):
    """Convert graph_bridge JSON → (nodes, edges) for streamlit-agraph."""
    nodes, edges = [], []

    for n in graph_data.get("nodes", []):
        nodes.append(Node(
            id=n["id"],
            label=n.get("label", n["id"]),
            size=n.get("size", 12),
            color=n.get("color", "#9CA3AF"),
            title=n.get("tooltip", ""),
        ))

    for e in graph_data.get("edges", []):
        edges.append(Edge(
            source=e["from"],
            target=e["to"],
            label=e.get("label", ""),
        ))

    return nodes, edges


col_graph, col_detail = st.columns([3, 1])

with col_graph:
    with st.spinner("Building graph…"):
        if level == "Macro":
            gdata = _cached_macro(panel_mode, persona)

        elif level == "Meso":
            if not meso_stages:
                meso_stages = graph_bridge.PERSONA_STAGE_DEFAULTS.get(persona, graph_bridge.ALL_STAGES)
            gdata = _cached_meso(
                tuple(meso_stages), tuple(meso_industries), panel_mode, persona
            )

        else:  # Micro
            if not micro_code:
                st.info("Select a company from the sidebar to view its ego graph.")
                st.stop()
            gdata = _cached_micro(micro_code, panel_mode, persona)

    if "error" in gdata:
        st.warning(gdata["error"])
        st.stop()

    nodes_ag, edges_ag = _to_agraph(gdata)
    node_count = gdata.get("node_count", len(nodes_ag))

    st.caption(
        f"**{level} view** · {node_count} nodes · {len(edges_ag)} edges · "
        f"Persona: {persona} · Panel: {panel_mode}"
    )

    selected = agraph(nodes=nodes_ag, edges=edges_ag, config=_graph_config)

# ── Detail / Explain This panel ───────────────────────────────────────────────

with col_detail:
    st.markdown("#### Detail")

    if selected:
        st.session_state["kg2_selected"] = selected

    clicked = st.session_state.get("kg2_selected")

    if clicked:
        # Identify what was clicked
        clicked_node = next(
            (n for n in gdata.get("nodes", []) if n["id"] == clicked), None
        )
        if clicked_node:
            ntype = clicked_node.get("type", "")
            st.markdown(f"**{clicked_node.get('label', clicked)}**")
            st.caption(f"Type: `{ntype}`")

            if clicked_node.get("tooltip"):
                st.markdown(clicked_node["tooltip"], unsafe_allow_html=True)

            if ntype in ("company", "company_focal", "company_peer"):
                code = clicked_node.get("company_code", "")
                if code and level != "Micro":
                    if st.button("Zoom to Micro →", key="kg2_zoom_micro"):
                        st.session_state["kg2_level"]         = "Micro"
                        st.session_state["kg2_micro_company"] = clicked_node.get("label", "")
                        st.rerun()

            st.divider()
            st.markdown("**Explain This** _(Phase 3+)_")
            st.caption(
                "When the OCaml analytics meta-layer is live, this panel will show "
                "the provenance chain: model → model_run → statistic → normative band."
            )
        else:
            st.info(f"Selected: `{clicked}`")
    else:
        st.info("Click any node to see details and provenance.")

    st.divider()

    # Node-type legend
    st.markdown("**Legend**")
    st.markdown(
        "🟢 Startup &nbsp; 🔵 Growth &nbsp; 🟣 Maturity  \n"
        "🟡 Shakeout1 &nbsp; 🔴 Shakeout2/3  \n"
        "⚫ Decline/Decay  \n"
        "🔵 Industry &nbsp; 🔴 Event  \n"
        "🟣 Company &nbsp; 🟠 Focal firm"
    )

# ── KG2 stats bar ─────────────────────────────────────────────────────────────

with st.expander("Graph stats", expanded=False):
    node_types: dict[str, int] = {}
    for n in gdata.get("nodes", []):
        nt = n.get("type", "unknown")
        node_types[nt] = node_types.get(nt, 0) + 1

    cols = st.columns(len(node_types) + 1)
    cols[0].metric("Total nodes", node_count)
    for i, (ntype, cnt) in enumerate(node_types.items(), start=1):
        cols[i].metric(ntype.replace("_", " ").title(), cnt)

    st.caption(
        "KG2 enforces hard node caps: Macro ≤21 · Meso ≤80 companies · "
        "Micro ≤21 (focal + 20 peers). This avoids the KG1 'hairball' (9,450 nodes)."
    )
