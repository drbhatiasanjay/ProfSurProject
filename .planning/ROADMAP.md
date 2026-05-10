# Roadmap: LifeCycle Leverage Dashboard v1.3 — Automation & Analytical Depth

## Overview

Four independent improvements: GitHub Actions CI/CD so every push auto-deploys, a company timeline view on page 18 showing life-stage trajectory with leverage overlay, a reproducibility audit trail JSON on the four core analytics pages, and two quality carry-forwards (smoke tests for pages 17-19, 8 US firms NULL tangibility fix). All phases are independent and execute in parallel.

## Phases

- [ ] **Phase 8: CI/CD Pipeline** — GitHub Actions test-gate + Cloud Run auto-deploy on push to master
- [ ] **Phase 9: Company Timeline View** — Per-company life-stage trajectory + leverage overlay on page 18
- [ ] **Phase 10: Reproducibility Audit Trail** — JSON audit export on pages 3, 8, 9, 13
- [ ] **Phase 11: Quality Carry-forwards** — smoke_auth.py pages 17-19 + 8 US firms NULL tangibility fix

## Phase Details

### Phase 8: CI/CD Pipeline
**Goal**: Every push to master automatically runs the full test suite and deploys to Cloud Run only when tests pass — eliminating manual deploy commands
**Depends on**: Nothing (infra-only, no app code changes)
**Requirements**: CICD-01, CICD-02, CICD-03
**Success Criteria** (what must be TRUE):
  1. `.github/workflows/deploy.yml` exists and defines test + deploy jobs
  2. Test job runs `pytest tests/ --ignore=tests/smoke_auth.py --ignore=tests/smoke_phase1.py` on Python 3.11
  3. Deploy job runs only after test job succeeds (needs: test)
  4. GCP service account credentials are stored as GitHub secret `GCP_SA_KEY`, not in code
  5. Pushing a commit to master triggers the workflow (verified via GitHub Actions UI or workflow run log)
**Plans**: 1 plan

Plans:
- [ ] 08-01: GitHub Actions workflow file + GCP service account setup instructions

---

### Phase 9: Company Timeline View
**Goal**: A user on page 18 Company Navigator can select any company and see its full life-stage trajectory year-by-year, with leverage ratio overlaid, revealing how leverage moves through stage transitions
**Depends on**: Nothing (new tab on existing page 18)
**Requirements**: TMLN-01, TMLN-02, TMLN-03
**Success Criteria** (what must be TRUE):
  1. Page 18 has a "Timeline" tab alongside existing Ego Graph / Peer Cluster / Stage Map tabs
  2. Timeline renders a Plotly figure with years on x-axis and life stage on y-axis (color-coded by STAGE_COLORS)
  3. Leverage ratio appears as a line on secondary y-axis (right side)
  4. Selecting a different company from the sidebar updates the timeline
  5. Page loads without errors for at least 3 test companies (e.g., 22859, 10000, 15000)
**Plans**: 1 plan

Plans:
- [ ] 09-01: Timeline tab on page 18 — stage trajectory + leverage overlay

---

### Phase 10: Reproducibility Audit Trail
**Goal**: A researcher on any of the four core analytics pages can download a JSON file that fully specifies the analysis they just ran — panel vintage, filters, model spec, observation count — enabling exact reproduction
**Depends on**: Nothing (additive widget on existing pages)
**Requirements**: REPRO-01, REPRO-02
**Success Criteria** (what must be TRUE):
  1. Pages 3 (Scenarios), 8 (Econometrics), 9 (ML Models), and 13 (Advanced Econometrics) each have a "Download Audit Trail" button
  2. Clicking the button downloads a `.json` file
  3. JSON contains: `page`, `panel`, `year_range`, `filters`, `model_spec`, `n_obs`, `n_firms`, `timestamp`, `username`
  4. `model_spec` captures the relevant estimator/variables for that page (e.g., FE with profitability/tangibility/size for page 8)
  5. File downloads without error on all four pages
**Plans**: 1 plan

Plans:
- [ ] 10-01: Audit trail JSON download button on pages 3, 8, 9, 13

---

### Phase 11: Quality Carry-forwards
**Goal**: Smoke test coverage extended to pages 17-19 so regressions are caught automatically, and the 8 US DJIA firms with NULL tangibility have correct values so peer benchmarks using the us_av_2024 vintage are accurate
**Depends on**: Nothing (test file + data fix, independent of app pages)
**Requirements**: QUAL-01, QUAL-02
**Success Criteria** (what must be TRUE):
  1. `tests/smoke_auth.py` includes login + page-load checks for page 17 (Board Export), 18 (Company Navigator), and 19 (AI Assistant)
  2. Smoke tests for pages 17-19 use the researcher role (skumar) which has access to all three pages
  3. `SELECT COUNT(*) FROM financials WHERE vintage='us_av_2024' AND tangibility IS NULL` returns 0 after the fix
  4. All existing 369+ pytest tests still pass (no regressions from data fix)
**Plans**: 1 plan

Plans:
- [ ] 11-01: smoke_auth.py pages 17-19 + NULL tangibility fix for 8 US firms

---

## Progress

**Execution Order:**
All phases (8-11) are independent — execute in parallel.

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 8. CI/CD Pipeline | 0/1 | ○ Pending | — |
| 9. Company Timeline View | 0/1 | ○ Pending | — |
| 10. Reproducibility Audit Trail | 0/1 | ○ Pending | — |
| 11. Quality Carry-forwards | 0/1 | ○ Pending | — |
