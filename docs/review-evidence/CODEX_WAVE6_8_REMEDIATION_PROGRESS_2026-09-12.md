# Codex Wave 6–8 Remediation Checkpoint

**Status:** IN PROGRESS — not an acceptance report

## Scope

This isolated repair worktree implements the approved technical and functional remediations. Deployment `secrets.toml` hardening and the common MVP test-password policy are explicitly excluded by user decision.

## Implemented and locally verified

- Added `models/model_context.py` with session-scoped model identity and JSON-safe public projection.
- Added explicit `AnalysisSession` support to the Stata execution seam and wired the AI Assistant and Stata Studio pages to session-scoped state.
- Removed silent FE/RE estimator fallback and hidden leverage rescaling.
- Required explicit panel setup for `xtreg`; removed positional panel inference from `xtset` query behavior.
- Bound `coefplot`, `esttab`, Hausman, and VIF behavior to available stored/model state; no hidden model synthesis.
- Renamed the implementation to `run_legacy_proxy_gmm` and labeled the result as a legacy IV-GMM proxy, retaining a compatibility alias for older callers.
- Replaced row-position GMM lags with exact calendar lags and fail-closed invalid panel-index handling.
- Added AI cache revisioning (`wave6-8-context-v2`) so stale narrative responses are not reused across result-context contract changes.
- Added normalized `error_code` values for unsupported commands and uncaught engine failures.
- Added `scripts/repo_governance_guard.py`, a fail-fast preflight that checks the isolated worktree index and shared Git objects/refs are writable before tests or commits start.

## Evidence executed

```text
python -m py_compile models/model_context.py models/stata_engine.py models/econometric.py models/llm_adapters.py pages/19_ai_assistant.py pages/23_stata_studio.py
python -m pytest -q tests/test_model_context.py tests/test_panel_mapping_contract.py --tb=line
```

Result: 10 tests passed, including the calendar-lag RED→GREEN test. The fast project gate also passed (`tests/test_chart_switcher_and_literature.py`: 6 passed). The test process emitted only existing Streamlit/no-runtime and pytest cache warnings.

The governance guard reproduced the environmental defect deterministically with exit code 2 and explicit `PermissionError` reports for the worktree metadata, objects, and refs directories.

AGY has reported a replacement MVP harness, `run_mvp_validation.py`, and an
active smoke/matrix task `task-3930`. This remains pending evidence review;
the previous 22-case selector run is invalidated. AGY must synchronize its
handoff, defect register, selector contract, exact SHA, and six Markdown
artifacts before Codex can review or promote the validation.

AGY subsequently completed run `AGY-W6-8-2UFJDIUM` on its isolated branch
(`4a96d765e1a461dfe38c721273c13c1c9f233c4b`) with `26 PASS / 30 FAIL / 0
BLOCKED`. The run is rejected as an acceptance gate. Most AI failures captured
the transient `Working...` state; several Stata rejection expectations conflict
with observed supported results. These require harness/registry reconciliation
before a targeted rerun.

## Not yet accepted

- Full regression suite and authenticated browser matrix are not yet rerun on this repair branch.
- Git commit is currently blocked by OS permission errors writing the isolated worktree Git index/object database; no shared or master worktree was modified by Codex.
- AI cache persistence still requires end-to-end UI/database verification.
- Numerical equivalence and production performance are not claimed.

## Required next gate

Resolve the isolated Git metadata permission contention, commit the complete repair slice, then run deterministic tests followed by authenticated root-`app.py` UI verification and update this checkpoint with exact commit SHA and reproducible evidence.
