# Canonical Implementation Plan: Stata CLI & Citation Inspector

**Operational Role:** Authoritative Technical Specification for Approved Workstreams 1 & 2  
**Provenance:** Derived from historical Antigravity recovery artifact (`dfad8734-d349-4cab-bff4-d88cf51c2925/implementation_plan.md`, Last Write `2026-09-06 00:14:39 IST`), reconciled against `master` at `6075708`, active codebase, and verified Phase 1–6 test evidence.

---

## 1. Branch Strategy & Non-Negotiable Invariants
Both workstreams must be implemented on two independent feature branches created from the SAME approved recovery/context commit on `master`. Neither branch may be created from the other.

```
master (recovery/context commit)
   │
   ├── feature/stata-cli-nlp-highlighting (Workstream 1)
   │      ├── Gap Parsers in models/stata_engine.py (ivregress 2sls, test, predict, winsor2)
   │      ├── Syntax Editor & Autocomplete in components/stata_editor.py
   │      ├── Bidirectional NL ↔ Stata Translator in models/stata_nl_translator.py
   │      └── Econometric Explainer Card in models/stata_explainer.py & pages/23_stata_studio.py
   │
   └── feature/citation-inspector-modal (Workstream 2)
          ├── Scholarly Metadata Catalog in models/citation_vault_metadata.py
          ├── Interactive @st.dialog Modal in components/citation_inspector.py
          └── Badge Trigger Callbacks across Stata Studio & AI Assistant
```

### Invariants & Independent Lifecycle Requirements:
- **Independent Lifecycles:** Each branch requires its own independent TDD RED phase, TDD GREEN phase, regression verification, UI verification, review gate, and merge decision.
- **Strict TDD:** Tests must be authored and confirmed failing (RED) before writing functional implementation (GREEN), followed by minimal refactoring.
- **Zero Regression:** All 19 exhaustively verified Phase-3 Stata commands and all 20 currently implemented top-level dispatch verbs in `models/stata_engine.py`, as well as all 46 AI Assistant prompts, must retain 100% PASS rates.
- **No Third Workstream:** The post-restart AutoPrompt proposal is strictly non-canonical and excluded.
- **Non-Destructive Standard:** Existing data loaders in `db.py`, panels, and CSS styling remain intact.

---

## 2. Workstream 1: Stata CLI / NLP Enhancement

### 2.1 User Intent & Problem Statement
Researchers and CFOs require the ability to:
1. Run advanced causal and diagnostic routines directly within Stata Studio (`ivregress 2sls`, `test`, `predict`, `winsor2`).
2. Input intuitive Natural Language econometric queries that reliably translate to valid Stata syntax.
3. Receive plain-English econometric explanations (Intent, Identification, Inference, Economic Theory) directly above the terminal output.
4. Benefit from responsive syntax highlighting and active panel variable autocompletion.

### 2.2 Existing Capabilities (Reconciliation Baseline)
- Core panel fixed/random effects (`xtreg, fe/re`), clustering (`cluster(company_code)`), standard error corrections, `hausman`, `estat vif`, `xttest0`, `xtserial`, `margins`, `esttab` LaTeX/Word export, and `coefplot` whiskers are fully functional.
- 1-click Light/Dark contrast toggle is already operational in `pages/23_stata_studio.py`.

### 2.3 Remaining Gaps
- `models/stata_engine.py` throws syntax errors on `ivregress`, `test`, `predict`, and `winsor2`.
- `pages/23_stata_studio.py` uses standard uncolored `st.text_input` without auto-suggesting panel columns.
- No bidirectional Natural Language ↔ Stata translation engine exists.
- Stata Studio lacks an attached plain-English econometric explanation card.

### 2.4 Technical Architecture & Affected Files
| File Path | Nature | Purpose |
| :--- | :---: | :--- |
| `models/stata_engine.py` | `[MODIFY]` | Add parsing & computation routines for `ivregress 2sls` (via `linearmodels.iv`), `test`, `predict`, and `winsor2`. |
| `models/stata_nl_translator.py` | `[NEW]` | Deterministic & LLM-assisted mapping of natural language queries to valid Stata syntax with variable disambiguation. |
| `models/stata_explainer.py` | `[NEW]` | Econometric deconstruction engine generating structured breakdowns (Intent, Identification, Inference, Theory). |
| `components/stata_editor.py` | `[NEW]` | Streamlit syntax-colored CLI editor component with active-panel column autocompletion dropdown. |
| `pages/23_stata_studio.py` | `[MODIFY]` | Mount Dual-Mode toggle (NL vs. Stata), embed `stata_editor`, and mount the live Explainer card. |
| `tests/test_stata_bidirectional_nlp.py` | `[NEW]` | TDD test suite for commands, translation pairs, and explainer schemas. |

### 2.5 Explicit Non-Goals
- Do NOT rewrite or modify existing working estimators (`xtreg`, `hausman`, `xttest0`).
- Do NOT run local LLM models (e.g. Ollama); use deterministic AST parsing with configured cloud API fallbacks.

### 2.6 TDD RED Test Specifications
Authored in `tests/test_stata_bidirectional_nlp.py`:
- `TC-ST-01`: `ivregress 2sls leverage (tangibility = L.tangibility) roa size` returns second-stage coefficients and Hansen/Sargan diagnostic.
- `TC-ST-02`: `test roa = 0` after `xtreg` returns valid Wald $F$-statistic and p-value.
- `TC-ST-03`: `predict y_hat, xb` calculates linear prediction vector and stores it in session state.
- `TC-ST-04`: `winsor2 leverage roa tang, cuts(1 99) replace` clamps extreme outliers to 1st and 99th percentiles.
- `TC-NL-01` to `TC-NL-10`: 10 positive NL translations (e.g., *"Show me how debt responds to profitability with firm clustering"* $\rightarrow$ `xtreg leverage profitability tangibility log_size, fe cluster(company_code)`).
- `TC-NL-ERR`: Sanitization against destructive commands (`DROP`, `DELETE`, SQL injections).

### 2.7 Acceptance Criteria
- 100% of new unit tests pass in `tests/test_stata_bidirectional_nlp.py`.
- Regression suite `py -3.12 scripts/project_ops.py test --fast` remains 100% green.
- Stata Studio terminal displays valid monospace ASCII output for all 4 gap commands.

---

## 3. Workstream 2: Citation Inspector / Academic Literature Vault

### 3.1 User Intent & Problem Statement
Academics, reviewers, and CFOs require immediate verification of econometric empirical benchmarks against peer-reviewed literature. Static text citations must be elevated into an interactive inspection experience providing DOIs, theoretical mechanisms, and corroboration against the Indian panel ($N=8,677$).

### 3.2 Existing Capabilities (Reconciliation Baseline)
- Comprehensive static literature catalog in `models/econometric_literature_vault.py` with 100% prompt coverage across 46 prompts.
- High-contrast categorized badges in `models/rich_chat_renderer.py` (`METHODOLOGY`, `JOURNAL OF FINANCE`, `INSTITUTIONAL REPORT`, `EMPIRICAL LITERATURE`).

### 3.3 Remaining Gaps
- Badges are static HTML `<span>` elements without click events or interactive triggers.
- Citations lack structured machine-readable metadata (verified HTTPS DOI links, theoretical channel tags, empirical coefficients from literature).
- No native Streamlit `@st.dialog` modal exists to inspect citations.

### 3.4 Technical Architecture & Affected Files
| File Path | Nature | Purpose |
| :--- | :---: | :--- |
| `models/citation_vault_metadata.py` | `[NEW]` | Canonical structured dictionary of peer-reviewed literature containing verified DOIs, mechanisms, and Indian panel relevance. |
| `components/citation_inspector.py` | `[NEW]` | Native `@st.dialog("Academic Citation Inspector")` modal component displaying structured metadata and external links. |
| `models/rich_chat_renderer.py` | `[MODIFY]` | Attach interactive trigger markup to citation badges. |
| `pages/23_stata_studio.py` | `[MODIFY]` | Connect Stata Studio econometric benchmarks to the Citation Inspector modal. |
| `pages/19_ai_assistant.py` | `[MODIFY]` | Connect AI Assistant citation badges to the Citation Inspector modal. |
| `tests/test_citation_inspector.py` | `[NEW]` | TDD validation of dictionary schema, valid DOI URL formatting, and modal state transitions. |

### 3.5 Explicit Non-Goals
- Do NOT delete or modify existing narrative text in `models/econometric_literature_vault.py`.
- Do NOT fetch external web URLs at runtime; all metadata must be compiled statically inside `models/citation_vault_metadata.py`.

### 3.6 TDD RED Test Specifications
Authored in `tests/test_citation_inspector.py`:
- `TC-CIT-01`: Query for `"Dickinson (2011)"` returns title, theory, cash flow mechanism, valid HTTPS DOI, and Indian panel application note.
- `TC-CIT-02`: Query for `"Rajan & Zingales (1995)"` returns cross-country benchmark and valid HTTPS DOI.
- `TC-CIT-03`: Unindexed citation query falls back gracefully to core textbook foundations without raising `KeyError`.
- `TC-CIT-04`: Verified DOI strings validate against RFC 3986 URI format.

### 3.7 Acceptance Criteria
- 100% of unit tests pass in `tests/test_citation_inspector.py`.
- Clicking a citation badge in Stata Studio or AI Assistant triggers the `@st.dialog` modal cleanly.
- Esc or clicking outside dismisses modal without resetting active econometric models or terminal outputs.

---

## 4. Dependencies, Risks & Verification Protocol
- **Dependencies:** `linearmodels` (IV/2SLS estimation), `statsmodels` (hypothesis testing), Streamlit $\ge 1.37$ (`@st.dialog`).
- **Risks:**
  - *Regression Risk:* Adding parsers to `stata_engine.py` might break existing commands. *Mitigation:* Full regression run of `test_all_19_stata_math.py` on every commit.
  - *UI State Reset Risk:* Triggering modals in Streamlit can reset session state. *Mitigation:* Store active command and estimates in `st.session_state["_stata_active_estimate"]`.
