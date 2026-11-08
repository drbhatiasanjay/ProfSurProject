import uuid
"""Private, append-only Pre-IPO source and fact ledger. No cloud model calls."""
from contextlib import contextmanager
from dataclasses import dataclass, field, asdict
from datetime import date, datetime, timezone
from decimal import Decimal, InvalidOperation
import hashlib
import io
import json
import re
import sqlite3

VERSION = "evidence-v1"
MAX_PDF_BYTES = 25 * 1024 * 1024
MAX_PAGES = 1500
PRESENCE = ("OBSERVED_VALUE", "EXPLICIT_NIL", "NOT_DISCLOSED", "NOT_SEARCHED", "EXTRACTION_FAILED", "NOT_APPLICABLE_CLAIMED", "REDACTED", "SOURCE_UNAVAILABLE")
REVIEW = ("UNREVIEWED", "ACCEPTED", "DISPUTED", "REJECTED", "SUPERSEDED", "WITHDRAWN")
ORIGINS = ("FILING_FACT", "DERIVED", "ANALYST_ASSUMPTION", "EXTERNAL_BENCHMARK", "LEGACY_EXAMPLE")
CONTEXT = ("entity", "period", "duration", "basis", "framework", "currency", "unit", "definition")
DOMAINS = {
    "Identity and business": ("background", "company_name", "sector"),
    "Offer and ownership": ("objects_of_offer", "cap_table", "fresh_issue", "ofs", "issue"),
    "Financial performance": ("history",),
    "Debt and obligations": ("indebtedness", "debt_maturity"),
    "Working capital": ("working_capital",),
    "Governance and legal": ("governance", "non_financial"),
    "Valuation and peers": ("valuation", "peer"),
    "Evidence and other disclosures": (),
}


@dataclass
class EvidencePeriod:
    fiscal_year: str
    revenue_ops_cr: object = None
    ebitda_cr: object = None
    pat_cr: object = None
    cfo_cr: object = None
    cfi_cr: object = None
    cff_cr: object = None
    capex_cr: object = None
    fcf_cr: object = None
    net_worth_cr: object = None
    total_assets_cr: object = None
    receivables_cr: object = None
    gross_margin_pct: object = None


@dataclass
class EvidenceProfile:
    company_name: str
    sector: str
    history: list
    filing_type: str = "NOT_ESTABLISHED"
    filing_date: str = "NOT_ESTABLISHED"
    cmie_crosswalk: list = field(default_factory=list)
    background: object = None
    generation: int = 1


def dump(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=False, allow_nan=False, separators=(",", ":"))


def digest(value):
    return hashlib.sha256(value if isinstance(value, bytes) else dump(value).encode()).hexdigest()


def domain(path):
    return next((name for name, prefixes in DOMAINS.items() if any(path.startswith(p) for p in prefixes)), "Evidence and other disclosures")


def numeric(value):
    try:
        result = Decimal(str(value).replace(",", ""))
    except InvalidOperation as exc:
        raise ValueError("A finite decimal number is required") from exc
    if not result.is_finite() or len(str(value)) > 100 or result and abs(result.adjusted())>100:
        raise ValueError("A finite bounded decimal number is required")
    return result


def normalize(value, scale="1"):
    factor = numeric(scale)
    if factor <= 0:
        raise ValueError("Scale must be positive")
    return str(numeric(value) * factor)


def compare(left, right, absolute="0.02", relative="0"):
    if numeric(absolute) < 0 or numeric(relative) < 0:
        raise ValueError("Tolerances cannot be negative")
    missing = [key for key in CONTEXT if not left.get("context", {}).get(key) or not right.get("context", {}).get(key)]
    if missing:
        return {"state": "CONTEXT_REVIEW_REQUIRED", "fields": missing}
    differences = [key for key in CONTEXT if left["context"][key] != right["context"][key]]
    if differences:
        return {"state": "NOT_COMPARABLE", "fields": differences}
    try:
        a, b = numeric(left["value"]), numeric(right["value"])
        tolerance = max(numeric(absolute), numeric(relative) * max(abs(a), abs(b)))
        return {"state": "NUMERIC_AGREEMENT" if abs(a-b) <= tolerance else "DISPUTED", "difference": str(a-b), "tolerance": str(tolerance)}
    except (ValueError, KeyError):
        return {"state": "TEXT_AGREEMENT" if left.get("value") == right.get("value") else "DISPUTED"}


@contextmanager
def connection():
    from db import get_connection
    from models.pre_ipo_migrations import apply_migrations
    conn = get_connection()
    conn.row_factory = sqlite3.Row
    try:
        conn.execute("PRAGMA foreign_keys=ON")
        apply_migrations(conn)
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def actor(owner, role=None):
    if not isinstance(owner, str) or not owner.strip():
        raise PermissionError("Authenticated owner required")
    if role is not None and role not in {"admin", "researcher"}:
        raise PermissionError("Researcher or admin required")


def _latest(conn, owner, company):
    records = conn.execute("""SELECT e.payload FROM pre_ipo_fact_events e JOIN
      (SELECT fact_id,MAX(revision) revision FROM pre_ipo_fact_events WHERE owner=? AND company=? GROUP BY fact_id) l
      ON e.fact_id=l.fact_id AND e.revision=l.revision WHERE e.owner=? AND e.company=? ORDER BY e.fact_id""", (owner,company,owner,company))
    return [json.loads(row[0]) for row in records]


def _as_of(conn,owner,company,cutoff):
    """Latest revision eligible by filing availability, including later withdrawals.

    This is public-as-of research, not a claim about what a user actually knew then.
    """
    if not cutoff:
        return _latest(conn,owner,company)
    date.fromisoformat(cutoff)
    source_dates={r[0]:json.loads(r[1])["available_by"] for r in conn.execute("SELECT id,metadata FROM pre_ipo_sources WHERE owner=? AND company=? AND status='ACTIVE'",(owner,company))}
    chosen={}
    for row in conn.execute("SELECT fact_id,payload FROM pre_ipo_fact_events WHERE owner=? AND company=? ORDER BY fact_id,revision DESC",(owner,company)):
        item=json.loads(row[1]); source_id=item.get("source",{}).get("id")
        if item["id"] in chosen:
            continue
        if source_id and (source_id not in source_dates or (cutoff and source_dates.get(source_id,"")>cutoff)):
            continue
        if item.get("review") == "WITHDRAWN":
            continue
        chosen[item["id"]]=item
    return list(chosen.values())


def facts(owner, company):
    actor(owner)
    with connection() as conn:
        return _latest(conn, owner, company)


def create_company(owner,role,name,sector,periods):
    actor(owner,role)
    if role and role not in {"admin", "researcher"}:
        raise PermissionError("Viewers cannot create private companies")
    if not name.strip() or not sector.strip() or not 1<=len(periods)<=10 or len(set(periods))!=len(periods):
        raise ValueError("Legal name, sector and 1–10 distinct reporting-period labels required")
    if any(not str(p).strip() or len(str(p))>60 for p in periods):
        raise ValueError("Valid reporting-period labels required")
    profile=EvidenceProfile(name.strip()[:300],sector.strip()[:300],[EvidencePeriod(p.strip()) for p in periods])
    key="private-"+digest({"name":name.strip(),"sector":sector.strip(),"periods":periods})[:20]
    with connection() as conn:
        max_tomb_gen = conn.execute(
            "SELECT MAX(generation) FROM pre_ipo_tombstones WHERE owner=? AND company=? AND target_kind='COMPANY'",
            (owner, key)
        ).fetchone()[0] or 0
        new_gen = max_tomb_gen + 1
        conn.execute("INSERT OR REPLACE INTO pre_ipo_company_profiles(owner,id,payload,generation,status) VALUES(?,?,?,?, 'ACTIVE')",
                     (owner,key,dump(asdict(profile)),new_gen))
    return key


def get_deletion_impact(owner, company_id):
    """Compute an owner-scoped dependency manifest before irreversible deletion."""
    actor(owner)
    with connection() as conn:
        prof = conn.execute("SELECT id, payload, generation, status FROM pre_ipo_company_profiles WHERE owner=? AND id=?", (owner, company_id)).fetchone()
        if not prof:
            return {"exists": False, "company_id": company_id}
        sources_cnt = conn.execute("SELECT COUNT(*) FROM pre_ipo_sources WHERE owner=? AND company=?", (owner, company_id)).fetchone()[0]
        artifacts_cnt = conn.execute("SELECT COUNT(*) FROM pre_ipo_artifacts WHERE owner=? AND company=?", (owner, company_id)).fetchone()[0]
        jobs_cnt = conn.execute("SELECT COUNT(*) FROM pre_ipo_jobs WHERE owner=? AND company=?", (owner, company_id)).fetchone()[0]
        facts_cnt = conn.execute("SELECT COUNT(*) FROM pre_ipo_fact_events WHERE owner=? AND company=?", (owner, company_id)).fetchone()[0]
        obs_cnt = conn.execute("SELECT COUNT(*) FROM pre_ipo_observations WHERE owner=? AND company=?", (owner, company_id)).fetchone()[0]
        snaps_cnt = conn.execute("SELECT COUNT(*) FROM pre_ipo_evidence_snapshots WHERE owner=? AND company=?", (owner, company_id)).fetchone()[0]
        dec_cols = [r[1] for r in conn.execute("PRAGMA table_info(pre_ipo_decision_versions)").fetchall()]
        dec_cnt = conn.execute("SELECT COUNT(*) FROM pre_ipo_decision_versions WHERE owner=? AND company_id=?", (owner, company_id)).fetchone()[0] if "company_id" in dec_cols else 0
        act_cnt = conn.execute("""
            SELECT COUNT(*) FROM pre_ipo_decision_actions 
            WHERE owner=? AND (company_id=? OR case_id IN (
                SELECT case_id FROM pre_ipo_decision_versions WHERE owner=? AND company_id=?
            ))
        """, (owner, company_id, owner, company_id)).fetchone()[0] if "company_id" in dec_cols else 0
        return {
            "exists": True,
            "company_id": company_id,
            "generation": prof["generation"] if "generation" in prof.keys() else 1,
            "status": prof["status"] if "status" in prof.keys() else "ACTIVE",
            "affected_counts": {
                "sources": sources_cnt,
                "artifacts": artifacts_cnt,
                "jobs": jobs_cnt,
                "facts": facts_cnt,
                "observations": obs_cnt,
                "snapshots": snaps_cnt,
                "saved_decisions": dec_cnt,
                "decision_actions": act_cnt,
            }
        }


def delete_company(owner, role, company_id):
    """Enforce full deletion lifecycle with atomic DELETE_PENDING transition, worker cancellation, and audit tombstones."""
    actor(owner, role)
    if role not in {"admin", "researcher"}:
        raise PermissionError("Viewers cannot delete private companies")
    with connection() as conn:
        conn.execute("BEGIN IMMEDIATE")
        prof = conn.execute("SELECT generation, status FROM pre_ipo_company_profiles WHERE owner=? AND id=?", (owner, company_id)).fetchone()
        if not prof:
            return False
        curr_gen = prof[0] if prof[0] is not None else 1

        # Mark DELETE_PENDING and bump generation to invalidate in-flight async commits
        conn.execute("UPDATE pre_ipo_company_profiles SET status='DELETE_PENDING', generation=? WHERE owner=? AND id=?",
                     (curr_gen + 1, owner, company_id))

        # Cancel pending / running background jobs
        conn.execute("UPDATE pre_ipo_jobs SET status='CANCELLED' WHERE owner=? AND company=? AND status IN ('QUEUED', 'RUNNING')",
                     (owner, company_id))

        # Atomic purge of scoped company records
        conn.execute("DELETE FROM pre_ipo_sources WHERE owner=? AND company=?", (owner, company_id))
        conn.execute("DELETE FROM pre_ipo_artifacts WHERE owner=? AND company=?", (owner, company_id))
        conn.execute("DELETE FROM pre_ipo_extraction_runs WHERE owner=? AND company=?", (owner, company_id))
        conn.execute("DELETE FROM pre_ipo_fact_events WHERE owner=? AND company=?", (owner, company_id))
        conn.execute("DELETE FROM pre_ipo_observations WHERE owner=? AND company=?", (owner, company_id))
        conn.execute("DELETE FROM pre_ipo_evidence_actions WHERE owner=? AND company=?", (owner, company_id))
        conn.execute("DELETE FROM pre_ipo_evidence_action_events WHERE owner=? AND company=?", (owner, company_id))
        conn.execute("DELETE FROM pre_ipo_evidence_snapshots WHERE owner=? AND company=?", (owner, company_id))
        conn.execute("DELETE FROM pre_ipo_dependencies WHERE owner=? AND company=?", (owner, company_id))

        # Purge dependent saved decisions AND decision actions
        try:
            conn.execute("""
                DELETE FROM pre_ipo_decision_actions 
                WHERE owner=? AND (company_id=? OR case_id IN (
                    SELECT case_id FROM pre_ipo_decision_versions WHERE owner=? AND company_id=?
                ))
            """, (owner, company_id, owner, company_id))
            conn.execute("DELETE FROM pre_ipo_decision_versions WHERE owner=? AND company_id=?", (owner, company_id))
        except Exception:
            pass

        # Purge profile itself
        conn.execute("DELETE FROM pre_ipo_company_profiles WHERE owner=? AND id=?", (owner, company_id))

        # Record non-reconstructive unique audit tombstone
        tomb_id = str(uuid.uuid4())
        conn.execute("""
            INSERT INTO pre_ipo_tombstones (id, owner, company, target_kind, target_id, generation, action, actor)
            VALUES (?, ?, ?, 'COMPANY', ?, ?, 'DELETE', ?)
        """, (tomb_id, owner, company_id, company_id, curr_gen, owner))
        conn.commit()
    return True


def delete_source(owner, role, company_id, source_id):
    """Permanently delete a specific document/source incarnation while preserving company and other documents."""
    actor(owner, role)
    if role not in {"admin", "researcher"}:
        raise PermissionError("Viewers cannot delete private sources")
    with connection() as conn:
        conn.execute("BEGIN IMMEDIATE")
        src = conn.execute("SELECT generation, status FROM pre_ipo_sources WHERE owner=? AND company=? AND id=?", (owner, company_id, source_id)).fetchone()
        if not src:
            return False
        curr_gen = src[0] if src[0] is not None else 1

        # Cancel jobs for this specific source
        conn.execute("UPDATE pre_ipo_jobs SET status='CANCELLED' WHERE owner=? AND company=? AND source_id=? AND status IN ('QUEUED', 'RUNNING')",
                     (owner, company_id, source_id))

        # Purge artifacts, observations, extraction runs, fact events, and source row
        conn.execute("DELETE FROM pre_ipo_artifacts WHERE owner=? AND company=? AND source_id=?", (owner, company_id, source_id))
        conn.execute("DELETE FROM pre_ipo_observations WHERE owner=? AND company=? AND source_id=?", (owner, company_id, source_id))
        conn.execute("DELETE FROM pre_ipo_extraction_runs WHERE owner=? AND company=? AND json_extract(payload, '$.source_id')=?", (owner, company_id, source_id))
        conn.execute("DELETE FROM pre_ipo_fact_events WHERE owner=? AND company=? AND (json_extract(payload, '$.source.id')=? OR json_extract(payload, '$.origin_id')=?)", (owner, company_id, source_id, source_id))
        conn.execute("DELETE FROM pre_ipo_sources WHERE owner=? AND company=? AND id=?", (owner, company_id, source_id))

        # Record unique company-scoped tombstone
        tomb_id = str(uuid.uuid4())
        conn.execute("""
            INSERT INTO pre_ipo_tombstones (id, owner, company, target_kind, target_id, generation, action, actor)
            VALUES (?, ?, ?, 'SOURCE', ?, ?, 'DELETE', ?)
        """, (tomb_id, owner, company_id, source_id, curr_gen + 1, owner))
        conn.commit()
    return True


def withdraw_source(owner, role, company_id, source_id, reason="Superseded by updated filing"):
    """Exclude source from new reliance while retaining historical audit trail."""
    actor(owner, role)
    if role not in {"admin", "researcher"}:
        raise PermissionError("Viewers cannot withdraw private sources")
    with connection() as conn:
        conn.execute("BEGIN IMMEDIATE")
        src = conn.execute("SELECT generation, status FROM pre_ipo_sources WHERE owner=? AND company=? AND id=?", (owner, company_id, source_id)).fetchone()
        if not src:
            return False
        curr_gen = src[0] if src[0] is not None else 1

        # Mark source WITHDRAWN and bump generation
        conn.execute("UPDATE pre_ipo_sources SET status='WITHDRAWN', generation=? WHERE owner=? AND company=? AND id=?",
                     (curr_gen + 1, owner, company_id, source_id))

        # Mark extracted observations WITHDRAWN
        conn.execute("UPDATE pre_ipo_observations SET review_state='WITHDRAWN' WHERE owner=? AND company=? AND source_id=?",
                     (owner, company_id, source_id))

        # Withdraw / supersede all fact events referencing this source
        affected_facts = conn.execute("""
            SELECT fact_id, MAX(revision), payload FROM pre_ipo_fact_events 
            WHERE owner=? AND company=? AND (
                json_extract(payload, '$.source.id')=? OR json_extract(payload, '$.origin_id')=?
            )
            GROUP BY fact_id
        """, (owner, company_id, source_id, source_id)).fetchall()

        for fid, max_rev, p_raw in affected_facts:
            p = json.loads(p_raw) if isinstance(p_raw, str) else p_raw
            p["review"] = "WITHDRAWN"
            p["presence"] = "NOT_DISCLOSED"
            p["reason"] = f"Withdrawn with source {source_id}: {reason}"
            p["revision"] = max_rev + 1
            p["updated_at"] = datetime.now(timezone.utc).isoformat()
            conn.execute(
                "INSERT INTO pre_ipo_fact_events(owner, company, fact_id, revision, payload) VALUES(?,?,?,?,?)",
                (owner, company_id, fid, max_rev + 1, dump(p))
            )

        # Record unique company-scoped tombstone
        tomb_id = str(uuid.uuid4())
        conn.execute("""
            INSERT INTO pre_ipo_tombstones (id, owner, company, target_kind, target_id, generation, action, reason, actor)
            VALUES (?, ?, ?, 'SOURCE', ?, ?, 'WITHDRAW', ?, ?)
        """, (tomb_id, owner, company_id, source_id, curr_gen + 1, reason, owner))
        conn.commit()
    return True


def companies(owner):
    actor(owner)
    with connection() as conn:
        output={}
        for row in conn.execute("SELECT id,payload,generation FROM pre_ipo_company_profiles WHERE owner=? ORDER BY id",(owner,)):
            payload=json.loads(row[1]); payload["history"]=[EvidencePeriod(**p) for p in payload["history"]]
            payload["generation"] = row[2] if row[2] is not None else 1
            output[row[0]]=EvidenceProfile(**payload)
        return output


def import_dossier(owner,role,legal_name,dossier,content,metadata):
    """Retain an existing intake without promoting defaults, citations or model scores."""
    actor(owner,role)
    if role and role not in {"admin", "researcher"}:
        raise PermissionError("Viewers cannot import private dossiers")
    from models.pre_ipo_decision.data_quality import dossier_attributes
    periods=[p.fiscal_year for p in dossier.history] or ["NOT_ESTABLISHED"]
    company=create_company(owner,role,legal_name,dossier.sector,periods)
    source_id=retain_pdf(owner,role,company,content,metadata)
    retained,_=source(owner,company,source_id)
    fingerprint=digest(asdict(dossier))
    blocked=any(g.gap_id.startswith(("GAP-OCR-","GAP-INTAKE-")) for g in dossier.limitations)
    run_config = {
        "source_id": source_id,
        "engine": "PreIPOIngestionEngine",
        "schema": VERSION,
        "version": str(metadata.get("version", "Draft 1.0")),
        "filing_type": str(metadata.get("filing_type", "DRHP")),
    }
    run_id = digest(run_config)
    gaps_list = [
        {
            "gap_id": getattr(g, "gap_id", str(g)),
            "item_name": getattr(g, "item_name", ""),
            "status": getattr(g, "current_status", "ACTIVE_GAP"),
            "priority": getattr(g, "materiality_priority", "HIGH"),
            "action": getattr(g, "recommended_diligence_request", ""),
        }
        for g in getattr(dossier, "limitations", [])
    ]
    run_payload = {
        "id": run_id,
        **run_config,
        "status": "COMPLETED_WITH_GAPS" if gaps_list else "BATCH_COMPLETED",
        "gaps": gaps_list,
        "limitations_count": len(gaps_list),
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    with connection() as conn:
        conn.execute("INSERT OR IGNORE INTO pre_ipo_extraction_runs(owner,company,id,payload) VALUES(?,?,?,?)",
                     (owner,company,run_id,dump(run_payload)))
        for row in dossier_attributes(dossier):
            key=row["attribute_id"]
            prior=conn.execute("SELECT revision,payload FROM pre_ipo_fact_events WHERE owner=? AND company=? AND fact_id=? ORDER BY revision DESC LIMIT 1",(owner,company,key)).fetchone()
            previous=json.loads(prior[1]) if prior else {}
            if previous.get("source",{}).get("id")==source_id and previous.get("intake_fingerprint")==fingerprint:
                continue
            match=re.match(r"history\[(\d+)\]",key)
            value=None if blocked else row["value"]
            item={"id":key,"revision":1,"raw_value":row["value"],"value":value,"presence":"EXTRACTION_FAILED" if blocked else "NOT_SEARCHED" if value is None else "OBSERVED_VALUE","origin":"FILING_FACT","review":"UNREVIEWED","domain":domain(key),"context":{"entity":legal_name,"period":periods[int(match[1])] if match else "NOT_ESTABLISHED","duration":"NOT_ESTABLISHED","basis":"NOT_ESTABLISHED","framework":"NOT_ESTABLISHED","currency":"INR" if key.endswith("_cr") else "NOT_ESTABLISHED","unit":"crore" if key.endswith("_cr") else "NOT_ESTABLISHED","definition":key},"source":{"id":source_id,"sha256":retained["sha256"]},"reason":"Existing intake candidate: defaults, source locations and model confidence are unverified. Original source review required.","reviewer":owner,"dependencies":[],"mapping":{}}
            item.update(revision=prior[0]+1 if prior else 1,intake_fingerprint=fingerprint,extraction_raw_value=row["value"])
            if prior:
                item["raw_value"]=previous.get("raw_value")
            conn.execute("INSERT INTO pre_ipo_fact_events(owner,company,fact_id,revision,payload) VALUES(?,?,?,?,?)",(owner,company,key,item["revision"],dump(item)))
            conn.execute("""
                INSERT OR REPLACE INTO pre_ipo_observations (
                    owner, company, observation_id, revision, source_id, entity, metric_id,
                    period, duration, basis, framework, currency, unit, value, presence,
                    review_state, provenance_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                owner, company, key, item["revision"], source_id, legal_name, key,
                item["context"]["period"], item["context"]["duration"], item["context"]["basis"],
                item["context"]["framework"], item["context"]["currency"], item["context"]["unit"],
                str(value) if value is not None else None, item["presence"], item["review"], dump(item.get("source", {}))
            ))
        conn.execute("""
            INSERT OR REPLACE INTO pre_ipo_jobs (
                id, owner, company, source_id, job_type, status, payload_json
            ) VALUES (?, ?, ?, ?, 'PreIPOIngestionEngine', ?, ?)
        """, (run_id, owner, company, source_id, "COMPLETED_WITH_GAPS" if gaps_list else "COMPLETED", json.dumps({"target_generation": 1, "profile_hash": run_id[:16], "page_range": f"1-{metadata.get('pages', 1)}"})))
        conn.execute("""
            INSERT OR REPLACE INTO pre_ipo_artifacts (
                owner, company, source_id, artifact_id, artifact_type, mime_type, content, metadata_json
            ) VALUES (?, ?, ?, ?, 'ORIGINAL_PDF', 'application/pdf', ?, ?)
        """, (owner, company, source_id, f"art-pdf-{source_id[:16]}", content, json.dumps({"digest": retained["sha256"]})))
    return company


def history(owner, company, fact_id):
    actor(owner)
    with connection() as conn:
        return [json.loads(r[0]) for r in conn.execute("SELECT payload FROM pre_ipo_fact_events WHERE owner=? AND company=? AND fact_id=? ORDER BY revision", (owner,company,fact_id))]


def preview_dossier(dossier):
    """Inspect existing attributes without creating or accepting private facts."""
    from models.pre_ipo_decision.data_quality import dossier_attributes
    output=[]
    periods = {str(i): item.fiscal_year for i, item in enumerate(dossier.history)}
    for row in dossier_attributes(dossier):
        path=row["attribute_id"]
        match=re.match(r"history\[(\d+)\]",path)
        context={"entity":dossier.company_name,"period":periods[match[1]] if match else "NOT_ESTABLISHED","duration":"ANNUALIZED_STUB" if match and "Ann." in periods[match[1]] else "NOT_ESTABLISHED","basis":"NOT_ESTABLISHED","framework":"NOT_ESTABLISHED","currency":"INR" if path.endswith("_cr") else "NOT_ESTABLISHED","unit":"crore" if path.endswith("_cr") else "NOT_ESTABLISHED","definition":path}
        private=isinstance(dossier,EvidenceProfile)
        output.append({"id":path,"revision":1,"raw_value":row["value"],"value":row["value"],"presence":"NOT_SEARCHED" if row["value"] is None else "OBSERVED_VALUE","origin":"ANALYST_ASSUMPTION" if private else "LEGACY_EXAMPLE","review":"UNREVIEWED","domain":domain(path),"context":context,"source":{},"reason":"User-created company profile; financial slots are empty." if private else "Imported registry example; original-document extraction not established.","reviewer":"","dependencies":[],"material":path.startswith(("history","indebtedness","objects_of_offer")),"mapping":{}})
    return output


def seed_dossier(owner, role, company, dossier):
    """Idempotent registry import. Never silently overwrites existing reviews."""
    actor(owner, role)
    rows=preview_dossier(dossier)
    with connection() as conn:
        conn.execute("BEGIN IMMEDIATE")
        for value in rows:
            path = value["id"]
            if conn.execute("SELECT 1 FROM pre_ipo_fact_events WHERE owner=? AND company=? AND fact_id=?", (owner,company,path)).fetchone():
                continue
            value["reviewer"]=owner
            conn.execute("INSERT INTO pre_ipo_fact_events(owner,company,fact_id,revision,payload) VALUES(?,?,?,?,?)",(owner,company,path,1,dump(value)))
    return len(rows)


def _source(conn, owner, company, source_id, allow_withdrawn=False):
    row = conn.execute("SELECT metadata, content, status FROM pre_ipo_sources WHERE owner=? AND company=? AND id=?", (owner, company, source_id)).fetchone()
    if not row:
        raise ValueError("Retained owned source required")
    if not allow_withdrawn and len(row) > 2 and row[2] == "WITHDRAWN":
        raise ValueError("Source has been withdrawn from reliance")
    metadata, data = json.loads(row[0]), bytes(row[1])
    if digest(data) != metadata["sha256"]:
        raise ValueError("Source hash mismatch")
    return metadata, data


def sources(owner, company):
    actor(owner)
    with connection() as conn:
        return [json.loads(r[0]) for r in conn.execute("SELECT metadata FROM pre_ipo_sources WHERE owner=? AND company=? ORDER BY id",(owner,company))]


def source(owner, company, source_id):
    actor(owner)
    with connection() as conn:
        return _source(conn,owner,company,source_id)


def retain_pdf(owner, role, company, content, metadata):
    actor(owner, role)
    if not content or len(content) > MAX_PDF_BYTES or not content.startswith(b"%PDF-"):
        raise ValueError("A PDF with a valid signature, up to 25 MB, is required")
    from pypdf import PdfReader
    try:
        reader = PdfReader(io.BytesIO(content), strict=False)
        if reader.is_encrypted:
            raise ValueError("Encrypted PDFs require an authorized unencrypted copy")
        pages = len(reader.pages)
        if not 1 <= pages <= MAX_PAGES:
            raise ValueError("PDF must contain 1–1,500 pages")
    except Exception as exc:
        raise ValueError("PDF could not be safely opened: " + type(exc).__name__) from exc
    required = ("title", "filing_type", "version", "available_by", "rights")
    if not all(str(metadata.get(k, "")).strip() for k in required):
        raise ValueError("Title, filing type/version, availability date and retention rights are required")
    available = date.fromisoformat(metadata["available_by"])
    if available > date.today():
        raise ValueError("A retained published filing cannot have a future availability date")
    sha = digest(content)
    # Document identity includes filing interpretation; repeated bytes cannot silently replace metadata.
    identity = digest({"sha256":sha, **{k:metadata[k] for k in required}})
    record = {k: str(v)[:2000] for k,v in metadata.items() if k in required or k in {"official_url", "issuer", "retention_policy"}}
    record.update(id=identity,sha256=sha,pages=pages,bytes=len(content),origin_id=sha,ingested_at=datetime.now(timezone.utc).isoformat())
    with connection() as conn:
        prof = conn.execute("SELECT status, generation FROM pre_ipo_company_profiles WHERE owner=? AND id=?", (owner, company)).fetchone()
        if not prof:
            tomb = conn.execute(
                "SELECT 1 FROM pre_ipo_tombstones WHERE owner=? AND company=? AND target_kind='COMPANY' AND action='DELETE'",
                (owner, company)
            ).fetchone()
            if tomb:
                raise ValueError(f"Company {company} does not exist or has been deleted")
            max_tomb_gen = conn.execute(
                "SELECT MAX(generation) FROM pre_ipo_tombstones WHERE owner=? AND company=? AND target_kind='COMPANY'",
                (owner, company)
            ).fetchone()[0] or 0
            new_gen = max_tomb_gen + 1
            default_payload = json.dumps({"name": company, "sector": "General", "history": []})
            conn.execute(
                "INSERT OR IGNORE INTO pre_ipo_company_profiles(owner, id, payload, generation, status) VALUES(?, ?, ?, ?, 'ACTIVE')",
                (owner, company, default_payload, new_gen)
            )
        elif prof[0] != "ACTIVE":
            raise ValueError(f"Company {company} is in state {prof[0]} and cannot accept new documents")

        max_src_tomb = conn.execute(
            "SELECT MAX(generation) FROM pre_ipo_tombstones WHERE owner=? AND company=? AND target_kind='SOURCE' AND target_id=?",
            (owner, company, identity)
        ).fetchone()[0] or 0
        src_gen = max_src_tomb + 1

        fam = metadata.get("family") or ("OFFER" if metadata.get("filing_type") in ("DRHP", "RHP") else "FINANCIAL")
        conn.execute("""
            INSERT OR REPLACE INTO pre_ipo_sources(owner, company, id, metadata, content, family, reporting_period, availability_date, generation, status)
            VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, 'ACTIVE')
        """, (owner, company, identity, dump(record), content, fam, metadata.get("reporting_period", "FY24"), metadata.get("available_by"), src_gen))
    return identity


def extract_pages(owner, role, company, source_id, first=1, count=10):
    """Explicit bounded native-text job; scanned pages remain OCR gaps, never zeros."""
    actor(owner,role)
    if count < 1 or count > 20:
        raise ValueError("Process between 1 and 20 pages per explicit batch")
    metadata, content = source(owner,company,source_id)
    if first < 1 or first > metadata["pages"]:
        raise ValueError("Page outside retained document")
    config = {"source_id":source_id,"first":first,"last":min(first+count-1,metadata["pages"]),"engine":"pypdf-native","schema":VERSION}
    run_id = digest(config)
    with connection() as conn:
        prior = conn.execute("SELECT payload FROM pre_ipo_extraction_runs WHERE owner=? AND company=? AND id=?",(owner,company,run_id)).fetchone()
        if prior:
            return json.loads(prior[0])
    from pypdf import PdfReader
    reader = PdfReader(io.BytesIO(content))
    pages=[]
    for number in range(first, config["last"]+1):
        try:
            text=reader.pages[number-1].extract_text() or ""
            pages.append({"page":number,"status":"TEXT_TRUNCATED" if len(text)>100000 else "TEXT_AVAILABLE" if text.strip() else "GAP-OCR-01","text":text[:100000],"text_truncated":len(text)>100000})
        except Exception as exc:
            pages.append({"page":number,"status":"EXTRACTION_FAILED","text":"","error":type(exc).__name__})
    run = {"id":run_id, **config,"pages":pages,"status":"COMPLETED_WITH_GAPS" if any(p["status"]!="TEXT_AVAILABLE" for p in pages) else "BATCH_COMPLETED", "scope":"Only the selected pages were processed; remaining pages are NOT_SEARCHED.","created_at":datetime.now(timezone.utc).isoformat()}
    with connection() as conn:
        conn.execute("INSERT OR IGNORE INTO pre_ipo_extraction_runs(owner,company,id,payload) VALUES(?,?,?,?)",(owner,company,run_id,dump(run)))
        return json.loads(conn.execute("SELECT payload FROM pre_ipo_extraction_runs WHERE owner=? AND company=? AND id=?",(owner,company,run_id)).fetchone()[0])


def runs(owner,company):
    actor(owner)
    with connection() as conn:
        return [json.loads(r[0]) for r in conn.execute("SELECT payload FROM pre_ipo_extraction_runs WHERE owner=? AND company=? ORDER BY id",(owner,company))]


def _validate_binding(conn, owner, company, fact):
    binding=fact.get("source",{})
    metadata, _ = _source(conn,owner,company,binding.get("id",""))
    if not isinstance(binding.get("page"),int) or not 1 <= binding["page"] <= metadata["pages"]:
        raise ValueError("Valid PDF page number required")
    if not binding.get("locator","").strip() or not binding.get("quote","").strip():
        raise ValueError("Table/footnote locator and exact source quotation required")
    if binding.get("sha256") != metadata["sha256"]:
        raise ValueError("Fact must bind to the retained source hash")
    for key in CONTEXT:
        if str(fact.get("context",{}).get(key,"")).strip().casefold() in {"", "not_established", "unknown", "not supplied"}:
            raise ValueError("Resolve semantic context: " + key)
    return metadata


def save_fact(owner, role, company, fact, expected_revision=0):
    actor(owner,role)
    candidate=json.loads(dump(fact))
    fact_id=candidate.get("id","").strip()
    if not fact_id or len(fact_id)>300:
        raise ValueError("Fact identifier required (up to 300 characters)")
    if candidate.get("presence") not in PRESENCE or candidate.get("origin") not in ORIGINS or candidate.get("review") not in REVIEW:
        raise ValueError("Invalid presence, origin or review state")
    if not candidate.get("reason","").strip():
        raise ValueError("Review/correction reason required")
    if candidate["presence"] == "OBSERVED_VALUE" and (candidate.get("value") is None or isinstance(candidate.get("value"),str) and not candidate["value"].strip()):
        raise ValueError("Observed value cannot be null")
    if candidate["presence"] != "OBSERVED_VALUE" and candidate.get("value") is not None:
        raise ValueError("Non-value presence must not carry a numeric/text value")
    if re.fullmatch(r"history\[\d+\]\.(?:\w+_cr|gross_margin_pct)",fact_id) and candidate["presence"]=="OBSERVED_VALUE":
        numeric(candidate["value"])
    if candidate["presence"] in {"NOT_DISCLOSED","NOT_APPLICABLE_CLAIMED"} and not candidate.get("search_scope","").strip():
        raise ValueError("Search/applicability scope and reason required")
    with connection() as conn:
        conn.execute("BEGIN IMMEDIATE")
        prior=conn.execute("SELECT revision,payload FROM pre_ipo_fact_events WHERE owner=? AND company=? AND fact_id=? ORDER BY revision DESC LIMIT 1",(owner,company,fact_id)).fetchone()
        if (prior[0] if prior else 0) != expected_revision:
            raise ValueError("Fact changed; reload before submitting")
        if prior:
            candidate["raw_value"]=json.loads(prior[1]).get("raw_value")
        else:
            candidate["raw_value"]=candidate.get("value")
        if candidate["review"]=="ACCEPTED":
            if candidate["origin"]=="LEGACY_EXAMPLE":
                raise ValueError("Legacy examples cannot be accepted as filing facts; propose a source-backed interpretation")
            if candidate["origin"] in {"FILING_FACT","EXTERNAL_BENCHMARK"}:
                metadata=_validate_binding(conn,owner,company,candidate)
                candidate["available_by"]=metadata["available_by"]
                candidate["origin_id"]=metadata["origin_id"]
            elif candidate["origin"]=="DERIVED":
                raise ValueError("Derived facts are produced by versioned calculations, not manual acceptance")
        candidate.update(revision=expected_revision+1,reviewer=owner,domain=candidate.get("domain",domain(fact_id)),updated_at=datetime.now(timezone.utc).isoformat())
        # No implicit sharing or second-review claims: this private workspace remains single-review.
        candidate["review_qualification"]="SINGLE_REVIEW"
        prof = conn.execute("SELECT status, generation FROM pre_ipo_company_profiles WHERE owner=? AND id=?", (owner, company)).fetchone()
        if not prof:
            tomb = conn.execute(
                "SELECT 1 FROM pre_ipo_tombstones WHERE owner=? AND company=? AND target_kind='COMPANY' AND action='DELETE'",
                (owner, company)
            ).fetchone()
            if tomb:
                raise ValueError(f"Company {company} does not exist or has been deleted")
            max_tomb_gen = conn.execute(
                "SELECT MAX(generation) FROM pre_ipo_tombstones WHERE owner=? AND company=? AND target_kind='COMPANY'",
                (owner, company)
            ).fetchone()[0] or 0
            new_gen = max_tomb_gen + 1
            default_payload = json.dumps({"name": company, "sector": "General", "history": []})
            conn.execute(
                "INSERT OR IGNORE INTO pre_ipo_company_profiles(owner, id, payload, generation, status) VALUES(?, ?, ?, ?, 'ACTIVE')",
                (owner, company, default_payload, new_gen)
            )
            prof = ("ACTIVE", new_gen)
        elif prof[0] != "ACTIVE":
            raise ValueError(f"Company {company} is in state {prof[0]} and cannot accept updates")

        expected_gen = candidate.get("expected_generation")
        if expected_gen is not None and prof[1] != expected_gen:
            raise ValueError(f"Company generation changed (expected {expected_gen}, active {prof[1]}); reload before submitting")
        conn.execute("INSERT INTO pre_ipo_fact_events(owner,company,fact_id,revision,payload) VALUES(?,?,?,?,?)",(owner,company,fact_id,candidate["revision"],dump(candidate)))
        conn.execute("""
            INSERT OR REPLACE INTO pre_ipo_observations (
                owner, company, observation_id, revision, source_id, entity, metric_id,
                period, duration, basis, framework, currency, unit, value, presence,
                review_state, provenance_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            owner, company, fact_id, candidate["revision"],
            candidate.get("source", {}).get("id") or candidate.get("origin_id", "manual"),
            candidate.get("context", {}).get("entity", company),
            fact_id,
            candidate.get("context", {}).get("period"),
            candidate.get("context", {}).get("duration"),
            candidate.get("context", {}).get("basis"),
            candidate.get("context", {}).get("framework"),
            candidate.get("context", {}).get("currency"),
            candidate.get("context", {}).get("unit"),
            str(candidate.get("value")) if candidate.get("value") is not None else None,
            candidate.get("presence", "OBSERVED_VALUE"),
            candidate["review"],
            dump(candidate.get("source", {}))
        ))
    return candidate


def valid_facts(owner, company, cutoff=None):
    """Revalidate bytes and context; review booleans from callers confer no authority."""
    actor(owner)
    result=[]
    with connection() as conn:
        for item in _as_of(conn,owner,company,cutoff):
            if item["review"]!="ACCEPTED" or item["origin"]!="FILING_FACT" or item["presence"]!="OBSERVED_VALUE":
                continue
            try:
                metadata=_validate_binding(conn,owner,company,item)
                if cutoff and date.fromisoformat(metadata["available_by"]) > date.fromisoformat(cutoff):
                    continue
            except ValueError:
                continue
            result.append(item)
    return result


def legacy_conflicts(dossier):
    """Nominal FY checks only; original-document/basis equivalence not established."""
    mapping={"SALES":"revenue_ops_cr","OP_PROFIT":"ebitda_cr","PAT":"pat_cr","CFO":"cfo_cr","CAPEX":"capex_cr","FCF":"fcf_cr","NET_WORTH":"net_worth_cr","TOTAL_ASSETS":"total_assets_cr"}
    output=[]
    for row in dossier.cmie_crosswalk:
        metric=mapping.get(row.cmie_field_code)
        period=re.search(r"\bFY\s*(\d{2,4})\b",row.drhp_raw_value,re.I)
        amount=re.search(r"(-)?(?:Rs\.?\s*)?([\d,]+(?:\.\d+)?)\s*Cr",row.cmie_normalized_value,re.I)
        if not(metric and period and amount):
            continue
        for i,item in enumerate(dossier.history):
            if item.fiscal_year[-2:]!=period[1][-2:]:
                continue
            value=getattr(item,metric)
            other=numeric(amount[2])*(-1 if amount[1] else 1)
            if value is None or abs(numeric(value)-other)>Decimal("0.02"):
                output.append({"fact_id":f"history[{i}].{metric}","period":item.fiscal_year,"history_value":value,"crosswalk_candidate":str(other),"state":"VALUE_ABSENT_IN_HISTORY" if value is None else "UNRESOLVED_INTERNAL_DIFFERENCE","reason":"Nominal FY only: source version, basis and definition require review; neither value is selected automatically."})
    return output


def add_action(owner,role,company,action):
    actor(owner,role)
    if not all(str(action.get(k,"")).strip() for k in ("question","next_action","assignee","due")):
        raise ValueError("Question, next action, owner and due date required")
    date.fromisoformat(action["due"])
    payload={**action,"created_at":datetime.now(timezone.utc).isoformat()}
    key=digest(action)
    with connection() as conn:
        conn.execute("INSERT OR IGNORE INTO pre_ipo_evidence_actions(owner,company,id,payload) VALUES(?,?,?,?)",(owner,company,key,dump(payload)))
    return key


def actions(owner,company):
    actor(owner)
    with connection() as conn:
        return _actions(conn,owner,company)


def _actions(conn,owner,company):
    result=[]
    for row in conn.execute("SELECT id,payload FROM pre_ipo_evidence_actions WHERE owner=? AND company=? ORDER BY id",(owner,company)):
        events=[json.loads(r[0]) for r in conn.execute("SELECT payload FROM pre_ipo_evidence_action_events WHERE owner=? AND company=? AND action_id=? ORDER BY revision",(owner,company,row[0]))]
        result.append({**json.loads(row[1]),"id":row[0],"status":events[-1]["status"] if events else "OPEN","revision":len(events),"events":events})
    return result


def transition_action(owner,role,company,action_id,status,reason,expected_revision):
    actor(owner,role)
    if status not in {"OPEN","COMPLETED","CANCELLED"} or not reason.strip():
        raise ValueError("Valid action status and disposition reason required")
    with connection() as conn:
        conn.execute("BEGIN IMMEDIATE")
        if not conn.execute("SELECT 1 FROM pre_ipo_evidence_actions WHERE owner=? AND company=? AND id=?",(owner,company,action_id)).fetchone():
            raise ValueError("Owned action required")
        revision=conn.execute("SELECT MAX(revision) FROM pre_ipo_evidence_action_events WHERE owner=? AND company=? AND action_id=?",(owner,company,action_id)).fetchone()[0] or 0
        if revision!=expected_revision:
            raise ValueError("Action changed; reload before updating")
        event={"status":status,"reason":reason,"revision":revision+1,"reviewer":owner,"created_at":datetime.now(timezone.utc).isoformat()}
        conn.execute("INSERT INTO pre_ipo_evidence_action_events(owner,company,action_id,revision,payload) VALUES(?,?,?,?,?)",(owner,company,action_id,revision+1,dump(event)))
    return event


def reference_import(owner,role,content,version,rights):
    actor(owner,role)
    import csv
    if len(content)>5*1024*1024 or not version.strip() or not rights.strip():
        raise ValueError("Reference up to 5 MB, version and permitted-use declaration required")
    text=content.decode("utf-8-sig")
    if not text.strip():
        raise ValueError("Reference is empty")
    reader=csv.DictReader(io.StringIO(text),delimiter="|" if text.splitlines()[0].count("|")>=2 else ",")
    if not {"Table","Field Name","Indicator"} <= set(reader.fieldnames or ()):
        raise ValueError("Reference requires Table, Field Name, Indicator columns")
    rows=list(reader)
    keys=[(r["Table"],r["Field Name"]) for r in rows]
    if len(rows)>20000 or len(set(keys))!=len(keys) or any(not all(k) for k in keys):
        raise ValueError("Invalid, duplicate or excessive table-qualified reference keys")
    record={"id":digest(content),"version":version,"rights":rights,"rows":rows,"tables":len(set(k[0] for k in keys)),"qualification":"Catalogue metadata only; complete definitions, units and licensed company values are not established."}
    with connection() as conn:
        prior=conn.execute("SELECT payload FROM pre_ipo_reference_versions WHERE owner=? AND id=?",(owner,record["id"])).fetchone()
        if prior and json.loads(prior[0])["version"]!=version:
            raise ValueError("Identical reference bytes already registered under another version")
        conn.execute("INSERT OR IGNORE INTO pre_ipo_reference_versions(owner,id,payload) VALUES(?,?,?)",(owner,record["id"],dump(record)))
    return record["id"]


def references(owner):
    actor(owner)
    with connection() as conn:
        return [json.loads(r[0]) for r in conn.execute("SELECT payload FROM pre_ipo_reference_versions WHERE owner=? ORDER BY id",(owner,))]


def map_reference(owner,role,company,fact_id,revision,reference_id,table,field,reason):
    """A reviewed catalogue candidate, never a vendor-value reconciliation."""
    actor(owner,role)
    ref=next((r for r in references(owner) if r["id"]==reference_id),None)
    if not ref or not any(r["Table"]==table and r["Field Name"]==field for r in ref["rows"]):
        raise ValueError("Table-qualified field not present in the selected reference version")
    item=next((r for r in facts(owner,company) if r["id"]==fact_id),None)
    if not item or not reason.strip():
        raise ValueError("Existing fact and candidate-mapping rationale required")
    item["mapping"]={"reference_id":reference_id,"reference_version":ref["version"],"table":table,"field":field,"state":"DEFINITION_REQUIRED","reason":reason,"qualification":"Catalogue candidate only; no verified provider observation or accounting equivalence."}
    item["reason"]="Reference candidate: "+reason
    return save_fact(owner,role,company,item,revision)


def snapshot(owner,role,company,dossier,cutoff):
    actor(owner,role)
    from models.pre_ipo_evidence_analysis import assess
    date.fromisoformat(cutoff)
    with connection() as conn:
        # One read/write transaction freezes all bindings and outputs together.
        conn.execute("BEGIN IMMEDIATE")
        reference_rows=[json.loads(r[0]) for r in conn.execute("SELECT payload FROM pre_ipo_reference_versions WHERE owner=?",(owner,))]
        retained=[json.loads(r[0]) for r in conn.execute("SELECT metadata FROM pre_ipo_sources WHERE owner=? AND company=?",(owner,company))]
        eligible_sources={s["id"] for s in retained if s["available_by"]<=cutoff}
        frozen_facts=[f for f in _as_of(conn,owner,company,cutoff) if not f.get("source",{}).get("id") or f["source"]["id"] in eligible_sources]
        payload={"version":VERSION,"company":company,"company_name":dossier.company_name,"cutoff":cutoff,"evidence_mode":"public_as_of_research","facts":frozen_facts,"sources":[s for s in retained if s["id"] in eligible_sources],"reference_versions":[{"id":r["id"],"version":r["version"]} for r in reference_rows],"actions":_actions(conn,owner,company),"review_policy":"SINGLE_REVIEW: no independent audit opinion", "created_at":datetime.now(timezone.utc).isoformat()}
        payload["assessment"]=assess(owner,company,dossier,cutoff)
        payload["id"]=digest(payload)
        conn.execute("INSERT INTO pre_ipo_evidence_snapshots(owner,company,id,payload) VALUES(?,?,?,?)",(owner,company,payload["id"],dump(payload)))
    return payload


def dossier(owner, company):
    return companies(owner)[company]


def freeze_snapshot(owner, role, company, cutoff):
    actor(owner, role)
    dossier = companies(owner)[company]
    snap = snapshot(owner, role, company, dossier, cutoff)
    return snap["id"]


def get_snapshot(owner, company, snap_id):
    actor(owner)
    with connection() as conn:
        row = conn.execute("SELECT payload FROM pre_ipo_evidence_snapshots WHERE owner=? AND company=? AND id=?", (owner, company, snap_id)).fetchone()
        return json.loads(row[0]) if row else None


def snapshots(owner,company):
    actor(owner)
    with connection() as conn:
        return [json.loads(r[0]) for r in conn.execute("SELECT payload FROM pre_ipo_evidence_snapshots WHERE owner=? AND company=? ORDER BY created_at DESC,id",(owner,company))]
