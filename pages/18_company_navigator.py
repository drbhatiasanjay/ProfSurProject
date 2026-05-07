"""
Page 18 — Company Navigator

Interactive graph explorer: select any company, explore its position in the
capital structure landscape. Three zoom levels:
  Stage Map    (L1) — 8 life-stage hubs + transition probabilities
  Peer Cluster (L2) — all same-stage firms, force-directed by leverage proximity
  Ego Graph    (L3) — focal company centred; peers + stage + industry + norm band

Company is the SUBJECT (not a data point). The full thesis panel is peer context.
Different from page 7 (Life Stage Dynamics) which is panel-wide statistical analytics.
"""

import streamlit as st
import streamlit.components.v1 as components
import pandas as pd

import db
from helpers import (
    ensure_session_state, require_role, plotly_layout,
    PLOTLY_CONFIG, STAGE_COLORS, STAGE_ORDER, new_badge,
)
from graph_builder import (
    build_knowledge_graph,
    build_cfo_ego_graph,
    build_peer_cluster_graph,
    build_stage_map_graph,
    get_cfo_node_panel,
)
from graph_viz import build_pyvis_html, graph_to_plotly_figure

ensure_session_state()
db.log_page_visit("Company Navigator")
require_role("admin", "researcher")

# ── Page header ───────────────────────────────────────────────────────────────
st.markdown(f"### Company Navigator {new_badge()}", unsafe_allow_html=True)
st.caption(
    "Explore any company's position in the capital structure landscape. "
    "Zoom from Stage Map → Peer Cluster → Ego Graph. "
    "All analysis uses the Thesis panel (2001–2024)."
)

# ── Load static data (cached) ─────────────────────────────────────────────────
@st.cache_data(ttl=3600)
def _load_full_panel():
    ft = db.filters_to_tuple({
        "panel_mode": "thesis",
        "company_codes": [],
        "year_range": (2001, 2024),
        "life_stages": [],
        "industry_groups": [],
        "events": {"gfc": False, "ibc": False, "covid": False},
    })
    return db.get_active_financials(ft)


@st.cache_data(ttl=3600)
def _load_stage_summary():
    ft = db.filters_to_tuple({
        "panel_mode": "thesis",
        "company_codes": [],
        "year_range": (2001, 2024),
        "life_stages": [],
        "industry_groups": [],
        "events": {"gfc": False, "ibc": False, "covid": False},
    })
    return db.get_life_stage_summary(ft)


@st.cache_data(ttl=3600)
def _load_G_full():
    fin = db.get_graph_financials()
    own = db.get_graph_ownership()
    return build_knowledge_graph(fin, own)


@st.cache_data(ttl=3600)
def _load_companies():
    df = db.get_companies("thesis")
    india_df = df[~df["company_name"].str.contains(r"Inc\.|Corp\.|Co\.", regex=True, na=False)]
    us_df    = df[ df["company_name"].str.contains(r"Inc\.|Corp\.|Co\.", regex=True, na=False)]
    return pd.concat([india_df, us_df], ignore_index=True)


try:
    with st.spinner("Loading..."):
        full_panel    = _load_full_panel()
        stage_summary = _load_stage_summary()
        G_full        = _load_G_full()
        companies_df  = _load_companies()
except Exception as _e:
    st.error(f"Failed to load data. Please refresh. ({_e})")
    st.stop()
ordered_names = companies_df["company_name"].tolist()

# ── Controls row ──────────────────────────────────────────────────────────────
_username   = st.session_state.get("user", {}).get("username", "")
_nav_prefs  = db.load_user_prefs(_username, "company_navigator") if _username else {}
_saved_name = _nav_prefs.get("selected_company", ordered_names[0] if ordered_names else "")
_default_idx = ordered_names.index(_saved_name) if _saved_name in ordered_names else 0

col_co, col_view = st.columns([2, 2])
with col_co:
    selected_name = st.selectbox(
        "Company",
        options=ordered_names,
        index=_default_idx,
        help="401 Indian firms + 25 US comparators.",
        key="nav_company",
    )
with col_view:
    view_mode = st.radio(
        "View",
        options=["Ego Graph", "Peer Cluster", "Stage Map"],
        horizontal=True,
        index=["Ego Graph", "Peer Cluster", "Stage Map"].index(
            st.session_state.get("navigator_view", "Ego Graph")
        ),
        key="nav_view",
    )

# Persist prefs
if _username:
    db.save_user_pref(_username, "company_navigator", {"selected_company": selected_name})

# Sync view mode from session (used when Stage Map click drills into Peer Cluster)
if "navigator_view" in st.session_state and st.session_state["navigator_view"] != view_mode:
    view_mode = st.session_state["navigator_view"]
st.session_state["navigator_view"] = view_mode

# Resolve company
company_row  = companies_df[companies_df["company_name"] == selected_name].iloc[0]
company_code = int(company_row["company_code"])

# Year slider (hidden for Stage Map)
if view_mode != "Stage Map":
    years_available = sorted(full_panel["year"].unique().tolist()) if "year" in full_panel.columns else list(range(2001, 2025))
    selected_year = st.slider(
        "Year",
        min_value=int(years_available[0]),
        max_value=int(years_available[-1]),
        value=int(years_available[-1]),
        key="nav_year",
    )
else:
    selected_year = None

st.divider()

# ── Build the selected graph ──────────────────────────────────────────────────
@st.cache_data(ttl=600)
def _build_ego(company_code, selected_year, _full_panel, _stage_summary, _G_full):
    company_df = db.get_company_detail(company_code)
    if selected_year is not None and "year" in company_df.columns:
        company_df = company_df[company_df["year"] <= selected_year]
    peers_df = db.get_company_peers(company_code, _full_panel)
    return build_cfo_ego_graph(_G_full, company_code, peers_df, company_df, _stage_summary), company_df


@st.cache_data(ttl=600)
def _build_peer_cluster(company_code, _full_panel, _G_full):
    company_df = db.get_company_detail(company_code)
    latest_stage = None
    if not company_df.empty and "life_stage" in company_df.columns:
        latest_stage = company_df.sort_values("year").iloc[-1].get("life_stage")
    if not latest_stage:
        return None, None
    G = build_peer_cluster_graph(_G_full, latest_stage, _full_panel, focal_code=company_code)
    return G, latest_stage


@st.cache_data(ttl=600)
def _build_stage_map(_full_panel, _G_full):
    return build_stage_map_graph(_G_full, _full_panel)


# ── Layout: graph left, detail panel right ────────────────────────────────────
col_graph, col_panel = st.columns([3, 1])

detail_node_id = None
G_active = None

with col_graph:
    if view_mode == "Ego Graph":
        G_ego, company_df = _build_ego(company_code, selected_year, full_panel, stage_summary, G_full)
        G_active = G_ego
        html = build_pyvis_html(G_ego, focal_node=f"company:{company_code}", height="560px")
        components.html(html, height=580, scrolling=False)

        company_nodes = sorted([
            (d.get("label", n), n)
            for n, d in G_ego.nodes(data=True)
            if d.get("node_type") == "company"
        ])
        node_labels = [label for label, _ in company_nodes]
        node_ids    = [nid   for _, nid  in company_nodes]
        focal_label = G_ego.nodes.get(f"company:{company_code}", {}).get("label", selected_name)
        default_sel = focal_label if focal_label in node_labels else (node_labels[0] if node_labels else None)
        default_idx = node_labels.index(default_sel) if default_sel in node_labels else 0

        sel_label = st.selectbox(
            "Select node to inspect",
            options=node_labels,
            index=default_idx,
            key="ego_node_select",
            help="Use this to open the detail panel for any visible company node.",
        )
        if sel_label and sel_label in node_labels:
            detail_node_id = node_ids[node_labels.index(sel_label)]

    elif view_mode == "Peer Cluster":
        G_cluster, cluster_stage = _build_peer_cluster(company_code, full_panel, G_full)
        if G_cluster is None or G_cluster.number_of_nodes() == 0:
            st.info("No peer cluster data available for this company's current stage.")
        else:
            G_active = G_cluster
            html = build_pyvis_html(G_cluster, focal_node=f"company:{company_code}", height="560px")
            components.html(html, height=580, scrolling=False)
            st.caption(f"Stage: **{cluster_stage}** · {G_cluster.number_of_nodes()} firms · colour = leverage quartile (green=low, red=high)")

            cluster_nodes = sorted([
                (d.get("label", n), n)
                for n, d in G_cluster.nodes(data=True)
            ])
            cl_labels = [l for l, _ in cluster_nodes]
            cl_ids    = [i for _, i in cluster_nodes]
            focal_label = G_cluster.nodes.get(f"company:{company_code}", {}).get("label", selected_name)
            def_idx = cl_labels.index(focal_label) if focal_label in cl_labels else 0
            sel_cl = st.selectbox(
                "Select node to inspect",
                options=cl_labels,
                index=def_idx,
                key="cluster_node_select",
            )
            if sel_cl and sel_cl in cl_labels:
                detail_node_id = cl_ids[cl_labels.index(sel_cl)]

    elif view_mode == "Stage Map":
        G_stage = _build_stage_map(full_panel, G_full)
        G_active = G_stage
        fig = graph_to_plotly_figure(G_stage, title="Life Stage Transition Map", height=560)

        try:
            from streamlit_plotly_events import plotly_events
            clicked = plotly_events(fig, click_event=True, key="stage_map_click")
            if clicked:
                raw_node = clicked[0].get("text") or clicked[0].get("customdata")
                if raw_node:
                    stage_label = str(raw_node).strip()
                    node_candidate = f"stage:{stage_label}"
                    if node_candidate not in G_stage.nodes:
                        for nid, nd in G_stage.nodes(data=True):
                            if nd.get("label") == stage_label:
                                node_candidate = nid
                                break
                    detail_node_id = node_candidate if node_candidate in G_stage.nodes else None
                    if detail_node_id:
                        st.session_state["navigator_drill_stage"] = stage_label
        except ImportError:
            st.plotly_chart(fig, config=PLOTLY_CONFIG, use_container_width=True)
            st.caption("Install streamlit-plotly-events for click-to-drill navigation.")

        stage_options = [nd.get("label", n) for n, nd in G_stage.nodes(data=True) if nd.get("node_type") == "life_stage"]
        sel_stage = st.selectbox(
            "Select stage to inspect",
            options=sorted(stage_options, key=lambda s: STAGE_ORDER.index(s) if s in STAGE_ORDER else 99),
            key="stage_map_select",
        )
        if sel_stage:
            detail_node_id = f"stage:{sel_stage}"

        drill_stage = st.session_state.get("navigator_drill_stage")
        if drill_stage:
            if st.button(f"Drill into Peer Cluster → {drill_stage}", type="secondary"):
                st.session_state["navigator_view"] = "Peer Cluster"
                del st.session_state["navigator_drill_stage"]
                st.rerun()

# ── Legend ────────────────────────────────────────────────────────────────────
with col_graph:
    st.markdown(
        "<small>Legend: "
        "<span style='color:#0D9488'>●</span> Company &nbsp;"
        "<span style='color:#22C55E'>◆</span> Life Stage &nbsp;"
        "<span style='color:#374151'>■</span> Industry &nbsp;"
        "<span style='color:#F97316'>▲</span> Event &nbsp;"
        "<span style='color:#6366F1'>○</span> Stage Norm</small>",
        unsafe_allow_html=True,
    )

# ── Detail panel ──────────────────────────────────────────────────────────────
with col_panel:
    st.markdown("**Node Detail**")
    if detail_node_id and G_active is not None:
        panel_data = get_cfo_node_panel(G_active, detail_node_id, full_panel)
        node_type  = panel_data.get("node_type", "")
        label      = panel_data.get("label", detail_node_id)

        st.markdown(f"**{label}**")

        if node_type == "company":
            stage = panel_data.get("stage", "—")
            stage_color = STAGE_COLORS.get(stage, "#9CA3AF")
            st.markdown(
                f"<span style='background:{stage_color};color:white;padding:2px 8px;"
                f"border-radius:4px;font-size:12px'>{stage}</span>",
                unsafe_allow_html=True,
            )
            st.write("")
            lev  = panel_data.get("leverage")
            prof = panel_data.get("profitability")
            lev_pct  = panel_data.get("leverage_pct")
            prof_pct = panel_data.get("profitability_pct")
            if lev is not None:
                pct_str = f" ({lev_pct:.0f}th pct)" if lev_pct is not None else ""
                st.metric("Leverage", f"{lev:.3f}{pct_str}")
            if prof is not None:
                pct_str = f" ({prof_pct:.0f}th pct)" if prof_pct is not None else ""
                st.metric("Profitability", f"{prof:.3f}{pct_str}")

            st.write("")
            detail_code = panel_data.get("company_code")
            if detail_code:
                detail_peers = db.get_company_peers(detail_code, full_panel, n=5)
                if not detail_peers.empty and "leverage" in detail_peers.columns:
                    import plotly.graph_objects as go
                    peer_levs = pd.to_numeric(detail_peers["leverage"], errors="coerce").dropna()
                    peer_names = detail_peers["company_name"].tolist()[:len(peer_levs)]
                    fig_mini = go.Figure(go.Bar(
                        x=peer_names,
                        y=peer_levs.tolist(),
                        marker_color="#5EEAD4",
                    ))
                    if lev is not None:
                        fig_mini.add_hline(y=lev, line_dash="dash", line_color="#0D9488",
                                           annotation_text="Selected")
                    layout = plotly_layout("Peer Leverage", 180)
                    layout.update(showlegend=False, margin=dict(l=0, r=0, t=25, b=40))
                    fig_mini.update_layout(**layout)
                    st.plotly_chart(fig_mini, config=PLOTLY_CONFIG, use_container_width=True)

            st.write("")
            if detail_code and _username:
                db.save_user_pref(_username, "board_deck", {"selected_company": label})
            if st.button("View Full Analysis →", type="primary", key="goto_board"):
                if detail_code and _username:
                    db.save_user_pref(_username, "board_deck", {"selected_company": label})
                st.switch_page("pages/17_board_export.py")

        elif node_type == "life_stage":
            st.write(f"**Stage norm band** (leverage)")
            p25 = panel_data.get("p25")
            p50 = panel_data.get("p50")
            p75 = panel_data.get("p75")
            cnt = panel_data.get("company_count", 0)
            if p25 is not None:
                st.write(f"p25: {p25:.3f}")
            if p50 is not None:
                st.write(f"p50 (median): {p50:.3f}")
            if p75 is not None:
                st.write(f"p75: {p75:.3f}")
            st.write(f"Firms in stage: {cnt}")

        elif node_type == "industry":
            cnt     = panel_data.get("company_count", 0)
            avg_lev = panel_data.get("avg_leverage")
            st.write(f"Firms: {cnt}")
            if avg_lev is not None:
                st.metric("Avg leverage", f"{avg_lev:.3f}")

        elif node_type in ("event", "stage_norm"):
            for k, v in panel_data.items():
                if k not in ("node_id", "node_type", "label") and v is not None:
                    st.write(f"**{k.replace('_', ' ').title()}:** {v}")
    else:
        st.info("Select a node below the graph to see details here.")
