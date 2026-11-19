# Task Plan: Milestone 19 - Temporal Knowledge Graph & Multi-DRHP Filing Comparison Diff Engine

## Goal
Build an institutional-grade Bi-Temporal Knowledge Graph and filing comparison engine that tracks corporate structural evolution, regulatory observations, strategic obfuscation, and valuation impact between preliminary filings (DRHP) and final offerings (RHP) under SEBI ICDR Regulations.

## Workstreams & Phases

### Phase 1: Planning, Research & Manus Setup [COMPLETED]
- [x] Audit academic literature (Cohen, Malloy, Nguyen 2020; Hanley & Hoberg 2010, 2012).
- [x] Audit industry software (Litera, Intelligize, AlphaSense/Sentieo, Bloomberg).
- [x] Identify fatal gaps in current lexical diff tools.
- [x] Initialize Manus working memory files: `task_plan.md`, `findings.md`, `progress.md`.
- [x] Author comprehensive PRD (`docs/PRD_TEMPORAL_KNOWLEDGE_GRAPH_DIFF_ENGINE.md`).
- [x] Author Technical Specification (`docs/TECH_SPEC_TEMPORAL_KNOWLEDGE_GRAPH.md`).
- [x] Author Independent Review & Visual Evidence Protocol (`docs/VERIFICATION_AND_INDEPENDENT_REVIEW_PROTOCOL.md`).

### Phase 2: Core Bi-Temporal Knowledge Graph Engine & Schemas
- [ ] Create `models/pre_ipo_temporal_schema.py`:
  - Bi-temporal quad representation: `(subject, predicate, object, [t_valid_start, t_valid_end])`.
  - SEBI ICDR Schedule VI chapter categorization (Chapters I through XI).
  - Explicit typing for mutation types (`ADDED`, `DELETED`, `MUTATED`, `BRACKET_RESOLVED`).
  - Strict zero-truthiness compliance (Rule E.3: `if val is None:`).
- [ ] Create `models/pre_ipo_temporal_diff_engine.py`:
  - Graph topological difference algorithm $O(|V| + |E|)$.
  - Cohen-Malloy Strategic Obfuscation Index (physical coordinate/page drift scoring).
  - Valuation & WACC ripple propagation calculator (translating factual changes to equity value delta).
  - Parent indemnity and litigation shield reconciliation.
- [ ] Author adversarial test suite `tests/test_pre_ipo_temporal_diff.py`:
  - Prove zero-truthiness preservation on 0.0% dilution, 0 legal claims, 0.0 WACC spread.
  - Test fail-closed boundary conditions on unindexed filing pairs.
  - Test obfuscation detection on buried risk factors (Section I to Footnotes).
  - Test mathematical inversion and valuation ripple reconciliation ($\le 0.05\%$).

### Phase 3: REST API & Gateway Endpoints
- [ ] Expose endpoints in `api/server.py`:
  - `GET /api/pre-ipo/kg/temporal/versions?symbol=HCCH`: Available filings list (DRHP v1.0, Addendum v2.1, Final RHP v3.2).
  - `GET /api/pre-ipo/kg/temporal/diff?symbol=HCCH&base=DRHP&target=RHP`: Complete quad mutation tree, chapter drift metrics, and valuation delta.
  - `GET /api/pre-ipo/kg/temporal/verbatim-redline?symbol=HCCH&fact_id=...`: Side-by-side bounding box excerpt and page coordinates.
- [ ] Restart backend service and verify HTTP 200 via CLI smoke tests.

### Phase 4: Innovative & Visual Frontend Experience
- [ ] Create `frontend/src/components/vaults/kg/TemporalFilingScrubber.tsx`:
  - Motion-driven time-travel slider scrubbing across filing dates.
- [ ] Create `frontend/src/components/vaults/kg/BiTemporalGraphMutationCanvas.tsx`:
  - High-performance visual canvas displaying green neon glowing added nodes, amber pulsating mutated edges, and ghosted red severed relationships.
- [ ] Create `frontend/src/components/vaults/kg/FilingDualRedlineDrawer.tsx`:
  - Synchronized split-screen PDF document drawer with verbatim bounding boxes.
- [ ] Create `frontend/src/components/vaults/kg/SemanticDriftRadar.tsx`:
  - 11-chapter SEBI ICDR drift radar with Cohen-Malloy Evasion Index indicator.
- [ ] Wire services in `frontend/src/services/dataService.ts` and update `ProspectusKnowledgeGraph.tsx`.
- [ ] Synchronize code to `C:/Users/hemas/Downloads/Yash224/frontend/` and verify production build.

### Phase 5: Verification, Independent Review & Release Gate
- [ ] Run full pytest regression suite (50+ tests).
- [ ] Run Playwright automated browser audit capturing screenshot proof of scrubber, canvas mutations, and split-screen redline drawer.
- [ ] Execute Independent Subagent Code Review (AST call-graph wiring, zero dead code, no AI patterns).
- [ ] Commit and push to `drbhatiasanjay/ProfSurProject` with valid keyring token.

## Key Decisions Log
| Decision | Rationale | Impact |
| :--- | :--- | :--- |
| Bi-Temporal Quads over Lexical Diff | Lexical diffs generate 95% false-positive noise on page/table shifts | Focuses analysis exclusively on verified statutory and corporate mutations |
| SEBI ICDR Schedule VI Anchor | Every mutation mapped to official SEBI chapters (I through XI) | Matches regulatory inspection requirements and institutional due diligence |
| Zero Python Truthiness | `0.0`, `0%`, and `0` are valid financial values distinct from `None` | Prevents fallback bugs in financial ratio calculations |
| Dedicated Scrubber + Redline Drawer | Separates macro visual topology from micro verbatim proof | Novice users see high-level ripple; advanced analysts inspect exact legal clauses |

## Errors Log
| Error | Attempt | Resolution |
| :--- | :--- | :--- |
| N/A | 0 | None yet |
