"""
Page 17 — Company Board Deck Generator

Individual-company analysis: select one firm, choose analytical topics,
preview interactive charts, download a branded .pptx board deck.

Distinct from all other pages (1–16) which are panel-wide thesis analyses.
Here the company is the SUBJECT; the 401-firm panel is the PEER CONTEXT.
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px

import db
from helpers import (
    ensure_session_state, require_role, plotly_layout,
    PLOTLY_CONFIG, STAGE_COLORS, render_interpretation, new_badge,
    df_download_button, chart_download_button,
    render_bento_kpi, render_stage_badge,
    PRIMARY, SECONDARY, ACCENT, NEUTRAL,
)
from models.board_export import TOPIC_BUILDERS, TOPIC_LABELS, build_topic_ai_narrative, board_ratios
from models.debt_board import get_thesis_companies
from models.econometric_literature_vault import get_relevant_vault_citations
from models.rich_chat_renderer import render_academic_vault_html
import models.pptx_generator as pptx_generator

ensure_session_state()
db.log_page_visit("Board Export")
require_role("admin", "researcher")

# ── Page header ───────────────────────────────────────────────────────────────
st.markdown(f"### Company Board Deck {new_badge()}", unsafe_allow_html=True)
st.caption(
    "Select a company, choose which analytical topics to include, preview the deck, "
    "then download a branded .pptx board presentation. "
    "All analysis uses the Thesis panel (2001–2024) with the company's life-stage peers as context."
)

# ── STEP 1: Company selector ──────────────────────────────────────────────────
_username  = st.session_state.get("user", {}).get("username", "")
_bd_prefs  = db.load_user_prefs(_username, "board_deck") if _username else {}

try:
    with st.spinner("Loading..."):
        companies_df = get_thesis_companies()
except Exception as _e:
    st.error(f"Failed to load company list. Please refresh. ({_e})")
    st.stop()
if companies_df.empty:
    st.warning("No companies have observations in the Thesis panel.")
    st.stop()
_company_codes = companies_df.company_code.astype(int).tolist()
_company_names = dict(zip(_company_codes, companies_df.company_name))
_duplicate_names = set(companies_df.loc[companies_df.company_name.duplicated(False), "company_name"])
_saved_code = _bd_prefs.get("selected_company_code")
if _saved_code not in _company_codes:
    _saved_code = next((code for code in _company_codes if _company_names[code] == _bd_prefs.get("selected_company")), _company_codes[0])

col_co, col_info = st.columns([2, 1])
with col_co:
    company_code = st.selectbox(
        "Select company",
        options=_company_codes,
        index=_company_codes.index(_saved_code),
        format_func=lambda code: f"{_company_names[code]} ({code})" if _company_names[code] in _duplicate_names else _company_names[code],
        help="Indian-company analysis against the frozen Thesis panel.",
    )
selected_name = _company_names[company_code]

# Persist company selection
if _username:
    _bd_prefs = dict(_bd_prefs, selected_company=selected_name, selected_company_code=int(company_code))
    db.save_user_pref(_username, "board_deck", _bd_prefs)
company_row = companies_df[companies_df["company_code"] == company_code].iloc[0]
company_code = int(company_code)
panel_mode = "thesis"  # page 17 is always thesis-pinned
st.session_state["active_company_cin"] = company_code


# ── STEP 2: Load data ─────────────────────────────────────────────────────────
@st.cache_data(ttl=300, show_spinner=False)
def _load_company_data(company_code: int):
    thesis_ft = db.filters_to_tuple({
        "panel_mode": "thesis",
        "company_codes": [],
        "year_range": (2001, 2024),
        "life_stages": [],
        "industry_groups": [],
        "events": {"gfc": False, "ibc": False, "covid": False},
    })
    full_panel    = db.get_filtered_financials(thesis_ft)
    company_df    = db._query("SELECT * FROM financials WHERE company_code = ? AND vintage = ? ORDER BY year", [company_code, "thesis"])
    stage_summary = db.get_life_stage_summary(thesis_ft)
    same_year = full_panel[full_panel.year == company_df.year.max()] if not company_df.empty else full_panel.iloc[:0]
    peers_df      = db.get_company_peers(company_code, same_year)
    return company_df, full_panel, stage_summary, peers_df


try:
    with st.spinner("Loading company data…"):
        company_df, full_panel, stage_summary, peers_df = _load_company_data(company_code)
except Exception as _e:
    st.error(f"Failed to load data. Please refresh. ({_e})")
    st.stop()

if company_df.empty:
    st.warning("No financial data found for this company in the Thesis panel.")
    st.stop()

# Build company_info dict used across all topic functions
_latest = company_df.sort_values("year").iloc[-1]
company_info = {
    "name":          selected_name,
    "code":          company_code,
    "industry":      company_row.get("industry_group", ""),
    "current_stage": _latest.get("life_stage", "Unknown"),
    "last_year":     int(_latest.get("year", 2024)),
}

_deck_modes = ["Full analytical deck (13 topics)", "Debt strategy board deck"]
deck_mode = st.radio("Deck format", _deck_modes,
    index=_deck_modes.index(_bd_prefs.get("deck_mode")) if _bd_prefs.get("deck_workflow_version") == 2 and _bd_prefs.get("deck_mode") in _deck_modes else 0,
    key="p17_deck_mode_v2", horizontal=True)
_bd_prefs = dict(_bd_prefs, deck_mode=deck_mode, deck_workflow_version=2)
if _username:
    db.save_user_pref(_username, "board_deck", _bd_prefs)
if deck_mode == "Debt strategy board deck":
    from components.debt_board_view import render_debt_board
    render_debt_board(company_df, company_info, peers_df, full_panel, stage_summary, _bd_prefs)
    st.stop()

# Legacy analytical visuals consume ratios, while the DB stores leverage in percent.
company_df, peers_df, full_panel, stage_summary = map(board_ratios, (company_df, peers_df, full_panel, stage_summary))
_latest = company_df.sort_values("year").iloc[-1]

# ── STEP 3: Snapshot header & Executive Bento Grid ────────────────────────────
stage = company_info["current_stage"]
stage_color = STAGE_COLORS.get(stage, "#0D9488")
lev_val = float(_latest.get("leverage", 0) or 0)
prof_val = float(_latest.get("profitability", 0) or 0)
tang_val = float(_latest.get("tangibility", 0) or 0)
pbit_val = float(_latest.get("pbit", 0) or 0)
int_val = float(_latest.get("interest_amt", 0) or 0)
ic_val = (pbit_val / int_val) if int_val > 0 else np.nan

n_peers = len(peers_df) if peers_df is not None else 0
peer_lev_med = float(peers_df["leverage"].median()) if peers_df is not None and not peers_df.empty and "leverage" in peers_df.columns else lev_val
peer_prof_med = float(peers_df["profitability"].median()) if peers_df is not None and not peers_df.empty and "profitability" in peers_df.columns else prof_val

from scipy import stats
def _calc_pct(series, val):
    clean = series.dropna() if series is not None else pd.Series([], dtype=float)
    return int(stats.percentileofscore(clean, val, kind="rank")) if not clean.empty else 50

lev_pct = _calc_pct(peers_df["leverage"] if peers_df is not None and not peers_df.empty else None, lev_val)
prof_pct = _calc_pct(peers_df["profitability"] if peers_df is not None and not peers_df.empty else None, prof_val)
tang_pct = _calc_pct(peers_df["tangibility"] if peers_df is not None and not peers_df.empty else None, tang_val)

df_hist = company_df.sort_values("year").tail(5)
lev_spark = (df_hist["leverage"] * 100).dropna().tolist() if "leverage" in df_hist.columns else []
prof_spark = (df_hist["profitability"] * 100).dropna().tolist() if "profitability" in df_hist.columns else []
tang_spark = (df_hist["tangibility"] * 100).dropna().tolist() if "tangibility" in df_hist.columns else []

with col_info:
    is_dark = st.session_state.get("theme", "light") == "dark"
    card_bg = "rgba(20, 24, 36, 0.85)" if is_dark else "#F0FDFA"
    text_color = "#F8FAFC" if is_dark else "#0F172A"
    sub_color = "#94A3B8" if is_dark else "#64748B"
    box_border = "rgba(255, 255, 255, 0.12)" if is_dark else "#E2E8F0"

    st.markdown(
        f"""<div style="background:{card_bg};border:1px solid {box_border};border-left:4px solid {stage_color};padding:12px 16px;border-radius:8px;font-size:13px;color:{text_color};box-shadow:0 2px 8px rgba(0,0,0,0.25);">
        <div style="font-size:14px;font-weight:700;color:{text_color};margin-bottom:4px;">
            {selected_name} &nbsp;·&nbsp; <span style="background:{stage_color}25;color:{stage_color};border:1px solid {stage_color}55;padding:2px 8px;border-radius:4px;font-weight:700;font-size:11px;">{stage}</span>
        </div>
        <div style="color:{sub_color};line-height:1.45;">
            Industry: <strong style="color:{text_color};">{company_info['industry'] or 'Panel Cohort'}</strong> &nbsp;·&nbsp; Fiscal Year: <strong style="color:{text_color};">{company_info['last_year']}</strong><br>
            Peer Benchmark: <strong style="color:{text_color};">{n_peers} firms</strong> in same life-cycle stage
        </div>
        </div>""",
        unsafe_allow_html=True,
    )

# Executive Bento KPI Row
bcol1, bcol2, bcol3, bcol4 = st.columns(4)
with bcol1:
    lev_delta = f"{(lev_val - peer_lev_med)*100:+.1f}% vs peer med"
    st.markdown(render_bento_kpi(
        title="Leverage (Total Debt / Assets)",
        value=f"{lev_val*100:.1f}%",
        delta=lev_delta,
        sparkline_data=lev_spark,
        percentile=lev_pct,
        tag=f"{lev_pct}th Pctile",
        help_text="Book leverage vs life-stage peers",
        stroke_color=PRIMARY,
    ), unsafe_allow_html=True)

with bcol2:
    prof_delta = f"{(prof_val - peer_prof_med)*100:+.1f}% vs peer med"
    st.markdown(render_bento_kpi(
        title="Operating ROA (PBIT / Assets)",
        value=f"{prof_val*100:.1f}%",
        delta=prof_delta,
        sparkline_data=prof_spark,
        percentile=prof_pct,
        tag=f"{prof_pct}th Pctile",
        help_text="Operating profitability vs life-stage peers",
        stroke_color=SECONDARY,
    ), unsafe_allow_html=True)

with bcol3:
    st.markdown(render_bento_kpi(
        title="Asset Tangibility (PPE / Assets)",
        value=f"{tang_val*100:.1f}%",
        delta=f"P{tang_pct}",
        sparkline_data=tang_spark,
        percentile=tang_pct,
        tag="Collateral Base",
        help_text="Fixed asset proportion available for debt collateralization",
        stroke_color=ACCENT,
    ), unsafe_allow_html=True)

with bcol4:
    ic_tag = "Robust Safety" if (pd.notna(ic_val) and ic_val >= 3.0) else ("Moderate Cover" if (pd.notna(ic_val) and ic_val >= 1.5) else "Elevated Risk")
    ic_str = f"{ic_val:.1f}x" if pd.notna(ic_val) and ic_val < 90 else (">50x" if ic_val >= 90 else "N/A")
    st.markdown(render_bento_kpi(
        title="Interest Coverage (EBIT / Interest)",
        value=ic_str,
        delta=ic_tag,
        sparkline_data=[],
        percentile=min(100, max(10, int(ic_val * 15))) if (pd.notna(ic_val) and ic_val < 50) else 95,
        tag="Debt Servicing",
        help_text="Ability of operating earnings to service debt interest burden",
        stroke_color="#10B981" if ic_tag == "Robust Safety" else "#F59E0B",
    ), unsafe_allow_html=True)

st.divider()

# ── STEP 4: Topic checklist ───────────────────────────────────────────────────
st.markdown("#### Select slides for your deck")
st.caption("All topics pre-selected — uncheck any you want to exclude.")

col_selall, col_deselall, _ = st.columns([1, 1, 4])
select_all   = col_selall.button("Select All",   key="sel_all")
deselect_all = col_deselall.button("Unselect All", key="desel_all")

# Initialise selection state & sync widget keys
if "deck_selection" not in st.session_state or select_all or deselect_all:
    _target_val = False if deselect_all else True
    st.session_state["deck_selection"] = {tid: _target_val for tid in TOPIC_LABELS}
    if select_all or deselect_all:
        for tid in TOPIC_LABELS:
            st.session_state[f"topic_{tid}"] = _target_val
        st.rerun()

selected_topics: dict[int, bool] = {}

# Render checkboxes in 2 columns of expanders
left_ids  = [1, 2, 3, 4, 5, 6, 7]
right_ids = [8, 9, 10, 11, 12, 13]

col_left, col_right = st.columns(2)

for col, ids in [(col_left, left_ids), (col_right, right_ids)]:
    with col:
        for tid in ids:
            label = TOPIC_LABELS[tid]
            with st.expander(f"**{tid}. {label}**", expanded=False):
                val = st.checkbox(
                    f"Include Topic {tid} — {label}",
                    value=st.session_state["deck_selection"].get(tid, True),
                    key=f"topic_{tid}",
                )
                st.session_state["deck_selection"][tid] = val
            selected_topics[tid] = st.session_state["deck_selection"].get(tid, True)

n_selected = sum(selected_topics.values())
st.caption(f"**{n_selected} of {len(TOPIC_LABELS)} topics selected** ({n_selected} sections in deck).")

st.divider()

# ── AI Narratives toggle ──────────────────────────────────────────────────────
ai_narratives_on = st.toggle(
    "Include AI Narratives",
    value=False,
    key="p17_ai_narratives",
    help="Generate a 100-150 word board-ready prose summary for each topic via Claude Sonnet. Adds ~5s per topic on first run; results are cached.",
)

# ── STEP 5: Action buttons ────────────────────────────────────────────────────
col_prev, col_dl, col_clear = st.columns([1.2, 1.2, 1])
preview_clicked  = col_prev.button("Preview Deck",         type="primary",   key="preview_btn")
download_clicked = col_dl.button("Generate & Download .pptx", type="secondary", key="dl_btn")
if col_clear.button("Clear Preview", key="clear_btn"):
    st.session_state.pop("deck_previewed", None)
    st.rerun()

if preview_clicked:
    st.session_state["deck_previewed"] = True

preview_topics = {}

# ── STEP 6: Preview ───────────────────────────────────────────────────────────
if st.session_state.get("deck_previewed"):
    st.markdown("---")
    st.markdown(f"#### Preview — {selected_name} Board Deck ({n_selected} topics)")
    st.caption(
        "Interactive preview using the same charts that will appear in the .pptx. "
        "Hover over charts to see values. Click 'Generate & Download .pptx' above to export."
    )

    for tid in sorted(selected_topics.keys()):
        if not selected_topics[tid]:
            continue
        builder = TOPIC_BUILDERS.get(tid)
        if builder is None:
            continue

        st.markdown(f"---")
        st.markdown(f"##### {tid}. {TOPIC_LABELS[tid]}")

        try:
            with st.spinner(f"Building Topic {tid}…"):
                topic_data = builder(company_df, company_info, peers_df, full_panel, stage_summary)

            preview_topics[tid] = topic_data
            if tid == 1:
                t1_view = st.radio(
                    "Topic 1 Visual Mode",
                    ["📈 5-Yr Trends & Indicators", "🕸️ Peer Benchmark Radar", "📊 Peer Quartile Distribution"],
                    horizontal=True,
                    key="p17_t1_vmode",
                    label_visibility="collapsed",
                )
                if t1_view == "🕸️ Peer Benchmark Radar":
                    # Multi-factor Radar vs 50th percentile peer median
                    categories = ["Leverage", "Profitability", "Tangibility", "Debt Coverage", "Size", "Growth"]
                    size_pct = _calc_pct(peers_df["size"] if peers_df is not None and "size" in peers_df.columns else None, _latest.get("size", 0))
                    growth_pct = _calc_pct(peers_df["growth"] if peers_df is not None and "growth" in peers_df.columns else None, _latest.get("growth", 0))
                    firm_pcts = [lev_pct, prof_pct, tang_pct, min(100, max(0, int(ic_val * 15))) if pd.notna(ic_val) else 50, size_pct, growth_pct]
                    # Close the loop
                    categories_loop = categories + [categories[0]]
                    firm_loop = firm_pcts + [firm_pcts[0]]
                    peer_loop = [50, 50, 50, 50, 50, 50, 50]

                    # Helper to convert hex to valid rgba for Plotly
                    def _hex_to_rgba(hex_code, alpha=0.25):
                        h = str(hex_code).lstrip("#")
                        if len(h) == 6:
                            return f"rgba({int(h[0:2], 16)}, {int(h[2:4], 16)}, {int(h[4:6], 16)}, {alpha})"
                        return f"rgba(13, 148, 136, {alpha})"

                    fig_radar = go.Figure()
                    fig_radar.add_trace(go.Scatterpolar(
                        r=firm_loop,
                        theta=categories_loop,
                        fill='toself',
                        fillcolor=_hex_to_rgba(stage_color, 0.25),
                        line=dict(color=stage_color, width=2.5),
                        name=f"{selected_name} (Percentile)",
                    ))
                    fig_radar.add_trace(go.Scatterpolar(
                        r=peer_loop,
                        theta=categories_loop,
                        line=dict(color="#9CA3AF", width=1.5, dash="dash"),
                        name="Peer Cohort Median (50th Pctile)",
                    ))
                    fig_radar.update_layout(
                        polar=dict(
                            radialaxis=dict(visible=True, range=[0, 100], ticksuffix="%"),
                        ),
                        showlegend=True,
                        **plotly_layout(f"{selected_name} — Comprehensive Factor Radar vs Life-Stage Peers", height=420),
                    )
                    st.plotly_chart(fig_radar, use_container_width=True, config=PLOTLY_CONFIG)
                    chart_download_button(fig_radar, "board_topic1_radar.png")
                    topic_data["figs"] = [fig_radar]

                elif t1_view == "📊 Peer Quartile Distribution":
                    # Peer comparison distribution bars
                    metric_labels = ["Leverage (%)", "ROA (%)", "Tangibility (%)"]
                    fig_dist = go.Figure()
                    for m_idx, (m_col, m_label, m_val) in enumerate([
                        ("leverage", "Leverage", lev_val),
                        ("profitability", "ROA", prof_val),
                        ("tangibility", "Tangibility", tang_val),
                    ]):
                        if peers_df is not None and m_col in peers_df.columns:
                            p_clean = peers_df[m_col].dropna() * 100
                            q25, q50, q75 = p_clean.quantile([0.25, 0.50, 0.75])
                            fig_dist.add_trace(go.Box(
                                x=p_clean,
                                y=[m_label] * len(p_clean),
                                orientation='h',
                                name=f"{m_label} Peers",
                                marker_color=PRIMARY if m_idx == 0 else (SECONDARY if m_idx == 1 else ACCENT),
                                boxpoints=False,
                                showlegend=False,
                            ))
                            fig_dist.add_trace(go.Scatter(
                                x=[m_val * 100],
                                y=[m_label],
                                mode='markers',
                                marker=dict(color='#DC2626', size=14, symbol='diamond', line=dict(color='white', width=1.5)),
                                name=f"{selected_name}",
                                showlegend=(m_idx == 0),
                            ))
                    fig_dist.update_layout(
                        xaxis_title="Ratio Value (%)",
                        **plotly_layout(f"{selected_name} vs Life-Stage Peer Distributions (Interquartile Range)", height=320),
                    )
                    st.plotly_chart(fig_dist, use_container_width=True, config=PLOTLY_CONFIG)
                    chart_download_button(fig_dist, "board_topic1_distribution.png")
                    topic_data["figs"] = [fig_dist]

                else:
                    for _fig_idx, fig in enumerate(topic_data.get("figs", [])):
                        st.plotly_chart(fig, use_container_width=True, config=PLOTLY_CONFIG)
                        chart_download_button(fig, f"board_topic{tid}_chart{_fig_idx + 1}.png")
            else:
                for _fig_idx, fig in enumerate(topic_data.get("figs", [])):
                    st.plotly_chart(fig, use_container_width=True, config=PLOTLY_CONFIG)
                    chart_download_button(fig, f"board_topic{tid}_chart{_fig_idx + 1}.png")

            for _tbl_idx, tbl in enumerate(topic_data.get("tables", [])):
                if tbl is not None and not tbl.empty:
                    st.dataframe(tbl, use_container_width=True, hide_index=True)
                    df_download_button(tbl, f"board_topic{tid}_table{_tbl_idx + 1}.csv")

            insights = topic_data.get("insights", [])
            actions  = topic_data.get("actions", [])
            if insights or actions:
                render_interpretation(insights, actions, title=f"Topic {tid} Interpretation")

            if ai_narratives_on:
                _ai_key = f"p17_ai_t{tid}_{company_code}"
                if _ai_key not in st.session_state:
                    _user_role = (st.session_state.get("user") or {}).get("role", "researcher")
                    _citations = st.session_state.get("p19_citations", False)
                    with st.spinner(f"Generating AI narrative for Topic {tid}…"):
                        st.session_state[_ai_key] = build_topic_ai_narrative(
                            topic_data, company_code,
                            panel_mode=panel_mode, role=_user_role, citations=_citations,
                        )
                if st.session_state.get(_ai_key):
                    with st.expander("🤖 Board AI Narrative", expanded=True):
                        st.markdown(st.session_state[_ai_key])
                    topic_data["insights"] = [*topic_data.get("insights", []), st.session_state[_ai_key]]

        except Exception as exc:
            st.error(f"Topic {tid} could not render: {exc}")

    # ── Scholarly Governance & Literature Benchmark Knowledge Vault ────────────
    st.markdown("---")
    _theme = st.session_state.get("theme", "dark")
    vault_cits = get_relevant_vault_citations("pecking order trade off dynamic speed of adjustment dickinson flannery rangan frank goyal kumar")
    if vault_cits:
        vault_html = render_academic_vault_html(
            vault_cits,
            theme=_theme,
            title="📚 Peer-Reviewed Literature Benchmark Knowledge Vault (Corporate Capital Structure & Board Strategy)"
        )
        st.markdown(vault_html, unsafe_allow_html=True)

    with st.expander("Topic 13: Additional Empirical CFO Recommendations", expanded=False):
        if st.button("Generate additional strategic commentary", key="p17_extra_commentary"):
            from models import board_export as _be
            _t13 = _be.build_topic_13_ai(company_code, panel_mode=panel_mode, backend="deterministic")
            st.session_state["p17_extra_commentary_result"] = (company_code, _t13)
        _extra = st.session_state.get("p17_extra_commentary_result")
        if _extra and _extra[0] == company_code:
            for _label, _bullets in _extra[1].get("insights", []):
                st.markdown(f"##### {_label}")
                for _b in _bullets:
                    st.markdown(f"- {_b}")
            for _a in _extra[1].get("actions", []):
                st.markdown(f"- {_a}")
        st.caption("Additional strategic commentary is separate from the analytical export.")

# ── STEP 7: PPTX generation & download ───────────────────────────────────────
import hashlib
_export_signature = hashlib.sha256((str(company_code) + str(selected_topics) + str(st.session_state.get("p17_t1_vmode"))
    + str(ai_narratives_on) + str(st.session_state.get("theme")) + company_df.to_json()
    + peers_df.to_json() + full_panel.to_json() + stage_summary.to_json()).encode()).hexdigest()
if st.session_state.get("p17_export_signature") != _export_signature:
    st.session_state.pop("p17_export", None)
    st.session_state["p17_export_signature"] = _export_signature
if download_clicked:
    if n_selected == 0:
        st.warning("Select at least one topic before generating the deck.")
    else:
        with st.spinner(f"Building the analytical deck for {selected_name}..."):
            try:
                warnings = []
                pptx_bytes = pptx_generator.build(company_df, company_info, peers_df, full_panel,
                    stage_summary, selected_topics, warnings=warnings, topic_data=preview_topics)
                st.session_state["p17_export"] = dict(data=pptx_bytes, warnings=warnings)
            except Exception as exc:
                st.error(f"PPTX generation failed: {exc}")
_export = st.session_state.get("p17_export")
if _export:
    for warning in _export["warnings"]:
        st.warning(warning)
    st.download_button("Download analytical .pptx", data=_export["data"],
        file_name=f"{company_code}_Analytical_BoardDeck.pptx",
        mime="application/vnd.openxmlformats-officedocument.presentationml.presentation")
