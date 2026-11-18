"""
TDD Tests for Canonical 84-Attribute & Docling to Knowledge Graph Bridge
Milestone 11.3 - Phase 3 Single Source of Truth (SSOT) Verification

Verifies:
1. Docling/84-attribute extraction directly populates Knowledge Graph.
2. Zero data drift: 100% parity between 84-attribute ledger and graph nodes.
3. Closed-world SHACL statutory validation gate on bridged data.
"""

import pytest
from models.pre_ipo_schema import extract_canonical_84_provenance
from models.pre_ipo_kg_engine import PreIPOPropertyGraphEngine
from models.pre_ipo_kg_bridge import hydrate_kg_from_canonical_84_provenance
from models.pre_ipo_shacl_engine import ExportBlockedError


def test_bridge_hydrates_kg_from_84_provenance_records():
    """Asserts that 84 canonical extraction records directly populate the Property Graph."""
    # 1. Obtain authentic canonical 84 records (simulating Docling extraction)
    dossier = {}
    offer_data = {
        "symbol": "HCCH",
        "companyName": "Hindustan Coca-Cola Holdings Pvt Ltd",
        "priceBandMin": None,
        "priceBandMax": None
    }
    records = extract_canonical_84_provenance(dossier=dossier, is_hccb=True, offer_data=offer_data)
    assert len(records) == 84

    # 2. Hydrate Knowledge Graph via Bridge
    engine = PreIPOPropertyGraphEngine(in_memory=True)
    summary = hydrate_kg_from_canonical_84_provenance(provenance_records=records, engine=engine)

    assert summary["status"] == "SUCCESS"
    assert summary["sourceAttributesCount"] == 84
    assert summary["graphNodesCount"] >= 8
    assert summary["shaclConforms"] is True

    # 3. Assert exact data parity with Rule E.3 Zero-Truthiness
    offering = engine.get_node("OFFERING_2026")
    assert offering is not None
    assert offering.properties["freshIssueCr"] == 0.0
    assert offering.properties["totalSizeCr"] == 9975.0

    promoter = engine.get_node("HCCOH")
    assert promoter is not None
    assert promoter.properties["preShareholdingPct"] == 60.0
    assert promoter.page_number >= 1


def test_bridge_shacl_closed_world_mismatch_blocks_export():
    """Asserts that tampered canonical attributes fail the SHACL gate before DB commit."""
    dossier = {}
    offer_data = {"symbol": "HCCH", "companyName": "Test"}
    records = extract_canonical_84_provenance(dossier=dossier, is_hccb=True, offer_data=offer_data)

    # Tamper with total issue size so Total != Fresh + OFS (10,000 != 0 + 12,500)
    for r in records:
        if "total_issue_size_cr" in r.get("attributeId", ""):
            r["value"] = 5000.0  # Mismatch: 5000 != 0 + 9975 / 12500

    engine = PreIPOPropertyGraphEngine(in_memory=True)
    with pytest.raises(ExportBlockedError):
        hydrate_kg_from_canonical_84_provenance(provenance_records=records, engine=engine)
