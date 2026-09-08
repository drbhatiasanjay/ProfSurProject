"""
models/command_registry.py — Wave 2 declarative command registry.

Replaces the flat if/elif dispatch chain in execute_stata_command().
Each entry carries a capability name and PRD §9 capability status.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Literal


CapabilityStatus = Literal[
    "CANDIDATE",
    "IMPLEMENTED_UNVERIFIED",
    "VALIDATED",
    "UNSUPPORTED",
    "NATIVE_RUNTIME_ONLY",
    "COMMUNITY_COMPATIBILITY",
]


@dataclass(frozen=True)
class CommandEntry:
    """Metadata for a single recognized command."""
    capability: str
    status: CapabilityStatus


# ---------------------------------------------------------------------------
# Canonical command → capability mapping (PRD §9 status model)
# ---------------------------------------------------------------------------
COMMAND_REGISTRY: dict[str, CommandEntry] = {
    # ── Descriptive statistics ───────────────────────────────────────────
    "summarize":    CommandEntry("descriptive",         "VALIDATED"),
    "sum":          CommandEntry("descriptive",         "VALIDATED"),
    "tabstat":      CommandEntry("descriptive",         "VALIDATED"),
    # ── Correlation ──────────────────────────────────────────────────────
    "pwcorr":       CommandEntry("correlation",         "VALIDATED"),
    "correlate":    CommandEntry("correlation",         "VALIDATED"),
    "corr":         CommandEntry("correlation",         "VALIDATED"),
    # ── OLS regression ───────────────────────────────────────────────────
    "regress":      CommandEntry("ols",                 "VALIDATED"),
    "reg":          CommandEntry("ols",                 "VALIDATED"),
    # ── Panel FE / RE ────────────────────────────────────────────────────
    "xtreg":        CommandEntry("panel_fe_re",         "VALIDATED"),
    "xtset":        CommandEntry("panel_declare",       "VALIDATED"),
    # ── Specification tests ───────────────────────────────────────────────
    "hausman":      CommandEntry("specification_test",  "VALIDATED"),
    # ── Post-estimation ───────────────────────────────────────────────────
    "estat":        CommandEntry("post_estimation",     "VALIDATED"),
    "estimates":    CommandEntry("stored_estimates",    "VALIDATED"),
    "estimate":     CommandEntry("stored_estimates",    "VALIDATED"),
    # ── Table export ─────────────────────────────────────────────────────
    "esttab":       CommandEntry("table_export",        "VALIDATED"),
    # ── Visualization ─────────────────────────────────────────────────────
    "coefplot":     CommandEntry("visualization",       "VALIDATED"),
    "scatter":      CommandEntry("visualization",       "VALIDATED"),
    "histogram":    CommandEntry("visualization",       "VALIDATED"),
    "hist":         CommandEntry("visualization",       "VALIDATED"),
    "twoway":       CommandEntry("visualization",       "VALIDATED"),
    "box":          CommandEntry("visualization",       "VALIDATED"),
    "hbox":         CommandEntry("visualization",       "VALIDATED"),
    # ── File export ───────────────────────────────────────────────────────
    "export":       CommandEntry("file_export",         "VALIDATED"),
    # ── PhD figure ────────────────────────────────────────────────────────
    "thesis":       CommandEntry("phd_figure",          "VALIDATED"),
    # ── Frequency tables ─────────────────────────────────────────────────
    "tabulate":     CommandEntry("frequency",           "VALIDATED"),
    "tab":          CommandEntry("frequency",           "VALIDATED"),
    # ── Diagnostics ──────────────────────────────────────────────────────
    "xttest0":      CommandEntry("diagnostic",          "VALIDATED"),
    "xtserial":     CommandEntry("diagnostic",          "VALIDATED"),
    # ── Marginal effects ─────────────────────────────────────────────────
    "margins":      CommandEntry("marginal_effects",    "VALIDATED"),
    # ── Lifecycle graph (community compat) ───────────────────────────────
    "lgraph":       CommandEntry("lifecycle_chart",     "COMMUNITY_COMPATIBILITY"),
    # ── IV estimation ─────────────────────────────────────────────────────
    "ivregress":    CommandEntry("iv_estimation",       "IMPLEMENTED_UNVERIFIED"),
    # ── Wald test ─────────────────────────────────────────────────────────
    "test":         CommandEntry("wald_test",           "VALIDATED"),
    # ── Prediction ────────────────────────────────────────────────────────
    "predict":      CommandEntry("prediction",          "VALIDATED"),
    # ── Data transform (winsorize) ────────────────────────────────────────
    "winsor2":      CommandEntry("data_transform",      "IMPLEMENTED_UNVERIFIED"),
    # ── Wave 4: Exploratory commands ──────────────────────────────────────
    "describe":     CommandEntry("describe",            "VALIDATED"),
    "des":          CommandEntry("describe",            "VALIDATED"),
    "d":            CommandEntry("describe",            "VALIDATED"),
    "codebook":     CommandEntry("codebook",            "VALIDATED"),
    "cb":           CommandEntry("codebook",            "VALIDATED"),
    "count":        CommandEntry("count",               "VALIDATED"),
    "mean":         CommandEntry("mean",                "VALIDATED"),
    "proportion":   CommandEntry("proportion",          "VALIDATED"),
    "prop":         CommandEntry("proportion",          "VALIDATED"),
    # ── Wave 4: Longitudinal panel commands ───────────────────────────────
    "xtdescribe":   CommandEntry("xtdescribe",          "VALIDATED"),
    "xtdes":        CommandEntry("xtdescribe",          "VALIDATED"),
    "xtsum":        CommandEntry("xtsum",               "VALIDATED"),
    "xttab":        CommandEntry("xttab",               "VALIDATED"),
    "xtline":       CommandEntry("xtline",              "VALIDATED"),
    # ── Wave 4: Post-estimation & inference ──────────────────────────────
    "testparm":     CommandEntry("wald_test",           "VALIDATED"),
    "lincom":       CommandEntry("linear_combination",  "VALIDATED"),
    "nlcom":        CommandEntry("nonlinear_combination", "IMPLEMENTED_UNVERIFIED"),
    # ── Wave 5: Advanced Econometrics & Scenarios ─────────────────────────
    # NOTE: 'ivregress' is kept as Wave 1 validated mapping (iv_estimation).
    # Wave 5 IV is registered under 'iv_candidate' to avoid displacing the
    # validated handler. Use 'hdfe' or 'didregress' for Wave 5 causal work.
    "gmm":          CommandEntry("gmm",                 "IMPLEMENTED_UNVERIFIED"),
    "hdfe":         CommandEntry("hdfe",                "IMPLEMENTED_UNVERIFIED"),
    "didregress":   CommandEntry("did",                 "CANDIDATE"),
    "scenario":     CommandEntry("scenario",            "CANDIDATE"),
    "predict_ml":   CommandEntry("ml_predict",          "IMPLEMENTED_UNVERIFIED"),
}


def resolve_capability(cmd: str) -> CommandEntry | None:
    """Return CommandEntry for cmd, or None if unrecognized."""
    return COMMAND_REGISTRY.get(cmd)
