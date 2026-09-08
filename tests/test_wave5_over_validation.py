"""Focused behavioral contracts for graph box over() validation."""

import numpy as np
import pandas as pd

from models.stata_engine import execute_stata_command


def _panel() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "leverage": np.arange(4, dtype=float),
            "life_stage": ["Startup", "Growth", "Maturity", "Decline"],
            "industry_group": ["A", "A", "B", "B"],
        }
    )


def test_graph_box_over_unknown_variable_fails_before_handler(monkeypatch):
    def unexpected_handler(*args, **kwargs):
        raise AssertionError("graph box handler must not run after over() validation failure")

    import models.stata_engine as stata_engine

    monkeypatch.setattr(stata_engine, "_handle_graph_box", unexpected_handler)
    result = execute_stata_command("graph box leverage, over(nonexistent_col)", _panel())

    assert result["status"] == "error"
    assert result["error_code"] == "VARIABLE_NOT_FOUND"
    assert result["metadata"] == {
        "stata_rc": 111,
        "invalid_argument": "nonexistent_col",
        "argument_role": "over",
    }


def test_graph_box_over_alias_is_not_substituted():
    result = execute_stata_command("graph box leverage, over(stage)", _panel())

    assert result["status"] == "error"
    assert result["error_code"] == "VARIABLE_NOT_FOUND"
    assert result["metadata"]["argument_role"] == "over"
    assert result["metadata"]["invalid_argument"] == "stage"


def test_graph_box_empty_over_is_typed_syntax_error():
    result = execute_stata_command("graph box leverage, over()", _panel())

    assert result["status"] == "error"
    assert result["error_code"] == "SYNTAX_ERROR"
    assert result["metadata"]["stata_rc"] == 198
    assert result["metadata"]["argument_role"] == "over"


def test_graph_box_over_preserves_requested_grouping_column():
    result = execute_stata_command("graph box leverage, over(industry_group)", _panel())

    assert result["status"] == "success"
    assert result["boxplot_data"]["group"] == "industry_group"
