# Screen-by-Screen UI Design Layout Blueprint
# LifeCycle Leverage — Complete Screen Wireframes & Grid Specifications

---

## Global Navigation Shell & Header Layout

```
┌─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│ 💎 LifeCycle Leverage  │ 🏷️ Active: (2001-25)_April26  │ 🏢 401 Firms · 7,820 Obs  │ [ ☀️ Light / 🌙 Dark ] │ 👤 Prof. Bhatia (Admin) │
├─────────────────────────┼───────────────────────────────────────────────────────────────────────────────────────────┴─────────────────┤
│ 📂 DATASET VINTAGE      │                                                                                                             │
│ [ 🏷️ (2001-25)_April26▼]│                                    MAIN SCREEN WORKSPACE CANVAS                                             │
│                         │                                                                                                             │
│ 🔍 COMPANY SEARCH       │                                                                                                             │
│ [ Search 401 firms... ] │                                                                                                             │
│ [MegaCap] [Nifty50]     │                                                                                                             │
│                         │                                                                                                             │
│ 📅 YEAR TIMELINE        │                                                                                                             │
│ 2001 ──[========]── 2025│                                                                                                             │
│ [01-10] [11-20] [IBC16+]│                                                                                                             │
│                         │                                                                                                             │
│ 🏷️ LIFE STAGES          │                                                                                                             │
│ (🟢) (🔵) (🟣) (🟠) (🔴)│                                                                                                             │
│                         │                                                                                                             │
│ ⚡ REGIME SHOCKS        │                                                                                                             │
│ [⚡ GFC] [🏛️ IBC] [🦠 CV]│                                                                                                             │
│                         │                                                                                                             │
│ 🎓 CITATIONS: [ON]      │                                                                                                             │
└─────────────────────────┴─────────────────────────────────────────────────────────────────────────────────────────────────────────────┘
```

---

# 🏛️ WORKSPACE 1: EXECUTIVE & DISCOVERY

---

## Screen 0: Overview & Research Architecture (`0_overview.py`)

### Layout Wireframe
```
┌─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│ 🏛️ LIFECYCLE LEVERAGE INTELLIGENCE PLATFORM                                                                                 │
│ Determinants of Capital Structure over Corporate Life Stages (Ph.D. Research, Prof. Surendra Kumar, University of Delhi)    │
├─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┤
│ ┌───────────────────────┬────────────────────────┬────────────────────────┬───────────────────────────────────────────────┐ │
│ │ 🏢 401                │ 📅 24 Years            │ 📊 7,820               │ ⚖️ 4 Theoretical Frameworks                   │ │
│ │ Listed Indian Firms   │ 2001 – 2025 Panel      │ Firm-Year Observations │ Pecking Order · Trade-Off · Agency · Market   │ │
│ └───────────────────────┴────────────────────────┴────────────────────────┴───────────────────────────────────────────────┘ │
├─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┤
│ 🗺️ RESEARCH & DATA FLOW ARCHITECTURE                                                                                        │
│ ┌────────────────────┐      ┌─────────────────────────┐      ┌────────────────────────┐      ┌────────────────────────────┐ │
│ │ 1. Dickinson (2011)│ ───► │ 2. Econometric Models   │ ───► │ 3. Machine Learning    │ ───► │ 4. Executive Action        │ │
│ │ Cash-Flow Patterns │      │ OLS / Fixed Effects/GMM │      │ Random Forest / SHAP   │      │ Board Decks & Simulator    │ │
│ └────────────────────┘      └─────────────────────────┘      └────────────────────────┘      └────────────────────────────┘ │
├─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┤
│ 🚀 QUICK LAUNCH WORKSPACES                                                                                                  │
│ ┌───────────────────────────────┬───────────────────────────────┬───────────────────────────────┬─────────────────────────┐ │
│ │ 📊 Executive Dashboard        │ 🔬 Econometrics Lab           │ 🕸️ Life-Stage Transitions     │ 🤖 AI Financial Copilot │ │
│ │ Real-time KPIs & Regime Shocks│ OLS, FE, RE & Forest Plots    │ Migration & Stickiness Matrices│ Grounded LLM Assistant │ │
│ │ [ Open Dashboard ➔ ]          │ [ Open Lab ➔ ]                │ [ Open Transitions ➔ ]        │ [ Open Copilot ➔ ]      │ │
│ └───────────────────────────────┴───────────────────────────────┴───────────────────────────────┴─────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## Screen 1: Executive Dashboard & Bento HUD (`1_dashboard.py`)

### Layout Wireframe
```
┌─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│ 📊 EXECUTIVE COMMAND CENTER                                                                                                 │
│ Real-time Macro, Determinant, and Life-Stage Leverage Overview                                                              │
├─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┤
│ ┌─────────────────────────────┬─────────────────────────────┬─────────────────────────────┬───────────────────────────────┐ │
│ │ 🏢 Active Universe          │ ⚖️ Average Leverage         │ 📈 Median Profitability     │ 🏭 Avg Tangibility            │ │
│ │ 401 Firms                   │ 34.2%  ▲ +1.4pp YoY         │ 12.8%  ▼ -0.3pp YoY         │ 48.6%  ▲ +0.8pp YoY           │ │
│ │ ▅▆▇█▇▆▅▄▃▂ (2001-2025)      │ ▂▃▅▆▇██▇▆▅ (Trend Sparkline)│ ▇▆▅▄▃▂▃▄▅▆ (Trend Sparkline)│ ▄▅▆▇▇██▇▆▅ (Trend Sparkline)  │ │
│ │ [Balanced Panel: 98.2%]     │ [ ───●──────── 72nd Pct ]   │ [ ─────●────── 55th Pct ]   │ [ ───────●──── 81st Pct ]     │ │
│ └─────────────────────────────┴─────────────────────────────┴─────────────────────────────┴───────────────────────────────┘ │
├─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┤
│ 💡 REAL-TIME ECONOMETRIC VERDICT BANNER                                                                                     │
│ 🏛️ Pecking Order Alignment: Profitability exerts a strong negative coefficient (β = -0.342, p < 0.001) on Debt ratios.    │
├──────────────────────────────────────────────────────────────┬──────────────────────────────────────────────────────────────┤
│ 📈 FINANCIAL LEVERAGE OVER TIME (WITH REGIME SHOCKS)         │ 🎯 CORPORATE LIFE-STAGE COMPOSITION                          │
│ ┌──────────────────────────────────────────────────────────┐ │ ┌──────────────────────────────────────────────────────────┐ │
│ │ [░░ GFC '08 ░░]    [▒▒ IBC '16 ▒▒]    [▓▓ COVID '20 ▓▓]  │ │ │              ╭──────────────╮                            │ │
│ │   ▲                     ▲                   ▲            │ │ │           ╭──╯  Mature 44%  ╰──╮                         │ │
│ │  ╱ ╲                   ╱ ╲                 ╱ ╲           │ │ │          │ Growth 28%       Intro 12%│                   │ │
│ │ ╱   ╲─────────────────╱   ╲───────────────╱   ╲          │ │ │           ╰──╮ Shakeout 11% ╭──╯                         │ │
│ │ 2001 2005   2008    2012  2016    2020  2024 2025        │ │ │              ╰── Decline 5%─╯                            │ │
│ └──────────────────────────────────────────────────────────┘ │ └──────────────────────────────────────────────────────────┘ │
├──────────────────────────────────────────────────────────────┴──────────────────────────────────────────────────────────────┤
│ 📋 DETERMINANT DECOMPOSITION TABLE (Table 5.9 Synthesis)                                                                    │
│ [ Firm Code │ Company Name │ Life Stage │ Leverage (%) │ Profitability (%) │ Tangibility (%) │ Size (Log TA) │ Vintage ]    │
└─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## Screen 2: Peer Benchmarks & Radar Matrix (`2_peer_benchmarks.py`)

### Layout Wireframe
```
┌─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│ 🎯 PEER BENCHMARKING & COHORT POSITIONING                                                                                   │
│ Target Company: [ Reliance Industries Limited ▼ ]  |  Peer Group: [ Energy Sector · Mature Stage (84 Firms) ]               │
├──────────────────────────────────────────────────────────────┬──────────────────────────────────────────────────────────────┤
│ 🕸️ MULTI-AXIAL RADAR COMPARISON                              │ 📊 QUARTILE POSITIONING MATRIX                               │
│                      Leverage (42%)                          │ ┌──────────────────────────────────────────────────────────┐ │
│                           ▲                                  │ │ Leverage (Debt/Equity):                                  │ │
│                           │      Reliance                    │ │ Min ───[ Q1 ──── Median ───●(Reliance 42%)── Q3 ]─── Max │ │
│            Size ──────────┼────────── Profitability          │ │                                                          │ │
│            (14.2)         │           (16.4%)                │ │ Profitability (ROA):                                     │ │
│                           │                                  │ │ Min ───[ Q1 ──── Median ───●(Reliance 16%)── Q3 ]─── Max │ │
│            Tangibility ───┴────────── Growth                 │ │                                                          │ │
│            (68%)                     (8.2%)                  │ │ Tangibility:                                             │ │
│              ─── Reliance  --- Energy Sector Median          │ │ Min ───[ Q1 ──── Median ───────────●(Reliance 68%) ] Max │ │
│ └──────────────────────────────────────────────────────────┘ │ └──────────────────────────────────────────────────────────┘ │
├──────────────────────────────────────────────────────────────┴──────────────────────────────────────────────────────────────┤
│ 🏢 DIRECT PEER COMPARISON TABLE                                                                                             │
│ [ Company Name │ Stage │ Total Debt (₹ Cr) │ Debt/Assets │ Interest Coverage │ Cash Flow / Total Assets │ Distress Score ]  │
└─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## Screen 5: Panel Data Explorer (`5_data_explorer.py`)

### Layout Wireframe
```
┌─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│ 🗄️ PANEL DATA EXPLORER & VINTAGE MATRIX                                                                                     │
│ [ View: Core Determinants ▼ ]  [ Vintage: All Vintages ▼ ]  [ Filter: All Stages ▼ ]  [ 📥 Export CSV ]  [ 📥 Export Parquet ]│
├─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┤
│ ┌──────────┬──────────────────────┬──────┬────────────┬─────────────┬──────────────┬─────────────┬────────────────────────┐ │
│ │ Co. Code │ Company Name         │ Year │ Life Stage │ Leverage    │ Profit (ROA) │ Tangibility │ Vintage Source         │ │
│ ├──────────┼──────────────────────┼──────┼────────────┼─────────────┼──────────────┼─────────────┼────────────────────────┤ │
│ │ 110100   │ Reliance Industries  │ 2024 │ Mature     │ 38.4%       │ 14.2%        │ 62.1%       │ [🏷️ Thesis (2001-24)]  │ │
│ │ 110100   │ Reliance Industries  │ 2025 │ Mature     │ 36.1%       │ 15.8%        │ 61.4%       │ [🏷️ CMIE 2025 Rollfwd] │ │
│ │ 120400   │ Tata Motors Ltd      │ 2024 │ Shakeout   │ 54.2%       │ 8.4%         │ 48.2%       │ [🏷️ Thesis (2001-24)]  │ │
│ │ 130800   │ Infosys Limited      │ 2025 │ Mature     │ 2.1%        │ 28.6%        │ 18.4%       │ [🏷️ CMIE 2025 Rollfwd] │ │
│ └──────────┴──────────────────────┴──────┴────────────┴─────────────┴──────────────┴─────────────┴────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┘
```

---

# 🔬 WORKSPACE 2: QUANTITATIVE & ECONOMETRICS LAB

---

## Screen 8: Econometrics Lab — OLS / FE / RE (`8_econometrics.py`)

### Layout Wireframe
```
┌─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│ 🔬 ECONOMETRICS LAB: STATIC PANEL ESTIMATIONS                                                                               │
│ Dependent Variable: [ Total Leverage (Book Debt / TA) ▼ ]  |  Panel Specification: [ Balanced Panel (2001-2024) ]          │
├─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┤
│ ┌─────────────────────────────┬─────────────────────────────┬─────────────────────────────┬───────────────────────────────┐ │
│ │ 📊 Pooled OLS               │ 🏛️ Fixed Effects (Within)   │ 🎲 Random Effects (GLS)     │ ⚖️ Hausman Diagnostic         │ │
│ │ R² = 0.428 · F = 184.2***   │ R² = 0.612 · F = 294.1***   │ R² = 0.584 · Wald = 312.4***│ χ² = 184.6 (p < 0.0001)       │ │
│ │ [View OLS Details]          │ [⭐ PREFERRED SPECIFICATION]│ [View RE Details]           │ Verdict: Reject Random Effects│ │
│ └─────────────────────────────┴─────────────────────────────┴─────────────────────────────┴───────────────────────────────┘ │
├──────────────────────────────────────────────────────────────┬──────────────────────────────────────────────────────────────┤
│ 🌲 REGRESSION COEFFICIENT FOREST PLOT (95% CI)              │ 📐 FORMULA SPECIFICATION & THEORY SUMMARY                    │
│ Variable       Coeff (95% CI)       P-Value                  │ ┌──────────────────────────────────────────────────────────┐ │
│ Profitability  ├───●───┤ (-0.342)    <0.001 ***              │ │ Lev_it = α_i + β_1 Prof_it + β_2 Tang_it +               │ │
│ Tangibility        ├───●───┤ (0.281) <0.001 ***              │ │          β_3 Size_it + β_4 Growth_it + γ_t + ε_it        │ │
│ Firm Size             ├──●──┤(0.142) <0.010 **               │ └──────────────────────────────────────────────────────────┘ │
│ Growth Opp.     ├──●──┤      (0.048)  0.082 .                │ • Profitability: Strong negative effect supports Pecking     │ │
│ NDTS         ├──●──┤        (-0.112) <0.050 *                │   Order Theory (internal financing preferred).               │ │
│ └──────────────────────────────────────────────────────────┘ │ • Tangibility: Positive coefficient confirms Trade-Off Theory│ │
└─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## Screen 13: Advanced Econometrics — Dynamic GMM (`13_advanced_econometrics.py`)

### Layout Wireframe
```
┌─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│ 🧪 ADVANCED DYNAMIC ECONOMETRICS: TWO-STEP SYSTEM GMM (Blundell-Bond)                                                       │
├─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┤
│ ┌─────────────────────────────┬─────────────────────────────┬─────────────────────────────┬───────────────────────────────┐ │
│ │ ⏱️ Target Adjustment Speed  │ 📊 Arellano-Bond AR(1)      │ 📊 Arellano-Bond AR(2)      │ 🛡️ Hansen Overidentification  │ │
│ │ λ = 0.384 (38.4% per year)  │ z = -4.82 (p < 0.001)       │ z = 0.84 (p = 0.402)        │ χ² = 42.1 (p = 0.284)         │ │
│ │ Half-Life = 1.44 Years      │ [✓] 1st-order correlation   │ [✓] NO 2nd-order correl.    │ [✓] Instruments are Valid     │ │
│ └─────────────────────────────┴─────────────────────────────┴─────────────────────────────┴───────────────────────────────┘ │
├──────────────────────────────────────────────────────────────┬──────────────────────────────────────────────────────────────┤
│ 📈 TARGET LEVERAGE ADJUSTMENT PATH                          │ 🦠 COVID-19 REGIME RESILIENCE WATERFALL                      │
│ Actual vs. Target Debt Ratio Trajectory                      │ Debt Expansion vs. Contraction by Life Stage Pre/Post-COVID  │
│ ┌──────────────────────────────────────────────────────────┐ │ ┌──────────────────────────────────────────────────────────┐ │
│ │ ─── Actual Leverage   - - - Target Optimal Leverage (Lev*)│ │ │ Intro Firms:   ▲ +6.4pp (Liquidity buffering)            │ │
│ │       ╭─────────────────────── Actual                    │ │ │ Growth Firms:  ▲ +4.2pp (Capex continuity)                │ │
│ │    ╭──╯   - - - - - - - - - - Target                     │ │ │ Mature Firms:  ▼ -2.8pp (Deleveraging & Cash conservation)│ │
│ │ ───╯                                                     │ │ │ Shakeout:      ▲ +8.1pp (Refinancing distress)            │ │
│ └──────────────────────────────────────────────────────────┘ │ └──────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## Screen 15: Interaction Effects (`15_interaction_effects.py`)

### Layout Wireframe
```
┌─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│ 🔀 INTERACTION & MODERATION EFFECTS: Profitability × Tangibility across Life Stages                                          │
├──────────────────────────────────────────────────────────────┬──────────────────────────────────────────────────────────────┤
│ 📈 SIMPLE SLOPES INTERACTION PLOT                            │ 📊 STAGE-MODERATED MARGINAL EFFECTS                          │
│ Profitability effect on Leverage conditioned on Tangibility  │ Marginal effect of Profitability on Leverage by Stage:       │
│ ┌──────────────────────────────────────────────────────────┐ │ ┌──────────────────────────────────────────────────────────┐ │
│ │ Leverage (%)                                             │ │ 🟢 Introduction Stage:  β = -0.142 (p = 0.082)             │ │
│ │   │ \  (Low Tangibility: β = -0.482***)                  │ │ 🔵 Growth Stage:        β = -0.284 (p = 0.004)             │ │
│ │   │  \                                                   │ │ 🟣 Mature Stage:        β = -0.428 (p < 0.001)             │ │
│ │   │   \─── (Mean Tangibility: β = -0.342***)             │ │ 🟠 Shakeout Stage:      β = -0.186 (p = 0.042)             │ │
│ │   │       \─────── (High Tangibility: β = -0.184***)     │ │ 🔴 Decline Stage:       β = +0.062 (p = 0.412, insig.)     │ │
│ │   └──────────────────────── Profitability (%)            │ │                                                            │ │
│ └──────────────────────────────────────────────────────────┘ │ └──────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## Screen 9: Machine Learning & SHAP Interpretability (`9_ml_models.py`)

### Layout Wireframe
```
┌─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│ 🤖 MACHINE LEARNING MODEL SUITE & NON-LINEAR SHAP INTERPRETABILITY                                                          │
├─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┤
│ ┌─────────────────────────────┬─────────────────────────────┬─────────────────────────────┬───────────────────────────────┐ │
│ │ 🌲 Random Forest Regressor  │ ⚡ XGBoost Regressor        │ 💡 LightGBM (Selected)      │ 🎯 Out-of-Sample Test R²      │ │
│ │ RMSE: 0.064 · MAE: 0.042    │ RMSE: 0.058 · MAE: 0.038    │ RMSE: 0.054 · MAE: 0.034    │ 74.2% (vs 61.2% OLS/FE)       │ │
│ └─────────────────────────────┴─────────────────────────────┴─────────────────────────────┴───────────────────────────────┘ │
├──────────────────────────────────────────────────────────────┬──────────────────────────────────────────────────────────────┤
│ 🐝 SHAP FEATURE IMPORTANCE BEESWARM                          │ 💧 SINGLE COMPANY SHAP WATERFALL EXPLAINER                   │
│ Feature          Impact on Leverage (SHAP value)             │ Target: Reliance Industries Limited (2024 Leverage: 38.4%)   │
│ Profitability   🔵🔵🔵🔵🔵 🔴🔴🔴🔴🔴                        │ Base Value (Panel Mean): 34.2%                               │
│ Tangibility         🔵🔵🔵 🔴🔴🔴🔴                          │ + Tangibility (62.1%):      ▲ +3.8pp                         │
│ Firm Size               🔵 🔴🔴🔴🔴                          │ + Size (Large Cap):         ▲ +2.4pp                         │
│ Dickinson Stage       🔵🔵 🔴🔴🔴                            │ - Profitability (14.2%):    ▼ -1.6pp                         │
│ NDTS                   🔵🔵 🔴🔴                             │ - Dickinson Stage (Mature): ▼ -0.4pp                         │
│ (Feature Value: 🔵 Low  🔴 High)                             │ Final Predicted Leverage: 38.4% [✓ Exact Match]              │
└──────────────────────────────────────────────────────────────┴──────────────────────────────────────────────────────────────┘
```

---

# 🕸️ WORKSPACE 3: LIFE-STAGE DYNAMICS & KNOWLEDGE GRAPHS

---

## Screen 20 & 12: Transitions & Markov Stickiness (`20_life_stage_dynamics.py`, `12_transitions.py`)

### Layout Wireframe
```
┌─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│ 🔄 MARKOV LIFE-STAGE TRANSITION MATRICES & MIGRATION CHORDS                                                                 │
├──────────────────────────────────────────────────────────────┬──────────────────────────────────────────────────────────────┤
│ 🎯 5×5 EMPIRICAL MARKOV TRANSITION MATRIX                    │ 🌊 24-YEAR CORPORATE MIGRATION FLOW (SANKEY)                 │
│ To:        Intro    Growth   Mature   Shake    Decline       │ ┌──────────────────────────────────────────────────────────┐ │
│ Intro      [ 68.4%   24.2%    4.1%     2.2%     1.1% ]       │ │ 2001                       2016                    2025  │ │
│ Growth     [  2.1%   78.6%   16.4%     1.8%     1.1% ]       │ │ Intro (18%) ────────► Growth (32%) ───────► Mature (44%) │ │
│ Mature     [  0.4%    3.2%   88.4%     6.2%     1.8% ] ◄Max  │ │ Growth (38%) ───────► Mature (48%) ───────► Shakeout(11%)│ │
│ Shakeout   [  1.2%    4.1%   28.4%    52.6%    13.7% ]       │ │ Mature (36%) ───────► Shakeout (14%) ─────► Decline (5%) │ │
│ Decline    [  0.8%    1.2%    8.4%    18.2%    71.4% ]       │ └──────────────────────────────────────────────────────────┘ │
├──────────────────────────────────────────────────────────────┴──────────────────────────────────────────────────────────────┤
│ ⏳ CORPORATE STAGE SURVIVAL & HALF-LIFE (Kaplan-Meier Analysis)                                                             │
│ • Mature Stage Half-Life: 14.8 Years | • Growth Stage Half-Life: 6.2 Years | • Shakeout Stage Half-Life: 2.8 Years          │
└─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## Screen 18 & 21: Knowledge Graph V2 & Company Navigator (`18_company_navigator.py`, `21_knowledge_graph2.py`)

### Layout Wireframe
```
┌─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│ 🕸️ OCAML-BACKED SEMANTIC KNOWLEDGE GRAPH (Macro ➔ Meso ➔ Micro)                                                             │
│ [ Zoom Level: 🌐 Macro (Policy) │ 🏢 Meso (Industry/Stage) │ 🔬 Micro (Firm Ego-Graph) ]                                    │
├──────────────────────────────────────────────────────────────┬──────────────────────────────────────────────────────────────┤
│ 🌌 OBSIDIAN-STYLED INTERACTIVE NETWORK CANVAS                │ 📋 NODE INSPECTOR & EXPLAIN THIS STAT DRAWER                 │
│                                                              │ ┌──────────────────────────────────────────────────────────┐ │
│                      (🏛️ IBC 2016 Shock)                    │ │ Selected Node: Reliance Industries Limited (Micro)        │ │
│                              │                               │ │ • Life Stage: Mature (Verified via OCaml Ontology)       │ │
│                 ╭────────────┴────────────╮                  │ │ • Normative Debt Band: [28.0% – 42.0%]                   │ │
│         (Energy Meso)               (Telecom Meso)           │ │ • Current Leverage: 38.4% (Within Safe Band)             │ │
│               │                           │                  │ │ • Anomaly Flag: [✓ Normal / No Breach]                   │ │
│        (Reliance Micro)──────────────(Tata Power Micro)      │ │                                                          │ │
│                                                              │ │ 💡 OCaml Reasoning Engine:                               │ │
│                                                              │ │ "Firms in Mature stage exhibit high free cash flows and  │ │
│                                                              │ │ low asymmetric information, enabling lower cost of debt."│ │
│ └──────────────────────────────────────────────────────────┘ └──────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┘
```

---

# 🎯 WORKSPACE 4: DECISION TOOLS & SYSTEM

---

## Screen 3: Capital Structure Simulator (`3_scenarios.py`)

### Layout Wireframe
```
┌─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│ 🎮 CAPITAL STRUCTURE SCENARIO SIMULATOR & SENSITIVITY COCKPIT                                                               │
│ Target Firm: [ Tata Motors Limited ▼ ]  |  Current Stage: [ Shakeout (2024) ]  |  Current Leverage: 54.2%                   │
├──────────────────────────────────────────────────────────────┬──────────────────────────────────────────────────────────────┤
│ 🎛️ WHAT-IF STRESS TESTING SLIDERS                            │ 🎯 REAL-TIME SIMULATION & DEBT CAPACITY HUD                  │
│                                                              │ ┌─────────────────────────────┬────────────────────────────┐ │
│ 1. Profitability Shock (Δ ROA):                              │ │ Projected Leverage: 46.8%   │ Credit Rating Forecast:    │ │
│ [-10%] ──────────[● (-3.5%)]────────── [+10%]                │ │ ▼ -7.4pp Debt Reduction     │ BBB+  ───►  A- (Upgrade)   │ │
│                                                              │ └─────────────────────────────┴────────────────────────────┘ │
│ 2. Tangibility Asset Shift (Δ Tang):                         │ 📊 Trade-Off vs Pecking Order Capacity Envelope:             │
│ [-20%] ──────────────[● (+5.0%)]────── [+20%]                │ ┌──────────────────────────────────────────────────────────┐ │
│                                                              │ │ Safe Capacity Band:       [ 32.0% ─────────── 48.0% ]    │ │
│ 3. Asset Scale Expansion:                                    │ │ Simulated Position:       [ ─────────────● (46.8%) ]     │ │
│ [ -5%] ──────────────────[● (+8.0%)]── [+25%]                │ │ Status:                   [ 🟢 WITHIN OPTIMAL ZONE ]     │ │
│                                                              │ └──────────────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────────────┴──────────────────────────────────────────────────────────────┘
```

---

## Screen 17: Board Deck Studio (`17_board_export.py`)

### Layout Wireframe
```
┌─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│ 📑 BOARD DECK STUDIO: Automated PowerPoint Executive Generator                                                              │
│ Target Company: [ Infosys Limited ▼ ]  |  Output Format: [ 📊 16:9 Widescreen (.pptx) ]                                     │
├──────────────────────────────────────────────────────────────┬──────────────────────────────────────────────────────────────┤
│ 🗂️ SELECT TOPICS TO INCLUDE (13 Econometric Topics)          │ 🖼️ LIVE SLIDE PREVIEW CAROUSEL                               │
│ [✓] Slide 1: Executive KPI & Leverage Summary                │ ┌──────────────────────────────────────────────────────────┐ │
│ [✓] Slide 2: Peer Benchmarking (IT Sector vs Mature Stage)   │ │  INFOSYS LIMITED — BOARD OF DIRECTORS BRIEFING           │ │
│ [✓] Slide 3: Life-Stage Trajectory & Dickinson Validation    │ │  Slide 2: Capital Structure vs IT Industry Peers         │ │
│ [✓] Slide 4: Determinant Sensitivity (Prof vs Tangibility)   │ │  ┌───────────────┬─────────────────────────────────────┐ │ │
│ [✓] Slide 5: COVID-19 Resilience & Post-IBC Performance      │ │  │ Radar Chart   │ • Zero Net Debt Strategy            │ │ │
│ [ ] Slide 6: GMM Speed of Adjustment Model                   │ │  │ ▅▆▇█▇▆        │ • Profitability ROA: 28.6% (Top 5%) │ │ │
│ [✓] Slide 7: AI Copilot Executive Summary & Recommendations  │ │  └───────────────┴─────────────────────────────────────┘ │ │
│                                                              │ └──────────────────────────────────────────────────────────┘ │
│ [ ⚡ Generate Complete 8-Slide PowerPoint Presentation (.pptx) 📥 ]                                                          │
└─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## Screen 19: AI Financial Assistant Studio (`19_ai_assistant.py`)

### Layout Wireframe & Component Breakdown
```
┌─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│ 🤖 AI FINANCIAL COPILOT & RESEARCH CANVAS                                                                                   │
├───────────────────────────────────────┬─────────────────────────────────────────────────────────────────────────────────────┤
│ 🗂️ RESEARCH THREADS & MEMORY          │ 💬 CONVERSATIONAL RESEARCH STUDIO                                                   │
│ ┌───────────────────────────────────┐ │ ┌─────────────────────────────────────────────────────────────────────────────────┐ │
│ │ ➕ New Investigation              │ │ │ 👤 User: What is the mean leverage for Maturity-stage firms?                    │ │
│ ├───────────────────────────────────┤ │ └─────────────────────────────────────────────────────────────────────────────────┘ │
│ │ 📌 Pinned Threads                 │ │ ┌─────────────────────────────────────────────────────────────────────────────────┐ │
│ │ • Reliance Life-Stage Shift       │ │ │ 🤖 AI Copilot                                [ 🏷️ Latest (2001-2025) · 401 Firms ]│ │
│ │ • System GMM λ (38.4%/yr)         │ │ │ The mean financial leverage for firms in the 🟣 Mature stage is:                │ │
│ ├───────────────────────────────────┤ │ │                                                                                 │ │
│ │ 🕒 Recent (Today, 06:29 UTC)      │ │ │ ┌─────────────────────────────────────────────────────────────────────────────┐ │ │
│ │ • Maturity Stage Leverage         │ │ │ │  📊 18.8%  (Book Debt / Total Assets)            [ ───●──────── 42nd Pct ]  │ │ │
│ │ • COVID Debt Buffering            │ │ │ │  🟣 Mature Stage Benchmark (176 Firms)           Δ -3.2pp vs Growth Stage   │ │ │
│ └───────────────────────────────────┘ │ │ └─────────────────────────────────────────────────────────────────────────────┘ │ │
│                                       │ │                                                                                 │ │
│ ⚙️ CONTEXT TOKEN GAUGE                │ │ 💡 Theoretical Mechanism:                                                       │ │
│ [■■■■□□] 4 / 6 Turns (2,410 Tokens)   │ │ Mature firms accumulate substantial internal retained earnings, reducing demand │ │
│                                       │ │ for external debt (Pecking Order Hypothesis).                                   │ │
│ ⚙️ ACTIVE GROUNDING SCOPE             │ │                                                                                 │ │
│ • Panel: (2001-25)_April26            │ │ 🎓 Literature Reference: [🎓 Myers & Majluf (1984)]  [🎓 Dickinson (2011)]       │ │
│ • Mode: [ 🎓 Researcher ▼ ]           │ │                                                                                 │ │
│ • Backend: [ ⚡ Gemini 1.5 Pro ▼ ]    │ │ 🔍 Data Provenance: [ 📋 Scoped SQLite View (v_active_fin) · 14ms · 176 Rows ▼ ]│ │
│ • Status: 🟢 SQLite Read-Only View    │ │ ───────────────────────────────────────────────────────────────────────────────│ │
│                                       │ │ [ 📋 Copy Markdown ]  [ 💾 Export Report ]  [ 🔄 Retry ]  │ ⚡ Gemini 1.5 · 3.4s│ │
│                                       │ └─────────────────────────────────────────────────────────────────────────────────┘ │
│                                       │ 💡 Continue Exploring (Click to run):                                               │ │
│                                       │ ┌─────────────────────────────────┐ ┌───────────────────────────┐ ┌───────────────┐ │ │
│                                       │ │ 📊 Compare Across 5 Stages  ➔   │ │ ⚖️ Pecking Order vs Trade-Off➔ │ 🏭 By Sector➔ │ │ │
│                                       │ └─────────────────────────────────┘ └───────────────────────────┘ └───────────────┘ │ │
├───────────────────────────────────────┴─────────────────────────────────────────────────────────────────────────────────────┤
│ ⌨️ PROMPT COCKPIT                                                                                                           │
│ [ 📎 Active Filters: Energy · 2001-2025 ]  [ 🎓 Citations: ON ]                                                             │
│ [ Ask any question about determinants, p-values, or companies...                                                      ] [ 🚀 ]│
└─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## Screen 4 & 16: Bulk Upload, Activity Log & Settings (`4_bulk_upload.py`, `16_admin_activity.py`, `6_settings.py`)

### Layout Wireframe
```
┌─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│ ⚙️ SYSTEM SETTINGS, DATA PIPELINES & AUDIT FEED                                                                             │
├──────────────────────────────────────────────────────────────┬──────────────────────────────────────────────────────────────┤
│ 📤 BULK DATASET INGESTION & CMIE API SYNC                    │ 📜 REAL-TIME AUDIT LOG & TELEMETRY                           │
│ ┌──────────────────────────────────────────────────────────┐ │ ┌──────────────────────────────────────────────────────────┐ │
│ │ 📁 Drag & Drop CSV / STATA .dta panel extract here       │ │ │ 🟢 11:42 UTC · Prof. Bhatia · Visited AI Assistant (P19) │ │
│ │    [ Browse Local Files ]                                │ │ │ 🟢 11:40 UTC · Prof. Bhatia · Switched Panel to 'run3'   │ │
│ │ [✓] 23 Canonical Columns Detected                        │ │ │ 🟢 11:38 UTC · Prof. Bhatia · Downloaded Board Deck .pptx│ │
│ │ [✓] 401 Unique Identifiers Validated                     │ │ │ 🟢 11:35 UTC · System · 344 Automated Tests Passed       │ │
│ │ [ 🚀 Commit to SQLite Vintage: cmie_2025 ]               │ │ └──────────────────────────────────────────────────────────┘ │
│ └──────────────────────────────────────────────────────────┘ │                                                              │
└─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┘
```
