import os
import sys
import json
import pandas as pd

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

from models.descriptive_analyst import describe_panel, DescriptiveAnalysisError

def run_backend_tests():
    results = []
    out_dir = os.path.join(os.path.dirname(__file__), "agy_defects")
    os.makedirs(out_dir, exist_ok=True)
    
    # Create mock dataset
    df = pd.DataFrame({
        "company_code": [1, 1, 2, 2],
        "leverage": [0.5, 0.6, 0.2, 0.3],
        "prof": [0.1, 0.15, 0.05, 0.08],
        "life_stage": ["Growth", "Growth", "Mature", "Mature"]
    })
    
    # 1. Descriptive averages by lifecycle stage
    try:
        res = describe_panel(df, variables=["leverage", "prof"], group_by="life_stage", run_id="run1")
        if res.provenance["grounding"] == "COMPUTED" and res.provenance["source_fingerprint"]:
            results.append({"scenario": "Grouped Summaries by lifecycle stage", "status": "PASS", "details": "Returned COMPUTED grounding and source fingerprint."})
        else:
            results.append({"scenario": "Grouped Summaries by lifecycle stage", "status": "FAIL", "details": "Missing metadata."})
    except Exception as e:
        results.append({"scenario": "Grouped Summaries by lifecycle stage", "status": "ERROR", "details": str(e)})

    # 2. Invalid-variable refusal
    try:
        res = describe_panel(df, variables=["invalid_var"], run_id="run2")
        results.append({"scenario": "Invalid-variable refusal", "status": "FAIL", "details": "Should have failed."})
    except DescriptiveAnalysisError as e:
        if "VARIABLE_NOT_FOUND" in str(e):
            results.append({"scenario": "Invalid-variable refusal", "status": "PASS", "details": "Failed securely with typed error."})
        else:
            results.append({"scenario": "Invalid-variable refusal", "status": "FAIL", "details": "Wrong error: " + str(e)})
            
    # 3. Empty-sample refusal
    try:
        res = describe_panel(pd.DataFrame(columns=["prof"]), variables=["prof"], run_id="run3")
        results.append({"scenario": "Empty-sample refusal", "status": "FAIL", "details": "Should have failed."})
    except DescriptiveAnalysisError as e:
        if "EMPTY_SAMPLE" in str(e):
            results.append({"scenario": "Empty-sample refusal", "status": "PASS", "details": "Failed securely with typed error."})
        else:
            results.append({"scenario": "Empty-sample refusal", "status": "FAIL", "details": "Wrong error: " + str(e)})

    # 4. Repeated identical query reproducibility
    try:
        res1 = describe_panel(df, variables=["leverage"], run_id="run4")
        res2 = describe_panel(df, variables=["leverage"], run_id="run5")
        if res1.provenance["source_fingerprint"] == res2.provenance["source_fingerprint"]:
            results.append({"scenario": "Repeated identical query reproducibility", "status": "PASS", "details": "Source fingerprint is deterministic."})
        else:
            results.append({"scenario": "Repeated identical query reproducibility", "status": "FAIL", "details": "Fingerprint mismatch."})
    except Exception as e:
        results.append({"scenario": "Repeated identical query reproducibility", "status": "ERROR", "details": str(e)})

    report_path = os.path.join(out_dir, "phase13_backend_report.json")
    with open(report_path, "w") as f:
        json.dump(results, f, indent=4)
        
    for r in results:
        print(f"[{r['status']}] {r['scenario']}: {r['details']}")

if __name__ == "__main__":
    run_backend_tests()
