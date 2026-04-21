"""
Optional CMIE / Prowess column aliases → internal names (extend as you lock indic layouts).

Applied before normalize_panel_like when raw tables use non-canonical headers.
"""

from __future__ import annotations

import re

import pandas as pd

# Lowercased column name → canonical name used by normalize_panel_like / api_financials
COLUMN_ALIASES: dict[str, str] = {
    "comp_code": "company_code",
    "companycode": "company_code",
    "firm_code": "company_code",
    "fy": "year",
    "financial_year": "year",
    "year_": "year",
}


def apply_cmie_column_aliases(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty or not len(df.columns):
        return df
    out = df.copy()
    rename = {}
    for c in out.columns:
        key = str(c).strip()
        low = key.lower()
        low = re.sub(r"\s+", "_", low)
        if low in COLUMN_ALIASES:
            rename[c] = COLUMN_ALIASES[low]
    if rename:
        out = out.rename(columns=rename)
    return out
