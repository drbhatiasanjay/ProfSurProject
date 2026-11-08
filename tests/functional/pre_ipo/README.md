# Pre-IPO functional acceptance suite

This is a Playwright Test CLI suite against the real Streamlit application. It drives visible forms, navigation and downloads. It is separate from the Python model unit tests. **Prepared for execution after Antigravity finishes; browser acceptance has not been run.**

## Scope and oracles

The suite covers existing-data inspection, all five built-in dossiers, six terminal personas, evidence tabs, original ingestion, retained sources, native page bounds, scans/gaps, review validation, CMIE metadata, missing-data follow-ups, every one of the 22 workbench methods with positive/adverse inputs, decision persistence, evidence handoff, export text parity, withdrawal, deletion, restart, reupload, ownership and stale browser submissions.

Four familiar usernames are recreated as **synthetic test accounts**, with freshly generated credentials and role equivalents. A fifth `e2e_new_researcher` proves that a newly created user can use the same functionality. Identical inputs are compared across users/roles. Roles control permitted writes; personas must not change facts/calculations. A viewer tests viewing and denied writes, rather than being made an administrator to pass tests.

Synthetic PDFs include true image-only, encrypted, corrupt, oversized, zero, negative, mixed-unit, 23-page and inert-markup cases. Expected arithmetic is independently specified in `support/model-vectors.cjs`; models are never called to manufacture their own expected answers. Read-only SQLite corroboration detects surviving rows even after the company profile was deleted.

The source-to-screen contracts use accessible labels and scoped Streamlit test IDs, not pixel coordinates. Streamlit tables are canvas grids; no financial values are inferred from missing DOM cell text. Downloads provide a user-visible machine-readable comparison. Selector drift is a test-maintenance issue, not proof of a financial defect: triage and update a renamed control only after verifying equivalent behaviour.

## Setup once

From the repository root in PowerShell:

```powershell
npm.cmd ci --prefix tests/functional/pre_ipo
node tests/functional/pre_ipo/node_modules/@playwright/test/cli.js install chromium
```

Use Python 3.12 with project development dependencies, plus reportlab and Pillow for synthetic fixtures (already present in the reviewed environment). The npm lockfile pins the installed Playwright version. Browser installation does not start a test.

## Inspect the cases without launching the app/browser

```powershell
node tests/functional/pre_ipo/node_modules/@playwright/test/cli.js test --config tests/functional/pre_ipo/playwright.config.cjs --list
py -3.12 scripts/research/build_pre_ipo_test_catalogue.py
py -3.12 -m pytest tests/functional/test_pre_ipo_harness_safety.py -q --tb=line
```

The generated detailed inventory is `docs/plans/PRE_IPO_FUNCTIONAL_TEST_CATALOGUE_2026-11-08.md`.

## Run after Antigravity's gate finishes

Snapshot the finished implementation, not this older application's branch by accident. Pass its exact checkout:

```powershell
# Smoke first. --headed opens the browser; omit it for headless execution.
py -3.12 scripts/run_pre_ipo_functional.py --app-root C:/Users/hemas/Downloads/ProfSurProject --execute --headed -- --project=drbhatia-dark --grep @smoke

# Full five-account/two-theme matrix; serial to make state/restart effects attributable.
py -3.12 scripts/run_pre_ipo_functional.py --app-root C:/Users/hemas/Downloads/ProfSurProject --execute --headed

# Narrow a repair rerun by user-visible case ID, never by changing expected values.
py -3.12 scripts/run_pre_ipo_functional.py --app-root C:/Users/hemas/Downloads/ProfSurProject --execute -- --project=e2e_new_researcher-dark --grep MOD-005
```

Without `--execute`, the launcher only prepares a snapshot and fixtures; it does not start the app. It always creates a fresh temporary run directory and database, generates test credentials, runs canonical `app.py` on a free loopback port, and terminates only its owned process. It will not target an existing server or arbitrary URL. No original secrets are copied. API keys are removed from the child environment. Cloud OCR consent is never enabled by these tests.

If the global shell needs a populated CMIE panel to navigate, supply `--dataset-db C:/Users/hemas/Downloads/ProfSurProject/capital_structure.db`. It uses a read-only online backup and scrubs private/auth tables **in the copy only**. It never modifies the source DB. An empty DB remains the default so hidden dataset dependencies are visible.

Do not run against Antigravity's active app or reuse its port. Wait for its implementation/testing to finish, then capture the finished source. Keep the snapshot manifest with the result.

## Coca-Cola and other real-issuer documents

`scripts/research/build_pre_ipo_corpus_plan.py` creates DRAFT inventories for Coca-Cola and the five new issuer folders. Drafts have `approved=false`, unknown entity status and empty expected fields deliberately. They are not financial gold data.

Use Antigravity's independently verified document/page comparison to annotate a COPY of each draft. Required document fields: issuer, title, exact path/hash/pages, filing type/version and `entityVerified=true`. Required expected fields:

```json
{
  "attributeId": "canonical metric or supported legacy attribute",
  "reviewId": "history[0].cfo_cr",
  "entity": "exact legal reporting entity",
  "period": "FY24",
  "basis": "CONSOLIDATED",
  "currency": "INR",
  "unit": "crore",
  "value": 0,
  "absoluteTolerance": 0,
  "page": 1,
  "locator": "exact original table/note",
  "quote": "exact source statement including units"
}
```

The zero above illustrates JSON shape, not an issuer value. Enter only independently verified actual values. Non-financial documents need their own typed facts, not invented ratios. `reviewId` is optional per field; at least two supported source-backed fields are required in the integrated issuer journey. Use compatible reporting perimeters and do not silently choose conflicting sources by document order.

Set plan `approved=true`, `reviewedBy` and `reviewedAt` only after review. Keep IPO-time and post-listing information distinguishable; legal document existence does not prove governance effectiveness.

```powershell
py -3.12 scripts/run_pre_ipo_functional.py --app-root C:/Users/hemas/Downloads/ProfSurProject --execute --corpus --gold-plan C:/path/to/reviewed-HndstnCocacola.json -- --project=drbhatia-dark --grep @corpus
```

This registers separate per-document tests plus an integrated shared-issuer journey: retain/process all documents, compare candidates to gold, review selected facts, inspect analysis/export, delete, restart and reupload. Full page ranges are processed through the UI. Missing structured extraction may therefore produce legitimate failures; do not bypass the UI by inserting facts into SQLite. An unreviewed/missing gold plan is **BLOCKED**, not passed or silently skipped.

## Evidence and interpretation

Every executed run prints a temporary `session.json` path. Its sibling directory contains source hashes, server logs, `functional-results.json`, HTML report, screenshots, downloads and failure traces. Authentication precedes tracing. Do not publish private account/control files, original documents or complete run directories.

`PASS` means the particular assertion passed, not that the company is investable. `FAIL` is a failed product/contract assertion to triage. `BLOCKED` requires missing prerequisites such as independently labelled corpus data. `NOT_EXECUTED` never counts as a pass. Retries are off so the first failure remains visible.

Automated PPTX checks cover text and basic shape bounds. Human rendered-slide review is still mandatory for clipping/readability. Automated checks cannot establish that a paper citation supports an economic claim, that an econometric identification strategy is defensible, or that a recommendation is suitable. Use the critical-review checklist in the companion functional test plan. Do not label those checks verified from heading presence or text length.
