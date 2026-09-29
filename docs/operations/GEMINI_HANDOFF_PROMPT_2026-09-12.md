# Gemini continuation prompt — ProfSurProject

Continue work only in:

`C:\Users\hemas\Downloads\ProfSurProject\.worktrees\codex-wave6-8-remediation-2026-09-12`

Repository: `ProfSurProject`  
Branch: `codex/wave6-8-remediation-2026-09-12`

## Current checkpoint

Codex completed and pushed the Wave 6–8 remediation checkpoint. Relevant commits:

- `b3fce3d` — analytical, persistence, role, and UI remediation.
- `bd0d294` — synchronization documentation.
- `f9e6e1f` — shared dark sidebar-arrow and dropdown selectors.

The user manually verified the reduced distinct-profile browser journeys and
confirmed the browser issue is resolved. Do not claim a new acceptance failure
without reproducing it from the canonical root app.

## Verified evidence

- GitHub targeted hook: **121 passed, 1 warning**.
- Streamlit `/_stcore/health`: `ok`.
- `capital_structure.db` was intentionally excluded from commits.
- Role-aware navigation, analytical result identity, cache/persistence fixes,
  truthful advanced-method labels, and evidence-slice relocation are complete.

## Known deferred work

The full dark-mode visual overhaul is not complete. Known cosmetic issues are:

- Native sidebar `<<`/`>>` styling is inconsistent on some Streamlit layouts.
- Some native BaseWeb dropdowns still do not visually match the intended dark
  dropdown in every page.
- Chat-bar polish remains deferred.

Do not mix this cosmetic work with analytical/authentication remediation.

## Safe next task

If continuing development, first inspect the current branch and run a small
visual reproduction matrix for only:

1. Settings sidebar collapse/reopen.
2. Data Explorer dropdown.
3. Peer Benchmarks dropdown.
4. AI Assistant chat input.

Use the canonical root URL `/`, not a direct page launch. Preserve the global
sidebar contract. Do not run 400 companies × 4 profiles. Do not modify or stage
`capital_structure.db`. Commit and push only intentional source/docs changes.

If no cosmetic task is requested, leave the branch unchanged and proceed to the
next product-priority item with a new explicit scope.
