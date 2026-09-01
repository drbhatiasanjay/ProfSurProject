"""Unit tests for stream_gemini_agent in models/llm_adapters.py."""
from unittest.mock import MagicMock, patch
import pytest
from models.llm_adapters import (
    build_chart_spec_from_rows,
    extract_chart_tool_spec,
    normalize_assistant_chunk,
    normalize_assistant_response,
    should_generate_chart,
    select_chart_rows_for_query,
    stream_gemini_agent,
)


class TestStreamGeminiAgent:
    def test_chart_fallback_builds_from_query_rows(self):
        spec = build_chart_spec_from_rows(
            [{"year": 2020, "profitability": 0.10}, {"year": 2021, "profitability": 0.20}],
            "show a trend chart",
        )
        assert spec["chart_type"] == "line"
        assert spec["categories"] == ["2020", "2021"]
        assert spec["series"][0]["values"] == [0.1, 0.2]

    def test_chart_fallback_preserves_multiple_numeric_series(self):
        spec = build_chart_spec_from_rows(
            [{"year": 2020, "leverage": 20, "profitability": 0.1},
             {"year": 2021, "leverage": 22, "profitability": 0.2}],
            "plot leverage and profitability trend",
        )
        assert len(spec["series"]) == 2

    def test_chart_fallback_supports_horizontal_bar(self):
        spec = build_chart_spec_from_rows(
            [{"industry_group": "A", "leverage": 20}, {"industry_group": "B", "leverage": 30}],
            "horizontal bar chart",
        )
        assert spec["orientation"] == "h"

    def test_chart_tool_response_accepts_direct_json_string(self):
        spec = {"chart_type": "line", "categories": ["2020", "2021"],
                "series": [{"name": "ROA", "values": [0.1, 0.2]}]}
        payload = {"status": "success", "chart_spec": spec}
        assert extract_chart_tool_spec(payload)["chart_type"] == "line"
        assert extract_chart_tool_spec(__import__("json").dumps(payload)) == spec

    def test_chart_tool_response_accepts_nested_result(self):
        spec = {"chart_type": "bar", "categories": ["A", "B"],
                "series": [{"name": "Leverage", "values": [10, 20]}]}
        payload = {"result": __import__("json").dumps({"status": "success", "chart_spec": spec})}
        assert extract_chart_tool_spec(payload) == spec

    def test_shared_text_parser_accepts_compact_nested_json(self):
        from models.agent_tools import extract_chat_chart_spec
        response = 'Analysis first. {"chart_spec":{"chart_type":"bar","title":"Leverage","categories":["A","B"],"series":[{"name":"Leverage","values":[10,20]}]}}'
        spec, cleaned = extract_chat_chart_spec(response)
        assert spec["chart_type"] == "bar"
        assert "chart_spec" not in cleaned

    def test_table_fallback_preserves_multiple_series(self):
        from models.agent_tools import extract_table_chart_spec
        spec = extract_table_chart_spec(
            "| Year | Leverage | Profitability |\n|---|---:|---:|\n| 2020 | 20 | 0.1 |\n| 2021 | 22 | 0.2 |",
            "show a line chart",
        )
        assert len(spec["series"]) == 2

    def test_table_fallback_accepts_tab_separated_industry_table(self):
        from models.agent_tools import extract_table_chart_spec
        text = (
            "Industry Group\tAverage Profitability (ROA)\n"
            "Lubricants, etc.\t0.439\n"
            "Readymade garments\t0.331\n"
            "Media-broadcasting\t0.283\n"
        )
        spec = extract_table_chart_spec(text, "show a bar chart")
        assert spec["chart_type"] == "bar"
        assert spec["categories"] == ["Lubricants, etc.", "Readymade garments", "Media-broadcasting"]
        assert spec["series"][0]["values"] == [0.439, 0.331, 0.283]

    def test_provider_neutral_response_contract(self):
        text, chart = normalize_assistant_chunk({"type": "chart", "spec": {"chart_type": "line"}})
        assert text == "" and chart["chart_type"] == "line"
        result = normalize_assistant_response(
            "| Year | ROA |\n|---|---:|\n| 2020 | 0.1 |\n| 2021 | 0.2 |",
            user_query="show a trend chart",
            chart_requested=True,
        )
        assert len(result["table"]) == 2
        assert result["chart_spec"]["chart_type"] == "line"

    def test_grouped_variation_question_requests_chart_fallback(self):
        assert should_generate_chart("How does profitability vary by industry group?")

    def test_chart_rows_selects_current_dataset_from_accumulated_history(self):
        datasets = [
            [{"life_stage": "Growth", "avg_profitability": 0.14}],
            [{"industry_group": "Software", "avg_profitability": 0.22}],
        ]
        rows = select_chart_rows_for_query(datasets, "How does profitability vary by industry group?")
        assert rows[0]["industry_group"] == "Software"

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
