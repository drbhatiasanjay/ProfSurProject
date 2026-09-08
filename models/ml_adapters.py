"""
models/ml_adapters.py — Wave 5 ML prediction adapter (contract-repaired).

STATUS: IMPLEMENTED_UNVERIFIED

Validation design:
  - Uses GroupShuffleSplit keyed on 'company_code' to prevent firm-level leakage.
  - Time-based split is preferred for forecasting; this adapter uses group-aware
    holdout as a minimum leakage-safe baseline.
  - Cross-validation (k-fold) is NOT performed; UI wording must reflect this.
  - Alpha hyperparameter is fixed at 1.0; CV tuning is a future enhancement.
"""
from __future__ import annotations

import pandas as pd
import numpy as np

from .analytical_contracts import AnalyticalRequest, CapabilityResult
from .analysis_run_envelope import AnalysisRunEnvelope

_VALIDATION_DISCLAIMER = (
    "VALIDATION NOTE: Uses GroupShuffleSplit on 'company_code' to prevent "
    "firm-level leakage. Alpha=1.0 (no CV tuning). "
    "Time-leakage across years within firms is mitigated but not fully eliminated. "
    "Treat results as IMPLEMENTED_UNVERIFIED."
)


class MLPredictAdapter:
    """
    IMPLEMENTED_UNVERIFIED — Ridge regression with group-aware train/test split.

    Prevents firm-level leakage by keeping all observations from one firm in
    the same split partition. Does NOT perform k-fold cross-validation.
    """

    @staticmethod
    def run(request: AnalyticalRequest, run_envelope: AnalysisRunEnvelope) -> CapabilityResult:
        try:
            from sklearn.linear_model import Ridge
            from sklearn.model_selection import GroupShuffleSplit
            from sklearn.metrics import root_mean_squared_error, r2_score
        except ImportError:
            return CapabilityResult(
                status="error",
                message="scikit-learn not installed. Run: pip install scikit-learn>=1.3",
                error_code="DEPENDENCY_UNAVAILABLE",
                correlation_id=request.correlation_id,
            )

        parsed = request.parsed
        df: pd.DataFrame = request.df.copy()
        y_col: str = parsed.get("depvar", "")
        x_cols: list = list(parsed.get("indepvars", []))

        if not y_col or not x_cols:
            return CapabilityResult(
                status="error",
                message="ML predict requires dependent and independent variables.",
                error_code="SYNTAX_ERROR",
                correlation_id=request.correlation_id,
            )

        needed = [y_col] + x_cols
        missing = [c for c in needed if c not in df.columns]
        if missing:
            return CapabilityResult(
                status="error",
                message=f"Variables not found: {missing}",
                error_code="VARIABLE_NOT_FOUND",
                correlation_id=request.correlation_id,
            )

        df = df.dropna(subset=needed)

        # Group-aware split: all rows of a firm go to the same partition
        entity_col = "company_code" if "company_code" in df.columns else None
        if entity_col is None:
            return CapabilityResult(
                status="error",
                message=(
                    "ML predict requires 'company_code' column for group-aware validation. "
                    "Without it, firm-level leakage cannot be prevented."
                ),
                error_code="PANEL_NOT_DECLARED",
                correlation_id=request.correlation_id,
            )

        X = df[x_cols].values
        y = df[y_col].values
        groups = df[entity_col].values

        gss = GroupShuffleSplit(n_splits=1, test_size=0.2, random_state=42)
        train_idx, test_idx = next(gss.split(X, y, groups))

        X_train, X_test = X[train_idx], X[test_idx]
        y_train, y_test = y[train_idx], y[test_idx]
        groups_test = groups[test_idx]

        if len(X_train) < 20 or len(X_test) < 5:
            return CapabilityResult(
                status="error",
                message=f"Insufficient data after group split (train={len(X_train)}, test={len(X_test)}).",
                error_code="INSUFFICIENT_OBSERVATIONS",
                correlation_id=request.correlation_id,
            )

        model = Ridge(alpha=1.0)
        model.fit(X_train, y_train)

        preds = model.predict(X_test)
        rmse = float(root_mean_squared_error(y_test, preds))
        r2 = float(r2_score(y_test, preds))

        n_test_firms = len(np.unique(groups_test))

        feat_rows = sorted(
            [
                {"Feature": col, "Ridge Coefficient": round(float(coef), 6)}
                for col, coef in zip(x_cols, model.coef_)
            ],
            key=lambda r: abs(r["Ridge Coefficient"]),
            reverse=True,
        )

        ascii_out = (
            f"{_VALIDATION_DISCLAIMER}\n\n"
            f"Ridge Regression (alpha=1.0) — Dependent: {y_col}\n"
            f"Train N={len(X_train)} ({len(np.unique(groups[train_idx]))} firms)   "
            f"Test N={len(X_test)} ({n_test_firms} firms)\n"
            f"Test RMSE: {rmse:.4f}   Test R²: {r2:.4f}"
        )

        return CapabilityResult(
            status="success",
            ascii_output=ascii_out,
            table=feat_rows,
            message=_VALIDATION_DISCLAIMER,
            correlation_id=request.correlation_id,
            run_id=run_envelope.run_id,
        )
