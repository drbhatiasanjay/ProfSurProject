# Design Architecture Document (DAD)
# LifeCycle Leverage — Modern Institutional UI/UX System Architecture

---

## 1. Architectural System Overview

The UI/UX modernisation is engineered using a **Layered Presentation Adapter Architecture**. The entire visual presentation layer is decoupled from the underlying econometric calculation engines, database connections, and data pipelines.

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                              PRESENTATION LAYER (STREAMLIT)                            │
│                                                                                        │
│  ┌──────────────────────────────────────────────────────────────────────────────────┐  │
│  │ 🌐 Design Token System (assets/style_dark.css & assets/style_light.css)          │  │
│  │ - CSS Variables (:root)  │ Glassmorphism Surfaces │ Typography Hierarchy         │  │
│  └────────────────────────────────────────┬─────────────────────────────────────────┘  │
│                                           │                                            │
│  ┌────────────────────────────────────────▼─────────────────────────────────────────┐  │
│  │ 🧩 Reusable Macro UI Components (helpers.py)                                     │  │
│  │ - render_bento_kpi()     │ render_stage_badge()   │ render_latex_card()          │  │
│  │ - render_citation_pill() │ render_sparkline_svg() │ render_provenance_drawer()   │  │
│  └────────────────────────────────────────┬─────────────────────────────────────────┘  │
│                                           │                                            │
│  ┌────────────────────────────────────────▼─────────────────────────────────────────┐  │
│  │ 📊 Plotly 2.0 Theme Dispatcher (helpers.plotly_layout)                           │  │
│  │ - Transparent Backdrops  │ Translucent Event Ribbons │ High-Contrast Tooltips    │  │
│  └────────────────────────────────────────┬─────────────────────────────────────────┘  │
└───────────────────────────────────────────┼────────────────────────────────────────────┘
                                            │ Pure Read-Only Invocation
┌───────────────────────────────────────────▼────────────────────────────────────────────┐
│                       CORE LOGIC & DATA LAYER (FROZEN & IMMUTABLE)                     │
│                                                                                        │
│  ┌───────────────────────────┐ ┌───────────────────────────┐ ┌──────────────────────┐  │
│  │ db.py                     │ │ models/                   │ │ cmie/                │  │
│  │ SQLite Queries & Caching  │ │ OLS / FE / GMM / SHAP     │ │ Data Transport & Sync│  │
│  └───────────────────────────┘ └───────────────────────────┘ └──────────────────────┘  │
└────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Design Token Specifications & CSS Variables

Design tokens are declared on `:root` and bound dynamically via CSS stylesheet switching (`style_dark.css` vs `style_light.css`):

### 2.1 Color Tokens & CSS Variables

```css
/* ==========================================================================
   Obsidian Slate (Dark Theme Tokens)
   ========================================================================== */
:root[data-theme="dark"] {
    --bg-canvas: #0B0E14;
    --bg-surface: #141824;
    --bg-surface-elevated: #1C2234;
    --bg-glass: rgba(20, 24, 36, 0.75);

    --border-subtle: rgba(255, 255, 255, 0.08);
    --border-focused: rgba(99, 102, 241, 0.5);

    --text-primary: #F8FAFC;
    --text-secondary: #94A3B8;
    --text-muted: #64748B;

    --accent-indigo: #6366F1;
    --accent-cyan: #06B6D4;
    --delta-positive: #10B981;
    --delta-negative: #F43F5E;

    /* Life Stage Semantic Colors */
    --stage-intro: #10B981;
    --stage-growth: #0EA5E9;
    --stage-mature: #8B5CF6;
    --stage-shakeout: #F59E0B;
    --stage-decline: #F43F5E;

    --shadow-elevation: 0 4px 20px -2px rgba(0, 0, 0, 0.45);
    --shadow-glow: 0 0 15px rgba(99, 102, 241, 0.25);
}

/* ==========================================================================
   Alpine Porcelain (Light Theme Tokens)
   ========================================================================== */
:root[data-theme="light"] {
    --bg-canvas: #F8FAFC;
    --bg-surface: #FFFFFF;
    --bg-surface-elevated: #F1F5F9;
    --bg-glass: rgba(255, 255, 255, 0.85);

    --border-subtle: rgba(226, 232, 240, 0.9);
    --border-focused: rgba(79, 70, 229, 0.5);

    --text-primary: #0F172A;
    --text-secondary: #475569;
    --text-muted: #94A3B8;

    --accent-indigo: #4F46E5;
    --accent-cyan: #0891B2;
    --delta-positive: #059669;
    --delta-negative: #E11D48;

    /* Life Stage Semantic Colors */
    --stage-intro: #059669;
    --stage-growth: #0284C7;
    --stage-mature: #7C3AED;
    --stage-shakeout: #D97706;
    --stage-decline: #E11D48;

    --shadow-elevation: 0 4px 16px -2px rgba(0, 0, 0, 0.06);
    --shadow-glow: 0 0 12px rgba(79, 70, 229, 0.15);
}
```

### 2.2 Typography Scale
- **Display & Headings**: `Plus Jakarta Sans`, `Inter`, sans-serif (`font-weight: 600 / 700`).
- **Body & Captions**: `Inter`, system-ui, sans-serif (`font-weight: 400 / 500`).
- **Metrics, P-Values & Formulas**: `JetBrains Mono`, `Fira Code`, monospace with `font-variant-numeric: tabular-nums;`.

---

## 3. Reusable Macro Component Architecture

To maintain code cleanliness and ensure rapid, consistent rendering across all 22 pages, HTML and SVG generators are encapsulated in `helpers.py`.

### 3.1 Bento Stat Capsule (`render_bento_kpi`)
```python
def render_bento_kpi(
    title: str,
    value: str,
    delta: str | None = None,
    sparkline_data: list[float] | None = None,
    percentile: float | None = None,
    tag: str | None = None,
    help_text: str | None = None
) -> str:
    """
    Renders an institutional Bento KPI capsule with an embedded SVG sparkline,
    delta pill, and percentile ranking dial. Returns pure HTML string.
    """
    # 1. Compute inline SVG Polyline from sparkline_data
    # 2. Render glassmorphic card container with tabular monospace value
    # 3. Inject percentile meter bar
```

### 3.2 Stage Status Badge (`render_stage_badge`)
```python
def render_stage_badge(stage: str) -> str:
    """
    Renders an animated glowing badge mapped to corporate life stages
    (Introduction, Growth, Mature, Shakeout, Decline).
    """
```

### 3.3 Clickable Academic Citation Pill (`render_citation_pill`)
```python
def render_citation_pill(author_year: str, paper_key: str) -> str:
    """
    Renders an interactive graduation cap pill [🎓 Rajan & Zingales (1995)].
    Clicking triggers popover containing title, abstract summary, and theory tags.
    """
```

### 3.4 LaTeX Formula Capsule (`render_latex_card`)
```python
def render_latex_card(equation_latex: str, title: str, interpretation: str) -> None:
    """
    Renders a syntax-highlighted econometric formula card with parameter descriptions.
    """
```

---

## 4. Plotly 2.0 Theme Dispatcher Engine

The centralized layout hook `helpers.plotly_layout()` is upgraded to automatically configure chart instances:

```python
def plotly_layout(theme: str = "light", **kwargs) -> dict:
    """
    Returns standard Plotly layout tokens aligned with the active theme.
    """
    is_dark = (theme == "dark")
    return {
        "paper_bgcolor": "rgba(0,0,0,0)",
        "plot_bgcolor": "rgba(0,0,0,0)",
        "font": {
            "family": "Inter, sans-serif",
            "color": "#F8FAFC" if is_dark else "#0F172A",
            "size": 12,
        },
        "xaxis": {
            "gridcolor": "rgba(255,255,255,0.06)" if is_dark else "rgba(0,0,0,0.06)",
            "zerolinecolor": "rgba(255,255,255,0.1)" if is_dark else "rgba(0,0,0,0.1)",
        },
        "yaxis": {
            "gridcolor": "rgba(255,255,255,0.06)" if is_dark else "rgba(0,0,0,0.06)",
            "zerolinecolor": "rgba(255,255,255,0.1)" if is_dark else "rgba(0,0,0,0.1)",
        },
        "hoverlabel": {
            "bgcolor": "#1E293B" if is_dark else "#FFFFFF",
            "bordercolor": "rgba(255,255,255,0.1)" if is_dark else "rgba(0,0,0,0.1)",
            "font": {"family": "Inter, sans-serif", "size": 12},
        },
        **kwargs,
    }
```

### 4.1 Regime Shocks Ribbon Architecture
Instead of opaque blocks, macro event bands (GFC 2008, IBC 2016, COVID 2020) render as **translucent vertical gradients** with clean annotation badges:
- **GFC (2008-09)**: `rgba(244, 63, 94, 0.10)` (Rose tint)
- **IBC (2016+)**: `rgba(14, 165, 233, 0.10)` (Cyan tint)
- **COVID (2020-21)**: `rgba(245, 158, 11, 0.10)` (Amber tint)

---

## 5. AI Financial Assistant (Page 19) Component Architecture

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                              AI ASSISTANT DUAL-PANE RUNTIME                            │
│                                                                                        │
│  ┌───────────────────────────┐  ┌───────────────────────────────────────────────────┐  │
│  │ LEFT RAIL: SESSION ENGINE │  │ MAIN CANVAS: CONVERSATION & ARTIFACTS             │  │
│  │                           │  │                                                   │  │
│  │ • Session SQLite Store    │  │ 1. Stream Assistant Prose (Token Normalizer)      │  │
│  │ • Pinned / Recent List    │  │ 2. Plotly Spec Parser (JSON Extractor)            │  │
│  │ • Active Scope Badge      │  │ 3. LaTeX Equation Box (KaTeX / Streamlit)         │  │
│  │ • Persona Toggle          │  │ 4. Citation Popover Injector (Academic Corpus)    │  │
│  │   (Researcher vs CFO)     │  │ 5. Scoped SQL Provenance Drawer                   │  │
│  │                           │  │ 6. Response Actions (Copy, Save, Retry, Feedback) │  │
│  │                           │  │ 7. Predictive Follow-up Chips                     │  │
│  └───────────────────────────┘  └───────────────────────────────────────────────────┘  │
└────────────────────────────────────────────────────────────────────────────────────────┘
```

### 5.1 SQL Sandbox & Grounding Isolation
To guarantee safety and performance:
1. LLM queries run against a dedicated read-only SQLite view (`v_active_financials`).
2. Hard limits: Max 500 rows, 3-second query execution timeout.
3. Provenance metadata (query string, execution latency, row count) is attached to message payload.

---

## 6. Execution & Verification Phasing

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│ Phase 1: Foundation & Tokens (assets/style_*.css, Theme Switch Icon, helpers.py)       │
│                                      ▼                                                 │
│ Phase 2: Executive Hub & Global Sidebar (0_overview.py, 1_dashboard.py, app.py)       │
│                                      ▼                                                 │
│ Phase 3: AI Assistant Studio (19_ai_assistant.py, Citations, Plotly Chart Generator)   │
│                                      ▼                                                 │
│ Phase 4: Quantitative Lab (8_econometrics.py, 13_advanced.py, 15_interaction.py)       │
│                                      ▼                                                 │
│ Phase 5: Life-Stage Dynamics & Decision Tools (12_transitions.py, 3_scenarios.py, etc) │
│                                      ▼                                                 │
│ Phase 6: Full Regression Test & Verification Gate (All 344+ pytest suites)             │
└────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 7. Zero-Regression Verification Gate

At the conclusion of each phase, the following automated test suite must run and pass with **0 errors**:

```bash
py -3.12 -m pytest tests/ -v
```

This ensures full mathematical reproducibility, database stability, and complete backward compatibility with all historical research assets.
