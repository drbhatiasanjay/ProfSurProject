#!/usr/bin/env python3
"""Task Contract and Scope Verifier for ProfSurProject.

Enforces machine-verifiable authority, workspace, branch, commit limits,
path boundaries (allowed_paths vs forbidden_paths), and protected artifact hashes.
Strictly fail-closed.
"""
import argparse
import fnmatch
import hashlib
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple


def _run_git(args: list[str], cwd: Path) -> Tuple[int, str, str]:
    try:
        proc = subprocess.run(
            ["git"] + args,
            cwd=str(cwd),
            capture_output=True,
            text=True,
            check=False,
        )
        return proc.returncode, proc.stdout.strip(), proc.stderr.strip()
    except Exception as e:
        return 1, "", str(e)


def _compute_sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _normalize_path(p: str) -> str:
    """Normalize file path to POSIX forward-slash representation."""
    return str(Path(p).as_posix()).strip()


def _path_matches(candidate: str, pattern: str) -> bool:
    """Match candidate path against glob pattern supporting ** and *."""
    c_norm = _normalize_path(candidate)
    p_norm = _normalize_path(pattern)

    # Direct match or exact file match
    if c_norm == p_norm:
        return True

    # If pattern ends with /**, matches directory and everything under it
    if p_norm.endswith("/**"):
        prefix = p_norm[:-3]
        if c_norm == prefix or c_norm.startswith(prefix + "/"):
            return True

    # Standard fnmatch
    if fnmatch.fnmatch(c_norm, p_norm):
        return True

    # Single directory prefix matching
    if p_norm.endswith("/*"):
        prefix = p_norm[:-2]
        if c_norm.startswith(prefix + "/"):
            return True

    return False


def _validate_schema(contract: Dict[str, Any]) -> List[str]:
    """Validate contract against strict schema rules without external heavy dependencies."""
    errors = []
    required_keys = [
        "schema_version",
        "task_id",
        "authority",
        "mode",
        "repository",
        "workspace",
        "base_branch",
        "base_sha",
        "worker_branch",
        "authorized_packet",
        "allowed_objectives",
        "forbidden_objectives",
        "allowed_paths",
        "forbidden_paths",
        "required_tests",
        "stop_conditions",
        "maximum_new_commits",
        "push_authorized",
        "pr_creation_authorized",
        "merge_authorized",
        "deployment_authorized",
        "protected_artifacts",
        "created_at",
        "expires_at",
    ]

    for k in required_keys:
        if k not in contract:
            errors.append(f"Missing required contract field: '{k}'")

    # Reject unknown properties
    for k in contract.keys():
        if k not in required_keys:
            errors.append(f"Unknown contract property rejected: '{k}'")

    # Validate types
    if "base_sha" in contract and (not isinstance(contract["base_sha"], str) or len(contract["base_sha"]) != 40):
        errors.append("base_sha must be a 40-character hexadecimal SHA")

    if "allowed_paths" in contract and (not isinstance(contract["allowed_paths"], list) or len(contract["allowed_paths"]) == 0):
        errors.append("allowed_paths must be a non-empty list of path patterns")

    if "allowed_objectives" in contract and (not isinstance(contract["allowed_objectives"], list) or len(contract["allowed_objectives"]) == 0):
        errors.append("allowed_objectives must be a non-empty list")

    if "maximum_new_commits" in contract and (not isinstance(contract["maximum_new_commits"], int) or contract["maximum_new_commits"] < 0):
        errors.append("maximum_new_commits must be an integer >= 0")

    for bool_flag in ("push_authorized", "pr_creation_authorized", "merge_authorized", "deployment_authorized"):
        if bool_flag in contract and not isinstance(contract[bool_flag], bool):
            errors.append(f"{bool_flag} must be a boolean")

    return errors


def verify_agent_scope(
    contract_path: Path,
    expected_hash: Optional[str] = None,
    repo_dir: Optional[Path] = None,
    base_override: Optional[str] = None,
) -> Dict[str, Any]:
    """Execute all scope verification checks against Git and active contract."""
    cwd = (repo_dir or Path.cwd()).resolve()
    errors = []

    # 1. Read contract bytes
    if not contract_path.is_file():
        return {
            "status": "FAIL",
            "errors": [{"code": "CONTRACT_NOT_FOUND", "message": f"Contract file not found: {contract_path}"}]
        }

    raw_bytes = contract_path.read_bytes()
    calc_hash = _compute_sha256_bytes(raw_bytes)

    # 2. Hash check (fail-closed)
    target_expected_hash = expected_hash or os.environ.get("PROFSUR_TASK_CONTRACT_SHA256")
    if not target_expected_hash:
        errors.append({
            "code": "EXPECTED_CONTRACT_HASH_REQUIRED",
            "message": "Expected contract hash was not provided via CLI or PROFSUR_TASK_CONTRACT_SHA256"
        })
    elif calc_hash.lower() != target_expected_hash.lower():
        errors.append({
            "code": "CONTRACT_HASH_MISMATCH",
            "message": f"Contract hash mismatch: computed {calc_hash} != expected {target_expected_hash}"
        })

    # 3. Parse JSON
    try:
        contract = json.loads(raw_bytes.decode("utf-8"))
    except Exception as e:
        errors.append({
            "code": "MALFORMED_CONTRACT_JSON",
            "message": f"Failed to parse contract JSON: {e}"
        })
        return {"status": "FAIL", "errors": errors}

    # 4. Schema Validation
    schema_errs = _validate_schema(contract)
    if schema_errs:
        for se in schema_errs:
            errors.append({"code": "SCHEMA_VALIDATION_FAILED", "message": se})
        return {"status": "FAIL", "errors": errors}

    # 5. Expiration Check
    try:
        exp_str = contract.get("expires_at", "")
        # Parse ISO date
        if exp_str.endswith("Z"):
            exp_str = exp_str[:-1] + "+00:00"
        exp_dt = datetime.fromisoformat(exp_str)
        now_dt = datetime.now(timezone.utc)
        if now_dt > exp_dt:
            errors.append({
                "code": "CONTRACT_EXPIRED",
                "message": f"Task contract expired at {exp_dt.isoformat()} (current UTC: {now_dt.isoformat()})"
            })
    except Exception as e:
        errors.append({
            "code": "CONTRACT_EXPIRED",
            "message": f"Invalid expires_at timestamp: {e}"
        })

    # 6. Repository and Workspace Validation
    code, root_out, _ = _run_git(["rev-parse", "--show-toplevel"], cwd)
    actual_root = Path(root_out).resolve() if (code == 0 and root_out) else cwd
    actual_repo_name = actual_root.name

    if contract.get("repository") != "ProfSurProject" or (
        "profsurproject" not in actual_repo_name.lower() and
        not any("profsurproject" in part.lower() for part in actual_root.parts)
    ):
        errors.append({
            "code": "REPOSITORY_MISMATCH",
            "message": f"Repository check failed: contract specifies {contract.get('repository')} but actual root is {actual_root}"
        })

    # 7. Branch Validation
    code_br, actual_branch, _ = _run_git(["branch", "--show-current"], actual_root)
    worker_branch = contract.get("worker_branch")
    if actual_branch != worker_branch:
        errors.append({
            "code": "BRANCH_MISMATCH",
            "message": f"Active branch '{actual_branch}' does not match contract worker_branch '{worker_branch}'"
        })

    # 8. Base SHA and Ancestry
    base_sha = base_override or contract.get("base_sha")
    code_base, _, _ = _run_git(["cat-file", "-e", f"{base_sha}^{{commit}}"], actual_root)
    if code_base != 0:
        errors.append({
            "code": "BASE_SHA_MISSING",
            "message": f"Base SHA '{base_sha}' does not exist in local git object database"
        })
    else:
        # Check merge-base ancestry
        code_mb, mbase, _ = _run_git(["merge-base", base_sha, "HEAD"], actual_root)
        if code_mb != 0 or mbase != base_sha:
            errors.append({
                "code": "BASE_NOT_ANCESTOR",
                "message": f"Base SHA '{base_sha}' is not an ancestor of HEAD (merge-base: '{mbase}')"
            })

    # 9. Commit Limit Enforcement
    if code_base == 0:
        code_revs, rev_count_str, _ = _run_git(["rev-list", "--count", f"{base_sha}..HEAD"], actual_root)
        if code_revs == 0 and rev_count_str.isdigit():
            commit_count = int(rev_count_str)
            max_commits = contract.get("maximum_new_commits", 0)
            if commit_count > max_commits:
                errors.append({
                    "code": "COMMIT_LIMIT_EXCEEDED",
                    "message": f"New commit count ({commit_count}) exceeds contract maximum ({max_commits})"
                })

    # 10. File Path Allowlist / Denylist Checking
    # Compute changed files from git between base_sha and HEAD + uncommitted working tree
    changed_files = set()
    if code_base == 0:
        code_diff, diff_out, _ = _run_git(["diff", "--name-only", f"{base_sha}...HEAD"], actual_root)
        if code_diff == 0 and diff_out:
            for f in diff_out.splitlines():
                if f.strip():
                    changed_files.add(_normalize_path(f.strip()))

    # Include uncommitted working tree changes
    code_wt, wt_out, _ = _run_git(["diff", "--name-only", "HEAD"], actual_root)
    if code_wt == 0 and wt_out:
        for f in wt_out.splitlines():
            if f.strip():
                changed_files.add(_normalize_path(f.strip()))

    allowed_patterns = contract.get("allowed_paths", [])
    forbidden_patterns = contract.get("forbidden_paths", [])

    for f_path in sorted(changed_files):
        # 10a. Check forbidden patterns
        for f_pat in forbidden_patterns:
            if _path_matches(f_path, f_pat):
                errors.append({
                    "code": "FORBIDDEN_PATH_CHANGED",
                    "message": f"Forbidden path modified: '{f_path}' matched forbidden pattern '{f_pat}'"
                })
                break

        # 10b. Check allowed patterns
        is_allowed = any(_path_matches(f_path, a_pat) for a_pat in allowed_patterns)
        if not is_allowed:
            errors.append({
                "code": "PATH_OUTSIDE_ALLOWLIST",
                "message": f"Path outside allowlist modified: '{f_path}' does not match any allowed pattern"
            })

    # 11. Protected Artifact Hashing
    protected_artifacts = contract.get("protected_artifacts", {})
    for rel_path, expected_art_hash in protected_artifacts.items():
        art_path = actual_root / rel_path
        if not art_path.is_file():
            errors.append({
                "code": "PROTECTED_ARTIFACT_CHANGED",
                "message": f"Protected artifact missing: '{rel_path}'"
            })
        else:
            calc_art_hash = _compute_sha256_bytes(art_path.read_bytes())
            if calc_art_hash.lower() != expected_art_hash.lower():
                errors.append({
                    "code": "PROTECTED_ARTIFACT_CHANGED",
                    "message": f"Protected artifact hash mismatch on '{rel_path}': expected {expected_art_hash}, got {calc_art_hash}"
                })

    result_status = "PASS" if not errors else "FAIL"
    return {
        "status": result_status,
        "contract_task_id": contract.get("task_id"),
        "contract_hash": calc_hash,
        "expected_hash": target_expected_hash,
        "changed_files_count": len(changed_files),
        "changed_files": sorted(list(changed_files)),
        "authorizations": {
            "push": contract.get("push_authorized", False),
            "pull_request": contract.get("pr_creation_authorized", False),
            "merge": contract.get("merge_authorized", False),
            "deployment": contract.get("deployment_authorized", False),
        },
        "errors": errors,
    }


def main():
    parser = argparse.ArgumentParser(description="Task contract scope verifier for ProfSurProject")
    parser.add_argument("--contract", required=True, type=Path, help="Path to active task contract JSON")
    parser.add_argument("--expected-contract-sha256", dest="expected_hash", default=None, help="Expected SHA256 of contract")
    parser.add_argument("--base", default=None, help="Override base commit SHA")
    parser.add_argument("--json", action="store_true", help="Output verification report in JSON")
    args = parser.parse_args()

    res = verify_agent_scope(
        contract_path=args.contract,
        expected_hash=args.expected_hash,
        base_override=args.base,
    )

    if args.json:
        print(json.dumps(res, indent=2))
    else:
        print(f"=== Scope Verification: {res['status']} ===")
        if res["errors"]:
            for err in res["errors"]:
                print(f"  [{err['code']}] {err['message']}")
        else:
            print("All scope and authority boundaries verified successfully.")

    sys.exit(0 if res["status"] == "PASS" else 1)


if __name__ == "__main__":
    main()
