"""Test suite for Phase 1: Official Filing Candidate Extraction Pipeline.

Verifies:
1. Candidate observation extraction parses table rows and values dynamically from page text.
2. Emitted observations strictly have review_state="PROPOSED", never auto-ACCEPTED.
3. Observations contain all 9 mandatory audit fields.
4. Persistence stores candidate observations strictly as UNREVIEWED.
5. Explicit human review (accept_candidate_observation) is required to transition to ACCEPTED.
6. Unreviewed observations cannot bypass capability gates.
"""

import os
import sqlite3
import pytest
from datetime import datetime, timezone

from models.pre_ipo_document_indexer import (
    DocumentIndexer,
    DocumentIndex,
    PageArtifact,
    CandidateObservation,
    CandidateState,
    accept_candidate_observation,
    OFFICIAL_HCCH_EXPECTED,
)
from models.pre_ipo_migrations import apply_migrations
from models.pre_ipo_capability_gate import evaluate_capability_gate, CapabilityType

OFFICIAL_PDF_PATH = os.path.join("data", "drhp", "Hindustan_Coca_Cola_Holdings_DRHP.pdf")


@pytest.fixture
def test_db():
    conn = sqlite3.connect(":memory:")
    apply_migrations(conn)
    yield conn
    conn.close()


def test_dynamic_table_extraction_audit_attributes(test_db):
    """Verify that candidate extraction produces PROPOSED observations with all 9 audit fields."""
    if not os.path.exists(OFFICIAL_PDF_PATH):
        pytest.skip(f"Official HCCH DRHP PDF not present on disk at {OFFICIAL_PDF_PATH}")
    with open(OFFICIAL_PDF_PATH, "rb") as f:
        pdf_bytes = f.read()

    indexer = DocumentIndexer(max_pages=300)
    doc_index = indexer.index_pdf_stream(
        pdf_bytes=pdf_bytes,
        source_id="official_hcch_drhp",
        allow_ocr=False,
        conn=test_db,
        owner="profsurkumar",
        company="coca_cola"
    )

    observations = indexer.extract_hcch_gold_observations(
        doc_index=doc_index,
        conn=test_db,
        owner="profsurkumar",
        company="coca_cola"
    )

    assert len(observations) >= 11

    # Verify every single observation satisfies the strict candidate contract
    mandatory_fields = [
        "document_sha256",
        "physical_page",
        "printed_page",
        "table_id",
        "row_label",
        "column_label",
        "raw_text",
        "value",
        "unit"
    ]

    for obs in observations:
        for field_name in mandatory_fields:
            assert field_name in obs, f"Observation {obs.get('metric_id')} missing mandatory field '{field_name}'"
            assert obs[field_name] is not None, f"Observation {obs.get('metric_id')} has None for '{field_name}'"

        # Contract Rule: review_state must be PROPOSED, NEVER auto-accepted
        assert obs["review_state"] == "PROPOSED", (
            f"Extraction auto-accepted observation '{obs['metric_id']}'. "
            "Observations must remain PROPOSED until human review."
        )
        assert obs["extraction_method"] == "REGEX_TABLE_PARSER_V1"
        assert obs["confidence"] == 0.95
        assert isinstance(obs["warnings"], list)


def test_sqlite_persistence_remains_unreviewed(test_db):
    """Verify that observations written to SQLite have review_state='UNREVIEWED' (zero auto-accepted)."""
    if not os.path.exists(OFFICIAL_PDF_PATH):
        pytest.skip(f"Official HCCH DRHP PDF not present on disk at {OFFICIAL_PDF_PATH}")
    with open(OFFICIAL_PDF_PATH, "rb") as f:
        pdf_bytes = f.read()

    indexer = DocumentIndexer(max_pages=300)
    doc_index = indexer.index_pdf_stream(
        pdf_bytes=pdf_bytes,
        source_id="official_hcch_drhp",
        allow_ocr=False,
        conn=test_db,
        owner="profsurkumar",
        company="coca_cola"
    )

    indexer.extract_hcch_gold_observations(
        doc_index=doc_index,
        conn=test_db,
        owner="profsurkumar",
        company="coca_cola"
    )

    cursor = test_db.cursor()

    # Zero auto-accepted rows
    cursor.execute("SELECT count(*) FROM pre_ipo_observations WHERE review_state = 'ACCEPTED'")
    accepted_count = cursor.fetchone()[0]
    assert accepted_count == 0, f"Found {accepted_count} auto-accepted observations in SQLite! Must be 0."

    # All candidate rows must be UNREVIEWED
    cursor.execute("SELECT count(*) FROM pre_ipo_observations WHERE review_state = 'UNREVIEWED'")
    unreviewed_count = cursor.fetchone()[0]
    assert unreviewed_count >= 11


def test_human_acceptance_lifecycle(test_db):
    """Verify the explicit human review and acceptance lifecycle."""
    if not os.path.exists(OFFICIAL_PDF_PATH):
        pytest.skip(f"Official HCCH DRHP PDF not present on disk at {OFFICIAL_PDF_PATH}")
    with open(OFFICIAL_PDF_PATH, "rb") as f:
        pdf_bytes = f.read()

    indexer = DocumentIndexer(max_pages=300)
    doc_index = indexer.index_pdf_stream(
        pdf_bytes=pdf_bytes,
        source_id="official_hcch_drhp",
        allow_ocr=False,
        conn=test_db,
        owner="profsurkumar",
        company="coca_cola"
    )

    indexer.extract_hcch_gold_observations(
        doc_index=doc_index,
        conn=test_db,
        owner="profsurkumar",
        company="coca_cola"
    )

    target_obs_id = f"obs_total_equity_cr_FY26_{doc_index.source_id}"

    # 1. Unreviewed initially
    cursor = test_db.cursor()
    cursor.execute("SELECT review_state, reviewer FROM pre_ipo_observations WHERE observation_id = ?", (target_obs_id,))
    row = cursor.fetchone()
    assert row[0] == "UNREVIEWED"
    assert row[1] is None

    # 2. Reject anonymous acceptance
    with pytest.raises(ValueError, match="identified reviewer"):
        accept_candidate_observation(
            conn=test_db,
            owner="profsurkumar",
            company="coca_cola",
            observation_id=target_obs_id,
            reviewer="",
            review_reason="Checked"
        )

    # 3. Reject acceptance without rationale
    with pytest.raises(ValueError, match="review_reason"):
        accept_candidate_observation(
            conn=test_db,
            owner="profsurkumar",
            company="coca_cola",
            observation_id=target_obs_id,
            reviewer="drbhatia",
            review_reason="  "
        )

    # 4. Valid human acceptance transitions observation
    res = accept_candidate_observation(
        conn=test_db,
        owner="profsurkumar",
        company="coca_cola",
        observation_id=target_obs_id,
        reviewer="drbhatia",
        review_reason="Audited against Annexure I p. 269 of SEBI filing"
    )
    assert res["review_state"] == "ACCEPTED"
    assert res["reviewer"] == "drbhatia"

    cursor.execute("SELECT review_state, reviewer, review_reason FROM pre_ipo_observations WHERE observation_id = ?", (target_obs_id,))
    row = cursor.fetchone()
    assert row[0] == "ACCEPTED"
    assert row[1] == "drbhatia"
    assert "Audited against Annexure I" in row[2]


def test_unreviewed_candidates_fail_closed_at_capability_gate(test_db):
    """Asserts that unreviewed observations fail closed at the capability gate."""
    # Attempting to query capability gate with an unreviewed snapshot must fail closed
    decision = evaluate_capability_gate(
        owner="profsurkumar",
        company="coca_cola",
        capability=CapabilityType.FINANCIAL_ANALYSIS,
        snapshot_id="unreviewed_candidate_snapshot",
        snapshot_status="UNREVIEWED",
        is_production=True
    )
    assert decision.allowed is False
    assert "accepted" in decision.reason.lower() or "unreviewed" in decision.reason.lower()
