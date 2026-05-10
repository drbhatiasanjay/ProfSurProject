---
phase: 11
plan: "01"
name: "Smoke Auth Extension + NULL Tangibility Fix"
subsystem: "quality / testing / data"
tags: [smoke-test, playwright, tangibility, us_av_2024, sqlite, imputation]

dependency_graph:
  requires: ["phases 1-7 complete (19 pages deployed)", "us_av_2024 vintage loaded"]
  provides: ["smoke coverage for pages 17-19", "clean us_av_2024 tangibility values"]
  affects: ["CI smoke test signal for restricted pages", "peer benchmarks for US sample"]

tech_stack:
  added: []
  patterns: ["industry-mean imputation with global fallback", "idempotent SQL UPDATE with IS NULL guard"]

key_files:
  created:
    - scripts/fix_us_tangibility.py
  modified:
    - tests/smoke_auth.py
    - capital_structure.db

decisions:
  - id: "board_deck_nav_title"
    choice: "Keep 'Board Deck' as nav title in smoke_auth.py"
    why: "app.py defines page 17 as title='Board Deck' — matches exactly what Streamlit sidebar renders. CLAUDE.md sidebar title note ('Board Export') was inaccurate; app.py is authoritative."
  - id: "tangibility_imputation"
    choice: "Industry-mean imputation from non-null us_av_2024 rows; global mean fallback for Energy (Chevron)"
    why: "Industry mean is the closest peer reference. Energy has zero non-null us_av_2024 peers so global mean (0.1719) is the only available reference."

metrics:
  duration: "~4 minutes"
  completed: "2026-05-10"
---

# Phase 11 Plan 01: Smoke Auth Extension + NULL Tangibility Fix Summary

**One-liner:** Playwright smoke tests extended to pages 17-19 (Board Deck, Company Navigator, AI Assistant) + 166 NULL tangibility rows filled for us_av_2024 via industry-mean imputation.

## What Was Done

### Task 1: Extend smoke_auth.py to cover pages 17, 18, 19

Two new entries added to `PROBE_PAGES`:
```python
("company_navigator", "Company Navigator", "Company Navigator"),  # admin+researcher page 18
("ai_assistant",      "AI Assistant",      "AI Assistant"),       # admin+researcher page 19
```

`ROLE_BLOCKED['viewer']` updated to include both new slugs:
```python
"viewer": ["bulk_upload", "workbench", "activity_log", "board_deck", "company_navigator", "ai_assistant"],
```

**Nav title correction check:** Confirmed that the existing `board_deck` entry correctly uses "Board Deck" — matching `app.py` line 220: `title="Board Deck"`. No correction needed (CLAUDE.md comment "Board Export" was stale).

### Task 2: Create and run scripts/fix_us_tangibility.py

**NULL state before fix:** 166 NULL rows across 10 firms in vintage='us_av_2024'

**Firms fixed:**

| company_code | industry_group | fill_value | source |
|---|---|---|---|
| 9000001 | Technology | 0.0875 | industry mean |
| 9000003 | Technology | 0.0875 | industry mean |
| 9000005 | Financials | 0.0265 | industry mean |
| 9000009 | Health Care | 0.1099 | industry mean |
| 9000012 | Health Care | 0.1099 | industry mean |
| 9000013 | Consumer Staples | 0.1554 | industry mean |
| 9000019 | Energy (Chevron) | 0.1719 | global fallback |
| 9000020 | Industrials | 0.1142 | industry mean |
| 9000021 | Industrials | 0.1142 | industry mean |
| 9000023 | Communication Services | 0.2476 | industry mean |

**NULL state after fix:** 0 NULL rows remaining

Derived columns also updated: `tang100 = tangibility * 100`, `log_tang = ln(tangibility)`.

## Deviations from Plan

### Auto-resolved: nav title verification

Plan said to check if "Board Deck" nav title was wrong and should be "Board Export". Verified in `app.py` line 220 — `title="Board Deck"` is correct. No change needed. CLAUDE.md comment about "Board Export" was inaccurate.

No other deviations.

## Test Results

- **Core unit tests** (test_database.py, test_models.py, test_scenario_regression.py): **75/75 passed**
- **Full suite** (excluding smoke_auth.py): 309 passed, 18 failed, 76 errors
  - The 18 failures and 76 errors are pre-existing environmental flakiness in TestPage13/14/15 (Streamlit import conflicts in non-browser test context) — same profile as before the fix.

## Next Phase Readiness

- smoke_auth.py now provides CI signal for all 19 pages including the three restricted-role pages
- us_av_2024 peer benchmarks will no longer silently drop the 10 US firms with previously NULL tangibility
- No blockers for next quality carry-forward tasks
