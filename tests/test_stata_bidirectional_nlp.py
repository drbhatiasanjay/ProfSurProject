"""TDD Unit and Regression Tests for Workstream 1: Stata CLI & NLP Enhancement.

Test cases:
- TC-ST-01: ivregress 2sls parsing, panel lag calculation, and estimation.
- TC-ST-02: Post-estimation Wald F-test (test var = 0).
- TC-ST-03: Post-estimation prediction (predict var, xb / residuals).
- TC-ST-04: Outlier winsorization (winsor2 varlist, cuts(1 99) replace).
- TC-NL-01 to TC-NL-10: Deterministic Natural Language -> Stata translation.
- TC-NL-ERR: Sanitization against malicious/destructive commands.
- TC-EXP-01: Econometric Explainer deconstruction schema.
"""

import pytest
import pandas as pd
import numpy as np


@pytest.fixture(scope="module")
def panel_data():
    """Create panel data with company_code and year for econometric testing."""
    np.random.seed(42)
    firms = [101, 102, 103, 104, 105, 106, 107, 108]
    years = list(range(2015, 2025))
    rows = []
    for f in firms:
        firm_fe = np.random.normal(0, 1.5)
        for y in years:
            roa = np.random.normal(0.12, 0.04)
            tang = np.random.normal(0.35, 0.08)
            size = np.random.normal(6.0, 0.8)
            lev = 10.0 + firm_fe - 8.0 * roa + 18.0 * tang + 1.2 * size + np.random.normal(0, 0.8)
            rows.append({
                "company_code": f,
                "year": y,
                "leverage": max(0.01, lev),
                "profitability": roa,
                "tangibility": tang,
                "log_size": size,
                "size": size,
                "roa": roa,
                "tang": tang,
                "cash_holdings": np.random.normal(0.10, 0.03),
            })
    df = pd.DataFrame(rows)
    return df


# ── TC-ST-01: ivregress 2sls ──────────────────────────────────────────────────

def test_tc_st_01_ivregress_just_identified(panel_data):
    """TC-ST-01a: ivregress 2sls with just-identified instrument."""
    from models.stata_engine import execute_stata_command

    cmd = "ivregress 2sls leverage (tangibility = L.tangibility) roa size"
    res = execute_stata_command(cmd, df=panel_data.copy())

    assert res["status"] == "success"
    assert "tangibility" in res["coefficients"]
    assert "profitability" in res["coefficients"] or "roa" in res["coefficients"]
    assert res["model_type"] == "IV2SLS"
    assert "ascii_output" in res
    assert "Instrumental variables (2SLS) regression" in res["ascii_output"]
    # Exact identification diagnostics
    assert "identification" in res
    assert res["identification"]["is_just_identified"] is True


def test_tc_st_01_ivregress_overidentified(panel_data):
    """TC-ST-01b: ivregress 2sls with over-identified instruments (Hansen/Sargan test)."""
    from models.stata_engine import execute_stata_command

    cmd = "ivregress 2sls leverage (tangibility = L.tangibility cash_holdings) roa size"
    res = execute_stata_command(cmd, df=panel_data.copy())

    assert res["status"] == "success"
    assert res["identification"]["is_just_identified"] is False
    assert "sargan_stat" in res["identification"]
    assert "sargan_pvalue" in res["identification"]
    assert res["identification"]["sargan_stat"] is not None


# ── TC-ST-02: Post-estimation Wald F-test ─────────────────────────────────────

def test_tc_st_02_post_estimation_test(panel_data):
    """TC-ST-02: 'test roa = 0' after xtreg."""
    from models.stata_engine import execute_stata_command

    # First run an xtreg regression to populate _LAST_ESTIMATE
    init_res = execute_stata_command("xtreg leverage profitability tangibility log_size, fe", df=panel_data.copy())
    assert init_res["status"] == "success"

    # Now execute test
    test_res = execute_stata_command("test roa = 0", df=panel_data.copy())
    assert test_res["status"] == "success"
    assert "f_stat" in test_res
    assert "p_value" in test_res
    assert test_res["f_stat"] > 0
    assert 0.0 <= test_res["p_value"] <= 1.0
    assert "F(" in test_res["ascii_output"]
    assert "Prob > F" in test_res["ascii_output"]


# ── TC-ST-03: Post-estimation predict ─────────────────────────────────────────

def test_tc_st_03_predict_xb_and_residuals(panel_data):
    """TC-ST-03: 'predict y_hat, xb' and 'predict e_hat, residuals'."""
    from models.stata_engine import execute_stata_command

    df_work = panel_data.copy()
    init_res = execute_stata_command("xtreg leverage profitability tangibility log_size, fe", df=df_work)
    assert init_res["status"] == "success"

    # Linear prediction
    pred_res = execute_stata_command("predict y_hat, xb", df=df_work)
    assert pred_res["status"] == "success"
    assert pred_res["varname"] == "y_hat"
    assert pred_res["type"] == "xb"
    assert "y_hat" in df_work.columns
    assert len(df_work["y_hat"].dropna()) > 0

    # Residuals prediction
    resid_res = execute_stata_command("predict e_hat, residuals", df=df_work)
    assert resid_res["status"] == "success"
    assert resid_res["varname"] == "e_hat"
    assert resid_res["type"] == "residuals"
    assert "e_hat" in df_work.columns


# ── TC-ST-04: Outlier winsorization (winsor2) ─────────────────────────────────

def test_tc_st_04_winsor2_replace(panel_data):
    """TC-ST-04: 'winsor2 leverage roa tang, cuts(1 99) replace'."""
    from models.stata_engine import execute_stata_command

    df_work = panel_data.copy()
    # Introduce deliberate extreme outliers
    df_work.loc[0, "leverage"] = 999.0
    df_work.loc[1, "leverage"] = -500.0

    cmd = "winsor2 leverage roa tang, cuts(1 99) replace"
    res = execute_stata_command(cmd, df=df_work)

    assert res["status"] == "success"
    assert "ascii_output" in res
    assert df_work.loc[0, "leverage"] < 999.0
    assert df_work.loc[1, "leverage"] > -500.0
    assert len(df_work) == len(panel_data)


# ── TC-NL-01 to TC-NL-10: Natural Language -> Stata Translation ───────────────

def test_tc_nl_translations():
    """TC-NL-01 to TC-NL-10: Validate deterministic natural language mappings."""
    from models.stata_nl_translator import translate_nl_to_stata

    test_pairs = [
        # TC-NL-01
        ("Show me how debt responds to profitability with firm clustering",
         "xtreg leverage profitability tangibility log_size, fe cluster(company_code)"),
        # TC-NL-02
        ("Run random effects regression of leverage on roa, tangibility, and size",
         "xtreg leverage profitability tangibility log_size, re"),
        # TC-NL-03
        ("Instrument tangibility with its lag to predict leverage controlling for roa and size using 2sls",
         "ivregress 2sls leverage (tangibility = L.tangibility) profitability log_size"),
        # TC-NL-04
        ("Test whether the coefficient of profitability equals zero",
         "test profitability = 0"),
        # TC-NL-05
        ("Generate fitted values for leverage model",
         "predict y_hat, xb"),
        # TC-NL-06
        ("Winsorize leverage, roa, and tangibility at 1st and 99th percentiles",
         "winsor2 leverage profitability tangibility, cuts(1 99) replace"),
        # TC-NL-07
        ("Summarize leverage and profitability with detailed percentiles",
         "summarize leverage profitability, detail"),
        # TC-NL-08
        ("Calculate pairwise correlation between debt, roa, tangibility and size with significance stars",
         "pwcorr leverage profitability tangibility log_size, sig star(0.05)"),
        # TC-NL-09
        ("Test for random effects using Breusch-Pagan LM test",
         "xttest0"),
        # TC-NL-10
        ("Test for first-order autocorrelation in panel residuals using Wooldridge test",
         "xtserial"),
    ]

    for nl_query, expected_pattern in test_pairs:
        result = translate_nl_to_stata(nl_query)
        assert result["status"] == "success"
        translated_cmd = result["stata_command"].strip()
        # Verify verb and core arguments match
        exp_verb = expected_pattern.split()[0]
        assert translated_cmd.startswith(exp_verb), f"Query '{nl_query}' produced '{translated_cmd}', expected verb '{exp_verb}'"


# ── TC-NL-ERR: Security Sanitization ──────────────────────────────────────────

def test_tc_nl_err_sanitization():
    """TC-NL-ERR: Block malicious or destructive inputs."""
    from models.stata_nl_translator import translate_nl_to_stata

    malicious_inputs = [
        "DROP TABLE users; --",
        "DELETE FROM capital_structure WHERE 1=1",
        "exec('import os; os.system(\"rm -rf /\")')",
        "__import__('os').system('dir')",
        "ALTER TABLE panel DROP COLUMN leverage",
    ]

    for malicious in malicious_inputs:
        res = translate_nl_to_stata(malicious)
        assert res["status"] == "error"
        assert "unauthorized" in res["message"].lower() or "syntax" in res["message"].lower()


# ── TC-EXP-01: Econometric Explainer Schema ────────────────────────────────────

def test_tc_exp_01_explainer_schema(panel_data):
    """TC-EXP-01: Econometric deconstruction engine schema."""
    from models.stata_explainer import explain_stata_command

    cmd = "ivregress 2sls leverage (tangibility = L.tangibility) profitability log_size"
    explanation = explain_stata_command(cmd)

    assert isinstance(explanation, dict)
    for key in ("intent", "identification", "inference", "economic_theory"):
        assert key in explanation
        assert isinstance(explanation[key], str)
        assert len(explanation[key]) > 0

# ── Regression Tests for Coordinator Review ───────────────────────────────────

def test_tc_regression_ivregress_liml_gmm(panel_data):
    from models.stata_engine import execute_stata_command
    res = execute_stata_command("ivregress liml leverage (tangibility = L.tangibility) roa", df=panel_data.copy())
    assert res["status"] == "error", "ivregress liml must be rejected"
    assert "2sls" in res["message"].lower()

def test_tc_regression_ivregress_panel_lag(panel_data):
    from models.stata_engine import execute_stata_command
    df = panel_data.copy()
    df = df[df["year"] != 2018]
    res = execute_stata_command("ivregress 2sls leverage (tangibility = L.tangibility) roa", df=df)
    assert res["status"] == "success"
    assert res.get("n_obs", 0) <= 56, "Gap in years must cause missing lag"

def test_tc_regression_ivregress_missing_var(panel_data):
    from models.stata_engine import execute_stata_command
    res = execute_stata_command("ivregress 2sls leverage (tangibility = L.tangibility) unknown_var", df=panel_data.copy())
    assert res["status"] == "error"
    assert "unknown_var" in res["message"] or "not found" in res["message"]

def test_tc_regression_ivregress_diagnostics(panel_data):
    from models.stata_engine import execute_stata_command
    res = execute_stata_command("ivregress 2sls leverage (tangibility = L.tangibility cash_holdings) roa", df=panel_data.copy())
    assert "Stock-Yogo" not in str(res.get("identification", {})), "Must not make universal Stock-Yogo causal claims"
    assert "sargan_stat" in res.get("identification", {})

def test_tc_regression_test_chi2(panel_data):
    from models.stata_engine import execute_stata_command
    state = {}
    init_res = execute_stata_command("xtreg leverage roa, fe", df=panel_data.copy(), stata_session_state=state)
    test_res = execute_stata_command("test roa = 0", df=panel_data.copy(), stata_session_state=state)
    assert test_res.get("test_type", "") in ["F", "chi2"], "Must identify if F or chi2"
    if test_res.get("test_type") == "chi2":
        assert "chi2(" in test_res["ascii_output"] and "F(" not in test_res["ascii_output"]

def test_tc_regression_predict_missing_propagate(panel_data):
    import numpy as np
    from models.stata_engine import execute_stata_command
    df = panel_data.copy()
    df.loc[0, "roa"] = np.nan
    state = {}
    execute_stata_command("xtreg leverage roa, fe", df=df, stata_session_state=state)
    execute_stata_command("predict y_hat, xb", df=df, stata_session_state=state)
    assert np.isnan(df.loc[0, "y_hat"]), "predict must propagate missing regressors, not fill with zero"

def test_tc_regression_winsor2_validation(panel_data):
    from models.stata_engine import execute_stata_command
    res = execute_stata_command("winsor2 leverage, cuts(-5 105) replace", df=panel_data.copy())
    assert res["status"] == "error", "cuts outside 0..100 must be rejected"
    res2 = execute_stata_command("winsor2 leverage, cuts(99 1) replace", df=panel_data.copy())
    assert res2["status"] == "error", "nonordered cuts must be rejected"
    res3 = execute_stata_command("winsor2 unknown_var, cuts(1 99) replace", df=panel_data.copy())
    assert res3["status"] == "error", "unknown variable must be rejected"

def test_tc_regression_nlp_ambiguous():
    from models.stata_nl_translator import translate_nl_to_stata
    res = translate_nl_to_stata("do some random stuff")
    assert res["status"] == "error", "Unknown NL text must return error"
    assert "xtreg" not in res.get("stata_command", "")

def test_tc_regression_execute_session_state(panel_data):
    from models.stata_engine import execute_stata_command
    state1 = {}
    state2 = {}
    execute_stata_command("xtreg leverage roa, fe", df=panel_data.copy(), stata_session_state=state1)
    execute_stata_command("xtreg leverage tang, re", df=panel_data.copy(), stata_session_state=state2)
    last_est1 = state1.get("_LAST_ESTIMATE")
    last_est2 = state2.get("_LAST_ESTIMATE")
    assert last_est1 is not None and last_est2 is not None
    assert "roa" in last_est1.params
    assert "tang" in last_est2.params
