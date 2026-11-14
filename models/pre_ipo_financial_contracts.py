"""Strict financial metric definitions and verification contracts for Pre-IPO analysis.

Implements PR 4 requirements:
- Offer contract: [●] -> NOT_DISCLOSED, face value rejected as issue price, no price blocks offer valuation.
- EBITDA contract: distinct metric IDs (issuer_ebitda vs operating_profit vs ebit vs cf_profit_before_wc).
- Cash flow contract: signed net CFO, CFI, CFF; capex cannot satisfy CFI; Dickinson classification.
- Net worth contract: separates owners_equity, non_controlling_interest, total_equity, sebi_net_worth.
- Gold comparison target verification for HCCH.
"""

from dataclasses import dataclass, field
from typing import Optional, Dict, List, Any, Union, Tuple
from enum import Enum

class MetricDefinition(str, Enum):
    # EBITDA perimeter
    ISSUER_EBITDA = "issuer_ebitda"
    OPERATING_PROFIT = "operating_profit"
    EBIT = "ebit"
    CF_PROFIT_BEFORE_WC = "cash_flow_operating_profit_before_wc"

    # Cash flows
    CFO_NET = "cfo_net"
    CFI_NET = "cfi_net"
    CFF_NET = "cff_net"
    CAPEX = "capex"

    # Net worth
    OWNERS_EQUITY = "owners_equity"
    NON_CONTROLLING_INTEREST = "non_controlling_interest"
    TOTAL_EQUITY_WITH_NCI = "total_equity_with_nci"
    SEBI_NET_WORTH = "sebi_net_worth"

    # Offer metrics
    FACE_VALUE = "face_value"
    ISSUE_PRICE = "issue_price"
    PRICE_BAND_LOWER = "price_band_lower"
    PRICE_BAND_UPPER = "price_band_upper"
    FRESH_SHARES = "fresh_shares"
    OFS_SHARES = "ofs_shares"
    OFFER_VALUE = "offer_value"


class DickinsonLifeCycle(str, Enum):
    INTRODUCTION = "Introduction"  # (-, -, +)
    GROWTH = "Growth"              # (+, -, +)
    MATURE = "Mature"              # (+, -, -)
    SHAKEOUT = "Shakeout"          # (-, -, -) or (+, +, +)
    DECLINE = "Decline"            # (-, +, -)
    INCONCLUSIVE = "Inconclusive"


# Audited reference gold targets for HCCH parent
HCCH_AUDITED_TARGETS = {
    "EBITDA": {"FY24": 1777.936, "FY25": 1640.019, "FY26": 1353.040},
    "CFI": {"FY24": -291.546, "FY25": -2071.558, "FY26": -219.446},
    "CFF": {"FY24": -125.047, "FY25": 492.878, "FY26": -1771.757},
    "NET_WORTH": {"FY24": 8897.184, "FY25": 9649.798, "FY26": 9760.911},
}


def parse_prospectus_token(val: Optional[str]) -> Tuple[Optional[float], str]:
    """
    Parses prospectus values.
    Returns (numeric_value, presence_state).
    [●] or '-' or 'N.A.' are parsed appropriately.
    """
    if val is None:
        return None, "NOT_DISCLOSED"
    v_clean = str(val).strip()
    if v_clean in ("[●]", "[•]", "●", "•", "undisclosed", "Undisclosed"):
        return None, "NOT_DISCLOSED"
    if v_clean in ("-", "—", "–", "nil", "Nil", "NIL"):
        return 0.0, "EXPLICIT_NIL"
    try:
        # Handle parentheses as negative numbers
        if v_clean.startswith("(") and v_clean.endswith(")"):
            num = -float(v_clean[1:-1].replace(",", "").strip())
        else:
            num = float(v_clean.replace(",", "").strip())
        return num, "OBSERVED_VALUE"
    except ValueError:
        return None, "EXTRACTION_FAILED"


def validate_offer_contract(
    face_value_inr: Optional[float] = None,
    issue_price_inr: Optional[float] = None,
    total_shares: Optional[float] = None,
    offered_shares: Optional[float] = None,
    total_post_issue_shares: Optional[float] = None,
    price_provenance: Optional[str] = None,
    source_metric_id: Optional[str] = None,
    is_at_par: bool = False,
) -> Dict[str, Any]:
    """
    Strict offer contract validation:
    - Face value must NEVER be substituted for issue price unless verified at-par issue.
    - Offer value = (offered_shares * issue_price) / 1e7
    - Market capitalization = (total_post_issue_shares * issue_price) / 1e7
    - If issue price is None/NOT_DISCLOSED, offer value and market cap are NOT_COMPUTABLE.
    """
    # Provenance-aware face value substitution rejection
    is_face_val_provenance = (
        price_provenance in ("FACE_VALUE", "PAR_VALUE") or
        source_metric_id in ("face_value", "face_value_inr", "par_value")
    )
    if is_face_val_provenance and not is_at_par:
        return {
            "valid": False,
            "error": "REJECTED: Face value provenance detected in issue price input for a book-building offer.",
            "offer_value_cr": None,
            "market_cap_cr": None,
            "is_priced": False,
        }

    if issue_price_inr is not None and face_value_inr is not None:
        if issue_price_inr == face_value_inr and face_value_inr in (1.0, 2.0, 5.0, 10.0) and not is_at_par:
            return {
                "valid": False,
                "error": "REJECTED: Face value cannot be used as issue price in a book-building offer.",
                "offer_value_cr": None,
                "market_cap_cr": None,
                "is_priced": False,
            }

    if issue_price_inr is None:
        return {
            "valid": True,
            "is_priced": False,
            "offer_value_cr": None,
            "market_cap_cr": None,
            "reason": "Price not disclosed in DRHP [●]. Offer value and market cap not computable under SEBI ICDR 2018.",
        }

    # Distinctly resolve offer value and market capitalization
    offer_val = round((issue_price_inr * offered_shares) / 10000000.0, 2) if offered_shares is not None else None

    # Market capitalization uses total post-issue shares
    effective_post_shares = total_post_issue_shares if total_post_issue_shares is not None else total_shares
    mcap_val = round((issue_price_inr * effective_post_shares) / 10000000.0, 2) if effective_post_shares is not None else None

    return {
        "valid": True,
        "is_priced": True,
        "offer_value_cr": offer_val,
        "market_cap_cr": mcap_val,
        "offered_shares": offered_shares,
        "total_post_issue_shares": effective_post_shares,
    }


def validate_ebitda_metric(metric_id: str, value: float) -> Dict[str, Any]:
    """
    Strict EBITDA input contract:
    Fails if cash-flow operating profit before working capital changes or EBIT is passed as EBITDA.
    """
    if metric_id == MetricDefinition.CF_PROFIT_BEFORE_WC.value:
        return {
            "accepted": False,
            "error": "REJECTED: Cash-flow operating profit before working-capital changes cannot satisfy operating EBITDA contract.",
        }
    if metric_id == MetricDefinition.EBIT.value:
        return {
            "accepted": False,
            "error": "REJECTED: EBIT cannot be passed directly into EBITDA without depreciation and amortization add-back.",
        }
    if metric_id in (MetricDefinition.ISSUER_EBITDA.value, MetricDefinition.OPERATING_PROFIT.value):
        return {
            "accepted": True,
            "value": value,
            "metric_id": metric_id,
        }
    return {
        "accepted": False,
        "error": f"REJECTED: Unrecognized or non-EBITDA metric ID '{metric_id}'.",
    }


def validate_cash_flow_inputs(
    cfo: Optional[float],
    cfi: Optional[float],
    cff: Optional[float],
    capex_proxy: Optional[float] = None
) -> Dict[str, Any]:
    """
    Strict Cash-flow contract:
    - Capex cannot satisfy CFI!
    - CFI and CFF must be signed totals.
    - Zero is not treated as negative.
    """
    if cfi is None and capex_proxy is not None:
        return {
            "valid": False,
            "error": "REJECTED: Capex proxy substitution for CFI is strictly prohibited.",
            "dickinson_stage": None,
        }

    if cfo is None or cfi is None or cff is None:
        return {
            "valid": False,
            "error": "Missing one or more required cash flow totals (CFO, CFI, CFF).",
            "dickinson_stage": None,
        }

    # Dickinson classification
    cfo_pos = cfo > 0
    cfi_neg = cfi < 0
    cff_pos = cff > 0

    if cfo_pos and cfi_neg and cff_pos:
        stage = DickinsonLifeCycle.GROWTH
    elif cfo_pos and cfi_neg and not cff_pos:
        stage = DickinsonLifeCycle.MATURE
    elif not cfo_pos and cfi_neg and cff_pos:
        stage = DickinsonLifeCycle.INTRODUCTION
    elif not cfo_pos and not cfi_neg and not cff_pos:
        stage = DickinsonLifeCycle.DECLINE
    else:
        stage = DickinsonLifeCycle.SHAKEOUT

    return {
        "valid": True,
        "cfo": cfo,
        "cfi": cfi,
        "cff": cff,
        "dickinson_stage": stage.value,
        "signs": (f"{'+' if cfo_pos else '-'}", f"{'-' if cfi_neg else '+'}", f"{'+' if cff_pos else '-'}"),
    }


def validate_net_worth_contract(
    metric_id: str,
    value: float,
    nci: Optional[float] = None,
    total_equity_with_nci: Optional[float] = None
) -> Dict[str, Any]:
    """
    Strict net-worth contract:
    Total equity including NCI cannot satisfy SEBI/issuer net worth if NCI is present.
    """
    if metric_id == MetricDefinition.TOTAL_EQUITY_WITH_NCI.value:
        if nci is not None and nci > 0:
            return {
                "accepted": False,
                "error": "REJECTED: Total equity including NCI cannot satisfy Net Worth contract when non-controlling interest exists.",
            }

    if metric_id in (MetricDefinition.SEBI_NET_WORTH.value, MetricDefinition.OWNERS_EQUITY.value):
        return {
            "accepted": True,
            "net_worth_cr": value,
            "definition": metric_id,
        }

    return {
        "accepted": False,
        "error": f"REJECTED: Metric {metric_id} is not valid for Net Worth.",
    }
