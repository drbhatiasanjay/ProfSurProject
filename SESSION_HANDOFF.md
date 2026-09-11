# ProfSurProject — Restart-Safe Operational Handoff

**Updated:** 2026-09-11  
**Workspace:** `C:\Users\hemas\Downloads\ProfSurProject`  
**Canonical branch:** `master`  
**Latest baseline:** `ce50085` (local; not yet published)
**Canonical demo:** `http://localhost:8501/`

## 1. Current truth

The current root application is `app.py`. It owns the Streamlit shell, fixed
header, global sidebar, dataset filters, theme, and `st.navigation()`.
`pages/19_ai_assistant.py` owns AI Chat content and page-specific controls.
`pages/23_stata_studio.py` owns the raw Stata interface.

Never launch a page file directly. Directly launching either page produces the
legacy auto-discovered lowercase sidebar and is archived behavior. Authenticate
at the root URL, then click the registered sidebar page.

## 2. Latest committed changes

- `82d9afb` — persisted direct Stata AI-chat follow-up actions.
- `fd71c83` — archived legacy shell convention, added source-to-screen mapping,
  synchronization contract, and four-user QA report.
- `8599dc6` — routed supported `xtset` and `lgraph` commands through AI Chat.
- `0437f2c` — recorded the honest 25-command matrix and current gaps.
- `6c89335` — bound AI panel context to the normalized active filter scope and
  added the four-profile panel-mapping regression contract.
- `5706617` — checkpointed panel-scope synchronization in the operational
  records.
- `e99bf6c` — corrected the panel-contract evidence status; runtime execution
  remains open rather than being reported as passed.

## 3. Verification status

### Passed

- Canonical 8501 Streamlit process restarted from root `app.py`; health endpoint
  returned `ok`.
- Four-user authenticated UI matrix passed for `drbhatia`, `profsurkumar`,
  `skumar`, and `sbhatia`: login, sidebar navigation, Stata estimation, and
  both themes.
- `xtset companycode year` executes successfully in the Stata engine and is now
  routed directly by AI Chat.
- 17 of the supplied 25 deterministic Stata inputs return successful results.
- Panel mapping contract is implemented for dataset vintage, year range,
  companies, life stages, industries, events, and all four roles. Source
  compilation passed; runtime execution remains pending after local resource
  contention.

### Open product gaps

The canonical dispatcher currently returns typed unsupported-command responses
for these eight inputs:

`ivregress`, `hdfe`, `gmm`, `didregress`, `test`, `predict`, `predict_ml`,
`scenario`.

These are real implementation gaps, not test failures to suppress. Do not
promote the 25-command matrix to VERIFIED until each is implemented or formally
deferred with an approved decision.

The AI natural-language equivalent sweep has not been run in this checkpoint.
It requires explicit authorization to transmit active panel context and the
provided prompts to the configured external LLM backend.

## 4. Evidence and mappings

- Screen/code mapping: `docs/operations/AI_CHAT_SCREEN_CODE_MAPPING.md`
- 25-command status: `docs/implementation-reports/AI_STATA_25_COMMAND_MATRIX_2026-09-10.md`
- Four-user QA: `docs/implementation-reports/AI_CHAT_FOUR_USER_MATRIX_2026-09-10.md`
- Canonical status: `CURRENT_STATUS.md`
- Session history: `SESSION_LOG.md`
- Project rules: `AGENTS.md`
- Orchestration loop: `docs/operations/AGENT_ORCHESTRATION_FRAMEWORK.md`

Evidence must be GitHub-ready Markdown. Local screenshots and JSON are useful
supporting artifacts but never the sole acceptance record.

## 5. Credential handling

- Approved sources are `.streamlit/secrets.toml` and approved environment
  variables such as `PROFSUR_VERIFY_PASSWORD`.
- Never write, print, commit, or place plaintext passwords or bcrypt hashes in
  handoff files, tests, prompts, screenshots, logs, or command output.
- Test profiles: `drbhatia` (admin), `profsurkumar` (researcher), `skumar`
  (researcher), and `sbhatia` (viewer).
- Use a process-only environment variable for authenticated automation. Clear
  it after the run. If absent, stop at the credential gate rather than guessing.
- Administrative credential rotation remains separate if any credential was
  previously exposed in historical artifacts.

## 6. Repeatable automation

1. Verify workspace and read `CURRENT_STATUS.md` first.
2. Check Graphify freshness; regenerate only when absent/stale with
   `graphify extract .` and `graphify cluster-only .`.
3. Kill only the intended local Streamlit listener before restarting 8501.
4. Launch the absolute root `app.py` with an explicit port.
5. Run focused deterministic tests, then the authenticated four-user matrix.
6. For UI tests, wait for the new result/card or command-specific marker after
   every Streamlit rerun; never read a previous card as the current result.
7. Record command, user, role, interface, expected/actual outcome, evidence
   reference, and timestamp in Markdown.
8. Run `git diff --check`, stage only intentional files, commit, and update
   this handoff plus `CURRENT_STATUS.md`/`SESSION_LOG.md`.

The reusable harness is `scratch/run_25_dual_matrix_8501.py`; its external AI
phase is opt-in and must not be silently run. Intentional invalid inputs count
as PASS only when the application fails closed with a typed response.

The complete non-development closure matrix is recorded in
`docs/operations/NON_DEVELOPMENT_CHECKLIST_2026-09-11.md`.

Today’s implementation checkpoint adds the duplicate-email bootstrap guard and
explicitly labels the internal dynamic-panel routine as an unverified IV-GMM
proxy. Evidence is in the two corresponding implementation reports.

The operations verifier also requires process-only `PROFSUR_VERIFY_PASSWORD`;
it has no plaintext CLI password fallback. See
`docs/implementation-reports/PROJECT_OPS_SECRET_GATE_2026-09-11.md`.

The XGBoost full-suite stall was isolated and bounded. XGBoost and LightGBM
now use `n_jobs=1`, consistent with Random Forest, to contain Windows thread
resource contention. Focused cross-validation checks passed for both models;
no performance improvement is claimed.

The full pytest collection audit is now concrete: plugin-disabled collection
reaches three untracked phase-test import mismatches and stops. See
`docs/implementation-reports/FULL_PYTEST_COLLECTION_AUDIT_2026-09-11.md`.
Focused auth/routing/panel checks pass; do not report the full suite as green.

The tracked debug-auth test is now collection-safe and secret-only. The latest
tracked-only collection reached 70% with no failures, then stalled at
`test_cross_validate_xgboost` and was stopped after 60 seconds. The full suite
remains open; this is recorded in the full-suite audit rather than treated as
green.

The active autonomous goal is to close today’s baseline safely. Its current
remaining gates are: reconcile the three untracked phase-test import
mismatches, diagnose the XGBoost stall in a bounded run, obtain the
process-only verification password for fresh four-profile browser evidence,
and receive explicit authorization before publishing the eight local commits.

The canonical 8501 health endpoint remains `ok`, but browser automation was
unavailable in this session. No fresh authenticated four-profile UI claim is
made.

Antigravity evidence was independently reviewed. Screenshot artifacts exist,
but the submitted matrix script contained a hardcoded test password and a
fixed retry sleep; both were corrected in the tracked-safe harness. The report
was tied to an older commit and its background task handle is unavailable, so
the UI claim remains not freshly reproduced. See
`docs/implementation-reports/AGY_EVIDENCE_REVIEW_2026-09-11.md`.

The consolidated deterministic regression gate passed in one clean process:
auth, AI/Stata routing, panel mapping, and the complete ML test class yielded
`19 passed in 74.05s` with plugin autoload disabled. This does not promote the
repository-wide suite to green.

The complete canonical tracked test set subsequently passed with
`733 passed, 1 skipped, 38 warnings in 279.18s`. This closes the prior tracked
XGBoost stall. Repository-wide collection still remains distinct because three
preserved untracked phase-test files import non-canonical modules/classes.

## 7. Lessons learned

- A healthy port is not proof of the correct application. Verify the launch
  command and visible shell marker (`lc-navbar`, title-case registered pages).
- Streamlit reruns recreate the shell. Page controls must extend the global
  sidebar, not create a competing navigation system.
- AI Stata routing must stay synchronized with engine dispatch; missing `xtset`
  caused an avoidable Anthropic call.
- Stateful post-estimation commands must not be cached without model identity
  and result context.
- Harnesses must synchronize on newly rendered results, not fixed sleeps or the
  last DOM card. Fixed sleeps caused stale-card false classifications.
- A broad pytest stall is not a pass; use quiet focused tests and report
  Windows/process limitations.
- Antigravity claims are evidence leads, not acceptance proof. Verify files,
  branch, process, output, and report locally before promotion.

## 8. Token, memory, and context-drift controls

- Read this handoff, `CURRENT_STATUS.md`, and `SESSION_LOG.md` before decisions.
- Use Graphify/search for discovery, then read narrow source slices.
- Keep reports concise and append-only; reference large screenshots/JSON from
  Markdown instead of loading them into context.
- Maintain one canonical branch and one canonical port for demo evidence.
- Record material work as `goal → plan → implementation → test → evidence →
  review → checkpoint`.
- Never carry experimental-worktree claims into `master` without reproducible
  evidence.
- Every checkpoint records commit, server command, test command, result, open
  gaps, credential source location only, and next action.

## 9. Resume procedure

```powershell
Set-Location C:\Users\hemas\Downloads\ProfSurProject
Get-Content CURRENT_STATUS.md -Tail 40
Get-Content SESSION_HANDOFF.md -Tail 40
git status --short
git log -3 --oneline
```

Resume from the eight-command implementation/defer decision and the separately
authorized AI natural-language test gate. Do not restart old worktrees or old
page-file entrypoints for demo evidence.
