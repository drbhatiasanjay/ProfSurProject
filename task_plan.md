# Task Plan: RHP In-Depth Cypher Query Bank, 84-Attribute Formula Lineage & In-App PDF Bounding Box Drawer

<!-- 
  MANUS Planning Framework: Working Memory on Disk
  Persistent files in project root: task_plan.md, findings.md, progress.md
-->

## Goal
Build a comprehensive institutional forensic diligence platform for Red Herring Prospectuses (HCCH DRHP benchmark): an in-depth Cypher Query Bank (25+ queries across 5 forensic categories), an unbroken 84-Attribute $\leftrightarrow$ 10-Section $\leftrightarrow$ Mathematical Formula Lineage Engine, and a modern In-App PDF Bounding Box Viewer Drawer in the React 19 terminal.

## Current Phase
Phase 5: End-to-End Verification, Playwright UI Evidence & Deployment (Complete)

## Phases

### Phase 1: Architecture, Ontology Mapping & Lineage Specification
- [x] Map all 84 Canonical Attributes across the 10 statutory SEBI ICDR sections.
- [x] Formalize mathematical formulas for all application analyses (Altman Z", Beneish M, Dickinson Life-Cycle, Huber RLM Froth, Ind AS 116 Net Debt, GCP 25% statutory limit, SARD multiple haircuts).
- [x] Define the 25+ Cypher queries taxonomy across 5 forensic risk categories.
- [x] Document in `findings.md` and `models/pre_ipo_formula_lineage.py`.
- **Status:** complete

### Phase 2: In-Depth Cypher Query Bank Engine (`models/pre_ipo_cypher_bank.py`)
- [x] Implement query templates with parameterized graph traversal (1-hop, 2-hop, 3+ hop contagion).
- [x] Integrate execution in `PreIPOPropertyGraphEngine` (DuckDB + NetworkX).
- [x] Wire multi-hop pathfinding into analytical verdicts and W3C PROV-O citation metadata.
- [x] Write pytest test suite `tests/test_pre_ipo_cypher_bank.py` asserting exact ground truth on 513-page HCCH DRHP.
- **Status:** complete

### Phase 3: Backend REST Endpoints & Capability Gates (`api/server.py`)
- [x] Register `/api/pre-ipo/kg/cypher-bank` (lists catalog of 25+ queries with categories, descriptions, and formulas).
- [x] Register `/api/pre-ipo/kg/cypher-exec` (executes selected query with parameter overrides).
- [x] Register `/api/pre-ipo/kg/formula-lineage` (returns complete mathematical DAG from metric to 84 attributes).
- [x] Register `/api/pre-ipo/kg/formula-calc` (calculates analytical formula with Rule E.3 zero-truthiness).
- [x] Register `/api/pre-ipo/kg/pdf-page/{page_number}` (serves authentic DRHP PDF page text and paragraphs from 513p PDF).
- **Status:** complete

### Phase 4: Frontend In-App PDF Bounding Box Drawer Component
- [x] Build `PdfBoundingBoxDrawer.tsx` slide-over modal in `frontend/src/components/vaults/kg/`.
- [x] Add interactive Formula Lineage inspector modal showing the math tree from analysis $\to$ formula $\to$ 84 attributes.
- [x] Add Cypher Query Bank dropdown/selector in Mode B (Expert Quant Studio) with live execution.
- [x] Wire data services in `frontend/src/services/dataService.ts`.
- **Status:** complete

### Phase 5: End-to-End Verification, Playwright UI Evidence & Deployment
- [x] Execute full pytest suite with 100% pass across all tests (53 smoke tests + 22 KG tests).
- [x] Run Playwright automated E2E script capturing Mode A, Mode B, Cypher Bank, and PDF Drawer screenshots.
- [x] Verify 0 console errors and zero truthiness regressions.
- [x] Update `progress.md`, `CURRENT_STATUS.md`, and commit/push to Git.
- **Status:** complete

## Errors Encountered
| Error | Attempt | Resolution |
| :--- | :---: | :--- |
| `networkx.NodeNotFound: Node NTPCGREEN is not in G` on `/api/pre-ipo/kg/graph/NTPCGREEN` | Symbol mismatch for active terminal deal | Fall back cleanly to `"HCCH"` benchmark graph if symbol is not present in graph |
| TypeScript duplicate tags in `KnowledgeGraphStudioVault.tsx` | TS compilation check | Removed trailing duplicate closing tags; verified 0 TS errors |
