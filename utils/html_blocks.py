"""Render HTML blocks without Markdown's indented-code interpretation."""
import streamlit as st


def render_html(html: str, *, unsafe_allow_html: bool = True):
    # Match the terminal fix: dedent alone leaves nested lines after blank lines.
    clean = "\n".join(line.strip() for line in html.splitlines() if line.strip())
    return st.markdown(clean, unsafe_allow_html=unsafe_allow_html)
