"""Independent Pre-IPO workbench; legacy terminal remains available."""
import inspect
import json
import streamlit as st
from models.pre_ipo_decision.service import METHODS, template, parse_bundle, run_case
from models.pre_ipo_decision.contracts import canonical_json, context_hash
from models.pre_ipo_decision import store

PERSONAS = {
    "Individual investor": "Focus on permanent loss, valuation assumptions, liquidity and unresolved diligence.",
    "HNI / family office": "Review position concentration, security rights, exit cash flows and downside scenarios.",
    "Institutional / equity fund": "Review underwriting assumptions, paired opportunities, covenants and evidence lineage.",
    "Issuer / adviser": "Review funding timing, dilution, commitment delivery and disclosure gaps.",
}
def _clear_model_fields():
    for key in list(st.session_state):
        if key.startswith("ipo_arg_"):
            del st.session_state[key]

def _render_content():
    user = st.session_state.get("user", {})
    owner, role = user.get("username", ""), user.get("role", "")
    if not owner:
        owner = st.session_state.get("username") or (st.session_state.get("auth_user") or {}).get("username", "")
        role = (st.session_state.get("auth_user") or {}).get("role", "viewer")
        if owner and not st.session_state.get("user"):
            st.session_state["user"] = {"username": owner, "role": role, "name": owner}
    st.title("Pre-IPO decision workbench")
    st.caption("Company facts → evidence → conditional models → diligence → recorded decision")
    st.info("Start with company facts or import an existing case. Optional models run only when you supply their inputs. Review source support and limitations, then save a dated case and record your next action.")
    if not owner:
        st.warning("Sign in to use a private workbench.")
        return
    if st.session_state.get("ipo_depth_owner") != owner:
        for key in list(st.session_state):
            if key.startswith("ipo_depth_") or key.startswith("ipo_arg_"):
                del st.session_state[key]
        st.session_state.ipo_depth_owner = owner
    if "ipo_depth_bundle" not in st.session_state:
        st.session_state.ipo_depth_bundle = template()
    bundle = st.session_state.ipo_depth_bundle
    persona = st.selectbox("Your decision perspective", list(PERSONAS))
    st.write(PERSONAS[persona])
    editable = role in {"admin", "researcher"}
    handoff=st.session_state.get("ipo_evidence_handoff")
    if handoff and handoff.get("owner")==owner:
        st.info("A source-review snapshot is ready. Applying it starts a new unsaved case; existing saved cases remain available.")
        if st.button("Apply prepared evidence case",disabled=not editable):
            _clear_model_fields()
            st.session_state.ipo_depth_bundle=handoff["context"]
            st.session_state.pop("ipo_depth_report",None)
            st.session_state.pop("ipo_depth_saved",None)
            st.session_state.pop("ipo_evidence_handoff",None)
            st.rerun()
    if st.button("New private case", disabled=not editable):
        _clear_model_fields()
        st.session_state.ipo_depth_bundle = template()
        st.session_state.pop("ipo_depth_report", None)
        st.session_state.pop("ipo_depth_saved", None)
        st.rerun()
    if not editable:
        st.warning("Your profile has read-only access. Case editing and saving require a researcher or admin role.")
    with st.expander("Import or restore a private case"):
        from models.pre_ipo_data import PRE_IPO_REGISTRY
        legacy_id = st.selectbox("Existing dossier to inspect", [""] + list(PRE_IPO_REGISTRY))
        if legacy_id:
            from models.pre_ipo_decision.data_quality import dossier_attributes
            dossier = PRE_IPO_REGISTRY[legacy_id]
            attributes = dossier_attributes(dossier)
            st.warning("Registry dossier values are unverified inputs in this workbench. Original filing availability, source locators and CMIE mappings still need review.")
            st.dataframe([{"Attribute": row["attribute_id"], "Value": json.dumps(row["value"], ensure_ascii=False), "Status": row["status"]} for row in attributes], use_container_width=True)
            if st.button("Start private case from this dossier", disabled=not editable):
                candidate = template()
                candidate.update(company=dossier.company_name, currency="INR", unit="crore", background=dossier.sector,
                                 extracted_attributes=attributes, imported_dossier_id=legacy_id)
                _clear_model_fields()
                st.session_state.ipo_depth_bundle = candidate
                st.session_state.pop("ipo_depth_report", None)
                st.session_state.pop("ipo_depth_saved", None)
                st.rerun()
        uploaded = st.file_uploader("Case JSON (maximum 1 MB)", type=["json"], disabled=not editable)
        if uploaded is not None and st.button("Apply imported case", disabled=not editable):
            try:
                imported = parse_bundle(uploaded.getvalue().decode("utf-8"))
                run_case(imported)
                _clear_model_fields()
                st.session_state.ipo_depth_bundle = imported
                st.session_state.pop("ipo_depth_report", None)
                st.session_state.pop("ipo_depth_saved", None)
                st.rerun()
            except (ValueError, UnicodeError, KeyError, TypeError) as exc:
                st.error(str(exc))
        cases = store.list_cases(owner)
        selected = st.selectbox("Saved case", [""] + [r["case_id"] for r in cases])
        revision = None
        if selected:
            timeline = store.history(owner, selected)
            revision = st.selectbox("Revision to inspect", [r["revision"] for r in timeline["versions"]])
            st.dataframe(timeline["actions"], use_container_width=True)
        if selected and st.button("Restore selected revision"):
            report = store.load_case(owner, selected, revision)
            _clear_model_fields()
            st.session_state.ipo_depth_bundle = report["context"]
            st.session_state.ipo_depth_report = report
            st.session_state.ipo_depth_saved = (selected, revision, report["context_hash"])
            st.rerun()
    with st.form("ipo_depth_facts"):
        st.subheader("1 · Company and decision context")
        st.caption("Known facts belong here once. Currency and units apply to all monetary model inputs; use separate cases for incompatible bases.")
        company = st.text_input("Company legal name", bundle.get("company", ""), disabled=not editable)
        background = st.text_area("Business background, sector and revenue model", bundle.get("background", ""), disabled=not editable)
        col1, col2, col3 = st.columns(3)
        as_of = col1.text_input("Information cutoff (ISO date)", bundle.get("as_of", ""), disabled=not editable)
        currency = col2.text_input("Currency (e.g. INR)", bundle.get("currency", ""), disabled=not editable)
        unit = col3.text_input("Monetary scale (e.g. millions)", bundle.get("unit", ""), disabled=not editable)
        applied = st.form_submit_button("Apply company facts", disabled=not editable)
        if applied:
            bundle.update(company=company, background=background, as_of=as_of, currency=currency, unit=unit)
            st.session_state.pop("ipo_depth_report", None)
            st.success("Facts applied. Add evidence and optional models, then run the assessment.")
    with st.expander("2 · Extracted attributes, evidence and missing data", expanded=True):
        st.caption("Attach the extracted attribute inventory and versioned CMIE reference in the case bundle. No completeness percentage is inferred from an absent reference.")
        st.json({"available_evidence": bundle.get("evidence", []), "missing_data": bundle.get("gaps", [])}, expanded=False)
        st.markdown("Each evidence item needs an ID, citation, page/table locator, availability date and review state. Repeated documents from one origin do not create independent evidence.")
        with st.form("ipo_depth_source"):
            source_id = st.text_input("Evidence ID", disabled=not editable)
            citation = st.text_input("Source title or citation", disabled=not editable)
            locator = st.text_input("Page, table or document locator", disabled=not editable)
            available = st.text_input("Established availability date (ISO)", disabled=not editable)
            origin = st.text_input("Original source family ID", disabled=not editable)
            review = st.selectbox("Source review state", ["unreviewed", "accepted", "disputed"], disabled=not editable)
            if st.form_submit_button("Add evidence record", disabled=not editable):
                try:
                    from models.pre_ipo_decision.contracts import timestamp
                    timestamp(available)
                    if not all((source_id.strip(), citation.strip(), locator.strip(), origin.strip())):
                        raise ValueError("Evidence ID, citation, locator and source family are required.")
                    if source_id in {row["id"] for row in bundle.get("evidence", [])}:
                        raise ValueError("Use a new evidence ID for a revision; retain the original record.")
                    bundle.setdefault("evidence", []).append({"id": source_id, "citation": citation, "locator": locator, "available_by": available, "origin_id": origin, "review_state": review})
                    st.session_state.pop("ipo_depth_report", None)
                    st.success("Evidence record added. Accepted means your review judgment.")
                except ValueError as exc:
                    st.error(str(exc))
    with st.expander("3 · Optional model inputs"):
        method = st.selectbox("Analysis", list(METHODS))
        signature = inspect.signature(METHODS[method])
        from models.pre_ipo_decision.guidance import explain
        question, mechanism, followup = explain(method, {"data": {}, "state": ""})
        st.write(question)
        st.caption(mechanism)
        st.caption("Why these inputs: " + followup)
        st.caption("Enter only the named inputs for this method. Rates use decimals (0.10 = 10%). Structured lists preserve dated events, security rights and scenarios; absent inputs remain missing.")
        current = bundle.get("models", {}).get(method, {"inputs": {}, "evidence_ids": []})
        binding=bundle.get("model_fact_bindings",{}).get(method)
        if binding:
            st.caption("Prefilled from reviewed snapshot "+binding["snapshot_id"][:12]+" · "+json.dumps(binding["context"],ensure_ascii=False)+". Review this period and definition before adding assumptions.")
        with st.form("ipo_depth_model_" + method):
            fields = {}
            st.caption("Enter numbers as decimals. Text fields need no quotation marks. Structured events, scenarios and classes use JSON lists/objects. Leave optional inputs blank to use the displayed method default.")
            for field, parameter in signature.parameters.items():
                value = current.get("inputs", {}).get(field, parameter.default)
                string_fields = {"claim", "rate_claim", "currency", "rate_currency", "basis", "rate_basis", "failure_metric", "method", "previous", "previous_event_id", "as_of"}
                initial = "" if value is inspect.Parameter.empty else str(value) if field in string_fields and value is not None else json.dumps(value)
                widget = st.text_area if field in {"segments", "events", "facilities", "cash_flows", "candidates", "scales", "weights", "flows", "classes", "gaps", "priors", "utilities", "joint_signal", "opportunities", "context_keys", "orientations", "commitment", "observation", "variants", "a", "b", "bridge"} else st.text_input
                fields[field] = widget(field.replace("_", " ").capitalize(), initial, disabled=not editable, key="ipo_arg_" + method + "_" + field)
            source_ids = st.text_input("Supporting evidence IDs (comma separated)", ", ".join(current.get("evidence_ids", [])), disabled=not editable)
            if st.form_submit_button("Apply optional model", disabled=not editable):
                try:
                    parsed = {key: (value if key in string_fields and value != "null" else json.loads(value)) for key, value in fields.items() if value.strip()}
                    canonical_json(parsed)
                    signature.bind(**parsed)
                    bundle.setdefault("models", {})[method] = {"inputs": parsed, "evidence_ids": [x.strip() for x in source_ids.split(",") if x.strip()]}
                    st.session_state.pop("ipo_depth_report", None)
                    st.success("Inputs applied. Run the assessment to update the results.")
                except (ValueError, TypeError) as exc:
                    st.error(str(exc))
    with st.expander("Advanced case editor · evidence, propositions, scenarios and gaps"):
        st.caption("Use this structured form for imported extraction data and complex nested models. Applying it replaces only this private case, never the existing terminal or source dataset.")
        with st.form("ipo_depth_advanced"):
            text = st.text_area("Complete case JSON", json.dumps(bundle, indent=2), height=320, disabled=not editable)
            if st.form_submit_button("Validate and apply case", disabled=not editable):
                try:
                    candidate = parse_bundle(text)
                    run_case(candidate)
                    _clear_model_fields()
                    st.session_state.ipo_depth_bundle = candidate
                    st.session_state.pop("ipo_depth_report", None)
                    st.rerun()
                except (ValueError, TypeError, KeyError) as exc:
                    st.error(str(exc))
    if st.button("Run decision assessment", type="primary", disabled=not editable):
        try:
            st.session_state.ipo_depth_report = run_case(bundle)
        except (ValueError, TypeError, KeyError) as exc:
            st.error(str(exc))
    report = st.session_state.get("ipo_depth_report")
    if not report:
        st.caption("Apply inputs and run the assessment. No illustrative company values are inserted.")
        return
    if report["context_hash"] != context_hash(bundle):
        st.warning("Inputs changed. Rerun before saving or exporting.")
        return
    st.subheader("4 · Interpretation and action")
    st.caption("Snapshot " + report["context_hash"][:12] + " · " + report["method_version"])
    st.write(report["context"].get("background") or "Company background is missing.")
    for name, result in report["results"].items():
        with st.expander(name.replace("_", " ").title() + " · " + result["state"]):
            for reason in result.get("reasons", []):
                st.warning(reason)
            from models.pre_ipo_decision.guidance import explain
            question, mechanism, followup = result.get("question", name), result.get("mechanism", ""), result.get("recommended_review", "Resolve the evidence requirements.")
            st.write(question)
            st.write(mechanism)
            st.write(result.get("interpretation", "Explicit evidence and rule-based assessment."))
            st.write("Recommended review: " + followup)
            data = result.get("data", {})
            if name == "cash_schedule" and data.get("rows"):
                import pandas as pd
                frame = pd.DataFrame(data["rows"])
                st.dataframe(frame, use_container_width=True)
                st.line_chart(frame.set_index("date")[["cash_close", "funding_gap"]])
            elif name == "attribute_inventory" and data.get("attributes"):
                st.dataframe([{"Attribute": r["label"], "Status": r["state"], "Next action": r["next_action"]} for r in data["attributes"]], use_container_width=True)
            else:
                st.json(data, expanded=False)
            for assumption in result.get("assumptions", []):
                st.caption(assumption)
            st.write("Next action: " + result.get("next_action", "Resolve outstanding evidence and record a review action."))
            st.caption(result.get("evidence_status", "Source support depends on the displayed evidence record."))
    st.subheader("Missing data and diligence")
    st.json(report["results"]["diligence"]["data"], expanded=True)
    with st.expander("Methodology references · separate from issuer evidence"):
        for reference in report.get("methodology_references", []):
            st.markdown("[" + reference["title"] + "](" + reference["url"] + ")")
            st.caption(reference["scope"])
    for limitation in report["limitations"]:
        st.caption(limitation)
    saved = st.session_state.get("ipo_depth_saved")
    if st.button("Save private case revision", disabled=not editable):
        try:
            case_id, revision = store.save_case(owner, role, report, saved[0] if saved else None, saved[1] if saved else 0)
            st.session_state.ipo_depth_saved = (case_id, revision, report["context_hash"])
            st.success("Saved revision " + str(revision))
        except (ValueError, PermissionError) as exc:
            st.error(str(exc))
    saved = st.session_state.get("ipo_depth_saved")
    with st.form("ipo_depth_action"):
        decision = st.selectbox("Review decision", ["Request evidence", "Revise assumptions", "Escalate for review", "Proceed to investment committee", "Defer"])
        rationale = st.text_area("Rationale and next action")
        if st.form_submit_button("Record action on saved revision", disabled=not editable or not saved or saved[2] != report["context_hash"]):
            try:
                store.record_action(owner, role, saved[0], saved[1], {"decision": decision, "rationale": rationale, "persona": persona})
                st.success("Action recorded against the immutable saved revision.")
            except (ValueError, PermissionError) as exc:
                st.error(str(exc))
    from utils.pre_ipo_decision_export import export_json, export_pptx
    st.download_button("Download evidence and results JSON", export_json(report), "pre_ipo_decision.json", "application/json", on_click="ignore")
    st.download_button("Download decision deck", export_pptx(report), "pre_ipo_decision.pptx", "application/vnd.openxmlformats-officedocument.presentationml.presentation", on_click="ignore")

def render():
    with st.container(key="ipo_depth_surface"):
        if st.session_state.get("theme") == "light":
            st.markdown("""
            <style>
            .st-key-ipo_depth_surface [data-testid="stForm"] {
                background: #fff !important; border: 1px solid #cbd5e1 !important;
                border-radius: 12px !important; padding: 16px !important;
            }
            .st-key-ipo_depth_surface [data-testid="stForm"] label,
            .st-key-ipo_depth_surface [data-testid="stForm"] label p,
            .st-key-ipo_depth_surface [data-testid="stForm"] h3,
            .st-key-ipo_depth_surface [data-testid="stForm"] [data-testid="stCaptionContainer"] p {
                color: #0f172a !important;
            }
            .st-key-ipo_depth_surface button {
                background: #fff !important; color: #0f172a !important;
                border-color: #94a3b8 !important;
            }
            .st-key-ipo_depth_surface button p,
            .st-key-ipo_depth_surface button span { color: inherit !important; }
            .st-key-ipo_depth_surface button[kind="primary"],
            .st-key-ipo_depth_surface button[kind="primaryFormSubmit"] {
                background: #4338ca !important; color: #fff !important;
            }
            .st-key-ipo_depth_surface button:disabled { opacity: .55 !important; }
            .st-key-ipo_depth_surface input,
            .st-key-ipo_depth_surface textarea,
            .st-key-ipo_depth_surface [data-baseweb="select"] > div {
                background: #fff !important; color: #0f172a !important;
                border-color: #94a3b8 !important;
            }
            .st-key-ipo_depth_surface [data-baseweb="select"] span,
            .st-key-ipo_depth_surface [data-baseweb="select"] div {
                color: #0f172a !important;
            }
            .st-key-ipo_depth_surface [data-testid="stAlert"] p {
                color: #0f172a !important;
            }
            </style>
            """, unsafe_allow_html=True)
        _render_content()
