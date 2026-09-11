# Antigravity Parallel Audit Brief — 2026-09-11

## Role and boundary

You are the independent Antigravity validation agent for `ProfSurProject`.
Work from a clean review context and treat `master` as read-only. Do not modify
`master`, push branches, deploy GCP, rotate credentials, run local LLMs, or run
the external AI natural-language sweep. Do not print, copy, hash, or record
passwords, bcrypt hashes, API keys, cookies, or tokens.

Antigravity findings are evidence and recommendations only. Codex owns
canonical implementation, integration, status promotion, and remote state.

## Evidence requirement

Produce GitHub-ready Markdown evidence in the repository’s approved evidence
path or as a proposed patch for Codex to apply. Do not leave acceptance evidence
only in local JSON, screenshots, terminal output, or hidden agent memory.
Every result must state: commit under review, timestamp, command/test, profile
and role (when applicable), expected result, actual result, evidence path, and
limitations. Never claim PASS from a timeout, stale DOM, healthy port alone, or
an unverified external-agent report.

## Audit tasks

### A. Authentication bootstrap — test-only

1. Inspect `auth.py`, the configured secret-loading path, and the SQLite
   `auth_users.email UNIQUE` constraint.
2. Test duplicate emails after casefolding and whitespace normalization.
3. Include records that would otherwise be skipped because their password
   entry is invalid or absent; configuration ambiguity must fail before any DB
   mutation.
4. Verify the failure is typed, generic, actionable, and does not echo the
   conflicting address or any secret.
5. Verify the database remains unchanged after rejection.
6. Return a recommendation and coverage table only; do not edit canonical code.

### B. System GMM wording inventory

Search current product/status documents, source, demos, and historical papers.
Classify each occurrence as exactly one of:

- `IMPLEMENTED`: callable in the canonical dispatcher and independently tested;
- `PROXY`: an explicitly limited approximation or named proxy;
- `HISTORICAL`: thesis, paper, demo, or background claim not representing the
  current callable product;
- `UNSUPPORTED`: not callable or intentionally fail-closed in the current app.

Do not perform a global search-and-replace. Report file, line/section, current
wording, classification, and recommended wording. Distinguish an implemented
function in `models/econometric.py` from a top-level Stata command exposed by
`models/stata_engine.py`.

### C. Canonical UI matrix

Use only root `app.py` on `http://localhost:8501/`. Authenticate at the root,
then click registered sidebar navigation. Test all configured profiles:
`profsurkumar`, `skumar`, `drbhatia`, and `sbhatia`, in both light and dark
themes. Verify `lc-navbar`, title-case navigation, Stata Studio, AI Assistant,
dataset/filters, and role visibility. Wait for command-specific new DOM markers;
never use fixed sleeps or stale cards. Record any profile-specific defect.

### D. Screen/code mapping drift

Review `docs/operations/AI_CHAT_SCREEN_CODE_MAPPING.md`, `app.py`, the global
sidebar, `pages/19_ai_assistant.py`, and `pages/23_stata_studio.py`. Check that
each left-panel control and right-panel action has one owner, survives the
expected Streamlit rerun, and is covered by source-to-screen evidence.

### E. Panel mapping runtime contract

Run `tests/test_panel_mapping_contract.py` in a clean, bounded process. If the
runner stalls or Windows resource contention prevents completion, report
`BLOCKED/INCONCLUSIVE`, capture the duration and process condition, and do not
convert it to PASS.

### F. Adversarial review

Challenge Codex’s proposed duplicate-email guard and wording changes against:
fail-closed behavior, no secret disclosure, no partial DB mutation, canonical
entrypoint rules, role isolation, rerun persistence, stale-evidence detection,
and unsupported-capability truthfulness.

## Deliverable

Return one concise Markdown report suitable for a GitHub PR description or
review comment. Include a closure matrix, exact evidence references, failed or
blocked checks, and explicit recommendations. Do not claim phase promotion.
