"""Independent benchmark contracts for Wave 6 numerical validation."""

from __future__ import annotations

from dataclasses import dataclass, field
from math import isfinite
from typing import Mapping


class BenchmarkContractError(ValueError):
    """Raised when benchmark evidence cannot be compared safely."""


@dataclass(frozen=True)
class BenchmarkSpec:
    benchmark_id: str
    capability: str
    estimator_variant: str
    covariance: str
    coefficient_tolerance: float = 0.01
    standard_error_tolerance: float = 0.02
    seed: int = 0

    def __post_init__(self) -> None:
        if not all(value.strip() for value in (self.benchmark_id, self.capability, self.estimator_variant, self.covariance)):
            raise BenchmarkContractError("benchmark identity and covariance are required")
        if self.coefficient_tolerance < 0 or self.standard_error_tolerance < 0:
            raise BenchmarkContractError("tolerances must be non-negative")


@dataclass(frozen=True)
class BenchmarkOutcome:
    benchmark_id: str
    dataset_fingerprint: str
    sample_fingerprint: str
    row_count: int
    effective_row_count: int
    dropped_row_reasons: Mapping[str, int] = field(default_factory=dict)
    covariance: str = ""
    coefficients: Mapping[str, float] = field(default_factory=dict)
    standard_errors: Mapping[str, float] = field(default_factory=dict)
    diagnostics: Mapping[str, float | str | bool] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.benchmark_id.strip() or not self.dataset_fingerprint.strip() or not self.sample_fingerprint.strip():
            raise BenchmarkContractError("benchmark and fingerprints are required")
        if self.row_count < 0 or self.effective_row_count < 0 or self.effective_row_count > self.row_count:
            raise BenchmarkContractError("effective sample must be within source sample")
        if any(count < 0 for count in self.dropped_row_reasons.values()):
            raise BenchmarkContractError("dropped-row counts cannot be negative")
        if set(self.coefficients) != set(self.standard_errors):
            raise BenchmarkContractError("coefficient and standard-error names must match")
        if any(not isfinite(float(value)) for value in (*self.coefficients.values(), *self.standard_errors.values())):
            raise BenchmarkContractError("coefficients and standard errors must be finite")


def compare_coefficients(
    spec: BenchmarkSpec,
    outcome: BenchmarkOutcome,
    *,
    reference_coefficients: Mapping[str, float],
    reference_standard_errors: Mapping[str, float],
) -> dict[str, float | str]:
    """Compare production output with an independently generated reference."""
    if outcome.benchmark_id != spec.benchmark_id:
        raise BenchmarkContractError("benchmark identity mismatch")
    if outcome.covariance != spec.covariance:
        raise BenchmarkContractError("covariance specification mismatch")
    if set(outcome.coefficients) != set(reference_coefficients) or set(outcome.standard_errors) != set(reference_standard_errors):
        raise BenchmarkContractError("coefficient names must match reference")
    coefficient_deltas = [abs(float(outcome.coefficients[name]) - float(reference_coefficients[name])) for name in outcome.coefficients]
    se_deltas = [abs(float(outcome.standard_errors[name]) - float(reference_standard_errors[name])) for name in outcome.standard_errors]
    max_coef = max(coefficient_deltas, default=0.0)
    max_se = max(se_deltas, default=0.0)
    return {
        "status": "PASS" if max_coef <= spec.coefficient_tolerance and max_se <= spec.standard_error_tolerance else "FAIL",
        "max_coefficient_delta": max_coef,
        "max_standard_error_delta": max_se,
    }
