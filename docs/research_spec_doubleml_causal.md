# Double Machine Learning (DoubleML) & Advanced Causal Inference Specification

**Separate Research Specification - ProfSurProject (SW-24)**  
Status: Research & Architectural Contract (Not Implemented in Core Paper Path)  
Compliance: IIMCFRC 2026 Manuscript Isolation Guarantee

---

## 1. Motivation and Econometric Framework
Conventional panel data estimators (fixed effects, year fixed effects, IV-Proxies) assume a predetermined linear form for all control variables. However, in life-cycle debt dynamics, firm-specific controls (Revenue Growth, ROA, Tangibility, Size, Market-to-Book) may exhibit high-dimensional, non-linear, and interactive confounding effects on leverage decisions.

Double Machine Learning (Chernozhukov et al., 2018) resolves this by using flexible machine learning nuisance estimators while preserving square-root-N consistency and valid 95% confidence intervals for the structural treatment parameter.

---

## 2. Mathematical Formulation

### A. Partially Linear Regression (PLR) Model
For firm $i$ at year $t$:
$$Y_{it} = \theta D_{it} + h(X_{it}) + U_{it},   \quad \mathrm{E}[U_{it} \mid D_{it}, X_{it}] = 0$$
$$D_{it} = m(X_{it}) + V_{it},   \quad \mathrm{E}[V_{it} \mid X_{it}] = 0$$

Where:
- $Y_{it}$: Firm debt leverage ratio.
- $D_{it}$: Treatment variable (e.g., Life-Stage dichotomy or Marginal Corporate Tax Rate Cuts).
- $X_{it}$: High-dimensional control vector (Size, Profitability, Tangibility, MBAR, Dividend Payout).
- $h(X), m(X)$: Unknown nuisance functions estimated via Gradient Boosting (XGBoost/LightGBM), Random Forests, or ElasticNet.
- $\theta$: Structural causal marginal effect.

### B. Neyman Orthogonal Score & K-Fold Cross-Fitting
To prevent regularization bias from downstream ML fitting, the Neyman orthogonal score is employed:
$$\psi(W; \theta, \eta) = (Y - \ell(X) - \theta(D - m(X)))(D - m(X))$$

**Cross-Fitting Protocol** ($K=5$) splits the 8,677 panel observations by **firm-level clusters** rather than independent rows, preserving autocorrelation structure across time within firms.

---

## 3. Planned Dependencies and Integration Gates
1. **Library Requirements:** `doubleml`, `scikit-learn`, `xgboost`.
2. **Isolation Gate:** This method is not presented in the IISDR 2026 / IIMCFRC 2026 paper, which strictly uses within-estimator fixed effects with Driscoll-Kraay standard errors.
3. **Validation Tests:** Prior to shipping as an in-app page, a Stata parity test between Partially Linear Models and `ddml` Stata package must achieve $< 0.1\%$ tolerance on simulated data.
