"""Unit tests for Pre-IPO schema migrations, journal tracking, and backup verification.
"""
import os
import sqlite3
import tempfile
from pathlib import Path
import pytest
from models.pre_ipo_migrations import (
    apply_migrations,
    get_applied_versions,
    backup_database,
    backfill_projections,
)


@pytest.fixture
def temp_db():
    temp_dir = tempfile.mkdtemp(prefix="mig_test_")
    db_path = os.path.join(temp_dir, "mig_test.db")
    conn = sqlite3.connect(db_path)
    yield conn, db_path
    conn.close()


def test_migrations_applied_and_journaled(temp_db):
    conn, db_path = temp_db
    newly_applied = apply_migrations(conn)
    assert 1 in newly_applied
    assert 2 in newly_applied
    assert 3 in newly_applied

    applied = get_applied_versions(conn)
    assert len(applied) == 3
    assert applied[1]["name"] == "001_baseline_evidence_schema"
    assert applied[2]["name"] == "002_lifecycle_and_multidoc_extensions"
    assert applied[3]["name"] == "003_evidence_contract_normalization"

    # Verify additive tables exist
    tables = [row[0] for row in conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()]
    assert "pre_ipo_schema_migrations" in tables
    assert "pre_ipo_sources" in tables
    assert "pre_ipo_company_profiles" in tables
    assert "pre_ipo_artifacts" in tables
    assert "pre_ipo_jobs" in tables
    assert "pre_ipo_observations" in tables
    assert "pre_ipo_dependencies" in tables
    assert "pre_ipo_tombstones" in tables

    # Verify additive columns exist
    prof_cols = [r[1] for r in conn.execute("PRAGMA table_info(pre_ipo_company_profiles)").fetchall()]
    assert "generation" in prof_cols
    assert "status" in prof_cols

    src_cols = [r[1] for r in conn.execute("PRAGMA table_info(pre_ipo_sources)").fetchall()]
    assert "generation" in src_cols
    assert "status" in src_cols
    assert "family" in src_cols
    assert "reporting_period" in src_cols
    assert "availability_date" in src_cols


def test_migrations_idempotent(temp_db):
    conn, _ = temp_db
    apply_migrations(conn)
    # Second run should apply 0 new migrations
    second_applied = apply_migrations(conn)
    assert len(second_applied) == 0


def test_backup_database(temp_db):
    conn, db_path = temp_db
    apply_migrations(conn)
    conn.execute("INSERT INTO pre_ipo_company_profiles(owner, id, payload, generation, status) VALUES ('test', 'c1', '{}', 1, 'ACTIVE')")
    conn.commit()

    backup_path = db_path + ".bak"
    res = backup_database(db_path, backup_path)
    assert os.path.exists(res)

    bak_conn = sqlite3.connect(res)
    rows = bak_conn.execute("SELECT owner, id FROM pre_ipo_company_profiles").fetchall()
    bak_conn.close()
    assert len(rows) == 1
    assert rows[0] == ("test", "c1")

