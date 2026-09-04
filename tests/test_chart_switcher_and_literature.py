"""
Unit tests for models/econometric_literature_vault.py and models/chart_switcher_engine.py
Verifies:
1. Chart compatibility filter correctly excludes invalid chart types.
2. Canonical variable labeling maps raw keys to formal academic titles and units.
3. Figure builders generate valid Plotly figure objects with non-empty traces.
4. Econometric literature vault evaluates statistical significance and produces citations.
"""

import pytest
import plotly.graph_objects as go
from models.chart_switcher_engine import (
    get_canonical_label,
    get_compatible_chart_types,
    build_forest_plot,
    build_beta_rank_bars,
    build_fitted_vs_actual,
    build_residuals_plot,
    build_time_series_chart,
)
from models.econometric_literature_vault import (
    TEXTBOOK_FOUNDATIONS,
    LITERATURE_EMPIRICAL_BENCHMARKS,
    evaluate_econometric_result,
)


def test_canonical_variable_labels():
    assert get_canonical_label("profitability") == "Return on Assets (ROA, %)"
    assert get_canonical_label("prof") == "Return on Assets (ROA, %)"
    assert get_canonical_label("tangibility") == "Asset Tangibility (PPE / Assets, %)"
    assert get_canonical_label("tang") == "Asset Tangibility (PPE / Assets, %)"
    assert get_canonical_label("log_size") == "Firm Scale (ln Total Assets)"
    assert get_canonical_label("leverage") == "Debt / Equity Leverage (%)"


def test_compatible_chart_types_filters():
    # Regression should include forest plot and beta rank, and NEVER donut or pie
    reg_opts = get_compatible_chart_types("regression")
    reg_ids = [o["id"] for o in reg_opts]
    assert "forest_plot" in reg_ids
    assert "beta_rank_bars" in reg_ids
    assert "composition_donut" not in reg_ids
    assert "pie" not in reg_ids

    # With fitted values, should also include fitted_vs_actual and residuals
    reg_opts_full = get_compatible_chart_types("regression", payload={"y_fitted": [0.1, 0.2]})
    reg_ids_full = [o["id"] for o in reg_opts_full]
    assert "fitted_vs_actual" in reg_ids_full
    assert "residuals_plot" in reg_ids_full

    # Time series options
    ts_opts = get_compatible_chart_types("time_series")
    ts_ids = [o["id"] for o in ts_opts]
    assert "connected_lines" in ts_ids
    assert "forest_plot" not in ts_ids
    assert "composition_donut" not in ts_ids

    # Categorical options: Donut only if is_share_composition=True
    cat_no_share = get_compatible_chart_types("categorical", payload={"is_share_composition": False})
    assert "composition_donut" not in [o["id"] for o in cat_no_share]

    cat_share = get_compatible_chart_types("categorical", payload={"is_share_composition": True})
    assert "composition_donut" in [o["id"] for o in cat_share]


def test_figure_builders():
    coef_data = {
        "profitability": {"coef": -25.40, "se": 2.50, "t": -10.12, "p": 0.000, "ci_low": -30.31, "ci_high": -20.48},
        "tangibility": {"coef": 22.15, "se": 3.11, "t": 7.12, "p": 0.000, "ci_low": 16.05, "ci_high": 28.25},
        "log_size": {"coef": -2.32, "se": 0.24, "t": -9.80, "p": 0.000, "ci_low": -2.79, "ci_high": -1.86},
    }

    # Forest plot
    fig_fp = build_forest_plot(coef_data, depvar="leverage")
    assert isinstance(fig_fp, go.Figure)
    assert len(fig_fp.data) > 0

    # Beta rank bars
    fig_br = build_beta_rank_bars(coef_data, depvar="leverage")
    assert isinstance(fig_br, go.Figure)
    assert len(fig_br.data) > 0

    # Fitted vs actual
    fig_fa = build_fitted_vs_actual([0.1, 0.2, 0.3], [0.12, 0.19, 0.28])
    assert isinstance(fig_fa, go.Figure)
    assert len(fig_fa.data) == 2

    # Residuals plot
    fig_res = build_residuals_plot([0.02, -0.01, -0.02], [0.12, 0.19, 0.28])
    assert isinstance(fig_res, go.Figure)
    assert len(fig_res.data) > 0

    # Time series
    fig_ts = build_time_series_chart([2020, 2021, 2022], {"leverage": [19.1, 17.8, 16.9]})
    assert isinstance(fig_ts, go.Figure)
    assert len(fig_ts.data) > 0


def test_literature_evaluation_engine():
    coef_dict = {
        "profitability": {"coef": -25.40, "se": 2.50, "t": -10.12, "p": 0.000},
        "tangibility": {"coef": 22.15, "se": 3.11, "t": 7.12, "p": 0.000},
        "log_size": {"coef": -2.32, "se": 0.24, "t": -9.80, "p": 0.000},
    }
    eval_res = evaluate_econometric_result(
        model_type="Fixed Effects",
        depvar="leverage",
        indepvars=["profitability", "tangibility", "log_size"],
        coefficients=coef_dict,
        f_stat=96.79,
        f_pval=0.0000,
        r2=0.0339,
        n_obs=8673,
        n_groups=401,
    )

    assert "evaluations" in eval_res
    assert len(eval_res["evaluations"]) == 3
    assert len(eval_res["citations"]) >= 4

    # Verify Wooldridge citation is present
    found_wooldridge = any("Wooldridge" in c for c in eval_res["citations"])
    assert found_wooldridge, "Wooldridge (2010) citation must be present for Fixed Effects models"

    # Verify Rajan & Zingales citation is present
    found_rz = any("Rajan" in c for c in eval_res["citations"])
    assert found_rz, "Rajan & Zingales (1995) must be present for capital structure determinants"

    # Verify synthesis text includes significance
    synth = eval_res["synthesis_markdown"]
    assert "statistically significant" in synth
    assert "Pecking Order Theory" in synth
    assert "Trade-Off Theory" in synth


def test_get_relevant_vault_citations():
    from models.econometric_literature_vault import get_relevant_vault_citations
    from models.rich_chat_renderer import render_academic_vault_html

    # Test 1: Life cycle question
    c_life = get_relevant_vault_citations("How does leverage vary across Dickinson life cycle stages?")
    assert any("Dickinson" in c for c in c_life)

    # Test 2: Profitability & Pecking Order question
    c_prof = get_relevant_vault_citations("Why does operating profitability reduce debt under Pecking Order?")
    assert any("Myers" in c for c in c_prof)
    assert any("Rajan" in c for c in c_prof)
    assert any("Reserve Bank" in c for c in c_prof)

    # Test 3: Tangibility & Collateral question
    c_tang = get_relevant_vault_citations("Explain why asset tangibility expands bank collateral under IBC")
    assert any("Titman" in c for c in c_tang)
    assert any("IBBI" in c for c in c_tang)

    # Test 4: Firm Size question
    c_size = get_relevant_vault_citations("What is the impact of firm size and corporate bond market access?")
    assert any("Fama" in c for c in c_size)
    assert any("SEBI" in c for c in c_size)

    # Test 5: Vault rendering with custom title for AI Chatbot
    html_custom = render_academic_vault_html(
        c_prof,
        theme="light",
        title="📚 Peer-Reviewed Literature & Institutional Benchmark Vault"
    )
    assert "📚 Peer-Reviewed Literature & Institutional Benchmark Vault" in html_custom
    assert "JOURNAL OF FINANCE" in html_custom
    assert "INSTITUTIONAL REPORT" in html_custom


def test_page_17_board_export_enhancements():
    import pathlib
    src = pathlib.Path("pages/17_board_export.py").read_text(encoding="utf-8")
    assert "render_bento_kpi" in src
    assert "get_relevant_vault_citations" in src
    assert "render_academic_vault_html" in src
    assert "Topic 1 Visual Mode" in src

