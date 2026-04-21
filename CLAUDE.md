# ProfSurProject — LifeCycle Leverage Dashboard

## What This Is
Streamlit dashboard analyzing capital structure determinants across corporate life stages for 401 Indian companies. Based on PhD thesis by Prof Surendra Kumar, University of Delhi. Thesis panel covers 2001–2024; CMIE 2025 rollforward is available on the Latest panel (`panel_mode='latest'`).

## Architecture
- **Frontend**: Streamlit multipage app (14 pages)
- **Database**: SQLite (`capital_structure.db`) — vintage-tagged since the DataV2 work (thesis + cmie_2025 vintages coexist)
- **Models**: `models/` package (econometric + ML + advanced + scenario_regression + data_ingest + workbench)
- **CMIE integration**: `cmie/` package (CmieClient, load_vintage, pipeline, normalize — all transports implemented)
- **Tests**: `tests/` with pytest (81 tests — DB + models + 7 CMIE suites + scenario_regression)
- **Deployment**: Docker (Python 3.11-slim) → Google Cloud Run

## Key Commands
```bash
# Local dev
streamlit run app.py

# Run tests
py -3.12 -m pytest tests/ -v

# Docker
docker compose up -d
docker exec lifecycle-app python -m pytest tests/ -v

# Deploy to GCP
export CLOUDSDK_PYTHON="/c/Users/hemas/AppData/Local/Programs/Python/Python312/python.exe"
gcloud run deploy lifecycle-leverage --source . --region us-east1 --project tempproject-462219 --port 8501 --memory 2Gi --allow-unauthenticated

# DataV2 vintage load (CMIE 2025 rollforward from DataV2/ pipe-delimited extracts)
py -3.12 -m cmie.load_vintage ./DataV2 --vintage cmie_2025

# Live CMIE diagnostics (standalone, gitignored artifacts)
py -3.12 scripts/cmie_stage1_reliance_diagnostic.py   # wapicall transport probe
py -3.12 scripts/cmie_stage1_queryphp_probe.py         # query.php transport probe
```

## UI controls (sidebar + Settings)
- **Panel** radio (sidebar): **Thesis** (2001–2024, reproducibility-frozen) vs **Latest** (2001–present with CMIE 2025). Reproducibility-critical pages (Scenarios, Econometrics, ML, Forecasting, Advanced Econometrics) pin `panel_mode='thesis'` at import regardless of sidebar selection.
- **Theme** radio (Settings → Appearance): **Light** (default, Streamlit-inheriting) vs **Dark** (DataV2-mock palette). Scoped to session.
- **Sidebar caption** shows current firm/obs count + year range + panel suffix + theme indicator.

## CMIE integration (feature-flagged)
- **Flag**: `ENABLE_CMIE=true` (env var or `.streamlit/secrets.toml`). When off, CMIE code paths short-circuit and the app runs on packaged SQLite only (production parity).
- **API Passkey**: `CMIE_API_KEY` in `.streamlit/secrets.toml` (gitignored). Rotate at `register.cmie.com` → API Passkey.
- **Transports supported**: query.php (indicator JSON), wapicall (company ZIP), legacy-streaming ZIP — all in `cmie/client.py`.
- **Sidebar block currently hidden** (`app.py:133-136` commented out); re-enable by uncommenting the two lines there.
- **Reference**: `docs/cmie_api_reference.md` — 13-section end-to-end spec (transports, payloads, rate limits, retries, known issues).

## Key docs
- **`docs/cmie_api_reference.md`** — CMIE API reference (all three transports, rate limits, known issues).
- **`docs/plans/2026-04-21-cmie-refactor-execution-strategy.md`** — refactor execution strategy (waves, API contract deltas, rate-limit/retry implementation deltas, §E.5 diagnostic outcomes).
- **`docs/plans/2026-04-21-cmie-panel-scenarios-bulk-e2e.md`** — panel parity per-file plan (scenarios, bulk upload, verification checklist).
- **`docs/plans/2026-04-21-datav2-vintage-ingest.md`** — DataV2 vintage ingest plan (T616/T617/T618/T623 loader, schema migration).
- **`docs/ENGINEERING_PLAYBOOK.md`** — repo conventions.
- **`FORK_WORKFLOW.md`** — fork/upstream rules when contributing CMIE lab features.

## GCP Details
- Account: drbhatiasanjay@gmail.com
- Project: tempproject-462219
- Region: us-east1
- Service: lifecycle-leverage

## File Structure
```
app.py              - Entrypoint, sidebar filters, panel+theme state, navigation
db.py               - All SQL queries, caching, vintage predicate, connection
helpers.py          - Formatters, chart theme dispatcher (plotly_layout),
                      new_badge() helper, interpretation engine
assets/
  style_light.css   - Default theme (inherits Streamlit defaults)
  style_dark.css    - DataV2-mock palette (full widget coverage)
cmie/
  client.py         - CmieClient (download_wapicall_zip, post_query_form,
                      download_query_zip) with backoff + TokenBucket hook;
                      Retry-After parsed into CmieRateLimitError.retry_after_s
  errors.py         - CmieError hierarchy (Auth / Entitlement / RateLimit / …)
  pipeline.py       - import_from_raw_dataframe, merge_zip_paths_to_version
  batch_pipeline.py - Hardened per-company wapicall loop: abort-on-auth,
                      Retry-After honouring, 5-consecutive-5xx circuit breaker,
                      shared TokenBucket (§F.3.3/4/5). run_per_company_batch +
                      import_results_to_db; returns CompanyResult + BatchSummary
  normalize.py      - CANONICAL_COLUMNS, normalize_panel_like, validate_panel
  indicator_map.py  - COLUMN_ALIASES (CMIE → canonical)
  query_form.py     - cmie_tabular_json_to_dataframe
  zip_parse.py      - ZIP extract + ERROR.txt classification
  rate_limit.py     - TokenBucket (now wired on all 4 streamlit_import sites)
  load_vintage.py   - DataV2 T616/T617/T618/T623 loader
  streamlit_import.py - Sidebar import UI (currently hidden at app.py:133-136);
                      errno-check guard (§E.5.3) before tabular parser
  __main__.py       - CLI: download / import-zip / merge-zips / batch-download
models/
  base.py           - PanelGroupKFold, prepare_panel, metrics
  econometric.py    - OLS, FE, RE, Hausman, ANOVA, GMM (Tier 1)
  scenario_regression.py - Pure OLS helpers for Scenarios (pytest-covered)
  ml_predict.py     - RF, XGBoost, LightGBM, SHAP (Tier 2)
  timeseries.py     - LSTM/GRU forecasting (Tier 3, torch-guarded)
  clustering.py     - K-Means, Dickinson comparison (Tier 3)
  survival.py       - Cox PH, Kaplan-Meier (Tier 3)
  data_ingest.py    - Bulk / CMIE ingest helpers (classification, validation)
  workbench.py      - Workbench page logic
  cache.py          - Model artifact storage
pages/
  1_dashboard.py           - KPIs, stage trends, T623 index, DataV2 vintage tabs
  2_peer_benchmarks.py     - Company vs industry/stage
  3_scenarios.py           - OLS scenario coefficients (pinned: panel_mode='thesis')
  4_bulk_upload.py         - Bulk upload + CMIE API Sync tab
  5_data_explorer.py       - Raw panel explorer (vintage-aware)
  6_settings.py            - Appearance (theme toggle) + CMIE lab UI
  7_knowledge_graph.py     - Determinants graph
  8_econometrics.py        - OLS/FE/RE/Hausman (pinned: thesis)
  9_ml_models.py           - RF/XGB/LGBM + SHAP (pinned: thesis)
  10_forecasting.py        - LSTM/GRU (pinned: thesis)
  11_clustering.py         - K-Means vs Dickinson
  12_transitions.py        - Life-stage transition matrices
  13_advanced_econometrics.py - GMM, delta-leverage, COVID cohorts (pinned: thesis)
  14_workbench.py          - Workbench scratchpad
scripts/
  cmie_stage1_reliance_diagnostic.py  - wapicall E2E probe (§E.5)
  cmie_stage1_queryphp_probe.py       - query.php E2E probe (§E.5.3)
tests/
  test_database.py, test_models.py, test_scenario_regression.py,
  test_cmie_*.py (7 files), test_bulk_upload_cmie_parse.py   (81 tests total)
cmie_validation/    - Per-run CMIE API artifacts (gitignored)
DataV2/             - Raw CMIE pipe-delimited extracts (gitignored)
```

## Important Notes
- **Python 3.11 required** in prod (3.14 breaks ML packages). Project tests target Python 3.12 locally; CI validates.
- **Torch is optional** — behind `HAS_TORCH` gate in `models/timeseries.py`. Streamlit Cloud builds without torch by default.
- **Every chart** has a dynamic interpretation expander below it.
- **Sidebar filters** apply globally across all pages via `st.session_state.filters`.
- **Vintage drift** is captured in `data_vintages` table (see migration `001_datav2_vintage.sql`).
- **Reproducibility pins** on Scenarios (3) / Econometrics (8) / ML (9) / Forecasting (10) / Advanced Econometrics (13) force `panel_mode='thesis'` regardless of sidebar so published coefficients reproduce bit-for-bit.
- **`get_filtered_financials`** and **`get_full_data_explorer`** both include the `vintage` column so downstream dashboards can split cmie_2025 from thesis rows.
