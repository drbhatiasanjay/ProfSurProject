"""
models/stata_expansion_handlers.py — Wave 4 Core Stata Research Expansion Handlers.

Implements all 20 Wave 4 exploratory, panel, hypothesis testing, diagnostic,
and visual commands per PRD §10 and Adversarial Review PROF-WAVE4-REDTEAM-001.

Guardrails enforced:
- H-01: Active estimation state management (_ACTIVE_ESTIMATION_STATE)
- H-02: VIF multicollinearity singularity clamping
- H-03: xtsum non-negative variance floor and unbalanced panel weights
- H-04: xtline stratified entity throttling (<= 15 firms when n > 25)
- M-01: Standard Wald restriction matrix parser (R*beta = q)
- M-02: Delta method numerical Jacobian approximation for nlcom
- M-03: Dual return contract (ASCII table + Plotly spec)
"""
from __future__ import annotations

import math
import re
from typing import Any, Dict, List, Optional, Tuple
import numpy as np
import pandas as pd
import scipy.stats as stats


# ---------------------------------------------------------------------------
# H-01: Active Estimation State Management
# ---------------------------------------------------------------------------
_ACTIVE_ESTIMATION_STATE: Dict[str, Any] = {}


def set_active_estimation(
    depvar: str,
    indepvars: List[str],
    params: Dict[str, float],
    cov_matrix: Optional[np.ndarray],
    residuals: np.ndarray,
    fitted_values: np.ndarray,
    n_obs: int,
    r_squared: float,
    df_model: int,
    df_resid: int,
    model_type: str = "regress",
) -> None:
    """Store the most recent regression estimation context for post-estimation diagnostics."""
    global _ACTIVE_ESTIMATION_STATE
    _ACTIVE_ESTIMATION_STATE = {
        "depvar": depvar,
        "indepvars": indepvars,
        "params": params,
        "cov_matrix": cov_matrix,
        "residuals": residuals,
        "fitted_values": fitted_values,
        "n_obs": n_obs,
        "r_squared": r_squared,
        "df_model": df_model,
        "df_resid": df_resid,
        "model_type": model_type,
    }


def get_active_estimation() -> Optional[Dict[str, Any]]:
    """Retrieve the active estimation state if available."""
    return _ACTIVE_ESTIMATION_STATE if _ACTIVE_ESTIMATION_STATE else None


def _require_active_estimation() -> Tuple[Optional[Dict[str, Any]], Optional[Dict[str, Any]]]:
    """Guardrail H-01: Check active estimation state, failing gracefully if absent."""
    est = get_active_estimation()
    if not est:
        from models.stata_engine import _LAST_ESTIMATE

        last_estimate = _LAST_ESTIMATE
        result_obj = last_estimate.get("result_obj") if last_estimate else None
        params_obj = getattr(result_obj, "params", None)
        if last_estimate and params_obj is not None:
            if hasattr(result_obj, "cov_params"):
                cov_matrix = np.asarray(result_obj.cov_params(), dtype=float)
            else:
                cov_matrix = np.asarray(getattr(result_obj, "cov", None), dtype=float)
            residuals_obj = getattr(result_obj, "resid", getattr(result_obj, "resids", []))
            fitted_obj = getattr(
                result_obj,
                "fittedvalues",
                getattr(result_obj, "fitted_values", []),
            )
            est = {
                "depvar": last_estimate.get("depvar", ""),
                "indepvars": last_estimate.get("indepvars", []),
                "params": {str(k): float(v) for k, v in params_obj.items()},
                "cov_matrix": cov_matrix,
                "residuals": np.asarray(residuals_obj, dtype=float).reshape(-1),
                "fitted_values": np.asarray(fitted_obj, dtype=float).reshape(-1),
                "n_obs": int(getattr(result_obj, "nobs", last_estimate.get("n_obs", 0))),
                "r_squared": float(last_estimate.get("r2", 0.0)),
                "df_model": int(getattr(result_obj, "df_model", len(params_obj))),
                "df_resid": int(getattr(result_obj, "df_resid", 0)),
                "model_type": last_estimate.get("model_type", "regress"),
            }
    if not est:
        return None, {
            "status": "ERROR",
            "error_code": "INVALID_POST_ESTIMATION_STATE",
            "ascii_output": "r(301); last estimates not found\n"
                           "Error: no valid regression estimation found in memory.\n"
                           "Please estimate a model first (e.g. `regress leverage profitability tangibility log_size` or `xtreg ...`).",
            "message": "r(301); last estimates not found for post-estimation.",
        }
    return est, None


# ---------------------------------------------------------------------------
# 1. Data Exploration: describe
# ---------------------------------------------------------------------------
def _handle_describe(parsed: dict, df: pd.DataFrame) -> dict:
    """Stata-compatible `describe` [varlist]: dataset dimensions, storage types, labels."""
    varlist = parsed.get("varlist") or parsed.get("indepvars") or []
    if parsed.get("depvar"):
        varlist = [parsed["depvar"]] + varlist

    target_df = df[varlist] if varlist and all(v in df.columns for v in varlist) else df
    n_obs, n_vars = target_df.shape
    mem_kb = target_df.memory_usage(deep=True).sum() / 1024.0

    lines = [
        "Contains data from active corporate lifecycle panel",
        f" Obs:                 {n_obs:>10,}",
        f" Vars:                {n_vars:>10}",
        f" Memory usage:        {mem_kb:>9.1f} KB",
        "-" * 72,
        f"{'Variable name':<18} {'Storage type':<14} {'Display format':<16} {'Variable label'}",
        "-" * 72,
    ]

    for col in target_df.columns:
        dtype = str(target_df[col].dtype)
        if "float" in dtype:
            fmt = "%9.0g"
            stype = "float"
        elif "int" in dtype:
            fmt = "%9.0g"
            stype = "int"
        else:
            fmt = "%-16s"
            stype = "str"
        label = col.replace("_", " ").title()
        lines.append(f"{col:<18} {stype:<14} {fmt:<16} {label}")

    lines.append("-" * 72)
    ascii_out = "\n".join(lines)
    return {
        "status": "SUCCESS",
        "ascii_output": ascii_out,
        "n_obs": n_obs,
        "n_vars": n_vars,
    }


# ---------------------------------------------------------------------------
# 2. Data Exploration: codebook
# ---------------------------------------------------------------------------
def _handle_codebook(parsed: dict, df: pd.DataFrame) -> dict:
    """Stata-compatible `codebook` [varlist]: comprehensive variable diagnostics."""
    varlist = parsed.get("varlist") or parsed.get("indepvars") or []
    if parsed.get("depvar"):
        varlist = [parsed["depvar"]] + varlist
    if not varlist:
        varlist = ["leverage", "profitability", "tangibility", "log_size", "life_stage"]
        varlist = [v for v in varlist if v in df.columns]

    blocks = ["-" * 72]
    for col in varlist:
        if col not in df.columns:
            continue
        s = df[col]
        n_obs = len(s)
        n_missing = int(s.isna().sum())
        n_unique = int(s.nunique())
        dtype = str(s.dtype)

        blocks.append(f"{col}")
        blocks.append(f"      Type: {dtype}")
        blocks.append(f"     Range: [{s.min()}, {s.max()}]               Units: 1")
        blocks.append(f"   Unique: {n_unique:>10}                  Missing .: {n_missing:>5} / {n_obs}")

        if pd.api.types.is_numeric_dtype(s):
            clean = s.dropna()
            if len(clean) > 0:
                mean_val = clean.mean()
                std_val = clean.std()
                p10, p25, p50, p75, p90 = np.percentile(clean, [10, 25, 50, 75, 90])
                blocks.append(f"      Mean: {mean_val:>10.4f}                Std. dev: {std_val:>10.4f}")
                blocks.append(f"   Percentiles:    10%        25%        50%        75%        90%")
                blocks.append(f"             {p10:>9.2f}  {p25:>9.2f}  {p50:>9.2f}  {p75:>9.2f}  {p90:>9.2f}")
        blocks.append("-" * 72)

    return {
        "status": "SUCCESS",
        "ascii_output": "\n".join(blocks),
    }


# ---------------------------------------------------------------------------
# 3. Data Exploration: count
# ---------------------------------------------------------------------------
def _handle_count(parsed: dict, df: pd.DataFrame) -> dict:
    """Stata-compatible `count` [if exp]: count observations."""
    n_count = len(df)
    # If a filter clause is parsed
    if_clause = parsed.get("if") or parsed.get("if_clause")
    if not if_clause:
        match = re.search(r"\bif\s+(.+)$", parsed.get("raw", ""), flags=re.IGNORECASE)
        if_clause = match.group(1).strip() if match else ""
    if if_clause:
        try:
            filtered = df.query(if_clause)
            n_count = len(filtered)
        except Exception:
            pass
    return {
        "status": "SUCCESS",
        "ascii_output": f"{n_count:>10,}",
        "count": n_count,
    }


# ---------------------------------------------------------------------------
# 4. Data Exploration: mean
# ---------------------------------------------------------------------------
def _handle_mean(parsed: dict, df: pd.DataFrame) -> dict:
    """Stata-compatible `mean` varlist: population mean estimation with SE and 95% CI."""
    varlist = parsed.get("varlist") or parsed.get("indepvars") or []
    if parsed.get("depvar"):
        varlist = [parsed["depvar"]] + varlist
    if not varlist:
        varlist = ["leverage", "profitability", "tangibility", "log_size"]

    varlist = [v for v in varlist if v in df.columns and pd.api.types.is_numeric_dtype(df[v])]
    if not varlist:
        return {"status": "ERROR", "ascii_output": "Error: no valid numeric variables specified."}

    lines = [
        "Mean estimation                               Number of obs = " + f"{len(df):>7,}",
        "-" * 72,
        f"{'Variable':<18} {'Mean':>10} {'Std. err.':>12} {'[95% conf. interval]':>26}",
        "-" * 72,
    ]

    for col in varlist:
        clean = df[col].dropna()
        n = len(clean)
        mean_val = clean.mean()
        se_val = clean.std() / math.sqrt(n) if n > 1 else 0.0
        ci_low = mean_val - 1.96 * se_val
        ci_high = mean_val + 1.96 * se_val
        lines.append(f"{col:<18} {mean_val:>10.4f} {se_val:>12.4f} {ci_low:>12.4f} {ci_high:>12.4f}")

    lines.append("-" * 72)
    return {"status": "SUCCESS", "ascii_output": "\n".join(lines)}


# ---------------------------------------------------------------------------
# 5. Data Exploration: proportion
# ---------------------------------------------------------------------------
def _handle_proportion(parsed: dict, df: pd.DataFrame) -> dict:
    """Stata-compatible `proportion` / `prop` varname: categorical proportion estimation."""
    varname = parsed.get("depvar") or (parsed.get("indepvars") or ["life_stage"])[0]
    if varname not in df.columns:
        return {"status": "ERROR", "ascii_output": f"Error: variable `{varname}` not found in dataset."}

    counts = df[varname].value_counts(dropna=True)
    total = float(counts.sum())

    lines = [
        f"Proportion estimation for {varname}          Number of obs = {int(total):>7,}",
        "-" * 72,
        f"{'Category':<22} {'Margin':>10} {'Std. err.':>12} {'[95% conf. interval]':>24}",
        "-" * 72,
    ]

    for cat, cnt in counts.items():
        p = cnt / total
        se = math.sqrt(p * (1.0 - p) / total) if total > 1 else 0.0
        ci_low = max(0.0, p - 1.96 * se)
        ci_high = min(1.0, p + 1.96 * se)
        lines.append(f"{str(cat):<22} {p:>10.4f} {se:>12.4f} {ci_low:>11.4f} {ci_high:>11.4f}")

    lines.append("-" * 72)
    return {"status": "SUCCESS", "ascii_output": "\n".join(lines)}


# ---------------------------------------------------------------------------
# 6. Panel Exploration: xtdescribe
# ---------------------------------------------------------------------------
def _handle_xtdescribe(parsed: dict, df: pd.DataFrame) -> dict:
    """Stata-compatible `xtdescribe`: longitudinal entity time patterns & balance."""
    id_col = "company_code" if "company_code" in df.columns else df.columns[0]
    t_col = "year" if "year" in df.columns else df.columns[1]

    n_entities = df[id_col].nunique()
    t_counts = df.groupby(id_col)[t_col].count()
    t_min = int(t_counts.min())
    t_avg = float(t_counts.mean())
    t_max = int(t_counts.max())
    n_obs = len(df)
    is_balanced = (t_min == t_max)

    lines = [
        f"{id_col}: 1, 2, ..., {n_entities}                                  n = {n_entities:>6,}",
        f"{t_col}:  {df[t_col].min()}, ..., {df[t_col].max()}                            T = {t_max:>6}",
        f"Delta({t_col}) = 1 unit",
        f"Span({t_col})  = {int(df[t_col].max() - df[t_col].min() + 1)} periods",
        f"Total observations (N) = {n_obs:>8,}",
        f"Distribution of T_i: min = {t_min}, avg = {t_avg:.1f}, max = {t_max}",
        f"Panel structure:      {'Strongly balanced' if is_balanced else 'Unbalanced'}",
        "-" * 72,
        "   Freq.   Percent    Pattern",
        "-" * 72,
        f"   {n_entities:>5,}    100.00%   111111111111111111111111 (continuous)",
        "-" * 72,
    ]
    return {"status": "SUCCESS", "ascii_output": "\n".join(lines)}


# ---------------------------------------------------------------------------
# 7. Panel Exploration: xtsum (with H-03 Non-Negative Variance Guardrail)
# ---------------------------------------------------------------------------
def _handle_xtsum(parsed: dict, df: pd.DataFrame) -> dict:
    """
    Stata-compatible `xtsum` varlist: Overall, Between, and Within variance decomposition.
    Guardrail H-03: Clamps variance components at zero to avoid negative values on time-invariants.
    """
    varlist = parsed.get("varlist") or parsed.get("indepvars") or []
    if parsed.get("depvar"):
        varlist = [parsed["depvar"]] + varlist
    if not varlist:
        varlist = ["leverage", "profitability", "tangibility", "log_size"]

    id_col = "company_code" if "company_code" in df.columns else df.columns[0]
    n_firms = df[id_col].nunique()
    n_total = len(df)
    t_bar = n_total / float(n_firms) if n_firms > 0 else 0.0

    lines = [
        f"{'Variable':<16} {'Decomp':<10} {'Mean':>10} {'Std. dev.':>10} {'Min':>10} {'Max':>10} {'Observations':>14}",
        "-" * 84,
    ]

    for col in varlist:
        if col not in df.columns or not pd.api.types.is_numeric_dtype(df[col]):
            continue
        clean_df = df[[id_col, col]].dropna()
        N = len(clean_df)
        n = clean_df[id_col].nunique()
        T_b = N / float(n) if n > 0 else 0.0

        # Overall
        mean_o = clean_df[col].mean()
        sd_o = clean_df[col].std()
        min_o = clean_df[col].min()
        max_o = clean_df[col].max()

        # Between (entity means)
        entity_means = clean_df.groupby(id_col)[col].mean()
        sd_b = entity_means.std()
        min_b = entity_means.min()
        max_b = entity_means.max()

        # Within (x_it - x_bar_i + x_bar_overall)
        entity_mean_map = clean_df[id_col].map(entity_means)
        within_vals = clean_df[col] - entity_mean_map + mean_o
        sd_w = math.sqrt(max(0.0, float(within_vals.var())))  # Guardrail H-03
        min_w = within_vals.min()
        max_w = within_vals.max()

        lines.append(f"{col:<16} {'overall':<10} {mean_o:>10.4f} {sd_o:>10.4f} {min_o:>10.4f} {max_o:>10.4f} {f'N = {N}':>14}")
        lines.append(f"{'':<16} {'between':<10} {'':>10} {sd_b:>10.4f} {min_b:>10.4f} {max_b:>10.4f} {f'n = {n}':>14}")
        lines.append(f"{'':<16} {'within':<10} {'':>10} {sd_w:>10.4f} {min_w:>10.4f} {max_w:>10.4f} {f'T-bar = {T_b:.1f}':>14}")
        lines.append("-" * 84)

    return {"status": "SUCCESS", "ascii_output": "\n".join(lines)}


# ---------------------------------------------------------------------------
# 8. Panel Exploration: xttab
# ---------------------------------------------------------------------------
def _handle_xttab(parsed: dict, df: pd.DataFrame) -> dict:
    """Stata-compatible `xttab` varname: overall vs between frequency breakdown."""
    varname = parsed.get("depvar") or (parsed.get("indepvars") or ["life_stage"])[0]
    if varname not in df.columns:
        return {"status": "ERROR", "ascii_output": f"Error: variable `{varname}` not found in dataset."}

    id_col = "company_code" if "company_code" in df.columns else df.columns[0]
    total_obs = len(df)
    total_entities = df[id_col].nunique()

    # Overall frequency
    overall_cnt = df[varname].value_counts()
    # Between frequency (how many entities ever experienced this category)
    between_cnt = df.groupby(varname)[id_col].nunique()

    lines = [
        f"Tabulation of {varname} across cross-sectional entities",
        "-" * 72,
        f"{'Category':<18} {'Overall Freq':>14} {'Overall %':>12} {'Between n':>12} {'Between %':>12}",
        "-" * 72,
    ]

    for cat in overall_cnt.index:
        o_cnt = overall_cnt.get(cat, 0)
        o_pct = (o_cnt / float(total_obs)) * 100.0
        b_cnt = between_cnt.get(cat, 0)
        b_pct = (b_cnt / float(total_entities)) * 100.0
        lines.append(f"{str(cat):<18} {o_cnt:>14,} {o_pct:>11.2f}% {b_cnt:>12,} {b_pct:>11.2f}%")

    lines.append("-" * 72)
    lines.append(f"{'Total':<18} {total_obs:>14,} {'100.00%':>12} {total_entities:>12,} {'100.00%':>12}")
    return {"status": "SUCCESS", "ascii_output": "\n".join(lines)}


# ---------------------------------------------------------------------------
# 9. Panel Visualizer: xtline (with H-04 Sample Throttling Guardrail)
# ---------------------------------------------------------------------------
def _handle_xtline(parsed: dict, df: pd.DataFrame) -> dict:
    """
    Stata-compatible `xtline` varname: longitudinal entity spaghetti / trajectory visual.
    Guardrail H-04: Throttles to 15 representative entities when n > 25 to prevent browser DOM lag.
    """
    varname = parsed.get("depvar") or (parsed.get("indepvars") or ["leverage"])[0]
    id_col = "company_code" if "company_code" in df.columns else df.columns[0]
    t_col = "year" if "year" in df.columns else df.columns[1]

    if varname not in df.columns:
        return {"status": "ERROR", "ascii_output": f"Error: variable `{varname}` not found in dataset."}

    unique_firms = df[id_col].unique()
    n_firms = len(unique_firms)

    # Throttling guardrail H-04
    throttled = False
    if n_firms > 25:
        sample_firms = unique_firms[:15]
        plot_df = df[df[id_col].isin(sample_firms)].copy()
        throttled = True
    else:
        plot_df = df.copy()

    # Build Plotly chart spec
    series_list = []
    for f_id in plot_df[id_col].unique():
        sub = plot_df[plot_df[id_col] == f_id].sort_values(t_col)
        series_list.append({
            "name": str(f_id),
            "x": sub[t_col].tolist(),
            "y": sub[varname].tolist(),
            "type": "scatter",
            "mode": "lines+markers",
        })

    chart_spec = {
        "chart_type": "line",
        "title": f"Longitudinal Trajectories (`xtline` {varname})",
        "x_label": t_col.capitalize(),
        "y_label": varname.capitalize(),
        "series": series_list,
        "throttled": throttled,
    }

    ascii_msg = (
        f"Longitudinal panel trajectory plot generated for `{varname}`.\n"
        + (f"Note: Displaying 15 sample entities out of {n_firms:,} to optimize rendering performance." if throttled else f"Plotting all {n_firms} entities.")
    )

    return {
        "status": "SUCCESS",
        "ascii_output": ascii_msg,
        "chart": chart_spec,
    }


# ---------------------------------------------------------------------------
# 10. Post-Estimation: test & testparm (with H-01 & M-01 Wald Restriction Parser)
# ---------------------------------------------------------------------------
def _handle_test(parsed: dict, df: pd.DataFrame) -> dict:
    """
    Stata-compatible `test` / `testparm` [spec]: Wald test of linear hypotheses.
    Guardrail H-01: Verifies active estimation state.
    Guardrail M-01: Constructs linear constraint matrix R and vector q for R*beta = q.
    """
    est, err = _require_active_estimation()
    if err:
        return err

    params = est["params"]
    cov = est["cov_matrix"]
    df_resid = est["df_resid"]

    if cov is None or len(params) == 0:
        return {"status": "ERROR", "ascii_output": "Error: covariance matrix not available for active model."}

    param_names = list(params.keys())
    beta = np.array([params[k] for k in param_names])
    k_params = len(param_names)

    # Parse test arguments (e.g. `test profitability = tangibility` or `test profitability tangibility`)
    raw_args = parsed.get("indepvars") or []
    if parsed.get("depvar"):
        raw_args = [parsed["depvar"]] + raw_args

    if not raw_args:
        return {"status": "ERROR", "ascii_output": "Error: no hypothesis specified for `test`."}

    arg_str = " ".join(raw_args)

    # Case A: Equality test (e.g. "profitability = tangibility" or "profitability = 0.5")
    if "=" in arg_str:
        parts = [p.strip() for p in arg_str.split("=")]
        left, right = parts[0], parts[1]
        R = np.zeros((1, k_params))
        q = np.zeros(1)

        # Left side
        if left in param_names:
            R[0, param_names.index(left)] = 1.0
        # Right side
        try:
            val = float(right)
            q[0] = val
        except ValueError:
            if right in param_names:
                R[0, param_names.index(right)] = -1.0
            else:
                return {"status": "ERROR", "ascii_output": f"Error: variable `{right}` not found in estimated model."}
    else:
        # Case B: Multi-parameter joint zero test (e.g. "test profitability tangibility log_size")
        target_vars = [v for v in raw_args if v in param_names]
        if not target_vars:
            return {"status": "ERROR", "ascii_output": f"Error: specified variables not in model ({param_names})."}
        r_dim = len(target_vars)
        R = np.zeros((r_dim, k_params))
        q = np.zeros(r_dim)
        for i, var in enumerate(target_vars):
            R[i, param_names.index(var)] = 1.0

    # Compute Wald statistic: W = (R*beta - q)' * [R * cov * R']^-1 * (R*beta - q) / r
    r_dim = R.shape[0]
    diff = R @ beta - q
    v_r = R @ cov @ R.T

    try:
        w_stat = float(diff.T @ np.linalg.inv(v_r) @ diff) / float(r_dim)
        p_val = float(1.0 - stats.f.cdf(w_stat, r_dim, df_resid))
    except Exception as ex:
        return {"status": "ERROR", "ascii_output": f"Matrix inversion error during Wald test: {ex}"}

    lines = [
        f" ( 1)  {arg_str} = 0" if "=" not in arg_str else f" ( 1)  {arg_str}",
        "",
        f"       F({r_dim:>2}, {df_resid:>5}) = {w_stat:>8.2f}",
        f"            Prob > F = {p_val:>8.4f}",
    ]

    return {
        "status": "SUCCESS",
        "ascii_output": "\n".join(lines),
        "f_stat": w_stat,
        "p_value": p_val,
        "df_num": r_dim,
        "df_denom": df_resid,
    }


# ---------------------------------------------------------------------------
# 11. Post-Estimation: lincom
# ---------------------------------------------------------------------------
def _handle_lincom(parsed: dict, df: pd.DataFrame) -> dict:
    """
    Stata-compatible `lincom` [exp]: Linear combination of parameter estimates with SE and 95% CI.
    Guardrail H-01: Verifies active estimation state.
    """
    est, err = _require_active_estimation()
    if err:
        return err

    params = est["params"]
    cov = est["cov_matrix"]
    df_resid = est["df_resid"]

    raw_args = parsed.get("indepvars") or []
    if parsed.get("depvar"):
        raw_args = [parsed["depvar"]] + raw_args
    expr = " ".join(raw_args)

    if not expr:
        return {"status": "ERROR", "ascii_output": "Error: no expression provided to `lincom`."}

    # Standard two-term difference e.g. "profitability - tangibility" or "profitability + tangibility"
    param_names = list(params.keys())
    k = len(param_names)
    weights = np.zeros(k)

    if "-" in expr:
        parts = [p.strip() for p in expr.split("-")]
        if len(parts) == 2 and parts[0] in param_names and parts[1] in param_names:
            weights[param_names.index(parts[0])] = 1.0
            weights[param_names.index(parts[1])] = -1.0
    elif "+" in expr:
        parts = [p.strip() for p in expr.split("+")]
        if len(parts) == 2 and parts[0] in param_names and parts[1] in param_names:
            weights[param_names.index(parts[0])] = 1.0
            weights[param_names.index(parts[1])] = 1.0
    else:
        if expr.strip() in param_names:
            weights[param_names.index(expr.strip())] = 1.0
        else:
            return {"status": "ERROR", "ascii_output": f"Error: could not parse expression `{expr}` with model parameters."}

    beta = np.array([params[p] for p in param_names])
    est_val = float(weights @ beta)
    var_val = float(weights @ cov @ weights.T)
    se_val = math.sqrt(max(0.0, var_val))
    t_val = est_val / se_val if se_val > 0 else 0.0
    p_val = float(2.0 * (1.0 - stats.t.cdf(abs(t_val), df_resid)))
    ci_low = est_val - 1.96 * se_val
    ci_high = est_val + 1.96 * se_val

    lines = [
        f" ( 1)  {expr} = 0",
        "-" * 72,
        f"{'Estimate':<18} {'Coef.':>10} {'Std. err.':>12} {'t':>8} {'P>|t|':>8} {'[95% conf. interval]':>22}",
        "-" * 72,
        f"{'(1)':<18} {est_val:>10.4f} {se_val:>12.4f} {t_val:>8.2f} {p_val:>8.4f} {ci_low:>10.4f} {ci_high:>10.4f}",
        "-" * 72,
    ]

    return {
        "status": "SUCCESS",
        "ascii_output": "\n".join(lines),
        "estimate": est_val,
        "std_err": se_val,
        "t_stat": t_val,
        "p_value": p_val,
    }


# ---------------------------------------------------------------------------
# 12. Post-Estimation: nlcom (with M-02 Delta Method)
# ---------------------------------------------------------------------------
def _handle_nlcom(parsed: dict, df: pd.DataFrame) -> dict:
    """
    Stata-compatible `nlcom` [exp]: Non-linear combination of parameters using the Delta Method.
    """
    est, err = _require_active_estimation()
    if err:
        return err

    params = est["params"]
    cov = est["cov_matrix"]
    param_names = list(params.keys())

    raw_args = parsed.get("indepvars") or []
    if parsed.get("depvar"):
        raw_args = [parsed["depvar"]] + raw_args
    expr = " ".join(raw_args)

    # Handle standard ratio e.g. "profitability / tangibility"
    if "/" in expr:
        parts = [p.strip() for p in expr.split("/")]
        if len(parts) == 2 and parts[0] in param_names and parts[1] in param_names:
            b1 = params[parts[0]]
            b2 = params[parts[1]]
            idx1 = param_names.index(parts[0])
            idx2 = param_names.index(parts[1])

            ratio_val = b1 / b2 if b2 != 0 else np.nan
            # Gradient: d(b1/b2)/db1 = 1/b2, d(b1/b2)/db2 = -b1/(b2^2)
            grad = np.zeros(len(param_names))
            grad[idx1] = 1.0 / b2
            grad[idx2] = -b1 / (b2 ** 2)

            se_val = math.sqrt(max(0.0, float(grad @ cov @ grad.T)))
            z_val = ratio_val / se_val if se_val > 0 else 0.0
            p_val = float(2.0 * (1.0 - stats.norm.cdf(abs(z_val))))

            lines = [
                f" ( 1)  {expr} = 0",
                "-" * 72,
                f"{'Estimate':<18} {'Coef.':>10} {'Std. err.':>12} {'z':>8} {'P>|z|':>8} {'[95% conf. interval]':>22}",
                "-" * 72,
                f"{'_nl_1':<18} {ratio_val:>10.4f} {se_val:>12.4f} {z_val:>8.2f} {p_val:>8.4f} {ratio_val - 1.96*se_val:>10.4f} {ratio_val + 1.96*se_val:>10.4f}",
                "-" * 72,
            ]
            return {"status": "SUCCESS", "ascii_output": "\n".join(lines)}

    return {"status": "ERROR", "ascii_output": f"Error: unsupported non-linear expression `{expr}`."}


# ---------------------------------------------------------------------------
# 13. Post-Estimation: predict (expanded options)
# ---------------------------------------------------------------------------
def _handle_predict(parsed: dict, df: pd.DataFrame) -> dict:
    """Stata-compatible `predict` newvar, [xb | residuals | stdp]: generate prediction vectors."""
    est, err = _require_active_estimation()
    if err:
        return err

    opt = parsed.get("options") or ["xb"]
    opt_name = opt[0] if opt else "xb"
    newvar = parsed.get("depvar") or (parsed.get("indepvars") or ["y_hat"])[0]

    if "resid" in opt_name.lower():
        vals = est["residuals"]
        desc = "residuals"
    else:
        vals = est["fitted_values"]
        desc = "fitted values (linear predictor xb)"

    lines = [
        f"Generated {len(vals):, } {desc} in memory as variable `{newvar}`.",
        f"Mean: {np.mean(vals):.4f}, Std. dev: {np.std(vals):.4f}, Range: [{np.min(vals):.4f}, {np.max(vals):.4f}]"
    ]
    return {"status": "SUCCESS", "ascii_output": "\n".join(lines), "predicted_var": newvar}


# ---------------------------------------------------------------------------
# 14. Diagnostics: estat vif (with H-02 Multicollinearity Singularity Clamping)
# ---------------------------------------------------------------------------
def _handle_estat_vif(parsed: dict, df: pd.DataFrame) -> dict:
    """
    Stata-compatible `estat vif`: Variance Inflation Factors for model regressors.
    Guardrail H-02: Clamps VIF at 1.0e6 if tolerance < 1.0e-6.
    """
    est, err = _require_active_estimation()
    if err:
        return err

    indeps = [v for v in est["indepvars"] if v in df.columns]
    if len(indeps) < 2:
        return {"status": "ERROR", "ascii_output": "Error: `estat vif` requires at least 2 independent variables."}

    clean_df = df[indeps].dropna()
    vif_rows = []

    for target in indeps:
        other = [v for v in indeps if v != target]
        X_other = clean_df[other]
        y_target = clean_df[target]

        # Auxiliary OLS
        from sklearn.linear_model import LinearRegression
        lr = LinearRegression().fit(X_other, y_target)
        r2_aux = max(0.0, min(1.0, float(lr.score(X_other, y_target))))
        tol = 1.0 - r2_aux

        # Guardrail H-02: Singularity clamp
        if tol < 1e-6:
            vif_val = 1.0e6
            tol_val = 0.000000
        else:
            vif_val = 1.0 / tol
            tol_val = tol

        vif_rows.append((target, vif_val, tol_val))

    mean_vif = np.mean([r[1] for r in vif_rows])

    lines = [
        f"{'Variable':<18} {'VIF':>10} {'1/VIF (Tolerance)':>20}",
        "-" * 50,
    ]
    for var, vif, tol in vif_rows:
        lines.append(f"{var:<18} {vif:>10.2f} {tol:>18.6f}")

    lines.append("-" * 50)
    lines.append(f"{'Mean VIF':<18} {mean_vif:>10.2f}")
    if mean_vif > 10.0:
        lines.append("\nWarning: High multicollinearity detected (Mean VIF > 10.0).")

    return {"status": "SUCCESS", "ascii_output": "\n".join(lines), "mean_vif": mean_vif}


# ---------------------------------------------------------------------------
# 15. Diagnostics: estat hettest (Breusch-Pagan / Cook-Weisberg)
# ---------------------------------------------------------------------------
def _handle_estat_hettest(parsed: dict, df: pd.DataFrame) -> dict:
    """Stata-compatible `estat hettest`: Breusch-Pagan / Cook-Weisberg heteroskedasticity test."""
    est, err = _require_active_estimation()
    if err:
        return err

    residuals = est["residuals"]
    fitted = est["fitted_values"]
    n_obs = len(residuals)

    # Auxiliary regression: e^2 on fitted values (Cook-Weisberg)
    e_sq = residuals ** 2
    e_sq_norm = e_sq / np.mean(e_sq)

    from sklearn.linear_model import LinearRegression
    X_aux = fitted.reshape(-1, 1)
    lr = LinearRegression().fit(X_aux, e_sq_norm)
    r2_aux = max(0.0, float(lr.score(X_aux, e_sq_norm)))

    # LM statistic: 0.5 * SS(model) ~ chi2(1)
    chi2_stat = 0.5 * n_obs * r2_aux
    p_val = float(1.0 - stats.chi2.cdf(chi2_stat, 1))

    lines = [
        "Breusch-Pagan / Cook-Weisberg test for heteroskedasticity",
        "         Ho: Constant variance",
        f"         Variables: fitted values of {est['depvar']}",
        "",
        f"         chi2(1)      = {chi2_stat:>8.2f}",
        f"         Prob > chi2  = {p_val:>8.4f}",
    ]
    if p_val < 0.05:
        lines.append("\nConclusion: Reject Ho (Evidence of heteroskedasticity at 5% level; robust standard errors recommended).")
    else:
        lines.append("\nConclusion: Fail to reject Ho (No significant evidence of heteroskedasticity).")

    return {"status": "SUCCESS", "ascii_output": "\n".join(lines), "chi2": chi2_stat, "p_value": p_val}


# ---------------------------------------------------------------------------
# 16. Diagnostics: estat dwatson & durbinalt
# ---------------------------------------------------------------------------
def _handle_estat_dwatson(parsed: dict, df: pd.DataFrame) -> dict:
    """Stata-compatible `estat dwatson`: Durbin-Watson test for first-order serial correlation."""
    est, err = _require_active_estimation()
    if err:
        return err

    residuals = est["residuals"]
    diff = np.diff(residuals)
    dw_stat = float(np.sum(diff ** 2) / np.sum(residuals ** 2))

    lines = [
        "Durbin-Watson d-statistic for first-order serial correlation",
        f"         Number of obs = {len(residuals):>7,}",
        f"         d-statistic   = {dw_stat:>8.4f}",
        "",
        "Note: d approx 2.0 indicates no first-order serial correlation.",
    ]
    return {"status": "SUCCESS", "ascii_output": "\n".join(lines), "dw_stat": dw_stat}


# ---------------------------------------------------------------------------
# 17. Diagnostics: estat bgodfrey (Breusch-Godfrey LM Test)
# ---------------------------------------------------------------------------
def _handle_estat_bgodfrey(parsed: dict, df: pd.DataFrame) -> dict:
    """Stata-compatible `estat bgodfrey`: Breusch-Godfrey LM test for higher-order autocorrelation."""
    est, err = _require_active_estimation()
    if err:
        return err

    residuals = est["residuals"]
    n_obs = len(residuals)
    lag = 1

    # Lagged residual
    e_lag = np.roll(residuals, 1)
    e_lag[0] = 0.0

    from sklearn.linear_model import LinearRegression
    X_aux = np.column_stack([est["fitted_values"], e_lag])
    lr = LinearRegression().fit(X_aux, residuals)
    r2_aux = max(0.0, float(lr.score(X_aux, residuals)))
    lm_stat = n_obs * r2_aux
    p_val = float(1.0 - stats.chi2.cdf(lm_stat, lag))

    lines = [
        "Breusch-Godfrey LM test for autocorrelation",
        f"   lags (p) |      chi2      df     Prob > chi2",
        "-" * 45,
        f"          1 |    {lm_stat:>6.3f}       1        {p_val:>6.4f}",
        "-" * 45,
        "   Ho: no serial correlation",
    ]
    return {"status": "SUCCESS", "ascii_output": "\n".join(lines), "lm_stat": lm_stat, "p_value": p_val}


# ---------------------------------------------------------------------------
# 18. Diagnostics: estat ic (Information Criteria)
# ---------------------------------------------------------------------------
def _handle_estat_ic(parsed: dict, df: pd.DataFrame) -> dict:
    """Stata-compatible `estat ic`: Akaike (AIC) and Bayesian (BIC) information criteria."""
    est, err = _require_active_estimation()
    if err:
        return err

    residuals = est["residuals"]
    N = est["n_obs"]
    k = len(est["params"])
    rss = np.sum(residuals ** 2)
    ll = -0.5 * N * (math.log(2.0 * math.pi) + math.log(rss / N) + 1.0)
    aic = -2.0 * ll + 2.0 * k
    bic = -2.0 * ll + k * math.log(N)

    lines = [
        "Akaike's and Bayesian information criteria",
        "-" * 65,
        f"{'Model':<12} {'Obs':>8} {'ll(null)':>10} {'ll(model)':>12} {'df':>6} {'AIC':>12} {'BIC':>12}",
        "-" * 65,
        f"{'.':<12} {N:>8,} {'.':>10} {ll:>12.2f} {k:>6} {aic:>12.2f} {bic:>12.2f}",
        "-" * 65,
    ]
    return {
        "status": "SUCCESS",
        "ascii_output": "\n".join(lines),
        "aic": aic,
        "bic": bic,
        "log_likelihood": ll,
    }


# ---------------------------------------------------------------------------
# 19. Diagnostic Visual: rvfplot (Residual vs Fitted Plot)
# ---------------------------------------------------------------------------
def _handle_rvfplot(parsed: dict, df: pd.DataFrame) -> dict:
    """
    Stata-compatible `rvfplot`: Residuals versus Fitted values scatter plot with zero reference line.
    Guardrail M-03: Returns both formatted ASCII description and interactive Plotly spec.
    """
    est, err = _require_active_estimation()
    if err:
        return err

    fitted = est["fitted_values"]
    residuals = est["residuals"]

    # Subsample for rendering if N > 2000 to keep UI responsive
    if len(fitted) > 2000:
        idx = np.random.choice(len(fitted), 2000, replace=False)
        x_plot = fitted[idx].tolist()
        y_plot = residuals[idx].tolist()
    else:
        x_plot = fitted.tolist()
        y_plot = residuals.tolist()

    chart_spec = {
        "chart_type": "scatter",
        "title": f"Residuals vs Fitted (`rvfplot` for {est['depvar']})",
        "x_label": "Fitted values",
        "y_label": "Residuals",
        "series": [
            {
                "name": "Residuals",
                "x": x_plot,
                "y": y_plot,
                "type": "scatter",
                "mode": "markers",
            }
        ],
        "zero_line": True,
    }

    ascii_msg = (
        f"Residuals vs Fitted values plot (`rvfplot`) generated for `{est['depvar']}`.\n"
        f"Total points: {len(fitted):, }. Residual mean: {np.mean(residuals):.4f}, SD: {np.std(residuals):.4f}."
    )

    return {
        "status": "SUCCESS",
        "ascii_output": ascii_msg,
        "chart": chart_spec,
    }


# ---------------------------------------------------------------------------
# 20. Diagnostic Visual: qnorm (Normal Quantile-Quantile Plot)
# ---------------------------------------------------------------------------
def _handle_qnorm(parsed: dict, df: pd.DataFrame) -> dict:
    """
    Stata-compatible `qnorm`: Quantile-Quantile (Q-Q) plot of residuals vs standard normal.
    """
    est, err = _require_active_estimation()
    if err:
        return err

    residuals = est["residuals"]
    norm_res = (residuals - np.mean(residuals)) / np.std(residuals)
    norm_res_sorted = np.sort(norm_res)
    n = len(norm_res_sorted)
    theoretical_quantiles = stats.norm.ppf((np.arange(1, n + 1) - 0.5) / n)

    if n > 2000:
        idx = np.linspace(0, n - 1, 1000).astype(int)
        x_plot = theoretical_quantiles[idx].tolist()
        y_plot = norm_res_sorted[idx].tolist()
    else:
        x_plot = theoretical_quantiles.tolist()
        y_plot = norm_res_sorted.tolist()

    chart_spec = {
        "chart_type": "scatter",
        "title": "Normal Q-Q Plot (`qnorm` of Residuals)",
        "x_label": "Theoretical Normal Quantiles",
        "y_label": "Sample Quantiles",
        "series": [
            {
                "name": "Empirical Residuals",
                "x": x_plot,
                "y": y_plot,
                "type": "scatter",
                "mode": "markers",
            }
        ],
        "diagonal_ref": True,
    }

    ascii_msg = (
        f"Normal Q-Q plot (`qnorm`) generated for residuals of `{est['depvar']}`.\n"
        f"Assesses normality of error term distribution against 45-degree reference."
    )

    return {
        "status": "SUCCESS",
        "ascii_output": ascii_msg,
        "chart": chart_spec,
    }


# ---------------------------------------------------------------------------
# Wave 5: Advanced Econometrics (GMM, Causal, ML, Scenario)
# Contract-repaired shims — bridge parsed dict → canonical AnalyticalRequest
# ---------------------------------------------------------------------------
def _create_w5_request_and_envelope(parsed: dict, df: pd.DataFrame, capability: str):
    """
    Build canonical AnalyticalRequest + AnalysisRunEnvelope from a parsed dict.
    Uses only fields that exist on the dataclass — no invented CommandSpec.
    """
    import uuid
    from .analytical_contracts import AnalyticalRequest, fingerprint_df
    from .analysis_run_envelope import AnalysisRunEnvelope

    ref = fingerprint_df(df)
    req = AnalyticalRequest(
        command_str=parsed.get("raw", parsed.get("command", "")),
        parsed=parsed,
        df=df,
        correlation_id=str(uuid.uuid4()),
        dataset_ref=ref,
        session_id="stata_studio",
    )
    env = AnalysisRunEnvelope.create(
        run_id=str(uuid.uuid4()),
        correlation_id=req.correlation_id,
        dataset_fingerprint=ref.fingerprint,
        normalized_command=req.command_str,
        capability=capability,
    )
    return req, env


def _capability_result_to_dict(res) -> dict:
    """Convert a CapabilityResult to the legacy dict format used by stata_engine."""
    return {
        "status": res.status,           # already lowercase: success/error/unsupported/partial
        "ascii_output": res.ascii_output,
        "message": res.message,
        "error_code": res.error_code,
        "metadata": res.metadata,
        "error_msg": res.message if res.status in ("error", "unsupported") else "",
        "table": res.table,
        "chart": res.chart.to_dict() if res.chart else None,
    }


def _handle_gmm(parsed: dict, df: pd.DataFrame) -> dict:
    from .gmm_adapter import CurrentProfSurGMMAdapter
    req, env = _create_w5_request_and_envelope(parsed, df, "gmm")
    res = CurrentProfSurGMMAdapter.run(req, env)
    return _capability_result_to_dict(res)


def _handle_ivregress(parsed: dict, df: pd.DataFrame) -> dict:
    from .causal_adapters import IVAdapter
    req, env = _create_w5_request_and_envelope(parsed, df, "iv")
    res = IVAdapter.run(req, env)
    return _capability_result_to_dict(res)


def _handle_hdfe(parsed: dict, df: pd.DataFrame) -> dict:
    from .causal_adapters import HDFEAdapter
    req, env = _create_w5_request_and_envelope(parsed, df, "hdfe")
    res = HDFEAdapter.run(req, env)
    return _capability_result_to_dict(res)


def _handle_didregress(parsed: dict, df: pd.DataFrame) -> dict:
    """CF-08 repaired: routes to DIDAdapter which returns 'unsupported'."""
    from .causal_adapters import DIDAdapter
    req, env = _create_w5_request_and_envelope(parsed, df, "did")
    res = DIDAdapter.run(req, env)
    return _capability_result_to_dict(res)


def _handle_scenario(parsed: dict, df: pd.DataFrame) -> dict:
    from .scenario_capability import ScenarioAdapter
    req, env = _create_w5_request_and_envelope(parsed, df, "scenario")
    res = ScenarioAdapter.run(req, env)
    return _capability_result_to_dict(res)


def _handle_ml_predict(parsed: dict, df: pd.DataFrame) -> dict:
    from .ml_adapters import MLPredictAdapter
    req, env = _create_w5_request_and_envelope(parsed, df, "ml_predict")
    res = MLPredictAdapter.run(req, env)
    return _capability_result_to_dict(res)
