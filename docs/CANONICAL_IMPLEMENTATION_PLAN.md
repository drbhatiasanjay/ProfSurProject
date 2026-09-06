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

### 2.4 End-to-End User Journeys with Concrete Examples

#### Journey 1A: Causal Identification & 2SLS Endogeneity Correction
- **Persona:** PhD Scholar / Econometric Researcher investigating whether asset tangibility causally determines leverage or suffers from reverse causality.
- **User Action:**
  1. Opens Stata Studio (`pages/23_stata_studio.py`).
  2. Selects `💻 Stata CLI Mode`.
  3. Clicks the one-click causal template button: `⚖️ . ivregress 2sls (tang=L.tang)`.
     *(Or manually types: `ivregress 2sls leverage (tangibility = L.tangibility) profitability log_size, small`)*.
  4. Clicks `▶ Run Command` (or presses Enter).
- **Backend Execution (`models/stata_engine.py`):**
  - AST parser splits exogenous covariates (`profitability`, `log_size`) from the instrument equation `(tangibility = L.tangibility)`.
  - Panel lag operator `L.` generates 1-year lagged tangibility grouped by `company_code` along the panel index `(company_code, year)`.
  - Estimates Two-Stage Least Squares via `linearmodels.iv.IV2SLS`.
  - Computes First-Stage diagnostic $F$-statistic, second-stage coefficients, asymptotic $z$-statistics, robust $p$-values, and 95% confidence intervals.
- **Frontend UI Display:**
  - Monospace ASCII Stata 18 terminal output displays full regression banner:
    ```stata
    . ivregress 2sls leverage (tangibility = L.tangibility) profitability log_size
    Instrumental variables (2SLS) regression          Number of obs   =      8276
                                                      Wald chi2(3)    =    148.92
                                                      Prob > chi2     =    0.0000
                                                      R-squared       =    0.1842
    ------------------------------------------------------------------------------
        leverage | Coefficient  Std. err.      z    P>|z|     [95% conf. interval]
    -------------+----------------------------------------------------------------
     tangibility |   0.284192   0.041284    6.88   0.000      0.203277    0.365107
    profitability|  -0.341209   0.038192   -8.93   0.000     -0.416064   -0.266354
        log_size |   0.051284   0.008912    5.75   0.000      0.033817    0.068751
           _cons |   0.114209   0.024185    4.72   0.000      0.066807    0.161611
    ------------------------------------------------------------------------------
    Instrumented: tangibility
    Instruments:  profitability log_size L.tangibility
    ```
  - Live Econometric Explainer card appears above terminal with 4-quadrant analysis:
    - **🎯 Research Intent:** Resolves simultaneous endogeneity between asset tangibility and borrowing capacity.
    - **🔬 Identification:** Uses predetermined lagged collateral ($L.\text{tangibility}$) as an instrumental variable ($Cov(Z, X) \neq 0$, $Cov(Z, \epsilon) = 0$).
    - **📐 Statistical Inference:** First-stage $F > 10$ rules out weak instrument bias; positive $\beta = 0.284$ ($p < 0.001$) confirms robust collateral channel.
    - **🏛 Economic Theory:** Supports Trade-Off Theory over Pecking Order by confirming tangibility expands debt capacity.

#### Journey 1B: Post-Estimation Wald Hypothesis Testing & Linear Predictions
- **Persona:** Empirical Quantitative Analyst evaluating parameter restrictions and generating fitted values.
- **User Action:**
  1. Immediately following the 2SLS or Fixed Effects estimation, clicks `🧪 . test roa = 0` (or types `test profitability = 0`).
  2. Terminal displays post-estimation restriction:
     ```stata
     . test profitability = 0
      ( 1)  profitability = 0

            F(  1,  8275) =  142.31
                 Prob > F =  0.0000
     ```
  3. User types: `predict y_hat, xb` and clicks Run.
  4. System computes $\hat{y} = \sum \hat{\beta}_j X_j$ using Cython-safe vectorization, stores `y_hat` into the active working dataframe `st.session_state["stata_working_df"]`, and reports:
     ```stata
     . predict y_hat, xb
     (variable y_hat generated as linear prediction xb)
     Observations: 8,276 | Mean: 0.2184 | Std: 0.1412 | Min: -0.0412 | Max: 0.8914
     ```

#### Journey 1C: Natural Language Querying with Real-Time Syntax Highlighting
- **Persona:** CFO / Board Advisor seeking quick econometric evidence without memorizing Stata commands.
- **User Action:**
  1. Switches mode toggle to `💬 Natural Language Query`.
  2. Enters: *"Show me how debt responds to profitability with firm clustering"*.
  3. System translates query in real time using deterministic AST matching to:
     `. xtreg leverage profitability tangibility log_size, fe cluster(company_code)`
  4. User views active variable chips (`leverage`, `profitability`, `tangibility`) and syntax preview.
  5. Presses Enter: executes panel fixed-effects regression seamlessly.

#### Journey 1D: Outlier Winsorization & Data Hygiene
- **Persona:** Data Scientist cleaning noisy financial ratios.
- **User Action:**
  1. Clicks `✂️ . winsor2 cuts(1 99)` (or types `winsor2 leverage profitability tangibility, cuts(1 99) replace`).
  2. Engine clamps extreme tail outliers to 1st and 99th percentiles in the isolated session copy `st.session_state["stata_working_df"]`.
  3. User inspects cleaned distribution; if needed, clicks `↺ Reset Data` to instantly restore pristine baseline panel data.

---

### 2.6 Technical Architecture & Affected Files
| File Path | Nature | Layer | Purpose |
| :--- | :---: | :---: | :--- |
| `models/stata_engine.py` | `[MODIFY]` | BE | Add parsing & computation routines for `ivregress 2sls` (via `linearmodels.iv`), `test`, `predict`, and `winsor2`. |
| `models/stata_nl_translator.py` | `[NEW]` | BE | Deterministic & AST mapping of natural language queries to valid Stata syntax with variable disambiguation. |
| `models/stata_explainer.py` | `[NEW]` | BE | Econometric deconstruction engine generating structured breakdowns (Intent, Identification, Inference, Theory). |
| `components/stata_editor.py` | `[NEW]` | FE | Streamlit syntax-colored CLI editor component with active-panel column autocompletion dropdown. |
| `pages/23_stata_studio.py` | `[MODIFY]` | FE | Mount Dual-Mode toggle (NL vs. Stata), embed `stata_editor`, and mount the live Explainer card. |
| `tests/test_stata_bidirectional_nlp.py` | `[NEW]` | BE/QA | TDD test suite for commands, translation pairs, and explainer schemas. |

### 2.7 Explicit Non-Goals
- Do NOT rewrite or modify existing working estimators (`xtreg`, `hausman`, `xttest0`).
- Do NOT run local LLM models (e.g. Ollama); use deterministic AST parsing with configured cloud API fallbacks.

### 2.8 TDD RED Test Specifications
Authored in `tests/test_stata_bidirectional_nlp.py`:
- `TC-ST-01`: `ivregress 2sls leverage (tangibility = L.tangibility) roa size` returns second-stage coefficients and Hansen/Sargan diagnostic.
- `TC-ST-02`: `test roa = 0` after `xtreg` returns valid Wald $F$-statistic and p-value.
- `TC-ST-03`: `predict y_hat, xb` calculates linear prediction vector and stores it in session state.
- `TC-ST-04`: `winsor2 leverage roa tang, cuts(1 99) replace` clamps extreme outliers to 1st and 99th percentiles.
- `TC-NL-01` to `TC-NL-10`: 10 positive NL translations (e.g., *"Show me how debt responds to profitability with firm clustering"* $\rightarrow$ `xtreg leverage profitability tangibility log_size, fe cluster(company_code)`).
- `TC-NL-ERR`: Sanitization against destructive commands (`DROP`, `DELETE`, SQL injections).

### 2.9 Acceptance Criteria
- 100% of new unit tests pass in `tests/test_stata_bidirectional_nlp.py`.
- Regression suite `py -3.12 scripts/project_ops.py test --fast` remains 100% green.
- Stata Studio terminal displays valid monospace ASCII output for all 4 gap commands.

---

## 3. Workstream 2: Citation Inspector / Academic Literature Vault

### 3.1 User Intent & Problem Statement
Academics, peer reviewers, and CFOs require immediate verification of empirical benchmarks against peer-reviewed literature. Static text citations must be elevated into an interactive inspection experience providing DOIs, theoretical mechanisms, empirical coefficients from literature, and corroboration against the Indian panel ($N=8,677$, CMIE Prowess 2001–2025).

### 3.2 Existing Capabilities (Reconciliation Baseline)
- Comprehensive static literature catalog in `models/econometric_literature_vault.py` with 100% prompt coverage across 46 prompts.
- High-contrast categorized badges in `models/rich_chat_renderer.py` (`METHODOLOGY`, `JOURNAL OF FINANCE`, `INSTITUTIONAL REPORT`, `EMPIRICAL LITERATURE`).

### 3.3 Remaining Gaps
- Badges are static HTML `<span>` elements without click events or interactive triggers.
- Citations lack structured machine-readable metadata (verified HTTPS DOI links, theoretical channel tags, empirical coefficients from literature).
- No native Streamlit `@st.dialog` modal exists to inspect citations.

### 3.4 End-to-End User Journeys with Concrete Examples

#### Journey 2A: Interactive Scholarly Inspection in Stata Studio
- **Persona:** Academic Journal Referee reviewing empirical capital structure findings for publication.
- **User Action:**
  1. Opens Stata Studio (`pages/23_stata_studio.py`) and inspects the 3-tier Scholarly Commentary card below a fixed-effects model.
  2. Reads theoretical comparison referencing Dickinson (2011) life cycle dynamics.
  3. Clicks the interactive badge button: `📖 Inspect Citation: Dickinson (2011)`.
- **Backend Execution (`models/citation_vault_metadata.py` & `components/citation_inspector.py`):**
  - Component retrieves canonical metadata record for `"Dickinson (2011)"`.
  - Formats bibliographic citations, DOI URI, theoretical mechanisms, and empirical Indian panel context.
  - Invokes `@st.dialog("Academic Citation Inspector: Dickinson (2011)")`.
- **Frontend UI Display:**
  - Modal overlay renders smoothly over the active page without causing a full page refresh:
    - **Header:** Verified Peer-Reviewed Publication badge + Journal name (*The Accounting Review*, 86(6)).
    - **Verified DOI Link:** Clickable button linking to `https://doi.org/10.2308/accr-10130`.
    - **Theoretical Mechanism:** 8-stage cash flow sign classification (Operating, Investing, Financing).
    - **Empirical Benchmark Table:**
      - US Life Cycle distribution vs Indian Manufacturing Panel ($N=8,677$): Maturity (51.8% vs 45.2%), Growth (22.3% vs 28.2%).
    - **Citation Export Tabs:**
      - `BibTeX`: Copyable `@article{dickinson2011cash...}` block.
      - `APA 7th`: Dickinson, V. (2011). Cash flow patterns as a proxy for firm life cycle...
      - `Stata Do-File`: `* Citation: Dickinson (2011) TAR 86(6): 1969-1994`.
  - Closing modal (Esc or click outside) retains all active Stata results and terminal state intact.

#### Journey 2B: Contextual Literature Verification in AI Financial Assistant
- **Persona:** CFO / Treasury Director querying optimal leverage thresholds.
- **User Action:**
  1. Navigates to AI Financial Assistant (`pages/19_ai_assistant.py`).
  2. Selects prompt: *"Pecking Order vs Trade-Off Theory in Indian Mature Firms"*.
  3. Assistant returns comprehensive analysis with citation chips: `[Myers & Majluf (1984)]` and `[Rajan & Zingales (1995)]`.
  4. User clicks `[Rajan & Zingales (1995)]`.
- **Frontend UI Display:**
  - Citation Inspector modal opens instantly with Rajan & Zingales (1995) cross-country leverage determinants, demonstrating how Indian manufacturing tangibility coefficients ($\beta \approx +0.28$) mirror G7 empirical benchmarks.

---

### 3.5 Technical Architecture & Affected Files
| File Path | Nature | Layer | Purpose |
| :--- | :---: | :---: | :--- |
| `models/citation_vault_metadata.py` | `[NEW]` | BE | Canonical structured catalog of peer-reviewed literature containing verified DOIs, mechanisms, and Indian panel relevance. |
| `components/citation_inspector.py` | `[NEW]` | FE | Native `@st.dialog("Academic Citation Inspector")` modal component displaying structured metadata, DOI links, and BibTeX export. |
| `models/rich_chat_renderer.py` | `[MODIFY]` | FE | Attach interactive trigger markup / buttons to citation badges. |
| `pages/23_stata_studio.py` | `[MODIFY]` | FE | Connect Stata Studio scholarly commentary cards to the Citation Inspector modal. |
| `pages/19_ai_assistant.py` | `[MODIFY]` | FE | Connect AI Assistant citation badges to the Citation Inspector modal. |
| `tests/test_citation_inspector.py` | `[NEW]` | BE/QA | TDD validation of dictionary schema, valid DOI URL formatting, and modal state transitions. |

### 3.6 Explicit Non-Goals
- Do NOT delete or modify existing narrative text in `models/econometric_literature_vault.py`.
- Do NOT fetch external web URLs at runtime; all metadata must be compiled statically inside `models/citation_vault_metadata.py`.

### 3.7 TDD RED Test Specifications
Authored in `tests/test_citation_inspector.py`:
- `TC-CIT-01`: Query for `"Dickinson (2011)"` returns title, theory, cash flow mechanism, valid HTTPS DOI, and Indian panel application note.
- `TC-CIT-02`: Query for `"Rajan & Zingales (1995)"` returns cross-country benchmark and valid HTTPS DOI.
- `TC-CIT-03`: Unindexed citation query falls back gracefully to core textbook foundations without raising `KeyError`.
- `TC-CIT-04`: Verified DOI strings validate against RFC 3986 URI format (`https://doi.org/...`).

### 3.8 Acceptance Criteria
- 100% of unit tests pass in `tests/test_citation_inspector.py`.
- Clicking a citation badge in Stata Studio or AI Assistant triggers the `@st.dialog` modal cleanly.
- Esc or clicking outside dismisses modal without resetting active econometric models or terminal outputs.

---

## 4. Architectural File Discovery Methodology: How We Know Which Files Need To Be Changed

To prevent speculative edits, scope creep, and breaking changes, our file identification process follows a deterministic 3-tier discovery methodology:

```
[Entry Points: User Interactions & Routes]
                │
                ▼
[Static AST & Graphify Call-Graph Mapping]
  - Trace callers and callees via codebase-memory-mcp & graphify
  - Identify dataflow contracts & state schemas
                │
                ▼
[Isolated Functional Boundaries (FE vs. BE)]
  - Models (stateful computation, business rules)
  - Components (reusable atomic UI widgets)
  - Pages (Streamlit routing & orchestration)
```

1. **AST Call-Graph & Symbol Tracing (`graphify` & `codebase-memory-mcp`):**
   - We inspect `graphify-out/GRAPH_REPORT.md` and query AST symbols (e.g. `execute_stata_command`, `render_rich_card`).
   - For **Workstream 1**, tracing `execute_stata_command` revealed the exact dispatch dictionary in `models/stata_engine.py` and its consumer in `pages/23_stata_studio.py`. By isolating parser additions inside dedicated helper handlers (`_handle_ivregress`, `_handle_test`, etc.), the existing 20 dispatch verbs remained mathematically untouched.
   - For **Workstream 2**, tracing literature badge rendering revealed that `models/rich_chat_renderer.py` and `models/econometric_literature_vault.py` produce static HTML strings consumed by `pages/19_ai_assistant.py` and `pages/23_stata_studio.py`. By placing the structured metadata dictionary in `models/citation_vault_metadata.py` and dialog UI in `components/citation_inspector.py`, we introduce zero breaking changes to existing narrative text.
2. **Streamlit Lifecycle & State Boundary Analysis:**
   - Streamlit re-executes top-to-bottom on every interaction. Files that mutate session state (`st.session_state`) must be strictly segregated from read-only display modules.
   - Example: Adding `winsor2 ... replace` required an isolated session copy `st.session_state["stata_working_df"]` so cached database queries in `db.py` remain immutable.

---

## 5. First-Time-Right (FTR) Quality Assurance Framework: How We Ensure It Works First Time

"First-Time-Right" engineering is enforced through a multi-tier defense system that prevents bugs from escaping into the working tree:

```
[1. TDD RED Phase] ────► [2. Minimal-Code GREEN] ────► [3. Mathematical Boundary Check]
                                                                   │
[6. Zero-Leak Gate] ◄──── [5. Headless Browser E2E] ◄──── [4. Automated Regression Suite]
```

1. **Strict TDD RED-GREEN-REFACTOR Cycle:**
   - Tests defining boundary conditions, edge cases, error modes, and schemas are authored *first* and confirmed failing (100% RED).
   - Functional implementation is written *only* to satisfy the failing assertions (GREEN), followed by clean refactoring.
2. **Ponytail Minimal-Code Principle (AGENTS.md Directives):**
   - Evaluate code necessity before writing: *Does this strictly need to exist? Can we reuse existing functions?*
   - Avoid heavy external dependencies; use Python standard libraries and native Streamlit primitives (`@st.dialog`, `st.columns`).
3. **Mathematical & Econometric Boundary Validation:**
   - Verify identification degrees of freedom ($l \ge k$), rank conditions, and collinearity handling before passing matrices to `linearmodels` or `statsmodels`.
   - Protect against Cython buffer mismatches by avoiding index type coercion during linear prediction.
4. **Automated Regression Suite:**
   - Execute `py -3.12 scripts/project_ops.py test --fast` and full test suites to prove that existing features (all 20 baseline Stata verbs, 19 Phase-3 command cases, 46 AI prompt categories) suffer zero regression.
5. **Headless Browser End-to-End Verification (Playwright):**
   - Automatically launch the application in headless Chromium, authenticate with configured credentials, navigate across target pages, trigger button clicks, execute commands, verify DOM contents, confirm zero traceback errors, and capture screenshot evidence in `scratch/`.
6. **Zero Plaintext Credential Leaks (`SECRET_SCAN: CLEAN`):**
   - Every staged diff is scanned using regex patterns for credential patterns before any commit is executed.

---

## 6. Complete Frontend (FE) & Backend (BE) Change Breakdown for Both Workstreams

| Workstream | Layer | File | Nature | Changes & Responsibilities |
| :--- | :---: | :--- | :---: | :--- |
| **WS1: Stata CLI / NLP** | **BE** | `models/stata_engine.py` | `[MODIFY]` | Adds formula parser for `(endog = instruments)`, lag operator `L.` on panel index, and handlers `_handle_ivregress()`, `_handle_test()`, `_handle_predict()`, `_handle_winsor2()`. |
| **WS1: Stata CLI / NLP** | **BE** | `models/stata_nl_translator.py` | `[NEW]` | Deterministic regex and AST natural language query translator with strict SQL/system injection sanitization. |
| **WS1: Stata CLI / NLP** | **BE** | `models/stata_explainer.py` | `[NEW]` | Econometric deconstruction engine generating 4-quadrant structured interpretations (*Intent, Identification, Inference, Economic Theory*). |
| **WS1: Stata CLI / NLP** | **FE** | `components/stata_editor.py` | `[NEW]` | Dual-mode input bar (`Stata CLI` vs `Natural Language`) with active-panel variable quick-insert chips and token-level syntax highlighting. |
| **WS1: Stata CLI / NLP** | **FE** | `pages/23_stata_studio.py` | `[MODIFY]` | Embeds Dual-Mode editor, causal/diagnostic template buttons (`2SLS`, `test`, `predict`, `winsor2`, `Reset Data`), session working dataset isolation, and live Explainer card. |
| **WS1: Stata CLI / NLP** | **QA** | `tests/test_stata_bidirectional_nlp.py` | `[NEW]` | 8 unit tests covering IV estimation, Wald test, linear predictions, winsorization, 10 NL queries, injection sanitization, and explainer schema. |
| **WS2: Citation Inspector** | **BE** | `models/citation_vault_metadata.py` | `[NEW]` | Canonical catalog containing structured metadata (verified DOIs, theoretical mechanisms, empirical coefficients, Indian panel relevance, BibTeX/APA). |
| **WS2: Citation Inspector** | **FE** | `components/citation_inspector.py` | `[NEW]` | Native `@st.dialog` modal component rendering paper title, verified HTTPS DOI link, theoretical mechanism breakdown, benchmark comparisons, and copyable citation formats. |
| **WS2: Citation Inspector** | **FE** | `models/rich_chat_renderer.py` | `[MODIFY]` | Adds clickable inspection badge triggers to rendered citation tags. |
| **WS2: Citation Inspector** | **FE** | `pages/23_stata_studio.py` | `[MODIFY]` | Connects Stata Studio 3-tier commentary cards and PhD figure citations to Citation Inspector dialog. |
| **WS2: Citation Inspector** | **FE** | `pages/19_ai_assistant.py` | `[MODIFY]` | Connects AI Assistant literature response badges to Citation Inspector dialog. |
| **WS2: Citation Inspector** | **QA** | `tests/test_citation_inspector.py` | `[NEW]` | Unit tests validating metadata completeness, DOI URI formatting, fallback handling, and dialog state transitions. |

