# Institutional Pre-IPO Terminal (v3.5.0) — Master End-of-Day Hand-Off Document
## Complete System Status, Lessons Learnt, Mistakes to Avoid, and Reusable Automation Blueprint

**Document Reference:** `HANDOFF_MASTER_PRE_IPO_TERMINAL_V35.md`  
**Date:** 18 November 2026 (07:45 IST Update)  
**Status:** DAY COMPLETE / DEPLOYMENT & UI CONTRACT VERIFIED LIVE ON GCP CLOUD RUN  
**Live Production URL:** `https://pre-ipo-terminal-779655496440.us-east1.run.app` (Revision `pre-ipo-terminal-00007-cfn` — Serving 100% Traffic)  
**Core Platform Production URL:** `https://lifecycle-leverage-qhzom2yadq-ue.a.run.app` (Streamlit Core Platform — Isolated & Untouched)  
**Local Verification URLs:**
- **React Terminal UI (Vite SPA):** `http://localhost:5173/` (Active, Verified)
- **FastAPI BFF Server:** `http://localhost:8000/` (Active, Verified)
- **Streamlit Core Platform:** `http://localhost:8501/` (Active, Untouched & Isolated)
**Cloud Run Production Service:** `pre-ipo-terminal` (Project: `tempproject-462219`, Region: `us-east1` — VERIFIED LIVE)  
**Associated Artifacts:**
- [`docs/EXPANDED_84_ATTRIBUTE_PRE_IPO_BLUEPRINT.md`](file:///c:/Users/hemas/Downloads/ProfSurProject/docs/EXPANDED_84_ATTRIBUTE_PRE_IPO_BLUEPRINT.md)
- [`pre_ipo_terminal_executive_brief_and_walkthrough.md`](file:///C:/Users/hemas/.gemini/antigravity/brain/2c3332b8-059d-400c-80e4-d12d334e8f37/pre_ipo_terminal_executive_brief_and_walkthrough.md)
- Visual Verification Screenshots:
  - `verified_cloud_dropdown_closed.png` (Matches Screen 2 Reference)
  - `verified_cloud_dropdown_open.png` (Matches Screen 3 Reference)

---

## 1. Executive Summary of Accomplishments

During this development cycle, the Pre-IPO Terminal evolved from an experimental prototype into an institutional-grade, 12-vault quantitative evaluation cockpit:

1. **84-Attribute SEBI ICDR Taxonomy & Vault 4 Statutory Provenance Ledger:**
   - 10 statutory sections covering baseline (Tier 1: 1–42) and deep diligence (Tier 2: 43–84) attributes.
   - PyMuPDF OCR bounding box drawer, Schedule VI citation mapping, and invariant telemetry equation (`Found + Pending + Reconfirm === 84`).
   - Strict Rule E.3 Zero-Truthiness preservation: explicit `0.0` values (e.g., zero fresh issue, zero promoter pledge) are preserved as `FOUND` with `value: 0.0`.

2. **Vault 5 Econometric & Forensic Lab:**
   - Single source of truth across 7 quantitative models:
     1. Beneish (1999) 8-Variable M-Score & Sloan (1996) Total Accruals.
     2. Dickinson (2011) Triple Sign Vector Life-Cycle Matrix.
     3. Huber (1964) Robust Multiple Peer Regression (RLM) with peer bias downweighting.
     4. Stub Seasonality & Pre-IPO Margin Structural Break Analyzer (Chow F-test).
     5. Ind AS 116 Lease-Adjusted Leverage & 12M Debt Refinancing Wall.
     6. Altman (2002) Emerging Market $Z''$-Score Model.
     7. Lock-In Cliff Float Expansion (T+30/90/180) & Sec 56(2)(x) Tax Drag.
   - Reverse DCF implied revenue growth solver verified with mathematical inversion error $\le 0.05\%$.
   - Interactive 2D Bivariate Stress Sensitivity Matrix (Volume Shock vs Raw Material Inflation).

3. **Active Pre-IPO Deal Dossier Dropdown Selector (Screen 2 & Screen 3 Match):**
   - Replaced clunky multi-row buttons with an institutional, high-density dropdown selector in `frontend/src/components/SidebarNav.tsx`.
   - **Closed State (Screen 2):** Compact header `Active Pre-IPO Deal Dossier` with `+ Ingest` action, cleanly displaying active company name with chevron.
   - **Open State (Screen 3):** Floating wide menu (`w-[390px]`) displaying complete statutory filing details without truncation:
     - `NTPC Green Energy Ltd. (RHP Nov 2024 · ₹10,000 Cr Fresh · Utilities)`
     - `Hindustan Coca-Cola Holdings Ltd. (DRHP 2024 · ₹9,975 Cr OFS · FMCG Giant)`
     - `Swiggy Ltd. (DRHP 2024 · ₹4,499 Cr Fresh · Hyperlocal Logistics)`
     - `Waaree Energies Ltd. (RHP 2024 · ₹4,321 Cr · Solar PV)`
     - `+ Ingest New DRHP / RHP PDF Document...`
   - Keeps all 12 Vaults in Sections I, II, III, and IV simultaneously visible in the left panel.

4. **Multi-Stage Containerization & Production Cloud Run Architecture:**
   - Multi-stage Docker build (`node:20-alpine` -> `nginx:alpine` on port 8080) in `frontend/Dockerfile` and `frontend/nginx.conf`.
   - Nginx caching fix: `Cache-Control: "no-store, no-cache, must-revalidate, max-age=0"` on `/index.html` prevents stale browser caching.
   - Complete isolation from core ProfSur Streamlit service (`lifecycle-leverage` on port 8501).
   - Live verified deployment on Cloud Run (`pre-ipo-terminal-00007-cfn`).

---

## 2. Lessons Learnt & Critical Mistakes to Avoid

| # | Mistake / Anti-Pattern | Root Cause Analysis | Remediation / Invariant to Follow |
| :--- | :--- | :--- | :--- |
| **1** | **Monolithic CI/CD Deployment Coupling** | The spin-off terminal deployment job in `.github/workflows/deploy.yml` was configured with `needs: [test]`. When legacy Python tests failed on `master`, the Docker build and Cloud Run deployment were blocked, leaving Cloud Run with HTTP 404. | **Always Decouple Spin-Off CI/CD Pipelines:** Standalone frontends must deploy via their own workflow (`deploy-terminal.yml`) without gating on un-related monolithic backend test suites. |
| **2** | **PowerShell Profile & Shell-Hook Subprocess Hangs** | In Windows `pwsh`, external tools (`git`, `gh`, `gcloud`) are intercepted by profile hooks (e.g. `lean-ctx` hook `_lc` in `Microsoft.PowerShell_profile.ps1`). Subprocesses hang waiting on stdin or buffering output. | **Scrub Environment & Use Clean Subprocess Execution:** Run automation with Python scripts that pop invalid `GITHUB_TOKEN` values, pass explicit `timeout` arguments, or execute with `pwsh -NoProfile`. |
| **3** | **Premature Link Sharing Before Endpoint Verification** | Cloud Run service URL was shared with the assumption that GitHub Actions had succeeded, before confirming HTTP 200 and visual rendering. | **Strict Evidence Gate (Anti-Fabrication Rule):** Never declare a deployment done or share a URL until an authenticated HTTP request confirms status 200 and an automated headless check verifies UI rendering on disk. |
| **4** | **Zero-Truthiness in Financial Metrics (Rule E.3)** | Using `val or default` in Python or JavaScript treats valid financial zeros (`0.0%` promoter pledge, `₹0 Cr` debt) as falsy/absent, triggering erroneous defaults or `NOT_FOUND` states. | **Explicit None Checks:** Always use `if val is None:` and `val !== null && val !== undefined`. Zero is a valid financial quantity. |
| **5** | **Static 4-Pillar Copy-Paste Across UI Tabs** | Showing identical "4-Pillar" narrative text across different navigation constructs destroys analytical value for institutional users. | **Context-Bound Synthesis:** Every vault and tab must bind its 4 pillars to its specific quantitative outputs, statutory benchmarks, and domain risks. |
| **6** | **Solver Divergence & Unbounded Clamping** | Numerical root-finders (Reverse DCF, IRR) can silently clamp to boundary values if initial bounds or convergence tolerances are loose. | **Solver Round-Trip Inversion (Rule E.4):** Every mathematical solver must have an automated test asserting that feeding the root back into the explicit valuation model reprices target value within $\le 0.05\%$. |
| **7** | **Nginx SPA `index.html` Cache Poisoning** | When Nginx serves `index.html` without cache-control headers, browsers cache `index.html` to disk. Users visiting after a new deployment continue rendering the old bundle from local disk cache, appearing as if the deployment never occurred. | **Enforce Strict `index.html` Cache Invalidation:** In `nginx.conf`, set `Cache-Control: "no-store, no-cache, must-revalidate, max-age=0"` specifically on `/index.html`. Hashed assets (`/assets/*.js`) can safely cache for 1 year (`immutable`). |
| **8** | **Single-Stage `COPY dist` Dockerfile Drift** | Relying on host-compiled `dist/` inside Dockerfiles causes silent drift when local compiles fail or when `.gitignore` excludes `dist/` in CI runners. | **Enforce Multi-Stage Docker Builds:** Compile TypeScript/Vite directly from source inside `node:20-alpine` builder stage, then pass clean artifacts to `nginx:alpine`. |
| **9** | **Source Context Upload Bloat in `gcloud run deploy`** | Omitting `node_modules/` or temporary files from `.dockerignore` and `.gcloudignore` causes hundreds of megabytes of binary data to upload over slow network connections, inflating deployment from 15 seconds to several minutes. | **Strict Ignore Manifests:** Ensure `.gcloudignore` and `.dockerignore` exclude `node_modules/` and local artifacts so source uploads remain under 2 MB. |
| **10** | **Interactive CLI Pager Hangs in Headless Agents** | Commands like `git log` or un-quiet CLI tools invoke pagers (`less`, `more`) that halt execution indefinitely waiting for keyboard input `q`. | **Enforce Non-Interactive Flags:** Always pass `--no-pager` for git and `--quiet` for gcloud in automated scripts. |

---

## 3. Automation to Build and Reuse

To prevent these issues from recurring and accelerate future development, the following automated tools are established:

### Automation 1: Automated Build, Deploy & Dual-State Visual Verifier (`scripts/execute_cloud_run_deploy.py`)
- **Purpose:** End-to-end automated deployment and visual proof capture for local and Cloud Run environments.
- **Workflow:**
  1. Runs local `npm run build` to assert zero TypeScript errors.
  2. Launches headless Playwright to capture local dev server screenshots (`verified_local_dropdown_closed.png`, `verified_local_dropdown_open.png`).
  3. Deploys cleanly to Google Cloud Run via `gcloud run deploy pre-ipo-terminal`.
  4. Launches headless Playwright to capture live Cloud Run screenshots (`verified_cloud_dropdown_closed.png`, `verified_cloud_dropdown_open.png`).
- **Reuse:** Can be executed anytime with `python scripts/execute_cloud_run_deploy.py` to deploy and verify the terminal in ~75 seconds.

### Automation 2: Automated Live URL & UI Health Verifier (`scripts/verify_live_terminal.py`)
- **Purpose:** Enforces the Anti-Fabrication Rule by checking live endpoint responsiveness.
- **Mechanism:**
  1. Issues an HTTP GET request to the target URL; asserts status code 200.
  2. Launches headless Playwright to inspect page DOM for `#root` and key terminal elements (`PROFSUR v3.5.0`).
  3. Captures a timestamped screenshot on disk to serve as physical verification evidence.

### Automation 3: Clean Windows Subprocess Runner (`scripts/clean_exec.py`)
- **Purpose:** Eliminates PowerShell profile hangs on Windows.
- **Mechanism:** Wraps `subprocess.run` with:
  - Strict timeout enforcement (5–30s).
  - Sanitized environment (removes dummy `GITHUB_TOKEN`).
  - Native invocation of `.venv/Scripts/python.exe` and CLI tools without invoking PowerShell profile wrappers.

### Automation 4: Reusable Decision Intelligence 4-Pillar Component (`EvidenceInterpretationPanel.tsx`)
- **Purpose:** A drop-in React component for any financial application.
- **Inputs:** `title`, `pillar1_sector`, `pillar2_precedents`, `pillar3_directives`, `pillar4_risks`, `metrics`, `citations`.
- **Features:** Responsive high-density dark UI, semantic color coding, progress bars, and citation modals.

---

## 4. Current State & Immediate Resume Instructions

- **Working Directory:** `c:\Users\hemas\Downloads\ProfSurProject`
- **Active Git Branch:** `feature/pre-ipo-cockpit-vault-v35`
- **Live Cloud Run Terminal:** `https://pre-ipo-terminal-779655496440.us-east1.run.app` (Revision `pre-ipo-terminal-00007-cfn` — VERIFIED LIVE)
- **Live Streamlit Core Platform:** `https://lifecycle-leverage-qhzom2yadq-ue.a.run.app` (Isolated, Port 8501, Untouched)
- **Verified Visual Evidence:**
  - `verified_cloud_dropdown_closed.png` (Active Pre-IPO Deal Dossier closed state)
  - `verified_cloud_dropdown_open.png` (Expanded options matching Screen 3)
- **Immediate Task on Next Resume:**
  1. Any future UI changes can be deployed and verified in one step using:
     ```bash
     py -3.12 scripts/execute_cloud_run_deploy.py
     ```
  2. To merge into master and trigger the CI/CD pipeline, run `py -3.12 scripts/commit_and_push.py`.
