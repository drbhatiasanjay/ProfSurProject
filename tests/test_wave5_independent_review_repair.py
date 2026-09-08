"""End-to-end acceptance contracts from the Wave 5 independent review."""

import uuid
import dataclasses
from pathlib import Path

import numpy as np
import pandas as pd
import pytest
import statsmodels.api as sm

import models.analytical_router as analytical_router
import models.stata_engine as stata_engine
from models.analytical_contracts import AnalyticalRequest, fingerprint_df
from models.analytical_router import route
from models.stata_engine import execute_stata_command, parse_stata_command


@pytest.fixture
def panel_df() -> pd.DataFrame:
    rng = np.random.default_rng(20260908)
    firms = np.repeat(np.arange(30), 6)
    years = np.tile(np.arange(2015, 2021), 30)
    profitability = rng.normal(size=len(firms))
    tangibility = rng.normal(size=len(firms))
    firm_effect = firms * 0.02
    year_effect = (years - years.min()) * -0.03
    error = rng.normal(scale=0.2, size=len(firms))
    leverage = 0.5 + 1.2 * profitability - 0.7 * tangibility + firm_effect + year_effect + error
    return pd.DataFrame({
        "company_code": firms,
        "year": years,
        "leverage": leverage,
        "profitability": profitability,
        "tangibility": tangibility,
        "log_size": rng.normal(5, 0.4, len(firms)),
        "tax": rng.uniform(0.15, 0.35, len(firms)),
        "life_stage": np.where(firms % 2, "Growth", "Maturity"),
    })


def _request(command: str, df: pd.DataFrame) -> AnalyticalRequest:
    parsed = parse_stata_command(command)
    return AnalyticalRequest(
        command_str=command,
        parsed=parsed,
        df=df,
        correlation_id=str(uuid.uuid4()),
        dataset_ref=fingerprint_df(df),
        session_id="wave5_review_repair",
    )


@pytest.mark.parametrize(
    ("command", "invalid_name"),
    [
        ("regress nonexistent_var tangibility", "nonexistent_var"),
        ("regress leverage nonexistent_var", "nonexistent_var"),
        ("tabstat leverage, by(nonexistent_col)", "nonexistent_col"),
        ("xtreg leverage nonexistent_var, fe", "nonexistent_var"),
    ],
)
def test_unknown_variables_fail_closed_through_execute(command, invalid_name, panel_df):
    result = execute_stata_command(command, panel_df, {})

    assert result["status"] == "error"
    assert result["error_code"] == "VARIABLE_NOT_FOUND"
    assert result["metadata"]["stata_rc"] == 111
    assert result["metadata"]["invalid_argument"] == invalid_name
    assert invalid_name in result["message"]
    assert "r(111)" in result["ascii_output"]
    assert "coefficients" not in result
    assert "data" not in result


@pytest.mark.parametrize(
    ("command", "invalid_name"),
    [
        ("regress nonexistent_var tangibility", "nonexistent_var"),
        ("regress leverage nonexistent_var", "nonexistent_var"),
        ("tabstat leverage, by(nonexistent_col)", "nonexistent_col"),
        ("xtreg leverage nonexistent_var, fe", "nonexistent_var"),
    ],
)
def test_unknown_variables_fail_closed_through_router(command, invalid_name, panel_df):
    result = route(_request(command, panel_df))

    assert result.status == "error"
    assert result.error_code == "VARIABLE_NOT_FOUND"
    assert result.metadata["stata_rc"] == 111
    assert result.metadata["invalid_argument"] == invalid_name
    assert invalid_name in result.message
    assert "r(111)" in result.ascii_output
    assert result.table is None


@pytest.mark.parametrize("command", ["regress", "xtreg leverage", "tabstat"])
def test_missing_required_syntax_is_not_treated_as_unknown_variable(command, panel_df):
    result = execute_stata_command(command, panel_df, {})

    assert result["status"] == "error"
    assert result["error_code"] == "SYNTAX_ERROR"
    assert result["metadata"]["stata_rc"] == 198
    assert "r(198)" in result["ascii_output"]


@pytest.mark.parametrize(
    ("command", "handler_name"),
    [
        ("regress leverage nonexistent_var", "_handle_regress"),
        ("tabstat leverage, by(nonexistent_col)", "_handle_tabstat"),
        ("xtreg leverage nonexistent_var, fe", "_handle_xtreg"),
    ],
)
def test_direct_validation_failure_prevents_estimator_dispatch(
    monkeypatch, command, handler_name, panel_df
):
    def unexpected_dispatch(*args, **kwargs):
        raise AssertionError("estimator handler must not run after validation failure")

    monkeypatch.setattr(stata_engine, handler_name, unexpected_dispatch)
    result = stata_engine.execute_stata_command(command, panel_df, {})

    assert result["status"] == "error"
    assert result["error_code"] == "VARIABLE_NOT_FOUND"


def test_router_validation_failure_prevents_handler_resolution(monkeypatch, panel_df):
    def unexpected_resolution(*args, **kwargs):
        raise AssertionError("handler resolution must not occur after validation failure")

    monkeypatch.setattr(analytical_router, "get_handler", unexpected_resolution)
    result = analytical_router.route(_request("regress leverage nonexistent_var", panel_df))

    assert result.status == "error"
    assert result.error_code == "VARIABLE_NOT_FOUND"


@pytest.mark.parametrize(
    "command",
    [
        "ivregress 2sls leverage profitability (tangibility = tax)",
        "test profitability = 0",
        "predict yhat, xb",
        "winsor2 leverage, cuts(1 99)",
    ],
)
def test_ws1_commands_use_behavioral_router_registry_path(monkeypatch, command, panel_df):
    original = analytical_router.get_handler
    seen = []

    def observed_handler(capability, cmd=""):
        handler = original(capability, cmd=cmd)
        seen.append((capability, cmd, handler is not None))
        return handler

    monkeypatch.setattr(analytical_router, "get_handler", observed_handler)
    result = route(_request(command, panel_df))

    expected_capability = {
        "ivregress": "iv_estimation",
        "test": "wald_test",
        "predict": "prediction",
        "winsor2": "data_transform",
    }[command.split()[0]]
    assert seen and seen[-1] == (expected_capability, command.split()[0], True)
    assert result.status != "unsupported"


@pytest.mark.parametrize(
    ("command", "invalid_name", "role"),
    [
        (
            "ivregress 2sls leverage profitability (tangibility = nonexistent_col)",
            "nonexistent_col",
            "instrument",
        ),
        ("winsor2 nonexistent_col, cuts(1 99)", "nonexistent_col", "variable"),
    ],
)
def test_other_user_supplied_variables_never_default(command, invalid_name, role, panel_df):
    result = execute_stata_command(command, panel_df, {})

    assert result["status"] == "error"
    assert result["error_code"] == "VARIABLE_NOT_FOUND"
    assert result["metadata"]["invalid_argument"] == invalid_name
    assert result["metadata"]["argument_role"] == role


def test_regress_covariance_semantics_and_cluster_reference(panel_df):
    conventional = execute_stata_command("regress leverage profitability", panel_df, {})
    robust = execute_stata_command("regress leverage profitability, vce(robust)", panel_df, {})
    missing = execute_stata_command(
        "regress leverage profitability, vce(cluster nonexistent_col)", panel_df, {}
    )
    clustered = execute_stata_command(
        "regress leverage profitability, vce(cluster company_code)", panel_df, {}
    )

    assert conventional["covariance_type"] == "nonrobust"
    assert conventional["cluster_variable"] is None
    assert robust["covariance_type"] == "robust"
    assert robust["cluster_variable"] is None
    assert missing["status"] == "error"
    assert missing["error_code"] == "VARIABLE_NOT_FOUND"
    assert missing["metadata"]["invalid_argument"] == "nonexistent_col"
    assert clustered["status"] == "success"
    assert clustered["covariance_type"] == "cluster"
    assert clustered["cluster_variable"] == "company_code"
    assert clustered["cluster_count"] == panel_df["company_code"].nunique()

    clean = panel_df[["leverage", "profitability", "company_code"]].dropna()
    reference = sm.OLS(
        clean["leverage"], sm.add_constant(clean[["profitability"]])
    ).fit(cov_type="cluster", cov_kwds={"groups": clean["company_code"]})
    observed_se = clustered["coefficients"]["profitability"]["se"]
    assert observed_se == pytest.approx(float(reference.bse["profitability"]), abs=1e-10)
    assert robust["coefficients"]["profitability"]["se"] != pytest.approx(observed_se)


def test_xtreg_covariance_semantics_and_cluster_reference(panel_df):
    linearmodels = pytest.importorskip("linearmodels.panel")

    conventional = execute_stata_command("xtreg leverage profitability, fe", panel_df, {})
    robust = execute_stata_command(
        "xtreg leverage profitability, fe vce(robust)", panel_df, {}
    )
    missing = execute_stata_command(
        "xtreg leverage profitability, fe vce(cluster nonexistent_col)", panel_df, {}
    )
    clustered = execute_stata_command(
        "xtreg leverage profitability, fe vce(cluster company_code)", panel_df, {}
    )

    assert conventional["covariance_type"] == "nonrobust"
    assert robust["covariance_type"] == "robust"
    assert missing["status"] == "error"
    assert missing["error_code"] == "VARIABLE_NOT_FOUND"
    assert clustered["status"] == "success"
    assert clustered["covariance_type"] == "cluster"
    assert clustered["cluster_variable"] == "company_code"
    assert clustered["cluster_count"] == panel_df["company_code"].nunique()

    clean = panel_df[["company_code", "year", "leverage", "profitability"]].dropna()
    indexed = clean.set_index(["company_code", "year"])
    reference = linearmodels.PanelOLS(
        indexed["leverage"], indexed[["profitability"]], entity_effects=True
    ).fit(
        cov_type="clustered",
        clusters=pd.DataFrame(
            {"company_code": indexed.index.get_level_values("company_code")},
            index=indexed.index,
        ),
    )
    observed_se = clustered["coefficients"]["profitability"]["se"]
    assert observed_se == pytest.approx(float(reference.std_errors["profitability"]), abs=1e-10)
    assert robust["coefficients"]["profitability"]["se"] != pytest.approx(observed_se)


@pytest.mark.parametrize(
    ("command", "covariance_type", "cluster_variable"),
    [
        ("regress leverage profitability", "nonrobust", None),
        ("regress leverage profitability, vce(robust)", "robust", None),
        ("regress leverage profitability, vce(cluster company_code)", "cluster", "company_code"),
        ("xtreg leverage profitability, fe", "nonrobust", None),
        ("xtreg leverage profitability, fe vce(robust)", "robust", None),
        ("xtreg leverage profitability, fe vce(cluster company_code)", "cluster", "company_code"),
    ],
)
def test_parser_preserves_covariance_contract(command, covariance_type, cluster_variable, panel_df):
    parsed = parse_stata_command(command)
    result = route(_request(command, panel_df))

    assert result.status == "success"
    assert parsed["cmd"] in {"regress", "xtreg"}
    assert result.metadata["covariance_type"] == covariance_type
    assert result.metadata["cluster_variable"] == cluster_variable


@pytest.mark.parametrize("command", [
    "tabstat leverage, by(stage)",
    "regress leverage profitability, vce(cluster firm)",
    "xtreg leverage profitability, fe vce(cluster id)",
])
def test_grouping_and_cluster_roles_do_not_use_analytical_aliases(command, panel_df):
    result = execute_stata_command(command, panel_df, {})
    assert result["status"] == "error"
    assert result["error_code"] == "VARIABLE_NOT_FOUND"
    assert result["metadata"]["stata_rc"] == 111


@pytest.mark.parametrize(
    "command",
    ["graph box leverage, over(stage)", "margins stage"],
)
def test_all_grouping_roles_fail_closed_without_alias_substitution(command, panel_df):
    result = execute_stata_command(command, panel_df, {})
    assert result["status"] == "error"
    assert result["error_code"] == "VARIABLE_NOT_FOUND"
    assert result["metadata"]["stata_rc"] == 111


@pytest.mark.parametrize("command", [
    "graph box leverage, over(life_stage)",
    "margins life_stage",
])
def test_valid_grouping_roles_are_normalized_and_preserved(command, panel_df):
    result = execute_stata_command(command, panel_df, {})
    assert result["status"] == "success"
    if command.startswith("graph"):
        assert result["boxplot_data"]["group"] == "life_stage"
    else:
        assert result["margins_data"]["group"] == "life_stage"


def test_post_estimation_test_unknown_variable_has_typed_error(panel_df):
    result = execute_stata_command("test nonexistent_col = 0", panel_df, {})
    assert result["status"] == "error"
    assert result["error_code"] == "VARIABLE_NOT_FOUND"
    assert result["metadata"]["argument_role"] == "test_variable"


def test_router_preserves_explicit_session_context_for_post_estimation(panel_df):
    from models.stata_engine import ModelResultContext

    context_a = ModelResultContext()
    context_b = ModelResultContext()
    fit_request = dataclasses.replace(
        _request("xtreg leverage profitability, fe", panel_df),
        session_context=context_a, session_id="a",
    )
    fitted = route(fit_request)
    assert fitted.status in {"success", "partial"}
    same_session = dataclasses.replace(
        _request("test profitability = 0", panel_df),
        session_context=context_a, session_id="a",
    )
    isolated = dataclasses.replace(
        _request("test profitability = 0", panel_df),
        session_context=context_b, session_id="b",
    )
    same_result = route(same_session)
    isolated_result = route(isolated)
    assert same_result.status == "success"
    assert isolated_result.status == "error"
    assert isolated_result.error_code == "NO_ACTIVE_ESTIMATION"


@pytest.mark.parametrize(
    "command",
    [
        "scenario leverage tax=-0.05",
        "scenario leverage, interventions(tax=-0.05)",
    ],
)
def test_scenario_parser_to_adapter_contract(command, panel_df):
    parsed = parse_stata_command(command)
    result = execute_stata_command(command, panel_df, {})

    assert parsed["depvar"] == "leverage"
    assert parsed["options"]["interventions"] == {"tax": -0.05}
    assert result["status"] == "partial"
    assert result["metadata"]["interventions"] == {"tax": -0.05}
    assert "INTERVENTION PREVIEW" in result["ascii_output"]


@pytest.mark.parametrize(
    "command",
    [
        "scenario leverage tax=not-a-number",
        "scenario leverage, interventions(tax)",
        "scenario leverage, interventions(tax=-0.05 broken)",
    ],
)
def test_malformed_scenario_syntax_fails_closed(command, panel_df):
    result = execute_stata_command(command, panel_df, {})

    assert result["status"] in {"error", "unsupported"}
    assert result["error_code"] in {"SYNTAX_ERROR", "UNSUPPORTED_OPTION"}
    assert result["metadata"]["stata_rc"] == 198
    assert "r(198)" in result["ascii_output"]


def test_unknown_scenario_intervention_fails_before_adapter(panel_df):
    result = execute_stata_command(
        "scenario leverage nonexistent_col=-0.05", panel_df, {}
    )

    assert result["status"] == "error"
    assert result["error_code"] == "VARIABLE_NOT_FOUND"
    assert result["metadata"]["invalid_argument"] == "nonexistent_col"
    assert "r(111)" in result["ascii_output"]


def test_hdfe_absorb_parser_to_estimator_contract(panel_df):
    command = "hdfe leverage profitability, absorb(company_code year)"
    parsed = parse_stata_command(command)
    result = execute_stata_command(command, panel_df, {})

    assert parsed["options"]["absorb"] == ["company_code", "year"]
    assert result["status"] == "partial"
    assert result["metadata"]["absorbed_variables"] == ["company_code", "year"]
    assert "company_code + year" in result["ascii_output"]


def test_hdfe_unknown_absorb_variable_fails_before_estimation(panel_df):
    result = execute_stata_command(
        "hdfe leverage profitability, absorb(company_code nonexistent_col)",
        panel_df,
        {},
    )

    assert result["status"] == "error"
    assert result["error_code"] == "VARIABLE_NOT_FOUND"
    assert result["metadata"]["argument_role"] == "absorb"
    assert result["metadata"]["invalid_argument"] == "nonexistent_col"


def test_legacy_gmm_proxy_has_no_system_gmm_or_arellano_bond_claims():
    econometric_source = Path("models/econometric.py").read_text(encoding="utf-8")
    page_source = Path("pages/13_advanced_econometrics.py").read_text(encoding="utf-8")

    forbidden = [
        '"type": "System GMM"',
        "Arellano-Bond AR(1)",
        "Arellano-Bond AR(2)",
        "estimated via System GMM",
        "Blundell & Bond (1998) System GMM",
        "overidentifying moment restrictions are valid",
    ]
    combined = econometric_source + page_source
    for claim in forbidden:
        assert claim not in combined

    assert "Experimental IV-GMM proxy" in combined
    assert "IV-GMM proxy" in combined


def test_user_facing_tracked_surfaces_have_no_unsupported_method_claims():
    import subprocess

    paths = subprocess.check_output(
        ["git", "ls-files", "--", "docs", "models", "pages"], text=True
    ).splitlines()
    historical = ("docs/implementation-reports/", "docs/generate_section_e.js")
    forbidden = (
        "TWO-STEP SYSTEM GMM",
        "Dynamic Panel System GMM",
        "Arellano-Bond AR(1)",
        "Arellano-Bond AR(2)",
        "Instruments are Valid",
    )
    violations = []
    for path in paths:
        if path.startswith(historical):
            continue
        text = Path(path).read_text(encoding="utf-8", errors="ignore")
        for claim in forbidden:
            if claim.lower() in text.lower():
                violations.append(f"{path}: {claim}")
    assert not violations, "unsupported user-facing claims: " + "; ".join(violations)


def test_ws1_availability_is_separate_from_master_merge_and_validation_docs():
    status = Path("CURRENT_STATUS.md").read_text(encoding="utf-8")
    report = Path(
        "docs/implementation-reports/WAVE_5_PR_02_WS1_RECONCILIATION_REPORT.md"
    ).read_text(encoding="utf-8")
    contracts = Path("docs/WAVE5_COMMAND_CONTRACTS.md").read_text(encoding="utf-8")
    combined = (status + report + contracts).lower()

    assert "implemented on the reconciliation lineage" in combined
    assert "not yet available on `master`" in combined
    assert "pending independent approval" in combined
    assert "implementation availability" in combined
    assert "methodological validation" in combined
    assert "never silently dropped, replaced, or" in combined
    assert 'options["interventions"] == {"tax": -0.05}' in combined
    assert 'options["absorb"] == ["company_code", "year"]' in combined


def test_stata_studio_validation_errors_suppress_success_interpretation():
    source = Path("pages/23_stata_studio.py").read_text(encoding="utf-8")

    assert 'is_failed_command = last_res.get("status") in ("error", "unsupported")' in source
    assert "if not is_failed_command:" in source
    assert "Stata Validation Error — estimation was not run" in source
    assert "Invalid {argument_role or 'argument'}" in source
