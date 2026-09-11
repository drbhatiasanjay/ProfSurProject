from __future__ import annotations

import pandas as pd
import pytest

from models.model_context import AnalysisSession, ModelResultContext
from models.stata_engine import execute_stata_command
from models.econometric import _calendar_lag


def test_model_context_isolated_between_sessions() -> None:
    frame = pd.DataFrame({"y": [1.0, 2.0], "x": [2.0, 4.0]})
    model = ModelResultContext.from_frame(
        model_id="m1",
        command="regress y x",
        estimator="statsmodels.OLS",
        frame=frame,
        dependent_variable="y",
        regressors=("x",),
        parameters={"x": 0.5},
        covariance=[[0.1]],
    )

    first = AnalysisSession()
    second = AnalysisSession()
    first.store(model)

    assert first.require("m1").model_id == "m1"
    with pytest.raises(KeyError):
        second.require("m1")


def test_model_context_public_projection_excludes_runtime_objects() -> None:
    frame = pd.DataFrame({"y": [1.0, 2.0], "x": [2.0, 4.0]})
    model = ModelResultContext.from_frame(
        model_id="m1",
        command="regress y x",
        estimator="statsmodels.OLS",
        frame=frame,
        dependent_variable="y",
        regressors=("x",),
        parameters={"x": 0.5},
        covariance=[[0.1]],
    )

    public = model.public_dict()

    assert public["model_id"] == "m1"
    assert public["n_obs"] == 2
    assert "backend_result" not in public
    assert "design_matrix" not in public


def test_stata_estimation_state_isolated_between_sessions() -> None:
    frame = pd.DataFrame({
        "leverage": [1.0, 2.0, 3.0, 4.0],
        "profitability": [1.0, 1.5, 2.5, 3.0],
    })
    first = AnalysisSession()
    second = AnalysisSession()

    result = execute_stata_command("regress leverage profitability", frame, session=first)
    assert result["status"] == "success"
    assert execute_stata_command("estimates store first", frame, session=first)["status"] == "success"

    isolated = execute_stata_command("estimates store second", frame, session=second)
    assert isolated["status"] == "error"
    assert "last estimates not found" in isolated["ascii_output"]


def test_xtreg_fails_closed_when_panel_is_not_set() -> None:
    frame = pd.DataFrame({"leverage": [1.0, 2.0], "profitability": [2.0, 4.0]})
    result = execute_stata_command("xtreg leverage profitability, fe", frame, session=AnalysisSession())
    assert result["status"] == "error"
    assert result["error_code"] == "PANEL_NOT_SET"


def test_post_estimation_does_not_synthesize_a_hidden_model() -> None:
    frame = pd.DataFrame({"leverage": [1.0, 2.0], "profitability": [2.0, 4.0]})
    session = AnalysisSession()
    result = execute_stata_command("coefplot", frame, session=session)
    assert result["status"] == "error"
    assert result["error_code"] == "MODEL_STORE_EMPTY"


def test_panel_declaration_isolated_between_sessions() -> None:
    frame = pd.DataFrame({
        "company_code": [1, 1, 2, 2],
        "year": [2020, 2021, 2020, 2021],
        "leverage": [1.0, 2.0, 1.5, 2.5],
        "profitability": [2.0, 4.0, 3.0, 5.0],
    })
    first = AnalysisSession()
    second = AnalysisSession()
    assert execute_stata_command("xtset company_code year", frame, session=first)["status"] == "success"
    query = execute_stata_command("xtset", frame, session=second)
    assert query["status"] == "error"
    assert "panel" in query["message"].lower()


def test_calendar_lag_does_not_use_row_position_when_years_are_missing() -> None:
    frame = pd.DataFrame({
        "company_code": [1, 1, 1],
        "year": [2020, 2022, 2023],
        "leverage": [10.0, 20.0, 30.0],
    })
    lag1 = _calendar_lag(frame, "leverage", "company_code", "year", 1)
    assert pd.isna(lag1.iloc[1])
    assert lag1.iloc[2] == 20.0
