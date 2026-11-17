# Task Plan: Institutional Pre-IPO Terminal (v3.5.0) Full Implementation

## Goal
Implement the frozen Option A (Dual-Layer Cockpit & Vault) Pre-IPO Terminal architecture on `http://localhost:5173/`, incorporating the 17 adopted capabilities from the 54-page master specification, with zero-truthiness numerical rigor (Rule E.3), fail-closed unpriced DRHP failsafes, and mandatory physical Playwright verification.

## Current Phase
Phase 7: Final Review & Milestone Commit

---

## 1. Comprehensive & Adversarial Acceptance Criteria (Institutional Grade)

Every phase of implementation has satisfied the following **8-pillar verification gates**:

### Gate 1: SEBI ICDR Statutory & Offering Dilution Criteria
- [x] **G1.1 (Filing Route Disclosures):** Every deal renders an explicit statutory route badge:
  - NTPC Green: `Regulation 6(2) 75% QIB Book Building`
  - HCCB: `Regulation 6(2) 75% QIB Book Building (Mature Cash Cow)`
- [x] **G1.2 (Exact Share Count Disclosures):** For unpriced OFS prospectuses (HCCB), offering size renders `997,461,456 Shares` alongside estimated Rupee value (`₹9,975.00 Cr Est.`), never showing `0 Shares` or `₹0.0 Cr`.
- [x] **G1.3 (SEBI Regulation 7 GCP Cap Check):** Tower 1 programmatically verifies that General Corporate Purposes allocation satisfies $\text{GCP} \le 25\%$ of gross Fresh Issue proceeds. (NTPC Green: exactly 25.0% ₹2,500 Cr; HCCB: 0% GCP on OFS).
- [x] **G1.4 (Lock-In Overhang Schedule):** Tower 3 renders the exact 3-tier lock-in ladder:
  - Day 1: Free trading float (15%)
  - Day 90: +35% (50% QIB Anchor release tranche)
  - Day 180: +50% (SEBI Reg 17 mandatory non-promoter lock-in release)

### Gate 2: Unpriced DRHP & Zero-Truthiness Mathematical Boundary Criteria
- [x] **G2.1 (Unpriced DRHP Failsafe):** When price band is unannounced (HCCB `₹[●]`), Tower 2 renders `Drafting / Unpriced (₹[●])` and `Undisclosed [●]` without generating `NaN`, `Infinity`, or division-by-zero errors.
- [x] **G2.2 (Strict Rule E.3 Zero-Truthiness):** No financial variable uses `val or default`. Numeric $0.0$, $0\%$, and $0$ are handled as legitimate values distinct from `null`/`undefined`.
- [x] **G2.3 (Priced Issue Parity):** For priced issues (NTPC Green ₹102–₹108), the statutory metric cards, Tower 2 Froth Gap ($+1508.8\%$), and live QIB order book render fully populated.

### Gate 3: Econometric & Valuation Studio Criteria
- [x] **G3.1 (Huber M-Estimator):** Outlier-resistant regression ($t=1.345$) calculates DRHP Peer Selection Bias Index and Warranted Fair Multiple in Vault 3.
- [x] **G3.2 (Quantile Valuation Envelopes):** Vault 3 displays P10 Bear, P50 Base, and P90 Bull fair valuation cones.
- [x] **G3.3 (18-Month WACA Step-Up):** Vault 2 displays upper price band step-up multiple vs. statutory 18-month WACA, triggering warning if step-up $>2.50\text{x}$.
- [x] **G3.4 (Mueller ROCE Persistence):** Vault 2 displays the Mueller (1986) AR(1) persistence coefficient ($\lambda$) and competitive rent half-life.

### Gate 4: Forensic Accounting & 6-Rule Red-Flag Scanner Criteria
- [x] **G4.1 (Tri-State Red-Flag Radar in Vault 8):** The scanner programmatically evaluates and renders status badges (`TRIGGERED`, `CLEAR`, `MONITOR`) for:
  - `FLAG-01`: Cash conversion divergence ($(3\text{Y PAT CAGR} > 20\%) \land (\text{CFO/EBITDA} < 0.55\text{x})$)
  - `FLAG-02`: Stub margin spike ($(\text{Stub EBITDA \%} - \text{Prior FY EBITDA \%}) > +350\text{ bps}$)
  - `FLAG-03`: Excessive insider exit ($(\text{OFS} / \text{Total Issue}) > 0.65$)
  - `FLAG-04`: Contingent tail risk ($(\text{Contingent Liab} / \text{Net Worth}) > 0.15$)
  - `FLAG-05`: Related Party leakage ($(\text{RPT Outflows} / \text{Revenue}) > 0.10$)
  - `FLAG-06`: Valuation step-up ($(\text{Upper Band} / \text{18M WACA}) > 2.50\text{x}$)
- [x] **G4.2 (Forensic Ratios):** Vault 8 computes and displays Sloan Accrual Ratio (4.2%) and modified Beneish M-Score (-2.84, Safe Zone).
- [x] **G4.3 (Customer Concentration Shock):** Vault 6 shows Top-1, Top-5, Top-10 customer concentration with $>40\%$ churn shock warning.

### Gate 5: Unlisted Post-Tax Arbitrage & Break-Even Simulator Criteria
- [x] **G5.1 (Interactive Cost Modeler in Vault 9):** Dynamic inputs for unlisted purchase price, 1.25% transaction friction, and 6-month opportunity carry cost.
- [x] **G5.2 (Section 56(2)(x) Rule 11UA FMV Tax Drag):** Calculates buyer income tax liability when unlisted purchase is below book/discounted cash flow FMV.
- [x] **G5.3 (LTCG vs. STCG Differential):** Enforces 20% STCG (exit at 6M post-listing) vs. 12.5% LTCG (24M holding period).
- [x] **G5.4 (Solver Round-Trip Inversion Test):** Post-tax breakeven listing price satisfies mathematical inversion ($\le 0.05\%$ tolerance, verified at $0.0000\%$).

### Gate 6: UI/UX & High-Craft Interaction Criteria
- [x] **G6.1 (Dual-Layer Cockpit & Vault 38/62 Split):** Pinned persistent cockpit occupies $\le 38\%$ of viewport height, leaving $\ge 62\%$ for vault analytics with zero vertical page doom-scrolling.
- [x] **G6.2 (Global Tri-State Ledger Counter):** Top bar displays live verification counters: `[ 🟢 36 VERIFIED ] [ ⚪ 4 RHP PENDING ] [ 🟠 2 RECONFIRM ]`.
- [x] **G6.3 (Tri-State Visual Cell Semantics):** Financial tables use solid border for `FOUND`, dashed muted badge for `NOT_FOUND (RHP PENDING)`, and amber left-border for `NEEDS_RECONFIRMATION` (never false zeros).
- [x] **G6.4 (Interactive Price-Band Simulator Slider):** Vault 1 & 9 feature interactive sliders recalculating implied valuation in real time.
- [x] **G6.5 (Trailing vs. Seasonality FY27E Toggle):** Two-way toggle in Hero switches between raw trailing actuals and normalized seasonality-adjusted forward earnings.
- [x] **G6.6 (4-Pillar Narrative Drawer):** Every card features an expandable `AnalystInsightDrawer.tsx` with Sector Context, Lifecycle Precedents, IC Directives, and Risk Radar.
- [x] **G6.7 (1-Click Regulatory Exports):** Vault 10 provides direct triggers for 16:9 Vector Board Deck (PPTX) and SEBI RA Research Memo (PDF) with download notifications.

### Gate 7: Evidence Containment & Bounding-Box Provenance Criteria
- [x] **G7.1 (Fail-Closed Quarantine):** When `is_contained === true` (HCCB), an amber dark glass banner appears with text: `SEBI ICDR 2018 STATUTORY EVIDENCE CONTAINMENT ACTIVE` and a direct `[ Review Ledger → ]` shortcut to Vault 4.
- [x] **G7.2 (5-Point Accounting Reconciliation Card):** Vault 4 displays Pass/Fail status across Balance Sheet Identity, Split, CFO to P&L, Dilution, and Objects of Offer.
- [x] **G7.3 (Lightweight Coordinate Inspector):** Clicking a `[Ch.X p.Y]` chip opens a snippet drawer highlighting the exact bounding box `[x0, y0, x1, y1]`.

### Gate 8: First-Time-Right Code Quality & Physical Evidence Gate
- [x] **G8.1 (Clean Compile):** `npx tsc --noEmit` and Vite build compile with zero errors; `py -3.12 -m py_compile` passes on all backend files.
- [x] **G8.2 (FastAPI Unit Tests):** `pytest tests/test_api_server.py -q` and `tests/test_pre_ipo_*.py` pass 100%.
- [x] **G8.3 (Mandatory Physical Evidence):** Automated Chromium Playwright script (`scripts/verify_pre_ipo_v35_e2e.py`) executed across both priced (NTPC Green) and unpriced (HCCB) deals, saving 6 physical PNG screenshots to disk.

---

## 2. Implementation Phases

### Phase 1: Working Memory & Isolated Worktree Setup
- [x] Create canonical `task_plan.md`, `findings.md`, and `progress.md`
- [x] Create isolated git branch: `feature/pre-ipo-cockpit-vault-v35`
- [x] Verify clean baseline compile in the isolated environment
- **Status:** complete

### Phase 2: TypeScript Data Contracts & Unpriced-Safe Types
- [x] Update `frontend/src/types/terminal.ts` with `OfferPriceBand` (supporting `is_undisclosed: boolean`, `raw_string: string`, `lower: number | null`, `upper: number | null`)
- [x] Add `VaultId` union type covering all 10 specialized vaults
- [x] Add `TriStateLedgerCounters` and `RedFlagItem` interfaces
- [x] Add `UnlistedArbitrageModel`, `AnchorQualityMetrics`, `FivePointReconciliationGate`, `ProvenanceField`
- [x] Verify zero-truthiness compliance and clean Vite HMR reload
- **Status:** complete

### Phase 3: Persistent Cockpit Component Hardening
- [x] Refactor `StatutoryOfferHero.tsx`:
  - Mount 6 statutory badges (Dickinson `(+,-,-)`, Route, Context, Audit, Date)
  - Display exact share count (`997,461,456 Shares`) alongside Rupee conversion
  - Add collapsible Amber Evidence Containment Banner with Vault 4 shortcut
  - Add Trailing FY26 vs. Seasonality-Adjusted FY27E Forward toggle
  - Add Mainboard vs. SME Emerge segment switcher
- [x] Build `LintelTowers.tsx`:
  - Tower 1: SEBI Reg 7 Capital Growth vs. OFS Exit with GCP $\le 25\%$ check
  - Tower 2: Huber Fair P/E vs. Asking Multiple Stretch with `Drafting / Unpriced (₹[●])` failsafe
  - Tower 3: Day-180 Float Overhang Cliff (Day 1: 15%, Day 90: +35%, Day 180: +50%)
- **Status:** complete

### Phase 4: Left Navigation & 10 Specialized Vault Workspaces
- [x] Update `SidebarNav.tsx` to mount 10 vault selectors with icons and sub-labels
- [x] Scaffold Vault 4: `ProvenanceLedgerVault.tsx` (513p BBox Coordinate Inspector & 5-Gate Accounting)
- [x] Scaffold Vault 5: `StressWorkpapersVault.tsx` (2D 5x5 Stress Grid & Debt Maturity Ladder)
- [x] Scaffold Vault 6: `InvestorQAVault.tsx` (14 Institutional Questions & Churn Shock Alert)
- [x] Scaffold Vault 7: `StakeholderLensVault.tsx` (6-Persona Switcher: CFO, Lender, QIB, Retail, RA, Board)
- [x] Scaffold Vault 8: `RedFlagScannerVault.tsx` (6-rule automated radar + Beneish M-Score)
- [x] Scaffold Vault 9: `UnlistedArbitrageVault.tsx` (Sec 56(2)(x) FMV check + 6M carry cost breakeven)
- [x] Scaffold Vault 10: `ICBoardDeckVault.tsx` (Mandate & 1-Click PPTX/PDF triggers)
- [x] Embed 4-Pillar Narrative Intelligence Drawer (`AnalystInsightDrawer.tsx`) across all major cards
- **Status:** complete

### Phase 5: Backend FastAPI Bridge Updates (`api/server.py`)
- [x] Extend `/api/pre-ipo/market-status` to return `totalOfferingShares`, `freshIssuePct`, `ofsPct`, `isPriceUndisclosed`, and `isContained`
- [x] Ensure fail-closed unpriced handling for HCCB (`isPriceUndisclosed = True`, `priceBandMin = None`)
- [x] Verify zero-truthiness (`if val is None:`) across all handlers
- [x] Run `py -3.12 -m py_compile api/server.py`
- **Status:** complete

### Phase 6: Automated Playwright Verification & Physical Evidence Gate
- [x] Author `scripts/verify_pre_ipo_v35_e2e.py` using Chromium Playwright
- [x] Test State A: NTPC Green Energy (Priced issue, 5 cards, Tower 2 Froth Gap)
- [x] Test State B: Hindustan Coca-Cola (Unpriced DRHP, Amber Banner, 997M shares, Tower 2 unpriced failsafe)
- [x] Test State C: Interactive Slider & Solver Round-Trip Inversion (0.0000% residual)
- [x] Test State D: Sidebar Vault Navigation (Click through all 10 vaults without error)
- [x] Capture and verify 6 physical `.png` screenshots on disk
- **Status:** complete

### Phase 7: Milestone Commit (v3.5.0 Cockpit Baseline)
- [x] Record milestone achievements in `findings.md` and `progress.md`
- [x] Create git commit on branch `feature/pre-ipo-cockpit-vault-v35` (`107f2505`)
- [x] Provide user handoff summary with clickable links to all evidence artifacts
- **Status:** complete

### Phase 8: Pinned-HUD Architecture & Left-Right Scroll Synchronization (Elephant-Goldfish Synthesis)
- [x] Build `frontend/src/components/CompactCockpitHUD.tsx`
- [x] Refactor `SidebarNav.tsx` (Viewport-lock the sidebar)
- [x] Refactor `App.tsx` (Wire `CompactCockpitHUD`, auto-reset scroll to $y=0$)
- [x] Milestone commit on `feature/pre-ipo-cockpit-vault-v35`
- **Status:** complete

### Phase 9: Standardized Narrative Interpretation & Action Framework (Decision Intelligence Engine)
- [x] Create `models/pre_ipo_interpretations.py`:
  - Deterministic synthesis layer producing `AnalyticalInterpretation` with `polarity`, `headline`, `what_it_means`, `evidence_basis` (with `cited_inputs` and DRHP page numbers), `call_to_action`, and `missing_data_and_blind_spots`
  - Zero Python truthiness, dynamic grounding in actual extracted metrics and missing fields
- [x] Wire into `models/pre_ipo_econometrics.py` & `api/server.py`:
  - Expose `@app.get("/api/pre-ipo/interpretations/{symbol}")` and attach to market-status
  - Fail-closed capability gating via `assert_capability_allowed`
- [x] Frontend Contract & Data Service (`frontend/src/types/terminal.ts`, `dataService.ts`):
  - Add `Polarity` and `AnalyticalInterpretation` interfaces
  - Add API fetchers and fallback mock datasets
- [x] Reusable Right-Hand Canvas Component (`frontend/src/components/shared/EvidenceInterpretationPanel.tsx`):
  - Polarity badge, "What This Means", Evidence Trail with clickable citation pills, Call to Action, Missing Data & Blind Spots checklist
- [x] Embed into Vaults:
  - `EconometricLabVault.tsx`, `ProvenanceLedgerVault.tsx`, `UnlistedArbitrageVault.tsx`, `RedFlagScannerVault.tsx`, `StakeholderLensVault.tsx`, `ICBoardDeckVault.tsx`, and `App.tsx` (Valuation & Peers views)
- [x] Verification & Tests:
  - Unit tests in `tests/test_pre_ipo_interpretations.py` (11/11 passed)
  - Synchronous pytest suite (39 passed, 2 skipped) and TypeScript (`tsc --noEmit`) passes with 0 errors
- **Status:** complete
