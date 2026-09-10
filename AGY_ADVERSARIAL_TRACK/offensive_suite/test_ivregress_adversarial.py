import os
import sys
import pandas as pd

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, PROJECT_ROOT)

from models.analytical_contracts import AnalyticalRequest
from models.analysis_run_envelope import AnalysisRunEnvelope

# Try to import the ivregress adapter. Assuming it exists in models based on Phase 13 spec.
try:
    from models.ivregress_adapter import CurrentProfSurIVRegressAdapter
    has_iv = True
except ImportError:
    has_iv = False

def test_ivregress_adversarial():
    print("Testing IVRegress Adversarial Capabilities")
    if not has_iv:
        print("IVRegress adapter not found locally. Skipping.")
        return

    df = pd.DataFrame({
        "company_code": [1]*50 + [2]*50,
        "year": list(range(2000, 2050)) * 2,
        "leverage": [0.5]*100,
        "prof": [0.1]*100,
        "x1": [1.0]*100,
        "x2": [1.0]*100, # Perfect collinearity
    })
    
    envelope = AnalysisRunEnvelope(
        request_id="req2", 
        correlation_id="corr2", 
        dataset_fingerprint="fp2", 
        normalized_command="ivregress", 
        capability="iv_estimator", 
        run_id="test_iv"
    )
    
    from models.analytical_contracts import fingerprint_df
    dataset_ref = fingerprint_df(df)

    req1 = AnalyticalRequest(
        command_str="ivregress leverage (prof = x1 x2)",
        parsed={"depvar": "leverage", "indepvars": ["prof", "x1", "x2"]},
        df=df,
        correlation_id="corr_iv1",
        dataset_ref=dataset_ref
    )
    
    try:
        res1 = CurrentProfSurIVRegressAdapter.run(req1, envelope)
        print(f"Collinearity result status: {res1.status}")
    except Exception as e:
        print(f"Collinearity crash: {e}")

if __name__ == "__main__":
    test_ivregress_adversarial()
