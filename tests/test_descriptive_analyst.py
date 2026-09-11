import json
import sqlite3

import pandas as pd
import pytest

from models.descriptive_analyst import DescriptiveAnalysisError, describe_panel
from models.llm_adapters import _descriptive_result_text


def test_describe_panel_returns_grounded_sample_and_reproducibility_metadata():
    frame = pd.DataFrame({"firm": [1, 1, 2], "year": [2023, 2024, 2024], "leverage": [10.0, 20.0, 30.0]})

    run = describe_panel(
        frame,
        variables=["leverage"],
        group_by="year",
        run_id="run-1",
        panel_mode="thesis",
        year_range=(2023, 2024),
    )

    payload = json.loads(run.to_json())
    assert payload["status"] == "completed"
    assert payload["capability_id"] == "descriptive_summary"
    assert payload["parameters"]["variables"] == ["leverage"]
    assert payload["provenance"]["n_obs"] == 3
    assert payload["provenance"]["n_firms"] == 2
    assert payload["provenance"]["panel_mode"] == "thesis"
    assert payload["provenance"]["source_fingerprint"]
    assert payload["result"]["groups"]["2024"]["leverage"]["mean"] == 25.0


def test_describe_panel_rejects_unknown_or_non_numeric_variables():
    frame = pd.DataFrame({"name": ["a"], "leverage": [1.0]})

    with pytest.raises(DescriptiveAnalysisError, match="VARIABLE_NOT_FOUND"):
        describe_panel(frame, variables=["missing"], run_id="run-2")
    with pytest.raises(DescriptiveAnalysisError, match="NON_NUMERIC_VARIABLE"):
        describe_panel(frame, variables=["name"], run_id="run-3")


def test_describe_panel_rejects_invalid_grouping_and_empty_sample():
    frame = pd.DataFrame({"value": [1.0, 2.0]})

    with pytest.raises(DescriptiveAnalysisError, match="GROUP_NOT_FOUND"):
        describe_panel(frame, variables=["value"], group_by="stage", run_id="run-4")
    with pytest.raises(DescriptiveAnalysisError, match="EMPTY_SAMPLE"):
        describe_panel(frame.iloc[0:0], variables=["value"], run_id="run-5")


def test_gemini_result_renderer_exposes_scope_without_private_reasoning():
    text = _descriptive_result_text({
        "status": "success",
        "analysis_run": {
            "provenance": {
                "panel_mode": "thesis",
                "n_obs": 3,
                "n_firms": 2,
                "variables": ["leverage"],
                "source_fingerprint": "abc123",
            }
        },
    })
    assert "COMPUTED" in text
    assert "observations: `3`" in text
    assert "abc123" in text
    assert "reasoning" not in text.lower()


def test_database_tool_fails_closed_before_database_access_for_unknown_variable():
    from models.agent_tools import describe_financial_database

    result = describe_financial_database(["unsupported_metric"])
    assert result == {
        "status": "error",
        "error_code": "VARIABLE_NOT_FOUND",
        "error": "unsupported_metric",
    }


def test_database_tool_reads_filtered_rows_without_mutating_source(monkeypatch, tmp_path):
    from models import agent_tools

    database_path = tmp_path / "panel.sqlite"
    source = sqlite3.connect(database_path)
    source.execute("CREATE TABLE financials (company_code INTEGER, year INTEGER, leverage REAL, vintage TEXT)")
    source.executemany(
        "INSERT INTO financials VALUES (?, ?, ?, ?)",
        [(1, 2023, 10.0, "thesis"), (1, 2024, 20.0, "thesis")],
    )
    source.commit()
    before = source.execute("SELECT * FROM financials").fetchall()
    source.close()
    monkeypatch.setattr(agent_tools.db, "get_connection", lambda: sqlite3.connect(database_path))
    monkeypatch.setattr(agent_tools, "_assistant_view_where", lambda *_args: "1=1")

    result = agent_tools.describe_financial_database(
        ["leverage"], panel_mode="thesis", filters={"year_range": [2024, 2024]}
    )

    assert result["status"] == "success"
    assert result["analysis_run"]["provenance"]["n_obs"] == 1
    repeat = agent_tools.describe_financial_database(
        ["leverage"], panel_mode="thesis", filters={"year_range": [2024, 2024]}
    )
    assert result["analysis_run"]["run_id"] == repeat["analysis_run"]["run_id"]
    check = sqlite3.connect(database_path)
    assert check.execute("SELECT * FROM financials").fetchall() == before
    check.close()


def test_descriptive_tool_supports_life_stage_grouping(monkeypatch, tmp_path):
    from models import agent_tools

    database_path = tmp_path / "panel.sqlite"
    source = sqlite3.connect(database_path)
    source.execute("CREATE TABLE financials (company_code INTEGER, year INTEGER, life_stage TEXT, leverage REAL, panel_vintage TEXT)")
    source.executemany(
        "INSERT INTO financials VALUES (?, ?, ?, ?, ?)",
        [(1, 2023, "Growth", 10.0, "thesis"), (2, 2023, "Maturity", 20.0, "thesis")],
    )
    source.commit()
    source.close()
    monkeypatch.setattr(agent_tools.db, "get_connection", lambda: sqlite3.connect(database_path))
    monkeypatch.setattr(agent_tools, "_assistant_view_where", lambda *_args: "1=1")

    result = agent_tools.describe_financial_database(
        ["leverage"], group_by="life_stage", panel_mode="thesis"
    )
    assert result["status"] == "success"
    assert set(result["analysis_run"]["result"]["groups"]) == {"Growth", "Maturity"}
