---
phase: 05-post-covid-cohort-analysis
plan: "01"
status: complete
commit: 3ff9a46
date: 2026-05-10
---

# Summary: 05-01 — compute_covid_cohorts profitability_change + Test Module

## What Was Done

Added `profitability_change` column to `compute_covid_cohorts()` in `graph_builder.py` and created `tests/test_covid_cohorts.py` with 22 unit tests covering COH-01/02/03.

## Tasks Completed

**Task 1 — `graph_builder.py` (+1 line in compute_covid_cohorts):**
- Added `profitability_change = post_prof - pre_prof` in the `rows.append()` dict
- `post_prof` = mean profitability in FY2022–2024; `pre_prof` = mean profitability in FY2018–2019
- Return dict now has both `leverage_change` and `profitability_change` columns

**Task 2 — `tests/test_covid_cohorts.py` (189 lines, 22 tests):**
- `TestCohortStructure` (4 tests): required keys, n_total reasonable, required columns
- `TestCohortCountConsistency` (6 tests): n_deteriorated/n_improved/n_entered_decline/n_recovered match df, pct values in range
- `TestPostCovidDeclineCohort` (3 tests): entered_decline_after_covid column, pre-COVID not in Decline, post-COVID in Decline
- `TestCovidResilienceTracker` (3 tests): mutually exclusive cohorts, recovered firms pre/post COVID stage
- `TestCohortMetricColumns` (6 tests): leverage_change/profitability_change have values and are numeric, scipy ttest + Mann-Whitney U run without error

## Must-Haves Verified

- ✅ `compute_covid_cohorts()` returns `profitability_change` column in `cohort_df`
- ✅ All 22 tests pass in isolation (`py -3.12 -m pytest tests/test_covid_cohorts.py -v` → 22 passed)
- ✅ Existing tests unaffected (1-line addition to graph_builder.py)

## Files Modified

| File | Change |
|------|--------|
| `graph_builder.py` | +1 line: profitability_change in compute_covid_cohorts rows.append() |
| `tests/test_covid_cohorts.py` | Created: 189 lines, 22 tests across 5 test classes |
