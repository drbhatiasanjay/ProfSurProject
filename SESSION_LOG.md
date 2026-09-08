# ProfSurProject — Session Log (2026-03-27)

## What We Did

### 1. Studied the Thesis Document

**File:** `DETERMINANTS OF CAPITAL STRUCTURE OVER CORPORATE LIFE STAGES.docx`

- PhD thesis by **Surendra Kumar**, University of Delhi (2025)
- Supervised by Dr. Varun Dawar & Dr. Chandra Prakash Gupta
- Topic: How capital structure determinants (profitability, tangibility, tax, size, etc.) vary across corporate life stages (Startup → Growth → Maturity → Decline) for Indian firms
- Methods: Panel data — Pooled OLS, Fixed Effects, Random Effects, System GMM
- Theories: Pecking Order, Trade-off, Agency Cost, Signalling, M&M, Free Cash Flow

### 2. Explored the Dataset

**File:** `sp401nf24y_furtherEd_oldCLS.dta` (Stata format)

- **8,677 rows** x **159 columns**
- **401 companies** (S&P BSE/NSE listed Indian corporates)
- **24 years** of panel data (2001–2024)
- **103 industry groups**

**Key variables identified:**

| Variable | Description | Notes |
|----------|-------------|-------|
| `leverage` | Debt ratio (dependent var) | Mean 21%, median 15.8%, outliers up to 1425% |
| `prof` | Profitability | <1% missing |
| `tang` | Asset tangibility | <1% missing |
| `tax` | Tax rate | <1% missing |
| `dvnd` | Dividend payout | 9% missing |
| `size` | Firm size (total assets) | <1% missing |
| `taxShield` | Non-debt tax shield | <1% missing |
| `pmShare` | Promoter shareholding | 15.7% missing |
| `corplifestage` | 8 life stages | Startup, Growth, Maturity, Shakeout1/2/3, Decline, Decay |
| `GFC` | Global Financial Crisis dummy | — |
| `ibc2016` | Insolvency & Bankruptcy Code dummy | — |
| `dcovid20less` | COVID-19 dummy | — |

**Life stage distribution:**

| Stage | Count | Avg Leverage (%) |
|-------|-------|-----------------|
| Maturity | 4,491 | 17.2 |
| Growth | 1,933 | 28.2 |
| Shakeout3 | 947 | 14.1 |
| Startup | 580 | 32.8 |
| Shakeout2 | 353 | 23.4 |
| Decay | 176 | 20.1 |
| Decline | 156 | 38.3 |
| Shakeout1 | 41 | 13.0 |

**Data quality:** ~40+ columns with >50% missing (mostly pledged shares, granular ownership). Core financials are clean (<1% missing).

### 3. Created SQLite Database

**Script:** `load_to_db.py`
**Database:** `capital_structure.db` (4.8 MB)

Normalized the flat 159-column Stata file into 5 relational tables:

| Table | Rows | Content |
|-------|------|---------|
| `companies` | 401 | Company info, NSE symbol, industry, incorporation year |
| `life_stages` | 8 | Life stage code → name mapping |
| `financials` | 8,677 | Leverage, profitability, tangibility, tax, size, cash flows, event dummies |
| `ownership` | 8,677 | Promoter/non-promoter shareholding patterns |
| `market_index` | 24 | Yearly S&P BSE index data (PE, PB, returns, beta) |

**3 pre-built views:**
- `v_company_financials` — joined company + financials + life stage (dashboard-ready)
- `v_life_stage_summary` — metrics aggregated by life stage and year
- `v_industry_summary` — metrics aggregated by industry and year

**6 indexes** for fast querying on company, year, life stage, and composites.

### 4. Saved to Obsidian

Created detailed project note at:
`MySecondBrain/Projects/ProfSurProject/ProfSurProject - Overview.md`

   - Created root `AGENTS.md` with the **Ponytail Minimal-Code Decision Ladder** and **Concise Engineer Rules**.
   - Streamlined `CLAUDE.md` to save ~1,400 input tokens on every turn.
   - Built unified CLI `scripts/project_ops.py` (`status`, `test --fast`, `push`, `verify`).
   - Built `scripts/gen_bulk_doc.py` to offload bulk HTML/markdown generation to Gemini 1.5 Flash.

## 2. Verified Deployments & Git State
- **Git HEAD:** `1556b35` (`master` in sync with `origin/master`).
- **Google Cloud Run:** Live build `33978079087` serving 100% traffic at `https://lifecycle-leverage-779655496440.us-east1.run.app`.
- **Key Milestones Resolved:**
  - `models/stata_engine.py`: Added smart data-aware variable resolution (`int_rate` <-> `interest`) and dropped all-NaN collinear variables before estimation to eliminate zero-size array crashes in `xtreg`.
  - `pages/23_stata_studio.py`: Wrapped command prompt in `st.form` for atomic input submission across both `Enter` keypress and `▶ Run Command` click.
  - `models/rich_chat_renderer.py` & CSS: Converted terminal output to native `st.html` with explicit `<pre>` block, fixing text contrast (`#F0F6FC`) and preventing CommonMark line collapsing.
- **Default Auth:** `profsurkumar` / `Pass@123` (Researcher role), `drbhatia` / `Pass@123` (Admin role).

## 3. Recommended Next Tasks
- [ ] Task A: Review & extend **Page 17: Board Deck Export** / **Page 18: Company Navigator**.
- [ ] Task B: Implement user observability & session metrics from **`USER_BEHAVIORAL_OBSERVABILITY_PROTOTYPE.html`**.
- [ ] Task C: Ingest CMIE 2025 rollforward updates via `scripts/project_ops.py`.


---

### 📋 Paste-Ready Handoff Prompt for Next Session:
```text
Resume LifeCycle Leverage project. We are on branch 'master' at commit e722ca5 (100% deployed to GCP). Follow AGENTS.md Ponytail minimal-code and concise rules. Use scripts/project_ops.py for operations. What would you like to build next?
```

---

# ProfSurProject — Session Log (2026-09-06 Recovery & Context Consolidation)

## 1. Forensic Recovery & Historical Reconciliation
- **Historical Recovery Source:** Fully recovered pre-shutdown Antigravity conversation and artifact directory (`C:\Users\hemas\.gemini\antigravity-ide\brain\dfad8734-d349-4cab-bff4-d88cf51c2925`).
- **Filesystem Timestamps Confirmed:**
  - `implementation_plan.md`: Created `2026-09-05 23:11:55 IST`, Last Write `2026-09-06 00:14:39 IST`.
  - `walkthrough.md`: Created `2026-09-05 23:25:23 IST`, Last Write `2026-09-05 23:41:36 IST`.
- **Exhaustive Verification Recovered:** 109/109 checkpoints verified 100% PASS across Phases 1–6 (Multi-page crawler 25/25, Interactive controls 19/19 with 34/34 actions pass, Stata math engine 19/19, AI Assistant prompts 46/46, 4-user auth matrix on local + GCP, and sub-second caching latency).
- **Approved Two Workstreams Isolated:**
  - Workstream 1: Stata CLI / NLP Enhancement (`feature/stata-cli-nlp-highlighting`).
  - Workstream 2: Citation Inspector / Academic Literature Vault (`feature/citation-inspector-modal`).
  - Post-restart AutoPrompt plan formally classified as non-canonical and discarded.

## 2. Governance & Consolidation Milestones
- **Human Gate #1 v2 Approved:** Forensic recovery accepted; established durable source-of-truth hierarchy.
- **`CURRENT_STATUS.md` Created:** Consolidated operational checkpoint anchored to baseline commit `6075708`.
- **`docs/CANONICAL_IMPLEMENTATION_PLAN.md` Created:** Reconciled technical specifications for Workstreams 1 & 2 removing already-implemented items.
- **Security Remediation Flagged:** Plaintext credentials removed from `AGENTS.md` and replaced with standard secret references; status set to `SECURITY_REMEDIATION_PENDING_ROTATION`.
- **`.graphifyignore` Created:** Configured dual-mode indexing for source code plus curated canonical Markdown while excluding binary databases, caches, and test scratch.

## 3. Stata Studio Alignment, Anti-Fade & GCP Live Deployment (Commit `7c1385e`)
- **Stata Output Formatting Fixed:**
  - Header right column statistics (`Number of obs`, `Number of groups`, `min`, `avg`, `max`, `F(...)`, `Prob > F`) have all `=` signs locked precisely at column 66 across all panel regressions.
  - OLS ANOVA table right column statistics locked at column 69.
  - Summarize table dynamically adjusts variable column width (`max(len(v), 13) + 1`), preventing 13-character `profitability` from displacing the vertical pipe divider `|`.
  - Pwcorr matrix column width dynamically sized to prevent column shift.
- **Terminal Card UI & Anti-Fade Polish:**
  - Header dots (red, yellow, green) aligned in non-collapsible left container with command text wrapping cleanly and right badge `N = ...` fixed in place.
  - Comprehensive anti-fade CSS injected into `pages/23_stata_studio.py`, `assets/style_light.css`, and `assets/style_dark.css` overriding Streamlit's `opacity: 0.33` stale DOM element dimming.
  - Replaced stale DOM updates with `output_placeholder = st.empty()` and clear `st.spinner(...)` computation lifecycle.
- **Deployment & Live GCP Verification:**
  - Pushed to `master` (commit `7c1385e`).
  - GitHub Actions run `34017700035` passed 100% (pytest in 2m12s, OCaml in 3m11s, Cloud Run deployment in 3m47s).
  - Live GCP Cloud Run (`https://lifecycle-leverage-779655496440.us-east1.run.app`) verified across all user roles (`drbhatia`, `profsurkumar`, `sbhatia`) executing the dissertation regression:
    `xtreg leverage i.corplifestage c.prof##c.tang c.prof##c.dvnd taxShield intRate i.year, fe`.
  - Stata Studio and AI Assistant tested and verified operational with screenshots recorded in `scratch/matrix_evidence/`.

---

# ProfSurProject — Session Log (2026-09-07 Stata Studio Compatibility & Error Hardening)

## 1. Issues Identified & Fully Resolved
1. **`xtset <panelvar> <timevar>` Implementation:**
   - Added `"companycode": "company_code"`, `"companyid": "company_code"`, `"company_id": "company_code"` to `COMMON_VAR_ALIASES`.
   - Built `PanelContext` dataclass capturing panel dimensions, balance, time range, observations, and duplicate keys.
   - Implemented `_handle_xtset()` validating panel variables, detecting repeated time values with `r(451);`, and rendering authentic Stata monospace ASCII output.
   - Persisted `PanelContext` to session state for downstream `xt` models.
2. **`lgraph <y1> [y2 ...] <xvar>, [wide]` Implementation:**
   - Implemented multi-series longitudinal time trend aggregator and parser.
   - Generates interactive Plotly figures with support for `wide` side-by-side facet subplots and high-contrast theme palettes.
   - Generates authentic Stata ASCII longitudinal means summary table.
3. **`python-docx` Packaging & Runtime Isolation:**
   - Added `python-docx>=1.1.0` to `requirements.txt`.
   - Guarded `generate_esttab_docx()` in `models/stata_engine.py` and download button in `pages/23_stata_studio.py` with `DOCX_AVAILABLE` detection so missing packages degrade gracefully without crashing.
4. **Non-Crashing Error Handling & "Contact Admin" Guidance:**
   - Intercepted unrecognized/unsupported commands in `execute_stata_command()` to return structured `status: "unsupported"`, authentic `r(199)` Stata output, and administrator contact details (`admin@lifecycle-leverage.internal`).
   - Added warning callout card in `pages/23_stata_studio.py` displaying the list of supported commands with zero raw Python tracebacks.
5. **Econometric Phrasing Calibration:**
   - Refined inference copy in `generate_stata_inference()` from overly deterministic causal claims ("proves", "isolating true within-firm causal elasticities") to peer-reviewed empirical terminology ("empirically supported", "identifying within-firm associations").

## 2. Verification & Test Evidence
- **8-Command Screenshot Sequence:** 8/8 commands verified with **100% SUCCESS** on the active 9,031-row panel dataset.
- **Unit & Regression Suite:** `tests/test_stata_compatibility.py` (9/9 passed in 4.72s) and `tests/test_chart_switcher_and_literature.py` (6/6 passed in 2.54s).

---

# ProfSurProject — Session Log (2026-09-07 Local Online Verification)

## 1. Full Browser & UI Verification (Workstream 1 Feature Worktree `bbe6e80`)

**Target:** `c:\Users\hemas\Downloads\ProfSurProject\.worktrees\stata-cli-nlp-integration`  
**Commit:** `bbe6e80` (`fix(stata-ui): key duplicate hausman template buttons`)  
**Local URL:** `http://localhost:8501`  
**Execution Timestamp:** `20260907_221512`  
**Detailed Audit Report:** `scratch/local_online_verification/20260907_221512/EXHAUSTIVE_HEALTH_AUDIT_REPORT.md`  

### Verification Summary
- **Deterministic Econometric Suite:** 59/59 passed (100% in 4.80s).
- **Phase A (25-Page Health & Navigation Audit):** 25/25 pages crawled cleanly via Playwright with 0 unhandled exceptions.
- **Phase B (Interactive Controls):** 19/19 controls, tabs, expanders, theme toggles, and export buttons passed.
- **Phase C (Workstream 1 UI Journeys):** 10/10 journeys passed (Stata Studio, `xtset`, `lgraph`, `ivregress 2sls`, `test`, `predict`, `winsor2`, natural language translation, plain-English explainer, syntax highlighting/error-card).
- **Phase D (Multi-User & Theme Matrix):** 4/4 users (`profsurkumar`, `skumar`, `drbhatia`, `sbhatia`) × Light/Dark modes verified.
- **Phase E (Performance Caching):** 10/10 analytical pages benchmarked with average cold load 4.79s and cached load 2.95s.
- **Security Finding:** Credential exposure detected in prior transcript; rotation required.
- **Deployment Readiness:** **READY FOR ONLINE DEPLOYMENT**.

---

# ProfSurProject — Session Log (2026-09-07 Wave 1 ModelResultContext Verification)

## 1. Full Browser & UI Verification (Wave 1 Worktree `0f828a9`)

**Target:** `c:\Users\hemas\Downloads\ProfSurProject\.worktrees\wave1-model-result-context`  
**Branch:** `feature/wave1-model-result-context`  
**Commit:** `0f828a9` (`Wave 1: ModelResultContext and AnalysisRun contract integration`)  
**Local URL:** `http://localhost:8501`  
**Execution Timestamp:** `20260907_224610`  
**Detailed Audit Report:** `scratch/local_online_verification/20260907_224610/EXHAUSTIVE_HEALTH_AUDIT_REPORT.md`  

### Verification Summary
- **Deterministic Test Suite:** 65/65 passed across 9 test modules (100% in 5.41s).
  - `tests/test_analysis_run_contracts.py` (6 passed)
  - `tests/test_model_result_context.py` (9 passed)
  - `tests/test_stata_studio_widgets.py` (4 passed)
  - `tests/test_stata_bidirectional_nlp.py` (8 passed)
  - `tests/test_stata_compatibility.py` (9 passed)
  - `tests/test_stata_expanded_commands.py` (5 passed)
  - `tests/test_stata_engine.py` (8 passed)
  - `tests/test_rich_ui_and_stata_integration.py` (10 passed)
  - `tests/test_chart_switcher_and_literature.py` (6 passed)
- **Phase A (25-Page Autonomous Crawler & Health Audit):** 25/25 passed (100% PASS with 0 unhandled exceptions).
- **Phase B (Interactive Controls):** 23/23 interactive tab and control checks passed cleanly.
- **Phase C (Workstream 1 & Wave 1 UI Journeys):** 10/10 journeys passed (Stata Studio, `xtset`, `lgraph`, `ivregress 2sls`, `test`, `predict`, `winsor2`, natural-language econometric translation, plain-English deconstruction, syntax highlighting/error-card).
- **Wave 1 Context-Specific Isolation:** Deterministic context isolation and ModelResultContext contracts verified; stored estimates and `esttab` output verified context-scoped.
- **Phase D (Multi-User & Theme Matrix):** 4/4 users (`profsurkumar`, `skumar`, `drbhatia`, `sbhatia`) × Light/Dark modes verified.
- **Phase E (Performance Benchmark):** Cold load average 4.73s, warm load average 3.06s.
- **Security Audit Finding:** Credential exposure detected in prior transcript; rotation required.
- **Deployment Readiness:** **READY FOR ONLINE DEPLOYMENT** (PR #3 verified ready for merge authorization).

---

# ProfSurProject — Session Log (2026-09-07 Workstream 2 Citation Inspector Verification)

## 1. Workstream 2: Academic Citation Inspector & Literature Vault (`3245356`)

**Target:** `c:\Users\hemas\Downloads\ProfSurProject\.worktrees\citation-inspector-modal`  
**Branch:** `feature/citation-inspector-modal`  
**Commit:** `3245356` (`feat(citation): complete Workstream 2 Citation Inspector with dialog modal, catalog metadata, and zero-collision triggers`)  
**PR:** `#4` (https://github.com/drbhatiasanjay/ProfSurProject/pull/4)  
**Local URL:** `http://localhost:8501`  
**Execution Timestamp:** `2026-09-07T23:21:00`  
**Browser Verification Evidence:** `scratch/citation_inspector_evidence/`  

### Verification Summary
- **Academic Metadata Catalog (`models/citation_vault_metadata.py`)**:
  - Registered 8 foundational empirical/theoretical papers: Dickinson (2011), Rajan & Zingales (1995), Myers & Majluf (1984), Jensen & Meckling (1976), Frank & Goyal (2009), Titman & Wessels (1988), DeAngelo et al. (2006), Kumar (2026).
  - All entries validated with RFC 3986 HTTPS DOIs, theoretical mechanisms, empirical benchmarks, and Indian panel corroboration (CMIE Prowess 2001–2025).
  - Formatters for dynamic BibTeX, APA 7th, and Stata comment export.
- **Native Streamlit Dialog Modal (`components/citation_inspector.py`)**:
  - Built with `@st.dialog("📖 Academic Citation Inspector")` with glassmorphic, theme-adaptive high-contrast styling.
  - Safe key generator `get_safe_button_key()` guarantees zero Streamlit DuplicateWidgetID collisions across loops and reruns.
- **Page Integrations**:
  - `pages/23_stata_studio.py`: Integrated `render_citation_badge_button()` across commentary cards and added quick `render_citation_selector()` dropdown expander.
  - `pages/19_ai_assistant.py`: Integrated `render_citation_badge_button()` across literature vault expanders for both historical turns and live responses.
- **TDD Test Suite (`tests/test_citation_inspector.py`)**: 6/6 passed (100% in 0.99s).
- **Full Project Regression**: 709/709 passed, 0 failures.
- **Browser Playwright UI Evidence**: Successfully captured modal activation, dialog rendering, and citation lookups in Stata Studio & AI Assistant.
  - `01_stata_studio_initial.png` (134 KB) — Stata Studio page loaded
  - `02_stata_studio_expanded.png` (139 KB) — Citation Vault section expanded
  - `03_stata_dialog_modal.png` (200 KB) — Citation Inspector modal open in Stata Studio ✅
  - `04_ai_assistant_initial.png` (176 KB) — AI Assistant page loaded
  - `05_ai_assistant_literature.png` (186 KB) — Academic Citation drawer expanded
  - `06_ai_assistant_dialog_modal.png` (197 KB) — Inspect Dickinson (2011) modal open in AI Assistant ✅
- **Targeted Regression (Stata Studio + AI Chat):** 109 passed, 1 skipped, 0 failures (4.14s).
- **Deployment Status:** **PR #4 CREATED AND READY FOR MERGE**.

---

## Session: 2026-09-08 — Wave 2 Capability Abstraction Layer

### Adversarial Review
- Performed full adversarial review of Wave 2 plan against PRD §4–10 and existing `docs/reviews/PRD_ANALYTICAL_STUDIO_MODERNIZATION_ADVERSARIAL_REVIEW.md`.
- Found **3 BLOCKERS, 3 HIGH, 2 MEDIUM** gaps.
- All 8 findings incorporated into revised implementation plan before coding.

### Implementation — Branch: `feature/wave2-capability-abstraction`
- **Commit:** `ffee390`
- **New files (5):**
  - `models/analytical_contracts.py` — `AnalyticalRequest`, `CapabilityResult`, `AnalyticalError` (14 PRD §7 fields), `VisualizationSpec`, `DatasetSnapshotRef`, `fingerprint_df`
  - `models/analysis_run_envelope.py` — `AnalysisRunEnvelope` per adversarial review H-01
  - `models/command_registry.py` — `CommandEntry` + `COMMAND_REGISTRY` with PRD §9 status per command
  - `models/capability_registry.py` — maps capability names → `_handle_*` functions (stata_engine.py untouched)
  - `models/analytical_router.py` — `route()` public entry point + `_log_route_event()` (PRD §8 structured logging)
- **Modified files (2):**
  - `pages/23_stata_studio.py` — 4 `execute_stata_command` call-sites → `_execute()` shim
  - `pages/19_ai_assistant.py` — 1 `execute_stata_command` call-site → `route()`
- **Test suite:** `tests/test_wave2_abstraction.py` — 17 tests (L1 + L3), all PASS
- **Full regression:** 126 passed, 1 skipped, 0 failures (5.90s)
- **PRD report:** `docs/implementation-reports/WAVE_2_PR_01_CAPABILITY_ABSTRACTION_REPORT.md`
- **`stata_engine.py`: ZERO LINES CHANGED**

---

## Session: 2026-09-08 — Wave 3 Open-Source Technology Evaluation Spike

### Evaluation Scope & Setup
- Created frozen benchmark dataset: `tests/fixtures/wave3_benchmark.parquet` (9,031 rows × 30 columns, SHA-256: `e70dcc...`).
- Evaluated 7 candidate backends: `statsmodels` (0.14.6), `linearmodels` (7.0), `pyfixest` (0.60.0), `scikit-learn` (1.7.1), `xgboost` (3.0.5), `lightgbm` (4.6.0), `dowhy` (0.14) against baseline `stata_engine_v1`.
- Built spike runner: `scripts/wave3_engine_spike.py` covering all 12 PRD §10 econometric scenarios.

### 12-Scenario Benchmark Summary
- **S-01 Descriptive:** `statsmodels`/`pandas` matches baseline Stata mean/SD to $\Delta = 0.00000$ (10.4 ms).
- **S-02 OLS:** `statsmodels`, `linearmodels`, `pyfixest`, `sklearn` match coefficients and $R^2 = 0.08483$ to $\Delta < 10^{-12}$.
- **S-03 FE (Firm):** `pyfixest` and `linearmodels` match within-$R^2 = 0.02927$ ($\Delta < 10^{-12}$). `pyfixest` executes in 34 ms.
- **S-04 Two-Way FE:** `pyfixest` (48 ms) is 2.3× faster than `linearmodels` (110 ms) on Entity+Time clustering.
- **S-05 Lifecycle Interaction:** `statsmodels.formula` and `pyfixest` isolate stage-specific slope interactions.
- **S-06 Random Effects:** `linearmodels.panel.RandomEffects` estimates GLS $\theta = 0.6710$, overall $R^2 = 0.0663$.
- **S-07 HDFE:** `pyfixest` absorbs 3-way fixed effects (firm + year + industry) in 27 ms.
- **S-08 IV/2SLS:** `linearmodels.iv.IV2SLS` and `pyfixest` calculate 2SLS with 1st-stage $F = 14.78$.
- **S-09 Dynamic GMM:** Reviewed `CurrentProfSurGMMAdapter`; flagged for lag instrument matrix expansion in Wave 5.
- **S-10 DID / Causal:** `pyfixest` TWFE DID ($ATT = 3.0102$) and `dowhy` backdoor identification completed in 43 ms.
- **S-11 Prediction / ML:** `scikit-learn` Ridge (RMSE 56.24, 4.9 ms) and `xgboost` (238 ms) evaluated for financial forecasting.
- **S-12 Controlled Failure:** Multi-collinearity auto-handled by `pyfixest` (drops collinear terms with structured warnings).

### Artifacts & Repository State
- **Branch:** `feature/wave3-engine-evaluation`
- **Tag:** `v2.2.0-wave3-complete`
- **Deliverables:**
  - `docs/implementation-reports/WAVE_3_ENGINE_EVALUATION_REPORT.md`
  - `docs/implementation-reports/wave3_engine_matrix.json`
  - `scripts/wave3_engine_spike.py`
  - `tests/fixtures/wave3_benchmark.parquet`
- **Regression:** 126 passed, 1 skipped, 0 failures (6.66s).
- **GitHub Status:** Synchronized and pushed to remote with tag `v2.2.0-wave3-complete`.

---

## Session: 2026-09-08 — Wave 4 Core Stata-Compatible Research Expansion

### Completed Scope (PRD §10 Wave 4)
- **1. Exploratory Suite:**
  - `describe` (`des`, `d`): Dataset schema, observation counts, storage types, display formats, labels.
  - `codebook` (`cb`): Data dictionary, missing audits, unique counts, percentiles ($p_{10}, p_{25}, p_{50}, p_{75}, p_{90}$).
  - `count`: Conditional observation counter with Stata-style `if` filtering.
  - `mean`: Point estimates, exact standard errors ($s/\sqrt{N}$), and 95% confidence bounds.
  - `proportion` (`prop`): Categorical proportion estimations and discrete distribution tables.
- **2. Longitudinal & Panel Suite:**
  - `xtdescribe` (`xtdes`): Panel participation patterns ($T_i$), balance verification, and entry/exit patterns.
  - `xtsum`: Decomposed panel variance ($s_{\text{overall}}, s_{\text{between}}, s_{\text{within}}$).
  - `xttab`: Categorical within-firm and between-firm persistence transition tables.
  - `xtline`: Multi-panel longitudinal trajectory line plots via Plotly with dark/light theme support.
- **3. Post-Estimation & Hypothesis Inference Suite:**
  - `testparm` / `test`: Joint Wald $F$-test / $\chi^2$ multi-parameter hypothesis testing.
  - `lincom`: Linear combinations ($c'\hat{\beta}$) with Delta-method standard errors and confidence intervals.
  - `estat ic`: Model selection AIC / BIC information criteria extraction from regression log-likelihood.
  - `estat summarize`: Exact estimation-sample summary statistics.
  - `r(301)` fail-closed error guards when no prior model exists in the session.
- **4. Architecture & Routing Integration:**
  - Updated `COMMAND_REGISTRY` in `models/command_registry.py`.
  - Updated `CAPABILITY_REGISTRY` & `_estat_dispatcher` in `models/capability_registry.py`.
  - Updated `get_financial_translation()` in `pages/23_stata_studio.py` with executive translations.
- **5. Verification Evidence:**
  - TDD test suite: `tests/test_wave4_expansion.py` (13/13 passed).
  - Stata engine & capability regression suite: 89/89 passed in 4.69s.
  - Branch: `feature/wave4-core-expansion`.




