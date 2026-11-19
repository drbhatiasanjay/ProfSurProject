# Findings & Research Dossier: Temporal Knowledge Graphs in Pre-IPO Due Diligence

## 1. Academic Discoveries

### A. The "Lazy Prices" Anomaly (Cohen, Malloy & Nguyen, Journal of Finance, 2020)
- **Empirical Evidence:** In U.S. corporate SEC filings (1995-2014), firms that substantially rewrite their regular disclosures ("changers") underperform firms that keep language identical ("non-changers") by up to 188 bps per month (over 22% annualized long-short alpha).
- **Behavioral Cause:** Market participants fixate on quantitative numbers (earnings, revenue) and are inattentive ("lazy") to narrative modifications.
- **Section Predictive Power:** Changes in *Risk Factors*, *Executive Management*, and *Litigation Contingencies* have the highest predictive power for future operational distress, earnings drops, and bankruptcy.
- **Application to Indian Pre-IPO:** The same dynamic occurs between preliminary DRHPs and final RHPs. Issuers rewrite sections under regulatory pressure or to downplay emerging liabilities.

### B. Strategic IPO Disclosure (Hanley & Hoberg, RFS 2010; JFE 2012)
- **Informative Content vs. Standard Content:** Prospectuses contain standard boilerplate and firm-specific informative content. The magnitude of informative revisions between the initial draft and final prospectus reflects underwriters' pre-market due diligence.
- **Litigation Hedging:** Underwriters and promoters strategically modify disclosure clauses when pre-market inquiries uncover exposure, trading off pricing adjustments against legal protection.

## 2. Industry Tool Audit & Limitations

| Platform | Primary Feature | Critical Limitation |
| :--- | :--- | :--- |
| **Litera / Workshare** | Word/character-level redline | Page-shift pollution: inserting one paragraph shifts 500 subsequent pages, flagging every line as modified. |
| **Intelligize (LexisNexis)** | SEC Edgar S-1 vs S-1/A diff | US-specific regex; fails on SEBI ICDR Schedule VI chapters, promoter covenants, and Ind AS 37 disclosures. |
| **AlphaSense / Sentieo** | Snippet search & redlining | Isolated text snippets; cannot trace entity relationship rewiring or hidden related-party transaction rings. |
| **Bloomberg / FactSet** | Financial statement deltas | Disconnected from legal narrative; cannot propagate legal disclosure changes into valuation models. |

## 3. Critical Gaps & Our Temporal Knowledge Graph Solutions

1. **Gap 1: Lexical False Positives vs. Semantic Graph Mutations**
   - *Problem:* Bracketed placeholders (`[○]`) being resolved with final numbers are treated as text rewrites.
   - *Solution:* Quad classification separating `BRACKET_RESOLVED` from `MUTATED` or `ADDED` entities.

2. **Gap 2: Strategic Obfuscation Detection (Physical Coordinate Drift)**
   - *Problem:* Companies bury critical warnings by moving them from prominent Risk Factor sections to deep footnotes.
   - *Solution:* Cohen-Malloy Evasion Index tracking page coordinate displacement and cross-chapter shifts.

3. **Gap 3: SEBI ICDR Schedule VI Specificity**
   - *Problem:* International tools treat filings as generic prose.
   - *Solution:* Deterministic grouping by all 11 SEBI statutory chapters.

4. **Gap 4: Dynamic Valuation Ripple Propagation**
   - *Problem:* A redline is static; it does not tell the investor the financial cost of the change.
   - *Solution:* Factual mutations feed directly into the Reverse DCF, Downside VaR, and Anchor Lock-in engines.

## 4. Anti-AI Coding Patterns Mandate
- No synthetic blank mocks or truncated fixtures (Rule E.6).
- No loose truthiness (`val or default`) in numeric values (Rule E.3). Always `if val is None:`.
- No dead helper classes or uncalled utilities (Rule E.1).
- No silent `try/catch` blocks or swallowed errors (Architectural Invariant 4).
- Enforce strict TypeScript discriminated unions with compile-time `never` exhaustive checks.
