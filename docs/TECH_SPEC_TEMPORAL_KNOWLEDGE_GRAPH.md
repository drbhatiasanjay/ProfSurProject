# Technical Specification: Bi-Temporal Knowledge Graph & Multi-Filing Comparison Diff Engine

**Document Version:** 1.0.0  
**Target Architecture:** FastAPI Backend · React / Vite Frontend · Bi-Temporal RDF Quads · Neo4j Cypher Compatible  

---

## 1. System Architecture

```
                               ┌─────────────────────────────────────────────────────────────┐
                               │                    FastAPI Backend (8000)                   │
                               │                                                             │
                               │  models/pre_ipo_temporal_schema.py                          │
                               │  • Bi-Temporal Quad Data Structures                         │
                               │  • SEBI ICDR Schedule VI Enumerations                       │
                               │                                                             │
                               │  models/pre_ipo_temporal_diff_engine.py                     │
                               │  • Isomorphic Graph Comparison: O(|V| + |E|)                │
                               │  • Cohen-Malloy Obfuscation Index Calculator                │
                               │  • Valuation & WACC Ripple Propagation Engine               │
                               │                                                             │
                               │  api/server.py                                              │
                               │  • GET /api/pre-ipo/kg/temporal/versions                    │
                               │  • GET /api/pre-ipo/kg/temporal/diff                        │
                               │  • GET /api/pre-ipo/kg/temporal/verbatim-redline            │
                               └──────────────────────────────┬──────────────────────────────┘
                                                              │ JSON Payloads
                                                              ▼
                               ┌─────────────────────────────────────────────────────────────┐
                               │              React 18 / TypeScript Frontend (5173 / 5174)   │
                               │                                                             │
                               │  frontend/src/types/terminal.ts                             │
                               │  • Discriminated Union: TemporalMutationState               │
                               │  • TemporalQuad, ObfuscationAudit, RedlineSnippet           │
                               │                                                             │
                               │  frontend/src/components/vaults/kg/                         │
                               │  ├─ TemporalFilingScrubber.tsx (Time-travel scrubber)       │
                               │  ├─ BiTemporalGraphMutationCanvas.tsx (Neon visual shaders) │
                               │  ├─ FilingDualRedlineDrawer.tsx (Synchronized PDF reader)   │
                               │  └─ SemanticDriftRadar.tsx (11-Chapter SEBI radar chart)    │
                               └─────────────────────────────────────────────────────────────┘
```

---

## 2. Backend Data Models (`models/pre_ipo_temporal_schema.py`)

### 2.1 Bi-Temporal Quad & Mutation Schemas
```python
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any, Literal

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
    page_number: int
    x: float
    y: float
    width: float
    height: float
    verbatim_text: str

@dataclass
class TemporalGraphMutation:
    mutation_id: str
    subject_entity: str
    predicate: str
    change_type: MutationType
    sebi_chapter: SEBIChapter
    drhp_value: Optional[str]
    rhp_value: str
    drhp_bbox: Optional[TemporalBoundingBox]
    rhp_bbox: TemporalBoundingBox
    obfuscation_severity: float          # 0.0 (benign) to 1.0 (severe evasion)
    valuation_impact_inr: float          # Direct impact on equity valuation (in INR Cr)
    wacc_spread_shift_bps: float         # WACC adjustment (+bps)
    w3c_prov_citation: str
    summary_explanation: str
```

---

## 3. Difference Algorithm & Obfuscation Scoring

### 3.1 Graph Isomorphism & Mutation Detection
Let $G_0 = (V_0, E_0)$ be the DRHP graph and $G_1 = (V_1, E_1)$ be the RHP graph:
1. **Entity Sets ($V$):**
   - $\forall v \in V_1 \setminus V_0$: Emit `ENTITY_ADDED`.
   - $\forall v \in V_0 \setminus V_1$: Emit `SEVERED_RELATION`.
2. **Edge Properties ($E$):**
   - For matching edges $e = (u, v) \in E_0 \cap E_1$:
     - If $e_0.\text{value} \in \{`[○]`, `[●]`, `[–]`\}$ and $e_1.\text{value} \notin \{`[○]`, `[●]`, `[–]`\}$: Emit `BRACKET_RESOLVED`.
     - Else if $e_0.\text{value} \ne e_1.\text{value}$: Emit `MUTATED_PROPERTY`.
     - If legal qualifier weakened ("shall" $\to$ "may endeavor"): Emit `QUALIFIER_WATERED_DOWN`.

### 3.2 Cohen-Malloy Strategic Obfuscation Formula
$$\text{Score} = \min\left(1.0, \; \frac{|\text{Page}_{\text{RHP}} - \text{Page}_{\text{DRHP}}|}{100} \times w_{\text{chapter}} + w_{\text{textual\_drift}}\right)$$
Where:
- $w_{\text{chapter}} = 0.5$ if moved across chapters (e.g. Chapter I $\to$ Chapter X/XI).
- $w_{\text{textual\_drift}} = 1.0 - \text{CosineSimilarity}(\vec{T}_{\text{DRHP}}, \vec{T}_{\text{RHP}})$.

---

## 4. REST API Schema (`api/server.py`)

### 4.1 Endpoint Signatures
```python
@app.get("/api/pre-ipo/kg/temporal/versions")
def get_temporal_filing_versions(symbol: str = "HCCH") -> List[Dict[str, Any]]:
    """Returns available filing snapshots (DRHP, Addendum, RHP) with filing dates and hashes."""
    ...

@app.get("/api/pre-ipo/kg/temporal/diff")
def get_temporal_graph_diff(
    symbol: str = "HCCH",
    base_version: str = "DRHP",
    target_version: str = "RHP"
) -> Dict[str, Any]:
    """Returns complete mutation tree, 11-chapter drift summary, and valuation impact."""
    ...

@app.get("/api/pre-ipo/kg/temporal/verbatim-redline")
def get_verbatim_redline_snippet(
    mutation_id: str,
    symbol: str = "HCCH"
) -> Dict[str, Any]:
    """Returns side-by-side bounding boxes and verbatim excerpts for split-screen reader."""
    ...
```

---

## 5. Frontend Architecture & Discriminated Unions

### 5.1 TypeScript Type Definitions (`frontend/src/types/terminal.ts`)
```typescript
export type MutationType = 
  | 'BRACKET_RESOLVED' 
  | 'ENTITY_ADDED' 
  | 'SEVERED_RELATION' 
  | 'MUTATED_PROPERTY' 
  | 'QUALIFIER_WATERED_DOWN';

export type TemporalFilingVersion = 'DRHP' | 'ADDENDUM' | 'RHP';

export type TemporalMutationState = 
  | { status: 'IDLE' }
  | { status: 'LOADING'; baseVersion: TemporalFilingVersion; targetVersion: TemporalFilingVersion }
  | { status: 'LOADED'; diff: TemporalGraphDiffResult }
  | { status: 'ERROR'; error: string };

export interface TemporalBoundingBox {
  page_number: number;
  x: number;
  y: number;
  width: number;
  height: number;
  verbatim_text: string;
}

export interface TemporalGraphMutation {
  mutation_id: string;
  subject_entity: string;
  predicate: string;
  change_type: MutationType;
  sebi_chapter: string;
  drhp_value: string | null;
  rhp_value: string;
  drhp_bbox: TemporalBoundingBox | null;
  rhp_bbox: TemporalBoundingBox;
  obfuscation_severity: number;
  valuation_impact_inr: number;
  wacc_spread_shift_bps: number;
  w3c_prov_citation: string;
  summary_explanation: string;
}

export interface TemporalGraphDiffResult {
  symbol: string;
  base_version: string;
  target_version: string;
  base_date: string;
  target_date: string;
  total_mutations: number;
  mutations: TemporalGraphMutation[];
  chapter_drift_scores: Record<string, number>;
  net_valuation_impact_inr: number;
  net_wacc_spread_shift_bps: number;
  overall_obfuscation_index: number;
}
```

---

## 6. Visual Shaders & UI Styling Specifications

### 6.1 Mutation Canvas Visual Rules
- **Added Nodes (`ENTITY_ADDED`)**: Glowing emerald neon border (`box-shadow: 0 0 15px rgba(16, 185, 129, 0.6)`), background `#064E3B`, badge `+ NEW DISCLOSURE`.
- **Mutated Edges (`MUTATED_PROPERTY`)**: Amber gold pulsing dash stroke (`#F59E0B`), animated dash array `stroke-dashoffset`, badge `Δ REVISED`.
- **Severed Relations (`SEVERED_RELATION`)**: Ghosted red strikethrough line (`#EF4444`, opacity $0.4$), strikethrough badge `✕ TERMINATED`.
- **Bracket Resolved (`BRACKET_RESOLVED`)**: Cyan calm glow (`#06B6D4`), badge `✓ PRICED`.
- **High Obfuscation ($> 0.7$)**: Warning beacon with flashing ruby triangle `▲ EVASION RISK`.
