"""Shared fixtures for all tests."""

import os
import sys
import pytest
import pandas as pd
import sqlite3

# Add project root to path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

import db as db_module

DB_PATH = os.path.join(PROJECT_ROOT, "capital_structure.db")


@pytest.fixture(scope="session")
def db_conn():
    """Session-scoped DB connection."""
    conn = sqlite3.connect(DB_PATH)
    yield conn
    conn.close()


@pytest.fixture(scope="session")
def full_panel(db_conn):
    """Full panel dataset for model testing."""
    return pd.read_sql("""
        SELECT f.company_code, f.year, f.life_stage,
               f.leverage, f.profitability, f.tangibility, f.tax,
               f.dividend, f.firm_size, f.log_size, f.tax_shield,
               f.cash_holdings, f.borrowings, f.interest,
               f.ncfo, f.ncfi, f.ncff,
               f.gfc, f.ibc_2016, f.covid_dummy
        FROM financials f
        ORDER BY f.company_code, f.year
    """, db_conn)


@pytest.fixture(scope="session")
def small_panel(full_panel):
    """Smaller subset for fast tests."""
    firms = full_panel["company_code"].unique()[:50]
    return full_panel[full_panel["company_code"].isin(firms)].copy()


@pytest.fixture
def temp_audit_db(tmp_path, monkeypatch):
    """Redirect db.get_connection to a temp sqlite with audit_log schema."""
    p = tmp_path / "test.db"
    conn = sqlite3.connect(str(p))
    conn.execute("""
        CREATE TABLE audit_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ts TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            username TEXT,
            role TEXT,
            page_name TEXT,
            action_type TEXT,
            details TEXT,
            session_id TEXT
        )
    """)
    conn.commit()
    conn.close()
    # Patch db.get_connection to return a connection to the temp DB.
    # NOTE: the actual API is db.get_connection() (no leading underscore) —
    # do NOT patch a non-existent db._connection.
    def _temp_conn():
        return sqlite3.connect(str(p))
    monkeypatch.setattr(db_module, "get_connection", _temp_conn)
    yield str(p)


@pytest.fixture
def sample_company_code():
    """Real company_code from thesis panel — Asian Paints (matches test_board_export.py fixtures)."""
    return 22859


@pytest.fixture
def temp_chat_db(tmp_path, monkeypatch):
    """Redirect db.get_connection to a temp sqlite with chat_sessions + chat_messages schema."""
    p = tmp_path / "chat_test.db"
    conn = sqlite3.connect(str(p))
    conn.executescript("""
        CREATE TABLE chat_sessions (
            chat_session_id  TEXT PRIMARY KEY,
            username         TEXT NOT NULL,
            role             TEXT NOT NULL,
            title            TEXT,
            panel_mode       TEXT DEFAULT 'thesis',
            mode             TEXT DEFAULT 'Researcher',
            company_code     INTEGER,
            started_at       TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_active      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            message_count    INTEGER DEFAULT 0,
            archived         INTEGER DEFAULT 0
        );
        CREATE TABLE chat_messages (
            id               INTEGER PRIMARY KEY AUTOINCREMENT,
            chat_session_id  TEXT NOT NULL REFERENCES chat_sessions(chat_session_id) ON DELETE CASCADE,
            ts               TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            role             TEXT NOT NULL CHECK(role IN ('user','assistant')),
            content          TEXT NOT NULL,
            model_used       TEXT,
            elapsed_s        REAL,
            followups        TEXT,
            chart_spec       TEXT,
            feedback         TEXT
        );
        CREATE INDEX idx_chat_sessions_user
            ON chat_sessions(username, last_active DESC);
        CREATE INDEX idx_chat_messages_session
            ON chat_messages(chat_session_id, ts ASC);
    """)
    conn.commit()
    conn.close()

    def _temp_conn():
        return sqlite3.connect(str(p))

    monkeypatch.setattr(db_module, "get_connection", _temp_conn)
    yield str(p)
