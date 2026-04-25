"""
Data layer for LifeCycle Leverage Dashboard.
All SQL queries, caching, and connection management.
"""

import os
import sqlite3
import pandas as pd
import streamlit as st
from datetime import datetime, timezone

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "capital_structure.db")


def is_cmie_lab_enabled() -> bool:
    """
    Gate all CMIE UI and CMIE-backed data paths. Default: off (production parity).

    Enable with environment variable ENABLE_CMIE=true (or 1/yes/on), or Streamlit
    secret ENABLE_CMIE=true. Used by upstream repo; fork labs turn this on.
    """
    v = os.environ.get("ENABLE_CMIE", "").strip().lower()
    if v in ("1", "true", "yes", "on"):
        return True
    if v in ("0", "false", "no", "off"):
        return False
    try:
        sec = st.secrets.get("ENABLE_CMIE", False)
        if isinstance(sec, str):
            return sec.strip().lower() in ("1", "true", "yes", "on")
        return bool(sec)
    except Exception:
        return False


# Set WAL mode once at import time, not per-connection
_init_conn = sqlite3.connect(DB_PATH)
_init_conn.execute("PRAGMA journal_mode=WAL")
_init_conn.close()


def get_connection():
    return sqlite3.connect(DB_PATH, check_same_thread=False)


def db_cache_revision() -> int:
    """Integer that changes when the SQLite file on disk changes (for Streamlit cache keys)."""
    try:
        return int(os.path.getmtime(DB_PATH))
    except OSError:
        return 0


def _query(sql, params=None):
    """Execute a read query with automatic connection cleanup."""
    conn = get_connection()
    try:
        df = pd.read_sql(sql, conn, params=params)
    finally:
        conn.close()
    return df


def _exec(sql: str, params=None) -> None:
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute("PRAGMA foreign_keys=ON")
        cur.execute(sql, params or [])
        conn.commit()
    finally:
        conn.close()


def ensure_cmie_tables():
    """
    Create versioned CMIE import tables if missing.
    Kept in db.py so Streamlit pages can rely on it without separate migrations.
    """
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute("PRAGMA journal_mode=WAL")
        cur.execute("PRAGMA foreign_keys=ON")

        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS api_imports (
                import_id TEXT PRIMARY KEY,
                company_code INTEGER,
                requested_at TEXT NOT NULL,
                finished_at TEXT,
                status TEXT NOT NULL, -- running|success|failed
                error_code TEXT,
                error_message TEXT,
                bytes_downloaded INTEGER,
                rows_written INTEGER,
                year_min INTEGER,
                year_max INTEGER,
                indicators TEXT,
                files TEXT
            )
            """
        )

        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS api_versions (
                version_id TEXT PRIMARY KEY,
                company_code INTEGER,
                import_id TEXT NOT NULL,
                created_at TEXT NOT NULL,
                is_current INTEGER NOT NULL DEFAULT 0,
                note TEXT,
                FOREIGN KEY(import_id) REFERENCES api_imports(import_id)
            )
            """
        )

        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS api_financials (
                version_id TEXT NOT NULL,
                company_code INTEGER NOT NULL,
                year INTEGER NOT NULL,
                life_stage TEXT,
                leverage REAL,
                profitability REAL,
                tangibility REAL,
                tax REAL,
                dividend REAL,
                firm_size REAL,
                log_size REAL,
                tax_shield REAL,
                borrowings REAL,
                total_liabilities REAL,
                cash_holdings REAL,
                ncfo REAL,
                ncfi REAL,
                ncff REAL,
                gfc INTEGER,
                ibc_2016 INTEGER,
                covid_dummy INTEGER,
                PRIMARY KEY (version_id, company_code, year)
            )
            """
        )

        cur.execute("CREATE INDEX IF NOT EXISTS idx_api_financials_version ON api_financials(version_id)")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_api_versions_current ON api_versions(company_code, is_current)")
        conn.commit()
    finally:
        conn.close()


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def get_current_api_version(company_code: int | None = None) -> str | None:
    ensure_cmie_tables()
    if company_code is None:
        df = _query("SELECT version_id FROM api_versions WHERE is_current = 1 ORDER BY created_at DESC LIMIT 1")
    else:
        df = _query(
            "SELECT version_id FROM api_versions WHERE is_current = 1 AND company_code = ? ORDER BY created_at DESC LIMIT 1",
            [company_code],
        )
    return df["version_id"].iloc[0] if not df.empty else None


def mark_current_api_version(version_id: str, company_code: int | None = None) -> None:
    ensure_cmie_tables()
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute("PRAGMA foreign_keys=ON")
        if company_code is None:
            cur.execute("UPDATE api_versions SET is_current = 0")
        else:
            cur.execute("UPDATE api_versions SET is_current = 0 WHERE company_code = ?", [company_code])
        cur.execute("UPDATE api_versions SET is_current = 1 WHERE version_id = ?", [version_id])
        conn.commit()
    finally:
        conn.close()


def insert_import_row(import_id: str, company_code: int | None, *, status: str, indicators: str = "", files: str = "") -> None:
    ensure_cmie_tables()
    _exec(
        """
        INSERT OR REPLACE INTO api_imports(import_id, company_code, requested_at, status, indicators, files)
        VALUES(?,?,?,?,?,?)
        """,
        [import_id, company_code, utc_now_iso(), status, indicators, files],
    )


def finish_import_row(
    import_id: str,
    *,
    status: str,
    error_code: str | None = None,
    error_message: str | None = None,
    bytes_downloaded: int | None = None,
    rows_written: int | None = None,
    year_min: int | None = None,
    year_max: int | None = None,
) -> None:
    ensure_cmie_tables()
    _exec(
        """
        UPDATE api_imports
        SET finished_at = ?, status = ?, error_code = ?, error_message = ?,
            bytes_downloaded = ?, rows_written = ?, year_min = ?, year_max = ?
        WHERE import_id = ?
        """,
        [utc_now_iso(), status, error_code, error_message, bytes_downloaded, rows_written, year_min, year_max, import_id],
    )


def create_version(import_id: str, company_code: int | None, note: str = "") -> str:
    ensure_cmie_tables()
    version_id = f"v_{import_id}"
    _exec(
        """
        INSERT OR REPLACE INTO api_versions(version_id, company_code, import_id, created_at, is_current, note)
        VALUES(?,?,?,?,0,?)
        """,
        [version_id, company_code, import_id, utc_now_iso(), note],
    )
    return version_id


def write_api_financials(version_id: str, panel_df: pd.DataFrame) -> int:
    """
    Store normalized panel rows into api_financials for the given version_id.
    """
    ensure_cmie_tables()
    if panel_df.empty:
        return 0

    df = panel_df.copy()
    df["version_id"] = version_id

    cols = [
        "version_id",
        "company_code",
        "year",
        "life_stage",
        "leverage",
        "profitability",
        "tangibility",
        "tax",
        "dividend",
        "firm_size",
        "log_size",
        "tax_shield",
        "borrowings",
        "total_liabilities",
        "cash_holdings",
        "ncfo",
        "ncfi",
        "ncff",
        "gfc",
        "ibc_2016",
        "covid_dummy",
    ]
    df = df[[c for c in cols if c in df.columns]]

    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute("PRAGMA foreign_keys=ON")
        cur.execute("BEGIN")
        cur.execute("DELETE FROM api_financials WHERE version_id = ?", [version_id])
        df.to_sql("api_financials", conn, if_exists="append", index=False, method="multi", chunksize=2000)
        cur.execute("COMMIT")
    except Exception:
        try:
            conn.rollback()
        except Exception:
            pass
        raise
    finally:
        conn.close()

    return int(len(df))


def _where_api_financials_join(filters_tuple):
    """WHERE clause for api_financials + companies join (industry lives on c, not f)."""
    filters = _deserialize_filters(filters_tuple)
    where, params = _build_where(filters, "f")
    where = where.replace("f.industry_group", "c.industry_group")
    return where, params


@st.cache_data(ttl=300)
def get_api_financials(version_id: str, _filters_tuple):
    """
    Read normalized CMIE panel rows for the active version_id and apply the same global filters.
    """
    where, params = _where_api_financials_join(_filters_tuple)
    sql = f"""
        SELECT
            f.company_code,
            c.company_name,
            c.nse_symbol,
            c.industry_group,
            c.inc_year,
            f.year,
            f.life_stage,
            f.leverage,
            f.profitability,
            f.tangibility,
            f.tax,
            f.dividend,
            f.firm_size,
            f.log_size,
            f.tax_shield,
            f.borrowings,
            f.total_liabilities,
            f.cash_holdings,
            f.ncfo,
            f.ncfi,
            f.ncff,
            f.gfc,
            f.ibc_2016,
            f.covid_dummy
        FROM api_financials f
        LEFT JOIN companies c ON f.company_code = c.company_code
        WHERE f.version_id = ? AND {where}
        ORDER BY c.company_name, f.year
    """
    return _query(sql, [version_id] + params)


@st.cache_data(ttl=300)
def get_api_panel_data(version_id: str, _filters_tuple):
    """
    Panel shaped like get_panel_data but sourced from api_financials for the given version.
    Interest / int_rate columns come from packaged financials when the same (company_code, year) exists.
    """
    where, params = _where_api_financials_join(_filters_tuple)
    sql = f"""
        SELECT f.company_code, f.year, f.life_stage,
               f.leverage, f.profitability, f.tangibility, f.tax,
               f.dividend, f.firm_size, f.log_size, f.tax_shield,
               f.borrowings, f.total_liabilities, f.cash_holdings,
               f.ncfo, f.ncfi, f.ncff,
               f_stat.interest, f_stat.int_rate, f_stat.int_rate_lt,
               f.gfc, f.ibc_2016, f.covid_dummy,
               c.industry_group,
               o.promoter_share, o.non_promoters,
               m.index_pe, m.index_pb, m.daily_returns AS market_return,
               m.index_yield AS market_yield
        FROM api_financials f
        LEFT JOIN companies c ON f.company_code = c.company_code
        LEFT JOIN financials f_stat ON f.company_code = f_stat.company_code AND f.year = f_stat.year
        LEFT JOIN ownership o ON f.company_code = o.company_code AND f.year = o.year
        LEFT JOIN market_index m ON f.year = m.year
        WHERE f.version_id = ? AND {where}
        ORDER BY f.company_code, f.year
    """
    return _query(sql, [version_id] + params)


@st.cache_data(ttl=300)
def get_api_life_stage_summary(version_id: str, _filters_tuple):
    """Aggregate life-stage × year from CMIE-imported api_financials (same shape as get_life_stage_summary)."""
    where, params = _where_api_financials_join(_filters_tuple)
    sql = f"""
        SELECT f.life_stage, f.year,
               COUNT(*) AS num_firms,
               AVG(f.leverage) AS avg_leverage,
               AVG(f.profitability) AS avg_profitability,
               AVG(f.tangibility) AS avg_tangibility,
               AVG(f.firm_size) AS avg_size,
               AVG(f.tax_shield) AS avg_tax_shield,
               AVG(f.cash_holdings) AS avg_cash_holdings
        FROM api_financials f
        LEFT JOIN companies c ON f.company_code = c.company_code
        WHERE f.version_id = ? AND {where}
        GROUP BY f.life_stage, f.year
        ORDER BY f.year
    """
    return _query(sql, [version_id] + params)


def get_active_life_stage_summary(_filters_tuple):
    """Match get_life_stage_summary when using CMIE active version."""
    if not is_cmie_lab_enabled():
        return get_life_stage_summary(_filters_tuple)
    mode = getattr(st.session_state, "data_source_mode", "sqlite")
    if mode == "cmie":
        version_id = get_current_api_version()
        if version_id:
            return get_api_life_stage_summary(version_id, _filters_tuple)
    return get_life_stage_summary(_filters_tuple)


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
def get_year_range(panel_mode: str = "latest"):
    """Year range of the selected panel.

    - `thesis` (2001-2024) — frozen replication panel
    - `latest` (2001-present) — thesis + cmie_2025 rollforward (production panel)
    - `run3`   (2001-2025)   — Stata replication panel from initialResults.do (parallel
                              to thesis + cmie_2025; overlapping years; do not union with them)
    """
    if panel_mode == "thesis":
        sql = "SELECT MIN(year) as min_yr, MAX(year) as max_yr FROM financials WHERE vintage = 'thesis'"
    elif panel_mode == "run3":
        sql = "SELECT MIN(year) as min_yr, MAX(year) as max_yr FROM financials WHERE vintage = 'run3'"
    else:
        # `latest` = production panel only (thesis + cmie_2025). run3 is intentionally excluded
        # because its 2001-2024 rows overlap with the thesis vintage; unioning would double-count.
        sql = "SELECT MIN(year) as min_yr, MAX(year) as max_yr FROM financials WHERE vintage IN ('thesis', 'cmie_2025')"
    row = _query(sql)
    return int(row["min_yr"].iloc[0]), int(row["max_yr"].iloc[0])


@st.cache_data(ttl=3600)
def get_data_vintages():
    """All loaded vintages with human labels. Drives the Panel dropdown."""
    return _query("SELECT vintage, label, loaded_at, description FROM data_vintages ORDER BY vintage")


def _vintage_predicate(panel_mode: str, table_prefix: str = "") -> tuple[str, list]:
    """Return (SQL fragment, params) for the panel_mode vintage predicate.

    Three production modes:
      thesis  → vintage = 'thesis'                       (2001-2024 frozen panel)
      latest  → vintage IN ('thesis', 'cmie_2025')       (production: thesis + 2025 rollforward)
      run3    → vintage = 'run3'                         (Stata replication, 2001-2025)

    Run3 is deliberately NOT in `latest` because its rows overlap thesis years —
    unioning them would double-count. Future additive vintages (e.g. cmie_2026) should
    be appended to the `latest` IN-list explicitly; replication / alternate panels stay
    standalone.
    """
    p = f"{table_prefix}." if table_prefix else ""
    if panel_mode == "thesis":
        return f"{p}vintage = ?", ["thesis"]
    if panel_mode == "run3":
        return f"{p}vintage = ?", ["run3"]
    # `latest` — production union. Hardcoded list so we control which vintages compose it.
    vintages = ["thesis", "cmie_2025"]
    placeholders = ",".join("?" * len(vintages))
    return f"{p}vintage IN ({placeholders})", vintages


# ── Core filtered queries ──

def _build_where(filters, table_prefix=""):
    p = f"{table_prefix}." if table_prefix else ""
    clauses = ["1=1"]
    params = []

    # Panel mode → vintage predicate. Defaults to 'latest' if not set (Dashboard/Benchmarks/Explorer).
    # Reproducibility-critical pages (Econometrics/ML/Forecasting) set panel_mode='thesis' before querying.
    panel_mode = filters.get("panel_mode", "latest")
    vintage_sql, vintage_params = _vintage_predicate(panel_mode, table_prefix)
    clauses.append(vintage_sql)
    params.extend(vintage_params)

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
               cash_holdings, gfc, ibc_2016, covid_dummy,
               vintage
        FROM v_company_financials
        WHERE {where}
        ORDER BY company_name, year
    """
    return _query(sql, params)


def get_active_financials(_filters_tuple):
    """
    Unified accessor used by pages.
    - If sidebar mode is 'cmie' and a current API version exists, return api_financials join.
    - Otherwise fall back to the packaged SQLite view.
    """
    if not is_cmie_lab_enabled():
        return get_filtered_financials(_filters_tuple)
    mode = getattr(st.session_state, "data_source_mode", "sqlite")
    if mode == "cmie":
        version_id = get_current_api_version()
        if version_id:
            return get_api_financials(version_id, _filters_tuple)
    return get_filtered_financials(_filters_tuple)


def get_active_panel_data(_filters_tuple):
    """
    Same contract as get_panel_data for econometrics/ML pages.
    When ENABLE_CMIE is on and data_source_mode is cmie with a current API version, read api_financials path.
    """
    if not is_cmie_lab_enabled():
        return get_panel_data(_filters_tuple)
    mode = getattr(st.session_state, "data_source_mode", "sqlite")
    if mode == "cmie":
        version_id = get_current_api_version()
        if version_id:
            return get_api_panel_data(version_id, _filters_tuple)
    return get_panel_data(_filters_tuple)


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
def get_market_index(year_min, year_max, index_code: int | None = None):
    """Market index closing values. Default (index_code=None) keeps Sensex back-compat via the
    legacy market_index table (rich fields: PE, PB, yield, beta, ...). If an explicit index_code
    is passed, pull closing values from market_index_series (T623 has 700+ series)."""
    if index_code is None:
        sql = """
            SELECT year, index_opening, index_closing, index_high, index_low,
                   index_market_cap, daily_returns, excess_returns,
                   index_pe, index_pb, index_yield, index_beta
            FROM market_index
            WHERE year BETWEEN ? AND ?
            ORDER BY year
        """
        return _query(sql, [year_min, year_max])

    sql = """
        SELECT year, index_name, index_closing
        FROM market_index_series
        WHERE index_code = ? AND year BETWEEN ? AND ?
        ORDER BY year
    """
    return _query(sql, [index_code, year_min, year_max])


@st.cache_data(ttl=3600)
def get_available_indices():
    """All T623 market index series with their latest closing year. Drives the Dashboard index picker."""
    sql = """
        SELECT index_code, index_name, MIN(year) AS year_min, MAX(year) AS year_max, COUNT(*) AS n_years
        FROM market_index_series
        GROUP BY index_code, index_name
        ORDER BY index_name
    """
    return _query(sql)


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
def get_db_metadata(panel_mode: str = "latest"):
    vintage_sql, vintage_params = _vintage_predicate(panel_mode, "f")
    df = _query(f"""
        SELECT
            COUNT(DISTINCT f.company_code) AS total_firms,
            COUNT(*) AS total_obs,
            MIN(f.year) AS year_min,
            MAX(f.year) AS year_max,
            (SELECT COUNT(DISTINCT industry_group) FROM companies) AS industries
        FROM financials f
        WHERE {vintage_sql}
    """, vintage_params)
    row = df.iloc[0]
    return {
        "total_firms": int(row["total_firms"]),
        "total_obs": int(row["total_obs"]),
        "year_min": int(row["year_min"]),
        "year_max": int(row["year_max"]),
        "industries": int(row["industries"]),
        "panel_mode": panel_mode,
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
