"""Integration acceptance test suite for Pre-IPO Part 2.
Verifies end-to-end connection between Part 1 ingestion and owner-scoped evidence ledger.

MANDATORY TEST SAFETY DIRECTIVE:
This file executes ONLY against an isolated, disposable temporary database.
Under no circumstances may it run against or delete records from capital_structure.db.
"""
import os
import sys
import io
import json
import tempfile
from pathlib import Path
from datetime import date

# ── MANDATORY TEST SAFETY: Initialize isolated test DB path BEFORE imports ──────
_ORIGINAL_PROFSUR_DB = os.environ.get("PROFSUR_DB_PATH")
_GUARDED_TEMP_DIR = tempfile.mkdtemp(prefix="prof_part2_guard_")
_GUARDED_TEMP_DB = str(Path(_GUARDED_TEMP_DIR) / "test_disposable_evidence.db")
os.environ["PROFSUR_DB_PATH"] = _GUARDED_TEMP_DB

# Strict verification of isolation
_resolved_test_db = Path(_GUARDED_TEMP_DB).resolve()
_temp_system_root = Path(tempfile.gettempdir()).resolve()
assert "capital_structure.db" not in _resolved_test_db.name, "Fatal: Test DB path cannot be capital_structure.db"
assert _resolved_test_db.is_relative_to(_temp_system_root), "Fatal: Test DB must be strictly inside system temp directory"

import pytest
from models.pre_ipo_ingest import PreIPOIngestionEngine
from models import pre_ipo_evidence as ledger
from utils.pre_ipo_evidence_export import export_json, export_pptx
from models.pre_ipo_custom_store import migrate_legacy_pickle

# Portable fixture resolution: check local repo scratch first, then fallback to codex worktree
LOCAL_FIXTURE_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "scratch", "ingestion_assessment_20261108", "known-values.pdf"
)
WORKTREE_FIXTURE_PATH = r"C:\Users\hemas\.codex\worktrees\profsur-decision-depth\ProfSurProject\scratch\ingestion_assessment_20261108\known-values.pdf"

KNOWN_VALUES_PDF = LOCAL_FIXTURE_PATH if os.path.exists(LOCAL_FIXTURE_PATH) else WORKTREE_FIXTURE_PATH

# Synthetic test accounts strictly isolated from real application users
TEST_OWNER_ADMIN = "test_synth_owner_admin"
TEST_OWNER_OTHER = "test_synth_owner_other"
TEST_VIEWER_USER = "test_synth_viewer"


@pytest.fixture(scope="module", autouse=True)
def restore_environment_db_path():
    yield
    if _ORIGINAL_PROFSUR_DB is not None:
        os.environ["PROFSUR_DB_PATH"] = _ORIGINAL_PROFSUR_DB
    else:
        os.environ.pop("PROFSUR_DB_PATH", None)


@pytest.fixture(autouse=True)
def guard_and_clean_test_companies():
    """Ensure clean ledger before and after tests, enforcing strict database isolation."""
    current_db = os.environ.get("PROFSUR_DB_PATH", "")
    resolved_db = Path(current_db).resolve()
    default_db = Path(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "capital_structure.db")).resolve()

    # Destructive guard: refuse execution if pointing to default or non-temporary database
    if not current_db or resolved_db == default_db or "capital_structure.db" in resolved_db.name:
        raise RuntimeError(f"TEST SAFETY VIOLATION BLOCKED: Refusing destructive test cleanup on: {current_db}")
    if not resolved_db.is_relative_to(Path(tempfile.gettempdir()).resolve()):
        raise RuntimeError(f"TEST SAFETY VIOLATION BLOCKED: DB path is not in temporary workspace: {resolved_db}")

    yield

    # Clean up ONLY synthetic test owners created by this test suite
    for owner in [TEST_OWNER_ADMIN, TEST_OWNER_OTHER, TEST_VIEWER_USER]:
        try:
            for cid in list(ledger.companies(owner).keys()):
                ledger.delete_company(owner, "admin", cid)
        except Exception:
            pass


def test_test_safety_guard_blocks_real_and_production_databases():
    """Verifies that the test safety guard strictly blocks execution against default/production DB."""
    active_db = os.environ.get("PROFSUR_DB_PATH", "")
    assert active_db, "PROFSUR_DB_PATH must be explicitly set"
    assert "capital_structure.db" not in Path(active_db).name, "Must not target capital_structure.db"
    assert Path(active_db).resolve().is_relative_to(Path(tempfile.gettempdir()).resolve())


def test_part2_end_to_end_upload_to_evidence_ledger():
    """Validates: Upload -> Ingest -> Ledger persistence -> Facts & evidence review data fidelity."""
    assert os.path.exists(KNOWN_VALUES_PDF), f"Test fixture missing: {KNOWN_VALUES_PDF}"
    with open(KNOWN_VALUES_PDF, "rb") as f:
        pdf_bytes = f.read()

    # Step 1: Run Part 1 extraction
    dossier = PreIPOIngestionEngine.ingest_document(io.BytesIO(pdf_bytes), company_name_hint="Fresh Venture Corp")
    assert len(dossier.history) == 1
    assert dossier.history[0].revenue_ops_cr == 1234.0

    # Step 2: Persist into owner-scoped evidence ledger
    meta = {
        "title": "Fresh Venture Corp DRHP",
        "filing_type": "DRHP",
        "version": "Draft 1.0",
        "available_by": str(date.today()),
        "rights": "Public Regulatory Filing (SEBI ICDR 2018)",
        "official_url": "Uploaded document",
        "issuer": "Fresh Venture Corp",
        "retention_policy": "Retained for Pre-IPO diligence",
    }
    company_id = ledger.import_dossier(TEST_OWNER_ADMIN, "admin", "Fresh Venture Corp", dossier, pdf_bytes, meta)
    assert company_id.startswith("private-")

    # Step 3: Verify company appears in owner's profile, but NOT in another owner's profile
    admin_companies = ledger.companies(TEST_OWNER_ADMIN)
    assert company_id in admin_companies
    assert admin_companies[company_id].company_name == "Fresh Venture Corp"

    # Isolation check: other synthetic owner must NOT see primary owner's private company
    other_companies = ledger.companies(TEST_OWNER_OTHER)
    assert company_id not in other_companies

    # Step 4: Verify facts in ledger match exact Part 1 extracted numbers
    facts = ledger.facts(TEST_OWNER_ADMIN, company_id)
    fact_dict = {f["id"]: f for f in facts}

    expected_facts = {
        "history[0].revenue_ops_cr": 1234.0,
        "history[0].ebitda_cr": 234.0,
        "history[0].pat_cr": 89.0,
        "history[0].cfo_cr": 123.0,
        "history[0].capex_cr": 45.0,
        "history[0].fcf_cr": 78.0,
        "history[0].net_worth_cr": 678.0,
        "indebtedness.secured_term_loans_cr": 200.0,
        "indebtedness.cash_and_equivalents_cr": 50.0,
    }

    for fid, exp_val in expected_facts.items():
        assert fid in fact_dict, f"Missing fact candidate in ledger: {fid}"
        f_entry = fact_dict[fid]
        assert f_entry["value"] == exp_val, f"Value mismatch for {fid}: expected {exp_val}, got {f_entry['value']}"
        assert f_entry["review"] == "UNREVIEWED", f"Expected review UNREVIEWED, got {f_entry['review']}"
        assert f_entry["origin"] == "FILING_FACT"
        assert f_entry["presence"] == "OBSERVED_VALUE"
        assert f_entry["source"]["sha256"] == ledger.digest(pdf_bytes)

    # Step 5: Verify original PDF source is retained byte-for-byte
    sources = ledger.sources(TEST_OWNER_ADMIN, company_id)
    assert len(sources) == 1
    src_meta, src_bytes = ledger.source(TEST_OWNER_ADMIN, company_id, sources[0]["id"])
    assert src_meta["sha256"] == ledger.digest(pdf_bytes)
    assert src_bytes == pdf_bytes

    # Step 6: Verify extraction run was recorded
    runs = ledger.runs(TEST_OWNER_ADMIN, company_id)
    assert len(runs) >= 1
    assert runs[0]["engine"] == "PreIPOIngestionEngine"
    assert runs[0]["status"] == "BATCH_COMPLETED"


def test_part2_duplicate_upload_idempotency_and_version_bumping():
    """Verify repeated uploads are idempotent and new filing versions create revision history."""
    with open(KNOWN_VALUES_PDF, "rb") as f:
        pdf_bytes = f.read()

    dossier = PreIPOIngestionEngine.ingest_document(io.BytesIO(pdf_bytes), company_name_hint="Idem Corp")
    meta_v1 = {
        "title": "Idem Corp DRHP",
        "filing_type": "DRHP",
        "version": "Draft 1.0",
        "available_by": str(date.today()),
        "rights": "SEBI ICDR 2018",
    }

    cid = ledger.import_dossier(TEST_OWNER_ADMIN, "admin", "Idem Corp", dossier, pdf_bytes, meta_v1)

    # First import: revision is 1
    f_v1 = next(f for f in ledger.facts(TEST_OWNER_ADMIN, cid) if f["id"] == "history[0].revenue_ops_cr")
    assert f_v1["revision"] == 1

    # Idempotent second upload of identical document and metadata: revision remains 1
    cid2 = ledger.import_dossier(TEST_OWNER_ADMIN, "admin", "Idem Corp", dossier, pdf_bytes, meta_v1)
    assert cid2 == cid
    f_v2 = next(f for f in ledger.facts(TEST_OWNER_ADMIN, cid) if f["id"] == "history[0].revenue_ops_cr")
    assert f_v2["revision"] == 1

    # Upload updated version (Draft 2.0): creates revision 2, preserving revision 1
    meta_v2 = {
        "title": "Idem Corp DRHP",
        "filing_type": "DRHP",
        "version": "Draft 2.0 (Updated)",
        "available_by": str(date.today()),
        "rights": "SEBI ICDR 2018",
    }
    ledger.import_dossier(TEST_OWNER_ADMIN, "admin", "Idem Corp", dossier, pdf_bytes, meta_v2)
    hist = ledger.history(TEST_OWNER_ADMIN, cid, "history[0].revenue_ops_cr")
    assert len(hist) == 2
    assert hist[0]["revision"] == 1
    assert hist[1]["revision"] == 2


def test_part2_role_permissions_and_viewer_restrictions():
    """Verify viewers cannot edit, import, or delete private companies."""
    with open(KNOWN_VALUES_PDF, "rb") as f:
        pdf_bytes = f.read()

    dossier = PreIPOIngestionEngine.ingest_document(io.BytesIO(pdf_bytes), company_name_hint="Secure Corp")
    meta = {
        "title": "Secure Corp DRHP",
        "filing_type": "DRHP",
        "version": "Draft 1.0",
        "available_by": str(date.today()),
        "rights": "SEBI ICDR 2018",
    }

    # Viewer cannot import
    with pytest.raises(PermissionError):
        ledger.import_dossier(TEST_VIEWER_USER, "viewer", "Secure Corp", dossier, pdf_bytes, meta)

    # Admin imports successfully
    cid = ledger.import_dossier(TEST_OWNER_ADMIN, "admin", "Secure Corp", dossier, pdf_bytes, meta)

    # Viewer cannot delete
    with pytest.raises(PermissionError):
        ledger.delete_company(TEST_OWNER_ADMIN, "viewer", cid)

    # Admin can delete
    assert ledger.delete_company(TEST_OWNER_ADMIN, "admin", cid) is True
    assert cid not in ledger.companies(TEST_OWNER_ADMIN)


def test_part2_frozen_export_consistency():
    """Verify JSON and PPTX exports consume the identical frozen snapshot."""
    with open(KNOWN_VALUES_PDF, "rb") as f:
        pdf_bytes = f.read()

    dossier = PreIPOIngestionEngine.ingest_document(io.BytesIO(pdf_bytes), company_name_hint="Export Corp")
    meta = {
        "title": "Export Corp DRHP",
        "filing_type": "DRHP",
        "version": "Draft 1.0",
        "available_by": str(date.today()),
        "rights": "SEBI ICDR 2018",
    }
    cid = ledger.import_dossier(TEST_OWNER_ADMIN, "admin", "Export Corp", dossier, pdf_bytes, meta)

    # Freeze evidence snapshot
    snap = ledger.snapshot(TEST_OWNER_ADMIN, "admin", cid, dossier, str(date.today()))
    assert "id" in snap
    assert snap["company"] == cid

    # Export JSON
    json_bytes = export_json(snap)
    parsed_json = json.loads(json_bytes.decode("utf-8"))
    assert parsed_json["id"] == snap["id"]
    assert parsed_json["company_name"] == "Export Corp"
    assert parsed_json["cutoff"] == str(date.today())

    # Export PPTX
    pptx_bytes = export_pptx(snap)
    assert len(pptx_bytes) > 10000
    assert pptx_bytes.startswith(b"PK")  # ZIP/OOXML header
