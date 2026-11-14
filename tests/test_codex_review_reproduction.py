"""Reproduction tests for Codex Review Findings F01–F10.

Demonstrates that the original candidate (commit 1bb597f) exhibits the exact vulnerabilities
and defects identified in PROFSUR_PR1_PR6_INDEPENDENT_REVIEW_2026-11-13.md:
- F03: Export succeeds with nonexistent snapshot and empty hashes.
- F04: AcceptedEvidenceSnapshot permits unreviewed facts, cross-owner observations, and invalid locators.
- F06: Blank PDF is marked complete, and empty OCR is marked OK.
- F07: compute_safe_wacc defaults missing CAPM/tax premises and corrupts zero beta / zero tax.
- F08: Reverse DCF shortcut fails to reprice back to target valuation.
- F09: Offer value and market capitalization are conflated.
"""

import pytest
from models.pre_ipo_data import PRE_IPO_REGISTRY
from models.pre_ipo_evidence import Observation, AcceptedEvidenceSnapshot, SourceLocator
from models.pre_ipo_document_indexer import DocumentIndexer
from models.pre_ipo_analysis_safety import compute_safe_wacc, compute_safe_reverse_dcf, BlockedResult
from models.pre_ipo_financial_contracts import validate_offer_contract
from utils.pre_ipo_deck_generator import generate_pre_ipo_board_deck
from pypdf import PdfWriter
import io


def test_reproduce_f03_export_unverified_snapshot_succeeds():
    """
    F03 Reproduction: On the original candidate, passing snapshot_id='nonexistent'
    and snapshot_status='ACCEPTED_FOR_ANALYSIS' without hashes generated ~43KB PowerPoint deck!
    """
    hcch = PRE_IPO_REGISTRY.get("hindustan_coca_cola")
    # In candidate 1bb597f, this incorrectly generates a deck:
    deck_bytes = generate_pre_ipo_board_deck(
        dossier=hcch,
        snapshot_id="nonexistent",
        snapshot_status="ACCEPTED_FOR_ANALYSIS",
        is_production=True
    )
    # The vulnerability: it succeeded and produced bytes
    assert len(deck_bytes) > 10000


def test_reproduce_f04_accepted_snapshot_allows_unreviewed_cross_owner():
    """
    F04 Reproduction: On the original candidate, AcceptedEvidenceSnapshot accepts
    UNREVIEWED observation from a different owner/company, with invalid locator.
    """
    obs_foreign = Observation(
        observation_id="obs_bad_01",
        owner="other_owner",
        company="other_company",
        metric_id="revenue_ops_cr",
        entity="Other Corp",
        value="100.0",
        review_state="UNREVIEWED",
        locator=SourceLocator(physical_page=-1)
    )
    # In candidate 1bb597f, this succeeds without raising ValueError:
    snap = AcceptedEvidenceSnapshot(
        snapshot_id="snap_insecure_01",
        owner="default_owner",
        company="target_company",
        snapshot_hash="arbitrary_hash",
        observations={"obs_bad_01": obs_foreign}
    )
    assert snap.snapshot_id == "snap_insecure_01"


def test_reproduce_f06_blank_pdf_marked_complete_and_empty_ocr_ok():
    """
    F06 Reproduction: Blank 1-page PDF returns is_complete=True.
    When allow_ocr=True, it marks status='OK' despite 0 characters extracted.
    """
    writer = PdfWriter()
    writer.add_blank_page(width=612, height=792)
    buf = io.BytesIO()
    writer.write(buf)
    pdf_bytes = buf.getvalue()

    indexer = DocumentIndexer()
    # 1. Without OCR consent: returns is_complete=True with IMAGE_ONLY
    index_no_ocr = indexer.index_pdf_stream(pdf_bytes, source_id="blank_no_ocr", allow_ocr=False)
    assert index_no_ocr.is_complete is True
    assert index_no_ocr.pages[1].status == "IMAGE_ONLY"

    # 2. With OCR consent: marks status='OK' despite empty text
    index_with_ocr = indexer.index_pdf_stream(pdf_bytes, source_id="blank_ocr", allow_ocr=True)
    assert index_with_ocr.pages[1].status == "OK"
    assert index_with_ocr.pages[1].char_count == 0


def test_reproduce_f07_wacc_alters_zeros_and_invents_premises():
    """
    F07 Reproduction:
    1. Zero beta and zero tax are overwritten by 'beta or 1.0' and 'tax_rate or 25.17',
       producing 9.24% instead of arithmetic 7.50%.
    2. Passing None for CAPM/tax premises invents 6.74% with is_scenario=False.
    """
    # Arithmetic expectation:
    # Ke = 5.0 + 0.0 * 6.0 = 5.0%
    # Kd_after_tax = 10.0 * (1 - 0.0) = 10.0%
    # Total cap = 200, We = 0.5, Wd = 0.5
    # WACC = 0.5 * 5.0 + 0.5 * 10.0 = 7.50%
    res_zero = compute_safe_wacc(
        market_equity_cr=100.0,
        total_debt_cr=100.0,
        cost_of_debt_pct=10.0,
        risk_free_rate_pct=5.0,
        beta=0.0,  # Zero beta
        market_risk_premium_pct=6.0,
        tax_rate_pct=0.0,  # Zero tax
    )
    # In candidate 1bb597f, this returned 9.24% because beta became 1.0 and tax became 25.17%:
    assert res_zero.wacc_pct == 9.24

    # Calling with None invents premises:
    res_none = compute_safe_wacc(
        market_equity_cr=10000.0,
        total_debt_cr=1000.0,
        cost_of_debt_pct=8.0,
        risk_free_rate_pct=None,
        beta=None,
        market_risk_premium_pct=None,
        tax_rate_pct=None,
    )
    assert not isinstance(res_none, BlockedResult)
    assert res_none.wacc_pct == 6.74


def test_reproduce_f08_reverse_dcf_shortcut_fails_repricing():
    """
    F08 Reproduction: Shortcut formula market_val * max(0.01, r-g) produces growth rate
    that does not reprice under standard DCF to the target value (returns ~913.81 instead of 1000).
    """
    target_val = 1000.0
    wacc = 10.0
    current_fcf = 100.0
    g_term = 5.0
    horizon = 5

    res = compute_safe_reverse_dcf(
        market_valuation_cr=target_val,
        wacc_pct=wacc,
        current_fcf_cr=current_fcf,
        terminal_growth_pct=g_term,
        forecast_years=horizon
    )
    g_solved = res.implied_revenue_cagr_pct / 100.0

    # Reprice with explicit 5-year DCF + Gordon terminal value:
    r = wacc / 100.0
    gt = g_term / 100.0
    pv = sum(current_fcf * ((1 + g_solved) ** t) / ((1 + r) ** t) for t in range(1, horizon + 1))
    terminal_fcf = current_fcf * ((1 + g_solved) ** horizon) * (1 + gt)
    pv += (terminal_fcf / (r - gt)) / ((1 + r) ** horizon)

    # In candidate 1bb597f, repriced pv is ~913.81, showing the shortcut does not match target:
    diff_pct = abs(pv - target_val) / target_val * 100.0
    assert diff_pct > 8.0, f"Expected shortcut to diverge from 1000, got repriced PV = {pv:.2f}"


def test_reproduce_f09_offer_and_market_cap_conflated():
    """
    F09 Reproduction: validate_offer_contract uses a single total_shares
    and returns identical numbers for offer_value_cr and market_cap_cr.
    """
    res = validate_offer_contract(
        face_value_inr=10.0,
        issue_price_inr=500.0,
        total_shares=10000000.0  # 1 Cr shares offered
    )
    # The flaw: offer_value_cr and market_cap_cr are identical
    assert res["offer_value_cr"] == res["market_cap_cr"]

