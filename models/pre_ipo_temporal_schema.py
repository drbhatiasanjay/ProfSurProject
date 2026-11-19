"""
Pre-IPO Bi-Temporal Knowledge Graph & Filing Comparison Schemas
Milestone 19 - Temporal Knowledge Graph & Multi-DRHP Filing Comparison Diff Engine

Governed by:
- docs/PRD_TEMPORAL_KNOWLEDGE_GRAPH_DIFF_ENGINE.md
- docs/TECH_SPEC_TEMPORAL_KNOWLEDGE_GRAPH.md
- Rule E.2: Fail-Closed Architecture (FilingNotFoundError)
- Rule E.3: Zero-Truthiness Financial Calculations
"""

from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any, Literal


class FilingNotFoundError(Exception):
    """Raised when an unindexed or invalid filing milestone is requested (Rule E.2)."""
    pass


MutationType = Literal[
    "BRACKET_RESOLVED",       # Placeholder [○] replaced by final number
    "ENTITY_ADDED",          # New legal entity/counterparty added
    "SEVERED_RELATION",      # Agreement or connection terminated
    "MUTATED_PROPERTY",      # Value changed (e.g., share count, debt amount)
    "QUALIFIER_WATERED_DOWN" # Legal watering down of obligation
]

SEBIChapter = Literal[
    "CHAPTER_I_RISK_FACTORS",
    "CHAPTER_II_CAPITAL_STRUCTURE",
    "CHAPTER_III_OBJECTS_OF_ISSUE",
    "CHAPTER_IV_BASIS_FOR_PRICE",
    "CHAPTER_V_INDUSTRY_OVERVIEW",
    "CHAPTER_VI_BUSINESS_OVERVIEW",
    "CHAPTER_VII_MANAGEMENT_GOVERNANCE",
    "CHAPTER_VIII_RELATED_PARTY_TRANSACTIONS",
    "CHAPTER_IX_FINANCIAL_STATEMENTS",
    "CHAPTER_X_LEGAL_OUTSTANDING_LITIGATION",
    "CHAPTER_XI_OTHER_REGULATORY_DISCLOSURES"
]


@dataclass(frozen=True)
class TemporalBoundingBox:
    """Represents verbatim text with exact physical coordinates in a filing."""
    page_number: int
    x: float
    y: float
    width: float
    height: float
    verbatim_text: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "page_number": self.page_number,
            "x": self.x,
            "y": self.y,
            "width": self.width,
            "height": self.height,
            "verbatim_text": self.verbatim_text
        }


@dataclass
class TemporalQuad:
    """Bi-temporal knowledge graph quadruple: (s, p, o, [t_valid_start, t_valid_end])."""
    subject: str
    predicate: str
    object_val: str
    t_valid_start: str
    t_valid_end: Optional[str] = None
    sebi_chapter: str = "CHAPTER_I_RISK_FACTORS"
    bbox: Optional[TemporalBoundingBox] = None


@dataclass
class TemporalGraphMutation:
    """Represents a discrete semantic mutation between two filing versions."""
    mutation_id: str
    subject_entity: str
    predicate: str
    change_type: MutationType
    sebi_chapter: str
    drhp_value: Optional[str]
    rhp_value: str
    drhp_bbox: Optional[TemporalBoundingBox]
    rhp_bbox: TemporalBoundingBox
    obfuscation_severity: float          # 0.0 (benign) to 1.0 (severe evasion)
    valuation_impact_inr: float          # Direct impact on equity valuation (in INR Cr)
    wacc_spread_shift_bps: float         # WACC adjustment (+bps)
    w3c_prov_citation: str
    summary_explanation: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "mutation_id": self.mutation_id,
            "subject_entity": self.subject_entity,
            "predicate": self.predicate,
            "change_type": self.change_type,
            "sebi_chapter": self.sebi_chapter,
            "drhp_value": self.drhp_value,
            "rhp_value": self.rhp_value,
            "drhp_bbox": self.drhp_bbox.to_dict() if self.drhp_bbox is not None else None,
            "rhp_bbox": self.rhp_bbox.to_dict(),
            "obfuscation_severity": self.obfuscation_severity,
            "valuation_impact_inr": self.valuation_impact_inr,
            "wacc_spread_shift_bps": self.wacc_spread_shift_bps,
            "w3c_prov_citation": self.w3c_prov_citation,
            "summary_explanation": self.summary_explanation
        }


@dataclass
class TemporalGraphDiffResult:
    """Consolidated outcome of bi-temporal graph diffing."""
    symbol: str
    base_version: str
    target_version: str
    base_date: str
    target_date: str
    total_mutations: int
    mutations: List[TemporalGraphMutation]
    chapter_drift_scores: Dict[str, float]
    net_valuation_impact_inr: float
    net_wacc_spread_shift_bps: float
    overall_obfuscation_index: float

    def to_dict(self) -> Dict[str, Any]:
        return {
            "symbol": self.symbol,
            "base_version": self.base_version,
            "target_version": self.target_version,
            "base_date": self.base_date,
            "target_date": self.target_date,
            "total_mutations": self.total_mutations,
            "mutations": [m.to_dict() for m in self.mutations],
            "chapter_drift_scores": self.chapter_drift_scores,
            "net_valuation_impact_inr": self.net_valuation_impact_inr,
            "net_wacc_spread_shift_bps": self.net_wacc_spread_shift_bps,
            "overall_obfuscation_index": self.overall_obfuscation_index
        }
