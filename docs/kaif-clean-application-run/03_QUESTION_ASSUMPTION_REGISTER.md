# Question and Assumption Register

`UNKNOWN` means no answer was available in tracked ProfSur or the supplied use case. Defaults permit design continuity only; they are not stakeholder-approved facts.

Blocking levels:

- **Design** — must be answered before the relevant design can be considered coherent.
- **Implementation** — design may proceed, but the affected build slice cannot exit.
- **Production release** — build/pilot may proceed under controlled conditions, but production promotion is blocked.
- **Non-blocking** — can be tuned after baseline measurement.

| ID | Question (`UNKNOWN`) | Why it matters | Assumption - planning default | Approver | Blocking level | Decision deadline |
|---|---|---|---|---|---|---|
| Q-01 | Who is the accountable product owner? | Owns scope, UX defaults, adoption, and release decision. | ProfSur product lead acts as accountable owner. | ProfSur sponsor | Production release | Before Slice 0 exit |
| Q-02 | Who is the statistical method owner/reviewer? | Must approve supported estimator semantics, thresholds, warnings, and explanation policy. | Named econometrics faculty/research lead owns method policy. | ProfSur sponsor | Implementation | Before Slice 1 acceptance criteria are frozen |
| Q-03 | Which panel vintage is canonical for this workflow? | Dataset identity and reproducibility depend on a stable source. | Use the active user-selected panel; approval binds its dataset/filter fingerprint. | Data owner + product owner | Implementation | Before Slice 1 build |
| Q-04 | What are authoritative variable labels, units, and admissible roles? | Prevents alias mistakes and invalid interpretation. | Generate catalog from active schema; data steward curates labels/units/role constraints. | Data owner | Implementation | Before variable-validation release |
| Q-05 | Are transformations/lags/interactions allowed in the first slice? | Changes parser grammar, validation, and explanation. | Exclude transformations/lags; allow only plain columns. Year FE is a dedicated option, not a free-form factor term. | Method owner | Implementation | Before Slice 1 scope lock |
| Q-06 | What exactly does “company and year fixed effects” mean in ProfSur policy? | Must distinguish absorbed entity effects from explicit year effects and avoid ambiguous display. | Two-way FE: company effects plus year effects; show both in specification/result metadata. | Method owner | Implementation | Before FE executor adapter acceptance |
| Q-07 | Which clustering choices are supported? | Covariance semantics and minimum-cluster rules are method-specific. | First slice supports one-way clustering by `company_code` only; no silent fallback. | Method owner | Implementation | Before Slice 1 scope lock |
| Q-08 | Minimum observations, entities, periods, and clusters? | Required for fail-closed sample validation. | Pilot defaults: N≥30, entities≥10 for FE, periods≥2, clusters≥30 for clustered inference; thresholds are configurable and visibly labeled pending approval. | Method owner | Production release | Before pilot exit; final values before production |
| Q-09 | How should missing data be handled? | Determines sample and potential bias. | Complete-case analysis on required fields; show per-field and total exclusions before approval; no automatic imputation. | Method owner + data owner | Implementation | Before Slice 1 acceptance |
| Q-10 | What collinearity/absorption policy determines warning vs failure? | A model can run while failing the research intent. | Block if DV invalid, rank is zero, or all requested predictors are omitted; warn and require reapproval when any named predictor/control is omitted. | Method owner | Implementation | Before result-validator build |
| Q-11 | Is winsorization permitted and, if so, when? | It changes the approved estimand and sample values. | No automatic winsorization in this slice; any future transformation must be explicit in specification. | Method owner | Implementation | Before executor adapter build |
| Q-12 | Must the user approve every run or may identical reruns reuse approval? | Defines authorization and UX friction. | Every new specification or dataset/filter fingerprint needs approval; exact rerun may reuse approval within the same authenticated session only if policy allows, otherwise ask. | Product + method owner | Production release | Before approval UX finalization |
| Q-13 | Who may execute analyses by role? | Authorization matrix depends on authenticated roles. | Existing authenticated researcher/admin roles may propose and approve their own read-only analyses; viewers may inspect only. | Product + security | Production release | Before authorization implementation |
| Q-14 | What dataset fields may be sent to the model provider? | Privacy and provider terms constrain parser/explainer context. | Send schema metadata and bounded result summaries only; do not send raw panel rows unless separately approved. | Data owner + privacy/security | Production release | Before any production model call |
| Q-15 | Data classification, residency, and retention requirements? | Determines logging, provider, region, and audit controls. | Treat dataset and prompts as internal research data; redact identifiers from model payload/logs; retain trace metadata, not raw prompts/results beyond existing policy. Exact retention remains unset. | Data owner + privacy/security | Production release | Before production architecture sign-off |
| Q-16 | Is Google Gemini an approved production provider and is `gemini-2.5-flash` approved? | Current source uses it, but vendor approval is not evidenced. | Retain current model/API ID for pilot only behind a provider-neutral adapter; manual deterministic form remains available. | Security/procurement + product | Production release | Before production pilot |
| Q-17 | What model quality/cost budget applies? | Needed for routing, rate limits, and cost controls. | One parser call and at most one explanation call per completed request; no autonomous loops; monetary budget `UNKNOWN`, meter tokens/cost first. | Product + finance/platform | Non-blocking for build; production release for cap | Before production launch |
| Q-18 | What production traffic, concurrency, latency, and availability are required? | Drives deployment and scaling decisions. | Continue current Cloud Run service; interactive target p95 ≤10 s excluding explicit long-run notice; no SLA claim until measured. | Product + operations | Production release | Before load/capacity gate |
| Q-19 | What trace/audit retention and export format are required? | Traceability is a core requirement and may contain sensitive data. | Store immutable structured records linked to existing chat/session IDs; downloadable JSON + human-readable summary; retention `UNKNOWN`. | Product + data/privacy owner | Production release | Before audit-store release |
| Q-20 | What constitutes reviewer-required “statistically risky”? | Drives escalation and user-visible state. | Escalate when approved thresholds fail, key predictors are omitted, cluster count is below threshold, model/result validator is partial, or requested interpretation implies causality. | Method owner | Implementation | Before evaluation suite finalization |
| Q-21 | Accessibility target? | Warnings, dialogs, tables, and status must be usable. | WCAG 2.2 AA planning target; keyboard operation, non-color severity labels, focus management, and screen-reader names required. | Product + accessibility owner | Production release | Before UI acceptance |
| Q-22 | Which languages must natural-language requests support? | Affects dataset, prompts, and evaluation coverage. | English only in first slice. | Product owner | Non-blocking | Before pilot recruitment |
| Q-23 | What baseline business/process metrics exist? | Targets cannot be responsibly set without baseline. | Instrument pilot and establish baseline before setting improvement targets; no financial claim. | Product owner | Non-blocking | End of pilot |
| Q-24 | Is a separate human reviewer required for all results or selected cases? | Changes operating model and turnaround time. | User self-approval for ordinary read-only analyses; method reviewer only for policy-triggered cases. | Method owner + product | Production release | Before workflow policy approval |
| Q-25 | What failure recovery and support ownership exists outside business hours? | Needed for production runbook/SLO. | Fail safely, preserve trace, allow idempotent retry; business-hours support until an on-call commitment is approved. | Operations owner | Production release | Before production launch |
| Q-26 | Are explanations allowed to cite literature automatically? | Citation accuracy and licensing affect the result contract. | First slice explains statistical output and limitations without generated literature claims; existing curated literature features remain separate. | Method owner + product | Implementation | Before explanation template acceptance |
| Q-27 | Should direct Stata commands share the same approval/trace contract? | Avoids inconsistent safety pathways. | New guided NL flow uses the contract first; direct console remains unchanged in Slice 1, with convergence planned in a later slice. | Product + method owner | Non-blocking for Slice 1 | Before Slice 3 planning |
| Q-28 | Is a persistent prompt/version registry available? | Reproducibility requires parser/explainer version identity. | Store prompt-pack hash and model ID in the trace; Git-tracked prompt pack is source of truth. | Engineering + method owner | Implementation | Before Slice 1 exit |
| Q-29 | What rollback mechanism is approved? | Model/prompt/statistical policy changes can regress behavior. | Feature flag disables NL-guided execution and returns users to current direct workflows; database changes are additive and backward-compatible. | Engineering + product | Production release | Before first deployment |
| Q-30 | Is current Cloud Run region/unauthenticated ingress acceptable? | Deployment configuration and app-level auth may not equal infrastructure policy. | Preserve current deployment for design; security review must explicitly approve ingress, IAM, region, and secrets before release. | Security + operations | Production release | Before deployment approval |

## Approval register

| Approval | Owner role | Status |
|---|---|---|
| Business scope and KPIs | Product owner | Pending |
| Statistical contract and thresholds | Statistical method owner | Pending |
| Dataset catalog and permissible fields | Data owner | Pending |
| Model/provider/data-processing posture | Security/privacy/procurement | Pending |
| UI accessibility | Product/accessibility owner | Pending |
| Production SLO/deployment/rollback | Operations + engineering | Pending |
| Pilot release | Product + method owner + engineering | Pending |
