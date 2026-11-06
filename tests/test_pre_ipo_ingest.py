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


def test_ingest_document_custom_fallback():
    dossier = PreIPOIngestionEngine.ingest_document(None, company_name_hint="Novel Biotech Pvt Ltd")
    assert dossier.deal_id == "custom_ingested_deal"
    assert dossier.company_name == "Novel Biotech Pvt Ltd"
    # Ensure audit report contains 3-tier statuses
    statuses = {item.status for item in dossier.audit_report}
    assert "FOUND_AND_RECONCILED" in statuses
    assert "CONVERTED_AND_NORMALIZED" in statuses
    assert "MISSING_UNDISCLOSED" in statuses
