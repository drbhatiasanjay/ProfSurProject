"""Canonical Field Binding Register and Model Adapters for Pre-IPO Ingestion.
Defines typed specifications for all 74 field families across 16 document profiles.
Translates canonical observations into legacy PreIPODealDossier and analytical models.
"""
from dataclasses import dataclass, field
from decimal import Decimal
from typing import Dict, List, Optional, Any, Union
import json
import csv
from pathlib import Path

# Lifecycle Status Flags per Section 17 of Design Specification
STATUS_DESIGNED = "DESIGNED"
STATUS_SCHEMA_READY = "SCHEMA_READY"
STATUS_EXTRACTOR_READY = "EXTRACTOR_READY"
STATUS_REVIEW_READY = "REVIEW_READY"
STATUS_MODEL_ADAPTER_READY = "MODEL_ADAPTER_READY"
STATUS_UI_READY = "UI_READY"
STATUS_EXPORT_READY = "EXPORT_READY"
STATUS_DELETE_READY = "DELETE_READY"
STATUS_ACCEPTED = "ACCEPTED"


@dataclass(frozen=True)
class FieldBindingSpec:
    canonical_id: str
    profile: str
    value_type: str
    existing_binding: str
    availability_status: str
    required_work: str
    target_store: str
    screen_consumer: str
    runtime_mapping_accepted: str
    child_fields: tuple = ()


# ── Nested Child Dataclasses for Complex Records ──────────────────────────────

@dataclass
class LeaseMovement:
    opening_balance_cr: Optional[float] = None
    additions_cr: Optional[float] = None
    interest_accreted_cr: Optional[float] = None
    payments_made_cr: Optional[float] = None
    closing_balance_cr: Optional[float] = None


@dataclass
class DebtFacilityItem:
    facility_type: str  # TERM_LOAN, WORKING_CAPITAL, NCD, UNSECURED
    lender_name: str
    currency: str = "INR"
    sanctioned_amount_cr: Optional[float] = None
    outstanding_amount_cr: Optional[float] = None
    interest_rate_pct: Optional[float] = None
    repayment_maturity: Optional[str] = None
    security_description: Optional[str] = None


@dataclass
class RPTTransaction:
    counterparty_name: str
    relationship: str
    nature_of_transaction: str
    transaction_amount_cr: Optional[float] = None
    balance_outstanding_cr: Optional[float] = None


@dataclass
class UseOfProceedsItem:
    purpose: str
    estimated_amount_cr: float
    deployment_schedule: Optional[str] = None


# ── Catalogue of 74 Field Families ───────────────────────────────────────────

def _load_canonical_register() -> Dict[str, FieldBindingSpec]:
    """Parse canonical register CSV and instantiate typed specifications."""
    csv_path = Path(__file__).parent.parent / "docs" / "plans" / "PRE_IPO_FIELD_BINDING_REGISTER_2026-11-08.csv"
    if not csv_path.exists():
        return {}

    registry = {}
    with open(csv_path, "r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            cid = row["canonical_field"]
            registry[cid] = FieldBindingSpec(
                canonical_id=cid,
                profile=row["profile"],
                value_type=row["value_type"],
                existing_binding=row["existing_binding"],
                availability_status=row["availability_status"],
                required_work=row["required_work"],
                target_store=row["target_store"],
                screen_consumer=row["screen_consumer"],
                runtime_mapping_accepted=row["runtime_mapping_accepted"]
            )
    return registry


FIELD_REGISTRY: Dict[str, FieldBindingSpec] = _load_canonical_register()


def get_field_spec(canonical_id: str) -> Optional[FieldBindingSpec]:
    """Look up specification by canonical ID."""
    return FIELD_REGISTRY.get(canonical_id)


def list_fields_by_profile(profile: str) -> List[FieldBindingSpec]:
    """Return all field bindings belonging to a profile."""
    return [spec for spec in FIELD_REGISTRY.values() if spec.profile == profile]


# ── Model Adapters: Observations -> PreIPODealDossier / Analytical Inputs ────

class PreIPOModelAdapter:
    """Translates canonical observations into legacy PreIPODealDossier and model inputs."""

    @staticmethod
    def observations_to_dossier(company_name: str, observations: List[Dict[str, Any]]):
        """Construct a PreIPODealDossier instance from a list of observations."""
        from models.pre_ipo_schema import (
            PreIPODealDossier,
            FinancialYearMetric,
            IndebtednessSchedule,
            WorkingCapitalDynamics,
            NonFinancialGovernance
        )

        # First collect debt fields and periods
        periods_map: Dict[str, Dict[str, Any]] = {}
        debt_fields: Dict[str, Any] = {
            "secured_term_loans_cr": 0.0,
            "working_capital_loans_cr": 0.0,
            "ncd_bonds_cr": 0.0,
            "unsecured_loans_cr": 0.0,
            "lease_liabilities_ind_as_116_cr": 0.0,
            "cash_and_equivalents_cr": 0.0,
        }

        for obs in observations:
            metric = obs.get("metric_id", "")
            val_raw = obs.get("value")
            if val_raw is None:
                continue

            try:
                val = float(str(val_raw).replace(",", ""))
            except (ValueError, TypeError):
                continue

            period = obs.get("period") or "FY24"
            if period not in periods_map:
                periods_map[period] = {"fiscal_year": period}

            # Map financial metrics
            if metric in ("financial.revenue_operations", "history[0].revenue_ops_cr"):
                periods_map[period]["revenue_ops_cr"] = val
            elif metric in ("financial.ebitda_reported", "history[0].ebitda_cr"):
                periods_map[period]["ebitda_cr"] = val
            elif metric in ("financial.pat", "history[0].pat_cr"):
                periods_map[period]["pat_cr"] = val
            elif metric in ("financial.cfo", "history[0].cfo_cr"):
                periods_map[period]["cfo_cr"] = val
            elif metric in ("financial.cfi", "history[0].cfi_cr"):
                periods_map[period]["cfi_cr"] = val
            elif metric in ("financial.cff", "history[0].cff_cr"):
                periods_map[period]["cff_cr"] = val
            elif metric in ("financial.cash_capex", "history[0].capex_cr"):
                periods_map[period]["capex_cr"] = val
            elif metric in ("financial.fcf", "history[0].fcf_cr"):
                periods_map[period]["fcf_cr"] = val
            elif metric in ("financial.equity_and_retained_earnings", "history[0].net_worth_cr"):
                periods_map[period]["net_worth_cr"] = val
            elif metric in ("financial.assets_and_liabilities", "history[0].total_assets_cr"):
                periods_map[period]["total_assets_cr"] = val
            elif metric in ("financial.receivables", "history[0].receivables_cr"):
                periods_map[period]["receivables_cr"] = val

            # Map indebtedness metrics
            elif metric in ("debt.facilities.secured_term_loans", "indebtedness.secured_term_loans_cr"):
                debt_fields["secured_term_loans_cr"] = val
            elif metric in ("debt.facilities.working_capital_loans", "indebtedness.working_capital_loans_cr"):
                debt_fields["working_capital_loans_cr"] = val
            elif metric in ("debt.cash_restrictions.cash_and_equivalents", "indebtedness.cash_and_equivalents_cr"):
                debt_fields["cash_and_equivalents_cr"] = val
            elif metric in ("lease.liability_movement", "indebtedness.lease_liabilities_ind_as_116_cr"):
                debt_fields["lease_liabilities_ind_as_116_cr"] = val

        indebtedness_inst = IndebtednessSchedule(
            secured_term_loans_cr=debt_fields["secured_term_loans_cr"],
            working_capital_loans_cr=debt_fields["working_capital_loans_cr"],
            ncd_bonds_cr=debt_fields["ncd_bonds_cr"],
            unsecured_loans_cr=debt_fields["unsecured_loans_cr"],
            lease_liabilities_ind_as_116_cr=debt_fields["lease_liabilities_ind_as_116_cr"],
            cash_and_equivalents_cr=debt_fields["cash_and_equivalents_cr"],
        )

        wc_inst = WorkingCapitalDynamics(
            inventory_days_dio=0.0,
            debtor_days_dso=0.0,
            creditor_days_dpo=0.0,
            net_working_capital_pct_sales=0.0
        )

        gov_inst = NonFinancialGovernance(
            promoter_pledge_pct=0.0,
            related_party_transactions_pct_rev=0.0,
            top_5_customer_concentration_pct=0.0,
            herfindahl_hhi_index=0.0,
            contingent_liabilities_pct_networth=0.0,
            independent_directors_pct=0.0
        )

        dossier = PreIPODealDossier(
            deal_id=f"deal-{company_name.lower().replace(' ', '-')}",
            company_name=company_name,
            sector="General Pre-IPO Diligence",
            filing_type="DRHP",
            filing_date="2024-01-01",
            total_issue_size_cr=0.0,
            fresh_issue_cr=0.0,
            ofs_cr=0.0,
            face_value_inr=10.0,
            brlm_bankers=[],
            exchange_listing=["NSE", "BSE"],
            history=[],
            indebtedness=indebtedness_inst,
            working_capital=wc_inst,
            governance=gov_inst
        )

        # Populate history
        for p_key in sorted(periods_map.keys(), reverse=True):
            p_data = periods_map[p_key]
            dossier.history.append(FinancialYearMetric(
                fiscal_year=p_data.get("fiscal_year", "FY24"),
                revenue_ops_cr=p_data.get("revenue_ops_cr", 0.0),
                ebitda_cr=p_data.get("ebitda_cr", 0.0),
                pat_cr=p_data.get("pat_cr", 0.0),
                cfo_cr=p_data.get("cfo_cr", 0.0),
                cfi_cr=p_data.get("cfi_cr", 0.0),
                cff_cr=p_data.get("cff_cr", 0.0),
                capex_cr=p_data.get("capex_cr", 0.0),
                fcf_cr=p_data.get("fcf_cr", 0.0),
                net_worth_cr=p_data.get("net_worth_cr", 0.0),
                total_assets_cr=p_data.get("total_assets_cr", 0.0),
                receivables_cr=p_data.get("receivables_cr", 0.0)
            ))

        return dossier

    @staticmethod
    def extract_analytical_inputs(observations: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Extract inputs required for financial ratios and covenant analysis."""
        adapter = PreIPOModelAdapter.observations_to_dossier("Analysis", observations)
        hist = adapter.history[0] if adapter.history else None

        rev = hist.revenue_ops_cr if hist else 0.0
        ebitda = hist.ebitda_cr if hist else 0.0
        pat = hist.pat_cr if hist else 0.0
        net_worth = hist.net_worth_cr if hist else 0.0
        total_debt = adapter.indebtedness.funded_bank_debt_cr
        cash = adapter.indebtedness.cash_and_equivalents_cr
        net_debt = adapter.indebtedness.net_funded_debt_cr

        return {
            "revenue_ops_cr": rev,
            "ebitda_cr": ebitda,
            "pat_cr": pat,
            "net_worth_cr": net_worth,
            "total_debt_cr": total_debt,
            "cash_cr": cash,
            "net_debt_cr": net_debt,
            "net_debt_to_ebitda": (net_debt / ebitda) if ebitda > 0 else None,
            "leverage_pct": (total_debt / (total_debt + net_worth) * 100) if (total_debt + net_worth) > 0 else 0.0,
            "is_eligible_for_underwriting": rev > 0 and ebitda != 0.0
        }
