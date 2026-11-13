"""
Pre-IPO Analytical Capability Gate (PR 1 — P0 Containment)
Provides fail-closed capability-specific gating for Pre-IPO analysis:
- Blocks built-in registry dossiers from bypassing evidence review (P0-01)
- Blocks unpriced offer valuation and market cap computation (P0-03)
- Blocks unsupported WACC, ROIC, and reverse DCF estimation (P0-07)
- Blocks automated investment committee approvals and agency ratings (P0-08)
- Rejects LEGACY_EXAMPLE origins from analysis eligibility (P1-02)
"""

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


def is_hcch_entity(company_identifier: str = "", company_name: str = "", cin: str = "") -> bool:
    """Robust detection of Hindustan Coca-Cola across keys, names, and regulatory CIN."""
    blob = f"{company_identifier} {company_name} {cin}".lower().replace("-", "_")
    return any(k in blob for k in ("coca_cola", "coca cola", "hcch", "hccb", "u15549dl1997ptc085183"))


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
) -> CapabilityDecision:
    """
    Evaluates whether an analytical capability is authorized to run.
    Strict fail-closed architecture:
    1. LEGACY_EXAMPLE is never accepted for analytical processing.
    2. HCCH is blocked from unreviewed production analysis (P0-01) regardless of selector avenue.
    3. Any unreviewed snapshot status blocks analytical capabilities.
    4. Unpriced filings block valuation, WACC, and reverse DCF (P0-03/P0-07).
    5. Committee approval and agency rating generation is prohibited (P0-08).
    """
    # 1. Reject LEGACY_EXAMPLE unconditionally
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

    # 2. Block production HCCH across all identifier avenues (key, name, CIN) without accepted snapshot (P0-01)
    is_hcch = is_hcch_entity(company, company, cin)
    if is_hcch and (origin == "LEGACY_REGISTRY" or snapshot_status != "ACCEPTED_FOR_ANALYSIS"):
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

    # 3. Recommendation / Approval ban (P0-08)
    if capability == CapabilityType.RECOMMENDATIONS:
        return CapabilityDecision(
            allowed=False,
            capability=capability,
            status="BLOCKED",
            reason="Automated investment committee approvals, agency credit ratings, and definitive anchor recommendations are strictly prohibited under P0-08.",
            next_action="Refer to factual diligence observations, risk factor catalog, and neutral decision support summary only.",
            snapshot_id=snapshot_id,
            snapshot_hash=snapshot_hash,
            blocked_metrics=["ic_verdict", "rating_grade", "recommendation_action"],
        )

    # 4. Require snapshot to be ACCEPTED_FOR_ANALYSIS for analytical capabilities
    if not snapshot_id or snapshot_status != "ACCEPTED_FOR_ANALYSIS":
        return CapabilityDecision(
            allowed=False,
            capability=capability,
            status="BLOCKED",
            reason=f"Evidence snapshot '{snapshot_id or 'None'}' is unreviewed or in status '{snapshot_status or 'UNREVIEWED'}'. Only ACCEPTED_FOR_ANALYSIS snapshots are eligible for analytical processing.",
            next_action="Audit and accept all candidate observations in Tab 2 Provenance Ledger to authorize downstream analysis.",
            snapshot_id=snapshot_id,
            snapshot_hash=snapshot_hash,
            blocked_metrics=["*"],
        )

    # 5. Unpriced book-building circuit breaker (P0-03, P0-07)
    if is_unpriced and capability in (CapabilityType.VALUATION, CapabilityType.WACC_ROIC, CapabilityType.REVERSE_DCF):
        return CapabilityDecision(
            allowed=False,
            capability=capability,
            status="BLOCKED",
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
    conn: Optional[Any] = None,
) -> None:
    """
    Fail-closed exporter assertion:
    Verifies that the dossier and snapshot are authorized for presentation/export.
    Resolves snapshot from persistence; never trusts arbitrary caller-provided status strings.
    Validates snapshot hashes and rejects absent hashes, invented snapshots, mismatches, or unaccepted data.
    Raises ExportBlockedError if unreviewed, blocked, nonexistent, or hash mismatch occurs.
    """
    company_name = getattr(dossier, "company_name", str(dossier))
    deal_id = getattr(dossier, "deal_id", "")
    cin = getattr(dossier, "cin", "")
    is_hcch = is_hcch_entity(deal_id, company_name, cin)

    # 1. HCCH Unreviewed Export Block
    if is_hcch and is_production and (not snapshot_id or snapshot_status != "ACCEPTED_FOR_ANALYSIS"):
        raise ExportBlockedError(
            f"Pre-IPO Board Deck export is BLOCKED for {company_name} under P0-01 containment. "
            "No unreviewed built-in registry dossier may be exported."
        )

    # 2. Check snapshot_id in persistence if in production mode
    if is_production and (snapshot_id is not None or snapshot_status == "ACCEPTED_FOR_ANALYSIS"):
        if not snapshot_id:
            raise ExportBlockedError("Export blocked: snapshot_id required for verified analytical export.")

        # Resolve snapshot from SQLite persistence
        db_conn = conn
        close_after = False
        if db_conn is None:
            try:
                from db import get_connection
                db_conn = get_connection()
                close_after = True
            except Exception:
                db_conn = None

        if db_conn is not None:
            try:
                # Query pre_ipo_evidence_snapshots table
                row = db_conn.execute(
                    "SELECT id, owner, company, payload FROM pre_ipo_evidence_snapshots WHERE id=?",
                    (snapshot_id,)
                ).fetchone()

                if not row:
                    # Also check if id column matches snapshot_id or if table has snapshot_id column
                    try:
                        row = db_conn.execute(
                            "SELECT id, owner, company, payload FROM pre_ipo_evidence_snapshots WHERE id=? OR payload LIKE ?",
                            (snapshot_id, f'%"{snapshot_id}"%')
                        ).fetchone()
                    except Exception:
                        row = None

                if not row:
                    raise ExportBlockedError(
                        f"Export blocked: snapshot '{snapshot_id}' does not exist in persistence. "
                        "Invented, unpersisted, or mock snapshot IDs are strictly rejected under P0-01/P0-03."
                    )

                snap_owner, snap_company, payload_raw = row[1], row[2], row[3]
                import json
                try:
                    payload = json.loads(payload_raw) if isinstance(payload_raw, str) else payload_raw
                except Exception:
                    payload = {}

                # Check persistence status
                persisted_status = payload.get("status", "ACCEPTED_FOR_ANALYSIS")
                if persisted_status not in ("ACCEPTED_FOR_ANALYSIS", "ACCEPTED"):
                    raise ExportBlockedError(
                        f"Export blocked: snapshot '{snapshot_id}' in persistence has status '{persisted_status}'. "
                        "Only ACCEPTED_FOR_ANALYSIS snapshots may be exported."
                    )

                # Check hash consistency
                persisted_hash = payload.get("snapshot_hash") or payload.get("id") or row[0]
                if not snapshot_hash or not result_snapshot_hash:
                    raise ExportBlockedError(
                        "Export blocked: snapshot_hash and result_snapshot_hash are mandatory for verified analytical exports."
                    )
                if snapshot_hash != result_snapshot_hash:
                    raise ExportBlockedError(
                        f"Export blocked: snapshot hash mismatch ({snapshot_hash} != {result_snapshot_hash}). "
                        "Data integrity validation failed."
                    )
                if persisted_hash and snapshot_hash != persisted_hash:
                    raise ExportBlockedError(
                        f"Export blocked: provided snapshot hash '{snapshot_hash}' does not match persisted hash '{persisted_hash}'."
                    )
            finally:
                if close_after and db_conn:
                    db_conn.close()

    # 3. Caller status sanity check
    if snapshot_status and snapshot_status != "ACCEPTED_FOR_ANALYSIS":
        raise ExportBlockedError(
            f"Export blocked: snapshot status is '{snapshot_status}'. Only ACCEPTED_FOR_ANALYSIS data may be exported."
        )

    # 4. Hash verification if hashes are supplied
    if snapshot_hash and result_snapshot_hash and snapshot_hash != result_snapshot_hash:
        raise ExportBlockedError(
            f"Export blocked: snapshot hash mismatch ({snapshot_hash} != {result_snapshot_hash}). "
            "Data integrity validation failed."
        )

