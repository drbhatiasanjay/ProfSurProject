"""
Unit tests for compute_covid_cohorts() in graph_builder.py.

Covers the four Phase 5 success criteria:
  COH-01: Post-COVID decline cohort identified and separated
  COH-02: COVID resilience tracker (improved vs deteriorated)
  COH-03: Leverage and profitability comparison columns present
  SC-4:   Cohort data accessible (function returns valid structure)
"""

import pytest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import db
from graph_builder import build_knowledge_graph, compute_covid_cohorts


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture(scope="module")
def fin_df():
    return db.get_graph_financials()


@pytest.fixture(scope="module")
def own_df():
    return db.get_graph_ownership()


@pytest.fixture(scope="module")
def G(fin_df, own_df):
    return build_knowledge_graph(fin_df, own_df)


@pytest.fixture(scope="module")
def cohort_result(G, fin_df):
    return compute_covid_cohorts(G, fin_df)


@pytest.fixture(scope="module")
def cohort_df(cohort_result):
    return cohort_result["cohort_df"]


# ── Structure tests (SC-4) ────────────────────────────────────────────────────

class TestCohortStructure:

    def test_no_error_with_thesis_data(self, cohort_result):
        assert "error" not in cohort_result, f"Unexpected error: {cohort_result.get('error')}"

    def test_required_keys_present(self, cohort_result):
        required = ["cohort_df", "n_total", "n_deteriorated", "n_improved",
                    "n_entered_decline", "n_recovered", "pct_deteriorated", "pct_improved"]
        for key in required:
            assert key in cohort_result, f"Missing key: {key}"

    def test_n_total_reasonable(self, cohort_result):
        assert cohort_result["n_total"] >= 50, (
            f"Expected at least 50 firms with pre/post COVID data, got {cohort_result['n_total']}"
        )

    def test_required_columns_in_cohort_df(self, cohort_df):
        required_cols = [
            "company", "industry", "pre_stage", "post_stage",
            "leverage_change", "profitability_change",
            "deteriorated", "improved", "entered_decline_after_covid", "recovered",
        ]
        for col in required_cols:
            assert col in cohort_df.columns, f"Missing column in cohort_df: {col}"


# ── Count consistency tests ────────────────────────────────────────────────────

class TestCohortCountConsistency:

    def test_n_deteriorated_matches_df(self, cohort_result, cohort_df):
        assert cohort_result["n_deteriorated"] == int(cohort_df["deteriorated"].sum())

    def test_n_improved_matches_df(self, cohort_result, cohort_df):
        assert cohort_result["n_improved"] == int(cohort_df["improved"].sum())

    def test_n_entered_decline_matches_df(self, cohort_result, cohort_df):
        assert cohort_result["n_entered_decline"] == int(cohort_df["entered_decline_after_covid"].sum())

    def test_n_recovered_matches_df(self, cohort_result, cohort_df):
        assert cohort_result["n_recovered"] == int(cohort_df["recovered"].sum())

    def test_pct_deteriorated_in_range(self, cohort_result):
        assert 0.0 <= cohort_result["pct_deteriorated"] <= 100.0

    def test_pct_improved_in_range(self, cohort_result):
        assert 0.0 <= cohort_result["pct_improved"] <= 100.0


# ── COH-01: Post-COVID decline cohort identified ──────────────────────────────

class TestPostCovidDeclineCohort:

    def test_entered_decline_after_covid_column_exists(self, cohort_df):
        assert "entered_decline_after_covid" in cohort_df.columns

    def test_entered_decline_firms_were_not_in_decline_pre_covid(self, cohort_df):
        """COH-01: Firms that entered Decline after COVID must NOT have been in Decline/Decay in 2019."""
        decline_stages = {"Decline", "Decay", "Shakeout1", "Shakeout2", "Shakeout3"}
        entered = cohort_df[cohort_df["entered_decline_after_covid"]]
        if not entered.empty:
            assert not entered["pre_stage"].isin(decline_stages).any(), (
                "Firms flagged entered_decline_after_covid must have non-decline pre_stage"
            )

    def test_entered_decline_firms_are_in_decline_post_covid(self, cohort_df):
        """COH-01: Firms that entered Decline after COVID must be in Decline/Decay/Shakeout post-2022."""
        decline_stages = {"Decline", "Decay", "Shakeout1", "Shakeout2", "Shakeout3"}
        entered = cohort_df[cohort_df["entered_decline_after_covid"]]
        if not entered.empty:
            assert entered["post_stage"].isin(decline_stages).all(), (
                "All entered_decline_after_covid firms must have decline-class post_stage"
            )


# ── COH-02: COVID resilience tracker ─────────────────────────────────────────

class TestCovidResilienceTracker:

    def test_resilience_cohorts_are_mutually_exclusive(self, cohort_df):
        """COH-02: A firm cannot be both improved and deteriorated."""
        both = cohort_df[cohort_df["improved"] & cohort_df["deteriorated"]]
        assert both.empty, f"{len(both)} firms flagged as both improved and deteriorated"

    def test_recovered_firms_were_in_decline_pre_covid(self, cohort_df):
        """COH-02: Recovered firms must have been in decline stages pre-COVID."""
        decline_stages = {"Decline", "Decay", "Shakeout1", "Shakeout2", "Shakeout3"}
        recovered = cohort_df[cohort_df["recovered"]]
        if not recovered.empty:
            assert recovered["pre_stage"].isin(decline_stages).all(), (
                "All recovered firms must have had decline-class pre_stage"
            )

    def test_recovered_firms_are_not_in_decline_post_covid(self, cohort_df):
        """COH-02: Recovered firms must NOT be in decline stages post-COVID."""
        decline_stages = {"Decline", "Decay", "Shakeout1", "Shakeout2", "Shakeout3"}
        recovered = cohort_df[cohort_df["recovered"]]
        if not recovered.empty:
            assert not recovered["post_stage"].isin(decline_stages).any(), (
                "Recovered firms must not have decline-class post_stage"
            )


# ── COH-03: Leverage and profitability comparison columns ─────────────────────

class TestCohortMetricColumns:

    def test_leverage_change_has_values(self, cohort_df):
        """COH-03: leverage_change must have non-null values for most firms."""
        assert cohort_df["leverage_change"].notna().sum() >= 20

    def test_profitability_change_has_values(self, cohort_df):
        """COH-03: profitability_change must have non-null values."""
        assert cohort_df["profitability_change"].notna().sum() >= 20

    def test_leverage_change_is_numeric(self, cohort_df):
        import pandas as pd
        assert pd.to_numeric(cohort_df["leverage_change"].dropna(), errors="coerce").notna().all()

    def test_profitability_change_is_numeric(self, cohort_df):
        import pandas as pd
        assert pd.to_numeric(cohort_df["profitability_change"].dropna(), errors="coerce").notna().all()

    def test_scipy_ttest_runs_on_cohorts(self, cohort_df):
        """COH-03: Welch's t-test must run without error when cohorts are large enough."""
        from scipy import stats
        det = cohort_df[cohort_df["deteriorated"]]["leverage_change"].dropna()
        imp = cohort_df[cohort_df["improved"]]["leverage_change"].dropna()
        if len(det) >= 5 and len(imp) >= 5:
            t_stat, p_val = stats.ttest_ind(det, imp, equal_var=False)
            assert 0.0 <= p_val <= 1.0

    def test_mannwhitneyu_runs_on_cohorts(self, cohort_df):
        """COH-03: Mann-Whitney U test must run without error when cohorts are large enough."""
        from scipy import stats
        det = cohort_df[cohort_df["deteriorated"]]["leverage_change"].dropna()
        imp = cohort_df[cohort_df["improved"]]["leverage_change"].dropna()
        if len(det) >= 5 and len(imp) >= 5:
            u_stat, p_mw = stats.mannwhitneyu(det, imp, alternative="two-sided")
            assert 0.0 <= p_mw <= 1.0
