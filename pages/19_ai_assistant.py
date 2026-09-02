"""
Page 19 — AI Financial Assistant.
Full-screen dedicated chat interface grounded in the capital structure panel data.
"""
import time
import uuid as _uuid
import copy
import csv
import io
import json
import re
import base64
import streamlit as st
import streamlit.components.v1 as components
import plotly.graph_objects as go
from helpers import require_role, plotly_layout
import db

require_role("admin", "researcher")
db.log_page_visit("ai_assistant_page")

# ── Session persistence lifecycle ─────────────────────────────────────────────
_u = st.session_state.get("user") or {}
_username = _u.get("username", "")

if "chat_session_id" not in st.session_state:
    _sessions = db.list_chat_sessions(_username, limit=1)
    if _sessions:
        _active_session = _sessions[0]
        _sid = _active_session["chat_session_id"]
        st.session_state["chat_session_id"] = _sid
        st.session_state["chat_history"] = db.load_chat_messages(_sid)
        st.session_state["p19_mode"] = _active_session.get("mode", "Researcher")
        if _active_session.get("company_code"):
            st.session_state["p19_company_code"] = int(_active_session["company_code"])
    else:
        _sid = f"cs_{_uuid.uuid4().hex[:12]}"
        st.session_state["chat_session_id"] = _sid
        db.create_chat_session(_sid, _username, _u.get("role", "viewer"),
                               panel_mode=st.session_state.get("panel_mode", "thesis"),
                               mode="Researcher")
        st.session_state["chat_history"] = []
    # Hydrate persisted follow-up chips from the last assistant turn, if any,
    # so "Continue exploring" survives a page reload instead of vanishing.
    if st.session_state["chat_history"]:
        _last_turn = st.session_state["chat_history"][-1]
        if _last_turn.get("role") == "assistant" and _last_turn.get("followups"):
            st.session_state["_followup_suggestions"] = _last_turn["followups"]

from models.llm_adapters import (
    build_company_context,
    build_panel_context,
    stream_ollama,
    stream_anthropic,
    stream_gemini_agent,
    log_chat_query,
    count_tokens,
    classify_query,
    parse_llm_json,
    parse_followup_chips,
    normalize_assistant_chunk,
    normalize_assistant_response,
    should_generate_chart,
    stream_with_fallback,
)
from models.agent_tools import render_chat_chart_figure, extract_chat_chart_spec, extract_table_chart_spec

_CHART_INSTRUCTION = (
    "\n\nVISUALIZATION INSTRUCTIONS:\n"
    "When the user requests a chart, plot, graph, or visual representation, provide your table and analytical explanation in markdown, and ALWAYS include an embedded JSON chart specification in this exact format:\n"
    "```json\n"
    "{\n"
    '  "chart_type": "line",\n'
    '  "title": "<Chart Title>",\n'
    '  "x_axis_label": "<X Axis Label>",\n'
    '  "y_axis_label": "<Y Axis Label>",\n'
    '  "categories": ["2001", "2002", "2003", ...],\n'
    '  "series": [\n'
    '    {"name": "<Series Name>", "values": [<val1>, <val2>, ...]}\n'
    '  ]\n'
    "}\n"
    "```\n"
    "Allowed chart_types: 'line', 'bar', 'scatter', 'box', 'histogram'. Never state that you are unable to generate a chart — output this JSON block and the platform will automatically render it as an interactive Plotly visualization.\n"
)

_FOLLOWUP_INSTRUCTION = (
    "\n\n---\nAfter your answer, on a new line output exactly:\n"
    'FOLLOWUPS_JSON: {"followups":["<specific stat or number question>?","<theory or mechanism question>?","<one focused industry, time-period, or peer comparison question>?"]}\n'
    "Replace each placeholder with one real follow-up question. Output ONLY that line after your answer — no markdown, no other text."
)

# Fallback chips shown when the model's FOLLOWUPS_JSON footer is missing or
# unparsable (e.g. truncated by max_tokens) — "Continue exploring" should
# never dead-end. Keyed by mode, same shape as _STARTER_QUESTIONS below.
_FALLBACK_CHIPS = {
    "Researcher": [
        "What is the mean leverage across all life stages?",
        "Explain the theoretical mechanism behind this result — pecking order vs trade-off.",
        "How does leverage differ across industries?",
    ],
    "CFO": [
        "How does my company's leverage compare to industry peers?",
        "What is the practical implication of this for capital structure decisions?",
            "How does leverage differ across industry peers?",
    ],
}

st.title("AI Financial Assistant")
st.caption("Ask questions grounded in the capital structure panel data.")
st.markdown(
    """
<style>
/* Chat prose wraps; only inherently wide content scrolls horizontally. */
[data-testid="stChatMessage"] {
    min-width: 0 !important;
    max-width: 100% !important;
    overflow: hidden !important;
}
[data-testid="stChatMessage"] [data-testid="stMarkdownContainer"] {
    min-width: 0 !important;
    max-width: 100% !important;
    overflow-wrap: anywhere !important;
    word-break: normal !important;
    white-space: normal !important;
}
[data-testid="stChatMessage"] p,
[data-testid="stChatMessage"] li,
[data-testid="stChatMessage"] h1,
[data-testid="stChatMessage"] h2,
[data-testid="stChatMessage"] h3 {
    overflow-wrap: anywhere !important;
    white-space: normal !important;
}
[data-testid="stChatMessage"] pre,
[data-testid="stChatMessage"] table {
    display: block;
    max-width: 100%;
    overflow-x: auto;
}
[data-testid="stChatMessage"] [data-testid="stCodeBlock"],
[data-testid="stChatMessage"] pre { max-width: 100%; overflow-x: auto; }
[data-testid="stChatMessage"] pre { white-space: pre; }
@media (max-width: 768px) {
    [data-testid="stChatMessage"] { padding-left: 0.5rem; padding-right: 0.5rem; }
}
</style>
    """,
    unsafe_allow_html=True,
)


def _render_chart_card(spec: dict, key_prefix: str) -> None:
    """Render a consistent, inspectable chart surface for history and live replies."""
    if not isinstance(spec, dict):
        return
    categories = list(spec.get("categories") or [])
    series = list(spec.get("series") or [])
    if not categories or not series:
        return

    with st.container(border=True):
        st.markdown("**Interactive visualization**")
        c1, c2, c3, c4 = st.columns([1, 1.2, 1.2, 1])
        with c1:
            limits = [10, 25, 50, len(categories)]
            limits = list(dict.fromkeys(n for n in limits if n <= len(categories)))
            top_n = st.selectbox("Categories", limits, index=len(limits) - 1,
                                 key=f"{key_prefix}_top_n")
        with c2:
            as_percent = st.checkbox("Display as %", value=False, key=f"{key_prefix}_percent")
        with c3:
            sort_order = st.selectbox(
                "Sort",
                ["Original order", "Highest first", "Lowest first"],
                key=f"{key_prefix}_sort",
            )
        with c4:
            orientation_label = st.selectbox(
                "Orientation",
                ["Vertical", "Horizontal"],
                key=f"{key_prefix}_orientation",
            )
        with c1:
            st.caption(f"{len(categories)} categories · {len(series)} series")

        display_spec = copy.deepcopy(spec)
        indexed_categories = list(enumerate(categories))
        if sort_order != "Original order" and series:
            sort_values = list(series[0].get("values") or [])
            indexed_categories.sort(
                key=lambda pair: float(sort_values[pair[0]])
                if pair[0] < len(sort_values) else 0.0,
                reverse=sort_order == "Highest first",
            )
        selected_indexes = [index for index, _ in indexed_categories[:top_n]]
        display_spec["categories"] = [categories[index] for index in selected_indexes]
        display_series = []
        for item in series:
            source_values = list(item.get("values") or [])
            values = [source_values[index] for index in selected_indexes if index < len(source_values)]
            if as_percent:
                values = [round(float(value) * 100, 4) for value in values]
            display_series.append({**item, "values": values})
        display_spec["series"] = display_series
        display_spec["orientation"] = "h" if orientation_label == "Horizontal" else "v"
        if as_percent and display_spec.get("y_axis_label"):
            label = str(display_spec["y_axis_label"])
            if "%" not in label:
                display_spec["y_axis_label"] = f"{label} (%)"

        fig = render_chat_chart_figure(display_spec, theme=st.session_state.get("theme", "light"))
        st.plotly_chart(fig, use_container_width=True, key=f"{key_prefix}_figure")
        with st.expander("Chart data", expanded=False):
            st.download_button(
                "Download JSON",
                data=json.dumps(display_spec, indent=2, default=str),
                file_name="ai_chart.json",
                mime="application/json",
                key=f"{key_prefix}_json",
            )
            output = io.StringIO()
            writer = csv.writer(output)
            writer.writerow(["category"] + [str(item.get("name", "Series")) for item in display_series])
            for index, category in enumerate(display_spec["categories"]):
                writer.writerow([category] + [item["values"][index] if index < len(item["values"]) else ""
                                              for item in display_series])
            st.download_button(
                "Download CSV",
                data=output.getvalue(),
                file_name="ai_chart.csv",
                mime="text/csv",
                key=f"{key_prefix}_csv",
            )
            st.download_button(
                "Download interactive HTML",
                data=fig.to_html(include_plotlyjs="cdn", full_html=True),
                file_name="ai_chart.html",
                mime="text/html",
                key=f"{key_prefix}_html",
            )
            # PNG conversion is intentionally omitted from the render path;
            # Kaleido can block the whole Streamlit script on large charts.
            st.caption("Use the chart toolbar camera icon to save a PNG.")


def _split_supporting_tables(text: str) -> tuple[str, list[str]]:
    """Keep markdown tables out of the prose column and render them on demand."""
    lines = str(text or "").splitlines()
    prose: list[str] = []
    tables: list[str] = []
    index = 0
    while index < len(lines):
        line = lines[index].strip()
        if line.startswith("|") and line.endswith("|"):
            block: list[str] = []
            while index < len(lines):
                candidate = lines[index].strip()
                if not (candidate.startswith("|") and candidate.endswith("|")):
                    break
                block.append(lines[index])
                index += 1
            if len(block) >= 3 and re.match(r"^[\s|:\-]+$", block[1]):
                tables.append("\n".join(block))
                if prose and prose[-1].strip():
                    prose.append("")
                continue
            prose.extend(block)
            continue
        prose.append(lines[index])
        index += 1
    return "\n".join(prose).strip(), tables


def _normalized_turn_content(turn: dict) -> tuple[str, list[str], dict | None]:
    """Return display prose, supporting tables, and chart for any provider turn."""
    normalized = normalize_assistant_response(
        turn.get("content", ""),
        chart_spec=turn.get("chart_spec"),
    )
    prose, tables = _split_supporting_tables(normalized["answer"])
    return prose, tables, normalized.get("chart_spec")


def _render_assistant_content(turn: dict, key_prefix: str, *, placeholder=None) -> None:
    """Render the common answer hierarchy: prose, chart, observations, data."""
    prose, tables, chart = _normalized_turn_content(turn)
    if placeholder is not None:
        placeholder.markdown(prose or "Preparing the answer...")
        return
    st.markdown(prose)
    if chart:
        _render_chart_card(chart, f"{key_prefix}_chart")
    if tables:
        with st.expander("Supporting data", expanded=False):
            for table in tables:
                st.markdown(table)
    _render_answer_context(key_prefix)


def _render_response_actions(content: str, key_prefix: str, regenerate_question: str = "", message_id=None, feedback=None) -> None:
    """Expose lightweight answer actions without coupling them to an LLM."""
    action_cols = st.columns([1.15, 1.15, 1.15, 1.25, 3.5])
    with action_cols[0]:
        st.download_button(
            "Save",
            data=str(content or ""),
            file_name="ai_answer.md",
            mime="text/markdown",
            key=f"{key_prefix}_download",
            help="Save this answer as Markdown",
        )
    with action_cols[1]:
        _copy_payload = base64.b64encode(str(content or "").encode("utf-8")).decode("ascii")
        components.html(
            f"""<button style='font:inherit;padding:0.4rem 0.7rem;border:1px solid #d1d5db;border-radius:0.4rem;background:white;cursor:pointer;white-space:nowrap' onclick=\"navigator.clipboard.writeText(atob('{_copy_payload}')).then(() => this.innerText='Copied')\">Copy</button>""",
            height=38,
        )
    with action_cols[2]:
        if regenerate_question and st.button("Retry", key=f"{key_prefix}_regenerate", help="Run the same question again"):
            st.session_state["_pending_followup"] = regenerate_question
            st.rerun()
    with action_cols[3]:
        feedback_key = f"{key_prefix}_feedback"
        if st.button("Helpful", key=feedback_key, help="Mark this answer as helpful"):
            st.session_state[feedback_key] = "submitted"
            if message_id:
                db.set_chat_message_feedback(message_id, "useful")
            st.toast("Thanks for the feedback")
    with action_cols[4]:
        if st.session_state.get(feedback_key) == "submitted":
            st.caption("Feedback recorded")


def _render_answer_context(key_prefix: str) -> None:
    """Show the active data scope without adding noise to the main answer."""
    filters = st.session_state.get("filters", {}) or {}
    panel_mode = st.session_state.get("panel_mode", "thesis")
    years = filters.get("year_range", ("All", "All"))
    industries = ", ".join(filters.get("industry_groups", [])) or "All industries"
    stages = ", ".join(filters.get("life_stages", [])) or "All life stages"
    backend = str(st.session_state.get("p19_backend", "gemini")).title()
    with st.expander("Answer context", expanded=False):
        st.caption(
            f"Panel: {panel_mode}  |  Years: {years[0]}-{years[1]}  |  "
            f"Industries: {industries}  |  Life stages: {stages}  |  Backend: {backend}"
        )


_panel_label = {
    "run3": "April 2026 panel",
    "thesis": "Thesis panel",
    "latest": "Latest panel",
    "us_av_2024": "US S&P panel",
}.get(st.session_state.get("panel_mode", "thesis"), st.session_state.get("panel_mode", "thesis"))
_header_cols = st.columns([2.4, 1.2, 1.2, 1.2])
with _header_cols[0]:
    st.markdown("**Current research workspace**")
    st.caption(_panel_label)
with _header_cols[1]:
    st.caption("Mode")
    st.markdown(f"**{st.session_state.get('p19_mode', 'Researcher')}**")
with _header_cols[2]:
    st.caption("Backend")
    st.markdown(f"**{st.session_state.get('p19_backend', 'gemini').title()}**")
with _header_cols[3]:
    st.caption("Context")
    st.markdown(f"**{min(len(st.session_state.get('chat_history', [])), 6)} recent turns**")

# ── Sidebar controls ─────────────────────────────────────────────────────────
with st.sidebar:
    mode = st.radio(
        "Mode",
        ["Researcher", "CFO"],
        index=0,
        key="p19_mode",
        help="Researcher: panel-wide context. CFO: single-company context.",
    )
    backend = st.radio(
        "Backend",
        ["gemini", "anthropic", "ollama"],
        index=0,
        key="p19_backend",
        help="Gemini: Google ADK multi-tool agent (NL-to-SQL + Charting + KG2). Anthropic: Claude Haiku/Sonnet. Ollama: local, zero data egress.",
    )
    citations_on = st.session_state.get("p19_citations", False)
    st.caption(f"Academic citations: **{'on' if citations_on else 'off'}** — toggle in sidebar under AI Settings.")
    if mode == "CFO":
        company_code = st.number_input(
            "Company code (int)",
            value=int(st.session_state.get("active_company_cin") or 22859),
            step=1,
            key="p19_company_code",
            help="Enter the numeric company_code from the panel (e.g. 22859 = Asian Paints).",
        )
    else:
        company_code = None

    # Sync mode & company to DB session
    if st.session_state.get("chat_session_id"):
        db.update_chat_session_mode(st.session_state["chat_session_id"], mode)
        if mode == "CFO" and company_code:
            db.update_chat_session_company(st.session_state["chat_session_id"], int(company_code))

    if st.button("Clear history", key="p19_clear"):
        db.delete_chat_session(st.session_state.get("chat_session_id", ""))
        st.session_state.pop("chat_session_id", None)
        st.session_state["chat_history"] = []
        st.session_state.pop("_followup_suggestions", None)
        st.session_state.pop("_last_qa", None)
        st.rerun()

    # FIX-10: export chat as markdown
    if st.session_state.get("chat_history"):
        from datetime import datetime as _dt
        _export_lines = ["# AI Chat Export", f"*{_dt.now().strftime('%Y-%m-%d %H:%M')}*", ""]
        for _t in st.session_state["chat_history"]:
            _export_lines.append(f"**{'You' if _t['role'] == 'user' else 'AI'}:** {_t['content']}\n")
        st.download_button(
            "⬇ Export Chat",
            data="\n".join(_export_lines),
            file_name=f"ai_chat_{_dt.now().strftime('%Y%m%d')}.md",
            mime="text/markdown",
            key="p19_export",
        )

    # FIX-11: context progress bar
    _n_msgs = len(st.session_state.get("chat_history", []))
    st.progress(min(_n_msgs / 20, 1.0))
    st.caption(f"Stored turns: {_n_msgs} · model context: up to 6 recent turns")

    # ── Chat History panel ────────────────────────────────────────────────────
    st.markdown("---")
    st.subheader("💬 Chat History")
    if st.button("➕ New Chat", use_container_width=True, key="p19_new_chat"):
        _new_sid = f"cs_{_uuid.uuid4().hex[:12]}"
        db.create_chat_session(_new_sid, _username, _u.get("role", "viewer"),
                               panel_mode=st.session_state.get("panel_mode", "thesis"),
                               mode=mode)
        st.session_state["chat_session_id"] = _new_sid
        st.session_state["chat_history"] = []
        st.session_state.pop("_followup_suggestions", None)
        st.session_state.pop("_last_qa", None)
        st.rerun()

    _chat_sessions = db.list_chat_sessions(_username, limit=50)
    _active_session_record = next(
        (s for s in _chat_sessions if s["chat_session_id"] == st.session_state.get("chat_session_id")),
        None,
    )
    with st.expander("Session settings", expanded=False):
        _current_title = (_active_session_record or {}).get("title") or "New chat"
        _edited_title = st.text_input(
            "Chat title",
            value=_current_title,
            max_chars=80,
            key="p19_chat_title",
        )
        if st.button("Save title", key="p19_save_title") and _active_session_record:
            db.update_chat_session_title(
                _active_session_record["chat_session_id"], _edited_title
            )
            st.rerun()

    _chat_search = st.text_input(
        "Search conversations",
        placeholder="Search titles...",
        key="p19_chat_search",
    ).strip().lower()
    _show_archived = st.checkbox("Show archived", value=False, key="p19_show_archived")
    _visible_sessions = [
        s for s in _chat_sessions
        if (_show_archived or not s.get("archived"))
        and (not _chat_search or _chat_search in (s["title"] or "New chat").lower())
    ]
    for _sess in _visible_sessions[:15]:
        _is_active = _sess["chat_session_id"] == st.session_state.get("chat_session_id")
        _archive_marker = " (archived)" if _sess.get("archived") else ""
        _label = f"{'▶ ' if _is_active else ''}{_sess['title'] or 'New chat'}{_archive_marker}"
        _sc1, _sc2, _sc3 = st.columns([4, 1, 1])
        with _sc1:
            if st.button(_label, key=f"sess_{_sess['chat_session_id']}", use_container_width=True):
                st.session_state["chat_session_id"] = _sess["chat_session_id"]
                _loaded = db.load_chat_messages(_sess["chat_session_id"])
                st.session_state["chat_history"] = _loaded
                st.session_state.pop("_followup_suggestions", None)
                st.session_state.pop("_last_qa", None)
                # Chips follow the session — restore them from its last turn.
                if _loaded and _loaded[-1].get("role") == "assistant" and _loaded[-1].get("followups"):
                    st.session_state["_followup_suggestions"] = _loaded[-1]["followups"]
                st.rerun()
        with _sc2:
            if st.button(
                "Restore" if _sess.get("archived") else "Archive",
                key=f"archive_{_sess['chat_session_id']}",
            ):
                db.set_chat_session_archived(
                    _sess["chat_session_id"], not bool(_sess.get("archived"))
                )
                st.rerun()
        with _sc3:
            if st.button("🗑", key=f"del_{_sess['chat_session_id']}"):
                db.delete_chat_session(_sess["chat_session_id"])
                if _is_active:
                    st.session_state.pop("chat_session_id", None)
                    st.session_state["chat_history"] = []
                    st.session_state.pop("_followup_suggestions", None)
                    st.session_state.pop("_last_qa", None)
                st.rerun()

# ── Shared history (same key as the global bubble — seamless handoff) ────────
if "chat_history" not in st.session_state:
    st.session_state["chat_history"] = []

_STARTER_QUESTIONS = {
    "researcher": [
        "What is the mean leverage for Maturity stage firms?",
        "Explain the role of profitability in leverage decisions — pecking order vs trade-off.",
        "Compare leverage trends during GFC 2008 and COVID 2020.",
    ],
    "admin": [
        "Which life stage carries the highest default risk in this panel?",
        "How does leverage differ across industries?",
        "What would happen to leverage if profitability increased by 10%?",
    ],
    "cfo": [
        "How does my company's leverage compare to industry peers?",
        "What is the optimal leverage for a Maturity stage firm?",
        "Which capital structure levers should a CFO adjust first?",
    ],
}

# ── Display history ───────────────────────────────────────────────────────────
if not st.session_state["chat_history"]:
    _role_key = (st.session_state.get("user") or {}).get("role", "researcher")
    _starters = _STARTER_QUESTIONS.get(_role_key, _STARTER_QUESTIONS["researcher"])
    st.caption("💡 **Try asking:**")
    for _sq in _starters:
        if st.button(_sq, use_container_width=True, key=f"starter_{hash(_sq)}"):
            st.session_state["_pending_followup"] = _sq
            st.rerun()

_previous_user_question = ""
for _turn_idx, turn in enumerate(st.session_state["chat_history"]):
    with st.chat_message(turn["role"]):
        if turn["role"] == "assistant":
            _render_assistant_content(turn, f"history_{_turn_idx}")
            _render_response_actions(
                turn.get("content", ""),
                f"history_{_turn_idx}",
                regenerate_question=_previous_user_question,
                message_id=turn.get("id"),
                feedback=turn.get("feedback"),
            )
        else:
            st.markdown(turn["content"])
            _previous_user_question = turn.get("content", "")
        if turn["role"] == "assistant" and turn.get("model_used"):
            _mu = str(turn["model_used"]).lower()
            if "gemini" in _mu:
                _model_short = "Gemini"
            elif "haiku" in _mu:
                _model_short = "Haiku"
            else:
                _model_short = "Sonnet"
            st.caption(f"*{_model_short} · {turn.get('elapsed_s', '?')}s*")

# ── Persistent followup chips (survive rerenders via session_state) ──────────
_stored_fups = st.session_state.get("_followup_suggestions", [])
if _stored_fups:
    st.caption("💡 Continue exploring:")
    _fup_cols = st.columns(3)
    for _idx, _fq in enumerate(_stored_fups[:3]):
        with _fup_cols[_idx]:
            if st.button(_fq, key=f"fq_{hash(_fq)}_{len(st.session_state['chat_history'])}", use_container_width=True):
                st.session_state["_pending_followup"] = _fq
                st.session_state.pop("_followup_suggestions", None)
                st.rerun()

# CFO mode: offer to add the last AI reply to the board deck. Rendered from
# session_state — not inline right after the stream — because the chip
# persistence rerun (below, after every answer) would otherwise skip a
# button only defined in the run that already ended.
_last_qa = st.session_state.get("_last_qa")
if mode == "CFO" and _last_qa:
    if st.button("➕ Add to Board Deck", key=f"brd_{len(st.session_state['chat_history'])}"):
        if "ai_recommendations" not in st.session_state:
            st.session_state["ai_recommendations"] = []
        st.session_state["ai_recommendations"].append(_last_qa)
        st.session_state.pop("_last_qa", None)
        st.toast("Added to Board Deck ✓")

# ── Input — always rendered so the chat box never disappears ─────────────────
user_q = st.chat_input("Ask about the panel data...", key="chat_input_p19")
if not user_q and st.session_state.get("_pending_followup"):
    user_q = st.session_state.pop("_pending_followup")
elif st.session_state.get("_pending_followup"):
    st.session_state.pop("_pending_followup")  # typed message wins; discard chip

if user_q:
    st.session_state.pop("_followup_suggestions", None)  # clear old chips on new message
    st.session_state.pop("_last_qa", None)
    panel_mode = st.session_state.get("panel_mode", "thesis")
    if mode == "CFO" and company_code:
        ctx = build_company_context(int(company_code), panel_mode=panel_mode)
    else:
        ctx = build_panel_context(panel_mode=panel_mode)

    # Feature E: Ingest active UI telemetry
    _filters = st.session_state.get("filters", {})
    _telemetry_ctx = (
        f"## [SOURCE: Active UI Telemetry]\n"
        f"- Active Panel: {panel_mode}\n"
        f"- Filtered Year Range: {_filters.get('year_range', ('All', 'All'))}\n"
        f"- Filtered Industries: {', '.join(_filters.get('industry_groups', [])) or 'All'}\n"
        f"- Filtered Life Stages: {', '.join(_filters.get('life_stages', [])) or 'All'}\n\n"
    )
    ctx = _telemetry_ctx + ctx

    st.session_state["chat_history"].append({"role": "user", "content": user_q})
    db.append_chat_message(st.session_state.get("chat_session_id", ""), "user", user_q)
    with st.chat_message("user"):
        st.markdown(user_q)

    # Keep provider context compact. Long prior chart answers cause models to
    # echo old headings/tables and materially increase first-token latency.
    messages = []
    for _context_turn in st.session_state["chat_history"][:-1][-6:]:
        _context_content = str(_context_turn.get("content", ""))
        if _context_turn.get("role") == "assistant" and len(_context_content) > 1800:
            _context_content = _context_content[:1800].rstrip() + "..."
        messages.append({"role": _context_turn["role"], "content": _context_content})
    messages.append({"role": "user", "content": user_q})

    # Model routing based on query classification
    q_type = classify_query(user_q)
    if backend == "gemini":
        model_to_use = "gemini-2.5-flash"
    elif q_type in ("analytical", "hybrid"):
        model_to_use = "claude-sonnet-4-6"
    else:
        model_to_use = "claude-haiku-4-5-20251001"

    max_tokens = 2048 if ("sonnet" in model_to_use or "gemini" in model_to_use) else 1024
    if q_type == "factual":
        ctx = "Answer in 1-2 sentences. State the exact number first, then one sentence of context.\n\n" + ctx
    ctx += (
        "\n\nAnswer only the current user question. Do not repeat headings, tables, charts, or analysis "
        "from earlier conversation turns unless the user explicitly asks for a recap."
        + _CHART_INSTRUCTION + _FOLLOWUP_INSTRUCTION
    )

    _user_role = (st.session_state.get("user") or {}).get("role", "viewer")
    _t0 = time.time()
    with st.chat_message("assistant"):
        _placeholder = st.empty()
        _buf = []
        _chart_found = None
        _chart_requested = should_generate_chart(user_q)
        if backend == "gemini":
            _stream = stream_gemini_agent(
                messages,
                system=ctx,
                model=model_to_use,
                max_tokens=max_tokens,
                role=_user_role,
                citations=citations_on,
                panel_mode=panel_mode,
                filters=_filters,
                chart_requested=_chart_requested,
            )
        elif backend == "ollama":
            _stream = stream_ollama(
                [{"role": "system", "content": ctx}] + messages,
                panel_mode=panel_mode,
                filters=_filters,
                chart_requested=_chart_requested,
            )
        else:
            _stream = stream_anthropic(
                messages,
                system=ctx,
                model=model_to_use,
                max_tokens=max_tokens,
                role=_user_role,
                citations=citations_on,
                panel_mode=panel_mode,
                filters=_filters,
                chart_requested=_chart_requested,
            )

        if backend == "gemini":
            _fallback_stream = lambda: stream_anthropic(
                messages, system=ctx, model="claude-sonnet-4-6", max_tokens=max_tokens,
                role=_user_role, citations=citations_on, panel_mode=panel_mode,
                filters=_filters, chart_requested=_chart_requested,
            )
        elif backend == "ollama":
            _fallback_stream = lambda: stream_anthropic(
                messages, system=ctx, model=model_to_use, max_tokens=max_tokens,
                role=_user_role, citations=citations_on, panel_mode=panel_mode,
                filters=_filters, chart_requested=_chart_requested,
            )
        else:
            _fallback_stream = lambda: stream_ollama(
                [{"role": "system", "content": ctx}] + messages,
                panel_mode=panel_mode, filters=_filters, chart_requested=_chart_requested,
            )
        _stream = stream_with_fallback(_stream, _fallback_stream)

        for _chunk in _stream:
            _chunk_text, _chunk_chart = normalize_assistant_chunk(_chunk)
            if _chunk_chart and _chart_found is None:
                _chart_found = _chunk_chart
            if _chunk_text:
                _buf.append(_chunk_text)
                _render_assistant_content(
                    {"content": "".join(_buf)},
                    f"stream_{len(st.session_state['chat_history'])}",
                    placeholder=_placeholder,
                )
        full = "".join(_buf)
        _elapsed = round(time.time() - _t0, 1)

        # If chart was not received as a tool event, check if model embedded a JSON chart spec in text or if table can be parsed
        normalized = normalize_assistant_response(
            full,
            chart_spec=_chart_found,
            user_query=user_q,
            chart_requested=_chart_requested,
        )
        full = normalized["answer"]
        if normalized["chart_spec"]:
            # Apply the same query-aware series filtering to tool-generated
            # charts and embedded/fallback charts before the final render.
            _chart_found = normalized["chart_spec"]

        full_display, _chips_found = parse_followup_chips(full)
        if not _chips_found:
            _fallback_pool = _FALLBACK_CHIPS.get(mode, _FALLBACK_CHIPS["Researcher"])
            _chips_found = [
                q for q in _fallback_pool if q.strip().lower() != user_q.strip().lower()
            ][:3]
        _placeholder.empty()
        _render_assistant_content(
            {"content": full_display, "chart_spec": _chart_found},
            f"live_{len(st.session_state['chat_history'])}",
        )

        if "gemini" in model_to_use.lower():
            _model_badge = "Gemini"
        elif "haiku" in model_to_use.lower():
            _model_badge = "Haiku"
        else:
            _model_badge = "Sonnet"
        st.caption(f"*{_model_badge} · {_elapsed}s*")
        _render_response_actions(full_display, f"live_{len(st.session_state['chat_history'])}", user_q)

    turn_data = {
        "role": "assistant",
        "content": full_display or "",
        "model_used": model_to_use,
        "elapsed_s": _elapsed,
        "followups": _chips_found,
    }
    if _chart_found:
        turn_data["chart_spec"] = _chart_found

    st.session_state["chat_history"].append(turn_data)
    db.append_chat_message(
        st.session_state.get("chat_session_id", ""), "assistant",
        full_display or "", model_used=model_to_use, elapsed_s=_elapsed,
        followups=_chips_found, chart_spec=_chart_found,
    )
    st.session_state["_followup_suggestions"] = _chips_found

    if mode == "CFO" and full_display:
        st.session_state["_last_qa"] = {"question": user_q, "answer": full_display}

    _u = st.session_state.get("user", {}) or {}
    _backend_logged = f"{backend}:{model_to_use}"
    log_chat_query(
        username=_u.get("username", "anonymous"),
        role=_u.get("role", "viewer"),
        backend=_backend_logged,
        token_count=count_tokens(ctx) + count_tokens(user_q) + count_tokens(full_display or ""),
        query=user_q,
        session_id=st.session_state.get("chat_session_id", ""),
    )

    st.rerun()
