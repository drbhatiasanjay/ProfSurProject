"""
DataV2 vintage loader — ingests CMIE pipe-delimited extracts into the vintage-tagged schema.

Handles the four standard CMIE tables:
  T616_identity*        — firm identity
  T617_financials*      — Standardised Annual Finance Standalone
  T618_eq_owner*        — equity ownership pattern
  T623_indexBS500closing* — market index closing series

Idempotent: re-running with the same vintage deletes prior rows for that vintage first.
Use: py -3.12 -m cmie.load_vintage ./DataV2 --vintage cmie_2025

See docs/plans/2026-04-21-datav2-vintage-ingest.md.
"""
from __future__ import annotations

import argparse
import datetime
import json
import math
import os
import re
import sqlite3
import sys
from pathlib import Path

import numpy as np
import pandas as pd


DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "capital_structure.db")

# CMIE header row positions (1-based in the files; 0-based for pandas skiprows).
# Inferred by inspecting each T-file — see docs/plans/2026-04-21-datav2-vintage-ingest.md §1.
HEADER_SKIPROWS = {
    "T616": 2,  # row 3 is column names, data starts row 4
    "T617": 4,  # rows 2-4 are metadata (User/CMIE Expr, source, units), data row 5+
    "T618": 3,  # rows 2-3 are metadata
    "T623": 3,
}

# Dickinson (2011) life-stage classification from cash-flow signs (NCFO, NCFI, NCFF).
# Matches the life_stages table seeded in load_to_db.py.
DICKINSON = {
    ("-", "-", "+"): (1, "Startup"),
    ("-", "-", "-"): (2, "Shakeout1"),
    ("+", "-", "+"): (3, "Growth"),
    ("+", "-", "-"): (4, "Maturity"),
    ("+", "+", "+"): (5, "Shakeout2"),
    ("+", "+", "-"): (6, "Shakeout3"),
    ("-", "+", "+"): (7, "Decline"),
    ("-", "+", "-"): (7, "Decay"),
}

# Known firm identity remaps (company code changes). These are one-off corrections
# applied at load time so historical and new rows join on one canonical code.
CODE_REMAPS = {
    # Tata Motors restructured post-demerger; CMIE re-issued under 729991.
    248093: {"new_code": 729991, "note": "Tata Motors demerger (2024)"},
}


def _sign(x) -> str:
    if x is None or (isinstance(x, float) and math.isnan(x)):
        return "0"
    if x > 0:
        return "+"
    if x < 0:
        return "-"
    return "0"


def dickinson_stage(ncfo, ncfi, ncff) -> tuple[int | None, str | None]:
    key = (_sign(ncfo), _sign(ncfi), _sign(ncff))
    return DICKINSON.get(key, (None, None))


def _none_if_nan(x):
    if x is None:
        return None
    try:
        if isinstance(x, float) and math.isnan(x):
            return None
    except Exception:
        pass
    return x


def _read_pipe(path: Path, skiprows: int) -> pd.DataFrame:
    return pd.read_csv(path, sep="|", skiprows=skiprows, dtype=str, keep_default_na=False, na_values=[""])


def _find_file(datadir: Path, prefix: str) -> Path:
    for p in sorted(datadir.glob(f"{prefix}*.txt")):
        return p
    raise FileNotFoundError(f"No file starting with {prefix} in {datadir}")


def _to_float_series(s: pd.Series) -> pd.Series:
    return pd.to_numeric(s, errors="coerce")


def _to_int_series(s: pd.Series) -> pd.Series:
    return pd.to_numeric(s, errors="coerce").astype("Int64")


def load_companies(conn: sqlite3.Connection, datadir: Path, vintage: str, source_files: dict) -> None:
    path = _find_file(datadir, "T616")
    source_files["T616"] = path.name
    df = _read_pipe(path, HEADER_SKIPROWS["T616"])
    df = df.rename(columns={c: c.strip() for c in df.columns})

    df["Company Code"] = _to_int_series(df["Company Code"])
    df = df.dropna(subset=["Company Code"])

    cur = conn.cursor()
    inserted = 0
    updated = 0
    for _, row in df.iterrows():
        code = int(row["Company Code"])
        name = row["Company Name"]
        nse = row.get("NSE symbol") or None
        inc = row.get("Incorporation year")
        inc_year = int(inc) if inc and str(inc).strip().isdigit() else None
        industry_group = row.get("Industry group") or None
        industry_group_code = row.get("Industry group code")
        try:
            industry_group_code = float(industry_group_code) if industry_group_code else None
        except Exception:
            industry_group_code = None
        industry_type = row.get("Industry type")
        try:
            industry_type = int(industry_type) if industry_type else None
        except Exception:
            industry_type = None

        existing = cur.execute(
            "SELECT company_code FROM companies WHERE company_code = ?", (code,)
        ).fetchone()
        if existing:
            cur.execute(
                """UPDATE companies
                   SET company_name = ?, nse_symbol = ?, inc_year = ?,
                       industry_group = ?, industry_group_code = ?, industry_type = ?
                   WHERE company_code = ?""",
                (name, nse, inc_year, industry_group, industry_group_code, industry_type, code),
            )
            updated += 1
        else:
            cur.execute(
                """INSERT INTO companies
                   (company_code, company_name, nse_symbol, inc_year,
                    industry_group, industry_group_code, industry_type)
                   VALUES (?,?,?,?,?,?,?)""",
                (code, name, nse, inc_year, industry_group, industry_group_code, industry_type),
            )
            inserted += 1

    # Apply code remaps. Mark old code superseded_by new, so joins can union both.
    for old_code, spec in CODE_REMAPS.items():
        new_code = spec["new_code"]
        new_exists = cur.execute("SELECT 1 FROM companies WHERE company_code=?", (new_code,)).fetchone()
        old_exists = cur.execute("SELECT 1 FROM companies WHERE company_code=?", (old_code,)).fetchone()
        if new_exists and old_exists:
            cur.execute(
                "UPDATE companies SET superseded_by = ? WHERE company_code = ? AND (superseded_by IS NULL OR superseded_by != ?)",
                (new_code, old_code, new_code),
            )

    # Mark companies absent from the new universe as delisted in the prior year.
    # Only tag firms that exist in DB but are not in the new T616 list AND not already
    # flagged as superseded (to avoid double-tagging Tata Motors old code).
    v2_codes = set(df["Company Code"].astype(int).tolist())
    absent = cur.execute(
        "SELECT company_code FROM companies WHERE company_code NOT IN ({}) AND delisted_in_year IS NULL AND superseded_by IS NULL".format(
            ",".join(str(c) for c in v2_codes) if v2_codes else "NULL"
        )
    ).fetchall()
    # Delisted year = max(year in existing financials for that code) — best effort.
    for (code,) in absent:
        last_yr = cur.execute(
            "SELECT MAX(year) FROM financials WHERE company_code = ?", (code,)
        ).fetchone()[0]
        if last_yr:
            cur.execute(
                "UPDATE companies SET delisted_in_year = ? WHERE company_code = ?",
                (int(last_yr), code),
            )

    conn.commit()
    print(f"  companies: +{inserted} inserted, {updated} updated, {len(absent)} flagged delisted")


def load_financials(conn: sqlite3.Connection, datadir: Path, vintage: str, source_files: dict) -> int:
    path = _find_file(datadir, "T617")
    source_files["T617"] = path.name
    df = _read_pipe(path, HEADER_SKIPROWS["T617"])
    df = df.rename(columns={c: c.strip() for c in df.columns})

    df["Company Code"] = _to_int_series(df["Company Code"])
    df["Slot Year"] = _to_int_series(df["Slot Year"])
    df = df.dropna(subset=["Company Code", "Slot Year"])

    # Slot Year is YYYYMMDD like 20250331 — derive panel year from the March close.
    df["year"] = (df["Slot Year"] // 10000).astype("Int64")

    # Age group is firm-level in T616 but stored per-year on financials by the original
    # load_to_db.py convention. Read T616 and build a code→age_group map.
    t616 = _read_pipe(_find_file(datadir, "T616"), HEADER_SKIPROWS["T616"])
    t616 = t616.rename(columns={c: c.strip() for c in t616.columns})
    t616["Company Code"] = _to_int_series(t616["Company Code"])
    age_map = dict(zip(t616["Company Code"].dropna().astype(int), t616["Age group"]))

    num_cols = [
        "prof", "tang", "tax", "dvnd", "interest", "size",
        "PBIT", "PBT", "Intamt", "Total capital", "Reserves and funds",
        "Borrowings", "Debentures and bonds", "Total liabilities",
        "ncfo", "ncfi", "ncff",
        "Debt to equity ratio (times)", "Total outside liabilities", "Short-term borrowings",
    ]
    for c in num_cols:
        if c in df.columns:
            df[c] = _to_float_series(df[c])

    cur = conn.cursor()
    # Idempotency: clear any prior rows for this vintage before insert.
    cur.execute("DELETE FROM financials WHERE vintage = ?", (vintage,))

    # Apply code remaps before insert (Tata Motors new code → old canonical, or just tag both).
    # Design: keep the new code; superseded_by already links old→new for historical unions.
    insert_sql = """
        INSERT INTO financials (
            company_code, year, slot_date, slot_year, age_group, cls_code, life_stage,
            leverage, lev_pct, profitability, tangibility, tax, dividend, interest,
            firm_size, log_size, ln_size, tax_shield,
            pbit, pbt, interest_amt, total_capital, reserves_and_funds,
            borrowings, debentures_bonds, total_liabilities,
            ncfo, ncfi, ncff, net_cash_flow, ncf_dummy,
            oc, ic, fc, gfc, ibc_2016, ibc_2016_20, covid_dummy,
            vintage, source_file
        ) VALUES (?,?,?,?,?,?,?, ?,?,?,?,?,?,?, ?,?,?,?, ?,?,?,?,?, ?,?,?, ?,?,?,?,?, ?,?,?,?,?,?,?, ?,?)
    """

    inserted = 0
    for _, row in df.iterrows():
        code = int(row["Company Code"])
        year = int(row["year"])
        slot_date = row.get("Slot Date")
        slot_year = str(int(row["Slot Year"]))

        age_group = age_map.get(code)

        ncfo = _none_if_nan(row.get("ncfo"))
        ncfi = _none_if_nan(row.get("ncfi"))
        ncff = _none_if_nan(row.get("ncff"))
        cls_code, life_stage = dickinson_stage(ncfo, ncfi, ncff)

        size = _none_if_nan(row.get("size"))
        ln_size = math.log(size) if size and size > 0 else None
        log_size = math.log10(size) if size and size > 0 else None

        # Leverage from CMIE D/E ratio (times). Keep on same scale as the thesis column.
        leverage = _none_if_nan(row.get("Debt to equity ratio (times)"))
        lev_pct = (leverage * 100) if leverage is not None else None

        pbit = _none_if_nan(row.get("PBIT"))
        # Tax shield in the thesis column is a depreciation/PBIT-ish ratio; not in T617.
        # Leave NULL for 2025 rows; econometrics pages default to thesis vintage anyway.
        tax_shield = None

        ncf_dummy = 1 if any(x is not None and x < 0 for x in (ncfo, ncfi, ncff)) else 0
        oc = 1 if _sign(ncfo) == "+" else 0
        ic = 1 if _sign(ncfi) == "+" else 0
        fc = 1 if _sign(ncff) == "+" else 0

        # Event dummies — static based on calendar year.
        gfc = 1 if year in (2008, 2009) else 0
        ibc_2016 = 1 if year >= 2016 else 0
        ibc_2016_20 = 1 if 2016 <= year <= 2020 else 0
        covid_dummy = 1 if year in (2020, 2021) else 0

        net_cash_flow = None
        try:
            parts = [v for v in (ncfo, ncfi, ncff) if v is not None]
            if parts:
                net_cash_flow = float(sum(parts))
        except Exception:
            net_cash_flow = None

        cur.execute(
            insert_sql,
            (
                code, year, slot_date, slot_year, age_group, cls_code, life_stage,
                leverage, lev_pct,
                _none_if_nan(row.get("prof")), _none_if_nan(row.get("tang")),
                _none_if_nan(row.get("tax")), _none_if_nan(row.get("dvnd")),
                _none_if_nan(row.get("interest")),
                size, log_size, ln_size, tax_shield,
                pbit, _none_if_nan(row.get("PBT")), _none_if_nan(row.get("Intamt")),
                _none_if_nan(row.get("Total capital")), _none_if_nan(row.get("Reserves and funds")),
                _none_if_nan(row.get("Borrowings")), _none_if_nan(row.get("Debentures and bonds")),
                _none_if_nan(row.get("Total liabilities")),
                ncfo, ncfi, ncff, net_cash_flow, ncf_dummy,
                oc, ic, fc, gfc, ibc_2016, ibc_2016_20, covid_dummy,
                vintage, source_files["T617"],
            ),
        )
        inserted += 1

    conn.commit()
    print(f"  financials: +{inserted} rows (vintage={vintage})")
    return inserted


def load_ownership(conn: sqlite3.Connection, datadir: Path, vintage: str, source_files: dict) -> int:
    path = _find_file(datadir, "T618")
    source_files["T618"] = path.name
    df = _read_pipe(path, HEADER_SKIPROWS["T618"])
    df = df.rename(columns={c: c.strip() for c in df.columns})
    df["Company Code"] = _to_int_series(df["Company Code"])
    df = df.dropna(subset=["Company Code"])

    cur = conn.cursor()
    cur.execute("DELETE FROM ownership WHERE vintage = ?", (vintage,))

    def g(row, key):
        return _none_if_nan(_to_float_series(pd.Series([row.get(key)]))[0])

    inserted = 0
    for _, row in df.iterrows():
        code = int(row["Company Code"])
        # Derive year from Slot Date "Mar 2025"
        slot_date = row.get("Slot Date", "") or ""
        m = re.match(r"\s*\w+\s+(\d{4})", slot_date)
        year = int(m.group(1)) if m else None
        if year is None:
            continue

        cur.execute(
            """INSERT INTO ownership (
                company_code, year,
                promoter_share, indian_promoters, foreign_promoters, promoters_pledged,
                non_promoters, non_promoter_institutions, non_promoter_mutual_funds,
                non_promoter_banks_fis, non_promoter_fin_institutions, non_promoter_insurance,
                non_promoter_fiis, non_promoter_non_institutions, non_promoter_corporate_bodies,
                non_promoter_individuals, total_share, total_shares_pledged,
                venture_capital, foreign_vc, qfi, custodians,
                non_promoter_individuals_small, non_promoter_individuals_large,
                vintage, source_file
            ) VALUES (?,?, ?,?,?,?, ?,?,?, ?,?,?, ?,?,?, ?,?,?, ?,?,?,?, ?,?, ?,?)""",
            (
                code, year,
                g(row, "Promoters (In %) - Shares held"),
                g(row, "Indian Promoters (In %) - Shares held"),
                g(row, "Foreign Promoters (In %) - Shares held"),
                g(row, "Promoters (In %) - Pledged Shares"),
                g(row, "Non-promoters (In %) - Shares held"),
                g(row, "Non-promoter Institutions (In %) - Shares held"),
                g(row, "Non-promoter Mutual  Funds/ UTI (In %) - Shares held"),
                g(row, "Non-promoter Banks, FI's, Insurance Cos. (In %) - Shares held"),
                g(row, "Non-promoter Financial Institutions & Banks (In %) - Shares held"),
                g(row, "Non-promoter Insurance Companies (In %) - Shares held"),
                g(row, "Non-promoter FIIs (In %) - Shares held"),
                g(row, "Non-promoter Non-institutions (In %) - Shares held"),
                g(row, "Non-promoter Corporate Bodies (In %) - Shares held"),
                g(row, "Non-promoter Individuals (In %) - Shares held"),
                None,  # total_share (not in T618)
                None,  # total_shares_pledged
                g(row, "Non-promoter Venture  Capital Funds (In %) - Shares held"),
                g(row, "Non-promoter Foreign Venture Capital (In %) - Shares held"),
                g(row, "Non-promoter Qualified Foreign Investor - Institutions (In %) - Shares held"),
                g(row, "Shares  held  by Custodians (In %) - Shares held"),
                g(row, "Non-promoter Investors holding nominal invest. upto Rs 1 lakh (In %) - Shares held"),
                g(row, "Non-promoter Investors holding nominal invest. over Rs 1 lakh (In %) - Shares held"),
                vintage, source_files["T618"],
            ),
        )
        inserted += 1

    conn.commit()
    print(f"  ownership: +{inserted} rows (vintage={vintage})")
    return inserted


def load_market_indices(conn: sqlite3.Connection, datadir: Path, vintage: str, source_files: dict) -> int:
    path = _find_file(datadir, "T623")
    source_files["T623"] = path.name
    df = _read_pipe(path, HEADER_SKIPROWS["T623"])
    df = df.rename(columns={c: c.strip() for c in df.columns})

    df["Index Code"] = _to_int_series(df["Index Code"])
    df = df.dropna(subset=["Index Code"])
    df["Index Closing"] = _to_float_series(df["Index Closing"])

    # Slot Date "Mar 2025" → year 2025
    def year_from_slot(s):
        m = re.match(r"\s*\w+\s+(\d{4})", str(s) or "")
        return int(m.group(1)) if m else None

    df["year"] = df["Slot Date"].apply(year_from_slot)
    df = df.dropna(subset=["year"])
    df["year"] = df["year"].astype(int)

    cur = conn.cursor()
    cur.execute("DELETE FROM market_index_series WHERE vintage = ?", (vintage,))

    # Upsert on (index_code, year) primary key
    rows = [
        (
            int(r["Index Code"]),
            r["Index Name"],
            int(r["year"]),
            r.get("Slot Date"),
            r.get("Index Date"),
            _none_if_nan(r.get("Index Closing")),
            vintage,
            source_files["T623"],
        )
        for _, r in df.iterrows()
    ]
    cur.executemany(
        """INSERT OR REPLACE INTO market_index_series
           (index_code, index_name, year, slot_date, index_date, index_closing, vintage, source_file)
           VALUES (?,?,?,?,?,?,?,?)""",
        rows,
    )
    conn.commit()

    n_series = cur.execute("SELECT COUNT(DISTINCT index_code) FROM market_index_series").fetchone()[0]
    n_rows = cur.execute("SELECT COUNT(*) FROM market_index_series").fetchone()[0]
    print(f"  market_index_series: {n_rows} total rows across {n_series} series")
    return len(rows)


def update_vintage_metadata(conn: sqlite3.Connection, vintage: str, counts: dict, source_files: dict) -> None:
    now = datetime.datetime.now(datetime.timezone.utc).isoformat()
    label = {"cmie_2025": "CMIE 2025"}.get(vintage, vintage)
    conn.execute(
        """INSERT INTO data_vintages (vintage, label, loaded_at, row_counts_json, description)
           VALUES (?,?,?,?,?)
           ON CONFLICT(vintage) DO UPDATE SET
             loaded_at = excluded.loaded_at,
             row_counts_json = excluded.row_counts_json,
             label = COALESCE(data_vintages.label, excluded.label)""",
        (
            vintage,
            label,
            now,
            json.dumps({**counts, "source_files": source_files}),
            f"Loaded by cmie.load_vintage at {now}",
        ),
    )
    conn.commit()


def run(datadir: str, vintage: str) -> None:
    datadir_p = Path(datadir).resolve()
    if not datadir_p.exists():
        raise SystemExit(f"Data directory not found: {datadir_p}")

    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys=ON")
    source_files: dict[str, str] = {}
    try:
        print(f"Loading vintage '{vintage}' from {datadir_p}")
        load_companies(conn, datadir_p, vintage, source_files)
        n_fin = load_financials(conn, datadir_p, vintage, source_files)
        n_own = load_ownership(conn, datadir_p, vintage, source_files)
        n_idx = load_market_indices(conn, datadir_p, vintage, source_files)

        update_vintage_metadata(
            conn,
            vintage,
            {"financials": n_fin, "ownership": n_own, "market_index_series": n_idx},
            source_files,
        )
        print("Done.")
    finally:
        conn.close()


def main(argv: list[str] | None = None) -> None:
    p = argparse.ArgumentParser(description="Load a CMIE DataV_ directory into the vintage-tagged schema.")
    p.add_argument("datadir", help="Path to DataV2/ (or DataV3/, etc.)")
    p.add_argument("--vintage", required=True, help="Vintage tag, e.g. cmie_2025")
    args = p.parse_args(argv)
    run(args.datadir, args.vintage)


if __name__ == "__main__":
    main()
