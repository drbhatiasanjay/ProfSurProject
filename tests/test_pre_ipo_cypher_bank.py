"""
Unit Tests for Pre-IPO Bank of Cypher Queries & Formula Lineage Register
Milestone 12 - MANUS Verification Protocol
"""

import pytest
from models.pre_ipo_kg_engine import PreIPOPropertyGraphEngine
from models.pre_ipo_kg_ingest import ingest_hcch_benchmark_graph
from models.pre_ipo_cypher_bank import (
    get_cypher_bank_catalog,
    get_query_template_by_id,
    execute_cypher_bank_query,
    CYPHER_QUERY_CATALOG
)
from models.pre_ipo_formula_lineage import (
    get_all_formula_lineages,
    get_formula_by_id,
    execute_formula_lineage_calc,
    STATUTORY_SECTIONS
)


@pytest.fixture
def in_memory_engine():
    engine = PreIPOPropertyGraphEngine(in_memory=True)
    ingest_hcch_benchmark_graph(engine)
    yield engine
    try:
        engine.conn.close()
    except Exception:
        pass


def test_statutory_sections_count():
    """Asserts that exactly 10 statutory SEBI ICDR sections are registered."""
    assert len(STATUTORY_SECTIONS) == 10
    total_attrs = sum(s["attributeCount"] for s in STATUTORY_SECTIONS)
    assert total_attrs == 84


def test_formula_lineage_catalog_integrity():
    """Asserts that all formula lineages define valid LaTeX, target vaults, and constituent attributes."""
    lineages = get_all_formula_lineages()
    assert len(lineages) >= 9
    for f in lineages:
        assert len(f["formulaId"]) > 0
        assert len(f["name"]) > 0
        assert len(f["latexFormula"]) > 0
        assert len(f["constituentAttributes"]) > 0
        assert "targetVault" in f


def test_deal_integrity_formula_zero_truthiness():
    """Asserts Rule E.3: 0.0 fresh issue is valid and passes reconciliation."""
    attrs = {
        "total_issue_size_cr": 9975.0,
        "fresh_issue_cr": 0.0,  # 0.0 is valid, not None!
        "ofs_issue_cr": 9975.0
    }
    res = execute_formula_lineage_calc("deal_integrity_reconciliation", attrs)
    assert res["conforms"] is True
    assert res["status"] == "PASS"
    assert res["resultValue"] == 0.0


def test_gcp_statutory_ceiling_calculation():
    """Asserts GCP <= 25% passes and > 25% fails closed."""
    # Compliant 25.0%
    res1 = execute_formula_lineage_calc("gcp_statutory_ceiling", {"gcp_allocation_cr": 2493.75, "total_issue_size_cr": 9975.0})
    assert res1["conforms"] is True
    assert res1["status"] == "COMPLIANT"

    # Non-compliant 30.0%
    res2 = execute_formula_lineage_calc("gcp_statutory_ceiling", {"gcp_allocation_cr": 3000.0, "total_issue_size_cr": 9975.0})
    assert res2["conforms"] is False
    assert res2["status"] == "NON_COMPLIANT"


def test_cypher_bank_catalog_size_and_categories():
    """Asserts that the Cypher query bank contains 25 pre-compiled queries across 5 categories."""
    catalog = get_cypher_bank_catalog()
    assert len(catalog) == 25
    categories = {q["category"] for q in catalog}
    assert len(categories) == 5
    assert "Capital Structure & OFS Flow" in categories
    assert "Related Party & Earnings Quality" in categories
    assert "Litigation & Contagion" in categories
    assert "Debt & Solvency" in categories
    assert "Statutory Objects & Valuation" in categories


def test_cypher_bank_execution_proceeds_flow(in_memory_engine):
    """Asserts Q01_PROCEEDS_FLOW returns 100% OFS exit verdict and DRHP citations."""
    res = execute_cypher_bank_query("Q01_PROCEEDS_FLOW", in_memory_engine)
    assert res["queryId"] == "Q01_PROCEEDS_FLOW"
    assert "100% OFS" in res["verdict"]
    assert len(res["citations"]) >= 2
    assert "HCCH" in res["subgraph"]["nodes"]


def test_cypher_bank_execution_litigation_contagion(in_memory_engine):
    """Asserts Q11_HOLDCO_VS_SUB_LITIGATION pierces the corporate veil."""
    res = execute_cypher_bank_query("Q11_HOLDCO_VS_SUB_LITIGATION", in_memory_engine)
    assert res["queryId"] == "Q11_HOLDCO_VS_SUB_LITIGATION"
    assert "4,455.47 Cr" in res["verdict"]
    assert len(res["table"]) == 3
    assert res["severity"] == "CRITICAL"
