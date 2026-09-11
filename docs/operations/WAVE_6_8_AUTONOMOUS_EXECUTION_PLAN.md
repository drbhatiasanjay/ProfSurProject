# Waves 6–8 Autonomous Execution Plan

**Date:** 2026-09-11  
**Baseline:** `master` / `b5853fc`
**Status:** ACTIVE — MVP-bounded

## Reconciled scope

The latest Wave 6 validation-workbench design governs execution. The older
programme PRD describes a bidirectional language engine as Wave 6; that work is
compatible, but cannot promote an estimator or bypass the validation ledger.

## Wave 6

- Complete independent IV/HDFE benchmark runners and sample/assumption audits.
- Preserve GMM as a named IV-GMM proxy with the lag cap and unsupported wording.
- Enforce evidence identity, manifest integrity, and derived capability status.
- Keep `VALIDATED` derived only from numerical, assumption, methodology,
  reproducibility, and independent-review PASS results.

## Wave 7

- Define minimal immutable visualization, fact-sheet, narrative, and story
  artifacts around verified `CapabilityResult` values.
- Bind every artifact to an analysis-run/evidence reference and dataset/sample
  fingerprints.
- Add bounded challenge and reproduce actions without changing source data or
  silently changing estimator, sample, or method.
- Constrain narrative language by capability status and methodology evidence.

## Wave 8

- Select one read-only descriptive or already-validated researcher workflow.
- Expose immutable run/provenance records through that researcher path.
- Preserve role authorization, session isolation, source immutability, and the
  current left/right panel mapping.
- Do not introduce Redis, multi-host tenancy, production deployment, AST
  rewrite, credential rotation, or broad estimator promotion in this MVP slice.

## Gates and evidence

Each slice follows `goal → plan → implementation → test → evidence → review →
checkpoint`. Every implementation produces a GitHub-ready report under
`docs/implementation-reports/` and updates the handoff/status records.
Missing browser credentials produce `BLOCKED`, never guessed PASS.

## Parallel Antigravity scope

Antigravity may independently audit benchmark reproducibility, artifact schemas,
panel mapping, and adversarial status-forging cases. It must treat master as
read-only, avoid credential values, produce GitHub-ready Markdown, and never
promote capability status.
