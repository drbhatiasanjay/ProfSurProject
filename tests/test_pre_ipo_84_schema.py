# -*- coding: utf-8 -*-
"""
tests/test_pre_ipo_84_schema.py
================================
Adversarial & Compliance Verification Suite for Expanded 84-Attribute Pre-IPO Schema.

Tests verify:
1. Canonical section partition (exactly 10 SEBI ICDR statutory sections).
2. Attribute inventory integrity (exactly 84 attributes, distinct IDs, valid units & refs).
3. Section-level attribute distribution matches specification (10, 6, 12, 10, 11, 9, 8, 6, 6, 6).
4. Backward compatibility (CANONICAL_42_ATTRIBUTES and CANONICAL_SECTIONS_42 preserved).
5. Zero-truthiness invariant (Rule E.3): 0.0 values preserved as FOUND with value 0.0.
6. Unpriced DRHP containment: unpriced price bands emitted as NOT_FOUND with syndicate reconfirmation reason.
7. Tri-state invariant: len(records) == 84, and found + not_found + reconfirm == 84.
8. FastAPI bridge endpoints (/api/pre-ipo/schema and /api/pre-ipo/market-status) emit 84 items.
"""

import pytest
from models.pre_ipo_schema import (
    CanonicalSection,
    ExpectedUnit,
    AttributeDefinition,
    CANONICAL_SECTIONS,
    CANONICAL_SECTIONS_42,
    CANONICAL_84_ATTRIBUTES,
    CANONICAL_42_ATTRIBUTES,
    extract_canonical_84_provenance,
    extract_canonical_42_provenance,
)


class TestCanonical84SchemaDefinition:
    """Verifies schema metadata, section integrity, and enumeration constraints."""

    def test_canonical_sections_count_and_order(self):
        """Assert exactly 10 canonical sections exist in correct statutory sequence."""
        assert len(CANONICAL_SECTIONS) == 10
        expected_sections = [
            CanonicalSection.OFFER_STRUCTURE.value,
            CanonicalSection.OBJECTS.value,
            CanonicalSection.PL.value,
            CanonicalSection.BALANCE_SHEET.value,
            CanonicalSection.WORKING_CAPITAL.value,
            CanonicalSection.INDEBTEDNESS.value,
            CanonicalSection.CAP_TABLE.value,
            CanonicalSection.GOVERNANCE.value,
            CanonicalSection.CONTINGENT_LIABILITIES.value,
            CanonicalSection.UNIT_ECONOMICS.value,
        ]
        assert CANONICAL_SECTIONS == expected_sections

    def test_canonical_84_attributes_count(self):
        """Assert exactly 84 canonical attributes are registered."""
        assert len(CANONICAL_84_ATTRIBUTES) == 84

    def test_canonical_84_attributes_unique_ids(self):
        """Assert all 84 attribute IDs are unique with zero duplicates."""
        ids = [attr.attribute_id for attr in CANONICAL_84_ATTRIBUTES]
        assert len(ids) == len(set(ids)), f"Duplicate attribute IDs found: {set([x for x in ids if ids.count(x) > 1])}"

    def test_canonical_84_per_section_distribution(self):
        """Assert attribute distribution across 10 sections matches the architectural specification."""
        expected_distribution = {
            CanonicalSection.OFFER_STRUCTURE.value: 10,
            CanonicalSection.OBJECTS.value: 6,
            CanonicalSection.PL.value: 12,
            CanonicalSection.BALANCE_SHEET.value: 10,
            CanonicalSection.WORKING_CAPITAL.value: 11,
            CanonicalSection.INDEBTEDNESS.value: 9,
            CanonicalSection.CAP_TABLE.value: 8,
            CanonicalSection.GOVERNANCE.value: 6,
            CanonicalSection.CONTINGENT_LIABILITIES.value: 6,
            CanonicalSection.UNIT_ECONOMICS.value: 6,
        }
        actual_distribution = {}
        for attr in CANONICAL_84_ATTRIBUTES:
            actual_distribution[attr.section] = actual_distribution.get(attr.section, 0) + 1

        assert actual_distribution == expected_distribution
        assert sum(actual_distribution.values()) == 84

    def test_canonical_84_attribute_contracts(self):
        """Assert every attribute definition satisfies schema invariants."""
        valid_sections = {s.value for s in CanonicalSection}
        valid_units = {u.value for u in ExpectedUnit}

        for attr in CANONICAL_84_ATTRIBUTES:
            assert isinstance(attr.attribute_id, str) and len(attr.attribute_id) > 0
            assert attr.section in valid_sections, f"Invalid section: {attr.section}"
            assert isinstance(attr.label, str) and len(attr.label) > 0
            assert attr.expected_unit in valid_units, f"Invalid unit: {attr.expected_unit}"
            assert isinstance(attr.statutory_reference, str) and len(attr.statutory_reference) > 0
            assert isinstance(attr.required_for_gate, bool)
            assert isinstance(attr.downstream_models, list)
            assert len(attr.downstream_models) > 0, f"{attr.attribute_id} must declare downstream consumer models"

    def test_backward_compatibility_tier1(self):
        """Assert CANONICAL_42_ATTRIBUTES matches the first 42 attributes of 84."""
        assert len(CANONICAL_42_ATTRIBUTES) == 42
        assert len(CANONICAL_SECTIONS_42) == 7
        for i in range(42):
            assert CANONICAL_42_ATTRIBUTES[i].attribute_id == CANONICAL_84_ATTRIBUTES[i].attribute_id


class TestCanonical84ProvenanceExtraction:
    """Verifies extraction behavior with strict zero-truthiness and unpriced handling."""

    def test_hccb_provenance_extraction_returns_84_records(self):
        """Assert extraction produces exactly 84 records."""
        records = extract_canonical_84_provenance(dossier=None, is_hccb=True)
        assert len(records) == 84

        # Invariant: found + not_found + reconfirm == 84
        found = sum(1 for r in records if r["status"] == "FOUND")
        not_found = sum(1 for r in records if r["status"] == "NOT_FOUND")
        reconfirm = sum(1 for r in records if r["status"] == "NEEDS_RECONFIRMATION")
        assert found + not_found + reconfirm == 84
        assert found >= 70, f"Expected at least 70 verified records for HCCB, got {found}"

    def test_zero_truthiness_preservation(self):
        """Adversarial check (Rule E.3): 0.0 values must be FOUND with value 0.0, never None or NOT_FOUND."""
        records = extract_canonical_84_provenance(dossier=None, is_hccb=True)
        record_map = {r["attributeId"]: r for r in records}

        # Fresh Issue for HCCB is 100% OFS, so fresh issue == 0.0
        fresh_rec = record_map.get("offer.fresh_issue_cr")
        assert fresh_rec is not None
        assert fresh_rec["status"] == "FOUND"
        assert fresh_rec["value"] == 0.0, f"Expected 0.0, got {fresh_rec['value']}"

        # Promoter pledge for HCCB is 0.00%
        pledge_rec = record_map.get("cap.promoter_pledge_pct")
        assert pledge_rec is not None
        assert pledge_rec["status"] == "FOUND"
        assert pledge_rec["value"] == 0.0, f"Expected 0.0, got {pledge_rec['value']}"

        # Secured term loans for HCCB is 0.0
        secured_debt_rec = record_map.get("debt.secured_term_loans_cr")
        assert secured_debt_rec is not None
        assert secured_debt_rec["status"] == "FOUND"
        assert secured_debt_rec["value"] == 0.0, f"Expected 0.0, got {secured_debt_rec['value']}"

    def test_unpriced_drhp_containment(self):
        """Assert unpriced DRHP variables ([•]) are emitted as NOT_FOUND with explicit reconfirmationReason."""
        records = extract_canonical_84_provenance(dossier=None, is_hccb=True)
        record_map = {r["attributeId"]: r for r in records}

        pmin = record_map.get("offer.price_band_min")
        assert pmin is not None
        assert pmin["status"] == "NOT_FOUND"
        assert pmin["value"] is None
        assert "RHP" in (pmin.get("reconfirmationReason") or "")

        pmax = record_map.get("offer.price_band_max")
        assert pmax is not None
        assert pmax["status"] == "NOT_FOUND"
        assert pmax["value"] is None
        assert "RHP" in (pmax.get("reconfirmationReason") or "")

    def test_bounding_box_and_confidence_integrity(self):
        """Assert all 84 records carry valid bounding boxes, citations, and confidence scores."""
        records = extract_canonical_84_provenance(dossier=None, is_hccb=True)
        for r in records:
            assert r["pdfPageNumber"] >= 1
            assert r.get("printedPageLabel") and len(r["printedPageLabel"]) > 0
            assert len(r["bboxCoordinates"]) == 4
            assert all(isinstance(c, (int, float)) for c in r["bboxCoordinates"])
            assert 0.0 <= r["confidenceScore"] <= 1.0
            if r["status"] == "FOUND":
                assert r["confidenceScore"] >= 0.85

    def test_backward_compatibility_wrapper_returns_42_or_84(self):
        """Assert extract_canonical_42_provenance returns valid list."""
        records = extract_canonical_42_provenance(dossier=None, is_hccb=True)
        assert len(records) == 84  # Enriched with all 84 canonical items


class TestFastApiSchemaEndpoints:
    """Verifies FastAPI bridge endpoints return the 84-attribute schema and provenance."""

    def test_api_schema_endpoint(self):
        """Assert /api/pre-ipo/schema returns totalCount=84 and 10 sections."""
        pytest.importorskip("fastapi")
        from fastapi.testclient import TestClient
        from api.server import app

        client = TestClient(app)
        resp = client.get("/api/pre-ipo/schema")
        assert resp.status_code == 200
        data = resp.json()
        assert data["totalCount"] == 84
        assert len(data["sections"]) == 10
        assert len(data["attributes"]) == 84

    def test_api_market_status_provenance_ledger(self):
        """Assert /api/pre-ipo/market-status returns provenanceLedger with 84 items."""
        pytest.importorskip("fastapi")
        from fastapi.testclient import TestClient
        from api.server import app

        client = TestClient(app)
        resp = client.get("/api/pre-ipo/market-status")
        assert resp.status_code == 200
        data = resp.json()
        active_offer = data.get("activeOffer", {})
        ledger = active_offer.get("provenanceLedger", [])
        assert len(ledger) == 84

        summary = active_offer.get("provenanceSummary", {})
        assert summary.get("totalCount") == 84
        assert summary.get("foundCount") + summary.get("notFoundCount") + summary.get("reconfirmCount") == 84
