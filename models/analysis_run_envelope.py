"""
models/analysis_run_envelope.py — Wave 2 minimal AnalysisRunEnvelope.

Binds run provenance for every route() call. Wave 8 expands this into
the full FDI multi-tenant contract. (PRD adversarial review H-01)
"""
from __future__ import annotations

import datetime
from dataclasses import dataclass
from typing import Literal

_UTC = datetime.timezone.utc


@dataclass(frozen=True)
class AnalysisRunEnvelope:
    """Minimal immutable provenance record for one analytical execution."""

    run_id: str                          # uuid4 — authoritative run identity
    request_id: str                      # = correlation_id from AnalyticalRequest
    correlation_id: str                  # tracing ID across UI→parser→router→engine
    dataset_fingerprint: str             # from DatasetSnapshotRef.fingerprint
    normalized_command: str              # parsed cmd string
    capability: str                      # resolved capability name
    method: str = ""                     # sub-method e.g. "fe" | "re" | "2sls"
    engine: str = "stata_engine_v1"
    engine_version: str = "1.0"
    status: Literal[
        "pending", "success", "error", "unsupported"
    ] = "pending"
    started_at: str = ""                 # ISO-8601
    completed_at: str = ""              # ISO-8601

    @classmethod
    def create(
        cls,
        *,
        run_id: str,
        correlation_id: str,
        dataset_fingerprint: str,
        normalized_command: str,
        capability: str,
        method: str = "",
    ) -> "AnalysisRunEnvelope":
        """Factory with auto-stamped started_at."""
        now = datetime.datetime.now(_UTC).isoformat()
        return cls(
            run_id=run_id,
            request_id=correlation_id,
            correlation_id=correlation_id,
            dataset_fingerprint=dataset_fingerprint,
            normalized_command=normalized_command,
            capability=capability,
            method=method,
            started_at=now,
        )

    def complete(
        self, status: Literal["success", "error", "unsupported"]
    ) -> "AnalysisRunEnvelope":
        """Return a new envelope with status and completed_at stamped."""
        now = datetime.datetime.now(_UTC).isoformat()
        # frozen=True — must reconstruct
        return AnalysisRunEnvelope(
            run_id=self.run_id,
            request_id=self.request_id,
            correlation_id=self.correlation_id,
            dataset_fingerprint=self.dataset_fingerprint,
            normalized_command=self.normalized_command,
            capability=self.capability,
            method=self.method,
            engine=self.engine,
            engine_version=self.engine_version,
            status=status,
            started_at=self.started_at,
            completed_at=now,
        )
