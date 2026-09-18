# Clean KAIF Application Run — Identity

| Field | Value |
|---|---|
| Purpose | Fresh, uncontaminated application of KAIF to the ProfSur natural-language statistical-analysis workflow; design only, not a KAIF audit or ProfSur defect investigation |
| Started | 2026-09-18T11:06:20+05:30 |
| Model | OpenAI Codex, GPT-5 family |
| ProfSur branch | `agy/wave6-8-harness-repair-2026-09-11` |
| ProfSur commit | `fa97df7e1e6b43726c63590a47906d8ae8e5797d` |
| KAIF branch | `main` |
| KAIF commit | `6da1d29ec11ee6c30e1c347e45eb4b58ca153f7b` |
| Output location | `C:\Users\hemas\Downloads\kaif-clean-application-run` |

## Source worktree states at start

- ProfSurProject: dirty. `capital_structure.db` was modified and more than 589 untracked entries were reported; the status command also reported one inaccessible temporary directory. This run therefore treats the recorded commit as the sole product-evidence baseline and reads tracked-at-HEAD content only.
- kaif-design: clean (`main...origin/main`).
- Neither source repository is modified by this run.
- No branch, commit, push, reset, clean, stash, dependency installation, test, service, browser, cache, generated graph, or background process is part of this run.

## Contamination exclusions

- `C:\Users\hemas\Downloads\kaif-pilot-output` is prohibited and was not inspected or modified.
- FDI, Symphony, BioKaggle, and unrelated repositories are excluded.
- Files not tracked at the recorded ProfSur commit are excluded as product evidence, including files created after this run began.
- The Graphify outputs are not tracked at the frozen ProfSur commit. They were not regenerated or consumed because source repositories are read-only and generated artifacts are prohibited for this run. Static tracked source and repository documentation were used instead.

## Run boundaries

The delivery slice is limited to OLS, fixed-effects regression, company and year fixed effects, clustered standard errors, variable/specification clarification and validation, execution validation, responsible explanation, visible warnings/errors, and end-to-end traceability. No implementation code is produced.
