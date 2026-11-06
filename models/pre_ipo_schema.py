"""
Pre-IPO DRHP Intelligence Data Schemas & Provenance Contracts.
Defines structured dataclasses for SEBI ICDR 2018 Restated Financials,
Funded vs Economic Indebtedness, Non-Financial Governance, and Auditable Ingestion.
"""
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any


@dataclass
class ProvenanceRef:
    section: str
    page: int
    table_or_note: str
    anchor_text: str


@dataclass
class FinancialYearMetric:
    fiscal_year: str
    revenue_ops_cr: float
    ebitda_cr: float
    pat_cr: float
    cfo_cr: float
    cfi_cr: float
    cff_cr: float
    capex_cr: float
    fcf_cr: float
    net_worth_cr: float
    provenance: Optional[ProvenanceRef] = None


@dataclass
class IndebtednessSchedule:
    secured_term_loans_cr: float
    working_capital_loans_cr: float
    ncd_bonds_cr: float
    unsecured_loans_cr: float
    lease_liabilities_ind_as_116_cr: float
    cash_and_equivalents_cr: float
    weighted_avg_interest_rate_pct: Optional[float] = None
    floating_benchmark_spread: Optional[str] = None
    sanctioned_limits_cr: Optional[float] = None
    provenance: Optional[ProvenanceRef] = None

    @property
    def funded_bank_debt_cr(self) -> float:
        return (
            self.secured_term_loans_cr
            + self.working_capital_loans_cr
            + self.ncd_bonds_cr
            + self.unsecured_loans_cr
        )

    @property
    def total_economic_indebtedness_cr(self) -> float:
        return self.funded_bank_debt_cr + self.lease_liabilities_ind_as_116_cr

    @property
    def net_funded_debt_cr(self) -> float:
        return max(0.0, self.funded_bank_debt_cr - self.cash_and_equivalents_cr)

    @property
    def net_economic_debt_cr(self) -> float:
        return max(0.0, self.total_economic_indebtedness_cr - self.cash_and_equivalents_cr)


@dataclass
class WorkingCapitalDynamics:
    inventory_days_dio: float
    debtor_days_dso: float
    creditor_days_dpo: float
    net_working_capital_pct_sales: float
    provenance: Optional[ProvenanceRef] = None

    @property
    def cash_conversion_cycle_days(self) -> float:
        return self.debtor_days_dso + self.inventory_days_dio - self.creditor_days_dpo


@dataclass
class NonFinancialGovernance:
    promoter_pledge_pct: float
    related_party_transactions_pct_rev: float
    top_5_customer_concentration_pct: float
    herfindahl_hhi_index: float
    contingent_liabilities_pct_networth: float
    independent_directors_pct: float
    provenance: Optional[ProvenanceRef] = None


@dataclass
class IngestionAuditItem:
    field_name: str
    raw_extracted_value: str
    normalized_metric: str
    status: str  # FOUND_AND_RECONCILED, CONVERTED_AND_NORMALIZED, MISSING_UNDISCLOSED
    citation: str
    confidence_score: float = 1.0


@dataclass
class PreIPODealDossier:
    deal_id: str
    company_name: str
    sector: str
    filing_type: str  # DRHP, RHP
    filing_date: str
    total_issue_size_cr: float
    fresh_issue_cr: float
    ofs_cr: float
    face_value_inr: float
    brlm_bankers: List[str]
    exchange_listing: List[str]
    history: List[FinancialYearMetric]
    indebtedness: IndebtednessSchedule
    working_capital: WorkingCapitalDynamics
    governance: NonFinancialGovernance
    audit_report: List[IngestionAuditItem] = field(default_factory=list)

    @property
    def latest_financials(self) -> FinancialYearMetric:
        return self.history[-1]

    @property
    def fresh_issue_pct(self) -> float:
        if self.total_issue_size_cr <= 0:
            return 0.0
        return (self.fresh_issue_cr / self.total_issue_size_cr) * 100.0

    @property
    def ofs_pct(self) -> float:
        if self.total_issue_size_cr <= 0:
            return 0.0
        return (self.ofs_cr / self.total_issue_size_cr) * 100.0
