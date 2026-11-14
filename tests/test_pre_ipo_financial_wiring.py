"""Adversarial verification of canonical FinancialStatementsContract and production caller wiring.

Validates:
- P0-04: Canonical FinancialStatementsContract enforcement across production callers.
- P0-05: Strict segregation of funded bank debt from Ind AS 116 operating lease liabilities.
- P0-06: Dickinson (2011) life cycle stage classification derived strictly from verified cash flow signs.
- Adversarial AST verification: Production routes actively invoke FinancialStatementsContract.
- Adversarial truthiness check: Zero 'val or default' in financial numerical calculations.
"""

import ast
import json
import re
from pathlib import Path
import pytest

from models.pre_ipo_financial_contracts import (
    FinancialStatementsContract,
    DickinsonLifeCycle,
    validate_ebitda_metric,
    validate_cash_flow_inputs,
    validate_net_worth_contract,
    MetricDefinition,
)
from models.pre_ipo_schema import FinancialYearMetric, IndebtednessSchedule
from models.pre_ipo_engine import classify_dickinson_stage


REPO_ROOT = Path(__file__).resolve().parent.parent


def test_financial_statements_contract_statutory_ebitda_perimeter():
    """Verify that FinancialStatementsContract enforces statutory EBITDA."""
    # When statutory_kpi_ebitda_cr is explicitly provided on metric
    fy = FinancialYearMetric(
        fiscal_year="FY24",
        revenue_ops_cr=14021.55,
        ebitda_cr=1895.71,
        pat_cr=2812.10,
        cfo_cr=284.69,
        cfi_cr=-291.55,
        cff_cr=-125.05,
        capex_cr=350.00,
        fcf_cr=-65.31,
        net_worth_cr=8897.18,
        statutory_kpi_ebitda_cr=1895.71,
        operating_profit_bwc_cr=1950.00,
    )
    contract = FinancialStatementsContract.from_financial_metric(fy)
    assert contract.statutory_ebitda_cr == 1895.71
    assert contract.ebitda_margin_pct == pytest.approx(13.52, abs=0.01)

    # Rejection of operating profit before WC changes as EBITDA
    wc_validation = validate_ebitda_metric(MetricDefinition.CF_PROFIT_BEFORE_WC.value, 1950.0)
    assert not wc_validation["accepted"]
    assert "cannot satisfy operating EBITDA" in wc_validation["error"]

    # Rejection of EBIT without D&A addback
    ebit_validation = validate_ebitda_metric(MetricDefinition.EBIT.value, 1500.0)
    assert not ebit_validation["accepted"]
    assert "depreciation and amortization add-back" in ebit_validation["error"]


def test_financial_statements_contract_debt_separation():
    """Verify strict segregation of funded bank debt from Ind AS 116 operating leases."""
    ind = IndebtednessSchedule(
        secured_term_loans_cr=150.0,
        working_capital_loans_cr=50.0,
        ncd_bonds_cr=100.0,
        unsecured_loans_cr=20.0,
        lease_liabilities_ind_as_116_cr=430.0,
        cash_and_equivalents_cr=80.0,
    )
    fy = FinancialYearMetric(
        fiscal_year="FY24",
        revenue_ops_cr=5000.0,
        ebitda_cr=800.0,
        pat_cr=400.0,
        cfo_cr=500.0,
        cfi_cr=-200.0,
        cff_cr=-100.0,
        capex_cr=150.0,
        fcf_cr=350.0,
        net_worth_cr=3000.0,
    )
    contract = FinancialStatementsContract.from_financial_metric(fy, indebtedness=ind)

    # Funded bank debt: 150 + 50 + 100 + 20 = 320 Cr
    assert contract.funded_bank_debt_cr == 320.0
    # Lease liabilities: 430 Cr
    assert contract.lease_liabilities_cr == 430.0
    # Total economic indebtedness: 320 + 430 = 750 Cr
    assert contract.total_economic_indebtedness_cr == 750.0
    # Net economic debt: 750 - 80 = 670 Cr
    assert contract.net_economic_debt_cr == 670.0
    # Net funded debt: 320 - 80 = 240 Cr
    assert contract.net_funded_debt_cr == 240.0


def test_financial_statements_contract_net_worth_nci_exclusion():
    """Verify that attributable Net Worth strictly excludes Non-Controlling Interest."""
    fy = FinancialYearMetric(
        fiscal_year="FY24",
        revenue_ops_cr=10000.0,
        ebitda_cr=1500.0,
        pat_cr=800.0,
        cfo_cr=1000.0,
        cfi_cr=-300.0,
        cff_cr=-200.0,
        capex_cr=200.0,
        fcf_cr=800.0,
        net_worth_cr=5000.0,
        parent_net_worth_cr=4800.0,
        non_controlling_interest_cr=200.0,
    )
    contract = FinancialStatementsContract.from_financial_metric(fy)
    assert contract.net_worth_cr == 4800.0
    assert contract.non_controlling_interest_cr == 200.0

    # Contract rejects total equity with NCI satisfying net worth
    nw_validation = validate_net_worth_contract(
        MetricDefinition.TOTAL_EQUITY_WITH_NCI.value,
        5000.0,
        nci=200.0,
    )
    assert not nw_validation["accepted"]
    assert "cannot satisfy Net Worth contract" in nw_validation["error"]


def test_financial_statements_contract_dickinson_classification():
    """Verify Dickinson (2011) life-cycle stages and fail-closed handling."""
    # 1. Growth: (+, -, +)
    c_growth = FinancialStatementsContract(
        fiscal_year="FY24", revenue_ops_cr=100.0, pat_cr=10.0,
        cfo_cr=50.0, cfi_cr=-30.0, cff_cr=20.0,
        statutory_ebitda_cr=20.0, net_worth_cr=80.0
    )
    stage, pattern = c_growth.dickinson_classification
    assert stage == "Growth"
    assert pattern == "(+, -, +)"

    # 2. Mature (Cash Cow): (+, -, -)
    c_mature = FinancialStatementsContract(
        fiscal_year="FY24", revenue_ops_cr=100.0, pat_cr=10.0,
        cfo_cr=50.0, cfi_cr=-20.0, cff_cr=-25.0,
        statutory_ebitda_cr=20.0, net_worth_cr=80.0
    )
    stage, pattern = c_mature.dickinson_classification
    assert stage == "Mature (Cash Cow)"
    assert pattern == "(+, -, -)"

    # 3. Introduction: (-, -, +)
    c_intro = FinancialStatementsContract(
        fiscal_year="FY24", revenue_ops_cr=100.0, pat_cr=-10.0,
        cfo_cr=-50.0, cfi_cr=-80.0, cff_cr=120.0,
        statutory_ebitda_cr=5.0, net_worth_cr=60.0
    )
    stage, pattern = c_intro.dickinson_classification
    assert stage == "Introduction"
    assert pattern == "(-, -, +)"

    # 4. Decline: (-, +, -)
    c_decline = FinancialStatementsContract(
        fiscal_year="FY24", revenue_ops_cr=100.0, pat_cr=-20.0,
        cfo_cr=-20.0, cfi_cr=40.0, cff_cr=-15.0,
        statutory_ebitda_cr=-5.0, net_worth_cr=30.0
    )
    stage, pattern = c_decline.dickinson_classification
    assert stage == "Decline"
    assert pattern == "(-, +, -)"

    # 5. Shake-out: (-, -, -)
    c_shakeout = FinancialStatementsContract(
        fiscal_year="FY24", revenue_ops_cr=100.0, pat_cr=-10.0,
        cfo_cr=-10.0, cfi_cr=-10.0, cff_cr=-10.0,
        statutory_ebitda_cr=5.0, net_worth_cr=50.0
    )
    stage, pattern = c_shakeout.dickinson_classification
    assert stage == "Shake-out"

    # Adversarial Fail-Closed: Missing cash flow values unconditionally fail
    c_missing = FinancialStatementsContract(
        fiscal_year="FY24", revenue_ops_cr=100.0, pat_cr=10.0,
        cfo_cr=None, cfi_cr=-20.0, cff_cr=-25.0,
        statutory_ebitda_cr=20.0, net_worth_cr=80.0
    )
    stage, pattern = c_missing.dickinson_classification
    assert stage == "Unclassified (Missing Cash Flow Data)"
    assert pattern == "(?, ?, ?)"

    # Standalone engine function delegates to the same logic
    assert classify_dickinson_stage(50.0, -30.0, 20.0) == ("Growth", "(+, -, +)")
    assert classify_dickinson_stage(None, -30.0, 20.0) == ("Unclassified (Missing Cash Flow Data)", "(?, ?, ?)")


def test_financial_statements_contract_from_accepted_snapshot():
    """Verify loading contract from an accepted golden snapshot."""
    golden_path = REPO_ROOT / "data" / "golden_oracles" / "hindustan_coca_cola_golden.json"
    with open(golden_path, encoding="utf-8") as f:
        golden_payload = json.load(f)

    # FY24
    c_fy24 = FinancialStatementsContract.from_accepted_snapshot(golden_payload, period="FY24")
    assert c_fy24.fiscal_year == "FY24"
    assert c_fy24.revenue_ops_cr == 14021.55
    assert c_fy24.statutory_ebitda_cr == 1895.71
    assert c_fy24.cfo_cr == 284.69
    assert c_fy24.cfi_cr == -291.55
    assert c_fy24.cff_cr == -125.05
    assert c_fy24.funded_bank_debt_cr == 0.0
    assert c_fy24.cash_and_equivalents_cr == 138.95
    assert c_fy24.net_worth_cr == 8897.18
    stage, pattern = c_fy24.dickinson_classification
    assert stage == "Mature (Cash Cow)"
    assert pattern == "(+, -, -)"

    # FY25
    c_fy25 = FinancialStatementsContract.from_accepted_snapshot(golden_payload, period="FY25")
    assert c_fy25.fiscal_year == "FY25"
    assert c_fy25.revenue_ops_cr == 12751.29
    assert c_fy25.statutory_ebitda_cr == 1726.31
    assert c_fy25.cfo_cr == 1572.70
    assert c_fy25.cfi_cr == -2071.56
    assert c_fy25.cff_cr == 492.88
    stage_25, pattern_25 = c_fy25.dickinson_classification
    assert stage_25 == "Growth"
    assert pattern_25 == "(+, -, +)"


def test_production_callers_invoke_financial_statements_contract_ast():
    """AST call-graph scan asserting production files import and invoke FinancialStatementsContract."""
    production_files = [
        REPO_ROOT / "pages" / "27_pre_ipo_drhp.py",
        REPO_ROOT / "models" / "pre_ipo_engine.py",
        REPO_ROOT / "utils" / "pre_ipo_deck_generator.py",
    ]

    for p in production_files:
        assert p.is_file(), f"File {p} must exist."
        tree = ast.parse(p.read_text(encoding="utf-8"))

        # Verify import of FinancialStatementsContract
        imports_contract = False
        invokes_contract = False

        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom):
                for alias in node.names:
                    if alias.name == "FinancialStatementsContract":
                        imports_contract = True
            elif isinstance(node, ast.Call):
                func = node.func
                if isinstance(func, ast.Name) and func.id == "FinancialStatementsContract":
                    invokes_contract = True
                elif isinstance(func, ast.Attribute) and func.attr in (
                    "from_financial_metric", "from_history_and_indebtedness", "from_accepted_snapshot"
                ):
                    invokes_contract = True

        assert imports_contract, f"{p.name} must import FinancialStatementsContract"
        assert invokes_contract, f"{p.name} must actively invoke FinancialStatementsContract (Zero Dead Code)"


def test_zero_python_truthiness_in_financial_calculations():
    """Adversarial check: zero numeric 'val or default' patterns in financial engines."""
    prohibited_pattern = re.compile(
        r'\b(?:ebitda|debt|wair|cfo|cfi|cff|tax|beta|price|shares|margin|spread)\w*\s+or\s+(?:\d|\'|")',
        re.IGNORECASE
    )

    targets = [
        REPO_ROOT / "models" / "pre_ipo_engine.py",
        REPO_ROOT / "models" / "pre_ipo_financial_contracts.py",
        REPO_ROOT / "utils" / "pre_ipo_deck_generator.py",
    ]

    violations = []
    for target in targets:
        lines = target.read_text(encoding="utf-8").splitlines()
        for idx, line in enumerate(lines, 1):
            if "#" in line:
                line_code = line.split("#")[0]
            else:
                line_code = line
            if prohibited_pattern.search(line_code):
                violations.append(f"{target.name}:{idx} -> {line.strip()}")

    assert not violations, f"Prohibited Python truthiness found in financial modules:\n" + "\n".join(violations)
