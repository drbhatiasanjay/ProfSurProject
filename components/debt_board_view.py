"""Facts-first debt review with optional, explicitly submitted scenario inputs."""

import hashlib
import json

import streamlit as st

import db
from helpers import PLOTLY_CONFIG, render_interpretation
from models.debt_board import build_debt_board, fmt, number
from models.board_export import TOPIC_BUILDERS, TOPIC_LABELS
from models.pptx_generator import build_sections


def _scenario_form(prefix, draft, borrowings):
    choices = ["Assess a funding proposal", "Stress existing debt only"]
    choice = st.radio("What would you like to assess?", choices,
        index=1 if draft.get("scenario_type") == "stress" else 0, key=f"{prefix}_scenario_type")
    funding = choice == choices[0]
    st.markdown("**How to complete this form**")
    st.markdown("1. Choose a funding proposal or an existing-debt stress test.\n"
        "2. Complete fields marked **\\*** using management plans, lender terms or assumptions you wish to test.\n"
        "3. Select **Apply scenario and calculate**, then review the results in Step 3 before exporting.")
    if funding:
        st.caption(f"Use the same monetary unit and scale as reported borrowings ({fmt(borrowings)} above). Currency and scale are not confirmed by this panel. A deliberate zero is allowed; a blank means not supplied.")
    else:
        st.caption("You only need four stress assumptions. No funding amount or future investment plan is required for this test.")

    def amount(label, field, help_text, maximum=None):
        return st.number_input(label, min_value=0.0, max_value=maximum,
            value=number(draft.get(field)), placeholder="Enter a value", key=f"{prefix}_{field}", help=help_text)

    with st.form(f"{prefix}_form_v2", border=True):
        values = dict(scenario_type="funding" if funding else "stress")
        if funding:
            st.markdown("##### A. Funding plan")
            st.caption("Explain why funding is needed and how much would be met by borrowing.")
            values["purpose"] = st.text_input("Funding purpose *", value=draft.get("purpose", ""),
                placeholder="For example: equipment investment or refinancing a maturing loan", max_chars=300,
                key=f"{prefix}_purpose", help="State the business use of the money so the board can judge the financing choice.")
            left, right = st.columns(2)
            with left:
                values["funding_uses"] = amount("Planned funding uses *", "funding_uses", "Total needed for the plan, from an approved budget or planning estimate.")
                values["internal_funding"] = amount("Internal funding allocated *", "internal_funding", "Funds management can allocate while preserving operating liquidity. The app does not assume all reported cash is available.")
            with right:
                values["new_debt"] = amount("Proposed new borrowing *", "new_debt", "Additional borrowing to assess. The app compares it with the funding gap.")
                values["new_rate"] = amount("Annual rate on new borrowing (%) *", "new_rate", "Use an indicative lender quote or a chosen rate assumption. For 8%, enter 8.", 100.0)
            st.divider()
        st.markdown("##### B. Downside assumptions" if funding else "##### A. Existing-debt stress assumptions")
        st.caption("Choose the conditions to test. These are assumptions, not company facts or forecasts.")
        left, right = st.columns(2)
        with left:
            floating = st.number_input("Existing debt exposed to rate changes (%) *", min_value=0.0, max_value=100.0,
                value=number(draft.get("floating_share")) * 100 if number(draft.get("floating_share")) is not None else None,
                placeholder="For example: 50", key=f"{prefix}_floating_share",
                help="Share of existing debt whose interest cost would change. Use the debt schedule; do not assume 100% is floating-rate.")
            values["rate_shock"] = amount("Interest-rate increase (basis points) *", "rate_shock", "100 basis points = 1 percentage point. Enter 200 to test a 2-point increase on exposed debt.", 10000.0)
        with right:
            earnings = st.number_input("PBIT decline (%) *", min_value=0.0, max_value=100.0,
                value=number(draft.get("earnings_shock")) * 100 if number(draft.get("earnings_shock")) is not None else None,
                placeholder="For example: 20", key=f"{prefix}_earnings_shock",
                help="Decline in profit before interest and tax. Enter 20 for a 20% decline, or an explicit 0 for no decline.")
            values["coverage_floor"] = st.number_input("Coverage floor to test (x) *", min_value=0.1, max_value=100.0,
                value=number(draft.get("coverage_floor")), placeholder="For example: 3", key=f"{prefix}_coverage_floor",
                help="Minimum PBIT / interest multiple to test. Enter 3 for 3x. This is an analytical assumption, not a verified covenant or legal threshold.")
        values["floating_share"] = floating / 100 if floating is not None else None
        values["earnings_shock"] = earnings / 100 if earnings is not None else None
        if not funding:
            values["purpose"] = "Stress existing debt"
        st.divider()
        st.markdown("**What happens after you apply?**")
        if funding:
            st.markdown("The app calculates the external funding gap, proposed annual interest, coverage before and after borrowing, the combined downside, and the earnings decline that reaches your selected coverage floor.")
        else:
            st.markdown("The app compares observed coverage with coverage after your rate increase and PBIT decline, then calculates the earnings decline that reaches your coverage floor. No new borrowing is assumed.")
        st.caption("Step 3 will show the applied assumptions, calculations and interpretation. They will also appear in the PowerPoint. Select Apply after editing; draft changes do not update the results.")
        submitted = st.form_submit_button("Apply scenario and calculate", type="primary", use_container_width=True)
    required = dict(floating_share="existing debt exposed to rate changes", rate_shock="interest-rate increase",
                    earnings_shock="PBIT decline", coverage_floor="coverage floor")
    if funding:
        required.update(funding_uses="planned funding uses", internal_funding="internal funding allocated",
                        new_debt="proposed new borrowing", new_rate="annual borrowing rate", purpose="funding purpose")
    missing = [label for field, label in required.items() if values.get(field) is None or (field == "purpose" and not values[field].strip())]
    return submitted, values, missing


def _render_sections(sections, prefix):
    for index, section in enumerate(sections):
        label = section["title"].split(". ", 1)[-1]
        with st.expander(label, expanded=section["title"].startswith("1. ")):
            for table in section["tables"]:
                if not table.empty:
                    st.dataframe(table, use_container_width=True, hide_index=True)
            for chart_index, fig in enumerate(section["figs"]):
                st.plotly_chart(fig, use_container_width=True, config=PLOTLY_CONFIG, key=f"{prefix}_{index}_{chart_index}")
            render_interpretation(section["insights"], section["actions"], title="Evidence and next step")


def _render_debt_board(company_df, company_info, peers_df, full_panel, stage_summary, prefs):
    username = st.session_state.get("user", {}).get("username", "")
    code = company_info["code"]
    prefix = f"debt_board_{username}_{code}"
    saved = prefs.get("companies", {}).get(str(code), {})
    current_version = saved.get("scenario_version") == 2
    applied_key = f"{prefix}_applied"
    if applied_key not in st.session_state:
        st.session_state[applied_key] = saved.get("assumptions") if current_version and saved.get("enabled") else None
    applied = st.session_state[applied_key]
    draft = applied or saved.get("assumptions") or saved.get("draft") or saved
    st.markdown("#### Debt strategy: facts to board decision")
    st.caption("Review the company's reported position first. Add a funding proposal or stress test only if you need one. You can export a historical review without completing a form.")

    light = st.session_state.get("theme") == "light"
    background, foreground, border = ("#F1F5F9", "#0F172A", "#CBD5E1") if light else ("#161F30", "#F1F5F9", "#475569")
    field_background = "#FFFFFF" if light else "#0B0E14"
    st.markdown(f"""<style>
    .st-key-debt_board_sections [data-testid="stExpander"] summary,
    .st-key-debt_board_results [data-testid="stExpander"] summary {{background-color: {background} !important; color: {foreground} !important;}}
    .st-key-debt_board_sections [data-testid="stExpander"] summary *,
    .st-key-debt_board_results [data-testid="stExpander"] summary * {{color: {foreground} !important;}}
    .st-key-debt_board_input_card {{border: 1px solid {border}; border-radius: 12px; padding: 20px; background: {background};}}
    .st-key-debt_board_input_card [data-testid="stForm"] {{border: 1px solid {border} !important; border-radius: 10px; padding: 20px !important;}}
    .st-key-debt_board_input_card input,
    .st-key-debt_board_input_card [data-baseweb="input"],
    .st-key-debt_board_input_card [data-baseweb="base-input"] {{background-color: {field_background} !important; color: {foreground} !important;}}
    .st-key-debt_board_input_card [data-testid="stNumberInputStepUp"],
    .st-key-debt_board_input_card [data-testid="stNumberInputStepDown"] {{background-color: {field_background} !important; color: {foreground} !important;}}
    .st-key-debt_board_input_card label,
    .st-key-debt_board_input_card label *,
    .st-key-debt_board_input_card [data-testid="stWidgetLabel"],
    .st-key-debt_board_input_card [data-testid="stWidgetLabel"] *,
    .st-key-debt_board_input_card [data-testid="stTooltipIcon"],
    .st-key-debt_board_input_card [data-testid="stTooltipIcon"] * {{color: {foreground} !important; opacity: 1 !important;}}
    .st-key-debt_board_workflow [data-testid="stAlert"],
    .st-key-debt_board_workflow [data-testid="stAlert"] * {{color: {foreground} !important;}}
    .st-key-debt_board_input_card [data-testid="stFormSubmitButton"] button {{background: #4338CA !important; border-color: #4338CA !important; color: #FFFFFF !important;}}
    .st-key-debt_board_input_card [data-testid="stFormSubmitButton"] button * {{color: #FFFFFF !important;}}
    </style>""", unsafe_allow_html=True)

    st.markdown("### Step 1 · Review company facts and analysis")
    analysis_slot = st.container(key="debt_board_sections")
    st.markdown("### Step 2 · Add an optional scenario")
    persist = False
    with st.container(key="debt_board_input_card"):
        st.markdown("#### Optional scenario form")
        st.write("The company facts above are loaded automatically. Use this form only to assess a future funding plan or test how existing debt responds to adverse conditions.")
        enabled = st.checkbox("Add a funding proposal or stress test to this deck", value=bool(current_version and saved.get("enabled")), key=f"{prefix}_enabled")
        if enabled:
            if applied is None and any(number(draft.get(field)) is not None for field in ("new_debt", "floating_share", "rate_shock")):
                st.caption("Previously saved inputs are shown as a draft. Review them and select Apply to use them in the results.")
            submitted, candidate, missing = _scenario_form(prefix, draft, company_df.sort_values("year").iloc[-1].get("borrowings"))
            if submitted:
                if missing:
                    st.error("Complete the following fields to calculate this scenario: " + ", ".join(missing) + ". Blank fields are not treated as zero.")
                else:
                    try:
                        build_debt_board(company_df, company_info, peers_df, candidate)
                    except ValueError as exc:
                        st.error(str(exc))
                    else:
                        applied = candidate
                        st.session_state[applied_key] = applied
                        persist = True
                        st.success("Scenario applied. Review the calculated results in Step 3.")
        else:
            st.caption("No scenario is required. Continue to Step 3 to export the historical review. Future funding plans will be marked Not supplied.")
            if applied is not None:
                draft = applied
                applied = None
                st.session_state[applied_key] = None
                persist = True

    st.markdown("### Step 3 · Review results and export")
    if applied is None:
        st.info("Historical review ready. No funding proposal or stress assumptions have been applied.")
    else:
        st.info("Applied scenario: " + applied.get("purpose", "Debt review") + ". Review the assumptions and results below before exporting.")
    results_slot = st.container(key="debt_board_results")
    appendix = st.multiselect("Optional analytical appendix topics", options=list(TOPIC_LABELS),
        default=saved.get("appendix", []), format_func=lambda tid: f"{tid}. {TOPIC_LABELS[tid]}", key=f"{prefix}_appendix")
    if username and (persist or appendix != saved.get("appendix", [])):
        prefs = dict(prefs, companies=dict(prefs.get("companies", {})))
        prefs["companies"][str(code)] = dict(scenario_version=2, enabled=applied is not None,
            assumptions=applied, draft=applied or draft, appendix=appendix)
        db.save_user_pref(username, "board_deck", prefs)

    digest = hashlib.sha256(json.dumps([code, applied, appendix, st.session_state.get("theme")], sort_keys=True).encode())
    for frame in (company_df, peers_df, full_panel, stage_summary):
        if frame is not None:
            digest.update(frame.to_json(date_format="iso").encode())
    signature = digest.hexdigest()
    pack_key = f"{prefix}_pack"
    if st.session_state.get(f"{prefix}_signature") != signature:
        pack = build_debt_board(company_df, company_info, peers_df, applied)
        if applied and applied.get("scenario_type", "funding") == "funding":
            pack["sections"][1]["insights"].insert(0, f"Funding purpose: {applied['purpose']}")
        for tid in appendix:
            try:
                section = TOPIC_BUILDERS[tid](company_df, company_info, peers_df, full_panel, stage_summary)
                section = dict(section, title=f"Appendix | {TOPIC_LABELS[tid]}", provenance=pack["provenance"])
            except Exception as exc:
                section = dict(title=f"Appendix | {TOPIC_LABELS[tid]}", figs=[], tables=[],
                    insights=[f"Analysis unavailable ({type(exc).__name__})."], actions=["Resolve before using this appendix."])
            pack["sections"].append(section)
        st.session_state[pack_key] = pack
        st.session_state[f"{prefix}_signature"] = signature
        st.session_state.pop(f"{prefix}_export", None)
    pack = st.session_state[pack_key]
    with analysis_slot:
        st.caption(pack["provenance"])
        _render_sections([pack["sections"][i] for i in (0, 2, 3, 4, 5, 6)], f"{prefix}_facts")
    with results_slot:
        _render_sections([pack["sections"][i] for i in (1, 7, 8, 9)] + pack["sections"][10:], f"{prefix}_results")

    st.caption(f"Prepared {pack['generated_at']} | {len(pack['sections'])} sections. The PowerPoint contains the same company facts and applied assumptions shown here.")
    if st.button("Generate debt strategy PowerPoint", type="primary", key=f"{prefix}_generate"):
        warnings = []
        with st.spinner("Building the PowerPoint from the displayed sections..."):
            try:
                data = build_sections(company_info, pack["sections"], warnings=warnings)
                st.session_state[f"{prefix}_export"] = dict(data=data, warnings=warnings)
            except Exception as exc:
                st.error(f"PowerPoint generation failed ({type(exc).__name__}).")
    export = st.session_state.get(f"{prefix}_export")
    if export:
        for warning in export["warnings"]:
            st.warning(warning)
        if export["warnings"]:
            st.warning("Export contains incomplete content. Review the warnings before sharing.")
        else:
            st.success("PowerPoint ready.")
        st.download_button("Download debt strategy .pptx", data=export["data"],
            file_name=f"{code}_Debt_Strategy.pptx", mime="application/vnd.openxmlformats-officedocument.presentationml.presentation",
            key=f"{prefix}_download")


def render_debt_board(company_df, company_info, peers_df, full_panel, stage_summary, prefs):
    with st.container(key="debt_board_workflow"):
        _render_debt_board(company_df, company_info, peers_df, full_panel, stage_summary, prefs)
