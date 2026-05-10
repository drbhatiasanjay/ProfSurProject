# Phase 3: Stage Comparisons - Research

**Researched:** 2026-05-10
**Domain:** Econometric stage comparison regressions, side-by-side coefficient tables
**Confidence:** HIGH

## Summary

`run_stage_comparison` already exists in `models/econometric.py` (lines 509–545). It is fully
functional and is already called by page 13's Stage Comparisons tab. The function runs pooled
OLS separately on each stage subset and builds a comparison DataFrame with `Divergent` flags.

The page (`pages/13_advanced_econometrics.py`) already renders the side-by-side table, bar
chart, and citation generator. Significance stars are added inline by the page using the
`significance_stars()` helper from `helpers.py`. One unit test (`test_stage_comparison`) covers
the Growth vs Maturity pair.

Phase 3 is therefore a **hardening and coverage** phase, not a greenfield build. The tasks are:
(1) add missing unit-test coverage for the Decline vs Decay pair and for the `Divergent` logic,
(2) add a `format_stage_comparison_table()` helper that centralises star-formatting so it can be
tested in isolation, and (3) add integration smoke tests that drive the page-13 comparison logic
end-to-end.

**Primary recommendation:** Harden existing `run_stage_comparison` — add edge-case guards
(too-few-obs per individual stage), expose a formatter helper, and add targeted tests.

---

## Standard Stack

### Core (already in repo)
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| statsmodels | pinned in requirements.txt | OLS regression | Thesis replication standard |
| pandas | pinned | DataFrame manipulation | Project-wide |
| scipy | pinned | stats utilities | Used elsewhere in econometric.py |

### Helpers already available
| Function | Location | Purpose |
|----------|----------|---------|
| `significance_stars(p)` | `helpers.py:82` | Returns `***`/`**`/`*`/`.`/`` from p-value |
| `format_coef_table(coef_df)` | `helpers.py:96` | Formats a single coef_table for display |
| `DEFAULT_X_COLS` | `models/base.py:10` | 6 thesis determinants |
| `STAGE_ORDER` | `helpers.py:35` | Canonical stage ordering |

---

## Architecture Patterns

### Existing `run_stage_comparison` signature
```python
run_stage_comparison(
    df,
    stage_a: str,
    stage_b: str,
    y_col=DEFAULT_Y_COL,
    x_cols=None,
    entity="company_code",
    time="year",
    stage_col="life_stage"
) -> dict
```

### Return dict contract (consumed by page 13, lines 306–374)
```python
{
    "stage_a": str,           # e.g. "Growth"
    "stage_b": str,           # e.g. "Maturity"
    "result_a": dict,         # full run_pooled_ols result for stage_a
    "result_b": dict,         # full run_pooled_ols result for stage_b
    "comparison": DataFrame,  # Variable | {A} Coef | {A} p | {B} Coef | {B} p | Divergent
}
# On error:
{"error": str}
```

The page reads these keys directly (lines 307–309, 314, 352, 364).

### Divergent flag logic (lines 536–539)
A variable is `Divergent` when:
- Coefficients have opposite signs, OR
- Significance at 5% differs between stages

### Page 13 significance-star pattern (lines 316–320)
```python
for s in [stage_a, stage_b]:
    p_col = f"{s} p"
    if p_col in comp.columns:
        comp[f"{s} Sig"] = comp[p_col].apply(significance_stars)
        comp[p_col] = comp[p_col].apply(format_pvalue)
```
Stars are added by the PAGE, not by the model function. A new formatter helper should
replicate this pattern so it is testable without Streamlit.

### Recommended Project Structure
No structural changes needed. All additions are:
```
models/econometric.py        # add format_stage_comparison_table() helper
tests/test_models.py         # new TestStageComparisons class
tests/test_page_integration.py  # new TestPage13StageComparisons class
```

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Significance notation | Custom star logic | `helpers.significance_stars(p)` | Already exists, tested in TestHelpers |
| Coefficient formatting | Custom formatter | `helpers.format_coef_table()` | Already exists |
| Panel prep | Custom dropna/clip | `models.base.prepare_panel()` | Handles winsorizing, MultiIndex |
| Stage subsetting | Manual filter | `df[df[stage_col] == stage]` inside `run_stage_comparison` | Pattern already in place |

---

## Common Pitfalls

### Pitfall 1: Per-stage too-few-observations (not caught today)
**What goes wrong:** The current 50-obs guard is on the UNION of both stages (line 519), but
each individual stage OLS can still fail if one stage has <30 obs. Decline has 156 obs,
Decay has 176 — enough for the full panel but with sidebar filters applied these can drop below
the threshold.
**How to avoid:** Add a per-stage guard before each `run_pooled_ols` call and return
`{"error": f"Too few observations for {stage_x} ({n})"}` rather than letting linearmodels raise.
**Warning signs:** `ValueError: sample size is too small` in prod logs.

### Pitfall 2: Divergent flag false-positives on const
**What goes wrong:** The `const` row in the comparison table gets a `Divergent` flag if sign
flips, but `const` is not a determinant — it causes noisy highlights.
**How to avoid:** Exclude `const` from the `Divergent` calculation.

### Pitfall 3: Column-name collision in comparison DataFrame
**What goes wrong:** If `stage_a == stage_b` (user selects same stage twice) the column names
`{s} Coef` and `{s} p` collide. The page already guards this at the UI layer (line 290:
`if stage_a == stage_b: st.warning`), but the model itself does not raise.
**How to avoid:** Add `if stage_a == stage_b: raise ValueError(...)` at the model level.

### Pitfall 4: `full_panel` fixture includes all vintages
**What goes wrong:** `conftest.full_panel` does NOT filter by vintage — it selects all rows
from `financials`. Decline + Decay obs counts (above) are for `thesis` vintage only; the full
fixture will have more rows (good), but downstream tests that assert specific obs counts may
be fragile.
**How to avoid:** Assert `n_obs >= 100` (not exact) in stage comparison tests, consistent with
the existing `test_stage_comparison` pattern.

---

## Code Examples

### Existing test (test_models.py:105–112) — pattern to follow
```python
def test_stage_comparison(self, full_panel):
    """Growth vs Maturity comparison regression."""
    from models.econometric import run_stage_comparison
    result = run_stage_comparison(full_panel, "Growth", "Maturity")
    assert "comparison" in result
    assert "result_a" in result
    assert "result_b" in result
    assert "Divergent" in result["comparison"].columns
```

### Proposed formatter helper (new, to add to models/econometric.py)
```python
def format_stage_comparison_table(comparison_df, stage_a, stage_b):
    """
    Add significance star columns to a comparison DataFrame from run_stage_comparison.
    Returns a display-ready copy with '{stage} Sig' columns added.
    Pure function — no Streamlit dependency.
    """
    from helpers import significance_stars, format_pvalue
    out = comparison_df.copy()
    for s in [stage_a, stage_b]:
        p_col = f"{s} p"
        if p_col in out.columns:
            out[f"{s} Sig"] = out[p_col].apply(significance_stars)
            out[p_col] = out[p_col].apply(format_pvalue)
    return out
```

### Integration smoke pattern (test_page_integration.py)
```python
class TestPage13StageComparisons:
    def test_growth_vs_maturity(self, thesis_panel):
        from models.econometric import run_stage_comparison
        result = run_stage_comparison(thesis_panel, "Growth", "Maturity")
        assert "error" not in result
        assert result["result_a"]["n_obs"] >= 100
        assert result["result_b"]["n_obs"] >= 100

    def test_decline_vs_decay(self, thesis_panel):
        from models.econometric import run_stage_comparison
        result = run_stage_comparison(thesis_panel, "Decline", "Decay")
        assert "error" not in result
        assert len(result["comparison"]) >= 6  # all determinants + const
```

---

## State of the Art

| Old Approach | Current Approach | Notes |
|--------------|------------------|-------|
| No stage comparison | `run_stage_comparison` (added) | Fully shipped, just needs hardening |
| Stars added in page | Stars added in page | Move to formatter helper for testability |

---

## Open Questions

1. **Decline/Decay obs after sidebar filters**
   - What we know: 156 Decline + 176 Decay in thesis vintage unfiltered
   - What's unclear: After sidebar year_range / company_code filters, counts can drop below 50
   - Recommendation: Per-stage minimum-obs guard (30 obs) with graceful error return

2. **`const` row in Divergent column**
   - What we know: `const` gets flagged when its sign differs (e.g. positive in one stage, negative in other)
   - What's unclear: Whether thesis Table 7.5 excludes `const` from the divergent discussion
   - Recommendation: Exclude `const` from Divergent calculation in hardening pass

---

## Sources

### Primary (HIGH confidence)
- Direct code inspection: `models/econometric.py` lines 507–545
- Direct code inspection: `pages/13_advanced_econometrics.py` lines 276–374
- Direct code inspection: `tests/test_models.py` lines 105–112
- Direct code inspection: `helpers.py` lines 82–105
- Direct DB query: `financials` table observation counts by life_stage

### Secondary (MEDIUM confidence)
- `tests/conftest.py` — fixture patterns to follow for new tests
- `tests/test_page_integration.py` — integration test class structure

---

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — directly verified in codebase
- Architecture: HIGH — existing function + page contract fully read
- Pitfalls: HIGH — identified from direct code inspection; obs counts verified via DB query
- Data counts: HIGH — queried live DB (thesis vintage)

**Research date:** 2026-05-10
**Valid until:** 2026-06-10 (stable codebase area)
