# Wave 8 PR-01 — Controlled Researcher Slice

**Date:** 2026-09-11  
**Status:** IMPLEMENTED — READY_FOR_REVIEW
**Predecessor:** Wave 7 PR-01 artifact contracts

## Goal

Define the first bounded FDI migration seam as a read-only researcher journey
that cannot widen role permissions or promote an unvalidated capability.

## Scope completed

- Added immutable `ResearcherSlice`.
- Bound every journey to a workspace, analysis run, and artifact IDs.
- Allowed only `admin` and `researcher` roles.
- Allowed only `challenge` and `reproduce` actions after creation.
- Forced the release status to remain `NOT_VALIDATED`.
- Mounted the slice on the canonical read-only `Overview` page for `admin` and
  `researcher` roles; `Reproduce` and `Challenge` are session-scoped actions.
- Added tests for immutability, authorization, action restrictions, and
  workspace/run preservation, including blank artifact-ID rejection.

## Non-goals

- No multi-tenant production deployment.
- No database or Streamlit navigation changes; the existing root navigation is
  unchanged and the Overview page is the only mounted surface.
- No estimator promotion, Redis, AST rewrite, credential changes, or GCP work.

## Verification

Command:

```text
python -m pytest -q tests/test_researcher_slice.py tests/test_research_artifacts.py tests/test_validation_ledger.py tests/test_benchmark_contracts.py tests/test_panel_mapping_contract.py --tb=line
```

Result: **22 passed, 1 warning in 4.10s** after the boundary hardening and
Overview mount. `pages/0_overview.py` and `models/researcher_slice.py` compile
cleanly; `git diff --check` passed.
`git diff --check` passed.

## Acceptance boundary

The slice is intentionally not a validation release: its status remains
`NOT_VALIDATED`, and no estimator or authorization boundary is widened. Fresh
authenticated browser acceptance remains separate because this session lacks a
browser automation surface and process-only verification credential.

## Implementation checkpoint

- Commit: `3be735d`
- Mounted surface: root `app.py` → registered `Overview` → `pages/0_overview.py`
- Allowed roles: `admin`, `researcher`
- Allowed actions: `view`, `reproduce`, `challenge`
- Evidence: `22 passed, 1 warning`; page/module compilation passed.
