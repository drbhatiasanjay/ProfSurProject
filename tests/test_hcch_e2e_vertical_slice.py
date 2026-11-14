"""
HCCH Pre-IPO End-to-End Vertical Slice Integration Suite.
Verifies the full 18-phase implementation against the authentic 513-page HCCH DRHP:
1. Authentic 513-page document index & SHA-256 integrity
2. Canonical 513-page structured extraction service & schema 005 persistence
3. Negative parsing & unpriced DRHP NOT_DISCLOSED classification
4. Strict fail-closed gating for unreviewed/unaccepted official evidence
5. Isolated demo-fixture mode (DEMO_ACCEPTED_TEST_ONLY) under PROFSUR_DEMO_FIXTURE_MODE=1
6. Typed PreIPODealDossier adaptation & canonical snapshot hash verification
7. Valuation and reverse DCF hurdle circuit breaker: BLOCKED_MISSING_REVIEWED_PRICE_BAND
8. Production board deck generation with 3-way hash verification
9. Immutable ground-truth database preservation (capital_structure.db SHA-256 untouched)
"""

import hashlib
import json
import os
import sqlite3
import tempfile
import pytest

from models.pre_ipo_ingest import DocumentIndexer
from models.pre_ipo_extraction_service import (
    CanonicalExtractionService,
    ExtractionRequest,
    PresenceState,
    parse_financial_value,
)
from models.pre_ipo_dossier_adapter import (
    build_hcch_dossier_from_snapshot,
    compute_canonical_snapshot_hash,
)
from models.pre_ipo_dossier_resolver import (
    resolve_dossier,
    DossierResolutionStatus,
)
from models.pre_ipo_capability_gate import (
    CapabilityType,
    evaluate_capability_gate,
    assert_export_allowed,
    ExportBlockedError,
)
from models.pre_ipo_demo_fixture import seed_hcch_demo_fixture
from utils.pre_ipo_deck_generator import generate_pre_ipo_board_deck
from models.pre_ipo_migrations import apply_migrations


OFFICIAL_PDF_PATH = os.path.join(
    os.path.dirname(__file__), "..", "data", "drhp", "Hindustan_Coca_Cola_Holdings_DRHP.pdf"
)
EXPECTED_SHA256 = "3f7ba673443dbbcf2047a6b0012c025235b54c4ad920474a2d2cd9e001727bc4"


@pytest.fixture
def test_db():
    """Provides an isolated in-memory SQLite database initialized with all 5 migrations."""
    conn = sqlite3.connect(":memory:")
    apply_migrations(conn)
    yield conn
    conn.close()


# ==============================================================================
# 1. Official Corpus Integrity & Indexer Verification
# ==============================================================================
def test_official_hcch_corpus_integrity():
    assert os.path.exists(OFFICIAL_PDF_PATH), f"Official DRHP not found at {OFFICIAL_PDF_PATH}"
    with open(OFFICIAL_PDF_PATH, "rb") as f:
        content = f.read()
    computed_sha = hashlib.sha256(content).hexdigest().lower()
    assert computed_sha == EXPECTED_SHA256, f"Corpus SHA mismatch: {computed_sha} != {EXPECTED_SHA256}"
    assert len(content) == 10547638, f"Corpus byte count mismatch: {len(content)}"


# ==============================================================================
# 2. Canonical Extraction Service & Schema 005 Persistence
# ==============================================================================
def test_canonical_extraction_service_and_persistence(test_db):
    extractor = CanonicalExtractionService()
    req = ExtractionRequest(
        company="hindustan_coca_cola",
        owner="skumar",
        source_id="hcch_drhp_official_corpus",
        extractor_version="v1.0.0-canonical-513p",
    )
    result = extractor.extract_from_official_corpus(req, conn=test_db)

    assert result.total_pages == 513
    assert result.pages_indexed == 513
    assert result.status == "STRUCTURED_EXTRACTION_COMPLETE"
    assert result.candidates_extracted >= 10

    # Verify unpriced offer price fact
    offer_facts = [c for c in result.candidates if c.metric_id == "offer_price_inr"]
    assert len(offer_facts) == 1
    assert offer_facts[0].presence == PresenceState.NOT_DISCLOSED
    assert offer_facts[0].value is None

    # Verify persistence in schema 005 tables
    run_row = test_db.execute(
        "SELECT total_pages, pages_indexed, status FROM pre_ipo_extraction_runs WHERE id=?",
        (result.run_id,)
    ).fetchone()
    assert run_row == (513, 513, "STRUCTURED_EXTRACTION_COMPLETE")

    pages_count = test_db.execute(
        "SELECT COUNT(*) FROM pre_ipo_page_artifacts WHERE run_id=?",
        (result.run_id,)
    ).fetchone()[0]
    assert pages_count == 513

    cand_count = test_db.execute(
        "SELECT COUNT(*) FROM pre_ipo_candidate_facts WHERE run_id=?",
        (result.run_id,)
    ).fetchone()[0]
    assert cand_count == result.candidates_extracted


# ==============================================================================
# 3. Financial Value Parser (Negative Parens & Dash Classification)
# ==============================================================================
def test_financial_value_parser():
    # Normal numbers
    val, pres = parse_financial_value("14,242.40")
    assert float(val) == 14242.40
    assert pres == PresenceState.OBSERVED_VALUE

    # Negative in parentheses
    val_neg, pres_neg = parse_financial_value("(1,032.50)")
    assert float(val_neg) == -1032.50
    assert pres_neg == PresenceState.OBSERVED_VALUE

    # Explicit nil
    val_nil, pres_nil = parse_financial_value("Nil")
    assert float(val_nil) == 0.0
    assert pres_nil == PresenceState.EXPLICIT_NIL

    val_dash, pres_dash = parse_financial_value("-")
    assert float(val_dash) == 0.0
    assert pres_dash == PresenceState.EXPLICIT_NIL

    # Undisclosed / empty
    val_blank, pres_blank = parse_financial_value("[•]")
    assert val_blank is None
    assert pres_blank == PresenceState.NOT_DISCLOSED


# ==============================================================================
# 4. Strict Fail-Closed Containment (Official Mode)
# ==============================================================================
def test_unreviewed_official_hcch_remains_strictly_blocked(test_db, monkeypatch):
    monkeypatch.delenv("PROFSUR_DEMO_FIXTURE_MODE", raising=False)
    monkeypatch.delenv("ENVIRONMENT", raising=False)

    # 1. No snapshot
    res_none = resolve_dossier(
        selected_deal_key="hindustan_coca_cola",
        owner="profsurkumar",
        snapshot_id=None,
        conn=test_db,
    )
    assert res_none.status == DossierResolutionStatus.BLOCKED_EVIDENCE_NOT_ACCEPTED
    assert res_none.dossier is None

    # 2. Unreviewed snapshot in DB
    dummy_hash = "a" * 64
    test_db.execute("""
        INSERT INTO pre_ipo_evidence_snapshots (id, owner, company, payload, status, snapshot_hash, accepted_by, accepted_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, ("snap_unreviewed", "profsurkumar", "hindustan_coca_cola", json.dumps({}), "UNREVIEWED", dummy_hash, "", ""))
    test_db.commit()

    res_unrev = resolve_dossier(
        selected_deal_key="hindustan_coca_cola",
        owner="profsurkumar",
        snapshot_id="snap_unreviewed",
        conn=test_db,
    )
    assert res_unrev.status == DossierResolutionStatus.BLOCKED_EVIDENCE_NOT_ACCEPTED

    # 3. Capability gate blocks unreviewed snapshot
    cap_dec = evaluate_capability_gate(
        owner="profsurkumar",
        company="hindustan_coca_cola",
        capability=CapabilityType.FINANCIAL_ANALYSIS,
        snapshot_id="snap_unreviewed",
        conn=test_db,
        is_production=True,
    )
    assert not cap_dec.allowed
    assert cap_dec.status == "BLOCKED"


# ==============================================================================
# 5. Demo-Fixture Mode (Phase G End-to-End)
# ==============================================================================
def test_demo_fixture_mode_lifecycle(test_db, monkeypatch):
    monkeypatch.setenv("PROFSUR_DEMO_FIXTURE_MODE", "1")
    monkeypatch.setenv("ENVIRONMENT", "demo")

    # 1. Seed demo fixture
    fixture = seed_hcch_demo_fixture(
        owner="drbhatia",
        company="hindustan_coca_cola",
        conn=test_db,
        force=True,
    )
    snap_id = fixture["snapshot_id"]
    snap_hash = fixture["snapshot_hash"]
    assert fixture["status"] == "DEMO_ACCEPTED_TEST_ONLY"
    assert len(snap_hash) == 64

    # 2. Resolve dossier via typed adapter
    res = resolve_dossier(
        selected_deal_key="hindustan_coca_cola",
        owner="drbhatia",
        snapshot_id=snap_id,
        conn=test_db,
    )
    assert res.status == DossierResolutionStatus.READY
    assert res.origin == "DEMO_FIXTURE"
    assert res.snapshot_hash == snap_hash
    dossier = res.dossier
    assert dossier is not None
    assert "Hindustan Coca-Cola" in dossier.company_name
    assert dossier.latest_financials.revenue_ops_cr > 10000.0  # FY24 ~14,242 Cr

    # 3. Capability gate: Financial Analysis allowed, but Valuation/WACC/DCF BLOCKED
    fin_dec = evaluate_capability_gate(
        owner="drbhatia",
        company="hindustan_coca_cola",
        capability=CapabilityType.FINANCIAL_ANALYSIS,
        snapshot_id=snap_id,
        snapshot_hash=snap_hash,
        conn=test_db,
        is_production=True,
        is_unpriced=True,
    )
    assert fin_dec.allowed is True
    assert fin_dec.status == "ACCEPTED_FOR_ANALYSIS"

    # Circuit breaker: Valuation and Reverse DCF must remain strictly BLOCKED_MISSING_REVIEWED_PRICE_BAND
    val_dec = evaluate_capability_gate(
        owner="drbhatia",
        company="hindustan_coca_cola",
        capability=CapabilityType.VALUATION,
        snapshot_id=snap_id,
        snapshot_hash=snap_hash,
        conn=test_db,
        is_production=True,
        is_unpriced=True,
    )
    assert val_dec.allowed is False
    assert val_dec.status == "BLOCKED_MISSING_REVIEWED_PRICE_BAND"

    dcf_dec = evaluate_capability_gate(
        owner="drbhatia",
        company="hindustan_coca_cola",
        capability=CapabilityType.REVERSE_DCF,
        snapshot_id=snap_id,
        snapshot_hash=snap_hash,
        conn=test_db,
        is_production=True,
        is_unpriced=True,
    )
    assert dcf_dec.allowed is False
    assert dcf_dec.status == "BLOCKED_MISSING_REVIEWED_PRICE_BAND"

    # 4. Generate board deck with 3-way hash verification
    deck_bytes = generate_pre_ipo_board_deck(
        dossier=dossier,
        snapshot_id=snap_id,
        snapshot_status="DEMO_ACCEPTED_TEST_ONLY",
        snapshot_hash=snap_hash,
        result_snapshot_hash=snap_hash,
        owner="drbhatia",
        company="hindustan_coca_cola",
        conn=test_db,
        is_production=True,
    )
    assert isinstance(deck_bytes, bytes)
    assert len(deck_bytes) > 10000
    assert deck_bytes[:4] == b"PK\x03\x04"  # PPTX / ZIP header


# ==============================================================================
# 6. Rejection of Demo Fixture in Production Mode
# ==============================================================================
def test_demo_fixture_rejected_when_not_in_demo_mode(test_db, monkeypatch):
    # Ensure production environment
    monkeypatch.delenv("PROFSUR_DEMO_FIXTURE_MODE", raising=False)
    monkeypatch.delenv("ENVIRONMENT", raising=False)

    # Directly insert a snapshot with DEMO_ACCEPTED_TEST_ONLY
    snap_hash = "b" * 64
    test_db.execute("""
        INSERT INTO pre_ipo_evidence_snapshots (id, owner, company, payload, status, snapshot_hash, accepted_by, accepted_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, ("snap_demo_in_prod", "drbhatia", "hindustan_coca_cola", json.dumps({}), "DEMO_ACCEPTED_TEST_ONLY", snap_hash, "auditor", "2026-11-14"))
    test_db.commit()

    # In production, this snapshot is rejected
    res = resolve_dossier(
        selected_deal_key="hindustan_coca_cola",
        owner="drbhatia",
        snapshot_id="snap_demo_in_prod",
        conn=test_db,
    )
    assert res.status == DossierResolutionStatus.BLOCKED_EVIDENCE_NOT_ACCEPTED

    # Export raises ExportBlockedError
    class MockDossier:
        company_name = "Hindustan Coca-Cola Beverages"
        deal_id = "hindustan_coca_cola"

    with pytest.raises(ExportBlockedError):
        assert_export_allowed(
            dossier=MockDossier(),
            snapshot_id="snap_demo_in_prod",
            snapshot_hash=snap_hash,
            result_snapshot_hash=snap_hash,
            owner="drbhatia",
            company="hindustan_coca_cola",
            conn=test_db,
            is_production=True,
        )


# ==============================================================================
# 7. Ground Truth capital_structure.db Immutability Check
# ==============================================================================
def test_production_db_immutability():
    db_path = os.path.join(os.path.dirname(__file__), "..", "capital_structure.db")
    if os.path.exists(db_path):
        with open(db_path, "rb") as f:
            db_sha = hashlib.sha256(f.read()).hexdigest().upper()
        assert db_sha == "CA696195A5C541B56E0533DE6C69A3BEC4E501A232FD2B18A1B09D15D6FA7873", (
            f"FATAL: Production capital_structure.db was modified! SHA: {db_sha}"
        )
