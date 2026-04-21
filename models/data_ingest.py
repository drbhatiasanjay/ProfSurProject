"""
Data Ingestion Engine — validate, standardize, classify, and store uploaded datasets.
"""
import pandas as pd
import numpy as np
import streamlit as st

# Standard column name mappings (CMIE Prowess variants -> our schema)
COLUMN_ALIASES = {
    # Entity/time
    "company_name": ["company_name", "comp_name", "firm_name", "name", "company"],
    "company_code": ["company_code", "comp_code", "firm_code", "code", "companycode"],
    "year": ["year", "yr", "fiscal_year", "fy", "period"],
    # Financials
    "leverage": ["leverage", "lev", "debt_ratio", "financial_leverage", "debt_equity"],
    "profitability": ["profitability", "prof", "roa", "pbdita_ta", "ebitda_ta", "return_on_assets"],
    "tangibility": ["tangibility", "tang", "fixed_assets_ta", "nfa_ta", "asset_tangibility"],
    "tax": ["tax", "tax_rate", "effective_tax", "corporate_tax"],
    "firm_size": ["firm_size", "size", "total_assets", "assets"],
    "log_size": ["log_size", "logsize", "ln_size", "lnsize", "log_assets"],
    "tax_shield": ["tax_shield", "taxshield", "ndts", "depreciation_ta"],
    "dividend": ["dividend", "dvnd", "div_payout", "dividend_payout"],
    "interest": ["interest", "interest_expense", "int_expense"],
    "borrowings": ["borrowings", "total_debt", "debt", "total_borrowings"],
    "total_liabilities": ["total_liabilities", "liabilities"],
    "cash_holdings": ["cash_holdings", "cash", "cash_and_equivalents"],
    # Cash flows (for Dickinson classification)
    "ncfo": ["ncfo", "ocf", "cfo", "operating_cf", "cash_from_operations"],
    "ncfi": ["ncfi", "icf", "cfi", "investing_cf", "cash_from_investing"],
    "ncff": ["ncff", "fcf_financing", "cff", "financing_cf", "cash_from_financing"],
    # Ownership
    "promoter_share": ["promoter_share", "pmshare", "promoter_holding", "promoter_pct"],
    "non_promoters": ["non_promoters", "public_holding", "non_promoter_share"],
    # Event dummies
    "gfc": ["gfc", "global_financial_crisis"],
    "ibc_2016": ["ibc_2016", "ibc", "insolvency"],
    "covid_dummy": ["covid_dummy", "covid", "pandemic"],
    # Market
    "int_rate": ["int_rate", "interest_rate", "rbi_rate", "policy_rate"],
}


def validate_upload(df):
    """
    Validate uploaded DataFrame. Returns dict with:
    valid (bool), errors (list), warnings (list), detected_columns (dict),
    n_rows, n_firms, year_range, has_cash_flows (bool for Dickinson)
    """
    errors = []
    warnings = []
    detected = {}

    if df is None or df.empty:
        return {
            "valid": False,
            "errors": ["Empty dataset"],
            "warnings": [],
            "detected_columns": {},
            "n_rows": 0,
            "n_firms": 0,
            "year_range": (None, None),
            "has_cash_flows": False,
        }

    cols_lower = {c.lower().strip().replace(" ", "_"): c for c in df.columns}

    # Check for entity column
    has_entity = False
    for std_name in ["company_name", "company_code"]:
        for alias in COLUMN_ALIASES[std_name]:
            if alias.lower() in cols_lower:
                has_entity = True
                detected["entity"] = cols_lower[alias.lower()]
                break
        if has_entity:
            break
    if not has_entity:
        errors.append("Missing entity column (company_name or company_code)")

    # Check for time column
    has_time = False
    for alias in COLUMN_ALIASES["year"]:
        if alias.lower() in cols_lower:
            has_time = True
            detected["time"] = cols_lower[alias.lower()]
            break
    if not has_time:
        errors.append("Missing time column (year)")

    # Detect numeric columns
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    detected["numeric"] = numeric_cols
    if len(numeric_cols) < 1:
        errors.append("No numeric columns found — need at least one for analysis")

    # Detect standard financial columns
    detected["matched"] = {}
    for std_name, aliases in COLUMN_ALIASES.items():
        for alias in aliases:
            if alias.lower() in cols_lower:
                detected["matched"][std_name] = cols_lower[alias.lower()]
                break

    # Check for cash flows (Dickinson classification capability)
    has_cf = all(k in detected["matched"] for k in ["ncfo", "ncfi", "ncff"])

    # Warnings
    for col in df.columns:
        pct_missing = df[col].isna().mean()
        if pct_missing > 0.2:
            warnings.append(f"Column '{col}' has {pct_missing:.0%} missing values")

    if "leverage" in detected["matched"]:
        lev_col = detected["matched"]["leverage"]
        lev = df[lev_col].dropna()
        if len(lev) > 0:
            if lev.max() > 200:
                warnings.append(
                    f"Leverage has extreme values (max={lev.max():.1f}%) — consider winsorizing"
                )
            if lev.min() < 0:
                warnings.append(
                    f"Leverage has negative values (min={lev.min():.1f}%) — check data"
                )

    # Compute summary stats
    n_rows = len(df)
    entity_col = detected.get("entity")
    n_firms = df[entity_col].nunique() if entity_col else n_rows
    time_col = detected.get("time")
    if time_col and time_col in df.columns:
        try:
            years = pd.to_numeric(df[time_col], errors="coerce").dropna()
            year_range = (int(years.min()), int(years.max())) if len(years) > 0 else (None, None)
        except Exception:
            year_range = (None, None)
    else:
        year_range = (None, None)

    return {
        "valid": len(errors) == 0,
        "errors": errors,
        "warnings": warnings,
        "detected_columns": detected,
        "n_rows": n_rows,
        "n_firms": n_firms,
        "year_range": year_range,
        "has_cash_flows": has_cf,
    }


def standardize_columns(df, detected_columns):
    """
    Rename detected columns to standard names.
    Returns (standardized_df, rename_log).
    """
    rename_map = {}
    for std_name, orig_col in detected_columns.get("matched", {}).items():
        if orig_col in df.columns and orig_col != std_name:
            rename_map[orig_col] = std_name

    result = df.rename(columns=rename_map)

    # Ensure entity column is named company_code or company_name
    entity_col = detected_columns.get("entity")
    if entity_col and entity_col in result.columns:
        if entity_col not in ["company_code", "company_name"]:
            result = result.rename(columns={entity_col: "company_name"})
            rename_map[entity_col] = "company_name"

    # Ensure company_code exists (create from company_name if needed)
    if "company_code" not in result.columns and "company_name" in result.columns:
        codes = {name: i + 1 for i, name in enumerate(result["company_name"].unique())}
        result["company_code"] = result["company_name"].map(codes)

    # Ensure year is numeric
    time_col = detected_columns.get("time")
    if time_col and time_col in df.columns:
        if time_col != "year":
            result = result.rename(columns={time_col: "year"})
            rename_map[time_col] = "year"
        result["year"] = pd.to_numeric(result["year"], errors="coerce")

    log = [f"'{orig}' -> '{std}'" for orig, std in rename_map.items()]
    return result, log


def enrich_with_classification(df):
    """
    Add life_stage column using Dickinson (2011) if ncfo/ncfi/ncff present.
    Returns (enriched_df, classified_bool).
    """
    from helpers import classify_life_stage

    if not all(c in df.columns for c in ["ncfo", "ncfi", "ncff"]):
        return df, False

    df = df.copy()
    df["life_stage"] = df.apply(
        lambda r: classify_life_stage(r["ncfo"], r["ncfi"], r["ncff"])
        if pd.notna(r["ncfo"]) and pd.notna(r["ncfi"]) and pd.notna(r["ncff"])
        else "Unclassified",
        axis=1,
    )
    return df, True


def store_session_dataset(df, name):
    """
    Store DataFrame in st.session_state.datasets. Max 3 uploads.
    Returns True if stored, False if limit reached.
    """
    if "datasets" not in st.session_state:
        st.session_state.datasets = {}

    if len(st.session_state.datasets) >= 3 and name not in st.session_state.datasets:
        return False

    st.session_state.datasets[name] = {
        "df": df,
        "n_rows": len(df),
        "n_firms": df["company_code"].nunique() if "company_code" in df.columns else len(df),
        "year_range": (
            (int(df["year"].min()), int(df["year"].max()))
            if "year" in df.columns
            else (None, None)
        ),
        "columns": list(df.columns),
    }
    return True


def remove_session_dataset(name):
    """Remove a dataset from session state."""
    if "datasets" in st.session_state and name in st.session_state.datasets:
        del st.session_state.datasets[name]


def list_available_datasets():
    """
    List all available datasets (default + uploaded).
    Returns list of dicts with name, source, n_rows, n_firms.
    """
    datasets = [
        {
            "name": "Default (401 firms, 2001-2024)",
            "source": "database",
            "n_rows": 8677,
            "n_firms": 401,
        }
    ]

    if "datasets" in st.session_state:
        for name, info in st.session_state.datasets.items():
            datasets.append({
                "name": name,
                "source": "upload",
                "n_rows": info["n_rows"],
                "n_firms": info["n_firms"],
            })
    return datasets


def get_dataset(name, filters=None):
    """
    Retrieve dataset by name.
    "Default" -> db.get_active_panel_data(). Uploaded -> session state.
    """
    if name.startswith("Default"):
        import db

        if filters:
            ft = db.filters_to_tuple(filters)
            return db.get_active_panel_data(ft)
        else:
            # Return unfiltered panel data with a minimal filter
            ft = db.filters_to_tuple({
                "company_codes": [],
                "year_range": (2001, 2024),
                "life_stages": [],
                "industry_groups": [],
                "events": {"gfc": False, "ibc": False, "covid": False},
            })
            return db.get_active_panel_data(ft)

    if "datasets" in st.session_state and name in st.session_state.datasets:
        return st.session_state.datasets[name]["df"].copy()

    return pd.DataFrame()
