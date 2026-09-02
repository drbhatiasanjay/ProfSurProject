# Product Requirements Document (PRD)
# LifeCycle Leverage — Modern Institutional UI/UX Transformation

---

## 1. Executive Summary & Vision

### 1.1 Product Vision
Transform the **LifeCycle Leverage Dashboard** into a **world-class, institutional-grade quantitative finance and econometric intelligence platform**. The updated platform will combine the visual elegance and fluidity of modern design systems (**Linear, Stripe, Tremor**) with the analytical depth, data density, and rigor required by corporate CFOs and academic researchers (**Bloomberg Terminal, FactSet, OpenBB**).

### 1.2 Core Objectives
1. **Aesthetic Elevation**: Replace standard Streamlit aesthetics with an ultra-refined, dual-theme design system (**Obsidian Slate Dark** and **Alpine Porcelain Light**), utilizing glassmorphism, glowing micro-accents, crisp 1px borders, and tabular financial typography.
2. **Cognitive Streamlining**: Reorganize 22+ multi-page tools into 4 intuitive, domain-driven **Workspaces** to eliminate navigation fatigue.
3. **High-Density Bento Executive HUD**: Introduce interactive Bento Grid metric cards equipped with embedded SVG sparklines, YoY delta pills, and percentile ranking dials.
4. **Plotly 2.0 Visualization Engine**: Modernize 200+ financial charts with translucent regime shock pillars (GFC, IBC, COVID), gradient area fills, and high-contrast tooltips.
5. **AI Research Assistant & In-App Copilot Studio**: Elevate the conversational assistant into an institutional-grade research studio featuring **Financial Stat Bento Capsules**, a **Unified Response Action Dock** (eliminating iframe alignment glitches), **Compact Glowing Follow-Up Action Pills**, **LaTeX Formula Cards**, **Clickable Academic Citations (`🎓`)**, and **Transparent SQL Data Provenance**.
6. **Zero Regression Safety & End-to-End FE/BE Synchronization**: Maintain 100% mathematical and architectural synchronization across all econometric (OLS/FE/RE/GMM), ML (SHAP/XGBoost), database vintage, and UI presentation layers, fully verified by 344+ automated pytest test suites.

---

## 2. Target Personas & Use Cases

| Persona | Primary Goal | Key Features Used |
| :--- | :--- | :--- |
| **Academic Researcher** | Validate PhD thesis econometric models, test capital structure theories, inspect p-values and standard errors. | Econometrics Lab, Advanced GMM, Interaction Effects, Markov Transitions, AI Academic Citations. |
| **CFO / Corporate Treasurer** | Benchmark firm debt capacity against life-stage peers, simulate profitability shocks, prepare board presentations. | Executive Bento HUD, Peer Radar, Capital Structure Simulator (Scenarios), Board Deck Studio (.pptx). |
| **Quantitative Analyst / Data Scientist** | Evaluate ML feature importance, analyze non-linearities, inspect time-series forecasts. | ML Models (SHAP Beeswarm), LSTM/GRU Forecasting, Unsupervised Clustering, Data Explorer. |
| **Executive / Board Director** | High-level synthesis of corporate health, macroeconomic regime impacts, and credit rating trajectories. | Overview, Executive Dashboard, Board Deck Export, AI Copilot Summaries. |

---

## 3. Global Theme & Visual Token System

### 3.1 Theme Architecture & Instant Switcher
* **1-Click Theme Switch Icon**: Pinned directly in the sidebar/header (`☀️ / 🌙`), toggling between Dark and Light mode with zero page reload or state loss.
* **Persistent Preferences**: Theme selection automatically synchronizes with SQLite `user_preferences`.

### 3.2 Design Token Palette
```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│ Obsidian Slate (Dark Theme)                                                           │
│ Background: #0B0E14  │ Panels: #141824  │ Borders: rgba(255,255,255,0.08)              │
│ Primary Accent: #6366F1 (Indigo) │ Secondary Accent: #06B6D4 (Cyan Glow)               │
├────────────────────────────────────────────────────────────────────────────────────────┤
│ Alpine Porcelain (Light Theme)                                                         │
│ Background: #F8FAFC  │ Panels: #FFFFFF  │ Borders: rgba(226,232,240,0.8)               │
│ Primary Accent: #4F46E5 (Indigo) │ Secondary Accent: #0891B2 (Deep Cyan)               │
└────────────────────────────────────────────────────────────────────────────────────────┘
```

### 3.3 Semantic Life-Stage Color Tokens
| Corporate Life Stage | Color Name | Hex Token (Dark / Light) | Semantic Meaning |
| :--- | :--- | :--- | :--- |
| **Introduction** | Emerald / Mint | `#10B981` / `#059669` | Nascent entry, vitality, cash-flow ramp |
| **Growth** | Electric Cyan | `#0EA5E9` / `#0284C7` | High investment, debt expansion |
| **Mature** | Royal Violet | `#8B5CF6` / `#7C3AED` | Peak cash flow, optimal leverage |
| **Shakeout** | Sunburst Amber | `#F59E0B` / `#D97706` | Margin pressure, debt volatility |
| **Decline** | Crimson Rose | `#F43F5E` / `#E11D48` | Contraction, distress risk |

---

## 4. Information Architecture & Navigation

Group the 22 pages into 4 intuitive workspaces:

```
├── 🏛️ WORKSPACE 1: EXECUTIVE & DISCOVERY
│   ├── 00. Overview (Hero metrics, research architecture)
│   ├── 01. Dashboard (Bento Grid, sparklines, regime shocks)
│   ├── 02. Peer Benchmarks (Multi-axial radar & peer positioning)
│   └── 05. Data Explorer (Ag-Grid styled panel table with vintage pills)
│
├── 🔬 WORKSPACE 2: QUANTITATIVE & ECONOMETRICS LAB
│   ├── 08. Econometrics Lab (OLS / FE / RE with Forest plots)
│   ├── 13. Advanced Econometrics (System GMM & COVID resilience)
│   ├── 15. Interaction Effects (3D / Simple slopes & confidence bands)
│   ├── 09. ML Models & Interpretability (SHAP beeswarm & waterfall)
│   ├── 10. Forecasting (LSTM/GRU multi-horizon fan charts)
│   └── 11. Clustering & Validation (K-Means vs Dickinson Sankey)
│
├── 🕸️ WORKSPACE 3: LIFE-STAGE DYNAMICS & KNOWLEDGE GRAPH
│   ├── 20. Life Stage Dynamics (Stickiness & survival analysis)
│   ├── 12. Transitions (Interactive Markov matrix & transition chord)
│   ├── 18. Company Navigator (Obsidian-styled ego-graphs & node drawer)
│   └── 21. Knowledge Graph V2 (OCaml Macro/Meso/Micro semantic zoom)
│
└── 🎯 WORKSPACE 4: DECISION TOOLS & SYSTEM
    ├── 03. Scenarios Simulator (Live What-If HUD & Rating Gauge)
    ├── 17. Board Deck Studio (Interactive slide carousel & high-res export)
    ├── 19. AI Research Assistant (Dual-pane studio, citations, SQL provenance)
    ├── 14. Workbench (Custom query sandbox & plot builder)
    ├── 04. Bulk Upload & CMIE Sync (Drag-and-drop validator)
    └── 16. Activity Log & Settings (Audit timeline & user preferences)
```

---

## 5. Detailed Functional & UI Requirements

### 5.1 Global Sidebar Controls & Top Navbar
* **Glassmorphic Top Navbar**: Background blur (`backdrop-filter: blur(16px)`), neutral ghost sign-out button, active panel badge, and header theme toggle icon (`☀️/🌙`).
* **Dataset Selector**: Capsule widget displaying vintage status badges (`Thesis 2024`, `CMIE 2025`, `US S&P`).
* **Company Fuzzy Search**: High-speed search with 1-click cohort presets (`[Top 10 MegaCap]`, `[Nifty 50]`, `[High Leverage]`).
* **Timeline Scrubber**: Interactive range slider with quick-decade chips (`[2001-2010]`, `[2011-2020]`, `[Post-IBC 2016+]`).
* **Life Stage Filter**: Glowing multi-chip selector with semantic stage colors.
* **Macro Regime Shocks**: Tactile toggle pills for **GFC (2008-09)**, **IBC (2016+)**, and **COVID (2020-21)**.

### 5.2 Bento Grid & Executive KPI Capsules (Page 1)
* Replace standard `st.metric` with multi-attribute Bento capsules:
  1. Primary metric formatted in mono-spaced tabular font.
  2. Micro SVG sparkline showing historical 10-year trajectory.
  3. YoY delta pill with contextual green/red shading.
  4. 100-percentile distribution bar showing relative position in the 401-firm panel.

### 5.3 Plotly 2.0 Visualization Engine
* **Transparent Theme Backdrops**: Seamless integration into container surfaces.
* **Translucent Regime Shock Ribbons**: Shaded event pillars with floating milestone tags.
* **Interactive Tooltips**: Custom HTML tooltips showing company logo, metric breakdown, and peer rank.
* **Tornado / Forest Plots**: For regression coefficients with 95% confidence intervals and significance stars ($^{***}, ^{**}, ^{*}$).
* **Markov Life-Stage Flow**: Sankey / Chord diagrams illustrating 24-year corporate stage migration.

### 5.4 AI Research Assistant & In-App Copilot Studio (Page 19)

#### A. Structured Output & Stat Bento Capsules
* **Financial Stat Bento Cards**: When extracting figures (e.g. `18.8% Leverage in Mature Stage`), the AI response automatically embeds a styled callout capsule containing the metric in tabular monospace font, stage badge (🟣 Mature), and percentile bar.
* **Clickable Grounding Scope Pill**: `[🏷️ Latest (2001-2025) · 401 Firms]` replaces raw bracketed text strings.

#### B. Unified Response Action Dock (Zero-Glitch Alignment)
* Replaces the mismatched HTML iframe button with a **pure CSS/JS Client-Side Action Bar**:
  * `[ 📋 Copy Markdown ]`: Seamless 1-click copy with instant feedback.
  * `[ 💾 Export Report ]`: Downloads response as clean `.md`.
  * `[ 🔄 Regenerate ]`: Reruns query with temperature variance.
  * `[ 👍 Useful ]` / `[ 👎 ]`: Telemetry feedback.
  * **Model Telemetry Badge**: `⚡ Gemini 1.5 Pro · 3.4s · 342 tokens` integrated into the dock edge.

#### C. Compact Glowing Follow-Up Action Pills
* Replaces heavy 40%-height rectangular boxes with **compact, horizontal glowing action pills**:
  * `[ 📊 Compare All 5 Stages ➔ ]`
  * `[ ⚖️ Pecking Order vs Trade-Off ➔ ]`
  * `[ 🏭 Sector Breakdown (Energy vs IT) ➔ ]`
  * 1-Click execution streaming the next turn immediately.

#### D. Left Rail Session Engine & Context Token Gauge
* **Context Capacity Meter**: Dynamic gauge showing memory utilization (`4/6 Turns · 2,410 / 8,000 Tokens`).
* **Categorized Thread List**: Grouped into `📌 Pinned` and `🕒 Recent` with relative timestamps.

#### E. Context-Aware Prompt Cockpit
* Active filter indicator: `[📎 Active Filters: Energy · 2001-2025]`.
* Dedicated toggle for `[🎓 Academic Citations: ON]`.

---

## 6. Skills, Plugins, MCPs & GitHub Reference Tools

### 6.1 Agent Skills
* **`frontend-design`**: Layout rhythm, optical spacing, responsive grid hierarchies.
* **`ui-tokens`**: Design token architecture and CSS variable synchronization.
* **`ui-pattern`**: Reusable component macros (Bento cards, stage chips, action docks).
* **`design-spells`**: Micro-interactions, tactile hover glows, and button press feedback.
* **`animejs-animation`**: Smooth transitions, gauge meters, and number count-ups.
* **`shadcn` / `radix-ui-design-system`**: Design system tokens and accessible popovers.

### 6.2 MCP Tools
* **`codebase-memory-mcp`**: Knowledge graph call-path tracing (`trace_call_path`) to guarantee zero broken dependencies during UI injection.
* **`visualization` MCP**: Rapid testing and validation of upgraded Plotly chart specifications.

### 6.3 GitHub Repositories & Design Systems for Inspiration
* **[Tremor](https://github.com/tremorlabs/tremor)** (`tremorlabs/tremor`): Financial KPI cards, sparklines, badge deltas, and bento dashboards.
* **[shadcn/ui](https://github.com/shadcn-ui/ui)** (`shadcn-ui/ui`): Minimalist borders, typography scale, and focus rings.
* **[Linear App](https://linear.app)**: Translucent glassmorphism, 1px subtle borders, dark mode depth.
* **[OpenBB Terminal](https://github.com/OpenBB-finance/OpenBBTerminal)**: High-density quantitative financial analytics and regime markers.
* **[Stripe Dashboard](https://stripe.com)**: Clean light mode, micro-charts, and high legibility.

---

## 7. Safety, Guardrails & Non-Functional Requirements

### 7.1 Separation of Concerns (SoC) Architectural Guardrail
```
┌────────────────────────────────────────────────────────────────────────┐
│  🎨 UI Presentation Layer (Enhanced)                                   │
│  - assets/style_light.css & assets/style_dark.css                      │
│  - helpers.py HTML/SVG Component Renderers                             │
│  - helpers.plotly_layout Theme Dispatcher                             │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │ Pure Read-Only Invocation
┌───────────────────────────────────▼────────────────────────────────────┐
│  🔒 Core Logic & Data Engine (FROZEN & IMMUTABLE)                      │
│  - db.py (SQL queries, vintage filtering, schema)                     │
│  - models/ (econometric, ML, forecasting, scenario calculations)      │
│  - cmie/ (transport pipelines, rate limits, token buckets)             │
│  - Reproducibility Pins (panel_mode='thesis' in Scenarios/Econometrics)│
└────────────────────────────────────────────────────────────────────────┘
```

### 7.2 Non-Functional Requirements
1. **Performance**: Page switch latency $< 200\text{ms}$; Bento card render time $< 50\text{ms}$.
2. **Accessibility (WCAG 2.1 AA)**: Minimum contrast ratio of $4.5:1$ for all text elements in both light and dark modes.
3. **Reproducibility**: Statistical coefficients, degrees of freedom, and p-values must remain 100% identical to thesis figures.
4. **Test Gate**: All 344+ automated tests in `tests/` must pass unconditionally with 0 failures:
   ```bash
   py -3.12 -m pytest tests/ -v
   ```

---

## 8. Frontend-to-Backend (FE/BE) Synchronization Matrix

```
┌─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                       FE / BE END-TO-END SYNCHRONIZATION PIPELINE                                           │
├─────────────────────────┬───────────────────────────────┬───────────────────────────────┬───────────────────────────────────┤
│ UI Component (Frontend) │ Backend Anchor / Source       │ Data Transformation Adapter   │ Synchronization & Guardrail Flow  │
├─────────────────────────┼───────────────────────────────┼───────────────────────────────┼───────────────────────────────────┤
│ 1. Bento Stat Capsules  │ db.get_active_financials(ft)  │ helpers.render_bento_kpi()    │ • In-memory Sparkline Polyline    │
│    (Sparklines, Delta,  │ Pandas DataFrame with 24-yr   │ In-memory groupby('year') and │   computed via Pandas aggregation │
│    Percentile Dial)     │ panel metrics                 │ scipy.stats.percentileofscore │ • Zero SQL roundtrips added       │
├─────────────────────────┼───────────────────────────────┼───────────────────────────────┼───────────────────────────────────┤
│ 2. Theme Quick-Switcher │ db.save_user_pref() /         │ st.session_state["theme"]     │ • Idempotent SQLite preference    │
│    (☀️ Light / 🌙 Dark) │ db.load_user_prefs()          │ Instant CSS :root swap        │   save; zero cache eviction       │
├─────────────────────────┼───────────────────────────────┼───────────────────────────────┼───────────────────────────────────┤
│ 3. Global Filter Bar    │ db.filters_to_tuple()         │ st.session_state.filters      │ • Session state keys preserved;   │
│    (Fuzzy Search, Chips)│ db.get_companies()            │ Exact SQL filter predicate    │   SQL query cache keys untouched  │
├─────────────────────────┼───────────────────────────────┼───────────────────────────────┼───────────────────────────────────┤
│ 4. Plotly 2.0 Engine    │ helpers.plotly_layout()       │ helpers.event_bands()         │ • Pure JSON layout schema update; │
│    (Ribbons, Forest)    │ models.econometric (b_se, pval│ Dynamic trace generator       │   underlying data arrays unmutated│
├─────────────────────────┼───────────────────────────────┼───────────────────────────────┼───────────────────────────────────┤
│ 5. AI Copilot Studio    │ models.llm_adapters           │ models.agent_tools            │ • Read-only SQL view sandbox;     │
│    (LaTeX, Citations,   │ db.list_chat_sessions()       │ SQL execution wrapper with    │   provenance telemetry attached to│
│    SQL Provenance)      │ db.save_chat_message()        │ latency & row-count metadata  │   chat payload schema             │
├─────────────────────────┼───────────────────────────────┼───────────────────────────────┼───────────────────────────────────┤
│ 6. Capital Simulator    │ models.scenario_regression    │ predict_scenario_leverage()   │ • Input slider bounds validated;  │
│    (Cockpit & Gauges)   │ (Pure OLS helper functions)   │ compute_normative_band()      │   tested via test_scenario_reg.py │
├─────────────────────────┼───────────────────────────────┼───────────────────────────────┼───────────────────────────────────┤
│ 7. Board Deck Studio    │ models.board_export           │ models.pptx_generator         │ • HTML slide thumbnail preview;   │
│    (Slide Deck Preview) │ 13 topic builder functions    │ Kaleido Plotly→PNG→PPTX       │   PPTX generator pipeline intact  │
├─────────────────────────┼───────────────────────────────┼───────────────────────────────┼───────────────────────────────────┤
│ 8. OCaml Knowledge Graph│ graph_bridge.py               │ json.loads()                  │ • Macro/Meso/Micro JSON contract  │
│    (Semantic Zoom)      │ lifecycle-ontology HTTP / stub│ Tree hierarchy adapter        │   adheres to test_kg2_bridge.py   │
└─────────────────────────┴───────────────────────────────┴───────────────────────────────┴───────────────────────────────────┘
```

---

## 9. Acceptance Criteria & Verification Matrix

| Area | Acceptance Criteria | Verification Method |
| :--- | :--- | :--- |
| **Theme Switcher** | 1-click icon switch toggles theme instantly across all 22 pages without page reload or filter loss. | Browser test + verify `user_preferences` table. |
| **Bento Grid** | KPI cards render SVG sparklines, YoY deltas, and percentile meters with zero computation lag. | Visual verification on `1_dashboard.py`. |
| **Chart Styling** | Transparent backdrops, custom tooltips, and regime ribbons render across all Plotly figures. | Visual check on Pages 1, 2, 8, 12, 15. |
| **AI Copilot** | LaTeX cards, interactive Plotly charts, citation popovers, Action Dock, and SQL provenance render reliably. | Multi-turn testing on `19_ai_assistant.py`. |
| **FE/BE Sync** | Data transformations execute in-memory; 0 regressions in DB cache hits or model outputs. | End-to-end integration tests in `tests/test_page_integration.py`. |
| **Zero Regression** | 344+ unit/integration tests pass with 100% success rate. | Automated CI / Pytest execution (`pytest tests/ -v`). |
