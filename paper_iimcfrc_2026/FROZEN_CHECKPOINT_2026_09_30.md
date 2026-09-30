# FROZEN CHECKPOINT: IIMCFRC 2026 SUBMISSION
**Date**: September 30, 2026  
**Target Venue**: IIM Calcutta Finance Research Conference (IIMCFRC 2026, Dec 12-14, 2026, Joka, Kolkata)  
**Track**: FinTech, Machine Learning & Digital Finance / Corporate Finance & Governance  
**Git Branch**: `paper/iimcfrc-2026-lifestagedebtai`  

---

## 1. Frozen Primary Deliverables (Version 5 - Master Publication Build)

1. **Word Document (`.docx`)**:
   - Path: `paper_iimcfrc_2026/LifeStageDebtAI_IIMCFRC2026_Final_Submission_v5.docx`
   - Status: **Frozen & Validated**
   - Word Count: ~3,750 words (complete 8-section manuscript with 5 formatted tables and embedded Figure 1)
   - Typography: Times New Roman, 1.15 line spacing, 1-inch margins
   - Em-Dashes: Exactly 0 instances (replaced with colons, commas, or parentheses)
   - Native Footnotes: 4 unique OpenXML superscript footnotes (`¹`, `²`, `³`, `⁴`)

2. **Submission PDF (`.pdf`)**:
   - Path: `paper_iimcfrc_2026/LifeStageDebtAI_IIMCFRC2026_Final_Submission_v5.pdf`
   - File Size: 0.38 MB (well within the 20 MB portal threshold)
   - Status: **Compiled via Word COM & Validated**

3. **Master Build Script**:
   - Path: `paper_iimcfrc_2026/build_v5_master.py`
   - Purpose: Fully reproducible programmatic build script generating V5 from source data and OpenXML definitions.

---

## 2. Document & Econometric Verifications

- **Table 1**: Dickinson (2011) Eight Cash-Flow Pattern Taxonomy (9 rows x 5 cols).
- **Table 2**: Data Vintages Register (Reference `2004-2020`, Extended `2001-2024`, Roll-Forward `2001-2025`).
- **Table 3**: Econometric Core Replication against Kumar (2025, Table 5.10 Model 2):
  - Growth: `0.038** (0.016)`
  - Maturity: `0.054*** (0.015)`
  - Shakeout: `0.021 (0.019)`
  - Decline: `0.047** (0.022)`
  - Tangibility: `0.184*** (0.024)`
  - Profitability: `-0.312*** (0.038)`
  - Size: `0.042*** (0.008)`
  - MB: `-0.015** (0.006)`
  - NDTS: `-0.108* (0.057)`
  - Observations: `4,218`
- **Table 4**: TreeSHAP Determinant Rankings (Profitability, Tangibility, Size, Liquidity, Tobin's Q).
- **Table 5**: Positioning Matrix (12-row comparison between conventional workflow and LifeStageDebtAI platform).
- **Section 5.1 Corporate Archetypes**:
  - **Tata Steel Ltd.**: Asset tangibility 0.38 - 0.42, debt Rs. 63,223 Cr, cross-validated with Chakraborty (2010).
  - **Infosys Ltd.**: Zero-debt, cash reserves Rs. 10,473 Cr (28.5% of assets), cross-validated with Ghose & Kabra (2016) and Bates et al. (2009).
  - **IndiGo (InterGlobe Aviation)**: Lease commitments Rs. 67,088 Cr, lease-adjusted leverage 72.1%, cross-validated with Srivastava & Mukherjee (2021).

---

## 3. Footnote Provenance Ledger

1. **Footnote 1 (Author Affiliation)**: Dr. Sanjay Bhatia (EOLABS.IN) & Dr. Surendra Kumar (Univ. of Delhi, PhD 2025).
2. **Footnote 2 (Section 2.1)**: Ind AS 7 / AS 3 cash flow standards and boundary resolution.
3. **Footnote 3 (Section 4.1)**: Petersen (2009) firm-level standard error clustering.
4. **Footnote 4 (Section 5.1)**: Ind AS 116 / IFRS 16 lease liability capitalization.
