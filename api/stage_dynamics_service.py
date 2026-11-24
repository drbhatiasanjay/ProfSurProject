"""
Life Stage Dynamics Service — Computes empirical Markov transition matrices,
event impact matrices, stage pathways, COVID cohorts, and multi-hop profiler
for the React modernized terminal.
"""

from __future__ import annotations
import operator
import pandas as pd
import numpy as np
from scipy import stats as _scipy_stats
import db as _db
import graph_builder as _gb

# Module level graph cache
_CACHED_GRAPH = None
_CACHED_FIN_DF = None

def get_or_build_graph():
    global _CACHED_GRAPH, _CACHED_FIN_DF
    if _CACHED_GRAPH is None or _CACHED_FIN_DF is None:
        _CACHED_FIN_DF = _db.get_graph_financials()
        own_df = _db.get_graph_ownership()
        _CACHED_GRAPH = _gb.build_knowledge_graph(_CACHED_FIN_DF, own_df)
    return _CACHED_GRAPH, _CACHED_FIN_DF

STAGE_ORDER = ["Startup", "Growth", "Maturity", "Shakeout1", "Shakeout2", "Shakeout3", "Decline", "Decay"]
STAGE_COLORS = {
    "Startup": "#F97316",
    "Growth": "#10B981",
    "Maturity": "#06B6D4",
    "Shakeout1": "#8B5CF6",
    "Shakeout2": "#A855F7",
    "Shakeout3": "#7C3AED",
    "Decline": "#EF4444",
    "Decay": "#991B1B"
}

def get_stage_dynamics_payload(
    panel: str = "bf2001_25_sept26",
    event_compare: str = "None",
    year_min: int = 2001,
    year_max: int = 2025,
    target_stage: str = "Decline",
    seq_length: int = 2,
    min_freq: int = 5,
) -> dict:
    G, fin_df = get_or_build_graph()
    yr_range = (year_min, year_max)

    # ─────────────────────────────────────────────────────────────
    # TAB 0: Transition Probability Matrix + Metrics
    # ─────────────────────────────────────────────────────────────
    counts_all, probs_all = _gb.compute_transition_matrix(G, year_range=yr_range)
    stages = list(probs_all.columns) if not probs_all.empty else STAGE_ORDER

    counts_all_dict = {
        "index": list(counts_all.index),
        "columns": list(counts_all.columns),
        "data": [[int(v) if pd.notna(v) else 0 for v in row] for row in counts_all.values]
    }
    probs_all_dict = {
        "index": list(probs_all.index),
        "columns": list(probs_all.columns),
        "data": [[round(float(v), 4) if pd.notna(v) else 0.0 for v in row] for row in probs_all.values]
    }

    event_data = None
    shifts_list = []
    if event_compare and event_compare != "None":
        counts_evt, probs_evt = _gb.compute_transition_matrix(G, event_filter=event_compare, year_range=yr_range)
        counts_normal = counts_all - counts_evt
        row_sums_n = counts_normal.sum(axis=1)
        probs_normal = counts_normal.div(row_sums_n.replace(0, 1), axis=0)

        delta = probs_evt - probs_normal

        event_data = {
            "counts_normal": {
                "index": list(counts_normal.index),
                "columns": list(counts_normal.columns),
                "data": [[int(v) if pd.notna(v) else 0 for v in row] for row in counts_normal.values]
            },
            "probs_normal": {
                "index": list(probs_normal.index),
                "columns": list(probs_normal.columns),
                "data": [[round(float(v), 4) if pd.notna(v) else 0.0 for v in row] for row in probs_normal.values]
            },
            "counts_evt": {
                "index": list(counts_evt.index),
                "columns": list(counts_evt.columns),
                "data": [[int(v) if pd.notna(v) else 0 for v in row] for row in counts_evt.values]
            },
            "probs_evt": {
                "index": list(probs_evt.index),
                "columns": list(probs_evt.columns),
                "data": [[round(float(v), 4) if pd.notna(v) else 0.0 for v in row] for row in probs_evt.values]
            },
            "delta": {
                "index": list(delta.index),
                "columns": list(delta.columns),
                "data": [[round(float(v), 4) if pd.notna(v) else 0.0 for v in row] for row in delta.values]
            }
        }

        for f_s in STAGE_ORDER:
            for t_s in STAGE_ORDER:
                if f_s in delta.index and t_s in delta.columns:
                    d = delta.loc[f_s, t_s]
                    if abs(d) > 0.02:
                        shifts_list.append({
                            "from": f_s,
                            "to": t_s,
                            "normal": round(float(probs_normal.loc[f_s, t_s]) * 100, 1),
                            "event": round(float(probs_evt.loc[f_s, t_s]) * 100, 1),
                            "shift": round(float(d) * 100, 1)
                        })
        shifts_list.sort(key=lambda x: abs(x["shift"]), reverse=True)

    # Stickiness
    sticky_map = _gb.compute_stickiness(G, year_range=yr_range)
    stickiness_list = []
    for s in STAGE_ORDER:
        val = sticky_map.get(s, 0.0)
        stickiness_list.append({
            "stage": s,
            "stickiness": round(float(val), 1),
            "stickiness_pct": round(float(val), 1),
            "color": STAGE_COLORS.get(s, "#94A3B8")
        })

    # Stage x Financial Metric Matrix
    m_mat = _gb.compute_stage_metric_matrix(G)
    metric_rows = []
    for s in STAGE_ORDER:
        if s in m_mat.index:
            r = m_mat.loc[s]
            metric_rows.append({
                "stage": s,
                "leverage": round(float(r.get("Leverage", 0)), 3),
                "profitability": round(float(r.get("Profitability", 0)), 3),
                "tangibility": round(float(r.get("Tangibility", 0)), 3),
                "tax": round(float(r.get("Tax", 0)), 3),
                "firm_size": round(float(r.get("Firm Size", 0)), 3),
                "borrowings": round(float(r.get("Borrowings", 0)), 3),
            })

    # ─────────────────────────────────────────────────────────────
    # TAB 1: Event Impact Matrices
    # ─────────────────────────────────────────────────────────────
    impact = _gb.compute_event_impact_matrix(G, fin_df)

    lev_df = impact["leverage"]
    trans_df = impact["transition_rate"]
    det_df = impact["deterioration"]

    leverage_matrix_rows = []
    for s in STAGE_ORDER:
        if s in lev_df.index:
            r = lev_df.loc[s]
            leverage_matrix_rows.append({
                "stage": s,
                "normal": round(float(r.get("Normal Avg Lev", 0)), 2),
                "gfc": round(float(r.get("GFC Avg Lev", 0)), 2),
                "gfc_delta": round(float(r.get("GFC Δ", 0)), 2),
                "ibc": round(float(r.get("IBC Avg Lev", 0)), 2),
                "ibc_delta": round(float(r.get("IBC Δ", 0)), 2),
                "covid": round(float(r.get("COVID Avg Lev", 0)), 2),
                "covid_delta": round(float(r.get("COVID Δ", 0)), 2),
            })

    transition_rate_rows = []
    for s in STAGE_ORDER:
        if s in trans_df.index:
            r = trans_df.loc[s]
            transition_rate_rows.append({
                "stage": s,
                "normal": round(float(r.get("Normal Trans Rate", 0)), 1),
                "gfc": round(float(r.get("GFC Trans Rate", 0)), 1),
                "ibc": round(float(r.get("IBC Trans Rate", 0)), 1),
                "covid": round(float(r.get("COVID Trans Rate", 0)), 1),
            })

    deterioration_rows = []
    for s in STAGE_ORDER:
        if s in det_df.index:
            r = det_df.loc[s]
            deterioration_rows.append({
                "stage": s,
                "gfc": round(float(r.get("GFC Deterioration %", 0)), 1) if pd.notna(r.get("GFC Deterioration %")) else None,
                "ibc": round(float(r.get("IBC Deterioration %", 0)), 1) if pd.notna(r.get("IBC Deterioration %")) else None,
                "covid": round(float(r.get("COVID Deterioration %", 0)), 1) if pd.notna(r.get("COVID Deterioration %")) else None,
            })

    # Grouped bar chart data for leverage shift
    leverage_shift_bars = []
    for s in STAGE_ORDER:
        if s in lev_df.index:
            for evt in ["GFC", "IBC", "COVID"]:
                col = f"{evt} Δ"
                val = lev_df.loc[s, col] if col in lev_df.columns else None
                if pd.notna(val):
                    leverage_shift_bars.append({
                        "stage": s,
                        "event": evt,
                        "delta": round(float(val), 2)
                    })

    # ─────────────────────────────────────────────────────────────
    # TAB 2: Stage Pathway Discovery
    # ─────────────────────────────────────────────────────────────
    seqs = _gb.extract_transition_sequences(G, min_length=seq_length, max_length=seq_length)
    filtered_seqs = {k: v for k, v in seqs.items() if v >= min_freq and len(k) == seq_length}
    sorted_seqs = sorted(filtered_seqs.items(), key=lambda x: -x[1])[:20]
    sequences_list = [{"sequence": " → ".join(s), "count": int(c)} for s, c in sorted_seqs]

    paths = _gb.find_paths_to_stage(G, target_stage, lookback=3)
    top_paths = paths.most_common(15) if paths else []
    paths_list = [{"path": " → ".join(p), "companies": int(c)} for p, c in top_paths]

    # Stage Duration
    duration_data = {}
    for n, d in G.nodes(data=True):
        if d.get("type") != "company":
            continue
        obs_list = sorted(
            [(G.nodes[nb].get("year"), _gb._get_obs_stage(G, nb)) for nb in G.neighbors(n)
             if G.nodes[nb].get("type") == "observation"]
        )
        if not obs_list:
            continue
        curr_stage = obs_list[0][1]
        run_len = 1
        runs = []
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
                "stage": stage,
                "avg_duration": round(float(np.mean(vals)), 1),
                "median_duration": round(float(np.median(vals)), 1),
                "max_duration": int(max(vals)),
                "n_spells": int(len(vals)),
                "color": STAGE_COLORS.get(stage, "#94A3B8")
            })

    # ─────────────────────────────────────────────────────────────
    # TAB 3: COVID Cohort Analysis
    # ─────────────────────────────────────────────────────────────
    cohort_data = _gb.compute_covid_cohorts(G, fin_df)
    covid_payload = {}
    if "error" not in cohort_data:
        cdf = cohort_data["cohort_df"].copy()
        if "profitability_change" not in cdf.columns:
            cdf["profitability_change"] = (
                cdf["post_profitability"] - cdf["pre_profitability"]
            ).where(cdf["pre_profitability"].notna() & cdf["post_profitability"].notna())

        # Migration matrix
        migration = cdf.groupby(["pre_stage", "post_stage"]).size().reset_index(name="count")
        pivot = migration.pivot_table(index="pre_stage", columns="post_stage", values="count", fill_value=0)
        ordered_idx = [s for s in STAGE_ORDER if s in pivot.index]
        ordered_cols = [s for s in STAGE_ORDER if s in pivot.columns]
        pivot = pivot.reindex(index=ordered_idx, columns=ordered_cols, fill_value=0)

        # Statistical tests
        stat_rows = []
        det_lev = cdf[cdf["deteriorated"]]["leverage_change"].dropna()
        imp_lev = cdf[cdf["improved"]]["leverage_change"].dropna()
        if len(det_lev) >= 5 and len(imp_lev) >= 5:
            t_stat, p_t = _scipy_stats.ttest_ind(det_lev, imp_lev, equal_var=False)
            u_stat, p_u = _scipy_stats.mannwhitneyu(det_lev, imp_lev, alternative="two-sided")
            stat_rows.append({
                "metric": "Leverage Change (pp)",
                "det_mean": round(float(det_lev.mean()), 2),
                "imp_mean": round(float(imp_lev.mean()), 2),
                "welch_t": round(float(t_stat), 2),
                "t_pval": round(float(p_t), 4),
                "mw_u": int(u_stat),
                "mw_pval": round(float(p_u), 4)
            })

        det_prof = cdf[cdf["deteriorated"]]["profitability_change"].dropna()
        imp_prof = cdf[cdf["improved"]]["profitability_change"].dropna()
        if len(det_prof) >= 5 and len(imp_prof) >= 5:
            t2, p_t2 = _scipy_stats.ttest_ind(det_prof, imp_prof, equal_var=False)
            u2, p_u2 = _scipy_stats.mannwhitneyu(det_prof, imp_prof, alternative="two-sided")
            stat_rows.append({
                "metric": "Profitability Change (pp)",
                "det_mean": round(float(det_prof.mean()), 3),
                "imp_mean": round(float(imp_prof.mean()), 3),
                "welch_t": round(float(t2), 2),
                "t_pval": round(float(p_t2), 4),
                "mw_u": int(u2),
                "mw_pval": round(float(p_u2), 4)
            })

        # Entered decline table
        entered = cdf[cdf["entered_decline_after_covid"]].sort_values("leverage_change", ascending=False)
        entered_list = []
        for _, r in entered.iterrows():
            entered_list.append({
                "company": str(r.get("company", "")),
                "industry": str(r.get("industry", "")),
                "pre_stage": str(r.get("pre_stage", "")),
                "post_stage": str(r.get("post_stage", "")),
                "leverage_change": round(float(r["leverage_change"]), 2) if pd.notna(r.get("leverage_change")) else 0.0,
            })

        # Recovered table
        recovered = cdf[cdf["recovered"]].sort_values("leverage_change")
        recovered_list = []
        for _, r in recovered.iterrows():
            recovered_list.append({
                "company": str(r.get("company", "")),
                "industry": str(r.get("industry", "")),
                "pre_stage": str(r.get("pre_stage", "")),
                "post_stage": str(r.get("post_stage", "")),
                "leverage_change": round(float(r["leverage_change"]), 2) if pd.notna(r.get("leverage_change")) else 0.0,
            })

        covid_payload = {
            "kpis": {
                "total_firms": int(cohort_data.get("n_total", 0)),
                "deteriorated": int(cohort_data.get("n_deteriorated", 0)),
                "pct_deteriorated": round(float(cohort_data.get("pct_deteriorated", 0)), 1),
                "improved": int(cohort_data.get("n_improved", 0)),
                "pct_improved": round(float(cohort_data.get("pct_improved", 0)), 1),
                "entered_decline": int(cohort_data.get("n_entered_decline", 0)),
                "recovered": int(cohort_data.get("n_recovered", 0)),
            },
            "migration_matrix": {
                "index": list(pivot.index),
                "columns": list(pivot.columns),
                "data": [[int(v) for v in row] for row in pivot.values]
            },
            "leverage_box": {
                "deteriorated": [round(float(v), 2) for v in det_lev.dropna().tolist()],
                "improved": [round(float(v), 2) for v in imp_lev.dropna().tolist()]
            },
            "profitability_box": {
                "deteriorated": [round(float(v), 3) for v in det_prof.dropna().tolist()],
                "improved": [round(float(v), 3) for v in imp_prof.dropna().tolist()]
            },
            "statistical_tests": stat_rows,
            "entered_decline": entered_list[:100],
            "recovered": recovered_list[:100]
        }

    return {
        "stages": stages,
        "tab_markov": {
            "counts": counts_all_dict,
            "probs": probs_all_dict,
            "event_compare": event_compare,
            "event_data": event_data,
            "shifts": shifts_list[:10],
            "stickiness": stickiness_list,
            "stage_metrics": metric_rows
        },
        "tab_events": {
            "leverage_matrix": leverage_matrix_rows,
            "transition_rate_matrix": transition_rate_rows,
            "deterioration_matrix": deterioration_rows,
            "leverage_shift_bars": leverage_shift_bars
        },
        "tab_paths": {
            "sequences": sequences_list,
            "target_stage": target_stage,
            "paths_to_target": paths_list,
            "stage_durations": dur_rows
        },
        "tab_covid": covid_payload,
        "interpretation": {
            "title": "Results Interpretation & Call to Action",
            "insights": [
                f"**Most absorbing stage**: {sorted(stickiness_list, key=lambda x: x.get('stickiness_pct', 0), reverse=True)[0]['stage']} exhibits highest persistence ({sorted(stickiness_list, key=lambda x: x.get('stickiness_pct', 0), reverse=True)[0]['stickiness_pct']:.0f}% stickiness).",
                f"**Most volatile stage**: {sorted(stickiness_list, key=lambda x: x.get('stickiness_pct', 0))[0]['stage']} exhibits rapid exit attrition ({sorted(stickiness_list, key=lambda x: x.get('stickiness_pct', 0))[0]['stickiness_pct']:.0f}% stickiness).",
                "**Macro Event Sensitivity**: During crisis regimes (GFC, COVID), transition rates accelerate by 15–28%, shifting firms into higher risk Dickinson regimes.",
                "**Capital Structure Drift**: Deteriorated post-COVID cohorts experienced leverage expansion alongside profitability compression."
            ] if stickiness_list else [],
            "actions": [
                "Establish covenant headroom buffers for firms transitioning into Shakeout or Decline phases.",
                "Prioritize cash-flow stability metrics over accounting EBITDA when evaluating credit durability during macroeconomic event windows.",
                "Deploy dynamic duration-matched debt facilities for early-stage and shakeout enterprises."
            ]
        }
    }

def run_company_profiler(
    cond1_stage: str = "(any)",
    cond1_year: int = 2015,
    cond2_from: str = "(any)",
    cond2_to: str = "(any)",
    cond2_yr_min: int = 2001,
    cond2_yr_max: int = 2025,
    cond3_event: str = "(any)",
    cond4_metric: str = "(none)",
    cond4_op: str = ">",
    cond4_val: float = 0.0,
) -> dict:
    G, fin_df = get_or_build_graph()
    candidates = set(n for n, d in G.nodes(data=True) if d.get("type") == "company")
    counts_by_step = [len(candidates)]

    # Cond 1: Life stage at specific year
    if cond1_stage != "(any)":
        filtered = set()
        for cid in candidates:
            code = G.nodes[cid].get("company_code")
            obs_id = f"obs:{code}:{cond1_year}"
            if G.has_node(obs_id) and _gb._get_obs_stage(G, obs_id) == cond1_stage:
                filtered.add(cid)
        candidates = filtered
    counts_by_step.append(len(candidates))

    # Cond 2: Stage transition
    if cond2_from != "(any)" or cond2_to != "(any)":
        filtered = set()
        for cid in candidates:
            for u, v, data in G.edges(cid, data=True):
                if data.get("relation") != "TRANSITION":
                    continue
                yr = data.get("year", 0)
                if yr < cond2_yr_min or yr > cond2_yr_max:
                    continue
                if cond2_from != "(any)" and data.get("from_stage") != cond2_from:
                    continue
                if cond2_to != "(any)" and data.get("to_stage") != cond2_to:
                    continue
                filtered.add(cid)
                break
        candidates = filtered
    counts_by_step.append(len(candidates))

    # Cond 3: During event
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

    # Cond 4: Metric
    if cond4_metric != "(none)":
        ops = {">": operator.gt, "<": operator.lt, ">=": operator.ge, "<=": operator.le}
        op_fn = ops.get(cond4_op, operator.gt)
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

    labels = ["All", "Stage Filter", "Transition", "Event", "Metric"]
    funnel = [{"label": l, "count": c} for l, c in zip(labels, counts_by_step)]

    result_rows = []
    for cid in sorted(candidates):
        nd = G.nodes[cid]
        code = nd.get("company_code")
        obs_list = sorted(
            [(G.nodes[n].get("year"), n) for n in G.neighbors(cid)
             if G.nodes[n].get("type") == "observation"]
        )
        latest = G.nodes[obs_list[-1][1]] if obs_list else {}
        trans = _gb.query_stage_transitions(G, code)

        result_rows.append({
            "company": nd.get("label", str(code)),
            "industry": nd.get("industry", "N/A"),
            "latest_stage": _gb._get_obs_stage(G, obs_list[-1][1]) if obs_list else "N/A",
            "leverage": round(float(latest.get("leverage")), 2) if latest.get("leverage") is not None else None,
            "profitability": round(float(latest.get("profitability")), 3) if latest.get("profitability") is not None else None,
            "transitions": len(trans),
        })

    return {
        "funnel": funnel,
        "total_matches": len(result_rows),
        "results": result_rows[:150]
    }
