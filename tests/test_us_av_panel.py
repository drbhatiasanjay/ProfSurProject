"""
Tests for US Alpha Vantage panel support.

Covers: vintage predicate, Dickinson life-stage mapping, field mapping
computations, firm-list integrity, and the is_india_panel helper.
No network calls; no DB writes.
"""
import math
import sys
import sqlite3
from pathlib import Path

import pytest

# Add project root to path so imports resolve without installing the package
sys.path.insert(0, str(Path(__file__).parent.parent))

from scripts.load_us_av_panel import (
    dickinson_stage, _map_row, TICKER_TO_CODE, US_FIRMS, VINTAGE,
)
from helpers import is_india_panel
from db import _vintage_predicate


# ── vintage predicate ─────────────────────────────────────────────────────────

def test_vintage_predicate_us_av():
    sql, params = _vintage_predicate("us_av_2024")
    assert "vintage" in sql
    assert params == ["us_av_2024"]
    assert "?" in sql


def test_vintage_predicate_us_av_with_prefix():
    sql, params = _vintage_predicate("us_av_2024", table_prefix="f")
    assert sql.startswith("f.")
    assert params == ["us_av_2024"]


# ── Dickinson life-stage ─────────────────────────────────────────────────────

_DICKINSON_CASES = [
    # (ncfo, ncfi, ncff, expected_stage)
    ( 1.0, -1.0, -1.0, "Growth"),
    ( 1.0, -1.0,  1.0, "Maturity"),
    ( 1.0,  1.0, -1.0, "Shakeout"),
    (-1.0, -1.0,  1.0, "Startup"),
    (-1.0,  1.0,  1.0, "Decline"),
    ( 1.0,  1.0,  1.0, "Decay"),
    (-1.0, -1.0, -1.0, "Shakeout2"),
    (-1.0,  1.0, -1.0, "Shakeout3"),
]


@pytest.mark.parametrize("ncfo,ncfi,ncff,expected", _DICKINSON_CASES)
def test_dickinson_all_8_stages(ncfo, ncfi, ncff, expected):
    assert dickinson_stage(ncfo, ncfi, ncff) == expected


def test_dickinson_zero_ncff_returns_none():
    assert dickinson_stage(1.0, -1.0, 0.0) is None


def test_dickinson_none_input_returns_none():
    assert dickinson_stage(None, -1.0, -1.0) is None


# ── Field mapping ─────────────────────────────────────────────────────────────

def _minimal_inc(**overrides):
    base = {
        "operatingIncome": "20",
        "netIncome": "10",
        "interestExpense": "2",
        "incomeTaxExpense": "5",
        "ebit": "25",
    }
    base.update(overrides)
    return base


def _minimal_bal(**overrides):
    base = {
        "totalAssets": "200",
        "longTermDebt": "50",
        "shortLongTermDebtTotal": "60",
        "propertyPlantEquipmentNet": "40",
        "totalLiabilities": "120",
        "cashAndCashEquivalentsAtCarryingValue": "15",
    }
    base.update(overrides)
    return base


def _minimal_cf(**overrides):
    base = {
        "operatingCashflow": "30",
        "capitalExpenditures": "10",
        "dividendPayout": "4",
        "repaymentOfLongTermDebt": "6",
    }
    base.update(overrides)
    return base


def test_field_mapping_leverage():
    row = _map_row(_minimal_inc(), _minimal_bal(), _minimal_cf(), "IBM", 2020)
    # leverage = longTermDebt(50) / totalAssets(200) = 0.25
    assert abs(row["leverage"] - 0.25) < 1e-9


def test_field_mapping_profitability():
    row = _map_row(_minimal_inc(), _minimal_bal(), _minimal_cf(), "IBM", 2020)
    # profitability = operatingIncome(20) / totalAssets(200) = 0.10
    assert abs(row["profitability"] - 0.10) < 1e-9


def test_field_mapping_firm_size():
    row = _map_row(_minimal_inc(), _minimal_bal(), _minimal_cf(), "IBM", 2020)
    # firm_size = log(200) in natural log
    assert abs(row["firm_size"] - math.log(200)) < 1e-9


def test_field_mapping_gfc_dummy():
    row_2008 = _map_row(_minimal_inc(), _minimal_bal(), _minimal_cf(), "IBM", 2008)
    row_2020 = _map_row(_minimal_inc(), _minimal_bal(), _minimal_cf(), "IBM", 2020)
    assert row_2008["gfc"] == 1
    assert row_2020["gfc"] == 0


def test_field_mapping_covid_dummy():
    row_2020 = _map_row(_minimal_inc(), _minimal_bal(), _minimal_cf(), "IBM", 2020)
    row_2019 = _map_row(_minimal_inc(), _minimal_bal(), _minimal_cf(), "IBM", 2019)
    assert row_2020["covid_dummy"] == 1
    assert row_2019["covid_dummy"] == 0


def test_field_mapping_ibc_is_null():
    row = _map_row(_minimal_inc(), _minimal_bal(), _minimal_cf(), "IBM", 2020)
    assert row["ibc_2016"] is None


def test_field_mapping_vintage():
    row = _map_row(_minimal_inc(), _minimal_bal(), _minimal_cf(), "IBM", 2020)
    assert row["vintage"] == VINTAGE


# ── Firm list integrity ───────────────────────────────────────────────────────

def test_firm_list_unique_codes():
    codes = list(TICKER_TO_CODE.values())
    assert len(codes) == len(set(codes)), "Duplicate company_codes in US_FIRMS"


def test_firm_list_codes_above_900000():
    assert all(code > 900_000 for code in TICKER_TO_CODE.values())


def test_firm_list_covers_all_tickers():
    tickers_in_firms = {t for t, _, _ in US_FIRMS}
    assert set(TICKER_TO_CODE.keys()) == tickers_in_firms


# ── is_india_panel helper ─────────────────────────────────────────────────────

@pytest.mark.parametrize("mode,expected", [
    ("thesis",     True),
    ("latest",     True),
    ("run3",       True),
    ("us_av_2024", False),
    ("unknown",    False),
])
def test_is_india_panel(mode, expected):
    assert is_india_panel(mode) == expected


# ── Schema migration idempotency ──────────────────────────────────────────────

def test_schema_migration_idempotent():
    """Running the migration SQL twice on an in-memory DB raises no unhandled error."""
    conn = sqlite3.connect(":memory:")
    conn.execute("CREATE TABLE companies (company_code INTEGER PRIMARY KEY, company_name TEXT)")
    conn.commit()

    migration_sql = [
        "ALTER TABLE companies ADD COLUMN country TEXT DEFAULT 'India'",
        "ALTER TABLE companies ADD COLUMN ticker  TEXT",
    ]
    for stmt in migration_sql:
        conn.execute(stmt)
    conn.commit()

    # Second application: should not raise (duplicate column caught in load script)
    for stmt in migration_sql:
        try:
            conn.execute(stmt)
        except sqlite3.OperationalError as e:
            assert "duplicate column name" in str(e).lower()

    conn.close()
