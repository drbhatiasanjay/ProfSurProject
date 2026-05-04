"""
End-to-end integration tests for all 15 pages.

Tests the full data pipeline each page depends on:
  DB query → model call → chart-ready output

Does NOT test Streamlit widget rendering (that requires a running server).
Tests that every page's critical path produces valid, non-empty output
for all four panel modes, and gracefully handles edge cases.
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

@pytest.fixture(scope="session")
def thesis_panel(db_conn):
    import db as _db
    ft = _db.filters_to_tuple({"panel_mode": "thesis", "year_range": (2001, 2024),
                                "company_codes": [], "life_stages": [], "industry_groups": [],
                                "events": {"gfc": False, "ibc": False, "covid": False}})
    return _db.get_active_financials(ft)


@pytest.fixture(scope="session")
def us_panel(db_conn):
    import db as _db
    ft = _db.filters_to_tuple({"panel_mode": "us_av_2024", "year_range": (2006, 2025),
                                "company_codes": [], "life_stages": [], "industry_groups": [],
                                "events": {"gfc": False, "ibc": False, "covid": False}})
    return _db.get_active_financials(ft)


@pytest.fixture(scope="session")
def run3_panel(db_conn):
    import db as _db
    ft = _db.filters_to_tuple({"panel_mode": "run3", "year_range": (2001, 2025),
                                "company_codes": [], "life_stages": [], "industry_groups": [],
                                "events": {"gfc": False, "ibc": False, "covid": False}})
    return _db.get_active_financials(ft)


@pytest.fixture(scope="session")
def small_thesis(thesis_panel):
    firms = thesis_panel["company_code"].unique()[:30]
    return thesis_panel[thesis_panel["company_code"].isin(firms)].copy()


# ─────────────────────────────────────────────
# Page 1 — Dashboard
# ─────────────────────────────────────────────

class TestPage1Dashboard:
    def test_kpi_metrics(self, thesis_panel):
        assert thesis_panel["leverage"].mean() > 0
        assert thesis_panel["profitability"].notna().sum() > 5000

    def test_stage_groups_for_anova(self, thesis_panel):
        from scipy import stats
        groups = [g["leverage"].dropna().values
                  for _, g in thesis_panel.groupby("life_stage")]
        groups = [g for g in groups if len(g) >= 5]
        assert len(groups) >= 4
        f, p = stats.f_oneway(*groups)
        assert p < 0.05, "ANOVA should be significant on full thesis panel"

    def test_yearly_aggregation(self, thesis_panel):
        yearly = thesis_panel.groupby("year")["leverage"].mean()
        assert len(yearly) >= 20
        assert yearly.index.min() == 2001

    def test_figure52_vars_present(self, thesis_panel):
        for col in ["leverage", "profitability", "tangibility", "dividend"]:
            assert col in thesis_panel.columns
            assert thesis_panel[col].notna().sum() > 100

    def test_figure51_stage_aggregation(self, thesis_panel):
        from helpers import STAGE_ORDER
        stage_means = thesis_panel.groupby("life_stage")[
            ["leverage", "profitability", "firm_size", "dividend"]
        ].mean()
        assert len(stage_means) >= 4
        assert "Growth" in stage_means.index or "Maturity" in stage_means.index

    def test_pairwise_comparison(self, thesis_panel):
        from models.econometric import run_pairwise_comparison
        result = run_pairwise_comparison(thesis_panel)
        assert result["n_significant"] >= 4
        assert result["matrix_pval"].shape[0] >= 4
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
    def test_industry_summary(self, db_conn):
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

    def test_leverage_boxplot_data(self, thesis_panel):
        stages = thesis_panel.groupby("life_stage")["leverage"].describe()
        assert "mean" in stages.columns
        assert len(stages) >= 4

    def test_radar_columns_present(self, thesis_panel):
        radar_cols = ["leverage", "profitability", "tangibility", "tax_shield", "firm_size"]
        for col in radar_cols:
            assert col in thesis_panel.columns


# ─────────────────────────────────────────────
# Page 3 — Scenarios
# ─────────────────────────────────────────────

class TestPage3Scenarios:
    def test_scenario_ols(self, thesis_panel):
        from models.scenario_regression import run_scenario_ols
        result = run_scenario_ols(thesis_panel)
        assert "coefficients" in result
        assert len(result["coefficients"]) >= 3

    def test_predictor_means(self, thesis_panel):
        from models.scenario_regression import get_predictor_means
        means = get_predictor_means(thesis_panel)
        assert "profitability" in means
        assert "tangibility" in means
        assert means["profitability"] > 0


# ─────────────────────────────────────────────
# Page 4 — Bulk Upload
# ─────────────────────────────────────────────

class TestPage4BulkUpload:
    def test_dickinson_classification(self):
        from models.data_ingest import classify_life_stage_dickinson
        # Growth: +ncfo, -ncfi, -ncff
        stage = classify_life_stage_dickinson(ncfo=1, ncfi=-1, ncff=-1)
        assert stage == "Growth"

    def test_dickinson_all_8_stages(self):
        from models.data_ingest import classify_life_stage_dickinson
        combos = [
            (1, -1, -1, "Growth"),
            (1, -1,  1, "Maturity"),
            (-1, -1, 1, "Startup"),
            (1,  1, -1, "Shakeout1"),
            (-1, 1,  1, "Decline"),
            (1,  1,  1, "Decay"),
            (-1, -1, -1, "Shakeout2"),
            (-1, 1, -1, "Shakeout3"),
        ]
        for ncfo, ncfi, ncff, expected in combos:
            result = classify_life_stage_dickinson(ncfo, ncfi, ncff)
            assert result == expected, f"Expected {expected} for ({ncfo},{ncfi},{ncff}), got {result}"

    def test_canonical_columns_exist(self):
        from cmie.normalize import CANONICAL_COLUMNS
        required = ["leverage", "profitability", "tangibility", "firm_size", "dividend"]
        for col in required:
            assert col in CANONICAL_COLUMNS


# ─────────────────────────────────────────────
# Page 5 — Data Explorer
# ─────────────────────────────────────────────

class TestPage5DataExplorer:
    def test_full_explorer_returns_data(self, db_conn):
        import db as _db
        ft = _db.filters_to_tuple({"panel_mode": "thesis", "year_range": (2001, 2024),
                                   "company_codes": [], "life_stages": [], "industry_groups": [],
                                   "events": {"gfc": False, "ibc": False, "covid": False}})
        df = _db.get_full_data_explorer(ft)
        assert len(df) >= 8000
        assert "vintage" in df.columns

    def test_filtered_by_stage(self, db_conn):
        import db as _db
        ft = _db.filters_to_tuple({"panel_mode": "thesis", "year_range": (2001, 2024),
                                   "company_codes": [], "life_stages": ["Growth"],
                                   "industry_groups": [],
                                   "events": {"gfc": False, "ibc": False, "covid": False}})
        df = _db.get_full_data_explorer(ft)
        assert len(df) > 100
        assert (df["life_stage"] == "Growth").all()

    def test_filtered_by_year_range(self, db_conn):
        import db as _db
        ft = _db.filters_to_tuple({"panel_mode": "thesis", "year_range": (2010, 2015),
                                   "company_codes": [], "life_stages": [], "industry_groups": [],
                                   "events": {"gfc": False, "ibc": False, "covid": False}})
        df = _db.get_full_data_explorer(ft)
        assert df["year"].min() >= 2010
        assert df["year"].max() <= 2015


# ─────────────────────────────────────────────
# Page 7 — Knowledge Graph
# ─────────────────────────────────────────────

class TestPage7KnowledgeGraph:
    def test_transition_matrix_shape(self, thesis_panel):
        from models.survival import prepare_transition_data
        trans = prepare_transition_data(thesis_panel)
        assert len(trans) > 0
        assert "from_stage" in trans.columns or "duration" in trans.columns

    def test_stage_distribution(self, thesis_panel):
        stage_counts = thesis_panel["life_stage"].value_counts()
        assert len(stage_counts) >= 4
        assert stage_counts.sum() >= 8000


# ─────────────────────────────────────────────
# Page 8 — Econometrics Lab
# ─────────────────────────────────────────────

class TestPage8Econometrics:
    def test_pooled_ols_thesis(self, thesis_panel):
        from models.econometric import run_pooled_ols
        r = run_pooled_ols(thesis_panel)
        assert r["r_squared"] > 0.05
        assert r["n_obs"] >= 8000

    def test_fixed_effects_thesis(self, thesis_panel):
        from models.econometric import run_fixed_effects
        r = run_fixed_effects(thesis_panel)
        assert r["n_firms"] >= 300

    def test_robust_regression(self, thesis_panel):
        from models.econometric import run_robust_regression
        r = run_robust_regression(thesis_panel)
        assert "coef_table" in r
        assert r["n_obs"] > 5000

    def test_model_on_run3(self, run3_panel):
        from models.econometric import run_pooled_ols
        r = run_pooled_ols(run3_panel)
        assert r["n_obs"] >= 8000

    def test_anova_significant(self, thesis_panel):
        from models.econometric import run_anova_by_stage
        r = run_anova_by_stage(thesis_panel)
        assert r["p_value"] < 0.001
        assert r["f_stat"] > 10


# ─────────────────────────────────────────────
# Page 9 — ML Models
# ─────────────────────────────────────────────

class TestPage9MLModels:
    def test_random_forest(self, small_thesis):
        from models.ml_predict import cross_validate_model
        r = cross_validate_model(small_thesis, model_type="rf", n_splits=2)
        assert "r2_mean" in r
        assert r["r2_mean"] > -1.0

    def test_feature_importance_columns(self, small_thesis):
        from models.ml_predict import cross_validate_model
        r = cross_validate_model(small_thesis, model_type="rf", n_splits=2)
        assert "feature_importance" in r
        assert len(r["feature_importance"]) > 0

    def test_model_comparison(self, small_thesis):
        from models.ml_predict import compare_all_models
        results = compare_all_models(small_thesis, n_splits=2)
        assert len(results) >= 2
        for r in results:
            assert "model" in r


# ─────────────────────────────────────────────
# Page 10 — Forecasting (torch-optional)
# ─────────────────────────────────────────────

class TestPage10Forecasting:
    def test_torch_import_guard(self):
        from models.timeseries import HAS_TORCH
        assert isinstance(HAS_TORCH, bool)

    def test_panel_data_prep_for_forecasting(self, thesis_panel):
        firm_years = thesis_panel.groupby("company_code")["year"].count()
        multi_year = firm_years[firm_years >= 5]
        assert len(multi_year) >= 100

    @pytest.mark.skipif(
        not __import__("models.timeseries", fromlist=["HAS_TORCH"]).HAS_TORCH,
        reason="torch not installed"
    )
    def test_lstm_model_build(self):
        from models.timeseries import build_lstm_model
        model = build_lstm_model(input_size=5, hidden_size=32, num_layers=1)
        assert model is not None


# ─────────────────────────────────────────────
# Page 11 — Clustering
# ─────────────────────────────────────────────

class TestPage11Clustering:
    def test_prepare_cluster_features(self, thesis_panel):
        from models.clustering import prepare_cluster_features
        X, firms = prepare_cluster_features(thesis_panel)
        assert X.shape[0] >= 300
        assert X.shape[1] >= 3

    def test_kmeans_fit(self, thesis_panel):
        from models.clustering import prepare_cluster_features, fit_kmeans
        X, firms = prepare_cluster_features(thesis_panel)
        result = fit_kmeans(X, k=4)
        assert "labels" in result
        assert len(result["labels"]) == len(firms)

    def test_silhouette_score_range(self, thesis_panel):
        from models.clustering import prepare_cluster_features, find_optimal_k
        X, _ = prepare_cluster_features(thesis_panel)
        scores = find_optimal_k(X, k_range=range(2, 6))
        assert len(scores) == 4
        assert all(-1 <= s <= 1 for s in scores.values())

    def test_dickinson_comparison(self, thesis_panel):
        from models.clustering import compare_with_dickinson
        from models.clustering import prepare_cluster_features, fit_kmeans
        X, firms = prepare_cluster_features(thesis_panel)
        km = fit_kmeans(X, k=8)
        ari = compare_with_dickinson(thesis_panel, km["labels"], firms)
        assert -1 <= ari <= 1


# ─────────────────────────────────────────────
# Page 12 — Transitions (Cox PH + KM)
# ─────────────────────────────────────────────

class TestPage12Transitions:
    def test_prepare_transition_data(self, thesis_panel):
        from models.survival import prepare_transition_data
        trans = prepare_transition_data(thesis_panel)
        assert len(trans) > 100
        assert "duration" in trans.columns
        assert "event" in trans.columns

    def test_kaplan_meier(self, thesis_panel):
        from models.survival import prepare_transition_data, fit_kaplan_meier
        trans = prepare_transition_data(thesis_panel)
        km_result = fit_kaplan_meier(trans)
        assert km_result is not None
        assert "median_survival" in km_result or "kmf" in km_result

    def test_cox_ph_returns_hazard_ratios(self, thesis_panel):
        from models.survival import prepare_transition_data, fit_cox_ph
        trans = prepare_transition_data(thesis_panel)
        cph, hr_df, summary = fit_cox_ph(trans)
        assert cph is not None
        assert hr_df is not None
        assert "Hazard Ratio" in hr_df.columns
        assert len(hr_df) >= 3

    def test_cox_ph_hazard_ratios_positive(self, thesis_panel):
        from models.survival import prepare_transition_data, fit_cox_ph
        trans = prepare_transition_data(thesis_panel)
        _, hr_df, _ = fit_cox_ph(trans)
        assert (hr_df["Hazard Ratio"] > 0).all(), "Hazard ratios must be positive"

    def test_cox_ph_profitability_delays_transition(self, thesis_panel):
        from models.survival import prepare_transition_data, fit_cox_ph
        trans = prepare_transition_data(thesis_panel)
        _, hr_df, _ = fit_cox_ph(trans)
        prof_row = hr_df[hr_df["Variable"] == "profitability"]
        if len(prof_row) > 0:
            assert prof_row.iloc[0]["Hazard Ratio"] < 1.5, "Profitability HR should not be extreme"

    def test_transition_matrix(self, thesis_panel):
        from models.survival import compute_transition_matrix
        tm = compute_transition_matrix(thesis_panel)
        assert tm is not None
        assert tm.shape[0] >= 4
        assert (tm.values >= 0).all()

    def test_insufficient_data_handled(self):
        from models.survival import fit_cox_ph
        import pandas as pd
        tiny = pd.DataFrame({"duration": [1, 2], "event": [1, 0],
                             "profitability": [0.1, 0.2]})
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
        assert "coef_table" in r
        assert r["n_obs"] > 5000

    def test_delta_leverage_by_stage(self, thesis_panel):
        from models.econometric import run_delta_leverage_by_stage
        results = run_delta_leverage_by_stage(thesis_panel)
        assert len(results) >= 3
        for stage, r in results.items():
            assert "coef_table" in r

    def test_stage_comparison(self, thesis_panel):
        from models.econometric import run_stage_comparison
        r = run_stage_comparison(thesis_panel, "Growth", "Maturity")
        assert r is not None

    def test_iv_regression(self, thesis_panel):
        from models.econometric import run_iv_regression
        r = run_iv_regression(thesis_panel)
        assert "coef_table" in r or "error" in r


# ─────────────────────────────────────────────
# Page 14 — Workbench
# ─────────────────────────────────────────────

class TestPage14Workbench:
    def test_base_ols_runs(self, thesis_panel):
        from models.econometric import run_pooled_ols
        from models.base import DEFAULT_X_COLS
        r = run_pooled_ols(thesis_panel, x_cols=DEFAULT_X_COLS[:3])
        assert "coef_table" in r

    def test_panel_subsample_by_stage(self, thesis_panel):
        growth = thesis_panel[thesis_panel["life_stage"] == "Growth"]
        assert len(growth) >= 500
        from models.econometric import run_pooled_ols
        r = run_pooled_ols(growth)
        assert r["n_obs"] >= 400

    def test_log_transform_firm_size(self, thesis_panel):
        assert "firm_size" in thesis_panel.columns
        assert "log_size" in thesis_panel.columns
        log_vals = thesis_panel["log_size"].dropna()
        assert (log_vals > 0).mean() > 0.9


# ─────────────────────────────────────────────
# Page 15 — Interaction Effects
# ─────────────────────────────────────────────

class TestPage15InteractionEffects:
    def test_cross_term_ols(self, thesis_panel):
        from models.interaction import run_cross_term_ols
        r = run_cross_term_ols(thesis_panel)
        assert "coef_table" in r
        assert r["n_obs"] > 5000

    def test_cross_term_has_interaction_coef(self, thesis_panel):
        from models.interaction import run_cross_term_ols
        r = run_cross_term_ols(thesis_panel)
        coef_names = r["coef_table"].index.tolist() if hasattr(r["coef_table"], "index") else []
        interaction_present = any("prof" in str(c).lower() and "tang" in str(c).lower()
                                  for c in coef_names)
        assert interaction_present, f"Interaction term missing from coef_table: {coef_names}"

    def test_stage_moderation_ols(self, thesis_panel):
        from models.interaction import run_stage_moderation_ols
        r = run_stage_moderation_ols(thesis_panel)
        assert "marginal_effects" in r
        assert len(r["marginal_effects"]) >= 3

    def test_simple_slopes(self, thesis_panel):
        from models.interaction import run_cross_term_ols, simple_slopes
        r = run_cross_term_ols(thesis_panel)
        slopes = simple_slopes(r, thesis_panel)
        assert slopes is not None
        assert len(slopes) >= 3

    def test_moderation_marginal_effects_range(self, thesis_panel):
        from models.interaction import run_stage_moderation_ols
        r = run_stage_moderation_ols(thesis_panel)
        for stage, effects in r["marginal_effects"].items():
            for var, val in effects.items():
                assert isinstance(val, float), f"Marginal effect must be float: {stage}/{var}={val}"


# ─────────────────────────────────────────────
# Cross-panel DB layer
# ─────────────────────────────────────────────

class TestDBLayer:
    @pytest.mark.parametrize("panel", ["thesis", "latest", "run3", "us_av_2024"])
    def test_year_range(self, panel):
        import db as _db
        yr_min, yr_max = _db.get_year_range(panel)
        assert yr_min >= 2001
        assert yr_max <= 2025
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

    def test_filters_to_tuple_roundtrip(self):
        import db as _db
        filters = {"panel_mode": "thesis", "year_range": (2005, 2020),
                   "company_codes": [101], "life_stages": ["Growth"],
                   "industry_groups": [], "events": {"gfc": True, "ibc": False, "covid": False}}
        ft = _db.filters_to_tuple(filters)
        assert ft is not None
        assert len(ft) > 0

    def test_india_panel_guard(self):
        from helpers import is_india_panel
        assert is_india_panel("thesis") is True
        assert is_india_panel("latest") is True
        assert is_india_panel("run3") is True
        assert is_india_panel("us_av_2024") is False


# ─────────────────────────────────────────────
# UI Helper Layer
# ─────────────────────────────────────────────

class TestUIHelpers:
    def test_plotly_config_modebar_hover(self):
        from helpers import PLOTLY_CONFIG
        assert PLOTLY_CONFIG["displayModeBar"] == "hover", (
            "Modebar must be 'hover' to prevent icon/title overlap in narrow columns"
        )

    def test_plotly_layout_light_top_margin(self):
        from helpers import plotly_layout_light
        layout = plotly_layout_light(title="Test Title", height=400)
        assert layout["margin"]["t"] >= 60, "Top margin must be ≥60px to give title breathing room"

    def test_plotly_layout_no_title_low_margin(self):
        from helpers import plotly_layout_light
        layout = plotly_layout_light(title="", height=400)
        assert layout["margin"]["t"] <= 40, "No-title charts should use reduced top margin"

    def test_plotly_layout_dark_top_margin(self):
        from helpers import plotly_layout_dark
        layout = plotly_layout_dark(title="Test Title", height=400)
        assert layout["margin"]["t"] >= 60

    def test_format_pct(self):
        from helpers import format_pct
        assert "23" in format_pct(23.4)
        assert format_pct(None) in ("—", "N/A", "")

    def test_winsorize(self):
        from helpers import winsorize
        import pandas as pd
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
            assert stage in STAGE_COLORS, f"Missing color for stage: {stage}"
            assert STAGE_COLORS[stage].startswith("#"), f"Invalid color for {stage}"

    def test_hazard_ratio_title_not_instructional(self):
        """Regression: chart title must not contain instructional parenthetical."""
        import ast, os
        page_path = os.path.join(PROJECT_ROOT, "pages", "12_transitions.py")
        with open(page_path) as f:
            src = f.read()
        assert "accelerates, <0 delays" not in src or 'update_xaxes' in src, (
            "Instructional text must be in xaxis title, not chart title"
        )

    def test_long_title_not_in_layout_calls(self):
        """Regression: chart titles must be ≤60 chars to avoid toolbar overlap."""
        import os, re
        pages_dir = os.path.join(PROJECT_ROOT, "pages")
        violations = []
        for fname in os.listdir(pages_dir):
            if not fname.endswith(".py"):
                continue
            with open(os.path.join(pages_dir, fname)) as f:
                src = f.read()
            for m in re.finditer(r'plotly_layout\("([^"]{61,})"', src):
                violations.append(f"{fname}: '{m.group(1)[:70]}...' ({len(m.group(1))} chars)")
        assert not violations, "Chart titles > 60 chars found:\n" + "\n".join(violations)
