# AGENTS.md — LifeCycle Leverage Dashboard Agent Directives

## 1. Core Operating Invariants
- **Authentication Standard:** Login credentials are `profsurkumar` (Prof. Surendra Kumar) and `skumar` with password `Pass@123`.
- **Server Autonomy:** Autonomously run, test, and manage the local Streamlit server (`http://localhost:8501`) and live GCP verification without asking user intervention.
- **Non-Destructive Standard:** Always append or extend existing features; never overwrite, remove, or degrade existing tabs, Stata cards, literature tables, or panel datasets.
- **No Local LLMs:** Do not run local LLMs (Ollama, local vLLM) on this machine. Use cloud APIs (Gemini 1.5 Flash, Claude) or Python template scripts.

## 2. Token Optimization & Context Rules
- **Concise Engineer Output:** Be ultra-terse. No conversational filler, no repeating user prompts, no verbose apologies. Output targeted diffs and concise verification lines only.
- **Ponytail Principle (Minimal Code):** Evaluate code necessity before writing:
  1. *Does this strictly need to exist?*
  2. *Can we reuse an existing function in `models/`, `utils/`, or `components/`?*
  3. *Use Python/Streamlit standard libraries over adding new wrappers.*
  4. *Write minimal code lines.*
- **Graph-First Symbol Discovery:** ALWAYS query `codebase-memory-mcp` (`search_graph`, `get_code_snippet`) or `graphify-out/GRAPH_REPORT.md` before reading files. Never dump full 800+ line files into context; read line slices (`StartLine`/`EndLine`) when necessary.
- **Quiet Test Execution:** Run tests using `py -3.12 scripts/project_ops.py test --fast` or `pytest -q --tb=line` to prevent terminal log dumps.
- **Project Ops CLI:** Always use `scripts/project_ops.py` (`status`, `test`, `push`, `verify`) for routine development operations.

## 3. Reference Maps & Memory
- **Knowledge Graph:** Community and caller maps are in `graphify-out/GRAPH_REPORT.md` and `graphify-out/graph.json`.
- **Session Memory:** Record major session milestones in `SESSION_LOG.md` / Obsidian for clean multi-session context restoration.
- **Full Token Rules:** Detailed token engineering specifications are in `.agents/rules/token_optimization.md`.
