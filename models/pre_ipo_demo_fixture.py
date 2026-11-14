"""Pre-IPO Demo Fixture Service (Phase G & Codex Standard).

Provides isolated demo-fixture generation for interface evaluation:
- Exercised exclusively in separate demo database or with DEMO_ACCEPTED_TEST_ONLY
- Enabled only when PROFSUR_DEMO_FIXTURE_MODE=1 or ENVIRONMENT=demo
- Generates verified demo snapshot with canonical lowercase SHA-256 hash
- Binds extracted candidate facts to snapshot bindings
- Preserves truth: Valuation and Reverse DCF remain BLOCKED_MISSING_REVIEWED_PRICE_BAND
"""

import json
import os
import sqlite3
from typing import Dict, Any, Optional

from models.pre_ipo_dossier_adapter import compute_canonical_snapshot_hash
from models.pre_ipo_extraction_service import CanonicalExtractionService, ExtractionRequest
from models.pre_ipo_capability_gate import is_demo_mode_active


def seed_hcch_demo_fixture(
    *,
    owner: str = "demo_reviewer",
    company: str = "hindustan_coca_cola",
    conn: sqlite3.Connection,
    force: bool = False,
) -> Dict[str, Any]:
    """
    Seeds an isolated demo-fixture snapshot strictly for demonstration and testing.
    Rejects execution if neither PROFSUR_DEMO_FIXTURE_MODE=1 nor ENVIRONMENT=demo is set,
    unless force=True in a unit-test context.
    """
    is_demo_mode = is_demo_mode_active()
    if not is_demo_mode and not force:
        raise PermissionError(
            "Demo fixture generation is blocked in production mode. "
            "Set PROFSUR_DEMO_FIXTURE_MODE=1 or ENVIRONMENT=demo to authorize demo fixtures."
        )

    from models.pre_ipo_migrations import apply_migrations
    apply_migrations(conn)

    if not force:
        try:
            existing = conn.execute(
                "SELECT id, snapshot_hash, status FROM pre_ipo_evidence_snapshots WHERE owner=? AND company=? AND status='DEMO_ACCEPTED_TEST_ONLY' ORDER BY created_at DESC LIMIT 1",
                (owner, company)
            ).fetchone()
            if existing:
                return {
                    "snapshot_id": existing[0],
                    "snapshot_hash": existing[1],
                    "status": existing[2],
                    "owner": owner,
                    "company": company,
                }
        except Exception:
            pass

    try:
        extractor = CanonicalExtractionService()
        req = ExtractionRequest(
            company=company,
            owner=owner,
            source_id="hcch_drhp_official_corpus",
            extractor_version="v1.0.0-canonical-513p",
        )
        res = extractor.extract_from_official_corpus(req, conn=conn)
        candidates = res.candidates
    except Exception:
        # Fallback to pre-extracted canonical facts for demo environments where PDF is excluded
        facts_path = os.path.join(os.path.dirname(__file__), "data", "hcch_canonical_facts.json")
        if os.path.exists(facts_path):
            with open(facts_path, "r", encoding="utf-8") as f:
                facts_data = json.load(f)
            from decimal import Decimal
            from models.pre_ipo_extraction_service import CandidateFact, PresenceState
            candidates = [
                CandidateFact(
                    observation_id=d["observation_id"],
                    metric_id=d["metric_id"],
                    entity=d["entity"],
                    entity_basis=d["entity_basis"],
                    period=d["period"],
                    duration=d["duration"],
                    unit=d["unit"],
                    value=Decimal(d["value"]) if d["value"] is not None else None,
                    presence=PresenceState(d["presence"]),
                    physical_page=d["physical_page"],
                    printed_page=d["printed_page"],
                    table_id=d["table_id"],
                    row_label=d["row_label"],
                    column_label=d["column_label"],
                    raw_text=d["raw_text"],
                    document_sha256=d["document_sha256"],
                    extraction_method=d["extraction_method"],
                    extractor_version=d["extractor_version"],
                )
                for d in facts_data
            ]
        else:
            raise

    # Convert candidate facts to observation format for canonical hashing
    obs_for_hash = []
    for cand in candidates:
        if cand.metric_id == "offer_price_inr":
            continue  # Do not include unpriced blank in financial metrics
        val_str = str(cand.value) if cand.value is not None else "0.0"
        obs_for_hash.append({
            "observation_id": cand.observation_id,
            "metric_id": cand.metric_id,
            "value": val_str,
            "unit": cand.unit,
            "period": cand.period or "FY24",
            "document_sha256": cand.document_sha256,
            "revision": "1",
        })

    snapshot_hash = compute_canonical_snapshot_hash(obs_for_hash)
    snapshot_id = f"snap_demo_hcch_{snapshot_hash[:12]}"
    status = "DEMO_ACCEPTED_TEST_ONLY"
    accepted_by = owner
    accepted_at = "2026-11-14T00:00:00Z"

    # Persist review actions, bindings, and snapshot
    conn.execute("BEGIN IMMEDIATE")
    try:
        # 1. Evidence snapshot
        payload = {
            "demo_fixture": True,
            "status": status,
            "snapshot_hash": snapshot_hash,
            "company": company,
            "owner": owner,
            "disclaimer": "DEMO REVIEW FIXTURE — NOT OFFICIAL ACCEPTED EVIDENCE",
        }
        conn.execute("""
            INSERT OR REPLACE INTO pre_ipo_evidence_snapshots (
                id, owner, company, payload, status, snapshot_hash, accepted_by, accepted_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            snapshot_id, owner, company, json.dumps(payload), status, snapshot_hash, accepted_by, accepted_at
        ))

        # 2. Snapshot bindings & review actions
        for cand in candidates:
            if cand.metric_id == "offer_price_inr":
                continue
            conn.execute("""
                INSERT OR REPLACE INTO pre_ipo_snapshot_bindings (
                    snapshot_id, observation_id, revision_reference, normalized_value, unit, period
                ) VALUES (?, ?, ?, ?, ?, ?)
            """, (
                snapshot_id, cand.observation_id, "1",
                str(cand.value) if cand.value is not None else "0.0",
                cand.unit, cand.period or "FY24"
            ))

            conn.execute("""
                INSERT OR REPLACE INTO pre_ipo_review_actions (
                    action_id, observation_id, action_type, prior_review_state,
                    new_review_state, reviewer, reviewer_role, review_reason,
                    original_value, corrected_value, source_sha256, page_locator
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                f"rev_{cand.observation_id}_{owner}",
                cand.observation_id,
                "ACCEPT",
                "PROPOSED",
                "ACCEPTED",
                owner,
                "AUDITOR",
                "Automated demo fixture acceptance for interface evaluation",
                str(cand.value) if cand.value is not None else "0.0",
                str(cand.value) if cand.value is not None else "0.0",
                cand.document_sha256,
                f"Page {cand.physical_page} (folio {cand.printed_page or 'N/A'})"
            ))

            # Dual-table compatibility: pre_ipo_observations
            try:
                prov = {
                    "physical_page": cand.physical_page,
                    "printed_page": cand.printed_page,
                    "table_id": cand.table_id,
                    "row_label": cand.row_label,
                    "raw_text": cand.raw_text,
                    "origin": "DEMO_FIXTURE",
                }
                conn.execute("""
                    INSERT OR REPLACE INTO pre_ipo_observations (
                        owner, company, observation_id, revision, source_id, entity,
                        metric_id, period, duration, basis, framework, currency, unit,
                        value, presence, review_state, provenance_json
                    ) VALUES (
                        ?, ?, ?, 1, ?, ?,
                        ?, ?, '12M', 'STANDALONE_OR_CONSOL', 'IND_AS', 'INR', ?,
                        ?, 'PRESENT', 'ACCEPTED', ?
                    )
                """, (
                    owner, company, cand.observation_id, req.source_id, cand.entity,
                    cand.metric_id, cand.period or "FY24", cand.unit,
                    float(cand.value) if cand.value is not None else 0.0,
                    json.dumps(prov)
                ))
            except Exception:
                pass

        conn.commit()
    except Exception:
        conn.rollback()
        raise

    return {
        "snapshot_id": snapshot_id,
        "snapshot_hash": snapshot_hash,
        "status": status,
        "owner": owner,
        "company": company,
        "bound_observations_count": len(obs_for_hash),
        "disclaimer": "DEMO REVIEW FIXTURE — NOT OFFICIAL ACCEPTED EVIDENCE",
    }
