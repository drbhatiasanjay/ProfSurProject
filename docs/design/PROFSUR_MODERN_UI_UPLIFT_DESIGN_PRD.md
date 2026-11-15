# Product Requirement Document (PRD)
## ProfSur Terminal: Institutional UI Uplift & Dual-Engine Architecture

**Document Version:** 1.0.0  
**Status:** Approved for Implementation Planning  
**Target Release:** v3.5.0 (Modern React Pre-IPO Terminal & Unified Strangler Architecture)  
**Author:** DeepMind Agentic Assistant (ProfSur Engineering Group)  
**Stakeholders:** Institutional Allocators, Quantitative Research Analysts, Corporate CFOs, Credit Committees  

---

## 1. Executive Summary & Product Vision

### 1.1 The Problem
The existing ProfSur platform provides deep econometric capability (8,677 CMIE firm-year observations, 121 KB Stata engine supporting `xtreg`/`reghdfe`, and a 1,830-line conversational financial assistant). However, its presentation layer is bound to Streamlit's legacy execution model:
1. **Full-Page Reruns**: Every slider movement, dropdown selection, or tab switch triggers a Python server-side execution loop, introducing 300ms–1500ms latency.
2. **Visual Clutter & Generic UI**: Streamlit's default container hierarchy lacks the dense, surgical, tabular typography required by institutional investment committees and research analysts.
3. **Stateless Disconnect**: Static historical DRHP/RHP filings (past fundamentals) are divorced from dynamic secondary market pricing (live peer multiples, QIB book demand, and lock-in supply shocks).

### 1.2 The Solution
The **ProfSur Modern UI Uplift** transitions the platform to a **Dual-Engine Strangler Fig Architecture**:
- **Front-of-House (Tier 1)**: A blazing-fast, high-density **React 19 + TypeScript + Tailwind CSS v4** terminal adhering to **Google Modern Web Guidance (MWG)** and institutional **Anti-AI-Slop** design principles (Obsidian canvas `#090D12`, Midnight Slate `#101620`, surgical borders `#223044`, tabular numerals `font-mono tabular-nums`).
- **Back-of-House (Tier 2)**: The deep Python econometric and Stata engine (`models/stata_engine.py`, `models/covenant_pilot.py`, `models/profsur_walkforward_ml_huber.py`, `pages/19_ai_assistant.py`) exposed via a high-performance **FastAPI** service bridge.
- **Unified Gateway**: Cloud Run routes the primary terminal experience at `/` while maintaining isolated, zero-regression access to the 28 deep research pages at `/research`.

---

## 2. User Personas & Analytical Journeys

```mermaid
journey
    title 5-Stage Institutional Pre-IPO Evaluation Journey
    section Stage 1: Filing
      Upload 500p DRHP/RHP: 5: Analyst
      Extract 74-Family Facts & Ind AS Financials: 5: System
      Run Sloan Accrual & Beneish M-Score: 4: System
    section Stage 2: Market
      Stream Live NSE Index & Regime: 5: System
      Harvest Live Comps Multiples: 5: System
      Track QIB vs Retail Book: 5: System
    section Stage 3: Valuation
      Detect DRHP Peer Selection Bias: 5: System
      Calibrate Huber M-Estimator: 5: System
      Quantify Unbacked Multiple Froth %: 4: Analyst
    section Stage 4: Trajectory
      Predict 180D Post-Listing Alpha (Head A): 4: System
      Forecast Month-6 Lock-in Supply CAR (Head B): 4: System
      Inspect SHAP Waterfall Drivers: 5: Analyst
    section Stage 5: Decision
      Issue SEBI RA Mandate (AVOID/BUY): 5: Investment Committee
      Sign Cryptographic SHA-256 Audit Seal: 5: Compliance
```

### 2.1 Target User Personas
1. **Institutional Portfolio Manager (CIO / Allocator)**:
   - *Needs*: Immediate clarity on listing-day hype vs. 1-year fundamental execution; statutory lock-in supply shock risks (Day 30/90 anchor and Day 180 pre-IPO shareholder unlocks).
   - *Key Metric*: Head A $P(\text{BHAR}_{180\text{D}} > +10\%)$ and Head B Month-6 CAR $[-5\text{D}, +10\text{D}]$.
2. **Quantitative Research Analyst (SEBI RA 2014)**:
   - *Needs*: Methodological rigor; robust statistics resisting outlier leverage; verification of cherry-picked comps.
   - *Key Metric*: Huber robust regression $t$-statistics, DRHP Peer-Selection Bias Index, Sloan Accrual ratio, and immutable SHA-256 audit ledger.
3. **Corporate CFO / Credit Committee**:
   - *Needs*: 12-quarter CFADS cash flow forecasting, Ind AS 116 lease obligations, and dynamic debt headroom before covenant breach.
   - *Key Metric*: Maximum borrowing headroom before $\text{ICR} < 2.0\times$ or $\text{DSCR} < 1.5\times$.

---

## 3. Design Tokens & Anti-AI-Slop Visual System

### 3.1 Design Philosophy: Anti-AI-Slop & Google MWG
- **Zero Generic AI Slop**: Absolutely NO centered floating cards with purple neon glows, blurry gradient blobs, or generic chatbot speech bubbles.
- **High-Density Bloomberg Terminal Aesthetic**: Maximum information density per viewport height; thin 1px surgical borders; tabular alignment; explicit visual hierarchy.
- **Google Modern Web Guidance (MWG)**:
  - Container Queries (`@container`) for modular responsiveness.
  - Subgrid for aligned tabular financial statements.
  - Zero Layout Shift ($\text{CLS} = 0$), Interaction to Next Paint ($\text{INP} \le 200\text{ms}$).
  - Full native keyboard accessibility (`Tab`, `Enter`, `Escape`).

### 3.2 Design Token Specification

| Token Category | Token Variable | Hex / CSS Value | Semantic Application |
| :--- | :--- | :--- | :--- |
| **Canvas** | `--bg-canvas` | `#090D12` | Root dark backdrop (Deep Obsidian) |
| **Panel Surface** | `--bg-panel` | `#101620` | Primary container surface (Midnight Slate) |
| **Panel Subtle** | `--bg-panel-subtle` | `#151D2A` | Elevated cards, hovered rows, nested tables |
| **Surgical Border** | `--border-surgical` | `#223044` | 1px hairline separation between financial blocks |
| **Border Accent** | `--border-accent` | `#334661` | Focused inputs, hovered cards, active tabs |
| **Primary Text** | `--text-primary` | `#F1F5F9` | High-contrast headers, active metrics, badges |
| **Secondary Text**| `--text-secondary` | `#94A3B8` | Column labels, subheadings, unit notations |
| **Muted Text** | `--text-muted` | `#64748B` | Footnotes, regulatory citations, inactive pills |
| **Accent Cyan** | `--accent-cyan` | `#06B6D4` | Terminal brand, primary actions, active indicators |
| **Accent Emerald**| `--accent-emerald` | `#10B981` | Positive returns, oversubscribed book, low risk |
| **Accent Amber** | `--accent-amber` | `#F59E0B` | Moderate risk, lock-in warning, NII undersubscription |
| **Accent Rose** | `--accent-rose` | `#F43F5E` | Valuation froth alert, negative alpha, covenant breach |
| **Accent Indigo** | `--accent-indigo` | `#6366F1` | Algorithmic comps tags, machine learning heads |

### 3.3 Typography Rules
- **Prose & Navigation**: `Inter`, `-apple-system`, `system-ui`, sans-serif. Clean, crisp, neutral.
- **Financial Figures & Tables**: `Fira Code`, `JetBrains Mono`, monospace.
- **Mandatory Constraint**: Every financial metric, percentage, currency value, and multiple MUST use `.tabular-nums` / `font-variant-numeric: tabular-nums` to guarantee vertical column decimal alignment.

---

## 4. Core Terminal Modules & Component Architecture

```mermaid
graph TD
    subgraph Terminal Shell
        TICKER["1. HeaderTicker.tsx (Live NSE Indices & Status)"]
        SIDEBAR["Navigation & Issuer Switcher (SidebarNav.tsx)"]
    end

    subgraph Central Canvas
        HERO["2. StatutoryOfferHero.tsx (Price Band, Lot, Dilution, RHP Links)"]
        BOOK["3. SubscriptionBookBar.tsx (QIB, NII, Retail Demand)"]
        COMPS["4. LivePeerCompsTable.tsx (52W Range, Comps Multiples)"]
        HUBER["5. HuberCalibrationCard.tsx (Bias Index & Froth %)"]
        ML["6. WalkForwardMLScorecard.tsx (Dual Heads & Recommendation)"]
        SHAP["SHAPWaterfallChart.tsx (Attribution Breakdown)"]
        AUDIT["7. SEBIComplianceStamp.tsx (SHA-256 Ledger Lock)"]
    end

    TICKER --> HERO
    SIDEBAR --> Central Canvas
    HERO --> BOOK
    HERO --> ML
    BOOK --> HUBER
    HUBER --> COMPS
    ML --> SHAP
    SHAP --> AUDIT
```

### 4.1 Module 1: `HeaderTicker.tsx`
- **Pulsing Status Beacon**: Emerald green live indicator reflecting WebSocket / HTTP session state to NSE India.
- **Streaming Index Strip**: Live quotes, point changes, percentage changes, and P/E ratios for:
  - `NIFTY 50`: Benchmark market sentiment.
  - `NIFTY FMCG` / Sector Index: Industry-specific valuation benchmark.
  - `INDIA VIX`: Volatility regime (< 15 Low Vol, 15–20 Normal, > 20 Elevated Risk).
- **Manual Sync Action**: Debounced refresh button initiating on-demand NSE quote harvesting.

### 4.2 Module 2: `StatutoryOfferHero.tsx`
- **Issuer Identity**: NSE Symbol, Company Name, Issue Type (Mainboard vs. SME), Bidding Dates.
- **Statutory Route Tag**: Regulation 6(1) (Net Tangible Assets & Profitability) vs. Regulation 6(2) (75% QIB Book Building).
- **Capital Structure Matrix**:
  - Price Band: Min ₹ to Max ₹ per equity share.
  - Market Lot: Exact lot size (e.g. 138 shares) with minimum application capital (₹14,904).
  - Issue Size: Total ₹ Cr, broken down into Fresh Issue share (%) and Offer for Sale (OFS) share (%).
  - Statutory Lock-In Timelines: 90 Days QIB Anchor (50% unlock) and 180 Days Pre-IPO Shareholder unlock.
- **Direct Regulatory Artifact Triggers**: One-click direct downloads for official **RHP ZIP** and **Anchor Book Allocation JSON**.

### 4.3 Module 3: `SubscriptionBookBar.tsx`
- **Segmented Category Demand Progress**: Real-time progress bars and multiples for:
  - Qualified Institutional Buyers (QIB) (Quota vs. Bids).
  - Non-Institutional Investors (NII / HNI).
  - Retail Individual Investors (RII).
  - Eligible Employees / Shareholders.
- **Total Capital Committed**: Aggregate shares bid and capital collected (₹ Cr).
- **Institutional Appetite Divergence Callout**: Automated analytical callout comparing QIB appetite against Retail leverage demand.

### 4.4 Module 4: `LivePeerCompsTable.tsx`
- **High-Density Tabular Comps**: Sortable by any column (Price, 1D %, P/E, EV/EBITDA, 3Y Rev CAGR, EBITDA %, ROCE, Market Cap).
- **Visual 52-Week Range**: Relative sparkline bar showing current quote position relative to 52W Low and 52W High.
- **Provenance Tagging**:
  - `DRHP DECLARED` (Cyan badge): Peer explicitly listed in the statutory prospectus.
  - `ALGO DISCOVERED` (Indigo badge): Unbiased peer discovered via multi-dimensional cosine feature similarity.

### 4.5 Module 5: `HuberCalibrationCard.tsx`
- **Huber Robust M-Estimator**: Regresses peer multiples using `HuberT(t=1.345)` to downweight extreme high-multiple outliers.
- **Key Forensic Metrics**:
  - Declared Peer Median P/E vs. Algorithmic Peer Median P/E.
  - **DRHP Peer-Selection Bias Index**: $\frac{\text{Declared Median}}{\text{Algorithmic Median}}$ (Flags upward comps manipulation).
  - **Warranted Fair P/E**: Regression-implied fair multiple based on issuer's actual restated fundamentals.
  - **Unbacked Valuation Froth**: Percentage premium demanded by upper price band over warranted fair value.
- **Covariate Significance Table**: Regression coefficients ($\beta$) and $t$-statistics ($|t| \ge 2.0$ significance) for Rev CAGR, EBITDA %, ROCE, and CFO/EBITDA.

### 4.6 Module 6: `WalkForwardMLScorecard.tsx` & `SHAPWaterfallChart.tsx`
- **Dual-Score Architecture**:
  - *Score 1 (Fundamental & Forensic Quality)*: 0–100 scale (Penalized by Sloan Accrual $> 10\%$, Beneish M-Score, and high froth).
  - *Score 2 (Pricing & Market Sentiment)*: 0–100 scale (Supported by Fresh Issue share, QIB subscription, and market regime).
- **Composite Institutional Rating**:
  - `STRONG_BUY_ALPHA`: Undervalued fundamental leader.
  - `TACTICAL_LISTING_ONLY`: Strong listing pop potential, high lock-in drawdown risk.
  - `HOLD_FOR_LOCK_IN_DIP`: Great business, overpriced issuance; buy post-lock-in.
  - `AVOID_HIGH_DRAWDOWN_RISK`: Fundamental red flags + valuation froth.
- **Dual Heads**:
  - *Head A (Classifier)*: $P(\text{BHAR}_{180\text{D}} > +10\%)$.
  - *Head B (Huber Regressor)*: Expected Month-6 Lock-in CAR $[-5\text{D}, +10\text{D}]$.
- **SHAP Waterfall Attribution**: Centered zero-axis horizontal bars explaining top 5 positive alpha contributors and top 5 negative risk penalties.

### 4.7 Module 7: `SEBIComplianceStamp.tsx`
- **Statutory Accreditation**: SEBI (Research Analysts) Regulations, 2014 Chapter III disclosure.
- **Cryptographic SHA-256 Digest**: Immutable report hash calculated from `Symbol + PriceBand + WarrantedP/E + Rating + Timestamp`.
- **One-Click Copy & Verification**: Copies raw hash to clipboard for institutional audit files.

---

## 5. Dual-Engine Architecture & Strangler Fig Topology

To preserve all 28 existing research pages without regression, ProfSur adopts the **Strangler Fig Gateway Topology**:

```
                                  Edge Cloud Run (Port 8080)
                                              │
                              FastAPI Primary Server (api/server.py)
                                              │
           ┌──────────────────────────────────┴──────────────────────────────────┐
           ▼                                                                     ▼
     Route: GET / and /api/...                                            Route: GET /research
     • Serves React 19 Pre-IPO Terminal (Static SPA)                      • Proxies Streamlit Shell (app.py)
     • Exposes NSE Live Feed & Huber APIs                                 • Stata Studio v2 (xtreg, reghdfe)
     • Zero server-side reruns (< 5ms response)                           • AI Assistant Chatbot (Page 19)
     • Obsidian / Midnight Slate Aesthetic                                • 8,677 CMIE observations
```

### 5.1 Single-Source-of-Truth Authentication Bridge
- **No Dual User Stores**: The existing [auth.py](file:///C:/Users/hemas/Downloads/ProfSurProject/auth.py) is already decoupled from Streamlit.
- **Auth Flow**:
  1. User authenticates via React login or Streamlit login modal.
  2. Credentials validated against `auth.db` using 12-round native bcrypt.
  3. Server sets an HTTP-Only, Secure, SameSite=Lax cookie: `ps_session` containing signed user credentials.
  4. Both FastAPI endpoints and Streamlit's `app.py` read the `ps_session` cookie; authenticating in one automatically authorizes the other.

### 5.2 Container Packaging: Multi-Stage Dockerfile
- **Build Stage (`node:22-alpine`)**:
  - Compiles React application (`npm ci && npm run build`).
  - Emits compressed static bundle to `frontend/dist`.
- **Runtime Stage (`python:3.12-slim` / existing base image)**:
  - Discards all Node.js/npm dependencies (zero image bloat).
  - Copies `frontend/dist` to `/app/frontend/dist`.
  - Mounts static files directly in FastAPI: `app.mount("/", StaticFiles(directory="frontend/dist", html=True))`.
  - Runs pure Python Uvicorn engine on port 8080.

---

## 6. Implementation Roadmap & Quality Gates

### 6.1 Phased Delivery Schedule

| Phase | Duration | Scope & Milestones | Exit Gate Criteria |
| :--- | :--- | :--- | :--- |
| **Phase 1: Local Proof of Concept** | Completed | Scaffold Vite + React 19 + Tailwind v4 + 7 Terminal Components. Build FastAPI server. | Playwright screenshots verified on disk; zero TS errors. |
| **Phase 2: Auth Bridge & Single Port** | 1.0 Day | Wire `auth.py` to `POST /api/auth/login`. Mount `frontend/dist` in FastAPI. | Single port `localhost:8000` serves React and validates auth without Vite dev server. |
| **Phase 3: Route-Split Docker Packaging** | 1.0 Day | Update `Dockerfile` to multi-stage build. Configure `/` for React and `/research` for Streamlit. | Container builds cleanly; image size $\le 1.2$ GB. |
| **Phase 4: Cloud Run Deployment & E2E** | 1.0 Day | Deploy to `tempproject-462219` (us-east1). Run authenticated Playwright smoke tests for all 4 user profiles. | Live Cloud Run URL verified with zero regressions across Stata and Pre-IPO. |

### 6.2 Mandatory Adversarial Quality Gates (`AGENTS.md`)
1. **Rule B (Ground Truth Verification)**: All test assertions must test authentic database observations ($N=8,677$) and regulatory filings (HCCH 513p DRHP, NTPC Green RHP), never synthetic blank-page fixtures.
2. **Rule E (Negative & Bypass Probing)**: API endpoints must fail closed:
   - Requesting market status with `symbol=None` or tampered query must return structured 400 Bad Request.
   - Missing authentication token must return 401 Unauthorized, never falling back to permissive defaults.
3. **Rule F (Evidence Gate)**: No deployment or feature shall be declared "done" without automated Chromium Playwright execution confirming live DOM rendering and physical screenshot verification on disk.

---

## 7. Open Architectural Decisions for Confirmation

1. **Top-Level Navigation Linkage**:
   - In the React Terminal, should the link to Streamlit be labeled *"Deep Econometrics & Stata Studio"* or *"Public Universe Research (8,600+ CMIE)"*?
2. **Default Workspace Landing Mode**:
   - When a user logs in at `https://lifecycle-leverage...`, should they land directly on the **React Modern Pre-IPO Terminal** (with a button to jump to Stata), or should they choose their initial workspace on login?
3. **NSE Live Feed Caching Window**:
   - To prevent Akamai IP throttling on Cloud Run, shall we set the NSE cache TTL to **60 seconds** or **120 seconds** during active market hours (09:15–15:30 IST)?
