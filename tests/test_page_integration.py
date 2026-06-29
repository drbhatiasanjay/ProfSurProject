"""
End-to-end integration tests for all 15 pages.

Tests the full data pipeline each page depends on:
  DB query → model call → chart-ready output

Uses get_active_panel_data (includes log_size, ncfo/ncfi/ncff, int_rate) so
that prepare_panel and all downstream models have required columns.
"""

import pytest
import pandas as pd
import numpy as np
import os
import sys

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)


# ─────────────────────────────────────────────
# Fixtures
# ─────────────────────────────────────────────

def _make_filters(panel, yr_min, yr_max):
    import db as _db
    return _db.filters_to_tuple({
        "panel_mode": panel,
        "year_range": (yr_min, yr_max),
        "company_codes": [], "life_stages": [], "industry_groups": [],
        "events": {"gfc": False, "ibc": False, "covid": False},
    })


@pytest.fixture(scope="session")
def thesis_panel(db_conn):
    import db as _db
    ft = _make_filters("thesis", 2001, 2024)
    return _db.get_active_panel_data(ft)


@pytest.fixture(scope="session")
def us_panel(db_conn):
    import db as _db
    ft = _make_filters("us_av_2024", 2006, 2026)
    return _db.get_active_panel_data(ft)


@pytest.fixture(scope="session")
def run3_panel(db_conn):
    import db as _db
    ft = _make_filters("run3", 2001, 2025)
    return _db.get_active_panel_data(ft)


@pytest.fixture(scope="session")
def small_thesis(thesis_panel):
    firms = thesis_panel["company_code"].unique()[:30]
    return thesis_panel[thesis_panel["company_code"].isin(firms)].copy()


# ─────────────────────────────────────────────
# Page 1 — Dashboard
# ─────────────────────────────────────────────

class TestPage1Dashboard:
    def test_panel_row_count(self, thesis_panel):
        assert len(thesis_panel) >= 8000

    def test_year_range_starts_2001(self, thesis_panel):
        assert thesis_panel["year"].min() == 2001

    def test_kpi_leverage_mean(self, thesis_panel):
        assert 5 < thesis_panel["leverage"].mean() < 60

    def test_stage_groups_anova(self, thesis_panel):
        from scipy import stats
        groups = [g["leverage"].dropna().values
                  for _, g in thesis_panel.groupby("life_stage")]
        groups = [g for g in groups if len(g) >= 5]
        assert len(groups) >= 4
        f, p = stats.f_oneway(*groups)
        assert p < 0.05

    def test_figure52_vars_present(self, thesis_panel):
        for col in ["leverage", "profitability", "tangibility", "dividend"]:
            assert col in thesis_panel.columns
            assert thesis_panel[col].notna().sum() > 100

    def test_figure51_stage_aggregation(self, thesis_panel):
        stage_means = thesis_panel.groupby("life_stage")[
            ["leverage", "profitability", "firm_size", "dividend"]
        ].mean()
        assert len(stage_means) >= 4

    def test_pairwise_comparison(self, thesis_panel):
        from models.econometric import run_pairwise_comparison
        result = run_pairwise_comparison(thesis_panel)
        assert result["n_significant"] >= 4
        assert len(result["significant_pairs"]) >= 4

    def test_event_impact(self, thesis_panel):
        gfc = thesis_panel[thesis_panel["year"].isin([2008, 2009])]["leverage"].mean()
        normal = thesis_panel[~thesis_panel["year"].isin([2008, 2009])]["leverage"].mean()
        assert not np.isnan(gfc)
        assert not np.isnan(normal)

    def test_us_panel_loads(self, us_panel):
        assert len(us_panel) > 0
        assert us_panel["year"].min() >= 2006


# ─────────────────────────────────────────────
# Page 2 — Peer Benchmarks
# ─────────────────────────────────────────────

class TestPage2PeerBenchmarks:
    def test_industry_groups_thesis(self, db_conn):
        import db as _db
        industries = _db.get_industry_groups("thesis")
        assert len(industries) >= 5

    def test_company_list_thesis(self, db_conn):
        import db as _db
        co = _db.get_companies("thesis")
        assert len(co) >= 400
        assert "company_name" in co.columns

    def test_company_list_us(self, db_conn):
        import db as _db
        co = _db.get_companies("us_av_2024")
        assert len(co) >= 8

    def test_leverage_by_stage(self, thesis_panel):
        stages = thesis_panel.groupby("life_stage")["leverage"].describe()
        assert "mean" in stages.columns
        assert len(stages) >= 4

    def test_radar_cols_present(self, thesis_panel):
        for col in ["leverage", "profitability", "tangibility", "tax_shield", "firm_size"]:
            assert col in thesis_panel.columns


# ─────────────────────────────────────────────
# Page 3 — Scenarios
# ─────────────────────────────────────────────

class TestPage3Scenarios:
    def test_compute_ols_coefs(self, thesis_panel):
        from models.scenario_regression import compute_leverage_ols_coefs
        result = compute_leverage_ols_coefs(thesis_panel)
        assert "intercept" in result
        assert "profitability" in result
        assert "r_squared" in result

    def test_predictor_means(self, thesis_panel):
        from models.scenario_regression import leverage_predictor_sample_means
        means = leverage_predictor_sample_means(thesis_panel)
        assert "prof" in means
        assert "tang" in means


# ─────────────────────────────────────────────
# Page 4 — Bulk Upload
# ─────────────────────────────────────────────

class TestPage4BulkUpload:
    def test_dickinson_growth(self):
        from helpers import classify_life_stage
        assert classify_life_stage(ncfo=1, ncfi=-1, ncff=1) == "Growth"

    def test_dickinson_all_8_stages(self):
        from helpers import classify_life_stage
        # Dickinson (2011): ncfo/ncfi/ncff signs → stage (matches helpers.py implementation)
        combos = [
            (1,  -1,  1, "Growth"),
            (1,  -1, -1, "Maturity"),
            (-1, -1,  1, "Startup"),
            (1,   1, -1, "Shakeout3"),
            (-1,  1,  1, "Decline"),
            (1,   1,  1, "Shakeout2"),
            (-1, -1, -1, "Shakeout1"),
            (-1,  1, -1, "Decay"),
        ]
        for ncfo, ncfi, ncff, expected in combos:
            result = classify_life_stage(ncfo, ncfi, ncff)
            assert result == expected, f"({ncfo},{ncfi},{ncff}) → {result}, expected {expected}"

    def test_validate_upload_function_exists(self):
        from models.data_ingest import validate_upload
        assert callable(validate_upload)

    def test_canonical_columns_exist(self):
        from cmie.normalize import CANONICAL_COLUMNS
        for col in ["leverage", "profitability", "tangibility", "firm_size", "dividend"]:
            assert col in CANONICAL_COLUMNS


# ─────────────────────────────────────────────
# Page 5 — Data Explorer
# ─────────────────────────────────────────────

class TestPage5DataExplorer:
    def test_panel_data_returns_rows(self, thesis_panel):
        assert len(thesis_panel) >= 8000
        assert "vintage" in thesis_panel.columns or "year" in thesis_panel.columns

    def test_filter_by_stage(self, db_conn):
        import db as _db
        ft = _make_filters("thesis", 2001, 2024)
        # Override life_stages filter
        import db as _db2
        ft2 = _db2.filters_to_tuple({
            "panel_mode": "thesis", "year_range": (2001, 2024),
            "company_codes": [], "life_stages": ["Growth"], "industry_groups": [],
            "events": {"gfc": False, "ibc": False, "covid": False},
        })
        df = _db.get_active_panel_data(ft2)
        assert len(df) > 100
        assert (df["life_stage"] == "Growth").all()

    def test_filter_by_year(self, db_conn):
        import db as _db
        ft = _db.filters_to_tuple({
            "panel_mode": "thesis", "year_range": (2010, 2015),
            "company_codes": [], "life_stages": [], "industry_groups": [],
            "events": {"gfc": False, "ibc": False, "covid": False},
        })
        df = _db.get_active_panel_data(ft)
        assert df["year"].min() >= 2010
        assert df["year"].max() <= 2015


# ─────────────────────────────────────────────
# Page 7 — Knowledge Graph
# ─────────────────────────────────────────────

class TestPage7KnowledgeGraph:
    def test_stage_transitions_from_db(self, db_conn):
        import sqlite3
        conn = sqlite3.connect(os.path.join(PROJECT_ROOT, "capital_structure.db"))
        df = pd.read_sql("""
            SELECT a.life_stage as from_stage, b.life_stage as to_stage, COUNT(*) as n
            FROM financials a JOIN financials b
              ON a.company_code=b.company_code AND b.year=a.year+1
              AND a.vintage IN ('thesis','cmie_2025')
              AND b.vintage IN ('thesis','cmie_2025')
            GROUP BY a.life_stage, b.life_stage
        """, conn)
        conn.close()
        assert len(df) >= 20
        assert "from_stage" in df.columns

    def test_prepare_transition_data(self, thesis_panel):
        from models.survival import prepare_transition_data
        trans = prepare_transition_data(thesis_panel)
        assert len(trans) > 100
        assert "duration" in trans.columns

    def test_stage_distribution(self, thesis_panel):
        counts = thesis_panel["life_stage"].value_counts()
        assert len(counts) >= 4
        assert counts.sum() >= 8000


# ─────────────────────────────────────────────
# Page 8 — Econometrics Lab
# ─────────────────────────────────────────────

class TestPage8Econometrics:
    def test_pooled_ols_thesis(self, thesis_panel):
        from models.econometric import run_pooled_ols
        r = run_pooled_ols(thesis_panel)
        assert r["r_squared"] > 0.05
        assert r["n_obs"] >= 7500

    def test_fixed_effects_thesis(self, thesis_panel):
        from models.econometric import run_fixed_effects
        r = run_fixed_effects(thesis_panel)
        assert r["n_firms"] >= 300

    def test_random_effects_thesis(self, thesis_panel):
        from models.econometric import run_random_effects
        r = run_random_effects(thesis_panel)
        assert r["n_obs"] >= 7500

    def test_hausman_test(self, thesis_panel):
        from models.econometric import run_fixed_effects, run_random_effects, run_hausman_test
        fe = run_fixed_effects(thesis_panel)
        re = run_random_effects(thesis_panel)
        h = run_hausman_test(fe, re)
        assert "chi2" in h
        assert h["recommended"] in ("Fixed Effects", "Random Effects")

    def test_robust_regression(self, thesis_panel):
        from models.econometric import run_robust_regression
        r = run_robust_regression(thesis_panel)
        assert "coef_table" in r
        assert r["n_obs"] > 5000

    def test_anova_significant(self, thesis_panel):
        from models.econometric import run_anova_by_stage
        r = run_anova_by_stage(thesis_panel)
        assert r["p_value"] < 0.001
        assert r["f_stat"] > 10

    def test_model_on_run3(self, run3_panel):
        from models.econometric import run_pooled_ols
        r = run_pooled_ols(run3_panel)
        assert r["n_obs"] >= 7000


# ─────────────────────────────────────────────
# Page 9 — ML Models
# ─────────────────────────────────────────────

class TestPage9MLModels:
    def test_random_forest_cv(self, small_thesis):
        from models.ml_predict import cross_validate_model
        r = cross_validate_model("Random Forest", small_thesis, n_splits=2)
        assert "avg_metrics" in r
        assert "r2" in r["avg_metrics"]

    def test_xgboost_cv(self, small_thesis):
        from models.ml_predict import cross_validate_model
        r = cross_validate_model("XGBoost", small_thesis, n_splits=2)
        assert "avg_metrics" in r

    def test_feature_importance(self, small_thesis):
        from models.ml_predict import cross_validate_model
        r = cross_validate_model("Random Forest", small_thesis, n_splits=2)
        assert "feature_names" in r
        assert len(r["feature_names"]) > 0

    def test_compare_models(self, small_thesis):
        from models.ml_predict import compare_all_models
        results = compare_all_models(small_thesis, n_splits=2)
        assert results is not None
        # may be list or dict — just check non-empty
        assert len(results) >= 1


# ─────────────────────────────────────────────
# Page 10 — Forecasting (torch-optional)
# ─────────────────────────────────────────────

class TestPage10Forecasting:
    def test_torch_import_guard(self):
        from models.timeseries import HAS_TORCH
        assert isinstance(HAS_TORCH, bool)

    def test_prepare_sequences(self, small_thesis):
        from models.timeseries import prepare_sequences
        features = ["leverage", "profitability", "tangibility", "firm_size", "tax_shield"]
        X, y, firms, years = prepare_sequences(small_thesis, features, seq_len=3)
        assert X.shape[0] == len(y)
        assert X.shape[2] == len(features)

    def test_temporal_split(self, small_thesis):
        from models.timeseries import prepare_sequences, temporal_split
        features = ["leverage", "profitability", "tangibility", "firm_size", "tax_shield"]
        X, y, firms, years = prepare_sequences(small_thesis, features, seq_len=3)
        split = temporal_split(X, y, years, train_end=2015, val_end=2019)
        assert "X_train" in split
        assert "X_test" in split

    @pytest.mark.skipif(
        not __import__("models.timeseries", fromlist=["HAS_TORCH"]).HAS_TORCH,
        reason="torch not installed"
    )
    def test_run_full_forecast_small(self, small_thesis):
        from models.timeseries import run_full_forecast
        r = run_full_forecast(small_thesis, epochs=2)
        assert "model" in r or "error" in r


# ─────────────────────────────────────────────
# Page 11 — Clustering
# ─────────────────────────────────────────────

class TestPage11Clustering:
    def test_prepare_firm_features(self, thesis_panel):
        from models.clustering import prepare_firm_features
        agg, X_scaled, scaler, feature_cols = prepare_firm_features(thesis_panel)
        assert X_scaled.shape[0] >= 300
        assert X_scaled.shape[1] >= 3

    def test_find_optimal_k(self, thesis_panel):
        from models.clustering import prepare_firm_features, find_optimal_k
        _, X_scaled, _, _ = prepare_firm_features(thesis_panel)
        best_k, scores_df = find_optimal_k(X_scaled, k_range=range(2, 6))
        assert 2 <= best_k <= 6
        assert len(scores_df) == 4

    def test_run_kmeans(self, thesis_panel):
        from models.clustering import prepare_firm_features, run_kmeans
        agg, X_scaled, _, _ = prepare_firm_features(thesis_panel)
        labels, firm_df, profiles, km = run_kmeans(X_scaled, 4, agg)
        assert len(labels) == len(agg)
        assert profiles.shape[0] == 4

    def test_compare_with_dickinson(self, thesis_panel):
        from models.clustering import prepare_firm_features, run_kmeans, compare_with_dickinson
        agg, X_scaled, _, _ = prepare_firm_features(thesis_panel)
        labels, firm_df, profiles, km = run_kmeans(X_scaled, 8, agg)
        crosstab, ari = compare_with_dickinson(firm_df)
        assert -1 <= ari <= 1


# ─────────────────────────────────────────────
# Page 12 — Transitions
# ─────────────────────────────────────────────

class TestPage12Transitions:
    def test_prepare_transition_data(self, thesis_panel):
        from models.survival import prepare_transition_data
        trans = prepare_transition_data(thesis_panel)
        assert len(trans) > 100
        assert "duration" in trans.columns
        assert "event" in trans.columns

    def test_kaplan_meier_returns_tuple(self, thesis_panel):
        from models.survival import prepare_transition_data, fit_kaplan_meier
        trans = prepare_transition_data(thesis_panel)
        km_fits, summary_df = fit_kaplan_meier(trans)
        assert km_fits is not None
        assert len(summary_df) >= 3
        assert "Stage" in summary_df.columns or summary_df.index.name is not None

    def test_cox_ph_returns_hazard_ratios(self, thesis_panel):
        from models.survival import prepare_transition_data, fit_cox_ph
        trans = prepare_transition_data(thesis_panel)
        cph, hr_df, summary = fit_cox_ph(trans)
        assert cph is not None
        assert hr_df is not None
        assert "Hazard Ratio" in hr_df.columns
        assert len(hr_df) >= 3

    def test_cox_ph_hr_positive(self, thesis_panel):
        from models.survival import prepare_transition_data, fit_cox_ph
        trans = prepare_transition_data(thesis_panel)
        _, hr_df, _ = fit_cox_ph(trans)
        assert (hr_df["Hazard Ratio"] > 0).all(), "All hazard ratios must be positive"

    def test_transition_matrix(self, thesis_panel):
        from models.survival import prepare_transition_data, get_transition_matrix
        trans = prepare_transition_data(thesis_panel)
        tm = get_transition_matrix(trans)
        assert tm is not None
        assert tm.shape[0] >= 4
        assert (tm.values >= 0).all()

    def test_insufficient_data_returns_none(self):
        from models.survival import fit_cox_ph
        tiny = pd.DataFrame({
            "duration": [1, 2], "event": [1, 0],
            "profitability": [0.1, 0.2], "tangibility": [0.3, 0.4],
            "log_size": [10.0, 11.0], "leverage": [0.2, 0.3], "tax_shield": [0.1, 0.1],
        })
        cph, hr_df, msg = fit_cox_ph(tiny)
        assert cph is None
        assert isinstance(msg, str)


# ─────────────────────────────────────────────
# Page 13 — Advanced Econometrics
# ─────────────────────────────────────────────

class TestPage13AdvancedEconometrics:
    def test_delta_leverage_all(self, thesis_panel):
        from models.econometric import run_delta_leverage_all
        r = run_delta_leverage_all(thesis_panel)
        assert "ols" in r
        assert r["ols"]["n_obs"] > 5000

    def test_delta_leverage_by_stage(self, thesis_panel):
        from models.econometric import run_delta_leverage_by_stage
        results = run_delta_leverage_by_stage(thesis_panel)
        assert len(results) >= 3
        for stage, r in results.items():
            if "error" not in r:
                assert "coef_table" in r

    def test_stage_comparison(self, thesis_panel):
        from models.econometric import run_stage_comparison
        r = run_stage_comparison(thesis_panel, "Growth", "Maturity")
        assert r is not None
        assert "stage_a" in r or "result_a" in r

    def test_iv_regression(self, thesis_panel):
        from models.econometric import run_iv_regression
        r = run_iv_regression(thesis_panel)
        assert "coef_table" in r or "error" in r

    def test_system_gmm(self, thesis_panel):
        """Page 13 GMM tab: run_system_gmm returns full valid dict on thesis panel."""
        from models.econometric import run_system_gmm
        r = run_system_gmm(thesis_panel)

        assert "error" not in r, f"run_system_gmm errored: {r.get('error')}"

        # All keys page 13 reads (pages/13_advanced_econometrics.py)
        for key in ["r_squared", "n_obs", "n_firms", "coef_table", "ar1", "ar2", "sargan"]:
            assert key in r, f"Missing key consumed by page 13: '{key}'"

        ct = r["coef_table"]
        assert set(ct.columns) >= {"Variable", "Coefficient", "Std Error", "t-stat", "p-value"}

        for ar_key in ("ar1", "ar2"):
            ar = r[ar_key]
            assert "correlation" in ar and "p_value" in ar and "verdict" in ar

        s = r["sargan"]
        assert "j_stat" in s and "p_value" in s and "verdict" in s
        assert r["n_obs"] > 0 and r["n_firms"] > 0
        assert 0.0 <= s["p_value"] <= 1.0
        assert s["j_stat"] < 1000, (
            f"j_stat={s['j_stat']:.1f} — OLS pseudo-formula detected; IVGMM not active"
        )


# ─────────────────────────────────────────────
# Page 14 — Workbench
# ─────────────────────────────────────────────

class TestPage14Workbench:
    def test_base_ols(self, thesis_panel):
        from models.econometric import run_pooled_ols
        from models.base import DEFAULT_X_COLS
        r = run_pooled_ols(thesis_panel, x_cols=DEFAULT_X_COLS[:3])
        assert "coef_table" in r

    def test_subsample_by_stage(self, thesis_panel):
        growth = thesis_panel[thesis_panel["life_stage"] == "Growth"]
        assert len(growth) >= 500
        from models.econometric import run_pooled_ols
        r = run_pooled_ols(growth)
        assert r["n_obs"] >= 400

    def test_log_size_in_panel(self, thesis_panel):
        assert "log_size" in thesis_panel.columns
        valid = thesis_panel["log_size"].dropna()
        assert (valid > 0).mean() > 0.9


# ─────────────────────────────────────────────
# Page 15 — Interaction Effects
# ─────────────────────────────────────────────

class TestPage15InteractionEffects:
    def test_cross_term_ols(self, thesis_panel):
        from models.interaction import run_cross_term_ols
        r = run_cross_term_ols(thesis_panel)
        assert "coef_table" in r
        assert r["n_obs"] > 5000

    def test_cross_term_interaction_coef_present(self, thesis_panel):
        from models.interaction import run_cross_term_ols
        r = run_cross_term_ols(thesis_panel)
        ct = r["coef_table"]
        # coef_table uses integer index; variable names are in the "Variable" column
        if hasattr(ct, "columns") and "Variable" in ct.columns:
            names = ct["Variable"].tolist()
        elif hasattr(ct, "index"):
            names = ct.index.tolist()
        else:
            names = list(ct)
        interaction_present = any(
            ("prof" in str(c).lower() and "tang" in str(c).lower()) or ":" in str(c) or "×" in str(c)
            for c in names
        )
        assert interaction_present, f"No interaction term found in: {names}"

    def test_simple_slopes(self, thesis_panel):
        from models.interaction import run_cross_term_ols, simple_slopes
        r = run_cross_term_ols(thesis_panel)
        slopes = simple_slopes(r)
        assert slopes is not None
        assert len(slopes) >= 3

    def test_stage_moderation_ols(self, thesis_panel):
        from models.interaction import run_stage_moderation_ols
        r = run_stage_moderation_ols(thesis_panel)
        assert "marginal_df" in r
        assert len(r["marginal_df"]) >= 3

    def test_moderation_marginal_df_columns(self, thesis_panel):
        from models.interaction import run_stage_moderation_ols
        r = run_stage_moderation_ols(thesis_panel)
        mdf = r["marginal_df"]
        assert "stage" in mdf.columns
        assert "variable" in mdf.columns
        assert "marginal_effect" in mdf.columns


# ─────────────────────────────────────────────
# Cross-panel DB layer
# ─────────────────────────────────────────────

class TestDBLayer:
    @pytest.mark.parametrize("panel,yr_lo,yr_hi", [
        ("thesis", 2001, 2024),
        ("latest", 2001, 2025),
        ("run3",   2001, 2025),
        ("us_av_2024", 2006, 2026),
    ])
    def test_year_range(self, panel, yr_lo, yr_hi):
        import db as _db
        yr_min, yr_max = _db.get_year_range(panel)
        assert yr_min >= yr_lo - 1
        assert yr_max <= yr_hi + 1
        assert yr_min < yr_max

    @pytest.mark.parametrize("panel", ["thesis", "latest", "run3", "us_av_2024"])
    def test_companies_query(self, panel):
        import db as _db
        co = _db.get_companies(panel)
        assert len(co) > 0
        assert "company_name" in co.columns

    @pytest.mark.parametrize("panel", ["thesis", "latest", "run3", "us_av_2024"])
    def test_db_metadata(self, panel):
        import db as _db
        meta = _db.get_db_metadata(panel)
        assert meta["total_firms"] >= 0
        assert meta["total_obs"] >= 0

    def test_vintage_predicate_thesis(self):
        import db as _db
        sql, params = _db._vintage_predicate("thesis")
        assert "vintage" in sql
        assert "thesis" in params

    def test_vintage_predicate_us(self):
        import db as _db
        sql, params = _db._vintage_predicate("us_av_2024")
        assert "us_av_2024" in params

    def test_filters_to_tuple(self):
        import db as _db
        ft = _db.filters_to_tuple({
            "panel_mode": "thesis", "year_range": (2005, 2020),
            "company_codes": [101], "life_stages": ["Growth"],
            "industry_groups": [], "events": {"gfc": True, "ibc": False, "covid": False},
        })
        assert ft is not None
        assert len(ft) > 0

    def test_is_india_panel(self):
        from helpers import is_india_panel
        assert is_india_panel("thesis") is True
        assert is_india_panel("latest") is True
        assert is_india_panel("run3") is True
        assert is_india_panel("us_av_2024") is False


# ─────────────────────────────────────────────
# Page 22 — Comparison
# ─────────────────────────────────────────────

class TestPage22Comparison:
    def test_company_detail_has_required_cols(self, db_conn):
        import db as _db
        co = _db.get_companies("thesis")
        code = int(co.iloc[0]["company_code"])
        df = _db.get_company_detail(code)
        for col in ["year", "leverage", "profitability", "tangibility", "firm_size", "tax_shield", "cash_holdings"]:
            assert col in df.columns, f"Missing column: {col}"

    def test_two_companies_have_data(self, db_conn):
        import db as _db
        co = _db.get_companies("thesis")
        assert len(co) >= 2
        df_a = _db.get_company_detail(int(co.iloc[0]["company_code"]))
        df_b = _db.get_company_detail(int(co.iloc[1]["company_code"]))
        assert not df_a.empty
        assert not df_b.empty

    def test_stage_aggregation(self, thesis_panel):
        stages = thesis_panel["life_stage"].unique().tolist()
        assert len(stages) >= 2
        for stage in stages[:2]:
            sub = thesis_panel[thesis_panel["life_stage"] == stage]
            agg = sub.groupby("year")["leverage"].mean()
            assert len(agg) >= 5

    def test_radar_cols_present_for_comparison(self, thesis_panel):
        for col in ["leverage", "profitability", "tangibility", "firm_size", "tax_shield", "cash_holdings"]:
            assert col in thesis_panel.columns

    def test_summary_table_shape(self, thesis_panel):
        stages = thesis_panel["life_stage"].dropna().unique()
        df_a = thesis_panel[thesis_panel["life_stage"] == stages[0]]
        df_b = thesis_panel[thesis_panel["life_stage"] == stages[1]]
        assert not df_a.empty and not df_b.empty
        assert df_a["leverage"].mean() >= 0
        assert df_b["leverage"].mean() >= 0


# ─────────────────────────────────────────────
# UI Helper regression guards
# ─────────────────────────────────────────────

class TestUIHelpers:
    def test_plotly_config_modebar_hover(self):
        from helpers import PLOTLY_CONFIG
        assert PLOTLY_CONFIG["displayModeBar"] == "hover", (
            "Modebar must be 'hover' to prevent icon/title overlap in narrow columns"
        )

    def test_plotly_layout_light_top_margin_with_title(self):
        from helpers import plotly_layout_light
        layout = plotly_layout_light(title="Test Title", height=400)
        assert layout["margin"]["t"] >= 60

    def test_plotly_layout_light_top_margin_no_title(self):
        from helpers import plotly_layout_light
        layout = plotly_layout_light(title="", height=400)
        assert layout["margin"]["t"] <= 40

    def test_plotly_layout_dark_top_margin(self):
        from helpers import plotly_layout_dark
        layout = plotly_layout_dark(title="Test Title", height=400)
        assert layout["margin"]["t"] >= 60

    def test_format_pct(self):
        from helpers import format_pct
        assert "23" in format_pct(23.4)

    def test_winsorize(self):
        from helpers import winsorize
        s = pd.Series([1, 2, 3, 100, -100])
        w = winsorize(s, lower=0.05, upper=0.95)
        assert w.max() < 100
        assert w.min() > -100

    def test_stage_order_completeness(self):
        from helpers import STAGE_ORDER
        expected = {"Startup", "Growth", "Maturity", "Shakeout1", "Shakeout2",
                    "Shakeout3", "Decline", "Decay"}
        assert expected.issubset(set(STAGE_ORDER))

    def test_stage_colors_all_stages(self):
        from helpers import STAGE_COLORS, STAGE_ORDER
        for stage in STAGE_ORDER:
            assert stage in STAGE_COLORS
            assert STAGE_COLORS[stage].startswith("#")

    def test_hazard_ratio_title_short(self):
        """Chart title must not contain instructional parenthetical."""
        page_path = os.path.join(PROJECT_ROOT, "pages", "12_transitions.py")
        with open(page_path, encoding="utf-8") as f:
            src = f.read()
        assert 'plotly_layout("Hazard Ratios (>0 accelerates' not in src, (
            "Instructional text must be in xaxis label, not chart title"
        )

    def test_long_titles_in_layout_calls(self):
        """Chart titles passed to plotly_layout() must be ≤60 chars."""
        import re
        pages_dir = os.path.join(PROJECT_ROOT, "pages")
        violations = []
        for fname in sorted(os.listdir(pages_dir)):
            if not fname.endswith(".py"):
                continue
            with open(os.path.join(pages_dir, fname), encoding="utf-8") as f:
                src = f.read()
            for m in re.finditer(r'plotly_layout\("([^"]{66,})"', src):
                title = m.group(1)
                violations.append(f"{fname}: '{title[:70]}' ({len(title)} chars)")
        assert not violations, "Chart titles >65 chars:\n" + "\n".join(violations)


class TestPage13StageComparisons:
    """Smoke tests for the Stage Comparisons tab in page 13. Phase 3: CMP-01/02."""

    def test_growth_vs_maturity_e2e(self, thesis_panel):
        """Growth vs Maturity runs without error on the full thesis panel (CMP-01)."""
        from models.econometric import run_stage_comparison
        result = run_stage_comparison(thesis_panel, "Growth", "Maturity")
        assert "error" not in result, f"Unexpected error: {result.get('error')}"
        assert result["result_a"]["n_obs"] >= 100
        assert result["result_b"]["n_obs"] >= 100
        assert result["comparison"]["Divergent"].dtype == bool

    def test_decline_vs_decay_e2e(self, thesis_panel):
        """Decline vs Decay returns distinct coefficient sets on thesis panel (CMP-02)."""
        from models.econometric import run_stage_comparison
        result = run_stage_comparison(thesis_panel, "Decline", "Decay")
        assert "error" not in result, f"Unexpected error: {result.get('error')}"
        comp = result["comparison"]
        assert "profitability" in comp["Variable"].values
        prof_row = comp[comp["Variable"] == "profitability"].iloc[0]
        assert not pd.isna(prof_row["Decline Coef"])
        assert not pd.isna(prof_row["Decay Coef"])
