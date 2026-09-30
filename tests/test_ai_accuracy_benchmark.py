# SW-16 Deterministic Accuracy Benchmark
import pytest
from models.agent_tools import (
    describe_financial_database,
    run_stata_command,
    run_cfo_stress_simulation,
)
from models.citation_vault_metadata import get_citation_metadata

def test_sw16_deterministic_mean_accuracy():
    res = describe_financial_database(["leverage", "profitability", "tangibility"], panel_mode="thesis")
    assert res["status"] == "success"
    groups = res["analysis_run"]["result"]["groups"]["all"]
    assert res["analysis_run"]["provenance"]["n_obs"] == 8677
    assert groups["leverage"]["count"] == 8677
    assert 20.0 <= groups["leverage"]["mean"] <= 25.0
    assert 0.20 <= groups["tangibility"]["mean"] <= 0.35

def test_sw16_correct_abstention_on_unknown_firm():
    res = run_cfo_stress_simulation(company_name_or_code="NON_EXISTENT_PSEUDO_CORP_99999")
    assert res["status"] == "error"
    assert res["error_code"] == "COMPANY_NOT_FOUND"
    assert "resolved_code" not in res or res.get("resolved_code") is None

def test_sw16_correct_abstention_on_unsupported_stata_command():
    res = run_stata_command("xtabond leverage profitability")
    assert res["status"] in ["unsupported", "error", "experimental_notice"]
    assert "r(199)" in res["ascii_output"] or "proxy" in res["ascii_output"].lower() or "experimental" in res["ascii_output"].lower() or "unrecognized" in res["ascii_output"].lower()

def test_sw16_correct_abstention_on_unindexed_citation():
    cit = get_citation_metadata("blundell_bond_1998")
    assert cit is not None
    assert cit["status"] == "UNRESOLVED"
    assert cit["doi"] is None
    assert cit["title"] is None

def test_sw16_scope_switch_isolation():
    res_thesis = describe_financial_database(["leverage"], panel_mode="thesis")
    res_bf = describe_financial_database(["leverage"], panel_mode="bf2001_25_sept26")
    assert res_thesis["analysis_run"]["provenance"]["panel_mode"] == "thesis"
    assert res_bf["analysis_run"]["provenance"]["panel_mode"] == "bf2001_25_sept26"
    assert res_thesis["analysis_run"]["provenance"]["n_obs"] == 8677

def test_sw16_scenario_assumptions_separation():
    res = run_cfo_stress_simulation(company_name_or_code="Tata Motors", interest_rate_shock_bps=100.0, operating_margin_shock_pct=-15.0, panel_mode="thesis")
    assert res["status"] == "success"
    assert res["simulation_type"] == "ILLUSTRATIVE_STRESS_SANDBOX"
    assert "indicative_financial_health_band" in res["covenant_and_debt_metrics"]
    assert "rating_grade" not in res["covenant_and_debt_metrics"]
