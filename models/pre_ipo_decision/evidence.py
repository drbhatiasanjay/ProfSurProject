"""Temporal evidence, origin families, semantic bridges and thesis gates (ALG01/02)."""
from .contracts import Result, number, positive, timestamp

def eligible_evidence(records: list[dict], cutoff: str, mode="public_replay") -> Result:
    if mode not in {"public_replay", "decision_audit"}:
        raise ValueError("Unknown replay mode")
    limit = timestamp(cutoff)
    eligible, excluded, families = [], [], {}
    identifiers = [r["id"] for r in records]
    if len(set(identifiers)) != len(identifiers):
        raise ValueError("Evidence IDs must be unique")
    from .contracts import validate_graph
    validate_graph({r["id"]: [r["supersedes_id"]] if r.get("supersedes_id") else [] for r in records})
    for record in records:
        available, access, withdrawal = record.get("available_by"), record.get("user_access_at"), record.get("withdrawn_at")
        reason = None
        if not available:
            reason = "Historical availability not established"
        elif timestamp(available) > limit:
            reason = "Not established as available by cutoff"
        elif record.get("available_from") and timestamp(record["available_from"]) > timestamp(available):
            raise ValueError("Availability interval is reversed")
        elif mode == "decision_audit" and (not access or timestamp(access) > limit):
            reason = "Not in recorded decision-maker information set"
        elif withdrawal and timestamp(withdrawal) <= limit:
            reason = "Withdrawn by cutoff"
        if reason:
            excluded.append({"id": record["id"], "reason": reason})
            continue
        eligible.append(record)
        origin = record.get("origin_id") or f"unknown-origin:{record['id']}"
        families.setdefault(origin, []).append(record["id"])
    superseded = {r.get("supersedes_id") for r in eligible}
    current = [r for r in eligible if r["id"] not in superseded]
    return Result("COMPUTED", {"eligible": current, "historical_eligible": eligible, "excluded": excluded,
                              "origin_families": families, "independence": "Not established by document or family counts"})

SEMANTIC_KEY = ("metric", "entity", "period", "duration", "basis", "definition", "unit", "lease", "net")

def compare_facts(a: dict, b: dict, absolute_tolerance: float, relative_tolerance=0.0, bridge=None) -> Result:
    absolute_tolerance = number(absolute_tolerance, "absolute tolerance", 0)
    relative_tolerance = number(relative_tolerance, "relative tolerance", 0)
    if any(k not in a or k not in b for k in SEMANTIC_KEY):
        return Result("INSUFFICIENT_EVIDENCE", reasons=("Semantic definition incomplete",))
    differences = [k for k in SEMANTIC_KEY if a[k] != b[k]]
    av = number(a["value"], "first value") * positive(a.get("scale", 1), "first scale")
    bv = number(b["value"], "second value") * positive(b.get("scale", 1), "second scale")
    tolerance = max(absolute_tolerance, relative_tolerance * max(abs(av), abs(bv)))
    if differences:
        if bridge and bridge.get("evidence_ids") and set(differences) == set(bridge.get("fields", [])):
            delta = number(bridge["adjustment"], "bridge adjustment")
            if abs(av + delta - bv) <= tolerance:
                return Result("EXPLAINED_BRIDGE", {"difference": bv - av, "bridge": bridge})
        return Result("NOT_COMPARABLE", {"different_fields": differences})
    return Result("COMPATIBLE" if abs(av - bv) <= tolerance else "DISPUTED",
                  {"first": av, "second": bv, "difference": bv - av, "tolerance": tolerance})

def dependency_state(expression, states: dict[str, str]) -> str:
    if isinstance(expression, str):
        return states.get(expression, "INSUFFICIENT_EVIDENCE")
    if not isinstance(expression, dict) or set(expression) not in ({"all"}, {"any"}):
        raise ValueError("Dependencies require a metric ID or an all/any expression")
    operator, children = next(iter(expression.items()))
    if not isinstance(children, list) or not children:
        raise ValueError("Dependency expression cannot be empty")
    evaluated = [dependency_state(child, states) for child in children]
    if operator == "any" and "SUPPORTED" in evaluated:
        return "SUPPORTED"
    if operator == "all" and all(s == "SUPPORTED" for s in evaluated):
        return "SUPPORTED"
    return "DISPUTED" if "DISPUTED" in evaluated else "INSUFFICIENT_EVIDENCE"

def assess_thesis(propositions: list[dict], evidence_states: dict[str, str]) -> Result:
    findings = []
    if len({p["id"] for p in propositions}) != len(propositions):
        raise ValueError("Proposition IDs must be unique")
    for proposition in propositions:
        required = ("id", "claim", "mechanism", "observable", "horizon", "review_trigger", "dependencies")
        if any(not proposition.get(key) for key in required):
            raise ValueError("Thesis requires a falsifiable proposition and explicit dependencies")
        state = dependency_state(proposition["dependencies"], evidence_states)
        findings.append({**proposition, "state": state,
                         "interpretation": "Evidence support, not causal identification or investment approval"})
    state = "SUPPORTED" if findings and all(f["state"] == "SUPPORTED" for f in findings) else "PARTIAL"
    return Result(state, {"propositions": findings})
