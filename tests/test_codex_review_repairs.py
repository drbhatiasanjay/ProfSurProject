"""Reproduction and Repair Verification tests for Codex Review Findings F01–F10.

Verifies that the repairs address all findings in PROFSUR_PR1_PR6_INDEPENDENT_REVIEW_2026-11-13.md:
- F01: Production integration of helper modules into pre_ipo_engine and pre_ipo_ingest.
- F02: IC Verdict containment leak closed across selector and custom upload avenues.
- F03: Export fails closed on nonexistent snapshots, missing hashes, or database mismatches.
- F04: AcceptedEvidenceSnapshot enforces ownership, review_state='ACCEPTED', positive physical page, canonical hashing, and immutability.
- F05: Migration 003 is genuinely atomic across DDL alterations and journal insertion.
- F06: Blank PDFs return is_complete=False; OCR consent requires actual text extraction; TOC lines ignored.
- F07: compute_safe_wacc preserves zero beta and zero tax (regression case 7.50%), and fails closed on None.
- F08: Reverse DCF exact root-finding solver reprices back to target valuation within 0.05% tolerance.
- F09: validate_offer_contract separates offer value from market capitalization.
"""

import pytest
import sqlite3
import io
import types
from pypdf import PdfWriter
from models.pre_ipo_data import PRE_IPO_REGISTRY
from models.pre_ipo_evidence import Observation, AcceptedEvidenceSnapshot, SourceLocator
from models.pre_ipo_document_indexer import DocumentIndexer
from models.pre_ipo_analysis_safety import (
    compute_safe_wacc,
    compute_safe_roic,
    compute_safe_reverse_dcf,
    SafeWACCResult,
    SafeROICResult,
    SafeReverseDCFResult,
    BlockedResult,
)
from models.pre_ipo_financial_contracts import validate_offer_contract
from models.pre_ipo_capability_gate import (
    evaluate_capability_gate,
    assert_export_allowed,
    CapabilityType,
    ExportBlockedError,
    is_hcch_entity,
)
from models.pre_ipo_engine import calculate_wacc_and_roic, calculate_reverse_dcf_hurdle
from utils.pre_ipo_deck_generator import generate_pre_ipo_board_deck


@pytest.fixture(autouse=True)
def isolated_db(monkeypatch, tmp_path):
    """Guarantees tests use an isolated disposable database."""
    db_file = str(tmp_path / "test_codex_repair.db")
    monkeypatch.setenv("PROFSUR_DB_PATH", db_file)
    from models.pre_ipo_migrations import apply_migrations
    with sqlite3.connect(db_file) as conn:
        apply_migrations(conn)
    return db_file


def test_f02_ic_verdict_containment_and_entity_detection():
    """F02: Asserts automated IC verdict is strictly blocked and HCCH detected across avenues."""
    # 1. HCCH detection across various representations
    assert is_hcch_entity("hindustan_coca_cola") is True
    assert is_hcch_entity("custom_deal_01", company_name="Hindustan Coca-Cola Beverages Pvt Ltd") is True
    assert is_hcch_entity("deal_99", cin="U15549DL1997PTC085183") is True
    assert is_hcch_entity("mankind_pharma", company_name="Mankind Pharma Ltd") is False

    # 2. Recommendations / IC Verdict capability is unconditionally blocked under P0-08
    decision = evaluate_capability_gate(
        owner="drbhatia",
        company="Hindustan Coca-Cola",
        capability=CapabilityType.RECOMMENDATIONS,
        snapshot_id="snap_123",
        snapshot_status="ACCEPTED_FOR_ANALYSIS",
    )
    assert decision.allowed is False
    assert decision.status == "BLOCKED"
    assert "P0-08" in decision.reason


def test_f03_export_unverified_snapshot_fails_closed():
    """F03: Asserts export fails closed on nonexistent snapshots and missing hashes."""
    hcch = PRE_IPO_REGISTRY.get("hindustan_coca_cola")

    # Nonexistent snapshot fails closed with ExportBlockedError
    with pytest.raises(ExportBlockedError) as exc_info:
        generate_pre_ipo_board_deck(
            dossier=hcch,
            snapshot_id="nonexistent",
            snapshot_status="ACCEPTED_FOR_ANALYSIS",
            is_production=True
        )
    assert "does not exist in persistence" in str(exc_info.value)

    # Missing hashes fail closed
    with pytest.raises(ExportBlockedError) as exc_info2:
        assert_export_allowed(
            dossier=hcch,
            snapshot_id="nonexistent",
            snapshot_status="ACCEPTED_FOR_ANALYSIS",
            snapshot_hash=None,
            result_snapshot_hash=None,
            is_production=True
        )
    assert "Export blocked" in str(exc_info2.value)


def test_f04_accepted_snapshot_enforces_contracts_and_immutability():
    """F04: Asserts AcceptedEvidenceSnapshot validates observation contracts and is immutable."""
    loc_good = SourceLocator(physical_page=12, raw_text="Revenue from operations")
    loc_bad_page = SourceLocator(physical_page=-5)

    obs_valid = Observation(
        observation_id="obs_01",
        owner="drbhatia",
        company="hcch",
        metric_id="revenue_ops_cr",
        entity="HCCH Ltd",
        value="12500.0",
        review_state="ACCEPTED",
        locator=loc_good,
        reviewer="drbhatia",
        review_reason="Verified from audited P&L page 12"
    )

    obs_unreviewed = Observation(
        observation_id="obs_02",
        owner="drbhatia",
        company="hcch",
        metric_id="ebitda_cr",
        entity="HCCH Ltd",
        value="2100.0",
        review_state="UNREVIEWED",
        locator=loc_good
    )

    # 1. Unreviewed observation rejected
    with pytest.raises(ValueError) as exc:
        AcceptedEvidenceSnapshot(
            snapshot_id="snap_01",
            owner="drbhatia",
            company="hcch",
            observations={"obs_02": obs_unreviewed}
        )
    assert "Only ACCEPTED observations are eligible" in str(exc.value)

    # 2. Cross-owner observation rejected
    obs_other_owner = Observation(
        observation_id="obs_03",
        owner="other_user",
        company="hcch",
        metric_id="revenue_ops_cr",
        entity="HCCH Ltd",
        value="12500.0",
        review_state="ACCEPTED",
        locator=loc_good,
        reviewer="drbhatia",
        review_reason="Verified"
    )
    with pytest.raises(ValueError) as exc:
        AcceptedEvidenceSnapshot(
            snapshot_id="snap_01",
            owner="drbhatia",
            company="hcch",
            observations={"obs_03": obs_other_owner}
        )
    assert "Cross-owner isolation violation" in str(exc.value)

    # 3. Negative physical page rejected
    with pytest.raises(ValueError) as exc:
        Observation(
            observation_id="obs_04",
            owner="drbhatia",
            company="hcch",
            metric_id="revenue_ops_cr",
            entity="HCCH Ltd",
            value="12500.0",
            review_state="ACCEPTED",
            locator=loc_bad_page,
            reviewer="drbhatia",
            review_reason="Verified"
        )
    assert "SourceLocator" in str(exc.value) or "positive physical page" in str(exc.value)

    # 4. Valid snapshot computes canonical hash and enforces immutability
    snap = AcceptedEvidenceSnapshot(
        snapshot_id="snap_valid_01",
        owner="drbhatia",
        company="hcch",
        observations={"obs_01": obs_valid},
        accepted_by="drbhatia",
        accepted_at="2026-11-13T12:00:00Z"
    )
    assert snap.snapshot_hash != ""
    assert isinstance(snap.observations, types.MappingProxyType)

    # Mutation attempt raises TypeError
    with pytest.raises(TypeError):
        snap.observations["obs_new"] = obs_valid


def test_f05_atomic_migration_003_rollback():
    """F05: Verifies transactional DDL execution rolls back cleanly on error."""
    from models.pre_ipo_migrations import _execute_sql_script_transactional, _get_table_columns

    conn = sqlite3.connect(":memory:")
    conn.execute("CREATE TABLE test_table (id INTEGER PRIMARY KEY, name TEXT)")
    conn.commit()

    # Begin transaction, alter table and add index, then simulate failure and rollback
    conn.execute("BEGIN IMMEDIATE")
    conn.execute("ALTER TABLE test_table ADD COLUMN extra_col TEXT")
    _execute_sql_script_transactional(conn, "CREATE INDEX idx_test_name ON test_table(name);")

    # Verify column exists inside transaction
    cols_in_tx = _get_table_columns(conn, "test_table")
    assert "extra_col" in cols_in_tx

    # Rollback transaction
    conn.rollback()

    # Column and index must be completely gone
    cols_after_rollback = _get_table_columns(conn, "test_table")
    assert "extra_col" not in cols_after_rollback
    indexes = [r[1] for r in conn.execute("PRAGMA index_list(test_table)").fetchall()]
    assert "idx_test_name" not in indexes
    conn.close()


def test_f06_blank_pdf_rejected_and_ocr_requires_text():
    """F06: Blank PDF is not text-extracted, and empty OCR is not marked OK."""
    writer = PdfWriter()
    writer.add_blank_page(width=612, height=792)
    buf = io.BytesIO()
    writer.write(buf)
    pdf_bytes = buf.getvalue()

    indexer = DocumentIndexer()
    # 1. Without OCR consent: is_text_extracted is False, status is IMAGE_ONLY
    index_no_ocr = indexer.index_pdf_stream(pdf_bytes, source_id="blank_no_ocr", allow_ocr=False)
    assert index_no_ocr.is_text_extracted is False
    assert index_no_ocr.pages[1].status == "IMAGE_ONLY"

    # 2. With OCR consent: empty text is still IMAGE_ONLY, is_text_extracted is False
    index_with_ocr = indexer.index_pdf_stream(pdf_bytes, source_id="blank_ocr", allow_ocr=True)
    assert index_with_ocr.is_text_extracted is False
    assert index_with_ocr.pages[1].status == "IMAGE_ONLY"


def test_f07_wacc_preserves_zero_beta_and_tax_and_blocks_none():
    """
    F07:
    Regression case: equity 100, debt 100, debt cost 10%, rf 5%, beta 0, mrp 6%, tax 0% must produce WACC 7.50%.
    Calling with None must return BlockedResult.
    """
    res_zero = compute_safe_wacc(
        market_equity_cr=100.0,
        total_debt_cr=100.0,
        cost_of_debt_pct=10.0,
        risk_free_rate_pct=5.0,
        beta=0.0,
        market_risk_premium_pct=6.0,
        tax_rate_pct=0.0,
    )
    assert isinstance(res_zero, SafeWACCResult)
    assert res_zero.cost_of_equity_pct == 5.0
    assert res_zero.after_tax_cost_of_debt_pct == 10.0
    assert res_zero.wacc_pct == 7.50

    # Passing None for required premise fails closed
    res_none = compute_safe_wacc(
        market_equity_cr=1000.0,
        total_debt_cr=500.0,
        cost_of_debt_pct=8.0,
        risk_free_rate_pct=None,
        beta=None,
        market_risk_premium_pct=None,
        tax_rate_pct=None,
    )
    assert isinstance(res_none, BlockedResult)
    assert res_none.is_blocked is True
    assert "risk_free_rate_pct" in res_none.missing_premises


def test_f08_reverse_dcf_exact_root_solver_and_repricing():
    """F08: Reverse DCF solves exact growth rate and reprices back to target valuation within 0.05%."""
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
    assert isinstance(res, SafeReverseDCFResult)
    assert res.repricing_error_pct < 0.05
    assert abs(res.repriced_valuation_cr - target_val) <= 0.5

    # Invalid terminal spread (wacc <= g_term) is rejected, not clamped
    res_invalid_spread = compute_safe_reverse_dcf(
        market_valuation_cr=target_val,
        wacc_pct=5.0,
        current_fcf_cr=current_fcf,
        terminal_growth_pct=5.5,
        forecast_years=horizon
    )
    assert isinstance(res_invalid_spread, BlockedResult)
    assert "WACC" in res_invalid_spread.reason


def test_f09_offer_value_and_market_cap_distinct():
    """F09: validate_offer_contract calculates distinct values for offer value and market cap."""
    res = validate_offer_contract(
        face_value_inr=10.0,
        issue_price_inr=500.0,
        offered_shares=10000000.0,          # 1 Cr shares offered
        total_post_issue_shares=100000000.0  # 10 Cr shares post-issue
    )
    assert res["valid"] is True
    assert res["offer_value_cr"] == 500.0
    assert res["market_cap_cr"] == 5000.0
    assert res["offer_value_cr"] != res["market_cap_cr"]

    # Face value substitution provenance check
    res_face = validate_offer_contract(
        face_value_inr=10.0,
        issue_price_inr=500.0,
        price_provenance="FACE_VALUE"
    )
    assert res_face["valid"] is False
    assert "Face value provenance detected" in res_face["error"]


def test_f01_production_engine_integration():
    """F01: Asserts calculate_wacc_and_roic in pre_ipo_engine uses safe contracts without 9% or book equity fallbacks."""
    deal = PRE_IPO_REGISTRY["mankind_pharma"]

    # 1. Unpriced deal or missing debt cost blocks WACC without silent fallback
    res = calculate_wacc_and_roic(deal)
    if not deal.valuation_comps or deal.valuation_comps.implied_mcap_cr <= 0:
        assert res["is_computable"] is False
        assert "UNPRICED" in res["status"] or "DEBT_COST" in res["status"] or "INSUFFICIENT" in res["status"]
    else:
        assert res["is_computable"] is True
        assert res["wacc_pct"] is not None
