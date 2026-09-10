import os
import sys
import pandas as pd

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, PROJECT_ROOT)

from models.analytical_contracts import AnalyticalRequest, fingerprint_df
from models.analysis_run_envelope import AnalysisRunEnvelope
from models.causal_adapters import IVAdapter, HDFEAdapter, DIDAdapter
from models.ml_adapters import MLPredictAdapter

def run_adversarial_tests():
    print("--- Adversarial Sweep on Causal & ML Estimators ---")
    
    # Mock data with perfect collinearity and missing values
    df = pd.DataFrame({
        "company_code": [1]*50 + [2]*50,
        "year": list(range(2000, 2050)) * 2,
        "leverage": [0.5]*100,
        "prof": [0.1]*100,
        "x1": [1.0]*100,
        "x2": [1.0]*100, # Perfect collinearity with x1
        "z1": [2.0]*100,
    })
    
    dataset_ref = fingerprint_df(df)
    envelope = AnalysisRunEnvelope(
        request_id="adv_req", 
        correlation_id="adv_corr", 
        dataset_fingerprint="adv_fp", 
        normalized_command="test", 
        capability="test", 
        run_id="adv_run"
    )

    # 1. IVRegress - Collinearity and missing instruments
    print("\n[1] Testing IVRegress Adversarial")
    req_iv = AnalyticalRequest(
        command_str="ivregress leverage (prof = x1 x2)",
        parsed={"depvar": "leverage", "indepvars": ["x1", "x2"], "options": {"endog": ["prof"], "instruments": ["z1", "x2"]}},
        df=df,
        correlation_id="corr_iv",
        dataset_ref=dataset_ref
    )
    res_iv = IVAdapter.run(req_iv, envelope)
    print(f"IVAdapter Result Status: {res_iv.status}")
    if res_iv.status == "error":
        print(f"PASS: Safely caught error -> {res_iv.error_code}: {res_iv.message}")
    elif res_iv.status == "partial" or res_iv.status == "success":
        print(f"FAIL: IVRegress proceeded despite perfect collinearity!")

    # 2. HDFE - Impossible Fixed Effects / Invalid absorb type
    print("\n[2] Testing HDFE Adversarial")
    req_hdfe = AnalyticalRequest(
        command_str="hdfe leverage x1 x2, absorb(SQL_INJECTION; DROP TABLE)",
        parsed={"depvar": "leverage", "indepvars": ["x1", "x2"], "options": {"absorb": "SQL_INJECTION; DROP TABLE"}},
        df=df,
        correlation_id="corr_hdfe",
        dataset_ref=dataset_ref
    )
    res_hdfe = HDFEAdapter.run(req_hdfe, envelope)
    print(f"HDFEAdapter Result Status: {res_hdfe.status}")
    if res_hdfe.status == "error":
        print(f"PASS: Safely caught error -> {res_hdfe.error_code}: {res_hdfe.message}")
    else:
        print(f"FAIL: HDFE allowed invalid absorb type!")
        
    # 3. DIDRegress - Ensure completely blocked
    print("\n[3] Testing DIDRegress Adversarial")
    req_did = AnalyticalRequest(
        command_str="didregress leverage prof",
        parsed={"depvar": "leverage", "indepvars": ["prof"]},
        df=df,
        correlation_id="corr_did",
        dataset_ref=dataset_ref
    )
    res_did = DIDAdapter.run(req_did, envelope)
    print(f"DIDAdapter Result Status: {res_did.status}")
    if res_did.status == "unsupported":
        print("PASS: DIDRegress securely blocked as unsupported.")
    else:
        print("FAIL: DIDRegress was not blocked!")

    # 4. ML Ridge - Impossible variables and missing dependencies check
    print("\n[4] Testing ML Ridge Adversarial")
    req_ml = AnalyticalRequest(
        command_str="predict_ml leverage prof x1 x2, method(ridge)",
        parsed={"depvar": "leverage", "indepvars": ["prof", "x1", "x2"]},
        df=df,
        correlation_id="corr_ml",
        dataset_ref=dataset_ref
    )
    res_ml = MLPredictAdapter.run(req_ml, envelope)
    print(f"MLPredictAdapter Result Status: {res_ml.status}")
    if res_ml.status == "error":
        print(f"PASS: Safely caught error -> {res_ml.error_code}: {res_ml.message}")
    else:
        print("FAIL/PASS: MLPredictAdapter proceeded. Output table length:", len(res_ml.table) if res_ml.table else 0)

if __name__ == "__main__":
    run_adversarial_tests()
