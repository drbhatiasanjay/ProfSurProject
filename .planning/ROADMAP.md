# Roadmap: LifeCycle Leverage Dashboard v1.2 — Thesis Gap Closure

## Overview

This milestone adds five missing econometric methods from the thesis that require no new data: Breusch-Pagan LM test, delta-leverage models, System GMM, stage comparison regressions, and post-COVID cohort analysis. Backend model functions are built first with tests alongside, then surfaced through a new Advanced Econometrics page and Knowledge Graph integration. Every phase is independently deployable without breaking the existing 12 pages or 40 tests.

## Phases

**Phase Numbering:**
- Integer phases (1, 2, 3, 4, 5): Planned milestone work
- Decimal phases (e.g., 2.1): Urgent insertions (marked with INSERTED)

- [ ] **Phase 1: Delta-Leverage & Diagnostics** - BP-LM test and change-in-leverage models extending econometric.py
- [ ] **Phase 2: System GMM** - Dynamic panel GMM with Arellano-Bond and Sargan/Hansen tests
- [ ] **Phase 3: Stage Comparisons** - Growth vs Maturity and Decline vs Decay subset regressions
- [ ] **Phase 4: Advanced Econometrics Page** - New page 13 surfacing all Phase 1-3 models with interpretation
- [ ] **Phase 5: Post-COVID Cohort Analysis** - COVID cohort identification and Knowledge Graph integration
- [ ] **Phase 6: AI Financial Assistant** - Floating global chat widget + Page 19 dedicated screen; Ollama local backend; context-aware CFO/Researcher modes; Page 17 Topic 13 AI Recommendations wired
- [ ] **Phase 7: Wave 2 Tier 1 UX Quick Wins** - 8 UX improvements: download buttons on all charts/tables, loading spinners, error states, progressive disclosure (expanders), chart zoom defaults, citation generator, navbar >> arrow fix, panel selector in navbar dropdown

## Phase Details

### Phase 1: Delta-Leverage & Diagnostics
**Goal**: Researchers can run change-in-leverage regressions and Breusch-Pagan LM tests through backend functions with full test coverage
**Depends on**: Nothing (extends existing models/econometric.py)
**Requirements**: TST-01, TST-02, DLV-01, DLV-02, DLV-03, DLV-04
**Success Criteria** (what must be TRUE):
  1. Breusch-Pagan LM test function returns chi-sq statistic, p-value, and model recommendation (Pooled OLS vs RE)
  2. Delta-leverage regressions (OLS/FE/RE) run with first-differenced dependent variable and return coefficient tables
  3. Hausman test works on delta-leverage FE vs RE models and returns correct selection
  4. Stage-specific delta-leverage regressions return separate results for each Dickinson life stage
**Plans**: 2 plans

Plans:
- [ ] 01-01-PLAN.md — Harden assertions on existing 4 delta-leverage / BP-LM tests in tests/test_models.py
- [ ] 01-02-PLAN.md — Add page-13 integration smoke test + full 345-test suite gate

### Phase 2: System GMM
**Goal**: Researchers can estimate dynamic panel models with proper instrument validity diagnostics
**Depends on**: Phase 1 (confirmed no regressions in model layer)
**Requirements**: GMM-01, GMM-02, GMM-03, GMM-04, TEST-01
**Success Criteria** (what must be TRUE):
  1. System GMM estimation runs with lagged dependent variable as regressor and returns coefficient table
  2. Arellano-Bond AR(1) and AR(2) test results are computed and returned with p-values
  3. Sargan/Hansen overidentification test result is computed and returned with test statistic and p-value
  4. All new model functions (GMM + Phase 1) have passing unit tests in test_models.py
**Plans**: TBD

Plans:
- [ ] 02-01: System GMM estimation function with AR tests and Sargan/Hansen in econometric.py
- [ ] 02-02: GMM unit tests + full TEST-01 validation (all new model functions tested)

### Phase 3: Stage Comparisons
**Goal**: Researchers can directly compare leverage determinants between specific life stage pairs
**Depends on**: Phase 1 (uses regression infrastructure)
**Requirements**: CMP-01, CMP-02, CMP-03
**Success Criteria** (what must be TRUE):
  1. Growth vs Maturity subset regression runs on pooled data and returns separate coefficient sets
  2. Decline vs Decay comparison regression shows distinct determinant patterns
  3. Side-by-side coefficient table displays both stage pairs with significance stars and highlights divergent coefficients
**Plans**: TBD

Plans:
- [ ] 03-01: Stage comparison functions and coefficient table formatter

### Phase 4: Advanced Econometrics Page
**Goal**: All Phase 1-3 econometric models are accessible through an interactive Streamlit page with thesis-quality output
**Depends on**: Phases 1, 2, 3 (all backend models complete)
**Requirements**: UI-01, UI-03, TEST-02
**Success Criteria** (what must be TRUE):
  1. Page 13 "Advanced Econometrics" loads in sidebar and renders without errors
  2. User can run GMM, delta-leverage, BP-LM, and stage comparisons from the page and see formatted results
  3. Every output section has a dynamic interpretation box explaining the result in plain language
  4. All 40 existing tests plus new tests pass (no regressions in any page)
**Plans**: TBD

Plans:
- [ ] 04-01: Page 13 layout with GMM and delta-leverage tabs
- [ ] 04-02: Stage comparison tab, interpretation boxes, full regression test suite

### Phase 5: Post-COVID Cohort Analysis
**Goal**: Researchers can identify and compare firms affected by COVID through cohort analysis integrated into Knowledge Graph
**Depends on**: Phase 4 (UI patterns established, interpretation engine validated)
**Requirements**: COH-01, COH-02, COH-03, UI-02
**Success Criteria** (what must be TRUE):
  1. Post-COVID decline cohort (entered Decline/Decay after 2022) is identified and separated from pre-COVID decline firms
  2. COVID resilience tracker shows firms that improved vs deteriorated in life stage after COVID
  3. Leverage and profitability comparison between resilient and deteriorated cohorts is displayed with statistical tests
  4. Cohort analysis is accessible from the Knowledge Graph page (Event Impact section or new tab)
**Plans**: TBD

Plans:
- [ ] 05-01: COVID cohort identification and comparison functions
- [ ] 05-02: Knowledge Graph page integration with cohort visualizations

### Phase 6: AI Financial Assistant
**Goal**: A CFO or researcher can ask natural-language questions about any company or the full panel from any page in the app, and receive grounded, data-driven answers via a floating chat widget; a dedicated Page 19 supports deep multi-turn research sessions; Page 17 Board Deck Topic 13 (AI Recommendations) is powered by the same backend.
**Depends on**: Nothing (self-contained new module; integrates with existing db.py, graph_builder.py, models/)
**Requirements**: CHAT-01 through CHAT-08 (see below)
**Success Criteria** (what must be TRUE):
  1. Floating 💬 bubble is visible in the bottom-right corner on every page; clicking opens a slide-in chat panel without full page reload
  2. Chat panel auto-detects context: CFO mode on pages 17-18 (company + peer metrics injected), Researcher mode on pages 1-16 (panel OLS outputs injected)
  3. Ollama backend answers questions using only the injected context — no hallucinated financial data
  4. Claude API backend is selectable in Settings; switching backend mid-session preserves conversation history
  5. Page 19 "AI Financial Assistant" renders as a full-screen dedicated chat with multi-turn history, mode selector, and backend toggle
  6. Page 17 Topic 13 AI Recommendations calls the context builder and LLM adapter and returns ≥1 non-empty recommendation bullet per sub-topic (13.1-13.4)
  7. tests/test_chatbot.py passes with mocked LLM: context builder produces correct token-bounded output for both modes
  8. 344 + N tests pass with zero regressions

**Requirements:**
- CHAT-01: Context builder produces ≤900 token grounded context block from db.py queries (no hallucination surface)
- CHAT-02: Query classifier routes factual SQL questions vs analytical/explanatory questions vs hybrid
- CHAT-03: Ollama adapter streams responses using ollama Python SDK (local, zero data egress)
- CHAT-04: Claude API adapter streams via anthropic SDK; key in .streamlit/secrets.toml
- CHAT-05: Floating bubble injected in app.py via st.html() custom CSS/JS; no per-page modification needed
- CHAT-06: Chat state (history, mode, backend) stored in st.session_state["chat_*"] keys
- CHAT-07: Every query logged to audit_log table (existing) with llm_backend and token_count fields
- CHAT-08: "Add to Board Deck" action in chat appends narrative to st.session_state["ai_recommendations"]

**Plans**:
- [ ] 06-01: models/chatbot.py — context builder + query classifier + LLM adapters (Ollama + Claude)
- [ ] 06-02: tests/test_chatbot.py — context builder + classifier unit tests with mock LLM
- [ ] 06-03: Floating chat widget injected in app.py (HTML/CSS/JS bubble + slide-in panel)
- [ ] 06-04: pages/19_ai_assistant.py — full-screen dedicated page
- [ ] 06-05: Page 17 Topic 13 AI Recommendations wired to chatbot backend + app.py registration

### Phase 7: Wave 2 Tier 1 UX Quick Wins

**Goal**: All 8 UX improvement items shipped with zero regressions in existing 344 tests and Playwright smoke tests updated for any moved widgets.

**Depends on**: Nothing (independent UX layer, no model changes)

**Success Criteria** (what must be TRUE):

1. Every `st.dataframe()` and Plotly chart in all 18 pages has a download button (CSV/PNG)
2. Every `db.*` call outside a cache hit is wrapped in `st.spinner()`
3. No raw Python tracebacks on any page — all `db.*` calls wrapped in try/except with `st.error()` + `st.stop()`
4. Advanced options on Econometrics, ML, Clustering, Advanced Econometrics, Interaction Effects pages are in `st.expander("Advanced options", expanded=False)`
5. All time-series Plotly charts default x-axis range to `[year_range[0], year_range[1]]` from active filter
6. Citation generator (APA + LaTeX) available on Econometrics, Scenarios, Advanced Econometrics pages
7. Sidebar `>>` expand arrow has explicit `left: 0.5rem !important` CSS in `app.py`
8. Panel selector moved from sidebar radio to navbar HTML `<select>` via `st.query_params`; all 18 pages read from `st.session_state.filters["panel_mode"]` unchanged

**Plans**:

- [ ] 07-01: Foundational fixes — >> arrow CSS, spinners, error states (W2-07, W2-02, W2-03)
- [ ] 07-02: helpers.py chart zoom + progressive disclosure expanders (W2-05, W2-04)
- [ ] 07-03: Download buttons — systematic pass all 18 pages (W2-01)
- [ ] 07-04: Citation generator on 3 pages (W2-06)
- [ ] 07-05: Panel selector → navbar dropdown via query_params (W2-08)

## Progress

**Execution Order:**
Phases 1-5 execute in numeric order (thesis gap closure); Phase 6 is independent and can execute any time. Phase 7 is independent UX work — can execute in parallel with any phase.

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Delta-Leverage & Diagnostics | 0/2 | Not started | - |
| 2. System GMM | 0/2 | Not started | - |
| 3. Stage Comparisons | 0/1 | Not started | - |
| 4. Advanced Econometrics Page | 0/2 | Not started | - |
| 5. Post-COVID Cohort Analysis | 0/2 | Not started | - |
| 6. AI Financial Assistant | 0/5 | Not started | - |
| 7. Wave 2 Tier 1 UX Quick Wins | 0/5 | Not started | - |
