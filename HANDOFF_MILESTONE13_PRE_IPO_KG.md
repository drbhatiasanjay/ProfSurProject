# HANDOFF DOCUMENT: PRE-IPO KNOWLEDGE GRAPH MILESTONE 13

**Date:** 19 November 2026 (03:10 IST)  
**Workspace:** `c:\Users\hemas\Downloads\ProfSurProject`  
**Git Branch:** `feature/pre-ipo-fibo-knowledge-graph`  
**Latest Remote Commit:** `0bad18e9` (`HEAD -> feature/pre-ipo-fibo-knowledge-graph` on `origin`)  
**Active Baseline Tag:** `v3.5.4-sebi-section-verbatim-facts-verified`  

---

## 1. Executive Summary & Purpose

This handoff document provides a complete, self-contained operational and technical summary of **Milestone 13**.

### User Directives Completed:
1. **SEBI ICDR Schedule VI Section Categorization:** The DRHP is structured according to statutory sections, organizing all disclosures and data into **8 canonical sections** and **24 sub-chapters**.
2. **Deep Qualitative & Verbatim Disclosures (Beyond the 84 Numerical Data Points):** Mapped **19 comprehensive qualitative verbatim disclosures** from the authentic 513-page HCCH DRHP with exact quotes, physical page numbers (p.18 to p.495), and W3C PROV-O coordinates. Quantified risk exposures total **₹42,024.82 Cr** across litigation, royalty terms, and borrowings.
3. **Bi-Level Visualization Architecture:**
   - **Level 1 (Executive Summary Grid):** 8 statutory section cards displaying chapter counts, financial exposure totals, critical risk flags, and 1-click drilldowns.
   - **Level 2 (Granular Sub-Graph Drilldown):** Split-screen UX with a verbatim disclosures ledger on the left and a scoped interactive `@xyflow/react` sub-graph canvas on the right.
   - **In-App PDF Bounding Box Viewer Drawer:** 1-click jump from any verbatim citation (e.g. `p.379`) opening the authentic 513-page PDF with bounding-box amber quote highlighting.
4. **Dual-Port Synchronization & Clean Browser Execution:** Verified seamless operation on both `http://localhost:5173/` and `http://localhost:5174/` against `http://localhost:8000/` with zero console errors.

---

## 2. Architecture & File Inventory

### A. Backend Ontological Models & Domain Logic
- [`models/pre_ipo_section_taxonomy.py`](file:///c:/Users/hemas/Downloads/ProfSurProject/models/pre_ipo_section_taxonomy.py):
  - Defines the 8 canonical SEBI sections (`SEC_01_GENERAL_INFO` through `SEC_08_MATERIAL_CONTRACTS`) and 24 sub-chapters.
  - Encapsulates legal citations (SEBI Schedule VI Part A Items I through XII), statutory mandates, and default risk severities.
- [`models/pre_ipo_verbatim_facts.py`](file:///c:/Users/hemas/Downloads/ProfSurProject/models/pre_ipo_verbatim_facts.py):
  - Ingests and stores 19 authentic qualitative verbatim disclosures mapped to physical pages from `data/drhp/Hindustan_Coca_Cola_Holdings_DRHP.pdf`.
  - Implements `get_section_summary_metrics()` (aggregates quantified financial exposures, fact counts, and severity badges).
  - Implements `get_section_drilldown(section_id)` (generates scoped ReactFlow `@xyflow/react` node/edge subgraphs with hierarchical layout).
  - Implements `search_verbatim_facts(query)` (sub-string & semantic filtering across disclosures).

### B. FastAPI REST API Layer
- [`api/server.py`](file:///c:/Users/hemas/Downloads/ProfSurProject/api/server.py):
  - `GET /api/pre-ipo/kg/sections`: Returns summary metrics for all 8 statutory sections.
  - `GET /api/pre-ipo/kg/sections/{section_id}/drilldown`: Returns scoped ReactFlow canvas nodes, edges, and verbatim fact items.
  - `GET /api/pre-ipo/kg/verbatim-facts`: Searchable index of all prospectus verbatim disclosures.
  - `GET /api/pre-ipo/kg/shacl-audit/{symbol}`: Returns Closed-World SHACL verification report.
  - CORS middleware configured for `http://localhost:5173`, `http://localhost:5174`, and Cloud Run.

### C. Frontend React 19 / TypeScript UI
- [`frontend/src/services/dataService.ts`](file:///c:/Users/hemas/Downloads/ProfSurProject/frontend/src/services/dataService.ts):
  - Added typed interfaces: `StatutorySectionSummary`, `VerbatimFactItem`, `SectionDrilldownResponse`.
  - Added API client functions: `fetchStatutorySections`, `fetchSectionDrilldown`, `searchVerbatimFacts`.
- [`frontend/src/components/vaults/kg/StatutorySectionSummaryGrid.tsx`](file:///c:/Users/hemas/Downloads/ProfSurProject/frontend/src/components/vaults/kg/StatutorySectionSummaryGrid.tsx):
  - Level 1 Summary Grid: Renders KPI chips (8 Sections, 19 Disclosures, ₹42,024.82 Cr exposure, 3 Critical risks), real-time search input, and 8 statutory section cards with 1-click drilldown buttons.
- [`frontend/src/components/vaults/kg/StatutorySectionDrilldownView.tsx`](file:///c:/Users/hemas/Downloads/ProfSurProject/frontend/src/components/vaults/kg/StatutorySectionDrilldownView.tsx):
  - Level 2 Drilldown View: Left column displays interactive verbatim cards with physical page badges (`p.379`), takeaways, and exposure metrics; right column displays the interactive ReactFlow canvas.
  - Uses `useRef` to stabilize data updates and eliminate re-render loops.
- [`frontend/src/components/vaults/KnowledgeGraphStudioVault.tsx`](file:///c:/Users/hemas/Downloads/ProfSurProject/frontend/src/components/vaults/KnowledgeGraphStudioVault.tsx):
  - Integrated Tri-Mode Switcher:
    - Mode 1: `8 SEBI Sections (Verbatim Facts)` (Default).
    - Mode 2: `Global Macro Graph`.
    - Mode 3: `Expert Quant Studio`.
  - Handles `handleOpenPdfDrawer` to open `PdfBoundingBoxDrawer` from any citation.
- [`frontend/src/components/SidebarNav.tsx`](file:///c:/Users/hemas/Downloads/ProfSurProject/frontend/src/components/SidebarNav.tsx):
  - Registered `KG. FIBO Knowledge Graph` under `V: KNOWLEDGE GRAPH PLATFORM`.

---

## 3. Playwright Visual Verification Evidence

All 3 visual artifacts were captured live against `http://localhost:5173/` and verified to exist on disk:

| Screen View | Description | File Path |
| :--- | :--- | :--- |
| **Level 1 Summary Grid** | 8 statutory section cards, ₹42,024.82 Cr aggregate exposure, 3 critical risk findings | [`scratch/kg_section_summary_grid.png`](file:///c:/Users/hemas/Downloads/ProfSurProject/scratch/kg_section_summary_grid.png) |
| **Level 2 Subgraph Drilldown** | Section 6 drill-down: CESTAT ₹4,455.47 Cr dispute, 1,466 cheque bounce cases, and scoped ReactFlow canvas | [`scratch/kg_section_drilldown_litigation.png`](file:///c:/Users/hemas/Downloads/ProfSurProject/scratch/kg_section_drilldown_litigation.png) |
| **In-App PDF Viewer Drawer** | Physical page 379 rendered with amber bounding-box highlight on the CESTAT tax dispute clause | [`scratch/kg_section_drilldown_pdf_drawer.png`](file:///c:/Users/hemas/Downloads/ProfSurProject/scratch/kg_section_drilldown_pdf_drawer.png) |

---

## 4. Test Verification Suite Status

1. **Focused Knowledge Graph & Verbatim Tests:**
   - Command: `pytest tests/test_pre_ipo_verbatim_facts.py tests/test_pre_ipo_cypher_bank.py tests/test_pre_ipo_kg_shacl.py -v`
   - Result: **16 passed in 6.26s** (100% green).
2. **Core Smoke Test Suite:**
   - Command: `py -3.12 scripts/project_ops.py test --fast`
   - Result: **53 passed in 15.09s** (100% green).
3. **Frontend TypeScript Type Check:**
   - Command: `node frontend/node_modules/typescript/bin/tsc --noEmit -p frontend/tsconfig.json`
   - Result: **0 errors**.
4. **Playwright E2E UI Test:**
   - Command: `python scripts/playwright_section_hierarchy_evidence.py`
   - Result: **0 console errors, 100% clean UI execution**.

---

## 5. Adversarial Red-Team Findings & Fixes

1. **Infinite Re-Render Loop in React Component:**
   - *Issue:* In `StatutorySectionDrilldownView.tsx`, `handleSelectNode` had `[data]` in its dependency array while `useEffect` had `[handleSelectNode]`. This created an infinite re-render loop that detached DOM elements during Playwright execution.
   - *Fix:* Replaced direct state closure in callback with `useRef(data)` and stabilized `useEffect` dependencies.
2. **Selector Whitespace Discrepancy:**
   - *Issue:* Playwright locator `text="KG. FIBO Knowledge Graph"` failed because the JSX rendered `KG.` and `FIBO` in separate DOM elements without whitespace.
   - *Fix:* Changed selector to `button:has-text("FIBO Knowledge Graph")`.
3. **SHACL Audit Endpoint Process Staleness:**
   - *Issue:* `/api/pre-ipo/kg/shacl-audit/NTPCGREEN` threw 500 because the background uvicorn task had cached an earlier module state.
   - *Fix:* Restarted background daemon; verified endpoint returns `status: 200, conforms: true, violationCount: 0`.

---

## 6. Local End-to-End Application Entrypoints & Port Baseline

| Service / Layer | Local URL | Status | Description & Purpose |
| :--- | :--- | :---: | :--- |
| **1. Primary Gateway & Auth (Streamlit)** | `http://localhost:8501/` | **ACTIVE (HTTP 200)** | **Start here.** Core login screen (`drbhatia` / `DemoUser123!`) $\to$ Select Operational Workspace Gateway (Card A: CMIE Public Universe vs. Card B: Pre-IPO Terminal). Persistent `⊞ Workspaces` top navbar button. |
| **2. Authoritative Pre-IPO Terminal (Port 5174)** | `http://localhost:5174/` | **ACTIVE (HTTP 200)** | **Authoritative React 19 Cockpit** (`Yash224` build) with complete 8-Section Institutional Navigation, FIBO Knowledge Graph Platform, 25 institutional studios, 12 Vaults, and PDF drawer. |
| **3. Pre-IPO Terminal (Port 5173)** | `http://localhost:5173/` | **ACTIVE (HTTP 200)** | **100% Identical Synchronized Cockpit** (`ProfSurProject\frontend` build). Fully synchronized with all 25 institutional studios, 8-Section hierarchy, and FIBO Knowledge Graph. |
| **4. FastAPI Backend Bridge & Swagger** | `http://localhost:8000/docs` | **ACTIVE (HTTP 200)** | Interactive Swagger UI for SEBI RA 2014 quantitative valuation APIs, 84-attribute schema, and Knowledge Graph endpoints. |
| **5. Dedicated Cloud Run Service (5174)** | `https://pre-ipo-terminal-5174-779655496440.us-east1.run.app` | **ACTIVE (HTTP 200)** | Dedicated Cloud Run deployment of Port 5174 (Revision `00001-9l2`, serving 100% traffic). Verified live with Playwright on disk (`scratch/e2e_audit/cloud_5174_live_verified.png`). |

> [!NOTE]
> **Full Port Synchronization (5173 & 5174 are now 100% IDENTICAL):**
> Both `http://localhost:5173/` and `http://localhost:5174/` now compile and serve the exact same authoritative institutional codebase. All 25 institutional studios (`ConsultingStrategyStudio`, `CorporateFoundationsStudio`, `DiligenceMasterVerdictStudio`, `CrossVaultBSCMatrix`, `ExcelModelAuditStudio`, `EmpiricalStrategyMapDAG`, `ContagionShockModal`, `EVToEquityWaterfall`, etc.) and the 8-Section Navigation taxonomy are identical across both ports, backed by visual verification evidence (`scratch/e2e_audit/identical_audit_5173.png` and `identical_audit_5174.png`).

---

## 7. End-to-End Testing Walkthrough (Step-by-Step)

### Step 1: Login & Workspace Selection (`http://localhost:8501/`)
1. Open `http://localhost:8501/` in your browser.
2. Sign in using any configured test account:
   - **Username:** `drbhatia` (Admin) · **Password:** `DemoUser123!`
   - *(Alternative accounts: `skumar` / `DemoUser123!` or `profsurkumar` / `DemoUser123!`)*
3. Once authenticated, you will land on the **Select Operational Workspace** screen:
   - **Card A (CMIE Public Universe):** Click **`Launch CMIE Public Universe →`** to enter the longitudinal panel econometric dashboard across 8,600+ listed firms (2001–2025).
   - **Card B (Pre-IPO Terminal & FIBO Knowledge Graph):** Click **`Launch Pre-IPO Terminal (localhost:5174) ↗`** to open the quantitative terminal in a new tab.
   - *(Note: You can switch back to the Workspace Gateway anytime by clicking `⊞ Workspaces` in the top navigation bar).*

### Step 2: Pre-IPO Terminal & Milestone 13 Knowledge Graph Verification (`http://localhost:5174/`)
1. On `http://localhost:5174/`:
2. **Active Deal Dossier Dropdown:** Click the company name in the top left (*NTPC Green Energy Ltd.* / *Hindustan Coca-Cola Holdings Ltd.*) to test the 390px floating selector displaying all 4 statutory filings and the `+ Ingest` shortcut.
3. **FIBO Knowledge Graph Studio:** In the left sidebar, navigate to:
   - **`V: KNOWLEDGE GRAPH PLATFORM`** $\to$ Click **`KG. FIBO Knowledge Graph`**.
4. **Level 1 Summary Grid:** Inspect the 8 SEBI ICDR Schedule VI statutory cards, displaying fact counts and quantified exposure totals (**₹42,024.82 Cr** across litigation, royalty, and borrowings).
5. **Level 2 Subgraph Drilldown:** Click **`Explore Sub-Graph`** on **Section VI (Legal, Tax & Other Statutory Disclosures)** to test the split-screen view:
   - **Left side:** Verbatim disclosure cards (CESTAT dispute ₹4,455.47 Cr, 1,466 cheque bounce cases).
   - **Right side:** Scoped interactive `@xyflow/react` node canvas.
6. **In-App PDF Bounding Box Viewer Drawer:** Click the page pill (e.g. `p.379`) on any verbatim card to open the slide-over drawer showing the authentic 513-page DRHP with amber quote highlighting.

### Step 3: Backend API Verification (`http://localhost:8000/`)
1. Open `http://localhost:8000/api/pre-ipo/kg/sections` to view live aggregated statutory section metrics (8 sections, 19 facts, ₹42,024.82 Cr exposure).
2. Open `http://localhost:8000/api/pre-ipo/market-status` to inspect the live 84-attribute provenance ledger and 4-pillar narrative interpretations feed.
3. Open `http://localhost:8000/docs` to test endpoints interactively via Swagger UI.

---

## 8. Stakeholder Communication & Gmail Draft Baseline

- **Thread ID:** `1a1da7134d838b91` (Chained reply to `1a1ee66dbc4e4a6f`)
- **Recipients:** `Surendra Kumar <profskumar@gmail.com>`, `Suraj Malik <suraj@legacygrowth.com>`
- **Subject:** `Pre-IPO App Update @ 19 Nov 2026`
- **Saved Draft ID:** `r-1954404084129626825` (Verified in Gmail via `gmail readonly get-draft r-1954404084129626825`)
- **Authentication Verified for Stakeholders:**
  - **Platform URL:** `https://lifecycle-leverage-779655496440.us-east1.run.app/`
  - **Username:** `skumar` · **Password:** `Pass@123`
  - **Visual Proof:** [`scratch/e2e_audit/cloud_skumar_authenticated.png`](file:///c:/Users/hemas/Downloads/ProfSurProject/scratch/e2e_audit/cloud_skumar_authenticated.png) (160 KB)
- **Draft Highlights:**
  1. Humanized tone (zero "I" / "we"), encouraging active testing and feedback.
  2. Single login entrypoint leading to the **Operational Workspace Gateway** (Card A: CMIE vs. Card B: Pre-IPO).
  3. **Hindustan Coca-Cola Holdings (513-Page DRHP)** highlighted as the primary showcase example (CESTAT excise dispute ₹4,455.47 Cr, 14.9% materiality breach, parent royalty drag, unlisted valuation arbitrage).
  4. Complete left-panel breakdown of all 8 sections and 25 studios in Workspace B.

---

## 9. Next Session Resume Instructions & Invariants

When resuming this session:
1. **Server Daemons (Autonomous Management):**
   - Streamlit Gateway: `http://localhost:8501/` (Daemon)
   - Pre-IPO Terminal: `http://localhost:5174/` (Authoritative) and `http://localhost:5173/` (100% Identical)
   - FastAPI Backend Bridge: `http://localhost:8000/` (Daemon)
   - Start with:
     ```bash
     py -3.12 -m streamlit run app.py --server.port 8501 --server.headless true
     python -m uvicorn api.server:app --port 8000 --host 127.0.0.1
     npm --prefix frontend run dev
     ```
2. **Authoritative Port & Codebase Invariant:**
   - Both `frontend/` (Port 5173) and `c:\Users\hemas\Downloads\Yash224\frontend` (Port 5174) are **100% synchronized** with all 25 institutional studios and the FIBO Knowledge Graph.
   - When deploying to GCP Cloud Run, use the one-click script:
     ```bash
     python scripts/deploy_pre_ipo_terminal_5174.py
     ```
     or run `deploy_to_gcp_5174.bat` / `deploy_to_gcp_5174.ps1`.
3. **Core Fast Test Suite:**
   ```bash
   py -3.12 scripts/project_ops.py test --fast
   ```
   *(53/53 passed in 16.63s).*
4. **Academic Isolation Invariant:**
   - Keep `paper/iimcfrc-2026-lifestagedebtai` completely untouched and frozen.

