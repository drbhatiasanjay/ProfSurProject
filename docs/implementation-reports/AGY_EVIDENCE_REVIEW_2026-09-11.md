# Antigravity Evidence Review — 2026-09-11

## Decision

**ACCEPTED WITH CORRECTIONS; not yet accepted as fresh UI evidence.**

Antigravity’s report is useful evidence lead material, but its acceptance
claims were not sufficient for baseline promotion because the referenced
matrix script and commit did not satisfy the project evidence contract.

## Verified artifacts

- Report received at `docs/review-evidence/2026_09_11_ANTIGRAVITY_AUDIT.md`.
- Matrix screenshot artifacts exist under `scratch/matrix_evidence/` for all
  four named profiles and both light/dark labels.
- `tests/test_panel_mapping_contract.py` is present and the canonical tracked
  suite later passed it.

## Findings requiring correction

1. `scratch/run_all_users_matrix.py` contained a hardcoded password assignment.
   This contradicted the secret-handling rule even though the value was not
   printed. The assignment was removed; the harness now requires the
   process-only `PROFSUR_VERIFY_PASSWORD` variable.
2. The same script used `time.sleep(2)` in its detached-DOM retry loop. This
   contradicted the no-fixed-sleeps rule. The retry now reacquires the visible
   terminal marker before retrying.
3. The Antigravity report identifies commit `d93e20a`, while the current
   canonical tip is later. Its claims are therefore not automatically proof
   against the current source state.
4. The reported background task handle is not available in this session.
   Existing screenshots prove artifact presence, not that every result was
   produced by the current canonical `app.py` process.

## Accepted evidence

- Duplicate-email fail-closed implementation and focused tests are independently
  verified in the canonical suite.
- GMM wording inventory and proxy classification are consistent with the
  current source review.
- Panel mapping contract passed in a clean process.
- The complete canonical tracked suite passed: **733 passed, 1 skipped**.

## UI acceptance status

The four-profile/two-theme matrix remains **NOT FRESHLY REPRODUCED** in this
Codex session because browser automation was unavailable and the approved
process-only password variable was absent. Do not promote the Antigravity
screenshots to fresh acceptance without rerunning the corrected harness from
root `app.py` on port 8501.

## Required next action

Run the corrected matrix in an available browser-enabled session with the
process-only password variable, then append its exact command, current commit,
profile/theme results, and evidence references here. Do not print or commit
the password or any bcrypt hash.
