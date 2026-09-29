import sys
from types import SimpleNamespace

import pytest
from streamlit.errors import StreamlitSecretNotFoundError

from models.runtime_config import get_gemini_api_key
from scripts.patch_demo_runtime import patch_chat, patch_scorecard


class MissingSecrets:
    def get(self, *args):
        raise StreamlitSecretNotFoundError("No secrets found")


@pytest.fixture
def config(monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
    fake = SimpleNamespace(session_state={}, secrets=MissingSecrets())
    monkeypatch.setitem(sys.modules, "streamlit", fake)
    return fake


def test_missing_secrets_is_unconfigured_not_a_crash(config):
    assert get_gemini_api_key() is None


@pytest.mark.parametrize("name", ["GEMINI_API_KEY", "GOOGLE_API_KEY"])
def test_environment_does_not_touch_missing_secrets(config, monkeypatch, name):
    monkeypatch.setenv(name, "test-only-key")
    assert get_gemini_api_key() == "test-only-key"


def test_session_key_works_without_secrets_file(config):
    config.session_state["gemini_api_key"] = "session-test-key"
    assert get_gemini_api_key() == "session-test-key"


@pytest.mark.parametrize("secrets", [
    {"GEMINI_API_KEY": "configured-test-key"},
    {"GOOGLE_API_KEY": "configured-test-key"},
    {"credentials": {"gemini_api_key": "configured-test-key"}},
])
def test_configured_aliases(config, secrets):
    config.secrets = secrets
    assert get_gemini_api_key() == "configured-test-key"


@pytest.mark.parametrize("coefficient,expected", [
    ({"coef": -2.5, "p": 0.01}, True), ({"coef": 2.5}, False),
    ({"coef": 0.0}, False), ({}, False), (-2.5, True), (None, False),
])
def test_scorecard_accepts_engine_coefficient_records(coefficient, expected):
    source = "_prof_sign = v\n_tang_sign = v\nsupported = _prof_sign is not None and _prof_sign < 0\n"
    scope = {"v": coefficient}
    exec(patch_scorecard(source), scope)
    assert scope["supported"] is expected


def test_deployment_patches_refuse_unrecognized_code():
    with pytest.raises(ValueError):
        patch_scorecard("unrelated = 1\n")
    with pytest.raises(ValueError):
        patch_chat("import os\nunrelated = 1\n")


def test_cfo_ladder_all_5_diverse_companies():
    """Verify that get_cfo_scenario_ladder produces 4 complete tiers for all 5 target companies."""
    targets = [
        (100632, "Infosys Ltd.", "Computer software"),
        (248136, "Tata Steel Ltd.", "Steel"),
        (34162, "Bharti Airtel Ltd.", "Telecommunication services"),
        (395047, "Interglobe Aviation Ltd.", "Air transport services"),
        (239726, "Sun Pharmaceutical Inds. Ltd.", "Drugs & pharmaceuticals"),
    ]
    # Execute function from file
    import re
    with open("pages/19_ai_assistant.py", "r", encoding="utf-8") as f:
        src = f.read()
    match = re.search(r"(def get_cfo_scenario_ladder\(.*?\n(?:    .*\n)+)", src)
    assert match is not None, "get_cfo_scenario_ladder must be defined"
    scope = {}
    exec(match.group(1), scope)
    func = scope["get_cfo_scenario_ladder"]

    for code, name, ind in targets:
        ladder = func(code, name, ind)
        assert len(ladder) == 4, f"Must have 4 tiers for {name}"
        expected_tiers = ["Tier 1: Simple", "Tier 2: Medium", "Tier 3: Complex", "Tier 4: Drill Down"]
        for idx, item in enumerate(ladder):
            assert item["tier"] == expected_tiers[idx]
            assert "badge" in item and item["badge"]
            assert "title" in item and item["title"]
            assert "desc" in item and item["desc"]
            assert "query" in item and len(item["query"]) > 30


def test_executive_badges_html_formatter():
    """Verify that _format_executive_badges_html converts badges to styled callouts."""
    import re
    with open("pages/19_ai_assistant.py", "r", encoding="utf-8") as f:
        src = f.read()
    match = re.search(r"(def _format_executive_badges_html\(.*?)(?=\ndef )", src, re.DOTALL)
    assert match is not None
    scope = {"re": re}
    exec(match.group(1), scope)
    fmt = scope["_format_executive_badges_html"]

    input_text = "🟢 STATUS: RESILIENT BALANCE SHEET — FINANCIAL FLEXIBILITY PRESERVED\nKey analysis follows."
    formatted = fmt(input_text)
    assert '<div style="background:rgba(34, 197, 94, 0.12)' in formatted
    assert 'border-left:4px solid #22c55e' in formatted
    assert 'STATUS: RESILIENT BALANCE SHEET' in formatted


def test_split_supporting_tables_inlines_decision_tables():
    """Verify that decision tables remain in the prose stream instead of being hidden."""
    import re
    with open("pages/19_ai_assistant.py", "r", encoding="utf-8") as f:
        src = f.read()
    match = re.search(r"(def _split_supporting_tables\(.*?\n(?:    .*\n)+)", src)
    assert match is not None
    scope = {"re": re}
    exec(match.group(1), scope)
    split_func = scope["_split_supporting_tables"]

    decision_table = (
        "| Financial Lever / Metric | Company Position | Industry Benchmark | Prudent Band | Strategic CFO Action |\n"
        "| :--- | :--- | :--- | :--- | :--- |\n"
        "| Debt Ratio | 4.2% | 12.5% | 0-15% | Maintain equity buffer |\n"
        "| ICR Coverage | 42.0x | 8.5x | > 3.0x | Covenant headroom secure |"
    )
    prose, tables = split_func(decision_table)
    assert "Debt Ratio" in prose
    assert len(tables) == 0, "Compact decision table should remain inline in prose"

