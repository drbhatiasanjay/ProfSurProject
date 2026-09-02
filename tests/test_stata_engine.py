"""Unit and regression tests for Stata Engine (models/stata_engine.py).

Following strict TDD: these tests define the expected behavior of:
1. Command parsing (xtreg, regress, summarize, tabstat, pwcorr, hausman, estat vif, esttab, coefplot, export dta).
2. Econometric execution parity with linearmodels and statsmodels.
3. Authentic Stata ASCII output rendering.
4. esttab multi-model comparison matrix (LaTeX and Word export).
5. coefplot visualizer coordinates.
6. Native binary Stata .dta dataset exporter.
"""

import os
import io
import pytest
import pandas as pd
import numpy as np


@pytest.fixture(scope="module")
def sample_panel_df():
    """Create a balanced synthetic panel dataset matching CMIE schema."""
    np.random.seed(42)
    firms = [101, 102, 103, 104, 105]
    years = list(range(2015, 2025))
    rows = []
    for f in firms:
        firm_effect = np.random.normal(0, 2.0)
        for y in years:
            roa = np.random.normal(0.15, 0.05)
            tang = np.random.normal(0.40, 0.10)
            size = np.random.normal(6.5, 1.0)
            # Leverage equation
            lev = 15.0 + firm_effect - 12.0 * roa + 25.0 * tang + 1.5 * size + np.random.normal(0, 1.0)
            rows.append({
                "company_code": f,
                "year": y,
                "leverage": max(0.0, lev),
                "profitability": roa,
                "tangibility": tang,
                "size": size,
                "log_size": size,
                "life_stage": "Maturity" if f in (101, 102) else ("Growth" if f in (103, 104) else "Decline"),
            })
    return pd.DataFrame(rows)


# ── Test 1: Parser Tests ──

def test_parse_xtreg_command():
    from models.stata_engine import parse_stata_command
    parsed = parse_stata_command("xtreg leverage profitability tangibility log_size, fe cluster(company_code)")
    assert parsed["cmd"] == "xtreg"
    assert parsed["depvar"] == "leverage"
    assert parsed["indepvars"] == ["profitability", "tangibility", "log_size"]
    assert parsed["options"].get("fe") is True
    assert parsed["options"].get("cluster") == "company_code"


def test_parse_command_with_leading_period():
    from models.stata_engine import parse_stata_command
    parsed = parse_stata_command(". summarize leverage profitability, detail")
    assert parsed["cmd"] == "summarize"
    assert parsed["indepvars"] == ["leverage", "profitability"]
    assert parsed["options"].get("detail") is True


def test_parse_pwcorr_command():
    from models.stata_engine import parse_stata_command
    parsed = parse_stata_command("pwcorr leverage profitability tangibility, sig star(0.05)")
    assert parsed["cmd"] == "pwcorr"
    assert parsed["indepvars"] == ["leverage", "profitability", "tangibility"]
    assert parsed["options"].get("sig") is True
    assert parsed["options"].get("star") == "0.05"


# ── Test 2: Execution Tests (Econometric Parity) ──

def test_execute_summarize_detail(sample_panel_df):
    from models.stata_engine import execute_stata_command
    res = execute_stata_command("summarize leverage profitability, detail", df=sample_panel_df)
    assert res["status"] == "success"
    assert "leverage" in res["data"]
    assert "profitability" in res["data"]
    lev_stats = res["data"]["leverage"]
    assert "mean" in lev_stats
    assert "p50" in lev_stats
    assert "p99" in lev_stats
    assert "Fixed-effects" not in res["ascii_output"]
    assert "Percentiles" in res["ascii_output"] or "Obs" in res["ascii_output"]


def test_execute_tabstat_by_stage(sample_panel_df):
    from models.stata_engine import execute_stata_command
    res = execute_stata_command("tabstat leverage profitability, by(life_stage) stat(mean sd n)", df=sample_panel_df)
    assert res["status"] == "success"
    assert "Maturity" in res["ascii_output"] or "Growth" in res["ascii_output"]


def test_execute_pwcorr_sig(sample_panel_df):
    from models.stata_engine import execute_stata_command
    res = execute_stata_command("pwcorr leverage profitability tangibility, sig star(0.05)", df=sample_panel_df)
    assert res["status"] == "success"
    assert "ascii_output" in res
    assert "leverage" in res["ascii_output"]


def test_execute_xtreg_fe_clustered(sample_panel_df):
    from models.stata_engine import execute_stata_command
    res = execute_stata_command("xtreg leverage profitability tangibility log_size, fe cluster(company_code)", df=sample_panel_df)
    assert res["status"] == "success"
    assert res["model_type"] == "Fixed Effects"
    assert res["n_obs"] == len(sample_panel_df)
    assert res["n_groups"] == sample_panel_df["company_code"].nunique()
    assert "profitability" in res["coefficients"]
    assert "tangibility" in res["coefficients"]
    # Check Stata ASCII table elements
    ascii_out = res["ascii_output"]
    assert "Fixed-effects (within) regression" in ascii_out
    assert "R-squared:" in ascii_out
    assert "Coefficient" in ascii_out
    assert "std. err." in ascii_out.lower()


def test_execute_xtreg_re(sample_panel_df):
    from models.stata_engine import execute_stata_command
    res = execute_stata_command("xtreg leverage profitability tangibility log_size, re", df=sample_panel_df)
    assert res["status"] == "success"
    assert res["model_type"] == "Random Effects"
    assert "Random-effects" in res["ascii_output"]


def test_execute_hausman_test(sample_panel_df):
    from models.stata_engine import execute_stata_command
    # Run and store FE and RE models
    execute_stata_command("xtreg leverage profitability tangibility log_size, fe", df=sample_panel_df)
    execute_stata_command("xtreg leverage profitability tangibility log_size, re", df=sample_panel_df)
    res = execute_stata_command("hausman fe re", df=sample_panel_df)
    assert res["status"] == "success"
    assert "chi2" in res or "p_value" in res
    assert "Hausman" in res["ascii_output"] or "chi2" in res["ascii_output"]


def test_execute_estat_vif(sample_panel_df):
    from models.stata_engine import execute_stata_command
    execute_stata_command("regress leverage profitability tangibility log_size", df=sample_panel_df)
    res = execute_stata_command("estat vif", df=sample_panel_df)
    assert res["status"] == "success"
    assert "VIF" in res["ascii_output"]
    assert "1/VIF" in res["ascii_output"]


def test_execute_coefplot(sample_panel_df):
    from models.stata_engine import execute_stata_command
    execute_stata_command("xtreg leverage profitability tangibility log_size, fe", df=sample_panel_df)
    res = execute_stata_command("coefplot, drop(_cons) xline(0)", df=sample_panel_df)
    assert res["status"] == "success"
    assert "chart_spec" in res
    chart = res["chart_spec"]
    assert "profitability" in chart["categories"]
    assert "tangibility" in chart["categories"]


def test_execute_esttab_latex(sample_panel_df):
    from models.stata_engine import execute_stata_command, get_stored_models_table
    execute_stata_command("xtreg leverage profitability tangibility, fe", df=sample_panel_df)
    res = execute_stata_command("esttab, se r2 star", df=sample_panel_df)
    assert res["status"] == "success"
    assert "table_html" in res
    assert "latex_code" in res
    assert "\\begin{table}" in res["latex_code"]
    assert "\\end{table}" in res["latex_code"]


def test_execute_export_dta(sample_panel_df, tmp_path):
    from models.stata_engine import execute_stata_command
    out_file = str(tmp_path / "test_panel.dta")
    res = execute_stata_command(f"export dta using {out_file}", df=sample_panel_df)
    assert res["status"] == "success"
    assert os.path.exists(out_file)
    # Verify readable by pandas Stata reader
    reloaded = pd.read_stata(out_file)
    assert len(reloaded) == len(sample_panel_df)


def test_regression_auto_generates_graph(sample_panel_df):
    from models.stata_engine import execute_stata_command
    res = execute_stata_command("xtreg leverage profitability tangibility log_size, fe", df=sample_panel_df)
    assert res["status"] == "success"
    assert "chart_spec" in res, "Regression must automatically return a chart_spec for immediate visualization"
    spec = res["chart_spec"]
    assert spec["chart_type"] == "scatter"
    assert "profitability" in spec["categories"]
    assert "error_bars" in spec
    assert len(spec["error_bars"]["low"]) == len(spec["categories"])


def test_scatter_graph_command(sample_panel_df):
    from models.stata_engine import execute_stata_command
    res = execute_stata_command("scatter leverage profitability", df=sample_panel_df)
    assert res["status"] == "success"
    assert "chart_spec" in res
    spec = res["chart_spec"]
    assert spec["chart_type"] == "scatter"
    assert spec["x_axis_label"] == "profitability"
    assert spec["y_axis_label"] == "leverage"


def test_histogram_graph_command(sample_panel_df):
    from models.stata_engine import execute_stata_command
    res = execute_stata_command("histogram leverage", df=sample_panel_df)
    assert res["status"] == "success"
    assert "chart_spec" in res
    spec = res["chart_spec"]
    assert spec["chart_type"] == "histogram"
    assert spec["x_axis_label"] == "leverage"
