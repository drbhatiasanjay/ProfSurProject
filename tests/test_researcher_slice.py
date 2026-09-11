import pytest

from models.researcher_slice import (
    ResearcherSliceError,
    ResearcherSlice,
    create_researcher_slice,
    apply_research_action,
)


def test_researcher_slice_is_read_only_and_workspace_bound():
    journey = create_researcher_slice(
        workspace_id="public-panel",
        role="researcher",
        analysis_run_id="run-1",
        artifact_ids=["viz-1", "note-1"],
        limitations=["Advanced methods remain unvalidated."],
    )
    assert isinstance(journey, ResearcherSlice)
    reproduced = apply_research_action(journey, "reproduce")
    assert reproduced.action == "reproduce"
    assert reproduced.workspace_id == journey.workspace_id
    assert reproduced.analysis_run_id == journey.analysis_run_id
    with pytest.raises((AttributeError, TypeError)):
        journey.role = "admin"


def test_researcher_slice_allows_challenge_without_promoting_status():
    journey = create_researcher_slice(
        workspace_id="public-panel",
        role="admin",
        analysis_run_id="run-1",
        artifact_ids=["viz-1"],
        limitations=[],
    )
    challenged = apply_research_action(journey, "challenge")
    assert challenged.action == "challenge"
    assert challenged.release_status == "NOT_VALIDATED"


def test_researcher_slice_rejects_unauthorized_roles_and_mutations():
    with pytest.raises(ResearcherSliceError, match="role"):
        create_researcher_slice(
            workspace_id="public-panel",
            role="viewer",
            analysis_run_id="run-1",
            artifact_ids=["viz-1"],
            limitations=[],
        )
    journey = create_researcher_slice(
        workspace_id="public-panel",
        role="researcher",
        analysis_run_id="run-1",
        artifact_ids=["viz-1"],
        limitations=[],
    )
    with pytest.raises(ResearcherSliceError, match="action"):
        apply_research_action(journey, "edit_source")


def test_researcher_slice_rejects_blank_artifact_ids():
    with pytest.raises(ResearcherSliceError, match="artifacts"):
        create_researcher_slice(
            workspace_id="public-panel",
            role="researcher",
            analysis_run_id="run-1",
            artifact_ids=["", "  "],
            limitations=[],
        )
