# Pre-IPO local master integration

7 November 2026. Integrates the decision-depth branch with master, including Antigravity's completed OCR annexure, exchange-registry and prototype algorithm changes checkpointed as `1faedb9`.

## Preserved and resolved

- Kept master's five-panel terminal, context selector, company background, equity questions, detailed workpapers, crosswalk, IC actions and revised exports.
- Added the independent decision workbench and shared HTML renderer. The initial page conflict was resolved from master's complete terminal and the small additive integration reapplied.
- Kept Antigravity's OCR and prototype modules. No database, credentials, manuscript, unrelated untracked artifacts, push or deployment is included.
- Fixed registry import to support the application's actual dataclass dossiers rather than assuming Pydantic models.

## Integration safeguards

- Unsuccessful scanned intake displays `GAP-OCR-01` and intake diagnostics, then stops before ratios, underwriting or analytical deck export.
- Empty/malformed/non-finite annexure responses cannot report successful extraction. Extracted tables require source review and do not automatically become ratio inputs. SDK error diagnostics expose class/status, not credential-bearing exception URLs.
- The exchange module is a local example registry, not a network feed. Default examples cannot reconcile a listing date or receive a green exchange-confirmed badge. Only an explicitly reviewed record with an official HTTPS source URL is eligible for local reconciliation; even that does not claim a live connection. A connected NSE/BSE provider remains outstanding.
- Dossier-based algorithm prototypes are optional, labelled experimental, and disabled by default. They are distinct from the workbench's supported explicit-input contracts. Fixed synthetic return examples are not issuer observations.
- The prototype stress method distinguishes no failure in its finite grid from a found frontier and does not exempt a loss-making leveraged issuer. Invalid negative/non-finite waterfall inputs are rejected. Full ALG01–ALG14 production acceptance remains outside these prototype claims.

## Verification

- Pre-IPO and integration regression suites: **102 passed**.
- Authentication, Company Financing and board/deck compatibility suites: **161 passed**.
- Project operations fast suite: **6 passed**.
- Combined candidate: **four authenticated profiles × both themes, 8/8 passed**. Verified the five-panel terminal, no raw HTML code blocks, truthful unconnected-feed state, workbench dossier inspection, optional financing model, private saves/actions and JSON/PPTX downloads. Viewer edit/save denial remains intact.
- Local browser artifacts: `scratch/merged_pre_ipo_evidence/`; generated artifacts and validation databases are not committed.

## External OCR limitation

The configured credential and `gemini-2.0-flash` model metadata were accessible. Actual generation on a synthetic scanned annexure returned **HTTP 402**. Live OCR success is therefore **not verified**. The application fails closed with `GAP-OCR-01`; the provider/account access condition must be resolved before repeating a real extraction. No real issuer document was transmitted in this check.

This is a local code merge, not a production deployment or confirmation of a live exchange connection.
