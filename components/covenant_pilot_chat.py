"""Inline scenario confirmation and evidence for the existing assistant page."""
import json
import os
from hashlib import sha256
from pathlib import Path
from uuid import uuid4

import pandas as pd
import streamlit as st

from models.covenant_chat import handle_query, make_draft
from models.covenant_examples import example_catalog
from models.covenant_pilot import CovenantSpec, ScenarioRequest


def enabled() -> bool:
    return os.environ.get("ENABLE_COVENANT_PILOT", "").lower() in ("1", "true", "yes")


def _evidence_frame(evidence):
    frame = pd.DataFrame(evidence)
    if "value" in frame:
        frame["value"] = frame["value"].map(str)
    return frame


def conversation_state(history: list, scope: str) -> dict:
    """Hydrate only the current owner/session/panel scope from persisted turns."""
    for turn in reversed(history):
        envelope = turn.get("result_envelope") or {}
        if envelope.get("capability") == "covenant_pilot" and envelope.get("scope") == scope:
            return envelope.get("state") or {}
    return {}


def route(query: str, history: list, scope: str, selected_company=None) -> dict | None:
    if not enabled():
        return None
    response = handle_query(query, conversation_state(history, scope), selected_company=selected_company)
    if response is None:
        return None
    return {"role": "assistant", "content": response["content"], "model_used": "Deterministic covenant pilot",
            "elapsed_s": 0.0, "result_envelope": {"capability": "covenant_pilot", "scope": scope,
                                                    "state": response["state"], "result": response.get("result")},
            "followups": ["confirm scenario", "cancel scenario"] if response.get("draft") else
                         ["margin -20%", "rates +150 bps", "compare scenarios"] if response.get("result") else []}


def render_turn(turn: dict, key: str):
    """Render stored outputs only. Button clicks queue an explicit new chat turn."""
    envelope = turn.get("result_envelope") or {}
    report = envelope.get("borrower_report")
    if report:
        with st.expander("Borrower evidence validation details", expanded=True):
            if report.get("uploaded_documents"):
                st.dataframe(pd.DataFrame(report["uploaded_documents"]), use_container_width=True)
            if report["issues"]:
                st.dataframe(pd.DataFrame(report["issues"]), use_container_width=True)
            st.caption("File identity and structure checks only. Finance review and contractual definition mapping remain required.")
            st.download_button("Download borrower validation report", json.dumps(report, indent=2, allow_nan=False),
                               file_name="borrower_validation_report.json", mime="application/json", key=f"{key}_borrower_report")
    result = envelope.get("result")
    if not result:
        return
    chart = pd.DataFrame({"Quarter": [q["quarter"] for q in result["stressed"]["quarters"]],
                          "Baseline cash": [q["closing_cash_cr"] for q in result["baseline"]["quarters"]],
                          "Scenario cash": [q["closing_cash_cr"] for q in result["stressed"]["quarters"]]})
    st.line_chart(chart, x="Quarter", y=["Baseline cash", "Scenario cash"], y_label="₹ crore")
    with st.expander("Covenant calculation evidence"):
        st.write("Validation: NOT_VALIDATED. Public anchors and illustrative assumptions are separated below.")
        st.dataframe(_evidence_frame(result["inputs"]["snapshot"]["evidence"]), use_container_width=True)
        st.write("Baseline quarters")
        st.dataframe(pd.DataFrame(result["baseline"]["quarters"]), use_container_width=True)
        st.write("Scenario quarters")
        st.dataframe(pd.DataFrame(result["stressed"]["quarters"]), use_container_width=True)
        for limitation in result["limitations"]:
            st.caption(limitation)
        st.download_button("Download reproducible scenario JSON", json.dumps(result, sort_keys=True, indent=2, allow_nan=False),
                           file_name=f"covenant_{result['simulation_id'][:12]}.json", mime="application/json", key=f"{key}_manifest")


def render_pending(history: list, scope: str):
    if not enabled():
        return
    state = conversation_state(history, scope)
    if state.get("borrower_intake_requested"):
        _render_borrower_intake(state, scope)
    draft = state.get("draft")
    if not draft:
        return
    example = example_catalog()[draft["entity_id"]]
    req, cov = draft["request"], draft["covenants"]
    st.markdown(f"**Pending covenant scenario: {draft['company']}**")
    st.caption("Frozen FY2025 public inputs with illustrative schedules and a 12-quarter forecast. Review assumptions before running.")
    # Keys follow the confirmed draft rather than previous widget state.
    from models.covenant_pilot import fingerprint
    key = f"covenant_{fingerprint(draft)[:12]}"
    with st.expander("Inspect sources and schedules"):
        st.dataframe(_evidence_frame(example["snapshot"].evidence), use_container_width=True)
        st.json({"debts": [vars(d) for d in example["debts"]], "leases": [vars(l) for l in example["leases"]]})
    with st.form(key):
        a, b = st.columns(2)
        with a:
            rate = st.number_input("Rate shock (bps)", value=float(req["rate_shock_bps"]))
            margin = st.number_input("Relative earnings/margin change (%)", min_value=-100.0, max_value=100.0, value=float(req["margin_shock_pct"]))
            debt = st.number_input("New debt spent on capex (₹ crore)", min_value=0.0, value=float(req["incremental_debt_cr"]))
            new_rate = st.number_input("New floating debt annual rate (%)", min_value=0.0, max_value=100.0, value=float(req["incremental_annual_rate"]) * 100)
        with b:
            dscr = st.number_input("Illustrative DSCR floor", min_value=0.01, value=float(cov["dscr_floor"]))
            icr = st.number_input("Illustrative earnings/interest floor", min_value=0.01, value=float(cov["icr_floor"]))
            tol = st.number_input("Illustrative TOL/TNW ceiling", min_value=0.01, value=float(cov["tol_tnw_ceiling"]))
            cash = st.number_input("Minimum cash (₹ crore)", min_value=0.0, value=float(cov["minimum_cash_cr"]))
        leases = st.checkbox("Include leases in coverage ratios", value=req["lease_in_coverage"])
        submitted = st.form_submit_button("Run confirmed scenario")
    if submitted:
        edited = make_draft(draft["entity_id"], ScenarioRequest(rate, margin, debt, new_rate / 100, leases),
                            CovenantSpec(dscr, icr, tol, cash))
        state["draft"] = edited
        response = handle_query("confirm scenario", state)
        import db
        sid = st.session_state["chat_session_id"]
        user_text = f"Confirm scenario for {edited['company']} using the displayed edited assumptions."
        user_turn = {"role": "user", "content": user_text}
        turn = {"role": "assistant", "content": response["content"], "model_used": "Deterministic covenant pilot",
                "result_envelope": {"capability": "covenant_pilot", "scope": scope, "state": response["state"], "result": response.get("result")}}
        db.append_chat_message(sid, "user", user_text)
        db.append_chat_message(sid, "assistant", turn["content"], model_used=turn["model_used"], result_envelope=turn["result_envelope"])
        st.session_state["chat_history"].extend([user_turn, turn])
        st.rerun()


def _render_borrower_intake(state: dict, scope: str):
    """Explicit, local-only uploads; no provider receives borrower documents."""
    st.markdown("**Borrower evidence upload**")
    st.caption("Supporting files stay in this local project. Submit a JSON packet with explicit source references; no automated document extraction is performed yet.")
    template = Path(__file__).resolve().parents[1] / "scratch/covenant_pilot/borrower_validation/borrower_packet_template.json"
    widget_key = sha256(scope.encode()).hexdigest()[:20]
    if template.is_file():
        st.download_button("Download blank borrower packet", template.read_bytes(), file_name="borrower_packet_template.json",
                           mime="application/json", key=f"borrower_template_{widget_key}")
    with st.form(f"borrower_intake_{widget_key}"):
        packet_file = st.file_uploader("Borrower packet (JSON)", type=["json"], key=f"borrower_packet_{widget_key}")
        source_files = st.file_uploader("Supporting borrower documents", type=["pdf", "csv", "xlsx", "docx", "txt"],
                                       accept_multiple_files=True, key=f"borrower_sources_{widget_key}")
        submitted = st.form_submit_button("Check borrower evidence")
    if not submitted:
        return
    if packet_file is None:
        st.error("Select a borrower JSON packet before checking evidence.")
        return
    try:
        packet = json.loads(packet_file.getvalue().decode("utf-8-sig"))
        if not isinstance(packet, dict):
            raise ValueError("The borrower packet must be a JSON object")
        # Each upload run gets its own scoped directory; filenames never select
        # another chat's evidence or arbitrary local paths.
        folder = Path(__file__).resolve().parents[1] / "scratch/covenant_pilot/borrower_uploads" / widget_key / uuid4().hex
        names = [Path(f.name.replace("\\", "/")).name for f in source_files]
        if len(set(names)) != len(names) or any(n in ("", ".", "..") for n in names):
            raise ValueError("Supporting document filenames must be unique and nonempty")
        folder.mkdir(parents=True, exist_ok=False)
        for name, uploaded in zip(names, source_files):
            (folder / name).write_bytes(uploaded.getvalue())
        from models.borrower_evidence import validate_packet
        report = validate_packet(packet, folder)
        report["uploaded_documents"] = [{"file": name, "sha256": sha256(uploaded.getvalue()).hexdigest()}
                                        for name, uploaded in zip(names, source_files)]
    except (ValueError, TypeError, KeyError, AttributeError, OSError) as exc:
        st.error(f"Borrower packet could not be checked: {exc}")
        return
    issues = report["issues"]
    content = (f"**Borrower evidence: {report['status']}**\n\n"
               f"Verified source files: {report['verified_document_count']}. Evidence issues: {len(issues)}.\n\n"
               "Review the issue table below, correct the packet or source files, and resubmit."
               if issues else
               "**Borrower evidence: READY_FOR_PROFESSIONAL_REVIEW**\n\nThe supplied source files, references and schedule controls passed intake checks. This is not financial approval.")
    content += "\n\nContractual calculations remain disabled. Validation status: NOT_VALIDATED."
    turn = {"role": "assistant", "content": content, "model_used": "Deterministic covenant pilot",
            "result_envelope": {"capability": "covenant_pilot", "scope": scope, "state": state,
                                "borrower_report": report}}
    import db
    sid = st.session_state["chat_session_id"]
    user_text = "Check the borrower packet and uploaded supporting evidence."
    db.append_chat_message(sid, "user", user_text)
    db.append_chat_message(sid, "assistant", content, model_used=turn["model_used"], result_envelope=turn["result_envelope"])
    st.session_state["chat_history"].extend([{"role": "user", "content": user_text}, turn])
    st.rerun()
