"""
SEBI ICDR Statutory Section & Chapter Taxonomy
Maps the authentic structure of an Indian Mainboard Red Herring Prospectus (DRHP/RHP)
under SEBI (Issue of Capital and Disclosure Requirements) Regulations, 2018 (Schedule VI).
"""

from typing import Dict, List, Any
from dataclasses import dataclass, field

@dataclass
class StatutorySubChapter:
    chapter_id: str
    title: str
    sebi_clause: str
    description: str

@dataclass
class StatutorySection:
    section_id: str
    section_number: int
    title: str
    sebi_schedule_reference: str
    description: str
    sub_chapters: List[StatutorySubChapter] = field(default_factory=list)

SEBI_ICDR_SECTIONS: Dict[str, StatutorySection] = {
    "SEC_01_GENERAL": StatutorySection(
        section_id="SEC_01_GENERAL",
        section_number=1,
        title="General Information & Overview",
        sebi_schedule_reference="SEBI ICDR Schedule VI, Part A, Item I & II",
        description="Definitions, statutory abbreviations, issue syndicate (BRLMs, Auditors, Legal Counsels), and summary financial data.",
        sub_chapters=[
            StatutorySubChapter("CH_01_DEFINITIONS", "Definitions & Abbreviations", "Part A, Item I", "Conventional terms and defined industry words."),
            StatutorySubChapter("CH_02_SUMMARY_OFFER", "Summary of the Offer", "Part A, Item II", "Offer size, selling shareholders, and price band."),
            StatutorySubChapter("CH_03_GENERAL_INFO", "General Information", "Part A, Item III", "BRLMs, syndicate members, registrars, and statutory auditors.")
        ]
    ),
    "SEC_02_RISK_FACTORS": StatutorySection(
        section_id="SEC_02_RISK_FACTORS",
        section_number=2,
        title="Risk Factors & Forensic Vulnerabilities",
        sebi_schedule_reference="SEBI ICDR Schedule VI, Part A, Item IV",
        description="Statutory disclosure of internal risks, legal vulnerabilities, supplier dependencies, customer concentration, and macro headwinds.",
        sub_chapters=[
            StatutorySubChapter("CH_04_INTERNAL_RISKS", "Internal Risk Factors", "Item IV(A)", "Litigation exposure, key contracts, promoter dependence, and supply bottlenecks."),
            StatutorySubChapter("CH_05_EXTERNAL_RISKS", "External & Macro Risks", "Item IV(B)", "Direct/indirect tax disputes, interest rate tightening, FX fluctuations, and regulatory audits."),
            StatutorySubChapter("CH_06_OFFER_RISKS", "Risks Relating to Equity Shares", "Item IV(C)", "Absence of prior public trading market, price volatility, and secondary dilution.")
        ]
    ),
    "SEC_03_CAPITAL_OBJECTS": StatutorySection(
        section_id="SEC_03_CAPITAL_OBJECTS",
        section_number=3,
        title="Capital Structure & Objects of the Offer",
        sebi_schedule_reference="SEBI ICDR Schedule VI, Part A, Item V & VI",
        description="Authorized share capital, promoter shareholding pre/post-issue, lock-in schedules, use of proceeds, GCP 25% statutory ceiling, and capex milestones.",
        sub_chapters=[
            StatutorySubChapter("CH_07_CAPITAL_STRUCTURE", "Capital Structure & Dilution", "Item V", "Equity share classes, promoter group shareholding, and lock-in covenants."),
            StatutorySubChapter("CH_08_OBJECTS_OFFER", "Objects of the Offer", "Item VI(A)", "Apportionment of net proceeds: debt repayment, capex project funding, and GCP ceiling."),
            StatutorySubChapter("CH_09_FUNDING_SCHEDULE", "Milestones & Phasing", "Item VI(B)", "Year-wise deployment timeline and means of finance.")
        ]
    ),
    "SEC_04_ISSUER_GOVERNANCE": StatutorySection(
        section_id="SEC_04_ISSUER_GOVERNANCE",
        section_number=4,
        title="About the Issuer Company & Corporate Governance",
        sebi_schedule_reference="SEBI ICDR Schedule VI, Part A, Item VII & VIII",
        description="Corporate history, manufacturing footprint, bottling franchise exclusivity, Board of Directors, KMP compensation, cross-directorships, and promoter control.",
        sub_chapters=[
            StatutorySubChapter("CH_10_BUSINESS_OVERVIEW", "Business Overview & Plants", "Item VII(A)", "Manufacturing units, bottling capacity, supply chain, and territory exclusivity."),
            StatutorySubChapter("CH_11_BOARD_DIRECTORS", "Board of Directors & KMP", "Item VIII(A)", "Board composition, independent directors, executive compensation, and external directorships."),
            StatutorySubChapter("CH_12_PROMOTER_GROUP", "Promoters & Holding Entities", "Item VIII(B)", "Promoter background, intermediate holding companies (Singapore/UK/US), and encumbrances.")
        ]
    ),
    "SEC_05_FINANCIAL_INFO": StatutorySection(
        section_id="SEC_05_FINANCIAL_INFO",
        section_number=5,
        title="Financial Information & Indebtedness",
        sebi_schedule_reference="SEBI ICDR Schedule VI, Part A, Item IX",
        description="Restated financial statements, Ind AS 116 capitalized operating lease debt, borrowing terms, interest coverage, and MD&A liquidity analysis.",
        sub_chapters=[
            StatutorySubChapter("CH_13_RESTATED_FINANCIALS", "Restated Financial Statements", "Item IX(A)", "Audited Balance Sheet, Statement of Profit & Loss, and Cash Flows under Ind AS."),
            StatutorySubChapter("CH_14_FINANCIAL_INDEBTEDNESS", "Borrowing Schedules & Leases", "Item IX(B)", "Secured/unsecured credit facilities, maturity ladders, and Ind AS 116 lease obligations."),
            StatutorySubChapter("CH_15_MDA_ANALYSIS", "Management Discussion (MD&A)", "Item IX(C)", "Operating margins, seasonality, working capital cycles, and capital expenditure.")
        ]
    ),
    "SEC_06_LEGAL_LITIGATION": StatutorySection(
        section_id="SEC_06_LEGAL_LITIGATION",
        section_number=6,
        title="Outstanding Litigation & Material Claims",
        sebi_schedule_reference="SEBI ICDR Schedule VI, Part A, Item X",
        description="Disaggregated litigation registers: Direct Tax appeals, Indirect Tax (CESTAT) claims, S.138 Cheque Bounce distributor clusters, and CPCB environmental notices.",
        sub_chapters=[
            StatutorySubChapter("CH_16_TAX_LITIGATION", "Direct & Indirect Tax Disputes", "Item X(A)", "Income tax assessment challenges, excise/customs claims, and GST demand notices."),
            StatutorySubChapter("CH_17_COMMERCIAL_CRIMINAL", "Civil & Criminal Proceedings", "Item X(B)", "Section 138 Negotiable Instruments Act cheque dishonour cases and contract arbitration."),
            StatutorySubChapter("CH_18_REGULATORY_ENVIRONMENTAL", "Statutory & Environmental Actions", "Item X(C)", "CPCB notices, groundwater extraction restrictions, and factory inspection show-cause.")
        ]
    ),
    "SEC_07_OFFERING_PRICING": StatutorySection(
        section_id="SEC_07_OFFERING_PRICING",
        section_number=7,
        title="Offering Terms & Basis for Issue Price",
        sebi_schedule_reference="SEBI ICDR Schedule VI, Part A, Item XI",
        description="Allocation quotas (QIB, NII, RII), Anchor investor bidding rules, basis for issue price, peer comparison P/E & EV/EBITDA, and RoNW benchmarks.",
        sub_chapters=[
            StatutorySubChapter("CH_19_OFFER_STRUCTURE", "Issue Structure & Quotas", "Item XI(A)", "Minimum application size, bidding mechanics, and investor reservation quotas."),
            StatutorySubChapter("CH_20_PRICE_BASIS", "Basis for Issue Price", "Item XI(B)", "Qualitative factors, diluted EPS, RoNW, NAV, and listed peer multiple multiples.")
        ]
    ),
    "SEC_08_MATERIAL_CONTRACTS": StatutorySection(
        section_id="SEC_08_MATERIAL_CONTRACTS",
        section_number=8,
        title="Material Contracts & Related-Party Ledger",
        sebi_schedule_reference="SEBI ICDR Schedule VI, Part A, Item XII",
        description="Key corporate agreements: Concentrates supply covenants, trademark sublicense agreements, marketing support arrangements, and inspection archives.",
        sub_chapters=[
            StatutorySubChapter("CH_21_RPT_AGREEMENTS", "Related Party Contracts", "Item XII(A)", "Transfer pricing terms, concentrate procurement formulas, and brand royalty charges."),
            StatutorySubChapter("CH_22_COMMERCIAL_ALLIANCES", "Commercial Franchise Agreements", "Item XII(B)", "Bottling franchise agreements, territory boundaries, and termination rights."),
            StatutorySubChapter("CH_23_INSPECTION_DOCUMENTS", "Documents for Inspection", "Item XII(C)", "Material contracts, charters, and expert opinion letters available to investors.")
        ]
    )
}

def get_section_catalog() -> List[Dict[str, Any]]:
    """Returns the ordered statutory sections catalog with sub-chapters."""
    result = []
    for sec_id, sec in sorted(SEBI_ICDR_SECTIONS.items(), key=lambda x: x[1].section_number):
        result.append({
            "sectionId": sec.section_id,
            "sectionNumber": sec.section_number,
            "title": sec.title,
            "sebiSchedule": sec.sebi_schedule_reference,
            "description": sec.description,
            "subChapters": [
                {
                    "chapterId": ch.chapter_id,
                    "title": ch.title,
                    "sebiClause": ch.sebi_clause,
                    "description": ch.description
                }
                for ch in sec.sub_chapters
            ]
        })
    return result
