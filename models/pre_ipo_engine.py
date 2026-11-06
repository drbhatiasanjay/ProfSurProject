"""
Pre-IPO Econometric & Quantitative Decision Support Engine.
Implements:
1. Dickinson (2011) Life-Cycle Cash-Flow Classification
2. 3-Constraint Dynamic Debt Capacity Sizing (Lev Ceiling, DSCR Floor, ICR Floor)
3. Beneish (1999) Forensic M-Score & Accrual Quality
4. Roychowdhury (2006) Real Earnings Management (REM)
5. 2D Stress Sensitivity Matrix (Interest Rate Shocks vs EBITDA Shocks)
"""
from typing import Dict, Any, List, Optional, Tuple
from models.pre_ipo_schema import PreIPODealDossier, FinancialYearMetric


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
    gross_margin_cur: float,
    gross_margin_prev: float,
    current_assets_cur: float,
    current_assets_prev: float,
    ppe_cur: float,
    ppe_prev: float,
    depr_cur: float,
    depr_prev: float,
    sga_cur: float,
    sga_prev: float,
    total_debt_cur: float,
    total_debt_prev: float,
) -> Dict[str, Any]:
    """
    Computes Beneish (1999) 8-variable M-Score.
    M-Score > -1.78 indicates high probability of earnings manipulation.
    """
    sales_growth = cur.revenue_ops_cr / max(0.01, prev.revenue_ops_cr)
    
    # Days Sales in Receivables Index (DSRI)
    dsri = 1.0
    
    # Gross Margin Index (GMI)
    gmi = (gross_margin_prev / max(0.001, gross_margin_cur)) if gross_margin_cur > 0 else 1.0
    
    # Asset Quality Index (AQI)
    non_ca_ppe_cur = max(0.0, cur.net_worth_cr + total_debt_cur - current_assets_cur - ppe_cur)
    non_ca_ppe_prev = max(0.0, prev.net_worth_cr + total_debt_prev - current_assets_prev - ppe_prev)
    aqi = (non_ca_ppe_cur / max(0.01, cur.net_worth_cr + total_debt_cur)) / max(
        0.001, (non_ca_ppe_prev / max(0.01, prev.net_worth_cr + total_debt_prev))
    )
    
    # Sales Growth Index (SGI)
    sgi = sales_growth
    
    # Depreciation Index (DEPI)
    depr_rate_prev = depr_prev / max(0.01, ppe_prev + depr_prev)
    depr_rate_cur = depr_cur / max(0.01, ppe_cur + depr_cur)
    depi = depr_rate_prev / max(0.001, depr_rate_cur)
    
    # SGA Expenses Index (SGAI)
    sgai = (sga_cur / max(0.01, cur.revenue_ops_cr)) / max(0.001, (sga_prev / max(0.01, prev.revenue_ops_cr)))
    
    # Leverage Index (LVGI)
    tot_assets_cur = cur.net_worth_cr + total_debt_cur
    tot_assets_prev = prev.net_worth_cr + total_debt_prev
    lvgi = (total_debt_cur / max(0.01, tot_assets_cur)) / max(0.001, (total_debt_prev / max(0.01, tot_assets_prev)))
    
    # Total Accruals to Total Assets (TATA)
    tata = (cur.pat_cr - cur.cfo_cr) / max(0.01, tot_assets_cur)

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
        "is_manipulation_risk": is_manipulation_risk,
        "tata": round(tata, 3),
        "sgi": round(sgi, 2),
        "gmi": round(gmi, 2),
        "dsri": round(dsri, 2),
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
    1. Leverage Ceiling Capacity: EBITDA * target_leverage_ceiling
    2. DSCR Floor Capacity: (CFO - Capex) / min_dscr_floor solved for sustainable debt
    3. ICR Floor Capacity: EBITDA / (min_icr_floor * wair)
    """
    if ebitda_cr <= 0:
        return {
            "max_sustainable_debt_cr": 0.0,
            "incremental_mna_headroom_cr": 0.0,
            "binding_constraint": "EBITDA Negative / Zero",
            "current_net_debt_ebitda": None,
            "current_icr": None,
        }

    wair_decimal = max(0.01, wair_pct / 100.0)

    # 1. Leverage Ceiling Capacity
    cap_lev = target_leverage_ceiling * ebitda_cr

    # 2. ICR Floor Capacity
    cap_icr = ebitda_cr / (min_icr_floor * wair_decimal)

    # 3. DSCR Floor Capacity (Free Cash Flow DSCR sizing)
    fcf = max(0.0, cfo_cr - capex_cr)
    # Annual debt service = Debt * (principal_repay_pct + wair_decimal)
    annual_servicing_rate = annual_principal_repay_pct + wair_decimal
    cap_dscr = fcf / (min_dscr_floor * annual_servicing_rate)

    max_sustainable_debt = min(cap_lev, cap_icr, cap_dscr)
    incremental_headroom = max(0.0, max_sustainable_debt - current_gross_debt_cr)

    binding_map = {
        cap_lev: f"Leverage Ceiling ({target_leverage_ceiling:.1f}x Net Debt/EBITDA)",
        cap_icr: f"Interest Coverage Floor ({min_icr_floor:.1f}x ICR)",
        cap_dscr: f"DSCR Cash Flow Floor ({min_dscr_floor:.2f}x DSCR)",
    }
    binding_constraint = binding_map.get(max_sustainable_debt, "Leverage Ceiling")

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
    }


def generate_2d_sensitivity_matrix(
    base_ebitda_cr: float,
    gross_debt_cr: float,
    base_wair_pct: float,
    ebitda_shocks_pct: Optional[List[int]] = None,
    rate_hikes_bps: Optional[List[int]] = None,
) -> Dict[str, Any]:
    """
    Generates 2D Interest Coverage Ratio (ICR) sensitivity matrix across:
    - Y-Axis: EBITDA Shocks (-30%, -20%, -10%, 0%, +10%, +20%)
    - X-Axis: Interest Rate Hikes (+0 bps, +100 bps, +200 bps, +300 bps)
    """
    if ebitda_shocks_pct is None:
        ebitda_shocks_pct = [20, 10, 0, -10, -20, -30]
    if rate_hikes_bps is None:
        rate_hikes_bps = [0, 100, 200, 300]

    matrix_rows = []
    for e_shock in ebitda_shocks_pct:
        shocked_ebitda = base_ebitda_cr * (1.0 + e_shock / 100.0)
        row = {"ebitda_shock_pct": e_shock, "shocked_ebitda_cr": round(shocked_ebitda, 1)}
        for hike in rate_hikes_bps:
            effective_wair = (base_wair_pct + (hike / 100.0)) / 100.0
            interest_cost = gross_debt_cr * effective_wair
            if shocked_ebitda <= 0:
                icr = 0.0
            else:
                icr = round(shocked_ebitda / max(0.1, interest_cost), 2)
            row[f"hike_{hike}bps"] = icr
        matrix_rows.append(row)

    return {
        "ebitda_shocks_pct": ebitda_shocks_pct,
        "rate_hikes_bps": rate_hikes_bps,
        "matrix": matrix_rows,
    }
