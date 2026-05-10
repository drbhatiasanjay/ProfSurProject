---
phase: 09-company-timeline-view
plan: 01
subsystem: ui
tags: [plotly, dual-axis, company-navigator, life-stage, leverage, timeline, streamlit]

# Dependency graph
requires:
  - phase: 07-wave2-tier1-ux
    provides: chart_download_button, PLOTLY_CONFIG, plotly_layout in helpers.py
  - phase: 06-ai-financial-assistant
    provides: page 19 AI assistant (shares page 18 company context via active_company_cin)
provides:
  - Timeline view in page 18 Company Navigator showing year-by-year life-stage trajectory
  - Dual-axis Plotly chart (STAGE_COLORS bars + leverage line on secondary y-axis)
  - Stage Transitions expander showing lifecycle change events
affects: [future board-export enhancements, page 17 company subject pages]

# Tech tracking
tech-stack:
  added: [plotly.subplots.make_subplots (already in deps), plotly.graph_objects (top-level import)]
  patterns:
    - make_subplots(specs=[[{"secondary_y": True}]]) for dual-axis Plotly in Streamlit
    - STAGE_RANK ordinal mapping for y-axis tick labels in bar charts

key-files:
  created: []
  modified: [pages/18_company_navigator.py]

key-decisions:
  - "Timeline branch sits inside with col_graph: at same indent as other elif blocks — detail panel shows info message when Timeline active, which is acceptable"
  - "Year slider hidden for Timeline (not year-specific; shows full history)"
  - "import plotly.graph_objects as go moved from inline (line ~331) to top-level imports"

patterns-established:
  - "Dual-axis Plotly pattern: make_subplots(specs=[[{'secondary_y': True}]]) then secondary_y=False/True on each add_trace"
  - "Stage bar chart pattern: STAGE_RANK for ordinal y, STAGE_COLORS for marker_color, STAGE_ORDER keys for tick labels"

# Metrics
duration: 8min
completed: 2026-05-10
---

# Phase 09 Plan 01: Company Timeline View Summary

**Dual-axis Plotly timeline added to page 18 Company Navigator — color-coded life-stage bars (STAGE_COLORS) on left y-axis, leverage ratio line on right y-axis, with Stage Transitions expander**

## Performance

- **Duration:** 8 min
- **Started:** 2026-05-10T10:21:22Z
- **Completed:** 2026-05-10T10:28:58Z
- **Tasks:** 2 completed
- **Files modified:** 1

## Accomplishments

- "Timeline" added as 4th option in View radio (Ego Graph / Peer Cluster / Stage Map / Timeline)
- Dual-axis Plotly figure using make_subplots(secondary_y=True): color-coded stage bars on left, leverage line on right
- Stage Transitions expander surfaces lifecycle change events (year + From + To columns)
- Year slider correctly hidden when Timeline is selected (not year-specific)
- Top-level go import moved from inline local import to module level; STAGE_RANK added to helpers import

## Task Commits

Each task was committed atomically:

1. **Tasks 1+2: Add Timeline radio option + implement dual-axis Timeline branch** - `3e8de67` (feat)

**Plan metadata:** (pending docs commit)

## Files Created/Modified

- `pages/18_company_navigator.py` - Added Timeline to View radio options list + index guard, updated year slider gate condition, moved go import to top-level, added STAGE_RANK to helpers import, added elif view_mode == "Timeline": branch with make_subplots dual-axis chart and Stage Transitions expander

## Decisions Made

- `import plotly.graph_objects as go` was an inline local import at line ~331; moved to top-level module imports to avoid duplication with the new Timeline branch usage.
- Timeline branch leaves `detail_node_id` and `G_active` as None — the right-hand detail panel shows "Select a node below the graph" info message when Timeline is active, which is acceptable behavior since Timeline is a standalone chart view.
- Year slider hidden for Timeline since the Timeline shows the full history on the x-axis; a year filter would be redundant.

## Deviations from Plan

None — plan executed exactly as written. The one minor discovery (local `go` import at line ~331) was anticipated in the plan's Task 2 notes and handled as a cleanup.

## Issues Encountered

- AST parse command failed with cp1252 encoding error on Windows when reading the file without explicit encoding. Fixed by passing `encoding='utf-8'` — py_compile (the authoritative check) passed cleanly. Not a code issue.

## User Setup Required

None — no external service configuration required. Change is a pure UI addition to an existing page.

## Next Phase Readiness

- Timeline view is live and functional for all 401 Indian firms with thesis panel data
- Edge case (US comparators with no life_stage data) handled gracefully with st.info()
- Ready for any follow-on enhancements (e.g., adding profitability as a third trace, or exporting timeline as part of board deck page 17)

---
*Phase: 09-company-timeline-view*
*Completed: 2026-05-10*
