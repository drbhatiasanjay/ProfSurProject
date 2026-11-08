"""Comprehensive Regression Suite for Pre-IPO Red-Team Findings (W01–W11).
Verifies that all 11 adversarial probe failure modes are permanently remediated:
  W01: Withdrawal removes facts from active analysis and readiness
  W02: Source deletion purges all copies; identical re-upload does not reactivate prior facts
  W03: Workbench handoff uses canonical IDs and enables deletion
  W04: Company deletion erases decision actions
  W05: Monotonic incarnation across recreation; audit tombstones are preserved
  W06: Existing decision tables upgrade smoothly without column/index errors
  W07: Runtime field registry loads without docs directory
  W08: Model adapter semantic filtering, chronology, and non-falsified eligibility
  W09: Disclosed zeros recognized; mixed units converted; no invented defaults
  W10: Projection backfill uses correct source IDs and is row-wise resumable
  W11: Migration runner enforces integrity checksums and detects drift

MANDATORY TEST SAFETY DIRECTIVE:
Executes strictly against an isolated disposable SQLite database in system temp.
"""
import os
import sys
import json
import sqlite3
import tempfile
from pathlib import Path
from datetime import date, datetime, timezone
import pytest

# ── MANDATORY TEST SAFETY: Disposable DB BEFORE imports ────────────────────────
_ORIGINAL_PROFSUR_DB = os.environ.get("PROFSUR_DB_PATH")
_GUARDED_TEMP_DIR = tempfile.mkdtemp(prefix="prof_redteam_guard_")
_GUARDED_TEMP_DB = str(Path(_GUARDED_TEMP_DIR) / "test_disposable_redteam.db")
os.environ["PROFSUR_DB_PATH"] = _GUARDED_TEMP_DB

_resolved_test_db = Path(_GUARDED_TEMP_DB).resolve()
_temp_system_root = Path(tempfile.gettempdir()).resolve()
assert "capital_structure.db" not in _resolved_test_db.name, "Fatal: Test DB path cannot be capital_structure.db"
assert _resolved_test_db.is_relative_to(_temp_system_root), "Fatal: Test DB must be strictly inside system temp directory"

import db
from models import pre_ipo_evidence as ledger
from models import pre_ipo_evidence_analysis as analysis
from models.pre_ipo_migrations import apply_migrations, backfill_projections, compute_checksum
from models.pre_ipo_decision import store as decision_store
from models.pre_ipo_field_registry import PreIPOModelAdapter, get_field_spec, FIELD_REGISTRY
from models.pre_ipo_ingest import PreIPOIngestionEngine


@pytest.fixture(scope="module", autouse=True)
def restore_environment_db_path():
    yield
    if _ORIGINAL_PROFSUR_DB is not None:
        os.environ["PROFSUR_DB_PATH"] = _ORIGINAL_PROFSUR_DB
    else:
        os.environ.pop("PROFSUR_DB_PATH", None)


@pytest.fixture()
def clean_conn():
    conn = db.get_connection()
    apply_migrations(conn)
    return conn


def _make_dummy_pdf():
    # Minimal 1-page PDF
    return (
        b"%PDF-1.4\n1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj\n"
        b"2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj\n"
        b"3 0 obj<</Type/Page/MediaBox[0 0 612 792]/Parent 2 0 R>>endobj\n"
        b"xref\n0 4\n0000000000 65535 f \n0000000009 00000 n \n0000000052 00000 n \n"
        b"0000000102 00000 n \ntrailer<</Size 4/Root 1 0 R>>\nstartxref\n178\n%%EOF\n"
    )


# ── W01: Withdrawal removes facts from active analysis ─────────────────────────

def test_w01_withdrawal_removes_facts_from_analysis(clean_conn):
    owner = "test_w01_owner"
    company = ledger.create_company(owner, "admin", "W01 Corp", "Tech", ["FY24"])
    pdf_bytes = _make_dummy_pdf()
    meta = {
        "title": "W01 Prospectus",
        "filing_type": "DRHP",
        "version": "v1",
        "available_by": "2024-01-01",
        "rights": "Authorized",
        "reporting_period": "FY24"
    }
    src_id = ledger.retain_pdf(owner, "admin", company, pdf_bytes, meta)

    # Save an accepted fact
    fact = {
        "id": "history[0].revenue_ops_cr",
        "presence": "OBSERVED_VALUE",
        "origin": "FILING_FACT",
        "review": "ACCEPTED",
        "reason": "Audited review",
        "value": 1500.0,
        "source": {
            "id": src_id,
            "page": 1,
            "locator": "Table 1",
            "quote": "Revenue: 1500",
            "sha256": meta.get("sha256") or ledger.digest(pdf_bytes)
        },
        "context": {
            "entity": "W01 Corp",
            "period": "FY24",
            "duration": "12M",
            "basis": "Restated",
            "framework": "IndAS",
            "currency": "INR",
            "unit": "crore",
            "definition": "Revenue from operations"
        }
    }
    ledger.save_fact(owner, "admin", company, fact)

    # Before withdrawal: fact is valid
    vf_before = ledger.valid_facts(owner, company)
    assert len(vf_before) == 1
    assert vf_before[0]["id"] == "history[0].revenue_ops_cr"

    # Withdraw the source
    success = ledger.withdraw_source(owner, "admin", company, src_id, reason="Superseded by restatement")
    assert success is True

    # After withdrawal: fact must NOT be in valid_facts
    vf_after = ledger.valid_facts(owner, company)
    assert len(vf_after) == 0, "Withdrawn source facts must not appear in valid_facts"

    # Assess must show 0 accepted slots
    dossier = ledger.dossier(owner, company)
    ass = analysis.assess(owner, company, dossier, cutoff="2024-12-31")
    assert ass["accepted_required_slots"] == 0


# ── W02: Source deletion purges all copies and prevents reactivation ──────────

def test_w02_source_deletion_purges_copies_and_reupload_does_not_reactivate(clean_conn):
    owner = "test_w02_owner"
    company = ledger.create_company(owner, "admin", "W02 Corp", "Tech", ["FY24"])
    pdf_bytes = _make_dummy_pdf()
    meta = {
        "title": "W02 Prospectus",
        "filing_type": "DRHP",
        "version": "v1",
        "available_by": "2024-01-01",
        "rights": "Authorized",
        "reporting_period": "FY24"
    }
    src_id = ledger.retain_pdf(owner, "admin", company, pdf_bytes, meta)

    fact = {
        "id": "history[0].ebitda_cr",
        "presence": "OBSERVED_VALUE",
        "origin": "FILING_FACT",
        "review": "ACCEPTED",
        "reason": "Audited review",
        "value": 300.0,
        "source": {
            "id": src_id,
            "page": 1,
            "locator": "Table 2",
            "quote": "EBITDA: 300",
            "sha256": ledger.digest(pdf_bytes)
        },
        "context": {
            "entity": "W02 Corp",
            "period": "FY24",
            "duration": "12M",
            "basis": "Restated",
            "framework": "IndAS",
            "currency": "INR",
            "unit": "crore",
            "definition": "Revenue from operations"
        }
    }
    ledger.save_fact(owner, "admin", company, fact)

    # Delete source
    del_ok = ledger.delete_source(owner, "admin", company, src_id)
    assert del_ok is True

    # Verify fact events, observations, runs are purged
    with ledger.connection() as conn:
        obs_cnt = conn.execute("SELECT COUNT(*) FROM pre_ipo_observations WHERE owner=? AND source_id=?", (owner, src_id)).fetchone()[0]
        assert obs_cnt == 0
        fe_cnt = conn.execute("SELECT COUNT(*) FROM pre_ipo_fact_events WHERE owner=? AND company=?", (owner, company)).fetchone()[0]
        assert fe_cnt == 0

    # Re-upload the identical PDF content
    new_src_id = ledger.retain_pdf(owner, "admin", company, pdf_bytes, meta)
    assert new_src_id == src_id

    # Prior accepted facts must NOT be revived
    vf_reupload = ledger.valid_facts(owner, company)
    assert len(vf_reupload) == 0, "Re-uploading must not revive previously deleted accepted facts without review"


# ── W03: Workbench handoff uses canonical IDs and enables deletion ─────────────

def test_w03_workbench_handoff_retains_company_id_and_deletes_with_company(clean_conn):
    owner = "test_w03_owner"
    company = ledger.create_company(owner, "admin", "W03 Energy", "Energy", ["FY24"])
    pdf_bytes = _make_dummy_pdf()
    meta = {
        "title": "W03 Energy Prospectus",
        "filing_type": "DRHP",
        "version": "v1",
        "available_by": "2024-01-01",
        "rights": "Authorized",
        "reporting_period": "FY24"
    }
    src_id = ledger.retain_pdf(owner, "admin", company, pdf_bytes, meta)

    # Freeze a snapshot
    snap_id = ledger.freeze_snapshot(owner, "admin", company, "2024-12-31")
    snap = ledger.get_snapshot(owner, company, snap_id)

    # Generate workbench context
    wb_ctx = analysis.workbench_context(snap)
    assert wb_ctx["company_id"] == company
    assert wb_ctx["snapshot_id"] == snap_id

    # Run case and save
    from models.pre_ipo_decision.service import run_case
    report = run_case(wb_ctx)
    case_id, rev = decision_store.save_case(owner, "admin", report)

    # Check deletion impact
    impact = ledger.get_deletion_impact(owner, company)
    assert impact["affected_counts"]["saved_decisions"] == 1

    # Delete company
    assert ledger.delete_company(owner, "admin", company) is True

    # Case should now be gone
    with db.get_connection() as conn:
        saved_left = conn.execute("SELECT COUNT(*) FROM pre_ipo_decision_versions WHERE owner=? AND company_id=?", (owner, company)).fetchone()[0]
        assert saved_left == 0


# ── W04: Company deletion erases decision actions ──────────────────────────────

def test_w04_company_deletion_erases_decision_actions(clean_conn):
    owner = "test_w04_owner"
    company = ledger.create_company(owner, "admin", "W04 Logistics", "Logistics", ["FY24"])
    pdf_bytes = _make_dummy_pdf()
    meta = {
        "title": "W04 Logistics Prospectus",
        "filing_type": "DRHP",
        "version": "v1",
        "available_by": "2024-01-01",
        "rights": "Authorized",
        "reporting_period": "FY24"
    }
    ledger.retain_pdf(owner, "admin", company, pdf_bytes, meta)
    snap_id = ledger.freeze_snapshot(owner, "admin", company, "2024-12-31")
    snap = ledger.get_snapshot(owner, company, snap_id)

    wb_ctx = analysis.workbench_context(snap)
    from models.pre_ipo_decision.service import run_case
    report = run_case(wb_ctx)
    case_id, rev = decision_store.save_case(owner, "admin", report)

    # Record action
    action = {"decision": "APPROVED_WITH_COVENANTS", "rationale": "Strong balance sheet"}
    act_id = decision_store.record_action(owner, "admin", case_id, rev, action)
    assert act_id is not None

    # Deletion impact must count actions
    impact = ledger.get_deletion_impact(owner, company)
    assert impact["affected_counts"]["decision_actions"] == 1

    # Delete company
    ledger.delete_company(owner, "admin", company)

    # Decision actions must be purged
    with db.get_connection() as conn:
        acts_left = conn.execute("SELECT COUNT(*) FROM pre_ipo_decision_actions WHERE owner=? AND company_id=?", (owner, company)).fetchone()[0]
        assert acts_left == 0


# ── W05: Monotonic incarnation across recreation and append-only tombstones ────

def test_w05_company_recreation_monotonic_generation_and_tombstone_history(clean_conn):
    owner = "test_w05_owner"
    c_name = "W05 Monotonic Ltd"

    # Create -> Delete 1st time
    cid = ledger.create_company(owner, "admin", c_name, "Manufacturing", ["FY24"])
    prof1 = ledger.companies(owner)[cid]
    assert prof1.generation == 1

    ledger.delete_company(owner, "admin", cid)

    # Recreate with same inputs
    cid2 = ledger.create_company(owner, "admin", c_name, "Manufacturing", ["FY24"])
    assert cid2 == cid
    prof2 = ledger.companies(owner)[cid]
    assert prof2.generation == 2, "Recreated company must advance to generation 2"

    # Delete 2nd time
    ledger.delete_company(owner, "admin", cid)

    # Recreate 3rd time
    cid3 = ledger.create_company(owner, "admin", c_name, "Manufacturing", ["FY24"])
    prof3 = ledger.companies(owner)[cid]
    assert prof3.generation == 3

    # Tombstones must contain multiple distinct records (not overwritten)
    with db.get_connection() as conn:
        tomb_rows = conn.execute(
            "SELECT generation, action FROM pre_ipo_tombstones WHERE owner=? AND company=? AND target_kind='COMPANY'",
            (owner, cid)
        ).fetchall()
        assert len(tomb_rows) == 2
        gens = [r[0] for r in tomb_rows]
        assert 1 not in gens or len(gens) == 2


# ── W06: Existing decision schema upgrade and index safety ─────────────────────

def test_w06_existing_decision_schema_upgrade_and_index_safety():
    # Create isolated disposable DB without company_id in decision_versions
    raw_tmp = tempfile.mktemp(prefix="prof_legacy_db_")
    conn = sqlite3.connect(raw_tmp)
    try:
        # Simulate legacy schema without company_id
        conn.execute("""
            CREATE TABLE pre_ipo_decision_versions (
                owner TEXT NOT NULL,
                case_id TEXT NOT NULL,
                revision INTEGER NOT NULL,
                payload TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY(owner, case_id, revision)
            )
        """)
        conn.commit()

        # Run migration runner: must not crash with OperationalError
        newly_applied = apply_migrations(conn)
        assert 2 in newly_applied

        # Verify company_id exists now
        cols = [r[1] for r in conn.execute("PRAGMA table_info(pre_ipo_decision_versions)").fetchall()]
        assert "company_id" in cols
        assert "snapshot_id" in cols
    finally:
        conn.close()
        if os.path.exists(raw_tmp):
            os.remove(raw_tmp)


# ── W07: Runtime field registry loads without docs directory ───────────────────

def test_w07_runtime_field_registry_loads_without_docs_directory():
    # Verify that get_field_spec works and loads all 74 field families
    assert len(FIELD_REGISTRY) == 74
    spec = get_field_spec("financial.revenue_operations")
    assert spec is not None
    assert spec.profile in ("FINANCIAL", "RESTATED_FINANCIALS")

    # Verify JSON resource exists in models/data
    json_path = Path("models/data/pre_ipo_field_bindings.json")
    assert json_path.exists(), "Packaged field bindings JSON must exist in models/data/"


# ── W08: Model adapter semantic filtering, chronology, and eligibility ─────────

def test_w08_model_adapter_filters_unreviewed_preserves_none_and_orders_chronology():
    obs = [
        # FY25 accepted
        {"metric_id": "financial.revenue_operations", "value": 2000.0, "period": "FY25", "review_state": "ACCEPTED", "currency": "INR"},
        {"metric_id": "financial.ebitda_reported", "value": 400.0, "period": "FY25", "review_state": "ACCEPTED", "currency": "INR"},
        {"metric_id": "financial.equity_and_retained_earnings", "value": 1000.0, "period": "FY25", "review_state": "ACCEPTED", "currency": "INR"},
        # FY24 accepted
        {"metric_id": "financial.revenue_operations", "value": 1600.0, "period": "FY24", "review_state": "ACCEPTED", "currency": "INR"},
        {"metric_id": "financial.ebitda_reported", "value": 300.0, "period": "FY24", "review_state": "ACCEPTED", "currency": "INR"},
        # Unreviewed / rejected observation
        {"metric_id": "financial.revenue_operations", "value": 99999.0, "period": "FY25", "review_state": "UNREVIEWED", "currency": "INR"},
        {"metric_id": "financial.cfo", "value": 99999.0, "period": "FY25", "review_state": "REJECTED", "currency": "INR"},
    ]

    dossier = PreIPOModelAdapter.observations_to_dossier("TestCo", obs)
    # Chronology must be ascending: FY24, FY25
    assert len(dossier.history) == 2
    assert dossier.history[0].fiscal_year == "FY24"
    assert dossier.history[1].fiscal_year == "FY25"

    # latest_financials must be FY25
    assert dossier.latest_financials.fiscal_year == "FY25"
    assert dossier.latest_financials.revenue_ops_cr == 2000.0

    # Missing CFO must be None, not 0.0
    assert dossier.latest_financials.cfo_cr is None

    # Analytical inputs check
    inputs = PreIPOModelAdapter.extract_analytical_inputs(obs)
    # Eligibility must be False because CFO is missing
    assert inputs["is_eligible_for_underwriting"] is False
    assert any("CFO" in r for r in inputs["eligibility_reasons"])


# ── W09: Disclosed zeros and mixed units handling in ingestion engine ──────────

def test_w09_native_extraction_disclosed_zeros_and_no_invented_defaults():
    # Disclosed zero EBITDA and CFO
    table_text = (
        "RESTATED FINANCIAL STATEMENTS (in ₹ crore)\n"
        "Particulars\tFY24\n"
        "Revenue from Operations\t1000.0\n"
        "Operating EBITDA\t0.0\n"
        "Cash Flow from Operations (CFO)\t0.0\n"
        "Profit After Tax (PAT)\t100.0\n"
        "Tangible Net Worth\t500.0\n"
        "Secured term loans from banks\t150.0\n"
    )

    dossier, audit_items, limitations, provenance = PreIPOIngestionEngine.extract_from_text(table_text)

    # Disclosed zeros should be FOUND_AND_RECONCILED, not MISSING_UNDISCLOSED
    eb_audit = next((a for a in audit_items if "Operating EBITDA" in a.field_name), None)
    assert eb_audit is not None
    assert eb_audit.status == "FOUND_AND_RECONCILED", f"Disclosed zero EBITDA should be reconciled, got {eb_audit.status}"

    cfo_audit = next((a for a in audit_items if "Cash Flow from Operations" in a.field_name), None)
    assert cfo_audit is not None
    assert cfo_audit.status == "FOUND_AND_RECONCILED", f"Disclosed zero CFO should be reconciled, got {cfo_audit.status}"

    # Limitations should NOT emit GAP-INTAKE-EBITDA-01 or GAP-INTAKE-CFO-01
    gap_ids = [lim.gap_id for lim in limitations]
    assert "GAP-INTAKE-EBITDA-01" not in gap_ids
    assert "GAP-INTAKE-CFO-01" not in gap_ids

    # Undisclosed interest rate and governance must NOT have invented defaults
    assert dossier.indebtedness.weighted_avg_interest_rate_pct is None
    assert dossier.governance.independent_directors_pct is None


# ── W10: Projection backfill source identity and resumability ──────────────────

def test_w10_projection_backfill_source_identity_and_resumability(clean_conn):
    owner = "test_w10_owner"
    company = ledger.create_company(owner, "admin", "W10 Logistics", "Logistics", ["FY24"])
    pdf_bytes = _make_dummy_pdf()
    meta = {
        "title": "W10 Prospectus",
        "filing_type": "DRHP",
        "version": "v1",
        "available_by": "2024-01-01",
        "rights": "Authorized",
        "reporting_period": "FY24"
    }
    src_id = ledger.retain_pdf(owner, "admin", company, pdf_bytes, meta)

    # Insert legacy fact event directly
    with db.get_connection() as conn:
        fact1 = {
            "id": "history[0].revenue_ops_cr",
            "value": 1200.0,
            "presence": "OBSERVED_VALUE",
            "review": "ACCEPTED",
            "source": {"id": src_id, "page": 1, "locator": "T1"},
            "context": {"entity": "W10 Logistics", "period": "FY24"}
        }
        conn.execute(
            "INSERT INTO pre_ipo_fact_events(owner, company, fact_id, revision, payload) VALUES(?,?,?,?,?)",
            (owner, company, fact1["id"], 1, json.dumps(fact1))
        )
        conn.commit()

        # Run 1st backfill
        c1 = backfill_projections(conn)
        assert c1["observations"] >= 1

        # Check source_id in observations
        obs_row = conn.execute(
            "SELECT source_id FROM pre_ipo_observations WHERE owner=? AND company=? AND observation_id=?",
            (owner, company, fact1["id"])
        ).fetchone()
        assert obs_row[0] == src_id, f"Expected source_id {src_id}, got {obs_row[0]}"

        # Insert a 2nd legacy fact event
        fact2 = {
            "id": "history[0].pat_cr",
            "value": 200.0,
            "presence": "OBSERVED_VALUE",
            "review": "ACCEPTED",
            "source": {"id": src_id, "page": 1, "locator": "T2"},
            "context": {"entity": "W10 Logistics", "period": "FY24"}
        }
        conn.execute(
            "INSERT INTO pre_ipo_fact_events(owner, company, fact_id, revision, payload) VALUES(?,?,?,?,?)",
            (owner, company, fact2["id"], 1, json.dumps(fact2))
        )
        conn.commit()

        # Run 2nd backfill: must resume and backfill fact2 without skipping!
        c2 = backfill_projections(conn)
        assert c2["observations"] >= 1, "Backfill must be resumable and process newly added facts"


# ── W11: Migration runner checksum enforcement and drift detection ─────────────

def test_w11_migration_checksum_enforcement_and_drift_detection(clean_conn):
    with db.get_connection() as conn:
        # Deliberately tamper with stored checksum in schema migrations journal
        conn.execute(
            "UPDATE pre_ipo_schema_migrations SET checksum='tampered_bad_checksum' WHERE version=1"
        )
        conn.commit()

        # Running apply_migrations must detect drift and raise RuntimeError
        with pytest.raises(RuntimeError, match="Migration checksum mismatch"):
            apply_migrations(conn)

        # Restore valid checksum for subsequent test isolation
        m1_file = Path("models/migrations/001_baseline_evidence_schema.sql")
        valid_chk = compute_checksum(m1_file.read_text(encoding="utf-8"))
        conn.execute(
            "UPDATE pre_ipo_schema_migrations SET checksum=? WHERE version=1",
            (valid_chk,)
        )
        conn.commit()
