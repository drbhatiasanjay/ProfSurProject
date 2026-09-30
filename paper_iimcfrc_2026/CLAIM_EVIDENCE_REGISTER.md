# Claim-Evidence Ledger: LifeStageDebtAI (IIMCFRC 2026)

This ledger establishes strict provenance for every empirical number and platform capability claimed in the submission manuscript.

| Manuscript Section & Claim | Source Artifact / Thesis Evidence | Verification Status |
| :--- | :--- | :---: |
| **Section 4: Baseline Sample Count**<br>4,218 Indian listed firm-years (2004–2020) | `DETERMINANTS OF CAPITAL STRUCTURE OVER CORPORATE LIFE STAGES.docx` (Chapter 4 & 5 sample summary) and `determinantsCapitalStructure05.docx` (Table 3). | **VERIFIED** |
| **Section 4: Fixed-Effects Coefficients**<br>TANG: 0.184 (0.024), PROF: -0.312 (0.038), SIZE: 0.042 (0.008), MB: -0.015 (0.006), NDTS: -0.108 (0.057) | `DETERMINANTS OF CAPITAL STRUCTURE OVER CORPORATE LIFE STAGES.docx` (Table 5.10, Model 2 Fixed Effects) & `determinantsCapitalStructure05.docx` (Table 3 Model 2). | **VERIFIED** |
| **Section 4: Life Stage Dummies**<br>Growth: 0.038 (0.016), Mature: 0.054 (0.015), Shake-Out: 0.021 (0.019), Decline: 0.047 (0.022) | `DETERMINANTS OF CAPITAL STRUCTURE OVER CORPORATE LIFE STAGES.docx` (Table 5.10 Model 2) with Startup/Intro as omitted reference category. | **VERIFIED** |
| **Section 2: Dickinson 8-Pattern Taxonomy**<br>Signs (+/-) of CFO, CFI, CFF mapping into 5 stages | Dickinson (2011, *The Accounting Review*) and Kumar (2025 PhD Thesis Chapter 4). | **VERIFIED** |
| **Section 3: Stata Studio Workbench**<br>Interactive execution of `xtset`, `xtreg`, `regress` with persistent session model registry | `pages/23_stata_studio.py`, `pages/25_stata_studio_v2.py`, and `models/stata_engine.py` in `ProfSurProject`. | **VERIFIED** |
| **Section 5: TreeSHAP Feature Attribution**<br>Profitability as top negative driver, tangibility collateral threshold | `Bhatia_Kumar_LifeStageDebtAI_IFC2026.docx` (Table 4) and XGBoost SHAP summary plots in project archives. | **VERIFIED** |
| **Section 3: Anti-Hallucination Guardrails**<br>Model context injection via pre-formatted JSON parameter structures | `pages/23_stata_studio.py` and session prompt payload contracts in `models/`. | **VERIFIED** |
