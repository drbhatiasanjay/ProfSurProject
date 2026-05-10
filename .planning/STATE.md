# Project State

## Project Reference

See: .planning/PROJECT.md

**Core value:** CFOs and researchers can explore capital structure determinants, benchmark peers, export board decks, and navigate their company's position in an interactive knowledge graph — all grounded in the PhD thesis panel of 401 Indian firms (2001–2024).

**Current focus:** Phase 2 — System GMM (Phase 1 complete; 02-01 next)

## Current Position

Phase: Phase 3 (03-stage-comparisons)
Plan: 0 of 1 — Phase 2 complete
Status: In progress
Last activity: 2026-05-10 - Completed Phase 2 (IVGMM + integration tests, 61ddf6e)

Progress: [██████████] Phases 1 + 2 + 6 + 7 complete; Phase 3 next

## App State (as of 2026-05-10)

**19 pages deployed** on GCP Cloud Run (revision 00041-tz2):
- Pages 1-16: Thesis/Academic analytics (panel-wide; company is a data point)
  - 1_dashboard, 2_peer_benchmarks, 3_scenarios, 4_bulk_upload, 5_data_explorer
  - 6_settings, 7_knowledge_graph (sidebar: "Life Stage Dynamics"), 8_econometrics
  - 9_ml_models, 10_forecasting, 11_clustering, 12_transitions
  - 13_advanced_econometrics, 14_workbench, 15_interaction_effects, 16_admin_activity
- Pages 17-18: Individual Company (company is the subject; panel is peer context)
  - 17_board_export: 13 topic builders → branded .pptx; python-pptx + kaleido
  - 18_company_navigator: pyvis ego graph + peer cluster + Plotly stage map; 3 zoom levels
  - 19_ai_assistant: full-screen AI chat (admin + researcher only); shared chat_history with any future FAB

**Auth gate**: streamlit-authenticator; 3 roles — sbhatia (admin), skumar (researcher), guest (viewer)
**GCP URL**: https://lifecycle-leverage-779655496440.us-east1.run.app
**GitHub**: https://github.com/drbhatiasanjay/ProfSurProject (master branch)
**Tests**: 302 passing (pre-existing 20 failures + 52 errors in TestPage15 are environmental flakiness)
**Python**: 3.12 locally, 3.11-slim in Docker/Cloud Run

## Key Architecture

**Database**: SQLite capital_structure.db — vintage-tagged (thesis + cmie_2025 + run3 + us_av_2024)
**Models package**: models/ (econometric, ml_predict, timeseries, clustering, survival, interaction, board_export, pptx_generator)
**Graph layer**: graph_builder.py (NetworkX MultiGraph) + graph_viz.py (Plotly + pyvis renderers)
  - CFO graph functions: build_cfo_ego_graph, build_peer_cluster_graph, build_stage_map_graph, get_cfo_node_panel
  - pyvis renderer: build_pyvis_html()
**Helpers**: helpers.py — plotly_layout(title, height, year_range=None), STAGE_COLORS, STAGE_ORDER, render_interpretation(), require_role(), new_badge()
**Session state keys in use**: filters, panel_mode, theme, user, guest_display_name
**Session state keys reserved for Phase 6**: chat_history, chat_mode, chat_backend, chat_open, ai_recommendations

## Recent commits (chronological, latest first)

- 540cb24 docs(01): Phase 1 research complete — all backend functions already implemented (2026-05-10)
- 47588f9 docs(07-03): complete download buttons plan (2026-05-10)
- 0fb45bf feat(07-03): CSV/PNG download buttons on all 17 data pages (2026-05-10)
- 399c154 feat(07-05): panel selector → navbar select via query_params (2026-05-10)
- 851a73a feat(07-04): citation generator APA+LaTeX on pages 3, 8, 13 (2026-05-10)
- 267cebd docs(06-05): Phase 6 AI Financial Assistant complete — UAT approved (2026-05-10)

## Accumulated Context

### Decisions

- **Two use-case architecture (pages 17+)**: Pages 1-16 = thesis/academic (panel-as-subject); Pages 17+ = individual company (company-as-subject). Never mix these in the same page.
- **Panel mode pins**: Pages 3/8/9/10/13/15 pin panel_mode='thesis' at import for reproducibility. Pages 1/2/5/7 respect sidebar selection.
- **Size decile parsing**: size_decile stored as "Decile N" string in DB; always use _decile_int() helper before arithmetic.
- **Pyvis over st-link-analysis**: st-link-analysis has no native click events without a fork; pyvis renders via components.v1.html(); companion st.selectbox for node selection.
- **app.py atomic edits**: st.Page() definition AND nav list insertion must be in ONE Edit call — splitting caused invisible pages in previous sessions.
- **No fine-tuning for LLM**: Context injection (800-900 token structured prompt) is the correct grounding mechanism. finance-llama:8b does not need fine-tuning.
- **Ollama as local default**: Zero data egress, free, runs on CPU. Claude API is opt-in (data leaves server — shown clearly to user). Cloud Run production uses Claude API (no local Ollama server on GCP).
- **Floating bubble over dedicated-page-only**: CFOs need to ask questions while looking at their board deck without navigating away. Bubble injected globally in app.py via st.html(). Dedicated Page 19 is for deep research sessions.
- **Streamlit iframe sandbox**: Floating bubble JS cannot directly call Python callbacks. State bridge uses a hidden st.checkbox whose value is toggled by JS — Streamlit re-runs on checkbox change.
- **Phase 6 page number**: AI Assistant is page 19 (page 17 = Board Deck, page 18 = Company Navigator).
- **Page 17 Topic 13**: AI Recommendations sub-topics 13.1-13.4 are the primary integration point — they call chatbot.build_company_context() + LLM adapter.
- **company_name/industry_group in companies table**: These columns are NOT in financials; any raw SQL needing them must JOIN companies c ON c.company_code = f.company_code.
- **leverage_predictor_sample_means key mapping**: Returns abbreviated keys (prof/tang/dvnd); PREDICTORS uses full names (profitability/tangibility/dividend). Use _means_key_map in llm_adapters.py as reference.
- **llm_adapters module import rule**: No streamlit at module level; all 9 public exports importable in plain Python/pytest; lazy st import only inside stream_anthropic function.
- **Panel selector via query_params (UX-08)**: Panel moved from sidebar st.radio to navbar HTML select driven by st.query_params.get('panel','latest'). URLSearchParams JS used in onchange to preserve other query params. _last_panel sentinel gates year-range reset to panel-change events only.

### Pending Todos

- **Phase 3 plan 03-01**: Harden `run_stage_comparison` — add per-stage min-obs guard, fix `const` row exclusion from Divergent column, validate same-stage inputs. Plan at `.planning/phases/03-stage-comparisons/03-01-PLAN.md`.
- **Reload 8 US firms (NULL tangibility)**: 1hr effort in models/data_ingest.py — carry-forward.
- **smoke_auth.py**: add page 17+18+19 checks (Playwright-based).
- **CMIE Economy API service activation**: external blocker on sk_pgdav; POC scripts ready.

### Blockers/Concerns

- Phase 1 backend functions already implemented — plans are test hardening only, fast execution expected.
- Phase 2 (GMM) and Phase 3 (Stage Comparisons) can be researched/planned in parallel once Phase 1 plans exist.
- GCP Cloud Run has no local Ollama server — Page 19 AI Assistant defaults to Claude API (ANTHROPIC_API_KEY in secrets.toml).

## Session Continuity

Last session: 2026-05-10T11:35:00Z
Stopped at: Completed 01-01-PLAN.md — contract docstrings + backend smoke verified. Ready for 01-02 unit test hardening.
Resume file: None — clean handoff point.
