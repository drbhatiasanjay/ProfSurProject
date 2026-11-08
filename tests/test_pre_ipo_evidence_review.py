"""Adversarial contracts for retained-source review, isolation and frozen exports."""
import copy
import io
import json
import sqlite3
import pytest
from pypdf import PdfWriter
from pptx import Presentation
from models import pre_ipo_evidence as e
from models.pre_ipo_evidence_analysis import assess
from models.pre_ipo_data import PRE_IPO_REGISTRY
from utils.pre_ipo_evidence_export import export_json,export_pptx


@pytest.fixture
def evidence_db(tmp_path,monkeypatch):
    import db
    path=tmp_path/"evidence.db"
    monkeypatch.setattr(db,"get_connection",lambda:sqlite3.connect(path,timeout=2))
    return path


def pdf():
    writer=PdfWriter(); writer.add_blank_page(width=612,height=792)
    stream=io.BytesIO(); writer.write(stream)
    return stream.getvalue()


def source():
    key=e.retain_pdf("analyst","researcher","afcons_infra",pdf(),{"title":"Synthetic validation filing","filing_type":"RHP","version":"test-1","available_by":"2024-01-01","rights":"Synthetic test permission"})
    metadata,_=e.source("analyst","afcons_infra",key)
    return key,metadata


def fact(key,metadata,identifier="history[2].cfo_cr",value="100"):
    return {"id":identifier,"value":value,"presence":"OBSERVED_VALUE","origin":"FILING_FACT","review":"ACCEPTED","context":{"entity":"Afcons Infrastructure Limited","period":"FY24","duration":"ANNUAL","basis":"CONSOLIDATED","framework":"IND_AS","currency":"INR","unit":"crore","definition":identifier.rsplit(".",1)[-1]},"source":{"id":key,"sha256":metadata["sha256"],"page":1,"locator":"Table 1, unit header","quote":"Synthetic validation observation"},"reason":"Manually inspected synthetic source; not an actual issuer verification"}


def test_legacy_baseline_keeps_conflicts_and_missing(evidence_db):
    count=0
    for key,dossier in PRE_IPO_REGISTRY.items():
        e.seed_dossier("analyst","researcher",key,dossier)
        initial=e.facts("analyst",key)
        count+=len(initial)
        assert all(row["origin"]=="LEGACY_EXAMPLE" and row["review"]=="UNREVIEWED" for row in initial)
        assert not e.valid_facts("analyst",key)
        e.seed_dossier("analyst","researcher",key,dossier)
        assert len(e.facts("analyst",key))==len(initial)
    assert count==2165
    differences=[row for d in PRE_IPO_REGISTRY.values() for row in e.legacy_conflicts(d)]
    assert len(differences)==24
    assert sum(r["state"]=="VALUE_ABSENT_IN_HISTORY" for r in differences)==5
    assert sum(r["state"]=="UNRESOLVED_INTERNAL_DIFFERENCE" for r in differences)==19


def test_existing_data_preview_requires_no_initialization_or_write(monkeypatch):
    def forbidden():
        raise AssertionError("Inspecting existing data must not open a ledger transaction")
    monkeypatch.setattr(e,"connection",forbidden)
    rows=e.preview_dossier(PRE_IPO_REGISTRY["mankind_pharma"])
    assert len(rows)==473
    assert next(r for r in rows if r["id"]=="history[0].revenue_ops_cr")["value"]==PRE_IPO_REGISTRY["mankind_pharma"].history[0].revenue_ops_cr
    assert all(r["review"]=="UNREVIEWED" and r["origin"]=="LEGACY_EXAMPLE" for r in rows)


def test_retain_owner_scope_role_and_integrity(evidence_db):
    key,meta=source()
    assert e.retain_pdf("analyst","researcher","afcons_infra",pdf(),{"title":"Synthetic validation filing","filing_type":"RHP","version":"test-1","available_by":"2024-01-01","rights":"Synthetic test permission"})==key
    assert e.sources("other","afcons_infra")==[]
    with pytest.raises(ValueError): e.source("other","afcons_infra",key)
    with pytest.raises(PermissionError): e.retain_pdf("viewer","viewer","a",pdf(),{})
    with pytest.raises(ValueError): e.retain_pdf("analyst","researcher","a",b"not a PDF",{})
    with sqlite3.connect(evidence_db) as conn:
        conn.execute("UPDATE pre_ipo_sources SET content=?",(b"changed",))
    with pytest.raises(ValueError,match="hash mismatch"): e.source("analyst","afcons_infra",key)


def test_review_requires_real_source_context_and_revision(evidence_db):
    key,meta=source()
    candidate=fact(key,meta)
    missing=copy.deepcopy(candidate); missing["source"]["id"]="invented"
    with pytest.raises(ValueError,match="Retained owned"): e.save_fact("analyst","researcher","afcons_infra",missing)
    missing=copy.deepcopy(candidate); missing["context"]["basis"]="NOT_ESTABLISHED"
    with pytest.raises(ValueError,match="semantic context"): e.save_fact("analyst","researcher","afcons_infra",missing)
    missing=copy.deepcopy(candidate); missing["source"]["page"]=2
    with pytest.raises(ValueError,match="page number"): e.save_fact("analyst","researcher","afcons_infra",missing)
    saved=e.save_fact("analyst","researcher","afcons_infra",candidate)
    assert saved["review_qualification"]=="SINGLE_REVIEW"
    with pytest.raises(ValueError,match="changed"): e.save_fact("analyst","researcher","afcons_infra",candidate)
    candidate["value"]="120"
    saved=e.save_fact("analyst","researcher","afcons_infra",candidate,1)
    assert saved["raw_value"]=="100" and saved["value"]=="120"
    assert len(e.history("analyst","afcons_infra",candidate["id"]))==2
    assert not e.valid_facts("analyst","afcons_infra","2023-12-31")
    assert len(e.valid_facts("analyst","afcons_infra","2024-01-01"))==1


def test_nil_zero_assumption_and_legacy_are_distinct(evidence_db):
    key,meta=source()
    candidate=fact(key,meta,value="0")
    e.save_fact("analyst","researcher","afcons_infra",candidate)
    assert e.valid_facts("analyst","afcons_infra")[0]["value"]=="0"
    candidate.update(id="assumption",origin="ANALYST_ASSUMPTION",value="200")
    e.save_fact("analyst","researcher","afcons_infra",candidate)
    assert len(e.valid_facts("analyst","afcons_infra"))==1
    candidate.update(id="legacy",origin="LEGACY_EXAMPLE")
    with pytest.raises(ValueError,match="Legacy examples"): e.save_fact("analyst","researcher","afcons_infra",candidate)
    candidate.update(id="nil",origin="FILING_FACT",presence="EXPLICIT_NIL",value="0")
    with pytest.raises(ValueError,match="Non-value presence"): e.save_fact("analyst","researcher","afcons_infra",candidate)
    candidate["value"]=None
    e.save_fact("analyst","researcher","afcons_infra",candidate)
    assert len(e.valid_facts("analyst","afcons_infra"))==1


def test_scanned_page_gap_explicit_scope_and_idempotency(evidence_db):
    key,meta=source()
    run=e.extract_pages("analyst","researcher","afcons_infra",key,1,1)
    assert run["pages"][0]["status"]=="GAP-OCR-01"
    assert run==e.extract_pages("analyst","researcher","afcons_infra",key,1,1)
    assert len(e.runs("analyst","afcons_infra"))==1
    assert not e.valid_facts("analyst","afcons_infra")
    with pytest.raises(ValueError): e.extract_pages("analyst","researcher","afcons_infra",key,2,1)


def test_readiness_and_frozen_export_survive_new_revision(evidence_db):
    key,meta=source()
    dossier=PRE_IPO_REGISTRY["afcons_infra"]
    for name,value in (("cfo_cr","100"),("ebitda_cr","200")):
        e.save_fact("analyst","researcher","afcons_infra",fact(key,meta,"history[2]."+name,value))
    assessment=assess("analyst","afcons_infra",dossier,"2026-01-01")
    result=next(q for q in assessment["questions"] if q["question"]=="Cash conversion" and q["period"]=="FY24")
    assert result["state"]=="READY_SINGLE_REVIEW" and result["value"]=="50.0"
    frozen=e.snapshot("analyst","researcher","afcons_infra",dossier,"2026-01-01")
    new=fact(key,meta,value="120")
    e.save_fact("analyst","researcher","afcons_infra",new,1)
    assert e.snapshots("analyst","afcons_infra")[0]==frozen
    assert json.loads(export_json(frozen))["id"]==frozen["id"]
    deck=Presentation(io.BytesIO(export_pptx(frozen)))
    text="\n".join(shape.text for slide in deck.slides for shape in slide.shapes if shape.has_text_frame)
    assert frozen["id"] in text and "50.00%" in text
    assert any("SOURCE_REVIEW_REQUIRED" in g["reason"] for g in frozen["assessment"]["gaps"])
    assert not e.snapshots("other","afcons_infra")


def test_semantic_context_scale_and_reference_ambiguity(evidence_db):
    assert e.normalize("1.25","10000000")=="12500000.00"
    with pytest.raises(ValueError): e.normalize("NaN")
    key,meta=source(); left=fact(key,meta); right=copy.deepcopy(left)
    right["context"]["basis"]="STANDALONE"
    assert e.compare(left,right)["state"]=="NOT_COMPARABLE"
    with pytest.raises(ValueError): e.compare(left,left,absolute="-1")
    content=b"Table|Field Name|Indicator\nstandalone|SALES|Sales\nconsolidated|SALES|Sales\n"
    e.reference_import("analyst","researcher",content,"test-v1","Internal metadata only")
    ref=e.references("analyst")[0]
    assert ref["tables"]==2 and len(ref["rows"])==2
    assert not e.references("other")
    with pytest.raises(ValueError): e.reference_import("analyst","researcher",content,"changed-version","Internal")


def test_viewer_write_denied_actions_deduplicated(evidence_db):
    key,meta=source()
    with pytest.raises(PermissionError): e.save_fact("analyst","viewer","afcons_infra",fact(key,meta))
    action={"question":"missing source","next_action":"Request exact RHP","assignee":"Research","due":"2027-01-01"}
    e.add_action("analyst","researcher","afcons_infra",action)
    e.add_action("analyst","researcher","afcons_infra",action)
    assert len(e.actions("analyst","afcons_infra"))==1


def test_private_company_no_invented_financial_values(evidence_db):
    company=e.create_company("analyst","researcher","Synthetic new issuer","Technology",["FY23","9M-FY24"])
    assert not e.companies("other")
    dossier=e.companies("analyst")[company]
    e.seed_dossier("analyst","researcher",company,dossier)
    rows=e.facts("analyst",company)
    financial=[r for r in rows if r["id"].startswith("history") and not r["id"].endswith("fiscal_year")]
    assert financial and all(r["value"] is None and r["presence"]=="NOT_SEARCHED" for r in financial)
    assert not e.valid_facts("analyst",company)
    assert not assess("analyst",company,dossier,"2026-01-01")["accepted_required_slots"]


def test_wrong_period_cannot_support_labelled_result(evidence_db):
    key,meta=source()
    for name in ("cfo_cr","ebitda_cr"):
        candidate=fact(key,meta,"history[2]."+name,"100")
        candidate["context"]["period"]="FY23"
        e.save_fact("analyst","researcher","afcons_infra",candidate)
    result=next(q for q in assess("analyst","afcons_infra",PRE_IPO_REGISTRY["afcons_infra"],"2026-01-01")["questions"] if q["question"]=="Cash conversion" and q["period"]=="FY24")
    assert result["state"]=="BLOCKED_EVIDENCE" and "value" not in result


def test_catalogue_mapping_stays_candidate_not_value_match(evidence_db):
    key,meta=source()
    e.save_fact("analyst","researcher","afcons_infra",fact(key,meta))
    reference=e.reference_import("analyst","researcher",b"Table|Field Name|Indicator\nconsolidated|CFO|Cash flow\n","test","Internal test metadata")
    updated=e.map_reference("analyst","researcher","afcons_infra","history[2].cfo_cr",1,reference,"consolidated","CFO","Definition and unit review still needed")
    assert updated["mapping"]["state"]=="DEFINITION_REQUIRED"
    with pytest.raises(ValueError): e.map_reference("analyst","researcher","afcons_infra","history[2].cfo_cr",2,reference,"wrong-table","CFO","Candidate")


def test_cutoff_excludes_future_source_from_snapshot(evidence_db):
    key,meta=source()
    e.save_fact("analyst","researcher","afcons_infra",fact(key,meta))
    frozen=e.snapshot("analyst","researcher","afcons_infra",PRE_IPO_REGISTRY["afcons_infra"],"2023-12-31")
    assert frozen["sources"]==[] and frozen["facts"]==[]
    assert not frozen["assessment"]["accepted_fact_revisions"]


def test_asof_recovers_earlier_source_revision_and_handoff_keeps_missing_inputs(evidence_db):
    from models.pre_ipo_evidence_analysis import workbench_context
    key,meta=source()
    e.save_fact("analyst","researcher","afcons_infra",fact(key,meta))
    newer=e.retain_pdf("analyst","researcher","afcons_infra",pdf(),{"title":"Synthetic addendum","filing_type":"Addendum","version":"test-2","available_by":"2025-01-01","rights":"Test only"})
    updated_meta,_=e.source("analyst","afcons_infra",newer)
    e.save_fact("analyst","researcher","afcons_infra",fact(newer,updated_meta,value="120"),1)
    old=e.valid_facts("analyst","afcons_infra","2024-12-31")
    assert old[0]["value"]=="100" and old[0]["revision"]==1
    frozen=e.snapshot("analyst","researcher","afcons_infra",PRE_IPO_REGISTRY["afcons_infra"],"2024-12-31")
    context=workbench_context(frozen)
    assert context["models"]["cash_flow_bridge"]["inputs"]=={"cfo":100.0}
    assert context["evidence_snapshot_id"]==frozen["id"]
    assert "cash_interest" not in context["models"]["cash_flow_bridge"]["inputs"]


def test_imported_intake_preserves_candidates_without_overwriting_history(evidence_db):
    dossier=copy.deepcopy(PRE_IPO_REGISTRY["afcons_infra"])
    metadata={"title":"Synthetic imported source","filing_type":"RHP","version":"one","available_by":"2024-01-01","rights":"Synthetic test"}
    company=e.import_dossier("analyst","researcher","Synthetic imported issuer",dossier,pdf(),metadata)
    count=len(e.facts("analyst",company))
    assert count and all(f["review"]=="UNREVIEWED" for f in e.facts("analyst",company))
    assert not e.valid_facts("analyst",company)
    e.import_dossier("analyst","researcher","Synthetic imported issuer",dossier,pdf(),metadata)
    assert len(e.history("analyst",company,"history[2].cfo_cr"))==1
    dossier.history[2].cfo_cr=999
    e.import_dossier("analyst","researcher","Synthetic imported issuer",dossier,pdf(),metadata)
    versions=e.history("analyst",company,"history[2].cfo_cr")
    assert len(versions)==2 and versions[0]["raw_value"]==versions[1]["raw_value"]
    assert versions[1]["extraction_raw_value"]==999


def test_concurrent_review_has_one_winner(evidence_db):
    from concurrent.futures import ThreadPoolExecutor
    key,meta=source()
    e.save_fact("analyst","researcher","afcons_infra",fact(key,meta))
    def attempt(value):
        try:
            e.save_fact("analyst","researcher","afcons_infra",fact(key,meta,value=value),1)
            return "saved"
        except ValueError:
            return "stale"
    with ThreadPoolExecutor(max_workers=2) as executor:
        assert sorted(executor.map(attempt,["110","120"]))==["saved","stale"]


def test_failed_intake_defaults_remain_failures(evidence_db):
    from models.pre_ipo_schema import DecisionLimitationItem
    dossier=copy.deepcopy(PRE_IPO_REGISTRY["afcons_infra"])
    dossier.limitations.append(DecisionLimitationItem("GAP-OCR-01","Scanned source","All","PARSE_FAILED","Unreadable source","All ratios","HIGH","Obtain OCR or manually review"))
    dossier.history[0].cfo_cr=0
    company=e.import_dossier("analyst","researcher","Synthetic failed intake",dossier,pdf(),{"title":"Failed intake original","filing_type":"DRHP","version":"one","available_by":"2024-01-01","rights":"Synthetic test"})
    item=next(f for f in e.facts("analyst",company) if f["id"]=="history[0].cfo_cr")
    assert item["raw_value"]==0 and item["value"] is None and item["presence"]=="EXTRACTION_FAILED"
    assert not e.valid_facts("analyst",company)


def test_typed_financial_value_and_negative_denominator(evidence_db):
    key,meta=source()
    for invalid in ("not a number","NaN","1e10000"):
        with pytest.raises(ValueError): e.save_fact("analyst","researcher","afcons_infra",fact(key,meta,value=invalid))
    for metric,value in (("cfo_cr","100"),("ebitda_cr","-200")):
        e.save_fact("analyst","researcher","afcons_infra",fact(key,meta,"history[2]."+metric,value))
    question=next(q for q in assess("analyst","afcons_infra",PRE_IPO_REGISTRY["afcons_infra"],"2026-01-01")["questions"] if q["question"]=="Cash conversion" and q["period"]=="FY24")
    assert question["state"]=="NOT_MEANINGFUL" and "value" not in question


def test_cash_bridge_needs_two_facts_and_checks_capex_sign(evidence_db):
    key,meta=source()
    for metric,value in (("cfo_cr","100"),("capex_cr","30")):
        e.save_fact("analyst","researcher","afcons_infra",fact(key,meta,"history[2]."+metric,value))
    def bridge():
        return next(q for q in assess("analyst","afcons_infra",PRE_IPO_REGISTRY["afcons_infra"],"2026-01-01")["questions"] if q["question"]=="Free cash flow bridge" and q["period"]=="FY24")
    assert bridge()["value"]=="70" and "Derived" in bridge()["observation"]
    e.save_fact("analyst","researcher","afcons_infra",fact(key,meta,"history[2].capex_cr","-30"),1)
    assert bridge()["state"]=="DEFINITION_REVIEW_REQUIRED" and "value" not in bridge()


def test_visual_page_renderer_does_not_silently_fallback():
    from utils.pre_ipo_evidence_export import render_page
    image=render_page(pdf(),1)
    assert image.width>0 and image.height>0 and image.width*image.height<=4_000_000


def test_handoff_requires_explicit_period_when_multiple_are_reviewed(evidence_db):
    from models.pre_ipo_evidence_analysis import workbench_context
    key,meta=source()
    for index,period,value in ((0,"FY22","80"),(2,"FY24","100")):
        candidate=fact(key,meta,f"history[{index}].cfo_cr",value)
        candidate["context"]["period"]=period
        e.save_fact("analyst","researcher","afcons_infra",candidate)
    frozen=e.snapshot("analyst","researcher","afcons_infra",PRE_IPO_REGISTRY["afcons_infra"],"2026-01-01")
    with pytest.raises(ValueError,match="reporting period"): workbench_context(frozen)
    context=workbench_context(frozen,"FY22")
    assert context["models"]["cash_flow_bridge"]["inputs"]["cfo"]==80
    assert context["model_fact_bindings"]["cash_flow_bridge"]["context"]["period"]=="FY22"


def test_action_lifecycle_is_append_only_and_snapshot_frozen(evidence_db):
    key=e.add_action("analyst","researcher","afcons_infra",{"question":"Review covenant source","next_action":"Obtain lender schedule","assignee":"Research","due":"2027-01-01"})
    frozen=e.snapshot("analyst","researcher","afcons_infra",PRE_IPO_REGISTRY["afcons_infra"],"2026-01-01")
    e.transition_action("analyst","researcher","afcons_infra",key,"COMPLETED","Schedule received; fact review remains separate",0)
    assert e.actions("analyst","afcons_infra")[0]["status"]=="COMPLETED"
    assert frozen["actions"][0]["status"]=="OPEN"
    with pytest.raises(ValueError,match="changed"): e.transition_action("analyst","researcher","afcons_infra",key,"OPEN","Reopen",0)
    with pytest.raises(ValueError,match="Owned"): e.transition_action("other","researcher","afcons_infra",key,"OPEN","Reopen",1)
    with pytest.raises(PermissionError): e.transition_action("analyst","viewer","afcons_infra",key,"OPEN","Reopen",1)
