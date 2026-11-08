"""Read-only corroboration of browser actions; never creates or modifies DB rows."""
import argparse
import json
from pathlib import Path
import sqlite3


def read(session, name, owner, remembered_ids=(), remembered_cases=()):
    root = Path(session["runDir"]).resolve()
    db = Path(session["dbPath"]).resolve()
    if session.get("marker") != "PROFSUR_DISPOSABLE_E2E_V1" or not db.is_relative_to(root) or db.name == "capital_structure.db":
        raise ValueError("Refusing non-disposable storage audit")
    conn = sqlite3.connect(db.as_uri() + "?mode=ro", uri=True)
    try:
        tables = {row[0] for row in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        if "pre_ipo_company_profiles" not in tables:
            return {"companies": [], "counts": {}}
        companies = []
        for cid, payload in conn.execute("SELECT id,payload FROM pre_ipo_company_profiles WHERE owner=?", (owner,)):
            profile = json.loads(payload)
            if profile.get("name") == name or profile.get("company_name") == name:
                companies.append(cid)
        target_ids = sorted(set(companies) | set(remembered_ids))
        counts, facts, documents, cases = {}, [], [], []
        for table in sorted(tables):
            if not table.startswith("pre_ipo_"):
                continue
            cols = {r[1] for r in conn.execute(f'PRAGMA table_info("{table}")')}
            company_col = "company" if "company" in cols else "company_id" if "company_id" in cols else None
            if "owner" in cols and company_col:
                counts[table] = sum(conn.execute(f'SELECT COUNT(*) FROM "{table}" WHERE owner=? AND "{company_col}"=?', (owner, cid)).fetchone()[0] for cid in target_ids)
        for cid in target_ids:
            if "pre_ipo_fact_events" in tables:
                facts += [json.loads(r[0]) for r in conn.execute("SELECT payload FROM pre_ipo_fact_events WHERE owner=? AND company=? ORDER BY fact_id,revision", (owner, cid))]
            if "pre_ipo_sources" in tables:
                documents += [json.loads(r[0]) for r in conn.execute("SELECT metadata FROM pre_ipo_sources WHERE owner=? AND company=?", (owner, cid))]
        if "pre_ipo_decision_versions" in tables:
            for case_id, payload in conn.execute("SELECT case_id,payload FROM pre_ipo_decision_versions WHERE owner=?", (owner,)):
                if json.loads(payload).get("context", {}).get("company") == name:
                    cases.append(case_id)
        case_ids = set(cases) | set(remembered_cases)
        if "pre_ipo_decision_actions" in tables:
            counts["remembered_decision_actions"] = sum(conn.execute("SELECT COUNT(*) FROM pre_ipo_decision_actions WHERE owner=? AND case_id=?", (owner, cid)).fetchone()[0] for cid in case_ids)
        return {"companies": companies, "counts": counts, "facts": facts, "documents": documents, "case_ids": sorted(set(cases))}
    finally:
        conn.close()


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--session", required=True)
    p.add_argument("--name", required=True)
    p.add_argument("--owner", required=True)
    p.add_argument("--company-id", action="append", default=[])
    p.add_argument("--case-id", action="append", default=[])
    a = p.parse_args()
    print(json.dumps(read(json.loads(Path(a.session).read_text()), a.name, a.owner, a.company_id, a.case_id)))
