---
phase: 03-stage-comparisons
plan: "01"
status: complete
commit: 03edbf9
date: 2026-05-10
---

# Summary: 03-01 — Stage Comparison Functions + Tests

## What Was Done

Hardened `run_stage_comparison` in `models/econometric.py` and added `format_stage_comparison_table` helper. Added 6 unit tests + 2 page-13 integration smoke tests covering CMP-01/02/03.

## Tasks Completed

**Task 1 — Harden `run_stage_comparison` (models/econometric.py):**
- Per-stage n<30 guard (checks each stage independently, not the union)
- Same-stage guard: `stage_a == stage_b` returns `{"error": "..."}` immediately
- `const` row excluded from Divergent flag calculation via `not_const` mask

**Task 2 — New `format_stage_comparison_table` helper (models/econometric.py):**
- Pure function (no Streamlit import)
- Adds `{stage} Sig` star columns and formats p-values as strings
- Used by page 13 for display-ready output

**Task 3 — Unit tests (`tests/test_models.py` — `TestStageComparisons`, 6 tests):**
- `test_growth_vs_maturity_structure` — dict keys + comparison columns (CMP-01/03)
- `test_growth_vs_maturity_separate_coefs` — independent OLS coefficients
- `test_decline_vs_decay_structure` — valid dict on full thesis panel (CMP-02)
- `test_divergent_flag_excludes_const` — const row never Divergent (CMP-03)
- `test_same_stage_returns_error` — same-stage guard
- `test_format_stage_comparison_table` — Sig columns + formatted p-values

**Task 4 — Integration smoke (`tests/test_page_integration.py` — `TestPage13StageComparisons`, 2 tests):**
- `test_growth_vs_maturity_e2e` — end-to-end on full thesis panel (CMP-01)
- `test_decline_vs_decay_e2e` — Decline vs Decay distinct coefficient sets (CMP-02)

## Must-Haves Verified

- ✅ `run_stage_comparison("Growth", "Maturity")` returns `{stage_a, stage_b, result_a, result_b, comparison}`
- ✅ `run_stage_comparison("Decline", "Decay")` valid on thesis panel (n>=30 per stage)
- ✅ `comparison` DataFrame has `Variable, {A} Coef, {A} p, {B} Coef, {B} p, Divergent`
- ✅ `const` row excluded from Divergent
- ✅ `format_stage_comparison_table()` adds `{stage} Sig` columns, no st import
- ✅ Same-stage call returns `{"error": str}` not a crash
- ✅ All 6 unit tests + 2 integration smoke tests pass

## Files Modified

| File | Change |
|------|--------|
| `models/econometric.py` | +42 lines: per-stage guards, const exclusion, format_stage_comparison_table |
| `tests/test_models.py` | +63 lines: TestStageComparisons (6 tests) |
| `tests/test_page_integration.py` | +24 lines: TestPage13StageComparisons (2 tests) |
