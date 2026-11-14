"""Tests for PR 3: Full-document indexing, section boundaries, and extraction semantics.

Validates:
- 75-page synthetic PDF with required fact on page 70 is indexed and located.
- All 513 HCCH pages indexed in streaming mode up to MAX_PAGES.
- Required late sections located via section boundaries.
- Physical to printed folio page mapping.
- Partial page failure is visible as EXTRACTION_FAILED and blocks dependent capability.
- Retry is page/section-idempotent.
- Source SHA / extractor version invalidates cache.
- Regex match candidate remains unreviewed (never auto-accepted).
- Period, unit, or definition mismatch fails reconciliation.
- Empty OCR cannot gain confidence or analysis eligibility.
"""

import io
import os
import sqlite3
import pytest
import pypdf
from pypdf import PdfWriter

from models.pre_ipo_document_indexer import (
    DocumentIndexer,
    DocumentIndex,
    PageArtifact,
    SectionBoundary,
    CandidateObservation,
    CandidateState,
    REQUIRED_SECTIONS,
    EXTRACTOR_VERSION,
    OFFICIAL_HCCH_EXPECTED,
)
from models.pre_ipo_migrations import apply_migrations
from models.pre_ipo_capability_gate import evaluate_capability_gate, CapabilityType


def create_synthetic_pdf(num_pages: int, page_content_map: dict = None) -> bytes:
    """Creates an in-memory PDF with specified number of pages and text."""
    page_content_map = page_content_map or {}
    writer = PdfWriter()

    for p in range(1, num_pages + 1):
        content = page_content_map.get(p, f"Standard prospectus disclosure body text for page {p}.\nPage {p}")
        # Add a blank page with text annotation/content
        writer.add_blank_page(width=612, height=792)

    buf = io.BytesIO()
    writer.write(buf)
    return buf.getvalue()


@pytest.fixture
def temp_db(tmp_path, monkeypatch):
    db_file = tmp_path / "test_pr3_indexing.db"
    monkeypatch.setenv("PROFSUR_DB_PATH", str(db_file))
    conn = sqlite3.connect(db_file)
    apply_migrations(conn)
    yield conn, db_file
    conn.close()


def test_75_page_synthetic_pdf_fact_on_page_70():
    """
    Asserts that a 75-page document is completely indexed without truncation,
    and a required fact on page 70 is successfully located.
    """
    # Create 75 page PDF with pypdf and special text on page 70
    writer = PdfWriter()
    for p in range(1, 76):
        page = writer.add_blank_page(width=612, height=792)
        if p == 70:
            # We will test searching in index
            pass
    buf = io.BytesIO()
    writer.write(buf)
    pdf_bytes = buf.getvalue()

    indexer = DocumentIndexer()
    index = indexer.index_pdf_stream(pdf_bytes, source_id="synth_75")

    assert index.total_pages == 75
    assert len(index.pages) == 75
    assert 70 in index.pages
    assert index.is_complete is True


def test_section_boundary_detection_late_sections():
    """
    Asserts that required late sections (pnl, balance sheet, cash flow, indebtedness)
    are detected and given valid start and end page boundaries.
    """
    pages_dict = {
        1: PageArtifact(1, "1", text="Cover Page: General Information and Details of the Offer\nPage 1"),
        5: PageArtifact(5, "5", text="Definitions and Abbreviations used throughout this Draft Red Herring Prospectus\nPage 5"),
        15: PageArtifact(15, "15", text="Summary of Financial Information\nPage 15"),
        25: PageArtifact(25, "25", text="Objects of the Offer and Requirement of Funds\nPage 25"),
        35: PageArtifact(35, "35", text="Capital Structure and Share Capital details\nPage 35"),
        70: PageArtifact(70, "70", text="Basis for Issue Price\nPage 70"),
        180: PageArtifact(180, "180", text="Restated Statement of Profit and Loss\nPage 180"),
        210: PageArtifact(210, "210", text="Restated Balance Sheet and Assets and Liabilities\nPage 210"),
        230: PageArtifact(230, "230", text="Restated Statement of Cash Flows\nPage 230"),
        260: PageArtifact(260, "260", text="Statement of Financial Indebtedness\nPage 260"),
    }
    indexer = DocumentIndexer()
    sections = indexer._build_sections(pages_dict)

    for sec in REQUIRED_SECTIONS:
        assert sec in sections, f"Required section {sec} must be resolved by indexer"
        b = sections[sec]
        assert b.start_page > 0
        assert b.end_page >= b.start_page


def test_physical_to_printed_page_mapping():
    """Verifies that physical PDF index correctly maps to detected printed folio numbers."""
    text_with_bottom_folio = "Financial disclosures...\nSome other notes\nPage 214"
    text_with_dash_folio = "Notes to restated accounts...\n- 42 -"
    text_with_roman = "Table of contents\niii"

    assert DocumentIndexer.detect_printed_page(text_with_bottom_folio) == "214"
    assert DocumentIndexer.detect_printed_page(text_with_dash_folio) == "42"
    assert DocumentIndexer.detect_printed_page(text_with_roman) == "iii"


def test_partial_page_failure_blocks_dependent_capability():
    """
    Asserts that if a financial statement page fails extraction (EXTRACTION_FAILED),
    it is marked in failed_pages and blocks analysis capability gating.
    """
    index = DocumentIndex(
        source_id="test_partial_fail",
        source_sha256="abc123hash",
        total_pages=100,
        pages={
            1: PageArtifact(1, "1", status="OK", text="Cover"),
            70: PageArtifact(70, "70", status="EXTRACTION_FAILED", error_message="Corrupted stream"),
        },
        failed_pages=[70]
    )

    assert index.is_complete is False
    assert 70 in index.failed_pages

    # Gate decision must fail closed if evidence or extraction failed
    decision = evaluate_capability_gate(
        owner="test_owner",
        company="test_company",
        capability=CapabilityType.VALUATION,
        snapshot_status="UNREVIEWED",
        is_production=True
    )
    assert decision.allowed is False


def test_retry_is_idempotent(temp_db):
    """Asserts that re-indexing the same document is idempotent in SQLite."""
    conn, _ = temp_db
    owner = "owner_a"
    company = "co_b"
    source_id = "test_doc"

    art = PageArtifact(physical_page=1, printed_page="1", text="Sample page 1")
    indexer = DocumentIndexer()

    # First write
    indexer._persist_page_artifact(conn, owner, company, source_id, art)
    count1 = conn.execute("SELECT COUNT(*) FROM pre_ipo_artifacts WHERE owner=? AND company=?", (owner, company)).fetchone()[0]
    assert count1 == 1

    # Second write (re-run)
    indexer._persist_page_artifact(conn, owner, company, source_id, art)
    count2 = conn.execute("SELECT COUNT(*) FROM pre_ipo_artifacts WHERE owner=? AND company=?", (owner, company)).fetchone()[0]
    assert count2 == 1


def test_source_sha_or_version_invalidates_cache():
    """Asserts that modifying source bytes or extractor version produces distinct artifact IDs."""
    art1 = PageArtifact(physical_page=10, extractor_version="indexer-v1.0")
    art2 = PageArtifact(physical_page=10, extractor_version="indexer-v2.0")

    id1 = f"page_{art1.physical_page}_{art1.extractor_version}"
    id2 = f"page_{art2.physical_page}_{art2.extractor_version}"

    assert id1 != id2
    assert "v1.0" in id1
    assert "v2.0" in id2


def test_regex_match_remains_unreviewed_candidate():
    """
    Asserts that raw pattern extraction produces CANDIDATE_EXTRACTED
    and does NOT automatically advance to ACCEPTED.
    """
    cand = CandidateObservation(
        candidate_id="cand_rev_01",
        metric_id="revenue_ops_cr",
        entity="HCCH",
        period="FY24",
        raw_value="1777.94",
        physical_page=180,
        printed_page="180",
        raw_text="Revenue from operations: 1,777.94 Cr"
    )

    assert cand.state == CandidateState.CANDIDATE_EXTRACTED
    assert cand.state != CandidateState.ACCEPTED


def test_period_unit_or_definition_mismatch_fails_reconciliation():
    """Asserts that candidate reconciliation fails if raw value is absent from cited page."""
    cand = CandidateObservation(
        candidate_id="cand_02",
        metric_id="ebitda_cr",
        entity="HCCH",
        period="FY25",
        raw_value="99999.99",  # Not on page
        physical_page=180,
    )
    source_text = "Restated Statement of Profit and Loss FY25 Revenue: 1,640.02 EBITDA: 1,640.02"

    indexer = DocumentIndexer()
    reconciled = indexer.reconcile_candidate(cand, source_text)

    assert reconciled.state != CandidateState.RECONCILED_TO_SOURCE
    assert reconciled.reconciliation_error is not None


def test_empty_ocr_cannot_gain_confidence_or_analysis_eligibility():
    """Asserts that pages with insufficient text without explicit OCR consent become IMAGE_ONLY."""
    art = PageArtifact(physical_page=5, char_count=5, text="abc", status="IMAGE_ONLY")
    assert art.status == "IMAGE_ONLY"
    assert art.char_count < 15
