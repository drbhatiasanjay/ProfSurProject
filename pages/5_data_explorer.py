"""
Data Explorer — Full filterable table with column selection, search, and export.
"""

import streamlit as st
import pandas as pd
import db
from helpers import export_csv, export_excel, format_pct, winsorize, ensure_session_state

ensure_session_state()
filters = st.session_state.filters
ft = db.filters_to_tuple(filters)

st.markdown("### Data Explorer")
_panel = st.session_state.get("panel_mode", "latest")
_panel_suffix = " · Latest panel (includes CMIE 2025)" if _panel == "latest" else " · Thesis panel (2001–2024)"
st.caption(f"Browse, filter, and export the full dataset. Respects sidebar filters.{_panel_suffix}")

# ── Column selection ──
ALL_COLUMNS = [
    "company_name", "nse_symbol", "industry_group", "year", "life_stage",
    "leverage", "profitability", "tangibility", "tax", "dividend",
    "firm_size", "tax_shield", "borrowings", "total_liabilities",
    "cash_holdings", "ncfo", "ncfi", "ncff", "promoter_share", "non_promoters",
]
DEFAULT_COLUMNS = [
    "company_name", "year", "life_stage", "leverage", "profitability",
    "tangibility", "firm_size", "borrowings",
]

selected_cols = st.multiselect(
    "Columns to display",
    options=ALL_COLUMNS,
    default=DEFAULT_COLUMNS,
)
if not selected_cols:
    selected_cols = DEFAULT_COLUMNS

# ── Inline filters ──
fc1, fc2 = st.columns(2)
with fc1:
    search_text = st.text_input("Search company name", placeholder="e.g. Reliance")
with fc2:
    lev_range = st.slider("Leverage range (%)", 0.0, 200.0, (0.0, 200.0), 1.0)

# ── Load data ──
with st.spinner("Loading data..."):
    if (
        db.is_cmie_lab_enabled()
        and getattr(st.session_state, "data_source_mode", "sqlite") == "cmie"
        and db.get_current_api_version()
    ):
        df = db.get_api_financials(db.get_current_api_version(), ft)
    else:
        df = db.get_full_data_explorer(ft)

if df.empty:
    st.warning("No data matches the current filters.")
    st.stop()

# Apply inline filters
if search_text:
    df = df[df["company_name"].str.contains(search_text, case=False, na=False)]

if "leverage" in df.columns:
    df = df[((df["leverage"] >= lev_range[0]) & (df["leverage"] <= lev_range[1])) | df["leverage"].isna()]

# Select columns
display_df = df[[c for c in selected_cols if c in df.columns]]

# ── Summary stats ──
st.markdown(f"**{len(display_df):,} rows** matching filters")

if not display_df.empty:
    # Numeric summary
    numeric_cols = display_df.select_dtypes(include="number").columns.tolist()
    if numeric_cols:
        stats_cols = st.columns(min(5, len(numeric_cols)))
        primary_col = "leverage" if "leverage" in numeric_cols else numeric_cols[0]
        col_data = display_df[primary_col].dropna()
        if not col_data.empty:
            with stats_cols[0]:
                st.metric("Count", f"{len(col_data):,}")
            with stats_cols[1 % len(stats_cols)]:
                st.metric(f"Mean {primary_col}", format_pct(col_data.mean()))
            with stats_cols[2 % len(stats_cols)]:
                st.metric(f"Median {primary_col}", format_pct(col_data.median()))
            with stats_cols[3 % len(stats_cols)]:
                st.metric(f"Std Dev", f"{col_data.std():.1f}")
            if len(stats_cols) > 4:
                with stats_cols[4]:
                    st.metric("Nulls", f"{display_df[primary_col].isna().sum()}")

    st.divider()

    # ── Data table ──
    column_config = {}
    if "leverage" in selected_cols:
        column_config["leverage"] = st.column_config.NumberColumn("Leverage (%)", format="%.1f")
    if "profitability" in selected_cols:
        column_config["profitability"] = st.column_config.NumberColumn("Profitability (%)", format="%.2f")
    if "tangibility" in selected_cols:
        column_config["tangibility"] = st.column_config.NumberColumn("Tangibility (%)", format="%.2f")
    if "firm_size" in selected_cols:
        column_config["firm_size"] = st.column_config.NumberColumn("Firm Size (Cr)", format="%.0f")
    if "borrowings" in selected_cols:
        column_config["borrowings"] = st.column_config.NumberColumn("Borrowings (Cr)", format="%.0f")

    st.dataframe(
        display_df,
        use_container_width=True,
        hide_index=True,
        column_config=column_config,
        height=500,
    )

    # ── Export ──
    st.divider()
    st.markdown("#### Export")
    ec1, ec2 = st.columns(2)
    with ec1:
        st.download_button(
            "Download CSV",
            data=export_csv(display_df),
            file_name="lifecycle_data_export.csv",
            mime="text/csv",
        )
    with ec2:
        st.download_button(
            "Download Excel",
            data=export_excel(display_df),
            file_name="lifecycle_data_export.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
