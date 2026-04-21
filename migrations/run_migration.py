"""
Idempotent SQLite migration runner for ProfSurProject.

Usage:
    py -3.12 migrations/run_migration.py migrations/001_datav2_vintage.sql

SQLite's ALTER TABLE ADD COLUMN is not idempotent, so this runner splits the
file into statements and skips "duplicate column" errors. Other statement
errors abort and roll back.
"""
import os
import re
import sys
import sqlite3

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "capital_structure.db")


def split_statements(sql_text: str) -> list[str]:
    # Strip -- line comments, preserve strings
    cleaned_lines = []
    for line in sql_text.splitlines():
        if "--" in line:
            line = line[: line.index("--")]
        cleaned_lines.append(line)
    cleaned = "\n".join(cleaned_lines)

    # SQLite doesn't support BEGIN/COMMIT inside executescript reliably when we
    # want per-statement error handling, so we drive statements ourselves.
    statements = [s.strip() for s in re.split(r";\s*(?:\n|$)", cleaned) if s.strip()]
    return statements


def apply_migration(sql_path: str) -> None:
    with open(sql_path, "r", encoding="utf-8") as f:
        sql_text = f.read()

    statements = split_statements(sql_text)
    conn = sqlite3.connect(DB_PATH)
    conn.isolation_level = None  # we manage transactions manually

    applied = 0
    skipped = 0
    try:
        conn.execute("BEGIN")
        for stmt in statements:
            upper = stmt.upper().strip()
            if upper in ("BEGIN", "COMMIT"):
                continue
            try:
                conn.execute(stmt)
                applied += 1
            except sqlite3.OperationalError as e:
                msg = str(e).lower()
                # Idempotency: these errors mean "already applied"
                if "duplicate column" in msg or "already exists" in msg:
                    skipped += 1
                    continue
                conn.execute("ROLLBACK")
                print(f"ERROR on statement:\n{stmt[:200]}...\n-> {e}", file=sys.stderr)
                raise
        conn.execute("COMMIT")
    finally:
        conn.close()

    print(f"Migration applied: {sql_path}")
    print(f"  statements executed: {applied}")
    print(f"  statements skipped (already applied): {skipped}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("usage: run_migration.py <path-to-sql>", file=sys.stderr)
        sys.exit(2)
    apply_migration(sys.argv[1])
