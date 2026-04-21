"""
Bulk Upload — CSV/Excel import, validation, Dickinson life-stage classification.
"""

import os
import tempfile

import pandas as pd
import streamlit as st

from helpers import classify_life_stage, winsorize, export_csv, export_excel, STAGE_COLORS
from models.data_ingest import (
    validate_upload, standardize_columns, enrich_with_classification,
    store_session_dataset, remove_session_dataset, list_available_datasets,
)

def fetch_cmie_data(api_key: str, company_code: str):
    """
    Download one company via CMIE wapicall (same contract as ``CmieClient`` / sidebar import),
    then parse the first tab-separated data file from the ZIP.
    """
    from cmie.client import CmieClient
    from cmie.errors import CmieError
    from cmie.wapicall_table import parse_cmie_company_download_zip

    key = (api_key or "").strip()
    if not key:
        return None, "API key is required."
    try:
        code = int(str(company_code).strip())
    except ValueError:
        return None, "Company code must be an integer."

    try:
        with tempfile.TemporaryDirectory(prefix="cmie_bulk_tab_") as td:
            zip_path = os.path.join(td, "wapicall.zip")
            client = CmieClient(key, timeout_s=600.0)
            client.download_wapicall_zip([code], dest_path=zip_path)
            try:
                df = parse_cmie_company_download_zip(zip_path)
            except pd.errors.EmptyDataError:
                return None, "CMIE returned an empty data table."
            except pd.errors.ParserError as e:
                return None, f"Could not parse CMIE TSV: {e}"
            if df is None or df.empty:
                return None, "CMIE zip contained no rows in the first data file."
            return df, None
    except CmieError as e:
        return None, str(e)
    except Exception as e:
        return None, f"Failed to fetch or parse data: {e}"

st.markdown("### Bulk Upload & Life Stage Classification")
st.caption("Upload company financial data to classify life stages or ingest for statistical analysis.")

tab1, tab2, tab3 = st.tabs(["Life Stage Classification", "Ingest for Analysis", "CMIE API Sync"])

# ═══════════════════════════════════════════════════════════════════════════════
# TAB 1 — Classify (original code, unchanged)
# ═══════════════════════════════════════════════════════════════════════════════
with tab1:
    # ── Required columns ──
    REQUIRED_COLS = ["company_name", "year", "ncfo", "ncfi", "ncff"]
    OPTIONAL_COLS = ["profitability", "tangibility", "tax", "firm_size", "leverage", "borrowings"]

    st.markdown("#### Required Columns")
    st.code(", ".join(REQUIRED_COLS), language=None)
    st.caption(f"Optional: {', '.join(OPTIONAL_COLS)}")

    # ── Sample template download ──
    sample = pd.DataFrame({
        "company_name": ["Acme Corp", "Beta Ltd", "Gamma Inc"],
        "year": [2023, 2023, 2023],
        "ncfo": [150.0, -50.0, 200.0],
        "ncfi": [-80.0, -30.0, -120.0],
        "ncff": [-60.0, 100.0, -40.0],
        "profitability": [12.5, -3.2, 18.0],
        "tangibility": [35.0, 22.0, 45.0],
        "leverage": [25.0, 55.0, 15.0],
    })

    st.download_button(
        "Download Sample Template (CSV)",
        data=export_csv(sample),
        file_name="lifecycle_template.csv",
        mime="text/csv",
    )

    st.divider()

    # ── File upload ──
    uploaded = st.file_uploader("Upload CSV or Excel file", type=["csv", "xlsx"], key="tab1_upload")

    if uploaded is not None:
        # Read file
        try:
            if uploaded.name.endswith(".csv"):
                df = pd.read_csv(uploaded)
            else:
                df = pd.read_excel(uploaded)
        except Exception as e:
            st.error(f"Failed to read file: {e}")
            st.stop()

        st.markdown(f"**Uploaded:** {len(df)} rows, {len(df.columns)} columns")

        # ── Validation ──
        errors = []
        warnings = []

        # Check required columns
        missing = [c for c in REQUIRED_COLS if c not in df.columns]
        if missing:
            errors.append(f"Missing required columns: {', '.join(missing)}")

        if errors:
            for e in errors:
                st.error(e)
            st.stop()

        # Type validation
        for col in ["ncfo", "ncfi", "ncff"]:
            if not pd.api.types.is_numeric_dtype(df[col]):
                try:
                    df[col] = pd.to_numeric(df[col], errors="coerce")
                    warnings.append(f"Column '{col}' had non-numeric values — coerced to NaN.")
                except Exception:
                    errors.append(f"Column '{col}' must be numeric.")

        # Null check
        null_rows = df[REQUIRED_COLS].isnull().any(axis=1).sum()
        if null_rows > 0:
            warnings.append(f"{null_rows} rows have missing values in required columns.")

        # Leverage outlier check
        if "leverage" in df.columns and pd.api.types.is_numeric_dtype(df["leverage"]):
            outliers = ((df["leverage"] < 0) | (df["leverage"] > 100)).sum()
            if outliers > 0:
                warnings.append(f"{outliers} rows have leverage outside 0-100% range (potential outliers).")

        # Display validation results
        valid_rows = len(df) - null_rows
        st.success(f"{valid_rows} rows are valid and ready for classification.")
        for w in warnings:
            st.warning(w)

        st.divider()

        # ── Life Stage Classification ──
        st.markdown("#### Classification Results")
        df["classified_life_stage"] = df.apply(
            lambda r: classify_life_stage(r["ncfo"], r["ncfi"], r["ncff"])
            if pd.notna(r["ncfo"]) and pd.notna(r["ncfi"]) and pd.notna(r["ncff"])
            else "Missing Data",
            axis=1,
        )

        # Summary
        stage_counts = df["classified_life_stage"].value_counts()
        sc1, sc2 = st.columns([1, 2])

        with sc1:
            st.markdown("**Distribution**")
            for stage, count in stage_counts.items():
                color = STAGE_COLORS.get(stage, "#6B7280")
                st.markdown(f":{color[1:]}[**{stage}**]: {count} firms")

        with sc2:
            st.markdown("**Classification Logic (Dickinson 2011)**")
            rules = pd.DataFrame({
                "Stage": ["Startup", "Growth", "Maturity", "Shakeout1", "Shakeout2", "Shakeout3", "Decline", "Decay"],
                "NCFo": ["-", "+", "+", "-", "+", "+", "-", "-"],
                "NCFi": ["-", "-", "-", "-", "+", "+", "+", "+"],
                "NCFf": ["+", "+", "-", "-", "+", "-", "+", "-"],
            })
            st.dataframe(rules, hide_index=True, use_container_width=True)

        st.divider()

        # ── Results table ──
        st.markdown("#### Enriched Data")

        # Highlight outlier rows
        display_cols = [c for c in df.columns if c in REQUIRED_COLS + OPTIONAL_COLS + ["classified_life_stage"]]
        st.dataframe(
            df[display_cols],
            use_container_width=True,
            hide_index=True,
            column_config={
                "classified_life_stage": st.column_config.TextColumn("Life Stage", width="medium"),
                "leverage": st.column_config.NumberColumn("Leverage (%)", format="%.1f"),
            },
        )

        # ── Export ──
        st.markdown("#### Export Results")
        ec1, ec2 = st.columns(2)
        with ec1:
            st.download_button(
                "Download as CSV",
                data=export_csv(df),
                file_name="classified_results.csv",
                mime="text/csv",
            )
        with ec2:
            st.download_button(
                "Download as Excel",
                data=export_excel(df),
                file_name="classified_results.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )

# ═══════════════════════════════════════════════════════════════════════════════
# TAB 2 — Ingest for Analysis
# ═══════════════════════════════════════════════════════════════════════════════
with tab2:
    st.markdown("#### Ingest External Data for Statistical Workbench")
    st.caption(
        "Upload any panel dataset (.csv, .xlsx, .dta). The engine auto-detects columns, "
        "standardizes names, optionally classifies life stages, and stores the dataset "
        "for use across all analysis pages."
    )

    # ── Step 1: File uploader ──
    ingest_file = st.file_uploader(
        "Upload a dataset", type=["csv", "xlsx", "dta"], key="tab2_ingest"
    )

    if ingest_file is not None:
        # Read file based on extension
        fname = ingest_file.name
        try:
            if fname.endswith(".csv"):
                ing_df = pd.read_csv(ingest_file)
            elif fname.endswith(".dta"):
                ing_df = pd.read_stata(ingest_file)
            else:
                ing_df = pd.read_excel(ingest_file)
        except Exception as exc:
            st.error(f"Failed to read file: {exc}")
            st.stop()

        st.markdown(f"**Loaded:** {len(ing_df):,} rows, {len(ing_df.columns)} columns")
        st.divider()

        # ── Step 2: Validate ──
        st.markdown("##### Validation")
        vresult = validate_upload(ing_df)

        if vresult["errors"]:
            for err in vresult["errors"]:
                st.error(err)
        else:
            st.success(
                f"Valid dataset — {vresult['n_rows']:,} rows, "
                f"{vresult['n_firms']:,} firms, "
                f"years {vresult['year_range'][0]}–{vresult['year_range'][1]}"
                if vresult["year_range"][0]
                else f"Valid dataset — {vresult['n_rows']:,} rows"
            )
        for wrn in vresult["warnings"]:
            st.warning(wrn)

        if not vresult["valid"]:
            st.info("Fix the errors above and re-upload.")
            st.stop()

        st.divider()

        # ── Step 3: Standardize columns ──
        st.markdown("##### Column Mapping")
        ing_df, rename_log = standardize_columns(ing_df, vresult["detected_columns"])

        if rename_log:
            for entry in rename_log:
                st.markdown(f"- {entry}")
        else:
            st.info("All columns already use standard names — no renaming needed.")

        matched = vresult["detected_columns"].get("matched", {})
        st.caption(f"Matched {len(matched)} standard columns: {', '.join(sorted(matched.keys()))}")

        st.divider()

        # ── Step 4: Enrich with Dickinson classification (if cash flows available) ──
        if vresult["has_cash_flows"]:
            st.markdown("##### Life Stage Classification")
            ing_df, classified = enrich_with_classification(ing_df)
            if classified:
                stage_dist = ing_df["life_stage"].value_counts()
                cols_dist = st.columns(min(len(stage_dist), 4))
                for idx, (stage, cnt) in enumerate(stage_dist.items()):
                    with cols_dist[idx % len(cols_dist)]:
                        color = STAGE_COLORS.get(stage, "#6B7280")
                        st.metric(stage, cnt)
                st.divider()
        else:
            st.info("No cash-flow columns (ncfo/ncfi/ncff) detected — skipping life stage classification.")
            st.divider()

        # ── Step 5: Data preview ──
        st.markdown("##### Data Preview (first 20 rows)")
        st.dataframe(ing_df.head(20), use_container_width=True, hide_index=True)
        st.divider()

        # ── Step 6: Store dataset ──
        st.markdown("##### Store Dataset")
        default_name = fname.rsplit(".", 1)[0]
        ds_name = st.text_input("Dataset name", value=default_name, key="ds_name_input")

        if st.button("Store as Session Dataset", type="primary", key="store_btn"):
            if not ds_name.strip():
                st.error("Please enter a dataset name.")
            else:
                stored = store_session_dataset(ing_df, ds_name.strip())
                if stored:
                    # ── Step 7: Success message ──
                    st.success(f"Available in Statistical Workbench as '{ds_name.strip()}'")
                else:
                    st.error("Maximum 3 uploaded datasets reached. Remove one below before adding another.")

    # ── Step 8: Active Datasets section (always visible) ──
    st.divider()
    st.markdown("##### Active Datasets")

    all_datasets = list_available_datasets()
    for ds in all_datasets:
        dc1, dc2, dc3 = st.columns([3, 2, 1])
        with dc1:
            label = ds["name"]
            if ds["source"] == "database":
                label += "  (built-in)"
            st.markdown(f"**{label}**")
        with dc2:
            st.caption(f"{ds['n_rows']:,} rows, {ds['n_firms']:,} firms")
        with dc3:
            if ds["source"] == "upload":
                if st.button("Remove", key=f"rm_{ds['name']}", type="secondary"):
                    remove_session_dataset(ds["name"])
                    st.rerun()

    if len(all_datasets) == 1:
        st.caption("No uploaded datasets yet. Upload a file above to get started.")

# ═══════════════════════════════════════════════════════════════════════════════
# TAB 3 — CMIE API Sync
# ═══════════════════════════════════════════════════════════════════════════════
with tab3:
    st.markdown("#### CMIE Economy API Integration")
    st.caption("Fetch live firm data directly from the CMIE database to classify life stages and run predictions.")
    st.info(
        "To load CMIE data into the **dashboard panel** (SQLite `api_financials`), use the **CMIE import** "
        "expander in the sidebar when `ENABLE_CMIE` is on. This tab only downloads and previews a single company ZIP."
    )

    with st.form("cmie_api_form"):
        api_col1, api_col2 = st.columns(2)
        with api_col1:
            api_key = st.text_input("CMIE API Key", type="password", help="Enter your registered CMIE Economy API key.")
        with api_col2:
            company_code = st.text_input("CMIE Company Code", placeholder="e.g., 100234")
            
        st.markdown("**Indicators to Fetch (Auto-Mapped to Dashboard Variables)**")
        st.code("NCFO, NCFI, NCFF, Total Assets, Borrowings, Net Profit, Tangible Assets, Tax Rate")
        
        use_mock = st.checkbox("Use Mock Data (Test Mode)", help="Generate fake CMIE data to test the pipeline without an API key.")
        submit_api = st.form_submit_button("Fetch & Analyze Data", type="primary")
        
    if submit_api:
        if not use_mock and (not api_key or not company_code):
            st.error("API Key and Company Code are required to initiate the request.")
        else:
            st.info("Initiating request...")
            
            with st.spinner("Fetching data from CMIE..."):
                if use_mock:
                    # Generate fake CMIE-formatted data for testing
                    import time
                    time.sleep(1) # Simulate network delay
                    df = pd.DataFrame({
                        "Company Code": [company_code or "100123"] * 5,
                        "Company Name": ["Mock Reliance Ind"] * 5,
                        "Year": [2019, 2020, 2021, 2022, 2023],
                        "NCFO": [120.5, 90.2, -30.0, 150.0, 200.0],
                        "NCFI": [-80.0, -100.0, -20.0, -90.0, -110.0],
                        "NCFF": [-40.0, 20.0, 60.0, -50.0, -80.0],
                        "Total_Assets": [1000, 1100, 1150, 1200, 1300],
                        "Borrowings": [400, 450, 500, 480, 420],
                        "Net_Profit": [50, 20, -10, 80, 110],
                        "Tangible_Assets": [600, 650, 630, 680, 700],
                        "Tax_Rate": [25.0, 25.0, 0.0, 25.0, 25.0]
                    })
                    error = None
                else:
                    df, error = fetch_cmie_data(api_key, company_code)
                
            if error:
                st.error(error)
            elif df is not None:
                st.success("Data fetched successfully!")
                
                st.markdown("##### Mapping CMIE Indicators")
                # NOTE: Adjust this mapping based on the actual CMIE API response headers
                cmie_mapping = {
                    "Company Code": "company_code",
                    "Company Name": "company_name",
                    "Year": "year",
                    "NCFO": "ncfo",
                    "NCFI": "ncfi",
                    "NCFF": "ncff",
                    "Total_Assets": "total_assets",
                    "Borrowings": "borrowings",
                    "Net_Profit": "profitability",
                    "Tangible_Assets": "tangibility",
                    "Tax_Rate": "tax"
                }
                
                df = df.rename(columns=cmie_mapping)
                st.dataframe(df.head(), use_container_width=True)
                
                if all(col in df.columns for col in ["ncfo", "ncfi", "ncff"]):
                    st.markdown("##### Life Stage Classification")
                    df, classified = enrich_with_classification(df)
                    if classified:
                        stage_dist = df["life_stage"].value_counts()
                        cols_dist = st.columns(min(len(stage_dist), 4))
                        for idx, (stage, cnt) in enumerate(stage_dist.items()):
                            with cols_dist[idx % len(cols_dist)]:
                                color = STAGE_COLORS.get(stage, "#6B7280")
                                st.metric(stage, cnt)
                
                ds_name = f"CMIE_{company_code}"
                if store_session_dataset(df, ds_name):
                    st.success(f"Dataset stored as '{ds_name}'. Available in Data Explorer and Econometrics Lab.")
                else:
                    st.error("Failed to store dataset. Maximum datasets reached.")
