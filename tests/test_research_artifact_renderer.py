from pathlib import Path


def test_ai_assistant_has_explicit_provenance_renderer_gate():
    source = Path("pages/19_ai_assistant.py").read_text(encoding="utf-8")
    assert "render_artifact_provenance" in source
    assert "artifact_provenance" in source


def test_provenance_renderer_rejects_incomplete_records():
    from components.research_artifact_renderer import render_artifact_provenance

    # Streamlit is not started in this unit test; incomplete input must be a no-op.
    render_artifact_provenance({"analysis_run_id": "run-1"}, key_prefix="test")
