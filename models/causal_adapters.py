"""
models/causal_adapters.py — Wave 5 causal method adapters (contract-repaired).

STATUS:
  IVAdapter   — IMPLEMENTED_UNVERIFIED (IV2SLS via linearmodels; requires golden benchmark)
  HDFEAdapter — IMPLEMENTED_UNVERIFIED (pyfixest feols; requires golden benchmark)
  DIDAdapter  — CANDIDATE / UNSUPPORTED (no model estimated; placeholder only)

Do not displace Wave 1 validated ivregress handler without explicit coefficient,
standard-error, diagnostic, and sample-membership comparison.
"""
from __future__ import annotations

import pandas as pd

from .analytical_contracts import AnalyticalRequest, CapabilityResult
from .analysis_run_envelope import AnalysisRunEnvelope
from .capability_status import result_status_metadata


_IDENTIFICATION_DISCLAIMER = (
    "METHODOLOGY GATE: Identification relies on specific causal assumptions "
    "(e.g. instrument exogeneity, parallel trends, exclusion restriction). "
    "These assumptions have NOT been formally verified by this agent. "
    "Results are IMPLEMENTED_UNVERIFIED and must not be cited without independent validation."
)


class IVAdapter:
    """IMPLEMENTED_UNVERIFIED — IV 2SLS via linearmodels.iv.IV2SLS."""

    @staticmethod
    def run(request: AnalyticalRequest, run_envelope: AnalysisRunEnvelope) -> CapabilityResult:
        try:
            from linearmodels.iv import IV2SLS
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
        exog_cols: list = list(parsed.get("indepvars", []))
        opts: dict = parsed.get("options", {})

        endog: list = opts.get("endog", [])
        instruments: list = opts.get("instruments", [])

        if not y_col:
            return CapabilityResult(
                status="error",
                message="IV regression requires a dependent variable.",
                error_code="SYNTAX_ERROR",
                correlation_id=request.correlation_id,
            )

        if not endog or not instruments:
            return CapabilityResult(
                status="unsupported",
                message=(
                    "IV regression requires endogenous variable(s) and instrument(s). "
                    "Provide via options: endog=[...], instruments=[...]. "
                    "Stata syntax: ivregress 2sls y x1 (x2 = z1 z2)"
                ),
                error_code="INVALID_INSTRUMENT_SPEC",
                correlation_id=request.correlation_id,
            )

        needed = [y_col] + exog_cols + list(endog) + list(instruments)
        missing = [c for c in needed if c not in df.columns]
        if missing:
            return CapabilityResult(
                status="error",
                message=f"Variables not found: {missing}",
                error_code="VARIABLE_NOT_FOUND",
                correlation_id=request.correlation_id,
            )

        df = df.dropna(subset=needed)

        y = df[y_col]
        exog = df[exog_cols].copy()
        if "const" not in exog.columns:
            exog.insert(0, "const", 1.0)
        endog_df = df[list(endog)]
        instr_df = df[list(instruments)]

        try:
            model = IV2SLS(y, exog, endog_df, instr_df)
            result = model.fit(cov_type="robust")
        except Exception as exc:
            return CapabilityResult(
                status="error",
                message=f"IV2SLS estimation failed: {exc}",
                error_code="ENGINE_FAILURE",
                correlation_id=request.correlation_id,
            )

        coef_rows = [
            {
                "Variable": var,
                "Coefficient": round(float(coef), 6),
                "Std Error": round(float(se), 6),
                "t-stat": round(float(tstat), 4),
                "p-value": round(float(pval), 4),
            }
            for var, coef, se, tstat, pval in zip(
                result.params.index,
                result.params.values,
                result.std_errors.values,
                result.tstats.values,
                result.pvalues.values,
            )
        ]

        ascii_out = (
            f"{_IDENTIFICATION_DISCLAIMER}\n\n"
            f"IV 2SLS (Robust SE) — Dependent: {y_col}\n"
            f"Endogenous: {endog}   Instruments: {instruments}\n"
            f"Observations: {int(result.nobs)}"
        )

        return CapabilityResult(
            status="partial",
            ascii_output=ascii_out,
            table=coef_rows,
            message=_IDENTIFICATION_DISCLAIMER,
            metadata=result_status_metadata("ivregress", estimator="IV2SLS"),
            correlation_id=request.correlation_id,
            run_id=run_envelope.run_id,
        )


class HDFEAdapter:
    """IMPLEMENTED_UNVERIFIED — High-Dimensional FE via pyfixest."""

    @staticmethod
    def run(request: AnalyticalRequest, run_envelope: AnalysisRunEnvelope) -> CapabilityResult:
        try:
            import pyfixest as pf
        except ImportError:
            return CapabilityResult(
                status="error",
                message="pyfixest not installed. Run: pip install pyfixest>=0.13",
                error_code="DEPENDENCY_UNAVAILABLE",
                correlation_id=request.correlation_id,
            )

        parsed = request.parsed
        df: pd.DataFrame = request.df.copy()
        y_col: str = parsed.get("depvar", "")
        x_cols: list = list(parsed.get("indepvars", []))
        opts: dict = parsed.get("options", {})
        fe_cols = opts.get("absorb", ["company_code", "year"])
        if not isinstance(fe_cols, list):
            return CapabilityResult(
                status="error",
                message="absorb() must be a validated list of variables.",
                error_code="SYNTAX_ERROR",
                metadata=result_status_metadata("hdfe"),
                correlation_id=request.correlation_id,
            )

        if not y_col:
            return CapabilityResult(
                status="error",
                message="HDFE requires a dependent variable.",
                error_code="SYNTAX_ERROR",
                correlation_id=request.correlation_id,
            )

        x_formula = " + ".join(x_cols) if x_cols else "1"
        fe_formula = " + ".join(fe_cols) if fe_cols else ""
        formula = f"{y_col} ~ {x_formula}"
        if fe_formula:
            formula += f" | {fe_formula}"

        try:
            model = pf.feols(formula, data=df, vcov="hetero")
        except Exception as exc:
            return CapabilityResult(
                status="error",
                message=f"HDFE (pyfixest) estimation failed: {exc}",
                error_code="ENGINE_FAILURE",
                correlation_id=request.correlation_id,
            )

        tidy = model.tidy()
        coef_rows = [
            {
                "Variable": str(var_name),
                "Coefficient": round(float(row["Estimate"]), 6),
                "Std Error": round(float(row["Std. Error"]), 6),
                "t-stat": round(float(row["t value"]), 4),
                "p-value": round(float(row["Pr(>|t|)"]), 4),
            }
            for var_name, row in tidy.iterrows()
        ]

        ascii_out = (
            f"{_IDENTIFICATION_DISCLAIMER}\n\n"
            f"HDFE (pyfixest) — Formula: {formula}\n"
            f"Absorbed fixed effects: {fe_formula}"
        )

        return CapabilityResult(
            status="partial",
            ascii_output=ascii_out,
            table=coef_rows,
            message=_IDENTIFICATION_DISCLAIMER,
            metadata=result_status_metadata(
                "hdfe", estimator="pyfixest.feols", absorbed_variables=fe_cols
            ),
            correlation_id=request.correlation_id,
            run_id=run_envelope.run_id,
        )


class DIDAdapter:
    """
    CANDIDATE / UNSUPPORTED — Difference-in-Differences.

    A validated DiD implementation requires:
      - Explicit treatment indicator
      - Pre/post time indicator
      - Parallel trends validation
      - Cohort-robust estimator (Callaway-Sant'Anna or Sun-Abraham)
      - Staggered adoption support (if applicable)

    Until these are implemented and validated against a benchmark,
    this handler returns 'unsupported' and must NOT claim success.
    """

    @staticmethod
    def run(request: AnalyticalRequest, run_envelope: AnalysisRunEnvelope) -> CapabilityResult:
        return CapabilityResult(
            status="unsupported",
            message=(
                "Difference-in-Differences (DiD) is registered as CANDIDATE. "
                "A validated DiD implementation requires explicit treatment/time indicators, "
                "parallel trends validation, and a cohort-robust estimator "
                "(e.g. Callaway-Sant'Anna). "
                "Use xtreg with treatment interaction as interim approach."
            ),
            error_code="UNSUPPORTED_CAPABILITY",
            metadata=result_status_metadata("didregress"),
            correlation_id=request.correlation_id,
        )
