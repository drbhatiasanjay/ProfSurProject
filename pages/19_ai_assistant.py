"""
Page 19 — AI Financial Assistant.
Full-screen dedicated chat interface grounded in the capital structure panel data.
"""
import streamlit as st
from helpers import require_role
import db

require_role("admin", "researcher")
db.log_page_visit("ai_assistant_page")

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
        st.session_state["chat_history"] = []
        st.rerun()

# ── Shared history (same key as the global bubble — seamless handoff) ────────
if "chat_history" not in st.session_state:
    st.session_state["chat_history"] = []

# ── Display history ───────────────────────────────────────────────────────────
if not st.session_state["chat_history"]:
    st.info(
        "Ask a question to get started. Examples:\n"
        "- What is the mean leverage for Maturity stage firms?\n"
        "- Which industries have the highest tangibility?\n"
        "- Explain the role of profitability in leverage decisions."
    )

for turn in st.session_state["chat_history"]:
    with st.chat_message(turn["role"]):
        st.markdown(turn["content"])

# ── Input (natural bottom-of-page position — guaranteed to work) ─────────────
# Handle pending follow-up questions from suggested chips
if st.session_state.get("_pending_followup"):
    user_q = st.session_state.pop("_pending_followup")
else:
    user_q = st.chat_input("Ask about the panel data...", key="chat_input_p19")

if user_q:
    panel_mode = st.session_state.get("panel_mode", "thesis")
    if mode == "CFO" and company_code:
        ctx = build_company_context(int(company_code), panel_mode=panel_mode)
    else:
        ctx = build_panel_context(panel_mode=panel_mode)

    st.session_state["chat_history"].append({"role": "user", "content": user_q})
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

    st.session_state["chat_history"].append(
        {"role": "assistant", "content": full or ""}
    )

    # Generate and render context-aware follow-up chips (FIX-6 + FIX-7)
    _followups = generate_followup_suggestions(
        st.session_state["chat_history"],
        last_query=user_q,
        last_response=full or "",
        query_type=q_type,
        role=_user_role,
    )
    if _followups:
        st.caption("💡 Continue exploring:")
        _cols = st.columns(3)
        for _idx, _fq in enumerate(_followups[:3]):
            with _cols[_idx]:
                if st.button(_fq, key=f"fq_{hash(_fq)}_{len(st.session_state['chat_history'])}", use_container_width=True):
                    st.session_state["_pending_followup"] = _fq
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
        session_id=st.session_state.get("session_id", ""),
    )
