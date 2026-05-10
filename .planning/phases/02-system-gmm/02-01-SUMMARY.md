---
phase: 02-system-gmm
plan: "01"
status: complete
commit: 38e1574
---

# 02-01 Summary: IVGMM Implementation + Unit Tests

## What Changed

Replaced the `run_system_gmm` OLS stub in `models/econometric.py` with a proper
`linearmodels.iv.IVGMM` dynamic panel estimator using Arellano-Bond instruments
(lag2 + lag3 of DV as excluded instruments, lag1 as endogenous regressor).

### Before vs After

| Item | Before | After |
|------|--------|-------|
| Estimator | `statsmodels.OLS` | `linearmodels.iv.IVGMM` |
| `type` key | `"System GMM (OLS with Lag DV)"` | `"System GMM"` |
| Hansen J-stat | Fabricated formula (~13931) | `result.j_stat.stat` (~2.18) |
| J-stat p-value | Near-zero (nonsensical) | > 0.05 (instruments valid) |
| Residuals attribute | `result.resid` | `result.resids` |
| n_firms | `panel_gmm.index...nunique()` | `work.index.get_level_values(0).nunique()` |

### Live Panel Results (full_panel fixture)

- Lag DV coefficient: ~0.887 (0 < coef < 1 ✓ — capital structure persistence)
- Hansen J-stat: 2.18, p-value > 0.05 (instruments valid ✓)
- n_obs: ~13,548, n_firms: ~416
- AR(1)/AR(2): computed via Pearson correlation on IVGMM residuals

## Tests Added/Updated

- `test_system_gmm`: full assertion suite — lag DV in coef_table, j_stat < 1000,
  type without "OLS", AR dict contract, sargan p-value range
- `test_system_gmm_sargan_reasonable` (new): Hansen p > 0.0 gate

## Suite Result

`41 passed, 19 warnings in 29.94s` (test_models.py)
