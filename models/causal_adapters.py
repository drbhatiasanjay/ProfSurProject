import pandas as pd
from .analytical_contracts import AnalyticalRequest, CapabilityResult, AnalysisRunEnvelope

class CausalAdapter:
    """Base class for methodology-gated causal methods."""
    @staticmethod
    def apply_methodology_gate(messages: list) -> list:
        messages.append("WARNING (Methodology Gate): Identification relies on specific causal assumptions (e.g. parallel trends, exogeneity). These assumptions have not been formally verified by this agent.")
        return messages

class IVAdapter(CausalAdapter):
    @staticmethod
    def run(request: AnalyticalRequest, run_envelope: AnalysisRunEnvelope) -> CapabilityResult:
        try:
            from linearmodels.iv import IV2SLS
        except ImportError:
            return CapabilityResult(request_id=request.id, success=False, error="linearmodels missing")
        
        df = request.dataset.copy()
        y_col = request.command.dependent_var
        
        # Simple extraction for IV: assume independent_vars[-1] is endogenous and we need instruments
        # This is simplified; the actual command parser needs to extract endogenous vs instruments
        exog_cols = request.command.independent_vars
        
        # For this adapter, we just do a placeholder or basic OLS if no instruments are passed
        # In a real scenario, Stata syntax: ivregress 2sls y x1 (x2 = z1 z2)
        # We will parse this in stata_engine.py and pass it via request.options
        endog = request.options.get("endog", [])
        instruments = request.options.get("instruments", [])
        
        if not endog or not instruments:
            return CapabilityResult(request_id=request.id, success=False, error="IV regression requires endogenous variables and instruments.")

        # Keep needed cols
        needed = [y_col] + exog_cols + endog + instruments
        df = df.dropna(subset=needed)

        y = df[y_col]
        exog = df[exog_cols]
        exog.insert(0, "const", 1.0)
        endog_df = df[endog]
        instr_df = df[instruments]

        try:
            model = IV2SLS(y, exog, endog_df, instr_df)
            result = model.fit(cov_type="robust")
        except Exception as e:
            return CapabilityResult(request_id=request.id, success=False, error=str(e))

        coef_table = pd.DataFrame({
            "Variable": result.params.index,
            "Coefficient": result.params.values,
            "Std Error": result.std_errors.values,
            "t-stat": result.tstats.values,
            "p-value": result.pvalues.values,
        })

        messages = IVAdapter.apply_methodology_gate([f"IV 2SLS executed. N={result.nobs}"])
        return CapabilityResult(
            request_id=request.id,
            success=True,
            display_tables={"IV 2SLS (Robust)": coef_table},
            run_envelope=run_envelope,
            messages=messages,
            internal_data={"result_obj": result}
        )

class HDFEAdapter(CausalAdapter):
    @staticmethod
    def run(request: AnalyticalRequest, run_envelope: AnalysisRunEnvelope) -> CapabilityResult:
        try:
            import pyfixest as pf
        except ImportError:
            return CapabilityResult(request_id=request.id, success=False, error="pyfixest missing")
            
        df = request.dataset.copy()
        y_col = request.command.dependent_var
        x_cols = request.command.independent_vars
        fe_cols = request.options.get("absorb", ["company_code", "year"])
        
        # Build formula: Y ~ X1 + X2 | FE1 + FE2
        x_formula = " + ".join(x_cols) if x_cols else "1"
        fe_formula = " + ".join(fe_cols) if fe_cols else ""
        formula = f"{y_col} ~ {x_formula}"
        if fe_formula:
            formula += f" | {fe_formula}"
            
        try:
            model = pf.feols(formula, data=df, vcov="hetero")
        except Exception as e:
            return CapabilityResult(request_id=request.id, success=False, error=str(e))
            
        tidy = model.tidy()
        coef_table = pd.DataFrame({
            "Variable": tidy["term"],
            "Coefficient": tidy["Estimate"],
            "Std Error": tidy["Std. Error"],
            "t-stat": tidy["t value"],
            "p-value": tidy["Pr(>|t|)"]
        })
        
        messages = HDFEAdapter.apply_methodology_gate([f"HDFE executed with absorbed fixed effects: {fe_formula}"])
        return CapabilityResult(
            request_id=request.id,
            success=True,
            display_tables={"HDFE": coef_table},
            run_envelope=run_envelope,
            messages=messages,
            internal_data={"result_obj": model}
        )
