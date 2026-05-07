"""
Page 17 — Company Board Deck Generator

Individual-company analysis: select one firm, choose analytical topics,
preview interactive charts, download a branded .pptx board deck.

Distinct from all other pages (1–16) which are panel-wide thesis analyses.
Here the company is the SUBJECT; the 401-firm panel is the PEER CONTEXT.
"""

import streamlit as st
import pandas as pd

import db
from helpers import (
    ensure_session_state, require_role, plotly_layout,
    PLOTLY_CONFIG, STAGE_COLORS, render_interpretation, new_badge,
)
from models.board_export import TOPIC_BUILDERS, TOPIC_LABELS
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
        companies_df = db.get_companies("thesis")
except Exception as _e:
    st.error(f"Failed to load company list. Please refresh. ({_e})")
    st.stop()
# Put Indian firms first (they have thesis data), US firms at the end
india_df = companies_df[~companies_df["company_name"].str.contains("Inc\.|Corp\.|Co\.", regex=True, na=False)]
us_df    = companies_df[companies_df["company_name"].str.contains("Inc\.|Corp\.|Co\.", regex=True, na=False)]
ordered_names = india_df["company_name"].tolist() + us_df["company_name"].tolist()

_saved_company = _bd_prefs.get("selected_company", ordered_names[0] if ordered_names else "")
_default_idx   = ordered_names.index(_saved_company) if _saved_company in ordered_names else 0

col_co, col_info = st.columns([2, 1])
with col_co:
    selected_name = st.selectbox(
        "Select company",
        options=ordered_names,
        index=_default_idx,
        help="401 Indian firms + 25 US firms. Analysis is always against Thesis panel (2001–2024).",
    )

# Persist company selection
if _username:
    db.save_user_pref(_username, "board_deck", {"selected_company": selected_name})
company_row = companies_df[companies_df["company_name"] == selected_name].iloc[0]
company_code = int(company_row["company_code"])


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
    company_df    = db.get_company_detail(company_code)
    full_panel    = db.get_active_financials(thesis_ft)
    stage_summary = db.get_life_stage_summary(thesis_ft)
    peers_df      = db.get_company_peers(company_code, full_panel)
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

# ── STEP 3: Snapshot header ───────────────────────────────────────────────────
with col_info:
    stage = company_info["current_stage"]
    stage_color = STAGE_COLORS.get(stage, "#0D9488")
    lev_val = _latest.get("leverage", 0)
    prof_val = _latest.get("profitability", 0)
    n_peers = len(peers_df) if peers_df is not None else 0
    st.markdown(
        f"""<div style="background:#F0FDFA;border-left:4px solid {stage_color};padding:10px 14px;border-radius:4px;font-size:13px;">
        <b>{selected_name}</b><br>
        Stage: <b style="color:{stage_color}">{stage}</b> &nbsp;·&nbsp; {company_info['last_year']}<br>
        Leverage: <b>{lev_val*100:.1f}%</b> &nbsp;·&nbsp; Profitability: <b>{prof_val*100:.1f}%</b><br>
        Peer group: <b>{n_peers} firms</b>
        </div>""",
        unsafe_allow_html=True,
    )

st.divider()

# ── STEP 4: Topic checklist ───────────────────────────────────────────────────
st.markdown("#### Select slides for your deck")
st.caption("All topics pre-selected — uncheck any you want to exclude.")

col_selall, col_deselall, _ = st.columns([1, 1, 4])
select_all   = col_selall.button("Select All",   key="sel_all")
deselect_all = col_deselall.button("Unselect All", key="desel_all")

# Initialise selection state
if "deck_selection" not in st.session_state or select_all or deselect_all:
    st.session_state["deck_selection"] = {
        tid: (False if deselect_all else True)
        for tid in TOPIC_LABELS
    }

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

# ── STEP 5: Action buttons ────────────────────────────────────────────────────
col_prev, col_dl, col_clear = st.columns([1.2, 1.2, 1])
preview_clicked  = col_prev.button("Preview Deck",         type="primary",   key="preview_btn")
download_clicked = col_dl.button("Generate & Download .pptx", type="secondary", key="dl_btn")
if col_clear.button("Clear Preview", key="clear_btn"):
    st.session_state.pop("deck_previewed", None)
    st.rerun()

if preview_clicked:
    st.session_state["deck_previewed"] = True

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

            for fig in topic_data.get("figs", []):
                st.plotly_chart(fig, use_container_width=True, config=PLOTLY_CONFIG)

            for tbl in topic_data.get("tables", []):
                if tbl is not None and not tbl.empty:
                    st.dataframe(tbl, use_container_width=True, hide_index=True)

            insights = topic_data.get("insights", [])
            actions  = topic_data.get("actions", [])
            if insights or actions:
                render_interpretation(insights, actions, title=f"Topic {tid} Interpretation")

        except Exception as exc:
            st.error(f"Topic {tid} could not render: {exc}")

# ── STEP 7: PPTX generation & download ───────────────────────────────────────
if download_clicked:
    if n_selected == 0:
        st.warning("Select at least one topic before generating the deck.")
    else:
        with st.spinner(f"Building {n_selected}-topic board deck for {selected_name}…"):
            try:
                pptx_bytes = pptx_generator.build(
                    company_df, company_info, peers_df,
                    full_panel, stage_summary, selected_topics,
                )
                fname = f"{selected_name.replace(' ', '_').replace('.', '')}_BoardDeck.pptx"
                st.download_button(
                    label=f"⬇ Download {fname}",
                    data=pptx_bytes,
                    file_name=fname,
                    mime="application/vnd.openxmlformats-officedocument.presentationml.presentation",
                    type="primary",
                )
                st.success(
                    f"Board deck ready — {n_selected} topics, {selected_name}. "
                    "Click the download button above."
                )
            except Exception as exc:
                st.error(f"PPTX generation failed: {exc}")
