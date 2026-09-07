# Adversarial Review — ProfSur Analytical Studio Modernization → FDI

**Review ID:** PROF-FDI-ADR-001  
**Reviewed document:** `docs/PRD_ANALYTICAL_STUDIO_MODERNIZATION_TO_FDI.md` v1.0  
**Review mode:** Architecture / methodology / implementation-readiness red team  
**Implementation code modified:** No  
**Verdict:** `APPROVE_WITH_CHANGES`

## 1. Executive assessment

The PRD has the correct strategic direction: repair ProfSur bottom-up, prevent a home-grown Stata clone, move analytical execution behind typed capabilities/adapters, validate open-source engines independently, preserve deterministic analytical authority, require TDD/UI verification, and evolve toward the canonical FDI architecture rather than rewrite the application.

The plan is strong enough to start bounded Wave 0 work after the high-priority planning corrections below are incorporated. The immediate `python-docx` / `xtset` / alias / `lgraph` remediation is not blocked by the findings.

The principal risk is not Wave 0. It is that Waves 2–7 currently introduce advanced analytical execution, multi-step planning, visualization, scenarios, and narrative generation before several cross-cutting FDI contracts are made explicit. If left unchanged, that sequencing could recreate technical debt that the migration is intended to remove.

## 2. BLOCKER findings

**No Wave-0 blocker identified.**

No finding requires delaying the immediate reliability PR once the PRD is amended. However, the HIGH items below should be fixed in the PRD before Waves 2–5 are allowed to proceed.

## 3. HIGH findings

### H-01 — `AnalysisRun` is named as a stable concept but is introduced operationally too late

**Risk:** Advanced engine selection, GMM, ML, scenarios, charts, and later narratives can acquire inconsistent provenance/result envelopes before FDI migration.

**Required delta:** Introduce a **minimal immutable `AnalysisRunEnvelope` in Wave 2**, not Wave 8. It should bind at minimum:
- run/request/correlation IDs;
- dataset snapshot/fingerprint;
- normalized request;
- capability + method;
- engine + version/environment fingerprint;
- sample/exclusions;
- warnings/diagnostics;
- normalized result fingerprint;
- status/timestamps.

Wave 8 may expand this into the full multi-tenant FDI contract.

### H-02 — Method validity is conflated with capability availability

**Risk:** `CapabilityRegistry` answers “can we execute this?” but not “when is this method appropriate?” This is dangerous for FE/RE, IV, GMM, DID, prediction, and scenarios.

**Required delta:** Add a **minimal `MethodRegistry` / Method Card contract in Wave 2–3** with:
- estimand/question class;
- prerequisites;
- assumptions;
- mandatory diagnostics;
- prohibited interpretations;
- validation requirements;
- permitted analytical tier.

Engine selection must occur only after method validity is resolved.

### H-03 — Dataset snapshot/version semantics are insufficiently early

**Risk:** Engine comparisons and later model executions may be numerically reproducible only by accident. A dataframe hash alone is insufficient if transformations, filters, vintages, or variable definitions drift.

**Required delta:** Before Wave 3, define a lightweight **`DatasetSnapshotRef` + transformation lineage** containing source/vintage, schema version, filters, transformations, row identity/sample fingerprint, and immutable content fingerprint.

Golden engine comparisons must run against the same frozen snapshot contract.

### H-04 — Heavy execution arrives before async/cancellation/resource contracts

**Risk:** Wave 5 introduces GMM, ML, forecasting and other expensive jobs while durable async execution, cancellation, deadlines, retry policy, and resource limits are deferred to FDI migration.

**Required delta:** Add a **Job Execution Contract before or as part of Wave 5**:
- interactive vs background threshold;
- queued/running/cancelling/cancelled/completed/failed states;
- hard timeout and CPU/memory limits;
- cancellation semantics;
- bounded retry only for transient infrastructure errors;
- idempotency key;
- no retry for numerical/specification errors;
- cleanup/no orphan workers.

This aligns ProfSur evolution with FDI’s long-running execution requirements.

### H-05 — No explicit feature-flag / shadow-run / rollback migration strategy

**Risk:** Adapter migration can replace known ProfSur behavior with a numerically different engine in one cutover, making regression diagnosis difficult.

**Required delta:** Add a **migration-control pattern from Wave 2 onward**:
1. legacy path remains available;
2. new adapter can run in shadow mode;
3. compare normalized outputs on approved fixtures/selected non-sensitive runs;
4. expose discrepancy report;
5. cut over by capability feature flag only after acceptance;
6. retain rollback until post-cutover stability gate passes.

### H-06 — Variable/measure semantics are missing between syntax/NL and computation

**Risk:** Aliases such as `prof`, `companycode`, leverage variants, lifecycle measures, and future natural-language terms can resolve inconsistently across Stata, UI, scenario, and Copilot paths.

**Required delta:** Add a **Variable/Measure Resolver contract in Wave 2**, with canonical IDs, aliases, unit/scale, type, allowed transformations, missingness rules, and dataset binding. Natural language and expert syntax must resolve through the same semantic layer.

### H-07 — Visualization contract is introduced after earlier waves already need semantic visuals

**Risk:** Wave 0 `lgraph`, Wave 4 diagnostics, and Wave 5 scenario/GMM/ML visuals may hard-code renderer-specific shapes before `VisualizationArtifact` exists.

**Required delta:** Introduce a **minimal `VisualizationSpec` in Wave 2** (data binding, chart intent, encodings, annotations, provenance). Wave 7 can expand it into rich `VisualizationArtifact` / `StoryArtifact` contracts. Do not require a renderer migration in Wave 0.

### H-08 — Narrative generation precedes full claim-governance sequencing

**Risk:** Wave 7 describes claim filtering while the full Claim Ledger is deferred to Wave 8, creating a gap where commentary may overstate C1/C2/C3 results.

**Required delta:** Introduce a **minimal Claim Permission / Epistemic Contract before narrative generation**. Each fact/insight entering the narrative planner must carry claim type, analytical tier, source `AnalysisRun`/Evidence reference, and permitted language. Wave 8 may migrate this to the canonical Claim Ledger.

### H-09 — Multi-step analytical plans lack explicit plan state machine and partial-failure semantics

**Risk:** Wave 6 compound research plans can become ambiguous when one branch fails, is cancelled, needs approval, or produces only partial evidence.

**Required delta:** Define an **AnalyticalPlan lifecycle in Wave 6** such as `DRAFT → READY → AWAITING_APPROVAL → EXECUTING → COMPLETED | PARTIAL | FAILED | ABSTAINED | CANCELLED`, with per-step dependency, retry/skip policy, and explicit partial-result rendering.

### H-10 — Security/isolation boundaries are deferred too far for third-party engines

**Risk:** Open-source engines and future model/tool integrations can accidentally gain unsafe filesystem/network/data access before FDI multi-tenancy exists.

**Required delta:** Add **engine isolation requirements to Wave 3** even for single-user ProfSur:
- allowlisted engine adapter calls;
- no arbitrary shell/Python execution through analytical commands;
- bounded filesystem access;
- network egress disabled unless explicitly required;
- dependency/security/license scan;
- sanitized exports (including spreadsheet formula injection);
- no secrets in logs/errors.

## 4. MEDIUM findings

### M-01 — Error taxonomy needs execution-lifecycle states
Add `TIMEOUT`, `CANCELLED`, `RESOURCE_LIMIT`, `RETRY_EXHAUSTED`, `STALE_DATASET`, `PARTIAL_FAILURE`, and `RESULT_SUPERSEDED` before async/multi-step work.

### M-02 — Contract/schema versioning is not explicit
Every durable contract (`AnalyticalRequest`, `CapabilityResult`, `VisualizationSpec`, `AnalysisRunEnvelope`) should include schema version and backward-compatibility/migration rules.

### M-03 — Reproducibility must include environment numerics
For econometric golden tests record package versions and numerical runtime where relevant (Python, BLAS/LAPACK/backend, OS/container fingerprint, random seed). Statistical equality may depend on these details.

### M-04 — Cache policy is absent
Define cache keys from dataset snapshot + normalized plan + engine/version + method parameters. Cache must never be analytical authority and must invalidate on any semantic input/version change.

### M-05 — Scenario contract is too thin for future decision use
Add assumption IDs, units, validity domain, model/version, branch parent, uncertainty method, baseline `AnalysisRun`, and explicit distinction between sensitivity, forecast, and counterfactual scenario.

### M-06 — ML reproducibility needs stronger artifact metadata
Record feature schema, split policy, leakage checks, seed, preprocessing, hyperparameters, training snapshot, evaluation snapshot, model fingerprint, calibration metrics, and deployment estimand.

### M-07 — Provider/LLM cost governance should be explicit before Copilot expansion
Wave 6 should add request budget, provider/model/effort metadata, routing reason, fallback/escalation reason, latency, and usage/cost telemetry. Provider capability must remain independent of analytical permission.

### M-08 — Superseded artifact behavior is undefined
When a new `AnalysisRun` replaces a prior run, charts/narratives/reports should remain immutable artifacts linked to the old run and be marked superseded rather than silently refreshed.

### M-09 — Release/CI gates should be machine-checkable
Where feasible, convert Definition-of-Done items into CI checks rather than relying only on implementation-report prose.

## 5. LOW findings

- Add explicit accessibility checks for keyboard operation of future scenario/touch interactions.
- Add a deprecation policy for capability aliases/command syntax.
- Add an engine compatibility matrix keyed by engine version so library upgrades trigger recertification.
- Add a user-visible provenance drawer pattern early, even if initially minimal.

## 6. Sequencing corrections recommended

The revised programme should preserve the existing waves but insert the following cross-cutting contracts:

```text
Wave 0  reliability repair
Wave 1  semantic correctness
Wave 2  + MethodRegistry
        + Variable/Measure Resolver
        + DatasetSnapshotRef
        + AnalysisRunEnvelope
        + minimal VisualizationSpec
        + feature flags/shadow mode
Wave 3  engine spike
        + engine isolation/security
        + environment reproducibility
Wave 4  command expansion through validated capabilities
Wave 5  advanced econometrics/scenario/ML
        + async Job Execution Contract
Wave 6  bidirectional language/Copilot
        + AnalyticalPlan state machine
        + human approval/partial-failure semantics
        + model-routing cost telemetry
Wave 7  rich visualization/narrative
        + minimal claim-permission contract
Wave 8  migrate these contracts into full canonical FDI multi-tenant
```

## 7. Specific review of immediate PR-1

Wave 0 / PR-1 remains appropriately bounded. The following should be enforced during implementation:

- `PanelContext` is session-scoped and must not become another module global.
- `xtset` success must require real validation, not cosmetic state.
- `companycode` alias normalization must be disclosed and tested.
- `lgraph` must reuse the existing plotting path and remain explicitly community compatibility.
- optional DOCX failure must not crash the Studio.
- raw traceback must not be normal user UX.
- error IDs/correlation IDs must be present on changed execution paths.
- targeted UI verification must cover command history, panel metadata, chart rendering, and failure state.
- no expansion to new estimators or unrelated commands.

## 8. Acceptance recommendation

**Verdict: `APPROVE_WITH_CHANGES`**

The architecture direction is sound. Incorporate H-01 through H-10 into PRD v1.1 before permitting the programme to move beyond the initial reliability/semantic-remediation work. Wave 0 can proceed after the PRD update without waiting for the full future SaaS design to be implemented.
