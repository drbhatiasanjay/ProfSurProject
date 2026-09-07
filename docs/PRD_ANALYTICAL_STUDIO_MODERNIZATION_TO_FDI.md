# PRD — ProfSur Analytical Studio Modernization and FDI Migration Program

**Document ID:** PROF-FDI-PRD-001  
**Version:** 1.0  
**Status:** Canonical implementation baseline  
**Repository:** `drbhatiasanjay/ProfSurProject`  
**Target path:** `docs/PRD_ANALYTICAL_STUDIO_MODERNIZATION_TO_FDI.md`  
**Primary objective:** Repair and harden the current ProfSur analytical experience, introduce clean capability and execution boundaries, expand analytical coverage through validated open-source engines, and create an evolutionary migration path into Financial Decision Intelligence (FDI) without a rewrite.

## 1. North Star

ProfSur is not to become a home-grown clone of Stata.

The product direction is to make rigorous financial, statistical, econometric, predictive, causal, forecasting, and scenario analysis accessible to researchers and practitioners through multiple interaction modes while preserving numerical correctness, methodological discipline, reproducibility, explainability, and evidence.

> **A trusted computational financial-decision-intelligence SaaS platform where researchers and financial practitioners can ask, build, manipulate, visualize, challenge, and reproduce complex quantitative analysis without needing to master the underlying statistical software.**

The product should ultimately support equivalent analytical intent expressed through natural language, Stata-compatible expert syntax, method-builder UI, touch interactions, scenario controls, rich interactive graphs, and later speech.

**Product principle:** **Simplify interaction; never simplify away methodological rigor.**

## 2. Why this modernization is required

ProfSur already contains Stata-like command execution, econometrics, GMM, scenarios, ML, forecasting, lifecycle transitions, interaction analysis, data exploration, rich charts, commentary, and an AI Assistant.

However, analytical logic is distributed across handlers, model modules, and page-specific workflows. Some commands that appear supported have incomplete or approximate semantics. Some analytical state is process-global. UI behavior, computation, and interpretation are not separated strongly enough for a multi-tenant SaaS or the full FDI architecture.

The modernization has two purposes:

1. **Make ProfSur reliable now.**
2. **Ensure each improvement is reusable in FDI later.**

## 3. Architectural principles

### 3.1 Stable contracts, replaceable implementations

FDI/ProfSur must be specification-centric rather than implementation-centric.

Stable concepts:
- `AnalyticalRequest`
- `PanelContext`
- `ModelResultContext`
- `CapabilityRequest`
- `CapabilityResult`
- `AnalysisRun`
- `VisualizationArtifact`
- `NarrativeArtifact`
- later `AnalyticalState`

Replaceable components include StatsPAI, PyFixest, linearmodels, statsmodels, PyWhy/DoWhy, scikit-learn, XGBoost, LightGBM, visualization renderers, LLM providers, speech engines, and UI frameworks.

No UI page may become directly dependent on a specific external analytical engine once the adapter layer is introduced.

### 3.2 Deterministic analytical authority

LLMs may understand questions, classify intent, decompose compound questions, recommend methods within permitted boundaries, generate or explain syntax, summarize verified results, challenge assumptions, and compose audience-specific commentary.

LLMs must not invent coefficients, calculate authoritative econometrics in model memory, silently change variables/estimators/samples/data vintages, fabricate citations, upgrade association to causation, or bypass tenant/data/tool permissions.

### 3.3 Open-source-first analytical execution

Prefer validated open-source implementations where suitable. Candidate engines include PyFixest, StatsPAI, linearmodels, statsmodels, SciPy, PyWhy/DoWhy, scikit-learn, XGBoost, LightGBM, and future engines that satisfy the same adapter contract.

No library is accepted because of feature claims alone. Capability adoption requires numerical and behavioral validation.

### 3.4 Do not hand-code mature estimator mathematics unnecessarily

Hand-written code is appropriate for parser/translation logic, FDI-specific financial semantics, lifecycle logic, scenario semantics, capability routing, typed contracts, provenance, claim governance, visualization metadata, and orchestration.

Established engines should perform commodity numerical estimation wherever they can be independently validated.

## 4. Software development methodology

### 4.1 GSD-style execution discipline

For this programme, GSD means goal-driven, bounded, evidence-producing delivery:

1. Define the user-visible outcome.
2. Define explicit non-goals.
3. Identify the smallest vertical slice.
4. List expected files and blast radius before editing.
5. Implement the smallest sufficient change.
6. Verify with deterministic tests.
7. Verify affected UI surfaces.
8. Produce evidence and a GitHub implementation report.
9. Stop at the PR/wave boundary.
10. Do not begin the next wave until the current wave is reviewed and accepted.

This must follow `docs/ENGINEERING_PLAYBOOK.md`.

### 4.2 TDD

TDD is mandatory for financial calculations, econometric translations, command parsing, alias resolution, typed errors, capability routing, panel validation, post-estimation calculations, scenario calculations, claim/tier restrictions, and security/tenant boundaries.

```text
RED → GREEN → REFACTOR → VERIFY
```

### 4.3 Contract-first development

Before a new backend or major capability, define typed contracts first. External libraries adapt to our contracts; our contracts must not simply expose third-party objects.

### 4.4 Vertical slicing

Each PR must deliver an observable path:

```text
request → validation → execution → result → error behavior → UI state → tests → report
```

### 4.5 No hidden broad refactors

Do not mix unrelated UI redesign, dependency upgrades, database changes, large renames, or formatting sweeps into analytical PRs unless explicitly authorized.

## 5. Mandatory GitHub implementation reporting

Every implementation PR/wave must produce a durable report in GitHub.

**Directory:** `docs/implementation-reports/`

**Naming:** `WAVE_<N>_PR_<NN>_<SHORT_NAME>_REPORT.md`

Example: `docs/implementation-reports/WAVE_0_PR_01_STATA_RELIABILITY_REPORT.md`

Every report must contain:
- goal;
- scope completed;
- explicit non-goals respected;
- files changed;
- contracts changed;
- dependencies/license rationale;
- tests added;
- exact test commands;
- test results;
- numerical/golden evidence;
- UI surfaces affected;
- UI verification performed;
- screenshots/traces if applicable;
- errors encountered;
- known limitations;
- logging/observability changes;
- backward compatibility;
- security/data-scope assessment;
- remaining risks;
- recommendation for next wave;
- commit SHA/PR when available;
- final `READY_FOR_REVIEW` or `BLOCKED`.

The coding agent must never report completion only in chat.

## 6. Testing and quality strategy

Extend the existing `docs/TEST_PLAN_MODERN_UI.md`.

### L1 Unit/property tests
For parsers, aliases, schemas, panel invariants, numerical helpers, error taxonomy, scenario transformations.

### L2 Financial/econometric golden tests
Validate coefficient estimates, SEs, sample membership, dropped observations, diagnostics, predictions, marginal effects, and failure behavior with explicit tolerances.

### L3 Contract/integration tests
Verify command → request, request → adapter, normalized results, typed errors, registry, serialization, and backward-compatible consumers.

### L4 LLM/copilot behavioral tests
Later waves test intent, tier preservation, explanation, translation, causal-language guards, use of verified values, and abstention. LLM judges are never sole mathematical truth oracles.

### L5 Semantic UI tests
Prefer component tests, DOM/semantic assertions, Playwright ARIA snapshots, stable table/chart metadata. Avoid whole-page body-text as primary oracle.

### L6 Critical E2E journeys
Focus on high-value workflows, not page×option Cartesian traversal.

### L7 Visual regression
Use fixed viewport, deterministic data, animations disabled, masked dynamic content, region/component screenshots where possible, full-page only for high-value release gates.

### L8 Accessibility
Automated accessibility where feasible, keyboard/navigation checks, semantic labels, readable errors, and never rely on color alone.

### UI verification is mandatory in every wave

Every PR declares:

`UI impact: NONE | INDIRECT | DIRECT`

- NONE: run relevant smoke/integration tests.
- INDIRECT: affected component/integration tests + one browser smoke path.
- DIRECT: component tests + semantic/ARIA + targeted Playwright + screenshot/visual comparison + relevant theme/responsive checks.

No PR is complete while an affected UI path is unverified.

## 7. Error handling architecture

### Typed error taxonomy

`SYNTAX_ERROR`, `UNRECOGNIZED_COMMAND`, `UNSUPPORTED_OPTION`, `UNSUPPORTED_CAPABILITY`, `VARIABLE_NOT_FOUND`, `AMBIGUOUS_VARIABLE`, `PANEL_NOT_DECLARED`, `DUPLICATE_PANEL_KEYS`, `INVALID_TIME_VARIABLE`, `INSUFFICIENT_OBSERVATIONS`, `INSUFFICIENT_VARIATION`, `COLLINEARITY`, `SINGULAR_MATRIX`, `NONCONVERGENCE`, `PERFECT_SEPARATION`, `INVALID_INSTRUMENT_SPEC`, `DIAGNOSTIC_FAILURE`, `METHOD_NOT_PERMITTED`, `CAUSAL_GATE_REQUIRED`, `DATA_SCOPE_ERROR`, `TENANT_SCOPE_ERROR`, `DEPENDENCY_UNAVAILABLE`, `ENGINE_UNAVAILABLE`, `ENGINE_FAILURE`, `EXPORT_FAILURE`, `INTERNAL_ERROR`.

### Error object

```yaml
error_id:
error_type:
severity:
user_message:
technical_message:
command:
normalized_command:
analysis_run_id:
workspace_id:
engine:
engine_version:
recoverable:
suggested_actions:
cause_chain:
timestamp:
```

Sensitive data must be redacted.

### User-facing error standard

Every error should answer:
1. What happened?
2. Why?
3. Was anything changed?
4. What can the user do?
5. Is this input, data, methodology, or system related?

Raw tracebacks are not normal UX. Expert users may expand technical details.

## 8. Logging and observability

Use structured logs with:

`timestamp`, `level`, `event_type`, `request_id`, `correlation_id`, `session_id`, `workspace_id`, pseudonymous user/tenant ID, `analysis_run_id`, `command_family`, `capability_id`, `engine_id`, `engine_version`, `dataset_fingerprint`, `duration_ms`, `status`, `error_type`, `error_id`.

Never log secrets, credentials, full sensitive datasets, or unrestricted proprietary source contents.

Every analytical user action receives a `correlation_id` connecting UI → parser → routing → engine → AnalysisRun → chart → commentary → error/report.

Logs are operational evidence; `AnalysisRun` is authoritative analytical/reproducibility evidence.

## 9. Capability status model

Use exactly:

`CANDIDATE`, `IMPLEMENTED_UNVERIFIED`, `VALIDATED`, `UNSUPPORTED`, `NATIVE_RUNTIME_ONLY`, `COMMUNITY_COMPATIBILITY`.

## 10. Wave roadmap

### WAVE 0 — Immediate Stata Studio reliability

**Scope**
- add `python-docx`;
- fail-safe optional Word export;
- `companycode → company_code` alias;
- real `xtset`;
- session-scoped `PanelContext`;
- duplicate entity-time validation;
- panel balance/gap metadata;
- `lgraph` through existing graph infrastructure;
- exact screenshot regression fixtures;
- typed errors and structured logs for changed paths;
- UI verification.

**Acceptance commands**
```stata
xtset companycode year
lgraph leverage prof year, wide
tabulate corplifestage
xtreg leverage i.corplifestage c.prof##c.tang c.prof##c.dvnd taxShield intRate i.year, fe
```

**Required report**
`docs/implementation-reports/WAVE_0_PR_01_STATA_RELIABILITY_REPORT.md`

**Non-goals**
No extra Stata commands, GMM rewrite, ML changes, navigation redesign, new chart library, Stata parity claim, or new process-global state.

**Exit**
Observed screenshot failures are resolved and normal Studio use no longer exposes DOCX import traceback.

### WAVE 1 — Existing analytical semantic correctness

Harden `xtreg`, `margins`, `marginsplot`, `xtserial`, `xttest0`, `hausman`, `estimates`, `esttab`.

Requirements:
- no silent estimator substitution;
- genuine post-estimation semantics;
- diagnostics tied to active model;
- compatible Hausman samples/specifications;
- session/workspace-scoped `ModelResultContext`;
- explicit unsupported-option behavior;
- method/result provenance in UI;
- diagnostic warnings separate from failures.

Exit: supported commands have explicit semantics and no known silent method changes.

### WAVE 2 — Command and capability abstraction

Deliver:
- `CommandRegistry`;
- `CapabilityRegistry`;
- `AnalyticalRequest`;
- adapter interface;
- normalized `CapabilityResult`;
- typed `AnalyticalError`;
- routing audit fields.

Flow:
```text
raw command → parser → normalized command → AnalyticalRequest → CapabilityRegistry → adapter → CapabilityResult → renderer
```

Pages may not directly call third-party econometric libraries once migrated.

### WAVE 3 — Open-source technology evaluation spike

Evaluate StatsPAI, PyFixest, linearmodels, statsmodels, SciPy, PyWhy/DoWhy, sklearn, XGBoost/LightGBM, and optional candidates such as Hayashi.

Use a frozen benchmark dataset and at least:
1. descriptive;
2. OLS;
3. FE;
4. FE + year effects;
5. lifecycle interaction;
6. RE;
7. HDFE;
8. IV/2SLS;
9. dynamic-panel/GMM;
10. DID/event study;
11. prediction;
12. controlled failure.

Compare numerical accuracy, sample semantics, inference, diagnostics, error semantics, structured output, performance, license, maintenance, integration complexity.

Output:
`docs/implementation-reports/WAVE_3_ENGINE_EVALUATION_REPORT.md`
plus machine-readable engine/capability matrix.

### WAVE 4 — Core Stata-compatible research expansion

Add only after adapter seam:
- `describe`, `codebook`, `count`, `mean`, `proportion`;
- `xtdescribe`, `xtsum`, `xttab`, `xtline`;
- `predict`, `test`, `testparm`, `lincom`, `nlcom`;
- selected `estat` diagnostics;
- diagnostic visuals.

Help/autocomplete/capability badges should be driven by registry state.

### WAVE 5 — Advanced econometrics, scenario, ML, forecasting, transitions

Wrap current capabilities first, then validate.

**GMM**
Current implementation becomes `CurrentProfSurGMMAdapter`, initially `IMPLEMENTED_UNVERIFIED`. Compare externally before selecting production backend. Support lag/instrument metadata, AR(1)/AR(2), Hansen/Sargan, instrument count/proliferation warnings, and careful wording.

**IV/HDFE/DID**
Standardize through capability adapters. Causal methods stay behind methodology gates.

**Scenario**
Create `ScenarioCapability` with:
```yaml
baseline:
interventions:
held_constant:
model:
prediction:
uncertainty:
comparison:
provenance:
```

**ML**
Register supervised regression/classification, model comparison, feature importance, local explanation, panel/time-aware validation.

**Forecasting/clustering/transitions**
Register as capabilities before redesign.

### WAVE 6 — Bidirectional analytical language engine

Enable:
- Stata → structured analytical intent + explanation;
- natural language → structured analytical intent;
- analytical intent → executable plan/syntax;
- multi-step research plans rather than one-command guessing;
- gradual replacement of current AI Assistant with FDI-style Copilot;
- replaceable reasoning provider adapters for OpenAI, Claude, Gemini, future providers.

Natural language, expert syntax, and method-builder input must converge on the same normalized request.

### WAVE 7 — Rich visualization, narrative, interactive analytical workspace

Introduce:
- `VisualizationArtifact`;
- `NarrativeArtifact`;
- `StoryArtifact`;
- deterministic Fact Sheet;
- Insight Candidate generation;
- claim filtering;
- narrative validation;
- interactive operations: select, filter, drill, compare, explain, challenge, scenario_change, undo, redo, branch, reproduce.

At least one controlled researcher journey must demonstrate analysis → visualization → commentary → challenge → reproduce.

### WAVE 8 — FDI migration boundary

Move validated capabilities into canonical FDI architecture:
- `AnalyticalState`;
- multi-tenant workspaces;
- immutable dataset snapshots;
- immutable `AnalysisRun`;
- Evidence Engine;
- Claim Ledger;
- model-independent Copilot;
- reasoning router;
- researcher/practitioner views.

Reasoning provider capability must never widen analytical, tenant, data, or tool permissions.

## 11. UI rules for all waves

For Waves 0–5, preserve familiar navigation and workflows. Add UX only where required for correctness, provenance, capability status, error handling, and traceability.

Use consistent states:
`success`, `warning`, `needs_input`, `unsupported`, `failed`, `blocked`.

Long operations:
`queued`, `planning`, `validating`, `executing`, `post-processing`, `complete`, `failed`.

No silent correction of estimator, sample, data vintage, or material method choice.

## 12. Traceability requirements

Progressively record:
`request_id`, `correlation_id`, session/workspace, dataset fingerprint, raw request, normalized request, capability, engine/version, method, variables, sample, filters, warnings, diagnostics, result fingerprint, duration, error ID.

## 13. Dependency policy

Every dependency requires purpose, capability, license, maintenance health, security note, runtime impact, fallback, and replaceability plan.

No dependency should be imported throughout the app; keep it behind an adapter.

## 14. Definition of Done — capability

Requires:
- valid fixture;
- invalid fixture;
- missing-variable fixture;
- golden numerical case;
- sample validation;
- SE/covariance validation where relevant;
- diagnostics;
- error path;
- registry entry;
- compatibility classification;
- structured logging;
- user-facing error;
- UI verification;
- implementation report;
- documented limitations.

## 15. Definition of Done — PR

Every PR must:
1. state scope and non-goals;
2. state risk/blast radius;
3. add/modify tests before or alongside implementation;
4. pass affected tests;
5. pass required regression gate;
6. perform UI verification;
7. add/update structured logging when execution path changes;
8. avoid raw traceback exposure;
9. update contracts/docs;
10. create GitHub implementation report;
11. include exact commands/results;
12. end `READY_FOR_REVIEW` or `BLOCKED`;
13. stop and not start the next PR automatically.

## 16. Mandatory review checkpoints

Independent review after Waves 0, 1, 2, 3, 5, 6, 7, and before FDI production migration.

Review:
- numerical correctness;
- methodology;
- architecture drift;
- UI regression evidence;
- security/data boundaries;
- logging/traceability;
- dependency/license posture;
- alignment with North Star.

## 17. Immediate execution instruction — PR-1

> **Implement Wave 0 / PR-1 only: Stata Studio Immediate Reliability Remediation.**
>
> Follow `docs/ENGINEERING_PLAYBOOK.md` and this PRD. Use GSD-style bounded delivery, contract-first design where required, and TDD for parser/panel/error behavior. Before editing, write the goal, expected files, blast radius, risks, and non-goals.
>
> Fix the missing `python-docx` dependency while ensuring absence of optional Word export cannot crash Stata Studio. Add canonical `companycode → company_code` resolution. Implement real `xtset` with session-scoped `PanelContext`, duplicate entity-time validation, core panel metadata, and useful user-facing output. Implement `lgraph leverage prof year, wide` through the existing visualization/aggregation infrastructure; do not create a parallel chart engine. Add permanent regression tests for the exact observed commands.
>
> Introduce typed errors and structured logging for changed paths. User-facing errors must explain what failed and provide an `error_id`; raw tracebacks must not be normal UI.
>
> **UI verification is mandatory.** Confirm Studio loads, command history status is correct, `xtset` output is usable, `lgraph` renders, error states are readable, and affected visual surfaces do not regress. Use targeted component/semantic/Playwright checks rather than blindly replaying every page. Capture visual evidence only for affected surfaces.
>
> Do not add other Stata commands. Do not change econometric estimator semantics. Do not redesign unrelated UI. Do not rewrite GMM/ML/scenario modules. Do not claim Stata parity. Do not introduce process-global analytical state.
>
> Create and commit:
> `docs/implementation-reports/WAVE_0_PR_01_STATA_RELIABILITY_REPORT.md`
>
> The report must contain changed files, tests added, exact test commands/results, exact screenshot-command acceptance evidence, UI verification, logging/error-handling changes, dependency/license note, known limitations, risks, commit SHA/PR if available, and final `READY_FOR_REVIEW` or `BLOCKED`.
>
> Stop after PR-1. Do not start Wave 1 until independent review accepts Wave 0.

## 18. Programme sequence

```text
PR-1  Wave 0 — Immediate Stata reliability
PR-2  Wave 1 — Existing-command semantic remediation
PR-3  Wave 1/2 — PanelContext + ModelResultContext hardening
PR-4  Wave 2 — CommandRegistry + CapabilityRegistry
PR-5  Wave 2 — AnalyticalRequest + adapter contracts
PR-6  Wave 3 — Open-source engine evaluation spike
PR-7  Wave 4 — Core research command expansion
PR-8  Wave 4 — Post-estimation and diagnostics
PR-9  Wave 5 — IV/HDFE/GMM capability adapters
PR-10 Wave 5 — Scenario/ML/forecast/transition wrappers
PR-11 Wave 6 — Natural language ↔ analytical request ↔ expert syntax
PR-12 Wave 6 — Embedded multi-model Copilot gateway
PR-13 Wave 7 — Visualization/Narrative/Story artifacts
PR-14 Wave 7 — Interactive analytical state and interaction protocol
PR-15 Wave 8 — Controlled FDI researcher vertical-slice migration
```

Each PR must be independently mergeable, testable, and reviewable.

## 19. Final success criteria

The programme succeeds when:
1. immediate broken Stata workflows are reliable;
2. existing commands are semantically defensible;
3. new commands use capabilities rather than ad-hoc handlers;
4. mature estimator math comes from validated open-source engines;
5. page modules no longer own isolated analytical truth;
6. natural language and expert syntax converge on the same analytical request;
7. results produce reproducible rich visual and narrative artifacts;
8. failures are diagnosable through typed errors and correlation IDs;
9. every wave leaves durable GitHub evidence;
10. FDI migration is evolutionary rather than a rewrite;
11. analytical software cost drops without compromising output quality;
12. rigorous financial/econometric analysis becomes intuitive for researchers and practitioners.
