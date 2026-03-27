"""
Knowledge Graph Explorer — Stage Transition Dynamics.

Answers: How do firms move between life stages? What triggers those moves?
How do macro events reshape transition patterns?

Tab 1: Transition Probability Matrix (Markov Chain)
Tab 2: Event-Triggered Transitions
Tab 3: Stage Pathway Discovery
Tab 4: Multi-Hop Company Profiler
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
import db
from graph_builder import (
    build_knowledge_graph, get_graph_stats,
    compute_transition_matrix, compute_stickiness,
    find_event_triggered_transitions,
    extract_transition_sequences, find_paths_to_stage,
    query_stage_transitions, _get_obs_stage,
)
from helpers import (
    STAGE_COLORS, STAGE_ORDER, STAGE_RANK, plotly_layout, event_bands,
    PRIMARY, SECONDARY, ACCENT, PLOTLY_CONFIG,
)

st.header("Knowledge Graph — Stage Transition Dynamics")
st.caption("How firms move between life stages, what triggers transitions, and how events reshape patterns")


# ── Build / cache the graph + source data ──
@st.cache_resource
def _build_graph():
    fin_df = db.get_graph_financials()
    own_df = db.get_graph_ownership()
    G = build_knowledge_graph(fin_df, own_df)
    return G, fin_df


G, fin_df = _build_graph()
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


# ── Helper: heatmap builder ──
def _make_heatmap(df, title, show_counts, height=450):
    fmt = ".0f" if show_counts else ".1%"
    text = [[f"{v:.0f}" if show_counts else f"{v:.1%}" for v in row] for row in df.values]

    fig = px.imshow(
        df.values, x=STAGE_ORDER, y=STAGE_ORDER,
        color_continuous_scale="Teal", aspect="auto",
        labels=dict(x="To Stage", y="From Stage", color="Count" if show_counts else "Probability"),
    )
    fig.update_traces(text=text, texttemplate="%{text}", textfont_size=10)
    hm_layout = plotly_layout(title, height)
    hm_layout["margin"] = dict(l=120, r=20, t=40, b=80)
    fig.update_layout(**hm_layout)
    return fig


# ── Tabs ──
tab_markov, tab_events, tab_paths, tab_profiler = st.tabs([
    "Transition Probabilities",
    "Event-Triggered Transitions",
    "Stage Pathways",
    "Company Profiler",
])


# ══════════════════════════════════════════════
# TAB 1: Transition Probability Matrix
# ══════════════════════════════════════════════
with tab_markov:
    st.subheader("Stage Transition Probability Matrix")
    st.caption("If a firm is in stage X this year, what's the probability it moves to stage Y next year?")

    col_ctrl1, col_ctrl2 = st.columns([1, 1])
    with col_ctrl1:
        event_compare = st.selectbox(
            "Compare with event", ["None", "GFC", "IBC", "COVID"],
            key="markov_event",
            help="Show normal-year probabilities alongside event-year probabilities",
        )
    with col_ctrl2:
        yr_min, yr_max = int(fin_df["year"].min()), int(fin_df["year"].max())
        yr_range = st.slider("Year range", yr_min, yr_max, (yr_min, yr_max), key="markov_yr")

    show_counts = st.toggle("Show counts instead of probabilities", value=False, key="markov_counts")

    # Compute matrices
    counts_all, probs_all = compute_transition_matrix(G, year_range=yr_range)
    display_all = counts_all if show_counts else probs_all

    if event_compare == "None":
        # Single heatmap
        fig = _make_heatmap(display_all, "All Years", show_counts)
        st.plotly_chart(fig, use_container_width=True, config=PLOTLY_CONFIG)
    else:
        # Side-by-side: Normal vs Event vs Delta
        counts_evt, probs_evt = compute_transition_matrix(G, event_filter=event_compare, year_range=yr_range)

        # Normal = all minus event
        counts_normal = counts_all - counts_evt
        row_sums_n = counts_normal.sum(axis=1)
        probs_normal = counts_normal.div(row_sums_n.replace(0, 1), axis=0)

        display_normal = counts_normal if show_counts else probs_normal
        display_evt = counts_evt if show_counts else probs_evt

        col_a, col_b = st.columns(2)
        with col_a:
            st.markdown("**Normal Years**")
            fig_n = _make_heatmap(display_normal, "", show_counts, height=400)
            st.plotly_chart(fig_n, use_container_width=True, config=PLOTLY_CONFIG)
        with col_b:
            st.markdown(f"**During {event_compare}**")
            fig_e = _make_heatmap(display_evt, "", show_counts, height=400)
            st.plotly_chart(fig_e, use_container_width=True, config=PLOTLY_CONFIG)

        # Delta heatmap (event minus normal probabilities)
        if not show_counts:
            st.markdown("**Probability Shift (Event − Normal)**")
            st.caption("Red = transition MORE likely during event. Blue = LESS likely.")
            delta = probs_evt - probs_normal
            fig_d = px.imshow(
                delta.values, x=STAGE_ORDER, y=STAGE_ORDER,
                color_continuous_scale="RdBu_r", zmin=-0.3, zmax=0.3,
                aspect="auto",
                labels=dict(x="To Stage", y="From Stage", color="Δ Prob"),
            )
            fig_d.update_traces(
                text=[[f"{v:+.2f}" if abs(v) > 0.01 else "" for v in row] for row in delta.values],
                texttemplate="%{text}", textfont_size=10,
            )
            d_layout = plotly_layout("", height=400)
            d_layout["margin"] = dict(l=120, r=20, t=30, b=80)
            fig_d.update_layout(**d_layout)
            st.plotly_chart(fig_d, use_container_width=True, config=PLOTLY_CONFIG)

            # Top surprising transitions
            shifts = []
            for f_s in STAGE_ORDER:
                for t_s in STAGE_ORDER:
                    d = delta.loc[f_s, t_s]
                    if abs(d) > 0.02:
                        shifts.append({"From": f_s, "To": t_s, "Normal": f"{probs_normal.loc[f_s, t_s]:.1%}",
                                       f"{event_compare}": f"{probs_evt.loc[f_s, t_s]:.1%}", "Shift": f"{d:+.1%}"})
            if shifts:
                shifts_df = pd.DataFrame(shifts).sort_values("Shift", key=lambda x: x.str.rstrip('%').astype(float).abs(), ascending=False)
                st.markdown(f"**Biggest probability shifts during {event_compare}**")
                st.dataframe(shifts_df.head(10), use_container_width=True, hide_index=True)

    # Stickiness
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
    fig_stick.update_layout(**plotly_layout("", height=350))
    fig_stick.update_layout(yaxis_title="Stickiness (%)", xaxis_title="")
    st.plotly_chart(fig_stick, use_container_width=True, config=PLOTLY_CONFIG)


# ══════════════════════════════════════════════
# TAB 2: Event-Triggered Transitions
# ══════════════════════════════════════════════
with tab_events:
    st.subheader("Event-Triggered Stage Transitions")
    st.caption("Which firms changed life stage during a macro event? What happened to their financials?")

    col_ev, col_ind = st.columns([1, 1])
    with col_ev:
        event_choice = st.selectbox("Event", ["GFC", "IBC", "COVID"], key="evt_event")
    with col_ind:
        industries = sorted(fin_df["industry_group"].unique())
        ind_filter = st.selectbox("Industry filter", ["(all)"] + industries, key="evt_ind")

    results = find_event_triggered_transitions(G, event_choice)
    if ind_filter != "(all)":
        results = [r for r in results if r["industry"] == ind_filter]

    transitioned = [r for r in results if r["had_transition"]]
    stable = [r for r in results if not r["had_transition"]]

    # Summary metrics
    mc1, mc2, mc3, mc4 = st.columns(4)
    mc1.metric("Firms During Event", len(results))
    mc2.metric("Changed Stage", len(transitioned))
    pct_trans = len(transitioned) / max(len(results), 1) * 100
    mc3.metric("Transition Rate", f"{pct_trans:.0f}%")

    # Deterioration: moved to a higher-rank stage
    deteriorated = sum(1 for r in transitioned
                       if r["pre_stage"] and r["event_stage"]
                       and STAGE_RANK.get(r["event_stage"], 0) > STAGE_RANK.get(r["pre_stage"], 0))
    mc4.metric("Deteriorated", f"{deteriorated} ({deteriorated / max(len(transitioned), 1) * 100:.0f}%)")

    if transitioned:
        # 3-column Sankey: Pre → During → Post
        st.markdown("#### Stage Flow: Pre → During → Post Event")
        st.caption("Tracking the SAME firms across time — each band is a group of companies")

        pre_stages = [r["pre_stage"] or "Unknown" for r in transitioned]
        evt_stages = [r["event_stage"] or "Unknown" for r in transitioned]
        post_stages = [r["post_stage"] or "Unknown" for r in transitioned]

        # Build 3-column Sankey
        all_labels = (
            [f"Pre: {s}" for s in STAGE_ORDER + ["Unknown"]] +
            [f"During: {s}" for s in STAGE_ORDER + ["Unknown"]] +
            [f"Post: {s}" for s in STAGE_ORDER + ["Unknown"]]
        )
        label_idx = {l: i for i, l in enumerate(all_labels)}
        n_stages = len(STAGE_ORDER) + 1

        node_colors = (
            [STAGE_COLORS.get(s, "#94A3B8") for s in STAGE_ORDER] + ["#CBD5E1"] +
            [STAGE_COLORS.get(s, "#94A3B8") for s in STAGE_ORDER] + ["#CBD5E1"] +
            [STAGE_COLORS.get(s, "#94A3B8") for s in STAGE_ORDER] + ["#CBD5E1"]
        )

        from collections import Counter

        def hex_to_rgba(hex_color, alpha=0.3):
            h = hex_color.lstrip("#")
            r, g, b = int(h[:2], 16), int(h[2:4], 16), int(h[4:6], 16)
            return f"rgba({r},{g},{b},{alpha})"

        # Pre → During links
        sources, targets, values, link_colors = [], [], [], []
        pre_to_dur = Counter(zip(pre_stages, evt_stages))
        for (ps, es), cnt in pre_to_dur.items():
            src = label_idx.get(f"Pre: {ps}")
            tgt = label_idx.get(f"During: {es}")
            if src is not None and tgt is not None:
                sources.append(src)
                targets.append(tgt)
                values.append(cnt)
                link_colors.append(hex_to_rgba(STAGE_COLORS.get(es, "#94A3B8")))

        # During → Post links
        dur_to_post = Counter(zip(evt_stages, post_stages))
        for (es, ps), cnt in dur_to_post.items():
            src = label_idx.get(f"During: {es}")
            tgt = label_idx.get(f"Post: {ps}")
            if src is not None and tgt is not None:
                sources.append(src)
                targets.append(tgt)
                values.append(cnt)
                link_colors.append(hex_to_rgba(STAGE_COLORS.get(ps, "#94A3B8")))

        fig_sankey = go.Figure(go.Sankey(
            arrangement="snap",
            node=dict(pad=10, thickness=18, line=dict(color="#E2E8F0", width=0.5),
                      label=all_labels, color=node_colors),
            link=dict(source=sources, target=targets, value=values, color=link_colors),
        ))
        sk_layout = plotly_layout("", height=500)
        sk_layout["margin"] = dict(l=10, r=10, t=20, b=20)
        fig_sankey.update_layout(**sk_layout)
        st.plotly_chart(fig_sankey, use_container_width=True, config=PLOTLY_CONFIG)

        # Scatter: leverage change vs profitability change
        st.markdown("#### Financial Impact of Transitions")
        scatter_data = []
        for r in transitioned:
            if r["pre_leverage"] is not None and r["event_leverage"] is not None:
                scatter_data.append({
                    "Company": r["company_name"],
                    "Leverage Δ": (r["event_leverage"] or 0) - (r["pre_leverage"] or 0),
                    "Profitability Δ": (r["event_profitability"] or 0) - (r["pre_profitability"] or 0),
                    "Transition": f"{r['pre_stage']} → {r['event_stage']}",
                    "Firm Size": r.get("firm_size") or 5,
                })
        if scatter_data:
            sdf = pd.DataFrame(scatter_data)
            fig_sc = px.scatter(
                sdf, x="Leverage Δ", y="Profitability Δ",
                color="Transition", size="Firm Size",
                hover_data=["Company"],
                labels={"Leverage Δ": "Leverage Change (pp)", "Profitability Δ": "Profitability Change"},
            )
            fig_sc.add_hline(y=0, line_dash="dash", line_color="#D1D5DB")
            fig_sc.add_vline(x=0, line_dash="dash", line_color="#D1D5DB")
            fig_sc.update_layout(**plotly_layout("", height=450))
            st.plotly_chart(fig_sc, use_container_width=True, config=PLOTLY_CONFIG)

        # Detail table
        with st.expander(f"All {len(transitioned)} transitioned firms"):
            tdf = pd.DataFrame(transitioned)
            display_cols = ["company_name", "industry", "pre_stage", "event_stage", "post_stage",
                            "pre_leverage", "event_leverage", "post_leverage"]
            available = [c for c in display_cols if c in tdf.columns]
            st.dataframe(tdf[available].sort_values("company_name"), use_container_width=True, hide_index=True)
    else:
        st.info("No firms transitioned during this event with current filters.")


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
        seq_df = pd.DataFrame([
            {"Pathway": " → ".join(seq), "Frequency": count}
            for seq, count in sorted_seqs
        ])

        fig_seq = go.Figure(go.Bar(
            y=[" → ".join(s) for s, _ in reversed(sorted_seqs)],
            x=[c for _, c in reversed(sorted_seqs)],
            orientation="h",
            marker_color=PRIMARY,
            text=[str(c) for _, c in reversed(sorted_seqs)],
            textposition="outside",
        ))
        fig_seq.update_layout(**plotly_layout("", height=max(350, len(sorted_seqs) * 28)))
        fig_seq.update_layout(xaxis_title="Frequency (companies × occurrences)", yaxis_title="")
        st.plotly_chart(fig_seq, use_container_width=True, config=PLOTLY_CONFIG)
    else:
        st.info("No sequences found with current filters.")

    st.divider()

    # Paths to target stage
    st.markdown(f"#### How Do Firms Reach **{target_stage}**?")
    st.caption(f"Most common stage sequences ending in {target_stage}, looking back up to 3 steps")

    paths = find_paths_to_stage(G, target_stage, lookback=3)
    if paths:
        top_paths = paths.most_common(15)

        # Sunburst data
        sunburst_ids, sunburst_labels, sunburst_parents, sunburst_values, sunburst_colors = [], [], [], [], []
        sunburst_ids.append(target_stage)
        sunburst_labels.append(target_stage)
        sunburst_parents.append("")
        sunburst_values.append(sum(c for _, c in top_paths))
        sunburst_colors.append(STAGE_COLORS.get(target_stage, "#94A3B8"))

        # Build sunburst from paths (reversed: target is center, predecessors are outer rings)
        for path, count in top_paths:
            for depth in range(len(path) - 2, -1, -1):
                # depth 0 = furthest back, len-2 = immediate predecessor
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

        # Table
        path_df = pd.DataFrame([
            {"Path": " → ".join(p), "Companies": c}
            for p, c in top_paths
        ])
        st.dataframe(path_df, use_container_width=True, hide_index=True)
    else:
        st.info(f"No transition paths found leading to {target_stage}.")


# ══════════════════════════════════════════════
# TAB 4: Multi-Hop Company Profiler
# ══════════════════════════════════════════════
with tab_profiler:
    st.subheader("Multi-Hop Company Profiler")
    st.caption("Chain conditions to find companies matching complex criteria across stages, events, and metrics")

    # Condition 1: Stage at year
    st.markdown("**Condition 1: Life stage at a specific year**")
    col_s1, col_y1 = st.columns(2)
    with col_s1:
        cond1_stage = st.selectbox("Stage", ["(any)"] + STAGE_ORDER, key="prof_s1")
    with col_y1:
        yr_min_p, yr_max_p = int(fin_df["year"].min()), int(fin_df["year"].max())
        cond1_year = st.slider("Year", yr_min_p, yr_max_p, 2015, key="prof_y1")

    # Condition 2: Transition type
    st.markdown("**Condition 2: Stage transition**")
    col_from, col_to, col_yr2 = st.columns(3)
    with col_from:
        cond2_from = st.selectbox("From stage", ["(any)"] + STAGE_ORDER, key="prof_from")
    with col_to:
        cond2_to = st.selectbox("To stage", ["(any)"] + STAGE_ORDER, key="prof_to")
    with col_yr2:
        cond2_yr = st.slider("Transition year range", yr_min_p, yr_max_p, (yr_min_p, yr_max_p), key="prof_yr2")

    # Condition 3: Event
    st.markdown("**Condition 3: During event**")
    cond3_event = st.selectbox("Event", ["(any)", "GFC", "IBC", "COVID"], key="prof_evt")

    # Condition 4: Metric filter
    st.markdown("**Condition 4: Financial metric**")
    col_m, col_op, col_v = st.columns(3)
    with col_m:
        cond4_metric = st.selectbox("Metric", ["(none)", "leverage", "profitability", "tangibility", "firm_size"], key="prof_met")
    with col_op:
        cond4_op = st.selectbox("Operator", [">", "<", ">=", "<="], key="prof_op")
    with col_v:
        cond4_val = st.number_input("Value", value=0.0, step=0.1, key="prof_val")

    if st.button("Run Query", type="primary", key="prof_run"):
        # Start with all companies
        candidates = set()
        for n, d in G.nodes(data=True):
            if d.get("type") == "company":
                candidates.add(n)

        counts_by_step = [len(candidates)]

        # Condition 1: stage at year
        if cond1_stage != "(any)":
            filtered = set()
            for company_id in candidates:
                code = G.nodes[company_id].get("company_code")
                obs_id = f"obs:{code}:{cond1_year}"
                if G.has_node(obs_id):
                    stage = _get_obs_stage(G, obs_id)
                    if stage == cond1_stage:
                        filtered.add(company_id)
            candidates = filtered
        counts_by_step.append(len(candidates))

        # Condition 2: transition
        if cond2_from != "(any)" or cond2_to != "(any)":
            filtered = set()
            for company_id in candidates:
                for u, v, data in G.edges(company_id, data=True):
                    if data.get("relation") != "TRANSITION":
                        continue
                    yr = data.get("year", 0)
                    if yr < cond2_yr[0] or yr > cond2_yr[1]:
                        continue
                    if cond2_from != "(any)" and data.get("from_stage") != cond2_from:
                        continue
                    if cond2_to != "(any)" and data.get("to_stage") != cond2_to:
                        continue
                    filtered.add(company_id)
                    break
            candidates = filtered
        counts_by_step.append(len(candidates))

        # Condition 3: event
        if cond3_event != "(any)":
            filtered = set()
            event_id = f"event:{cond3_event}"
            for company_id in candidates:
                # Check if any observation of this company is during the event
                for neighbor in G.neighbors(company_id):
                    if G.nodes[neighbor].get("type") == "observation" and G.has_edge(neighbor, event_id):
                        filtered.add(company_id)
                        break
            candidates = filtered
        counts_by_step.append(len(candidates))

        # Condition 4: metric filter
        if cond4_metric != "(none)":
            import operator
            ops = {">": operator.gt, "<": operator.lt, ">=": operator.ge, "<=": operator.le}
            op_fn = ops[cond4_op]
            filtered = set()
            for company_id in candidates:
                for neighbor in G.neighbors(company_id):
                    nd = G.nodes[neighbor]
                    if nd.get("type") == "observation":
                        val = nd.get(cond4_metric)
                        if val is not None and op_fn(val, cond4_val):
                            filtered.add(company_id)
                            break
            candidates = filtered
        counts_by_step.append(len(candidates))

        # Show funnel
        st.divider()
        labels = ["All Companies", "After Stage Filter", "After Transition Filter",
                   "After Event Filter", "After Metric Filter"]
        fc1, fc2, fc3, fc4, fc5 = st.columns(5)
        for col, label, count in zip([fc1, fc2, fc3, fc4, fc5], labels, counts_by_step):
            col.metric(label, count)

        # Results
        if candidates:
            result_rows = []
            for company_id in sorted(candidates):
                nd = G.nodes[company_id]
                code = nd.get("company_code")
                # Get latest observation metrics
                obs_list = [(G.nodes[n].get("year"), n) for n in G.neighbors(company_id)
                            if G.nodes[n].get("type") == "observation"]
                obs_list.sort()
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
        else:
            st.warning("No companies match all conditions.")
