"""Test suite for Pre-IPO Full Deletion Lifecycle & Referential Integrity.
Verifies withdrawal, single-document deletion, company deletion, stale-write rejection,
audit tombstones, and impact preview manifests.
"""
import os
import io
import tempfile
from pathlib import Path
from datetime import date
import pytest

# Ensure isolated test database BEFORE application imports
_TEMP_DIR = tempfile.mkdtemp(prefix="prof_test_delete_")
_TEMP_DB = str(Path(_TEMP_DIR) / "test_delete_lifecycle.db")
os.environ["PROFSUR_DB_PATH"] = _TEMP_DB

from models import pre_ipo_evidence as ledger
from models.pre_ipo_ingest import PreIPOIngestionEngine
from models.pre_ipo_decision import store as decision_store

TEST_OWNER = "test_owner_lifecycle"
OTHER_OWNER = "test_owner_isolated"

SAMPLE_PDF_BYTES = b"%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n/Pages 2 0 R\n>>\nendobj\n2 0 obj\n<<\n/Type /Pages\n/Count 1\n/Kids [3 0 R]\n>>\nendobj\n3 0 obj\n<<\n/Type /Page\n/Parent 2 0 R\n/MediaBox [0 0 612 792]\n>>\nendobj\nxref\n0 4\n0000000000 65535 f\n0000000010 00000 n\n0000000060 00000 n\n0000000090 00000 n\ntrailer\n<<\n/Size 4\n/Root 1 0 R\n>>\nstartxref\n140\n%%EOF\n"


import uuid

@pytest.fixture(autouse=True)
def clean_test_data():
    def _cleanup():
        for o in [TEST_OWNER, OTHER_OWNER]:
            try:
                for cid in list(ledger.companies(o).keys()):
                    ledger.delete_company(o, "admin", cid)
            except Exception:
                pass
    _cleanup()
    yield
    _cleanup()


def _create_sample_company_with_docs(owner=TEST_OWNER):
    """Helper to create a company with 2 sources and facts."""
    comp_name = f"Lifecycle Corp {uuid.uuid4().hex[:8]}"
    cid = ledger.create_company(owner, "admin", comp_name, "Technology", ["FY24", "FY23"])
    meta1 = {
        "title": "Lifecycle Corp DRHP",
        "filing_type": "DRHP",
        "version": "Draft 1.0",
        "available_by": str(date.today()),
        "rights": "SEBI ICDR 2018",
    }
    src1 = ledger.retain_pdf(owner, "admin", cid, SAMPLE_PDF_BYTES, meta1)

    meta2 = {
        "title": "Lifecycle Corp FY23 Annual Report",
        "filing_type": "Annual Report",
        "family": "FINANCIAL",
        "version": "Final 1.0",
        "available_by": str(date.today()),
        "rights": "MCA Filing",
    }
    # Slight variation in bytes to have different digest
    pdf2 = SAMPLE_PDF_BYTES + b"% version2\n"
    src2 = ledger.retain_pdf(owner, "admin", cid, pdf2, meta2)

    # Add a fact
    fact = {
        "id": "financial.revenue_operations",
        "value": 1500.0,
        "raw_value": 1500.0,
        "presence": "OBSERVED_VALUE",
        "origin": "FILING_FACT",
        "review": "UNREVIEWED",
        "reason": "Extracted from DRHP Section V",
        "context": {"entity": "Lifecycle Corp", "period": "FY24"},
        "source": {"id": src1, "sha256": ledger.digest(SAMPLE_PDF_BYTES), "page": 1, "locator": "Table 1", "quote": "Revenue"},
    }
    ledger.save_fact(owner, "admin", cid, fact)
    return cid, src1, src2


def test_deletion_impact_preview():
    cid, src1, src2 = _create_sample_company_with_docs()
    impact = ledger.get_deletion_impact(TEST_OWNER, cid)

    assert impact["exists"] is True
    assert impact["company_id"] == cid
    assert impact["affected_counts"]["sources"] == 2
    assert impact["affected_counts"]["facts"] >= 1
    assert impact["affected_counts"]["observations"] >= 1


def test_withdraw_source():
    cid, src1, src2 = _create_sample_company_with_docs()
    res = ledger.withdraw_source(TEST_OWNER, "admin", cid, src1, reason="Test audit withdrawal")
    assert res is True

    # Check that src1 is now marked WITHDRAWN
    with ledger.connection() as conn:
        row = conn.execute("SELECT status, generation FROM pre_ipo_sources WHERE owner=? AND company=? AND id=?", (TEST_OWNER, cid, src1)).fetchone()
        assert row["status"] == "WITHDRAWN"
        assert row["generation"] == 2

        # Check tombstone
        tomb = conn.execute("SELECT action, reason FROM pre_ipo_tombstones WHERE owner=? AND target_id=?", (TEST_OWNER, src1)).fetchone()
        assert tomb["action"] == "WITHDRAW"
        assert tomb["reason"] == "Test audit withdrawal"

        # Check observations originating from src1
        obs = conn.execute("SELECT review_state FROM pre_ipo_observations WHERE owner=? AND company=? AND source_id=?", (TEST_OWNER, cid, src1)).fetchall()
        for o in obs:
            assert o["review_state"] == "WITHDRAWN"

        # Check src2 remains active
        row2 = conn.execute("SELECT status FROM pre_ipo_sources WHERE owner=? AND company=? AND id=?", (TEST_OWNER, cid, src2)).fetchone()
        assert row2["status"] == "ACTIVE"


def test_delete_single_source_preserves_other_sources():
    cid, src1, src2 = _create_sample_company_with_docs()
    res = ledger.delete_source(TEST_OWNER, "admin", cid, src1)
    assert res is True

    with ledger.connection() as conn:
        # src1 must be gone
        row1 = conn.execute("SELECT 1 FROM pre_ipo_sources WHERE owner=? AND company=? AND id=?", (TEST_OWNER, cid, src1)).fetchone()
        assert row1 is None

        # src2 must remain
        row2 = conn.execute("SELECT 1 FROM pre_ipo_sources WHERE owner=? AND company=? AND id=?", (TEST_OWNER, cid, src2)).fetchone()
        assert row2 is not None

        # Company profile must remain
        prof = conn.execute("SELECT 1 FROM pre_ipo_company_profiles WHERE owner=? AND id=?", (TEST_OWNER, cid)).fetchone()
        assert prof is not None


def test_delete_company_purges_all_dependent_records():
    cid, src1, src2 = _create_sample_company_with_docs()

    # Link a decision case
    with ledger.connection() as conn:
        conn.execute("INSERT INTO pre_ipo_decision_versions(owner, case_id, revision, company_id, payload) VALUES (?, 'case-test-1', 1, ?, '{}')", (TEST_OWNER, cid))

    # Delete company
    res = ledger.delete_company(TEST_OWNER, "admin", cid)
    assert res is True

    with ledger.connection() as conn:
        # All company rows must be purged
        assert conn.execute("SELECT COUNT(*) FROM pre_ipo_company_profiles WHERE owner=? AND id=?", (TEST_OWNER, cid)).fetchone()[0] == 0
        assert conn.execute("SELECT COUNT(*) FROM pre_ipo_sources WHERE owner=? AND company=?", (TEST_OWNER, cid)).fetchone()[0] == 0
        assert conn.execute("SELECT COUNT(*) FROM pre_ipo_fact_events WHERE owner=? AND company=?", (TEST_OWNER, cid)).fetchone()[0] == 0
        assert conn.execute("SELECT COUNT(*) FROM pre_ipo_observations WHERE owner=? AND company=?", (TEST_OWNER, cid)).fetchone()[0] == 0
        assert conn.execute("SELECT COUNT(*) FROM pre_ipo_decision_versions WHERE owner=? AND company_id=?", (TEST_OWNER, cid)).fetchone()[0] == 0

        # Tombstone must be present
        tomb = conn.execute("SELECT action FROM pre_ipo_tombstones WHERE owner=? AND target_id=?", (TEST_OWNER, cid)).fetchone()
        assert tomb is not None
        assert tomb["action"] == "DELETE"


def test_stale_writes_rejected_after_company_deletion():
    cid, src1, src2 = _create_sample_company_with_docs()
    ledger.delete_company(TEST_OWNER, "admin", cid)

    # Attempting to save fact to deleted company must fail
    stale_fact = {
        "id": "financial.revenue_operations",
        "value": 999.0,
        "presence": "OBSERVED_VALUE",
        "origin": "FILING_FACT",
        "review": "UNREVIEWED",
        "reason": "Stale update attempt",
    }
    with pytest.raises(ValueError, match="does not exist or has been deleted"):
        ledger.save_fact(TEST_OWNER, "admin", cid, stale_fact)

    # Attempting to retain PDF to deleted company must fail
    with pytest.raises(ValueError, match="does not exist or has been deleted"):
        ledger.retain_pdf(TEST_OWNER, "admin", cid, SAMPLE_PDF_BYTES, {"title": "X", "filing_type": "DRHP", "version": "1", "available_by": str(date.today()), "rights": "R"})


def test_delete_nonexistent_company_returns_false():
    res = ledger.delete_company(TEST_OWNER, "admin", "private-nonexistent-id")
    assert res is False
