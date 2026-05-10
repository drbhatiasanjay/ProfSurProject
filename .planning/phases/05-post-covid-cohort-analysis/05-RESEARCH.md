# Phase 5: Post-COVID Cohort Analysis — Research

**Researched:** 2026-05-10
**Domain:** COVID cohort analysis integrated into Knowledge Graph (page 7)
**Confidence:** HIGH — all findings come from direct code inspection of the live codebase

---

## Summary

**The core work is largely done.** Phase 5 is primarily a hardening and test-coverage task, not a greenfield build.

`compute_covid_cohorts()` already exists in `graph_builder.py` (lines 600-699) and is already wired into `pages/7_knowledge_graph.py` as a live `tab_covid` tab (line 107). The tab renders KPI metrics, a pre→post stage migration heatmap, a box-plot for leverage change by cohort, and two drilldown tables (entered-decline and recovered firms). This covers COH-01, COH-02, and COH-03 at the UI level.

**What is missing:**
1. No unit tests for `compute_covid_cohorts()` exist anywhere in `tests/`. The function is completely untested.
2. The cohort comparison is leverage-only. COH-03 requires profitability comparison too.
3. No statistical test (t-test / Mann-Whitney U) is surfaced in the UI. The phase requires statistical tests between resilient and deteriorated cohorts.
4. No interpretation/insight box below the cohort charts (all other tabs have these).
5. The cohort DataFrame has `pre_profitability` and `post_profitability` columns already computed but they are never used in the UI.

**Primary recommendation:** Add statistical tests (scipy.stats.ttest_ind + mannwhitneyu) and profitability comparison to the existing UI, then write a full test module for `compute_covid_cohorts()`.

---

## Standard Stack

### Core (already installed, no new deps needed)

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| scipy | already in requirements | `stats.ttest_ind`, `stats.mannwhitneyu` | Already used in board_export.py, econometric.py, interaction.py, workbench.py |
| pandas | already installed | cohort DataFrame pivoting | Already used everywhere |
| plotly.express | already installed | box plots, bar charts | Already used in tab_covid |
| networkx | already installed | graph traversal in `compute_covid_cohorts` | Core dependency of graph_builder.py |

### No new packages needed.

**Installation:**
```bash
# No new installs — scipy already imported in models/board_export.py, models/econometric.py
```

---

## Architecture Patterns

### Existing Structure (tab_covid in page 7, lines 626-707)

```
pages/7_knowledge_graph.py
  tab_covid (Tab 4)
    ├── KPIs: n_total, n_deteriorated, n_improved, n_entered_decline, n_recovered
    ├── Stage migration heatmap (pre → post)
    ├── Box plot: leverage_change by Deteriorated/Improved
    ├── Table: firms entered Decline after COVID
    └── Table: firms that recovered after COVID

graph_builder.py
  compute_covid_cohorts(G, fin_df)
    ├── pre_covid_obs: year == 2019
    ├── post_covid_obs: year >= 2022 (latest available)
    └── Returns cohort_df with columns:
        company, industry, pre_stage, post_stage, pre_rank, post_rank,
        pre_leverage, post_leverage, leverage_change,
        pre_profitability, post_profitability,  ← already computed, not shown
        was_declining, entered_decline_after_covid, recovered, deteriorated, improved
```

### Pattern: Statistical Test Display (from board_export.py)

```python
# Source: models/board_export.py line 19
from scipy import stats

# Pattern used in econometric.py for significance stars (helpers.py line 82-93)
def significance_stars(p):
    if p < 0.001: return "***"
    if p < 0.01:  return "**"
    if p < 0.05:  return "*"
    if p < 0.1:   return "."
    return ""
```

### Pattern: Two-Cohort Comparison with Statistical Test

```python
from scipy import stats

det_lev = cdf[cdf["deteriorated"]]["leverage_change"].dropna()
imp_lev = cdf[cdf["improved"]]["leverage_change"].dropna()

# t-test (parametric, appropriate when n >= 30 per group)
t_stat, p_val = stats.ttest_ind(det_lev, imp_lev, equal_var=False)  # Welch's t-test

# Mann-Whitney U (non-parametric fallback for small samples / non-normal)
u_stat, p_mw = stats.mannwhitneyu(det_lev, imp_lev, alternative="two-sided")
```

### Pattern: Box Plot for Two Groups (existing in tab_covid lines 664-676)

```python
# Already correct pattern in use — extend with profitability, not replace
fig_box = px.box(bdf, x="Group", y="Leverage Change (pp)", color="Group",
                  color_discrete_map={"Deteriorated": "#EF4444", "Improved": "#22C55E"})
```

### Pattern: Interpretation Box (from helpers.py)

```python
# helpers._render_insight_box is used in peer_benchmarks, econometrics pages
# Not currently used in tab_covid — needs to be added
with st.expander("What does this mean?"):
    st.markdown(f"**{n_deteriorated} firms ({pct_det}%) deteriorated** ...")
```

### Test Pattern (from test_cfo_graph.py and test_page_integration.py)

```python
# test_cfo_graph.py uses live DB fixture — same pattern for covid cohort tests
@pytest.fixture(scope="module")
def fin_df():
    ft = db.filters_to_tuple({
        "panel_mode": "thesis",
        "company_codes": [],
        "year_range": (2001, 2024),
        ...
    })
    return db.get_graph_financials()

def test_compute_covid_cohorts_structure(G_and_fin):
    G, fin_df = G_and_fin
    result = compute_covid_cohorts(G, fin_df)
    assert "cohort_df" in result
    assert result["n_total"] > 0
```

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Two-sample significance test | Custom mean-diff logic | `scipy.stats.ttest_ind` (Welch's) | Already available, already imported elsewhere |
| Non-parametric test | Manual rank-sum | `scipy.stats.mannwhitneyu` | Handles non-normal distributions, small samples |
| Significance stars | Custom star logic | `helpers.significance_stars(p)` | Already exists in helpers.py line 82-93 |
| Download buttons | Custom CSV export | `df_download_button()` + `chart_download_button()` | Already imported in tab_covid from helpers |

---

## Common Pitfalls

### Pitfall 1: Cohort Returns "error" Key When Data Absent

**What goes wrong:** `compute_covid_cohorts()` returns `{"error": "No firms with both pre-COVID (2019) and post-COVID (2022+) data"}` when no firms have 2019 AND 2022+ observations. The UI correctly checks `if "error" in cohort_data`. Tests must mock or use real data; never assert on structure without checking for this error key first.

**How to avoid:** In tests, use the thesis panel (2001-2024) which has 2019 and 2022-2024 data. Always check `"error" not in result` before asserting on `n_total`.

### Pitfall 2: profitability_change Not in cohort_df

**What goes wrong:** `compute_covid_cohorts()` returns `pre_profitability` and `post_profitability` but NOT a pre-computed `profitability_change` column. The UI addition must compute `cdf["profitability_change"] = cdf["post_profitability"] - cdf["pre_profitability"]` before building the box-plot.

**How to avoid:** Either add `profitability_change` computation inside `compute_covid_cohorts()` (cleanest) or compute inline in the page — either works, but the function change is testable.

### Pitfall 3: Small Cohort Sizes Break scipy tests

**What goes wrong:** `mannwhitneyu` raises `ValueError` when one group has fewer than 2 observations. Deteriorated firms in some filtered subsets may be very small.

**How to avoid:** Guard the test calls:
```python
if len(det_series) >= 5 and len(imp_series) >= 5:
    t_stat, p_val = stats.ttest_ind(det_series, imp_series, equal_var=False)
```

### Pitfall 4: Pre-COVID Anchor is Fixed at 2019

**What goes wrong:** The function hard-codes `pre_covid_obs = [(y, o) for y, o in obs_list if y == 2019]`. If a company has no 2019 observation it's excluded entirely. This is correct behaviour but worth testing explicitly.

**Warning signs:** `n_total` much lower than total companies (401). Expected: ~200-300 firms have both 2019 and 2022+ observations in the thesis panel.

### Pitfall 5: `compute_covid_cohorts` Takes G + fin_df (not just fin_df)

**What goes wrong:** The function needs the full knowledge graph `G` AND `fin_df`. In tests, you must build `G` first via `build_knowledge_graph(fin_df, own_df)`. This is expensive — use `scope="module"` on the fixture.

---

## Code Examples

### Statistical Comparison Block (to add to tab_covid)

```python
# Source: pattern from models/board_export.py + models/econometric.py
from scipy import stats
from helpers import significance_stars, format_pvalue

det_lev = cdf[cdf["deteriorated"]]["leverage_change"].dropna()
imp_lev = cdf[cdf["improved"]]["leverage_change"].dropna()

if len(det_lev) >= 5 and len(imp_lev) >= 5:
    t_stat, p_ttest = stats.ttest_ind(det_lev, imp_lev, equal_var=False)
    u_stat, p_mw = stats.mannwhitneyu(det_lev, imp_lev, alternative="two-sided")
    st.markdown(
        f"**Leverage change difference** — "
        f"Welch t({len(det_lev)+len(imp_lev)-2})={t_stat:.2f}, "
        f"p={format_pvalue(p_ttest)}{significance_stars(p_ttest)} "
        f"| Mann-Whitney U={u_stat:.0f}, p={format_pvalue(p_mw)}{significance_stars(p_mw)}"
    )
```

### profitability_change Column (to add to compute_covid_cohorts)

```python
# Add inside compute_covid_cohorts() before building rows dict
rows.append({
    ...
    "profitability_change": (post_prof - pre_prof) if pre_prof is not None and post_prof is not None else None,
    ...
})
```

### Test Module Structure (new file: tests/test_covid_cohorts.py)

```python
import pytest
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
import db
from graph_builder import build_knowledge_graph, compute_covid_cohorts

@pytest.fixture(scope="module")
def G_and_fin(db_conn):
    fin_df = db.get_graph_financials()
    own_df = db.get_graph_ownership()
    G = build_knowledge_graph(fin_df, own_df)
    return G, fin_df

def test_cohort_result_structure(G_and_fin):
    G, fin_df = G_and_fin
    result = compute_covid_cohorts(G, fin_df)
    assert "error" not in result
    assert "cohort_df" in result
    assert result["n_total"] > 50  # thesis panel has enough 2019+2022 firms

def test_cohort_counts_consistency(G_and_fin):
    G, fin_df = G_and_fin
    result = compute_covid_cohorts(G, fin_df)
    cdf = result["cohort_df"]
    assert result["n_deteriorated"] == cdf["deteriorated"].sum()
    assert result["n_improved"] == cdf["improved"].sum()
    assert result["n_entered_decline"] == cdf["entered_decline_after_covid"].sum()
    assert result["n_recovered"] == cdf["recovered"].sum()

def test_leverage_change_computed(G_and_fin):
    G, fin_df = G_and_fin
    result = compute_covid_cohorts(G, fin_df)
    cdf = result["cohort_df"]
    assert "leverage_change" in cdf.columns
    assert cdf["leverage_change"].notna().sum() > 0

def test_profitability_change_computed(G_and_fin):
    # After adding profitability_change to compute_covid_cohorts
    G, fin_df = G_and_fin
    result = compute_covid_cohorts(G, fin_df)
    cdf = result["cohort_df"]
    assert "profitability_change" in cdf.columns
```

---

## State of the Art

| Old Approach | Current Approach | Status |
|--------------|------------------|--------|
| tab_covid exists with leverage-only comparison | Add profitability comparison + statistical tests | Gap to fill |
| compute_covid_cohorts() untested | Add tests/test_covid_cohorts.py | Gap to fill |
| No interpretation box in tab_covid | Add expander with data-driven insight text | Gap to fill |

---

## Open Questions

1. **profitability_change column location**
   - What we know: `pre_profitability` and `post_profitability` are returned; `profitability_change` is not
   - Recommendation: Add `profitability_change` computation inside `compute_covid_cohorts()` for testability, rather than inline in the page

2. **Statistical test choice**
   - What we know: `ttest_ind` (parametric) and `mannwhitneyu` (non-parametric) are both appropriate; the project uses `f_oneway` for ANOVA elsewhere
   - Recommendation: Show both with Welch's t-test primary, Mann-Whitney U as robustness check

3. **Cohort tab panel pinning**
   - The COVID cohorts tab uses `fin_df` from the graph build (which uses `db.get_graph_financials()` — not panel-filtered). This means it always uses the full thesis panel regardless of the sidebar Panel selector. This is probably correct for reproducibility, but worth documenting in the plan.

---

## Sources

### Primary (HIGH confidence)
- Direct code inspection: `pages/7_knowledge_graph.py` (lines 107, 626-707) — tab_covid fully implemented
- Direct code inspection: `graph_builder.py` (lines 600-699) — compute_covid_cohorts fully implemented
- Direct code inspection: `db.py` — `covid_dummy` column confirmed in `financials` table schema and all major queries
- Direct code inspection: `tests/conftest.py` — `covid_dummy` in full_panel fixture query (line 36)
- Direct code inspection: `helpers.py` — `significance_stars()` at line 82, `format_pvalue()` at line 74
- Direct code inspection: `models/board_export.py` — `from scipy import stats` pattern confirmed

### Secondary (MEDIUM confidence)
- None needed — all findings from live code

---

## Metadata

**Confidence breakdown:**
- Current state of tab_covid: HIGH — read every line of the implementation
- covid_dummy column exists: HIGH — confirmed in DB schema, conftest.py, and all major queries
- Statistical test approach: HIGH — scipy already available, patterns identical to existing codebase usage
- Gap analysis (missing profitability_change, missing tests, missing stat tests): HIGH — grep confirms no test files touch compute_covid_cohorts

**Research date:** 2026-05-10
**Valid until:** Stable — no external dependencies to change
