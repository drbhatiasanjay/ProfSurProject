"""Focused router contracts for session identity and post-estimation errors."""

import uuid

import pandas as pd

from models.analytical_contracts import AnalyticalRequest, fingerprint_df
from models.analytical_router import route
from models.stata_engine import ModelResultContext, parse_stata_command


def _frame() -> pd.DataFrame:
    return pd.DataFrame({
        "y": [1.0, 2.0, 1.5, 3.0, 2.5, 4.0, 3.5, 5.0],
        "x": [0.2, 0.4, 0.3, 0.8, 0.7, 1.1, 1.0, 1.4],
    })


def _request(command: str, frame: pd.DataFrame, context: ModelResultContext, session_id: str):
    return AnalyticalRequest(
        command_str=command,
        parsed=parse_stata_command(command),
        df=frame,
        correlation_id=str(uuid.uuid4()),
        dataset_ref=fingerprint_df(frame),
        session_id=session_id,
        session_context=context,
    )


def test_router_rejects_context_reuse_by_another_session():
    frame = _frame()
    context = ModelResultContext()

    fitted = route(_request("regress y x", frame, context, "session-a"))
    assert fitted.status == "success"

    result = route(_request("test x = 0", frame, context, "session-b"))
    assert result.status == "error"
    assert result.error_code == "DATA_SCOPE_ERROR"
    assert "another session" in result.message


def test_router_distinguishes_no_model_from_bad_test_variable():
    frame = _frame()
    empty = ModelResultContext()
    no_model = route(_request("test x = 0", frame, empty, "session-a"))
    assert no_model.error_code == "NO_ACTIVE_ESTIMATION"

    fitted_context = ModelResultContext()
    assert route(_request("regress y x", frame, fitted_context, "session-a")).status == "success"
    bad_variable = route(_request("test missing = 0", frame, fitted_context, "session-a"))
    assert bad_variable.error_code == "VARIABLE_NOT_FOUND"
    assert bad_variable.metadata["stata_rc"] == 111
