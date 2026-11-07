"""Explicit, bounded dispatch over immutable decision inputs."""
import json
from .contracts import Result, METHOD_VERSION, context_hash, canonical_json, timestamp
from . import financial, assessment, evidence, data_quality

METHODS = {
    "operating_model": financial.operating_model, "cohort_retention": financial.cohort_retention,
    "cash_flow_bridge": financial.cash_flow_bridge, "cash_tax": financial.cash_tax,
    "cash_schedule": financial.cash_schedule, "ordinary_raise": financial.ordinary_raise,
    "equity_bridge": financial.equity_bridge, "terminal_cash": financial.terminal_cash,
    "discounted_value": financial.discounted_value, "reverse_dcf": financial.reverse_dcf,
    "reverse_stress": financial.reverse_stress, "price_attribution": financial.price_attribution,
    "investor_returns": financial.investor_returns, "private_waterfall": financial.private_waterfall,
    "diligence_priority": assessment.diligence_priority, "information_value": assessment.information_value,
    "compare_opportunities": assessment.compare_opportunities, "evaluate_commitment": assessment.evaluate_commitment,
    "monitor": assessment.monitor, "robustness": assessment.robustness,
    "compare_facts": evidence.compare_facts, "method_eligibility": data_quality.method_eligibility,
}
NEXT_ACTION = {
    "INSUFFICIENT_EVIDENCE": "Obtain the missing dated inputs and source definitions before relying on this result.",
    "INVALID_INPUT": "Correct the listed input errors and reapply the case.",
    "NOT_COMPARABLE": "Reconcile the entity, period, currency, definitions and security rights.",
    "INFEASIBLE": "Revise the financing or operating assumptions; retain this failed case as a risk scenario.",
    "UNBRACKETED": "Review the economic search domain; do not interpret the boundary as a solution.",
    "DISPUTED": "Resolve conflicting source values with a documented reconciliation.",
}
def parse_bundle(text):
    if len(text.encode("utf-8")) > 1_000_000:
        raise ValueError("Case exceeds 1 MB")
    def reject(value):
        raise ValueError("Non-finite JSON number: " + value)
    bundle = json.loads(text, parse_constant=reject)
    canonical_json(bundle)
    if not isinstance(bundle, dict):
        raise ValueError("Case must be a JSON object")
    return bundle

def template():
    return {"schema_version": 1, "company": "", "as_of": "2026-11-07", "currency": "",
            "unit": "", "background": "", "evidence": [], "propositions": [], "models": {},
            "gaps": [{"attribute": "CMIE attribute mapping", "mandatory": True,
                      "next_action": "Attach the versioned CMIE reference and extracted attribute inventory."}]}

def run_case(bundle):
    bundle = json.loads(canonical_json(bundle))
    if len(canonical_json(bundle).encode("utf-8")) > 1_000_000:
        raise ValueError("Case exceeds 1 MB")
    if bundle.get("schema_version") != 1:
        raise ValueError("Unsupported schema version")
    for key in ("company", "as_of", "currency", "unit"):
        if not isinstance(bundle.get(key), str) or not bundle[key].strip():
            raise ValueError(key + " is required")
    timestamp(bundle["as_of"])
    models = bundle.get("models", {})
    if not isinstance(models, dict) or len(models) > len(METHODS) or set(models) - set(METHODS):
        raise ValueError("Invalid model set")
    temporal = evidence.eligible_evidence(bundle.get("evidence", []), bundle["as_of"], bundle.get("replay_mode", "public_replay"))
    eligible = {r["id"]: r for r in temporal.data["eligible"]}
    states = {key: ("SUPPORTED" if row.get("review_state") == "accepted" and row.get("locator") and row.get("citation") else "DISPUTED" if row.get("review_state") == "disputed" else "INSUFFICIENT_EVIDENCE") for key, row in eligible.items()}
    results = {}
    for name, function in METHODS.items():
        specification = models.get(name)
        if specification is None:
            result = Result("INSUFFICIENT_EVIDENCE", reasons=("Optional model inputs not supplied",))
        else:
            try:
                if not isinstance(specification, dict) or not isinstance(specification.get("inputs"), dict):
                    raise ValueError("Model requires an inputs object")
                if name in {"discounted_value", "reverse_dcf", "terminal_cash", "operating_model"} and bundle.get("sector_model") == "financial_institution":
                    result = Result("UNSUPPORTED", reasons=("Financial institutions require a capital/distribution model; generic industrial valuation is not eligible.",))
                elif name == "discounted_value" and specification["inputs"].get("currency") != bundle["currency"]:
                    result = Result("NOT_COMPARABLE", reasons=("Valuation currency does not match the case context.",))
                else:
                    result = function(**specification["inputs"])
                canonical_json(result.to_dict())
            except (ValueError, TypeError, KeyError, OverflowError, ZeroDivisionError) as exc:
                result = Result("INVALID_INPUT", reasons=(str(exc),))
        record = result.to_dict()
        source_ids = specification.get("evidence_ids", []) if isinstance(specification, dict) else []
        record["evidence_status"] = "REVIEWED_REFERENCES_INPUT_MAPPING_UNVERIFIED" if source_ids and all(states.get(i) == "SUPPORTED" for i in source_ids) else "ASSUMPTIONS_OR_UNVERIFIED_INPUTS"
        record["interpretation"] = "Conditional calculation under the displayed inputs. Source acceptance is a recorded reviewer judgment; it is not independent verification."
        record["next_action"] = NEXT_ACTION.get(result.state, "Review sensitivity, assumptions and source support before recording a decision.")
        from .guidance import explain
        question, mechanism, followup = explain(name, record)
        record.update(question=question, mechanism=mechanism, recommended_review=followup)
        results[name] = record
    results["thesis"] = evidence.assess_thesis(bundle.get("propositions", []), states).to_dict()
    results["diligence"] = assessment.diligence_priority(bundle.get("gaps", [])).to_dict()
    results["attribute_inventory"] = data_quality.attribute_inventory(bundle.get("attribute_reference"), bundle.get("extracted_attributes", [])).to_dict()
    from .guidance import REFERENCES
    return {"methodology_references": REFERENCES, "method_version": METHOD_VERSION, "context_hash": context_hash(bundle), "context": bundle,
            "evidence": temporal.to_dict(), "results": results,
            "limitations": ["Scenario outputs are not empirical probabilities or personalized investment advice.",
                            "No external citation or CMIE completeness is inferred when its reference is absent.",
                            "Persona changes presentation only; it does not change facts, rights or calculations."]}
