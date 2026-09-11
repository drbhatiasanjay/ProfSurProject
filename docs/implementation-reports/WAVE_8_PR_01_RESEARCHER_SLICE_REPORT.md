# Wave 8 PR-01 — Controlled Researcher Slice

**Date:** 2026-09-11  
**Status:** READY_FOR_REVIEW  
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
- Added tests for immutability, authorization, action restrictions, and
  workspace/run preservation.

## Non-goals

- No multi-tenant production deployment.
- No database or Streamlit navigation changes.
- No estimator promotion, Redis, AST rewrite, credential changes, or GCP work.

## Verification

Command:

```text
python -m pytest -q tests/test_researcher_slice.py tests/test_research_artifacts.py tests/test_validation_ledger.py tests/test_benchmark_contracts.py tests/test_panel_mapping_contract.py --tb=line
```

Result: **18 passed, 1 warning in 3.30s**. `git diff --check` passed.

## Limitation

The contract is not yet mounted in a page. The next slice must connect it to a
single existing read-only researcher view and verify the canonical root app.
