import pytest

from models.research_artifacts import (
    ArtifactContractError,
    ArtifactProvenance,
    NarrativeArtifact,
    VisualizationArtifact,
    build_narrative_artifact,
    build_visualization_artifact,
)


def _provenance():
    return ArtifactProvenance(
        analysis_run_id="run-1",
        dataset_fingerprint="sha256:data",
        sample_fingerprint="sha256:sample",
        result_fingerprint="sha256:result",
        capability_status="IMPLEMENTED_UNVERIFIED",
    )


def test_visualization_is_provenance_bound_and_immutable():
    artifact = build_visualization_artifact(
        title="Leverage by stage",
        categories=["Growth", "Maturity"],
        series=[{"name": "mean", "values": [0.2, 0.3]}],
        provenance=_provenance(),
    )
    assert isinstance(artifact, VisualizationArtifact)
    assert artifact.provenance.analysis_run_id == "run-1"
    with pytest.raises((AttributeError, TypeError)):
        artifact.title = "changed"


def test_visualization_rejects_misaligned_series():
    with pytest.raises(ArtifactContractError, match="series length"):
        build_visualization_artifact(
            title="Bad",
            categories=["A", "B"],
            series=[{"name": "mean", "values": [1.0]}],
            provenance=_provenance(),
        )


def test_narrative_keeps_limitations_and_does_not_promote_status():
    artifact = build_narrative_artifact(
        title="Research note",
        text="The computed association is shown for review.",
        claims=["Computed association"],
        limitations=["Methodology review remains open."],
        provenance=_provenance(),
    )
    assert isinstance(artifact, NarrativeArtifact)
    assert artifact.provenance.capability_status == "IMPLEMENTED_UNVERIFIED"
    assert "Methodology review remains open." in artifact.limitations


def test_narrative_rejects_unbound_or_empty_claims():
    with pytest.raises(ArtifactContractError):
        build_narrative_artifact(
            title="Unbound",
            text="text",
            claims=[],
            limitations=[],
            provenance=_provenance(),
        )


def test_unvalidated_narrative_rejects_causal_language():
    with pytest.raises(ArtifactContractError, match="causal language"):
        build_narrative_artifact(
            title="Unsafe claim",
            text="Profitability causes lower leverage.",
            claims=["causal effect"],
            limitations=["Independent review remains open."],
            provenance=_provenance(),
        )
