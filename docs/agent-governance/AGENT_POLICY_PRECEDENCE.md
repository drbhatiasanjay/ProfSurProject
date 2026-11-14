# AGENT_POLICY_PRECEDENCE.md — Operational Authority & Conflict Hierarchy

This document details the operational authority hierarchy, precedence rules, and automated conflict-resolution protocol for autonomous agents working on **ProfSurProject**.

---

## 1. Precedence Levels

```
Level 1: Current User Authorization (Interactive Prompt)
   │
   ▼
Level 2: Active Task Contract (task-contract.json verified by SHA-256)
   │
   ▼
Level 3: Runtime Git & Filesystem State (scripts/project_status.py)
   │
   ▼
Level 4: Documentary Evidence (SEBI DRHP PDFs & verified SHA-256)
   │
   ▼
Level 5: Constitution Policy (AGENTS.md)
   │
   ▼
Level 6: Operational Summary (CURRENT_STATUS.md)
   │
   ▼
Level 7: Historical Records & Session Logs (docs/archive/*, SESSION_LOG.md)
```

---

## 2. Mandatory Conflict Halt Protocol

If any two applicable sources provide conflicting instructions, requirements, or data values:

1. **Do not guess:** The agent must not guess user intent or assume the more convenient interpretation.
2. **Do not silently reconcile:** The agent must never merge contradictory fields without explicit direction.
3. **Fail closed:** The agent must immediately halt with the exact status:
   ```
   SOURCE_OF_TRUTH_CONFLICT
   ```
4. **Detail the conflict:** The halt message must present the conflicting sources, line numbers, and contradictory values to the user or reviewer for formal resolution.
