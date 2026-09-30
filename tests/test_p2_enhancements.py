"""Comprehensive Validation Suite for P2 Enhancements (SW-17 through SW-25).

Tests:
- SW-17: Dynamic Confidence Interval calculations in chart engine.
- SW-18: Non-redundant session state configuration.
- SW-19: Methodological guardrail presence in ML pages.
- SW-22: Feature-flagged parallel simulation execution with immutable data isolation.
- SW-23: Task-gated Knowledge Graph routing.
- SW-24: DoubleML econometric specification completeness & isolation.
- SW-25: Workflow efficiency & transcription error elimination ledger.
"""

import os
import pytest
import pandas as pd
import numpy as np

from models.chart_switcher_engine import build_forest_plot
from models.parallel_simulations import (
    run_simulation_matrix,
    ENABLE_PARALLEL_SIMULATIONS,
)
from models.workflow_metrics import WorkflowMetricsLedger, workflow_ledger


def test_sw17_dynamic_ci_bounds_calculation():
    """SW-17: Chart engine computes 95% CIs dynamically from standard errors."""
    coef_data = {
        "profitability": {"coef": -0.345, "se": 0.050},
        "tangibility": {"coef": 0.280, "se": 0.040},
        "unestimated_var": {"coef": 0.150, "se": None},
    }
    fig = build_forest_plot(coef_data, depvar="leverage")
    assert fig is not None
    # Verify traces were created
    assert len(fig.data) >= 1
    scatter = fig.data[0]
    # Check that error_x was populated
    assert scatter.error_x is not None
    assert len(scatter.error_x.array) == 3
    # Check unestimated variable has zero error width (no fake default bar)
    assert scatter.error_x.array[2] == 0.0


def test_sw19_ml_predictive_boundary_notice():
    """SW-19: ML models page contains prominent non-causal predictive boundary notice."""
    with open("pages/9_ml_models.py", "r", encoding="utf-8") as f:
        content = f.read()
    assert "Methodological Guardrail (SW-19)" in content
    assert "non-causal predictive diagnostics" in content
    assert "structural causal identification" in content


def test_sw22_parallel_simulation_feature_flag_and_isolation():
    """SW-22: Feature-flagged parallel execution preserves branch reproducibility and immutability."""
    df = pd.DataFrame({"leverage": [0.20, 0.40, 0.60], "growth": [0.05, 0.10, 0.15]})
    df_copy = df.copy(deep=True)

    def shock(frame):
        frame["leverage"] = frame["leverage"] * 1.10
        return frame

    def eval_mean(frame, rng):
        return {"mean_lev": float(frame["leverage"].mean())}

    # Sequential execution
    res_seq = run_simulation_matrix(
        df,
        [{"name": "base"}, {"name": "shocked", "transform": shock}],
        {"eval": eval_mean},
        seed=100,
        use_parallel=False,
    )
    assert res_seq["execution_mode"] == "sequential"
    assert len(res_seq["cases"]) == 2

    # Parallel execution
    res_par = run_simulation_matrix(
        df,
        [{"name": "base"}, {"name": "shocked", "transform": shock}],
        {"eval": eval_mean},
        seed=100,
        use_parallel=True,
    )
    assert res_par["execution_mode"] == "parallel"
    assert len(res_par["cases"]) == 2

    # Parity check
    assert res_seq["cases"][0]["outputs"] == res_par["cases"][0]["outputs"]
    assert res_seq["cases"][1]["outputs"] == res_par["cases"][1]["outputs"]

    # Immutability check
    pd.testing.assert_frame_equal(df, df_copy)


def test_sw23_task_gated_knowledge_graph():
    """SW-23: Knowledge graph page has task-gated navigation banner."""
    with open("pages/7_knowledge_graph.py", "r", encoding="utf-8") as f:
        content = f.read()
    assert "Task-Gated Navigation (SW-23)" in content
    assert "Research Focus" in content


def test_sw24_doubleml_research_specification():
    """SW-24: DoubleML specification is documented with required mathematical formulas and isolation gates."""
    spec_path = "docs/research_spec_doubleml_causal.md"
    assert os.path.exists(spec_path)
    with open(spec_path, "r", encoding="utf-8") as f:
        text = f.read()
    assert "Partially Linear Regression (PLR) Model" in text
    assert "Neyman Orthogonal Score" in text
    assert "Cross-Fitting Protocol" in text
    assert "IIMCFRC 2026 Manuscript Isolation Guarantee" in text


def test_sw25_workflow_metrics_ledger():
    """SW-25: Workflow metrics ledger quantifies transcription error elimination and guardrail prevention."""
    ledger = WorkflowMetricsLedger()
    event = ledger.record_econometric_run(
        model_type="Entity Fixed Effects",
        n_obs=8677,
        gets_latex_export=True,
        guardrails_applied=["Negative Hausman Bound", "IV-Proxy Notice"],
    )
    assert event["automated_transcription"] is True
    assert event["transcription_error_risk"] == 0.0
    assert len(event["guardrails_caught"]) == 2

    stats = ledger.get_summary_statistics()
    assert stats["total_econometric_runs"] == 1
    assert stats["measured_transcription_error_rate"] == 0.0
    assert stats["automated_table_export_pct"] == 100.0
