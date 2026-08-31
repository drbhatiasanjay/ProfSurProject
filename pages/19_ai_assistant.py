"""
Page 19 — AI Financial Assistant.
Full-screen dedicated chat interface grounded in the capital structure panel data.
"""
import time
import uuid as _uuid
import streamlit as st
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
    'FOLLOWUPS_JSON: {"followups":["<specific stat or number question>?","<theory or mechanism question>?","<industry, time period, or peer comparison question>?"]}\n'
    "Replace each placeholder with one real follow-up question. Output ONLY that line after your answer — no markdown, no other text."
)

# Fallback chips shown when the model's FOLLOWUPS_JSON footer is missing or
# unparsable (e.g. truncated by max_tokens) — "Continue exploring" should
# never dead-end. Keyed by mode, same shape as _STARTER_QUESTIONS below.
_FALLBACK_CHIPS = {
    "Researcher": [
        "What is the mean leverage across all life stages?",
        "Explain the theoretical mechanism behind this result — pecking order vs trade-off.",
        "How does this compare across industries or time periods?",
    ],
    "CFO": [
        "How does my company's leverage compare to industry peers?",
        "What is the practical implication of this for capital structure decisions?",
        "Which industry or time period comparison is most relevant here?",
    ],
}

st.title("AI Financial Assistant")
st.caption("Ask questions grounded in the capital structure panel data.")

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
    st.caption(f"Context: {_n_msgs}/20 messages")

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

    for _sess in db.list_chat_sessions(_username, limit=15):
        _is_active = _sess["chat_session_id"] == st.session_state.get("chat_session_id")
        _label = f"{'▶ ' if _is_active else ''}{_sess['title'] or 'New chat'}"
        _sc1, _sc2 = st.columns([5, 1])
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

for turn in st.session_state["chat_history"]:
    with st.chat_message(turn["role"]):
        st.markdown(turn["content"])
        if turn.get("chart_spec"):
            fig = render_chat_chart_figure(turn["chart_spec"], theme=st.session_state.get("theme", "light"))
            st.plotly_chart(fig, use_container_width=True)
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

    # Last 10 turns as context window (exclude the turn we just appended)
    messages = [
        {"role": t["role"], "content": t["content"]}
        for t in st.session_state["chat_history"][-11:-1]
    ]
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
    ctx += _CHART_INSTRUCTION + _FOLLOWUP_INSTRUCTION

    _user_role = (st.session_state.get("user") or {}).get("role", "viewer")
    _t0 = time.time()
    with st.chat_message("assistant"):
        _placeholder = st.empty()
        _buf = []
        _chart_found = None
        _chart_requested = any(
            w in user_q.lower()
            for w in ("chart", "graph", "plot", "visual", "bar", "trend")
        )
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

        for _chunk in _stream:
            if isinstance(_chunk, dict) and _chunk.get("type") == "chart":
                _chart_found = _chunk.get("spec")
                fig = render_chat_chart_figure(_chart_found, theme=st.session_state.get("theme", "light"))
                st.plotly_chart(fig, use_container_width=True)
            elif isinstance(_chunk, str):
                _buf.append(_chunk)
                _placeholder.markdown("".join(_buf))
        full = "".join(_buf)
        _elapsed = round(time.time() - _t0, 1)

        # If chart was not received as a tool event, check if model embedded a JSON chart spec in text or if table can be parsed
        if not _chart_found:
            _extracted_chart, _cleaned_full = extract_chat_chart_spec(full)
            if _extracted_chart:
                _chart_found = _extracted_chart
                full = _cleaned_full
            elif any(w in user_q.lower() for w in ("chart", "graph", "plot", "visual", "bar", "trend")):
                _chart_found = extract_table_chart_spec(full, user_q=user_q)
            if _chart_found:
                fig = render_chat_chart_figure(_chart_found, theme=st.session_state.get("theme", "light"))
                st.plotly_chart(fig, use_container_width=True)

        full_display, _chips_found = parse_followup_chips(full)
        if not _chips_found:
            _fallback_pool = _FALLBACK_CHIPS.get(mode, _FALLBACK_CHIPS["Researcher"])
            _chips_found = [
                q for q in _fallback_pool if q.strip().lower() != user_q.strip().lower()
            ][:3]
        _placeholder.markdown(full_display)

        if "gemini" in model_to_use.lower():
            _model_badge = "Gemini"
        elif "haiku" in model_to_use.lower():
            _model_badge = "Haiku"
        else:
            _model_badge = "Sonnet"
        st.caption(f"*{_model_badge} · {_elapsed}s*")

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
