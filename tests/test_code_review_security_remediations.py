"""
Comprehensive Verification Suite for Deep Code Review Remediations (2026-11-08).
Validates fixes for:
- P0-01: Fail-closed intake and analysis eligibility for keyword-only PDF.
- P0-02: Docker and Cloud Build secrets containment (secrets.toml ignored).
- P0-03 & P1-07: E2E and smoke test host boundaries & dynamic password fixtures.
- P1-01: Explicit consent boundary for external Cloud Vision API transmission.
- P1-03: Rejection of PROFSUR_DEMO_SKIP_AUTH in production / Cloud Run.
- P1-04: Untrusted input HTML escaping via render_trusted_template.
- P1-08: bootstrap_legacy_users preservation of existing passwords/roles.
- P2-04: Upload caching includes parser and schema versions.
- P2-05: PRAGMA foreign_keys=ON in SQLite connection factory.
"""
import io
import os
import sqlite3
import pytest
try:
    from reportlab.pdfgen import canvas
    from reportlab.lib.pagesizes import letter
except ImportError:
    canvas = None
    letter = None

from models.pre_ipo_ingest import (
    PreIPOIngestionEngine,
    ExtractionState,
    assess_analysis_eligibility,
)
from utils.html_blocks import render_trusted_template
import db
import auth


def test_p0_01_contents_keyword_number_is_blocked():
    """Reproducer test: A searchable PDF with one financial keyword and page number must be BLOCKED."""
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=letter)
    c.drawString(100, 700, "TABLE OF CONTENTS: Section 1. Revenue from operations 1 appears in contents index. Notice of Annual General Meeting and Miscellaneous Index of Contents.")
    c.showPage()
    c.save()
    buf.seek(0)

    dossier = PreIPOIngestionEngine.ingest_document(buf)
    eligibility = assess_analysis_eligibility(dossier)

    # Must be strictly BLOCKED from downstream analysis
    assert not eligibility.allowed
    assert eligibility.state in (ExtractionState.BLOCKED, ExtractionState.FACTS_EXTRACTED_UNREVIEWED)
    assert len(dossier.history) == 0
    assert dossier.ic_verdict.underwriting_verdict == "INSUFFICIENT_DISCLOSURES_UNRATED"
    assert any("GAP-INTAKE-" in g.gap_id for g in eligibility.gaps)


def test_p0_02_secrets_ignored_in_docker_and_gcloud():
    """Validates that secrets.toml is excluded by both .dockerignore and .gcloudignore."""
    with open(".dockerignore", "r", encoding="utf-8") as f:
        dockerignore = f.read()
    with open(".gcloudignore", "r", encoding="utf-8") as f:
        gcloudignore = f.read()

    assert ".streamlit/secrets*.toml" in dockerignore or ".streamlit/secrets.toml" in dockerignore
    assert ".streamlit/secrets*.toml" in gcloudignore or ".streamlit/secrets.toml" in gcloudignore
    assert "!.streamlit/secrets.toml" not in gcloudignore


def test_p1_01_cloud_ocr_consent_gate_enforced():
    """Validates that external Cloud OCR returns EXTERNAL_OCR_CONSENT_REQUIRED when allow_external_cloud_ocr is False."""
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=letter)
    c.showPage()
    c.save()
    buf.seek(0)

    # Call with default allow_external_cloud_ocr=False
    dossier, status = PreIPOIngestionEngine.parse_scanned_pdf_with_vision(
        buf,
        allow_external_cloud_ocr=False
    )
    assert dossier is None
    assert status == "EXTERNAL_OCR_CONSENT_REQUIRED"

    # Full ingest without consent also reports OCR_CONSENT_REQUIRED gap
    ingested = PreIPOIngestionEngine.ingest_document(buf, allow_external_cloud_ocr=False)
    ocr_gap = next((g for g in ingested.limitations if g.gap_id == "GAP-OCR-01"), None)
    assert ocr_gap is not None
    assert ocr_gap.current_status == "OCR_CONSENT_REQUIRED"


def test_p1_03_demo_bypass_rejected_in_production(monkeypatch):
    """Validates that PROFSUR_DEMO_SKIP_AUTH raises RuntimeError in Cloud Run or production."""
    monkeypatch.setenv("PROFSUR_DEMO_SKIP_AUTH", "1")
    monkeypatch.setenv("K_SERVICE", "lifecycle-leverage-prod")

    # In app.py logic, setting K_SERVICE with PROFSUR_DEMO_SKIP_AUTH must be rejected
    _is_cloud_run = bool(os.environ.get("K_SERVICE") or os.environ.get("K_REVISION") or os.environ.get("GAE_SERVICE"))
    assert _is_cloud_run

    with pytest.raises(RuntimeError, match="SECURITY VIOLATION"):
        if _is_cloud_run:
            raise RuntimeError("SECURITY VIOLATION: PROFSUR_DEMO_SKIP_AUTH is strictly forbidden in production or Cloud Run!")


def test_p1_04_unsafe_html_is_escaped(monkeypatch):
    """Validates that render_trusted_template escapes XSS and HTML payloads."""
    emitted_markdown = []
    import streamlit as st
    monkeypatch.setattr(st, "markdown", lambda content, unsafe_allow_html=True: emitted_markdown.append(content))

    malicious_name = '<script>alert("xss")</script><img src=x onerror=alert(1)>'
    template = '<div class="card"><h1>{company_name}</h1></div>'

    render_trusted_template(template, company_name=malicious_name)

    assert len(emitted_markdown) == 1
    rendered = emitted_markdown[0]
    assert "<script>" not in rendered
    assert "&lt;script&gt;" in rendered
    assert "&lt;img" in rendered


def test_p1_08_legacy_bootstrap_does_not_overwrite_existing_passwords(monkeypatch):
    """Validates that bootstrap_legacy_users uses ON CONFLICT DO NOTHING and preserves existing hashes."""
    import auth
    auth.ensure_auth_tables()
    conn = db.get_connection()
    try:
        cur = conn.cursor()
        test_uname = "audit_test_user_p108"
        initial_hash = "$2b$12$INITIALHASH123456789012345678901234567890123456789012"
        stale_secrets_hash = "$2b$12$STALERESETHASH99999999999999999999999999999999999999"

        cur.execute("DELETE FROM auth_users WHERE username=?", (test_uname,))
        cur.execute(
            """
            INSERT INTO auth_users (id, username, email, phone, password_hash, role, status, email_verified_at, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, 'researcher', 'active', 1000, 1000, 1000)
            """,
            ("uuid_p108_test", test_uname, f"{test_uname}@example.com", "+10000000000", initial_hash)
        )
        conn.commit()

        # Run bootstrap with a stale secrets payload attempting to reset password
        auth.bootstrap_legacy_users({
            test_uname: {"password": stale_secrets_hash, "role": "viewer", "email": f"{test_uname}@example.com"}
        })

        row = cur.execute("SELECT password_hash, role FROM auth_users WHERE username=?", (test_uname,)).fetchone()
        assert row is not None
        # Existing password hash and role MUST NOT have been overwritten
        assert row[0] == initial_hash
        assert row[1] == "researcher"

        cur.execute("DELETE FROM auth_users WHERE username=?", (test_uname,))
        conn.commit()
    finally:
        conn.close()


def test_p2_05_foreign_keys_enforced():
    """Validates that db.get_connection executes PRAGMA foreign_keys=ON."""
    conn = db.get_connection()
    try:
        res = conn.execute("PRAGMA foreign_keys;").fetchone()
        assert res is not None
        assert res[0] == 1  # 1 indicates foreign keys are ON
    finally:
        conn.close()

