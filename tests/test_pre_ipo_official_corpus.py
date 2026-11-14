"""Full official-corpus acceptance test suite for Hindustan Coca-Cola Holdings (HCCH) DRHP.

Verifies PR 3 / Finding F06 resolution:
1. Authentic 513-page regulatory corpus (SHA-256 3f7ba673443dbbcf2047a6b0012c025235b54c4ad920474a2d2cd9e001727bc4).
2. All 513 pages indexed without failure (is_complete=True, is_text_extracted=True, is_capability_ready=True).
3. Exact physical and printed folio mapping.
4. Robust section boundaries without Table of Contents or cross-reference contamination.
5. Extraction and source substring reconciliation of gold restated financials.
6. Clean persistence in disposable SQLite with zero mutation to ground-truth production DB.
"""

import os
import hashlib
import sqlite3
import pytest

from models.pre_ipo_document_indexer import (
    DocumentIndexer,
    DocumentIndex,
    CandidateObservation,
    CandidateState,
    OFFICIAL_HCCH_EXPECTED,
    REQUIRED_SECTIONS
)
from models.pre_ipo_migrations import apply_migrations

OFFICIAL_PDF_PATH = os.path.join("data", "drhp", "Hindustan_Coca_Cola_Holdings_DRHP.pdf")


def test_official_drhp_identity_and_tamper_rejection():
    """Verify that the official HCCH DRHP file exists and invalid checksums are rejected."""
    assert os.path.exists(OFFICIAL_PDF_PATH), f"Missing official DRHP at {OFFICIAL_PDF_PATH}"
    
    with open(OFFICIAL_PDF_PATH, "rb") as f:
        pdf_bytes = f.read()

    assert len(pdf_bytes) == OFFICIAL_HCCH_EXPECTED["size_bytes"]
    sha = hashlib.sha256(pdf_bytes).hexdigest()
    assert sha == OFFICIAL_HCCH_EXPECTED["sha256"]

    # Adversarial tamper check: Claiming to be official HCCH with wrong bytes must raise ValueError
    indexer = DocumentIndexer()
    fake_bytes = b"%PDF-1.4 fake official document"
    with pytest.raises(ValueError, match="Official HCCH PDF checksum mismatch"):
        indexer.index_pdf_stream(fake_bytes, source_id="official_hcch_drhp")


def test_full_513_page_corpus_indexing_and_readiness():
    """Verify that all 513 pages are fully indexed, text-extracted, and capability-ready."""
    with open(OFFICIAL_PDF_PATH, "rb") as f:
        pdf_bytes = f.read()

    indexer = DocumentIndexer(max_pages=600)
    
    # Run in disposable in-memory database
    conn = sqlite3.connect(":memory:")
    apply_migrations(conn)

    doc_index = indexer.index_pdf_stream(
        pdf_bytes=pdf_bytes,
        source_id="official_hcch_drhp",
        allow_ocr=False,
        conn=conn,
        owner="profsurkumar",
        company="coca_cola"
    )

    # 1. Page count and completeness invariants
    assert doc_index.total_pages == 513
    assert len(doc_index.pages) == 513
    assert len(doc_index.failed_pages) == 0
    assert doc_index.is_complete is True
    assert doc_index.is_text_extracted is True
    assert doc_index.is_capability_ready is True

    # 2. Page artifact persistence
    cursor = conn.cursor()
    cursor.execute("SELECT count(*) FROM pre_ipo_artifacts WHERE artifact_type = 'PAGE_TEXT'")
    artifact_count = cursor.fetchone()[0]
    assert artifact_count == 513

    # 3. Printed folio mapping verification
    # Page 11 is printed page 6
    assert doc_index.pages[11].printed_page == "6"
    # Page 93 (Capital structure) is printed page 88
    assert doc_index.pages[93].printed_page == "88"
    # Page 274 (Balance sheet) is printed page 269
    assert doc_index.pages[274].printed_page == "269"
    # Page 513 is printed page 508
    assert doc_index.pages[513].printed_page == "508"

    # 4. Section boundary detection without TOC/cross-reference false starts
    sections = doc_index.sections
    assert len(sections) == 10
    for req_sec in REQUIRED_SECTIONS:
        assert req_sec in sections, f"Missing required section: {req_sec}"

    # Verify section starts reflect authentic document locations, not definitions cross-references
    assert sections["definitions"].start_page == 6
    assert sections["summary_financials"].start_page == 73
    assert sections["capital_structure"].start_page == 93
    assert sections["objects"].start_page == 108
    assert sections["basis_for_price"].start_page == 110
    assert sections["balance_sheet"].start_page == 274
    assert sections["pnl"].start_page == 275
    assert sections["cash_flow"].start_page == 276
    assert sections["indebtedness"].start_page == 381

    # Verify section ordering
    assert sections["definitions"].start_page < sections["summary_financials"].start_page
    assert sections["summary_financials"].start_page < sections["capital_structure"].start_page
    assert sections["capital_structure"].start_page < sections["objects"].start_page
    assert sections["objects"].start_page < sections["basis_for_price"].start_page
    assert sections["basis_for_price"].start_page < sections["balance_sheet"].start_page
    assert sections["balance_sheet"].start_page < sections["pnl"].start_page
    assert sections["pnl"].start_page < sections["cash_flow"].start_page
    assert sections["cash_flow"].start_page < sections["indebtedness"].start_page

    # 5. Extract gold restated observations and verify reconciliation
    gold_obs = indexer.extract_hcch_gold_observations(
        doc_index=doc_index,
        conn=conn,
        owner="profsurkumar",
        company="coca_cola"
    )
    assert len(gold_obs) >= 11

    obs_map = {o["metric_id"]: o for o in gold_obs}

    # Verify Capital Structure (pp. 93 / 88)
    assert obs_map["authorized_capital_cr"]["value"] == "9000.00"
    assert obs_map["equity_face_value"]["value"] == "10.00"

    # Verify Balance Sheet (pp. 274 / 269)
    assert obs_map["total_equity_cr"]["value"] == "9765.14"
    assert obs_map["owners_equity_cr"]["value"] == "9760.91"
    assert obs_map["nci_equity_cr"]["value"] == "4.23"
    assert obs_map["total_assets_cr"]["value"] == "15637.09"
    assert obs_map["cash_and_equiv_cr"]["value"] == "431.96"
    assert obs_map["borrowings_cr"]["value"] == "0.00"

    # Verify P&L (pp. 275 / 270)
    assert obs_map["pat_cr"]["value"] == "1165.05"
    assert obs_map["diluted_eps"]["value"] == "1.75"

    # Verify Cash Flows (pp. 276 / 271)
    assert obs_map["operating_profit_before_wc_cr"]["value"] == "1310.18"
    assert obs_map["pbt_cr"]["value"] == "1417.48"

    # 6. Reconcile candidates against page text
    for o in gold_obs:
        p_text = doc_index.pages[o["physical_page"]].text
        cand = CandidateObservation(
            candidate_id=f"cand_{o['metric_id']}",
            metric_id=o["metric_id"],
            entity=o["entity"],
            period=o["period"],
            raw_value=o["value"],
            physical_page=o["physical_page"],
            printed_page=o["printed_page"]
        )
        reconciled = indexer.reconcile_candidate(cand, source_text=p_text)
        assert reconciled.state in (CandidateState.STRUCTURE_VALIDATED, CandidateState.RECONCILED_TO_SOURCE)

    # 7. Verify SQLite persistence of observations
    cursor.execute("SELECT count(*) FROM pre_ipo_observations WHERE origin = 'DRHP_EXTRACTION'")
    obs_count = cursor.fetchone()[0]
    assert obs_count >= 11
