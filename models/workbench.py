"""
Statistical Workbench — Formula engine for custom regression building.
Transforms, model fitting, post-estimation, esttab comparison.

This module does NOT call existing functions from models/econometric.py
because those hard-code prepare_panel() with fixed defaults. This module
accepts arbitrary DataFrames with arbitrary column names.
"""

import warnings
import numpy as np
import pandas as pd
import statsmodels.api as sm
from scipy import stats
from statsmodels.stats.outliers_influence import variance_inflation_factor
from uuid import uuid4


# ── Variable Transforms ──

def apply_transforms(df, specs, entity="company_code", time="year"):
    """
    Apply variable transformations to a DataFrame.

    specs = [
        {"type": "log", "var": "profitability"},           # -> ln_profitability
        {"type": "sq", "var": "profitability"},             # -> profitability_sq
        {"type": "sqrt", "var": "firm_size"},               # -> sqrt_firm_size
        {"type": "interaction", "var1": "profitability", "var2": "tangibility"},  # -> profitability_x_tangibility
        {"type": "lag", "var": "leverage", "order": 1},     # -> L1.leverage
        {"type": "lead", "var": "leverage", "order": 1},    # -> F1.leverage
        {"type": "diff", "var": "leverage"},                 # -> D.leverage
    ]

    Returns (transformed_df, new_column_names, warnings).
    """
    result = df.copy()
    new_cols = []
    warn_msgs = []

    for spec in specs:
        t = spec["type"]

        if t == "log":
            var = spec["var"]
            col_name = f"ln_{var}"
            vals = result[var].copy()
            n_neg = (vals <= 0).sum()
            if n_neg > 0:
                warn_msgs.append(
                    f"Log transform: {n_neg} non-positive values in '{var}' clipped to 1e-8"
                )
                vals = vals.clip(lower=1e-8)
            result[col_name] = np.log(vals)
            new_cols.append(col_name)

        elif t == "sq":
            var = spec["var"]
            col_name = f"{var}_sq"
            result[col_name] = result[var] ** 2
            new_cols.append(col_name)

        elif t == "sqrt":
            var = spec["var"]
            col_name = f"sqrt_{var}"
            vals = result[var].clip(lower=0)
            result[col_name] = np.sqrt(vals)
            new_cols.append(col_name)

        elif t == "interaction":
            var1, var2 = spec["var1"], spec["var2"]
            col_name = f"{var1}_x_{var2}"
            result[col_name] = result[var1] * result[var2]
            new_cols.append(col_name)

        elif t == "lag":
            var = spec["var"]
            order = spec.get("order", 1)
            col_name = f"L{order}.{var}"
            result = result.sort_values([entity, time])
            result[col_name] = result.groupby(entity)[var].shift(order)
            new_cols.append(col_name)

        elif t == "lead":
            var = spec["var"]
            order = spec.get("order", 1)
            col_name = f"F{order}.{var}"
            result = result.sort_values([entity, time])
            result[col_name] = result.groupby(entity)[var].shift(-order)
            new_cols.append(col_name)

        elif t == "diff":
            var = spec["var"]
            col_name = f"D.{var}"
            result = result.sort_values([entity, time])
            result[col_name] = result.groupby(entity)[var].diff()
            new_cols.append(col_name)

    return result, new_cols, warn_msgs


# ── Subsample Filtering ──

def apply_subsample_filter(df, conditions):
    """
    Safe parameterized filtering -- NO eval().

    conditions = [
        {"column": "profitability", "op": ">", "value": 0},
        {"column": "life_stage", "op": "in", "value": ["Growth", "Maturity"]},
        {"column": "year", "op": ">=", "value": 2010},
    ]

    Supported ops: >, <, >=, <=, ==, !=, in, not_in
    Returns filtered DataFrame.
    """
    result = df.copy()

    for cond in conditions:
        col = cond["column"]
        op = cond["op"]
        val = cond["value"]

        if col not in result.columns:
            continue

        if op == ">":
            result = result[result[col] > float(val)]
        elif op == "<":
            result = result[result[col] < float(val)]
        elif op == ">=":
            result = result[result[col] >= float(val)]
        elif op == "<=":
            result = result[result[col] <= float(val)]
        elif op == "==":
            result = result[result[col] == val]
        elif op == "!=":
            result = result[result[col] != val]
        elif op == "in":
            result = result[result[col].isin(val if isinstance(val, list) else [val])]
        elif op == "not_in":
            result = result[~result[col].isin(val if isinstance(val, list) else [val])]

    return result


# ── Collinearity Check ──

def check_collinearity(X_df, threshold=10.0):
    """
    Compute VIF for each predictor.
    Returns list of {variable, vif, warning} dicts.
    """
    # Remove constant if present
    cols = [c for c in X_df.columns if c != "const"]
    X = X_df[cols].values

    results = []
    for i, col in enumerate(cols):
        try:
            vif = variance_inflation_factor(X, i)
        except Exception:
            vif = float("inf")
        results.append({
            "variable": col,
            "vif": round(vif, 2),
            "warning": vif > threshold,
        })

    return sorted(results, key=lambda x: x["vif"], reverse=True)


# ── Core Model Fitting ──

def fit_model(df, y_col, x_cols, model_type="OLS", cov_type="HC1",
              entity="company_code", time="year", quantile=0.5):
    """
    Fit a regression model. Dispatches to statsmodels or linearmodels.

    model_type: "OLS" | "FE" | "RE" | "Quantile"
    cov_type: "HC1" | "HC3" | "clustered_entity" | "clustered_time" | "two_way"

    Returns standardized result dict.
    """
    # Prepare data
    cols_needed = [entity, time, y_col] + x_cols
    cols_available = [c for c in cols_needed if c in df.columns]
    clean = df[cols_available].dropna().copy()

    if len(clean) < 2 * (len(x_cols) + 1):
        return {
            "error": (
                f"Too few observations ({len(clean)}) for "
                f"{len(x_cols) + 1} parameters. "
                f"Need at least {2 * (len(x_cols) + 1)}."
            )
        }

    n_firms = clean[entity].nunique() if entity in clean.columns else len(clean)

    # Build formula string for display
    formula_str = f"{y_col} ~ {' + '.join(x_cols)}"

    try:
        if model_type == "OLS":
            return _fit_ols(clean, y_col, x_cols, cov_type, n_firms, formula_str)

        elif model_type == "FE":
            return _fit_fe(clean, y_col, x_cols, cov_type, entity, time, formula_str)

        elif model_type == "RE":
            return _fit_re(clean, y_col, x_cols, cov_type, entity, time, formula_str)

        elif model_type == "Quantile":
            return _fit_quantile(clean, y_col, x_cols, n_firms, formula_str, quantile)

        else:
            return {"error": f"Unknown model type: {model_type}"}

    except np.linalg.LinAlgError:
        return {"error": "Perfect collinearity detected. Remove redundant variables."}
    except Exception as e:
        return {"error": str(e)}


def _fit_ols(clean, y_col, x_cols, cov_type, n_firms, formula_str):
    """Fit Pooled OLS via statsmodels."""
    y = clean[y_col]
    X = sm.add_constant(clean[x_cols])

    valid_hc = ("HC0", "HC1", "HC2", "HC3")
    actual_cov = cov_type if cov_type in valid_hc else "HC1"

    model = sm.OLS(y, X)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        result = model.fit(cov_type=actual_cov)

    ci = result.conf_int()
    coef_table = pd.DataFrame({
        "Variable": result.params.index,
        "Coefficient": result.params.values,
        "Std Error": result.bse.values,
        "t-stat": result.tvalues.values,
        "p-value": result.pvalues.values,
        "CI Lower": ci[0].values,
        "CI Upper": ci[1].values,
    })

    return {
        "model_id": str(uuid4())[:8],
        "type": f"Pooled OLS ({actual_cov})",
        "y_col": y_col,
        "x_cols": x_cols,
        "cov_type": actual_cov,
        "coef_table": coef_table,
        "r_squared": result.rsquared,
        "adj_r_squared": result.rsquared_adj,
        "f_stat": result.fvalue,
        "f_pvalue": result.f_pvalue,
        "n_obs": int(result.nobs),
        "n_firms": n_firms,
        "aic": result.aic,
        "bic": result.bic,
        "result_obj": result,
        "residuals": result.resid.values,
        "fitted": result.fittedvalues.values,
        "formula_str": formula_str,
    }


def _fit_fe(clean, y_col, x_cols, cov_type, entity, time, formula_str):
    """Fit Fixed Effects via linearmodels PanelOLS."""
    from linearmodels.panel import PanelOLS

    panel = clean.set_index([entity, time])
    y = panel[y_col]
    X = sm.add_constant(panel[x_cols])

    fit_kwargs = _panel_cov_kwargs(cov_type)

    model = PanelOLS(y, X, entity_effects=True)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        result = model.fit(**fit_kwargs)

    coef_table = pd.DataFrame({
        "Variable": result.params.index,
        "Coefficient": result.params.values,
        "Std Error": result.std_errors.values,
        "t-stat": result.tstats.values,
        "p-value": result.pvalues.values,
    })

    return {
        "model_id": str(uuid4())[:8],
        "type": f"Fixed Effects ({cov_type})",
        "y_col": y_col,
        "x_cols": x_cols,
        "cov_type": cov_type,
        "coef_table": coef_table,
        "r_squared": result.rsquared,
        "r_squared_within": result.rsquared_within,
        "n_obs": int(result.nobs),
        "n_firms": int(result.entity_info.total),
        "result_obj": result,
        "residuals": result.resids.values,
        "fitted": result.fitted_values.values,
        "formula_str": formula_str + " [FE: entity]",
    }


def _fit_re(clean, y_col, x_cols, cov_type, entity, time, formula_str):
    """Fit Random Effects via linearmodels."""
    from linearmodels.panel import RandomEffects

    panel = clean.set_index([entity, time])
    y = panel[y_col]
    X = sm.add_constant(panel[x_cols])

    fit_kwargs = {}
    if cov_type in ("clustered_entity", "two_way"):
        fit_kwargs["cov_type"] = "clustered"
        fit_kwargs["cluster_entity"] = True
    else:
        fit_kwargs["cov_type"] = "robust"

    model = RandomEffects(y, X)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        result = model.fit(**fit_kwargs)

    coef_table = pd.DataFrame({
        "Variable": result.params.index,
        "Coefficient": result.params.values,
        "Std Error": result.std_errors.values,
        "t-stat": result.tstats.values,
        "p-value": result.pvalues.values,
    })

    return {
        "model_id": str(uuid4())[:8],
        "type": f"Random Effects ({cov_type})",
        "y_col": y_col,
        "x_cols": x_cols,
        "cov_type": cov_type,
        "coef_table": coef_table,
        "r_squared": result.rsquared,
        "r_squared_within": result.rsquared_within,
        "n_obs": int(result.nobs),
        "n_firms": int(result.entity_info.total),
        "result_obj": result,
        "residuals": result.resids.values,
        "fitted": result.fitted_values.values,
        "formula_str": formula_str + " [RE]",
    }


def _fit_quantile(clean, y_col, x_cols, n_firms, formula_str, quantile):
    """Fit Quantile Regression via statsmodels."""
    y = clean[y_col]
    X = sm.add_constant(clean[x_cols])

    model = sm.QuantReg(y, X)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        result = model.fit(q=quantile)

    coef_table = pd.DataFrame({
        "Variable": result.params.index,
        "Coefficient": result.params.values,
        "Std Error": result.bse.values,
        "t-stat": result.tvalues.values,
        "p-value": result.pvalues.values,
    })

    # Pseudo R-squared for quantile regression
    abs_resid_sum = result.resid.abs().sum()
    abs_dev_sum = (y - y.median()).abs().sum()
    pseudo_r2 = 1 - (abs_resid_sum / abs_dev_sum) if abs_dev_sum != 0 else 0.0

    return {
        "model_id": str(uuid4())[:8],
        "type": f"Quantile Regression (q={quantile})",
        "y_col": y_col,
        "x_cols": x_cols,
        "cov_type": "kernel",
        "coef_table": coef_table,
        "r_squared": pseudo_r2,
        "n_obs": int(result.nobs),
        "n_firms": n_firms,
        "result_obj": result,
        "residuals": result.resid.values,
        "fitted": result.fittedvalues.values,
        "formula_str": formula_str + f" [Q={quantile}]",
        "quantile": quantile,
    }


def _panel_cov_kwargs(cov_type):
    """Map user-facing cov_type string to linearmodels fit kwargs."""
    kwargs = {}
    if cov_type == "clustered_entity":
        kwargs["cov_type"] = "clustered"
        kwargs["cluster_entity"] = True
    elif cov_type == "clustered_time":
        kwargs["cov_type"] = "clustered"
        kwargs["cluster_time"] = True
    elif cov_type == "two_way":
        kwargs["cov_type"] = "clustered"
        kwargs["cluster_entity"] = True
        kwargs["cluster_time"] = True
    else:
        kwargs["cov_type"] = "robust"
    return kwargs


# ── Post-Estimation ──

def run_wald_test(result_dict, restriction_str):
    """
    Parse and run a Wald test.
    restriction_str: "profitability = 0" or "profitability = tangibility"
    Returns {chi2, df, p_value, verdict}.
    """
    result_obj = result_dict.get("result_obj")
    if result_obj is None:
        return {"error": "No result object available for Wald test"}

    params = result_obj.params

    # Parse restriction
    restriction_str = restriction_str.strip()
    if "=" not in restriction_str:
        return {"error": "Restriction must contain '=' (e.g., 'profitability = 0')"}

    parts = restriction_str.split("=")
    lhs = parts[0].strip()
    rhs = parts[1].strip()

    try:
        # Build R matrix and q vector for R @ beta = q
        n_params = len(params)
        param_names = list(params.index)

        R = np.zeros((1, n_params))
        q = np.zeros(1)

        if lhs in param_names:
            R[0, param_names.index(lhs)] = 1.0
        else:
            return {
                "error": (
                    f"Variable '{lhs}' not found in model. "
                    f"Available: {param_names}"
                )
            }

        try:
            q[0] = float(rhs)
        except ValueError:
            # rhs is a variable name -- test lhs = rhs, i.e., lhs - rhs = 0
            if rhs in param_names:
                R[0, param_names.index(rhs)] = -1.0
                q[0] = 0.0
            else:
                return {
                    "error": (
                        f"Variable '{rhs}' not found in model. "
                        f"Available: {param_names}"
                    )
                }

        # Run Wald test
        if hasattr(result_obj, "wald_test"):
            test = result_obj.wald_test(R, q)
            chi2 = float(test.statistic)
            p_value = float(test.pvalue)
        else:
            # Manual Wald: (R@beta - q)' @ inv(R @ V @ R') @ (R@beta - q)
            beta = params.values
            if hasattr(result_obj, "cov_params"):
                V = result_obj.cov_params().values
            else:
                V = np.eye(n_params)
            diff = R @ beta - q
            chi2 = float(diff.T @ np.linalg.inv(R @ V @ R.T) @ diff)
            p_value = float(1 - stats.chi2.cdf(chi2, 1))

        if p_value < 0.05:
            verdict = f"Reject H0 (p={p_value:.4f})"
        else:
            verdict = f"Cannot reject H0 (p={p_value:.4f})"

        return {
            "chi2": chi2,
            "df": 1,
            "p_value": p_value,
            "verdict": verdict,
            "restriction": restriction_str,
        }

    except Exception as e:
        return {"error": f"Wald test failed: {str(e)}"}


def compute_post_estimation(result_dict):
    """
    Compute post-estimation diagnostics.
    Returns dict with vif, predicted_vs_actual df, and marginal_effects (for
    interaction models).
    """
    post = {}

    # VIF
    result_obj = result_dict.get("result_obj")
    if (
        result_obj is not None
        and hasattr(result_obj, "model")
        and hasattr(result_obj.model, "exog")
    ):
        exog_names = (
            result_obj.model.exog_names
            if hasattr(result_obj.model, "exog_names")
            else [f"X{i}" for i in range(result_obj.model.exog.shape[1])]
        )
        X_df = pd.DataFrame(result_obj.model.exog, columns=exog_names)
        post["vif"] = check_collinearity(X_df)

    # Predicted vs actual
    resid = result_dict.get("residuals")
    fitted = result_dict.get("fitted")
    if resid is not None and fitted is not None:
        fitted_arr = np.asarray(fitted)
        resid_arr = np.asarray(resid)
        actual = fitted_arr + resid_arr
        post["pred_vs_actual"] = pd.DataFrame({
            "Actual": actual,
            "Predicted": fitted_arr,
        })

    return post


# ── Model Comparison Table (esttab) ──

def _significance_stars(p):
    """
    Fallback significance stars function in case helpers import fails.
    * p<0.05, ** p<0.01, *** p<0.001
    """
    if p < 0.001:
        return "***"
    elif p < 0.01:
        return "**"
    elif p < 0.05:
        return "*"
    return ""


def _get_stars_func():
    """Import significance_stars from helpers, fall back to local."""
    try:
        from helpers import significance_stars
        return significance_stars
    except ImportError:
        return _significance_stars


def build_comparison_table(models_list):
    """
    Build Stata esttab-style comparison table from up to 5 model results.
    Returns display_df.

    display_df has rows like:
      Variable  | Model 1    | Model 2    | Model 3
      profit    | -27.4***   | -15.3***   | -22.1***
                | (3.8)      | (1.8)      | (4.2)
      ...
      N         | 6,920      | 6,492      | 6,920
      R-sq      | 0.309      | 0.181      | 0.345
    """
    significance_stars = _get_stars_func()

    if not models_list:
        return pd.DataFrame()

    # Collect all variables across all models
    all_vars = []
    for m in models_list:
        if "coef_table" in m:
            for v in m["coef_table"]["Variable"]:
                if v not in all_vars and v != "const":
                    all_vars.append(v)
    all_vars.append("const")  # Constant at the end

    # Build display table
    rows = []
    for var in all_vars:
        coef_row = {"Variable": var}
        se_row = {"Variable": ""}
        for i, m in enumerate(models_list):
            col = f"Model {i + 1}"
            ct = m.get("coef_table", pd.DataFrame())
            if ct.empty:
                coef_row[col] = ""
                se_row[col] = ""
                continue
            match = ct[ct["Variable"] == var]
            if len(match) > 0:
                row = match.iloc[0]
                stars = significance_stars(row["p-value"])
                coef_row[col] = f"{row['Coefficient']:.3f}{stars}"
                se_row[col] = f"({row['Std Error']:.3f})"
            else:
                coef_row[col] = ""
                se_row[col] = ""
        rows.append(coef_row)
        rows.append(se_row)

    # Add footer rows
    footer_specs = [
        ("N", "n_obs", lambda x: f"{x:,}"),
        ("R-sq", "r_squared", lambda x: f"{x:.4f}"),
        ("Adj R-sq", "adj_r_squared", lambda x: f"{x:.4f}" if x else ""),
        ("Model", "type", lambda x: str(x)),
        ("Cov Type", "cov_type", lambda x: str(x)),
    ]
    for metric, key, fmt in footer_specs:
        row = {"Variable": metric}
        for i, m in enumerate(models_list):
            col = f"Model {i + 1}"
            val = m.get(key)
            row[col] = fmt(val) if val is not None else ""
        rows.append(row)

    display_df = pd.DataFrame(rows)
    return display_df


def export_latex(comparison_df):
    """Generate publication-ready LaTeX tabular."""
    if comparison_df.empty:
        return ""

    cols = list(comparison_df.columns)
    n_cols = len(cols)

    lines = []
    lines.append(r"\begin{table}[htbp]")
    lines.append(r"\centering")
    lines.append(r"\caption{Regression Results}")
    lines.append(r"\begin{tabular}{l" + "c" * (n_cols - 1) + "}")
    lines.append(r"\hline\hline")

    # Header
    header = " & ".join(cols)
    lines.append(f"{header} \\\\")
    lines.append(r"\hline")

    # Data rows
    for _, row in comparison_df.iterrows():
        vals = [str(v) for v in row.values]
        lines.append(" & ".join(vals) + " \\\\")

    lines.append(r"\hline\hline")
    lines.append(
        r"\multicolumn{" + str(n_cols) + r"}{l}"
        r"{\textit{Standard errors in parentheses. "
        r"* p$<$0.05, ** p$<$0.01, *** p$<$0.001}} \\"
    )
    lines.append(r"\end{tabular}")
    lines.append(r"\end{table}")

    return "\n".join(lines)


def export_comparison_csv(comparison_df):
    """Export comparison table as CSV string."""
    return comparison_df.to_csv(index=False)
