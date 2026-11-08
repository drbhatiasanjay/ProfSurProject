"""Evidence-qualified descriptive questions, gaps and reproducible commentary."""
from decimal import Decimal
import re
from models import pre_ipo_evidence as ledger

PROFILE_VERSION = "ipo-diligence-1"
# Required disclosure slots, not every field in the CMIE catalogue.
DISCLOSURES = {
    "Identity and business": ("Legal identity and reporting perimeter", "Business model and operating segments", "Customers, concentration and competition", "Sector operating KPI definitions"),
    "Offer and ownership": ("Primary issue, OFS and fee bridge", "Proceeds uses and execution milestones", "Diluted share count and investor rights", "Lock-in terms and source dates"),
    "Governance and legal": ("Auditor qualifications and changes", "Related parties and promoter interests", "Material litigation and contingencies", "Sector approvals and material sustainability obligations"),
    "Debt and obligations": ("Maturity, security and covenants", "Rate, currency and lease definitions"),
    "Valuation and peers": ("Dated comparable peer definitions", "Enterprise to diluted equity value bridge", "Forecast assumptions and thesis falsifiers"),
}
METHODS = {
    "Cash conversion": ("cfo_cr", "ebitda_cr"),
    "Free cash flow bridge": ("cfo_cr", "capex_cr"),
    "Asset return": ("pat_cr", "total_assets_cr"),
    "Revenue trend": ("revenue_ops_cr",),
}
METHOD_REFERENCES=[
    {"id":"CFA-FCF","title":"CFA Institute · Free Cash Flow Valuation (2026)","url":"https://www.cfainstitute.org/insights/professional-learning/refresher-readings/2026/free-cash-flow-valuation","scope":"FCFF/FCFE definitions and valuation context; not issuer-specific evidence or validation of this app."},
    {"id":"DAMODARAN-DCF","title":"Damodaran · DCF Problems and Solutions","url":"https://pages.stern.nyu.edu/~adamodar/New_Home_Page/problems/dcfprob.htm","scope":"Consistency of cash flows, discount rates and assumptions; teaching reference, not an issuer finding."},
]


def _compatible(rows):
    fields=("entity","period","duration","basis","framework","currency","unit")
    return len({tuple(r["context"].get(k) for k in fields) for r in rows})==1


def assess(owner,company,dossier,cutoff):
    all_facts=ledger.facts(owner,company)
    accepted=ledger.valid_facts(owner,company,cutoff)
    def correct_slot(item):
        if item.get("context",{}).get("entity")!=dossier.company_name:
            return False
        match=re.match(r"history\[(\d+)\]",item["id"])
        return not match or int(match[1])<len(dossier.history) and item["context"].get("period")==dossier.history[int(match[1])].fiscal_year
    accepted=[item for item in accepted if correct_slot(item)]
    by_id={f["id"]:f for f in all_facts}
    valid={f["id"]:f for f in accepted}
    required=[]
    gaps=[]
    for index,year in enumerate(dossier.history):
        for field in ("revenue_ops_cr","ebitda_cr","pat_cr","cfo_cr","cfi_cr","cff_cr","capex_cr","fcf_cr","net_worth_cr","total_assets_cr","receivables_cr","gross_margin_pct"):
            key=f"history[{index}].{field}"
            required.append(key)
            item=by_id.get(key)
            if key not in valid:
                reason=item.get("presence","NOT_SEARCHED") if item and item.get("presence")!="OBSERVED_VALUE" else "SOURCE_REVIEW_REQUIRED" if item else "NOT_SEARCHED"
                gaps.append({"fact_id":key,"domain":"Financial performance","period":year.fiscal_year,"reason":reason,"next_action":"Retain exact filing; locate field, definition, period and unit; submit a source-backed review.","criticality":"MATERIAL","affected_questions":[name for name,fields in METHODS.items() if field in fields]})
    for group,slots in DISCLOSURES.items():
        for label in slots:
            key="disclosure:"+label
            required.append(key)
            if key not in valid:
                gaps.append({"fact_id":key,"domain":group,"period":"Filing-specific","reason":"SOURCE_REVIEW_REQUIRED","next_action":"Locate and review this disclosure or document its non-applicability and search scope.","criticality":"MATERIAL","affected_questions":[label]})
    # Reviewed N/A requires a retained source binding and an explicit applicability scope.
    not_applicable=[]
    for item in all_facts:
        if item["id"] in required and item.get("review")=="ACCEPTED" and item.get("presence")=="NOT_APPLICABLE_CLAIMED" and item.get("search_scope") and item.get("origin")=="FILING_FACT":
            try:
                metadata,_=ledger.source(owner,company,item.get("source",{}).get("id",""))
                if metadata["available_by"]<=cutoff:
                    not_applicable.append(item["id"])
            except ValueError:
                pass
    gaps=[g for g in gaps if g["fact_id"] not in not_applicable]
    applicable=[k for k in required if k not in not_applicable]
    methods=[]
    for index,year in enumerate(dossier.history):
        for name,fields in METHODS.items():
            ids=[f"history[{index}].{field}" for field in fields]
            items=[valid[k] for k in ids if k in valid]
            result={"question":name,"period":year.fiscal_year,"state":"BLOCKED_EVIDENCE","fact_ids":ids,"missing":[k for k in ids if k not in valid],"observation":"No source-qualified result until required facts are reviewed.","interpretation":"Stored examples and mapping statuses do not establish accepted evidence.","next_action":"Resolve the listed facts in Source review.","method_reference":"Descriptive calculation, not an econometric or causal estimate."}
            context_matches_period=all(r.get("context",{}).get("period")==year.fiscal_year for r in items)
            if len(items)==len(ids) and _compatible(items) and context_matches_period:
                try:
                    values=[ledger.numeric(r["value"]) for r in items]
                    result.update(state="READY_SINGLE_REVIEW",missing=[],review_qualification="Single reviewer; no independent audit opinion")
                    if name=="Cash conversion":
                        if values[1]<=0:
                            result.update(state="NOT_MEANINGFUL",observation="EBITDA is zero or negative; CFO/EBITDA is not presented as a quality score.")
                        else:
                            result["value"]=str(values[0]/values[1]*100)
                            result["unit"]="percent"
                            result["observation"]=f"CFO / EBITDA is {values[0]/values[1]*100:.2f}% for the reviewed period."
                        result["interpretation"]="Conversion reflects the reviewed CFO and EBITDA definitions; timing, tax/interest classification and working capital can change the ratio. It does not establish debt capacity."
                        result["next_action"]="Inspect working-capital movements and cash-flow classification before attributing the change to business quality."
                    elif name=="Free cash flow bridge":
                        result["value"]=str(values[0]-values[1]); result["unit"]=items[0]["context"]["unit"]
                        result["observation"]=f"Derived CFO minus capex is {values[0]-values[1]}; no separate reported FCF is assumed."
                        result["interpretation"]="This is a simple CFO-minus-capex bridge, not automatically FCFF or FCFE."
                        result["next_action"]="Reconcile cash/noncash capex and interest treatment before valuation."
                        reported=valid.get(f"history[{index}].fcf_cr")
                        if reported and _compatible(items+[reported]) and abs(values[0]-values[1]-ledger.numeric(reported["value"]))>Decimal("0.02"):
                            result.update(state="RECONCILIATION_REQUIRED",next_action="Resolve the reported FCF definition/bridge before using it in valuation.")
                        if values[1]<0:
                            result.pop("value",None)
                            result.update(state="DEFINITION_REVIEW_REQUIRED",observation="Negative capex requires a documented cash-outflow sign bridge before CFO-minus-capex is calculated.",next_action="Review and normalize the capex sign convention without changing the raw observation.")
                    elif name=="Asset return":
                        result.update(state="INSUFFICIENT_DATA",observation="Closing assets alone do not establish average assets for a return measure.",next_action="Review beginning and ending comparable assets and the return definition.")
                    else:
                        result["value"]=str(values[0]); result["unit"]=items[0]["context"]["unit"]
                        result["observation"]=f"Reviewed revenue is {values[0]} ({items[0]['context']['unit']})."
                        result["interpretation"]="An isolated level is not a growth estimate; comparable reporting duration and perimeter are required."
                        result["next_action"]="Review another comparable annual period; keep annualized stubs separate."
                    if items[0]["context"]["duration"]!="ANNUAL":
                        result["interpretation"]+=" This observation is not a reported annual period."
                except ValueError:
                    result.update(state="INVALID_NUMERIC_VALUE",next_action="Review the numeric interpretation and units.")
            elif len(items)==len(ids):
                result.update(state="NOT_COMPARABLE",next_action="Reconcile period, duration, basis, framework, currency and units.")
            methods.append(result)
    conflicts=[]
    for item in ledger.legacy_conflicts(dossier):
        chosen=valid.get(item["fact_id"])
        conflicts.append({**item,"disposition":"SOURCE_SELECTION_REVIEWED" if chosen else "UNRESOLVED", "selected_revision":chosen["revision"] if chosen else None})
    for group,slots in DISCLOSURES.items():
        ids=["disclosure:"+label for label in slots]
        supported=[valid[k] for k in ids if k in valid]
        methods.append({"question":group+" · disclosure assessment","period":"Filing-specific","state":"DISCLOSURES_REVIEWED" if len(supported)==len(ids) else "BLOCKED_EVIDENCE","fact_ids":ids,"missing":[k for k in ids if k not in valid],"observation":" | ".join(str(f["value"]) for f in supported) or "No accepted source-backed disclosures for this domain.","interpretation":"These are attributed disclosures reviewed by one user, not independently corroborated conclusions or an empirical estimate.","next_action":"Review the remaining disclosures, contradictory evidence and decision implications; record a diligence action.","method_reference":"Issuer-specific facts are bound to retained source pages; methodology references cannot substitute for missing disclosures."})
    for name,why in (("Panel regression","Independent entity/time variation and an identification design are not established by the issuer dossier."),("Predictive ML","A labelled target, leakage-safe validation split and sufficient independent training observations are not established."),("Private terms waterfall","Actual preference, participation, seniority and conversion terms must be reviewed; no default contract is assumed."),("Live exchange monitoring","No live-feed acceptance is implied by retained documents or local exchange examples.")):
        methods.append({"question":name,"period":"Not established","state":"DESIGN_REVIEW_REQUIRED","fact_ids":[],"missing":[],"observation":why,"interpretation":"Existing tools remain available in their original modules; availability is not evidence of applicability.","next_action":"Provide the required data and review the method design before running.","method_reference":"Method eligibility gate; no empirical result generated."})
    denominator=len(applicable)
    return {"profile_version":PROFILE_VERSION,"cutoff":cutoff,"required_slots":len(required),"applicable_slots":denominator,"not_applicable_reviewed":not_applicable,"accepted_required_slots":sum(k in valid for k in applicable),"accepted_coverage_pct":round(100*sum(k in valid for k in applicable)/denominator,1) if denominator else None,"qualification":"Source-bound single-review coverage, not extraction accuracy or an audit opinion.","gaps":gaps,"conflicts":conflicts,"questions":methods,"methodology_references":METHOD_REFERENCES,"accepted_fact_revisions":{f["id"]:f["revision"] for f in accepted}}


def workbench_context(snapshot,period=None):
    """Carry the frozen accepted facts into existing optional-model forms once."""
    from models.pre_ipo_decision.service import template
    context=template()
    accepted=snapshot["assessment"]["accepted_fact_revisions"]
    selected=[f for f in snapshot["facts"] if accepted.get(f["id"])==f["revision"]]
    contexts={(f["context"]["currency"],f["context"]["unit"]) for f in selected if f["id"].startswith("history") and f["id"].endswith("_cr") and (period is None or f["context"]["period"]==period)}
    if len(contexts)>1:
        raise ValueError("Use separate decision cases for incompatible currencies or monetary scales")
    currency,unit=next(iter(contexts),("INR","crore"))
    canonical_cid = snapshot.get("company") or snapshot.get("company_id")
    legal_name = snapshot.get("company_name") or canonical_cid
    context.update(
        company_id=canonical_cid,
        company=canonical_cid,
        company_name=legal_name,
        legal_name=legal_name,
        as_of=snapshot["cutoff"],
        currency=currency,
        unit=unit,
        background="Imported from frozen source-review snapshot "+snapshot["id"],
        snapshot_id=snapshot["id"],
        evidence_snapshot_id=snapshot["id"],
        source_review_qualification=snapshot["review_policy"]
    )
    context["extracted_attributes"]=[{"attribute_id":f["id"],"value":f["value"],"reviewed":True,"source_id":f["source"]["id"],"locator":f["source"]["locator"],"fact_revision":f["revision"],"context":f["context"]} for f in selected]
    context["evidence"]=[{"id":f["id"],"citation":f["source"]["id"],"locator":f"PDF {f['source']['page']}: {f['source']['locator']}","available_by":f["available_by"],"origin_id":f["origin_id"],"review_state":"accepted"} for f in selected]
    context["gaps"]=[{"attribute":g["fact_id"],"mandatory":True,"next_action":g["next_action"]} for g in snapshot["assessment"]["gaps"]]
    # CFO/capex can prefill the existing bridge, but interest/tax conventions remain required.
    cfo=[f for f in selected if f["id"].startswith("history[") and f["id"].endswith(".cfo_cr") and (period is None or f["context"]["period"]==period)]
    if len(cfo)>1:
        raise ValueError("Select one reporting period before prefilling optional model inputs")
    if cfo:
        latest=sorted(cfo,key=lambda f:int(re.search(r"history\[(\d+)\]",f["id"])[1]))[-1]
        model={"inputs":{"cfo":float(ledger.numeric(latest["value"]))},"evidence_ids":[latest["id"]]}
        capex=next((f for f in selected if f["id"]==latest["id"].replace(".cfo_cr",".capex_cr")),None)
        if capex and _compatible([latest,capex]):
            model["inputs"]["cash_capex"]=float(ledger.numeric(capex["value"]))
            model["evidence_ids"].append(capex["id"])
        context["models"]["cash_flow_bridge"]=model
        context["model_fact_bindings"]={"cash_flow_bridge":{"snapshot_id":snapshot["id"],"context":latest["context"],"fact_ids":model["evidence_ids"]}}
    return context
