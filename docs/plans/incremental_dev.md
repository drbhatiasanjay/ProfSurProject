# Incremental Development Plan — ProfSurProject v2

**Last updated**: 2026-05-07  
**Current state**: 17 pages, 299 tests, GCP Cloud Run, auth gate (3 roles), SQLite panel 401 firms 2001–2024  
**Phase 1 (Board Deck Export)**: ✅ COMPLETE — 2026-05-07

---

## Feature A — Page 17: Board-Ready Export Pack

### Goal
A CFO or analyst selects any company in the database, chooses which analytical slides to include, and downloads a professional `.pptx` or `.pdf` board deck pre-populated with that company's data, charts, peer benchmarks, and AI-generated recommendations — in under 60 seconds.

---

### User Journey

1. Navigate to **Page 17 — Board Deck Generator** (role: admin + researcher)
2. Select company from dropdown (all 401 Indian firms + US comparators)
3. See a **live snapshot panel** immediately: life stage, leverage, peers count, last data year
4. Choose slides via **topic/sub-topic checklist** (see Slide Catalogue below)
5. Set **scenario inputs** (optional): projected debt raise, target leverage, growth assumption
6. Click **Generate Board Deck**
7. Progress bar while charts render and slides assemble (~15–30 sec)
8. Download `.pptx` and/or `.pdf`

---

### Analysis Catalogue — Individual Company View

**Design principle**: Two distinct use cases in the app.
- **Thesis / Academic**: Panel-wide regressions on all 401 firms. Pages 8–15. Company is one data point.
- **Individual Company**: Single company as the subject, panel as the peer context. Pages 17–18.

All topics below are optional via checkboxes — all pre-selected by default, user unchecks to remove.
Each topic = one or more slides in the export deck AND one section in the Streamlit preview.

Data availability key: ✅ in DB now · ⚡ computed from DB · 🔶 needs additional data

---

#### TOPIC 1 — Executive Summary
*Audience: Board, CEO, all stakeholders. Always included.*

| # | Sub-topic | Data | Type |
|---|---|---|---|
| 1.1 | Cover slide: company, industry, date, life-stage badge | company_name, life_stage | ✅ |
| 1.2 | KPI snapshot grid: leverage, profitability, tangibility, interest coverage, firm size | all key ratios | ✅ |
| 1.3 | 5-year trajectory sparklines: 5 key metrics in one row | financials 5yr | ✅ |
| 1.4 | AI-generated 3-bullet narrative: where we are, vs peers, key action | LLM + model outputs | ⚡ |

---

#### TOPIC 2 — Corporate Life Cycle
*Audience: Board, CFO, Strategy. Unique differentiator — no other tool has this.*

| # | Sub-topic | Data | Type |
|---|---|---|---|
| 2.1 | Current life-stage classification: badge + Dickinson cashflow sign table | life_stage, ncfo, ncfi, ncff | ✅ |
| 2.2 | 24-year stage trajectory: year-by-year stage history (Gantt-style timeline) | life_stage by year | ✅ |
| 2.3 | Time distribution: % of years spent in each stage (pie / bar) | life_stage counts | ✅ |
| 2.4 | Peer cohort: how many of 401 firms are in same stage today, by sector | panel life_stage | ✅ |
| 2.5 | Stage-level capital structure norms: what leverage/profitability looks like at each stage | panel medians by stage | ✅ |
| 2.6 | Transition probability: historical base rates — what stage comes next | transition matrix (page 12 engine) | ⚡ |
| 2.7 | Peer transition paths: how similar firms moved through stages over 10 years | panel stage history | ✅ |

---

#### TOPIC 3 — Capital Structure Profile
*Audience: CFO, Treasurer, Lenders, Rating agencies.*

| # | Sub-topic | Data | Type |
|---|---|---|---|
| 3.1 | Leverage ratio trend: 10-year line vs stage-peer median band | leverage by year + peer quantiles | ✅ |
| 3.2 | Debt composition breakdown: borrowings, debentures, working capital | borrowings, debentures_bonds, total_liabilities | ✅ |
| 3.3 | Equity vs debt evolution: stacked area — reserves + borrowings over time | reserves_and_funds, borrowings | ✅ |
| 3.4 | Interest coverage ratio trend (PBIT / Interest) | pbit, interest_amt | ✅ |
| 3.5 | Effective interest rate trend: interest cost as % of total debt | int_rate, int_rate_lt | ✅ |
| 3.6 | Net debt position: total debt minus cash & liquid investments | borrowings, cash_holdings, st_invest | ✅ |
| 3.7 | Leverage vs size: how leverage evolved as firm grew (size_decile over time) | leverage, firm_size | ✅ |

---

#### TOPIC 4 — Profitability & Earnings
*Audience: CFO, Board, Investors. Pecking Order theory test.*

| # | Sub-topic | Data | Type |
|---|---|---|---|
| 4.1 | Profitability trend: 10-year PBIT margin vs stage-peer median | profitability by year + peer median | ✅ |
| 4.2 | PBIT vs PBT: effect of interest burden on earnings | pbit, pbt | ✅ |
| 4.3 | Profitability percentile: where firm ranks among all 401 firms and stage peers | prof100, peer distribution | ✅ |
| 4.4 | Pecking Order signal: profitability vs leverage scatter — this firm highlighted | profitability, leverage, panel scatter | ✅ |
| 4.5 | Retained earnings proxy: reserves trend as share of total capital | reserves_and_funds, total_capital | ✅ |
| 4.6 | Interest burden: interest_amt as % of PBIT — how much earnings go to debt service | intamt1, pbit1 | ✅ |

---

#### TOPIC 5 — Asset Base & Tangibility
*Audience: CFO, Lenders, Credit analysts. Trade-Off theory test.*

| # | Sub-topic | Data | Type |
|---|---|---|---|
| 5.1 | Tangibility ratio trend: 10-year vs stage-peer median | tangibility by year | ✅ |
| 5.2 | Trade-Off signal: tangibility vs leverage scatter — this firm highlighted | tangibility, leverage | ✅ |
| 5.3 | Asset intensity ranking: tangibility percentile vs peers | tang100 | ✅ |
| 5.4 | Investment activity: NCFI trend — capital-intensive vs asset-light trajectory | ncfi by year | ✅ |
| 5.5 | Collateral coverage estimate: tangible assets vs total borrowings ratio | tangibility × firm_size vs borrowings | ⚡ |

---

#### TOPIC 6 — Cash Flow Analysis
*Audience: CFO, Treasurer, Lenders. Liquidity and Dickinson classification inputs.*

| # | Sub-topic | Data | Type |
|---|---|---|---|
| 6.1 | Three-cashflow dashboard: NCFO / NCFI / NCFF trend (3 lines, 10 years) | ncfo, ncfi, ncff | ✅ |
| 6.2 | Dickinson classification inputs: cashflow sign pattern table by year | ncfo, ncfi, ncff sign | ✅ |
| 6.3 | Operating cashflow vs PBIT: quality of earnings test | ncfo, pbit | ✅ |
| 6.4 | Free cashflow proxy: NCFO − NCFI | ncfo, ncfi | ⚡ |
| 6.5 | Cash holdings trend: cash + bank + liquid investments | cash_holdings, st_invest | ✅ |
| 6.6 | Net cashflow volatility: year-on-year swings (stability indicator) | net_cash_flow | ✅ |

---

#### TOPIC 7 — Tax & Dividend Policy
*Audience: CFO, Tax team, Board.*

| # | Sub-topic | Data | Type |
|---|---|---|---|
| 7.1 | Effective tax rate trend vs sector peers | tax by year + peer median | ✅ |
| 7.2 | Tax shield utilization: tax_shield trend — benefit from interest deductibility | tax_shield | ✅ |
| 7.3 | Dividend policy: payer vs non-payer classification over time | dividend | ✅ |
| 7.4 | Dividend vs leverage: does dividend payment correlate with lower debt? | dividend, leverage | ✅ |
| 7.5 | Tax shield vs peer: is this firm extracting more/less benefit than peers? | tax_shield percentile | ✅ |

---

#### TOPIC 8 — Peer Benchmarking
*Audience: CFO, IR, Board. "How do we compare?"*

| # | Sub-topic | Data | Type |
|---|---|---|---|
| 8.1 | Leverage percentile: box plot — firm vs same-stage peers | leverage distribution | ✅ |
| 8.2 | Multi-variable radar: leverage / profitability / tangibility / tax shield / interest cover vs peer median | all key ratios | ✅ |
| 8.3 | Closest peer table: top 10 peers by stage + sector + size band, with all ratios | panel filtered | ✅ |
| 8.4 | 5-year co-movement: how this firm's leverage moved relative to its cohort median | leverage time series | ✅ |
| 8.5 | Top-quartile benchmark: what the best-performing same-stage peers look like | panel 75th percentile | ✅ |
| 8.6 | Custom peer set builder: user picks specific companies to compare | manual company multiselect | ✅ |

---

#### TOPIC 9 — Capital Structure Optimisation
*Audience: CFO, Board, Investment bankers. "What should we target?"*

| # | Sub-topic | Data | Type |
|---|---|---|---|
| 9.1 | Optimal leverage range: stage-peer 25th–75th percentile band vs current | peer distribution | ✅ |
| 9.2 | Position gauge: under-leveraged / within range / over-leveraged | leverage vs peer band | ✅ |
| 9.3 | Debt headroom: how much additional debt before breaching 75th percentile | peer 75th, current leverage | ✅ |
| 9.4 | Scenario table: ±10% / ±20% / ±30% debt change → leverage + interest cover impact | financials, user inputs | ⚡ |
| 9.5 | Pecking Order vs Trade-Off: which theory fits this company's behaviour? | beta signs from panel OLS | ⚡ |
| 9.6 | Interaction effect: profitability × tangibility — does joint signal apply here? | interaction model results | ⚡ |
| 9.7 | Marginal effect at this stage: dLeverage/dProfitability for this firm's life stage | stage moderation model | ⚡ |

---

#### TOPIC 10 — Forward View & Strategy
*Audience: Board, CFO, Strategy team.*

| # | Sub-topic | Data | Type |
|---|---|---|---|
| 10.1 | Stage transition forecast: probability of moving to each next stage in 1/3/5 years | transition matrix | ⚡ |
| 10.2 | Capital structure at next stage: what leverage norms look like in the projected next stage | panel stage medians | ✅ |
| 10.3 | Peer precedent: firms that moved from same stage — what happened to their leverage | panel stage transitions | ✅ |
| 10.4 | Growth vs debt trade-off: NCFI (investment) vs NCFF (financing) — self-funding capacity | ncfi, ncff | ✅ |
| 10.5 | 3-year leverage target range: where should leverage be if firm moves to next stage | scenario + stage norms | ⚡ |

---

#### TOPIC 11 — Risk & Stress Testing
*Audience: CFO, Risk officer, Lenders, Regulators.*

| # | Sub-topic | Data | Type |
|---|---|---|---|
| 11.1 | Interest coverage stress: coverage at +200bp / +400bp interest rate shock | interest_amt, pbit, int_rate | ⚡ |
| 11.2 | Earnings stress: coverage if PBIT falls 20% / 40% | pbit, interest_amt | ⚡ |
| 11.3 | GFC resilience: how leverage and coverage moved in 2008–09 vs peers | gfc dummy, historical data | ✅ |
| 11.4 | IBC exposure flag: interest coverage < 1.5x in any recent year | ibc_2016, intamt1, pbit | ✅ |
| 11.5 | COVID resilience: 2020–21 leverage and cashflow vs sector peers | covid_dummy | ✅ |
| 11.6 | Leverage volatility: standard deviation of leverage over 10 years (stability score) | leverage time series | ⚡ |
| 11.7 | Distress proximity: Z-score proxy from available ratios | profitability, leverage, cashflow | ⚡ |

---

#### TOPIC 12 — SEBI / Regulatory Compliance
*Audience: Company Secretary, CFO, Compliance officer.*

| # | Sub-topic | Data | Type |
|---|---|---|---|
| 12.1 | Debt/Equity ratio vs SEBI LODR thresholds (sector-specific) | leverage, borrowings, reserves | ⚡ |
| 12.2 | Interest coverage compliance flag: < 1.5x = amber, < 1.0x = red | intamt1, pbit | ✅ |
| 12.3 | Historical compliance status: green/amber/red by year (2001–2024) | computed thresholds | ⚡ |
| 12.4 | Peer compliance comparison: how many same-stage firms are compliant | panel threshold check | ⚡ |

---

#### TOPIC 13 — AI Recommendations
*Audience: CFO, Board. Auto-generated from all model outputs.*

| # | Sub-topic | Data | Type |
|---|---|---|---|
| 13.1 | Capital structure recommendation: 3–5 bullets (LLM + model) | LLM with full context | ⚡ |
| 13.2 | Peer gap analysis: 2–3 bullets on what top-quartile peers do differently | peer comparison | ⚡ |
| 13.3 | Stage-specific risks and opportunities: from interaction effects model | interaction model | ⚡ |
| 13.4 | 3-year roadmap bullets: leverage targets at each projected stage | stage forecasts | ⚡ |

---

### What Needs Additional Data (🔶 Not in DB Yet)

| Data point | Use in catalogue | Source | Effort |
|---|---|---|---|
| SEBI LODR sector thresholds | Topic 12 | SEBI website / manual table | Low (static lookup) |
| Credit rating (if any) | Topic 3, 11 | BSE/NSE filings | Medium |
| Market capitalisation | Topic 5, 9 | NSE/BSE API | Medium |
| Debt maturity schedule | Topic 3 | Annual report | High |
| ESG score | Future | Third-party | High |

Everything else — all 13 topics, 65 sub-topics — is computable from what is **already in the database**.

---

### Technical Architecture

#### New files
```
pages/17_board_export.py      — Streamlit UI (company selector, slide checklist, download)
models/board_export.py        — Slide data builder (SQL → structured dicts per slide)
models/pptx_generator.py      — python-pptx assembly: layout, chart embedding, text boxes
```

#### Core dependencies
```
python-pptx>=0.6.23           — PPTX assembly
kaleido>=0.2.1                — Plotly → PNG static export (required by pptx_generator)
reportlab>=4.0                — Optional: PDF export path
```

#### Slide generation pipeline
```python
# 1. Fetch data
company_profile = db.get_company_profile(company_code)         # name, industry, stage history
panel_data      = db.get_company_financials(company_code)      # leverage, profitability, etc.
peer_data       = db.get_life_stage_peers(company_code)        # peers in same stage
model_outputs   = run_slide_models(panel_data, peer_data)      # OLS + transitions + scenarios

# 2. Build charts (existing helpers)
figs = build_slide_charts(panel_data, peer_data, model_outputs)  # returns dict[slide_id → fig]

# 3. Export charts to PNG (kaleido)
chart_images = {k: fig.to_image(format="png", width=1200, height=600) for k, fig in figs.items()}

# 4. Assemble PPTX
pptx_bytes = pptx_generator.build(company_profile, model_outputs, chart_images, selected_slides)

# 5. Streamlit download
st.download_button("Download .pptx", pptx_bytes, file_name=f"{company_name}_BoardDeck.pptx")
```

#### Data queries needed (new in db.py)
- `get_company_profile(company_code)` — name, industry, inc_year, stage history series
- `get_company_financials(company_code, years=10)` — full row per year, thesis vintage
- `get_life_stage_peers(company_code, n=20)` — same stage + sector + size band firms

#### Access control
- Role: `admin` + `researcher` only (consistent with Workbench/Bulk Upload pattern)
- Audit log: `db.log_page_visit("Board Export")` + log company_code selected

---

## Feature B — Page 18: AI Financial Assistant (Chatbot)

### Goal
An in-app conversational assistant that understands the company data, can answer specific numerical questions ("What is Reliance's leverage trend?"), explain model outputs ("Why did the interaction term come out negative?"), and generate narrative summaries — with a configurable LLM backend that keeps sensitive data private.

---

### User Journey

1. Navigate to **Page 18 — AI Assistant** (role: admin + researcher)
2. Select context mode:
   - **Company Focus**: pick one company → context pre-loaded automatically
   - **Dataset Q&A**: ask questions across all 401 firms
3. Ask questions in the chat interface (natural language)
4. Assistant responds with: numbers pulled from DB + narrative explanation
5. Option: **"Add to board deck"** — appends assistant response as a recommendations slide

Sample questions the assistant should handle:
```
"What is Tata Motors' leverage trend over the last 5 years?"
"Which Growth-stage firms have the lowest leverage in the dataset?"
"Why is the interaction between profitability and tangibility negative?"
"What does it mean that Infosys is in the Maturity stage?"
"Compare Asian Paints' capital structure to its Maturity-stage peers"
"What stage is Wipro likely to be in next year based on historical transitions?"
"Explain the marginal effect of profitability on leverage for Shakeout firms"
```

---

### LLM Backend Architecture

Three configurable backends. User selects in Settings page (or sidebar toggle). Default: Ollama local.

```
┌─────────────────────────────────────────────────────────────────┐
│  STREAMLIT CHAT UI (st.chat_input / st.chat_message)            │
└─────────────────────┬───────────────────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────────────────┐
│  QUERY CLASSIFIER (rule-based, no LLM needed)                   │
│                                                                  │
│  "leverage in 2024"  → SQL_QUERY route                          │
│  "explain why..."   → LLM_ANALYTICAL route                      │
│  "compare X to Y"   → SQL_QUERY + LLM_ANALYTICAL combined       │
└────────┬──────────────────────────┬────────────────────────────-┘
         │                          │
┌────────▼──────────┐   ┌───────────▼────────────────────────────┐
│  SQL EXECUTOR     │   │  CONTEXT BUILDER                        │
│                   │   │                                          │
│  db.py queries    │   │  company_profile (stage, industry)      │
│  → formatted      │   │  + financials (10yr, key ratios)        │
│    answer table   │   │  + peer_summary (medians, percentiles)  │
│                   │   │  + model_outputs (OLS coefficients)      │
│  (no LLM cost)   │   │  → structured text block (~800 tokens)  │
└────────┬──────────┘   └───────────┬────────────────────────────┘
         │                          │
         └──────────┬───────────────┘
                    │
┌───────────────────▼────────────────────────────────────────────┐
│  LLM ADAPTER  (configurable backend)                            │
│                                                                  │
│  Option A: Ollama (LOCAL — recommended for privacy)             │
│    models: llama3.1:8b (default), mistral:7b, qwen2.5:14b      │
│    install: ollama pull llama3.1:8b                             │
│    hardware: 8GB RAM min (8B), 16GB (14B), CPU or GPU          │
│    cost: $0/query, data never leaves machine                    │
│                                                                  │
│  Option B: Claude API (cloud)                                   │
│    model: claude-haiku-4-5 (fast+cheap) or claude-sonnet-4-6   │
│    config: ANTHROPIC_API_KEY in .streamlit/secrets.toml         │
│    cost: ~$0.001–0.003 per query (haiku)                        │
│    data: sent to Anthropic — not for internal CFO data          │
│                                                                  │
│  Option C: OpenAI (cloud)                                       │
│    model: gpt-4o-mini                                           │
│    config: OPENAI_API_KEY in .streamlit/secrets.toml            │
│    cost: ~$0.001 per query                                      │
│    data: sent to OpenAI — not for internal CFO data             │
│                                                                  │
│  Backend switched via: st.session_state["llm_backend"]         │
│  Exposed in Settings page (page 6)                              │
└───────────────────┬────────────────────────────────────────────┘
                    │
┌───────────────────▼───────────────────────────────────────────┐
│  STREAMING OUTPUT  (Streamlit + generator pattern)             │
│                                                                 │
│  for chunk in llm_adapter.stream(messages):                    │
│      st.write_stream(chunk)   ← native Streamlit 1.32+ API    │
└───────────────────────────────────────────────────────────────┘
```

---

### Context Builder — Prompt Template

For a company-focused query, the system prompt injected into every message:

```
You are a financial analyst assistant for ProfSurProject, a capital structure 
analytics platform covering 401 Indian listed companies (2001–2024), based on 
the PhD thesis of Prof. Surendra Kumar (University of Delhi, 2025).

The data uses Dickinson (2011) life-stage classification with 8 stages:
Startup, Growth, Maturity, Shakeout1, Shakeout2, Shakeout3, Decline, Decay.

=== COMPANY CONTEXT ===
Company: {company_name} | Code: {company_code}
Industry: {industry_group}

Life Stage (2024): {current_stage}
Stage History: {stage_history_compact}   # e.g. "Growth(01-08) → Maturity(09-24)"

=== CAPITAL STRUCTURE (last 5 years) ===
Year | Leverage | Profitability | Tangibility | Interest_Cover | Stage
{financials_table_5yr}

=== PEER CONTEXT ===
Peer group: {peer_count} firms in {current_stage} stage
Median leverage: {peer_median_leverage} | This company: {percentile}th percentile
Median profitability: {peer_median_prof} | This company: {prof_percentile}th percentile

=== ECONOMETRIC CONTEXT ===
OLS (pooled, HC1): β(profitability)={beta_prof:.3f} (p={p_prof}), 
                   β(tangibility)={beta_tang:.3f} (p={p_tang})
Interaction term β₃={beta_interaction:.3f} (p={p_int})
Stage marginal effects: {marginal_effects_compact}

Answer questions clearly. Cite specific numbers. When uncertain, say so.
Do not hallucinate financial data outside the context above.
```

---

### New Files

```
pages/18_ai_assistant.py       — Chat UI, context mode selector, LLM backend selector
models/chatbot.py              — Context builder, query classifier, LLM adapter
  └── build_company_context()  — DB → structured text (800 tokens)
  └── classify_query()         — rule-based: SQL vs LLM vs hybrid
  └── LLMAdapter               — wrapper class with .stream() for all 3 backends
  └── execute_sql_query()      — safe read-only SQL execution for numerical questions
```

### New dependencies
```
ollama>=0.2.0                  — Ollama Python client (local backend)
anthropic>=0.25.0              — Already likely installed (Claude API)
openai>=1.30.0                 — OpenAI backend (optional)
litellm>=1.40.0                — Optional: universal LLM wrapper (Ollama + Claude + OpenAI via one API)
```

### Recommended Ollama models (2025 research)
| Model | Size | RAM needed | Best for |
|---|---|---|---|
| `finance-llama:8b` (4-bit) | 5GB on disk | 8GB RAM | Financial narrative, ratio explanations — fine-tuned on financial data |
| `mistral:7b` | 4.1GB | 8GB RAM | Fast general Q&A, good for numerical summaries |
| `qwen2.5:14b` | 9GB | 16GB RAM | Higher quality, better at multi-step reasoning |
| `llama3.1:8b` | 4.7GB | 8GB RAM | Balanced — good default if finance-llama unavailable |

**Hardware reality**: 4-bit quantized 8B models need 8GB RAM minimum, 16GB recommended for large context windows (the 800-token company context + conversation history can push 4K tokens per query).

---

### Privacy Decision Matrix

| Use case | Recommended backend | Why |
|---|---|---|
| PhD research / academic use | Ollama (LLaMA 3.1 8B) | Free, private, good enough for financial narrative |
| Internal CFO team (listed company data) | Ollama or Claude API with DPA | Financial data sensitivity; Ollama = zero data egress |
| Demo / investor pitch | Claude API (Haiku) | Best output quality, fast, cheap for demo use |
| Enterprise / bank deployment | Ollama or self-hosted LLM | Regulatory requirement in banking sector (no cloud LLM for client data) |

---

### Data Privacy Architecture (important for enterprise sales)

**What data leaves the app with Ollama (local):**
- Nothing. LLM runs on the same machine as the app. SQLite data never leaves.

**What data leaves with Claude API / OpenAI:**
- The context block (~800 tokens) containing company name, financial ratios, and model outputs is sent to the API provider per query.
- Mitigations: anonymise company codes (not names) in context; use API data-processing addendums (Anthropic DPA, OpenAI Business).

**Recommended architecture for enterprise:**
- Default backend: Ollama
- Cloud LLM: opt-in only, shown as "Enhanced Analysis (data leaves this server)"
- Audit log: every query logged to `audit_log` table with `llm_backend` field

---

## Implementation Sequencing

### ✅ Phase 1 (COMPLETE — 2026-05-07): Board Deck Export

1. ✅ Add `kaleido` + `python-pptx` to requirements.txt
2. ✅ `db.get_company_peers()` — same-stage + size_decile ±1 peer filter (parsed "Decile N" strings)
3. ✅ `models/board_export.py` — 13 topic builders, all returning {figs, tables, insights, actions, title}
4. ✅ `models/pptx_generator.py` — branded 16:9 slides, teal header, 2-col insights, kaleido PNG embed
5. ✅ `pages/17_board_export.py` — company selector, topic checklist (all pre-selected), preview + download
6. ✅ `tests/test_board_export.py` — 64 tests: contract shape × 13 topics × 3 edge cases + value assertions
7. ✅ All 299 tests passing, zero regressions

### Phase 2 (3–4 days): AI Assistant — Ollama backend first
1. Install Ollama locally: `ollama pull llama3.1:8b`
2. Build `models/chatbot.py` — context builder + Ollama adapter
3. Build `pages/18_ai_assistant.py` — chat UI, company selector, streaming output
4. Add LLM backend selector to Settings page (page 6)
5. Wire `audit_log` for chat queries
6. Tests: `tests/test_chatbot.py` — context builder unit tests (mock LLM)

### Phase 3 (1 day): Claude API + OpenAI backends
1. Add Claude + OpenAI adapters to `models/chatbot.py`
2. Add API key config to `.streamlit/secrets.toml` template
3. Add backend toggle in Settings

### Phase 4 (1 day): Integration
1. "Add to Board Deck" button in chat — appends AI recommendation to session state
2. Page 17 picks up session-state recommendation for Slide 9.1
3. Update CLAUDE.md file structure section

---

## Outstanding Low-Effort Items (carry-forward from EOD 2026-05-07)

| Item | Effort | File |
|---|---|---|
| Reload 8 US firms (fix NULL tangibility) | 1 hr | `models/data_ingest.py` |
| Load MMM (25th US firm) | 30 min | same |
| `plotly_layout()` `legend_override` param | 30 min | `helpers.py` |
| `prepare_panel()` extra_cols documentation | 30 min | `docs/ENGINEERING_PLAYBOOK.md` |
| Unit tests for `run_cross_term_ols` / `run_stage_moderation_ols` | 2 hr | `tests/test_models.py` |
| SEBI LODR Compliance Dashboard (standalone page) | 2 days | `pages/19_compliance.py` |
| Optimal Capital Structure Simulator (extends Scenarios) | 2 days | `pages/3_scenarios.py` enhancement |

---

## Future Phases (post v2)

| Feature | Effort | Commercial value |
|---|---|---|
| REST API layer (Flask/FastAPI) | 1 week | Enterprise integration |
| Multi-company watchlist / portfolio view | 3 days | CFO teams |
| Life-stage transition alerts (email/webhook) | 2 days | Retention / engagement |
| WACC Calculator (CAPM + DDM) | 3 days | Investment analysis |
| ESG capital structure overlay | 1 week | Premium tier |
| Multi-tenant SaaS (per-org DB isolation) | 2 weeks | Commercial scale |
