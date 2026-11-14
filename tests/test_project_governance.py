"""Tests for scripts/validate_project_governance.py.

Verifies detection of:
1. Two canonical-source claims
2. Hardcoded SHA in AGENTS.md
3. Plaintext credential patterns (with value redacted)
4. DEFAULT 'FILING_FACT' migration patterns
5. Hardcoded issuer-specific extractor values
6. PRE_IPO_REGISTRY in production analytical routes
7. Circular golden-oracle tests
8. Prohibited CLOSED_VERIFIED worker claims
9. Clean fixture with no findings
10. Allowlisted synthetic credential fixtures
"""
import json
import subprocess
import pytest
from pathlib import Path


def run_governance_cli(repo_dir: Path, *args):
    script_path = Path(__file__).resolve().parent.parent / "scripts" / "validate_project_governance.py"
    cmd = ["py", "-3.12", str(script_path)] + list(args)
    proc = subprocess.run(
        cmd,
        cwd=str(repo_dir),
        capture_output=True,
        text=True,
    )
    return proc


@pytest.fixture
def clean_repo(tmp_path):
    repo = tmp_path / "CleanRepo"
    repo.mkdir()
    (repo / "AGENTS.md").write_text("# Clean Constitution\nRules without hardcoded SHAs or branches.\n", encoding="utf-8")
    (repo / "CURRENT_STATUS.md").write_text("# Operational Summary\nUse project_status.py.\n", encoding="utf-8")
    return repo


def test_gov_linter_clean_repo(clean_repo):
    """Verify clean fixture returns zero errors/warnings and exit code 0."""
    proc = run_governance_cli(clean_repo, "--json")
    assert proc.returncode == 0
    data = json.loads(proc.stdout)
    assert data["errors_count"] == 0
    assert data["status"] in ("CLEAN", "PASS")


def test_gov_linter_detects_two_canonical_sources(clean_repo):
    """Verify detection of multiple files claiming to be the single canonical source."""
    (clean_repo / "DOC1.md").write_text("This document is the canonical source of truth for repository state.", encoding="utf-8")
    (clean_repo / "DOC2.md").write_text("This document is the canonical source of truth for the project.", encoding="utf-8")

    proc = run_governance_cli(clean_repo, "--json")
    data = json.loads(proc.stdout)
    findings = [f["rule_id"] for f in data.get("findings", [])]
    assert "MULTIPLE_CANONICAL_CLAIMS" in findings or any("canonical" in f["message"].lower() for f in data.get("findings", []))


def test_gov_linter_detects_hardcoded_sha_in_agents_md(clean_repo):
    """Verify detection of hardcoded baseline commit SHA in AGENTS.md."""
    (clean_repo / "AGENTS.md").write_text(
        "# AGENTS\nBaseline commit is `6462cbb5ac70deded664a4543e72c776fbed769a`.\n",
        encoding="utf-8"
    )
    proc = run_governance_cli(clean_repo, "--json")
    data = json.loads(proc.stdout)
    findings = [f["rule_id"] for f in data.get("findings", [])]
    assert "HARDCODED_SHA_IN_AGENTS_MD" in findings or any("sha" in f["message"].lower() for f in data.get("findings", []))


def test_gov_linter_detects_plaintext_credential_redacted(clean_repo):
    """Verify detection of plaintext credentials with secret value REDACTED in output."""
    (clean_repo / "script.py").write_text(
        'password = "SecretPassword123!"\n',
        encoding="utf-8"
    )
    proc = run_governance_cli(clean_repo, "--json")
    # Must detect finding
    assert "SecretPassword123!" not in proc.stdout, "Secret value was leaked in CLI stdout!"
    assert "SecretPassword123!" not in proc.stderr, "Secret value was leaked in CLI stderr!"
    data = json.loads(proc.stdout)
    findings = [f for f in data.get("findings", []) if "CREDENTIAL" in f.get("rule_id", "")]
    assert len(findings) > 0
    assert findings[0]["matched_snippet"] == "[REDACTED]" or "SecretPassword123!" not in str(findings[0])


def test_gov_linter_detects_default_filing_fact(clean_repo):
    """Verify detection of DEFAULT 'FILING_FACT' permissive migration pattern."""
    sql_dir = clean_repo / "models" / "migrations"
    sql_dir.mkdir(parents=True)
    (sql_dir / "003_migration.sql").write_text(
        "ALTER TABLE observations ADD COLUMN origin TEXT NOT NULL DEFAULT 'FILING_FACT';\n",
        encoding="utf-8"
    )
    proc = run_governance_cli(clean_repo, "--json")
    data = json.loads(proc.stdout)
    rule_ids = [f["rule_id"] for f in data.get("findings", [])]
    assert "PERMISSIVE_MIGRATION_DEFAULT" in rule_ids or any("filing_fact" in str(f).lower() for f in data.get("findings", []))


def test_gov_linter_detects_hardcoded_issuer_extractor(clean_repo):
    """Verify detection of issuer-specific keyword extraction hardcoding expected numerical results."""
    indexer_file = clean_repo / "models" / "extractor.py"
    indexer_file.parent.mkdir(parents=True, exist_ok=True)
    indexer_file.write_text(
        'if "hindustan coca cola" in text.lower():\n    return {"revenue_cr": 3450.5, "status": "ACCEPTED"}\n',
        encoding="utf-8"
    )
    proc = run_governance_cli(clean_repo, "--json")
    data = json.loads(proc.stdout)
    rule_ids = [f["rule_id"] for f in data.get("findings", [])]
    assert "PSEUDO_EXTRACTION_ORACLE" in rule_ids or any("extractor" in str(f).lower() for f in data.get("findings", []))


def test_gov_linter_detects_pre_ipo_registry_production_usage(clean_repo):
    """Verify detection of PRE_IPO_REGISTRY references in production page routes."""
    page_dir = clean_repo / "pages"
    page_dir.mkdir(parents=True)
    (page_dir / "27_pre_ipo_drhp.py").write_text(
        "from models.pre_ipo_data import PRE_IPO_REGISTRY\ndossier = PRE_IPO_REGISTRY[selected_deal_key]\n",
        encoding="utf-8"
    )
    proc = run_governance_cli(clean_repo, "--json")
    data = json.loads(proc.stdout)
    rule_ids = [f["rule_id"] for f in data.get("findings", [])]
    assert "PRODUCTION_REGISTRY_USAGE" in rule_ids or any("pre_ipo_registry" in str(f).lower() for f in data.get("findings", []))


def test_gov_linter_detects_circular_golden_oracle_test(clean_repo):
    """Verify detection of tests comparing golden fixture directly against PRE_IPO_REGISTRY."""
    tests_dir = clean_repo / "tests"
    tests_dir.mkdir(parents=True)
    (tests_dir / "test_golden_oracles.py").write_text(
        "def test_oracle():\n    assert golden_fixture['revenue'] == PRE_IPO_REGISTRY[key].revenue\n",
        encoding="utf-8"
    )
    proc = run_governance_cli(clean_repo, "--json")
    data = json.loads(proc.stdout)
    rule_ids = [f["rule_id"] for f in data.get("findings", [])]
    assert "CIRCULAR_GOLDEN_ORACLE_TEST" in rule_ids or any("circular" in str(f).lower() for f in data.get("findings", []))


def test_gov_linter_detects_closed_verified_worker_claim(clean_repo):
    """Verify detection of worker reports claiming prohibited CLOSED_VERIFIED status."""
    docs_dir = clean_repo / "docs" / "review-evidence"
    docs_dir.mkdir(parents=True)
    (docs_dir / "REPORT.md").write_text(
        "Worker Completion Status: CLOSED_VERIFIED\nAll tests passed.\n",
        encoding="utf-8"
    )
    proc = run_governance_cli(clean_repo, "--json")
    data = json.loads(proc.stdout)
    rule_ids = [f["rule_id"] for f in data.get("findings", [])]
    assert "PROHIBITED_SELF_APPROVAL" in rule_ids or any("closed_verified" in str(f).lower() for f in data.get("findings", []))


def test_gov_linter_allowlist_synthetic_credential(clean_repo):
    """Verify that allowlisted synthetic credentials in documented test fixtures do not trigger error."""
    tests_dir = clean_repo / "tests"
    tests_dir.mkdir(parents=True)
    (tests_dir / "fixture_credentials.py").write_text(
        '# ALLOWLIST_SYNTHETIC_CREDENTIAL\nTEST_TOKEN = "synthetic-dummy-token-00000"\n',
        encoding="utf-8"
    )
    proc = run_governance_cli(clean_repo, "--json")
    data = json.loads(proc.stdout)
    # Should not report credential finding for allowlisted file
    cred_findings = [f for f in data.get("findings", []) if "CREDENTIAL" in f.get("rule_id", "")]
    assert len(cred_findings) == 0
