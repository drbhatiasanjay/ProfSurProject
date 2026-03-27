"""
Bulk Upload — CSV/Excel import, validation, Dickinson life-stage classification.
"""

import streamlit as st
import pandas as pd
from helpers import classify_life_stage, winsorize, export_csv, export_excel, STAGE_COLORS

st.markdown("### Bulk Upload & Life Stage Classification")
st.caption("Upload company financial data to classify life stages using the Dickinson (2011) cash-flow method.")

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
uploaded = st.file_uploader("Upload CSV or Excel file", type=["csv", "xlsx"])

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
