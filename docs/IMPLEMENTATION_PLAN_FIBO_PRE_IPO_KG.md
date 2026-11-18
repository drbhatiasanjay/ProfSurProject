# Work Breakdown Structure & Implementation Plan (WBS)
## Milestone 11: FIBO-Aligned Pre-IPO Financial Knowledge Graph Platform

**Branch:** `feature/pre-ipo-fibo-knowledge-graph`  
**Governing Documents:**
- [`docs/PRD_FIBO_PRE_IPO_KNOWLEDGE_GRAPH.md`](file:///c:/Users/hemas/Downloads/ProfSurProject/docs/PRD_FIBO_PRE_IPO_KNOWLEDGE_GRAPH.md)
- [`docs/ARCHITECTURE_SPEC_FIBO_PRE_IPO_KG.md`](file:///c:/Users/hemas/Downloads/ProfSurProject/docs/ARCHITECTURE_SPEC_FIBO_PRE_IPO_KG.md)
- [`docs/adr/ADR_001_EMBEDDED_KUZU_VS_NEO4J.md`](file:///c:/Users/hemas/Downloads/ProfSurProject/docs/adr/ADR_001_EMBEDDED_KUZU_VS_NEO4J.md)
- [`docs/adr/ADR_002_CLOSED_WORLD_SHACL_VS_OPEN_WORLD_OWL.md`](file:///c:/Users/hemas/Downloads/ProfSurProject/docs/adr/ADR_002_CLOSED_WORLD_SHACL_VS_OPEN_WORLD_OWL.md)

---

## Phase 1: Core Ontology & Closed-World SHACL Validation (Milestone 11.1)
- [ ] **Task 1.1: Codify Scoped FIBO TBox (`models/ontology/fibo_pre_ipo_tbox.ttl`)**
  - Define namespaces: `fibo-fnd`, `fibo-be`, `fibo-fbc`, `fibo-sec`, `fibo-ind`, and custom `fibo-sebi`.
  - Partition legal entities (`be:LegalEntity`) from roles (`fibo-sebi:SellingShareholderRole`, `fibo-sebi:PromoterRole`).
  - Define Indian SEBI extensions (`MaterialSubsidiary`, `PromoterGroup`, `OfferObject`, `LitigationProceeding`, `ExclusiveTerritory`, `RelatedPartyContract`).
- [ ] **Task 1.2: Author Statutory SHACL Constraints (`models/ontology/sebi_icdr_shapes.ttl`)**
  - Shape 1: `OfferStructureShape` (Reconciliation: $\text{Total Issue} = \text{Fresh} + \text{OFS}$; Rule E.3 Zero-Truthiness).
  - Shape 2: `PromoterDisclosureShape` (Mandatory PAN, pre-issue shareholding, lock-in period).
  - Shape 3: `LitigationReconciliationShape` (Risk factor cross-check against litigation chapter).
  - Shape 4: `RPTMaterialityShape` (Discretionary incentive growth vs. EBITDA margin alert).
- [ ] **Task 1.3: Closed-World Validation Engine (`models/pre_ipo_shacl_engine.py`)**
  - Implement `validate_prospectus_abox(graph_data) -> SHACLValidationReport`.
  - Write negative red-team unit tests asserting fail-closed behavior on missing or corrupted disclosures.
  - Verification: `pytest tests/test_pre_ipo_kg_shacl.py` (100% pass).

---

## Phase 2: In-Process Hybrid Storage & Ingestion Pipeline (Milestone 11.2)
- [ ] **Task 2.1: Embedded Kùzu Graph Engine (`models/pre_ipo_kuzu_engine.py`)**
  - Initialize embedded Kùzu schema: Node tables (`CompanyNode`, `SubsidiaryNode`, `LitigationNode`, etc.) and Rel tables (`OWNS`, `OFFERS_IN`, `DEFENDANT_IN`, `OPERATES_IN`).
  - Implement atomic commit wrapper with single-writer mutex locks.
- [ ] **Task 2.2: W3C PROV-O Layout-Aware Ingestion Pipeline (`models/pre_ipo_kg_ingest.py`)**
  - Ingest PDF text and tables via PyMuPDF/pdfplumber with physical bounding-box coordinates.
  - Anchor every extracted fact to `documentSha256`, `pageNumber`, and `[x0, y0, x1, y1]` coordinates.
- [ ] **Task 2.3: MicroDecisionEngine & Fallback Adapter (`models/pre_ipo_decision_engine.py`)**
  - Abstract interface: `evaluate_micro_decision(state, questions)`.
  - TypeSafe Jev connector (`POST /v1/systemone` using pinned `typesafe/jev-1.14.0`).
  - Local heuristic / Gemini 1.5 Flash fallback adapter for offline CI execution.
- [ ] **Task 2.4: HCCH Benchmark Golden Extraction Test (`tests/test_pre_ipo_kg_hcch.py`)**
  - Ingest authentic 513-page HCCH DRHP dataset into staging graph $\to$ validate via SHACL $\to$ commit to Kùzu.
  - Assert 100% OFS, ₹4,455 Cr HCCB litigation, and 75.63% northern territory revenue concentration.

---

## Phase 3: Analytical Query Tiers & Valuation Simulator (Milestone 11.3)
- [ ] **Task 3.1: Tier 1 (1-Hop Lookups) & Tier 2 (2-Hop Cross-Chapter) Engine**
  - Pre-compiled Cypher query templates in `models/pre_ipo_kg_queries.py`.
  - Correlate Q1 FY27 EBITDA margin jump to related-party discounts and Risk Factor 4.
- [ ] **Task 3.2: Tier 3 (3+ Hop Contagion) & Jev Subgraph Pruning**
  - Multi-hop pathfinding: `(Distributor Cheque Bounces) -> (5 Territories) -> (Campa War) -> (VBL Outlet Gap)`.
  - Integrate Jev pruning ($noul \ge 0.65$) to strip 90% irrelevant subgraphs before LLM synthesis.
- [ ] **Task 3.3: Arrow Financial Calculations & Valuation Simulator (`models/pre_ipo_kg_valuation.py`)**
  - Connect DuckDB/Polars Arrow tables for dynamic multiple discounting and SARD weights.
  - Implement mathematical round-trip inversion tests for valuation outputs.
- [ ] **Task 3.4: FastAPI Endpoints Registration (`api/server.py`)**
  - Register `/api/pre-ipo/kg/ingest`, `/api/pre-ipo/kg/graph/{symbol}`, `/api/pre-ipo/kg/query`, and `/api/pre-ipo/kg/shacl-audit`.

---

## Phase 4: Modern Dual-Persona UI/UX Studio (Milestone 11.4)
- [ ] **Task 4.1: UI Foundation & Typography Tokens (`frontend/src/`)**
  - Configure Inter font with `tabular-nums slashed-zero` and 12-column responsive grid.
  - Build Dual-Persona Header Switcher (`Guided Discovery` $\leftrightarrow$ `Quant Studio`).
- [ ] **Task 4.2: Mode A — Novice Guided Discovery Canvas (`frontend/src/components/vaults/kg/NoviceGuidedCanvas.tsx`)**
  - 5-second traffic-light verdict HUD strip.
  - Bloom-style interactive node expansion with custom card nodes using `@xyflow/react`.
  - Plain-English narrative cards with clickable DRHP page citation pills.
- [ ] **Task 4.3: Mode B — Expert Quant Studio (`frontend/src/components/vaults/kg/ExpertQuantStudio.tsx`)**
  - Split-pane Monaco Cypher query console + live network canvas.
  - PROV-O Bounding Box Inspector with in-app PDF crop viewer.
  - Live sensitivity workbench (Jev pruning threshold slider, territory haircut, ECharts Football Field).
- [ ] **Task 4.4: Vault 8 Navigation & App Integration (`frontend/src/App.tsx` & `SidebarNav.tsx`)**
  - Register `KnowledgeGraphStudioVault` in navigation sidebar.
- [ ] **Task 4.5: Browser E2E Verification & Screen Evidence Capture**
  - Execute live authenticated browser tests across both Novice and Expert modes.
  - Capture disk screenshot evidence and verify zero console errors.
