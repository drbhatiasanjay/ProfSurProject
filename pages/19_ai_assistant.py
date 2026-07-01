"""
Page 19 — AI Financial Assistant.
Full-screen dedicated chat interface grounded in the capital structure panel data.
"""
import time
import uuid as _uuid
import streamlit as st
from helpers import require_role
import db

require_role("admin", "researcher")
db.log_page_visit("ai_assistant_page")

# ── Session persistence lifecycle ─────────────────────────────────────────────
_u = st.session_state.get("user") or {}
_username = _u.get("username", "")

if "chat_session_id" not in st.session_state:
    _sessions = db.list_chat_sessions(_username, limit=1)
    if _sessions:
        _sid = _sessions[0]["chat_session_id"]
        st.session_state["chat_session_id"] = _sid
        st.session_state["chat_history"] = db.load_chat_messages(_sid)
    else:
        _sid = f"cs_{_uuid.uuid4().hex[:12]}"
        st.session_state["chat_session_id"] = _sid
        db.create_chat_session(_sid, _username, _u.get("role", "viewer"),
                               panel_mode=st.session_state.get("panel_mode", "thesis"),
                               mode="Researcher")
        st.session_state["chat_history"] = []

from models.llm_adapters import (
    build_company_context,
    build_panel_context,
    stream_ollama,
    stream_anthropic,
    log_chat_query,
    count_tokens,
    classify_query,
    parse_llm_json,
    generate_followup_suggestions,
)

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
        ["anthropic", "ollama"],
        index=0,
        key="p19_backend",
        help="Anthropic: cloud API (default, requires ANTHROPIC_API_KEY in secrets.toml). Ollama: local, zero data egress.",
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

    if st.button("Clear history", key="p19_clear"):
        db.delete_chat_session(st.session_state.get("chat_session_id", ""))
        st.session_state.pop("chat_session_id", None)
        st.session_state["chat_history"] = []
        st.session_state.pop("_followup_suggestions", None)
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
        st.rerun()

    for _sess in db.list_chat_sessions(_username, limit=15):
        _is_active = _sess["chat_session_id"] == st.session_state.get("chat_session_id")
        _label = f"{'▶ ' if _is_active else ''}{_sess['title'] or 'New chat'}"
        _sc1, _sc2 = st.columns([5, 1])
        with _sc1:
            if st.button(_label, key=f"sess_{_sess['chat_session_id']}", use_container_width=True):
                st.session_state["chat_session_id"] = _sess["chat_session_id"]
                st.session_state["chat_history"] = db.load_chat_messages(_sess["chat_session_id"])
                st.session_state.pop("_followup_suggestions", None)
                st.rerun()
        with _sc2:
            if st.button("🗑", key=f"del_{_sess['chat_session_id']}"):
                db.delete_chat_session(_sess["chat_session_id"])
                if _is_active:
                    st.session_state.pop("chat_session_id", None)
                    st.session_state["chat_history"] = []
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
        if turn["role"] == "assistant" and turn.get("model_used"):
            _model_short = "Haiku" if "haiku" in turn["model_used"] else "Sonnet"
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

# ── Input — always rendered so the chat box never disappears ─────────────────
user_q = st.chat_input("Ask about the panel data...", key="chat_input_p19")
if not user_q and st.session_state.get("_pending_followup"):
    user_q = st.session_state.pop("_pending_followup")
elif st.session_state.get("_pending_followup"):
    st.session_state.pop("_pending_followup")  # typed message wins; discard chip

if user_q:
    st.session_state.pop("_followup_suggestions", None)  # clear old chips on new message
    panel_mode = st.session_state.get("panel_mode", "thesis")
    if mode == "CFO" and company_code:
        ctx = build_company_context(int(company_code), panel_mode=panel_mode)
    else:
        ctx = build_panel_context(panel_mode=panel_mode)

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
    model_to_use = "claude-sonnet-4-6" if q_type in ("analytical", "hybrid") else "claude-haiku-4-5-20251001"
    # FIX-5: factual queries lead with the number, not preamble
    if q_type == "factual":
        ctx = "Answer in 1-2 sentences. State the exact number first, then one sentence of context.\n\n" + ctx

    _user_role = (st.session_state.get("user") or {}).get("role", "viewer")
    _t0 = time.time()
    with st.chat_message("assistant"):
        if backend == "ollama":
            full = st.write_stream(
                stream_ollama([{"role": "system", "content": ctx}] + messages)
            )
        else:
            full = st.write_stream(
                stream_anthropic(
                    messages, system=ctx, model=model_to_use,
                    role=_user_role, citations=citations_on,
                )
            )
        _elapsed = round(time.time() - _t0, 1)
        _model_badge = "Haiku" if "haiku" in model_to_use else "Sonnet"
        st.caption(f"*{_model_badge} · {_elapsed}s*")

    st.session_state["chat_history"].append({
        "role": "assistant",
        "content": full or "",
        "model_used": model_to_use,
        "elapsed_s": _elapsed,
    })
    db.append_chat_message(
        st.session_state.get("chat_session_id", ""), "assistant",
        full or "", model_used=model_to_use, elapsed_s=_elapsed,
    )

    # Generate chips — stored in session_state so they persist after rerender
    with st.spinner("Generating follow-up questions…"):
        _followups = generate_followup_suggestions(
            st.session_state["chat_history"],
            last_query=user_q,
            last_response=full or "",
            query_type=q_type,
            role=_user_role,
        )
    if _followups:
        st.session_state["_followup_suggestions"] = _followups
        st.rerun()

    # CFO mode: offer to add reply to board deck
    if mode == "CFO" and full:
        if "ai_recommendations" not in st.session_state:
            st.session_state["ai_recommendations"] = []
        if st.button("➕ Add to Board Deck", key=f"brd_{len(st.session_state['chat_history'])}"):
            st.session_state["ai_recommendations"].append(
                {"question": user_q, "answer": full}
            )
            st.toast("Added to Board Deck ✓")

    _u = st.session_state.get("user", {}) or {}
    _backend_logged = f"anthropic:{model_to_use}" if backend == "anthropic" else "ollama"
    log_chat_query(
        username=_u.get("username", "anonymous"),
        role=_u.get("role", "viewer"),
        backend=_backend_logged,
        token_count=count_tokens(ctx) + count_tokens(user_q) + count_tokens(full or ""),
        query=user_q,
        session_id=st.session_state.get("chat_session_id", ""),
    )
