"""Scenario page must not show synthetic predictions for unavailable estimation."""
from pathlib import Path

import streamlit as st
from streamlit.testing.v1 import AppTest


def test_thesis_scenario_page_renders_with_actual_units(monkeypatch):
    import db
    monkeypatch.setattr(db, "log_page_visit", lambda *args, **kwargs: None)
    monkeypatch.setattr(db, "save_user_pref", lambda *args, **kwargs: None)
    app = AppTest.from_file(str(Path(__file__).resolve().parents[1] / "pages/3_scenarios.py"), default_timeout=30)
    app.session_state["user"] = dict(username="scenario_test", role="researcher")
    app.session_state["panel_mode"] = "thesis"
    app.session_state["filters"] = dict(panel_mode="thesis", company_codes=[], year_range=(2001,2024), life_stages=[], industry_groups=[],events={})
    app.run()
    assert not app.exception
    assert app.slider, dict(errors=[x.value for x in app.error], warnings=[x.value for x in app.warning])
    prof = next(x for x in app.slider if x.label == "Profitability (%)")
    tang = next(x for x in app.slider if x.label == "Tangibility (%)")
    assert 10 < prof.value < 20
    assert 20 < tang.value < 40


def test_empty_sample_withholds_prediction(monkeypatch):
    import db
    import models.scenario_regression as regression
    monkeypatch.setattr(db, "log_page_visit", lambda *args, **kwargs: None)
    monkeypatch.setattr(regression, "compute_leverage_ols_coefs", lambda *args: dict(n_obs=0))
    st.cache_data.clear()
    app = AppTest.from_file(str(Path(__file__).resolve().parents[1] / "pages/3_scenarios.py"), default_timeout=30)
    app.session_state["user"] = dict(role="researcher")
    app.run()
    assert not app.exception
    assert any("no predicted leverage" in x.value for x in app.warning)
    assert not app.slider
