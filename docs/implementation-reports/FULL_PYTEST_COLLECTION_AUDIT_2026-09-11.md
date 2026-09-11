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
diagnostic run excluding those exact tests progressed to 68% without failures
but then became silent for over 60 seconds and was stopped. This is evidence of
another slow/hanging test section, not a passing full-suite result.
