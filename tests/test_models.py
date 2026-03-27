"""Test all ML and econometric models."""

import pytest
import numpy as np


class TestEconometric:
    def test_pooled_ols(self, full_panel):
        from models.econometric import run_pooled_ols
        result = run_pooled_ols(full_panel)
        assert result["type"] == "Pooled OLS"
        assert result["r_squared"] > 0.1, f"R² too low: {result['r_squared']}"
        assert result["n_obs"] > 5000
        assert len(result["coef_table"]) >= 6  # 6 predictors + const

    def test_fixed_effects(self, full_panel):
        from models.econometric import run_fixed_effects
        result = run_fixed_effects(full_panel)
        assert result["type"] == "Fixed Effects"
        assert result["r_squared"] > 0.05
        assert result["n_firms"] > 300

    def test_random_effects(self, full_panel):
        from models.econometric import run_random_effects
        result = run_random_effects(full_panel)
        assert result["type"] == "Random Effects"
        assert result["r_squared"] > 0.05

    def test_hausman_test(self, full_panel):
        from models.econometric import run_fixed_effects, run_random_effects, run_hausman_test
        fe = run_fixed_effects(full_panel)
        re = run_random_effects(full_panel)
        h = run_hausman_test(fe, re)
        assert "chi2" in h
        assert "p_value" in h
        assert h["recommended"] in ("Fixed Effects", "Random Effects")

    def test_anova(self, full_panel):
        from models.econometric import run_anova_by_stage
        result = run_anova_by_stage(full_panel)
        assert result["f_stat"] > 0
        assert result["p_value"] < 0.05, "ANOVA should be significant"
        assert len(result["group_stats"]) >= 7  # At least 7 stages

    def test_auto_suggest(self, full_panel):
        from models.econometric import run_all_and_compare
        results = run_all_and_compare(full_panel)
        assert results["recommended"] in ("Fixed Effects", "Random Effects")
        assert len(results["comparison"]) == 3

    def test_profitability_negative(self, full_panel):
        """Pecking Order: profitability should have negative coefficient."""
        from models.econometric import run_pooled_ols
        result = run_pooled_ols(full_panel)
        ct = result["coef_table"]
        prof_row = ct[ct["Variable"] == "profitability"]
        assert len(prof_row) == 1
        assert prof_row.iloc[0]["Coefficient"] < 0, "Profitability should reduce leverage (Pecking Order)"

    def test_tangibility_positive(self, full_panel):
        """Trade-off Theory: tangibility should have positive coefficient."""
        from models.econometric import run_pooled_ols
        result = run_pooled_ols(full_panel)
        ct = result["coef_table"]
        tang_row = ct[ct["Variable"] == "tangibility"]
        assert len(tang_row) == 1
        assert tang_row.iloc[0]["Coefficient"] > 0, "Tangibility should increase leverage (Trade-off)"


    def test_breusch_pagan_lm(self, full_panel):
        """BP-LM test: Pooled OLS vs Random Effects."""
        from models.econometric import run_pooled_ols, run_breusch_pagan_lm
        ols = run_pooled_ols(full_panel)
        bp = run_breusch_pagan_lm(ols)
        assert "lm_stat" in bp
        assert "lm_pvalue" in bp
        assert bp["lm_stat"] > 0
        assert "verdict" in bp

    def test_delta_leverage_ols(self, full_panel):
        """Delta-leverage OLS regression."""
        from models.econometric import run_delta_leverage_ols
        result = run_delta_leverage_ols(full_panel)
        assert result["type"] == "Pooled OLS"
        assert result["n_obs"] > 3000

    def test_delta_leverage_all(self, full_panel):
        """Delta-leverage with FE/RE + Hausman."""
        from models.econometric import run_delta_leverage_all
        result = run_delta_leverage_all(full_panel)
        assert result["recommended"] in ("Fixed Effects", "Random Effects")
        assert "ols" in result
        assert "fe" in result
        assert "re" in result

    def test_delta_leverage_by_stage(self, full_panel):
        """Stage-specific delta-leverage regressions."""
        from models.econometric import run_delta_leverage_by_stage
        results = run_delta_leverage_by_stage(full_panel)
        assert len(results) >= 3  # At least Growth, Maturity, Startup
        for stage, res in results.items():
            if "error" not in res:
                assert "coef_table" in res

    def test_stage_comparison(self, full_panel):
        """Growth vs Maturity comparison regression."""
        from models.econometric import run_stage_comparison
        result = run_stage_comparison(full_panel, "Growth", "Maturity")
        assert "comparison" in result
        assert "result_a" in result
        assert "result_b" in result
        assert "Divergent" in result["comparison"].columns

    def test_system_gmm(self, full_panel):
        """System GMM with lag DV."""
        from models.econometric import run_system_gmm
        result = run_system_gmm(full_panel)
        assert "coef_table" in result
        assert result["lag_dv_included"] is True
        assert "ar1" in result
        assert "ar2" in result
        assert "sargan" in result
        assert result["n_obs"] > 2000


class TestMLModels:
    def test_cross_validate_rf(self, small_panel):
        from models.ml_predict import cross_validate_model
        result = cross_validate_model("Random Forest", small_panel, n_splits=3)
        assert result["model_name"] == "Random Forest"
        assert result["avg_metrics"]["r2"] > -1  # At least not catastrophic
        assert result["avg_metrics"]["rmse"] < 100
        assert result["n_obs"] > 100

    def test_cross_validate_xgboost(self, small_panel):
        from models.ml_predict import cross_validate_model
        result = cross_validate_model("XGBoost", small_panel, n_splits=3)
        assert result["avg_metrics"]["rmse"] < 100

    def test_cross_validate_lightgbm(self, small_panel):
        from models.ml_predict import cross_validate_model
        result = cross_validate_model("LightGBM", small_panel, n_splits=3)
        assert result["avg_metrics"]["rmse"] < 100

    def test_compare_all_models(self, small_panel):
        from models.ml_predict import compare_all_models
        results, comparison = compare_all_models(small_panel, n_splits=3)
        assert len(results) == 3
        assert len(comparison) == 3
        assert "R-squared" in comparison.columns
        # Best model should be first
        assert comparison.iloc[0]["R-squared"] >= comparison.iloc[-1]["R-squared"]

    def test_feature_importance(self, small_panel):
        from models.ml_predict import cross_validate_model, get_feature_importance
        result = cross_validate_model("XGBoost", small_panel, n_splits=3)
        imp = get_feature_importance(result["model"], result["feature_names"])
        assert len(imp) == len(result["feature_names"])
        assert imp["Importance"].sum() > 0

    def test_predict_leverage(self, small_panel):
        from models.ml_predict import cross_validate_model, predict_leverage
        result = cross_validate_model("XGBoost", small_panel, n_splits=3)
        pred = predict_leverage(result["model"], [10, 0.3, 15, 7, 5, 2], result["feature_names"])
        assert pred >= 0
        assert pred < 200  # Reasonable leverage


class TestClustering:
    def test_prepare_features(self, full_panel):
        from models.clustering import prepare_firm_features
        firm_df, X, scaler, feats = prepare_firm_features(full_panel)
        assert len(firm_df) > 300
        assert X.shape[1] == len(feats)

    def test_optimal_k(self, full_panel):
        from models.clustering import prepare_firm_features, find_optimal_k
        _, X, _, _ = prepare_firm_features(full_panel)
        best_k, scores = find_optimal_k(X)
        assert 3 <= best_k <= 12
        assert len(scores) == 10  # k_range=3..12

    def test_kmeans(self, full_panel):
        from models.clustering import prepare_firm_features, run_kmeans
        firm_df, X, _, _ = prepare_firm_features(full_panel)
        labels, clustered, profiles, km = run_kmeans(X, 5, firm_df)
        assert len(set(labels)) == 5
        assert "cluster_label" in clustered.columns

    def test_dickinson_comparison(self, full_panel):
        from models.clustering import prepare_firm_features, run_kmeans, compare_with_dickinson
        firm_df, X, _, _ = prepare_firm_features(full_panel)
        _, clustered, _, _ = run_kmeans(X, 8, firm_df)
        crosstab, ari = compare_with_dickinson(clustered)
        assert -1 <= ari <= 1
        assert len(crosstab) > 0


class TestSurvival:
    def test_prepare_transitions(self, full_panel):
        from models.survival import prepare_transition_data
        trans = prepare_transition_data(full_panel)
        assert len(trans) > 100
        assert "duration" in trans.columns
        assert "event" in trans.columns
        assert trans["event"].sum() > 0

    def test_kaplan_meier(self, full_panel):
        from models.survival import prepare_transition_data, fit_kaplan_meier
        trans = prepare_transition_data(full_panel)
        km_fits, summary = fit_kaplan_meier(trans)
        assert len(km_fits) >= 5
        assert "Median Duration (yrs)" in summary.columns

    def test_cox_ph(self, full_panel):
        from models.survival import prepare_transition_data, fit_cox_ph
        trans = prepare_transition_data(full_panel)
        cph, hr_df, summary = fit_cox_ph(trans)
        assert cph is not None
        assert "Hazard Ratio" in hr_df.columns
        assert len(hr_df) >= 3

    def test_transition_matrix(self, full_panel):
        from models.survival import prepare_transition_data, get_transition_matrix
        trans = prepare_transition_data(full_panel)
        matrix = get_transition_matrix(trans)
        assert not matrix.empty
        # Each row should sum to ~100%
        for idx, row in matrix.iterrows():
            assert abs(row.sum() - 100) < 5, f"Row {idx} sums to {row.sum()}, not ~100"


class TestHelpers:
    def test_winsorize(self):
        import pandas as pd
        from helpers import winsorize
        s = pd.Series([1, 2, 3, 100, 200])
        w = winsorize(s)
        assert w.max() < 200
        assert w.min() >= 1

    def test_classify_life_stage(self):
        from helpers import classify_life_stage
        assert classify_life_stage(-10, -5, 20) == "Startup"
        assert classify_life_stage(10, -5, 20) == "Growth"
        assert classify_life_stage(10, -5, -20) == "Maturity"
        assert classify_life_stage(-10, 5, 5) == "Decline"
        assert classify_life_stage(-10, 5, -5) == "Decay"

    def test_format_functions(self):
        from helpers import format_pct, format_inr, format_number
        assert format_pct(21.5) == "21.5%"
        assert format_pct(None) == "N/A"
        assert "Cr" in format_inr(1500)
        assert format_number(8677) == "8,677"

    def test_interpret_functions_dynamic(self, full_panel):
        """Ensure interpretation functions produce non-empty output."""
        from helpers import interpret_kpi_cards, interpret_econometric
        from models.econometric import run_pooled_ols
        f, a = interpret_kpi_cards(full_panel, 401, 21.0, 15.8, 0.15, "Maturity", 8677)
        assert len(f) >= 2, "KPI interpretation should have findings"
        assert len(a) >= 1, "KPI interpretation should have actions"

        result = run_pooled_ols(full_panel)
        f2, a2 = interpret_econometric(result)
        assert len(f2) >= 3, "Econometric interpretation should be detailed"
        assert any("Pecking Order" in x or "Trade-off" in x for x in f2), "Should reference capital structure theories"
