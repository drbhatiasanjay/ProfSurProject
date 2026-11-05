# CURRENT_STATUS.md — LifeCycle Leverage Canonical Operational Status

**Last Updated:** 05 November 2026 (Release v2.1.0 Closure Checkpoint)  
**Active Baseline Commit:** `07f6622` on `master`  
**Release Tag:** `v2.1.0` (Synced to `origin/master`)  
**Production URL:** `https://lifecycle-leverage-qhzom2yadq-ue.a.run.app`  
**GCP Project:** `tempproject-462219` (Region: `us-east1`)  
**Active Revision:** `lifecycle-leverage-00222-wsw`  
**Paper Freeze Branch:** `paper/iimcfrc-2026-lifestagedebtai` (Frozen & Isolated)  
**Operational Role:** Single Canonical Source of Operational Truth & Immediate Resume Point  

---

## 1. Executive Summary & Release v2.1.0 Milestone
Release `v2.1.0` consolidates the full-stack stability, high-contrast theme interoperability (seamless Dark/Light modes), econometric rigor, and automated CI/CD continuous deployment on Google Cloud Run.

### Core Release Deliverables:
1. **Automated CI/CD Deployment:** GitHub Actions workflow `Test and Deploy` (Run `42068823114`) executed cleanly with 100% pass rate:
   - `Run pytest (Python 3.11)`: 820 tests passed in 2m41s.
   - `OCaml build + tests (lifecycle-ontology)`: 100% build & verification passed in 3m49s.
   - `Deploy to Cloud Run`: Deployed revision `lifecycle-leverage-00222-wsw` in 4m35s with zero manual gates.
2. **First-Time-Right Authentication Matrix (100% Verified):**
   - `drbhatia` (Role `admin`): Authenticated via bcrypt against SQLite `auth_users`.
   - `skumar` (Role `researcher`): Authenticated via bcrypt against SQLite `auth_users`.
   - `profsurkumar` (Role `researcher`): Authenticated via bcrypt against SQLite `auth_users`.
   - `sbhatia` (Role `viewer`): Authenticated via bcrypt against SQLite `auth_users`.
   - `guest` (Role `viewer`): Authenticated via bcrypt against SQLite `auth_users`.
3. **UI/UX & Layout Hardening:**
   - **Sidebar Hierarchy:** Navigation links (`st.Page`) are strictly anchored at the **top** of the left panel above dataset and year-range filters.
   - **Theme Interoperability:** High-contrast Dark and Light modes validated across all dashboard views, charts, and tables without unreadable contrasts or styling bleeding.
   - **Auth Card Sanitization:** Eliminated raw HTML tag artifacts (`<div class="auth-brand-badge">`) and removed stray CSS code block displays.
4. **Econometric & Calculation Integrity (Red-Team Certified):**
   - Ground truth company primary keys verified (`Tata Motors = 248093`, $N=8,677$ panel sample size, $N=9,031$ extended universe).
   - Fixed Effects within-estimator fallback with `.cov` covariance matrix preservation for Hausman specification test (`hausman fe re`).
   - Fail-closed error handling for runtime estimator anomalies.
   - Dynamic 95% Confidence Intervals and variance-covariance standard errors.

---

## 2. Live Deployment & Visual Evidence Gate (AGENTS.md Rule 5)
Browser subagent verification conducted on the live Google Cloud Run instance (`https://lifecycle-leverage-qhzom2yadq-ue.a.run.app`):
- **Verified Dark Mode Rendering:** `verified_gcp_v2_1_live_dark.png` (44,351 bytes, verified on disk).
  - Confirmed top banner branding: `LifeCycle Leverage v2.1.0`, vintage `bf2001-25_Sept26`, `drbhatia · Admin`.
  - Confirmed navigation list positioned at top of sidebar.
  - Confirmed core thesis metrics: $N=9,031$ Firm-Years, 400 Enterprises (2001–2025).

---

## 3. Knowledge Graph & Architecture Index
- **Graphify Knowledge Graph:** Re-extracted and clustered via `graphify extract .` and `graphify cluster-only .`.
- **Node Count:** 7,450 nodes.
- **Edge Count:** 12,204 edges.
- **Communities:** 850 communities indexed in `graphify-out/GRAPH_REPORT.md` and `graphify-out/graph.json`.
- **Stata Capabilities:** Fully synchronized in `docs/COMMAND_CAPABILITIES.md` via `scripts/sync_command_registry_docs.py`.

---

## 4. Operational Invariants for Future Sessions
1. **Exclusive Workspace Boundary:** Strictly confined to `c:\Users\hemas\Downloads\ProfSurProject`. Never touch external repositories or `paper/iimcfrc-2026-lifestagedebtai`.
2. **Canonical Entrypoint:** Launch only `app.py` from repository root.
3. **Test Execution Protocol:** Always run fast tests via `py -3.12 scripts/project_ops.py test --fast` or `pytest -q --tb=line`.
4. **Automated Deployment:** Pushes to `master` automatically trigger `.github/workflows/deploy.yml` and deploy directly to Cloud Run without manual intervention.
