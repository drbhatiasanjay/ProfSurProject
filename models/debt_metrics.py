"""Shared static coverage arithmetic; missing evidence never implies capacity."""
import math


def finite(value):
    try:
        result = float(value)
        return result if math.isfinite(result) else None
    except (TypeError, ValueError):
        return None


def coverage_case(pbit, interest, debt, *, new_debt=0, new_rate=0,
                  floating_share=None, shock_bps=0, earnings_decline=0):
    """Amounts keep source units, rate is percent, shares/decline are fractions."""
    pbit, interest, debt = map(finite, (pbit, interest, debt))
    new_debt, new_rate, shock_bps, earnings_decline = map(finite, (new_debt, new_rate, shock_bps, earnings_decline))
    if any(v is None for v in (new_debt, new_rate, shock_bps, earnings_decline)):
        raise ValueError("Scenario assumptions must be finite numbers.")
    if new_debt < 0 or new_rate < 0 or shock_bps < 0 or not 0 <= earnings_decline <= 1:
        raise ValueError("Amounts/rates must be nonnegative and earnings decline between 0 and 1.")
    exposed = finite(floating_share)
    if exposed is not None and not 0 <= exposed <= 1:
        raise ValueError("Floating share must be between 0 and 1.")
    adjusted_pbit = pbit * (1 - earnings_decline) if pbit is not None else None
    shock_cost = 0 if shock_bps == 0 else (
        (debt * exposed + new_debt) * shock_bps / 10000
        if debt is not None and debt >= 0 and exposed is not None else None)
    adjusted_interest = (interest + new_debt * new_rate / 100 + shock_cost
        if interest is not None and interest >= 0 and shock_cost is not None else None)
    return dict(pbit=adjusted_pbit, annual_interest=adjusted_interest,
        coverage=adjusted_pbit / adjusted_interest
        if adjusted_pbit is not None and adjusted_interest is not None and adjusted_interest > 0 else None)
