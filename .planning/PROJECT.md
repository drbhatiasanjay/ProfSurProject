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

### Active

- [ ] Dynamic Panel GMM (System GMM with lag dependent variable) — thesis Table 5.12
- [ ] Determinants of CHANGES in capital structure (delta-leverage models) — thesis Tables 5.11, 6.5, 7.2, 7.4, 8.4, 8.5
- [ ] Breusch-Pagan LM test (Pooled OLS vs RE selection) — thesis section 4.8.3
- [ ] Growth vs Maturity direct comparison (subset regression) — thesis Table 7.5
- [ ] Post-COVID cohort analysis — thesis limitation #4

### Out of Scope

- Multi-country comparison — requires external data not in SQLite
- Collateral/security analysis — data not available (thesis limitation #2)
- Cash flow quantum (magnitude, not just +/- direction) — would require raw CF data restructuring
- Real-time data feeds — thesis is historical panel data
- Neo4j graph database — networkx in-process is sufficient for 401 firms

## Context

- Data: CMIE Prowess, 8,677 firm-year observations, 5 SQLite tables
- Stack: Streamlit, Plotly, pandas, networkx, statsmodels, scikit-learn, linearmodels
- Thesis methodology: OLS, FE, RE, Hausman, Breusch-Pagan, System GMM, ANOVA
- Deploy: Docker (Python 3.11-slim) → Google Cloud Run (us-east1)
- Live URL: https://lifecycle-leverage-779655496440.us-east1.run.app

## Constraints

- **Python 3.11**: Required — 3.14 breaks ML packages
- **No PyTorch in Docker**: Too large (2GB+), forecasting page shows graceful fallback
- **SQLite only**: No external DB — all data in capital_structure.db
- **Existing pages must not break**: 12 pages deployed and working

## Current Milestone: v1.2 Thesis Gap Closure

**Goal:** Add missing econometric methods from the thesis that don't require new data — Dynamic GMM, change-in-leverage models, Breusch-Pagan LM test, Growth vs Maturity comparison, post-COVID cohort analysis.

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| networkx over Neo4j | 401 firms fits in memory, no infra needed | ✓ Good |
| linearmodels for panel FE/RE | statsmodels PanelOLS is limited | ✓ Good |
| PyTorch optional (not in Docker) | 2GB+ dependency, graceful fallback | ✓ Good |
| Plotly legends below chart | Prevents modebar overlap globally | ✓ Good |
| All test commands run in background | Prevents session freezes | ✓ Good |

---
*Last updated: 2026-03-28 after thesis gap analysis*
