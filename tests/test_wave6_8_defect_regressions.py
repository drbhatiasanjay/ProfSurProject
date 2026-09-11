from __future__ import annotations

import pandas as pd
import numpy as np
import pytest
import db

from models.model_context import AnalysisSession
from models.stata_engine import execute_stata_command
from models.econometric import _calendar_lag
from models.econometric import run_hausman_test


def _panel() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "company_code": [1, 1, 1, 2, 2, 2],
            "year": [2020, 2021, 2022, 2020, 2021, 2022],
            "leverage": [10.0, 11.0, 13.0, 20.0, 21.0, 24.0],
            "profitability": [1.0, 2.0, 3.0, 2.0, 4.0, 6.0],
            "tangibility": [2.0, 3.0, 4.0, 3.0, 5.0, 7.0],
            "log_size": [4.0, 4.1, 4.2, 5.0, 5.1, 5.2],
        }
    )


def test_vif_is_bound_to_active_model_regressors() -> None:
    frame = _panel()
    session = AnalysisSession()
    fitted = execute_stata_command(
        "regress leverage profitability tangibility", frame, session=session
    )
    assert fitted["status"] == "success"

    vif = execute_stata_command("estat vif", frame, session=session)

    assert vif["status"] == "success"
    assert set(vif["vif_data"]) == {"profitability", "tangibility"}


def test_coefplot_rejects_ambiguous_implicit_model() -> None:
    frame = _panel()
    session = AnalysisSession()
    assert execute_stata_command("regress leverage profitability", frame, session=session)["status"] == "success"
    assert execute_stata_command("xtset company_code year", frame, session=session)["status"] == "success"
    assert execute_stata_command("xtreg leverage profitability, fe", frame, session=session)["status"] == "success"

    result = execute_stata_command("coefplot", frame, session=session)

    assert result["status"] == "error"
    assert result["error_code"] == "MODEL_ID_REQUIRED"


def test_xtreg_never_relabels_estimator_failure_as_success(monkeypatch) -> None:
    frame = _panel()
    session = AnalysisSession()
    assert execute_stata_command("xtset company_code year", frame, session=session)["status"] == "success"

    import linearmodels.panel

    class BrokenPanelOLS:
        def __init__(self, *args, **kwargs):
            raise RuntimeError("forced estimator failure")

    monkeypatch.setattr(linearmodels.panel, "PanelOLS", BrokenPanelOLS)
    result = execute_stata_command(
        "xtreg leverage profitability, fe", frame, session=session
    )

    assert result["status"] == "error"
    assert result["error_code"] == "ESTIMATION_FAILURE"


def test_calendar_lag_rejects_duplicate_entity_time_keys() -> None:
    frame = pd.DataFrame(
        {
            "company_code": [1, 1],
            "year": [2020, 2020],
            "leverage": [10.0, 11.0],
        }
    )

    try:
        _calendar_lag(frame, "leverage", "company_code", "year", 1)
    except ValueError as exc:
        assert "Duplicate entity/time" in str(exc)
    else:
        raise AssertionError("duplicate panel keys must fail closed")


def test_hausman_uses_full_covariance_difference() -> None:
    class Result:
        def __init__(self, params, cov):
            self.params = pd.Series(params)
            self.cov = pd.DataFrame(cov, index=["x1", "x2"], columns=["x1", "x2"])

    fe = {"result_obj": Result({"x1": 1.0, "x2": 1.0}, [[4.0, 1.0], [1.0, 4.0]])}
    re = {"result_obj": Result({"x1": 0.0, "x2": 0.0}, [[1.0, 0.0], [0.0, 1.0]])}
    result = run_hausman_test(fe, re)
    expected = np.array([1.0, 1.0]) @ np.linalg.inv(np.array([[3.0, 1.0], [1.0, 3.0]])) @ np.array([1.0, 1.0])
    assert result["chi2"] == pytest.approx(expected)


def test_margins_preserves_native_leverage_units() -> None:
    frame = _panel().assign(life_stage="Maturity")
    result = execute_stata_command("margins life_stage", frame, session=AnalysisSession())
    assert result["status"] == "success"
    assert result["margins_data"]["margins"][0] == pytest.approx(frame["leverage"].mean())


def test_chat_result_envelope_round_trips_without_runtime_objects(temp_chat_db) -> None:
    db.create_chat_session("envelope", "tester", "researcher")
    envelope = {
        "model_id": "OLS:abc",
        "estimator": "OLS",
        "sample_fingerprint": "sample-1",
        "n_obs": 42,
    }
    db.append_chat_message(
        "envelope", "assistant", "result", result_envelope=envelope
    )
    loaded = db.load_chat_messages("envelope")
    assert loaded[0]["result_envelope"] == envelope
