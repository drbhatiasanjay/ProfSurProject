from pathlib import Path


def test_ai_assistant_has_explicit_provenance_renderer_gate():
    source = Path("pages/19_ai_assistant.py").read_text(encoding="utf-8")
    assert "render_artifact_provenance" in source
    assert "artifact_provenance" in source
    assert "capability_id" in source
    assert "descriptive_summary" in source


def test_provenance_renderer_rejects_incomplete_records():
    from components.research_artifact_renderer import render_artifact_provenance

    # Streamlit is not started in this unit test; incomplete input must be a no-op.
    render_artifact_provenance({"analysis_run_id": "run-1"}, key_prefix="test")


def test_descriptive_metadata_requires_explicit_source_fingerprint(monkeypatch):
    import components.research_artifact_renderer as renderer

    calls = []
    monkeypatch.setattr(renderer.st, "caption", lambda value: calls.append(value))
    renderer.render_descriptive_metadata({"n_obs": 3}, key_prefix="missing")
    assert calls == []
    renderer.render_descriptive_metadata(
        {"source_fingerprint": "abc", "n_obs": 3, "n_firms": 2},
        key_prefix="present",
    )
    assert any("COMPUTED" in value for value in calls)
    assert any("abc" in value for value in calls)
