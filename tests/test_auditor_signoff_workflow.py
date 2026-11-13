"""Adversarial Red-Team & Validation Suite for Auditor Fact Sign-Off & Citation Inspector.

Tests Item 1 & Item 4:
1. `record_observation_review()` records valid reviews into SQLite.
2. An anonymous or empty reviewer is rejected (fail-closed security).
3. Accepting a fact requires a non-empty audit rationale.
4. Flagging a discrepancy sets state to 'DISPUTED' or 'REJECTED' with reason.
5. In-memory single-page PDF slice extraction returns a valid 1-page PDF.
6. Extraction page out-of-bounds raises ValueError.
"""

import pytest
import sqlite3
import io
import pypdf
from models.pre_ipo_evidence import (
    record_observation_review,
    get_observation_review,
    connection,
    Observation,
    SourceLocator,
)
from models.pre_ipo_document_indexer import (
    extract_single_page_bytes,
    extract_page_slice_text,
    DocumentIndex,
    PageArtifact,
)
from models.pre_ipo_migrations import apply_migrations


@pytest.fixture
def test_db():
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    apply_migrations(conn)
    yield conn
    conn.close()


def test_record_observation_review_success(test_db):
    """Test successful auditor acceptance of a statutory fact."""
    # Insert dummy observation
    test_db.execute("""
        INSERT INTO pre_ipo_observations (
            owner, company, observation_id, revision, source_id, entity, metric_id,
            period, value, presence, review_state, physical_page, printed_page,
            table_id, raw_text, origin
        ) VALUES (
            'drbhatia', 'hindustan_coca_cola', 'obs-rev-01', 1, 'src-hcch', 'HCCH', 'revenue_ops_cr',
            'FY24', '14021.55', 'OBSERVED_VALUE', 'UNREVIEWED', 68, 'Page 58',
            'Restated Summary Statement of Profit and Loss', 'Revenue: Rs. 140,215.45 Mn', 'FILING_FACT'
        )
    """)
    test_db.commit()

    res = record_observation_review(
        conn=test_db,
        owner="drbhatia",
        company="hindustan_coca_cola",
        observation_id="obs-rev-01",
        review_state="ACCEPTED",
        reviewer="drbhatia",
        review_reason="Reconciled against Restated Summary P&L Annexure I on physical page 68.",
        revision=1,
    )
    assert res is not None
    assert res["review_state"] == "ACCEPTED"
    assert res["reviewer"] == "drbhatia"
    assert "Reconciled" in res["review_reason"]

    # Verify persisted in database
    row = test_db.execute(
        "SELECT review_state, reviewer, review_reason FROM pre_ipo_observations WHERE observation_id='obs-rev-01'"
    ).fetchone()
    assert row["review_state"] == "ACCEPTED"
    assert row["reviewer"] == "drbhatia"


def test_adversarial_anonymous_signoff_rejected(test_db):
    """Adversarial check: Anonymous or whitespace-only reviewer must fail-closed."""
    with pytest.raises(ValueError, match="identified reviewer|Anonymous"):
        record_observation_review(
            conn=test_db,
            owner="drbhatia",
            company="hindustan_coca_cola",
            observation_id="obs-rev-02",
            review_state="ACCEPTED",
            reviewer="",  # Anonymous bypass attempt
            review_reason="Looks good",
        )


def test_adversarial_empty_reason_rejected(test_db):
    """Adversarial check: Acceptance without explicit rationale must fail-closed."""
    with pytest.raises(ValueError, match="explicit review_reason|rationale"):
        record_observation_review(
            conn=test_db,
            owner="drbhatia",
            company="hindustan_coca_cola",
            observation_id="obs-rev-03",
            review_state="ACCEPTED",
            reviewer="drbhatia",
            review_reason="   ",  # Blank rationale
        )


def test_flag_discrepancy_workflow(test_db):
    """Test flagging a fact discrepancy for audit re-examination."""
    test_db.execute("""
        INSERT INTO pre_ipo_observations (
            owner, company, observation_id, revision, source_id, entity, metric_id,
            period, value, presence, review_state, physical_page, origin
        ) VALUES (
            'drbhatia', 'swiggy', 'obs-disc-01', 1, 'src-swiggy', 'Swiggy', 'pat_cr',
            'FY24', '-2350.24', 'OBSERVED_VALUE', 'UNREVIEWED', 240, 'FILING_FACT'
        )
    """)
    test_db.commit()

    res = record_observation_review(
        conn=test_db,
        owner="drbhatia",
        company="swiggy",
        observation_id="obs-disc-01",
        review_state="DISPUTED",
        reviewer="profsurkumar",
        review_reason="Variance detected against footnote 14 regarding share-based payments.",
        revision=1,
    )
    assert res["review_state"] == "DISPUTED"
    assert res["reviewer"] == "profsurkumar"


def test_extract_single_page_bytes_valid():
    """Verify single-page PDF slice extraction generates a valid 1-page PDF."""
    # Create a synthetic 3-page PDF in memory
    writer = pypdf.PdfWriter()
    writer.add_blank_page(width=612, height=792)
    writer.add_blank_page(width=612, height=792)
    writer.add_blank_page(width=612, height=792)
    buf = io.BytesIO()
    writer.write(buf)
    pdf_bytes = buf.getvalue()

    # Extract page 2
    slice_bytes = extract_single_page_bytes(pdf_bytes, physical_page=2)
    assert slice_bytes is not None
    assert len(slice_bytes) > 0

    # Read slice back and verify exactly 1 page
    slice_reader = pypdf.PdfReader(io.BytesIO(slice_bytes))
    assert len(slice_reader.pages) == 1


def test_extract_single_page_bytes_out_of_bounds():
    """Verify out-of-bounds page numbers raise ValueError."""
    writer = pypdf.PdfWriter()
    writer.add_blank_page(width=612, height=792)
    buf = io.BytesIO()
    writer.write(buf)
    pdf_bytes = buf.getvalue()

    with pytest.raises(ValueError, match="out of bounds"):
        extract_single_page_bytes(pdf_bytes, physical_page=0)

    with pytest.raises(ValueError, match="out of bounds"):
        extract_single_page_bytes(pdf_bytes, physical_page=999)
