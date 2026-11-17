# Institutional Pre-IPO Terminal: Expanded 84-Attribute Schema, Econometric Suite & Screen Architecture Blueprint

**Document Reference:** `docs/EXPANDED_84_ATTRIBUTE_PRE_IPO_BLUEPRINT.md`  
**Governing Standard:** SEBI ICDR 2018 (Schedule VI), Dickinson (2011) Life-Cycle, Huber (1964) Robust M-Estimation ($c=1.345$), Beneish (1999) M-Score, Altman (2002) Emerging Market $Z''$-Score  
**Authoritative Corpus Reference:** `Hindustan_Coca_Cola_Holdings_DRHP.pdf` (513-Page Benchmark Filing)  
**Status:** Canonical Architectural Blueprint & Implementation Specification  

---

## Executive Summary & System Evolution

Expanding the extraction taxonomy from the 42 baseline accounting metrics to an **84-Attribute Institutional Pre-IPO Schema** transforms the platform from a static compliance ledger into a full-stack forensic, econometric, and valuation workbench.

While the baseline 42 attributes capture single-year statutory accounting facts (e.g., FY24 revenue, debt, net worth, and basic offer sizing), institutional buy-side analysis demands:
1. **Multi-period trajectory and stub seasonality** to detect pre-IPO revenue stuffing or margin compression.
2. **Contractual and lease-adjusted credit analysis** to uncover Ind AS 116 liabilities distorting apparent leverage.
3. **Forensic accrual and window-dressing detection** (Beneish M-Score, Sloan Accruals).
4. **Supply overhang and arbitrage analytics** to track pre-IPO lock-in cliffs ($T+30$, $T+90$, $T+180$) and Section 56(2)(x) tax exposure.
5. **Operational moats and contingent liabilities** to stress-test litigation reserves and regulatory friction.

This blueprint establishes:
- The authoritative 84-attribute extraction inventory partitioned into **10 canonical SEBI ICDR sections**.
- The 7-engine institutional econometric, forensic, and machine learning analytical suite with automated narrative synthesis.
- The 4-layer synchronized screen architecture and UI vault mapping.
- The master implementation prompt enforcing all `AGENTS.md` engineering invariants.

---

## 1. Expanded 84-Attribute Pre-IPO Extraction Inventory

The taxonomy is organized into **Tier 1 (Core Statutory & Financial Baseline, Attributes 1–42)** and **Tier 2 (Deep Intelligence, Attributes 43–84)**, mapped across 10 statutory chapters of SEBI ICDR Schedule VI.

```
┌──────────────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│                               84-ATTRIBUTE PRE-IPO INSTITUTIONAL TAXONOMY                                        │
├────────────────────────────────────────┬─────────────────────────────────────────────────────────────────────────┤
│ TIER 1: Core Statutory Baseline (1–42)  │ Single-period financials, statutory offer terms, baseline cap table     │
│ TIER 2: Deep Intelligence (43–84)       │ Multi-period stubs, contractual moats, contingent risks, lock-in cliffs   │
└────────────────────────────────────────┴─────────────────────────────────────────────────────────────────────────┘
```

### Complete 10-Section Inventory & Vault Mapping Matrix

| Statutory Section | Total Attrs | Tier 1: Core Baseline Attributes (1–42) | Tier 2: Expanded Deep Intelligence Attributes (43–84) | Primary UI Vault Destination | Downstream Analytical Engine |
| :--- | :---: | :--- | :--- | :--- | :--- |
| **1. Offer Structure** | 10 | `issue_type`, `gross_fresh_issue`, `gross_ofs`, `total_issue_size`, `face_value`, `price_band_min`, `price_band_max`, `post_issue_dilution_pct` | `implied_ev_at_cap`, `qib_anchor_allocation_pct` | `CompactCockpitHUD`, `StatutoryOfferHero` | Reg 7 Dilution Engine & Valuation Router |
| **2. Objects & Use of Proceeds** | 6 | `net_company_inflow`, `capex_allocation`, `debt_repayment_allocation`, `gcp_allocation`, `gcp_pct_of_fresh` | `debt_repayment_to_brlm_affiliates_pct` (SEBI ICDR conflict check) | `ProvenanceLedgerVault`, `RedFlagScannerVault` | Objects 5-Point Accounting Gate |
| **3. P&L & Stub Trajectory** | 12 | `rev_ops_fy25`, `other_income_fy25`, `total_income_fy25`, `ebitda_fy25`, `ebitda_margin_fy25`, `pat_fy25`, `pat_margin_fy25` | `rev_ops_fy23`, `rev_ops_fy24`, `rev_ops_stub` (Q1 FY27), `ebitda_stub`, `pat_stub` (3-Yr CAGR & stub seasonality delta) | `ProvenanceLedgerVault`, `ValuationEngineVault` | Beneish M-Score, STL Seasonal Decomposer |
| **4. Balance Sheet & Capital** | 10 | `tangible_net_worth_fy25`, `total_assets_fy25`, `total_liabilities_fy25`, `cash_and_liquid_inv_fy25`, `capex_fy25` | `tangible_net_worth_stub` (₹8,200.20 Cr), `gross_block_ppe`, `goodwill_intangibles`, `roce_pct`, `roe_pct` | `ProvenanceLedgerVault`, `PeerBenchmarkVault` | Huber Robust Multiples & Capital Quality |
| **5. Cash Flow & Working Capital** | 11 | `cfo_fy25`, `cfi_fy25`, `cff_fy25`, `fcf_fy25`, `dso_days`, `dio_days`, `dpo_days`, `ccc_days` | `cfo_stub`, `cfi_stub`, `cff_stub` (Dickinson lifecycle sign vector & CFO/EBITDA cash conversion) | `ProvenanceLedgerVault`, `EconometricLabVault` | Dickinson (2011) Cash Flow Classifier |
| **6. Indebtedness & Leases** | 9 | `secured_term_loans`, `working_capital_debt`, `total_borrowings_ex_lease`, `ind_as_116_lease_liabilities`, `total_debt_inc_lease`, `net_debt`, `net_debt_to_ebitda` | `weighted_avg_interest_rate_pct` (7.95%), `debt_maturing_within_12m` (refinancing wall & lease distortion) | `ProvenanceLedgerVault`, `CovenantStressVault` | Altman $Z''$-Score & Lease Unwinding |
| **7. Cap Table & Lock-In Cliffs** | 8 | `promoter_pre_ipo_pct`, `promoter_post_ipo_pct`, `non_selling_copromoter_pct` (Jubilant 40.0%), `promoter_pledge_pct` | `promoter_waca_price`, `pre_ipo_investor_waca_price`, `anchor_lockin_shares_t30_t90`, `non_promoter_lockin_shares_t180` | `StakeholderLensVault`, `UnlistedArbitrageVault` | Lock-In Supply Impact & Rule 11UA Tax |
| **8. Governance & Related Party** | 6 | `rpt_pct_of_rev` (3.40%), `independent_directors_pct` (50.00%), `top_5_customer_conc_pct` (8.20%) | `parent_royalty_or_concentrate_formula`, `cfo_turnover_last_24m`, `auditor_emphasis_of_matter_count` | `RedFlagScannerVault`, `ICBoardDeckVault` | Forensic Governance Radar (FLAG-01 to 06) |
| **9. Contingent Liabilities & Litigation** | 6 | *(New Section)* `disputed_tax_demands_inr_cr`, `civil_regulatory_claims_inr_cr`, `total_contingent_liabilities_inr_cr` | `contingent_to_net_worth_pct`, `criminal_proceedings_promoter_count`, `environmental_notices_count` | `RedFlagScannerVault`, `ICBoardDeckVault` | Contingent Risk & Net Worth Haircut Engine |
| **10. Unit Economics & Capacity** | 6 | *(New Section)* `installed_capacity_units`, `capacity_utilization_pct`, `distribution_reach_count` (2.5M+ outlets) | `gross_margin_pct`, `raw_material_to_rev_pct`, `revenue_per_outlet_or_unit` | `EconometricLabVault`, `PeerBenchmarkVault` | Operational Moat & Capacity Bottleneck Model |

---

### Field-Level Statutory Taxonomy Specification

#### Section 1: Offer Structure (10 Attributes)
- `attr_01_issue_type`: Category of offering (`100% OFS`, `100% FRESH`, `FRESH_AND_OFS`). Statutory citation: SEBI ICDR Reg 6(1).
- `attr_02_gross_fresh_issue`: Gross proceeds from primary issue in ₹ Cr. Unit: Currency (`INR_CR`).
- `attr_03_gross_ofs`: Gross proceeds from existing shareholder secondary sale in ₹ Cr. Unit: Currency (`INR_CR`).
- `attr_04_total_issue_size`: Combined issue value (`gross_fresh_issue + gross_ofs`) in ₹ Cr. Unit: Currency (`INR_CR`).
- `attr_05_face_value`: Equity share nominal face value in ₹ per share. Unit: Currency (`INR_PER_SHARE`).
- `attr_06_price_band_min`: Lower price floor in ₹ per share (or `None` for unpriced DRHP). Unit: Currency (`INR_PER_SHARE`).
- `attr_07_price_band_max`: Upper price cap in ₹ per share (or `None` for unpriced DRHP). Unit: Currency (`INR_PER_SHARE`).
- `attr_08_post_issue_dilution_pct`: Percentage dilution of pre-issue capital. Unit: Percentage (`PCT`).
- `attr_09_implied_ev_at_cap`: Implied Enterprise Value calculated at issue price cap in ₹ Cr. Unit: Currency (`INR_CR`).
- `attr_10_qib_anchor_allocation_pct`: Anchor book portion allocated to Qualified Institutional Buyers (up to 60% of QIB). Unit: Percentage (`PCT`).

#### Section 2: Objects & Use of Proceeds (6 Attributes)
- `attr_11_net_company_inflow`: Actual net cash retained by issuer after deducting issue expenses and OFS payout. Unit: Currency (`INR_CR`).
- `attr_12_capex_allocation`: Earmarked capex proceeds in ₹ Cr. Unit: Currency (`INR_CR`).
- `attr_13_debt_repayment_allocation`: Proceeds directed towards debt reduction in ₹ Cr. Unit: Currency (`INR_CR`).
- `attr_14_gcp_allocation`: General Corporate Purposes allocation in ₹ Cr. Unit: Currency (`INR_CR`).
- `attr_15_gcp_pct_of_fresh`: GCP as percentage of Fresh Issue (statutory limit $\le 25\%$ under SEBI ICDR Reg 7(2)). Unit: Percentage (`PCT`).
- `attr_16_debt_repayment_to_brlm_affiliates_pct`: Proceeds intended to repay lenders affiliated with Book Running Lead Managers. Statutory conflict check: SEBI ICDR Reg 23(4). Unit: Percentage (`PCT`).

#### Section 3: P&L & Stub Trajectory (12 Attributes)
- `attr_17_rev_ops_fy23`: Revenue from operations for FY23 in ₹ Cr. Unit: Currency (`INR_CR`).
- `attr_18_rev_ops_fy24`: Revenue from operations for FY24 in ₹ Cr. Unit: Currency (`INR_CR`).
- `attr_19_rev_ops_fy25`: Restated revenue from operations for FY25 in ₹ Cr. Unit: Currency (`INR_CR`).
- `attr_20_rev_ops_stub`: Unaudited / reviewed revenue from operations for the latest interim stub period in ₹ Cr. Unit: Currency (`INR_CR`).
- `attr_21_other_income_fy25`: Non-operating income for FY25 in ₹ Cr. Unit: Currency (`INR_CR`).
- `attr_22_total_income_fy25`: Total revenue (`rev_ops_fy25 + other_income_fy25`) in ₹ Cr. Unit: Currency (`INR_CR`).
- `attr_23_ebitda_fy25`: Operating earnings before interest, tax, depreciation, and amortisation in ₹ Cr. Unit: Currency (`INR_CR`).
- `attr_24_ebitda_margin_fy25`: FY25 EBITDA margin (`ebitda_fy25 / rev_ops_fy25`). Unit: Percentage (`PCT`).
- `attr_25_ebitda_stub`: Stub period EBITDA in ₹ Cr. Unit: Currency (`INR_CR`).
- `attr_26_pat_fy25`: Restated Profit After Tax for FY25 in ₹ Cr. Unit: Currency (`INR_CR`).
- `attr_27_pat_margin_fy25`: FY25 PAT margin (`pat_fy25 / total_income_fy25`). Unit: Percentage (`PCT`).
- `attr_28_pat_stub`: Stub period Profit After Tax in ₹ Cr. Unit: Currency (`INR_CR`).

#### Section 4: Balance Sheet & Capital (10 Attributes)
- `attr_29_tangible_net_worth_fy25`: Total net worth excluding intangible assets and deferred tax assets in ₹ Cr. Unit: Currency (`INR_CR`).
- `attr_30_tangible_net_worth_stub`: Tangible net worth as of latest stub balance sheet in ₹ Cr. Unit: Currency (`INR_CR`).
- `attr_31_total_assets_fy25`: Total restated balance sheet assets in ₹ Cr. Unit: Currency (`INR_CR`).
- `attr_32_total_liabilities_fy25`: Total restated balance sheet liabilities in ₹ Cr. Unit: Currency (`INR_CR`).
- `attr_33_cash_and_liquid_inv_fy25`: Cash, bank balances, and current liquid investments in ₹ Cr. Unit: Currency (`INR_CR`).
- `attr_34_capex_fy25`: Capital expenditure incurred during FY25 in ₹ Cr. Unit: Currency (`INR_CR`).
- `attr_35_gross_block_ppe`: Gross carrying value of Property, Plant & Equipment in ₹ Cr. Unit: Currency (`INR_CR`).
- `attr_36_goodwill_intangibles`: Goodwill on consolidation and other intangible assets in ₹ Cr. Unit: Currency (`INR_CR`).
- `attr_37_roce_pct`: Return on Capital Employed (`EBIT / (Total Assets - Current Liabilities)`). Unit: Percentage (`PCT`).
- `attr_38_roe_pct`: Return on Net Worth (`PAT / Average Net Worth`). Unit: Percentage (`PCT`).

#### Section 5: Cash Flow & Working Capital (11 Attributes)
- `attr_39_cfo_fy25`: Cash flow from operating activities for FY25 in ₹ Cr. Unit: Currency (`INR_CR`).
- `attr_40_cfi_fy25`: Cash flow from investing activities for FY25 in ₹ Cr. Unit: Currency (`INR_CR`).
- `attr_41_cff_fy25`: Cash flow from financing activities for FY25 in ₹ Cr. Unit: Currency (`INR_CR`).
- `attr_42_fcf_fy25`: Free cash flow (`cfo_fy25 - capex_fy25`) in ₹ Cr. Unit: Currency (`INR_CR`).
- `attr_43_cfo_stub`: Operating cash flow for the stub period in ₹ Cr. Unit: Currency (`INR_CR`).
- `attr_44_cfi_stub`: Investing cash flow for the stub period in ₹ Cr. Unit: Currency (`INR_CR`).
- `attr_45_cff_stub`: Financing cash flow for the stub period in ₹ Cr. Unit: Currency (`INR_CR`).
- `attr_46_dso_days`: Days Sales Outstanding (`(Trade Receivables / Rev Ops) * 365`). Unit: Number (`DAYS`).
- `attr_47_dio_days`: Days Inventory Outstanding (`(Inventory / COGS) * 365`). Unit: Number (`DAYS`).
- `attr_48_dpo_days`: Days Payable Outstanding (`(Trade Payables / Purchases) * 365`). Unit: Number (`DAYS`).
- `attr_49_ccc_days`: Cash Conversion Cycle (`DSO + DIO - DPO`). Unit: Number (`DAYS`).

#### Section 6: Indebtedness & Leases (9 Attributes)
- `attr_50_secured_term_loans`: Long-term secured borrowing balances in ₹ Cr. Unit: Currency (`INR_CR`).
- `attr_51_working_capital_debt`: Short-term fund-based working capital facilities in ₹ Cr. Unit: Currency (`INR_CR`).
- `attr_52_total_borrowings_ex_lease`: Total debt excluding Ind AS 116 lease liabilities in ₹ Cr. Unit: Currency (`INR_CR`).
- `attr_53_ind_as_116_lease_liabilities`: Present value of operating lease obligations under Ind AS 116 in ₹ Cr. Unit: Currency (`INR_CR`).
- `attr_54_total_debt_inc_lease`: Comprehensive debt (`total_borrowings_ex_lease + ind_as_116_lease_liabilities`) in ₹ Cr. Unit: Currency (`INR_CR`).
- `attr_55_net_debt`: Net debt (`total_debt_inc_lease - cash_and_liquid_inv_fy25`) in ₹ Cr. Unit: Currency (`INR_CR`).
- `attr_56_net_debt_to_ebitda`: Leverage ratio (`net_debt / ebitda_fy25`). Unit: Ratio (`MULTIPLE`).
- `attr_57_weighted_avg_interest_rate_pct`: Weighted average effective cost of borrowing. Unit: Percentage (`PCT`).
- `attr_58_debt_maturing_within_12m`: Principal repayments falling due within the next 12 months in ₹ Cr. Unit: Currency (`INR_CR`).

#### Section 7: Cap Table & Lock-In Cliffs (8 Attributes)
- `attr_59_promoter_pre_ipo_pct`: Aggregate promoter and promoter group pre-issue equity stake. Unit: Percentage (`PCT`).
- `attr_60_promoter_post_ipo_pct`: Expected aggregate promoter post-issue equity stake. Unit: Percentage (`PCT`).
- `attr_61_non_selling_copromoter_pct`: Equity stake held by non-selling co-promoters (e.g., Jubilant 40.0% in HCCH). Unit: Percentage (`PCT`).
- `attr_62_promoter_pledge_pct`: Percentage of promoter equity encumbered or pledged. Unit: Percentage (`PCT`).
- `attr_63_promoter_waca_price`: Weighted Average Cost of Acquisition for promoter shares in ₹. Unit: Currency (`INR_PER_SHARE`).
- `attr_64_pre_ipo_investor_waca_price`: Weighted Average Cost of Acquisition for pre-IPO round investors in ₹. Unit: Currency (`INR_PER_SHARE`).
- `attr_65_anchor_lockin_shares_t30_t90`: Number of anchor investor shares under statutory 30-day (50%) and 90-day (50%) lock-in. Unit: Shares (`COUNT`).
- `attr_66_non_promoter_lockin_shares_t180`: Number of pre-IPO non-promoter shares subject to 6-month statutory lock-in (SEBI ICDR Reg 17). Unit: Shares (`COUNT`).

#### Section 8: Governance & Related Party (6 Attributes)
- `attr_67_rpt_pct_of_rev`: Total Related Party Transactions as percentage of operating revenue. Unit: Percentage (`PCT`).
- `attr_68_independent_directors_pct`: Proportion of Independent Directors on Board of Directors. Unit: Percentage (`PCT`).
- `attr_69_top_5_customer_conc_pct`: Revenue contribution of the top 5 customers. Unit: Percentage (`PCT`).
- `attr_70_parent_royalty_or_concentrate_formula`: Contractual royalty or raw material concentrate pricing formula with global parent entity. Unit: Categorical (`TEXT`).
- `attr_71_cfo_turnover_last_24m`: Number of Chief Financial Officer resignations or replacements in prior 24 months. Unit: Count (`COUNT`).
- `attr_72_auditor_emphasis_of_matter_count`: Number of Emphasis of Matter or Key Audit Matters flagged in restated audit reports. Unit: Count (`COUNT`).

#### Section 9: Contingent Liabilities & Litigation (6 Attributes — New Section)
- `attr_73_disputed_tax_demands_inr_cr`: Total pending direct and indirect tax demands under appeal in ₹ Cr. Unit: Currency (`INR_CR`).
- `attr_74_civil_regulatory_claims_inr_cr`: Pending civil, labor, consumer, and regulatory proceedings against issuer in ₹ Cr. Unit: Currency (`INR_CR`).
- `attr_75_total_contingent_liabilities_inr_cr`: Comprehensive contingent liability pool disclosed in Restated Financial Notes in ₹ Cr. Unit: Currency (`INR_CR`).
- `attr_76_contingent_to_net_worth_pct`: Contingent liabilities as percentage of Tangible Net Worth (`total_contingent / net_worth`). Unit: Percentage (`PCT`).
- `attr_77_criminal_proceedings_promoter_count`: Number of active criminal cases against company, promoters, or directors. Unit: Count (`COUNT`).
- `attr_78_environmental_notices_count`: Show-cause notices, closures, or penalties from State / Central Pollution Control Boards. Unit: Count (`COUNT`).

#### Section 10: Unit Economics & Capacity (6 Attributes — New Section)
- `attr_79_installed_capacity_units`: Total licensed/installed manufacturing capacity across plants (e.g., million cases/year). Unit: Volume (`VOLUME_UNITS`).
- `attr_80_capacity_utilization_pct`: Average operational capacity utilization rate. Unit: Percentage (`PCT`).
- `attr_81_distribution_reach_count`: Total retail touchpoints, distribution outlets, or active client accounts. Unit: Count (`COUNT`).
- `attr_82_gross_margin_pct`: Gross profit margin (`(Rev Ops - Cost of Materials Consumed) / Rev Ops`). Unit: Percentage (`PCT`).
- `attr_83_raw_material_to_rev_pct`: Key raw material costs as percentage of operating revenue. Unit: Percentage (`PCT`).
- `attr_84_revenue_per_outlet_or_unit`: Unit realization metric (`rev_ops / distribution_reach` or `rev_ops / volume_shipped`). Unit: Currency (`INR_PER_UNIT`).

---

## 2. Institutional Econometric, Forensic & ML Analytical Suite

The 84-attribute structured ledger directly feeds 7 institutional quantitative engines. Each engine evaluates specific micro-foundations and emits both mathematical metrics and an **Automated Narrative & Statistical Interpretation**.

```
84-Attribute Verified Ledger
         │
         ├──> [1. Beneish M-Score & Sloan Accruals] ─────────> Window-Dressing & Manipulation Verdict
         ├──> [2. Dickinson Life-Cycle Vector] ──────────────> Introduction / Growth / Mature Classification
         ├──> [3. Huber Robust Peer Regression] ────────────> Outlier-Resistant Valuation Premium (σ)
         ├──> [4. STL Decomposition & Chow Break Test] ──────> Stub Seasonality & Pre-IPO Margin Spike Detection
         ├──> [5. Monte Carlo Reverse DCF (10,000 Draws)] ──> Implied Growth Hurdle ($P_{10}, P_{50}, P_{90}$)
         ├──> [6. Event-Study Lock-In Cliff Impact] ─────────> Supply Overhang ($T+30, T+90, T+180$) & Rule 11UA Tax
         └──> [7. Altman Z''-Score & Lease Unwinding] ───────> Ind AS 116 Adjusted Credit Distance & Headroom
```

### Econometric Specification Matrix

| # | Analytical Engine | Academic / Regulatory Framework | Mathematical / Econometric Specification | Open-Source Python Stack | Statistical Thresholds & Automated Verdict |
| :-: | :--- | :--- | :--- | :--- | :--- |
| **1** | **Earnings Manipulation & Accrual Quality** | Beneish (1999) 8-Variable Model & Sloan (1996) Balance Sheet Accruals | $$M = -4.84 + 0.92\,\text{DSRI} + 0.528\,\text{GMI} + 0.404\,\text{AQI} + 0.892\,\text{SGI} + 0.115\,\text{DEPI} - 0.172\,\text{SGAI} + 4.679\,\text{TATA} - 0.327\,\text{LVGI}$$ Total Accruals: $$\text{TATA} = \frac{(\Delta\text{CA} - \Delta\text{Cash}) - (\Delta\text{CL} - \Delta\text{STD} - \Delta\text{TP}) - \text{Dep}}{\text{Total Assets}}$$ | `numpy`, `scipy.stats`, `pandas` | **Safe:** $M \le -2.22$<br>**Grey Zone:** $-2.22 < M < -1.78$<br>**Manipulator Alert:** $M > -1.78$ or $\text{TATA} > 10\%$. Decomposes driver (e.g. DSRI receivable bloat). |
| **2** | **Cash Flow Life-Cycle & Capital Allocation** | Dickinson (2011) Triple Sign Vector Classification | Sign vector: $$S = \big(\text{sgn}(\text{CFO}),\,\text{sgn}(\text{CFI}),\,\text{sgn}(\text{CFF})\big)$$ evaluated across FY23, FY24, FY25, and interim stub. | `pandas`, `numpy` | **Introduction:** $(-, -, +)$<br>**Growth:** $(+, -, +)$<br>**Mature Cash Cow:** $(+, -, -)$<br>**Shake-Out:** $(-, -, -)$ or $(+, +, +)$<br>**Decline:** $(-, +, +)$<br>Flags structural transitions. |
| **3** | **Robust Peer Multiple & Implied EV Regression** | Huber (1964) Robust M-Estimator & Koenker-Bassett Quantile Regression | $$\frac{\text{EV}}{\text{EBITDA}}_i = \alpha + \beta_1\,\text{ROCE}_i + \beta_2\,\text{RevCAGR}_i + \beta_3\,\text{Margin}_i - \beta_4\left(\frac{\text{NetDebt}}{\text{EBITDA}}\right)_i + \epsilon_i$$ Robust loss: $\rho(r) = \begin{cases} \frac{1}{2}r^2 & \|r\| \le c \\ c\|r\| - \frac{1}{2}c^2 & \|r\| > c \end{cases}$ with $c=1.345$. | `statsmodels.robust.robust_linear_model.RLM`, `statsmodels.regression.quantile_regression.QuantReg`, `scikit-learn.linear_model.HuberRegressor` | Downweights outlier peers (e.g. loss-making fast-growers with EV/EBITDA $> 150\times$). Emits fair value multiple and tells IC if IPO cap is $+1.5\sigma$ over priced. |
| **4** | **Stub Seasonality & Margin Structural Break** | STL (LOESS Seasonal-Trend Decomposition) & Chow / Bai-Perron Structural Break Test | Tests null hypothesis of equal coefficients before vs. during stub: $$F = \frac{(RSS_C - (RSS_1 + RSS_2)) / k}{(RSS_1 + RSS_2) / (N_1 + N_2 - 2k)}$$ Stub Run-Rate: $\text{Rev}_{\text{annualized}} = \text{Rev}_{\text{stub}} \times \frac{1}{\omega_{\text{season}}}$ | `statsmodels.tsa.seasonal.STL`, `scipy.stats`, `numpy` | **Rejection ($p < 0.05$):** Rejects naive $4\times$ run-rate. Quantifies seasonal Q1 beverage surge vs true annualized run-rate; flags pre-IPO margin stuffing. |
| **5** | **Monte Carlo Reverse DCF & WACC Stress** | Damodaran Cost of Capital + 2D Adversarial Stress Surface (10,000 draws) | Solves for implied $g_{\text{revenue}}$ such that: $$\text{Enterprise Value} = \sum_{t=1}^{10} \frac{\text{FCFF}_t(g)}{(1 + \text{WACC})^t} + \frac{\text{FCFF}_{10}(1 + g_{\text{term}})}{(\text{WACC} - g_{\text{term}})(1 + \text{WACC})^{10}}$$ with $\text{WACC} \sim \mathcal{N}(\mu_W, \sigma_W^2)$, $\text{Margin} \sim \text{Beta}(\alpha, \beta)$. | `numpy.random`, `scipy.optimize.brentq` | Outputs probability density ($P_{10}, P_{50}, P_{90}$) of intrinsic EV vs. Issue Price Cap. If $P(\text{Intrinsic} \ge \text{Cap}) < 35\%$, triggers IC Valuation Warning. |
| **6** | **Lock-In Supply Overhang & Unlisted Arbitrage** | Event-Study Liquidity Impact + Income Tax Sec 56(2)(x) / Rule 11UA | Supply shock duration: $$\text{Days}_{\text{overhang}} = \frac{\text{Shares}_{\text{unlocked}}}{\text{ADT}_{30}}$$ Tax spread: $$\text{Tax Liability} = \max(0, \text{FMV}_{\text{Rule 11UA}} - P_{\text{entry}}) \times \tau_{\text{applicable}}$$ | `numpy`, `pandas` | Projects $T+30, T+90, T+180$ float expansion. Flags adverse tax consequences when unlisted acquisition was below NAV/DCF fair market value. |
| **7** | **Bankruptcy & Lease-Adjusted Credit Distance** | Altman (2002) Emerging Market $Z''$-Score & Ind AS 116 Lease Unwinding | $$Z'' = 6.56\,X_1 + 3.26\,X_2 + 6.72\,X_3 + 1.05\,X_4$$ where $X_1 = \text{WC}/\text{TA}$, $X_2 = \text{RE}/\text{TA}$, $X_3 = \text{EBIT}/\text{TA}$, $X_4 = \text{BV Equity}/\text{Total Liab}$.<br>Lease unwinding: $$\text{Debt}^* = \text{Debt} + \text{LeaseLiab};\quad \text{EBITDAR} = \text{EBITDA} + \text{RentExp}$$ | `numpy`, `pandas` | **Safe Zone:** $Z'' > 2.60$<br>**Grey Zone:** $1.10 \le Z'' \le 2.60$<br>**Distress Zone:** $Z'' < 1.10$<br>Uncovers leverage understated by Ind AS 116 operating leases. |

---

### Automated Narrative & Statistical Interpretation Engine

For every econometric engine, the system outputs an automated **3-part narrative synthesis box**:

```
┌────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│ [ ENGINE CARD: 1. EARNINGS MANIPULATION & ACCRUAL QUALITY (BENEISH M-SCORE) ]                         │
├────────────────────────────────────────────────────────────────────────────────────────────────────────┤
│ 1. STATISTICAL FINDING:                                                                                │
│    Beneish M-Score = -2.48 (Safe Zone < -1.78). TATA (Total Accruals to Total Assets) = +0.024 (2.4%,  │
│    well below 10.0% threshold). DSRI = 1.04, indicating stable receivables growth matching sales.     │
│                                                                                                        │
│ 2. ECONOMIC MECHANISM:                                                                                 │
│    The issuer shows strong cash earnings quality with CFO/EBITDA of 91.2%. Operating cash flow         │
│    (₹1,438.5 Cr) fully supports reported PAT (₹1,021.4 Cr). No aggressive revenue capitalization or   │
│    depreciation slowdown detected.                                                                     │
│                                                                                                        │
│ 3. IC ACTIONABLE TAKEAWAY:                                                                             │
│    EARNINGS QUALITY: PASS. Zero evidence of pre-IPO aggressive earnings window-dressing. No accounting │
│    discount required on trailing financial statements.                                                │
└────────────────────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 3. Screen Architecture: 4 Synchronized Visual Layers

To present 84 attributes and 7 econometric models without interface fragmentation or vertical doom-scrolling, the user experience is divided into 4 synchronized layers:

```
┌────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│ LAYER 1: PINNED TELEMETRY STRIP (CompactCockpitHUD.tsx & StatutoryOfferHero.tsx)                      │
│ ├── Ticker Banner | Deal Pricing State: [ RHP_PRICED ] | Deal Integrity: [ PASS (5/5) ]                │
│ ├── 84-Attribute Completeness: [ 🟢 78 FOUND ] [ ⚪ 4 PENDING ] [ 🟠 2 RECONFIRM ]                      │
│ └── Top KPI Bento: Issue Size (₹ Cr) | Implied EV/EBITDA (x) | Net Debt/EBITDA | Dickinson (+,-,-)    │
├────────────────────────────────────────────────────────────────────────────────────────────────────────┤
│ LOWER WORKSPACE (Swapped dynamically via Left Sidebar)                                                │
│                                                                                                        │
│ ┌────────────────────────────────────────────────────────────────────────────────────────────────────┐ │
│ │ LAYER 2 (VAULT 4): FACT & PROVENANCE EVIDENCE LEDGER (ProvenanceLedgerVault.tsx)                   │ │
│ │ ├── 10 Statutory Accordions (10/10 Offer, 6/6 Objects, 12/12 P&L, 10/10 BS, 11/11 CF, ...)         │ │
│ │ ├── Multi-Filter Bar: [ Instant Search... ] [ All 10 Sections ▾ ] [ All (84) | Verified | Flags ] │ │
│ │ ├── High-Density Table: Label | Attribute ID | Metric (font-mono) | Unit | Conf | Citation Pill    │ │
│ │ └── Inline PDF Coordinate Inspector Drawer (Verbatim Quote, Bounding Box [x0,y0,x1,y1], SHA-256)   │ │
│ └────────────────────────────────────────────────────────────────────────────────────────────────────┘ │
│                                                                                                        │
│ ┌────────────────────────────────────────────────────────────────────────────────────────────────────┐ │
│ │ LAYER 3 (VAULT 5): ECONOMETRIC & FORENSIC LAB (EconometricLabVault.tsx)                            │ │
│ │ ├── Top Tab Navigation: [ Beneish M-Score | Dickinson | Huber Comps | STL Break | Monte Carlo DCF ]│ │
│ │ ├── Interactive Visual Canvas: Waterfall / Phase Diagram / Robust Scatter / Monte Carlo Fan Chart   │ │
│ │ └── Automated 3-Part Interpretation Panel: Statistical Finding | Economic Mechanism | IC Takeaway │ │
│ └────────────────────────────────────────────────────────────────────────────────────────────────────┘ │
│                                                                                                        │
│ ┌────────────────────────────────────────────────────────────────────────────────────────────────────┐ │
│ │ LAYER 4 (VAULTS 6–10): DECISION SYNTHESIS WORKBENCH                                                │ │
│ │ ├── Vault 6: 14 Institutional Diligence Questions (Discoms, Royalties, RPT, Capacity)             │ │
│ │ ├── Vault 7: 6-Persona Stakeholder Lens (CFO, Senior Lender, Buy-Side Equity, Retail, Board)        │ │
│ │ ├── Vault 8: 6-Rule Red-Flag Governance Radar (FLAG-01 to FLAG-06)                                 │ │
│ │ ├── Vault 9: Unlisted Arbitrage & Rule 11UA Tax Simulator                                          │ │
│ │ └── Vault 10: IC Stance & One-Click 16:9 PowerPoint Board Deck Export                               │ │
│ └────────────────────────────────────────────────────────────────────────────────────────────────────┘ │
└────────────────────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 4. Master Antigravity Implementation Prompt

The prompt below is structured for direct invocation in a clean session, adhering strictly to the `AGENTS.md` engineering invariants.

```markdown
### MASTER IMPLEMENTATION INSTRUCTION: 84-ATTRIBUTE PRE-IPO TERMINAL EXPANSION

You are executing under the strict engineering directives of `c:\Users\hemas\Downloads\ProfSurProject\AGENTS.md`.

#### OPERATIONAL CONTEXT & INVARIANTS:
1. **Workspace Boundary:** Strictly confined to `ProfSurProject`.
2. **Zero Python Truthiness (Rule E.3):** Never write `val or default`. Treat `0.0`, `0%`, and `0` as distinct valid disclosures. Always use explicit checks (`if val is None:`).
3. **Fail-Closed Capability Architecture (Rule E.2):** All valuation, export, and econometric endpoints must enforce `assert_capability_allowed`. Unreviewed or missing models fail closed (`ExportBlockedError`).
4. **TypeScript Discriminated Unions:** Enforce strict discriminated unions across all data models (`DealPricingState`, `ProvenanceField<T>`, `EconometricStatus`). Zero unchecked `as Type` casts. Zero multi-boolean flags.
5. **Database Transaction Atomicity (Rule E.5):** No `conn.executescript()` inside active transaction blocks. All schema migrations must be rollback-verified.

#### IMPLEMENTATION STAGES:

- **Stage 1: Python Canonical 84-Attribute Registry (`models/pre_ipo_schema.py`)**
  - Expand the schema registry from 42 to 84 attributes across the 10 canonical SEBI ICDR sections.
  - Add statutory references (SEBI ICDR Schedule VI clauses) and strict data types for attributes 43–84.
  - Implement fallback and extraction mocks for both benchmark filings (`Hindustan_Coca_Cola_Holdings_DRHP.pdf` and `NTPC_Green_Energy_DRHP.pdf`).

- **Stage 2: Institutional Econometric Suite (`models/pre_ipo_econometrics.py`)**
  - Implement the 7 quantitative models using `numpy`, `scipy.stats`, and `statsmodels`:
    1. Beneish M-Score & Sloan Accruals.
    2. Dickinson Cash Flow Life-Cycle classifier.
    3. Huber M-Estimator ($c=1.345$) & Quantile Regression.
    4. STL Decomposition & Chow Structural Break test.
    5. Monte Carlo Reverse DCF with 10,000 parameter draws.
    6. Lock-In Supply Overhang & Sec 56(2)(x) Rule 11UA tax model.
    7. Altman $Z''$-Score & Ind AS 116 Lease Unwinding.
  - Implement the Automated Narrative & Statistical Interpretation Engine emitting structured 3-part summaries (Finding, Mechanism, IC Takeaway).

- **Stage 3: FastAPI Bridge Endpoints (`api/server.py`)**
  - Update `@app.get("/api/pre-ipo/schema")` to return the complete 84-attribute registry.
  - Update `@app.get("/api/pre-ipo/market-status")` to deliver 84-attribute provenance ledgers and summaries (`totalCount = 84`).
  - Expose `@app.get("/api/pre-ipo/econometrics/{symbol}")` returning results and interpretations for all 7 models.

- **Stage 4: Frontend Type Contracts & Service Layer (`frontend/src/`)**
  - Update `types/terminal.ts` to expand `CanonicalSection` to all 10 sections and add typed contracts for the 7 econometric models.
  - Update `services/canonicalProvenance.ts` to contain the full 84-attribute frontend fallback dictionary.
  - Ensure total count telemetry strictly validates: `foundCount + notFoundCount + reconfirmCount === 84`.

- **Stage 5: Vault 4 & Vault 5 UI Components (`frontend/src/components/vaults/`)**
  - `ProvenanceLedgerVault.tsx`: Render all 10 collapsible accordions, live search, section filter dropdown, and coordinate inspection drawer for all 84 attributes.
  - `EconometricLabVault.tsx`: Implement interactive analytical cards for each of the 7 engines with visual plots and the 3-part narrative interpretation panel.

- **Stage 6: Verification & Test Suite (`tests/test_pre_ipo_84_attributes.py`)**
  - Author adversarial unit tests:
    - Verify 84-attribute schema registry structure and section counts.
    - Test zero-value preservation ($0.0$ Fresh Issue, $0.0\%$ pledge).
    - Assert that mathematical solvers invert within documented tolerances ($\le 0.05\%$).
    - Run TypeScript type checks (`tsc --noEmit`).
```

---

## 5. Architectural Quality Checklist

- [x] **SEBI ICDR Schedule VI Alignment:** All 84 attributes mapped to explicit statutory disclosure clauses.
- [x] **Peer-Reviewed Econometric Foundations:** Models grounded in Dickinson (2011), Beneish (1999), Huber (1964), and Altman (2002).
- [x] **Zero Truthiness Design:** Distinguishes $0.0$, $0\%$, and $0$ from `None`.
- [x] **Multi-Period Stub Awareness:** Solves the seasonal run-rate annualization trap in quarterly DRHP/RHP stubs.
- [x] **Lease-Adjusted Solvency:** Integrates Ind AS 116 lease liability unwinding into standard credit metrics.
- [x] **Provenance Traceability:** Every attribute links to document citation, page number, bounding box, and cryptographic hash.
- [x] **Token-Optimized UI Hierarchy:** Partitioned into Cockpit telemetry and specialized analytical vaults.
