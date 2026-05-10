---
phase: 06-ai-financial-assistant
plan: 01
subsystem: api
tags: [llm, ollama, anthropic, tiktoken, sqlite, audit-log, context-grounding]

# Dependency graph
requires:
  - phase: 05-company-navigator
    provides: db.get_connection, db._vintage_predicate, audit_log schema, companies+financials tables
  - phase: 04-board-export
    provides: models.scenario_regression (compute_leverage_ols_coefs, leverage_predictor_sample_means, PREDICTORS)
provides:
  - models/llm_adapters.py with 9 public exports
  - Token-bounded context builders (CFO + researcher modes) using raw SQL
  - Query classifier (factual/analytical/hybrid)
  - Ollama and Anthropic streaming adapters (st.write_stream compatible)
  - JSON response parser with 4-key schema
  - Audit logger writing to existing audit_log table
affects: [06-02, 06-03, 06-04, 06-05, floating-chat-bubble, page-19-ai-assistant, board-deck-topic-13]

# Tech tracking
tech-stack:
  added: [ollama>=0.6.2, anthropic>=0.25, tiktoken>=0.5]
  patterns:
    - "Raw SQL via db.get_connection() for non-Streamlit contexts (avoids @st.cache_data)"
    - "Lazy Streamlit import inside functions to keep module importable in pytest"
    - "Token-budget guard with progressive truncation (drop trend line, then peer detail)"
    - "Generator-based streaming (yield string chunks) compatible with st.write_stream()"

key-files:
  created:
    - models/llm_adapters.py
  modified:
    - models/__init__.py
    - requirements.txt

key-decisions:
  - "JOIN companies table for company_name/industry_group — those columns are NOT in financials"
  - "leverage_predictor_sample_means returns abbreviated keys (prof/tang/dvnd) — map to PREDICTORS names in build_panel_context"
  - "No streamlit import at module level — lazy import only inside stream_anthropic function"
  - "Ollama num_ctx=8192 override mandatory (default 2048 truncates 1250-token prompts)"
  - "Audit log uses existing schema — no migration; details JSON carries backend+token_count+query_preview"

patterns-established:
  - "Context builders always return graceful strings even on DB errors (never raise)"
  - "Streaming adapters always yield at least one string chunk (error or content)"
  - "parse_llm_json never raises — plain text wrapped in answer key"

# Metrics
duration: 6min
completed: 2026-05-07
---

# Phase 6 Plan 01: LLM Adapters Module Summary

**models/llm_adapters.py: context-grounded LLM backend with Ollama+Anthropic streaming, query classifier, JSON parser, audit logger — all importable outside Streamlit**

## Performance

- **Duration:** 6 min
- **Started:** 2026-05-07T01:39:45Z
- **Completed:** 2026-05-07T01:45:36Z
- **Tasks:** 2/2
- **Files modified:** 3 (models/llm_adapters.py, models/__init__.py, requirements.txt)

## Accomplishments

- Created models/llm_adapters.py with 9 public exports powering all Phase 6 features
- build_company_context: 237 tokens for Asian Paints (company + 5yr trend + peer group), JOIN-based SQL
- build_panel_context: 250 tokens for thesis panel (401 firms, OLS baseline with correct sample means)
- Both streaming adapters yield string chunks compatible with st.write_stream(); graceful error strings when backend unavailable
- Zero regressions — all 344 existing tests still pass

## Public API

### Context Builders

**`build_company_context(company_code: int, panel_mode: str = "thesis") -> str`**
- JOINs companies + financials for latest 5 years + peer group
- Returns <= 900 token markdown with COMPANY + PEER GROUP sections + GROUNDING_FOOTER
- Tested: 237 tokens for Asian Paints (22859), 223 tokens for company 1120, 232 tokens for 5747

**`build_panel_context(panel_mode: str = "thesis") -> str`**
- Uses compute_leverage_ols_coefs + leverage_predictor_sample_means from scenario_regression
- Returns <= 900 token markdown with PANEL OVERVIEW + OLS BASELINE sections
- Tested: 250 tokens for thesis mode (401 firms, 8677 obs, 2001-2024)

### Query Classifier

**`classify_query(query: str) -> Literal["factual", "analytical", "hybrid"]`**
- Keyword heuristic: factual ("what is", "how much", "show me") vs analytical ("why", "explain", "recommend")
- "What is leverage of Reliance?" -> factual; "Why is leverage high?" -> analytical; mixed -> hybrid

### Streaming Adapters

**`stream_ollama(messages: list[dict], model: str = "llama3.1:8b") -> Iterator[str]`**
- num_ctx=8192 override (default 2048 truncates context)
- Graceful error string if Ollama not installed or model not found

**`stream_anthropic(messages: list[dict], system: str = "", model: str = "claude-haiku-4-5-20251001", max_tokens: int = 1024) -> Iterator[str]`**
- API key: ANTHROPIC_API_KEY env var, then st.secrets fallback
- Graceful error string if key not configured

### Utilities

**`parse_llm_json(raw: str) -> dict`**
- Keys: answer, citations, followup_questions, chart_request
- Falls back to plain text in answer key; never raises

**`log_chat_query(username, role, backend, token_count, query, session_id) -> None`**
- Writes to audit_log: page_name="ai_assistant", action_type="ai_query"
- Details JSON: {"llm_backend": "ollama", "token_count": 150, "query_preview": "..."}
- Silent no-op on DB errors — never breaks chat

**`count_tokens(text: str) -> int`**
- tiktoken cl100k_base encoding; falls back to len(text)//4 if tiktoken unavailable

**`GROUNDING_FOOTER: str`**
- Standard grounding instruction appended to all contexts

## Backend Selection Logic

```
stream_anthropic:
  1. os.environ.get("ANTHROPIC_API_KEY")
  2. st.secrets.get("ANTHROPIC_API_KEY")  [lazy import inside function]
  3. Yield error string if neither found

stream_ollama:
  No auth needed — local server on port 11434
  num_ctx=8192 passed via options dict
```

## Audit Log Row Shape

```
INSERT INTO audit_log(username, role, page_name, action_type, details, session_id)
page_name = "ai_assistant"
action_type = "ai_query"
details = {"llm_backend": "ollama|anthropic", "token_count": N, "query_preview": "...[:200]"}
```

## Token Budgets Observed (3 sample contexts)

| Mode | company_code | Life Stage | Tokens | Within Budget |
|------|-------------|-----------|--------|---------------|
| CFO (thesis) | 22859 (Asian Paints) | Maturity | 237 | Yes (<= 900) |
| CFO (thesis) | 1120 | Growth | 223 | Yes (<= 900) |
| CFO (thesis) | 5747 | Decline | 232 | Yes (<= 900) |
| Researcher (thesis) | n/a | panel-level | 250 | Yes (<= 900) |

## Task Commits

1. **Task 1+2: LLM adapters module (context builders + classifier + adapters + parser + logger)** - `690790b` (feat)

Note: Both tasks were implemented in a single atomic commit since the complete module was written as one cohesive unit. The plan allowed splitting but the full module had no inter-task dependencies.

## Files Created/Modified

- `models/llm_adapters.py` — Full LLM adapter module (9 public exports, ~340 lines)
- `models/__init__.py` — Added `from . import llm_adapters`
- `requirements.txt` — Added ollama>=0.6.2, anthropic>=0.25, tiktoken>=0.5

## Decisions Made

1. **JOIN companies table**: `company_name` and `industry_group` are in `companies`, not `financials`. Plan's SQL specification assumed wrong table — fixed with JOIN.
2. **Key mapping for sample means**: `leverage_predictor_sample_means` returns `prof`/`tang`/`dvnd` keys but PREDICTORS list uses `profitability`/`tangibility`/`dividend`. Added explicit mapping dict `_means_key_map`.
3. **Complete module in one pass**: Both tasks' code was written together since there were no inter-task dependencies. The Task 1 commit captured everything.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Wrong table for company_name and industry_group**
- **Found during:** Task 1 verification smoke test
- **Issue:** Plan's SQL template queried `company_name` and `industry_group` directly from `financials` table, but these columns don't exist there — they live in the `companies` table
- **Fix:** Changed SQL to `JOIN companies c ON c.company_code = f.company_code` and prefixed columns with `c.` for name/industry, `f.` for financial columns. Peer query also updated to JOIN companies for industry_group filter.
- **Files modified:** models/llm_adapters.py
- **Verification:** build_company_context(22859) now returns "Asian Paints Ltd." with correct industry "Paints & varnishes"
- **Committed in:** 690790b

**2. [Rule 1 - Bug] Wrong key names for leverage_predictor_sample_means lookup**
- **Found during:** Task 1 verification (sample means showed 0.000 for profitability, tangibility, dividend)
- **Issue:** Plan's coef_lines template used `means.get(p, 0.0)` where `p` is a PREDICTORS name like "profitability", but `leverage_predictor_sample_means` returns abbreviated keys ("prof", "tang", "dvnd"). Three of six predictors silently returned 0.0.
- **Fix:** Added `_means_key_map` dict mapping PREDICTORS names to abbreviated keys; used in coef_lines f-string.
- **Files modified:** models/llm_adapters.py
- **Verification:** build_panel_context shows correct sample means (profitability=+0.157, tangibility=+0.285, dividend=+29.350)
- **Committed in:** 690790b

---

**Total deviations:** 2 auto-fixed (2 bugs)
**Impact on plan:** Both fixes were necessary for correct data display. No scope creep.

## Issues Encountered

None — both bugs were caught and fixed during verification before commit.

## User Setup Required

This plan introduced two external service dependencies:

**Ollama (local dev only)**
- Install: `winget install Ollama.Ollama`
- Pull model: `ollama pull llama3.1:8b`
- GCP Cloud Run does NOT use Ollama (no local server)

**Anthropic (Cloud Run prod)**
- Add to `.streamlit/secrets.toml`: `ANTHROPIC_API_KEY = "sk-ant-..."`
- Or set env var: `ANTHROPIC_API_KEY`
- Console: https://console.anthropic.com/settings/keys

## Next Phase Readiness

- models/llm_adapters.py complete — all Phase 6 features can import from here
- Ready for 06-02-PLAN.md (floating chat bubble in app.py)
- Ollama dev setup and Anthropic key still needed for live LLM calls (expected)
- 344 tests passing — no regressions

---
*Phase: 06-ai-financial-assistant*
*Completed: 2026-05-07*
