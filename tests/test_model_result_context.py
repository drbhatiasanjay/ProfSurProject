"""Behavioral tests for session-scoped Stata model state."""

import pandas as pd

from models.stata_engine import ModelResultContext, execute_stata_command


def _panel_frame():
    return pd.DataFrame(
        {
            "leverage": [0.10 + i * 0.01 for i in range(20)],
            "profitability": [0.20 + i * 0.005 for i in range(20)],
            "tangibility": [0.30 + i * 0.004 for i in range(20)],
            "log_size": [5.0 + i * 0.02 for i in range(20)],
        }
    )


def test_post_estimation_uses_only_the_active_model_context():
    frame = _panel_frame()
    first = ModelResultContext()
    second = ModelResultContext()

    fitted = execute_stata_command(
        "regress leverage profitability tangibility log_size",
        df=frame,
        stata_session_state=first,
    )
    assert fitted["status"] == "success"
    assert first.last_estimate is not None

    same_context = execute_stata_command(
        "test profitability = 0",
        df=frame,
        stata_session_state=first,
    )
    isolated_context = execute_stata_command(
        "test profitability = 0",
        df=frame,
        stata_session_state=second,
    )

    assert same_context["status"] == "success"
    assert isolated_context["status"] == "error"
    assert "r(301)" in isolated_context["ascii_output"]
