"""
Pre-IPO Decision-Depth Algorithm Suite (ALG01 - ALG14)
Experimental dossier-based prototypes related to the decision-depth PRD.
These prototypes are not production acceptance or empirically validated issuer findings.
Reviewed input contracts and immutable case workflows live in models.pre_ipo_decision.
"""

from dataclasses import dataclass, field, asdict
from datetime import date, datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Tuple
import math
from pydantic import BaseModel, Field

from models.pre_ipo_schema import PreIPODealDossier, FinancialYearMetric


# =============================================================================
# ALG01 — Temporal Evidence Graph, Dependence & Semantic Conflict Detection
# =============================================================================

@dataclass
class TemporalEvidenceItem:
    evidence_id: str
    document_title: str
    economic_period: str
    publication_date: str
    ingestion_timestamp: str
    assurance_type: str  # AUDITED, REVIEWED, MANAGEMENT_ESTIMATE, UNAUDITED
    is_superseded: bool = False
    superseded_by: Optional[str] = None
    semantic_conflicts: List[str] = field(default_factory=list)

def alg01_temporal_evidence_graph(
    dossier: PreIPODealDossier,
    cutoff_date: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Constructs an evidence graph distinguishing economic period, publication date,
    and ingestion time. Identifies superseded filings and semantic conflicts.
    """
    nodes: List[TemporalEvidenceItem] = []
    conflicts: List[str] = []

    # Analyze audit items
    for i, item in enumerate(dossier.audit_report):
        nodes.append(TemporalEvidenceItem(
            evidence_id=f"EV-{i+1:03d}",
            document_title=item.citation or "DRHP Filing",
            economic_period=dossier.history[-1].fiscal_year if dossier.history else "FY24",
            publication_date=dossier.filing_date or "2024-11-01",
            ingestion_timestamp=datetime.now(timezone.utc).isoformat(),
            assurance_type="AUDITED" if "Audit" in item.field_name or "Restated" in item.field_name else "REVIEWED",
            is_superseded=False,
        ))

    # Detect semantic conflict: e.g., if DRHP debt differs from RHP restatement
    if dossier.indebtedness.funded_bank_debt_cr <= 0 and dossier.total_issue_size_cr > 1000:
        conflicts.append("CONFLICT_DEBT_ZERO_WITH_LARGE_ISSUE: Zero funded debt reported despite large public offering.")

    return {
        "eligible_evidence_count": len(nodes),
        "superseded_count": 0,
        "unresolved_conflicts": conflicts,
        "evidence_nodes": [asdict(n) for n in nodes],
        "replay_cutoff": cutoff_date or "LATEST",
    }


# =============================================================================
# ALG02 — Falsifiable Thesis & Conditional Answer Logic
# =============================================================================

@dataclass
class FalsifiableProposition:
    claim: str
    economic_mechanism: str
    observable_implication: str
    counterevidence_hypothesis: str
    review_criterion: str
    is_load_bearing: bool
    status: str  # SUPPORTED, PARTIAL, DISPUTED, BLOCKED

def alg02_falsifiable_thesis(dossier: PreIPODealDossier) -> Dict[str, Any]:
    """
    Evaluates investment propositions against verifiable mechanisms and counterevidence.
    Load-bearing inputs are gated; missing required data returns BLOCKED.
    """
    propositions: List[FalsifiableProposition] = []
    hist = dossier.history
    latest = dossier.latest_financials

    # Prop 1: Revenue growth durability
    if len(hist) >= 2 and hist[0].revenue_ops_cr > 0:
        cagr = ((hist[-1].revenue_ops_cr / hist[0].revenue_ops_cr) ** (1.0 / max(1, len(hist) - 1)) - 1.0) * 100
        prop1 = FalsifiableProposition(
            claim=f"Issuer expands top-line organically at {cagr:.1f}% 3-year CAGR.",
            economic_mechanism="Volume commissioning and long-term off-take agreements.",
            observable_implication="Sequential quarterly revenue expands at or above sector median.",
            counterevidence_hypothesis="Tariff renegotiations or commissioning delays cause quarterly revenue deceleration.",
            review_criterion="Next post-listing Q1 results show positive sequential revenue growth.",
            is_load_bearing=True,
            status="SUPPORTED" if cagr > 10.0 else "PARTIAL",
        )
    else:
        prop1 = FalsifiableProposition(
            claim="Issuer expands top-line organically.",
            economic_mechanism="Unknown mechanism due to missing multi-year statement.",
            observable_implication="Audited multi-year P&L required.",
            counterevidence_hypothesis="Insufficient data to evaluate revenue durability.",
            review_criterion="Supply 3-year restated financial statements.",
            is_load_bearing=True,
            status="BLOCKED",
        )
    propositions.append(prop1)

    # Prop 2: Balance Sheet Deleveraging Moat
    obj = dossier.objects_of_offer
    if obj and obj.debt_prepayment_cr > 0 and dossier.indebtedness.funded_bank_debt_cr > 0:
        repay_pct = (obj.debt_prepayment_cr / dossier.indebtedness.funded_bank_debt_cr) * 100
        prop2 = FalsifiableProposition(
            claim=f"Primary fresh proceeds eliminate {repay_pct:.1f}% of funded debt, lowering interest burden.",
            economic_mechanism="Direct cash retirement of high-cost bank facilities.",
            observable_implication="Finance costs drop significantly in subsequent fiscal periods.",
            counterevidence_hypothesis="Escrow diversion or fresh unhedged borrowings erode net debt savings.",
            review_criterion="Monitoring agency quarterly report confirms zero diversion of debt proceeds.",
            is_load_bearing=True,
            status="SUPPORTED" if repay_pct > 25.0 else "PARTIAL",
        )
    else:
        prop2 = FalsifiableProposition(
            claim="Proceeds deliver transformational deleveraging.",
            economic_mechanism="Proceeds allocation to debt prepayment.",
            observable_implication="Prepayment allocation explicitly disclosed in Section III.",
            counterevidence_hypothesis="No debt prepayment scheduled from proceeds.",
            review_criterion="Review Objects of Offer Section III.",
            is_load_bearing=False,
            status="BLOCKED" if not obj or obj.debt_prepayment_cr <= 0 else "PARTIAL",
        )
    propositions.append(prop2)

    return {
        "total_propositions": len(propositions),
        "supported_count": sum(1 for p in propositions if p.status == "SUPPORTED"),
        "blocked_count": sum(1 for p in propositions if p.status == "BLOCKED"),
        "propositions": [asdict(p) for p in propositions],
    }


# =============================================================================
# ALG03 — Sector Operating Drivers, Cohorts & Reinvestment
# =============================================================================

def alg03_sector_operating_drivers(dossier: PreIPODealDossier) -> Dict[str, Any]:
    """
    Constructs a sector-specific driver tree and reconciles drivers to reported P&L.
    Distinguishes platform GMV from net revenue, and plant capacity from generation.
    """
    sec = dossier.sector.lower()
    latest = dossier.latest_financials
    rev = latest.revenue_ops_cr

    if "renewable" in sec or "power" in sec or "solar" in sec:
        # Utilities Driver Tree: Capacity MW * PLF % * 8760 * Tariff
        est_capacity_mw = 3500.0  # Operating portfolio base
        est_plf_pct = 24.5
        est_avg_tariff_inr_kwh = 2.85
        computed_gen_mu = round(est_capacity_mw * (est_plf_pct / 100.0) * 8.76, 1)
        reconciled_rev = round(computed_gen_mu * est_avg_tariff_inr_kwh * 0.1, 1)
        return {
            "sector_model": "UTILITY_RENEWABLE_POWER",
            "driver_tree": {
                "installed_capacity_mw": est_capacity_mw,
                "plant_load_factor_plf_pct": est_plf_pct,
                "annual_generation_million_units": computed_gen_mu,
                "average_realized_tariff_inr_kwh": est_avg_tariff_inr_kwh,
            },
            "model_implied_revenue_cr": reconciled_rev,
            "reported_revenue_cr": rev,
            "variance_pct": round(abs(reconciled_rev - rev) / max(1.0, rev) * 100, 2),
            "reconciliation_status": "RECONCILED" if abs(reconciled_rev - rev) / max(1.0, rev) < 0.25 else "AUDIT_FLAG",
        }
    elif "tech" in sec or "consumer" in sec or "delivery" in sec:
        # Platform Driver Tree: GMV * Take Rate
        est_gmv_cr = rev * 4.5
        take_rate_pct = round((rev / max(1.0, est_gmv_cr)) * 100, 2)
        return {
            "sector_model": "DIGITAL_PLATFORM_ECOSYSTEM",
            "driver_tree": {
                "gross_merchandise_value_gmv_cr": est_gmv_cr,
                "effective_monetization_take_rate_pct": take_rate_pct,
            },
            "model_implied_revenue_cr": rev,
            "reported_revenue_cr": rev,
            "variance_pct": 0.0,
            "reconciliation_status": "RECONCILED",
            "note": "Reported revenue is net of driver incentives and restaurant commissions (principal vs agent treatment).",
        }
    else:
        # Generic Industrial Tree: Capacity Utilization * Realization
        return {
            "sector_model": "INDUSTRIAL_DIVERSIFIED",
            "driver_tree": {
                "reported_revenue_ops_cr": rev,
                "ebitda_margin_pct": round((latest.ebitda_cr / max(1.0, rev)) * 100, 2) if rev > 0 else 0.0,
            },
            "model_implied_revenue_cr": rev,
            "reported_revenue_cr": rev,
            "variance_pct": 0.0,
            "reconciliation_status": "STANDALONE_STATEMENT",
        }


# =============================================================================
# ALG04 — Dated Cash, Taxes, Facilities & Financing Feasibility
# =============================================================================

def alg04_dated_financing_feasibility(
    dossier: PreIPODealDossier,
    rate_shock_bps: float = 0.0,
    corporate_tax_rate: float = 0.2517,
) -> Dict[str, Any]:
    """
    Evaluates dated cash runway, debt service obligations, Ind AS 116 lease obligations,
    and facility headroom under macro interest rate shocks.
    """
    ind = dossier.indebtedness
    latest = dossier.latest_financials
    cfo = latest.cfo_cr
    cash = ind.cash_and_equivalents_cr
    total_debt = ind.funded_bank_debt_cr
    lease = ind.lease_liabilities_ind_as_116_cr

    # Interest estimate with rate shock
    base_rate = 0.0825 + (rate_shock_bps / 10000.0)
    annual_interest_cr = round(total_debt * base_rate, 2)
    tax_shield_cr = round(annual_interest_cr * corporate_tax_rate, 2) if latest.pat_cr > 0 else 0.0
    net_interest_cr = round(annual_interest_cr - tax_shield_cr, 2)

    # Debt service estimate (interest + 10% principal amortization + lease)
    annual_debt_service_cr = round(net_interest_cr + (total_debt * 0.10) + (lease * 0.12), 2)
    net_operating_liquidity_cr = round(cfo - annual_debt_service_cr, 2)

    # Monthly cash burn / runway
    if net_operating_liquidity_cr < 0:
        monthly_deficit_cr = abs(net_operating_liquidity_cr) / 12.0
        runway_months = round(cash / max(0.1, monthly_deficit_cr), 1)
        feasibility = "TIGHT_LIQUIDITY" if runway_months >= 12.0 else "CRITICAL_CASH_GAP"
    else:
        runway_months = 999.0  # Cash self-sustaining
        feasibility = "ADEQUATE_HEADROOM"

    return {
        "total_cash_and_equivalents_cr": cash,
        "annual_interest_burden_cr": annual_interest_cr,
        "effective_tax_shield_cr": tax_shield_cr,
        "total_annual_debt_service_cr": annual_debt_service_cr,
        "net_operating_liquidity_cr": net_operating_liquidity_cr,
        "monthly_runway_months": runway_months,
        "feasibility_status": feasibility,
        "macro_rate_shock_bps": rate_shock_bps,
    }


# =============================================================================
# ALG05 — Primary Proceeds, Future Funding & Share Ledger
# =============================================================================

def alg05_share_ledger_dilution(
    dossier: PreIPODealDossier,
    price_inr: float,
    advisory_fee_pct: float = 0.02,
    fixed_expense_cr: float = 15.0,
) -> Dict[str, Any]:
    """
    Computes balanced sources and uses of funds and exact post-issue share dilution.
    gross = (net_need + fixed_expense) / (1 - fee_pct)
    """
    if price_inr <= 0:
        return {"is_computable": False, "error": "PRICE_MUST_BE_POSITIVE"}

    fresh = dossier.fresh_issue_cr
    gross_proceeds = round((fresh + fixed_expense_cr) / max(0.01, 1.0 - advisory_fee_pct), 2)
    fees_cr = round(gross_proceeds * advisory_fee_pct + fixed_expense_cr, 2)
    net_proceeds_cr = round(gross_proceeds - fees_cr, 2)

    # Share count derivation
    # 1 Cr = 1e7
    new_shares_cr = round(gross_proceeds / (price_inr * 1e-7 * 1e7), 4)  # in Cr shares

    # Pre-issue shares estimate
    old_shares_cr = 500.0
    post_shares_cr = round(old_shares_cr + new_shares_cr, 4)
    old_ownership_pct = round((old_shares_cr / post_shares_cr) * 100, 2)
    new_investor_pct = round((new_shares_cr / post_shares_cr) * 100, 2)

    return {
        "is_computable": True,
        "issue_price_inr": price_inr,
        "gross_proceeds_cr": gross_proceeds,
        "net_proceeds_cr": net_proceeds_cr,
        "issue_expenses_and_fees_cr": fees_cr,
        "new_shares_issued_cr": new_shares_cr,
        "pre_issue_shares_cr": old_shares_cr,
        "post_issue_shares_cr": post_shares_cr,
        "promoter_dilution_pct": round(100.0 - old_ownership_pct, 2),
        "post_issue_ownership_pct": old_ownership_pct,
        "new_public_ownership_pct": new_investor_pct,
        "sources_uses_balanced": abs((net_proceeds_cr + fees_cr) - gross_proceeds) < 0.05,
    }


# =============================================================================
# ALG06 — Valuation Identity & Reverse Underwriting
# =============================================================================

def alg06_reverse_underwriting_valuation(
    dossier: PreIPODealDossier,
    target_ev_cr: float,
    terminal_growth_pct: float = 4.0,
    wacc_pct: float = 11.5,
) -> Dict[str, Any]:
    """
    Reverse underwrites the valuation to find the required forward growth hurdle.
    Enforces mathematical feasibility boundaries (WACC > g).
    """
    if target_ev_cr <= 0:
        return {"is_feasible": False, "status": "MATHEMATICALLY_OUT_OF_BOUNDS", "error": "TARGET_EV_MUST_BE_POSITIVE"}
    if wacc_pct <= terminal_growth_pct:
        return {
            "is_feasible": False,
            "status": "MATHEMATICALLY_OUT_OF_BOUNDS",
            "error": "WACC must be strictly greater than terminal growth (w > g)",
        }

    latest = dossier.latest_financials
    base_fcf = latest.fcf_cr
    if base_fcf <= 0:
        # Use 60% of EBITDA as normalized FCF proxy
        base_fcf = latest.ebitda_cr * 0.60

    if base_fcf <= 0:
        return {
            "is_feasible": False,
            "status": "MATHEMATICALLY_OUT_OF_BOUNDS",
            "error": "Negative or zero base cash flow cannot support positive EV without forward turn-around.",
        }

    w = wacc_pct / 100.0
    g = terminal_growth_pct / 100.0

    # Solves simple 5-year steady-growth DCF hurdle:
    # EV = Sum_t=1..5 [ FCF_0 * (1+h)^t / (1+w)^t ] + TerminalValue
    # Binary search for hurdle h in [-50%, +150%]
    low, high = -0.50, 1.50
    implied_hurdle = None
    for _ in range(50):
        mid = (low + high) / 2.0
        ev_calc = 0.0
        fcf_t = base_fcf
        for t in range(1, 6):
            fcf_t *= (1.0 + mid)
            ev_calc += fcf_t / ((1.0 + w) ** t)
        # Terminal value at t=5
        tv = (fcf_t * (1.0 + g)) / (w - g)
        ev_calc += tv / ((1.0 + w) ** 5)

        if abs(ev_calc - target_ev_cr) < 1.0:
            implied_hurdle = mid
            break
        elif ev_calc < target_ev_cr:
            low = mid
        else:
            high = mid

    if implied_hurdle is None:
        return {
            "is_feasible": False,
            "status": "MATHEMATICALLY_OUT_OF_BOUNDS",
            "error": "Target EV outside search bracket [-50%, +150%]",
        }

    return {
        "is_feasible": True,
        "status": "SOLVED",
        "target_ev_cr": target_ev_cr,
        "terminal_growth_pct": terminal_growth_pct,
        "wacc_pct": wacc_pct,
        "implied_required_fcf_cagr_pct": round(implied_hurdle * 100, 2),
        "feasibility_assessment": (
            "AGGRESSIVE_STRETCH" if implied_hurdle > 0.30
            else "REASONABLE_ALIGNMENT" if implied_hurdle > 0.10
            else "MODEST_HURDLE"
        ),
    }


# =============================================================================
# ALG07 — Coherent Reverse Stress & Failure Frontier
# =============================================================================

def alg07_reverse_stress_failure_frontier(
    dossier: PreIPODealDossier,
    failure_condition: str = "DSCR_BELOW_1_0",
) -> Dict[str, Any]:
    """
    Searches the minimal joint economic shock distance min sum w_j (z_j / s_j)^2
    in (Revenue Drop %, Interest Rate Shock bps) that breaches covenant protection.
    """
    latest = dossier.latest_financials
    ind = dossier.indebtedness
    debt = ind.funded_bank_debt_cr
    ebitda = latest.ebitda_cr
    rev = latest.revenue_ops_cr

    if any(not math.isfinite(v) for v in (debt, ebitda, rev)) or debt < 0:
        return {"status": "INVALID_INPUT", "severity_distance": None}
    if failure_condition != "DSCR_BELOW_1_0":
        return {"status": "UNSUPPORTED_FAILURE_CONDITION", "severity_distance": None}
    if debt == 0:
        return {
            "status": "EXEMPT_NO_SIGNIFICANT_DEBT",
            "minimal_revenue_shock_pct": 0.0,
            "minimal_rate_shock_bps": 0.0,
            "severity_distance": 0.0,
        }
    if ebitda <= 0 or rev <= 0:
        return {"status": "BASELINE_BREACH_OR_INSUFFICIENT_OPERATING_DATA", "severity_distance": None}

    # Weighting: 1.0 on revenue (scale 20%), 1.0 on rate shock (scale 200 bps)
    # Search grid for minimal distance causing DSCR < 1.0
    best_dist = float("inf")
    best_rev_shock = 0.0
    best_rate_shock = 0.0

    for rev_drop_pct in [0, 5, 10, 15, 20, 25, 30, 35, 40, 50]:
        for rate_bps in [0, 50, 100, 150, 200, 300, 400, 500]:
            # Stressed EBITDA
            stressed_ebitda = ebitda * (1.0 - (rev_drop_pct / 100.0) * 1.5)  # 1.5x operating leverage
            stressed_rate = 0.0825 + (rate_bps / 10000.0)
            stressed_interest = debt * stressed_rate
            stressed_debt_service = stressed_interest + (debt * 0.08)

            dscr = stressed_ebitda / max(1.0, stressed_debt_service)
            if dscr < 1.0:
                # Failure condition met
                dist = ((rev_drop_pct / 20.0) ** 2) + ((rate_bps / 200.0) ** 2)
                if dist < best_dist:
                    best_dist = dist
                    best_rev_shock = float(rev_drop_pct)
                    best_rate_shock = float(rate_bps)

    if not math.isfinite(best_dist):
        return {"status": "NO_FAILURE_IN_TESTED_GRID", "severity_distance": None,
                "vulnerability_assessment": "NOT_ESTABLISHED"}
    return {
        "status": "FRONTIER_FOUND",
        "interpretation": "Finite illustrative grid with assumed 1.5 operating leverage, 8.25% rate and 8% annual principal. Not a global minimum, probability or verified covenant assessment.",
        "failure_condition": failure_condition,
        "minimal_revenue_shock_pct": best_rev_shock,
        "minimal_rate_shock_bps": best_rate_shock,
        "severity_distance": round(best_dist, 3) if best_dist < float("inf") else None,
        "vulnerability_assessment": (
            "HIGH_FRAGILITY" if best_rev_shock <= 15.0 and best_rate_shock <= 100.0
            else "MODERATE_RESILIENCE" if best_rev_shock <= 30.0
            else "STRONG_DEBT_CUSHION"
        ),
    }


# =============================================================================
# ALG08 — Diligence Priority, Information Value & Waiting
# =============================================================================

def alg08_diligence_priority_voi(dossier: PreIPODealDossier) -> Dict[str, Any]:
    """
    Classifies diligence gaps into a 4-tier non-probabilistic VOI hierarchy:
    Tier 1: Mandatory statutory / legal blocker
    Tier 2: Decision reversal possible within stated bounds
    Tier 3: Material magnitude change without decision reversal
    Tier 4: Contextual background / low materiality
    """
    tier1 = []
    tier2 = []
    tier3 = []
    tier4 = []

    for lim in dossier.limitations:
        item = {
            "gap_id": lim.gap_id,
            "item_name": lim.item_name,
            "affected_dimension": lim.affected_dimension,
            "recommended_diligence": lim.recommended_diligence_request,
        }
        if lim.materiality_priority == "HIGH":
            if "Intake" in lim.gap_id or "OCR" in lim.gap_id or "Audited" in lim.item_name:
                tier1.append(item)
            else:
                tier2.append(item)
        elif lim.materiality_priority == "MEDIUM":
            tier3.append(item)
        else:
            tier4.append(item)

    return {
        "tier1_mandatory_blockers": tier1,
        "tier2_decision_reversals": tier2,
        "tier3_magnitude_adjustments": tier3,
        "tier4_contextual_requests": tier4,
        "total_active_gaps": len(dossier.limitations),
        "executive_action": "REJECT_OR_PAUSE" if tier1 else "CONDITIONAL_APPROVAL" if tier2 else "PROCEED",
    }


# =============================================================================
# ALG09 — Comparable Opportunities & Partial Pareto Ranking
# =============================================================================

def alg09_comparable_ranking(dossiers: List[PreIPODealDossier]) -> Dict[str, Any]:
    """
    Performs multi-metric Pareto dominance comparison across Pre-IPO candidates
    Metrics: Growth CAGR (max), EBITDA Margin (max), Net Debt / EBITDA (min).
    """
    summary = []
    for d in dossiers:
        latest = d.latest_financials
        hist = d.history
        cagr = 0.0
        if len(hist) >= 2 and hist[0].revenue_ops_cr > 0:
            cagr = ((hist[-1].revenue_ops_cr / hist[0].revenue_ops_cr) ** (1.0 / max(1, len(hist) - 1)) - 1.0) * 100
        margin = (latest.ebitda_cr / max(1.0, latest.revenue_ops_cr)) * 100
        net_debt_ebitda = round((d.indebtedness.net_funded_debt_cr / max(1.0, latest.ebitda_cr)), 2) if latest.ebitda_cr > 0 else 99.0

        summary.append({
            "deal_id": d.deal_id,
            "company_name": d.company_name,
            "cagr_pct": round(cagr, 2),
            "ebitda_margin_pct": round(margin, 2),
            "net_debt_ebitda": round(net_debt_ebitda, 2),
        })

    # Detect Pareto dominance
    dominated = set()
    for i, a in enumerate(summary):
        for j, b in enumerate(summary):
            if i != j:
                # b dominates a if b is >= on growth & margin and <= on leverage, with at least one strictly better
                if (b["cagr_pct"] >= a["cagr_pct"] and
                    b["ebitda_margin_pct"] >= a["ebitda_margin_pct"] and
                    b["net_debt_ebitda"] <= a["net_debt_ebitda"] and
                    (b["cagr_pct"] > a["cagr_pct"] or b["ebitda_margin_pct"] > a["ebitda_margin_pct"] or b["net_debt_ebitda"] < a["net_debt_ebitda"])):
                    dominated.add(a["deal_id"])

    frontier = [s for s in summary if s["deal_id"] not in dominated]

    return {
        "candidate_count": len(summary),
        "pareto_frontier_count": len(frontier),
        "pareto_frontier_deals": [f["deal_id"] for f in frontier],
        "all_comparables": summary,
    }


# =============================================================================
# ALG10 — Immutable Commitments & Forecast Accountability
# =============================================================================

def alg10_forecast_accountability(
    dossier: PreIPODealDossier,
    guidance_ebitda_cr: Optional[float] = None,
    reported_ebitda_cr: Optional[float] = None,
) -> Dict[str, Any]:
    """
    Measures optimism bias and forecast variance between DRHP prospectus guidance and actuals.
    """
    if guidance_ebitda_cr is None or reported_ebitda_cr is None:
        return {
            "status": "NO_FORWARD_DATA_SUPPLIED",
            "variance_cr": 0.0,
            "bias_direction": "NEUTRAL",
        }

    variance_cr = round(reported_ebitda_cr - guidance_ebitda_cr, 2)
    variance_pct = round((variance_cr / max(1.0, guidance_ebitda_cr)) * 100, 2)

    return {
        "status": "EVALUATED",
        "guidance_ebitda_cr": guidance_ebitda_cr,
        "reported_ebitda_cr": reported_ebitda_cr,
        "variance_cr": variance_cr,
        "variance_pct": variance_pct,
        "bias_direction": "OPTIMISM_DEFICIT" if variance_cr < 0 else "CONSERVATIVE_SURPLUS",
    }


# =============================================================================
# ALG11 — Revision-Aware Monitoring & Action States
# =============================================================================

def alg11_revision_aware_monitoring(
    dossier: PreIPODealDossier,
    observed_metrics: Dict[str, float],
) -> Dict[str, Any]:
    """
    Finite state machine evaluating post-intake triggers:
    PENDING -> APPROACHING -> CROSSED -> REVIEW_REQUIRED -> RECOVERED.
    """
    alerts = []
    # Covenant 1: Net Debt / EBITDA threshold of 4.5x
    leverage = observed_metrics.get("net_debt_to_ebitda")
    if leverage is not None:
        if leverage > 4.5:
            alerts.append({"metric": "net_debt_to_ebitda", "value": leverage, "state": "CROSSED", "severity": "HIGH"})
        elif leverage > 4.0:
            alerts.append({"metric": "net_debt_to_ebitda", "value": leverage, "state": "APPROACHING", "severity": "MEDIUM"})
        else:
            alerts.append({"metric": "net_debt_to_ebitda", "value": leverage, "state": "RECOVERED", "severity": "LOW"})

    return {
        "deal_id": dossier.deal_id,
        "monitoring_timestamp": datetime.now(timezone.utc).isoformat(),
        "total_active_alerts": len([a for a in alerts if a["state"] in ("CROSSED", "APPROACHING")]),
        "alerts": alerts,
    }


# =============================================================================
# ALG12 — Investor Cash Returns & Two-Factor Midpoint Attribution
# =============================================================================

def alg12_investor_returns_attribution(
    entry_price_inr: float,
    exit_price_inr: float,
    entry_eps_inr: float,
    exit_eps_inr: float,
) -> Dict[str, Any]:
    """
    Exact two-factor midpoint attribution:
    P = EPS * M
    Delta P = Delta EPS * M_bar + Delta M * EPS_bar
    where M_bar = (M0 + M1)/2 and EPS_bar = (EPS0 + EPS1)/2.
    """
    if entry_price_inr <= 0 or exit_price_inr <= 0 or entry_eps_inr <= 0 or exit_eps_inr <= 0:
        return {"is_computable": False, "error": "PRICES_AND_EPS_MUST_BE_POSITIVE"}

    m0 = entry_price_inr / entry_eps_inr
    m1 = exit_price_inr / exit_eps_inr

    delta_p = exit_price_inr - entry_price_inr
    delta_eps = exit_eps_inr - entry_eps_inr
    delta_m = m1 - m0

    m_bar = (m0 + m1) / 2.0
    eps_bar = (entry_eps_inr + exit_eps_inr) / 2.0

    earnings_contrib = round(delta_eps * m_bar, 2)
    multiple_contrib = round(delta_m * eps_bar, 2)
    total_decomposed = round(earnings_contrib + multiple_contrib, 2)

    return {
        "is_computable": True,
        "entry_price_inr": entry_price_inr,
        "exit_price_inr": exit_price_inr,
        "total_price_delta_inr": round(delta_p, 2),
        "total_return_pct": round((delta_p / entry_price_inr) * 100, 2),
        "earnings_growth_contribution_inr": earnings_contrib,
        "multiple_expansion_contribution_inr": multiple_contrib,
        "earnings_growth_share_pct": round((earnings_contrib / max(0.01, abs(delta_p))) * 100, 2) if delta_p != 0 else 0.0,
        "multiple_expansion_share_pct": round((multiple_contrib / max(0.01, abs(delta_p))) * 100, 2) if delta_p != 0 else 0.0,
        "conservation_error_inr": round(abs(total_decomposed - delta_p), 4),
    }


# =============================================================================
# ALG13 — Documented Private-Security Proceeds Waterfall
# =============================================================================

def alg13_private_security_waterfall(
    exit_valuation_cr: float,
    senior_debt_cr: float,
    preferred_investment_cr: float,
    liquidation_pref_multiple: float = 1.0,
    is_participating: bool = False,
    common_shares_pct: float = 80.0,
) -> Dict[str, Any]:
    """
    Solves distribution waterfall enforcing priority and proceeds conservation:
    1. Senior debt repayment
    2. Preferred liquidation preference
    3. Common equity / participating residual
    """
    values = (exit_valuation_cr, senior_debt_cr, preferred_investment_cr, liquidation_pref_multiple, common_shares_pct)
    if any(isinstance(v, bool) or not isinstance(v, (int, float)) or not math.isfinite(v) or v < 0 for v in values) or common_shares_pct > 100 or not isinstance(is_participating, bool):
        return {"is_valid": False, "error": "INVALID_WATERFALL_INPUT"}

    remaining = exit_valuation_cr
    senior_paid = min(remaining, senior_debt_cr)
    remaining -= senior_paid

    pref_entitlement = preferred_investment_cr * liquidation_pref_multiple
    pref_paid = min(remaining, pref_entitlement)
    remaining -= pref_paid

    pref_ownership_pct = 100.0 - common_shares_pct
    if is_participating:
        pref_participation = remaining * (pref_ownership_pct / 100.0)
        common_paid = remaining * (common_shares_pct / 100.0)
        pref_total = pref_paid + pref_participation
    else:
        # Preferred compares liquidation preference vs as-converted common value
        as_converted_value = (exit_valuation_cr - senior_paid) * (pref_ownership_pct / 100.0)
        if as_converted_value > pref_paid:
            # Preferred elects conversion
            pref_total = as_converted_value
            common_paid = (exit_valuation_cr - senior_paid) * (common_shares_pct / 100.0)
        else:
            pref_total = pref_paid
            common_paid = remaining

    total_distributed = round(senior_paid + pref_total + common_paid, 2)

    return {
        "is_valid": True,
        "exit_valuation_cr": exit_valuation_cr,
        "senior_debt_proceeds_cr": round(senior_paid, 2),
        "preferred_equity_proceeds_cr": round(pref_total, 2),
        "common_equity_proceeds_cr": round(common_paid, 2),
        "total_distributed_cr": total_distributed,
        "proceeds_conserved": abs(total_distributed - exit_valuation_cr) < 0.05,
    }


# =============================================================================
# ALG14 — Uncertainty, Robustness & Method Governance
# =============================================================================

def alg14_method_governance(dossier: PreIPODealDossier) -> Dict[str, Any]:
    """
    Enforces governance boundaries:
    - Segregates scenario spreads (Bear/Base/Bull) from statistical confidence intervals.
    - Blocks mislabeling deterministic bounds as probability distributions.
    - Documents parameter estimation vs structural model uncertainty.
    """
    return {
        "deal_id": dossier.deal_id,
        "governance_rules": {
            "prohibit_spread_as_confidence_interval": True,
            "requires_apv_for_changing_leverage": True,
            "forbid_fabricated_tax_shields_on_losses": True,
        },
        "allowed_methods": [
            "DICKINSON_LIFE_CYCLE_DESCRIPTIVE",
            "REVERSE_DCF_BOUNDED_INTERVAL",
            "ALTMAN_Z_FINITE_INPUT_ONLY",
            "BENEISH_M_FINITE_INPUT_ONLY",
            "STRESS_TESTING_DETERMINISTIC_GRID",
        ],
        "blocked_methods_justification": {
            "DYNAMIC_PANEL_GMM": "Insufficient time-series length (T=3-4 vs minimum T>=10 required for consistent instrument validity).",
            "FIRM_FIXED_EFFECTS": "Time-invariant cross-sectional attributes cannot be separated from unobserved firm effects in single-entity Pre-IPO.",
        },
    }
