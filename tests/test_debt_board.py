"""Decision narrative, unit contracts, adverse inputs and actual PPTX integrity."""
from io import BytesIO
import sqlite3

import numpy as np
import pandas as pd
import pytest
from pptx import Presentation

from models import board_export, debt_board, pptx_generator


@pytest.fixture
def assumptions():
    return dict(funding_uses=200, internal_funding=50, new_debt=150,
                new_rate=8, floating_share=.5, rate_shock=200,
                earnings_shock=.2, coverage_floor=3)


@pytest.fixture
def company():
    return pd.DataFrame([dict(year=2024, life_stage="Maturity", borrowings=1000,
        cash_holdings=100, pbit=200, interest_amt=40, ncfo=180, ncfi=-100, ncff=-60,
        leverage=25, profitability=.05, tangibility=.4, tax=.25, tax_shield=100)])


@pytest.fixture
def info():
    return dict(name="Example", code=1, current_stage="Maturity", industry="Example")


def build(company, info, assumptions, peers=None):
    return debt_board.build_debt_board(company, info, peers, assumptions)


def test_facts_precede_analysis_scenarios_and_decision(company, info, assumptions):
    pack = build(company, info, assumptions)
    titles = [s["title"] for s in pack["sections"]]
    assert len(titles) == 10
    assert titles[0] == "1. Core facts"
    assert titles[7] == "8. Scenarios and failure points"
    assert titles[-1] == "10. Board decision and monitoring"
    facts = pack["sections"][0]["tables"][0].set_index("Core fact")["Observed value"]
    assert facts["Reported leverage"] == "25.00%"
    assert facts["Interest coverage"] == "5.00x"


def test_combined_stress_uses_explicit_floating_share(company, info, assumptions):
    table = build(company, info, assumptions)["sections"][7]["tables"][0]
    assert table.iloc[1]["Annual interest"] == pytest.approx(52)
    assert table.iloc[2]["Annual interest"] == pytest.approx(65)
    assert table.iloc[2]["Coverage (x)"] == pytest.approx(160 / 65)
    assert "Rework" in build(company, info, assumptions)["sections"][8]["insights"][0]


@pytest.mark.parametrize("interest,pbit", [(0, 0), (0, 200), (np.nan, 200), (40, np.nan), (-5, 200)])
def test_missing_or_nonpositive_interest_never_implies_unlimited_capacity(company, info, assumptions, interest, pbit):
    company.loc[0, ["interest_amt", "pbit"]] = [interest, pbit]
    pack = build(company, info, assumptions)
    facts = pack["sections"][0]["tables"][0].set_index("Core fact")["Observed value"]
    assert facts["Interest coverage"] == "N/A"
    assert "not an approved debt limit" in " ".join(pack["sections"][4]["insights"])


def test_negative_earnings_fail_policy_test(company, info, assumptions):
    company.loc[0, "pbit"] = -20
    table = build(company, info, assumptions)["sections"][7]["tables"][0]
    assert table.iloc[0]["Coverage (x)"] < 0
    assert table.iloc[0]["Illustrative policy test"] == "Below policy floor"


@pytest.mark.parametrize("key,value", [("new_debt", -1), ("floating_share", 2), ("coverage_floor", 0), ("new_rate", np.inf), ("earnings_shock", 1.1)])
def test_invalid_assumptions_rejected(company, info, assumptions, key, value):
    assumptions[key] = value
    with pytest.raises(ValueError):
        build(company, info, assumptions)


def test_peers_exclude_stale_year_other_stage_and_self(company, info, assumptions):
    peers = pd.DataFrame([
        dict(company_code=1, year=2024, life_stage="Maturity", leverage=25),
        dict(company_code=2, year=2023, life_stage="Maturity", leverage=99),
        dict(company_code=3, year=2024, life_stage="Growth", leverage=90),
        dict(company_code=4, year=2024, life_stage="Maturity", leverage=30),
    ])
    pack = build(company, info, assumptions, peers)
    assert "1 same-year" in pack["sections"][5]["insights"][0]
    assert pack["sections"][5]["tables"][0].iloc[0]["Peer median"] == "30.00"
    assert "neither optimal" in pack["sections"][5]["insights"][1]


def test_duplicate_years_require_vintage_selection(company, info, assumptions):
    with pytest.raises(ValueError, match="vintage"):
        build(pd.concat([company, company]), info, assumptions)


def test_board_unit_conversion_is_explicit_and_idempotent(company, info):
    normal = board_export.board_ratios(company)
    assert normal.leverage.iloc[0] == .25
    assert board_export.board_ratios(normal).leverage.iloc[0] == .25
    assert company.leverage.iloc[0] == 25
    out = board_export.build_topic_1(company, info, pd.DataFrame(), None, None)
    indicators = {t.title.text: t for t in out["figs"][0].data}
    assert indicators["Interest Cover"].value == 5
    assert indicators["Interest Cover"].number.suffix == "x"
    assert indicators["Leverage"].value == 25
    assert indicators["Tax Shield"].value == 100
    company.loc[0, "interest_amt"] = 0
    missing = board_export.build_topic_1(company, info, pd.DataFrame(), None, None)
    assert any("N/A" in t.text for t in missing["figs"][0].layout.annotations)


def test_pptx_keeps_all_rows_columns_bullets_and_correct_page_numbers(info):
    table = pd.DataFrame({f"Column{j}": [f"cell-{i}-{j}" for i in range(19)] for j in range(9)})
    section = dict(title="Evidence", figs=[], tables=[table], insights=[f"Finding {i}" for i in range(7)],
                   actions=[f"Action {i}" for i in range(5)], provenance="FY2024 source")
    blob = pptx_generator.build_sections(info, [section])
    prs = Presentation(BytesIO(blob))
    cells = [c.text for s in prs.slides for shape in s.shapes if shape.has_table for row in shape.table.rows for c in row.cells]
    assert all(f"cell-{i}-{j}" in cells for i in range(19) for j in range(9))
    texts = " ".join(shape.text for s in prs.slides for shape in s.shapes if shape.has_text_frame)
    assert "Finding 6" in texts and "Action 4" in texts
    for i, slide in enumerate(prs.slides, 1):
        assert any(f"Slide {i} of {len(prs.slides)}" in shape.text for shape in slide.shapes if shape.has_text_frame)
    assert "FY2024 source" in prs.slides[1].notes_slide.notes_text_frame.text


def test_export_reports_chart_failure_visibly(monkeypatch, info):
    def fail(*a, **kw):
        raise RuntimeError("renderer failure")
    monkeypatch.setattr(pptx_generator, "_add_chart_image", fail)
    warnings = []
    blob = pptx_generator.build_sections(info, [dict(title="Scenario", figs=[object()], tables=[], insights=[], actions=[])], warnings=warnings)
    assert warnings and "chart unavailable" in warnings[0]
    prs = Presentation(BytesIO(blob))
    assert any("chart unavailable" in shape.text for shape in prs.slides[1].shapes if shape.has_text_frame)


def test_deterministic_commentary_never_calls_a_model(monkeypatch):
    import models.llm_adapters as la
    def forbidden(*args, **kwargs):
        raise AssertionError("Model call was not authorised")
    monkeypatch.setattr(la, "stream_ollama", forbidden)
    monkeypatch.setattr(la, "stream_anthropic", forbidden)
    result = board_export.build_topic_13_ai(248093, backend="deterministic")
    assert result["ai_offline"]
    assert result["insights"] and result["actions"]


def test_export_uses_supplied_preview_without_rebuilding(monkeypatch, info):
    def fail(*a, **kw):
        raise AssertionError("Unexpected rebuild")
    monkeypatch.setitem(pptx_generator.TOPIC_BUILDERS, 1, fail)
    prepared = dict(title="Selected radar", figs=[], tables=[], insights=["User-selected view"], actions=[])
    blob = pptx_generator.build(None, info, None, None, None, {1: True}, topic_data={1: prepared})
    prs = Presentation(BytesIO(blob))
    assert any("User-selected view" in shape.text for shape in prs.slides[1].shapes if shape.has_text_frame)


def test_real_thesis_tata_facts_use_verified_units(assumptions):
    import db
    with sqlite3.connect(f"file:{db.DB_PATH}?mode=ro", uri=True) as conn:
        df = pd.read_sql_query("SELECT * FROM financials WHERE company_code=248093 AND vintage='thesis' ORDER BY year", conn)
    info = dict(code=248093, name="Tata Motors Ltd.", current_stage=df.iloc[-1].life_stage)
    row = df.iloc[-1]
    assert int(row.year) == 2024
    assert float(row.pbit) == pytest.approx(9811.5400390625)
    assert float(row.interest_amt) == pytest.approx(1960.719970703125)
    facts = build(df, info, assumptions)["sections"][0]["tables"][0].set_index("Core fact")["Observed value"]
    assert facts["Interest coverage"] == "5.00x"
    assert facts["Reported leverage"] == "20.29%"


def test_company_choices_exclude_same_name_codes_from_other_vintages():
    choices = debt_board.get_thesis_companies()
    tata = choices.loc[choices.company_name == "Tata Motors Ltd.", "company_code"].tolist()
    assert tata == [248093]
    assert 729991 not in choices.company_code.values
    assert not choices.company_code.duplicated().any()


def test_historical_deck_has_no_invented_funding_plan_or_policy(company, info):
    pack = debt_board.build_debt_board(company, info, None)
    assert pack["assumptions"] is None
    assert pack["scenario_type"] == "historical"
    assert set(pack["sections"][1]["tables"][0]["Amount (source units)"]) == {"Not supplied"}
    assert not pack["sections"][7]["figs"]
    assert len(pack["sections"][7]["tables"][0]) == 1
    assert "No funding proposal" in pack["sections"][8]["insights"][0]
    assert "No coverage policy floor supplied" in pack["sections"][4]["insights"][0]
    blob = pptx_generator.build_sections(info, pack["sections"])
    prs = Presentation(BytesIO(blob))
    text = " ".join(shape.text for slide in prs.slides for shape in slide.shapes if shape.has_text_frame)
    cells = " ".join(cell.text for slide in prs.slides for shape in slide.shapes if shape.has_table for row in shape.table.rows for cell in row.cells)
    assert "Not supplied" in cells
    assert "proposal passes" not in text


def test_existing_debt_stress_does_not_require_funding_plan(company, info):
    inputs = dict(scenario_type="stress", floating_share=.5, rate_shock=200,
                  earnings_shock=.2, coverage_floor=3)
    pack = debt_board.build_debt_board(company, info, None, inputs)
    table = pack["sections"][7]["tables"][0]
    assert len(table) == 2
    assert table.iloc[1]["Annual interest"] == 50
    assert table.iloc[1]["Coverage (x)"] == pytest.approx(3.2)
    assert set(pack["sections"][1]["tables"][0]["Amount (source units)"]) == {"Not supplied"}
    assert pack["assumptions"]["funding_uses"] is None


def test_partial_funding_is_rejected_instead_of_filled_with_zeros(company, info, assumptions):
    assumptions["new_debt"] = None
    with pytest.raises(ValueError, match="new_debt"):
        debt_board.build_debt_board(company, info, None, assumptions)
