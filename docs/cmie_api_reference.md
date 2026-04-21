# CMIE Economy API — Reference & Data-Load Guide

> How the **LifeCycle Leverage Dashboard** fetches live company financials from the CMIE
> Economy Outlook / Prowess Economy API and loads them into `capital_structure.db`.
>
> Source of truth in code: [`cmie/`](../cmie/) package.
> Public docs: <https://economyapi.cmie.com/> (section **"example_js"** shows the tabular JSON shape).

---

## 1. What CMIE exposes

CMIE (Centre for Monitoring Indian Economy) offers a paid HTTP API (Economy Outlook / Prowess
subscription) that returns Indian macro + company financial data. This project uses **three
transports**, all rooted at `https://economyapi.cmie.com`:

| # | Transport | Endpoint | Body | Returns | Used for |
|---|-----------|----------|------|---------|----------|
| 1 | **Legacy streaming ZIP** | `POST /query.php` | `multipart/form-data` — `apikey`, `json` (string) | ZIP of TSVs | Bulk company panels (`scheme=MITS` + company_code) |
| 2 | **Form → tabular JSON** | `POST /query.php` | `application/x-www-form-urlencoded` — `apikey` + scheme fields (`scheme`, `indicnum`, `freq`, `nperiod`, …) | JSON `{ head: […], data: […] }` | Indicator time-series (macro / scheme queries) |
| 3 | **Wapicall company ZIP** | `POST /kommon/bin/sr.php?kall=wapicall` | `application/json` — `{ apikey, company_code: [ … ] }` | ZIP of TSVs (`ERROR.txt` if failure) | Consolidated per-company download (≤ 10 codes, 3 hits/company/day) |

Constants (see [`cmie/client.py:23-25`](../cmie/client.py#L23-L25)):

```python
CMIE_QUERY_URL    = "https://economyapi.cmie.com/query.php"
CMIE_WAPICALL_URL = "https://economyapi.cmie.com/kommon/bin/sr.php?kall=wapicall"
```

---

## 2. Authentication

- **Credential:** a single string `apikey` tied to your Prowess / Economy Outlook subscription.
- Sent **in the POST body** (never in the query string / URL). For every transport:
  - Legacy ZIP: form field `apikey`
  - Form tabular: form field `apikey`
  - Wapicall: JSON key `apikey`
- Failures surface as **HTTP 401/403**, or **HTTP 200 + `ERROR.txt`** inside the ZIP containing
  words like `apikey`, `unauthorized`, `login`, `permission`, `subscribe`, or `entitle`.

### Where the key lives in this project

Priority order:

1. `st.secrets["CMIE_API_KEY"]` — Streamlit Cloud / `.streamlit/secrets.toml`
2. Environment variable `CMIE_API_KEY` — local / Docker / Cloud Run
3. Sidebar password field (`Settings → CMIE API key (session only)`) — for one-off sessions

**Never** commit the key; `.streamlit/secrets.toml` is in `.gitignore`.

---

## 3. Transport #1 — Legacy streaming ZIP (`query.php` + `json` field)

Use when you need a **full company panel** (many indicators × many years for one company or a
small batch).

### Request

```
POST https://economyapi.cmie.com/query.php
Content-Type: multipart/form-data

apikey=<KEY>
json={"scheme":"MITS","freq":"A","company_code":100001}
```

### Response

- **200 OK** with `Content-Type: application/zip` and a binary body.
- The client streams the body to disk in 256 KB chunks
  ([`client.py:181-193`](../cmie/client.py#L181-L193)).
- Zip is sanity-checked with `zipfile.is_zipfile` — CMIE sometimes replies `200` + HTML/JSON
  error body, which raises `CmieZipError("ZIP_BAD", …)` with a 2 KB snippet
  ([`client.py:59-92`](../cmie/client.py#L59-L92)).

### Zip contents

| File | Meaning |
|------|---------|
| `data_*.txt` | Tab-separated table, first row = headers. Parsed by [`cmie/zip_parse.py`](../cmie/zip_parse.py) via `pandas.read_csv(sep="\t", dtype=str)`. |
| `ERROR.txt`  | Present only on failure — classified by [`raise_if_error_txt()`](../cmie/zip_parse.py#L52-L63) into `CmieAuthError` / `CmieEntitlementError` / `CmieParseError`. |

### Code entry points

| Action | Function |
|--------|----------|
| Download | [`CmieClient.download_query_zip()`](../cmie/client.py#L121) |
| Single import | [`pipeline.import_from_zip_file()`](../cmie/pipeline.py#L158) |
| Merge many zips → one version | [`pipeline.merge_zip_paths_to_version()`](../cmie/pipeline.py#L86) |
| CLI | `python -m cmie download --payload-json '{…}' --out-zip resp.zip` then `python -m cmie import-zip resp.zip` |

### Batch mode (≤ 10 companies per run — see §7)

JSON template must include the placeholder `__CMIE_COMPANY_CODE__`; the client substitutes it
per code ([`batch_utils.json_payload_for_company()`](../cmie/batch_utils.py#L40)).

```json
{"scheme":"MITS","freq":"A","company_code": __CMIE_COMPANY_CODE__}
```

CLI:

```bash
python -m cmie batch-download \
  --codes "100001,100002,100003" \
  --payload-json-file tpl.json \
  --out-dir ./zips \
  --delay 1.0
python -m cmie merge-zips ./zips/*.zip --min-years 1
```

---

## 4. Transport #2 — Form tabular JSON (`query.php`, form fields)

Use for **indicator / scheme queries** that return a rectangular table rather than a per-company
panel. Matches the public **"example_js"** pattern on CMIE's docs page.

### Request

```
POST https://economyapi.cmie.com/query.php
Content-Type: application/x-www-form-urlencoded

apikey=<KEY>&scheme=MITS&indicnum=1,2&freq=Q&nperiod=14
```

### Response shape

```json
{
  "head": ["company_code", "year", "leverage", "profitability", "tangibility"],
  "data": [
    [100001, 2019, 0.42, 0.11, 0.55],
    [100001, 2020, 0.45, 0.09, 0.57]
  ]
}
```

- `head` / `data` may also be nested under `meta` — both shapes handled by
  [`cmie_tabular_json_to_dataframe()`](../cmie/query_form.py#L16).
- `data` rows may be list-of-lists *or* list-of-dicts; both are supported.

### Code entry points

| Action | Function |
|--------|----------|
| Network call | [`CmieClient.post_query_form()`](../cmie/client.py#L219) |
| Parse JSON → DataFrame | [`cmie_tabular_json_to_dataframe()`](../cmie/query_form.py#L16) |
| Full pipeline | [`pipeline.import_from_raw_dataframe()`](../cmie/pipeline.py#L27) |

---

## 5. Transport #3 — Wapicall company ZIP

Use when a CMIE subscription exposes the **consolidated company download** endpoint (the one the
Prowess web UI uses for "download all data for this company"). Sends **JSON** (not form-encoded)
and accepts up to 10 `company_code` ints per call.

### Request

```
POST https://economyapi.cmie.com/kommon/bin/sr.php?kall=wapicall
Content-Type: application/json

{
  "apikey": "<KEY>",
  "company_code": ["100001", "100002"]
}
```

Note: codes are **stringified** in the JSON body (matches CMIE's published example; see
[`client.py:292`](../cmie/client.py#L292)).

### Response

Same ZIP-of-TSV + optional `ERROR.txt` layout as transport #1 — parsed by the same
[`parse_cmie_company_download_zip()`](../cmie/wapicall_table.py#L13) helper.

### Quota

CMIE docs state a hard limit of **3 hits/company/day** for wapicall. The Streamlit batch UI
enforces `MAX_BATCH_COMPANIES = 10` per click to keep well within that ceiling
([`streamlit_import.py:99`](../cmie/streamlit_import.py#L99)).

### Code entry points

| Action | Function |
|--------|----------|
| Download | [`CmieClient.download_wapicall_zip()`](../cmie/client.py#L277) |
| Parse | [`parse_cmie_company_download_zip()`](../cmie/wapicall_table.py#L13) |

---

## 6. Payload schema — confirmed-by-code vs. owned-by-CMIE-docs

> **Honest scope audit.** This codebase is a **transport + parser**, not a scheme catalogue.
> Half the payload is encoded in code (so you can rely on it); half is pass-through to CMIE
> (so you must consult CMIE's docs / your account entitlement sheet). This section separates
> the two so you don't conflate them.

### 6.1 ✅ What the code *fully* pins down (wire-level)

Anything here is enforced by `CmieClient` — CMIE *will* see exactly these bytes:

| Layer | Guaranteed value | Source |
|---|---|---|
| Legacy URL | `https://economyapi.cmie.com/query.php` | [`client.py:23`](../cmie/client.py#L23) |
| Wapicall URL | `https://economyapi.cmie.com/kommon/bin/sr.php?kall=wapicall` | [`client.py:25`](../cmie/client.py#L25) |
| Legacy ZIP body encoding | `multipart/form-data`, fields `apikey=<str>` and `json=<json-string>` | [`client.py:146-148`](../cmie/client.py#L146-L148) |
| Form body encoding | `application/x-www-form-urlencoded`, `apikey=<str>` + caller's fields as strings | [`client.py:226-243`](../cmie/client.py#L226-L243) |
| Wapicall body encoding | `application/json`, `{"apikey": str, "company_code": [str, …]}` | [`client.py:292, 308`](../cmie/client.py#L292) |
| `company_code` type in wapicall | Stringified ints, array | [`client.py:292`](../cmie/client.py#L292) |
| Batch placeholder | `__CMIE_COMPANY_CODE__` (literal substring, one-shot replace) | [`batch_utils.py:50-55`](../cmie/batch_utils.py#L50-L55) |
| Batch size ceiling | `MAX_BATCH_COMPANIES = 10` | [`batch_utils.py:10`](../cmie/batch_utils.py#L10) |
| Download streaming chunk | 256 KB (`1024 * 256`) | [`client.py:181, 333`](../cmie/client.py#L181) |

### 6.2 ⚠️ What the code shows only as **placeholder defaults** (needs CMIE docs)

These appear as default values in the UI but are **not validated** — the client forwards
whatever the caller puts in the JSON/form. You must verify each against **your CMIE account's
scheme sheet**:

| Field | Default we seed | Where | Meaning (per CMIE convention) |
|---|---|---|---|
| `scheme` | `"MITS"` | [`streamlit_import.py:89, 137`](../cmie/streamlit_import.py#L89) | Dataset family. `MITS` = Prowess company financials. Other CMIE schemes exist (macro, industry, markets). **Code does not enumerate them.** |
| `indicnum` | `"1,2"` | [`streamlit_import.py:89`](../cmie/streamlit_import.py#L89) | Comma-separated indicator IDs inside a scheme. Valid IDs are **scheme-specific** and listed in CMIE's online indicator browser. |
| `freq` | `"A"` / `"Q"` | [`streamlit_import.py:89, 137`](../cmie/streamlit_import.py#L89) | Periodicity. Conventional values: `A` (annual), `Q` (quarterly), `M` (monthly). **Not validated client-side.** |
| `nperiod` | `"14"` | [`streamlit_import.py:89`](../cmie/streamlit_import.py#L89) | Number of periods (back from latest). **Maximum depends on subscription.** |
| `company_code` | caller-supplied int | legacy — user's JSON; wapicall — `[str(c)]` | 6-digit Prowess identifier. **Numeric or stringified — code does not assume; batch_utils.py:40 comment says "adjust to match CMIE's expected field types".** |

**Takeaway:** before you trust a payload end-to-end, ask CMIE support for:
1. The list of `scheme` codes enabled on your subscription.
2. The `indicnum` catalogue per scheme (the Prowess web UI ships a CSV/XLS).
3. The `freq` values your scheme accepts.
4. Whether `company_code` in the legacy `json` field is expected as **number** or **string**
   — in wapicall it's always an array of strings.

### 6.3 🧪 Minimal payloads the code has been exercised with

Grep across the repo (`scheme|indicnum|MITS|freq`) shows only these concrete payloads actually
appearing in commits — treat them as starting points, not authoritative:

```json
// Legacy ZIP, single company (streamlit_import.py:137)
{"scheme":"MITS","freq":"A"}

// Legacy ZIP, batch template (docs pattern)
{"scheme":"MITS","freq":"A","company_code": __CMIE_COMPANY_CODE__}

// Form tabular (streamlit_import.py:89)
{"scheme": "MITS", "indicnum": "1,2", "freq": "Q", "nperiod": "14"}

// Wapicall (client.py:292)  ← fully generated by the client, never user-authored
{"apikey":"…","company_code":["100001","100002"]}

// Test fixture (tests/test_cmie_batch_utils.py:18)
{"scheme":"MITS","co":"__CMIE_COMPANY_CODE__"}
```

### 6.4 Response shape — what the **parsers** require

Even if CMIE accepts a payload, the downstream pipeline will reject it unless the response
contains these columns (after [`indicator_map.COLUMN_ALIASES`](../cmie/indicator_map.py#L14)
is applied):

| Column | Required? | Alias variants accepted | Purpose |
|---|---|---|---|
| `company_code` | **Yes** (hard) | `comp_code`, `companycode`, `firm_code` | Entity key; `CmieSchemaError` if missing |
| `year` | **Yes** (hard) | `fy`, `financial_year`, `year_` | Time key; `CmieSchemaError` if missing |
| `leverage` | **Yes** (soft) | — | `CmieValidationError` if missing or ≥35 % NaN |
| `profitability`, `tangibility`, `firm_size` | Recommended | — | Soft NaN check; warns but does not block |
| `tax`, `dividend`, `tax_shield`, `borrowings`, `total_liabilities`, `cash_holdings`, `ncfo`, `ncfi`, `ncff` | Optional | — | Coerced to numeric if present; kept if in `CANONICAL_COLUMNS` |
| Anything else | Dropped | — | Not in `CANONICAL_COLUMNS` → removed at normalize time |

If your scheme returns different column names, add them to
[`cmie/indicator_map.COLUMN_ALIASES`](../cmie/indicator_map.py#L14) and extend
[`normalize.CANONICAL_COLUMNS`](../cmie/normalize.py#L13-L37) — otherwise a technically-valid
response will silently lose data.

### 6.5 Bottom line

- **The *envelope* is fully analyzed and locked down in code** — URLs, auth field, encoding,
  `company_code` array shape for wapicall, batch semantics, retry/timeout.
- **The *contents* of the envelope** (`scheme`, `indicnum`, `freq`, `nperiod`, which columns
  come back) are **not** exhaustively enumerated in code — they're CMIE-subscription-specific
  and must be cross-referenced with CMIE's indicator catalogue.

---

## 7. Rate limits, performance, retries, timeouts & known issues

Everything in this section is pulled directly from [`cmie/client.py`](../cmie/client.py),
[`cmie/rate_limit.py`](../cmie/rate_limit.py), and [`cmie/streamlit_import.py`](../cmie/streamlit_import.py).
Numbers are the **actual** values compiled into the binary — not recommendations.

### 7.1 Rate limits — what we know

| Scope | Value | Source | Enforced by |
|---|---|---|---|
| **Wapicall hits / company / day** | **3** | CMIE public docs (quoted in UI caption) | CMIE server → returns `ERROR.txt` or 429 |
| **Streamlit batch size** | `MAX_BATCH_COMPANIES = 10` | [`batch_utils.py:10`](../cmie/batch_utils.py#L10) | UI + CLI `parse_company_codes()` |
| **Inter-request delay (legacy batch, CLI)** | `--delay 1.0` s default | [`__main__.py:221`](../cmie/__main__.py#L221) | CLI loop `time.sleep(ns.delay)` |
| **Inter-request delay (legacy batch, UI)** | `1.0` s default, 0–60 s settable | [`streamlit_import.py:151`](../cmie/streamlit_import.py#L151) | UI loop `time.sleep(delay_s)` |
| **Per-account daily RPS** | *Not pinned in code* — CMIE enforces | — | Remote `429`, `Retry-After` |
| **In-process `TokenBucket`** | **Optional, unset by default** | [`rate_limit.py`](../cmie/rate_limit.py), [`client.py:117`](../cmie/client.py#L117) | Caller must pass `limiter=` |

> ⚠️ **Gap.** `CmieClient(limiter=...)` is optional and **no caller in the repo currently wires
> one up** (Streamlit, CLI, pipeline all pass `limiter=None`). If you're sharing one API key
> across multiple users / tabs / processes, add `TokenBucket(rate_per_sec=1.0, burst=3)` or
> similar at the call site. Otherwise you rely entirely on CMIE's server-side throttle.

### 7.2 Server signals we handle

All three transports handle these status codes identically:

| Status | Raised as | Retries? | Notes |
|---|---|---|---|
| 200 OK + valid ZIP / JSON | — (success) | — | — |
| 200 OK + non-zip body | `CmieZipError("ZIP_BAD")` | No | 2 KB snippet captured for debug |
| 200 OK + `ERROR.txt` in zip | `CmieAuthError` / `CmieEntitlementError` / `CmieParseError` | No | Keyword-classified by [`raise_if_error_txt()`](../cmie/zip_parse.py#L52) |
| 401 / 403 | `CmieAuthError("AUTH")` | **No** — fail fast | User action required |
| 429 | `CmieRateLimitError("RATE_LIMIT_REMOTE")` | **No** — fail fast | `Retry-After` header surfaced in `error.detail` |
| 5xx | `CmieNetworkError("SERVER")` | **Yes** (up to 4×) | — |
| Other non-200 | `CmieNetworkError("HTTP")` | Yes | Detail = `HTTP <code>` |
| `requests.Timeout` | `CmieNetworkError("TIMEOUT")` | Yes | — |
| `requests.RequestException` | `CmieNetworkError("NETWORK")` | Yes | Connection reset, DNS, TLS, etc. |
| Invalid JSON (form transport) | `CmieNetworkError("JSON")` | Yes | — |

See [`client.py:150-174`](../cmie/client.py#L150-L174), [`client.py:244-275`](../cmie/client.py#L244-L275),
[`client.py:311-327`](../cmie/client.py#L311-L327).

### 7.3 Retry policy (exact formula)

Applied automatically in **all three** download/post methods:

- **Max retries:** `max_retries = 4` (so **up to 5 total attempts**).
- **Skipped for:** `CmieAuthError`, `CmieRateLimitError` — these propagate immediately.
- **Backoff (seconds):**

  ```
  base    = 1.0 * 2 ** (attempt - 1)        # 1, 2, 4, 8, 16 …
  capped  = min(20.0, base)                 # hard cap at 20 s
  jitter  = 0.7 + 0.6 * random.random()     # × [0.7, 1.3]
  sleep_s = capped * jitter
  ```

  So the worst-case total wait across 4 retries is roughly:
  `1 + 2 + 4 + 8 = 15` s (nominal) → `~10–20` s with jitter and the 20 s cap.

- Code: [`client.py:208-214`](../cmie/client.py#L208-L214), duplicated in `post_query_form`
  and `download_wapicall_zip`.

> ⚠️ **`Retry-After` is not honored for automatic retry.** We receive it on 429, surface it
> in `error.detail`, and then **raise** — the user / caller must decide to sleep and retry.
> This is deliberate (CMIE's 429 almost always means a daily/per-company quota that won't
> recover in seconds).

### 7.4 Timeouts

| Surface | Default | Set where |
|---|---|---|
| `CmieClient(timeout_s=…)` library default | **120 s** | [`client.py:111`](../cmie/client.py#L111) |
| Streamlit importer | **600 s** | [`streamlit_import.py:179, 232, 285, 335`](../cmie/streamlit_import.py#L179) |
| CLI `download` / `batch-download` | **600 s** (`--timeout`) | [`__main__.py:189, 220`](../cmie/__main__.py#L189) |
| `TokenBucket.acquire(timeout_s=10)` (local limiter wait) | 10 s | [`client.py:134, 236, 298`](../cmie/client.py#L134) |

The `requests.post(..., timeout=N)` is a **per-attempt read timeout**. A 600 s timeout × 4
retries × jitter can in theory take ~50 minutes on a stuck connection — in practice the
network layer fails fast.

### 7.5 Performance characteristics

Measured against `cmie/client.py` behavior, not benchmarks:

| Aspect | Behavior |
|---|---|
| **Streaming download** | Yes — 256 KB chunks, constant memory (`resp.iter_content(chunk_size=1024*256)`). OK for multi-hundred-MB zips. |
| **Progress callback** | Called after every chunk with `{received_bytes, total_bytes, elapsed_s}` + derived `pct`, `bytes_per_s`, `eta_s`. |
| **Content-Length** | Used when present; pct/ETA `None` when missing (CMIE sometimes omits it → UI shows `?`). |
| **Concurrency** | **Sequential**, not parallel. Batch loop downloads one zip at a time with `time.sleep(delay)` between them. No `ThreadPool`. |
| **Disk I/O** | Each zip is written to `tempfile.gettempdir()/cmie_<import_id>/…` then extracted in-place. Not cleaned up on failure — manual `%TEMP%` sweep if retrying a lot. |
| **Parsing cost** | `pandas.read_csv(sep='\t', engine='python', dtype=str, on_bad_lines='skip')` — **python engine** (slower than C) chosen for forgiving bad-line handling. Swap to `engine='c'` in [`zip_parse.py:66-76`](../cmie/zip_parse.py#L66-L76) if you trust the CMIE export. |
| **SQLite writes** | Single `INSERT` pass in `db.write_api_financials(version_id, panel)` — typically fast (< 1 s for 10 companies × 20 years). |
| **Streamlit `@st.cache_data` invalidation** | Cache key **must include** `data_source_mode`, `version_id`, and `filters_tuple` — see the note in [`docs/plans/2026-04-21-cmie-panel-scenarios-bulk-e2e.md`](plans/2026-04-21-cmie-panel-scenarios-bulk-e2e.md) (Task 2). Streamlit ignores underscore-prefixed parameters, so `_api_key` is safely excluded — but that *also* means you cannot rely on cache-miss-on-new-key unless you add an explicit version arg. |

### 7.6 Known issues & gotchas

| # | Issue | Impact | Mitigation |
|---|---|---|---|
| 1 | **HTML body with HTTP 200** | CMIE sometimes returns a login/error page as a 200 with `text/html`. `zipfile.is_zipfile` fails → `CmieZipError("ZIP_BAD")` with 2 KB snippet. | Check snippet in `error.detail`; usually auth/quota — retry is pointless. |
| 2 | **Silent column drop** | Any CMIE column outside `CANONICAL_COLUMNS` is dropped at normalize time with no warning. | Add new headers to [`indicator_map.py`](../cmie/indicator_map.py) + [`normalize.py`](../cmie/normalize.py). |
| 3 | **`company_code` type mismatch (legacy)** | Some schemes want `"company_code":100001` (int), others `"100001"` (string). Code is agnostic and CMIE may 200 + garbage. | Try both; the batch_utils docstring at [`batch_utils.py:41-48`](../cmie/batch_utils.py#L41-L48) flags this. |
| 4 | **Streamlit request disconnect** | Browser sleep / reverse proxy idle timeout kills the 600 s request. | Use `python -m cmie download …` + `import-zip` — same DB, no UI dependency. |
| 5 | **API key caching leakage** | `pages/4_bulk_upload.py::fetch_cmie_data(_api_key, …)` passes `_api_key` which Streamlit excludes from cache key → **cached response from another session's key can be served**. | Either delete the cache on logout, or migrate that page to `CmieClient` (tracked in the panel-parity plan doc). |
| 6 | **Retry amplifies quota burn** | 4 retries on a 5xx that is actually a quota mask can consume 5 wapicall hits → blow the 3/company/day limit. | Keep an eye on `ERROR.txt` classification; if entitlement errors come back as 5xx, short-circuit manually. |
| 7 | **No global limiter wired up** | Multi-user Streamlit deployments share one key → concurrent requests. | Pass a `TokenBucket` to `CmieClient` at the call site (one-line change in `streamlit_import.py`). |
| 8 | **`find_data_txt_files` picks up all `.txt`** | Any `readme.txt` / `notes.txt` in a future CMIE zip would be parsed as data and blow up `pd.read_csv`. | Tighten the filter in [`zip_parse.py:79-85`](../cmie/zip_parse.py#L79-L85) if CMIE changes archive layout. |
| 9 | **`@dataclass(frozen=True)` on `CmieError`** | Makes exceptions hashable but immutable — you can't add attributes downstream. | Construct a new error rather than mutating. |
| 10 | **Validation requires ≥ 3 unique years** | Single-year imports fail `CmieValidationError("VALIDATION")`. | Pass `--min-years 1` for one-off tests; keep default `3` for econometric use. |
| 11 | **Retry-After not auto-slept** | 429 fails fast, even if `Retry-After: 60` says retry in 1 min. | Wrap CLI in a shell `sleep` loop, or add a wrapper that inspects `CmieRateLimitError.detail`. |
| 12 | **Tempfiles accumulate** | Failed imports leave zips in `%TEMP%/cmie_<id>/`. | Periodically clean: `Remove-Item $env:TEMP\cmie_* -Recurse -Force`. |

### 7.7 Recommendations (not yet in code)

These are obvious hardening steps; the current code doesn't implement them but they map
cleanly onto the existing class surface:

1. **Wire a default `TokenBucket`** in `streamlit_import.py` at module import (`rate_per_sec=0.5, burst=3`).
2. **Respect `Retry-After`** on 429 when small (< 30 s) — loop once inside `CmieClient` before raising.
3. **Auto-cleanup** `%TEMP%/cmie_<import_id>/` in a `finally:` block of the pipeline.
4. **Switch `engine='c'`** in `read_tsv` and fall back to `engine='python'` on failure.
5. **Add a `HEAD` / cheap `query.php` health check** before burning a wapicall quota hit.

---

## 8. End-to-end data flow

```
   ┌─ User clicks "Fetch" in sidebar (pages/6_settings.py via streamlit_import.py)
   │
   ▼
CmieClient.download_*()  ──▶  <zip on disk>
   │
   ▼
extract_zip_to_dir()  ──▶  raise_if_error_txt()  ──▶  read_tsv() ── pandas.DataFrame(raw)
   │
   ▼
apply_cmie_column_aliases()     (comp_code → company_code, fy → year, …)
   │
   ▼
normalize_panel_like()
   ├─ coerce numerics (leverage, profitability, tangibility, firm_size, …)
   ├─ log_size = ln(firm_size)
   ├─ enrich_with_classification()  → Dickinson life_stage
   └─ event dummies:  gfc (2008-09), ibc_2016 (≥2016), covid_dummy (2020-21)
   │
   ▼
validate_panel(min_years=3, max_missing_frac=0.35)
   │
   ▼
db.create_version(import_id, …)
db.write_api_financials(version_id, panel)   ──▶  SQLite table api_financials
db.mark_current_api_version(version_id, None) ──▶  whole batch becomes the active CMIE panel
```

### Canonical columns written to `api_financials`

From [`normalize.CANONICAL_COLUMNS`](../cmie/normalize.py#L13-L37):

```
company_code, company_name, nse_symbol, industry_group,
year, life_stage,
leverage, profitability, tangibility, tax, dividend,
firm_size, log_size, tax_shield,
borrowings, total_liabilities, cash_holdings,
ncfo, ncfi, ncff,
gfc, ibc_2016, covid_dummy
```

Any CMIE columns outside this set are dropped at normalization time.

---

## 9. Loading data — step-by-step

### A. One-time setup

1. **Get an API key** from CMIE (Prowess / Economy Outlook subscription).
2. **Enable the CMIE Lab** flag — `db.is_cmie_lab_enabled()` must return `True`
   (toggled on the **Settings** page).
3. **Store the key** in one of:
   - `.streamlit/secrets.toml` → `CMIE_API_KEY = "…"` (local / Streamlit Cloud)
   - Shell env → `export CMIE_API_KEY=…` (CLI / Docker)
4. Ensure `capital_structure.db` exists (shipped with the repo) and run
   `db.ensure_cmie_tables()` once — the Streamlit importer does this automatically.

### B. Interactive (Streamlit sidebar)

`Settings page → CMIE Economy API (Live)` block, produced by
[`render_cmie_sidebar_block()`](../cmie/streamlit_import.py#L28):

1. Pick a transport (**Legacy / Form / Wapicall**).
2. Fill the JSON payload or form fields.
3. **Single**: enter one `company_code`. **Batch**: paste ≤ 10 codes.
4. Click **Fetch** — progress bar shows `% downloaded`, then `normalize → SQLite`.
5. Switch **Data source** in the sidebar from `sqlite` → `cmie` to use the new version across
   all 12 pages.

### C. Command line (preferred when the browser disconnects)

```bash
# Single company — legacy ZIP
python -m cmie download \
  --payload-json '{"scheme":"MITS","freq":"A","company_code":100001}' \
  --out-zip /tmp/cmie_100001.zip
python -m cmie import-zip /tmp/cmie_100001.zip --company-code 100001 --min-years 1

# Batch (≤ 10)
python -m cmie batch-download \
  --codes "100001,100002,100003" \
  --payload-json-file tpl.json \
  --out-dir /tmp/cmie_batch \
  --delay 1.0
python -m cmie merge-zips /tmp/cmie_batch/*.zip --min-years 1

# Import a CSV / tabular JSON dumped from the Form transport
python -m cmie import-table response.json --min-years 1
```

All CLI calls write into the **same** `capital_structure.db` that Streamlit reads.

### D. Programmatic (inside another script)

```python
from cmie.client import CmieClient
from cmie.rate_limit import TokenBucket
from cmie.pipeline import import_from_zip_file

client = CmieClient(
    api_key=os.environ["CMIE_API_KEY"],
    timeout_s=600.0,
    limiter=TokenBucket(rate_per_sec=0.5, burst=3),   # recommended but optional
    max_retries=4,
)
client.download_query_zip(
    {"scheme": "MITS", "freq": "A", "company_code": 100001},
    dest_path="/tmp/cmie.zip",
)
version_id = import_from_zip_file("/tmp/cmie.zip", 100001, min_validation_years=1)
print("active CMIE version:", version_id)
```

---

## 10. Verifying a successful import

```python
import db
with db.connect() as con:
    print(con.execute("SELECT id, created_at, note FROM api_versions "
                      "ORDER BY created_at DESC LIMIT 5").fetchall())
    print(con.execute("SELECT COUNT(*) FROM api_financials "
                      "WHERE version_id = (SELECT current_version_id FROM api_settings)"
                      ).fetchone())
```

You should see a new `api_versions` row and `api_financials` rows tagged with that
`version_id`. The sidebar's **Data source** radio flipping to `cmie` confirms the UI picked
it up.

---

## 11. Troubleshooting cheat-sheet

| Symptom | Likely cause | Fix |
|---------|--------------|-----|
| `AUTH: Unauthorized…` | Wrong / expired `apikey` | Rotate key in `secrets.toml` or env var |
| `CMIE_ERROR: …subscribe…` (in `ERROR.txt`) | Subscription doesn't cover the requested scheme/indicator | Narrow the `indicnum` list or contact CMIE |
| `ZIP_BAD: …not a valid zip…` | CMIE returned an HTML error page with HTTP 200 | Check the 2 KB snippet in `error.detail`; usually bad payload or quota |
| `RATE_LIMIT_REMOTE (HTTP 429)` | Hit CMIE's throttle (3 hits/company/day on wapicall) | Wait `Retry-After` seconds, reduce batch cadence |
| `SCHEMA: missing company_code/year` | CMIE headers differ from aliases | Add a new entry to `cmie/indicator_map.COLUMN_ALIASES` |
| `VALIDATION: Too few years` | Normalized panel < `min_years` | Lower `--min-years` (default 3) or widen `nperiod` |
| Streamlit disconnects mid-download | Browser idle / Cloud Run cold-start | Re-run offline: `python -m cmie import-zip <path>` against the saved ZIP |
| `import_from_raw_dataframe` silently drops columns | Column name outside `CANONICAL_COLUMNS` | Extend `CANONICAL_COLUMNS` in [`normalize.py`](../cmie/normalize.py) and retry |

---

## 12. Tests

Parity / regression tests live in [`tests/`](../tests/):

- `test_cmie_zip_parse.py`       — ZIP extraction + `ERROR.txt` classification
- `test_cmie_normalize.py`       — `normalize_panel_like` invariants
- `test_cmie_indicator_map.py`   — column alias coverage
- `test_cmie_batch_utils.py`     — `parse_company_codes` / payload substitution
- `test_cmie_query_form.py`      — tabular JSON (head/data) parser edge cases
- `test_cmie_feature_gate.py`    — `is_cmie_lab_enabled` behaviour
- `test_bulk_upload_cmie_parse.py` — bulk-upload parity with the CMIE panel shape

Run:

```bash
python -m pytest tests/test_cmie_*.py -v
```

---

## 13. Quick reference — which transport when

| You have… | Use |
|-----------|-----|
| One / few company codes, want full financials | **Legacy ZIP** (transport #1) |
| An indicator scheme query (macro/time series) | **Form tabular JSON** (transport #2) |
| A wapicall-eligible company-level export | **Wapicall** (transport #3) |
| Only a CSV / JSON dump already on disk | `python -m cmie import-table …` |
| A saved ZIP from a previous failed UI run | `python -m cmie import-zip …` |
