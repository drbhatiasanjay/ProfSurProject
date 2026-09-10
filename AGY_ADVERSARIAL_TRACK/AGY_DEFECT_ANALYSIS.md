# AGY Defect Analysis & Remediation Plan (Adversarial Track)

## D-AGY-001: AI Chatbot Suppresses Causal Methodology Disclaimers
**Priority:** HIGH
**Component:** `pages/19_ai_assistant.py` & `models/llm_adapters.py`

### Detailed Analysis
The system uses causal adapters (like `HDFEAdapter` or `CurrentProfSurGMMAdapter`) which correctly return a `CapabilityResult` containing a strict methodology disclaimer (e.g., `_IDENTIFICATION_DISCLAIMER`) in the `message` field.
There are two execution paths in the AI Chatbot that suppress this:
1. **Fast Direct Execution Path (`pages/19_ai_assistant.py`):** The code extracts `ascii_output` and `interpretation`, but completely drops `stata_res.get("message")` when formatting `reply_content`.
2. **LLM Execution Path (`models/llm_adapters.py`):** When the AI agent (`stream_gemini_agent` or Claude) invokes the Stata tool, the JSON output contains the disclaimer. However, the LLM often summarizes the output and discards the disclaimer because the `agent_instructions` do not explicitly mandate its reproduction.

### Fix Evaluation
- **Method 1 (Prompt Engineering + Fast Path Fix):** Update the `agent_instructions` in `models/llm_adapters.py` to strictly enforce verbatim reproduction of any `METHODOLOGY GATE` or `METHODOLOGY NOTICE` returned by the tool. Simultaneously, fix the Fast Direct execution in `pages/19_ai_assistant.py` to explicitly append `stata_res.get("message")` to the `reply_content`.
- **Method 2 (UI-Layer Enforcement):** Force the tool functions (`run_stata_command`, etc.) to write any critical `message` strings into `st.session_state["_last_warnings"]`. Then, modify the chat loop in `pages/19_ai_assistant.py` to forcefully render `st.warning` outside the LLM's control.
- **Method 3 (Hard-mount via intent):** Use regex matching on user prompts in the UI to always render the disclaimer if words like "causal" or "hdfe" are detected.

### Chosen Best Method
**Method 1 (Prompt Engineering + Fast Path Fix)** combined with **Method 2 (UI-Layer Warnings)**. 
We will implement an out-of-band warning system. In `pages/19_ai_assistant.py`, we will check if the result dictionary (or the LLM's internal tool outputs) generated a warning, and we will safely render `stata_res.get("message")`. For the LLM path, updating the prompt engineering ensures the text is grounded inside the LLM context, preventing hallucinations.

**Files to be changed:**
- `pages/19_ai_assistant.py`: Add logic to append `stata_res.get("message")` to the chat response.
- `models/llm_adapters.py`: Update `agent_instructions` to require verbatim reproduction of methodology disclaimers.

---

## D-AGY-002: Backend Allows Unrestricted GMM Instrument Matrix Generation
**Priority:** CRITICAL
**Component:** `models/gmm_adapter.py` & `models/stata_engine.py`

### Detailed Analysis
When a user requests a dynamic panel GMM with excessive lags (e.g., "Run a dynamic panel GMM using lags 1 to 24 as instruments"), the `parse_stata_command` parses the command as a standard regression. The `CurrentProfSurGMMAdapter.run` currently hardcodes the creation of `lag1` to `lag4`, completely ignoring user options, and builds instruments using `lag2` and `lag3`. 
Crucially, while it calculates `instr_count` and `n_firms` and adds a warning if `instr_count > n_firms`, it **does not block the execution**. This leads to severe overfitting and violation of rule V-04 (Instrument Proliferation).

### Fix Evaluation
- **Method 1 (Strict Adapter-Level Blocking):** Modify `CurrentProfSurGMMAdapter.run` in `models/gmm_adapter.py` to evaluate the number of instruments before fitting the model. If `instr_count > n_firms` (or another hard cap like `max_lags = 4`), return an error `CapabilityResult` with `error_code="INVALID_INSTRUMENT_SPEC"` to halt the execution immediately.
- **Method 2 (Engine-Level Syntax Validation):** Update `parse_stata_command` in `models/stata_engine.py` to parse GMM-specific syntax (e.g. `lags(2 4)`) and throw a syntax error if lags > 4.
- **Method 3 (Winsorization and Matrix Clipping):** Allow the generation but silently clip the matrix using PCA or limit the instruments to the highest eigenvalues.

### Chosen Best Method
**Method 1 (Strict Adapter-Level Blocking)** combined with parsing support for the `lags()` option.
We will modify `CurrentProfSurGMMAdapter.run` to:
1. Parse the `lags` option from the `parsed.get("options")` dictionary. If not provided, default to a safe limit.
2. Hard-cap the allowed lags to a maximum of 4 to prevent excessive matrix generation.
3. Enforce `instr_count <= n_firms`. If this condition fails, return an error `CapabilityResult` (with status `error` and code `INVALID_INSTRUMENT_SPEC`) instead of proceeding with the fit.

**Files to be changed:**
- `models/gmm_adapter.py`: Implement the hard-cap and error-return logic for instrument proliferation.
- `models/stata_engine.py`: Ensure `options` parser successfully extracts the `lags` argument.

---

## Review & Merge Workflow
No code changes have been executed in the main application files. 
This analysis should be reviewed alongside Codex to ensure our chosen methods align with the system's architecture before we proceed with the implementation.
