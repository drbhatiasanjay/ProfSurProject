"""End-to-end golden scenario tests for AI Financial Assistant (Features A, B, and E)."""
import pytest
import sqlite3
import pandas as pd

from models.agent_tools import (
    query_financial_database,
    generate_chat_chart,
    render_chat_chart_figure,
    extract_chat_chart_spec,
    query_semantic_ontology,
    get_database_schema_summary,
)
from models.llm_adapters import build_panel_context, build_company_context, classify_query


class TestScenario1NLtoSQL:
    """Golden Scenario 1: Natural-Language-to-SQL retrieval against capital_structure.db."""

    def test_top_leverage_companies_retrieval(self):
        sql = """
            SELECT c.company_name, f.year, f.leverage, f.profitability, f.life_stage
            FROM financials f
            JOIN companies c ON c.company_code = f.company_code
            WHERE f.year = 2022
            ORDER BY f.leverage DESC
            LIMIT 5
        """
        result = query_financial_database(sql, panel_mode="thesis")
        assert result["status"] == "success"
        assert result["count"] == 5
        assert len(result["rows"]) == 5
        assert "company_name" in result["columns"]
        assert "leverage" in result["columns"]
        # Verify deterministic sorted descending order
        levs = [r["leverage"] for r in result["rows"]]
        assert levs == sorted(levs, reverse=True)

    def test_industry_stage_distribution_aggregation(self):
        sql = """
            SELECT life_stage, COUNT(*) as firm_count, AVG(leverage) as avg_lev
            FROM financials
            GROUP BY life_stage
            HAVING firm_count > 10
            ORDER BY avg_lev DESC
        """
        result = query_financial_database(sql, panel_mode="thesis")
        assert result["status"] == "success"
        assert result["count"] >= 3
        stages = [r["life_stage"] for r in result["rows"]]
        assert any(s in ("Startup", "Growth", "Maturity", "Decline", "Decay") for s in stages)


class TestScenario2InChatCharting:
    """Golden Scenario 2: Generating interactive Plotly charts and verifying layout specs."""

    def test_generate_and_render_5yr_trend_chart(self):
        spec_result = generate_chat_chart(
            chart_type="line",
            title="5-Year Leverage Comparison: Asian Paints vs Maturity Stage Median",
            x_axis_label="Fiscal Year",
            y_axis_label="Debt / Total Assets (%)",
            categories=["2020", "2021", "2022", "2023", "2024"],
            series=[
                {"name": "Asian Paints", "values": [12.4, 13.8, 14.1, 15.2, 14.8]},
                {"name": "Maturity Median", "values": [18.5, 18.2, 17.9, 18.1, 18.0]},
            ],
        )
        assert spec_result["status"] == "success"
        spec = spec_result["chart_spec"]

        # Render with light theme
        fig_light = render_chat_chart_figure(spec, theme="light")
        assert len(fig_light.data) == 2
        assert fig_light.layout.title.text == "5-Year Leverage Comparison: Asian Paints vs Maturity Stage Median"
        assert fig_light.layout.xaxis.title.text == "Fiscal Year"
        assert fig_light.layout.yaxis.title.text == "Debt / Total Assets (%)"

        # Render with dark theme
        fig_dark = render_chat_chart_figure(spec, theme="dark")
        assert len(fig_dark.data) == 2
        assert fig_dark.layout.paper_bgcolor is not None

    def test_extract_and_render_roa_profitability_chart(self):
        sample_response = (
            "Here is the average profitability (ROA) across all firms from 2001 to 2025:\n\n"
            "| Year | Mean ROA |\n|---|---|\n| 2001 | 0.161 |\n| 2002 | 0.155 |\n\n"
            "```json\n"
            "{\n"
            '  "chart_type": "line",\n'
            '  "title": "Average Profitability (ROA) 2001-2025",\n'
            '  "x_axis_label": "Fiscal Year",\n'
            '  "y_axis_label": "Mean ROA",\n'
            '  "categories": ["2001", "2002", "2003", "2004", "2005"],\n'
            '  "series": [\n'
            '    {"name": "ROA", "values": [0.161, 0.155, 0.158, 0.166, 0.173]}\n'
            "  ]\n"
            "}\n"
            "```\n\n"
            "Economic Analysis: Profitability peaked in 2006-2007 prior to GFC.\n"
            "FOLLOWUPS_JSON: {\"followups\": [\"Why did ROA dip post-GFC?\", \"How does POT explain this?\", \"Compare to US ROA\"]}"
        )
        spec, cleaned_text = extract_chat_chart_spec(sample_response)
        assert spec is not None
        assert spec["chart_type"] == "line"
        assert spec["title"] == "Average Profitability (ROA) 2001-2025"
        assert len(spec["series"][0]["values"]) == 5
        assert "```json" not in cleaned_text
        assert "Average Profitability (ROA) 2001-2025" not in cleaned_text

        fig = render_chat_chart_figure(spec, theme="light")
        assert len(fig.data) == 1
        assert list(fig.data[0].y) == [0.161, 0.155, 0.158, 0.166, 0.173]


class TestScenario3CrossPageTelemetry:
    """Golden Scenario 3: Telemetry ingestion and grounded context assembly."""

    def test_context_includes_active_filters(self):
        ctx = build_panel_context(panel_mode="thesis")
        assert "## [SOURCE: Theory]" in ctx
        assert "## [SOURCE: Thesis (2001-2024)]" in ctx
        assert "## [SOURCE: OLS Model]" in ctx

    def test_query_classification_routes_correctly(self):
        assert classify_query("What is the leverage of Reliance in 2023?") == "factual"
        assert classify_query("Why does profitability negatively impact leverage under POT?") == "analytical"
        assert classify_query("Compare pre-GFC and post-COVID leverage across sectors") == "hybrid"


class TestScenario4KG2SemanticOntology:
    """Golden Scenario 4: Querying semantic knowledge graph ontology and Dickinson rules."""

    def test_startup_and_maturity_normative_bands(self):
        startup_band = query_semantic_ontology("normative_band", stage="Startup")
        assert startup_band["status"] == "success"
        assert "Equity" in startup_band["normative_band"]["primary_source"]

        maturity_band = query_semantic_ontology("normative_band", stage="Maturity")
        assert maturity_band["status"] == "success"
        assert "Retained Earnings" in maturity_band["normative_band"]["primary_source"]

    def test_explain_decline_distress_anomaly(self):
        anomaly = query_semantic_ontology("explain_anomaly", stage="Decline", metric="leverage")
        assert anomaly["status"] == "success"
        assert "distress" in anomaly["explanation"].lower()
        assert "Jensen & Meckling (1976)" in anomaly["citations"]
