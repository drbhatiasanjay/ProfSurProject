# Comprehensive Stata Command Test Plan

This document provides an exhaustive list of all Stata commands supported by the ProfSur engine, along with a specific negative test scenario designed to verify correct error handling, boundary validation, and architectural robustness. 

## 1. Core Econometric Estimators

| Command | Description | Negative Test Case Scenario | Expected Error Code / Handling |
|---------|-------------|-----------------------------|--------------------------------|
| `regress` / `reg` | Pooled OLS Regression | `regress leverage prof profit_margin` (where `prof` and `profit_margin` are perfectly collinear) | `COLLINEARITY` / `SINGULAR_MATRIX` |
| `xtreg` | Panel Regression (FE/RE) | `xtreg leverage prof, fe` without defining a panel (or deleting `company_code` from dataset) | `PANEL_NOT_DECLARED` |
| `ivregress` | Instrumental Variables | `ivregress 2sls leverage (prof = ) size` (empty instruments block) | `INVALID_INSTRUMENT_SPEC` / `SYNTAX_ERROR` |
| `hdfe` | High-Dimensional FE | `hdfe leverage prof, absorb(non_existent_var)` | `VARIABLE_NOT_FOUND` |
| `gmm` | Generalized Method of Moments | `gmm leverage prof tang, lags(1 30)` | `INVALID_INSTRUMENT_SPEC` (Must block instrument proliferation $N_{instr} > N_{firms}$) |
| `didregress` | Difference-in-Differences | `didregress leverage prof` | `UNSUPPORTED_CAPABILITY` (Placeholder; must strictly reject execution until benchmarked) |

## 2. Descriptive & Statistical Summaries

| Command | Description | Negative Test Case Scenario | Expected Error Code / Handling |
|---------|-------------|-----------------------------|--------------------------------|
| `summarize` / `sum` | Summary Statistics | `summarize string_column_name, detail` | Graceful failure or skip non-numeric without crashing |
| `tabstat` | Group Tabulations | `tabstat leverage, by(continuous_variable)` | `INVALID_TIME_VARIABLE` or Too many groups handled cleanly |
| `tabulate` / `tab` | Frequency Tables | `tabulate very_high_cardinality_var` | Should truncate output or warn `UNSUPPORTED_OPTION` |
| `pwcorr` / `corr` | Correlation Matrix | `pwcorr single_variable, star(0.05)` | `INSUFFICIENT_VARIATION` / Handle elegantly |

## 3. Post-Estimation & Diagnostics

| Command | Description | Negative Test Case Scenario | Expected Error Code / Handling |
|---------|-------------|-----------------------------|--------------------------------|
| `hausman` | Specification Test | `hausman fe re` without estimating `fe` and `re` first | `NO_ACTIVE_ESTIMATION` |
| `estat vif` | Variance Inflation Factor | `estat vif` after running an estimator that does not support VIF (e.g. `gmm`) | `METHOD_NOT_PERMITTED` / `NO_ACTIVE_ESTIMATION` |
| `estimates store` | Store Model Results | `estimates store m1` without any prior regression run | `NO_ACTIVE_ESTIMATION` |
| `esttab` | Side-by-Side Tables | `esttab m1 m2` referencing models that do not exist | `NO_ACTIVE_ESTIMATION` / `VARIABLE_NOT_FOUND` |
| `xttest0` | Breusch-Pagan LM Test | `xttest0` run immediately after `xtreg, fe` (only valid for RE) | `DIAGNOSTIC_FAILURE` / `METHOD_NOT_PERMITTED` |
| `xtserial` | Wooldridge Test | `xtserial` with less than 3 time periods per panel | `INSUFFICIENT_OBSERVATIONS` / `INVALID_TIME_VARIABLE` |
| `test` | Wald Test | `test prof = size` after a model that did not include `size` | `VARIABLE_NOT_FOUND` |
| `predict` | Fitted Values / Residuals | `predict res, resid` without a prior estimated model | `NO_ACTIVE_ESTIMATION` |

## 4. Visualization & Plotting

| Command | Description | Negative Test Case Scenario | Expected Error Code / Handling |
|---------|-------------|-----------------------------|--------------------------------|
| `scatter` / `twoway` | Scatter Plots | `scatter leverage prof tang size` (Too many axes/dimensions) | `UNSUPPORTED_OPTION` / `SYNTAX_ERROR` |
| `histogram` / `hist` | Histograms | `histogram company_code` (Plotting an ID column) | Graceful handling / warn `DATA_SCOPE_ERROR` |
| `graph box` / `hbox`| Box Plots | `graph box leverage, over(continuous_var)` | `UNSUPPORTED_OPTION` / Cap on groups |
| `coefplot` | Coefficient Plots | `coefplot` without prior regression | `NO_ACTIVE_ESTIMATION` |
| `margins` / `plot` | Marginal Effects | `margins` on a linear model without factor interactions | `METHOD_NOT_PERMITTED` / Skip |

## 5. Machine Learning, Simulation & Utilities

| Command | Description | Negative Test Case Scenario | Expected Error Code / Handling |
|---------|-------------|-----------------------------|--------------------------------|
| `predict_ml` | Random Forest / XGBoost | `predict_ml` with `scikit-learn` intentionally uninstalled | `DEPENDENCY_UNAVAILABLE` (Must not crash the server) |
| `scenario` | CFO Stress Testing | `scenario leverage prof` with conflicting inline and `interventions()` arguments | `SYNTAX_ERROR` |
| `winsor2` | Winsorization | `winsor2 leverage, cuts(5 95)` (Missing dependency or valid parsing) | Handled correctly as dataset modification |
| `export` | Native Stata Export | `export dta using /root/protected.dta` (Path traversal / permission denied) | `EXPORT_FAILURE` / `DATA_SCOPE_ERROR` |
| `xtset` | Panel Declaration | `xtset year company_code` (Reversing the expected order) | `INVALID_TIME_VARIABLE` / `DUPLICATE_PANEL_KEYS` |

## Execution Plan
To test these, we will build a `comprehensive_negative_test_harness.py` that loops through this exact array, executing each command against the backend `_route` or `execute_stata_command` API, and validating that the exact `ANALYTICAL_ERROR_CODES` or safe fail-states are thrown without leaking stack traces or hanging the Streamlit interface.
