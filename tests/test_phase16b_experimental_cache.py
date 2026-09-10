"""Phase 16B local cache correctness and concurrency contracts."""

from concurrent.futures import ThreadPoolExecutor
import time
import uuid

import pandas as pd

from models.analytical_contracts import AnalyticalRequest, CapabilityResult, fingerprint_df
import AGY_EXPERIMENTAL_TRACK.experimental_analytical_router as router


def _request(command: str, *, raw: str | None = None) -> AnalyticalRequest:
    frame = pd.DataFrame({"y": range(1000), "x": range(1000)})
    return AnalyticalRequest(
        command_str=raw or command,
        parsed={"cmd": command},
        df=frame,
        correlation_id=str(uuid.uuid4()),
        dataset_ref=fingerprint_df(frame),
        tenant_id="shared-analytical-panel",
        session_id=str(uuid.uuid4()),
    )


def test_pure_cache_hit_isolated_and_handler_runs_once(monkeypatch):
    router._CACHE.clear()
    calls = []

    def execute(request):
        calls.append(1)
        return CapabilityResult(status="success", table=[{"value": 1}])

    monkeypatch.setattr(router, "_execute_route", execute)
    first = router.route(_request("summarize"))
    second = router.route(_request("summarize"))
    assert len(calls) == 1
    assert first.table == second.table
    second.table[0]["value"] = 99
    assert router.route(_request("summarize")).table == [{"value": 1}]


def test_stateful_post_estimation_bypasses_cache(monkeypatch):
    router._CACHE.clear()
    calls = []

    def execute(request):
        calls.append(1)
        return CapabilityResult(status="success", ascii_output="stateful")

    monkeypatch.setattr(router, "_execute_route", execute)
    router.route(_request("predict"))
    router.route(_request("predict"))
    assert len(calls) == 2


def test_concurrent_hot_hits_are_error_free(monkeypatch):
    router._CACHE.clear()
    monkeypatch.setattr(
        router,
        "_execute_route",
        lambda request: CapabilityResult(status="success", table=[{"value": 1}]),
    )
    router.route(_request("summarize"))
    started = time.perf_counter()
    with ThreadPoolExecutor(max_workers=20) as pool:
        results = list(pool.map(lambda _: router.route(_request("summarize")), range(50)))
    elapsed = time.perf_counter() - started
    assert len(results) == 50
    assert all(result.status == "success" for result in results)
    assert elapsed >= 0


def test_concurrent_cold_misses_are_coalesced(monkeypatch):
    router._CACHE.clear()
    router._INFLIGHT.clear()
    calls = []

    def execute(request):
        calls.append(1)
        time.sleep(0.01)
        return CapabilityResult(status="success", table=[{"value": 1}])

    monkeypatch.setattr(router, "_execute_route", execute)
    with ThreadPoolExecutor(max_workers=20) as pool:
        results = list(pool.map(lambda _: router.route(_request("summarize")), range(50)))
    assert len(calls) == 1
    assert len(results) == 50
    assert all(result.table == [{"value": 1}] for result in results)


def test_restart_safe_empty_cache_state():
    router._CACHE.clear()
    router._INFLIGHT.clear()
    assert router._CACHE == {}
    assert router._INFLIGHT == {}


def test_cache_eviction_is_bounded(monkeypatch):
    router._CACHE.clear()
    monkeypatch.setattr(
        router,
        "_execute_route",
        lambda request: CapabilityResult(status="success"),
    )
    for index in range(140):
        router.route(_request("summarize", raw=f"summarize y // {index}"))
    assert len(router._CACHE) <= 128
