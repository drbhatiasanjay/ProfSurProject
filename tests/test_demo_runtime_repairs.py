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
