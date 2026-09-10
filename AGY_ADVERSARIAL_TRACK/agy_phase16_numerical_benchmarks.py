import os
import sys
import numpy as np
import pandas as pd

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

from models.analytical_contracts import AnalyticalRequest, fingerprint_df
from models.analysis_run_envelope import AnalysisRunEnvelope
from models.causal_adapters import IVAdapter, HDFEAdapter

def run_phase16_benchmarks():
    print("--- Phase 16 Gate A: Numerical Validation Benchmarks ---")
    
    # 1. Establish Golden Synthetic Dataset
    # We create a simple DGP where true coefficients are known exactly.
    np.random.seed(42)
    N = 1000
    df = pd.DataFrame({
        "company_code": np.random.randint(1, 10, N),
        "year": np.random.randint(2000, 2010, N),
        "x": np.random.normal(0, 1, N),
        "z": np.random.normal(0, 1, N), # Strong instrument for endog
        "u": np.random.normal(0, 1, N)  # Unobserved error
    })
    
    # DGP for IV: y = 2.5*endog + 1.2*x + u. endog = 0.8*z + 0.5*u
    df["endog"] = 0.8 * df["z"] + 0.5 * df["u"] + np.random.normal(0, 0.1, N)
    df["y_iv"] = 2.5 * df["endog"] + 1.2 * df["x"] + df["u"] + np.random.normal(0, 0.1, N)
    
    # DGP for HDFE: y = 1.75*x + FE_company + FE_year + error
    company_effects = df["company_code"] * 0.5
    year_effects = (df["year"] - 2000) * 0.3
    df["y_hdfe"] = 1.75 * df["x"] + company_effects + year_effects + np.random.normal(0, 0.5, N)
    
    dataset_ref = fingerprint_df(df)
    envelope = AnalysisRunEnvelope(
        request_id="ph16", correlation_id="ph16", dataset_fingerprint=dataset_ref.fingerprint, 
        normalized_command="benchmark", capability="benchmark", run_id="benchmark_run"
    )

    # 2. IV2SLS Numerical Benchmark
    print("\n[Gate A] Executing IV2SLS Numerical Benchmark")
    req_iv = AnalyticalRequest(
        command_str="ivregress y_iv x (endog = z)",
        parsed={"depvar": "y_iv", "indepvars": ["x"], "options": {"endog": ["endog"], "instruments": ["z"]}},
        df=df, correlation_id="ph16_iv", dataset_ref=dataset_ref
    )
    
    res_iv = IVAdapter.run(req_iv, envelope)
    if res_iv.status == "partial":
        # Extract coefficient for "endog"
        endog_row = next((r for r in res_iv.table if r["Variable"] == "endog"), None)
        coef = endog_row["Coefficient"]
        diff = abs(coef - 2.5)
        print(f"True Beta: 2.500000 | Estimated Beta: {coef:.6f} | Diff: {diff:.6f}")
        if diff < 0.1: # Within acceptable sampling error
            print("PASS: IV2SLS Numerical Parity Verified (TOLERANCE MET)")
        else:
            print("FAIL: IV2SLS Numerical Parity Violated!")
    else:
        print(f"FAIL: IV2SLS execution failed -> {res_iv.message}")

    # 3. HDFE Numerical Benchmark
    print("\n[Gate A] Executing HDFE Numerical Benchmark")
    req_hdfe = AnalyticalRequest(
        command_str="hdfe y_hdfe x, absorb(company_code year)",
        parsed={"depvar": "y_hdfe", "indepvars": ["x"], "options": {"absorb": ["company_code", "year"]}},
        df=df, correlation_id="ph16_hdfe", dataset_ref=dataset_ref
    )
    
    res_hdfe = HDFEAdapter.run(req_hdfe, envelope)
    if res_hdfe.status == "partial":
        x_row = next((r for r in res_hdfe.table if r["Variable"] == "x"), None)
        coef = x_row["Coefficient"]
        diff = abs(coef - 1.75)
        print(f"True Beta: 1.750000 | Estimated Beta: {coef:.6f} | Diff: {diff:.6f}")
        if diff < 0.05:
            print("PASS: HDFE Numerical Parity Verified (TOLERANCE MET)")
        else:
            print("FAIL: HDFE Numerical Parity Violated!")
    else:
        print(f"FAIL: HDFE execution failed -> {res_hdfe.message}")

if __name__ == "__main__":
    run_phase16_benchmarks()
