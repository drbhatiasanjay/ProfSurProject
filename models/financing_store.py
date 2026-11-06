"""Append-only financing cases with owner isolation and optimistic concurrency."""
import json
from uuid import uuid4

import db


def _schema(conn):
    conn.execute("""CREATE TABLE IF NOT EXISTS financing_case_versions (
        case_id TEXT NOT NULL, owner TEXT NOT NULL, company_code INTEGER NOT NULL,
        vintage TEXT NOT NULL, revision INTEGER NOT NULL, title TEXT NOT NULL,
        payload TEXT NOT NULL, saved_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')),
        PRIMARY KEY(case_id, revision))""")


def list_cases(owner, company_code, vintage):
    conn = db.get_connection()
    try:
        _schema(conn)
        rows = conn.execute("""SELECT v.case_id,v.title,v.revision,v.saved_at
            FROM financing_case_versions v WHERE v.owner=? AND v.company_code=? AND v.vintage=?
            AND v.revision=(SELECT MAX(r.revision) FROM financing_case_versions r WHERE r.case_id=v.case_id)
            ORDER BY v.saved_at DESC,v.case_id""", (owner, int(company_code), vintage)).fetchall()
        return [dict(zip(("case_id", "title", "revision", "saved_at"), row)) for row in rows]
    finally:
        conn.close()


def load_case(owner, case_id, revision=None):
    conn = db.get_connection()
    try:
        _schema(conn)
        row = conn.execute("""SELECT company_code,vintage,revision,title,payload,saved_at
            FROM financing_case_versions WHERE owner=? AND case_id=? """ +
            ("AND revision=? " if revision is not None else "") + "ORDER BY revision DESC LIMIT 1",
            (owner, case_id, revision) if revision is not None else (owner, case_id)).fetchone()
        return dict(company_code=row[0], vintage=row[1], revision=row[2], title=row[3],
            payload=json.loads(row[4]), saved_at=row[5], case_id=case_id) if row else None
    finally:
        conn.close()


def save_case(owner, role, company_code, vintage, title, payload, *, case_id=None, expected_revision=0):
    if not owner or role not in ("admin", "researcher"):
        raise PermissionError("A signed-in researcher or administrator is required.")
    if not title.strip() or len(title) > 150:
        raise ValueError("Case title is required and must be at most 150 characters.")
    from models.financing import validate_register
    result = validate_register(payload.get("context", {}), payload.get("facilities", []), payload.get("repayments", []))
    if result["errors"]:
        raise ValueError("; ".join(result["errors"]))
    data = json.dumps(dict(payload, context=result["context"], facilities=result["facilities"],
        repayments=result["repayments"], evidence_gaps=result["gaps"]), allow_nan=False)
    conn = db.get_connection()
    try:
        _schema(conn)
        conn.execute("BEGIN IMMEDIATE")
        case_id = case_id or str(uuid4())
        existing = conn.execute("SELECT owner,company_code,vintage,MAX(revision) FROM financing_case_versions WHERE case_id=? GROUP BY owner,company_code,vintage", (case_id,)).fetchone()
        if existing and tuple(existing[:3]) != (owner, int(company_code), vintage):
            raise PermissionError("This case does not belong to this owner/company/vintage.")
        latest = existing[3] if existing else 0
        if latest != expected_revision:
            raise ValueError("Case changed in another session. Reload its latest revision before saving.")
        conn.execute("INSERT INTO financing_case_versions(case_id,owner,company_code,vintage,revision,title,payload) VALUES(?,?,?,?,?,?,?)",
            (case_id, owner, int(company_code), vintage, latest+1, title.strip(), data))
        conn.commit()
        return dict(case_id=case_id, revision=latest+1)
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
