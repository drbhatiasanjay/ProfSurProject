"""Tests for cmie.batch_pipeline — F.3.3/F.3.4/F.3.5 semantics.

Uses a FakeClient that mirrors the subset of CmieClient surface the pipeline
calls (`download_wapicall_zip`). All time-consuming pauses are neutralised by
passing `inter_call_delay_s=0` and using a `retry_after_s=0.01` on rate-limit
fixtures so the whole suite runs in under a second.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any, List, Tuple

import pytest

from cmie.batch_pipeline import (
    CompanyResult,
    BatchSummary,
    run_per_company_batch,
)
from cmie.errors import (
    CmieAuthError,
    CmieEntitlementError,
    CmieNetworkError,
    CmieRateLimitError,
    CmieSchemaError,
    CmieZipError,
)


class FakeClient:
    """Minimal test double for `CmieClient.download_wapicall_zip`.

    `script` is a list of step tuples:
        ("ok",   bytes_to_write)
        ("raise", exception_instance)
    One step is consumed per `download_wapicall_zip` call.
    """

    def __init__(self, script: List[Tuple[str, Any]]):
        self._script = list(script)
        self.calls: list[int] = []  # company_codes received, in order

    def download_wapicall_zip(self, company_codes, *, dest_path, on_progress=None):
        self.calls.extend(int(c) for c in company_codes)
        if not self._script:
            raise AssertionError("FakeClient exhausted — more calls than scripted")
        action, payload = self._script.pop(0)
        if action == "ok":
            p = Path(dest_path)
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_bytes(payload)
            return str(p)
        if action == "raise":
            raise payload
        raise AssertionError(f"unknown FakeClient action {action!r}")


# ────────────────────────────────────────────────────────────── happy path


def test_happy_path_two_companies(tmp_path):
    companies = [(100001, "Reliance"), (100002, "Tata")]
    client = FakeClient([("ok", b"PKfake"), ("ok", b"PKfake")])
    results, summary = run_per_company_batch(
        api_key="dummy",
        companies=companies,
        out_dir=tmp_path,
        inter_call_delay_s=0,
        _client=client,
    )
    assert len(results) == 2
    assert all(r.status == "success" for r in results)
    assert summary.succeeded == 2
    assert summary.failed == 0
    assert summary.skipped == 0
    assert summary.aborted_auth is False
    assert summary.circuit_opened is False
    # Each success should have its zip path recorded
    for r in results:
        assert r.zip_path is not None
        assert Path(r.zip_path).exists()


# ────────────────────────────────────────────────────── F.3.3 abort-on-auth


def test_auth_error_aborts_batch(tmp_path):
    companies = [(1, "A"), (2, "B"), (3, "C")]
    client = FakeClient(
        [("raise", CmieAuthError(code="AUTH", message="bad passkey"))]
    )
    results, summary = run_per_company_batch(
        api_key="dummy",
        companies=companies,
        out_dir=tmp_path,
        inter_call_delay_s=0,
        _client=client,
    )
    assert len(results) == 3
    assert results[0].status == "failed"
    assert results[0].outcome == "auth"
    assert results[0].error_code == "AUTH"
    assert results[1].status == "skipped"
    assert results[1].outcome == "aborted_auth"
    assert results[1].error_code == "ABORTED_AUTH"
    assert results[2].status == "skipped"
    assert summary.aborted_auth is True
    assert summary.succeeded == 0
    assert summary.failed == 1
    assert summary.skipped == 2
    # Only ONE wapicall HTTP call was made — the remaining 2 were not attempted
    assert client.calls == [1]


# ─────────────────────────────── entitlement is per-company, does NOT abort


def test_entitlement_error_does_not_abort(tmp_path):
    companies = [(1, "A"), (2, "B")]
    client = FakeClient([
        ("raise", CmieEntitlementError(code="CMIE_ERROR", message="not subscribed")),
        ("ok", b"PKfake"),
    ])
    results, summary = run_per_company_batch(
        api_key="dummy",
        companies=companies,
        out_dir=tmp_path,
        inter_call_delay_s=0,
        _client=client,
    )
    assert results[0].outcome == "entitlement"
    assert results[0].status == "failed"
    assert results[1].status == "success"
    assert summary.aborted_auth is False
    assert summary.succeeded == 1
    assert summary.failed == 1


# ────────────────────────────── F.3.4 Retry-After honour (pause, no retry)


def test_rate_limit_pauses_then_continues(tmp_path):
    companies = [(1, "A"), (2, "B")]
    client = FakeClient([
        # retry_after_s=0.01 — pause is trivial; continue to next company
        ("raise", CmieRateLimitError(
            code="RATE_LIMIT", message="429", detail="Retry-After: 0.01",
            retry_after_s=0.01,
        )),
        ("ok", b"PKfake"),
    ])
    results, summary = run_per_company_batch(
        api_key="dummy",
        companies=companies,
        out_dir=tmp_path,
        inter_call_delay_s=0,
        _client=client,
    )
    assert len(results) == 2
    assert results[0].outcome == "rate_limit"
    assert results[0].status == "failed"
    assert results[1].status == "success"
    assert summary.aborted_auth is False
    # Pipeline did NOT retry the rate-limited company — it moved on
    assert client.calls == [1, 2]


def test_rate_limit_without_retry_after_uses_default(tmp_path):
    """CMIE didn't supply Retry-After → fall back to `retry_after_default_s`."""
    companies = [(1, "A"), (2, "B")]
    client = FakeClient([
        ("raise", CmieRateLimitError(
            code="RATE_LIMIT", message="429", detail="HTTP 429",
            retry_after_s=None,
        )),
        ("ok", b"PKfake"),
    ])
    # Use retry_after_default_s=0.01 to keep the test fast
    results, _ = run_per_company_batch(
        api_key="dummy",
        companies=companies,
        out_dir=tmp_path,
        inter_call_delay_s=0,
        retry_after_default_s=0.01,
        _client=client,
    )
    assert results[0].outcome == "rate_limit"
    assert results[1].status == "success"


# ────────────────────────────────── F.3.5 circuit breaker on consecutive 5xx


def test_circuit_breaker_opens_on_5_consecutive_server_errors(tmp_path):
    companies = [(i, f"C{i}") for i in range(1, 8)]  # 7 companies
    # 5 consecutive SERVER errors; last 2 should never be attempted
    script = [("raise", CmieNetworkError(code="SERVER", message="500")) for _ in range(5)]
    script += [("ok", b"PK")] * 2  # should not reach these
    client = FakeClient(script)

    results, summary = run_per_company_batch(
        api_key="dummy",
        companies=companies,
        out_dir=tmp_path,
        inter_call_delay_s=0,
        circuit_breaker_threshold=5,
        _client=client,
    )
    assert len(results) == 7
    assert summary.circuit_opened is True
    # First 5 attempted (and failed), last 2 skipped
    assert client.calls == [1, 2, 3, 4, 5]
    assert [r.status for r in results[:5]] == ["failed"] * 5
    assert [r.outcome for r in results[:5]] == ["server"] * 5
    assert [r.status for r in results[5:]] == ["skipped"] * 2
    assert [r.outcome for r in results[5:]] == ["circuit_open"] * 2
    assert all(r.error_code == "CIRCUIT_OPEN" for r in results[5:])


def test_server_errors_reset_on_success(tmp_path):
    """3 SERVER errors, then a SUCCESS, then 2 more — circuit stays closed."""
    companies = [(i, f"C{i}") for i in range(1, 6)]
    script = [
        ("raise", CmieNetworkError(code="SERVER", message="500")),
        ("raise", CmieNetworkError(code="SERVER", message="500")),
        ("raise", CmieNetworkError(code="SERVER", message="500")),
        ("ok", b"PKfake"),
        ("ok", b"PKfake"),
    ]
    client = FakeClient(script)
    results, summary = run_per_company_batch(
        api_key="dummy",
        companies=companies,
        out_dir=tmp_path,
        inter_call_delay_s=0,
        circuit_breaker_threshold=5,
        _client=client,
    )
    assert summary.circuit_opened is False
    assert summary.succeeded == 2
    assert summary.failed == 3
    # All 5 companies were actually attempted
    assert client.calls == [1, 2, 3, 4, 5]


def test_network_error_does_not_trip_circuit_breaker(tmp_path):
    """NETWORK / TIMEOUT are not SERVER outcomes — they reset the counter."""
    companies = [(i, f"C{i}") for i in range(1, 7)]
    script = [
        # 4 SERVER errors (below threshold=5)
        ("raise", CmieNetworkError(code="SERVER", message="500")),
        ("raise", CmieNetworkError(code="SERVER", message="500")),
        ("raise", CmieNetworkError(code="SERVER", message="500")),
        ("raise", CmieNetworkError(code="SERVER", message="500")),
        # A NETWORK error resets the consecutive-server counter
        ("raise", CmieNetworkError(code="NETWORK", message="connection reset")),
        # Then a SERVER again — should not open the circuit (counter reset at 4)
        ("raise", CmieNetworkError(code="SERVER", message="500")),
    ]
    client = FakeClient(script)
    results, summary = run_per_company_batch(
        api_key="dummy",
        companies=companies,
        out_dir=tmp_path,
        inter_call_delay_s=0,
        circuit_breaker_threshold=5,
        _client=client,
    )
    assert summary.circuit_opened is False
    assert summary.failed == 6
    assert len([r for r in results if r.outcome == "network"]) == 1


# ───────────────────────────────────────── ZIP_BAD + schema + mixed outcomes


def test_zip_bad_does_not_abort_batch(tmp_path):
    """ZIP_BAD is per-company — batch continues."""
    companies = [(1, "A"), (2, "B")]
    client = FakeClient([
        ("raise", CmieZipError(code="ZIP_BAD", message="html body at 200")),
        ("ok", b"PKfake"),
    ])
    results, summary = run_per_company_batch(
        api_key="dummy",
        companies=companies,
        out_dir=tmp_path,
        inter_call_delay_s=0,
        _client=client,
    )
    assert results[0].outcome == "zip_bad"
    assert results[1].status == "success"
    assert summary.aborted_auth is False


def test_unexpected_cmie_error_is_classified_other(tmp_path):
    """SchemaError / ValidationError / etc. land in outcome='other'."""
    companies = [(1, "A"), (2, "B")]
    client = FakeClient([
        ("raise", CmieSchemaError(code="SCHEMA", message="missing company_code")),
        ("ok", b"PKfake"),
    ])
    results, _ = run_per_company_batch(
        api_key="dummy",
        companies=companies,
        out_dir=tmp_path,
        inter_call_delay_s=0,
        _client=client,
    )
    assert results[0].outcome == "other"
    assert results[0].error_code == "SCHEMA"
    assert results[1].status == "success"


# ─────────────────────────────────────────────────────────── summary totals


def test_summary_accounts_http_calls_and_bytes(tmp_path):
    """Summary should sum http_calls and bytes_downloaded across per-company results."""
    companies = [(1, "A"), (2, "B"), (3, "C")]
    client = FakeClient([
        ("ok", b"X" * 100),                                       # 100 bytes
        ("raise", CmieNetworkError(code="SERVER", message="500")),  # counts as 1+max_retries
        ("ok", b"X" * 50),                                        # 50 bytes
    ])
    results, summary = run_per_company_batch(
        api_key="dummy",
        companies=companies,
        out_dir=tmp_path,
        inter_call_delay_s=0,
        max_retries=1,
        _client=client,
    )
    assert summary.total == 3
    assert summary.succeeded == 2
    assert summary.failed == 1
    assert summary.total_bytes_downloaded == 150
    # 1 (success) + 2 (failure with max_retries=1) + 1 (success) = 4
    assert summary.total_http_calls == 4


def test_progress_callback_invoked_per_company(tmp_path):
    companies = [(1, "A"), (2, "B"), (3, "C")]
    client = FakeClient([("ok", b"X")] * 3)
    progress_log: list[tuple[int, int, str]] = []
    run_per_company_batch(
        api_key="dummy",
        companies=companies,
        out_dir=tmp_path,
        inter_call_delay_s=0,
        on_progress=lambda i, n, msg: progress_log.append((i, n, msg)),
        _client=client,
    )
    # One progress call per company before its download attempt
    assert len(progress_log) == 3
    assert progress_log[0][:2] == (0, 3)
    assert progress_log[2][:2] == (2, 3)
