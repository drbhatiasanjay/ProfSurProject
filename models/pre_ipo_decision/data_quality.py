"""Attribute availability and method eligibility, without fabricated CMIE coverage."""
from .contracts import Result

def attribute_inventory(reference, extracted):
    if not reference or not reference.get("version") or not reference.get("attributes"):
        return Result("REFERENCE_REQUIRED", {"extracted": extracted}, reasons=("Versioned CMIE attribute reference not supplied; completeness cannot be established.",))
    keys = [row["id"] for row in reference["attributes"]]
    if len(set(keys)) != len(keys):
        raise ValueError("Duplicate reference attribute IDs")
    supplied = {}
    for row in extracted:
        if row["attribute_id"] in supplied:
            raise ValueError("Reconcile duplicate extracted attributes before coverage assessment")
        supplied[row["attribute_id"]] = row
    rows = []
    for attribute in reference["attributes"]:
        item = supplied.get(attribute["id"])
        state = "MISSING" if not item or item.get("value") is None else "DISPUTED" if item.get("disputed") else "EXTRACTED_UNVERIFIED"
        if item and item.get("not_applicable") is True:
            state = "NOT_APPLICABLE_REVIEW_REQUIRED"
        elif item and item.get("reviewed") is True and item.get("source_id") and item.get("locator") and state == "EXTRACTED_UNVERIFIED":
            state = "REVIEWED"
        rows.append({"attribute_id": attribute["id"], "label": attribute.get("label", attribute["id"]), "state": state,
                     "extraction": item, "next_action": "Resolve or source missing attribute" if state != "REVIEWED" else "Verify semantic basis against model requirement"})
    return Result("MAPPED", {"reference_version": reference["version"], "attributes": rows,
                             "unmapped_extractions": sorted(set(supplied)-set(keys))},
                  assumptions=("Extraction availability does not establish accuracy or methodological adequacy.",))

def dossier_attributes(dossier):
    """Flatten an existing dossier without upgrading its provenance."""
    from dataclasses import asdict, is_dataclass
    payload = asdict(dossier) if is_dataclass(dossier) else dossier.model_dump(mode="json") if hasattr(dossier, "model_dump") else dossier
    rows = []
    def visit(value, path):
        if isinstance(value, dict):
            for key, child in value.items():
                visit(child, path + "." + key if path else key)
        elif isinstance(value, list):
            if not value:
                rows.append({"attribute_id": path, "value": None, "status": "EMPTY_COLLECTION"})
            for index, child in enumerate(value):
                visit(child, path + "[" + str(index) + "]")
        else:
            rows.append({"attribute_id": path, "value": value, "reviewed": False,
                         "status": "MISSING" if value is None else "EXTRACTED_UNVERIFIED"})
    visit(payload, "")
    return rows

def method_eligibility(method, independent_entities, periods, target_defined=False, temporal_split=False, valid_instruments=False):
    if independent_entities < 0 or periods < 0:
        raise ValueError("Sample dimensions cannot be negative")
    if method == "descriptive":
        return Result("ELIGIBLE" if periods >= 1 else "INSUFFICIENT_DATA")
    if method == "panel_regression":
        return Result("REQUIRES_DESIGN_REVIEW" if independent_entities >= 2 and periods >= 2 else "INSUFFICIENT_DATA",
                      reasons=("Entity/time variation, identification and dependence-aware inference must be reviewed; counts alone never qualify a model.",))
    if method == "dynamic_panel_gmm":
        return Result("REQUIRES_DESIGN_REVIEW" if independent_entities >= 2 and periods >= 3 and valid_instruments else "INSUFFICIENT_DATA",
                      reasons=("Instrument relevance/validity, proliferation and specification diagnostics required.",))
    if method == "predictive_ml":
        return Result("REQUIRES_VALIDATION" if target_defined and temporal_split and independent_entities >= 2 else "INSUFFICIENT_DATA",
                      reasons=("Leakage-safe temporal/group validation, baseline comparison and calibration required.",))
    return Result("UNSUPPORTED", reasons=("No eligibility contract registered for this method.",))
