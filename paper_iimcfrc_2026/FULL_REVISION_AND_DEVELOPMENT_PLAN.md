# Full revision and development plan — preserved audit
Updated 30 September 2026 after the user's submission-first direction.

This document preserves the complete earlier audit and longer-term development/research agenda. It is not a prerequisite for today's submission. SUBMISSION_FIRST_PLAN.md governs today's work: omit incomplete or unverified capabilities; do not repair the application or run new empirical studies before drafting. Treat Studio V2 as the upgraded Stata Studio, not a second contribution. Final Grammarly review is mandatory.

## Deferred priorities
1. Repair dataset-scope enforcement, unknown-citation fallback, estimator labels and unsupported-command inconsistencies; verify affected routes.
2. Replace or validate heuristic CFO metrics, improve entity resolution and remove unsupported fixed numerical prompts.
3. Freeze data vintages, reconcile September values and produce controlled matched-sample/full-sample comparisons.
4. Complete estimator-specific numerical and methodological validation; implement true System GMM only if scientifically warranted.
5. Verify exact run-to-export replication, validation-state integrity, researcher workflows and deployed branch parity.
6. Evaluate AI numerical/semantic accuracy, citations and abstention using a prespecified benchmark; assess provider paths separately.
7. Evaluate optional parallel simulations, newer causal methods and user-study outcomes separately from the current paper.

The original assessment follows unchanged as historical evidence. Any advice in it to include incompletely verified material with a caveat is superseded by the user's direction to omit it from today's paper. Supporting files: LITERATURE_UPDATE_PLAN.md and WRITING_TOOLS_AND_ACCEPTANCE.md.

---
# LifeStageDebtAI — revision assessment
30 September 2026 | ProfSurProject | Assessment and writing plan; not a revised manuscript

## Recommendation
Retain the life-stage capital-structure research question and the existing eight-section structure. Centre the revision on **updated panel evidence and an executable, auditable research workflow**.

The August paper already includes FY2025 data, machine learning/SHAP, forecasting, scenarios, transitions, semantic organisation, browser access and a US pilot. These are existing capabilities, not new contributions. The significant additions are on-demand AI execution, Stata-style research workbenches, session-specific model identity, inspectable citations, research-evidence controls and revised replication data.

Suggested subtitle: **From Fixed-Reference Replication to Interactive, Evidence-Linked Capital-Structure Research**. Keep the main title provisionally, but clarify “Open”: no root LICENSE file was found, and CMIE data remain proprietary. Public application access, open-source licensing and open data are separate matters.

## Conference requirements
The existing manuscript names IFC 2026 at IIM Bangalore, 21–23 December. The supplied call is for **IIM Calcutta Finance Research Conference, 12–14 December 2026**. Submission closes **30 September 2026**, today; no cutoff time is stated. It invites original, unpublished full papers. Corporate finance and FinTech are relevant areas. Participation is in person.
[Official call](https://www.iimcal.ac.in/events/Call-for-Papers-IIM-Calcutta-Finance-Research-Conference-IIMCFRC-2026)

The form accepts **PDF, DOC or DOCX under 20 MB**. Neither inspected page specifies a page/word limit, font, citation style or anonymisation rule. Its 100-word “Any Request” field is not an abstract limit. Preserve the existing scholarly layout unless additional instructions are supplied.
[Submission form](https://application.iimcal.ac.in/conference-paper-submission-iimcfrc-2026)

Correct the title-page conference details. Do not transfer “Track: Financial Analytics” as an official Calcutta track without checking the portal choices. Original/unpublished status needs author confirmation; local files cannot establish it.

## Audit scope
- Baseline: [August Word manuscript](C:/Users/hemas/Downloads/ProfSurProject/docs/Bhatia_Kumar_LifeStageDebtAI_IFC2026.docx), approximately 5,584 words including tables. Title checked directly in DOCX; existing extracted text reviewed in full.
- Local branch: `agy/wave6-8-harness-repair-2026-09-11`; HEAD `f7edee52ea6992c3c847de9c971b3e4a861ac310`.
- Cached origin/master: `ae8d7e8`, 18 September. No remote fetch. Local code differs materially and is not evidence of the currently deployed build.
- The database has pre-existing uncommitted changes. Counts below describe the local database inspected, not a frozen publication dataset.
- Reviewed Git history, current source, manuscript, implementation reports, read-only SQL aggregates, focused tests and a synthetic scope probe.
- The 29 September code map was used only for navigation. Full regeneration lacked an LLM key; a code-only refresh did not finish within the bounded attempt. Findings rely on direct current-source inspection.
- No application fixes, cloud LLM requests, deployment, paper rewriting or submission were performed. Browser behaviour/cloud parity were not re-certified.

## Prioritised enhancement inventory

| Priority | Enhancement | Completion/evidence boundary | Paper action |
|---|---|---|---|
| 1 | September bifurcated-stage panel | Registered in UI and database; 9,031 observations, 400 firms, 2001–2025. Source reconciliation remains needed. | Expand §3.3/Table 2; add controlled comparison in §4. |
| 1 | AI requests data and estimates models on demand | Gemini registers SQL, descriptive, live econometric, Stata, chart, ontology and stress tools. Scope/correctness are not uniformly verified. | Rewrite §§2.4, 3.2, 3.6 and architecture figure. |
| 1 | Stata Studio and Studio V2 | Both registered. Typed variables, grouped commands, run history, tables, plots, hypothesis commentary and export controls exist. A subset of Stata-like syntax, not Stata itself. | Add workbench description and researcher walkthrough. |
| 1 | Session-specific model/result identity | AnalysisSession/ModelResultContext track sample fingerprints, parameters, covariance, stored estimates and active model. Calendar-lag/state repairs exist. | Strengthen reproducibility and model/sample lineage sections. |
| 2 | Deterministic descriptive AnalysisRun | Statistics and metadata implemented; confirmed vintage/company filtering defect in database gateway. | Describe contract and limitation; test isolation before claiming correctness. |
| 2 | Validation ledger and research artifacts | Separate numerical, assumption, methodological, reproducibility and reviewer gates; provenance-bound charts/narratives. Engineering controls, not universal scientific validation. | Add evidence/status table in §§3.7/4. |
| 2 | Literature Vault/Citation Inspector | DOI links, theory/context and BibTeX/APA/Stata formatting. Unknown references receive placeholder metadata. | Describe curated citation support; do not claim all citations verified. |
| 2 | Charts and reporting | Provider-neutral chart rendering, chart switching, Word/LaTeX table exports and board-deck improvements. Do-file is a preset template. | Update Table 5 and explain exact export scope. |
| 2 | Persistent conversational workspace | Session search/rename, saved messages, feedback/actions, follow-ups and streaming fallback. | Brief addition in §3.6; productivity benefits need a study. |
| 2 | Company-specific CFO interface | Infosys, Tata Steel, Bharti Airtel, IndiGo and Sun Pharma selectors, staged prompts and named comparisons. Some prompts embed fixed numbers. | One illustrative case in §5.2; verify every baseline. |
| 3 | CFO stress outputs | Implemented heuristics for ICR, headroom, ratings and sensitivities; default-company fallback exists. | Illustrative assumptions only, or omit numerical claims. |
| 3 | Reproduce/Challenge controls | Currently in Settings. Actions update a read-only context and retain NOT_VALIDATED. They do not rerun an estimator. | Qualified governance paragraph, not a claim of full replication. |
| 3 | Parallel simulation matrix | Isolated branches, seeds, fingerprints and disagreement reporting. Module is untracked; no page integration found. | Experimental appendix/future work, not released capability. |
| Supplement | Themes, layouts, demo videos | Substantial recent work is usability/demonstration production. | Supplementary material; not financial findings. |

## Data findings: a substantive new revision opportunity
These are raw counts, not regression sample sizes.

| Dataset | Period | Firms | Firm-years | Missing leverage |
|---|---|---:|---:|---:|
| thesis | 2001–2024 | 401 | 8,677 | 0 |
| cmie_2025 | 2025 | 400 | 400 | 4 |
| latest: thesis + cmie_2025 | 2001–2025 | 402 | 9,077 | 4 |
| run3: April26 replication panel | 2001–2025 | 400 | 9,031 | 869 |
| bf2001_25_sept26 | 2001–2025 | 400 | 9,031 | 1 |
| us_av_2024 | 2006–2026 | 24 | 480 | 11 |

Individual vintages have unique company-year keys in this inspection. The physical financials table contains 27,619 rows across overlapping vintages and 426 distinct company codes. **Do not claim a 27,619-observation independent study sample.**

April and September match on all 9,031 company-year keys. September has **868 non-missing leverage values where April has NULL**, plus **one changed non-NULL leverage value**. Stage, profitability and tangibility match across every paired row. This is a measured coverage change, not validation of recovered values or evidence of a changed financial relationship. Check source units, missingness handling and the revised non-NULL observation.

The September source is `nf400_BifurcateStageWise25yrs.dta`; April is `nf400yrs2001_25.dta`. September is now the default panel in app.py. Keep the thesis reference frozen.

The original paper mixes discussion of 8,677 raw reference rows, 6,920 estimation observations, 9,077 combined raw records and separate common-variable samples. Replace ambiguous wording with a sample-flow table. The 402-firm combined panel and 400-firm replication panels are not interchangeable.

## Claims requiring correction before reuse

### 1. System GMM
The old paper and Table 5 describe System GMM. Current `run_legacy_proxy_gmm` uses linearmodels.iv.IVGMM with fixed lag instruments; the advanced page explicitly labels it an unverified proxy. Separate methods in the reference thesis from methods actually validated in this platform. Do not call this Blundell–Bond System GMM; qualify/remove the keyword.
[Source](C:/Users/hemas/Downloads/ProfSurProject/models/econometric.py:818) · [Inventory](C:/Users/hemas/Downloads/ProfSurProject/docs/implementation-reports/SYSTEM_GMM_CAPABILITY_INVENTORY_2026-09-11.md)

### 2. AI scope/grounding
The descriptive gateway reads all financials, applies a year filter and records requested panel/filter metadata without enforcing vintage/company selection. A synthetic two-row probe requested thesis/company 1: expected N=1, mean=10; actual N=2, mean=50 while reporting thesis.

The SQL gateway has explicit filtering, but that does not establish the descriptive tool's correctness. The CFO tool separately hardcodes thesis. Test every execution route before claiming all AI answers respect active filters or have complete lineage.
[Gateway](C:/Users/hemas/Downloads/ProfSurProject/models/agent_tools.py:237) · [Descriptive contract](C:/Users/hemas/Downloads/ProfSurProject/models/descriptive_analyst.py)

Also replace the old claim that AI only explains previously computed results. It can now request database queries and new model execution; the language model's role and the deterministic computation boundary must be explained accurately.

### 3. Citation integrity
Unknown references receive a constructed title, generic author/journal and fixed DOI; the inspector uses an “Open Verified DOI” label. Do not use that fallback to build the bibliography or claim universal citation authentication. Known catalogue entries still need claim-to-source review. Unknown entries should be unresolved.
[Metadata](C:/Users/hemas/Downloads/ProfSurProject/models/citation_vault_metadata.py:222) · [Inspector](C:/Users/hemas/Downloads/ProfSurProject/components/citation_inspector.py)

### 4. CFO figures
The stress tool fixes baseline ICR at 3.55, computes headroom from preset equations, applies rating thresholds and constant sensitivities. Unmatched entities can fall back to Tata Motors and default financials. Some scenario prompts include fixed leverage/ROA figures.
These are illustrative assumptions, not measured firm-specific covenant capacity, actual credit ratings, causal counterfactuals or optimal debt ratios.
[Stress tool](C:/Users/hemas/Downloads/ProfSurProject/models/agent_tools.py:1179)

### 5. Method labels and exported replication
The live tool can say “Two-Way Fixed Effects” while the underlying model specifies entity effects only. Its selection explanation says p<0.0001 on a branch that only tests p<0.05. Reconcile model/fallback labels and quote actual diagnostics.

V2's do-file is a fixed OLS/FE/RE template, not a replay of arbitrary current commands/transformations/covariance choices. External Stata execution and numerical checks are required before claiming parity.
[Live tool](C:/Users/hemas/Downloads/ProfSurProject/models/agent_tools.py:941) · [FE](C:/Users/hemas/Downloads/ProfSurProject/models/econometric.py:142) · [Export](C:/Users/hemas/Downloads/ProfSurProject/pages/25_stata_studio_v2.py:815)

### 6. Capability/release inconsistencies
Status notes report some merged capabilities, but the current canonical dispatcher lacks routes for ivregress, hdfe, gmm, didregress, test, predict, predict_ml, scenario and winsor2. Related functions on other surfaces do not make these Studio commands available. State the interface and implementation separately.

A fingerprint establishes identity, not correctness. A validation record is an engineering mechanism, not independent scientific evidence. Historical “109/109” checks and demo scores are not proof that this current build is fully validated.
[Dispatcher](C:/Users/hemas/Downloads/ProfSurProject/models/stata_engine.py:385)

## Section-by-section writing plan

| Section | Proposed change |
|---|---|
| Title/abstract/keywords | Correct conference. Add September panel and executable research workflow. Avoid unmeasured performance claims. Clarify Open and GMM. |
| 1 Introduction | Keep financing/life-stage motivation. State controlled data revision, interactive execution and traceable interpretation as contributions. Delete duplicated reference-validation paragraph (P14/P15). |
| 2 Background | Retain financial theory. Distinguish retrieval, tool execution, numerical accuracy, citation support and interpretive accuracy. Avoid an unverified “no competing platform” claim. |
| 3.1 Architecture | Redraw: vintage selection → scoped data gateway → deterministic tools → result context → tables/charts/narratives → exports. Mark heuristic/experimental paths. |
| 3.2–3.3 Data/provenance | Add April/September panels, source files, missingness, overlaps and sample identities. Separate raw/usable/estimation N. |
| 3.4 Analytics | Add Stata-style workbench, supported method families, state isolation, calendar lags and error boundaries. Correct GMM. |
| 3.5 Transitions/semantics | Retain established material. Knowledge-graph navigation is hidden/WIP; do not describe a new completed graph UI. |
| 3.6 AI | Rewrite retrieval-only description. Explain querying, model execution, charts, sessions, citations and provider differences. Disclose scope/citation gaps. |
| 3.7 Reproducibility/access | Explain model/sample identity, artifacts and validation gates. Describe Settings controls accurately. Separate access/licensing/proprietary data. |
| 4 Validation/results | Keep reference benchmark as historical evidence pending rerun. Add vintage comparison and separate numerical/AI evaluation. Do not transfer old XGBoost R² to new data. |
| 5 Applications | One researcher journey and one explicitly assumed CFO scenario. Remaining company cases/video in supplement. |
| 6 Contributions | Connect engineering additions to financial research needs. Distinguish implemented mechanisms from measured benefits. |
| 7 Limitations | Replace “no AI tests” with “engineering tests exist; systematic numerical/semantic accuracy remains incomplete.” Include identified scope, citation, proxy, heuristic and export limits. |
| 8 Conclusion | Summarise demonstrated evidence. No causal, optimal-leverage, rating or productivity claims from feature availability alone. |
| Bibliography | Retain verified sources, independently check additions and never use fallback metadata as a reference. |

## Tables, figures and evidence needed
1. **Revised Table 2:** data-vintage/sample-flow inventory, including variable missingness and exact analysis sample.
2. **Rechecked Table 3:** reference FE coefficients, standard errors/diagnostics where relevant, tolerance, sample and exact code/data snapshot.
3. **New vintage-comparison table:** common-variable estimates on matched samples, then full September usable sample separately. Distinguish changed values from added usable observations.
4. **Capability/evidence table:** availability, numerical verification, methodological validation, external replication and limitations. Command list in appendix.
5. **AI evaluation table:** requested/actual scope, operation, reference result, returned value, citation support and failure/abstention behaviour.
6. **Updated architecture figure and one workflow figure:** sourced from the chosen release, showing a real bounded research task.

### Proposed evaluation — not completed results
- Compare direct Python, Stata-style and AI-requested execution on the same frozen sample. Measure numerical agreement, correct sample selection and error handling.
- Re-estimate old/September panels with consistent units, omitted stage, transformations, missing-value rules and covariance. Separate matched/full samples.
- Rerun relevant firm-grouped/temporal predictive evaluation before updating ML claims; old R²=0.64 cannot be assumed for the September panel. SHAP remains predictive attribution.
- Prespecify prompts covering descriptive queries, estimation, comparisons, scope switches, unsupported commands, unknown companies, unknown citations and scenarios. Repeat across actual provider paths and disclose failures.
- User productivity/expert usefulness studies remain proposed unless performed with a documented protocol.

## Checks actually performed
- DOCX title/structure check, complete baseline extracted-text review, Git history and current-source inspection.
- Read-only dataset/vintage counts, unique company-year checks, missingness and April/September matching.
- Five focused test files: model_context, research_artifacts, research_artifact_renderer, validation_ledger and wave6_8_defect_regressions. **26 passed initially; one relative-path test failed because execution started in Downloads. Rerunning that one test from the project directory passed. All 27 selected tests passed across those invocations.** Three warnings in the first run. This is not full-suite or live-browser certification.
- In-memory synthetic scope probe confirmed the descriptive-tool defect: expected N=1/mean 10, actual N=2/mean 50.
- Inspected citation fallback, CFO formulas, estimator labels, command routes, Settings controls and do-file template.

No new econometric coefficients, forecast metrics, provider accuracy rates or productivity findings were produced in this assessment.

## Recommended order
1. Freeze the publication branch/data snapshot and preserve the August manuscript.
2. Correct conference identity and inaccurate existing method claims.
3. Fix scope/citation/model-label issues before using AI outputs as evidence; validate or explicitly exclude CFO numeric claims.
4. Reproduce reference FE and prepare the September comparison/sample-flow table.
5. Write data/architecture/workbench sections, then results and abstract around actual evidence.
6. Check bibliography, limitations and submission PDF.

For today's deadline, a defensible shorter revision can add verified implementation/data-inventory findings, preserve dated historical results and disclose unfinished evaluation. Stronger empirical claims require the comparative analyses; writing cannot substitute for them.

## Additional implementation references
[Model context](C:/Users/hemas/Downloads/ProfSurProject/models/model_context.py) ·
[Validation ledger](C:/Users/hemas/Downloads/ProfSurProject/models/validation_ledger.py) ·
[Research artifacts](C:/Users/hemas/Downloads/ProfSurProject/models/research_artifacts.py) ·
[Settings controls](C:/Users/hemas/Downloads/ProfSurProject/pages/6_settings.py:19) ·
[September loader](C:/Users/hemas/Downloads/ProfSurProject/scripts/load_bifurcate_dta.py) ·
[Phase 16–17 boundary](C:/Users/hemas/Downloads/ProfSurProject/docs/implementation-reports/PHASE_16_17_GATE_A_STATUS.md)

Historical reports document earlier checkpoints. Where they conflict with current source, this assessment uses the current implementation and the scoped checks above.
