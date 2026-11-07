# Pre-IPO decision depth: adversarial design assessment

Date: 7 November 2026. Scope: proposed extensions discussed after the equity-question PRD—thesis challenge, operating economics, reverse underwriting, diligence priority, opportunity comparison, funding/dilution, management delivery, evidence conflicts, return attribution and monitoring.

**These are design risks and missing algorithm contracts, not 28 newly demonstrated bugs in Antigravity's active application.** The separate code review remains `PRE_IPO_CODE_REVIEW_5687478_2026-11-07.md`. Existing correctness fixes are prerequisites, not replaced by this assessment.

## Method and outcome

Applied the adversarial-review workflow with two independent Codex finders, a separate Codex adversary and parent verification. The optional external multi-model server was absent; no GPT-4o/Gemini review or provider calls are claimed. The workflow was adapted to a proposed method/design scope rather than changed source lines.

Inputs: prior incremental equity PRD, the user's proposed gap areas, primary methodology research and independent mathematical counterexamples. No active application, database, original external specifications or manuscript files were changed.

Result: 28 consolidated design risks and 14 proposed algorithm contracts. All 14 contracts survived with explicit boundaries after challenge; several stronger claims were rejected. **Eighteen synthetic specification checks passed** in `scratch/pre_ipo_decision_logic_review/validate_method_examples.py`; output is `method_example_results.json`. These establish the stated arithmetic/state examples, not production implementation, empirical calibration or predictive validity.

## Risk register

Priority P1 means required before the affected capability can produce decision conclusions. P2 means required for its operational/interpretive acceptance. IDs map to the companion PRD's algorithms and tests.

| ID | Priority | Failure mode / counterexample | Required contract |
| --- | --- | --- | --- |
| DG01 | P1 | A FY2023 figure restated in 2025 enters a 2023 investment replay | ALG01: separate economic period, public availability, user access, ingestion and revision time; preserve historical views |
| DG02 | P1 | Ten articles copying one issuer claim count as ten confirmations | ALG01: origin-family provenance, dependency/assurance distinctions; source count is not probability |
| DG03 | P1 | Borrowings 100 and debt including leases 140 are averaged or wrongly flagged as the same fact | ALG01: semantic keys and explained bridges before conflict detection; exact-key conflicts remain disputed |
| DG04 | P1 | Unbounded or selectively undisclosed information is treated as low priority or zero risk | ALG08: impact-not-estimable and mandatory blockers; no missing-value quality bonus |
| DG05 | P1 | Equal-length bull/bear prose substitutes for testable theses | ALG02: mechanism, observables, load-bearing assumptions, competing hypotheses and dated review criteria |
| DG06 | P1 | Regression, feature attribution or a falsification trigger is described as causal proof | ALG02/14: identify descriptive, predictive, causal and policy claims; require separate causal design |
| DG07 | P1 | Forecast growth exceeds capacity or requires capex/working capital that is never funded | ALG03/04: operating constraints and linked cash/capital requirements |
| DG08 | P1 | Retention excludes churned customers; acquisition or incentive exclusions make unit economics improve artificially | ALG03: frozen cohorts, consistent populations/cost definitions, sector applicability and financial reconciliation |
| DG09 | P1 | Positive period-end cash hides inability to pay an earlier obligation | ALG04: material dated cash events and interim minimum-cash checks; annual adequacy cannot imply continuous liquidity |
| DG10 | P1 | After-interest cash is valued at WACC; interest/taxes are deducted twice; losses create imaginary cash refunds | ALG04/06: cash-flow claim and tax policy contracts; explicit cash-interest and realized tax-benefit bridges |
| DG11 | P1 | A financing plug fills every shortfall even when facilities are uncommitted or conditions are unmet | ALG04: eligible draw policies, contingent financing branches and unfinanced deficits |
| DG12 | P1 | New-share dilution ignores fees or uses a price generated circularly by its own post-financing value | ALG05: dated event ledger and fixed/solved pricing convention with residuals |
| DG13 | P1 | Primary proceeds both repay debt and remain as extra cash in the equity bridge | ALG05/06: event-level sources/uses and one consistent pre/post-deployment state |
| DG14 | P1 | Perpetual growth is capitalized without the reinvestment that sustains it | ALG03/06: terminal operating state, growth/capital efficiency and maintenance/growth reconciliation |
| DG15 | P1 | FCFE/FCFF, currency, nominal/real rates, security rights or financial-sector models are mixed | ALG06/13: model-eligibility and valuation-claim identity before execution |
| DG16 | P1 | A solver returns the interval edge or one discovered root as a unique economic answer | ALG06/12: domain, bracket, continuity, residual and ambiguity checks; no-bracket is not no-root |
| DG17 | P1 | Closest standardized failure shock is called most probable | ALG07: disclosed severity metric and alternative coherent breach frontiers; probabilities need validated joint distributions |
| DG18 | P1 | A sensitivity range becomes an expected rupee value of collecting information | ALG08: non-probabilistic priority by default; optional VOI requires actions, utilities, probabilities and information model |
| DG19 | P1 | Headline returns rank incomparable horizons, currencies, liquidity or securities | ALG09: comparison contract and partial ordering; missing criteria cannot improve rank |
| DG20 | P2 | Revised targets erase original misses; only easy public promises enter a delivery score | ALG10: immutable commitment ledger, declared inclusion policy, maturity and comparable actuals |
| DG21 | P1 | Earnings and multiple effects are added without interaction; EPS dilution is penalized twice | ALG12: exact reconciled attribution convention, separate dated investor cash ledger |
| DG22 | P1 | One returned IRR hides multiple roots or weak capital recovery | ALG12: NPV profile, root diagnostics, MOIC conventions, dates and actual investor distributions |
| DG23 | P1 | Missing/delayed results trigger revenue collapse; restatements look like new operating shocks | ALG11: observation maturity, revision-aware alerts and overdue-data states |
| DG24 | P1 | Arbitrary Monte Carlo distributions or stress counts are presented as success/default probabilities | ALG14: separate scenario, parameter and empirical uncertainty; validate distributions or show bounded scenarios |
| DG25 | P1 | Agreement among models sharing the same inputs is called independent validation | ALG14: model/input family dependence, structural sensitivity and out-of-time evaluation |
| DG26 | P1 | Preferred classes independently elect maximum payoffs that exceed distributable proceeds | ALG13: actual legal priorities/conversion rules and aggregate conservation |
| DG27 | P1 | Waiting for information is a free option with no price/access/deadline consequences | ALG08/09: dated actions, information arrival, transaction availability and delay costs; otherwise no waiting-value claim |
| DG28 | P1 | A source/model change silently rewrites an accepted decision or produces mixed-version screen/export results | All: atomic accepted snapshots, dependency invalidation, historical decision attribution and shared export context |

## Counterexamples that materially change the design

1. **Liquidity:** opening cash 50, payment 100, later receipt 100 gives ending cash 50 but an interim deficit of 50. It is a timing failure under the scenario, not automatically a legal insolvency conclusion.
2. **Cash-flow convention:** CFO 70 already reflects interest 20 and tax benefit 5; capex 30. CFO minus capex is 40, while the consistently bridged FCFF is 55. Their discount rates/claims cannot be interchanged.
3. **Funding:** net need 100, 5% proportional fees, issue price 8 and 100 old shares require gross 105.263 and 13.158 new shares; old ownership becomes approximately 88.372%.
4. **Primary conservation:** operating EV 1,000, debt 200, no cash; primary proceeds 100 entirely repay debt. Post-event total equity is 900, not 1,000 from counting proceeds twice. Per-old-share value still requires the new-share ledger.
5. **Terminal economics:** under a stated stable operating-growth model, next NOPAT 100, growth 5% and marginal ROIC 10% require reinvestment 50, leaving next FCFF 50. This identity is not a universal rule for arbitrary FCF growth or shrinking firms.
6. **Information priority:** a bounded value range 90–130 around a user hurdle 110 can change that policy conclusion; 118–122 does not cross it. Neither range implies a probability of reversal.
7. **VOI:** illustrative invest/decline payoffs and supplied equal probabilities give EVPI 15 and a specified imperfect signal EVSI 7. Paying 8 for that signal yields net value −1. These are toy inputs, not calibrated investment recommendations.
8. **Returns:** earnings factor 1.2 and multiple factor 1.25 produce 50% price growth, not 45%. Exact two-factor midpoint allocation gives 22.5 and 27.5 percentage points. It is attribution, not causality or a complete TSR calculation.
9. **IRR:** annual cash flows −100, +230, −132 have roots at both 10% and 20%. One solver output cannot establish uniqueness.
10. **Root finding:** `(x−0.2)(x−0.8)` is positive at both interval endpoints 0 and 1 but has two interior roots. An absent sign change does not prove there is no solution.

## Claims explicitly rejected by the adversary

- Number of citations as calibrated confidence or independent observations.
- Historical public replay requiring today's ingestion timestamp to precede a historical cutoff; authenticated historical availability is the relevant public-replay gate. Actual decision-audit replay has a different information set.
- Minimum stress distance as likelihood, probability or uniquely plausible economic path.
- A bracket or one discovered XIRR root as proof of global uniqueness.
- Sensitivity or valuation width as expected monetary information value.
- Midpoint/Shapley-style attribution as causal explanation.
- Missed guidance as a management-honesty score.
- Terminal `g/ROIC` applied to arbitrary FCF growth, negative growth or every sector.
- Hysteresis delaying an immediate contractual/legal event.
- Overlapping marginal intervals as proof that no alternative dominates; joint scenarios can matter.
- More detailed models or multiple dependent models as validation.

## Research grounding and scope limits

The companion PRD contains a source register with primary references for model validation, cash-flow valuation, reverse stress, root-finding, return measures and information value. These sources inform methodology; none validates the app, its scenario probabilities, issuer recommendations or a universal numerical policy.

Basel stress/data principles are banking references used for methodological analogy, not statutory requirements on Indian IPO issuers. Sheffield/York information-value research supplies general decision-theory context, not finance-specific calibration. Public CFA summaries are used within their accessible scope. No commercial data access, historical forecast dataset or management reliability model is asserted.

## Delivery recommendation

Build the shared temporal/evidence and dependency contract first, then coherent operating/cash/funding models, then valuation and bounded decision analysis, then comparison/monitoring. Keep probabilistic VOI and complex private rights behind explicit eligibility gates. Each engine must be able to return a bound, ambiguity, conflict, data request or unsolved state without disguising it as an affirmative investment conclusion.

Next: [algorithm and decision-depth incremental PRD](../plans/PRE_IPO_DECISION_DEPTH_ALGORITHM_PRD_2026-11-07.md).
