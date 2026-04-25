"""
One-shot fix for cmie_2025 vintage leverage scale.

Discovered post-load (see chat record 2026-04-25): the DataV2 loader at
cmie/load_vintage.py:263-264 stored leverage as a DECIMAL (e.g. 0.5 = D/E
ratio of 0.5 times) instead of as a PERCENT like the thesis vintage
(e.g. 50.0 = 50%). It also left lev1_100, prof100, tang100 as NULL.

Net effect on the dashboard's Latest panel: 2025 leverage values appeared
~100x smaller than 2001-2024 values for the same firm, breaking visual
comparability and any cross-vintage averages.

This script applies the missing transforms in a single transaction:

  Before                    After
  ---------------------     -----------------------
  leverage     = D/E (dec)  → lev1_100 (decimal)
  lev_pct      = leverage*100 (still small)  → leverage (percent)
  lev_pct = leverage_pct * 100  (matches thesis quirk)
  prof100 = profitability * 100
  tang100 = tangibility * 100

Idempotency: re-running re-applies the transforms only if leverage is still
in the ~0-10 range (heuristic). After the first successful run, leverage
will be in the ~0-1000 range and the script will refuse to re-rescale.

Companion patch in cmie/load_vintage.py ensures future DataV2 reloads write
percent directly, so this script never needs to be re-run.
"""
from __future__ import annotations

import sqlite3
import sys
from pathlib import Path

DB_PATH = Path("capital_structure.db")
VINTAGE = "cmie_2025"


def main() -> int:
    if not DB_PATH.is_file():
        sys.exit(f"FATAL: {DB_PATH} not found")

    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()

    # Snapshot pre-state
    pre = cur.execute(
        "SELECT MIN(leverage), MAX(leverage), AVG(leverage), COUNT(leverage), "
        "MIN(lev_pct), MAX(lev_pct), COUNT(lev1_100), COUNT(prof100), COUNT(tang100) "
        "FROM financials WHERE vintage = ?",
        (VINTAGE,),
    ).fetchone()
    print(f"[fix] vintage='{VINTAGE}' BEFORE:")
    print(f"  leverage : min={pre[0]:.4f}  max={pre[1]:.4f}  avg={pre[2]:.4f}  n={pre[3]}")
    print(f"  lev_pct  : min={pre[4]:.4f}  max={pre[5]:.4f}")
    print(f"  lev1_100 non-NULL count: {pre[6]}")
    print(f"  prof100  non-NULL count: {pre[7]}")
    print(f"  tang100  non-NULL count: {pre[8]}")

    # Idempotency guard: if max leverage is already > 100 the rescale was applied
    if pre[1] is not None and pre[1] > 100:
        print(f"[fix] leverage max {pre[1]:.2f} suggests rescale already applied; aborting.")
        con.close()
        return 0

    # Apply the transforms in a single transaction
    cur.execute(
        """UPDATE financials SET
             lev1_100 = leverage,
             leverage = lev_pct,
             lev_pct  = lev_pct * 100,
             prof100  = profitability * 100,
             tang100  = tangibility * 100
           WHERE vintage = ?""",
        (VINTAGE,),
    )
    n = cur.rowcount
    con.commit()
    print(f"[fix] UPDATE applied to {n} rows in vintage='{VINTAGE}'")

    # Verify
    post = cur.execute(
        "SELECT MIN(leverage), MAX(leverage), AVG(leverage), COUNT(leverage), "
        "MIN(lev_pct), MAX(lev_pct), COUNT(lev1_100), COUNT(prof100), COUNT(tang100) "
        "FROM financials WHERE vintage = ?",
        (VINTAGE,),
    ).fetchone()
    print(f"[fix] vintage='{VINTAGE}' AFTER:")
    print(f"  leverage : min={post[0]:.4f}  max={post[1]:.4f}  avg={post[2]:.4f}  n={post[3]}")
    print(f"  lev_pct  : min={post[4]:.4f}  max={post[5]:.4f}")
    print(f"  lev1_100 non-NULL count: {post[6]}")
    print(f"  prof100  non-NULL count: {post[7]}")
    print(f"  tang100  non-NULL count: {post[8]}")

    # Cross-vintage sanity
    print()
    print("[fix] cross-vintage leverage sanity (should all be in percent now):")
    for row in cur.execute(
        "SELECT vintage, MIN(leverage), MAX(leverage), AVG(leverage) "
        "FROM financials WHERE leverage IS NOT NULL GROUP BY vintage ORDER BY vintage"
    ):
        print(f"  vintage={row[0]:>15s}  min={row[1]:>7.2f}  max={row[2]:>9.2f}  avg={row[3]:>6.2f}")

    con.close()
    print()
    print("[fix] done")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
