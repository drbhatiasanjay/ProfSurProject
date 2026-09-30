import pytest

@pytest.fixture(scope="session")
def thesis_panel_ground_truth():
    """Canonical ground-truth metrics for primary empirical panel."""
    return {
        "n_obs": 8677,
        "n_firms": 401,
        "mean_leverage_pct": 21.0063,
        "mean_tangibility_ratio": 0.2848,
        "tata_motors_code": 248093,
        "panel_mode_primary": "thesis",
        "panel_mode_extended": "bf2001_25_sept26",
    }
