# Wave 7 PR-01 — Research Artifact Contracts

**Date:** 2026-09-11  
**Status:** READY_FOR_REVIEW  
**Predecessor:** Wave 6 PR-01, `c8e3a9d`

## Goal

Create a minimal immutable presentation boundary so visualizations and
narratives remain tied to the exact analysis run, dataset/sample, result, and
capability status that produced them.

## Scope completed

- Added `ArtifactProvenance`.
- Added immutable `VisualizationArtifact` and `NarrativeArtifact` contracts.
- Added builders with category/series alignment and required-claim validation.
- Added deny-by-default causal-language and limitation checks for narratives
  whose capability status is not `VALIDATED`.
- Added tests for provenance binding, immutability, malformed series, and empty
  claims.

## Non-goals

- No renderer or page changes.
- No causal-language promotion.
- No estimator changes or capability-status changes.
- No Redis, AST rewrite, deployment, or credential changes.

## Verification

```text
python -m pytest -q tests/test_research_artifacts.py tests/test_validation_ledger.py tests/test_benchmark_contracts.py tests/test_panel_mapping_contract.py --tb=line
```

Result: **15 passed, 1 warning in 4.21s**. `git diff --check` passed.

## Limitations

The contracts are mounted only through the provenance/descriptive renderer
gates; full authenticated browser acceptance remains required. Production
capability promotion still requires the Wave 6 validation ledger.
