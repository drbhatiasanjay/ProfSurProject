"""Read-only registry/reference audit. No cloud extraction or application DB writes."""
import argparse
import ast
from collections import Counter
import csv
from dataclasses import asdict
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import sqlite3
import subprocess
import sys
import types


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--reference", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    repo, out = args.repo.resolve(), args.out.resolve()
    out.mkdir(parents=True, exist_ok=True)
    sys.path.insert(0, str(repo))
    # The application's models/__init__.py initializes unrelated DB/cache modules.
    # Load only the pure dataclass/registry modules for this read-only audit.
    package = types.ModuleType("models")
    package.__path__ = [str(repo/"models")]
    sys.modules["models"] = package
    from models.pre_ipo_data import PRE_IPO_REGISTRY
    from models.pre_ipo_decision.data_quality import dossier_attributes

    reference = list(csv.DictReader(args.reference.open(encoding="utf-8-sig"), delimiter="|"))
    by_name = {}
    for row in reference:
        by_name.setdefault(row["Field Name"].casefold(), set()).add(row["Table"])
    source = (repo/"models/pre_ipo_engine.py").read_text(encoding="utf-8-sig")
    tree = ast.parse(source)
    function = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "generate_cmie_crosswalk_coverage")
    namespace = {"PreIPODealDossier": object, "Dict": dict, "Any": object}
    exec(compile(ast.Module(body=[function], type_ignores=[]), "coverage_function", "exec"), namespace)

    companies, inventory, comparisons, crosswalks = [], [], [], []
    numeric_map = {"SALES":"revenue_ops_cr", "OP_PROFIT":"ebitda_cr", "PAT":"pat_cr", "CFO":"cfo_cr", "CAPEX":"capex_cr", "FCF":"fcf_cr", "NET_WORTH":"net_worth_cr", "TOTAL_ASSETS":"total_assets_cr"}
    for key, dossier in PRE_IPO_REGISTRY.items():
        payload = asdict(dossier)
        leaves = dossier_attributes(dossier)
        meaningful = [r for r in leaves if not any(part in r["attribute_id"] for part in (".provenance", "equity_questions", "cmie_crosswalk", "audit_report", "limitations", "ic_verdict"))]
        for row in leaves:
            inventory.append({"company_id":key,"attribute_path":row["attribute_id"],"availability":row["status"],
                "origin":"CODE_REGISTRY_EXEMPLAR","review_state":"UNREVIEWED","value_json":json.dumps(row["value"], ensure_ascii=False, allow_nan=False)})
        financial_rows = []
        for item in dossier.history:
            financial_rows.append({"period":item.fiscal_year,"non_null_optional_fields":[name for name in ("total_assets_cr","receivables_cr","gross_margin_pct") if getattr(item,name) is not None],
                "missing_optional_fields":[name for name in ("total_assets_cr","receivables_cr","gross_margin_pct") if getattr(item,name) is None],
                "group_provenance_present":item.provenance is not None})
            if abs(item.fcf_cr-(item.cfo_cr-item.capex_cr)) > .01:
                comparisons.append({"company_id":key,"field":"fcf_cr","period":item.fiscal_year,"state":"INTERNAL_ARITHMETIC_DIFFERENCE", "stored":item.fcf_cr,"comparison":item.cfo_cr-item.capex_cr,"reason":"Stored FCF differs from the registry convention CFO minus capex; source and definition review required."})
        for record in dossier.cmie_crosswalk:
            candidates = sorted(by_name.get(record.cmie_field_code.casefold(), set()))
            crosswalks.append({"company_id":key,"local_alias":record.cmie_field_code,"local_concept":record.canonical_concept,
                "stored_status":record.status,"casefold_name_candidate_count":len(candidates),"table_qualified_mapping":False,
                "mapping_state":"UNQUALIFIED_NAME_CANDIDATE" if candidates else "NO_EXACT_FIELD_NAME_CANDIDATE"})
            metric = numeric_map.get(record.cmie_field_code)
            period = re.search(r"\bFY\s*(\d{2,4})\b", record.drhp_raw_value, re.I)
            amount = re.search(r"(-)?(?:Rs\.?\s*)?([\d,]+(?:\.\d+)?)\s*Cr", record.cmie_normalized_value, re.I)
            if metric and period and amount:
                year = period.group(1)[-2:]
                matching = [r for r in dossier.history if r.fiscal_year[-2:] == year]
                if matching:
                    actual = getattr(matching[0], metric)
                    target = float(amount.group(2).replace(",", "")) * (-1 if amount.group(1) else 1)
                    if actual is None or abs(actual-target) > .02:
                        comparisons.append({"company_id":key,"field":metric,"period":matching[0].fiscal_year,
                            "state":"VALUE_ABSENT_IN_HISTORY" if actual is None else "UNRESOLVED_INTERNAL_DIFFERENCE",
                            "stored":actual,"comparison":target,"reason":"Crosswalk and history nominally reference the same FY. Basis/definition and source equality are not established; do not silently overwrite either."})
        coverage = namespace["generate_cmie_crosswalk_coverage"](dossier)
        companies.append({"company_id":key,"company_name":dossier.company_name,"origin":"CODE_REGISTRY_EXEMPLAR",
            "declared_filing_type":dossier.filing_type,"declared_filing_date":dossier.filing_date,
            "history_years":[r.fiscal_year for r in dossier.history],"scalar_leaf_rows_including_metadata":len(leaves),
            "non_null_payload_leaves_excluding_audit_claim_crosswalk":sum(r["value"] is not None for r in meaningful),
            "null_payload_leaves_excluding_audit_claim_crosswalk":sum(r["value"] is None for r in meaningful),
            "crosswalk_rows":len(dossier.cmie_crosswalk),"crosswalk_status_counts":dict(Counter(r.status for r in dossier.cmie_crosswalk)),
            "legacy_coverage_pct":coverage["coverage_pct"],"legacy_verdict":coverage["data_quality_verdict"],
            "audit_items":len(dossier.audit_report),"audit_confidence_values":sorted(set(r.confidence_score for r in dossier.audit_report)),
            "financial_rows":financial_rows,"background_present":dossier.background is not None,
            "group_provenance_count":sum(isinstance(value,dict) and value.get("provenance") is not None for value in payload.values()),
            "field_to_retained_document_hash_bindings":0})

    db_result = {"path":"canonical capital_structure.db", "access":"SQLite mode=ro; query_only=ON", "tables":[]}
    db_path=repo/"capital_structure.db"
    if db_path.exists():
        with sqlite3.connect(db_path.as_uri()+"?mode=ro",uri=True) as conn:
            conn.execute("PRAGMA query_only=ON")
            names=[row[0] for row in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")]
            relevant=[name for name in names if re.search(r"pre_ipo|drhp|extract|document|evidence",name,re.I)]
            for name in relevant:
                if not re.fullmatch(r"[A-Za-z0-9_]+",name):
                    continue
                columns=[r[1] for r in conn.execute('PRAGMA table_info("'+name+'")')]
                item={"table":name,"columns":columns,"rows":conn.execute('SELECT COUNT(*) FROM "'+name+'"').fetchone()[0]}
                if name=="pre_ipo_decision_versions":
                    counters=Counter()
                    for (text,) in conn.execute("SELECT payload FROM pre_ipo_decision_versions"):
                        try:
                            bundle=json.loads(text).get("context",{})
                            company=bundle.get("company","").lower()
                            counters["synthetic_labelled_versions" if "synthetic" in company or company.startswith("test") else "other_versions_not_source_verified"]+=1
                            counters["versions_with_extracted_attributes"]+=bool(bundle.get("extracted_attributes"))
                            counters["versions_with_evidence_records"]+=bool(bundle.get("evidence"))
                            counters["versions_with_attribute_reference"]+=bool(bundle.get("attribute_reference"))
                        except (ValueError,TypeError):
                            counters["unreadable_versions"]+=1
                    item["aggregate_payload_states_no_owner_data"]=dict(counters)
                db_result["tables"].append(item)
            if "financials" in names:
                db_result["financials_physical_columns"]=[r[1] for r in conn.execute("PRAGMA table_info(financials)")]

    prospectuses=[]
    prune={".git",".venv","node_modules",".worktrees",".claude","archive","paper","paper_iimcfrc_2026","scratch","graphify-out"}
    for folder, dirs, files in os.walk(repo):
        dirs[:]=[d for d in dirs if d not in prune]
        for filename in files:
            if filename.lower().endswith(".pdf") and re.search(r"drhp|rhp|prospectus|ntpc|swiggy|afcons|mankind|tata.tech",filename,re.I):
                prospectuses.append(str((Path(folder)/filename).relative_to(repo)))
    selected=["models/pre_ipo_data.py","models/pre_ipo_schema.py","models/pre_ipo_ingest.py","models/pre_ipo_engine.py","models/pre_ipo_decision/data_quality.py","models/pre_ipo_decision/service.py","models/pre_ipo_decision/store.py","pages/27_pre_ipo_drhp.py","components/pre_ipo_decision_workbench.py","cmie/indicator_map.py","db.py","cloudbuild.yaml"]
    report={"captured_at_utc":datetime.now(timezone.utc).isoformat(),"repo_head":subprocess.check_output(["git","rev-parse","HEAD"],cwd=repo,text=True).strip(),
        "source_hashes":{name:digest(repo/name) for name in selected},"reference":{"rows":len(reference),"tables":len(set(r["Table"] for r in reference)),"sha256":digest(args.reference),"columns":list(reference[0]),"source_url":"https://www.cmie.com/kommon/bin/sr.php?file=prowessdx&kall=wlstind&type=ind","qualification":"Field catalogue, not complete accounting definitions, units, licensed values or a production mapping."},
        "companies":companies,"internal_comparisons":comparisons,"database":db_result,
        "prospectus_filename_search":{"matching_files":prospectuses,"excluded_directories":sorted(prune),"limit":"Only filenames in the traversed repository. Not archive contents, remote buckets, other worktrees or user machine search."},
        "limits":["Registry entries are code-populated examples, not a demonstrated extraction run.","No original PDF financial values are independently verified by this audit.","Counts are payload shape, not completeness or accuracy.","Public CMIE field-name candidates do not establish semantic equivalence or licensed value matches."]}
    (out/"audit_summary.json").write_text(json.dumps(report,indent=2,ensure_ascii=False,allow_nan=False),encoding="utf-8")
    for name, rows in (("attribute_inventory.csv",inventory),("cmie_crosswalk_validation.csv",crosswalks),("internal_comparisons.csv",comparisons)):
        with (out/name).open("w",newline="",encoding="utf-8-sig") as target:
            writer=csv.DictWriter(target,fieldnames=list(rows[0]) if rows else ["state"])
            writer.writeheader();writer.writerows(rows)
    print(json.dumps({"registry_companies":len(companies),"inventory_rows":len(inventory),"crosswalk_rows":len(crosswalks),"internal_review_items":len(comparisons),"reference_rows":len(reference),"reference_tables":report["reference"]["tables"],"database_tables":[r["table"] for r in db_result["tables"]]},indent=2))


if __name__=="__main__":
    main()
