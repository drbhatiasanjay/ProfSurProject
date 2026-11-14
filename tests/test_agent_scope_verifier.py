"""Tests for scripts/verify_agent_scope.py.

Verifies strict machine-enforced scope boundary:
- contract hash verification
- expiration checks
- repository / workspace / branch validation
- allowed_paths vs forbidden_paths enforcement
- protected artifact hashing
- commit limit checking
- safe error handling for malformed input
"""
import hashlib
import json
import os
import subprocess
import tempfile
import pytest
from datetime import datetime, timezone, timedelta
from pathlib import Path


def run_scope_cli(repo_dir: Path, *args):
    script_path = Path(__file__).resolve().parent.parent / "scripts" / "verify_agent_scope.py"
    cmd = ["py", "-3.12", str(script_path)] + list(args)
    proc = subprocess.run(
        cmd,
        cwd=str(repo_dir),
        capture_output=True,
        text=True,
    )
    return proc


def compute_sha256(content: str) -> str:
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


def make_dummy_contract(
    repo_dir: Path,
    base_sha: str,
    worker_branch: str = "chore/test-governance",
    allowed_paths=None,
    forbidden_paths=None,
    expires_delta_hours=24,
    protected_artifacts=None,
    max_commits=5,
    extra_props=None,
):
    if allowed_paths is None:
        allowed_paths = ["AGENTS.md", "scripts/**", "tests/**"]
    if forbidden_paths is None:
        forbidden_paths = ["models/**", "pages/**", "app.py"]
    if protected_artifacts is None:
        protected_artifacts = {}

    exp = datetime.now(timezone.utc) + timedelta(hours=expires_delta_hours)
    created = datetime.now(timezone.utc) - timedelta(hours=1)

    contract = {
        "schema_version": "2026-11-14",
        "task_id": "TEST_TASK_001",
        "authority": "CODEX_INDEPENDENT_REVIEWER",
        "mode": "WORKER_IMPLEMENTATION_ONLY",
        "repository": "ProfSurProject",
        "workspace": str(repo_dir),
        "base_branch": "master",
        "base_sha": base_sha,
        "worker_branch": worker_branch,
        "authorized_packet": "TEST_PACKET_2026_11_14",
        "allowed_objectives": ["Implement test governance controls"],
        "forbidden_objectives": ["Touch production code"],
        "allowed_paths": allowed_paths,
        "forbidden_paths": forbidden_paths,
        "required_tests": ["tests/test_project_status.py"],
        "stop_conditions": ["READY_FOR_CODEX_REMOTE_REVIEW"],
        "maximum_new_commits": max_commits,
        "push_authorized": False,
        "pr_creation_authorized": False,
        "merge_authorized": False,
        "deployment_authorized": False,
        "protected_artifacts": protected_artifacts,
        "created_at": created.isoformat(),
        "expires_at": exp.isoformat(),
    }
    if extra_props:
        contract.update(extra_props)
    return contract


@pytest.fixture
def test_git_repo(tmp_path):
    repo = tmp_path / "ProfSurProject"
    repo.mkdir()
    subprocess.run(["git", "init", "-b", "master"], cwd=str(repo), check=True, capture_output=True)
    subprocess.run(["git", "config", "user.email", "tester@example.com"], cwd=str(repo), check=True)
    subprocess.run(["git", "config", "user.name", "Tester"], cwd=str(repo), check=True)

    # Base commit
    (repo / "AGENTS.md").write_text("# Agents Base", encoding="utf-8")
    (repo / "app.py").write_text("# Production app", encoding="utf-8")
    subprocess.run(["git", "add", "."], cwd=str(repo), check=True)
    subprocess.run(["git", "commit", "-m", "initial base"], cwd=str(repo), check=True)
    base_sha = subprocess.run(["git", "rev-parse", "HEAD"], cwd=str(repo), capture_output=True, text=True, check=True).stdout.strip()

    # Checkout worker branch
    worker_branch = "chore/test-governance"
    subprocess.run(["git", "checkout", "-b", worker_branch], cwd=str(repo), check=True, capture_output=True)

    return repo, base_sha, worker_branch


def test_scope_verifier_valid_change_passes(test_git_repo, tmp_path):
    """Verify that a valid allowed change passes with exit code 0."""
    repo, base_sha, worker_branch = test_git_repo
    # Make allowed change
    (repo / "AGENTS.md").write_text("# Updated Agents", encoding="utf-8")
    subprocess.run(["git", "add", "AGENTS.md"], cwd=str(repo), check=True)
    subprocess.run(["git", "commit", "-m", "update agents"], cwd=str(repo), check=True)

    contract = make_dummy_contract(repo, base_sha, worker_branch)
    contract_path = tmp_path / "task-contract.json"
    raw_bytes = json.dumps(contract, indent=2).encode("utf-8")
    contract_path.write_bytes(raw_bytes)
    contract_hash = hashlib.sha256(raw_bytes).hexdigest()

    proc = run_scope_cli(repo, "--contract", str(contract_path), "--expected-contract-sha256", contract_hash, "--json")
    assert proc.returncode == 0, f"Scope verifier failed: {proc.stderr}\n{proc.stdout}"
    data = json.loads(proc.stdout)
    assert data["status"] == "PASS"


def test_scope_verifier_forbidden_file_fails(test_git_repo, tmp_path):
    """Verify that changing a forbidden file fails with FORBIDDEN_PATH_CHANGED."""
    repo, base_sha, worker_branch = test_git_repo
    # Modify forbidden file
    (repo / "app.py").write_text("# Tampered production app", encoding="utf-8")
    subprocess.run(["git", "add", "app.py"], cwd=str(repo), check=True)
    subprocess.run(["git", "commit", "-m", "illegal change to app.py"], cwd=str(repo), check=True)

    contract = make_dummy_contract(repo, base_sha, worker_branch)
    contract_path = tmp_path / "task-contract.json"
    raw_bytes = json.dumps(contract, indent=2).encode("utf-8")
    contract_path.write_bytes(raw_bytes)
    contract_hash = hashlib.sha256(raw_bytes).hexdigest()

    proc = run_scope_cli(repo, "--contract", str(contract_path), "--expected-contract-sha256", contract_hash, "--json")
    assert proc.returncode != 0
    data = json.loads(proc.stdout)
    assert data["status"] == "FAIL"
    error_codes = [err["code"] for err in data.get("errors", [])]
    assert "FORBIDDEN_PATH_CHANGED" in error_codes


def test_scope_verifier_unlisted_path_fails(test_git_repo, tmp_path):
    """Verify that changing a path not in allowed_paths fails with PATH_OUTSIDE_ALLOWLIST."""
    repo, base_sha, worker_branch = test_git_repo
    # Add unlisted file
    (repo / "random_script.py").write_text("# Unlisted file", encoding="utf-8")
    subprocess.run(["git", "add", "random_script.py"], cwd=str(repo), check=True)
    subprocess.run(["git", "commit", "-m", "unlisted file"], cwd=str(repo), check=True)

    contract = make_dummy_contract(repo, base_sha, worker_branch)
    contract_path = tmp_path / "task-contract.json"
    raw_bytes = json.dumps(contract, indent=2).encode("utf-8")
    contract_path.write_bytes(raw_bytes)
    contract_hash = hashlib.sha256(raw_bytes).hexdigest()

    proc = run_scope_cli(repo, "--contract", str(contract_path), "--expected-contract-sha256", contract_hash, "--json")
    assert proc.returncode != 0
    data = json.loads(proc.stdout)
    assert "PATH_OUTSIDE_ALLOWLIST" in [e["code"] for e in data.get("errors", [])]


def test_scope_verifier_wrong_branch_fails(test_git_repo, tmp_path):
    """Verify that being on the wrong branch fails with BRANCH_MISMATCH."""
    repo, base_sha, _ = test_git_repo
    contract = make_dummy_contract(repo, base_sha, worker_branch="feature/different-branch")
    contract_path = tmp_path / "task-contract.json"
    raw_bytes = json.dumps(contract).encode("utf-8")
    contract_path.write_bytes(raw_bytes)
    contract_hash = hashlib.sha256(raw_bytes).hexdigest()

    proc = run_scope_cli(repo, "--contract", str(contract_path), "--expected-contract-sha256", contract_hash, "--json")
    assert proc.returncode != 0
    data = json.loads(proc.stdout)
    assert "BRANCH_MISMATCH" in [e["code"] for e in data.get("errors", [])]


def test_scope_verifier_wrong_repo_fails(test_git_repo, tmp_path):
    """Verify that repository mismatch fails with REPOSITORY_MISMATCH."""
    repo, base_sha, worker_branch = test_git_repo
    contract = make_dummy_contract(repo, base_sha, worker_branch)
    contract["repository"] = "OtherProject"
    contract_path = tmp_path / "task-contract.json"
    raw_bytes = json.dumps(contract).encode("utf-8")
    contract_path.write_bytes(raw_bytes)
    contract_hash = hashlib.sha256(raw_bytes).hexdigest()

    proc = run_scope_cli(repo, "--contract", str(contract_path), "--expected-contract-sha256", contract_hash, "--json")
    assert proc.returncode != 0
    data = json.loads(proc.stdout)
    assert "REPOSITORY_MISMATCH" in [e["code"] for e in data.get("errors", [])]


def test_scope_verifier_wrong_base_sha_fails(test_git_repo, tmp_path):
    """Verify that invalid base_sha fails with BASE_SHA_MISSING or BASE_NOT_ANCESTOR."""
    repo, _, worker_branch = test_git_repo
    fake_sha = "0000000000000000000000000000000000000000"
    contract = make_dummy_contract(repo, fake_sha, worker_branch)
    contract_path = tmp_path / "task-contract.json"
    raw_bytes = json.dumps(contract).encode("utf-8")
    contract_path.write_bytes(raw_bytes)
    contract_hash = hashlib.sha256(raw_bytes).hexdigest()

    proc = run_scope_cli(repo, "--contract", str(contract_path), "--expected-contract-sha256", contract_hash, "--json")
    assert proc.returncode != 0
    data = json.loads(proc.stdout)
    codes = [e["code"] for e in data.get("errors", [])]
    assert "BASE_SHA_MISSING" in codes or "BASE_NOT_ANCESTOR" in codes


def test_scope_verifier_contract_hash_mismatch(test_git_repo, tmp_path):
    """Verify that contract hash mismatch fails with CONTRACT_HASH_MISMATCH."""
    repo, base_sha, worker_branch = test_git_repo
    contract = make_dummy_contract(repo, base_sha, worker_branch)
    contract_path = tmp_path / "task-contract.json"
    contract_text = json.dumps(contract)
    contract_path.write_text(contract_text, encoding="utf-8")

    wrong_hash = "abcdef0123456789abcdef0123456789abcdef0123456789abcdef0123456789"
    proc = run_scope_cli(repo, "--contract", str(contract_path), "--expected-contract-sha256", wrong_hash, "--json")
    assert proc.returncode != 0
    data = json.loads(proc.stdout)
    assert "CONTRACT_HASH_MISMATCH" in [e["code"] for e in data.get("errors", [])]


def test_scope_verifier_missing_expected_hash_fails(test_git_repo, tmp_path):
    """Verify that missing expected hash fails closed with EXPECTED_CONTRACT_HASH_REQUIRED."""
    repo, base_sha, worker_branch = test_git_repo
    contract = make_dummy_contract(repo, base_sha, worker_branch)
    contract_path = tmp_path / "task-contract.json"
    contract_path.write_text(json.dumps(contract), encoding="utf-8")

    proc = run_scope_cli(repo, "--contract", str(contract_path), "--json")
    assert proc.returncode != 0
    data = json.loads(proc.stdout)
    assert "EXPECTED_CONTRACT_HASH_REQUIRED" in [e["code"] for e in data.get("errors", [])]


def test_scope_verifier_expired_contract_fails(test_git_repo, tmp_path):
    """Verify that an expired contract fails with CONTRACT_EXPIRED."""
    repo, base_sha, worker_branch = test_git_repo
    contract = make_dummy_contract(repo, base_sha, worker_branch, expires_delta_hours=-2)  # Expired 2h ago
    contract_path = tmp_path / "task-contract.json"
    raw_bytes = json.dumps(contract).encode("utf-8")
    contract_path.write_bytes(raw_bytes)
    contract_hash = hashlib.sha256(raw_bytes).hexdigest()

    proc = run_scope_cli(repo, "--contract", str(contract_path), "--expected-contract-sha256", contract_hash, "--json")
    assert proc.returncode != 0
    data = json.loads(proc.stdout)
    assert "CONTRACT_EXPIRED" in [e["code"] for e in data.get("errors", [])]


def test_scope_verifier_commit_limit_exceeded_fails(test_git_repo, tmp_path):
    """Verify that exceeding maximum_new_commits fails with COMMIT_LIMIT_EXCEEDED."""
    repo, base_sha, worker_branch = test_git_repo
    # Max commits = 1, but we create 2 commits
    contract = make_dummy_contract(repo, base_sha, worker_branch, max_commits=1)
    contract_path = tmp_path / "task-contract.json"
    raw_bytes = json.dumps(contract).encode("utf-8")
    contract_path.write_bytes(raw_bytes)
    contract_hash = hashlib.sha256(raw_bytes).hexdigest()

    (repo / "AGENTS.md").write_text("# Commit 1", encoding="utf-8")
    subprocess.run(["git", "commit", "-am", "c1"], cwd=str(repo), check=True)
    (repo / "AGENTS.md").write_text("# Commit 2", encoding="utf-8")
    subprocess.run(["git", "commit", "-am", "c2"], cwd=str(repo), check=True)

    proc = run_scope_cli(repo, "--contract", str(contract_path), "--expected-contract-sha256", contract_hash, "--json")
    assert proc.returncode != 0
    data = json.loads(proc.stdout)
    assert "COMMIT_LIMIT_EXCEEDED" in [e["code"] for e in data.get("errors", [])]


def test_scope_verifier_protected_artifact_hash_mismatch(test_git_repo, tmp_path):
    """Verify that tampering with a protected artifact fails with PROTECTED_ARTIFACT_CHANGED."""
    repo, base_sha, worker_branch = test_git_repo
    db = repo / "capital_structure.db"
    db.write_bytes(b"initial db")
    db_hash = hashlib.sha256(b"initial db").hexdigest()

    contract = make_dummy_contract(
        repo, base_sha, worker_branch,
        protected_artifacts={"capital_structure.db": db_hash}
    )
    # Tamper with the db
    db.write_bytes(b"tampered db")

    contract_path = tmp_path / "task-contract.json"
    raw_bytes = json.dumps(contract).encode("utf-8")
    contract_path.write_bytes(raw_bytes)
    contract_hash = hashlib.sha256(raw_bytes).hexdigest()

    proc = run_scope_cli(repo, "--contract", str(contract_path), "--expected-contract-sha256", contract_hash, "--json")
    assert proc.returncode != 0
    data = json.loads(proc.stdout)
    assert "PROTECTED_ARTIFACT_CHANGED" in [e["code"] for e in data.get("errors", [])]


def test_scope_verifier_path_normalization(test_git_repo, tmp_path):
    """Verify Windows backslashes and POSIX slashes normalize identically."""
    repo, base_sha, worker_branch = test_git_repo
    contract = make_dummy_contract(
        repo, base_sha, worker_branch,
        allowed_paths=["scripts/**", "docs/review-evidence/*"],
        forbidden_paths=["models\\**", "pages/**"]
    )
    contract_path = tmp_path / "task-contract.json"
    raw_bytes = json.dumps(contract).encode("utf-8")
    contract_path.write_bytes(raw_bytes)
    contract_hash = hashlib.sha256(raw_bytes).hexdigest()

    # Valid change using subfolder
    sub = repo / "scripts"
    sub.mkdir(exist_ok=True)
    (sub / "test.py").write_text("# new test", encoding="utf-8")
    subprocess.run(["git", "add", "."], cwd=str(repo), check=True)
    subprocess.run(["git", "commit", "-m", "add script"], cwd=str(repo), check=True)

    proc = run_scope_cli(repo, "--contract", str(contract_path), "--expected-contract-sha256", contract_hash, "--json")
    assert proc.returncode == 0


def test_scope_verifier_unknown_schema_property_rejected(test_git_repo, tmp_path):
    """Verify that unknown schema properties in task-contract are rejected."""
    repo, base_sha, worker_branch = test_git_repo
    contract = make_dummy_contract(
        repo, base_sha, worker_branch,
        extra_props={"unauthorized_extra_field": "injected_value"}
    )
    contract_path = tmp_path / "task-contract.json"
    raw_bytes = json.dumps(contract).encode("utf-8")
    contract_path.write_bytes(raw_bytes)
    contract_hash = hashlib.sha256(raw_bytes).hexdigest()

    proc = run_scope_cli(repo, "--contract", str(contract_path), "--expected-contract-sha256", contract_hash, "--json")
    assert proc.returncode != 0
    data = json.loads(proc.stdout)
    assert any("SCHEMA" in err.get("code", "") or "INVALID" in err.get("code", "") for err in data.get("errors", []))
