# Decision and Evidence Register

## Register conventions

- **Evidence** identifies a tracked ProfSur artifact at the frozen source baseline, a KAIF instruction, or a primary external source.
- **Assumption - planning default** is not a product fact. It remains subject to approval by the named owner.
- Decisions marked **proposed** are design recommendations, not production approvals.

## D-01 — Solution agency

- **Decision:** Use an LLM-assisted deterministic workflow, not an autonomous agent.
- **Business reason:** Natural-language interpretation benefits from a model, while statistical execution, authorization, and safety require reproducible deterministic controls.
- **Alternatives considered:** deterministic code only; workflow automation; LLM-assisted workflow; single autonomous agent; multi-agent system.
- **Selected option:** LLM-assisted workflow with schema-constrained drafting, deterministic validation and authorization, explicit human approval, and bounded execution.
- **Evidence:** `models/llm_adapters.py`, `models/agent_tools.py`, `models/stata_engine.py`; KAIF agency-ladder and parsimony guidance.
- **Assumption - planning default:** A deterministic form remains available when the model is unavailable or the user prefers direct specification.
- **Owner:** Product owner with statistical-methods and security approvers.
- **Revisit trigger:** Measured tasks cannot be completed at target accuracy without materially greater agency.

## D-02 — Execution boundary

- **Decision:** Treat model output as an untrusted draft; only a deterministic authorization service may invoke the bounded statistical executor.
- **Business reason:** Prevents prompt content or parsing errors from becoming executable commands.
- **Alternatives considered:** direct model-to-tool execution; raw Stata/Python generation; reviewed structured execution.
- **Selected option:** Approved structured specification plus server-side authorization token, allowlisted executor, and immutable execution snapshot.
- **Evidence:** Existing bounded entry points in `models/agent_tools.py` and `models/stata_engine.py`; [OWASP prompt-injection guidance](https://owasp.org/www-community/attacks/PromptInjection).
- **Assumption - planning default:** No arbitrary Python, SQL, shell, or raw Stata text is accepted from the model.
- **Owner:** Security owner and technical lead.
- **Revisit trigger:** A separately governed advanced-code feature is approved with an isolated sandbox and new threat model.

## D-03 — Initial statistical scope

- **Decision:** Limit the first delivery slice to OLS and company/year fixed-effects regression with company-clustered standard errors.
- **Business reason:** This is the requested bounded use case and permits precise validation and evaluation before expansion.
- **Alternatives considered:** all currently recognized methods; OLS only; the selected bounded pair.
- **Selected option:** OLS plus two-way company/year FE; unsupported methods receive a clear refusal and supported alternatives, never silent substitution.
- **Evidence:** User-authorized scope; existing OLS/FE capabilities in `models/econometric.py` and `models/stata_engine.py`.
- **Assumption - planning default:** Company clustering is the only cluster mode enabled in slice 1.
- **Owner:** Statistical-methods owner and product owner.
- **Revisit trigger:** Slice-1 gates pass and a prioritized method-expansion case is approved.

## D-04 — Specification preservation and approval

- **Decision:** Preserve the original request, parser draft, clarifications, approved specification, execution snapshot, result, warnings, and explanation in one trace.
- **Business reason:** Users need to see exactly what was requested, changed, approved, and executed.
- **Alternatives considered:** chat transcript only; current-state record; append-only trace bundle.
- **Selected option:** Append-only, versioned trace with explicit approval tied to a specification hash.
- **Evidence:** Existing validation-ledger pattern in `models/validation_ledger.py`; user traceability requirement.
- **Assumption - planning default:** Approval expires after any specification or dataset change.
- **Owner:** Product owner, compliance/privacy owner, and technical lead.
- **Revisit trigger:** Retention, export, or regulated-record requirements are decided.

## D-05 — Parser and contracts

- **Decision:** Use a versioned schema-constrained parser contract with deterministic normalization and validation.
- **Business reason:** Free-form output cannot provide reliable parameter fidelity or stable evaluation.
- **Alternatives considered:** regex-only parser; unconstrained LLM text; structured model output; deterministic form only.
- **Selected option:** Structured model draft plus deterministic form fallback; both produce the same statistical-specification contract.
- **Evidence:** Existing aliases/parsing in `models/stata_engine.py`; [Gemini structured-output documentation](https://ai.google.dev/gemini-api/docs/structured-output).
- **Assumption - planning default:** Parser confidence is advisory and never authorizes execution.
- **Owner:** Technical lead and evaluation owner.
- **Revisit trigger:** Schema version changes or measured extraction accuracy misses the gate.

## D-06 — Model use

- **Decision:** Pilot with the currently integrated `gemini-2.5-flash` behind an adapter; do not make model identity part of the domain contract.
- **Business reason:** Reuses the current integration while allowing replacement and deterministic fallback.
- **Alternatives considered:** no model; new model procurement; current adapter; multiple-model routing.
- **Selected option:** Current model for draft extraction and optional bounded explanation only.
- **Evidence:** `models/llm_adapters.py`; [Gemini 2.5 Flash model documentation](https://ai.google.dev/gemini-api/docs/models#gemini-2.5-flash).
- **Assumption - planning default:** Production model approval, region, retention, and data-processing terms remain unresolved.
- **Owner:** AI/model-risk owner, privacy owner, and procurement owner.
- **Revisit trigger:** Provider policy, quality, latency, cost, or data-residency requirements change.

## D-07 — Memory and retrieval

- **Decision:** Add no long-term conversational memory, RAG, GraphRAG, or vector database in the initial scope.
- **Business reason:** The workflow depends on the current request, approved dataset metadata, and execution trace; retrieval infrastructure is not needed to satisfy it.
- **Alternatives considered:** session state; durable trace; vector memory; GraphRAG.
- **Selected option:** Request-scoped state plus durable trace records under an approved retention policy.
- **Evidence:** Current Streamlit session-oriented journeys in `pages/19_ai_assistant.py` and `pages/23_stata_studio.py`; KAIF Knowledge-is-not-Memory guidance.
- **Assumption - planning default:** Dataset dictionaries are authoritative application data, not model memory.
- **Owner:** Product owner and privacy owner.
- **Revisit trigger:** A separately approved cross-study knowledge-retrieval use case emerges.

## D-08 — User experience and clarification

- **Decision:** Show a structured specification preview, targeted clarification prompts, and explicit approve/edit/cancel controls before execution.
- **Business reason:** Researchers must retain control over method, variables, fixed effects, clustering, and sample behavior.
- **Alternatives considered:** one-click chat execution; generic follow-up question; field-level clarification.
- **Selected option:** Field-level clarification with reason, accepted values, and retained prior answers.
- **Evidence:** Existing Streamlit entry points in `app.py`, `pages/19_ai_assistant.py`, and `pages/23_stata_studio.py`; user requirements.
- **Assumption - planning default:** Missing critical fields block approval; noncritical defaults are visible and editable.
- **Owner:** Product/design owner and accessibility owner.
- **Revisit trigger:** Usability testing shows excessive clarification or comprehension failure.

## D-09 — Missing data and sample disclosure

- **Decision:** Apply complete-case analysis for required model columns in slice 1 and disclose row loss before approval and after execution.
- **Business reason:** Silent sample changes can materially alter interpretation.
- **Alternatives considered:** implicit library behavior; automatic imputation; complete-case disclosure.
- **Selected option:** Deterministic complete-case filtering with counts, percentages, and per-variable missingness; no automatic imputation.
- **Evidence:** Current execution handling in `models/stata_engine.py`; statistical safety requirements.
- **Assumption - planning default:** A material-loss warning threshold is set during S0 and approved by the statistical-methods owner.
- **Owner:** Statistical-methods owner.
- **Revisit trigger:** Approved missing-data methods or study-specific policies are introduced.

## D-10 — Collinearity and sample adequacy

- **Decision:** Block non-estimable specifications; otherwise surface dropped terms, rank problems, singleton effects, and sample-size warnings without inventing coefficients.
- **Business reason:** Successful library return does not alone establish a valid or interpretable result.
- **Alternatives considered:** library defaults only; blanket failure; deterministic post-fit validation.
- **Selected option:** Preflight checks plus post-fit result validator with severity-classified findings.
- **Evidence:** Existing collinearity/missing handling in `models/stata_engine.py`; [PanelOLS documentation](https://bashtage.github.io/linearmodels/panel/panel/linearmodels.panel.model.PanelOLS.html).
- **Assumption - planning default:** Numeric thresholds and fixture tolerances require statistical-methods approval.
- **Owner:** Statistical-methods owner and evaluation owner.
- **Revisit trigger:** Reference parity or user research indicates different thresholds.

## D-11 — Explanation policy

- **Decision:** Generate a deterministic factual summary first; permit an optional bounded model explanation only from validated result fields and warnings.
- **Business reason:** Explanation must not overstate causality, significance, or unsupported findings.
- **Alternatives considered:** raw table only; unconstrained model narrative; deterministic template; bounded hybrid.
- **Selected option:** Hybrid with mandatory association-not-causation language unless a separately approved causal design exists.
- **Evidence:** Existing optional explanation in `models/llm_adapters.py`; [ASA statement on p-values](https://www.amstat.org/asa/files/pdfs/p-valuestatement.pdf).
- **Assumption - planning default:** Failed critical result validation suppresses substantive explanation.
- **Owner:** Statistical-methods owner and responsible-AI owner.
- **Revisit trigger:** Causal inference methods or publication-grade reporting are added.

## D-12 — Deployment

- **Decision:** Retain the current containerized Streamlit deployment on Cloud Run for the initial slice.
- **Business reason:** The use case does not justify a platform migration and the repository already contains this path.
- **Alternatives considered:** current Cloud Run container; conventional VM/application host; other managed services; standalone containers; Kubernetes.
- **Selected option:** Current Cloud Run approach, with measured concurrency/timeout/resource tuning.
- **Evidence:** `Dockerfile`, `cloudbuild.yaml`, `deploy.ps1`; [Cloud Run autoscaling documentation](https://cloud.google.com/run/docs/about-instance-autoscaling) and [concurrency documentation](https://cloud.google.com/run/docs/about-concurrency).
- **Assumption - planning default:** Existing deployment remains supported pending operational-owner confirmation and load testing.
- **Owner:** Platform/operations owner.
- **Revisit trigger:** Measured scale, isolation, networking, availability, or organizational platform requirements exceed Cloud Run capabilities.

## D-13 — Kubernetes

- **Decision:** Do not adopt Kubernetes for this use case.
- **Business reason:** No evidenced scheduling, tenancy, portability, or operational constraint requires cluster orchestration.
- **Alternatives considered:** managed application deployment; managed services; containers; Kubernetes.
- **Selected option:** Managed container deployment on the current platform.
- **Evidence:** Current deployment artifacts and bounded synchronous workflow.
- **Assumption - planning default:** Production volume and SLOs remain `UNKNOWN` until measured.
- **Owner:** Platform/operations owner and architecture approver.
- **Revisit trigger:** Approved requirements demonstrate a capability gap that cannot be met economically by the current managed platform.

## D-14 — Observability and evaluation

- **Decision:** Gate release on scenario-based evaluation and emit privacy-safe structured telemetry correlated by trace ID.
- **Business reason:** Accuracy, safety, and operational behavior must be demonstrated continuously, not inferred from a successful response.
- **Alternatives considered:** ad hoc manual testing; unit tests only; golden scenarios plus telemetry and human review.
- **Selected option:** Automated contract/parity/security suites, statistical human review, controlled pilot, and production monitors.
- **Evidence:** `07_EVALUATION_AND_ACCEPTANCE_SPEC.yaml`; [NIST AI RMF Generative AI Profile](https://www.nist.gov/publications/artificial-intelligence-risk-management-framework-generative-artificial-intelligence) and [OpenTelemetry semantic conventions](https://opentelemetry.io/docs/specs/semconv/).
- **Assumption - planning default:** Raw prompts, datasets, coefficients, and provider payloads are excluded from default logs.
- **Owner:** Evaluation owner, operations owner, privacy owner.
- **Revisit trigger:** Incident, drift, schema/model change, or threshold miss.

## D-15 — Rollout and rollback

- **Decision:** Deliver behind feature flags through S0 contracts, S1 vertical slice, S2 hardening, and S3 controlled pilot; rollback disables parser/explanation first and the entire workflow if necessary.
- **Business reason:** Limits exposure while preserving deterministic fallback and trace evidence.
- **Alternatives considered:** big-bang release; code rollback only; staged flags and compatible schemas.
- **Selected option:** Staged rollout with backward-compatible trace schema and tested kill switches.
- **Evidence:** `08_IMPLEMENTATION_BACKLOG.md` and technical design rollout section.
- **Assumption - planning default:** Existing Stata Studio and AI Assistant journeys remain available during pilot unless explicitly retired later.
- **Owner:** Product owner and release/operations owner.
- **Revisit trigger:** Pilot evidence supports broader release or reveals a critical risk.
