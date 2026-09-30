"""Provider-neutral isolated simulation matrix for Phase 15.

This module orchestrates bounded scenario branches. It does not claim causal
counterfactual validity: callers supply the transformation and perspective
evaluators, while this layer guarantees isolation, reproducibility, and
transparent comparison metadata.
"""

from __future__ import annotations

import os
import hashlib
import json
from copy import deepcopy
from concurrent.futures import ThreadPoolExecutor
from typing import Any, Callable, Mapping, Sequence

import numpy as np
import pandas as pd

from .analytical_contracts import fingerprint_df

# Feature Flag for Parallel Simulation Execution (SW-22)
ENABLE_PARALLEL_SIMULATIONS: bool = os.getenv("ENABLE_PARALLEL_SIMULATIONS", "false").lower() == "true"

Transform = Callable[[pd.DataFrame], pd.DataFrame | None]
Evaluator = Callable[[pd.DataFrame, np.random.Generator], Mapping[str, Any]]


def _branch_seed(seed: int, index: int, name: str) -> int:
    payload = f"{int(seed)}:{index}:{name}".encode("utf-8")
    return int.from_bytes(hashlib.sha256(payload).digest()[:8], "big")


def _run_single_case(
    index: int,
    case: Mapping[str, Any],
    name: str,
    source: pd.DataFrame,
    perspectives: Mapping[str, Evaluator],
    seed: int,
    source_fprint: str,
) -> dict[str, Any]:
    branch = deepcopy(source)
    transform = case.get("transform")
    if transform is not None and not callable(transform):
        raise TypeError(f"transform for {name!r} must be callable")
    if transform is not None:
        transformed = transform(branch)
        if transformed is not None:
            if not isinstance(transformed, pd.DataFrame):
                raise TypeError(f"transform for {name!r} must return a DataFrame or None")
            branch = transformed

    branch_seed = _branch_seed(seed, index, name)
    outputs: dict[str, dict[str, Any]] = {}
    for perspective, evaluator in perspectives.items():
        if not callable(evaluator):
            raise TypeError(f"perspective {perspective!r} must be callable")
        value = evaluator(deepcopy(branch), np.random.default_rng(branch_seed))
        if not isinstance(value, Mapping):
            raise TypeError(f"perspective {perspective!r} must return a mapping")
        outputs[str(perspective)] = dict(value)

    return {
        "index": index,
        "name": name,
        "seed": branch_seed,
        "source_fingerprint": source_fprint,
        "branch_fingerprint": fingerprint_df(branch).fingerprint,
        "observations": int(len(branch)),
        "outputs": outputs,
    }


def run_simulation_matrix(
    source: pd.DataFrame,
    cases: Sequence[Mapping[str, Any]],
    perspectives: Mapping[str, Evaluator],
    *,
    seed: int = 0,
    disagreement_tolerance: float = 1e-9,
    use_parallel: bool | None = None,
) -> dict[str, Any]:
    """Run isolated simulation branches and return auditable comparisons.
    
    SW-22: Supports both deterministic sequential execution and feature-flagged
    parallel matrix evaluation with immutable dataframe isolation.
    """
    if not isinstance(source, pd.DataFrame):
        raise TypeError("source must be a pandas DataFrame")
    if not cases:
        raise ValueError("at least one simulation case is required")
    if not perspectives:
        raise ValueError("at least one perspective evaluator is required")
    names = [str(case.get("name", "")).strip() for case in cases]
    if any(not name for name in names) or len(set(names)) != len(names):
        raise ValueError("simulation case names must be non-empty and unique")
    if disagreement_tolerance < 0:
        raise ValueError("disagreement_tolerance must be non-negative")

    is_parallel = ENABLE_PARALLEL_SIMULATIONS if use_parallel is None else bool(use_parallel)
    source_ref = fingerprint_df(source)
    results: list[dict[str, Any]] = []

    if is_parallel and len(cases) > 1:
        with ThreadPoolExecutor(max_workers=min(len(cases), 4)) as executor:
            futures = [
                executor.submit(
                    _run_single_case, i, cases[i], names[i], source, perspectives, seed, source_ref.fingerprint
                )
                for i in range(len(cases))
            ]
            raw_results = [f.result() for f in futures]
            raw_results.sort(key=lambda x: x["index"])
            results = [{k: v for k, v in r.items() if k != "index"} for r in raw_results]
    else:
        for index, item in enumerate(cases):
            res_unit = _run_single_case(
                index, item, names[index], source, perspectives, seed, source_ref.fingerprint
            )
            res_unit.pop("index", None)
            results.append(res_unit)

    numeric_keys = sorted({
        str(key)
        for result in results
        for output in result["outputs"].values()
        for key, value in output.items()
        if isinstance(value, (int, float, np.number)) and not isinstance(value, bool)
    })
    sensitivity: list[dict[str, Any]] = []
    baseline = results[0]
    for result in results:
        for key in numeric_keys:
            base_values = [o.get(key) for o in baseline["outputs"].values() if isinstance(o.get(key), (int, float, np.number))]
            current_values = [o.get(key) for o in result["outputs"].values() if isinstance(o.get(key), (int, float, np.number))]
            if base_values and current_values:
                sensitivity.append({
                    "case": result["name"],
                    "metric": key,
                    "baseline_mean": float(np.mean(base_values)),
                    "case_mean": float(np.mean(current_values)),
                    "delta": float(np.mean(current_values) - np.mean(base_values)),
                })

    disagreements: list[dict[str, Any]] = []
    for result in results:
        for key in numeric_keys:
            values = {
                perspective: float(output[key])
                for perspective, output in result["outputs"].items()
                if isinstance(output.get(key), (int, float, np.number)) and not isinstance(output.get(key), bool)
            }
            if len(values) >= 2:
                spread = max(values.values()) - min(values.values())
                disagreements.append({
                    "case": result["name"],
                    "metric": key,
                    "values": values,
                    "spread": float(spread),
                    "status": "AGREEMENT" if spread <= disagreement_tolerance else "DISAGREEMENT",
                })

    return {
        "status": "completed",
        "seed": int(seed),
        "execution_mode": "parallel" if is_parallel else "sequential",
        "source_fingerprint": source_ref.fingerprint,
        "source_observations": int(len(source)),
        "cases": results,
        "sensitivity": sensitivity,
        "disagreements": disagreements,
        "limitations": [
            "Simulation branches are isolated and reproducible, not validated causal counterfactuals.",
            "Perspective disagreement reports numerical spread; it does not select a scientifically correct perspective.",
        ],
    }
