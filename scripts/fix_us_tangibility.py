"""
One-shot fix: fill NULL tangibility values for vintage='us_av_2024' rows.

Strategy:
- Compute industry-mean tangibility from non-null us_av_2024 rows
  (JOIN financials -> companies on company_code, GROUP BY industry_group)
- For each NULL row, set tangibility = industry mean for that firm's industry_group
- Fallback: if industry has no non-null peers in us_av_2024, use global us_av_2024 mean
  (e.g. Chevron, industry_group='Energy', company_code=9000019 — no Energy peers with
   non-null tangibility in us_av_2024, so falls back to global mean ~0.1719)
- Also recompute derived columns:
    tang100  = tangibility * 100
    log_tang = ln(tangibility)  where tangibility > 0, else NULL

Idempotent: WHERE tangibility IS NULL guard means re-running is safe.

Usage:
    py -3.12 scripts/fix_us_tangibility.py
    py -3.12 scripts/fix_us_tangibility.py --db path/to/other.db
    py -3.12 scripts/fix_us_tangibility.py --dry-run
"""
import argparse
import math
import sqlite3


def main() -> None:
    parser = argparse.ArgumentParser(description="Fill NULL tangibility for us_av_2024 vintage")
    parser.add_argument("--dry-run", action="store_true", help="Print what would be done but don't write")
    parser.add_argument("--db", default="capital_structure.db", help="Path to SQLite database")
    args = parser.parse_args()

    conn = sqlite3.connect(args.db)

    # Industry-level means from non-null us_av_2024 rows
    industry_avg: dict[str, float] = dict(
        conn.execute(
            """
            SELECT c.industry_group, AVG(f.tangibility)
            FROM financials f
            JOIN companies c ON c.company_code = f.company_code
            WHERE f.vintage = 'us_av_2024'
              AND f.tangibility IS NOT NULL
            GROUP BY c.industry_group
            """
        ).fetchall()
    )

    # Global fallback (used when an industry has no non-null us_av_2024 peers)
    global_avg: float = conn.execute(
        "SELECT AVG(tangibility) FROM financials WHERE vintage = 'us_av_2024' AND tangibility IS NOT NULL"
    ).fetchone()[0]

    print(f"Global us_av_2024 tangibility mean: {global_avg:.4f}")
    print(f"Industry averages ({len(industry_avg)} groups): {industry_avg}")

    # Distinct firms with NULL tangibility in us_av_2024
    null_firms = conn.execute(
        """
        SELECT DISTINCT f.company_code, c.industry_group
        FROM financials f
        JOIN companies c ON c.company_code = f.company_code
        WHERE f.vintage = 'us_av_2024'
          AND f.tangibility IS NULL
        """
    ).fetchall()

    if not null_firms:
        print("No NULL rows found — nothing to do.")
        conn.close()
        return

    print(f"\nFirms to fix: {len(null_firms)}")
    total_rows_updated = 0

    for company_code, industry_group in null_firms:
        fill_value: float = industry_avg.get(industry_group, global_avg)
        tang100: float | None = fill_value * 100 if fill_value is not None else None
        log_tang: float | None = math.log(fill_value) if (fill_value is not None and fill_value > 0) else None

        fallback_note = "" if industry_group in industry_avg else " [FALLBACK: global mean]"
        dry_note = " [DRY RUN]" if args.dry_run else ""
        log_tang_str = f"{log_tang:.4f}" if log_tang is not None else "NULL"
        print(
            f"  [{company_code}] industry={industry_group!r} "
            f"fill={fill_value:.4f} tang100={tang100:.2f} log_tang={log_tang_str}"
            f"{fallback_note}{dry_note}"
        )

        if not args.dry_run:
            cursor = conn.execute(
                """
                UPDATE financials
                SET tangibility = ?,
                    tang100     = ?,
                    log_tang    = ?
                WHERE company_code = ?
                  AND vintage       = 'us_av_2024'
                  AND tangibility   IS NULL
                """,
                (fill_value, tang100, log_tang, company_code),
            )
            total_rows_updated += cursor.rowcount

    if args.dry_run:
        print("\n[DRY RUN] No changes written.")
        conn.close()
        return

    conn.commit()

    remaining: int = conn.execute(
        "SELECT COUNT(*) FROM financials WHERE vintage = 'us_av_2024' AND tangibility IS NULL"
    ).fetchone()[0]

    print(f"\nRows updated: {total_rows_updated}")
    print(f"NULL tangibility remaining: {remaining}")

    if remaining != 0:
        conn.close()
        raise AssertionError(f"Still {remaining} NULL rows after fix!")

    print("PASS: all NULL tangibility rows filled for us_av_2024 vintage")
    conn.close()


if __name__ == "__main__":
    main()
