import pytest

from models.benchmark_contracts import (
    BenchmarkContractError,
    BenchmarkSpec,
    BenchmarkOutcome,
    compare_coefficients,
)


def _spec(**overrides):
    values = {
        "benchmark_id": "iv-known-answer-v1",
        "capability": "ivregress",
        "estimator_variant": "2sls",
        "covariance": "robust",
        "coefficient_tolerance": 0.01,
        "standard_error_tolerance": 0.02,
        "seed": 42,
    }
    values.update(overrides)
    return BenchmarkSpec(**values)


def _outcome(**overrides):
    values = {
        "benchmark_id": "iv-known-answer-v1",
        "dataset_fingerprint": "sha256:source",
        "sample_fingerprint": "sha256:sample",
        "row_count": 100,
        "effective_row_count": 96,
        "dropped_row_reasons": {"missing_lag": 4},
        "covariance": "robust",
        "coefficients": {"x": 1.0},
        "standard_errors": {"x": 0.2},
        "diagnostics": {"first_stage_f": 18.0},
    }
    values.update(overrides)
    return BenchmarkOutcome(**values)


def test_comparison_passes_within_independent_tolerances():
    result = compare_coefficients(
        _spec(), _outcome(),
        reference_coefficients={"x": 1.005},
        reference_standard_errors={"x": 0.215},
    )
    assert result["status"] == "PASS"
    assert result["max_coefficient_delta"] == pytest.approx(0.005)


def test_comparison_fails_on_missing_or_out_of_tolerance_terms():
    with pytest.raises(BenchmarkContractError, match="coefficient names"):
        compare_coefficients(_spec(), _outcome(), reference_coefficients={"z": 1.0}, reference_standard_errors={"x": 0.2})
    result = compare_coefficients(_spec(), _outcome(), reference_coefficients={"x": 1.2}, reference_standard_errors={"x": 0.2})
    assert result["status"] == "FAIL"


def test_outcome_rejects_inconsistent_sample_accounting_or_covariance():
    with pytest.raises(BenchmarkContractError):
        _outcome(effective_row_count=101)
    with pytest.raises(BenchmarkContractError):
        compare_coefficients(_spec(covariance="cluster:firm"), _outcome(), reference_coefficients={"x": 1.0}, reference_standard_errors={"x": 0.2})
