import os
import sys
import pandas as pd

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, PROJECT_ROOT)

from models.gmm_adapter import CurrentProfSurGMMAdapter
from models.analytical_contracts import AnalyticalRequest
from models.analysis_run_envelope import AnalysisRunEnvelope

def test_gmm_lag_cap():
    print("Testing D-AGY-002: GMM Lag Constraints (Safe Cap = 4)")
    
    # Mock data
    df = pd.DataFrame({
        "company_code": [1]*50 + [2]*50,
        "year": list(range(2000, 2050)) * 2,
        "leverage": [0.5]*100,
        "prof": [0.1]*100
    })
    
    envelope = AnalysisRunEnvelope(
        request_id="req1", 
        correlation_id="corr1", 
        dataset_fingerprint="fp1", 
        normalized_command="gmm", 
        capability="gmm_estimator", 
        run_id="test_gmm_cap"
    )
    
    # 1. Test lag 4 (Should pass the cap, but fail on data since variables are missing lag columns unless we prep them)
    # The adapter expects caller to pre-process data or it creates lags internally. Wait, the adapter creates them:
    # `work[f"{y_col}_lag{lag}"] = work.groupby(entity)[y_col].shift(lag)`
    from models.analytical_contracts import fingerprint_df
    dataset_ref = fingerprint_df(df)
    
    req_safe = AnalyticalRequest(
        command_str="gmm leverage prof",
        parsed={"depvar": "leverage", "indepvars": ["prof"], "options": {"lags": "1 4"}},
        df=df,
        correlation_id="corr_safe",
        dataset_ref=dataset_ref
    )
    
    res_safe = CurrentProfSurGMMAdapter.run(req_safe, envelope)
    print(f"Safe lag (4) result status: {res_safe.status}")
    if res_safe.status == "error" and "exceeds the safe maximum" in res_safe.message:
        print("FAIL: Lag 4 was falsely rejected.")
    else:
        print("PASS: Lag 4 was not rejected by the cap.")
        
    # 2. Test lag 5 (Should fail immediately)
    req_unsafe = AnalyticalRequest(
        command_str="gmm leverage prof",
        parsed={"depvar": "leverage", "indepvars": ["prof"], "options": {"lags": "1 5"}},
        df=df,
        correlation_id="corr_unsafe",
        dataset_ref=dataset_ref
    )
    
    res_unsafe = CurrentProfSurGMMAdapter.run(req_unsafe, envelope)
    print(f"Unsafe lag (5) result status: {res_unsafe.status}")
    if res_unsafe.status == "error" and "exceeds the safe maximum" in res_safe.message:
        print("PASS: Lag 5 was correctly rejected with error code:", res_unsafe.error_code)
    elif res_unsafe.status == "error" and "exceeds the safe maximum" in res_unsafe.message:
        print("PASS: Lag 5 was correctly rejected with error code:", res_unsafe.error_code)
    else:
        print("FAIL: Lag 5 was allowed to bypass the cap! Message:", res_unsafe.message)

if __name__ == "__main__":
    test_gmm_lag_cap()
