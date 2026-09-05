"""Provider-neutral contracts for CFO decision-support responses.

The LLM may propose an answer, but these contracts are validated outside the
provider adapter so Gemini, Anthropic, Ollama, and future providers share the
same evidence and visualization rules.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Literal


EvidenceKind = Literal["observed", "derived", "modeled", "assumption", "interpretation"]


@dataclass(frozen=True)
class EvidenceItem:
    """A claim or input with an explicit evidence classification."""

    label: str
    value: Any
    kind: EvidenceKind
    source: str = ""
    confidence: Literal["high", "medium", "low"] | None = None


@dataclass(frozen=True)
class ScenarioCase:
    """A named CFO case with transparent, user-editable assumptions."""

    name: str
    assumptions: dict[str, Any] = field(default_factory=dict)
    outputs: dict[str, Any] = field(default_factory=dict)
    limitations: tuple[str, ...] = ()


@dataclass(frozen=True)
class DecisionBrief:
    """Canonical response envelope used by all LLM providers."""

    analysis_id: str = ""
    status: Literal["success", "partial", "failed"] = "success"
    decision: str = ""
    answer: str = ""
    table: list[dict[str, Any]] = field(default_factory=list)
    chart: dict[str, Any] | None = None
    evidence: tuple[EvidenceItem, ...] = ()
    scenarios: tuple[ScenarioCase, ...] = ()
    assumptions: tuple[str, ...] = ()
    limitations: tuple[str, ...] = ()
    validation: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Serialize without requiring a provider-specific model library."""
        return asdict(self)


def validate_chart_table(
    table: list[dict[str, Any]] | None,
    chart: dict[str, Any] | None,
) -> dict[str, Any]:
    """Validate the invariants that make a chart trustworthy in the UI."""
    errors: list[str] = []
    warnings: list[str] = []
    table = table or []

    if chart is None:
        return {
            "valid": True,
            "chart_present": False,
            "errors": errors,
            "warnings": warnings,
        }

    categories = chart.get("categories")
    series = chart.get("series")
    if not isinstance(categories, list) or len(categories) < 2:
        errors.append("chart requires at least two categories")
    if not isinstance(series, list) or not series:
        errors.append("chart requires at least one series")

    if isinstance(categories, list) and isinstance(series, list):
        for index, item in enumerate(series):
            values = item.get("values") if isinstance(item, dict) else None
            if not isinstance(values, list):
                errors.append(f"series {index} has no values list")
            elif len(values) != len(categories):
                errors.append(
                    f"series {index} length {len(values)} does not match categories {len(categories)}"
                )

    if table and isinstance(categories, list) and len(table) != len(categories):
        warnings.append("supporting table row count differs from chart category count")

    return {
        "valid": not errors,
        "chart_present": True,
        "errors": errors,
        "warnings": warnings,
    }


def build_decision_brief(
    *,
    answer: str,
    table: list[dict[str, Any]] | None = None,
    chart: dict[str, Any] | None = None,
    user_query: str = "",
    limitations: list[str] | None = None,
) -> DecisionBrief:
    """Create the common envelope after provider output is normalized."""
    validation = validate_chart_table(table, chart)
    effective_chart = chart if validation["valid"] else None
    effective_limitations = list(limitations or [])
    if validation["errors"]:
        effective_limitations.append("Visualization was withheld because its data contract failed validation.")
    return DecisionBrief(
        decision=user_query.strip(),
        answer=str(answer or ""),
        table=list(table or []),
        chart=effective_chart,
        limitations=tuple(effective_limitations),
        validation=validation,
    )

