import io
import json
import pytest
from pptx import Presentation
from models.pre_ipo_decision import financial as f, assessment as a, evidence as e, service
from models.pre_ipo_decision.contracts import affected_nodes
from utils.pre_ipo_decision_export import export_json, export_pptx

def case():
    value = service.template()
    value.update(company="Test issuer", currency="INR", unit="million")
    return value

def test_temporal_evidence_and_dependent_origins():
    records = [
        {"id":"old", "available_by":"2025-01-01", "origin_id":"filing"},
        {"id":"copy", "available_by":"2025-01-02", "origin_id":"filing"},
        {"id":"future", "available_by":"2027-01-01", "supersedes_id":"old"}]
    result = e.eligible_evidence(records, "2026-01-01")
    assert {x["id"] for x in result.data["eligible"]} == {"old", "copy"}
    assert len(result.data["origin_families"]) == 1
    assert not e.eligible_evidence(records, "2026-01-01", "decision_audit").data["eligible"]

def test_semantic_conflict_and_explicit_bridge():
    base = dict(metric="revenue",entity="A",period="2025",duration="annual",basis="consolidated",definition="net",unit="INR",lease="included",net=True,value=100)
    assert e.compare_facts(base, dict(base,value=101), .1).state == "DISPUTED"
    other = dict(base,basis="standalone",value=80)
    assert e.compare_facts(base,other,.1).state == "NOT_COMPARABLE"
    assert e.compare_facts(base,other,.1,bridge={"fields":["basis"],"adjustment":-20,"evidence_ids":["reconciliation"]}).state == "EXPLAINED_BRIDGE"

def test_unknown_thesis_and_graph_cycles():
    assert e.dependency_state({"all":["a","b"]},{"a":"SUPPORTED"}) == "INSUFFICIENT_EVIDENCE"
    assert e.dependency_state({"any":["a","b"]},{"a":"SUPPORTED"}) == "SUPPORTED"
    assert affected_nodes({"a"},{"b":["a"],"c":["b"]}) == ["a","b","c"]
    with pytest.raises(ValueError):
        affected_nodes({"a"},{"a":["b"],"b":["a"]})

def test_operating_capacity_cohort_and_tax():
    segment = dict(name="factory",quantity=10,capacity=9,net_price=2,unit_cost=1,fixed_cost=1)
    assert f.operating_model([segment]).state == "INFEASIBLE"
    segment["capacity"] = 10
    assert f.operating_model([segment],20).data["reconciliation_difference"] == 0
    assert f.cohort_retention(100,10,5,5,new_customers=50).data["nrr"] == 1
    assert f.cash_tax(-10,.25).data["cash_tax"] == 0
    assert f.cash_flow_bridge(100,20,10,2,cfo_includes_interest=True).data["fcff"] == 88
    assert f.cash_flow_bridge(100,20,10,2,cfo_includes_interest=False).data["fcff"] == 78
    with pytest.raises(ValueError):
        f.cohort_retention(100,0,70,40)

def test_interim_gap_and_ineligible_financing():
    events = [{"date":"2026-01-01","cash_capex":15},{"date":"2026-02-01","net_primary_equity":30}]
    result = f.cash_schedule(10,0,events)
    assert result.state == "FUNDING_GAP"
    assert result.data["closing_cash"] == 25
    assert f.cash_schedule(10,0,[{"date":"2026-01-01","draw":20}]).state == "INFEASIBLE"
    with pytest.raises(ValueError):
        f.cash_schedule(10,0,[{"date":"2026-01-01"},{"date":"2026-01-01"}])

def test_raise_cash_equity_conservation():
    result = f.ordinary_raise(100,90,10,.1)
    assert result.data["gross_raise"] == pytest.approx(100)
    assert result.data["net_receipts"] == pytest.approx(90)
    before = f.equity_bridge(200,80,10,primary_net=30)
    after = f.equity_bridge(200,80,10,primary_net=30,repayment=25)
    assert before.data["aggregate_equity_value"] == after.data["aggregate_equity_value"]
    assert f.equity_bridge(200,80,10,repayment=20).state == "INFEASIBLE"

def test_valuation_domain_and_solver_residual():
    assert f.terminal_cash(100,.03,.15).data["next_fcff"] == pytest.approx(80)
    assert f.terminal_cash(100,.2,.1).state == "INFEASIBLE"
    args = dict(cash_flows=[10],discount_rate=.1,terminal_next_cash=10,terminal_growth=.02,claim="FCFF",rate_claim="KE",currency="INR",rate_currency="INR",basis="nominal",rate_basis="nominal")
    assert f.discounted_value(**args).state == "UNSUPPORTED"
    assert f.bracketed_root(lambda x:x*x+1,-1,1).state == "UNBRACKETED"
    result = f.bracketed_root(lambda x:x*x-2,0,2)
    assert result.data["root"] == pytest.approx(2**.5,rel=1e-7)
    assert f.bracketed_root(lambda x: -1 if x < .5 else 1,0,1,max_iterations=20).state == "NOT_CONVERGED"
    assert f.reverse_dcf(10,150,.1,.02,-.5,1).state == "SOLVED_IN_BRACKET"

def test_stress_not_probability():
    result = f.reverse_stress([{"id":"a","shocks":{"sales":-.1},"cash_margin":-1,"economically_admissible":True},
                              {"id":"b","shocks":{"sales":-.01},"cash_margin":-1,"economically_admissible":False}],{"sales":.1})
    assert result.data["failure_paths"][0]["severity"] == pytest.approx(1)
    assert result.data["excluded"] == ["b"]

def test_information_value_and_diligence():
    result = a.information_value({"good":.5,"bad":.5},{"invest":{"good":100,"bad":-100},"wait":{"good":0,"bad":0}},
                                 {"yes":{"good":.5,"bad":0},"no":{"good":0,"bad":.5}},cost=10,delay_cost=5)
    assert result.data == {"baseline":0,"evpi":50,"evsi":50,"net_value":35}
    with pytest.raises(ValueError):
        a.information_value({"s":1},{"a":{"s":1}},{"x":{"s":.5}})
    assert a.diligence_priority([{"mandatory":True}]).data["gaps"][0]["priority"] == "BLOCKER"

def test_paired_opportunity_and_mature_commitment():
    opportunities = [{"id":"a","context":{"currency":"INR"},"scenarios":{"down":{"npv":5}}},
                     {"id":"b","context":{"currency":"INR"},"scenarios":{"down":{"npv":3}}}]
    assert a.compare_opportunities(opportunities,["currency"],{"npv":1}).data["comparisons"][0]["state"] == "A_DOMINATES"
    opportunities[1]["context"]["currency"] = "USD"
    assert a.compare_opportunities(opportunities,["currency"],{"npv":1}).state == "NOT_COMPARABLE"
    commitment = dict(id="promise",target=100,direction="at_least",deadline="2026-01-01",metric="revenue",period="FY25",basis="consolidated")
    assert a.evaluate_commitment(commitment,"2025-01-01").state == "NOT_DUE"
    assert a.evaluate_commitment(commitment,"2026-02-01").state == "PENDING_COMPARABLE_OBSERVATION"
    observation = dict(metric="revenue",period="FY25",basis="consolidated",available_by="2026-01-20",value=90)
    assert a.evaluate_commitment(commitment,"2026-02-01",observation).state == "MISSED"

def test_monitor_hysteresis_revision_dedup():
    assert a.monitor(None,10,12).state == "UNKNOWN"
    assert a.monitor({"id":"1","value":9},10,12).state == "BREACH"
    assert a.monitor({"id":"2","value":11},10,12,previous="BREACH").state == "BREACH"
    assert a.monitor({"id":"2","value":12},10,12,previous="BREACH").state == "RECOVERED"
    assert a.monitor({"id":"2","value":12},10,12,previous_event_id="2").state == "DUPLICATE"

def test_returns_waterfall_and_robustness():
    attribution = f.price_attribution(2,3,10,12)
    assert attribution.data["residual"] == pytest.approx(0)
    result = f.investor_returns([{"date":"2025-01-01","amount":-100},{"date":"2026-01-01","amount":110}],.1)
    assert result.state == "IRR_SOLVED"
    assert result.data["roots_found"][0] == pytest.approx(.1,abs=1e-6)
    classes=[dict(id="pref",shares=10,preference=80,seniority=1,conversion_election="prefer"),
             dict(id="common",shares=90,conversion_election="ordinary")]
    result=f.private_waterfall(100,classes,terms_verified=True)
    assert result.data["class_proceeds"] == {"pref":80,"common":20}
    assert result.data["conservation_residual"] == 0
    assert f.private_waterfall(100,classes).state == "INSUFFICIENT_EVIDENCE"
    assert a.robustness([{"value":1,"decision":"yes"},{"value":2,"decision":"no"}]).state == "STRUCTURALLY_SENSITIVE"

def test_service_exports_missing_inputs_and_nonfinite():
    report = service.run_case(case())
    assert all(r["state"] == "INSUFFICIENT_EVIDENCE" for key,r in report["results"].items() if key in service.METHODS)
    assert json.loads(export_json(report))["context_hash"] == report["context_hash"]
    deck = Presentation(io.BytesIO(export_pptx(report)))
    text = "\n".join(shape.text for slide in deck.slides for shape in slide.shapes if shape.has_text_frame)
    assert report["context_hash"] in text
    assert "INSUFFICIENT_EVIDENCE" in text
    with pytest.raises(ValueError):
        service.parse_bundle('{"x":NaN}')
    bad=case(); bad["models"]={"ordinary_raise":{"inputs":{"old_shares":True}}}
    assert service.run_case(bad)["results"]["ordinary_raise"]["state"] == "INVALID_INPUT"

def test_snapshot_is_immutable_and_dossier_values_remain_unverified():
    from models.pre_ipo_decision.data_quality import dossier_attributes
    bundle=case()
    report=service.run_case(bundle)
    bundle["company"]="Changed"
    assert report["context"]["company"]=="Test issuer"
    rows=dossier_attributes({"cash":0,"debt":None,"financials":[{"revenue":10}]})
    assert rows[0]["value"]==0 and rows[0]["reviewed"] is False
    assert rows[1]["status"]=="MISSING"
    assert rows[2]["attribute_id"]=="financials[0].revenue"

def test_inventory_missing_disputed_and_real_zero():
    from models.pre_ipo_decision.data_quality import attribute_inventory, method_eligibility
    reference={"version":"test-reference-1","attributes":[{"id":"cash"},{"id":"revenue"},{"id":"debt"}]}
    result=attribute_inventory(reference,[{"attribute_id":"cash","value":0},{"attribute_id":"debt","value":10,"disputed":True}])
    assert [r["state"] for r in result.data["attributes"]] == ["EXTRACTED_UNVERIFIED","MISSING","DISPUTED"]
    assert attribute_inventory(None,[]).state == "REFERENCE_REQUIRED"
    assert method_eligibility("panel_regression",1,3).state == "INSUFFICIENT_DATA"
    assert method_eligibility("predictive_ml",1,3).state == "INSUFFICIENT_DATA"

def test_invalid_empty_and_duplicate_cases():
    assert f.operating_model([]).state == "INSUFFICIENT_EVIDENCE"
    assert f.reverse_stress([],{"x":1}).state == "INSUFFICIENT_EVIDENCE"
    with pytest.raises(ValueError):
        e.eligible_evidence([{"id":"a","supersedes_id":"b"},{"id":"b","supersedes_id":"a"}],"2026-01-01")
    bad=case(); bad["models"]={"nonexistent":{}}
    with pytest.raises(ValueError):
        service.run_case(bad)
    assert f.investor_returns([{"date":"2025-01-01","amount":-100},{"date":"2026-01-01","amount":230},{"date":"2027-01-01","amount":-132}],.1).state == "IRR_NON_UNIQUE_OR_UNVERIFIED"

def test_workbench_forms_rerun_and_snapshot(monkeypatch):
    from streamlit.testing.v1 import AppTest
    from models.pre_ipo_decision import store
    monkeypatch.setattr(store,"list_cases",lambda owner: [])
    monkeypatch.setattr(store,"save_case",lambda *args: ("case1",1))
    def harness():
        import streamlit as st
        st.session_state["user"]={"username":"test","role":"researcher"}
        from components.pre_ipo_decision_workbench import render
        render()
    app=AppTest.from_function(harness).run(timeout=30)
    def field(label):
        return next(x for x in app.text_input if x.label==label)
    def button(label):
        return next(x for x in app.button if x.label==label)
    field("Company legal name").set_value("Form issuer")
    field("Currency (e.g. INR)").set_value("INR")
    field("Monetary scale (e.g. millions)").set_value("millions")
    button("Apply company facts").click().run()
    button("Run decision assessment").click().run(timeout=30)
    assert not app.exception
    expected=app.session_state["ipo_depth_report"]["context_hash"]
    button("Save private case revision").click().run()
    assert not button("Record action on saved revision").disabled
    next(x for x in app.selectbox if x.label=="Your decision perspective").select("HNI / family office")
    app.run()
    assert app.session_state["ipo_depth_report"]["context_hash"]==expected
    assert not button("Record action on saved revision").disabled

def test_private_store_owner_and_revision(monkeypatch,tmp_path):
    from contextlib import contextmanager
    import sqlite3
    from models.pre_ipo_decision import store
    @contextmanager
    def connection():
        conn=sqlite3.connect(tmp_path/"cases.db")
        try:
            with conn:
                yield conn
        finally:
            conn.close()
    monkeypatch.setattr(store,"get_connection",connection)
    report=service.run_case(case())
    identifier,revision=store.save_case("alice","researcher",report)
    assert revision == 1
    assert store.load_case("bob",identifier) is None
    with pytest.raises(PermissionError):
        store.save_case("alice","viewer",report)
    with pytest.raises(ValueError):
        store.save_case("alice","researcher",report,identifier,0)
    assert store.save_case("alice","researcher",report,identifier,1)[1] == 2
    action={"decision":"defer","rationale":"Missing source"}
    assert store.record_action("alice","researcher",identifier,1,action) == store.record_action("alice","researcher",identifier,1,action)
    assert len(store.history("alice",identifier)["actions"]) == 1
    assert len(store.history("alice",identifier)["versions"]) == 2
    assert store.history("bob",identifier) == {"versions":[],"actions":[]}
    with pytest.raises(ValueError):
        store.record_action("bob","researcher",identifier,1,{"decision":"defer","rationale":"Missing source"})
