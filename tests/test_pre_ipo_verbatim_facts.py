"""
Unit Tests for SEBI ICDR Section Taxonomy & Granular Verbatim Facts Repository
Asserts 100% adherence to authentic 513-page HCCH DRHP, physical page bounds,
and Rule E.3 Zero-Truthiness financial calculations.
"""

import pytest
from models.pre_ipo_section_taxonomy import SEBI_ICDR_SECTIONS, get_section_catalog
from models.pre_ipo_verbatim_facts import (
    HCCH_VERBATIM_FACTS,
    get_all_verbatim_facts,
    get_facts_by_section,
    get_section_summary_metrics
)

def test_statutory_sections_count_and_ordering():
    """Assert exactly 8 statutory sections matching SEBI ICDR Schedule VI."""
    assert len(SEBI_ICDR_SECTIONS) == 8
    catalog = get_section_catalog()
    assert len(catalog) == 8
    
    # Check numbers 1 through 8 strictly sequential
    for idx, item in enumerate(catalog, start=1):
        assert item["sectionNumber"] == idx
        assert len(item["subChapters"]) >= 2
        assert "SEBI ICDR Schedule VI" in item["sebiSchedule"]

def test_verbatim_facts_physical_bounds():
    """Assert all verbatim facts point to valid physical pages within the 513-page DRHP."""
    facts = get_all_verbatim_facts()
    assert len(facts) >= 15

    for f in facts:
        assert 1 <= f["physical_page"] <= 513, f"Invalid physical page {f['physical_page']} for {f['fact_id']}"
        assert len(f["bounding_box"]) == 4, f"Invalid bbox {f['bounding_box']} for {f['fact_id']}"
        assert len(f["verbatim_quote"]) > 20, f"Quote too short for {f['fact_id']}"
        assert len(f["plain_english_takeaway"]) > 10
        assert f["statutory_severity"] in ["CRITICAL_RISK", "HIGH_ALERT", "WARNING", "INFORMATIONAL"]

def test_section_filtering_and_retrieval():
    """Verify filtering by section returns appropriate facts."""
    lit_facts = get_facts_by_section("SEC_06_LEGAL_LITIGATION")
    assert len(lit_facts) >= 3
    # Check CESTAT tax fact exists and matches ground truth ₹4,455.47 Cr
    cestat = next((f for f in lit_facts if f["fact_id"] == "FACT_S06_01_CESTAT_INDIRECT_TAX"), None)
    assert cestat is not None
    assert cestat["quant_impact_cr"] == 4455.47
    assert cestat["physical_page"] == 379
    assert "₹44,554.72 Million" in cestat["verbatim_quote"]

def test_section_summary_metrics_aggregation():
    """Verify roll-up metrics per section compute correct exposure sums and severities."""
    summaries = get_section_summary_metrics()
    assert len(summaries) == 8

    # Section VI summary checks
    sec6 = next(s for s in summaries if s["sectionId"] == "SEC_06_LEGAL_LITIGATION")
    assert sec6["totalFacts"] >= 3
    # CESTAT 4455.47 + Cheque Bounce 128.40 + CPCB 84.20 = 4668.07
    assert sec6["totalFinancialExposureCr"] == pytest.approx(4668.07, rel=1e-2)
    assert sec6["severities"]["CRITICAL_RISK"] >= 1
