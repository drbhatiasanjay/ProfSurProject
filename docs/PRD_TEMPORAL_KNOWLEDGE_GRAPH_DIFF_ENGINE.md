# Product Requirements Document (PRD): Bi-Temporal Knowledge Graph & Multi-Filing Comparison Diff Engine

**Document Version:** 1.0.0  
**Status:** Approved for Implementation  
**Author:** Institutional Engineering & Antigravity Research Group  
**Framework:** Manus Persistent Planning (`task_plan.md`, `findings.md`, `progress.md`)  
**Target Milestone:** Milestone 19 (`feature/pre-ipo-fibo-knowledge-graph`)  

---

## 1. Executive Summary & Vision

### 1.1 Objective
Build an institutional-grade Bi-Temporal Knowledge Graph (TKG) and filing comparison engine that tracks corporate structural evolution, regulatory observations, strategic obfuscation, and valuation impact between preliminary filings (DRHP) and final offerings (RHP) under the SEBI ICDR Regulations.

### 1.2 The Core Problem
During an IPO process in India, months elapse between the initial Draft Red Herring Prospectus (DRHP) and the final Red Herring Prospectus (RHP). During this period, the issuer responds to confidential SEBI observation letters, market inquiries, and audit challenges. Issuers frequently alter critical disclosures:
- Adding newly surfaced litigation claims or tax demands.
- Altering the Objects of the Issue (e.g. cutting debt repayment from ₹1,000 Cr to ₹200 Cr to fund unverified acquisitions).
- Changing promoter share pledges and dilution structures (e.g. shifting from fresh issue growth capital to a 100% Offer for Sale cashout).
- Relocating severe risk warnings from front-matter chapters to obscure back-matter footnotes.

Traditional legal redlining tools (Litera, Word diff, basic PDF comparators) fail because they operate on string characters. A minor formatting or page shift pollutes the diff with thousands of false positives, and character diffs have zero connection to financial models or corporate governance graphs.

### 1.3 The Solution
A **Bi-Temporal Knowledge Graph Diff Engine** that parses prospectus iterations into temporal quads:
$$(s, p, o, [t_{\text{valid\_start}}, t_{\text{valid\_end}}])$$
The engine categorizes mutations, detects physical coordinate displacement (strategic obfuscation), and propagates factual alterations directly into the valuation, WACC, and downside VaR models.

---

## 2. Academic & Industry Grounding

### 2.1 The "Lazy Prices" Anomaly (Cohen, Malloy & Nguyen, *Journal of Finance*, 2020)
Empirical evidence proves that firms making significant textual and structural changes between annual/preliminary filings underperform non-changers by up to 188 basis points per month (22% annualized alpha). The market is inattentive to disclosure rewrites, creating persistent mispricings that can be systematically exploited by institutional investors.

### 2.2 Strategic IPO Disclosures (Hanley & Hoberg, *RFS* 2010; *JFE* 2012)
Issuers strategically trade off IPO pricing against disclosure revisions. When severe pre-market risks are flagged during due diligence, underwriters modify disclosure language to hedge against legal liability. Tracking these revisions reveals previously hidden operational distress.

---

## 3. Target User Personas & Use Cases

| Persona | Primary Goal | Critical Pain Point | How This Engine Solves It |
| :--- | :--- | :--- | :--- |
| **Novice / Retail Investor** | Understand if the company became riskier before applying for IPO shares. | Cannot read 600-page dense legal prospectuses or understand technical tax changes. | Time-Travel scrubber with high-level plain-English alert badges (e.g., "Parent Company agreed to shield ₹431 Cr tax demand; zero balance sheet bleed"). |
| **Institutional Fund Manager / QIB** | Quantify changes in Fair Value, WACC, and downside VaR caused by disclosure revisions. | Spreadsheet models are disconnected from filing amendments; manual review takes days. | Instant recalculation of DCF Fair Value and 99% Downside VaR driven by graph mutation edges. |
| **SEBI Compliance & Legal Counsel** | Audit compliance against SEBI ICDR Schedule VI and detect altered promoter covenants. | Uncovering subtle wording dilutions across draft amendments is prone to human oversight. | Side-by-side synchronized verbatim bounding-box drawer with SHA-256 cryptographic audit trail. |

---

## 4. Functional Requirements (FR)

### FR-1: Bi-Temporal Knowledge Graph Ingestion & Quad Schema
- The engine must represent all factual assertions as bi-temporal quads:
  $$(s, p, o, [t_{\text{valid\_start}}, t_{\text{valid\_end}}])$$
- Where:
  - $s$: Subject Entity IRI (e.g., `fibo-fnd:HCCB_Holdings_Ltd`).
  - $p$: Predicate / Relationship (e.g., `fibo-fnd:hasLitigationDemand`).
  - $o$: Object Entity or Literal Value (e.g., `CESTAT_Excise_Demand_INR_431Cr`).
  - $t_{\text{valid\_start}}, t_{\text{valid\_end}}$: Filing milestone timestamps (e.g., `DRHP_2023_12_01` to `RHP_2024_10_15`).

### FR-2: Quad Mutation Classification
The engine must classify every detected difference into one of four deterministic types:
1. `BRACKET_RESOLVED`: Placeholder markers (`[○]`, `[●]`, `[–]`) resolved with final verified values (e.g., Issue Price Band, Bid Opening Date).
2. `ENTITY_ADDED`: A new entity (promoter, subsidiary, key supplier, litigation counterparty) absent in DRHP.
3. `SEVERED_RELATION`: A contract, loan, or supply agreement terminated between filing versions.
4. `MUTATED_PROPERTY`: A changed financial or operational scalar (e.g. OFS percentage jumping from 20% to 100%, capacity utilization drop).
5. `QUALIFIER_WATERED_DOWN`: Legal watering-down of promoter or indemnity obligations (e.g. changing mandatory "shall indemnify" to discretionary "may endeavor to reimburse").

### FR-3: Cohen-Malloy Strategic Obfuscation & Coordinate Drift Index
- Compute the physical displacement between filings:
  $$\Delta \text{Displacement} = (\text{Page}_{\text{RHP}} - \text{Page}_{\text{DRHP}}) \times \text{ChapterWeight}$$
- If a high-severity risk factor or litigation disclosure is moved from Chapter I (*Risk Factors*) to Chapter XII (*Outstanding Litigation Footnotes*), the engine must assign an Obfuscation Severity Score ($0.0$ to $1.0$) and trigger an `EVASION_ALERT`.

### FR-4: Financial Valuation Ripple Propagation
- Any change in financial or statutory facts must immediately recalculate:
  - **WACC Adjustment**: Additional risk premiums for unshielded legal demands.
  - **Reverse DCF Fair Value Delta**: $\Delta P_{\text{fair}} = P_{\text{RHP}} - P_{\text{DRHP}}$.
  - **95% & 99% Downside VaR**: Widened distribution curves under altered leverage.
  - **Anchor Lock-in Buffer**: Float expansion impact at T+30 and T+90 days.

### FR-5: 11-Chapter SEBI ICDR Schedule VI Partitioning
Every mutation must be mapped to one of the 11 statutory SEBI chapters:
- Chapter I: General Risk Factors
- Chapter II: General Information & Capital Structure
- Chapter III: Objects of the Issue & Proceeds Deployment
- Chapter IV: Basis for Issue Price & Accounting Ratios
- Chapter V: Industry Overview & Market Positioning
- Chapter VI: Business Overview & Operational Metrics
- Chapter VII: Management & Board Governance
- Chapter VIII: Promoter Group & Related Party Transactions
- Chapter IX: Financial Statements & Ind AS Accounting
- Chapter X: Legal & Other Statutory Disclosures (Litigation)
- Chapter XI: Other Regulatory & Statutory Disclosures

### FR-6: Synchronized Dual Redline Bounding Box Viewer
- Clicking any mutation node must open a split-screen document viewer:
  - Left Pane: Original DRHP page excerpt with exact pixel bounding box (`x, y, w, h`).
  - Right Pane: Amended RHP page excerpt with exact pixel bounding box.
  - Verbatim text difference highlighted in red strikethrough (deletions) and green highlight (additions).

---

## 5. Non-Functional Requirements & Engineering Standards

### 5.1 Performance & Latency
- Bi-temporal graph isomorphism and mutation diff computation must execute in $< 150\text{ ms}$ for a graph of 500 nodes and 1,200 edges.
- Frontend time-travel scrubber must render at 60 FPS without layout shift or dropped animation frames.

### 5.2 Strict Zero-Truthiness Financial Rule (Rule E.3)
- In financial econometrics, $0.0$, $0\%$, and $0$ are genuine, valid numbers distinct from absence (`None`).
- Under no circumstances shall `val or default` be written. All checks must strictly use `if val is None:`.

### 5.3 Fail-Closed Architecture (Rule E.2)
- If a requested filing version does not exist, the engine must immediately raise `FilingNotFoundError` and fail closed. Permissive default fallbacks are strictly prohibited.

### 5.4 Elimination of AI Coding Patterns
- No mock blank fixtures or truncated synthetic files (Rule E.6).
- No dead helper functions or unused classes (Rule E.1).
- No silent `try/catch` blocks swallowing errors.
- TypeScript code must enforce discriminated unions with compile-time exhaustive checks (`const _exhaustive: never = state;`).

---

## 6. Verification & Evidence Gates

1. **Adversarial Unit Test Suite**: Minimum 8 comprehensive unit tests covering:
   - Quad mutation classification accuracy.
   - Strategic obfuscation index calculation.
   - Rule E.3 zero-truthiness preservation.
   - Mathematical valuation round-trip inversion ($\le 0.05\%$).
2. **Playwright Automated Browser Audit**:
   - Live navigation to standalone terminal (`localhost:5174`) and unified terminal (`localhost:5173`).
   - Dragging the time-travel scrubber.
   - Verifying neon glowing canvas mutations.
   - Opening the split-screen dual redline drawer and confirming physical screenshot existence on disk.
3. **Independent Subagent Auditor Review**:
   - Codebase review checking AST production wiring, zero dead code, and absence of AI tropes.
