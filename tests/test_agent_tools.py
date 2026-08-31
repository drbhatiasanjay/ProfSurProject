"""Unit tests for models/agent_tools.py — safe SQL sandbox, chart specs, and KG2 ontology lookups."""
import pytest
from models.agent_tools import (
    query_financial_database,
    generate_chat_chart,
    query_semantic_ontology,
    get_database_schema_summary,
)


class TestQueryFinancialDatabase:
    def test_valid_select_query(self):
        res = query_financial_database("SELECT company_code, company_name FROM companies LIMIT 5")
        assert res["status"] == "success"
        assert res["count"] > 0
        assert "company_name" in res["columns"]
        assert len(res["rows"]) <= 5

    def test_auto_limit_injection(self):
        res = query_financial_database("SELECT company_code FROM companies")
        assert res["status"] == "success"
        assert "LIMIT 50" in res["query_executed"]
        assert len(res["rows"]) <= 50

    def test_blocks_dml_insert(self):
        res = query_financial_database("INSERT INTO companies (company_code) VALUES (99999)")
        assert res["status"] == "error"
        assert "Security violation" in res["error"] or "must start with SELECT" in res["error"]

    def test_blocks_dml_delete(self):
        res = query_financial_database("DELETE FROM financials WHERE year < 2005")
        assert res["status"] == "error"
        assert "Security violation" in res["error"]

    def test_blocks_ddl_drop(self):
        res = query_financial_database("DROP TABLE financials")
        assert res["status"] == "error"
        assert "Security violation" in res["error"]

    def test_blocks_stacked_queries_semicolon(self):
        res = query_financial_database("SELECT 1; DROP TABLE financials;")
        assert res["status"] == "error"
        assert "Security violation" in res["error"]

    def test_empty_query_returns_error(self):
        res = query_financial_database("   ")
        assert res["status"] == "error"

    def test_syntax_error_returns_helpful_hint(self):
        res = query_financial_database("SELECT non_existent_column_xyz FROM financials")
        assert res["status"] == "error"
        assert "schema_hint" in res

    def test_blocks_sensitive_table_access(self):
        res = query_financial_database("SELECT username FROM audit_log")
        assert res["status"] == "error"
        assert "allow" in res["error"].lower() or "security" in res["error"].lower()

    def test_panel_mode_scopes_financials_query(self):
        res = query_financial_database(
            "SELECT COUNT(*) AS n FROM financials", panel_mode="thesis"
        )
        assert res["status"] == "success"
        assert "assistant_financials" in res["query_executed"]

    def test_normalizes_panel_metric_aliases(self):
        res = query_financial_database(
            "SELECT year, AVG(ndts) AS ndts, AVG(liquidity) AS liquidity, "
            "AVG(ocf) AS ocf FROM financials GROUP BY year LIMIT 2"
        )
        assert res["status"] == "success"
        assert "tax_shield" in res["query_executed"]
        assert "cash_holdings" in res["query_executed"]
        assert "AVG(oc)" in res["query_executed"]

    def test_supports_statistical_aggregates(self):
        res = query_financial_database(
            "SELECT MEDIAN(profitability) AS median_roa, "
            "P25(profitability) AS p25_roa, P75(profitability) AS p75_roa, "
            "STDEV(profitability) AS sd_roa FROM financials"
        )
        assert res["status"] == "success"
        row = res["rows"][0]
        assert all(row[key] is not None for key in ("median_roa", "p25_roa", "p75_roa", "sd_roa"))


class TestGenerateChatChart:
    def test_valid_line_chart_spec(self):
        res = generate_chat_chart(
            chart_type="line",
            title="5-Year Leverage Trend",
            x_axis_label="Year",
            y_axis_label="Leverage (%)",
            categories=["2020", "2021", "2022", "2023", "2024"],
            series=[{"name": "Company", "values": [12.5, 14.2, 13.8, 15.0, 14.5]}],
        )
        assert res["status"] == "success"
        assert res["chart_spec"]["chart_type"] == "line"
        assert len(res["chart_spec"]["series"]) == 1
        assert res["chart_spec"]["series"][0]["name"] == "Company"

    def test_empty_series_returns_error(self):
        res = generate_chat_chart(
            chart_type="bar",
            title="Empty Chart",
            x_axis_label="X",
            y_axis_label="Y",
            categories=["A", "B"],
            series=[],
        )
        assert res["status"] == "error"

    def test_invalid_chart_type_defaults_to_line(self):
        res = generate_chat_chart(
            chart_type="radar",
            title="Radar Test",
            x_axis_label="X",
            y_axis_label="Y",
            categories=["A", "B"],
            series=[{"name": "S1", "values": [1, 2]}],
        )
        assert res["status"] == "success"
        assert res["chart_spec"]["chart_type"] == "line"


class TestQuerySemanticOntology:
    def test_normative_band_for_maturity(self):
        res = query_semantic_ontology("normative_band", stage="Maturity")
        assert res["status"] == "success"
        assert res["stage"] == "Maturity"
        assert "normative_band" in res
        assert "Dickinson" in res["source"]

    def test_stage_definition_startup(self):
        res = query_semantic_ontology("stage_definition", stage="Startup")
        assert res["status"] == "success"
        assert res["cash_flow_signs"]["OCF"] == "-"
        assert res["cash_flow_signs"]["FCF"] == "+"

    def test_explain_anomaly_decline(self):
        res = query_semantic_ontology("explain_anomaly", stage="Decline", metric="leverage")
        assert res["status"] == "success"
        assert "distress" in res["explanation"].lower()
        assert len(res["citations"]) > 0

    def test_schema_summary_helper(self):
        summary = get_database_schema_summary()
        assert "companies" in summary
        assert "financials" in summary
        assert "leverage" in summary
