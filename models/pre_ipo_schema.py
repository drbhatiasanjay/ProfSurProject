"""
Pre-IPO DRHP Intelligence Data Schemas & Provenance Contracts.
Defines structured dataclasses for SEBI ICDR 2018 Restated Financials,
Funded vs Economic Indebtedness, Non-Financial Governance, Auditable Ingestion,
Cap Table Dilution, Objects of Offer Waterfall, Beneish Forensics, Debt Maturity Ladder,
Valuation Peer Comps, Structured Decision Limitations, and Investment Committee Stance.
"""
import math
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
    total_assets_cr: Optional[float] = None
    receivables_cr: Optional[float] = None
    gross_margin_pct: Optional[float] = None
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
    fixed_rate_portion_pct: float = 20.0
    floating_rate_portion_pct: float = 80.0
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

    @property
    def floating_rate_debt_pct(self) -> float:
        return self.floating_rate_portion_pct

    @property
    def fixed_rate_debt_pct(self) -> float:
        return self.fixed_rate_portion_pct


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
class AnchorLockinMilestone:
    milestone_name: str  # e.g. "Listing Day (T0)", "Day 30 Unlock (50% Anchor)", "Day 90 Unlock (100% Anchor)", "Day 180 Promoter Excess"
    days_from_listing: int  # 0, 30, 90, 180
    calendar_date: str  # YYYY-MM-DD or projected
    unlocked_pct: float  # % of anchor or excess tranche unlocked
    unlocked_shares_cr: float  # Estimated shares (Cr)
    unlocked_value_cr: float  # Estimated value (₹ Cr)
    cumulative_free_float_pct: float  # Resulting free float %
    supply_risk_level: str  # LOW, MEDIUM, ELEVATED, HIGH
    status: str  # EXPIRED, ACTIVE_WINDOW, UPCOMING
    exchange_notice_ref: str = "SEBI ICDR Reg 17 / NSE Circular"


@dataclass
class CapTableDilution:
    promoter_holding_pre_pct: float
    promoter_holding_post_pct: float
    public_holding_post_pct: float
    anchor_portion_pct: float = 30.0
    promoter_min_contribution_lock_months: int = 18
    promoter_excess_holding_lock_months: int = 6
    anchor_lock_30d_pct: float = 50.0
    anchor_lock_90d_pct: float = 50.0
    employee_reservation_cr: float = 0.0
    anchor_lockin_schedule: List[AnchorLockinMilestone] = field(default_factory=list)
    provenance: Optional[ProvenanceRef] = None

    @property
    def promoter_dilution_pct(self) -> float:
        return max(0.0, self.promoter_holding_pre_pct - self.promoter_holding_post_pct)


@dataclass
class ObjectsOfOfferWaterfall:
    gross_fresh_issue_cr: float
    issue_expenses_cr: float
    debt_prepayment_cr: float
    capex_expansion_cr: float
    inorganic_acquisition_cr: float
    general_corporate_purposes_cr: float
    interest_rate_on_retired_debt_pct: float = 9.0
    shares_pre_issue_cr: float = 36.0
    shares_post_issue_cr: float = 40.0
    pre_issue_pat_cr: float = 0.0
    provenance: Optional[ProvenanceRef] = None

    @property
    def net_fresh_proceeds_cr(self) -> float:
        return max(0.0, self.gross_fresh_issue_cr - self.issue_expenses_cr)

    @property
    def gcp_pct_of_gross(self) -> float:
        if self.gross_fresh_issue_cr <= 0:
            return 0.0
        return (self.general_corporate_purposes_cr / self.gross_fresh_issue_cr) * 100.0

    @property
    def total_specified_uses_cr(self) -> float:
        return round(
            self.debt_prepayment_cr
            + self.capex_expansion_cr
            + self.inorganic_acquisition_cr
            + self.general_corporate_purposes_cr,
            2,
        )

    @property
    def is_allocation_valid(self) -> bool:
        # Total uses cannot exceed net proceeds (allow 0.05 Cr rounding tolerance)
        # All allocations must be non-negative
        if self.gross_fresh_issue_cr < 0 or self.issue_expenses_cr < 0:
            return False
        if any(x < 0 for x in (self.debt_prepayment_cr, self.capex_expansion_cr, self.inorganic_acquisition_cr, self.general_corporate_purposes_cr)):
            return False
        return self.total_specified_uses_cr <= (self.net_fresh_proceeds_cr + 0.05)

    @property
    def allocation_variance_cr(self) -> float:
        return round(self.net_fresh_proceeds_cr - self.total_specified_uses_cr, 2)

    @property
    def sebi_gcp_compliant(self) -> bool:
        # SEBI ICDR 2018 Reg 7(1): GCP shall not exceed 25% of gross fresh issue
        # AND total allocations must be structurally valid
        if not self.is_allocation_valid:
            return False
        return self.gcp_pct_of_gross <= 25.01

    @property
    def eligible_debt_prepayment_cr(self) -> float:
        # Debt prepayment cannot exceed net fresh proceeds
        return max(0.0, min(self.debt_prepayment_cr, self.net_fresh_proceeds_cr))

    @property
    def annual_interest_savings_cr(self) -> float:
        # Only eligible prepayment qualifies for interest savings
        return round(self.eligible_debt_prepayment_cr * (self.interest_rate_on_retired_debt_pct / 100.0), 2)

    @property
    def pro_forma_pat_accretion_cr(self) -> float:
        # Corporate tax rate: 25.17% (Section 115BAA)
        return round(self.annual_interest_savings_cr * (1.0 - 0.2517), 2)

    @property
    def pre_issue_eps_inr(self) -> Optional[float]:
        if self.shares_pre_issue_cr <= 0:
            return None
        return round(self.pre_issue_pat_cr / self.shares_pre_issue_cr, 2)

    @property
    def post_issue_pro_forma_eps_inr(self) -> Optional[float]:
        if self.shares_post_issue_cr <= 0:
            return None
        post_pat = self.pre_issue_pat_cr + self.pro_forma_pat_accretion_cr
        return round(post_pat / self.shares_post_issue_cr, 2)

    @property
    def eps_accretion_dilution_inr(self) -> Optional[float]:
        pre = self.pre_issue_eps_inr
        post = self.post_issue_pro_forma_eps_inr
        if pre is None or post is None:
            return None
        return round(post - pre, 2)

    @property
    def is_dilutive(self) -> Optional[bool]:
        diff = self.eps_accretion_dilution_inr
        if diff is None:
            return None
        return diff < 0

    @property
    def pro_forma_eps_accretion_inr(self) -> float:
        val = self.eps_accretion_dilution_inr
        return val if val is not None else 0.0


@dataclass
class BeneishMScoreRatios:
    dsri: Optional[float] = None   # Days Sales in Receivables Index
    gmi: Optional[float] = None    # Gross Margin Index
    aqi: Optional[float] = None    # Asset Quality Index
    sgi: Optional[float] = None    # Sales Growth Index
    depi: Optional[float] = None   # Depreciation Index
    sgai: Optional[float] = None   # SGA Expenses Index
    lvgi: Optional[float] = None   # Leverage Index
    tata: Optional[float] = None   # Total Accruals to Total Assets
    abnormal_cfo_proxy: float = 0.0
    provenance: Optional[ProvenanceRef] = None

    @property
    def is_computable(self) -> bool:
        # All 8 indices must be valid, finite non-NaN numbers
        ratios = (self.dsri, self.gmi, self.aqi, self.sgi, self.depi, self.sgai, self.lvgi, self.tata)
        for r in ratios:
            if r is None or not isinstance(r, (int, float)) or not math.isfinite(r) or math.isnan(r):
                return False
        return True

    @property
    def m_score(self) -> Optional[float]:
        if not self.is_computable:
            return None
        return round(
            -4.84
            + 0.920 * self.dsri
            + 0.528 * self.gmi
            + 0.404 * self.aqi
            + 0.892 * self.sgi
            + 0.115 * self.depi
            - 0.172 * self.sgai
            + 4.037 * self.tata
            + 0.0327 * self.lvgi,
            2,
        )

    @property
    def is_manipulation_risk(self) -> Optional[bool]:
        # Threshold: -1.78 per Beneish (1999)
        if not self.is_computable:
            return None
        ms = self.m_score
        if ms is None or not math.isfinite(ms) or math.isnan(ms):
            return None
        return ms > -1.78


@dataclass
class DebtMaturityLadder:
    repayment_due_year_1_cr: float  # Current maturities
    repayment_due_year_2_cr: float
    repayment_due_year_3_cr: float
    repayment_due_year_4_cr: float
    repayment_due_year_5_plus_cr: float
    fixed_rate_debt_pct: float
    floating_rate_debt_pct: float
    weighted_average_maturity_years: float = 3.2
    refinancing_risk_rating: str = "MODERATE"  # LOW, MODERATE, ELEVATED
    provenance: Optional[ProvenanceRef] = None

    @property
    def floating_rate_portion_pct(self) -> float:
        return self.floating_rate_debt_pct

    @property
    def fixed_rate_portion_pct(self) -> float:
        return self.fixed_rate_debt_pct

    @property
    def total_repayment_profile_cr(self) -> float:
        return (
            self.repayment_due_year_1_cr
            + self.repayment_due_year_2_cr
            + self.repayment_due_year_3_cr
            + self.repayment_due_year_4_cr
            + self.repayment_due_year_5_plus_cr
        )


@dataclass
class ListedPeerComp:
    peer_name: str
    ticker: str
    mcap_cr: float
    pe_ratio: Optional[float]
    ev_ebitda: Optional[float]
    ev_sales: float
    pb_ratio: float
    pat_margin_pct: float
    roe_pct: float
    dickinson_stage: str


@dataclass
class ValuationPeerBenchmarking:
    price_band_lower_inr: float
    price_band_upper_inr: float
    implied_mcap_cr: float
    implied_ev_cr: float
    implied_pe_ratio: float
    implied_ev_ebitda: float
    implied_ev_sales: float
    implied_pb_ratio: float
    sector_peer_group: str
    peers: List[ListedPeerComp]
    valuation_verdict: str  # ATTRACTIVE_DISCOUNT, FAIR_VALUE, EXPENSIVE_PREMIUM
    provenance: Optional[ProvenanceRef] = None

    @property
    def peer_median_pe(self) -> Optional[float]:
        if not self.peers:
            return None
        vals = sorted([p.pe_ratio for p in self.peers if p.pe_ratio is not None and p.pe_ratio > 0])
        if not vals:
            return None
        n = len(vals)
        if n % 2 == 1:
            return vals[n // 2]
        return round((vals[n // 2 - 1] + vals[n // 2]) / 2.0, 2)

    @property
    def peer_median_ev_ebitda(self) -> Optional[float]:
        if not self.peers:
            return None
        vals = sorted([p.ev_ebitda for p in self.peers if p.ev_ebitda is not None and p.ev_ebitda > 0])
        if not vals:
            return None
        n = len(vals)
        if n % 2 == 1:
            return vals[n // 2]
        return round((vals[n // 2 - 1] + vals[n // 2]) / 2.0, 2)

    @property
    def pe_discount_to_peers_pct(self) -> Optional[float]:
        med = self.peer_median_pe
        if med is None or med <= 0 or self.implied_pe_ratio <= 0:
            return None
        return round(((med - self.implied_pe_ratio) / med) * 100.0, 1)


@dataclass
class DecisionLimitationItem:
    gap_id: str
    item_name: str
    affected_dimension: str
    current_status: str  # NOT_SUPPLIED, PARSE_FAILED, INCONSISTENT, AWAITING_AUDIT, UNDISCLOSED, NOT_APPLICABLE
    why_it_matters: str
    blocked_decision_or_recommendation: str
    materiality_priority: str  # HIGH, MEDIUM, LOW
    recommended_diligence_request: str
    provisional_assumption_applied: Optional[str] = None


@dataclass
class InvestmentCommitteeVerdict:
    underwriting_verdict: str  # APPROVE WITH COVENANTS, RESTRICTED LEVERAGE, DELEVERAGING MANDATE, UNLEVERAGED M&A ACCRETION
    internal_screening_grade: str  # TIER_1_STRONG_CUSHION, TIER_2_MODERATE_LEVERAGE, TIER_3_ELEVATED_MONITORING
    max_recommended_leverage_ratio: float
    key_credit_strengths: List[str]
    key_downside_risks: List[str]
    mandatory_loan_covenants: List[str]
    treasury_call_to_action: str
    external_rating_agency: Optional[str] = None
    external_rating_symbol: Optional[str] = None
    rating_disclaimer: str = (
        "Internal quantitative screening grade only — does not constitute a statutory credit rating "
        "issued by a SEBI-registered Credit Rating Agency (SEBI CRA Regulations 1999)."
    )
    provenance: Optional[ProvenanceRef] = None

    @property
    def credit_rating_equivalent(self) -> str:
        # Backward-compatible property for existing consumers
        if self.external_rating_symbol:
            return f"{self.external_rating_symbol} (Official Agency)"
        return self.internal_screening_grade


@dataclass
class IngestionAuditItem:
    field_name: str
    raw_extracted_value: str
    normalized_metric: str
    status: str  # FOUND_AND_RECONCILED, CONVERTED_AND_NORMALIZED, MISSING_UNDISCLOSED
    citation: str
    confidence_score: float = 1.0


@dataclass
class CompanyBackground:
    cin: Optional[str]
    incorporation_year: int
    headquarters: str
    legal_form: str
    business_model_summary: str
    core_products_and_services: List[Dict[str, Any]]
    revenue_model: str
    customer_segments: List[str]
    geographic_presence: Dict[str, float]
    promoter_and_management_pedigree: str
    material_operational_dependencies: List[str]
    filing_cutoff_date: str
    provenance: Optional[ProvenanceRef] = None


@dataclass
class EquityClaimLineage:
    statement: str
    claim_type: str  # ISSUER_DISCLOSURE, CALCULATION, BENCHMARK, ANALYST_ESTIMATE
    verified_source: str
    confidence: str = "HIGH"  # HIGH, MEDIUM, PROVISIONAL


@dataclass
class EquityConditionalAction:
    recommendation: str
    action_owner: str
    preconditions: str
    completion_evidence: str
    monitoring_trigger: str


@dataclass
class EquityQuestionFinding:
    question_id: str  # Q01..Q10, PX01..PX04
    title: str
    status: str  # ANSWERED_WITH_EVIDENCE, PARTIAL_WITH_GAPS, BLOCKED_MISSING_DATA, NOT_APPLICABLE
    direct_verdict: str
    detailed_analysis: str
    evidence_sources: List[str]
    claim_lineage: List[EquityClaimLineage] = field(default_factory=list)
    alternative_explanations: List[str] = field(default_factory=list)
    limitations_and_uncertainties: List[str] = field(default_factory=list)
    conditional_recommendations: List[EquityConditionalAction] = field(default_factory=list)
    inflection_triggers: List[str] = field(default_factory=list)


@dataclass
class CMIECrosswalkRecord:
    canonical_concept: str
    cmie_field_code: str
    cmie_definition: str
    drhp_raw_value: str
    cmie_normalized_value: str
    status: str  # EXACT_MATCH, RECONCILED, UNDISCLOSED_IN_DRHP, NOT_SUPPLIED, PARSE_FAILED
    reconciliation_note: str


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
    cap_table: Optional[CapTableDilution] = None
    objects_of_offer: Optional[ObjectsOfOfferWaterfall] = None
    beneish_forensics: Optional[BeneishMScoreRatios] = None
    debt_maturity: Optional[DebtMaturityLadder] = None
    valuation_comps: Optional[ValuationPeerBenchmarking] = None
    ic_verdict: Optional[InvestmentCommitteeVerdict] = None
    background: Optional[CompanyBackground] = None
    equity_questions: Dict[str, EquityQuestionFinding] = field(default_factory=dict)
    cmie_crosswalk: List[CMIECrosswalkRecord] = field(default_factory=list)
    limitations: List[DecisionLimitationItem] = field(default_factory=list)
    audit_report: List[IngestionAuditItem] = field(default_factory=list)
    listing_date: Optional[str] = None
    issue_status: str = "COMPLETED"  # COMPLETED, RUNNING_PIPELINE, AWAITING_LISTING, PRE_IPO_DRHP
    anchor_calendar_active: bool = True

    @property
    def latest_financials(self) -> FinancialYearMetric:
        if not self.history:
            return FinancialYearMetric("None", 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0)
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
