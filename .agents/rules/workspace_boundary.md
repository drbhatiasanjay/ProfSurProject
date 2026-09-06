# Exclusive Workspace Boundary & Cross-Project Blunder Prevention

## Mandatory Operating Rule
This agent session is strictly and exclusively confined to **`ProfSurProject`** located at:
`c:\Users\hemas\Downloads\ProfSurProject`

## Accidental Input Interception Protocol
If the user accidentally types, pastes, or issues a command or prompt referencing another workspace or external project (including, but not limited to):
- `FinancialDecisionIntelligence` / `FDI`
- PR reviews on external repositories (e.g. PR #1 FDI)
- Symphony / KAIF / external harness tasks
- Any path or file outside `c:\Users\hemas\Downloads\ProfSurProject`

### Required Agent Action:
1. **DO NOT START OR EXECUTE**: Do not run commands, write files, or modify external repositories.
2. **IMMEDIATELY PAUSE & ALERT**: Intercept the prompt immediately and notify the user:
   > ⚠️ **Workspace Mismatch Detected**: This session is strictly confined to **ProfSurProject**. The submitted prompt appears to reference an external project (`FinancialDecisionIntelligence`). Execution has been stopped to prevent cross-project blunders.
3. **AWAIT USER CONFIRMATION**: Do not proceed until the user explicitly clarifies or redirects the instruction to `ProfSurProject`.
