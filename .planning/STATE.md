# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-03-28)

**Core value:** Researchers can explore leverage determinants across life stages with rigorous econometric models matching the thesis
**Current focus:** Three-panel comparison (Thesis / Latest / Run 3) — analysis pages now respect user choice

## Current Position

Phase: Maintenance + extension (post-v1.2)
Latest milestone: Methodology gaps closed (G2/G3/G4) + run3 vintage loaded + thesis pin removed
Status: Code-complete on this thread of work; G1 (true System GMM Arellano-Bond/Blundell-Bond) deferred pending explicit go-ahead
Last activity: **2026-04-25** — slider year-range now preserves user selection across panel switches

Progress: [██████████] 100% on the active scope (panel parity + methodology depth + run3 ingest)

## Recent commits (chronological)

- `8f57282` feat(panel): preserve year-range selection across panel switches
- `5a4947b` feat(analysis): respect sidebar Panel choice on every analysis page
- `a35b963` feat(panel): add Run 3 as a third sidebar option alongside Thesis / Latest
- `ae51e1c` fix(cmie_2025): rescale leverage to percent + populate lev1_100/prof100/tang100
- `b9cfc1a` feat(data): load nf400yrs2001_25.dta as vintage='run3'
- `187d842` feat(ui): wire G2 robust regression into page 8 + G3 IV/2SLS into page 13
- `fb33da6` feat(econometric): G2 robust M-estimator + G3 IV/2SLS + G4 pairwise tests

## Vintage inventory (capital_structure.db)

| Vintage | Rows | Years | Firms | Leverage units | Notes |
|---|---:|---|---:|---|---|
| `thesis` | 8,677 | 2001-2024 | 401 | percent | Frozen reproducibility panel |
| `cmie_2025` | 400 | 2025 | 400 | percent (rescaled `ae51e1c`) | DataV2 rollforward |
| `run3` | 9,031 | 2001-2025 | 400 | percent | Stata replication panel from `nf400yrs2001_25.dta` |

## Performance Metrics

**Tests:** 101 / 101 pass (was 93 before this session). Net +8 from G2/G3/G4 (3 robust + 3 IV/2SLS + 2 pairwise).

**Cloud Run revisions deployed today:** 00010 → 00011 → 00012 → 00013 (in flight)

## Accumulated Context

### Decisions

- **Run 3 is standalone** in the sidebar — does NOT union into "Latest" because its 2001-2024 rows overlap thesis vintage; unioning would double-count.
- **Analysis pages now respect sidebar Panel choice** — previous thesis-pin removed from pages 3/8/9/10/13. A yellow `🔄` banner appears on non-thesis panels reminding users that coefficients differ from published values.
- **Year-range slider preserves user selection across panel switches** — clamps to fit the new panel's bounds rather than wiping to full range.
- **Robust regression in the thesis sense = M-estimator (RLM)**, not HC1 standard errors. The `run_pooled_ols(cov_type='HC1')` already does HC1; the new `run_robust_regression(norm='HuberT')` does the outlier-downweighting interpretation that the thesis discussion implied.

### Pending Todos

- **G1 — true System GMM** (Arellano-Bond / Blundell-Bond replacing the OLS-with-lag-DV proxy at `models/econometric.py::run_system_gmm`). Deferred because the new estimator may shift chapter 5 GMM-table coefficients; needs explicit user decision on whether to revisit thesis tables.
- **CMIE Economy API service activation on `sk_pgdav`** — external blocker; technical note drafted in chat for Prof Kumar to send to CMIE. Until activation, no live API ingestion is possible (POCs at `scripts/cmie_stage1_*.py` ready to fire when unblocked).

### Blockers/Concerns

- CMIE service activation is the only external blocker. Code side is fully ready.
- G1 is the only un-closed methodology gap; everything else (G2/G3/G4 + delta-leverage + pairwise + Hausman/BP-LM + ANOVA + IV/2SLS) is shipped and tested.

## Session Continuity

Last session: 2026-04-25
Stopped at: Three-panel sidebar live on local + Streamlit Cloud + Cloud Run rev 00013; STATE.md and Obsidian updated to reflect end-of-day.
Resume file: None — clean stopping point. Next natural action is either G1 (System GMM), or wait for CMIE service activation, or move to a different feature.
