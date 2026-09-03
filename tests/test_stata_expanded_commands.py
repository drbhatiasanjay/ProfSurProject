import pytest
import pandas as pd
import numpy as np
from models.stata_engine import execute_stata_command, parse_stata_command


@pytest.fixture
def panel_data():
    np.random.seed(42)
    n_firms = 20
    years = list(range(2010, 2020))
    records = []
    stages = ["Startup", "Growth", "Maturity", "Shakeout", "Decline"]
    industries = ["Automotive", "Chemicals", "Metals", "Textiles"]

    for i in range(1, n_firms + 1):
        for y in years:
            records.append({
                "company_code": i,
                "year": y,
                "life_stage": stages[(i + y) % len(stages)],
                "industry_group": industries[i % len(industries)],
                "leverage": 0.25 + 0.05 * np.random.randn(),
                "profitability": 0.15 + 0.03 * np.random.randn(),
                "tangibility": 0.40 + 0.08 * np.random.randn(),
                "log_size": 4.5 + 0.2 * np.random.randn(),
            })
    return pd.DataFrame(records)


def test_parse_expanded_commands():
    p1 = parse_stata_command("tab life_stage")
    assert p1["cmd"] == "tab"
    assert "life_stage" in p1["indepvars"]

    p2 = parse_stata_command("graph box leverage, over(life_stage)")
    assert p2["cmd"] == "box"
    assert p2["options"].get("over") == "life_stage"

    p3 = parse_stata_command("xttest0")
    assert p3["cmd"] == "xttest0"

    p4 = parse_stata_command("xtserial")
    assert p4["cmd"] == "xtserial"

    p5 = parse_stata_command("margins life_stage")
    assert p5["cmd"] == "margins"
    assert "life_stage" in p5["indepvars"]


def test_tabulate_1way(panel_data):
    res = execute_stata_command("tab life_stage", df=panel_data)
    assert res["status"] == "success"
    assert "Freq." in res["ascii_output"]
    assert "Percent" in res["ascii_output"]
    assert "Maturity" in res["ascii_output"]
    assert "chart_spec" in res
    assert "interpretation" in res
    assert "Categorical Frequency Distribution" in res["interpretation"]


def test_tabulate_2way(panel_data):
    res = execute_stata_command("tab life_stage industry", df=panel_data)
    assert res["status"] == "success"
    assert "Pearson chi2" in res["ascii_output"]
    assert "chart_spec" in res
    assert "interpretation" in res
    assert "Two-Way Categorical Association" in res["interpretation"]


def test_graph_box(panel_data):
    res = execute_stata_command("graph box leverage, over(life_stage)", df=panel_data)
    assert res["status"] == "success"
    assert "P25" in res["ascii_output"]
    assert "Median" in res["ascii_output"]
    assert "IQR" in res["ascii_output"]
    assert "chart_spec" in res
    assert "interpretation" in res
    assert "Quartile & Dispersion Diagnostics" in res["interpretation"]


def test_xttest0(panel_data):
    res = execute_stata_command("xttest0", df=panel_data)
    assert res["status"] == "success"
    assert "Breusch and Pagan" in res["ascii_output"]
    assert "chibar2" in res["ascii_output"]
    assert "interpretation" in res
    assert "Lagrangian Multiplier Test" in res["interpretation"]


def test_xtserial(panel_data):
    res = execute_stata_command("xtserial", df=panel_data)
    assert res["status"] == "success"
    assert "Wooldridge test" in res["ascii_output"]
    assert "interpretation" in res
    assert "Wooldridge Test" in res["interpretation"]


def test_margins(panel_data):
    res = execute_stata_command("margins life_stage", df=panel_data)
    assert res["status"] == "success"
    assert "Delta-method" in res["ascii_output"]
    assert "Margin" in res["ascii_output"]
    assert "chart_spec" in res
    assert "interpretation" in res
    assert "Predictive Margins" in res["interpretation"]
