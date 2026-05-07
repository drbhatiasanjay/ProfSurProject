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
        ["ollama", "anthropic"],
        index=0,
        key="p19_backend",
        help="Ollama: local, zero data egress. Anthropic: cloud API (requires key in secrets.toml).",
    )
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

    with st.chat_message("assistant"):
        if backend == "ollama":
            full = st.write_stream(
                stream_ollama([{"role": "system", "content": ctx}] + messages)
            )
        else:
            full = st.write_stream(stream_anthropic(messages, system=ctx))

    st.session_state["chat_history"].append(
        {"role": "assistant", "content": full or ""}
    )

    _u = st.session_state.get("user", {}) or {}
    log_chat_query(
        username=_u.get("username", "anonymous"),
        role=_u.get("role", "viewer"),
        backend=backend,
        token_count=count_tokens(ctx) + count_tokens(user_q) + count_tokens(full or ""),
        query=user_q,
        session_id=st.session_state.get("session_id", ""),
    )
