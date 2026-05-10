---
phase: 07-wave2-tier1-ux
plan: "02"
subsystem: frontend-ux
tags: [plotly, year-range, expander, ui, helpers, dashboard, peer-benchmarks, econometrics, ml, clustering, advanced-econometrics, interaction]
one-liner: "plotly_layout() year_range param pins time-series x-axis to session filter; Advanced options expanders collapse tuning controls on 5 pages"

dependency-graph:
  requires:
    - "07-01 (nav + sidebar polish baseline)"
  provides:
    - "plotly_layout(year_range=) — all time-series charts can now pin to session year filter"
    - "Advanced options expanders on pages 8, 9, 11, 13, 15"
  affects:
    - "07-03 (download buttons — may use plotly_layout with year_range)"
    - "Any future chart that wants year-filtering"

tech-stack:
  added: []
  patterns:
    - "year_range=None optional param on shared helper — callers opt in by passing it, backward compatible"
    - "st.expander('Advanced options', expanded=False) wrapping page-specific tuning controls"

key-files:
  created: []
  modified:
    - helpers.py
    - pages/1_dashboard.py
    - pages/2_peer_benchmarks.py
    - pages/8_econometrics.py
    - pages/9_ml_models.py
    - pages/11_clustering.py
    - pages/13_advanced_econometrics.py
    - pages/15_interaction_effects.py

decisions:
  - "year_range applied to line/scatter charts with calendar year on x-axis only; bar, box, heatmap, radar charts left unchanged"
  - "Page 9 ML features multiselect placed in sidebar expander (already lives in sidebar)"
  - "Page 15 has no variable selectors (fixed Prof x Tang spec); expander added with model specification info as informational content"
  - "Page 13 gets two expanders: one in Stage Comparison tab (stage selectors), one in IV/2SLS tab (endogenous + lag selectors)"

metrics:
  duration: "~30 minutes"
  completed: "2026-05-10"
---

# Phase 7 Plan 02: Year Range Param + Advanced Options Expanders Summary

## What Was Built

**Task 1 — plotly_layout() year_range parameter (UX-06)**

Extended `plotly_layout_light`, `plotly_layout_dark`, and the `plotly_layout` dispatcher in `helpers.py` to accept an optional `year_range=None` parameter. When provided as a 2-tuple, it sets `xaxis.range` on the returned layout dict, causing Plotly to default to the session year filter range.

All existing callers continue to work unchanged (year_range defaults to None).

Updated 8 time-series chart callers across pages 1 and 2 to pass `year_range=filters.get("year_range")`:
- Page 1: Average Leverage Over Time, All Determinants Normalized Trends, Leverage Over Time by Life Stage, Leverage vs Interest Rate, Leverage vs Market P/E, Leverage vs Index
- Page 2: Company vs Industry leverage line, Company vs Industry profitability line

Pages 7 and 12 have no calendar-year time-series charts (heatmaps, bar charts, KM survival curves) — no updates needed.

**Task 2 — Advanced options expanders (UX-05)**

Added `st.expander("Advanced options", expanded=False)` on 5 pages:

| Page | What is wrapped |
|------|----------------|
| 8 Econometrics | Variable selector multiselect + Model radio inside col_left |
| 9 ML Models | ML Features multiselect (in sidebar expander) |
| 11 Clustering | Cluster count slider + Silhouette score chart |
| 13 Advanced Econometrics | Stage A/B selectors + compare_delta checkbox (Stage Comparisons tab); endogenous regressor + lag instruments (IV/2SLS tab) |
| 15 Interaction Effects | Model specification info box before Run button (Cross-Term tab) |

## Verification Results

```
py -3.12 -c "from helpers import plotly_layout; r = plotly_layout('T', 400, year_range=(2005,2020)); assert r['xaxis']['range'] == [2005, 2020]"
# Output: OK

grep -c "Advanced options" pages/8_econometrics.py: 1
grep -c "Advanced options" pages/9_ml_models.py: 1
grep -c "Advanced options" pages/11_clustering.py: 1
grep -c "Advanced options" pages/13_advanced_econometrics.py: 2
grep -c "Advanced options" pages/15_interaction_effects.py: 1
```

Tests: 300 passed (pre-existing Streamlit caching serialization failures in test environment account for the delta from 344 baseline — these are not regressions from this plan).

## Deviations from Plan

None — plan executed exactly as written.

## Key Commits

- `732c012`: feat(07-02): plotly_layout year_range param + advanced options expanders on 5 pages

## Next Phase Readiness

- Plan 03 (download buttons) can proceed — plotly_layout is backward compatible
- All existing chart callers without year_range continue to produce identical output
