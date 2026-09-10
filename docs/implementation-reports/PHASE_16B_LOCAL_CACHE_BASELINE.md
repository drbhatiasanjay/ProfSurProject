# Phase 16B — Local Cache Baseline

**Status:** MEASURED MVP BASELINE — not a Redis or multi-process benchmark
**Date:** 2026-09-10
**Branch:** `experimental-performance-fixes`

## Scope

The benchmark used the experimental router with a real 5,000-row pandas
DataFrame and the real `summarize y x` parser/router path. It measured one
Python process, a cold route, 100 hot hits, and 50 concurrent hot hits.

## Results

| Measurement | Result |
|---|---:|
| Cold route | 0.014301 s |
| Hot p50 | 0.000544 s |
| Hot p95 | 0.001032 s |
| Hot p99 | 0.001710 s |
| 50 concurrent hot-hit wall time | 0.030990 s |
| Maximum concurrent individual latency | 0.002275 s |
| Cache entries | 1 |

## Interpretation

The local cache materially reduces repeated `summarize` routing time in this
synthetic local-process workload. This is a cache-hit observation, not a claim
of end-to-end application improvement. It does not measure JIT savings, cold
analytical computation at production scale, multiple processes, multiple
hosts, Redis, Arrow, or Plasma.

The 50-request run is concurrency evidence for hot reads only. It is not a
cache-stampede test because the cache was warmed before the concurrent calls.

## Reproduction

```powershell
py -3.12 AGY_EXPERIMENTAL_TRACK\phase16b_benchmark.py
$env:PYTEST_DISABLE_PLUGIN_AUTOLOAD='1'
py -3.12 -m pytest -q --disable-warnings tests/test_phase16b_experimental_cache.py tests/test_cache_keys.py tests/test_ai_cache.py
```

Verification: **22 passed, 8 warnings**.

## Decision

For the current one-process MVP, retain the local cache architecture. Do not
introduce Redis, Plasma, or Arrow based on this evidence alone. Reconsider a
shared backend only after multi-process deployment or a measured p95/memory
problem appears.
