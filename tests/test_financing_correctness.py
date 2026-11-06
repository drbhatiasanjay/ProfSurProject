"""Cross-surface coverage parity and deterministic recursive forecast checks."""
import numpy as np
import pandas as pd
import pytest

from models.debt_metrics import coverage_case
from models import timeseries
from models.agent_tools import run_cfo_stress_simulation


def test_company_grounded_ai_matches_deck():
    from models.debt_board import build_debt_board
    import db
    data = db._query("SELECT * FROM financials WHERE company_code=248093 AND vintage='thesis' ORDER BY year")
    # Ground truth queried before this test was authored: FY2024 PBIT 9811.540039, interest 1960.719971, debt 14190.639648.
    result = run_cfo_stress_simulation("248093", 200, -20, panel_mode="thesis", floating_rate_share=.5, coverage_floor=3)
    pack = build_debt_board(data, dict(code=248093, name="Tata Motors"), None,
        dict(scenario_type="stress", floating_share=.5, rate_shock=200, earnings_shock=.2, coverage_floor=3))
    screen = pack["sections"][7]["tables"][0]
    assert result["calculated_cases"]["baseline"]["coverage"] == pytest.approx(9811.5400390625/1960.719970703125)
    assert result["calculated_cases"]["downside"]["coverage"] == pytest.approx(screen.iloc[1]["Coverage (x)"])
    metrics = result["covenant_and_debt_metrics"]
    assert metrics["available_debt_headroom_cr"] is None and metrics["covenant_floor"] is None


def test_missing_exposure_and_bad_assumptions():
    result = run_cfo_stress_simulation("248093", 100, -10)
    assert result["calculated_cases"]["downside"]["coverage"] is None
    assert run_cfo_stress_simulation("248093", 100, -10, floating_rate_share=2)["status"] == "error"
    assert coverage_case(100, 0, 1000)["coverage"] is None
    assert coverage_case(-100, 20, 1000)["coverage"] == -5
    assert coverage_case(100, 20, 1000, floating_share=0, shock_bps=100)["coverage"] == 5


def test_recursive_forecast_updates_target_by_name_only():
    if not timeseries.HAS_TORCH:
        pytest.skip("PyTorch unavailable")
    import torch
    class Recorder:
        def __init__(self):
            self.windows = []
        def eval(self):
            pass
        def __call__(self, value):
            self.windows.append(value.numpy().copy())
            return torch.tensor([42.0])
    for features in (["profitability", "leverage"], ["leverage", "profitability"]):
        model = Recorder()
        df = pd.DataFrame(dict(year=[2020, 2021, 2022], profitability=[.1,.2,.3], leverage=[10,11,12]))
        result = timeseries.forecast_firm(model, df, features, seq_len=3, n_steps=3)
        assert len(result) == 3
        assert model.windows[1][0,-1,features.index("leverage")] == 42
        assert model.windows[1][0,-1,features.index("profitability")] == pytest.approx(.3)
        df.loc[2,"year"] = 2024
        assert timeseries.forecast_firm(model, df, features, seq_len=3) == []


def test_training_sequences_reject_year_gaps():
    df = pd.DataFrame(dict(company_code=[1]*4,year=[2020,2021,2023,2024],leverage=[1,2,3,4]))
    x, _, _, _ = timeseries.prepare_sequences(df, ["leverage"], seq_len=2)
    assert len(x) == 0


def test_debt_equity_upload_is_not_silently_debt_assets():
    from models.data_ingest import validate_upload, standardize_columns
    raw = pd.DataFrame(dict(company_code=[1], year=[2024], debt_equity=[.5]))
    validation = validate_upload(raw)
    cleaned, _ = standardize_columns(raw, validation["detected_columns"])
    assert "leverage" not in cleaned
    assert any("Debt/equity" in warning for warning in validation["warnings"])
