"""
Interaction Effects models for the LifeCycle Leverage Dashboard.

Two analysis modes:
  1. run_cross_term_ols     — Profitability × Tangibility cross-term added to the base OLS.
  2. run_stage_moderation_ols — Life-stage dummies × profitability / tangibility interaction terms
                               in one pooled OLS to produce per-stage marginal effects.

Both use HC1 robust standard errors and mean-centre continuous interaction variables.
Pinned to thesis panel at the page level; these functions are panel-agnostic.
"""

import numpy as np
import pandas as pd
import statsmodels.api as sm
from scipy import stats

from .base import prepare_panel, DEFAULT_Y_COL, DEFAULT_X_COLS

# Must match helpers.STAGE_ORDER — duplicated here to keep models layer clean.
_STAGE_ORDER = [
    "Startup", "Growth", "Maturity",
    "Shakeout1", "Shakeout2", "Shakeout3",
    "Decline", "Decay",
]

_CONTROLS = ["tax", "log_size", "tax_shield", "dividend"]


def _sig_stars(p: float) -> str:
    if p < 0.01:
        return "***"
    if p < 0.05:
        return "**"
    if p < 0.10:
        return "*"
    return ""


def _build_coef_table(result) -> pd.DataFrame:
    """Construct a coefficient table matching the project-wide schema."""
    ci = result.conf_int()
    return pd.DataFrame({
        "Variable": result.params.index,
        "Coefficient": result.params.values,
        "Std Error": result.bse.values,
        "t-stat": result.tvalues.values,
        "p-value": result.pvalues.values,
        "CI Lower": ci[0].values,
        "CI Upper": ci[1].values,
    })


# ── Model 1: Cross-Term ────────────────────────────────────────────────────────

def run_cross_term_ols(df: pd.DataFrame, center: bool = True) -> dict:
    """
    Pooled OLS with a Profitability × Tangibility interaction term (HC1 robust SEs).

    Both variables are mean-centred before multiplication so that:
    - The main-effect coefficients are interpretable at the mean of each variable.
    - Multicollinearity from the interaction term is reduced.

    Returns
    -------
    dict with keys:
      coef_table      DataFrame [Variable, Coefficient, Std Error, t-stat, p-value, CI Lower, CI Upper]
      r_squared       float
      adj_r_squared   float
      f_stat          float
      f_pvalue        float
      n_obs           int
      n_firms         int
      centered_at     dict {var: mean} — values used for centering
      result_obj      statsmodels RegressionResultsWrapper
      panel           prepared DataFrame (MultiIndex company_code/year, centred cols added)
    """
    panel, y_col, _ = prepare_panel(
        df, y_col=DEFAULT_Y_COL, x_cols=DEFAULT_X_COLS,
        entity="company_code", time="year",
    )

    panel = panel.copy()

    if center:
        prof_mean = panel["profitability"].mean()
        tang_mean = panel["tangibility"].mean()
        panel["prof_c"] = panel["profitability"] - prof_mean
        panel["tang_c"] = panel["tangibility"] - tang_mean
        centered_at = {"profitability": prof_mean, "tangibility": tang_mean}
    else:
        panel["prof_c"] = panel["profitability"]
        panel["tang_c"] = panel["tangibility"]
        centered_at = {}

    panel["prof_c_x_tang_c"] = panel["prof_c"] * panel["tang_c"]

    x_cols_model = ["prof_c", "tang_c", "prof_c_x_tang_c"] + _CONTROLS

    y = panel[y_col]
    X = sm.add_constant(panel[x_cols_model])
    result = sm.OLS(y, X).fit(cov_type="HC1")

    coef_table = _build_coef_table(result)

    _label_map = {
        "const": "Intercept",
        "prof_c": "Profitability (centred)",
        "tang_c": "Tangibility (centred)",
        "prof_c_x_tang_c": "Profitability × Tangibility",
        "tax": "Tax Rate",
        "log_size": "Log Firm Size",
        "tax_shield": "Tax Shield",
        "dividend": "Dividend",
    }
    coef_table["Variable"] = coef_table["Variable"].map(
        lambda v: _label_map.get(v, v)
    )

    return {
        "coef_table": coef_table,
        "r_squared": result.rsquared,
        "adj_r_squared": result.rsquared_adj,
        "f_stat": result.fvalue,
        "f_pvalue": result.f_pvalue,
        "n_obs": int(result.nobs),
        "n_firms": panel.index.get_level_values(0).nunique(),
        "centered_at": centered_at,
        "result_obj": result,
        "panel": panel,
    }


def simple_slopes(cross_term_result: dict, n_points: int = 60) -> pd.DataFrame:
    """
    Generate simple-slope predictions for the cross-term model.

    Varies profitability across its 5th–95th percentile range while fixing tangibility
    at three levels (mean−1SD, mean, mean+1SD) and all controls at their means.

    Returns a DataFrame with columns [profitability, tang_level, predicted_leverage]
    where tang_level is a human-readable label string.
    """
    result = cross_term_result["result_obj"]
    panel = cross_term_result["panel"]
    params = result.params
    prof_mean = cross_term_result["centered_at"].get("profitability", 0.0)

    prof_c_range = np.linspace(
        panel["prof_c"].quantile(0.05),
        panel["prof_c"].quantile(0.95),
        n_points,
    )
    tang_sd = panel["tang_c"].std()
    tang_levels = {
        "Low (mean−1SD)": -tang_sd,
        "Mean": 0.0,
        "High (mean+1SD)": tang_sd,
    }
    ctrl_means = {c: float(panel[c].mean()) for c in _CONTROLS}

    rows = []
    ctrl_contribution = sum(params[c] * ctrl_means[c] for c in _CONTROLS)
    for level_label, tang_c_val in tang_levels.items():
        for prof_c_val in prof_c_range:
            pred = (
                params["const"]
                + params["prof_c"] * prof_c_val
                + params["tang_c"] * tang_c_val
                + params["prof_c_x_tang_c"] * prof_c_val * tang_c_val
                + ctrl_contribution
            )
            rows.append({
                "profitability": prof_c_val + prof_mean,
                "tang_level": level_label,
                "predicted_leverage": float(pred),
            })

    return pd.DataFrame(rows)


# ── Model 2: Stage Moderation ──────────────────────────────────────────────────

def run_stage_moderation_ols(
    df: pd.DataFrame,
    reference_stage: str = "Maturity",
    center: bool = True,
) -> dict:
    """
    Pooled OLS with stage-dummy × profitability and stage-dummy × tangibility interaction
    terms (HC1 robust SEs).

    The reference stage (default: Maturity) is absorbed into the intercept — its marginal
    effects equal the main-effect coefficients β_prof and β_tang.  For all other stages k:
      dLeverage/dProfitability|stage=k = β_prof + γ_k
      dLeverage/dTangibility|stage=k   = β_tang + δ_k

    Standard errors of marginal effects are computed via the delta method:
      Var(β + γ_k) = Var(β) + Var(γ_k) + 2·Cov(β, γ_k)

    Returns
    -------
    dict with keys:
      coef_table    DataFrame — full regression coefficients
      marginal_df   DataFrame [stage, variable, marginal_effect, se, t, pval, sig]
      r_squared     float
      adj_r_squared float
      f_stat / f_pvalue
      n_obs / n_firms
      centered_at   dict {var: mean}
    """
    panel, y_col, _ = prepare_panel(
        df, y_col=DEFAULT_Y_COL, x_cols=DEFAULT_X_COLS,
        entity="company_code", time="year",
    )

    # Merge life_stage back (prepare_panel drops it as non-numeric)
    panel_r = panel.reset_index()
    stage_lookup = (
        df[["company_code", "year", "life_stage"]]
        .dropna(subset=["life_stage"])
        .drop_duplicates(subset=["company_code", "year"])
    )
    panel_r = panel_r.merge(stage_lookup, on=["company_code", "year"], how="inner")
    panel_r = panel_r.dropna(subset=["life_stage"])
    panel_r = panel_r.set_index(["company_code", "year"])

    if center:
        prof_mean = panel_r["profitability"].mean()
        tang_mean = panel_r["tangibility"].mean()
        panel_r["prof_c"] = panel_r["profitability"] - prof_mean
        panel_r["tang_c"] = panel_r["tangibility"] - tang_mean
        centered_at = {"profitability": prof_mean, "tangibility": tang_mean}
    else:
        panel_r["prof_c"] = panel_r["profitability"]
        panel_r["tang_c"] = panel_r["tangibility"]
        centered_at = {}

    non_ref = [s for s in _STAGE_ORDER if s != reference_stage]
    present_stages = set(panel_r["life_stage"].unique())
    non_ref = [s for s in non_ref if s in present_stages]

    # Stage main-effect dummies
    for s in non_ref:
        panel_r[f"stage_{s}"] = (panel_r["life_stage"] == s).astype(float)

    # Interaction terms
    for s in non_ref:
        panel_r[f"{s}_x_prof_c"] = panel_r[f"stage_{s}"] * panel_r["prof_c"]
        panel_r[f"{s}_x_tang_c"] = panel_r[f"stage_{s}"] * panel_r["tang_c"]

    x_cols_model = (
        [f"stage_{s}" for s in non_ref]
        + ["prof_c", "tang_c"]
        + [f"{s}_x_prof_c" for s in non_ref]
        + [f"{s}_x_tang_c" for s in non_ref]
        + _CONTROLS
    )

    y = panel_r[y_col]
    X = sm.add_constant(panel_r[x_cols_model])
    result = sm.OLS(y, X).fit(cov_type="HC1")

    coef_table = _build_coef_table(result)
    # Human-readable variable labels
    def _friendly(v):
        if v == "const":
            return "Intercept"
        if v == "prof_c":
            return "Profitability (centred)"
        if v == "tang_c":
            return "Tangibility (centred)"
        if v.startswith("stage_"):
            return f"Stage: {v[6:]}"
        if v.endswith("_x_prof_c"):
            return f"{v[:-9]} × Profitability"
        if v.endswith("_x_tang_c"):
            return f"{v[:-9]} × Tangibility"
        return v
    coef_table["Variable"] = coef_table["Variable"].map(_friendly)

    # ── Marginal effects via delta method ─────────────────────────────────────
    cov = result.cov_params()
    params = result.params
    df_resid = result.df_resid

    all_stages = [s for s in _STAGE_ORDER if s in present_stages]
    rows = []
    for stage in all_stages:
        for var_label, base_col, int_tmpl in [
            ("Profitability", "prof_c", "{s}_x_prof_c"),
            ("Tangibility",   "tang_c", "{s}_x_tang_c"),
        ]:
            int_col = int_tmpl.format(s=stage)

            if stage == reference_stage:
                me = float(params[base_col])
                se = float(np.sqrt(cov.loc[base_col, base_col]))
            else:
                me = float(params[base_col] + params[int_col])
                se = float(np.sqrt(
                    cov.loc[base_col, base_col]
                    + cov.loc[int_col, int_col]
                    + 2.0 * cov.loc[base_col, int_col]
                ))

            t_val = me / se if se > 0 else np.nan
            p_val = float(2 * stats.t.sf(abs(t_val), df=df_resid)) if not np.isnan(t_val) else np.nan
            rows.append({
                "stage": stage,
                "variable": var_label,
                "marginal_effect": me,
                "se": se,
                "t": t_val,
                "pval": p_val,
                "sig": _sig_stars(p_val) if not np.isnan(p_val) else "",
            })

    marginal_df = pd.DataFrame(rows)

    return {
        "coef_table": coef_table,
        "marginal_df": marginal_df,
        "r_squared": result.rsquared,
        "adj_r_squared": result.rsquared_adj,
        "f_stat": result.fvalue,
        "f_pvalue": result.f_pvalue,
        "n_obs": int(result.nobs),
        "n_firms": panel_r.index.get_level_values(0).nunique(),
        "centered_at": centered_at,
    }
