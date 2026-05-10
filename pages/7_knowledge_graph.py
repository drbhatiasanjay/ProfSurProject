"""
Knowledge Graph Explorer — Stage Transition Dynamics.

Answers: How do firms move between life stages? What triggers those moves?
How do macro events reshape transition patterns?

Tab 0: Knowledge Graph (interactive network view — stages, industries, events, companies)
Tab 1: Transition Probability Matrix + Stage Metrics Matrix
Tab 2: Event Impact Matrices (Leverage, Transition Rate, Deterioration)
Tab 3: Stage Pathway Discovery
Tab 4: Multi-Hop Company Profiler
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from collections import Counter
import operator
from scipy import stats as _scipy_stats
import db
from graph_builder import (
    build_knowledge_graph, get_graph_stats,
    get_node_details, get_subgraph,
    compute_transition_matrix, compute_stickiness,
    find_event_triggered_transitions,
    compute_event_impact_matrix, compute_stage_metric_matrix,
    compute_covid_cohorts,
    extract_transition_sequences, find_paths_to_stage,
    query_stage_transitions, _get_obs_stage,
)
from graph_viz import graph_to_plotly_figure, build_drill_down_figure
from helpers import (
    STAGE_COLORS, STAGE_ORDER, STAGE_RANK, plotly_layout, event_bands,
    PRIMARY, SECONDARY, ACCENT, PLOTLY_CONFIG,
    df_download_button, chart_download_button,
)

db.log_page_visit("Knowledge Graph")
st.markdown("### Life Stage Dynamics")
st.caption("How firms move between life stages, what triggers transitions, and how events reshape patterns")


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


# ── Helpers ──
def _make_heatmap(df, title, show_counts, height=450, colorscale="Teal"):
    text = [[f"{v:.0f}" if show_counts else f"{v:.1%}" for v in row] for row in df.values]
    fig = px.imshow(
        df.values, x=list(df.columns), y=list(df.index),
        color_continuous_scale=colorscale, aspect="auto",
        labels=dict(x="To Stage", y="From Stage", color="Count" if show_counts else "Probability"),
    )
    fig.update_traces(text=text, texttemplate="%{text}", textfont_size=10)
    hm_layout = plotly_layout(title, height)
    hm_layout["margin"] = dict(l=120, r=20, t=40, b=80)
    fig.update_layout(**hm_layout)
    return fig


def _make_matrix_figure(df, title, fmt=".1f", colorscale="Teal", height=400, zmin=None, zmax=None):
    """Generic annotated heatmap for any matrix."""
    vals = df.values.astype(float)
    text = [[f"{v:{fmt}}" if not np.isnan(v) else "" for v in row] for row in vals]
    kwargs = dict(color_continuous_scale=colorscale, aspect="auto")
    if zmin is not None:
        kwargs["zmin"] = zmin
    if zmax is not None:
        kwargs["zmax"] = zmax
    fig = px.imshow(vals, x=list(df.columns), y=list(df.index), **kwargs)
    fig.update_traces(text=text, texttemplate="%{text}", textfont_size=10)
    ml = plotly_layout(title, height)
    ml["margin"] = dict(l=140, r=20, t=50, b=80)
    fig.update_layout(**ml)
    return fig


# ── Tabs ──
tab_graph, tab_markov, tab_events, tab_paths, tab_covid, tab_profiler = st.tabs([
    "Knowledge Graph",
    "Transition Probabilities",
    "Event Impact Matrices",
    "Stage Pathways",
    "COVID Cohorts",
    "Company Profiler",
])


# ══════════════════════════════════════════════
# TAB 0: Knowledge Graph — interactive network
# ══════════════════════════════════════════════
with tab_graph:
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
                G_agg.add_node(ind_id, **G.nodes[ind_id], label=f"{ind} ({cnt})")

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

# ══════════════════════════════════════════════
# TAB 1: Transition Probability Matrix + Metrics
# ══════════════════════════════════════════════
with tab_markov:
    st.subheader("Stage Transition Probability Matrix")
    st.caption("If a firm is in stage X this year, what's the probability it moves to stage Y next year? Diagonal = stayed in same stage.")

    col_ctrl1, col_ctrl2 = st.columns([1, 1])
    with col_ctrl1:
        event_compare = st.selectbox(
            "Compare with event", ["None", "GFC", "IBC", "COVID"],
            key="markov_event",
        )
    with col_ctrl2:
        yr_min, yr_max = int(fin_df["year"].min()), int(fin_df["year"].max())
        yr_range = st.slider("Year range", yr_min, yr_max, (yr_min, yr_max), key="markov_yr")

    show_counts = st.toggle("Show counts instead of probabilities", value=False, key="markov_counts")

    # Compute matrices
    counts_all, probs_all = compute_transition_matrix(G, year_range=yr_range)
    display_all = counts_all if show_counts else probs_all

    if event_compare == "None":
        fig = _make_heatmap(display_all, "All Years", show_counts)
        st.plotly_chart(fig, use_container_width=True, config=PLOTLY_CONFIG)
        chart_download_button(fig, "transition_matrix.png")
    else:
        counts_evt, probs_evt = compute_transition_matrix(G, event_filter=event_compare, year_range=yr_range)
        counts_normal = counts_all - counts_evt
        row_sums_n = counts_normal.sum(axis=1)
        probs_normal = counts_normal.div(row_sums_n.replace(0, 1), axis=0)

        display_normal = counts_normal if show_counts else probs_normal
        display_evt = counts_evt if show_counts else probs_evt

        col_a, col_b = st.columns(2)
        with col_a:
            st.markdown("**Normal Years**")
            fig_n = _make_heatmap(display_normal, "", show_counts, height=380)
            st.plotly_chart(fig_n, use_container_width=True, config=PLOTLY_CONFIG)
            chart_download_button(fig_n, "transition_matrix_normal.png")
        with col_b:
            st.markdown(f"**During {event_compare}**")
            fig_e = _make_heatmap(display_evt, "", show_counts, height=380)
            st.plotly_chart(fig_e, use_container_width=True, config=PLOTLY_CONFIG)
            chart_download_button(fig_e, "transition_matrix_event.png")

        if not show_counts:
            st.markdown("**Probability Shift (Event minus Normal)**")
            st.caption("Red = transition MORE likely during event. Blue = LESS likely.")
            delta = probs_evt - probs_normal
            fig_d = _make_matrix_figure(delta, "", fmt="+.2f", colorscale="RdBu_r",
                                         height=380, zmin=-0.3, zmax=0.3)
            st.plotly_chart(fig_d, use_container_width=True, config=PLOTLY_CONFIG)
            chart_download_button(fig_d, "transition_probability_shift.png")

            shifts = []
            for f_s in STAGE_ORDER:
                for t_s in STAGE_ORDER:
                    d = delta.loc[f_s, t_s]
                    if abs(d) > 0.02:
                        shifts.append({"From": f_s, "To": t_s,
                                       "Normal": f"{probs_normal.loc[f_s, t_s]:.1%}",
                                       f"{event_compare}": f"{probs_evt.loc[f_s, t_s]:.1%}",
                                       "Shift": f"{d:+.1%}"})
            if shifts:
                shifts_df = pd.DataFrame(shifts).sort_values(
                    "Shift", key=lambda x: x.str.rstrip('%').astype(float).abs(), ascending=False)
                st.markdown(f"**Biggest probability shifts during {event_compare}**")
                st.dataframe(shifts_df.head(10), use_container_width=True, hide_index=True)
                df_download_button(shifts_df.head(10), "probability_shifts.csv")

    # Stickiness bar
    st.divider()
    st.markdown("#### Stage Stickiness")
    st.caption("% of firm-years where a company stayed in the same stage the following year. Higher = more absorbing.")
    sticky = compute_stickiness(G, year_range=yr_range)

    fig_stick = go.Figure(go.Bar(
        x=list(sticky.keys()), y=list(sticky.values()),
        marker_color=[STAGE_COLORS.get(s, "#94A3B8") for s in sticky.keys()],
        text=[f"{v:.0f}%" for v in sticky.values()],
        textposition="outside",
    ))
    fig_stick.update_layout(**plotly_layout("", height=320))
    fig_stick.update_layout(yaxis_title="Stickiness (%)", xaxis_title="")
    st.plotly_chart(fig_stick, use_container_width=True, config=PLOTLY_CONFIG)
    chart_download_button(fig_stick, "stage_stickiness.png")

    # Stage × Metric Matrix
    st.divider()
    st.markdown("#### Stage × Financial Metric Matrix")
    st.caption("Average financial characteristics at each life stage — reveals the DNA of each stage")
    metric_matrix = compute_stage_metric_matrix(G)
    fig_mm = _make_matrix_figure(metric_matrix, "", fmt=".2f", height=380)
    st.plotly_chart(fig_mm, use_container_width=True, config=PLOTLY_CONFIG)
    chart_download_button(fig_mm, "stage_metric_matrix.png")
    st.dataframe(metric_matrix.round(3), use_container_width=True)
    df_download_button(metric_matrix.round(3).reset_index(), "stage_metric_matrix.csv")


# ══════════════════════════════════════════════
# TAB 2: Event Impact Matrices
# ══════════════════════════════════════════════
with tab_events:
    st.subheader("Event Impact Matrices")
    st.caption("Three matrices showing how GFC, IBC, and COVID affected each life stage differently")

    impact = compute_event_impact_matrix(G, fin_df)

    # --- Matrix 1: Leverage Impact ---
    st.markdown("#### 1. Leverage Impact Matrix")
    st.caption("Average leverage by stage during each event, and the delta vs normal years. Red = leverage increased during event.")

    lev_df = impact["leverage"]
    # Show delta columns as a heatmap
    delta_cols = [c for c in lev_df.columns if "Δ" in c]
    if delta_cols:
        delta_display = lev_df[delta_cols].copy()
        delta_display.columns = [c.replace(" Δ", "") for c in delta_cols]
        fig_lev = _make_matrix_figure(delta_display, "Leverage Change vs Normal (pp)",
                                       fmt="+.2f", colorscale="RdBu_r", height=380,
                                       zmin=-5, zmax=5)
        st.plotly_chart(fig_lev, use_container_width=True, config=PLOTLY_CONFIG)
        chart_download_button(fig_lev, "event_leverage_impact.png")

    # Full table
    with st.expander("Full leverage data"):
        st.dataframe(lev_df.round(2), use_container_width=True)
        df_download_button(lev_df.round(2).reset_index(), "event_leverage_full.csv")

    st.divider()

    # --- Matrix 2: Transition Rate ---
    st.markdown("#### 2. Transition Rate Matrix")
    st.caption("% of firm-years at each stage where the firm changed stage. Higher = more disrupted by the event.")

    trans_df = impact["transition_rate"]
    rate_cols = [c for c in trans_df.columns if "Trans Rate" in c and c != "Normal Trans Rate"]
    if rate_cols:
        rate_display = trans_df[["Normal Trans Rate"] + rate_cols].copy()
        rate_display.columns = ["Normal"] + [c.replace(" Trans Rate", "") for c in rate_cols]
        fig_tr = _make_matrix_figure(rate_display, "Transition Rate by Stage × Event (%)",
                                      fmt=".1f", colorscale="OrRd", height=380)
        st.plotly_chart(fig_tr, use_container_width=True, config=PLOTLY_CONFIG)
        chart_download_button(fig_tr, "event_transition_rate.png")

    st.divider()

    # --- Matrix 3: Deterioration ---
    st.markdown("#### 3. Deterioration Matrix")
    st.caption("Of firms that transitioned during an event, % that moved to a WORSE stage (higher rank). Empty = no transitions from that stage.")

    det_df = impact["deterioration"]
    det_display = det_df.copy()
    det_display.columns = [c.replace(" Deterioration %", "") for c in det_display.columns]
    fig_det = _make_matrix_figure(det_display, "Deterioration Rate (%)",
                                   fmt=".0f", colorscale="Reds", height=380)
    st.plotly_chart(fig_det, use_container_width=True, config=PLOTLY_CONFIG)
    chart_download_button(fig_det, "event_deterioration_rate.png")

    st.divider()

    # --- Event comparison bar chart ---
    st.markdown("#### Event Comparison: Avg Leverage Shift by Stage")
    if delta_cols:
        bar_data = []
        for stage in STAGE_ORDER:
            for evt in ["GFC", "IBC", "COVID"]:
                col = f"{evt} Δ"
                if col in lev_df.columns:
                    val = lev_df.loc[stage, col]
                    if pd.notna(val):
                        bar_data.append({"Stage": stage, "Event": evt, "Leverage Δ (pp)": val})

        if bar_data:
            bdf = pd.DataFrame(bar_data)
            fig_bar = px.bar(bdf, x="Stage", y="Leverage Δ (pp)", color="Event", barmode="group",
                             color_discrete_map={"GFC": "#EF4444", "IBC": SECONDARY, "COVID": ACCENT},
                             category_orders={"Stage": STAGE_ORDER})
            fig_bar.add_hline(y=0, line_dash="dash", line_color="#D1D5DB")
            fig_bar.update_layout(**plotly_layout("", height=400))
            st.plotly_chart(fig_bar, use_container_width=True, config=PLOTLY_CONFIG)
            chart_download_button(fig_bar, "event_leverage_shift_by_stage.png")


# ══════════════════════════════════════════════
# TAB 3: Stage Pathway Discovery
# ══════════════════════════════════════════════
with tab_paths:
    st.subheader("Stage Pathway Discovery")
    st.caption("Most common multi-step transition sequences and paths to specific stages")

    col_p1, col_p2 = st.columns([1, 1])
    with col_p1:
        seq_length = st.slider("Sequence length", 2, 4, 2, key="seq_len")
        min_freq = st.slider("Minimum frequency", 1, 50, 5, key="min_freq")
    with col_p2:
        target_stage = st.selectbox("Paths leading TO", STAGE_ORDER, index=6, key="target_stage")

    # Top sequences
    st.markdown(f"#### Most Common {seq_length}-Step Sequences")
    seqs = extract_transition_sequences(G, min_length=seq_length, max_length=seq_length)
    filtered_seqs = {k: v for k, v in seqs.items() if v >= min_freq and len(k) == seq_length}
    sorted_seqs = sorted(filtered_seqs.items(), key=lambda x: -x[1])[:20]

    if sorted_seqs:
        fig_seq = go.Figure(go.Bar(
            y=[" → ".join(s) for s, _ in reversed(sorted_seqs)],
            x=[c for _, c in reversed(sorted_seqs)],
            orientation="h",
            marker_color=PRIMARY,
            text=[str(c) for _, c in reversed(sorted_seqs)],
            textposition="outside",
        ))
        fig_seq.update_layout(**plotly_layout("", height=max(350, len(sorted_seqs) * 28)))
        fig_seq.update_layout(xaxis_title="Frequency", yaxis_title="")
        st.plotly_chart(fig_seq, use_container_width=True, config=PLOTLY_CONFIG)
        chart_download_button(fig_seq, "stage_sequences.png")
    else:
        st.info("No sequences found with current filters.")

    st.divider()

    # Paths to target stage
    st.markdown(f"#### How Do Firms Reach **{target_stage}**?")
    st.caption(f"Most common stage sequences ending in {target_stage}, looking back up to 3 steps")

    paths = find_paths_to_stage(G, target_stage, lookback=3)
    if paths:
        top_paths = paths.most_common(15)

        # Build sunburst
        sunburst_ids = [target_stage]
        sunburst_labels = [target_stage]
        sunburst_parents = [""]
        sunburst_values = [sum(c for _, c in top_paths)]
        sunburst_colors = [STAGE_COLORS.get(target_stage, "#94A3B8")]

        for path, count in top_paths:
            for depth in range(len(path) - 2, -1, -1):
                stage = path[depth]
                child_path = path[depth:]
                node_id = " → ".join(child_path)
                parent_path = path[depth + 1:]
                parent_id = " → ".join(parent_path) if len(parent_path) > 1 else parent_path[0] if parent_path else ""

                if node_id not in sunburst_ids:
                    sunburst_ids.append(node_id)
                    sunburst_labels.append(stage)
                    sunburst_parents.append(parent_id)
                    sunburst_values.append(count)
                    sunburst_colors.append(STAGE_COLORS.get(stage, "#94A3B8"))

        fig_sun = go.Figure(go.Sunburst(
            ids=sunburst_ids, labels=sunburst_labels, parents=sunburst_parents,
            values=sunburst_values, marker=dict(colors=sunburst_colors),
            branchvalues="total",
        ))
        sun_layout = plotly_layout("", height=450)
        sun_layout["margin"] = dict(l=10, r=10, t=30, b=10)
        fig_sun.update_layout(**sun_layout)
        st.plotly_chart(fig_sun, use_container_width=True, config=PLOTLY_CONFIG)
        chart_download_button(fig_sun, "stage_paths_sunburst.png")

        path_df = pd.DataFrame([{"Path": " → ".join(p), "Companies": c} for p, c in top_paths])
        st.dataframe(path_df, use_container_width=True, hide_index=True)
        df_download_button(path_df, "stage_paths.csv")
    else:
        st.info(f"No transition paths found leading to {target_stage}.")

    # Transition velocity: avg years spent in each stage before leaving
    st.divider()
    st.markdown("#### Stage Duration Matrix")
    st.caption("Average consecutive years a firm stays in each stage before transitioning out")

    duration_data = {}
    for n, d in G.nodes(data=True):
        if d.get("type") != "company":
            continue
        obs_list = sorted(
            [(G.nodes[nb].get("year"), _get_obs_stage(G, nb)) for nb in G.neighbors(n)
             if G.nodes[nb].get("type") == "observation"],
        )
        if not obs_list:
            continue
        # Count consecutive years in same stage
        runs = []
        curr_stage = obs_list[0][1]
        run_len = 1
        for i in range(1, len(obs_list)):
            if obs_list[i][1] == curr_stage:
                run_len += 1
            else:
                if curr_stage:
                    runs.append((curr_stage, run_len))
                curr_stage = obs_list[i][1]
                run_len = 1
        if curr_stage:
            runs.append((curr_stage, run_len))

        for stage, length in runs:
            if stage not in duration_data:
                duration_data[stage] = []
            duration_data[stage].append(length)

    dur_rows = []
    for stage in STAGE_ORDER:
        vals = duration_data.get(stage, [])
        if vals:
            dur_rows.append({
                "Stage": stage,
                "Avg Duration (yrs)": np.mean(vals),
                "Median Duration": np.median(vals),
                "Max Duration": max(vals),
                "N Spells": len(vals),
            })
    if dur_rows:
        dur_df = pd.DataFrame(dur_rows)
        fig_dur = go.Figure(go.Bar(
            x=dur_df["Stage"], y=dur_df["Avg Duration (yrs)"],
            marker_color=[STAGE_COLORS.get(s, "#94A3B8") for s in dur_df["Stage"]],
            text=[f"{v:.1f}" for v in dur_df["Avg Duration (yrs)"]],
            textposition="outside",
        ))
        fig_dur.update_layout(**plotly_layout("", height=350))
        fig_dur.update_layout(yaxis_title="Avg Years", xaxis_title="")
        st.plotly_chart(fig_dur, use_container_width=True, config=PLOTLY_CONFIG)
        chart_download_button(fig_dur, "stage_duration.png")
        st.dataframe(dur_df.set_index("Stage").round(1), use_container_width=True)
        df_download_button(dur_df, "stage_duration.csv")


# ══════════════════════════════════════════════
# TAB 4: COVID Cohort Analysis
# ══════════════════════════════════════════════
with tab_covid:
    st.subheader("Post-COVID Cohort Analysis")
    st.caption("Which firms entered Decline after COVID? Which recovered? Comparing pre-COVID (2019) vs post-COVID (2022+) stages.")

    cohort_data = compute_covid_cohorts(G, fin_df)

    if "error" in cohort_data:
        st.warning(cohort_data["error"])
    else:
        cdf = cohort_data["cohort_df"]

        # Backwards compat: compute profitability_change if not present
        if "profitability_change" not in cdf.columns:
            cdf = cdf.copy()
            cdf["profitability_change"] = (
                cdf["post_profitability"] - cdf["pre_profitability"]
            ).where(cdf["pre_profitability"].notna() & cdf["post_profitability"].notna())

        # KPIs
        kc1, kc2, kc3, kc4, kc5 = st.columns(5)
        kc1.metric("Total Firms", cohort_data["n_total"])
        kc2.metric("Deteriorated", f"{cohort_data['n_deteriorated']} ({cohort_data['pct_deteriorated']}%)")
        kc3.metric("Improved", f"{cohort_data['n_improved']} ({cohort_data['pct_improved']}%)")
        kc4.metric("Entered Decline", cohort_data["n_entered_decline"])
        kc5.metric("Recovered", cohort_data["n_recovered"])

        # Stage migration heatmap
        st.markdown("#### Pre-COVID → Post-COVID Stage Migration")
        migration = cdf.groupby(["pre_stage", "post_stage"]).size().reset_index(name="count")
        pivot = migration.pivot_table(index="pre_stage", columns="post_stage",
                                       values="count", fill_value=0)
        ordered = [s for s in STAGE_ORDER if s in pivot.index]
        ordered_cols = [s for s in STAGE_ORDER if s in pivot.columns]
        if ordered and ordered_cols:
            pivot = pivot.reindex(index=ordered, columns=ordered_cols, fill_value=0)
            fig_mig = _make_matrix_figure(pivot, "Firms: Pre-COVID Stage (rows) → Post-COVID Stage (cols)",
                                           fmt=".0f", height=400)
            st.plotly_chart(fig_mig, use_container_width=True, config=PLOTLY_CONFIG)
            chart_download_button(fig_mig, "covid_stage_migration.png")

        # Leverage change comparison
        st.markdown("#### Leverage Change: Deteriorated vs Improved Firms")
        det_firms = cdf[cdf["deteriorated"]]["leverage_change"].dropna()
        imp_firms = cdf[cdf["improved"]]["leverage_change"].dropna()

        if not det_firms.empty or not imp_firms.empty:
            box_data = []
            for val in det_firms:
                box_data.append({"Group": "Deteriorated", "Leverage Change (pp)": val})
            for val in imp_firms:
                box_data.append({"Group": "Improved", "Leverage Change (pp)": val})
            if box_data:
                bdf = pd.DataFrame(box_data)
                fig_box = px.box(bdf, x="Group", y="Leverage Change (pp)", color="Group",
                                  color_discrete_map={"Deteriorated": "#EF4444", "Improved": "#22C55E"})
                fig_box.update_layout(**plotly_layout("", height=350))
                st.plotly_chart(fig_box, use_container_width=True, config=PLOTLY_CONFIG)
                chart_download_button(fig_box, "covid_leverage_change.png")

        # Profitability change comparison
        st.markdown("#### Profitability Change: Deteriorated vs Improved Firms")
        det_prof = cdf[cdf["deteriorated"]]["profitability_change"].dropna()
        imp_prof = cdf[cdf["improved"]]["profitability_change"].dropna()

        if not det_prof.empty or not imp_prof.empty:
            prof_box_data = []
            for val in det_prof:
                prof_box_data.append({"Group": "Deteriorated", "Profitability Change (pp)": val})
            for val in imp_prof:
                prof_box_data.append({"Group": "Improved", "Profitability Change (pp)": val})
            if prof_box_data:
                pbdf = pd.DataFrame(prof_box_data)
                fig_prof_box = px.box(pbdf, x="Group", y="Profitability Change (pp)", color="Group",
                                      color_discrete_map={"Deteriorated": "#EF4444", "Improved": "#22C55E"})
                fig_prof_box.update_layout(**plotly_layout("", height=350))
                st.plotly_chart(fig_prof_box, use_container_width=True, config=PLOTLY_CONFIG)
                chart_download_button(fig_prof_box, "covid_profitability_change.png")

        # Statistical comparison: Deteriorated vs Improved cohorts
        st.markdown("#### Statistical Tests: Deteriorated vs Improved Cohorts")
        st.caption(
            "Welch's t-test (assumes unequal variances) + Mann-Whitney U (non-parametric). "
            "Minimum 5 firms per group required."
        )
        from helpers import significance_stars, format_pvalue

        _stat_rows = []

        det_lev_s = cdf[cdf["deteriorated"]]["leverage_change"].dropna()
        imp_lev_s = cdf[cdf["improved"]]["leverage_change"].dropna()
        if len(det_lev_s) >= 5 and len(imp_lev_s) >= 5:
            _t, _p_t = _scipy_stats.ttest_ind(det_lev_s, imp_lev_s, equal_var=False)
            _u, _p_u = _scipy_stats.mannwhitneyu(det_lev_s, imp_lev_s, alternative="two-sided")
            _stat_rows.append({
                "Metric": "Leverage Change (pp)",
                "Det Mean": f"{det_lev_s.mean():.2f}",
                "Imp Mean": f"{imp_lev_s.mean():.2f}",
                "Welch t": f"{_t:.2f}",
                "t p-value": f"{format_pvalue(_p_t)}{significance_stars(_p_t)}",
                "MW U": f"{_u:.0f}",
                "MW p-value": f"{format_pvalue(_p_u)}{significance_stars(_p_u)}",
            })

        det_prof_s = cdf[cdf["deteriorated"]]["profitability_change"].dropna()
        imp_prof_s = cdf[cdf["improved"]]["profitability_change"].dropna()
        if len(det_prof_s) >= 5 and len(imp_prof_s) >= 5:
            _t2, _p_t2 = _scipy_stats.ttest_ind(det_prof_s, imp_prof_s, equal_var=False)
            _u2, _p_u2 = _scipy_stats.mannwhitneyu(det_prof_s, imp_prof_s, alternative="two-sided")
            _stat_rows.append({
                "Metric": "Profitability Change (pp)",
                "Det Mean": f"{det_prof_s.mean():.3f}",
                "Imp Mean": f"{imp_prof_s.mean():.3f}",
                "Welch t": f"{_t2:.2f}",
                "t p-value": f"{format_pvalue(_p_t2)}{significance_stars(_p_t2)}",
                "MW U": f"{_u2:.0f}",
                "MW p-value": f"{format_pvalue(_p_u2)}{significance_stars(_p_u2)}",
            })

        if _stat_rows:
            st.dataframe(pd.DataFrame(_stat_rows), use_container_width=True, hide_index=True)
            df_download_button(pd.DataFrame(_stat_rows), "covid_cohort_stats.csv")
        elif cohort_data["n_deteriorated"] < 5 or cohort_data["n_improved"] < 5:
            st.info("Not enough firms in each cohort for statistical tests (minimum 5 per group).")

        # Interpretation
        with st.expander("What does this mean?"):
            _pct_det = cohort_data["pct_deteriorated"]
            _pct_imp = cohort_data["pct_improved"]
            _n_ent = cohort_data["n_entered_decline"]
            _n_rec = cohort_data["n_recovered"]
            _n_tot = cohort_data["n_total"]
            st.markdown(
                f"**{_n_ent} firms** entered Decline or Decay after COVID that were NOT in decline before — "
                f"representing COVID-induced structural deterioration beyond pre-existing weakness.\n\n"
                f"**{_n_rec} firms** recovered from decline-stage classifications post-COVID, "
                f"demonstrating COVID resilience or restructuring effectiveness.\n\n"
                f"Across all **{_n_tot} firms** with pre-COVID (2019) and post-COVID (2022+) data: "
                f"**{_pct_det}% deteriorated** (moved to a worse life stage) vs "
                f"**{_pct_imp}% improved** (moved to a better life stage). "
                f"A deterioration rate above 50% signals net COVID-era structural damage to the panel."
            )

        # Table of firms that entered decline after COVID
        if cohort_data["n_entered_decline"] > 0:
            st.markdown("#### Firms That Entered Decline/Decay After COVID")
            entered = cdf[cdf["entered_decline_after_covid"]].sort_values("leverage_change", ascending=False)
            _entered_display = entered[["company", "industry", "pre_stage", "post_stage", "leverage_change"]].rename(columns={
                "company": "Company", "industry": "Industry",
                "pre_stage": "Pre-COVID Stage", "post_stage": "Post-COVID Stage",
                "leverage_change": "Leverage Δ (pp)",
            })
            st.dataframe(
                _entered_display,
                use_container_width=True, hide_index=True,
            )
            df_download_button(_entered_display, "covid_decline_firms.csv")

        # Recovered firms
        if cohort_data["n_recovered"] > 0:
            st.markdown("#### Firms That Recovered After COVID")
            recovered = cdf[cdf["recovered"]].sort_values("leverage_change")
            _recovered_display = recovered[["company", "industry", "pre_stage", "post_stage", "leverage_change"]].rename(columns={
                "company": "Company", "industry": "Industry",
                "pre_stage": "Pre-COVID Stage", "post_stage": "Post-COVID Stage",
                "leverage_change": "Leverage Δ (pp)",
            })
            st.dataframe(
                _recovered_display,
                use_container_width=True, hide_index=True,
            )
            df_download_button(_recovered_display, "covid_recovered_firms.csv")


# ══════════════════════════════════════════════
# TAB 5: Multi-Hop Company Profiler
# ══════════════════════════════════════════════
with tab_profiler:
    st.subheader("Multi-Hop Company Profiler")
    st.caption("Chain conditions to find companies matching complex criteria across stages, events, and metrics")

    st.markdown("**Condition 1: Life stage at a specific year**")
    col_s1, col_y1 = st.columns(2)
    with col_s1:
        cond1_stage = st.selectbox("Stage", ["(any)"] + STAGE_ORDER, key="prof_s1")
    with col_y1:
        yr_min_p, yr_max_p = int(fin_df["year"].min()), int(fin_df["year"].max())
        cond1_year = st.slider("Year", yr_min_p, yr_max_p, 2015, key="prof_y1")

    st.markdown("**Condition 2: Stage transition**")
    col_from, col_to, col_yr2 = st.columns(3)
    with col_from:
        cond2_from = st.selectbox("From stage", ["(any)"] + STAGE_ORDER, key="prof_from")
    with col_to:
        cond2_to = st.selectbox("To stage", ["(any)"] + STAGE_ORDER, key="prof_to")
    with col_yr2:
        cond2_yr = st.slider("Transition year range", yr_min_p, yr_max_p, (yr_min_p, yr_max_p), key="prof_yr2")

    st.markdown("**Condition 3: During event**")
    cond3_event = st.selectbox("Event", ["(any)", "GFC", "IBC", "COVID"], key="prof_evt")

    st.markdown("**Condition 4: Financial metric**")
    col_m, col_op, col_v = st.columns(3)
    with col_m:
        cond4_metric = st.selectbox("Metric", ["(none)", "leverage", "profitability", "tangibility", "firm_size"], key="prof_met")
    with col_op:
        cond4_op = st.selectbox("Operator", [">", "<", ">=", "<="], key="prof_op")
    with col_v:
        cond4_val = st.number_input("Value", value=0.0, step=0.1, key="prof_val")

    if st.button("Run Query", type="primary", key="prof_run"):
        candidates = set(n for n, d in G.nodes(data=True) if d.get("type") == "company")
        counts_by_step = [len(candidates)]

        # Condition 1
        if cond1_stage != "(any)":
            filtered = set()
            for cid in candidates:
                code = G.nodes[cid].get("company_code")
                obs_id = f"obs:{code}:{cond1_year}"
                if G.has_node(obs_id) and _get_obs_stage(G, obs_id) == cond1_stage:
                    filtered.add(cid)
            candidates = filtered
        counts_by_step.append(len(candidates))

        # Condition 2
        if cond2_from != "(any)" or cond2_to != "(any)":
            filtered = set()
            for cid in candidates:
                for u, v, data in G.edges(cid, data=True):
                    if data.get("relation") != "TRANSITION":
                        continue
                    yr = data.get("year", 0)
                    if yr < cond2_yr[0] or yr > cond2_yr[1]:
                        continue
                    if cond2_from != "(any)" and data.get("from_stage") != cond2_from:
                        continue
                    if cond2_to != "(any)" and data.get("to_stage") != cond2_to:
                        continue
                    filtered.add(cid)
                    break
            candidates = filtered
        counts_by_step.append(len(candidates))

        # Condition 3
        if cond3_event != "(any)":
            filtered = set()
            event_id = f"event:{cond3_event}"
            for cid in candidates:
                for nb in G.neighbors(cid):
                    if G.nodes[nb].get("type") == "observation" and G.has_edge(nb, event_id):
                        filtered.add(cid)
                        break
            candidates = filtered
        counts_by_step.append(len(candidates))

        # Condition 4
        if cond4_metric != "(none)":
            ops = {">": operator.gt, "<": operator.lt, ">=": operator.ge, "<=": operator.le}
            op_fn = ops[cond4_op]
            filtered = set()
            for cid in candidates:
                for nb in G.neighbors(cid):
                    nd = G.nodes[nb]
                    if nd.get("type") == "observation":
                        val = nd.get(cond4_metric)
                        if val is not None and op_fn(val, cond4_val):
                            filtered.add(cid)
                            break
            candidates = filtered
        counts_by_step.append(len(candidates))

        # Funnel
        st.divider()
        labels = ["All", "Stage Filter", "Transition", "Event", "Metric"]
        funnel_cols = st.columns(5)
        for col, label, count in zip(funnel_cols, labels, counts_by_step):
            col.metric(label, count)

        if candidates:
            result_rows = []
            for cid in sorted(candidates):
                nd = G.nodes[cid]
                code = nd.get("company_code")
                obs_list = sorted(
                    [(G.nodes[n].get("year"), n) for n in G.neighbors(cid)
                     if G.nodes[n].get("type") == "observation"])
                latest = G.nodes[obs_list[-1][1]] if obs_list else {}
                trans = query_stage_transitions(G, code)

                result_rows.append({
                    "Company": nd.get("label"),
                    "Industry": nd.get("industry"),
                    "Latest Stage": _get_obs_stage(G, obs_list[-1][1]) if obs_list else "N/A",
                    "Leverage": latest.get("leverage"),
                    "Profitability": latest.get("profitability"),
                    "Transitions": len(trans),
                })

            rdf = pd.DataFrame(result_rows)
            st.dataframe(rdf, use_container_width=True, hide_index=True,
                         column_config={
                             "Leverage": st.column_config.NumberColumn(format="%.2f"),
                             "Profitability": st.column_config.NumberColumn(format="%.3f"),
                         })
            df_download_button(rdf, "profiler_results.csv")
        else:
            st.warning("No companies match all conditions.")
