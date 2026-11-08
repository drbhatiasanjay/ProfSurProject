"""Integration acceptance test suite for Pre-IPO Part 2.
Verifies end-to-end connection between Part 1 ingestion and owner-scoped evidence ledger.
"""
import os
import io
import json
import pytest
from datetime import date
from models.pre_ipo_ingest import PreIPOIngestionEngine
from models import pre_ipo_evidence as ledger
from utils.pre_ipo_evidence_export import export_json, export_pptx
from models.pre_ipo_custom_store import migrate_legacy_pickle

KNOWN_VALUES_PDF = r"C:\Users\hemas\.codex\worktrees\profsur-decision-depth\ProfSurProject\scratch\ingestion_assessment_20261108\known-values.pdf"


@pytest.fixture(autouse=True)
def clean_test_companies():
    """Ensure clean ledger before and after tests."""
    yield
    for owner in ["drbhatia", "profsurkumar", "test_user_alpha", "skumar", "sbhatia"]:
        try:
            for cid in list(ledger.companies(owner).keys()):
                ledger.delete_company(owner, "admin", cid)
        except Exception:
            pass


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
    company_id = ledger.import_dossier("drbhatia", "admin", "Fresh Venture Corp", dossier, pdf_bytes, meta)
    assert company_id.startswith("private-")

    # Step 3: Verify company appears in owner's profile, but NOT in another owner's profile
    dr_companies = ledger.companies("drbhatia")
    assert company_id in dr_companies
    assert dr_companies[company_id].company_name == "Fresh Venture Corp"

    # Isolation check: profsurkumar must NOT see drbhatia's private company
    prof_companies = ledger.companies("profsurkumar")
    assert company_id not in prof_companies

    # Step 4: Verify facts in ledger match exact Part 1 extracted numbers
    facts = ledger.facts("drbhatia", company_id)
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
    sources = ledger.sources("drbhatia", company_id)
    assert len(sources) == 1
    src_meta, src_bytes = ledger.source("drbhatia", company_id, sources[0]["id"])
    assert src_meta["sha256"] == ledger.digest(pdf_bytes)
    assert src_bytes == pdf_bytes

    # Step 6: Verify extraction run was recorded
    runs = ledger.runs("drbhatia", company_id)
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

    cid = ledger.import_dossier("drbhatia", "admin", "Idem Corp", dossier, pdf_bytes, meta_v1)

    # First import: revision is 1
    f_v1 = next(f for f in ledger.facts("drbhatia", cid) if f["id"] == "history[0].revenue_ops_cr")
    assert f_v1["revision"] == 1

    # Idempotent second upload of identical document and metadata: revision remains 1
    cid2 = ledger.import_dossier("drbhatia", "admin", "Idem Corp", dossier, pdf_bytes, meta_v1)
    assert cid2 == cid
    f_v2 = next(f for f in ledger.facts("drbhatia", cid) if f["id"] == "history[0].revenue_ops_cr")
    assert f_v2["revision"] == 1

    # Upload updated version (Draft 2.0): creates revision 2, preserving revision 1
    meta_v2 = {
        "title": "Idem Corp DRHP",
        "filing_type": "DRHP",
        "version": "Draft 2.0 (Updated)",
        "available_by": str(date.today()),
        "rights": "SEBI ICDR 2018",
    }
    ledger.import_dossier("drbhatia", "admin", "Idem Corp", dossier, pdf_bytes, meta_v2)
    hist = ledger.history("drbhatia", cid, "history[0].revenue_ops_cr")
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
        ledger.import_dossier("skumar", "viewer", "Secure Corp", dossier, pdf_bytes, meta)

    # Admin imports successfully
    cid = ledger.import_dossier("drbhatia", "admin", "Secure Corp", dossier, pdf_bytes, meta)

    # Viewer cannot delete
    with pytest.raises(PermissionError):
        ledger.delete_company("drbhatia", "viewer", cid)

    # Admin can delete
    assert ledger.delete_company("drbhatia", "admin", cid) is True
    assert cid not in ledger.companies("drbhatia")


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
    cid = ledger.import_dossier("drbhatia", "admin", "Export Corp", dossier, pdf_bytes, meta)

    # Freeze evidence snapshot
    snap = ledger.snapshot("drbhatia", "admin", cid, dossier, str(date.today()))
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
