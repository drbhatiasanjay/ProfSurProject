# Pilot 2 statistical and UI probe extract

## Attribution

- Source artifacts: `statistical_probe_results.json`, `06_TARGETED_TEST_EVIDENCE.md`
- Local provenance: `C:\Users\hemas\Downloads\kaif-pilot-output\statistical_probe_results.json`
- Reviewed ProfSur commit recorded by the audit: `fa97df7e1e6b43726c63590a47906d8ae8e5797d`
- Method: AST extraction of selected original functions from `models/stata_engine.py` and the Stata Studio UI expression, with synthetic pandas data and stubbed state/chart helpers.

## Reproduced behaviors

| Probe identifier | Observed result | Interpretation boundary |
|---|---|---|
| `missing_dependent` | `regress absent profitability` succeeded using `leverage` as the actual dependent variable. | Direct evidence for this probed resolver path only. |
| `missing_predictor` | `regress leverage absent` succeeded using default predictors. | Direct evidence for this probed resolver path only. |
| `unknown_covariance` | Invalid `vce(garbage)` returned success with `HC1`. | Direct evidence for this parser/handler path only. |
| `cluster_ignored` | `cluster(company_code)` returned `nonrobust`. | Direct evidence for this probed route only. |
| `missing_group` | `tabstat leverage, by(absent)` used `life_stage`. | Direct evidence for this fallback path only. |
| `insignificant_interpretation` | Inputs with p-values 0.8 and 0.9 still produced significance and theory claims. | Direct evidence for the generated-inference path under the synthetic inputs. |
| `fe_cluster_year` | Requested year clustering returned a company-cluster note and no time effects. | Direct evidence for this FE option path only. |
| `fe_absorb_both` | `absorb(company_code year)` returned `time_effects=false`. | Direct evidence for this option path only. |
| `fe_missing_dep` | `xtreg absent profitability, fe` displayed `absent` while modeling `leverage`. | Direct evidence for this resolver/display path only. |
| `ui_error_badge` | An input error mapped to output status `success` in the isolated UI expression. | Expression-level evidence; no browser execution. |

## Numerical control

`valid_ols` matched the independent NumPy least-squares reference within `8.881784197001252e-16`; this supports the arithmetic for that synthetic fixture only and does not offset the specification or interpretation findings.

## Limitation

This extract does not claim that every route has these defects. It does not establish runtime frequency, user impact, or root causes beyond the inspected source paths.
