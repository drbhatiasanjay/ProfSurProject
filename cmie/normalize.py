from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Iterable, List, Optional, Tuple

import numpy as np
import pandas as pd

from cmie.errors import CmieSchemaError, CmieValidationError
from models.data_ingest import enrich_with_classification


CANONICAL_COLUMNS = [
    "company_code",
    "company_name",
    "nse_symbol",
    "industry_group",
    "year",
    "life_stage",
    "leverage",
    "profitability",
    "tangibility",
    "tax",
    "dividend",
    "firm_size",
    "log_size",
    "tax_shield",
    "borrowings",
    "total_liabilities",
    "cash_holdings",
    "ncfo",
    "ncfi",
    "ncff",
    "gfc",
    "ibc_2016",
    "covid_dummy",
]


@dataclass(frozen=True)
class NormalizeReport:
    n_rows_in: int
    n_rows_out: int
    missing_required: Dict[str, int]
    year_min: Optional[int]
    year_max: Optional[int]


def _to_num(s: pd.Series) -> pd.Series:
    return pd.to_numeric(s, errors="coerce")


def _add_event_dummies(df: pd.DataFrame) -> pd.DataFrame:
    # Match the existing DB year rules (approx):
    # GFC: 2008-2009, IBC: 2016+, COVID: 2020-2021
    df = df.copy()
    y = df["year"]
    df["gfc"] = ((y >= 2008) & (y <= 2009)).astype(int)
    df["ibc_2016"] = (y >= 2016).astype(int)
    df["covid_dummy"] = ((y >= 2020) & (y <= 2021)).astype(int)
    return df


def normalize_panel_like(
    df: pd.DataFrame,
    *,
    company_code_col: str = "company_code",
    year_col: str = "year",
    required_numeric: Optional[List[str]] = None,
) -> tuple[pd.DataFrame, NormalizeReport]:
    """
    Normalize any CMIE-parsed data into the canonical panel shape used by the app pages.

    This function is deliberately conservative: it will keep unknown extra columns out,
    coerce numeric fields, compute log_size, add event dummies, and run Dickinson if cash flows exist.
    """
    if required_numeric is None:
        required_numeric = ["leverage", "profitability", "tangibility", "firm_size"]

    if company_code_col not in df.columns or year_col not in df.columns:
        raise CmieSchemaError(
            code="SCHEMA",
            message="CMIE data missing required entity/time columns.",
            detail=f"Expected columns '{company_code_col}' and '{year_col}'. Found: {sorted(df.columns.tolist())[:30]}",
        )

    out = df.copy()

    # Standardize entity/time names
    if company_code_col != "company_code":
        out = out.rename(columns={company_code_col: "company_code"})
    if year_col != "year":
        out = out.rename(columns={year_col: "year"})

    out["company_code"] = pd.to_numeric(out["company_code"], errors="coerce").astype("Int64")
    out["year"] = pd.to_numeric(out["year"], errors="coerce").astype("Int64")
    out = out.dropna(subset=["company_code", "year"])
    out["company_code"] = out["company_code"].astype(int)
    out["year"] = out["year"].astype(int)

    # Numeric coercions for known columns if present
    numeric_cols = [
        "leverage",
        "profitability",
        "tangibility",
        "tax",
        "dividend",
        "firm_size",
        "tax_shield",
        "borrowings",
        "total_liabilities",
        "cash_holdings",
        "ncfo",
        "ncfi",
        "ncff",
    ]
    for c in numeric_cols:
        if c in out.columns:
            out[c] = _to_num(out[c])

    if "firm_size" in out.columns:
        out["log_size"] = np.log(out["firm_size"].where(out["firm_size"] > 0))

    # Dickinson classification (reuses existing helper)
    if "life_stage" not in out.columns:
        out, _classified = enrich_with_classification(out)

    out = _add_event_dummies(out)

    # Keep canonical columns when present
    keep = [c for c in CANONICAL_COLUMNS if c in out.columns]
    out = out[keep].copy()

    missing_required = {}
    for c in required_numeric:
        if c not in out.columns:
            missing_required[c] = len(out)
        else:
            missing_required[c] = int(out[c].isna().sum())

    yr_min = int(out["year"].min()) if "year" in out.columns and not out.empty else None
    yr_max = int(out["year"].max()) if "year" in out.columns and not out.empty else None

    rep = NormalizeReport(
        n_rows_in=len(df),
        n_rows_out=len(out),
        missing_required=missing_required,
        year_min=yr_min,
        year_max=yr_max,
    )
    return out, rep


def validate_panel(
    panel: pd.DataFrame,
    *,
    min_years: int = 3,
    max_missing_frac: float = 0.35,
    required_cols: Optional[List[str]] = None,
) -> None:
    if required_cols is None:
        required_cols = ["company_code", "year", "leverage"]

    missing = [c for c in required_cols if c not in panel.columns]
    if missing:
        raise CmieValidationError(code="VALIDATION", message="Normalized panel is missing required columns.", detail=str(missing))

    if panel.empty:
        raise CmieValidationError(code="VALIDATION", message="No rows in normalized panel after cleaning.")

    years = panel["year"].nunique()
    if years < min_years:
        raise CmieValidationError(
            code="VALIDATION",
            message="Too few years returned for forecasting/econometrics.",
            detail=f"Got {years} unique years; need at least {min_years}.",
        )

    # Missingness checks for key fields (soft guardrail)
    key_fields = [c for c in ["leverage", "profitability", "tangibility", "firm_size"] if c in panel.columns]
    for c in key_fields:
        frac = float(panel[c].isna().mean())
        if frac > max_missing_frac:
            raise CmieValidationError(
                code="VALIDATION",
                message=f"Too much missing data in '{c}'.",
                detail=f"Missing fraction {frac:.0%} exceeds {max_missing_frac:.0%}.",
            )

