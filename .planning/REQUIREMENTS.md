# Requirements: LifeCycle Leverage Dashboard v1.2

**Defined:** 2026-03-28
**Core Value:** Rigorous econometric models matching thesis methodology for capital structure analysis across life stages

## v1.2 Requirements

### Dynamic Panel GMM

- [ ] **GMM-01**: System GMM estimation with lag dependent variable for full panel
- [ ] **GMM-02**: Arellano-Bond AR(1)/AR(2) serial correlation test results displayed
- [ ] **GMM-03**: Sargan/Hansen overidentification test results displayed
- [ ] **GMM-04**: GMM results table with coefficients, std errors, p-values matching thesis Table 5.12 format

### Delta-Leverage Models

- [ ] **DLV-01**: OLS/FE/RE regressions with CHANGE in leverage as dependent variable (first-difference)
- [ ] **DLV-02**: Hausman test for delta-leverage FE vs RE selection
- [ ] **DLV-03**: Stage-specific delta-leverage regressions (Startup, Growth, Maturity, Decline, Decay)
- [ ] **DLV-04**: Results displayed with coefficient comparison across stages

### Diagnostic Tests

- [ ] **TST-01**: Breusch-Pagan LM test for Pooled OLS vs RE model selection
- [ ] **TST-02**: Test results displayed with interpretation (chi-sq statistic, p-value, recommendation)

### Stage Comparisons

- [ ] **CMP-01**: Growth vs Maturity direct subset regression with pooled data
- [ ] **CMP-02**: Decline vs Decay comparison showing distinct determinants
- [ ] **CMP-03**: Side-by-side coefficient comparison table with significance indicators

### Post-COVID Cohort Analysis

- [ ] **COH-01**: Identify firms that entered Decline/Decay AFTER COVID (2022+) vs already in decline before
- [ ] **COH-02**: COVID resilience tracker — firms that improved stage post-COVID vs deteriorated
- [ ] **COH-03**: Leverage/profitability comparison between resilient and deteriorated cohorts

### UI & Integration

- [ ] **UI-01**: New page 13 "Advanced Econometrics" for GMM, delta-leverage, diagnostics, stage comparisons
- [ ] **UI-02**: COVID cohort analysis added to Knowledge Graph page (Tab 2: Event Impact) or new section
- [ ] **UI-03**: Dynamic interpretation boxes on all new outputs

### Testing

- [ ] **TEST-01**: Unit tests for GMM, delta-leverage, BP-LM model functions
- [ ] **TEST-02**: Existing 40 tests still pass (no regressions)

## v2 Requirements

### Deferred

- **MULTI-01**: Multi-country comparison — requires external datasets
- **COLL-01**: Collateral/security analysis — data not available
- **QUANT-01**: Cash flow magnitude analysis (not just +/- direction)

## Out of Scope

| Feature | Reason |
|---------|--------|
| Neo4j migration | networkx sufficient for 401 firms |
| Real-time data feeds | Thesis is historical panel data |
| PyTorch in Docker | 2GB+ dependency, graceful fallback exists |
| New data ingestion | All data already in SQLite |

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| TST-01 | Phase 1 | Pending |
| TST-02 | Phase 1 | Pending |
| DLV-01 | Phase 1 | Pending |
| DLV-02 | Phase 1 | Pending |
| DLV-03 | Phase 1 | Pending |
| DLV-04 | Phase 1 | Pending |
| GMM-01 | Phase 2 | Pending |
| GMM-02 | Phase 2 | Pending |
| GMM-03 | Phase 2 | Pending |
| GMM-04 | Phase 2 | Pending |
| TEST-01 | Phase 2 | Pending |
| CMP-01 | Phase 3 | Pending |
| CMP-02 | Phase 3 | Pending |
| CMP-03 | Phase 3 | Pending |
| UI-01 | Phase 4 | Pending |
| UI-03 | Phase 4 | Pending |
| TEST-02 | Phase 4 | Pending |
| COH-01 | Phase 5 | Pending |
| COH-02 | Phase 5 | Pending |
| COH-03 | Phase 5 | Pending |
| UI-02 | Phase 5 | Pending |

**Coverage:**
- v1.2 requirements: 21 total
- Mapped to phases: 21/21
- Unmapped: 0

---
*Requirements defined: 2026-03-28*
*Last updated: 2026-03-27 after roadmap creation*
