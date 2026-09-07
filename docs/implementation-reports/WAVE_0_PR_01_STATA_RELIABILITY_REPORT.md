# Wave 0 / PR-1 — Stata Studio Immediate Reliability

**Status:** `READY_FOR_REVIEW`  
**Implementation checkpoint:** `7c6de12`  
**Scope:** ProfSurProject Stata Studio reliability remediation

## Scope completed

- Added the optional `python-docx` dependency and fail-safe Word export behavior.
- Added canonical `companycode`/`companyid`/`company_id` resolution to `company_code`.
- Implemented session-scoped `PanelContext` through `xtset`, including panel dimensions,
  balance, time range, observation count, and duplicate entity-time validation (`r(451)`).
- Implemented `lgraph <y-vars> <time-var>, wide` through the existing aggregation and
  Plotly infrastructure.
- Added structured unsupported-command/error responses and user-facing administrator guidance.
- Added regression tests for compatibility behavior and recorded UI evidence.

## Changed files

- `models/stata_engine.py`
- `pages/23_stata_studio.py`
- `requirements.txt`
- `tests/test_stata_compatibility.py`
- `SESSION_LOG.md`

## Acceptance commands

```stata
xtset companycode year
lgraph leverage prof year, wide
```

Both commands were exercised against the active panel dataset and rendered usable output.

## Verification evidence

- `tests/test_stata_compatibility.py`: 9/9 passed (recorded session evidence).
- `tests/test_chart_switcher_and_literature.py`: 6/6 passed (recorded session evidence).
- Combined focused compatibility/UI run: 15/15 passed.
- Exhaustive local/GCP audit: 109/109 checkpoints passed across page, interaction,
  Stata math, AI prompt, multi-user/theme, and performance phases.
- Browser and screenshot evidence: `scratch/exhaustive_suite/` and `scratch/matrix_evidence/`.

## UI and error-handling checks

- Stata Studio loads without an unhandled Streamlit exception.
- `xtset` output reports panel metadata and duplicate-key failures use Stata-style errors.
- `lgraph` renders the summary table and wide chart view.
- Unsupported commands return structured `r(199)` output and administrator guidance;
  raw Python tracebacks are not presented as normal UI.
- Missing `python-docx` degrades the export control without crashing the page.

## Dependency and license note

`python-docx>=1.1.0` is an optional document-export dependency; runtime detection preserves
operation when it is unavailable. No new analytical engine or external data source was added.

## Known limitations and risks

- Existing-command semantic hardening (`ModelResultContext`, post-estimation provenance,
  and estimator-specific diagnostics) is Wave 1 scope and remains outstanding.
- Browser evidence is currently stored as local scratch artifacts and should be attached to
  the review workflow as durable CI artifacts.
- Authentication credentials must continue to come from `.streamlit/secrets.toml` or
  `PROFSUR_AUTH_USERS`; they must never be copied into test scripts or reports.

## Review decision

`READY_FOR_REVIEW` — independent review and acceptance are required before declaring Wave 0
complete or merging subsequent Wave 1 work.
