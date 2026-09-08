"""Pure parsing helpers for structured Stata command options."""

from __future__ import annotations

import re


def parse_interventions_spec(value) -> tuple[dict[str, float], str | None]:
    if isinstance(value, dict):
        items = value.items()
    elif isinstance(value, str) and value.strip():
        parts = [part for part in re.split(r"\s*,\s*|\s+", value.strip()) if part]
        parsed = []
        for part in parts:
            if "=" not in part:
                return {}, f"invalid intervention expression: {part}"
            name, raw_value = part.split("=", 1)
            parsed.append((name.strip(), raw_value.strip()))
        items = parsed
    else:
        return {}, "scenario requires at least one variable=value intervention"

    interventions: dict[str, float] = {}
    for name, raw_value in items:
        if not re.fullmatch(r"[A-Za-z_]\w*", str(name)):
            return {}, f"invalid intervention variable: {name}"
        try:
            interventions[str(name)] = float(raw_value)
        except (TypeError, ValueError):
            return {}, f"intervention for {name} must be numeric"
    return interventions, None


def parse_absorb_spec(value) -> tuple[list[str], str | None]:
    if isinstance(value, (list, tuple)):
        variables = [str(item).strip() for item in value if str(item).strip()]
    elif isinstance(value, str):
        variables = [item for item in re.split(r"[\s,]+", value.strip()) if item]
    else:
        return [], "absorb() requires one or more variable names"
    if not variables:
        return [], "absorb() requires one or more variable names"
    for variable in variables:
        if not re.fullmatch(r"[A-Za-z_]\w*", variable):
            return [], f"invalid absorb variable: {variable}"
    return variables, None
