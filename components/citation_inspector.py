"""
Citation Inspector Modal Component for LifeCycle Leverage.

Implements native Streamlit @st.dialog modal for inspecting peer-reviewed citations,
verified DOIs, theoretical mechanisms, empirical benchmarks, and Indian panel relevance.
"""

import re
import streamlit as st
from typing import Optional, Dict, Any

from models.citation_vault_metadata import (
    get_citation_metadata,
    format_bibtex,
    format_apa,
    format_stata_comment,
    list_all_citations,
)


def get_safe_button_key(citation_key: str, scope: str = "default", idx: int = 0) -> str:
    """Generate a collision-free, syntax-clean Streamlit widget key."""
    clean_key = re.sub(r"[^a-zA-Z0-9_]", "_", str(citation_key).lower())
    return f"btn_cit_{scope}_{clean_key}_{idx}"


@st.dialog("📖 Academic Citation Inspector")
def show_citation_dialog(citation_query: str):
    """Render a modal dialog with structured scholarly metadata for the citation."""
    is_dark = st.session_state.get("theme", "light") == "dark"
    title_color = "#F8FAFC" if is_dark else "#0F172A"
    body_color = "#CBD5E1" if is_dark else "#334155"
    muted_color = "#94A3B8" if is_dark else "#475569"
    st.markdown(
        f"""
        <style>
        div[data-testid="stDialog"] div[role="dialog"] {
            background-color: #0b1120 !important;
            color: #f1f5f9 !important;
            border: 1px solid rgba(56, 189, 248, 0.3) !important;
            border-radius: 14px !important;
            box-shadow: 0 20px 50px rgba(0, 0, 0, 0.8) !important;
        }
        div[data-testid="stDialog"] h4 {
            color: {title_color} !important;
        }
        div[data-testid="stDialog"] .stCaption, div[data-testid="stDialog"] p {
            color: {body_color} !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    meta = get_citation_metadata(citation_query)
    
    # Header badges
    category = meta.get("category", "EMPIRICAL LITERATURE")
    year = meta.get("year", "")
    journal = meta.get("journal", "")
    doi = meta.get("doi", "")
    
    cat_colors = {
        "METHODOLOGY": ("#0284c7", "rgba(2, 132, 199, 0.12)"),
        "JOURNAL OF FINANCE": ("#059669", "rgba(5, 150, 105, 0.12)"),
        "EMPIRICAL LITERATURE": ("#7c3aed", "rgba(124, 58, 237, 0.12)"),
        "INSTITUTIONAL REPORT": ("#d97706", "rgba(217, 119, 6, 0.12)"),
    }
    fg_col, bg_col = cat_colors.get(category, ("#0284c7", "rgba(2, 132, 199, 0.12)"))
    
    st.markdown(
        f"""
        <div style="display: flex; gap: 8px; align-items: center; margin-bottom: 8px; flex-wrap: wrap;">
            <span style="background: {bg_col}; color: {fg_col}; border: 1px solid {fg_col}50; padding: 2px 10px; border-radius: 12px; font-size: 11px; font-weight: 700; letter-spacing: 0.04em;">
                {category}
            </span>
            <span style="font-size: 12.5px; color: {muted_color}; font-weight: 600;">
                {journal} ({year})
            </span>
        </div>
        <h3 style="margin: 0 0 6px 0; font-size: 18px; font-weight: 800; line-height: 1.35; color: {title_color} !important;">
            {meta.get('title', '')}
        </h3>
        <div style="font-size: 13.5px; color: {body_color} !important; margin-bottom: 12px;">
            <b style="color: {title_color} !important;">Authors:</b> {meta.get('authors', '')}
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
            <div style="background: #f0f9ff; border: 1px solid #bae6fd; border-radius: 8px; padding: 12px; height: 100%;">
                <div style="font-size: 12px; font-weight: 700; color: #0369a1; margin-bottom: 6px;">
                    🔬 Theoretical Mechanism & Channel
                </div>
                <div style="font-size: 12.5px; line-height: 1.5; color: #1e293b;">
                    {meta.get('theoretical_mechanism', '')}
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with col_right:
        st.markdown(
            f"""
            <div style="background: #ecfdf5; border: 1px solid #a7f3d0; border-radius: 8px; padding: 12px; height: 100%;">
                <div style="font-size: 12px; font-weight: 700; color: #047857; margin-bottom: 6px;">
                    📊 International Benchmark Findings
                </div>
                <div style="font-size: 12.5px; line-height: 1.5; color: #1e293b;">
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
        <div style="background: #fffbeb; border: 1px solid #fde68a; border-radius: 8px; padding: 12px;">
            <div style="font-size: 12px; font-weight: 700; color: #b45309; margin-bottom: 6px;">
                🇮🇳 Application to Indian Panel Dataset (N=8,677, CMIE Prowess 2001–2025)
            </div>
            <div style="font-size: 12.5px; line-height: 1.5; color: #1e293b;">
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


def render_citation_badge_button(citation_key: str, scope: str = "default", idx: int = 0) -> bool:
    """Render an inline citation inspection button with collision-free keying."""
    btn_id = get_safe_button_key(citation_key, scope=scope, idx=idx)
    raw_label = str(citation_key).strip()
    label = f"📖 {raw_label}" if len(raw_label) <= 24 else f"📖 {raw_label[:21].rstrip()}…"
    if st.button(label, key=btn_id, help=f"Inspect scholarly citation details for {citation_key}", use_container_width=True):
        show_citation_dialog(citation_key)
        return True
    return False


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
