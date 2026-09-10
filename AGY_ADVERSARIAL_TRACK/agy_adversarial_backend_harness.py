import sys
import json
import os

class MissingModuleMock:
    def __getattr__(self, name):
        raise ModuleNotFoundError("No module named 'sklearn'")

sys.modules['sklearn'] = MissingModuleMock()

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

def run_backend_harness():
    results = []
    print("Running Scenario A-03...")
    
    try:
        from models.ml_adapters import MLPredictAdapter
        from models.analytical_contracts import AnalyticalRequest
        from models.analysis_run_envelope import AnalysisRunEnvelope
        import pandas as pd
        
        req = AnalyticalRequest(
            command_type="predict_ml",
            df=pd.DataFrame({"leverage": [1], "prof": [2], "tang": [3], "company_code": [1]}),
            parsed={"depvar": "leverage", "indepvars": ["prof", "tang"]}
        )
        env = AnalysisRunEnvelope(user_id="test")
        
        res = MLPredictAdapter.run(req, env)
        if res and res.status == "error" and "scikit-learn not installed" in res.message:
            print("[PASS] A-03: Gracefully handled missing dependency.")
            results.append({"scenario": "A-03", "status": "PASS", "details": "Gracefully handled missing sklearn."})
        else:
            print("[FAIL] A-03: Did not fail with expected error message.")
            results.append({"scenario": "A-03", "status": "FAIL", "details": f"Got unexpected result: {res}"})
    except Exception as e:
        if isinstance(e, ModuleNotFoundError) and 'sklearn' in str(e):
             print("[FAIL] A-03: Uncaught ModuleNotFoundError raised to top level! V-05 Violation.")
             results.append({"scenario": "A-03", "status": "FAIL", "details": "Uncaught ModuleNotFoundError raised to top level! V-05 Violation."})
        else:
             print(f"[ERROR] A-03: Unexpected exception: {e}")
             results.append({"scenario": "A-03", "status": "ERROR", "details": str(e)})

    out_dir = os.path.join(os.path.dirname(__file__), "agy_defects")
    os.makedirs(out_dir, exist_ok=True)
    with open(os.path.join(out_dir, "agy_backend_report.json"), "w") as f:
        json.dump(results, f, indent=4)

if __name__ == "__main__":
    run_backend_harness()
