---
phase: 01-delta-leverage-diagnostics
plan: "02"
status: complete
commit: b97ea43
---

# 01-02 Summary: Harden Phase 1 Unit Test Assertions

## Assertion Counts (before → after)

| Test | Before | After | Key additions |
|------|--------|-------|---------------|
| test_breusch_pagan_lm | 4 | 9 | f_stat/f_pvalue keys, lm_pvalue range [0,1], f_pvalue range, exact verdict string |
| test_delta_leverage_ols | 2 | 7 | coef_table len, r_squared key, n_obs>0, n_obs < baseline (first-diff proof), n_obs>3000 |
| test_delta_leverage_all | 3 | 11 | hausman sub-dict contract, chi2≥0, p_value range, result.recommended == hausman.recommended, FE n_obs == RE n_obs |
| test_delta_leverage_by_stage | 3 | 9 | ok/error partition, coef_table+n_obs+r_squared on every ok stage, 'Too few observations' substring on every error stage, diagnostic print |

## Live Panel Results

**BP-LM verdict on `panel_thesis_v` fixture:** `"Panel effects detected (reject Pooled OLS at 5% level)"`
— matched one of the two pinned strings (TST-01 ✓)

**`result['recommended'] == hausman['recommended']`:** Confirmed on live panel (DLV-02 ✓)

**Stage-specific results:**
```
ok_stages=['Shakeout2', 'Maturity', 'Growth', 'Shakeout3', 'Startup', 'Decline', 'Decay', 'Shakeout1']
error_stages=[]
```

**Shakeout1 note:** RESEARCH.md estimated ~31 raw obs → <30 after first-differencing. Live panel (includes cmie_2025 through 2025) has sufficient observations for Shakeout1 to succeed. The conditional lock was removed. The 'Too few observations' error-path contract is still present via the `errors` partition loop — it just fires zero times on this fixture.

## Test Suite Result

```
40 passed, 19 warnings in 32.94s
```

## Scope Verification

`git diff --name-only` after Plan 01-02 edits:
```
tests/test_models.py
```
Zero changes to `models/` or `pages/`.

## Deviations from Plan

- Shakeout1 conditional lock removed: the lock asserted `"error" in results["Shakeout1"]` but Shakeout1 succeeds on the actual database (all 8 stages run). Lock was fixture-incorrect — removing it is the correct response per the plan's own "fixture-robust" intent.
