"""Independent known-answer and adversarial cases for quarterly debt mechanics."""
from dataclasses import replace
import json

import pytest

from models.covenant_pilot import (CompanySnapshot, CovenantSpec, DebtSchedule,
                                   LeaseSchedule, ScenarioInputError, ScenarioRequest, simulate)
from models.covenant_chat import handle_query, render_result, run_draft
from models.covenant_examples import example_catalog
from components.covenant_pilot_chat import conversation_state, route


def case():
    snap = CompanySnapshot("known", "Known borrower", "2025-03-31", "Standalone", "EBITDA",
                           (30.0,) * 4, (2.0,) * 4, (3.0,) * 4, (0.0,) * 4,
                           50.0, 100.0, 20.0)
    debts = (DebtSchedule("loan", 100.0, 0.08, True, (10.0,) * 4),)
    return snap, debts, (), CovenantSpec(), ScenarioRequest()


def test_known_answer_quarterly_schedule():
    result = simulate(*case())
    quarters = result["stressed"]["quarters"]
    assert quarters[0]["debt_interest_cr"] == pytest.approx(2.0)
    assert quarters[1]["debt_interest_cr"] == pytest.approx(1.8)
    assert quarters[0]["dscr"] == pytest.approx(25 / 12)
    assert quarters[0]["icr"] == pytest.approx(30 / 2)
    assert quarters[0]["tol_tnw"] == pytest.approx(1.2)
    assert quarters[0]["closing_cash_cr"] == pytest.approx(63)
    # Q1 DSCR: 25/(12 + extra*(1/4 + .09/4)) >= 1.25.
    expected = (25 / 1.25 - 12) / (1 / 4 + .09 / 4)
    assert result["additional_headroom_cr"] == pytest.approx(expected, abs=0.011)
    assert "DSCR" in result["binding_constraints"]


def test_company_specific_results_and_deterministic_replay():
    inputs = case()
    first = simulate(*inputs)
    assert first == simulate(*inputs)
    altered = simulate(replace(inputs[0], earnings_cr=(15.0,) * 4), *inputs[1:])
    assert altered["simulation_id"] != first["simulation_id"]
    assert altered["additional_headroom_cr"] < first["additional_headroom_cr"]
    json.dumps(first, allow_nan=False)


def test_only_floating_debt_receives_rate_shock():
    snap, debts, leases, cov, _ = case()
    req = ScenarioRequest(rate_shock_bps=100)
    floating = simulate(snap, debts, leases, cov, req)
    fixed = simulate(snap, (replace(debts[0], floating=False),), leases, cov, req)
    assert floating["stressed"]["quarters"][0]["debt_interest_cr"] == pytest.approx(2.25)
    assert fixed["stressed"]["quarters"][0]["debt_interest_cr"] == pytest.approx(2.0)


def test_leases_count_once_and_always_affect_liquidity():
    snap, debts, _, cov, _ = case()
    lease = (LeaseSchedule("lease", 40, .1, (4.0,) * 4, (1.0,) * 4),)
    included = simulate(snap, debts, lease, cov, ScenarioRequest())
    excluded = simulate(snap, debts, lease, cov, ScenarioRequest(lease_in_coverage=False))
    a, b = included["stressed"]["quarters"][0], excluded["stressed"]["quarters"][0]
    assert a["lease_cash_cr"] == pytest.approx(6.0)
    assert a["dscr"] == pytest.approx(25 / 18)
    assert b["dscr"] == pytest.approx(25 / 12)
    assert a["closing_cash_cr"] == b["closing_cash_cr"] == pytest.approx(57)
    assert a["tol_tnw"] == b["tol_tnw"] == pytest.approx(1.6)


def test_missing_net_worth_withholds_headroom():
    inputs = case()
    result = simulate(replace(inputs[0], tangible_net_worth_cr=None), *inputs[1:])
    assert result["additional_headroom_cr"] is None
    assert result["status"] == "partial"
    assert result["stressed"]["quarters"][0]["tol_tnw"] is None


def test_negative_net_worth_does_not_pass_compliance():
    inputs = case()
    result = simulate(replace(inputs[0], tangible_net_worth_cr=-1), *inputs[1:])
    assert not result["stressed"]["feasible"]
    assert result["additional_headroom_cr"] is None


def test_zero_interest_denominators_are_na_not_infinity():
    snap, _, leases, cov, req = case()
    result = simulate(snap, (), leases, cov, req)
    assert result["stressed"]["quarters"][0]["icr"] is None
    assert result["stressed"]["quarters"][0]["dscr"] is None
    json.dumps(result, allow_nan=False)


def test_existing_breach_has_zero_headroom_and_no_invented_sweep():
    inputs = case()
    result = simulate(replace(inputs[0], earnings_cr=(1.0,) * 4), *inputs[1:])
    assert result["additional_headroom_cr"] == 0
    assert result["baseline"]["violations"]
    assert not any(q["cash_sweep_triggered"] for q in result["stressed"]["quarters"])
    assert "baseline also" in render_result(result)


@pytest.mark.parametrize("change", [dict(rate_shock_bps=float("nan")), dict(incremental_debt_cr=-1),
                                     dict(margin_shock_pct=-101), dict(lease_in_coverage="yes")])
def test_invalid_request_fails_closed(change):
    snap, debts, leases, cov, req = case()
    with pytest.raises(ScenarioInputError):
        simulate(snap, debts, leases, cov, replace(req, **change))


def test_overpayments_and_misaligned_quarters_rejected():
    snap, debts, leases, cov, req = case()
    with pytest.raises(ScenarioInputError):
        simulate(snap, (replace(debts[0], principal_cr=(30.0,) * 4),), leases, cov, req)
    with pytest.raises(ScenarioInputError):
        simulate(replace(snap, cash_taxes_cr=(1.0,)), debts, leases, cov, req)


def test_covenant_boundary_and_search_bound():
    snap, debts, leases, _, req = case()
    cov = CovenantSpec(dscr_floor=25 / 12, icr_floor=15, tol_tnw_ceiling=1.2)
    assert not simulate(snap, debts, leases, cov, req)["stressed"]["violations"]
    bounded = simulate(snap, debts, leases, CovenantSpec(), replace(req, search_limit_cr=1))
    assert bounded["search_limit_reached"]
    assert bounded["additional_headroom_cr"] == 1


def test_chat_requires_confirmation_and_keeps_followup_assumptions():
    drafted = handle_query("Can Tata Steel fund new debt 10,500 crore with rates +150 bps and margins falling 20%?")
    assert drafted is not None
    # 'falling' is intentionally clarified rather than silently ignored.
    if "draft" not in drafted:
        drafted = handle_query("covenant pilot for Tata Steel rates +150 bps margin -20% new debt 10,500 crore")
    assert "result" not in drafted
    assert drafted["draft"]["request"]["incremental_debt_cr"] == 10500
    confirmed = handle_query("confirm scenario", drafted["state"])
    assert "result" in confirmed
    edited = handle_query("margin -10%", confirmed["state"])
    assert edited["draft"]["request"]["rate_shock_bps"] == 150
    assert edited["draft"]["request"]["incremental_debt_cr"] == 10500
    assert edited["draft"]["request"]["margin_shock_pct"] == -10
    assert "result" not in handle_query("confirm scenario", confirmed["state"])


def test_not_found_and_ambiguous_entities_never_fallback():
    assert "not supported" in handle_query("debt headroom for Missing Borrower")['content']
    assert "Choose one" in handle_query("covenant pilot Tata Steel and IndiGo")['content']
    assert "Choose the public example" in handle_query("debt headroom")['content']
    assert handle_query("explain fixed effects") is None


@pytest.mark.parametrize("query", ["covenant pilot for IndiGo fuel +25%", "covenant pilot for Tata Steel margin 10 percentage points",
                                   "covenant pilot for Tata Steel new debt 10 million", "covenant pilot for Tata Steel rates 1%"])
def test_unsupported_shocks_and_units_do_not_execute(query):
    assert "draft" not in handle_query(query)


def test_scope_and_feature_gate(monkeypatch):
    monkeypatch.delenv("ENABLE_COVENANT_PILOT", raising=False)
    assert route("covenant pilot for Tata Steel", [], "owner:a:thesis") is None
    monkeypatch.setenv("ENABLE_COVENANT_PILOT", "1")
    turn = route("covenant pilot for Tata Steel", [], "owner:a:thesis")
    history = [turn]
    assert conversation_state(history, "owner:a:thesis")["draft"]
    assert conversation_state(history, "other:a:thesis") == {}
    assert conversation_state(history, "owner:b:thesis") == {}
    assert conversation_state(history, "owner:a:latest") == {}


def test_inputs_changed_invalidates_confirmation():
    draft = handle_query("covenant pilot for IndiGo")["draft"]
    draft["source_fingerprint"] = "changed"
    with pytest.raises(ScenarioInputError):
        run_draft(draft)


def test_example_units_and_evidence():
    examples = example_catalog()
    indigo = examples["indigo-fy2025"]
    assert indigo["snapshot"].opening_cash_cr == 33153.1
    assert indigo["snapshot"].earnings_basis == "EBITDAR"
    assert indigo["debts"][0].opening_balance_cr + indigo["leases"][0].opening_liability_cr == pytest.approx(66809.8)
    for example in examples.values():
        assert any(e["kind"] == "observed" for e in example["snapshot"].evidence)
        assert any(e["kind"] == "assumption" for e in example["snapshot"].evidence)
        assert all(d.source_kind == "assumption" for d in example["debts"])
