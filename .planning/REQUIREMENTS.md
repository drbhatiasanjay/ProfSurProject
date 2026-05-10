# Requirements: LifeCycle Leverage Dashboard v1.3

**Defined:** 2026-05-10
**Core Value:** CFOs and researchers can explore capital structure determinants, benchmark peers, export board decks, and navigate their company's position in an interactive knowledge graph — all grounded in the PhD thesis panel of 401 Indian firms (2001–2024).

## v1.3 Requirements

### CI/CD Automation

- [ ] **CICD-01**: Pushing to master triggers automated pytest run on GitHub Actions (Python 3.11, ignores smoke tests)
- [ ] **CICD-02**: Deployment to Cloud Run fires only when all tests pass (green gate)
- [ ] **CICD-03**: GitHub Actions secrets hold GCP service account credentials (no secrets in code)

### Company Timeline View

- [ ] **TMLN-01**: User can view per-company life-stage trajectory as horizontal timeline (year × stage) on page 18 Company Navigator
- [ ] **TMLN-02**: Timeline overlays leverage ratio as a line on secondary y-axis so stage transitions and leverage moves are visible together
- [ ] **TMLN-03**: Timeline is filterable by company via existing company selector on page 18

### Reproducibility Audit Trail

- [ ] **REPRO-01**: Researcher can download a JSON audit trail from Econometrics (8), ML Models (9), Scenarios (3), and Advanced Econometrics (13) pages
- [ ] **REPRO-02**: Audit JSON contains: page, panel vintage, year range, active filters, model spec (estimator/variables), n_obs, n_firms, timestamp, username

### Quality & Data Carry-forwards

- [ ] **QUAL-01**: Playwright smoke_auth.py covers pages 17 (Board Export), 18 (Company Navigator), 19 (AI Assistant) with login + render checks
- [ ] **QUAL-02**: 8 US DJIA firms with NULL tangibility have values reloaded via models/data_ingest.py; tangibility column is non-null for all us_av_2024 vintage rows

## v2 Requirements

### Deferred

- **SVDV-01**: Saved views / bookmarks — name and restore filter sets (DB layer ready, UX design deferred)
- **SCEN-01**: Scenario comparison overlay — compare N saved OLS scenarios on one chart (needs wireframe)
- **PEER-01**: Custom peer groups — user-defined named sets reusable across pages (UX placement TBD)
- **ANNO-01**: Chart annotation layer — per-user notes on time-series points (scope: per-user vs shared TBD)
- **WLIST-01**: Watchlist + stage-change email alerts (requires sending domain setup)

## Out of Scope

| Feature | Reason |
|---------|--------|
| Share / email export | Not required (user decision 2026-05-10) |
| CMIE live API integration | External blocker — API service not activated |
| PostgreSQL migration | SQLite sufficient for current user base; defer until concurrent write pressure |
| FastAPI backend layer | No API consumer today; defer until PostgreSQL migration |
| Full US S&P 500 panel | Depends on WRDS access via University of Delhi (unknown) |
| Mobile-responsive UI | Desktop-first; defer |

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| CICD-01 | Phase 8 | Pending |
| CICD-02 | Phase 8 | Pending |
| CICD-03 | Phase 8 | Pending |
| TMLN-01 | Phase 9 | Pending |
| TMLN-02 | Phase 9 | Pending |
| TMLN-03 | Phase 9 | Pending |
| REPRO-01 | Phase 10 | Pending |
| REPRO-02 | Phase 10 | Pending |
| QUAL-01 | Phase 11 | Pending |
| QUAL-02 | Phase 11 | Pending |

**Coverage:**
- v1.3 requirements: 10 total
- Mapped to phases: 10/10
- Unmapped: 0 ✓

---
*Requirements defined: 2026-05-10*
*Last updated: 2026-05-10 after milestone v1.3 start*
