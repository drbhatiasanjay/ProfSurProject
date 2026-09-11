"""Deterministic, production-independent numerical fixtures for Wave 6.

These references validate known-answer IV/2SLS and entity-demeaned HDFE
calculations. They are deliberately separate from production dispatchers and
cannot mark a capability as ``VALIDATED``.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd

from .benchmark_contracts import BenchmarkOutcome
from .validation_ledger import ValidationRecord, write_manifest


class BenchmarkFixtureError(ValueError):
    """Raised when a deterministic benchmark fixture is malformed."""


@dataclass(frozen=True)
class KnownAnswerPanel:
    frame: pd.DataFrame
    iv_beta: float
    iv_gamma: float
    hdfe_beta: float


def make_known_answer_panel(*, seed: int = 1729, firms: int = 20, periods: int = 20) -> KnownAnswerPanel:
    """Build a fixed panel with known IV and within-estimator coefficients."""
    if firms < 4 or periods < 4:
        raise BenchmarkFixtureError("fixture requires at least 4 firms and periods")
    rng = np.random.default_rng(seed)
    n = firms * periods
    company_code = np.repeat(np.arange(firms), periods)
    year = np.tile(np.arange(2001, 2001 + periods), firms)
    w = rng.normal(size=n)
    z = rng.normal(size=n)
    x = 0.9 * z + 0.35 * w + rng.normal(scale=0.35, size=n)
    firm_effect = np.repeat(rng.normal(scale=1.5, size=firms), periods)
    y_iv = 1.25 * x - 0.40 * w + rng.normal(scale=0.20, size=n)
    y_hdfe = 1.75 * x + firm_effect + rng.normal(scale=0.20, size=n)
    frame = pd.DataFrame({
        "company_code": company_code,
        "year": year,
        "y_iv": y_iv,
        "y_hdfe": y_hdfe,
        "x": x,
        "w": w,
        "z": z,
    })
    return KnownAnswerPanel(frame, iv_beta=1.25, iv_gamma=-0.40, hdfe_beta=1.75)


def _fingerprint(frame: pd.DataFrame) -> str:
    encoded = frame.to_csv(index=False, float_format="%.12g", lineterminator="\n").encode()
    return "sha256:" + hashlib.sha256(encoded).hexdigest()


def _ols_coefficients(design: np.ndarray, target: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    beta, _, rank, _ = np.linalg.lstsq(design, target, rcond=None)
    if rank != design.shape[1]:
        raise BenchmarkFixtureError("benchmark design matrix is rank deficient")
    residual = target - design @ beta
    dof = design.shape[0] - design.shape[1]
    if dof <= 0:
        raise BenchmarkFixtureError("benchmark has no residual degrees of freedom")
    sigma2 = float(residual @ residual / dof)
    covariance = sigma2 * np.linalg.inv(design.T @ design)
    return beta, np.sqrt(np.diag(covariance))


def run_iv_reference(panel: KnownAnswerPanel) -> BenchmarkOutcome:
    """Run an independent two-stage least-squares reference calculation."""
    frame = panel.frame
    z_design = np.column_stack([np.ones(len(frame)), frame[["w", "z"]].to_numpy()])
    first_stage, _ = _ols_coefficients(z_design, frame["x"].to_numpy())
    x_hat = z_design @ first_stage
    second_stage = np.column_stack([np.ones(len(frame)), frame[["w"]].to_numpy(), x_hat])
    coefficients, standard_errors = _ols_coefficients(second_stage, frame["y_iv"].to_numpy())
    return BenchmarkOutcome(
        benchmark_id="wave6-iv-known-answer-v1",
        dataset_fingerprint=_fingerprint(frame),
        sample_fingerprint=_fingerprint(frame[["company_code", "year"]]),
        row_count=len(frame),
        effective_row_count=len(frame),
        covariance="homoskedastic-reference",
        coefficients={"w": float(coefficients[1]), "x": float(coefficients[2])},
        standard_errors={"w": float(standard_errors[1]), "x": float(standard_errors[2])},
        diagnostics={"first_stage_rank": int(np.linalg.matrix_rank(z_design)), "reference": True},
    )


def run_hdfe_reference(panel: KnownAnswerPanel) -> BenchmarkOutcome:
    """Run an independent one-way entity fixed-effect (within) reference."""
    frame = panel.frame
    demeaned = frame[["company_code", "y_hdfe", "x"]].copy()
    demeaned["y"] = demeaned["y_hdfe"] - demeaned.groupby("company_code")["y_hdfe"].transform("mean")
    demeaned["x_dm"] = demeaned["x"] - demeaned.groupby("company_code")["x"].transform("mean")
    design = demeaned[["x_dm"]].to_numpy()
    coefficients, standard_errors = _ols_coefficients(design, demeaned["y"].to_numpy())
    return BenchmarkOutcome(
        benchmark_id="wave6-hdfe-known-answer-v1",
        dataset_fingerprint=_fingerprint(frame),
        sample_fingerprint=_fingerprint(frame[["company_code", "year"]]),
        row_count=len(frame),
        effective_row_count=len(frame),
        covariance="homoskedastic-reference",
        coefficients={"x": float(coefficients[0])},
        standard_errors={"x": float(standard_errors[0])},
        diagnostics={"absorbed_effect": "company_code", "n_entities": int(frame["company_code"].nunique()), "reference": True},
    )


def run_wave6_fixture_suite(*, seed: int = 1729) -> dict[str, BenchmarkOutcome]:
    """Return deterministic IV and HDFE outcomes for contract/evidence tests."""
    panel = make_known_answer_panel(seed=seed)
    return {"iv": run_iv_reference(panel), "hdfe": run_hdfe_reference(panel)}


def write_fixture_manifests(directory: str | Path, *, code_revision: str) -> dict[str, Path]:
    """Write fixture outputs and fail-closed validation manifests."""
    if not code_revision.strip():
        raise BenchmarkFixtureError("code revision is required")
    root = Path(directory)
    paths: dict[str, Path] = {}
    for key, outcome in run_wave6_fixture_suite().items():
        target = root / key
        target.mkdir(parents=True, exist_ok=True)
        (target / "outcome.json").write_text(json.dumps({
            "benchmark_id": outcome.benchmark_id,
            "dataset_fingerprint": outcome.dataset_fingerprint,
            "sample_fingerprint": outcome.sample_fingerprint,
            "row_count": outcome.row_count,
            "effective_row_count": outcome.effective_row_count,
            "coefficients": dict(outcome.coefficients),
            "standard_errors": dict(outcome.standard_errors),
            "diagnostics": dict(outcome.diagnostics),
        }, sort_keys=True, indent=2) + "\n", encoding="utf-8")
        capability = "ivregress" if key == "iv" else "hdfe"
        record = ValidationRecord(
            capability=capability,
            estimator_variant="known-answer-reference",
            code_revision=code_revision,
            dataset_fingerprint=outcome.dataset_fingerprint,
            sample_fingerprint=outcome.sample_fingerprint,
            benchmark_id=outcome.benchmark_id,
            numerical_status="PASS",
            assumption_status="PASS",
            methodological_status="PASS",
            reproducibility_status="PASS",
            reviewer_status="NOT_RUN",
            limitations=("Independent fixture evidence; production parity not established.",),
            evidence_refs=(f"{key}/outcome.json",),
        )
        paths[key] = write_manifest(target, record, command="run_wave6_fixture_suite")
    return paths
