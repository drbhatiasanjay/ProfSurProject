"""
TDD Unit Test Suite for Workstream 2: Citation Inspector / Academic Literature Vault
Covers:
- TC-CIT-01: Dickinson (2011) lifecycle cash flow metadata & DOI validation
- TC-CIT-02: Rajan & Zingales (1995) cross-country determinants & DOI validation
- TC-CIT-03: Graceful fallback for unindexed citations
- TC-CIT-04: Strict catalog schema validation for all registered citations
"""

import re
import pytest

from models.citation_vault_metadata import (
    get_citation_metadata,
    list_all_citations,
    format_bibtex,
    format_apa,
    CITATION_CATALOG,
)


def test_tc_cit_01_dickinson_metadata():
    """TC-CIT-01: Dickinson (2011) returns structured lifecycle metadata and valid DOI."""
    meta = get_citation_metadata("Dickinson (2011)")
    assert meta is not None
    assert "Dickinson" in meta["authors"]
    assert meta["year"] == 2011
    assert "The Accounting Review" in meta["journal"]
    assert meta["doi"].startswith("https://doi.org/10.2308/accr-10130")
    assert "cash flow" in meta["theoretical_mechanism"].lower()
    assert "8,677" in meta["indian_panel_relevance"] or "panel" in meta["indian_panel_relevance"].lower()
    
    bib = format_bibtex(meta)
    assert bib.startswith("@article{dickinson2011")
    assert "accr-10130" in bib
    
    apa = format_apa(meta)
    assert "Dickinson, V. (2011)" in apa


def test_tc_cit_02_rajan_zingales_metadata():
    """TC-CIT-02: Rajan & Zingales (1995) returns cross-country determinants and valid DOI."""
    meta = get_citation_metadata("Rajan & Zingales (1995)")
    assert meta is not None
    assert "Rajan" in meta["authors"]
    assert meta["year"] == 1995
    assert "Journal of Finance" in meta["journal"]
    assert meta["doi"].startswith("https://doi.org/10.1111/j.1540-6261.1995.tb05184.x")
    assert "capital structure" in meta["title"].lower()
    assert "tangibility" in meta["empirical_benchmark"].lower()


def test_tc_cit_03_fallback_unindexed():
    """TC-CIT-03: Unindexed query falls back gracefully without KeyError."""
    meta = get_citation_metadata("NonExistentScholar (2099)")
    assert meta is not None
    assert meta["is_fallback"] is True
    assert "title" in meta
    assert "doi" in meta
    assert meta["doi"].startswith("https://doi.org/")


def test_tc_cit_04_schema_validation_all_citations():
    """TC-CIT-04: All catalog citations conform to schema and RFC 3986 HTTPS DOI format."""
    citations = list_all_citations()
    assert len(citations) >= 8, f"Expected at least 8 core finance citations, got {len(citations)}"
    
    doi_pattern = re.compile(r"^https://doi\.org/10\.\d{4,9}/[-._;()/:A-Za-z0-9]+$")
    
    for key, item in CITATION_CATALOG.items():
        assert "title" in item, f"Missing title in {key}"
        assert "authors" in item, f"Missing authors in {key}"
        assert "year" in item and isinstance(item["year"], int), f"Invalid year in {key}"
        assert "journal" in item, f"Missing journal in {key}"
        assert "doi" in item, f"Missing doi in {key}"
        assert doi_pattern.match(item["doi"]), f"Invalid DOI URI format: {item['doi']} in {key}"
        assert "theoretical_mechanism" in item, f"Missing mechanism in {key}"
        assert "indian_panel_relevance" in item, f"Missing Indian relevance in {key}"
        assert "empirical_benchmark" in item, f"Missing empirical benchmark in {key}"
