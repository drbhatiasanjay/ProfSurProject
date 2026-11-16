# Findings & Technical Discoveries: Pre-IPO Terminal v3.5.0

## Ground Truth Data Points & Constants
- **Hindustan Coca-Cola Holdings Ltd. (HCCH):**
  - Filing: DRHP October 2026 (513 physical pages)
  - Offering Structure: 100% OFS, 0% Fresh Issue
  - Exact Legal Share Count: `997,461,456 Equity Shares`
  - Indicative Price: `₹[●] Undisclosed` (Estimated value ₹9,975.00 Cr at ~₹100/sh)
  - Dickinson Life-Cycle Stage: `MATURE (CASH COW) (+, -, -)` (Operating CFO positive, Investing CFI negative, Financing CFF negative)
  - FY24 Actuals: Revenue ₹14,021.5 Cr, EBITDA ₹1,895.7 Cr, PAT ₹2,812.1 Cr, Bank Debt ₹0.0 Cr
  - Beneish M-Score: `-2.48` (Low probability of earnings manipulation)
  - BRLM Syndicate: Kotak Mahindra Capital, Citigroup Global Markets, Morgan Stanley India, J.P. Morgan India
- **NTPC Green Energy Limited (NGEL):**
  - Filing: RHP November 2024
  - Route: Regulation 6(2) 75% QIB Book Building
  - Price Band: ₹102 - ₹108 per share
  - Market Lot: 138 shares (Min ₹14,904 commitment)
  - Issue Size: ₹10,000.00 Cr (100% Fresh Issue, 0% OFS)
  - Huber Fair P/E: 146.1x vs Asking P/E 2349.7x (Froth Gap: +1508.8% / +2203.7x P/E)
- **Varun Beverages (VBL) Benchmark:**
  - 15-Year Life Cycle: FY11–FY25
  - Multiple Compression: De-rated from 56.7x to 42.2x despite delivering 23.2% CAGR and 23.4% EBITDA margins.
  - Mueller ROCE Persistence: $\lambda = 0.74$, Half-life $2.3\text{ years}$.
- **Seasonality Reality:**
  - Q1 (Summer beverage) accounts for 34.5% of annual revenue and 46.0% of annual EBITDA.
  - Naive $4\times$ annualization of Q1 overstates full-year earnings by ~47%.

## Master Guide Audit (Adopted vs. Non-Adopted)
| Category | Adopted (17 Items) | Non-Adopted (8 Items) & Why |
| :--- | :--- | :--- |
| **Architecture** | Option A Dual-Layer Cockpit & Vault (38/62 split) | Full client PDF.js 85MB canvas (RAM bloat / lag) |
| **Ingestion** | Decoupled backend batch workers + FastMCP tools | In-browser live Playwright scraping (CORS/ban risk) |
| **Modeling** | Huber $M$-estimator ($t=1.345$), Dual-Score, Quantiles | Local 70B parameter LLM fine-tuning (Rule 4 violation) |
| **Red Flags** | 6-Rule Radar (FLAG-01 to 06), Sloan Accrual, Beneish | Monolithic 42-field flat table (cognitive doom-scroll) |
| **Arbitrage** | Sec 56(2)(x) FMV tax drag, 6M carry cost, breakeven | Outbound FIX protocol broker trading (SEBI boundary) |
| **UI/UX** | Tri-state counters, dashed RHP cell borders, slider | Automated algorithmic order placement (Broker status needed) |
| **Governance** | 1-Click PPTX/PDF exports, 4-pillar narrative drawers | Synthetic proxy imputation for unlisted peers (fraud risk) |

## Root Causes of Past Errors & Preventative Fixes
1. **Premature Completion Confirmation:** Checked HTTP 200 rather than visual page elements. Fixed by requiring verified physical `.png` screenshots on disk via Playwright.
2. **String Replacement Delimiters:** Orphaned code in `api/server.py`. Fixed by running `py_compile` after every edit.
3. **PowerShell Multi-line Delimiters:** Running inline `-c` scripts with quotes/LaTeX `$`. Fixed by writing standalone `.py` scripts.
4. **Financial Truthiness Bugs:** Writing `val or default` which treated valid $0.0$ debt as missing. Fixed by enforcing explicit presence checks (`if val is None:` and `val !== null && val !== undefined`).
5. **Unpriced DRHP Crashes:** Missing price bands causing `NaN`. Fixed by building typed `is_undisclosed` branch logic.
