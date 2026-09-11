"""Immutable, provenance-bound artifacts for the Wave 7 research workspace."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, Mapping


class ArtifactContractError(ValueError):
    """Raised when a visualization or narrative cannot be trusted."""


_CAUSAL_LANGUAGE = re.compile(
    r"\b(cause|causes|causal|causally|impact|impacts|effect|effects|proves|leads? to)\b",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class ArtifactProvenance:
    analysis_run_id: str
    dataset_fingerprint: str
    sample_fingerprint: str
    result_fingerprint: str
    capability_status: str

    def __post_init__(self) -> None:
        if not all(
            value.strip()
            for value in (
                self.analysis_run_id,
                self.dataset_fingerprint,
                self.sample_fingerprint,
                self.result_fingerprint,
                self.capability_status,
            )
        ):
            raise ArtifactContractError("complete provenance is required")


@dataclass(frozen=True)
class VisualizationArtifact:
    title: str
    categories: tuple[str, ...]
    series: tuple[tuple[str, tuple[float | int | None, ...]], ...]
    provenance: ArtifactProvenance


@dataclass(frozen=True)
class NarrativeArtifact:
    title: str
    text: str
    claims: tuple[str, ...]
    limitations: tuple[str, ...]
    provenance: ArtifactProvenance


def build_visualization_artifact(
    *,
    title: str,
    categories: list[str] | tuple[str, ...],
    series: list[Mapping[str, Any]] | tuple[Mapping[str, Any], ...],
    provenance: ArtifactProvenance,
) -> VisualizationArtifact:
    if not title.strip() or len(categories) < 2 or not series:
        raise ArtifactContractError("title, two categories, and one series are required")
    normalized: list[tuple[str, tuple[float | int | None, ...]]] = []
    for item in series:
        name = str(item.get("name", "")).strip()
        values = item.get("values")
        if not name or not isinstance(values, (list, tuple)):
            raise ArtifactContractError("each series requires a name and values")
        if len(values) != len(categories):
            raise ArtifactContractError("series length must match categories")
        normalized.append((name, tuple(values)))
    return VisualizationArtifact(
        title=title.strip(),
        categories=tuple(str(value) for value in categories),
        series=tuple(normalized),
        provenance=provenance,
    )


def build_narrative_artifact(
    *,
    title: str,
    text: str,
    claims: list[str] | tuple[str, ...],
    limitations: list[str] | tuple[str, ...],
    provenance: ArtifactProvenance,
) -> NarrativeArtifact:
    if not title.strip() or not text.strip() or not claims:
        raise ArtifactContractError("title, text, and at least one claim are required")
    if provenance.capability_status != "VALIDATED":
        combined = " ".join((text, *claims))
        if _CAUSAL_LANGUAGE.search(combined):
            raise ArtifactContractError(
                "causal language requires a VALIDATED capability and independent evidence"
            )
        if not limitations:
            raise ArtifactContractError("limitations are required for unvalidated narratives")
    return NarrativeArtifact(
        title=title.strip(),
        text=text.strip(),
        claims=tuple(str(claim).strip() for claim in claims if str(claim).strip()),
        limitations=tuple(str(item).strip() for item in limitations if str(item).strip()),
        provenance=provenance,
    )
