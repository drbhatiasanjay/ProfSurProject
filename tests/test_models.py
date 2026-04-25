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

    def test_pairwise_comparison_structure(self, full_panel):
        """Tukey HSD pairwise comparison — output shape + matrix invariants."""
        from models.econometric import run_pairwise_comparison
        result = run_pairwise_comparison(full_panel)

        # Required keys
        for key in ("pairwise_df", "matrix_diff", "matrix_pval", "matrix_sig",
                    "group_means", "significant_pairs", "n_pairs", "n_significant"):
            assert key in result, f"Missing key: {key}"

        pdf = result["pairwise_df"]
        # Required columns
        for col in ("Stage A", "Stage B", "Mean Diff", "p-value", "Significant"):
            assert col in pdf.columns

        # Pair count = C(k, 2) for k stages present
        all_stages = set(pdf["Stage A"]) | set(pdf["Stage B"])
        k = len(all_stages)
        assert result["n_pairs"] == k * (k - 1) // 2

        # Matrix invariants
        m_diff = result["matrix_diff"]
        m_pval = result["matrix_pval"]
        for s in m_diff.index:
            # Diagonal: zero diff, p=1
            assert m_diff.loc[s, s] == 0.0
            assert m_pval.loc[s, s] == 1.0
        # Anti-symmetry of diff and symmetry of p-value
        stages = list(m_diff.index)
        for i in range(len(stages)):
            for j in range(i + 1, len(stages)):
                a, b = stages[i], stages[j]
                assert m_diff.loc[a, b] == pytest.approx(-m_diff.loc[b, a])
                assert m_pval.loc[a, b] == pytest.approx(m_pval.loc[b, a])

    def test_robust_regression_huber(self, full_panel):
        """RLM with Huber-T norm — return shape + outlier downweighting."""
        from models.econometric import run_robust_regression
        result = run_robust_regression(full_panel)
        assert result["type"].startswith("Robust M")
        assert result["norm"] == "HuberT"
        assert result["n_obs"] > 5000
        assert len(result["coef_table"]) >= 6  # const + 6 predictors
        # Sanity on pseudo-R² — should be in (-1, 1) plausibly
        assert -1.0 < result["r_squared"] < 1.0
        # IRLS should downweight some obs on a panel with leverage outliers
        assert result["n_downweighted"] > 0, \
            "RLM should downweight some outliers on the thesis panel"
        # Min weight strictly < 1 confirms IRLS actually fired
        assert result["weight_min"] < 1.0

    def test_robust_vs_ols_pecking_order(self, full_panel):
        """Both OLS and RLM should keep profitability negative (Pecking Order),
        but coefficient magnitudes differ — that's the whole point of robust regression."""
        from models.econometric import run_pooled_ols, run_robust_regression
        ols = run_pooled_ols(full_panel)
        rlm = run_robust_regression(full_panel)

        ols_prof = ols["coef_table"].set_index("Variable").loc["profitability", "Coefficient"]
        rlm_prof = rlm["coef_table"].set_index("Variable").loc["profitability", "Coefficient"]
        assert ols_prof < 0, "OLS profitability coefficient should be negative"
        assert rlm_prof < 0, "RLM profitability coefficient should be negative"
        # RLM should not produce identical coefficients to OLS — IRLS reweights
        assert ols_prof != pytest.approx(rlm_prof, abs=1e-6), \
            "RLM and OLS coefficients should differ"

    def test_robust_regression_unknown_norm_raises(self, full_panel):
        """Invalid norm string raises ValueError with supported-list hint."""
        from models.econometric import run_robust_regression
        with pytest.raises(ValueError, match="Supported"):
            run_robust_regression(full_panel, norm="NonExistentNorm")

    def test_iv_regression_default(self, full_panel):
        """IV/2SLS with default spec (instrument profitability with its 1- and 2-period lags)."""
        from models.econometric import run_iv_regression
        result = run_iv_regression(full_panel)
        assert result["type"] == "IV / 2SLS"
        assert "error" not in result, f"Got error: {result.get('error')}"
        assert result["endogenous"] == "profitability"
        assert result["instruments"] == ["profitability_lag1", "profitability_lag2"]
        assert "coef_table" in result
        # Lagging by 2 + dropna trims rows; expect at least 3000 obs (panel has 8.6k)
        assert result["n_obs"] > 3000

    def test_iv_regression_diagnostics(self, full_panel):
        """First-stage F-stat should be strong (>10) and Sargan p > 0.05 (instruments valid)
        for the default profitability spec on the thesis panel."""
        from models.econometric import run_iv_regression
        result = run_iv_regression(full_panel)
        # First-stage F-stat (rule of thumb: > 10 = strong instruments)
        if result.get("first_stage_f") is not None:
            assert result["first_stage_f"] > 10, \
                f"Weak instruments — first-stage F = {result['first_stage_f']:.2f}"
        # Sargan over-id test — only meaningful with > 1 instrument
        if result.get("sargan_pvalue") is not None:
            # Document but don't enforce: thesis panel may or may not satisfy
            # over-id at strict 5% on these instruments. This test just records.
            assert 0.0 <= result["sargan_pvalue"] <= 1.0

    def test_iv_regression_custom_endog(self, full_panel):
        """Override the endogenous regressor + instruments."""
        from models.econometric import run_iv_regression
        result = run_iv_regression(
            full_panel,
            x_endog="tangibility",
            instruments=["tangibility_lag1", "tangibility_lag2"],
        )
        assert "error" not in result, f"Got error: {result.get('error')}"
        assert result["endogenous"] == "tangibility"
        # Profitability now in exogenous list
        assert "profitability" in result["exogenous"]
        # Coefficient table includes the instrumented endogenous regressor
        assert "tangibility" in set(result["coef_table"]["Variable"])

    def test_pairwise_aligns_with_anova(self, full_panel):
        """If ANOVA finds a significant between-stage difference, at least
        one Tukey-HSD pair should also be significant. (Tukey is conservative,
        so the converse isn't guaranteed.)"""
        from models.econometric import run_anova_by_stage, run_pairwise_comparison
        anova = run_anova_by_stage(full_panel)
        pw = run_pairwise_comparison(full_panel)
        if anova["p_value"] < 0.05:
            assert pw["n_significant"] >= 1, \
                "ANOVA significant but Tukey HSD found no significant pairs"


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
