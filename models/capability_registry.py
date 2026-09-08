"""
models/capability_registry.py — Wave 2 capability → handler mapping.

Maps capability names to the existing _handle_* functions in stata_engine.py.
stata_engine.py is NOT modified. This file is the sole bridge.
"""
from __future__ import annotations

from typing import Callable

import pandas as pd

from models.stata_engine import (
    _handle_summarize,
    _handle_tabstat,
    _handle_pwcorr,
    _handle_regress,
    _handle_xtreg,
    _handle_xtset,
    _handle_lgraph,
    _handle_hausman,
    _handle_estat_vif,
    _handle_coefplot,
    _handle_scatter,
    _handle_histogram,
    _handle_twoway,
    _handle_esttab,
    _handle_tabulate,
    _handle_graph_box,
    _handle_xttest0,
    _handle_xtserial,
    _handle_margins,
    _handle_export,
    _handle_thesis,
    # Wave 4 handlers
    _handle_describe,
    _handle_codebook,
    _handle_count,
    _handle_mean,
    _handle_proportion,
    _handle_xtdescribe,
    _handle_xtsum,
    _handle_xttab,
    _handle_xtline,
    _handle_estat_ic,
    _handle_estat_summarize,
    _handle_testparm,
    _handle_lincom,
)

# Wave 1 handlers (may not exist on older branches — import gracefully)
try:
    from models.stata_engine import (
        _handle_ivregress,
        _handle_test,
        _handle_predict,
        _handle_winsor2,
    )
    _HAS_WAVE1_HANDLERS = True
except ImportError:
    _HAS_WAVE1_HANDLERS = False

from models.stata_expansion_handlers import (
    _handle_gmm,
    _handle_ivregress as _w5_handle_ivregress,
    _handle_hdfe,
    _handle_didregress,
    _handle_scenario,
    _handle_ml_predict,
)


CapabilityHandler = Callable[[dict, pd.DataFrame], dict]


def _estimates_handler(parsed: dict, df: pd.DataFrame) -> dict:
    """Inline handler for stored estimates — logic lifted from execute_stata_command."""
    from models.stata_engine import _STORED_ESTIMATES, _LAST_ESTIMATE  # type: ignore[attr-defined]
    if parsed.get("indepvars") and parsed["indepvars"][0] == "store":
        name = parsed["indepvars"][1] if len(parsed["indepvars"]) > 1 else "m1"
        if _LAST_ESTIMATE:
            _STORED_ESTIMATES[name] = _LAST_ESTIMATE
            return {
                "status": "success",
                "message": f"Saved current model as '{name}'",
                "ascii_output": f"(estimates stored as {name})",
            }
        return {
            "status": "error",
            "message": "No estimation results found to store.",
            "ascii_output": "r(301); last estimates not found",
        }
    from models.stata_engine import _STORED_ESTIMATES  # type: ignore[attr-defined]
    return {"status": "success", "ascii_output": f"Stored estimates: {list(_STORED_ESTIMATES.keys())}"}


def _estat_dispatcher(parsed: dict, df: pd.DataFrame) -> dict:
    """Dispatch estat subcommands (vif, ic, summarize)."""
    indep = parsed.get("indepvars", [])
    opts = parsed.get("options", [])
    if "vif" in indep or "vif" in opts:
        return _handle_estat_vif(parsed, df)
    if "ic" in indep or "ic" in opts:
        return _handle_estat_ic(parsed, df)
    if "summarize" in indep or "summarize" in opts:
        return _handle_estat_summarize(parsed, df)
    return {
        "status": "error",
        "message": f"Unsupported estat subcommand: {indep}",
        "ascii_output": "r(198); invalid estat subcommand",
    }


# ---------------------------------------------------------------------------
# Capability → handler map
# ---------------------------------------------------------------------------
CAPABILITY_REGISTRY: dict[str, CapabilityHandler] = {
    "descriptive":          _handle_summarize,
    "correlation":          _handle_pwcorr,
    "ols":                  _handle_regress,
    "panel_fe_re":          _handle_xtreg,
    "panel_declare":        _handle_xtset,
    "specification_test":   _handle_hausman,
    "post_estimation":      _estat_dispatcher,
    "stored_estimates":     _estimates_handler,
    "table_export":         _handle_esttab,
    "visualization":        _handle_coefplot,
    "file_export":          _handle_export,
    "phd_figure":           _handle_thesis,
    "frequency":            _handle_tabulate,
    "diagnostic":           _handle_xttest0,
    "marginal_effects":     _handle_margins,
    "lifecycle_chart":      _handle_lgraph,
    # Wave 4 capabilities
    "describe":             _handle_describe,
    "codebook":             _handle_codebook,
    "count":                _handle_count,
    "mean":                 _handle_mean,
    "proportion":           _handle_proportion,
    "xtdescribe":           _handle_xtdescribe,
    "xtsum":                _handle_xtsum,
    "xttab":                _handle_xttab,
    "xtline":               _handle_xtline,
    "linear_combination":   _handle_lincom,
    # Wave 5 capabilities
    "gmm":                  _handle_gmm,
    "iv":                   _w5_handle_ivregress,
    "hdfe":                 _handle_hdfe,
    "did":                  _handle_didregress,
    "scenario":             _handle_scenario,
    "ml_predict":           _handle_ml_predict,
}

# Add visualization sub-handlers so router can pick by cmd
_VIZ_HANDLERS: dict[str, CapabilityHandler] = {
    "coefplot":   _handle_coefplot,
    "scatter":    _handle_scatter,
    "histogram":  _handle_histogram,
    "hist":       _handle_histogram,
    "twoway":     _handle_twoway,
    "box":        _handle_graph_box,
    "hbox":       _handle_graph_box,
}

_DIAG_HANDLERS: dict[str, CapabilityHandler] = {
    "xttest0":  _handle_xttest0,
    "xtserial": _handle_xtserial,
}

_WALD_HANDLERS: dict[str, CapabilityHandler] = {
    "test":     _handle_test if _HAS_WAVE1_HANDLERS else _handle_testparm,
    "testparm": _handle_testparm,
}

if _HAS_WAVE1_HANDLERS:
    CAPABILITY_REGISTRY["iv_estimation"] = _handle_ivregress  # type: ignore[assignment]
    CAPABILITY_REGISTRY["wald_test"]     = _handle_test       # type: ignore[assignment]
    CAPABILITY_REGISTRY["prediction"]    = _handle_predict    # type: ignore[assignment]
    CAPABILITY_REGISTRY["data_transform"] = _handle_winsor2   # type: ignore[assignment]
else:
    CAPABILITY_REGISTRY["wald_test"]     = _handle_testparm


def get_handler(capability: str, cmd: str = "") -> CapabilityHandler | None:
    """Return handler for capability (and optionally narrow by cmd for multi-handler caps)."""
    if capability == "visualization" and cmd in _VIZ_HANDLERS:
        return _VIZ_HANDLERS[cmd]
    if capability == "diagnostic" and cmd in _DIAG_HANDLERS:
        return _DIAG_HANDLERS[cmd]
    if capability == "wald_test" and cmd in _WALD_HANDLERS:
        return _WALD_HANDLERS[cmd]
    if capability == "post_estimation":
        return _estat_dispatcher
    if capability == "stored_estimates":
        return _estimates_handler
    return CAPABILITY_REGISTRY.get(capability)
