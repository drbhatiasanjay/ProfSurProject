---
phase: 07-wave2-tier1-ux
plan: "01"
subsystem: ui
tags: [streamlit, css, error-handling, ux, spinners]

# Dependency graph
requires:
  - phase: 06-ai-financial-assistant
    provides: 18-page app fully operational on GCP Cloud Run
provides:
  - Sidebar expand arrow visible and clickable at left: 0.5rem offset
  - st.spinner() on all uncached db.* data-load calls in all 18 pages
  - try/except with st.error() + st.stop() on all db.* data-load calls
affects: [all future pages, any new page added must follow the same guard pattern]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Error guard pattern: try/except + st.error() + st.stop() wrapping every db.* data-load call"
    - "Spinner pattern: with st.spinner('Loading...') inside every try block"
    - "Excluded from st.stop() guards: db.log_page_visit, db.save_user_pref, db.load_user_prefs"

key-files:
  created: [.planning/phases/07-wave2-tier1-ux/07-01-SUMMARY.md]
  modified:
    - app.py
    - pages/1_dashboard.py
    - pages/2_peer_benchmarks.py
    - pages/3_scenarios.py
    - pages/5_data_explorer.py
    - pages/6_settings.py
    - pages/7_knowledge_graph.py
    - pages/8_econometrics.py
    - pages/9_ml_models.py
    - pages/10_forecasting.py
    - pages/11_clustering.py
    - pages/12_transitions.py
    - pages/13_advanced_econometrics.py
    - pages/15_interaction_effects.py
    - pages/16_admin_activity.py
    - pages/17_board_export.py
    - pages/18_company_navigator.py

key-decisions:
  - "Pages 4 and 14 skipped for data-load guards (only db.log_page_visit in page 4; only db.log_page_visit in page 14)"
  - "Secondary/optional db calls (get_market_index, get_available_indices, get_top_leveraged) get st.error but non-fatal (no st.stop) where data is supplemental"
  - "Cached functions (@st.cache_data) still wrapped in try/except since cache miss triggers db call"

patterns-established:
  - "Error guard pattern: try/except + st.error() + st.stop() wrapping every db.* data-load call"
  - "All new pages must include spinner + try/except for any db.* data-load"

# Metrics
duration: 35min
completed: 2026-05-07
---

# Phase 7 Plan 01: Wave 2 Tier 1 UX — Foundational Safety and CSS Summary

**CSS left offset fix for sidebar expand arrow + spinners and try/except error guards on all 18 pages' db.* data-load calls**

## Performance

- **Duration:** ~35 min
- **Started:** 2026-05-07
- **Completed:** 2026-05-07
- **Tasks:** 2
- **Files modified:** 17 (app.py + 16 page files; pages 4 and 14 had no data-load calls)

## Accomplishments

- Fixed collapsedControl CSS: added `left: 0.5rem !important` so sidebar expand arrow is always visible
- Added `with st.spinner("Loading...")` to all uncached db.* data-load calls across all 18 pages
- Added `try/except` with `st.error() + st.stop()` to all primary data-load calls across all 18 pages
- Secondary/supplemental data calls (market index, index series, top10) get non-fatal st.error without st.stop
- 344 tests pass with no regressions

## Task Commits

Each task was committed atomically:

1. **Task 1: Fix collapsedControl CSS (UX-07)** - `b01657f` (fix)
2. **Task 2: Add spinners and error guards to all 18 pages (UX-03, UX-04)** - `8f8a927` (fix)

**Plan metadata:** (docs commit to follow)

## Files Created/Modified

- `app.py` — Added `left: 0.5rem !important` to `button[data-testid="collapsedControl"]` CSS rule
- `pages/1_dashboard.py` — try/except on primary load + secondary loads (macro, indices, top10)
- `pages/2_peer_benchmarks.py` — try/except + spinner on get_companies and data load block
- `pages/3_scenarios.py` — try/except + spinner on compute_coefficients, get_companies, get_company_detail
- `pages/5_data_explorer.py` — try/except wrapped existing spinner
- `pages/6_settings.py` — try/except + spinner on get_db_metadata
- `pages/7_knowledge_graph.py` — try/except + spinner on _build_graph call
- `pages/8_econometrics.py` — try/except wrapped existing spinner on get_active_panel_data
- `pages/9_ml_models.py` — try/except + spinner on get_active_panel_data
- `pages/10_forecasting.py` — try/except + spinner on get_active_panel_data
- `pages/11_clustering.py` — try/except + spinner on get_active_panel_data
- `pages/12_transitions.py` — try/except + spinner on get_active_panel_data
- `pages/13_advanced_econometrics.py` — try/except + spinner on get_active_panel_data
- `pages/15_interaction_effects.py` — try/except + spinner on get_active_panel_data
- `pages/16_admin_activity.py` — try/except + spinner on get_audit_log
- `pages/17_board_export.py` — try/except + spinner on get_companies and _load_company_data
- `pages/18_company_navigator.py` — try/except + spinner on all four cached loaders

## Decisions Made

- Pages 4 (bulk_upload) and 14 (workbench) had no direct db.* data-load calls — only `db.log_page_visit` which is excluded per plan spec. No changes needed.
- Secondary data calls (market index overlay, T623 index series, top10 chart) use non-fatal try/except — the page can still render without these supplemental datasets.
- Cached functions wrapped in try/except because cache misses trigger db calls and must be guarded.

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- Foundational safety layer complete. All 18 pages are now resilient to DB failures.
- Ready for 07-02 (next plan in phase 7 wave 2 tier 1 UX).

---
*Phase: 07-wave2-tier1-ux*
*Completed: 2026-05-07*
