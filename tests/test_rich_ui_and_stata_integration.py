"""
TDD Tests for Backend Integration of Stata Engine with Literature Vault & Chart Switcher.
Verifies that execute_stata_command produces:
1. compatible_charts list matching data-to-graph matrix.
2. evaluations against top-tier literature.
3. theory_scorecard table data.
4. textbook foundations and formal citations.
"""

import pytest
import pandas as pd
import numpy as np
from models.stata_engine import execute_stata_command


@pytest.fixture(scope="module")
def panel_df():
    """Create a balanced panel dataset matching CMIE schema."""
    np.random.seed(42)
    firms = list(range(101, 121))
    years = list(range(2010, 2025))
    rows = []
    for f in firms:
        alpha_i = np.random.normal(0, 0.5)
        for y in years:
            prof = np.random.normal(15.0, 5.0)
            tang = np.random.normal(40.0, 10.0)
            size = np.random.normal(8.0, 1.2)
            lev = 30.0 + alpha_i - 0.25 * prof + 0.20 * tang - 1.5 * size + np.random.normal(0, 2.0)
            rows.append({
                "company_code": f,
                "year": y,
                "leverage": lev,
                "profitability": prof,
                "tangibility": tang,
                "log_size": size,
            })
    return pd.DataFrame(rows)


def test_stata_engine_xtreg_returns_literature_and_charts(panel_df):
    cmd = "xtreg leverage profitability tangibility log_size, fe cluster(company_code)"
    res = execute_stata_command(cmd, panel_df)

    assert res["status"] == "success"
    assert "coefficients" in res
    assert "profitability" in res["coefficients"]

    # Must contain compatible charts from chart switcher engine
    assert "compatible_charts" in res
    compat_ids = [c["id"] for c in res["compatible_charts"]]
    assert "forest_plot" in compat_ids
    assert "beta_rank_bars" in compat_ids
    assert "composition_donut" not in compat_ids

    # Must contain literature evaluation and citations
    assert "literature_eval" in res
    lit = res["literature_eval"]
    assert "evaluations" in lit
    assert "citations" in lit
    assert "synthesis_markdown" in lit
    assert len(lit["citations"]) >= 3

    # Check that Wooldridge and Rajan & Zingales or Booth are cited
    citations_str = " ".join(lit["citations"])
    assert "Wooldridge" in citations_str
    assert "Booth" in citations_str or "Rajan" in citations_str

    # Must contain theory scorecard data for UI table rendering
    assert "theory_scorecard" in res
    scorecard = res["theory_scorecard"]
    assert len(scorecard) >= 3
    prof_card = next((s for s in scorecard if "profitability" in s["variable"].lower() or "roa" in s["variable"].lower()), None)
    assert prof_card is not None
    assert "Pecking Order" in prof_card["theory"]
    assert "VALIDATED" in prof_card["status"]
