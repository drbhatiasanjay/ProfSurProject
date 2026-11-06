"""Candidate identity, time gaps and closed promotion gates, not parity claims."""
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from models.dynamic_panel_candidate import panel_inventory, run_candidate


def generated_panel():
    rng = np.random.default_rng(21)
    rows = []
    for firm in range(60):
        y, effect = rng.normal(), rng.normal(scale=.5)
        for year in range(2000, 2012):
            x = rng.normal()
            y = .6 * y + .3 * x + effect + rng.normal(scale=.5)
            rows.append((firm, year, y, x))
    return pd.DataFrame(rows, columns=["company_code", "year", "leverage", "profitability"])


def test_inventory_counts_observations_and_firms_separately():
    frame = generated_panel()
    result = panel_inventory(frame)
    assert result["observations"] == 720
    assert result["unique_firms"] == 60
    assert result["dataset_fingerprint"] == panel_inventory(frame.sample(frac=1, random_state=1))["dataset_fingerprint"]


def test_specification_injection_and_duplicate_keys_rejected():
    frame = generated_panel()
    assert run_candidate(frame, dependent="leverage | gmm(x)")["error_code"] == "INVALID_SPECIFICATION"
    assert run_candidate(pd.concat([frame, frame.iloc[:1]]), regressors=("profitability",))["error_code"] == "INVALID_PANEL"


def test_insufficient_panel_and_infinite_inputs_rejected():
    frame = generated_panel()
    assert run_candidate(frame.head(40), regressors=("profitability",))["error_code"] == "INSUFFICIENT_PANEL"
    frame.loc[0, "leverage"] = np.inf
    assert run_candidate(frame, regressors=("profitability",))["error_code"] == "NONFINITE_DATA"


def test_missing_optional_dependency_has_typed_response(monkeypatch):
    import models.dynamic_panel_candidate as module
    def unavailable(_):
        raise ImportError("not installed")
    monkeypatch.setattr(module, "version", unavailable)
    result = run_candidate(generated_panel(), regressors=("profitability",))
    assert result["error_code"] == "OPTIONAL_DEPENDENCY_MISSING"
    assert result["validation_status"] == "NOT_VALIDATED"


@pytest.mark.parametrize("gap", [False, True])
def test_actual_candidate_executes_without_promoting_parity(gap):
    local = Path(__file__).resolve().parents[1] / "scratch/covenant_pilot/deps"
    if local.exists():
        monkey = pytest.MonkeyPatch()
        monkey.syspath_prepend(str(local))
    else:
        monkey = None
    try:
        pytest.importorskip("pydynpd")
        frame = generated_panel()
        if gap:
            # Individual missing years remain gaps in the annual padded grid.
            frame = frame[~((frame.year == 2005) & (frame.company_code % 3 == 0))]
        original = frame.copy(deep=True)
        result = run_candidate(frame, regressors=("profitability",), code_revision="test")
        assert result["status"] == "success", result
        assert result["validation_status"] == "NOT_VALIDATED"
        assert result["validation_record"]["numerical_status"] == "NOT_RUN"
        assert result["padded_grid_rows"] == 720
        assert result["diagnostics"]["instrument_count"] > 0
        assert "L1.leverage" in result["coefficients"]
        assert all(v >= 0 for v in result["standard_errors"].values())
        pd.testing.assert_frame_equal(frame, original)
        assert result["sample_fingerprint"] == run_candidate(frame, regressors=("profitability",))["sample_fingerprint"]
    finally:
        if monkey:
            monkey.undo()


def test_global_period_gap_never_becomes_adjacent_lag():
    frame = generated_panel()
    result = run_candidate(frame[frame.year != 2005], regressors=("profitability",))
    assert result["error_code"] == "GLOBAL_PERIOD_GAP"
    assert result["validation_status"] == "NOT_VALIDATED"
