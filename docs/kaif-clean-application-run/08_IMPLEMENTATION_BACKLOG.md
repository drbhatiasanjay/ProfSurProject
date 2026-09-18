# Implementation Backlog

The backlog uses tracer-bullet vertical slices. Every slice has acceptance criteria, required tests, rollback, owner role, priority, and blockers. Story identifiers are design identifiers, not claims about exact file changes.

## Epic E0 — Governance and contracts

### Slice S0 — Contract and policy foundation

#### E0-S0-01 — Define statistical specification schema

- **Story:** As an engineering and method team, define a versioned specification that represents OLS/FE, variable roles, company/year FE, covariance/cluster, panel keys, filters, and missing policy without free-form execution text.
- **Business rationale:** Creates one reviewable handoff from intent to execution.
- **Technical scope:** JSON/YAML schema, canonicalization, hashes, versioning, examples, migration policy.
- **Dependencies:** Method-owner decisions Q-05–Q-11; data catalog interface.
- **Acceptance criteria:** Required fields/enums defined; `additionalProperties=false`; round-trip canonicalization stable; unsupported fields rejected; facts/defaults visibly tagged.
- **Required tests:** Schema positive/negative/property tests; canonical hash determinism; version-compatibility tests.
- **Rollback:** Retain prior schema version; no runtime activation.
- **Owner role:** Backend/statistical engineer + statistical method owner.
- **Priority:** P0.
- **Unresolved blocker:** Exact method/threshold policy approval.

#### E0-S0-02 — Define request, approval, authorization, result, error, and trace contracts

- **Story:** As a reviewer, I can reconstruct every transition and verify that the approved specification is the one executed.
- **Business rationale:** Satisfies traceability and prevents stale or changed execution.
- **Technical scope:** Immutable IDs, hashes, state events, idempotency, result and error schemas, trace export format.
- **Dependencies:** E0-S0-01; retention/access decisions.
- **Acceptance criteria:** All contracts versioned; every state transition linkable; approval binds user/spec/dataset/filter; result identifies estimator/effects/covariance/sample; errors include recovery; trace export has canonical JSON and human summary.
- **Required tests:** Contract/schema tests; tamper/hash tests; transition tests; idempotency/replay tests; export round trip.
- **Rollback:** Use prior contract version; additive storage only.
- **Owner role:** Backend engineer + security + method owner.
- **Priority:** P0.
- **Unresolved blocker:** Q-12, Q-13, Q-19, Q-28.

#### E0-S0-03 — Establish capability matrix and statistical policy

- **Story:** As a researcher, I receive predictable support/refusal for every first-slice combination.
- **Business rationale:** Prevents silent substitution and unsafe execution.
- **Technical scope:** OLS/FE variants, FE/cluster combinations, sample/group/cluster thresholds, missingness and collinearity severity, explanation rules.
- **Dependencies:** Statistical method owner named.
- **Acceptance criteria:** Every combination maps to supported/warning/error; thresholds are configurable and approved; no default is presented as fact; policy version is traceable.
- **Required tests:** Exhaustive decision-table tests; boundary-value tests; unsupported substitution tests.
- **Rollback:** Pin prior policy; disable affected capability.
- **Owner role:** Statistical method owner + statistical engineer.
- **Priority:** P0.
- **Unresolved blocker:** Q-02, Q-06–Q-11, Q-20, Q-26.

#### E0-S0-04 — Curate active variable catalog contract

- **Story:** As a researcher, I see authoritative variable names, labels, units, roles, and safe aliases.
- **Business rationale:** Reduces ambiguity and interpretation errors.
- **Technical scope:** Catalog derived from active schema, steward metadata, alias uniqueness, role/type constraints, catalog version.
- **Dependencies:** Data owner and canonical panel decision.
- **Acceptance criteria:** Every first-slice variable has name/type/unit/description/roles; ambiguous aliases are not auto-resolved; unavailable variables are visible; catalog version enters spec/trace.
- **Required tests:** Alias collision tests; schema/catalog drift tests; data-type/role tests.
- **Rollback:** Pin previous catalog; require manual exact names.
- **Owner role:** Data steward + backend engineer.
- **Priority:** P0.
- **Unresolved blocker:** Q-03, Q-04.

## Epic E1 — Deterministic validation and execution

### Slice S1 — Approved OLS/FE vertical path

#### E1-S1-01 — Implement pure specification preflight

- **Story:** As a researcher, I see blocking errors and material warnings before approval.
- **Business rationale:** Avoids unsafe or misleading runs.
- **Technical scope:** Method/role validation, active-column/type checks, panel uniqueness, FE/cluster checks, missingness/sample profile, rank/collinearity preflight, canonical executor request.
- **Dependencies:** E0-S0-01, E0-S0-03, E0-S0-04.
- **Acceptance criteria:** No mutation; deterministic results; all codes follow error contract; sample counts disclosed; no silent fallback; generated request round-trips to spec.
- **Required tests:** Unit/property tests; missing/constant/duplicate/low-sample/low-cluster/rank fixtures; capability matrix coverage.
- **Rollback:** Disable affected capability; retain direct current workflow.
- **Owner role:** Statistical/backend engineer.
- **Priority:** P0.
- **Unresolved blocker:** Approved thresholds and catalog.

#### E1-S1-02 — Build authorized executor adapter

- **Story:** As the system, execute only an approved immutable OLS or two-way-FE specification.
- **Business rationale:** Separates model/user intent from bounded computation.
- **Technical scope:** Authorization token verification, enum-to-engine mapping, OLS HC1, company/year FE, company cluster, timeout/idempotency, canonical command representation.
- **Dependencies:** E0-S0-02, E1-S1-01.
- **Acceptance criteria:** Raw text cannot enter executor; exact requested options preserved; repeat with same idempotency key cannot duplicate side effects; output conforms to result contract.
- **Required tests:** Statistical fixtures; permission/hash/idempotency tests; timeout/exception tests; parameter capture tests.
- **Rollback:** Feature flag off; disable capability ID.
- **Owner role:** Statistical engineer.
- **Priority:** P0.
- **Unresolved blocker:** Q-06–Q-08 and method-owner parity references.

#### E1-S1-03 — Build result validator and validation-ledger integration

- **Story:** As a reviewer, I know whether the result is numerically, methodologically, and reproducibly validated.
- **Business rationale:** Prevents successful process exit from being mistaken for valid analysis.
- **Technical scope:** Fidelity/hash checks, sample accounting, finite/range/structure checks, omissions/warnings, fixture references, derived validation status.
- **Dependencies:** E1-S1-02; approved validation semantics.
- **Acceptance criteria:** Critical failure blocks explanation; `VALIDATED` is derived only; all requested omissions accounted; evidence refs safe and unique.
- **Required tests:** Mismatch/tamper/nonfinite/omission/sample fixtures; ledger integrity tests; deterministic status tests.
- **Rollback:** Mark capability not validated; disable guided execution.
- **Owner role:** Statistical engineer + method owner.
- **Priority:** P0.
- **Unresolved blocker:** Reviewer gate policy and numerical tolerances.

## Epic E2 — Guided user journey

### Slice S1 — Clarify, review, approve, execute, recover

#### E2-S1-01 — Create deterministic specification form and clarification UI

- **Story:** As a researcher, I can complete/correct every field without the model.
- **Business rationale:** Provides transparency and outage fallback.
- **Technical scope:** Method, variable roles, effects, covariance/cluster, filters, missing policy, candidate definitions, persistent state.
- **Dependencies:** E0 contracts/catalog; E1 preflight.
- **Acceptance criteria:** All fields keyboard operable; ambiguous candidates labeled; values survive reruns/errors; unsupported options disabled/explained; focus moves to first issue.
- **Required tests:** Component/state tests; accessibility keyboard/focus/name tests; error recovery tests.
- **Rollback:** Hide guided form; current journeys remain.
- **Owner role:** Streamlit/frontend engineer + product/accessibility.
- **Priority:** P0.
- **Unresolved blocker:** Q-21 and approved UX wording.

#### E2-S1-02 — Add schema-constrained parser adapter

- **Story:** As a researcher, natural language prefills the deterministic specification without gaining execution authority.
- **Business rationale:** Reduces manual translation while retaining control.
- **Technical scope:** Bounded context, structured output, one repair retry, prompt/version hashes, uncertainty/ambiguity output, manual fallback.
- **Dependencies:** E2-S1-01; provider/data approval for pilot; prompt pack.
- **Acceptance criteria:** Model receives no raw rows; extra/invalid fields rejected; no direct tool execution; failure opens populated manual form; explicit/ambiguous golden thresholds met.
- **Required tests:** Mock provider contract tests; parser golden/adversarial set; schema-repair/fallback tests; redaction tests; token cap tests.
- **Rollback:** Disable parser; deterministic form remains.
- **Owner role:** AI engineer + method owner + security.
- **Priority:** P0 for pilot, production blocked.
- **Unresolved blocker:** Q-14–Q-17.

#### E2-S1-03 — Build specification preview, diff, approval, and authorization UX

- **Story:** As a researcher, I approve the exact version and material warnings before execution.
- **Business rationale:** Makes human control meaningful and auditable.
- **Technical scope:** Original-to-normalized diff, sample preview, warnings, generated command, unselected approve/reject, hash binding, invalidation on context change.
- **Dependencies:** E0-S0-02, E1-S1-01.
- **Acceptance criteria:** No approval while blockers/unresolved fields exist; changes invalidate approval; material warnings require acknowledgement; role denial visible; stale approval cannot execute.
- **Required tests:** State-transition, hash, stale approval, warning acknowledgement, role, rerun, accessibility tests.
- **Rollback:** Disable approval path and guided execution.
- **Owner role:** Frontend/backend engineer + product/security.
- **Priority:** P0.
- **Unresolved blocker:** Q-12, Q-13, Q-24.

#### E2-S1-04 — Present validated result, warnings, and recovery

- **Story:** As a researcher, I see what ran, what data were used, what was omitted, and what to do next.
- **Business rationale:** Supports correct decisions and reduces confusion.
- **Technical scope:** Result summary, method/sample metadata, coefficient table, warning/error cards, validation status, revise/retry/export actions.
- **Dependencies:** E1-S1-03.
- **Acceptance criteria:** Critical result failure shows no normal explanation; every warning has severity/consequence; method/effects/cluster/sample always visible; no color-only meaning; trace ID shown.
- **Required tests:** Rendering snapshots/component tests; warning/error matrix; accessibility; failure/retry paths.
- **Rollback:** Fall back to raw bounded existing result rendering for internal reviewer only; disable feature for users.
- **Owner role:** Frontend engineer + method owner/product.
- **Priority:** P0.
- **Unresolved blocker:** Approved wording/severity policy.

## Epic E3 — Responsible explanation and traceability

### Slice S1 — Deterministic explanation and reproducibility

#### E3-S1-01 — Implement deterministic statistical summary

- **Story:** As a researcher, I receive an accurate explanation even when the model is unavailable.
- **Business rationale:** Removes provider dependence from correctness.
- **Technical scope:** Templates for OLS and two-way FE, magnitude/interval/p-value, FE/cluster/sample, omissions, limitations, causal boundary.
- **Dependencies:** Validated result contract and explanation policy.
- **Acceptance criteria:** All facts derive from contract; exact values match; association language used; required limitations present; no literature/causal additions.
- **Required tests:** Golden text facts; number/unit checks; prohibited phrase tests; missing/omitted term cases.
- **Rollback:** Display validated structured result without narrative.
- **Owner role:** Statistical engineer + method owner.
- **Priority:** P0.
- **Unresolved blocker:** Q-26.

#### E3-S1-02 — Add optional bounded explanation refinement

- **Story:** As a researcher, I receive readable prose without changing the validated facts.
- **Business rationale:** Improves comprehension while retaining deterministic authority.
- **Technical scope:** Result-only prompt, no tools, one call, prompt hash, exact-number/warning/causal checks, template fallback.
- **Dependencies:** E3-S1-01; provider approval.
- **Acceptance criteria:** Failure or policy mismatch falls back to deterministic summary; no new numbers/variables/claims; evaluation thresholds pass.
- **Required tests:** Explanation golden/adversarial suite; exact-number and warning-preservation checks; outage/cost-cap fallback.
- **Rollback:** Disable optional refinement.
- **Owner role:** AI engineer + method owner.
- **Priority:** P1.
- **Unresolved blocker:** Q-14–Q-17, Q-26.

#### E3-S1-03 — Persist and export trace bundle

- **Story:** As a reviewer, I can reconstruct request, revisions, approval, execution, validation, and explanation.
- **Business rationale:** Enables reproducibility and accountability.
- **Technical scope:** Additive records/events, hash links, access control, redaction, JSON/human export.
- **Dependencies:** E0-S0-02; retention policy.
- **Acceptance criteria:** Required trace completeness 100%; tamper detected; role access enforced; export validates; secrets absent.
- **Required tests:** Persistence/transaction/failure tests; trace completeness; tamper; authorization; redaction; export parse.
- **Rollback:** Stop new guided execution if trace write unavailable; do not delete existing records.
- **Owner role:** Backend engineer + security/data owner.
- **Priority:** P0.
- **Unresolved blocker:** Q-15, Q-19.

## Epic E4 — Evaluation, observability, and operations

### Slice S2 — Hardening and pilot readiness

#### E4-S2-01 — Implement golden and statistical parity suites

- **Story:** As the method owner, I can approve behavior and numerical correctness before release.
- **Business rationale:** Makes quality measurable and regression-resistant.
- **Technical scope:** `07` scenarios, frozen synthetic/de-identified fixtures, independent expected results, CI gates, human-review sampling.
- **Dependencies:** All S1 components; method-owner references.
- **Acceptance criteria:** All global thresholds met; critical failures zero; exact suite/version evidence stored; human sign-off recorded.
- **Required tests:** The suite itself, mutation/negative controls, determinism, fixture integrity.
- **Rollback:** Block promotion; pin previous accepted capability/prompt/policy.
- **Owner role:** Evaluation engineer + method owner.
- **Priority:** P0.
- **Unresolved blocker:** Named method owner and approved thresholds/tolerances.

#### E4-S2-02 — Add correlated telemetry and dashboards

- **Story:** As operations/product, I can locate failures, measure quality/latency/cost, and monitor adoption without exposing raw data.
- **Business rationale:** Supports pilot decisions and safe operation.
- **Technical scope:** OTel-compatible IDs/spans/metrics/logs, redaction, stage dashboards, alerts.
- **Dependencies:** Trace IDs; logging/privacy policy.
- **Acceptance criteria:** End-to-end correlation; no raw rows/secrets; critical alerts tested; stage latency/token/cost and quality counters visible.
- **Required tests:** Telemetry contract; redaction; cardinality; alert injection; trace sampling.
- **Rollback:** Disable optional telemetry export; retain safe minimal audit events.
- **Owner role:** Operations engineer + security.
- **Priority:** P1.
- **Unresolved blocker:** Q-15, Q-18, Q-25.

#### E4-S2-03 — Accessibility, failure drills, and runbook

- **Story:** As a user/operator, I can recover from provider, executor, and persistence failures and use the workflow accessibly.
- **Business rationale:** Required for production trust and inclusion.
- **Technical scope:** WCAG acceptance, timeout/retry/idempotency, feature rollback, provider/form fallback, incident and support runbook.
- **Dependencies:** S1 complete; ownership/SLO decisions.
- **Acceptance criteria:** All accessibility scenarios pass; failure drills produce expected states; rollback demonstrated; support ownership documented.
- **Required tests:** Keyboard/screen-reader review; chaos/fault injection; canary/rollback drill; concurrency/load test.
- **Rollback:** Disable guided feature; current workflows remain.
- **Owner role:** Product/accessibility + operations + engineering.
- **Priority:** P0 for release.
- **Unresolved blocker:** Q-18, Q-21, Q-25, Q-29, Q-30.

## Epic E5 — Controlled production pilot

### Slice S3 — Pilot and release decision

#### E5-S3-01 — Run feature-flagged researcher pilot

- **Story:** As Product and the method owner, evaluate real workflow value and risk with a bounded cohort.
- **Business rationale:** Establishes baseline and validates adoption without broad exposure.
- **Technical scope:** Approved cohort, canary, dashboards, reviewer sampling, feedback taxonomy, incident/rollback readiness.
- **Dependencies:** S2 exit; all production blockers resolved.
- **Acceptance criteria:** Two approved evaluation windows with no critical failure; KPI baselines established; correction/escalation burden reviewed; owners sign release/defer decision.
- **Required tests:** Preflight smoke through authenticated UI, acceptance regression, load/capacity, rollback drill, trace sampling.
- **Rollback:** Feature flag off and prior Cloud Run revision; preserve evidence.
- **Owner role:** Product + method owner + operations/security.
- **Priority:** P1 after S2.
- **Unresolved blocker:** All production-release items in the question register.

## Backlog Definition of Ready

A story is ready only when its owner is named, referenced contracts exist, dependencies are accepted, assumptions are labeled, test fixtures are available, and any required method/data/security decision is approved.

## Backlog Definition of Done

A story is done only when acceptance criteria and required tests pass, trace/evidence is stored, documentation/runbook changes are complete, rollback is demonstrated where applicable, and no critical gate is partial or waived without the named approver and recorded rationale.
