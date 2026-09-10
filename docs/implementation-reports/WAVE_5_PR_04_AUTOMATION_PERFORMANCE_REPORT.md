# WAVE 5 PR-04 — Automation and Performance Action-Item Report

**Date:** 2026-09-08
**Branch:** `reconcile/wave5-independent-review-repair-2026-09-08`
**Base commit:** `9ace95e`
**Status:** `READY_FOR_INDEPENDENT_RE_REVIEW`

## Closed Action Items

- Integrated the previously isolated tiktoken import-safety repair.
- Removed eager `llm_adapters` import from `models/__init__.py`.
- Removed import-time SQLite initialization and model-cache directory creation.
- Added static import-side-effect and Stata-contract audits.
- Added fast, targeted, and full test tiers with disposable databases and isolated
  pytest temporary directories.
- Added machine-readable JSON evidence output to `project_ops.py`.
- Added a reusable 9,031-row real-data audit CLI with source/copy hash checks.
- Added generated advanced-capability status documentation from one source catalog.
- Added canonical syntax examples and parser tests generated from documentation.
- Added reusable Playwright Stata helpers and a committed four-journey UI verifier.
- Added explicit GitHub Actions gates for contracts, import safety, generated status,
  automation, and independent-review repair tests.
- Split pure structured-option parsing from semantic validation, reducing
  `stata_validation.py` from 359 to 318 lines and moving 46 lines to
  `stata_syntax.py`.
- Documented the optimized verification and Graphify workflow in the engineering playbook.

## Automation Surfaces

- `scripts/test_fast.ps1`
- `scripts/project_ops.py`
- `scripts/check_import_side_effects.py`
- `scripts/check_stata_contracts.py`
- `scripts/render_capability_status.py`
- `scripts/wave5_realdata_audit.py`
- `scripts/playwright_stata.py`
- `scripts/verify_wave5_ui.py`
- `.github/workflows/deploy.yml`

## Authoritative Status

- Source: `models/capability_status.py`
- Generated document: `docs/CAPABILITY_STATUS.md`
- Verification: `py -3.12 scripts/render_capability_status.py --check`

Registry status, result metadata, and primary UI descriptions consume the same
catalog. No advanced capability is `VALIDATED`.

## Import Safety and Performance

- `import models`: **0.000652 seconds**.
- Explicit `from models import llm_adapters`: **2.410616 seconds**.
- Tiktoken initialization is lazy and falls back with one warning on load or
  encode failure.
- Docker pre-caches `cl100k_base` under `/opt/tiktoken-cache`.
- `import db` performs no SQLite connection or schema write.
- `import models.cache` creates no directory.

## Verification Tiers

Machine-readable evidence is emitted with `--evidence <path>`.

| Tier | Result | Pytest time | Total wrapper time |
|---|---|---:|---:|
| Fast | 242 passed, 1 skipped | 18.28s | 22.032s |
| Targeted | 153 passed | 15.80s | 18.303s |
| Full | 871 passed, 1 skipped | 154.87s | 159.257s |

Additional action-item contract gate: **55 passed in 15.52s**.

Upstream-range pre-push gate: **243 passed, 2 warnings in 22.20s**, followed by
the disposable 9,031-row real-data audit.

## Real-Data Audit

`py -3.12 scripts/wave5_realdata_audit.py`

- Panel rows: 9,031.
- Core commands: 22 success.
- WS1 commands: 4 success.
- Invalid requests: 8 failed closed.
- Covariance cases: 6 success with exact cluster metadata.
- Scenario: 2 partial previews.
- HDFE: partial.
- Source and disposable copy SHA-256:
  `354E9B4E62E54AACC0C4306253E9473EB65A7FC37F8ED9545EFEBABDBC915975`.

## UI Automation

`scripts/verify_wave5_ui.py` uses `scripts/playwright_stata.py` and binds every
assertion to the current terminal command title.

Result: **`WAVE5_UI_PASS journeys=4`**.

## Failure Modes Prevented

- Unrelated local pytest plugins cannot auto-load.
- Pytest lock collisions are isolated by unique `--basetemp` directories.
- Tests do not use the tracked database for write-capable paths.
- Documentation-status drift fails generated-document checks.
- Silent substitution and prohibited GMM claims fail static checks.
- Import-time tiktoken/network, SQLite, and cache-directory side effects fail static
  and subprocess tests.
- Project push automation targets the current branch instead of hardcoded `master`.
- Browser assertions cannot pass from stale or static command text.

## Remaining Constraints

- GMM, IV, HDFE, ML, and scenario methodology classifications remain unchanged
  and non-validated.
- Real-data audit accepts either a partial HDFE result or a typed
  `DEPENDENCY_UNAVAILABLE` result when the optional backend is absent.
- Graphify semantic attribution warnings remain a tooling limitation; generation
  is restricted to bootstrap and final-commit checkpoints.

## Non-Actions

- No PR created.
- No merge into `master`.
- No deployment.
- No Wave 6 work.
- No tracked database mutation.

**Verdict:** `READY_FOR_INDEPENDENT_RE_REVIEW`
