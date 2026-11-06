# Company Financing workspace

Local implementation on `codex/company-financing`, based on the approved board-deck commit `ff7db3b3`. This branch is isolated from Antigravity's master integration. Merge, push and deployment have not been performed.

## Delivered workflow

The new Company Financing sidebar page is registered once in `app.py` and reached through the canonical root app. The route is `/company_financing`.

1. Select one actual financial dataset version and a company by stable code. The page automatically loads the latest source observation and displays reporting year, debt, reported cash, PBIT, interest, operating cash flow, leverage and derived coverage. Monetary units remain unconfirmed until management supplies evidence.
2. Create or select a private financing case. Add only missing treasury details. A bordered native form explains each step and what saving will do. Unknown cash and other values remain blank, not zero.
3. Enter reporting currency, scale, statement basis, balance date, source evidence and unrestricted cash. Add facility rows and future principal repayment rows linked by facility ID. Missing evidence may be saved as an incomplete draft; structurally invalid entries cannot be saved.
4. Alternatively download the Excel template, complete its Context, Facilities and Repayments sheets, preview the import, then explicitly select Use imported draft. Import does not automatically save, overwrite source facts, or apply deck scenarios.
5. Validate and save. Each save appends a revision, preserving a snapshot of observed facts separately from management inputs. Repeat saves use the same case ID. Another user's cases cannot be listed or loaded. A stale browser session cannot overwrite a newer revision.
6. Inspect missing evidence and principal coverage. A drawn-debt reconciliation is calculated only after the user explicitly confirms a matching currency, scale, statement basis and reporting date. Mixed currencies are never added together. Differences remain visible.
7. Reload a saved case, inspect/download an earlier revision as JSON, or export the working register as Excel. A changed source observation is flagged rather than silently substituted into an old snapshot.

Existing historical deck generation remains available without completing this workspace. The new register does not silently populate or change a deck's assumptions.

## Validation and persistence

- Facility IDs are unique; repayments must reference existing IDs.
- Numeric amounts are finite and nonnegative; principal repayments are positive.
- Zero and missing values remain distinct.
- Dates must be valid ISO dates. Future principal falls after the register balance date and no later than maturity.
- Duplicate facility/payment dates are rejected; schedule principal cannot exceed drawn balance. An incomplete principal schedule is a visible evidence gap.
- Fixed and floating rate types are explicit. Floating benchmark, spread and reset evidence are requested when missing. No rate exposure is inferred.
- Workbook size, expanded ZIP size, sheets, columns and row counts are checked. Management text is exported as literal text rather than executable Excel formulas.
- `financing_case_versions` is added lazily to the configured SQLite database. Existing financial tables are not changed. Versions are append-only, ownership scoped, with optimistic concurrency under `BEGIN IMMEDIATE`.
- The page retains the existing admin/researcher access boundary; viewers are denied. Sharing, approval workflows and cross-user editing are not introduced.
- All new light/dark CSS is scoped beneath `company_financing_page` and `company_financing_form`; global theme files are unchanged.

## Correctness fixes delivered with this workspace

- `models/debt_metrics.py` supplies shared PBIT/interest stress arithmetic to the Debt Strategy deck and AI stress tool. Identical company data and explicit assumptions produce identical metrics.
- AI stress uses measured company PBIT and interest instead of a fixed 3.55x baseline. A nonzero rate shock without a confirmed floating share withholds stressed coverage. A coverage floor is an optional analytical assumption, not a contractual covenant.
- Removed fabricated monetary headroom, implied credit ratings, generic covenant floors, leverage-target shifts and cash-release amounts from the AI stress result. Legacy response keys remain available with unavailable values where appropriate. The prompt and tool schema describe these boundaries.
- Corrected AI ROA/tangibility display from source fractions to percentages and resolves names only within the active panel; ambiguous names require a code.
- Recursive forecasting updates leverage by feature name, preserves other predictors under an explicit constant-predictor assumption, and rejects sequences with year gaps.
- Forecast results are bound to the training data, active panel, filters, model and sequence length. Firm histories come from the same filtered training dataset. PyTorch availability reflects the actual backend.
- Regression Scenarios withholds predictions when no fitted sample is available, uses actual fitted-sample mean, removes an arbitrary colour threshold, and converts ROA/tangibility fractions to percentage-valued slider inputs. Cache wrapper source changed to invalidate prior unit contracts.
- Empty serialized event filters now deserialize as dictionaries rather than an unusable tuple.
- Generic upload no longer silently maps debt/equity to debt/assets leverage. The upload screen accurately describes its session-scoped Workbench integration.

## Source-to-screen mapping

| Visible function | Source |
| --- | --- |
| Navigation registration | `app.py` |
| Company/dataset selectors, facts, form, import preview, results and scoped styling | `pages/26_company_financing.py` |
| Register validation, reconciliation, Excel roundtrip, snapshots | `models/financing.py` |
| Owner-scoped case listing, revision loading, append-only saves | `models/financing_store.py` |
| Shared coverage calculations | `models/debt_metrics.py` |
| AI/deck integration | `models/agent_tools.py`, `models/llm_adapters.py`, `models/debt_board.py` |
| Forecast corrections | `models/timeseries.py`, `pages/10_forecasting.py` |
| Regression/input corrections | `models/scenario_regression.py`, `pages/3_scenarios.py`, `db.py`, `models/data_ingest.py` |

## Scope boundary

This release prepares verified financing evidence. A monthly forward cash-flow engine, debt-capacity solver, contractual covenant engine, lender pricing comparison, shared reviewer approval and automatic register-to-deck integration are future work. No DSCR, cash runway or approved borrowing limit is presented without those inputs and calculations.

## Verification and merge handoff

Final release checks on 6 November 2026: **172 focused tests passed**, two upstream deprecation warnings; **6 project fast checks passed**; whitespace validation passed. The focused set includes the new register/store/native UI tests, forecast-context and recursion tests, regression Scenarios tests, existing board/PPTX tests, P0 remediation and AI accuracy benchmarks. Google tool-schema conversion for the added optional assumptions also succeeded offline without making a model request.

Focused tests exercise the actual Tata Motors source baseline, AI/deck parity, missing exposures, recursive feature ordering, year gaps, malformed schedules, missing versus zero amounts, mixed currencies, workbook roundtrip, formula-like text, owner isolation, optimistic locking and native Streamlit reruns/profile boundaries. Browser evidence is recorded separately under ignored `scratch/financing_evidence/`.

Local preview: `http://127.0.0.1:8504/`, root `app.py`, separate ignored validation database. Existing ports 8501-8503 were not stopped. Existing approved credentials were validated without printing them. No external model requests are required for verification.

After Antigravity finishes the prior deck integration, integrate only this branch's commits after `ff7db3b3`. Preserve its newer theme changes. Expected shared files include `app.py`, `db.py`, `models/debt_board.py` and `SESSION_LOG.md`; resolve additions rather than accepting a whole side. Do not copy databases, secrets, scratch scripts, screenshots or generated graph artifacts into master.

Review the precise integration range with `git log --reverse --oneline ff7db3b3..codex/company-financing`. This range contains the financial correctness commit first and the financing workspace commit second. Apply both after preserving any ongoing work and confirming that master already contains the approved prior deck. This document is a handoff; it does not authorize a push or deployment.

Run the focused financial/UI tests and project fast checks on the integrated branch, then confirm both themes and all four configured profiles through the root application. A health response is not browser acceptance.

Authenticated browser acceptance completed on 6 November 2026 using the canonical root app on 8504: profsurkumar and skumar (Researcher), drbhatia (Admin), and sbhatia (Viewer), both themes. Allowed profiles created revisions; viewer was denied with readable warnings and no case controls. The browser verified owner isolation, save/reload/reauth restoration, actual Excel download and import, explicit import application, revision 3 restoration, invalid currency/date rejection, and post-save selection/Create-new behaviour. Unconfirmed basis correctly withheld reconciliation.

The prior Board Deck funding-to-stress assertion was checked in the actual browser after its rerun settled: four numeric fields, no funding purpose, two rendered coverage bars. It was a test-timing issue; no board-form source modification was needed.

Final light/dark screenshots and `browser_acceptance.json` exist under ignored `scratch/financing_evidence/`; the final light screenshot was also visually inspected by the parent agent. No fresh browser PowerPoint download or manual canvas negative-principal edit was performed in this acceptance run. Actual PPTX integrity and invalid schedules are covered by the focused automated tests; do not substitute that for a claim of fresh browser download evidence.
