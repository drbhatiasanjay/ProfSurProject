"""
models/scenario_capability.py — Wave 5 scenario adapter (contract-repaired).

STATUS: CANDIDATE / INTERVENTION PREVIEW ONLY

A validated counterfactual scenario requires:
  1. Baseline: mean predictions from a fitted model on unmodified data
  2. Intervention: variable shift applied to held-constant dataset
  3. Prediction: model re-scores the intervened dataset
  4. Uncertainty: prediction intervals or bootstrapped CIs
  5. Comparison: delta between baseline and intervened predictions
  6. Provenance: run_id, model reference, dataset fingerprint

This adapter provides only an INTERVENTION PREVIEW (steps 1-2 partial)
and must NOT claim success as a counterfactual prediction result.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List

import pandas as pd

from .analytical_contracts import AnalyticalRequest, CapabilityResult
from .analysis_run_envelope import AnalysisRunEnvelope


@dataclass
class InterventionPreview:
    """Metadata about a scenario intervention — NOT a validated counterfactual."""
    baseline_description: str
    interventions: Dict[str, float]
    held_constant: List[str]
    model_used: str
    status: str = "INTERVENTION_PREVIEW"
    validation_required: str = (
        "Prediction, uncertainty quantification, and baseline comparison "
        "are required before this can be classified as counterfactual analysis."
    )


class ScenarioAdapter:
    """
    CANDIDATE — Intervention preview only.

    Returns 'partial' (not 'success') because it applies variable shifts
    without a fitted model, uncertainty, or baseline/intervention comparison.
    Full counterfactual analysis is a future Wave 6+ capability.
    """

    _STATUS_MESSAGE = (
        "INTERVENTION PREVIEW (not validated counterfactual): "
        "Variable shifts have been applied to the dataset copy. "
        "A fitted model, baseline predictions, uncertainty quantification, "
        "and intervention/baseline comparison are required for validated scenario analysis."
    )

    @staticmethod
    def run(request: AnalyticalRequest, run_envelope: AnalysisRunEnvelope) -> CapabilityResult:
        parsed = request.parsed
        df: pd.DataFrame = request.df.copy()
        opts: dict = parsed.get("options", {})
        interventions: dict = opts.get("interventions", {})

        if not interventions:
            return CapabilityResult(
                status="unsupported",
                message=(
                    "Scenario requires at least one intervention. "
                    "Provide via options: interventions={'variable': delta_value}. "
                    "Example: scenario leverage tax=-0.05"
                ),
                error_code="UNSUPPORTED_CAPABILITY",
                correlation_id=request.correlation_id,
            )

        # Apply shifts — explicitly documented as preview, not prediction
        applied = {}
        skipped = {}
        for col, shift in interventions.items():
            if col in df.columns:
                df[col] = df[col] + float(shift)
                applied[col] = shift
            else:
                skipped[col] = f"column not found"

        if not applied:
            return CapabilityResult(
                status="error",
                message=f"No valid intervention columns found. Skipped: {skipped}",
                error_code="VARIABLE_NOT_FOUND",
                correlation_id=request.correlation_id,
            )

        preview = InterventionPreview(
            baseline_description="Current dataset (unmodified)",
            interventions=applied,
            held_constant=[c for c in df.columns if c not in applied],
            model_used="None — no fitted model applied",
        )

        summary_rows = [
            {"Component": "Status", "Value": "INTERVENTION PREVIEW"},
            {"Component": "Baseline", "Value": preview.baseline_description},
            {"Component": "Model applied", "Value": preview.model_used},
            {"Component": "Validated counterfactual", "Value": "NO"},
            {"Component": "Required for validation",
             "Value": "Fitted model + baseline predictions + uncertainty + comparison"},
        ] + [
            {"Component": f"Intervention: {col}", "Value": f"shift {delta:+.4f}"}
            for col, delta in applied.items()
        ] + (
            [{"Component": f"Skipped: {col}", "Value": reason}
             for col, reason in skipped.items()]
        )

        ascii_out = (
            f"{ScenarioAdapter._STATUS_MESSAGE}\n\n"
            f"Interventions applied: {applied}\n"
            + (f"Skipped (not found): {skipped}\n" if skipped else "")
        )

        # Return 'partial' — intervention applied but not a complete scenario result
        return CapabilityResult(
            status="partial",
            ascii_output=ascii_out,
            table=summary_rows,
            message=ScenarioAdapter._STATUS_MESSAGE,
            metadata={
                "methodology_status": "CANDIDATE",
                "result_type": "INTERVENTION_PREVIEW",
                "interventions": applied,
            },
            correlation_id=request.correlation_id,
            run_id=run_envelope.run_id,
        )
