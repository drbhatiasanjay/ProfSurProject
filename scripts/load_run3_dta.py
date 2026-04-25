"""
Load `nf400yrs2001_25.dta` as `vintage='run3'` into the `financials` table.

Source: 78-column Stata panel referenced from `batch_result03/initialResults.do`
(Prof Surendra Kumar, run 25 Apr 2026). Companion to the existing `thesis`
(2001-2024) and `cmie_2025` (Mar-2025 rollforward) vintages.

Transforms applied (decided during pre-load sanity check, see chat record):
  1. leverage × 100      — .dta stores fraction (0-1.4); our DB stores percent (0-100)
  2. cls_code mapping    — .dta uses 1-8 (Dickinson with separate 7=Decline, 8=Decay);
                           thesis vintage uses 1-7 with code 7 carrying both Decline
                           and Decay distinguished by another flag. We preserve the
                           .dta's 8-code numbering verbatim and rely on the text
                           `life_stage` field for cross-vintage queries.
  3. column renames      — Stata-style → canonical (companycode→company_code, prof→
                           profitability, tang→tangibility, etc.)
  4. drops               — `_merge`, `_est_fixed`, `_est_random`, `v26`, `v27`,
                           `lifestageNdecline` (duplicate of corplifestage), and the
                           ownership / promoter / industry columns (those go to the
                           `companies` and `ownership` tables, not `financials`)

Idempotent: re-running first DELETEs existing `vintage='run3'` rows in both
`financials` and `data_vintages`.

Usage:
  py -3.12 scripts/load_run3_dta.py
"""
from __future__ import annotations

import json
import sqlite3
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

DTA_PATH = Path("nf400yrs2001_25.dta")
DB_PATH = Path("capital_structure.db")
VINTAGE = "run3"
SOURCE_FILE = "nf400yrs2001_25.dta"

# .dta `corplifestage` integer → `life_stage` text (per .dta convention)
LIFE_STAGE_MAP = {
    1: "Startup",
    2: "Growth",
    3: "Maturity",
    4: "Shakeout1",
    5: "Shakeout2",
    6: "Shakeout3",
    7: "Decline",
    8: "Decay",
}


def _str_or_none(s) -> object:
    """Coerce a value to str, but keep NaN as None for SQL NULL."""
    if pd.isna(s):
        return None
    return str(s)


def main() -> int:
    if not DTA_PATH.is_file():
        sys.exit(f"FATAL: {DTA_PATH} not found")
    if not DB_PATH.is_file():
        sys.exit(f"FATAL: {DB_PATH} not found")

    print(f"[run3] reading {DTA_PATH}")
    df = pd.read_stata(DTA_PATH, convert_categoricals=False)
    print(f"[run3] loaded {len(df):,} rows x {df.shape[1]} cols")

    # ── Build the destination frame, column by column ──────────────────────
    dest = pd.DataFrame(index=df.index)

    # Identity
    dest["company_code"] = df["companycode"].astype(int)
    dest["year"] = df["year"].astype(int)
    dest["slot_date"] = df["slotdate"].apply(_str_or_none) if "slotdate" in df else None
    dest["slot_year"] = df["slotyear"].apply(_str_or_none) if "slotyear" in df else None
    dest["age_group"] = df["agegroup"].apply(_str_or_none) if "agegroup" in df else None

    # Life-stage classification
    dest["cls_code"] = df["corplifestage"].astype(int)
    dest["life_stage"] = df["corplifestage"].astype(int).map(LIFE_STAGE_MAP)

    # Leverage — rescale fraction → percent
    dest["leverage"] = df["leverage"] * 100.0
    # `lev_pct` in existing thesis vintage = leverage * 100 (= original *10000),
    # `lev1_100` in existing thesis vintage = leverage / 100 (= original fraction).
    # Match those conventions for cross-vintage parity.
    dest["lev_pct"] = dest["leverage"] * 100.0
    dest["lev1_100"] = df["leverage"]  # original decimal form

    # Continuous fundamentals
    dest["profitability"] = df["prof"]
    dest["tangibility"] = df["tang"]
    dest["tax"] = df["tax"]
    dest["dividend"] = df["dvnd"]
    dest["interest"] = df["interest"]
    dest["firm_size"] = df["size"]
    log_size = np.log(df["size"].where(df["size"] > 0))
    dest["log_size"] = log_size
    dest["ln_size"] = log_size  # mirror thesis convention
    dest["tax_shield"] = df["taxShield"]

    # Existing thesis stores prof×100 / tang×100 — populate for cross-vintage parity
    dest["prof100"] = df["prof"] * 100.0
    dest["tang100"] = df["tang"] * 100.0

    # Balance-sheet fields
    dest["pbit"] = df["pbit"]
    dest["pbt"] = df["pbt"]
    dest["interest_amt"] = df["intamt"]
    dest["total_capital"] = df["totalcapital"]
    dest["reserves_and_funds"] = df["reservesandfunds"]
    dest["borrowings"] = df["borrowings"]
    dest["debentures_bonds"] = df["debenturesandbonds"]
    dest["total_liabilities"] = df["totalliabilities"]

    # Cash flows + Dickinson sign indicators
    dest["ncfo"] = df["ncfo"]
    dest["ncfi"] = df["ncfi"]
    dest["ncff"] = df["ncff"]
    dest["oc"] = df["oc"].astype("Int64") if "oc" in df else None
    dest["ic"] = df["ic"].astype("Int64") if "ic" in df else None
    dest["fc"] = df["fc"].astype("Int64") if "fc" in df else None

    # Event dummies
    dest["gfc"] = df["GFC"].astype(int)
    dest["ibc_2016"] = df["ibc2016"].astype(int)
    dest["covid_dummy"] = df["dcovid20less"].astype(int)

    # Vintage tags (last)
    dest["vintage"] = VINTAGE
    dest["source_file"] = SOURCE_FILE

    print(f"[run3] dest frame: {len(dest):,} rows x {dest.shape[1]} cols")

    # ── DB write ───────────────────────────────────────────────────────────
    print(f"[run3] connecting to {DB_PATH}")
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()

    # Idempotency: clear prior `run3` rows first
    cur.execute("DELETE FROM financials WHERE vintage = ?", (VINTAGE,))
    deleted = cur.rowcount
    if deleted > 0:
        print(f"[run3] deleted {deleted:,} prior rows for vintage='{VINTAGE}'")

    # Insert
    dest.to_sql("financials", con, if_exists="append", index=False)
    con.commit()
    print(f"[run3] inserted {len(dest):,} rows")

    # Register / refresh data_vintages entry
    counts = {
        "financials": int(len(dest)),
        "year_min": int(dest["year"].min()),
        "year_max": int(dest["year"].max()),
        "n_firms": int(dest["company_code"].nunique()),
        "leverage_rescaled_x100": True,
        "source_file": SOURCE_FILE,
        "stata_dta_obs": int(len(df)),
        "stata_dta_cols": int(df.shape[1]),
    }
    cur.execute("DELETE FROM data_vintages WHERE vintage = ?", (VINTAGE,))
    cur.execute(
        """INSERT INTO data_vintages
           (vintage, label, loaded_at, row_counts_json, description)
           VALUES (?, ?, ?, ?, ?)""",
        (
            VINTAGE,
            "Run 3 — Stata replication (2001-2025)",
            datetime.now(timezone.utc).isoformat(),
            json.dumps(counts),
            "Stata-replication panel from batch_result03/initialResults.do (25 Apr 2026); "
            "9,031 obs × 400 firms × 2001-2025. Excludes Gujarat State Petronet (delisted "
            "2024) and Tata Motors's old code 248093 (uses new code 729991).",
        ),
    )
    con.commit()

    # ── Post-load verification ─────────────────────────────────────────────
    print()
    print("[run3] post-load row counts by vintage:")
    for row in cur.execute(
        "SELECT vintage, COUNT(*), MIN(year), MAX(year), COUNT(DISTINCT company_code) "
        "FROM financials GROUP BY vintage ORDER BY vintage"
    ):
        v, n, ymin, ymax, nfirms = row
        print(f"  vintage={v:>15s}  rows={n:>6,}  yrs={ymin}-{ymax}  firms={nfirms}")

    print()
    print("[run3] leverage range by vintage (sanity — all should be in percent 0-200):")
    for row in cur.execute(
        "SELECT vintage, MIN(leverage), MAX(leverage), AVG(leverage), COUNT(leverage) "
        "FROM financials WHERE leverage IS NOT NULL GROUP BY vintage ORDER BY vintage"
    ):
        v, mn, mx, avg, n = row
        print(f"  vintage={v:>15s}  min={mn:>7.2f}  max={mx:>9.2f}  avg={avg:>6.2f}  n={n:,}")

    print()
    print("[run3] life_stage distribution in run3 (should match .dta tabulation):")
    for row in cur.execute(
        "SELECT life_stage, cls_code, COUNT(*) FROM financials WHERE vintage='run3' "
        "GROUP BY life_stage, cls_code ORDER BY cls_code"
    ):
        print(f"  cls_code={row[1]} life_stage={row[0]:>10s}  n={row[2]:,}")

    con.close()
    print()
    print("[run3] done")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
