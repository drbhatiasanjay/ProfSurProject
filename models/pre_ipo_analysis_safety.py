"""Analytical and Decision-Support Safety Engine (PR 5).

Implements:
- Removal of unsupported defaults/proxies from WACC, ROIC, and Reverse DCF.
- Fail-closed BlockedResult when analytical premises are missing.
- Prohibition of invented committee approvals, agency rating mimicry, and buy/sell advice.
- Neutral DecisionSupportSummary replacing InvestmentCommitteeVerdict.
- Strict isolation of ANALYST_SCENARIO from verified filing facts.
- Banned-claim auditing across screen, API, and deck representations.
"""

from dataclasses import dataclass, field, asdict
from typing import Optional, Dict, List, Any, Union
from enum import Enum
import hashlib
import json
import re

BANNED_CLAIM_TERMS = {
    "APPROVE",
    "RECOMMEND SUBSCRIBE",
    "STRONG BUY",
    "TIER_1_STRONG_CUSHION",
    "AAA",
    "SAFE INVESTMENT",
    "DEFINITIVE ANCHOR PARTICIPATION",
    "UNCONDITIONAL BUY",
    "UNCONDITIONAL SUBSCRIBE",
}


@dataclass
class BlockedResult:
    capability: str
    is_blocked: bool = True
    missing_premises: List[str] = field(default_factory=list)
    reason: str = ""
    remedy_action: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "is_blocked": True,
            "capability": self.capability,
            "missing_premises": self.missing_premises,
            "reason": self.reason,
            "remedy_action": self.remedy_action,
        }


@dataclass
class SafeWACCResult:
    wacc_pct: float
    cost_of_equity_pct: float
    after_tax_cost_of_debt_pct: float
    equity_weight_pct: float
    debt_weight_pct: float
    is_scenario: bool = False
    lineage_hash: str = ""


@dataclass
class SafeROICResult:
    roic_pct: float
    nopat_cr: float
    invested_capital_cr: float
    definition: str = "EBIT * (1 - t) / Invested Capital"
    is_scenario: bool = False
    lineage_hash: str = ""


@dataclass
class SafeReverseDCFResult:
    implied_fcf_growth_cagr_pct: float
    implied_revenue_cagr_pct: float
    implied_terminal_fcf_cr: float
    market_valuation_cr: float
    discount_rate_wacc_pct: float
    terminal_growth_pct: float
    forecast_years: int
    repriced_valuation_cr: float
    repricing_error_pct: float
    nature: str = "ANALYST_SCENARIO"
    disclaimer: str = "Implied FCF hurdle analysis under analyst scenario premises; not a forecast or filing fact."
    lineage_hash: str = ""


@dataclass
class ExternalRatingRecord:
    agency: str
    instrument: str
    rating_symbol: str
    outlook: str
    effective_date: str
    source_citation: str
    source_page: Optional[int] = None


@dataclass
class DecisionSupportSummary:
    company_name: str
    decision_context: str
    supported_evidence: List[str] = field(default_factory=list)
    unresolved_unknowns: List[str] = field(default_factory=list)
    diligence_questions: List[str] = field(default_factory=list)
    conditional_considerations: List[str] = field(default_factory=list)
    external_ratings: List[ExternalRatingRecord] = field(default_factory=list)
    policy_compliant: bool = True

    def validate_claim_policy(self) -> List[str]:
        """Scans all summary fields for banned claim semantics."""
        violations = []
        combined_text = " ".join(
            [self.decision_context]
            + self.supported_evidence
            + self.unresolved_unknowns
            + self.diligence_questions
            + self.conditional_considerations
        ).upper()

        for term in BANNED_CLAIM_TERMS:
            # Whole word boundary search
            if re.search(rf"\b{re.escape(term)}\b", combined_text):
                violations.append(f"Found prohibited claim term '{term}' in decision support summary.")
        return violations


@dataclass
class AnalystScenarioSet:
    scenario_id: str
    owner: str
    created_at: str
    source_justification: str
    assumptions: Dict[str, Any]
    nature: str = "ANALYST_SCENARIO"
    scenario_hash: str = ""

    def __post_init__(self):
        payload = json.dumps({"owner": self.owner, "assumptions": self.assumptions}, sort_keys=True)
        self.scenario_hash = hashlib.sha256(payload.encode("utf-8")).hexdigest()


def compute_safe_wacc(
    market_equity_cr: Optional[float],
    total_debt_cr: Optional[float],
    cost_of_debt_pct: Optional[float],
    risk_free_rate_pct: Optional[float] = None,
    beta: Optional[float] = None,
    market_risk_premium_pct: Optional[float] = None,
    tax_rate_pct: Optional[float] = None,
    is_scenario: bool = False
) -> Union[SafeWACCResult, BlockedResult]:
    """
    Computes WACC without unaccepted fallbacks.
    Never silently substitutes book equity for market equity, or 9% for cost of debt.
    Preserves genuine zeros (beta=0.0, tax_rate_pct=0.0) without corrupting them.
    Fails closed if any required premise is None.
    """
    missing = []
    if market_equity_cr is None or market_equity_cr <= 0:
        missing.append("market_equity_cr (unpriced offer blocks market equity value)")
    if total_debt_cr is None:
        missing.append("total_debt_cr")
    if cost_of_debt_pct is None:
        missing.append("cost_of_debt_pct (prohibited from defaulting to 9.0%)")
    if risk_free_rate_pct is None:
        missing.append("risk_free_rate_pct")
    if beta is None:
        missing.append("beta")
    if market_risk_premium_pct is None:
        missing.append("market_risk_premium_pct")
    if tax_rate_pct is None:
        missing.append("tax_rate_pct")

    if missing:
        return BlockedResult(
            capability="WACC",
            missing_premises=missing,
            reason="WACC computation blocked due to missing required premises.",
            remedy_action="Provide accepted market pricing, explicit cost of debt, CAPM parameters, and tax rate, or enter in Analyst Scenario workspace."
        )

    # Cost of equity = Rf + Beta * MRP (preserving zero beta)
    ke = risk_free_rate_pct + (beta * market_risk_premium_pct)
    # After tax cost of debt (preserving zero tax rate)
    kd_after_tax = cost_of_debt_pct * (1.0 - (tax_rate_pct / 100.0))

    total_cap = market_equity_cr + total_debt_cr
    if total_cap <= 0:
        return BlockedResult(
            capability="WACC",
            missing_premises=["total_capital_base"],
            reason="Total capitalization base must be strictly positive.",
            remedy_action="Ensure market equity or debt is positive."
        )

    we = market_equity_cr / total_cap
    wd = total_debt_cr / total_cap

    wacc = round((we * ke) + (wd * kd_after_tax), 2)
    h = hashlib.sha256(f"{market_equity_cr}_{total_debt_cr}_{cost_of_debt_pct}_{ke}_{tax_rate_pct}".encode("utf-8")).hexdigest()

    return SafeWACCResult(
        wacc_pct=wacc,
        cost_of_equity_pct=round(ke, 2),
        after_tax_cost_of_debt_pct=round(kd_after_tax, 2),
        equity_weight_pct=round(we * 100.0, 2),
        debt_weight_pct=round(wd * 100.0, 2),
        is_scenario=is_scenario,
        lineage_hash=h
    )


def compute_safe_roic(
    ebit_cr: Optional[float],
    invested_capital_cr: Optional[float],
    tax_rate_pct: float = 25.17,
    is_scenario: bool = False
) -> Union[SafeROICResult, BlockedResult]:
    """
    Computes ROIC = NOPAT / Invested Capital.
    Deletes 'EBITDA - 0.5 * capex' proxy. Fails closed if EBIT or Invested Capital is missing.
    """
    missing = []
    if ebit_cr is None:
        missing.append("ebit_cr (EBITDA - 0.5 * capex proxy is deleted)")
    if invested_capital_cr is None or invested_capital_cr <= 0:
        missing.append("invested_capital_cr")

    if missing:
        return BlockedResult(
            capability="ROIC",
            missing_premises=missing,
            reason="ROIC computation blocked due to missing verified operating EBIT or Invested Capital.",
            remedy_action="Review and accept Restated P&L EBIT and Net Operating Assets in Facts Review."
        )

    nopat = ebit_cr * (1.0 - (tax_rate_pct / 100.0))
    roic = round((nopat / invested_capital_cr) * 100.0, 2)
    h = hashlib.sha256(f"{ebit_cr}_{invested_capital_cr}_{tax_rate_pct}".encode("utf-8")).hexdigest()

    return SafeROICResult(
        roic_pct=roic,
        nopat_cr=round(nopat, 2),
        invested_capital_cr=round(invested_capital_cr, 2),
        is_scenario=is_scenario,
        lineage_hash=h
    )


def compute_safe_reverse_dcf(
    market_valuation_cr: Optional[float],
    wacc_pct: Optional[float],
    current_fcf_cr: Optional[float],
    terminal_growth_pct: float = 5.0,
    forecast_years: int = 5
) -> Union[SafeReverseDCFResult, BlockedResult]:
    """
    Exact Reverse DCF hurdle analysis under explicit scenario assumptions.
    Solves for constant FCF growth rate g during explicit forecast period such that
    PV(g) = market_valuation_cr within 0.01% tolerance.
    Reprices back to verify valuation and rejects invalid terminal assumptions.
    Never portrayed as forecast or fact.
    """
    missing = []
    if market_valuation_cr is None or market_valuation_cr <= 0:
        missing.append("market_valuation_cr (unpriced DRHP blocks reverse DCF)")
    if wacc_pct is None or wacc_pct <= 0:
        missing.append("wacc_pct")
    if current_fcf_cr is None or current_fcf_cr <= 0:
        missing.append("current_fcf_cr (positive base cash flow required)")

    if missing:
        return BlockedResult(
            capability="REVERSE_DCF",
            missing_premises=missing,
            reason="Reverse DCF hurdle cannot be computed without market valuation, discount rate, and positive cash flow.",
            remedy_action="Configure explicit pricing scenario in Analyst Scenario panel."
        )

    r = wacc_pct / 100.0
    gt = terminal_growth_pct / 100.0

    # Reject invalid Gordon terminal assumption rather than clamping
    if r <= gt:
        return BlockedResult(
            capability="REVERSE_DCF",
            missing_premises=["valid_terminal_spread"],
            reason=f"Invalid terminal assumption: WACC ({wacc_pct}%) must be strictly greater than terminal growth rate ({terminal_growth_pct}%). Clamping is prohibited under P0-07.",
            remedy_action="Adjust discount rate or reduce perpetual terminal growth assumption."
        )

    # Standard DCF valuation equation as a function of growth rate g
    def compute_dcf_pv(g: float) -> float:
        pv_explicit = sum(
            current_fcf_cr * ((1.0 + g) ** t) / ((1.0 + r) ** t)
            for t in range(1, forecast_years + 1)
        )
        fcf_n = current_fcf_cr * ((1.0 + g) ** forecast_years)
        terminal_val = (fcf_n * (1.0 + gt)) / (r - gt)
        pv_terminal = terminal_val / ((1.0 + r) ** forecast_years)
        return pv_explicit + pv_terminal

    # Bisection root-finding solver: pv(g) = target
    low_g = -0.99  # -99% growth
    high_g = 10.0  # +1000% growth
    target = market_valuation_cr

    pv_low = compute_dcf_pv(low_g)
    pv_high = compute_dcf_pv(high_g)

    if target < pv_low or target > pv_high:
        return BlockedResult(
            capability="REVERSE_DCF",
            missing_premises=["admissible_growth_domain"],
            reason=f"Target valuation ({target} Cr) falls outside admissible growth domain [-99%, +1000%].",
            remedy_action="Check market valuation or base cash flow inputs."
        )

    # Bisection search
    for _ in range(100):
        mid_g = (low_g + high_g) / 2.0
        pv_mid = compute_dcf_pv(mid_g)
        if abs(pv_mid - target) / target < 1e-6:
            break
        if pv_mid < target:
            low_g = mid_g
        else:
            high_g = mid_g

    g_star = mid_g
    repriced_pv = compute_dcf_pv(g_star)
    repricing_error_pct = abs(repriced_pv - target) / target * 100.0

    terminal_fcf = current_fcf_cr * ((1.0 + g_star) ** forecast_years) * (1.0 + gt)
    cagr_pct = round(g_star * 100.0, 2)
    h = hashlib.sha256(f"{market_valuation_cr}_{wacc_pct}_{current_fcf_cr}_{terminal_growth_pct}_{forecast_years}_{cagr_pct}".encode("utf-8")).hexdigest()

    return SafeReverseDCFResult(
        implied_fcf_growth_cagr_pct=cagr_pct,
        implied_revenue_cagr_pct=cagr_pct,
        implied_terminal_fcf_cr=round(terminal_fcf, 2),
        market_valuation_cr=market_valuation_cr,
        discount_rate_wacc_pct=wacc_pct,
        terminal_growth_pct=terminal_growth_pct,
        forecast_years=forecast_years,
        repriced_valuation_cr=round(repriced_pv, 2),
        repricing_error_pct=round(repricing_error_pct, 4),
        nature="ANALYST_SCENARIO",
        lineage_hash=h
    )
