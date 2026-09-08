"""
models/analytical_router.py — Wave 2 single public routing entry point.

Pages call route() instead of execute_stata_command() directly.
All _handle_* functions in stata_engine.py remain untouched.

Flow:
  raw command → AnalyticalRequest → CommandRegistry → CapabilityRegistry
             → handler → CapabilityResult + AnalysisRunEnvelope
"""
from __future__ import annotations

import logging
import inspect
import time
import uuid
from dataclasses import replace

from models.analytical_contracts import (
    AnalyticalError,
    AnalyticalRequest,
    CapabilityResult,
    VisualizationSpec,
)
from models.analysis_run_envelope import AnalysisRunEnvelope
from models.command_registry import CommandEntry, resolve_capability
from models.capability_registry import get_handler
from models.stata_engine import resolve_panel_variable
from models.stata_validation import validate_stata_command

logger = logging.getLogger("profsur.router")


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

def route(request: AnalyticalRequest) -> CapabilityResult:
    """
    Route an AnalyticalRequest through the capability layer and return a
    CapabilityResult. Never raises — all errors are captured into the result.

    PRD §4.4 vertical slice:
      request → validation → execution → result → error behavior
    """
    t0 = time.perf_counter()
    run_id = str(uuid.uuid4())
    validated_parsed, validation_failure = validate_stata_command(
        request.parsed, request.df, resolve_panel_variable
    )
    request = replace(request, parsed=validated_parsed)
    cmd = validated_parsed.get("cmd", "")
    entry: CommandEntry | None = resolve_capability(cmd)

    if validation_failure:
        result = CapabilityResult(
            status="error",
            error_code=validation_failure["error_code"],
            message=validation_failure["message"],
            ascii_output=validation_failure["ascii_output"],
            metadata=validation_failure.get("metadata"),
            correlation_id=request.correlation_id,
            run_id=run_id,
        )
        envelope = AnalysisRunEnvelope.create(
            run_id=run_id,
            correlation_id=request.correlation_id,
            dataset_fingerprint=request.dataset_ref.fingerprint,
            normalized_command=cmd,
            capability=entry.capability if entry else "NONE",
        ).complete("error")
        _log_route_event(
            request, result, entry, envelope,
            round((time.perf_counter() - t0) * 1000, 2),
        )
        return result

    # ── Unrecognized command ──────────────────────────────────────────────
    if entry is None:
        result = CapabilityResult(
            status="unsupported",
            error_code="UNRECOGNIZED_COMMAND",
            message=f"Unrecognized command: {cmd!r}. "
                    f"Type 'help' to see supported commands.",
            correlation_id=request.correlation_id,
            run_id=run_id,
        )
        envelope = AnalysisRunEnvelope.create(
            run_id=run_id,
            correlation_id=request.correlation_id,
            dataset_fingerprint=request.dataset_ref.fingerprint,
            normalized_command=cmd,
            capability="NONE",
        ).complete("unsupported")
        _log_route_event(request, result, entry, envelope,
                         round((time.perf_counter() - t0) * 1000, 2))
        return result

    # ── Resolve handler ───────────────────────────────────────────────────
    handler = get_handler(entry.capability, cmd=cmd)
    if handler is None:
        result = CapabilityResult(
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
        ).complete("unsupported")
        _log_route_event(request, result, entry, envelope,
                         round((time.perf_counter() - t0) * 1000, 2))
        return result

    # ── Execute ───────────────────────────────────────────────────────────
    envelope = AnalysisRunEnvelope.create(
        run_id=run_id,
        correlation_id=request.correlation_id,
        dataset_fingerprint=request.dataset_ref.fingerprint,
        normalized_command=cmd,
        capability=entry.capability,
    )

    try:
        handler_args = (request.parsed, request.df)
        if request.session_context is not None and len(inspect.signature(handler).parameters) >= 3:
            handler_args += (request.session_context,)
        raw: dict = handler(*handler_args)

        # Wrap raw chart dict in VisualizationSpec if present
        chart_raw = raw.pop("chart", None)
        chart: VisualizationSpec | None = None
        if isinstance(chart_raw, dict) and chart_raw:
            chart_type = chart_raw.pop("type", cmd)
            chart = VisualizationSpec(
                chart_type=chart_type,
                data=chart_raw,
                provenance_run_id=run_id,
            )

        result_status = str(raw.get("status", "success")).lower()
        if result_status not in {"success", "error", "unsupported", "partial"}:
            result_status = "error"
        if entry.status == "CANDIDATE" and result_status == "success":
            result_status = "unsupported"
        elif entry.status == "IMPLEMENTED_UNVERIFIED" and result_status == "success":
            result_status = "partial"

        result = CapabilityResult(
            status=result_status,
            ascii_output=raw.get("ascii_output", ""),
            chart=chart,
            table=raw.get("table"),
            message=raw.get("message", ""),
            error_code=raw.get("error_code", ""),
            metadata=raw.get("metadata"),
            correlation_id=request.correlation_id,
            run_id=run_id,
            engine="stata_engine_v1",
            engine_version="1.0",
        )
        envelope = envelope.complete(result.status)  # type: ignore[arg-type]

    except AnalyticalError as exc:
        result = CapabilityResult(
            status="error",
            error_code=exc.code,
            message=exc.user_message,
            correlation_id=request.correlation_id,
            run_id=run_id,
        )
        envelope = envelope.complete("error")

    except Exception as exc:  # noqa: BLE001
        result = CapabilityResult(
            status="error",
            error_code="INTERNAL_ERROR",
            message=f"Internal error: {exc}",
            correlation_id=request.correlation_id,
            run_id=run_id,
        )
        envelope = envelope.complete("error")

    _log_route_event(request, result, entry, envelope,
                     round((time.perf_counter() - t0) * 1000, 2))
    return result


# ---------------------------------------------------------------------------
# Structured logging (PRD §8)
# ---------------------------------------------------------------------------

def _log_route_event(
    req: AnalyticalRequest,
    res: CapabilityResult,
    entry: CommandEntry | None,
    envelope: AnalysisRunEnvelope,
    duration_ms: float,
) -> None:
    """Emit one structured log record per route() call (PRD §8 fields)."""
    logger.info(
        "route",
        extra={
            "correlation_id":      req.correlation_id,
            "analysis_run_id":     envelope.run_id,
            "session_id":          req.session_id,
            "command_family":      req.parsed.get("cmd", ""),
            "capability_id":       entry.capability if entry else "NONE",
            "capability_status":   entry.status if entry else "UNRECOGNIZED",
            "engine_id":           "stata_engine_v1",
            "engine_version":      "1.0",
            "dataset_fingerprint": req.dataset_ref.fingerprint,
            "status":              res.status,
            "error_code":          res.error_code or None,
            "duration_ms":         duration_ms,
        },
    )
