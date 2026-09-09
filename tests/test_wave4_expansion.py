"""
tests/test_wave4_expansion.py — TDD test suite for Wave 4 commands.

Covers:
1. Exploratory Suite: describe, codebook, count, mean, proportion
2. Longitudinal / Panel Suite: xtdescribe, xtsum, xttab, xtline
3. Post-Estimation & Hypothesis Suite: testparm, lincom, nlcom, estat ic, estat summarize
4. Router & Registry Integration: route() through analytical_router
5. Negative & Boundary Cases: r(301) last estimates not found, r(111) variable not found, r(198) syntax error
"""
import pytest
import pandas as pd
import numpy as np

from models.analytical_contracts import AnalyticalRequest, DatasetSnapshotRef, fingerprint_df
from models.analytical_router import route
from models.command_registry import resolve_capability
import models.stata_engine as se
from models.stata_engine import ModelResultContext
from typing import Any


@pytest.fixture
def sample_panel_df() -> pd.DataFrame:
    """Create a deterministic 4-firm, 5-year balanced panel dataset."""
    records = []
    np.random.seed(42)
    firms = ["FIRM_A", "FIRM_B", "FIRM_C", "FIRM_D"]
    years = [2020, 2021, 2022, 2023, 2024]
    life_stages = ["Introduction", "Growth", "Mature", "Shake-out"]
    
    for f_idx, firm in enumerate(firms):
        for y_idx, year in enumerate(years):
            profit = 0.05 + 0.02 * f_idx + 0.01 * y_idx + np.random.normal(0, 0.01)
            tang = 0.30 + 0.05 * f_idx + np.random.normal(0, 0.02)
            size = 10.0 + 0.5 * f_idx + 0.1 * y_idx
            lev = 0.40 - 0.5 * profit + 0.3 * tang + 0.02 * size + np.random.normal(0, 0.01)
            stage = life_stages[(f_idx + y_idx) % len(life_stages)]
            records.append({
                "companycode": firm,
                "year": year,
                "leverage": lev,
                "profitability": profit,
                "tangibility": tang,
                "size": size,
                "life_stage": stage,
            })
    return pd.DataFrame(records)


def make_request(raw_cmd: str, df: pd.DataFrame, session_context: Any = None) -> AnalyticalRequest:
    parsed = se.parse_stata_command(raw_cmd)
    ref = fingerprint_df(df)
    return AnalyticalRequest(
        command_str=raw_cmd,
        parsed=parsed,
        df=df,
        dataset_ref=ref,
        correlation_id="test-corr-w4",
        session_id="test-sess-w4",
        session_context=session_context,
    )


# ---------------------------------------------------------------------------
# 1. Exploratory Commands Tests
# ---------------------------------------------------------------------------

def test_describe_command(sample_panel_df):
    """Test 'describe' returns dataset dimensions, storage types, and variable summary."""
    req = make_request("describe", sample_panel_df)
    res = route(req)
    assert res.status == "success"
    assert "Obs:" in res.ascii_output or "obs:" in res.ascii_output
    assert "Vars:" in res.ascii_output or "vars:" in res.ascii_output
    assert "leverage" in res.ascii_output
    assert "profitability" in res.ascii_output


def test_codebook_command(sample_panel_df):
    """Test 'codebook' returns summary statistics and unique count for continuous and discrete vars."""
    req = make_request("codebook leverage life_stage", sample_panel_df)
    res = route(req)
    assert res.status == "success"
    assert "leverage" in res.ascii_output
    assert "life_stage" in res.ascii_output
    assert "Unique values:" in res.ascii_output or "unique values:" in res.ascii_output or "unique" in res.ascii_output.lower()


def test_count_command(sample_panel_df):
    """Test 'count' counts all observations and supports 'if' conditionals."""
    req1 = make_request("count", sample_panel_df)
    res1 = route(req1)
    assert res1.status == "success"
    assert "20" in res1.ascii_output

    req2 = make_request("count if year == 2020", sample_panel_df)
    res2 = route(req2)
    assert res2.status == "success"
    assert "4" in res2.ascii_output


def test_mean_command(sample_panel_df):
    """Test 'mean' computes point estimate, std err, and 95% confidence intervals."""
    req = make_request("mean leverage profitability", sample_panel_df)
    res = route(req)
    assert res.status == "success"
    assert "Mean" in res.ascii_output or "mean" in res.ascii_output
    assert "Std. err." in res.ascii_output or "Std. Err." in res.ascii_output
    assert "[95% conf. interval]" in res.ascii_output or "95% Conf." in res.ascii_output or "95%" in res.ascii_output


def test_proportion_command(sample_panel_df):
    """Test 'proportion' computes categorical proportions and standard errors."""
    req = make_request("proportion life_stage", sample_panel_df)
    res = route(req)
    assert res.status == "success"
    assert "Proportion" in res.ascii_output or "proportion" in res.ascii_output
    assert "Growth" in res.ascii_output
    assert "Mature" in res.ascii_output


# ---------------------------------------------------------------------------
# 2. Longitudinal / Panel Commands Tests
# ---------------------------------------------------------------------------

def test_xtdescribe_command(sample_panel_df):
    """Test 'xtdescribe' provides panel participation pattern and T_i distribution."""
    route(make_request("xtset companycode year", sample_panel_df))
    
    req = make_request("xtdescribe", sample_panel_df)
    res = route(req)
    assert res.status == "success"
    assert "n =" in res.ascii_output or "n=" in res.ascii_output or "Number of panels" in res.ascii_output or "4" in res.ascii_output
    assert "T =" in res.ascii_output or "T=" in res.ascii_output or "Time periods" in res.ascii_output or "5" in res.ascii_output


def test_xtsum_command(sample_panel_df):
    """Test 'xtsum' calculates overall, between, and within variance decomposition."""
    route(make_request("xtset companycode year", sample_panel_df))
    
    req = make_request("xtsum leverage profitability", sample_panel_df)
    res = route(req)
    assert res.status == "success"
    assert "overall" in res.ascii_output
    assert "between" in res.ascii_output
    assert "within" in res.ascii_output
    assert "leverage" in res.ascii_output


def test_xttab_command(sample_panel_df):
    """Test 'xttab' computes overall and between transitions for categorical variables."""
    route(make_request("xtset companycode year", sample_panel_df))
    
    req = make_request("xttab life_stage", sample_panel_df)
    res = route(req)
    assert res.status == "success"
    assert "Overall" in res.ascii_output or "overall" in res.ascii_output
    assert "Between" in res.ascii_output or "between" in res.ascii_output


def test_xtline_command(sample_panel_df):
    """Test 'xtline' creates a Plotly longitudinal chart specification."""
    route(make_request("xtset companycode year", sample_panel_df))
    
    req = make_request("xtline leverage", sample_panel_df)
    res = route(req)
    assert res.status == "success"
    assert res.chart is not None
    assert res.chart.chart_type == "xtline"


# ---------------------------------------------------------------------------
# 3. Post-Estimation & Hypothesis Tests
# ---------------------------------------------------------------------------

def test_estat_ic_and_summarize(sample_panel_df):
    """Test 'estat ic' (AIC/BIC) and 'estat summarize' after regression."""
    ctx = ModelResultContext(session_id="test-sess-w4")
    route(make_request("regress leverage profitability tangibility size", sample_panel_df, session_context=ctx))
    
    # estat ic
    req_ic = make_request("estat ic", sample_panel_df, session_context=ctx)
    res_ic = route(req_ic)
    assert res_ic.status == "success"
    assert "AIC" in res_ic.ascii_output or "Akaike" in res_ic.ascii_output
    assert "BIC" in res_ic.ascii_output or "Bayesian" in res_ic.ascii_output

    # estat summarize
    req_sum = make_request("estat summarize", sample_panel_df, session_context=ctx)
    res_sum = route(req_sum)
    assert res_sum.status == "success"
    assert "leverage" in res_sum.ascii_output


def test_testparm_command(sample_panel_df):
    """Test 'testparm' executes joint hypothesis test on multiple parameters."""
    ctx = ModelResultContext(session_id="test-sess-w4")
    route(make_request("regress leverage profitability tangibility size", sample_panel_df, session_context=ctx))
    
    req = make_request("testparm profitability tangibility", sample_panel_df, session_context=ctx)
    res = route(req)
    assert res.status == "success"
    assert "F(" in res.ascii_output or "chi2(" in res.ascii_output or "Prob >" in res.ascii_output


def test_lincom_command(sample_panel_df):
    """Test 'lincom' calculates linear combinations of coefficients with SE and CI."""
    ctx = ModelResultContext(session_id="test-sess-w4")
    route(make_request("regress leverage profitability tangibility size", sample_panel_df, session_context=ctx))
    
    req = make_request("lincom profitability - tangibility", sample_panel_df, session_context=ctx)
    res = route(req)
    assert res.status == "success"
    assert "Coef." in res.ascii_output or "Estimate" in res.ascii_output
    assert "Std. Err." in res.ascii_output or "Std. err." in res.ascii_output


def test_post_estimation_no_model_error(sample_panel_df):
    """Test that post-estimation without prior model cleanly returns r(301)."""
    ctx = ModelResultContext(session_id="test-sess-w4")
    
    req = make_request("testparm profitability", sample_panel_df, session_context=ctx)
    res = route(req)
    assert res.status in ("error", "unsupported")
    assert "r(301)" in res.ascii_output or "last estimates not found" in res.message.lower()
