"""Plain-language method context and result-specific follow-up."""
GUIDANCE = {
 "operating_model": ("Can operational capacity support the plan?", "Revenue is quantity × realized price; operating profit deducts unit and fixed costs. Compare the derived revenue with the same-period financial statement.", "Obtain capacity funding, utilization and price/volume evidence."),
 "cohort_retention": ("Is growth coming from retained customers?", "Net retention follows a frozen opening revenue cohort. New customer revenue is excluded.", "Reconcile cohort membership and separate expansion, churn and new sales."),
 "cash_flow_bridge": ("Does reported cash translate into enterprise cash flow?", "The bridge reconciles capex and the stated cash interest/tax classification.", "Reconcile statement classifications and actual realized tax benefits."),
 "cash_tax": ("When is tax actually paid?", "The illustrative loss-use policy computes cash tax without an immediate refund on losses.", "Confirm eligibility, expiry and jurisdiction-specific tax treatment."),
 "cash_schedule": ("Can the company survive before funding arrives?", "Dated receipts and payments expose interim deficits; only documented eligible facilities can be drawn.", "Resolve the earliest funding deficit before relying on a positive closing balance."),
 "ordinary_raise": ("How much primary equity and dilution are required?", "Gross proceeds cover the net need and fixed/proportional fees at a supplied issue price.", "Confirm price, fees and fully diluted share rights; test alternative issue prices."),
 "equity_bridge": ("Does enterprise value reconcile to shareholder value?", "Post-financing cash and debt are reconciled without counting debt repayment twice.", "Reconcile restricted cash and senior claims before allocating value to old shareholders."),
 "terminal_cash": ("Is terminal growth funded?", "Stable growth consumes reinvestment equal to NOPAT × growth / marginal ROIC.", "Support marginal ROIC and maintenance investment with sector evidence."),
 "discounted_value": ("What do the supplied cash flows imply for value?", "FCFF uses WACC; FCFE uses cost of equity. Currency and real/nominal conventions must match.", "Review terminal-value dependence and compare coherent alternative forecasts."),
 "reverse_dcf": ("What growth is embedded in the proposed enterprise value?", "A bracketed solver finds the growth rate that matches value under fixed discount and terminal assumptions.", "Compare the solved requirement with capacity, market share and comparable growth evidence."),
 "reverse_stress": ("Which tested coherent shock combinations breach the limit?", "A finite admissible scenario set is ranked by standardized severity. Severity does not measure likelihood.", "Review the nearest tested failure path and document mitigating actions."),
 "price_attribution": ("What arithmetic explains the change in price?", "Symmetric earnings and multiple components allocate their interaction exactly; this is not causal attribution.", "Check dividends, share changes and investor cash flows separately."),
 "investor_returns": ("What did the investor contribute and receive, and when?", "Dated cash flows produce NPV and distribution-only MOIC. Nonconventional flows may have ambiguous IRRs.", "Include all fees, contributions and distributions; do not substitute marks for realized cash."),
 "private_waterfall": ("How are exit proceeds allocated across security classes?", "Supported nonparticipating rights use documented fixed joint elections and seniority, conserving proceeds.", "Obtain reviewed legal terms; escalate participation or strategic conversion elections."),
 "information_value": ("Is further diligence worth its cost?", "EVPI and optional EVSI use explicit subjective priors and common action utilities, including cost and delay.", "Elicit defensible utilities and signal behavior; use rule-based priority when priors are unavailable."),
 "compare_opportunities": ("Does one opportunity dominate on paired assumptions?", "Context and scenario metrics must match; only partial dominance is reported.", "Resolve context differences and retain trade-offs rather than forcing a universal score."),
 "evaluate_commitment": ("Did management deliver its original commitment?", "The original target is compared only with a mature same-period, same-basis observation.", "Retain revisions separately and seek comparable disclosed outcomes."),
 "monitor": ("Has a confirmed threshold breach or recovery occurred?", "Hysteresis prevents threshold chatter; missing, stale or disputed observations remain unknown.", "Review new observations and revision lineage before escalating."),
 "robustness": ("Does the conclusion depend on structural choices?", "The tested model envelope distinguishes stable decisions from sensitive ones without claiming confidence intervals.", "Investigate the variants that change the decision."),
}
REFERENCES = [
 {"title": "CFA Institute: Free Cash Flow Valuation", "url": "https://www.cfainstitute.org/insights/professional-learning/refresher-readings/2026/free-cash-flow-valuation", "scope": "FCFF/FCFE methodology; does not validate issuer inputs."},
 {"title": "Damodaran: DCF Problems and Solutions", "url": "https://pages.stern.nyu.edu/~adamodar/New_Home_Page/problems/dcfprob.htm", "scope": "Cash-flow/rate consistency; teaching reference, not issuer evidence."},
 {"title": "CFA Research Foundation: Investment Model Validation", "url": "https://rpc.cfainstitute.org/sites/default/files/-/media/documents/article/rf-brief/investment-model-validation.pdf", "scope": "Model validation and scenario methodology; no empirical app calibration implied."},
 {"title": "CFA Institute: Alternative Investment Performance and Returns", "url": "https://www.cfainstitute.org/insights/professional-learning/refresher-readings/2026/alternative-investment-performance-and-returns", "scope": "MOIC and dated investor-return concepts; no outcome guarantee."},
]
def explain(name, result):
    question, mechanism, followup = GUIDANCE.get(name, ("What can this method establish?", "Explicit rule-based assessment using supplied inputs.", "Resolve the displayed evidence and method requirements."))
    data = result.get("data", {})
    if name == "cash_schedule" and result["state"] == "FUNDING_GAP":
        followup = "Funding gap first observed: " + str(data.get("first_gap") or "opening balance") + ". Obtain committed funding before this date or reschedule uses."
    if name == "discounted_value" and data.get("value"):
        share = data.get("pv_terminal", 0) / data["value"]
        followup = f"Terminal value contributes {share:.1%} of modeled value. Test terminal reinvestment and discount-rate assumptions."
    return question, mechanism, followup
