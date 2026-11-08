"""Render HTML blocks without Markdown's indented-code interpretation with strict trust boundaries."""
import html
import streamlit as st


def render_html(html_str: str, *, unsafe_allow_html: bool = True):
    """Render raw HTML layout markup after stripping indentation artifacts."""
    clean = "\n".join(line.strip() for line in html_str.splitlines() if line.strip())
    return st.markdown(clean, unsafe_allow_html=unsafe_allow_html)


def render_trusted_template(template: str, **values: object):
    """Render HTML template where all dynamic user/document values are automatically HTML-escaped."""
    escaped = {key: html.escape(str(val) if val is not None else "", quote=True) for key, val in values.items()}
    clean_tmpl = "\n".join(line.strip() for line in template.splitlines() if line.strip())
    rendered = clean_tmpl.format_map(escaped)
    return st.markdown(rendered, unsafe_allow_html=True)


def render_user_text(value: object):
    """Render user text safely via standard Streamlit text components."""
    st.write(value)
