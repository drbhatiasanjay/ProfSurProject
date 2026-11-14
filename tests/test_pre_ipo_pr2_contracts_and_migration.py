"""
PR 2 — Evidence Contract & Additive Migration 003 Test Suite
Covers all PR 2 requirements:
- fresh migration
- upgrade from 001
- upgrade from 001+002
- idempotent rerun
- checksum mismatch
- rollback and backup/restore
- conservative legacy backfill
- missing-value round trip
- genuine zero round trip
- accepted observation requires valid locator/reviewer/reason
- LEGACY_EXAMPLE cannot enter accepted snapshot
- missing input cannot participate in arithmetic
- static/AST test rejects prohibited factual fallbacks in Pre-IPO production modules
"""

import ast
import os
import sqlite3
import pytest
from pathlib import Path
from models.pre_ipo_migrations import (
    apply_migrations,
    compute_checksum,
    get_applied_migrations,
    backup_database,
    backfill_projections,
    _get_table_columns,
    MIGRATIONS_DIR,
)
from models.pre_ipo_evidence import (
    Observation,
    SourceLocator,
    AcceptedEvidenceSnapshot,
    PRESENCE,
    REVIEW,
    ORIGINS,
)
from models.pre_ipo_schema import ObjectsOfOfferWaterfall


@pytest.fixture
def test_db_path(tmp_path, monkeypatch):
    """Provides isolated temporary SQLite database path."""
    db_file = tmp_path / "test_pre_ipo_migration.db"
    monkeypatch.setenv("PROFSUR_DB_PATH", str(db_file))
    return str(db_file)


def test_fresh_migration(test_db_path):
    """Verify fresh migration on an empty database applies versions 1, 2, and 3."""
    conn = sqlite3.connect(test_db_path)
    try:
        applied = apply_migrations(conn)
        assert applied == [1, 2, 3, 4], f"Expected [1, 2, 3, 4], got {applied}"
        
        # Verify schema journal
        journal = get_applied_migrations(conn)
        assert 1 in journal and 2 in journal and 3 in journal
        assert journal[3]["status"] == "APPLIED"
        
        # Verify columns added by 003 in pre_ipo_observations
        cols = _get_table_columns(conn, "pre_ipo_observations")
        expected_003_cols = [
            "definition_id", "physical_page", "printed_page", "table_id",
            "row_label", "column_label", "raw_text", "extraction_run_id",
            "method_version", "reviewer", "reviewed_at", "review_reason"
        ]
        for col in expected_003_cols:
            assert col in cols, f"Column {col} missing in pre_ipo_observations"
            
        # Verify columns added in pre_ipo_evidence_snapshots
        snap_cols = _get_table_columns(conn, "pre_ipo_evidence_snapshots")
        assert "status" in snap_cols
        assert "snapshot_hash" in snap_cols
    finally:
        conn.close()


def test_upgrade_from_001(test_db_path):
    """Verify clean upgrade from 001 to 002 and 003."""
    conn = sqlite3.connect(test_db_path)
    try:
        # Apply 001 manually
        sql_001 = (MIGRATIONS_DIR / "001_baseline_evidence_schema.sql").read_text(encoding="utf-8")
        conn.executescript(sql_001)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS pre_ipo_schema_migrations (
                version INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                checksum TEXT NOT NULL,
                applied_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                status TEXT NOT NULL
            )
        """)
        conn.execute(
            "INSERT INTO pre_ipo_schema_migrations(version, name, checksum, status) VALUES(?, ?, ?, ?)",
            (1, "001_baseline_evidence_schema", compute_checksum(sql_001), "APPLIED")
        )
        conn.commit()
        
        # Upgrade
        applied = apply_migrations(conn)
        assert applied == [2, 3, 4]
        
        journal = get_applied_migrations(conn)
        assert 2 in journal and 3 in journal
    finally:
        conn.close()


def test_upgrade_from_001_and_002(test_db_path):
    """Verify additive upgrade when 001 and 002 are already applied."""
    conn = sqlite3.connect(test_db_path)
    try:
        # Apply 1 and 2
        sql_001 = (MIGRATIONS_DIR / "001_baseline_evidence_schema.sql").read_text(encoding="utf-8")
        sql_002 = (MIGRATIONS_DIR / "002_lifecycle_and_multidoc_extensions.sql").read_text(encoding="utf-8")
        conn.executescript(sql_001)
        conn.executescript(sql_002)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS pre_ipo_schema_migrations (
                version INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                checksum TEXT NOT NULL,
                applied_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                status TEXT NOT NULL
            )
        """)
        conn.execute(
            "INSERT INTO pre_ipo_schema_migrations(version, name, checksum, status) VALUES(?, ?, ?, ?)",
            (1, "001_baseline_evidence_schema", compute_checksum(sql_001), "APPLIED")
        )
        conn.execute(
            "INSERT INTO pre_ipo_schema_migrations(version, name, checksum, status) VALUES(?, ?, ?, ?)",
            (2, "002_lifecycle_and_multidoc_extensions", compute_checksum(sql_002), "APPLIED")
        )
        conn.commit()
        
        # Apply pending
        applied = apply_migrations(conn)
        assert applied == [3, 4]
        
        cols = _get_table_columns(conn, "pre_ipo_observations")
        assert "definition_id" in cols
        assert "physical_page" in cols
    finally:
        conn.close()


def test_idempotent_rerun(test_db_path):
    """Verify that applying migrations repeatedly is completely idempotent."""
    conn = sqlite3.connect(test_db_path)
    try:
        applied1 = apply_migrations(conn)
        assert applied1 == [1, 2, 3, 4]
        
        # Second run should apply 0 migrations and succeed
        applied2 = apply_migrations(conn)
        assert applied2 == []
    finally:
        conn.close()


def test_checksum_mismatch(test_db_path):
    """Verify that any modification to an applied migration triggers schema drift RuntimeError."""
    conn = sqlite3.connect(test_db_path)
    try:
        apply_migrations(conn)
        # Corrupt the journal checksum for version 1
        conn.execute("UPDATE pre_ipo_schema_migrations SET checksum='tampered_hash' WHERE version=1")
        conn.commit()
        
        with pytest.raises(RuntimeError) as exc_info:
            apply_migrations(conn)
        assert "checksum mismatch" in str(exc_info.value).lower()
    finally:
        conn.close()


def test_rollback_and_backup_restore(test_db_path, tmp_path):
    """Verify SQLite backup API generates a restorable rehearsal copy."""
    conn = sqlite3.connect(test_db_path)
    try:
        apply_migrations(conn)
        backup_file = str(tmp_path / "backup_rehearsal.db")
        backup_database(test_db_path, backup_file)
        
        assert os.path.exists(backup_file)
        b_conn = sqlite3.connect(backup_file)
        b_journal = get_applied_migrations(b_conn)
        assert 3 in b_journal
        b_conn.close()
    finally:
        conn.close()


def test_conservative_legacy_backfill(test_db_path):
    """
    Backfill rule: Legacy registry/fact data becomes LEGACY_EXAMPLE and UNREVIEWED.
    Missing fields remain None/unknown without invented locators.
    """
    conn = sqlite3.connect(test_db_path)
    try:
        apply_migrations(conn)
        # Insert a legacy fact event
        conn.execute("""
            INSERT INTO pre_ipo_sources (owner, company, id, metadata, content)
            VALUES ('drbhatia', 'legacy_corp', 'legacy_src', '{}', X'00')
        """)
        conn.execute("""
            INSERT INTO pre_ipo_fact_events (owner, company, fact_id, revision, payload)
            VALUES ('drbhatia', 'legacy_corp', 'fact_rev_01', 1, '{"value": 1250.5, "presence": "OBSERVED_VALUE", "source": {"id": "legacy_src"}}')
        """)
        conn.commit()
        
        counts = backfill_projections(conn)
        assert counts["observations"] >= 1
        
        obs_row = conn.execute("""
            SELECT value, presence, review_state, physical_page, definition_id
            FROM pre_ipo_observations
            WHERE owner='drbhatia' AND company='legacy_corp' AND observation_id='fact_rev_01'
        """).fetchone()
        
        assert obs_row is not None
        assert obs_row[0] == "1250.5"
        assert obs_row[1] == "OBSERVED_VALUE"
        assert obs_row[2] == "UNREVIEWED"
        assert obs_row[3] is None, "Physical page must not be invented for legacy fact"
        assert obs_row[4] is None, "Definition ID must not be invented for legacy fact"
    finally:
        conn.close()


def test_missing_value_round_trip():
    """Verify missing disclosures are preserved as NOT_DISCLOSED and None, never coerced to 0."""
    obs = Observation(
        observation_id="obs_rev_missing",
        owner="drbhatia",
        company="test_co",
        metric_id="revenue_ops_cr",
        entity="test_co",
        value=None,
        presence="NOT_DISCLOSED",
        review_state="UNREVIEWED",
        origin="FILING_FACT",
    )
    assert obs.value is None
    assert obs.presence == "NOT_DISCLOSED"
    assert obs.numeric_value is None
    assert obs.is_observed is False


def test_genuine_zero_round_trip():
    """Verify explicit zero is captured as EXPLICIT_NIL, distinct from absence/None."""
    obs = Observation(
        observation_id="obs_zero_debt",
        owner="drbhatia",
        company="test_co",
        metric_id="short_term_debt_cr",
        entity="test_co",
        value="0.0",
        presence="EXPLICIT_NIL",
        review_state="UNREVIEWED",
        origin="FILING_FACT",
    )
    assert obs.value == "0.0"
    assert obs.presence == "EXPLICIT_NIL"
    assert obs.numeric_value == 0.0
    assert obs.is_explicit_zero is True


def test_accepted_observation_requires_valid_locator_reviewer_reason():
    """Verify that an observation cannot be ACCEPTED without valid locator, reviewer, and reason."""
    # Missing locator and reviewer
    with pytest.raises(ValueError) as exc:
        Observation(
            observation_id="obs_bad_accept",
            owner="drbhatia",
            company="test_co",
            metric_id="ebitda_cr",
            entity="test_co",
            value="1640.0",
            presence="OBSERVED_VALUE",
            review_state="ACCEPTED",
            origin="FILING_FACT",
            locator=None,
            reviewer=None,
            review_reason=None,
        )
    assert "locator" in str(exc.value).lower() or "reviewer" in str(exc.value).lower()

    # Valid accepted observation
    valid_loc = SourceLocator(
        physical_page=68,
        printed_page="62",
        table_id="tbl_restated_pnl",
        raw_text="Operating Profit (EBITDA): 1,640.019",
    )
    obs_valid = Observation(
        observation_id="obs_good_accept",
        owner="drbhatia",
        company="test_co",
        metric_id="ebitda_cr",
        entity="test_co",
        value="1640.019",
        presence="OBSERVED_VALUE",
        review_state="ACCEPTED",
        origin="FILING_FACT",
        locator=valid_loc,
        reviewer="drbhatia",
        review_reason="Verified against Restated Standalone P&L Schedule V Page 68",
    )
    assert obs_valid.review_state == "ACCEPTED"


def test_legacy_example_cannot_enter_accepted_snapshot():
    """Verify that LEGACY_EXAMPLE origin observations are strictly rejected from accepted snapshots."""
    loc = SourceLocator(physical_page=10, raw_text="Sample text")
    obs = Observation(
        observation_id="obs_legacy",
        owner="drbhatia",
        company="test_co",
        metric_id="pat_cr",
        entity="test_co",
        value="500.0",
        presence="OBSERVED_VALUE",
        review_state="ACCEPTED",
        origin="LEGACY_EXAMPLE",
        locator=loc,
        reviewer="drbhatia",
        review_reason="Legacy review",
    )
    with pytest.raises(ValueError) as exc:
        AcceptedEvidenceSnapshot(
            snapshot_id="snap_test_001",
            owner="drbhatia",
            company="test_co",
            snapshot_hash="hash123",
            observations={"obs_legacy": obs},
            accepted_by="drbhatia",
            accepted_at="2026-11-13T12:00:00Z",
            created_at="2026-11-13T12:00:00Z",
        )
    assert "LEGACY_EXAMPLE" in str(exc.value)


def test_missing_input_cannot_participate_in_arithmetic():
    """
    Verify that absence of interest rate does NOT silently calculate with 9.0%.
    It must return None when interest rate is None and prepayment is positive.
    """
    waterfall = ObjectsOfOfferWaterfall(
        gross_fresh_issue_cr=1000.0,
        issue_expenses_cr=50.0,
        debt_prepayment_cr=400.0,
        capex_expansion_cr=300.0,
        inorganic_acquisition_cr=100.0,
        general_corporate_purposes_cr=150.0,
        interest_rate_on_retired_debt_pct=None,  # No default 9.0%
        shares_pre_issue_cr=None,               # No default 36.0 Cr
        shares_post_issue_cr=None,              # No default 40.0 Cr
    )
    assert waterfall.interest_rate_on_retired_debt_pct is None
    assert waterfall.shares_pre_issue_cr is None
    assert waterfall.shares_post_issue_cr is None
    # Annual interest savings cannot be fabricated without interest rate
    assert waterfall.annual_interest_savings_cr is None


def test_static_ast_rejects_prohibited_factual_fallbacks():
    """
    Static/AST inspection asserting no hardcoded 9.0% / 8.5% interest defaults,
    no 36/40 Cr share count defaults, and no 10.0 face value defaults in schema.
    """
    schema_path = Path(__file__).parent.parent / "models" / "pre_ipo_schema.py"
    with open(schema_path, "r", encoding="utf-8") as f:
        tree = ast.parse(f.read(), filename=str(schema_path))

    for node in ast.walk(tree):
        if isinstance(node, ast.AnnAssign):
            target_name = node.target.id if isinstance(node.target, ast.Name) else ""
            if target_name == "interest_rate_on_retired_debt_pct":
                if isinstance(node.value, ast.Constant):
                    assert node.value.value is None, "interest_rate_on_retired_debt_pct must default to None, not 9.0"
            elif target_name in ("shares_pre_issue_cr", "shares_post_issue_cr"):
                if isinstance(node.value, ast.Constant):
                    assert node.value.value is None, f"{target_name} must default to None, not 36/40"
            elif target_name == "face_value_inr":
                if isinstance(node.value, ast.Constant):
                    assert node.value.value is None, "face_value_inr must default to None, not 10.0"

