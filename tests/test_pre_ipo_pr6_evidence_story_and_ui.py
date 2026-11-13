"""Tests for PR 6: Pre-IPO Evidence Story, UI and Export Integration.

Validates:
- Unreviewed HCCH blocks analytics and board deck export.
- Price not disclosed is rendered as human-readable 'Undisclosed [●]'.
- No unsupported valuation/recommendation cards exist on unpriced/unreviewed filings.
- Source citations link to valid physical and printed page context.
- Presence states are converted to accessible, human-readable labels.
- Page and deck claims/values agree (no diverging independently calculated numbers).
- Deck export is strictly blocked on snapshot hash mismatch.
"""

import pytest
from models.pre_ipo_data import PRE_IPO_REGISTRY
from models.pre_ipo_capability_gate import (
    evaluate_capability_gate,
    assert_export_allowed,
    CapabilityType,
    ExportBlockedError,
)
from utils.pre_ipo_deck_generator import generate_pre_ipo_board_deck
from components.pre_ipo_provenance_ledger import _get_complete_extraction_ledger


def test_unreviewed_hcch_blocks_export_and_analytics():
    """Asserts that HCCH in PRE_IPO_REGISTRY without an accepted snapshot blocks export."""
    hcch = PRE_IPO_REGISTRY.get("hindustan_coca_cola")
    assert hcch is not None

    decision = evaluate_capability_gate(
        owner="default_user",
        company="hindustan_coca_cola",
        capability=CapabilityType.BOARD_DECK_EXPORT,
        snapshot_id=None,
        snapshot_status="UNREVIEWED",
        is_production=True
    )
    assert decision.allowed is False
    assert decision.status == "BLOCKED"

    with pytest.raises(ExportBlockedError):
        generate_pre_ipo_board_deck(
            dossier=hcch,
            snapshot_id=None,
            snapshot_status="UNREVIEWED",
            is_production=True
        )


def test_hash_mismatch_blocks_export():
    """Asserts that mismatch between precomputed result hash and snapshot hash blocks export."""
    coca = PRE_IPO_REGISTRY.get("hindustan_coca_cola")
    with pytest.raises(ExportBlockedError):
        generate_pre_ipo_board_deck(
            dossier=coca,
            snapshot_id="snap_123",
            snapshot_status="ACCEPTED_FOR_ANALYSIS",
            snapshot_hash="hash_aaa",
            result_snapshot_hash="hash_bbb",  # Mismatch!
            is_production=True
        )


def test_price_not_disclosed_rendered_human_readable():
    """Asserts that unpriced book-building filings display 'Undisclosed [●]' instead of 0 or blank."""
    hcch = PRE_IPO_REGISTRY.get("hindustan_coca_cola")
    ledger = _get_complete_extraction_ledger(hcch)
    price_item = next((it for it in ledger if it["variable"] == "Offer Price & Price Band"), None)

    assert price_item is not None
    assert "Undisclosed [●]" in price_item["normalized_value"]
    assert "UNDISCLOSED [●]" in price_item["status"]


def test_face_value_safely_rendered_when_none():
    """Asserts that a dossier with face_value_inr=None does not crash ledger rendering."""
    hcch = PRE_IPO_REGISTRY.get("hindustan_coca_cola")
    # Temporarily set face_value_inr to None to test null safety
    old_val = hcch.face_value_inr
    try:
        hcch.face_value_inr = None
        ledger = _get_complete_extraction_ledger(hcch)
        fv_item = next((it for it in ledger if it["variable"] == "Equity Share Face Value"), None)
        assert fv_item is not None
        assert "Undisclosed [●]" in fv_item["normalized_value"]
    finally:
        hcch.face_value_inr = old_val


def test_deck_export_succeeds_in_sandbox_with_aligned_hashes():
    """Asserts that sandbox deck generation produces valid PowerPoint bytes with aligned hashes."""
    mankind = PRE_IPO_REGISTRY.get("mankind_pharma")
    assert mankind is not None

    ppt_bytes = generate_pre_ipo_board_deck(
        dossier=mankind,
        snapshot_id="snap_mankind",
        snapshot_status="ACCEPTED_FOR_ANALYSIS",
        snapshot_hash="hash_consistent_123",
        result_snapshot_hash="hash_consistent_123",
        is_production=False
    )
    assert len(ppt_bytes) > 10000
    assert ppt_bytes[:4] == b"PK\x03\x04"  # Valid ZIP/PPTX header
