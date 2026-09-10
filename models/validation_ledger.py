"""Provider-neutral validation records and fail-closed release derivation."""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable

STATUS_NOT_RUN = "NOT_RUN"
STATUS_PASS = "PASS"
STATUS_PARTIAL = "PARTIAL"
STATUS_FAIL = "FAIL"
STATUS_BLOCKED = "BLOCKED"
ALLOWED_STATUSES = frozenset(
    {STATUS_NOT_RUN, STATUS_PASS, STATUS_PARTIAL, STATUS_FAIL, STATUS_BLOCKED}
)
_SAFE_REF = re.compile(r"^(?!/)(?![A-Za-z]:)(?!.*(?:^|/|\\)\.\.(?:/|\\|$))[A-Za-z0-9_./\\-]+$")
_GATES = (
    "numerical_status",
    "assumption_status",
    "methodological_status",
    "reproducibility_status",
    "reviewer_status",
)


class ValidationLedgerError(ValueError):
    """Raised when a validation record or evidence manifest is unsafe/incomplete."""


@dataclass(frozen=True)
class ValidationRecord:
    capability: str
    estimator_variant: str
    code_revision: str
    dataset_fingerprint: str
    sample_fingerprint: str
    benchmark_id: str
    numerical_status: str = STATUS_NOT_RUN
    assumption_status: str = STATUS_NOT_RUN
    methodological_status: str = STATUS_NOT_RUN
    reproducibility_status: str = STATUS_NOT_RUN
    reviewer_status: str = STATUS_NOT_RUN
    limitations: tuple[str, ...] = ()
    evidence_refs: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        for field in ("capability", "estimator_variant", "code_revision", "dataset_fingerprint", "sample_fingerprint", "benchmark_id"):
            if not getattr(self, field).strip():
                raise ValidationLedgerError(f"{field} is required")
        for gate in _GATES:
            if getattr(self, gate) not in ALLOWED_STATUSES:
                raise ValidationLedgerError(f"invalid {gate}; VALIDATED is derived, not writable")
        for ref in self.evidence_refs:
            if not _SAFE_REF.fullmatch(ref) or ref.endswith(("/", "\\")):
                raise ValidationLedgerError(f"unsafe evidence reference: {ref!r}")
        if len(set(self.evidence_refs)) != len(self.evidence_refs):
            raise ValidationLedgerError("duplicate evidence references are not allowed")

    def to_dict(self) -> dict:
        payload = asdict(self)
        payload["limitations"] = list(self.limitations)
        payload["evidence_refs"] = list(self.evidence_refs)
        return payload


def derive_validation_status(record: ValidationRecord) -> str:
    """Derive release status; no caller can directly set ``VALIDATED``."""
    return "VALIDATED" if all(getattr(record, gate) == STATUS_PASS for gate in _GATES) else "NOT_VALIDATED"


def write_manifest(directory: str | Path, record: ValidationRecord, *, command: str = "") -> Path:
    """Write a deterministic, credential-free manifest for a validation run."""
    if not command.strip():
        raise ValidationLedgerError("manifest command is required")
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    payload = {
        "schema_version": 1,
        "record": record.to_dict(),
        "derived_status": derive_validation_status(record),
        "command": command.strip(),
    }
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    payload["manifest_sha256"] = hashlib.sha256(encoded).hexdigest()
    target = directory / "manifest.json"
    target.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return target
