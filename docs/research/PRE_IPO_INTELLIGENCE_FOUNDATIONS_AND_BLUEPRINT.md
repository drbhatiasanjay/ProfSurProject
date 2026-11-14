# Pre-IPO Intelligence: Comprehensive Foundations, AI/ML Landscape, Institutional Frameworks & Architectural Blueprint

**Document Class:** Institutional Research, Brainstorming & Architecture Blueprint  
**Target System:** `ProfSurProject` — LifeCycle Leverage Intelligence Platform  
**Date:** November 2026  
**Status:** Living Master Context & Reference Document  

---

## Executive Summary: The Pre-IPO Intelligence Frontier

There is **no single, universally standard standalone financial model** (in the sense of a pretrained, turnkey foundation model like BloombergGPT or FinGPT) purpose-built solely for pre-IPO intelligence. 

Because private and late-stage pre-IPO firms suffer from severe information asymmetry and lack continuous, order-book public price discovery, a turnkey model cannot resolve the multi-faceted problem of pricing, governance, and structural risk. Instead, a deep literature scan across empirical finance, econometrics, corporate valuation, and financial machine learning reveals that pre-IPO intelligence is governed by **four distinct methodological paradigms**:

1. **Theoretical Asset-Pricing & Corporate Valuation Frameworks** (Asymmetric information signalling, winner's curse, downside risk, survival-adjusted DCF, and forensic earnings quality).
2. **Econometric Specifications in Empirical IPO Literature** (Cross-sectional robust regressions, BHAR event studies, Heckman two-stage selection, Cox proportional hazards, and panel fixed-effects).
3. **Supervised & Unsupervised Financial Machine Learning Architectures** (Gradient Boosted Decision Trees, Random Forests, Gaussian Mixture Models, and Temporal Fusion Transformers).
4. **Prospectus NLP & Document Intelligence Models** (Domain-adapted FinBERT sentiment, linguistic uncertainty scoring, layout-aware document parsing, and semantic peer embedding retrieval).

This document establishes the permanent theoretical, empirical, regulatory, and software architecture foundations for pre-IPO evaluation in `ProfSurProject`. It aggregates core research, integrates the complete practitioner blueprint for Indian primary markets (**SEBI ICDR 2018**, **CRISIL IPO Grading**, **JRFM 2023**, **SJMSOM IIT Bombay ML research**), details the **end-to-end 6-stage engineering pipeline** for parsing statutory prospectuses, formalizes the **NSE India live API connection architecture**, establishes the **longitudinal Cohort Lifecycle & Post-IPO Trajectory framework**, and defines the evolutionary roadmap for our Pre-IPO intelligence engine.

---

## Section 1: The Four Methodological Paradigms of Pre-IPO Intelligence

Institutional research desks, sovereign wealth allocators, and quantitative funds layer four complementary paradigms to separate fundamental business quality from issuance mispricing:

```mermaid
flowchart TD
    subgraph PARADIGM_1["1. Theoretical & Valuation Frameworks"]
        P1A["Asymmetric Information & Signalling\n(Rock 1986; Leland & Pyle 1977; Welch 1989)"]
        P1B["Survival-Adjusted DCF & Downside Beta\n(Damodaran; Estrada)"]
        P1C["Forensic Accounting & Accruals\n(Beneish M-Score; Sloan Ratio)"]
        P1D["Warranted Multiples\n(Bhojraj & Lee 2002)"]
    end

    subgraph PARADIGM_2["2. Econometric Estimators"]
        P2A["Huber / Quantile Robust Comps"]
        P2B["Buy-and-Hold Abnormal Returns (BHAR)\n& CAR Event Studies"]
        P2C["Heckman Two-Stage Selection (Mills λ)\n& Propensity Score Matching"]
        P2D["Cox Proportional Hazards & Fama-MacBeth"]
    end

    subgraph PARADIGM_3["3. Machine Learning Architectures"]
        P3A["Tabular GBDTs: LightGBM / CatBoost / XGBoost\n(IIT Bombay Non-Linear Thresholds)"]
        P3B["Random Forests (Feature Importance Ranking)"]
        P3C["Gaussian Mixture Models (Unsupervised Archetypes)"]
        P3D["Temporal Fusion Transformers (TFT / LSTM Sequences)"]
    end

    subgraph PARADIGM_4["4. Prospectus NLP & Document AI"]
        P4A["Domain Encoders (FinBERT, SEC-BERT, DeBERTa-v3)"]
        P4B["Linguistic Uncertainty & Litigation Scanners"]
        P4C["Layout Parsers (Docling, TATR) + Schema LLMs"]
        P4D["Semantic Peer Discovery (BGE / FinE5 Embeddings)"]
    end

    PARADIGM_1 --> SYNTHESIS["PROFSUR PRE-IPO DECISION CORE"]
    PARADIGM_2 --> SYNTHESIS
    PARADIGM_3 --> SYNTHESIS
    PARADIGM_4 --> SYNTHESIS
```

### 1.1 Theoretical & Corporate Valuation Frameworks
Academic and industry literature establishes that standard secondary-market models fail on pre-IPO issuers due to information asymmetry, illiquidity, and non-normal return distributions:

- **Asymmetric Information & Signalling Models (Rock, 1986; Leland & Pyle, 1977; Welch, 1989):**
  - *Winner's Curse (Rock):* Uninformed investors receive disproportionate allocations in overpriced IPOs, forcing issuers to leave a structural **IPO Discount** (10%–20%) on the table to retain market participation.
  - *Signalling & Equity Retention:* Promoter equity retention (low Offer-for-Sale ratio) and Tier-1 lead manager / anchor investor certification act as costly signals of private intrinsic quality.
- **Adjusted Discounted Cash Flow & Downside Risk Models (Damodaran; Estrada):**
  - Standard CAPM systematically misprices emerging-market and pre-profit technology IPOs (documented in empirical case studies of Zomato, Paytm, and Nykaa) because historical beta is unavailable and return volatility is heavily skewed.
  - *Correction:* Practitioners use **Bottom-Up Levered Sector Betas** adjusted for post-Fresh-Issue cash/debt changes, **Estrada's Downside Beta** (semi-variance relative to market downside), and **Two-Stage Survival-Adjusted DCF** (explicitly modeling failure probability $p_{\text{fail}}$ before terminal value):
    $$\text{Valuation} = (1 - p_{\text{fail}}) \times \sum_{t=1}^T \frac{\text{FCFF}_t}{(1 + WACC)^t} + p_{\text{fail}} \times \text{Liquidation Value}$$
- **Forensic Earnings Quality Frameworks:**
  - *Beneish M-Score & Sloan Accrual Ratio:* Deployed in pre-IPO accounting literature to detect "window dressing"—where issuers inflate pre-filing stub-period EBITDA by cutting discretionary R&D/marketing or stretching trade receivables:
    $$\text{Sloan Accrual Ratio} = \frac{\text{Net Income} - \text{CFO}}{\text{Total Assets}}$$
- **Comparable Company & Statistical Comps Frameworks (Bhojraj & Lee, 2002; Damodaran):**
  - Replaces subjective peer selection with **Warranted Multiples** derived from fundamental value drivers (growth, ROE/ROCE, leverage, and reinvestment rate).

---

### 1.2 Econometric Specifications in Empirical IPO Literature

Econometric studies across US (EDGAR) and Indian (NSE/BSE) primary markets rely on specific estimators tailored to cross-sectional IPO cohorts and post-listing event windows:

| Econometric Method | Mathematical Formulation / Estimator | Primary Pre-IPO Research Application |
|---|---|---|
| **Cross-Sectional OLS & Robust Regression** (Huber / Quantile) | $\text{Multiple}_i = \alpha + \sum \beta_k X_{ik} + \gamma \text{Sector}_i + \epsilon_i$ | Estimates "Fundamental Fair Multiples" ($P/E$, $EV/\text{EBITDA}$, $EV/\text{Sales}$) while neutralizing extreme peer outliers. |
| **Buy-and-Hold Abnormal Returns (BHAR) & CAR** | $\text{BHAR}_{i,T} = \prod_{t=1}^{T}(1 + R_{it}) - \prod_{t=1}^{T}(1 + R_{mt})$ | Measures post-IPO wealth creation/destruction across $T \in \{30\text{D}, 90\text{D}, 180\text{D}, 1\text{Y}, 3\text{Y}\}$ and lock-in expiry windows. |
| **Heckman Two-Stage Selection & PSM** | $\text{Pr}(\text{IPO}=1) = \Phi(Z'\gamma)$<br>$\text{Outcome} = X'\beta + \rho \sigma \lambda(Z'\gamma) + \epsilon$ | Controls for self-selection bias (firms choose to go public during hot market windows or peak margin cycles via Inverse Mills Ratio $\lambda$). |
| **Cox Proportional Hazards & Survival Analysis** | $h(t \mid X) = h_0(t)\exp(\beta' X)$ | Models time-to-IPO exit for late-stage private companies or post-listing distress probability. |
| **Fama-MacBeth & Panel Fixed-Effects** | $R_{it} - R_{ft} = \alpha_i + \beta_i \mathbf{F}_t + \tau_t + \mu_s + \epsilon_{it}$ | Controls for IPO vintage year ($\tau_t$) and sector fixed effects ($\mu_s$), separating macro waves from firm fundamentals. |

#### Key Empirical Findings from Indian Primary Market Studies:
- **Short-Run Underpricing Drivers:** QIB/NII oversubscription multiples, industry $P/E$ momentum, and listing delay positively drive Day-1 returns, while issue size and market volatility reduce them.
- **Long-Run Underperformance Drivers:** Indian empirical studies confirm that short-run pops mean-revert over 6 to 24 months; **Return on Net Worth (RONW)**, **Return on Assets (ROA)**, **Cash Flow Conversion ($CFO/\text{EBITDA}$)**, and **Debt-to-Assets** dominate long-term abnormal return predictability.

---

### 1.3 Machine Learning & Deep Learning Architectures

Recent academic literature (2020–2026) demonstrates that non-linear ensemble and neural architectures outperform linear regressions in capturing complex interactions between financial ratios, offer structure, and market sentiment:

#### A. Tabular Supervised Learning (Pricing & Post-Listing Returns)
- **Gradient Boosted Decision Trees (LightGBM, XGBoost, CatBoost):**
  - *Empirical Consensus:* Consistently rank #1 on tabular IPO datasets (including IIT Bombay SJMSOM studies on Indian IPO underperformance and international underpricing benchmarks).
  - *Why they work:* Handle non-linear thresholds (e.g., when $OFS > 70\%$ combined with $P/E$ premium $> 40\%$), missing stub-period features, and skewed financial ratios without strict Gaussian assumptions.
- **Random Forests & Extra Trees:**
  - Effective for feature-importance ranking (e.g., identifying that pre-IPO profit margin stability and issue price band rank highest in variance explanation) and variance reduction on smaller country-specific IPO cohorts (500–1,500 listings).
- **Artificial Neural Networks (MLPs) & Error-Correction Neural Networks:**
  - Applied in studies on KOSDAQ and Indian listings to blend multiple valuation anchors (DCF + Comps + Asset Value) into a non-linear fair-price estimator.

#### B. Unsupervised & Hybrid Clustering Architectures
- **Gaussian Mixture Models (GMM) & Hierarchical Agglomerative Clustering:**
  - Used to cluster pre-IPO issuers and historical sector peers into behavioral trajectories (e.g., separating capital-efficient compounders from PE-exit supply overhangs) without relying on rigid SIC/NIC industry codes.
- **Genetic Algorithms (GA) + Rough Set Theory:**
  - Used in portfolio allocation research (e.g., Kim et al.) to optimize feature subset selection and rule induction for IPO subscription filtering.

#### C. Time-Series & Deep Sequence Models
- **Temporal Fusion Transformers (TFT) & LSTMs:**
  - Recommended in recent 2026 empirical reviews for modeling post-listing trajectory sequences ($T_0$ through $T_{+8\text{ quarters}}$) where static pre-IPO covariates interact with dynamic post-listing quarterly earnings and macro volatility.

---

### 1.4 Prospectus NLP & Document Intelligence Models

A major frontier in recent literature (from Loughran-McDonald lexical frameworks through modern LLM agents) is extracting predictive signals from unstructured S-1 and DRHP text:

- **Domain-Adapted Encoders (FinBERT, SEC-BERT, DeBERTa-v3):**
  - *Linguistic Uncertainty & Litigation Density:* Quantifies modal/uncertain word density in Risk Factors and MD&A. Empirical papers prove that higher textual uncertainty directly increases first-day underpricing (investors demand a wider discount for ambiguity) and post-listing return volatility.
- **Layout-Aware Document Parsers + Schema-Constrained LLMs:**
  - Architectures like **Docling**, **Nougat**, and **Table Transformer (TATR)** paired with QLoRA fine-tuned LLMs (Llama-3 / Qwen-2.5) extract multi-year restated Ind AS/GAAP schedules, cap table conversion waterfalls, and statutory KPIs with deterministic Pydantic validation.
- **Semantic Embedding Peer Retrieval (BGE-large / FinE5):**
  - Computes cosine similarity between the issuer's "Our Business" narrative and listed firms' annual report business descriptions to uncover true economic peers omitted from the prospectus.

---

### 1.5 Industry Practitioner Frameworks (Institutional & VC/PE)

In commercial practice, top-tier institutions combine these quantitative layers into standardized decision engines:

- **CRISIL / ICRA 4-Pillar Grading Architecture:** Strictly decouples **Fundamental Quality** (Business Prospects, Financial Position, Management, Governance) from **Issue Pricing**, preventing market hype from masking weak balance sheets.
- **CB Insights Mosaic & CapitalVX (Ross et al., 2021):** Combines syndicate network centrality (investor tiering), momentum signals (headcount, web/app traction, patent velocity), and financial health into private-to-IPO exit probability scores.
- **Crossover Hedge Fund "$T_0\text{-to-}T_{+4\text{Q}}$" Diligence Playbook:** Benchmarks restated DRHP stub margins against post-listing consensus estimates, stress-testing break-even prices across Day-30/90 Anchor and Month-6 non-promoter lock-in expiries.

---

## Section 2: Traditional Quantitative & Econometric Pre-IPO Models

In investment banking, equity research, and private equity, pre-IPO modeling relies on deterministic financial models adjusted for the unique characteristics of private-to-public transitions:

| Model Architecture | Pre-IPO Focus & Critical Structural Adjustments |
|---|---|
| **Consensus & Peer Comps (Trading Multiples)** | Adjusts for the statutory **"IPO Discount"** (typically 10%–20% below trading multiples of public peers to ensure an oversubscribed book-building process and first-day pop). Neutralizes differences in capital structure using EV/EBITDA. |
| **Capital Structure & Dilution Waterfall** | Models conversion mechanics: Preferred Stock to Common Stock conversions, SAFE/convertible note settlements, employee option pool expansion prior to pricing, promoter share lock-in, and Greenshoe (over-allotment) exercise scenarios. |
| **Discounted Cash Flow (DCF)** | Deploys scenario-weighted cash flows and **step-down WACC curves**: higher initial discount rates prior to listing (reflecting private firm illiquidity and execution risk) that step down post-IPO as liquidity risk declines and access to capital markets expands. |
| **Working Capital & Liquidity Runway** | Models monthly cash burn rates to verify post-issue working capital sufficiency (statutorily required by listing regulations, such as 18–24 months of verified operating runway). |
| **Dickinson (2011) Life-Cycle Stage Mapping** | Evaluates Cash Flow from Operations (CFO), Investing (CFI), and Financing (CFF) sign vectors to classify the issuer into Introduction, Growth, Mature, Shake-Out, or Decline stages, determining sustainable leverage capacity. |

---

## Section 3: Commercial Pre-IPO Intelligence Platforms Landscape

Several commercial platforms combine quantitative modeling and machine learning specifically for late-stage and pre-IPO assets:

* **InSync Analytics:** Delivers pre-built, forward-looking pre-IPO financial models, segment KPIs, and peer comps directly integrated into analyst workflows for imminent listings.
* **PitchBook & CB Insights:** Deploy proprietary scoring algorithms (e.g., CB Insights' *Mosaic* algorithm) that predict exit likelihood, IPO timing, and implied valuation based on syndicate quality, financial health, and industry momentum.
* **Forge Global / Caplight / CartaX:** Aggregate secondary market transaction pricing, synthetic forward curves, and liquidity discounts for late-stage unicorns preparing for statutory filings.
* **Indian Primary Market Data Portals (NSE, BSE, Chittorgarh, IPO Watch, Ace Equity, CMIE Prowess):** Provide live bidding subscription rates across QIB/NII/Retail buckets, Grey Market Premiums, anchor allocation sheets, and historical Ind AS restatement databases.

---

## Section 4: Indian Pre-IPO Analysis Framework (Six-Pillar Methodology)

*(Exhaustive integration from `Pre-IPO-Analysis-Framework-and-App-Blueprint-India.pdf`)*

A pre-IPO analysis framework in India evaluates an unlisted company's business fundamentals, corporate governance, valuation, and regulatory readiness prior to listing on the National Stock Exchange (NSE) or BSE. Whether an investor is acquiring unlisted shares in the off-market or evaluating an upcoming public issue via its Draft Red Herring Prospectus (DRHP), institutional due diligence relies on six core pillars:

```mermaid
flowchart LR
    P1["1. Regulatory & Listing Readiness\n(SEBI ICDR, Mainboard Routes,\nFresh vs. OFS Split)"] --> EVAL["PRE-IPO DUE DILIGENCE ENGINE"]
    P2["2. Business Model & Moat\n(Revenue Quality, Client Concentration,\nUnit Economics)"] --> EVAL
    P3["3. Restated Ind AS Financials\n(3-Yr CAGR, Window Dressing,\nCFO/EBITDA Conversion)"] --> EVAL
    P4["4. Governance & Promoters\n(Litigation, Auditor Turnover,\nRelated Party Transactions)"] --> EVAL
    P5["5. Valuation & Margin of Safety\n(Peer Multiples, WACA Basis,\nIPO Discount)"] --> EVAL
    P6["6. Liquidity, Lock-In & Tax\n(SEBI Reg 17 6-Mo Lock-In,\nOff-Market DIS, 24-Mo LTCG)"] --> EVAL
```

### Pillar 1: Regulatory & Listing Readiness
Before analyzing financial multiples, practitioners verify how close the issuer is to a public listing under the SEBI (Issue of Capital and Disclosure Requirements) [ICDR] Regulations:
- **Filing Status:** Verify whether the company has filed a DRHP on the SEBI Filings Portal. Acquiring unlisted shares prior to a DRHP filing carries substantial timeline and liquidity risk, as there is no statutory obligation for a private company to complete a listing.
- **Mainboard Eligibility Routes:** 
  - *Standard Profitability Route:* Requires at least ₹3 crore in net tangible assets in each of the preceding three full years and ₹15 crore in average pre-tax operating profit in at least three of the preceding five years.
  - *QIB / Alternative Route:* Designed for loss-making, high-growth technology enterprises, requiring at least 75% allocation to Qualified Institutional Buyers (QIBs).
- **Objects of the Issue (Fresh Issue vs. OFS):** Separate capital raised via a **Fresh Issue** (proceeds enter the company's balance sheet for capacity expansion, working capital, or debt reduction) from an **Offer for Sale (OFS)** (proceeds go to exiting private equity investors or promoters). A predominantly OFS issue with minimal growth capital requires scrutiny of insider exit motivations.

### Pillar 2: Business Model & Competitive Moat
- **Revenue Quality & Concentration:** Distinguish recurring, contract-backed revenue from one-off windfalls. Examine top-5 and top-10 customer and supplier concentration tables in the DRHP; dependence on a narrow client base exposes post-listing earnings to sudden shocks.
- **Unit Economics & Scalability:** Assess whether contribution margins expand alongside top-line growth. For consumer-facing and digital platforms, track Customer Acquisition Cost (CAC) trends relative to Customer Lifetime Value (LTV) and cohort retention.
- **Industry Tailwinds & Defensibility:** Benchmark market share, distribution reach, intellectual property, and customer switching costs against established listed peers.

### Pillar 3: Restated Financial Health (3-Year Track Record)
Indian issuers must present three full financial years (plus any applicable stub period) of restated financial statements prepared under Indian Accounting Standards (Ind AS). Emphasis must be placed on cash generation rather than accrual accounting profits:
- **Earnings Trajectory & Window Dressing Check:** Analyze 3-year Compound Annual Growth Rates (CAGR) across Revenue, EBITDA, and Profit After Tax (PAT). Flag abrupt margin spikes in the final pre-DRHP fiscal year or stub period, which frequently reflect temporary cuts in marketing, R&D, or employee expenses.
- **Cash Flow Conversion:** Compare Cash Flow from Operations (CFO) against EBITDA and PAT. Consistent accounting profits paired with weak or negative CFO indicate working capital stress, ballooning trade receivables, or aggressive revenue recognition.
- **Leverage & Capital Efficiency Ratios:** Evaluate Debt-to-Equity, Interest Coverage Ratio (ICR), Return on Equity (ROE), and Return on Capital Employed (ROCE) to determine how efficiently management deploys capital.

### Pillar 4: Governance, Promoters & Red Flags
- **Promoter Track Record & Litigation:** Inspect the *"Promoters and Promoter Group"* and *"Outstanding Litigation and Material Developments"* chapters of the DRHP for criminal proceedings, SEBI/RBI regulatory actions, tax disputes, or frequent statutory auditor resignations over the preceding three years.
- **Related Party Transactions (RPTs):** Scrutinize loans, advances, brand royalties, leases, and procurement contracts involving promoter-owned entities. High RPT volumes relative to revenue or net worth signal potential value leakage.
- **Cap Table Cleanliness:** Verify that complex instruments—such as Optionally Convertible Debentures (OCDs), Compulsorily Convertible Preference Shares (CCPS), and special shareholder veto rights—are converted or terminated prior to Red Herring Prospectus (RHP) filing.

### Pillar 5: Valuation & Margin of Safety
Unlisted share prices are formed through negotiated bilateral trades rather than transparent order-book discovery, often embedding optimistic premiums. Practitioners benchmark implied issue valuations against listed peers across four core multiples:

| Valuation Metric | Primary Applicability | Practitioner Benchmark Check |
|---|---|---|
| **P/E Ratio (Price-to-Earnings)** | Profitable, mature manufacturing, financial, and service businesses | Compare implied post-issue P/E (at upper price band) against listed peers' trailing 12-month and forward P/E. |
| **EV / EBITDA** | Capital-intensive, asset-heavy, or leveraged companies | Neutralizes capital structure and depreciation differences across comparable listed firms. |
| **Price-to-Sales (P/S)** | High-growth, pre-profit startups and digital platforms | Evaluate alongside gross margin profile, unit economics, and realistic timeline to EBITDA break-even. |
| **Last Round Valuation (WACA)** | Secondary pre-IPO unlisted share purchases | Compare current grey/unlisted quote against the Weighted Average Cost of Acquisition (WACA) disclosed in the DRHP. |

### Pillar 6: Liquidity, Lock-In & Tax Rules (Unlisted Market Buyers)
When advising clients purchasing shares in the pre-IPO unlisted market rather than bidding in the public IPO, structural regulatory constraints apply:
- **Mandatory 6-Month Post-Listing Lock-In:** Under Regulation 17 of SEBI (ICDR) Regulations, the entire pre-issue capital held by non-promoters is locked in for **6 months** from the date of IPO allotment. Unlisted buyers cannot exit on listing day to capture a listing pop; the investment thesis must remain viable six months post-listing.
- **Settlement & Counterparty Risk:** Off-market transfers occur via Delivery Instruction Slips (DIS) or electronic CDSL/NSDL off-market transfer modules rather than exchange clearing corporations. Counterparty verification and escrow/simultaneous settlement protocols are essential.
- **Capital Gains & Valuation Tax Rules:** Unlisted equity shares require a **24-month holding period** to qualify for Long-Term Capital Gains (LTCG) tax treatment (compared to 12 months for listed equities). Additionally, acquisitions below prescribed Fair Market Value (FMV) attract taxation under Section 56(2)(x) of the Income Tax Act.

---

### Practical Application Example: Evaluating a Pre-IPO Issue
> **Case Study (from Blueprint):**  
> Consider a consumer manufacturing firm filing a ₹1,200 crore DRHP structured as ₹300 crore Fresh Issue and ₹900 crore Offer for Sale (**75% OFS**).  
> - 3-year Revenue CAGR is 22%.  
> - PAT margin jumped from 6% in FY23 to 14% in FY25.  
> - **However:** CFO/EBITDA dropped from $0.85\times$ to $0.35\times$ due to rising trade receivables.  
> - Implied upper-band P/E is $58\times$ versus a listed peer average of $36\times$.  
> 
> *Diagnosis:* Under this framework, the heavy OFS (75%), deteriorating cash conversion, and 61% valuation premium trigger critical governance and pricing red flags—especially for unlisted buyers bound by the mandatory 6-month SEBI lock-in.

---

## Section 5: End-to-End Automated Pipeline Engineering for Prospectus Parsing & Quantitative Valuation

Building an automated pipeline to parse statutory pre-IPO prospectuses (such as SEC Form S-1 in the US or SEBI Draft Red Herring Prospectus [DRHP] in India) and generate an institutional quantitative pre-IPO valuation model involves **six distinct engineering stages**.

```text
┌────────────────────────────────────────────────────────────────────────┐
│                        EDGAR / SEBI SCRAPER                            │
│           (Query SEC EDGAR S-1/A or SEBI/NSE/BSE DRHP/RHP)             │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│             DOCUMENT PARTITIONING & LAYOUT EXTRACTION                  │
│       (Regex Boundary Headings, Marker, Nougat, Table Transformers)    │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│             INFORMATION EXTRACTION & STANDARDIZATION                   │
│         (LLM JSON Schema Enforcement / Pydantic Financial Ontology)    │
└───────────┬───────────────────────┼───────────────────────────┬────────┘
            │                       │                           │
            ▼                       ▼                           ▼
┌──────────────────────┐  ┌──────────────────────┐  ┌──────────────────────┐
│  CAP TABLE ENGINE    │  │ FINANCIAL STATEMENTS │  │ QUALITATIVE NLP      │
│  • CCPS/CCD ratios   │  │  RECONSTRUCTION      │  │  SCORER              │
│  • ESOP option pool  │  │ • Ind AS / US GAAP   │  │ • FinBERT sentiment  │
│  • Fresh vs. OFS     │  │ • Restated Balance   │  │ • Litigation claims /│
│  • Diluted post-IPO  │  │   Sheet, P&L, CFO    │  │   Net Worth ratio    │
│    share count       │  │ • Audit: A = L + E   │  │ • RPT / Revenue %    │
└───────────┬──────────┘  └──────────┬───────────┘  └──────────┬───────────┘
            │                        │                         │
            └────────────────────────┼─────────────────────────┘
                                     │
                                     ▼
┌────────────────────────────────────────────────────────────────────────┐
│                     PEER COMPS & VALUATION ENGINE                      │
│        • Dynamic Public Multiples (P/E, EV/EBITDA, EV/Sales, P/B)      │
│        • Parameter-Driven IPO Discount (10%–20%)                       │
│        • DCF with Step-Down WACC Curve & Fresh Cash Bridge             │
└────────────────────────────────────┬───────────────────────────────────┘
                                     │
                                     ▼
┌────────────────────────────────────────────────────────────────────────┐
│                  EXPORT & DYNAMIC SENSITIVITY OUTPUT                   │
│        (Streamlit Interactive Dashboard / OpenPyXL Auditable Excel /   │
│         PowerPoint Board Memos)                                        │
└────────────────────────────────────────────────────────────────────────┘
```

### Stage 1: Automated Prospectus Ingestion & Section Routing
- **Ingestion:** Query SEC EDGAR via `sec-edgar-downloader` / EDGAR API for US Form S-1/A; scrape SEBI/NSE/BSE for Indian DRHP/RHP PDFs using Playwright and BeautifulSoup.
- **Document Segmentation:** Boundary heading detection via regex and PDF outline trees into:
  1. *Financial Statements:* "Restated Financial Information", "Consolidated Financial Statements".
  2. *Capital Structure:* "Capitalisation and Indebtedness", "Objects of the Offer".
  3. *Operational & Risk Metrics:* "Management's Discussion and Analysis (MD&A)", "Risk Factors".

### Stage 2: High-Fidelity Table & Layout Parsing
- **Tooling:** Dedicated layout parsers (*Marker*, *Nougat*, *Table Transformer [TATR]*, *Docling*) extracting complex tables, multi-year restatements, footnote markers, and unit scales (INR Crores/Lakhs vs. USD Thousands/Millions).
- **Extraction Schema (3-Year History):**
  - *Balance Sheet:* Net Debt, Cash & Equivalents, Funded Borrowings, Lease Liabilities (Ind AS 116 / ASC 842), Net Worth.
  - *Income Statement:* Revenue, Gross Profit, EBITDA, Operating Profit, PAT.
  - *Cash Flow Statement:* CFO, CapEx, Financing Cash Flow (CFF), Free Cash Flow.

### Stage 3: Cap Table Normalization & Dilution Mechanics
- **Share Class Unification:** Parses conversion ratios for Series A–F Preferred Shares, CCDs, CCPS, liquidation preferences, and anti-dilution protections.
- **Fresh Issue vs. OFS:** Models new cash injected to balance sheet vs. secondary liquidity to selling shareholders.
- **Fully Diluted Post-IPO Share Count Formula:**
  $$\text{Post-IPO Diluted Shares} = \text{Existing Common Shares} + \sum (\text{Converted Preferred} \times \text{Ratio}) + \text{Vested Options/ESOPs} + \text{Fresh Issue Shares}$$

### Stage 4: Quantitative Valuation Engine
1. **Trading Comps with IPO Discount (10%–20%):**
   $$\text{Implied Offer Price per Share} = \frac{\text{Sector Multiple} \times \text{Company Metric} \times (1 - \text{IPO Discount})}{\text{Post-Issue Diluted Shares}}$$
2. **DCF with Step-Down WACC & Proceeds Cash Injection:**
   $$\text{FCFF} = \text{EBIT} \times (1 - t) + \text{D\&A} - \text{CapEx} - \Delta\text{NWC}$$
   Adds net Fresh Issue proceeds to starting cash, reducing interest expense on retired debt.

### Stage 5: Qualitative Risk & Sentiment NLP
- **FinBERT Sentiment Categorization:** Tags risk disclosures (*Regulatory*, *Legal*, *Operational*, *Client Concentration*).
- **Litigation Exposure Ratio:** $\frac{\sum \text{Pending Monetary Claims}}{\text{Net Worth}}$ *(flagged if $> 15\%$).*
- **RPT Leakage Ratio:** $\frac{\text{Total Annual RPT Volume}}{\text{Total Revenue}}$.

### Stage 6: Modular Implementation Tech Stack & Pydantic Schema

```python
from pydantic import BaseModel, Field, model_validator
from typing import List, Optional

class FinancialMetric(BaseModel):
    fiscal_year: str = Field(description="e.g. FY23, FY24, FY25 or stub period")
    revenue_operations: float = Field(description="Total revenue from operations in INR Cr or USD M")
    ebitda: float = Field(description="Earnings before interest, taxes, depreciation, and amortization")
    net_profit_pat: float = Field(description="Profit after tax")
    cash_and_equivalents: float = Field(description="Cash and cash equivalents")
    funded_debt: float = Field(description="Total borrowings excluding lease liabilities")
    lease_liabilities: float = Field(default=0.0, description="Operating lease liabilities under Ind AS 116 / ASC 842")
    cfo: float = Field(description="Cash flow from operations")
    capex: float = Field(description="Capital expenditures")

    @property
    def total_economic_debt(self) -> float:
        return self.funded_debt + self.lease_liabilities

    @property
    def cfo_to_ebitda(self) -> float:
        return (self.cfo / self.ebitda) if self.ebitda != 0 else 0.0

class CapitalStructure(BaseModel):
    pre_offer_equity_shares: float
    fresh_issue_amount_cr: float
    fresh_issue_shares: Optional[float] = None
    ofs_shares: float = Field(default=0.0, description="Shares offered for sale by selling shareholders")
    esop_pool_options_vested: float = Field(default=0.0)
    preferred_shares_convertible: float = Field(default=0.0)
    conversion_ratio: float = Field(default=1.0)

    @property
    def post_issue_diluted_shares(self) -> float:
        fresh = self.fresh_issue_shares or 0.0
        converted_pref = self.preferred_shares_convertible * self.conversion_ratio
        return self.pre_offer_equity_shares + fresh + converted_pref + self.esop_pool_options_vested

class PreIPOProspectusData(BaseModel):
    company_name: str
    filing_type: str = Field(description="DRHP, RHP, S-1, S-1/A")
    peer_group: List[str]
    financials: List[FinancialMetric]
    capital_structure: CapitalStructure
    objects_of_offer_fresh_cash: float
    contingent_liabilities_cr: float = Field(default=0.0)
    net_worth_cr: float
    annual_rpt_volume_cr: float = Field(default=0.0)
    top_5_customer_revenue_percentage: Optional[float] = None

    @model_validator(mode="after")
    def verify_financial_integrity(self):
        if self.net_worth_cr > 0 and (self.contingent_liabilities_cr / self.net_worth_cr) > 0.15:
            pass
        return self
```

---

## Section 6: Live Market Data Ingestion & NSE India API Architecture

To transition pre-IPO models from static prospectus snapshots into live, market-synchronized decision tools, the platform interfaces directly with the National Stock Exchange of India (NSE). 

The NSE data landscape operates across two major dimensions:
1. **Exchange-Level Institutional Interfaces (2025–2026 Circulars):**
   - *NSE Single Filing System API (NSE-BSE Integrated Reporting):* Standardized API framework for statutory filings under SEBI Listing Obligations and Disclosure Requirements (LODR). Provides direct machine-readable feeds for Regulation 33 Financial Statements (XBRL/JSON), shareholding patterns, and corporate governance reports.
   - *Order & Trade Drop Copy API v3.0 (Late 2026):* Binary/JSON socket protocols for institutional members to stream drop-copy executions.
   - *Client Direct API (SEBI Algorithmic Mandate):* Standardized broker-mediated REST/WebSocket protocol enforcing static IP mapping and 10 Orders-Per-Second (OPS) throttling for retail algorithmic trading.
2. **Primary Market & IPO Web Endpoints (`nseindia.com/api/...`):**
   - High-value REST endpoints powering the official NSE primary market portal, delivering real-time IPO schedules, live subscription multiples, anchor books, and listed peer metrics.

```mermaid
flowchart TD
    subgraph NSE_DATA["NSE Live Data Endpoints"]
        E1["/api/ipo-current-issue\n(Issue Master & Dates)"]
        E2["/api/ipo-bid-details\n(Live 3-Day Subscription Multiples)"]
        E3["/api/quote-equity\n(Live Listed Peer Comps)"]
        E4["/api/corporate-announcements\n(Statutory Filings & Events)"]
        E5["/api/allIndices\n(India VIX & Sector Benchmarks)"]
    end

    subgraph PRE_IPO_ENGINE["ProfSurProject Pre-IPO Pipeline"]
        M1["Price Band Unlocking\n(Transitions unpriced DRHP to priced RHP)"]
        M2["Sentiment & Demand Score\n(QIB, NII, Retail Oversubscription Multiples)"]
        M3["Dynamic Trading Comps\n(P/E, EV/EBITDA, EV/Sales with 10-20% IPO Discount)"]
        M4["Red-Flag NLP Scanner\n(Litigation disclosures & Show-Cause notices)"]
        M5["Macro Regime Adjuster\n(VIX volatility step-down WACC calibration)"]
    end

    E1 --> M1
    E2 --> M2
    E3 --> M3
    E4 --> M4
    E5 --> M5
```

### 6.1 Extracted Data Taxonomy for Pre-IPO Intelligence

| Domain | NSE Endpoint | Extracted Data Attributes | Pre-IPO Intelligence Use Case |
|---|---|---|---|
| **IPO Schedule & Terms** | `/api/ipo-current-issue` | Issue Name, Symbol, Issue Type, Open/Close Dates, **Price Band (Floor & Cap)**, Lot Size, Issue Size (₹ Cr). | Unlocks the statutory valuation circuit breaker (`BLOCKED_MISSING_REVIEWED_PRICE_BAND`). |
| **Live Subscription Tracking** | `/api/ipo-bid-details?symbol={SYM}` | • **QIB Subscription Multiple** ($x$ times)<br>• **NII / HNI Multiple**<br>• **Retail Individual (RII) Multiple**<br>• Total Cumulative Demand | Feeds directly into **Score 2 (Pricing & Sentiment Score)** and first-day pop prediction. |
| **Anchor Book & Allotment** | `/api/ipo-detail?symbol={SYM}` & Allocation Sheet | Total anchor size (₹ Cr), allocation count, proportion of marquee domestic MFs vs. sovereign wealth funds vs. opaque FPIs. | Computes the **Anchor Quality Tiering Index**. |
| **Declared Listed Comps** | `/api/quote-equity?symbol={PEER}` | Live Price, Market Cap, Trailing P/E, Forward P/E, Industry P/E, 52-Week High/Low, Beta. | Feeds the **Comparable Company Analysis (Trading Comps)** matrix. |
| **Corporate Announcements** | `/api/corporate-announcements?index=equities` | Board meeting notices, SEBI/RBI show-cause disclosures, auditor change events. | Continuous background ingestion for the **Automated DRHP Red-Flag Scanner**. |
| **Market Volatility Index** | `/api/allIndices` | India VIX, Nifty 50 P/E, Nifty Smallcap/Midcap multiples. | Quantifies market sentiment and tunes the private-to-public WACC spread. |

### 6.2 Connection Architecture & Protocol

Because `nseindia.com` uses Cloudflare anti-bot verification and dynamic cookie rotation, sending a stateless HTTP `GET` request returns `403 Forbidden`. The production client follows a **two-step session handshake**:
1. **Session Initialization:** Send a `GET` request to the base homepage (`https://www.nseindia.com`) with realistic browser headers to harvest session cookies (`nsit`, `nseappid`, `ak_bmsc`).
2. **Subsequent API Queries:** Re-use the authenticated `requests.Session` object with `Referer: https://www.nseindia.com/` for all target JSON endpoints.
3. **Automatic Cookie Rotation:** Refresh the session every 5–10 minutes to prevent expiration.

#### Production Python Client Implementation (`models/pre_ipo_nse_client.py`)

```python
import time
import requests
from typing import Dict, Any, Optional

class NSELiveClient:
    """
    Session-aware live client for NSE India primary market and equity endpoints.
    Handles Cloudflare handshake, cookie harvesting, and header sequencing.
    """
    BASE_URL = "https://www.nseindia.com"
    API_IPO_CURRENT = "https://www.nseindia.com/api/ipo-current-issue"
    API_IPO_BID = "https://www.nseindia.com/api/ipo-bid-details?symbol={symbol}"
    API_QUOTE_EQUITY = "https://www.nseindia.com/api/quote-equity?symbol={symbol}"

    HEADERS = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
        "Accept": "*/*",
        "Accept-Language": "en-US,en;q=0.9",
        "Accept-Encoding": "gzip, deflate, br",
        "Referer": "https://www.nseindia.com/",
        "Connection": "keep-alive",
    }

    def __init__(self, session_ttl_seconds: int = 300):
        self.session_ttl = session_ttl_seconds
        self.last_handshake: float = 0.0
        self.session: requests.Session = requests.Session()
        self.session.headers.update(self.HEADERS)

    def _ensure_session(self) -> None:
        now = time.time()
        if now - self.last_handshake > self.session_ttl or not self.session.cookies:
            resp = self.session.get(self.BASE_URL, timeout=10)
            if resp.status_code == 200:
                self.last_handshake = now
            else:
                raise ConnectionError(f"NSE Session Handshake failed: HTTP {resp.status_code}")

    def get_current_ipos(self) -> Dict[str, Any]:
        self._ensure_session()
        resp = self.session.get(self.API_IPO_CURRENT, timeout=10)
        resp.raise_for_status()
        return resp.json()

    def get_live_subscription(self, symbol: str) -> Dict[str, Any]:
        self._ensure_session()
        url = self.API_IPO_BID.format(symbol=symbol.upper())
        resp = self.session.get(url, timeout=10)
        resp.raise_for_status()
        return resp.json()

    def get_listed_peer_multiples(self, symbol: str) -> Dict[str, Any]:
        self._ensure_session()
        url = self.API_QUOTE_EQUITY.format(symbol=symbol.upper())
        resp = self.session.get(url, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        
        price_info = data.get("priceInfo", {})
        metadata = data.get("metadata", {})
        security_info = data.get("securityInfo", {})
        
        return {
            "symbol": symbol.upper(),
            "last_price": price_info.get("lastPrice"),
            "pe_ratio": metadata.get("pdSectorPe") or security_info.get("pe"),
            "market_cap_cr": metadata.get("totalMarketCap"),
            "52w_high": price_info.get("weekHighLow", {}).get("max"),
            "52w_low": price_info.get("weekHighLow", {}).get("min"),
        }
```

---

## Section 7: Cohort Lifecycle & Post-IPO Trajectory Analysis (IPO Vintage Benchmarking)

While standard peer review asks *"How is Peer X priced today?"*, longitudinal peer cohort analysis asks: 
> **"When Peer X went public at a similar stage, margin profile, and multiple, how did its story actually play out over the next 4 to 12 quarters?"**

In Indian primary markets especially, empirical studies show a sharp regime shift: **short-term listing gains are driven by demand and sentiment** (subscription multiples and Grey Market Premium), whereas **1-year and multi-year post-listing trajectories revert strictly to fundamental execution, promoter retention, and multiple compression/expansion**.

```mermaid
flowchart LR
    subgraph T0["At-IPO Baseline (T = 0)"]
        D1["DRHP Financial Profile\n• Revenue CAGR\n• EBITDA Margin\n• CFO / EBITDA\n• Fresh vs. OFS %"]
        D2["Issue Pricing & Demand\n• Issue P/E, EV/EBITDA\n• QIB / Anchor Multiple\n• Grey Market Premium"]
    end

    subgraph TRAJECTORY["Event-Time Longitudinal Window (T+1D to T+24M)"]
        T1["T+1D to T+30D:\nListing Pop & Anchor 30D Unwind"]
        T2["T+90D:\nAnchor 90D Unwind"]
        T3["T+180D (M6):\nSEBI Reg 17 Non-Promoter Lock-In Expiry"]
        T4["T+4Q to T+8Q:\nDRHP vs. Actual Quarterly Reality Check"]
    end

    subgraph OUTCOMES["Post-IPO Behavioral Archetypes"]
        O1["1. Compounding Compounder\n(Sustained Alpha, High CFO Conversion)"]
        O2["2. Priced-to-Perfection De-Rater\n(Growth Deceleration, Multiple Compression)"]
        O3["3. PE Exit Supply Overhang\n(Drawdowns at M6 Lock-In Expiry)"]
        O4["4. Window-Dressed Fader\n(Post-IPO Margin & Accrual Collapse)"]
    end

    D1 & D2 --> T1 --> T2 --> T3 --> T4
    T4 --> O1 & O2 & O3 & O4
```

### 7.1 What This Longitudinal Lens Reveals
Analyzing how prior IPOs in the same sector played out post-listing exposes four recurring market patterns that static point-in-time valuation tables hide:

1. **The Multiple Compression vs. Earnings Catch-Up Race:**
   Many high-growth companies list at aggressive valuations (e.g., $60\times$–$80\times$ $P/E$ or $12\times$ $EV/\text{Sales}$) on the promise that rapid earnings growth will "grow into the multiple." Tracking prior sector listings reveals whether peers actually grew earnings fast enough to compress their multiple organically—or whether the stock price suffered a 30%–50% de-rating when post-IPO growth decelerated.
2. **Pre-IPO "Window Dressing" Mean Reversion:**
   Comparing a peer's DRHP numbers (FY-1 and stub period prior to listing) against its first 4–8 post-listing quarterly results shows whether margins or cash conversion were temporarily inflated before the IPO and normalized downward once public.
3. **Lock-In Expiry Supply Overhangs:**
   Tracking how peer stocks behaved around statutory supply unlocks—specifically the **30-day and 90-day Anchor Investor lock-in expiries** and the **6-month mandatory SEBI ICDR non-promoter / pre-IPO investor lock-in expiry**—quantifies the historical selling pressure caused by PE/VC exits in that specific sector.
4. **Use-of-Proceeds Execution vs. Guidance:**
   Did prior peers in the sector deploy their Fresh Issue capital on schedule (capex, debt reduction, store expansion) and deliver the promised ROCE lift, or did capex delays and working capital bloat drag returns down?

---

### 7.2 The 4-Stage Trajectory Framework

To build this as a repeatable analytical module inside `ProfSurProject`, we align every historical sector peer to a common **Event-Time ($T = 0$)** study timeline rather than calendar dates:

#### Step 1: Event-Time Alignment ($T_0$ Normalization)
Anchor each comparable listed company at its own IPO Listing Date ($T_0$). Extract two snapshots for every historical peer:
- **At-IPO Baseline ($T_0$):** Issue price, implied $P/E$ or $EV/\text{EBITDA}$ at issue, Fresh Issue vs. OFS split, pre-IPO 3-year revenue CAGR, EBITDA margin, CFO/EBITDA, and QIB/Anchor subscription.
- **Post-IPO Trajectory ($T_{+1\text{D}}, T_{+30\text{D}}, T_{+90\text{D}}, T_{+6\text{M}}, T_{+1\text{Y}}, T_{+2\text{Y}}$):** Cumulative total return, benchmark-adjusted alpha (vs. Nifty 50 / Nifty Midcap / Sector Index), and trailing valuation multiple at each milestone.

#### Step 2: DRHP-to-Quarterly Reality Check (Guidance vs. Actuals)
Compare the peer's pre-IPO 3-year trajectory (from its DRHP) against its first 4–8 post-IPO quarters (from NSE/BSE quarterly filings / CMIE Prowess):
- **Growth Delta:**
  $$\Delta_{\text{growth}} = \text{Post-IPO 4Q YoY Revenue Growth} - \text{Pre-IPO 3Y Revenue CAGR}$$
- **Margin Delta:**
  $$\Delta_{\text{margin}} = \text{Post-IPO EBITDA Margin} - \text{Pre-IPO Peak/Stub EBITDA Margin}$$
- **Cash Conversion Drift:** Did $CFO/\text{EBITDA}$ hold steady or deteriorate post-listing?

#### Step 3: Lock-In Expiry Event Study
Measure abnormal returns and delivery volume spikes in the $[-5\text{ days}, +10\text{ days}]$ trading windows around:
- **Day 30 & Day 90:** Anchor investor partial/full lock-in release.
- **Month 6 (Day 180):** Pre-IPO non-promoter / PE/VC lock-in release (SEBI ICDR Reg 17).

> *Empirical Signal:* If prior sector peers with $>50\%$ OFS or heavy PE backing consistently dropped $8\%$–$15\%$ around Day 180, that becomes a direct risk-timing signal for both IPO bidders and unlisted pre-IPO buyers.

#### Step 4: Archetype Clustering (Mapping the Current IPO to Peer "Stories")
Classify historical sector IPOs into four behavioral archetypes based on how their post-listing story unfolded, then score which archetype the current DRHP issuer resembles most closely:

| Post-IPO Archetype | At-IPO Signature (DRHP Profile) | How the Post-Listing Story Played Out |
|---|---|---|
| **1. Compounding Compounder** | Reasonable issue multiple ($\le$ peer median), high Fresh Issue %, strong $CFO/\text{EBITDA} > 0.8\times$, durable ROCE. | Modest Day-1 pop, absorbed lock-in expiries smoothly, delivered steady earnings beats and sustained 1Y–3Y alpha. |
| **2. Priced-to-Perfection De-Rater** | Strong business, but issued at a $40\%$–$80\%$ multiple premium to peers; peak stub-period margins. | Strong Day-1 listing pop, followed by 6–18 months of sideways/negative stock returns while earnings caught up to valuation. |
| **3. PE Exit / Supply Overhang** | Heavy OFS ($>70\%$), multiple late-stage PE funds on cap table, high pre-IPO secondary WACA step-ups. | Repeated price drawdowns around Day 90 (Anchor) and Month 6 (Pre-IPO lock-in) as institutional block deals hit the tape. |
| **4. Pre-IPO Window-Dressed Fader** | Sudden margin jump in final pre-DRHP year, rising receivable days, high RPTs or contingent liabilities. | Missed post-listing quarterly estimates within 2–3 quarters; sharp multiple compression below issue price. |

---

### 7.3 Why Current Tools Miss This (And How ProfSur Fills the Gap)

- **The Blind Spot in Existing Platforms:**
  - *Public market terminals (Screener, Capital IQ, Bloomberg):* Show a peer's current stock chart and current multiples, forgetting what multiple that peer traded at on its own IPO day 2 or 3 years ago.
  - *IPO portals (Chittorgarh, InvestorGain):* Track listing-day gain and current LTP, but do not link pre-IPO DRHP financial quality to post-listing quarterly earnings delivery or lock-in drawdowns.
- **The ProfSur Advantage ("Peer IPO Time-Machine" View):**
  Inside `ProfSurProject`'s Pre-IPO Intelligence workspace, we render an **Event-Time Cohort Overlay ($T_0$ to $T_{+24\text{M}}$)** comparing the current issuer's DRHP metrics against 3–5 sector peers as they looked on their own IPO filing dates, alongside normalized price paths, multiple compression curves, and lock-in expiry markers.

---

## Section 8: Institutional Frameworks & Academic Literature

The scoring weights, feature selection, and dual-score design of the application are grounded in established Indian regulatory grading frameworks and peer-reviewed empirical research on NSE and BSE listings:

### 8.1 Institutional & Regulatory Frameworks (India-Specific)
- **CRISIL / ICRA IPO Grading Methodology:** Introduced under SEBI's framework in 2007 (made optional in 2014), CRISIL's IPO Grading Methodology remains the benchmark practitioner scorecard in India. It evaluates issuers on a 1-to-5 scale across four pillars: **Business Prospects**, **Financial Position**, **Management Capabilities**, and **Corporate Governance**. Crucially, it separates fundamental business quality from issue pricing—a structural separation the application must preserve.
- **SEBI Statutory KPI Disclosure Framework (ICDR Amendments):** SEBI mandates that loss-making and new-age issuers disclose audited Key Performance Indicators (KPIs) in the *"Basis for Issue Price"* chapter of the DRHP, alongside Weighted Average Cost of Acquisition (WACA) across past private funding rounds. Parsing this mandatory table provides a regulator-audited valuation anchor.

### 8.2 Peer-Reviewed Academic Studies on Indian IPOs
- **Pre-IPO Financial Performance & Offer Price Estimation (JRFM, 2023):** Empirical analysis of Indian IPOs demonstrates that four financial metrics exhibit the highest combined explanatory power for justifying IPO offer prices: **Net Asset Value (NAV)**, **Return on Assets (ROA)**, **Profit After Tax (PAT)**, and **Return on Net Worth (RONW)**.
- **Systematic Literature Review of Indian IPOs (2023):** A PRISMA systematic review synthesizing 111 studies on the Indian primary market establishes that while agency signals (promoter dilution, Fresh Issue vs. OFS split) and institutional demand (QIB/Anchor subscription) drive short-term listing pops, corporate governance quality and pre-IPO earnings management (artificial margin inflation prior to filing) are the strongest predictors of long-run post-listing underperformance.
- **Efficacy of IPO Grading on Long-Run Operating Performance (EELET, IJF):** Studies evaluating graded Indian IPOs show that structured fundamental grading correlates significantly with lower post-listing return volatility and superior industry-adjusted operating performance (PBDITA/Total Assets), even though fundamental grades alone do not predict day-one listing gains.

### 8.3 Machine Learning & Prospectus NLP Research
- **ML Prediction of Indian IPO Underperformance (SJMSOM, IIT Bombay):** Research comparing ensemble machine learning models (Gradient Boosting, Random Forest) against traditional regressions on Indian listings confirms that **Gradient Boosting** significantly improves underperformance prediction, identifying profit margins, debt-to-assets ratio, and prevailing market sentiment as top predictive features.
- **Automated RHP Rating & Textual Uncertainty Models (SSRN):** Quantitative NLP studies analyzing Red Herring Prospectuses demonstrate that linguistic tone, risk-factor density, and litigation disclosure complexity significantly explain valuation uncertainty and improve abnormal return forecasts compared to financial ratios alone.

---

## Section 9: The Recommended Dual-Score Architecture

Based on the consensus across Indian IPO literature, an institutional application must avoid blending fundamentals and market hype into a single opaque number. Instead, it computes **two independent, transparent scores**:

```text
                                  ┌──────────────────────────────────────────────┐
                                  │          PRE-IPO EVALUATION ENGINE           │
                                  └──────────────────────┬───────────────────────┘
                                                         │
                         ┌───────────────────────────────┴───────────────────────────────┐
                         ▼                                                               ▼
        ┌──────────────────────────────────┐                            ┌──────────────────────────────────┐
        │  SCORE 1: FUNDAMENTAL QUALITY    │                            │    SCORE 2: PRICING & SENTIMENT  │
        │    (Long-Term Hold Signal)       │                            │      (Listing Gain Signal)       │
        └────────────────┬─────────────────┘                            └────────────────┬─────────────────┘
                         │                                                               │
        • Return on Net Worth (RONW)                                    • Peer Multiple Discount (P/E, EV/EBITDA)
        • Return on Assets (ROA)                                        • Fresh Issue vs. OFS Capital Split
        • CFO-to-EBITDA Cash Conversion                                 • Anchor Investor Tiering (MFs/SWFs vs. FPIs)
        • Debt-to-Assets & Ind AS 116 Perimeter                         • QIB / NII Live Subscription Multiples
        • Window-Dressing & Accrual Check                               • Grey Market Premium (GMP) Dynamics
        • NLP Risk-Factor & Litigation Density                          • WACA Ratio vs. Upper Price Band
```

1. **Fundamental & Governance Score (Long-Term Hold Signal):** Weighted toward RONW, ROA, CFO-to-EBITDA conversion, Debt-to-Assets, and NLP red-flag scans of Risk Factors and Litigations (grounded in CRISIL methodology, JRFM 2023, and IIT Bombay ML findings).
2. **Pricing & Sentiment Score (Listing Gain Signal):** Weighted toward peer P/E or EV/EBITDA discount, Fresh Issue vs. OFS ratio, Anchor Investor quality, and live QIB/NII subscription multiples (grounded in Indian IPO underpricing literature).

---

## Section 10: Recommended 4-Layer Production Architecture for `ProfSurProject`

To translate this academic and industry landscape into a high-precision engine inside `ProfSurProject`, we combine **four complementary production layers**:

1. **Extraction & Semantic Layer:** Layout-aware PDF parser (**Docling**) + Pydantic schema-enforced LLM + dense text embeddings (**BGE-large / FinBERT**) for DRHP table extraction, risk scoring, and unbiased economic peer discovery.
2. **Econometric Calibration Layer:** Huber-robust cross-sectional regressions (`statsmodels`) for Warranted Fair Multiples + Buy-and-Hold Abnormal Return (**BHAR**) event-study curves across historical sector peers ($T_0$ to $T_{+24\text{M}}$).
3. **Machine Learning Layer:** Walk-forward validated **LightGBM / CatBoost** classifiers trained on historical Indian IPOs to score Fundamental Hold Quality vs. Listing-Day / Lock-In Drawdown Risk.
4. **Deterministic Valuation Core:** Pure Python financial engine computing Diluted Post-Fresh-Issue Comps, Survival-Adjusted DCF, and Unlisted Lock-In Arbitrage.

---

## Section 11: Structured Academic & Econometric Bibliography (with Key Equations & Datasets)

A rigorous pre-IPO intelligence platform requires grounding in academic asset pricing, empirical microeconometrics, and domain-adapted financial machine learning. The literature is structured below across three complementary methodological taxonomies: foundational economic theory, cross-sectional econometric specifications, and modern machine learning/NLP architectures.

### 11.1 Foundational Asset-Pricing, Information Asymmetry & Valuation Frameworks

| Framework / Author | Core Mechanism & Exact Formulation | Empirical Dataset & Variables |
| :--- | :--- | :--- |
| **Winner's Curse & Asymmetric Information**<br>*(Rock, 1986)* | $\text{E}[R_1 \mid \text{Allocated}] = 0 \implies P_{\text{offer}} < \text{E}[V]$<br><br>Informed institutional investors crowd out uninformed retail investors in high-quality offerings. Issuers must embed a structural **IPO Discount** so uninformed demand participates to clear the book. | **US & Global Primary Market Allocations:**<br>• Institutional vs. retail allocation ratios<br>• Offer price discount relative to secondary market fair value<br>• Over-subscription multiples across investor tranches |
| **Promoter Retention Signalling**<br>*(Leland & Pyle, 1977)* | $V_0 = f(\alpha_{\text{retained}}, \sigma^2_{\text{cashflow}}), \quad \frac{\partial V_0}{\partial \alpha_{\text{retained}}} > 0$<br><br>Insiders hold private information regarding true cash-flow distribution. Higher post-issue equity retention ($\alpha_{\text{retained}}$) and lower Offer for Sale (OFS) proportion credibly signal private intrinsic quality. | **Primary Equity Issuances (NSE / BSE / SEC):**<br>• Fresh Issue capital vs. OFS exit ratio<br>• Post-issue promoter shareholding %<br>• Statutory lock-in commitment duration |
| **Seasoned Offerings & Imitation Costs**<br>*(Welch, 1989; Allen & Faulhaber, 1989)* | $P_{\text{offer}} < V^* \implies \text{Paved path for Seasoned Offerings (QIP / Rights)}$<br><br>High-quality firms intentionally underprice during initial issuance to leave a positive market sentiment, recouping capital at lower dilution during subsequent Qualified Institutional Placements (QIP). | **Multi-Stage Corporate Issuances:**<br>• Follow-on offering frequency within 36 months<br>• Cost of equity spread between IPO and post-listing QIPs |
| **Warranted Multiples & Statistical Comps**<br>*(Bhojraj & Lee, 2002; Damodaran)* | $\widehat{M}_i = \hat{\alpha} + \hat{\beta}_1 g_i + \hat{\beta}_2 \text{ROCE}_i + \hat{\beta}_3 \text{Leverage}_i + \hat{\beta}_4 \text{Payout}_i$<br><br>Replaces subjective peer selection with cross-sectional regression-implied fair multiples conditioned on fundamentals, growth velocity, and capital structure. | **Compustat / NSE-BSE Listed Universe:**<br>• $P/E$, $EV/\text{EBITDA}$, $EV/\text{Sales}$<br>• 3-Year EPS / Revenue CAGR ($g$)<br>• Return on Capital Employed (ROCE)<br>• Net Debt / EBITDA & Dividend Payout % |
| **Survival-Adjusted Two-Stage DCF**<br>*(Damodaran Emerging Market / Pre-Profit Valuation)* | $V_{\text{equity}} = \text{DCF}_{\text{going concern}} \times (1 - p_{\text{fail}}) + V_{\text{distress}} \times p_{\text{fail}} + \text{Cash}_{\text{fresh}}$<br><br>Adjusts high-growth, pre-profit issuers for structural failure probability ($p_{\text{fail}}$) and models post-IPO WACC step-down as liquidity and governance risk decline post-listing. | **Emerging Market Tech / Consumer IPOs:**<br>• Bottom-up unlevered sector beta adjusted for cash<br>• Cost of capital step-down path ($14.5\% \to 11.2\%$)<br>• Current cash burn rate and months of runway |
| **Forensic Earnings Quality (Window Dressing)**<br>*(Sloan, 1996; Beneish, 1999)* | $\text{Accrual Ratio} = \frac{\text{PAT} - \text{CFO} - \text{CFI}}{\text{Average Total Assets}}$<br><br>$\text{DSRI} = \frac{\text{Receivables}_t / \text{Sales}_t}{\text{Receivables}_{t-1} / \text{Sales}_{t-1}}$<br><br>Detects aggressive revenue recognition, deferred expenses, and balance-sheet accrual bloat in restated pre-DRHP stub periods. | **Restated 3-Year Ind AS / GAAP Filings:**<br>• Cash Flow from Operations to EBITDA ratio<br>• Trade receivable DSO spikes in stub periods<br>• Other non-operating income as % of PBT |
| **Downside Risk D-CAPM for Emerging Markets**<br>*(Estrada, 2002)* | $\beta_i^D = \frac{\text{E}[\min(R_i - \mu_i, 0) \cdot \min(R_m - \mu_m, 0)]}{\text{E}[\min(R_m - \mu_m, 0)^2]}$<br><br>Replaces standard CAPM beta with semi-variance downside beta, penalizing downside drawdowns rather than upside volatility for unseasoned equities. | **Emerging Market Primary Indices:**<br>• Asymmetric downside covariance with market benchmark<br>• High-growth technology issuer return series |

---

### 11.2 Econometric Specifications in Empirical IPO Research

| Econometric Method | Exact Mathematical Specification | Datasets & Empirical Findings (Indian & Global) |
| :--- | :--- | :--- |
| **Buy-and-Hold Abnormal Returns (BHAR)**<br>*(Ritter, 1991; Indian Primary Market Reviews)* | $\text{BHAR}_{i,T} = \prod_{t=1}^{T}(1 + R_{it}) - \prod_{t=1}^{T}(1 + R_{\text{bench},t})$<br><br>Evaluates compound wealth relatives across investment horizons $T \in \{1\text{D}, 30\text{D}, 90\text{D}, 180\text{D}, 1\text{Y}, 3\text{Y}\}$. | **NSE/BSE Listings (2000–2025) vs. Nifty 50 / Midcap 150:**<br>Confirms initial listing gains are sentiment-driven, while 180-day and 365-day abnormal returns revert to fundamental execution and multiple re-rating. |
| **Huber-Robust Cross-Sectional Multiple Regression** | $\min_{\beta} \sum_{i=1}^{N} \rho_\delta\!\left(M_i - X_i'\beta\right), \quad \rho_\delta(u) = \begin{cases} \frac{1}{2}u^2 & \vert u\vert \le \delta \\ \delta(\vert u\vert - \frac{1}{2}\delta) & \vert u\vert > \delta \end{cases}$<br><br>Replaces standard OLS to eliminate bias caused by extreme valuation multiple outliers in listed peer groups. | **NSE/BSE Sector Peers + CMIE Prowess:**<br>• Winsorized $P/E$ and $EV/\text{EBITDA}$<br>• 3-Year EBITDA CAGR, RONW, CFO/EBITDA<br>• Robust estimation of warranted fair multiples |
| **Heckman Two-Stage Selection Correction** | **Stage 1 (Probit Selection):**<br>$\Pr(\text{IPO}_i = 1) = \Phi(Z_i'\gamma)$<br><br>**Stage 2 (Outcome Model):**<br>$Y_i = X_i'\beta + \theta \lambda(Z_i'\gamma) + \epsilon_i$<br><br>Corrects for endogenous market-timing bias (firms list during bubble valuations or peak operational margin cycles). | **Private-to-Public Firm Panels (MCA + SEBI DRHP):**<br>The Inverse Mills Ratio ($\lambda$) isolates authentic post-listing operational alpha from opportunistic market-timing bias. |
| **Lock-In Expiry Event Study (CAR)** | $\text{CAR}_i[\tau_1, \tau_2] = \sum_{t=\tau_1}^{\tau_2} \left(R_{it} - \hat{\alpha}_i - \hat{\beta}_i R_{mt}\right)$<br><br>Calculated across event window $[ -5\text{D}, +10\text{D}]$ around Day 30/90 Anchor and Day 180 Pre-IPO Investor lock-in expirations. | **NSE/BSE Bulk/Block Deals & Delivery Volumes:**<br>Issues with heavy OFS and private equity selling exhibit statistically significant negative Cumulative Abnormal Returns around Month 6. |
| **Statutory Offer Price Justification Model**<br>*(JRFM, 2023 — Indian IPOs)* | $P_{\text{offer},i} = \beta_0 + \beta_1 \text{NAV}_i + \beta_2 \text{ROA}_i + \beta_3 \text{PAT}_i + \beta_4 \text{RONW}_i + \epsilon_i$<br><br>Cross-sectional regression isolating mandatory SEBI Reg 26(1) disclosure metrics on historical Indian mainboard offerings. | **Indian Mainboard IPO Dataset (2010–2022):**<br>Empirical findings prove Net Asset Value (NAV), ROA, PAT, and RONW possess highest joint explanatory power ($R^2 \approx 0.72$) for offer pricing. |

---

### 11.3 Machine Learning & Prospectus NLP Literature

| Model Family / Paper | Architecture & Formulation | Dataset & Key Quantitative Takeaway |
| :--- | :--- | :--- |
| **Gradient Boosted Decision Trees**<br>*(Agrawal & Ananthakumar, SJMSOM IIT Bombay)* | $F_M(x) = \sum_{m=1}^{M} \eta h_m(x; \theta_m)$<br><br>Minimizing regularized log-loss / Huber loss across combined tabular prospectus fundamentals and book-building market metrics. | **Indian Mainboard IPOs (NSE/BSE):**<br>GBDTs (CatBoost / LightGBM) significantly outperform classical logistic and linear regressions in predicting post-listing underperformance and drawdown risk. |
| **Prospectus Textual Uncertainty & Tone**<br>*(Loughran & McDonald, 2013; SSRN Indian RHP Studies)* | $\text{Uncertainty Score}_i = \frac{\sum w_{\text{uncertain}} \in \text{Risk/MD&A}_i}{\text{Total Tokens}_i}$<br><br>Coupled with domain-adapted **FinBERT** and **DeBERTa-v3** contextual embeddings across Chapter IV (Risk Factors) and Outstanding Litigation tables. | **SEBI RHP Filings & SEC S-1s:**<br>Higher textual uncertainty density and litigation counts correlate with wider initial underpricing spreads and elevated 1-year post-listing return volatility. |
| **Semantic Embedding Peer Retrieval**<br>*(Dense Vector Cosine Similarity)* | $\text{Sim}(A, B) = \frac{\mathbf{e}_A \cdot \mathbf{e}_B}{\Vert\mathbf{e}_A\Vert \Vert\mathbf{e}_B\Vert}$<br><br>Dense vector representations generated from DRHP *Our Business* descriptions matched against listed public companies' business descriptions. | **NSE/BSE Listed Universe (~2,200+ active equities):**<br>Uncovers omitted low-multiple direct competitors systematically excluded from merchant bankers' cherry-picked peer lists in DRHP filings. |
| **Cohort Trajectory Clustering**<br>*(Dynamic Time Warping / Gaussian Mixture Models)* | $p(x_i) = \sum_{k=1}^{K} \pi_k \mathcal{N}(x_i \mid \mu_k, \Sigma_k)$<br><br>Unsupervised clustering of historical sector IPOs on $T_0$-aligned post-listing return, margin, and multiple compression trajectories ($T_0$ to $T_{+24\text{M}}$). | **Historical Indian IPO Database:**<br>Statistically separates new offerings into four behavioral archetypes: *Compounding Compounder*, *Priced-to-Perfection De-Rater*, *Post-Listing Margin Deteriorator*, and *PE Exit Overhang*. |
| **Venture Capital Exit Classifiers**<br>*(CapitalVX, Ross et al., 2021 — MIT / SSRN)* | Binary & multi-class ensemble classifiers predicting IPO probability vs. M&A vs. failure across venture financing rounds and cap table milestones. | **Global Venture Deals & Secondary Trades:**<br>Proves pre-IPO round step-up multiples and lead investor reputation tiers provide statistically significant signals of public market survival. |

---

## Section 12: Walk-Forward Machine Learning Feature Engineering Pipeline for Indian IPOs (Mainboard & SME)

To eliminate look-ahead bias and protect models from macroeconomic regime leakage (e.g., training during 2020–2021 zero-rate liquidity expansion and testing during 2022–2023 monetary tightening), the machine learning framework in `ProfSurProject` enforces strict **point-in-time feature construction** and **expanding-window walk-forward validation**.

### 12.1 End-to-End Walk-Forward Pipeline Architecture

```text
[Stage 1: Point-in-Time Data Cutoff (T_cutoff = 5:00 PM IST on Final Bidding Day)]
   ├── DRHP / RHP Restated Ind AS Financial Tables (3 Full Years + Stub Period)
   ├── SEBI Statutory KPIs & 18-Month WACA Acquisition Schedule
   ├── NSE / BSE Live Peer Group Quotations (Winsorized Multiples & Growth)
   └── Final Bidding Book (QIB / NII / Retail Subscription + Anchor Book Quality + India VIX)
          │
          ▼
[Stage 2: Domain Feature Engineering & Cross-Sectional Normalization]
   ├── Block 1: Restated Fundamentals & Forensic Accruals (12 features)
   ├── Block 2: Cap Table, Agency & WACA Step-Up Signals (8 features)
   ├── Block 3: De-Biased Valuation & Econometric Spreads (7 features)
   ├── Block 4: Governance, Litigation & FinBERT NLP Density (7 features)
   └── Block 5: Book-Building Demand & Macro Regime Features (6 features)
          │
          ▼
[Stage 3: Expanding-Window Walk-Forward Cross-Validation (Mainboard & SME)]
   ├── Fold 1: Train [FY15–FY20] ──► Validate [FY21] ──► Test [FY22] (Embargo: 180 Days)
   ├── Fold 2: Train [FY15–FY21] ──► Validate [FY22] ──► Test [FY23] (Embargo: 180 Days)
   ├── Fold 3: Train [FY15–FY22] ──► Validate [FY23] ──► Test [FY24] (Embargo: 180 Days)
   └── Fold 4: Train [FY15–FY23] ──► Validate [FY24] ──► Test [FY25–FY26] (Embargo: 180 Days)
          │
          ▼
[Stage 4: Dual-Head Calibrated Inference (LightGBM + CatBoost Ensemble)]
   ├── Head A (Fundamental Quality Score): Pr(BHAR_180D > +10% | Post-Lock-In Outperformance)
   ├── Head B (Pricing & Listing Risk Score): Expected Day-1 Pop % & Day-180 Drawdown Probability
   └── Local SHAP Attribution: Top-5 Positive / Negative Feature Attributions for SEBI Due Diligence
```

---

### 12.2 Complete 40-Feature Engineering Matrix (Across 5 Blocks)

Every feature in the matrix is computable exclusively from disclosures available on or before the final day of bidding ($T_{\text{cutoff}}$), ensuring absolute zero future leakage.

| Block | Feature Name | Formula / Exact Construction | Economic & Econometric Rationale |
| :--- | :--- | :--- | :--- |
| **1. Fundamentals & Forensics** | `rev_cagr_3y` | $(\text{Rev}_{T} / \text{Rev}_{T-2})^{0.5} - 1$ | Measures top-line organic growth velocity across restated Ind AS years. |
| | `ebitda_margin_stub_delta` | $\text{EBITDA\%}_{\text{stub}} - \text{EBITDA\%}_{T-1}$ | Detects pre-DRHP stub-period margin inflation (*window dressing*). |
| | `cfo_to_ebitda_latest` | $\text{CFO}_{T} / \text{EBITDA}_{T}$ | Cash realization quality vs. accrual operating profits. |
| | `cfo_to_ebitda_trend` | $(\text{CFO/EBITDA})_{T} - (\text{CFO/EBITDA})_{T-2}$ | Tracks multi-year working capital deterioration prior to public issue. |
| | `sloan_accrual_ratio` | $(\text{PAT}_T - \text{CFO}_T - \text{CFI}_T) / \text{AvgAssets}_T$ | Captures balance-sheet accrual bloat (Sloan, 1996). |
| | `receivable_days_delta` | $\text{DSO}_T - \text{DSO}_{T-1}$ | Flags channel-stuffing or aggressive credit extensions to bolster pre-IPO sales. |
| | `ronw_latest` | $\text{PAT}_T / \text{NetWorth}_T$ | Primary driver in JRFM (2023) offer-price justification regression. |
| | `roce_latest` | $\text{EBIT}_T / (\text{TotalAssets}_T - \text{CurrentLiabilities}_T)$ | Operating capital efficiency independent of leverage. |
| | `net_debt_to_ebitda` | $(\text{TotalDebt}_T - \text{Cash}_{\text{post-fresh}}) / \text{EBITDA}_T$ | Post-issue balance sheet solvency and debt-clearance capacity. |
| | `other_income_to_pbt` | $\text{OtherIncome}_T / \text{PBT}_T$ | Screens out companies dependent on non-operating gains for net profit. |
| | `asset_turnover_latest` | $\text{Revenue}_T / \text{AverageTotalAssets}_T$ | Asset utilization efficiency and operational intensity. |
| | `working_capital_days` | $(\text{NetWorkingCapital}_T / \text{Revenue}_T) \times 365$ | Operating cycle length and working-capital drag. |
| **2. Cap Table & Agency** | `ofs_ratio` | $\text{OFS Proceeds} / \text{Total Issue Size}$ | Measures insider cash-out vs. primary growth capital (Leland-Pyle). |
| | `promoter_post_hold_pct` | $\text{Post-IPO Promoter Shares} / \text{Total Diluted Shares}$ | Long-term insider alignment and skin in the game. |
| | `waca_stepup_multiple` | $\text{Upper Price Band} / \text{18-Month WACA Acquisition Cost}$ | Quantifies pre-IPO secondary markup over recent private funding cost. |
| | `esop_ccps_dilution_pct` | $(\text{Converted CCPS} + \text{ESOP Overhang}) / \text{Pre-Offer Shares}$ | Measures latent overhang from dilutive instruments pre-listing. |
| | `issue_size_to_networth` | $\text{Total Issue Size} / \text{Pre-IPO Net Worth}$ | Capital raise absorption stress relative to historical equity base. |
| | `board_segment_flag` | Binary: $1 = \text{Mainboard}, \, 0 = \text{NSE Emerge / BSE SME}$ | Controls for SME liquidity, lot-size constraints, and institutional participation. |
| | `pe_backer_reputation_tier` | Ordinal $[0, 3]$: Tier-1 Global/Domestic PE vs. Unbacked | Institutional certification effect and exit pressure profile. |
| | `primary_fresh_issue_share`| $\text{Fresh Issue Capital} / \text{Total Issue Size}$ | Share of capital deployed into capex or debt reduction. |
| **3. Valuation & Comps** | `pe_premium_vs_true_peers` | $(\text{Offer P/E}_{\text{diluted}} / \text{Algo Peer Median P/E}) - 1$ | True valuation spread vs. unbiased semantic peers. |
| | `ev_ebitda_premium_peers` | $(\text{Offer EV/EBITDA} / \text{Algo Peer Median EV/EBITDA}) - 1$ | Capital-structure-neutral multiple premium over industry peers. |
| | `regression_fair_pe_gap` | $(\text{Offer P/E} - \widehat{\text{P/E}}_{\text{Huber}}) / \widehat{\text{P/E}}_{\text{Huber}}$ | Isolates pricing froth after controlling for growth, ROCE, and leverage. |
| | `drhp_peer_bias_index` | $\text{Median P/E}_{\text{DRHP Peers}} / \text{Median P/E}_{\text{Algo Peers}}$ | Quantifies merchant banker peer cherry-picking bias. |
| | `peer_cohort_1y_bhar` | Median 12M post-IPO BHAR of historical sector vintage | Historical post-listing success rate of the sector cohort. |
| | `price_to_book_relative` | $\text{Offer P/B} / \text{Median Peer P/B}$ | Asset-backed valuation ratio comparison. |
| | `ev_sales_premium` | $(\text{Offer EV/Sales} / \text{Algo Peer Median EV/Sales}) - 1$ | Top-line comparative multiple for pre-profit / hyper-growth issuers. |
| **4. Governance & NLP** | `contingent_liab_to_nw` | $\text{Disclosed Contingent Liabilities} / \text{Net Worth}$ | Measures legal, tax, and regulatory balance-sheet tail risk. |
| | `rpt_to_revenue_pct` | $\text{Aggregate RPT Outflows} / \text{Revenue}_T$ | Related-Party Transaction leakage and promoter siphoning risk. |
| | `auditor_change_3y_flag` | Binary: $1$ if statutory auditor resigned within 3 years | Top corporate governance red flag in Indian primary markets. |
| | `promoter_pledge_pct` | $\text{Pledged Promoter Shares} / \text{Total Promoter Shares}$ | Forced-selling vulnerability and promoter balance sheet distress. |
| | `finbert_risk_uncertainty` | Mean FinBERT / DeBERTa uncertainty logit on Risk Factors | Textual ambiguity, litigation complexity, and disclosure opacity. |
| | `top5_customer_conc_pct` | $\text{Top-5 Customer Revenue} / \text{Total Revenue}_T$ | Revenue concentration and counterparty loss vulnerability. |
| | `independent_directors_pct` | $\text{Independent Directors} / \text{Total Board Size}$ | Board oversight compliance and minority shareholder protection. |
| **5. Demand & Macro** | `qib_sub_multiple_log` | $\ln(1 + \text{QIB Oversubscription Multiple})$ | Logarithmic institutional book-building price-discovery signal. |
| | `nii_to_retail_sub_ratio` | $\text{NII/HNI Subscription Multiple} / \text{Retail Sub Multiple}$ | Gauges leveraged HNI speculative fervor relative to organic retail demand. |
| | `anchor_marquee_share` | $\text{Tier-1 Domestic Mutual Funds + SWFs} / \text{Total Anchor Book}$ | Quality, stickiness, and certification of institutional anchor investors. |
| | `india_vix_offer_open` | $\text{India VIX Index level at Bidding Open Date}$ | Broad equity market volatility regime during offer period. |
| | `nifty500_3m_momentum` | $\text{Nifty 500 63-Trading-Day Cumulative Return}$ | Hot vs. cold primary market issuance window timing. |
| | `sme_sentiment_index` | 30-Day Rolling Median Listing Gain across SME issues | SME market liquidity froth and risk appetite indicator. |

---

### 12.3 Walk-Forward Training & Leakage-Prevention Rules

To guarantee institution-grade econometric integrity when deploying this model family, `ProfSurProject` enforces four inviolable engineering constraints:

1. **Strict Temporal Cutoff ($T_{\text{cutoff}}$):**
   All fundamental ratios, restated balance-sheet figures, peer comps, and macroeconomic inputs are frozen strictly at **5:00 PM IST on the final day of the public bidding period** (prior to basis of allotment and secondary market listing). Under no circumstances are post-listing quarterly results, post-allotment announcements, or secondary volume statistics fed into model feature matrices.
2. **Sector-Stratified Winsorization & Scaling:**
   Continuous valuation multiples ($P/E$, $EV/\text{EBITDA}$, $EV/\text{Sales}$) and growth figures are winsorized at the 2.5th and 97.5th percentiles. All imputation medians and scaler statistics are **fit exclusively on the training window of each walk-forward fold** before transforming validation or test cohorts, preventing out-of-sample data leakage.
3. **Embargo Gap (6-Month Horizon Buffer):**
   When predicting 180-day post-lock-in abnormal returns ($\text{BHAR}_{180\text{D}}$), any historical IPO listed fewer than **180 trading days prior to the validation fold boundary** is purged from the training set. This ensures that overlapping future price paths never bleed backward into historical training splits.
4. **SHAP (SHapley Additive exPlanations) Attribution:**
   Every model output surfaces the top-5 positive and top-5 negative SHAP feature attributions directly inside the `ProfSur` analyst interface. This satisfies SEBI Research Analyst transparency requirements, ensuring quantitative buy/avoid recommendations can be audited back to specific root causes (e.g., $\text{OFS Ratio} = 0.82$, $\text{Fair P/E Gap} = +46\%$, $\text{CFO-to-EBITDA Trend} = -34\%$).

---

## Section 13: Comprehensive Academic & Statutory Reference List

1. **Securities and Exchange Board of India (SEBI).** *SEBI (Issue of Capital and Disclosure Requirements) Regulations, 2018 (as amended) & DRHP Public Filings Portal.*  
   [SEBI Filings Portal](https://www.sebi.gov.in/sebiweb/home/HomeAction.do?doListing=yes&sid=3&ssid=15&smid=10)
2. **National Stock Exchange of India (NSE) & BSE India.** *Primary Market IPO Bidding, Anchor Allocation, and Listed Peer Valuation Data Portals.*  
   [NSE India](https://www.nseindia.com/) • [BSE India](https://www.bseindia.com/)
3. **CRISIL Ratings / CRISIL Research.** *CRISIL IPO Grading Methodology: Framework for Assessing Business Prospects, Financial Position, Management Capabilities, and Corporate Governance.*  
   [CRISIL Research IPO Grading](https://www.crisilratings.com/content/dam/crisil/our-businesses/capital-markets/ipo-grading-list/company-name/CRISIL-Research-IPO-grading.html)
4. **Journal of Risk and Financial Management (MDPI, 2023).** *Pre-IPO Financial Performance and Offer Price Estimation: Evidence from India.* Volume 16, Issue 2, Article 135.  
   [MDPI JRFM 2023 Article](https://www.mdpi.com/1911-8074/16/2/135)
5. **Systematic Review on Indian Primary Markets (2023).** *Studies on Indian IPO: Systematic Review and Future Research Agenda* (PRISMA synthesis of 111 empirical studies on Indian IPO underpricing, governance, and long-run performance).  
   [ResearchGate Publication 373948198](https://www.researchgate.net/publication/373948198_Studies_on_Indian_IPO_systematic_review_and_future_research_agenda)
6. **Indian Journal of Finance.** *Grading and Risk-Adjusted Performance of Indian IPOs* (Empirical evaluation of IPO grading impact on post-listing volatility and risk-adjusted returns).  
   [Indian Journal of Finance](https://indianjournaloffinance.co.in/article/grading-and-risk-adjusted-performance-of-indian-ipos/)
7. **European Economic Letters (EELET).** *Does IPO Grading Convey Future Performance? Evidence from Indian IPOs* (Analysis of PBDITA/Total Assets and industry-adjusted operating performance).  
   [EELET Article 3354](https://www.eelet.org.uk/index.php/journal/article/view/3354)
8. **Agrawal, S. & Ananthakumar, U. (SJMSOM, IIT Bombay).** *Predicting IPO Underperformance in Indian Markets Using Machine Learning Techniques* (Comparative evaluation of Gradient Boosting, Random Forest, and financial/sentiment predictors).  
   [Scribd Document 757005109](https://www.scribd.com/document/757005109/Predicting-IPO-underperformance-using-machine-learning)
9. **SSRN Working Paper Series.** *Predicting Ratings of Indian IPOs from Red Herring Prospectus* (Automated textual and quantitative modeling of Indian RHP disclosures).  
   [SSRN Abstract 5217693](https://papers.ssrn.com/sol3/Delivery.cfm/5217693.pdf?abstractid=5217693&mirid=1&type=2)
10. **SSRN Working Paper Series.** *Textual Information and IPO Underpricing: A Machine Learning Approach* (NLP-based measurement of prospectus uncertainty, tone, and abnormal returns).  
    [SSRN Abstract 4963076](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=4963076)
11. **Rock, K. (1986).** *Why new issues are underpriced.* Journal of Financial Economics, 15(1-2), 187-212.
12. **Leland, H. E., & Pyle, D. H. (1977).** *Informational asymmetries, financial structure, and financial intermediation.* The Journal of Finance, 32(2), 371-387.
13. **Welch, I. (1989).** *Seasoned offerings, imitation costs, and the underpricing of initial public offerings.* The Journal of Finance, 44(2), 421-449.
14. **Bhojraj, S., & Lee, C. M. (2002).** *Who is my peer? A valuation-based approach to the selection of comparable firms.* Journal of Accounting Research, 40(2), 415-439.
15. **Damodaran, A. (2024).** *Narrative and Numbers: Valuing High-Growth and Pre-IPO Technology Companies.* Stern School of Business Research Papers.
16. **Estrada, J. (2002).** *Systematic risk in emerging markets: the D-CAPM.* Emerging Markets Review, 3(4), 365-379.
17. **Beneish, M. D. (1999).** *The detection of earnings manipulation.* Financial Analysts Journal, 55(5), 24-36.
18. **Sloan, R. G. (1996).** *Do stock prices fully reflect information in accruals and cash flows about future earnings?* The Accounting Review, 71(3), 289-315.
19. **Ross, G. et al. (2021).** *CapitalVX: A machine learning model for predicting venture capital exits.* MIT / SSRN.

---

## Section 14: Target Module Architecture & Production Roadmap for `ProfSurProject`

To extend `ProfSurProject` from its current verified baseline (513-page HCCH DRHP vertical slice, Ind AS restatements, Dickinson life-cycle mapping, immutable evidence snapshots, and SEBI Reg 26(1) valuation circuit breakers), we map the implementation into clean, test-driven Python modules:

```text
ProfSurProject/
├── models/
│   ├── pre_ipo_dossier_adapter.py        # [Existing] Typed dossier & canonical hash verification
│   ├── pre_ipo_capability_gate.py        # [Existing] Dual-mode gate & Reg 26(1) circuit breaker
│   ├── pre_ipo_nse_client.py             # [NEW] Live NSE session-aware client & peer comps
│   ├── pre_ipo_cohort_trajectory.py      # [NEW] Event-time T_0 peer trajectory & archetype scoring
│   ├── pre_ipo_dual_score_engine.py      # [NEW] Fundamental (CRISIL) & Pricing/Sentiment Scores
│   ├── pre_ipo_anomaly_scanner.py        # [NEW] Window-dressing, CFO/EBITDA & accruals detector
│   ├── pre_ipo_objects_route_scanner.py  # [NEW] Fresh vs. OFS split & SEBI profitability route
│   ├── pre_ipo_lockin_arbitrage.py       # [NEW] Reg 17 6-month lock-in & unlisted LTCG tax model
│   └── pre_ipo_waca_peer_matrix.py       # [NEW] Basis for Issue Price WACA & CMIE peer comps
└── pages/
    └── 27_pre_ipo_drhp.py                # [Existing/Extended] Institutional Due Diligence Tabs
```

This ensures full continuity with our existing immutable database constraints, 4-profile RBAC model, and Cloud Run zero-traffic deployment standards.
