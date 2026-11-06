"""In-process workflow tests; authenticated browser acceptance is separate."""
import streamlit.testing.v1 as st_test


SCRIPT = '''
import streamlit as st
import pandas as pd
from components.debt_board_view import render_debt_board
st.session_state.setdefault("user", dict(username="component_test", role="researcher"))
st.session_state.setdefault("theme", "light")
company = pd.DataFrame([dict(year=2024,life_stage="Maturity",borrowings=1000,
    cash_holdings=100,pbit=200,interest_amt=40,ncfo=180,ncfi=-100,ncff=-60,
    leverage=25,profitability=.05,tangibility=.4,tax=.25,tax_shield=100)])
info = dict(code=1,name="Example",current_stage="Maturity")
render_debt_board(company, info, pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), {})
'''

PREFIX = "debt_board_component_test_1"


def button(app, label):
    return next(x for x in app.button if x.label == label)


def enable(app):
    app.checkbox(key=f"{PREFIX}_enabled").check().run()
    assert not app.exception


def fill_funding(app, debt=150.0):
    app.text_input(key=f"{PREFIX}_purpose").set_value("Fund expansion")
    for key, value in dict(funding_uses=200.0, internal_funding=50.0, new_debt=debt,
        new_rate=8.0, floating_share=50.0, rate_shock=200.0, earnings_shock=20.0, coverage_floor=3.0).items():
        app.number_input(key=f"{PREFIX}_{key}").set_value(value)


def test_initial_review_needs_no_form_or_assumptions_and_exports(monkeypatch):
    import db
    import components.debt_board_view as view
    monkeypatch.setattr(db, "save_user_pref", lambda *args: None)
    monkeypatch.setattr(view, "build_sections", lambda *args, **kwargs: b"historical-export")
    app = st_test.AppTest.from_string(SCRIPT, default_timeout=30).run()
    assert not app.exception
    assert not app.number_input
    assert [x.label for x in app.expander][:2] == ["Core facts", "Life-stage diagnosis"]
    assert app.session_state[f"{PREFIX}_pack"]["assumptions"] is None
    button(app, "Generate debt strategy PowerPoint").click().run()
    assert app.session_state[f"{PREFIX}_export"]["data"] == b"historical-export"
    app.run()
    assert app.session_state[f"{PREFIX}_export"]["data"] == b"historical-export"


def test_blank_optional_form_does_not_create_zero_plan(monkeypatch):
    import db
    saved = []
    monkeypatch.setattr(db, "save_user_pref", lambda *args: saved.append(args))
    app = st_test.AppTest.from_string(SCRIPT, default_timeout=30).run()
    enable(app)
    assert all(x.value is None for x in app.number_input)
    button(app, "Apply scenario and calculate").click().run()
    assert not app.exception
    assert app.error and "Blank fields are not treated as zero" in app.error[0].value
    assert app.session_state[f"{PREFIX}_pack"]["assumptions"] is None
    assert not saved


def test_applied_funding_saved_and_draft_changes_do_not_replace_export(monkeypatch):
    import db
    import components.debt_board_view as view
    saved = []
    monkeypatch.setattr(db, "save_user_pref", lambda *args: saved.append(args))
    monkeypatch.setattr(view, "build_sections", lambda *args, **kwargs: b"scenario-export")
    app = st_test.AppTest.from_string(SCRIPT, default_timeout=30).run()
    enable(app)
    fill_funding(app)
    button(app, "Apply scenario and calculate").click().run()
    assert not app.exception
    assert saved[-1][2]["companies"]["1"]["assumptions"]["new_debt"] == 150
    button(app, "Generate debt strategy PowerPoint").click().run()
    app.number_input(key=f"{PREFIX}_new_debt").set_value(200.0)
    app.run()
    assert app.session_state[f"{PREFIX}_pack"]["assumptions"]["new_debt"] == 150
    assert app.session_state[f"{PREFIX}_export"]["data"] == b"scenario-export"
    app.number_input(key=f"{PREFIX}_new_debt").set_value(200.0)
    button(app, "Apply scenario and calculate").click().run()
    assert app.session_state[f"{PREFIX}_pack"]["assumptions"]["new_debt"] == 200
    assert f"{PREFIX}_export" not in app.session_state
    app.checkbox(key=f"{PREFIX}_enabled").uncheck().run()
    assert not app.exception
    assert app.session_state[f"{PREFIX}_pack"]["assumptions"] is None
    assert saved[-1][2]["companies"]["1"]["enabled"] is False


def test_stress_only_requires_four_fields_and_preserves_appendix(monkeypatch):
    import db
    monkeypatch.setattr(db, "save_user_pref", lambda *args: None)
    app = st_test.AppTest.from_string(SCRIPT, default_timeout=30).run()
    enable(app)
    app.radio(key=f"{PREFIX}_scenario_type").set_value("Stress existing debt only").run()
    assert len(app.number_input) == 4
    assert not app.text_input
    for key, value in dict(floating_share=50.0, rate_shock=200.0, earnings_shock=20.0, coverage_floor=3.0).items():
        app.number_input(key=f"{PREFIX}_{key}").set_value(value)
    button(app, "Apply scenario and calculate").click().run()
    assert not app.exception
    pack = app.session_state[f"{PREFIX}_pack"]
    assert pack["scenario_type"] == "stress"
    assert len(pack["sections"][7]["tables"][0]) == 2
    app.multiselect(key=f"{PREFIX}_appendix").set_value([1, 12]).run()
    assert not app.exception
    assert len(app.session_state[f"{PREFIX}_pack"]["sections"]) == 12
    app.session_state["theme"] = "dark"
    app.run()
    assert not app.exception


def test_legacy_saved_numbers_do_not_silently_become_applied_plan(monkeypatch):
    import db
    monkeypatch.setattr(db, "save_user_pref", lambda *args: None)
    script = SCRIPT.replace('pd.DataFrame(), {})', 'pd.DataFrame(), {"companies": {"1": {"new_debt": 999.0}}})')
    app = st_test.AppTest.from_string(script, default_timeout=30).run()
    assert not app.exception
