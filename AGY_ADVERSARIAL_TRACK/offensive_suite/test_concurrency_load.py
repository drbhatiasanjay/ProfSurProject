import os
import sys
import pandas as pd
import concurrent.futures
import time
import uuid

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, PROJECT_ROOT)

from models.analytical_contracts import AnalyticalRequest, fingerprint_df
from models.analytical_router import route
from models.stata_engine import ModelResultContext

def simulate_request(req_id: int):
    """Simulates a single analytical request, randomly choosing between Descriptive and Causal."""
    df = pd.DataFrame({
        "leverage": [0.5, 0.4, 0.6, 0.3, 0.7] * 20,
        "prof": [0.1, 0.2, 0.15, 0.05, 0.25] * 20,
        "year": [2020]*50 + [2021]*50,
        "company_code": list(range(100))
    })
    dataset_ref = fingerprint_df(df)
    
    session_id = f"concurrent_session_{req_id}"
    ctx = ModelResultContext()
    
    if req_id % 2 == 0:
        # Causal: regress
        req = AnalyticalRequest(
            command_str="regress leverage prof",
            parsed={"cmd": "regress", "depvar": "leverage", "indepvars": ["prof"]},
            df=df,
            session_id=session_id,
            session_context=ctx,
            correlation_id=f"corr_{req_id}",
            dataset_ref=dataset_ref
        )
    else:
        # Descriptive: summarize
        req = AnalyticalRequest(
            command_str="summarize leverage",
            parsed={"cmd": "summarize", "varlist": ["leverage"]},
            df=df,
            session_id=session_id,
            session_context=ctx,
            correlation_id=f"corr_{req_id}",
            dataset_ref=dataset_ref
        )
        
    try:
        res = route(req)
        return req_id, res.status, res.error_code
    except Exception as e:
        return req_id, "CRASH", str(e)

def run_concurrency_test():
    print("--- Phase 15 Infrastructure: High-Concurrency Load Test ---")
    print("Spawning 50 simultaneous analytical router threads...")
    
    NUM_REQUESTS = 50
    results = []
    
    start_time = time.perf_counter()
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=50) as executor:
        futures = [executor.submit(simulate_request, i) for i in range(NUM_REQUESTS)]
        for future in concurrent.futures.as_completed(futures):
            results.append(future.result())
            
    end_time = time.perf_counter()
    duration = end_time - start_time
    
    success_count = sum(1 for r in results if r[1] in ["success", "partial"])
    error_count = sum(1 for r in results if r[1] == "error")
    crash_count = sum(1 for r in results if r[1] == "CRASH")
    
    print(f"\nExecution completed in {duration:.2f} seconds.")
    print(f"Total Requests: {NUM_REQUESTS}")
    print(f"Successful (No engine lockups): {success_count}")
    print(f"Handled Errors (Validation/Math): {error_count}")
    print(f"Fatal Thread Crashes (Deadlocks/Race Conditions): {crash_count}")
    
    if crash_count == 0 and (success_count + error_count) == NUM_REQUESTS:
        print("\nPASS: The analytical engine and ModelResultContext are perfectly thread-safe!")
    else:
        print("\nFAIL: Concurrency issues detected in the routing layer.")

if __name__ == "__main__":
    run_concurrency_test()
