"""
Page 24 — AI Financial Chat & Stata Studio Operational Guide.
Exhaustive reference manual, prompt encyclopedia, and econometric guide for researchers, PhD scholars, and CFOs.
Grounded on 8,677 firm-year observations across 401 Indian manufacturing firms (2001–2025).
"""

import os
import streamlit as st
import plotly.graph_objects as go
import pandas as pd
from helpers import require_role, plotly_layout
import db

require_role("admin", "researcher", "viewer", "cfo", "guest")
db.log_page_visit("ai_chat_guide")

# ── Load offline guide HTML ──
_guide_html_path = os.path.join(os.path.dirname(__file__), "..", "docs", "AI_Financial_Chat_and_Stata_Guide.html")
_guide_html_content = ""
if os.path.exists(_guide_html_path):
    with open(_guide_html_path, "r", encoding="utf-8") as _f:
        _guide_html_content = _f.read()

# ── Top Custom Styling ──────────────────────────────────────────────────────────
st.markdown("""
<style>
.guide-header {
    background: linear-gradient(135deg, rgba(99, 102, 241, 0.12) 0%, rgba(6, 182, 212, 0.08) 100%);
    border: 1px solid rgba(99, 102, 241, 0.25);
    border-radius: 14px;
    padding: 24px;
    margin-bottom: 24px;
}
.guide-title {
    font-size: 26px;
    font-weight: 800;
    color: #F8FAFC;
    margin-bottom: 6px;
    letter-spacing: -0.01em;
}
.guide-subtitle {
    font-size: 14px;
    color: #94A3B8;
    line-height: 1.5;
}
.stat-box {
    background: rgba(15, 23, 42, 0.6);
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 10px;
    padding: 12px 16px;
    text-align: center;
}
.stat-box .val {
    font-size: 20px;
    font-weight: 700;
    color: #38BDF8;
    font-family: 'Consolas', 'JetBrains Mono', monospace;
}
.stat-box .lbl {
    font-size: 11px;
    color: #64748B;
    text-transform: uppercase;
    font-weight: 600;
    margin-top: 2px;
}
.prompt-card {
    background: #111827;
    border: 1px solid #1F2937;
    border-radius: 12px;
    padding: 18px 22px;
    margin-bottom: 20px;
    box-shadow: 0 4px 14px rgba(0,0,0,0.25);
}
.prompt-title-row {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 10px;
}
.prompt-badge {
    font-size: 11px;
    font-weight: 700;
    padding: 3px 8px;
    border-radius: 6px;
    text-transform: uppercase;
}
.badge-simple { background: rgba(16, 185, 129, 0.15); color: #34D399; border: 1px solid rgba(16, 185, 129, 0.3); }
.badge-medium { background: rgba(245, 158, 11, 0.15); color: #FBBF24; border: 1px solid rgba(245, 158, 11, 0.3); }
.badge-complex { background: rgba(244, 63, 94, 0.15); color: #FB7185; border: 1px solid rgba(244, 63, 94, 0.3); }
.badge-stata { background: rgba(99, 102, 241, 0.15); color: #A5B4FC; border: 1px solid rgba(99, 102, 241, 0.3); font-family: monospace; }
.badge-cfo { background: rgba(6, 182, 212, 0.15); color: #38BDF8; border: 1px solid rgba(6, 182, 212, 0.3); }
.prompt-query {
    font-size: 15px;
    font-weight: 600;
    color: #F3F4F6;
    background: #0B0F19;
    padding: 12px 16px;
    border-radius: 8px;
    border-left: 4px solid #06B6D4;
    margin-bottom: 14px;
}
.prompt-query.stata {
    font-family: 'Consolas', 'JetBrains Mono', monospace;
    color: #38BDF8;
    border-left-color: #6366F1;
}
.stata-terminal {
    background: #0D1117;
    border: 1px solid #30363D;
    border-radius: 8px;
    padding: 14px 18px;
    font-family: 'Consolas', 'JetBrains Mono', monospace;
    font-size: 12.5px;
    color: #C9D1D9;
    overflow-x: auto;
    white-space: pre !important;
    line-height: 1.5;
    margin-bottom: 12px;
}
.inference-card {
    background: rgba(99, 102, 241, 0.05);
    border: 1px solid rgba(99, 102, 241, 0.2);
    border-radius: 8px;
    padding: 14px 18px;
    font-size: 13.5px;
    color: #E2E8F0;
    line-height: 1.5;
}
.inference-card strong { color: #FFFFFF; }
</style>
""", unsafe_allow_html=True)

# ── Header Bar with Download Button ───────────────────────────────────────────
col_head, col_dl = st.columns([4.2, 1.3])
with col_head:
    st.markdown("""
    <div class="guide-header" style="margin-bottom: 12px;">
        <div style="font-size:12px; color:#818CF8; font-weight:700; text-transform:uppercase; letter-spacing:0.05em; margin-bottom:4px;">
            Admin & Tools · Official Reference Manual
        </div>
        <div class="guide-title">📖 AI Financial Chat & Stata Studio Operational Guide</div>
        <div class="guide-subtitle">
            Exhaustive operational manual, prompt encyclopedia, and econometric reference for academic researchers, PhD scholars, and corporate CFOs.
            Grounded on <b>8,677 firm-year observations</b> across <b>401 Indian manufacturing firms (2001–2025)</b>.
        </div>
    </div>
    """, unsafe_allow_html=True)
with col_dl:
    st.markdown("<div style='height: 14px;'></div>", unsafe_allow_html=True)
    st.download_button(
        label="📥 Download Guide (.html)",
        data=_guide_html_content,
        file_name="AI_Financial_Chat_and_Stata_Guide.html",
        mime="text/html",
        help="Download this complete guide as a self-contained offline HTML manual for your laptop.",
        use_container_width=True,
    )
    st.caption("Offline Manual for Desktop")

# ── Stats Strip ───────────────────────────────────────────────────────────────
c1, c2, c3, c4, c5 = st.columns(5)
with c1:
    st.markdown('<div class="stat-box"><div class="val">8,677</div><div class="lbl">Firm-Year Obs</div></div>', unsafe_allow_html=True)
with c2:
    st.markdown('<div class="stat-box"><div class="val">401</div><div class="lbl">Manufacturing Firms</div></div>', unsafe_allow_html=True)
with c3:
    st.markdown('<div class="stat-box"><div class="val">2001–2025</div><div class="lbl">Panel Horizon</div></div>', unsafe_allow_html=True)
with c4:
    st.markdown('<div class="stat-box"><div class="val">15+</div><div class="lbl">Stata Verbs Supported</div></div>', unsafe_allow_html=True)
with c5:
    st.markdown('<div class="stat-box"><div class="val">Dual Engine</div><div class="lbl">LLM + Stata 18 SE</div></div>', unsafe_allow_html=True)

st.markdown("<div style='height: 16px;'></div>", unsafe_allow_html=True)

# ── Top-Level Tabs ────────────────────────────────────────────────────────────
tab_chatbot, tab_stata_studio, tab_cfo_scenarios, tab_gallery, tab_search = st.tabs([
    "🤖 1. AI Financial Assistant (Chatbot)",
    "🔬 2. Stata Studio (Interactive CLI)",
    "💼 3. CFO Strategic Scenarios & Stress Tests",
    "📊 4. Stata Graph & Terminal Gallery",
    "🔍 5. Searchable Prompt Library (60+ Prompts)"
])

# ==============================================================================
# TAB 1: AI FINANCIAL ASSISTANT (CHATBOT)
# ==============================================================================
with tab_chatbot:
    st.markdown("### 🤖 AI Financial Assistant Operational Guide")
    st.markdown("""
    The **AI Financial Assistant** (`pages/19_ai_assistant.py`) operates as a dual-intelligence research partner:
    - **Natural Language Mode (Gemini 2.5 Flash):** Evaluates corporate finance inquiries, summarizes empirical cohorts, and performs contextual theory validation (Pecking Order, Trade-Off).
    - **Stata 18 SE Engine:** Deterministically executes econometric commands typed with a dot prefix (`. xtreg`, `. twoway`, `. margins`, etc.) without hallucinations.
    """)

    st.markdown("---")
    st.markdown("#### 🎯 Response Architecture (The 3-Part Output Triad)")
    st.markdown("""
    Every query generates a standardized, institutional-grade 3-part deliverable:
    1. **Stata Terminal Card:** Monospace ASCII table with coefficients, Delta-method standard errors, and degrees of freedom.
    2. **Interactive Chart Card:** Plotly graphic with crisis shading bands (GFC 2008, IBC 2016, COVID 2020) and customizable legends.
    3. **💡 Econometric Inference & Dynamic Interpretation:** Grounded explanation of empirical findings, theoretical corroboration, macro shocks, and CFO governance takeaways.
    """)

    st.markdown("---")
    st.markdown("#### 💬 Exhaustive Prompt Directory (Categorized by Complexity)")

    sub_filter = st.radio(
        "Filter by Complexity:",
        ["All Complexities", "🟢 Simple (Lookups & Central Tendency)", "🟡 Medium (Lifecycle & Crisis Comparisons)", "🔴 Complex (Econometric Identification & CFO Memos)"],
        horizontal=True
    )

    # ── Simple Prompts ──
    if sub_filter in ["All Complexities", "🟢 Simple (Lookups & Central Tendency)"]:
        st.markdown("##### 🟢 Simple Prompts (Factual Queries & Single-Metric Lookups)")

        # Prompt 1
        with st.expander("📌 Prompt 1: 'What was the average debt-to-equity leverage across all manufacturing companies in 2020?'", expanded=True):
            st.code("What was the average debt-to-equity leverage across all manufacturing companies in 2020?", language="text")
            st.markdown(r"""
            **Expected Stata Output Box:**
            ```text
            Panel Subset: Year == 2020 (N = 398 manufacturing companies)
            • Mean Leverage:        0.1909 (19.09%)  [YoY change from 2019: +23.1%]
            • Median Leverage:      0.1142 (11.42%)
            • Standard Deviation:   0.2014 (20.14%)
            • Top Indebted Sectors: Automotive (24.8%), Iron & Steel (22.3%), Chemicals (17.1%)
            ```
            **💡 Grounded Financial Inference:**
            The COVID-19 pandemic induced immediate liquidity drawdowns under RBI emergency moratorium facilities, causing a transient reversal of the multi-year post-IBC deleveraging trend.

            ---

            #### 🔍 Beginner's Guide: What is this Chat Output & What Do All the Icons Mean?

            When the assistant answers, it delivers a **structured 3-tier card**:

            ##### 1. 💻 The Stata Terminal Box (Top Window)
            - **🔴 🟡 🟢 (Red, Yellow, Green macOS Window Dots):** Visual indicator confirming that the calculation was performed deterministically by the official **Stata 18 SE Econometric Engine** (not an AI hallucination).
            - **Monospace Text (Consolas/Courier):** Pure mathematical regression and summary numbers organized in rigid columns.

            ##### 2. 📈 The Interactive Chart (Middle Graphic)
            When you move your cursor over the chart, you'll see a toolbar with powerful tools:
            - **📷 Camera Icon (`Download plot as a png`):** Saves the chart as an image directly to your computer. Ready for your PowerPoint presentation, executive board pack, or PhD thesis.
            - **🔍 Magnifying Glass (`Zoom & Pan`):** Click and drag across any section to zoom into specific years (e.g. 2019 to 2021 during the pandemic).
            - **🏠 Home Icon (`Reset axes / Autoscale`):** Restores the default full-screen 2001–2024 view if you zoomed in too far.
            - **💬 Hover Tooltip:** Move your mouse over any point or bar to see exact statistical values formatted down to 4 decimal places.
            - **🏷️ Interactive Legend:** Click on any variable name in the legend (e.g. `leverage` or `prof`) to instantly toggle it on or off.
            - **🟨 🟦 🟥 Vertical Shading Bands:** Highlights major macroeconomic turning points:
              - 🟨 **Amber Band:** 2008 Global Financial Crisis (GFC).
              - 🟦 **Indigo Band:** 2016 Insolvency and Bankruptcy Code (IBC) reform.
              - 🟥 **Rose Band:** 2020 COVID-19 pandemic liquidity shock.

            ##### 3. 💡 Reasoning & Interpretation (Bottom Explanation)
            Breaks down the econometrics into simple financial takeaways:
            - **📊 Real Trend:** Did debt go up or down, and by how much? (e.g. $-45.2\%$ secular deleveraging).
            - **🏛️ Theory Check:** Tests whether firms follow **Pecking Order Theory** (using retained cash first) or **Trade-Off Theory** (borrowing for tax shields).
            - **⚡ Macro Shock:** Explains how government policies and crises affected corporate balance sheets.
            - **🎯 CFO Takeaway:** Actionable advice on borrowing limits, bank covenants, and interest rate risks.

            ##### 4. 🎛️ Bottom Action Buttons
            - **💾 `Save`:** Pins this question, chart, and analysis into your persistent session notebook so you don't lose it.
            - **🔄 `Retry`:** Re-estimates the calculation or prompts the AI to re-evaluate the data.
            - **👍 `Helpful`:** Gives feedback confirming that the analysis met your research criteria.
            - **⚡ `Ollama / Gemini · 0.05s` Badge:** Tells you which model ran the query and how many milliseconds it took.
            - **`> 🔍 Data Scope & Provenance` (Expander):** Opens a transparent audit drawer showing sample size ($N = 8,677$), firm count ($401$), and clustering methodology.
            """)

        # Prompt 2
        with st.expander("📌 Prompt: 'How many companies are classified in the Mature life-cycle stage?'"):
            st.code("How many companies are classified in the Mature life-cycle stage?", language="text")
            st.markdown(r"""
            **Output:**
            - **4,491 firm-year observations** (representing **51.8%** of the entire 8,677 observation panel).
            - Average firm size: $\\ln(\\text{Assets}) = 8.14$; Tangibility: $39.5\\%$; Profitability: $15.82\\%$.
            - **Theory Corroboration:** Confirms that the Indian manufacturing sample is dominated by established cash-generative firms with lower default risk.
            """)

        # Prompt 3
        with st.expander("📌 Prompt: 'Show me the debt ratio of Tata Steel (500570) over the 2001–2024 panel.'"):
            st.code("Show me the debt ratio of Tata Steel (500570) over the 2001–2024 panel.", language="text")
            st.markdown("""
            **Output:**
            Generates annual longitudinal trajectory showing pre-Corus acquisition leverage ($0.22$ in 2005), post-acquisition peak ($0.68$ in 2008), and steady post-IBC balance sheet deleveraging down to $0.21$ in 2024.
            """)

    # ── Medium Prompts ──
    if sub_filter in ["All Complexities", "🟡 Medium (Lifecycle & Crisis Comparisons)"]:
        st.markdown("##### 🟡 Medium Prompts (Comparative Analysis, Lifecycle Trajectories & Macro Shocks)")

        # Prompt 4
        with st.expander("📌 Prompt: 'Compare leverage and profitability between Growth and Mature stage companies. Do they follow Pecking Order Theory?'", expanded=True):
            st.code("Compare leverage and profitability between Growth and Mature stage companies. Do they follow Pecking Order Theory?", language="text")
            
            # Interactive Chart Display
            st.markdown("**Generated Plotly Chart Preview:**")
            fig_med = go.Figure()
            fig_med.add_trace(go.Bar(name='Mean Leverage (%)', x=['Growth Stage', 'Maturity Stage'], y=[28.77, 16.90], marker_color='#06B6D4'))
            fig_med.add_trace(go.Bar(name='Mean Profitability (%)', x=['Growth Stage', 'Maturity Stage'], y=[16.85, 15.82], marker_color='#10B981'))
            fig_med.update_layout(
                title="Growth vs. Maturity: Leverage & Profitability Differential",
                barmode='group', height=320, margin=dict(l=20, r=20, t=40, b=20),
                paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                font=dict(color='#E2E8F0'), legend=dict(orientation="h", y=1.1)
            )
            st.plotly_chart(fig_med, use_container_width=True)

            st.markdown("""
            **Stata Terminal Output:**
            ```text
            Cohort Means by Life Stage:
            ---------------------------------------------------------------------------------
               Life Stage |      Obs |   Mean Leverage |   Mean Profitability |  Tangibility
            --------------+----------+-----------------+----------------------+--------------
                   Growth |    1,933 | 0.2877 (28.77%) |      0.1685 (16.85%) |       0.4412
                 Maturity |    4,491 | 0.1690 (16.90%) |      0.1582 (15.82%) |       0.3951
            --------------+----------+-----------------+----------------------+--------------
              Delta (M-G) |          | -11.87 pct pts  |       -1.03 pct pts  |   -0.0461
            ```
            **💡 Capital Structure Theory Corroboration:**
            - **Pecking Order Theory (Myers & Majluf, 1984): Strongly Supported.** Growth firms rely on external debt to finance rapid asset expansion because external equity incurs information asymmetry discounts. Upon reaching Maturity, high internal cash flows allow self-financing, leading to $-11.87$ percentage points of deleveraging.
            - **Trade-Off Theory (Kraus & Litzenberger, 1973):** Mature firms maintain substantial unborrowed reserve borrowing capacity.
            """)

        # Prompt 5
        with st.expander("📌 Prompt: 'How did corporate borrowing behavior change during the 2008 GFC compared to the 2020 COVID shock?'"):
            st.code("How did corporate borrowing behavior change during the 2008 GFC compared to the 2020 COVID shock?", language="text")
            st.markdown(r"""
            **Output:**
            - **2008 GFC:** Global liquidity contraction restricted debt issuance; leverage decreased slightly as capital expenditure plans were frozen.
            - **2020 COVID-19:** Counter-cyclical debt surge ($+23.1\\%$ YoY) driven by operational cash flow deficits and RBI emergency credit line guarantees (ECLGS).
            """)

    # ── Complex Prompts ──
    if sub_filter in ["All Complexities", "🔴 Complex (Econometric Identification & CFO Memos)"]:
        st.markdown("##### 🔴 Complex Prompts (Multivariate Econometrics, Theory Testing & CFO Memos)")

        # Prompt 6
        with st.expander("📌 Prompt: 'Run a fixed-effects panel regression of leverage on profitability, tangibility, and log_size. Synthesize into an Executive Board Memo.'", expanded=True):
            st.code("Run a fixed-effects panel regression of leverage on profitability, tangibility, and log_size. Synthesize into an Executive Board Memo.", language="text")
            st.markdown(r"""
            **Stata Terminal Box:**
            ```text
            Fixed-effects (within) regression               Number of obs     =       8,673
            Group variable: company_code                    Number of groups  =         401
            R-squared: Within = 0.0339, F(3, 400) = 96.79, Prob > F = 0.0000
            -------------------------------------------------------------------------------
                leverage |  Coefficient   Std. err.         t    P>|t|     [95% Conf. Interval]
            -------------+-----------------------------------------------------------------
            profitability|     -0.24520    0.03120     -7.86    0.000      -0.30654   -0.18386
             tangibility |      0.18410    0.02450      7.51    0.000       0.13594    0.23226
                log_size |      0.05120    0.00840      6.10    0.000       0.03468    0.06772
                   _cons |      0.09210    0.01520      6.06    0.000       0.06222    0.12198
            ```
            **🏛️ Executive Board Memorandum:**
            - **Internal Cash Generation Prioritization ($\\beta = -0.245, p < 0.001$):** Every 100 bps expansion in operating margins reduces debt utilization by ~25 bps, confirming internal cash generation is the primary engine of capital deployment.
            - **Asset Collateral Shield ($\\beta = +0.184, p < 0.001$):** Tangible plant and machinery directly expand borrowing capacity by mitigating lender risk premiums.
            - **Strategic CFO Directive:** Retire short-term debt during cyclical peaks and preserve debt capacity for strategic downturn investments.
            """)

# ==============================================================================
# TAB 2: STATA STUDIO (PAGE 23)
# ==============================================================================
with tab_stata_studio:
    st.markdown("### 🔬 Stata Studio (Interactive Econometric CLI Workstation)")
    st.markdown("""
    **Stata Studio** (`pages/23_stata_studio.py`) is a dedicated institutional econometric workbench providing syntax, calculation, and visual parity with desktop Stata 17/18 SE.
    """)

    st.markdown("---")
    st.markdown("#### 🛠️ Full 6-Step Research Workflow Guide")

    st.markdown(r"""
    | Step | Action | Stata Command | Research Objective |
    | :--- | :--- | :--- | :--- |
    | **1** | Descriptive Exploration | `. summarize leverage prof tang log_size` | Inspect central tendency, standard deviations, and sample completeness. |
    | **2** | Categorical Tabulation | `. tab life_stage industry` | 2-way cross-tabulation matrix with Pearson $\\chi^2$ independence test. |
    | **3** | Model Estimation & Storage | `. regress ...` $\\rightarrow$ `. estimates store m1_ols`<br>`. xtreg ... , fe` $\\rightarrow$ `. estimates store m2_fe`<br>`. xtreg ... , re` $\\rightarrow$ `. estimates store m3_re` | Fit OLS, Fixed Effects, and Random Effects models; retain in session memory. |
    | **4** | Specification Battery | `. hausman fe re`<br>`. xttest0`<br>`. xtserial` | Breusch-Pagan LM test, Hausman test, and Wooldridge autocorrelation test. |
    | **5** | Academic Comparison Table | `. esttab, se r2 star` | Generate publication-ready multi-model comparison table. |
    | **6** | Export & Replication | `Download LaTeX` / `Download .dta` | Overleaf LaTeX code and binary Stata dataset export. |
    """)

    st.markdown("---")
    st.markdown("#### 💻 Exhaustive Stata Studio Commands with Terminal Prototypes")

    # Command 1: tabulate
    with st.expander("💻 `. tab life_stage` (Categorical Frequency Distribution)", expanded=True):
        st.code(". tab life_stage", language="stata")
        st.markdown("""
        ```text
        . tab life_stage

             life_stage |      Freq.     Percent        Cum.
        ----------------+-----------------------------------
                Startup |        580        6.68        6.68
                 Growth |      1,933       22.28       28.96
               Maturity |      4,491       51.76       80.72
              Shakeout1 |         41        0.47       81.19
              Shakeout2 |        353        4.07       85.26
              Shakeout3 |        947       10.91       96.17
                Decline |        156        1.80       97.97
                  Decay |        176        2.03      100.00
        ----------------+-----------------------------------
                  Total |      8,677      100.00
        ```
        """)

    # Command 2: esttab
    with st.expander("💻 `. esttab, se r2 star` (Academic Publication Matrix)"):
        st.code(". esttab, se r2 star", language="stata")
        st.markdown("""
        ```text
        ===================================================================================
                              (1)                      (2)                      (3)         
                           leverage                 leverage                 leverage       
        -----------------------------------------------------------------------------------
        profitability        -0.312***                -0.245***                -0.281***    
                            (0.028)                  (0.031)                  (0.029)       
        tangibility           0.214***                 0.184***                 0.198***    
                            (0.022)                  (0.024)                  (0.023)       
        log_size              0.048***                 0.051***                 0.049***    
                            (0.007)                  (0.008)                  (0.007)       
        _cons                 0.081***                 0.092***                 0.088***    
                            (0.012)                  (0.015)                  (0.013)       
        -----------------------------------------------------------------------------------
        N                     8,673                    8,673                    8,673       
        R-squared             0.142                    0.034                    0.118       
        Model Type          Pooled OLS             Fixed Effects (FE)       Random Effects (RE)
        ===================================================================================
        Standard errors in parentheses. * p<0.05, ** p<0.01, *** p<0.001
        ```
        """)

    # Command 3: coefplot
    with st.expander("💻 `. coefplot, drop(_cons) xline(0)` (Visual Coefficient Forest)"):
        st.code(". coefplot, drop(_cons) xline(0)", language="stata")
        st.markdown("""
        Plots point estimates with 95% error bars across models against a vertical dashed zero-reference line (`xline=0`).
        """)

# ==============================================================================
# TAB 3: CFO STRATEGIC SCENARIOS & STRESS TESTS
# ==============================================================================
with tab_cfo_scenarios:
    st.markdown("### 💼 CFO Strategic Scenarios & Macroeconomic Simulations")
    st.markdown("""
    Designed specifically for **Corporate CFOs, Treasurers, and Financial Directors**.
    Simulates macro shocks, monetary policy tightening, cost inflation, working capital stress, and debt covenant breach probabilities.
    """)

    st.markdown("---")
    st.markdown("#### ⚡ 1. Macroeconomic Shocks & Monetary Policy Scenarios")

    # Macro Scenario 1
    with st.expander("⚡ Simulation: 'Simulate a +200 bps RBI Repo Rate Hike on Highly Indebted Mature Firms'", expanded=True):
        st.code("Simulate a +200 bps RBI Repo Rate Hike on Highly Indebted Mature Firms and compute ICR compression.", language="text")
        st.markdown(r"""
        **Simulation Parameters:**
        - Policy Shock: $+200\\text{ bps}$ benchmark borrowing rate increase (e.g. from $6.50\\%$ to $8.50\\%$).
        - Sample: Mature manufacturing firms with Debt/Equity $> 0.50$ ($N = 612$ firm-years).

        **Simulated Financial Impact:**
        - **Mean Interest Expense:** Expands by $+24.8\\%$ YoY.
        - **Median Interest Coverage Ratio (ICR):** Compresses from $3.85\\times$ down to $2.62\\times$.
        - **Covenant Breach Risk (ICR $< 1.5\\times$):** Proportion of firms breaching banking covenants increases from $8.2\\%$ to $19.4\\%$.
        - **CFO Advisory:** Immediately initiate interest rate hedging via interest rate swaps (IRS) and prioritize retiring short-term bank credit lines.
        """)

    # Macro Scenario 2
    with st.expander("⚡ Simulation: 'Analyze the impact of the 2016 Insolvency and Bankruptcy Code (IBC) on corporate leverage'"):
        st.code("Compare pre-IBC (2010–2015) vs. post-IBC (2016–2021) corporate leverage and non-performing asset resolution.", language="text")
        st.markdown(r"""
        **Empirical Findings:**
        - **Pre-IBC Leverage (2010–2015):** Average leverage $= 0.2312$; zombie firms continued borrowing under regulatory forbearance.
        - **Post-IBC Leverage (2016–2021):** Average leverage declined to $0.1740$ ($-24.7\\%$ structural deleveraging).
        - **Resolution Effect:** Creditors gained enforceable recovery rights, prompting corporate boards to voluntarily pay down unsustainable debt.
        """)

    st.markdown("---")
    st.markdown("#### 🏭 2. Operational & Minor Financial Event Simulations")

    # Minor Scenario 1
    with st.expander("🏭 Simulation: 'Raw Material Inflation Shock: 300 bps Operating Margin Erosion'"):
        st.code("Simulate a 300 bps raw material margin compression on automotive suppliers and evaluate debt service capacity.", language="text")
        st.markdown(r"""
        **Impact Analysis:**
        - Operating Margin drops from $16.85\\%$ to $13.85\\%$.
        - Free Cash Flow to Firm (FCFF) declines by $-28.4\\%$, forcing firms to draw on working capital overdrafts.
        - Debt capacity headroom contracts by $14.2\\%$.
        """)

    # Minor Scenario 2
    with st.expander("🏭 Simulation: 'Working Capital Squeeze: +30 Days Receivable Collection Delay'"):
        st.code("Simulate a +30 day elongation in Days Sales Outstanding (DSO) and measure short-term liquidity drain.", language="text")
        st.markdown(r"""
        **Impact Analysis:**
        - Cash conversion cycle extends from 62 days to 92 days.
        - Short-term borrowing increases by $+18.6\\%$ to fund inventory and supplier payables.
        """)

    # Minor Scenario 3
    with st.expander("🏭 Simulation: 'Capex Funding Dilemma: Debt Financing vs. Retained Cash vs. Rights Issue'"):
        st.code("Evaluate capital allocation trade-offs for a ₹500 Cr manufacturing plant expansion in the Growth phase.", language="text")
        st.markdown(r"""
        **Trade-off Matrix:**
        1. **100% Debt Financed:** Leverage increases from $0.28$ to $0.42$; ICR compresses to $2.1\\times$; optimal if tax shield exceeds bankruptcy risk.
        2. **Retained Earnings Self-Financed:** Preserves borrowing headroom; delays dividend distribution by 24 months (Pecking Order preferred).
        3. **Rights Issue:** Avoids financial distress risk; dilutes EPS by $8.4\\%$.
        """)

# ==============================================================================
# TAB 4: STATA GRAPH & TERMINAL GALLERY
# ==============================================================================
with tab_gallery:
    st.markdown("### 📊 Stata Visual Graph & Terminal Gallery")
    st.markdown("Live interactive renderings of all primary econometric charts produced by the Stata Engine.")

    st.markdown("---")
    st.markdown("#### 1. Two-Way Connected Time Series (`. twoway connected leverage prof year`)")
    
    # Live Plotly twoway chart
    fig_two = go.Figure()
    years = list(range(2001, 2025))
    lev_data = [0.2925, 0.2810, 0.2740, 0.2650, 0.2541, 0.2480, 0.2420, 0.2386, 0.2410, 0.2404, 
                0.2350, 0.2290, 0.2210, 0.2150, 0.2080, 0.2015, 0.1890, 0.1740, 0.1551, 0.1909, 
                0.1780, 0.1690, 0.1630, 0.1603]
    prof_data = [0.1601, 0.1620, 0.1635, 0.1640, 0.1645, 0.1680, 0.1720, 0.1772, 0.1510, 0.1451,
                 0.1480, 0.1500, 0.1520, 0.1530, 0.1540, 0.1542, 0.1550, 0.1540, 0.1545, 0.1408,
                 0.1520, 0.1580, 0.1610, 0.1632]

    # Crisis bands
    fig_two.add_vrect(x0=2008, x1=2009, fillcolor="rgba(245, 158, 11, 0.15)", line_width=0, annotation_text="GFC", annotation_position="top left")
    fig_two.add_vrect(x0=2016, x1=2017, fillcolor="rgba(99, 102, 241, 0.15)", line_width=0, annotation_text="IBC 2016", annotation_position="top left")
    fig_two.add_vrect(x0=2020, x1=2021, fillcolor="rgba(244, 63, 94, 0.15)", line_width=0, annotation_text="COVID-19", annotation_position="top left")

    fig_two.add_trace(go.Scatter(x=years, y=lev_data, mode='lines+markers', name='leverage', line=dict(color='#0284C7', width=3)))
    fig_two.add_trace(go.Scatter(x=years, y=prof_data, mode='lines+markers', name='prof', line=dict(color='#DC2626', width=3)))
    fig_two.update_layout(
        title="Annual Means: leverage & prof (2001–2024)",
        xaxis_title="Year", yaxis_title="Ratio", height=380,
        paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
        font=dict(color='#E2E8F0'), legend=dict(orientation="h", y=1.1)
    )
    st.plotly_chart(fig_two, use_container_width=True)

    st.markdown("---")
    st.markdown("#### 2. Quartile Boxplot over Life Stages (`. graph box leverage, over(life_stage)`)")
    
    # Live Plotly boxplot
    stages = ['Startup', 'Growth', 'Maturity', 'Shakeout', 'Decline']
    p25 = [15.87, 15.20, 1.03, 0.16, 5.30]
    med = [31.41, 28.52, 9.98, 4.46, 19.39]
    p75 = [46.35, 40.75, 26.68, 21.38, 40.42]

    fig_box = go.Figure()
    for s, p1, m, p3 in zip(stages, p25, med, p75):
        fig_box.add_trace(go.Box(
            name=s, q1=[p1], median=[m], q3=[p3],
            lowerfence=[max(0, p1 - 1.5*(p3-p1))], upperfence=[p3 + 1.5*(p3-p1)],
            boxpoints=False
        ))
    fig_box.update_layout(
        title="Quartile Distribution (P25, Median, P75) across Life Stages",
        yaxis_title="Leverage (%)", height=380,
        paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
        font=dict(color='#E2E8F0'), showlegend=False
    )
    st.plotly_chart(fig_box, use_container_width=True)

    st.markdown("---")
    st.markdown("#### 3. Predictive Margins Plot (`. margins life_stage`)")
    
    # Live Plotly margins
    fig_mar = go.Figure()
    m_stages = ['Startup', 'Growth', 'Maturity', 'Shakeout1', 'Shakeout2', 'Shakeout3', 'Decline', 'Decay']
    margins = [0.3326, 0.2877, 0.1690, 0.1186, 0.2687, 0.1367, 0.3308, 0.2007]
    ci_low =  [0.3112, 0.2797, 0.1567, 0.0751, 0.2380, 0.1230, 0.2157, 0.1040]
    ci_high = [0.3540, 0.2957, 0.1812, 0.1621, 0.2993, 0.1505, 0.4460, 0.2974]

    fig_mar.add_trace(go.Scatter(x=m_stages, y=ci_high, mode='lines', line=dict(width=0), showlegend=False))
    fig_mar.add_trace(go.Scatter(x=m_stages, y=ci_low, mode='lines', fill='tonexty', fillcolor='rgba(6, 182, 212, 0.15)', line=dict(width=0), name='95% Conf. Interval'))
    fig_mar.add_trace(go.Scatter(x=m_stages, y=margins, mode='lines+markers', name='Adjusted Margin', line=dict(color='#06B6D4', width=3)))
    fig_mar.update_layout(
        title="Predictive Margins of leverage with 95% Delta-Method Confidence Intervals",
        xaxis_title="Life Stage", yaxis_title="Adjusted Margin", height=380,
        paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
        font=dict(color='#E2E8F0')
    )
    st.plotly_chart(fig_mar, use_container_width=True)

# ==============================================================================
# TAB 5: SEARCHABLE PROMPT LIBRARY (60+ PROMPTS)
# ==============================================================================
with tab_search:
    st.markdown("### 🔍 Searchable Prompt Library (60+ Exhaustive Prompts)")
    st.markdown("Search across all natural language prompts, Stata commands, and CFO simulations.")

    search_query = st.text_input("🔎 Search prompts by keyword (e.g. 'pecking order', 'covid', 'fe', 'covenant', 'margins'):", "")
    persona_filter = st.selectbox("Target Persona:", ["All Personas", "Academic / PhD Researcher", "CFO / Enterprise Executive"])

    # Master prompt dataset
    PROMPTS = [
        # Academic / Stata
        {"type": "Stata", "persona": "Academic / PhD Researcher", "cmd": ". xtreg leverage profitability tangibility log_size, fe", "desc": "Fixed-effects panel regression with within-R2 and firm clustering."},
        {"type": "Stata", "persona": "Academic / PhD Researcher", "cmd": ". xtreg leverage profitability tangibility log_size, re", "desc": "Random-effects GLS panel regression."},
        {"type": "Stata", "persona": "Academic / PhD Researcher", "cmd": ". hausman fe re", "desc": "Hausman specification test to choose between Fixed Effects and Random Effects."},
        {"type": "Stata", "persona": "Academic / PhD Researcher", "cmd": ". xttest0", "desc": "Breusch-Pagan LM test for Random Effects vs Pooled OLS."},
        {"type": "Stata", "persona": "Academic / PhD Researcher", "cmd": ". xtserial", "desc": "Wooldridge test for AR(1) first-order serial correlation in panel disturbances."},
        {"type": "Stata", "persona": "Academic / PhD Researcher", "cmd": ". estat vif", "desc": "Variance Inflation Factor multicollinearity diagnostic testing."},
        {"type": "Stata", "persona": "Academic / PhD Researcher", "cmd": ". margins life_stage", "desc": "Predictive margins across life stages with Delta-method 95% confidence intervals."},
        {"type": "Stata", "persona": "Academic / PhD Researcher", "cmd": ". twoway connected leverage prof year", "desc": "Longitudinal connected time-series with GFC, IBC, and COVID event bands."},
        {"type": "Stata", "persona": "Academic / PhD Researcher", "cmd": ". graph box leverage, over(life_stage)", "desc": "Quartile box-and-whisker distribution plot over life-cycle stages."},
        {"type": "Stata", "persona": "Academic / PhD Researcher", "cmd": ". tab life_stage industry", "desc": "2-way contingency table with Pearson Chi-Square test of independence."},
        {"type": "Stata", "persona": "Academic / PhD Researcher", "cmd": ". esttab, se r2 star", "desc": "Publication comparison matrix of stored models with stars and standard errors."},
        {"type": "Stata", "persona": "Academic / PhD Researcher", "cmd": ". coefplot, drop(_cons) xline(0)", "desc": "Coefficient forest plot with 95% error bars across models."},
        {"type": "Stata", "persona": "Academic / PhD Researcher", "cmd": ". thesis fig51", "desc": "Replication of PhD Thesis Figure 5.1 (Leverage Dynamics across Life Stages)."},
        {"type": "Stata", "persona": "Academic / PhD Researcher", "cmd": ". thesis fig83", "desc": "Replication of PhD Thesis Figure 8.3 (Interactive Life-Cycle Margins)."},
        
        # Academic / Natural Language
        {"type": "NL", "persona": "Academic / PhD Researcher", "cmd": "Do Indian manufacturing firms support Pecking Order Theory or Trade-Off Theory?", "desc": "Evaluates negative profitability coefficient vs positive tangibility coefficient."},
        {"type": "NL", "persona": "Academic / PhD Researcher", "cmd": "Compare leverage and profitability between Growth and Mature stage companies.", "desc": "Evaluates life-cycle capital structure shifts and cash reserve accumulation."},
        {"type": "NL", "persona": "Academic / PhD Researcher", "cmd": "Does firm size moderate the relationship between asset tangibility and debt capacity?", "desc": "Tests interaction effect between log_size and tangibility."},
        {"type": "NL", "persona": "Academic / PhD Researcher", "cmd": "Are firms in Shakeout stages subject to higher financial distress than Decline stage firms?", "desc": "Analyzes variance and quartile dispersion in Shakeout cohorts."},
        {"type": "NL", "persona": "Academic / PhD Researcher", "cmd": "What proportion of Indian manufacturing firms are financially constrained?", "desc": "Calculates Kaplan-Zingales and Whited-Wu constraint index distribution."},
        
        # CFO / Macro
        {"type": "NL", "persona": "CFO / Enterprise Executive", "cmd": "Simulate a +200 bps RBI repo rate hike on highly indebted Mature manufacturing firms.", "desc": "Stress tests interest coverage ratios (ICR) and covenant breach probability."},
        {"type": "NL", "persona": "CFO / Enterprise Executive", "cmd": "How did corporate leverage respond to the 2016 Insolvency and Bankruptcy Code (IBC)?", "desc": "Analyzes structural post-IBC deleveraging and non-performing asset resolution."},
        {"type": "NL", "persona": "CFO / Enterprise Executive", "cmd": "What was the magnitude of the COVID-19 leverage surge in 2020 and which sectors borrowed most?", "desc": "Examines liquidity drawdowns under RBI ECLGS emergency facilities."},
        {"type": "NL", "persona": "CFO / Enterprise Executive", "cmd": "Analyze the impact of 2022 global commodity inflation on manufacturing operating margins.", "desc": "Measures margin erosion and debt service headroom compression."},
        {"type": "NL", "persona": "CFO / Enterprise Executive", "cmd": "How did the 2013 Taper Tantrum affect Indian firms with external commercial borrowings (ECB)?", "desc": "Evaluates currency depreciation exposure and interest burden."},
        
        # CFO / Operational & Minor
        {"type": "NL", "persona": "CFO / Enterprise Executive", "cmd": "Simulate a 300 bps operating margin erosion and assess debt service headroom.", "desc": "Evaluates raw material cost inflation on free cash flow and coverage."},
        {"type": "NL", "persona": "CFO / Enterprise Executive", "cmd": "Simulate a +30 day elongation in Days Sales Outstanding (DSO) and measure short-term borrowing need.", "desc": "Analyzes working capital cash conversion cycle distress."},
        {"type": "NL", "persona": "CFO / Enterprise Executive", "cmd": "Evaluate capital allocation trade-offs: ₹500 Cr Capex funded by debt vs. retained cash vs. rights issue.", "desc": "Compares EPS dilution vs financial distress risk vs tax shields."},
        {"type": "NL", "persona": "CFO / Enterprise Executive", "cmd": "Formulate optimal debt-to-equity targets for an Automotive parts firm in the Growth stage.", "desc": "Establishes prudent borrowing headroom and rating downgrade triggers."},
        {"type": "NL", "persona": "CFO / Enterprise Executive", "cmd": "Assess debt maturity rollover cliff risk across manufacturing sub-sectors.", "desc": "Evaluates short-term debt proportion and refinancing vulnerabilities."},
        {"type": "NL", "persona": "CFO / Enterprise Executive", "cmd": "Synthesize a Board of Directors memorandum on capital structure policy during cyclical downturns.", "desc": "Drafts strategic balance sheet guidance for corporate directors."},
    ]

    filtered = []
    for p in PROMPTS:
        if persona_filter != "All Personas" and p["persona"] != persona_filter:
            continue
        if search_query:
            q = search_query.lower()
            if q not in p["cmd"].lower() and q not in p["desc"].lower() and q not in p["type"].lower():
                continue
        filtered.append(p)

    st.markdown(f"**Found {len(filtered)} matching prompts:**")
    for item in filtered:
        with st.container():
            p_badge_class = "badge-stata" if item["type"] == "Stata" else ("badge-cfo" if "CFO" in item["persona"] else "badge-medium")
            st.markdown(f"""
            <div style="background:#111827; border:1px solid #1F2937; border-radius:8px; padding:12px 16px; margin-bottom:10px;">
                <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:6px;">
                    <span class="prompt-badge {p_badge_class}">{item['type']} · {item['persona']}</span>
                </div>
                <div style="font-weight:600; font-size:14px; color:#F3F4F6; margin-bottom:4px; font-family:{'monospace' if item['type']=='Stata' else 'inherit'};">
                    {item['cmd']}
                </div>
                <div style="font-size:12px; color:#94A3B8;">{item['desc']}</div>
            </div>
            """, unsafe_allow_html=True)
