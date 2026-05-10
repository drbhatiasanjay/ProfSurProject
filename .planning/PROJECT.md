# LifeCycle Leverage Dashboard

## What This Is

A Streamlit dashboard analyzing determinants of capital structure across corporate life stages for 401 Indian S&P BSE 500 non-financial firms (2001-2024). Based on PhD thesis by Prof Surendra Kumar, University of Delhi, supervised by Dr. Varun Dawar & Dr. Chandra Prakash Gupta.

## Core Value

Researchers and analysts can interactively explore how leverage determinants differ across Dickinson (2011) life stages (Startup, Growth, Maturity, Shakeout, Decline, Decay), with rigorous econometric models matching the thesis methodology.

## Requirements

### Validated

- ✓ KPI Dashboard with leverage trends, lifecycle distribution, event impact — v1.0
- ✓ Peer Benchmarks with company vs industry comparison, radar chart — v1.0
- ✓ Scenario Analysis with OLS regression sliders and waterfall — v1.0
- ✓ Bulk Upload with Dickinson classification — v1.0
- ✓ Data Explorer with filtering and export — v1.0
- ✓ Econometrics Lab: Pooled OLS, FE, RE, Hausman test, ANOVA, stage-specific regressions — v1.1
- ✓ ML Models: RF, XGBoost, LightGBM with SHAP — v1.1
- ✓ Forecasting: LSTM/GRU time-series (requires PyTorch) — v1.1
- ✓ Clustering: K-Means with Dickinson comparison — v1.1
- ✓ Transitions: Kaplan-Meier survival, Cox PH, transition matrix — v1.1
- ✓ Knowledge Graph: Markov transition matrix, event impact matrices, pathway discovery, company profiler — v1.1
- ✓ Dynamic interpretation engine on all charts — v1.1
- ✓ Docker deployment + Cloud Run — v1.1
- ✓ 40 pytest tests (14 DB + 26 model) — v1.1
- ✓ Board Export page (17): 13 topic builders → branded .pptx (python-pptx + kaleido) — v1.2
- ✓ Company Navigator page (18): pyvis ego graph + peer cluster + Plotly stage map + Timeline (dual-axis) — v1.2/v1.3
- ✓ AI Financial Assistant page (19): full-screen chat (Ollama/Anthropic), grounded context injection — v1.2
- ✓ Wave 2 UX: CSV/PNG downloads on 17 pages, citation generator (pages 3/8/13), navbar panel selector — v1.2
- ✓ CI/CD: GitHub Actions pytest gate (Python 3.11) → Cloud Run auto-deploy on green master push — v1.3
- ✓ Reproducibility Audit Trail: `build_audit_json` + download button on pages 3, 8, 9, 13 — v1.3
- ✓ Playwright smoke tests covering all 19 pages (pages 17-19 added in v1.3) — v1.3
- ✓ us_av_2024 tangibility: 166 NULL rows filled via industry-mean imputation — v1.3

### Active

_(To be defined for v1.4 via `/gsd:new-milestone`)_

### Out of Scope

- Multi-country comparison — requires external data not in SQLite
- Collateral/security analysis — data not available (thesis limitation #2)
- Cash flow quantum (magnitude, not just +/- direction) — would require raw CF data restructuring
- Real-time data feeds — thesis is historical panel data
- Neo4j graph database — networkx in-process is sufficient for 401 firms

## Context

- Data: CMIE Prowess, 8,677 firm-year observations, 5 SQLite tables; us_av_2024 vintage (10 US DJIA comparators, tangibility clean as of v1.3)
- Stack: Streamlit, Plotly, pandas, networkx, statsmodels, scikit-learn, linearmodels, python-pptx, kaleido, Ollama/Anthropic (Page 19)
- Thesis methodology: OLS, FE, RE, Hausman, Breusch-Pagan, System GMM, ANOVA
- Deploy: Docker (Python 3.11-slim) → Google Cloud Run (us-east1); CI/CD via GitHub Actions (pytest gate + auto-deploy)
- Live URL: https://lifecycle-leverage-779655496440.us-east1.run.app
- Pages: 19 deployed (1-16 academic/panel, 17-19 individual company)
- Tests: ~302 passing in CI (Python 3.11); pre-existing TestPage15 environmental flakiness excluded

## Constraints

- **Python 3.11**: Required — 3.14 breaks ML packages
- **No PyTorch in Docker**: Too large (2GB+), forecasting page shows graceful fallback
- **SQLite only**: No external DB — all data in capital_structure.db
- **Existing pages must not break**: 12 pages deployed and working

## Current Milestone

v1.3 shipped 2026-05-10. Next milestone to be defined via `/gsd:new-milestone`.

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| networkx over Neo4j | 401 firms fits in memory, no infra needed | ✓ Good |
| linearmodels for panel FE/RE | statsmodels PanelOLS is limited | ✓ Good |
| PyTorch optional (not in Docker) | 2GB+ dependency, graceful fallback | ✓ Good |
| Plotly legends below chart | Prevents modebar overlap globally | ✓ Good |
| All test commands run in background | Prevents session freezes | ✓ Good |
| CI/CD: JSON SA key over Workload Identity Federation | Fastest unblocked path; WIF needs extra GCP setup | ✓ Good (v1.3) |
| `build_audit_json` zero Streamlit deps | Importable in plain Python/pytest | ✓ Good (v1.3) |
| Torch CPU wheel in CI | Avoids 2GB GPU download that times out runners | ✓ Good (v1.3) |
| `st.cache_data.clear()` autouse fixture in conftest | Prevents serialization corruption across tests in same process | ✓ Good (v1.3) |
| Industry-mean imputation for NULL tangibility | Closest peer reference; global mean fallback for Energy sector | ✓ Good (v1.3) |

---
*Last updated: 2026-05-10 after v1.3 milestone — Automation & Analytical Depth*
