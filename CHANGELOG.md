# Changelog

All notable changes to LifeCycle Leverage are documented here.
Format follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

## [1.3.1] — 2026-05-12

### Changed
- **Knowledge Graph** (page 7) now shows only the interactive network visualization (Stage + Industry overview, With Companies, Company drill-down)
- **Life Stage Dynamics** added as a new sidebar page (page 20) with five analytical tabs: Transition Probabilities, Event Impact Matrices, Stage Pathways, COVID Cohorts, Company Profiler

### Added
- `VERSION` file — single source of truth for app version
- `CHANGELOG.md` — release history
- Version badge displayed in navbar (`v1.3.1`)
- Version + release date displayed in Settings → About section

## [1.3.0] — 2026-05-10

### Added
- 19-page dashboard fully deployed on GCP Cloud Run
- CI/CD pipeline (GitHub Actions: test → deploy on master push)
- Auth gate with 3 roles: admin / researcher / viewer
- Panel selector in navbar (Latest, Thesis, Run 3, US S&P Sample) via query params
- AI Assistant (page 19) powered by Claude API (Anthropic)
- Board Deck export (page 17) — 13-topic python-pptx generator with kaleido PNG rendering
- Company Navigator (page 18) — pyvis ego graph, peer cluster, stage map
- Workbench (page 14) — scratchpad for ad-hoc analysis
- Interaction Effects (page 15) — cross-term OLS, stage moderation, simple slopes
- Knowledge Graph (page 7) — networkx graph with stage transition dynamics

### Fixed
- `sys.modules.pop("streamlit")` in tests replaced with monkeypatch (was breaking st.cache_data across test suite)
- `st.secrets.get()` wrapped in try/except at module level (prevents crash when secrets.toml absent)
- Artifact Registry Writer role added to GCP service account (required for `--source .` deploys)
- GitHub Actions secrets.toml write changed to `printf '%s'` + env var (fixes quoted TOML values)
