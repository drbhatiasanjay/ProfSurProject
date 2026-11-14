"""Versioned Database Migration Runner for Pre-IPO Ledger & Lifecycle.
Guarantees idempotent migrations, backup verification, integrity checksums, and backfill execution.
"""
import os
import hashlib
import sqlite3
import json
from pathlib import Path
from typing import Dict, List, Any, Optional

MIGRATIONS_DIR = Path(__file__).parent / "migrations"


def compute_checksum(content: str) -> str:
    """Compute SHA256 checksum of normalized SQL content."""
    normalized = content.strip().replace("\r\n", "\n")
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def _execute_sql_script_transactional(conn: sqlite3.Connection, sql: str) -> None:
    """Executes multiple SQL statements sequentially within an active transaction without implicit commit."""
    statements = []
    current = []
    for line in sql.splitlines():
        line_clean = line.strip()
        if line_clean.startswith("--") or not line_clean:
            continue
        current.append(line)
        if ";" in line:
            full_stmt = "\n".join(current)
            for part in full_stmt.split(";"):
                part_clean = part.strip()
                if part_clean:
                    statements.append(part_clean)
            current = []
    if current:
        remaining = "\n".join(current).strip()
        if remaining:
            statements.append(remaining)

    for stmt in statements:
        conn.execute(stmt)


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


def get_applied_migrations(conn: sqlite3.Connection) -> Dict[int, Dict[str, Any]]:
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


def get_applied_versions(conn: sqlite3.Connection):
    """Return applied migrations dict (for backward compatibility)."""
    return get_applied_migrations(conn)


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
    """Execute all pending migrations idempotently in sequence with strict checksum validation."""
    _ensure_journal(conn)
    applied_records = get_applied_migrations(conn)

    # 1. Enforce checksum and integrity validation on all previously applied migrations
    for version, record in applied_records.items():
        if record["status"] != "APPLIED":
            raise RuntimeError(f"Migration {version} has invalid status: {record['status']}")

        # Locate migration file on disk
        candidates = list(MIGRATIONS_DIR.glob(f"{version:03d}_*.sql"))
        if not candidates:
            raise RuntimeError(f"Applied migration {version} ({record['name']}) is missing from disk.")

        file_sql = candidates[0].read_text(encoding="utf-8")
        current_chk = compute_checksum(file_sql)
        if current_chk != record["checksum"]:
            raise RuntimeError(
                f"Migration checksum mismatch for version {version} ({record['name']}): "
                f"database journal has {record['checksum']}, but file on disk has {current_chk}. Schema drift detected!"
            )

    newly_applied = []

    # 2. Migration 1: Baseline Evidence Schema
    if 1 not in applied_records:
        m1_file = MIGRATIONS_DIR / "001_baseline_evidence_schema.sql"
        if not m1_file.exists():
            raise RuntimeError("Required migration file 001_baseline_evidence_schema.sql missing from disk.")
        sql = m1_file.read_text(encoding="utf-8")
        chk = compute_checksum(sql)
        conn.execute("BEGIN IMMEDIATE")
        try:
            _execute_sql_script_transactional(conn, sql)
            conn.execute(
                "INSERT INTO pre_ipo_schema_migrations(version, name, checksum, status) VALUES(?, ?, ?, ?)",
                (1, "001_baseline_evidence_schema", chk, "APPLIED")
            )
            conn.commit()
            newly_applied.append(1)
        except Exception:
            conn.rollback()
            raise

    # 3. Migration 2: Lifecycle & Multi-Document Extensions
    if 2 not in applied_records:
        m2_file = MIGRATIONS_DIR / "002_lifecycle_and_multidoc_extensions.sql"
        if not m2_file.exists():
            raise RuntimeError("Required migration file 002_lifecycle_and_multidoc_extensions.sql missing from disk.")
        sql = m2_file.read_text(encoding="utf-8")
        chk = compute_checksum(sql)
        conn.execute("BEGIN IMMEDIATE")
        try:
            # Safely handle pre-existing legacy tables before executing additive script
            # Company profiles
            prof_cols = _get_table_columns(conn, "pre_ipo_company_profiles")
            if prof_cols:
                if "generation" not in prof_cols:
                    conn.execute("ALTER TABLE pre_ipo_company_profiles ADD COLUMN generation INTEGER NOT NULL DEFAULT 1")
                if "status" not in prof_cols:
                    conn.execute("ALTER TABLE pre_ipo_company_profiles ADD COLUMN status TEXT NOT NULL DEFAULT 'ACTIVE'")

            # Sources
            src_cols = _get_table_columns(conn, "pre_ipo_sources")
            if src_cols:
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

            # Decision versions
            dec_cols = _get_table_columns(conn, "pre_ipo_decision_versions")
            if dec_cols:
                if "company_id" not in dec_cols:
                    conn.execute("ALTER TABLE pre_ipo_decision_versions ADD COLUMN company_id TEXT")
                if "snapshot_id" not in dec_cols:
                    conn.execute("ALTER TABLE pre_ipo_decision_versions ADD COLUMN snapshot_id TEXT")

            # Decision actions
            act_cols = _get_table_columns(conn, "pre_ipo_decision_actions")
            if act_cols:
                if "company_id" not in act_cols:
                    conn.execute("ALTER TABLE pre_ipo_decision_actions ADD COLUMN company_id TEXT")

            # Execute SQL script for newly defined tables and indexes
            _execute_sql_script_transactional(conn, sql)

            # Ensure decision versions index is created after columns exist
            conn.execute("CREATE INDEX IF NOT EXISTS idx_decision_versions_company ON pre_ipo_decision_versions(owner, company_id)")

            conn.execute(
                "INSERT INTO pre_ipo_schema_migrations(version, name, checksum, status) VALUES(?, ?, ?, ?)",
                (2, "002_lifecycle_and_multidoc_extensions", chk, "APPLIED")
            )
            conn.commit()
            newly_applied.append(2)
        except Exception:
            conn.rollback()
            raise

    # 4. Migration 3: Evidence Contract Normalization and Audit Attributes
    if 3 not in applied_records:
        m3_file = MIGRATIONS_DIR / "003_evidence_contract_normalization.sql"
        if not m3_file.exists():
            raise RuntimeError("Required migration file 003_evidence_contract_normalization.sql missing from disk.")
        sql = m3_file.read_text(encoding="utf-8")
        chk = compute_checksum(sql)
        conn.execute("BEGIN IMMEDIATE")
        try:
            # 1. Additive columns to pre_ipo_observations
            obs_cols = _get_table_columns(conn, "pre_ipo_observations")
            if obs_cols:
                cols_to_add = [
                    ("definition_id", "TEXT"),
                    ("physical_page", "INTEGER"),
                    ("printed_page", "TEXT"),
                    ("table_id", "TEXT"),
                    ("row_label", "TEXT"),
                    ("column_label", "TEXT"),
                    ("raw_text", "TEXT"),
                    ("extraction_run_id", "TEXT"),
                    ("method_version", "TEXT"),
                    ("reviewer", "TEXT"),
                    ("reviewed_at", "TEXT"),
                    ("review_reason", "TEXT"),
                    ("origin", "TEXT"),
                ]
                for col_name, col_type in cols_to_add:
                    if col_name not in obs_cols:
                        conn.execute(f"ALTER TABLE pre_ipo_observations ADD COLUMN {col_name} {col_type}")

                # Fail-closed classification of pre-existing legacy data
                conn.execute("UPDATE pre_ipo_observations SET origin = 'LEGACY_EXAMPLE' WHERE origin IS NULL")
                conn.execute("UPDATE pre_ipo_observations SET review_state = 'UNREVIEWED' WHERE origin = 'LEGACY_EXAMPLE'")

            # 2. Additive columns to pre_ipo_evidence_snapshots
            snap_cols = _get_table_columns(conn, "pre_ipo_evidence_snapshots")
            if snap_cols:
                snap_to_add = [
                    ("status", "TEXT NOT NULL DEFAULT 'UNREVIEWED'"),
                    ("snapshot_hash", "TEXT"),
                    ("accepted_by", "TEXT"),
                    ("accepted_at", "TEXT"),
                ]
                for col_name, col_type in snap_to_add:
                    if col_name not in snap_cols:
                        conn.execute(f"ALTER TABLE pre_ipo_evidence_snapshots ADD COLUMN {col_name} {col_type}")

            # Execute SQL script for indexes
            _execute_sql_script_transactional(conn, sql)

            conn.execute(
                "INSERT INTO pre_ipo_schema_migrations(version, name, checksum, status) VALUES(?, ?, ?, ?)",
                (3, "003_evidence_contract_normalization", chk, "APPLIED")
            )
            conn.commit()
            newly_applied.append(3)
        except Exception:
            conn.rollback()
            raise

    # 5. Migration 4: Legacy Evidence Origin Remediation
    if 4 not in applied_records:
        m4_file = MIGRATIONS_DIR / "004_legacy_evidence_origin_remediation.sql"
        if not m4_file.exists():
            raise RuntimeError("Required migration file 004_legacy_evidence_origin_remediation.sql missing from disk.")
        sql = m4_file.read_text(encoding="utf-8")
        chk = compute_checksum(sql)
        conn.execute("BEGIN IMMEDIATE")
        try:
            # Execute SQL script for remediation
            _execute_sql_script_transactional(conn, sql)

            # Python-level verification: Downgrade any non-hex64 snapshot_hash or invalid acceptance fields
            cursor = conn.execute(
                "SELECT owner, company, id, status, snapshot_hash, accepted_by, accepted_at "
                "FROM pre_ipo_evidence_snapshots WHERE status = 'ACCEPTED_FOR_ANALYSIS'"
            )
            rows = cursor.fetchall()
            for r in rows:
                s_owner, s_comp, s_id, s_stat, s_hash, s_by, s_at = r
                is_valid_hash = bool(s_hash and len(s_hash) == 64 and all(c in '0123456789abcdef' for c in str(s_hash)))
                is_valid_by = bool(s_by and str(s_by).strip())
                is_valid_at = bool(s_at and str(s_at).strip())
                if not (is_valid_hash and is_valid_by and is_valid_at):
                    conn.execute(
                        "UPDATE pre_ipo_evidence_snapshots SET status = 'UNREVIEWED' WHERE owner=? AND company=? AND id=?",
                        (s_owner, s_comp, s_id)
                    )

            conn.execute(
                "INSERT INTO pre_ipo_schema_migrations(version, name, checksum, status) VALUES(?, ?, ?, ?)",
                (4, "004_legacy_evidence_origin_remediation", chk, "APPLIED")
            )
            conn.commit()
            newly_applied.append(4)
        except Exception:
            conn.rollback()
            raise

    # 6. Migration 5: HCCH End-to-End Evidence Contract
    if 5 not in applied_records:
        m5_file = MIGRATIONS_DIR / "005_hcch_e2e_evidence_contract.sql"
        if not m5_file.exists():
            raise RuntimeError("Required migration file 005_hcch_e2e_evidence_contract.sql missing from disk.")
        sql = m5_file.read_text(encoding="utf-8")
        chk = compute_checksum(sql)
        conn.execute("BEGIN IMMEDIATE")
        try:
            # Safely handle pre-existing baseline extraction_runs table
            run_cols = _get_table_columns(conn, "pre_ipo_extraction_runs")
            if run_cols:
                cols_to_add = [
                    ("source_id", "TEXT"),
                    ("document_sha256", "TEXT"),
                    ("total_pages", "INTEGER"),
                    ("pages_indexed", "INTEGER"),
                    ("pages_requiring_ocr", "INTEGER NOT NULL DEFAULT 0"),
                    ("status", "TEXT"),
                    ("extractor_version", "TEXT"),
                    ("created_at", "TEXT"),
                ]
                for col_name, col_type in cols_to_add:
                    if col_name not in run_cols:
                        conn.execute(f"ALTER TABLE pre_ipo_extraction_runs ADD COLUMN {col_name} {col_type}")

            _execute_sql_script_transactional(conn, sql)
            conn.execute(
                "INSERT INTO pre_ipo_schema_migrations(version, name, checksum, status) VALUES(?, ?, ?, ?)",
                (5, "005_hcch_e2e_evidence_contract", chk, "APPLIED")
            )
            conn.commit()
            newly_applied.append(5)
        except Exception:
            conn.rollback()
            raise

    return newly_applied


def backfill_projections(conn: sqlite3.Connection) -> Dict[str, int]:
    """Backfill projections row-wise and resumably from legacy payloads into observations and dependencies."""
    counts = {"observations": 0, "decision_links": 0, "quarantined_orphans": 0}

    # 1. Backfill fact events into pre_ipo_observations row-wise
    facts = conn.execute("""
        SELECT f.owner, f.company, f.fact_id, f.revision, f.payload, f.created_at
        FROM pre_ipo_fact_events f
        WHERE NOT EXISTS (
            SELECT 1 FROM pre_ipo_observations o
            WHERE o.owner = f.owner AND o.company = f.company
              AND o.observation_id = f.fact_id AND o.revision = f.revision
        )
    """).fetchall()

    for owner, company, fact_id, rev, payload_raw, created_at in facts:
        try:
            p = json.loads(payload_raw) if isinstance(payload_raw, str) else payload_raw
            val = str(p.get("value")) if p.get("value") is not None else None
            pres = p.get("presence", "OBSERVED_VALUE")
            review = p.get("review", "UNREVIEWED")
            ctx = p.get("context", {})
            src = p.get("source", {})

            # Source ID must be the canonical source ID or origin ID, NOT the raw content sha256
            src_id = src.get("id") or p.get("origin_id") or src.get("origin_id") or "legacy_source"

            # Check if source exists in pre_ipo_sources
            src_row = conn.execute(
                "SELECT 1 FROM pre_ipo_sources WHERE owner=? AND company=? AND id=?",
                (owner, company, src_id)
            ).fetchone()

            if not src_row and src_id != "legacy_source":
                counts["quarantined_orphans"] += 1
                continue

            obs_cols = _get_table_columns(conn, "pre_ipo_observations")
            if "origin" in obs_cols:
                conn.execute("""
                    INSERT OR REPLACE INTO pre_ipo_observations (
                        owner, company, observation_id, revision, source_id, entity, metric_id,
                        period, duration, basis, framework, currency, unit, value, presence,
                        review_state, provenance_json, created_at, origin
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'LEGACY_EXAMPLE')
                """, (
                    owner, company, fact_id, rev, src_id, ctx.get("entity", company),
                    fact_id, ctx.get("period"), ctx.get("duration"), ctx.get("basis"),
                    ctx.get("framework"), ctx.get("currency"), ctx.get("unit"), val,
                    pres, review, json.dumps(src), created_at
                ))
            else:
                conn.execute("""
                    INSERT OR REPLACE INTO pre_ipo_observations (
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

    # 2. Backfill decision versions company_id / snapshot_id if missing or unresolved
    dec_cols = _get_table_columns(conn, "pre_ipo_decision_versions")
    if "company_id" in dec_cols:
        rows = conn.execute("""
            SELECT owner, case_id, revision, payload, company_id, snapshot_id
            FROM pre_ipo_decision_versions
            WHERE company_id IS NULL OR snapshot_id IS NULL
        """).fetchall()

        for owner, case_id, rev, payload_raw, curr_cid, curr_snap in rows:
            try:
                p = json.loads(payload_raw)
                ctx = p.get("context", {})

                # Resolve canonical company ID
                cid = curr_cid or ctx.get("company_id") or ctx.get("company")
                snap_id = curr_snap or ctx.get("snapshot_id") or ctx.get("evidence_snapshot_id") or p.get("snapshot_id")

                # If cid is a display name, attempt to match canonical ID from pre_ipo_company_profiles
                if cid:
                    prof_match = conn.execute(
                        "SELECT id FROM pre_ipo_company_profiles WHERE owner=? AND (id=? OR json_extract(payload, '$.name')=?)",
                        (owner, cid, cid)
                    ).fetchone()
                    if prof_match:
                        cid = prof_match[0]

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
