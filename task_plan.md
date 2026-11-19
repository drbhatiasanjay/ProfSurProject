# Task Plan: Milestone 13 — Statutory Section-Hierarchical Knowledge Graph with Deep Verbatim Fact Mapping & Bi-Level Summary/Drill-Down Architecture

<!-- 
  MANUS Planning Framework: Working Memory on Disk
  Persistent files in project root: task_plan.md, findings.md, progress.md
-->

## Goal
Transform the Pre-IPO Financial Knowledge Graph from a flat macro-entity graph into an authentic **SEBI ICDR Statutory Section-Hierarchical Knowledge Graph**. Map hundreds of deep, granular entities and verbatim qualitative disclosures (beyond the 84 scalar numerical points) across the 513-page HCCH DRHP, with a bi-level **Summary Executive View $\leftrightarrow$ Granular Drill-Down View** in the terminal.

## Current Phase
Phase 1: Statutory SEBI Section Taxonomy & Granular Verbatim Fact Ontology

## Phases

### Phase 1: Statutory SEBI Section Taxonomy & Granular Verbatim Fact Ontology
- [ ] Define the 8 SEBI ICDR Sections / 24 Statutory Chapters hierarchy in `models/pre_ipo_section_taxonomy.py`.
- [ ] Model the `VerbatimFact` and `StatutorySection` schema classes in the FIBO ontology.
- [ ] Formalize typed relationships connecting Sections $\to$ Chapters $\to$ Entities $\to$ Verbatim Disclosures (`[:DISCLOSES_FACT]`, `[:APPOINTS_DIRECTOR]`, `[:EXECUTES_CONTRACT]`, `[:FACES_LITIGATION]`).
- [ ] Document in `findings.md`.
- **Status:** in_progress

### Phase 2: Deep Granular Entity Density & Verbatim Fact Extraction (`models/pre_ipo_verbatim_facts.py`)
- [ ] Extract and map 120+ granular entities and verbatim statutory facts from the 513-page HCCH DRHP:
  - Section IV (Management & Promoters): Directors, KMP, cross-directorships, lock-in commitments, promoter group cross-holdings.
  - Section IV (Business & Contracts): Concentrate Supply Agreement, Trademark Sublicense, parent marketing subsidies, plant assets.
  - Section V (Financials): Ind AS 116 lease commitments, auditor notes, restated P&L caveats.
  - Section VI (Litigation): 100+ disaggregated lawsuits across Direct Tax, Indirect Tax (CESTAT), S.138 Cheque Bounce, and CPCB environmental actions.
  - Section III (Capital Structure & Objects): 100% OFS exit, GCP ceiling, plant capex allocation.
- [ ] Ensure 100% of facts have exact verbatim quotes, physical DRHP page numbers, and W3C PROV-O confidence scores.
- [ ] Authored pytest unit suite `tests/test_pre_ipo_verbatim_facts.py`.
- **Status:** pending

### Phase 3: Hierarchical Graph Engine & Backend REST Endpoints (`api/server.py`)
- [ ] Implement section-based subgraph filtering and roll-up aggregation in `models/pre_ipo_kg_engine.py`.
- [ ] Register `GET /api/pre-ipo/kg/sections`: Returns the 8 statutory sections with aggregate risk counts, fact counts, and entity density.
- [ ] Register `GET /api/pre-ipo/kg/sections/{section_id}/drilldown`: Returns the granular sub-graph, nodes, edges, and verbatim fact cards for any selected section.
- [ ] Register `GET /api/pre-ipo/kg/verbatim-facts/search`: Semantic and keyword search across all verbatim disclosures with direct PDF page jumps.
- [ ] Write integration test `tests/test_pre_ipo_hierarchical_kg_api.py`.
- **Status:** pending

### Phase 4: Bi-Level Frontend Architecture (Summary View $\leftrightarrow$ Granular Drill-Down View)
- [x] Build `frontend/src/components/vaults/kg/StatutorySectionSummaryGrid.tsx`:
  - Executive Level 1: 8 statutory section cards displaying mapped entity counts, critical risk badges, financial exposures (e.g. ₹4,455 Cr litigation), and contagion alert pills.
  - 1-click "Drill Down into Section Subgraph" action.
- [x] Build `frontend/src/components/vaults/kg/StatutorySectionDrilldownView.tsx`:
  - Deep Level 2: Interactive ReactFlow canvas scoped to the selected statutory chapter, category filter pills (Directors, Contracts, Litigations, Financials), and verbatim fact side-drawer.
  - Citation clicks seamlessly open the `PdfBoundingBoxDrawer` with amber quote highlights.
- [x] Wire bi-level navigation into `KnowledgeGraphStudioVault.tsx` with smooth back-and-forth breadcrumbs (`Sections Overview > Section VI: Legal & Litigation > Case CESTAT 4455 Cr`).
- [x] Verify 0 TypeScript errors.
- **Status:** completed

### Phase 5: Verification, Playwright UI Evidence Capture & Documentation
- [x] Run Playwright automated E2E script capturing:
  - Level 1 Summary Section Overview (`scratch/kg_section_summary_grid.png`).
  - Level 2 Drill-Down into Section VI (`scratch/kg_section_drilldown_litigation.png`).
  - Verbatim Fact citation click opening the In-App PDF Drawer (`scratch/kg_section_drilldown_pdf_drawer.png`).
- [x] Verify 0 console errors on port 5173 and 5174.
- [x] Update `progress.md`, `CURRENT_STATUS.md`, commit and push to Git.
- **Status:** completed

## Errors Encountered & Red-Team Resolutions
| Error | Attempt | Resolution |
| :--- | :---: | :--- |
| `Locator.scroll_into_view_if_needed: Timeout 30000ms exceeded on text="KG. FIBO Knowledge Graph"` | 1 | Button DOM had no whitespace between `KG.` and `FIBO`. Changed selector to `button:has-text("FIBO Knowledge Graph")`. |
| `Locator.scroll_into_view_if_needed: Element is not attached to the DOM` on citation click | 1 | Discovered infinite re-render loop caused by `handleSelectNode` reference recreation in `useEffect` dependency array. Refactored to `useRef` and stable dependencies. |
## Milestone 14: Phase 2A - Cross-Section Risk Contagion & Shock Simulation Engine
- [x] Phase 1: Mathematical Contagion Core & Graph Traversal (`models/pre_ipo_contagion_engine.py`)
- [x] Phase 2: Red-Team Unit Test Suite (`tests/test_pre_ipo_contagion_engine.py` - 6/6 passed)
- [x] Phase 3: REST API Integration (`api/server.py`: `/simulate-contagion`, `/contagion-scenarios`)
- [x] Phase 4: Frontend Contagion Shock Workbench (`ContagionShockModal.tsx`)
- [x] Phase 5: Playwright Visual Verification (`scratch/kg_contagion_shock_workbench.png`)
- **Status:** completed

## Milestone 15: Phase 2B - GraphRAG & Natural Language Cypher Copilot
- [x] Phase 1: Grounded NL Cypher Intent Router (`models/pre_ipo_graphrag_router.py`)
- [x] Phase 2: Unit Test Suite (`tests/test_pre_ipo_graphrag_router.py` - 6/6 passed)
- [x] Phase 3: REST API Integration (`api/server.py`: `/copilot/query`, `/copilot/suggested-prompts`)
- [x] Phase 4: Frontend Copilot Bar (`KnowledgeGraphCopilotBar.tsx` with Novice/Advanced persona toggle)
- [x] Phase 5: Playwright Visual Verification & Bounding Box Jump (`scratch/kg_copilot_query_result.png`, `scratch/kg_copilot_pdf_jump.png`)
- **Status:** completed

## Milestone 16: Phase 2C - CMIE ProwessIQ Peer Benchmarks & Macro Transmission Linkage
- [x] Phase 1: Peer Ingestion & Macro Transmission Elasticity (`models/pre_ipo_cmie_macro_engine.py`)
- [x] Phase 2: Relative Valuation Spread Solver (VBL 38.5x vs HCCB 24.5x, Crude -> PET Resin pass-through)
- [x] Phase 3: REST API Integration (`/api/pre-ipo/kg/cmie-peers`, `/api/pre-ipo/kg/simulate-macro-shock`)
- [x] Phase 4: Frontend CMIE Macro Workbench (`CMIEMacroWorkbench.tsx`)
- **Status:** completed

## Milestone 17: Phase 2D - Post-IPO Simulations & Institutional Export Pipeline
- [x] Phase 1: Post-IPO Lifecycle Simulator (`models/pre_ipo_post_ipo_simulator.py`: T+30/T+90 Anchor Cliff, Day 1 Discovery, BHAR Decay)
- [x] Phase 2: Institutional Exporter (`models/pre_ipo_institutional_exporter.py`: W3C RDF Turtle `.ttl`, Neo4j Cypher `.cyp`, FIBO JSON-LD `.jsonld`, SHA-256 SEBI Audit Manifest)
- [x] Phase 3: Unit Test Suite (`tests/test_pre_ipo_cmie_and_export.py` - 9/9 passed)
- [x] Phase 4: REST API Integration (`/api/pre-ipo/kg/post-ipo/anchor-cliff`, `/api/pre-ipo/kg/export/*`)
- [x] Phase 5: Frontend Institutional Export Modal (`InstitutionalExportModal.tsx`)
- [x] Phase 6: Playwright Visual Verification (`scratch/kg_cmie_macro_workbench.png`, `scratch/kg_institutional_export_modal.png`)
- **Status:** completed

