# ProfSurProject — Restart-Safe Operational Handoff

**Updated:** 2026-09-11  
**Workspace:** `C:\Users\hemas\Downloads\ProfSurProject`  
**Canonical branch:** `master`  
**Latest published baseline:** `f8673a2` (origin/master synchronized)
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

The Wave 7 provenance renderer and Wave 8 researcher-slice contracts are now
implemented through commit `b5853fc`, with documentation checkpoint `e3f6e2a`.
The focused Wave 6/7/8 gate passed with `20 passed, 1 warning`; the project
fast gate passed with `6 passed, 1 warning`; changed modules compile cleanly.
The root 8501 health endpoint returned `ok`. Fresh authenticated browser
verification is still not claimed because no browser automation surface or
process-only verification credential is available in this session.

The current Wave 6/7/8 integration adds a deterministic descriptive Gemini
tool, typed provenance stream events, canonical AI-page metadata rendering, and
stable researcher-slice serialization. Focused verification is `42 passed, 1
warning`; the latest GitHub workflow for this head passed. A repository-wide
pytest attempt timed out at 120 seconds, including collection-only mode; this
remains an unresolved broad-suite gate and is not reported as green.

Wave 8 PR-02 is now mounted on the canonical Overview page in commit `3be735d`.
The existing root navigation is unchanged. For `admin` and `researcher` roles,
the page exposes a read-only Researcher Evidence Slice bound to
`public-panel` and the active panel run. `view`, `reproduce`, and `challenge`
are the only actions; every action remains `NOT_VALIDATED` and cannot promote
an estimator or widen authorization. Focused Wave 6/7/8 verification is
`22 passed, 1 warning`; changed modules compile and diff checks pass.

The current committed code/documentation checkpoint is `f8673a2`, published on
origin/master. Browser and authenticated acceptance remain unclaimed because
Chromium and the process-only verification credential are unavailable.

A fresh anonymous headless smoke check was attempted after this checkpoint;
Playwright could not launch because its Chromium executable is not installed.
This is an environment blocker, not an application failure. No browser binary
was downloaded automatically.

The independent Wave 6 benchmark fixture slice is published at `2208734`, with
manifest emission added in `b04a66c`; the synchronized documentation checkpoint
is published in `500e7b9`.
It provides seeded known-answer IV/2SLS and entity-demeaned HDFE references
with dataset/sample fingerprints and rank/sample checks. Focused fixture and
benchmark-contract tests passed `7 passed, 1 warning`; two manifest tests hit
Windows pytest temporary-directory ACL contention and are not counted as a
pass. Production capabilities remain unpromoted.

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

## 10. Codex restart checkpoint — 2026-09-12

### Active repair worktree

- Path: `C:\Users\hemas\Downloads\ProfSurProject\.worktrees\codex-wave6-8-remediation-2026-09-12`
- Branch: `codex/wave6-8-remediation-2026-09-12`
- Base HEAD: `ab7aeb2`
- Shared/master worktree: not modified by Codex.
- Deployment `secrets.toml` hardening and the common MVP test-password policy remain explicitly deferred.

### Implemented in the isolated worktree

- Session-scoped analytical model and panel state with AI Assistant/Stata Studio wiring.
- Fail-closed FE/RE estimation; removed hidden leverage rescaling and positional panel inference.
- Explicit model binding for Hausman, VIF, `coefplot`, `esttab`, and stored estimates.
- Legacy proxy GMM naming and truthful output labeling.
- Exact calendar-aware GMM lags; missing periods no longer become row-position lags.
- AI cache revision `wave6-8-context-v2`.
- Normalized unsupported/engine error codes.
- `scripts/repo_governance_guard.py` fail-fast Git metadata preflight.

### Verification before restart

- Focused model-context/panel tests: `10 passed`.
- Fast project gate: `6 passed`.
- Changed Python modules compile successfully.
- Governance guard reproduces the environment failure with exit code `2`:
  `.git\worktrees`, `.git\objects`, and `.git\refs` are not writable.
- No commit was created because Git cannot write its index/object database.

### Confirmed environment root cause

This is not an application defect or stale `index.lock`. The shared repository
Git metadata is protected by Windows ACL/read-only state, and concurrent agent/
IDE Git activity has repeatedly amplified the contention. Rebooting alone is
not a fix.

### Required post-restart sequence

1. Close Antigravity and VS Code Git/Source Control operations.
2. Do not launch the Streamlit app or validation harness yet.
3. From an elevated PowerShell, grant Modify only to the current Windows user
   on this repository's `.git` directory and clear read-only attributes:

```powershell
$repo = "C:\Users\hemas\Downloads\ProfSurProject"
$git = "$repo\.git"
$user = "$(whoami)"
icacls $git /inheritance:e /grant:r "${user}:(OI)(CI)M" /T
attrib -R "$git\*" /S /D
python "$repo\.worktrees\codex-wave6-8-remediation-2026-09-12\scripts\repo_governance_guard.py"
```

4. Expected guard result: `READY: writable Git metadata ...`.
5. Return to the isolated worktree, run `git diff --check`, stage only the
   intentional remediation/test/evidence files, and commit.
6. Run focused tests, the fast gate, then the optimized authenticated UI gate.
7. Update this handoff with the actual commit SHA, test results, evidence paths,
   and unresolved items. Do not claim completion before those checks pass.

### Governance rule for future agents

Run `python scripts/repo_governance_guard.py` before any long test or commit.
Use one canonical worktree plus one validation worktree. Never run concurrent
Git writers against the shared repository metadata. AGY remains validation-only
and must publish GitHub-ready Markdown evidence without modifying master.

### User-observed UI smoke note — 2026-09-12

The user manually verified that `drbhatia` can open both Stata Studio and AI
Assistant in the current demo. Chat-specific issues were observed and are
intentionally deferred for a later discussion. This is useful smoke evidence,
but it is not a substitute for the authenticated automated matrix or a clean
commit/evidence reconciliation.

### AGY validation status — 2026-09-12

AGY reports a replacement MVP harness, `run_mvp_validation.py`, replacing the
older `run_final_validation_loop.py`. Its reported run `task-3930` is still
initializing and has not produced acceptance evidence. The prior 22-case run
remains invalid because of the obsolete `section.main` selector. AGY must
finish the smoke test, publish the six GitHub-ready Markdown artifacts, and
report exact PASS/FAIL/BLOCKED totals before any phase promotion. AGY must not
close its task until the handoff, selector contract, defect status, and run
SHA are synchronized.

The Codex integration gate remains the repository governance guard:
`scripts/repo_governance_guard.py` must return `READY` after the ACL repair.
Only then may Codex commit the isolated remediation and reconcile AGY's report.

### AGY final MVP matrix review — 2026-09-12

AGY's isolated run `AGY-W6-8-2UFJDIUM` on branch `agy-validation-w6-8-2`,
HEAD `4a96d765e1a461dfe38c721273c13c1c9f233c4b`, port `8503`, completed with
`PASS 26 / FAIL 30 / BLOCKED 0` out of 56. The report is a **FAILED validation
run**, not acceptance evidence.

Evidence paths in the AGY worktree:

- `docs/review-evidence/AGY_W6_8_ORTHOGONAL_VALIDATION_AGY-W6-8-2UFJDIUM.md`
- `docs/review-evidence/AGY_W6_8_DEFECT_REGISTER_AGY-W6-8-2UFJDIUM.md`
- `docs/review-evidence/AGY_W6_8_HANDOFF_TO_CODEX_AGY-W6-8-2UFJDIUM.md`

Classification of the observed failures:

- Eighteen AI rows captured the transient `Working...` state and did not
  prove a final dispatch marker. This is insufficient to distinguish an AI
  backend failure from harness synchronization failure; no product fix is
  authorized from these rows.
- `xttest0`, `xtserial`, `coefplot`, and `margins` were expected as typed
  rejections but Stata Studio returned results. This is a capability-registry/
  harness expectation mismatch requiring reconciliation before rerun, not an
  automatic product regression.
- The `drbhatia` summarize failure is an alias/identity assertion mismatch and
  requires normalized command/result matching.
- The prior 22-row `section.main` run remains `HARNESS_INVALID` and is not
  reused.

No phase is promoted. The next validation must first reconcile the live
capability registry and improve AI completion synchronization, then rerun the
affected cases with a fresh run ID. The Git governance guard remains the
Codex commit gate and currently reports unwritable metadata.

## 2026-09-12 — Current remediation checkpoint

- Continue in the isolated remediation worktree on branch
  `codex/wave6-8-remediation-2026-09-12` (base `6fc56e9`).
- The shared checkout is intentionally untouched. Exclude
  `capital_structure.db` from all staging/reset operations.
- Windows Git metadata repair is complete. The governance guard reports
  `READY: writable Git metadata`; commit/push can proceed after review.
- Automated checkpoint: 7 defect tests, 84 affected analytical/cache/AI/Stata
  tests, 103 numerical/page tests, and 142 latest page/defect/chat tests pass;
  compilation and diff checks pass.
- No authenticated four-profile browser closure claim exists. AGY's 26 PASS /
  30 FAIL run remains failed validation evidence.
- Resume with the canonical root `/` and a reduced distinct-role matrix: admin,
  researcher, second researcher/session isolation, and viewer. Do not run 400
  companies across four profiles.
- Full UI overhaul remains deferred.
