"""Owner-scoped append-only snapshots, with optimistic revision checks."""
import json
import uuid
from db import get_connection
from .contracts import canonical_json

def _schema(conn):
    try:
        from models.pre_ipo_migrations import apply_migrations
        apply_migrations(conn)
    except Exception:
        pass

    # Ensure pre_ipo_decision_versions has all columns
    conn.execute("""CREATE TABLE IF NOT EXISTS pre_ipo_decision_versions (
        owner TEXT NOT NULL, case_id TEXT NOT NULL, revision INTEGER NOT NULL, company_id TEXT, snapshot_id TEXT,
        payload TEXT NOT NULL, created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
        PRIMARY KEY(owner, case_id, revision))""")

    cols_v = [r[1] for r in conn.execute("PRAGMA table_info(pre_ipo_decision_versions)").fetchall()]
    if "company_id" not in cols_v:
        conn.execute("ALTER TABLE pre_ipo_decision_versions ADD COLUMN company_id TEXT")
    if "snapshot_id" not in cols_v:
        conn.execute("ALTER TABLE pre_ipo_decision_versions ADD COLUMN snapshot_id TEXT")

    # Ensure pre_ipo_decision_actions has all columns
    conn.execute("""CREATE TABLE IF NOT EXISTS pre_ipo_decision_actions (
        owner TEXT NOT NULL, case_id TEXT NOT NULL, revision INTEGER NOT NULL, company_id TEXT, snapshot_id TEXT,
        action_id TEXT NOT NULL, payload TEXT NOT NULL,
        created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
        PRIMARY KEY(owner, action_id))""")

    cols_a = [r[1] for r in conn.execute("PRAGMA table_info(pre_ipo_decision_actions)").fetchall()]
    if "company_id" not in cols_a:
        conn.execute("ALTER TABLE pre_ipo_decision_actions ADD COLUMN company_id TEXT")
    if "snapshot_id" not in cols_a:
        conn.execute("ALTER TABLE pre_ipo_decision_actions ADD COLUMN snapshot_id TEXT")

def list_cases(owner):
    with get_connection() as conn:
        _schema(conn)
        return [dict(zip(("case_id", "revision"), row)) for row in conn.execute(
            "SELECT case_id,MAX(revision) FROM pre_ipo_decision_versions WHERE owner=? GROUP BY case_id", (owner,)).fetchall()]

def history(owner, case_id):
    with get_connection() as conn:
        _schema(conn)
        versions = [{"revision": r[0], "created_at": r[1]} for r in conn.execute(
            "SELECT revision,created_at FROM pre_ipo_decision_versions WHERE owner=? AND case_id=? ORDER BY revision DESC", (owner, case_id))]
        actions = [{"revision": r[0], "created_at": r[1], **json.loads(r[2])} for r in conn.execute(
            "SELECT revision,created_at,payload FROM pre_ipo_decision_actions WHERE owner=? AND case_id=? ORDER BY created_at,action_id", (owner, case_id))]
    return {"versions": versions, "actions": actions}

def load_case(owner, case_id, revision=None):
    with get_connection() as conn:
        _schema(conn)
        row = conn.execute("SELECT payload FROM pre_ipo_decision_versions WHERE owner=? AND case_id=? AND (? IS NULL OR revision=?) ORDER BY revision DESC LIMIT 1",
                           (owner, case_id, revision, revision)).fetchone()
        return json.loads(row[0]) if row else None

def save_case(owner, role, report, case_id=None, expected_revision=0):
    if not owner or role not in {"admin", "researcher"}:
        raise PermissionError("Researcher or admin required")
    from .service import run_case
    verified = run_case(report["context"])
    if canonical_json(verified) != canonical_json(report):
        raise ValueError("Report does not match its immutable input snapshot")
    case_id = case_id or str(uuid.uuid4())
    payload = canonical_json(report)
    with get_connection() as conn:
        _schema(conn)
        conn.execute("BEGIN IMMEDIATE")
        revision = conn.execute("SELECT MAX(revision) FROM pre_ipo_decision_versions WHERE owner=? AND case_id=?", (owner, case_id)).fetchone()[0] or 0
        if revision != expected_revision:
            raise ValueError("Case changed; reload before saving")
        ctx = report.get("context", {}) if isinstance(report, dict) else {}
        cid = ctx.get("company_id") or ctx.get("company")
        snap_id = ctx.get("snapshot_id") or ctx.get("evidence_snapshot_id") or (report.get("snapshot_id") if isinstance(report, dict) else None)

        # Resolve display name to canonical ID from pre_ipo_company_profiles if needed
        if cid:
            try:
                prof_match = conn.execute(
                    "SELECT id FROM pre_ipo_company_profiles WHERE owner=? AND (id=? OR json_extract(payload, '$.name')=?)",
                    (owner, cid, cid)
                ).fetchone()
                if prof_match:
                    cid = prof_match[0]
            except Exception:
                pass

        conn.execute("INSERT INTO pre_ipo_decision_versions(owner,case_id,revision,company_id,snapshot_id,payload) VALUES(?,?,?,?,?,?)", (owner, case_id, revision+1, cid, snap_id, payload))
        if cid:
            try:
                conn.execute("INSERT OR IGNORE INTO pre_ipo_dependencies(owner, company, dependent_kind, dependent_id, target_kind, target_id, relation_type) VALUES(?, ?, 'DECISION', ?, 'COMPANY', ?, 'USES_COMPANY')", (owner, cid, case_id, cid))
                if snap_id:
                    conn.execute("INSERT OR IGNORE INTO pre_ipo_dependencies(owner, company, dependent_kind, dependent_id, target_kind, target_id, relation_type) VALUES(?, ?, 'DECISION', ?, 'SNAPSHOT', ?, 'USES_SNAPSHOT')", (owner, cid, case_id, snap_id))
            except Exception:
                pass
    return case_id, revision+1

def record_action(owner, role, case_id, revision, action):
    if role not in {"admin", "researcher"}:
        raise PermissionError("Researcher or admin required")
    if not action.get("decision") or not action.get("rationale"):
        raise ValueError("Decision and rationale required")
    with get_connection() as conn:
        _schema(conn)
        ver_row = conn.execute(
            "SELECT company_id, snapshot_id FROM pre_ipo_decision_versions WHERE owner=? AND case_id=? AND revision=?",
            (owner, case_id, revision)
        ).fetchone()
        if not ver_row:
            raise ValueError("Owned saved revision required")
        cid, snap_id = ver_row[0], ver_row[1]

        from .contracts import context_hash
        action_id = context_hash({"owner": owner, "case_id": case_id, "revision": revision, "action": action})
        conn.execute("BEGIN IMMEDIATE")
        if conn.execute("SELECT 1 FROM pre_ipo_decision_actions WHERE owner=? AND action_id=?", (owner, action_id)).fetchone():
            return action_id
        conn.execute(
            "INSERT INTO pre_ipo_decision_actions(owner,case_id,revision,company_id,snapshot_id,action_id,payload) VALUES(?,?,?,?,?,?,?)",
            (owner, case_id, revision, cid, snap_id, action_id, canonical_json(action))
        )
    return action_id
