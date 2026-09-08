"""Focused regression tests for explicit, isolated post-estimation state."""

import pandas as pd

from models.stata_engine import ModelResultContext, execute_stata_command


def _frame() -> pd.DataFrame:
    return pd.DataFrame({
        "y": [1.0, 2.0, 1.5, 3.0, 2.5, 4.0, 3.5, 5.0],
        "x": [0.2, 0.4, 0.3, 0.8, 0.7, 1.1, 1.0, 1.4],
    })


def test_post_estimation_state_is_explicit_and_isolated():
    frame = _frame()
    first = ModelResultContext()
    second = ModelResultContext()

    assert execute_stata_command("regress y x", frame, first)["status"] == "success"
    assert execute_stata_command("test x = 0", frame, first)["status"] == "success"

    isolated = execute_stata_command("test x = 0", frame, second)
    assert isolated["status"] == "error"
    assert isolated["error_code"] == "NO_ACTIVE_ESTIMATION"
    assert isolated["metadata"]["stata_rc"] == 301


def test_implicit_calls_do_not_share_post_estimation_state():
    frame = _frame()
    assert execute_stata_command("regress y x", frame)["status"] == "success"

    result = execute_stata_command("predict fitted, xb", frame)
    assert result["status"] == "error"
    assert result["error_code"] == "NO_ACTIVE_ESTIMATION"
