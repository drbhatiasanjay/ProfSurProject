"""Test database layer — schema, views, queries."""

import pytest


class TestSchema:
    def test_companies_table(self, db_conn):
        # After DataV2 vintage load: 401 thesis firms + 1 new Tata Motors code (729991) = 402.
        # Old Tata Motors (248093) is kept with superseded_by=729991;
        # Gujarat State Petronet (86923) is kept with delisted_in_year=2024.
        df = db_conn.execute("SELECT COUNT(*) FROM companies").fetchone()
        assert df[0] >= 401, f"Expected ≥401 companies, got {df[0]}"

    def test_current_universe_is_401(self, db_conn):
        """Current universe = non-delisted, non-superseded firms. Still 401 by design."""
        row = db_conn.execute(
            "SELECT COUNT(*) FROM companies WHERE delisted_in_year IS NULL AND superseded_by IS NULL"
        ).fetchone()
        assert row[0] == 400 or row[0] == 401, f"Expected 400/401 current firms, got {row[0]}"

    def test_financials_thesis_vintage(self, db_conn):
        df = db_conn.execute("SELECT COUNT(*) FROM financials WHERE vintage = 'thesis'").fetchone()
        assert df[0] == 8677, f"Expected 8677 thesis rows, got {df[0]}"

    def test_life_stages_table(self, db_conn):
        df = db_conn.execute("SELECT COUNT(*) FROM life_stages").fetchone()
        assert df[0] == 8, f"Expected 8 stages, got {df[0]}"

    def test_ownership_thesis_vintage(self, db_conn):
        df = db_conn.execute("SELECT COUNT(*) FROM ownership WHERE vintage = 'thesis'").fetchone()
        assert df[0] == 8677

    def test_market_index_table(self, db_conn):
        df = db_conn.execute("SELECT COUNT(*) FROM market_index").fetchone()
        assert df[0] == 24

    def test_view_company_financials_thesis(self, db_conn):
        row = db_conn.execute("SELECT COUNT(*) FROM v_company_financials WHERE vintage = 'thesis'").fetchone()
        assert row[0] == 8677

    def test_view_has_company_code(self, db_conn):
        row = db_conn.execute("SELECT company_code FROM v_company_financials LIMIT 1").fetchone()
        assert row[0] is not None

    def test_year_range_thesis(self, db_conn):
        row = db_conn.execute("SELECT MIN(year), MAX(year) FROM financials WHERE vintage = 'thesis'").fetchone()
        assert row[0] == 2001
        assert row[1] == 2024

    def test_life_stage_values(self, db_conn):
        rows = db_conn.execute("SELECT DISTINCT stage_name FROM life_stages ORDER BY cls_code").fetchall()
        stages = [r[0] for r in rows]
        assert "Startup" in stages
        assert "Growth" in stages
        assert "Maturity" in stages
        assert "Decline" in stages


class TestDataV2Vintage:
    """DataV2 CMIE 2025 vintage load acceptance checks."""

    def test_cmie_2025_financials_count(self, db_conn):
        n = db_conn.execute("SELECT COUNT(*) FROM financials WHERE vintage = 'cmie_2025'").fetchone()[0]
        assert n == 400, f"Expected 400 cmie_2025 financials rows, got {n}"

    def test_cmie_2025_ownership_count(self, db_conn):
        n = db_conn.execute("SELECT COUNT(*) FROM ownership WHERE vintage = 'cmie_2025'").fetchone()[0]
        assert n == 400

    def test_cmie_2025_year_is_2025(self, db_conn):
        rows = db_conn.execute("SELECT DISTINCT year FROM financials WHERE vintage = 'cmie_2025'").fetchall()
        assert rows == [(2025,)]

    def test_data_vintages_registry(self, db_conn):
        rows = db_conn.execute("SELECT vintage FROM data_vintages ORDER BY vintage").fetchall()
        vintages = {r[0] for r in rows}
        assert "thesis" in vintages
        assert "cmie_2025" in vintages

    def test_market_index_series_populated(self, db_conn):
        n_series = db_conn.execute("SELECT COUNT(DISTINCT index_code) FROM market_index_series").fetchone()[0]
        assert n_series > 100, f"Expected >100 T623 index series, got {n_series}"

    def test_tata_motors_code_remap(self, db_conn):
        """Old Tata Motors code (248093) must be marked superseded_by new code (729991)."""
        row = db_conn.execute(
            "SELECT superseded_by FROM companies WHERE company_code = 248093"
        ).fetchone()
        assert row is not None, "Old Tata Motors row missing"
        assert row[0] == 729991, f"Expected superseded_by=729991, got {row[0]}"

    def test_gujarat_state_petronet_delisted(self, db_conn):
        row = db_conn.execute(
            "SELECT delisted_in_year FROM companies WHERE company_code = 86923"
        ).fetchone()
        assert row is not None
        assert row[0] == 2024, f"Expected delisted_in_year=2024, got {row[0]}"

    def test_panel_mode_thesis_row_count(self, db_conn):
        """Vintage predicate for 'thesis' mode returns exactly the thesis rows."""
        n = db_conn.execute(
            "SELECT COUNT(*) FROM financials WHERE vintage = 'thesis'"
        ).fetchone()[0]
        assert n == 8677

    def test_panel_mode_latest_row_count(self, db_conn):
        """Latest = thesis + cmie_2025 = 8677 + 400 = 9077."""
        n = db_conn.execute(
            "SELECT COUNT(*) FROM financials WHERE vintage IN ('thesis','cmie_2025')"
        ).fetchone()[0]
        assert n == 9077

    def test_age_group_populated_on_2025(self, db_conn):
        """2025 rows must carry age_group for filter/view queries to work."""
        n_null = db_conn.execute(
            "SELECT COUNT(*) FROM financials WHERE vintage='cmie_2025' AND age_group IS NULL"
        ).fetchone()[0]
        assert n_null == 0, f"{n_null} cmie_2025 rows have NULL age_group"


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
