# ProfSurProject — LifeCycle Leverage Dashboard

## What This Is
Streamlit dashboard analyzing capital structure determinants across corporate life stages for 401 Indian companies. Based on PhD thesis by Prof Surendra Kumar, University of Delhi. Thesis panel covers 2001–2024; CMIE 2025 rollforward is available on the Latest panel (`panel_mode='latest'`).

## Architecture
- **Frontend**: Streamlit multipage app (21 pages — KG1 stack pages 1–20 retained; KG2 added as page 21)
- **Database**: SQLite (`capital_structure.db`) — vintage-tagged (thesis + cmie_2025 + run3 + us_av_2024 vintages coexist)
- **Models**: `models/` package (econometric + ML + advanced + scenario_regression + data_ingest + workbench + interaction)
- **CMIE integration**: `cmie/` package (CmieClient, load_vintage, pipeline, normalize — all transports implemented)
- **KG2 / OCaml layer**: `lifecycle-ontology/` OCaml service + `graph_bridge.py` Python stub (separate from KG1; never touches graph_builder.py)
- **Tests**: `tests/` with pytest (316 tests — DB + models + 7 CMIE suites + scenario_regression + page integration + board export + CFO graph)
- **Deployment**: Docker (Python 3.11-slim) → Google Cloud Run

## Key Commands
```bash
# Unified Project Ops CLI (Zero-Bloat Automation)
py -3.12 scripts/project_ops.py status               # Check local, remote, and Cloud Run revision status
py -3.12 scripts/project_ops.py test --fast          # Run targeted test suites with quiet output
py -3.12 scripts/project_ops.py verify --env gcp     # Live Playwright browser verification + screenshot
py -3.12 scripts/project_ops.py push                 # Keyring-isolated pre-push test and git push

# Local dev
streamlit run app.py

# Run tests (quiet mode to preserve token limits)
py -3.12 -m pytest tests/ -q --tb=line

# Docker
docker compose up -d
docker exec lifecycle-app python -m pytest tests/ -q

# Deploy to GCP
export CLOUDSDK_PYTHON="/c/Users/hemas/AppData/Local/Programs/Python/Python312/python.exe"
gcloud run deploy lifecycle-leverage --source . --region us-east1 --project tempproject-462219 --port 8501 --memory 2Gi --allow-unauthenticated
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
  interaction.py    - Cross-term OLS + stage moderation + simple slopes (delta method SEs)
  board_export.py   - 13 topic builder functions → {figs, tables, insights, actions} (page 17)
  pptx_generator.py - PPTX assembly: Plotly→PNG (kaleido) → python-pptx slides
pages/
  1_dashboard.py           - KPIs, Fig 5.1 stage view, Fig 5.2 year trends, Table 5.9, T623 index
  2_peer_benchmarks.py     - Company vs industry/stage
  3_scenarios.py           - OLS scenario coefficients (pinned: panel_mode='thesis')
  4_bulk_upload.py         - Bulk upload + CMIE API Sync tab
  5_data_explorer.py       - Raw panel explorer (vintage-aware)
  6_settings.py            - Appearance (theme toggle) + CMIE lab UI
  7_knowledge_graph.py     - Life Stage Dynamics: Markov transitions, stickiness, event impact, COVID cohorts, multi-hop profiling (sidebar title: "Life Stage Dynamics") [KG1 — do not modify]
  8_econometrics.py        - OLS/FE/RE/Hausman (pinned: thesis)
  9_ml_models.py           - RF/XGB/LGBM + SHAP (pinned: thesis)
  10_forecasting.py        - LSTM/GRU (pinned: thesis)
  11_clustering.py         - K-Means vs Dickinson
  12_transitions.py        - Life-stage transition matrices
  13_advanced_econometrics.py - GMM, delta-leverage, COVID cohorts (pinned: thesis)
  14_workbench.py          - Workbench scratchpad
  15_interaction_effects.py - Cross-term (Prof×Tang) + stage moderation + simple slopes (pinned: thesis)
  16_admin_activity.py     - Admin audit log viewer (role: admin only)
  17_board_export.py       - Individual company board deck: 13 topics, preview + .pptx download (role: admin/researcher)
  18_company_navigator.py  - Interactive graph explorer: Ego Graph / Peer Cluster / Stage Map, pyvis + Plotly (role: admin/researcher) [KG1 — do not modify]
  19_ai_assistant.py       - AI assistant chat interface
  20_life_stage_dynamics.py - Life stage dynamics explorer
  21_knowledge_graph2.py   - KG2: OCaml-ontology-backed semantic graph (Macro/Meso/Micro, personas, Explain This) [KG2 — separate stack]
graph_bridge.py     - KG2 Python stub: generates Macro/Meso/Micro JSON matching OCaml contract;
                      swap for OCaml HTTP call once lifecycle-ontology service is live
lifecycle-ontology/ - OCaml semantic + analytics meta-layer (KG2 backend)
  dune-project
  src/
    domain/         - stage, period, metric, company types + smart constructors
    analytics_meta/ - model, model_run, statistic, normative_band, scenario, explanation, persona
    normative/      - band computation + anomaly flags
    scenario/       - scenario DSL + validation
    graph_export/   - ocamlgraph Macro/Meso/Micro → JSON/DOT
    api/            - Dream HTTP: /lifecycle_query /explain_stat /scenario_runner
    cli/            - cmdliner entry point
  test/             - alcotest unit tests
scripts/
  cmie_stage1_reliance_diagnostic.py  - wapicall E2E probe (§E.5)
  cmie_stage1_queryphp_probe.py       - query.php E2E probe (§E.5.3)
tests/
  test_database.py, test_models.py, test_scenario_regression.py,
  test_cmie_*.py (7 files), test_bulk_upload_cmie_parse.py,
  test_page_integration.py, test_board_export.py, test_cfo_graph.py   (344 tests total)
  test_kg2_bridge.py  - KG2 graph_bridge JSON contract tests
cmie_validation/    - Per-run CMIE API artifacts (gitignored)
DataV2/             - Raw CMIE pipe-delimited extracts (gitignored)
docs/
  KG2_ARCHITECTURE.md - KG2 entry-point doc (cross-references all four OCaml spec files)
```

## Key Commands (KG2)
```bash
# OCaml toolchain (one-time setup)
opam switch create 5.2.0 && eval $(opam env)
opam install dune base core eio_main yojson ocamlgraph cmdliner dream alcotest

# Build OCaml service
cd lifecycle-ontology && dune build && dune runtest

# Run OCaml service locally (port 8080)
dune exec src/cli/main.exe -- serve --port 8080

# Test Python bridge contract
py -3.12 -c "from graph_bridge import get_graph_json; import json; print(json.dumps(get_graph_json('macro'), indent=2))"

# Run KG2 bridge tests
py -3.12 -m pytest tests/test_kg2_bridge.py -v
```

## Important Notes
- **Python 3.11 required** in prod (3.14 breaks ML packages). Project tests target Python 3.12 locally; CI validates.
- **Torch is optional** — behind `HAS_TORCH` gate in `models/timeseries.py`. Streamlit Cloud builds without torch by default.
- **KG2 isolation** — `pages/21_knowledge_graph2.py` and `graph_bridge.py` must **never** import from `pages/7_knowledge_graph.py`, `pages/18_company_navigator.py`, or `graph_builder.py`. KG2 reads from `db.py` directly. The KG1 stack (pages 7, 18, graph_builder.py) is frozen.
- **Every chart** has a dynamic interpretation expander below it.
- **Sidebar filters** apply globally across all pages via `st.session_state.filters`.
- **Vintage drift** is captured in `data_vintages` table (see migration `001_datav2_vintage.sql`).
- **Reproducibility pins** on Scenarios (3) / Econometrics (8) / ML (9) / Forecasting (10) / Advanced Econometrics (13) force `panel_mode='thesis'` regardless of sidebar so published coefficients reproduce bit-for-bit.
- **`get_filtered_financials`** and **`get_full_data_explorer`** both include the `vintage` column so downstream dashboards can split cmie_2025 from thesis rows.

## Architectural Load-Bearers (god nodes)
<!-- generated by graphify 2026-05-20 — re-run /graphify to refresh -->
Before editing any file below, check what depends on it. Touching a god node affects everything connected to it.

| Node | Edges | File | What breaks if you change it |
| --- | --- | --- | --- |
| `_query()` | 30 | `db.py` | Every page — all data reads/writes go through this |
| `CmieClient` | 22 | `cmie/client.py` | All 3 transports (query.php, wapicall, ZIP) |
| `plotly_layout()` | 21 | `helpers.py` | Every chart on every page |
| `run_per_company_batch()` | 19 | `cmie/batch_pipeline.py` | CMIE batch ingestion + circuit breaker |
| `run_pooled_ols()` | 18 | `models/econometric.py` | Econometrics, Scenarios, Advanced Econ pages |
| `cross_validate_model()` | 15 | `models/base.py` | All ML tiers (RF, XGB, LGBM, LSTM) |
| `_login()` | 15 | `app.py` | Auth gate — every session |
| `CmieError` / `CmieAuthError` / `CmieRateLimitError` | 14 each | `cmie/errors.py` | All CMIE error handling paths |
| `CompanyResult` | 13 | `cmie/batch_pipeline.py` | Batch result schema — affects DB ingest |
| `TokenBucket` | 13 | `cmie/rate_limit.py` | Rate limiting on all 4 CMIE import sites |

**Rule:** if your change touches a god node, explicitly test every caller listed in `graphify-out/GRAPH_REPORT.md` before committing.

Full interactive graph: `graphify-out/graph.html` (open in browser)
