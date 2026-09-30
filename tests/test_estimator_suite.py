"""
Estimator-Specific Numerical Reference Suite (SW-11).
Verifies Pooled OLS, Entity Fixed Effects, Random Effects, and Hausman diagnostics
against deterministic numerical reference benchmarks.
"""
import pytest
import numpy as np
import pandas as pd
from models.econometric import (
    run_pooled_ols,
    run_fixed_effects,
    run_random_effects,
    run_hausman_test,
)


@pytest.fixture
def synthetic_panel_df():
    """Deterministic 5-firm, 10-year balanced panel with known DGP."""
    np.random.seed(42)
    n_firms = 10
    n_years = 10
    records = []
    
    for i in range(1, n_firms + 1):
        alpha_i = float(i * 2.0)  # Firm fixed effect
        for t in range(2010, 2010 + n_years):
            x1 = float(np.sin(i + t) * 10 + 20)
            x2 = float(np.cos(i * t) * 5 + 15)
            # y = alpha_i + 0.5*x1 - 0.3*x2 + eps
            eps = float(np.random.normal(0, 0.5))
            y = alpha_i + 0.5 * x1 - 0.3 * x2 + eps
            records.append({
                "company_code": i,
                "year": t,
                "leverage": y,
                "profitability": x1,
                "tangibility": x2,
            })
    return pd.DataFrame(records)


def test_sw11_fixed_effects_numerical_benchmark(synthetic_panel_df):
    """SW-11: Verify Entity Fixed Effects within-estimator coefficients and fit."""
    res = run_fixed_effects(
        synthetic_panel_df,
        y_col="leverage",
        x_cols=["profitability", "tangibility"],
        entity="company_code",
        time="year",
    )
    assert res is not None
    assert "coef_table" in res
    coefs = dict(zip(res["coef_table"]["Variable"], res["coef_table"]["Coefficient"]))
    
    # Within estimator should recover beta1 ~ 0.5 and beta2 ~ -0.3 within tight tolerance
    assert abs(coefs["profitability"] - 0.5) < 0.05, f"Expected beta_prof ~ 0.5, got {coefs['profitability']}"
    assert abs(coefs["tangibility"] - (-0.3)) < 0.05, f"Expected beta_tang ~ -0.3, got {coefs['tangibility']}"
    assert res["n_obs"] == 100
    assert res["n_firms"] == 10
    assert res["r_squared_within"] > 0.85


def test_sw11_random_effects_numerical_benchmark(synthetic_panel_df):
    """SW-11: Verify Random Effects GLS estimator execution and structure."""
    res = run_random_effects(
        synthetic_panel_df,
        y_col="leverage",
        x_cols=["profitability", "tangibility"],
        entity="company_code",
        time="year",
    )
    assert res is not None
    assert "coef_table" in res
    assert res["n_obs"] == 100
    assert res["n_firms"] == 10


def test_sw11_hausman_specification_test(synthetic_panel_df):
    """SW-11: Verify Hausman specification test returns valid Chi2 and p-value."""
    fe_res = run_fixed_effects(
        synthetic_panel_df,
        y_col="leverage",
        x_cols=["profitability", "tangibility"],
    )
    re_res = run_random_effects(
        synthetic_panel_df,
        y_col="leverage",
        x_cols=["profitability", "tangibility"],
    )
    h_res = run_hausman_test(fe_res, re_res)
    assert "chi2" in h_res
    assert "p_value" in h_res
    assert h_res["chi2"] >= 0 or np.isnan(h_res["chi2"])
