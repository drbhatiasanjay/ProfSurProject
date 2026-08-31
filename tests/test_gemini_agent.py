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
        mock_chat = MagicMock()
        mock_response = MagicMock()
        mock_response.function_calls = None
        mock_response.text = "Grounded response from Gemini."
        mock_chat.send_message.return_value = mock_response
        mock_client.chats.create.return_value = mock_chat

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
        mock_chat = MagicMock()

        # Step 1: LLM returns a function call for query_financial_database
        mock_call = MagicMock()
        mock_call.name = "query_financial_database"
        mock_call.args = {"sql_query": "SELECT company_name FROM companies LIMIT 2"}

        mock_resp1 = MagicMock()
        mock_resp1.function_calls = [mock_call]
        mock_resp1.text = None

        # Step 2: After function response, LLM returns final text
        mock_resp2 = MagicMock()
        mock_resp2.function_calls = None
        mock_resp2.text = "Here are the 2 companies found."

        mock_chat.send_message.side_effect = [mock_resp1, mock_resp2]
        mock_client.chats.create.return_value = mock_chat

        with patch("google.genai.Client", return_value=mock_client):
            chunks = list(stream_gemini_agent(
                messages=[{"role": "user", "content": "Show me two companies."}],
                system="System prompt",
            ))
            assert len(chunks) == 1
            assert chunks[0] == "Here are the 2 companies found."
