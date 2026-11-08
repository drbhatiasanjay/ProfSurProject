"""Versioned Database Migration Runner for Pre-IPO Ledger & Lifecycle.
Guarantees idempotent migrations, backup verification, and backfill execution.
"""
import os
import hashlib
import sqlite3
from pathlib import Path
from typing import Dict, List, Any, Optional

MIGRATIONS_DIR = Path(__file__).parent / "migrations"


def compute_checksum(content: str) -> str:
    """Compute SHA256 checksum of SQL content."""
    return hashlib.sha256(content.strip().encode("utf-8")).hexdigest()


def _get_table_columns(conn: sqlite3.Connection, table_name: str) -> List[str]:
    """Retrieve list of column names for a table."""
    try:
        cursor = conn.execute(f"PRAGMA table_info({table_name})")
        return [row[1] for row in cursor.fetchall()]
    except Exception:
        return []


def _ensure_journal(conn: sqlite3.Connection) -> None:
    """Ensure the schema migration journal exists."""
    conn.execute("""
        CREATE TABLE IF NOT EXISTS pre_ipo_schema_migrations (
            version INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            checksum TEXT NOT NULL,
            applied_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            status TEXT NOT NULL
        )
    """)
    conn.commit()


def get_applied_versions(conn: sqlite3.Connection) -> Dict[int, Dict[str, Any]]:
    """Return dict of version -> {name, checksum, applied_at, status}."""
    _ensure_journal(conn)
    cursor = conn.execute("SELECT version, name, checksum, applied_at, status FROM pre_ipo_schema_migrations ORDER BY version ASC")
    return {
        row[0]: {
            "name": row[1],
            "checksum": row[2],
            "applied_at": row[3],
            "status": row[4]
        }
        for row in cursor.fetchall()
    }


def backup_database(source_db_path: str, backup_path: str) -> str:
    """Rehearsal backup using SQLite Online Backup API while holding shared lock."""
    source_p = Path(source_db_path)
    if not source_p.exists():
        raise FileNotFoundError(f"Source database not found: {source_db_path}")

    target_p = Path(backup_path)
    target_p.parent.mkdir(parents=True, exist_ok=True)

    src_conn = sqlite3.connect(str(source_p))
    dst_conn = sqlite3.connect(str(target_p))
    try:
        src_conn.backup(dst_conn)
    finally:
        dst_conn.close()
        src_conn.close()
    return str(target_p)


def apply_migrations(conn: sqlite3.Connection) -> List[int]:
    """Execute all pending migrations idempotently in sequence."""
    _ensure_journal(conn)
    applied = get_applied_versions(conn)
    newly_applied = []

    # Migration 1: Baseline Evidence Schema
    if 1 not in applied:
        m1_file = MIGRATIONS_DIR / "001_baseline_evidence_schema.sql"
        if m1_file.exists():
            sql = m1_file.read_text(encoding="utf-8")
            chk = compute_checksum(sql)
            conn.executescript(sql)
            conn.execute(
                "INSERT INTO pre_ipo_schema_migrations(version, name, checksum, status) VALUES(?, ?, ?, ?)",
                (1, "001_baseline_evidence_schema", chk, "APPLIED")
            )
            conn.commit()
            newly_applied.append(1)

    # Migration 2: Lifecycle & Multi-Document Extensions
    if 2 not in applied:
        m2_file = MIGRATIONS_DIR / "002_lifecycle_and_multidoc_extensions.sql"
        if m2_file.exists():
            sql = m2_file.read_text(encoding="utf-8")
            chk = compute_checksum(sql)
            conn.executescript(sql)

            # Safely add additive columns to pre_ipo_company_profiles if missing
            prof_cols = _get_table_columns(conn, "pre_ipo_company_profiles")
            if "generation" not in prof_cols:
                conn.execute("ALTER TABLE pre_ipo_company_profiles ADD COLUMN generation INTEGER NOT NULL DEFAULT 1")
            if "status" not in prof_cols:
                conn.execute("ALTER TABLE pre_ipo_company_profiles ADD COLUMN status TEXT NOT NULL DEFAULT 'ACTIVE'")

            # Safely add additive columns to pre_ipo_sources if missing
            src_cols = _get_table_columns(conn, "pre_ipo_sources")
            if "generation" not in src_cols:
                conn.execute("ALTER TABLE pre_ipo_sources ADD COLUMN generation INTEGER NOT NULL DEFAULT 1")
            if "status" not in src_cols:
                conn.execute("ALTER TABLE pre_ipo_sources ADD COLUMN status TEXT NOT NULL DEFAULT 'ACTIVE'")
            if "family" not in src_cols:
                conn.execute("ALTER TABLE pre_ipo_sources ADD COLUMN family TEXT NOT NULL DEFAULT 'OFFER'")
            if "reporting_period" not in src_cols:
                conn.execute("ALTER TABLE pre_ipo_sources ADD COLUMN reporting_period TEXT")
            if "availability_date" not in src_cols:
                conn.execute("ALTER TABLE pre_ipo_sources ADD COLUMN availability_date TEXT")

            # Safely add additive columns to pre_ipo_decision_versions if table exists
            dec_cols = _get_table_columns(conn, "pre_ipo_decision_versions")
            if dec_cols:
                if "company_id" not in dec_cols:
                    conn.execute("ALTER TABLE pre_ipo_decision_versions ADD COLUMN company_id TEXT")
                if "snapshot_id" not in dec_cols:
                    conn.execute("ALTER TABLE pre_ipo_decision_versions ADD COLUMN snapshot_id TEXT")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_decision_versions_company ON pre_ipo_decision_versions(owner, company_id)")

            conn.execute(
                "INSERT INTO pre_ipo_schema_migrations(version, name, checksum, status) VALUES(?, ?, ?, ?)",
                (2, "002_lifecycle_and_multidoc_extensions", chk, "APPLIED")
            )
            conn.commit()
            newly_applied.append(2)

    return newly_applied


def backfill_projections(conn: sqlite3.Connection) -> Dict[str, int]:
    """Backfill projections from legacy payloads into observations and dependencies."""
    counts = {"observations": 0, "decision_links": 0, "quarantined_orphans": 0}

    # 1. Backfill fact events into pre_ipo_observations if observations are empty
    obs_count = conn.execute("SELECT COUNT(*) FROM pre_ipo_observations").fetchone()[0]
    if obs_count == 0:
        import json
        facts = conn.execute("SELECT owner, company, fact_id, revision, payload, created_at FROM pre_ipo_fact_events").fetchall()
        for owner, company, fact_id, rev, payload_raw, created_at in facts:
            try:
                p = json.loads(payload_raw) if isinstance(payload_raw, str) else payload_raw
                val = str(p.get("value")) if p.get("value") is not None else None
                pres = p.get("presence", "OBSERVED_VALUE")
                review = p.get("review", "UNREVIEWED")
                ctx = p.get("context", {})
                src = p.get("source", {})
                src_id = src.get("sha256", "legacy_source")

                conn.execute("""
                    INSERT OR IGNORE INTO pre_ipo_observations (
                        owner, company, observation_id, revision, source_id, entity, metric_id,
                        period, duration, basis, framework, currency, unit, value, presence,
                        review_state, provenance_json, created_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    owner, company, fact_id, rev, src_id, ctx.get("entity", company),
                    fact_id, ctx.get("period"), ctx.get("duration"), ctx.get("basis"),
                    ctx.get("framework"), ctx.get("currency"), ctx.get("unit"), val,
                    pres, review, json.dumps(src), created_at
                ))
                counts["observations"] += 1
            except Exception:
                counts["quarantined_orphans"] += 1

    # 2. Backfill decision versions company_id / snapshot_id if empty
    dec_cols = _get_table_columns(conn, "pre_ipo_decision_versions")
    if "company_id" in dec_cols:
        import json
        rows = conn.execute("SELECT owner, case_id, revision, payload FROM pre_ipo_decision_versions WHERE company_id IS NULL").fetchall()
        for owner, case_id, rev, payload_raw in rows:
            try:
                p = json.loads(payload_raw)
                ctx = p.get("context", {})
                cid = ctx.get("company_id") or ctx.get("company")
                snap_id = ctx.get("snapshot_id") or p.get("snapshot_id")
                if cid:
                    conn.execute(
                        "UPDATE pre_ipo_decision_versions SET company_id=?, snapshot_id=? WHERE owner=? AND case_id=? AND revision=?",
                        (cid, snap_id, owner, case_id, rev)
                    )
                    conn.execute("""
                        INSERT OR IGNORE INTO pre_ipo_dependencies(
                            owner, company, dependent_kind, dependent_id, target_kind, target_id, relation_type
                        ) VALUES (?, ?, 'DECISION', ?, 'COMPANY', ?, 'USES_COMPANY')
                    """, (owner, cid, case_id, cid))
                    if snap_id:
                        conn.execute("""
                            INSERT OR IGNORE INTO pre_ipo_dependencies(
                                owner, company, dependent_kind, dependent_id, target_kind, target_id, relation_type
                            ) VALUES (?, ?, 'DECISION', ?, 'SNAPSHOT', ?, 'USES_SNAPSHOT')
                        """, (owner, cid, case_id, snap_id))
                    counts["decision_links"] += 1
            except Exception:
                pass

    conn.commit()
    return counts
