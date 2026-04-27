"""
Alpha Vantage ingestion script for US S&P sample panel.

Fetches annual financial statements (INCOME_STATEMENT, BALANCE_SHEET, CASH_FLOW)
for 25 DJIA / S&P blue-chip firms and loads them into the `financials` table as
vintage='us_av_2024'.  Writes no other tables and does not touch Indian data.

Usage:
    py -3.12 scripts/load_us_av_panel.py --api-key <KEY>
    py -3.12 scripts/load_us_av_panel.py --api-key <KEY> --tickers IBM,AAPL
    py -3.12 scripts/load_us_av_panel.py --api-key demo --tickers IBM --dry-run

Environment variable alternative:
    ALPHA_VANTAGE_KEY=<KEY> py -3.12 scripts/load_us_av_panel.py

Rate limits (Alpha Vantage free tier): 5 calls/min, 25 calls/day.
Each firm needs 3 calls, so 25 firms = 75 calls.
Script sleeps 12 s between calls to stay within 5/min.
Full 25-firm load takes ~15 min.  Use --tickers to load a subset.
"""
from __future__ import annotations

import argparse
import datetime
import json
import math
import os
import sqlite3
import sys
import time
from pathlib import Path

import requests

# ── Firm catalogue ──────────────────────────────────────────────────────────
# synthetic company_code = 9000001 + list index (avoids collision with CMIE codes ≤ ~730 000)
US_FIRMS: list[tuple[str, str, str]] = [
    # (ticker, company_name, gics_sector)
    ("AAPL",  "Apple Inc.",               "Technology"),
    ("MSFT",  "Microsoft Corp.",           "Technology"),
    ("IBM",   "IBM Corp.",                "Technology"),
    ("CSCO",  "Cisco Systems Inc.",        "Technology"),
    ("JPM",   "JPMorgan Chase & Co.",      "Financials"),
    ("GS",    "Goldman Sachs Group Inc.",  "Financials"),
    ("AXP",   "American Express Co.",      "Financials"),
    ("V",     "Visa Inc.",                "Financials"),
    ("JNJ",   "Johnson & Johnson",         "Health Care"),
    ("UNH",   "UnitedHealth Group Inc.",   "Health Care"),
    ("MRK",   "Merck & Co. Inc.",          "Health Care"),
    ("AMGN",  "Amgen Inc.",               "Health Care"),
    ("WMT",   "Walmart Inc.",              "Consumer Staples"),
    ("PG",    "Procter & Gamble Co.",      "Consumer Staples"),
    ("KO",    "Coca-Cola Co.",             "Consumer Staples"),
    ("MCD",   "McDonald's Corp.",          "Consumer Discretionary"),
    ("NKE",   "Nike Inc.",                "Consumer Discretionary"),
    ("HD",    "Home Depot Inc.",           "Consumer Discretionary"),
    ("CVX",   "Chevron Corp.",             "Energy"),
    ("CAT",   "Caterpillar Inc.",          "Industrials"),
    ("HON",   "Honeywell International",   "Industrials"),
    ("BA",    "Boeing Co.",               "Industrials"),
    ("VZ",    "Verizon Communications",    "Communication Services"),
    ("DIS",   "Walt Disney Co.",           "Communication Services"),
    ("MMM",   "3M Company",               "Materials"),
]

VINTAGE = "us_av_2024"
CODE_BASE = 9_000_001  # US firm codes start here

TICKER_TO_CODE: dict[str, int] = {
    ticker: CODE_BASE + i for i, (ticker, _, _) in enumerate(US_FIRMS)
}

AV_BASE = "https://www.alphavantage.co/query"
INTER_CALL_SLEEP = 12  # seconds — keeps calls/min <= 5

# ── Dickinson (2011) life-stage map ─────────────────────────────────────────
# sign(ncfo), sign(ncfi), sign(ncff) -> stage_name
_DICKINSON: dict[tuple[int, int, int], str] = {
    ( 1, -1, -1): "Growth",
    ( 1, -1,  1): "Maturity",
    ( 1,  1, -1): "Shakeout",
    (-1, -1,  1): "Startup",
    (-1,  1,  1): "Decline",
    ( 1,  1,  1): "Decay",
    (-1, -1, -1): "Shakeout2",
    (-1,  1, -1): "Shakeout3",
}


def _sgn(v: float | None) -> int:
    if v is None or math.isnan(v):
        return 0
    return 1 if v > 0 else (-1 if v < 0 else 0)


def dickinson_stage(ncfo: float | None, ncfi: float | None, ncff: float | None) -> str | None:
    key = (_sgn(ncfo), _sgn(ncfi), _sgn(ncff))
    if 0 in key:
        return None
    return _DICKINSON.get(key)


# ── Field helpers ────────────────────────────────────────────────────────────

def _num(d: dict, *keys: str) -> float | None:
    for k in keys:
        v = d.get(k)
        if v not in (None, "None", ""):
            try:
                return float(v)
            except (ValueError, TypeError):
                pass
    return None


def _safe_div(num: float | None, denom: float | None, clamp: float = 5.0) -> float | None:
    if num is None or denom is None or denom == 0:
        return None
    return max(-clamp, min(clamp, num / denom))


def _map_row(inc: dict, bal: dict, cf: dict, ticker: str, year: int) -> dict:
    """Map one year's AV triple into canonical columns."""
    total_assets = _num(bal, "totalAssets")
    long_term_debt = _num(bal, "longTermDebt")
    total_debt = _num(bal, "shortLongTermDebtTotal", "longTermDebt")
    pp_ne = _num(bal, "propertyPlantEquipmentNet")
    total_liabilities = _num(bal, "totalLiabilities")
    cash_eq = _num(bal, "cashAndCashEquivalentsAtCarryingValue", "cashAndShortTermInvestments")

    operating_income = _num(inc, "operatingIncome", "ebit")
    net_income = _num(inc, "netIncome")
    interest_exp = _num(inc, "interestExpense")
    tax_exp = _num(inc, "incomeTaxExpense")
    ebit = _num(inc, "ebit", "operatingIncome")
    div_payout = _num(cf, "dividendPayout", "dividendPayoutCommonStock")
    debt_repay = _num(cf, "repaymentOfLongTermDebt", "proceedsFromRepaymentsOfShortTermDebt")

    ncfo = _num(cf, "operatingCashflow")
    # AV reports capex as positive; we negate for sign convention (investing outflow = negative)
    _capex = _num(cf, "capitalExpenditures")
    ncfi = -_capex if _capex is not None else None
    # Financing outflows: dividends + debt repayment (both are cash-out)
    _div = div_payout or 0.0
    _rep = debt_repay or 0.0
    ncff = -(_div + _rep)  # negative = net financing outflow

    leverage = _safe_div(long_term_debt, total_assets)
    profitability = _safe_div(operating_income, total_assets)
    tangibility = _safe_div(pp_ne, total_assets)

    # Effective tax rate clamped to [0, 1]
    eff_tax = None
    if tax_exp is not None and ebit is not None and ebit > 0:
        eff_tax = max(0.0, min(1.0, tax_exp / ebit))
    tax_col = eff_tax

    dividend_col = None
    if div_payout is not None and net_income is not None and net_income > 0:
        dividend_col = max(0.0, min(5.0, abs(div_payout) / net_income))

    interest_col = _safe_div(interest_exp, total_debt) if interest_exp is not None else None

    firm_size = math.log(total_assets) if total_assets and total_assets > 0 else None

    tax_shield = None
    if long_term_debt is not None and eff_tax is not None:
        tax_shield = long_term_debt * eff_tax

    life_stage = dickinson_stage(ncfo, ncfi, ncff)

    return {
        "company_code": TICKER_TO_CODE[ticker],
        "year": year,
        "vintage": VINTAGE,
        "life_stage": life_stage,
        "leverage": leverage,
        "profitability": profitability,
        "tangibility": tangibility,
        "tax": tax_col,
        "dividend": dividend_col,
        "interest": interest_col,
        "firm_size": firm_size,
        "log_size": firm_size,
        "ln_size": firm_size,
        "tax_shield": tax_shield,
        "borrowings": total_debt,
        "total_liabilities": total_liabilities,
        "cash_holdings": cash_eq,
        "ncfo": ncfo,
        "ncfi": ncfi,
        "ncff": ncff,
        "gfc": 1 if year in (2008, 2009) else 0,
        "ibc_2016": None,
        "covid_dummy": 1 if year in (2020, 2021) else 0,
    }


# ── Alpha Vantage API ────────────────────────────────────────────────────────

def _av_get(function: str, symbol: str, api_key: str, session: requests.Session, log: list) -> dict | None:
    url = f"{AV_BASE}?function={function}&symbol={symbol}&apikey={api_key}"
    try:
        r = session.get(url, timeout=30)
        log.append({"url": url, "status": r.status_code, "elapsed_s": round(r.elapsed.total_seconds(), 2)})
        if r.status_code == 429:
            retry = int(r.headers.get("Retry-After", 60))
            print(f"    429 rate-limit, sleeping {retry}s")
            time.sleep(retry)
            r = session.get(url, timeout=30)
            log.append({"url": url, "status": r.status_code, "retry": True})
        r.raise_for_status()
        data = r.json()
        if "Information" in data:
            print(f"    AV note: {data['Information'][:120]}")
            return None
        if "Note" in data:
            print(f"    AV note: {data['Note'][:120]}")
        return data
    except Exception as e:
        log.append({"url": url, "error": str(e)})
        print(f"    ERROR: {e}")
        return None


def fetch_ticker(ticker: str, api_key: str, session: requests.Session, log: list) -> list[dict]:
    """Fetch 3 AV endpoints for one ticker; return list of mapped canonical rows."""
    print(f"  [{ticker}] INCOME_STATEMENT", end=" ", flush=True)
    inc_data = _av_get("INCOME_STATEMENT", ticker, api_key, session, log)
    time.sleep(INTER_CALL_SLEEP)

    print(f"BALANCE_SHEET", end=" ", flush=True)
    bal_data = _av_get("BALANCE_SHEET", ticker, api_key, session, log)
    time.sleep(INTER_CALL_SLEEP)

    print(f"CASH_FLOW", end=" ", flush=True)
    cf_data = _av_get("CASH_FLOW", ticker, api_key, session, log)
    time.sleep(INTER_CALL_SLEEP)

    if not inc_data or not bal_data or not cf_data:
        print("-> SKIP (fetch failed)")
        return []

    inc_reports = {r["fiscalDateEnding"]: r for r in inc_data.get("annualReports", [])}
    bal_reports = {r["fiscalDateEnding"]: r for r in bal_data.get("annualReports", [])}
    cf_reports  = {r["fiscalDateEnding"]: r for r in cf_data.get("annualReports", [])}

    # Intersect on common fiscal-date keys
    common_dates = set(inc_reports) & set(bal_reports) & set(cf_reports)
    rows = []
    for date_str in sorted(common_dates):
        year = int(date_str[:4])
        row = _map_row(inc_reports[date_str], bal_reports[date_str], cf_reports[date_str], ticker, year)
        rows.append(row)

    print(f"-> {len(rows)} years")
    return rows


# ── DB helpers ───────────────────────────────────────────────────────────────

DB_PATH = Path(__file__).parent.parent / "capital_structure.db"


def _apply_migration(conn: sqlite3.Connection) -> None:
    cur = conn.cursor()
    for col, default in [("country", "'India'"), ("ticker", "NULL")]:
        try:
            cur.execute(f"ALTER TABLE companies ADD COLUMN {col} TEXT DEFAULT {default}")
            conn.commit()
            print(f"  [migration] added companies.{col}")
        except sqlite3.OperationalError as e:
            if "duplicate column name" in str(e).lower():
                pass  # already applied
            else:
                raise


def _upsert_company(conn: sqlite3.Connection, ticker: str, name: str, sector: str) -> None:
    code = TICKER_TO_CODE[ticker]
    cur = conn.cursor()
    cur.execute(
        """
        INSERT OR IGNORE INTO companies
            (company_code, company_name, nse_symbol, industry_group, country, ticker)
        VALUES (?, ?, ?, ?, 'USA', ?)
        """,
        [code, name, ticker, sector, ticker],
    )
    cur.execute(
        "UPDATE companies SET country='USA', ticker=? WHERE company_code=?",
        [ticker, code],
    )
    conn.commit()


def _upsert_vintage_label(conn: sqlite3.Connection, n_firms: int) -> None:
    cur = conn.cursor()
    cur.execute(
        """
        INSERT OR REPLACE INTO data_vintages (vintage, label, loaded_at, description)
        VALUES (?, ?, ?, ?)
        """,
        [
            VINTAGE,
            f"US S&P Sample (Alpha Vantage, {n_firms} firms)",
            datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "Annual financials for US blue-chip firms from Alpha Vantage free API. "
            "Canonical columns mapped; Dickinson life-stage from cash-flow signs.",
        ],
    )
    conn.commit()


def _write_rows(conn: sqlite3.Connection, ticker: str, rows: list[dict]) -> int:
    code = TICKER_TO_CODE[ticker]
    cur = conn.cursor()
    cur.execute("DELETE FROM financials WHERE company_code=? AND vintage=?", [code, VINTAGE])

    cols = [
        "company_code", "year", "vintage", "life_stage",
        "leverage", "profitability", "tangibility", "tax", "dividend",
        "interest", "firm_size", "log_size", "ln_size", "tax_shield",
        "borrowings", "total_liabilities", "cash_holdings",
        "ncfo", "ncfi", "ncff",
        "gfc", "ibc_2016", "covid_dummy",
    ]
    placeholders = ",".join("?" * len(cols))
    for row in rows:
        values = [row.get(c) for c in cols]
        cur.execute(f"INSERT INTO financials ({','.join(cols)}) VALUES ({placeholders})", values)

    conn.commit()
    return len(rows)


# ── CLI ──────────────────────────────────────────────────────────────────────

def main() -> int:
    parser = argparse.ArgumentParser(description="Load US Alpha Vantage panel into capital_structure.db")
    parser.add_argument("--api-key", default=os.environ.get("ALPHA_VANTAGE_KEY", ""), help="AV API key")
    parser.add_argument("--tickers", default="", help="Comma-separated subset of tickers (default: all 25)")
    parser.add_argument("--dry-run", action="store_true", help="Print rows but write nothing")
    args = parser.parse_args()

    if not args.api_key:
        print("ERROR: provide --api-key <KEY> or set ALPHA_VANTAGE_KEY env var", file=sys.stderr)
        return 1

    ticker_filter: set[str] | None = None
    if args.tickers:
        ticker_filter = {t.strip().upper() for t in args.tickers.split(",")}
        unknown = ticker_filter - {t for t, _, _ in US_FIRMS}
        if unknown:
            print(f"WARNING: unknown tickers (not in US_FIRMS): {unknown}")

    firms_to_load = [(t, n, s) for t, n, s in US_FIRMS if ticker_filter is None or t in ticker_filter]
    if not firms_to_load:
        print("ERROR: no matching tickers", file=sys.stderr)
        return 1

    ts = datetime.datetime.now().strftime("%Y-%m-%d_%H%M%S")
    out_dir = Path("cmie_validation") / f"us_av_{ts}"
    out_dir.mkdir(parents=True, exist_ok=True)

    print(f"[us_av] loading {len(firms_to_load)} firms -> {out_dir.as_posix()}")
    print(f"[us_av] dry_run={args.dry_run}, vintage='{VINTAGE}'")

    log: list = []
    session = requests.Session()
    all_rows: dict[str, list[dict]] = {}

    for ticker, name, sector in firms_to_load:
        rows = fetch_ticker(ticker, args.api_key, session, log)
        all_rows[ticker] = rows
        if rows:
            (out_dir / f"{ticker}.json").write_text(json.dumps(rows, indent=2), encoding="utf-8")

    if args.dry_run:
        print("\n[dry-run] sample rows (not written to DB):")
        for ticker, rows in all_rows.items():
            if rows:
                print(f"  {ticker}: {len(rows)} years, sample={json.dumps(rows[0], indent=4)[:400]}")
        (out_dir / "fetch_log.json").write_text(json.dumps(log, indent=2), encoding="utf-8")
        print(f"\n[us_av] fetch log: {(out_dir / 'fetch_log.json').as_posix()}")
        return 0

    conn = sqlite3.connect(str(DB_PATH))
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=OFF")  # US firms use codes not in original companies PK list

    try:
        _apply_migration(conn)
        total_rows = 0
        firms_loaded = 0
        for ticker, name, sector in firms_to_load:
            rows = all_rows.get(ticker, [])
            if not rows:
                print(f"  [{ticker}] skipped (no data)")
                continue
            _upsert_company(conn, ticker, name, sector)
            n = _write_rows(conn, ticker, rows)
            total_rows += n
            firms_loaded += 1
            print(f"  [{ticker}] written {n} rows")

        _upsert_vintage_label(conn, firms_loaded)
        print(f"\n[us_av] done: {firms_loaded} firms, {total_rows} rows, vintage='{VINTAGE}'")
    finally:
        conn.close()

    (out_dir / "fetch_log.json").write_text(json.dumps(log, indent=2), encoding="utf-8")
    print(f"[us_av] fetch log: {(out_dir / 'fetch_log.json').as_posix()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
