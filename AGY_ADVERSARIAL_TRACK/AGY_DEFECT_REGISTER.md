# AGY Defect Register (Adversarial Track)

This log contains all structural, architectural, and logical vulnerabilities identified during the Deep Adversarial Test Harness executed against the isolated Stata/AI pipeline.

## Defect Summary

| ID | Target Component | Scenario | Priority | Status |
|---|---|---|---|---|
| **D-AGY-001** | AI Chatbot / Causal Adapters | Scenario A-01: Deep Causal Disclaimer Evasion | **HIGH** | Remediated; boundary tests passed; scientific validation deferred |
| **D-AGY-002** | Stata Engine / GMM Adapter | Scenario A-04: Instrument Proliferation Overfitting Evasion | **CRITICAL** | Remediated; lag-cap harness passed; scientific validation deferred |
| **D-AGY-003** | UI Renderer / Chatbot | Phase 13 Descriptive Analyst Missing Metadata | **HIGH** | Closed; `PHASE13_UI_PASS` |

---

## Detailed Defect Reports

### D-AGY-001: AI Chatbot Suppresses Causal Methodology Disclaimers
**Priority:** HIGH
**Component:** `components/chat_interface.py` & `models/stata_expansion_handlers.py`
**Description:**
When injecting a prompt to force causal language (e.g., *"prove profitability causes lower leverage using hdfe"*), the backend correctly generates the table. However, the AI Chatbot's LLM parser strips out the `AnalyticalResult.messages` or suppresses the mandatory methodology gate warning (*"Identification relies on the parallel trends assumption"*).
**Impact:**
Violation of V-03 from the Adversarial Architecture Review. Users are allowed to infer spurious causality without system-enforced methodological disclaimers.
**Remediation Required:**
The AI System Prompt must be updated to strictly mandate the verbatim inclusion of `capability_message` in the final markdown output, or the UI must hard-mount the disclaimer outside the LLM context.

**Resolution:** System instructions now require verbatim methodology notices;
the UI also hard-mounts the causal disclaimer for causal/HD FE/DiD prompts.

### D-AGY-002: Backend Allows Unrestricted GMM Instrument Matrix Generation
**Priority:** CRITICAL
**Component:** `models/stata_engine.py` & `models/gmm_adapter.py`
**Description:**
When the AI Chatbot translates the intent *"Run a dynamic panel GMM using lags 1 to 24 as instruments"*, the backend accepts the syntax and attempts to generate the massive lag matrix. It does not enforce a maximum `lag_order` limit relative to $N=401$.
**Impact:**
Violation of V-04. Generating $T(T-1)/2$ instruments for 24 periods causes severe overfitting, leading to mathematically invalid results or memory segmentation faults in extreme cases. 
**Remediation Required:**
The `CurrentProfSurGMMAdapter` must parse the lag syntax and hard-cap the instruments (e.g., maximum lag 4) or fail cleanly when instruments > $N$.

**Resolution:** Requested lags above 4 now fail closed with
`INVALID_INSTRUMENT_SPEC`, before estimation or matrix construction.

**Independent evidence:** `D_AGY_002_analysis/test_gmm_lag_cap.py` was run
against the current adapter. Lag 4 was not rejected by the cap; lag 5 returned
`INVALID_INSTRUMENT_SPEC`. This validates the safety boundary only, not GMM
scientific or numerical correctness.

### D-AGY-003: Descriptive Analyst UI Missing Required Metadata
**Priority:** HIGH
**Component:** `pages/19_ai_assistant.py` & `models/descriptive_analyst.py`
**Description:**
When executing a Phase 13 descriptive query (e.g., *"What are the average profitability and tangibility by lifecycle stage?"*) through the AI Assistant UI, the backend successfully processes the command and returns the `AnalysisRun` with proper grouped stats and provenance. However, the UI completely fails to render the required metadata labels (`COMPUTED`, `source fingerprint`, observations count). 
**Impact:**
Violation of Phase 13 UI specification which strictly requires visible auditable metadata in one response (grounding badge, scope row, sample row, reproducibility row).
**Remediation Required:**
The AI Assistant UI renderer (`_render_assistant_content` or similar) must be updated to explicitly catch the `descriptive_summary` capability ID and render its provenance metadata natively, bypassing or supplementing the LLM's raw text response.

**Resolution:** The UI now preserves and natively renders the descriptive
`AnalysisRun` metadata; a provider-independent preflight guarantees metadata
for supported descriptive requests. Antigravity result:
`PHASE13_UI_PASS`.

**Independent evidence:** `agy_defects/phase13_ui_defect_report.json` reports
`PASS` with no missing metadata and no leak markers; the backend report also
passes grouped, refusal, and reproducibility scenarios.

---

## Verified Robustness (No Defect)

The following attack vectors were successfully repelled by the system:
- **Scenario A-02 (Synchronous Thread Hanging):** The UI successfully wrapped the expensive GMM command and returned within 5 seconds without locking the Streamlit WebSocket.
- **Scenario A-03 (Dependency Sabotage):** The `MLPredictAdapter` successfully traps `ImportError` inside its `run()` boundary and fails closed gracefully instead of crashing the Streamlit server (Verified via source review).
- **Scenario A-05 (Unregistered Command Injection):** Community commands (`sgmediation`) are successfully blocked and do not evaluate against the backend.

## Evidence qualification

The new `offensive_suite/test_ivregress_adversarial.py` does not execute an IV
adapter in this workspace: it prints `IVRegress adapter not found locally` and
returns. It is retained as a future test scaffold, but must not be cited as an
IV security pass. `ivregress` remains `IMPLEMENTED_UNVERIFIED` pending a real
adapter/backend path and Phase 16 validation.
