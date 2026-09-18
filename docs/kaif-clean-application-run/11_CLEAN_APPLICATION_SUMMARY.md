# Clean Application Summary

## Application objective

Design a trustworthy ProfSur workflow in which a researcher or analyst describes an analysis in natural language, confirms an explicit statistical specification, executes only a supported and authorized analysis against the selected dataset, receives statistically validated output and responsible explanation, and can trace the original request through every decision to the final result.

The initial scope is deliberately bounded to OLS and company/year fixed-effects regression with company-clustered standard errors, variable and panel validation, clarification, execution/result validation, user-visible warnings/errors, and reproducible traceability.

## Selected architecture

The selected architecture is an **LLM-assisted deterministic workflow** inside the existing ProfSur application and deployment shape:

1. Preserve the original request and dataset snapshot.
2. Produce a schema-constrained draft specification using the current model adapter, or use a deterministic form fallback.
3. Normalize and validate all fields deterministically against an authoritative variable catalog and capability policy.
4. Ask targeted questions for missing, conflicting, or ambiguous critical fields.
5. Present the complete specification, sample impact, assumptions, warnings, and execution plan for explicit user approval.
6. Bind approval to a specification hash and authorize only an allowlisted execution contract.
7. Invoke the existing bounded OLS/FE capability through an adapter; never execute model-generated code.
8. Validate result structure, model identity, sample accounting, covariance/clustering, estimability, warnings, and numerical integrity.
9. Render deterministic results and warning summaries, with an optional bounded model explanation based only on validated fields.
10. Store an append-only trace from request through result and explanation.

The design retains the current Streamlit/container/Cloud Run approach. It adds no MCP dependency, long-term memory, RAG, GraphRAG, vector database, new model requirement, multi-agent system, Kubernetes platform, or full rewrite.

## Minimum justified agency

The minimum justified agency is **no autonomous agent**. A model assists with natural-language extraction and optional explanation, but it cannot approve, authorize, choose hidden defaults, execute arbitrary tools, or bypass deterministic controls. Deterministic code owns validation, policy, authorization, execution dispatch, result checking, trace creation, and fallback behavior.

This is simpler and safer than a single-agent or multi-agent design while still satisfying the natural-language use case. Deterministic-only input remains available as a fallback, but deterministic parsing alone is not the preferred primary experience because researcher requests can be linguistically varied and ambiguous.

## First implementation slice

The first vertical slice delivers one end-to-end, feature-flagged path:

- Natural-language or deterministic-form input.
- OLS or company/year fixed-effects method selection.
- One dependent variable and one or more predictors from plain dataset columns.
- Company and year fixed effects for the FE path.
- Company-clustered standard errors for the FE path.
- Deterministic variable, panel, cluster, sample, missingness, and estimability checks.
- Targeted specification clarification.
- Complete specification preview and explicit approval.
- Authorization-bound execution through the bounded existing executor.
- Result-contract and numerical sanity validation.
- Responsible association-focused summary, visible warnings/errors, and downloadable trace.

Before that vertical slice begins, S0 must approve and version the specification, approval, execution, result, error, warning, trace, variable-catalog, capability-policy, and statistical-policy contracts.

## Principal risks

- Incorrect extraction of method or variable roles could execute a materially different analysis.
- Dataset metadata may not be authoritative enough to validate variable meaning, panel identity, or eligible cluster fields.
- Missing-data loss, sparse panels, collinearity, or singleton effects may produce misleading or non-estimable results.
- A model-generated explanation may overstate causality or statistical evidence.
- Prompt injection or forged client state could attempt to cross the execution boundary.
- Trace data and provider payloads may expose sensitive prompts or dataset metadata without an approved privacy/retention policy.
- Unknown production volume, SLOs, concurrency behavior, and cost budgets prevent production-capacity claims.
- Existing implementation paths may produce different numerical behavior unless reference fixtures and parity tolerances are approved.

Controls are explicit approval, immutable specification hashes, allowlisted execution, least privilege, deterministic validation, result gating, bounded explanation, privacy-safe telemetry, reference parity, feature flags, and staged rollout.

## Unresolved decisions

The design can proceed, but implementation or production release requires named decisions recorded in `03_QUESTION_ASSUMPTION_REGISTER.md`, especially:

- Product, statistical-methods, security, privacy, model-risk, evaluation, accessibility, operations, and release ownership.
- Authoritative variable catalog and dataset identity/version semantics.
- Missing-data warning threshold, sample-adequacy rules, singleton behavior, cluster policy, and numerical tolerances.
- Model-provider approval, data region/retention terms, and cost budget.
- Trace retention, deletion, export, and access policy.
- Production SLOs, expected load/concurrency, recovery objectives, and pilot cohort.
- Accessibility conformance target and human-review sampling plan.

These are `UNKNOWN`, not inferred facts. The register provides separate planning defaults, approvers, blocking levels, and decision deadlines.

## Evaluation gates

Release is blocked unless the scenario suite in `07_EVALUATION_AND_ACCEPTANCE_SPEC.yaml` demonstrates:

- 100% accuracy for explicit method cases and critical dependent-variable fields.
- At least 98% overall method and variable-role accuracy.
- At least 98% clarification recall with zero critical misses and at least 90% precision.
- 100% fidelity between the user-approved specification and executed snapshot.
- Zero silent unsupported-method substitutions, authorization bypasses, stale approvals, critical warning omissions, or unsupported causal claims.
- 100% critical parameter accuracy, trace completeness, and required warning presentation.
- Approved statistical parity against independent reference fixtures within named tolerances.
- No critical security failures and successful operational-failure recovery.
- Human statistical-methods review, security/privacy review, accessibility review, and controlled-pilot sign-off at the specified gates.

Every implementation slice has explicit acceptance criteria, required tests, rollback requirements, and an exit gate in `08_IMPLEMENTATION_BACKLOG.md`.

## Recommended next implementation action

Name the product, statistical-methods, security/privacy, evaluation, accessibility, and operations approvers, then run the **S0 contract and policy workshop**. Its concrete output is an approved, versioned specification/result/error/trace contract set plus authoritative variable catalog, capability matrix, statistical policy, numerical tolerances, and golden fixtures. Only after the S0 gate passes should the team implement the feature-flagged S1 vertical slice.

No product code change is part of this clean KAIF application run.
