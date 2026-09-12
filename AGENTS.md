# AGENTS.md — LifeCycle Leverage Dashboard Agent Directives

## 0. Mandatory Operational Anchor & Bootstrap Sequence
Every agent (Antigravity, Codex, Claude, Cline) MUST follow this deterministic bootstrap sequence before inspecting code or undertaking tasks:
0. **Workspace Verification & Blunder Prevention:** Confirm that the target of the prompt is exclusively **`ProfSurProject`** (`c:\Users\hemas\Downloads\ProfSurProject`). If an incoming prompt mentions or targets another workspace or external repository (e.g., `FinancialDecisionIntelligence`, `FDI`, external PR reviews, Symphony, KAIF), **DO NOT START OR EXECUTE**. Immediately halt, alert the user of the workspace mismatch, and verify with the user to prevent cross-workspace blunders.
1. **Read `CURRENT_STATUS.md` FIRST:** It defines the canonical operational truth, baseline commit (`6075708`), verified test evidence, approved workstreams, and active resume point.
2. **Check Graphify Freshness:** Check whether `graphify-out/GRAPH_REPORT.md` and `graphify-out/graph.json` exist and are fresh enough for the current `HEAD`.
3. **Regenerate if Absent/Stale:** Generated graph artifacts are intentionally untracked in Git. If absent (e.g. after a fresh clone) or stale relative to `HEAD`, regenerate Graphify from the repository root using the approved `.graphifyignore` process:
   ```bash
   graphify extract .
   graphify cluster-only .
   ```
4. **Symbol Discovery:** Only after confirming freshness, use Graphify (`graphify-out/GRAPH_REPORT.md`) or `codebase-memory-mcp` (`search_graph`, `get_code_snippet`) for symbol and call-graph discovery before inspecting source files.

## 1. Core Operating Invariants
- **Exclusive Workspace Boundary & Blunder Prevention:** This session is strictly and exclusively confined to **`ProfSurProject`** (`c:\Users\hemas\Downloads\ProfSurProject`). If the user accidentally types or pastes a command, PR review task, or prompt belonging to another workspace or external repository (e.g., `FinancialDecisionIntelligence`, `FDI`, Symphony, KAIF), the agent **MUST NOT START OR EXECUTE IT**. The agent must immediately pause, notify the user of the detected workspace mismatch, and prevent any cross-project blunders before touching any files.
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

## 4. Screen/Code Synchronization Contract
- **Canonical entrypoint:** Run only `app.py` from the repository root. Never launch a file under `pages/` directly; that activates Streamlit's legacy auto-discovered navigation and is archived/deprecated.
- **Canonical demo URL:** `http://localhost:8501/`. Authenticate at the root, then navigate by clicking the registered sidebar page. Do not use a stale tab or a second Streamlit process on the same port.
- **Navigation registry:** Every visible page must have one `st.Page(...)` registration and one `st.navigation(...)` membership in `app.py`; page titles and routes must match the visible sidebar.
- **Left-panel contract:** The global sidebar owns dataset, filters, theme, and navigation. Page-specific controls may extend it, but must not create a competing navigation list or replace the global shell.
- **Right-panel contract:** Every submit, navigation, theme, chart, download, follow-up, and session action must survive the expected Streamlit rerun or be explicitly session-scoped. Persist user-visible chat actions that must survive reload.
- **Evidence gate:** Any UI change requires a source-to-screen mapping and an authenticated browser check for all four configured profiles (`profsurkumar`, `skumar`, `drbhatia`, `sbhatia`). A healthy HTTP endpoint alone is not UI evidence.

## 5. Operational Directives & Learned Safeguards
Detailed rule: `.agents/rules/engineering_safeguards.md`.
- **Baseline Truth:** GitHub `origin/master` (`6075708`) is immutable ground truth. All unmerged designs are strictly experimental.
- **Trace Full Auth Path:** Do not guess password failures. Verify complete path (`secrets.toml` -> SQLite `UNIQUE(email)` constraint -> native `bcrypt.checkpw()`). Duplicate emails in `secrets.toml` break database synchronization!
- **Native bcrypt Only:** Always generate hashes using Python's native `bcrypt` (12 rounds), never unverified library wrapper classes with divergent salt schemes.
- **Deterministic 1s Validation:** Test DB rows and credentials via CLI one-liners before launching browser subagents.
- **Strict Phase Gate:** Keep large UI/UX designs (e.g. Apple Liquid Glass) as `DESIGNED BUT NOT IMPLEMENTED` until explicit user greenlight.
- **Deployment Evidence Gate & Anti-Fabrication:** Never declare a deployment (Cloud Run / GCP / local) "done" based solely on an HTTP health check (`/_stcore/health` 200). Verification strictly requires an authenticated browser session confirming the specific target page/feature is rendered in the UI. Under NO circumstances should screenshot paths or completion claims be output until the browser subagent has completed execution and the resulting artifact files are verified to exist on disk.
