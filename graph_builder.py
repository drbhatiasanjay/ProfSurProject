"""
Knowledge graph construction from SQLite data.
Builds a networkx graph with typed nodes and relationship edges.
"""

import networkx as nx
import numpy as np
import pandas as pd


EVENT_PERIODS = {
    "GFC": {"col": "gfc", "years": (2008, 2009), "color": "#EF4444"},
    "IBC": {"col": "ibc_2016", "years": (2016, 2020), "color": "#6366F1"},
    "COVID": {"col": "covid_dummy", "years": (2020, 2021), "color": "#F97316"},
}


def build_knowledge_graph(financials_df, ownership_df=None):
    """
    Build a knowledge graph from financial panel data.

    Args:
        financials_df: DataFrame with columns: company_code, company_name,
            industry_group, year, life_stage, leverage, profitability, etc.
        ownership_df: Optional DataFrame with promoter_share, non_promoters.

    Returns:
        networkx.MultiGraph with typed nodes and labeled edges.
    """
    G = nx.MultiGraph()

    # ── 1. Add LifeStage nodes ──
    stages = financials_df["life_stage"].dropna().unique()
    for stage in stages:
        G.add_node(f"stage:{stage}", type="life_stage", label=stage,
                   color=_stage_color(stage))

    # ── 2. Add IndustryGroup nodes ──
    industries = financials_df["industry_group"].dropna().unique()
    for ind in industries:
        G.add_node(f"industry:{ind}", type="industry", label=ind,
                   color="#374151")

    # ── 3. Add EventPeriod nodes ──
    for event_name, meta in EVENT_PERIODS.items():
        col = meta["col"]
        if col in financials_df.columns and financials_df[col].sum() > 0:
            G.add_node(f"event:{event_name}", type="event", label=event_name,
                       years=meta["years"], color=meta["color"])

    # ── 4. Add Company nodes + edges ──
    companies = financials_df.groupby("company_code").first().reset_index()
    for _, row in companies.iterrows():
        code = int(row["company_code"])
        node_id = f"company:{code}"
        G.add_node(node_id, type="company", label=row["company_name"],
                   company_code=code, industry=row.get("industry_group", ""),
                   color="#0D9488")

        # Company -> Industry
        if pd.notna(row.get("industry_group")):
            G.add_edge(node_id, f"industry:{row['industry_group']}",
                       relation="IN_INDUSTRY")

    # ── 5. Add Observation nodes + edges ──
    for _, row in financials_df.iterrows():
        code = int(row["company_code"])
        year = int(row["year"])
        obs_id = f"obs:{code}:{year}"
        company_id = f"company:{code}"

        G.add_node(obs_id, type="observation", label=f"{year}",
                   year=year, company_code=code,
                   leverage=row.get("leverage"),
                   profitability=row.get("profitability"),
                   tangibility=row.get("tangibility"),
                   tax=row.get("tax"),
                   firm_size=row.get("firm_size"),
                   borrowings=row.get("borrowings"),
                   color="#94A3B8")

        # Company -> Observation
        G.add_edge(company_id, obs_id, relation="HAS_OBSERVATION", year=year)

        # Observation -> LifeStage
        if pd.notna(row.get("life_stage")):
            G.add_edge(obs_id, f"stage:{row['life_stage']}",
                       relation="AT_STAGE", year=year)

        # Observation -> EventPeriod
        for event_name, meta in EVENT_PERIODS.items():
            col = meta["col"]
            if col in row.index and row[col] == 1:
                G.add_edge(obs_id, f"event:{event_name}",
                           relation="DURING_EVENT", year=year)

        # Company -> LifeStage (direct shortcut)
        if pd.notna(row.get("life_stage")):
            stage_id = f"stage:{row['life_stage']}"
            # Check if shortcut already exists
            existing = [
                k for u, v, k, d in G.edges(company_id, keys=True, data=True)
                if v == stage_id and d.get("relation") == "AT_STAGE"
            ]
            if not existing:
                G.add_edge(company_id, stage_id,
                           relation="AT_STAGE", year=year)

    # ── 6. Merge ownership data ──
    if ownership_df is not None and not ownership_df.empty:
        for _, row in ownership_df.iterrows():
            obs_id = f"obs:{int(row['company_code'])}:{int(row['year'])}"
            if G.has_node(obs_id):
                G.nodes[obs_id]["promoter_share"] = row.get("promoter_share")
                G.nodes[obs_id]["non_promoters"] = row.get("non_promoters")

    # ── 7. Add lifecycle transition edges ──
    for code, group in financials_df.groupby("company_code"):
        sorted_obs = group.sort_values("year")
        prev_stage = None
        for _, row in sorted_obs.iterrows():
            curr_stage = row.get("life_stage")
            curr_year = int(row["year"])
            if prev_stage and curr_stage and prev_stage != curr_stage:
                company_id = f"company:{int(code)}"
                G.add_edge(
                    company_id, f"stage:{curr_stage}",
                    relation="TRANSITION",
                    from_stage=prev_stage,
                    to_stage=curr_stage,
                    year=curr_year,
                )
            prev_stage = curr_stage

    return G


def get_node_details(G, node_id):
    """Return full attribute dict for a node."""
    if node_id not in G:
        return None
    return dict(G.nodes[node_id])


def get_neighbors(G, node_id, relation=None):
    """
    Get neighbor nodes with their attributes.

    Args:
        G: The knowledge graph.
        node_id: Source node ID.
        relation: Optional filter by edge relation type.

    Returns:
        List of dicts with node attributes + edge_relation.
    """
    if node_id not in G:
        return []
    results = []
    seen = set()
    for u, v, data in G.edges(node_id, data=True):
        neighbor = v if v != node_id else u
        if relation and data.get("relation") != relation:
            continue
        if neighbor in seen:
            continue
        seen.add(neighbor)
        node_data = dict(G.nodes[neighbor])
        node_data["node_id"] = neighbor
        node_data["edge_relation"] = data.get("relation", "")
        results.append(node_data)
    return results


def get_subgraph(G, center_node, depth=1):
    """
    Extract a subgraph around a center node up to N hops.

    Args:
        G: Full knowledge graph.
        center_node: Node ID to center on.
        depth: Number of hops outward.

    Returns:
        networkx.MultiGraph subgraph.
    """
    nodes = {center_node}
    frontier = {center_node}
    for _ in range(depth):
        next_frontier = set()
        for node in frontier:
            for neighbor in G.neighbors(node):
                next_frontier.add(neighbor)
        nodes.update(next_frontier)
        frontier = next_frontier
    return G.subgraph(nodes).copy()


def query_companies_by_stage_and_event(G, stage_name, event_name=None):
    """
    Traverse: find companies at a given stage, optionally during an event.

    Returns list of dicts with company_id, company_name, year, leverage, profitability.
    """
    stage_id = f"stage:{stage_name}"
    if stage_id not in G:
        return []

    results = []
    for neighbor in G.neighbors(stage_id):
        obs = G.nodes[neighbor]
        if obs.get("type") != "observation":
            continue

        # Check event filter
        if event_name:
            event_id = f"event:{event_name}"
            if not G.has_edge(neighbor, event_id):
                continue

        # Find parent company
        for obs_neighbor in G.neighbors(neighbor):
            n = G.nodes[obs_neighbor]
            if n.get("type") == "company":
                results.append({
                    "company_id": obs_neighbor,
                    "company_name": n["label"],
                    "year": obs.get("year"),
                    "leverage": obs.get("leverage"),
                    "profitability": obs.get("profitability"),
                })
    return results


def query_stage_transitions(G, company_code):
    """
    Find life stage transitions for a company across years.

    Returns list of dicts: {year, from_stage, to_stage}.
    """
    company_id = f"company:{company_code}"
    if company_id not in G:
        return []

    transitions = []
    for u, v, data in G.edges(company_id, data=True):
        if data.get("relation") == "TRANSITION":
            transitions.append({
                "year": data.get("year"),
                "from_stage": data.get("from_stage"),
                "to_stage": data.get("to_stage"),
            })

    transitions.sort(key=lambda x: x["year"])
    return transitions


def get_graph_stats(G):
    """Return summary statistics of the knowledge graph."""
    type_counts = {}
    for _, data in G.nodes(data=True):
        t = data.get("type", "unknown")
        type_counts[t] = type_counts.get(t, 0) + 1

    relation_counts = {}
    for _, _, data in G.edges(data=True):
        r = data.get("relation", "unknown")
        relation_counts[r] = relation_counts.get(r, 0) + 1

    return {
        "total_nodes": G.number_of_nodes(),
        "total_edges": G.number_of_edges(),
        "node_types": type_counts,
        "edge_types": relation_counts,
    }


# ── Transition analytics (graph-powered) ──

def compute_transition_matrix(G, event_filter=None, year_range=None):
    """
    Build an 8×8 stage transition probability matrix from TRANSITION edges.

    If event_filter is set, only count transitions where the company's observation
    at the transition year has a DURING_EVENT edge to that event (2-hop traversal).

    Returns (counts_df, prob_df) — both 8×8 DataFrames indexed by STAGE_ORDER.
    """
    from helpers import STAGE_ORDER
    from collections import Counter

    counts = Counter()

    for u, v, data in G.edges(data=True):
        if data.get("relation") != "TRANSITION":
            continue

        from_s = data.get("from_stage")
        to_s = data.get("to_stage")
        year = data.get("year")

        if not from_s or not to_s:
            continue

        # Year range filter
        if year_range and (year < year_range[0] or year > year_range[1]):
            continue

        # Event filter: check if the observation at (company, year) is during the event
        if event_filter:
            # u is the company node, year is the transition year
            company_id = u if G.nodes[u].get("type") == "company" else v
            code = G.nodes[company_id].get("company_code")
            obs_id = f"obs:{code}:{year}"
            event_id = f"event:{event_filter}"
            if not G.has_node(obs_id) or not G.has_edge(obs_id, event_id):
                continue

        counts[(from_s, to_s)] += 1

    # Build DataFrame
    counts_df = pd.DataFrame(0, index=STAGE_ORDER, columns=STAGE_ORDER)
    for (f, t), c in counts.items():
        if f in STAGE_ORDER and t in STAGE_ORDER:
            counts_df.loc[f, t] = c

    # Normalize to probabilities
    row_sums = counts_df.sum(axis=1)
    prob_df = counts_df.div(row_sums.replace(0, 1), axis=0)

    return counts_df, prob_df


def compute_stickiness(G, year_range=None):
    """
    For each stage, compute % of firm-years where the company stayed in the same
    stage the following year. Walks consecutive HAS_OBSERVATION edges per company.

    Returns dict {stage_name: stickiness_pct (0-100)}.
    """
    from helpers import STAGE_ORDER
    from collections import defaultdict

    stayed = defaultdict(int)
    total = defaultdict(int)

    # Group observations by company
    company_nodes = [n for n, d in G.nodes(data=True) if d.get("type") == "company"]

    for company_id in company_nodes:
        # Get all observation neighbors sorted by year
        obs_list = []
        for neighbor in G.neighbors(company_id):
            nd = G.nodes[neighbor]
            if nd.get("type") == "observation":
                obs_list.append((nd.get("year"), neighbor))
        obs_list.sort()

        for i in range(len(obs_list) - 1):
            yr1, obs1 = obs_list[i]
            yr2, obs2 = obs_list[i + 1]

            if year_range and (yr1 < year_range[0] or yr1 > year_range[1]):
                continue

            # Find stage of each observation
            stage1 = _get_obs_stage(G, obs1)
            stage2 = _get_obs_stage(G, obs2)

            if stage1 and stage2:
                total[stage1] += 1
                if stage1 == stage2:
                    stayed[stage1] += 1

    result = {}
    for stage in STAGE_ORDER:
        if total[stage] > 0:
            result[stage] = round(stayed[stage] / total[stage] * 100, 1)
        else:
            result[stage] = 0.0
    return result


def _get_obs_stage(G, obs_id):
    """Get the life stage of an observation node via AT_STAGE edge."""
    for neighbor in G.neighbors(obs_id):
        nd = G.nodes[neighbor]
        if nd.get("type") == "life_stage":
            return nd.get("label")
    return None


def find_event_triggered_transitions(G, event_name):
    """
    Multi-hop traversal: find firms that changed life stage during an event.

    Path: Event → DURING_EVENT → Observations → parent Company →
          adjacent Observations (pre/post) → compare stages.

    Returns list of dicts with company info and pre/during/post metrics.
    """
    event_id = f"event:{event_name}"
    if event_id not in G:
        return []

    event_years = EVENT_PERIODS[event_name]["years"]
    yr_start, yr_end = event_years

    # Collect all observations during event, grouped by company
    company_event_obs = {}  # company_code -> [(year, obs_id)]
    for neighbor in G.neighbors(event_id):
        nd = G.nodes[neighbor]
        if nd.get("type") != "observation":
            continue
        code = nd.get("company_code")
        year = nd.get("year")
        if code not in company_event_obs:
            company_event_obs[code] = []
        company_event_obs[code].append((year, neighbor))

    results = []
    for code, event_obs_list in company_event_obs.items():
        event_obs_list.sort()
        company_id = f"company:{code}"
        if company_id not in G:
            continue

        company_data = G.nodes[company_id]

        # Get ALL observations for this company, sorted by year
        all_obs = []
        for neighbor in G.neighbors(company_id):
            nd = G.nodes[neighbor]
            if nd.get("type") == "observation":
                all_obs.append((nd.get("year"), neighbor))
        all_obs.sort()

        # Find pre-event, during-event, post-event observations
        pre_obs = [(y, o) for y, o in all_obs if y < yr_start]
        during_obs = [(y, o) for y, o in all_obs if yr_start <= y <= yr_end]
        post_obs = [(y, o) for y, o in all_obs if y > yr_end]

        if not during_obs:
            continue

        # Get stages
        pre_stage = _get_obs_stage(G, pre_obs[-1][1]) if pre_obs else None
        during_stages = [_get_obs_stage(G, o) for _, o in during_obs]
        during_stages = [s for s in during_stages if s]
        post_stage = _get_obs_stage(G, post_obs[0][1]) if post_obs else None

        # Check if any stage change happened during the event
        event_stage = during_stages[-1] if during_stages else None
        first_during = during_stages[0] if during_stages else None

        had_transition = (pre_stage and first_during and pre_stage != first_during) or \
                         (event_stage and post_stage and event_stage != post_stage) or \
                         len(set(during_stages)) > 1

        # Get financial metrics
        pre_lev = G.nodes[pre_obs[-1][1]].get("leverage") if pre_obs else None
        during_lev = G.nodes[during_obs[-1][1]].get("leverage")
        post_lev = G.nodes[post_obs[0][1]].get("leverage") if post_obs else None

        pre_prof = G.nodes[pre_obs[-1][1]].get("profitability") if pre_obs else None
        during_prof = G.nodes[during_obs[-1][1]].get("profitability")
        post_prof = G.nodes[post_obs[0][1]].get("profitability") if post_obs else None

        results.append({
            "company_name": company_data.get("label"),
            "industry": company_data.get("industry"),
            "pre_stage": pre_stage,
            "event_stage": event_stage,
            "post_stage": post_stage,
            "had_transition": had_transition,
            "pre_leverage": pre_lev,
            "event_leverage": during_lev,
            "post_leverage": post_lev,
            "pre_profitability": pre_prof,
            "event_profitability": during_prof,
            "post_profitability": post_prof,
            "firm_size": G.nodes[during_obs[-1][1]].get("firm_size"),
        })

    return results


def compute_event_impact_matrix(G, fin_df):
    """
    Build Stage × Event matrices showing:
    1. Avg leverage during each event vs normal, by stage
    2. Transition rate (% of firms changing stage) during event vs normal, per stage
    3. Deterioration rate per stage per event

    Returns dict of DataFrames.
    """
    from helpers import STAGE_ORDER, STAGE_RANK
    from collections import defaultdict

    events = ["GFC", "IBC", "COVID"]

    # --- Leverage impact matrix ---
    lev_rows = []
    for stage in STAGE_ORDER:
        row = {"Stage": stage}
        stage_data = fin_df[fin_df["life_stage"] == stage]
        row["Normal Avg Lev"] = stage_data["leverage"].mean()
        for evt in events:
            col = EVENT_PERIODS[evt]["col"]
            evt_data = stage_data[stage_data[col] == 1]
            row[f"{evt} Avg Lev"] = evt_data["leverage"].mean() if not evt_data.empty else None
            normal_lev = stage_data[stage_data[col] != 1]["leverage"].mean()
            row[f"{evt} Δ"] = (row[f"{evt} Avg Lev"] - normal_lev) if row[f"{evt} Avg Lev"] is not None and pd.notna(normal_lev) else None
        lev_rows.append(row)
    lev_df = pd.DataFrame(lev_rows).set_index("Stage")

    # --- Transition rate matrix: % of firms that changed stage during event year ---
    trans_rate_rows = []
    for stage in STAGE_ORDER:
        row = {"Stage": stage}
        # Normal transition rate for this stage
        all_trans_from = sum(1 for _, _, d in G.edges(data=True)
                            if d.get("relation") == "TRANSITION" and d.get("from_stage") == stage)
        # Total firm-years at this stage
        total_at_stage = len(fin_df[fin_df["life_stage"] == stage])
        row["Normal Trans Rate"] = all_trans_from / max(total_at_stage, 1) * 100

        for evt in events:
            col = EVENT_PERIODS[evt]["col"]
            evt_at_stage = fin_df[(fin_df["life_stage"] == stage) & (fin_df[col] == 1)]
            evt_total = len(evt_at_stage)

            # Count transitions from this stage during event years
            evt_years = set(evt_at_stage["year"].unique())
            evt_trans = sum(1 for _, _, d in G.edges(data=True)
                           if d.get("relation") == "TRANSITION"
                           and d.get("from_stage") == stage
                           and d.get("year") in evt_years)
            row[f"{evt} Trans Rate"] = evt_trans / max(evt_total, 1) * 100
        trans_rate_rows.append(row)
    trans_rate_df = pd.DataFrame(trans_rate_rows).set_index("Stage")

    # --- Deterioration matrix: of those who transitioned, % that moved to worse stage ---
    det_rows = []
    for stage in STAGE_ORDER:
        row = {"Stage": stage}
        stage_rank = STAGE_RANK.get(stage, 0)

        for evt in events:
            col = EVENT_PERIODS[evt]["col"]
            evt_at_stage = fin_df[(fin_df["life_stage"] == stage) & (fin_df[col] == 1)]
            evt_years = set(evt_at_stage["year"].unique())

            trans_during = [(d.get("to_stage"), d.get("year")) for _, _, d in G.edges(data=True)
                           if d.get("relation") == "TRANSITION"
                           and d.get("from_stage") == stage
                           and d.get("year") in evt_years]
            n_trans = len(trans_during)
            n_worse = sum(1 for to_s, _ in trans_during if STAGE_RANK.get(to_s, 0) > stage_rank)
            row[f"{evt} Deterioration %"] = n_worse / max(n_trans, 1) * 100 if n_trans > 0 else None
        det_rows.append(row)
    det_df = pd.DataFrame(det_rows).set_index("Stage")

    return {"leverage": lev_df, "transition_rate": trans_rate_df, "deterioration": det_df}


def compute_stage_metric_matrix(G):
    """
    Build Stage × Metric matrix: average of each financial metric by life stage.
    Returns DataFrame indexed by stage, columns = metrics.
    """
    from helpers import STAGE_ORDER
    from collections import defaultdict

    metrics = ["leverage", "profitability", "tangibility", "tax", "firm_size", "borrowings"]
    accum = defaultdict(lambda: defaultdict(list))

    for n, d in G.nodes(data=True):
        if d.get("type") != "observation":
            continue
        stage = _get_obs_stage(G, n)
        if not stage:
            continue
        for m in metrics:
            val = d.get(m)
            if val is not None and not pd.isna(val):
                accum[stage][m].append(val)

    rows = []
    for stage in STAGE_ORDER:
        row = {"Stage": stage}
        for m in metrics:
            vals = accum[stage].get(m, [])
            row[m.replace("_", " ").title()] = np.mean(vals) if vals else None
        rows.append(row)

    return pd.DataFrame(rows).set_index("Stage")


def compute_covid_cohorts(G, fin_df):
    """
    Identify and compare post-COVID cohorts:
    1. Firms already in Decline/Decay BEFORE COVID (pre-2020)
    2. Firms that entered Decline/Decay AFTER COVID (2022+)
    3. Resilient firms: improved stage post-COVID vs deteriorated

    Returns dict with cohort DataFrames and comparison stats.
    """
    from helpers import STAGE_RANK

    decline_stages = {"Decline", "Decay", "Shakeout1", "Shakeout2", "Shakeout3"}

    # Pre-COVID stage (2019) and post-COVID stage (latest available, 2022+)
    company_nodes = [n for n, d in G.nodes(data=True) if d.get("type") == "company"]

    rows = []
    for cid in company_nodes:
        nd = G.nodes[cid]
        code = nd.get("company_code")

        obs_list = sorted(
            [(G.nodes[nb].get("year"), nb) for nb in G.neighbors(cid)
             if G.nodes[nb].get("type") == "observation"],
        )
        if not obs_list:
            continue

        # Find pre-COVID (2019) and post-COVID (2022 or later) observations
        pre_covid_obs = [(y, o) for y, o in obs_list if y == 2019]
        post_covid_obs = [(y, o) for y, o in obs_list if y >= 2022]

        if not pre_covid_obs or not post_covid_obs:
            continue

        pre_year, pre_oid = pre_covid_obs[0]
        post_year, post_oid = post_covid_obs[-1]  # latest available

        pre_stage = _get_obs_stage(G, pre_oid)
        post_stage = _get_obs_stage(G, post_oid)
        pre_lev = G.nodes[pre_oid].get("leverage")
        post_lev = G.nodes[post_oid].get("leverage")
        pre_prof = G.nodes[pre_oid].get("profitability")
        post_prof = G.nodes[post_oid].get("profitability")

        if not pre_stage or not post_stage:
            continue

        pre_rank = STAGE_RANK.get(pre_stage, 0)
        post_rank = STAGE_RANK.get(post_stage, 0)

        # Classify
        was_declining = pre_stage in decline_stages
        now_declining = post_stage in decline_stages
        entered_decline_after = not was_declining and now_declining
        recovered = was_declining and not now_declining
        deteriorated = post_rank > pre_rank
        improved = post_rank < pre_rank

        rows.append({
            "company": nd.get("label"),
            "industry": nd.get("industry"),
            "pre_stage": pre_stage,
            "post_stage": post_stage,
            "pre_rank": pre_rank,
            "post_rank": post_rank,
            "pre_leverage": pre_lev,
            "post_leverage": post_lev,
            "leverage_change": (post_lev - pre_lev) if pre_lev is not None and post_lev is not None else None,
            "pre_profitability": pre_prof,
            "post_profitability": post_prof,
            "was_declining": was_declining,
            "entered_decline_after_covid": entered_decline_after,
            "recovered": recovered,
            "deteriorated": deteriorated,
            "improved": improved,
        })

    cohort_df = pd.DataFrame(rows)

    if cohort_df.empty:
        return {"error": "No firms with both pre-COVID (2019) and post-COVID (2022+) data"}

    # Summary stats
    n_total = len(cohort_df)
    n_deteriorated = cohort_df["deteriorated"].sum()
    n_improved = cohort_df["improved"].sum()
    n_entered_decline = cohort_df["entered_decline_after_covid"].sum()
    n_recovered = cohort_df["recovered"].sum()

    return {
        "cohort_df": cohort_df,
        "n_total": n_total,
        "n_deteriorated": int(n_deteriorated),
        "n_improved": int(n_improved),
        "n_entered_decline": int(n_entered_decline),
        "n_recovered": int(n_recovered),
        "pct_deteriorated": round(n_deteriorated / n_total * 100, 1),
        "pct_improved": round(n_improved / n_total * 100, 1),
    }


def extract_transition_sequences(G, min_length=2, max_length=4):
    """
    For each company, walk TRANSITION edges to extract stage sequences,
    then count n-gram frequencies across all companies.

    Returns Counter of stage tuples, sorted by frequency.
    """
    from collections import Counter

    all_ngrams = Counter()

    company_nodes = [n for n, d in G.nodes(data=True) if d.get("type") == "company"]

    for company_id in company_nodes:
        # Collect transitions sorted by year
        transitions = []
        for u, v, data in G.edges(company_id, data=True):
            if data.get("relation") == "TRANSITION":
                transitions.append((data["year"], data["from_stage"], data["to_stage"]))
        transitions.sort()

        if not transitions:
            continue

        # Build full stage sequence: first from_stage, then all to_stages
        sequence = [transitions[0][1]]  # first from_stage
        for _, _, to_s in transitions:
            sequence.append(to_s)

        # Extract n-grams
        for n in range(min_length, min(max_length + 1, len(sequence) + 1)):
            for i in range(len(sequence) - n + 1):
                ngram = tuple(sequence[i:i + n])
                all_ngrams[ngram] += 1

    return all_ngrams


def find_paths_to_stage(G, target_stage, lookback=3):
    """
    For each company that reaches target_stage, walk backwards through
    TRANSITION edges to find the preceding stage sequence.

    Returns Counter of path tuples (most recent last = target_stage).
    """
    from collections import Counter

    path_counts = Counter()

    company_nodes = [n for n, d in G.nodes(data=True) if d.get("type") == "company"]

    for company_id in company_nodes:
        transitions = []
        for u, v, data in G.edges(company_id, data=True):
            if data.get("relation") == "TRANSITION":
                transitions.append((data["year"], data["from_stage"], data["to_stage"]))
        transitions.sort()

        # Find all indices where to_stage == target
        for i, (yr, from_s, to_s) in enumerate(transitions):
            if to_s != target_stage:
                continue

            # Walk backwards up to lookback steps
            path = [target_stage]
            path.insert(0, from_s)
            j = i - 1
            while j >= 0 and len(path) - 1 < lookback:
                path.insert(0, transitions[j][1])  # from_stage
                j -= 1

            path_counts[tuple(path)] += 1

    return path_counts


def _stage_color(stage):
    colors = {
        "Startup": "#F97316", "Growth": "#22C55E", "Maturity": "#0D9488",
        "Shakeout1": "#A78BFA", "Shakeout2": "#8B5CF6", "Shakeout3": "#7C3AED",
        "Decline": "#EF4444", "Decay": "#991B1B",
    }
    return colors.get(stage, "#94A3B8")
