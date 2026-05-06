"""
Fast unit tests for the user-state db.py functions added in migration 002.
No browser or running Streamlit server required.

Tests: save/load prefs, audit_log insert + filter, log_page_visit (with mocked
streamlit session_state), model run history, busy_timeout pragma.

Run:  py -3.12 -m pytest tests/test_user_state.py -v
"""
import inspect
import json
import sqlite3
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

MIGRATION_002 = PROJECT_ROOT / "migrations" / "002_user_state.sql"

import db  # noqa: E402  — must be after sys.path insert


# ── fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture()
def test_db(tmp_path, monkeypatch):
    """Temp SQLite DB with migration 002 applied; db.DB_PATH redirected to it."""
    p = tmp_path / "state.db"
    conn = sqlite3.connect(str(p))
    conn.executescript(MIGRATION_002.read_text(encoding="utf-8"))
    conn.close()
    monkeypatch.setattr(db, "DB_PATH", str(p))
    return str(p)


# ── helpers ───────────────────────────────────────────────────────────────────

class _SS:
    """Minimal dict-backed session_state stand-in for log_page_visit tests."""
    def __init__(self, data: dict):
        self._d = data

    def get(self, key, default=None):
        return self._d.get(key, default)


def _fake_st(session_data: dict) -> MagicMock:
    m = MagicMock()
    m.session_state = _SS(session_data)
    return m


def _count(db_path: str, table: str) -> int:
    c = sqlite3.connect(db_path)
    n = c.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
    c.close()
    return n


def _seed_visits(db_path: str, rows: list[dict]) -> None:
    c = sqlite3.connect(db_path)
    for r in rows:
        c.execute(
            "INSERT INTO audit_log(username, role, page_name, action_type) VALUES (?,?,?,?)",
            [r["username"], r["role"], r["page_name"], r.get("action_type", "page_visit")],
        )
    c.commit()
    c.close()


# ── user preferences ──────────────────────────────────────────────────────────

def test_save_load_pref_roundtrip(test_db):
    prefs = {"selected_x": ["profitability", "tangibility"], "model_choice": "Fixed Effects"}
    db.save_user_pref("sbhatia", "econometrics", prefs)
    assert db.load_user_prefs("sbhatia", "econometrics") == prefs


def test_load_missing_pref_returns_empty(test_db):
    assert db.load_user_prefs("nobody", "nowhere") == {}


def test_save_pref_upserts(test_db):
    db.save_user_pref("sbhatia", "scenarios", {"prof_val": 10.0})
    db.save_user_pref("sbhatia", "scenarios", {"prof_val": 25.0})
    assert db.load_user_prefs("sbhatia", "scenarios")["prof_val"] == 25.0
    c = sqlite3.connect(test_db)
    n = c.execute(
        "SELECT COUNT(*) FROM user_preferences WHERE username='sbhatia' AND page='scenarios'"
    ).fetchone()[0]
    c.close()
    assert n == 1  # INSERT OR REPLACE, not two rows


def test_different_users_different_prefs(test_db):
    db.save_user_pref("sbhatia", "data_explorer", {"selected_cols": ["leverage", "year"]})
    db.save_user_pref("skumar",  "data_explorer", {"selected_cols": ["company_name"]})
    assert db.load_user_prefs("sbhatia", "data_explorer")["selected_cols"] == ["leverage", "year"]
    assert db.load_user_prefs("skumar",  "data_explorer")["selected_cols"] == ["company_name"]


# ── audit log ─────────────────────────────────────────────────────────────────

def test_get_audit_log_returns_all(test_db):
    _seed_visits(test_db, [
        {"username": "sbhatia", "role": "admin",      "page_name": "Dashboard"},
        {"username": "skumar",  "role": "researcher", "page_name": "Econometrics Lab"},
        {"username": "guest",   "role": "viewer",     "page_name": "Data Explorer"},
    ])
    assert len(db.get_audit_log(limit=50)) == 3


def test_get_audit_log_username_filter(test_db):
    _seed_visits(test_db, [
        {"username": "sbhatia", "role": "admin",      "page_name": "Dashboard"},
        {"username": "skumar",  "role": "researcher", "page_name": "ML Models"},
        {"username": "sbhatia", "role": "admin",      "page_name": "Scenarios"},
    ])
    df = db.get_audit_log(limit=50, username="skumar")
    assert len(df) == 1
    assert df.iloc[0]["username"] == "skumar"


def test_get_audit_log_respects_limit(test_db):
    _seed_visits(test_db, [
        {"username": "sbhatia", "role": "admin", "page_name": f"Page{i}"} for i in range(10)
    ])
    assert len(db.get_audit_log(limit=3)) == 3


# ── log_page_visit (mocked streamlit) ────────────────────────────────────────

def test_log_page_visit_inserts_row(test_db):
    session = {"user": {"username": "sbhatia", "role": "admin"}, "session_id": "s1"}
    with patch.dict(sys.modules, {"streamlit": _fake_st(session)}):
        db.log_page_visit("Dashboard")
    c = sqlite3.connect(test_db)
    row = c.execute("SELECT username, role, page_name FROM audit_log").fetchone()
    c.close()
    assert row == ("sbhatia", "admin", "Dashboard")


def test_log_page_visit_viewer_captures_display_name(test_db):
    session = {
        "user": {"username": "guest", "role": "viewer"},
        "session_id": "g1",
        "guest_display_name": "Prof. Dawar",
    }
    with patch.dict(sys.modules, {"streamlit": _fake_st(session)}):
        db.log_page_visit("Data Explorer")
    c = sqlite3.connect(test_db)
    row = c.execute("SELECT details FROM audit_log WHERE username='guest'").fetchone()
    c.close()
    assert row is not None
    assert json.loads(row[0])["display_name"] == "Prof. Dawar"


def test_log_page_visit_viewer_without_name_omits_details(test_db):
    session = {
        "user": {"username": "guest", "role": "viewer"},
        "session_id": "g2",
        # no guest_display_name
    }
    with patch.dict(sys.modules, {"streamlit": _fake_st(session)}):
        db.log_page_visit("Dashboard")
    c = sqlite3.connect(test_db)
    row = c.execute("SELECT details FROM audit_log WHERE username='guest'").fetchone()
    c.close()
    assert row is not None
    assert row[0] is None  # no details JSON when display name not yet set


def test_log_page_visit_no_user_is_noop(test_db):
    session = {"session_id": "nope"}  # no "user" key
    with patch.dict(sys.modules, {"streamlit": _fake_st(session)}):
        db.log_page_visit("Dashboard")
    assert _count(test_db, "audit_log") == 0


# ── model runs ────────────────────────────────────────────────────────────────

def test_save_get_model_runs_roundtrip(test_db):
    db.save_model_run(
        "sbhatia", "econometrics",
        params={"model": "Fixed Effects", "n_vars": 5},
        summary={"r2": 0.42, "n_obs": 3000},
    )
    df = db.get_model_runs("sbhatia", "econometrics")
    assert len(df) == 1
    assert json.loads(df.iloc[0]["params"])["model"] == "Fixed Effects"
    assert json.loads(df.iloc[0]["summary"])["r2"] == 0.42


def test_get_model_runs_empty_for_unknown_user(test_db):
    assert len(db.get_model_runs("nobody", "econometrics")) == 0


def test_get_model_runs_limit(test_db):
    for i in range(25):
        db.save_model_run("sbhatia", "ml_models", params={"run": i}, summary={"r2": 0.5})
    assert len(db.get_model_runs("sbhatia", "ml_models", limit=10)) == 10


def test_get_model_runs_ordered_newest_first(test_db):
    db.save_model_run("sbhatia", "econometrics", params={"run": 1}, summary={})
    db.save_model_run("sbhatia", "econometrics", params={"run": 2}, summary={})
    df = db.get_model_runs("sbhatia", "econometrics")
    # Most recent first — run_id 2 should be first row
    first_params = json.loads(df.iloc[0]["params"])
    assert first_params["run"] == 2


# ── busy_timeout ──────────────────────────────────────────────────────────────

def test_busy_timeout_in_exec_source():
    """_exec must set PRAGMA busy_timeout=10000 before every write."""
    src = inspect.getsource(db._exec)
    assert "busy_timeout" in src
    assert "10000" in src
