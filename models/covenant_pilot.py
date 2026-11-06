"""Deterministic quarterly covenant mechanics, independent of chat and estimators.

All amounts are INR crore. Demo forecasts and covenants are assumptions, not
loan-compliance or agency-rating opinions. No database writes or network calls.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from hashlib import sha256
import json
import math


class ScenarioInputError(ValueError):
    pass


def _finite(value, name, minimum=None):
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        raise ScenarioInputError(f"{name} must be a finite number")
    if minimum is not None and value < minimum:
        raise ScenarioInputError(f"{name} must be at least {minimum}")


@dataclass(frozen=True)
class CompanySnapshot:
    entity_id: str
    company: str
    as_of: str
    perimeter: str
    earnings_basis: str
    earnings_cr: tuple[float, ...]
    cash_taxes_cr: tuple[float, ...]
    maintenance_capex_cr: tuple[float, ...]
    working_capital_use_cr: tuple[float, ...]
    opening_cash_cr: float
    tangible_net_worth_cr: float | None
    other_liabilities_cr: float | None
    evidence: tuple[dict, ...] = ()


@dataclass(frozen=True)
class DebtSchedule:
    name: str
    opening_balance_cr: float
    annual_rate: float
    floating: bool
    principal_cr: tuple[float, ...]
    source_kind: str = "assumption"


@dataclass(frozen=True)
class LeaseSchedule:
    name: str
    opening_liability_cr: float
    annual_rate: float
    principal_cr: tuple[float, ...]
    variable_rent_cr: tuple[float, ...]
    source_kind: str = "assumption"


@dataclass(frozen=True)
class CovenantSpec:
    dscr_floor: float | None = 1.25
    icr_floor: float | None = 2.0
    tol_tnw_ceiling: float | None = 3.0
    minimum_cash_cr: float = 0.0
    cash_sweep_dscr: float | None = None
    definition: str = "DEMO_CFADS_PRE_FINANCING_OVER_TOTAL_DEBT_SERVICE"


@dataclass(frozen=True)
class ScenarioRequest:
    rate_shock_bps: float = 0.0
    margin_shock_pct: float = 0.0
    incremental_debt_cr: float = 0.0
    incremental_annual_rate: float = 0.09
    lease_in_coverage: bool = True
    search_limit_cr: float = 1_000_000.0


def fingerprint(payload: dict) -> str:
    return sha256(json.dumps(payload, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()).hexdigest()


def _validate(snapshot, debts, leases, covenants, request):
    if not all(str(x).strip() for x in (snapshot.entity_id, snapshot.company, snapshot.as_of,
                                       snapshot.perimeter, snapshot.earnings_basis)):
        raise ScenarioInputError("Company, date, perimeter, and earnings basis are required")
    horizon = len(snapshot.earnings_cr)
    if not 1 <= horizon <= 12:
        raise ScenarioInputError("Horizon must contain 1 to 12 quarters")
    for name in ("earnings_cr", "cash_taxes_cr", "maintenance_capex_cr", "working_capital_use_cr"):
        values = getattr(snapshot, name)
        if len(values) != horizon:
            raise ScenarioInputError(f"{name} must cover every quarter")
        for value in values:
            _finite(value, name, 0 if name in ("cash_taxes_cr", "maintenance_capex_cr") else None)
    _finite(snapshot.opening_cash_cr, "opening_cash_cr", 0)
    for name in ("tangible_net_worth_cr", "other_liabilities_cr"):
        value = getattr(snapshot, name)
        if value is not None:
            _finite(value, name, 0 if name == "other_liabilities_cr" else None)
    for name in ("dscr_floor", "icr_floor", "tol_tnw_ceiling", "cash_sweep_dscr"):
        value = getattr(covenants, name)
        if value is not None:
            _finite(value, name, 0)
            if value == 0:
                raise ScenarioInputError(f"{name} must be positive or disabled")
    _finite(covenants.minimum_cash_cr, "minimum_cash_cr", 0)
    if covenants.definition != "DEMO_CFADS_PRE_FINANCING_OVER_TOTAL_DEBT_SERVICE":
        raise ScenarioInputError("Unsupported covenant definition")
    for name in ("rate_shock_bps", "margin_shock_pct", "incremental_debt_cr",
                 "incremental_annual_rate", "search_limit_cr"):
        _finite(getattr(request, name), name, 0 if name in (
            "incremental_debt_cr", "incremental_annual_rate", "search_limit_cr") else None)
    if request.margin_shock_pct < -100 or request.margin_shock_pct > 100:
        raise ScenarioInputError("Margin shock must be between -100% and +100%")
    if not isinstance(request.lease_in_coverage, bool):
        raise ScenarioInputError("lease_in_coverage must be boolean")
    if request.incremental_annual_rate + request.rate_shock_bps / 10_000 < 0:
        raise ScenarioInputError("Shocked incremental borrowing rate cannot be negative")
    names = [x.name for x in (*debts, *leases)]
    if len(set(names)) != len(names):
        raise ScenarioInputError("Schedule names must be unique")
    for schedule in (*debts, *leases):
        opening = schedule.opening_balance_cr if isinstance(schedule, DebtSchedule) else schedule.opening_liability_cr
        _finite(opening, schedule.name, 0)
        _finite(schedule.annual_rate, "annual_rate", 0)
        if not schedule.name.strip() or len(schedule.principal_cr) != horizon:
            raise ScenarioInputError("Each named schedule must cover the full horizon")
        if isinstance(schedule, DebtSchedule):
            if not isinstance(schedule.floating, bool):
                raise ScenarioInputError("floating must be boolean")
            if schedule.annual_rate + (request.rate_shock_bps / 10_000 if schedule.floating else 0) < 0:
                raise ScenarioInputError("Shocked floating rate cannot be negative")
        else:
            if len(schedule.variable_rent_cr) != horizon:
                raise ScenarioInputError("Variable rent must cover every quarter")
            for value in schedule.variable_rent_cr:
                _finite(value, "variable_rent_cr", 0)
        for value in schedule.principal_cr:
            _finite(value, "principal_cr", 0)
        if sum(schedule.principal_cr) > opening + 1e-7:
            raise ScenarioInputError("Principal repayments exceed opening balance")
    return horizon


def validate_inputs(snapshot, debts, leases, covenants, request):
    """Validate a draft without executing a forecast or headroom search."""
    return _validate(snapshot, debts, leases, covenants, request)


def _path(snapshot, debts, leases, covenants, request, additional=0.0):
    horizon = len(snapshot.earnings_cr)
    new_debt = request.incremental_debt_cr + additional
    debt_balances = [d.opening_balance_cr for d in debts]
    lease_balances = [l.opening_liability_cr for l in leases]
    new_balance = new_debt
    cash = snapshot.opening_cash_cr
    rows, violations, unavailable = [], [], set()
    for q in range(horizon):
        debt_interest = sum(balance * (d.annual_rate + (request.rate_shock_bps / 10_000 if d.floating else 0)) / 4
                            for balance, d in zip(debt_balances, debts))
        debt_interest += new_balance * (request.incremental_annual_rate + request.rate_shock_bps / 10_000) / 4
        debt_principal = sum(d.principal_cr[q] for d in debts) + new_debt / horizon
        lease_interest = sum(balance * l.annual_rate / 4 for balance, l in zip(lease_balances, leases))
        lease_principal = sum(l.principal_cr[q] for l in leases)
        variable_rent = sum(l.variable_rent_cr[q] for l in leases)
        lease_cash = lease_interest + lease_principal + variable_rent
        earnings = snapshot.earnings_cr[q] * (1 + request.margin_shock_pct / 100)
        cfads = earnings - snapshot.cash_taxes_cr[q] - snapshot.maintenance_capex_cr[q] - snapshot.working_capital_use_cr[q]
        coverage_service = debt_interest + debt_principal + (lease_cash if request.lease_in_coverage else 0)
        coverage_interest = debt_interest + (lease_interest if request.lease_in_coverage else 0)
        dscr = cfads / coverage_service if coverage_service > 0 else None
        icr = earnings / coverage_interest if coverage_interest > 0 else None
        # Incremental borrowing is fully spent on capex at inception. All lease
        # payments still reduce cash even when comparing debt-only coverage.
        cash += cfads - debt_interest - debt_principal - lease_cash
        tol = None
        if snapshot.other_liabilities_cr is not None and snapshot.tangible_net_worth_cr is not None and snapshot.tangible_net_worth_cr > 0:
            tol = (sum(debt_balances) + new_balance + sum(lease_balances) + snapshot.other_liabilities_cr) / snapshot.tangible_net_worth_cr
        elif covenants.tol_tnw_ceiling is not None:
            unavailable.add("TOL/TNW needs positive tangible net worth and non-debt liabilities")
        breaches = []
        for label, ratio, floor in (("DSCR", dscr, covenants.dscr_floor), ("ICR", icr, covenants.icr_floor)):
            if floor is not None and ratio is not None and ratio < floor - 1e-9:
                breaches.append(label)
        if covenants.tol_tnw_ceiling is not None and tol is not None and tol > covenants.tol_tnw_ceiling + 1e-9:
            breaches.append("TOL/TNW")
        if cash < covenants.minimum_cash_cr - 1e-7:
            breaches.append("MINIMUM_CASH")
        violations.extend({"quarter": q + 1, "constraint": b} for b in breaches)
        rows.append({
            "quarter": q + 1, "earnings_cr": earnings, "cfads_cr": cfads,
            "debt_interest_cr": debt_interest, "debt_principal_cr": debt_principal,
            "lease_interest_cr": lease_interest, "lease_principal_cr": lease_principal,
            "lease_cash_cr": lease_cash, "closing_cash_cr": cash,
            "dscr": dscr, "icr": icr, "tol_tnw": tol, "breaches": breaches,
            "cash_sweep_triggered": bool(covenants.cash_sweep_dscr is not None and dscr is not None and dscr < covenants.cash_sweep_dscr),
        })
        debt_balances = [max(0, balance - d.principal_cr[q]) for balance, d in zip(debt_balances, debts)]
        lease_balances = [max(0, balance - l.principal_cr[q]) for balance, l in zip(lease_balances, leases)]
        new_balance = max(0, new_balance - new_debt / horizon)
    return {"quarters": rows, "violations": violations, "unavailable": sorted(unavailable),
            "feasible": not violations and not unavailable}


def simulate(snapshot: CompanySnapshot, debts: tuple[DebtSchedule, ...], leases: tuple[LeaseSchedule, ...],
             covenants: CovenantSpec, request: ScenarioRequest) -> dict:
    """Compute baseline, stress, and extra-debt envelope using the same mechanics."""
    _validate(snapshot, debts, leases, covenants, request)
    inputs = {"snapshot": asdict(snapshot), "debts": [asdict(d) for d in debts],
              "leases": [asdict(l) for l in leases], "covenants": asdict(covenants), "request": asdict(request)}
    baseline_request = ScenarioRequest(incremental_annual_rate=request.incremental_annual_rate,
                                      lease_in_coverage=request.lease_in_coverage)
    baseline = _path(snapshot, debts, leases, covenants, baseline_request)
    stressed = _path(snapshot, debts, leases, covenants, request)
    headroom, binding, bounded = None, [], False
    if stressed["unavailable"]:
        binding = ["MISSING_INPUTS"]
    elif not stressed["feasible"]:
        headroom = 0.0
        binding = sorted({v["constraint"] for v in stressed["violations"]})
    else:
        low, high = 0.0, request.search_limit_cr
        if _path(snapshot, debts, leases, covenants, request, high)["feasible"]:
            headroom, binding, bounded = high, ["SEARCH_LIMIT"], True
        else:
            for _ in range(60):
                mid = (low + high) / 2
                if _path(snapshot, debts, leases, covenants, request, mid)["feasible"]:
                    low = mid
                else:
                    high = mid
            headroom = math.floor(low * 100) / 100
            limit_path = _path(snapshot, debts, leases, covenants, request, high + 0.01)
            binding = sorted({v["constraint"] for v in limit_path["violations"]})
    return {
        "schema_version": 1, "simulation_id": fingerprint(inputs), "inputs": inputs,
        "company": snapshot.company, "baseline": baseline, "stressed": stressed,
        "additional_headroom_cr": headroom, "binding_constraints": binding, "search_limit_reached": bounded,
        "status": "partial" if stressed["unavailable"] else "success",
        "validation_status": "NOT_VALIDATED", "simulation_type": "ILLUSTRATIVE_COVENANT_PILOT",
        "limitations": [
            "Public historical figures anchor an illustrative forecast, not actual loan compliance or a credit rating.",
            "CFADS equals pre-financing earnings less specified cash tax, maintenance capex and working-capital use.",
            "Coverage interest uses the declared earnings basis; this is not a contractual EBIT-based ICR.",
            "New debt is spent on capex at inception and repaid equally over the scenario horizon; no capex income is assumed.",
            "Net worth and other liabilities remain constant; lease payments always reduce liquidity.",
            "Cash sweeps are flags only; their waterfall effects are not simulated.",
        ],
    }
