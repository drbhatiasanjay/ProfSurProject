# AI Chatbot — Fix List (2026-06-27)

## Status key
- [ ] To do
- [x] Done

---

## Section 1 — Context Bugs (cause cop-outs on valid questions)

### FIX-1: THESIS block hardcodes wrong scope for non-thesis panels
**File:** `models/llm_adapters.py` → `build_panel_context()`

**Problem:** The THESIS block always says "401 Indian listed firms, panel 2001–2024" even when
the user is on the run3 panel (400 firms, 2001–2025) or latest panel (402 firms, 2001–2025).
This creates a visible conflict — the DATA block says 400 firms while THESIS says 401.

**Fix:** Remove the hardcoded numbers from the THESIS block. They belong only in the DATA block,
which is already panel-mode-aware.

---

### FIX-2: Missing industry/sector leverage data → 4 cop-outs
**File:** `models/llm_adapters.py` → `build_panel_context()`

**Prompts that fail today:** H1, H2, H3, F4

**Problem:** The context has only life-stage means. There is no sector-level or year-level
breakdown, so any question about Manufacturing vs Services, industry rankings, or event-period
comparisons (GFC/IBC/COVID) returns "This data is not available in my current context."

**Fix:** Add two compact blocks to the context:

```
## [SOURCE: DATA] Industry Leverage (top 8 by post-2015 mean, same vintage)
Telecom: 133% | Steel: 27% | Cement: 21% | Chemicals: 20% |
Pharma: 10% | IT/Software: 5% | ...

## [SOURCE: DATA] Leverage by Event Period (panel mean %)
Pre-GFC (2001-07): XX | GFC (2008-09): XX | Post-GFC (2010-15): XX |
Post-IBC (2016-19): XX | COVID (2020-21): XX | Post-COVID (2022-25): XX
```

Data source: `db.get_industry_summary()` already exists.
Budget: context is 697 tokens; this adds ~150 tokens. Well within budget.

---

### FIX-3: Missing leverage distribution stats
**File:** `models/llm_adapters.py` → `build_panel_context()`

**Problem:** When users ask "why does leverage go from 0 to 200%?" the bot gives theory only,
cannot cite the actual distribution.

**Fix:** Add one line to the DATA block:
```
Leverage distribution: median=15.9%, p90=46%, p99=76%, max=1425%
(36 firm-years >100%, driven by Tata Teleservices Maharashtra)
```

---

## Section 2 — Response Quality (answers exist but are weak)

### FIX-4: A3 — Tangibility coefficient not cited despite being in context
**File:** `models/llm_adapters.py` → system prompt instructions

**Problem:** The context has `tangibility: coef=+34.726` but when asked about economic
significance, the AI deflects ("FE not available, I'll use OLS") without quoting the value.

**Fix:** Strengthen the instruction line:
```
# Current (weak):
Never fabricate numbers. Cite exact values from the context.

# Fix (explicit):
For coefficient interpretation questions, always quote the exact coefficient AND the sample
mean to compute the standardised effect: effect = coef × sample_mean.
```

---

### FIX-5: F1-type factual queries — Haiku sometimes gives theory before the number
**File:** `models/llm_adapters.py` → system prompt instructions

**Problem:** F1 "What is the mean leverage for Mature stage firms?" returns the correct number
(18.789%) but wraps it in theory prose before stating it. For factual queries routed to Haiku,
the answer should be the number first.

**Fix:** Add role-aware instruction prefix for factual queries:
```python
if query_type == "factual":
    system = "Answer in 1-2 sentences. State the number first, then one sentence of context.\n\n" + system
```
This should be applied in page 19 before calling `stream_anthropic`, not inside the adapter.

---

## Section 3 — UI Improvements (from approved plan)

### FIX-6: Follow-up suggestions don't work reliably
**File:** `models/llm_adapters.py`, `pages/19_ai_assistant.py`

**Problem:** `parse_llm_json()` looks for `{"followup_questions": [...]}` in the LLM response,
but the system prompt never asks for JSON, so follow-ups are rarely produced.

**Fix:** Add `generate_followup_suggestions()` — a separate Haiku call after the main response,
reading the last 3 turns and returning 3 contextual follow-up questions.

---

### FIX-7: Follow-up chips render as vertical button stack
**File:** `pages/19_ai_assistant.py`

**Fix:** Render in `st.columns(3)` with `use_container_width=True` so chips appear side-by-side.

---

### FIX-8: No metadata on responses (which model, how fast)
**File:** `pages/19_ai_assistant.py`

**Fix:** Store `model_used` and `elapsed_s` in chat_history. Show below each assistant message:
`Haiku · 2.1s` or `Sonnet · 8.4s`.

---

### FIX-9: Empty state shows hardcoded generic questions
**File:** `pages/19_ai_assistant.py`

**Fix:** Role-aware starter questions:
- `researcher` → thesis-level questions (stage means, coefficients, theory)
- `admin`/`cfo` → actionable questions (peer comparison, risk, what-if)

---

### FIX-10: No way to export the conversation
**File:** `pages/19_ai_assistant.py`

**Fix:** Add `st.download_button` in sidebar to export full chat as `.md` file.

---

### FIX-11: No context usage indicator
**File:** `pages/19_ai_assistant.py`

**Fix:** Add `st.progress(min(n/20, 1.0))` + caption `Context: N/20 messages` in sidebar.

---

## Section 4 — Correct Behaviour (do NOT fix)

### NOTED: F3 — Single-company leverage is always a cop-out in panel mode
This is **correct behaviour**. Company-specific data (Reliance 2023 leverage) is only available
in CFO mode (`build_company_context()`). The bot correctly says it cannot answer this in panel mode.

---

## Priority Order

| Priority | Fix | Effort | Impact |
|---|---|---|---|
| P0 | FIX-1: Remove hardcoded scope from THESIS block | 5 min | Removes false data conflict |
| P0 | FIX-2: Add industry + event-period data to context | 1 hr | Fixes H1, H2, H3, F4 cop-outs |
| P1 | FIX-3: Add leverage distribution to context | 15 min | Fixes 0-200% question |
| P1 | FIX-4: Strengthen coefficient citation instruction | 10 min | Fixes A3 weakness |
| P2 | FIX-5: Factual query prefix instruction | 20 min | Cleaner F1-type answers |
| P2 | FIX-6 to FIX-11: UI improvements | 3-4 hr | Better UX, not correctness |

---

## Files to modify

| File | Fixes |
|---|---|
| `models/llm_adapters.py` | FIX-1, FIX-2, FIX-3, FIX-4, FIX-6 |
| `pages/19_ai_assistant.py` | FIX-5, FIX-7, FIX-8, FIX-9, FIX-10, FIX-11 |
| `tests/test_chatbot.py` | New tests for FIX-6 (`generate_followup_suggestions`) |
