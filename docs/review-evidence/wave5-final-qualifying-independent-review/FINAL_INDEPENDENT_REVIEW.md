# Wave 5 Final Qualifying Independent Review

**Reviewer context**: FRESH_AND_IMPLEMENTATION_INDEPENDENT  
**Review date**: 2026-09-09  
**Reviewer**: Antigravity (no inherited Wave 5 development or repair context)  
**Candidate SHA**: `5c02509f18b1fa8cb2070f88d78fb2cf5393e48f`  
**Baseline SHA**: `88ab5c29c295abed19dd44820e809092806a433f`  
**Canonical evidence HEAD**: `3e05faec1205ef58e4512f6c2b4e981abf09bce1`  
**Reviewer branch**: `review/wave5-5c02509-final-independent-2026-09-09`

---

## Review A — Native Playwright Acceptance

### Execution Record

| Item | Value |
|------|-------|
| Isolated worktree | `C:\Users\hemas\Downloads\ProfSurProject\.worktrees\wave5-final-independent-5c02509` |
| Worktree HEAD | `5c02509f18b1fa8cb2070f88d78fb2cf5393e48f` |
| Streamlit port | 8504 |
| Streamlit PID | 38096 (first attempt, crashed); task-1400 (successful daemon) |
| HTTP 200 confirmed | YES |
| Verifier command | `py -3.12 scripts\verify_wave5_ui.py --base-url http://127.0.0.1:8504 --username profsurkumar --evidence-dir scratch/wave5_final_independent_review` |
| Verifier start | 2026-09-09T17:28:58Z |
| Verifier end | 2026-09-09T17:30:02Z |
| Duration | ~64 seconds |
| Exit code | **0** |
| Pass marker | **`PLAYWRIGHT_PASS journeys=4 commands=19`** |
| Journeys completed | 4 of 4 |
| Commands submitted | 19 of 19 |
| Pass screenshot | `playwright/wave5_ui_pass.png` |

### Database Integrity

| Database | SHA-256 Before | SHA-256 After | Intact |
|----------|---------------|---------------|--------|
| Source `capital_structure.db` | `354e9b4e62e54aacc0c4306253e9473eb65a7fc37f8ed9545efebabdbc915975` | `354e9b4e62e54aacc0c4306253e9473eb65a7fc37f8ed9545efebabdbc915975` | **YES** |
| Disposable copy | `354e9b4e62e54aacc0c4306253e9473eb65a7fc37f8ed9545efebabdbc915975` | `354e9b4e62e54aacc0c4306253e9473eb65a7fc37f8ed9545efebabdbc915975` | YES (read-only run) |

Source database integrity: **CONFIRMED PRESERVED**.

### Journey Summary

| Journey | Commands | Coverage | Result |
|---------|----------|----------|--------|
| 1 — Invalid variable rejection | 4 | `nonexistent_var`, `nonexistent_col` across `regress`, `tabstat`, `xtreg`, `regress vce(cluster nonexistent_col)` | PASS — each returned `Stata Validation Error — estimation was not run` + `r(111)` + invalid name; no `Econometric Deconstruction` rendered |
| 2 — Covariance labelling | 4 | Robust HC1, cluster company_code (OLS + xtreg) | PASS — HC1 and 400-cluster labels confirmed per command |
| 3 — Scenario / HDFE | 3 | scenario (2 forms), hdfe | PASS — `INTERVENTION PREVIEW` confirmed for scenario; HDFE accepted either `IMPLEMENTED_UNVERIFIED` or `pyfixest not installed` |
| 4 — Post-estimation chain | 8 (1 fresh + 7 fresh=False) | xtreg→test→predict→ivregress→winsor2→gmm→didregress→predict_ml | PASS — all commands executed and produced current-command-bound results |

**Journey 4 critical check (xtreg → test profitability = 0):**
- `xtreg leverage profitability tangibility log_size, fe` submitted fresh; `Fixed-effects` confirmed
- `test profitability = 0` submitted `fresh=False`; `Prob > F` confirmed with command-specific title `Stata 18 SE · test profitability = 0`
- Stale text from prior command could not satisfy assertion because assertion includes current-command title prefix

### Candidate Repair Independently Verified

The candidate introduced two changes to the verifier/helper (new files in the baseline comparison):

1. **`scripts/playwright_stata.py`** (new): Uses middle-dot `·` (U+00B7) in `f"Stata 18 SE · {command}"` matching the UI's rendered title separator (confirmed at `pages/23_stata_studio.py` line 619).
2. **Fragment OR-logic** (lines 45-48): Assertions support `tuple` alternatives — any one matching satisfies the assertion. This correctly handles the HDFE optional-dependency case.
3. **`pages/23_stata_studio.py`**: Changed `text_input` to use `key="stata_cmd_input"` (Streamlit keyed widget, prevents stale reinit); routes all commands through `route(request)` with `ModelResultContext`; clears stale result on each submission with `st.session_state["stata_last_result"] = None`.

None of these changes introduce silent result binding or stale output acceptance.

### Stale Text Safety

The verifier's first assertion for every command is `f"Stata 18 SE · {command}"` — the exact command string is part of the first required fragment. A stale prior result cannot satisfy this because it contains a different command in the title.

---

## Review B — Independent Methodology Truthfulness

### Files Inspected

- `models/capability_status.py` — status registry
- `models/capability_registry.py` — routing
- `models/analytical_router.py` — dispatcher
- `models/stata_engine.py` — OLS/xtreg engine VCE paths
- `models/stata_validation.py` — pre-estimation fail-closed validation
- `models/causal_adapters.py` — IV, HDFE, DID adapters
- `models/gmm_adapter.py` — GMM proxy adapter
- `models/scenario_capability.py` — scenario adapter
- `pages/23_stata_studio.py` — UI rendering
- `docs/WAVE5_COMMAND_CONTRACTS.md` — command contracts
- `docs/CAPABILITY_STATUS.md` — capability documentation

### Check Results

| # | Requirement | Finding | Result |
|---|-------------|---------|--------|
| 1 | Conventional, robust, and clustered covariance behaviorally and textually distinguished | OLS: `nonrobust` / `HC1` / `cluster with cov_kwds groups=sub[cluster_variable]`; text labels: default / `(HC1 heteroskedasticity-robust standard errors)` / `(Std. err. adjusted for N clusters in VARNAME)`. Panel xtreg: identical differentiation. Both the cluster variable name and count appear in the output. | **PASS** |
| 2 | Invalid cluster, group, absorb, intervention variables fail closed before estimation | `stata_validation.py` `_resolve()` called before estimation for `cluster` and `by`; returns `ValidationError(r(111))` with `invalid_argument=raw_term`. HDFE `absorb` type-checked; `ImportError` for missing pyfixest returns clean `DEPENDENCY_UNAVAILABLE`. | **PASS** |
| 3 | Scenario described only as intervention preview, not model-derived counterfactual | `scenario_capability.py` docstring (line 4): `STATUS: CANDIDATE / INTERVENTION PREVIEW ONLY`; `_STATUS_MESSAGE`: `"INTERVENTION PREVIEW (not validated counterfactual)"`. UI: `"intervention preview only; it is not a validated counterfactual forecast."` | **PASS** |
| 4 | HDFE remains partial/unverified | `causal_adapters.py` docstring: `IMPLEMENTED_UNVERIFIED (pyfixest feols; requires golden benchmark)`. Returns `status="partial"`. `capability_status.py`: `registry_status="IMPLEMENTED_UNVERIFIED"`. | **PASS** |
| 5 | Missing optional HDFE dependency cannot be mistaken for successful estimation | `ImportError` path returns `status="error"`, `message="pyfixest not installed..."`, `error_code="DEPENDENCY_UNAVAILABLE"`. Verifier accepts this as truthful. | **PASS** |
| 6 | GMM not presented as System GMM / Arellano–Bond / Blundell–Bond | `gmm_adapter.py` line 9: `"Do not present this as System GMM in any UI or report."` ASCII output: `"IV-GMM Proxy (NOT System GMM)"`. Methodology disclaimer prepended. | **PASS** |
| 7 | Descriptive residual correlations not presented as formal dynamic-panel AR tests | `gmm_adapter.py`: Pearson lag-1/2 correlations labelled `"(NOTE: descriptive correlation only; not a formal dynamic-panel test)"` inline. | **PASS** |
| 8 | J-test not presented as proof of instrument validity | `j_pval` reported from `result.j_stat.pval` as `"Hansen J-statistic p-value"` without validity claim; overarching `_METHODOLOGY_DISCLAIMER` and `IMPLEMENTED_UNVERIFIED` status apply. | **PASS** |
| 9 | IV, GMM, HDFE, ML, scenario, other advanced methods not marked VALIDATED without qualifying evidence | `capability_status.py` registry: iv=`IMPLEMENTED_UNVERIFIED`, gmm=`IMPLEMENTED_UNVERIFIED`, hdfe=`IMPLEMENTED_UNVERIFIED`, predict_ml=`IMPLEMENTED_UNVERIFIED`, scenario=`CANDIDATE`, didregress=`CANDIDATE`. No capability is `VALIDATED`. | **PASS** |
| 10 | UI text, registry status, result metadata, help text, documentation agree | `pages/23_stata_studio.py` `get_financial_translation()` now reads from `capability_status()` live registry for GMM, HDFE, DID, scenario, predict_ml, ivregress descriptions. Single source of truth. | **PASS** |
| 11 | No silent parameter substitution in Wave 5 paths | `analytical_router.py` contains no silent fallback/substitution pattern. `stata_validation.py` validates all semantic arguments before dispatch. | **PASS** |
| 12 | Streamlit repair does not misbind results to wrong command or reuse stale output | `key="stata_cmd_input"` prevents Streamlit stale widget reinit. `st.session_state["stata_last_result"] = None` clears on each new submission. `route(request)` dispatches fresh `AnalyticalRequest` with unique `correlation_id` and current `command_str`. UI renders `Stata 18 SE · {active_cmd}` from current execution only. | **PASS** |

### Blocking Findings

**None.**

---

## Application Code and Test Modification Statement

The reviewer did not modify any application code, tests, verifier scripts, or existing evidence during this review. The isolated worktree was used for execution only. The reviewer branch contains only new evidence files.

---

## Verdict

```
NATIVE_PLAYWRIGHT_ACCEPTANCE      = PASS
INDEPENDENT_METHODOLOGY_REVIEW    = PASS
RECOMMENDED_WAVE_5_CORE_BASELINE_GATE = PASS
```
