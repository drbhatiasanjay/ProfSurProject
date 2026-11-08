"""
Unit tests for Pre-IPO Ingestion and Diagnostic Reconciliation Engine.
"""
import pytest
from models.pre_ipo_ingest import PreIPOIngestionEngine
from models.pre_ipo_schema import PreIPODealDossier


def test_ingest_document_by_deal_id_hint():
    dossier = PreIPOIngestionEngine.ingest_document(None, deal_id_hint="mankind_pharma")
    assert isinstance(dossier, PreIPODealDossier)
    assert dossier.company_name == "Mankind Pharma Limited"
    assert len(dossier.audit_report) > 0


def test_ingest_document_by_company_name_hint():
    dossier = PreIPOIngestionEngine.ingest_document(None, company_name_hint="Afcons Infrastructure")
    assert dossier.deal_id == "afcons_infra"
    assert dossier.fresh_issue_cr == 1250.0


def test_ingest_document_unverified_fallback():
    # An unknown company or invalid document must yield unverified facts and missing data limitations, NEVER invented numbers
    dossier = PreIPOIngestionEngine.ingest_document(None, company_name_hint="Novel Biotech Pvt Ltd")
    assert dossier.deal_id in ("unverified_upload", "unverified_scanned_upload")
    assert "Novel Biotech Pvt Ltd" in dossier.company_name
    assert any(tag in dossier.company_name for tag in ["[Unverified Extraction]", "[Not Extracted - Scanned Image]"])
    assert dossier.total_issue_size_cr == 0.0
    assert dossier.history[0].revenue_ops_cr == 0.0
    assert dossier.ic_verdict.underwriting_verdict in ("INSUFFICIENT DATA TO CONCLUDE", "INSUFFICIENT_DISCLOSURES_UNRATED")
    assert len(dossier.limitations) > 0
    assert dossier.limitations[0].current_status in ("PARSE_FAILED", "NOT_SUPPLIED", "AWAITING_OCR_KEY", "NOT_EXTRACTED", "OCR_CONSENT_REQUIRED")


def test_parse_scanned_pdf_missing_key_behavior():
    import io
    from unittest.mock import patch
    with patch("models.pre_ipo_ingest.get_gemini_api_key", return_value=None):
        res, status = PreIPOIngestionEngine.parse_scanned_pdf_with_vision(io.BytesIO(b"%PDF-1.4 scanned image"), allow_external_cloud_ocr=True)
        assert res is None
        assert status == "GEMINI_API_KEY_REQUIRED"


def test_parse_scanned_pdf_vision_success_mock():
    import io
    from unittest.mock import patch, MagicMock
    mock_json_response = """{
        "company_name": "SolarTech Infrastructure Ltd",
        "sector": "Renewables",
        "filing_type": "DRHP",
        "filing_date": "November 2024",
        "total_issue_size_cr": 2500.0,
        "fresh_issue_cr": 2000.0,
        "ofs_cr": 500.0,
        "face_value_inr": 10.0,
        "brlm_bankers": ["Kotak Mahindra Capital"],
        "exchange_listing": ["BSE", "NSE"],
        "history": [
            {"fiscal_year": "FY24", "revenue_ops_cr": 1200.0, "ebitda_cr": 450.0, "pat_cr": 210.0, "cfo_cr": 380.0, "cfi_cr": -600.0, "cff_cr": 250.0, "capex_cr": 600.0, "fcf_cr": -220.0, "net_worth_cr": 1500.0}
        ],
        "indebtedness": {
            "secured_term_loans_cr": 800.0,
            "working_capital_loans_cr": 200.0,
            "ncd_bonds_cr": 0.0,
            "unsecured_loans_cr": 50.0,
            "lease_liabilities_ind_as_116_cr": 80.0,
            "cash_and_equivalents_cr": 120.0
        },
        "objects_of_offer": {
            "gross_fresh_issue_cr": 2000.0,
            "issue_expenses_cr": 50.0,
            "debt_prepayment_cr": 1200.0,
            "capex_expansion_cr": 300.0,
            "inorganic_acquisition_cr": 0.0,
            "general_corporate_purposes_cr": 450.0
        },
        "working_capital": {
            "inventory_days_dio": 30.0,
            "debtor_days_dso": 65.0,
            "creditor_days_dpo": 40.0,
            "net_working_capital_pct_sales": 15.0
        },
        "governance": {
            "promoter_pledge_pct": 0.0,
            "related_party_transactions_pct_rev": 12.0,
            "top_5_customer_concentration_pct": 45.0,
            "herfindahl_hhi_index": 0.12,
            "contingent_liabilities_pct_networth": 8.0,
            "independent_directors_pct": 50.0
        }
    }"""
    mock_client = MagicMock()
    mock_resp = MagicMock()
    mock_resp.text = mock_json_response
    mock_client.models.generate_content.return_value = mock_resp

    with patch("models.pre_ipo_ingest.get_gemini_api_key", return_value="test-key-fake"):
        with patch("google.genai.Client", return_value=mock_client):
            dossier, status = PreIPOIngestionEngine.parse_scanned_pdf_with_vision(
                io.BytesIO(b"%PDF-1.4 dummy scanned pdf content that is long enough to simulate real file bytes" * 5),
                allow_external_cloud_ocr=True
            )
            assert status == "SUCCESS"
            assert dossier is not None
            assert dossier.company_name == "SolarTech Infrastructure Ltd [Vision OCR Extracted]"
            assert dossier.fresh_issue_cr == 2000.0
            assert dossier.objects_of_offer.debt_prepayment_cr == 1200.0
            assert dossier.indebtedness.secured_term_loans_cr == 800.0
            assert any(item.normalized_metric == "GEMINI_FLASH_VISION_EXTRACTED" for item in dossier.audit_report)


