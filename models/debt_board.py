"""Debt decision narrative. Historical facts and explicit illustrative assumptions only."""

from datetime import datetime
from zoneinfo import ZoneInfo
import math

import pandas as pd
import plotly.graph_objects as go

from helpers import plotly_layout, PRIMARY, SECONDARY


def get_thesis_companies():
    """Company choices must have observations in this deck's frozen vintage."""
    import db
    return db._query("""SELECT c.company_code, c.company_name, c.nse_symbol, c.industry_group
        FROM companies c WHERE EXISTS (SELECT 1 FROM financials f
        WHERE f.company_code = c.company_code AND f.vintage = ?)
        ORDER BY c.company_name, c.company_code""", ["thesis"])


def number(value):
    """Missing/nonfinite inputs must never become a zero or an unlimited capacity."""
    try:
        value = float(value)
        return value if math.isfinite(value) else None
    except (TypeError, ValueError):
        return None


def fmt(value, suffix=""):
    value = number(value)
    return "N/A" if value is None else f"{value:,.2f}{suffix}"


def build_debt_board(company_df, company_info, peers_df, assumptions=None):
    """Return the ordered sections consumed unchanged by both screen and PPTX.

    Input is the thesis database contract: leverage is percent, profitability and
    tangibility are fractions. Monetary inputs retain the source dataset unit.
    No unit or currency conversion is guessed. Peers must match the focal year.
    """
    if company_df.empty:
        raise ValueError("No company observations available.")
    if company_df.year.duplicated().any():
        raise ValueError("Multiple observations per year: select one dataset vintage first.")
    df = company_df.sort_values("year")
    row = df.iloc[-1]
    year = int(row.year)
    has_scenario = assumptions is not None
    a = dict(assumptions or {})
    scenario_type = a.get("scenario_type", "funding") if has_scenario else "historical"
    if scenario_type not in ("funding", "stress", "historical"):
        raise ValueError("Unsupported scenario type")
    funding_supplied = has_scenario and scenario_type == "funding"
    required = ("floating_share", "rate_shock", "earnings_shock", "coverage_floor")
    if funding_supplied:
        required += ("funding_uses", "internal_funding", "new_debt", "new_rate")
    for key in ("funding_uses", "internal_funding", "new_debt", "new_rate", "floating_share", "rate_shock", "earnings_shock", "coverage_floor"):
        a[key] = number(a.get(key))
        if has_scenario and key in required and (a[key] is None or a[key] < 0):
            raise ValueError(f"Invalid assumption: {key}")
    if has_scenario and (not 0 <= a["floating_share"] <= 1 or not 0 <= a["earnings_shock"] <= 1 or a["coverage_floor"] <= 0):
        raise ValueError("Shares and earnings stress must be between 0 and 1; coverage floor must be positive.")
    if not funding_supplied:
        a["funding_uses"] = a["internal_funding"] = None
        a["new_debt"] = a["new_rate"] = 0 if has_scenario else None
    debt, cash, ebit, interest, cfo = (number(row.get(k)) for k in ("borrowings", "cash_holdings", "pbit", "interest_amt", "ncfo"))
    coverage = ebit / interest if ebit is not None and interest is not None and interest > 0 else None
    stage = str(row.get("life_stage", "Unknown"))
    peers = peers_df.copy() if peers_df is not None else pd.DataFrame()
    if not peers.empty:
        peers = peers[(peers.year == year) & (peers.company_code != company_info["code"]) & (peers.life_stage == stage)]
        peers = peers.sort_values("year").drop_duplicates("company_code", keep="last")
    provenance = (
        f"Thesis panel | company {company_info['code']} | FY{year} | "
        f"history {int(df.year.min())}-{year} | {len(peers)} same-year life-stage peers. "
        "Money: source dataset units; confirm currency and scale before a financing decision. "
        "Financial statement basis is not supplied by the panel."
    )
    sections = []

    def add(title, insights, actions=(), tables=(), figs=()):
        sections.append(dict(title=title, insights=list(insights), actions=list(actions),
                             tables=list(tables), figs=list(figs), provenance=provenance))

    facts = pd.DataFrame([
        ("Fiscal year", str(year)), ("Life stage", stage),
        ("Borrowings", fmt(debt)), ("Cash holdings (availability unverified)", fmt(cash)),
        ("Borrowings less reported cash (proxy)", fmt(debt - cash if debt is not None and cash is not None else None)),
        ("PBIT", fmt(ebit)), ("Interest expense", fmt(interest)),
        ("Interest coverage", fmt(coverage, "x")), ("Operating cash flow", fmt(cfo)),
        ("Reported leverage", fmt(row.get("leverage"), "%")),
    ], columns=["Core fact", "Observed value"])
    add("1. Core facts", [f"{company_info['name']}: FY{year} observed financial position.",
        "Reported cash is not assumed to be unrestricted; the net-debt figure is a proxy."],
        ["Confirm reporting basis, monetary units, and data freshness."], [facts])

    gap = max(0, a["funding_uses"] - a["internal_funding"]) if funding_supplied else None
    funding = pd.DataFrame([
        ("Planned uses", a["funding_uses"]), ("Internal funding available", a["internal_funding"]),
        ("External funding gap", gap), ("Proposed new debt", a["new_debt"]),
        ("Residual gap / (surplus)", gap - a["new_debt"] if funding_supplied else None),
    ], columns=["Management input / calculation", "Amount (source units)"])
    if not funding_supplied:
        funding["Amount (source units)"] = "Not supplied"
    add("2. Funding requirement", (["Funding inputs are management assumptions, not measured forecasts.",
        f"External funding gap: {fmt(gap)}; proposed new debt: {fmt(a['new_debt'])}."] if funding_supplied else
        ["No funding proposal supplied. Historical financials do not establish management's future funding plans."]),
        ["Specify the use of proceeds and explain any funding surplus or residual gap."], [funding])

    stage_view = pd.DataFrame({"Year": df.year, "Life stage": df.life_stage,
                              "Operating cash flow": df.get("ncfo"), "Investing cash flow": df.get("ncfi"),
                              "Financing cash flow": df.get("ncff")}).tail(5)
    add("3. Life-stage diagnosis", [f"Latest classification: {stage}. Cash-flow signs inform the Dickinson (2011) framework.",
        "Life stage provides financing context; it does not determine a borrowing limit."],
        ["Explain whether current funding needs follow expansion, refinancing, or cash-flow pressure."], [stage_view])

    missing = ["Debt maturity and principal repayment schedule", "Contractual covenants and definitions",
               "Committed undrawn facilities and unrestricted cash", "Fixed/floating split and reset dates",
               "Currency, security, guarantees and lease obligations", "Forward cash-flow forecast and capex commitments"]
    add("4. Existing debt obligations", [f"Reported borrowings: {fmt(debt)}; interest expense: {fmt(interest)}.",
        "The panel does not provide a verified instrument-level debt schedule."],
        ["Obtain treasury inputs before proposing an executable financing structure."],
        [pd.DataFrame({"Required evidence": missing, "Status": ["Management input required"] * len(missing)})])

    interest_budget = max(0, ebit / a["coverage_floor"] - interest) if has_scenario and ebit is not None and interest is not None and interest >= 0 else None
    capacity_insights = [f"Observed interest coverage: {fmt(coverage, 'x')}. No coverage policy floor supplied.",
        "Principal repayments, forward cash flows and contractual limits are needed to assess serviceable debt."]
    if has_scenario:
        capacity_insights = [f"Observed interest coverage: {fmt(coverage, 'x')}; illustrative policy floor: {a['coverage_floor']:.2f}x.",
        f"Additional annual interest room against that floor: {fmt(interest_budget)}.",
        "This static PBIT test excludes principal repayments and liquidity needs. It is not an approved debt limit."]
    add("5. Debt-service capacity", capacity_insights,
        ["Validate serviceable debt with forecast cash flows, scheduled repayments, covenants and a liquidity buffer."],
        [pd.DataFrame([("Interest coverage", fmt(coverage, "x")), ("Debt-service coverage including principal", "Not estimable: repayment schedule missing"),
                       ("Approved incremental debt capacity", "Not established")], columns=["Capacity measure", "Assessment"])])

    peer_table = pd.DataFrame(columns=["Metric", "Company", "Peer median"])
    if not peers.empty:
        for col, label, scale in [("leverage", "Leverage (%)", 1), ("profitability", "Operating ROA (%)", 100), ("tangibility", "Tangibility (%)", 100)]:
            values = pd.to_numeric(peers[col], errors="coerce") if col in peers else pd.Series(dtype=float)
            value = number(row.get(col))
            peer_table.loc[len(peer_table)] = [label, fmt(value * scale if value is not None else None), fmt(values.median() * scale)]
    add("6. Peer context", [f"{len(peers)} same-year, same-stage peers from the selected cohort; not an industry-matched credit assessment.",
        "Peer leverage is descriptive evidence. A peer percentile is neither optimal leverage nor unused debt capacity."],
        ["Explain differences in business risk, cash generation, sector and financing access."], [peer_table])

    add("7. Financing alternatives", ["Compare alternatives against the funding purpose, cash-flow timing and financial flexibility."],
        ["Obtain indicative terms and compare total costs before selecting an instrument."],
        [pd.DataFrame([
            ("Internal funds", "Avoid new interest", "Preserve minimum liquidity"),
            ("New term debt", "Match long-lived funding needs", "Check serviceability, price and covenants"),
            ("Refinancing", "Address maturity concentration", "Confirm access and fees; does not itself create earnings"),
            ("Equity / asset monetisation", "Reduce fixed debt-service burden", "Assess dilution, execution and lost future cash flows"),
            ("Phase / defer investment", "Reduce immediate funding need", "Assess strategic and operating consequences"),
        ], columns=["Alternative", "Potential role", "Decision condition"])])

    scenario_rows = []
    new_interest = a["new_debt"] * a["new_rate"] / 100 if funding_supplied else 0
    cases = [("Observed baseline", False, False)]
    if funding_supplied:
        cases += [("Proposed funding", True, False), ("Combined downside", True, True)]
    elif has_scenario:
        cases += [("Existing debt downside", False, True)]
    for label, include_new, shocked in cases:
        adj_ebit = ebit * (1 - a["earnings_shock"] if shocked else 1) if ebit is not None else None
        # Existing floating share is explicit. New debt is fully exposed in the stress.
        shock_cost = ((debt * a["floating_share"] + a["new_debt"]) * a["rate_shock"] / 10000) if shocked and debt is not None and debt >= 0 else (None if shocked else 0)
        adj_interest = interest + (new_interest if include_new else 0) + shock_cost if interest is not None and interest >= 0 and shock_cost is not None else None
        cov = adj_ebit / adj_interest if adj_ebit is not None and adj_interest is not None and adj_interest > 0 else None
        scenario_rows.append([label, adj_ebit, adj_interest, cov,
                              "No policy floor supplied" if not has_scenario else ("Not estimable" if cov is None else ("Below policy floor" if cov < a["coverage_floor"] else "Within policy floor"))])
    scenario = pd.DataFrame(scenario_rows, columns=["Scenario", "PBIT", "Annual interest", "Coverage (x)", "Illustrative policy test"])
    proposed = scenario_rows[1][3] if funding_supplied else coverage
    stress = scenario_rows[-1][3] if has_scenario else None
    break_decline = None
    comparison_interest = scenario_rows[1][2] if funding_supplied else interest
    if has_scenario and ebit is not None and ebit > 0 and comparison_interest is not None and comparison_interest > 0:
        break_decline = max(0, 1 - a["coverage_floor"] * comparison_interest / ebit) * 100
    chart = go.Figure()
    chart.add_trace(go.Bar(x=scenario.Scenario, y=scenario["Coverage (x)"], marker_color=[PRIMARY, SECONDARY, "#D97706"]))
    if has_scenario:
        chart.add_hline(y=a["coverage_floor"], line_dash="dot", annotation_text="Illustrative policy floor")
    chart.update_layout(**plotly_layout("Coverage under the proposed funding and combined downside" if funding_supplied else "Existing debt coverage under stress", height=340), yaxis_title="Coverage (x)")
    scenario_insights = ["No optional scenario applied. Only observed historical coverage is shown; no rate, floating-share or earnings assumptions have been inferred."]
    if has_scenario:
        scenario_insights = [
        f"Assumptions: new debt {fmt(a['new_debt'])}; annual rate {a['new_rate']:.2f}%; existing floating share {a['floating_share']:.0%}; rate shock +{a['rate_shock']:.0f} bps; PBIT decline {a['earnings_shock']:.0%}.",
        f"PBIT decline to reach the policy floor after proposed funding, without a rate shock: {fmt(break_decline, '%')}. Zero means at or below the floor already.",
        "Static illustration: no growth benefit, tax benefit, principal amortisation, fees or refinancing assumed. New debt, if proposed, is fully exposed to the stressed rate."]
        if not funding_supplied:
            scenario_insights[0] = f"Existing debt only: floating share {a['floating_share']:.0%}; rate shock +{a['rate_shock']:.0f} bps; PBIT decline {a['earnings_shock']:.0%}. No new borrowing proposed."
            scenario_insights[1] = f"PBIT decline to reach the selected policy floor at unchanged rates: {fmt(break_decline, '%')}. Zero means at or below the floor already."
    add("8. Scenarios and failure points", scenario_insights,
        ["Run a forecast cash-flow and liquidity stress before commitment."], [scenario], [chart] if has_scenario else [])

    if not has_scenario:
        posture = "No funding proposal or stress assumptions supplied. Review the historical position and evidence gaps before deciding whether to develop a financing proposal."
    elif not funding_supplied:
        posture = "Existing debt stress is not estimable from the available inputs." if stress is None else ("Existing debt falls below the selected policy floor under stress." if stress < a["coverage_floor"] else "Existing debt meets the selected coverage floor in this illustration; no new borrowing has been assessed.")
    elif proposed is None or stress is None:
        posture = "Insufficient evidence to assess the proposed funding."
    elif proposed < a["coverage_floor"] or stress < a["coverage_floor"]:
        posture = "Rework the funding proposal: at least one illustrative coverage test falls below the selected policy floor."
    else:
        posture = "The proposal passes the selected interest-coverage illustrations; full debt-capacity approval remains conditional on missing treasury evidence."
    add("9. Proposed debt strategy" if funding_supplied else "9. Debt strategy review", [posture, "A passing interest test does not establish lender appetite, covenant compliance or a credit rating."],
        ["Compare a lower debt amount, phased spending, alternative funding or refinancing as appropriate.",
         "Confirm the funding purpose, contractual terms and forward liquidity before recommending execution."])

    add("10. Board decision and monitoring", ["Decision requested: review the illustrative funding approach and commission the evidence needed for a financing approval." if funding_supplied else "Decision requested: review the observed financial position and commission any additional treasury evidence needed.",
        "This historical-panel deck does not authorise borrowing."],
        ["Assign owners and dates; return to the board with an executable proposal."],
        [pd.DataFrame([
            ("Validate sources and uses / forecasts", "CFO / FP&A", "Before financing approval"),
            ("Confirm debt schedule, facilities and covenants", "Treasury / legal", "Before financing approval"),
            ("Obtain and compare funding terms", "Treasury", "Before execution"),
            (f"Monitor coverage against selected {a['coverage_floor']:.2f}x floor and liquidity" if has_scenario else "Agree monitoring limits after reviewing cash flows and contractual terms", "CFO / treasury", "At each management reporting cycle"),
        ], columns=["Action", "Proposed owner", "Review point"])])
    return dict(sections=sections, assumptions=a if has_scenario else None, scenario_type=scenario_type, provenance=provenance,
                generated_at=datetime.now(ZoneInfo("Asia/Kolkata")).isoformat(timespec="seconds"))
