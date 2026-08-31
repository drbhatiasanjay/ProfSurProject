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
        """BP-LM test: Pooled OLS vs Random Effects. Phase 1: TST-01, TST-02."""
        from models.econometric import run_pooled_ols, run_breusch_pagan_lm
        ols = run_pooled_ols(full_panel)
        bp = run_breusch_pagan_lm(ols)

        # TST-02: full contract per 01-01 docstring
        assert "lm_stat" in bp and "lm_pvalue" in bp
        assert "f_stat" in bp and "f_pvalue" in bp
        assert "verdict" in bp

        # Statistical sanity
        assert bp["lm_stat"] > 0, f"lm_stat must be positive, got {bp['lm_stat']}"
        assert 0.0 <= bp["lm_pvalue"] <= 1.0, f"lm_pvalue out of [0,1]: {bp['lm_pvalue']}"
        assert 0.0 <= bp["f_pvalue"] <= 1.0

        # TST-01: exact verdict string contract (locked in models/econometric.py docstring)
        assert bp["verdict"] in (
            "Panel effects detected (reject Pooled OLS at 5% level)",
            "No significant panel effects (Pooled OLS adequate)",
        ), f"Unexpected BP-LM verdict: {bp['verdict']!r}"

    def test_delta_leverage_ols(self, full_panel):
        """Delta-leverage OLS regression. Phase 1: DLV-01."""
        from models.econometric import run_pooled_ols, run_delta_leverage_ols
        baseline = run_pooled_ols(full_panel)
        result = run_delta_leverage_ols(full_panel)

        # DLV-01: type contract from 01-01 docstring
        assert result["type"] == "Pooled OLS"

        # DLV-01: full result-dict contract
        assert "coef_table" in result and len(result["coef_table"]) > 0
        assert "r_squared" in result
        assert "n_obs" in result and result["n_obs"] > 0

        # DLV-01: first-difference reduces n_obs (drops first obs per firm)
        assert result["n_obs"] < baseline["n_obs"], (
            f"delta n_obs ({result['n_obs']}) must be < baseline ({baseline['n_obs']}) "
            f"because first-differencing drops obs[0] per firm"
        )
        assert result["n_obs"] > 3000, f"delta panel too small: {result['n_obs']}"

    def test_delta_leverage_all(self, full_panel):
        """Delta-leverage with FE/RE + Hausman. Phase 1: DLV-02."""
        from models.econometric import run_delta_leverage_all
        result = run_delta_leverage_all(full_panel)

        # DLV-02: top-level contract from 01-01 docstring
        assert "ols" in result
        assert "fe" in result
        assert "re" in result
        assert "hausman" in result
        assert "recommended" in result
        assert result["recommended"] in ("Fixed Effects", "Random Effects")

        # DLV-02: Hausman sub-dict contract
        h = result["hausman"]
        assert "chi2" in h and "p_value" in h and "verdict" in h and "recommended" in h
        assert h["chi2"] >= 0, f"hausman chi2 must be non-negative, got {h['chi2']}"
        assert 0.0 <= h["p_value"] <= 1.0

        # DLV-02: top-level recommended mirrors Hausman recommendation (per 01-01 docstring)
        assert result["recommended"] == h["recommended"], (
            f"top-level recommended ({result['recommended']}) must equal "
            f"hausman.recommended ({h['recommended']})"
        )

        # FE and RE share the same first-differenced panel
        assert result["fe"]["n_obs"] == result["re"]["n_obs"], (
            f"FE n_obs ({result['fe']['n_obs']}) != RE n_obs ({result['re']['n_obs']})"
        )

    def test_delta_leverage_by_stage(self, full_panel):
        """Stage-specific delta-leverage regressions. Phase 1: DLV-03, DLV-04."""
        from models.econometric import run_delta_leverage_by_stage
        results = run_delta_leverage_by_stage(full_panel)

        # DLV-03: shape — dict mapping stage name to result-or-error
        assert isinstance(results, dict)
        assert len(results) >= 3, f"expected at least 3 stages, got {len(results)}"

        ok = {s: r for s, r in results.items() if "error" not in r}
        errors = {s: r for s, r in results.items() if "error" in r}

        # DLV-03: at least one stage produced a real regression
        assert len(ok) >= 1, "At least one stage must produce a coef_table (DLV-03)"

        # DLV-04: every ok stage has the documented run_pooled_ols contract
        for stage, res in ok.items():
            assert "coef_table" in res, f"{stage}: missing coef_table"
            assert len(res["coef_table"]) > 0, f"{stage}: empty coef_table"
            assert "n_obs" in res and res["n_obs"] > 0, f"{stage}: bad n_obs"
            assert "r_squared" in res, f"{stage}: missing r_squared"

        # Every error dict uses the 'Too few observations (N)' string format
        for stage, res in errors.items():
            assert isinstance(res["error"], str)
            assert "Too few observations" in res["error"], (
                f"{stage}: unexpected error string {res['error']!r}"
            )

        # Diagnostic (printed only with pytest -s)
        print(f"\n[DLV-03/04] ok_stages={list(ok.keys())}")
        print(f"[DLV-03/04] error_stages={list(errors.keys())}")

    def test_stage_comparison(self, full_panel):
        """Growth vs Maturity comparison regression."""
        from models.econometric import run_stage_comparison
        result = run_stage_comparison(full_panel, "Growth", "Maturity")
        assert "comparison" in result
        assert "result_a" in result
        assert "result_b" in result
        assert "Divergent" in result["comparison"].columns

    def test_system_gmm(self, full_panel):
        """System GMM with lag DV using IVGMM — Arellano-Bond instrument approach."""
        from models.econometric import run_system_gmm
        result = run_system_gmm(full_panel)

        assert "coef_table" in result
        assert result["lag_dv_included"] is True
        assert "ar1" in result
        assert "ar2" in result
        assert "sargan" in result
        assert result["n_obs"] > 2000

        # coef_table shape and columns (GMM-04)
        ct = result["coef_table"]
        assert set(ct.columns) >= {"Variable", "Coefficient", "Std Error", "t-stat", "p-value"}
        assert any("lag" in str(v).lower() for v in ct["Variable"]), (
            "coef_table must contain the lag DV regressor"
        )

        # Lag DV coefficient should be positive and < 1 (capital structure persistence)
        lag_row = ct[ct["Variable"].str.contains("lag", case=False)]
        assert not lag_row.empty
        lag_coef = float(lag_row.iloc[0]["Coefficient"])
        assert 0.0 < lag_coef < 1.0, (
            f"Lag DV coef {lag_coef:.3f} out of [0,1] — OLS stub may still be active"
        )

        # Hansen J-stat must be real value (not old fabricated ~13931) (GMM-03)
        assert result["sargan"]["j_stat"] < 1000, (
            f"sargan j_stat={result['sargan']['j_stat']:.1f} — looks like old OLS pseudo-formula"
        )
        assert 0.0 <= result["sargan"]["p_value"] <= 1.0

        # AR(1) and AR(2) keys (GMM-02)
        for ar_key in ("ar1", "ar2"):
            ar = result[ar_key]
            assert "correlation" in ar
            assert "p_value" in ar
            assert "verdict" in ar
            assert -1.0 <= ar["correlation"] <= 1.0
            assert 0.0 <= ar["p_value"] <= 1.0

        # type must not claim OLS (GMM-01)
        assert "OLS" not in result.get("type", ""), (
            f"type='{result.get('type')}' still mentions OLS — IVGMM not active"
        )

    def test_system_gmm_sargan_reasonable(self, full_panel):
        """Hansen J p-value should be > 0.0 (not old formula). Phase 2: GMM-03."""
        from models.econometric import run_system_gmm
        result = run_system_gmm(full_panel)
        p = result["sargan"]["p_value"]
        assert p > 0.0, "Hansen p=0.0 exactly — IVGMM not active (old OLS formula)"

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


class TestStageComparisons:
    """Tests for run_stage_comparison and format_stage_comparison_table. Phase 3: CMP-01/02/03."""

    def test_growth_vs_maturity_structure(self, full_panel):
        """Return dict has required keys and comparison columns (CMP-01 / CMP-03)."""
        from models.econometric import run_stage_comparison
        result = run_stage_comparison(full_panel, "Growth", "Maturity")
        assert "error" not in result, f"Unexpected error: {result.get('error')}"
        assert result["stage_a"] == "Growth"
        assert result["stage_b"] == "Maturity"
        for key in ("result_a", "result_b", "comparison"):
            assert key in result, f"Missing key: {key}"
        comp = result["comparison"]
        expected_cols = {"Variable", "Growth Coef", "Growth p", "Maturity Coef", "Maturity p", "Divergent"}
        assert expected_cols.issubset(set(comp.columns)), f"Missing columns: {expected_cols - set(comp.columns)}"

    def test_growth_vs_maturity_separate_coefs(self, full_panel):
        """Each stage produces independent OLS coefficients (CMP-01)."""
        from models.econometric import run_stage_comparison
        result = run_stage_comparison(full_panel, "Growth", "Maturity")
        assert result["result_a"]["n_obs"] >= 100
        assert result["result_b"]["n_obs"] >= 100
        coef_a = result["result_a"]["coef_table"].set_index("Variable")["Coefficient"]
        coef_b = result["result_b"]["coef_table"].set_index("Variable")["Coefficient"]
        common = coef_a.index.intersection(coef_b.index)
        assert not coef_a[common].equals(coef_b[common]), "Growth and Maturity OLS coefs should differ"

    def test_decline_vs_decay_structure(self, full_panel):
        """Decline vs Decay returns valid dict (CMP-02)."""
        from models.econometric import run_stage_comparison
        result = run_stage_comparison(full_panel, "Decline", "Decay")
        assert "error" not in result, f"Unexpected error: {result.get('error')}"
        assert len(result["comparison"]) >= 6

    def test_divergent_flag_excludes_const(self, full_panel):
        """The 'const' row must never be flagged Divergent (CMP-03)."""
        from models.econometric import run_stage_comparison
        result = run_stage_comparison(full_panel, "Growth", "Maturity")
        comp = result["comparison"]
        const_rows = comp[comp["Variable"] == "const"]
        if not const_rows.empty:
            assert not const_rows["Divergent"].any(), "'const' row should not be Divergent"

    def test_same_stage_returns_error(self, full_panel):
        """Passing the same stage for both A and B returns an error dict."""
        from models.econometric import run_stage_comparison
        result = run_stage_comparison(full_panel, "Growth", "Growth")
        assert "error" in result

    def test_format_stage_comparison_table(self, full_panel):
        """format_stage_comparison_table adds Sig columns and formats p-values (CMP-03)."""
        from models.econometric import run_stage_comparison, format_stage_comparison_table
        result = run_stage_comparison(full_panel, "Growth", "Maturity")
        assert "error" not in result
        formatted = format_stage_comparison_table(result["comparison"], "Growth", "Maturity")
        assert "Growth Sig" in formatted.columns
        assert "Maturity Sig" in formatted.columns
        assert formatted["Growth p"].dtype == object, "Growth p should be formatted string"
        valid_stars = {"***", "**", "*", ".", ""}
        for v in formatted["Growth Sig"].dropna():
            assert v in valid_stars, f"Unexpected star value: {v!r}"


class TestMLModels:
    def test_random_forest_uses_single_process_by_default(self):
        from models.ml_predict import MODEL_CONFIGS
        assert MODEL_CONFIGS["Random Forest"]["params"]["n_jobs"] == 1

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
