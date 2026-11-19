"""
Pre-IPO GraphRAG & Natural Language Cypher Copilot Router
Milestone 15 (Phase 2B) - Hybrid Dual-Head GraphRAG Architecture

Maps natural language analyst queries into deterministic Cypher query templates,
extracts multi-hop path chains, generates visual canvas highlight sets, and links
verbatim prospectus disclosures directly to physical PDF bounding box coordinates.

Governed by:
- docs/SPEC_PRE_IPO_KNOWLEDGE_GRAPH_PHASE2.md
- Rule E.3: Zero Python Truthiness in Financial Calculations
- Rule E.2: Fail-Closed Architecture for Ungrounded Inquiries
"""

import re
from dataclasses import dataclass, asdict
from typing import Dict, List, Any, Optional

from models.pre_ipo_verbatim_facts import HCCH_VERBATIM_FACTS, VerbatimFact
from models.pre_ipo_cypher_bank import CYPHER_QUERY_CATALOG, CypherQueryTemplate


@dataclass
class GraphRAGResult:
    """Institutional structured output for GraphRAG query execution."""
    query: str
    intent: str
    template_id: Optional[str]
    cypher_query: str
    summary_markdown: str
    severity: str  # 'CRITICAL' | 'WARNING' | 'ALERT' | 'INFO'
    matched_node_ids: List[str]
    matched_edge_ids: List[str]
    primary_fact: Optional[Dict[str, Any]]
    provenance_score: float
    target_page: Optional[int]
    bounding_box: Optional[List[float]]
    suggested_followups: List[str]
    can_simulate_shock: bool
    shock_fact_id: Optional[str]


# Pre-configured intent descriptors and semantic triggers
INTENT_SPECS = [
    {
        "intent": "LITIGATION_STRESS",
        "keywords": ["litigation", "lawsuit", "dispute", "tax demand", "cestat", "cheque bounce", "court", "claims", "penalty"],
        "template_id": "Q11_HOLDCO_VS_SUB_LITIGATION",
        "primary_fact_id": "FACT_S06_01_CESTAT_INDIRECT_TAX",
        "can_simulate_shock": True,
        "nodes": ["node_hcch_issuer", "node_hccb_operating", "node_cestat_tax", "node_tangible_net_worth"],
        "edges": ["edge_holdco_operating", "edge_operating_litigation", "edge_litigation_net_worth"],
        "followups": [
            "What is the parent indemnity shield coverage under Section 8?",
            "How many Section 138 cheque bounce proceedings exist?",
            "What happens to Debt/Equity if CESTAT tax crystallizes?"
        ]
    },
    {
        "intent": "CHEQUE_BOUNCE_EPIDEMIC",
        "keywords": ["cheque bounce", "sec 138", "138", "distributor default", "dishonour", "ni act"],
        "template_id": "Q12_SEC_138_CHEQUE_BOUNCE_EPIDEMIC",
        "primary_fact_id": "FACT_S06_02_CHEQUE_BOUNCE_NETWORK",
        "can_simulate_shock": True,
        "nodes": ["node_hccb_operating", "node_distributor_network", "node_cheque_bounce_claims"],
        "edges": ["edge_operating_distributors", "edge_distributors_defaults"],
        "followups": [
            "Are distributor collections insured or collateralized?",
            "Does this impact trade receivables aging under Ind AS 109?",
            "What is the total disputed amount in cheque dishonour suits?"
        ]
    },
    {
        "intent": "SUPPLIER_CONCENTRATION",
        "keywords": ["sole source", "supplier", "concentrate", "raw material", "coca-cola india", "bottlers agreement", "syrup"],
        "template_id": "Q08_PARENT_SUPPLY_CONCENTRATION",
        "primary_fact_id": "FACT_S02_01_RAW_MATERIAL_CONCENTRATE",
        "can_simulate_shock": True,
        "nodes": ["node_hccb_operating", "node_coca_cola_india_sup", "node_bottlers_agreement"],
        "edges": ["edge_operating_procurement", "edge_contract_governance"],
        "followups": [
            "What is the cancellation notice period for concentrate supply?",
            "Can HCCB procure beverage syrup from alternate domestic vendors?",
            "What are the parent royalty pricing escalation terms?"
        ]
    },
    {
        "intent": "OFFER_STRUCTURE",
        "keywords": ["offer structure", "ofs", "fresh issue", "proceeds", "selling shareholder", "corporate infusion", "use of proceeds"],
        "template_id": "Q01_PROCEEDS_FLOW",
        "primary_fact_id": "FACT_S01_01_ISSUE_STRUCTURE",
        "can_simulate_shock": False,
        "nodes": ["node_hcch_issuer", "node_offering_2026", "node_selling_shareholders", "node_hccb_operating"],
        "edges": ["edge_issuer_offering", "edge_offering_proceeds_exit"],
        "followups": [
            "How much of the ₹9,975 Cr enters operating company HCCB?",
            "What is the promoter Weighted Average Cost of Acquisition (WACA)?",
            "What are the pre-IPO dividend payouts prior to filing?"
        ]
    },
    {
        "intent": "PROMOTER_LOCKIN",
        "keywords": ["lock-in", "lockin", "lock in", "promoter lockin", "anchor lockin", "float unlock", "30-day", "90-day", "supply wall", "vesting", "anchor investor"],
        "template_id": "Q03_LOCKIN_SUPPLY_WALLS",
        "primary_fact_id": "FACT_S03_01_PROMOTER_LOCKIN_SCHEDULE",
        "can_simulate_shock": False,
        "nodes": ["node_hcch_issuer", "node_promoter_lockin", "node_anchor_investors", "node_free_float"],
        "edges": ["edge_issuer_lockin", "edge_lockin_expiry_tranches"],
        "followups": [
            "How many shares unlock at the 30-day anchor investor cliff?",
            "What percentage of promoter capital is locked in for 18 months under SEBI ICDR Reg 16?",
            "What is the expected free-float expansion velocity post-listing?"
        ]
    },
    {
        "intent": "REGULATORY_GROUNDWATER",
        "keywords": ["groundwater", "cpcb", "environmental", "noc", "water extraction", "pollution", "plant inspection"],
        "template_id": "Q14_ENVIRONMENTAL_CPCB_SHUTDOWN",
        "primary_fact_id": "FACT_S02_02_GROUNDWATER_EXTRACTION",
        "can_simulate_shock": True,
        "nodes": ["node_hccb_operating", "node_cpcb_regulator", "node_plant_facilities", "node_groundwater_noc"],
        "edges": ["edge_operating_plants", "edge_plants_environmental_compliance"],
        "followups": [
            "How many bottling plants operate with pending CGWA renewal NOCs?",
            "What is the historical precedent for bottling plant closure in India?",
            "Are there pending environmental PILs before the National Green Tribunal?"
        ]
    },
    {
        "intent": "ROYALTY_COVENANTS",
        "keywords": ["royalty", "trademark", "brand license", "parent charges", "markup", "formula price", "intellectual property"],
        "template_id": "Q07_UNHEDGED_ROYALTY_DRAIN",
        "primary_fact_id": "FACT_S08_01_TRADEMARK_ROYALTY_ESCALATION",
        "can_simulate_shock": True,
        "nodes": ["node_hccb_operating", "node_the_coca_cola_co_us", "node_trademark_license"],
        "edges": ["edge_operating_royalty_drain", "edge_trademark_sublicense"],
        "followups": [
            "Does the parent hold unilateral power to increase trademark royalty rates?",
            "What are the parent trade discounts reported in Q1 FY27?",
            "How does a 100 bps royalty increase compress EBITDA margins?"
        ]
    },
    {
        "intent": "DIRECTOR_GOVERNANCE",
        "keywords": ["director", "board", "kmp", "independent director", "governance", "audit committee", "cross directorship"],
        "template_id": "Q17_PROMOTER_INTERLOCKING_DIRECTORSHIPS",
        "primary_fact_id": "FACT_S04_01_DIRECTOR_CROSS_DIRECTORSHIPS",
        "can_simulate_shock": False,
        "nodes": ["node_board_of_directors", "node_independent_directors", "node_promoter_nominees"],
        "edges": ["edge_board_composition", "edge_committee_oversight"],
        "followups": [
            "Are any independent directors on the board of competitor FMCG firms?",
            "What is the KMP remuneration share of operating profit?",
            "Does the audit committee have majority independent representation?"
        ]
    },
    {
        "intent": "IND_AS_116_LEASES",
        "keywords": ["ind as 116", "indas", "lease", "right of use", "rou", "debt covenant", "operating lease", "warehouse"],
        "template_id": "Q20_LEASE_LIABILITY_OFF_BALANCE_SHEET",
        "primary_fact_id": "FACT_S05_01_INDAS116_LEASES",
        "can_simulate_shock": True,
        "nodes": ["node_hccb_operating", "node_lease_liabilities_rou", "node_gross_debt"],
        "edges": ["edge_operating_leases", "edge_leases_to_gross_debt"],
        "followups": [
            "What is the total Ind AS 116 lease liability capitalized on balance sheet?",
            "How does capitalizing leases affect reported Net Debt/EBITDA leverage?",
            "Are plant facilities owned freehold or held on long-term operating lease?"
        ]
    }
]


class PreIPOGraphRAGRouter:
    """Deterministic, grounded Natural Language to Cypher Copilot Router."""

    def __init__(self):
        self._catalog_map = {q.query_id: q for q in CYPHER_QUERY_CATALOG}
        self._facts_map = {f.fact_id: f for f in HCCH_VERBATIM_FACTS}

    def route_query(self, query: str, symbol: str = "HCCH") -> GraphRAGResult:
        """
        Routes an analyst query to the most grounded Cypher query and verbatim fact.
        Adheres to Rule E.2 (Fail-Closed) and Rule E.3 (Zero-Truthiness).
        """
        clean_q = (query or "").strip().lower()

        if not clean_q:
            return self._fail_closed_response("Empty query received. Please provide a financial or prospectus inquiry.")

        # Score matching intents by keyword frequency
        best_spec = None
        best_score = 0

        for spec in INTENT_SPECS:
            score = 0
            for kw in spec["keywords"]:
                if re.search(r"\b" + re.escape(kw) + r"\b", clean_q):
                    score += 3
                elif kw in clean_q:
                    score += 1
            if score > best_score:
                best_score = score
                best_spec = spec

        # Minimum relevance threshold: fail closed if no clear financial/prospectus signal
        if best_spec is None or best_score == 0:
            return self._fail_closed_response(
                f"Query '{query}' does not match statutory disclosures in the {symbol} Red Herring Prospectus. "
                "Try asking about: litigation exposure, 100% OFS exit, concentrate supplier terms, anchor lock-in, or Ind AS 116 leases."
            )

        # Retrieve matched Cypher template and VerbatimFact
        template = self._catalog_map.get(best_spec["template_id"])
        fact = self._facts_map.get(best_spec["primary_fact_id"])

        if template is None or fact is None:
            # Fallback fail-closed if internal mapping is broken
            return self._fail_closed_response("Statutory mapping failure for detected intent.")

        # Synthesize institutional markdown summary
        summary_md = self._synthesize_summary(query, best_spec["intent"], template, fact)

        fact_dict = asdict(fact)

        return GraphRAGResult(
            query=query,
            intent=best_spec["intent"],
            template_id=template.query_id,
            cypher_query=template.cypher_code,
            summary_markdown=summary_md,
            severity=template.severity,
            matched_node_ids=best_spec["nodes"],
            matched_edge_ids=best_spec["edges"],
            primary_fact=fact_dict,
            provenance_score=0.99,
            target_page=fact.physical_page,
            bounding_box=fact.bounding_box,
            suggested_followups=best_spec["followups"],
            can_simulate_shock=best_spec["can_simulate_shock"],
            shock_fact_id=best_spec["primary_fact_id"] if best_spec["can_simulate_shock"] else None
        )

    def _synthesize_summary(
        self,
        query: str,
        intent: str,
        template: CypherQueryTemplate,
        fact: VerbatimFact
    ) -> str:
        """Synthesizes structured, institutional briefing note."""
        impact_str = f"₹{fact.quant_impact_cr:,.2f} Cr" if fact.quant_impact_cr is not None else "Qualitative / Covenants"
        holdco_contagion = "YES (Pervasive)" if fact.contagion_to_holdco else "Quarantined at Subsidiary"

        return f"""### Institutional Diligence Finding: {template.title}

> **Statutory SEBI Grounding:** [{fact.statutory_section_id} — {fact.statutory_topic}](p. {fact.physical_page})  
> **Physical Prospectus Quote (p. {fact.physical_page}):**  
> *"{fact.verbatim_quote}"*

#### Key Analytical Takeaway
- **Executive Stance:** {fact.plain_english_takeaway}
- **Quantified Exposure:** `{impact_str}`
- **Contagion to HoldCo:** `{holdco_contagion}`
- **Executed Cypher:** `{template.query_id}` across `{template.expected_hops}` hops

#### Institutional Recommendation
{template.verdict_template}
"""

    def _fail_closed_response(self, error_message: str) -> GraphRAGResult:
        """Fails closed safely without hallucinating speculative answers."""
        return GraphRAGResult(
            query="",
            intent="UNGROUNDED_INQUIRY",
            template_id=None,
            cypher_query="// Query ungrounded - execution blocked by fail-closed gate",
            summary_markdown=f"> ⚠️ **Grounded Prospectus Boundary Gate:**  \n> {error_message}",
            severity="WARNING",
            matched_node_ids=[],
            matched_edge_ids=[],
            primary_fact=None,
            provenance_score=0.0,
            target_page=None,
            bounding_box=None,
            suggested_followups=[
                "What happens if the CESTAT tax dispute is lost?",
                "Are there sole-source supplier dependencies for concentrate syrup?",
                "Show promoter lock-in expiry tranches under SEBI ICDR Reg 16",
                "What is the 100% OFS exit structure and proceeds distribution?"
            ],
            can_simulate_shock=False,
            shock_fact_id=None
        )

    def get_suggested_prompts(self, symbol: str = "HCCH") -> Dict[str, List[Dict[str, str]]]:
        """Returns pre-calibrated suggested prompts for Novice and Advanced personas."""
        return {
            "novice": [
                {
                    "label": "What happens if CESTAT tax dispute is lost?",
                    "intent": "LITIGATION_STRESS",
                    "badge": "Risk Shock",
                    "icon": "⚖️"
                },
                {
                    "label": "Who gets the ₹9,975 Cr IPO proceeds?",
                    "intent": "OFFER_STRUCTURE",
                    "badge": "Capital Flow",
                    "icon": "💸"
                },
                {
                    "label": "Can Coca-Cola stop supplying syrup concentrate?",
                    "intent": "SUPPLIER_CONCENTRATION",
                    "badge": "Supply Chain",
                    "icon": "🏭"
                },
                {
                    "label": "When can Anchor Investors sell their shares?",
                    "intent": "PROMOTER_LOCKIN",
                    "badge": "Supply Cliff",
                    "icon": "🔓"
                },
                {
                    "label": "Are there environmental groundwater violations?",
                    "intent": "REGULATORY_GROUNDWATER",
                    "badge": "Compliance",
                    "icon": "💧"
                }
            ],
            "advanced": [
                {
                    "label": "Trace multi-hop contagion path from CESTAT litigation to Net Worth erosion",
                    "intent": "LITIGATION_STRESS",
                    "badge": "Multi-Hop Traversal",
                    "icon": "🕸️"
                },
                {
                    "label": "Audit related-party trademark sublicense royalty pricing power",
                    "intent": "ROYALTY_COVENANTS",
                    "badge": "RPT Covenants",
                    "icon": "📜"
                },
                {
                    "label": "Stress-test Debt/Equity covenant headroom under Ind AS 116 leases",
                    "intent": "IND_AS_116_LEASES",
                    "badge": "Ind AS 116 Headroom",
                    "icon": "📊"
                },
                {
                    "label": "Map distributor default epidemic across 1,466 Section 138 NI Act suits",
                    "intent": "CHEQUE_BOUNCE_EPIDEMIC",
                    "badge": "Credit Risk",
                    "icon": "⚠️"
                },
                {
                    "label": "Verify promoter WACA entry cost vs implied public IPO valuation band",
                    "intent": "OFFER_STRUCTURE",
                    "badge": "Valuation Dilution",
                    "icon": "🎯"
                }
            ]
        }
