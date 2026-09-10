"""
experimental_analytical_router.py — Phase 15 Experimental Router

Implements:
1. Thread-safe Computation LRU Cache (Fingerprint + Command)
2. Cache Immutability (Deep Copy)
3. Idempotent Command Guard
4. Comprehensive JIT Compiler Pre-Warming
"""
import time
import uuid
import inspect
import threading
import copy
from functools import lru_cache
from dataclasses import replace
import pandas as pd
import numpy as np

from models.analytical_contracts import (
    AnalyticalError,
    AnalyticalRequest,
    CapabilityResult,
    VisualizationSpec,
)
from models.analysis_run_envelope import AnalysisRunEnvelope
from models.command_registry import resolve_capability
from models.capability_registry import get_handler
from models.stata_engine import ModelResultContext, resolve_panel_variable
from models.stata_validation import validate_stata_command

# --- 1. Comprehensive JIT Pre-Warming ---
def initialize_engines():
    """Warms up PyFixest to eliminate Numba JIT penalty across all major model families."""
    print("Pre-warming PyFixest JIT compiler (feols, feglm, feiv)...")
    try:
        import pyfixest as pf
        df = pd.DataFrame({
            "y": np.random.randn(20), 
            "x": np.random.randn(20), 
            "z": np.random.randn(20),
            "c": np.random.randint(0,2,20)
        })
        # OLS
        pf.feols("y ~ x | c", data=df)
        # Poisson/GLM
        pf.feglm("c ~ x", data=df, family="poisson")
        # IV
        pf.feols("y ~ 1 | c | x ~ z", data=df)
        print("JIT Pre-warming complete.")
    except ImportError:
        print("PyFixest not installed, skipping JIT warm-up.")
    except Exception as e:
        print(f"JIT warmup encountered an error, continuing: {e}")

# --- 2. Computation LRU Cache ---
_CACHE = {}
_CACHE_LOCK = threading.Lock()

# Whitelist of pure, non-mutating analytical commands
IDEMPOTENT_COMMANDS = {
    "summarize", "regress", "correlate", "pwcorr", "tabulate", "tabstat", 
    "xtreg", "didregress", "ivregress", "gmm", "test", "margins", "predict",
    "estat", "estimates", "hausman"
}

def route(request: AnalyticalRequest) -> CapabilityResult:
    """Public entry point: Wraps the router in the caching layer."""
    t0 = time.perf_counter()
    # Normalize the command and use the deterministic fingerprint
    cmd = request.parsed.get("cmd", request.command_str)
    
    # 🚨 Guard 1: Only cache idempotent commands
    base_cmd = cmd.split()[0] if cmd else ""
    is_idempotent = base_cmd in IDEMPOTENT_COMMANDS
    
    # Standardize dictionary for hashing by sorting keys
    cache_key = f"{request.dataset_ref.fingerprint}::{cmd}::{request.command_str}"
    
    if is_idempotent:
        with _CACHE_LOCK:
            if cache_key in _CACHE:
                # 🚨 Guard 2: Cache Immutability via Deep Copy
                cached_result = copy.deepcopy(_CACHE[cache_key])
                
                # Overwrite dynamic fields so the cached result looks like a fresh run
                cached_result = replace(
                    cached_result, 
                    correlation_id=request.correlation_id,
                    run_id=str(uuid.uuid4())
                )
                #print(f"[CACHE HIT] {cmd}")
                return cached_result
    
    # Cache Miss or Mutating Command
    result = _execute_route(request)
    
    if is_idempotent and result.status in ("success", "partial"):
        with _CACHE_LOCK:
            # Store in cache (limit size to prevent memory leak)
            if len(_CACHE) > 128:
                # Simple FIFO eviction under lock
                _CACHE.pop(next(iter(_CACHE)))
            
            # 🚨 Guard 2: Cache Immutability via Deep Copy
            _CACHE[cache_key] = copy.deepcopy(result)
    
    # Overwrite dynamic fields
    result = replace(
        result, 
        correlation_id=request.correlation_id,
        run_id=str(uuid.uuid4())
    )
    return result

def _execute_route(request: AnalyticalRequest) -> CapabilityResult:
    """Original routing logic without caching overhead."""
    run_id = str(uuid.uuid4())
    validated_parsed, validation_failure = validate_stata_command(
        request.parsed, request.df, resolve_panel_variable
    )
    request = replace(request, parsed=validated_parsed)
    cmd = validated_parsed.get("cmd", "")
    entry = resolve_capability(cmd)

    if validation_failure:
        return CapabilityResult(
            status="error",
            error_code=validation_failure["error_code"],
            message=validation_failure["message"],
            correlation_id=request.correlation_id,
            run_id=run_id,
        )

    if entry is None:
        return CapabilityResult(
            status="unsupported",
            error_code="UNRECOGNIZED_COMMAND",
            message=f"Unrecognized command: {cmd!r}.",
            correlation_id=request.correlation_id,
            run_id=run_id,
        )

    handler = get_handler(entry.capability, cmd=cmd)
    if handler is None:
        return CapabilityResult(
            status="unsupported",
            error_code="UNSUPPORTED_CAPABILITY",
            message=f"Capability '{entry.capability}' has no registered handler.",
            correlation_id=request.correlation_id,
            run_id=run_id,
        )

    envelope = AnalysisRunEnvelope.create(
        run_id=run_id,
        correlation_id=request.correlation_id,
        dataset_fingerprint=request.dataset_ref.fingerprint,
        normalized_command=cmd,
        capability=entry.capability,
    )

    try:
        if isinstance(request.session_context, ModelResultContext):
            request.session_context.bind_session(request.session_id)
        
        handler_args = (request.parsed, request.df)
        if request.session_context is not None and len(inspect.signature(handler).parameters) >= 3:
            handler_args += (request.session_context,)
            
        raw: dict = handler(*handler_args)
        
        result_status = str(raw.get("status", "success")).lower()
        if entry.status == "CANDIDATE" and result_status == "success":
            result_status = "unsupported"
        elif entry.status == "IMPLEMENTED_UNVERIFIED" and result_status == "success":
            result_status = "partial"

        return CapabilityResult(
            status=result_status,
            ascii_output=raw.get("ascii_output", ""),
            table=raw.get("table"),
            message=raw.get("message", ""),
            error_code=raw.get("error_code", ""),
            metadata=raw.get("metadata"),
            correlation_id=request.correlation_id,
            run_id=run_id,
            engine="stata_engine_v1",
            engine_version="1.0",
        )
    except Exception as exc:
        return CapabilityResult(
            status="error",
            error_code="INTERNAL_ERROR",
            message=f"Internal error: {exc}",
            correlation_id=request.correlation_id,
            run_id=run_id,
        )
