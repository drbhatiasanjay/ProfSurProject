"""Session-scoped, serializable identity for analytical model results."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Any

import pandas as pd


def fingerprint_frame(frame: pd.DataFrame) -> str:
    """Return a deterministic fingerprint for schema, values, and row identity."""
    schema = json.dumps(
        [(str(column), str(dtype)) for column, dtype in zip(frame.columns, frame.dtypes)],
        separators=(",", ":"),
    ).encode("utf-8")
    values = pd.util.hash_pandas_object(frame, index=True).values.tobytes()
    return hashlib.sha256(schema + values).hexdigest()


@dataclass(frozen=True)
class ModelResultContext:
    model_id: str
    command: str
    estimator: str
    dependent_variable: str
    regressors: tuple[str, ...]
    dataset_fingerprint: str
    sample_fingerprint: str
    estimation_index: tuple[Any, ...]
    parameters: tuple[tuple[str, float], ...]
    covariance: tuple[tuple[float, ...], ...]

    @classmethod
    def from_frame(
        cls,
        *,
        model_id: str,
        command: str,
        estimator: str,
        frame: pd.DataFrame,
        dependent_variable: str,
        regressors: tuple[str, ...],
        parameters: dict[str, float],
        covariance: list[list[float]],
    ) -> "ModelResultContext":
        if not model_id.strip():
            raise ValueError("model_id is required")
        if dependent_variable not in frame.columns:
            raise ValueError(f"unknown dependent variable: {dependent_variable}")
        return cls(
            model_id=model_id,
            command=command,
            estimator=estimator,
            dependent_variable=dependent_variable,
            regressors=tuple(regressors),
            dataset_fingerprint=fingerprint_frame(frame),
            sample_fingerprint=fingerprint_frame(frame),
            estimation_index=tuple(frame.index.tolist()),
            parameters=tuple((name, float(value)) for name, value in parameters.items()),
            covariance=tuple(tuple(float(value) for value in row) for row in covariance),
        )

    @property
    def n_obs(self) -> int:
        return len(self.estimation_index)

    def public_dict(self) -> dict[str, Any]:
        """Return a JSON-safe projection; runtime estimator objects are excluded."""
        return {
            "model_id": self.model_id,
            "command": self.command,
            "estimator": self.estimator,
            "dependent_variable": self.dependent_variable,
            "regressors": list(self.regressors),
            "dataset_fingerprint": self.dataset_fingerprint,
            "sample_fingerprint": self.sample_fingerprint,
            "n_obs": self.n_obs,
            "parameters": dict(self.parameters),
            "covariance": [list(row) for row in self.covariance],
        }


@dataclass
class AnalysisSession:
    active_model: ModelResultContext | None = None
    stored_models: dict[str, ModelResultContext] | None = None
    runtime_estimates: dict[str, dict] | None = None
    last_estimate: dict | None = None
    panel_context: Any = None

    def __post_init__(self) -> None:
        if self.stored_models is None:
            self.stored_models = {}
        if self.runtime_estimates is None:
            self.runtime_estimates = {}

    def store(self, model: ModelResultContext) -> None:
        assert self.stored_models is not None
        self.stored_models[model.model_id] = model
        self.active_model = model

    def require(self, model_id: str) -> ModelResultContext:
        assert self.stored_models is not None
        try:
            return self.stored_models[model_id]
        except KeyError as exc:
            raise KeyError(f"model not found: {model_id}") from exc
