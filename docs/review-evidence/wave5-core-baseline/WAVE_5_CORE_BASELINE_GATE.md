# Wave 5 Core Engineering Baseline Gate

**Purpose:** define a durable engineering and truthfulness baseline. This gate does not claim scientific validation of IV, GMM, HDFE, ML, scenario, DiD, or other advanced methods.

**Reviewed baseline:** `88ab5c29c295abed19dd44820e809092806a433f`
**Initial code candidate:** `d5ffdf2b2d9f77d3f4f83bd2bf90a19475d4001f`

## Acceptance gates

1. **Repository and lineage integrity** — PASS requires the authorized branch to be clean, descendant-only, non-rewritten, and synchronized with its remote. BLOCKED if unexpected code changes, divergence, or history rewriting exists.
2. **Parser/runtime fail-closed behavior** — PASS requires requested variables, options, grouping, clustering, absorb variables, and interventions to execute exactly or return typed errors before estimation. BLOCKED for silent substitution or estimator dispatch after validation failure.
3. **Covariance semantics** — PASS requires conventional, robust, and requested-cluster behavior with explicit metadata and no mislabeled standard errors. BLOCKED for semantic drift or unsupported claims.
4. **Scenario truthfulness** — PASS requires canonical and alternate intervention syntax to preserve requested semantics and describe preview/partial behavior honestly. BLOCKED for fabricated counterfactual claims or silent intervention changes.
5. **HDFE truthfulness** — PASS requires absorb-list validation and partial/dependency-unavailable behavior to be explicit. BLOCKED for silent absorb changes or claims of scientific validation.
6. **GMM/Arellano–Bond/System-GMM claim truthfulness** — PASS requires experimental levels IV-GMM to remain distinct from dynamic-panel methods and diagnostics to remain descriptive unless formally implemented. BLOCKED for unsupported labels.
7. **UI typed-error and active-command binding** — PASS requires typed failures to reach the UI, success cards to be suppressed after failed estimation, and browser assertions to bind to the active terminal command. BLOCKED for stale/static assertions or misleading success states.
8. **Capability-status consistency** — PASS requires the registry, result metadata, generated document, and primary UI labels to agree. BLOCKED for drift or any false `VALIDATED` status.
9. **Database immutability** — PASS requires source and disposable-copy hashes to remain equal before and after audit. BLOCKED for mutation of the protected database.
10. **Independent native Playwright acceptance** — PASS requires a qualifying current-candidate native run with explicit journey/command results. BLOCKED for environment-only setup failure, incomplete run, or absent current-candidate evidence.
11. **Independent methodology review** — PASS requires an evidence-backed reviewer verdict against the final candidate. BLOCKED for bare labels, unsupported claims, or a reviewer environment limitation presented as a product defect.
12. **Remote GitHub verification** — PASS requires branch ref, API commit, local HEAD, and upstream to agree at 0/0 divergence. BLOCKED for unverified publication.
13. **Documentation and evidence consistency** — PASS requires historical results to remain attributed, current results to be identified, artifact hashes to be recorded, and reviewer limitations to be preserved. BLOCKED for provenance loss or contradictory current claims.
14. **No advanced method falsely marked VALIDATED** — PASS requires every advanced capability without separate scientific validation to remain non-validated. BLOCKED for promotion based only on routing, parsing, UI, or contract tests.

The final closure verdict is PASS only when every mandatory gate is PASS. A core baseline may remain BLOCKED even when engineering contracts pass if qualifying independent acceptance or methodology evidence is absent.
