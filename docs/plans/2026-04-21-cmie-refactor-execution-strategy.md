# CMIE Refactor — Execution Strategy

> Carried over from a prior Claude session that got stuck before it could act on the analysis.
> This is the **meta-plan** (how to execute) that complements the per-file plan in
> [`2026-04-21-cmie-panel-scenarios-bulk-e2e.md`](2026-04-21-cmie-panel-scenarios-bulk-e2e.md).
>
> **Scope flag.** Parts of this strategy reference artifacts that do **not** yet exist in
> `master` — `pages/15_data_load.py`, `cmie/batch_pipeline.py`, `data_loads` table,
> `v_all_financials` view, and a `db.get_panel_data(ft, version_id)` signature. Treat this
> document as the strategy for a **larger versioned-loads refactor** that wraps around the
> per-file plan above; it is not a drop-in guide for today's repo.

---

## A) Parallel sub-agent strategy for this refactor

The plan has a natural **serial-then-fan-out** shape. Don't parallelize early — `db.py` +
`helpers.py` + `batch_pipeline.py` must land and stabilize before page edits, or fan-out agents
will write against a shifting API.

| Wave | Mode | Tracks |
|------|------|--------|
| 1 | Serial, main thread | Data model in `db.py` + `tests/test_data_loads.py`. Everything else blocks on this API. |
| 2 | 2 agents in parallel | **B:** `cmie/batch_pipeline.py` + tests. **C:** `helpers.render_active_load_banner` + sidebar selector in `app.py`. |
| 3 | 3–4 agents in parallel (page groups) | **G1:** pages 1, 2, 5. **G2:** 3, 8. **G3:** 9, 10, 11. **G4:** 7, 12, 13, 14. Each agent gets: the new `db.get_panel_data(ft, version_id)` signature, the banner import, and a grep-delete list for `data_source_mode` / `get_active_*`. |
| 4 | Serial, main thread | `pages/15_data_load.py` (wires B + C + upload helpers). Final sweep + full test run. |

**Rules for fan-out:**
1. Each agent owns **only** its listed files.
2. The `db.py` / `helpers.py` API is **frozen** at the start of its wave.
3. Return a terse *"changes made + any surprises"* report.
4. Never let parallel agents touch shared files.

---

## B) Skills / Hooks / CLI / MCP worth using now

### Skills (invoke as the refactor unfolds)

- **`using-git-worktrees`** — run the whole refactor in `../ProfSurProject-versioned-loads`.
  Master stays clickable if we need to ship a hotfix.
- **`systematic-debugging`** — when CMIE single-company fetch is retried live, the actual
  root cause (likely `VALIDATION` with `min_years=3`, possibly `ZIP_BAD` if response is HTML)
  must be confirmed rather than assumed.
- **`verification-before-completion`** — mandatory gate before claiming any wave done.
  Ties directly to past mistake #4.
- **`webapp-testing` (Playwright)** — between waves 3 and 4, smoke-test all 14 pages with a
  script rather than clicking. Addresses mistake #4 at scale.
- **`simplify`** — one pass after wave 4 to look for dead code from the old `data_source_mode`
  world.
- **`requesting-code-review`** — between wave 3 and wave 4.

### Hooks

**Do NOT add mid-refactor.** They change the blast radius of every edit. Defer to a separate
PR (already flagged earlier).

### CLI

`py -3.12 -m pytest` and `streamlit run app.py` cover it. Add `ruff` *after* the refactor lands
(running it now floods output). `gh` for PR.

### MCP

- **`mcp__sequential-thinking__sequentialthinking`** — useful for reasoning through the
  `v_all_financials` column UNION once I read the actual `financials` schema (column sets may
  not align cleanly).
- **`mcp__context7__*`** — Streamlit `st.column_config`, `st.page_link`,
  `st.selectbox(format_func=…)` API signatures have moved in recent versions; worth confirming
  against the pinned Streamlit version.
- Everything else from the deferred list: **skip**.

---

## C) Reusable patterns to adopt (not reinvent)

Cited from the explore pass:

| What | Where | How to reuse |
|---|---|---|
| `CREATE-IF-NOT-EXISTS` + `INDEX` + commit-in-`finally` | `ensure_cmie_tables()` at `db.py:75-153` | Copy shape for `ensure_data_loads_table()` |
| `filters_to_tuple` / `_build_where` | `db.py:441-476` + `db.py:714-720` | Extend to accept `version_id`; don't rewrite |
| Upload validation pipeline (returns `valid/errors/warnings/detected_columns/n_rows/n_firms/year_range`) | `validate_upload` / `standardize_columns` at `models/data_ingest.py:43-205` | Plug straight into the Manual Upload tab |
| `st.status` + `st.progress` + nested `set_step(pct, label)` | `cmie/streamlit_import.py:166-172` | Lift into `pages/15_data_load.py` |
| Company roster (1-hr cache already set) | `get_companies()` at `db.py:416-418` | Use as-is |
| Cache-buster for `list_loads()` | `db_cache_revision()` at `db.py:46-51` | Use when `data_loads` row count changes |
| Version ID pattern `uuid.uuid4().hex[:12]` → `f"v_{import_id}"` (used 5× already) | — | **Add one helper** `db.new_version_id(prefix)` instead of copying the pattern a 6th time |

### What does NOT exist and must be built from scratch

- **Per-row red/green status table** — no helper anywhere; build on `st.column_config` + custom
  emoji prefix.
- **Exception-to-UI helper** — currently every caller does `st.error(str(e))` by hand. Add
  `helpers.format_cmie_error(e) -> (code, message, detail)` once and reuse.
- **Page banner** — no shared title pattern today; this refactor creates the first one.

---

## D) Past mistakes — concrete guards for this refactor

From memory file + git log + earlier code review:

| # | Mistake class | How it bites this refactor | Guard |
|---|---|---|---|
| 1 | Gitignored source code (the `models/` incident) | None of the new files — `pages/15_data_load.py`, `cmie/batch_pipeline.py`, `helpers.py` edits — can land under a gitignored path | Read `.gitignore` before first commit; `git check-ignore` each new file |
| 2 | Python version pinning drift (3.14 vs 3.11) | Prod is 3.11 (`.python-version`), dev is 3.12 (`py -3.12` in permissions). CI (239b875) runs tests only; Streamlit Cloud rebuilds on push | Run tests with both `py -3.11` and `py -3.12` before push |
| 3 | Heavy deps (torch ~2 GB) | Adding `requests` / `pandas` extras would not hit this, but don't bring in a new dep for convenience | No new lines in `requirements.txt` this PR |
| 4 | Pushed without testing (repeated 3×) | Most likely failure class for a 14-page refactor | After each wave: `streamlit run app.py`, click every page; run full pytest |
| 5 | `.streamlit/secrets.toml` not gitignored (flagged earlier) | API key is already in it. A single `git add .` leaks the key to a public repo | Add `.streamlit/secrets.toml` + `*.stackdump` + `capital_structure.db` to `.gitignore` before any commit |
| 6 | `_filters_tuple` leading-underscore cache bug (flagged earlier) | This plan rewrites exactly those functions. Easy to carry the bug forward | Every new `@st.cache_data` fn: args are `filters_tuple`, `version_id` — **no underscores**. Already noted in the plan |
| 7 | Scope creep (workbench / `data_ingest` landed unplanned last time) | Temptation to fix comparison, retry button, parallel fetches | User deferred all three explicitly. Keep out |
| 8 | `np.asarray(x).flatten()` for model outputs | Not relevant unless I touch charts — I shouldn't | N/A |
| 9 | Uncommitted `capital_structure.db` drift | This refactor creates `data_loads` table + view, so the local DB **will** drift | Decide upfront: either (a) gitignore the DB and ship a rebuild script, or (b) explicitly commit the migrated DB with a clean rebuild note. **Don't let it drift accidentally** |
| 10 | 3× "Fix Streamlit Cloud deployment" commits in git log | Deployment is the fragile surface | Don't touch `.python-version`, `requirements.txt`, `packages.txt`, file tree layout unless necessary |

---

## E) API contract — deltas verified against code + public docs

> Cross-checked against [`docs/cmie_api_reference.md`](../cmie_api_reference.md) — only items
> *not* already captured there are included below. The items here are refactor-critical
> (they change page behaviour, retry policy, and parser choice).

### E.1 Input contract — fields NOT sent (wapicall)

The wire payload is exactly `{apikey, company_code}`. Four field categories that look like
they should be inputs but **are not**:

| Field | Reality | Consequence for the page |
|---|---|---|
| `company_name` | **Not sent.** CMIE *returns* it embedded in the `.txt` filename. | UI input labelled `"Display name (not sent to CMIE)"`; used only in the result table. |
| `year` / `from_date` / `to_date` | **Not parameters on wapicall.** CMIE returns its default windows (`latest`, `last5yr`). | Remove any year-range control from the CMIE tab. Year filtering = post-download only. |
| `scheme` / `indicnum` / `freq` / `nperiod` | Belong to `query.php`, not wapicall. | Don't surface on this page. |
| (diagnostic uncertainty) Body encoding | Code sends `application/json`; public docs don't explicitly confirm. Works empirically. | If diagnostic run returns `ZIP_BAD` under otherwise-valid conditions, try form-encoded wapicall as a fallback. |

### E.2 Output contract — ZIP structure discovered

Empirically (not in public docs):

- **ZIP filename:** `Economyapi_yyyymmdd_hhmmss.zip`
- **Contents:** 1…N `.txt` files + optional `ERROR.txt`
- **`.txt` filename pattern:** `{company_code}_{COMPANY_NAME}_{latest|last5yr}_{username}.txt`
- **A single-company response contains multiple `.txt` files** — typically one for
  `latest` and one for `last5yr`. Multi-company batches produce one `.txt` per company per
  variant.

### E.3 Behavioural deltas that change the plan

1. **Billing is per-company, not per-call.** Public docs: *"3 hits shall be deducted per
   company."* Splitting a 10-company request into 10 one-company calls costs the same as a
   single batched call. The per-company loop in the plan is **not** wasteful.
2. **Retries consume quota.** `max_retries=4` ([`cmie/client.py:111`](../../cmie/client.py#L111))
   → up to 5 POSTs per company. If CMIE counts connection attempts against the 3-hit budget,
   one company can exhaust its daily quota in one failed call. **For wapicall on this page,
   override to `max_retries=1`** (max 2 hits — safely under budget).
3. **Bug: `parse_cmie_company_download_zip` reads only the first `.txt`.**
   [`cmie/wapicall_table.py:28`](../../cmie/wapicall_table.py#L28) does `read_tsv(txts[0])`
   and ignores the rest. For a `latest` + `last5yr` response this **drops half the data**.
   Use `merge_zip_paths_to_version` instead — it iterates every `.txt`
   ([`cmie/pipeline.py:130-140`](../../cmie/pipeline.py#L130-L140)) and dedups on
   `(company_code, year)` ([`cmie/pipeline.py:54`](../../cmie/pipeline.py#L54)).
4. **ERROR.txt heuristics are fragile.** `raise_if_error_txt`
   ([`cmie/zip_parse.py:52-63`](../../cmie/zip_parse.py#L52-L63)) matches on
   `apikey / unauthor / subscribe / entitle / not allowed / login / permission`. Any wording
   drift (e.g. `"invalid company code"`) falls through to a generic `CmieParseError`.
   **Surface the full ERROR.txt text in the result table**, not just the classified code.
5. **Year range is CMIE's choice.** If user asks for "just 2020–2024", they still get the
   full series and we filter on read. `validate_panel(min_years=1)` is almost always
   satisfiable unless CMIE literally returns one year.
6. **Response columns are empirically discovered on first real fetch.** First run will likely
   expose column-name mismatches → `CmieSchemaError`. The result table **must show `detail`
   in full** — it contains the actual returned columns, so we can extend `COLUMN_ALIASES`
   without a second fetch.

### E.4 Concrete changes to the approved plan

| # | Change | Where |
|---|---|---|
| 1 | Input form = `(company_code, company_name)` with name labelled display-only | `pages/15_data_load.py` CMIE tab |
| 2 | Remove any year-range input from the CMIE tab; keep `min_years` as a post-download filter and clarify in tooltip | same |
| 3 | Use `merge_zip_paths_to_version` (not `parse_cmie_company_download_zip`) in `cmie/batch_pipeline.py::run_per_company_batch` step 3 | `cmie/batch_pipeline.py` |
| 4 | Instantiate `CmieClient(api_key, max_retries=1)` for wapicall on this page — stay inside the 3-hit budget | same |

### E.5 First-run diagnostic (BEFORE Wave 1 coding)

Fetch one known-good company — **Reliance = `196667`** — through the existing sidebar flow
with `max_retries=0`, and log:

- HTTP status
- Response headers (especially `Content-Type`)
- ZIP contents listing
- First 3 lines of the first `.txt` file (reveals actual column headers)

That disambiguates the earlier test failure — it's one of:

- **`ZIP_BAD`** → HTML body returned (likely auth / wrong body encoding — see E.1).
- **`CmieValidationError`** → `min_years=3` default too strict; lower to 1 for smoke tests.
- **`CmieSchemaError`** → CMIE columns don't match `COLUMN_ALIASES`; extend the map.

Until this diagnostic is run, the schema assumptions in `normalize.py` and `indicator_map.py`
are **unverified** against real CMIE output for any company this subscription covers.

#### E.5.1 First-run outcome — 2026-04-22 00:05 UTC (commit 8e138a9)

Script: [`scripts/cmie_stage1_reliance_diagnostic.py`](../../scripts/cmie_stage1_reliance_diagnostic.py).

| Check | Result |
|---|---|
| URL + method + body encoding | ✅ Match CMIE's own `?section=example_php` verbatim (both JSON and form-encoded are documented as valid — our code sends JSON) |
| §E.2 filename pattern prediction | ✅ Confirmed verbatim by CMIE docs: `196667_RELIANCE_INDUSTRIES_LTD__latest_username.txt` |
| F.3.2 hotfix classification | ✅ `non_zip_body` raised and short-circuited in 0.6 s (without the fix, 4 retries × ~19 s backoff would have run) |
| Wapicall response for Reliance | ❌ HTTP 200, `Content-Type: text/html`, 8,440 bytes — CMIE's landing page (not a ZIP and not an `ERROR.txt`) |
| `/kommon/bin/sr.php?kall=wdiagnosis` GET | Returns *"User status: User not logged in."* — confirms session/key not associated |
| API Passkey present in `.streamlit/secrets.toml` | ✅ 19 chars, loaded correctly |

**Root cause:** API Passkey is invalid / expired / for-wrong-account. CMIE silently returns its
landing page rather than a 401 or an `ERROR.txt` ZIP — which is why our existing
`raise_if_error_txt` heuristics don't catch this class of failure either.

**Unblock step:** rotate the Passkey at `register.cmie.com → API Passkey → Generate New API Passkey`;
copy once (not shown again); update `.streamlit/secrets.toml`; re-run the diagnostic.

**Refactor implications (new, beyond §E.4):**

1. **`raise_if_error_txt` only catches ERROR.txt content** — but CMIE's "invalid-passkey" failure
   mode returns a normal HTML landing page with no ERROR.txt anywhere. Current code relies on
   `_zip_sanity_check` → `CmieZipError("ZIP_BAD")` to catch this, which F.3.2 now routes to a
   fail-fast path. Good, but the user-facing message says *"response was not a valid zip"* —
   misleading for a Passkey issue. **Add a lightweight HTML sniff** in `_zip_sanity_check` that
   recognises CMIE's prelogin markers (`prelogin.js`, `prelogin.css`, `loginform`) and raises a
   `CmieAuthError("AUTH_PRELOGIN")` instead, with a message pointing at `register.cmie.com`.
2. **Add a cheap pre-flight call** to `/wdiagnosis` (GET, no hits consumed, returns HTML) that
   can confirm network reachability *without* burning 3 hits on a dead Passkey. Useful as the
   first thing a batch pipeline does before fanning out.
3. **§F.1 row 5 updated:** quota-exhausted response shape is unconfirmed, but **"Passkey-invalid
   response shape"** is now confirmed — it's an HTML landing page, not a 401 and not an ERROR.txt.

---

## F) Rate limits, retries, circuit breakers — implementation deltas

> These deltas extend §E with **concrete code patterns** for the new
> `cmie/batch_pipeline.py` and for small fixes in `cmie/client.py` + `cmie/errors.py`.
> Baseline context (TokenBucket exists but dead, `max_retries=4`, backoff formula,
> `Retry-After` not honored) is already in
> [`docs/cmie_api_reference.md` §7](../cmie_api_reference.md). This section contains only
> items **not** already documented there.

### F.1 Published vs undocumented — defensive-design audit

| Item | Published by CMIE? | Notes |
|---|---|---|
| Hit cost | **Yes** — "3 hits shall be deducted per company" (applies for `latest`-only and 5-year history) | [economyapi.cmie.com/?section=general](https://economyapi.cmie.com/?section=general) |
| Per-minute / per-day cap | **No** | Must design for unknown caps |
| Concurrent-request policy | **No** | Must assume N = 1 until proven otherwise |
| Hit-counting granularity (per-request vs per-company vs per-variant) | **Ambiguous** | Drives retry-budget choice — see F.3.1 |
| Quota-exhausted response shape | **No** — likely `ERROR.txt` in the zip, but unconfirmed | Surface full ERROR.txt in results table |

The five undocumented items are **unknowns that could bite in production**. Treat them as
defensive-design requirements, not assumptions.

### F.2 Verified code issues not yet captured anywhere

1. **`ZIP_BAD` is silently retried 4×.** `_zip_sanity_check` raises `CmieZipError`
   ([`client.py:88`](../../cmie/client.py#L88)), which is **not** in the
   `(CmieAuthError, CmieRateLimitError)` no-retry tuple at
   [`client.py:198`](../../cmie/client.py#L198) /
   [`client.py:261`](../../cmie/client.py#L261) /
   [`client.py:348`](../../cmie/client.py#L348). It falls through to the catch-all
   `except Exception` and is retried 4×. A wrong API key returning an HTML login page costs
   **5 POSTs × ~19 s backoff ≈ 15+ minutes wasted** on a 50-company batch before the user
   sees the error. **This affects current users today**, not just the refactor.
2. **`TokenBucket` is dead code.** Defined at
   [`rate_limit.py:7-39`](../../cmie/rate_limit.py#L7), always `limiter=None` at
   [`streamlit_import.py:179, 232, 285, 335`](../../cmie/streamlit_import.py#L179). The
   branch at [`client.py:133-139`](../../cmie/client.py#L133) never fires. Three unmitigated
   risks:
   - (a) Undocumented per-minute caps on CMIE side → surprise 429s.
   - (b) User double-clicking **Run import** → two concurrent batches, one key.
   - (c) Multi-user Streamlit Cloud → two sessions sharing one key → quota collision.
3. **`Retry-After` is string-discarded.** On 429 we format the header into
   `CmieRateLimitError.detail` as prose then raise. Callers can't programmatically honour
   the wait — CMIE tells us exactly when to come back and we throw that away.
4. **No per-batch abort on auth failure.** If company #1 raises `CmieAuthError`, the loop
   continues to companies #2…N, each burning hits for the same misconfiguration.
5. **No circuit breaker on 5xx.** Five consecutive `SERVER` errors (CMIE outage) still try
   the remaining companies — good hits after bad.

### F.3 Concrete implementation deltas

#### F.3.1 Client construction (`cmie/batch_pipeline.py`)

```python
limiter = TokenBucket(rate_per_sec=2.0, burst=3)   # shared across the batch
client  = CmieClient(
    api_key,
    limiter=limiter,
    max_retries=1,        # ≤2 HTTP per company — inside the 3-hit budget
    timeout_s=120.0,
)
```

Rationale: `max_retries=1` keeps worst-case hit burn under the 3-hit/company ceiling
**even under the worst interpretation of "CMIE counts every HTTP attempt"** (F.1 row 4).
`rate_per_sec=2.0, burst=3` smooths double-click / multi-user bursts without meaningfully
slowing the happy path.

#### F.3.2 Stop retrying `ZIP_BAD` — one-line fix, ship as standalone hotfix

Add `CmieZipError` to the three no-retry tuples at
[`client.py:198, 261, 348`](../../cmie/client.py#L198):

```python
except (CmieAuthError, CmieRateLimitError, CmieZipError) as e:
    raise e
```

HTML-at-200 is almost always auth / endpoint misconfiguration — retrying wastes hits and UI
time. **This fix is independent of the refactor** and should ship as its own small PR so
current users stop paying the 15-minute misconfig tax.

#### F.3.3 Abort-on-auth across the batch

```python
except CmieAuthError as e:
    _record_failed_result(code, name, e)
    for rem_code, rem_name in companies[i+1:]:
        results.append(CompanyResult(
            company_code=rem_code, company_name=rem_name,
            status="skipped", error_code="ABORTED_AUTH",
            error_message="Batch aborted after authentication failure.",
        ))
    break
```

#### F.3.4 Respect `Retry-After` on 429 (pause between companies — don't retry the current one)

```python
except CmieRateLimitError as e:
    _record_failed_result(code, name, e)                 # this company already burned its hits
    wait_s = e.retry_after_s or 60.0                     # typed attribute — see F.3.6
    on_progress(i, N, f"CMIE rate-limited, pausing {wait_s:.0f}s")
    time.sleep(min(wait_s, 300.0))                       # cap at 5 min — don't hang UI
    continue
```

#### F.3.5 Circuit breaker on consecutive 5xx

Track the last 5 outcomes; if all are `CmieNetworkError(code="SERVER")`, skip every
remaining company with `status="skipped", error_code="CIRCUIT_OPEN"`. A CMIE outage
should not burn good hits on companies 6…50.

#### F.3.6 Expose `retry_after_s` on `CmieRateLimitError` (prereq for F.3.4)

Today F.3.4 would have to regex-parse `e.detail`. Cleaner: parse in the client, attach as a
typed attribute:

```python
# cmie/errors.py
class CmieRateLimitError(CmieError):
    retry_after_s: float | None = None
```

Client populates it from the `Retry-After` header at the 429 branches.

### F.4 UI affordances for `pages/15_data_load.py`

- **Advanced controls expander** (collapsed by default — 95 % of users never touch): exposes
  `max_retries` and the token-bucket params. A power user can bump `max_retries` to 2 for a
  one-off high-priority single-company diagnostic run.
- **"Total hits estimated" KPI**: `sum(r.http_calls for r in results) * 3`, with footnote
  *"3 hits / company per CMIE docs × HTTP requests — not billing-accurate (granularity
  undocumented, F.1 row 4) but makes cost visible."*

### F.5 Performance expectations

With `max_retries=1`, `rate_per_sec=2.0`, `inter_call_delay_s=0.5`:

| Batch size | Happy-path wall time | Hit cost (3/company) | Worst case (all flaky, 1 retry each) |
|---|---|---|---|
| 1  | 2–10 s   | 3   | 6 hits + ~2 s retry sleep |
| 10 | 25–105 s | 30  | 60 hits + ~20 s retry sleeps |
| 50 | 2–9 min  | 150 | 300 hits + ~100 s retry sleeps |

Dominant cost is network RTT to `economyapi.cmie.com` + zip size. CPU (parse + normalize)
is ≈ 100 ms per small company — negligible.

### F.6 Summary — files changed by §F

| File | Change |
|---|---|
| `cmie/client.py` | Add `CmieZipError` to no-retry tuples (3 sites, F.3.2); parse `Retry-After` → populate `CmieRateLimitError.retry_after_s` at 429 branches (F.3.6) |
| `cmie/errors.py` | Add `retry_after_s: float \| None = None` to `CmieRateLimitError` (F.3.6) |
| `cmie/batch_pipeline.py` *(new)* | `max_retries=1`, shared `TokenBucket`, abort-on-auth, respect `Retry-After`, 5-consecutive-5xx circuit breaker |
| `pages/15_data_load.py` *(new)* | Advanced-controls expander; "Total hits estimated" KPI |

---

## Recommendation — concrete next action

Before typing the first line of code:

1. **Worktree the refactor** via `using-git-worktrees` skill →
   `../ProfSurProject-versioned-loads`.
2. **Run the existing 70 tests** in that worktree to confirm a green baseline. If any fail
   *before* we touch code, **fix-first**.
3. **Patch `.gitignore`** to cover `.streamlit/secrets.toml`, `*.stackdump`,
   `bash.exe.stackdump`, `capital_structure.db` — single housekeeping commit before the
   refactor starts.
4. **Inspect the `financials` schema** (`sqlite3 capital_structure.db ".schema financials"`)
   so the `v_all_financials` UNION column list is real, not guessed.
5. **Run the §E.5 first-run diagnostic** against Reliance (`196667`) with
   `max_retries=0`. Record HTTP status, `Content-Type`, ZIP listing, and first 3 lines of the
   first `.txt`. This is the only way to validate the schema assumptions in `normalize.py` +
   `indicator_map.py` before they're baked into a 14-page refactor.

Then **Wave 1: data model + tests**.
