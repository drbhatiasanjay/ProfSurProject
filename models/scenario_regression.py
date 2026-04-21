"""
Pure helpers for Scenario Analysis leverage OLS (no Streamlit).

Used by pages/3_scenarios.py so coefficients can be unit-tested.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

PREDICTORS = ["profitability", "tangibility", "tax", "log_size", "tax_shield", "dividend"]

_FALLBACK_COEFS: dict = {
    "intercept": 21.0,
    "profitability": -0.3,
    "tangibility": 0.15,
    "tax": -0.05,
    "log_size": 2.0,
    "tax_shield": 0.1,
    "dividend": -0.02,
    "r_squared": 0.0,
    "n_obs": 0,
}

_DEFAULT_MEANS: dict[str, float] = {
    "prof": 10.0,
    "tang": 30.0,
    "tax": 20.0,
    "log_size": 7.0,
    "tax_shield": 5.0,
    "dvnd": 2.0,
}


def _prepare_ols_frame(df: pd.DataFrame) -> pd.DataFrame:
    need = ["leverage", *PREDICTORS]
    if df.empty or any(c not in df.columns for c in need):
        return pd.DataFrame()
    return df[need].dropna()


def compute_leverage_ols_coefs(df: pd.DataFrame) -> dict:
    """Simple OLS of leverage on PREDICTORS; same numerics as legacy Scenarios SQL path."""
    work = _prepare_ols_frame(df)
    if work.empty:
        return dict(_FALLBACK_COEFS)

    y = work["leverage"].values
    X = work[PREDICTORS].fillna(0).values
    X = np.column_stack([np.ones(len(X)), X])

    try:
        beta = np.linalg.lstsq(X, y, rcond=None)[0]
        coefs: dict = {"intercept": float(beta[0])}
        for i, name in enumerate(PREDICTORS):
            coefs[name] = float(beta[i + 1])
        y_hat = X @ beta
        ss_res = float(np.sum((y - y_hat) ** 2))
        ss_tot = float(np.sum((y - np.mean(y)) ** 2))
        coefs["r_squared"] = float(1 - ss_res / ss_tot) if ss_tot > 0 else 0.0
        coefs["n_obs"] = int(len(work))
    except np.linalg.LinAlgError:
        coefs = dict(_FALLBACK_COEFS)
    return coefs


def leverage_predictor_sample_means(df: pd.DataFrame) -> dict:
    """
    Means of predictors among rows with non-null leverage (matches prior SQL AVG ... WHERE leverage IS NOT NULL).
    Keys: prof, tang, tax, log_size, tax_shield, dvnd — same as legacy get_sample_means().
    """
    if df.empty or "leverage" not in df.columns:
        return dict(_DEFAULT_MEANS)
    sub = df[df["leverage"].notna()]
    if sub.empty:
        return dict(_DEFAULT_MEANS)

    out: dict[str, float] = {}
    mapping = [
        ("profitability", "prof"),
        ("tangibility", "tang"),
        ("tax", "tax"),
        ("log_size", "log_size"),
        ("tax_shield", "tax_shield"),
        ("dividend", "dvnd"),
    ]
    for col, key in mapping:
        dflt = _DEFAULT_MEANS[key]
        if col not in sub.columns:
            out[key] = dflt
            continue
        v = sub[col].mean(skipna=True)
        out[key] = float(v) if pd.notna(v) else dflt
    return out
