"""Changing data/model settings must not reuse a stale trained result."""
from pathlib import Path

import pandas as pd
from streamlit.testing.v1 import AppTest


def test_result_is_invalidated_by_model_and_data_changes(monkeypatch):
    import db
    import models.timeseries as backend
    frame = pd.DataFrame(dict(company_code=[1,1], year=[2023,2024], leverage=[20.,21.],
        profitability=[.1,.2],tangibility=[.3,.4],log_size=[7.,8.],tax_shield=[1.,2.]))
    monkeypatch.setattr(db, "get_active_panel_data", lambda *args: frame.copy())
    monkeypatch.setattr(db, "log_page_visit", lambda *args: None)
    monkeypatch.setattr(backend, "HAS_TORCH", True)
    calls = []
    def train(*args, **kwargs):
        calls.append(kwargs["model_type"])
        return dict(error="Test training result")
    monkeypatch.setattr(backend, "run_full_forecast", train)
    app = AppTest.from_file(str(Path(__file__).resolve().parents[1] / "pages/10_forecasting.py"), default_timeout=30).run()
    assert not app.exception
    next(x for x in app.button if x.label == "Train Forecast Model").click().run()
    assert calls == ["LSTM"] and app.session_state["forecast_result"]
    app.run()
    assert calls == ["LSTM"] and app.session_state["forecast_result"]
    app.radio[0].set_value("GRU").run()
    assert app.session_state["forecast_result"] is None
    next(x for x in app.button if x.label == "Train Forecast Model").click().run()
    assert calls == ["LSTM", "GRU"]
    frame.loc[0,"leverage"] = 30.
    app.run()
    assert not app.exception and app.session_state["forecast_result"] is None
