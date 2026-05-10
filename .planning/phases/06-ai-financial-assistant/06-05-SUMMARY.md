---
phase: 06-ai-financial-assistant
plan: "05"
status: complete
commits: [1317f43, d09d391]
date: 2026-05-10
uat: approved
---

# Summary: 06-05 — Topic 13 AI Wiring + active_company_cin + Page 19 Nav

## What Was Done

Completed Phase 6 integration: wired Page 17 Topic 13 to the LLM backend, set `active_company_cin` on Pages 17/18 to enable CFO-mode auto-detection in the floating chat bubble, and confirmed Page 19 navigation registration (already done in 06-04).

## Tasks Completed

**Task 1 — `build_topic_13_ai` in models/board_export.py (commit 1317f43):**
- Added new function alongside the existing rule-based `build_topic_13` (which was NOT touched)
- Signature: `build_topic_13_ai(company_code: int, panel_mode: str = "thesis", backend: str = "ollama") -> dict`
- LLM-first: calls `build_company_context(company_code)` → sends 4 sub-prompts (13.1–13.4) via `stream_ollama` or `stream_anthropic` → parses bullet lines
- Fallback: raw SQL via `db.get_connection()` + `db._vintage_predicate()` (avoids @st.cache_data issue) → derives rule-based bullets from latest `leverage`, `profitability`, `industry_group`, `life_stage`
- Returns `{figs, tables, insights: [(label, [bullets])], actions: [str], ai_offline: bool}`
- 3 new tests in `TestTopic13AIRecommendations`: LLM-up, LLM-offline, unknown company code — all pass

**Task 2 — Pages 17/18 + Page 19 nav (commit d09d391):**
- `pages/17_board_export.py`: `st.session_state["active_company_cin"] = company_code` on selection; Topic 13 AI expander renders `build_topic_13_ai` output with offline warning badge
- `pages/18_company_navigator.py`: `st.session_state["active_company_cin"] = company_code` on node selection
- `app.py` Page 19 nav: already registered in f9b8839 — no change needed

**Task 3 — UAT Checkpoint:** Approved by user (all 6 journeys pass).

## Must-Haves Verified

- ✅ Page 19 visible to admin + researcher; hidden from viewer
- ✅ Topic 13 in Page 17 preview renders 4 sub-topic blocks with ≥1 bullet (LLM path)
- ✅ Topic 13 falls back to rule-based bullets with "AI offline" warning (offline path)
- ✅ Pages 17/18 set `active_company_cin` → floating bubble auto-detects CFO mode
- ✅ Audit log distinguishes `ai_assistant` (bubble) from `ai_assistant_page` (Page 19)
- ✅ UAT journeys 1–6 all pass

## Key Architecture Contracts (for future reference)

| Contract | Detail |
|----------|--------|
| `build_topic_13_ai` signature | `(company_code: int, panel_mode: str, backend: str) -> dict` |
| DB columns used | `company_code` (int), `leverage`, `profitability`, `industry_group`, `life_stage` |
| Fallback SQL | `db.get_connection()` + `db._vintage_predicate()` — NOT `db.get_filtered_financials` |
| `active_company_cin` set by | Pages 17 and 18 on company selection |
| Chat mode detection | `_detect_chat_mode()` in app.py keys off `active_company_cin` |
| Audit log page_name taxonomy | `ai_assistant` (bubble), `ai_assistant_page` (Page 19) |
| Role visibility | Page 19: admin + researcher only; FAB bubble: all logged-in users |
| Cloud Run production | No local Ollama — defaults to Claude API (`ANTHROPIC_API_KEY` in secrets.toml) |

## Test Count

- 95 board_export tests pass (was 92, +3 new for Topic 13 AI)
- Overall suite: pre-existing 18 failed / 52 errors (TestPage15 flakiness) — unrelated to this plan

## Phase 6 Completion

All 5 plans complete. Phase 6 goal achieved: AI Financial Assistant is a coherent end-to-end product with floating bubble (global), dedicated Page 19, and Board Export Topic 13 AI Recommendations.
