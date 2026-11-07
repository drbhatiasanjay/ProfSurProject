import io
import json
import pytest
from unittest.mock import MagicMock, patch
from models.pre_ipo_ingest import PreIPOIngestionEngine

def test_detect_mime_type_magic_bytes():
    pdf_bytes = b"%PDF-1.7 sample content"
    png_bytes = b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR"
    jpg_bytes = b"\xff\xd8\xff\xe0\x00\x10JFIF"
    webp_bytes = b"RIFF\x24\x00\x00\x00WEBPVP8 "

    assert PreIPOIngestionEngine.detect_mime_type(pdf_bytes) == "application/pdf"
    assert PreIPOIngestionEngine.detect_mime_type(png_bytes) == "image/png"
    assert PreIPOIngestionEngine.detect_mime_type(jpg_bytes) == "image/jpeg"
    assert PreIPOIngestionEngine.detect_mime_type(webp_bytes) == "image/webp"

def test_detect_mime_type_extension_fallback():
    dummy = b"random string without header"
    assert PreIPOIngestionEngine.detect_mime_type(dummy, "report.png") == "image/png"
    assert PreIPOIngestionEngine.detect_mime_type(dummy, "annexure.jpg") == "image/jpeg"
    assert PreIPOIngestionEngine.detect_mime_type(dummy, "scan.webp") == "image/webp"
    assert PreIPOIngestionEngine.detect_mime_type(dummy, "drhp.pdf") == "application/pdf"

def test_extract_scanned_drhp_annexures_no_key_returns_gap_item():
    with patch("models.pre_ipo_ingest.get_gemini_api_key", return_value=None):
        result = PreIPOIngestionEngine.extract_scanned_drhp_annexures(
            document_source=io.BytesIO(b"%PDF-1.7 dummy pdf bytes" * 10),
            annexure_type="BORROWINGS",
        )
        assert result["status"] == "SUSPENDED_AWAITING_KEY"
        assert result["error"] == "GEMINI_API_KEY_REQUIRED"
        assert result["gap_id"] == "GAP-OCR-01"

def test_extract_scanned_drhp_annexures_oversized_rejected():
    with patch("models.pre_ipo_ingest.get_gemini_api_key", return_value="dummy-key"):
        large_bytes = b"0" * (26 * 1024 * 1024)
        result = PreIPOIngestionEngine.extract_scanned_drhp_annexures(
            document_source=large_bytes,
        )
        assert result["status"] == "FAILED"
        assert result["error"] == "FILE_TOO_LARGE"

def test_extract_scanned_drhp_annexures_mock_success():
    mock_payload = {
        "annexure_borrowings": [
            {
                "lender_name": "State Bank of India",
                "facility_type": "Term Loan",
                "sanctioned_amount_cr": 5000.0,
                "outstanding_amount_cr": 4200.0,
                "interest_rate_pct": 8.25,
                "repayment_terms": "Structured quarterly installments through FY32",
            }
        ],
        "annexure_objects_of_offer": [
            {
                "object_category": "Debt Prepayment",
                "proposed_utilization_cr": 7500.0,
                "deployment_fy25_cr": 5000.0,
                "deployment_fy26_cr": 2500.0,
            }
        ],
        "annexure_restated_pnl": [
            {
                "fiscal_year": "FY24",
                "revenue_from_ops_cr": 1962.6,
                "ebitda_cr": 1746.5,
                "finance_costs_cr": 1120.0,
                "pat_cr": 344.7,
            }
        ],
        "confidence_score": 0.94,
        "source_annexure_citation": "DRHP Annexure VI, page 214",
    }

    mock_resp = MagicMock()
    mock_resp.text = json.dumps(mock_payload)
    mock_client = MagicMock()
    mock_client.models.generate_content.return_value = mock_resp

    with patch("models.pre_ipo_ingest.get_gemini_api_key", return_value="valid-key"), \
         patch("google.genai.Client", return_value=mock_client):
        sample_doc = io.BytesIO(b"%PDF-1.7" + b"x" * 200)
        res = PreIPOIngestionEngine.extract_scanned_drhp_annexures(
            document_source=sample_doc,
            annexure_type="ALL",
            company_name_hint="NTPC Green",
        )
        assert res["status"] == "SUCCESS"
        assert len(res["tables"]["annexure_borrowings"]) == 1
        assert res["tables"]["annexure_borrowings"][0]["sanctioned_amount_cr"] == 5000.0
        assert res["tables"]["confidence_score"] == 0.94

