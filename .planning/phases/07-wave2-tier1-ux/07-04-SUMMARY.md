---
phase: 07-wave2-tier1-ux
plan: 04
subsystem: ui
tags: [streamlit, citation, apa, latex, econometrics, scenarios]

# Dependency graph
requires:
  - phase: 07-wave2-tier1-ux
    provides: Pages 3, 8, 13 regression result displays
provides:
  - APA + LaTeX citation expanders on page 3 (Scenarios)
  - APA + LaTeX citation expanders on page 8 (Econometrics)
  - Three APA + LaTeX citation expanders on page 13 (System GMM, Delta-Leverage, Stage Comparisons)
affects: [future-phases]

# Tech tracking
tech-stack:
  added: []
  patterns: [st.expander with st.code blocks for copy-paste citation output]

key-files:
  created: []
  modified:
    - pages/3_scenarios.py
    - pages/8_econometrics.py
    - pages/13_advanced_econometrics.py

key-decisions:
  - "Page 13 gets three expanders (one per tab result type) because each model produces a distinct citable result"
  - "Variables adapted to actual in-scope names rather than plan pseudocode names"
  - "Unicode em-dash used in APA text; double hyphen in LaTeX per convention"

patterns-established:
  - "Citation expander pattern: st.expander('Cite this result') with APA + LaTeX st.code blocks"
  - "Dynamic citation text built from live result variables (r_squared, n_obs, n_firms, year_range)"

# Metrics
duration: 15min
completed: 2026-05-10
---

# Phase 7 Plan 04: Citation Generator Summary

**APA + LaTeX 'Cite this result' expanders added to pages 3, 8, and 13 — dynamically populated from live regression results (model type, panel, year range, N firms, obs, R²)**

## Performance

- **Duration:** ~15 min
- **Started:** 2026-05-10T00:00:00Z
- **Completed:** 2026-05-10T00:15:00Z
- **Tasks:** 3 code tasks + verify + commit
- **Files modified:** 3

## Accomplishments
- Page 8 (Econometrics): citation expander inserted after coefficient table, before coefficient plot — pulls model type, N firms, obs, R² from `best` dict
- Page 13 (Advanced Econometrics): three expanders — System GMM tab (after coefficient table), Delta-Leverage Full Panel tab (after recommended model coefficients), Stage Comparisons tab (after side-by-side table)
- Page 3 (Scenarios): citation expander inside `with res_left:` block after OLS equation display — includes predicted leverage value in APA text
- All expanders render two copy-ready blocks: APA-7 format and LaTeX `\cite{}` format

## Task Commits

Each task was committed atomically:

1. **Tasks 1-3: citation expanders on pages 3, 8, 13** — `851a73a` (feat)

**Plan metadata:** (docs commit follows)

## Files Created/Modified
- `pages/3_scenarios.py` — Citation expander after OLS equation inside `with res_left:` block
- `pages/8_econometrics.py` — Citation expander after `st.dataframe(display_coefs, ...)` before coefficient plot
- `pages/13_advanced_econometrics.py` — Three citation expanders: System GMM, Delta-Leverage, Stage Comparisons tabs

## Decisions Made
- Page 13 gets three separate expanders rather than one, because GMM, Delta-Leverage, and Stage Comparisons are distinct result types with different model names and statistics
- Stage Comparisons citation captures both R² values (stage_a and stage_b) since there is no single R² for the comparison
- LaTeX f-string format uses `$R^2_{{{stage}}}$` double-brace escaping for literal `{` in f-strings

## Deviations from Plan

None — plan executed exactly as written. Variable names in scope matched plan pseudocode (`best`, `_panel`, `filters`, `coefs`, `predicted`).

## Issues Encountered

- Initial `ast.parse` syntax check failed with cp1252 encoding error on Windows — resolved by adding `encoding='utf-8'` to the check command. Files were UTF-8 throughout; no file changes needed.

## User Setup Required
None — no external service configuration required.

## Next Phase Readiness
- Citation blocks are live on pages 3, 8, 13
- Pattern established for any future result page that needs citability
- Tests: 300 passed (pre-existing 20 failures and 52 errors are unrelated to citation changes)

---
*Phase: 07-wave2-tier1-ux*
*Completed: 2026-05-10*
