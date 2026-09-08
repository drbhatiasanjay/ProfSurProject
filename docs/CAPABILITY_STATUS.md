# Advanced Capability Status

Generated from `models/capability_status.py`. Do not edit manually.

| Command | Registry | Implementation | Execution | Numerical evidence | Methodology | Limitation |
|---|---|---|---|---|---|---|
| `ivregress` | `IMPLEMENTED_UNVERIFIED` | implemented | executable | synthetic 2SLS checks | unverified | Instrument relevance, exogeneity, and exclusion restrictions require independent validation. |
| `gmm` | `IMPLEMENTED_UNVERIFIED` | implemented | partial | limited proxy checks | unverified | Not Arellano-Bond or Blundell-Bond System GMM. |
| `hdfe` | `IMPLEMENTED_UNVERIFIED` | implemented | dependency-gated partial | synthetic coefficient checks | unverified | Sample, covariance, and absorbed-effect parity require independent validation. |
| `predict_ml` | `IMPLEMENTED_UNVERIFIED` | implemented | partial | firm-group holdout checks | unverified | No forward-time validation or hyperparameter cross-validation. |
| `scenario` | `CANDIDATE` | preview only | partial | contract and immutability checks | not validated | Not a model-based counterfactual forecast. |
| `didregress` | `CANDIDATE` | not implemented | unsupported | none | not validated | Requires treatment timing, parallel-trends checks, and a cohort-robust estimator. |

Implementation availability, executable behavior, numerical checking, and methodological validation are separate states.
