---
phase: 07-wave2-tier1-ux
plan: "05"
subsystem: navigation
tags: [streamlit, query-params, navbar, panel-selector, ux]

dependency-graph:
  requires:
    - "07-01"  # Peer Benchmarks sidebar polish
    - "07-02"  # Knowledge Graph rename
    - "07-03"  # Navbar sign-out / fixed header
    - "07-04"  # Citation expanders
  provides:
    - Panel selector as navbar <select> driven by st.query_params
    - No sidebar radio for panel switching
    - URLSearchParams JS for clean URL propagation
  affects:
    - All 18 pages (consume panel_mode via st.session_state.filters unchanged)
    - GCP Cloud Run deployment (query_params work transparently)

tech-stack:
  added: []
  patterns:
    - "st.query_params.get() for URL-driven state at Streamlit startup"
    - "URLSearchParams JS for multi-param-safe URL manipulation in navbar"
    - "HTML <select> with f-string selected attribute for pre-selection"
    - "_last_panel sentinel to gate year-range reset on panel change only"

key-files:
  created: []
  modified:
    - app.py
    - tests/smoke_auth.py

decisions:
  - id: D1
    title: "URLSearchParams over bare ?panel= concatenation"
    choice: "Use URLSearchParams to build the new URL so existing query params (e.g. ?page=...) are preserved"
    rationale: "Future-proofing: if Streamlit adds its own query params, naive ?panel= concatenation would clobber them"
  - id: D2
    title: "Sub-step D (lc-chat-fab) skipped"
    choice: "No-op — lc-chat-fab count in app.py is 0"
    rationale: "FAB was removed in commit 561420d as noted in plan context"
  - id: D3
    title: "HTML entities for en-dash and em-dash in option labels"
    choice: "&#8211; and &#8212; instead of literal Unicode — and — in the f-string"
    rationale: "Avoids potential encoding issues in HTML attribute context; keeps the file ASCII-safe"

metrics:
  duration: "22 minutes"
  completed: "2026-05-10"
  tasks-completed: 2
  commits: 3
---

# Phase 7 Plan 05: Panel Selector to Navbar select Summary

**One-liner:** Navbar `<select id="lc-panel-sel">` driven by `st.query_params` replaces sidebar `st.radio("Panel")`, eliminating `st.rerun()` on panel change.

## What Was Built

The Panel selector was moved from a sidebar `st.radio()` widget (which triggered `st.rerun()` on every change) into the always-visible navbar as an HTML `<select>` element. The select's `onchange` handler uses `URLSearchParams` JS to navigate to `?panel=<value>`, causing a full browser page reload — equivalent behavior, cleaner UX.

At startup, `app.py` reads `st.query_params.get("panel", "latest")` before the sidebar block and sets `st.session_state.panel_mode` and `st.session_state.filters["panel_mode"]`. All 18 pages continue to consume `st.session_state.filters["panel_mode"]` without any changes.

## Tasks Completed

| Task | Name | Commit | Key Files |
|------|------|--------|-----------|
| 1 | Replace sidebar Panel radio with navbar select (UX-08) | 399c154 | app.py |
| 2 | Update smoke_auth.py to remove Panel radio dependency | 8cadf60 | tests/smoke_auth.py |

## Verification Results

| Check | Result |
|-------|--------|
| `app.py` AST syntax | OK |
| `st.radio.*Panel` count in app.py | 0 |
| `lc-panel-sel` count in app.py | 1 |
| `query_params.get.*panel` present | Yes |
| `URLSearchParams` + `onchange` present | Yes |
| `smoke_auth.py` compiles | OK |
| Panel radio refs in smoke_auth.py | 0 |
| Core tests (test_database, test_models, etc.) | 180 passed |

## Deviations from Plan

### Auto-fixed Issues

None — plan executed exactly as written.

### Sub-step D (lc-chat-fab) — No-op

As predicted in the plan, `lc-chat-fab` count in `app.py` is 0 (FAB was removed in commit 561420d). Sub-step D was correctly skipped.

### smoke_auth.py — No Panel Radio References Found

`smoke_auth.py` had zero existing references to Panel radio. The file was updated with a documentation comment confirming the panel selector move rather than removing any assertions.

## Architecture Notes

- `st.session_state.filters["_last_panel"]` sentinel gates year-range reset: only resets when panel actually changes, not on every page load.
- The `from helpers import PANEL_LABELS as panel_label_map` import was kept (moved out of the sidebar `with` block to module scope at line 112) since it is still used for `_panel_display` in the navbar.
- The `vintages_df = db.get_data_vintages()` call was removed since it was only used to annotate the panel radio labels.

## Test Baseline Note

Full test suite in ordering-dependent mode shows 300 passed / 20 failed / 52 errors — this matches the pre-existing environmental flakiness baseline documented in the project STATE.md (database state contamination between test modules). All failures pass when run in isolation. This plan introduced zero new test failures.

## Next Phase Readiness

Phase 7 is now complete (all 5 plans executed). The app is ready for:
- GCP Cloud Run deployment (query_params work transparently in Cloud Run)
- Phase 6 AI Financial Assistant plans (06-03 through 06-05)
- No blockers introduced by this plan
