# Engineering Standard & Lessons Learnt Directives (30 Sept 2026 Update)

## A. Windows File Writing & Escaping Rules
- NEVER pass inline Python code containing `$` (LaTeX variables like `$Y_{it}$`) or complex nested quotes inside PowerShell `-c "..."`. PowerShell expands `$` into empty variables or breaks string delimiters.
- ALWAYS use PowerShell verbatim single-quoted here-strings (`@' ... '@ | Out-File -FilePath <path> -Encoding utf8`) or standalone python scripts.

## B. First-Time-Right Verification Protocol
1. **Query Database Ground Truth First:** Before writing test assertions, verify actual database values (`N=8,677`, exact mean values, exact primary keys like Tata Motors = `248093`).
2. **Inspect Signatures First:** Always inspect module exports via `dir(module)` before writing test imports to avoid `ImportError` on collection.
3. **Adversarial Red-Team Check:** Test edge cases (unestimated standard errors, negative quadratic forms, unsupported command routing) rather than only happy-path cases.

## C. Manuscript & Paper Isolation
- Keep `paper/iimcfrc-2026-lifestagedebtai` cleanly isolated and frozen.
- Never bleed software changes into manuscript paths.
- Enforce formal academic tone: zero em-dashes (`--`), no AI tropes/clichés, Dickinson (2011) life-cycle attribution.

## D. Automated Capability Synchronization
- Run `python scripts/sync_command_registry_docs.py` whenever modifying `models/stata_engine.py` to keep `docs/COMMAND_CAPABILITIES.md` synchronized.

## E. Codex Review Post-Mortem & Adversarial Safeguards (13 Nov 2026 Update)
1. **End-to-End Production Wiring Contract (Zero Dead Helpers):** Writing a new helper module or contract class is strictly incomplete until production callers (`app.py`, `models/pre_ipo_engine.py`, `models/pre_ipo_ingest.py`, `pages/27_pre_ipo_drhp.py`) import, route, and execute it. Unit tests verifying helper functions in isolation do NOT constitute production implementation.
2. **Negative & Bypass Probing (Fail-Closed Architecture):** Never write assertions testing only happy paths and matching hashes. Explicitly test malicious or edge-case bypasses:
   - What happens when `snapshot_hash` is `None`?
   - What happens when `snapshot_id="nonexistent"`?
   - What happens when a user uploads a custom document that does not contain the default dropdown key?
   Gates must unconditionally fail closed (`ExportBlockedError`, `BlockedResult`).
3. **Zero Python Truthiness in Financial Calculations:** In financial econometrics, $0.0$, $0\%$, and $0$ are genuine, valid numbers distinct from absence (`None`). NEVER write `val or default` (e.g. `beta or 1.0`, `tax or 25.17`). Always use explicit presence checks: `if val is None:`.
4. **Solver Round-Trip Inversion Requirement:** Any mathematical root-finding or optimization solver (e.g. reverse DCF implied CAGR) MUST have a unit test asserting that feeding the solved value back into the explicit multi-period model reprices the target valuation within documented tolerance ($\le 0.05\%$).
5. **Database Transaction Atomicity & Fault-Injection:** In Python's standard `sqlite3`, calling `conn.executescript()` silently triggers an implicit `COMMIT` before executing the script, breaking transaction atomicity. Never use `executescript()` inside an active `BEGIN IMMEDIATE` transaction. Migration tests MUST inject an intentional failure midway (after DDL alteration and before journal write) to prove that `conn.rollback()` restores the pre-migration schema with zero residual columns or indexes.
6. **Ground-Truth Corpus Respect:** Never substitute synthetic blank pages or truncated fixtures (e.g., 3-page test PDF) as substitutes for official filings (513-page HCCH DRHP). OCR consent alone must never mark empty text as status `OK`.

## F. The Adversarial Mindset: Verification Across the Design & Code Lifecycle
Author bias is the single largest source of escaped defects: authors test to demonstrate their design *works*, while reviewers test to find how it *breaks*. Every engineer and autonomous agent working on this codebase must adopt an explicit **Adversarial Mindset** across all three phases of the engineering lifecycle:

### 1. Phase 1: Pre-Design Adversarial Threat Modeling (Before Architecture & Design)
- **Assume Hostile Callers & Environmental Corruption:** Before drafting any design or interface, ask: *"How will a caller bypass this contract? What if caller-supplied IDs or hashes are omitted, unpersisted, spoofed, or replayed?"*
- **Identify Structural Traps Early:** Uncover hidden library quirks (e.g. SQLite `executescript()` silently auto-committing active transactions; Streamlit rerun lifecycles dropping state) *before* committing to an architecture.
- **Fail-Closed by Design:** Architect gates so that missing data, unexpected document keys, or unauthenticated snapshots unconditionally reject or fail closed (`ExportBlockedError`, `BlockedResult`), rather than falling back to permissive defaults.
- **Explicit Numerical Domain Design:** Design data contracts such that mathematical boundaries ($0.0$, $0\%$, negative values) are first-class valid inputs distinct from absent/None values.

### 2. Phase 2: Pre-Code Adversarial Red-Teaming (The Red Phase of TDD)
- **Author Malicious & Boundary Tests First:** Before writing implementation code, write tests specifically designed to exploit and break the system:
  1. *Bypass Probing:* Call export/service layers directly with `snapshot_id="nonexistent"`, `snapshot_hash=None`, or tampered hashes. The test must assert immediate failure.
  2. *Truthiness Probing:* Pass zero values (`beta=0.0`, `tax_rate=0.0`, `debt=0.0`) and assert that the calculation does not substitute defaults (`or 1.0`, `or 25.17`).
  3. *Solver Boundary Probing:* Provide extreme financial values ($WACC \le g$, high interest rates) and assert that the solver halts cleanly with typed diagnostics rather than silently clamping.
  4. *Transaction Fault Injection:* Inject exceptions midway during DDL executions to verify `conn.rollback()` restores the pre-migration state with zero residual schema changes.
- **Verify Red-Phase Failure:** Confirm that these tests genuinely fail against unpatched code before implementing the fix. A test that passes before code is written provides zero verification value.

### 3. Phase 3: Post-Code Adversarial Self-Audit Gate (Before Declaring Any Task Done)
Before submitting a PR, commit, or repair handoff, the author must switch roles into a Hostile Auditor and complete this verification checklist:
- [ ] **Zero Dead Code / Production Wiring Audit:** Trace AST or call-graphs from production entrypoints (`app.py`, `pages/`, CLI) down to the new code. Are all new classes, validators, and helpers actively invoked in the production pipeline?
- [ ] **Bypass Immunity Check:** Re-run the negative bypass suite. Can any caller obtain analytical output without satisfying persistence and cryptographic hash verification?
- [ ] **Truthiness Scan:** Grep all modified files for `\bor\b` following numeric or financial variables (`val or default`). Replace every instance with explicit `if val is None:`.
- [ ] **Mathematical Inversion Check:** For any numerical solver (e.g. reverse DCF implied CAGR), assert that feeding solved parameters back into the multi-period discounting model reprices the target valuation within $\le 0.05\%$.
- [ ] **Transaction Atomicity Verification:** Confirm no `conn.executescript()` calls exist inside transaction blocks. Verify rollback recovery with fault-injection tests.
- [ ] **Ground-Truth Data & DB Immutability:** Verify that `capital_structure.db` SHA-256 is unchanged (`CA696195...`). Verify that regulatory tests use authentic filings, never synthetic blank-page fixtures.
- [ ] **Evidence Gate Verification:** Do not report browser UI success without live, authenticated browser execution and physical screenshot verification on disk.

---
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

## 6. Master Video Walkthrough & Screen Recording Directives (AI Assistant)
- **Canonical Script:** `scripts/produce_ai_chatbot_demo_recordly.py`
- **Mandatory 4-Phase Screen Recording Flow Invariant:**
  1. **Phase 1 (Input & Intent):** Type the query live on camera into `stChatInputTextArea` while Sentence 0 audio introduces the entity context.
  2. **Phase 2 (Silent Authentic Working State):** When the query is submitted, **TOTAL SILENCE** is maintained. Zero audio/talking occurs while the native `Working...` spinner executes (~5–10s).
  3. **Phase 3 (Immediate Scroll-Up to Top):** The exact millisecond the generation completes and results appear, the viewport immediately snaps to $y=0$ via `scrollTo({top: 0})` so the CFO Recommendations, badges, and hypothesis are in full view.
  4. **Phase 4 (Commentary & Focal Scroll):** Commentary and subtitles begin narrating the results and interpretation *after* the results are visible, with paced focal scrolling down through tables and charts.
- **Mandatory 5-Company Archetype Coverage:** Every master walkthrough run MUST include individual, dedicated scenes for all 5 enterprise archetypes:
  1. **Infosys Ltd. (Tech):** Mature stage, 4.2% leverage, internal cash self-financing.
  2. **Tata Steel Ltd. (Metals):** Macro rate shock (+150 bps), ICR compression, covenant defense.
  3. **Bharti Airtel (Telecom):** 5G spectrum commitments, InvIT monetization, balance sheet repair.
  4. **InterGlobe Aviation / IndiGo (Aviation):** Jet fuel shocks, cash burn runway, Sale-and-Leaseback debt.
  5. **Sun Pharma (Pharma):** Cross-border M&A, Euro Notes natural currency FX hedge.
- **Subtitle Governance:** Floating subtitles must be anchored at `MarginV=90` in clean upper white space to guarantee zero chat input bar or control occlusion.


