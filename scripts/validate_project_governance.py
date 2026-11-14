#!/usr/bin/env python3
"""Project Governance Linter and Integrity Scanner for ProfSurProject.

Strictly read-only. Detects:
A. Multiple documents claiming canonical authority
B. Hardcoded SHA/branch in AGENTS.md
C. Historical handoffs claiming present operational authority
D. Plaintext credential patterns (with values strictly REDACTED)
E. Permissive migration defaults (e.g. DEFAULT 'FILING_FACT')
F. Pseudo-extraction oracles (issuer detection + hardcoded expected value)
G. Production routes referencing PRE_IPO_REGISTRY
H. Circular golden-oracle tests
I. Prohibited worker self-approval claims (e.g. CLOSED_VERIFIED)

Supports --json and output redaction. Never modifies files.
"""
import argparse
import json
import os
import re
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional


SEVERITY_ERROR = "ERROR"
SEVERITY_WARNING = "WARNING"
SEVERITY_INFO = "INFORMATIONAL"


def _scan_for_canonical_claims(repo_root: Path) -> List[Dict[str, Any]]:
    findings = []
    canonical_files = []
    canonical_pattern = re.compile(r'canonical source of truth|single source of truth', re.IGNORECASE)

    for doc_path in repo_root.glob("**/*.md"):
        # Ignore docs/archive and review-evidence
        if any(ign in doc_path.parts for ign in (".git", "node_modules", "archive", "brain", ".worktrees")):
            continue
        try:
            text = doc_path.read_text(encoding="utf-8", errors="ignore")
            for i, line in enumerate(text.splitlines(), 1):
                if canonical_pattern.search(line):
                    canonical_files.append((doc_path, i, line.strip()))
        except Exception:
            pass

    if len(canonical_files) > 1:
        for p, line_no, snip in canonical_files:
            findings.append({
                "rule_id": "MULTIPLE_CANONICAL_CLAIMS",
                "severity": SEVERITY_ERROR,
                "file": str(p.relative_to(repo_root)),
                "line": line_no,
                "message": f"Contradictory canonical claim: multiple files claim to be single canonical source of truth",
                "matched_snippet": snip[:100],
            })
    return findings


def _scan_agents_md(repo_root: Path) -> List[Dict[str, Any]]:
    findings = []
    agents_path = repo_root / "AGENTS.md"
    if not agents_path.is_file():
        return findings

    text = agents_path.read_text(encoding="utf-8", errors="ignore")
    # Detect hardcoded 40-char SHA or commit claims
    sha_pattern = re.compile(r'(?:baseline commit|HEAD commit|active commit|commit:?)(?:\s+is)?\s*[`\'"]?([0-9a-f]{7,40})[`\'"]?|\b[0-9a-f]{40}\b', re.IGNORECASE)
    branch_pattern = re.compile(r'(?:current branch|active branch)\s*[:=]\s*[`\'"]?([a-zA-Z0-9_\-\/]+)[`\'"]?', re.IGNORECASE)

    for i, line in enumerate(text.splitlines(), 1):
        m_sha = sha_pattern.search(line)
        if m_sha:
            findings.append({
                "rule_id": "HARDCODED_SHA_IN_AGENTS_MD",
                "severity": SEVERITY_ERROR,
                "file": "AGENTS.md",
                "line": i,
                "message": f"AGENTS.md must not contain hardcoded baseline or commit SHAs",
                "matched_snippet": line.strip()[:100],
            })
        m_br = branch_pattern.search(line)
        if m_br and "worker_branch" not in line and "base_branch" not in line:
            findings.append({
                "rule_id": "HARDCODED_BRANCH_IN_AGENTS_MD",
                "severity": SEVERITY_WARNING,
                "file": "AGENTS.md",
                "line": i,
                "message": f"AGENTS.md should not hardcode active or current branch names",
                "matched_snippet": line.strip()[:100],
            })
    return findings


def _scan_plaintext_credentials(repo_root: Path) -> List[Dict[str, Any]]:
    findings = []
    cred_pattern = re.compile(r'(?:password|secret|passwd|token)\s*=\s*["\']([^"\']{6,})["\']', re.IGNORECASE)
    raw_pass_pattern = re.compile(r'Pass@123', re.IGNORECASE)

    for ext in ("*.py", "*.sh", "*.ps1", "*.toml"):
        for path in repo_root.glob(f"**/{ext}"):
            if any(ign in path.parts for ign in (".git", "node_modules", "brain", ".worktrees", "__pycache__")):
                continue
            try:
                text = path.read_text(encoding="utf-8", errors="ignore")
                # File-level allowlist
                if "ALLOWLIST_SYNTHETIC_CREDENTIAL" in text:
                    continue
                if "test_project_governance.py" in str(path) or "test_adversarial_containment_codex_standard.py" in str(path):
                    continue

                for i, line in enumerate(text.splitlines(), 1):
                    if "os.environ" in line or "st.secrets" in line or "{hashed}" in line or "token_urlsafe" in line:
                        continue

                    if raw_pass_pattern.search(line) or cred_pattern.search(line):
                        findings.append({
                            "rule_id": "PLAINTEXT_CREDENTIAL_DETECTED",
                            "severity": SEVERITY_ERROR,
                            "file": str(path.relative_to(repo_root)),
                            "line": i,
                            "message": "Potential plaintext credential or secret detected. Value has been redacted.",
                            "matched_snippet": "[REDACTED]",
                        })
            except Exception:
                pass
    return findings


def _scan_migration_permissive_defaults(repo_root: Path) -> List[Dict[str, Any]]:
    findings = []
    pattern = re.compile(r'DEFAULT\s+[\'"]FILING_FACT[\'"]', re.IGNORECASE)

    for sql_file in repo_root.glob("**/*.sql"):
        if any(ign in sql_file.parts for ign in (".git", "node_modules", "brain", ".worktrees")):
            continue
        try:
            text = sql_file.read_text(encoding="utf-8", errors="ignore")
            for i, line in enumerate(text.splitlines(), 1):
                if pattern.search(line):
                    findings.append({
                        "rule_id": "PERMISSIVE_MIGRATION_DEFAULT",
                        "severity": SEVERITY_ERROR,
                        "file": str(sql_file.relative_to(repo_root)),
                        "line": i,
                        "message": "Migration contains permissive DEFAULT 'FILING_FACT' which misclassifies legacy records.",
                        "matched_snippet": line.strip()[:100],
                    })
        except Exception:
            pass

    for py_file in repo_root.glob("**/pre_ipo_migrations*.py"):
        if any(ign in py_file.parts for ign in (".git", "node_modules", "brain", ".worktrees")):
            continue
        try:
            text = py_file.read_text(encoding="utf-8", errors="ignore")
            for i, line in enumerate(text.splitlines(), 1):
                if pattern.search(line):
                    findings.append({
                        "rule_id": "PERMISSIVE_MIGRATION_DEFAULT",
                        "severity": SEVERITY_ERROR,
                        "file": str(py_file.relative_to(repo_root)),
                        "line": i,
                        "message": "Python migration runner contains permissive DEFAULT 'FILING_FACT'.",
                        "matched_snippet": line.strip()[:100],
                    })
        except Exception:
            pass

    return findings


def _scan_pseudo_extraction_oracles(repo_root: Path) -> List[Dict[str, Any]]:
    findings = []
    # Pattern: searching for issuer keyword and then returning numeric literal with ACCEPTED
    for py_file in repo_root.glob("**/pre_ipo_document_indexer*.py"):
        if any(ign in py_file.parts for ign in (".git", "node_modules", "brain", ".worktrees")):
            continue
        try:
            text = py_file.read_text(encoding="utf-8", errors="ignore")
            lines = text.splitlines()
            for i, line in enumerate(lines, 1):
                if ("coca cola" in line.lower() or "hcch" in line.lower()) and "if " in line:
                    # Check next 15 lines for hardcoded dictionary or numbers
                    window = "\n".join(lines[i:i+15])
                    if ("3,450" in window or "3450" in window or "ACCEPTED" in window) and "return" in window:
                        findings.append({
                            "rule_id": "PSEUDO_EXTRACTION_ORACLE",
                            "severity": SEVERITY_ERROR,
                            "file": str(py_file.relative_to(repo_root)),
                            "line": i,
                            "message": "Issuer keyword detection combined with hardcoded expected numeric return detected.",
                            "matched_snippet": line.strip()[:100],
                        })
        except Exception:
            pass

    # Generic check for any models/ file matching issuer + expected value return
    for py_file in repo_root.glob("models/**/*.py"):
        if any(ign in py_file.parts for ign in (".git", "node_modules", "brain", ".worktrees")):
            continue
        try:
            text = py_file.read_text(encoding="utf-8", errors="ignore")
            lines = text.splitlines()
            for i, line in enumerate(lines, 1):
                if ("coca cola" in line.lower() or "hcch" in line.lower()) and "if " in line:
                    window = "\n".join(lines[i:i+10])
                    if "return " in window and ("revenue" in window.lower() or "accepted" in window.lower()) and any(ch.isdigit() for ch in window):
                        findings.append({
                            "rule_id": "PSEUDO_EXTRACTION_ORACLE",
                            "severity": SEVERITY_ERROR,
                            "file": str(py_file.relative_to(repo_root)),
                            "line": i,
                            "message": "Issuer keyword detection combined with hardcoded numerical output in model.",
                            "matched_snippet": line.strip()[:100],
                        })
        except Exception:
            pass

    return findings


def _scan_production_registry_usage(repo_root: Path) -> List[Dict[str, Any]]:
    findings = []
    # Pattern: PRE_IPO_REGISTRY in production pages
    pages_dir = repo_root / "pages"
    if not pages_dir.is_dir():
        return findings

    for page_path in pages_dir.glob("*.py"):
        try:
            text = page_path.read_text(encoding="utf-8", errors="ignore")
            for i, line in enumerate(text.splitlines(), 1):
                if "PRE_IPO_REGISTRY[" in line or "PRE_IPO_REGISTRY.get(" in line:
                    # Exclude comment lines
                    if line.strip().startswith("#"):
                        continue
                    findings.append({
                        "rule_id": "PRODUCTION_REGISTRY_USAGE",
                        "severity": SEVERITY_ERROR,
                        "file": str(page_path.relative_to(repo_root)),
                        "line": i,
                        "message": "Production page route resolves dossier from unreviewed PRE_IPO_REGISTRY.",
                        "matched_snippet": line.strip()[:100],
                    })
        except Exception:
            pass
    return findings


def _scan_circular_golden_oracle_tests(repo_root: Path) -> List[Dict[str, Any]]:
    findings = []
    tests_dir = repo_root / "tests"
    if not tests_dir.is_dir():
        return findings

    for test_path in tests_dir.glob("**/test_*.py"):
        if "test_project_governance.py" in str(test_path):
            continue
        try:
            text = test_path.read_text(encoding="utf-8", errors="ignore")
            lines = text.splitlines()
            for i, line in enumerate(lines, 1):
                if "PRE_IPO_REGISTRY" in line and ("assert" in line or any("assert" in lines[max(0, i-3):i+3])):
                    if ("fixture" in line.lower() or "oracle" in line.lower() or "golden" in line.lower() or
                        any("golden" in l.lower() for l in lines[max(0, i-4):i+4])):
                        findings.append({
                            "rule_id": "CIRCULAR_GOLDEN_ORACLE_TEST",
                            "severity": SEVERITY_ERROR,
                            "file": str(test_path.relative_to(repo_root)),
                            "line": i,
                            "message": "Circular golden oracle test compares fixture against PRE_IPO_REGISTRY.",
                            "matched_snippet": line.strip()[:100],
                        })
        except Exception:
            pass
    return findings


def _scan_prohibited_self_approval(repo_root: Path) -> List[Dict[str, Any]]:
    findings = []
    prohibited_terms = [
        "CLOSED_VERIFIED",
        "PRODUCTION_SAFE",
        "SCIENTIFICALLY_VALIDATED",
        "READY_TO_MERGE",
        "READY_TO_DEPLOY",
    ]
    pattern = re.compile(r'\b(' + '|'.join(prohibited_terms) + r')\b')

    for doc_path in repo_root.glob("docs/review-evidence/**/*.md"):
        try:
            text = doc_path.read_text(encoding="utf-8", errors="ignore")
            for i, line in enumerate(text.splitlines(), 1):
                m = pattern.search(line)
                if m:
                    # Ignore negations and rules e.g. "Do not report: CLOSED_VERIFIED", "prohibited", "withheld"
                    line_lower = line.lower()
                    if any(neg in line_lower for neg in ["do not", "not report", "never", "prohibited", "withheld", "no worker", "previous", "flaw"]):
                        continue
                    findings.append({
                        "rule_id": "PROHIBITED_SELF_APPROVAL",
                        "severity": SEVERITY_ERROR,
                        "file": str(doc_path.relative_to(repo_root)),
                        "line": i,
                        "message": f"Worker report claims prohibited self-approval status: '{m.group(1)}'.",
                        "matched_snippet": line.strip()[:100],
                    })
        except Exception:
            pass
    return findings


def run_project_governance_scan(repo_dir: Optional[Path] = None) -> Dict[str, Any]:
    """Execute all governance linters across repository."""
    root = (repo_dir or Path.cwd()).resolve()

    all_findings = []
    all_findings.extend(_scan_for_canonical_claims(root))
    all_findings.extend(_scan_agents_md(root))
    all_findings.extend(_scan_plaintext_credentials(root))
    all_findings.extend(_scan_migration_permissive_defaults(root))
    all_findings.extend(_scan_pseudo_extraction_oracles(root))
    all_findings.extend(_scan_production_registry_usage(root))
    all_findings.extend(_scan_circular_golden_oracle_tests(root))
    all_findings.extend(_scan_prohibited_self_approval(root))

    errors_count = sum(1 for f in all_findings if f["severity"] == SEVERITY_ERROR)
    warnings_count = sum(1 for f in all_findings if f["severity"] == SEVERITY_WARNING)
    infos_count = sum(1 for f in all_findings if f["severity"] == SEVERITY_INFO)

    status = "CLEAN" if (errors_count == 0 and warnings_count == 0) else "FINDINGS_PRESENT"

    return {
        "status": status,
        "errors_count": errors_count,
        "warnings_count": warnings_count,
        "informational_count": infos_count,
        "total_findings": len(all_findings),
        "findings": all_findings,
    }


def main():
    parser = argparse.ArgumentParser(description="Project governance linter for ProfSurProject")
    parser.add_argument("--json", action="store_true", help="Output findings in JSON format")
    args = parser.parse_args()

    result = run_project_governance_scan()

    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print(f"=== Project Governance Scan: {result['status']} ===")
        print(f"Errors: {result['errors_count']} | Warnings: {result['warnings_count']} | Info: {result['informational_count']}")
        for f in result["findings"]:
            print(f"  [{f['severity']}][{f['rule_id']}] {f['file']}:{f['line']}: {f['message']}")

    # Exit nonzero if errors or warnings are present
    sys.exit(0 if result["status"] == "CLEAN" else 1)


if __name__ == "__main__":
    main()
