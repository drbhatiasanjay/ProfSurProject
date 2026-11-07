# Incremental PRD: Pre-IPO decision depth and algorithm contracts

Version 1.0. Date: 7 November 2026. Status: **design specified; production implementation and empirical validation pending**.

## 1. Purpose, sequence and authority

Deepen the Pre-IPO investment decision by connecting its thesis, operating economics, funding, valuation, evidence and subsequent outcomes. This addendum turns the proposed next enhancements into executable method contracts. It does not replace the existing ten-question/forty-subquestion investor PRD, repeat the original build or authorize deployment.

Finish Antigravity's active work and the applicable correctness remediations first. At the next checkpoint, map this document against the completed implementation: verified, partial, missing, blocked or not applicable. Implement only the remaining delta. Do not infer completion from names such as “evidence engine,” “rigorous ROIC” or “institutional grade.”

Reference documents in the current Codex worktree:
- [base equity/investor-question PRD](PRE_IPO_INCREMENTAL_EQUITY_QUESTIONS_PRD_2026-11-07.md)
- [current code review](../reviews/PRE_IPO_CODE_REVIEW_5687478_2026-11-07.md)
- [adversarial design assessment: DG01–DG28](../reviews/PRE_IPO_DECISION_DEPTH_RED_TEAM_2026-11-07.md)
- [earlier evidence and UI research](../research/PRE_IPO_EQUITY_DECISION_RESEARCH_2026-11-07.md)

Work exclusively in ProfSurProject. Read current project instructions, inspect Git/worktree state and preserve unrelated changes. New documents here may be uncommitted and absent from another checkout. No merge, push, deployment, external messaging, investment execution or manuscript changes are authorized by this PRD.

## 2. Outcomes and boundaries

The product must explain:

1. What must be true for the investment to work?
2. Which evidence supports or contradicts those assumptions?
3. How do operating changes affect cash, financing, ownership and investor value?
4. Which missing fact could change the decision?
5. What alternatives, actions and monitoring follow?

The same facts/calculations serve all personas; only emphasis changes. Keep access role, presentation persona, actual security/transaction context and optional decision policy separate. Wealth labels do not establish sophistication, legal rights or suitability.

This is not a requirement to invent issuer forecasts, calibrated success/default probabilities, a management-honesty rating, a universal IPO score or an automated portfolio recommendation. A method can correctly return a bound, ambiguity, unavailable input or failed numerical solve. Statistical, accounting, legal and market-data eligibility remain explicit gates.

All examples below are synthetic and explanatory. Eighteen arithmetic/state checks were run in `scratch/pre_ipo_decision_logic_review/validate_method_examples.py`; they do not establish empirical validity or constitute production engines.

## 3. Shared analytical backbone

Use one versioned dependency graph:

```mermaid
flowchart LR
  S[Source and availability] --> M[Accepted metric and definition]
  M --> R[Eligible method run]
  R --> F[Finding and limitation]
  F --> T[Thesis proposition]
  T --> D[Conditional decision]
  D --> A[Action or diligence request]
  A --> O[Monitoring observation]
  O --> F
```

The displayed graph can contain feedback over time, but a single computational snapshot must have an acyclic dependency order. Feedback creates a new version. Financial circularity must be handled by a declared solver or timing convention, not an accidental dependency cycle.

Shared context contains issuer/deal/security, owner/access, accepted documents/metrics, public-as-of versus actual-decision replay mode, assumption/scenario/policy versions, peer vintage, method version and time basis. It produces a stable context hash used by all findings and exports. No calculation can silently fetch a different currently selected global company.

Each method run records inputs and units, source lineage, gates, formula/specification, assumptions, numerical settings, result, residuals/diagnostics, uncertainty type, output state and invalidation dependencies. Financial output states include Computed under stated assumptions, Approximate, Insufficient evidence, Disputed, Unbracketed, Infeasible within stated domain, Ambiguous, Unsupported and Failed. Names may be adapted to existing enums, but semantics must remain distinguishable.

Implement these logical contracts by extending validated existing functions/stores where practical. Do not create a thin wrapper or new microservice per algorithm. No implementation may present a conditional model output as an observed fact.

## 4. ALG01 — Temporal evidence, dependence and semantic conflicts

**Risk coverage:** DG01–DG04, DG25, DG28. **Inputs:** documents, raw/normalized metric records, semantic definitions, origin relationships and temporal/access metadata. **Outputs:** eligible evidence set, compatible bridges, unresolved conflicts and invalidation list.

DD-01 Store economic period, publication/public-availability time or interval, actual user access where known, ingestion time, supersession/withdrawal and revision identifiers separately. Historical public replay includes a source only when its historical public availability is established before the cutoff. A document ingested today can be used in that replay if authentic historical availability is established. Actual internal decision-audit replay uses the recorded decision-maker information set; do not retroactively claim access. Uncertain dates remain intervals or unknown.

DD-02 Build an evidence-origin graph using reproduces, derives-from, supersedes and assurance relationships. Ten copies of one issuer assertion remain one origin family. Grouping is not proof that other families are independent. Store assurance type separately; an auditor opinion does not certify every claim in a presentation. Never convert source counts or review badges into probability.

Conflict algorithm:
1. Filter by replay/access eligibility.
2. Canonicalize currency/scale only with a traceable conversion; preserve raw records.
3. Compare semantic keys: entity scope, metric definition, period/duration, accounting/consolidation basis, gross/net and lease treatment, currency/price basis.
4. Different concepts yield “not directly comparable” or an explicit bridge, not an averaged value.
5. For same-key numbers, flag differences exceeding `max(abs_tolerance, relative_tolerance × max(abs(a), abs(b)))`; tolerances are metric/unit-specific and versioned. Zero does not eliminate the absolute tolerance.
6. Keep material unresolved conflicts disputed. An authorized reviewer can accept one interpretation with evidence/rationale, preserving alternatives and affected outputs.

Do not make “latest,” “audited” or majority vote an unconditional precedence rule. A later audited restatement may be inappropriate to an earlier information set. Example EX01/02/17.

## 5. ALG02 — Falsifiable thesis and conditional answer logic

**Risk coverage:** DG05/06/25/28. **Inputs:** ten-question findings, load-bearing assumptions, operating mechanisms and evidence graph. **Outputs:** supported/partial/disputed thesis propositions, counter-thesis hypotheses and decision conditions.

DD-03 Represent each proposition as claim, economic mechanism, observable implication, evidence, counterevidence, competing explanation, horizon and review/falsification criterion. Identify whether it is load-bearing for valuation or supporting context. A margin is not by itself evidence of a moat. A hypothetical customer loss stays a hypothesis in bull/bear views and exports.

DD-04 Use dependency expressions rather than a completeness score: required-all inputs must all pass; alternative evidence paths must be explicitly documented. Unknown is not False or favorable. If one required material input is disputed/unavailable, qualify or block that proposition; unaffected propositions can proceed. Predetermined evidence sufficiency rules and permitted reviewer overrides must be versioned and explained.

For decision policy `P`, feasible actions `A` and admitted scenarios `S`, evaluate consequences without adding unsupported probabilities. Classify a proposed action as constraint-infeasible, conditional, evidence-blocked or robust within the tested domain. “Robust” describes that domain/policy only. Do not manufacture equally strong positive and negative arguments. A falsification rule is a review criterion, not automatically a causal experiment.

LLM use is optional wording over an accepted evidence bundle. It cannot change sufficiency, fabricate citations or turn a hypothesis into a disclosure. Preserve deterministic useful answers when it is disabled.

## 6. ALG03 — Sector operating drivers, cohorts and reinvestment

**Risk coverage:** DG07/08/14/24. **Inputs:** segment volumes/prices, cost structure, capacity, cohorts, capex/capital efficiency and definitions. **Outputs:** reconciled revenue, operating costs, capital needs and driver scenarios.

DD-05 Select a sector-appropriate driver tree and reconcile it to statements. Examples: segment revenue = delivered quantity × net realized price; platform revenue = appropriately defined transaction volume × monetization, with principal/agent treatment; services revenue = compatible billable capacity × utilization × price. Gross merchandise value is not automatically recognized revenue. Capacity, market share, price-volume trade-offs and commissioning dates constrain forecasts. Do not multiply independent optimistic assumptions that cannot coexist.

DD-06 Cohort/unit-economics KPIs retain population, cohort entry, activity definition, observation/maturity window, numerator/denominator, exclusions, customer exits and cost-allocation policy. Separate new/acquired customers from existing cohorts; reconcile incentives and variable/central costs. Use multiple clearly labelled contribution levels when necessary. Never compare different contribution definitions as the same margin.

For a compatible existing-revenue cohort:
`NRR = (opening cohort revenue + expansion − contraction − churn) / opening cohort revenue`.
New-customer revenue is excluded. Opening 100, expansion 20, contraction 5 and churn 10 gives 105%, even if new customers add 60 (EX03). This formula is inapplicable where the revenue/cohort contract differs; do not force a SaaS metric onto project businesses.

Terminal operating growth must fund its incremental capital. Under an explicit stable-growth/capital-efficiency model with eligible nonnegative growth and positive marginal ROIC, `growth reinvestment rate = g / marginal_ROIC` and `next_FCFF = next_NOPAT × (1 − growth_reinvestment_rate)`, after maintenance needs are consistently reconciled. Validate finite inputs and sustainable funding/capital assumptions; a positive ratio alone does not establish feasibility. This is not a rule for arbitrary FCF CAGR, negative growth/disinvestment or discrete capacity steps. Do not silently clamp an economically inconsistent rate. EX08 checks NOPAT 100, g 5%, marginal ROIC 10% → growth reinvestment 50, FCFF 50.

## 7. ALG04 — Dated cash, taxes, facilities and financing feasibility

**Risk coverage:** DG09–DG11/15/24. **Inputs:** operating-driver model, cash timing, tax policy, unrestricted/restricted balances, facilities and dated obligations. **Outputs:** cash/debt paths, interim gaps and financing-condition branches.

DD-07 Use a material event/calendar schedule rather than annual ending cash as proof of adequacy. Minimum resolution follows payment/receipt concentration; monthly data can still hide a day-one shortfall. With only annual inputs, state that interim adequacy is unassessed. Opening 50, early payment 100 and later receipt 100 creates −50 interim cash despite ending 50 (EX04).

DD-08 Funding follows a declared policy. Draws require documented limit, availability, currency, maturity and conditions precedent; uncommitted financing is a separate conditional branch. Do not balance every gap automatically with debt/equity. Respect restrictions on cash use and dividends. Report a model funding failure, not automatically legal insolvency or actual contractual default.

Under a specifically defined pre-debt-service operating-cash convention:

```
cash_close[t] = cash_open[t] + operating_cash_pre_debt_service[t]
                - cash_capex[t] - acquisitions[t] + disposal_receipts[t]
                - cash_interest[t] - principal[t] - distributions[t]
                + eligible_draws[t] + net_primary_equity[t]
```

Taxes/interest already included in the operating input must be removed from this bridge or the corresponding separate deduction, never counted twice. Lease cash flows, PIK interest, FX remeasurement and noncash debt changes have explicit separate ledgers. Reconcile closing debt and cash; do not infer unrestricted cash from its accounting caption.

Interest timing must specify opening/closing/average or event balances. For a coupled average-debt/draw calculation, use a validated fixed-point/bracketed solution with residual/iteration limits or change to an explicit dated convention. Nonconvergence remains unsolved.

Tax inputs distinguish book expense, current cash payment, deferred tax, loss carryforwards, interest deductibility and recognized refunds. A loss or statutory tax rate alone does not create a cash receipt. Apply dated, verified jurisdiction policy; otherwise request inputs or run explicitly hypothetical assumptions. EX05 checks a consistent after-interest CFO → FCFF bridge, not a universal shortcut.

## 8. ALG05 — Primary proceeds, future funding and the share ledger

**Risk coverage:** DG12/13/15/26. **Inputs:** financing need, issue dates, net/gross fees, price convention, security classes and corporate actions. **Outputs:** sources/uses, cash/debt changes, share counts, ownership and funding alternatives.

DD-09 Record every event as a balanced source/use and share-class movement. Distinguish primary proceeds, secondary transfers, debt repayment, retained cash, fees, option exercise and conversion. Total equity value, value of an existing holder and value per share are different outputs. Do not count proceeds as both retained cash and repaid debt.

DD-10 For a supported fixed-price ordinary-share raise with proportional fee `f`, fixed expense `F`, net need `N` and price `p`:
`gross = (N + F)/(1−f)`, `new_shares = gross/p`, `old_ownership = old_shares/(old_shares+new_shares)`.
Require `0 ≤ f < 1`, `p > 0`, nonnegative expenses and compatible currency/share units. Instrument-specific terms can invalidate the simple formula.

If price depends on post-financing valuation, identify the coupled variables and economic pricing convention; solve them with feasibility/residual checks or expose the price as an explicit assumption. A guessed dilution haircut is not a solved financing case. Funding failure is an alternative outcome, not repaired by an arbitrary low issuance price.

EX06: 100 old shares, net need 100, fee 5%, price 8 → 105.263 gross, 13.158 new shares, old ownership ≈88.372%. EX07: EV 1,000, debt 200, cash zero, net primary 100 fully repaying debt → post cash zero, debt 100, aggregate equity 900. Per-existing-share consequences still need the issuance ledger.

## 9. ALG06 — Valuation identity and reverse underwriting

**Risk coverage:** DG10/12–DG16/24/25. **Inputs:** eligible cash-flow claim, driver/funding scenarios, terminal state, discount convention, price/share/security bridge. **Outputs:** valuation range or implied expectation frontier, solver diagnostics and blocked assumptions.

DD-11 Match FCFF with an appropriate WACC framework and equity cash flows with cost of equity. Match currency, nominal/real, pre/post-tax, horizon, claim seniority and lease conventions. Do not automatically call CFO-minus-capex FCFF. Under a compatible convention, FCFE can be bridged from FCFF by cash interest, realized interest tax benefit and net borrowing; disclose the exact accounting bridge. Banks/insurers and complex claims need separately eligible methods.

Operating EV must bridge to total equity through appropriate debt, excess/unrestricted cash, non-operating assets and other claims exactly once, at a consistent transaction/deployment date. Use documented market capital weights and capital policy, or label supplied illustrative assumptions; do not invent EBIT from capex, market cap from a multiple of book equity, or a tax shield from losses. Changing leverage can require period-specific rates or a justified alternative such as APV; do not force every case into a constant WACC.

DD-12 A price does not uniquely determine growth, margin, reinvestment and discount rate together. Offer (a) a one-variable solve with the remaining assumptions fixed/visible or (b) a feasible surface/frontier. Separate operating-growth and FCF-growth conventions. A negative base FCF cannot support a simple positive-CAGR extrapolation; require an explicit turnaround path.

Root protocol:
1. Validate finite inputs, economic domain and terminal conditions, including WACC greater than terminal growth where a perpetuity requires it. Reject rather than silently alter assumptions.
2. Define `f(x)=model_value(x)−target_value`, target scale and value-residual tolerance.
3. Establish continuity/eligibility of the selected interval; inspect endpoints and monotonicity only where actually justified.
4. Use an existing supported bracketed solver when the preconditions hold. Check numerical convergence and `abs(f(root))/max(abs(target), currency_scale)`.
5. Report unbracketed, domain-infeasible, nonconverged or ambiguous outcomes explicitly. Search-boundary values are not answers.
6. A bracket identifies an interval solution, not global uniqueness. Same-sign endpoints do not prove no root; discrete financing changes can create discontinuities or multiple feasible regions.

EX09/10 verify a simple root and a same-sign-endpoint function with two interior roots. Terminal value share, discount/growth sensitivities and structural method differences must be visible. Do not label an implied growth hurdle achievable/sector-normal without actual comparable evidence.

## 10. ALG07 — Coherent reverse stress and failure frontiers

**Risk coverage:** DG07/09/11/16/17/24. **Inputs:** accepted operating/cash/funding model, permitted shocks, constraints and a defined adverse condition. **Outputs:** breach paths/frontier, assumptions, numerical status and mitigation limits.

DD-13 Define the adverse outcome first: minimum-cash shortfall by time, contractual ratio crossing under its real definition, inability to fund a specified commitment, or a user valuation-policy threshold. Keep actual obligations, house thresholds and modeled investment conclusions distinct.

DD-14 Search the economically admissible shock set. One optional severity formulation is `min Σ w_j × (z_j/s_j)^2` subject to a selected failure condition and all capacity/timing/financing constraints. Positive scales and visible weights are mandatory. Changing units with scales converted consistently must not change results. This distance is a policy construction, **not probability or unique plausibility**.

For multiple constraints, solve/report each relevant breach frontier or a documented union; do not require all failure conditions simultaneously unless that is the stated question. Multiple local solutions or discrete refinancing events require alternative paths/grid checks and diagnostic disclosure. No validated global search → no global-minimum claim.

Likelihood/Mahalanobis approaches require a separately justified joint distribution/covariance and diagnostics. Handle zero scales, singular matrices, regime dependence and tail correlation. Without those data, show coherent bounded scenarios. Stress-case counts are not default probabilities. Record both unmitigated and feasible management-response cases; a mitigation cannot occur before its decision/implementation lead time.

## 11. ALG08 — Diligence priority, information value and waiting

**Risk coverage:** DG04/18/24/27. **Inputs:** gaps, affected methods/actions, policy thresholds, coherent scenario bounds, information access/cost/timing. **Outputs:** prioritized requests and conditional decision sensitivity; optional explicitly modeled VOI.

DD-15 Default to non-probabilistic classification:
1. Mandatory evidence/authorization or feasibility blocker.
2. Decision reversal/ordering change possible within stated admissible bounds.
3. Material magnitude change without demonstrated reversal.
4. Supporting information.
5. Impact not estimable because uncertainty is unbounded/structural.

For each gap, traverse real dependencies, vary it within justified joint scenarios and evaluate the specified action set/policy. Hold other assumptions fixed only when economically legitimate. Report bounds, model structural limits, request owner, access, time-to-decision, effort and whether evidence can arrive in time as separate fields. Do not hide them in an invented weighted score. Impact-not-estimable is not low priority. EX13 uses 90–130 versus 118–122 around policy hurdle 110; no reversal probability follows.

DD-16 Optional VOI is gated on explicit actions `a`, state/parameter model `θ`, probabilities, utility/payoff `U`, feasible information signal `Y` and a consistent decision time:

```
EVPI = Eθ[max_a U(a,θ)] − max_a Eθ[U(a,θ)]
EVSI = EY[max_a Eθ[U(a,θ)|Y]] − max_a Eθ[U(a,θ)]
net_information_value = EVSI − acquisition_cost − modeled_delay_cost
```

Utility units are not automatically rupees. No priors/information model → no expected monetary VOI. Under the same coherent free-information decision model, `0 ≤ EVSI ≤ EVPI`; violations indicate specification/numerical error. Costs can make net value negative. EX12 uses explicitly supplied toy probabilities and an 80%-accurate signal, not an issuer calibration.

“Invest now,” “wait,” “request data” and “decline” are distinct dated actions. Waiting may change price, allocation access, deadlines and information. Without a justified timing/transition model, show those dependencies and do not call waiting a free option or compute an unsupported optimal entry time.

## 12. ALG09 — Comparable opportunities and partial ranking

**Risk coverage:** DG04/15/19/24/25/27. **Inputs:** accepted per-opportunity snapshots and a declared comparison policy. **Outputs:** comparable/trade-off/dominance/insufficient/incomparable states, scenario rank stability and diligence differences.

DD-17 Require common or explicitly bridged date, currency, horizon, security/rights, fees, distributions, valuation basis, accessible information and liquidity constraints. Sector metrics can differ; do not rank a loss-making platform and manufacturer by an invalid P/E comparison. Annualizing a conditional promised return does not verify it (EX14).

DD-18 Compare paired coherent scenarios under common shocks where defensible. Use Pareto/partial ordering on explicitly oriented criteria and constraints. Robust interval bounds may establish sufficient dominance, but overlapping marginal ranges do not prove no dominance. State which alternatives were examined; the frontier is not the whole market.

Missing risk cannot become zero or enhance rank. Show trade-offs and unknowns. If a user requests a weighted ranking, expose weights, scales, excluded criteria and rank sensitivity; no claim that the score is calibrated probability or universal quality. Do not average dependent model outputs and call the result independent confirmation. Investor-specific portfolio optimization requires separately supplied portfolio data/objective and is outside this base increment.

## 13. ALG10 — Immutable commitments and forecast accountability

**Risk coverage:** DG01/03/20/24. **Inputs:** original management statements/guidance, revisions and comparable actuals. **Outputs:** commitment ledger, delivery states and appropriately normalized forecast errors.

DD-19 Record source excerpt, speaker, publication/availability, metric definition/scope, direction, point/range target, deadline, conditions and original interpretation before observing outcomes. Distinguish aspiration, guidance, conditional commitment and actual contractual obligation. Revisions link to, not overwrite, the original. Declare the collection policy and unobserved/omitted commitments to limit cherry-picking.

DD-20 Evaluate only matured, measurable and comparable commitments. States include Not measurable, Not due, Awaiting comparable actual, Met, Partially met, Missed, Withdrawn and Not comparable. Define whether exceeding a range is favorable, unfavorable or outside guidance; higher is not always better. M&A, FX and accounting changes need bridges. Keep original-reporting and later-restated evaluations separate.

For eligible numerical forecasts, compute signed error and absolute error in actual units; use a declared positive material scale for normalized errors. Avoid MAPE at zero/near-zero values and inappropriate pooled comparisons across units. Compare against a simple predeclared baseline when judging forecasting usefulness. Report denominators and uncertainty with sparse observations; no management-integrity or honesty score. A forecast miss can reflect a genuine external shock or changed scope.

## 14. ALG11 — Revision-aware monitoring and action states

**Risk coverage:** DG01/20/23/28. **Inputs:** accepted triggers, metric observations, due/availability calendars, revision events and owners. **Outputs:** deduplicated evidence-linked alerts, review tasks and recovery states.

DD-21 Each trigger defines metric/basis, baseline, threshold provenance, observation period, reporting lag, maturity/acceptance criteria, immediate-event flag, optional persistence/recovery rules and owner. Missing results produce Pending/Overdue data, never zero revenue or automatic performance failure. Restatements are revision events, not new economic shocks today (EX18).

DD-22 Transition through Data pending/overdue, Disputed, Approaching, Crossed, Review required, Confirmed thesis change and Recovered as appropriate. Human decision attribution is distinct from a detected condition. Hysteresis/persistence is optional, justified noise control, never a reason to suppress an immediate contractual/legal event. Deduplicate by trigger/version/observation period; repeated imports must not create duplicate alerts/actions.

Persist decisions and action history. New evidence marks dependent answers stale until reviewed/recomputed. This product monitoring workflow does not authorize scheduling external automations or sending messages under this PRD.

## 15. ALG12 — Investor cash returns, attribution and ambiguous IRR

**Risk coverage:** DG12/13/15/21/22/26. **Inputs:** dated investor contributions/distributions, ownership/security ledger, valuations and corporate actions. **Outputs:** reconciled currency P&L, conditional returns, attribution convention and IRR diagnostics.

DD-23 Separate issuer performance from investor cash realization. Use actual/assumed dates, fees, tax scope, dividends, dilution and terminal proceeds after senior claims. State MOIC numerator/denominator and whether residual unrealized value is included; MOIC ignores timing. Do not use headline EV as investor exit proceeds.

For a limited positive-EPS, no-distribution price identity `P=EPS×M`, exact two-factor midpoint attribution is:

```
earnings_component = (EPS1−EPS0) × (M0+M1)/2
multiple_component = (M1−M0) × (EPS0+EPS1)/2
sum = P1−P0
```

This allocates the interaction symmetrically; it is not causality or a complete total-shareholder-return decomposition. A sequential waterfall is also allowed if order and residual/interaction are disclosed. EPS already includes share-count effects; do not add a second independent dilution penalty. Losses/near-zero EPS make P/E attribution inappropriate. For additional factors use a documented reconciliation convention; do not promise causal Shapley attribution.

DD-24 XIRR/IRR uses an explicit day-count convention, date aggregation, supported numerical domain, finite inputs and residual/convergence checks. Require meaningful contribution/distribution structure. Multiple cash-flow sign changes trigger ambiguity diagnostics, NPV profile and potentially multiple roots; a grid search finding one root does not prove uniqueness or exhaust all roots. Return Non-unique or uniqueness unverified when warranted. Handle total loss, all-negative/all-positive, zero elapsed time and unknown exit date honestly. EX15/16 verify price interaction and IRRs 10%/20% for annual −100,+230,−132.

## 16. ALG13 — Documented private-security proceeds waterfall

**Risk coverage:** DG12/13/15/22/26. **Inputs:** actual dated security documents, class quantities, senior claims, conversion/election rules, caps and exit/distribution scenario. **Outputs:** class/investor proceeds or unsupported legal-term state.

DD-25 First reconcile enterprise/asset sale value to distributable proceeds after actual senior claims and costs, then apply documented priorities/participation/conversion/consent rules. Scope ordinary public equity separately. Do not infer special rights from a persona or company name. Unknown shareholder agreements block definitive waterfalls.

DD-26 For a small explicitly supported set of conversion elections, enumerate only legally feasible joint configurations, compute all classes together and enforce proceeds conservation, nonnegative distributions, contractual caps and valid election/consent rules. Do not independently maximize every class if the combined result is infeasible. If terms imply strategic/equilibrium choices outside the supported model, report ambiguity or specialist review instead of selecting an arbitrary favorable result. No guaranteed exit from a hypothetical waterfall.

## 17. ALG14 — Uncertainty, robustness and method governance

**Risk coverage:** DG06/14–DG19/24/25/28. **Inputs:** model family, assumption provenance, scenario bounds/distributions, validation data and declared policy. **Outputs:** robustness limits, validation state, structural sensitivity and answer eligibility.

DD-27 Distinguish scenario uncertainty, parameter-estimation uncertainty, measurement/source uncertainty and model-structure uncertainty. Do not label bear/base/bull spread a confidence interval. Monte Carlo requires justified marginal/joint distributions, dependence/tail/regime assumptions and validation; otherwise run bounded coherent scenarios without probability language. Historical peer correlations or analyst confidence badges do not automatically supply these distributions.

DD-28 Test alternative legitimate accounting bridges, operating structures, discount conventions and financing policies. Show whether conclusions change and which assumptions are load-bearing. Models sharing inputs or source claims are dependent corroboration, not independent validation. Use point-in-time, out-of-time and issuer-separated evaluation where the prediction task requires it; select method-specific diagnostics/sample rules and compare with predeclared simple baselines. No synthetic-example pass can establish predictive calibration.

Every released method has version/owner, supported input domain, reference tests, limitations, change review and output-status contract. A material method revision invalidates dependent current results but preserves historical decisions. A textual claim must pass its dependencies before appearing on screen, in AI explanation or export.

## 18. UI and interaction additions

Reuse approved tokens/components and the original company → questions → workpapers → evidence → actions flow. No new competing sidebar or decorative analytics score.

| Component | Functional contract |
| --- | --- |
| Thesis challenge board | Load-bearing propositions, support/counterevidence, hypotheses and review triggers; evidence strength can be asymmetric |
| Evidence-conflict inspector | Semantic definitions, timing, normalization/bridge, origin family, reviewer resolution and dependent conclusions |
| Driver-to-value workpaper | Operating input → statement/cash/funding → ownership → valuation trace; unavailable links remain explicit |
| Funding runway timeline | Material cash events, minimum cash, conditional facilities, first shortfall and funding alternatives; no annual-solvency illusion |
| Reverse-underwriting surface | Fixed assumptions, solved variable/frontier, admissible domain, residual and unsolved/ambiguous states |
| Diligence impact queue | Blockers, reversal-sensitive gaps, bounds, evidence access/cost/timing and precise request; no invented monetary value |
| Opportunity comparison | Common context, trade-offs, unknown criteria, scenario rank changes and rights/liquidity differences |
| Commitment and monitoring ledger | Original target, revisions, maturity, comparable outcome, alerts and review history |
| Return bridge | Investor cash ledger, attribution convention, interactions and ambiguous return metrics |

All panels must distinguish disclosed/calculated/assumed/interpreted values and material limitations. Use text plus color, keyboard-accessible evidence controls and readable light/dark themes. Do not add exact-looking values when only bounds are justified. Explain what can be done next in every unsolved/missing state.

Export one immutable accepted context with answer states, formulas/assumptions, materially conflicting evidence, solver limits, private-term scope and actions. Do not recalculate from new defaults in the deck. Changes made during export must not mix snapshots; fail/retry or finish the explicitly selected immutable version.

## 19. Data, runtime and release controls

Extend existing source/metric/method/finding/decision contracts with origin-family edges, availability intervals/replay mode, typed cash-flow claims, timed ledgers, security classes, numerical diagnostics, commitment versions and observation maturity. Maintain a minimal schema; logical contracts do not require one new wrapper/file each.

Owner authorization applies to private sources, notes, scenarios, requests, model runs, comparisons and exports. Persona switching cannot change access or financial assumptions. Escape untrusted text. Bound document/model/scenario workloads; use cancellation and idempotent jobs keyed by owner/context/method. An old background result must not populate a new company. Do not silently truncate PDF bytes or rerun extraction for presentation changes.

Performance budgets must be measured on a declared corpus/environment. No arbitrary-PDF SLA or prediction quality is specified without evidence. Validate the ordinary fixed-input deterministic path before introducing stochastic models, optimization or complex securities.

## 20. Acceptance scenarios

| Test | Coverage | Required result |
| --- | --- | --- |
| DT01 | ALG01 / DG01 | Later restatement excluded from earlier replay; legitimate historical public availability distinct from current ingestion |
| DT02 | ALG01 / DG02 | Ten dependent citations do not improve independent support; assurance type remains separate |
| DT03 | ALG01 / DG03 | Borrowings/leases bridge works; same-key conflicting values stay disputed; tolerances respect units |
| DT04 | ALG01/02 | AND/OR dependencies block only affected claims; unknown never becomes favorable |
| DT05 | ALG02 / DG05/06 | Moat and counterclaims remain hypotheses without evidence; triggers are predeclared, not called causal proof |
| DT06 | ALG03 / DG07 | Growth beyond capacity requires explicit capex/funding or is infeasible |
| DT07 | ALG03 / DG08 | NRR example is 105%; new customers/churn exclusion and contribution-cost changes cannot silently alter definitions |
| DT08 | ALG04 / DG09 | Positive ending cash with early deficit displays the actual interim shortfall |
| DT09 | ALG04/06 / DG10 | Cash-interest/tax classification reconciles; CFO-minus-capex is not automatically FCFF |
| DT10 | ALG04 | Losses do not automatically create cash tax refunds; verified tax policy governs any benefit |
| DT11 | ALG04 / DG11 | Uncommitted/conditional lines do not automatically fill a cash deficit; restrictions and lead times respected |
| DT12 | ALG05 / DG12 | Fees and price drive correct new shares; circular pricing either converges with residual or stays unsolved |
| DT13 | ALG05/06 / DG13 | Primary proceeds used for repayment are not retained as extra cash; pre/post and per-holder values reconcile |
| DT14 | ALG13 / DG26 | Joint class distributions conserve proceeds and obey terms; absent terms block definitive outputs |
| DT15 | ALG03/06 / DG14 | Terminal growth funds reinvestment under the declared model; incompatible growth/returns are not silently clamped |
| DT16 | ALG06 / DG15 | Incompatible claim/rate/currency/tax/security model rejected; financial-sector exception visible |
| DT17 | ALG06 / DG16 | Known root meets residual; boundary and same-sign-endpoint cases return correct ambiguity/unbracketed states |
| DT18 | ALG07 / DG17 | Scale/unit conversion leaves policy-distance result consistent; invalid scales/dependence and multiple paths are explicit |
| DT19 | ALG07/14 / DG24 | Scenario counts/distances do not become probabilities; no most-likely claim without a supported distribution |
| DT20 | ALG08 / DG04/18 | Range around a specified hurdle is reversal-sensitive; unbounded impact is not estimable, not low risk |
| DT21 | ALG08 | Optional toy VOI has 0≤EVSI≤EVPI; costs reduce net value; no probabilities → no expected monetary output |
| DT22 | ALG09 / DG19 | Horizon/security/liquidity mismatches visible; missing criteria cannot improve rank; paired-scenario trade-offs retained |
| DT23 | ALG10 / DG20 | Revised guidance preserves original; not-due/not-comparable targets are not failed; no honesty score |
| DT24 | ALG11 / DG23 | Missing result is pending/overdue; restatement is revision; identical imports deduplicate; immediate events not delayed |
| DT25 | ALG12 / DG21 | Earnings/multiple interaction reconciles exactly under declared attribution; dilution not counted twice |
| DT26 | ALG12 / DG22 | Multiple-IRR example returns ambiguity/two verified roots, not one definitive return; invalid date/flow cases handled |
| DT27 | ALG14 / DG25 | Model agreement with shared inputs is labelled dependent; structural assumptions that reverse conclusions are visible |
| DT28 | All / DG28 | Source/model change invalidates dependent current results; historical decisions preserved; screen/export use one context |
| DT29 | Personas/UI | All four profiles have expected access/denial, both themes work, persona invariants and real evidence interactions verified |
| DT30 | Runtime | Cancellation, reruns and delayed jobs do not duplicate costs/actions or populate another deal; workload budgets measured |

Tests DT01–DT30 are required production acceptance targets. EX01–EX18 are already executed synthetic specification examples, not substitutes for these end-to-end tests. Test negative, inconsistent, sparse and non-finite inputs; do not merely assert seeded issuer values.

## 21. Delivery order and handoff

1. **Foundation gate:** finish current code-review fixes; accepted facts, null/status handling, identity/access and snapshot/export parity.
2. **Decision evidence:** ALG01/02, source conflict inspector, dependencies and non-probabilistic ALG08 diligence queue.
3. **Operating and funding:** ALG03–ALG05 with statement/cash/share conservation and explicit constraints.
4. **Valuation and downside:** ALG06/07, validated solvers, terminal economics and appropriate uncertainty states.
5. **Comparison and accountability:** ALG09–ALG12 plus history/monitoring UI.
6. **Conditional advanced scope:** ALG13 and probabilistic VOI/Monte Carlo only when actual terms/data/model validation permit them; ALG14 governs every slice.

For each slice provide implemented/partial/blocked requirements, method/run evidence, tests, actual browser/export checks and remaining data requests. No unsupported institutional-readiness score. The correct unavailable answer is acceptable where external data is absent, but an unimplemented required dependency or misleading UI is not complete.

Final handoff: actual branch/commit, delta from base PRD, DG/DD/DT traceability matrix, supported-domain catalogue, source/assumption register, numerical examples and diagnostics, four-profile/both-theme evidence, inspected exports and merge prerequisites. Do not merge, push or deploy.

## 22. Research register and limits

The contracts above are product/mathematical synthesis. Sources guide methodology; they do not validate the application, calibrate probabilities or establish an Indian issuer's investment suitability. Accessed 7 November 2026.

| Source | Specific support and limit |
| --- | --- |
| [Joseph Simonian, Investment Model Validation: A Guide for Practitioners, CFA Research Foundation, 2024](https://rpc.cfainstitute.org/sites/default/files/-/media/documents/article/rf-brief/investment-model-validation.pdf), chapters 2–4 and 7; printed pages 3–17, 36–38 | Model checks, temporal validation, stress and scenario methodology; no app validation inferred. PDF cover title verified despite inaccurate search metadata. |
| [CFA: Free Cash Flow Valuation, 2026 public summary](https://www.cfainstitute.org/insights/professional-learning/refresher-readings/2026/free-cash-flow-valuation) | Claim-specific FCFF/FCFE valuation; public summary only, not gated curriculum. |
| [Damodaran: DCF Problems and Solutions](https://pages.stern.nyu.edu/~adamodar/New_Home_Page/problems/dcfprob.htm) | Match cash flows, discount rates and tax/nominal conventions. Teaching material, not an issuer forecast. |
| [Damodaran: Valuing Young, Start-up and Growth Companies, 2009](https://pages.stern.nyu.edu/~adamodar/pdfiles/papers/younggrowth.pdf) | Short histories, losses, reinvestment and valuation uncertainty. No historical failure-rate estimate imported. |
| [BIS: Stress Testing, RMA30](https://www.bis.org/committees/bcbs/basel-consolidated-guidelines/module/rma/30), definitions and principles | Reverse stress and coherent adverse outcomes. Banking methodology reference, not mandatory IPO law. |
| [SciPy: brentq documentation](https://docs.scipy.org/doc/scipy/reference/generated/scipy.optimize.brentq.html), parameters/convergence | Continuity/bracket preconditions and numerical diagnostics. Does not establish economic validity or uniqueness. |
| [Sheffield SAVI](https://savi.sheffield.ac.uk/SAVI/) and [York: Expected Value of Sample Information](https://pure.york.ac.uk/portal/en/publications/the-expected-value-of-sample-information/) | General information-value concepts. SAVI indexed text was available but direct fetch timed out; no external numeric estimate imported. Healthcare/decision-theory context is not finance calibration. |
| [CFA: Alternative Investment Performance and Returns, 2026](https://www.cfainstitute.org/insights/professional-learning/refresher-readings/2026/alternative-investment-performance-and-returns) | Cash timing and MOIC/IRR distinctions. Root counterexamples are independently checked mathematics. |
| [CFA: Backtesting and Simulation, 2026](https://www.cfainstitute.org/insights/professional-learning/refresher-readings/2026/backtesting-and-simulation) | Walk-forward framing and bias awareness; no claimed backtest performed here. |
| [IFRS: Management Commentary, 2025](https://www.ifrs.org/issued-standards/list-of-standards/management-commentary-practice-statement-1/) | Connected narrative and financial prospects; not automatically applicable Indian disclosure law. |
| [BIS: Principles for Effective Risk Data Aggregation and Reporting](https://www.bis.org/publ/bcbs239.pdf) | Accuracy/completeness/timeliness analogy only; bank-specific requirements are not imposed on issuers. |

No claim of commercial market-data access, original historical management-forecast dataset, causal identification, validated default/return model, legal waterfall certification or production acceptance is made by this design work.
