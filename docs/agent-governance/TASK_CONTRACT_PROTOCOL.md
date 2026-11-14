# TASK_CONTRACT_PROTOCOL.md — Machine-Verifiable Task Contracts

This protocol governs the authoring, distribution, cryptographic verification, and runtime enforcement of task contracts for autonomous implementation workers.

---

## 1. Core Principles

1. **External Contract Authoring:** Active task contracts are authored strictly by human operators or independent review authorities (e.g. Codex). Implementation workers never generate their own active authority contract.
2. **Cryptographic Integrity:** Every contract is verified against its SHA-256 hash passed via CLI (`--expected-contract-sha256`) or the environment variable `PROFSUR_TASK_CONTRACT_SHA256`. If the calculated hash does not match, execution fails closed.
3. **Fail-Closed Enforcement:** Missing expected contract hash, expired contract, branch mismatch, path outside allowlist, or modification of forbidden paths causes `scripts/verify_agent_scope.py` to exit with a nonzero status code.

---

## 2. Usage Instructions

### Verifying a Task Contract
```bash
py -3.12 scripts/verify_agent_scope.py \
  --contract <path-to-task-contract.json> \
  --expected-contract-sha256 <expected-64-char-hex-hash> \
  --json
```

### Inspecting Live Project Status
```bash
py -3.12 scripts/project_status.py --json
```

### Running the Governance Linter
```bash
py -3.12 scripts/validate_project_governance.py --json
```
