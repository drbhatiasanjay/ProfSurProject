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
**Plans**: TBD

Plans:
- [ ] 01-01: BP-LM test function and delta-leverage model functions in econometric.py
- [ ] 01-02: Unit tests for all Phase 1 functions + regression check on existing 40 tests

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

## Progress

**Execution Order:**
Phases execute in numeric order: 1 -> 2 -> 3 -> 4 -> 5

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Delta-Leverage & Diagnostics | 0/2 | Not started | - |
| 2. System GMM | 0/2 | Not started | - |
| 3. Stage Comparisons | 0/1 | Not started | - |
| 4. Advanced Econometrics Page | 0/2 | Not started | - |
| 5. Post-COVID Cohort Analysis | 0/2 | Not started | - |
