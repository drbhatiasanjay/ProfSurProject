from pathlib import Path


def test_ai_chat_routes_panel_setup_and_longitudinal_graph_commands_to_stata():
    """Commands already supported by the engine must bypass LLM routing."""
    source = Path("pages/19_ai_assistant.py").read_text(encoding="utf-8")
    registry_start = source.index("_stata_verbs = (")
    registry = source[registry_start:source.index(")", registry_start) + 1]
    assert '"xtset"' in registry
    assert '"lgraph"' in registry
