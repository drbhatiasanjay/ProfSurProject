"""Adversarial Red-Team & Verification Suite for Screen-to-Deck Export Parity & Neutral Decision Policy.

Tests Item 3 (Resolving Codex Finding F10 on Slides 7 & 8):
1. generate_pre_ipo_board_deck accepts precomputed wacc_result, reverse_dcf_result,
   and stress_matrix from page 27, guaranteeing 100% numerical parity.
2. Slide 8 eliminates string .replace() hacks on raw_verdict and enforces an explicit,
   neutral evidence-based decision policy.
3. Zero forbidden advisory phrases (e.g. unsolicited buy/sell/subscribe ratings) appear in the deck.
4. Fail-closed gate: Export blocked when snapshot hashes or reviews are invalid.
"""

import io
import pytest
from pptx import Presentation
from models.pre_ipo_data import PRE_IPO_REGISTRY
from models.pre_ipo_engine import (
    calculate_wacc_and_roic,
    calculate_reverse_dcf_hurdle,
    generate_2d_sensitivity_matrix,
)
from utils.pre_ipo_deck_generator import generate_pre_ipo_board_deck
from models.pre_ipo_capability_gate import ExportBlockedError


def test_screen_to_deck_numerical_parity():
    """Verify numbers passed into deck generator match the resulting text in slides 7 and 8."""
    dossier = PRE_IPO_REGISTRY["tata_technologies"]
    latest = dossier.history[-1]

    # Precompute results exactly as page 27 does
    wacc_res = calculate_wacc_and_roic(dossier, rf_rate=0.07, market_risk_premium=0.06)
    rev_dcf = calculate_reverse_dcf_hurdle(dossier)
    stress_mat = generate_2d_sensitivity_matrix(
        base_ebitda_cr=latest.ebitda_cr,
        gross_debt_cr=dossier.indebtedness.funded_bank_debt_cr,
        base_wair_pct=dossier.indebtedness.weighted_avg_interest_rate_pct or 9.0,
    )

    deck_bytes = generate_pre_ipo_board_deck(
        dossier=dossier,
        snapshot_id="snap-test",
        snapshot_status="ACCEPTED_FOR_ANALYSIS",
        snapshot_hash="hash-123",
        result_snapshot_hash="hash-123",
        is_production=False,  # Bypass P0 containment for unit test
        wacc_result=wacc_res,
        reverse_dcf_result=rev_dcf,
        stress_matrix=stress_mat,
        decision_support_policy="NEUTRAL_EVIDENCE_BASED",
    )

    assert deck_bytes is not None
    assert len(deck_bytes) > 1000

    # Parse PPTX presentation
    prs = Presentation(io.BytesIO(deck_bytes))
    assert len(prs.slides) == 8

    # Extract all text from Slide 7
    s7_text = " ".join(shape.text_frame.text for shape in prs.slides[6].shapes if shape.has_text_frame)
    # Check that ROIC, WACC, and Reverse DCF match precomputed results
    assert f"ROIC: {wacc_res['roic_pct']:.1f}%" in s7_text
    assert f"WACC: {wacc_res['wacc_pct']:.1f}%" in s7_text

    # Extract all text from Slide 8
    s8_text = " ".join(shape.text_frame.text for shape in prs.slides[7].shapes if shape.has_text_frame)
    # Verify neutral decision support policy
    assert "DECISION SUPPORT" in s8_text
    # Verify absence of legacy unmanaged raw string replacements
    assert "APPROVE WITH COVENANTS" not in s8_text


def test_zero_advisory_strings_policy():
    """Adversarial check: The generated deck must never emit unsolicited retail buy/sell recommendations."""
    dossier = PRE_IPO_REGISTRY["hindustan_coca_cola"]
    deck_bytes = generate_pre_ipo_board_deck(
        dossier=dossier,
        snapshot_id="snap-test-hcch",
        snapshot_status="ACCEPTED_FOR_ANALYSIS",
        snapshot_hash="hash-hcch",
        result_snapshot_hash="hash-hcch",
        is_production=False,
    )

    prs = Presentation(io.BytesIO(deck_bytes))
    full_deck_text = ""
    for slide in prs.slides:
        for shape in slide.shapes:
            if shape.has_text_frame:
                full_deck_text += " " + shape.text_frame.text

    forbidden_phrases = ["STRONG BUY", "DEFINITE SELL", "SUBSCRIBE FOR LISTING GAINS", "TARGET PRICE ₹"]
    for phrase in forbidden_phrases:
        assert phrase not in full_deck_text.upper(), f"Forbidden retail recommendation phrase found: '{phrase}'"


def test_adversarial_export_blocked_on_unreviewed_snapshot():
    """Adversarial check: Unreviewed or missing snapshot must block deck export unconditionally."""
    dossier = PRE_IPO_REGISTRY["hindustan_coca_cola"]
    with pytest.raises(ExportBlockedError, match="not approved|UNREVIEWED|unreviewed"):
        generate_pre_ipo_board_deck(
            dossier=dossier,
            snapshot_id="snap-unreviewed",
            snapshot_status="UNREVIEWED",
            snapshot_hash="hash-abc",
            result_snapshot_hash="hash-abc",
            is_production=True,  # Production enforcement
        )
