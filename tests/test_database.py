"""Test database layer — schema, views, queries."""

import pytest


class TestSchema:
    def test_companies_table(self, db_conn):
        df = db_conn.execute("SELECT COUNT(*) FROM companies").fetchone()
        assert df[0] == 401, f"Expected 401 companies, got {df[0]}"

    def test_financials_table(self, db_conn):
        df = db_conn.execute("SELECT COUNT(*) FROM financials").fetchone()
        assert df[0] == 8677, f"Expected 8677 rows, got {df[0]}"

    def test_life_stages_table(self, db_conn):
        df = db_conn.execute("SELECT COUNT(*) FROM life_stages").fetchone()
        assert df[0] == 8, f"Expected 8 stages, got {df[0]}"

    def test_ownership_table(self, db_conn):
        df = db_conn.execute("SELECT COUNT(*) FROM ownership").fetchone()
        assert df[0] == 8677

    def test_market_index_table(self, db_conn):
        df = db_conn.execute("SELECT COUNT(*) FROM market_index").fetchone()
        assert df[0] == 24

    def test_view_company_financials(self, db_conn):
        row = db_conn.execute("SELECT COUNT(*) FROM v_company_financials").fetchone()
        assert row[0] == 8677

    def test_view_has_company_code(self, db_conn):
        row = db_conn.execute("SELECT company_code FROM v_company_financials LIMIT 1").fetchone()
        assert row[0] is not None

    def test_year_range(self, db_conn):
        row = db_conn.execute("SELECT MIN(year), MAX(year) FROM financials").fetchone()
        assert row[0] == 2001
        assert row[1] == 2024

    def test_life_stage_values(self, db_conn):
        rows = db_conn.execute("SELECT DISTINCT stage_name FROM life_stages ORDER BY cls_code").fetchall()
        stages = [r[0] for r in rows]
        assert "Startup" in stages
        assert "Growth" in stages
        assert "Maturity" in stages
        assert "Decline" in stages


class TestFilteredQueries:
    def test_company_filter(self, db_conn):
        row = db_conn.execute("""
            SELECT COUNT(DISTINCT company_name) FROM v_company_financials
            WHERE company_code IN (SELECT company_code FROM companies WHERE company_name = 'Infosys Ltd.')
        """).fetchone()
        assert row[0] == 1

    def test_life_stage_filter(self, db_conn):
        row = db_conn.execute("""
            SELECT COUNT(*) FROM v_company_financials WHERE life_stage = 'Startup'
        """).fetchone()
        assert row[0] > 0 and row[0] < 8677

    def test_year_filter(self, db_conn):
        row = db_conn.execute("""
            SELECT COUNT(*) FROM v_company_financials WHERE year BETWEEN 2010 AND 2015
        """).fetchone()
        assert row[0] > 0 and row[0] < 8677

    def test_gfc_filter(self, db_conn):
        row = db_conn.execute("SELECT COUNT(*) FROM financials WHERE gfc = 1").fetchone()
        assert row[0] > 0

    def test_parameterized_query_safe(self, db_conn):
        """Ensure parameterized queries work (no SQL injection)."""
        row = db_conn.execute(
            "SELECT COUNT(*) FROM v_company_financials WHERE life_stage = ?",
            ("Growth",)
        ).fetchone()
        assert row[0] > 0
