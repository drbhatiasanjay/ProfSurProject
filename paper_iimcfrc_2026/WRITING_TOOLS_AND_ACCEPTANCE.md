# Writing tools and acceptance record
Checked 30 September 2026. This records observed availability, not completion of manuscript review.

## Skill sources located and read
All five requested skill files were found under C:/Users/hemas/.gemini/config/skills/:
- [avoid-ai-writing](C:/Users/hemas/.gemini/config/skills/avoid-ai-writing/SKILL.md): 21-category review and a second pass.
- [unslop](C:/Users/hemas/.gemini/config/skills/unslop/SKILL.md): deterministic CLI processing with diff review.
- [scientific-writing](C:/Users/hemas/.gemini/config/skills/scientific-writing/SKILL.md): empirical precision, field terminology, paragraph-based manuscript and source-backed statements.
- [citation-management](C:/Users/hemas/.gemini/config/skills/citation-management/SKILL.md): metadata, identifiers, versions and claim support.
- [deep-research](C:/Users/hemas/.gemini/config/skills/deep-research/SKILL.md): research workflow. Its Gemini service was not invoked.

The available ECC deep-research skill was also read and its search/read/verify structure used with the callable web tool. The deadline scope and the user's existing-format requirement take precedence over generic skill prescriptions for extensive searches, additional generated figures or a different scientific field's reporting format.

## Actual environment
- Callable research tool in this chat: web.run through the tools interface. No tools named search_web or read_url_content, and no Grammarly connector, were found in the active inventory. Equivalent search/open capability was used.
- Python 3.12 module discovery: linearmodels, statsmodels, sklearn, pandas, numpy, scipy, shap and docx found. This is discoverability, not a numerical-validation or full-import test.
- doubleml was not discoverable in that interpreter. Its availability in another environment was not assessed. It is unnecessary for the deadline manuscript.
- unslop executable was not found on PATH; its module was not discoverable in Python 3.12. Skill availability does not establish CLI availability. Actual unslop processing is pending.
- Citation-management's referenced scripts directory was not found in the checked skill location. Metadata verification can use primary publisher records; do not claim its bundled scripts ran.
- [audit_anti_slop.py](C:/Users/hemas/Downloads/ProfSurProject/paper_iimcfrc_2026/audit_anti_slop.py) exists and was inspected. It searches a banned-phrase list and returns a pass/fail code. It does not check all five humanisation rules, citation accuracy, statistical validity or originality. This review did not establish that a pre-commit hook invokes it.

## Required final-paper review sequence
Scientific review → citation review → avoid-ai-writing and second pass → deterministic unslop with reviewed diff → local phrase audit/manual style review → Grammarly → final scientific/layout review.

Protect technical meanings, numerical values, reference titles, equations and standard terminology. A plain-word replacement must not change financial leverage into a different construct or remove the technical adjective in robust standard errors.

Grammarly is mandatory per the user. Review every final prose section; resolve applicable errors and record retained technical exceptions. Record exact filename, revision/hash, date, reviewer, evidence of completion and any post-review edits. A high score or an AI-detection score is not a substitute for this review. No detector score is a scientific validity criterion.

## Current gate statuses
| Gate | Status |
|---|---|
| Submission scope and plan | Prepared |
| Full audit preserved | Confirmed: complete original text retained verbatim after the new scope header |
| Initial literature shortlist | Prepared; final bibliography not yet validated |
| New submission manuscript | Not drafted in this turn |
| scientific-writing / avoid-ai-writing final-paper passes | Pending final manuscript |
| unslop execution | Pending tool availability and final manuscript |
| Local phrase audit of short plan | PASS on 30 September 2026; this is not a manuscript-language pass |
| Grammarly final-paper review | Pending signed-in access or user-performed review |
| Scientific review after Grammarly | Pending |
| Submission PDF / portal receipt | Pending |

Do not change any pending manuscript gate to PASS because the plan itself passes a phrase audit.
