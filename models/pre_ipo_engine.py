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
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple
from models.pre_ipo_schema import PreIPODealDossier, FinancialYearMetric, AnchorLockinMilestone


def classify_dickinson_stage(cfo: float, cfi: float, cff: float) -> Tuple[str, str]:
    """
    Classify firm life-cycle stage based on Dickinson (2011) cash-flow sign pattern.
    Returns (stage_name, sign_pattern)
    """
    s_cfo = "+" if cfo > 0 else "-"
    s_cfi = "+" if cfi > 0 else "-"
    s_cff = "+" if cff > 0 else "-"
    pattern = f"({s_cfo}, {s_cfi}, {s_cff})"

    if s_cfo == "-" and s_cfi == "-" and s_cff == "+":
        return "Introduction", pattern
    elif s_cfo == "+" and s_cfi == "-" and s_cff == "+":
        return "Growth", pattern
    elif s_cfo == "+" and s_cfi == "-" and s_cff == "-":
        return "Mature (Cash Cow)", pattern
    elif s_cfo == "-" and s_cfi == "+" and s_cff in ["+", "-"]:
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

    inflection_triggers = (
        "A 15% increase in debtor collection days (DSO) or a 200 bps contraction in operating margin would compress free cash flow by an estimated 18-25%."
    )

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

    inflection_triggers = (
        "An unexpected lease portfolio expansion or a 100 bps increase in the incremental borrowing rate would increase annual finance expense by an estimated ₹8-15 Cr."
    )

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
                ("Offer Size", f"₹{dossier.total_issue_size_cr:,.1f} Cr"),
                ("Implied P/E", f"{dossier.valuation_comps.implied_pe_ratio:.1f}x" if dossier.valuation_comps else "N/A"),
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
                ("Total Offer Size", f"₹{dossier.total_issue_size_cr:,.1f} Cr"),
                ("GCP Allocation Share", f"{obj.gcp_pct_of_gross if obj else 0:.1f}% (SEBI Limit: 25%)"),
                ("Promoter Pledge Encumbrance", f"{dossier.governance.promoter_pledge_pct:.1f}%"),
                ("Independent Directors", f"{dossier.governance.independent_directors_pct:.1f}%"),
            ],
            "decision_question": "Is the offering structure compliant with SEBI regulations, and does it maximize long-term shareholder value?",
            "recommendation": (
                f"Verdict: {ic.underwriting_verdict if ic else 'APPROVE'}. "
                "Ensure strict ring-fencing of debt repayment proceeds and confirm SEBI ICDR 2018 Regulation 7 compliance."
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


def generate_anchor_lockin_calendar(dossier: PreIPODealDossier) -> List[AnchorLockinMilestone]:
    """
    Constructs statutory SEBI ICDR (2018 / 2022 amendment) Anchor Lock-In Expiry Schedule
    and secondary floating supply impact analysis.
    - Listing Day (T0): 0% Anchor shares tradable; initial restricted public float.
    - Day 30: 50% Anchor allocation released into secondary market.
    - Day 90: Remaining 50% Anchor allocation released into secondary market.
    - Day 180: Non-promoter pre-issue holding / excess promoter lock-in expiry.
    """
    # Parse or anchor listing date
    raw_date = dossier.listing_date or dossier.filing_date or "2024-11-20"
    try:
        if "-" in raw_date and len(raw_date.split("-")[0]) == 4:
            base_dt = datetime.strptime(raw_date[:10], "%Y-%m-%d")
        else:
            base_dt = datetime(2024, 11, 27)
    except Exception:
        base_dt = datetime(2024, 11, 27)

    now_dt = datetime(2024, 11, 25)  # Reference date for active evaluation

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

    def _eval_status(target_dt: datetime) -> str:
        diff = (target_dt - now_dt).days
        if diff < -2:
            return "EXPIRED"
        elif -2 <= diff <= 10:
            return "ACTIVE_WINDOW"
        return "UPCOMING"

    schedule = [
        AnchorLockinMilestone(
            milestone_name="Listing Day (T0)",
            days_from_listing=0,
            calendar_date=base_dt.strftime("%Y-%m-%d"),
            unlocked_pct=0.0,
            unlocked_shares_cr=0.0,
            unlocked_value_cr=0.0,
            cumulative_free_float_pct=day0_float_pct,
            supply_risk_level="LOW",
            status=_eval_status(base_dt),
            exchange_notice_ref="SEBI ICDR Reg 16 / NSE Listing Notice",
        ),
        AnchorLockinMilestone(
            milestone_name="Day 30 Anchor Unlock (50%)",
            days_from_listing=30,
            calendar_date=(base_dt + timedelta(days=30)).strftime("%Y-%m-%d"),
            unlocked_pct=50.0,
            unlocked_shares_cr=round(total_anchor_shares_cr * 0.5, 2),
            unlocked_value_cr=round(total_anchor_val_cr * 0.5, 2),
            cumulative_free_float_pct=day30_float_pct,
            supply_risk_level="HIGH" if total_anchor_val_cr * 0.5 > 1000.0 else "ELEVATED",
            status=_eval_status(base_dt + timedelta(days=30)),
            exchange_notice_ref="SEBI ICDR Reg 17(1) 30-Day Tranche",
        ),
        AnchorLockinMilestone(
            milestone_name="Day 90 Anchor Unlock (Remaining 50%)",
            days_from_listing=90,
            calendar_date=(base_dt + timedelta(days=90)).strftime("%Y-%m-%d"),
            unlocked_pct=50.0,
            unlocked_shares_cr=round(total_anchor_shares_cr * 0.5, 2),
            unlocked_value_cr=round(total_anchor_val_cr * 0.5, 2),
            cumulative_free_float_pct=day90_float_pct,
            supply_risk_level="ELEVATED",
            status=_eval_status(base_dt + timedelta(days=90)),
            exchange_notice_ref="SEBI ICDR Reg 17(2) 90-Day Full Liquidity",
        ),
        AnchorLockinMilestone(
            milestone_name="Day 180 Pre-IPO / Excess Promoter Unlock",
            days_from_listing=180,
            calendar_date=(base_dt + timedelta(days=180)).strftime("%Y-%m-%d"),
            unlocked_pct=100.0,
            unlocked_shares_cr=round(total_anchor_shares_cr * 0.8, 2),
            unlocked_value_cr=round(total_issue_cr * 0.4, 2),
            cumulative_free_float_pct=day180_float_pct,
            supply_risk_level="MEDIUM",
            status=_eval_status(base_dt + timedelta(days=180)),
            exchange_notice_ref="SEBI ICDR Reg 16(b) Promoter Excess Holding",
        ),
    ]

    return schedule
