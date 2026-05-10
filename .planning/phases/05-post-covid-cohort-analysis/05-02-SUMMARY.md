---
phase: 05-post-covid-cohort-analysis
plan: "02"
status: complete
commit: 3ff9a46
date: 2026-05-10
---

# Summary: 05-02 — Extended tab_covid on Page 7 (Knowledge Graph)

## What Was Done

Extended `tab_covid` in `pages/7_knowledge_graph.py` (+91 lines) to show profitability comparison box plot, Welch's t-test + Mann-Whitney U for both leverage_change and profitability_change, and a plain-language interpretation expander.

## Tasks Completed

**Task 1 — `pages/7_knowledge_graph.py` tab_covid extension (+91 lines):**
- Profitability comparison box plot: pre_profitability vs post_profitability split by cohort group (Deteriorated / Improved / Entered Decline / Recovered)
- Welch's t-test (`scipy.stats.ttest_ind`) for leverage_change between Deteriorated and Improved cohorts
- Mann-Whitney U (`scipy.stats.mannwhitneyu`) for leverage_change (non-parametric)
- Same two statistical tests repeated for profitability_change
- Interpretation expander below statistical results explaining what the test results mean
- All four existing download buttons (covid_decline_firms.csv, covid_recovered_firms.csv, covid_leverage_change.png, covid_stage_migration.png) preserved

## Must-Haves Verified

- ✅ tab_covid shows profitability comparison box plot
- ✅ Welch's t-test + Mann-Whitney U shown for leverage_change
- ✅ Welch's t-test + Mann-Whitney U shown for profitability_change
- ✅ Interpretation expander present below statistical results
- ✅ All four download buttons functional (unchanged)
- ✅ 22 test_covid_cohorts.py tests pass in isolation

## Files Modified

| File | Change |
|------|--------|
| `pages/7_knowledge_graph.py` | +91 lines: profitability box plot + statistical tests + interpretation expander in tab_covid |

## Phase 5 Completion

Both plans (05-01 + 05-02) complete. Phase 5 goal achieved: COVID cohort analysis integrated into Knowledge Graph page with statistical comparisons for both leverage and profitability dimensions.
