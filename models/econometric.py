"""
Tier 1 Econometric Models — Thesis replication.
OLS, Fixed Effects, Random Effects, System GMM, Hausman Test, ANOVA.
"""

import numpy as np
import pandas as pd
import statsmodels.api as sm
from scipy import stats
from .base import prepare_panel, DEFAULT_X_COLS, DEFAULT_Y_COL


def run_pooled_ols(df, y_col=DEFAULT_Y_COL, x_cols=None, entity="company_code", time="year"):
    """
    Pooled OLS with heteroskedasticity-robust (HC1) standard errors.
    Returns dict with coefficients, diagnostics, and the result object.
    """
    if x_cols is None:
        x_cols = DEFAULT_X_COLS

    panel, y_col, x_cols = prepare_panel(df, y_col, x_cols, entity, time)
    y = panel[y_col]
    X = sm.add_constant(panel[x_cols])

    model = sm.OLS(y, X)
    result = model.fit(cov_type="HC1")

    coef_table = pd.DataFrame({
        "Variable": result.params.index,
        "Coefficient": result.params.values,
        "Std Error": result.bse.values,
        "t-stat": result.tvalues.values,
        "p-value": result.pvalues.values,
        "CI Lower": result.conf_int()[0].values,
        "CI Upper": result.conf_int()[1].values,
    })

    return {
        "type": "Pooled OLS",
        "coef_table": coef_table,
        "r_squared": result.rsquared,
        "adj_r_squared": result.rsquared_adj,
        "f_stat": result.fvalue,
        "f_pvalue": result.f_pvalue,
        "n_obs": int(result.nobs),
        "n_firms": panel.index.get_level_values(0).nunique(),
        "aic": result.aic,
        "bic": result.bic,
        "result_obj": result,
        "residuals": result.resid,
        "fitted": result.fittedvalues,
    }


def run_fixed_effects(df, y_col=DEFAULT_Y_COL, x_cols=None, entity="company_code", time="year"):
    """
    Panel Fixed Effects model using linearmodels.
    Controls for firm-specific unobserved heterogeneity.
    """
    from linearmodels.panel import PanelOLS

    if x_cols is None:
        x_cols = DEFAULT_X_COLS

    panel, y_col, x_cols = prepare_panel(df, y_col, x_cols, entity, time)
    y = panel[y_col]
    X = sm.add_constant(panel[x_cols])

    model = PanelOLS(y, X, entity_effects=True)
    result = model.fit(cov_type="clustered", cluster_entity=True)

    coef_table = pd.DataFrame({
        "Variable": result.params.index,
        "Coefficient": result.params.values,
        "Std Error": result.std_errors.values,
        "t-stat": result.tstats.values,
        "p-value": result.pvalues.values,
    })

    return {
        "type": "Fixed Effects",
        "coef_table": coef_table,
        "r_squared": result.rsquared,
        "r_squared_within": result.rsquared_within,
        "f_stat": result.f_statistic.stat,
        "f_pvalue": result.f_statistic.pval,
        "n_obs": int(result.nobs),
        "n_firms": int(result.entity_info.total),
        "result_obj": result,
        "residuals": result.resids,
        "fitted": result.fitted_values,
    }


def run_random_effects(df, y_col=DEFAULT_Y_COL, x_cols=None, entity="company_code", time="year"):
    """
    Panel Random Effects model using linearmodels (GLS estimation).
    """
    from linearmodels.panel import RandomEffects

    if x_cols is None:
        x_cols = DEFAULT_X_COLS

    panel, y_col, x_cols = prepare_panel(df, y_col, x_cols, entity, time)
    y = panel[y_col]
    X = sm.add_constant(panel[x_cols])

    model = RandomEffects(y, X)
    result = model.fit(cov_type="clustered", cluster_entity=True)

    coef_table = pd.DataFrame({
        "Variable": result.params.index,
        "Coefficient": result.params.values,
        "Std Error": result.std_errors.values,
        "t-stat": result.tstats.values,
        "p-value": result.pvalues.values,
    })

    return {
        "type": "Random Effects",
        "coef_table": coef_table,
        "r_squared": result.rsquared,
        "r_squared_within": result.rsquared_within,
        "n_obs": int(result.nobs),
        "n_firms": int(result.entity_info.total),
        "result_obj": result,
        "residuals": result.resids,
        "fitted": result.fitted_values,
    }


def run_hausman_test(fe_result, re_result):
    """
    Hausman specification test: FE vs RE.
    H0: RE is consistent and efficient (prefer RE).
    H1: RE is inconsistent (prefer FE).
    """
    fe_obj = fe_result["result_obj"]
    re_obj = re_result["result_obj"]

    # Get common coefficients (exclude constant)
    fe_coefs = fe_obj.params.drop("const", errors="ignore")
    re_coefs = re_obj.params.drop("const", errors="ignore")
    common = fe_coefs.index.intersection(re_coefs.index)

    b_fe = fe_coefs[common].values
    b_re = re_coefs[common].values
    diff = b_fe - b_re

    # Variance of difference
    v_fe = np.diag(fe_obj.cov.loc[common, common].values)
    v_re = np.diag(re_obj.cov.loc[common, common].values)
    v_diff = v_fe - v_re

    # Guard against negative variances
    v_diff = np.maximum(v_diff, 1e-10)

    chi2 = float(np.sum(diff ** 2 / v_diff))
    df = len(common)
    p_value = float(1 - stats.chi2.cdf(chi2, df))

    if p_value < 0.05:
        verdict = "Fixed Effects preferred (reject H0 at 5% level)"
        recommended = "Fixed Effects"
    else:
        verdict = "Random Effects preferred (cannot reject H0 at 5% level)"
        recommended = "Random Effects"

    return {
        "chi2": chi2,
        "df": df,
        "p_value": p_value,
        "verdict": verdict,
        "recommended": recommended,
    }


def run_breusch_pagan_lm(ols_result):
    """
    Breusch-Pagan Lagrange Multiplier test: Pooled OLS vs Random Effects.
    H0: No panel effects (OLS is adequate).
    H1: Panel effects exist (use RE or FE).
    """
    resid = ols_result["residuals"]
    result_obj = ols_result["result_obj"]

    # BP test from statsmodels
    from statsmodels.stats.diagnostic import het_breuschpagan
    X = result_obj.model.exog
    lm_stat, lm_pvalue, f_stat, f_pvalue = het_breuschpagan(resid, X)

    if lm_pvalue < 0.05:
        verdict = "Panel effects detected (reject Pooled OLS at 5% level)"
    else:
        verdict = "No significant panel effects (Pooled OLS adequate)"

    return {
        "lm_stat": float(lm_stat),
        "lm_pvalue": float(lm_pvalue),
        "f_stat": float(f_stat),
        "f_pvalue": float(f_pvalue),
        "verdict": verdict,
    }


def run_anova_by_stage(df, y_col=DEFAULT_Y_COL, stage_col="life_stage"):
    """
    One-way ANOVA: test if leverage differs significantly across life stages.
    Returns F-stat, p-value, and group means.
    """
    clean = df[[y_col, stage_col]].dropna()
    groups = [group[y_col].values for _, group in clean.groupby(stage_col)]

    f_stat, p_value = stats.f_oneway(*groups)

    group_stats = clean.groupby(stage_col)[y_col].agg(["mean", "std", "count"]).reset_index()
    group_stats.columns = ["Stage", "Mean", "Std Dev", "Count"]
    group_stats = group_stats.sort_values("Mean", ascending=False)

    if p_value < 0.05:
        verdict = f"Significant difference across stages (F={f_stat:.2f}, p={p_value:.4f})"
    else:
        verdict = f"No significant difference across stages (F={f_stat:.2f}, p={p_value:.4f})"

    return {
        "f_stat": float(f_stat),
        "p_value": float(p_value),
        "group_stats": group_stats,
        "verdict": verdict,
    }


def run_all_and_compare(df, y_col=DEFAULT_Y_COL, x_cols=None, entity="company_code", time="year"):
    """
    Run OLS, FE, RE + Hausman + BP-LM. Auto-recommend the best model.
    Returns all results plus a comparison summary.
    """
    ols = run_pooled_ols(df, y_col, x_cols, entity, time)
    fe = run_fixed_effects(df, y_col, x_cols, entity, time)
    re = run_random_effects(df, y_col, x_cols, entity, time)
    hausman = run_hausman_test(fe, re)
    bp = run_breusch_pagan_lm(ols)

    comparison = pd.DataFrame({
        "Model": ["Pooled OLS", "Fixed Effects", "Random Effects"],
        "R-squared": [ols["r_squared"], fe["r_squared"], re["r_squared"]],
        "N Obs": [ols["n_obs"], fe["n_obs"], re["n_obs"]],
        "N Firms": [ols["n_firms"], fe["n_firms"], re["n_firms"]],
    })

    return {
        "ols": ols,
        "fe": fe,
        "re": re,
        "hausman": hausman,
        "bp_lm": bp,
        "comparison": comparison,
        "recommended": hausman["recommended"],
    }
