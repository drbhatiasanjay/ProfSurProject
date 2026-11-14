"""
Pre-IPO Dossier Resolver (P0-01 Containment & Codex Standard).
Provides architectural boundary separation between raw evidence snapshots
and domain analytical dossiers:
- Strictly prevents unreviewed HCCH registry dossiers from entering production analytics
- Rejects arbitrary JSON deserialization of snapshot payloads into dossier objects
- Differentiates unaccepted evidence from accepted evidence lacking a reviewed mapping adapter
- Preserves demonstration issuers labeled explicitly as legacy demonstration data
"""

from dataclasses import dataclass
from enum import Enum
from typing import Optional, Any, Dict
from models.pre_ipo_capability_gate import is_hcch_entity, _get_persisted_snapshot_data
from models.pre_ipo_data import get_legacy_dossier


class DossierResolutionStatus(str, Enum):
    READY = "READY"
    BLOCKED_EVIDENCE_NOT_ACCEPTED = "BLOCKED_EVIDENCE_NOT_ACCEPTED"
    BLOCKED_EVIDENCE_DOSSIER_ADAPTER_UNAVAILABLE = "BLOCKED_EVIDENCE_DOSSIER_ADAPTER_UNAVAILABLE"


@dataclass(frozen=True)
class DossierResolution:
    status: DossierResolutionStatus
    dossier: Optional[Any]
    origin: str  # DEMONSTRATION_LEGACY | PROCESSED_INTAKE | BLOCKED | NOT_FOUND
    reason: str
    next_action: str
    snapshot_id: Optional[str] = None
    snapshot_hash: Optional[str] = None


def resolve_dossier(
    selected_deal_key: str,
    owner: Optional[str],
    snapshot_id: Optional[str] = None,
    custom_dossier: Optional[Any] = None,
    cin: str = "",
    conn: Optional[Any] = None,
) -> DossierResolution:
    """
    Architectural boundary resolver for Pre-IPO dossiers.
    Enforces strict fail-closed gating:
    1. HCCH: Never resolves from PRE_IPO_REGISTRY, never deserializes payload["dossier"].
       - If snapshot_id is absent or unreviewed/unaccepted -> BLOCKED_EVIDENCE_NOT_ACCEPTED.
       - If snapshot is ACCEPTED_FOR_ANALYSIS -> BLOCKED_EVIDENCE_DOSSIER_ADAPTER_UNAVAILABLE.
    2. Non-HCCH custom intake -> READY with origin PROCESSED_INTAKE.
    3. Non-HCCH demonstration issuers -> READY with origin DEMONSTRATION_LEGACY.
    """
    is_hcch = is_hcch_entity(selected_deal_key, selected_deal_key, cin)

    if is_hcch:
        # P0-01 Containment: HCCH is strictly disconnected from PRE_IPO_REGISTRY
        # Never deserialize arbitrary payload["dossier"] or unreviewed registry data
        if not owner or not snapshot_id:
            return DossierResolution(
                status=DossierResolutionStatus.BLOCKED_EVIDENCE_NOT_ACCEPTED,
                dossier=None,
                origin="BLOCKED",
                reason=(
                    "Hindustan Coca-Cola Beverages is strictly disconnected from the unreviewed built-in registry. "
                    "Under SEBI ICDR regulations and P0-01 containment, production ratio calculations, Dickinson stage "
                    "classification, and analytical deck export are blocked until an official filing snapshot is reviewed and accepted."
                ),
                next_action="Open Tab 2 Provenance Ledger or upload the official 513-page DRHP to audit and accept source observations.",
                snapshot_id=snapshot_id,
            )

        persisted = _get_persisted_snapshot_data(snapshot_id, owner, selected_deal_key, conn=conn)
        if not persisted or persisted.get("status") != "ACCEPTED_FOR_ANALYSIS":
            return DossierResolution(
                status=DossierResolutionStatus.BLOCKED_EVIDENCE_NOT_ACCEPTED,
                dossier=None,
                origin="BLOCKED",
                reason=(
                    f"Evidence snapshot '{snapshot_id}' for HCCH is unreviewed or in status '{persisted.get('status') if persisted else 'NOT_FOUND'}'. "
                    "Only ACCEPTED_FOR_ANALYSIS snapshots are eligible for analytical processing."
                ),
                next_action="Audit and accept all candidate observations in Tab 2 Provenance Ledger.",
                snapshot_id=snapshot_id,
            )

        # Snapshot is accepted, but evidence-to-dossier analytical adapter is not yet implemented
        return DossierResolution(
            status=DossierResolutionStatus.BLOCKED_EVIDENCE_DOSSIER_ADAPTER_UNAVAILABLE,
            dossier=None,
            origin="BLOCKED",
            reason=(
                "Evidence snapshot is accepted with verified source provenance, but the official evidence-to-dossier "
                "analytical adapter is not yet available for HCCH. Production ratios, valuation, and analytical models "
                "cannot be computed from raw snapshots without an audited analytical mapping adapter."
            ),
            next_action="Complete independent audit review and implementation of the evidence-to-dossier mapping adapter.",
            snapshot_id=snapshot_id,
            snapshot_hash=persisted.get("snapshot_hash"),
        )

    # Non-HCCH Issuers
    if custom_dossier is not None:
        return DossierResolution(
            status=DossierResolutionStatus.READY,
            dossier=custom_dossier,
            origin="PROCESSED_INTAKE",
            reason="Custom user-ingested dossier loaded from document intake pipeline.",
            next_action="Ready for analytical presentation.",
            snapshot_id=snapshot_id,
        )

    legacy = get_legacy_dossier(selected_deal_key)
    if legacy is not None:
        return DossierResolution(
            status=DossierResolutionStatus.READY,
            dossier=legacy,
            origin="DEMONSTRATION_LEGACY",
            reason="Loaded demonstration legacy data for interface evaluation.",
            next_action="Ready for demonstration review.",
            snapshot_id=snapshot_id,
        )

    return DossierResolution(
        status=DossierResolutionStatus.BLOCKED_EVIDENCE_NOT_ACCEPTED,
        dossier=None,
        origin="NOT_FOUND",
        reason=f"No dossier or evidence snapshot found for '{selected_deal_key}'.",
        next_action="Ingest filing or select a supported demonstration issuer.",
        snapshot_id=snapshot_id,
    )
