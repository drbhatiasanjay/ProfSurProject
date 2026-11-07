"""Decision processes: transparent rules, never inferred probabilities."""
from .contracts import Result, number, positive, timestamp

def diligence_priority(gaps):
    rows = []
    for gap in gaps:
        mandatory = bool(gap.get("mandatory", False))
        outcomes = gap.get("decision_outcomes", [])
        unresolved = not outcomes or len(set(outcomes)) > 1
        if gap.get("impact_range") is not None:
            lower, upper = gap["impact_range"]
            lower, upper = number(lower, "lower impact"), number(upper, "upper impact")
            hurdle = number(gap["decision_hurdle"], "decision hurdle")
            if lower > upper:
                raise ValueError("Impact range is reversed")
            unresolved = lower <= hurdle <= upper
        rows.append({**gap, "priority": "BLOCKER" if mandatory else "HIGH" if unresolved else "LOW",
                     "next_action": gap.get("next_action") or "Request source, definition and dated reconciliation"})
    rows.sort(key=lambda r: {"BLOCKER": 0, "HIGH": 1, "LOW": 2}[r["priority"]])
    return Result("RULE_BASED", {"gaps": rows}, assumptions=("Priority reflects decision sensitivity, not probability.",))

def information_value(priors, utilities, joint_signal=None, cost=0, delay_cost=0):
    p = {k: number(v, k, 0, 1) for k, v in priors.items()}
    if not p or abs(sum(p.values()) - 1) > 1e-9 or not utilities:
        raise ValueError("Complete normalized priors and action utilities required")
    for action in utilities.values():
        if set(action) != set(p):
            raise ValueError("Every action needs a utility for every state")
        for value in action.values():
            number(value, "utility")
    baseline = max(sum(p[s] * a[s] for s in p) for a in utilities.values())
    perfect = sum(p[s] * max(a[s] for a in utilities.values()) for s in p)
    data = {"baseline": baseline, "evpi": max(0, perfect - baseline)}
    if joint_signal is not None:
        marginals = {s: 0.0 for s in p}
        signal_value = 0.0
        for joint in joint_signal.values():
            if set(joint) != set(p):
                raise ValueError("Joint signal states do not match prior")
            for s, probability in joint.items():
                marginals[s] += number(probability, "joint probability", 0, 1)
            signal_value += max(sum(joint[s] * a[s] for s in p) for a in utilities.values())
        if any(abs(marginals[s] - p[s]) > 1e-9 for s in p):
            raise ValueError("Joint signal marginals must equal the prior")
        evsi = signal_value - baseline
        if evsi < -1e-8 or evsi > data["evpi"] + 1e-8:
            raise ValueError("Information value bounds violated")
        data.update(evsi=max(0, evsi), net_value=evsi-number(cost, "cost", 0)-number(delay_cost, "delay cost", 0))
    return Result("CONDITIONAL_MODEL", data, assumptions=("Explicit subjective priors and common utility units; no empirical calibration implied.",))

def compare_opportunities(opportunities, context_keys, orientations):
    if len(opportunities) < 2 or not context_keys or not orientations:
        return Result("INSUFFICIENT_EVIDENCE", reasons=("Two opportunities and explicit common context/metrics required",))
    first = opportunities[0]
    if any(any(k not in item.get("context", {}) for k in context_keys) for item in opportunities):
        return Result("NOT_COMPARABLE", reasons=("Required context missing",))
    if any(any(item["context"][k] != first["context"][k] for k in context_keys) for item in opportunities):
        return Result("NOT_COMPARABLE", reasons=("Currency, date, horizon, security rights and cost basis must match",))
    pairs = []
    for a_index, a in enumerate(opportunities):
        for b in opportunities[a_index+1:]:
            scenarios = set(a.get("scenarios", {}))
            if not scenarios or scenarios != set(b.get("scenarios", {})):
                pairs.append({"a": a["id"], "b": b["id"], "state": "NOT_COMPARABLE"})
                continue
            differences = []
            for scenario in scenarios:
                for metric, direction in orientations.items():
                    if direction not in {-1, 1}:
                        raise ValueError("Metric orientation must be -1 or 1")
                    av, bv = a["scenarios"][scenario].get(metric), b["scenarios"][scenario].get(metric)
                    if av is None or bv is None:
                        return Result("INSUFFICIENT_EVIDENCE", reasons=("Paired scenario metric missing",))
                    differences.append(direction*(number(av, metric)-number(bv, metric)))
            state = "A_DOMINATES" if all(d >= 0 for d in differences) and any(d > 0 for d in differences) else "B_DOMINATES" if all(d <= 0 for d in differences) and any(d < 0 for d in differences) else "TRADEOFF_OR_EQUAL"
            pairs.append({"a": a["id"], "b": b["id"], "state": state})
    return Result("PAIRED_SCENARIOS", {"comparisons": pairs}, assumptions=("Dominance applies only to supplied scenarios and metrics.",))

def evaluate_commitment(commitment, as_of, observation=None):
    required = ("id", "target", "direction", "deadline", "metric", "period", "basis")
    if any(k not in commitment for k in required):
        raise ValueError("Original commitment definition incomplete")
    target = number(commitment["target"], "target")
    if commitment["direction"] not in {"at_least", "at_most"}:
        raise ValueError("Unknown target direction")
    if timestamp(as_of) < timestamp(commitment["deadline"]):
        return Result("NOT_DUE", {"original": commitment})
    if not observation or any(observation.get(k) != commitment[k] for k in ("metric", "period", "basis")):
        return Result("PENDING_COMPARABLE_OBSERVATION", {"original": commitment})
    if not observation.get("available_by") or timestamp(observation["available_by"]) > timestamp(as_of):
        return Result("PENDING_COMPARABLE_OBSERVATION", {"original": commitment})
    actual = number(observation["value"], "actual")
    met = actual >= target if commitment["direction"] == "at_least" else actual <= target
    return Result("MET" if met else "MISSED", {"original": commitment, "observation": observation, "variance": actual-target})

def monitor(observation, threshold, recovery, previous="NORMAL", previous_event_id=None):
    threshold, recovery = number(threshold, "threshold"), number(recovery, "recovery")
    if recovery < threshold:
        raise ValueError("Recovery must be at or above lower-bound breach threshold")
    if not observation or observation.get("value") is None:
        return Result("UNKNOWN", reasons=("Missing observation is not zero",))
    if observation.get("disputed") or observation.get("stale"):
        return Result("UNKNOWN", reasons=("Observation disputed or stale",))
    if not observation.get("id"):
        raise ValueError("Observation ID required for deduplication")
    if observation["id"] == previous_event_id:
        return Result("DUPLICATE", {"previous": previous})
    value = number(observation["value"], "observation")
    state = "BREACH" if value < threshold else "RECOVERED" if previous == "BREACH" and value >= recovery else "BREACH" if previous == "BREACH" else "NORMAL"
    return Result(state, {"event_id": observation["id"], "revision_of": observation.get("revision_of"), "value": value})

def robustness(variants):
    if not variants:
        return Result("INSUFFICIENT_EVIDENCE", reasons=("Plausible structural variants required",))
    values = [number(v["value"], "variant value") for v in variants]
    decisions = {v["decision"] for v in variants}
    return Result("STABLE_ON_TESTED_VARIANTS" if len(decisions) == 1 else "STRUCTURALLY_SENSITIVE",
                  {"minimum": min(values), "maximum": max(values), "variants": variants},
                  assumptions=("Finite model envelope, not a confidence interval or outcome probability.",))
