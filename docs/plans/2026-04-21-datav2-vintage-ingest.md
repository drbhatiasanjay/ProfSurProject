# DataV2 vintage ingest — extend panel to 2025 and beyond

**Date:** 2026-04-21
**Status:** proposal / pre-build
**Artefacts:** [docs/mocks/datav2_dashboard_mock.html](../mocks/datav2_dashboard_mock.html) (UI preview)

**Goal:** Load the four CMIE extract files in [`DataV2/`](../../DataV2/) into the existing SQLite store as an **additive vintage**, extend the panel from 2001–2024 → 2001–**2025**, light up ~639 T623 market indices, and establish a repeatable annual-refresh workflow that needs **no schema changes** for future drops.

**Design principle:** Treat each CMIE drop as a new `vintage` tag, never overwrite. Every existing page keeps working; new UI surfaces are additive and optional.

---

## 1. What DataV2 contains

Four pipe-delimited CMIE extract files, 2025 vintage:

| File | Rows | Period | What it is |
|---|---|---|---|
| [`T616_identityBSEnf401y2025.txt`](../../DataV2/T616_identityBSEnf401y2025.txt) | 400 firms | snapshot | Identity: Company Code, Name, Incorp year, Industry group (+code), Ownership group, Age group, Listing flag (all Y), NSE symbol |
| [`T617_financialsBSEnf401y2025.txt`](../../DataV2/T617_financialsBSEnf401y2025.txt) | 400 firms × **1 year** (`Slot Year = 20250331`) | Mar-2025 only | Standardised Annual Finance Standalone — `prof, tang, tax, dvnd, interest, size, PBIT, PBT, Intamt, Total capital, Reserves & funds, Borrowings, Debentures & bonds, Total liabilities, ncfo, ncfi, ncff, D/E, Total outside liabilities, Short-term borrowings` |
| [`T618_eq_ownerBSEnf401y2025.txt`](../../DataV2/T618_eq_ownerBSEnf401y2025.txt) | 400 firms × 1 year | Mar-2025 only | Shareholding pattern (27 cols incl. Promoters/Indian/Foreign, pledges, MFs, FIIs, insurance, VC/FVCI/QFI, custodians, individuals, corporates) |
| [`T623_indexBS500closing.txt`](../../DataV2/T623_indexBS500closing.txt) | 16,609 | 2000–2025 (26 years) | Mar-end closing values for **~639 distinct indices** — BSE Sensex/100/200/500, Nifty 50/500/sector, full suite of CMIE sector sub-indices |

## 2. Comparison vs. existing DB

**Firm universe** — 399 of 400 DataV2 firms overlap with `companies` (401 rows). Deltas:

- Only in DataV2: **Tata Motors Ltd.** with new code `729991` (old code `248093` in DB; changed post-demerger).
- Only in DB: `Gujarat State Petronet Ltd.` (86923) and the old Tata Motors code (248093).

**Financials** — T617 column names already match the ratio names the `financials` table uses (`prof`, `tang`, `tax`, `dvnd`, `interest`, `size`). One-for-one column map for ~20 of 24 fields; `lev_pct`, `ln_size`, `cls_code`/`life_stage` are **derivable** from T617 (ncfo/ncfi/ncff signs → Dickinson life stages). **Not in T617**: `st_invest`, `cash_bal`, `bank_bal`, `cash_holdings` — these stay NULL for 2025 rows.

**Ownership** — T618 covers every column in `ownership` plus extras (VC, Foreign VC, QFI, custodians, corporate bodies split).

**Market index** — Currently `market_index` stores only **Bse Sensex × 24 rows**. T623 is a **~665× expansion** (639 indices × 26 years). Biggest net-new data asset.

## 3. Database changes

| Table | Change | Why |
|---|---|---|
| `companies` | Add row for Tata Motors `729991`. Add columns `superseded_by INTEGER`, `delisted_in_year INTEGER`. Set `superseded_by=729991` on the old Tata Motors row; set `delisted_in_year=2024` on Gujarat State Petronet (86923). | Tata Motors code changed post-demerger; without this, 2025 rows and pre-2025 rows for the same firm won't join. |
| `financials` | Append ~400 rows for `year=2025`. Add columns `vintage TEXT` (default `"thesis"`; DataV2 rows tagged `"cmie_2025"`), `source_file TEXT`, `revised_in TEXT` (nullable). | Lets users filter "exclude 2025" with one predicate; keeps provenance clean; supports restatements. |
| `ownership` | Append 400 rows for `year=2025`. Add columns for the new T618 fields (`venture_capital`, `foreign_vc`, `qfi`, `custodians`, `non_promoter_individuals_small`, `non_promoter_individuals_large`). Nullable for 2001–2024. Add same `vintage`, `source_file`. | T618 has richer decomposition than the current schema. |
| `market_index` | New table `market_index_series` keyed on `(index_code, year)` with columns `index_name, slot_date, index_date, index_closing, vintage, source_file`. Preserve existing `market_index` as a view: `SELECT * FROM market_index_series WHERE index_code = 27749` (Sensex) for full back-compat with [`db.py:603-613`](../../db.py#L603-L613). | T623's 639 indices unlock sector benchmarks; old `market_index` consumers keep working unchanged. |
| `life_stages`, `v_*` views | No schema change. Re-run the CLS classifier on new rows only (ncfo/ncfi/ncff are present in T617). | Same pipeline the bulk-upload flow already uses. |
| `data_vintages` (new) | `(vintage TEXT PK, label TEXT, loaded_at TEXT, row_counts_json TEXT, description TEXT)`. | Drives the UI vintage multiselect and caption. |
| `financials_history` (new) | Same shape as `financials` + `archived_at`. Stores rows displaced by later restatements. | Audit trail for when CMIE revises prior-year numbers. |

One SQLite migration script; no break to existing columns.

## 4. Backend changes

**Ingestion** — new module `cmie/load_vintage.py`

- Reuses [`cmie/zip_parse.py`](../../cmie/zip_parse.py) / [`cmie/indicator_map.py`](../../cmie/indicator_map.py) — the `T616/T617/T618/T623` filenames already match what the CMIE pipeline expects. Adds a loader for loose `.txt` files (no zip).
- After insert, **recompute derived fields for new rows only**: `lev_pct`, `ln_size`, `log_size`, `tax_shield`, `cls_code`/`life_stage` (Dickinson), event dummies (`covid_dummy=0` for 2025, `ibc_2016=1`, `ibc_2016_20=0`), `int_rate`.
- Tata Motors code remap: insert new `companies` row, set `superseded_by` on old code. Read-path queries union both codes when displaying "Tata Motors" history.
- Restatement policy: on `(company_code, year, vintage)` conflict where the incoming vintage is newer, copy the old row into `financials_history` and replace.

**Query layer changes in [`db.py`](../../db.py)**

- [`get_year_range()`](../../db.py#L434) — no code change, auto-returns `(2001, 2025)`.
- [`get_market_index(year_min, year_max)`](../../db.py#L603-L613) — add `index_code` argument (default Sensex `27749` for back-compat). New helper `get_available_indices()` returns the ~639-series picker list.
- [`get_db_metadata()`](../../db.py#L641) — add `vintage_counts` so sidebar caption reads `"401 firms | 9,077 obs | 2001-2025 (CMIE 2025 included)"`.
- New `get_data_vintages()` helper (returns rows from `data_vintages`). A `panel_mode` argument is added to `_build_where(...)` that maps to a vintage predicate:
  - `panel_mode = "thesis"` → `WHERE vintage = 'thesis'`
  - `panel_mode = "latest"` → `WHERE vintage IN ('thesis','cmie_2025')` (auto-extends as new vintages load)
  Every query that hits `financials`/`ownership` honours `st.session_state.panel_mode`.
- All `@st.cache_data` decorators key on arguments, so adding `panel_mode` invalidates cleanly. `db_cache_revision()` bumps via mtime after each load.

**Tests** — extend [`tests/test_database.py`](../../tests/test_database.py) with:
- 2025 row count assertions (financials = 400, ownership = 400).
- Tata Motors code-merge join test (old + new codes return unified history).
- `market_index_series` multi-series query test.
- Panel-mode predicate test (`thesis` vs `latest` return expected row counts).
- Restatement test (older row moves to `financials_history`).

## 5. UI changes

See mock: [docs/mocks/datav2_dashboard_mock.html](../mocks/datav2_dashboard_mock.html)

**Sidebar** ([`app.py`](../../app.py))

- **New "Panel" control** (single-select dropdown or radio) near [`app.py:59-65`](../../app.py#L59-L65). Two options, named by intent not by data source:
  - `Thesis panel (2001–2024)` — original 401-firm panel, preserves thesis reproducibility.
  - `Latest panel (2001–2025)` — thesis + CMIE 2025 rollforward (default on Dashboard/Benchmarks/Explorer).
  Wires into `st.session_state.panel_mode` (values: `"thesis"` or `"latest"`). Per-page defaults: Dashboard/Benchmarks/Explorer land on `latest`; Econometrics/ML/Forecasting land on `thesis`.
- Year slider at [`app.py:59-65`](../../app.py#L59-L65) auto-adjusts to the selected panel's year range via `get_year_range(panel_mode)`. **Slider remains fully draggable** with both handles (existing `st.slider` behaviour).
- Caption at [`app.py:94`](../../app.py#L94) reflects the active panel: `401 firms | 8,677 obs | 2001–2024` (thesis) or `401 firms | 9,077 obs | 2001–2025 • includes CMIE 2025` (latest).

**Per-page changes**

- [`pages/1_dashboard.py`](../../pages/1_dashboard.py) — line 243 `get_market_index(...)` gets an **index picker** (selectbox sourced from `get_available_indices()`). Add a "Compare to sector index" widget that draws CMIE sector series alongside leverage.
- [`pages/2_peer_benchmarks.py`](../../pages/2_peer_benchmarks.py) — add a "2025 snapshot" tab that shows current-year peer medians separately from the 2001–2024 historical panel.
- [`pages/5_data_explorer.py`](../../pages/5_data_explorer.py) — show `vintage` column; add a badge/chip on rows sourced from CMIE 2025.
- [`pages/10_forecasting.py`](../../pages/10_forecasting.py) — hold out 2025 as the natural test year; add a "Predicted vs. actual 2025" panel.
- [`pages/8_econometrics.py`](../../pages/8_econometrics.py), [`pages/9_ml_models.py`](../../pages/9_ml_models.py) — toggle "Include 2025 in training" (off by default).
- **New** [`pages/15_market_indices.py`](../../pages/15_market_indices.py) — charts the ~639 T623 series, sector-vs-firm leverage overlays, CMIE industry index benchmarking.

**KPI cards added to Dashboard**

- "Latest year: 2025" (CMIE Mar-2025 close)
- "Market indices: 639 (was 1 — Sensex only)"

## 6. Future-proofing — annual refresh workflow

CMIE publishes yearly. Every future drop follows the **same workflow**, no schema changes:

```
DataV2/  → vintage="cmie_2025" → adds 400 rows at year=2025
DataV3/  → vintage="cmie_2026" → adds 400 rows at year=2026
DataV4/  → vintage="cmie_2027" → adds 400 rows at year=2027
```

Operational command:

```bash
python -m cmie.load_vintage ./DataV3 --vintage cmie_2026
```

~30 seconds. No UI change, no redeployment, no manual SQL.

**What auto-works on each load:**

- Slider max extends (reads `MAX(year)` from DB, scoped to the active panel mode).
- `Latest panel` option auto-absorbs the new vintage — its predicate grows from `IN ('thesis','cmie_2025')` to `IN ('thesis','cmie_2025','cmie_2026')`. The dropdown stays a clean two-option control; the "Thesis panel" option is frozen as the reproducibility anchor.
- `get_db_metadata()` caption auto-updates: `401 firms | 9,477 obs | 2001–2026`.
- All existing pages keep working; they just see one more year of data.

**Edge cases to handle on each load:**

| Situation | Policy |
|---|---|
| **Restatements** — CMIE revises 2025 in the 2026 file | On `(company_code, year)` conflict with newer vintage: replace the row, copy old values to `financials_history`, stamp `revised_in` on the new row. |
| **New firms enter the BSE 401** | Insert to `companies` with first-seen year. Historical rows simply don't exist for them; charts already handle sparse panels. |
| **Firms delist / merge** (like Gujarat State Petronet) | Set `delisted_in_year`. Keep rows so history charts still draw; fade out post-delisting. |
| **Code changes** (like Tata Motors `248093` → `729991`) | Use `superseded_by` chain on `companies` — same mechanism reused. |
| **New columns in T617/T618** | Loader lands files into `raw_cmie_*` staging first. Unknown columns log a warning but don't break ingest. Widen schema on your schedule. |
| **T623 grows** (new indices launch, old ones retire) | `(index_code, year)` upsert in `market_index_series`. Picker gains/drops entries automatically. |
| **Re-derive analytics** | Loader recomputes `life_stage`, `lev_pct`, `ln_size`, event dummies, `int_rate` **for new rows only**. |

**Sprawl control** — the two-option dropdown (`Thesis panel` / `Latest panel`) does not grow with new vintages. "Latest panel" silently absorbs each new CMIE drop; users never see vintage sprawl. Power users who want to isolate a specific vintage for forensic work can use the SQL layer directly — no UI exposure needed.

## 7. Reproducibility safeguard

- **Default `panel_mode = "thesis"`** on **Econometrics / Forecasting / ML** pages so published thesis results reproduce bit-for-bit.
- **Default `panel_mode = "latest"`** on **Dashboard / Benchmarks / Explorer** so latest data shows by default.
- The "Thesis panel" option is **frozen at 2001–2024** forever — it is the reproducibility anchor, not a rolling window. Future CMIE drops extend "Latest panel" only.
- Interpretation expander on each chart notes panel context: "Latest panel (includes CMIE 2025)" / "Thesis panel (2001–2024)".

## 8. Rollout plan (one day of work)

| Step | Time | Artefact |
|---|---|---|
| 1. Schema migration (`vintage` column + `data_vintages` + `market_index_series` + `financials_history`) | 1 hr | `migrations/003_datav2_vintage.sql` |
| 2. Loader script `cmie/load_vintage.py` — parses four T-files, upserts, handles Tata Motors remap | 2 hr | new module + tests |
| 3. `db.py` query updates (`vintages` filter, `get_available_indices`, metadata) + tests | 1.5 hr | edits to `db.py`, `tests/test_database.py` |
| 4. Sidebar vintage toggle + index picker on Dashboard | 1 hr | edits to `app.py`, `pages/1_dashboard.py` |
| 5. New `pages/15_market_indices.py` | 1.5 hr | new page |
| 6. Reproducibility defaults on Econometrics / ML pages + interpretation notes | 1 hr | edits to `pages/8,9,10` |

Total: ~8 hr. Rollout is reversible — each step lands in its own commit, the `vintage` filter can be short-circuited to hide DataV2 if anything misbehaves in prod.

## 9. Acceptance checks

- `SELECT COUNT(*) FROM financials WHERE year = 2025` → 400.
- `SELECT COUNT(*) FROM ownership WHERE year = 2025` → 400.
- `SELECT COUNT(DISTINCT index_code) FROM market_index_series` → 639.
- Sidebar in "Latest panel" mode shows `401 firms | 9,077 obs | 2001–2025`.
- Sidebar in "Thesis panel" mode shows `401 firms | 8,677 obs | 2001–2024` and the year slider caps at 2024.
- Switching the panel dropdown invalidates `@st.cache_data` caches and all charts redraw without a manual rerun.
- Econometrics page lands on "Thesis panel" by default and reproduces thesis Table 4 coefficients to ≥ 4 decimal places.
- Dashboard page lands on "Latest panel" by default and shows 2025 data in all charts.
- Tata Motors page shows continuous history 2001–2025 in Latest mode (joins both `248093` and `729991`).
- Re-running the loader on the same files is idempotent (no duplicate rows).

## 10. Open questions — decisions (2026-04-21)

| # | Question | Decision |
| --- | --- | --- |
| 1 | UI vintage label — `CMIE 2025` vs `cmie_2025` vs both? | **Separate**: DB stores `cmie_2025` (stable code value); UI shows human labels via `data_vintages.label`. User-facing control is a two-option **"Panel"** dropdown (`Thesis panel (2001–2024)` / `Latest panel (2001–2025)`) named by intent rather than by vintage codes. |
| 2 | Ship `pages/15_market_indices.py` in v1 or defer? | **Defer to v1.1.** T623 data still loads; Dashboard macro picker exposes all ~639 series immediately. A dedicated browser page deserves proper design after real usage. |
| 3 | Restatement default — silent replace or "revised" badge? | **Silent replace, always write audit trail.** Move displaced rows to `financials_history` with `archived_at` and `archived_from_vintage`; stamp `revised_in` on the replacement. Data Explorer gets a small footer counter (`"N rows revised in cmie_2026"`). Full per-cell badges only if explicitly requested later. |
| 4 | Gujarat State Petronet retention — keep or archive? | **Keep permanently with `delisted_in_year=2024`.** Thesis reproducibility is non-negotiable. Apply the same policy to the old Tata Motors code (`248093`) via `superseded_by=729991`. Default queries use `WHERE delisted_in_year IS NULL` for "current universe" views; historical charts show firms until their exit year. |
