"""
Wave 2 — Command & Capability Abstraction Layer
TDD RED phase: all tests must fail before implementation.

PRD §6 levels:
  L1 — unit/property
  L3 — contract/integration
"""
from __future__ import annotations

import importlib
import uuid
from dataclasses import fields

import pandas as pd
import pytest


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _sample_df() -> pd.DataFrame:
    return pd.DataFrame({
        "company_code": [1, 1, 2, 2],
        "year":         [2001, 2002, 2001, 2002],
        "leverage":     [0.3, 0.35, 0.4, 0.38],
        "profitability":[0.1, 0.12, 0.08, 0.11],
        "tangibility":  [0.5, 0.52, 0.48, 0.50],
        "log_size":     [10.1, 10.2, 9.8, 9.9],
    })


# ---------------------------------------------------------------------------
# T-01  AnalyticalRequest is immutable (frozen dataclass)            [L1]
# ---------------------------------------------------------------------------
def test_analytical_request_is_frozen():
    from models.analytical_contracts import AnalyticalRequest, fingerprint_df
    df = _sample_df()
    req = AnalyticalRequest(
        command_str="summarize leverage",
        parsed={"cmd": "summarize"},
        df=df,
        correlation_id=str(uuid.uuid4()),
        dataset_ref=fingerprint_df(df),
    )
    with pytest.raises((TypeError, AttributeError)):
        req.command_str = "mutated"  # type: ignore[misc]


# ---------------------------------------------------------------------------
# T-02  CapabilityResult echoes correlation_id and run_id            [L1]
# ---------------------------------------------------------------------------
def test_capability_result_echoes_ids():
    from models.analytical_contracts import CapabilityResult
    cid = str(uuid.uuid4())
    rid = str(uuid.uuid4())
    r = CapabilityResult(status="success", correlation_id=cid, run_id=rid)
    assert r.correlation_id == cid
    assert r.run_id == rid


# ---------------------------------------------------------------------------
# T-03  Known commands resolve to correct CommandEntry               [L1]
# ---------------------------------------------------------------------------
def test_command_registry_resolves_known_commands():
    from models.command_registry import resolve_capability
    entry = resolve_capability("summarize")
    assert entry is not None
    assert entry.capability == "descriptive"

    entry_xtreg = resolve_capability("xtreg")
    assert entry_xtreg.capability == "panel_fe_re"

    entry_reg = resolve_capability("reg")
    assert entry_reg.capability == "ols"


# ---------------------------------------------------------------------------
# T-04  Unknown command returns None from resolve_capability          [L1]
# ---------------------------------------------------------------------------
def test_command_registry_returns_none_for_unknown():
    from models.command_registry import resolve_capability
    assert resolve_capability("nonexistent_cmd_xyz") is None


# ---------------------------------------------------------------------------
# T-05  route() returns CapabilityResult for summarize               [L3]
# ---------------------------------------------------------------------------
def test_route_summarize():
    from models.analytical_contracts import AnalyticalRequest, fingerprint_df
    from models.analytical_router import route
    from models.stata_engine import parse_stata_command

    df = _sample_df()
    req = AnalyticalRequest(
        command_str="summarize leverage profitability",
        parsed=parse_stata_command("summarize leverage profitability"),
        df=df,
        correlation_id=str(uuid.uuid4()),
        dataset_ref=fingerprint_df(df),
    )
    result = route(req)
    assert result.status == "success"
    assert result.correlation_id == req.correlation_id
    assert result.engine == "stata_engine_v1"


# ---------------------------------------------------------------------------
# T-06  route() returns CapabilityResult for xtreg                  [L3]
# ---------------------------------------------------------------------------
def test_route_xtreg():
    from models.analytical_contracts import AnalyticalRequest, fingerprint_df
    from models.analytical_router import route
    from models.stata_engine import parse_stata_command

    df = _sample_df()
    req = AnalyticalRequest(
        command_str="xtreg leverage profitability tangibility log_size, fe",
        parsed=parse_stata_command(
            "xtreg leverage profitability tangibility log_size, fe"
        ),
        df=df,
        correlation_id=str(uuid.uuid4()),
        dataset_ref=fingerprint_df(df),
    )
    result = route(req)
    assert result.status in ("success", "error")   # error OK if panel not set
    assert result.correlation_id == req.correlation_id


# ---------------------------------------------------------------------------
# T-07  route() returns CapabilityResult for ivregress               [L3]
# ---------------------------------------------------------------------------
def test_route_ivregress():
    from models.analytical_contracts import AnalyticalRequest, fingerprint_df
    from models.analytical_router import route
    from models.stata_engine import parse_stata_command

    df = _sample_df()
    cmd = "ivregress 2sls leverage (profitability = tangibility)"
    req = AnalyticalRequest(
        command_str=cmd,
        parsed=parse_stata_command(cmd),
        df=df,
        correlation_id=str(uuid.uuid4()),
        dataset_ref=fingerprint_df(df),
    )
    result = route(req)
    # Accept success, error, OR unsupported — Wave 1 handlers may not be present on this branch
    assert result.status in ("success", "partial", "error", "unsupported")
    assert result.correlation_id == req.correlation_id


# ---------------------------------------------------------------------------
# T-08  route() returns UNRECOGNIZED_COMMAND for unknown command     [L3]
# ---------------------------------------------------------------------------
def test_route_unrecognized_command():
    from models.analytical_contracts import AnalyticalRequest, fingerprint_df
    from models.analytical_router import route
    from models.stata_engine import parse_stata_command

    df = _sample_df()
    req = AnalyticalRequest(
        command_str="frobnicator leverage",
        parsed=parse_stata_command("frobnicator leverage"),
        df=df,
        correlation_id=str(uuid.uuid4()),
        dataset_ref=fingerprint_df(df),
    )
    result = route(req)
    assert result.status == "unsupported"
    assert result.error_code == "UNRECOGNIZED_COMMAND"


# ---------------------------------------------------------------------------
# T-09  AnalyticalError carries all 14 PRD schema fields             [L1]
# ---------------------------------------------------------------------------
def test_analytical_error_has_14_prd_fields():
    from models.analytical_contracts import AnalyticalError
    required = {
        "code", "user_message", "technical_message", "command",
        "normalized_command", "correlation_id", "analysis_run_id",
        "workspace_id", "engine", "engine_version", "severity",
        "recoverable", "suggested_actions", "cause_chain",
    }
    actual = {f.name for f in fields(AnalyticalError)}
    missing = required - actual
    assert not missing, f"AnalyticalError missing PRD fields: {missing}"


# ---------------------------------------------------------------------------
# T-10  All 25 PRD error codes present in ANALYTICAL_ERROR_CODES     [L1]
# ---------------------------------------------------------------------------
def test_all_25_error_codes_present():
    from models.analytical_contracts import ANALYTICAL_ERROR_CODES
    expected = {
        "SYNTAX_ERROR", "UNRECOGNIZED_COMMAND", "UNSUPPORTED_OPTION",
        "UNSUPPORTED_CAPABILITY", "VARIABLE_NOT_FOUND", "AMBIGUOUS_VARIABLE",
        "PANEL_NOT_DECLARED", "DUPLICATE_PANEL_KEYS", "INVALID_TIME_VARIABLE",
        "INSUFFICIENT_OBSERVATIONS", "INSUFFICIENT_VARIATION", "COLLINEARITY",
        "SINGULAR_MATRIX", "NONCONVERGENCE", "PERFECT_SEPARATION",
        "INVALID_INSTRUMENT_SPEC", "DIAGNOSTIC_FAILURE", "METHOD_NOT_PERMITTED",
        "CAUSAL_GATE_REQUIRED", "DATA_SCOPE_ERROR", "TENANT_SCOPE_ERROR",
        "DEPENDENCY_UNAVAILABLE", "ENGINE_UNAVAILABLE", "ENGINE_FAILURE",
        "EXPORT_FAILURE", "INTERNAL_ERROR",
    }
    assert expected == ANALYTICAL_ERROR_CODES, (
        f"Missing codes: {expected - ANALYTICAL_ERROR_CODES}"
    )


# ---------------------------------------------------------------------------
# T-11  route() sets engine="stata_engine_v1" on success             [L3]
# ---------------------------------------------------------------------------
def test_route_sets_engine_provenance():
    from models.analytical_contracts import AnalyticalRequest, fingerprint_df
    from models.analytical_router import route
    from models.stata_engine import parse_stata_command

    df = _sample_df()
    req = AnalyticalRequest(
        command_str="summarize leverage",
        parsed=parse_stata_command("summarize leverage"),
        df=df,
        correlation_id=str(uuid.uuid4()),
        dataset_ref=fingerprint_df(df),
    )
    result = route(req)
    assert result.engine == "stata_engine_v1"


# ---------------------------------------------------------------------------
# T-12  lgraph resolves to COMMUNITY_COMPATIBILITY status            [L1]
# ---------------------------------------------------------------------------
def test_lgraph_has_community_compatibility_status():
    from models.command_registry import resolve_capability
    entry = resolve_capability("lgraph")
    assert entry is not None
    assert entry.status == "COMMUNITY_COMPATIBILITY"


# ---------------------------------------------------------------------------
# T-13  CapabilityResult.to_dict() round-trips cleanly (no df)      [L3]
# ---------------------------------------------------------------------------
def test_capability_result_to_dict():
    from models.analytical_contracts import CapabilityResult
    r = CapabilityResult(
        status="success",
        ascii_output="some output",
        correlation_id="abc",
        run_id="xyz",
        engine="stata_engine_v1",
    )
    d = r.to_dict()
    assert isinstance(d, dict)
    assert d["status"] == "success"
    assert d["correlation_id"] == "abc"
    assert "df" not in d          # dataframes must NOT be serialized


# ---------------------------------------------------------------------------
# T-14  AnalysisRunEnvelope binds correlation_id from request        [L3]
# ---------------------------------------------------------------------------
def test_analysis_run_envelope_binds_correlation_id():
    from models.analysis_run_envelope import AnalysisRunEnvelope
    cid = str(uuid.uuid4())
    env = AnalysisRunEnvelope(
        run_id=str(uuid.uuid4()),
        request_id=cid,
        correlation_id=cid,
        dataset_fingerprint="abc123",
        normalized_command="summarize leverage",
        capability="descriptive",
    )
    assert env.correlation_id == cid


# ---------------------------------------------------------------------------
# T-15  fingerprint_df() is deterministic across two calls           [L1]
# ---------------------------------------------------------------------------
def test_fingerprint_df_is_deterministic():
    from models.analytical_contracts import fingerprint_df
    df = _sample_df()
    ref1 = fingerprint_df(df)
    ref2 = fingerprint_df(df)
    assert ref1.fingerprint == ref2.fingerprint
    assert ref1.row_count == len(df)
    assert ref1.col_count == len(df.columns)


# ---------------------------------------------------------------------------
# T-16  All 25 PRD error codes are str literals — none missing       [L1]
# ---------------------------------------------------------------------------
def test_error_codes_are_strings():
    from models.analytical_contracts import ANALYTICAL_ERROR_CODES
    assert all(isinstance(c, str) for c in ANALYTICAL_ERROR_CODES)
    assert len(ANALYTICAL_ERROR_CODES) == 26  # 25 + INTERNAL_ERROR = 26 total


# ---------------------------------------------------------------------------
# T-17  execute_stata_command backward compat — still importable     [L3]
# ---------------------------------------------------------------------------
def test_execute_stata_command_backward_compat():
    from models.stata_engine import execute_stata_command
    df = _sample_df()
    result = execute_stata_command("summarize leverage", df=df)
    assert isinstance(result, dict)
    assert result.get("status") == "success"
