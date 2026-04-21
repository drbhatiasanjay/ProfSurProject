"""Unit tests for scenario leverage OLS helpers."""

from __future__ import annotations

import pandas as pd

from models.scenario_regression import compute_leverage_ols_coefs, leverage_predictor_sample_means


def test_compute_leverage_ols_coefs_simple():
    df = pd.DataFrame(
        {
            "leverage": [20.0, 30.0, 25.0],
            "profitability": [10.0, 5.0, 8.0],
            "tangibility": [30.0, 40.0, 35.0],
            "tax": [20.0, 20.0, 20.0],
            "log_size": [7.0, 8.0, 7.5],
            "tax_shield": [5.0, 5.0, 5.0],
            "dividend": [2.0, 2.0, 2.0],
        }
    )
    coefs = compute_leverage_ols_coefs(df)
    assert "intercept" in coefs and "n_obs" in coefs
    assert coefs["n_obs"] == 3
    assert 0.0 <= coefs["r_squared"] <= 1.0


def test_sample_means_keys():
    df = pd.DataFrame(
        {
            "leverage": [10.0, 20.0],
            "profitability": [1.0, 3.0],
            "tangibility": [10.0, 20.0],
            "tax": [5.0, 15.0],
            "log_size": [2.0, 4.0],
            "tax_shield": [1.0, 2.0],
            "dividend": [0.5, 1.5],
        }
    )
    m = leverage_predictor_sample_means(df)
    assert m["prof"] == 2.0
    assert m["tang"] == 15.0


def test_compute_fallback_when_empty():
    out = compute_leverage_ols_coefs(pd.DataFrame())
    assert out["n_obs"] == 0
    assert out["intercept"] == 21.0
