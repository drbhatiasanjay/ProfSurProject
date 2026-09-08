# WAVE 5 PR-03 — Independent Review Repair Report

**Date:** 2026-09-08
**Branch:** `reconcile/wave5-independent-review-repair-2026-09-08`
**Immutable reviewed baseline:** `88ab5c29c295abed19dd44820e809092806a433f`
**Master observed at review:** `b96cc3a`
**Status:** `READY_FOR_INDEPENDENT_RE_REVIEW`

## Goal

Repair every release-blocking finding from `INDEPENDENT_REVIEW_FAIL` without
rewriting the reviewed commit, adding analytical features, merging to `master`,
or promoting any unverified method to `VALIDATED`.

## Release-Blocking Invariant

A user-specified variable, grouping variable, clustering variable, estimator
option, absorb variable, or intervention is never silently dropped, replaced, or
defaulted. The command executes exactly the requested semantics or fails with a
typed user-visible error before estimator dispatch.

## Implementation Summary

- Added canonical `models/stata_validation.py` between parser and execution.
- Wired validation into both `execute_stata_command()` and `analytical_router.route()`.
- Added structured error metadata: Stata return code, invalid argument, and role.
- Removed dependent-variable, regressor, and `tabstat by()` substitutions.
- Implemented explicit covariance contracts for OLS and panel FE/RE:
  conventional, robust, and exact requested-variable clustering.
- Added scenario parsing for inline and `interventions()` syntax.
- Added typed HDFE `absorb()` list parsing and validation.
- Changed WS1 `ivregress` methodology status to `IMPLEMENTED_UNVERIFIED` while
  preserving successful execution.
- Removed legacy System-GMM, Arellano–Bond diagnostic, instrument-validity, and
  Blundell–Bond behavior claims from engine, UI, help, demo, and generated-doc surfaces.
- Updated Stata Studio to expose validation metadata and suppress success
  interpretation cards when estimation did not run.
- Added `docs/WAVE5_COMMAND_CONTRACTS.md` as the authoritative syntax/status contract.

## RED Evidence Against `88ab5c2`

Command:

```powershell
py -3.12 -m pytest -q --tb=line tests/test_wave5_independent_review_repair.py
```

Initial result: **29 failed, 2 warnings in 5.24s**; elapsed 8.48s including startup.

Failing node families included:

- `test_unknown_variables_fail_closed_through_execute[...]`
- `test_unknown_variables_fail_closed_through_router[...]`
- `test_missing_required_syntax_is_not_treated_as_unknown_variable[...]`
- `test_regress_covariance_semantics_and_cluster_reference`
- `test_xtreg_covariance_semantics_and_cluster_reference`
- `test_parser_preserves_covariance_contract[...]`
- `test_scenario_parser_to_adapter_contract[...]`
- `test_malformed_scenario_syntax_fails_closed[...]`
- `test_unknown_scenario_intervention_fails_before_adapter`
- `test_hdfe_absorb_parser_to_estimator_contract`
- `test_hdfe_unknown_absorb_variable_fails_before_estimation`
- `test_legacy_gmm_proxy_has_no_system_gmm_or_arellano_bond_claims`
- `test_ws1_availability_is_separate_from_master_merge_and_validation_docs`

Final suite contains **36 collected node IDs**, including explicit tests proving
validation prevents direct estimator dispatch and router handler resolution.

## Repaired Test Evidence

### Independent-review repair contracts

```powershell
py -3.12 -m pytest -q --tb=line tests/test_wave5_independent_review_repair.py
```

- 36 tests collected.
- Final result: **36 passed, 2 warnings in 3.80s**.

### Wave 2 / Wave 4 / WS1 / Wave 5 selection

```powershell
py -3.12 -m pytest -q --tb=line \
  tests/test_wave5_independent_review_repair.py \
  tests/test_wave5_contract_red.py tests/test_wave5_numerical_golden.py \
  tests/test_wave2_abstraction.py tests/test_wave4_expansion.py \
  tests/test_analysis_run_contracts.py tests/test_model_result_context.py \
  tests/test_stata_bidirectional_nlp.py tests/test_stata_studio_widgets.py
```

Result: **134 passed, 2 warnings in 5.36s**.

### Full GitHub-equivalent selection

```powershell
py -3.12 -m pytest tests/ \
  --ignore=tests/smoke_auth.py --ignore=tests/smoke_phase1.py \
  -q --tb=line
```

Result: **852 passed, 1 skipped, 38 warnings in 117.98s**.

The tracked `capital_structure.db` SHA-256 was identical before and after:
`354E9B4E62E54AACC0C4306253E9473EB65A7FC37F8ED9545EFEBABDBC915975`.

### Push-hook selection

```powershell
pwsh -NoProfile -ExecutionPolicy Bypass -File scripts/test_fast.ps1 -PrePush
```

Result: **67 passed, 1 warning in 2.94s**.

An initial sandboxed attempt produced one pytest temporary-lock permission error;
the exact hook passed outside the sandbox with no code change.

The actual code push hook expanded its selection because model and engine files
were changed and passed **115 tests, 18 warnings in 29.67s**.

## Real 9,031-Row Panel Audit

The audit used a disposable database copy. Both source and copy hashes remained
unchanged before and after execution.

- 22 documented core commands: **22 success** with genuine result payloads.
- WS1 commands (`ivregress`, `test`, `predict`, `winsor2`): **4 success**.
- Invalid dependent, regressor, `by()`, cluster, absorb, and intervention inputs:
  **8 typed `VARIABLE_NOT_FOUND` errors**, zero coefficient/result payloads.
- Covariance commands: **6 success**, with explicit metadata.
- Scenario canonical and alternate syntax: **2 partial intervention previews**.
- HDFE canonical syntax: **partial**, absorbed variables
  `company_code` and `year`.
- IV result metadata: `IMPLEMENTED_UNVERIFIED`.

Real-data standard errors for `profitability`:

| Command | SE |
|---|---:|
| OLS conventional | 2.595352716145 |
| OLS HC1 robust | 14.364779062551 |
| OLS clustered by `company_code` | 14.971126301766 |
| FE conventional | 0.025710064919 |
| FE robust | 0.190147849004 |
| FE clustered by `company_code` | 0.224648858744 |

Cluster metadata records `company_code` and 400 clusters. Invalid cluster
variables return `r(111)` before estimation.

## Playwright Evidence

Target: isolated local successor app on port 8502 using the disposable panel copy.

Result: **`PLAYWRIGHT_PASS journeys=4 commands=19`**.

Journeys covered:

1. typed validation errors and suppression of successful interpretation cards;
2. robust versus clustered covariance labels;
3. scenario and HDFE parser-to-adapter execution;
4. WS1 commands plus GMM/DiD/ML methodology status and corrected Advanced
   Econometrics wording.

Untracked evidence:

- `scratch/wave5_independent_review_repair/01_typed_validation_errors.png`
- `scratch/wave5_independent_review_repair/04_methodology_status.png`

## Factual Branch Record

- WS1 commands are implemented and executable on the reconciliation lineage.
- They are not yet available on `master` at `b96cc3a`.
- They remain pending independent approval, PR creation, and merge to `master`.
- Execution availability does not establish methodological validation.

## Remaining Methodological Limitations

- The legacy GMM routine remains an experimental levels IV-GMM proxy, not
  Arellano–Bond or Blundell–Bond System GMM.
- Residual lag correlations are descriptive Pearson statistics, not formal
  dynamic-panel AR tests.
- The IV-GMM J-test does not by itself establish instrument validity.
- WS1 IV, Wave 5 IV, HDFE, GMM, and ML remain unverified.
- ML lacks forward-time validation and hyperparameter cross-validation.
- Scenario remains an intervention preview without model-based counterfactuals.
- DiD remains unsupported.

## Explicit Non-Actions

- No PR created.
- No merge into `master`.
- No deployment.
- No Wave 6 work.
- No `capital_structure.db` staging or commit.
- No unrelated untracked files touched.

**Final verdict:** `READY_FOR_INDEPENDENT_RE_REVIEW`
