# KG2 Architecture — LifeCycle Leverage Knowledge Graph 2

> **Primary entry point** for KG2 implementation. Cross-references all four spec files.
> KG1 (`pages/7_knowledge_graph.py`, `pages/18_company_navigator.py`, `graph_builder.py`) is **frozen and untouched**.

---

## 1. What Is KG2?

Knowledge Graph 2 is a separate, new graph analytics page (`pages/21_knowledge_graph2.py`) built alongside the existing KG1 stack. It is backed by an OCaml semantic meta-layer and rendered via `streamlit-agraph` (React physics graph), replacing KG1's NetworkX/pyvis "hairball" with a structured three-level visual hierarchy.

**Why KG2 is better than KG1:**

| Aspect | KG1 | KG2 |
|---|---|---|
| Node count | 9,450+ (hairball) | Hard caps: 21 / 80 / 21 |
| Type safety | Python dicts / strings | OCaml ADTs (invalid stages impossible) |
| Visualization | pyvis HTML embed | streamlit-agraph React (click, physics sim) |
| Explainability | None | "Explain This" panel with provenance |
| Personas | None | 6 personas shaping KPIs and views |
| Normative bands | None | Conformalized QR bands with coverage guarantee |
| Scenarios | None | What-if scenario runner per persona |
| ML analytics | None | PyKEEN, GAT, DoWhy, scikit-survival, DSPy |
| Provenance | None | W3C PROV-O aligned, MLflow tracked |

---

## 2. Spec Document Map

All design decisions trace back to these four files:

| File | Purpose |
|---|---|
| `OCaml Ontology & Analytics Spec.md` | Master spec v4 — full system detail (ontology types, MCP tools, CI, UX) |
| `LifeCycle Leverage – OCaml Archit.md` | Architecture overview — service boundaries, data/control flow, deployment |
| `LifeCycle Leverage – Ontology Des.md` | Ontology design — types, relations, invariants, ML extensions, academic standards |
| `Claude VS Code Dev Guide for Life.md` | Claude master prompt + technology constraints + Phase 0–8 implementation order |

---

## 3. KG2 Isolation Contract

**KG2 must never import from KG1.**

| Rule | Detail |
|---|---|
| No KG1 imports | `pages/21_knowledge_graph2.py` and `graph_bridge.py` must not import `graph_builder`, `pages/7_knowledge_graph`, or `pages/18_company_navigator` |
| DB access only via `db.py` | Use `get_filtered_financials`, `get_company_list`, etc. — never raw SQL in the page |
| Canonical OCaml IDs | All stage/metric/persona values crossing Python↔OCaml boundary use OCaml ADT IDs, not arbitrary strings |
| Separate tests | `tests/test_kg2_bridge.py` only; no fixture sharing with `test_cfo_graph.py` or KG1 test files |
| Visualization library | KG2 uses `streamlit-agraph`; KG1 retains pyvis HTML embeds |

---

## 4. Three-Level Visual Hierarchy

```
Macro  ─── 8 stage nodes + 10 industry nodes + 3 event nodes  (≤ 21 total)
   │
Meso   ─── user-filtered stages/industries + ≤ 80 company nodes
   │
Micro  ─── focal firm + ≤ 20 peers (ego graph)
```

**Hard limits** — never return more than the cap regardless of filters.

Every node requires a `tooltip` field (HTML string) for hover display:
- Stage nodes: aggregate leverage/profitability/tangibility, firm count.
- Company nodes: firm fingerprint — latest stage, key metrics, anomaly flags.
- Industry nodes: firm count, median leverage, stage distribution.

Edge types: `IN_INDUSTRY`, `AT_STAGE`, `TRANSITION`, `IS_PEER_OF` (with `similarity_score`), `EXPERIENCED_EVENT`, `HAS_NORM`.

---

## 5. Component Layout

```
pages/21_knowledge_graph2.py   ← Streamlit UI: Macro/Meso/Micro viewer,
                                  persona selector, "Explain This" panel,
                                  normative band overlays, .owl download
        │
        ▼
graph_bridge.py                ← Python seam: Phase 0 = stub generating
                                  OCaml-contract JSON; Phase 5 = HTTP call
        │                         to OCaml service (zero UI changes)
        ▼
[Phase 0] Python stub          ← reads db.py, returns Macro/Meso/Micro JSON
[Phase 5] OCaml HTTP           ← POST /lifecycle_query → dream/Eio service
        │
        ▼
lifecycle-ontology/            ← OCaml service
  src/domain/                  ← stage, period, metric, company ADTs
  src/analytics_meta/          ← model, statistic, normative_band, scenario
  src/normative/               ← conformalized QR bands + anomaly flags
  src/scenario/                ← scenario DSL + DSPy explanation templates
  src/graph_export/            ← Macro/Meso/Micro → JSON/DOT exporters
  src/api/                     ← Dream HTTP: /lifecycle_query /explain_stat
  src/cli/                     ← cmdliner commands
  test/                        ← alcotest unit tests
        │
        ▼
capitalstructure.db (SQLite)   ← authoritative panel source
DuckDB                         ← analytical queries (20–50× faster)
Graphiti                       ← temporal stage-transition episode store
```

---

## 6. `graph_bridge.py` JSON Contract

All three functions return JSON objects matching this schema. The schema is identical whether the stub or the OCaml service is the source.

### Macro graph
```json
{
  "level": "macro",
  "nodes": [
    {"id": "stage_Startup", "type": "stage", "label": "Startup",
     "tooltip": "<b>Startup</b><br>Firms: 47<br>Avg leverage: 0.32"},
    {"id": "industry_Steel", "type": "industry", "label": "Steel", "tooltip": "..."},
    {"id": "event_GFC",      "type": "event",    "label": "GFC",   "tooltip": "..."}
  ],
  "edges": [
    {"from": "industry_Steel", "to": "stage_Growth", "type": "IN_INDUSTRY", "weight": 12}
  ]
}
```

### Meso graph
```json
{
  "level": "meso",
  "filters": {"stages": ["Growth", "Maturity"], "industries": ["Steel"]},
  "nodes": [/* ≤ 80 company nodes + stage/industry nodes */],
  "edges": [/* AT_STAGE, IN_INDUSTRY, TRANSITION */]
}
```

### Micro graph (ego)
```json
{
  "level": "micro",
  "focal_company": "TATA001",
  "nodes": [/* focal + ≤ 20 peers */],
  "edges": [/* IS_PEER_OF with similarity_score, IN_STAGE, EXPERIENCED_EVENT, HAS_NORM */]
}
```

---

## 7. OCaml Ontology Types (Summary)

Full types in `OCaml Ontology & Analytics Spec.md` §2. Key domain types:

```ocaml
type stage = Startup | Growth | Maturity
           | Shakeout1 | Shakeout2 | Shakeout3
           | Decline | Decay

type persona =
  | RatingAnalyst | CorporateCFO | VentureDebtInvestor
  | PEVCInvestor  | FacultyPhDSupervisor | RegulatorPolicyAnalyst

type event = GFC | IBC | COVID
```

Invariant: invalid stages are a compile-time error in OCaml — impossible to pass `"shakeout"` where a `stage` is expected.

---

## 8. ML Analytics Layer

Results feed back into the graph as `statistic` objects with provenance:

| Library | Role |
|---|---|
| **PyKEEN** (RotatE) | Stage-transition link prediction — scores all 8 stages at t+1 |
| **PyG GAT v2** | Peer-influence via attention weights; GNNExplainer subgraph |
| **DoWhy** | Causal: "GFC increased Decline odds by 3.2× (95% CI: 2.1–4.8)" |
| **scikit-survival** | Competing-risk time-to-stage-transition (AalenJohansenFitter) |
| **PyOD** | Trajectory anomaly: AutoEncoder on 401×24 leverage matrix |
| **DSPy** | Structured explanation generation with typed output schemas |
| **Conformalized QR** | Normative bands with finite-sample coverage guarantee |

---

## 9. Phase 0–8 Build Sequence

Detailed in `Claude VS Code Dev Guide for Life.md` §3. Summary:

| Phase | Deliverable | Gate |
|---|---|---|
| **0** | Python stub + `pages/21_knowledge_graph2.py` + `app.py` nav | `pytest tests/test_kg2_bridge.py` green; KG1 tests (344) still pass |
| **1** | OCaml scaffold: `lifecycle-ontology/` + `dune-project` | `dune build` green |
| **2** | Domain types: `stage.ml`, `period.ml`, `metric.ml`, `company.ml` | `dune runtest` green |
| **3** | Analytics meta: model, statistic, normative_band, scenario, persona + JSON serialization | alcotest coverage |
| **4** | Normative + Scenario logic: conformalized QR, scenario DSL, DSPy templates | unit tests green |
| **5** | Graph export: Macro/Meso/Micro JSON; swap `graph_bridge.py` stub for OCaml HTTP | zero UI changes |
| **6** | CLI + HTTP/MCP: Dream endpoints, Neo4j MCP, Graphiti MCP | integration tests |
| **7** | ML analytics: PyKEEN, GAT, DoWhy, scikit-survival, DSPy | model outputs in KG2 UI |
| **8** | Academic: PROV-O alignment, MLflow, Gephi export, Zenodo LOD publication | PhD thesis artifacts |

---

## 10. Key Commands

```bash
# Phase 0: run KG2 locally (Python stub only, no OCaml needed)
streamlit run app.py

# KG2 bridge tests
py -3.12 -m pytest tests/test_kg2_bridge.py -v

# Full test suite (must stay green — 344+ tests)
py -3.12 -m pytest tests/ -v

# Phase 1+: OCaml toolchain
opam switch create 5.2.0
opam install dune base core eio_main yojson ocamlgraph cmdliner dream alcotest

# OCaml build + test
cd lifecycle-ontology && dune build && dune runtest

# OCaml CLI examples
lifecycle-ontology export-graph --vintage run3 --max-firms 50 > kg_sample.json
lifecycle-ontology normative-bands --vintage run3 > normative.json
```
