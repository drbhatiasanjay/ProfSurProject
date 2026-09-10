import os
import sys
import pandas as pd

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, PROJECT_ROOT)

from models.analytical_contracts import AnalyticalRequest, fingerprint_df
from models.analytical_router import route
from models.stata_engine import ModelResultContext

def run_state_bleed_tests():
    print("--- End-to-End State Bleed & Context Isolation Tests ---")
    
    df = pd.DataFrame({
        "leverage": [0.5, 0.4, 0.6, 0.3, 0.7],
        "prof": [0.1, 0.2, 0.15, 0.05, 0.25],
    })
    dataset_ref = fingerprint_df(df)
    
    # 1. Test session binding isolation
    print("\n[1] Testing ModelResultContext Cross-Session Bleed")
    
    # Create context and bind to Session A
    session_A = "session_A_123"
    ctx = ModelResultContext()
    
    req_A = AnalyticalRequest(
        command_str="regress leverage prof",
        parsed={"cmd": "regress", "depvar": "leverage", "indepvars": ["prof"]},
        df=df,
        session_id=session_A,
        session_context=ctx,
        correlation_id="corr_A",
        dataset_ref=dataset_ref
    )
    
    # Run in Session A (should succeed and bind)
    res_A = route(req_A)
    print(f"Session A execution status: {res_A.status}")
    
    # Now try to reuse the exact same context in Session B
    session_B = "session_B_456"
    req_B = AnalyticalRequest(
        command_str="predict p1",
        parsed={"cmd": "predict", "newvar": "p1"},
        df=df,
        session_id=session_B,
        session_context=ctx, # Maliciously passing Session A's context
        correlation_id="corr_B",
        dataset_ref=dataset_ref
    )
    
    res_B = route(req_B)
    print(f"Session B execution status: {res_B.status}")
    if res_B.status == "error" and res_B.error_code == "DATA_SCOPE_ERROR":
        print(f"PASS: Safely caught cross-session bleed -> {res_B.message}")
    else:
        print("FAIL: Context bleed was allowed!")

    # 2. Test Descriptive -> Predictive Bleed (Phase 13 to Wave 5 interference)
    print("\n[2] Testing Descriptive to Causal State Bleed")
    
    # A descriptive request should not populate estimation state
    ctx_clean = ModelResultContext()
    req_desc = AnalyticalRequest(
        command_str="summarize leverage",
        parsed={"cmd": "summarize", "varlist": ["leverage"]},
        df=df,
        session_id="session_C",
        session_context=ctx_clean,
        correlation_id="corr_C",
        dataset_ref=dataset_ref
    )
    
    res_desc = route(req_desc)
    print(f"Descriptive execution status: {res_desc.status}")
    
    # Immediately try to predict (should fail because no model was estimated, shouldn't hallucinate)
    req_pred = AnalyticalRequest(
        command_str="predict p_desc",
        parsed={"cmd": "predict", "newvar": "p_desc"},
        df=df,
        session_id="session_C",
        session_context=ctx_clean,
        correlation_id="corr_C_2",
        dataset_ref=dataset_ref
    )
    
    res_pred = route(req_pred)
    print(f"Predict execution status: {res_pred.status}")
    if res_pred.status == "error":
        print(f"PASS: Predict correctly failed (no hallucinated state) -> {res_pred.message}")
    else:
        print("FAIL: Predict succeeded without a prior estimation model!")

if __name__ == "__main__":
    run_state_bleed_tests()
