"""Declarative Golden Oracle Loader & Integrity Verification Module.

Provides cryptographic verification, strict JSON schema validation,
and high-speed retrieval of ground-truth prospectus filings.
"""

from __future__ import annotations
import json
import hashlib
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any

GOLDEN_ORACLE_DIR = Path(__file__).resolve().parent.parent / "data" / "golden_oracles"

EXPECTED_ORACLE_DEALS = (
    "mankind_pharma",
    "afcons_infra",
    "swiggy",
    "tata_technologies",
    "ntpc_green",
    "hindustan_coca_cola",
)


class GoldenOracleError(Exception):
    """Raised when an oracle file is missing, corrupt, or fails schema validation."""
    pass


def verify_oracle_sha(oracle_path: str | Path, expected_sha: Optional[str] = None) -> str:
    """Compute SHA-256 of the oracle file and assert match if expected_sha provided."""
    path = Path(oracle_path)
    if not path.exists():
        raise GoldenOracleError(f"Golden oracle file not found: {path}")
    
    hasher = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(65536):
            hasher.update(chunk)
            
    digest = hasher.hexdigest()
    if expected_sha is not None and digest.lower() != expected_sha.lower():
        raise GoldenOracleError(
            f"Cryptographic mismatch: file {path.name} has SHA-256 {digest}, "
            f"expected {expected_sha}. File may be corrupted or tampered."
        )
    return digest


def validate_oracle_schema(oracle: Any) -> Tuple[bool, List[str]]:
    """Validate that an oracle dict conforms to strict structural and financial constraints."""
    errors: List[str] = []
    
    if not isinstance(oracle, dict):
        return False, ["Oracle root must be a dictionary."]
        
    for req_key in ("deal_id", "company_name", "filing_type", "restated_financials"):
        if req_key not in oracle:
            errors.append(f"Missing required root key: '{req_key}'")
            
    if errors:
        return False, errors
        
    financials = oracle.get("restated_financials")
    if not isinstance(financials, list) or len(financials) == 0:
        errors.append("'restated_financials' must be a non-empty list.")
    else:
        for idx, fin in enumerate(financials):
            if not isinstance(fin, dict):
                errors.append(f"Financial record #{idx} must be a dictionary.")
                continue
            if "period" not in fin:
                errors.append(f"Financial record #{idx} missing required key 'period'.")
            
            # Numeric sanity checks
            rev = fin.get("revenue_ops_cr")
            if rev is None or not isinstance(rev, (int, float)):
                errors.append(f"Financial record #{idx} ('{fin.get('period')}') has non-numeric revenue.")
            elif rev < 0:
                errors.append(f"Financial record #{idx} ('{fin.get('period')}') has negative revenue ({rev}).")
                
            pat = fin.get("pat_cr")
            if pat is None or not isinstance(pat, (int, float)):
                errors.append(f"Financial record #{idx} ('{fin.get('period')}') has non-numeric PAT.")

    # Semantic Disclosures & Absence Validation
    disclosures = oracle.get("semantic_disclosures")
    if disclosures is not None:
        if not isinstance(disclosures, list):
            errors.append("'semantic_disclosures' must be a list if present.")
        else:
            valid_presence = ("PRESENT", "DISCLOSED_ZERO", "NOT_DISCLOSED")
            for idx, disc in enumerate(disclosures):
                if not isinstance(disc, dict):
                    errors.append(f"Semantic disclosure #{idx} must be a dictionary.")
                    continue
                if "metric_id" not in disc or not disc["metric_id"]:
                    errors.append(f"Semantic disclosure #{idx} missing 'metric_id'.")
                pres = disc.get("presence")
                if pres not in valid_presence:
                    errors.append(f"Semantic disclosure #{idx} ('{disc.get('metric_id')}') has invalid presence '{pres}'. Must be one of {valid_presence}.")
                if pres == "NOT_DISCLOSED" and disc.get("value") is not None:
                    errors.append(f"Semantic disclosure #{idx} ('{disc.get('metric_id')}') has presence NOT_DISCLOSED but value is not None ({disc.get('value')}).")
                if pres == "DISCLOSED_ZERO" and disc.get("value") not in (0, 0.0):
                    errors.append(f"Semantic disclosure #{idx} ('{disc.get('metric_id')}') has presence DISCLOSED_ZERO but value is not 0.0 ({disc.get('value')}).")
                if "citation" not in disc or not str(disc.get("citation", "")).strip():
                    errors.append(f"Semantic disclosure #{idx} ('{disc.get('metric_id')}') missing 'citation'.")

    # Offer details validation (ensuring unpriced deals use None, not 0.0)
    offer_details = oracle.get("offer_details")
    if isinstance(offer_details, dict):
        for num_key in ("total_issue_size_cr", "fresh_issue_cr", "ofs_cr"):
            val = offer_details.get(num_key)
            if val is not None and not isinstance(val, (int, float)):
                errors.append(f"Offer detail '{num_key}' must be a number or None, got {type(val).__name__}.")

    return (len(errors) == 0), errors


def load_golden_oracle(deal_id: str, verify_hash: bool = True) -> Dict[str, Any]:
    """Load, validate, and return the declarative golden oracle for a prospectus deal."""
    if deal_id not in EXPECTED_ORACLE_DEALS:
        # Check if direct file exists or raise
        oracle_file = GOLDEN_ORACLE_DIR / f"{deal_id}_golden.json"
        if not oracle_file.exists():
            raise GoldenOracleError(f"Golden oracle for deal '{deal_id}' does not exist.")
    else:
        oracle_file = GOLDEN_ORACLE_DIR / f"{deal_id}_golden.json"
        
    if not oracle_file.exists():
        raise GoldenOracleError(f"Golden oracle file not found: {oracle_file}")
        
    try:
        with open(oracle_file, "r", encoding="utf-8") as f:
            oracle_data = json.load(f)
    except Exception as exc:
        raise GoldenOracleError(f"Failed to parse golden oracle JSON at {oracle_file}: {exc}") from exc
        
    is_valid, errors = validate_oracle_schema(oracle_data)
    if not is_valid:
        raise GoldenOracleError(f"Golden oracle {deal_id} failed schema validation: {errors}")
        
    return oracle_data


def get_all_oracles() -> Dict[str, Dict[str, Any]]:
    """Load all 6 canonical golden oracles in a dictionary keyed by deal_id."""
    return {deal_id: load_golden_oracle(deal_id) for deal_id in EXPECTED_ORACLE_DEALS}

