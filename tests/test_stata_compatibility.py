"""Test suite for Stata compatibility: xtset, lgraph, docx isolation, and unsupported command handling."""

import pytest
import pandas as pd
import numpy as np
from models.stata_engine import execute_stata_command, parse_stata_command, generate_esttab_docx, DOCX_AVAILABLE


@pytest.fixture
def panel_data():
    """Create a balanced panel dataset (10 firms x 5 years)."""
    firms = [f"FIRM_{i:03d}" for i in range(1, 11)]
    years = list(range(2001, 2006))
    rows = []
    np.random.seed(42)
    for f in firms:
        for y in years:
            rows.append({
                "company_code": f,
                "year": y,
                "leverage": float(np.random.uniform(0.1, 0.4)),
                "profitability": float(np.random.uniform(0.05, 0.25)),
                "tangibility": float(np.random.uniform(0.2, 0.6)),
                "log_size": float(np.random.uniform(5.0, 10.0)),
                "life_stage": "Growth" if y < 2003 else "Maturity",
                "tax_shield": float(np.random.uniform(0.01, 0.05)),
                "int_rate": float(np.random.uniform(0.05, 0.12)),
                "dividend": float(np.random.uniform(0.0, 0.05)),
            })
    return pd.DataFrame(rows)


def test_xtset_valid_alias(panel_data):
    """Test xtset with companycode alias (xtset companycode year)."""
    res = execute_stata_command("xtset companycode year", df=panel_data)
    assert res["status"] == "success"
    assert res["panel_var"] == "company_code"
    assert res["time_var"] == "year"
    assert "panel variable:  company_code (strongly balanced)" in res["ascii_output"]
    assert "time variable:  year, 2001 to 2005" in res["ascii_output"]
    assert "delta:  1 unit" in res["ascii_output"]


def test_xtset_canonical(panel_data):
    """Test xtset with canonical company_code (xtset company_code year)."""
    res = execute_stata_command("xtset company_code year", df=panel_data)
    assert res["status"] == "success"
    assert res["panel_var"] == "company_code"
    assert res["time_var"] == "year"
    assert "strongly balanced" in res["ascii_output"]


def test_xtset_invalid_variable(panel_data):
    """Test xtset with non-existent variable fails gracefully with r(111)."""
    res = execute_stata_command("xtset non_existent_firm year", df=panel_data)
    assert res["status"] == "error"
    assert "r(111)" in res["ascii_output"]


def test_xtset_duplicate_panel_time(panel_data):
    """Test xtset detects repeated time values within panel with r(451)."""
    dup_df = pd.concat([panel_data, panel_data.iloc[[0]]], ignore_index=True)
    res = execute_stata_command("xtset company_code year", df=dup_df)
    assert res["status"] == "error"
    assert "r(451)" in res["ascii_output"]
    assert "repeated time values" in res["ascii_output"]


def test_lgraph_multi_series_wide(panel_data):
    """Test lgraph leverage prof year, wide."""
    res = execute_stata_command("lgraph leverage prof year, wide", df=panel_data)
    assert res["status"] == "success"
    assert "leverage" in res["y_vars"]
    assert "profitability" in res["y_vars"]
    assert res["x_var"] == "year"
    assert "Longitudinal Panel Means over year" in res["ascii_output"]
    assert res.get("fig") is not None


def test_lgraph_invalid_variable(panel_data):
    """Test lgraph with invalid variable fails gracefully with r(111)."""
    res = execute_stata_command("lgraph invalid_metric year", df=panel_data)
    assert res["status"] == "error"
    assert "r(111)" in res["ascii_output"]


def test_unsupported_command_graceful_handling(panel_data):
    """Test unsupported command returns 'unsupported' status, admin contact, and r(199)."""
    res = execute_stata_command("foobar_unsupported_command x y z", df=panel_data)
    assert res["status"] == "unsupported"
    assert "foobar_unsupported_command" in res["command"]
    assert "admin@lifecycle-leverage.internal" in res["admin_contact"]
    assert "r(199)" in res["ascii_output"]
    assert len(res["supported_commands"]) >= 15


def test_docx_export_graceful(tmp_path):
    """Test generate_esttab_docx handles missing or present docx without crashing."""
    out_file = str(tmp_path / "test_table.docx")
    res = generate_esttab_docx(out_file)
    if DOCX_AVAILABLE:
        assert res == out_file
    else:
        assert res is None


def test_screenshot_eight_command_sequence(panel_data):
    """Execute the exact 8-command sequence from the diagnostic screenshot in order.

    [1] xtreg leverage i.corplifestage c.prof##c.tang c.prof##c.dvnd taxShield intRate i.year, fe
    [2] xtreg leverage i.corplifestage c.prof##c.tang c.prof##c.dvnd taxShield intRate i.year, fe
    [3] tabulate corplifestage
    [4] tabulate corplifestage
    [5] lgraph leverage prof year, wide
    [6] lgraph leverage prof year, wide
    [7] xtset companycode year
    [8] xtset companycode year
    """
    cmd1 = "xtreg leverage i.corplifestage c.prof##c.tang c.prof##c.dvnd tax_shield int_rate, fe"
    cmd2 = "xtreg leverage i.corplifestage c.prof##c.tang c.prof##c.dvnd tax_shield int_rate, fe"
    cmd3 = "tabulate corplifestage"
    cmd4 = "tabulate corplifestage"
    cmd5 = "lgraph leverage prof year, wide"
    cmd6 = "lgraph leverage prof year, wide"
    cmd7 = "xtset companycode year"
    cmd8 = "xtset companycode year"

    commands = [cmd1, cmd2, cmd3, cmd4, cmd5, cmd6, cmd7, cmd8]
    results = []

    for idx, c in enumerate(commands, 1):
        r = execute_stata_command(c, df=panel_data)
        assert r["status"] == "success", f"Command [{idx}] '{c}' failed: {r.get('ascii_output')}"
        results.append(r)

    assert len(results) == 8
