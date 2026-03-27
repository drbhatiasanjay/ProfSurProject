"""Shared fixtures for all tests."""

import os
import sys
import pytest
import pandas as pd
import sqlite3

# Add project root to path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

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
