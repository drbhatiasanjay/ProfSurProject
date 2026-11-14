"""
Pre-IPO Analytical Capability Gate (PR 1 — P0 Containment & Codex Standard)
Provides fail-closed capability-specific gating for Pre-IPO analysis:
- Blocks built-in registry dossiers from bypassing evidence review (P0-01)
- Blocks unpriced offer valuation and market cap computation (P0-03)
- Blocks unsupported WACC, ROIC, and reverse DCF estimation (P0-07)
- Blocks automated investment committee approvals and agency ratings (P0-08)
- Rejects LEGACY_EXAMPLE origins from analysis eligibility (P1-02)
- Enforces strict relational authority and 3-way hash equality on analytical export
"""

import os
import re
from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional, Dict, Any


class CapabilityType(str, Enum):
    FINANCIAL_ANALYSIS = "FINANCIAL_ANALYSIS"
    VALUATION = "VALUATION"
    WACC_ROIC = "WACC_ROIC"
    REVERSE_DCF = "REVERSE_DCF"
    RECOMMENDATIONS = "RECOMMENDATIONS"
    BOARD_DECK_EXPORT = "BOARD_DECK_EXPORT"


class ExportBlockedError(Exception):
    """Raised when an analytical export is attempted on unreviewed, blocked, or hash-mismatched data."""
    pass


def is_valid_hex_sha256(val: Optional[str]) -> bool:
    """Validate that val is a lowercase 64-character hexadecimal SHA-256 hash."""
    if not val or not isinstance(val, str):
        return False
    return bool(re.match(r"^[0-9a-f]{64}$", val))


def is_demo_mode_active() -> bool:
    """Check if demo fixture mode is active via PROFSUR_DEMO_FIXTURE_MODE=1 or ENVIRONMENT=demo."""
    env = os.environ.get("ENVIRONMENT", "").lower()
    fixture_flag = os.environ.get("PROFSUR_DEMO_FIXTURE_MODE", "")
    return fixture_flag == "1" or "demo" in env or "profsur_demo_fixture_mode=1" in env


def is_hcch_entity(company_identifier: str = "", company_name: str = "", cin: str = "") -> bool:
    """Robust detection of Hindustan Coca-Cola across keys, names, and regulatory CIN."""
    blob = f"{company_identifier} {company_name} {cin}".lower().replace("-", "_")
    return any(k in blob for k in ("coca_cola", "coca cola", "hcch", "hccb", "u15549dl1997ptc085183"))


def _get_persisted_snapshot_data(
    snapshot_id: Optional[str],
    owner: Optional[str],
    company: Optional[str],
    conn: Optional[Any] = None,
) -> Optional[Dict[str, Any]]:
    """
    Strictly scoped persistence resolver for evidence snapshots.
    Scopes query strictly by exact (id, owner, company) equality.
    Removes fuzzy company matching and default owner behavior.
    Requires relational columns: status, snapshot_hash, accepted_by, accepted_at.
    Treats relational fields as authoritative over JSON payload.
    Duplicate keys in payload must strictly match relational fields.
    Validates lowercase 64-char hex SHA-256 hash (never row ID fallback).
    Fail-closed: Returns None if snapshot_id, owner, or company is absent/blank,
    not found, or DB/schema validation fails.
    """
    if not snapshot_id or not isinstance(snapshot_id, str) or not snapshot_id.strip():
        return None
    if not owner or not isinstance(owner, str) or not owner.strip():
        return None
    if not company or not isinstance(company, str) or not company.strip():
        return None

    db_conn = conn
    close_after = False
    if db_conn is None:
        try:
            from db import get_connection
            db_conn = get_connection()
            close_after = True
        except Exception:
            return None

    try:
        # Check relational columns exist in table schema
        cursor = db_conn.execute("PRAGMA table_info(pre_ipo_evidence_snapshots)")
        cols = {row[1] for row in cursor.fetchall()}
        required_cols = {"id", "owner", "company", "payload", "status", "snapshot_hash", "accepted_by", "accepted_at"}
        if not required_cols.issubset(cols):
            return None

        # Scoped query strictly by exact (id, owner, company) equality
        cursor = db_conn.execute(
            "SELECT id, owner, company, payload, status, snapshot_hash, accepted_by, accepted_at "
            "FROM pre_ipo_evidence_snapshots WHERE id=? AND owner=? AND company=?",
            (snapshot_id.strip(), owner.strip(), company.strip())
        )
        row = cursor.fetchone()
        if not row:
            return None

        r_id, r_owner, r_company, payload_raw, r_status, r_hash, r_accepted_by, r_accepted_at = row

        import json
        if isinstance(payload_raw, str):
            try:
                payload = json.loads(payload_raw)
            except Exception:
                return None
        elif isinstance(payload_raw, dict):
            payload = payload_raw
        else:
            return None

        # Relational fields are strictly authoritative
        rel_status = str(r_status) if r_status is not None else "UNREVIEWED"
        rel_hash = str(r_hash) if r_hash is not None else ""
        rel_by = str(r_accepted_by) if r_accepted_by is not None else ""
        rel_at = str(r_accepted_at) if r_accepted_at is not None else ""

        # Require exact agreement if duplicate fields exist in payload
        if "status" in payload and str(payload["status"]) != rel_status:
            return None
        if "snapshot_hash" in payload and str(payload["snapshot_hash"]) != rel_hash:
            return None
        if "owner" in payload and str(payload["owner"]) != r_owner:
            return None
        if "company" in payload and str(payload["company"]) != r_company:
            return None

        # Status validation: Only ACCEPTED_FOR_ANALYSIS is accepted (generic ACCEPTED is rejected)
        # In demo-fixture mode (PROFSUR_DEMO_FIXTURE_MODE=1), DEMO_ACCEPTED_TEST_ONLY is also authorized
        import os
        is_demo_mode = is_demo_mode_active()
        allowed_statuses = {"ACCEPTED_FOR_ANALYSIS"}
        if is_demo_mode:
            allowed_statuses.add("DEMO_ACCEPTED_TEST_ONLY")

        if rel_status in allowed_statuses:
            if not is_valid_hex_sha256(rel_hash):
                return None
            if not rel_by.strip():
                return None
            if not rel_at.strip():
                return None

        return {
            "id": r_id,
            "owner": r_owner,
            "company": r_company,
            "payload": payload,
            "status": rel_status,
            "snapshot_hash": rel_hash,
            "accepted_by": rel_by,
            "accepted_at": rel_at,
        }
    except Exception:
        return None
    finally:
        if close_after and db_conn:
            try:
                db_conn.close()
            except Exception:
                pass


@dataclass(frozen=True)
class CapabilityDecision:
    allowed: bool
    capability: CapabilityType
    status: str  # ACCEPTED_FOR_ANALYSIS | BLOCKED | NOT_PERMITTED
    reason: str
    next_action: str
    snapshot_id: Optional[str] = None
    snapshot_hash: Optional[str] = None
    blocked_metrics: List[str] = field(default_factory=list)


def evaluate_capability_gate(
    owner: str,
    company: str,
    capability: CapabilityType,
    snapshot_id: Optional[str] = None,
    snapshot_hash: Optional[str] = None,
    snapshot_status: Optional[str] = None,
    origin: Optional[str] = None,
    is_production: bool = True,
    allow_synthetic_examples: bool = False,
    is_unpriced: bool = False,
    cin: str = "",
    conn: Optional[Any] = None,
) -> CapabilityDecision:
    """
    Evaluates whether an analytical capability is authorized to run.
    Strict fail-closed architecture:
    1. Recommendation / Approval ban (P0-08) is unconditional and evaluated first.
    2. LEGACY_EXAMPLE is never accepted for analytical processing (P1-02).
    3. HCCH is blocked from unreviewed production analysis (P0-01) regardless of selector avenue.
    4. Persistence verification: scopes by exact (id, owner, company); binds caller hash to persisted hash.
    5. Any unreviewed snapshot status blocks analytical capabilities.
    6. Unpriced filings block valuation, WACC, and reverse DCF (P0-03/P0-07).
    """
    # 1. Recommendation / Approval ban (P0-08) is unconditional
    if capability == CapabilityType.RECOMMENDATIONS:
        return CapabilityDecision(
            allowed=False,
            capability=capability,
            status="BLOCKED",
            reason="Automated investment committee approvals, agency credit ratings, and definitive anchor recommendations are strictly prohibited under P0-08 (unreviewed automated decisions not accepted).",
            next_action="Refer to factual diligence observations, risk factor catalog, and neutral decision support summary only.",
            snapshot_id=snapshot_id,
            snapshot_hash=snapshot_hash,
            blocked_metrics=["ic_verdict", "rating_grade", "recommendation_action"],
        )

    # 2. Reject LEGACY_EXAMPLE unconditionally
    if origin == "LEGACY_EXAMPLE":
        return CapabilityDecision(
            allowed=False,
            capability=capability,
            status="BLOCKED",
            reason="LEGACY_EXAMPLE origin is strictly prohibited from analytical processing or evidence derivation under P1-02.",
            next_action="Ingest official regulatory filing into evidence repository and complete audit review.",
            snapshot_id=snapshot_id,
            snapshot_hash=snapshot_hash,
            blocked_metrics=["*"],
        )

    # 3. Block production HCCH across all identifier avenues (key, name, CIN) without accepted snapshot (P0-01)
    is_hcch = is_hcch_entity(company, company, cin)
    if is_hcch and (origin == "LEGACY_REGISTRY" or not snapshot_id):
        return CapabilityDecision(
            allowed=False,
            capability=capability,
            status="BLOCKED",
            reason="Production HCCH analysis from unreviewed built-in registry is blocked under P0-01 containment. Real analysis requires an accepted evidence snapshot.",
            next_action="Ingest official 513-page DRHP and complete evidence review in Tab 2 Provenance Ledger.",
            snapshot_id=snapshot_id,
            snapshot_hash=snapshot_hash,
            blocked_metrics=["valuation", "wacc", "roic", "dcf", "recommendations", "board_deck"],
        )

    # 4. Persistence verification: never trust caller-supplied snapshot_status in production
    effective_status = snapshot_status
    if is_production and snapshot_id:
        persisted = _get_persisted_snapshot_data(snapshot_id, owner, company, conn=conn)
        if persisted is None:
            return CapabilityDecision(
                allowed=False,
                capability=capability,
                status="BLOCKED",
                reason=f"Evidence snapshot '{snapshot_id}' does not exist in persistence for owner '{owner}' and company '{company}'. Unpersisted or spoofed snapshot IDs are strictly rejected.",
                next_action="Persist and audit candidate observations in Tab 2 Provenance Ledger.",
                snapshot_id=snapshot_id,
                snapshot_hash=snapshot_hash,
                blocked_metrics=["*"],
            )
        effective_status = persisted.get("status")
        persisted_hash = persisted.get("snapshot_hash")

        # Bind caller-supplied hash to persisted hash
        if snapshot_hash:
            if snapshot_hash != persisted_hash:
                return CapabilityDecision(
                    allowed=False,
                    capability=capability,
                    status="BLOCKED",
                    reason=f"Caller-supplied snapshot hash '{snapshot_hash}' does not match persisted hash '{persisted_hash}'.",
                    next_action="Verify snapshot hash integrity in Tab 2 Provenance Ledger.",
                    snapshot_id=snapshot_id,
                    snapshot_hash=snapshot_hash,
                    blocked_metrics=["*"],
                )
        else:
            snapshot_hash = persisted_hash

        import os
        is_demo_mode = is_demo_mode_active()
        allowed_statuses = {"ACCEPTED_FOR_ANALYSIS"}
        if is_demo_mode:
            allowed_statuses.add("DEMO_ACCEPTED_TEST_ONLY")

        if effective_status not in allowed_statuses:
            return CapabilityDecision(
                allowed=False,
                capability=capability,
                status="BLOCKED",
                reason=f"Evidence snapshot '{snapshot_id}' is unreviewed or in status '{effective_status or 'UNREVIEWED'}'. Only ACCEPTED_FOR_ANALYSIS snapshots are eligible for analytical processing.",
                next_action="Audit and accept all candidate observations in Tab 2 Provenance Ledger to authorize downstream analysis.",
                snapshot_id=snapshot_id,
                snapshot_hash=snapshot_hash,
                blocked_metrics=["*"],
            )
    elif is_production and not snapshot_id:
        # Non-HCCH demonstration issuers (DEMONSTRATION_LEGACY / DEMO_DOSSIER) preserve demonstration analysis without snapshot
        if origin not in ("DEMONSTRATION_LEGACY", "DEMO_DOSSIER"):
            return CapabilityDecision(
                allowed=False,
                capability=capability,
                status="BLOCKED",
                reason="Production analysis requires an accepted evidence snapshot in persistence.",
                next_action="Audit and accept candidate observations in Tab 2 Provenance Ledger to authorize downstream analysis.",
                snapshot_id=None,
                snapshot_hash=None,
                blocked_metrics=["*"],
            )

    # 5. Unpriced book-building circuit breaker (P0-03, P0-07)
    if is_unpriced and capability in (CapabilityType.VALUATION, CapabilityType.WACC_ROIC, CapabilityType.REVERSE_DCF):
        return CapabilityDecision(
            allowed=False,
            capability=capability,
            status="BLOCKED_MISSING_REVIEWED_PRICE_BAND",
            reason="Unpriced DRHP with undisclosed issue price under SEBI ICDR 2018 Regulation 26(1). Valuation, WACC, and reverse DCF hurdles cannot be computed without accepted price.",
            next_action="Utilize interactive scenario pricing sandbox or await RHP book-building price band disclosure.",
            snapshot_id=snapshot_id,
            snapshot_hash=snapshot_hash,
            blocked_metrics=["issue_price", "market_cap", "ev_ebitda", "implied_pe", "wacc_pct", "reverse_dcf_growth"],
        )

    # Approved capability
    return CapabilityDecision(
        allowed=True,
        capability=capability,
        status="ACCEPTED_FOR_ANALYSIS",
        reason="Evidence snapshot accepted with full source provenance.",
        next_action="Ready for analytical presentation.",
        snapshot_id=snapshot_id,
        snapshot_hash=snapshot_hash,
    )


def assert_export_allowed(
    dossier: Any,
    snapshot_id: Optional[str] = None,
    snapshot_status: Optional[str] = None,
    snapshot_hash: Optional[str] = None,
    result_snapshot_hash: Optional[str] = None,
    is_production: bool = True,
    owner: Optional[str] = None,
    company: Optional[str] = None,
    conn: Optional[Any] = None,
) -> None:
    """
    Fail-closed exporter assertion:
    Verifies that the dossier and snapshot are authorized for presentation/export.
    Resolves snapshot strictly from persistence; never trusts arbitrary caller-provided status strings.
    Requires explicit authenticated owner and exact company matching.
    Enforces 3-way hash equality: persisted_hash == snapshot_hash == result_snapshot_hash.
    Accepts strictly status ACCEPTED_FOR_ANALYSIS (rejects generic ACCEPTED).
    Raises ExportBlockedError if unreviewed, blocked, nonexistent, or hash mismatch occurs.
    """
    company_name = getattr(dossier, "company_name", str(dossier))
    deal_id = getattr(dossier, "deal_id", "")
    target_company = company or deal_id or company_name

    # In production, analytical export unconditionally requires verified persistence & 3-way hash equality
    if is_production:
        effective_owner = owner or ""
        if not snapshot_id:
            raise ExportBlockedError(
                f"Export blocked: snapshot_id required for verified analytical export of {company_name}."
            )

        persisted = _get_persisted_snapshot_data(
            snapshot_id=snapshot_id,
            owner=effective_owner,
            company=target_company,
            conn=conn,
        )

        if persisted is None:
            raise ExportBlockedError(
                f"Export blocked: verified evidence snapshot '{snapshot_id}' does not exist in persistence "
                f"for owner '{effective_owner}' and company '{target_company}'. "
                "Invented, unpersisted, un-scoped, or mock snapshot IDs are strictly rejected."
            )

        persisted_status = persisted.get("status")
        # FAIL-CLOSED: Snapshot status must be strictly ACCEPTED_FOR_ANALYSIS (or DEMO_ACCEPTED_TEST_ONLY in fixture mode)
        import os
        is_demo_mode = is_demo_mode_active()
        allowed_statuses = {"ACCEPTED_FOR_ANALYSIS"}
        if is_demo_mode:
            allowed_statuses.add("DEMO_ACCEPTED_TEST_ONLY")

        if persisted_status not in allowed_statuses:
            raise ExportBlockedError(
                f"Export blocked: snapshot '{snapshot_id}' in persistence has status '{persisted_status or 'UNREVIEWED'}'. "
                f"Only {allowed_statuses} snapshots may be exported."
            )

        persisted_hash = persisted.get("snapshot_hash")
        if not snapshot_hash or not result_snapshot_hash:
            raise ExportBlockedError(
                "Export blocked: snapshot_hash and result_snapshot_hash are mandatory for verified analytical exports."
            )
        if not is_valid_hex_sha256(snapshot_hash):
            raise ExportBlockedError(
                f"Export blocked: snapshot_hash '{snapshot_hash}' is not a valid 64-character lowercase hex SHA-256."
            )
        if snapshot_hash != result_snapshot_hash:
            raise ExportBlockedError(
                f"Export blocked: snapshot hash mismatch ({snapshot_hash} != {result_snapshot_hash}). "
                "Data integrity validation failed."
            )
        if snapshot_hash != persisted_hash:
            raise ExportBlockedError(
                f"Export blocked: provided snapshot hash '{snapshot_hash}' does not match persisted hash '{persisted_hash}'."
            )

    # 3. Caller status sanity check
    import os
    is_demo_mode = is_demo_mode_active()
    allowed_statuses = {"ACCEPTED_FOR_ANALYSIS"}
    if is_demo_mode:
        allowed_statuses.add("DEMO_ACCEPTED_TEST_ONLY")

    if snapshot_status and snapshot_status not in allowed_statuses:
        raise ExportBlockedError(
            f"Export blocked: snapshot status is '{snapshot_status}'. Only {allowed_statuses} data may be exported."
        )

    # 4. Hash verification if hashes are supplied
    if snapshot_hash and result_snapshot_hash and snapshot_hash != result_snapshot_hash:
        raise ExportBlockedError(
            f"Export blocked: snapshot hash mismatch ({snapshot_hash} != {result_snapshot_hash}). "
            "Data integrity validation failed."
        )
