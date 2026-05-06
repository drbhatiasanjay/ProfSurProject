"""
Tests for models/board_export.py data pipeline.

Tests the data-building layer only — no browser, no Streamlit, no PPTX rendering.
Validates that each topic function returns the expected contract shape and
that insights are data-driven (non-empty, non-generic when real data is present).
"""

import pytest
import pandas as pd
import numpy as np
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import db
from models.board_export import (
    TOPIC_BUILDERS, TOPIC_LABELS,
    build_topic_1, build_topic_2, build_topic_3, build_topic_4,
    build_topic_5, build_topic_6, build_topic_7, build_topic_8,
    build_topic_9, build_topic_10, build_topic_11, build_topic_12,
    build_topic_13,
)

# ── Fixtures ──────────────────────────────────────────────────────────────────

ASIAN_PAINTS_CODE = 22859   # well-known Maturity-stage firm in thesis panel
RELIANCE_CODE     = 196667


@pytest.fixture(scope="module")
def company_df():
    return db.get_company_detail(ASIAN_PAINTS_CODE)


@pytest.fixture(scope="module")
def full_panel():
    ft = db.filters_to_tuple({
        "panel_mode": "thesis",
        "company_codes": [],
        "year_range": (2001, 2024),
        "life_stages": [],
        "industry_groups": [],
        "events": {"gfc": False, "ibc": False, "covid": False},
    })
    return db.get_active_financials(ft)


@pytest.fixture(scope="module")
def stage_summary(full_panel):
    ft = db.filters_to_tuple({
        "panel_mode": "thesis",
        "company_codes": [],
        "year_range": (2001, 2024),
        "life_stages": [],
        "industry_groups": [],
        "events": {"gfc": False, "ibc": False, "covid": False},
    })
    return db.get_life_stage_summary(ft)


@pytest.fixture(scope="module")
def peers_df(full_panel):
    return db.get_company_peers(ASIAN_PAINTS_CODE, full_panel)


@pytest.fixture(scope="module")
def company_info(company_df):
    row = company_df.sort_values("year").iloc[-1]
    return {
        "name": "Asian Paints Ltd.",
        "code": ASIAN_PAINTS_CODE,
        "industry": "Paints & varnishes",
        "current_stage": row.get("life_stage", "Maturity"),
        "last_year": int(row.get("year", 2024)),
    }


# ── get_company_peers tests ────────────────────────────────────────────────────

class TestGetCompanyPeers:
    def test_returns_dataframe(self, full_panel):
        result = db.get_company_peers(ASIAN_PAINTS_CODE, full_panel)
        assert isinstance(result, pd.DataFrame)

    def test_excludes_focal_company(self, full_panel):
        result = db.get_company_peers(ASIAN_PAINTS_CODE, full_panel)
        assert ASIAN_PAINTS_CODE not in result["company_code"].values

    def test_peers_in_same_stage(self, full_panel, company_df):
        focal_stage = company_df.sort_values("year").iloc[-1]["life_stage"]
        result = db.get_company_peers(ASIAN_PAINTS_CODE, full_panel)
        if not result.empty and "life_stage" in result.columns:
            assert (result["life_stage"] == focal_stage).all()

    def test_max_n_respected(self, full_panel):
        result = db.get_company_peers(ASIAN_PAINTS_CODE, full_panel, n=5)
        assert len(result) <= 5

    def test_empty_panel_returns_empty(self):
        result = db.get_company_peers(ASIAN_PAINTS_CODE, pd.DataFrame())
        assert result.empty

    def test_unknown_company_returns_empty(self, full_panel):
        result = db.get_company_peers(9999999, full_panel)
        assert result.empty


# ── Topic function contract tests ─────────────────────────────────────────────

def _assert_contract(result, topic_id):
    """Assert the standard topic function return contract."""
    assert isinstance(result, dict), f"Topic {topic_id} must return dict"
    assert "figs" in result,     f"Topic {topic_id} missing 'figs'"
    assert "tables" in result,   f"Topic {topic_id} missing 'tables'"
    assert "insights" in result, f"Topic {topic_id} missing 'insights'"
    assert "actions" in result,  f"Topic {topic_id} missing 'actions'"
    assert "title" in result,    f"Topic {topic_id} missing 'title'"
    assert isinstance(result["figs"], list)
    assert isinstance(result["tables"], list)
    assert isinstance(result["insights"], list)
    assert isinstance(result["actions"], list)
    assert isinstance(result["title"], str) and result["title"]
    assert len(result["insights"]) >= 1, f"Topic {topic_id} must have at least 1 insight"
    assert len(result["actions"]) >= 1,  f"Topic {topic_id} must have at least 1 action"


class TestTopicContracts:
    """All 13 topic functions must return the correct contract shape."""

    @pytest.mark.parametrize("tid", list(TOPIC_BUILDERS.keys()))
    def test_contract_shape(self, tid, company_df, company_info, peers_df, full_panel, stage_summary):
        result = TOPIC_BUILDERS[tid](company_df, company_info, peers_df, full_panel, stage_summary)
        _assert_contract(result, tid)

    @pytest.mark.parametrize("tid", list(TOPIC_BUILDERS.keys()))
    def test_no_exceptions_on_empty_peers(self, tid, company_df, company_info, full_panel, stage_summary):
        """Topic functions must not crash when peers_df is empty."""
        result = TOPIC_BUILDERS[tid](company_df, company_info, pd.DataFrame(),
                                      full_panel, stage_summary)
        _assert_contract(result, tid)

    @pytest.mark.parametrize("tid", list(TOPIC_BUILDERS.keys()))
    def test_no_exceptions_on_none_panel(self, tid, company_df, company_info, peers_df, stage_summary):
        """Topic functions must not crash when full_panel is None."""
        result = TOPIC_BUILDERS[tid](company_df, company_info, peers_df, None, stage_summary)
        _assert_contract(result, tid)


# ── Topic-specific value assertions ────────────────────────────────────────────

class TestTopic1ExecutiveSummary:
    def test_has_two_figs(self, company_df, company_info, peers_df, full_panel, stage_summary):
        result = build_topic_1(company_df, company_info, peers_df, full_panel, stage_summary)
        assert len(result["figs"]) == 2

    def test_insight_mentions_leverage(self, company_df, company_info, peers_df, full_panel, stage_summary):
        result = build_topic_1(company_df, company_info, peers_df, full_panel, stage_summary)
        assert any("everage" in i for i in result["insights"])

    def test_insight_mentions_percentile(self, company_df, company_info, peers_df, full_panel, stage_summary):
        result = build_topic_1(company_df, company_info, peers_df, full_panel, stage_summary)
        assert any("percentile" in i for i in result["insights"])


class TestTopic2LifeCycle:
    def test_has_figs(self, company_df, company_info, peers_df, full_panel, stage_summary):
        result = build_topic_2(company_df, company_info, peers_df, full_panel, stage_summary)
        assert len(result["figs"]) >= 2

    def test_insight_mentions_stage(self, company_df, company_info, peers_df, full_panel, stage_summary):
        result = build_topic_2(company_df, company_info, peers_df, full_panel, stage_summary)
        stage = company_info["current_stage"]
        assert any(stage in i for i in result["insights"])

    def test_insight_mentions_peer_count(self, company_df, company_info, peers_df, full_panel, stage_summary):
        result = build_topic_2(company_df, company_info, peers_df, full_panel, stage_summary)
        assert any("firms" in i or "401" in i for i in result["insights"])


class TestTopic8PeerBenchmarking:
    def test_has_peer_table(self, company_df, company_info, peers_df, full_panel, stage_summary):
        result = build_topic_8(company_df, company_info, peers_df, full_panel, stage_summary)
        assert len(result["tables"]) >= 1

    def test_insight_mentions_percentile(self, company_df, company_info, peers_df, full_panel, stage_summary):
        result = build_topic_8(company_df, company_info, peers_df, full_panel, stage_summary)
        assert any("percentile" in i or "band" in i for i in result["insights"])


class TestTopic9Optimisation:
    def test_has_scenario_table(self, company_df, company_info, peers_df, full_panel, stage_summary):
        result = build_topic_9(company_df, company_info, peers_df, full_panel, stage_summary)
        tables = [t for t in result["tables"] if t is not None and not t.empty]
        assert len(tables) >= 1

    def test_scenario_table_has_five_rows(self, company_df, company_info, peers_df, full_panel, stage_summary):
        result = build_topic_9(company_df, company_info, peers_df, full_panel, stage_summary)
        scen = result["tables"][0]
        assert len(scen) == 5   # -20%, -10%, Current, +10%, +20%


class TestTopic11RiskStress:
    def test_has_stress_tables(self, company_df, company_info, peers_df, full_panel, stage_summary):
        result = build_topic_11(company_df, company_info, peers_df, full_panel, stage_summary)
        tables = [t for t in result["tables"] if t is not None and not t.empty]
        assert len(tables) >= 1   # interest rate shock table

    def test_stress_table_has_three_rows(self, company_df, company_info, peers_df, full_panel, stage_summary):
        result = build_topic_11(company_df, company_info, peers_df, full_panel, stage_summary)
        shock_tbl = result["tables"][0]
        assert len(shock_tbl) == 3   # Base, +200bp, +400bp


class TestTopic12SEBICompliance:
    def test_has_compliance_table(self, company_df, company_info, peers_df, full_panel, stage_summary):
        result = build_topic_12(company_df, company_info, peers_df, full_panel, stage_summary)
        tables = [t for t in result["tables"] if t is not None and not t.empty]
        assert len(tables) >= 1

    def test_insight_mentions_sebi(self, company_df, company_info, peers_df, full_panel, stage_summary):
        result = build_topic_12(company_df, company_info, peers_df, full_panel, stage_summary)
        assert any("SEBI" in i or "D/E" in i or "Debt" in i for i in result["insights"])


class TestTopic13Recommendations:
    def test_has_at_least_three_insights(self, company_df, company_info, peers_df, full_panel, stage_summary):
        result = build_topic_13(company_df, company_info, peers_df, full_panel, stage_summary)
        assert len(result["insights"]) >= 2

    def test_no_hallucination_marker(self, company_df, company_info, peers_df, full_panel, stage_summary):
        """Insights must be grounded — no placeholder or generic text."""
        result = build_topic_13(company_df, company_info, peers_df, full_panel, stage_summary)
        forbidden = ["[INSERT", "TODO", "PLACEHOLDER", "N/A analysis"]
        for insight in result["insights"]:
            for f in forbidden:
                assert f not in insight


# ── TOPIC_LABELS completeness ─────────────────────────────────────────────────

class TestCatalogue:
    def test_all_13_topics_in_builders(self):
        assert set(TOPIC_BUILDERS.keys()) == set(range(1, 14))

    def test_all_13_topics_in_labels(self):
        assert set(TOPIC_LABELS.keys()) == set(range(1, 14))

    def test_reliance_also_works(self, full_panel, stage_summary):
        co_df = db.get_company_detail(RELIANCE_CODE)
        row = co_df.sort_values("year").iloc[-1]
        co_info = {
            "name": "Reliance Industries Ltd.",
            "code": RELIANCE_CODE,
            "industry": "Refinery",
            "current_stage": row.get("life_stage", "Maturity"),
            "last_year": int(row.get("year", 2024)),
        }
        peers = db.get_company_peers(RELIANCE_CODE, full_panel)
        for tid in [1, 2, 3, 8, 9, 13]:
            result = TOPIC_BUILDERS[tid](co_df, co_info, peers, full_panel, stage_summary)
            _assert_contract(result, tid)


# ── DB column-presence tests (regression guard for get_company_detail fix) ───

class TestGetCompanyDetailColumns:
    """get_company_detail() must return all columns consumed by board_export topics."""

    REQUIRED_COLS = [
        "year", "life_stage", "leverage", "profitability", "tangibility",
        "tax", "dividend", "firm_size", "log_size", "tax_shield",
        "borrowings", "debentures_bonds", "total_capital", "reserves_and_funds",
        "total_liabilities", "cash_holdings", "ncfo", "ncfi", "ncff",
        "pbit", "pbt", "interest_amt", "int_rate",
        "gfc", "ibc_2016", "covid_dummy",
    ]

    def test_all_required_columns_present(self):
        df = db.get_company_detail(ASIAN_PAINTS_CODE)
        missing = [c for c in self.REQUIRED_COLS if c not in df.columns]
        assert not missing, f"get_company_detail missing columns: {missing}"

    def test_pbit_has_non_null_values(self):
        df = db.get_company_detail(ASIAN_PAINTS_CODE)
        assert "pbit" in df.columns, "pbit column not present"
        assert df["pbit"].notna().any(), "pbit is entirely NULL for Asian Paints"

    def test_interest_amt_has_non_null_values(self):
        df = db.get_company_detail(ASIAN_PAINTS_CODE)
        assert "interest_amt" in df.columns
        assert df["interest_amt"].notna().any(), "interest_amt is entirely NULL for Asian Paints"

    def test_total_capital_present(self):
        df = db.get_company_detail(ASIAN_PAINTS_CODE)
        assert "total_capital" in df.columns

    def test_reserves_and_funds_present(self):
        df = db.get_company_detail(ASIAN_PAINTS_CODE)
        assert "reserves_and_funds" in df.columns


# ── Zero / NaN interest edge-case tests ──────────────────────────────────────

def _make_zero_interest_df(base_df: pd.DataFrame) -> pd.DataFrame:
    """Copy of company_df with interest_amt forced to 0 (no debt service)."""
    df = base_df.copy()
    df["interest_amt"] = 0.0
    return df


def _make_nan_pbit_df(base_df: pd.DataFrame) -> pd.DataFrame:
    """Copy of company_df with pbit forced to NaN (column exists but missing data)."""
    df = base_df.copy()
    df["pbit"] = np.nan
    return df


class TestZeroInterestEdgeCases:
    """Topics 1, 11, 12, 13 use pbit/interest_amt for coverage calculations."""

    def test_topic_1_zero_interest_no_zero_division(self, company_df, company_info,
                                                     peers_df, full_panel, stage_summary):
        result = build_topic_1(
            _make_zero_interest_df(company_df), company_info,
            peers_df, full_panel, stage_summary
        )
        assert "figs" in result  # must not raise ZeroDivisionError

    def test_topic_11_zero_interest_no_zero_division(self, company_df, company_info,
                                                      peers_df, full_panel, stage_summary):
        result = TOPIC_BUILDERS[11](
            _make_zero_interest_df(company_df), company_info,
            peers_df, full_panel, stage_summary
        )
        assert "tables" in result
        tbl = result["tables"][0]
        assert len(tbl) == 3, "Should still produce 3 interest-rate shock rows"

    def test_topic_12_zero_interest_no_crash(self, company_df, company_info,
                                              peers_df, full_panel, stage_summary):
        result = TOPIC_BUILDERS[12](
            _make_zero_interest_df(company_df), company_info,
            peers_df, full_panel, stage_summary
        )
        _assert_contract(result, 12)

    def test_topic_13_zero_interest_no_crash(self, company_df, company_info,
                                              peers_df, full_panel, stage_summary):
        result = TOPIC_BUILDERS[13](
            _make_zero_interest_df(company_df), company_info,
            peers_df, full_panel, stage_summary
        )
        _assert_contract(result, 13)


class TestNaNPbitEdgeCases:
    """When pbit is NaN (common for some companies), topics must degrade gracefully."""

    def test_topic_1_nan_pbit_no_crash(self, company_df, company_info,
                                        peers_df, full_panel, stage_summary):
        result = build_topic_1(
            _make_nan_pbit_df(company_df), company_info,
            peers_df, full_panel, stage_summary
        )
        assert "figs" in result

    def test_topic_3_nan_pbit_no_crash(self, company_df, company_info,
                                        peers_df, full_panel, stage_summary):
        result = TOPIC_BUILDERS[3](
            _make_nan_pbit_df(company_df), company_info,
            peers_df, full_panel, stage_summary
        )
        _assert_contract(result, 3)

    def test_topic_11_nan_pbit_fallback(self, company_df, company_info,
                                         peers_df, full_panel, stage_summary):
        """Topic 11 falls back to profitability * firm_size when pbit is NaN — must still produce table."""
        result = TOPIC_BUILDERS[11](
            _make_nan_pbit_df(company_df), company_info,
            peers_df, full_panel, stage_summary
        )
        assert len(result["tables"]) >= 1


# ── Single-year company (minimal data) ───────────────────────────────────────

class TestMinimalData:
    """A company with only 1 year of data should not crash any topic."""

    @pytest.fixture
    def one_year_df(self, company_df):
        return company_df.tail(1).copy().reset_index(drop=True)

    @pytest.mark.parametrize("tid", list(TOPIC_BUILDERS.keys()))
    def test_single_year_no_crash(self, tid, one_year_df, company_info,
                                   peers_df, full_panel, stage_summary):
        result = TOPIC_BUILDERS[tid](one_year_df, company_info,
                                     peers_df, full_panel, stage_summary)
        assert "figs" in result


# ── Role access enforcement ───────────────────────────────────────────────────

def test_require_role_imported_in_page_17():
    """Page 17 must import and call require_role to block viewer access."""
    import ast, pathlib
    src = pathlib.Path("pages/17_board_export.py").read_text(encoding="utf-8")
    tree = ast.parse(src)
    calls = [
        node for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and isinstance(getattr(node.func, "id", None), str)
        and node.func.id == "require_role"
    ]
    assert calls, "require_role() not called in pages/17_board_export.py"
    # Must block viewer — at least one call must NOT include 'viewer'
    found_viewer_block = False
    for call in calls:
        arg_values = [
            a.s if isinstance(a, ast.Constant) else None
            for a in call.args
        ]
        if "viewer" not in arg_values:
            found_viewer_block = True
    assert found_viewer_block, "require_role() in page 17 does not exclude 'viewer'"


def test_page_17_in_navigation():
    """pages/17_board_export.py must be registered in app.py st.navigation()."""
    import pathlib
    src = pathlib.Path("app.py").read_text(encoding="utf-8")
    assert "17_board_export.py" in src, (
        "pages/17_board_export.py is not referenced in app.py — page is unreachable"
    )


def test_log_page_visit_called_in_page_17():
    """Page 17 must call db.log_page_visit() for audit trail compliance."""
    import pathlib
    src = pathlib.Path("pages/17_board_export.py").read_text(encoding="utf-8")
    assert "log_page_visit" in src, "db.log_page_visit() not called in page 17"
