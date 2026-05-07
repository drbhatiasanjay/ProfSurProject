# Phase 6: AI Financial Assistant - Research

**Researched:** 2026-05-07
**Domain:** LLM integration, Streamlit floating UI, streaming adapters, context injection
**Confidence:** HIGH (all critical library APIs verified against official sources)

---

## Summary

This phase integrates a context-injection LLM chat assistant into the existing Streamlit multipage app.
No fine-tuning is used — grounding is achieved via structured 800-900 token prompt blocks injected per
query. Two backends must be supported: Ollama (llama3.1:8b, local dev) and Anthropic (claude-haiku-4-5,
GCP Cloud Run prod). A floating FAB bubble is injected globally from app.py via st.markdown
(unsafe_allow_html=True), consistent with the existing fixed navbar already in the codebase. Chat state
lives in st.session_state["chat_*"] keys and survives page navigation within a single browser session.

The standard approach for both LLM adapters is a generator-based wrapper that yields string chunks,
compatible with Streamlit's st.write_stream(). The hidden-checkbox state bridge for the FAB bubble is
workable but requires careful management on every rerun; the simpler and more robust alternative is to
keep chat open/closed state in st.session_state and re-inject the FAB HTML block on every app.py rerun
(which already happens for the fixed navbar). LiteLLM is a viable but heavyweight abstraction — its
~1 second import time and ~500 MB memory footprint make it unsuitable for this app's production Cloud
Run deployment; two lean native adapters (30 lines each) are the better choice.

**Primary recommendation:** Write two ~30-line adapter functions using the native ollama and anthropic
SDKs, each returning a generator of string chunks compatible with st.write_stream(). Keep the FAB
open/closed state in st.session_state, not in a hidden HTML checkbox. Re-inject the FAB HTML on every
app.py rerun (same pattern as the existing navbar).

---

## Standard Stack

### Core

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| ollama | 0.6.2 (Apr 2026) | Ollama Python SDK, local LLM streaming | Official SDK, dict + attribute access |
| anthropic | latest (>=0.25) | Anthropic Python SDK, cloud streaming | Official SDK, text_stream generator |

### Supporting

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| tiktoken | >=0.5 | Fast token counting for context budget | Count tokens before injection |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Native ollama + anthropic SDKs | litellm | LiteLLM unifies API but adds ~1 s import time, ~500 MB memory, 8 ms/req proxy overhead — unacceptable for Cloud Run cold starts |
| st.session_state open/closed | hidden HTML checkbox bridge | Checkbox bridge is fragile across reruns; session_state is the canonical Streamlit state mechanism |

### Installation

```bash
pip install ollama anthropic tiktoken
```

---

## Ollama SDK — Exact API

**Source:** https://github.com/ollama/ollama-python (verified, v0.6.2)
**Confidence:** HIGH

```python
# Synchronous streaming — chunk is a dict or attribute-access object
from ollama import chat as ollama_chat

def stream_ollama(messages: list[dict], model: str = "llama3.1:8b"):
    """Yields string chunks. Compatible with st.write_stream()."""
    stream = ollama_chat(model=model, messages=messages, stream=True)
    for chunk in stream:
        # Both dict access and attribute access work:
        # chunk["message"]["content"]  OR  chunk.message.content
        yield chunk.message.content or ""
```

Key facts:
- `stream=False` is the SDK default; must pass `stream=True` explicitly.
- Install: `pip install ollama`
- Error type: `ollama.ResponseError` for model-not-found, connection refused, etc.
- Ollama server must be running separately (`ollama serve`); SDK does not start it.
- Host defaults to `http://localhost:11434`. Override: `Client(host="http://...")`.
- On GCP Cloud Run, Ollama is NOT available. The adapter must detect this and fall back.

**Ollama availability check pattern:**

```python
import os

OLLAMA_AVAILABLE = os.environ.get("OLLAMA_HOST", "http://localhost:11434")

def is_ollama_reachable() -> bool:
    try:
        import requests
        r = requests.get(f"{OLLAMA_AVAILABLE}/api/tags", timeout=1)
        return r.status_code == 200
    except Exception:
        return False
```

---

## Anthropic SDK — Exact Streaming Pattern

**Source:** https://platform.claude.com/docs/en/build-with-claude/streaming (verified)
**Confidence:** HIGH

```python
import anthropic

def stream_anthropic(messages: list[dict], model: str = "claude-haiku-4-5-20251001",
                     system: str = "", max_tokens: int = 1024):
    """Yields string chunks. Compatible with st.write_stream()."""
    client = anthropic.Anthropic()  # reads ANTHROPIC_API_KEY from env
    with client.messages.stream(
        model=model,
        max_tokens=max_tokens,
        system=system,
        messages=messages,
    ) as stream:
        for text in stream.text_stream:
            yield text
```

Key facts (from official docs):
- **Exact model ID:** `claude-haiku-4-5-20251001` (alias: `claude-haiku-4-5`)
- Context window: 200k tokens; max output: 64k tokens.
- `stream.text_stream` yields plain strings directly — no array-unwrapping needed.
- The `with` block manages the HTTP connection; must not be used outside the generator.
  **Important:** When wrapping in a generator function, the `with` block stays open
  while the generator is being consumed. This is correct Python generator behavior.
- The issue noted in Streamlit GitHub #8963 (JSON output) arises when using
  `client.messages.create(stream=True)` directly (raw SSE events). Using
  `client.messages.stream()` with `.text_stream` resolves this — it yields plain strings.
- API key: read from `ANTHROPIC_API_KEY` env var, or `st.secrets["ANTHROPIC_API_KEY"]`.

**Adapter selection logic (backend router):**

```python
def get_llm_backend() -> str:
    """Returns 'ollama' or 'anthropic' based on availability and config."""
    import streamlit as st
    # Explicit override via secrets
    backend = st.secrets.get("LLM_BACKEND", "auto")
    if backend in ("ollama", "anthropic"):
        return backend
    # Auto-detect: try Ollama first, fall back to Anthropic
    if is_ollama_reachable():
        return "ollama"
    if st.secrets.get("ANTHROPIC_API_KEY"):
        return "anthropic"
    return "none"  # no LLM available — UI shows graceful error
```

---

## Streamlit Floating Overlay — Best Pattern

**Source:** Streamlit docs, existing app.py navbar pattern, community research
**Confidence:** HIGH for session_state approach; MEDIUM for JS interaction due to sandbox

### Confirmed Working: st.markdown with unsafe_allow_html=True (already in app.py)

The existing codebase already uses this exact pattern for the fixed navbar at line 264 of app.py.
The `st.markdown(..., unsafe_allow_html=True)` pattern with inline `position: fixed` CSS is confirmed
working in the running app. The same mechanism WILL work for the FAB bubble.

**Note on st.html() regression:** Streamlit GitHub issue #10384 documents a regression in v1.42+
where `st.html()` injects CSS but it does not apply. Since app.py already uses `st.markdown` for the
navbar successfully, use `st.markdown` (not `st.html`) for the FAB injection.

### FAB State Management

Do NOT use a hidden HTML checkbox as the state bridge. Use st.session_state directly:

```python
# In app.py, after the navbar injection:
if "chat_open" not in st.session_state:
    st.session_state["chat_open"] = False
```

The FAB button click must trigger a Streamlit rerun. Two options:
1. **Pure Python button in a fixed container** — not possible (Streamlit containers cannot be `position: fixed`)
2. **HTML FAB + JS window.location href trick** — FAB click sets a query param, Streamlit detects on rerun
3. **HTML FAB + JS postMessage** — FAB click posts message; requires custom component to receive
4. **Recommended: st.button in sidebar or top-right nav** — simplest, fully functional; FAB is cosmetic

**Pragmatic recommendation for the FAB:**

Render the FAB as a purely cosmetic HTML overlay via st.markdown. When clicked, the JS sets
`window.location.search = "?chat=1"`. In app.py, detect `st.query_params.get("chat")` and flip
`st.session_state["chat_open"]`. This produces one extra rerun per click but is fully correct.

```python
# In app.py — inject FAB HTML (re-injected every rerun, same as navbar)
_chat_icon = "✕" if st.session_state.get("chat_open") else "💬"
st.markdown(f"""
<a id="lc-chat-fab" href="?chat={'0' if st.session_state.get('chat_open') else '1'}"
   style="
     position: fixed; bottom: 2rem; right: 2rem; z-index: 1000002;
     width: 56px; height: 56px; border-radius: 50%;
     background: #0D9488; color: white; border: none; cursor: pointer;
     font-size: 22px; display: flex; align-items: center; justify-content: center;
     box-shadow: 0 4px 16px rgba(13,148,136,0.4); text-decoration: none;
   ">{_chat_icon}</a>
""", unsafe_allow_html=True)

# Handle query param toggle
_chat_param = st.query_params.get("chat", "0")
if _chat_param == "1" and not st.session_state.get("chat_open"):
    st.session_state["chat_open"] = True
    st.query_params.clear()
    st.rerun()
elif _chat_param == "0" and st.session_state.get("chat_open"):
    st.session_state["chat_open"] = False
    st.query_params.clear()
    st.rerun()
```

For the expanded panel (360px slide-in), render it as a Streamlit `st.container()` with custom CSS
applied via `st.markdown` targeting the container's data-testid. This is where actual chat UI lives.

### CSS Persistence Across Reruns

Since app.py runs on EVERY rerun (it is the entrypoint), all `st.markdown` calls in app.py are
automatically re-injected on every rerun. This is the existing pattern for the navbar and theme CSS.
No special persistence mechanism is needed — just place the FAB injection in app.py before `nav.run()`.

---

## Context Window and Token Math

**Source:** Ollama library page + Anthropic docs (both verified)
**Confidence:** HIGH

### llama3.1:8b Context Window
- **Native context window:** 128k tokens (confirmed on Ollama library page)
- **Default Ollama context (`num_ctx`):** 2048 tokens unless overridden with `options={"num_ctx": 8192}`
- **Critical:** Ollama's default `num_ctx` is 2048, NOT the model's native 128k. Must explicitly set.

```python
# Correct Ollama call with sufficient context
ollama_chat(
    model="llama3.1:8b",
    messages=messages,
    stream=True,
    options={"num_ctx": 8192}  # REQUIRED — default is 2048
)
```

### Token Budget Analysis

| Component | Estimated Tokens |
|-----------|-----------------|
| System prompt (role, instructions) | ~80 |
| Company context block (5yr table, stage history) | ~350 |
| Peer context block | ~120 |
| Econometric context block | ~150 |
| Total context injection | ~700 |
| 5-turn chat history (user+assistant, ~100 tok/turn) | ~500 |
| User query | ~50 |
| **Total input** | **~1,250** |
| Expected JSON output (answer + citations + followups) | ~300 |
| **Total with output** | **~1,550** |

**Conclusion:** The 800-900 token context block + 5-turn history + response fits comfortably within
8,192 tokens. An `num_ctx=8192` Ollama setting is sufficient with headroom to spare. The 128k model
window is not needed. Claude Haiku 4.5's 200k context window is far more than adequate.

### tiktoken for Token Counting

```python
import tiktoken

# Use cl100k_base for both OpenAI-family and llama models (approximate)
_enc = tiktoken.get_encoding("cl100k_base")

def count_tokens(text: str) -> int:
    return len(_enc.encode(text))
```

Token counts for llama3.1:8b will differ slightly from cl100k but the approximation is accurate
enough for budget management (within 10%).

---

## LiteLLM vs Dual Adapters

**Source:** LiteLLM GitHub issues #7605, #21046; PyPI; community benchmarks
**Confidence:** HIGH

### LiteLLM Overhead Facts

| Metric | Value | Source |
|--------|-------|--------|
| Import time | ~1 second | GitHub issue #7605 |
| Memory per worker | ~500 MB | GitHub issue #21046 |
| Proxy latency (median) | 8 ms | Release notes v1.71.1 |
| Proxy latency (P99) | 45 ms | Release notes v1.71.1 |

### Decision: Do NOT use LiteLLM

Reasons:
1. **Import time:** 1 second import hits every Cloud Run cold start — unacceptable for a dashboard app.
2. **Memory:** 500 MB base memory competes with the existing app's ML libraries on a 2 Gi Cloud Run instance.
3. **Unnecessary abstraction:** Only two backends needed (Ollama local, Anthropic prod). Two 30-line
   adapter functions are simpler, faster, and have zero overhead.
4. **Feature parity:** The unified streaming API (`for chunk in completion(...)`) is trivially replicated
   with the pattern `for chunk in stream_ollama_or_anthropic(...)`.

**Use the native SDKs.** Total adapter code: ~60 lines in a new `models/llm_adapters.py` file.

---

## Streamlit Chat State Persistence

**Source:** Streamlit official docs, community discussions
**Confidence:** HIGH

### What Persists

- `st.session_state` persists across page navigation within a single browser session (confirmed).
- Navigating via the st.navigation sidebar does NOT reset session_state.
- Navigating via URL change (direct link, reload) DOES reset session_state (WebSocket reconnect).

### Chat Keys in session_state

```python
# Keys to initialize (in helpers.py ensure_session_state() or app.py)
defaults = {
    "chat_open": False,
    "chat_messages": [],       # list of {"role": "user"|"assistant", "content": str}
    "chat_context_mode": None, # "cfo" | "researcher" — set by page context
    "chat_company_code": None, # set when on pages 17-18
    "chat_last_response": None, # full parsed JSON of last LLM response
}
```

### Message Format

Follow the standard Streamlit/OpenAI format for cross-compatibility:

```python
st.session_state.chat_messages.append({"role": "user", "content": user_query})
# After streaming:
st.session_state.chat_messages.append({"role": "assistant", "content": full_response_text})
```

### History Truncation

Truncate history to last N turns before each API call to stay within token budget:

```python
MAX_HISTORY_TURNS = 5  # 5 user + 5 assistant = 10 messages
history_for_api = st.session_state.chat_messages[-MAX_HISTORY_TURNS * 2:]
```

---

## Windows Ollama Notes

**Source:** Ollama troubleshooting docs, GitHub issues
**Confidence:** MEDIUM

| Issue | Details | Fix |
|-------|---------|-----|
| Windows Defender quarantine | Defender may flag Ollama binary | Exclude Ollama install dir from real-time scan |
| PATH not updated in open terminals | Installer updates PATH but open terminals miss it | Close all terminals, reopen |
| Model path env var not respected | `OLLAMA_MODELS` may not work on Windows | Set via System Properties → Environment Variables, not shell |
| Slow token generation from shortcut | Launching from .lnk is slower than CLI | Always run `ollama serve` from PowerShell |
| GPU not found in WSL2 | Models run on CPU only inside WSL | Install NVIDIA CUDA driver for WSL or run Ollama on Windows host |
| Default context window 2048 | Even with 128k model, Ollama defaults to 2048 ctx | Always pass `options={"num_ctx": 8192}` |

**For this project:** Ollama is local-dev-only. GCP Cloud Run uses Anthropic API. Windows dev box
runs Ollama natively (not WSL). The developer must run `ollama pull llama3.1:8b` before first use.

---

## Architecture Patterns

### Recommended Module Structure

```
models/
  llm_adapters.py      # stream_ollama(), stream_anthropic(), get_backend(), build_context_block()
pages/
  19_ai_assistant.py   # Full-screen Page 19 chat interface
app.py                 # FAB injection + chat_open state management (already the entrypoint)
```

### Context Builder Pattern

```python
# models/llm_adapters.py

def build_cfo_context(company_code: int, db_module) -> str:
    """Builds ~700-token CFO-mode context block."""
    detail = db_module.get_company_detail(company_code)
    peers = db_module.get_company_peers(company_code)
    financials = db_module.get_active_financials(company_code)
    # ... format as the template defined in phase context
    return context_str

def build_researcher_context(filters: dict, db_module, models_module) -> str:
    """Builds ~700-token researcher-mode context block from panel OLS outputs."""
    # Run or retrieve cached OLS results
    # Format panel stats, model coefficients
    return context_str
```

### Streaming Response + JSON Parse Pattern

The LLM is prompted to return structured JSON. Parse after streaming completes:

```python
import json, re

def parse_llm_json(raw: str) -> dict:
    """Extract JSON from LLM response that may have surrounding prose."""
    # Try direct parse first
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        pass
    # Find JSON block in response
    m = re.search(r'\{.*\}', raw, re.DOTALL)
    if m:
        try:
            return json.loads(m.group())
        except json.JSONDecodeError:
            pass
    # Fallback: wrap raw text in answer field
    return {"answer": raw, "citations": [], "followup_questions": [], "chart_request": None}
```

**Important:** Stream the raw text for typewriter effect, then parse the full response. Do NOT
attempt to parse JSON incrementally during streaming.

### Audit Log Integration

The existing `audit_log` table has columns: `ts, username, role, page_name, action_type, details, session_id`.
The `details` column is a JSON string. Extend via the `details` field — no schema migration needed:

```python
def log_ai_query(username: str, role: str, session_id: str,
                 backend: str, token_count: int, query: str) -> None:
    import json
    details = json.dumps({
        "llm_backend": backend,
        "token_count": token_count,
        "query_preview": query[:100],
    })
    db._exec(
        "INSERT INTO audit_log(username, role, page_name, action_type, details, session_id)"
        " VALUES (?,?,?,?,?,?)",
        [username, role, "ai_assistant", "ai_query", details, session_id],
    )
```

This uses the existing `_exec` helper. No new db functions required — or add `log_ai_query()` to db.py
for consistency.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Streaming from Anthropic | Custom HTTP SSE parser | `client.messages.stream()` + `.text_stream` | SDK handles reconnect, error types, buffering |
| Streaming from Ollama | Raw HTTP requests to localhost | `ollama.chat(stream=True)` | SDK handles chunked responses, error types |
| Token counting | Character-based estimation | `tiktoken` | Character count varies 2-4x per token; budget management fails |
| JSON extraction from LLM output | Regex-only parser | `json.loads()` with regex fallback | LLMs occasionally produce valid JSON with surrounding prose |
| Chat history truncation | Custom summarization | Fixed sliding window (last 5 turns) | Summarization requires another LLM call; window is sufficient |

**Key insight:** Both LLM SDKs handle the hardest parts (backpressure, connection management,
error classification). The adapters are thin wrappers — ~30 lines each.

---

## Common Pitfalls

### Pitfall 1: Ollama Default Context (num_ctx = 2048)

**What goes wrong:** Context block + history exceeds 2048 tokens; model silently truncates to
2048 — response is incoherent or ignores most of the context.
**Why it happens:** Ollama SDK defaults num_ctx to 2048 regardless of model capability.
**How to avoid:** Always pass `options={"num_ctx": 8192}` to `ollama_chat()`.
**Warning signs:** Responses ignore the injected company data; seem generic.

### Pitfall 2: Anthropic streaming generator + with block

**What goes wrong:** `with client.messages.stream(...) as stream: yield` — the generator is consumed
lazily. If the caller doesn't fully exhaust the generator, the `with` block may not close properly.
**Why it happens:** Python generators are lazy; the `with` block's `__exit__` runs only when the
generator is garbage-collected if not fully consumed.
**How to avoid:** Use `st.write_stream(stream_fn(...))` which always exhausts the generator. If using
manually, wrap in `try/finally` or use `list()` to force exhaustion.

### Pitfall 3: JSON streaming display

**What goes wrong:** The entire JSON blob (including `"answer"`, `"citations"`, `"followup_questions"`)
streams character-by-character into the chat bubble — users see raw JSON.
**Why it happens:** `st.write_stream()` shows everything yielded, including the JSON wrapper.
**How to avoid:** Two options:
- Have the LLM stream only the `answer` field text, then call the API a second time (non-streaming)
  for the structured metadata.
- Preferred: Stream all text into a hidden buffer; display only after `parse_llm_json()` succeeds.
  Show a spinner during streaming, then render the parsed answer.

### Pitfall 4: st.html() CSS regression

**What goes wrong:** Using `st.html()` to inject the FAB CSS — styles are in DOM but don't apply
(Streamlit bug #10384, regression in v1.42.1).
**How to avoid:** Use `st.markdown(..., unsafe_allow_html=True)` for all CSS injection. The app
already does this successfully for the navbar.

### Pitfall 5: Chat session_state reset on URL navigation

**What goes wrong:** User opens a direct URL (e.g., shares a link to Page 19) — chat history gone.
**Why it happens:** Direct URL navigation creates a new WebSocket session = new session_state.
**How to avoid:** This is expected Streamlit behavior. Don't promise chat history persistence across
browser sessions. Document that the chat is session-scoped.

### Pitfall 6: LLM hallucinating data outside context

**What goes wrong:** LLM invents leverage ratios, peer names, or years not in the injected context.
**Why it happens:** Both llama3.1:8b and claude-haiku will generate plausible-sounding numbers.
**How to avoid:** Context block ends with: "Answer ONLY from the data above. If asked about something
not in the context, say 'This data is not available in my current context.'"

### Pitfall 7: Blocking main thread during LLM call

**What goes wrong:** LLM call blocks Streamlit's main thread — sidebar and other widgets freeze.
**Why it happens:** Streamlit runs synchronously; a 5-15 second Ollama call blocks everything.
**How to avoid:** Use `st.write_stream()` which renders incrementally. The streaming generators
yield control between chunks. This is sufficient for the use case; async is not required.

---

## Code Examples

### Full Adapter Module Pattern

```python
# models/llm_adapters.py
# Source: ollama PyPI v0.6.2 + Anthropic docs (official)

from typing import Generator
import streamlit as st

def stream_ollama(messages: list[dict], model: str = "llama3.1:8b") -> Generator[str, None, None]:
    from ollama import chat as ollama_chat, ResponseError
    try:
        stream = ollama_chat(
            model=model,
            messages=messages,
            stream=True,
            options={"num_ctx": 8192},
        )
        for chunk in stream:
            yield chunk.message.content or ""
    except ResponseError as e:
        yield f"\n[Ollama error: {e}]"
    except Exception as e:
        yield f"\n[Connection error: {e}]"


def stream_anthropic(messages: list[dict], system: str = "",
                     model: str = "claude-haiku-4-5-20251001",
                     max_tokens: int = 1024) -> Generator[str, None, None]:
    import anthropic
    api_key = st.secrets.get("ANTHROPIC_API_KEY", "")
    if not api_key:
        yield "[No ANTHROPIC_API_KEY configured. Add to .streamlit/secrets.toml]"
        return
    client = anthropic.Anthropic(api_key=api_key)
    try:
        with client.messages.stream(
            model=model,
            max_tokens=max_tokens,
            system=system,
            messages=messages,
        ) as stream:
            for text in stream.text_stream:
                yield text
    except anthropic.AuthenticationError:
        yield "[Authentication failed — check ANTHROPIC_API_KEY]"
    except anthropic.RateLimitError:
        yield "[Rate limit hit — try again in a moment]"
    except Exception as e:
        yield f"[Anthropic error: {e}]"
```

### st.write_stream Usage in Page 19

```python
# pages/19_ai_assistant.py (simplified)
import streamlit as st
from models.llm_adapters import stream_ollama, stream_anthropic, get_backend

with st.chat_message("assistant"):
    # st.write_stream exhausts the generator and returns full string
    response_text = st.write_stream(
        stream_ollama(api_messages) if get_backend() == "ollama"
        else stream_anthropic(api_messages, system=system_prompt)
    )

# After streaming, parse JSON from response_text
from models.llm_adapters import parse_llm_json
parsed = parse_llm_json(response_text)
# Render citations, follow-up chips, "Add to Board Deck" button
```

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|-----------------|--------------|--------|
| OpenAI-only SDKs | Native Ollama SDK (ollama 0.6.x) | 2024 | Local-first LLM support |
| `client.messages.create(stream=True)` raw SSE | `client.messages.stream()` context manager | 2024 | Clean text_stream iterator; no SSE parsing |
| st.html() for CSS injection | st.markdown(unsafe_allow_html=True) | Regressed in Streamlit 1.42 | Use markdown approach exclusively |
| Fine-tuning for domain knowledge | Context injection (RAG-lite) | 2024 mainstream | Zero infra cost, grounded answers |

---

## Open Questions

1. **JSON streaming display strategy**
   - What we know: st.write_stream shows raw streamed text; LLM output includes JSON wrapper
   - What's unclear: Whether a two-pass approach (stream answer, fetch metadata separately) or
     a spinner-then-display approach is preferred UX
   - Recommendation: Use spinner-then-display (buffer entire response, then show parsed answer)
     for cleaner UX. Adds ~1 extra second of latency but avoids raw JSON flash.

2. **"Add to Board Deck" write path**
   - What we know: st.session_state["ai_recommendations"] is read by page 17 topic 13
   - What's unclear: The exact structure of `ai_recommendations` that `build_topic_13()` expects
   - Recommendation: Read `models/board_export.py build_topic_13()` before implementing;
     match its expected input format.

3. **Streamlit query_params as FAB state bridge**
   - What we know: `st.query_params` is available in Streamlit 1.30+
   - What's unclear: Whether `?chat=1` in the URL causes unwanted browser history entries
   - Recommendation: Use `st.query_params.clear()` immediately after reading the param to avoid
     polluting browser history. Alternatively, skip the FAB entirely and use a sidebar button.

---

## Sources

### Primary (HIGH confidence)
- `https://github.com/ollama/ollama-python` — v0.6.2 README, streaming API, install
- `https://platform.claude.com/docs/en/build-with-claude/streaming` — Anthropic SDK streaming docs
- `https://platform.claude.com/docs/en/about-claude/models/overview` — Exact model IDs and context windows
- `https://docs.streamlit.io/develop/api-reference/write-magic/st.write_stream` — st.write_stream API signature
- `https://docs.streamlit.io/develop/tutorials/chat-and-llm-apps/build-conversational-apps` — chat state pattern
- `https://ollama.com/library/llama3.1:8b` — model context window (128k), quantization details
- Existing `app.py` lines 264-305 — confirmed working `st.markdown` fixed overlay pattern

### Secondary (MEDIUM confidence)
- `https://github.com/streamlit/streamlit/issues/10384` — st.html() CSS regression in v1.42.1
- `https://github.com/streamlit/streamlit/issues/8963` — Anthropic streaming + st.write_stream issue (use .text_stream to avoid)
- LiteLLM GitHub issues #7605, #21046 — import overhead and memory benchmarks

### Tertiary (LOW confidence)
- Windows Ollama troubleshooting pages — common issues list
- Community discussions on st.markdown persistent CSS across reruns

---

## Dependencies to Add

```
# Add to requirements.txt
ollama>=0.6.2
anthropic>=0.25
tiktoken>=0.5
```

No new Streamlit packages required. No litellm. No streamlit-float.

---

## Metadata

**Confidence breakdown:**
- Ollama SDK API: HIGH — verified from official GitHub README v0.6.2
- Anthropic SDK API: HIGH — verified from official platform docs, exact model ID confirmed
- Streamlit overlay pattern: HIGH — pattern already working in app.py for navbar
- Context window math: HIGH — verified from both Ollama library page and Anthropic docs
- LiteLLM decision: HIGH — based on measured overhead figures from official GitHub issues
- Pitfalls: HIGH — based on official docs + known Streamlit issues

**Research date:** 2026-05-07
**Valid until:** 2026-08-07 (stable libraries; check Anthropic model IDs before deployment as aliases may update)

---

## RESEARCH COMPLETE
