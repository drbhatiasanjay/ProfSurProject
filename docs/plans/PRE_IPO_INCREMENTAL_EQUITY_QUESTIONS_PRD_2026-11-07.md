# Incremental PRD: Pre-IPO investor questions, evidence and decision support

Version 1.0. Date: 7 November 2026. Status: **specified; implementation and acceptance pending**. Project: ProfSurProject. This is a queued increment, not an instruction to interrupt Antigravity's active build.

Follow-on methodology: [Decision-depth algorithm PRD](PRE_IPO_DECISION_DEPTH_ALGORITHM_PRD_2026-11-07.md) adds adversarially challenged algorithms for the advanced thesis, funding, valuation, comparison and monitoring capabilities. Read it at the next appropriate checkpoint; do not interrupt current work or run duplicate builds. This document remains the base product/UX requirement set.

## 1. Product decision and execution sequence

Extend the existing Pre-IPO feature from historical debt/offer analysis into an evidence-backed equity investment thesis. Preserve the debt capability as a distinctive component. Give investors useful answers about the business, growth, earnings, management, price, downside and return path, with sources and unresolved diligence clearly visible.

Finish and verify the active build first. Then inspect what exists, record already verified/partial/missing/blocked requirements and implement the remaining delta. Correct inherited defects that block dependent functionality before extending it. Do not restart the original feature, repeat completed work or conceal unresolved correctness issues behind new UI.

This PRD consolidates the product scope discussed after the first review, including the company overview, extracted-data/CMIE comparison, analytical tools, interpretation, recommendations, missing-data register and UI. It is the authoritative scope document for this follow-on increment. Earlier briefs remain context and their correctness/security requirements remain in force. If an earlier brief conflicts with this one on follow-on information architecture or scope, use this PRD and record the decision. Actual project instructions, verified legal applicability and source facts take precedence over design examples.

Local reference documents:
- `docs/plans/PRE_IPO_ANTIGRAVITY_NEXT_BUILD_PROMPT_2026-11-07.md`
- `docs/plans/PRE_IPO_INCREMENT_2_DATA_TOOLS_OVERVIEW_UI_2026-11-07.md`
- `docs/reviews/PRE_IPO_RED_TEAM_REVIEW_2026-11-06.md`
- `docs/reviews/PRE_IPO_LATEST_CODE_REVIEW_2026-11-07.md`
- [research and source register](../research/PRE_IPO_EQUITY_DECISION_RESEARCH_2026-11-07.md)

These files currently live in `C:/Users/hemas/.codex/worktrees/profsur-financing/ProfSurProject`; they may not exist in another checkout until deliberately transferred or committed. Do not assume a push has occurred.

## 2. Observed baseline and remaining gaps

The canonical checkout was inspected at HEAD `2df06abfb49ca0fc64a4559613338ab7c7c7e867`, including uncommitted Pre-IPO changes. The source snapshot is hashed in `scratch/pre_ipo_prd_research_2026_11_07/manifest.json`. Source observations are not authenticated browser acceptance.

Final document validation detected further changes in the data, engine, ingestion, schema, page and tests after snapshot capture. The baseline table describes the captured revision only; it is not a final audit of Antigravity's continuing work. The S0 delta check must use the completed implementation.

| Area | Observed foundation | Delta required |
| --- | --- | --- |
| Analysis UI | Twelve tabs, existing charts and financial workpapers | Add a question-led synthesis without duplicating engines or hiding existing analysis |
| Commentary | Seven generators with six-part output | Structured claim/evidence links; remove generic unsupported impact estimates and certainty |
| Personas | CFO, lender, investor, retail, board, compliance | Extend equity/private/strategic/research lenses and explicit transaction context |
| Missing information | `DecisionLimitationItem` and a limitations tab | Attribute dependencies, prioritized requests, owners and recomputation |
| Peer statistics | Optional medians and even-count correction | Validate cohort/as-of comparability and propagate unavailable states |
| Ingestion | File-object extraction and failed-upload pathway | Distinguish null from zero, review states, provenance and unknown-document acceptance |
| Identity/export | Dossier and PPTX generator | Versioned shared snapshot and question/recommendation/gap parity |
| Data/tools | Audit items and registered original application pages | Full local CMIE crosswalk and applicability/integration inventory |

Observed remaining issues include broad evidence strings, hardcoded forecast-impact ranges, prescriptive default thresholds and a failed-extraction dossier with zero financial placeholders. Recheck them; do not assume they remain unchanged when implementation starts. In particular, do not repeat earlier findings about invented upload revenue as a current defect without rerunning them against the new code.

## 3. Goals, boundaries and success

### Goals

G1. A user can understand what the company does before encountering detailed financial analysis.

G2. Every core investor question receives a company-specific answer, a qualified partial answer, or a precise explanation of why it cannot yet be answered.

G3. Each material factual assertion and numerical conclusion can be traced to an accepted source or reproducible computation. Interpretations, assumptions and external methods remain distinguishable.

G4. Users can inspect extracted attributes, compare them with actual CMIE reference fields, identify missing inputs and see which decisions are affected.

G5. Relevant existing tools operate on the correct company/source/peer/scenario context; unsuitable methods are explained instead of forced onto short histories.

G6. Recommendations have conditions, alternatives, proposed owners and monitoring; screen and exports share the same accepted analysis.

### Boundaries

This is company research and decision support. A selected persona does not establish investment suitability, regulatory eligibility, a trading mandate or professional approval. Do not execute trades, subscriptions, lender instructions or external messages. Do not claim guaranteed returns, official ratings, legal clearance or validated probabilities without the necessary evidence.

No requirement to train new ML models, estimate post-IPO survival or build every possible Stata command into the page. The requirement is transparent coverage, appropriate reuse and justified applicability. No new commercial data entitlement is assumed. No manuscript changes, local LLMs, unsolicited deployment, merge or push.

### Acceptance outcomes

All ten core question families and all four existing exemplars are represented. Every material answer has lineage or a visible insufficient-evidence state. Every critical gap appears in the executive view and export. No unsupported recommendation becomes actionable solely because a field is missing. Personas preserve the same facts. These are release criteria, not claims of current achievement.

## 4. Personas and transaction contexts

Use sophistication, objective, horizon and information needs rather than wealth as a proxy for understanding. “Small/medium/high investor” are user descriptions, not statutory categories. Do not encode subscription-category thresholds from this PRD.

| Persona | Decision emphasis | Required output |
| --- | --- | --- |
| Retail / plain-language | Understand the company, price, dilution and downside | Readable thesis, major risks, unknowns and questions before deciding |
| Experienced individual | Challenge assumptions and compare alternatives | Valuation range, scenario drivers and monitoring checklist |
| HNI / family office | Capital preservation, concentration, liquidity and terms | Downside, ownership/governance, liquidity constraints and diligence pack |
| Institutional public equity | Differentiated investment thesis and portfolio capacity | Forecasts, valuation workpapers, catalysts, counter-thesis and liquidity limits |
| PE / growth equity | Negotiated investment, value creation and exit | Rights/terms, funding plan, operating initiatives, return waterfall and exit dependencies |
| Strategic equity investor | Standalone value plus integration/synergies | Separate synergy assumptions, execution cost, control and conflicts |
| CFO / founder / treasury | Funding alternatives and value per share | Capital allocation, dilution/control and financing trade-offs |
| Lender / credit committee | Liquidity and repayment protection | Actual covenants, stress, collateral and diligence conditions |
| Board / investment committee | Decision, alternatives, accountability | Conditions before action, capital at risk, owners and monitoring |
| BRLM / adviser | Offer/disclosure/pricing consistency | Source gaps, offer economics and execution dependencies |
| Auditor / legal / compliance | Verifiability and applicability | Accounting judgments, conflicts, source lineage and review tasks |
| Researcher | Reproducibility and limits | Formulas, cohort query, model diagnostics and external validity |

Separate transaction context from persona: (a) public IPO ordinary-equity research; (b) private/pre-IPO negotiated investment; (c) strategic/control transaction; (d) later monitoring. A family office can use context (a) or (b). Do not infer private rights or liquidity preferences from an IPO prospectus. Switching context must disclose which facts remain valid and which terms are unavailable.

Portfolio fit is an optional separate discussion requiring user inputs. Do not manufacture position sizes or personal suitability from issuer data. Proposed personas have not been validated through user interviews; schedule product validation after a demonstrable build.

## 5. Information architecture and workflow

Default sequence:

**Company Overview → Investor Questions & Investment Thesis → Detailed Analysis → Data & Evidence → Recommendations & Actions.**

All sections are accessible without a forced wizard. Data & Evidence is prominent and linked from every answer. Company introduction appears first. The investor-question feature is one coherent local section/tab with expandable answers, not ten additional top-level tabs. Existing workpapers remain reachable under Detailed Analysis; do not delete accepted analytical functionality.

Primary journey:
1. Select an exemplar or upload an authorized document; show demonstration/verification state.
2. Inspect company background, source version and as-of context.
3. Review extracted facts and material gaps; accept/correct a versioned snapshot.
4. Choose a persona and transaction context.
5. Read the executive thesis and expand relevant questions.
6. Follow evidence or run an applicable analysis; optionally apply scenario assumptions through a form.
7. Review conditional recommendations and blocked conclusions.
8. Record a decision or diligence request and export the accepted snapshot.
9. Revisit monitoring triggers; new evidence produces a new revision and marks prior conclusions stale.

## 6. Investor question catalogue

Every Q01–Q10 must always appear, with status Answered, Partial, Insufficient evidence, Disputed or Not applicable. A short history is a limitation, not permission to omit a question or invent an estimate. Detailed subquestions can adapt by sector/persona; stable IDs must remain available for traceability.

| ID | Core question and required subquestions | Assessment/evidence | Expected answer and missing-data behavior |
| --- | --- | --- | --- |
| Q01 | **What business am I buying?** A: customers/products and revenue model; B: segments/geographies; C: recurring/cyclical/project revenue; D: customer/supplier dependencies | Source-backed description, segment/revenue bridge and concentration; issuer disclosures plus independent industry evidence where available | Explain the economic engine and dependencies. Missing segment/customer data becomes a specific request, not diversified-business language. |
| Q02 | **Why can this company win?** A: pricing power; B: cost/distribution/technology advantages; C: competition and substitutes; D: durability of claimed moat | Competitive framework, margins/share evidence, retention/pricing if disclosed; distinguish management claims from corroboration | State which advantages are evidenced, claimed or unproven. No automated moat score from profitability alone. |
| Q03 | **How credible is growth?** A: volume/price/new-market drivers; B: accessible market; C: investment/capacity needs; D: execution and maturation | Driver forecasts, comparable benchmarks, coherent scenarios; regression only if an eligible sample exists | Show what must happen and what it costs. No full-year CAGR from incomparable stubs or causal growth claim from correlation. |
| Q04 | **Can I trust earnings and cash generation?** A: recurring earnings; B: PAT-to-CFO bridge; C: working-capital/accounting judgments; D: audit/restatement signals | Statements/notes, cash reconciliation, accrual and approved forensic screening | Explain identified drivers and alternative explanations. Missing ageing or total assets blocks the relevant conclusion/model. No fraud or accounting-integrity verdict from one score. |
| Q05 | **Does growth create value per share?** A: ROIC/reinvestment; B: cost of capital; C: dilution and future funding; D: capital-allocation track record | Average invested capital/NOPAT definitions, project/DCF scenarios, full share and earnings bridge | Separate growth, accounting accretion and economic value. If WACC/forecast inputs are absent, show ranges only from explicit assumptions or report unavailable. |
| Q06 | **Can shareholders trust management and control?** A: delivery history; B: incentives/ownership; C: RPT/conflicts; D: oversight and material disputes | Dated disclosures, shareholding, remuneration, governance documents and independent corroboration | Evidence-led strengths and concerns; unresolved issues remain diligence tasks. No integrity clearance or automatic adverse inference from absence. |
| Q07 | **Why this IPO, and who benefits?** A: fresh/OFS and sellers; B: funds reaching issuer; C: uses/timing; D: funding need if delayed | Reconciled source/use ledger, seller ownership bridge, fees and milestones | Explain growth/repayment/secondary liquidity and alignment without treating OFS as inherently adverse. Undisclosed allocations remain unallocated/unavailable. |
| Q08 | **Is the price justified?** A: diluted market cap/EV; B: justified peer set; C: absolute/relative range; D: implied expectations | Dated market inputs, normalized metrics, DCF/reverse DCF when eligible, scenario sensitivities | State what price assumes and valuation dependencies. No buy signal from P/E discount, no negative-P/E cheapness, no market cap without price/shares. |
| Q09 | **What could permanently impair capital?** A: business failure/disruption; B: governance/legal loss; C: liquidity/dilution; D: valuation compression | Material risk register, operating/cash/financing scenarios and reverse stress | Explain transmission mechanisms, downside bounds and mitigation limits. Never equate scenario frequencies or life stages with default probabilities. |
| Q10 | **How might returns be realized and monitored?** A: earnings/cash/dividends; B: entry/exit valuation; C: holding period and liquidity; D: catalysts and thesis breaks | Conditional return bridge, dated distributions, float/lock-ins when sourced, monitoring plan | Show return drivers, not a guaranteed target. Pre-listing trading volume is unavailable; proxies are labelled. No invented exit date or automatic lock-in rule. |

### Private/strategic extensions

PX01: What security and rights are being acquired? Capture actual preference, conversion, anti-dilution, information/board rights, transfer restrictions and contractual conditions. Missing legal documents block a terms conclusion. No special rights assumed for public IPO shares.

PX02: What additional capital or operating change is required? Model dated funding and owner-backed initiatives, dependencies, costs and feasibility. Separate management plans from investor assumptions.

PX03: What are the exit routes and realized return waterfall? Use actual security terms, cash-call/distribution dates, fees and dilution. Show MOIC and money-weighted IRR with limitations; do not multiply a forecast business value directly by an unadjusted ownership percentage.

PX04: What is the standalone value versus buyer-specific synergy? Model them separately, with integration costs, timing, dis-synergies and probability assumptions only if supplied. Synergy is not automatically available to public minority shareholders.

## 7. Answer and evidence contract

REQ-01 **Direct answer:** One or two company-specific sentences followed by conclusion status, period/as-of date and analysis revision. Match language to results; weak coverage cannot say “robust,” and missing data cannot imply “safe.”

REQ-02 **Common answer structure:** Observation → supporting facts/calculations → interpretation → counterevidence/alternative explanations → limitations/data gaps → conditional action → what changes the conclusion. Existing six-part rendering can be extended rather than replaced wholesale.

REQ-03 **Claim-level lineage:** Material claims carry evidence IDs. Numbers resolve to a source metric or formula/run. A broad phrase such as “DRHP Section V” is not sufficient for a specific value. Qualitative claims identify whether the source is management or independent evidence.

REQ-04 **Evidence categories:** Display Disclosed fact, Calculated result, Empirical comparison, Model estimate, User assumption or Analyst interpretation. Store supporting and contradicting links. “Source reviewed” is distinct from “independently corroborated.”

REQ-05 **External sources:** Maintain publisher/author, title/date/version, URL/DOI, pinpoint, supported proposition, jurisdiction/applicability, limitations and verification date. Practitioner citations justify analytical context; they do not validate the issuer. Missing full text is disclosed; no invented references, quotations or numerical effects.

REQ-06 **Sufficiency:** Use Supported, Partial, Insufficient or Conflicting evidence with reasons. Data completeness is a separate measure. No fabricated confidence percentage or statistical probability from field coverage.

REQ-07 **Deterministic core:** Generate calculations and core conclusions from accepted structured facts. Optional approved cloud explanation consumes a bounded evidence bundle and cannot introduce unsupported values/citations. Useful answers remain available without an LLM. Treat source/model instructions as untrusted content.

REQ-08 **Question dependency:** Every answer links required and optional metrics, methods, findings, data gaps and actions. A changed source, correction, peer vintage or scenario invalidates dependent conclusions. Prior accepted decisions remain historical and visibly stale, not silently rewritten.

REQ-09 **Completeness:** All ten families and eligible PX questions appear in export and on screen with their status. An unanswered question is explained, not hidden. Persona changes can reorder emphasis and terminology but cannot change facts, mathematical results or evidence states.

## 8. Company overview and source identity

REQ-10 Provide factual background: business description, incorporation, sector/subsector, products, revenue model, segments/geographies, promoters/ownership and material dependencies. Include financial/offer highlights only when supported. Claims of market leadership require attribution and date. Use a verified logo or a neutral identifier.

REQ-11 Version the filing package: issuer/deal/document IDs; draft/RHP/prospectus/amendments; publication and financial dates; document hash; currency/scale; statement basis; source-review status. Separate publication date, financial period and analysis date. Subsequent events must not leak into a historical investment assessment unless an explicit later-information view is chosen.

REQ-12 Uploaded unknown/scanned/invalid documents must not inherit exemplar values, exchange membership, an OFS status, stage or approval. If extraction is incomplete, show precise failure/missing states and a controlled manual-completion path. Null is not zero. Enforce validation at result/answer/export boundaries even while legacy adapters still contain placeholders.

## 9. Extracted attributes, CMIE comparison and coverage

REQ-13 Build the crosswalk from actual local licensed CMIE schemas/data dictionaries and current analytical dependencies. Never invent exact CMIE field names. Save the reference vintage/schema hash. Distinguish reference CMIE fields, compatible mappings, prospectus-only attributes and extra forward/diligence inputs.

REQ-14 Each attribute has a stable canonical key, definition, raw/normalized value, unit/scale, period/duration, consolidated/standalone/restatement basis, provenance, extraction method, correction history and dependent analyses. Mapping state: Exact, Conditional, Incompatible or No equivalent, with reason. Shared name or fiscal label alone does not prove equivalence.

REQ-15 Use orthogonal status axes rather than one overloaded badge: availability; extraction/normalization; reconciliation; source review; comparability. An extracted value can be normalized and reviewed simultaneously. At minimum distinguish not supplied, not found within searched scope, parse failed, truly undisclosed after review, disputed, stale and not applicable. Record pages searched; extraction limits must not become issuer nondisclosure.

REQ-16 Provide search/status/group filters, raw-to-normalized inspector, company comparison and downloadable accepted attribute inventory/crosswalk. Offer a coverage matrix with accessible detail rows. Show both populated and unavailable attributes, not only the seed fields.

REQ-17 Coverage counts operate on unique applicable attribute-period-basis records and explicitly state their scope/denominator. Derived values are not new independent disclosure evidence. Show data completeness and decision readiness separately. No percentile/score implies data quality without validation.

REQ-18 Keep a distinct prioritized missing-data register: gap ID/item, source state, affected period, why it matters, blocked questions/analyses, materiality, expected document, proposed owner/request, optional explicit assumption, resolution status and revision. Prioritize decision blockers over cosmetic omissions. Display material gaps near the thesis and export, not only in a diagnostic tab.

## 10. Analytical methods and use of the original platform

REQ-19 Produce an actual capability inventory across registered Econometrics Lab, Advanced Econometrics, Interaction Effects, Stata Studio, ML, Forecasting, Clustering, Transitions, Life Stage Dynamics, peer benchmarks, financing and scenarios. Inspect supported command registry/docs and model exports; do not advertise unsupported Stata commands. Navigation registration alone is not functional binding.

REQ-20 Each capability records decision question, engine/command/version, required inputs, data type, estimation population, applicability, readiness, validation state, access policy, adapter and tests. Keep permission denial distinct from missing inputs or an unsuitable method. Show a next step for every unavailable capability.

| Method family | Appropriate contribution | Required gate |
| --- | --- | --- |
| Accounting/ratio bridges | Earnings/cash/offer/dilution reconciliation | Complete definitions, compatible periods, finite inputs and denominator validity |
| Descriptive peers | Relative operating and valuation context | Justified cohort, self-exclusion, as-of data, basis alignment, firm/observation counts and small-cohort limitations |
| Driver forecasts/scenarios | Q03/Q05/Q08/Q09 | Coherent dated assumptions and operational/financial reconciliation; scenarios are conditional, not confidence intervals |
| DCF/reverse DCF | Value range and embedded expectations | Explicit cash flows, reinvestment, discount rate, terminal assumptions and share/EV bridge |
| Panel/interaction estimators | Research on financing/performance relationships | Valid multi-firm panel, adequate variation, specification and diagnostics; no issuer-specific causal verdict by default |
| Time series | Forecasting when histories support it | Actual date frequency/history, baseline comparison, validation and uncertainty; do not fit ARIMA to three annual points |
| Clustering/life-cycle/transitions | Descriptive peer/archetype context | Versioned features/scaling and validated mapping; no guaranteed future trajectory |
| ML | Cohort-based prediction if an approved task/model exists | Target/horizon, provenance, time/issuer separation, leakage/survivorship checks, out-of-sample metrics, baseline, calibration where probabilistic and drift limits |
| Forensic screening | Focused accounting diligence | Published version/inputs/eligibility; screening is not proof of fraud or integrity |
| Qualitative frameworks | Competitive position/governance/contract questions | Cited evidence, explicit judgments, alternatives and limitations; do not force an econometric label |

REQ-21 Each model result includes sample identifiers/filters, target, formula/specification, units, estimation date/cutoff, diagnostics, validation limitations and sensitivity. Report uncertainty where mathematically meaningful. Do not call scenario spread a statistical interval or SHAP a causal explanation. Minimum-sample rules must be method-specific and documented, not an arbitrary global constant.

REQ-22 Existing applicable engines must open/run with accepted company/source/peer/scenario context and return findings linked to questions. An unlisted deal has its own identity; never insert invented CMIE financial rows. Preserve the original full tool navigation/workflows; offer scoped capability access even if the Pre-IPO sidebar is currently narrower.

## 11. Financial depth and valuation safeguards

REQ-23 Preserve and deepen the eighteen dimensions specified previously: business/competition; historical performance; earnings quality; liquidity; working capital; debt/obligations; offer/ownership; proceeds/allocation; pro-forma accounts; financing alternatives; valuation; scenarios/reverse stress; governance; legal/contingent risk; sector economics; execution/external risk; life-cycle/peers; monitoring. Q01–Q10 synthesize these workpapers rather than create duplicate calculations.

REQ-24 Capital allocation must separate ROIC from ROE, marginal/project returns from historical returns, and accounting EPS accretion from economic value creation. Define NOPAT/invested capital and use consistent tax/lease treatment. State when cost of capital is assumed rather than observed.

REQ-25 Proceeds and dilution need actual seller/primary share movements, issuer expenses, allocations, retained cash, repayment eligibility, issue price and fully diluted counts. OFS is a secondary transfer, not primary cash or automatically new-share dilution. Show historical, pro-forma run-rate and realized-period results separately.

REQ-26 Valuation uses dated comparable business/financial definitions and an explicit EV-to-equity bridge, including cash restrictions, lease treatment and other claims where relevant. Use at least two suitable approaches when feasible; if only one is defensible, explain the limitation rather than manufacture a second. No unsupported discount or target-price precision. Never average incompatible valuation methods mechanically.

REQ-27 Driver-based bear/base/bull and reverse stress link operations, margins, working capital, capex, financing, tax and dilution. Show which operational change causes the first liquidity/coverage shortfall. Shock floating exposure rather than all debt by default. Model feasibility matters; unsupported covenants remain hypothetical thresholds.

REQ-28 Sector modules require real inputs: pharma product/market/regulatory/R&D exposure; infrastructure executable order book, retentions, guarantees and collection risk; platforms unit/contribution economics, incentives and cohorts; services client mix, utilization, attrition and contract dependency. Do not substitute GMV for revenue or order book for guaranteed cash. Unsupported KPIs become gaps.

REQ-29 Governance/accounting/legal conclusions use applicable, dated definitions and specialist review where necessary. Separate house thresholds, actual contracts and statutory requirements. Do not apply a current rule retrospectively or label a source-provenance chip regulatory approval.

## 12. Recommendations, actions and monitoring

REQ-30 Each recommendation references finding/question/evidence IDs and includes the proposed action, why now, preconditions, alternatives/trade-offs, estimated effect or “not estimable,” costs/constraints, proposed owner/timeframe, completion evidence and monitoring trigger. A deadline is labelled sourced or proposed. Do not fabricate precise savings or impact percentages.

REQ-31 Decision states: Continue diligence, Compare alternatives, Consider subject to conditions, Defer pending evidence, or Do not proceed under stated assumptions. These are analyst/user workflow states, not official investment/credit approval. Any actual decision is separately attributed to its authorized user. No automatic subscription recommendation from peer discount, stage, anchor participation or a composite score.

REQ-32 Actions support View source, Resolve data gap, Edit assumptions, Run/compare analysis, Record decision and Export diligence requests. Persist owner-scoped status Proposed/Needs information/Accepted/In progress/Complete/Deferred, rationale and history. Do not send external requests automatically.

REQ-33 Monitoring includes accepted metric definition, baseline/date, proposed or contractual trigger, cadence, evidence owner and response. Cover operating performance, cash conversion, allocation milestones, dilution, sourced lock-in/float events and thesis breaks. Missing listing/market data must not produce fabricated trading liquidity.

## 13. Minimal shared data contracts

Extend existing dataclasses/stores where practical; avoid unnecessary service layers. The following are logical contracts, not a mandate to introduce one class/file per row.

| Contract | Minimum fields |
| --- | --- |
| AnalysisContext | owner/access, issuer/deal ID, document revision, accepted data revision, as-of mode/date, transaction context, peer vintage, scenario/assumption revision, methodology version |
| MetricRecord | canonical attribute ID, value nullable, raw value, unit/scale, period/basis, status axes, provenance IDs, derivation/input IDs and review history |
| CrosswalkRecord | schema/vintage hash, actual CMIE field/definition, mapping state, transform/limitations and reference scope |
| EvidenceRecord | source type, publisher/document/hash, publication/effective date, pinpoint/excerpt, supported proposition, review state and owner access |
| Finding / Answer | IDs/question, context hash, conclusion status, observation/claims, metric/run/evidence IDs, interpretation, counterevidence, limitations, action IDs and stale state |
| MethodRun | method/version, input snapshot, cohort/specification, parameters, diagnostics, output/uncertainty, eligibility and validation state |
| Gap / Action / Decision | dependencies, priority, proposed owner, request/conditions, state/history, user attribution, completion evidence and monitoring |

Use canonical units internally and explicit display conversion. Do not permit NaN/infinity or untracked placeholders. A deterministic snapshot/context hash keys calculations and exports. Persona-specific presentation may reference that same snapshot; it must not fork source facts. Maintain compatibility adapters only where necessary and test their unavailable behavior.

## 14. UI component requirements and taste

Reuse the approved Pre-IPO token schema: canvas, surface, elevated, border, accent and text roles. Reconcile it with the latest application theme implementation. Correct known contrast defects rather than reproduce an unsafe historical token pairing. No parallel design system or hardcoded dark-only containers.

| Component | Required behavior |
| --- | --- |
| Company hero | Name/neutral logo, factual business sentence, sector/geography, filing and review state; compact offer composition and Review data action |
| Business snapshot | Business summary plus aligned fact column; sources accessible; no unsupported decorative KPIs |
| Filing timeline | Actual document versions and subsequent events; explicit selected as-of state |
| Thesis brief | Decision question, supporting findings, reservations, conditions and material gaps; no opaque green score |
| Question explorer | One section, ten expandable families, status and persona filters, cross-links to workpapers/evidence; preserve expanded/filter state across ordinary reruns |
| Answer panel | Direct answer, metric/chart where useful, evidence chips, interpretation, alternatives/limitations, action and thesis-change trigger |
| Coverage strip/matrix | Separate reviewed/extracted/derived/gap dimensions with stated denominator; clickable matrix and keyboard/table equivalent |
| Attribute grid | Search/group/status filters; Attribute, Value, Period, State, Source, Comparability columns; right-aligned values; extended details in inspector |
| Evidence inspector | Supported dialog/panel/expander with excerpt, raw-normalized bridge, review history and working authorized actions |
| Capability explorer | Plain-language questions grouped by purpose; applicability, readiness, validation and permission displayed distinctly; working run/explanation actions |
| Assumption form | Optional inputs with units, purpose, defaults labelled illustrative, explicit Apply; unapplied edits separate from active scenario |
| Gap/action register | Prioritized expandable rows, blocked decisions, owners and next steps; no wall of undifferentiated warnings |
| Scenario comparison | Consistent baseline/bear/bull units and dates, driver differences, constrained outputs and source notes; table alternative |

“Wow” comes from three genuine interactions: company → coherent sourced introduction; gap → affected question → resolution; recommendation → calculation → attribute → source. Optional subtle transitions may clarify changes; no fake live counters, decorative gauges, excessive gradients or hover-only evidence. Use tabular financial typography and whitespace; keep detailed prose expandable.

Accessibility acceptance: rendered normal-text contrast at least 4.5:1 and qualifying large text 3:1; status not color-only; keyboard/focus access; useful labels; practical 200% zoom/narrow-window checks; no focus-trapping inspector. Respect reduced motion. Existing global sidebar remains application navigation; local navigation is clearly scoped.

## 15. Security, persistence and operational behavior

REQ-34 Authenticate through approved account configuration. Separate persona from role. Enforce owner/access restrictions on document viewing, metrics, model runs, chat, requests and exports; do not rely on session state alone. Viewer capabilities follow existing policy, not a new blanket grant.

REQ-35 Accept uploaded bytes for normal users. Bound file/pages/OCR/time, handle cancellation and preserve useful partial evidence. Any operator path import must be allowlisted and canonicalized. Treat uploaded text and model output as data, not instructions. Escape untrusted content before HTML rendering; do not expose arbitrary file paths or secrets through evidence links.

REQ-36 Version accepted facts, edits, assumptions, answers and decisions privately. Cache by owner/context where private data is involved. Define retention/deletion and provider transmission. Public-source content does not make a private user's notes public. No local LLMs.

REQ-37 Company/source changes, profile switching, theme changes, save/load and expected Streamlit reruns must retain valid context or show explicit invalidation. Do not bind facts to whichever global CMIE company happens to be selected. Prevent background/pending results from one deal populating another.

Performance acceptance uses a declared document corpus and environment; record cold/warm timings, failure rates and model-call costs. Do not invent an arbitrary-PDF latency guarantee. Avoid full ingestion, model work and deck rendering on every persona/filter change; provide explicit run/process states. Large tables can paginate/filter without truncating downloadable accepted data.

## 16. Export and interoperability

REQ-38 UI, AI context, PPTX, research report and data export use one accepted snapshot. Include company/filing/as-of identity, question status/answers, evidence-linked investment thesis, valuation/scenario assumptions, material gaps, conditional actions and methodology appendix. Different personas may have different narrative emphasis but identical metrics/source identity.

REQ-39 Do not force a slide count that clips evidence. Use concise main slides and appendices/continuations. Remove stale hardcoded conclusions. Open/render real downloaded files; compare answer statuses, key numbers, caveats and action owners against the accepted screen snapshot. File validity alone is insufficient.

REQ-40 Integrate with existing financing/peer/scenario/Stata/board tools through supported APIs/adapters. Retain original pages and commands. Changes to `models/stata_engine.py` require the repository's command-document synchronization. No new dependency or wrapper without a demonstrated need.

## 17. Worked acceptance examples (synthetic, not issuer facts)

E1. **Cash conversion:** Revenue 1,000; EBITDA 200; CFO 80. Show 40% CFO/EBITDA. If the cash-flow bridge/ageing is absent, explain possible causes and block “collections are poor.” A 70% house threshold cannot prove unencumbered liquidity.

E2. **Dilution:** PAT 100 and 100 shares give EPS 1. Interest savings 80 with explicit illustrative 25% tax add 60 PAT. With 200 newly issued shares, post-issue EPS is 160/300 ≈ 0.533. Do not call this EPS accretion despite higher PAT. Units must be consistent.

E3. **Working-capital option:** Constant annual credit sales 3,650 over 365 days and a hypothetical 10-day DSO reduction imply 100 cash released before other effects. Show its assumption and feasibility limits; do not use this result when only total revenue is known or treat it as guaranteed free cash.

E4. **Peer median:** Multiples 10x/20x yield 15x. No eligible peers yields unavailable. A discount does not generate subscription approval. Distinguish issuer forecast earnings from peer trailing earnings.

E5. **Bad intake:** Invalid bytes or an unknown unreadable PDF produce no valid revenue, stage, valuation or approval; a clear failure/manual-review state and blocked questions are exported too.

E6. **Method ineligibility:** Three annual issuer observations cannot automatically run an issuer-specific panel regression or train an ML return predictor. A separately eligible peer panel may support a research comparison with its own documented limits.

E7. **Version change:** Correct a material debt/cash attribute. Dependent answers, recommendations and draft exports recompute or become stale. The prior user decision remains an attributed historical record.

E8. **Private rights:** An IPO ordinary-share analysis without a shareholder agreement cannot show a liquidation preference or guaranteed exit. A private-term scenario is available only after explicit documents/assumptions.

## 18. Acceptance and traceability matrix

All tests below are required unless explicitly not applicable with rationale. Targeted automated tests complement authenticated UI/export checks; no requirement is declared verified merely because a documentation checklist exists.

| Test | Requirement coverage | Acceptance |
| --- | --- | --- |
| AT01 | Q01–Q10, REQ-01/09 | All ten families render for each existing exemplar and unknown upload, with honest answer state |
| AT02 | REQ-02–07 | Material numbers/facts resolve to accepted evidence/calculation; generic section string cannot satisfy a pinpointed claim |
| AT03 | REQ-06/12/15 | Missing, zero, parse-failed, disputed and not-applicable fixtures remain distinct through UI and export |
| AT04 | REQ-08/37 | Source, deal, peer or scenario changes invalidate only affected results and never leak another issuer's context |
| AT05 | REQ-10/11 | Overview is first; filing-time and subsequent information are visibly separated |
| AT06 | REQ-13–17 | Crosswalk references real local fields/vintage; incompatible bases are flagged; coverage counts equal unique applicable records |
| AT07 | REQ-16/18 | Matrix/filter/detail/download agree; resolving a gap updates readiness and affected questions |
| AT08 | REQ-19–22 | Capability inventory reconciles to actual supported registry; representative ready/panel/missing/unsuitable/denied paths work |
| AT09 | REQ-21 | Research runs disclose cohort/specification, time cutoff and uncertainty; look-ahead/self-inclusion are rejected or explicit |
| AT10 | REQ-24/25 | Synthetic EPS/ROIC/proceeds bridges conserve values and never equate earnings growth with shareholder value |
| AT11 | REQ-26 | Correct even median/empty peers, loss multiples, diluted shares, EV bridge and dated comparability |
| AT12 | REQ-27/28 | Scenario values recalculate from drivers; fixed-rate debt unaffected by floating shock; sector-inapplicable metrics stay unavailable |
| AT13 | REQ-04/29 | A screening signal does not declare fraud/integrity; policy thresholds do not become contracts/law |
| AT14 | REQ-30–33 | Recommendations have evidence, conditions, alternatives, owners and triggers; no unsupported savings or approvals |
| AT15 | Personas / PX | Facts invariant across personas; public/private context does not invent rights or portfolio suitability |
| AT16 | UI contract | All three demonstration interactions work, including keyboard source inspection and back navigation |
| AT17 | REQ-34–37 | All four configured profiles show expected access/denial; two-owner separation; reauthentication/rerun persistence |
| AT18 | UI contract | Both themes, readable charts/tables/inspectors, status labels, narrow viewport and 200% zoom |
| AT19 | REQ-38/39 | Actual downloaded PPTX/report/data match same snapshot, material gaps, conclusion states and actions; inspect rendering |
| AT20 | REQ-35/36 | Malformed/oversized inputs, hostile document instructions and untrusted HTML do not change permissions or fabricate accepted facts |
| AT21 | REQ-40 | Existing listed-company, financing, original tools and board workflows pass appropriate regression checks |
| AT22 | REQ-07 | With optional model disabled/unavailable, deterministic supported answers and gaps remain usable |

Use all four exemplars for regression/sector coverage only after source verification. Add synthetic fixtures with no issuer identity, an OFS-only case, a primary issue, loss-making issuer, low/zero debt, restricted cash, conflicting periods, missing price and a private-security case. Avoid tests that merely bless old exemplar constants.

## 19. Delivery slices and release gates

| Slice | Scope | Exit evidence |
| --- | --- | --- |
| S0: Reconcile baseline | Finish active build; delta checklist; inherited P1 review findings and actual source packages | Verified/partial/missing matrix and no blocking trust defect in accepted results |
| S1: Foundation | Company overview, identity, attributes/CMIE crosswalk, null/status handling and gaps | AT03–07 plus owner/source tests |
| S2: Investor questions | Ten-question catalogue, shared answer/evidence contract, basic thesis and method links | AT01–02/04/13/22; every unsupported answer explicitly blocked |
| S3: Decision depth | Appropriate tool adapters, forecasts/valuation/scenarios, personas and conditional actions | AT08–15 and domain tests; unsupported advanced models stay labelled |
| S4: Experience/export | Final components, private extensions when data exists, monitoring and export parity | AT16–21, four profiles, both themes and inspected artifacts |

Release gates: source/identity accuracy; no fabricated values/claims; owner authorization; calculation correctness; ten-question coverage with explicit unknowns; complete material-gap visibility; screen/export agreement. Optional predictive models and missing externally supplied data may be deferred with visible limits. Required UI/lineage cannot be called complete by deferring it silently.

Implementation handoff includes actual branch/commit, requirement/test/evidence matrix, source-to-screen mapping, demonstration walkthroughs, source catalogue, attribute/tool inventories, changed files, test results, remaining gaps and merge prerequisites. No unsupported 10/10 score or deployment claim. Do not merge, push or deploy under this PRD task.

## 20. Research traceability and unresolved decisions

| Product area | Research IDs | Interpretation |
| --- | --- | --- |
| Investor questions/company overview | S01–S04, S19 | Question-led equity analysis; product structure is our synthesis |
| Connected commentary/evidence | S05, S13 | Link economics, facts and judgments; not a substitute for issuer verification |
| Forecast/valuation depth | S04, S06–S08 | Business-specific assumptions and financing trade-offs; no universal thresholds |
| Debt/liquidity continuity | S08–S09 | Retain financing strength within broader equity decisions |
| Private/strategic context | S10–S11 | Add rights/value-creation/exit only when supported by actual documents |
| Governance | S12 | Material disclosure/conflicts and shareholder treatment |
| Method eligibility | S14–S15 | Control statistical bias and avoid causal overclaiming |
| KPI applicability | S16 | Verify full applicable legal text before encoding rules |
| Accessible UI | S17–S18 | Contrast and non-color state communication |

Open implementation decisions: actual licensed CMIE reference scope; public/private document retention/provider terms; availability of dated peer prices; which existing engines pass required applicability tests; manual-review ownership and role policy; optional report format supported by the current stack. Resolve by inspection/configuration first. Missing external inputs should become explicit requests; they do not justify invented data or an unnecessary stop to independent work.

## Appendix A. Attribute groups to reconcile with the real CMIE schema

The following are canonical business concepts, **not assertions of exact CMIE field names or availability**. The implementation crosswalk must preserve the actual reference definition and mark absent/incompatible fields honestly.

| Group | Candidate canonical concepts | Questions most affected |
| --- | --- | --- |
| Identity/background | issuer/deal/document identity, incorporation, sector, business description, products, segments and geography | Q01–Q03/Q06 |
| Income statement | operations revenue, other income, cost categories, EBITDA bridge, depreciation, EBIT, finance cost, tax and attributable PAT | Q03–Q05/Q08 |
| Balance sheet | total/current assets and liabilities, equity, tangible/intangible assets, receivables, inventory, payables, contract assets and cash restrictions | Q04/Q05/Q09 |
| Cash flows | operating/investing/financing flows, interest/tax classification, capex, acquisitions, disposals and cash movement bridge | Q03–Q05/Q07/Q09 |
| Debt and obligations | drawn principal, rate/repricing, currency, maturity, leases, security, guarantees, covenants and committed drawable lines | Q05/Q07/Q09 |
| Offer and ownership | primary/secondary shares, price band, issuer expenses, allocations, sellers, pre/post diluted shares, ESOPs/conversions, promoter holdings and sourced restrictions | Q05–Q08/Q10 |
| Governance and assurance | related parties, audit opinion/restatements, remuneration, independence, litigation, licenses and material approvals | Q04/Q06/Q09 |
| Operating economics | volume/price/mix, customers/suppliers, retention/cohorts, utilization, market share and sector-specific KPIs | Q01–Q03/Q09 |
| Valuation and markets | dated peer price/shares, enterprise bridge components, comparable earnings/basis, float, dividends and supported market liquidity | Q08/Q10 |
| Forward assumptions | growth/margins, working capital, maintenance/growth capex, financing/tax, discount rate, terminal assumptions and minimum cash | Q03/Q05/Q08–Q10 |
| Private terms and monitoring | security rights, future calls/distributions, contractual exit constraints, initiative milestones, triggers and decision history | PX01–PX04/Q10 |

Maintain a dependency map from these concepts to calculations and answers. A short list of available seed fields must not be presented as the complete reference universe. If the full CMIE dictionary is unavailable, scope the crosswalk to the inspected local tables and say so prominently.
