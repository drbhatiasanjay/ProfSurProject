"""Authoritative implementation and methodology status for advanced capabilities."""

from __future__ import annotations

from copy import deepcopy


CAPABILITY_STATUS = {
    "ivregress": {
        "registry_status": "IMPLEMENTED_UNVERIFIED",
        "implementation": "implemented",
        "execution": "executable",
        "numerical_evidence": "synthetic 2SLS checks",
        "methodology": "unverified",
        "label": "IV/2SLS",
        "limitation": "Instrument relevance, exogeneity, and exclusion restrictions require independent validation.",
    },
    "gmm": {
        "registry_status": "IMPLEMENTED_UNVERIFIED",
        "implementation": "implemented",
        "execution": "partial",
        "numerical_evidence": "limited proxy checks",
        "methodology": "unverified",
        "label": "Experimental IV-GMM proxy",
        "limitation": "Not Arellano-Bond or Blundell-Bond System GMM.",
    },
    "hdfe": {
        "registry_status": "IMPLEMENTED_UNVERIFIED",
        "implementation": "implemented",
        "execution": "dependency-gated partial",
        "numerical_evidence": "synthetic coefficient checks",
        "methodology": "unverified",
        "label": "High-dimensional fixed effects",
        "limitation": "Sample, covariance, and absorbed-effect parity require independent validation.",
    },
    "predict_ml": {
        "registry_status": "IMPLEMENTED_UNVERIFIED",
        "implementation": "implemented",
        "execution": "partial",
        "numerical_evidence": "firm-group holdout checks",
        "methodology": "unverified",
        "label": "Ridge prediction",
        "limitation": "No forward-time validation or hyperparameter cross-validation.",
    },
    "scenario": {
        "registry_status": "CANDIDATE",
        "implementation": "preview only",
        "execution": "partial",
        "numerical_evidence": "contract and immutability checks",
        "methodology": "not validated",
        "label": "Intervention preview",
        "limitation": "Not a model-based counterfactual forecast.",
    },
    "didregress": {
        "registry_status": "CANDIDATE",
        "implementation": "not implemented",
        "execution": "unsupported",
        "numerical_evidence": "none",
        "methodology": "not validated",
        "label": "Difference-in-Differences",
        "limitation": "Requires treatment timing, parallel-trends checks, and a cohort-robust estimator.",
    },
}


def capability_status(command: str) -> dict[str, str]:
    return deepcopy(CAPABILITY_STATUS[command])


def result_status_metadata(command: str, **extra) -> dict:
    status = capability_status(command)
    metadata = {
        "capability": command,
        "registry_status": status["registry_status"],
        "implementation_status": status["implementation"],
        "execution_status": status["execution"],
        "methodology_status": status["registry_status"],
        "methodology_validation": status["methodology"],
        "methodology_limitation": status["limitation"],
    }
    metadata.update(extra)
    return metadata
