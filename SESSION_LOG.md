# ProfSurProject — Session Log (2026-03-27)

## What We Did

### 1. Studied the Thesis Document

**File:** `DETERMINANTS OF CAPITAL STRUCTURE OVER CORPORATE LIFE STAGES.docx`

- PhD thesis by **Surendra Kumar**, University of Delhi (2025)
- Supervised by Dr. Varun Dawar & Dr. Chandra Prakash Gupta
- Topic: How capital structure determinants (profitability, tangibility, tax, size, etc.) vary across corporate life stages (Startup → Growth → Maturity → Decline) for Indian firms
- Methods: Panel data — Pooled OLS, Fixed Effects, Random Effects, System GMM
- Theories: Pecking Order, Trade-off, Agency Cost, Signalling, M&M, Free Cash Flow

### 2. Explored the Dataset

**File:** `sp401nf24y_furtherEd_oldCLS.dta` (Stata format)

- **8,677 rows** x **159 columns**
- **401 companies** (S&P BSE/NSE listed Indian corporates)
- **24 years** of panel data (2001–2024)
- **103 industry groups**

**Key variables identified:**

| Variable | Description | Notes |
|----------|-------------|-------|
| `leverage` | Debt ratio (dependent var) | Mean 21%, median 15.8%, outliers up to 1425% |
| `prof` | Profitability | <1% missing |
| `tang` | Asset tangibility | <1% missing |
| `tax` | Tax rate | <1% missing |
| `dvnd` | Dividend payout | 9% missing |
| `size` | Firm size (total assets) | <1% missing |
| `taxShield` | Non-debt tax shield | <1% missing |
| `pmShare` | Promoter shareholding | 15.7% missing |
| `corplifestage` | 8 life stages | Startup, Growth, Maturity, Shakeout1/2/3, Decline, Decay |
| `GFC` | Global Financial Crisis dummy | — |
| `ibc2016` | Insolvency & Bankruptcy Code dummy | — |
| `dcovid20less` | COVID-19 dummy | — |

**Life stage distribution:**

| Stage | Count | Avg Leverage (%) |
|-------|-------|-----------------|
| Maturity | 4,491 | 17.2 |
| Growth | 1,933 | 28.2 |
| Shakeout3 | 947 | 14.1 |
| Startup | 580 | 32.8 |
| Shakeout2 | 353 | 23.4 |
| Decay | 176 | 20.1 |
| Decline | 156 | 38.3 |
| Shakeout1 | 41 | 13.0 |

**Data quality:** ~40+ columns with >50% missing (mostly pledged shares, granular ownership). Core financials are clean (<1% missing).

### 3. Created SQLite Database

**Script:** `load_to_db.py`
**Database:** `capital_structure.db` (4.8 MB)

Normalized the flat 159-column Stata file into 5 relational tables:

| Table | Rows | Content |
|-------|------|---------|
| `companies` | 401 | Company info, NSE symbol, industry, incorporation year |
| `life_stages` | 8 | Life stage code → name mapping |
| `financials` | 8,677 | Leverage, profitability, tangibility, tax, size, cash flows, event dummies |
| `ownership` | 8,677 | Promoter/non-promoter shareholding patterns |
| `market_index` | 24 | Yearly S&P BSE index data (PE, PB, returns, beta) |

**3 pre-built views:**
- `v_company_financials` — joined company + financials + life stage (dashboard-ready)
- `v_life_stage_summary` — metrics aggregated by life stage and year
- `v_industry_summary` — metrics aggregated by industry and year

**6 indexes** for fast querying on company, year, life stage, and composites.

### 4. Saved to Obsidian

Created detailed project note at:
`MySecondBrain/Projects/ProfSurProject/ProfSurProject - Overview.md`

---

# ProfSurProject — Session Log (2026-09-04)

## 1. Milestones Completed & Deployed
1. **Literature Vault in AI Assistant (`pages/19_ai_assistant.py`):**
   - Appended non-destructive, collapsible Peer-Reviewed Literature Vault drawer under conversational chat responses.
   - Grounded responses against 10+ core finance papers (Myers & Majluf 1984, Jensen & Meckling 1976, Rajan & Zingales 1995, IBBI 2022).
2. **Stata Studio Interactive Suite (`pages/08_stata_studio.py`):**
   - Implemented 4-way Chart Switcher (Forest Plot, Beta Bar, Radar, Scatter).
   - Added 3-tier scholarly commentary (Economic Mechanism, Theoretical Assessment, Literature Comparison).
3. **Stata Academic Guide (`pages/24_stata_academic_guide.py`):**
   - Live with full command references and top-level PDF/HTML download button.
4. **Token Optimization & Context Preservation System:**
   - Created root `AGENTS.md` with the **Ponytail Minimal-Code Decision Ladder** and **Concise Engineer Rules**.
   - Streamlined `CLAUDE.md` to save ~1,400 input tokens on every turn.
   - Built unified CLI `scripts/project_ops.py` (`status`, `test --fast`, `push`, `verify`).
   - Built `scripts/gen_bulk_doc.py` to offload bulk HTML/markdown generation to Gemini 1.5 Flash.

## 2. Verified Deployments & Git State
- **Git HEAD:** `e722ca5` (`master` in sync with `origin/master`).
- **Google Cloud Run:** Revision `lifecycle-leverage-00173-jq4` serving 100% traffic at `https://lifecycle-leverage-779655496440.us-east1.run.app`.
- **Test Suite:** 86/86 targeted tests passing (100% green).
- **Default Auth:** `profsurkumar` / `Pass@123`.

## 3. Recommended Next Session Starting Tasks
- [ ] Task A: Enhance **Page 17: Board Deck Export** / **Page 18: Company Navigator**.
- [ ] Task B: Review/extend **`docs/CHART_SWITCHER_ACADEMIC_PROTOTYPE.html`** into additional dashboard views.
- [ ] Task C: Ingest CMIE 2025 rollforward updates via `scripts/project_ops.py`.

---

### 📋 Paste-Ready Handoff Prompt for Next Session:
```text
Resume LifeCycle Leverage project. We are on branch 'master' at commit e722ca5 (100% deployed to GCP). Follow AGENTS.md Ponytail minimal-code and concise rules. Use scripts/project_ops.py for operations. What would you like to build next?
```
