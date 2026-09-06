"""
Citation Inspector Modal Component for LifeCycle Leverage.

Implements native Streamlit @st.dialog modal for inspecting peer-reviewed citations,
verified DOIs, theoretical mechanisms, empirical benchmarks, and Indian panel relevance.
"""

import streamlit as st
from typing import Optional, Dict, Any

from models.citation_vault_metadata import (
    get_citation_metadata,
    format_bibtex,
    format_apa,
    format_stata_comment,
    list_all_citations,
)


@st.dialog("📖 Academic Citation Inspector")
def show_citation_dialog(citation_query: str):
    """Render a modal dialog with structured scholarly metadata for the citation."""
    meta = get_citation_metadata(citation_query)
    
    # Header badges
    category = meta.get("category", "EMPIRICAL LITERATURE")
    year = meta.get("year", "")
    journal = meta.get("journal", "")
    doi = meta.get("doi", "")
    
    cat_colors = {
        "METHODOLOGY": ("#0284c7", "rgba(2, 132, 199, 0.12)"),
        "JOURNAL OF FINANCE": ("#10b981", "rgba(16, 185, 129, 0.12)"),
        "EMPIRICAL LITERATURE": ("#8b5cf6", "rgba(139, 92, 246, 0.12)"),
        "INSTITUTIONAL REPORT": ("#f59e0b", "rgba(245, 158, 11, 0.12)"),
    }
    fg_col, bg_col = cat_colors.get(category, ("#0284c7", "rgba(2, 132, 199, 0.12)"))
    
    st.markdown(
        f"""
        <div style="display: flex; gap: 8px; align-items: center; margin-bottom: 8px; flex-wrap: wrap;">
            <span style="background: {bg_col}; color: {fg_col}; border: 1px solid {fg_col}40; padding: 2px 8px; border-radius: 12px; font-size: 11px; font-weight: 700;">
                {category}
            </span>
            <span style="font-size: 12px; color: #64748b; font-weight: 600;">
                {journal} ({year})
            </span>
        </div>
        <h4 style="margin: 0 0 6px 0; font-size: 16px; font-weight: 700; line-height: 1.3;">
            {meta.get('title', '')}
        </h4>
        <div style="font-size: 13px; color: #64748b; margin-bottom: 12px;">
            <b>Authors:</b> {meta.get('authors', '')}
        </div>
        """,
        unsafe_allow_html=True,
    )
    
    # DOI link button & metadata bar
    c1, c2 = st.columns([2, 1])
    with c1:
        if doi:
            st.link_button(f"🔗 Open Verified DOI ({doi.replace('https://doi.org/', '')})", doi, use_container_width=True)
    with c2:
        theories = meta.get("theories", [])
        if theories:
            st.caption(f"**Theories:** {', '.join(theories)}")

    st.divider()

    # Two column theoretical & empirical breakdown
    col_left, col_right = st.columns(2)
    with col_left:
        st.markdown(
            f"""
            <div style="background: rgba(56, 189, 248, 0.05); border: 1px solid rgba(56, 189, 248, 0.2); border-radius: 8px; padding: 12px; height: 100%;">
                <div style="font-size: 12px; font-weight: 700; color: #0284c7; margin-bottom: 4px;">
                    🔬 Theoretical Mechanism & Channel
                </div>
                <div style="font-size: 12.5px; line-height: 1.45; color: #334155;">
                    {meta.get('theoretical_mechanism', '')}
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with col_right:
        st.markdown(
            f"""
            <div style="background: rgba(16, 185, 129, 0.05); border: 1px solid rgba(16, 185, 129, 0.2); border-radius: 8px; padding: 12px; height: 100%;">
                <div style="font-size: 12px; font-weight: 700; color: #10b981; margin-bottom: 4px;">
                    📊 International Benchmark Findings
                </div>
                <div style="font-size: 12.5px; line-height: 1.45; color: #334155;">
                    {meta.get('empirical_benchmark', '')}
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("<div style='margin-top: 10px;'></div>", unsafe_allow_html=True)

    # Indian Panel Corroboration Card
    st.markdown(
        f"""
        <div style="background: rgba(245, 158, 11, 0.05); border: 1px solid rgba(245, 158, 11, 0.25); border-radius: 8px; padding: 12px;">
            <div style="font-size: 12px; font-weight: 700; color: #d97706; margin-bottom: 4px;">
                🇮🇳 Application to Indian Panel Dataset (N=8,677, CMIE Prowess 2001–2025)
            </div>
            <div style="font-size: 12.5px; line-height: 1.45; color: #334155;">
                {meta.get('indian_panel_relevance', '')}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("<div style='margin-top: 12px;'></div>", unsafe_allow_html=True)

    # Export Citation Tabs
    t_bib, t_apa, t_stata = st.tabs(["BibTeX", "APA 7th", "Stata Do-File"])
    with t_bib:
        st.code(format_bibtex(meta), language="latex")
    with t_apa:
        st.code(format_apa(meta), language="text")
    with t_stata:
        st.code(format_stata_comment(meta), language="stata")


def render_citation_selector():
    """Quick dropdown selector to inspect any catalog citation."""
    all_cits = list_all_citations()
    sel = st.selectbox(
        "Select literature benchmark to inspect:",
        all_cits,
        index=0,
        key="_cit_inspector_selector",
        label_visibility="collapsed",
    )
    if st.button(f"🔍 Inspect {sel}", key="_btn_inspect_sel", use_container_width=True):
        show_citation_dialog(sel)
