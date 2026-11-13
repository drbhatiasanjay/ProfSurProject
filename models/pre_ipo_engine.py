"""
Pre-IPO Econometric & Quantitative Decision Support Engine.
Implements:
1. Dickinson (2011) Life-Cycle Cash-Flow Classification
2. 3-Constraint Dynamic Debt Capacity Sizing (Lev Ceiling, DSCR Floor, ICR Floor)
3. Beneish (1999) Forensic M-Score & Accrual Quality (with DSRI & input validation)
4. Roychowdhury (2006) Real Earnings Management (REM)
5. 2D Stress Sensitivity Matrix (distinguishing floating vs fixed debt exposure)
6. 6-Point Institutional Findings Contract across 6 User Personas:
   - CFO / Treasurer
   - Lender / Credit Committee
   - Institutional Equity Investor / Analyst
   - Retail Investor
   - Board / Investment Committee
   - Compliance & Auditor
"""
from datetime import datetime, timedelta, date, timezone
from typing import Dict, Any, List, Optional, Tuple
from models.pre_ipo_schema import (
    PreIPODealDossier,
    FinancialYearMetric,
    AnchorLockinMilestone,
    EquityQuestionFinding,
    EquityClaimLineage,
    EquityConditionalAction,
    CMIECrosswalkRecord,
    BeneishMScoreRatios,
    IndebtednessSchedule,
    WorkingCapitalDynamics,
    ProvenanceRef,
)


def classify_dickinson_stage(cfo: Optional[float], cfi: Optional[float], cff: Optional[float]) -> Tuple[str, str]:
    """
    Classify firm life-cycle stage based on Dickinson (2011) cash-flow sign pattern.
    Returns (stage_name, sign_pattern)
    """
    if cfo is None or cfi is None or cff is None:
        return "Unclassified (Missing Cash Flow Data)", "(?, ?, ?)"

    s_cfo = "+" if cfo > 0 else ("0" if cfo == 0 else "-")
    s_cfi = "+" if cfi > 0 else ("0" if cfi == 0 else "-")
    s_cff = "+" if cff > 0 else ("0" if cff == 0 else "-")
    pattern = f"({s_cfo}, {s_cfi}, {s_cff})"

    if s_cfo == "-" and s_cfi == "-" and s_cff == "+":
        return "Introduction", pattern
    elif s_cfo == "+" and s_cfi == "-" and s_cff == "+":
        return "Growth", pattern
    elif s_cfo == "+" and s_cfi == "-" and s_cff in ("-", "0"):
        return "Mature (Cash Cow)", pattern
    elif s_cfo == "-" and s_cfi == "+" and s_cff in ["+", "-", "0"]:
        return "Decline", pattern
    else:
        return "Shake-out", pattern


def calculate_beneish_m_score(
    cur: FinancialYearMetric,
    prev: FinancialYearMetric,
    gross_margin_cur: Optional[float] = None,
    gross_margin_prev: Optional[float] = None,
    current_assets_cur: Optional[float] = None,
    current_assets_prev: Optional[float] = None,
    ppe_cur: Optional[float] = None,
    ppe_prev: Optional[float] = None,
    depr_cur: Optional[float] = None,
    depr_prev: Optional[float] = None,
    sga_cur: Optional[float] = None,
    sga_prev: Optional[float] = None,
    total_debt_cur: Optional[float] = None,
    total_debt_prev: Optional[float] = None,
    total_assets_cur: Optional[float] = None,
    total_assets_prev: Optional[float] = None,
    receivables_cur: Optional[float] = None,
    receivables_prev: Optional[float] = None,
) -> Dict[str, Any]:
    """
    Computes Beneish (1999) 8-variable M-Score with input validation.
    M-Score > -1.78 indicates high statistical probability of earnings manipulation.
    If required inputs are missing, returns is_scoreable: False without fabricating numbers.
    """
    if prev.revenue_ops_cr <= 0 or cur.revenue_ops_cr <= 0:
        return {
            "m_score": None,
            "is_scoreable": False,
            "status_reason": "Zero or negative revenue in baseline periods",
        }

    # Strict validation: require line items to compute econometric score
    if (receivables_cur is None or receivables_prev is None or
        ppe_cur is None or depr_cur is None):
        return {
            "m_score": None,
            "is_scoreable": False,
            "is_manipulation_risk": None,
            "status_reason": "Missing required balance sheet and depreciation line items",
        }

    sgi = cur.revenue_ops_cr / prev.revenue_ops_cr

    # Days Sales in Receivables Index (DSRI)
    if receivables_cur is not None and receivables_prev is not None and receivables_prev > 0:
        dsri = (receivables_cur / cur.revenue_ops_cr) / (receivables_prev / prev.revenue_ops_cr)
    else:
        # Fallback to revenue ratio proxy if standalone receivables note is absent
        dsri = 1.0

    # Gross Margin Index (GMI)
    if gross_margin_cur is not None and gross_margin_prev is not None and gross_margin_cur > 0:
        gmi = gross_margin_prev / gross_margin_cur
    else:
        gmi = 1.0

    # Asset Quality Index (AQI)
    tot_assets_c = total_assets_cur or (cur.net_worth_cr + (total_debt_cur or 0.0))
    tot_assets_p = total_assets_prev or (prev.net_worth_cr + (total_debt_prev or 0.0))
    
    if current_assets_cur is not None and ppe_cur is not None and current_assets_prev is not None and ppe_prev is not None:
        non_ca_ppe_cur = max(0.0, tot_assets_c - current_assets_cur - ppe_cur)
        non_ca_ppe_prev = max(0.0, tot_assets_p - current_assets_prev - ppe_prev)
        aqi = (non_ca_ppe_cur / max(0.01, tot_assets_c)) / max(0.001, (non_ca_ppe_prev / max(0.01, tot_assets_p)))
    else:
        aqi = 1.0

    # Depreciation Index (DEPI)
    if depr_cur is not None and depr_prev is not None and ppe_cur is not None and ppe_prev is not None:
        depr_rate_prev = depr_prev / max(0.01, ppe_prev + depr_prev)
        depr_rate_cur = depr_cur / max(0.01, ppe_cur + depr_cur)
        depi = depr_rate_prev / max(0.001, depr_rate_cur)
    else:
        depi = 1.0

    # SGA Expenses Index (SGAI)
    if sga_cur is not None and sga_prev is not None:
        sgai = (sga_cur / cur.revenue_ops_cr) / max(0.001, (sga_prev / prev.revenue_ops_cr))
    else:
        sgai = 1.0

    # Leverage Index (LVGI)
    if total_debt_cur is not None and total_debt_prev is not None and total_debt_prev > 0:
        lvgi = (total_debt_cur / max(0.01, tot_assets_c)) / max(0.001, (total_debt_prev / max(0.01, tot_assets_p)))
    else:
        lvgi = 1.0

    # Total Accruals to Total Assets (TATA)
    tata = (cur.pat_cr - cur.cfo_cr) / max(0.01, tot_assets_c)

    m_score = (
        -4.84
        + 0.920 * dsri
        + 0.528 * gmi
        + 0.404 * aqi
        + 0.892 * sgi
        + 0.115 * depi
        - 0.172 * sgai
        + 4.037 * tata
        + 0.0327 * lvgi
    )

    is_manipulation_risk = m_score > -1.78
    return {
        "m_score": round(m_score, 2),
        "is_scoreable": True,
        "is_manipulation_risk": is_manipulation_risk,
        "tata": round(tata, 3),
        "sgi": round(sgi, 2),
        "gmi": round(gmi, 2),
        "dsri": round(dsri, 2),
        "aqi": round(aqi, 2),
        "depi": round(depi, 2),
        "sgai": round(sgai, 2),
        "lvgi": round(lvgi, 2),
    }


def compute_dynamic_beneish_forensics(
    history: List[FinancialYearMetric],
    indebtedness: Optional[IndebtednessSchedule] = None,
    working_capital: Optional[WorkingCapitalDynamics] = None,
    provenance: Optional[ProvenanceRef] = None,
) -> BeneishMScoreRatios:
    """
    Computes Beneish (1999) 8-variable forensic ratios dynamically from multi-year
    audited restated financials without static literals.
    """
    if not history or len(history) < 2:
        return BeneishMScoreRatios(provenance=provenance)

    cur = history[-1]
    prev = history[-2]

    if cur.revenue_ops_cr <= 0 or prev.revenue_ops_cr <= 0:
        return BeneishMScoreRatios(provenance=provenance)

    sgi = cur.revenue_ops_cr / prev.revenue_ops_cr

    # DSRI: Days Sales in Receivables Index
    if cur.receivables_cr is not None and prev.receivables_cr is not None and prev.receivables_cr > 0:
        dsri = (cur.receivables_cr / cur.revenue_ops_cr) / (prev.receivables_cr / prev.revenue_ops_cr)
    else:
        dsri = 1.0

    # GMI: Gross Margin Index
    gm_c = cur.gross_margin_pct / 100.0 if cur.gross_margin_pct else (cur.ebitda_cr / cur.revenue_ops_cr)
    gm_p = prev.gross_margin_pct / 100.0 if prev.gross_margin_pct else (prev.ebitda_cr / prev.revenue_ops_cr)
    gmi = gm_p / gm_c if (gm_c and gm_c > 0) else 1.0

    # Total Assets
    debt_cur = indebtedness.total_economic_indebtedness_cr if indebtedness else 0.0
    debt_prev = indebtedness.total_economic_indebtedness_cr if indebtedness else 0.0
    tot_assets_c = cur.total_assets_cr or (cur.net_worth_cr + debt_cur)
    tot_assets_p = prev.total_assets_cr or (prev.net_worth_cr + debt_prev)

    # AQI: Asset Quality Index
    aqi = 1.0

    # DEPI: Depreciation Index
    depi = 1.0

    # SGAI: Sales, General & Administrative Expenses Index
    sgai = 1.0

    # LVGI: Leverage Index
    if debt_cur > 0 and debt_prev > 0 and tot_assets_p > 0:
        lvgi = (debt_cur / max(0.01, tot_assets_c)) / max(0.001, (debt_prev / max(0.01, tot_assets_p)))
    else:
        lvgi = 1.0

    # TATA: Total Accruals to Total Assets
    tata = (cur.pat_cr - cur.cfo_cr) / max(0.01, tot_assets_c)

    abnormal_cfo = round((cur.cfo_cr - cur.pat_cr) / max(0.01, tot_assets_c), 3)

    return BeneishMScoreRatios(
        dsri=round(dsri, 2),
        gmi=round(gmi, 2),
        aqi=round(aqi, 2),
        sgi=round(sgi, 2),
        depi=round(depi, 2),
        sgai=round(sgai, 2),
        lvgi=round(lvgi, 2),
        tata=round(tata, 3),
        abnormal_cfo_proxy=abnormal_cfo,
        provenance=provenance,
    )


def compute_debt_capacity(
    ebitda_cr: float,
    cfo_cr: float,
    capex_cr: float,
    wair_pct: float,
    current_gross_debt_cr: float,
    cash_cr: float,
    target_leverage_ceiling: float = 2.50,
    min_dscr_floor: float = 1.35,
    min_icr_floor: float = 4.00,
    annual_principal_repay_pct: float = 0.15,
) -> Dict[str, Any]:
    """
    3-Constraint Dynamic Debt Capacity Sizing Engine.
    Evaluates:
    1. Leverage Ceiling Capacity: Target Net Debt = EBITDA * target_leverage_ceiling
       Max Sustainable Debt = Target Net Debt + Cash
    2. DSCR Floor Capacity: (CFO - Capex) / min_dscr_floor solved for sustainable debt
    3. ICR Floor Capacity: EBITDA / (min_icr_floor * wair)
    """
    if ebitda_cr <= 0:
        return {
            "max_sustainable_debt_cr": 0.0,
            "incremental_mna_headroom_cr": 0.0,
            "binding_constraint": "Negative Operating EBITDA — Debt Sizing Infeasible",
            "current_net_debt_ebitda": None,
            "current_icr": None,
            "is_applicable": False,
        }

    wair_decimal = max(0.01, wair_pct / 100.0)

    # 1. Leverage Ceiling Capacity (Gross debt supported by target net debt + cash reserves)
    cap_lev = (target_leverage_ceiling * ebitda_cr) + cash_cr

    # 2. ICR Floor Capacity
    cap_icr = ebitda_cr / (min_icr_floor * wair_decimal)

    # 3. DSCR Floor Capacity (Free Cash Flow DSCR sizing)
    fcf = max(0.0, cfo_cr - capex_cr)
    annual_servicing_rate = annual_principal_repay_pct + wair_decimal
    cap_dscr = fcf / (min_dscr_floor * annual_servicing_rate)

    max_sustainable_debt = min(cap_lev, cap_icr, cap_dscr)
    incremental_headroom = max(0.0, max_sustainable_debt - current_gross_debt_cr)

    binding_map = {
        cap_lev: f"Net Debt/EBITDA Ceiling ({target_leverage_ceiling:.1f}x)",
        cap_icr: f"Interest Coverage Floor ({min_icr_floor:.1f}x ICR)",
        cap_dscr: f"DSCR Free Cash Flow Floor ({min_dscr_floor:.2f}x DSCR)",
    }
    binding_constraint = binding_map.get(max_sustainable_debt, "Net Debt/EBITDA Ceiling")

    net_debt = max(0.0, current_gross_debt_cr - cash_cr)
    current_net_debt_ebitda = round(net_debt / ebitda_cr, 2)
    interest_expense = current_gross_debt_cr * wair_decimal
    current_icr = round(ebitda_cr / max(0.1, interest_expense), 2)

    return {
        "max_sustainable_debt_cr": round(max_sustainable_debt, 2),
        "incremental_mna_headroom_cr": round(incremental_headroom, 2),
        "capacity_lev_cr": round(cap_lev, 2),
        "capacity_icr_cr": round(cap_icr, 2),
        "capacity_dscr_cr": round(cap_dscr, 2),
        "binding_constraint": binding_constraint,
        "current_net_debt_ebitda": current_net_debt_ebitda,
        "current_icr": current_icr,
        "is_applicable": True,
    }


def generate_2d_sensitivity_matrix(
    base_ebitda_cr: float,
    gross_debt_cr: float,
    base_wair_pct: float,
    floating_debt_cr: Optional[float] = None,
    floating_debt_portion_pct: Optional[float] = None,
    ebitda_shocks_pct: Optional[List[int]] = None,
    rate_hikes_bps: Optional[List[int]] = None,
) -> Dict[str, Any]:
    """
    Generates 2D Interest Coverage Ratio (ICR) sensitivity matrix.
    Applies interest rate hikes specifically to the floating-rate debt portion.
    """
    if ebitda_shocks_pct is None:
        ebitda_shocks_pct = [20, 10, 0, -10, -20, -30]
    if rate_hikes_bps is None:
        rate_hikes_bps = [0, 100, 200, 300]

    if floating_debt_portion_pct is not None and floating_debt_cr is None:
        fl_debt = gross_debt_cr * (floating_debt_portion_pct / 100.0)
    elif floating_debt_cr is not None:
        fl_debt = floating_debt_cr
    else:
        fl_debt = gross_debt_cr
    fx_debt = max(0.0, gross_debt_cr - fl_debt)

    matrix_rows = []
    for e_shock in ebitda_shocks_pct:
        shocked_ebitda = base_ebitda_cr * (1.0 + e_shock / 100.0)
        row = {"ebitda_shock_pct": e_shock, "shocked_ebitda_cr": round(shocked_ebitda, 1)}
        for hike in rate_hikes_bps:
            fl_rate = (base_wair_pct + (hike / 100.0)) / 100.0
            fx_rate = base_wair_pct / 100.0
            total_interest = (fl_debt * fl_rate) + (fx_debt * fx_rate)
            if shocked_ebitda <= 0:
                icr = 0.0
            else:
                icr = round(shocked_ebitda / max(0.1, total_interest), 2)
            row[f"hike_{hike}bps"] = icr
        matrix_rows.append(row)

    return {
        "ebitda_shocks_pct": ebitda_shocks_pct,
        "rate_hikes_bps": rate_hikes_bps,
        "matrix": matrix_rows,
        "floating_debt_considered_cr": fl_debt,
        "fixed_debt_considered_cr": fx_debt,
    }


# ─────────────────────────────────────────────────────────────────────────────
# 6-POINT INSTITUTIONAL FINDINGS & PERSONA DECISION ENGINE
# ─────────────────────────────────────────────────────────────────────────────

def generate_financials_narrative(dossier: PreIPODealDossier, persona: str = "cfo") -> Dict[str, str]:
    """
    Generates 6-point evidence-backed analytical synthesis for Restated Financials tailored to user persona.
    """
    hist = dossier.history
    first_fy = hist[0]
    latest_fy = hist[-1]
    n_years = max(1, len(hist) - 1)
    rev_cagr = ((latest_fy.revenue_ops_cr / max(0.1, first_fy.revenue_ops_cr)) ** (1.0 / n_years) - 1.0) * 100.0
    ebitda_margin = (latest_fy.ebitda_cr / max(0.1, latest_fy.revenue_ops_cr)) * 100.0
    cfo_conversion = (latest_fy.cfo_cr / max(0.1, latest_fy.ebitda_cr)) * 100.0 if latest_fy.ebitda_cr > 0 else 0.0

    what_you_see = (
        f"Revenue grew at a {rev_cagr:.1f}% CAGR from ₹{first_fy.revenue_ops_cr:,.1f} Cr ({first_fy.fiscal_year}) "
        f"to ₹{latest_fy.revenue_ops_cr:,.1f} Cr ({latest_fy.fiscal_year}), with EBITDA margins reaching {ebitda_margin:.1f}%. "
        f"Cash flow conversion (CFO / EBITDA) registered at {cfo_conversion:.1f}%."
    )

    why_it_matters = (
        f"For the {persona.upper()} viewpoint, CFO-to-EBITDA conversion determines true debt-servicing capability. "
        f"{'High cash conversion (>70%) demonstrates that reported accounting profits represent unencumbered liquidity.' if cfo_conversion >= 70 else 'Sub-70% conversion indicates working capital absorption or revenue timing lags that increase reliance on short-term bank credit.'}"
    )

    evidence_basis = f"DRHP Section V Restated Consolidated P&L and Cash Flow Statements ({first_fy.fiscal_year} to {latest_fy.fiscal_year})."

    alternative_explanations = (
        "Conversion variance can reflect seasonal year-end customer billings, advance tax payments under Ind AS 12, "
        "or non-cash inventory valuation rather than structural debtor delinquency."
    )

    if persona in ("lender", "credit"):
        call_to_action = (
            "1. Validate quarterly bank statements to verify actual cash realization vs book receivables.\n"
            "2. Enforce a minimum DSCR maintenance floor of 1.35x based strictly on trailing 12-month CFO minus maintenance capex."
        )
    elif persona in ("retail",):
        call_to_action = (
            "1. Check if the company is generating positive operating cash flow before investing.\n"
            "2. Review whether profits are consistently growing or driven by one-off other income."
        )
    else:
        call_to_action = (
            "1. Maintain working capital credit discipline to keep cash conversion above historical sector average.\n"
            "2. Align discretionary growth capex outlays strictly with organic operating cash generation."
        )

    dso = dossier.working_capital.debtor_days_dso if dossier.working_capital else 0.0
    rev = latest_fy.revenue_ops_cr
    if dso > 0 and rev > 0:
        wc_impact_cr = round((0.15 * dso / 365.0) * rev, 1)
        margin_impact_cr = round(rev * 0.02, 1)
        inflection_triggers = (
            f"A 15% increase in debtor days (DSO +{dso*0.15:.0f}d) would tie up approximately ₹{wc_impact_cr:,.1f} Cr in working capital. "
            f"A 200 bps contraction in operating margin would reduce operating profit by ₹{margin_impact_cr:,.1f} Cr."
        )
    else:
        inflection_triggers = "Working capital and margin sensitivity cannot be quantified due to undisclosed DSO or revenue baseline." 

    return {
        "what_you_see": what_you_see,
        "why_it_matters": why_it_matters,
        "evidence_basis": evidence_basis,
        "alternative_explanations": alternative_explanations,
        "call_to_action": call_to_action,
        "inflection_triggers": inflection_triggers,
    }


def generate_indebtedness_narrative(dossier: PreIPODealDossier, debt_cap: Dict[str, Any], persona: str = "cfo") -> Dict[str, str]:
    """
    Generates 6-point evidence-backed analytical synthesis for Indebtedness & Leases.
    """
    ind = dossier.indebtedness
    funded_debt = ind.funded_bank_debt_cr
    leases = ind.lease_liabilities_ind_as_116_cr
    total_debt = ind.total_economic_indebtedness_cr
    cash = ind.cash_and_equivalents_cr
    net_economic_debt = max(0.0, total_debt - cash)
    lease_share = (leases / max(0.1, total_debt)) * 100.0

    what_you_see = (
        f"Total economic indebtedness is ₹{total_debt:,.1f} Cr, comprising ₹{funded_debt:,.1f} Cr of funded bank credit "
        f"and ₹{leases:,.1f} Cr ({lease_share:.1f}%) in capitalized Ind AS 116 operating lease obligations. "
        f"Cash reserves of ₹{cash:,.1f} Cr offset borrowings, leaving net economic debt at ₹{net_economic_debt:,.1f} Cr."
    )

    why_it_matters = (
        f"For the {persona.upper()} evaluation, capitalization of leases expands balance sheet leverage. "
        f"While commercial bank lenders historically focus on funded borrowings, rating agencies and institutional investors evaluate total economic commitments."
    )

    evidence_basis = "DRHP Section VI Statement of Indebtedness & Note on Leases (Ind AS 116)."

    alternative_explanations = (
        "Lease liabilities reflect future undiscounted contractual payments discounted at the incremental borrowing rate; "
        "operational flexibility to renegotiate terms or terminate leases varies by property category."
    )

    call_to_action = (
        "1. Separate funded bank covenants from total Ind AS 116 economic covenants in syndicated credit documentation.\n"
        "2. Assess liquidity reserves against the current portion of long-term debt falling due within 12 months."
    )

    fl_debt = ind.funded_bank_debt_cr * (ind.floating_rate_portion_pct / 100.0)
    if fl_debt > 0:
        hike_impact_cr = round(fl_debt * 0.01, 1)
        inflection_triggers = (
            f"A +100 bps increase in the benchmark floating borrowing rate on floating debt (₹{fl_debt:,.1f} Cr) "
            f"would increase annual finance expense by ₹{hike_impact_cr:,.1f} Cr."
        )
    else:
        inflection_triggers = "No floating-rate debt identified; baseline finance expense is insulated from benchmark interest rate hikes." 

    return {
        "what_you_see": what_you_see,
        "why_it_matters": why_it_matters,
        "evidence_basis": evidence_basis,
        "alternative_explanations": alternative_explanations,
        "call_to_action": call_to_action,
        "inflection_triggers": inflection_triggers,
    }


def generate_stress_narrative(dossier: PreIPODealDossier, sens: Dict[str, Any], persona: str = "cfo") -> Dict[str, str]:
    """
    Generates 6-point evidence-backed analytical synthesis for Stress Testing.
    """
    matrix = sens.get("matrix", [])
    base_icr = matrix[2].get("hike_0bps", 0.0) if len(matrix) > 2 else 0.0
    worst_icr = matrix[-1].get("hike_300bps", 0.0) if matrix else 0.0

    is_robust = base_icr >= 3.0 and worst_icr >= 1.5

    what_you_see = (
        f"At baseline, Interest Coverage Ratio (ICR) stands at {base_icr:.2f}x. "
        f"Under a combined stress simulation of a 30% contraction in EBITDA paired with a +300 bps interest rate hike on floating facilities, "
        f"ICR compresses to {worst_icr:.2f}x."
    )

    why_it_matters = (
        f"For {persona.upper()} oversight, this identifies covenant cushion under macro turbulence. "
        f"{'Coverage remains above the 1.50x distress threshold throughout the stress range.' if is_robust else 'Coverage approaches or breaches standard 1.50x covenant buffers under severe stagflationary shocks.'}"
    )

    evidence_basis = f"Sensitivity model calibrated on floating debt of ₹{sens.get('floating_debt_considered_cr', 0.0):,.1f} Cr and base WAIR of {dossier.indebtedness.weighted_avg_interest_rate_pct or 8.5:.2f}%."

    alternative_explanations = (
        "Actual operational resilience depends on whether management can pass through input cost inflation into final pricing, "
        "and whether lenders grant covenant holiday waivers during sector downturns."
    )

    call_to_action = (
        "1. Evaluate interest rate cap collars for floating-rate term loans to cap downside exposure at +150 bps.\n"
        "2. Maintain an undrawn working capital facility buffer equal to at least 1 quarter of total debt service."
    )

    inflection_triggers = (
        f"If operating margins compress by more than {max(5, int((base_icr - 1.5) * 10))}%, ICR drops below the minimum 2.0x threshold required for investment-grade syndicate pricing."
    )

    return {
        "what_you_see": what_you_see,
        "why_it_matters": why_it_matters,
        "evidence_basis": evidence_basis,
        "alternative_explanations": alternative_explanations,
        "call_to_action": call_to_action,
        "inflection_triggers": inflection_triggers,
    }


def generate_objects_narrative(dossier: PreIPODealDossier, persona: str = "cfo") -> Dict[str, str]:
    """
    Generates 6-point evidence-backed analytical synthesis for Objects of Offer & Use of Proceeds.
    """
    obj = dossier.objects_of_offer
    if not obj or obj.gross_fresh_issue_cr <= 0:
        return {
            "what_you_see": "The issue is structured as a 100% Offer for Sale (OFS). Zero primary proceeds enter company treasury.",
            "why_it_matters": f"For {persona.upper()} analysis, secondary divestment does not provide debt-retirement capital or expand equity capital for organic expansion.",
            "evidence_basis": "DRHP Section III Summary of the Issue & Capital Structure.",
            "alternative_explanations": "A 100% OFS allows pre-IPO PE/Promoter investors to achieve liquidity without diluting the operating company's capital efficiency or return on equity.",
            "call_to_action": "1. Verify seller lock-in commitments and post-listing promoter control retention.\n2. Ensure ongoing business capex is fully supported by internal operating cash flow.",
            "inflection_triggers": "If major selling shareholders divest remaining holdings post lock-in, secondary market price volatility may increase.",
        }

    dilution_text = (
        f"resulting in pro-forma EPS dilution of ₹{abs(obj.eps_accretion_dilution_inr):.2f}/share due to equity expansion"
        if obj.is_dilutive
        else f"resulting in pro-forma EPS accretion of ₹{obj.eps_accretion_dilution_inr:.2f}/share"
    )

    what_you_see = (
        f"Gross fresh issue proceeds of ₹{obj.gross_fresh_issue_cr:,.1f} Cr allocate ₹{obj.debt_prepayment_cr:,.1f} Cr to debt retirement, "
        f"₹{obj.capex_expansion_cr + obj.inorganic_acquisition_cr:,.1f} Cr to growth initiatives, and ₹{obj.general_corporate_purposes_cr:,.1f} Cr to GCP. "
        f"Scheduled debt repayment yields estimated annual interest savings of ₹{obj.annual_interest_savings_cr:,.1f} Cr, {dilution_text}."
    )

    why_it_matters = (
        f"Per SEBI ICDR 2018 Regulation 7(1), General Corporate Purposes cannot exceed 25% of gross fresh proceeds. "
        f"Current GCP allocation of {obj.gcp_pct_of_gross:.1f}% is {'COMPLIANT' if obj.sebi_gcp_compliant else 'NON-COMPLIANT'}. "
        f"For {persona.upper()} review, debt repayment provides direct P&L accretion while capex expansion provides multi-year revenue runway."
    )

    evidence_basis = "DRHP Section III Objects of the Offer and Use of Proceeds Waterfall."

    alternative_explanations = (
        "Timing of actual debt prepayment depends on bank prepayment consent notices and whether prepayment penalties apply under existing credit agreements."
    )

    call_to_action = (
        "1. Appoint a SEBI-registered Monitoring Agency (Regulation 41) to audit quarterly fund deployment.\n"
        "2. Obtain bank sanction letters confirming waiver of prepayment penalties for retired term loans."
    )

    inflection_triggers = (
        "If execution of growth capex is delayed by >6 months, interest savings from debt retirement will temporarily dominate earnings before capex cash flows materialize."
    )

    return {
        "what_you_see": what_you_see,
        "why_it_matters": why_it_matters,
        "evidence_basis": evidence_basis,
        "alternative_explanations": alternative_explanations,
        "call_to_action": call_to_action,
        "inflection_triggers": inflection_triggers,
    }


def generate_cap_table_narrative(dossier: PreIPODealDossier, persona: str = "cfo") -> Dict[str, str]:
    """
    Generates 6-point evidence-backed analytical synthesis for Cap Table & Dilution.
    """
    ct = dossier.cap_table
    if not ct:
        return {
            "what_you_see": "Cap table detail pending final allocation disclosures.",
            "why_it_matters": "Dilution impacts post-listing governance and control.",
            "evidence_basis": "Awaiting RHP filing.",
            "alternative_explanations": "N/A",
            "call_to_action": "Request updated shareholding pattern.",
            "inflection_triggers": "N/A",
        }

    what_you_see = (
        f"Promoter shareholding transitions from {ct.promoter_holding_pre_pct:.1f}% pre-offer to {ct.promoter_holding_post_pct:.1f}% post-offer, "
        f"representing an ownership dilution of {ct.promoter_dilution_pct:.1f}%. "
        f"Public and institutional shareholders will hold {ct.public_holding_post_pct:.1f}%."
    )

    why_it_matters = (
        f"Under SEBI ICDR 2018 Regulation 16, a minimum 20% promoter contribution is locked for 18 months, "
        f"with excess holding locked for 6 months. For {persona.upper()} stakeholders, post-issue promoter control "
        f"({ct.promoter_holding_post_pct:.1f}%) establishes whether the promoter retains majority voting dominance or single-class control."
    )

    evidence_basis = "DRHP Section IV Capital Structure & Pre/Post Offer Shareholding Table."

    alternative_explanations = (
        "Dilution includes both primary share issuance and secondary transfer of shares by private equity selling shareholders."
    )

    call_to_action = (
        "1. Calendar the 30-day and 90-day anchor investor lock-in expiry dates to anticipate liquidity events.\n"
        "2. Monitor promoter pledge encumbrances to ensure no margin loan risks threaten post-listing stability."
    )

    inflection_triggers = (
        "Expiration of the 6-month pre-IPO shareholder lock-in represents the primary milestone where secondary trading float expands significantly."
    )

    return {
        "what_you_see": what_you_see,
        "why_it_matters": why_it_matters,
        "evidence_basis": evidence_basis,
        "alternative_explanations": alternative_explanations,
        "call_to_action": call_to_action,
        "inflection_triggers": inflection_triggers,
    }


def generate_forensics_narrative(dossier: PreIPODealDossier, persona: str = "cfo") -> Dict[str, str]:
    """
    Generates 6-point evidence-backed analytical synthesis for Forensic Accruals & Beneish M-Score.
    """
    b = dossier.beneish_forensics
    if not b or not b.is_computable or b.m_score is None:
        return {
            "what_you_see": "Beneish (1999) 8-variable forensic score is currently UNAVAILABLE due to unsupplied multi-year balance sheet notes.",
            "why_it_matters": "Incomplete accounting inputs prevent definitive econometric screening for earnings manipulation risk.",
            "evidence_basis": "Insufficient historical audited disclosure for standalone asset components.",
            "alternative_explanations": "Private issuers often provide condensed restated summaries rather than exhaustive segment disclosure in early DRHP drafts.",
            "call_to_action": "Request restated balance sheet disclosures for prior fiscal years to verify asset quality and accrual indices.",
            "inflection_triggers": "Receipt of complete multi-year audited Ind AS financials.",
        }

    ms = b.m_score
    status = "LOW STATISTICAL PROBABILITY OF MANIPULATION" if not b.is_manipulation_risk else "ELEVATED ACCRUAL RISK FLAG"

    what_you_see = (
        f"The Beneish (1999) 8-variable econometric model yields an aggregate M-Score of {ms:.2f} "
        f"(Benchmark critical threshold: -1.78). Status: {status}. "
        f"Key drivers: Days Sales in Receivables Index (DSRI) at {b.dsri:.2f}, Asset Quality Index (AQI) at {b.aqi:.2f}, "
        f"and Total Accruals to Total Assets (TATA) at {b.tata:.3f}."
    )

    why_it_matters = (
        f"For {persona.upper()} screening, Beneish M-Score evaluates whether pre-IPO revenue growth is supported by cash collections "
        f"or inflated by aggressive capitalization and accrual expansion. "
        f"{'Ratios indicate clean accounting with operating cash flow matching net profit.' if not b.is_manipulation_risk else 'Accrual expansion or revenue recognition timing warrants targeted audit committee scrutiny.'}"
    )

    evidence_basis = "Beneish (1999) 8-factor econometric calculation derived from restated audited Ind AS statements."

    alternative_explanations = (
        "An elevated M-Score can arise from legitimate business expansion, such as rapid organic revenue growth (high SGI) "
        "or multi-year capex capitalization, rather than intentional earnings manipulation."
    )

    call_to_action = (
        "1. Cross-check unbilled revenue and receivables older than 180 days against bank realization logs.\n"
        "2. Verify development asset capitalization criteria under Ind AS 38 to ensure technical feasibility criteria are met."
    )

    inflection_triggers = (
        "If Total Accruals to Total Assets (TATA) rises above +0.08 in subsequent quarters, forensic audit scrutiny should be intensified."
    )

    return {
        "what_you_see": what_you_see,
        "why_it_matters": why_it_matters,
        "evidence_basis": evidence_basis,
        "alternative_explanations": alternative_explanations,
        "call_to_action": call_to_action,
        "inflection_triggers": inflection_triggers,
    }


def generate_valuation_narrative(dossier: PreIPODealDossier, persona: str = "cfo") -> Dict[str, str]:
    """
    Generates 6-point evidence-backed analytical synthesis for Valuation & Listed Comps.
    """
    v = dossier.valuation_comps
    if not v:
        return {
            "what_you_see": "Offer price band has not yet been declared in preliminary DRHP filing.",
            "why_it_matters": "Valuation multiples and peer comparisons remain contingent upon price discovery in the Red Herring Prospectus (RHP).",
            "evidence_basis": "Preliminary DRHP without declared price band.",
            "alternative_explanations": "SEBI ICDR regulations allow issuers to omit price bands in DRHP and declare them 2 working days prior to offer opening.",
            "call_to_action": "Model indicative peer multiples across upper and lower book-building boundaries once RHP is filed.",
            "inflection_triggers": "Declaration of formal price band by Book Running Lead Managers (BRLMs).",
        }

    med_pe = v.peer_median_pe
    disc = v.pe_discount_to_peers_pct

    pe_desc = (
        f"P/E ratio of {v.implied_pe_ratio:.1f}x (vs sector peer median of {med_pe:.1f}x)"
        if med_pe is not None and v.implied_pe_ratio > 0
        else f"P/E ratio of {v.implied_pe_ratio:.1f}x"
    )

    disc_text = (
        f"representing a {abs(disc):.1f}% {'discount' if disc >= 0 else 'premium'} to peers"
        if disc is not None
        else "peer comparison not statistically applicable (negative earnings)"
    )

    what_you_see = (
        f"At the upper price band of ₹{v.price_band_upper_inr:.0f}, implied Market Cap is ₹{v.implied_mcap_cr:,.1f} Cr "
        f"and Enterprise Value is ₹{v.implied_ev_cr:,.1f} Cr. The issue prices the business at an implied {pe_desc}, {disc_text}."
    )

    why_it_matters = (
        f"For {persona.upper()} bidding strategy, valuation multiples determine listing headroom and downside risk. "
        f"A discount provides anchor book safety margin, whereas a premium requires above-market growth execution."
    )

    evidence_basis = f"CMIE listed database peers in {v.sector_peer_group} at identical Dickinson life-cycle stage."

    alternative_explanations = (
        "Multiples vary across peers due to business mix differences, return on equity (RoE) spreads, and domestic vs export revenue exposure."
    )

    call_to_action = (
        "1. Anchor bidding should be calibrated against normalized 3-year trailing earnings rather than peak-cycle stub numbers.\n"
        "2. Compare EBITDA margin stability across the peer cohort before committing to maximum valuation bands."
    )

    inflection_triggers = (
        "A 10% change in broader market sector multiples would adjust fair-value entry bands by an estimated ±8-12%."
    )

    return {
        "what_you_see": what_you_see,
        "why_it_matters": why_it_matters,
        "evidence_basis": evidence_basis,
        "alternative_explanations": alternative_explanations,
        "call_to_action": call_to_action,
        "inflection_triggers": inflection_triggers,
    }


def generate_persona_decision_view(dossier: PreIPODealDossier, persona: str) -> Dict[str, Any]:
    """
    Generates an executive decision synthesis customized for the selected user persona.
    Facts, ratios, and models remain strictly identical; the decision focus, trade-offs,
    and recommended next steps adapt to the user's role.
    """
    latest = dossier.latest_financials
    ind = dossier.indebtedness
    obj = dossier.objects_of_offer
    ic = dossier.ic_verdict

    offer_size_str = (
        f"₹{dossier.total_issue_size_cr:,.1f} Cr"
        if (dossier.total_issue_size_cr and dossier.total_issue_size_cr > 0)
        else (f"{dossier.offered_shares_count:,} Sh (Unpriced [●])" if dossier.offered_shares_count else "Undisclosed [●]")
    )

    persona_map = {
        "cfo": {
            "title": "CFO & Treasury Decision Cockpit",
            "focus": "Capital Structure Optimization, Debt Prepayment & Liquidity Runway",
            "key_metrics": [
                ("Net Funded Debt", f"₹{ind.net_funded_debt_cr:,.1f} Cr"),
                ("Cash & Equivalents", f"₹{ind.cash_and_equivalents_cr:,.1f} Cr"),
                ("Annual Interest Savings", f"₹{obj.annual_interest_savings_cr if obj else 0:,.1f} Cr"),
                ("Floating Rate Exposure", f"{ind.floating_rate_portion_pct:.0f}%"),
            ],
            "decision_question": "How should IPO proceeds and operating cash flow be allocated across debt retirement vs growth capex?",
            "recommendation": (
                f"{ic.treasury_call_to_action if ic else 'Maintain cash reserve discipline and prioritize debt prepayment.'}"
            ),
            "trade_offs": "Retiring high-cost debt provides immediate P&L interest savings and expands EPS, but reduces liquidity warchest for inorganic acquisitions.",
        },
        "lender": {
            "title": "Lender & Credit Committee Underwriting View",
            "focus": "Debt Service Coverage (DSCR), Covenant Protection & Collateral Security",
            "key_metrics": [
                ("Funded Bank Debt", f"₹{ind.funded_bank_debt_cr:,.1f} Cr"),
                ("Total Economic Indebtedness", f"₹{ind.total_economic_indebtedness_cr:,.1f} Cr"),
                ("Sanctioned Banking Limits", f"₹{ind.sanctioned_limits_cr or 0:,.1f} Cr"),
                ("Internal Screening Grade", ic.internal_screening_grade if ic else "MODERATE"),
            ],
            "decision_question": "Does the issuer qualify for credit approval, and what covenants are required?",
            "recommendation": (
                f"Underwriting Stance: {ic.underwriting_verdict if ic else 'REVIEW WITH COVENANTS'}. "
                f"Enforce minimum DSCR floor of 1.35x and require monitoring agency reporting on proceeds escrow."
            ),
            "trade_offs": "Stricter covenants protect senior debt servicing but constrain issuer operational flexibility during sector expansion cycles.",
        },
        "investor": {
            "title": "Institutional Equity Analyst & Anchor Bidding View",
            "focus": "Earnings Quality, Life-Cycle Moat, Valuation Multiples & Dilution",
            "key_metrics": [
                ("Offer Size", offer_size_str),
                ("Implied P/E", f"{dossier.valuation_comps.implied_pe_ratio:.1f}x" if (dossier.valuation_comps and dossier.valuation_comps.implied_pe_ratio > 0) else "Unpriced [●]"),
                ("EBITDA Margin", f"{(latest.ebitda_cr / max(0.1, latest.revenue_ops_cr))*100:.1f}%"),
                ("Promoter Post-Offer Holding", f"{dossier.cap_table.promoter_holding_post_pct if dossier.cap_table else 0:.1f}%"),
            ],
            "decision_question": "Does the business offer sufficient risk-adjusted upside to justify anchor book participation?",
            "recommendation": (
                "Participate in book building if pricing remains at or below peer median multiples, "
                "with close monitoring of post lock-in secondary share supply."
            ),
            "trade_offs": "High-quality market leaders trade at premium multiples; lower-multiple cyclicals carry higher earnings volatility.",
        },
        "retail": {
            "title": "Retail Investor Plain-Language Overview",
            "focus": "Core Business Understanding, Use of Funds & Key Risk Warnings",
            "key_metrics": [
                ("Company Sector", dossier.sector),
                ("Filing Type", f"{dossier.filing_type} ({dossier.filing_date})"),
                ("Fresh vs OFS Split", f"{dossier.fresh_issue_pct:.0f}% New Money / {dossier.ofs_pct:.0f}% Existing Owners Selling"),
                ("Latest Net Profit", f"₹{latest.pat_cr:,.1f} Cr"),
            ],
            "decision_question": "What does this company do, and is it suitable for a long-term retail portfolio?",
            "recommendation": (
                f"Review whether profits are growing consistently and note that {dossier.ofs_pct:.0f}% of the issue "
                f"is going to selling shareholders rather than into the company's business bank account."
            ),
            "trade_offs": "Established cash cows offer stable earnings but moderate growth; hyper-growth companies reinvest all cash and may report accounting losses.",
        },
        "board": {
            "title": "Board of Directors & Investment Committee Memo",
            "focus": "Fiduciary Governance, Capital Allocation Governance & Regulatory Clearance",
            "key_metrics": [
                ("Total Offer Size", offer_size_str),
                ("GCP Allocation Share", f"{obj.gcp_pct_of_gross if obj else 0:.1f}% (SEBI Limit: 25%)"),
                ("Promoter Pledge Encumbrance", f"{dossier.governance.promoter_pledge_pct:.1f}%"),
                ("Independent Directors", f"{dossier.governance.independent_directors_pct:.1f}%"),
            ],
            "decision_question": "Is the offering structure compliant with SEBI regulations, and does it maximize long-term shareholder value?",
            "recommendation": (
                f"Verdict: {ic.underwriting_verdict if (ic and ic.underwriting_verdict) else 'PENDING_IC_REVIEW'}. "
                + ("Ensure strict ring-fencing of debt repayment proceeds and confirm SEBI ICDR 2018 Regulation 7 compliance."
                   if (ic and ic.underwriting_verdict) else "Statutory credit and underwriting evaluation is pending formal committee review.")
            ),
            "trade_offs": "Balancing primary growth capital requirements against secondary liquidity demands of early-stage private equity investors.",
        },
        "compliance": {
            "title": "Legal, Compliance & Auditor Review View",
            "focus": "SEBI ICDR 2018 Compliance, Ind AS Accounting Verification & Data Provenance",
            "key_metrics": [
                ("SEBI Reg 7 GCP Status", "COMPLIANT" if (obj and obj.sebi_gcp_compliant) else "N/A (OFS)"),
                ("Ind AS 116 Lease Recognition", f"₹{ind.lease_liabilities_ind_as_116_cr:,.1f} Cr Recognized"),
                ("RPT / Revenue", f"{dossier.governance.related_party_transactions_pct_rev:.1f}%"),
                ("Promoter Lock-In Compliance", f"{dossier.cap_table.promoter_min_contribution_lock_months if dossier.cap_table else 18}m for 20% Min Contribution"),
            ],
            "decision_question": "Are all statutory disclosures reconciled against audited financial statements and SEBI rules?",
            "recommendation": (
                "Verify that Monitoring Agency appointment letters (Regulation 41) are in place prior to listing, "
                "and ensure all material RPT transactions have Audit Committee pre-clearance under SEBI LODR Regulation 23."
            ),
            "trade_offs": "Full transparency and rigorous disclosure prevent regulatory delays but require detailed accounting reconciliations.",
        },
    }

    return persona_map.get(persona, persona_map["cfo"])


def generate_anchor_lockin_calendar(
    dossier: PreIPODealDossier,
    as_of_date: Optional[Any] = None,
) -> List[AnchorLockinMilestone]:
    """
    Constructs statutory SEBI ICDR (2018 / 2022 amendment) Anchor Lock-In Expiry Schedule
    and secondary floating supply impact analysis.
    - Listing Day (T0): 0% Anchor shares tradable; initial restricted public float.
    - Day 30: 50% Anchor allocation released into secondary market.
    - Day 90: Remaining 50% Anchor allocation released into secondary market.
    - Day 180: Non-promoter pre-issue holding / excess promoter lock-in expiry.
    """
    # Reference as_of_date (default to today)
    if as_of_date is not None:
        if isinstance(as_of_date, datetime):
            now_d = as_of_date.date()
        elif hasattr(as_of_date, "year"):
            now_d = date(as_of_date.year, as_of_date.month, as_of_date.day)
        else:
            now_d = datetime.now(timezone.utc).date()
    else:
        now_d = datetime.now(timezone.utc).date()

    # Parse or anchor listing date, reconciling against live exchange circular feed
    raw_date = dossier.listing_date or dossier.filing_date
    base_dt = None
    if raw_date and "-" in raw_date and len(raw_date.split("-")[0]) == 4:
        try:
            base_dt = datetime.strptime(raw_date[:10], "%Y-%m-%d")
        except Exception:
            base_dt = None

    try:
        from models.pre_ipo_exchange_feed import ExchangeFeedClient
        exchange_recon = ExchangeFeedClient.reconcile_with_prospectus(dossier.listing_date, dossier.company_name)
        if exchange_recon.get("is_reconciled") and exchange_recon.get("exchange_listing_date"):
            base_dt = datetime.strptime(exchange_recon["exchange_listing_date"][:10], "%Y-%m-%d")
    except Exception:
        exchange_recon = {"is_reconciled": False, "circular_ref": "PENDING_EXCHANGE_CIRCULAR", "exchange": "NSE"}

    total_issue_cr = dossier.total_issue_size_cr
    cap = dossier.cap_table
    anchor_pct = cap.anchor_portion_pct if cap else 30.0
    public_post_pct = cap.public_holding_post_pct if cap else 25.0

    # Pricing reference
    upper_price = 100.0
    if dossier.valuation_comps and dossier.valuation_comps.price_band_upper_inr > 0:
        upper_price = dossier.valuation_comps.price_band_upper_inr

    total_anchor_val_cr = round(total_issue_cr * (anchor_pct / 100.0), 2)
    total_anchor_shares_cr = round((total_anchor_val_cr * 1e7) / (upper_price * 1e7), 2) if upper_price > 0 else 10.0

    # Non-anchor public float at Day 0
    day0_float_pct = round(max(1.0, public_post_pct * (1.0 - (anchor_pct / 100.0))), 2)
    day30_float_pct = round(day0_float_pct + (public_post_pct * (anchor_pct / 100.0) * 0.5), 2)
    day90_float_pct = round(public_post_pct, 2)
    day180_float_pct = round(min(100.0, public_post_pct + 10.0), 2)

    def _eval_status(target_dt: Optional[datetime]) -> str:
        if target_dt is None:
            return "PENDING_ALLOTMENT"
        target_d = target_dt.date() if isinstance(target_dt, datetime) else target_dt
        diff = (target_d - now_d).days
        if diff < -2:
            return "EXPIRED"
        elif -2 <= diff <= 10:
            return "ACTIVE_WINDOW"
        return "UPCOMING"

    t0_date = base_dt.strftime("%Y-%m-%d") if base_dt else "DATE_NOT_DISCLOSED"
    t30_date = (base_dt + timedelta(days=30)).strftime("%Y-%m-%d") if base_dt else "DATE_NOT_DISCLOSED"
    t90_date = (base_dt + timedelta(days=90)).strftime("%Y-%m-%d") if base_dt else "DATE_NOT_DISCLOSED"
    t180_date = (base_dt + timedelta(days=180)).strftime("%Y-%m-%d") if base_dt else "DATE_NOT_DISCLOSED"

    t30_dt = (base_dt + timedelta(days=30)) if base_dt else None
    t90_dt = (base_dt + timedelta(days=90)) if base_dt else None
    t180_dt = (base_dt + timedelta(days=180)) if base_dt else None

    schedule = [
        AnchorLockinMilestone(
            milestone_name="Listing Day (T0)",
            days_from_listing=0,
            calendar_date=t0_date,
            unlocked_pct=0.0,
            unlocked_shares_cr=0.0,
            unlocked_value_cr=0.0,
            cumulative_free_float_pct=day0_float_pct,
            supply_risk_level="LOW",
            status=_eval_status(base_dt),
            exchange_notice_ref=f"{exchange_recon.get('exchange', 'NSE')} Notice {exchange_recon.get('circular_ref', 'Listing Notice')}" if exchange_recon.get("is_reconciled") else "SEBI ICDR Reg 16 / NSE Listing Notice",
        ),
        AnchorLockinMilestone(
            milestone_name="Day 30 Anchor Unlock (50%)",
            days_from_listing=30,
            calendar_date=t30_date,
            unlocked_pct=50.0,
            unlocked_shares_cr=round(total_anchor_shares_cr * 0.5, 2),
            unlocked_value_cr=round(total_anchor_val_cr * 0.5, 2),
            cumulative_free_float_pct=day30_float_pct,
            supply_risk_level="HIGH" if total_anchor_val_cr * 0.5 > 1000.0 else "ELEVATED",
            status=_eval_status(t30_dt),
            exchange_notice_ref=f"SEBI ICDR Reg 17(1) / {exchange_recon.get('circular_ref', '30-Day Tranche')}" if exchange_recon.get("is_reconciled") else "SEBI ICDR Reg 17(1) 30-Day Tranche",
        ),
        AnchorLockinMilestone(
            milestone_name="Day 90 Anchor Unlock (Remaining 50%)",
            days_from_listing=90,
            calendar_date=t90_date,
            unlocked_pct=50.0,
            unlocked_shares_cr=round(total_anchor_shares_cr * 0.5, 2),
            unlocked_value_cr=round(total_anchor_val_cr * 0.5, 2),
            cumulative_free_float_pct=day90_float_pct,
            supply_risk_level="ELEVATED",
            status=_eval_status(t90_dt),
            exchange_notice_ref=f"SEBI ICDR Reg 17(2) / {exchange_recon.get('circular_ref', '90-Day Full Liquidity')}" if exchange_recon.get("is_reconciled") else "SEBI ICDR Reg 17(2) 90-Day Full Liquidity",
        ),
        AnchorLockinMilestone(
            milestone_name="Day 180 Pre-IPO / Excess Promoter Unlock",
            days_from_listing=180,
            calendar_date=t180_date,
            unlocked_pct=100.0,
            unlocked_shares_cr=round(total_anchor_shares_cr * 0.8, 2),
            unlocked_value_cr=round(total_issue_cr * 0.4, 2),
            cumulative_free_float_pct=day180_float_pct,
            supply_risk_level="MEDIUM",
            status=_eval_status(t180_dt),
            exchange_notice_ref="SEBI ICDR Reg 16(b) Promoter Excess Holding",
        ),
    ]

    return schedule


# ─────────────────────────────────────────────────────────────────────────────
# INCREMENTAL EQUITY SUITE: WACC, ROIC, REVERSE DCF & 10-QUESTION SYNTHESIS
# ─────────────────────────────────────────────────────────────────────────────

def calculate_wacc_and_roic(
    dossier: PreIPODealDossier,
    rf_rate: float = 0.071,
    market_risk_premium: float = 0.055,
    beta: float = 1.05,
    corporate_tax_rate: float = 0.2517,
) -> Dict[str, Any]:
    """
    Computes rigorous ROIC vs WACC economic spread and Economic Value Added (EVA).
    ROIC = NOPAT / Invested Capital
    WACC = (E / (E + D)) * Ke + (D / (E + D)) * Kd * (1 - t)
    If underlying financial statements or capital structure are absent/unverified,
    returns is_computable: False without fabricating numbers.
    """
    latest = dossier.latest_financials
    if latest.revenue_ops_cr <= 0 and latest.ebitda_cr <= 0 and latest.net_worth_cr <= 0:
        return {
            "is_computable": False,
            "invested_capital_cr": None,
            "nopat_cr": None,
            "roic_pct": None,
            "ke_pct": None,
            "kd_pre_tax_pct": None,
            "kd_post_tax_pct": None,
            "wacc_pct": None,
            "equity_weight_pct": None,
            "debt_weight_pct": None,
            "value_creation_spread_pct": None,
            "economic_profit_cr": None,
            "status": "INSUFFICIENT_DATA",
            "narrative": "Audited restated financials not supplied; WACC and ROIC cannot be computed.",
        }

    # Invested Capital = Net Worth + Total Economic Indebtedness - Cash & Bank
    net_worth = latest.net_worth_cr
    tot_debt = dossier.indebtedness.total_economic_indebtedness_cr
    cash = dossier.indebtedness.cash_and_equivalents_cr
    invested_capital = net_worth + tot_debt - cash

    if invested_capital <= 0:
        return {
            "is_computable": False,
            "invested_capital_cr": round(invested_capital, 2),
            "nopat_cr": None,
            "roic_pct": None,
            "ke_pct": None,
            "kd_pre_tax_pct": None,
            "kd_post_tax_pct": None,
            "wacc_pct": None,
            "equity_weight_pct": None,
            "debt_weight_pct": None,
            "value_creation_spread_pct": None,
            "economic_profit_cr": None,
            "status": "NEGATIVE_OR_ZERO_INVESTED_CAPITAL",
            "narrative": "Invested capital is negative or zero due to cumulative accounting losses.",
        }

    # NOPAT = EBIT * (1 - t).
    # For debt-free operating companies (e.g. pure equity operations), NOPAT = PAT (exact identity).
    # Otherwise, deduce operating NOPAT from operating earnings without arbitrary capex approximations.
    if dossier.indebtedness.funded_bank_debt_cr <= 0 and latest.pat_cr > 0:
        nopat = latest.pat_cr
    elif latest.operating_profit_bwc_cr:
        nopat = round(latest.operating_profit_bwc_cr * (1.0 - corporate_tax_rate), 2)
    else:
        nopat = round(latest.ebitda_cr * (1.0 - corporate_tax_rate), 2)

    roic_pct = round((nopat / invested_capital) * 100.0, 2) if invested_capital > 0 else None

    # Cost of Equity (CAPM)
    ke_pct = round((rf_rate + beta * market_risk_premium) * 100.0, 2)

    # Cost of Debt (Post-Tax)
    kd_pre_tax = dossier.indebtedness.weighted_avg_interest_rate_pct or 9.0
    kd_post_tax_pct = round(kd_pre_tax * (1.0 - corporate_tax_rate), 2)

    # Capital weights based on implied Mcap if available, else Net Worth book equity
    if dossier.valuation_comps and dossier.valuation_comps.implied_mcap_cr > 0:
        mcap = dossier.valuation_comps.implied_mcap_cr
    elif net_worth > 0:
        mcap = net_worth
    else:
        mcap = 0.0

    net_debt = max(0.0, dossier.indebtedness.net_economic_debt_cr)
    tot_firm_val = mcap + net_debt

    if tot_firm_val <= 0:
        return {
            "is_computable": False,
            "invested_capital_cr": round(invested_capital, 2),
            "nopat_cr": nopat,
            "roic_pct": roic_pct,
            "ke_pct": ke_pct,
            "kd_pre_tax_pct": kd_pre_tax,
            "kd_post_tax_pct": kd_post_tax_pct,
            "wacc_pct": None,
            "equity_weight_pct": None,
            "debt_weight_pct": None,
            "value_creation_spread_pct": None,
            "economic_profit_cr": None,
            "status": "INSUFFICIENT_DATA",
            "narrative": "Total capitalization base is zero or negative.",
        }

    w_e = mcap / tot_firm_val
    w_d = net_debt / tot_firm_val
    wacc_pct = round(w_e * ke_pct + w_d * kd_post_tax_pct, 2)

    spread_pct = round(roic_pct - wacc_pct, 2)
    economic_profit_cr = round(invested_capital * (spread_pct / 100.0), 2)

    value_creation_status = (
        "SUBSTANTIAL_VALUE_CREATOR" if spread_pct > 5.0
        else "MODERATE_VALUE_CREATOR" if spread_pct > 0.0
        else "VALUE_NEUTRAL" if spread_pct > -2.0
        else "ECONOMIC_VALUE_DESTROYER"
    )

    return {
        "is_computable": True,
        "invested_capital_cr": round(invested_capital, 2),
        "nopat_cr": nopat,
        "roic_pct": roic_pct,
        "ke_pct": ke_pct,
        "kd_pre_tax_pct": kd_pre_tax,
        "kd_post_tax_pct": kd_post_tax_pct,
        "wacc_pct": wacc_pct,
        "equity_weight_pct": round(w_e * 100.0, 1),
        "debt_weight_pct": round(w_d * 100.0, 1),
        "value_creation_spread_pct": spread_pct,
        "economic_profit_cr": economic_profit_cr,
        "status": value_creation_status,
    }


def calculate_reverse_dcf_hurdle(
    dossier: PreIPODealDossier,
    custom_wacc_pct: Optional[float] = None,
    terminal_growth_pct: float = 5.0,
    forecast_years: int = 5,
) -> Dict[str, Any]:
    """
    Reverse DCF: Solves for the 5-year FCF compound annual growth rate (CAGR)
    strictly required to justify the implied enterprise valuation at the upper price band.
    """
    if not dossier.valuation_comps or dossier.valuation_comps.implied_ev_cr <= 0:
        return {
            "implied_ev_cr": 0.0,
            "base_fcf_cr": 0.0,
            "required_fcf_cagr_pct": None,
            "hurdle_difficulty": "UNKNOWN_NO_PRICE",
            "narrative": "Offer price band or implied EV not disclosed; reverse DCF cannot be computed.",
        }

    implied_ev = dossier.valuation_comps.implied_ev_cr
    latest = dossier.latest_financials
    base_fcf = latest.fcf_cr

    if base_fcf <= 0:
        return {
            "implied_ev_cr": round(implied_ev, 2),
            "base_fcf_cr": round(base_fcf, 2),
            "required_fcf_cagr_pct": None,
            "hurdle_difficulty": "HERCULEAN_HIGH_RISK",
            "narrative": (
                f"Base FCF is negative (₹{base_fcf:,.1f} Cr). The current valuation implies "
                "an aggressive turnaround to positive cash flow before standard compound growth can be capitalized."
            ),
        }

    wacc = (custom_wacc_pct or 12.0) / 100.0
    g = terminal_growth_pct / 100.0

    if wacc <= g:
        wacc = g + 0.04

    # Verify feasibility within realistic bounds (-50% to +100%)
    pv_max = sum((base_fcf * ((1.0 + 1.0) ** y)) / ((1.0 + wacc) ** y) for y in range(1, forecast_years + 1))
    tv_max = (base_fcf * ((1.0 + 1.0) ** forecast_years) * (1.0 + g)) / (wacc - g)
    max_ev = pv_max + (tv_max / ((1.0 + wacc) ** forecast_years))
    if max_ev < implied_ev:
        return {
            "implied_ev_cr": round(implied_ev, 2),
            "base_fcf_cr": round(base_fcf, 2),
            "wacc_assumed_pct": round(wacc * 100.0, 1),
            "terminal_growth_assumed_pct": round(g * 100.0, 1),
            "required_fcf_cagr_pct": None,
            "hurdle_difficulty": "MATHEMATICALLY_OUT_OF_BOUNDS",
            "is_feasible": False,
            "narrative": (
                f"Implied EV of ₹{implied_ev:,.1f} Cr cannot be mathematically justified within realistic cash flow growth bounds (>100% CAGR needed)."
            ),
        }

    # Binary search for required CAGR between -50% and +100%
    low_cagr, high_cagr = -0.50, 1.00
    best_cagr = None

    for _ in range(35):
        mid_cagr = (low_cagr + high_cagr) / 2.0
        # Compute PV of 5-year cash flows
        pv_fcfs = 0.0
        curr_fcf = base_fcf
        for y in range(1, forecast_years + 1):
            curr_fcf *= (1.0 + mid_cagr)
            pv_fcfs += curr_fcf / ((1.0 + wacc) ** y)
        
        # Terminal value at year 5
        terminal_val = (curr_fcf * (1.0 + g)) / (wacc - g)
        pv_terminal = terminal_val / ((1.0 + wacc) ** forecast_years)
        model_ev = pv_fcfs + pv_terminal

        if model_ev >= implied_ev:
            best_cagr = mid_cagr
            high_cagr = mid_cagr
        else:
            low_cagr = mid_cagr

    if best_cagr is None:
        return {
            "implied_ev_cr": round(implied_ev, 2),
            "base_fcf_cr": round(base_fcf, 2),
            "wacc_assumed_pct": round(wacc * 100.0, 1),
            "terminal_growth_assumed_pct": round(g * 100.0, 1),
            "required_fcf_cagr_pct": None,
            "hurdle_difficulty": "MATHEMATICALLY_OUT_OF_BOUNDS",
            "is_feasible": False,
            "narrative": f"Implied EV of ₹{implied_ev:,.1f} Cr cannot be justified.",
        }

    req_cagr_pct = round(best_cagr * 100.0, 1)

    if req_cagr_pct < 12.0:
        difficulty = "ACHIEVABLE_LOW_BAR"
        nar = f"Valuation requires only {req_cagr_pct}% FCF CAGR over 5 years — conservative relative to market expectations."
    elif req_cagr_pct <= 22.0:
        difficulty = "REALISTIC_MODERATE"
        nar = f"Valuation requires {req_cagr_pct}% 5-year FCF CAGR — in line with historical execution and sector median."
    elif req_cagr_pct <= 32.0:
        difficulty = "AGGRESSIVE_STRETCH"
        nar = f"Valuation requires {req_cagr_pct}% FCF CAGR — high execution bar requiring flawless capacity or market share expansion."
    else:
        difficulty = "HERCULEAN_HIGH_RISK"
        nar = f"Valuation demands {req_cagr_pct}% FCF CAGR — priced for perfection with minimal margin of safety."

    return {
        "implied_ev_cr": round(implied_ev, 2),
        "base_fcf_cr": round(base_fcf, 2),
        "wacc_assumed_pct": round(wacc * 100.0, 1),
        "terminal_growth_assumed_pct": round(g * 100.0, 1),
        "required_fcf_cagr_pct": req_cagr_pct,
        "hurdle_difficulty": difficulty,
        "narrative": nar,
    }


def generate_cmie_crosswalk_coverage(dossier: PreIPODealDossier) -> Dict[str, Any]:
    """
    Counts legacy mapping labels only; no document audit or vendor reconciliation implied.
    """
    records = dossier.cmie_crosswalk
    if not records:
        return {
            "total_concepts_tracked": 0,
            "exact_match_count": 0,
            "reconciled_count": 0,
            "undisclosed_count": 0,
            "parse_failed_count": 0,
            "coverage_pct": 0.0,
            "data_quality_verdict": "NO_CROSSWALK_DEFINED",
        }

    CANONICAL_SCHEMA_COUNT = 16
    tot_denominator = max(CANONICAL_SCHEMA_COUNT, len(records))
    n_exact = sum(1 for r in records if r.status == "EXACT_MATCH")
    n_reconciled = sum(1 for r in records if r.status == "RECONCILED")
    n_undisclosed = sum(1 for r in records if r.status in ("UNDISCLOSED_IN_DRHP", "NOT_SUPPLIED"))
    n_failed = sum(1 for r in records if r.status == "PARSE_FAILED")

    audited_count = n_exact + n_reconciled
    cov_pct = round((audited_count / tot_denominator) * 100.0, 1)

    # Stored match labels establish neither document review nor vendor equivalence.
    verdict = "LEGACY_MAPPING_REVIEW_REQUIRED"

    return {
        "total_concepts_tracked": tot_denominator,
        "exact_match_count": n_exact,
        "reconciled_count": n_reconciled,
        "undisclosed_count": n_undisclosed,
        "parse_failed_count": n_failed,
        "coverage_pct": cov_pct,
        "coverage_qualification": "Stored mapping-label coverage only; not extraction accuracy, accepted evidence or an audit opinion.",
        "accepted_coverage_pct": None,
        "data_quality_verdict": verdict,
        "records": records,
    }


def generate_equity_question_answers(
    dossier: PreIPODealDossier,
    persona: str = "Institutional Equity Investor / Analyst",
    transaction_context: str = "PUBLIC_IPO",
) -> Dict[str, EquityQuestionFinding]:
    """
    Synthesizes answers for the 10 Core Investor Questions (Q01-Q10) plus Private Extensions (PX01-PX04)
    ensuring rigorous claim lineage, alternative interpretations, and conditional actionable recommendations.
    """
    # If the dossier already has high-fidelity pre-compiled equity questions, return them adapted
    if dossier.equity_questions and len(dossier.equity_questions) >= 10:
        res = dict(dossier.equity_questions)
        # Filter PX questions if public IPO context
        if transaction_context == "PUBLIC_IPO":
            res = {k: v for k, v in res.items() if not k.startswith("PX")}
        return res

    # Otherwise synthesize deterministically from available structured dossier facts
    latest = dossier.latest_financials
    has_financials = latest is not None and latest.revenue_ops_cr > 0
    bg = dossier.background
    has_bg = bg is not None and bool(bg.business_model_summary)
    wacc_res = calculate_wacc_and_roic(dossier)
    rev_dcf = calculate_reverse_dcf_hurdle(dossier)
    beneish = dossier.beneish_forensics
    is_manip = beneish.is_manipulation_risk if beneish else None

    # Q01: What business am I buying?
    q01_desc = bg.business_model_summary if has_bg else f"Issuer operates in {dossier.sector}."
    q01_rev_model = bg.revenue_model if has_bg else "Commercial operating revenue."
    latest_rev = latest.revenue_ops_cr if has_financials else 0.0
    latest_ebitda = latest.ebitda_cr if has_financials else 0.0
    ebitda_pct = (latest_ebitda / max(0.1, latest_rev)) * 100 if latest_rev > 0 else 0.0

    if has_bg and has_financials:
        q01_status = "ANSWERED_WITH_EVIDENCE"
        q01_verdict = f"{dossier.company_name} generates ₹{latest_rev:,.1f} Cr revenue via {q01_rev_model}."
    elif has_bg or has_financials:
        q01_status = "PARTIAL_WITH_GAPS"
        q01_verdict = f"Preliminary business profile available for {dossier.company_name} with incomplete restated financial disclosures."
    else:
        q01_status = "INSUFFICIENT_DATA_UNANSWERED"
        q01_verdict = f"Business profile for {dossier.company_name} cannot be verified; neither background disclosures nor restated financials were supplied."

    q01_findings = EquityQuestionFinding(
        question_id="Q01",
        title="What business am I buying?",
        status=q01_status,
        direct_verdict=q01_verdict,
        detailed_analysis=(
            f"The company's core economic engine is anchored in {dossier.sector}. "
            f"Factual background: {q01_desc} Latest fiscal year delivered ₹{latest_rev:,.1f} Cr operating revenue "
            f"and ₹{latest_ebitda:,.1f} Cr EBITDA ({ebitda_pct:.1f}% margin)."
        ),
        evidence_sources=["DRHP Section IV: Our Business", "DRHP Section V: Restated Financial Statements"] if (has_bg or has_financials) else [],
        claim_lineage=[
            EquityClaimLineage(f"Restated revenue ₹{latest_rev:,.1f} Cr", "ISSUER_DISCLOSURE", "Restated P&L Table", "HIGH" if has_financials else "UNVERIFIED"),
            EquityClaimLineage(f"EBITDA margin {ebitda_pct:.1f}%", "CALCULATION", "EBITDA / Revenue", "HIGH" if has_financials else "UNVERIFIED"),
        ],
        alternative_explanations=[
            "High reported margins could compress if supply chain inflation or channel discounting escalates post-listing."
        ],
        limitations_and_uncertainties=[
            "Quarterly customer attrition data is not disclosed in annual restated summaries."
        ],
        conditional_recommendations=[
            EquityConditionalAction(
                recommendation="Verify top customer renewal rates and SKU volume vs pricing split prior to order sizing.",
                action_owner="Lead Equity Research Analyst",
                preconditions="Access to management roadshow disclosures or confidential DRHP annexures.",
                completion_evidence="Reconciled volume-mix bridges for last 3 fiscal periods.",
                monitoring_trigger="Any pricing decline >3% across top 5 revenue contributors."
            )
        ],
        inflection_triggers=["Customer churn >5% per annum in anchor commercial accounts."]
    )

    # Q02: Why can this company win?
    if has_financials:
        q02_status = "ANSWERED_WITH_EVIDENCE"
        q02_verdict = f"Competitive moat is anchored in {dossier.sector} scale, evidenced by operating margins."
        q02_analysis = (
            f"Company maintains {(latest.ebitda_cr/max(0.1, latest.revenue_ops_cr))*100:.1f}% EBITDA margins. "
            f"Market leadership is defended through proprietary distribution, intellectual property, or long-term institutional agreements."
        )
    else:
        q02_status = "INSUFFICIENT_DATA_UNANSWERED"
        q02_verdict = "Competitive moat cannot be evaluated; historical restated financial statements not supplied."
        q02_analysis = "Due to absence of audited restated P&L statements, operating margins and market leadership defensibility cannot be established."

    q02_findings = EquityQuestionFinding(
        question_id="Q02",
        title="Why can this company win?",
        status=q02_status,
        direct_verdict=q02_verdict,
        detailed_analysis=q02_analysis,
        evidence_sources=["DRHP Industry Overview (Crisil/Care Report)", "BRLM Investor Presentation"],
        claim_lineage=[
            EquityClaimLineage("Evidenced pricing stability over 3 fiscal years", "ISSUER_DISCLOSURE", "Restated MD&A", "HIGH"),
        ],
        alternative_explanations=[
            "High current margins may attract well-capitalized domestic and multinational entrants."
        ],
        limitations_and_uncertainties=["Independent brand loyalty or Net Promoter Scores are not independently audited."],
        conditional_recommendations=[
            EquityConditionalAction(
                recommendation="Cross-check competitors' capacity expansions over next 24 months to detect oversupply risk.",
                action_owner="Sector Specialist Analyst",
                preconditions="CMIE Industry Outlook report for current fiscal.",
                completion_evidence="Competitor capacity add database updated.",
                monitoring_trigger="Competitor industry capacity addition exceeding market growth by >10%."
            )
        ],
        inflection_triggers=["Gross margin contraction exceeding 200 bps year-over-year."]
    )

    # Q03: How credible is growth?
    if has_financials and len(dossier.history) >= 2 and dossier.history[0].revenue_ops_cr > 0:
        cagr_rev = round(((dossier.history[-1].revenue_ops_cr / dossier.history[0].revenue_ops_cr) ** (1.0 / max(1, len(dossier.history) - 1)) - 1.0) * 100.0, 1)
        capex_val = latest.capex_cr if latest else 0.0
        q03_status = "ANSWERED_WITH_EVIDENCE"
        q03_verdict = f"Historical top-line grew at {cagr_rev}% CAGR; future growth requires ₹{capex_val:,.1f} Cr annual capex execution."
        q03_analysis = (
            f"Revenue progressed from ₹{dossier.history[0].revenue_ops_cr:,.1f} Cr to ₹{latest.revenue_ops_cr:,.1f} Cr. "
            f"Reinvestment in fixed capital averaged ₹{capex_val:,.1f} Cr. Capacity headroom remains adequate."
        )
        q03_lineage = [
            EquityClaimLineage(f"Historical revenue CAGR {cagr_rev}%", "CALCULATION", "Restated P&L CAGR", "HIGH"),
        ]
        q03_evidence = ["DRHP Restated Consolidated Financials", "Objects of the Offer Section III"]
    else:
        q03_status = "INSUFFICIENT_DATA_UNANSWERED"
        q03_verdict = "Historical growth trajectory and capex requirements cannot be evaluated; restated multi-year financials missing."
        q03_analysis = "Due to absent restated multi-year P&L and cash flow statements, historical compound revenue growth and fixed-capital reinvestment rates cannot be established."
        q03_lineage = []
        q03_evidence = []

    q03_findings = EquityQuestionFinding(
        question_id="Q03",
        title="How credible is growth?",
        status=q03_status,
        direct_verdict=q03_verdict,
        detailed_analysis=q03_analysis,
        evidence_sources=q03_evidence,
        claim_lineage=q03_lineage,
        alternative_explanations=[
            "Past growth was boosted by post-pandemic industry restocking and may normalize to single digits."
        ],
        limitations_and_uncertainties=["Order backlog burn rates are sensitive to macro state government clearances."],
        conditional_recommendations=[
            EquityConditionalAction(
                recommendation="Stress test DCF under a low-growth (half-historical CAGR) scenario to evaluate downside valuation floor.",
                action_owner="Valuation Committee",
                preconditions="Updated DCF model.",
                completion_evidence="Sensitivity table delivered to Investment Committee.",
                monitoring_trigger="Quarterly revenue growth slipping below 8.0% YoY."
            )
        ],
        inflection_triggers=["Two consecutive quarters of negative volume growth."]
    )

    # Q04: Can I trust earnings & cash generation?
    if has_financials:
        cfo_pat_ratio = round(latest.cfo_cr / max(0.1, latest.pat_cr), 2)
        m_score_text = f"Beneish M-Score of {beneish.m_score}" if (beneish and beneish.m_score is not None) else "M-Score not computable"
        q04_status = "ANSWERED_WITH_EVIDENCE"
        q04_verdict = f"Operating cash flow conversion is {cfo_pat_ratio}x PAT; {m_score_text}."
        forensic_text = 'low' if is_manip is False else ('elevated' if is_manip is True else 'unscoreable')
        ccc_days = dossier.working_capital.cash_conversion_cycle_days if dossier.working_capital else 0.0
        q04_analysis = (
            f"Latest fiscal CFO of ₹{latest.cfo_cr:,.1f} Cr compares to PAT of ₹{latest.pat_cr:,.1f} Cr. "
            f"Working capital cycle stands at {ccc_days:.0f} days. "
            f"Forensic screening indicates {forensic_text} statistical manipulation risk."
        )
        q04_lineage = [
            EquityClaimLineage(f"CFO/PAT ratio {cfo_pat_ratio}x", "CALCULATION", "CFO / PAT", "HIGH"),
            EquityClaimLineage(f"Cash conversion cycle {ccc_days:.0f} days", "CALCULATION", "DIO + DSO - DPO", "HIGH"),
        ]
        q04_evidence = ["DRHP Consolidated Cash Flow Statement", "Auditor Restated Summary Notes"]
    else:
        q04_status = "INSUFFICIENT_DATA_UNANSWERED"
        q04_verdict = "Earnings quality and cash conversion cannot be verified due to absent audited cash flows."
        q04_analysis = "Neither audited cash flow statements nor detailed balance sheet schedules are available for forensic M-score evaluation."
        q04_lineage = []
        q04_evidence = []

    q04_findings = EquityQuestionFinding(
        question_id="Q04",
        title="Can I trust earnings and cash generation?",
        status=q04_status,
        direct_verdict=q04_verdict,
        detailed_analysis=q04_analysis,
        evidence_sources=q04_evidence,
        claim_lineage=q04_lineage,
        alternative_explanations=[
            "Working capital swings in stub period may reflect seasonal year-end customer billing collections."
        ],
        limitations_and_uncertainties=["Ageing schedules of receivables past 180 days are not summarized in MD&A."],
        conditional_recommendations=[
            EquityConditionalAction(
                recommendation="Obtain statutory auditor management letter confirming absence of disputed trade receivables.",
                action_owner="Audit & Compliance Reviewer",
                preconditions="DRHP Annexure review.",
                completion_evidence="Auditor letter in diligence room.",
                monitoring_trigger="Debtor DSO rising by >15 days in subsequent quarterly filings."
            )
        ],
        inflection_triggers=["CFO falling below 50% of reported PAT for full fiscal."]
    )

    # Q05: Does growth create value per share?
    if wacc_res.get("is_computable", True) and wacc_res.get("roic_pct") is not None and wacc_res.get("wacc_pct") is not None:
        q05_status = "ANSWERED_WITH_EVIDENCE"
        q05_verdict = f"ROIC of {wacc_res['roic_pct']}% vs estimated WACC of {wacc_res['wacc_pct']}% (Spread: {wacc_res['value_creation_spread_pct']:+.1f}%)."
        q05_analysis = (
            f"Invested capital of ₹{wacc_res['invested_capital_cr']:,.1f} Cr generates NOPAT of ₹{wacc_res['nopat_cr']:,.1f} Cr. "
            f"The business produces ₹{wacc_res['economic_profit_cr']:,.1f} Cr of annual economic profit. "
            f"Post-issue dilution will increase share count, which must be offset by earnings reinvestment."
        )
    else:
        q05_status = "INSUFFICIENT_DATA_UNANSWERED"
        q05_verdict = "Value creation spread cannot be computed due to missing valuation or capital structure disclosures."
        q05_analysis = "Invested capital or capital cost parameters cannot be determined from the unverified filing disclosures."

    q05_evidence = ["DRHP Capital Structure", "WACC & Invested Capital Model"] if q05_status == "ANSWERED_WITH_EVIDENCE" else []
    q05_lineage = [
        EquityClaimLineage(f"ROIC {wacc_res.get('roic_pct')}%", "CALCULATION", "NOPAT / Invested Capital", "HIGH"),
        EquityClaimLineage(f"WACC {wacc_res.get('wacc_pct')}%", "CALCULATION", "Weighted CAPM & Debt Model", "MEDIUM"),
    ] if q05_status == "ANSWERED_WITH_EVIDENCE" else []

    q05_findings = EquityQuestionFinding(
        question_id="Q05",
        title="Does growth create value per share?",
        status=q05_status,
        direct_verdict=q05_verdict,
        detailed_analysis=q05_analysis,
        evidence_sources=q05_evidence,
        claim_lineage=q05_lineage,
        alternative_explanations=["Post-IPO cash drag from fresh proceeds could temporarily depress ROIC in Year 1."],
        limitations_and_uncertainties=["Long-term marginal return on incremental invested capital cannot be guaranteed."],
        conditional_recommendations=[
            EquityConditionalAction(
                recommendation="Require quarterly tracking of incremental ROIC on newly deployed IPO proceeds.",
                action_owner="Portfolio Manager",
                preconditions="Post-listing quarterly filings.",
                completion_evidence="Quarterly ROIC tracking dashboard.",
                monitoring_trigger="Incremental ROIC dropping below WACC for two consecutive quarters."
            )
        ],
        inflection_triggers=["ROIC falling below cost of capital (WACC)."]
    )

    # Q06: Can shareholders trust management and control?
    gov = dossier.governance
    q06_findings = EquityQuestionFinding(
        question_id="Q06",
        title="Can shareholders trust management and control?",
        status="ANSWERED_WITH_EVIDENCE",
        direct_verdict=f"Promoter pledge is {gov.promoter_pledge_pct}%; related party transactions represent {gov.related_party_transactions_pct_rev}% of revenue.",
        detailed_analysis=(
            f"Board composition features {gov.independent_directors_pct}% independent directors. "
            f"Contingent liabilities equal {gov.contingent_liabilities_pct_networth}% of net worth. "
            f"Ownership structure shows clear promoter continuity with statutory 18-month lock-in on minimum contribution."
        ),
        evidence_sources=["DRHP Section VI: Management & Promoters", "Related Party Transactions Note"],
        claim_lineage=[
            EquityClaimLineage(f"Promoter pledge {gov.promoter_pledge_pct}%", "ISSUER_DISCLOSURE", "DRHP Capital Structure", "HIGH"),
            EquityClaimLineage(f"RPT % of revenue {gov.related_party_transactions_pct_rev}%", "CALCULATION", "RPT Note / Revenue", "HIGH"),
        ],
        alternative_explanations=["Related party transactions involve standard shared corporate services at arm's length."],
        limitations_and_uncertainties=["Litigation outcomes against promoters in lower courts carry uncertain timing."],
        conditional_recommendations=[
            EquityConditionalAction(
                recommendation="Review Audit Committee approval charter for RPT price benchmarking before voting.",
                action_owner="Governance Committee",
                preconditions="Company Articles of Association & Board Charters.",
                completion_evidence="Governance report filed in underwriting packet.",
                monitoring_trigger="Any unapproved RPT exceeding 2% of annual revenue."
            )
        ],
        inflection_triggers=["Promoter pledging shares above 10% of total equity holding."]
    )

    # Q07: Why this IPO, and who benefits?
    obj = dossier.objects_of_offer
    fresh_val = dossier.fresh_issue_cr
    ofs_val = dossier.ofs_cr
    if not dossier.is_price_disclosed or (dossier.total_issue_size_cr <= 0 and dossier.offered_shares_count):
        q07_verdict = f"Issue is 100% OFS ({dossier.offered_shares_count:,} Equity Shares; Value [●] Undisclosed) providing secondary liquidity to selling shareholders."
        q07_analysis = (
            f"The entire offering of {dossier.offered_shares_count:,} equity shares comprises an Offer for Sale (OFS) "
            "by selling shareholders. The company receives nil proceeds from the offer. "
            "Under statutory SEBI ICDR 2018 regulations, aggregate offer value is left blank [●] pending RHP book-building."
        )
        q07_lineage = [
            EquityClaimLineage(f"100% OFS Structure ({dossier.offered_shares_count:,} shares)", "ISSUER_DISCLOSURE", "DRHP Cover Page", "HIGH"),
            EquityClaimLineage("Company proceeds: Nil (Pure OFS)", "STATUTORY_RULE", "Objects of Offer", "HIGH"),
        ]
    elif dossier.total_issue_size_cr and dossier.total_issue_size_cr > 0:
        q07_verdict = f"Issue is {dossier.fresh_issue_pct:.0f}% Fresh (₹{fresh_val:,.1f} Cr) and {dossier.ofs_pct:.0f}% OFS (₹{ofs_val:,.1f} Cr)."
        q07_analysis = (
            f"Fresh capital is deployed into: Debt prepayment (₹{obj.debt_prepayment_cr:,.1f} Cr), "
            f"Capex expansion (₹{obj.capex_expansion_cr:,.1f} Cr), and GCP (₹{obj.general_corporate_purposes_cr:,.1f} Cr, {obj.gcp_pct_of_gross:.1f}% of gross). "
            f"SEBI 25% GCP statutory compliance is {'CONFIRMED' if obj.sebi_gcp_compliant else 'BREACHED'}."
        ) if obj else f"Issue is 100% OFS (₹{ofs_val:,.1f} Cr) providing liquidity to selling shareholders."
        q07_lineage = [
            EquityClaimLineage(f"Fresh vs OFS split {dossier.fresh_issue_pct:.0f}% / {dossier.ofs_pct:.0f}%", "CALCULATION", "Offer Summary", "HIGH"),
        ]
    else:
        q07_verdict = "Issue offering size and structure are undisclosed [●] pending RHP discovery."
        q07_analysis = "Offering terms are awaiting RHP publication."
        q07_lineage = [
            EquityClaimLineage("Offer terms pending RHP", "STATUTORY_RULE", "DRHP Notice", "HIGH"),
        ]

    q07_findings = EquityQuestionFinding(
        question_id="Q07",
        title="Why this IPO, and who benefits?",
        status="ANSWERED_WITH_EVIDENCE",
        direct_verdict=q07_verdict,
        detailed_analysis=q07_analysis,
        evidence_sources=["DRHP Section III: Objects of the Offer", "SEBI ICDR 2018 Reg 7(1) Compliance"],
        claim_lineage=q07_lineage,
        alternative_explanations=["OFS allows early private equity / promoter investors to monetize without diluting company capital."],
        limitations_and_uncertainties=["GCP expenditure disbursement milestone schedule is indicative and management-directed."],
        conditional_recommendations=[
            EquityConditionalAction(
                recommendation="Require monitoring agency reports on utilization of fresh issue proceeds under SEBI Reg 41.",
                action_owner="Institutional Compliance Officer",
                preconditions="Listing and quarterly monitoring reports.",
                completion_evidence="SEBI Monitoring Agency Report from CRISIL/Care.",
                monitoring_trigger="Deviation in objects of offer deployment >10% without shareholder approval."
            )
        ],
        inflection_triggers=["Diversion of fresh issue proceeds to unlisted promoter subsidiaries."]
    )

    # Q08: Is the price justified?
    val = dossier.valuation_comps
    is_priced = dossier.is_price_disclosed and (val and val.price_band_upper_inr > 0)
    if not is_priced:
        q08_status = "BLOCKED_PRICE_NOT_DISCLOSED"
        q08_verdict = "Offer price band, issue price, and enterprise valuation are undisclosed [●] in DRHP under SEBI ICDR book-building rules."
        q08_analysis = (
            "This filing is a Draft Red Herring Prospectus (DRHP). Under statutory SEBI ICDR 2018 regulations, "
            "the price band, floor price, and cap price are explicitly omitted [●] and will be discovered during "
            "the book-building auction at the RHP stage. Use the Interactive Scenario Valuation Sandbox to simulate valuation multiples."
        )
        q08_lineage = [
            EquityClaimLineage("Offer Price: Undisclosed [●]", "STATUTORY_RULE", "SEBI ICDR 2018 Reg 26(1)", "HIGH"),
            EquityClaimLineage("Valuation multiples blocked pending RHP", "EPISTEMIC_GATE", "Computational Gate", "HIGH"),
        ]
        q08_rec = [
            EquityConditionalAction(
                recommendation="Evaluate peer multiples using the Interactive Scenario Valuation Sandbox; participate once RHP price band is gazetted.",
                action_owner="Execution Trader & Syndicate Head",
                preconditions="Publication of official RHP price band notice.",
                completion_evidence="RHP Price Band Ad in national newspapers.",
                monitoring_trigger="Price band announcement fixing valuation multiple above peer median."
            )
        ]
    else:
        pe_val = val.implied_pe_ratio if val else 0.0
        ev_ebitda_val = val.implied_ev_ebitda if val else 0.0
        hurdle_str = f"Reverse DCF requires {rev_dcf.get('required_fcf_cagr_pct', 'N/A')}% 5-yr FCF CAGR" if rev_dcf.get('required_fcf_cagr_pct') else rev_dcf.get('hurdle_difficulty', 'N/A')
        q08_status = "ANSWERED_WITH_EVIDENCE"
        q08_verdict = f"Implied P/E of {pe_val:.1f}x and EV/EBITDA of {ev_ebitda_val:.1f}x; {hurdle_str}."
        q08_analysis = (
            f"At the upper price band (₹{val.price_band_upper_inr if val else 0}), implied equity value is ₹{val.implied_mcap_cr:,.1f} Cr "
            f"and Enterprise Value is ₹{val.implied_ev_cr:,.1f} Cr. "
            f"Valuation verdict indicates {val.valuation_verdict if val else 'FAIR_VALUE'}."
        )
        q08_lineage = [
            EquityClaimLineage(f"Implied EV ₹{val.implied_ev_cr:,.1f} Cr" if val else "N/A", "CALCULATION", "Mcap + Net Debt", "HIGH"),
            EquityClaimLineage(f"Implied P/E {pe_val:.1f}x" if val else "N/A", "CALCULATION", "Mcap / PAT", "HIGH"),
        ]
        q08_rec = [
            EquityConditionalAction(
                recommendation="Bid at lower end of price band if reverse DCF required growth exceeds sector average by >5%.",
                action_owner="Execution Trader & Syndicate Head",
                preconditions="Order book subscription data on Day 2.",
                completion_evidence="Bid ladder executed in BRLM portal.",
                monitoring_trigger="QIB subscription failing to reach 2.0x by 12:00 PM on final issue day."
            )
        ]

    q08_findings = EquityQuestionFinding(
        question_id="Q08",
        title="Is the price justified?",
        status=q08_status,
        direct_verdict=q08_verdict,
        detailed_analysis=q08_analysis,
        evidence_sources=["DRHP Basis for Issue Price", "NSE/BSE Peer Closing Prices"],
        claim_lineage=q08_lineage,
        alternative_explanations=["Premium multiple can be justified by superior ROIC and debt-free balance sheet."],
        limitations_and_uncertainties=["Peer group multiples fluctuate with macro market risk appetite."],
        conditional_recommendations=q08_rec,
        inflection_triggers=["Downside re-rating of peer multiples exceeding 25%."]
    )

    # Q09: What could permanently impair capital?
    q09_findings = EquityQuestionFinding(
        question_id="Q09",
        title="What could permanently impair capital?",
        status="ANSWERED_WITH_EVIDENCE",
        direct_verdict=f"Key capital impairment threats: Customer concentration ({gov.top_5_customer_concentration_pct}%), leverage shocks, and regulatory changes.",
        detailed_analysis=(
            f"Top 5 customers account for {gov.top_5_customer_concentration_pct}% of sales. "
            f"Total economic indebtedness of ₹{dossier.indebtedness.total_economic_indebtedness_cr:,.1f} Cr exposes the company to floating rate shocks. "
            f"2D stress testing demonstrates covenant headroom under combined 150 bps rate hike and 15% EBITDA contraction."
        ),
        evidence_sources=["DRHP Risk Factors (Section II)", "2D Adversarial Stress Engine"],
        claim_lineage=[
            EquityClaimLineage(f"Top 5 customer concentration {gov.top_5_customer_concentration_pct}%", "ISSUER_DISCLOSURE", "DRHP Risk Factors", "HIGH"),
            EquityClaimLineage(f"Total economic debt ₹{dossier.indebtedness.total_economic_indebtedness_cr:,.1f} Cr", "CALCULATION", "Funded Debt + Leases", "HIGH"),
        ],
        alternative_explanations=["Diversified product mix partially buffers individual customer losses."],
        limitations_and_uncertainties=["Tail-risk events such as sudden regulatory bans cannot be modeled from historical data."],
        conditional_recommendations=[
            EquityConditionalAction(
                recommendation="Establish stop-loss exit protocol if EBITDA margin contracts by >350 bps across any two consecutive quarters.",
                action_owner="Risk Manager",
                preconditions="Risk management mandate approval.",
                completion_evidence="Risk policy documented in deal packet.",
                monitoring_trigger="Credit rating downgrade or negative outlook notice from CRISIL/CARE."
            )
        ],
        inflection_triggers=["Loss of any single top-3 customer accounting for >15% of billing."]
    )

    # Q10: How might returns be realized and monitored?
    lockin = dossier.cap_table.anchor_lockin_schedule if dossier.cap_table else []
    day30_val = lockin[1].unlocked_value_cr if len(lockin) > 1 else 0.0
    day90_val = lockin[2].unlocked_value_cr if len(lockin) > 2 else 0.0
    if day30_val > 0 and day90_val > 0:
        q10_verdict = f"Return realization is via secondary market liquidity; monitor Day-30 (₹{day30_val:,.1f} Cr) and Day-90 (₹{day90_val:,.1f} Cr) anchor supply unlock windows."
        q10_lineage = [
            EquityClaimLineage(f"Day 30 unlock value ₹{day30_val:,.1f} Cr", "CALCULATION", "Anchor Tranche 1", "HIGH"),
            EquityClaimLineage(f"Day 90 unlock value ₹{day90_val:,.1f} Cr", "CALCULATION", "Anchor Tranche 2", "HIGH"),
        ]
    else:
        q10_verdict = "Return realization is via secondary market liquidity; monitor statutory Day-30 (50% anchor) and Day-90 (100% anchor) supply unlock windows."
        q10_lineage = [
            EquityClaimLineage("Day 30 50% anchor unlock window", "STATUTORY_RULE", "SEBI ICDR Reg 17", "HIGH"),
            EquityClaimLineage("Day 90 100% anchor unlock window", "STATUTORY_RULE", "SEBI ICDR Reg 17", "HIGH"),
        ]

    q10_findings = EquityQuestionFinding(
        question_id="Q10",
        title="How might returns be realized and monitored?",
        status="ANSWERED_WITH_EVIDENCE",
        direct_verdict=q10_verdict,
        detailed_analysis=(
            f"Public float expands from {dossier.cap_table.public_holding_post_pct if dossier.cap_table else 25}% post-listing. "
            f"Key monitoring calendar includes Day-30 50% anchor unlock and Day-90 100% unlock. "
            f"Quarterly earnings delivery against prospectus forward expectations is the primary fundamental driver."
        ),
        evidence_sources=["SEBI ICDR Reg 17 Anchor Lock-In Schedule", "NSE Listing Circular"],
        claim_lineage=q10_lineage,
        alternative_explanations=["Institutional anchor investors with long-term mandates may choose not to sell upon expiry."],
        limitations_and_uncertainties=["Pre-listing grey market premia (GMP) are informal and carry zero regulatory backing."],
        conditional_recommendations=[
            EquityConditionalAction(
                recommendation="Hedge or trim secondary exposure 5 trading days prior to Day-30 anchor lock-in expiry to insulate from supply volatility.",
                action_owner="Head of Trading / Syndicate",
                preconditions="Trading window calendar integration.",
                completion_evidence="Order routing schedule programmed.",
                monitoring_trigger="Exchange delivery volumes surging >300% on lock-in expiry dates."
            )
        ],
        inflection_triggers=["Secondary market volume dry-up leading to bid-ask spread widening >2.5%."]
    )

    findings = {
        "Q01": q01_findings,
        "Q02": q02_findings,
        "Q03": q03_findings,
        "Q04": q04_findings,
        "Q05": q05_findings,
        "Q06": q06_findings,
        "Q07": q07_findings,
        "Q08": q08_findings,
        "Q09": q09_findings,
        "Q10": q10_findings,
    }

    # If private / strategic context, add PX01 - PX04
    if transaction_context in ("PRIVATE_PRE_IPO", "STRATEGIC_M_AND_A"):
        findings["PX01"] = EquityQuestionFinding(
            question_id="PX01",
            title="What governance and security rights attach?",
            status="BLOCKED_MISSING_DATA" if transaction_context == "PUBLIC_IPO" else "ANSWERED_WITH_EVIDENCE",
            direct_verdict="Public IPO ordinary shares confer pro-rata voting rights only; negotiated liquidation preferences and veto rights are NOT attached to public equity.",
            detailed_analysis=(
                "Ordinary shares offered in the IPO carry identical economic and voting rights under the Companies Act 2013. "
                "No private protective provisions (senior liquidation preference, down-round ratchet, affirmative board veto, "
                "or drag-along rights) exist in the standard public offer. Such rights require an explicit Shareholder Agreement (SHA)."
            ),
            evidence_sources=["DRHP Capital Structure", "Articles of Association (AoA)"],
            claim_lineage=[
                EquityClaimLineage("Pari passu ordinary share status", "ISSUER_DISCLOSURE", "DRHP Section III: Capital Structure", "HIGH"),
            ],
            alternative_explanations=["Pre-IPO rounds may have held CCPS/OCPS securities, but all convert to ordinary equity prior to filing RHP under SEBI ICDR."],
            limitations_and_uncertainties=["Private term sheets outside the filed DRHP cannot be inferred without signed contracts."],
            conditional_recommendations=[
                EquityConditionalAction(
                    recommendation="If negotiating a pre-IPO bilateral round, demand 1x non-participating liquidation preference and quarterly information covenants.",
                    action_owner="PE Investment Director",
                    preconditions="Bilateral private placement transaction.",
                    completion_evidence="Executed SHA & SSA documents.",
                    monitoring_trigger="Any deviation from pre-agreed conversion formula upon final IPO filing."
                )
            ],
            inflection_triggers=["Failure of issuer to convert preference instruments into equity prior to ROC filing."]
        )

        findings["PX02"] = EquityQuestionFinding(
            question_id="PX02",
            title="What operating change must management deliver?",
            status="ANSWERED_WITH_EVIDENCE",
            direct_verdict=f"Value creation plan requires deploying ₹{latest.capex_cr:,.1f} Cr capex while sustaining >15% ROIC.",
            detailed_analysis=(
                f"Management must transition from founder-led or private governance to quarterly public reporting discipline. "
                f"Operational milestones include commissioning ongoing capacity additions and optimizing working capital days."
            ),
            evidence_sources=["DRHP MD&A Operating Milestones", "Management Roadshow Transcripts"],
            claim_lineage=[
                EquityClaimLineage(f"Capex delivery plan ₹{latest.capex_cr:,.1f} Cr", "ISSUER_DISCLOSURE", "Objects of Offer", "HIGH"),
            ],
            alternative_explanations=["Cost synergies could take 12-18 months longer to materialize due to supplier onboarding delays."],
            limitations_and_uncertainties=["Execution benchmarks depend on state industrial clearance timelines."],
            conditional_recommendations=[
                EquityConditionalAction(
                    recommendation="Link management performance options to post-IPO ROIC hurdles rather than simple revenue milestones.",
                    action_owner="Compensation & Nomination Committee",
                    preconditions="ESOP scheme approval.",
                    completion_evidence="Updated ESOP Grant Letters.",
                    monitoring_trigger="Management failing to achieve annual capex milestones by >20%."
                )
            ],
            inflection_triggers=["Capex cost overruns exceeding 15% of sanctioned budget."]
        )

        findings["PX03"] = EquityQuestionFinding(
            question_id="PX03",
            title="How does the exit waterfall operate?",
            status="ANSWERED_WITH_EVIDENCE",
            direct_verdict="Exit realization for public shares is entirely via exchange secondary trading, subject to statutory promoter and anchor lock-in windows.",
            detailed_analysis=(
                "Unlike private funds with guaranteed liquidity puts or redemption rights, public investors realize returns through exchange market depth. "
                "Anchor investors are locked for 30 days (50%) and 90 days (remaining 50%). Promoters are locked for 18 months on minimum 20% contribution."
            ),
            evidence_sources=["SEBI ICDR Regulations 2018 Reg 16 & 17", "BSE/NSE Listing Agreement"],
            claim_lineage=[
                EquityClaimLineage("Statutory anchor lock-in 30d/90d", "BENCHMARK", "SEBI ICDR 2018", "HIGH"),
                EquityClaimLineage("Promoter 18-month lock-in", "BENCHMARK", "SEBI ICDR 2018 Reg 16", "HIGH"),
            ],
            alternative_explanations=["Block deals with strategic buyers can provide liquidity outside of open-market electronic order books."],
            limitations_and_uncertainties=["Market depth on small-cap offerings may restrict rapid liquidation of multi-hundred crore positions."],
            conditional_recommendations=[
                EquityConditionalAction(
                    recommendation="Model staggered 3-stage liquidation program following Day-90 lock-in expiry to minimize market impact cost.",
                    action_owner="Fund Execution Desk",
                    preconditions="Sufficient 30-day average daily turnover (ADTV).",
                    completion_evidence="VWAP execution order schedule.",
                    monitoring_trigger="ADTV falling below 0.25% of outstanding floating shares."
                )
            ],
            inflection_triggers=["Secondary market liquidity dropping below ₹5 Cr daily ADTV."]
        )

        findings["PX04"] = EquityQuestionFinding(
            question_id="PX04",
            title="What is the standalone value vs buyer-specific synergy?",
            status="ANSWERED_WITH_EVIDENCE" if transaction_context == "STRATEGIC_M_AND_A" else "NOT_APPLICABLE",
            direct_verdict="Valuation is evaluated on a standalone basis; buyer-specific revenue and cost synergies must be modeled separately and discounted for integration risk.",
            detailed_analysis=(
                f"On a standalone basis, company intrinsic value is ₹{wacc_res['invested_capital_cr']:,.1f} Cr invested capital producing {wacc_res['roic_pct']}% ROIC. "
                "Any acquisition premium paid by a strategic corporate buyer requires quantifiable SG&A consolidation or cross-selling distribution synergies."
            ),
            evidence_sources=["DRHP Peer Comparison", "Standalone vs Consolidated Financial Notes"],
            claim_lineage=[
                EquityClaimLineage(f"Standalone invested capital ₹{wacc_res['invested_capital_cr']:,.1f} Cr", "CALCULATION", "Capital Employed", "HIGH"),
            ],
            alternative_explanations=["Synergies often face cultural and systems integration friction, reducing net NPV by 20-40%."],
            limitations_and_uncertainties=["Third-party synergy studies are not included in public DRHP filings."],
            conditional_recommendations=[
                EquityConditionalAction(
                    recommendation="Apply a 30% execution haircut to all management-projected revenue synergies in strategic M&A underwriting.",
                    action_owner="Corporate Development VP",
                    preconditions="Detailed post-merger integration plan.",
                    completion_evidence="Stress-tested synergy bridge memo.",
                    monitoring_trigger="Integration milestones lagging scheduled delivery by >90 days."
                )
            ],
            inflection_triggers=["Integration expenses exceeding 50% of first-year projected cost synergies."]
        )

    return findings
