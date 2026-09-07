"""Public behavior tests for the canonical analytical run envelope."""

import json

import pytest

from models.decision_contracts import AnalysisRun


def test_completed_run_serializes_deterministically():
    run = AnalysisRun(
        run_id="run-001",
        capability_id="stata.xtreg.fe",
        status="completed",
        parameters={"depvar": "leverage", "indepvars": ["prof"]},
        dataset_fingerprint="sha256:panel-001",
        result={"n_obs": 8673, "r2": 0.0339},
        provenance={"engine": "stata", "version": "18-compatible"},
    )

    first = run.to_json()
    second = AnalysisRun.from_dict(json.loads(first)).to_json()

    assert first == second
    assert json.loads(first)["status"] == "completed"
    assert json.loads(first)["capability_id"] == "stata.xtreg.fe"


@pytest.mark.parametrize(
    "overrides",
    [{"run_id": ""}, {"capability_id": ""}, {"status": "unknown"}],
)
def test_run_rejects_invalid_identity_or_status(overrides):
    payload = {
        "run_id": "run-002",
        "capability_id": "stata.summarize",
        "status": "failed",
    }
    payload.update(overrides)

    with pytest.raises(ValueError):
        AnalysisRun(**payload)
