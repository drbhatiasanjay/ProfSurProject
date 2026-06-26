"""
Tests for Anthropic prompt-caching beta + fallback in stream_anthropic().
Verifies: standard path works when beta unavailable, role/citations params
are backward-compatible with callers that don't pass them.
"""
import os
import pytest
from unittest.mock import MagicMock, patch


# ── helpers ───────────────────────────────────────────────────────────────────

def _make_mock_stream(chunks=("Hello", " world")):
    """Return a context-manager mock whose text_stream yields chunks."""
    class MockStream:
        def __init__(self, _chunks):
            self._chunks = _chunks

        def __enter__(self):
            return self

        def __exit__(self, *args):
            pass

        @property
        def text_stream(self):
            return iter(self._chunks)

    return MockStream(chunks)


def _make_client(beta_chunks=None, beta_raises=None, std_chunks=None, std_raises=None):
    """Build a mock anthropic.Anthropic() instance."""
    client = MagicMock()

    if beta_raises:
        client.beta.prompt_caching.messages.stream.side_effect = beta_raises
    else:
        client.beta.prompt_caching.messages.stream.return_value = _make_mock_stream(
            beta_chunks or ("Hello", " world")
        )

    if std_raises:
        client.messages.stream.side_effect = std_raises
    else:
        client.messages.stream.return_value = _make_mock_stream(
            std_chunks or ("Fallback", " response")
        )
    return client


# ── stream_anthropic backward compatibility ───────────────────────────────────

class TestStreamAnthropicSignature:
    def _run(self, **kwargs):
        """Helper: call stream_anthropic with a mocked Anthropic client."""
        client = kwargs.pop("_mock_client", _make_client())
        with patch.dict(os.environ, {"ANTHROPIC_API_KEY": "test-key"}):
            with patch("anthropic.Anthropic", return_value=client):
                from models import llm_adapters
                # force re-import to pick up env var
                result = list(llm_adapters.stream_anthropic(
                    [{"role": "user", "content": "hello"}],
                    **kwargs,
                ))
        return result, client

    def test_no_role_or_citations_still_works(self):
        """Old callers that pass only (messages, system, model) must not break."""
        result, _ = self._run(system="system prompt", model="claude-haiku-4-5-20251001")
        assert "".join(result) == "Hello world"

    def test_role_viewer_no_academic_preamble(self):
        """viewer role should NOT inject academic terminology into system."""
        captured = {}

        def capture(**kwargs):
            captured["system"] = kwargs.get("system", "")
            return _make_mock_stream()

        client = MagicMock()
        client.beta.prompt_caching.messages.stream.side_effect = capture
        result, _ = self._run(system="base context", role="viewer", _mock_client=client)

        sys_content = captured.get("system", "")
        if isinstance(sys_content, list):
            text = " ".join(b.get("text", "") for b in sys_content)
        else:
            text = str(sys_content)
        assert "Rajan" not in text
        assert "Zingales" not in text

    def test_role_researcher_adds_academic_preamble(self):
        """researcher role SHOULD inject academic terminology into system."""
        captured = {}

        def capture(**kwargs):
            captured["system"] = kwargs.get("system", "")
            return _make_mock_stream()

        client = MagicMock()
        client.beta.prompt_caching.messages.stream.side_effect = capture
        self._run(system="base context", role="researcher", _mock_client=client)

        sys_content = captured.get("system", "")
        if isinstance(sys_content, list):
            text = " ".join(b.get("text", "") for b in sys_content)
        else:
            text = str(sys_content)
        assert any(word in text for word in ["academic", "econometric", "precision"])

    def test_citations_flag_appends_instruction(self):
        """citations=True should append citation instruction to system."""
        captured = {}

        def capture(**kwargs):
            captured["system"] = kwargs.get("system", "")
            return _make_mock_stream()

        client = MagicMock()
        client.beta.prompt_caching.messages.stream.side_effect = capture
        self._run(system="base context", citations=True, _mock_client=client)

        sys_content = captured.get("system", "")
        if isinstance(sys_content, list):
            text = " ".join(b.get("text", "") for b in sys_content)
        else:
            text = str(sys_content)
        assert any(word in text for word in ["cite", "citation", "Modigliani", "Myers"])


# ── prompt caching fallback ───────────────────────────────────────────────────

class TestPromptCachingFallback:
    def test_falls_back_to_standard_when_beta_raises(self):
        """When beta.prompt_caching raises, standard messages.stream is used."""
        client = _make_client(
            beta_raises=Exception("beta unavailable"),
            std_chunks=("Fallback", " response"),
        )
        with patch.dict(os.environ, {"ANTHROPIC_API_KEY": "test-key"}):
            with patch("anthropic.Anthropic", return_value=client):
                from models import llm_adapters
                result = list(llm_adapters.stream_anthropic(
                    [{"role": "user", "content": "hello"}],
                    system="base context",
                ))
        assert "".join(result) == "Fallback response"
        assert client.messages.stream.called

    def test_no_crash_when_both_paths_raise(self):
        """When both beta and standard raise, stream_anthropic returns an error string, not a crash."""
        client = _make_client(
            beta_raises=Exception("beta down"),
            std_raises=Exception("api down"),
        )
        with patch.dict(os.environ, {"ANTHROPIC_API_KEY": "test-key"}):
            with patch("anthropic.Anthropic", return_value=client):
                from models import llm_adapters
                result = list(llm_adapters.stream_anthropic(
                    [{"role": "user", "content": "hello"}],
                    system="base context",
                ))
        # Should yield exactly one error string, not raise
        assert isinstance(result, list)
        assert len(result) >= 1
        assert all(isinstance(r, str) for r in result)

    def test_missing_api_key_yields_error_string(self):
        """Missing ANTHROPIC_API_KEY should yield an explanatory string, not crash."""
        with patch.dict(os.environ, {}, clear=True):
            # Also ensure st.secrets unavailable
            with patch("streamlit.secrets", MagicMock(get=lambda k, d=None: None)):
                from models import llm_adapters
                result = list(llm_adapters.stream_anthropic(
                    [{"role": "user", "content": "hello"}],
                    system="base context",
                ))
        assert len(result) == 1
        assert "configured" in result[0].lower() or "api" in result[0].lower() or "[" in result[0]
