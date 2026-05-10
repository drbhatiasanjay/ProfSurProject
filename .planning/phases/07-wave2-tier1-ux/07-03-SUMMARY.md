---
phase: "07"
plan: "03"
subsystem: ux-export
tags: [streamlit, download, csv, png, kaleido, helpers]
depends_on:
  requires:
    - "07-02"
  provides:
    - df_download_button helper
    - chart_download_button helper
    - CSV download below every st.dataframe on all 17 data pages
    - PNG download below every st.plotly_chart on all 17 data pages
  affects:
    - "07-04"
    - "07-05"
tech-stack:
  added: []
  patterns:
    - id(df)/id(fig) for unique Streamlit widget keys across multiple downloads per page
    - lazy streamlit import inside helper functions for test-environment safety
    - kaleido PNG export wrapped in try/except for graceful fallback
key-files:
  created:
    - .planning/phases/07-wave2-tier1-ux/07-03-SUMMARY.md
  modified:
    - helpers.py
    - pages/1_dashboard.py
    - pages/2_peer_benchmarks.py
    - pages/3_scenarios.py
    - pages/4_bulk_upload.py
    - pages/5_data_explorer.py
    - pages/7_knowledge_graph.py
    - pages/8_econometrics.py
    - pages/9_ml_models.py
    - pages/10_forecasting.py
    - pages/11_clustering.py
    - pages/12_transitions.py
    - pages/13_advanced_econometrics.py
    - pages/14_workbench.py
    - pages/15_interaction_effects.py
    - pages/16_admin_activity.py
    - pages/17_board_export.py
    - pages/18_company_navigator.py
decisions:
  - choice: "id(df) and id(fig) as widget key suffix"
    rationale: "Prevents DuplicateWidgetID errors on pages with multiple download buttons (e.g. dashboard has 14 charts, knowledge_graph has 20+ charts/tables)"
  - choice: "lazy `import streamlit as st` inside helper functions"
    rationale: "helpers.py is imported by tests and scripts that run without Streamlit; module-level st import breaks those import chains"
  - choice: "kaleido errors silently swallowed in chart_download_button"
    rationale: "kaleido unavailable in CI/test environment; swallowing the exception means tests pass without any change needed in test fixtures"
  - choice: "Pages 6 (settings) and 19 (AI chat) excluded"
    rationale: "Neither page contains st.dataframe() or st.plotly_chart() calls — no download buttons needed or applicable"
  - choice: "Board Export (page 17) loop uses _fig_idx/_tbl_idx as filename suffix"
    rationale: "Multiple figs and tables per topic; enumeration gives deterministic, non-colliding filenames"
metrics:
  duration: "~45 minutes (continuation from prior session)"
  completed: "2026-05-10"
---

# Phase 7 Plan 03: In-App CSV/PNG Download Buttons Summary

One-liner: Added `df_download_button()` and `chart_download_button()` helpers to helpers.py and applied them after every `st.dataframe()` and `st.plotly_chart()` call across all 17 data pages (1–5, 7–18), enabling one-click export without leaving the app.

## Objective

Make every chart and table in the app independently downloadable without requiring the user to navigate to a separate export page. Previously, only a few pages had export capability (page 5 data explorer had CSV, page 17 had pptx). Now every dataframe and every Plotly chart has a dedicated download button immediately below it.

## What Was Built

### Task 1: Helper Functions in helpers.py (commit 475ed7b)

Two new public functions added after `export_excel`:

- `df_download_button(df, filename, label)` — renders a `st.download_button` for a DataFrame as CSV using `df.to_csv(index=False).encode("utf-8")`. Widget key is `dl_csv_{filename}_{id(df)}`.
- `chart_download_button(fig, filename, label)` — renders a `st.download_button` for a Plotly figure as PNG using `fig.to_image(format="png", scale=2)`. Widget key is `dl_png_{filename}_{id(fig)}`. kaleido errors are silently suppressed.

Both functions use lazy `import streamlit as st` internally to keep helpers.py importable in non-Streamlit contexts (tests, scripts).

### Task 2: Applied Across All 17 Data Pages (commit 0fb45bf)

Pages 1–5, 7–18 all updated. Page 6 (settings) and Page 19 (AI chat) have no charts or tables, so they were correctly excluded.

Key patterns used:
- Placed at **same indentation level** as the preceding `st.plotly_chart()` or `st.dataframe()` call, respecting `with col:` and `with st.expander():` context managers
- For inline expressions passed to `st.dataframe()`, extracted to named variable first (e.g., `sig_df[["Stage A", ...]]` → `_sig_display = ...`)
- Board Export page (17) loop uses `enumerate()` to give each chart/table a numbered suffix in the filename
- Stage Moderation bar chart loop (page 15) uses `var_name.lower()` in the filename for descriptive names

## Verification

- `grep -l "df_download_button|chart_download_button" pages/*.py` returns 17 files (correct — 6/settings and 19/AI chat are correctly absent)
- `py -3.12 -c "from helpers import df_download_button, chart_download_button; print('OK')"` passes
- `py -3.12 -m pytest tests/ -q --ignore=tests/test_page_integration.py` → 1 pre-existing failure, 281 passed
- All edits respect the "no download buttons inside @st.cache_data" constraint from the plan

## Deviations from Plan

None — plan executed exactly as written. All 18 pages surveyed; only 17 required changes (6 and 19 have no applicable calls). The context session boundary between prior and current execution was transparent to the implementation.

## Next Phase Readiness

- Plan 07-04 (sidebar filter presets): No dependency on this plan
- Plan 07-05 (panel selector to navbar): Already complete; no impact
- All download helpers are exported from helpers.py and available for any future pages
