# Project State

## Project Reference

See: .planning/PROJECT.md

**Core value:** CFOs and researchers can explore capital structure determinants, benchmark peers, export board decks, and navigate their company's position in an interactive knowledge graph — all grounded in the PhD thesis panel of 401 Indian firms (2001–2024).

**Current focus:** Phase 7 — Wave 2 Tier-1 UX (citation generator, export polish, navigation improvements)

## Current Position

Phase: Phase 7 (07-wave2-tier1-ux)
Plan: 2 of 5 in current phase (07-02 just completed; 07-04 also done out-of-order)
Status: In progress
Last activity: 2026-05-10 - Completed 07-02-PLAN.md (plotly_layout year_range param + Advanced options expanders on 5 pages)

Progress: [██████████] Pages 1-18 complete; Phase 7 plan 4/5 done

## App State (as of 2026-05-07)

**18 pages deployed** on GCP Cloud Run (revision 00039-6zp):
- Pages 1-16: Thesis/Academic analytics (panel-wide; company is a data point)
  - 1_dashboard, 2_peer_benchmarks, 3_scenarios, 4_bulk_upload, 5_data_explorer
  - 6_settings, 7_knowledge_graph (sidebar: "Life Stage Dynamics"), 8_econometrics
  - 9_ml_models, 10_forecasting, 11_clustering, 12_transitions
  - 13_advanced_econometrics, 14_workbench, 15_interaction_effects, 16_admin_activity
- Pages 17-18: Individual Company (company is the subject; panel is peer context)
  - 17_board_export: 13 topic builders → branded .pptx; python-pptx + kaleido
  - 18_company_navigator: pyvis ego graph + peer cluster + Plotly stage map; 3 zoom levels

**Auth gate**: streamlit-authenticator; 3 roles — sbhatia (admin), skumar (researcher), guest (viewer)
**GCP URL**: https://lifecycle-leverage-779655496440.us-east1.run.app
**GitHub**: https://github.com/drbhatiasanjay/ProfSurProject (master branch)
**Tests**: 344 passing (py -3.12 -m pytest tests/ -v)
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

- revision 00039-6zp: feat(page18): Company Navigator — pyvis ego/peer/stage map; page 7 renamed Life Stage Dynamics
- revision 00038: feat(auth+navbar): fixed header bar + Sign Out in navbar + sidebar arrow fix
- feat(page17): Board Deck Export — 13 topics, python-pptx, kaleido
- feat(auth+page16): streamlit-authenticator login gate, audit_log, Activity Log page
- 8f57282 feat(panel): preserve year-range selection across panel switches (2026-04-25)

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

### Pending Todos

- **Phase 6 AI Financial Assistant**: models/chatbot.py + floating bubble in app.py + pages/19_ai_assistant.py + page 17 topic 13 wiring. Plans being created now.
- **Reload 8 US firms (NULL tangibility)**: 1hr effort in models/data_ingest.py — carry-forward.
- **smoke_auth.py**: add page 17+18 checks.
- **G1 System GMM (Arellano-Bond/Blundell-Bond)**: deferred pending explicit user decision.
- **CMIE Economy API service activation**: external blocker on sk_pgdav; POC scripts ready.

### Blockers/Concerns

- Ollama must be installed locally for Phase 6 local dev: winget install Ollama.Ollama then ollama pull llama3.1:8b
- GCP Cloud Run has no local Ollama server — production default must be Claude API or graceful "no backend configured" state with clear UI message.
- Streamlit iframe sandbox limits floating bubble JS. Use hidden st.checkbox as state bridge (checkbox change triggers st.rerun()).

## Session Continuity

Last session: 2026-05-10T04:14:57Z
Stopped at: Completed 07-02-PLAN.md — plotly_layout year_range param + Advanced options expanders (commit 732c012)
Resume file: None — clean stopping point. Next action: execute 07-03-PLAN.md or 07-05-PLAN.md
