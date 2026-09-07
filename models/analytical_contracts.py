"""
models/analytical_contracts.py — Wave 2 typed contracts.

External libraries adapt to these contracts; these contracts must not expose
third-party objects directly. (PRD §4.3 contract-first development)
"""
from __future__ import annotations

import hashlib
import datetime
from dataclasses import dataclass, field, asdict
from typing import Any, Literal

import pandas as pd


# ---------------------------------------------------------------------------
# PRD §7 — 25 canonical error codes + INTERNAL_ERROR
# ---------------------------------------------------------------------------
ANALYTICAL_ERROR_CODES: frozenset[str] = frozenset({
    "SYNTAX_ERROR",
    "UNRECOGNIZED_COMMAND",
    "UNSUPPORTED_OPTION",
    "UNSUPPORTED_CAPABILITY",
    "VARIABLE_NOT_FOUND",
    "AMBIGUOUS_VARIABLE",
    "PANEL_NOT_DECLARED",
    "DUPLICATE_PANEL_KEYS",
    "INVALID_TIME_VARIABLE",
    "INSUFFICIENT_OBSERVATIONS",
    "INSUFFICIENT_VARIATION",
    "COLLINEARITY",
    "SINGULAR_MATRIX",
    "NONCONVERGENCE",
    "PERFECT_SEPARATION",
    "INVALID_INSTRUMENT_SPEC",
    "DIAGNOSTIC_FAILURE",
    "METHOD_NOT_PERMITTED",
    "CAUSAL_GATE_REQUIRED",
    "DATA_SCOPE_ERROR",
    "TENANT_SCOPE_ERROR",
    "DEPENDENCY_UNAVAILABLE",
    "ENGINE_UNAVAILABLE",
    "ENGINE_FAILURE",
    "EXPORT_FAILURE",
    "INTERNAL_ERROR",
})


# ---------------------------------------------------------------------------
# PRD §7 — Typed error (14 schema fields)
# ---------------------------------------------------------------------------
@dataclass
class AnalyticalError(Exception):
    """Typed error envelope matching PRD §7 error object schema (14 fields)."""

    code: str                                      # one of ANALYTICAL_ERROR_CODES
    user_message: str                              # plain-English: what / why / what to do
    technical_message: str = ""
    command: str = ""
    normalized_command: str = ""
    correlation_id: str = ""
    analysis_run_id: str = ""
    workspace_id: str = ""
    engine: str = "stata_engine_v1"
    engine_version: str = "1.0"
    severity: Literal["ERROR", "WARNING", "INFO"] = "ERROR"
    recoverable: bool = False
    suggested_actions: tuple[str, ...] = ()
    cause_chain: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        # Auto-stamp timestamp on first creation; stored as ISO-8601 string
        if not hasattr(self, "_timestamp"):
            object.__setattr__(self, "_timestamp",
                               datetime.datetime.utcnow().isoformat() + "Z")
        # Validate code
        if self.code not in ANALYTICAL_ERROR_CODES:
            raise ValueError(
                f"Invalid error code {self.code!r}. "
                f"Must be one of ANALYTICAL_ERROR_CODES."
            )

    @property
    def timestamp(self) -> str:
        return getattr(self, "_timestamp", "")


# ---------------------------------------------------------------------------
# Minimal VisualizationSpec (PRD adversarial review H-07)
# ---------------------------------------------------------------------------
@dataclass
class VisualizationSpec:
    """Typed chart envelope — engine-specific payload wrapped in semantic metadata."""

    chart_type: str           # "scatter" | "bar" | "line" | "coefplot" | "histogram" | ...
    data: dict                # plotly / matplotlib payload (engine-specific for Wave 2)
    intent: str = ""          # "diagnostic" | "descriptive" | "lifecycle" | "causal"
    provenance_run_id: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "chart_type": self.chart_type,
            "data": self.data,
            "intent": self.intent,
            "provenance_run_id": self.provenance_run_id,
        }


# ---------------------------------------------------------------------------
# DatasetSnapshotRef — lightweight fingerprint (PRD adversarial review H-03)
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class DatasetSnapshotRef:
    """Deterministic, lightweight fingerprint of a DataFrame — does NOT serialize data."""

    fingerprint: str          # sha256 hex of shape + sorted column names + row sample
    row_count: int
    col_count: int
    columns: tuple[str, ...]


def fingerprint_df(df: pd.DataFrame) -> DatasetSnapshotRef:
    """Compute a deterministic DatasetSnapshotRef without serializing the full DataFrame."""
    cols_sorted = tuple(sorted(df.columns.tolist()))
    # Sample up to 100 rows for speed; use first+last to catch edge cases
    sample_size = min(100, len(df))
    row_sample = df.iloc[:sample_size].to_csv(index=False).encode("utf-8")
    payload = (
        f"{df.shape[0]}:{df.shape[1]}:"
        + ":".join(cols_sorted)
    ).encode("utf-8") + row_sample
    fp = hashlib.sha256(payload).hexdigest()
    return DatasetSnapshotRef(
        fingerprint=fp,
        row_count=len(df),
        col_count=len(df.columns),
        columns=cols_sorted,
    )


# ---------------------------------------------------------------------------
# AnalyticalRequest — normalized, immutable request envelope
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class AnalyticalRequest:
    """Immutable request envelope passed from UI → router → handler."""

    command_str: str                # raw user input
    parsed: dict                    # output of parse_stata_command()
    df: pd.DataFrame                # active panel dataset — never serialized
    correlation_id: str             # uuid4, generated at UI entry point
    dataset_ref: DatasetSnapshotRef # lightweight fingerprint
    tenant_id: str = ""             # Wave 8 multi-tenant scoping
    session_id: str = ""            # Streamlit session_id

    class Config:
        arbitrary_types_allowed = True  # for pd.DataFrame


# ---------------------------------------------------------------------------
# CapabilityResult — normalized output contract
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class CapabilityResult:
    """Immutable result envelope returned by route() to pages."""

    status: Literal["success", "error", "unsupported", "partial"]
    ascii_output: str = ""
    chart: VisualizationSpec | None = None
    table: list[dict] | None = None
    message: str = ""
    error_code: str = ""            # one of ANALYTICAL_ERROR_CODES (or "")
    correlation_id: str = ""        # echoed from AnalyticalRequest
    run_id: str = ""                # echoed from AnalysisRunEnvelope
    engine: str = "stata_engine_v1"
    engine_version: str = "1.0"

    def to_dict(self) -> dict[str, Any]:
        """Serialize without including the raw DataFrame or non-serializable objects."""
        return {
            "status": self.status,
            "ascii_output": self.ascii_output,
            "chart": self.chart.to_dict() if self.chart else None,
            "table": self.table,
            "message": self.message,
            "error_code": self.error_code,
            "correlation_id": self.correlation_id,
            "run_id": self.run_id,
            "engine": self.engine,
            "engine_version": self.engine_version,
        }
