"""Stata Interactive Syntax-Highlighted Editor & Variable Autocomplete Component.

Provides:
1. Real-time Stata syntax highlighting matching Stata 18 Dark/Light aesthetics.
2. Active panel variable autocompletion & variable quick-insert pills.
3. Bidirectional Natural Language ↔ Stata command translation trigger.
4. Seamless integration with Streamlit session state and forms.
"""

import re
import html
import streamlit as st
import pandas as pd
from typing import List, Dict, Any, Optional

from models.stata_nl_translator import translate_nl_to_stata


STATA_COMMAND_VERBS = {
    "xtreg", "regress", "reg", "ivregress", "test", "predict", "winsor2", "winsor",
    "summarize", "sum", "tabstat", "pwcorr", "correlate", "corr", "hausman",
    "estat", "estimates", "estimate", "esttab", "coefplot", "scatter",
    "histogram", "hist", "export", "twoway", "thesis", "tabulate", "tab",
    "box", "hbox", "xttest0", "xtserial", "margins", "marginsplot",
}

STATA_OPTIONS = {
    "fe", "re", "be", "robust", "detail", "sig", "nocons", "noconstant",
    "cluster", "vce", "by", "over", "star", "level", "cuts", "replace",
    "trim", "suffix", "xb", "residuals", "r", "2sls", "liml", "gmm",
}


def highlight_stata_syntax(cmd_str: str, theme: str = "dark") -> str:
    """Tokenize and generate colored HTML syntax highlighting for a Stata command."""
    if not cmd_str:
        return ""

    escaped = html.escape(cmd_str)
    tokens = escaped.split()
    styled_tokens = []

    # Palette
    is_dark = (theme == "dark")
    c_verb = "#58a6ff" if is_dark else "#0969da"
    c_opt = "#7ee787" if is_dark else "#1a7f37"
    c_num = "#ffa657" if is_dark else "#9a6700"
    c_op = "#d2a8ff" if is_dark else "#8250df"
    c_var = "#79c0ff" if is_dark else "#0550ae"

    for i, tok in enumerate(tokens):
        low_tok = re.sub(r"[^\w.]", "", tok).lower()
        if i == 0 and low_tok in STATA_COMMAND_VERBS:
            styled_tokens.append(f"<span style='color:{c_verb}; font-weight:700;'>{tok}</span>")
        elif low_tok in STATA_OPTIONS or any(tok.startswith(opt + "(") for opt in STATA_OPTIONS):
            styled_tokens.append(f"<span style='color:{c_opt}; font-weight:600;'>{tok}</span>")
        elif re.match(r"^-?\d+(?:\.\d+)?$", low_tok):
            styled_tokens.append(f"<span style='color:{c_num};'>{tok}</span>")
        elif tok in ("=", "==", ">", "<", ">=", "<=", "+", "-", "*", "/", ","):
            styled_tokens.append(f"<span style='color:{c_op}; font-weight:700;'>{tok}</span>")
        elif tok.startswith("(") or tok.endswith(")"):
            inner = tok.strip("()")
            styled_tokens.append(f"<span style='color:{c_op};'>(</span><span style='color:{c_var};'>{inner}</span><span style='color:{c_op};'>)</span>")
        elif tok.startswith("L.") or tok.startswith("L1.") or tok.startswith("L2."):
            styled_tokens.append(f"<span style='color:{c_op}; font-weight:600;'>L.</span><span style='color:{c_var}; font-weight:500;'>{tok[2:]}</span>")
        else:
            styled_tokens.append(f"<span style='color:{c_var}; font-weight:500;'>{tok}</span>")

    bg = "#0d1117" if is_dark else "#f6f8fa"
    border = "#30363d" if is_dark else "#d0d7de"
    color = "#c9d1d9" if is_dark else "#24292f"

    return f"""
    <div style="
        font-family: 'Consolas', 'Courier New', monospace;
        font-size: 13px;
        background: {bg};
        border: 1px solid {border};
        border-radius: 6px;
        padding: 8px 12px;
        color: {color};
        margin-top: 4px;
        margin-bottom: 8px;
        overflow-x: auto;
    ">
        <span style="color: {c_verb}; font-weight: bold; margin-right: 6px;">.</span>{' '.join(styled_tokens)}
    </div>
    """


def render_variable_autocomplete_chips(df: Optional[pd.DataFrame] = None, max_vars: int = 12):
    """Render clickable variable suggestion chips from the active panel dataset."""
    if df is None or df.empty:
        return

    cols = [c for c in df.columns if not c.startswith("_") and c not in ("index", "const")]
    selected_cols = cols[:max_vars]

    st.markdown(
        """<div style="font-size: 11.5px; font-weight: 600; color: var(--text-muted, #64748B); margin-bottom: 4px;">
        💡 Active Panel Variable Quick-Insert:
        </div>""",
        unsafe_allow_html=True,
    )

    chip_cols = st.columns(len(selected_cols))
    for idx, col_name in enumerate(selected_cols):
        with chip_cols[idx]:
            if st.button(f"+ {col_name}", key=f"chip_var_{col_name}_{idx}", help=f"Append '{col_name}' to prompt"):
                cur_cmd = st.session_state.get("stata_cmd_input", "")
                if col_name not in cur_cmd.split():
                    st.session_state["stata_cmd_input"] = f"{cur_cmd} {col_name}".strip()
                    st.rerun()


def render_stata_dual_input(df: Optional[pd.DataFrame] = None, theme: str = "light") -> str:
    """Render Dual-Mode (Stata CLI vs Natural Language) editor with real-time preview."""
    mode = st.radio(
        "Input Mode:",
        options=["⚡ Stata 18 CLI", "💬 Natural Language Economist"],
        horizontal=True,
        label_visibility="collapsed",
        key="stata_editor_mode_toggle",
    )

    is_nl = ("Natural Language" in mode)

    if is_nl:
        nl_input = st.text_input(
            "Natural Language Query:",
            value=st.session_state.get("stata_nl_query", ""),
            placeholder="e.g. Show me how debt responds to profitability with firm clustering, or instrument tangibility with lag using 2sls",
            key="stata_nl_input_field",
        )
        if nl_input:
            trans_res = translate_nl_to_stata(nl_input)
            if trans_res["status"] == "success":
                translated_stata = trans_res["stata_command"]
                st.session_state["stata_cmd_input"] = translated_stata
                st.markdown(
                    f"<div style='font-size: 11px; color: #10B981; margin-bottom: 2px;'><b>✨ Translated Stata 18 Syntax:</b></div>",
                    unsafe_allow_html=True,
                )
                st.markdown(highlight_stata_syntax(translated_stata, theme=theme), unsafe_allow_html=True)
            else:
                st.error(trans_res.get("message", "Syntax error"))

    # Variable autocomplete helper
    render_variable_autocomplete_chips(df)

    # Active Stata syntax input
    active_val = st.session_state.get("stata_cmd_input", "xtreg leverage profitability tangibility log_size, fe cluster(company_code)")
    with st.form("stata_command_form", clear_on_submit=False):
        c_in1, c_in2 = st.columns([5, 1])
        with c_in1:
            typed_cmd = st.text_input(
                "Stata Command Prompt:",
                value=active_val,
                placeholder=". xtreg leverage profitability tangibility log_size, fe cluster(company_code)",
                label_visibility="collapsed",
            )
        with c_in2:
            run_clicked = st.form_submit_button("▶ Run Command", use_container_width=True, type="primary")

    if not is_nl and typed_cmd:
        st.markdown(highlight_stata_syntax(typed_cmd, theme=theme), unsafe_allow_html=True)

    if run_clicked:
        st.session_state["_trigger_stata_run"] = True
        st.session_state["stata_cmd_input"] = typed_cmd

    return typed_cmd
