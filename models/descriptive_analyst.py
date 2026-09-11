"""Deterministic, provider-neutral descriptive analysis contract for Phase 13."""
from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from typing import Any

import pandas as pd

class DescriptiveAnalysisError(ValueError):
    """Typed fail-closed error for invalid descriptive requests."""


_STAT_KEYS = ("count", "mean", "std", "min", "25%", "50%", "75%", "max")
_FIRM_COLUMNS = ("company_code", "firm", "firm_id", "company")


@dataclass(frozen=True)
class AnalysisRun:
    """Small provider-neutral envelope for deterministic descriptive results."""

    run_id: str
    capability_id: str
    status: str
    parameters: dict[str, Any]
    dataset_fingerprint: str
    result: dict[str, Any]
    provenance: dict[str, Any]

    def to_json(self) -> str:
        return json.dumps(asdict(self), sort_keys=True, default=str)


def _fingerprint(frame: pd.DataFrame) -> str:
    schema = json.dumps(
        [(str(column), str(dtype)) for column, dtype in zip(frame.columns, frame.dtypes)],
        separators=(",", ":"),
    ).encode()
    values = pd.util.hash_pandas_object(frame.reset_index(drop=True), index=True).values.tobytes()
    return hashlib.sha256(schema + values).hexdigest()


def _clean_number(value: Any) -> int | float | None:
    if pd.isna(value):
        return None
    number = float(value)
    return int(number) if number.is_integer() else number


def describe_panel(
    frame: pd.DataFrame,
    *,
    variables: list[str],
    group_by: str | None = None,
    run_id: str,
    panel_mode: str = "unknown",
    year_range: tuple[int | None, int | None] = (None, None),
    filters: dict[str, Any] | None = None,
) -> AnalysisRun:
    """Return deterministic descriptive statistics in the canonical AnalysisRun envelope."""
    if frame.empty:
        raise DescriptiveAnalysisError("EMPTY_SAMPLE: no observations remain after filtering")
    requested = list(dict.fromkeys(variables))
    if not requested:
        raise DescriptiveAnalysisError("VARIABLE_NOT_FOUND: at least one variable is required")
    missing = [column for column in requested if column not in frame.columns]
    if missing:
        raise DescriptiveAnalysisError(f"VARIABLE_NOT_FOUND: {', '.join(missing)}")
    if group_by and group_by not in frame.columns:
        raise DescriptiveAnalysisError(f"GROUP_NOT_FOUND: {group_by}")
    non_numeric = [column for column in requested if not pd.api.types.is_numeric_dtype(frame[column])]
    if non_numeric:
        raise DescriptiveAnalysisError(f"NON_NUMERIC_VARIABLE: {', '.join(non_numeric)}")

    groups: dict[str, dict[str, dict[str, int | float | None]]] = {}
    grouped = [("all", frame)] if not group_by else frame.groupby(group_by, dropna=False, sort=True)
    for key, subset in grouped:
        stats: dict[str, dict[str, int | float | None]] = {}
        for column in requested:
            summary = subset[column].describe()
            stats[column] = {name: _clean_number(summary.get(name)) for name in _STAT_KEYS}
        groups[str(key)] = stats

    firm_column = next((column for column in _FIRM_COLUMNS if column in frame.columns), None)
    provenance = {
        "panel_mode": panel_mode,
        "year_range": list(year_range),
        "n_obs": int(len(frame)),
        "n_firms": int(frame[firm_column].nunique()) if firm_column else None,
        "firm_column": firm_column,
        "variables": requested,
        "group_by": group_by,
        "source_fingerprint": _fingerprint(frame),
        "filters": dict(filters or {}),
        "grounding": "COMPUTED",
    }
    return AnalysisRun(
        run_id=run_id,
        capability_id="descriptive_summary",
        status="completed",
        parameters={"variables": requested, "group_by": group_by},
        dataset_fingerprint=provenance["source_fingerprint"],
        result={"groups": groups},
        provenance=provenance,
    )
