import pandas as pd
from scipy import stats
from .analytical_contracts import AnalyticalRequest, CapabilityResult, AnalysisRunEnvelope

class CurrentProfSurGMMAdapter:
    """
    IMPLEMENTED_UNVERIFIED
    System GMM estimation with lagged dependent variable (Arellano-Bond instrument approach).
    Uses linearmodels.iv.IVGMM with lag2 and lag3 of DV as excluded instruments.
    """
    
    @staticmethod
    def run(request: AnalyticalRequest, run_envelope: AnalysisRunEnvelope) -> CapabilityResult:
        try:
            from linearmodels.iv import IVGMM
        except ImportError:
            return CapabilityResult(
                request_id=request.id,
                success=False,
                error="linearmodels not installed. Run: pip install linearmodels>=7.0",
                messages=["Dependency 'linearmodels' is required for GMM estimation."]
            )

        df = request.dataset.copy()
        y_col = request.command.dependent_var
        x_cols = request.command.independent_vars
        
        # We need an entity and time column in the panel. In our schema: 'company_code', 'year'
        # Check if they exist.
        if "company_code" not in df.columns or "year" not in df.columns:
            return CapabilityResult(
                request_id=request.id,
                success=False,
                error="GMM requires 'company_code' and 'year' panel structure.",
            )
            
        entity, time = "company_code", "year"
        
        work = df.sort_values([entity, time]).copy()
        
        # Create lags
        for lag in (1, 2, 3, 4):
            work[f"{y_col}_lag{lag}"] = work.groupby(entity)[y_col].shift(lag)

        # Clip outliers as done previously
        low, high = work[y_col].quantile(0.01), work[y_col].quantile(0.99)
        work[y_col] = work[y_col].clip(lower=low, upper=high)

        # Build columns to keep
        needed = [y_col, f"{y_col}_lag1", f"{y_col}_lag2", f"{y_col}_lag3"] + list(x_cols)
        work = work.dropna(subset=needed).set_index([entity, time])

        if len(work) < 100:
            return CapabilityResult(
                request_id=request.id,
                success=False,
                error=f"Too few observations for GMM ({len(work)}). Need 100+."
            )

        y = work[y_col]
        exog = work[list(x_cols)].copy()
        exog.insert(0, "const", 1.0)
        endog = work[[f"{y_col}_lag1"]]
        instr = work[[f"{y_col}_lag2", f"{y_col}_lag3"]]

        try:
            model = IVGMM(y, exog, endog, instr)
            result = model.fit(cov_type="robust")
        except Exception as e:
            return CapabilityResult(
                request_id=request.id,
                success=False,
                error=f"GMM estimation failed: {str(e)}"
            )

        coef_table = pd.DataFrame({
            "Variable":    result.params.index.tolist(),
            "Coefficient": result.params.values,
            "Std Error":   result.std_errors.values,
            "t-stat":      result.tstats.values,
            "p-value":     result.pvalues.values,
        })

        # AR(1)/AR(2) tests via Pearson correlation on IVGMM residuals
        resid_df = result.resids.reset_index()
        resid_df.columns = [entity, time, "resid"]
        resid_df = resid_df.sort_values([entity, time])
        resid_df["resid_lag1"] = resid_df.groupby(entity)["resid"].shift(1)
        resid_df["resid_lag2"] = resid_df.groupby(entity)["resid"].shift(2)

        ar1_df = resid_df.dropna(subset=["resid", "resid_lag1"])
        ar2_df = resid_df.dropna(subset=["resid", "resid_lag2"])

        ar1_corr, ar1_p = stats.pearsonr(ar1_df["resid"], ar1_df["resid_lag1"]) if len(ar1_df) > 10 else (0.0, 1.0)
        ar2_corr, ar2_p = stats.pearsonr(ar2_df["resid"], ar2_df["resid_lag2"]) if len(ar2_df) > 10 else (0.0, 1.0)

        j = result.j_stat
        
        ar1_verdict = "AR(1) expected significant" if ar1_p < 0.05 else "AR(1) not significant"
        ar2_verdict = "AR(2) not significant (good)" if ar2_p > 0.05 else "AR(2) significant (instruments may be invalid)"

        n_obs = int(result.nobs)
        n_firms = int(work.index.get_level_values(0).nunique())
        
        # Check instrument proliferation
        instr_count = len(instr.columns)
        messages = [
            f"Arellano-Bond Dynamic Panel GMM estimated with {instr_count} excluded instruments.",
            f"Observations: {n_obs}, Firms: {n_firms}"
        ]
        if instr_count > n_firms:
            messages.append("WARNING: Instrument count exceeds number of firms. Potential overfitting (instrument proliferation).")
            
        messages.append(f"Hansen J-test p-value: {j.pval:.4f}")
        messages.append(f"AR(1) test p-value: {ar1_p:.4f} ({ar1_verdict})")
        messages.append(f"AR(2) test p-value: {ar2_p:.4f} ({ar2_verdict})")

        return CapabilityResult(
            request_id=request.id,
            success=True,
            display_tables={"System GMM": coef_table},
            run_envelope=run_envelope,
            messages=messages,
            internal_data={
                "result_obj": result,
                "nobs": n_obs,
                "r_squared": float(result.rsquared),
                "j_stat": float(j.stat)
            }
        )
