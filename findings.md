# Findings & Architectural Decisions

<!--
  MANUS Planning Framework: Working Memory on Disk
  Stores discovered requirements, mathematical formulas, and technical decisions.
-->

## Requirements
1. **Bank of In-Depth Cypher Queries for Red Herring Prospectus:**
   - 25+ pre-compiled, parameterized queries covering:
     - Category A: Capital Structure, OFS Cash Flows & Promoter Dilution.
     - Category B: Related Party Subsidies & EBITDA Margin Stuffing.
     - Category C: Litigation Contagion & Shield Penetration (Sec 138 Cheque Bounces).
     - Category D: Ind AS 116 Leases, Capitalized Debt & 12M Liquidity Walls.
     - Category E: Statutory Objects, GCP 25% Ceiling & SEBI Schedule VI Disclosures.
2. **Comprehensive 84-Attribute Mapping across 10 Statutory Sections:**
   - Section 1: Issue Details & Structure (10 attributes)
   - Section 2: Capital Structure & Shareholding (6 attributes)
   - Section 3: Promoters & Key Management Personnel (12 attributes)
   - Section 4: Financial Performance & Restatements (10 attributes)
   - Section 5: Borrowings & Ind AS 116 Lease Liabilities (11 attributes)
   - Section 6: Statutory Objects of Offer & GCP (9 attributes)
   - Section 7: Litigation, Tax & Material Inquiries (8 attributes)
   - Section 8: Related Party Disclosures & Commercial Subsidies (6 attributes)
   - Section 9: Risk Factors, Geographic & Customer Concentration (6 attributes)
   - Section 10: Valuation Metrics & Peer Benchmarking (6 attributes)
3. **Mathematical Formula Lineage Engine:**
   - Map every analytical card/score in the app back through explicit KaTeX/LaTeX formulas to its constituent 84 attributes.
   - Zero hardcoded numbers; full formula DAG traceability.
4. **In-App PDF Bounding Box Viewer Drawer:**
   - High-fidelity slide-over drawer in React 19.
   - Shows the authentic DRHP page with visual amber bounding box highlights `[x0, y0, x1, y1]`.
   - Displays verbatim banker quotes, page numbers, and PROV-O confidence scores.

---

## Technical Decisions & Architecture

| Decision | Rationale | Alternatives Considered |
| :--- | :--- | :--- |
| **Cypher Query Bank in DuckDB + NetworkX** | In-process, ultra-fast ($< 5\text{ ms}$), zero extra daemons, Windows Python 3.14 compatible | Neo4j server (too heavy, requires JVM), Kùzu (wheel unavailable on Win Py 3.14) |
| **PDF Extraction & BBox Geometry** | Authentic HCCH DRHP PDF vector text coordinates via PyMuPDF/pdfplumber normalized to $[0, 1]$ viewport scale | Tesseract OCR (slow, noisy), synthetic blank fixtures (violates Rule E.6) |
| **In-App Drawer vs External Tab** | Keeping analyst within the same terminal viewport preserves workflow momentum and trust | Opening PDF in new browser tab (loses page context and bounding box focus) |
| **Zustand / Component Modal State** | Synchronizes selected citation and bounding box coordinates seamlessly across Vaults | URL hash navigation (causes unnecessary Streamlit / React reload) |

---

## Formula-to-Attribute Mapping Specification

1. **5-Point Deal Integrity:**
   $$\text{Total Issue Size} = \text{Fresh Issue} + \text{Offer for Sale (OFS)}$$
   $$\text{Promoter Pre-Issue Shares} - \text{Promoter OFS Shares} = \text{Promoter Post-Issue Shares}$$
   *Constituent Attributes:* `total_issue_size_cr`, `fresh_issue_size_cr`, `ofs_issue_size_cr`, `pre_issue_shares_promoter`, `ofs_shares_promoter`.

2. **GCP Statutory Ceiling Gate:**
   $$\text{GCP Ratio} = \frac{\text{GCP Allocation (Cr)}}{\text{Gross Total Issue Size (Cr)}} \le 25.00\%$$
   *Constituent Attributes:* `gcp_allocation_cr`, `total_issue_size_cr`.

3. **Lease-Adjusted Net Debt & Debt/EBITDA:**
   $$\text{Effective Net Debt} = \text{Long-Term Debt} + \text{Short-Term Debt} + \text{Ind AS 116 Lease Liabilities} - \text{Cash}$$
   $$\text{Lease-Adjusted Leverage} = \frac{\text{Effective Net Debt}}{\text{Operating EBITDA}}$$
   *Constituent Attributes:* `long_term_borrowings_cr`, `short_term_borrowings_cr`, `ind_as_116_lease_liabilities_cr`, `cash_equivalents_cr`, `reported_ebitda_cr`.

4. **Altman Emerging Market Z"-Score:**
   $$Z'' = 6.56 X_1 + 3.26 X_2 + 6.72 X_3 + 1.05 X_4$$
   where $X_1 = \frac{\text{Current Assets} - \text{Current Liab}}{\text{Total Assets}}$, $X_2 = \frac{\text{Retained Earnings}}{\text{Total Assets}}$, $X_3 = \frac{\text{EBIT}}{\text{Total Assets}}$, $X_4 = \frac{\text{Tangible Net Worth}}{\text{Total Liabilities}}$.
   *Constituent Attributes:* `current_assets_cr`, `current_liabilities_cr`, `total_assets_cr`, `retained_earnings_cr`, `ebit_cr`, `tangible_net_worth_cr`, `total_liabilities_cr`.

5. **Beneish M-Score for Pre-IPO Earnings Quality:**
   $$M = -4.84 + 0.920 \cdot \text{DSRI} + 0.528 \cdot \text{GMI} + 0.404 \cdot \text{AQI} + 0.892 \cdot \text{SGI} + 0.115 \cdot \text{DEPI} - 0.172 \cdot \text{SGAI} + 4.037 \cdot \text{TATA} + 0.0327 \cdot \text{LVGI}$$
   *Constituent Attributes:* `revenue_fy_curr`, `revenue_fy_prev`, `gross_profit_curr`, `gross_profit_prev`, `cfo_curr`, `net_income_curr`, `total_assets_cr`, `depreciation_curr`, `sga_expense_curr`.

6. **Dickinson Cash Flow Life-Cycle Classification:**
   $$\text{LifeCycle Vector} = (\text{sign}(\text{CFO}), \text{sign}(\text{CFI}), \text{sign}(\text{CFF}))$$
   *Constituent Attributes:* `operating_cf_cr`, `investing_cf_cr`, `financing_cf_cr`.

7. **Subsidiary Litigation Overhang vs Net Worth:**
   $$\text{Litigation Overhang Ratio} = \frac{\text{Subsidiary Claims (Cr)}}{\text{Tangible Net Worth (Cr)}}$$
   *Constituent Attributes:* `total_subsidiary_claims_cr`, `tangible_net_worth_cr`.

8. **Normalized Operating EBITDA (Parent Subsidy Stripping):**
   $$\text{Normalized EBITDA} = \text{Reported EBITDA} - \text{Parent Trade Discounts/Incentives}$$
   $$\text{Normalized Margin} = \frac{\text{Normalized EBITDA}}{\text{Revenue from Operations}}$$
   *Constituent Attributes:* `reported_ebitda_cr`, `parent_trade_discounts_cr`, `revenue_fy_curr`.

9. **SARD Valuation Fair Multiple Haircut:**
   $$\text{Warranted Multiple} = \text{Peer Multiple} \cdot \left(1 - \frac{\text{Territory Disc} + \text{Channel Disc}}{100}\right)$$
   *Constituent Attributes:* `peer_ev_ebitda_multiple`, `top_territory_revenue_share_pct`, `distributor_cheque_bounce_cases_count`.
