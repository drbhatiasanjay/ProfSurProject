"""
models/gmm_adapter.py — Wave 5 GMM adapter (contract-repaired).

STATUS: IMPLEMENTED_UNVERIFIED
  - Uses linearmodels.iv.IVGMM as a proxy estimator.
  - IVGMM is NOT Arellano-Bond or Blundell-Bond system GMM.
  - The AR(1)/AR(2) tests use Pearson residual correlation, which is NOT
    the Arellano-Bond z-statistic. These are excluded pending a validated
    xtdpdsys/xtabond2-equivalent implementation.
  - Do not present this as System GMM in any UI or report.
  - Silent clipping/winsorization is removed; callers must pre-process explicitly.
"""
from __future__ import annotations

import pandas as pd
from scipy import stats

from .analytical_contracts import AnalyticalRequest, CapabilityResult, ANALYTICAL_ERROR_CODES
from .analysis_run_envelope import AnalysisRunEnvelope


class CurrentProfSurGMMAdapter:
    """
    IMPLEMENTED_UNVERIFIED — IV-GMM proxy (NOT Arellano-Bond / System GMM).

    Uses linearmodels.iv.IVGMM with lag-2 and lag-3 of the dependent variable
    as excluded instruments. This approximates dynamic panel logic but is
    fundamentally different from the Arellano-Bond (1991) or Blundell-Bond (1998)
    estimators. A validated AB/BB implementation is required before this can be
    presented as System GMM.
    """

    _METHODOLOGY_DISCLAIMER = (
        "METHODOLOGY NOTICE: This estimator uses linearmodels IVGMM (IV-based GMM), "
        "NOT Arellano-Bond or Blundell-Bond System GMM. "
        "AR(1)/AR(2) diagnostics shown are Pearson residual correlations, "
        "not the formal Arellano-Bond z-statistics. "
        "Results are UNVERIFIED and must not be cited as System GMM."
    )

    @staticmethod
    def run(request: AnalyticalRequest, run_envelope: AnalysisRunEnvelope) -> CapabilityResult:
        try:
            from linearmodels.iv import IVGMM
        except ImportError:
            return CapabilityResult(
                status="error",
                message="linearmodels not installed. Run: pip install linearmodels>=7.0",
                error_code="DEPENDENCY_UNAVAILABLE",
                correlation_id=request.correlation_id,
            )

        parsed = request.parsed
        df: pd.DataFrame = request.df.copy()
        y_col: str = parsed.get("depvar", "")
        x_cols: list = parsed.get("indepvars", [])

        if not y_col:
            return CapabilityResult(
                status="error",
                message="GMM requires a dependent variable.",
                error_code="SYNTAX_ERROR",
                correlation_id=request.correlation_id,
            )

        if "company_code" not in df.columns or "year" not in df.columns:
            return CapabilityResult(
                status="error",
                message="GMM requires 'company_code' and 'year' panel structure.",
                error_code="PANEL_NOT_DECLARED",
                correlation_id=request.correlation_id,
            )

        entity, time = "company_code", "year"
        work = df.sort_values([entity, time]).copy()

        # Create lags — no silent winsorization; caller pre-processes data
        for lag in (1, 2, 3, 4):
            work[f"{y_col}_lag{lag}"] = work.groupby(entity)[y_col].shift(lag)

        needed = [y_col, f"{y_col}_lag1", f"{y_col}_lag2", f"{y_col}_lag3"] + list(x_cols)
        missing = [c for c in needed if c not in work.columns]
        if missing:
            return CapabilityResult(
                status="error",
                message=f"Variables not found: {missing}",
                error_code="VARIABLE_NOT_FOUND",
                correlation_id=request.correlation_id,
            )

        work = work.dropna(subset=needed).set_index([entity, time])

        if len(work) < 100:
            return CapabilityResult(
                status="error",
                message=f"Too few observations for IV-GMM ({len(work)}). Minimum 100 required.",
                error_code="INSUFFICIENT_OBSERVATIONS",
                correlation_id=request.correlation_id,
            )

        y = work[y_col]
        exog = work[list(x_cols)].copy()
        exog.insert(0, "const", 1.0)
        endog = work[[f"{y_col}_lag1"]]
        instr = work[[f"{y_col}_lag2", f"{y_col}_lag3"]]

        try:
            model = IVGMM(y, exog, endog, instr)
            result = model.fit(cov_type="robust")
        except Exception as exc:
            return CapabilityResult(
                status="error",
                message=f"IV-GMM estimation failed: {exc}",
                error_code="ENGINE_FAILURE",
                correlation_id=request.correlation_id,
            )

        coef_rows = []
        for var, coef, se, tstat, pval in zip(
            result.params.index,
            result.params.values,
            result.std_errors.values,
            result.tstats.values,
            result.pvalues.values,
        ):
            coef_rows.append({
                "Variable": var,
                "Coefficient": round(float(coef), 6),
                "Std Error": round(float(se), 6),
                "t-stat": round(float(tstat), 4),
                "p-value": round(float(pval), 4),
            })

        n_obs = int(result.nobs)
        n_firms = int(work.index.get_level_values(0).nunique())
        instr_count = len(instr.columns)

        # Pearson residual correlations — labelled explicitly, NOT as Arellano-Bond AR tests
        resid_df = result.resids.reset_index()
        resid_df.columns = [entity, time, "resid"]
        resid_df = resid_df.sort_values([entity, time])
        resid_df["resid_lag1"] = resid_df.groupby(entity)["resid"].shift(1)
        resid_df["resid_lag2"] = resid_df.groupby(entity)["resid"].shift(2)

        ar1_df = resid_df.dropna(subset=["resid", "resid_lag1"])
        ar2_df = resid_df.dropna(subset=["resid", "resid_lag2"])
        ar1_corr, ar1_p = (
            stats.pearsonr(ar1_df["resid"], ar1_df["resid_lag1"])
            if len(ar1_df) > 10 else (0.0, 1.0)
        )
        ar2_corr, ar2_p = (
            stats.pearsonr(ar2_df["resid"], ar2_df["resid_lag2"])
            if len(ar2_df) > 10 else (0.0, 1.0)
        )

        j_pval = float(result.j_stat.pval) if hasattr(result, "j_stat") else float("nan")

        warnings = []
        if instr_count > n_firms:
            warnings.append(
                f"WARNING: Instrument count ({instr_count}) > firm count ({n_firms}). "
                "Instrument proliferation risk."
            )

        ascii_lines = [
            CurrentProfSurGMMAdapter._METHODOLOGY_DISCLAIMER,
            "",
            f"IV-GMM Proxy (NOT System GMM) — Dependent: {y_col}",
            f"Observations: {n_obs}   Firms: {n_firms}",
            f"Hansen J-statistic p-value: {j_pval:.4f}",
            f"Residual Pearson lag-1 correlation: r={ar1_corr:.4f}, p={ar1_p:.4f}  "
            "(NOTE: not an Arellano-Bond AR(1) test)",
            f"Residual Pearson lag-2 correlation: r={ar2_corr:.4f}, p={ar2_p:.4f}  "
            "(NOTE: not an Arellano-Bond AR(2) test)",
        ] + warnings

        return CapabilityResult(
            status="partial",
            ascii_output="\n".join(ascii_lines),
            table=coef_rows,
            message=CurrentProfSurGMMAdapter._METHODOLOGY_DISCLAIMER,
            correlation_id=request.correlation_id,
            run_id=run_envelope.run_id,
        )
