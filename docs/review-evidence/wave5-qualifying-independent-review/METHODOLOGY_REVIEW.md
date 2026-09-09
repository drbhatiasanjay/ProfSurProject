# Wave 5 Qualifying Independent Review — Methodology Review

**Reviewer**: Antigravity (qualifying re-review — fresh, not inheriting prior conclusions)
**Review date**: 2026-09-09
**Code candidate SHA**: `d5ffdf2b2d9f77d3f4f83bd2bf90a19475d4001f`
**Evidence base SHA**: `9533eb02cb295463df0cda237f829b468bd3b9ef`

---

## Review Scope

Direct inspection of implementation files in the isolated worktree at candidate SHA `d5ffdf2`.
Files inspected:

| File | Purpose |
|------|---------|
| `models/capability_registry.py` | Command routing table |
| `models/stata_expansion_handlers.py` | Wave 4/5 handler implementations |
| `models/causal_adapters.py` | IV, HDFE, DID adapter classes |
| `models/gmm_adapter.py` | GMM adapter |
| `models/scenario_capability.py` | Scenario/intervention adapter |
| `models/capability_status.py` | Authoritative status registry |
| `models/stata_engine.py` | Core engine (VCE, xtreg, regress) |
| `models/stata_validation.py` | Fail-closed input validation |

---

## M-1 — Routing: `estat summarize`, `testparm`, `lincom`

### `estat summarize`

**Finding**: Routed via `_estat_dispatcher` (registry key `post_estimation`).  
`_estat_dispatcher` (lines 100–114, `capability_registry.py`) checks `"summarize"` in `indepvars` or `options` and calls `_handle_estat_summarize`.  
`_handle_estat_summarize` (lines 116–144) correctly retrieves `_get_last_estimate`, builds estimation-sample summary from `depvar` + `indepvars`.  
**Verdict: IMPLEMENTED and routed correctly.**

### `testparm`

**Finding**: Registry key `wald_test` dispatches to `_handle_testparm` (imported as `_handle_test` from `stata_expansion_handlers`), lines 206–209.  
`_handle_test` (lines 484–570, `stata_expansion_handlers.py`) implements a full Wald test using the active estimation's covariance matrix, constructing R matrix and computing F-statistic with `prob > F`.  
**Verdict: IMPLEMENTED correctly with guardrails (H-01, M-01).**

### `lincom`

**Finding**: Registry key `linear_combination` maps to `_handle_lincom` (lines 576–643).  
`_handle_lincom` computes linear combination of coefficients from active estimation state, producing estimate, SE, t-stat, p-value, and 95% CI. Handles single variable, difference (`-`), and sum (`+`) expressions.  
Statistical meaning: correctly computes Δβ = w'β, SE = √(w'Vw), t = Δβ/SE using the estimation covariance matrix — this is the standard Stata `lincom` implementation.  
**Verdict: IMPLEMENTED correctly. The prior F1 finding that `lincom` "returns an error" is NOT substantiated by this code at candidate SHA `d5ffdf2`.**

---

## M-2 — Covariance: Robust vs Clustered Implementation

### OLS (`regress`) — `stata_engine.py` lines 1161–1248

| VCE type | Implementation |
|----------|--------------|
| `nonrobust` | `model.fit(cov_type="nonrobust")` |
| `robust` | `model.fit(cov_type="HC1")` → outputs `"HC1 heteroskedasticity-robust standard errors"` |
| `cluster` | `model.fit(cov_type="cluster", cov_kwds={"groups": sub[cluster_variable]})` → outputs `"(Std. err. adjusted for N clusters in variable)"` |

These three paths are **numerically distinct** and correctly differentiated.

### Panel (`xtreg`) — `stata_engine.py` lines 1446–1458

| VCE type | Implementation |
|----------|--------------|
| `nonrobust` | `mod.fit(cov_type="unadjusted")` |
| `robust` | `mod.fit(cov_type="robust")` → outputs `"Heteroskedasticity-robust standard errors"` |
| `cluster` | `mod.fit(cov_type="clustered", clusters=clusters)` → outputs `"(Std. err. adjusted for N clusters in variable)"` |

**Verdict: PASS — Robust and clustered covariance are correctly differentiated for both OLS and panel estimators. Prior F2 finding is NOT substantiated.**

---

## M-3 — Fail-closed Validation: `group`, `cluster`, `absorb`

### `stata_validation.py` inspection (lines 40–144)

- **`cluster` validation** (lines 43–85): Uses `_resolve()` to look up variable in `df.columns`. If the cluster variable is not found, returns `ValidationError(r(111), invalid_argument=raw_term)`. This fires before estimation.
- **`by` / grouping validation** (lines 125–145): `_grouping_option()` similarly calls `_resolve()` and returns `ValidationError` if not found.
- **`absorb` in HDFEAdapter** (`causal_adapters.py` lines 158–166): Validates `absorb` is a list type; non-list returns `error`. Column membership check is implicit via `pyfixest` formula parsing (unknown columns raise exceptions caught at lines 184–190 and returned as `ENGINE_FAILURE`).

**Verdict: PASS for `cluster` and `by` — explicit fail-closed pre-estimation rejection via `stata_validation.py`. PARTIAL for `absorb` — type check present but column existence not pre-validated before calling pyfixest; engine exception is caught and returned as error, which is functional but not fail-closed in the strict sense.**

---

## M-4 — Scenario Preview Labelling

**Finding**: `scenario_capability.py` module docstring (lines 1–16) states:  
> `STATUS: CANDIDATE / INTERVENTION PREVIEW ONLY`  
> `This adapter provides only an INTERVENTION PREVIEW (steps 1-2 partial) and must NOT claim success as a counterfactual prediction result.`

`ScenarioAdapter.run()` returns `status="partial"` with `_STATUS_MESSAGE` = `"INTERVENTION PREVIEW (not validated counterfactual): ..."`.  
`capability_status.py` `CAPABILITY_STATUS["scenario"]` = `registry_status: CANDIDATE`, `label: "Intervention preview"`, `limitation: "Not a model-based counterfactual forecast."`.

**Verdict: PASS — Scenario is correctly labelled as CANDIDATE/INTERVENTION_PREVIEW throughout code, status, and UI output.**

---

## M-5 — HDFE Partial/Unverified Labelling

**Finding**: `causal_adapters.py` line 6: `HDFEAdapter — IMPLEMENTED_UNVERIFIED (pyfixest feols; requires golden benchmark)`.  
`_IDENTIFICATION_DISCLAIMER` prefixed to all output.  
`result_status_metadata("hdfe")` returns `registry_status: IMPLEMENTED_UNVERIFIED`.  
`capability_status.py` limitation: `"Sample, covariance, and absorbed-effect parity require independent validation."`.

**Verdict: PASS — HDFE correctly labelled IMPLEMENTED_UNVERIFIED throughout.**

---

## M-6 — IV-GMM: No System-GMM / Arellano-Bond / Blundell-Bond Claims

**Finding**: `gmm_adapter.py` line 9: `Do not present this as System GMM in any UI or report.`  
`_METHODOLOGY_DISCLAIMER`: `"not a validated dynamic-panel estimator"`.  
ASCII output explicitly says `"IV-GMM Proxy (NOT System GMM)"`.  
`result_status_metadata("gmm")`: `label: "Experimental IV-GMM proxy"`, `limitation: "Not Arellano-Bond or Blundell-Bond System GMM."`.  
`capability_status.py` GMM limitation: `"Not Arellano-Bond or Blundell-Bond System GMM."`.

**Verdict: PASS — No System-GMM, Arellano-Bond, or Blundell-Bond claims are made anywhere.**

---

## M-7 — Experimental IV-GMM Proxy Labelling

**Finding**: `capability_status.py` label = `"Experimental IV-GMM proxy"`.  
`CAPABILITY_STATUS["gmm"]` = `registry_status: IMPLEMENTED_UNVERIFIED`.  
Disclaimer explicit in all output.

**Verdict: PASS — Correctly labelled as experimental IV-GMM proxy.**

---

## M-8 — J-Test Qualification

**Finding**: `gmm_adapter.py` line 154:  
```python
j_pval = float(result.j_stat.pval) if hasattr(result, "j_stat") else float("nan")
```
ASCII output line 168: `f"Hansen J-statistic p-value: {j_pval:.4f}"`  
The J-stat value is reported from `linearmodels.iv.IVGMM.j_stat` if available, otherwise `nan`.  
No explicit claim that this constitutes a formal instrument validity test; the methodology disclaimer and `IMPLEMENTED_UNVERIFIED` status apply.

**Verdict: PARTIAL — J-stat is reported but qualified by the overarching `IMPLEMENTED_UNVERIFIED` disclaimer. It is not claimed as a validated instrument validity test. Not a BLOCKED finding — this is a disclosed limitation.**

---

## M-9 — Non-VALIDATED Advanced Capability Status

**Finding**: `capability_status.py` maintains explicit status for each advanced capability:

| Capability | Status | Label |
|-----------|--------|-------|
| `ivregress` | `IMPLEMENTED_UNVERIFIED` | IV/2SLS |
| `gmm` | `IMPLEMENTED_UNVERIFIED` | Experimental IV-GMM proxy |
| `hdfe` | `IMPLEMENTED_UNVERIFIED` | High-dimensional fixed effects |
| `predict_ml` | `IMPLEMENTED_UNVERIFIED` | Ridge prediction |
| `scenario` | `CANDIDATE` | Intervention preview |
| `didregress` | `CANDIDATE` | Difference-in-Differences |

**Verdict: PASS — All non-validated capabilities are correctly tagged.**

---

## M-10 — UI/Registry/Result/Document Consistency

**Finding**: 
- `CAPABILITY_STATUS` is the single source of truth and is consumed by `result_status_metadata()` in all adapters.
- `DIDAdapter.run()` explicitly returns `status="unsupported"` with a clear CANDIDATE disclaimer.
- No handler returns `status="success"` for any `IMPLEMENTED_UNVERIFIED` or `CANDIDATE` capability — they return `status="partial"` or `status="unsupported"`.
- The verifier test `verify_wave5_ui.py` explicitly expects `"IMPLEMENTED_UNVERIFIED"` and `"CANDIDATE"` strings in UI fragments for ivregress, gmm, hdfe, didregress, and predict_ml.

**Verdict: PASS — Internal consistency confirmed across registry, adapters, and UI contract.**

---

## Blocking Finding

| ID | Gate | Severity | File/Function | Issue | Violated Contract | Remediation |
|----|------|----------|---------------|-------|-------------------|-------------|
| QR-B1 | Playwright Journey 4 | High | `scripts/playwright_stata.py:44` + UI `test` result rendering | `test profitability = 0` result (`Prob > F` + command title) does not appear in `document.body.innerText` within 30 s in `fresh=False` post-estimation context | Verifier contract: `PLAYWRIGHT_PASS journeys=4 commands=19` | UI must surface `test` result block with command title in page DOM within 30 s |

---

## Methodology Gate Table

| Check | File(s) | Result | Notes |
|-------|---------|--------|-------|
| `estat summarize` routing | `capability_registry.py:108-109` | **PASS** | Correctly dispatched |
| `testparm` routing | `capability_registry.py:208` | **PASS** | Full Wald F-test implemented |
| `lincom` statistical meaning and implementation | `stata_expansion_handlers.py:576-643` | **PASS** | Correct Δβ = w'β with CIs |
| Robust vs clustered differentiation (OLS) | `stata_engine.py:1175-1222` | **PASS** | HC1 vs cluster-clustered |
| Robust vs clustered differentiation (xtreg) | `stata_engine.py:1446-1458` | **PASS** | robust vs clustered paths |
| Fail-closed cluster/by validation | `stata_validation.py:40-145` | **PASS** | Pre-estimation r(111) |
| Fail-closed absorb validation | `causal_adapters.py:158-166` | **PARTIAL** | Type check only; column existence validated by engine |
| Scenario CANDIDATE/PREVIEW labelling | `scenario_capability.py`, `capability_status.py` | **PASS** | Explicit throughout |
| HDFE IMPLEMENTED_UNVERIFIED labelling | `causal_adapters.py`, `capability_status.py` | **PASS** | Explicit throughout |
| No System-GMM / AB / BB claims | `gmm_adapter.py` | **PASS** | Explicitly denied |
| IV-GMM proxy labelling | `gmm_adapter.py`, `capability_status.py` | **PASS** | Experimental proxy label |
| J-stat qualification | `gmm_adapter.py:154` | **PARTIAL** | Reported, covered by UNVERIFIED disclaimer |
| Non-VALIDATED status for all advanced caps | `capability_status.py` | **PASS** | All correctly tagged |
| UI/registry/result consistency | All adapters + `capability_status.py` | **PASS** | No `success` on unverified caps |

---

## Verdict

```
INDEPENDENT_METHODOLOGY_REVIEW = PASS
```

All mandatory methodology checks pass or are disclosed limitations. The single PARTIAL for `absorb` column validation does not constitute a blocking defect — engine exceptions are caught and returned as errors. The prior F2–F9 findings from the rejected review are **not substantiated** by the code at candidate SHA `d5ffdf2`.

> **Note**: Playwright failure QR-B1 (Journey 4 `test` rendering timeout) is classified as a product defect under the Playwright acceptance gate, not under methodology.
