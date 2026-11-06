"""Offline evidence intake checks; never evaluates contractual compliance."""
from datetime import date
from hashlib import sha256
from pathlib import Path
import json
import math


REQUIRED_INPUTS = ("opening_cash_cr", "debt_excluding_leases_cr", "lease_liability_cr",
                   "tangible_net_worth_cr", "other_liabilities_cr")
REQUIRED_DOCUMENTS = {"financial_statement", "facility_terms", "debt_schedule",
                      "cash_flow_forecast", "net_worth_bridge"}


def validate_packet(packet: dict, evidence_dir: Path) -> dict:
    """Check structure, hashed local evidence and controls, without promotion.

    A source file's hash proves identity, not its truth or the correctness of a
    human transcription. READY_FOR_REVIEW is explicitly not approval to run.
    """
    issues = []
    def issue(code, field, message):
        issues.append({"code": code, "field": field, "message": message})
    def number(value):
        return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)
    def iso(value):
        try:
            return date.fromisoformat(value) if isinstance(value, str) else None
        except ValueError:
            return None
    if packet.get("schema_version") != 1:
        issue("SCHEMA", "schema_version", "Expected version 1")
    meta = packet.get("borrower", {})
    for field in ("legal_name", "entity_id", "perimeter"):
        if not isinstance(meta.get(field), str) or not meta[field].strip():
            issue("MISSING", f"borrower.{field}", "Required borrower identifier or perimeter")
    as_of = iso(meta.get("as_of"))
    if not as_of:
        issue("DATE", "borrower.as_of", "Required ISO date")
    if meta.get("currency") != "INR" or meta.get("unit") != "crore":
        issue("UNITS", "borrower", "Normalize explicitly to INR crore; no implicit conversion")
    periods = packet.get("period_ends", [])
    dates = [iso(p) for p in periods]
    if not 1 <= len(periods) <= 12 or any(d is None for d in dates):
        issue("PERIODS", "period_ends", "Provide 1–12 valid ISO period ends")
    elif dates != sorted(set(dates)) or (as_of and dates[0] <= as_of):
        issue("PERIODS", "period_ends", "Unique ascending future periods required")
    root = evidence_dir.resolve()
    sources, verified = {}, set()
    for i, doc in enumerate(packet.get("documents", [])):
        key = doc.get("id")
        if not isinstance(key, str) or not key or key in sources:
            issue("DOCUMENT_ID", f"documents[{i}]", "Nonempty unique document id required")
            continue
        sources[key] = doc
        try:
            if not isinstance(doc.get("file"), str) or not doc["file"].strip():
                raise ValueError("Supporting document filename required")
            relative = Path(doc.get("file", ""))
            target = (root / relative).resolve()
            if relative.is_absolute() or not target.is_relative_to(root) or not target.is_file():
                raise ValueError("Document must exist inside evidence directory")
            digest = sha256(target.read_bytes()).hexdigest()
            if digest != str(doc.get("sha256", "")).lower():
                raise ValueError("SHA-256 missing or mismatched")
            if doc.get("entity_id") != meta.get("entity_id") or doc.get("perimeter") != meta.get("perimeter"):
                raise ValueError("Document entity/perimeter mismatch")
            if doc.get("as_of") != meta.get("as_of"):
                raise ValueError("Document reference date must match packet as-of; map contract effective dates in terms")
            verified.add(key)
        except (OSError, TypeError, ValueError) as exc:
            issue("EVIDENCE_FILE", f"documents[{i}]", str(exc))
    kinds = {sources[key].get("kind") for key in verified}
    inputs = packet.get("inputs", {})
    if number(inputs.get("lease_liability_cr", {}).get("value")) and inputs["lease_liability_cr"]["value"] > 0:
        required = REQUIRED_DOCUMENTS | {"lease_schedule"}
    else:
        required = REQUIRED_DOCUMENTS
    for kind in sorted(required - kinds):
        issue("MISSING_DOCUMENT", "documents", f"Verified {kind} required")
    def reference(record, field, expected_kind=None):
        key = record.get("document_id")
        if key not in verified or not isinstance(record.get("locator"), str) or not record["locator"].strip():
            issue("SOURCE_REFERENCE", field, "Verified document and page/clause/cell locator required")
        elif expected_kind and sources[key].get("kind") != expected_kind:
            issue("SOURCE_KIND", field, f"Expected {expected_kind} evidence")
        if record.get("evidence_kind") not in ("observed", "approved_forecast", "derived"):
            issue("ASSUMPTION", field, "Unreviewed assumptions cannot enter actual-borrower review")
        if record.get("evidence_kind") == "derived" and not record.get("derivation"):
            issue("DERIVATION", field, "Derived values need a traceable calculation")
    for field in REQUIRED_INPUTS:
        record = inputs.get(field, {})
        if not number(record.get("value")) or (field != "tangible_net_worth_cr" and record["value"] < 0):
            issue("INPUT_VALUE", f"inputs.{field}", "Finite balance required; no missing-to-zero substitution")
        reference(record, f"inputs.{field}", "net_worth_bridge" if field == "tangible_net_worth_cr" else "financial_statement")
    facility_ids = set()
    for kind, control, collection in (("debt_schedule", "debt_excluding_leases_cr", "loans"),
                                      ("lease_schedule", "lease_liability_cr", "leases")):
        total = 0.0
        schedules = packet.get(collection, [])
        for i, schedule in enumerate(schedules):
            field = f"{collection}[{i}]"
            key = schedule.get("facility_id")
            if not key or key in facility_ids:
                issue("FACILITY_ID", field, "Unique facility id required across loans and leases")
            facility_ids.add(key)
            reference(schedule, field, kind)
            opening = schedule.get("opening_balance_cr")
            if not number(opening) or opening < 0:
                issue("SCHEDULE_VALUE", field, "Finite nonnegative opening balance required")
                opening = 0
            total += opening
            flows = schedule.get("periods", [])
            if [p.get("end") for p in flows] != periods:
                issue("SCHEDULE_PERIODS", field, "Schedule must match every packet period exactly")
            balance = opening
            for q, flow in enumerate(flows):
                values = [flow.get(x) for x in ("drawdown_cr", "principal_cr", "interest_cr", "other_cash_cr")]
                if any(not number(v) or v < 0 for v in values):
                    issue("SCHEDULE_VALUE", f"{field}.periods[{q}]", "Explicit nonnegative cash amounts required")
                    continue
                balance += values[0] - values[1]
                if balance < -0.01:
                    issue("OVERPAYMENT", f"{field}.periods[{q}]", "Principal exceeds available balance")
        record = inputs.get(control, {})
        if number(record.get("value")) and abs(total - record["value"]) > 0.01:
            issue("BALANCE_RECONCILIATION", collection, "Schedule openings do not match financial-statement control within 0.01 crore")
    forecasts = packet.get("cash_flow_forecast", [])
    if [r.get("end") for r in forecasts] != periods:
        issue("FORECAST_PERIODS", "cash_flow_forecast", "Forecast must cover every packet period")
    for i, forecast in enumerate(forecasts):
        field = f"cash_flow_forecast[{i}]"
        reference(forecast, field, "cash_flow_forecast")
        for key in ("earnings_cr", "cash_taxes_cr", "maintenance_capex_cr", "working_capital_use_cr"):
            if not number(forecast.get(key)):
                issue("FORECAST_VALUE", f"{field}.{key}", "Explicit finite value required")
        if forecast.get("earnings_basis") not in ("EBIT", "EBITDA", "EBITDAR"):
            issue("EARNINGS_BASIS", field, "Explicit earnings basis required")
    terms = packet.get("covenants", [])
    if not terms:
        issue("MISSING_TERMS", "covenants", "Transcribe actual clauses; absence is not inferred waiver")
    for i, term in enumerate(terms):
        field = f"covenants[{i}]"
        reference(term, field, "facility_terms")
        for key in ("metric", "definition_text", "numerator", "denominator", "testing_basis",
                    "lease_treatment", "cash_sweep", "effective_from", "facility_id"):
            if not isinstance(term.get(key), str) or not term[key].strip():
                issue("TERM_DEFINITION", f"{field}.{key}", "Explicit contractual definition required")
        if term.get("facility_id") not in facility_ids:
            issue("TERM_FACILITY", field, "Covenant must map to a supplied facility")
        if not number(term.get("threshold")) or term.get("operator") not in (">=", "<="):
            issue("TERM_LIMIT", field, "Finite threshold and explicit comparison operator required")
        if not iso(term.get("effective_from")):
            issue("TERM_DATE", field, "Valid effective date required")
    return {"schema_version": 1, "borrower": meta,
            "packet_sha256": sha256(json.dumps(packet, sort_keys=True, allow_nan=False).encode()).hexdigest(),
            "status": "NEEDS_EVIDENCE" if issues else "READY_FOR_PROFESSIONAL_REVIEW",
            "validation_status": "NOT_VALIDATED", "contractual_calculation_enabled": False,
            "verified_document_count": len(verified), "issues": issues,
            "limitations": ["Hashes verify file identity, not source truth or human transcription.",
                            "Contract definitions need professional review and an explicit engine capability mapping.",
                            "No scenario execution, contractual compliance conclusion or lending approval is produced."]}
