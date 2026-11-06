"""Company facts and a durable, evidence-led treasury register."""
import hashlib
import json

import pandas as pd
import streamlit as st

import db
from helpers import ensure_session_state, require_role
from models.debt_metrics import coverage_case, finite
from models.financing import (FACILITY_COLUMNS, REPAYMENT_COLUMNS, validate_register,
    reconcile_register, register_workbook, read_register_workbook, case_payload)
from models.financing_store import list_cases, load_case, save_case

def render_company_financing():
    with st.container(key="company_financing_page"):
        ensure_session_state()
        light = st.session_state.get("theme") == "light"
        foreground, background, border = ("#0F172A", "#FFFFFF", "#CBD5E1") if light else ("#F1F5F9", "#0B0E14", "#475569")
        st.markdown(f"""<style>
        .st-key-company_financing_page label, .st-key-company_financing_page label *,
        .st-key-company_financing_page [data-testid="stWidgetLabel"], .st-key-company_financing_page [data-testid="stWidgetLabel"] *,
        .st-key-company_financing_page [data-testid="stAlert"], .st-key-company_financing_page [data-testid="stAlert"] * {{color:{foreground} !important; opacity:1 !important;}}
        .st-key-company_financing_page [data-testid="stTooltipIcon"], .st-key-company_financing_page [data-testid="stTooltipIcon"] *,
        .st-key-company_financing_page [data-testid="stTooltipIcon"] svg {{color:{foreground} !important;}}
        .st-key-company_financing_page [data-testid="stTooltipIcon"] svg,
        .st-key-company_financing_page [data-testid="stTooltipIcon"] svg * {{fill:none !important; stroke:{foreground} !important;}}
        .st-key-company_financing_page [data-testid="stFileUploader"] button {{background:#4338CA !important; border-color:#4338CA !important; color:#FFFFFF !important;}}
        .st-key-company_financing_page [data-testid="stFileUploader"] button * {{color:#FFFFFF !important;}}
        .st-key-company_financing_form [data-testid="stForm"] {{border:1px solid {border}; border-radius:12px; padding:20px;}}
        .st-key-company_financing_form label, .st-key-company_financing_form label *,
        .st-key-company_financing_form [data-testid="stWidgetLabel"], .st-key-company_financing_form [data-testid="stWidgetLabel"] *,
        .st-key-company_financing_form [data-testid="stTooltipIcon"], .st-key-company_financing_form [data-testid="stTooltipIcon"] * {{color:{foreground} !important; opacity:1 !important;}}
        .st-key-company_financing_form input, .st-key-company_financing_form [data-baseweb="input"],
        .st-key-company_financing_form [data-baseweb="base-input"], .st-key-company_financing_form [data-baseweb="select"] > div {{background:{background} !important; color:{foreground} !important;}}
        .st-key-company_financing_form [data-baseweb="select"] span {{color:{foreground} !important;}}
        .st-key-company_financing_form input::placeholder {{color:{'#64748B' if light else '#94A3B8'} !important; opacity:1 !important;}}
        .st-key-company_financing_form [data-testid="stNumberInputStepUp"], .st-key-company_financing_form [data-testid="stNumberInputStepDown"] {{background:{background} !important; color:{foreground} !important;}}
        .st-key-company_financing_form [data-testid="stFormSubmitButton"] button {{background:#4338CA !important; border-color:#4338CA !important; color:#FFFFFF !important;}}
        .st-key-company_financing_form [data-testid="stFormSubmitButton"] button * {{color:#FFFFFF !important;}}
        </style>""", unsafe_allow_html=True)
        require_role("admin", "researcher")
        user = st.session_state.get("user", {})
        owner = user.get("username", "")
        st.markdown("### Company Financing")
        st.write("Review company facts, add missing treasury evidence, then save a debt register. Known financial values are loaded automatically; you do not need to type them again.")
        st.info("This workspace prepares financing evidence. It does not yet forecast future cash flows or establish borrowing capacity, covenant compliance or a credit rating.")

        vintages = db.get_data_vintages()
        if vintages.empty:
            st.warning("No financial datasets are available.")
            st.stop()
        vintage = st.selectbox("Financing case dataset", vintages.vintage.tolist(),
            format_func=lambda v: str(vintages.set_index("vintage").loc[v, "label"]), key="fin_vintage",
            help="Choose one actual dataset version. A case never silently switches between historical and current observations.")
        companies = db._query("""SELECT c.company_code,c.company_name FROM companies c
            WHERE EXISTS(SELECT 1 FROM financials f WHERE f.company_code=c.company_code AND f.vintage=?)
            ORDER BY c.company_name,c.company_code""", [vintage])
        if companies.empty:
            st.warning("No companies have observations in this dataset.")
            st.stop()
        names = dict(zip(companies.company_code, companies.company_name))
        code = st.selectbox("Financing case company", companies.company_code.astype(int).tolist(),
            format_func=lambda c: f"{names[c]} ({c})", key=f"fin_company_{vintage}")
        history = db._query("SELECT * FROM financials WHERE company_code=? AND vintage=? ORDER BY year", [int(code), vintage])
        if history.year.duplicated().any():
            st.error("Duplicate company/year observations found. Resolve the dataset before creating a financing case.")
            st.stop()
        latest = history.iloc[-1]
        facts = dict(company_code=int(code), company_name=str(names[code]), vintage=vintage, year=int(latest.year),
            **{key: finite(latest.get(key)) for key in ("borrowings", "cash_holdings", "pbit", "interest_amt", "ncfo", "leverage")})
        facts["interest_coverage"] = coverage_case(facts["pbit"], facts["interest_amt"], facts["borrowings"])["coverage"]
        st.markdown("#### 1. Review source facts")
        st.caption(f"Company {code} | Dataset {vintage} | FY{facts['year']} | Source amounts retain dataset units. Currency, scale and statement basis require confirmation.")
        fact_labels = {"borrowings": "Reported borrowings", "cash_holdings": "Reported cash (availability unverified)",
            "pbit": "Profit before interest and tax (PBIT)", "interest_amt": "Annual interest expense",
            "ncfo": "Operating cash flow", "leverage": "Reported leverage (%)", "interest_coverage": "Interest coverage (x)"}
        fact_rows = [("Fiscal year", str(facts["year"]))]
        for field, label in fact_labels.items():
            value = facts[field]
            suffix = "%" if field == "leverage" else "x" if field == "interest_coverage" else ""
            fact_rows.append((label, "Unavailable" if value is None else f"{value:,.2f}{suffix}"))
        st.dataframe(pd.DataFrame(fact_rows, columns=["Observed fact / derived coverage", "Value"]),
            hide_index=True, use_container_width=True)

        cases = list_cases(owner, code, vintage)
        case_names = {row["case_id"]: f"{row['title']} · {row['case_id'][:8]}" for row in cases}
        selection_key = f"fin_case_{owner}_{vintage}_{code}"
        pending = st.session_state.pop(selection_key+"_pending", None)
        if pending in case_names:
            st.session_state[selection_key] = pending
        selected = st.selectbox("Saved financing case", ["new", *case_names],
            format_func=lambda c: "Create a new case" if c == "new" else case_names[c], key=selection_key)
        notice = st.session_state.pop(selection_key+"_notice", None)
        if notice:
            st.success(notice)
        scope = f"fin_{owner}_{vintage}_{code}_{selected}"
        state_key = scope + "_working"
        if state_key not in st.session_state:
            loaded = load_case(owner, selected) if selected != "new" else None
            st.session_state[state_key] = dict(title=loaded["title"] if loaded else "",
                revision=loaded["revision"] if loaded else 0, case_id=loaded["case_id"] if loaded else None,
                payload=loaded["payload"] if loaded else {}, generation=0)
        working = st.session_state[state_key]
        if selected != "new":
            st.caption(f"Loaded revision {working['revision']}. Saving appends a new revision; previous records remain available.")
            left, right = st.columns(2)
            with left:
                if st.button("Reload latest saved revision", key=scope+"_reload"):
                    st.session_state.pop(state_key, None)
                    st.rerun()
            with right:
                revision = st.selectbox("Inspect saved revision", range(1, working["revision"]+1), index=working["revision"]-1, key=scope+"_revision")
                historical = load_case(owner, selected, revision)
                st.download_button("Download saved revision JSON", json.dumps(historical, indent=2),
                    file_name=f"{code}_{selected}_r{revision}.json", mime="application/json", key=scope+"_history")

        st.markdown("#### 2. Complete the optional treasury evidence")
        st.write("Save an incomplete draft if evidence is not yet available. Blank means unknown; enter zero only when it is confirmed. All amounts must use the selected scale. Different currencies remain separate and are not added together.")
        st.download_button("Download Excel register template", register_workbook(),
            file_name="company_debt_register_template.xlsx", key=scope+"_template")
        upload = st.file_uploader("Import a completed register template (optional)", type=["xlsx"], key=scope+"_upload")
        if upload:
            digest = hashlib.sha256(upload.getvalue()).hexdigest()
            try:
                imported = read_register_workbook(upload.getvalue())
                st.caption("Import preview. Existing working values change only after you select Use imported draft; saving is a separate action.")
                st.dataframe(pd.DataFrame(imported["facilities"], columns=FACILITY_COLUMNS), hide_index=True)
                for message in imported["errors"]:
                    st.error(message)
                if st.button("Use imported draft", disabled=bool(imported["errors"]), key=scope+"_import_"+digest):
                    working["payload"] = dict(context=imported["context"], facilities=imported["facilities"], repayments=imported["repayments"])
                    working["generation"] += 1
                    st.rerun()
            except (ValueError, KeyError, OSError) as exc:
                st.error(f"Workbook could not be imported: {exc}")
            except Exception:
                st.error("Workbook could not be read. Use an unencrypted Excel template from this page.")

        payload = working["payload"]
        context = payload.get("context", {})
        form_key = scope + f"_g{working['generation']}"
        form_host = st.container(key="company_financing_form")
        with form_host, st.form(form_key, border=True):
            title = st.text_input("Case title *", value=working["title"], max_chars=150,
                placeholder="For example: FY2025 treasury evidence review")
            st.markdown("**Reporting context and available cash**")
            left, right = st.columns(2)
            with left:
                currency = st.text_input("Reporting currency", value=context.get("currency") or "", max_chars=3,
                    help="Three-letter code such as INR. Confirm this against the source statements.")
                scales = ["Unconfirmed", "units", "thousands", "lakhs", "millions", "crores"]
                scale = st.selectbox("Monetary scale", scales, index=scales.index(context.get("scale")) if context.get("scale") in scales else 0)
                cash = st.number_input("Confirmed unrestricted cash", min_value=0.0, value=context.get("unrestricted_cash"),
                    placeholder="Leave blank until confirmed", help="Management-confirmed available cash; reported cash is not automatically unrestricted.")
            with right:
                bases = ["Unconfirmed", "standalone", "consolidated"]
                basis = st.selectbox("Financial statement basis", bases, index=bases.index(context.get("statement_basis")) if context.get("statement_basis") in bases else 0)
                as_of = st.text_input("Register as-of date (YYYY-MM-DD)", value=context.get("as_of") or "",
                    help="Balance date for this register. Dates of future principal payments must be later.")
                source = st.text_input("Context evidence source", value=context.get("source") or "",
                    help="Document name, statement date or treasury schedule reference.")
            confirmed = st.checkbox("I confirm the register matches the source facts in currency, scale, statement basis and reporting date",
                value=payload.get("basis_confirmed", False), help="Required only for a numerical reconciliation. Unconfirmed or mixed-currency registers remain drafts.")
            st.markdown("**Debt facilities**")
            st.caption("Use one row per facility and a unique facility_id. Rate type is fixed or floating. annual_rate_pct is the current all-in annual rate; spread_bps is additional benchmark detail. Dates use YYYY-MM-DD. Add/remove rows using the table controls.")
            facilities = st.data_editor(pd.DataFrame(payload.get("facilities", []), columns=FACILITY_COLUMNS),
                num_rows="dynamic", hide_index=True, use_container_width=True, key=form_key+"_facilities")
            st.markdown("**Future principal repayments**")
            st.caption("Link each payment to a facility_id. Enter principal only; interest is not principal. Include the full remaining schedule, including any final balloon payment. Do not enter an assumed repayment when the schedule is unknown.")
            repayments = st.data_editor(pd.DataFrame(payload.get("repayments", []), columns=REPAYMENT_COLUMNS),
                num_rows="dynamic", hide_index=True, use_container_width=True, key=form_key+"_repayments")
            st.markdown("**What happens when you save?**")
            st.write("The app checks IDs, dates and amounts; lists missing evidence; compares scheduled principal with drawn balances; and saves a private, versioned case with a snapshot of today's displayed source facts. It never overwrites the financial dataset. Cash-flow forecasting and borrowing-capacity assessment will require a later planning step.")
            submitted = st.form_submit_button("Validate and save case", type="primary")

        if submitted:
            register = validate_register(dict(currency=currency, scale=None if scale == "Unconfirmed" else scale,
                statement_basis=None if basis == "Unconfirmed" else basis, as_of=as_of, source=source, unrestricted_cash=cash), facilities, repayments)
            if register["errors"]:
                for error in register["errors"]:
                    st.error(error)
            else:
                try:
                    snapshot = case_payload(register, facts, confirmed)
                    saved = save_case(owner, user.get("role"), code, vintage, title, snapshot,
                        case_id=working.get("case_id"), expected_revision=working["revision"])
                    working.update(title=title, revision=saved["revision"], case_id=saved["case_id"], payload=snapshot)
                    st.session_state[selection_key+"_pending"] = saved["case_id"]
                    st.session_state[selection_key+"_notice"] = f"Case saved as revision {saved['revision']}. Source financials were preserved."
                    if selected == "new":
                        st.session_state.pop(state_key, None)
                    st.rerun()
                except (ValueError, PermissionError) as exc:
                    st.error(str(exc))

        st.markdown("#### 3. Review evidence and reconciliation")
        active = working["payload"]
        register = validate_register(active.get("context", {}), active.get("facilities", []), active.get("repayments", []))
        if active:
            saved_facts = active.get("observed_facts", {})
            if saved_facts and saved_facts != facts:
                st.warning("Source facts have changed since this case was saved. Review the current facts above; save a new revision to update the snapshot.")
            st.caption("Results below reflect the last saved or imported draft, not unsubmitted table edits.")
        for gap in register["gaps"]:
            st.warning(gap)
        reconciliation = reconcile_register(register, facts["borrowings"], active.get("basis_confirmed", False))
        if reconciliation["comparable"]:
            st.metric("Register drawn debt", f"{reconciliation['drawn_total']:,.2f}")
            difference = reconciliation["difference"]
            if difference is None:
                st.info("Reported borrowings are unavailable; no source reconciliation can be calculated.")
            elif abs(difference) > 1e-6:
                st.warning(f"Register less reported borrowings: {difference:,.2f}. Explain the difference before using this register for financing decisions.")
            else:
                st.success("Register drawn balance reconciles with reported borrowings on the confirmed basis.")
        else:
            st.info("Numerical reconciliation is unavailable until amounts and a matching reporting basis are confirmed. Mixed currencies require currency conversion evidence.")
        if register["repayments"]:
            schedule = pd.DataFrame(register["repayments"])
            currencies = {r["facility_id"]: r["currency"] for r in register["facilities"]}
            schedule["currency"] = schedule.facility_id.map(currencies)
            st.dataframe(schedule, hide_index=True, use_container_width=True)
        if active:
            st.download_button("Download working register Excel", register_workbook(register["context"], register["facilities"], register["repayments"]),
                file_name=f"{code}_debt_register.xlsx", key=scope+"_export")
        st.caption("Historical board decks remain available without completing this workspace. No scenario or deck assumptions are applied automatically.")


render_company_financing()
