# Master Test Strategy & Verification Plan
# LifeCycle Leverage — Modern UI/UX Transformation & Zero-Regression Quality Gates

---

## 1. Executive Summary & Objective

The objective of this Test Plan is to guarantee **100% mathematical integrity, zero regression across 24-year econometric panel models, and seamless end-to-end frontend/backend synchronization** during the LifeCycle Leverage UI/UX modernization.

### Test Governance Principles
1. **Zero Regression Baseline**: All 344+ existing pytest tests in `tests/` must remain green across every phase.
2. **Layered Quality Gates**: No UI component or macro helper is merged without unit, integration, and visual verification.
3. **Decoupled Verification**: Presentation formatting tests are strictly decoupled from core econometrics, database queries, and ML calculations.

---

## 2. Test Architecture & Coverage Matrix

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                                 TEST SUITE HIERARCHY                                   │
├────────────────────────────────────────────────────────────────────────────────────────┤
│ 1. Core Econometric & DB Regression Suite (Existing 344+ Tests)                        │
│    - tests/test_database.py           │ tests/test_models.py                           │
│    - tests/test_cmie_*.py (7 suites)  │ tests/test_scenario_regression.py              │
│    - tests/test_board_export.py       │ tests/test_covid_cohorts.py                    │
├────────────────────────────────────────────────────────────────────────────────────────┤
│ 2. New UI Presentation & Token Test Suite (Phase-wise Additions)                       │
│    - tests/test_ui_theme_tokens.py    (CSS Variables, Navbar & Theme Persistence)      │
│    - tests/test_bento_components.py   (Bento KPI, SVG Sparklines, Percentile Dials)    │
│    - tests/test_plotly_dispatcher.py  (Plotly 2.0 Layouts, Regime Shock Ribbons)       │
│    - tests/test_ai_copilot_canvas.py  (Action Dock, Stat Bento, Citations, SQL Prov)   │
├────────────────────────────────────────────────────────────────────────────────────────┤
│ 3. Page Integration & End-to-End Pipeline Suite                                        │
│    - tests/test_page_integration.py   (Data pipeline & rendering across all 22 pages)  │
│    - tests/e2e_full.py                (End-to-end session & multi-panel workflows)     │
└────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 3. Detailed Test Suites & Verification Specifications

### Suite 1: Theme Engine & CSS Design Tokens (`tests/test_ui_theme_tokens.py`)
* **Objective**: Verify that dark/light themes render correctly, `:root` CSS variables are syntactically valid, and preferences persist in SQLite without cache eviction.
* **Test Cases**:
  1. `test_css_files_exist_and_non_empty()`: Asserts `assets/style_dark.css` and `assets/style_light.css` exist and have non-zero file sizes.
  2. `test_css_token_variable_coverage()`: Inspects stylesheets for required tokens (`--bg-canvas`, `--bg-surface`, `--text-primary`, `--stage-intro`, `--stage-mature`, `--delta-positive`).
  3. `test_theme_user_preference_persistence()`: Simulates setting theme to `dark` and `light` via `db.save_user_pref()` and verifies `db.load_user_prefs()` retrieves the exact state.
  4. `test_theme_switch_session_state_idempotence()`: Verifies that toggling `st.session_state.theme` does not invalidate `@st.cache_data` caches in `db.py`.

---

### Suite 2: Bento Stat Capsules & Micro SVG Helpers (`tests/test_bento_components.py`)
* **Objective**: Verify HTML and SVG polyline generation for the high-density Bento Grid.
* **Test Cases**:
  1. `test_sparkline_svg_generation()`:
     * Inputs: `[10.2, 12.4, 15.1, 14.8, 18.2, 22.0]`.
     * Asserts: Returns `<svg class="sparkline-svg"><polyline points="..." /></svg>`.
     * Asserts: Coordinates scale within the $0 \le x \le 240$ and $0 \le y \le 36$ bounding box.
     * Asserts: Gracefully handles empty lists or single-element inputs without zero-division errors.
  2. `test_bento_kpi_card_html_output()`:
     * Inputs: `title="Avg Leverage"`, `value="34.2%"`, `delta="+1.4pp"`, `percentile=72.0`.
     * Asserts: Contains tabular monospace styling, delta class `delta-up`, and percentile fill width `72%`.
  3. `test_stage_badge_semantic_colors()`:
     * Validates that `render_stage_badge(stage)` maps Introduction $\rightarrow$ `#10B981`, Growth $\rightarrow$ `#0EA5E9`, Mature $\rightarrow$ `#8B5CF6`, Shakeout $\rightarrow$ `#F59E0B`, Decline $\rightarrow$ `#F43F5E`.
  4. `test_xss_sanitization_in_card_renderers()`:
     * Injects malicious strings (e.g. `<script>alert(1)</script>`) into company titles or labels and verifies output is HTML-escaped.

---

### Suite 3: Plotly 2.0 Theme Dispatcher & Regime Ribbons (`tests/test_plotly_dispatcher.py`)
* **Objective**: Validate Plotly figure styling, transparent backdrops, and non-destructive regime shock ribbon overlays.
* **Test Cases**:
  1. `test_plotly_layout_dark_theme()`:
     * Invokes `plotly_layout(theme="dark")`.
     * Asserts: `paper_bgcolor == "rgba(0,0,0,0)"`, `plot_bgcolor == "rgba(0,0,0,0)"`, and font color is light slate (`#F8FAFC`).
  2. `test_plotly_layout_light_theme()`:
     * Invokes `plotly_layout(theme="light")`.
     * Asserts: Font color is dark slate (`#0F172A`) and grid lines are subtle.
  3. `test_regime_shock_event_bands_injection()`:
     * Creates a dummy Plotly line figure.
     * Passes figure to `helpers.event_bands(fig, events={"gfc": True, "ibc": True, "covid": True})`.
     * Asserts: Injects 3 translucent `vrect` shapes corresponding to 2008-09, 2016-2025, and 2020-21 without removing existing data traces.
  4. `test_forest_plot_trace_generation()`:
     * Passes mock OLS/FE results (`params`, `b_se`, `pvalues`) to the forest plot helper and verifies error bar whiskers ($95\%\text{ CI} = \beta \pm 1.96 \cdot \text{SE}$) are mathematically exact.

---

### Suite 4: AI Financial Assistant Studio & Citations (`tests/test_ai_copilot_canvas.py`)
* **Objective**: Validate LaTeX formula cards, academic citation popovers, SQL provenance metadata, Action Dock, Stat Bento Capsules, and multi-turn session persistence.
* **Test Cases**:
  1. `test_chatbot_stat_bento_capsule_extraction()`:
     * Tests that responses mentioning stats (e.g., `18.789% Mature Stage`) generate a structured Bento capsule with tabular monospace font and stage badge.
  2. `test_chatbot_action_dock_alignment_and_copy_payload()`:
     * Verifies that the client-side clipboard Copy payload produces valid base64-encoded strings and does not create iframe visual misalignment with `Save`, `Retry`, and `Helpful`.
  3. `test_followup_action_pills_compact_rendering()`:
     * Verifies that `_FALLBACK_CHIPS` and LLM `FOLLOWUPS_JSON` render as compact, glowing horizontal action pills ($< 38\text{px}$ height) rather than tall rectangular boxes.
  4. `test_context_token_gauge_calculation()`:
     * Supplies conversation turns and verifies token/turn count calculation (`4/6 Turns · 2,410 Tokens`).
  5. `test_academic_citations_corpus_lookup()`:
     * Verifies that `helpers.ACADEMIC_CITATIONS_CORPUS` contains entries for `rajan_zingales_1995`, `myers_1984`, `dickinson_2011`, `jensen_meckling_1976`.
     * Asserts that `render_citation_pill()` produces valid popover trigger HTML.
  6. `test_sql_provenance_envelope()`:
     * Verifies that database tool calls attach `execution_time_ms`, `row_count`, and `sql_query` to message metadata without leaking write operations.

---

### Suite 5: Page Integration & End-to-End Pipeline (`tests/test_page_integration.py`)
* **Objective**: Ensure that all 22 pages load, prepare panel data, and execute downstream models without error across all 4 dataset vintages (`thesis`, `latest`, `run3`, `us_av_2024`).
* **Test Coverage**:
  * **Page 0 (Overview)**: Metric counts, research metadata.
  * **Page 1 (Dashboard)**: Bento cards, ANOVA stage tests, Figure 5.1/5.2 aggregations, Table 5.9 synthesis.
  * **Page 2 (Peer Benchmarks)**: Company radar calculations, quartile distribution bounds.
  * **Page 3 (Scenarios)**: OLS scenario prediction math, normative band bounds.
  * **Page 5 (Data Explorer)**: Column schema validation, vintage tags.
  * **Page 8 (Econometrics)**: OLS, Within-FE, GLS-RE, Hausman test statistic ($p < 0.0001$).
  * **Page 9 (ML Models)**: Random Forest, XGBoost, LightGBM inference, SHAP summary values.
  * **Page 10 (Forecasting)**: LSTM/GRU sequence generation.
  * **Page 12 (Transitions)**: Markov transition matrix row-stochasticity ($\sum_j P_{ij} = 1.0$).
  * **Page 13 (Advanced Econometrics)**: Two-step System GMM, Arellano-Bond AR(1)/AR(2), Hansen test.
  * **Page 15 (Interaction Effects)**: Cross-term $\text{Prof} \times \text{Tang}$ OLS and simple slopes.
  * **Page 17 (Board Export)**: 13 topic builders output valid figures and tables.
  * **Page 18 & 21 (Knowledge Graph V1/V2)**: Graph bridge contract adherence and ego-graph node counts.

---

## 4. Performance & Latency Benchmarks

| Metric / Action | Maximum Allowed Threshold | Verification Method |
| :--- | :--- | :--- |
| **Bento Stat Capsule Render** | $< 50\text{ms}$ | Microsecond timer in `test_bento_components.py` |
| **Plotly Theme Layout Dispatch**| $< 10\text{ms}$ | Profiler benchmark in `test_plotly_dispatcher.py` |
| **Page Switch Latency** | $< 200\text{ms}$ | Playwright / Streamlit runner benchmark |
| **Theme Toggle CSS Swap** | $< 16\text{ms}$ (1 Frame @ 60fps) | Headless browser DOM transition timing |
| **Full Pytest Suite Run (350+ Tests)** | $< 45\text{s}$ | CI runner execution time |

---

## 5. Execution Workflow & CI Quality Gates

```
┌────────────────────────────────────────────────────────────────────────┐
│                              CI QUALITY GATE                           │
├────────────────────────────────────────────────────────────────────────┤
│ Step 1: Static Analysis & Linting                                      │
│         ruff check . && ruff format --check .                          │
│                                                                        │
│ Step 2: Unit & Macro Component Tests                                   │
│         pytest tests/test_ui_theme_tokens.py                           │
│         pytest tests/test_bento_components.py                          │
│         pytest tests/test_plotly_dispatcher.py                         │
│         pytest tests/test_ai_copilot_canvas.py                         │
│                                                                        │
│ Step 3: Econometric & Machine Learning Model Regression Suite          │
│         pytest tests/test_models.py                                    │
│         pytest tests/test_scenario_regression.py                       │
│         pytest tests/test_covid_cohorts.py                             │
│                                                                        │
│ Step 4: Full End-to-End Page Integration Gate (350+ Tests)             │
│         pytest tests/ -v                                               │
│         [PASS REQUIREMENT: 100% Passed, 0 Failures, 0 Regressions]     │
└────────────────────────────────────────────────────────────────────────┘
```
