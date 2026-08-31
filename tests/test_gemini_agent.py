"""Unit tests for stream_gemini_agent in models/llm_adapters.py."""
from unittest.mock import MagicMock, patch
import pytest
from models.llm_adapters import stream_gemini_agent


class TestStreamGeminiAgent:
    def test_missing_api_key_yields_configuration_message(self, monkeypatch):
        monkeypatch.delenv("GEMINI_API_KEY", raising=False)
        monkeypatch.delenv("GOOGLE_API_KEY", raising=False)

        chunks = list(stream_gemini_agent(
            messages=[{"role": "user", "content": "What is leverage?"}],
            system="System prompt",
        ))
        assert len(chunks) == 1
        assert "not configured" in chunks[0]

    @patch("models.llm_adapters.os.environ.get")
    def test_mocked_gemini_agent_text_response(self, mock_env):
        mock_env.return_value = "fake_gemini_api_key"

        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.text = "Grounded response from Gemini."
        mock_response.automatic_function_calling_history = []
        mock_client.models.generate_content.return_value = mock_response

        with patch("google.genai.Client", return_value=mock_client):
            chunks = list(stream_gemini_agent(
                messages=[{"role": "user", "content": "Explain Dickinson 2011 stages."}],
                system="System prompt",
            ))
            assert len(chunks) == 1
            assert chunks[0] == "Grounded response from Gemini."

    @patch("models.llm_adapters.os.environ.get")
    def test_mocked_gemini_agent_tool_calling_loop(self, mock_env):
        mock_env.return_value = "fake_gemini_api_key"

        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.text = "Here are the 2 companies found."

        # Simulate automatic_function_calling_history recorded by the SDK
        mock_part = MagicMock()
        mock_part.function_response = MagicMock()
        mock_part.function_response.name = "query_financial_database"
        mock_part.function_response.response = {"result": '{"status": "success", "count": 2}'}

        mock_item = MagicMock()
        mock_item.parts = [mock_part]
        mock_response.automatic_function_calling_history = [mock_item]

        mock_client.models.generate_content.return_value = mock_response

        with patch("google.genai.Client", return_value=mock_client):
            chunks = list(stream_gemini_agent(
                messages=[{"role": "user", "content": "Show me two companies."}],
                system="System prompt",
            ))
            assert len(chunks) == 1
            assert chunks[0] == "Here are the 2 companies found."
