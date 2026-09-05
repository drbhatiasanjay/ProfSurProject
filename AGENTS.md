# AGENTS.md — LifeCycle Leverage Dashboard Agent Directives

## 0. Mandatory Operational Anchor & Bootstrap Sequence
Every agent (Antigravity, Codex, Claude, Cline) MUST follow this deterministic bootstrap sequence before inspecting code or undertaking tasks:
1. **Read `CURRENT_STATUS.md` FIRST:** It defines the canonical operational truth, baseline commit (`6075708`), verified test evidence, approved workstreams, and active resume point.
2. **Check Graphify Freshness:** Check whether `graphify-out/GRAPH_REPORT.md` and `graphify-out/graph.json` exist and are fresh enough for the current `HEAD`.
3. **Regenerate if Absent/Stale:** Generated graph artifacts are intentionally untracked in Git. If absent (e.g. after a fresh clone) or stale relative to `HEAD`, regenerate Graphify from the repository root using the approved `.graphifyignore` process:
   ```bash
   graphify extract .
   graphify cluster-only .
   ```
4. **Symbol Discovery:** Only after confirming freshness, use Graphify (`graphify-out/GRAPH_REPORT.md`) or `codebase-memory-mcp` (`search_graph`, `get_code_snippet`) for symbol and call-graph discovery before inspecting source files.

## 1. Core Operating Invariants
- **Authentication Standard:** Authenticate using accounts configured in `.streamlit/secrets.toml` or approved environment variables (`PROFSUR_AUTH_USERS`). Never hardcode or print plaintext passwords in code, logs, comments, or documentation.
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
- **Graph-First Symbol Discovery:** Never dump full 800+ line files into context; read line slices (`StartLine`/`EndLine`) when necessary.
- **Quiet Test Execution:** Run tests using `py -3.12 scripts/project_ops.py test --fast` or `pytest -q --tb=line` to prevent terminal log dumps.
- **Project Ops CLI:** Always use `scripts/project_ops.py` (`status`, `test`, `push`, `verify`) for routine development operations.

## 3. Reference Maps & Memory
- **Knowledge Graph:** Community and caller maps are in `graphify-out/GRAPH_REPORT.md` and `graphify-out/graph.json` (regenerate locally when absent).
- **Session Memory:** Record major session milestones in `SESSION_LOG.md` for clean multi-session context restoration.
- **Full Token Rules:** Detailed token engineering specifications are in `.agents/rules/token_optimization.md`.
