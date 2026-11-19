"""
Adversarial Unit Test Suite for Pre-IPO GraphRAG Router
Milestone 15 (Phase 2B)

Verifies:
- Intent classification precision for Novice and Advanced financial queries
- Closed-world fail-closed boundary protection against ungrounded hallucinations
- Physical PDF page and bounding box coordinate fidelity (W3C PROV-O)
- Rule E.3 Zero-Truthiness and empty query safety
- Dual-head prompt catalog integrity
"""

import pytest
from models.pre_ipo_graphrag_router import PreIPOGraphRAGRouter, GraphRAGResult


@pytest.fixture
def router():
    return PreIPOGraphRAGRouter()


def test_cestat_litigation_intent_and_coordinates(router):
    """Verifies litigation query resolves to CESTAT fact and page 379 coordinates."""
    res = router.route_query("What happens if CESTAT tax dispute is lost?")
    assert isinstance(res, GraphRAGResult)
    assert res.intent == "LITIGATION_STRESS"
    assert res.template_id == "Q11_HOLDCO_VS_SUB_LITIGATION"
    assert "MATCH (e:LegalEntity)-[:DEFENDANT_IN]->(lit:Litigation)" in res.cypher_query
    assert res.severity == "CRITICAL"
    assert res.target_page == 379
    assert res.bounding_box == [0.18, 0.08, 0.35, 0.92]
    assert res.can_simulate_shock is True
    assert res.shock_fact_id == "FACT_S06_01_CESTAT_INDIRECT_TAX"
    assert len(res.matched_node_ids) >= 3
    assert len(res.matched_edge_ids) >= 2
    assert "4,455.47 Cr" in res.summary_markdown


def test_supplier_concentration_intent(router):
    """Verifies concentrate raw material query resolves to Section 2 / Q08."""
    res = router.route_query("Are there sole source supplier dependencies for concentrate syrup?")
    assert res.intent == "SUPPLIER_CONCENTRATION"
    assert res.template_id == "Q08_PARENT_SUPPLY_CONCENTRATION"
    assert res.target_page == 74
    assert res.primary_fact is not None
    assert "Concentrate Supply Agreement" in res.primary_fact["entity_name"]
    assert res.can_simulate_shock is True


def test_promoter_lockin_intent(router):
    """Verifies anchor/promoter lockin query resolves to Q03 and page 154."""
    res = router.route_query("When does anchor investor lock-in expire?")
    assert res.intent == "PROMOTER_LOCKIN"
    assert res.template_id == "Q03_LOCKIN_SUPPLY_WALLS"
    assert res.target_page == 154
    assert res.primary_fact["statutory_topic"] == "Promoter Contribution & 18-Month Lock-in"


def test_fail_closed_on_unrelated_inquiry(router):
    """Rule E.2: Ungrounded queries must fail closed with zero hallucination."""
    res = router.route_query("What is the recipe for baking chocolate cake?")
    assert res.intent == "UNGROUNDED_INQUIRY"
    assert res.template_id is None
    assert res.provenance_score == 0.0
    assert len(res.matched_node_ids) == 0
    assert "Grounded Prospectus Boundary Gate" in res.summary_markdown
    assert len(res.suggested_followups) >= 3


def test_rule_e3_empty_query_safety(router):
    """Rule E.3: Empty or whitespace query must fail closed safely without error."""
    res1 = router.route_query("")
    assert res1.intent == "UNGROUNDED_INQUIRY"

    res2 = router.route_query("    ")
    assert res2.intent == "UNGROUNDED_INQUIRY"


def test_suggested_prompts_dual_head(router):
    """Verifies Novice and Advanced prompt library integrity."""
    prompts = router.get_suggested_prompts("HCCH")
    assert "novice" in prompts
    assert "advanced" in prompts
    assert len(prompts["novice"]) >= 5
    assert len(prompts["advanced"]) >= 5

    for p in prompts["novice"] + prompts["advanced"]:
        assert "label" in p and len(p["label"]) > 5
        assert "intent" in p
        assert "badge" in p
        assert "icon" in p
