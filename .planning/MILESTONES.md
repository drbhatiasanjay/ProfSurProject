# Project Milestones: LifeCycle Leverage Dashboard

---

## v1.3 Automation & Analytical Depth (Shipped: 2026-05-10)

**Delivered:** CI/CD pipeline auto-deploying every passing master push, per-company life-stage timeline on page 18, reproducibility audit JSON on 4 analytics pages, smoke test coverage for pages 17-19, and NULL tangibility fix for 10 US firms.

**Phases completed:** 8–11 (4 plans total)

**Key accomplishments:**

- GitHub Actions pipeline: pytest gate (Python 3.11, torch CPU wheel, ENABLE_CMIE=false) → Cloud Run deploy on master; both jobs verified green (run 25627948851)
- Company Timeline View: dual-axis Plotly on page 18 — STAGE_COLORS bars (STAGE_RANK ordinal y) + leverage scatter line on secondary y; Stage Transitions expander
- Reproducibility Audit Trail: `build_audit_json()` (pure Python) + `audit_trail_download_button()` in helpers.py; wired on pages 3, 8, 9, 13 with page-specific model_spec
- Playwright smoke tests extended to pages 17 (Board Deck), 18 (Company Navigator), 19 (AI Assistant); viewer role blocked from all three
- 166 NULL tangibility rows filled for 10 US firms in us_av_2024 via industry-mean imputation; Chevron (Energy) used global mean 0.1719 fallback; tang100 + log_tang derived columns also updated

**Stats:**

- 19 files created/modified
- ~1,100 lines of Python added/changed
- 4 phases, 4 plans
- 1 day (all four phases shipped in parallel, 2026-05-10)

**Git range:** `2d68601` (ci: GitHub Actions pipeline) → `c1b2149` (docs: CI/CD phase complete)

**Archive:** `.planning/milestones/v1.3-ROADMAP.md`

---

## v1.2 Individual Company Intelligence (Shipped: 2026-05-10)

**Delivered:** Board deck export (page 17), Company Navigator with knowledge graph (page 18), AI Financial Assistant (page 19), plus Wave 2 UX improvements across all 17 data pages.

**Phases completed:** 6–7 (multiple plans)

**Key accomplishments:**

- Page 17 Board Export: 13 topic builders → branded .pptx via python-pptx + kaleido
- Page 18 Company Navigator: pyvis ego graph + peer cluster + Plotly stage map; 4 view modes
- Page 19 AI Assistant: full-screen chat (Ollama local / Anthropic API); shared chat_history with floating bubble
- Wave 2 UX: CSV/PNG download buttons on all 17 data pages, citation generator APA+LaTeX (pages 3/8/13), panel selector moved to navbar via query_params, floating chat bubble global injection

---

## v1.1 Advanced Analytics (Shipped: ~2026-04-22)

**Delivered:** Advanced econometric models (GMM, delta-leverage, stage comparisons, IV-2SLS), post-COVID cohort analysis, DataV2/CMIE 2025 vintage rollforward, Dark mode + Playwright smoke tests.

**Phases completed:** 1–5

**Key accomplishments:**

- System GMM (linearmodels IVGMM) replacing OLS stub — thesis Table 5.12
- Delta-leverage models (6.5, 7.2, 7.4, 8.4, 8.5), stage comparisons (Table 7.5), Breusch-Pagan LM test
- Post-COVID cohort analysis on page 13
- DataV2 vintage ingest: cmie_2025 + us_av_2024 panel loaded, vintage-tagged in SQLite
- Light/Dark theme toggle, Dashboard polish, Playwright smoke gate
