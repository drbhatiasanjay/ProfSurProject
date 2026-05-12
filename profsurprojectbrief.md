# ProfSurProject — Comprehensive Project Brief

**LifeCycle Leverage Dashboard | Capital Structure Analytics Platform**
*As of 2026-05-12 | v1.3 | 18 pages | 344 tests | GCP Cloud Run*

---

## 1. Origin & Purpose

Built from Prof. Surendra Kumar's (University of Delhi) PhD thesis on capital structure determinants across corporate life stages. The thesis analysed 401 Indian listed companies over 24 years (2001–2024), applying Dickinson (2011) lifecycle classification to test whether financing behaviour — leverage, profitability sensitivity, tangibility — varies systematically across eight corporate life stages.

The interactive platform converts a static academic manuscript into a live, queryable analytics tool with real-time CMIE data rollforward, ML predictions, knowledge graph exploration, and board-ready exports.

**Core research question:** Does the leverage–profitability relationship differ across corporate life stages, and do Indian firms exhibit Pecking Order or Trade-Off Theory behaviour?

**Key finding:** β(profitability) = −0.187 (p<0.01) — Pecking Order Theory holds universally across ALL 8 lifecycle stages. Trade-Off Theory is stage-conditional.

---

## 2. Dickinson (2011) Lifecycle Classification

Companies are classified each year based on cash flow sign patterns from three statements:

| Stage | NCFO | NCFI | NCFF | Interpretation |
|---|---|---|---|---|
| Startup | − | − | + | Burning operating cash, investing aggressively, raising external capital |
| Growth | + | − | + | Generating operating cash, still investing heavily and raising capital |
| Maturity | + | − | − | Self-funding operations, net repaying debt — the ideal steady state |
| Shakeout1 | + | + | + | Asset recycling while still raising capital — unusual transitional state |
| Shakeout2 | − | + | + | Selling assets and raising capital simultaneously — distress signal |
| Shakeout3 | + | + | − | Asset sales funding debt repayment — restructuring mode |
| Decline | − | + | + | Selling assets and raising capital to survive |
| Decay | − | + | − | Asset liquidation, no new capital — terminal state |

The `financials.life_stage` TEXT column and `cls_code` integer (1–8) store this classification for every firm-year across 24 years.

---

## 3. Database Architecture

**File:** `capital_structure.db` (SQLite, gitignored)

### 3.1 Core Tables

#### `financials` — 18,588 rows, 56 columns — the primary analytical panel

| Column group | Key columns | Notes |
|---|---|---|
| Identity | `company_code`, `year` | Composite PK |
| Life stage | `life_stage` (TEXT), `cls_code` (INT 1–8) | Dickinson classification |
| **Leverage** | `lev1_100`, `leverage`, `lev_pct` | **Critical:** `lev1_100` = decimal ratio (×100 for %). `leverage` = already-% values. Never multiply `leverage` by 100. |
| Profitability | `profitability`, `prof100` | EBIT / Total Assets |
| Tangibility | `tangibility`, `tang100` | Net Fixed Assets / Total Assets |
| Capital structure | `tax`, `dividend`, `interest`, `firm_size`, `log_size` | |
| Cash flows | `ncfo`, `ncfi`, `ncff` | Raw inputs to Dickinson classification |
| P&L | `pbit`, `interest_amt`, `borrowings` | |
| Event dummies | `gfc`, `ibc_2016`, `covid_dummy` | Regime shift controls (binary 0/1) |
| Panel metadata | `vintage` | `thesis` / `cmie_2025` / `run3` / `us_av_2024` |

#### `companies` — 426 rows

| Column | Notes |
|---|---|
| `company_code` | Primary key |
| `company_name`, `nse_symbol` | Display identifiers |
| `industry_group` | NIC sector classification |
| `superseded_by` | Tracks corporate actions / mergers |

401 Indian thesis firms + 25 US S&P comparator firms.

#### `ownership` — 9,077 rows

Promoter shareholding breakdown by year:
`promoter_share`, `indian_promoters`, `foreign_promoters`, `non_promoter_mutual_funds`, `non_promoter_fiis`, `vintage`

#### `life_stages` — 8 rows — lookup table

| cls_code | stage_name |
|---|---|
| 1 | Startup |
| 2 | Growth |
| 3 | Maturity |
| 4 | Shakeout1 |
| 5 | Shakeout2 |
| 6 | Shakeout3 |
| 7 | Decline |
| 8 | Decay |

#### `market_index_series` — 16,609 rows

BSE/NSE index data (T623) across all vintages. Used on Dashboard for market context overlay.

#### Auth/activity tables

| Table | Rows | Purpose |
|---|---|---|
| `audit_log` | 20+ | Every page visit, model run, export — timestamped with session_id |
| `user_preferences` | 3 | Per-user page preference JSON |
| `user_model_runs` | 0 | Reserved for model run history |

#### Database views

`v_company_financials`, `v_industry_summary`, `v_life_stage_summary`

---

### 3.2 Data Vintages

Four vintages coexist in every table via the `vintage` column:

| Vintage | Rows | Firms | Year range | Purpose |
|---|---|---|---|---|
| `thesis` | 8,677 | 401 | 2001–2024 | Reproducibility-frozen. Published thesis coefficients reproduce bit-for-bit from this vintage only. |
| `cmie_2025` | 400 | 400 | 2025 only | CMIE API rollforward — adds one additional year to the panel |
| `run3` | 9,031 | 400 | 2001–2025 | Full "Latest" panel combining thesis rows + cmie_2025 extension |
| `us_av_2024` | 480 | 24 | 2006–2026 | US S&P comparator firms for cross-market benchmarking |

**Reproducibility pins:** Pages 3, 8, 9, 10, 13 force `panel_mode='thesis'` at import regardless of sidebar selection. This ensures published thesis coefficients always reproduce exactly.

---

## 4. Platform Architecture

### 4.1 18-Page Streamlit Application

| # | File | Sidebar title | Role access | Core functionality |
|---|---|---|---|---|
| — | `app.py` | — | All | Entry point; Panel radio; Theme toggle; global filters; `st.session_state.filters`; auth gate |
| 1 | `1_dashboard.py` | Dashboard | All | KPIs (firms, obs, year range); Fig 5.1 stage distribution; Fig 5.2 year trends; Table 5.9 stage × leverage; T623 market index overlay |
| 2 | `2_peer_benchmarks.py` | Peer Benchmarks | All | Company vs industry avg vs stage avg; dynamic interpretation expander per chart |
| 3 | `3_scenarios.py` | Scenario Analysis | All | Pure OLS scenario coefficients (thesis-pinned); slider-driven what-if leverage projection |
| 4 | `4_bulk_upload.py` | Bulk Upload | admin/researcher | CSV upload + Dickinson classification engine + CMIE API Sync tab |
| 5 | `5_data_explorer.py` | Data Explorer | All | Raw panel table; vintage-aware filter; CSV export |
| 6 | `6_settings.py` | Settings | All | Light/Dark theme toggle; CMIE lab UI diagnostics |
| 7 | `7_knowledge_graph.py` | Life Stage Dynamics | All | Full knowledge graph (6 tabs — see Section 6 below) |
| 8 | `8_econometrics.py` | Econometrics | All | OLS / FE / RE panel regression + Hausman χ² test (thesis-pinned) |
| 9 | `9_ml_models.py` | ML Models | All | RF / XGBoost / LightGBM + SHAP feature importance (thesis-pinned) |
| 10 | `10_forecasting.py` | LSTM Forecasting | All | LSTM/GRU firm-level leverage trajectory; torch-guarded (thesis-pinned) |
| 11 | `11_clustering.py` | Clustering | All | K-Means vs Dickinson overlay; cluster profiling |
| 12 | `12_transitions.py` | Stage Transitions | All | Life-stage transition matrices; 1/3/5-year windows |
| 13 | `13_advanced_econometrics.py` | Advanced Econometrics | All | System GMM (Arellano-Bover/Blundell-Bond); Speed of Adjustment; delta-leverage decomposition; COVID cohort split (thesis-pinned) |
| 14 | `14_workbench.py` | Workbench | admin/researcher | Ad-hoc regression scratchpad with custom variable selection |
| 15 | `15_interaction_effects.py` | Interaction Effects | All | Prof×Tang cross-term OLS; stage moderation; simple slopes; delta-method standard errors (thesis-pinned) |
| 16 | `16_admin_activity.py` | Admin Activity | admin only | Full audit log viewer; session replay |
| 17 | `17_board_export.py` | Board Export | admin/researcher | 13-topic company board deck → PPTX download (Plotly→PNG via kaleido + python-pptx) |
| 18 | `18_company_navigator.py` | Company Navigator | admin/researcher | Interactive graph explorer: Ego Graph / Peer Cluster / Stage Map using pyvis + Plotly |

---

### 4.2 Sidebar Global State

`st.session_state.filters` carries all sidebar selections across all 18 pages:

```python
{
    "panel_mode": "thesis" | "latest" | "run3" | "us_av_2024",
    "industry": list[str],          # multi-select NIC industry groups
    "year_range": (int, int),       # year slider
    "company": str | None,          # optional single-company focus
    "theme": "light" | "dark",      # CSS toggle
}
```

Reproducibility-critical pages override `filters["panel_mode"] = "thesis"` at import.

---

### 4.3 Backend — Models Package

**`models/`**

| Module | Contents |
|---|---|
| `base.py` | `PanelGroupKFold` cross-validator, `prepare_panel()`, evaluation metrics (MAE, RMSE, R²) |
| `econometric.py` | OLS, Fixed Effects, Random Effects, Hausman χ² test (χ²=225.53 p=0.000 → confirms FE), ANOVA, Arellano-Bover/Blundell-Bond System GMM |
| `scenario_regression.py` | Pure OLS helpers for Scenarios page — separately pytest-covered |
| `ml_predict.py` | RF, XGBoost, LightGBM training + SHAP feature importance; `PanelGroupKFold` cross-validation |
| `timeseries.py` | LSTM/GRU firm-level leverage forecasting; guarded by `HAS_TORCH` flag |
| `clustering.py` | K-Means with Dickinson classification overlay; elbow method |
| `survival.py` | Cox Proportional Hazard model; Kaplan-Meier curves; median Maturity duration = 5.2 years; Maturity→Decline probability = 24% |
| `interaction.py` | Cross-term OLS (Prof×Tang); delta-method standard errors; stage moderation; simple slopes |
| `board_export.py` | 13 topic builder functions → `{figs, tables, insights, actions}` dicts for PPTX |
| `pptx_generator.py` | PPTX assembly: Plotly → PNG (kaleido) → python-pptx slide builder |
| `data_ingest.py` | Bulk/CMIE ingest: Dickinson classification engine, validation, column normalisation |
| `workbench.py` | Workbench page scratchpad model logic |
| `cache.py` | Model artifact storage — avoids retraining on every page reload |

---

### 4.4 CMIE Integration

Feature-flagged via `ENABLE_CMIE=true` in `.streamlit/secrets.toml`. When off, all CMIE code paths short-circuit — app runs on packaged SQLite only.

**`cmie/` package:**

| Module | Role |
|---|---|
| `client.py` | `CmieClient` with 3 transports: `post_query_form` (query.php tabular JSON), `download_wapicall_zip` (wapicall per-company ZIP), legacy-streaming ZIP; exponential backoff; `TokenBucket` rate limiting; `Retry-After` parsing into `CmieRateLimitError.retry_after_s` |
| `batch_pipeline.py` | Per-company wapicall loop: abort-on-auth-error, Retry-After honouring, 5-consecutive-5xx circuit breaker, shared `TokenBucket`; `run_per_company_batch()` + `import_results_to_db()`; returns `CompanyResult` + `BatchSummary` |
| `pipeline.py` | `import_from_raw_dataframe()`, `merge_zip_paths_to_version()` |
| `normalize.py` | `CANONICAL_COLUMNS`, `normalize_panel_like()`, `validate_panel()` |
| `indicator_map.py` | `COLUMN_ALIASES` — CMIE API column names → canonical names mapping |
| `query_form.py` | `cmie_tabular_json_to_dataframe()` — parses CMIE tabular JSON response |
| `zip_parse.py` | ZIP extract + `ERROR.txt` classification by error type |
| `rate_limit.py` | `TokenBucket` — wired on all 4 streamlit_import sites |
| `load_vintage.py` | DataV2 T616/T617/T618/T623 pipe-delimited extract loader |
| `streamlit_import.py` | Sidebar import UI (currently commented out at `app.py:133-136` — uncomment to re-enable) |
| `errors.py` | `CmieError` hierarchy: `CmieAuthError` / `CmieEntitlementError` / `CmieRateLimitError` / base `CmieError` |

**CLI for CMIE operations:**
```powershell
# DataV2 vintage load
py -3.12 -m cmie.load_vintage ./DataV2 --vintage cmie_2025

# Diagnostics
py -3.12 scripts/cmie_stage1_reliance_diagnostic.py   # wapicall probe
py -3.12 scripts/cmie_stage1_queryphp_probe.py         # query.php probe
```

---

### 4.5 Authentication & Access Control

**Library:** `streamlit-authenticator`

| User | Role | Pages accessible |
|---|---|---|
| `sbhatia` | admin | All 18 pages + Admin Activity + Board Export |
| `skumar` | researcher | All pages except Admin Activity |
| `guest` | viewer | Dashboard, Peer Benchmarks, Data Explorer, Scenarios (read-only) |

Credentials stored in `.streamlit/secrets.toml` (gitignored, bcrypt-hashed). Session cookie: `lifecycle_leverage_auth`, 7-day expiry. Every action logged to `audit_log` with timestamp + session_id.

---

## 5. Knowledge Graph — Life Stage Dynamics (Page 7)

This is the most analytically complex page. It builds a full NetworkX `MultiGraph` from the financial panel and ownership data, then exposes it through 6 interactive tabs.

### 5.1 Graph Schema (`graph_builder.py`)

The graph is a **NetworkX `MultiGraph`** — allows multiple parallel edges between the same pair of nodes (e.g. a company can have TRANSITION edges to the same stage in different years).

#### Node Types

| Node ID pattern | Type | Attributes |
|---|---|---|
| `stage:{name}` | `life_stage` | `label`, `color` (stage-specific palette) |
| `industry:{name}` | `industry` | `label`, `color="#374151"` |
| `event:{GFC\|IBC\|COVID}` | `event` | `label`, `years` tuple, `color` (GFC=red, IBC=indigo, COVID=orange) |
| `company:{code}` | `company` | `label`, `company_code`, `industry`, `color="#0D9488"` |
| `obs:{code}:{year}` | `observation` | `year`, `company_code`, `leverage`, `profitability`, `tangibility`, `tax`, `firm_size`, `borrowings`, `promoter_share`, `non_promoters` |

18,000+ observation nodes carry the full financial fingerprint of each firm-year.

#### Edge Types

| Relation | From | To | Metadata |
|---|---|---|---|
| `IN_INDUSTRY` | company | industry | — |
| `HAS_OBSERVATION` | company | observation | `year` |
| `AT_STAGE` | observation | life_stage | `year` |
| `AT_STAGE` | company | life_stage | `year` (shortcut edge — most recent) |
| `DURING_EVENT` | observation | event | `year` (only when GFC/IBC/COVID dummy = 1) |
| `TRANSITION` | company | life_stage | `from_stage`, `to_stage`, `year` (only on stage CHANGE) |

The `TRANSITION` edges are the analytical centrepiece — they encode every stage change event across 401 companies × 24 years.

#### Construction sequence (in `build_knowledge_graph()`):

1. Add 8 LifeStage nodes
2. Add Industry nodes from `industry_group` column
3. Add 3 EventPeriod nodes (GFC/IBC/COVID — only if dummy column has any 1s)
4. Add Company nodes + `IN_INDUSTRY` edges
5. Add 18,000+ Observation nodes + `HAS_OBSERVATION` + `AT_STAGE` + `DURING_EVENT` edges
6. Merge ownership data into observation node attributes
7. Add `TRANSITION` edges — by scanning each company's sorted observations for year-on-year stage changes

### 5.2 Graph Statistics (live panel)

5 KPI metrics shown at top of page:
- Companies (401)
- Observations (~9,000 for thesis vintage)
- Transitions (total TRANSITION edge count)
- Avg Transitions/Firm
- Life Stages (8)

### 5.3 Tab 0 — Knowledge Graph (Interactive Network)

Three view modes selectable via radio button:

**View 1: Stage + Industry overview (aggregate)**
- Nodes: 8 life stages + top 15 industries by firm count + 3 event nodes
- Edges weighted by number of companies in that stage+industry combination (min 3 firms)
- Event nodes connected to stages proportional to observations during that event period
- Rendered via `graph_to_plotly_figure()` — Plotly scatter trace + line trace overlay
- Node symbols: ◆ Life Stage, ■ Industry, ▲ Event

**View 2: With companies (up to 80)**
- Adds individual company nodes to the aggregate view
- Stage filter multiselect to narrow to specific lifecycle stages
- Capped at 80 companies for legibility
- Optional "Show observation nodes" checkbox (adds 9,000+ nodes — slower)

**View 3: Company drill-down**
- Select any company from dropdown
- 1–3 hop depth slider
- `build_drill_down_figure()` builds ego subgraph around selected company
- Node details panel: company type, industry, full stage transition history table (year / from / to)
- Download: stage transition history as CSV

### 5.4 Tab 1 — Transition Probability Matrix (Markov)

**8×8 Markov transition matrix heatmap:**
- Cell [i,j] = probability a firm in stage i this year is in stage j next year
- Diagonal = stickiness (probability of remaining in same stage)
- Toggle: show raw counts vs probabilities
- Year range slider to restrict analysis window

**Event comparison mode (GFC / IBC / COVID):**
- Side-by-side heatmaps: Normal Years | During Event
- Third panel: Probability Shift (event − normal), diverging red/blue scale (−0.3 to +0.3)
- Top-10 biggest probability shifts table (sorted by absolute delta)
- Threshold: only shifts > 2pp shown

**Stage Stickiness bar chart:**
- Colour-coded by lifecycle stage
- Higher stickiness = more absorbing state (Maturity is typically the stickiest)

**Stage × Financial Metric Matrix:**
- Annotated heatmap: rows = 8 stages, columns = key financial metrics
- Shows average leverage, profitability, tangibility, firm_size per stage
- Reveals the "financial DNA" of each lifecycle stage
- Downloadable as CSV

### 5.5 Tab 2 — Event Impact Matrices

Three matrices showing differential impact of GFC (2008–09), IBC (2016–20), COVID (2020–21) across all 8 stages:

**Matrix 1 — Leverage Impact:**
- Shows leverage change in percentage points (pp) vs normal years
- Red = leverage increased during event; Blue = decreased
- Scale: −5pp to +5pp
- Full data expandable with Normal / GFC / IBC / COVID columns

**Matrix 2 — Transition Rate:**
- % of firm-years at each stage where the firm changed stage
- Compares Normal rate vs each event period
- Higher rate = event disrupted that stage more

**Matrix 3 — Deterioration Rate:**
- Of firms that DID transition during an event, what % moved to a WORSE stage?
- STAGE_RANK order: Startup < Growth < Maturity < Shakeout1/2/3 < Decline < Decay
- Empty cell = no transitions from that stage during that event

**Event comparison bar chart:**
- Grouped bar chart: x = stage, y = leverage Δ pp, colour = GFC/IBC/COVID
- Zero line reference

### 5.6 Tab 3 — Stage Pathway Discovery

**Most common N-step sequences:**
- Configurable sequence length (2–4 steps) and minimum frequency
- Horizontal bar chart of top 20 sequences (e.g. "Maturity → Decline → Decay" = 47 firms)
- Download as CSV

**Paths to target stage — Sunburst:**
- Select any target stage
- Looks back up to 3 steps: "how did firms arrive at this stage?"
- Rendered as a Plotly sunburst chart (inner ring = most recent step, outer = earlier steps)
- Top 15 paths shown with firm counts

**Stage Duration Matrix:**
- Scans each company's full observation sequence for consecutive "runs" in each stage
- Computes: Avg Duration (years), Median Duration, Max Duration, N Spells
- Bar chart coloured by stage + data table with download

### 5.7 Tab 4 — COVID Cohort Analysis

**Definition:** Compares each firm's life stage in 2019 (pre-COVID) vs 2022+ (post-COVID).

**KPI strip (5 metrics):**
- Total Firms with both pre and post data
- Deteriorated count + % (moved to worse stage)
- Improved count + % (moved to better stage)
- Entered Decline (were NOT in Decline/Decay pre-COVID but are post-COVID)
- Recovered (were in Decline/Decay pre-COVID but improved post-COVID)

**Pre-COVID → Post-COVID Stage Migration heatmap:**
- 8×8 matrix showing firm counts: rows = pre-COVID stage, columns = post-COVID stage
- Diagonal = no change; off-diagonal = stage migration

**Leverage change comparison (box plots):**
- Deteriorated firms vs Improved firms: leverage change distribution
- Profitability change distribution (same comparison)

**Statistical tests:**
- Welch's t-test (unequal variances assumed) + Mann-Whitney U (non-parametric)
- Minimum 5 firms per group required
- Output: metric, group means, t-statistic, p-values with significance stars (*/***/***)

**Named firm tables:**
- "Firms That Entered Decline/Decay After COVID" — company, industry, pre/post stage, leverage Δ
- "Firms That Recovered After COVID" — same columns
- Both downloadable as CSV

**Auto-interpretation expander** with plain-English summary of deterioration rate and what it means for the panel's structural health.

### 5.8 Tab 5 — Multi-Hop Company Profiler

A **4-condition chained query engine** that traverses the graph to find companies matching complex compound criteria:

| Condition | What it filters |
|---|---|
| **Condition 1:** Stage @ Year | Companies in a specific Dickinson stage in a specific year |
| **Condition 2:** Transition | Companies that made a specific From→To stage change in a year range |
| **Condition 3:** During Event | Companies with observations during GFC / IBC / COVID |
| **Condition 4:** Financial metric | Companies where any observation meets a metric threshold (e.g. leverage > 0.5) |

All conditions are combinable — each successively narrows the candidate set.

**Output:**
- Funnel display showing firms surviving each filter step (5 metrics: All / Stage / Transition / Event / Metric)
- Results table: Company, Industry, Latest Stage, Leverage, Profitability, Total Transitions
- CSV download

**Example queries:**
- "Which Growth-stage firms in 2015 later transitioned to Decline during COVID with profitability < 0.02?"
- "Which Maturity firms made a Maturity→Shakeout transition between 2016–2020?"

---

## 6. Theory Frameworks Implemented

| Framework | Page | Key result |
|---|---|---|
| Dickinson (2011) lifecycle | All pages | 8-stage cash flow classification applied to 401 firms × 24 years |
| Pecking Order Theory | Econometrics (8) | β(Prof) = −0.187 (p<0.01) — universal across all 8 stages |
| Trade-Off Theory | Econometrics (8) | Stage-conditional; strongest in Maturity |
| Panel Fixed Effects | Econometrics (8) | Hausman χ²=225.53, p=0.000 — FE confirmed over RE |
| System GMM | Adv Econometrics (13) | Arellano-Bover/Blundell-Bond; SOA = 1 − lag-leverage coefficient |
| Kaplan-Meier survival | Life Stage Dynamics (7) | Median Maturity duration = 5.2 years; Maturity→Decline probability = 24% |
| Markov transitions | Life Stage Dynamics (7) + Transitions (12) | Full 8×8 stage-to-stage probability matrix |
| Interaction effects (delta method) | Interaction Effects (15) | Prof×Tang cross-term; stage moderation with analytically-derived SEs |

---

## 7. Deployment Stack

| Layer | Technology |
|---|---|
| Runtime | Docker, Python 3.11-slim |
| Platform | Google Cloud Run |
| **Live URL** | `https://lifecycle-leverage-qhzom2yadq-ue.a.run.app` |
| GCP Project | `tempproject-462219` |
| Region | `us-east1` |
| Memory | 2Gi |
| Access | `--allow-unauthenticated` (app-level auth gate controls user access) |
| CI/CD | GitHub Actions → Docker build → Artifact Registry → Cloud Run deploy |
| Secrets injection | `STREAMLIT_SECRETS_TOML` GitHub Actions secret → `.streamlit/secrets.toml` at build time |
| Repository | `github.com/drbhatiasanjay/ProfSurProject` |

**Deploy command:**
```powershell
$env:CLOUDSDK_PYTHON = "C:\Users\hemas\AppData\Local\Programs\Python\Python312\python.exe"
gcloud run deploy lifecycle-leverage --source . --region us-east1 --project tempproject-462219 --port 8501 --memory 2Gi --allow-unauthenticated
```

---

## 8. Test Suite — 344 Tests

| Test file | Coverage area |
|---|---|
| `test_database.py` | DB queries, vintage predicates, view correctness |
| `test_models.py` | Econometric + ML model outputs |
| `test_scenario_regression.py` | Pure OLS scenario helpers |
| `test_cmie_client.py` | API transport mocks |
| `test_cmie_pipeline.py` | Import pipeline |
| `test_cmie_batch.py` | Batch pipeline circuit breaker + retry logic |
| `test_cmie_normalize.py` | Column normalisation + CANONICAL_COLUMNS |
| `test_cmie_rate_limit.py` | TokenBucket behaviour |
| `test_cmie_zip_parse.py` | ZIP extract + ERROR.txt classification |
| `test_cmie_query_form.py` | Tabular JSON parser |
| `test_bulk_upload_cmie_parse.py` | CSV ingest + CMIE parse end-to-end |
| `test_page_integration.py` | All 18 pages load without import error |
| `test_board_export.py` | 13-topic PPTX builder |
| `test_cfo_graph.py` | Company Navigator pyvis graph |

```powershell
py -3.12 -m pytest tests/ -v
```

---

## 9. Scripts & Production Tools

| Script | Purpose |
|---|---|
| `scripts/demo_recorder.py` | Automated demo: 16 sections, screen+voice capture (ffmpeg gdigrab + dshow), Playwright browser automation, faster-whisper Whisper transcription, burned-in SRT captions, title cards, final concat to `demo_FULL.mp4` |
| `scripts/make_ebook_v3.py` | Generates `profsur-ebook-v3.html` — 719 KB, card/dashboard format, real CMIE data from SQLite, 4 embedded screenshots, inline EOLABS logo |
| `scripts/make_ebook_v3_1.py` | Generates `profsur-ebook-v3.1.html` — 128 KB, narrative chapter format |
| `scripts/cmie_stage1_reliance_diagnostic.py` | wapicall transport E2E probe (gitignored artifacts) |
| `scripts/cmie_stage1_queryphp_probe.py` | query.php transport E2E probe |

**Demo recorder usage:**
```powershell
streamlit run app.py
py -3.12 scripts/demo_recorder.py            # record all 16 sections
py -3.12 scripts/demo_recorder.py --section 07    # re-record one section
py -3.12 scripts/demo_recorder.py --concat-only   # stitch without re-recording
```

---

## 10. Commercial Positioning

### 10 Unique Capabilities (No Competitor Has All 10)

1. Dickinson (2011) lifecycle classification engine applied to Indian listed firms
2. Stage-specific panel regression (OLS/FE/RE with Hausman test)
3. System GMM Speed of Adjustment computation
4. Kaplan-Meier stage duration survival curves
5. Markov stage transition probability matrices with event comparison
6. Stage-moderated interaction effects (delta-method standard errors)
7. LSTM/GRU firm-level leverage trajectory forecasting
8. SHAP feature importance for leverage determinants
9. Real-time CMIE API rollforward integration (Latest panel = 2025 data)
10. Board-ready PPTX export with live chart-to-slide pipeline

**Competitive positioning:** Bloomberg, Capital IQ, LSEG, CMIE ProwessOnWeb, Screener.in — none provide Dickinson lifecycle classification + stage-specific panel regression + GMM SOA + survival analysis for Indian listed firms. The analytical space is entirely unoccupied.

**Key differentiator quote:** *"Bloomberg tells you the ratio. This tells you whether the ratio is right for where you are."*

### Market Size

- India financial analytics market: $483M (2025) → $1.35B (2035), 10.81% CAGR
- India venture debt: INR 10,300 crore, 58% CAGR — natural buyer for BSE SME lifecycle comparables
- NSE Emerge + BSE SME: 900+ listed SMEs — most actionable startup-adjacent segment

### 9 Buyer Segments (GTM Priority Order)

| Priority | Segment | WTP | Decision cycle |
|---|---|---|---|
| 1 | Credit rating agencies (CRISIL, ICRA, CARE, India Ratings) | ₹8–15L/yr SaaS | 6-month POC |
| 2 | IIM/IIT/XLRI finance faculty + PhD programs | ₹3–6L/yr academic | Semester budget cycle |
| 3 | Corporate CFOs / treasury (BSE 500 firms) | ₹2–5L/yr per firm | Annual IT budget |
| 4 | Venture debt funds (Stride, Trifecta, Alteria, Blacksoil) | ₹5–12L/yr | 3-month pilot |
| 5 | Private sector banks (HDFC, ICICI, Axis — large corporate credit) | ₹15–30L/yr | 12–18 month procurement |
| 6 | NSE Emerge + BSE SME ecosystem (900+ listed SMEs) | ₹1–3L/yr | Quarterly |
| 7 | PE / FII (portfolio lifecycle monitoring) | ₹10–25L/yr | 12-month |
| 8 | Investment banks (M&A lifecycle risk assessment) | ₹20–40L/yr | 18-month |
| 9 | SEBI / RBI (systemic monitoring across sectors) | Commissioned research | 24+ month |

### Day-to-Day Monetary ROI by Stakeholder

| Stakeholder | Use case | Frequency | Value unlocked |
|---|---|---|---|
| Rating analyst | Lifecycle-adjusted default probability for credit reports | Weekly | Reduces analyst research time by ~3 hrs/company |
| CFO (BSE 500) | "Where are my peers in lifecycle vs my leverage?" | Quarterly board prep | Avoids 1 mispriced debt tranche (~₹50L–2Cr saving) |
| Venture debt fund | Lifecycle classification before disbursement to Growth-stage SME | Per deal | Reduces default probability by narrowing to Growth-stage borrowers |
| IIM faculty | Live panel dataset + analytical results for PhD supervision | Per semester | Eliminates manual data assembly (40–80 hrs/student) |
| PE fund | Monitor portfolio company lifecycle drift in real time | Monthly | Early Shakeout detection → intervention 6–12 months earlier |

---

## 11. Pending Features (Awaiting Go-Ahead)

| Feature | Status | Implementation detail |
|---|---|---|
| **Phase 2 Comparison Page** (`pages/19_comparison.py`) | Ready to build | 3 modes: Vintage (thesis vs cmie_2025 side-by-side), Year (two years same firm), Firm (two firms same year). Needs `get_overlapping_firms_delta()` + `get_industry_delta()` DB helpers. |
| **Panel Selector → Navbar** | Ready to build | Option A: `st.query_params` + HTML `<select>` + JS `window.location.href='?panel=<value>'` → full page reload. `app.py` reads `st.query_params.get("panel","latest")` at startup. Zero changes to 18 existing pages. Saves ~80px sidebar space. |
| **CMIE sidebar re-enable** | 2 lines to uncomment | `app.py:133-136` — sidebar import block commented out; re-enable by uncommenting |

---

## 12. Critical Implementation Rules

1. **`lev1_100` vs `leverage`:** Always use `lev1_100` (decimal ratio, ×100 for %). The `leverage` column stores values already as percentages — multiplying it by 100 gives impossible values like 2029%.

2. **Python 3.11 in prod, 3.12 locally:** Docker uses `python:3.11-slim`. Python 3.14 breaks ML packages. Test with `py -3.12`.

3. **Torch is optional:** Behind `HAS_TORCH` gate in `models/timeseries.py`. Platform works fully without torch — Forecasting page degrades gracefully.

4. **Reproducibility pins are immutable:** Never remove the `panel_mode='thesis'` override at top of pages 3/8/9/10/13. Published thesis coefficients must reproduce bit-for-bit.

5. **secrets.toml is gitignored — always:** Regenerate from Obsidian `Credentials & Access Reference.md` if lost. CI injects via `STREAMLIT_SECRETS_TOML` GitHub Actions secret.

6. **Screen capture uses logical pixels:** ffmpeg gdigrab requires logical pixel resolution. On a 125%-DPI-scaled 1920×1080 display this is 1707×960. Use `ctypes.windll.user32.GetSystemMetrics(0/1)` — never hardcode resolution.

7. **Graph build is cached by DB mtime:** `@st.cache_resource` on `_build_graph()` busts when `capital_structure.db` modification time changes. No manual cache clearing needed after data updates.

---

## 13. File Structure Summary

```
app.py                  Entrypoint, sidebar, panel+theme state, auth gate
db.py                   All SQL queries, caching, vintage predicate, connection
helpers.py              Formatters, chart theme, STAGE_COLORS, plotly_layout()
graph_builder.py        NetworkX MultiGraph construction from SQLite data
graph_viz.py            Plotly figure builders for graph views
assets/
  style_light.css       Default theme (inherits Streamlit defaults)
  style_dark.css        DataV2-mock palette (full widget coverage)
cmie/                   CMIE API integration package (7 modules)
models/                 Analytical models package (13 modules)
pages/                  18 page files (1_dashboard.py … 18_company_navigator.py)
scripts/                Demo recorder, ebook generators, CMIE diagnostics
tests/                  344 tests (14 test files)
docs/
  cmie_api_reference.md     CMIE API spec (13 sections)
  ENGINEERING_PLAYBOOK.md   Repo conventions
  plans/                    Execution strategy docs (CMIE refactor, DataV2, panel parity)
.streamlit/
  secrets.toml          CMIE key + user credentials (gitignored)
capital_structure.db    SQLite database (gitignored)
DataV2/                 Raw CMIE pipe-delimited extracts (gitignored)
```
