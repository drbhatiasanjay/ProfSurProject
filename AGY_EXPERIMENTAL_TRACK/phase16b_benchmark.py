"""Reproducible Phase 16B local-process cache benchmark.

Measures real summarize routing with a real DataFrame. It intentionally does
not claim to measure JIT savings, multi-process sharing, or Redis performance.
"""

from concurrent.futures import ThreadPoolExecutor
import statistics
import sys
import time
import uuid
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from models.analytical_contracts import AnalyticalRequest, fingerprint_df
from models.stata_engine import parse_stata_command
from AGY_EXPERIMENTAL_TRACK.experimental_analytical_router import route, _CACHE


def request(frame: pd.DataFrame) -> AnalyticalRequest:
    command = "summarize y x"
    return AnalyticalRequest(
        command_str=command,
        parsed=parse_stata_command(command),
        df=frame,
        correlation_id=str(uuid.uuid4()),
        dataset_ref=fingerprint_df(frame),
        tenant_id="shared-analytical-panel",
        session_id=str(uuid.uuid4()),
    )


def timed_hit(frame: pd.DataFrame) -> float:
    started = time.perf_counter()
    result = route(request(frame))
    elapsed = time.perf_counter() - started
    assert result.status == "success"
    return elapsed


def main() -> None:
    frame = pd.DataFrame({"y": range(5000), "x": range(5000)})
    _CACHE.clear()
    cold = timed_hit(frame)
    samples = [timed_hit(frame) for _ in range(100)]
    with ThreadPoolExecutor(max_workers=20) as pool:
        started = time.perf_counter()
        concurrent = list(pool.map(lambda _: timed_hit(frame), range(50)))
        wall = time.perf_counter() - started
    print(f"cold_route_seconds={cold:.6f}")
    print(f"hot_p50_seconds={statistics.median(samples):.6f}")
    print(f"hot_p95_seconds={sorted(samples)[94]:.6f}")
    print(f"hot_p99_seconds={sorted(samples)[98]:.6f}")
    print(f"concurrent_50_wall_seconds={wall:.6f}")
    print(f"concurrent_50_max_seconds={max(concurrent):.6f}")
    print(f"cache_entries={len(_CACHE)}")


if __name__ == "__main__":
    main()
