"""Econometric Deconstruction & Plain-English Explanation Engine.

Translates Stata commands and estimation outputs into structured academic
and executive breakdowns across four core dimensions:
1. Intent: Primary empirical and causal objective.
2. Identification: Strategy used to isolate causal variation.
3. Inference: Standard error adjustments and asymptotic properties.
4. Economic Theory: Grounding in capital structure literature and Indian manufacturing.
"""

from typing import Dict, Any


def explain_stata_command(cmd_str: str, result: Dict[str, Any] = None) -> Dict[str, str]:
    """Generate structured plain-English econometric explanation for a Stata command."""
    low = (cmd_str or "").lower().strip()

    if low.startswith("ivregress"):
        return {
            "intent": "Execute an IMPLEMENTED_UNVERIFIED Two-Stage Least Squares (2SLS) specification for leverage.",
            "identification": "The requested instruments are used computationally, but relevance, exogeneity, and exclusion restrictions require independent empirical justification.",
            "inference": "Reports robust 2SLS estimates and available diagnostics; successful execution does not establish causal validity.",
            "economic_theory": "Provides an IV-based sensitivity analysis for capital-structure relationships without claiming validated causal effects.",
        }

    if low.startswith("test"):
        return {
            "intent": "Conduct joint or single hypothesis test (Wald test) on parameter estimates following model estimation.",
            "identification": "Evaluates linear equality constraints (e.g. H0: beta = 0) against the unconstrained asymptotic variance-covariance matrix of estimators.",
            "inference": "Uses finite-sample Wald F-statistic or chi-squared distribution with degrees of freedom equal to the number of linear restrictions.",
            "economic_theory": "Tests whether firm profitability or collateral tangibility exerts a statistically discernable effect on corporate debt ratios at conventional significance thresholds.",
        }

    if low.startswith("predict"):
        return {
            "intent": "Generate post-estimation fitted linear predictions (xb) or model residuals (e) for diagnostic analysis.",
            "identification": "Applies estimated parameter vector beta_hat to individual firm-year covariate vectors to compute conditional expectations E[Y|X].",
            "inference": "Useful for detecting influential leverage outliers, heteroskedasticity patterns, or assessing model out-of-sample fit.",
            "economic_theory": "Quantifies the gap between predicted target leverage and observed borrowing, identifying over-leveraged and under-leveraged firms across corporate life stages.",
        }

    if low.startswith("winsor2") or low.startswith("winsor"):
        return {
            "intent": "Clean extreme outlier values by clamping continuous panel covariates at specified percentiles (default 1st and 99th).",
            "identification": "Reduces high-leverage influence points and data recording anomalies without dropping observations or introducing attrition bias.",
            "inference": "Prevents heavy-tailed leverage and profitability shocks from distorting OLS and panel estimator variance-covariance matrices.",
            "economic_theory": "Standard empirical discipline in CMIE Prowess empirical accounting and finance studies (Rajan & Zingales 1995, Frank & Goyal 2009).",
        }

    if low.startswith("xtreg") and ", fe" in low:
        return {
            "intent": "Estimate within-firm panel fixed effects regression of debt on corporate financial determinants.",
            "identification": "Within-firm de-meaning transformation purges all time-invariant unobserved firm heterogeneity (management quality, firm culture, founding lineage).",
            "inference": "Standard errors clustered at firm level, robust to heteroskedasticity and arbitrary within-firm serial correlation across time.",
            "economic_theory": "Directly tests Pecking Order (negative profitability beta) versus Trade-Off Theory (positive tangibility beta) on Indian corporate panels.",
        }

    if low.startswith("xtreg") and ", re" in low:
        return {
            "intent": "Estimate random effects Generalized Least Squares (GLS) matrix on panel data.",
            "identification": "Assumes unobserved firm-specific effects are strictly uncorrelated with observed explanatory variables (E[c_i | X_it] = 0).",
            "inference": "GLS quasidemeaning balances between-firm and within-firm variance, yielding efficient estimates under the orthogonality assumption.",
            "economic_theory": "Permits estimation of time-invariant industry and group effects, benchmarked against Fixed Effects via the Hausman specification test.",
        }

    if low.startswith("hausman"):
        return {
            "intent": "Test fixed effects consistency against random effects efficiency (H0: difference in coefficients not systematic).",
            "identification": "Contrasts consistent FE coefficients with efficient RE coefficients under the null of zero correlation between unobserved effects and regressors.",
            "inference": "Asymptotic chi-squared test with degrees of freedom equal to the rank of the differenced covariance matrix.",
            "economic_theory": "Determines whether firm-level unobserved endowments bias cross-sectional leverage regressions in Indian manufacturing.",
        }

    if low.startswith("xttest0"):
        return {
            "intent": "Breusch and Pagan Lagrangian multiplier test for random effects (H0: Var(u_i) = 0).",
            "identification": "Tests presence of unobserved individual-specific variance against standard pooled OLS.",
            "inference": "Distributed asymptotically as chi-squared with 1 degree of freedom.",
            "economic_theory": "Demonstrates that panel techniques are statistically indispensable compared to pooled cross-sectional regressions.",
        }

    if low.startswith("xtserial"):
        return {
            "intent": "Wooldridge test for first-order autocorrelation in panel-data models.",
            "identification": "Regresses differenced panel residuals on their first lag to detect intra-firm temporal persistence.",
            "inference": "F-distributed test robust to conditional heteroskedasticity.",
            "economic_theory": "Confirms presence of serial persistence in firm debt decisions, justifying dynamic models or clustered standard errors.",
        }

    # General exploratory fallback
    return {
        "intent": "Exploratory econometric examination of continuous and categorical panel covariates.",
        "identification": "Sample summary distributions across cross-sectional manufacturing units and longitudinal periods.",
        "inference": "Parametric and non-parametric summary metrics (mean, standard deviation, percentiles, skewness).",
        "economic_theory": "Establishes empirical baselines for Indian manufacturing leverage distributions across 2001–2025.",
    }
