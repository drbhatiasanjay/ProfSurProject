import json

import pytest

from models.validation_ledger import (
    STATUS_PASS,
    ValidationLedgerError,
    ValidationRecord,
    derive_validation_status,
    write_manifest,
)


def _record(**overrides):
    values = {
        "capability": "ivregress",
        "estimator_variant": "2sls",
        "code_revision": "abc123",
        "dataset_fingerprint": "sha256:data",
        "sample_fingerprint": "sha256:sample",
        "benchmark_id": "iv-known-answer-v1",
        "numerical_status": STATUS_PASS,
        "assumption_status": STATUS_PASS,
        "methodological_status": STATUS_PASS,
        "reproducibility_status": STATUS_PASS,
        "reviewer_status": STATUS_PASS,
        "limitations": ("fixture only",),
        "evidence_refs": ("evidence/ivregress/run-1/benchmark_results.json",),
    }
    values.update(overrides)
    return ValidationRecord(**values)


def test_all_independent_gates_are_required_for_validation():
    assert derive_validation_status(_record()) == "VALIDATED"
    assert derive_validation_status(_record(methodological_status="PARTIAL")) == "NOT_VALIDATED"
    assert derive_validation_status(_record(reviewer_status="NOT_RUN")) == "NOT_VALIDATED"


def test_record_is_immutable_and_rejects_handler_emitted_validated_status():
    record = _record()
    with pytest.raises((AttributeError, TypeError)):
        record.capability = "gmm"
    with pytest.raises(ValidationLedgerError):
        _record(numerical_status="VALIDATED")


def test_record_serialization_is_json_safe_and_copies_sequences():
    record = _record()
    payload = record.to_dict()
    assert payload["limitations"] == ["fixture only"]
    assert json.loads(json.dumps(payload))["capability"] == "ivregress"


def test_manifest_detects_duplicate_or_unsafe_evidence_references(tmp_path):
    with pytest.raises(ValidationLedgerError):
        write_manifest(tmp_path, _record(evidence_refs=("a.json", "a.json")))
    with pytest.raises(ValidationLedgerError):
        write_manifest(tmp_path, _record(evidence_refs=("../secrets.txt",)))
