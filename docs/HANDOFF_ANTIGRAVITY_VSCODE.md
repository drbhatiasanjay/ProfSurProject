# LeverageDebtAI / ProfSurProject
# Antigravity → VS Code / Cross-Agent Handoff

**Last Updated:** 2026-09-06  
**Canonical Operational Anchor:** Read [`CURRENT_STATUS.md`](../CURRENT_STATUS.md) FIRST before inspecting source code or running commands.

---

## 1. Handoff Objective & Operating Baseline
Resume development of the LifeCycle Leverage platform from durable repository state without relying on ephemeral IDE conversation memory.

- **Active Branch:** `master`
- **Head Commit:** `6075708` (`fix(auth): auto-assign display name for authenticated viewer accounts`)
- **Remote Qualification:** Local `HEAD` matches locally known tracking ref `origin/master` (`6075708`). No fresh network fetch performed under recovery guardrails.
- **Working Tree Policy:** The working tree contains user testing evidence and local database modifications. Treat untracked files as preserved evidence; do not reset, clean, stash, or checkout without authorization.

---

## 2. Mandatory First Step for All Incoming Agents
Every agent (Antigravity, Codex, Claude, Cline) MUST read:
1. [`CURRENT_STATUS.md`](../CURRENT_STATUS.md) — Current operational baseline, verified test evidence, and immediate resume point.
2. [`AGENTS.md`](../AGENTS.md) — Operating invariants, Ponytail minimal-code standard, and token optimization rules.
3. [`docs/CANONICAL_IMPLEMENTATION_PLAN.md`](CANONICAL_IMPLEMENTATION_PLAN.md) — Authoritative technical specifications for approved Workstreams 1 & 2.

---

## 3. Approved Workstreams
Feature development is strictly partitioned into two parallel, TDD-governed workstreams:

### Workstream 1: Stata CLI / NLP Enhancement
- **Target Branch:** `feature/stata-cli-nlp-highlighting`
- **Scope:** Gap command execution (`ivregress 2sls`, `test`, `predict`, `winsor2`), syntax-colored terminal input bar with autocomplete (`components/stata_editor.py`), bidirectional Natural Language ↔ Stata translation (`models/stata_nl_translator.py`), and live econometric explainer cards (`models/stata_explainer.py`).

### Workstream 2: Citation Inspector / Academic Literature Vault
- **Target Branch:** `feature/citation-inspector-modal`
- **Scope:** Structured academic metadata catalog with verified DOIs (`models/citation_vault_metadata.py`), interactive `@st.dialog` modal (`components/citation_inspector.py`), and cross-page badge inspection triggers.

*Explicit Non-Goal:* The post-restart AutoPrompt proposal is non-canonical and must not be implemented.

---

## 4. Operational Commands & Testing Invariants
- **Fast Test Suite:** `py -3.12 scripts/project_ops.py test --fast` or `pytest -q --tb=line`
- **Quiet Mode:** Always maintain concise output; avoid dumping raw 800+ line files into conversation context.
- **Local Dev Server:** Managed autonomously on `http://localhost:8501`.
- **Secrets Management:** Never hardcode credentials in code, documentation, or git commits. Read authentication details from `.streamlit/secrets.toml` or environment variables.
