# Literature update plan and candidate register
30 September 2026 | Focused submission-day update, not a completed systematic literature review

## Purpose and limits
Update only the literature needed by the retained paper. Search across financial life-cycle research, financial numerical reasoning, and reproducible/tool-assisted research workflows. Verify primary records, read the relevant passages, and distinguish bibliographic validity from evidentiary support.

The initial searches below produced a shortlist. Full bibliography validation and sentence-level citation placement remain drafting tasks. Do not describe this work as a systematic review or claim the absence of competing platforms.

## Existing references: retain selectively
- Dickinson (2011), Anthony and Ramesh (1992): distinguish cash-flow-based classification from alternative life-cycle measures.
- Myers and Majluf (1984), Frank and Goyal (2009), La Rocca et al. (2011), Faff et al. (2016), Castro et al. (2015/2016): retain where they support financing/life-stage arguments.
- Bhaduri (2002), Chakraborty (2010), Kumar (2025): retain Indian context and the actual reference study; verify thesis details and table attribution.
- Hausman (1978): retain only with the relevant test description.
- Mullainathan and Spiess (2017), Athey and Imbens (2019), Lundberg and Lee (2017): retain if the associated predictive analysis remains supported.
- Lewis et al. (2020), Ji et al. (2023), Stodden et al. (2016): retain where retrieval, generation risks and computational reproducibility remain discussed.
- Arellano and Bond (1991), Blundell and Bond (1998): do not use these to imply that the platform implements validated System GMM. Retain only for an explicit, relevant reference-study discussion; otherwise remove.
- BloombergGPT/FinGPT references: retain only if their domain-specific modelling discussion remains in the shortened background, with accurate publication status.

This is a retention list from the existing manuscript, not a claim that all entries were freshly verified today.

## Candidate additions

| Candidate | Proposed use | Primary evidence/status | Decision for deadline draft |
|---|---|---|---|
| Chen et al. (2021), *FinQA: A Dataset of Numerical Reasoning over Financial Data*, EMNLP, 3697–3711; DOI 10.18653/v1/2021.emnlp-main.300 | Explain why fluent financial answers require explicit numerical correctness checks | ACL abstract and bibliographic record opened; official BibTeX retrieved. | Strong candidate for one short background/limitation sentence. Do not imply LifeStageDebtAI was tested on FinQA. |
| La Rocca, Fasano, Staglianò, La Rocca and Deloof (2025), *The financial life cycle of European SMEs before, during and after crisis periods. What is the role of a country's financial system?*, International Review of Financial Analysis 104(A), 104342; DOI 10.1016/j.irfa.2025.104342 | Add recent finance context and explain limits of generalising across firm populations/institutions | Publisher-indexed abstract and metadata retrieved. Direct follow-up access failed; full-text claim review remains pending. | Conditional candidate. Use only a narrow statement supported by the accessible abstract after final metadata check. Firm age/European SMEs are not Dickinson stages/Indian listed firms. |
| Yao et al. (2023), *ReAct: Synergizing Reasoning and Acting in Language Models*, ICLR 2023; arXiv 2210.03629 | Distinguish language-model explanation from interaction with external tools | Author arXiv record opened; OpenReview encountered a browser challenge. | Optional, only if a supported tool-execution description remains. Do not claim the application implements or validates ReAct. |
| Peng (2011), *Reproducible Research in Computational Science*, DOI 10.1126/science.1213847 | Additional reproducibility context | Discovery records found; publisher/PMC full access was blocked in this pass. | Defer for this deadline unless primary verification is completed; existing Stodden citation may be sufficient. |

Primary links:
- [FinQA record](https://aclanthology.org/2021.emnlp-main.300/) and [official BibTeX](https://aclanthology.org/2021.emnlp-main.300.bib).
- [La Rocca et al. publisher record](https://www.sciencedirect.com/science/article/pii/S1057521925004296).
- [ReAct author record](https://arxiv.org/abs/2210.03629).

## Explicit exclusion identified
**Kim, Muhn and Nikolaev, Financial Statement Analysis with Large Language Models:** exclude as supporting evidence. The author's University of Chicago page states that the working paper was temporarily withdrawn while inconsistencies in data and analyses were reviewed. An accessible old PDF, SSRN record or arXiv abstract does not override that notice.
[Author's current notice](https://faculty.chicagobooth.edu/valeri-nikolaev/ongoing-research-projects)

Do not add Chernozhukov et al. merely because a local plan proposed DoubleML: no new DML study belongs in this submission. Do not invent or import “Kumar & Dawar / Gupta (2025)” from an instruction file without identifying an actual relevant publication. Illustrative figures and sample sizes in PAPER_ENVIRONMENT.md are not evidence.

## Search record
Queries used in this planning pass:
1. site.aclanthology.org FinQA dataset numerical reasoning financial data 2021
2. site.science.org Peng 2011 Reproducible Research Computational Science 1213847
3. site.openreview.net ReAct Synergizing Reasoning Acting Language Models 2023
4. site.ssrn.com Financial Statement Analysis with Large Language Models Kim Muhn Nikolaev
5. site.sciencedirect.com life cycle capital structure 2024 2025 firms
6. Roger Peng Reproducible Research Computational Science 2011 site.pmc.ncbi.nlm.nih.gov
7. site.publications.aaahq.org Dickinson 2011 Cash Flow Patterns Proxy Firm Life Cycle 1969 1994

Follow-up opens inspected original records, official BibTeX and the author withdrawal notice. Secondary search hits were not adopted as evidence for technical claims.

## Citation acceptance record
For each final entry record:
citation_key | author/year/version | title/venue | DOI/stable ID | primary_URL | claim_supported | section | relevant_page_or_passage | publication/withdrawal_status | checked_date | include/exclude

A resolving DOI is necessary when one exists, but does not establish that the source supports the sentence. Prefer an accurately labelled preprint without a DOI to a fabricated journal citation. Generate APA-style author–date text and BibTeX from the same verified register; preserve the paper's existing citation convention consistently.

## Change budget
Normally add two or three well-matched sources after verification, remove citations for omitted methods, and correct existing metadata. Do not expand the literature section solely to make the bibliography look more recent.
