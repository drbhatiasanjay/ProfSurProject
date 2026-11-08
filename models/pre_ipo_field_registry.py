"""Pre-IPO 74-Family Canonical Field Binding Register & Model Adapters.
Maps canonical observations across 16 document profiles to analytical models and legacy structures.
Packaged runtime resource loading guarantees availability across Docker container environments.
"""
import os
import csv
import json
from pathlib import Path
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional, Any, Union


# ── Typed Specification Dataclasses ──────────────────────────────────────────

@dataclass
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


@dataclass
class LeaseMovement:
    opening_balance: Optional[float] = None
    additions: Optional[float] = None
    interest_accrued: Optional[float] = None
    payments_made: Optional[float] = None
    closing_balance: Optional[float] = None


@dataclass
class DebtFacilityItem:
    lender_name: str = ""
    facility_type: str = ""
    sanctioned_amount_cr: Optional[float] = None
    outstanding_amount_cr: Optional[float] = None
    interest_rate_pct: Optional[float] = None
    repayment_terms: str = ""


@dataclass
class RPTTransaction:
    related_party_name: str = ""
    relationship: str = ""
    transaction_type: str = ""
    amount_cr: Optional[float] = None
    percentage_of_revenue: Optional[float] = None


@dataclass
class UseOfProceedsItem:
    object_category: str = ""
    sub_project: str = ""
    allocation_amount_cr: Optional[float] = None
    estimated_schedule_fy: str = ""


# ── Catalogue of 74 Field Families ───────────────────────────────────────────

def _load_canonical_register() -> Dict[str, FieldBindingSpec]:
    """Parse canonical register from package JSON resource or fallback to CSV."""
    json_path = Path(__file__).parent / "data" / "pre_ipo_field_bindings.json"
    if json_path.exists():
        with open(json_path, "r", encoding="utf-8") as f:
            records = json.load(f)
            return {
                r["canonical_field"]: FieldBindingSpec(
                    canonical_id=r["canonical_field"],
                    profile=r["profile"],
                    value_type=r["value_type"],
                    existing_binding=r["existing_binding"],
                    availability_status=r["availability_status"],
                    required_work=r["required_work"],
                    target_store=r["target_store"],
                    screen_consumer=r["screen_consumer"],
                    runtime_mapping_accepted=r["runtime_mapping_accepted"]
                )
                for r in records
            }

    csv_path = Path(__file__).parent.parent / "docs" / "plans" / "PRE_IPO_FIELD_BINDING_REGISTER_2026-11-08.csv"
    if csv_path.exists():
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

    raise RuntimeError("Critical Pre-IPO field registry configuration missing. Failed to load canonical field bindings.")


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
        """Construct a PreIPODealDossier instance strictly from reviewed/accepted observations."""
        from models.pre_ipo_schema import (
            PreIPODealDossier,
            FinancialYearMetric,
            IndebtednessSchedule,
            WorkingCapitalDynamics,
            NonFinancialGovernance
        )

        periods_map: Dict[str, Dict[str, Any]] = {}
        debt_fields: Dict[str, Any] = {
            "secured_term_loans_cr": None,
            "working_capital_loans_cr": None,
            "ncd_bonds_cr": None,
            "unsecured_loans_cr": None,
            "lease_liabilities_ind_as_116_cr": None,
            "cash_and_equivalents_cr": None,
        }

        # Filter strictly for ACCEPTED / AUDITED facts matching entity and INR currency
        valid_obs = []
        for obs in observations:
            rev_state = obs.get("review_state") or obs.get("review")
            if rev_state not in ("ACCEPTED", "AUDITED"):
                continue
            entity = obs.get("entity") or obs.get("context", {}).get("entity")
            if entity and company_name and entity.lower() != company_name.lower():
                continue
            curr = obs.get("currency") or obs.get("context", {}).get("currency")
            if curr and curr.upper() not in ("INR", "RS", "RUPEES", ""):
                continue
            valid_obs.append(obs)

        for obs in valid_obs:
            metric = obs.get("metric_id", "")
            val_raw = obs.get("value")
            if val_raw is None:
                continue

            try:
                val = float(str(val_raw).replace(",", ""))
            except (ValueError, TypeError):
                continue

            period = obs.get("period") or obs.get("context", {}).get("period") or "FY24"
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
            elif metric in ("debt.facilities.ncd_bonds", "indebtedness.ncd_bonds_cr"):
                debt_fields["ncd_bonds_cr"] = val
            elif metric in ("debt.facilities.unsecured_loans", "indebtedness.unsecured_loans_cr"):
                debt_fields["unsecured_loans_cr"] = val
            elif metric in ("debt.cash_restrictions.cash_and_equivalents", "indebtedness.cash_and_equivalents_cr"):
                debt_fields["cash_and_equivalents_cr"] = val
            elif metric in ("lease.liability_movement", "indebtedness.lease_liabilities_ind_as_116_cr"):
                debt_fields["lease_liabilities_ind_as_116_cr"] = val

        indebtedness_inst = IndebtednessSchedule(
            secured_term_loans_cr=debt_fields["secured_term_loans_cr"] or 0.0,
            working_capital_loans_cr=debt_fields["working_capital_loans_cr"] or 0.0,
            ncd_bonds_cr=debt_fields["ncd_bonds_cr"] or 0.0,
            unsecured_loans_cr=debt_fields["unsecured_loans_cr"] or 0.0,
            lease_liabilities_ind_as_116_cr=debt_fields["lease_liabilities_ind_as_116_cr"] or 0.0,
            cash_and_equivalents_cr=debt_fields["cash_and_equivalents_cr"] or 0.0,
        )

        wc_inst = WorkingCapitalDynamics(
            inventory_days_dio=None,
            debtor_days_dso=None,
            creditor_days_dpo=None,
            net_working_capital_pct_sales=None
        )

        gov_inst = NonFinancialGovernance(
            promoter_pledge_pct=None,
            related_party_transactions_pct_rev=None,
            top_5_customer_concentration_pct=None,
            herfindahl_hhi_index=None,
            contingent_liabilities_pct_networth=None,
            independent_directors_pct=None
        )

        dossier = PreIPODealDossier(
            deal_id=f"deal-{company_name.lower().replace(' ', '-')}",
            company_name=company_name,
            sector="General Pre-IPO Diligence",
            filing_type="DRHP",
            filing_date=None,
            total_issue_size_cr=None,
            fresh_issue_cr=None,
            ofs_cr=None,
            face_value_inr=None,
            brlm_bankers=[],
            exchange_listing=["NSE", "BSE"],
            history=[],
            indebtedness=indebtedness_inst,
            working_capital=wc_inst,
            governance=gov_inst
        )

        # Sort history chronologically ASCENDING (e.g. FY23, FY24, FY25) so history[-1] is latest
        for p_key in sorted(periods_map.keys(), reverse=False):
            p_data = periods_map[p_key]
            dossier.history.append(FinancialYearMetric(
                fiscal_year=p_data.get("fiscal_year", p_key),
                revenue_ops_cr=p_data.get("revenue_ops_cr"),
                ebitda_cr=p_data.get("ebitda_cr"),
                pat_cr=p_data.get("pat_cr"),
                cfo_cr=p_data.get("cfo_cr"),
                cfi_cr=p_data.get("cfi_cr"),
                cff_cr=p_data.get("cff_cr"),
                capex_cr=p_data.get("capex_cr"),
                fcf_cr=p_data.get("fcf_cr"),
                net_worth_cr=p_data.get("net_worth_cr"),
                total_assets_cr=p_data.get("total_assets_cr"),
                receivables_cr=p_data.get("receivables_cr")
            ))

        return dossier

    @staticmethod
    def extract_analytical_inputs(observations: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Extract inputs required for financial ratios and covenant analysis with strict qualification checks."""
        adapter = PreIPOModelAdapter.observations_to_dossier("Analysis", observations)
        hist = adapter.history[-1] if adapter.history else None  # latest period is the last item

        rev = hist.revenue_ops_cr if hist and hist.revenue_ops_cr is not None else None
        ebitda = hist.ebitda_cr if hist and hist.ebitda_cr is not None else None
        pat = hist.pat_cr if hist and hist.pat_cr is not None else None
        net_worth = hist.net_worth_cr if hist and hist.net_worth_cr is not None else None
        cfo = hist.cfo_cr if hist and hist.cfo_cr is not None else None

        total_debt = adapter.indebtedness.funded_bank_debt_cr
        cash = adapter.indebtedness.cash_and_equivalents_cr
        net_debt = adapter.indebtedness.net_funded_debt_cr

        # Strict eligibility verification
        reasons = []
        if rev is None or rev <= 0:
            reasons.append("Missing or non-positive accepted operating revenue")
        if ebitda is None or ebitda == 0.0:
            reasons.append("Missing or unverified accepted EBITDA")
        if cfo is None:
            reasons.append("Missing accepted Cash Flow from Operations (CFO)")
        if net_worth is None or net_worth <= 0:
            reasons.append("Missing or non-positive net worth")

        is_eligible = len(reasons) == 0

        net_debt_to_ebitda = (net_debt / ebitda) if (ebitda is not None and ebitda > 0 and net_debt is not None) else None
        denom = (total_debt + net_worth) if (total_debt is not None and net_worth is not None) else 0.0
        leverage_pct = (total_debt / denom * 100) if denom > 0 else None

        return {
            "revenue_ops_cr": rev,
            "ebitda_cr": ebitda,
            "pat_cr": pat,
            "cfo_cr": cfo,
            "net_worth_cr": net_worth,
            "total_debt_cr": total_debt,
            "cash_cr": cash,
            "net_debt_cr": net_debt,
            "net_debt_to_ebitda": net_debt_to_ebitda,
            "leverage_pct": leverage_pct,
            "is_eligible_for_underwriting": is_eligible,
            "eligibility_reasons": reasons
        }
