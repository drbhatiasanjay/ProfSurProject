"""Bounded read-only researcher journey for the Wave 8 FDI boundary."""

from __future__ import annotations

from dataclasses import dataclass


class ResearcherSliceError(ValueError):
    """Raised when a researcher action crosses the read-only boundary."""


@dataclass(frozen=True)
class ResearcherSlice:
    workspace_id: str
    role: str
    analysis_run_id: str
    artifact_ids: tuple[str, ...]
    limitations: tuple[str, ...]
    action: str = "view"
    release_status: str = "NOT_VALIDATED"


def create_researcher_slice(
    *,
    workspace_id: str,
    role: str,
    analysis_run_id: str,
    artifact_ids: list[str] | tuple[str, ...],
    limitations: list[str] | tuple[str, ...],
) -> ResearcherSlice:
    if role not in {"admin", "researcher"}:
        raise ResearcherSliceError("role is not authorized for researcher slice")
    normalized_artifacts = tuple(str(item).strip() for item in artifact_ids if str(item).strip())
    if not workspace_id.strip() or not analysis_run_id.strip() or not normalized_artifacts:
        raise ResearcherSliceError("workspace, analysis run, and artifacts are required")
    return ResearcherSlice(
        workspace_id=workspace_id.strip(),
        role=role,
        analysis_run_id=analysis_run_id.strip(),
        artifact_ids=normalized_artifacts,
        limitations=tuple(str(item).strip() for item in limitations if str(item).strip()),
    )


def apply_research_action(slice_: ResearcherSlice, action: str) -> ResearcherSlice:
    if action not in {"challenge", "reproduce"}:
        raise ResearcherSliceError("action is not permitted in read-only slice")
    return ResearcherSlice(
        workspace_id=slice_.workspace_id,
        role=slice_.role,
        analysis_run_id=slice_.analysis_run_id,
        artifact_ids=slice_.artifact_ids,
        limitations=slice_.limitations,
        action=action,
        release_status="NOT_VALIDATED",
    )
