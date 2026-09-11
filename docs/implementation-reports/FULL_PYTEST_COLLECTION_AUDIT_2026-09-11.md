# Full Pytest Collection Audit — 2026-09-11

## Result

**BLOCKED at collection; not a runtime regression of the current changes.**

Command:

```text
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 py -3.12 -m pytest -q tests/ --tb=line
```

The plugin-disabled run reached collection in 37.92 seconds and stopped on
three import errors:

| Test surface | Import error | Classification |
|---|---|---|
| `tests/test_descriptive_analyst.py` | `AnalysisRun` absent from `models.decision_contracts` | phase/test-surface mismatch |
| `tests/test_parallel_simulations.py` | `models.analytical_contracts` absent | phase/test-surface mismatch |
| `tests/test_phase14_econometrics_workbench.py` | `ModelResultContext` absent from `models.stata_engine` | phase/test-surface mismatch |

These test files are untracked in the current working tree and appear to
represent work from non-canonical or unmerged phase slices. They were not
deleted, modified, or excluded. The correct resolution is to reconcile their
branch/source dependencies or formally remove them through an approved
repository decision—not to suppress collection errors.

## Passing focused gates

- `tests/test_auth.py` — 6 passed in 5.03s
- `tests/test_ai_stata_routing.py` + `tests/test_panel_mapping_contract.py` —
  10 passed in 5.90s
- `py_compile` for changed Python modules — PASS

## Environment finding

Default pytest plugin autoload caused an earlier no-output stall. Disabling
plugin autoload isolates that contention, but does not resolve the independent
collection errors above.

## Follow-up

The tracked `tests/_debug_auth.py` import-time Playwright runner was converted
to an opt-in `main()` and now requires process-only
`PROFSUR_VERIFY_PASSWORD`. It no longer starts a browser during collection or
contains a plaintext credential.

With that correction, a plugin-disabled collection reached **735 tests** and
still reported only the three phase-test import mismatches listed above. A
tracked-only run collected **732 tests** and passed through **70%** without a
failure, then became silent while executing
`tests/test_models.py::TestMLModels::test_cross_validate_xgboost`; that known
test process was stopped after an additional 60 seconds. This is evidence of a
slow or hanging XGBoost section, not a passing full-suite result. The three
phase-test import mismatches and the XGBoost hang remain open gates.

## Bounded ML follow-up

The stall was isolated to the XGBoost ML test path. XGBoost and LightGBM are
now explicitly configured with `n_jobs=1`, matching the existing Random Forest
resource policy. This is a Windows/resource-containment change; no speedup is
claimed.

- XGBoost configuration contract + cross-validation: **2 passed in 37.34s**
- LightGBM configuration contract + cross-validation: **2 passed in 34.67s**

The broad suite remains open: the three phase-test imports and remaining
full-run coverage require separate closure.

## Canonical tracked-suite rerun

After the single-process ML configuration, the complete tracked test set was
run in one clean process with third-party plugin autoload disabled:

```text
$tracked = git ls-files 'tests/test_*.py'
py -3.12 -m pytest $tracked -q --tb=line
```

**733 passed, 1 skipped, 38 warnings in 279.18s.** The canonical tracked
baseline is therefore green. The three import mismatches belong to preserved
untracked phase-test files and are not part of this canonical result.

## Consolidated regression gate

The post-mitigation deterministic gate passed in one clean process with
third-party plugin autoload disabled:

```text
tests/test_auth.py
tests/test_ai_stata_routing.py
tests/test_panel_mapping_contract.py
tests/test_models.py::TestMLModels
```

**19 passed in 74.05s.** This closes the focused regression gate while leaving
the repository-wide collection mismatches and fresh authenticated UI gate
explicitly open.
