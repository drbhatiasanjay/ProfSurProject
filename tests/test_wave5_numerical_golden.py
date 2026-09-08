"""Deterministic numerical gates for Wave 5 advanced capabilities."""

import uuid

import numpy as np
import pandas as pd
import pytest

from models.analysis_run_envelope import AnalysisRunEnvelope
from models.analytical_contracts import AnalyticalRequest, fingerprint_df


def _request(df, cmd, depvar, indepvars, options=None):
    parsed = {
        "cmd": cmd,
        "command": cmd,
        "depvar": depvar,
        "indepvars": indepvars,
        "options": options or {},
        "raw": f"{cmd} {depvar} {' '.join(indepvars)}",
    }
    ref = fingerprint_df(df)
    request = AnalyticalRequest(
        command_str=parsed["raw"],
        parsed=parsed,
        df=df,
        correlation_id=str(uuid.uuid4()),
        dataset_ref=ref,
        session_id="wave5_golden",
    )
    envelope = AnalysisRunEnvelope.create(
        run_id=str(uuid.uuid4()),
        correlation_id=request.correlation_id,
        dataset_fingerprint=ref.fingerprint,
        normalized_command=request.command_str,
        capability=cmd,
    )
    return request, envelope


def test_iv_2sls_matches_closed_form_reference_but_remains_partial():
    pytest.importorskip("linearmodels.iv")
    from models.causal_adapters import IVAdapter

    rng = np.random.default_rng(20260908)
    n_obs = 600
    instrument = rng.normal(size=n_obs)
    control = rng.normal(size=n_obs)
    structural_error = rng.normal(scale=0.4, size=n_obs)
    endogenous = 0.9 * instrument + 0.35 * structural_error + rng.normal(scale=0.5, size=n_obs)
    outcome = 1.25 + 0.6 * control + 1.8 * endogenous + structural_error
    df = pd.DataFrame({
        "outcome": outcome,
        "control": control,
        "endogenous": endogenous,
        "instrument": instrument,
    })
    request, envelope = _request(
        df,
        "iv_candidate",
        "outcome",
        ["control"],
        {"endog": ["endogenous"], "instruments": ["instrument"]},
    )

    result = IVAdapter.run(request, envelope)

    instruments = np.column_stack([np.ones(n_obs), control, instrument])
    regressors = np.column_stack([np.ones(n_obs), control, endogenous])
    projected_cross = regressors.T @ instruments @ np.linalg.solve(
        instruments.T @ instruments,
        instruments.T @ regressors,
    )
    projected_outcome = regressors.T @ instruments @ np.linalg.solve(
        instruments.T @ instruments,
        instruments.T @ outcome,
    )
    reference = np.linalg.solve(projected_cross, projected_outcome)
    observed = {row["Variable"]: row["Coefficient"] for row in result.table or []}

    assert result.status == "partial"
    assert "IMPLEMENTED_UNVERIFIED" in result.message
    np.testing.assert_allclose(
        [observed["const"], observed["control"], observed["endogenous"]],
        reference,
        rtol=0,
        atol=1e-5,
    )


def test_hdfe_matches_two_way_fixed_effects_fixture_but_remains_partial():
    pytest.importorskip("pyfixest")
    from models.causal_adapters import HDFEAdapter

    firms = np.repeat(np.arange(20), 6)
    years = np.tile(np.arange(2015, 2021), 20)
    predictor = np.sin(firms * 0.7 + years * 0.11)
    firm_effect = (firms % 5) * 0.4
    year_effect = (years - years.min()) * -0.2
    outcome = 1.75 * predictor + firm_effect + year_effect
    df = pd.DataFrame({
        "company_code": firms,
        "year": years,
        "outcome": outcome,
        "profitability": predictor,
    })
    request, envelope = _request(
        df,
        "hdfe",
        "outcome",
        ["profitability"],
        {"absorb": ["company_code", "year"]},
    )

    result = HDFEAdapter.run(request, envelope)
    observed = {row["Variable"]: row["Coefficient"] for row in result.table or []}

    assert result.status == "partial"
    assert "IMPLEMENTED_UNVERIFIED" in result.message
    assert observed["profitability"] == pytest.approx(1.75, abs=1e-6)


def test_ml_ridge_matches_closed_form_group_holdout_but_remains_partial():
    pytest.importorskip("sklearn")
    from sklearn.model_selection import GroupShuffleSplit
    from models.ml_adapters import MLPredictAdapter

    firms = np.repeat(np.arange(30), 4)
    years = np.tile(np.arange(2018, 2022), 30)
    profitability = np.cos(firms * 0.31 + years * 0.07)
    tangibility = np.sin(firms * 0.17 - years * 0.05)
    outcome = 0.4 + 1.2 * profitability - 0.7 * tangibility + firms * 0.002
    df = pd.DataFrame({
        "company_code": firms,
        "year": years,
        "leverage": outcome,
        "profitability": profitability,
        "tangibility": tangibility,
    })
    request, envelope = _request(
        df,
        "predict_ml",
        "leverage",
        ["profitability", "tangibility"],
    )

    result = MLPredictAdapter.run(request, envelope)

    features = df[["profitability", "tangibility"]].to_numpy()
    target = df["leverage"].to_numpy()
    splitter = GroupShuffleSplit(n_splits=1, test_size=0.2, random_state=42)
    train_idx, test_idx = next(splitter.split(features, target, firms))
    assert set(firms[train_idx]).isdisjoint(set(firms[test_idx]))
    train_x = features[train_idx]
    train_y = target[train_idx]
    centered_x = train_x - train_x.mean(axis=0)
    centered_y = train_y - train_y.mean()
    reference = np.linalg.solve(
        centered_x.T @ centered_x + np.eye(centered_x.shape[1]),
        centered_x.T @ centered_y,
    )
    observed = {row["Feature"]: row["Ridge Coefficient"] for row in result.table or []}

    assert result.status == "partial"
    assert "IMPLEMENTED_UNVERIFIED" in result.message
    np.testing.assert_allclose(
        [observed["profitability"], observed["tangibility"]],
        reference,
        rtol=0,
        atol=1e-5,
    )


def test_scenario_preview_is_partial_and_does_not_mutate_source_data():
    from models.scenario_capability import ScenarioAdapter

    df = pd.DataFrame({"company_code": [1, 2], "tax": [0.25, 0.30]})
    original = df.copy(deep=True)
    request, envelope = _request(
        df,
        "scenario",
        "",
        [],
        {"interventions": {"tax": -0.05}},
    )

    result = ScenarioAdapter.run(request, envelope)

    assert result.status == "partial"
    assert "not validated counterfactual" in result.message.lower()
    pd.testing.assert_frame_equal(df, original)


def test_advanced_registry_entries_are_not_validated():
    from models.command_registry import COMMAND_REGISTRY

    for command in ("gmm", "hdfe", "didregress", "scenario", "predict_ml"):
        assert COMMAND_REGISTRY[command].status != "VALIDATED"


@pytest.mark.parametrize(
    ("registry_status", "expected_status"),
    [
        ("IMPLEMENTED_UNVERIFIED", "partial"),
        ("CANDIDATE", "unsupported"),
    ],
)
def test_router_demotes_false_success_for_unvalidated_capabilities(
    monkeypatch, registry_status, expected_status
):
    from models import analytical_router
    from models.command_registry import CommandEntry

    df = pd.DataFrame({"company_code": [1], "year": [2020], "leverage": [0.4]})
    request, _ = _request(df, "advanced_test", "leverage", [])
    monkeypatch.setattr(
        analytical_router,
        "resolve_capability",
        lambda command: CommandEntry("advanced_test", registry_status),
    )
    monkeypatch.setattr(
        analytical_router,
        "get_handler",
        lambda capability, cmd="": lambda parsed, data: {
            "status": "success",
            "ascii_output": "unverified output",
        },
    )

    result = analytical_router.route(request)

    assert result.status == expected_status
