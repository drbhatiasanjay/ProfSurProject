# CMIE panel parity — Scenarios, Bulk Sync, verification

> **For Claude:** REQUIRED SUB-SKILL: Use **superpowers:executing-plans** (or **superpowers:subagent-driven-development**) to implement this plan task-by-task.
>
> **Companion strategy doc:** execution meta-plan (waves, skills/MCP picks, reusable patterns,
> past-mistake guards) lives in
> [`2026-04-21-cmie-refactor-execution-strategy.md`](2026-04-21-cmie-refactor-execution-strategy.md).

**Goal:** One coherent data story: when the CMIE lab is on and the user selects the CMIE panel, **Scenario Analysis** regressions and sample means use the **same active panel** as dashboards and peer benchmarks; **Bulk Upload → CMIE API Sync** aligns with **`CmieClient`** and safe caching; add automated tests and a short live verification checklist.

**Architecture:** Extract small **pure functions** for OLS coefficients and column means so pytest can cover them without spinning Streamlit. **`pages/3_scenarios.py`** calls `db.get_active_panel_data(ft)` (or equivalent filtered DataFrame) whenever `db.is_cmie_lab_enabled()`, `st.session_state.data_source_mode == "cmie"`, and `db.get_current_api_version()` are truthy; otherwise keep **`db.get_panel_data(ft)`** (not unfiltered `financials`) so sidebar filters apply. **`@st.cache_data`** on those computations must include **`ft`**, **data source mode**, and **`version_id`** (or `"none"`) in the function arguments so cache keys stay correct after import or filter changes. **`pages/4_bulk_upload.py`** tab 3 either delegates download to **`CmieClient.download_wapicall_zip`** / documented **`download_query_zip`** JSON shape or is reduced to a **link + caption** pointing to the CMIE sidebar import—avoid maintaining two incompatible `query.php` contracts.

**Tech stack:** Python 3.12 (project tests), Streamlit, pandas, numpy, SQLite via `db.py`, `cmie/client.py`, existing `tests/test_cmie_feature_gate.py`.

---

## Preconditions (read once)

- `db.get_active_panel_data(ft)` — same econometric columns as `get_panel_data`, with CMIE path joining packaged `financials` for `interest` / `int_rate` where needed (`db.py` ~331–358).
- `api_financials` includes `leverage`, `profitability`, `tangibility`, `tax`, `dividend`, `log_size`, `tax_shield` (`db.py` ~114–137).
- `pages/3_scenarios.py` today: `compute_coefficients` / `get_sample_means` query **`financials` only** and **ignore `ft`** (~19–77) — this is the core gap.
- `pages/4_bulk_upload.py`: `fetch_cmie_data` (~16–49) uses flat `data=payload` to `query.php`; **`CmieClient.download_query_zip`** uses `data={"apikey", "json": json.dumps(...)}` (`cmie/client.py` ~103–110). `_api_key` is excluded from Streamlit’s cache key — **cross-session leakage risk** on shared hosts.

**Verification commands (repo root):**

```text
py -3.12 -m pytest tests/test_cmie_feature_gate.py tests/test_database.py -v --tb=short
py -3.12 -m pytest tests/ -v --tb=short
```

---

### Task 1: Pure helpers for scenario regression

**Files:**

- Create: `models/scenario_regression.py`
- Test: `tests/test_scenario_regression.py`

**Step 1: Write failing tests**

In `tests/test_scenario_regression.py`, import functions (not yet created) from `models.scenario_regression`:

```python
import numpy as np
import pandas as pd
from models.scenario_regression import compute_leverage_ols_coefs, leverage_predictor_sample_means


def test_compute_leverage_ols_coefs_simple():
    df = pd.DataFrame({
        "leverage": [20.0, 30.0, 25.0],
        "profitability": [10.0, 5.0, 8.0],
        "tangibility": [30.0, 40.0, 35.0],
        "tax": [20.0, 20.0, 20.0],
        "log_size": [7.0, 8.0, 7.5],
        "tax_shield": [5.0, 5.0, 5.0],
        "dividend": [2.0, 2.0, 2.0],
    })
    coefs = compute_leverage_ols_coefs(df)
    assert "intercept" in coefs and "n_obs" in coefs
    assert coefs["n_obs"] == 3
    assert 0.0 <= coefs["r_squared"] <= 1.0


def test_sample_means_keys():
    df = pd.DataFrame({
        "profitability": [1.0, 3.0],
        "tangibility": [10.0, 20.0],
        "tax": [5.0, 15.0],
        "log_size": [2.0, 4.0],
        "tax_shield": [1.0, 2.0],
        "dividend": [0.5, 1.5],
    })
    m = leverage_predictor_sample_means(df)
    assert m["prof"] == 2.0
    assert m["tang"] == 15.0
```

**Step 2: Run tests — expect FAIL**

Run: `py -3.12 -m pytest tests/test_scenario_regression.py -v --tb=short`  
Expected: `ModuleNotFoundError` or `ImportError`.

**Step 3: Implement minimal module**

Create `models/scenario_regression.py`:

- `PREDICTORS = ["profitability", "tangibility", "tax", "log_size", "tax_shield", "dividend"]`
- `compute_leverage_ols_coefs(df: pd.DataFrame) -> dict` — drop rows with null `leverage` or any predictor; same `np.linalg.lstsq` logic as `pages/3_scenarios.py` today; on `LinAlgError` return the same fallback dict as current code (~54–58).
- `leverage_predictor_sample_means(df: pd.DataFrame) -> dict` — return keys `prof`, `tang`, `tax`, `log_size`, `tax_shield`, `dvnd` aligned with current `get_sample_means()` consumers (map from column AVGs).

**Step 4: Run tests — expect PASS**

Run: `py -3.12 -m pytest tests/test_scenario_regression.py -v --tb=short`

**Step 5: Commit**

```bash
git add models/scenario_regression.py tests/test_scenario_regression.py
git commit -m "test: add scenario OLS helpers with unit tests"
```

---

### Task 2: Scenarios page — active panel + filters in cache

**Files:**

- Modify: `pages/3_scenarios.py` (~18–77 and call sites)

**Step 1: Add failing integration test (optional but recommended)**

In `tests/test_scenario_regression.py` (or new `tests/test_scenarios_data_source.py`), mock `st.session_state` and monkeypatch `db.get_active_panel_data` / `get_panel_data` to return small DataFrames; call the **panel resolution** helper if you extract `_scenario_panel_df(ft)` into `models/scenario_regression.py` or a thin `pages/scenarios_data.py`. If full Streamlit test is too heavy, **skip** and rely on Task 1 + manual check — YAGNI for first merge.

**Step 2: Refactor `pages/3_scenarios.py`**

- Import `compute_leverage_ols_coefs`, `leverage_predictor_sample_means` from `models.scenario_regression`.
- Replace raw SQL in `compute_coefficients` / `get_sample_means` with:
  - `use_api = db.is_cmie_lab_enabled() and getattr(st.session_state, "data_source_mode", "sqlite") == "cmie" and db.get_current_api_version()`
  - If `use_api`: `panel = db.get_active_panel_data(ft)` else: `panel = db.get_panel_data(ft)`
  - Subset columns: ensure `leverage` + all predictors exist; `panel = panel.dropna(subset=[...])` before calling helpers.
- Change `@st.cache_data` signatures to accept **`filters_tuple`**, **`data_source`**, and **`version_id`** as arguments **without** a leading underscore (Streamlit **excludes** `_`-prefixed parameters from the cache key, which would break invalidation).

```python
@st.cache_data(ttl=3600)
def compute_coefficients(filters_tuple, data_source: str, version_id: str | None):
    ...
```

Call with `compute_coefficients(ft, st.session_state.get("data_source_mode", "sqlite"), db.get_current_api_version() if ... )`.

- If `panel` is empty after dropna, return the same fallback coef dict and neutral means (document in a one-line caption).

**Step 3: Run pytest**

`py -3.12 -m pytest tests/test_scenario_regression.py tests/test_cmie_feature_gate.py -v --tb=short`

**Step 4: Manual smoke**

`streamlit run app.py` → enable CMIE + import → CMIE data source → open Scenarios: check R² and n_obs change vs SQLite mode.

**Step 5: Commit**

```bash
git add pages/3_scenarios.py
git commit -m "feat(scenarios): OLS and means from active panel when CMIE mode on"
```

---

### Task 3: Bulk Upload CMIE tab — contract + cache + parse errors

**Files:**

- Modify: `pages/4_bulk_upload.py` (~16–49, tab3 ~346+)

**Step 1: Remove or fix `fetch_cmie_data`**

Preferred **minimal-risk** path:

- Delete `@st.cache_data` on the raw fetch **or** replace body with **`CmieClient(api_key)`** calling **`download_wapicall_zip([int(company_code)], dest_path=tmp_path)`** then read the first data `.txt` with **`cmie.zip_parse.read_tsv`** (or reuse `import_from_zip_file` only if you also want DB writes — usually tab3 only needs a DataFrame for display/mapping; align with product intent).
- If tab3 should **not** duplicate DB import, add `st.info` linking users to **Settings / CMIE sidebar** for authoritative import.

**Step 2: Cache key safety**

If any `@st.cache_data` remains for CMIE fetch, **never** use leading underscore on the API key for cache-key fields. Use e.g. `api_key_fingerprint: str` computed with **`hashlib.sha256(api_key.encode()).hexdigest()[:12]`** (same idea as `cmie/client.py` `_hash_key`) as a **positional** argument to the cached function.

**Step 3: Parsing**

Wrap `pd.read_csv(..., sep="\t")` in `try` / `except pd.errors.EmptyDataError` (and `ParserError`) with a clear return message.

**Step 4: Tests**

Add `tests/test_bulk_upload_cmie_parse.py` with a tiny **BytesIO** zip containing one `.txt` TSV line — or mark manual-only if zip fixture is heavy.

**Step 5: Commit**

```bash
git add pages/4_bulk_upload.py tests/test_bulk_upload_cmie_parse.py
git commit -m "fix(cmie): align bulk upload sync with CmieClient and safe cache keys"
```

---

### Task 4 (optional): Knowledge graph cache invalidation

**Files:**

- Modify: `pages/7_knowledge_graph.py` (~39–47)

**Step 1:** Add a cheap **`db_revision()`** helper in `db.py` (e.g. `SELECT MAX(rowid) FROM financials` or `PRAGMA data_version` / file mtime of `capital_structure.db` via `os.path.getmtime`).

**Step 2:** Change `_build_graph()` to `@st.cache_resource` with argument **`_db_rev: int`** from `db_revision()`; call `_build_graph(db_revision())` so reruns refresh after ingest.

**Step 3:** Commit — `fix(kg): invalidate graph cache when SQLite data changes`

---

### Task 5: End-to-end verification checklist (no code)

Execute after Tasks 1–3:

1. `ENABLE_CMIE=true`, `streamlit run app.py`.
2. Import one company via **wapicall** or **import-zip** (sidebar).
3. Switch **data source** to CMIE; confirm **Dashboard** and **Peer Benchmarks** match expectations.
4. **Scenarios:** compare coef `n_obs` to row count of filtered panel; toggle filters and confirm numbers update.
5. **Bulk Upload → CMIE API Sync:** live key + one company — no `ERROR.txt`, dataframe renders; optional mock path unchanged.

---

### Task 6: Plan index (optional)

Add one line to `CLAUDE.md` under commands: “CMIE execution plan: `docs/plans/2026-04-21-cmie-panel-scenarios-bulk-e2e.md`.”

---

## Risk notes (blast radius)

- **Wrong cache keys** → stale scenarios after CMIE re-import; mitigated by `_version_id` + `_filters_tuple` in cached function args.
- **Sparse CMIE panel** → OLS singular; existing `LinAlgError` fallback remains; add UI caption when `n_obs` is low.
- **Bulk tab writing to DB** — only add if explicitly required; default is display-only alignment with `CmieClient`.

---

## Execution handoff

**Plan saved to:** `docs/plans/2026-04-21-cmie-panel-scenarios-bulk-e2e.md`

**Two execution options:**

1. **Subagent-driven (this session)** — Use **superpowers:subagent-driven-development**: one subagent per task above, review between tasks.  
2. **Parallel session** — New chat with **superpowers:executing-plans**, paste path to this file, run tasks in order with checkpoints.

**Which approach do you want?**
