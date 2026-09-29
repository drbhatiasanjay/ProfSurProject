"""Optional cloud configuration shared by the chat UI and provider adapter."""
import os


def get_gemini_api_key():
    key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    if key:
        return key
    import streamlit as st

    key = st.session_state.get("gemini_api_key")
    if key:
        return key
    try:
        return (
            st.secrets.get("GEMINI_API_KEY")
            or st.secrets.get("GOOGLE_API_KEY")
            or st.secrets.get("credentials", {}).get("gemini_api_key")
        )
    except FileNotFoundError:
        return None
