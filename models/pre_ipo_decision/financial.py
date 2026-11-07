"""Operating, timed financing, valuation and investor-return methods (ALG03-07/12-13)."""
import math
from .contracts import Result, number, positive, timestamp

def operating_model(segments: list[dict], reconciliation_revenue=None) -> Result:
    if not segments:
        return Result("INSUFFICIENT_EVIDENCE", reasons=("Operating segments not supplied",))
    rows = []
    for s in segments:
        quantity = number(s["quantity"], "quantity", 0)
        capacity = number(s["capacity"], "capacity", 0)
        price = number(s["net_price"], "net price", 0)
        if quantity > capacity:
            return Result("INFEASIBLE", reasons=(f"{s['name']}: quantity exceeds funded capacity",))
        revenue = quantity * price
        cost = quantity * number(s["unit_cost"], "unit cost", 0) + number(s["fixed_cost"], "fixed cost", 0)
        rows.append({"name": s["name"], "revenue": revenue, "operating_profit": revenue - cost})
    total = sum(r["revenue"] for r in rows)
    delta = None if reconciliation_revenue is None else total - number(reconciliation_revenue, "reported revenue")
    return Result("COMPUTED", {"segments": rows, "revenue": total, "reconciliation_difference": delta},
                  assumptions=("Same period, compatible quantities/prices and funded capacity supplied by user",))

def cohort_retention(opening, expansion, contraction, churn, *, new_customers=0) -> Result:
    opening = positive(opening, "opening cohort revenue")
    expansion, contraction, churn, new_customers = [number(v, k, 0) for k, v in
        [("expansion", expansion), ("contraction", contraction), ("churn", churn), ("new customers", new_customers)]]
    if contraction + churn > opening:
        raise ValueError("Contraction and churn exceed the frozen opening cohort")
    retained = opening + expansion - contraction - churn
    return Result("COMPUTED", {"nrr": retained / opening, "existing_cohort_revenue": retained,
                              "excluded_new_revenue": new_customers},
                  assumptions=("Frozen comparable revenue cohort; exited members retained",))

def cash_flow_bridge(cfo, cash_capex, cash_interest, realized_interest_tax_benefit, *, cfo_includes_interest) -> Result:
    cfo = number(cfo, "CFO")
    capex = number(cash_capex, "capex", 0)
    interest = number(cash_interest, "interest", 0)
    benefit = number(realized_interest_tax_benefit, "realized tax benefit", 0)
    if not isinstance(cfo_includes_interest, bool) or benefit > interest:
        raise ValueError("Confirm the cash-flow convention and realized tax benefit")
    fcff = cfo - capex + (interest if cfo_includes_interest else 0) - benefit
    return Result("COMPUTED", {"fcff": fcff, "cfo_less_capex": cfo - capex},
                  assumptions=("Supplied CFO and cash-tax/interest classification reconciled; not generic FCFE",))

def cash_tax(taxable_profit, rate, loss_available=0, loss_usage_limit=1.0) -> Result:
    profit = number(taxable_profit, "taxable profit")
    rate = number(rate, "tax rate", 0, 1)
    losses = number(loss_available, "available tax losses", 0)
    limit = number(loss_usage_limit, "loss usage fraction", 0, 1)
    used = min(losses, max(0, profit) * limit)
    return Result("CONDITIONAL_MODEL", {"cash_tax": max(0, profit - used) * rate,
        "loss_used": used, "closing_loss": losses - used + max(0, -profit)},
        assumptions=("Illustrative supplied tax-loss policy; no immediate refund or legal eligibility inferred",))

def cash_schedule(opening_cash, minimum_cash, events: list[dict], facilities: list[dict] | None = None) -> Result:
    cash = number(opening_cash, "opening unrestricted cash", 0)
    minimum = number(minimum_cash, "minimum cash", 0)
    facilities = facilities or []
    lines = {}
    for f in facilities:
        if f["id"] in lines:
            raise ValueError("Duplicate facility ID")
        lines[f["id"]] = dict(f, remaining=number(f["available"], "available facility", 0))
        timestamp(f["available_from"]); timestamp(f["available_until"])
    order = [(timestamp(e["date"]), e.get("sequence", 0)) for e in events]
    if len(order) != len(set(order)):
        raise ValueError("Same-date cash events need unique explicit sequence values")
    rows = []
    first_gap = None
    for e in sorted(events, key=lambda x: (timestamp(x["date"]), x.get("sequence", 0))):
        receipts = number(e.get("operating_cash_pre_debt_service", 0), "operating cash")
        uses = sum(number(e.get(k, 0), k, 0) for k in
                   ("cash_capex", "acquisitions", "cash_interest", "principal", "distributions"))
        cash += receipts + number(e.get("disposal_receipts", 0), "disposal receipts", 0) - uses
        before = cash
        draw = number(e.get("draw", 0), "draw", 0)
        if draw:
            facility = lines.get(e.get("facility_id"))
            t = timestamp(e["date"])
            if (not facility or facility.get("committed") is not True or facility.get("conditions_met") is not True
                or not timestamp(facility["available_from"]) <= t <= timestamp(facility["available_until"])
                or draw > facility["remaining"]):
                return Result("INFEASIBLE", {"rows": rows, "failed_event": e},
                              reasons=("Draw exceeds documented eligibility/availability; no balancing plug applied",))
            facility["remaining"] -= draw
        cash += draw + number(e.get("net_primary_equity", 0), "net equity", 0)
        gap = max(0, minimum - cash)
        if gap and first_gap is None:
            first_gap = e["date"]
        rows.append({"date": e["date"], "sequence": e.get("sequence", 0), "pre_financing_cash": before,
                     "cash_close": cash, "funding_gap": gap})
    opening_gap = max(0, minimum - number(opening_cash, "opening cash"))
    return Result("FUNDING_GAP" if first_gap or opening_gap else "CONDITIONAL_MODEL",
                  {"rows": rows, "closing_cash": cash, "opening_gap": opening_gap, "first_gap": first_gap,
                   "minimum_observed_cash": min([opening_cash] + [r["cash_close"] for r in rows])},
                  assumptions=("Cash events are net at supplied timestamps; intra-event and omitted timing unassessed",
                               "Operating cash excludes separately deducted debt service and includes reconciled cash taxes"))

def ordinary_raise(old_shares, required_net, price, proportional_fee, fixed_fee=0) -> Result:
    old_shares, price = positive(old_shares, "old shares"), positive(price, "issue price")
    net, fixed = number(required_net, "net need", 0), number(fixed_fee, "fixed fee", 0)
    fee = number(proportional_fee, "proportional fee", 0)
    if fee >= 1:
        raise ValueError("Proportional fee must be below one")
    gross = (net + fixed) / (1 - fee)
    new = gross / price
    return Result("CONDITIONAL_MODEL", {"gross_raise": gross, "new_shares": new,
        "post_shares": old_shares + new, "old_ownership": old_shares / (old_shares + new),
        "net_receipts": gross * (1 - fee) - fixed},
        assumptions=("Fixed supplied price, ordinary primary equity only; no conversion rights",))

def equity_bridge(operating_ev, debt, unrestricted_excess_cash, *, primary_net=0, repayment=0, other_uses=0,
                  other_claims=0) -> Result:
    ev = number(operating_ev, "operating EV", 0)
    debt, cash, primary, repayment, uses, claims = [number(v, k, 0) for k, v in
        [("debt", debt), ("cash", unrestricted_excess_cash), ("primary", primary_net),
         ("repayment", repayment), ("uses", other_uses), ("other claims", other_claims)]]
    if repayment > debt or repayment + uses > cash + primary:
        return Result("INFEASIBLE", reasons=("Repayment exceeds principal or available sources",))
    post_cash, post_debt = cash + primary - repayment - uses, debt - repayment
    return Result("CONDITIONAL_MODEL", {"post_cash": post_cash, "post_debt": post_debt,
        "aggregate_equity_value": ev + post_cash - post_debt - claims},
        assumptions=("Operating EV already reflects modeled investment uses; aggregate value is not old-holder value",))

def terminal_cash(next_nopat, growth, marginal_roic) -> Result:
    nopat = number(next_nopat, "next NOPAT", 0)
    growth = number(growth, "stable operating growth", 0)
    roic = positive(marginal_roic, "marginal ROIC")
    reinvestment = nopat * growth / roic
    if growth > roic:
        return Result("INFEASIBLE", reasons=("Stable growth requires more than supplied operating profit for reinvestment",))
    return Result("CONDITIONAL_MODEL", {"growth_reinvestment": reinvestment, "next_fcff": nopat - reinvestment},
                  assumptions=("Stable operating capital efficiency; maintenance reconciled separately; not arbitrary FCF CAGR",))

def discounted_value(cash_flows: list[float], discount_rate, terminal_next_cash, terminal_growth,
                     *, claim, rate_claim, currency, rate_currency, basis, rate_basis) -> Result:
    if claim not in {"FCFF", "FCFE"} or rate_claim != {"FCFF": "WACC", "FCFE": "KE"}[claim]:
        return Result("UNSUPPORTED", reasons=("Cash-flow and discount-rate claims do not match",))
    if currency != rate_currency or basis != rate_basis or basis not in {"nominal", "real"}:
        return Result("UNSUPPORTED", reasons=("Currency or nominal/real conventions do not match",))
    if not cash_flows:
        raise ValueError("Forecast cash flows required")
    rate = number(discount_rate, "discount rate")
    growth = number(terminal_growth, "terminal growth")
    terminal = number(terminal_next_cash, "terminal next cash", 0)
    if rate <= -1 or growth <= -1 or rate <= growth:
        return Result("INVALID_DOMAIN", reasons=("Require discount rate > terminal growth and both above -100%",))
    flows = [number(x, "cash flow") for x in cash_flows]
    pv = sum(v / (1 + rate) ** (i + 1) for i, v in enumerate(flows))
    pv_terminal = terminal / (rate - growth) / (1 + rate) ** len(flows)
    return Result("CONDITIONAL_MODEL", {"value": pv + pv_terminal, "pv_forecast": pv,
                                      "pv_terminal": pv_terminal, "claim": claim},
                  assumptions=("End-period annual cash flows; terminal operating economics separately validated",))

def bracketed_root(fn, low, high, *, value_scale=1.0, residual_tolerance=1e-8, max_iterations=150) -> Result:
    low, high = number(low, "lower bound"), number(high, "upper bound")
    scale, tol = positive(value_scale, "value scale"), positive(residual_tolerance, "residual tolerance")
    if low >= high or not isinstance(max_iterations, int) or not 1 <= max_iterations <= 10000:
        raise ValueError("Valid bounds and iteration budget required")
    fl, fh = number(fn(low), "lower residual"), number(fn(high), "upper residual")
    for x, f in ((low, fl), (high, fh)):
        if abs(f) / scale <= tol:
            return Result("SOLVED_IN_BRACKET", {"root": x, "normalized_residual": abs(f) / scale},
                          assumptions=("Caller must establish continuity; no global uniqueness claim",))
    if (fl > 0) == (fh > 0):
        return Result("UNBRACKETED", {"lower_residual": fl, "upper_residual": fh},
                      reasons=("No sign-changing bracket; this does not prove absence of roots",))
    for iteration in range(max_iterations):
        mid = (low + high) / 2
        fm = number(fn(mid), "candidate residual")
        if abs(fm) / scale <= tol:
            return Result("SOLVED_IN_BRACKET", {"root": mid, "normalized_residual": abs(fm) / scale,
                                               "iterations": iteration + 1},
                          assumptions=("Continuous eligible bracket supplied; uniqueness outside it unverified",))
        if (fl > 0) != (fm > 0):
            high = mid
        else:
            low, fl = mid, fm
    return Result("NOT_CONVERGED", reasons=("Residual criterion not met; no boundary substituted",))

def reverse_dcf(base_fcff, target_ev, discount_rate, terminal_growth, low, high, years=5) -> Result:
    base, target = positive(base_fcff, "positive starting FCFF"), positive(target_ev, "target EV")
    rate, growth = number(discount_rate, "discount rate"), number(terminal_growth, "terminal growth")
    low, high = number(low, "lower growth bound"), number(high, "upper growth bound")
    if rate <= growth or rate <= -1 or growth <= -1 or low <= -1:
        return Result("INVALID_DOMAIN", reasons=("Invalid perpetuity/growth domain",))
    if not isinstance(years, int) or not 1 <= years <= 100:
        raise ValueError("Forecast years must be an integer from 1 to 100")
    def residual(cagr):
        flows = [base * (1 + cagr) ** y for y in range(1, years + 1)]
        return sum(f / (1 + rate) ** (i + 1) for i, f in enumerate(flows)) + flows[-1] * (1 + growth) / (rate - growth) / (1 + rate) ** years - target
    result = bracketed_root(residual, low, high, value_scale=target)
    return Result(result.state, result.data, result.reasons, result.assumptions +
                  ("One-variable FCFF growth model; rate/terminal assumptions fixed, not empirical achievability",))

def reverse_stress(candidates: list[dict], scales: dict, weights=None, *, failure_metric="cash_margin") -> Result:
    weights = weights or {k: 1.0 for k in scales}
    if not scales or set(weights) != set(scales):
        raise ValueError("Shock scales and weights must share a nonempty schema")
    for key in scales:
        positive(scales[key], f"{key} scale"); positive(weights[key], f"{key} weight")
    if not candidates:
        return Result("INSUFFICIENT_EVIDENCE", reasons=("No coherent stress scenarios supplied",))
    failures, excluded = [], []
    for case in candidates:
        if set(case["shocks"]) != set(scales):
            raise ValueError("Every stress case must have the declared shock schema")
        distance = sum(weights[k] * (number(case["shocks"][k], k) / scales[k]) ** 2 for k in scales)
        margin = number(case[failure_metric], failure_metric)
        if case.get("economically_admissible") is not True:
            excluded.append(case["id"])
        elif margin < 0:
            failures.append(dict(case, severity=math.sqrt(distance)))
    failures.sort(key=lambda x: (x["severity"], x["id"]))
    return Result("ENUMERATED_FAILURE_FRONTIER" if failures else "NO_BREACH_IN_TESTED_SET",
                  {"failure_paths": failures, "excluded": excluded, "tested": len(candidates)},
                  assumptions=("Finite supplied coherent scenarios; not a global minimum, likelihood or probability",))

def price_attribution(eps0, eps1, multiple0, multiple1) -> Result:
    e0, e1, m0, m1 = [positive(v, n) for n, v in
                       [("opening EPS", eps0), ("closing EPS", eps1), ("opening multiple", multiple0), ("closing multiple", multiple1)]]
    earnings, multiple = (e1 - e0) * (m0 + m1) / 2, (m1 - m0) * (e0 + e1) / 2
    change = e1 * m1 - e0 * m0
    return Result("COMPUTED", {"earnings_component": earnings, "multiple_component": multiple,
        "price_change": change, "price_return": change / (e0 * m0), "residual": change - earnings - multiple},
        assumptions=("Symmetric price-identity attribution, not causality/TSR; dilution already in EPS",))

def investor_returns(flows: list[dict], discount_rate, *, search_low=-0.99, search_high=10.0, grid_size=400) -> Result:
    if not 10 <= grid_size <= 5000 or search_low <= -1 or search_high <= search_low:
        raise ValueError("Invalid IRR search domain/budget")
    grouped = {}
    for flow in flows:
        t = timestamp(flow["date"])
        grouped[t] = grouped.get(t, 0) + number(flow["amount"], "investor cash flow")
    dated = sorted((t, cf) for t, cf in grouped.items() if cf != 0)
    if len(dated) < 2 or not any(cf < 0 for _, cf in dated) or not any(cf > 0 for _, cf in dated):
        return Result("IRR_UNAVAILABLE", reasons=("Need dated contributions and distributions over nonzero elapsed time",))
    origin = dated[0][0]
    times = [(t - origin).total_seconds() / (365 * 86400) for t, _ in dated]
    rate = number(discount_rate, "NPV discount rate")
    if rate <= -1:
        raise ValueError("NPV rate must exceed -100%")
    def npv(r):
        return sum(cf / (1 + r) ** dt for (_, cf), dt in zip(dated, times))
    scale = sum(abs(cf) for _, cf in dated)
    roots = []
    points = [math.expm1(math.log1p(search_low) + i / grid_size *
                         (math.log1p(search_high) - math.log1p(search_low))) for i in range(grid_size + 1)]
    for a, b in zip(points, points[1:]):
        result = bracketed_root(npv, a, b, value_scale=scale)
        if result.state == "SOLVED_IN_BRACKET" and all(abs(result.data["root"] - r) > 1e-6 for r in roots):
            roots.append(result.data["root"])
    changes = sum(a[1] * b[1] < 0 for a, b in zip(dated, dated[1:]))
    unique_shape = changes == 1 and dated[0][1] < 0 and all(cf > 0 for _, cf in dated[1:])
    state = "IRR_SOLVED" if unique_shape and len(roots) == 1 else "IRR_NON_UNIQUE_OR_UNVERIFIED"
    return Result(state, {"roots_found": roots, "npv": npv(rate),
        "moic_distributions_only": sum(cf for _, cf in dated if cf > 0) / -sum(cf for _, cf in dated if cf < 0),
        "sign_changes": changes, "search_domain": [search_low, search_high]},
        assumptions=("ACT/365, dated net investor cash; finite search does not exhaust roots",))

def private_waterfall(proceeds, classes: list[dict], *, terms_verified=False) -> Result:
    proceeds = number(proceeds, "distributable proceeds after senior claims/costs", 0)
    if terms_verified is not True:
        return Result("INSUFFICIENT_EVIDENCE", reasons=("Dated security terms require authorized source review",))
    if not classes or len({c["id"] for c in classes}) != len(classes):
        raise ValueError("Unique share classes required")
    # Supported domain: nonparticipating preferences; fixed conversion elections only.
    if any(c.get("participating") or c.get("conversion_election") not in {"convert", "prefer", "ordinary"} for c in classes):
        return Result("UNSUPPORTED_TERMS", reasons=("Participation, strategic elections and complex rights require specialist model",))
    remaining, allocation = proceeds, {c["id"]: 0.0 for c in classes}
    for c in classes:
        number(c["shares"], "class shares", 0)
        number(c.get("preference", 0), "preference", 0)
    preferred = [c for c in classes if c["conversion_election"] == "prefer"]
    for c in preferred:
        number(c["seniority"], "seniority", 0)
    for priority in sorted({c["seniority"] for c in preferred}):
        group = [c for c in preferred if c["seniority"] == priority]
        total = sum(c["preference"] for c in group)
        paid = min(remaining, total)
        for c in group:
            allocation[c["id"]] = paid * c["preference"] / total if total else 0
        remaining -= paid
    common = [c for c in classes if c["conversion_election"] in {"convert", "ordinary"}]
    total_common = sum(c["shares"] for c in common)
    if remaining and not total_common:
        return Result("UNSUPPORTED_TERMS", reasons=("Residual proceeds have no documented common claim",))
    for c in common:
        allocation[c["id"]] += remaining * c["shares"] / total_common if total_common else 0
    return Result("CONDITIONAL_MODEL", {"class_proceeds": allocation, "conservation_residual": proceeds - sum(allocation.values())},
                  assumptions=("Fixed documented joint elections; nonparticipating classes only; no exit guarantee",))
