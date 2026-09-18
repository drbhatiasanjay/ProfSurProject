# Business and Process Discovery

## Discovery status

This discovery reconstructs known product facts from ProfSur files tracked at commit `fa97df7e1e6b43726c63590a47906d8ae8e5797d`. No live stakeholder interview occurred. Missing information is marked `UNKNOWN`; safe defaults are separately labeled `Assumption - planning default` and catalogued in `03_QUESTION_ASSUMPTION_REGISTER.md`.

## Business case

### Primary user

A researcher or analyst working with ProfSur's corporate panel data who wants to express an econometric question in ordinary language and obtain a reviewable, reproducible statistical result without manually translating every request into Stata syntax.

### Job to be done

When I describe a relationship I want to estimate, help me turn that intent into an explicit statistical specification, tell me what is missing or unsafe, let me approve the exact specification, run only a supported analysis against the active dataset, and explain the result without overstating what the analysis proves.

### Business problem

ProfSur currently exposes two relevant journeys:

1. A direct Stata-style command console executes commands such as `regress` and `xtreg` against the active panel and renders terminal output, charts, interpretation, and follow-up actions.
2. An AI Assistant accepts natural-language requests and can call database, econometric, chart, ontology, and Stata tools. Its live econometric tool accepts dependent/independent variables, model type, filters, and years, and returns model results and limitations.

The bounded business need is to make the transition from natural-language intent to execution an explicit, user-reviewable contract. The design must preserve the researcher's requested method and variables, clarify ambiguity, reject unsupported specifications, validate against the active dataset, and preserve evidence from request through explanation.

### User value

- Less manual translation between research intent and executable syntax.
- Fewer accidental runs with missing, unresolved, or silently substituted specification details.
- A clear approval point before computation.
- Consistent warnings for missingness, sample sufficiency, absorbed/collinear terms, unsupported methods, and interpretation limits.
- Reproducibility through immutable request, specification, dataset, execution, and result identifiers.

No financial benefit is claimed. A future business case should measure time from request to approved result, avoidable reruns, clarification burden, and reviewer acceptance before assigning monetary value.

## Product evidence and constraints

| Known fact | Evidence at frozen ProfSur commit | Design consequence |
|---|---|---|
| Canonical UI is Streamlit with registered pages for AI Assistant and Stata Studio | `app.py` navigation registry | Extend the existing application shell and session model; do not create a new product surface by default. |
| Active panel rows include `company_code`, `year`, `life_stage`, leverage, profitability, tangibility, tax, dividend, size, tax shield, macro and ownership fields | `db.py:get_panel_data` | Build variable discovery and validation from the active dataset schema, not a model-invented catalog. |
| Direct Stata execution supports `regress`, `xtreg`, `xtset`, and typed unsupported responses | `models/stata_engine.py` | Reuse the existing execution boundary behind a stricter specification adapter; do not let the LLM execute arbitrary code. |
| The engine resolves aliases and factor terms, handles missing rows, collinearity notes, panel declaration, and entity clustering | `models/stata_engine.py` | Preserve these capabilities but expose their consequences before approval and in result warnings. |
| Existing fixed-effects implementations use panel estimators and clustered covariance | `models/econometric.py`, `models/stata_engine.py` | Treat estimator and covariance choices as explicit contract fields and verify implementation capability per approved variant. |
| AI Assistant uses `gemini-2.5-flash` and exposes callable analysis tools | `models/llm_adapters.py`, `pages/19_ai_assistant.py` | Use the current model only for a typed draft/clarification and bounded explanation; deterministic code remains authoritative. |
| Chat sessions/messages and model metadata are persisted | `db.py`, `pages/19_ai_assistant.py` | Link analysis trace records to the existing authenticated session where appropriate. |
| A provider-neutral validation ledger already models numerical, assumption, methodological, reproducibility, and reviewer gates | `models/validation_ledger.py` | Reuse the vocabulary and fail-closed principle for execution/result validation. |
| Deployment is a single Streamlit container on Cloud Run | `Dockerfile`, `cloudbuild.yaml`, `.github/workflows/deploy.yml` | Prefer the current conventional managed-container deployment. Kubernetes is not justified for this slice. |

## Actors and systems

| Actor/system | Role | Decisions/actions |
|---|---|---|
| Researcher/analyst | Primary user | States intent, answers clarification questions, approves specification, reviews result and warnings. |
| Statistical reviewer/method owner | Human governance role | Approves statistical policies and production thresholds; reviews escalated or high-risk interpretations. |
| Product owner | Business owner | Approves workflow defaults, UX, scope, KPI targets, and release gates. |
| Data owner/steward | Dataset authority | Confirms canonical panel, variable definitions, sensitivity, and permitted uses. |
| ProfSur Streamlit application | Interaction shell | Captures request, displays specification, clarification, warnings, approval, progress, results, and trace. |
| Intent parser | LLM-assisted component | Produces a typed draft and explicit uncertainty; cannot authorize or execute. |
| Specification policy/validator | Deterministic component | Validates method, fields, variable roles, FE/cluster compatibility, dataset availability, and release policy. |
| Statistical executor | Existing bounded Python/Stata-style engine | Executes an approved immutable specification only. |
| Result validator | Deterministic component plus test/eval evidence | Checks execution status, sample/accounting invariants, result shape, finite values, and warning completeness. |
| Explanation composer | Templates plus bounded LLM | Explains validated results using only the result contract and policy; distinguishes association from causation. |
| Audit/trace store | Existing database plus new typed records | Links request, revisions, approval, dataset fingerprint, execution, result, explanation, and model/prompt versions. |
| Google Gemini API | Existing external model service | Draft parsing and optional explanation; availability, privacy, and procurement constraints remain open. |
| Cloud Run | Existing deployment target | Hosts the current container; managed autoscaling remains sufficient pending measured load. |

## Current process

1. User opens AI Assistant or Stata Studio within the authenticated Streamlit application.
2. In Stata Studio, the user enters or selects a command and execution begins immediately.
3. In AI Assistant, the user enters natural language; the current Gemini tool loop decides whether to query data or call an econometric/statistical tool.
4. The live econometric tool normalizes variable aliases, loads the panel, filters rows, checks required columns and minimum sample, runs candidate estimators, chooses or honors a model type, and returns coefficients/diagnostics/limitations.
5. The assistant renders an answer, charts, follow-ups, and model/timing metadata; chat history is persisted.

This is a product-flow description, not a defect assessment.

## Desired process

1. **Capture** — preserve the original request verbatim with user, session, active panel/filter context, and timestamp.
2. **Draft** — an LLM produces a schema-constrained `StatisticalSpecificationDraft`, including confidence and unresolved fields.
3. **Clarify** — deterministic rules classify missing/ambiguous fields and ask only questions necessary for a valid specification. No execution is possible in this state.
4. **Validate** — deterministic checks resolve variables against the active dataset, validate method/FE/cluster support, profile missingness and sample sufficiency, and produce blocking errors plus non-blocking warnings.
5. **Review** — show the exact method, outcome, predictors, controls, company/year FE, clustering variable, sample/filter, missing-data policy, and generated reproducible command. User explicitly approves the immutable version.
6. **Authorize** — a non-LLM gate verifies approval, unchanged dataset/specification fingerprints, permissions, and supported execution policy.
7. **Execute** — the bounded executor runs only the approved specification and emits an `ExecutionResult` with identity and provenance.
8. **Validate result** — verify status, observation accounting, finite statistics, requested-versus-executed equivalence, warning capture, and reproducibility metadata. Fail closed if critical checks fail.
9. **Explain** — generate a deterministic summary first; optional LLM prose may use only the validated contract. It must report estimates, uncertainty, sample, FE/cluster choices, limitations, and association/causation language.
10. **Present and recover** — display result, warnings, errors, trace, copy/download specification, and targeted recovery actions. Persist the complete chain.

## Human decision points

| Point | Human | Required decision |
|---|---|---|
| Ambiguity resolution | Researcher | Select method/variables/options when intent cannot be resolved safely. |
| Pre-execution approval | Researcher | Confirm exact immutable statistical specification. |
| Statistical policy | Method owner | Approve supported variants, sample/cluster thresholds, warning severity, and interpretation rules. |
| Data policy | Data owner/security | Approve fields sent to the model, retention, residency, and audit policy. |
| Release gate | Product + method owner + engineering | Accept evaluation evidence for each slice. |
| Escalated interpretation | Statistical reviewer | Review results that trigger defined methodological risk rules. |

## Sunny-day scenarios

| ID | Scenario | Expected behavior |
|---|---|---|
| SD-01 | “Regress leverage on profitability, tangibility, and log size using OLS with robust errors.” | Parse all roles/options, validate columns/sample, show preview, obtain approval, execute OLS, validate, explain association with uncertainty. |
| SD-02 | “Estimate leverage on profitability and tangibility with company and year fixed effects, clustered by company.” | Create two-way FE specification, verify panel/entity/time and cluster variable, preview generated command/contract, execute approved variant, report absorbed/omitted terms and within-model diagnostics. |
| SD-03 | “Does profitability predict leverage after controlling for size and tax shield?” | Detect incomplete method/covariance/FE choices; ask a compact clarification question, then continue through approval and execution. |
| SD-04 | User revisits a completed analysis | Show original request, every specification revision, approval identity/time, dataset/sample fingerprints, executable representation, result, warnings, explanation version, and downloadable trace. |

## Rainy-day scenarios

| ID | Scenario | Expected behavior |
|---|---|---|
| RD-01 | Unknown or ambiguous variable alias | Do not guess among multiple candidates; show candidates and definitions, request selection. |
| RD-02 | Dependent variable also appears as predictor | Blocking validation error with a direct correction path. |
| RD-03 | Unsupported method (for example IV/GMM outside this slice) | Refuse execution; preserve request and show supported methods without silently substituting OLS/FE. |
| RD-04 | Company/year FE requested but panel columns are missing, duplicated, or invalid | Block execution and explain the panel requirement. |
| RD-05 | Cluster variable missing, constant, too sparse, or incompatible | Block or require reviewer-approved warning according to policy; never silently fall back to conventional SE. |
| RD-06 | Missing data materially changes the estimation sample | Show pre/post counts and per-variable missingness before approval; require reapproval if the sample changes after approval. |
| RD-07 | All/most predictors are absorbed or collinear | Do not present a normal success state; identify omitted variables and classify validity according to policy. |
| RD-08 | Too few observations, firms, years, or clusters | Block execution using method-owner thresholds and explain remediation. |
| RD-09 | LLM emits malformed, unsupported, or extraneous fields | Reject the draft at schema boundary; retry once with error feedback or use manual specification form. |
| RD-10 | Model provider unavailable | Preserve user work; allow manual deterministic specification entry and direct supported execution after approval. |
| RD-11 | Execution timeout/exception | Mark failed, retain trace, do not explain partial output as a result, allow safe retry with same immutable specification. |
| RD-12 | Result includes a statistically significant coefficient but no causal design | Explanation says “associated with,” reports effect size/interval, and prohibits causal claims. |
| RD-13 | Prompt attempts to bypass validation or request arbitrary code/SQL | Treat prompt as data; permit only schema fields and allowlisted methods/options; refuse arbitrary execution. |
| RD-14 | Dataset or filters change after approval | Invalidate approval and return to review with a visible diff. |

## Functional boundary

### In scope

- Natural-language intake and typed specification drafting.
- OLS and fixed-effects regression.
- Company and year fixed effects.
- Clustered standard errors, initially company clustering.
- Dependent variable, predictor, control, FE, panel, time, and cluster validation.
- Clarification, review, explicit approval, deterministic authorization.
- Missingness/sample/collinearity warnings and unsupported-method refusal.
- Execution/result validation and statistically responsible explanation.
- User-visible status, warning, error, recovery, and traceability artifacts.

### Exclusions

- IV, GMM, difference-in-differences, random effects, causal identification automation, model search, and automatic specification optimization.
- Automatic variable discovery or “best model” selection.
- Arbitrary code, SQL, shell, user-defined functions, or unrestricted Stata execution from natural language.
- New vector database, GraphRAG, ontology, long-term personal memory, MCP layer, multi-agent team, Kubernetes migration, or platform rewrite.
- Production policy, legal/compliance, or financial-benefit claims not supported by stakeholder evidence.

## Business rules

1. The original request is immutable; clarifications create versioned specification revisions.
2. The model may propose; deterministic code validates and authorizes; the bounded executor executes.
3. No execution occurs while required fields are unknown, ambiguous, unsupported, or unapproved.
4. Requested method/options may not be silently changed. Any normalization is visible in a request-to-specification diff.
5. Dataset/filter/specification fingerprints must match at approval and execution.
6. Variable validation uses the active dataset schema and data profile, not model memory.
7. Missing-row handling is explicit and observation counts are disclosed before and after execution.
8. Unsupported methods are refused, not approximated with a supported method.
9. Explanations use the executed result contract, not a fresh reconstruction of the user's intent.
10. Causal language is prohibited unless a separately approved causal-identification contract exists; none is in this slice.
11. A critical result-validation failure yields no substantive explanation.
12. Every visible error includes a stable code, plain-language message, affected field, and recovery action.

## Expected outcomes and measures

### Expected outcomes

- Users can see and approve exactly what will run.
- Executed specifications match approved specifications.
- Unsupported/unsafe requests fail closed with actionable feedback.
- Results disclose sample, estimator, FE, clustering, omissions, and limitations.
- A reviewer can reconstruct the path from request to final explanation.

### Business KPIs

| KPI | Definition | Baseline/target status |
|---|---|---|
| Approved-result completion rate | Approved supported requests reaching validated result | Baseline `UNKNOWN`; target set after pilot baseline. |
| Median time to approved specification | Request timestamp to approval | Baseline `UNKNOWN`; measure in pilot. |
| Avoidable rerun rate | Re-runs caused by preventable specification misunderstanding | Baseline `UNKNOWN`; manually classify pilot traces. |
| Reviewer acceptance rate | Results accepted without specification/explanation correction | Baseline `UNKNOWN`; target approved by method owner. |
| Unsupported substitution rate | Unsupported requests silently run as another method | Required target: 0. |

### Process/technical KPIs

| KPI | Definition | Initial gate |
|---|---|---|
| Method-selection accuracy | Exact supported method match | ≥ 98% on golden set; 100% for explicit method names. |
| Variable-role accuracy | Correct DV/predictor/control/FE/cluster assignments | ≥ 98% exact-field accuracy; critical DV errors = 0 at release. |
| Clarification precision | Asked clarification was necessary | ≥ 90%. |
| Clarification recall | Required ambiguity triggered clarification | ≥ 98%; critical unsafe misses = 0. |
| Specification-to-execution fidelity | Approved and executed normalized contracts match | 100%. |
| Execution success | Valid approved cases complete without engine failure | ≥ 99% in controlled acceptance suite. |
| Warning accuracy | Required user-visible warnings shown with correct severity | ≥ 98%; critical omissions = 0. |
| Explanation policy compliance | No unsupported causal claim; required limitations present | 100% for critical policy rules. |
| Trace completeness | Required identifiers/events present | 100%. |

Thresholds above are design acceptance defaults, not production SLAs; owner approval is pending.

## Adoption measures

- Share of eligible OLS/FE analyses initiated through guided natural-language workflow.
- Completion rate after clarification.
- User override/correction rate on drafted specifications.
- Manual Stata fallback rate and reason.
- Download/use rate for reproducibility bundles.
- Researcher and reviewer confidence score collected after pilot tasks.

## Operating ownership

| Area | Recommended owner role | Status |
|---|---|---|
| Product workflow and adoption | Product owner | `UNKNOWN`; confirm named owner. |
| Statistical method policy and explanation policy | Statistical method owner | `UNKNOWN`; required before production. |
| Dataset definitions and quality | Data owner/steward | `UNKNOWN`; required before production. |
| Application/executor and on-call | ProfSur engineering/operations | Existing team identity `UNKNOWN`. |
| Prompt/specification schema and eval set | AI/product engineering with method-owner approval | Planning default. |
| Security/privacy review | Security/privacy owner | `UNKNOWN`; required before production. |

## Principal risks

| Risk | Control | Owner role | Trigger |
|---|---|---|---|
| Intent is converted into the wrong specification | Typed schema, ambiguity detection, diff, explicit approval, golden tests | Product + method owner | Any critical field mismatch. |
| Unsupported execution | Allowlisted capability matrix and fail-closed authorization | Engineering + method owner | Unsupported method/option appears. |
| Statistically invalid sample/specification | Deterministic preflight and result validation | Method owner | Threshold or rank/panel check fails. |
| Explanation overstates evidence | Deterministic facts, controlled wording, causal-language policy, eval | Method owner | Causal or unsupported interpretation detected. |
| Model outage or malformed output | Manual form fallback; schema rejection; bounded retry | Engineering | Provider failure/schema failure. |
| Sensitive data disclosure | Minimal model payload, redaction, retention policy, provider approval | Security/data owner | Any restricted field in outbound payload. |
| Trace contains secrets/raw sensitive content | Allowlists, redaction, hashed identifiers, retention controls | Security/engineering | Redaction or audit-integrity failure. |
| Scope expands into platform complexity | Architecture decision gate and evolve triggers | Product/architecture | Measured limits exceed current deployment. |

## Unknowns

The authoritative question and assumption register is `03_QUESTION_ASSUMPTION_REGISTER.md`. None of the current unknowns makes the design logically impossible. Several block implementation details or production release, especially statistical thresholds, data/privacy policy, ownership, production SLOs, and approval/audit retention policy.
