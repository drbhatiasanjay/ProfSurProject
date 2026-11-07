"""Shared numerical, snapshot and result contracts for decision workpapers."""
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
import hashlib
import json
import math
from numbers import Real
from typing import Any

METHOD_VERSION = "decision-depth-1"

@dataclass(frozen=True)
class Result:
    state: str
    data: dict = field(default_factory=dict)
    reasons: tuple[str, ...] = ()
    assumptions: tuple[str, ...] = ()

    def to_dict(self):
        return asdict(self)

def number(value: Any, name: str, minimum=None, maximum=None) -> float:
    if isinstance(value, bool) or not isinstance(value, Real) or not math.isfinite(value):
        raise ValueError(f"{name} must be a finite number")
    value = float(value)
    if minimum is not None and value < minimum:
        raise ValueError(f"{name} must be at least {minimum}")
    if maximum is not None and value > maximum:
        raise ValueError(f"{name} must be at most {maximum}")
    return value

def positive(value, name):
    value = number(value, name)
    if value <= 0:
        raise ValueError(f"{name} must be positive")
    return value

def timestamp(value: str) -> datetime:
    if not isinstance(value, str):
        raise ValueError("Dates must be ISO strings")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError(f"Invalid ISO date: {value}") from exc
    return parsed.replace(tzinfo=timezone.utc) if parsed.tzinfo is None else parsed.astimezone(timezone.utc)

def canonical_json(value) -> str:
    return json.dumps(value, sort_keys=True, ensure_ascii=False, allow_nan=False, separators=(",", ":"))

def context_hash(value) -> str:
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()

def validate_graph(dependencies: dict[str, list[str]]):
    active, visited = set(), set()
    def visit(node):
        if node in active:
            raise ValueError("A snapshot's computational dependencies must be acyclic")
        if node in visited:
            return
        active.add(node)
        for parent in dependencies.get(node, []):
            visit(parent)
        active.remove(node)
        visited.add(node)
    for node in dependencies:
        visit(node)

def affected_nodes(changed: set[str], dependencies: dict[str, list[str]]) -> list[str]:
    validate_graph(dependencies)
    affected = set(changed)
    while True:
        expanded = affected | {node for node, parents in dependencies.items() if affected.intersection(parents)}
        if expanded == affected:
            return sorted(affected)
        affected = expanded
