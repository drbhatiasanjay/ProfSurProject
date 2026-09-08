# WAVE 5 PR-01 — Advanced Methods Implementation Report

**Report ID:** `WAVE_5_PR_01_ADVANCED_METHODS_REPORT`
**Date:** 2026-09-08
**Historical implementation commit:** `85ccd1e`
**Reconciliation branch:** `reconcile/wave5-ws1-contract-repair-2026-09-08`
**Status:** `READY_FOR_INDEPENDENT_REVIEW`

---

## Goal

Preserve the Wave 5 implementation as historical evidence while making its
advanced econometric, causal, scenario, and machine-learning paths conform to
the canonical Wave 2 contracts and fail closed until method-specific validation
is sufficient for a `VALIDATED` classification.

## Scope Completed

- Removed fabricated `CommandSpec` use and invented request/result fields.
- Standardized Wave 5 adapters on `AnalyticalRequest`, `CapabilityResult`, and
  `AnalysisRunEnvelope`.
- Added `partial` to the run-envelope lifecycle.
- Normalized legacy handler statuses to canonical lowercase values at the router.
- Preserved validated Wave 1 `ivregress` routing; Wave 5 IV remains isolated as
  `iv_candidate`.
- Restored Wave 5 parser and Stata Studio console dispatch lost during the WS1 merge.
- Added a central router gate that demotes false `success` from:
  - `IMPLEMENTED_UNVERIFIED` to `partial`;
  - `CANDIDATE` to `unsupported`.
- Restored Wave 4 handler imports and post-estimation state interoperability after
  the WS1 merge.
- Corrected user-facing descriptions for GMM, HDFE, DiD, scenario, and ML.

## Capability Classification

| Command / adapter | Registry state | Runtime completion | Limitation |
|---|---|---|---|
| `gmm` | `IMPLEMENTED_UNVERIFIED` | `partial` or typed error | IV-GMM proxy; not Arellano-Bond or Blundell-Bond System GMM |
| Wave 5 IV adapter | isolated candidate | `partial` or typed error | Does not replace validated Wave 1 `ivregress` |
| `hdfe` | `IMPLEMENTED_UNVERIFIED` | `partial` or typed error | Requires independent sample/SE/covariance parity review |
| `didregress` | `CANDIDATE` | `unsupported` | No cohort-robust estimator or parallel-trends diagnostics |
| `scenario` | `CANDIDATE` | `partial` preview or `unsupported` | No fitted counterfactual model or uncertainty intervals |
| `predict_ml` | `IMPLEMENTED_UNVERIFIED` | `partial` or typed error | Firm-aware holdout; no temporal forecasting validation or k-fold CV |

No Wave 5 advanced method is classified as `VALIDATED`.

## Contracts Changed

- `AnalysisRunEnvelope.status` now accepts `partial`, matching `CapabilityResult`.
- `analytical_router.route()` validates lowercase status and applies registry-state
  fail-closed demotion.
- Legacy shim conversion now preserves `message` and `error_code`.
- No third-party model object is exposed through a public contract.

## Dependencies / License Rationale

No dependency was added in this reconciliation.

- `linearmodels` remains the IV/IV-GMM engine already declared in requirements.
- `scikit-learn` remains the Ridge/group-holdout engine already declared.
- `pyfixest` is optional and lazily imported; it is not added to production
  requirements by this repair.
- All heavy imports remain inside adapter runtime functions.

## Tests Added or Repaired

- `tests/test_wave5_contract_red.py`
  - 37 fast contract/import/routing tests.
  - Real estimators replaced with deterministic dependency mocks or minimal fixtures.
  - Historical four `xfail` pipeline checks converted into passing status-gate tests.
- `tests/test_wave5_numerical_golden.py`
  - closed-form 2SLS coefficient parity;
  - planted two-way HDFE coefficient recovery;
  - closed-form Ridge coefficient parity with disjoint firm groups;
  - scenario source-data immutability;
  - registry classification and router-demotion gates.
- `pytest.ini`
  - disables unintended auto-loading of the local `napari` pytest plugin.

## Exact Test Commands and Results

```powershell
py -3.12 -m pytest --collect-only -q tests/test_wave5_contract_red.py
```

- 37 tests collected.
- Collection: 0.40 seconds pytest time.

```powershell
py -3.12 -m pytest -q --tb=line \
  tests/test_wave5_contract_red.py tests/test_wave5_numerical_golden.py
```

- 44 passed, 2 warnings in 3.01 seconds.

```powershell
py -3.12 -m pytest -q --tb=line \
  tests/test_analysis_run_contracts.py tests/test_model_result_context.py \
  tests/test_wave2_abstraction.py tests/test_wave4_expansion.py \
  tests/test_stata_bidirectional_nlp.py tests/test_stata_studio_widgets.py \
  tests/test_wave5_contract_red.py tests/test_wave5_numerical_golden.py
```

- 98 passed, 2 warnings in 3.96 seconds.

```powershell
py -3.12 -m pytest tests/ \
  --ignore=tests/smoke_auth.py --ignore=tests/smoke_phase1.py \
  -q --tb=line
```

- 816 passed, 1 skipped, 38 warnings in 117.55 seconds.
- This is the same test selection as `.github/workflows/deploy.yml`.
- Local Python 3.11 was unavailable; the complete selection ran on Python 3.12.

## Numerical / Golden Evidence

- IV/2SLS: 600-observation synthetic case matched an independent closed-form
  projection-matrix reference within absolute tolerance `1e-5`; result remains
  `partial`.
- HDFE: deterministic two-way fixed-effects fixture recovered planted coefficient
  `1.75` within absolute tolerance `1e-6`; result remains `partial`.
- ML: Ridge coefficients matched an independent centered closed-form solution at
  `alpha=1.0` within absolute tolerance `1e-5`; train/test firm sets are disjoint;
  result remains `partial`.
- Scenario: source DataFrame equality is exact after intervention preview; result
  remains `partial` and explicitly denies validated counterfactual status.
- GMM: no System GMM numerical validation is claimed. The current code remains an
  IV-GMM proxy and must not be cited as Arellano-Bond or Blundell-Bond.

## UI Verification

Target: local Streamlit `http://127.0.0.1:8501/stata_studio`.

Targeted headless Playwright checks passed for four commands:

1. `gmm` — unverified IV-GMM wording and typed syntax error.
2. `didregress leverage profitability` — candidate/fail-closed wording.
3. `scenario` — intervention-preview wording and unsupported UI state.
4. `predict_ml leverage profitability tangibility log_size` — firm-aware
   `GroupShuffleSplit`, unverified status, and test metrics.

Evidence screenshot:
`scratch/wave5_reconciliation_evidence/stata_studio_wave5_fail_closed.png`.

## Errors Encountered

- The original RED suite exceeded 18 minutes before test output.
- Exact collect-only also exceeded a bounded 60-second audit.
- Root cause: locally auto-loaded `napari.utils._testsupport`; isolated import
  exceeded the 10-second bound before collection. No individual test node hung.
- After `-p no:napari` and estimator mocking, 37 RED tests complete in 2.38 seconds.
- Playwright initially hit stale Streamlit sessions and overly strict text assertions;
  the verifier was isolated per command and capped at 90 seconds.

## Known Limitations

1. Current GMM is not a validated dynamic-panel estimator.
2. HDFE and IV do not yet have dissertation-data sample-membership, clustered-SE,
   and diagnostic parity evidence sufficient for `VALIDATED`.
3. ML uses a firm-group holdout, not forward-chaining temporal validation.
4. Scenario remains an intervention preview without model-based counterfactuals.
5. DiD remains unavailable until a cohort-robust implementation and identification
   diagnostics are added under a separately approved scope.
6. UI unsupported rendering uses a generic card and may not display every typed
   backend message, although the methodology translation is visible.

## Non-Goals Respected

- No merge into `master`.
- No deployment.
- No Wave 6 work.
- No original Wave 5 pull request.
- No unrelated database or untracked user artifact included.

## Recommendation

Open a new reconciliation pull request from
`reconcile/wave5-ws1-contract-repair-2026-09-08` to `master` only after independent
methodological and code review. Do not revive the original Wave 5 pull request.

**Final verdict:** `READY_FOR_INDEPENDENT_REVIEW`
