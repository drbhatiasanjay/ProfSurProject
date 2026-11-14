# AGENTS.md — ProfSurProject Agent Constitution & Invariants

This constitution governs all autonomous implementation workers and reviewer agents working on **ProfSurProject**. It defines permanent architectural boundaries, authority rules, security invariants, and engineering standards.

---

## 1. Authority Precedence & Conflict Resolution

When evaluating repository state, task instructions, or evidence, agents must apply this strict hierarchy (highest to lowest):

1. **Current User Authorization:** Explicit interactive human instructions for the active session.
2. **Current Task Contract:** Machine-verifiable contract (`.agents/task-contract.json` or CLI parameters) signed by authorized reviewer.
3. **Runtime Git and Filesystem State:** Empirical live state returned by `py -3.12 scripts/project_status.py --json`.
4. **Official Source Documents & Cryptographic Hashes:** Raw regulatory filing bytes (e.g. SEBI DRHP PDFs) with verified SHA-256.
5. **Stable AGENTS.md Policy:** The permanent operational rules and invariants defined in this constitution.
6. **Current Operational Summary:** Human-readable context in `CURRENT_STATUS.md`.
7. **Historical Handoffs and Session Logs:** Prior milestone reports, narrative logs, and archived handoffs.

> [!CAUTION]
> If any two applicable sources conflict, the worker agent must immediately halt and output:
> `SOURCE_OF_TRUTH_CONFLICT`
> The agent must not guess, reconcile silently, or assume the more permissive interpretation.

---

## 2. Strict Task Authorization & Scope Boundaries

* **Exclusive Workspace Boundary:** Work is strictly confined to `ProfSurProject` (`c:\Users\hemas\Downloads\ProfSurProject`). Never access, inspect, or modify external workspaces (e.g. FDI, Symphony, KAIF).
* **Bounded Packet Execution:** A roadmap, future PR sequence, backlog, or TODO list is context only—it is NOT authorization.
* **No Successor Auto-Authorization:** Completing one authorized packet never authorizes the next packet.
* **Stop Condition Discipline:** The worker must immediately halt upon satisfying the authorized packet's exit criteria.
* **Reporting Adjacent Defects:** Adjacent bugs or missing helpers must be recorded as findings in review evidence, not silently repaired without authorization.
* **Publication Authority:** Workers may never push to remote branches, open pull requests, merge into master, or deploy to production unless explicitly authorized by the active contract.

---

## 3. Independent Verification & No Self-Approval

* **Zero Self-Approval:** Implementation workers cannot close their own defects or declare tasks `CLOSED_VERIFIED`, `PRODUCTION_SAFE`, `SCIENTIFICALLY_VALIDATED`, `READY_TO_MERGE`, or `READY_TO_DEPLOY`.
* **Worker Status Domain:** Worker completion status may only be reported as:
  - `IMPLEMENTED_PENDING_INDEPENDENT_REVIEW`
  - `PARTIALLY_IMPLEMENTED`
  - `BLOCKED`
* **Test Authorship Boundary:** Tests authored by the implementation worker serve as evidence inputs to verify changes, not independent acceptance.
* **Separation of Roles:** Codex (or a separately designated auditor) holds exclusive authority for independent verification and production acceptance.

---

## 4. Production Wiring & Anti-Dead-Code Principle

> “Preserve validated capability, not defective implementation paths.”

Writing a new contract, validator, or helper function in isolation is strictly incomplete until production callers are wired through it. A correctness repair must:
1. Map every production caller from application entrypoints (`app.py`, `pages/`, CLI).
2. Route callers through the corrected, validated implementation.
3. Make the defective legacy path unreachable.
4. Remove or explicitly deprecate the old path.
5. Prove unreachability and fail-closed behavior through adversarial tests.

Adding a parallel helper while production continues executing the legacy path is classified as an incomplete implementation.

---

## 5. Data Authority & Empirical Hierarchy

* **Documentary Authority:** Official regulatory filing bytes (e.g. 513-page HCCH DRHP PDF) and their cryptographic SHA-256 hashes constitute primary truth.
* **Application Authority:** Analytical modules may only ingest human-reviewed, immutable, accepted evidence snapshots (`ACCEPTED_FOR_ANALYSIS`).
* **Persistence Role:** Databases (SQLite `capital_structure.db`) represent mutable state persistence, never primary documentary truth.
* **Legacy Registry Classification:** `PRE_IPO_REGISTRY` is unverified legacy sample data, never a source of truth or an oracle.
* **Candidate Extraction:** Document extractors emit `PROPOSED` candidates containing raw text, coordinates, page numbers, and confidence. Extraction must never assign `ACCEPTED` status without human auditor sign-off.
* **Numerical Domain Integrity:** In financial econometrics, $0.0$, $0\%$, and $0$ are valid numbers distinct from absence (`None`). Never use zero to represent missing, unsearched, undisclosed, or not applicable values. Missing data must be explicitly represented as `NOT_DISCLOSED` or fail closed.

---

## 6. Security & Credential Invariants

* **Zero Committed Credentials:** Never commit, log, print, or screenshot passwords, tokens, API keys, session cookies, or reusable test credentials.
* **Dynamic Resolution:** Authentication in tests and tools must resolve exclusively from environment variables (e.g. `PROFSUR_AUTH_PASS`) or `.streamlit/secrets.toml`.
* **Missing Credential Gate:** If credentials are missing, tests must fail closed and halt; agents must never invent fallback passwords in code or scripts.
* **Redaction Mandatory:** Any secret pattern detected in logs or reports must be masked with `[REDACTED]`.

---

## 7. Execution Invariants & Environmental Rules

* **Canonical Entrypoint:** Launch the platform strictly via `app.py` from repository root using Python 3.12 (`py -3.12 -m streamlit run app.py`).
* **Ground-Truth Database Immutability:** `capital_structure.db` SHA-256 (`CA696195A5C541B56E0533DE6C69A3BEC4E501A232FD2B18A1B09D15D6FA7873`) must remain pristine. Tests must use isolated temporary databases (`$env:PROFSUR_DB_PATH`).
* **No Local LLMs:** Do not launch local LLMs (Ollama, local vLLM). Use approved cloud APIs or Python templates.
* **Manuscript Isolation:** The research paper repository in `paper/` is frozen and isolated. Never bleed software edits into paper paths.
* **Symbol Discovery:** Prefer Graphify (`graphify-out/GRAPH_REPORT.md`) or `codebase-memory-mcp` for symbol and call-graph discovery before inspecting source files.
* **Screen-to-Source Verification:** UI verification requires live, authenticated browser execution with physical screenshot verification saved to disk. HTTP `200` responses alone are not UI evidence.

---

## 8. Worker Completion Gate

A worker must stop immediately and refuse to proceed if:
1. The authorized task packet objectives are completed.
2. A required change exceeds the authorized file path allowlist.
3. The active base commit SHA does not match the contract.
4. Any forbidden path or protected database is modified.
5. Required evidence or credentials are unavailable.
