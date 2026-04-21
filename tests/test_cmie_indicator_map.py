"""Tests for CMIE column alias normalization."""

from __future__ import annotations

import pandas as pd

from cmie.indicator_map import apply_cmie_column_aliases


def test_apply_cmie_column_aliases_renames_known_headers() -> None:
    df = pd.DataFrame(
        {
            "comp_code": [1, 2],
            "fy": [2020, 2021],
            "x": [0.1, 0.2],
        }
    )
    out = apply_cmie_column_aliases(df)
    assert list(out.columns) == ["company_code", "year", "x"]
    assert out["company_code"].tolist() == [1, 2]


def test_apply_cmie_column_aliases_whitespace_and_case() -> None:
    df = pd.DataFrame([{"Comp_Code": 9, "FY": 2019}])
    out = apply_cmie_column_aliases(df)
    assert "company_code" in out.columns and "year" in out.columns


def test_apply_cmie_column_aliases_empty_unchanged() -> None:
    df = pd.DataFrame()
    assert apply_cmie_column_aliases(df).empty
