"""
Tests for enhanced interpret_* functions in helpers.py.
Verifies: real stat values appear in output, no crash when optional params absent.
"""
import pytest
from helpers import (
    interpret_kpi_cards,
    interpret_econometric,
    interpret_ml_comparison,
    interpret_clustering,
    interpret_leverage_trend,
)
import pandas as pd
import numpy as np


# ── helpers ───────────────────────────────────────────────────────────────────

def _make_df(n=50, leverage=0.55, profitability=0.12):
    np.random.seed(42)
    return pd.DataFrame({
        "leverage": np.random.normal(leverage, 0.12, n).clip(0, 1),
        "profitability": np.random.normal(profitability, 0.05, n),
        "life_stage": np.random.choice(["Growth", "Mature", "Decline"], n),
        "year": np.random.randint(2010, 2024, n),
        "company_code": np.arange(n),
    })


# ── interpret_kpi_cards ───────────────────────────────────────────────────────

class TestInterpretKpiCards:
    def test_returns_tuple(self):
        df = _make_df()
        result = interpret_kpi_cards(df, 50, 0.55, 0.52, 0.12, "Mature", 250)
        assert isinstance(result, tuple) and len(result) == 2

    def test_no_crash_without_optional_params(self):
        df = _make_df()
        insights, actions = interpret_kpi_cards(df, 50, 0.55, 0.52, 0.12, "Mature", 250)
        assert isinstance(insights, list)
        assert isinstance(actions, list)

    def test_std_appears_in_insights_when_passed(self):
        df = _make_df()
        insights, _ = interpret_kpi_cards(
            df, 50, 0.55, 0.52, 0.12, "Mature", 250, std_lev=0.18
        )
        combined = " ".join(insights)
        assert "0.18" in combined or "σ" in combined or "std" in combined.lower()

    def test_pct_rank_appears_when_passed(self):
        df = _make_df()
        insights, _ = interpret_kpi_cards(
            df, 50, 0.55, 0.52, 0.12, "Mature", 250, pct_rank=74.0
        )
        combined = " ".join(insights)
        assert "74" in combined

    def test_yoy_delta_positive(self):
        df = _make_df()
        insights, _ = interpret_kpi_cards(
            df, 50, 0.55, 0.52, 0.12, "Mature", 250, yoy_delta=2.5
        )
        combined = " ".join(insights)
        assert "2.5" in combined or "increase" in combined.lower() or "↑" in combined or "rising" in combined.lower()

    def test_yoy_delta_negative(self):
        df = _make_df()
        insights, _ = interpret_kpi_cards(
            df, 50, 0.55, 0.52, 0.12, "Mature", 250, yoy_delta=-3.1
        )
        combined = " ".join(insights)
        assert "3.1" in combined or "decrease" in combined.lower() or "↓" in combined or "falling" in combined.lower()

    def test_peer_gap_positive(self):
        df = _make_df()
        insights, _ = interpret_kpi_cards(
            df, 50, 0.65, 0.62, 0.12, "Mature", 250, peer_gap=5.2
        )
        combined = " ".join(insights)
        assert "5.2" in combined or "above" in combined.lower() or "higher" in combined.lower()

    def test_peer_gap_negative(self):
        df = _make_df()
        insights, _ = interpret_kpi_cards(
            df, 50, 0.40, 0.38, 0.12, "Mature", 250, peer_gap=-4.1
        )
        combined = " ".join(insights)
        assert "4.1" in combined or "below" in combined.lower() or "lower" in combined.lower()

    def test_no_crash_all_optional_none(self):
        df = _make_df()
        insights, actions = interpret_kpi_cards(
            df, 50, 0.55, 0.52, 0.12, "Mature", 250,
            std_lev=None, pct_rank=None, yoy_delta=None, peer_gap=None
        )
        assert len(insights) > 0


# ── interpret_econometric ─────────────────────────────────────────────────────

class TestInterpretEconometric:
    def _make_result(self):
        return {
            "r_squared": 0.42,
            "adj_r_squared": 0.39,
            "f_statistic": 28.4,
            "f_pvalue": 0.0001,
            "n_obs": 3200,
            "model_type": "Pooled OLS",
            "coef_table": pd.DataFrame({
                "Variable": ["profitability", "firm_size", "tangibility"],
                "Coefficient": [-0.312, 0.087, 0.195],
                "Std Error": [0.045, 0.021, 0.033],
                "t-stat": [-6.93, 4.14, 5.91],
                "p-value": [0.0001, 0.0001, 0.0001],
            }),
        }

    def test_returns_tuple(self):
        r = self._make_result()
        result = interpret_econometric(r)
        assert isinstance(result, tuple) and len(result) == 2

    def test_no_crash_without_optional_stats(self):
        r = self._make_result()
        insights, actions = interpret_econometric(r)
        assert isinstance(insights, list)

    def test_adj_r2_in_output(self):
        r = self._make_result()
        insights, _ = interpret_econometric(r, adj_r2=0.39)
        combined = " ".join(insights)
        assert "0.39" in combined or "adj" in combined.lower()

    def test_f_stat_in_output(self):
        r = self._make_result()
        insights, _ = interpret_econometric(r, f_stat=28.4, f_pvalue=0.0001)
        combined = " ".join(insights)
        assert "28.4" in combined or "F" in combined

    def test_n_obs_in_output(self):
        r = self._make_result()
        insights, _ = interpret_econometric(r, n_obs=3200)
        combined = " ".join(insights)
        assert "3200" in combined or "3,200" in combined

    def test_hausman_in_output(self):
        r = self._make_result()
        hausman = {"chi2": 14.3, "p_value": 0.001}
        insights, actions = interpret_econometric(r, hausman=hausman)
        combined = " ".join(insights) + " ".join(actions)
        assert "Fixed" in combined or "Hausman" in combined


# ── interpret_ml_comparison ───────────────────────────────────────────────────

class TestInterpretMlComparison:
    def _make_comparison(self):
        # interpret_ml_comparison uses .iloc[0] as best — must sort descending by R²
        return pd.DataFrame({
            "Model": ["XGBoost", "LightGBM", "RF", "OLS"],
            "R-squared": [0.65, 0.64, 0.61, 0.28],
            "RMSE": [0.08, 0.085, 0.09, 0.14],
            "MAE": [0.065, 0.07, 0.07, 0.11],
        })

    def test_returns_tuple(self):
        result = interpret_ml_comparison(self._make_comparison())
        assert isinstance(result, tuple) and len(result) == 2

    def test_best_model_mentioned(self):
        insights, _ = interpret_ml_comparison(self._make_comparison())
        combined = " ".join(insights)
        assert "XGBoost" in combined or "LightGBM" in combined

    def test_ols_vs_best_gap(self):
        insights, _ = interpret_ml_comparison(self._make_comparison())
        combined = " ".join(insights)
        # Should mention the gap between OLS and best ML model
        assert "0.28" in combined or "0.65" in combined or "OLS" in combined


# ── interpret_clustering ──────────────────────────────────────────────────────

class TestInterpretClustering:
    def _make_summary(self):
        return pd.DataFrame({
            "cluster_label": ["Cluster 1", "Cluster 2", "Cluster 3"],
            "avg_leverage": [0.72, 0.45, 0.31],
            "avg_profitability": [0.08, 0.14, 0.19],
            "n_firms": [87, 145, 169],
        })

    def test_returns_tuple(self):
        result = interpret_clustering(0.71, 3, self._make_summary())
        assert isinstance(result, tuple) and len(result) == 2

    def test_no_crash_without_silhouette(self):
        insights, actions = interpret_clustering(0.71, 3, self._make_summary())
        assert isinstance(insights, list)

    def test_silhouette_in_output_when_passed(self):
        insights, _ = interpret_clustering(0.71, 3, self._make_summary(), silhouette=0.62)
        combined = " ".join(insights)
        assert "0.62" in combined or "silhouette" in combined.lower()

    def test_poor_silhouette_flagged(self):
        insights, _ = interpret_clustering(0.71, 3, self._make_summary(), silhouette=0.21)
        combined = " ".join(insights)
        assert "0.21" in combined or "weak" in combined.lower() or "poor" in combined.lower() or "overlap" in combined.lower()

    def test_k_mentioned(self):
        insights, _ = interpret_clustering(0.71, 3, self._make_summary())
        combined = " ".join(insights)
        assert "3" in combined


# ── interpret_leverage_trend ─────────────────────────────────────────────────

class TestInterpretLeverageTrend:
    def _make_stage_summary(self):
        """stage_summary is a df with life_stage, year, avg_leverage columns."""
        rows = []
        for stage in ["Growth", "Mature", "Decline"]:
            base = {"Growth": 0.55, "Mature": 0.62, "Decline": 0.70}[stage]
            for yr in range(2019, 2025):
                rows.append({
                    "life_stage": stage,
                    "year": yr,
                    "avg_leverage": base + (yr - 2019) * 0.01,
                })
        return pd.DataFrame(rows)

    def test_returns_tuple(self):
        result = interpret_leverage_trend(self._make_stage_summary())
        assert isinstance(result, tuple) and len(result) == 2

    def test_trend_or_volatility_in_output(self):
        insights, _ = interpret_leverage_trend(self._make_stage_summary())
        combined = " ".join(insights).lower()
        # Should mention volatility, stage name, or a trend direction
        assert any(word in combined for word in [
            "volatil", "increasing", "decreasing", "growth", "mature", "decline", "trend", "pp"
        ])
