import pytest

from models.wave6_benchmarks import (
    BenchmarkFixtureError,
    make_known_answer_panel,
    run_hdfe_reference,
    run_iv_reference,
    run_wave6_fixture_suite,
)


def test_iv_reference_is_known_answer_and_finite():
    panel = make_known_answer_panel()
    outcome = run_iv_reference(panel)
    assert outcome.benchmark_id == "wave6-iv-known-answer-v1"
    assert outcome.coefficients["x"] == pytest.approx(panel.iv_beta, abs=0.08)
    assert outcome.coefficients["w"] == pytest.approx(panel.iv_gamma, abs=0.08)
    assert outcome.effective_row_count == outcome.row_count


def test_hdfe_reference_absorbs_entity_effects():
    panel = make_known_answer_panel()
    outcome = run_hdfe_reference(panel)
    assert outcome.benchmark_id == "wave6-hdfe-known-answer-v1"
    assert outcome.coefficients["x"] == pytest.approx(panel.hdfe_beta, abs=0.08)
    assert outcome.diagnostics["absorbed_effect"] == "company_code"


def test_fixture_is_deterministic_and_both_outcomes_are_fingerprinted():
    first = run_wave6_fixture_suite()
    second = run_wave6_fixture_suite()
    assert first["iv"].dataset_fingerprint == second["iv"].dataset_fingerprint
    assert first["hdfe"].sample_fingerprint == second["hdfe"].sample_fingerprint
    assert first["iv"].coefficients == second["iv"].coefficients


def test_fixture_rejects_tiny_panels():
    with pytest.raises(BenchmarkFixtureError, match="at least 4"):
        make_known_answer_panel(firms=3)
