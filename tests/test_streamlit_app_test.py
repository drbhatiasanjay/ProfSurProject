"""Deterministic Streamlit smoke coverage for the authenticated app shell."""
from pathlib import Path

from streamlit.testing.v1 import AppTest


def test_authenticated_app_shell_runs_without_exception():
    app = AppTest.from_file(Path(__file__).parents[1] / "app.py")
    app.session_state["user"] = {
        "username": "apptest",
        "name": "App Test",
        "role": "admin",
    }
    app.run(timeout=30)
    assert not app.exception
