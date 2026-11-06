"""Native Streamlit reruns, case revisions, role boundaries and working drafts."""
from pathlib import Path
import sqlite3

import pytest
from streamlit.testing.v1 import AppTest


PAGE = Path(__file__).resolve().parents[1] / "pages/26_company_financing.py"


@pytest.fixture
def case_store(monkeypatch, tmp_path):
    from models import financing_store
    # Keep source company queries real and redirect only financing persistence.
    class Database:
        @staticmethod
        def get_connection():
            return sqlite3.connect(tmp_path / "cases.db")
    monkeypatch.setattr(financing_store, "db", Database)
    return financing_store


@pytest.mark.parametrize("profile,role", [("profsurkumar", "researcher"), ("skumar", "researcher"),
    ("drbhatia", "admin"), ("sbhatia", "viewer")])
def test_native_page_profiles_and_blank_evidence(profile, role, case_store):
    app = AppTest.from_file(str(PAGE), default_timeout=30)
    app.session_state["user"] = dict(username=profile, role=role)
    app.session_state["theme"] = "light"
    app.run()
    assert not app.exception
    if role == "viewer":
        assert not app.text_input
        assert "permission" in app.warning[0].value
        return
    assert any(x.label == "Case title *" for x in app.text_input)
    assert app.number_input[0].value is None
    assert any("unrestricted cash" in x.value for x in app.warning)
    next(x for x in app.text_input if x.label == "Case title *").set_value("Evidence draft")
    next(x for x in app.button if x.label == "Validate and save case").click().run()
    assert not app.exception
    assert any("revision 1" in x.value for x in app.success)
    next(x for x in app.button if x.label == "Validate and save case").click().run()
    assert not app.exception
    assert any("revision 2" in x.value for x in app.success)
    app.session_state["theme"] = "dark"
    app.run()
    assert not app.exception
    # Two revisions belong to one case, not two replacement cases.
    working_keys = [k for k in app.session_state.filtered_state if k.endswith("_working")]
    assert len(working_keys) == 1
    working = app.session_state[working_keys[0]]
    assert case_store.load_case(profile, working["case_id"], 1)
    assert case_store.load_case(profile, working["case_id"])["revision"] == 2
    next(x for x in app.selectbox if x.label == "Saved financing case").set_value("new").run()
    assert not app.exception
    assert next(x for x in app.text_input if x.label == "Case title *").value == ""
    assert app.number_input[0].value is None
