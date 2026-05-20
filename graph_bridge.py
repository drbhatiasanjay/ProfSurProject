"""
KG2 graph bridge — Phase 7: OCaml HTTP + Python fallback.

Tries the OCaml lifecycle-ontology service first (POST /lifecycle_query).
Falls back silently to the Python stub when the service is unavailable.

ISOLATION CONTRACT: never import from graph_builder, pages/7_knowledge_graph,
or pages/18_company_navigator. Read from db.py functions only.
"""

import json
import math
import os
from typing import Optional

import db

# ── OCaml service config ──────────────────────────────────────────────────────

OCAML_SERVICE_URL = os.getenv("LIFECYCLE_ONTOLOGY_URL", "http://localhost:8080")
_OCAML_TIMEOUT = 2.0  # seconds — fail fast and fall back


def _call_ocaml(payload: dict) -> "dict | None":
    """POST payload to OCaml /lifecycle_query. Returns dict or None on any error."""
    try:
        import urllib.request
        body = json.dumps(payload).encode()
        req = urllib.request.Request(
            f"{OCAML_SERVICE_URL}/lifecycle_query",
            data=body,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=_OCAML_TIMEOUT) as resp:
            result = json.loads(resp.read())
            return None if "error" in result else result
    except Exception:
        return None


def _augment_company_nodes(nodes: list) -> list:
    """Backfill company_code on nodes whose id starts with 'company_'."""
    for n in nodes:
        if n.get("type", "").startswith("company") and "company_code" not in n:
            n["company_code"] = n["id"][len("company_"):]
    return nodes

# ── Ontology constants ────────────────────────────────────────────────────────

ALL_STAGES = [
    "Startup", "Growth", "Maturity",
    "Shakeout1", "Shakeout2", "Shakeout3",
    "Decline", "Decay",
]

STAGE_COLORS = {
    "Startup":   "#10B981",
    "Growth":    "#3B82F6",
    "Maturity":  "#8B5CF6",
    "Shakeout1": "#F59E0B",
    "Shakeout2": "#EF4444",
    "Shakeout3": "#DC2626",
    "Decline":   "#6B7280",
    "Decay":     "#374151",
}

# Persona defaults: which stages to pre-select in Meso view
PERSONA_STAGE_DEFAULTS = {
    "CorporateCFO":          ["Growth", "Maturity", "Shakeout1"],
    "RatingAnalyst":         ["Maturity", "Shakeout1", "Shakeout2", "Decline"],
    "VentureDebtInvestor":   ["Startup", "Growth"],
    "PEVCInvestor":          ["Startup", "Growth", "Maturity"],
    "FacultyPhDSupervisor":  ALL_STAGES,
    "RegulatorPolicyAnalyst": ["Shakeout3", "Decline", "Decay"],
}

VALID_PERSONAS = list(PERSONA_STAGE_DEFAULTS.keys())
VALID_LEVELS   = ["macro", "meso", "micro"]

# ── Helpers ───────────────────────────────────────────────────────────────────

def _fmt(v, digits: int = 3) -> str:
    if v is None:
        return "n/a"
    try:
        f = float(v)
        if math.isnan(f) or math.isinf(f):
            return "n/a"
        return str(round(f, digits))
    except (TypeError, ValueError):
        return "n/a"


def _stage_tooltip(stage: str, n_firms: int, avg_lev, avg_prof, avg_tang) -> str:
    return (
        f"<b>{stage}</b><br>"
        f"Firms: {n_firms}<br>"
        f"Avg Leverage: {_fmt(avg_lev)}<br>"
        f"Avg Profitability: {_fmt(avg_prof)}<br>"
        f"Avg Tangibility: {_fmt(avg_tang)}"
    )


def _industry_tooltip(industry: str, n_firms: int, avg_lev) -> str:
    return (
        f"<b>{industry}</b><br>"
        f"Firms: {n_firms}<br>"
        f"Avg Leverage: {_fmt(avg_lev)}"
    )


_EVENT_LABELS = {
    "GFC":   "Global Financial Crisis (2008-09)",
    "IBC":   "Insolvency & Bankruptcy Code (2016+)",
    "COVID": "COVID-19 (2020-21)",
}

def _event_tooltip(event: str, n_obs: int) -> str:
    return f"<b>{_EVENT_LABELS.get(event, event)}</b><br>Affected firm-years: {n_obs}"


def _company_tooltip(name: str, industry: str, stage: str, lev, prof) -> str:
    return (
        f"<b>{name}</b><br>"
        f"Industry: {industry or 'n/a'}<br>"
        f"Stage: {stage or 'n/a'}<br>"
        f"Leverage: {_fmt(lev)}<br>"
        f"Profitability: {_fmt(prof)}"
    )


def _cosine_sim(a_lev, a_prof, a_tang, b_lev, b_prof, b_tang) -> float:
    def _safe(x):
        try:
            v = float(x)
            return 0.0 if math.isnan(v) or math.isinf(v) else v
        except (TypeError, ValueError):
            return 0.0

    a = [_safe(a_lev), _safe(a_prof), _safe(a_tang)]
    b = [_safe(b_lev), _safe(b_prof), _safe(b_tang)]
    dot   = sum(x * y for x, y in zip(a, b))
    mag_a = math.sqrt(sum(x ** 2 for x in a))
    mag_b = math.sqrt(sum(x ** 2 for x in b))
    if mag_a == 0 or mag_b == 0:
        return 0.0
    return dot / (mag_a * mag_b)


# ── Macro graph (≤ 21 nodes) ──────────────────────────────────────────────────

def get_macro_graph(panel_mode: str = "latest", persona: str = "CorporateCFO") -> dict:
    """
    Macro level: exactly 8 stage nodes + top-10 industry nodes + 3 event nodes.
    Total nodes ≤ 21 (hard limit per OCaml contract).
    Tries OCaml service first; falls back to Python implementation.
    """
    if persona not in VALID_PERSONAS:
        persona = "CorporateCFO"

    snap = db.get_kg2_company_snapshot(panel_mode)
    hist = db.get_graph_financials()

    # ── OCaml path ─────────────────────────────────────────────────────────────
    event_col_map = {"GFC": "gfc", "IBC": "ibc_2016", "COVID": "covid_dummy"}
    si_counts = [
        [st, str(ind), int(cnt)]
        for (st, ind), cnt in
        snap.groupby(["life_stage", "industry_group"])["company_code"].nunique().items()
    ]
    crisis_stages_payload = []
    for event_name, col in event_col_map.items():
        if col in hist.columns:
            ev_stages = (
                hist[hist[col] == 1]["life_stage"]
                .dropna().unique().tolist()
            )
            if ev_stages:
                crisis_stages_payload.append([event_name, ev_stages])

    ocaml_result = _call_ocaml({
        "level":                  "macro",
        "persona":                persona,
        "panel_mode":             panel_mode,
        "stage_industry_counts":  si_counts,
        "stage_transitions":      [],
        "crisis_stages":          crisis_stages_payload,
    })
    if ocaml_result is not None:
        return ocaml_result

    # ── Python fallback ─────────────────────────────────────────────────────────
    nodes: list[dict] = []
    edges: list[dict] = []

    # Stage nodes (always 8)
    for stage in ALL_STAGES:
        sub = snap[snap["life_stage"] == stage]
        n   = len(sub)
        nodes.append({
            "id":      f"stage_{stage}",
            "type":    "stage",
            "label":   stage,
            "color":   STAGE_COLORS.get(stage, "#9CA3AF"),
            "size":    max(12, min(40, n // 4 + 12)),
            "tooltip": _stage_tooltip(
                stage, n,
                sub["leverage"].mean()      if n else None,
                sub["profitability"].mean() if n else None,
                sub["tangibility"].mean()   if n else None,
            ),
        })

    # Industry nodes: top 10 by distinct firm count
    ind_counts = snap.groupby("industry_group")["company_code"].nunique().sort_values(ascending=False)
    ind_lev    = snap.groupby("industry_group")["leverage"].mean()
    for ind in ind_counts.head(10).index:
        n       = int(ind_counts[ind])
        avg_lev = float(ind_lev.get(ind, float("nan")))
        nodes.append({
            "id":      f"industry_{ind}",
            "type":    "industry",
            "label":   str(ind)[:20],
            "color":   "#60A5FA",
            "size":    max(10, min(28, n // 3 + 8)),
            "tooltip": _industry_tooltip(str(ind), n, avg_lev),
        })
        # Stage → Industry edges (weight = distinct firms in that stage×industry)
        si = snap[snap["industry_group"] == ind].groupby("life_stage")["company_code"].nunique()
        for stage, cnt in si.items():
            if stage in ALL_STAGES and int(cnt) > 0:
                edges.append({
                    "from":   f"stage_{stage}",
                    "to":     f"industry_{ind}",
                    "type":   "IN_INDUSTRY",
                    "weight": int(cnt),
                    "label":  "",
                })

    # Event nodes (3): GFC, IBC, COVID
    event_cols = {"GFC": "gfc", "IBC": "ibc_2016", "COVID": "covid_dummy"}
    for event_name, col in event_cols.items():
        n_obs = int(hist[col].sum()) if col in hist.columns else 0
        nodes.append({
            "id":      f"event_{event_name}",
            "type":    "event",
            "label":   event_name,
            "color":   "#F87171",
            "size":    15,
            "tooltip": _event_tooltip(event_name, n_obs),
        })
        if col in hist.columns:
            ev_stages = hist[hist[col] == 1].groupby("life_stage")["company_code"].nunique()
            for stage, cnt in ev_stages.items():
                if stage in ALL_STAGES and int(cnt) > 0:
                    edges.append({
                        "from":   f"event_{event_name}",
                        "to":     f"stage_{stage}",
                        "type":   "EXPERIENCED_EVENT",
                        "weight": int(cnt),
                        "label":  "",
                    })

    return {
        "level":       "macro",
        "persona":     persona,
        "panel_mode":  panel_mode,
        "node_count":  len(nodes),
        "nodes":       nodes,
        "edges":       edges,
    }


# ── Meso graph (≤ 80 company nodes) ──────────────────────────────────────────

def get_meso_graph(
    stages:     Optional[list] = None,
    industries: Optional[list] = None,
    panel_mode: str = "latest",
    persona:    str = "CorporateCFO",
) -> dict:
    """
    Meso level: selected stages + industries + ≤80 company nodes.
    Defaults to persona-appropriate stage filter.
    Tries OCaml service first; falls back to Python implementation.
    """
    if persona not in VALID_PERSONAS:
        persona = "CorporateCFO"
    if not stages:
        stages = PERSONA_STAGE_DEFAULTS.get(persona, ALL_STAGES)
    if not industries:
        industries = []

    snap = db.get_kg2_company_snapshot(panel_mode)

    mask = snap["life_stage"].isin(stages)
    if industries:
        mask = mask & snap["industry_group"].isin(industries)
    filtered = snap[mask].copy()

    # Cap at 80 companies — prefer firms with cleaner data (non-null leverage)
    filtered = filtered.dropna(subset=["leverage"])
    if len(filtered) > 80:
        filtered = filtered.nlargest(80, "leverage")

    # ── OCaml path ─────────────────────────────────────────────────────────────
    companies_payload = [
        [
            str(row["company_code"]),
            str(row.get("company_name", row["company_code"]))[:18],
            str(row.get("life_stage", "")),
            str(row.get("industry_group", "")),
            float(row.get("leverage") or 0.0),
        ]
        for _, row in filtered.iterrows()
    ]
    ocaml_result = _call_ocaml({
        "level":      "meso",
        "persona":    persona,
        "panel_mode": panel_mode,
        "companies":  companies_payload,
    })
    if ocaml_result is not None:
        _augment_company_nodes(ocaml_result["nodes"])
        ocaml_result["filters"] = {"stages": stages, "industries": industries}
        return ocaml_result

    # ── Python fallback ─────────────────────────────────────────────────────────
    nodes:  list[dict] = []
    edges:  list[dict] = []
    node_ids: set[str] = set()

    # Stage nodes
    for stage in stages:
        sub   = filtered[filtered["life_stage"] == stage]
        n_sub = len(sub)
        nid   = f"stage_{stage}"
        nodes.append({
            "id":      nid,
            "type":    "stage",
            "label":   stage,
            "color":   STAGE_COLORS.get(stage, "#9CA3AF"),
            "size":    20,
            "tooltip": _stage_tooltip(
                stage, n_sub,
                sub["leverage"].mean()      if n_sub else None,
                sub["profitability"].mean() if n_sub else None,
                sub["tangibility"].mean()   if n_sub else None,
            ),
        })
        node_ids.add(nid)

    # Industry nodes (active in filtered set, capped at 10)
    active_inds = filtered["industry_group"].dropna().value_counts().head(10).index.tolist()
    if industries:
        active_inds = [i for i in active_inds if i in industries]
    for ind in active_inds:
        n_ind   = int(filtered[filtered["industry_group"] == ind].shape[0])
        avg_lev = filtered[filtered["industry_group"] == ind]["leverage"].mean()
        nid     = f"industry_{ind}"
        nodes.append({
            "id":      nid,
            "type":    "industry",
            "label":   str(ind)[:20],
            "color":   "#60A5FA",
            "size":    15,
            "tooltip": _industry_tooltip(str(ind), n_ind, avg_lev),
        })
        node_ids.add(nid)

    # Company nodes
    for _, row in filtered.iterrows():
        code  = str(row["company_code"])
        stage = str(row.get("life_stage", ""))
        ind   = str(row.get("industry_group", ""))
        nid   = f"company_{code}"
        if nid in node_ids:
            continue
        node_ids.add(nid)
        nodes.append({
            "id":           nid,
            "type":         "company",
            "label":        str(row.get("company_name", code))[:18],
            "color":        "#A78BFA",
            "size":         10,
            "tooltip":      _company_tooltip(
                                str(row.get("company_name", code)),
                                ind, stage,
                                row.get("leverage"),
                                row.get("profitability"),
                            ),
            "company_code": code,
        })
        if f"stage_{stage}" in node_ids:
            edges.append({
                "from": nid, "to": f"stage_{stage}",
                "type": "AT_STAGE", "weight": 1, "label": "",
            })
        if f"industry_{ind}" in node_ids:
            edges.append({
                "from": nid, "to": f"industry_{ind}",
                "type": "IN_INDUSTRY", "weight": 1, "label": "",
            })

    return {
        "level":      "meso",
        "persona":    persona,
        "panel_mode": panel_mode,
        "filters":    {"stages": stages, "industries": industries or []},
        "node_count": len(nodes),
        "nodes":      nodes,
        "edges":      edges,
    }


# ── Micro graph (focal firm + ≤20 peers) ─────────────────────────────────────

def get_micro_graph(
    company_code: str,
    panel_mode:   str = "latest",
    persona:      str = "CorporateCFO",
) -> dict:
    """
    Micro level (ego graph): focal company + ≤20 peers + stage + event nodes.
    Peers ranked by cosine similarity on (leverage, profitability, tangibility).
    Tries OCaml service first; falls back to Python implementation.
    """
    if persona not in VALID_PERSONAS:
        persona = "CorporateCFO"

    snap = db.get_kg2_company_snapshot(panel_mode)
    focal_rows = snap[snap["company_code"].astype(str) == str(company_code)]
    if focal_rows.empty:
        return {
            "level":          "micro",
            "persona":        persona,
            "panel_mode":     panel_mode,
            "focal_company":  company_code,
            "error":          f"Company {company_code} not found in panel {panel_mode}",
            "node_count":     0,
            "nodes":          [],
            "edges":          [],
        }

    focal        = focal_rows.iloc[0]
    focal_stage  = str(focal.get("life_stage", "") or "")
    focal_ind    = str(focal.get("industry_group", "") or "")
    f_lev        = focal.get("leverage", 0.0)
    f_prof       = focal.get("profitability", 0.0)
    f_tang       = focal.get("tangibility", 0.0)

    # Peer candidates: same industry first, fall back to same stage
    peer_pool = snap[snap["company_code"].astype(str) != str(company_code)].copy()
    same_ind  = peer_pool[peer_pool["industry_group"] == focal_ind].copy()
    if len(same_ind) < 5:
        same_ind = peer_pool[peer_pool["life_stage"] == focal_stage].copy()

    if len(same_ind) > 0:
        same_ind["_sim"] = same_ind.apply(
            lambda r: _cosine_sim(
                f_lev, f_prof, f_tang,
                r.get("leverage"), r.get("profitability"), r.get("tangibility"),
            ),
            axis=1,
        )
        peers = same_ind.nlargest(20, "_sim")
    else:
        peers = peer_pool.head(20)
        peers = peers.copy()
        peers["_sim"] = 0.0

    history    = db.get_kg2_company_history(company_code, panel_mode)
    event_col_map = {"GFC": "gfc", "IBC": "ibc_2016", "COVID": "covid_dummy"}
    crisis_events = [
        ev for ev, col in event_col_map.items()
        if col in history.columns and history[col].sum() > 0
    ]

    # ── OCaml path ─────────────────────────────────────────────────────────────
    peers_payload = [
        [
            str(r["company_code"]),
            str(r.get("company_name", r["company_code"]))[:18],
            str(r.get("life_stage", "")),
            float(r.get("leverage") or 0.0),
            round(float(r.get("_sim", 0.0)), 3),
        ]
        for _, r in peers.iterrows()
    ]
    ocaml_result = _call_ocaml({
        "level":           "micro",
        "persona":         persona,
        "panel_mode":      panel_mode,
        "focal_code":      str(company_code),
        "focal_name":      str(focal.get("company_name", company_code))[:18],
        "focal_stage":     focal_stage,
        "focal_leverage":  float(f_lev or 0.0),
        "peers":           peers_payload,
        "crisis_events":   crisis_events,
    })
    if ocaml_result is not None:
        _augment_company_nodes(ocaml_result["nodes"])
        ocaml_result["focal_company"] = str(company_code)
        focal_nid = f"company_{company_code}"
        for n in ocaml_result["nodes"]:
            if n.get("type") == "company":
                n["type"] = "company_focal" if n["id"] == focal_nid else "company_peer"
        return ocaml_result

    # ── Python fallback ─────────────────────────────────────────────────────────
    nodes:    list[dict] = []
    edges:    list[dict] = []
    node_ids: set[str]   = set()

    # Focal node
    focal_nid = f"company_{company_code}"
    nodes.append({
        "id":           focal_nid,
        "type":         "company_focal",
        "label":        str(focal.get("company_name", company_code))[:18],
        "color":        "#F59E0B",
        "size":         28,
        "tooltip":      _company_tooltip(
                            str(focal.get("company_name", company_code)),
                            focal_ind, focal_stage, f_lev, f_prof,
                        ),
        "company_code": str(company_code),
    })
    node_ids.add(focal_nid)

    # Stage node
    if focal_stage:
        stage_nid = f"stage_{focal_stage}"
        nodes.append({
            "id":      stage_nid,
            "type":    "stage",
            "label":   focal_stage,
            "color":   STAGE_COLORS.get(focal_stage, "#9CA3AF"),
            "size":    18,
            "tooltip": focal_stage,
        })
        node_ids.add(stage_nid)
        edges.append({
            "from": focal_nid, "to": stage_nid,
            "type": "IN_STAGE", "weight": 1, "label": "",
        })

    # Event nodes from history (already fetched above)
    for event_name, col in event_col_map.items():
        if col in history.columns and history[col].sum() > 0:
            n_obs   = int(history[col].sum())
            evt_nid = f"event_{event_name}"
            nodes.append({
                "id":      evt_nid,
                "type":    "event",
                "label":   event_name,
                "color":   "#F87171",
                "size":    12,
                "tooltip": _event_tooltip(event_name, n_obs),
            })
            node_ids.add(evt_nid)
            edges.append({
                "from": focal_nid, "to": evt_nid,
                "type": "EXPERIENCED_EVENT", "weight": n_obs, "label": "",
            })

    # Peer nodes (≤20)
    for _, peer in peers.iterrows():
        peer_code = str(peer["company_code"])
        sim       = round(float(peer.get("_sim", 0.0)), 3)
        peer_nid  = f"company_{peer_code}"
        if peer_nid in node_ids:
            continue
        node_ids.add(peer_nid)
        nodes.append({
            "id":           peer_nid,
            "type":         "company_peer",
            "label":        str(peer.get("company_name", peer_code))[:18],
            "color":        "#C4B5FD",
            "size":         9,
            "tooltip":      _company_tooltip(
                                str(peer.get("company_name", peer_code)),
                                str(peer.get("industry_group", "")),
                                str(peer.get("life_stage", "")),
                                peer.get("leverage"),
                                peer.get("profitability"),
                            ),
            "company_code": peer_code,
        })
        edges.append({
            "from":   focal_nid,
            "to":     peer_nid,
            "type":   "IS_PEER_OF",
            "weight": sim,
            "label":  f"sim={sim}",
        })

    return {
        "level":          "micro",
        "persona":        persona,
        "panel_mode":     panel_mode,
        "focal_company":  str(company_code),
        "node_count":     len(nodes),
        "nodes":          nodes,
        "edges":          edges,
    }


# ── Unified entry point ───────────────────────────────────────────────────────

def get_graph_json(level: str, **kwargs) -> dict:
    """
    Unified entry point for all KG2 graph levels.
    level: 'macro' | 'meso' | 'micro'

    Phase 5: swap each branch for:
        return requests.post(OCAML_SERVICE_URL + "/" + level, json=kwargs).json()
    """
    if level == "macro":
        return get_macro_graph(
            panel_mode=kwargs.get("panel_mode", "latest"),
            persona=kwargs.get("persona", "CorporateCFO"),
        )
    elif level == "meso":
        return get_meso_graph(
            stages=kwargs.get("stages"),
            industries=kwargs.get("industries"),
            panel_mode=kwargs.get("panel_mode", "latest"),
            persona=kwargs.get("persona", "CorporateCFO"),
        )
    elif level == "micro":
        return get_micro_graph(
            company_code=kwargs["company_code"],
            panel_mode=kwargs.get("panel_mode", "latest"),
            persona=kwargs.get("persona", "CorporateCFO"),
        )
    else:
        raise ValueError(f"Unknown level '{level}'. Must be one of {VALID_LEVELS}")
