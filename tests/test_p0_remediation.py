"""
Comprehensive P0 Remediation Test Suite (SW-01 through SW-05).
"""
import pytest
import pandas as pd
from models.agent_tools import (
    describe_financial_database,
    query_financial_database,
    run_live_econometric_model,
    run_cfo_stress_simulation,
)
from models.descriptive_analyst import describe_panel
from models.citation_vault_metadata import (
    get_citation_metadata,
    format_bibtex,
    format_apa,
    format_stata_comment,
)


def test_sw01_two_row_scope_probe():
    """SW-01 Specific Finding: A two-row probe requesting company 1 returns N=1 and mean=10."""
    df_two_row = pd.DataFrame([
        {"company_code": 1, "year": 2020, "leverage": 10.0, "vintage": "thesis"},
        {"company_code": 2, "year": 2020, "leverage": 90.0, "vintage": "thesis"},
    ])
    # Scoped frame for company 1
    scoped_frame = df_two_row[df_two_row["company_code"] == 1]
    run = describe_panel(
        scoped_frame,
        variables=["leverage"],
        run_id="test_probe_1",
        panel_mode="thesis",
        filters={"company_code": 1},
    )
    result = run.result["groups"]["all"]["leverage"]
    assert result["count"] == 1
    assert result["mean"] == 10
    assert run.provenance["n_firms"] == 1
    assert run.provenance["n_obs"] == 1


def test_sw01_describe_financial_database_scoping():
    """SW-01: describe_financial_database strictly enforces vintage, company, and filters."""
    # 1. Scoped query for a single company code (Tata Motors = 248093)
    res = describe_financial_database(
        ["leverage", "profitability"],
        panel_mode="thesis",
        filters={"company_code": 248093, "year_range": (2015, 2020)},
    )
    assert res["status"] == "success", f"Expected success, got: {res}"
    analysis = res["analysis_run"]
    prov = analysis["provenance"]
    assert prov["panel_mode"] == "thesis"
    assert prov["n_firms"] == 1
    assert prov["n_obs"] == 6  # 6 years (2015-2020) for Tata Motors

    # 2. Scoped query with industry group: "Steel"
    res_ind = describe_financial_database(
        ["leverage"],
        panel_mode="thesis",
        filters={"industry_groups": ["Steel"]},
    )
    assert res_ind["status"] == "success"
    assert res_ind["analysis_run"]["provenance"]["n_firms"] > 0
    assert res_ind["analysis_run"]["provenance"]["n_firms"] < 400

    # 3. Empty scope check - non-existent company must return EMPTY_SAMPLE error
    res_empty = describe_financial_database(
        ["leverage"],
        panel_mode="thesis",
        filters={"company_code": 9999999},
    )
    assert res_empty["status"] == "error"
    assert res_empty["error_code"] == "EMPTY_SAMPLE"


def test_sw02_remove_fabricated_citation_metadata():
    """SW-02: Unindexed citations return UNRESOLVED status without fabricated DOIs or titles."""
    meta = get_citation_metadata("NonExistentScholar (2099)")
    assert meta["status"] == "UNRESOLVED"
    assert meta["is_fallback"] is True
    assert meta["doi"] is None
    assert meta["title"] is None
    assert meta["authors"] is None
    assert meta["journal"] is None

    # Verify formatting output contains no fake DOIs
    bib = format_bibtex(meta)
    assert "UNRESOLVED" in bib
    assert "10.1016" not in bib

    apa = format_apa(meta)
    assert "Unresolved Reference" in apa

    stata = format_stata_comment(meta)
    assert "Unresolved Citation" in stata


def test_sw03_truthful_estimator_and_diagnostics():
    """SW-03: Report the estimator actually executed and exact diagnostic p-values."""
    res = run_live_econometric_model(
        dependent_var="leverage",
        independent_vars=["profitability", "tangibility"],
        model_type="auto",
        year_start=2010,
        year_end=2020,
        panel_mode="thesis",
    )
    assert res["status"] == "success"
    # Verify accurate label
    assert res["selected_model"] == "Entity Fixed Effects (Within-Estimator)"
    
    # Verify Hausman reporting carries dynamic statistics
    diag = res["diagnostics"]
    assert "hausman_pvalue" in diag
    reason = res["selection_reason"]
    assert "Entity Fixed Effects" in reason or "Fixed Effects" in reason


def test_sw04_eliminate_silent_company_substitution():
    """SW-04: Unknown companies return COMPANY_NOT_FOUND, never falling back to Tata Motors."""
    res = run_cfo_stress_simulation(
        company_name_or_code="UnknownFictionalFirm999XYZ",
        panel_mode="thesis",
    )
    assert res["status"] == "error"
    assert res["error_code"] == "COMPANY_NOT_FOUND"
    assert "UnknownFictionalFirm999XYZ" in res["error"]


def test_sw05_isolated_honest_cfo_stress_sandbox():
    """SW-05: CFO stress outputs are labeled illustrative sandbox and use measured baselines."""
    res = run_cfo_stress_simulation(
        company_name_or_code="Tata Motors",
        interest_rate_shock_bps=150.0,
        operating_margin_shock_pct=-10.0,
        panel_mode="thesis",
    )
    assert res["status"] == "success"
    assert res["simulation_type"] == "ILLUSTRATIVE_STRESS_SANDBOX"
    assert res["company_code"] == 248093
    assert "measured_baseline" in res
    assert "indicative_financial_health_band" in res["covenant_and_debt_metrics"]
    assert "guardrail_notice" in res
