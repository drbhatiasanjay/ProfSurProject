# Two-Pilot Comparison

## Side-by-side view

| Dimension | Pilot 1: Clean KAIF application | Pilot 2: Independent red-team audit |
|---|---|---|
| Objective | Produce the design KAIF gives a normal ProfSur team for a bounded natural-language statistical workflow. | Test how well the available KAIF materials cover real brownfield functional, technical, statistical, governance, and delivery needs. |
| Method | Sequential business discovery, executive HLD, handoff, TDD, evaluation specification, and implementation handoff. | Repository inventory, source and workflow mapping, bounded probes, harness application, module assessment, traceability, adversarial review, and action planning. |
| Inputs | Tracked ProfSur evidence at the recorded source baseline, KAIF instructions, and the user-defined OLS/FE scope. | ProfSur source evidence, KAIF source inventory, synthetic fixtures, isolated tests, bounded probes, and 40 audit scenarios. |
| Historical independence | Did not inspect or use the audit output. | Conducted independently and consolidated only after Pilot 1 was merged and frozen. |
| Outputs | 11 merged artifacts under `docs/kaif-clean-application-run/`. | Local audit archive with identity, inventories, flows, findings, tests, scenarios, HLD/TDD, module assessment, applicability, traceability, actions, adjudication, and rubric. |
| Main strength | Coherent, proportionate, approval-ready design for a small brownfield slice. | Broad coverage and direct challenge of whether design instructions amount to executable capability. |
| Main limitation | Design only; stakeholder approvals and runtime evidence remain absent. | Single-orchestrator audit, no authenticated end-to-end run, no control arm, and several KAIF modules unavailable as implementations. |
| Evidence produced | Requirements, decisions, contracts, explicit unknowns, evaluation gates, backlog, and provenance journal. | 229 capability records, 19 functional-flow records, 40 scenarios, seven isolated contract tests, 12 probes, 16 ProfSur actions, 10 KAIF gaps, and final verdicts. |
| Conclusions supported | KAIF can structure a useful low-agency design for this use case; S0 is ready to begin. | The design harnesses are useful as a design alpha; executable enforcement, comparative efficacy, and runtime claims remain unproved. |
| Conclusions not supported | Implemented feature behavior, production safety, adoption, ROI, or S1 readiness. | Production certification, full UI readiness, broad KAIF module maturity, causation of defect discovery, or business benefit. |

## Where the pilots agree

1. **Use the minimum justified agency.** Both favor an LLM-assisted deterministic workflow instead of an autonomous or multi-agent system.
2. **Preserve the requested statistical specification.** Method, dependent variable, predictors, effects, covariance, clustering, sample, and dataset identity must survive from request through execution.
3. **Separate proposal, approval, authorization, and execution.** Model output is an untrusted draft, not an executable command.
4. **Use the current deployment shape.** A bounded Streamlit and Cloud Run extension is more proportionate than a Kubernetes migration.
5. **Treat explanation as a controlled result consumer.** Deterministic validation must precede any narrative, and association must not become causation.
6. **Make evidence and uncertainty visible.** Both distinguish facts, unknowns, defaults, approvals, and runtime gaps.
7. **Do not start S1 yet.** Contracts, ownership, statistical policy, provider posture, and fixtures need S0 decisions first.

## Where they differ

### Design output versus framework assessment

Pilot 1 demonstrates that the KAIF design harness can organize a strong design when a capable orchestrator applies it carefully. Pilot 2 asks whether the repository itself enforces that quality. Its answer is no: important consistency checks, domain scenarios, and evidence validation were manually created.

### Statistical findings

Pilot 1 intentionally avoided defect hunting and used ProfSur only to understand the product and architecture. Pilot 2 intentionally probed source behavior and recorded specification-substitution and interpretation risks. These findings must not be read backward into the historical clean run.

### Strict harness conformance

Pilot 1 adapted routine checkpoints into pending approvals because the user authorized autonomous progress. Pilot 2 recorded that some harness routing and output requirements conflict with the bounded use case. The difference reflects purpose: one pilot produced a usable design; the other tested the method's fit and consistency.

### Runtime evidence

Pilot 2 has more execution evidence than Pilot 1, but it is still bounded. Seven isolated contract tests and 12 probes support specific observations. They do not establish authenticated application behavior, deployed service behavior, browser behavior, or the correctness of an unimplemented future workflow.

## Combined conclusion

Together, the pilots support a measured conclusion: KAIF demonstrated practical value as a structured design method for this brownfield slice. It did not demonstrate an executable seven-module platform, improved outcomes relative to ordinary review, production readiness, or a working ProfSur implementation. The combined evidence is sufficient to share with the KAIF team and to run ProfSur's S0 workshop, but not to start S1 development.
