"""
Data layer for LifeCycle Leverage Dashboard.
All SQL queries, caching, and connection management.
"""

import os
import sqlite3
import pandas as pd
import streamlit as st

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "capital_structure.db")

# Set WAL mode once at import time, not per-connection
_init_conn = sqlite3.connect(DB_PATH)
_init_conn.execute("PRAGMA journal_mode=WAL")
_init_conn.close()


def get_connection():
    return sqlite3.connect(DB_PATH, check_same_thread=False)


def _query(sql, params=None):
    """Execute a read query with automatic connection cleanup."""
    conn = get_connection()
    try:
        df = pd.read_sql(sql, conn, params=params)
    finally:
        conn.close()
    return df


def _deserialize_filters(filters_tuple):
    """Convert cached tuple back to a usable filters dict."""
    filters = dict(filters_tuple)
    for key in ("company_codes", "life_stages", "industry_groups"):
        if filters.get(key):
            filters[key] = list(filters[key])
    if filters.get("events"):
        filters["events"] = dict(filters["events"])
    return filters


# ── Lookup queries (long cache) ──

@st.cache_data(ttl=3600)
def get_companies():
    return _query("SELECT company_code, company_name, nse_symbol, industry_group FROM companies ORDER BY company_name")


@st.cache_data(ttl=3600)
def get_life_stages():
    df = _query("SELECT stage_name FROM life_stages ORDER BY cls_code")
    return df["stage_name"].tolist()


@st.cache_data(ttl=3600)
def get_industry_groups():
    df = _query("SELECT DISTINCT industry_group FROM companies ORDER BY industry_group")
    return df["industry_group"].tolist()


@st.cache_data(ttl=3600)
def get_year_range():
    row = _query("SELECT MIN(year) as min_yr, MAX(year) as max_yr FROM financials")
    return int(row["min_yr"].iloc[0]), int(row["max_yr"].iloc[0])


# ── Core filtered queries ──

def _build_where(filters, table_prefix=""):
    p = f"{table_prefix}." if table_prefix else ""
    clauses = ["1=1"]
    params = []

    yr = filters.get("year_range", (2001, 2024))
    clauses.append(f"{p}year BETWEEN ? AND ?")
    params.extend([yr[0], yr[1]])

    if filters.get("company_codes"):
        placeholders = ",".join("?" * len(filters["company_codes"]))
        clauses.append(f"{p}company_code IN ({placeholders})")
        params.extend(filters["company_codes"])

    if filters.get("life_stages"):
        placeholders = ",".join("?" * len(filters["life_stages"]))
        clauses.append(f"{p}life_stage IN ({placeholders})")
        params.extend(filters["life_stages"])

    if filters.get("industry_groups"):
        placeholders = ",".join("?" * len(filters["industry_groups"]))
        clauses.append(f"{p}industry_group IN ({placeholders})")
        params.extend(filters["industry_groups"])

    events = filters.get("events", {})
    event_conditions = []
    if events.get("gfc"):
        event_conditions.append(f"{p}gfc = 1")
    if events.get("ibc"):
        event_conditions.append(f"{p}ibc_2016 = 1")
    if events.get("covid"):
        event_conditions.append(f"{p}covid_dummy = 1")
    if event_conditions:
        clauses.append(f"({' OR '.join(event_conditions)})")

    return " AND ".join(clauses), params


@st.cache_data(ttl=600)
def get_filtered_financials(_filters_tuple):
    filters = _deserialize_filters(_filters_tuple)
    where, params = _build_where(filters)
    sql = f"""
        SELECT company_code, company_name, nse_symbol, industry_group, inc_year,
               year, age_group, size_decile, life_stage,
               leverage, profitability, tangibility, tax, dividend,
               firm_size, tax_shield, borrowings, total_liabilities,
               cash_holdings, gfc, ibc_2016, covid_dummy
        FROM v_company_financials
        WHERE {where}
        ORDER BY company_name, year
    """
    return _query(sql, params)


@st.cache_data(ttl=600)
def get_life_stage_summary(_filters_tuple):
    filters = _deserialize_filters(_filters_tuple)
    where, params = _build_where(filters, "f")
    sql = f"""
        SELECT f.life_stage, f.year,
               COUNT(*) AS num_firms,
               AVG(f.leverage) AS avg_leverage,
               AVG(f.profitability) AS avg_profitability,
               AVG(f.tangibility) AS avg_tangibility,
               AVG(f.firm_size) AS avg_size,
               AVG(f.tax_shield) AS avg_tax_shield,
               AVG(f.cash_holdings) AS avg_cash_holdings
        FROM financials f
        WHERE {where}
        GROUP BY f.life_stage, f.year
        ORDER BY f.year
    """
    return _query(sql, params)


@st.cache_data(ttl=600)
def get_industry_summary(_filters_tuple):
    filters = _deserialize_filters(_filters_tuple)
    where, params = _build_where(filters, "f")
    sql = f"""
        SELECT c.industry_group, f.year,
               COUNT(*) AS num_firms,
               AVG(f.leverage) AS avg_leverage,
               AVG(f.profitability) AS avg_profitability,
               AVG(f.borrowings) AS avg_borrowings
        FROM financials f
        JOIN companies c ON f.company_code = c.company_code
        WHERE {where}
        GROUP BY c.industry_group, f.year
        ORDER BY c.industry_group, f.year
    """
    return _query(sql, params)


@st.cache_data(ttl=600)
def get_company_detail(company_code):
    sql = """
        SELECT f.year, f.life_stage, f.leverage, f.profitability, f.tangibility,
               f.tax, f.dividend, f.firm_size, f.tax_shield, f.borrowings,
               f.total_liabilities, f.cash_holdings, f.ncfo, f.ncfi, f.ncff,
               f.gfc, f.ibc_2016, f.covid_dummy,
               o.promoter_share, o.indian_promoters, o.foreign_promoters,
               o.non_promoters, o.non_promoter_institutions, o.non_promoter_fiis
        FROM financials f
        LEFT JOIN ownership o ON f.company_code = o.company_code AND f.year = o.year
        WHERE f.company_code = ?
        ORDER BY f.year
    """
    return _query(sql, [company_code])


@st.cache_data(ttl=600)
def get_top_leveraged(n, _filters_tuple):
    filters = _deserialize_filters(_filters_tuple)
    where, params = _build_where(filters)
    sql = f"""
        SELECT company_name, life_stage,
               AVG(leverage) AS avg_leverage,
               COUNT(*) AS obs
        FROM v_company_financials
        WHERE {where}
        GROUP BY company_name, life_stage
        HAVING AVG(leverage) IS NOT NULL
        ORDER BY avg_leverage DESC
        LIMIT ?
    """
    params.append(n)
    return _query(sql, params)


@st.cache_data(ttl=600)
def get_market_index(year_min, year_max):
    sql = """
        SELECT year, index_opening, index_closing, index_high, index_low,
               index_market_cap, daily_returns, excess_returns,
               index_pe, index_pb, index_yield, index_beta
        FROM market_index
        WHERE year BETWEEN ? AND ?
        ORDER BY year
    """
    return _query(sql, [year_min, year_max])


@st.cache_data(ttl=3600)
def get_leverage_percentiles():
    df = _query("SELECT leverage FROM financials WHERE leverage IS NOT NULL ORDER BY leverage")
    return df["leverage"].quantile(0.01), df["leverage"].quantile(0.99)


@st.cache_data(ttl=600)
def get_full_data_explorer(_filters_tuple):
    filters = _deserialize_filters(_filters_tuple)
    where, params = _build_where(filters, "f")
    sql = f"""
        SELECT c.company_name, c.nse_symbol, c.industry_group, f.year, f.life_stage,
               f.leverage, f.profitability, f.tangibility, f.tax, f.dividend,
               f.firm_size, f.tax_shield, f.borrowings, f.total_liabilities,
               f.cash_holdings, f.ncfo, f.ncfi, f.ncff,
               o.promoter_share, o.non_promoters
        FROM financials f
        JOIN companies c ON f.company_code = c.company_code
        LEFT JOIN ownership o ON f.company_code = o.company_code AND f.year = o.year
        WHERE {where}
        ORDER BY c.company_name, f.year
    """
    return _query(sql, params)


@st.cache_data(ttl=3600)
def get_db_metadata():
    df = _query("""
        SELECT
            COUNT(DISTINCT f.company_code) AS total_firms,
            COUNT(*) AS total_obs,
            MIN(f.year) AS year_min,
            MAX(f.year) AS year_max,
            (SELECT COUNT(DISTINCT industry_group) FROM companies) AS industries
        FROM financials f
    """)
    row = df.iloc[0]
    return {
        "total_firms": int(row["total_firms"]),
        "total_obs": int(row["total_obs"]),
        "year_min": int(row["year_min"]),
        "year_max": int(row["year_max"]),
        "industries": int(row["industries"]),
    }


@st.cache_data(ttl=3600)
def get_graph_financials():
    """Get financial data formatted for knowledge graph construction."""
    return _query("""
        SELECT f.company_code, c.company_name, c.industry_group,
               f.year, f.life_stage, f.leverage, f.profitability,
               f.tangibility, f.tax, f.firm_size, f.tax_shield,
               f.cash_holdings, f.borrowings,
               f.gfc, f.ibc_2016, f.covid_dummy
        FROM financials f
        JOIN companies c ON f.company_code = c.company_code
        ORDER BY f.company_code, f.year
    """)


@st.cache_data(ttl=3600)
def get_graph_ownership():
    """Get ownership data formatted for knowledge graph construction."""
    return _query("""
        SELECT company_code, year, promoter_share, non_promoters
        FROM ownership
        ORDER BY company_code, year
    """)


@st.cache_data(ttl=600)
def get_panel_data(_filters_tuple):
    """Get panel data ready for econometric/ML modeling. Returns flat DataFrame."""
    filters = _deserialize_filters(_filters_tuple)
    where, params = _build_where(filters, "f")
    sql = f"""
        SELECT f.company_code, f.year, f.life_stage,
               f.leverage, f.profitability, f.tangibility, f.tax,
               f.dividend, f.firm_size, f.log_size, f.tax_shield,
               f.borrowings, f.total_liabilities, f.cash_holdings,
               f.ncfo, f.ncfi, f.ncff, f.interest,
               f.int_rate, f.int_rate_lt,
               f.gfc, f.ibc_2016, f.covid_dummy,
               c.industry_group,
               o.promoter_share, o.non_promoters,
               m.index_pe, m.index_pb, m.daily_returns AS market_return,
               m.index_yield AS market_yield
        FROM financials f
        JOIN companies c ON f.company_code = c.company_code
        LEFT JOIN ownership o ON f.company_code = o.company_code AND f.year = o.year
        LEFT JOIN market_index m ON f.year = m.year
        WHERE {where}
        ORDER BY f.company_code, f.year
    """
    return _query(sql, params)


def filters_to_tuple(filters):
    """Convert filters dict to a hashable tuple for st.cache_data."""
    return tuple(
        (k, tuple(v) if isinstance(v, list) else
            tuple(sorted(v.items())) if isinstance(v, dict) else v)
        for k, v in sorted(filters.items())
    )
