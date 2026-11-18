"""
Adversarial TDD Test Suite for Closed-World SHACL Statutory Gate
Milestone 11.1 - Phase 1 Verification

Tests:
1. Valid HCCH pure OFS offer conforms (0.0 fresh issue accepted under Rule E.3).
2. Mathematical reconciliation mismatch (Total != Fresh + OFS) fails closed with ExportBlockedError.
3. Missing mandatory promoter disclosure fails closed under Closed-World SHACL.
4. Provenance integrity (page >= 1, confidence >= 0.85) enforced.
"""

import pytest
from models.pre_ipo_shacl_engine import (
    validate_prospectus_graph,
    assert_capability_allowed_shacl,
    ExportBlockedError
)

# Benchmark fixture: HCCH authentic 100% OFS offer structure
HCCH_VALID_ABOX_TTL = """
@prefix fibo-sec-eq-ipo: <https://spec.edmcouncil.org/fibo/ontology/SEC/Equities/EquityInitialPublicOfferings/> .
@prefix fibo-sebi: <https://spec.profsur.org/fibo/sebi-icdr/> .
@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .

<https://spec.profsur.org/fibo/sebi-icdr/offering/HCCH-2026> a fibo-sec-eq-ipo:InitialPublicOffering ;
    fibo-sebi:totalIssueSizeCr "12500.00"^^xsd:decimal ;
    fibo-sebi:freshIssueCr "0.00"^^xsd:decimal ;
    fibo-sebi:offerForSaleCr "12500.00"^^xsd:decimal ;
    fibo-sebi:pageNumber 74 ;
    fibo-sebi:verbatimQuote "The Offer comprises an Offer for Sale of up to 997,500,000 Equity Shares with no fresh issue." ;
    fibo-sebi:confidenceScore "0.98"^^xsd:decimal .

<https://spec.profsur.org/fibo/sebi-icdr/promoter/HCCOH> a fibo-sebi:PromoterRole ;
    fibo-sebi:preIssueShareholdingPct "60.00"^^xsd:decimal ;
    fibo-sebi:postLockinPeriodDays 1080 ;
    fibo-sebi:pageNumber 82 ;
    fibo-sebi:verbatimQuote "HCCOH holds 60.00% of the pre-offer equity share capital of the company." ;
    fibo-sebi:confidenceScore "0.95"^^xsd:decimal .
"""

# Malicious / broken fixture: Math reconciliation mismatch
MATH_MISMATCH_ABOX_TTL = """
@prefix fibo-sec-eq-ipo: <https://spec.edmcouncil.org/fibo/ontology/SEC/Equities/EquityInitialPublicOfferings/> .
@prefix fibo-sebi: <https://spec.profsur.org/fibo/sebi-icdr/> .
@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .

<https://spec.profsur.org/fibo/sebi-icdr/offering/BROKEN-MATH> a fibo-sec-eq-ipo:InitialPublicOffering ;
    fibo-sebi:totalIssueSizeCr "10000.00"^^xsd:decimal ;
    fibo-sebi:freshIssueCr "2000.00"^^xsd:decimal ;
    fibo-sebi:offerForSaleCr "5000.00"^^xsd:decimal ;
    fibo-sebi:pageNumber 50 ;
    fibo-sebi:verbatimQuote "Total issue 10000 Cr, fresh 2000 Cr, OFS 5000 Cr." ;
    fibo-sebi:confidenceScore "0.90"^^xsd:decimal .
"""

# Missing statutory field fixture: Promoter without pre-issue shareholding
MISSING_PROMOTER_DISCLOSURE_TTL = """
@prefix fibo-sebi: <https://spec.profsur.org/fibo/sebi-icdr/> .
@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .

<https://spec.profsur.org/fibo/sebi-icdr/promoter/INCOMPLETE> a fibo-sebi:PromoterRole ;
    fibo-sebi:postLockinPeriodDays 365 ;
    fibo-sebi:pageNumber 85 ;
    fibo-sebi:verbatimQuote "Promoter shares locked in for 365 days." ;
    fibo-sebi:confidenceScore "0.90"^^xsd:decimal .
"""

# Broken provenance fixture: Page 0 and low confidence
BROKEN_PROVENANCE_TTL = """
@prefix fibo-sec-eq-ipo: <https://spec.edmcouncil.org/fibo/ontology/SEC/Equities/EquityInitialPublicOfferings/> .
@prefix fibo-sebi: <https://spec.profsur.org/fibo/sebi-icdr/> .
@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .

<https://spec.profsur.org/fibo/sebi-icdr/offering/LOW-CONF> a fibo-sec-eq-ipo:InitialPublicOffering ;
    fibo-sebi:totalIssueSizeCr "5000.00"^^xsd:decimal ;
    fibo-sebi:freshIssueCr "2500.00"^^xsd:decimal ;
    fibo-sebi:offerForSaleCr "2500.00"^^xsd:decimal ;
    fibo-sebi:pageNumber 0 ;
    fibo-sebi:verbatimQuote "Hallucinated statement with no authentic page" ;
    fibo-sebi:confidenceScore "0.55"^^xsd:decimal .
"""


def test_valid_hcch_offering_conforms():
    """Asserts that authentic HCCH filing with 0.0 fresh issue passes validation."""
    result = validate_prospectus_graph(HCCH_VALID_ABOX_TTL)
    assert result.conforms is True, f"Valid HCCH filing should conform, got: {result.raw_text}"
    assert result.violation_count == 0


def test_rule_e3_zero_truthiness_preservation():
    """Asserts that 0.0 fresh issue is valid and not rejected as absent."""
    result = validate_prospectus_graph(HCCH_VALID_ABOX_TTL)
    assert result.conforms is True
    # Export gate should pass without raising
    passed_result = assert_capability_allowed_shacl(HCCH_VALID_ABOX_TTL)
    assert passed_result.conforms is True


def test_mathematical_reconciliation_mismatch_fails_closed():
    """Asserts that Total != Fresh + OFS triggers a SPARQL constraint violation."""
    result = validate_prospectus_graph(MATH_MISMATCH_ABOX_TTL)
    assert result.conforms is False
    assert result.violation_count >= 1

    with pytest.raises(ExportBlockedError) as exc_info:
        assert_capability_allowed_shacl(MATH_MISMATCH_ABOX_TTL)
    assert "Statutory SHACL gate failed" in str(exc_info.value)


def test_missing_mandatory_promoter_field_fails_closed():
    """Asserts that omitting statutory pre-issue shareholding triggers a closed-world violation."""
    result = validate_prospectus_graph(MISSING_PROMOTER_DISCLOSURE_TTL)
    assert result.conforms is False
    assert any("preIssueShareholdingPct" in v.result_path for v in result.violations)

    with pytest.raises(ExportBlockedError):
        assert_capability_allowed_shacl(MISSING_PROMOTER_DISCLOSURE_TTL)


def test_broken_provenance_fails_statutory_gate():
    """Asserts that page < 1 and confidence < 0.85 are rejected."""
    result = validate_prospectus_graph(BROKEN_PROVENANCE_TTL)
    assert result.conforms is False
    assert result.violation_count >= 1
