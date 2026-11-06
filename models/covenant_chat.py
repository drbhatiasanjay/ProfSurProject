"""Provider-independent chat routing for the opt-in covenant pilot.

Only supported, explicitly parsed requests reach the engine. Drafts require
confirmation and include their input fingerprint. State belongs to the calling
conversation, never a module-level cache. Financial prose is rendered from JSON.
"""
from dataclasses import asdict, replace
import re

from models.covenant_examples import example_catalog
from models.covenant_pilot import CovenantSpec, ScenarioRequest, ScenarioInputError, fingerprint, simulate, validate_inputs


def _ratio(value):
    return "N/A" if value is None else f"{value:.2f}x"


def render_result(result: dict) -> str:
    stressed = result["stressed"]
    decision = "Inputs incomplete: headroom withheld." if stressed["unavailable"] else (
        "The proposed financing breaches the illustrative constraints." if stressed["violations"] else
        "The proposed financing satisfies the illustrative constraints over the modeled horizon.")
    headroom = result["additional_headroom_cr"]
    rows = [f"**{result['company']} — covenant pilot**", decision,
            "", "**Illustrative forecast; not actual covenant compliance or a credit rating.**", "",
            f"Additional borrowing headroom above the proposed debt: **{'withheld' if headroom is None else f'₹{headroom:,.2f} crore'}**.",
            f"Binding constraints: {', '.join(result['binding_constraints']) or 'none'}.", "",
            "| Metric | Baseline Q1 | Scenario Q1 |", "|---|---:|---:|"]
    base, stress = result["baseline"]["quarters"][0], stressed["quarters"][0]
    for label, key in (("DSCR (demo definition)", "dscr"), ("Earnings / interest coverage", "icr"), ("TOL/TNW", "tol_tnw")):
        rows.append(f"| {label} | {_ratio(base[key])} | {_ratio(stress[key])} |")
    rows.append(f"| Closing cash (₹ crore) | {base['closing_cash_cr']:,.2f} | {stress['closing_cash_cr']:,.2f} |")
    if result["baseline"]["violations"]:
        rows.extend(["", "The unstressed baseline also has modeled breaches; inspect its quarter-by-quarter results."])
    if stressed["violations"]:
        first = stressed["violations"][0]
        rows.extend(["", f"First modeled breach: quarter {first['quarter']}, {first['constraint']}."])
    if any(q["cash_sweep_triggered"] for q in stressed["quarters"]):
        rows.extend(["", "The configured cash-sweep threshold is triggered; waterfall effects are not modeled."])
    rows.extend(["", *stressed["unavailable"]])
    if result["search_limit_reached"]:
        rows.append("Headroom is capped by the search limit, not a proven maximum.")
    rows.extend(["", f"Earnings basis: {result['inputs']['snapshot']['earnings_basis']}; public anchor date: {result['inputs']['snapshot']['as_of']}.",
                 "Loan/lease schedules, forecasts and covenant limits are illustrative; no calibrated System GMM is used."])
    return "\n".join(rows)


def draft_text(draft: dict) -> str:
    req, cov = draft["request"], draft["covenants"]
    return (
        f"**Confirm covenant scenario: {draft['company']}**\n\n"
        f"Frozen public anchor: {draft['as_of']} ({draft['perimeter']}); horizon: 12 quarters.\n\n"
        f"Rate shock: {req['rate_shock_bps']:+g} bps; earnings/margin shock: {req['margin_shock_pct']:+g}% relative; "
        f"new debt spent on capex: ₹{req['incremental_debt_cr']:,.2f} crore; new floating rate: {req['incremental_annual_rate']:.2%}.\n\n"
        f"Lease payments {'included' if req['lease_in_coverage'] else 'excluded'} in coverage ratios; always included in cash outflows.\n\n"
        f"Illustrative covenant assumptions: DSCR {cov['dscr_floor']}x; earnings/interest coverage {cov['icr_floor']}x; "
        f"TOL/TNW {cov['tol_tnw_ceiling']}x; minimum cash ₹{cov['minimum_cash_cr']:,.2f} crore.\n\n"
        "Schedules and forward projections are illustrative. Open the scenario card to inspect evidence and edit assumptions, "
        "then choose **Run confirmed scenario**, or reply **confirm scenario**."
    )


def make_draft(entity_id: str, request=None, covenants=None) -> dict:
    example = example_catalog()[entity_id]
    snap = example["snapshot"]
    return {"entity_id": entity_id, "company": snap.company, "as_of": snap.as_of, "perimeter": snap.perimeter,
            "request": asdict(request or ScenarioRequest()), "covenants": asdict(covenants or CovenantSpec()),
            "source_fingerprint": fingerprint({"snapshot": asdict(snap), "debts": [asdict(d) for d in example["debts"]],
                                               "leases": [asdict(l) for l in example["leases"]]})}


def run_draft(draft: dict) -> dict:
    fresh = make_draft(draft["entity_id"])
    if draft["source_fingerprint"] != fresh["source_fingerprint"]:
        raise ScenarioInputError("Example inputs changed; review and reconfirm a fresh scenario")
    example = example_catalog()[draft["entity_id"]]
    return simulate(example["snapshot"], example["debts"], example["leases"],
                    CovenantSpec(**draft["covenants"]), ScenarioRequest(**draft["request"]))


def handle_query(query: str, state: dict | None = None, *, selected_company=None) -> dict | None:
    """Return a handled turn and new state, or None for the normal assistant.

    The pilot uses a deliberately small deterministic grammar. Unsupported
    finance shocks return an explanation, never invented numerical parameters.
    """
    state = dict(state or {})
    q = query.strip().lower().replace("₹", "rs ")
    if q in ("cancel borrower validation", "cancel borrower intake"):
        state.pop("borrower_intake_requested", None)
        return {"content": "Borrower evidence upload card closed. Saved reports are retained.", "state": state}
    if re.search(r"\b(borrower validation|validate (?:an? |the )?(?:actual )?borrower|validate actual (?:data|documents)|borrower evidence)\b", q):
        state["borrower_intake_requested"] = True
        return {"content": "**Borrower evidence validation**\n\nUse the upload card below to submit a borrower packet and its supporting financial statements, facility terms, loan/lease schedules, forecast and net-worth bridge. The check reports missing evidence, source mismatches and balance reconciliation issues. It does not infer covenant terms or substitute the illustrative example schedules.\n\nIf you need the packet format, download the blank template from the card. Actual covenant calculations remain disabled pending finance review and definition mapping.", "state": state}
    confirm = q in ("confirm scenario", "run confirmed scenario", "confirm covenant scenario")
    cancel = q in ("cancel scenario", "cancel covenant scenario")
    compare = q in ("compare scenarios", "compare covenant scenarios")
    active = state.get("draft")
    previous = active or state.get("last_draft")
    catalog = example_catalog()
    matches = [entity for entity, item in catalog.items() if any(re.search(r"(?<!\w)" + re.escape(alias) + r"(?!\w)", q) for alias in item["aliases"])]
    finance_terms = re.search(r"\b(bps|margin|earnings|new debt|incremental debt|leases|dscr|icr|tol|minimum cash|capex|covenant)\b", q)
    looks_like_edit = previous is not None and bool(finance_terms)
    if not (confirm or cancel or compare or looks_like_edit or (matches and finance_terms) or re.search(r"covenant pilot|debt headroom|borrowing headroom|covenant scenario", q)):
        return None
    if cancel:
        state.pop("draft", None)
        return {"content": "Pending covenant scenario cancelled. Previous confirmed results are retained.", "state": state}
    if compare:
        results = state.get("results", [])
        if len(results) < 2:
            return {"content": "Run two confirmed covenant scenarios before comparing them.", "state": state}
        lines = ["| Scenario | Company | Rate shock (bps) | Margin shock (%) | New debt (₹ crore) | Additional headroom (₹ crore) |", "|---|---|---:|---:|---:|---:|"]
        for i, result in enumerate(results[-2:], 1):
            r = result["inputs"]["request"]
            value = result["additional_headroom_cr"]
            lines.append(f"| {i} | {result['company']} | {r['rate_shock_bps']} | {r['margin_shock_pct']} | {r['incremental_debt_cr']} | {'withheld' if value is None else f'{value:,.2f}'} |")
        return {"content": "\n".join(lines) + "\n\nIllustrative forecasts; company-specific earnings bases and sources may differ.", "state": state}
    if confirm:
        if not active:
            return {"content": "No pending scenario. Start with 'covenant pilot for Tata Steel' or 'covenant pilot for IndiGo'.", "state": state}
        try:
            result = run_draft(active)
        except (ScenarioInputError, TypeError, KeyError) as exc:
            return {"content": f"Scenario not executed: {exc}", "state": state}
        state["results"] = (state.get("results", []) + [result])[-10:]
        # Retain assumptions for explicit follow-up editing, but mark confirmation
        # consumed so replay cannot execute again without a new draft.
        state["last_draft"] = active
        state.pop("draft", None)
        return {"content": render_result(result), "state": state, "result": result}
    if len(matches) > 1:
        return {"content": "Choose one company per scenario: Tata Steel or IndiGo. Run both separately, then compare scenarios.", "state": state}
    # An explicit unknown company cannot inherit a previous/selected entity.
    if not matches and re.search(r"\bfor\s+[a-z]", q):
        return {"content": "Company not supported by the pilot. Choose Tata Steel or IndiGo; other companies need complete schedules and source evidence.", "state": state}
    entity = matches[0] if matches else (previous["entity_id"] if previous else None)
    if entity is None and selected_company is not None:
        entity = next((e for e, item in catalog.items() if str(selected_company) in item["aliases"]), None)
    if entity is None:
        state["awaiting_company_query"] = query
        return {"content": "Choose the public example: reply 'covenant pilot for Tata Steel' or 'covenant pilot for IndiGo'. The schedules and forecasts are illustrative.", "state": state}
    inherited = previous if previous and previous["entity_id"] == entity else None
    request = ScenarioRequest(**inherited["request"]) if inherited else ScenarioRequest()
    cov = CovenantSpec(**inherited["covenants"]) if inherited else CovenantSpec()
    if re.search(r"\b(fuel|fx|currency|forex|buyback|tax rate|collateral|life.stage)\b", q):
        return {"content": "That shock is not modeled in this pilot. Use a rate shock in bps, a relative margin shock, incremental debt in crore, or lease coverage inclusion.", "state": state}
    values = {}
    rate = re.search(r"([+-]?\d+(?:\.\d+)?)\s*bps\b", q)
    if len(re.findall(r"[+-]?\d+(?:\.\d+)?\s*bps\b", q)) > 1:
        return {"content": "Specify one rate shock per scenario, then compare confirmed scenarios.", "state": state}
    if re.search(r"\b(rates?|interest)\b", q) and not rate:
        return {"content": "Specify the rate shock in basis points, for example 'rates +150 bps'.", "state": state}
    if rate:
        number = float(rate.group(1))
        if re.search(r"\b(cut|cuts|fall|falls|drop|drops|decrease)\b[^.;%]*" + re.escape(rate.group(0)), q):
            number = -abs(number)
        values["rate_shock_bps"] = number
    margin = re.search(r"(?:margins?|earnings|ebitda)\s*(?:(?:shock|falls?|falling|drops?|dropping|contracts?|contracting|rises?|rising|increases?|compression|by|to|of|:|=)\s*)*([+-]?\d+(?:\.\d+)?)\s*%", q)
    reverse_margin = re.search(r"([+-]?\d+(?:\.\d+)?)\s*%\s*(?:operating\s+)?(?:margin|earnings|ebitda)\s*(?:shock|compression|contraction|drop)?", q)
    if margin or reverse_margin:
        matched = margin or reverse_margin
        number = float(matched.group(1))
        if any(word in matched.group(0) for word in ("fall", "drop", "contract", "compression")):
            number = -abs(number)
        values["margin_shock_pct"] = number
    debt = re.search(r"(?:new|incremental)\s+debt\s*(?:of|:|=|to)?\s*(?:rs\.?\s*)?([\d,]+(?:\.\d+)?)\s*(?:crore|cr)\b", q)
    reverse_debt = re.search(r"(?:rs\.?\s*)?([\d,]+(?:\.\d+)?)\s*(?:crore|cr)\s*(?:of\s+)?(?:new|incremental)\s+debt", q)
    if debt or reverse_debt:
        values["incremental_debt_cr"] = float((debt or reverse_debt).group(1).replace(",", ""))
    if "exclude leases" in q or "without leases" in q or "debt-only" in q:
        values["lease_in_coverage"] = False
    elif "include leases" in q or "with leases" in q:
        values["lease_in_coverage"] = True
    cov_values = {}
    for field, pattern in (("dscr_floor", r"dscr\s*(?:floor|:|=|to)?\s*(\d+(?:\.\d+)?)"),
                           ("icr_floor", r"icr\s*(?:floor|:|=|to)?\s*(\d+(?:\.\d+)?)"),
                           ("tol_tnw_ceiling", r"tol/?tnw\s*(?:ceiling|:|=|to)?\s*(\d+(?:\.\d+)?)"),
                           ("minimum_cash_cr", r"minimum cash\s*(?:of|:|=|to)?\s*(?:rs\.?\s*)?([\d,]+(?:\.\d+)?)\s*(?:crore|cr)")):
        matched = re.search(pattern, q)
        if matched:
            cov_values[field] = float(matched.group(1).replace(",", ""))
    if ("margin" in q or "earnings" in q) and not (margin or reverse_margin):
        return {"content": "Specify a signed relative margin change, for example 'margin -20%'. Percentage-point margin changes are not supported.", "state": state}
    if re.search(r"\b(new|incremental)\s+debt\b", q) and not (debt or reverse_debt):
        return {"content": "Specify incremental debt in crore, for example 'new debt 10,500 crore'.", "state": state}
    if "percentage point" in q or "pp" in q or "billion" in q or "million" in q:
        return {"content": "Use a relative margin percentage and monetary amounts in crore. Other units are not converted implicitly.", "state": state}
    request = replace(request, **values)
    cov = replace(cov, **cov_values)
    draft = make_draft(entity, request, cov)
    # Validate the typed inputs before presenting an executable confirmation.
    try:
        example = catalog[entity]
        validate_inputs(example["snapshot"], example["debts"], example["leases"], cov, request)
    except ScenarioInputError as exc:
        return {"content": f"Please correct the scenario inputs: {exc}", "state": state}
    state["draft"] = draft
    state.pop("awaiting_company_query", None)
    return {"content": draft_text(draft), "state": state, "draft": draft}
