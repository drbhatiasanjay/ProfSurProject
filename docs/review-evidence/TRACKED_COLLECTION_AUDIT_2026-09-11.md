# Tracked Pytest Collection Audit — 2026-09-11

Generated: 2026-09-11 (consolidated serial controls)
Probe workers: 1; collection timeout per file: 20s; plugin autoload disabled.
Coverage: files 1-20 of 53 tracked test files, executed in two serial batches.

Summary: PASS=20, FAIL=0, TIMEOUT=0

| File | Status | Detail |
|---|---|---|
| `tests/test_agent_tools.py` | PASS | 19 tests collected in 3.70s |
| `tests/test_ai_assistant_e2e.py` | PASS | 8 tests collected in 3.15s |
| `tests/test_ai_cache.py` | PASS | 8 tests collected in 0.16s |
| `tests/test_ai_chat_guide.py` | PASS | 3 tests collected in 0.08s |
| `tests/test_ai_chat_ui.py` | PASS | 1 test collected in 0.16s |
| `tests/test_ai_copilot_canvas.py` | PASS | 3 tests collected in 0.12s |
| `tests/test_ai_stata_routing.py` | PASS | 1 test collected in 0.10s |
| `tests/test_auth.py` | PASS | 6 tests collected in 0.24s |
| `tests/test_batch_pipeline.py` | PASS | 12 tests collected in 1.37s |
| `tests/test_benchmark_contracts.py` | PASS | 3 tests collected in 3.40s |

## Batch 2: files 11–20

| File | Status | Detail |
|---|---|---|
| `tests/test_bento_components.py` | PASS | 5 tests collected in 0.18s |
| `tests/test_board_export.py` | PASS | 95 tests collected in 8.01s |
| `tests/test_bulk_upload_cmie_parse.py` | PASS | 1 test collected in 0.18s |
| `tests/test_cfo_graph.py` | PASS | 17 tests collected in 2.24s |
| `tests/test_chart_switcher_and_literature.py` | PASS | 6 tests collected in 3.14s |
| `tests/test_chat_persistence.py` | PASS | 38 tests collected in 0.20s |
| `tests/test_chatbot.py` | PASS | 72 tests collected in 2.57s |
| `tests/test_citation_inspector.py` | PASS | 6 tests collected in 2.86s |
| `tests/test_cmie_batch_utils.py` | PASS | 5 tests collected in 0.09s |
| `tests/test_cmie_feature_gate.py` | PASS | 3 tests collected in 0.12s |

## Interpretation

This is a bounded collection audit, not a full-suite pass. The first 20 of 53
tracked test files collected successfully in serial controls. The prior
four-worker probe timed out under local Windows process contention; no failure
is inferred from those timeouts. Full execution, authenticated browser
acceptance, and the external AI sweep remain separately gated.
