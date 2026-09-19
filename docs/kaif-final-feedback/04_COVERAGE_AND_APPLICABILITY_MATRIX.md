# Coverage and Applicability Matrix

## Classification rules

| Classification | Meaning |
|---|---|
| Covered and evidenced | The pilots contain direct, traceable evidence sufficient for the design-level conclusion. |
| Covered in design only | The design addresses the topic, but no implementation or runtime proof exists. |
| Partly covered | Material coverage exists, but decisions, enforcement, or evidence remain incomplete. |
| Applicable but missing | The topic matters to ProfSur or KAIF, but the available evidence does not cover it adequately. |
| Requires runtime validation | Design exists or the requirement is known, but only implementation/runtime evidence can close it. |
| Not testable in this pilot | The topic was in scope conceptually but the available environment or authorization could not test it. |
| Not applicable to ProfSur | The topic is not needed for this bounded use case; the reason is stated explicitly. |
| Not implemented in KAIF | The capability is described but no implementation exists in the authorized KAIF repository. |

## Matrix

| ID | Aspect | Classification | Evidence | Reason or remaining limitation |
|---|---|---|---|---|
| M-01 | Business problem definition | Covered and evidenced | Pilot 1 discovery, business case and current/desired workflow; Pilot 2 `04_USE_CASE_AND_VALUE_HYPOTHESIS.md`. | The bounded problem is explicit and linked to user consequences. |
| M-02 | Stakeholder identification | Covered in design only | Pilot 1 actor and ownership sections; question and approval register. | Roles are defined, but accountable people have not been assigned. |
| M-03 | Measurable value | Partly covered | Pilot 1 KPI framework; Pilot 2 KF08 and value hypothesis. | Measures are defined, but baselines, adoption, timing, review effort, and ROI are unmeasured. |
| M-04 | Current-state discovery | Covered and evidenced | Pilot 1 product evidence and current process; Pilot 2 19-item functional-flow map. | Static repository evidence supports the design context. |
| M-05 | Functional requirements | Covered and evidenced | Pilot 1 FR-001 through FR-010 and user journeys; Pilot 2 FR01 through FR40. | Requirements are broad and traceable at design level. |
| M-06 | Non-functional requirements | Covered in design only | Pilot 1 NFRs, HLD reliability, observability, accessibility, and security sections. | SLO values, capacity, accessibility target, retention, and support model await approval/evidence. |
| M-07 | Executive HLD | Covered and evidenced | Pilot 1 `04_KAIF_EXECUTIVE_HLD.md`; Pilot 2 `07_KAIF_EXECUTIVE_HLD.md`. | Two independent designs exist with stated evidence boundaries. |
| M-08 | Technical TDD | Covered and evidenced | Pilot 1 `06_KAIF_TECHNICAL_TDD.md`; Pilot 2 `08_KAIF_TECHNICAL_TDD.md`. | The TDD is implementation-oriented but not an implementation result. |
| M-09 | Data architecture | Covered in design only | Specification, result, trace, variable-catalog, dataset-fingerprint, and state contracts. | Authoritative catalog, retention, schema migration, and store choice remain open. |
| M-10 | Integration architecture | Covered in design only | Existing Streamlit, bounded Python interfaces, model adapter, execution boundary, and Cloud Run context. | No integrated vertical slice has been built or exercised. |
| M-11 | Security | Covered in design only | Threats, least privilege, allowlists, prompt injection, tamper, timeout, and fail-closed controls. | Controls are requirements, not verified enforcement. |
| M-12 | Privacy | Partly covered | Data minimization defaults, redaction requirements, provider boundary, and Q-14/Q-15. | Classification, region, retention, deletion, and provider terms remain open. |
| M-13 | Authorization | Covered in design only | Approval hash, server-side authorization token, role matrix, stale approval rejection. | Role policy and deny-path implementation are absent. |
| M-14 | Statistical correctness | Partly covered | Pilot 1 statistical contracts and 100 percent critical gates; Pilot 2 40 scenarios and bounded probes. | Numerical fixtures, approved tolerances, full estimator parity, and implemented controls are missing. |
| M-15 | Model governance | Covered in design only | Named current model, provider-neutral adapter, prompt/version hashes, fallback, model-risk owner. | Provider approval, benchmark, budget, and change-control operation remain open. |
| M-16 | Prompt-injection protection | Covered in design only | Untrusted-model boundary, structured draft, no raw code/tool execution, adversarial scenarios. | No implemented attack suite or runtime deny evidence exists. |
| M-17 | Human approval | Covered in design only | Specification preview, material warnings, explicit approval, hash binding, invalidation on change. | Approval UX and role behavior are unimplemented. |
| M-18 | Observability | Covered in design only | Trace IDs, stage spans, quality counters, latency, cost, fallback, and failure metrics. | No telemetry or dashboards exist for the proposed flow. |
| M-19 | Auditability | Covered in design only | Append-only trace contract, request/spec/approval/execution/result/explanation lineage. | Retention, access, persistence failure behavior, and export policy remain undecided. |
| M-20 | Cost | Partly covered | Cost categories and token metering are identified; no financial benefit is invented. | Current provider pricing retrieval failed in Pilot 2 and no approved budget exists. |
| M-21 | Performance | Requires runtime validation | Latency stages, p95 planning default, load and concurrency gates are specified. | No representative load or end-to-end latency evidence exists. |
| M-22 | Reliability | Requires runtime validation | Timeout, retry, idempotency, fallback, result-validation, and rollback requirements exist. | Failure drills and integrated recovery have not run. |
| M-23 | Accessibility | Requires runtime validation | Keyboard, focus, non-color status, accessible names, tables, and WCAG planning target are specified. | No assistive-technology or authenticated UI acceptance was run. |
| M-24 | Deployment | Partly covered | Current Docker, Cloud Run, workflow, rollout, and alternatives are documented. | Proposed feature deployment, ingress review, capacity, and production SLO evidence are absent. |
| M-25 | Rollback | Covered in design only | Feature flag, deterministic fallback, prior revision, compatible contracts, and evidence preservation. | No rollback drill for the proposed feature exists. |
| M-26 | Evaluation | Partly covered | Pilot 1 has 41 scenarios, 12 metrics, and S0-S3 gates; Pilot 2 has 40 scenarios and bounded probes. | The proposed product evaluation suite is not implemented, and the KAIF validator is absent. |
| M-27 | Traceability | Covered and evidenced | Pilot 1 handoff and 21/21 coverage validation; Pilot 2 `11_END_TO_END_TRACEABILITY.md`. | Runtime trace completeness cannot be assessed before implementation. |
| M-28 | Implementation backlog | Covered and evidenced | Pilot 1 S0-S3 backlog with acceptance criteria, tests, rollback, owners, priorities, and blockers. | Work is ready for decision preparation, not S1 execution. |
| M-29 | Decision governance | Covered in design only | Question register, approvers, explicit stage gates, assumptions, and decision/evidence register. | Named accountable approvers have not accepted decisions. |
| M-30 | Runtime validation | Requires runtime validation | Both pilots explicitly distinguish design from runtime; Pilot 2 isolated tests are bounded. | No authenticated end-to-end implementation of the proposed flow exists. |
| M-31 | User acceptance | Requires runtime validation | User journeys and acceptance scenarios are defined. | No researcher cohort, four-profile journey, or usability evidence exists for the proposed flow. |
| M-32 | Production readiness | Applicable but missing | Production gates and unresolved questions are explicit. | Implementation, approvals, runtime evidence, operations, and release sign-off are absent. |
| M-33 | kaif-design implementation | Covered and evidenced | Both design harnesses, skills, templates, outputs, and observations were applied. | Evidence supports USEFUL_DESIGN_ALPHA, not production certification. |
| M-34 | kaif-platform implementation | Not implemented in KAIF | Pilot 2 module assessment, module 2. | Only a concept description existed in the authorized repository. |
| M-35 | kaif-deploy implementation | Not implemented in KAIF | Pilot 2 module assessment, module 3. | Only a concept description existed in the authorized repository. |
| M-36 | kaif-eval implementation | Not implemented in KAIF | Pilot 2 module assessment, module 4; auditor-authored validators. | No callable evaluation spine existed in the authorized repository. |
| M-37 | kaif-guard implementation | Not implemented in KAIF | Pilot 2 module assessment, module 5. | No callable guard enforcement existed in the authorized repository. |
| M-38 | kaif-value implementation | Not implemented in KAIF | Pilot 2 module assessment, module 6. | No callable value-measurement implementation existed in the authorized repository. |
| M-39 | kaif-identity implementation | Not implemented in KAIF | Pilot 2 module assessment, module 7. | No callable identity/isolation implementation existed in the authorized repository. |
| M-40 | Kubernetes-specific HPA, PDB, and namespace controls | Not applicable to ProfSur | Current slice remains one managed Streamlit container on Cloud Run with no measured cluster trigger. | Kubernetes can be revisited only if approved scale, isolation, or platform requirements exceed the current service. |
| M-41 | Multi-agent coordination | Not applicable to ProfSur | Both pilots selected an LLM-assisted deterministic workflow. | The bounded request does not require dynamic delegation among autonomous specialists. |
| M-42 | Long-term memory, RAG, GraphRAG, or vector database | Not applicable to ProfSur | The workflow requires current request state, dataset metadata, and an audit trace. | No cross-study semantic retrieval requirement was identified. |
| M-43 | Live provider pricing and cost benchmark | Not testable in this pilot | Pilot 2 records failed pricing retrieval; Pilot 1 labels budget as UNKNOWN. | No current price or ROI claim is made; recheck under approved procurement and network conditions. |

## Classification counts

| Classification | Count |
|---|---:|
| Covered and evidenced | 8 |
| Covered in design only | 13 |
| Partly covered | 6 |
| Applicable but missing | 1 |
| Requires runtime validation | 5 |
| Not testable in this pilot | 1 |
| Not applicable to ProfSur | 3 |
| Not implemented in KAIF | 6 |
