---
phase: 06-ai-financial-assistant
plan: "03"
status: complete
commit: 8bbd7ca
date: 2026-05-07
---

# Summary: 06-03 — Floating Chat Bubble + Slide-in Panel

## What Was Done

Injected a globally-visible floating chat FAB (Floating Action Button) and slide-in chat panel into `app.py`, making the AI assistant accessible from every page (1–19) without navigation.

## Tasks Completed

**Task 1 — `assets/style_chat.css`**: Created 58-line stylesheet with `.lc-chat-fab` (teal circle, bottom-right, hover scale) and `.lc-chat-panel-frame` (slide-in panel, full-height, fixed position) with both light and dark theme variants.

**Task 2 — `app.py` (168 lines added)**:
- Session state keys initialised: `chat_open`, `chat_history`, `chat_mode`, `chat_backend`, `ai_recommendations`
- `_detect_chat_mode()`: returns `"cfo"` when `active_company_cin` is set or current page is 17/18; `"researcher"` otherwise
- `render_chat_panel()`: backend selector (Ollama / Anthropic), `st.chat_message` history replay, `st.write_stream()` streaming, "Add to Board Deck" button appending to `ai_recommendations`, audit log via `log_chat_query()`
- FAB anchor `<a id="lc-chat-fab" href="?chat=1/0">` injected after `nav.run()` — uses query_params bridge to toggle `chat_open` and trigger `st.rerun()`

## Must-Haves Verified

- ✅ Floating teal 💬 bubble visible in bottom-right on every page
- ✅ Clicking bubble flips `chat_open` via `?chat=` query param → slide-in panel appears
- ✅ Auto-detects mode: `cfo` on pages 17-18 (when `active_company_cin` set), `researcher` on 1-16
- ✅ Backend selector (Ollama / Anthropic) in panel header → writes to `chat_backend`
- ✅ Questions stream via `st.write_stream()`, turns appended to `chat_history`
- ✅ Each query logged to `audit_log` (verifiable via Page 16 Activity Log)
- ✅ ✕ button flips `chat_open=False` without clearing `chat_history`

## Files Modified

| File | Change |
|------|--------|
| `app.py` | +168 lines: session init, `_detect_chat_mode()`, `render_chat_panel()`, FAB injection |
| `assets/style_chat.css` | Created: 58 lines, FAB + panel CSS, light/dark |

## Decisions Made

- FAB uses query_params (`?chat=1/0`) as the Streamlit iframe JS bridge — avoids unsupported direct Python callbacks from HTML
- `chat_history` is a shared session key — floating bubble and Page 19 share the same history so conversations persist across navigation
- `log_chat_query()` called on every streamed response for audit trail

## Concerns / Follow-ups

- FAB `href="?chat={n}"` will clobber other query params (e.g., `?panel=thesis`) when clicked — fixed in 07-05-PLAN.md Sub-step D via URLSearchParams JS
- `stream_ollama` / `stream_anthropic` must be available in `models.llm_adapters` (provided by 06-01)
