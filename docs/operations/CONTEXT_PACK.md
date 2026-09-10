# ProfSurProject Canonical Context Pack

Updated: 2026-09-10  
Purpose: compact restart anchor for Codex and bounded reviewers

## Canonical repository

- Repository: `drbhatiasanjay/ProfSurProject`
- Worktree: `.worktrees/wave5-independent-review-repair`
- Branch: `reconcile/wave5-independent-review-repair-2026-09-08`
- Last locally created commit: `021a2cf6484f47c3bffa90c95cac341dddf62f18`
- Last published upstream: `dcddc1007c2e6210e3592a7b45b40c6a0d6c097e`
- Current divergence: `0 behind / 2 ahead`
- Push blocker: Git HTTPS receives an invalid cached credential despite valid
  GitHub CLI identity; a separate bad Codex checkpoint reference was reported.
- Do not delete or repair either issue destructively without a scoped diagnosis.

## Product truth

ProfSur is a grounded, explainable research workbench. It must distinguish
facts, computations, interpretations, hypotheses, and unsupported claims; fail
closed on invalid or unsupported requests; preserve source-data immutability;
and expose an action/evidence trace rather than private chain-of-thought.

Codex owns canonical integration and adjudication. External model output is
untrusted evidence. Fresh-context review is required when independence matters.

Advanced methods—including IV, GMM, HDFE, ML, scenario, DiD, and forecasting—
remain non-validated unless separate numerical, methodological, and
reproducibility evidence exists. The legacy GMM routine is not System GMM,
Arellano–Bond, or Blundell–Bond.

## Wave 5 status

- Core engineering baseline: PASS at the last completed closure transaction.
- Independent methodology review: PASS.
- Independent native Playwright acceptance: PASS.
- Canonical full automation evidence: `871 passed, 1 skipped, 37 warnings`.
- Historical `852 passed` evidence is superseded, not combined with 871.
- Source database hash was preserved in the closure evidence.
- No PR merge, deployment, master/main merge, or Wave 6 start is authorized.

## Active roadmap

Phase 12 is DRAFT: Explainable and Grounded Orchestration.

Target vertical slice:

`query → intent → evidence → plan → computation → visible action trace → result → uncertainty`

Immediate scope is intent classification, evidence labels, typed refusal,
reproducible result envelopes, visible status propagation, and adversarial
regression cases using an existing supported capability.

Deferred scope includes provider orchestration, parallel simulations,
self-learning, new econometric methods, and scientific validation of advanced
capabilities.

## Current planning artifacts

- `INTENT.md` — mission and operating principles.
- `NORTH_STAR.md` — user-visible product outcome and capability ladder.
- `.planning/ROADMAP.md` — phases and lifecycle states.
- `.planning/phases/12-explainable-grounded-orchestration/12-01-PLAN.md` — active
  Phase 12 draft.
- `docs/planning/FDI_ADOPTION_MATRIX.md` — selective TempFDI adoption and
  practicality triage.
- `docs/PLANNING_ADVERSARIAL_REVIEW_PROMPT.md` — review protocol.

## Operating rules

1. Verify branch, SHA, upstream, divergence, and tracked status first.
2. Read this pack and `CURRENT_STATUS.md` before project work.
3. Use `lean-ctx` search-first and narrow reads.
4. Preserve all untracked evidence and the source database.
5. Stage only explicitly scoped files.
6. Require adversarial review before a draft becomes a baseline.
7. Keep implementation, evidence, review, and closure heads distinct.
8. Do not accept reviewer labels without examining underlying evidence.
9. Do not expose credentials or private chain-of-thought.
10. Stop and report if a request expands beyond the stated phase or authority.

## Next action

Resolve the Git publication blocker safely, then obtain a fresh adversarial
review of the FDI adoption matrix and Phase 12 plan. No Phase 12 implementation
is authorized until that review is reconciled.
