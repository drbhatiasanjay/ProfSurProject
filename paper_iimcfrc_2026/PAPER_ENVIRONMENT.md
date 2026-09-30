# Environment & Anti-AI Tone Directives: LifeStageDebtAI Academic Paper
# Target: IIM Calcutta Finance Research Conference (IIMCFRC) 2026
# Authors: Dr. Sanjay Bhatia & Prof. Surendra Kumar

---

## 1. Project Overview & Worktree Context
- **Workspace/Branch**: `paper/iimcfrc-2026-lifestagedebtai` under `ProfSurProject`
- **Paper Title (Working)**: *LifeStageDebtAI: Dynamic Capital Structure and Debt Capacity Across Corporate Life Cycles via Double Machine Learning and Explainable Econometrics*
- **Target Venue**: IIM Calcutta Finance Research Conference (IIMCFRC) 2026 (Joka, Kolkata)
- **Theoretical Benchmark**: Prof. Surendra Kumar (2025 PhD Thesis, Dept. of Finance & Business Economics, University of Delhi) on *Determinants of Capital Structure Over Corporate Life Stages*.

---

## 2. Mandatory Writing Rules (The 5 Anti-AI Humanization Principles)

### Rule 1: Strict Ban on AI Vocabulary & Clichés
The following words, phrases, and structures are strictly **BANNED** from all paper text:
- **Banned Words**: *delve, tapestry, beacon, testament to, pivotal, realm, vibrant, crucial, foster, harness, leverage (as a verb for 'use'), multifaceted, multifaceted landscape, game-changer, seamless, bedrock, underscore (excessive use), plethora*.
- **Banned Transitional Formulae**: *"In today's fast-paced/dynamic world...", "It is important to note that...", "Having discussed X, we now delve into Y...", "Not only X, but also Y..."* (when used formulaically).
- **Banned Stylistic Patterns**: Rule-of-three adjective strings (*"robust, scalable, and versatile"*), superficial rhetorical questions, and hollow introductory summaries.

### Rule 2: Sentence Rhythm & Cadence Variance ("Burstiness")
- Do NOT generate monotonous compound sentences of equal length (20–25 words each).
- Alternate between complex, mathematically precise sentences and short, punchy empirical assertions.
- Example: *"Dynamic panel models face instrument proliferation when time periods expand. System GMM addresses this through collapsed instrument matrices. Yet, non-linearities remain uncaptured."*

### Rule 3: Concrete Empirical Data Over Vague Adjectives
- Never write *"LifeStageDebtAI significantly improves leverage prediction accuracy."*
- Always write: *"Across 10-fold cross-validation on 4,218 NSE/BSE listed firm-years (2004–2024), LifeStageDebtAI reduces out-of-sample Root Mean Squared Error (RMSE) to 0.038, a 26.3% error reduction relative to the two-step Blundell-Bond System GMM baseline (RMSE 0.052)."*

### Rule 4: Authentic Indian Institutional & Regulatory Realities
All policy discussions and empirical interpretations must ground themselves in genuine Indian corporate finance institutions:
1. **Insolvency and Bankruptcy Code (IBC 2016)** and NCLT resolution dynamics.
2. **RBI Prudential Framework on Resolution of Stressed Assets** (June 7, 2019 Circular).
3. **SEBI (Listing Obligations and Disclosure Requirements - LODR)** corporate governance and related-party disclosure mandates.
4. **Asset Quality Review (AQR 2015)** and public sector bank bad-loan cleanups.

### Rule 5: Direct Academic Authority & Balanced Skepticism
- Write with the voice of seasoned financial economists (Dr. Sanjay Bhatia & Prof. Surendra Kumar).
- Acknowledge econometric trade-offs, potential survivorship bias in CMIE Prowess data, instrument weakness in GMM, and boundary conditions of tree-based vs. neural estimators.

---

## 3. Econometric & Methodological Standards

1. **Life Cycle Identification**: Follow **Dickinson (2011)** operating, investing, and financing cash flow sign profiles as the primary identification strategy, benchmarked against Anthony & Ramesh (1992).
2. **Dynamic Adjustment Speed**: Report the speed of adjustment ($\lambda = 1 - lpha$) toward target leverage across individual life stages (Introduction, Growth, Mature, Shake-out, Decline).
3. **Causal Machine Learning**: Use **Double/Debiased Machine Learning (DML - Chernozhukov et al., 2018)** to test treatment effects of stage transitions on borrowing costs, resolving confounding without ad-hoc functional form assumptions.
4. **Explainable AI (XAI)**: Feature attributions must be computed via **TreeSHAP** and reported in economically meaningful basis-point changes or leverage percentage points.

---

## 4. Citation & Reference Integrity

- Never fabricate DOIs, authors, or publication years.
- All core references must match the established corporate finance canon:
  - Modigliani & Miller (1958, 1963), Kraus & Litzenberger (1973), Jensen & Meckling (1976), Myers & Majluf (1984).
  - Flannery & Rangan (2006), Dickinson (2011), Arellano & Bond (1991), Blundell & Bond (1998), Chernozhukov et al. (2018).
  - Indian context: Kumar & Dawar / Gupta (2025), Bhaduri (2002), Mukherjee & Mahakud (2012).
