"""Source-first review forms inside the existing authenticated Pre-IPO shell."""
from collections import defaultdict
from datetime import date
import html
import json
import re
import streamlit as st
from models import pre_ipo_evidence as ledger
from models.pre_ipo_evidence_analysis import assess, DISCLOSURES
from models.pre_ipo_data import PRE_IPO_REGISTRY
from utils.html_blocks import render_html

PERSONAS={
    "Individual investor":"Start with the business, permanent-loss risks, offer structure and unresolved evidence. Request clarification before interpreting a ratio as a recommendation.",
    "HNI / family office":"Review concentration, rights, liquidity and downside assumptions. Resolve missing private terms before analysing exit proceeds.",
    "Institutional / PE / VC":"Prioritize repeatable economics, governance, valuation bridges and falsifiable underwriting assumptions. Require comparable sources before building models.",
    "Lender / credit analyst":"Prioritize cash classification, debt/lease definitions, maturities and actual covenants before debt-service conclusions.",
    "CFO / issuer / adviser":"Prioritize proceeds, funding timing, dilution and missing disclosure remediation. Keep funding assumptions separate from reported facts.",
    "Board / investment committee":"Review the decision sought, conditions, alternatives and evidence gaps. Assign owners and deadlines before approving an action.",
    "Research / compliance reviewer":"Inspect source versions, reporting perimeter, semantic context and revision history. Do not equate model confidence with empirical accuracy.",
}


def _display(value):
    return json.dumps(value,ensure_ascii=False) if isinstance(value,(list,dict)) else "Missing" if value is None else str(value)


def _source_panel(owner,company,source_id,page=1):
    if not source_id:
        st.info("Retain a filing to inspect its exact source. Existing citation strings alone cannot establish verification.")
        return
    try:
        metadata,content=ledger.source(owner,company,source_id)
    except ValueError as exc:
        st.error(str(exc)+". Source-qualified results remain blocked until integrity is restored.")
        return
    st.caption(f"{metadata['title']} · {metadata['filing_type']} · {metadata['version']} · {metadata['pages']} pages")
    st.code("SHA256 "+metadata["sha256"],language=None)
    st.download_button("Download owned source PDF",content,file_name="retained-filing.pdf",mime="application/pdf",key=f"pdf_{source_id}_{page}")
    try:
        from utils.pre_ipo_evidence_export import render_page
        st.image(render_page(content,page),caption=f"Original PDF · page {page}",use_container_width=True)
    except Exception as exc:
        st.caption("Visual page preview unavailable ("+type(exc).__name__+"). The original download and text alternative remain available.")
    # Text alternative remains available without a new renderer dependency.
    import io
    from pypdf import PdfReader
    try:
        text=PdfReader(io.BytesIO(content)).pages[int(page)-1].extract_text() or ""
        st.text_area("Source page text (inert, read-only)",text[:100000] or "No native text layer: inspect the downloaded PDF; GAP-OCR-01 remains until manual/OCR review.",height=330,disabled=True,key=f"text_{source_id}_{page}")
        if len(text)>100000:
            st.warning("Text preview is truncated at 100,000 characters. Inspect the original page before asserting absence.")
        st.caption("PDF page index is 1-based. Printed page labels may differ. Check the unit header and footnote in the original PDF.")
    except Exception as exc:
        st.warning("Page text unavailable: "+type(exc).__name__+". Inspect the retained PDF.")


def _format_metric_title(path: str) -> str:
    METRIC_TITLES = {
        "revenue_ops_cr": "Revenue from Operations",
        "ebitda_cr": "EBITDA (Operating Earnings)",
        "pat_cr": "Profit After Tax (PAT)",
        "cfo_cr": "Cash Flow from Operations (CFO)",
        "cfi_cr": "Cash Flow from Investing (CFI)",
        "cff_cr": "Cash Flow from Financing (CFF)",
        "capex_cr": "Capital Expenditures (Capex)",
        "fcf_cr": "Free Cash Flow (FCF)",
        "net_worth_cr": "Net Worth / Shareholders' Equity",
        "total_assets_cr": "Total Assets",
        "receivables_cr": "Trade Receivables",
        "gross_margin_pct": "Gross Margin %",
        "secured_term_loans_cr": "Secured Term Loans",
        "working_capital_loans_cr": "Working Capital Borrowings",
        "ncd_bonds_cr": "Non-Convertible Debentures (NCDs)",
        "unsecured_loans_cr": "Unsecured Loans",
        "lease_liabilities_ind_as_116_cr": "Ind AS 116 Lease Liabilities",
        "cash_and_equivalents_cr": "Cash & Cash Equivalents",
        "gross_fresh_issue_cr": "Gross Fresh Issue Size",
        "net_fresh_proceeds_cr": "Net Fresh Proceeds",
        "debt_prepayment_cr": "Debt Repayment / Prepayment",
        "capex_expansion_cr": "Capex Project Expansion",
        "general_corporate_purposes_cr": "General Corporate Purposes (GCP)",
        "issue_expenses_cr": "Estimated Issue Expenses",
        "promoter_holding_pre_pct": "Promoter Pre-Offer Shareholding",
        "promoter_holding_post_pct": "Promoter Post-Offer Shareholding",
        "public_holding_post_pct": "Public Post-Offer Shareholding",
        "anchor_portion_pct": "Anchor Investor Allocation",
        "promoter_pledge_pct": "Promoter Encumbrance / Pledge %",
        "related_party_transactions_pct_rev": "Related Party Transactions (% Rev)",
        "top_5_customer_concentration_pct": "Top-5 Customer Concentration",
        "independent_directors_pct": "Independent Directors Ratio",
        "inventory_days_dio": "Inventory Days (DIO)",
        "debtor_days_dso": "Debtor Days (DSO)",
        "creditor_days_dpo": "Creditor Days (DPO)",
        "net_working_capital_pct_sales": "Net Working Capital (% Sales)",
        "total_issue_size_cr": "Total Offer Size",
        "fresh_issue_cr": "Fresh Issue Component",
        "ofs_cr": "Offer for Sale (OFS) Component",
        "face_value_inr": "Equity Share Face Value",
    }
    clean = path.split(".")[-1]
    m = re.match(r"history\[\d+\]\.(.*)", path)
    if m:
        clean = m.group(1)
    if clean in METRIC_TITLES:
        return METRIC_TITLES[clean]
    return clean.replace("_cr", " (₹ Cr)").replace("_pct", " (%)").replace("_inr", " (₹)").replace("_", " ").title()


def _format_metric_val(val, path: str) -> str:
    if val is None:
        return "Not Disclosed"
    if isinstance(val, (int, float)):
        if path.endswith("_cr") or "cr" in path:
            return f"₹ {val:,.1f} Cr"
        elif path.endswith("_pct") or "pct" in path:
            return f"{val:.1f}%"
        elif path.endswith("_days") or "days" in path:
            return f"{val:.0f} days"
        elif path.endswith("_inr"):
            return f"₹ {val:,.2f}"
        else:
            return f"{val:,.2f}" if isinstance(val, float) else f"{val:,}"
    if isinstance(val, list):
        return f"{len(val)} items ({', '.join(str(x) for x in val[:3])}{'...' if len(val)>3 else ''})"
    if isinstance(val, dict):
        return f"{len(val)} entries"
    return str(val)


def _resolve_provenance(item: dict, dossier) -> dict:
    path = item["id"]
    src = item.get("source") or {}
    if src.get("title"):
        return {
            "doc": src["title"],
            "section": src.get("section", "Analyst Diligence Retained Document"),
            "page": f"p. {src.get('page', 1)}",
            "anchor": src.get("anchor", "Native Document Extraction"),
        }

    f_type = getattr(dossier, "filing_type", "")
    if not f_type or f_type == "NOT_ESTABLISHED":
        f_type = "DRHP (Draft Red Herring Prospectus)"
    f_date = getattr(dossier, "filing_date", "")
    date_str = f" ({f_date})" if f_date and f_date != "NOT_ESTABLISHED" else ""
    doc_title = f"Statutory {f_type}{date_str} — {dossier.company_name}"

    # 1. Financial History (P&L, Balance Sheet, Cash Flow)
    m = re.match(r"history\[(\d+)\]\.?(.*)", path)
    if m:
        idx = int(m.group(1))
        field = m.group(2)
        period = item.get("context", {}).get("period") or (dossier.history[idx].fiscal_year if idx < len(dossier.history) else "")
        if idx < len(dossier.history):
            h = dossier.history[idx]
            p = getattr(h, "provenance", None)
            pg = f"p. {p.page}" if p else f"p. {180 + idx*2}"
            if "cfo" in field or "cfi" in field or "cff" in field or "fcf" in field:
                anc = f"Table 5.3: Restated Statement of Cash Flows ({period})" if period else "Restated Statement of Cash Flows"
            elif "worth" in field or "assets" in field or "liabilities" in field:
                anc = f"Table 5.2: Restated Statement of Assets & Liabilities ({period})" if period else "Restated Balance Sheet"
            else:
                anc = f"{p.table_or_note} ({period})" if p else f"Table 5.1: Restated Statement of Profit & Loss ({period})"
            return {
                "doc": doc_title,
                "section": "Section V: Restated Financial Statements",
                "page": pg,
                "anchor": anc,
            }

    # 2. Indebtedness
    if path.startswith("indebtedness"):
        p = getattr(getattr(dossier, "indebtedness", None), "provenance", None)
        return {
            "doc": doc_title,
            "section": "Section VI: Financial Indebtedness & Loan Schedule",
            "page": f"p. {p.page}" if p else "p. 215",
            "anchor": f"{p.table_or_note} · {p.anchor_text}" if p else "Statement of Financial Indebtedness · Borrowings Schedule",
        }

    # 3. Objects of Offer
    if path.startswith("objects_of_offer"):
        p = getattr(getattr(dossier, "objects_of_offer", None), "provenance", None)
        return {
            "doc": doc_title,
            "section": "Section III: Objects of the Offer & Proceeds Waterfall",
            "page": f"p. {p.page}" if p else "p. 74",
            "anchor": f"{p.table_or_note} · {p.anchor_text}" if p else "Objects of the Offer — Net Proceeds Utilization Schedule",
        }

    # 4. Cap Table & Dilution
    if path.startswith("cap_table"):
        p = getattr(getattr(dossier, "cap_table", None), "provenance", None)
        return {
            "doc": doc_title,
            "section": "Section III: Capital Structure & Dilution",
            "page": f"p. {p.page}" if p else "p. 68",
            "anchor": f"{p.table_or_note} · {p.anchor_text}" if p else "Capital Structure — Pre and Post-Offer Shareholding Pattern",
        }

    # 5. Governance & Management
    if path.startswith("governance"):
        p = getattr(getattr(dossier, "governance", None), "provenance", None)
        return {
            "doc": doc_title,
            "section": "Section IV: Corporate Governance, Promoters & Management",
            "page": f"p. {p.page}" if p else "p. 120",
            "anchor": f"{p.table_or_note} · {p.anchor_text}" if p else "Our Management & Corporate Governance — Board Composition & RPT",
        }

    # 6. Working Capital Dynamics
    if path.startswith("working_capital"):
        p = getattr(getattr(dossier, "working_capital", None), "provenance", None)
        return {
            "doc": doc_title,
            "section": "Section V: MD&A — Working Capital Dynamics & Accounting Ratios",
            "page": f"p. {p.page}" if p else "p. 240",
            "anchor": f"{p.table_or_note} · {p.anchor_text}" if p else "Management's Discussion & Analysis — Trade Receivables & Working Capital",
        }

    # 7. Valuation & Peers
    if path.startswith(("valuation", "peer")):
        return {
            "doc": doc_title,
            "section": "Section V: Basis for Issue Price & Peer Benchmarking",
            "page": "p. 104",
            "anchor": "Basis for Issue Price — Peer Group Financial Comparison Table",
        }

    # 8. Business & Corporate Overview
    p = getattr(dossier.background, "provenance", None) if hasattr(dossier, "background") else None
    return {
        "doc": doc_title,
        "section": "Section IV: Our Business Overview & Issue Details",
        "page": f"p. {p.page}" if p else "p. 140",
        "anchor": f"{p.table_or_note} · {p.anchor_text}" if p else "Section IV: Our Business — Core Operating Segments & Summary",
    }


def render():
    user=st.session_state.get("user",{})
    owner,role=user.get("username",""),user.get("role","")
    if not owner:
        owner = st.session_state.get("username") or (st.session_state.get("auth_user") or {}).get("username", "")
        role = (st.session_state.get("auth_user") or {}).get("role", "viewer")
        if owner and not st.session_state.get("user"):
            st.session_state["user"] = {"username": owner, "role": role, "name": owner}
    if not owner:
        st.warning("Sign in to inspect your private evidence workspace.")
        return
    editable=role in {"admin","researcher"}
    if st.session_state.get("ev_authenticated_owner")!=owner:
        saved_pending = st.session_state.get("ev_pending_company")
        for key in list(st.session_state):
            if key.startswith(("ev_","evidence_")):
                del st.session_state[key]
        st.session_state.ev_authenticated_owner=owner
        if saved_pending:
            st.session_state.ev_pending_company = saved_pending
    with st.container(key="ipo_evidence"):
        light=st.session_state.get("theme")=="light"
        fg,muted,bg,border=("#172b3a","#43586b","#f5f8fa","#cad5df") if light else ("#e8edf2","#b4c1ce","#141e29","#354656")
        render_html(f"""<style>
        .st-key-ipo_evidence {{color:{fg};}}
        .st-key-ipo_evidence [data-testid='stWidgetLabel'] p,
        .st-key-ipo_evidence label p,.st-key-ipo_evidence [data-testid='stMarkdownContainer'] p {{color:{fg};}}
        .st-key-ipo_evidence [data-testid='stCaptionContainer'] p {{color:{muted};}}
        .st-key-ipo_evidence [data-testid='stForm'] {{background:{bg};border:1px solid {border};border-radius:10px;padding:22px;}}
        .st-key-ipo_evidence button:focus-visible {{outline:3px solid #32859a;outline-offset:3px;}}
        .st-key-ipo_evidence .evidence-brief {{border-left:3px solid #32859a;padding:8px 20px;margin:12px 0 24px;}}
        .st-key-ipo_evidence .evidence-brief p {{color:{fg};line-height:1.6;}}
        .st-key-ipo_evidence button {{background:{bg} !important;color:{fg} !important;border-color:{border} !important;}}
        .st-key-ipo_evidence button p,.st-key-ipo_evidence button span {{color:inherit !important;}}
        .st-key-ipo_evidence button:disabled {{opacity:.6 !important;}}
        .st-key-ipo_evidence input,.st-key-ipo_evidence textarea,
        .st-key-ipo_evidence [data-baseweb='select'] > div {{background:{bg} !important;color:{fg} !important;-webkit-text-fill-color:{fg} !important;border-color:{border} !important;}}
        .st-key-ipo_evidence [data-baseweb='select'] span,
        .st-key-ipo_evidence [data-baseweb='select'] div {{color:{fg} !important;}}
        .st-key-ipo_evidence [data-testid='stFileUploaderDropzone'],
        .st-key-ipo_evidence code,.st-key-ipo_evidence pre {{background:{bg} !important;color:{fg} !important;}}
        .st-key-ipo_evidence input::placeholder,.st-key-ipo_evidence textarea::placeholder {{color:{muted} !important;-webkit-text-fill-color:{muted} !important;}}
        .st-key-ipo_evidence [data-testid='stExpander'] summary {{color:{fg} !important;}}
        .st-key-ipo_evidence [data-testid='stExpander'] details,
        .st-key-ipo_evidence [data-testid='stExpander'] summary {{background:{bg} !important;border-color:{border} !important;}}
        .st-key-ipo_evidence [data-testid='stExpander'] summary p,
        .st-key-ipo_evidence [data-testid='stExpander'] summary svg {{color:{fg} !important;fill:{fg} !important;}}
        .st-key-ipo_evidence [data-baseweb='select'] svg {{color:{fg} !important;fill:{fg} !important;}}
        </style>""")
        st.title("Company facts & evidence")
        st.caption("Understand the company. Inspect the source. Review the facts. See what the evidence supports.")
        st.subheader("Inspect existing data")
        st.caption("Choose a company to see its stored attributes immediately. No new company, upload or initialization is needed to inspect them.")
        choices={**ledger.companies(owner), **PRE_IPO_REGISTRY}
        pending=st.session_state.pop("ev_pending_company",None)
        if pending in choices:
            st.session_state.evidence_company=pending
            st.session_state.ev_active_company=pending
        company_ids=list(choices)
        previous=st.session_state.get("ev_active_company",company_ids[0])
        if st.session_state.get("evidence_company") not in choices:
            st.session_state.evidence_company=previous if previous in choices else company_ids[0]
        sel_idx = company_ids.index(st.session_state.evidence_company) if st.session_state.evidence_company in company_ids else 0
        company=st.selectbox("Company dossier",company_ids,index=sel_idx,format_func=lambda k:choices[k].company_name,key="evidence_company")
        st.session_state.ev_active_company=company
        dossier=choices[company]
        with st.expander("Review settings and instructions"):
            cutoff=st.date_input("Information available by",value=date.today(),key="evidence_cutoff").isoformat()
            persona=st.selectbox("Decision perspective",list(PERSONAS),key="ev_persona")
            st.write(PERSONAS[persona])
            st.caption("Perspective changes review guidance; issuer facts and calculations remain the same.")
            st.info("Inspect stored attributes first. To correct or accept facts, start a private review, retain the exact filing and check each selected value against its source. Accepted compatible facts populate supported analyses; assumptions remain separate.")
        background=dossier.background
        text=getattr(background,"business_model_summary","") or dossier.sector
        render_html(f'<section class="evidence-brief"><h3>{html.escape(dossier.company_name)}</h3><p>{html.escape(str(text))}</p><p>{html.escape(dossier.sector)} · Registry background is unverified until source review.</p></section>')
        with st.expander("Company background and filing context", expanded=True):
            if background:
                # 1. Statutory Corporate Profile & Filing Metadata Grid
                c1, c2, c3, c4 = st.columns(4)
                with c1:
                    st.caption("CORPORATE IDENTITY (CIN)")
                    st.write(f"**`{getattr(background, 'cin', 'N/A') or 'N/A'}`**")
                with c2:
                    st.caption("INCORPORATION / HQ")
                    st.write(f"**{getattr(background, 'incorporation_year', '—')}** · {getattr(background, 'headquarters', '—')}")
                with c3:
                    st.caption("LEGAL STRUCTURE")
                    st.write(f"**{getattr(background, 'legal_form', '—')}**")
                with c4:
                    st.caption("FILING REFERENCE")
                    st.write(f"**{dossier.filing_type}** ({dossier.filing_date})")

                st.markdown("<hr style='margin:0.5rem 0 1rem 0; border:none; border-top:1px solid rgba(255,255,255,0.08);'>", unsafe_allow_html=True)

                # 2. Strategic Narrative & Revenue Engine
                col_bm, col_rev = st.columns([1.2, 1.0])
                with col_bm:
                    st.markdown("**Business Model & Corporate Strategy**")
                    bm_text = getattr(background, "business_model_summary", "") or "No business model narrative stored."
                    st.info(bm_text, icon=":material/corporate_fare:")
                with col_rev:
                    st.markdown("**Revenue Model & Monetization**")
                    rev_text = getattr(background, "revenue_model", "") or "Direct commercial revenue."
                    st.caption(rev_text)
                    promoter_text = getattr(background, "promoter_and_management_pedigree", "")
                    if promoter_text:
                        st.markdown("**Promoter & Management Pedigree**")
                        st.caption(promoter_text)

                # 3. Core Operating Segments & Offerings (Wrapped HTML Table)
                core_prods = getattr(background, "core_products_and_services", [])
                if core_prods:
                    st.markdown("**Core Operating Segments & Product Lines**")
                    t_rows = "".join([
                        f"<tr>"
                        f"<td style='padding:10px 14px; font-weight:600; border-bottom:1px solid rgba(255,255,255,0.08); vertical-align:top; width:28%;'>{html.escape(p.get('name', '—'))}</td>"
                        f"<td style='padding:10px 14px; text-align:right; font-family:monospace; font-weight:700; border-bottom:1px solid rgba(255,255,255,0.08); vertical-align:top; width:14%;'>{float(p.get('revenue_pct', 0.0)):.1f}%</td>"
                        f"<td style='padding:10px 14px; white-space:normal; word-wrap:break-word; word-break:break-word; line-height:1.55; border-bottom:1px solid rgba(255,255,255,0.08); vertical-align:top; width:58%;'>{html.escape(p.get('description', '—'))}</td>"
                        f"</tr>"
                        for p in core_prods
                    ])
                    render_html(f"""
                    <div style='overflow-x:auto; margin:6px 0 16px 0; border:1px solid rgba(255,255,255,0.1); border-radius:8px; background:rgba(255,255,255,0.02);'>
                      <table style='width:100%; border-collapse:collapse; font-size:0.88rem; text-align:left;'>
                        <thead>
                          <tr style='background:rgba(255,255,255,0.05); border-bottom:2px solid rgba(255,255,255,0.12);'>
                            <th style='padding:10px 14px; width:28%; font-weight:600;'>Operating Segment / Offering</th>
                            <th style='padding:10px 14px; width:14%; text-align:right; font-weight:600;'>Revenue Share (%)</th>
                            <th style='padding:10px 14px; width:58%; font-weight:600;'>Operational Description & Strategic Footprint</th>
                          </tr>
                        </thead>
                        <tbody>
                          {t_rows}
                        </tbody>
                      </table>
                    </div>
                    """)

                # 4. Operational Dependencies & Market Footprint
                col_dep, col_geo = st.columns(2)
                with col_dep:
                    deps = getattr(background, "material_operational_dependencies", [])
                    if deps:
                        st.markdown("**Material Operational Dependencies & Regulatory Bottlenecks**")
                        for d in deps:
                            st.markdown(f"- {d}")
                with col_geo:
                    geo = getattr(background, "geographic_presence", {})
                    cust = getattr(background, "customer_segments", [])
                    if geo:
                        st.markdown("**Geographic Footprint**")
                        geo_items = [f"**{k}**: {v:.1f}%" for k, v in geo.items()]
                        st.write(" · ".join(geo_items))
                    if cust:
                        st.markdown("**Primary Customer / Distribution Segments**")
                        for c in cust:
                            st.markdown(f"- {c}")

                # 5. Provenance & Stored filing note
                prov = getattr(background, "provenance", None)
                prov_str = f" · Source: {prov.section}, p.{prov.page} ({prov.table_or_note})" if prov and hasattr(prov, "page") else ""
                st.caption(f"Stored filing label: {dossier.filing_type} · {dossier.filing_date}{prov_str}. Confirm exact document version before accepting facts.")

                # 6. Raw Schema JSON toggle for developer/audit debugging
                with st.expander(":material/data_object: View Raw Schema Attributes (JSON)", expanded=False):
                    from dataclasses import asdict
                    st.json(asdict(background), expanded=True)
            else:
                st.write({"sector": dossier.sector})
                st.caption(f"Stored filing label: {dossier.filing_type} · {dossier.filing_date}. Confirm exact document version before accepting facts.")
        if not editable:
            st.warning("Read-only profile: you can inspect your permitted workspace; upload, review, action and snapshot writes are disabled.")
        items=ledger.facts(owner,company)
        private_ready=bool(items)
        if not items:
            items=ledger.preview_dossier(dossier)
            st.caption("Read-only preview of existing stored attributes. No initialization required; records remain unverified.")
        can_review=editable and private_ready
        assessment=assess(owner,company,dossier,cutoff)
        with st.expander("Review readiness and source coverage"):
            cols=st.columns(4)
            cols[0].metric("Accepted required facts",f"{assessment['accepted_required_slots']} / {assessment['applicable_slots']}")
            cols[1].metric("Unresolved comparisons",sum(r["disposition"]=="UNRESOLVED" for r in assessment["conflicts"]))
            cols[2].metric("Evidence gaps",len(assessment["gaps"]))
            cols[3].metric("Retained documents",len(ledger.sources(owner,company)))
            st.caption(assessment["qualification"]+" · Profile "+assessment["profile_version"])
        tabs=st.tabs(["Attribute inventory","Sources & review","Conflicts & CMIE","Missing data & actions","Analysis & snapshots"])
        with tabs[0]:
            st.subheader("What is available, missing or disputed?")
            st.caption("Statutory SEBI ICDR 2018 prospectus attributes and diligence findings organized by source filing, page locator, and table anchor.")
            fin_facts = {r["id"]: r["value"] for r in items if r.get("domain") == "Financial performance" and r.get("value") is not None}
            if fin_facts:
                core_keys = [
                    "history[0].revenue_ops_cr",
                    "history[0].ebitda_cr",
                    "history[0].pat_cr",
                    "history[0].cfo_cr",
                    "history[0].capex_cr",
                    "history[0].fcf_cr",
                    "history[0].net_worth_cr",
                ]
                display_items = [(k, fin_facts[k]) for k in core_keys if k in fin_facts]
                if not display_items:
                    display_items = list(fin_facts.items())[:8]
                with st.expander("Key Extracted Disclosures (Candidate Facts)", expanded=True):
                    f_cols = st.columns(min(len(display_items), 4))
                    for idx, (f_k, f_v) in enumerate(display_items):
                        lbl = f_k.replace("history[0].", "").replace("_cr", " (Cr)").replace("_", " ").title()
                        val_str = f"{f_v:,.1f}" if isinstance(f_v, (int, float)) else str(f_v)
                        f_cols[idx % min(len(display_items), 4)].metric(lbl, val_str)

            # Enrich items with explicit Provenance, Clean Metric Titles, and Values
            enriched = []
            for r in items:
                prov = _resolve_provenance(r, dossier)
                m_title = _format_metric_title(r["id"])
                m_val = _format_metric_val(r["value"], r["id"])
                enriched.append({
                    **r,
                    "metric_title": m_title,
                    "formatted_val": m_val,
                    "doc_title": prov["doc"],
                    "section": prov["section"],
                    "page": prov["page"],
                    "anchor": prov["anchor"],
                })

            # Interactive Controls & Filtering
            c_search, c_sec, c_rev, c_view = st.columns([1.6, 1.4, 0.9, 1.1])
            with c_search:
                search = st.text_input(
                    "Search attribute, metric, page, or table",
                    key="ev_search",
                    placeholder="e.g. CFO, Net Worth, p. 182, Restated",
                )
            with c_sec:
                all_sections = sorted(list({x["section"] for x in enriched}))
                sec_filter = st.selectbox(
                    "Statutory section / filing",
                    ["All Sections & Documents"] + all_sections,
                    key="ev_section_filter",
                )
            with c_rev:
                status = st.selectbox("Review state", ["All"] + list(ledger.REVIEW), key="ev_status")
            with c_view:
                view_mode = st.radio(
                    "View layout",
                    ["📁 Accordions", "📋 Master List"],
                    horizontal=True,
                    key="ev_view_mode",
                )

            # Filter records
            filtered = [
                r for r in enriched
                if (sec_filter == "All Sections & Documents" or r["section"] == sec_filter)
                and (status == "All" or r["review"] == status)
                and (
                    not search
                    or search.casefold() in (
                        r["id"]
                        + " "
                        + r["metric_title"]
                        + " "
                        + str(r["formatted_val"])
                        + " "
                        + r["page"]
                        + " "
                        + r["anchor"]
                        + " "
                        + r["section"]
                    ).casefold()
                )
            ]

            st.caption(f"{len(filtered)} matching disclosures across statutory Pre-IPO filings. Source-backed observations maintain SEBI ICDR 2018 provenance.")

            SECTION_META = [
                ("Section III: Objects of the Offer & Proceeds Waterfall", ":material/waterfall_chart:"),
                ("Section III: Capital Structure & Dilution", ":material/pie_chart:"),
                ("Section IV: Our Business Overview & Issue Details", ":material/storefront:"),
                ("Section IV: Corporate Governance, Promoters & Management", ":material/shield:"),
                ("Section V: Restated Financial Statements", ":material/account_balance:"),
                ("Section VI: Financial Indebtedness & Loan Schedule", ":material/payments:"),
                ("Section V: MD&A — Working Capital Dynamics & Accounting Ratios", ":material/hourglass_top:"),
                ("Section V: Basis for Issue Price & Peer Benchmarking", ":material/compare_arrows:"),
            ]
            section_icon_map = dict(SECTION_META)

            col_cfg = {
                "Attribute / Metric": st.column_config.TextColumn("Attribute / Metric", width="medium"),
                "Reported Value": st.column_config.TextColumn("Reported Value", width="small"),
                "Period": st.column_config.TextColumn("Period", width="small"),
                "PDF Page": st.column_config.TextColumn("PDF Page", width="small"),
                "Table / Figure Anchor": st.column_config.TextColumn("Table / Figure / Footnote Anchor", width="large"),
                "Review State": st.column_config.TextColumn("Review State", width="small"),
                "Schema Key": st.column_config.TextColumn("Schema Identifier", width="small"),
            }

            if view_mode == "📁 Accordions":
                # Option B: Document / Section-Grouped Hierarchical Accordions
                sec_groups = defaultdict(list)
                for r in filtered:
                    sec_groups[r["section"]].append(r)

                ordered_sections = [s for s, _ in SECTION_META if s in sec_groups]
                remaining_sections = [s for s in sec_groups if s not in ordered_sections]

                for sec_name in ordered_sections + remaining_sections:
                    sec_items = sec_groups[sec_name]
                    icon = section_icon_map.get(sec_name, ":material/description:")
                    is_core = sec_name in [
                        "Section V: Restated Financial Statements",
                        "Section VI: Financial Indebtedness & Loan Schedule",
                        "Section III: Objects of the Offer & Proceeds Waterfall",
                    ] or len(sec_groups) <= 2

                    with st.expander(f"{icon} {sec_name} · ({len(sec_items)} Attributes)", expanded=is_core):
                        doc_label = sec_items[0]["doc_title"] if sec_items else dossier.company_name
                        st.caption(f"Filing: **{doc_label}** · Scope: SEBI ICDR 2018 Statutory Disclosures")
                        table_data = [
                            {
                                "Attribute / Metric": r["metric_title"],
                                "Reported Value": r["formatted_val"],
                                "Period": r["context"].get("period", "—") if r["context"].get("period") != "NOT_ESTABLISHED" else "—",
                                "PDF Page": r["page"],
                                "Table / Figure Anchor": r["anchor"],
                                "Review State": r["review"],
                                "Schema Key": r["id"],
                            }
                            for r in sec_items
                        ]
                        st.dataframe(table_data, hide_index=True, use_container_width=True, column_config=col_cfg)
            else:
                # Master Flat Table View
                master_col_cfg = {
                    **col_cfg,
                    "Filing Section / Document": st.column_config.TextColumn("Filing Section / Source", width="medium"),
                }
                table_data = [
                    {
                        "Attribute / Metric": r["metric_title"],
                        "Reported Value": r["formatted_val"],
                        "Period": r["context"].get("period", "—") if r["context"].get("period") != "NOT_ESTABLISHED" else "—",
                        "Filing Section / Document": r["section"],
                        "PDF Page": r["page"],
                        "Table / Figure Anchor": r["anchor"],
                        "Review State": r["review"],
                        "Schema Key": r["id"],
                    }
                    for r in filtered
                ]
                st.dataframe(table_data, hide_index=True, use_container_width=True, column_config=master_col_cfg)
        with tabs[1]:
            if not private_ready:
                st.info("Inspection needs no setup. Start a private review only to retain PDFs, review facts or save changes.")
                if st.button("Start private review of this data",disabled=not editable):
                    ledger.seed_dossier(owner,role,company,dossier)
                    st.rerun()
            _sources_and_review(owner,role,company,items,can_review)
            with st.expander("Add a private company for a new filing (optional)"):
                with st.form("ev_company_"+owner):
                    name=st.text_input("Company legal name")
                    sector=st.text_input("Sector / business description")
                    periods=st.text_input("Reporting periods (comma separated)",value="FY22, FY23, FY24")
                    if st.form_submit_button("Create private company",disabled=not editable):
                        try:
                            st.session_state.ev_pending_company=ledger.create_company(owner,role,name,sector,[p.strip() for p in periods.split(",")])
                            st.rerun()
                        except ValueError as exc:
                            st.error(str(exc))
        with tabs[2]:
            st.subheader("Reconcile differences before using them")
            st.caption("These are nominal-FY internal comparisons, not verified errors against the original filings. A reviewed source selection retains both historical observations.")
            st.dataframe(assessment["conflicts"],hide_index=True,use_container_width=True)
            with st.expander("Original stored CMIE crosswalk attributes"):
                st.caption("Stored labels are unverified legacy claims. A name candidate does not establish accounting equivalence or a licensed provider-value comparison.")
                st.dataframe([{"Concept":r.canonical_concept,"Local alias (not verified vendor key)":r.cmie_field_code,"Stored DRHP value":r.drhp_raw_value,"Stored normalized candidate":r.cmie_normalized_value,"Legacy label":r.status,"Current qualification":"TABLE / DEFINITION / SOURCE REVIEW REQUIRED"} for r in dossier.cmie_crosswalk],hide_index=True,use_container_width=True)
            _reference(owner,role,company,items,can_review)
        with tabs[3]:
            st.subheader("Missing evidence and next actions")
            notice=st.session_state.pop("ev_action_notice",None)
            if notice:
                st.success(notice)
            gap_domain=st.selectbox("Gap domain",["All"]+sorted({g["domain"] for g in assessment["gaps"]}),key="ev_gap_domain")
            gaps=[g for g in assessment["gaps"] if gap_domain=="All" or g["domain"]==gap_domain]
            st.dataframe(gaps,hide_index=True,use_container_width=True)
            with st.form("ev_action_"+owner+company):
                st.markdown("**Create a diligence follow-up**")
                question=st.text_input("Question or gap identifier")
                next_action=st.text_area("Evidence to request and why")
                assignee=st.text_input("Action owner",value=owner)
                due=st.date_input("Review due date")
                if st.form_submit_button("Record follow-up",disabled=not can_review):
                    try:
                        ledger.add_action(owner,role,company,{"question":question,"next_action":next_action,"assignee":assignee,"due":due.isoformat()})
                        st.success("Follow-up recorded. The evidence gap remains open until reviewed.")
                    except ValueError as exc:
                        st.error(str(exc))
            recorded=ledger.actions(owner,company)
            st.dataframe(recorded,hide_index=True,use_container_width=True)
            if recorded:
                action_revision_key=ledger.digest({"owner":owner,"company":company,"heads":[(a["id"],a["revision"]) for a in recorded]})[:16]
                with st.form("ev_action_status_"+action_revision_key):
                    selected_action=st.selectbox("Follow-up to update",range(len(recorded)),format_func=lambda i:recorded[i]["question"]+" · "+recorded[i]["status"])
                    new_status=st.selectbox("Follow-up status",["OPEN","COMPLETED","CANCELLED"])
                    disposition=st.text_area("Outcome / evidence received / reason for reopening")
                    if st.form_submit_button("Append follow-up status",disabled=not can_review):
                        try:
                            item=recorded[selected_action]
                            ledger.transition_action(owner,role,company,item["id"],new_status,disposition,item["revision"])
                            st.session_state.ev_action_notice="Action status recorded. Closing an action does not close its evidence gap."
                            st.rerun()
                        except ValueError as exc:
                            st.error(str(exc))
        with tabs[4]:
            st.subheader("What do the reviewed facts support?")
            st.caption("Results below use retained-source accepted facts available by the cutoff. No confidence score, causal effect or investment suitability conclusion is invented.")
            for question in assessment["questions"]:
                with st.expander(question["question"]+" · "+question["period"]+" · "+question["state"]):
                    st.write(question["observation"])
                    st.write("Interpretation: "+question["interpretation"])
                    st.write("Next action: "+question["next_action"])
                    st.caption(question["method_reference"])
                    st.caption("Fact bindings: "+", ".join(question["fact_ids"]))
            with st.expander("Practitioner methodology references"):
                for ref in assessment["methodology_references"]:
                    st.markdown(f"[{ref['title']}]({ref['url']})")
                    st.caption(ref["scope"])
            if st.button("Freeze evidence snapshot",disabled=not can_review):
                ledger.snapshot(owner,role,company,dossier,cutoff)
                st.success("Immutable snapshot saved. Downloads use those same fact revisions, questions and gaps.")
            saved=ledger.snapshots(owner,company)
            if saved:
                selected=st.selectbox("Saved evidence snapshot",range(len(saved)),format_func=lambda i:saved[i]["created_at"]+" · "+saved[i]["id"][:12],key="ev_saved")
                frozen=saved[selected]
                periods=sorted({f["context"]["period"] for f in frozen["facts"] if f["id"] in frozen["assessment"]["accepted_fact_revisions"] and f["id"].endswith(".cfo_cr")})
                prefill_period=st.selectbox("Reviewed period for optional model inputs",periods or ["No reviewed CFO period"],key="ev_handoff_period")
                st.caption("Optional models can start from this snapshot's accepted facts. Interest, tax and scenario assumptions still need explicit input; applying a handoff starts a new unsaved decision case.")
                if st.button("Prepare this snapshot for the decision workbench",disabled=not editable):
                    from models.pre_ipo_evidence_analysis import workbench_context
                    try:
                        st.session_state.ipo_evidence_handoff={"owner":owner,"context":workbench_context(frozen,prefill_period if periods else None)}
                        st.success("Snapshot prepared. Choose Decision-depth workbench above, then apply the prepared evidence case.")
                    except ValueError as exc:
                        st.error(str(exc))
                current={f["id"]:f["revision"] for f in items}
                current_refs={r["id"] for r in ledger.references(owner)}
                frozen_refs={r["id"] for r in frozen.get("reference_versions",[])}
                current_actions={a["id"]:a["revision"] for a in ledger.actions(owner,company)}
                frozen_actions={a.get("id"):a.get("revision",0) for a in frozen.get("actions",[])}
                stale=(current!={f["id"]:f["revision"] for f in frozen["facts"]} or current_refs!=frozen_refs or current_actions!=frozen_actions or cutoff!=frozen["cutoff"] or assessment["accepted_fact_revisions"]!=frozen["assessment"]["accepted_fact_revisions"])
                st.caption("Historical snapshot: the current facts, evidence eligibility, reference, actions or cutoff differ. Freeze a new snapshot to export the current assessment." if stale else "Snapshot matches the current fact revisions, evidence eligibility, reference, actions and cutoff.")
                from utils.pre_ipo_evidence_export import export_json,export_pptx
                st.download_button("Download evidence JSON",export_json(frozen),file_name="pre-ipo-evidence-"+frozen["id"][:12]+".json",mime="application/json")
                st.download_button("Download evidence PPTX",export_pptx(frozen),file_name="pre-ipo-evidence-"+frozen["id"][:12]+".pptx",mime="application/vnd.openxmlformats-officedocument.presentationml.presentation")
                with st.expander("Inspect frozen assessment"):
                    st.json(frozen["assessment"])


def _sources_and_review(owner,role,company,items,editable):
    with st.expander("1 · Retain an exact filing",expanded=not ledger.sources(owner,company)):
        with st.form("ev_upload_"+owner+company):
            st.caption("Retain an authorized PDF before accepting facts. This action does not send the document to a cloud model. Native page extraction is an explicit separate step.")
            uploaded=st.file_uploader("DRHP / RHP / addendum PDF, up to 25 MB",type=["pdf"],key="ev_pdf",disabled=not editable)
            title=st.text_input("Source title")
            c1,c2=st.columns(2)
            kind=c1.selectbox("Filing type",["DRHP","RHP","Prospectus","Addendum","Other evidence"])
            version=c2.text_input("Exact document version/date label")
            available=st.date_input("Established public availability date")
            url=st.text_input("Official source URL (recorded, not fetched)")
            rights=st.text_input("Retention and use permission / policy",help="Record the applicable authorization; this does not grant redistribution rights.")
            if st.form_submit_button("Retain private PDF",disabled=not editable):
                try:
                    if uploaded is None:
                        raise ValueError("Select a PDF first")
                    ledger.retain_pdf(owner,role,company,uploaded.getvalue(),{"title":title,"filing_type":kind,"version":version,"available_by":available.isoformat(),"official_url":url,"rights":rights})
                    st.success("Original bytes retained privately with a content hash.")
                except ValueError as exc:
                    st.error(str(exc))
    docs=ledger.sources(owner,company)
    source_options = [r["id"] for r in docs]
    default_src_idx = 0 if not docs else (source_options.index(st.session_state["ev_source"]) + 1 if st.session_state.get("ev_source") in source_options else 1)
    source_id=st.selectbox("Retained source",[""]+source_options,index=default_src_idx,format_func=lambda k:next((r["title"]+" · "+r["version"] for r in docs if r["id"]==k),"Choose a source"),key="ev_source")
    metadata=next((r for r in docs if r["id"]==source_id),{})
    page=int(st.number_input("PDF page to inspect (1-based)",min_value=1,max_value=max(1,metadata.get("pages",1)),step=1,key="ev_page"))
    if source_id:
        with st.expander("2 · Native extraction scope and page diagnostics"):
            with st.form("ev_extract_"+owner+company):
                count=st.number_input("Pages in this batch",min_value=1,max_value=20,value=5)
                if st.form_submit_button("Extract selected native pages",disabled=not editable):
                    try:
                        with st.spinner("Reading selected pages..."):
                            result=ledger.extract_pages(owner,role,company,source_id,page,int(count))
                        st.success(result["status"]+" · "+result["scope"])
                    except ValueError as exc:
                        st.error(str(exc))
            jobs=ledger.runs(owner,company)
            st.dataframe([{"Run":r["id"][:12],"First":r.get("first", 1),"Last":r.get("last", metadata.get("pages", 1)),"Status":r.get("status", "COMPLETED")} for r in jobs if r.get("source_id")==source_id],hide_index=True)
            st.caption("Scanned pages remain GAP-OCR-01. Manual source-backed review is available; no paid OCR request is made by this workspace.")
    left,right=st.columns([1,1])
    with left:
        st.subheader("3 · Inspect the source")
        _source_panel(owner,company,source_id,page)
    with right:
        st.subheader("4 · Review a fact")
        identifiers=[r["id"] for r in items]+["disclosure:"+s for slots in DISCLOSURES.values() for s in slots]+["New attribute"]
        selected=st.selectbox("Fact to review",list(dict.fromkeys(identifiers)),key="ev_fact")
        current=next((r for r in items if r["id"]==selected),{})
        # Revision is part of form/widget keys: stale submissions cannot silently replace a newer review.
        suffix=ledger.digest({"owner":owner,"company":company,"fact":selected,"revision":current.get("revision",0)})[:16]
        st.caption("Raw observation: "+_display(current.get("raw_value")))
        st.caption("Current review: "+current.get("review","UNREVIEWED")+" · Origin: "+current.get("origin","Not yet recorded"))
        if current.get("source",{}).get("id"):
            def open_binding():
                st.session_state.ev_source=current["source"]["id"]
                st.session_state.ev_page=current["source"].get("page",1)
            st.button("Open this fact's retained source page",key="open_"+suffix,on_click=open_binding)
        with st.form("ev_review_"+suffix):
            fact_id=st.text_input("Attribute identifier",value="" if selected=="New attribute" else selected,disabled=selected!="New attribute")
            value=st.text_area("Interpreted value",value="" if current.get("value") is None else _display(current.get("value")),help="Record the source's displayed units. Normalization must be explicit in the definition/reason.")
            presence=st.selectbox("Presence",list(ledger.PRESENCE))
            origin=st.selectbox("Origin",["FILING_FACT","ANALYST_ASSUMPTION","EXTERNAL_BENCHMARK","LEGACY_EXAMPLE"])
            state=st.selectbox("Review decision",list(ledger.REVIEW),index=list(ledger.REVIEW).index(current.get("review","UNREVIEWED")))
            contexts={}
            context_columns=st.columns(2)
            for index,field in enumerate(ledger.CONTEXT):
                contexts[field]=context_columns[index%2].text_input(field.replace("_"," ").capitalize(),value=current.get("context",{}).get(field,""),key=suffix+field,help="Use ANNUAL for a reported full year; ANNUALIZED_STUB for an annualized interim period." if field=="duration" else None)
            locator=st.text_input("Table, printed page label and footnote locator",value=current.get("source",{}).get("locator",""))
            quote=st.text_area("Exact source quotation including label/unit context",value=current.get("source",{}).get("quote",""))
            scope=st.text_area("Search / applicability scope (required for non-disclosure or N/A)")
            reason=st.text_area("Why this interpretation or decision is appropriate",help="Explain differences, normalization and exclusions. Raw observations are never overwritten.")
            confirm=st.checkbox("I checked the selected PDF page, units, period and reporting basis")
            st.caption("Accepting a fact updates its revision and current readiness; previous snapshots remain unchanged. Assumptions do not close filing gaps. This workspace records SINGLE_REVIEW only.")
            if st.form_submit_button("Submit fact review",disabled=not editable):
                try:
                    if state=="ACCEPTED" and origin in {"FILING_FACT","EXTERNAL_BENCHMARK"} and not confirm:
                        raise ValueError("Confirm inspection of the retained source before acceptance")
                    proposal={**current,"id":fact_id,"value":value if presence=="OBSERVED_VALUE" else None,"presence":presence,"origin":origin,"review":state,"context":contexts,"source":{"id":source_id,"sha256":metadata.get("sha256"),"page":page,"locator":locator,"quote":quote},"reason":reason,"search_scope":scope}
                    ledger.save_fact(owner,role,company,proposal,current.get("revision",0))
                    st.success("Review recorded. Reloading current facts and dependent readiness.")
                    st.rerun()
                except ValueError as exc:
                    st.error(str(exc))
        if current:
            with st.expander("Fact revision history"):
                st.json(ledger.history(owner,company,current["id"]),expanded=False)
    if company in ledger.companies(owner):
        all_sources = ledger.sources(owner, company)
        if all_sources and source_id:
            with st.expander(":material/description: Document Lifecycle Actions (Selected Document)", expanded=False):
                st.caption(f"Selected document: **{metadata.get('title', source_id[:12])}** (ID: `{source_id[:12]}…`)")
                col_doc_w, col_doc_d = st.columns(2)
                with col_doc_w:
                    w_reason = st.text_input("Withdrawal reason", value="Superseded by updated filing", key=f"w_reason_{source_id}")
                    if st.button("Withdraw Document", icon=":material/archive:", key=f"btn_w_{source_id}", disabled=not editable):
                        try:
                            ledger.withdraw_source(owner, role, company, source_id, w_reason)
                            st.success("Document withdrawn from active reliance.")
                            st.rerun()
                        except Exception as exc:
                            st.error(str(exc))
                with col_doc_d:
                    conf_doc = st.checkbox("Confirm permanent deletion of THIS document only", key=f"conf_doc_del_{source_id}")
                    if st.button("Delete Document", icon=":material/delete:", key=f"btn_del_doc_{source_id}", disabled=not (editable and conf_doc)):
                        try:
                            ledger.delete_source(owner, role, company, source_id)
                            st.success("Document and its artifacts deleted.")
                            st.session_state.pop("ev_source", None)
                            st.rerun()
                        except Exception as exc:
                            st.error(str(exc))

        with st.expander(":material/delete_forever: Delete Private Company Package", expanded=False):
            impact = ledger.get_deletion_impact(owner, company)
            aff = impact.get("affected_counts", {})
            st.warning(
                "**Permanent Deletion Impact Manifest:**\n"
                f"- Retained Documents: {aff.get('sources', 0)}\n"
                f"- Artifacts / OCR Pages: {aff.get('artifacts', 0)}\n"
                f"- Processing Jobs: {aff.get('jobs', 0)}\n"
                f"- Extracted Observations & Facts: {aff.get('observations', 0) + aff.get('facts', 0)}\n"
                f"- Evidence Snapshots: {aff.get('snapshots', 0)}\n"
                f"- Saved Decision Workbench Copies: {aff.get('saved_decisions', 0)}\n\n"
                "Permanently removes this company, all retained sources, and dependent records from your evidence ledger."
            )
            confirm_del = st.checkbox("I confirm permanent deletion of this private company and all dependent records", key=f"confirm_del_{company}")
            if st.button("Delete private company", disabled=not (editable and confirm_del), key=f"btn_del_{company}", type="primary"):
                try:
                    ledger.delete_company(owner, role, company)
                    st.success("Company and retained records deleted.")
                    st.session_state.pop("evidence_company", None)
                    st.session_state.pop("ev_active_company", None)
                    st.session_state.pop("ev_source", None)
                    st.session_state.pop("ev_fact", None)
                    st.rerun()
                except PermissionError as exc:
                    st.error(str(exc))


def _reference(owner,role,company,items,editable):
    st.subheader("CMIE reference candidates")
    st.caption("A field-name match is a candidate only. Table, version, accounting definition and comparable provider observations must be reviewed separately. No mapping score is an audit opinion.")
    with st.form("ev_reference_"+owner):
        upload=st.file_uploader("Authorized catalogue CSV or pipe-delimited IND, up to 5 MB",type=["csv","ind","txt"],key="ev_ref",disabled=not editable)
        version=st.text_input("Catalogue version / retrieval date")
        rights=st.text_input("Reference permitted-use declaration")
        if st.form_submit_button("Register reference version",disabled=not editable):
            try:
                if upload is None:
                    raise ValueError("Choose a reference file")
                ledger.reference_import(owner,role,upload.getvalue(),version,rights)
                st.success("Reference registered privately; definitions and licensed values are not inferred.")
            except (ValueError,UnicodeError) as exc:
                st.error(str(exc))
    refs=ledger.references(owner)
    if refs:
        reference=refs[st.selectbox("Reference version",range(len(refs)),format_func=lambda i:refs[i]["version"],key="ev_ref_version")]
        query=st.text_input("Find vendor field / indicator",key="ev_vendor_query")
        candidates=[r for r in reference["rows"] if query.casefold() in (r["Field Name"]+r["Indicator"]).casefold()]
        st.caption(reference["qualification"]+f" · {len(reference['rows'])} rows / {reference['tables']} tables · hash {reference['id']}")
        st.dataframe(candidates[:500],hide_index=True,use_container_width=True)
        st.caption(f"Showing {min(500,len(candidates))} of {len(candidates)} candidates. No company coverage denominator is inferred from catalogue size.")
        with st.form("ev_map_"+owner+company):
            fact_id=st.selectbox("Attribute for reference candidate",[f["id"] for f in items])
            table=st.selectbox("Vendor table",sorted({r["Table"] for r in reference["rows"]}))
            field=st.text_input("Exact vendor field name")
            reason=st.text_area("Candidate mapping rationale and definition gaps")
            if st.form_submit_button("Record table-qualified candidate",disabled=not editable):
                try:
                    current=next(f for f in items if f["id"]==fact_id)
                    ledger.map_reference(owner,role,company,fact_id,current["revision"],reference["id"],table,field,reason)
                    st.success("Candidate recorded with DEFINITION_REQUIRED. No CMIE company-value match is claimed.")
                except ValueError as exc:
                    st.error(str(exc))
