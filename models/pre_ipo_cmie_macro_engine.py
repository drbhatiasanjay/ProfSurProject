"""
Pre-IPO CMIE ProwessIQ Peer Intelligence & Macro Factor Linkage Engine
Milestone 16 (Phase 2C) - Cross-Ecosystem Synthesis

Integrates peer financial benchmarks (Varun Beverages, Tata Consumer, Dabur India)
and macroeconomic transmission channels (RBI Repo Rate, Food CPI, Brent Crude)
with the Pre-IPO Knowledge Graph for relative valuation and cost pass-through analysis.

Governed by:
- docs/SPEC_PRE_IPO_KNOWLEDGE_GRAPH_PHASE2.md
- Rule E.3: Zero Python Truthiness in Financial Calculations
- Rule E.2: Fail-Closed Architecture for Domain Boundaries
"""

from dataclasses import dataclass, asdict
from typing import Dict, List, Any, Optional


@dataclass
class CMIELocalPeer:
    peer_id: str
    company_name: str
    ticker_nse: str
    business_model: str
    ev_ebitda_multiple: float
    pe_multiple: float
    roce_pct: float
    gross_margin_pct: float
    ebitda_margin_pct: float
    revenue_3yr_cagr_pct: float
    franchise_exclusivity_years: int
    net_debt_to_ebitda: float
    valuation_verdict: str


@dataclass
class MacroeconomicTransmissionFactors:
    rbi_repo_rate_pct: float
    food_beverage_cpi_inflation_pct: float
    brent_crude_usd_per_bbl: float
    pet_resin_cost_inr_per_kg: float
    sugar_commodity_inr_per_quintal: float


@dataclass
class MacroShockSimulationResult:
    base_crude_usd: float
    shocked_crude_usd: float
    pet_resin_inflation_pct: float
    gross_margin_compression_bps: float
    post_shock_gross_margin_pct: float
    base_repo_rate_pct: float
    shocked_repo_rate_pct: float
    incremental_borrowing_cost_cr: float
    post_shock_ebitda_margin_pct: float
    relative_multiple_discount_pct: float
    ic_guidance: str
    macro_causal_nodes: List[Dict[str, Any]]
    macro_causal_edges: List[Dict[str, Any]]


# Ground-truth peer data from CMIE ProwessIQ & Annual Reports (FY24 / FY25)
CMIE_BEVERAGE_PEERS: List[CMIELocalPeer] = [
    CMIELocalPeer(
        peer_id="PEER_VBL",
        company_name="Varun Beverages Limited (RJ Corp)",
        ticker_nse="VBL",
        business_model="Exclusive PepsiCo Bottler (India, Nepal, Sri Lanka, Africa)",
        ev_ebitda_multiple=38.5,
        pe_multiple=62.4,
        roce_pct=28.4,
        gross_margin_pct=53.2,
        ebitda_margin_pct=23.8,
        revenue_3yr_cagr_pct=24.1,
        franchise_exclusivity_years=25,
        net_debt_to_ebitda=0.85,
        valuation_verdict="Premium multiple benchmark; high capital efficiency (28.4% ROCE) and 25-year franchise lock."
    ),
    CMIELocalPeer(
        peer_id="PEER_TATACONS",
        company_name="Tata Consumer Products Limited",
        ticker_nse="TATACONSUM",
        business_model="Diversified F&B (Tata Tea, NourishCo Water, Campa Rivalry)",
        ev_ebitda_multiple=42.1,
        pe_multiple=71.2,
        roce_pct=14.2,
        gross_margin_pct=43.8,
        ebitda_margin_pct=15.1,
        revenue_3yr_cagr_pct=11.6,
        franchise_exclusivity_years=0,
        net_debt_to_ebitda=0.45,
        valuation_verdict="Conglomerate FMCG brand premium; lower asset turnover offsets multiple."
    ),
    CMIELocalPeer(
        peer_id="PEER_DABUR",
        company_name="Dabur India Limited",
        ticker_nse="DABUR",
        business_model="Ayurvedic Beverages (Real Fruit Juice) & Consumer Goods",
        ev_ebitda_multiple=32.0,
        pe_multiple=48.5,
        roce_pct=22.1,
        gross_margin_pct=48.6,
        ebitda_margin_pct=19.4,
        revenue_3yr_cagr_pct=8.9,
        franchise_exclusivity_years=0,
        net_debt_to_ebitda=0.15,
        valuation_verdict="Mature growth profile with defensive balance sheet and pristine net debt."
    )
]

# Baseline macroeconomic constants for Indian capital markets
BASELINE_MACRO = MacroeconomicTransmissionFactors(
    rbi_repo_rate_pct=6.50,
    food_beverage_cpi_inflation_pct=7.20,
    brent_crude_usd_per_bbl=78.0,
    pet_resin_cost_inr_per_kg=92.5,
    sugar_commodity_inr_per_quintal=3850.0
)

# Issuer HCCB Baseline Financial Anchors
HCCB_BASELINE = {
    "company_name": "Hindustan Coca-Cola Holdings (Operating Co: HCCBPL)",
    "target_ipo_multiple": 24.5,
    "implied_pe": 41.2,
    "roce_pct": 19.8,
    "gross_margin_pct": 51.4,
    "ebitda_margin_pct": 17.2,
    "revenue_3yr_cagr_pct=16.8": 16.8,
    "total_debt_cr": 3270.50,
    "pet_resin_cogs_share_pct": 14.5,
    "sugar_cogs_share_pct": 18.2
}


class CMIEMacroEngine:
    """Computes relative valuation spreads and macroeconomic factor stress."""

    def get_peer_comparison(self) -> Dict[str, Any]:
        """Returns structured peer metrics, valuation differentials, and peer discount."""
        vbl = next(p for p in CMIE_BEVERAGE_PEERS if p.peer_id == "PEER_VBL")
        hccb_multiple = HCCB_BASELINE["target_ipo_multiple"]
        vbl_multiple = vbl.ev_ebitda_multiple

        multiple_discount_to_vbl_pct = round(((vbl_multiple - hccb_multiple) / vbl_multiple) * 100, 2)
        roce_gap_pct = round(vbl.roce_pct - HCCB_BASELINE["roce_pct"], 2)

        return {
            "issuer": HCCB_BASELINE,
            "peers": [asdict(p) for p in CMIE_BEVERAGE_PEERS],
            "relative_spread": {
                "hccb_ask_multiple": hccb_multiple,
                "vbl_trading_multiple": vbl_multiple,
                "multiple_discount_pct": multiple_discount_to_vbl_pct,
                "roce_differential_pct": roce_gap_pct,
                "analytical_verdict": (
                    f"HCCB's 24.5x ask represents a {multiple_discount_to_vbl_pct}% discount to Varun Beverages (38.5x). "
                    f"However, Varun commands a {roce_gap_pct} bps ROCE premium (28.4% vs 19.8%) due to younger bottling assets "
                    "and 25-year territorial lock, justifying a normalized discount of 20-25%."
                )
            },
            "macro_factors": asdict(BASELINE_MACRO)
        }

    def simulate_macro_shock(
        self,
        brent_crude_shift_usd: float = 0.0,
        rbi_repo_shift_bps: float = 0.0
    ) -> MacroShockSimulationResult:
        """
        Simulates commodity price pass-through and monetary rate shocks.
        Rule E.3: Preserves zero values explicitly (e.g. brent_crude_shift_usd=0.0).
        """
        if brent_crude_shift_usd is None:
            brent_crude_shift_usd = 0.0
        if rbi_repo_shift_bps is None:
            rbi_repo_shift_bps = 0.0

        base_crude = BASELINE_MACRO.brent_crude_usd_per_bbl
        shocked_crude = max(20.0, base_crude + brent_crude_shift_usd)
        crude_pct_change = (shocked_crude - base_crude) / base_crude

        # PET Resin pass-through elasticity: 0.65x
        pet_inflation_pct = round(crude_pct_change * 0.65 * 100, 2)

        # Gross margin impact: PET is 14.5% of CoGS, CoGS is 48.6% of Rev -> ~7.05% of Revenue
        gross_margin_compression_pct = (crude_pct_change * 0.65) * (HCCB_BASELINE["pet_resin_cogs_share_pct"] / 100.0) * 0.486
        gross_margin_compression_bps = round(gross_margin_compression_pct * 10000, 1)

        post_gross_margin = max(10.0, round(HCCB_BASELINE["gross_margin_pct"] - (gross_margin_compression_bps / 100.0), 2))

        # Monetary Rate Shock
        base_repo = BASELINE_MACRO.rbi_repo_rate_pct
        shocked_repo = max(0.0, round(base_repo + (rbi_repo_shift_bps / 100.0), 2))

        # Floating debt share is ~60% of total borrowings (₹3,270.5 Cr)
        floating_debt_cr = HCCB_BASELINE["total_debt_cr"] * 0.60
        incremental_borrowing_cr = round(floating_debt_cr * (rbi_repo_shift_bps / 10000.0), 2)

        # EBITDA margin compression from combined cost pressures
        ebitda_compression_pct = (gross_margin_compression_bps / 100.0)
        post_ebitda_margin = max(5.0, round(HCCB_BASELINE["ebitda_margin_pct"] - ebitda_compression_pct, 2))

        # Target multiple discount (10 bps multiple discount per 25 bps crude/EBITDA margin loss)
        multiple_discount_pct = round((ebitda_compression_pct / HCCB_BASELINE["ebitda_margin_pct"]) * 100 * 0.5, 2)

        if post_ebitda_margin < 12.0:
            guidance = "AVOID: Severe margin compression below sustainable bottling hurdle rate (12%)."
        elif multiple_discount_pct > 10.0:
            guidance = "SUBSCRIBE WITH VALUATION BUFFER: Commodity cost inflation requires 15% discount to offer band."
        else:
            guidance = "SUBSCRIBE: Resilient pass-through capability and stable borrowing cost headroom."

        # Causal graph nodes and edges
        causal_nodes = [
            {"id": "macro_crude", "label": "Brent Crude", "value": f"${shocked_crude:.1f}/bbl", "delta": f"{brent_crude_shift_usd:+.1f}$"},
            {"id": "factor_pet_resin", "label": "PET Resin Packaging", "value": f"{pet_inflation_pct:+.1f}%", "delta": "Pass-through 0.65x"},
            {"id": "issuer_gross_margin", "label": "HCCB Gross Margin", "value": f"{post_gross_margin:.2f}%", "delta": f"{-gross_margin_compression_bps:+.0f} bps"},
            {"id": "macro_repo", "label": "RBI Repo Rate", "value": f"{shocked_repo:.2f}%", "delta": f"{rbi_repo_shift_bps:+.0f} bps"},
            {"id": "issuer_borrowing_cost", "label": "Floating Debt Cost", "value": f"+₹{incremental_borrowing_cr:.2f} Cr", "delta": "60% Float"},
            {"id": "issuer_post_ebitda", "label": "Post-Shock EBITDA", "value": f"{post_ebitda_margin:.2f}%", "delta": f"Multiple -{multiple_discount_pct:.1f}%"}
        ]

        causal_edges = [
            {"source": "macro_crude", "target": "factor_pet_resin", "relation": "INFLATES_PACKAGING"},
            {"source": "factor_pet_resin", "target": "issuer_gross_margin", "relation": "COMPRESSES_MARGIN"},
            {"source": "issuer_gross_margin", "target": "issuer_post_ebitda", "relation": "IMPACTS_EBITDA"},
            {"source": "macro_repo", "target": "issuer_borrowing_cost", "relation": "INCREASES_INTEREST"},
            {"source": "issuer_borrowing_cost", "target": "issuer_post_ebitda", "relation": "EATS_CASHFLOW"}
        ]

        return MacroShockSimulationResult(
            base_crude_usd=base_crude,
            shocked_crude_usd=shocked_crude,
            pet_resin_inflation_pct=pet_inflation_pct,
            gross_margin_compression_bps=gross_margin_compression_bps,
            post_shock_gross_margin_pct=post_gross_margin,
            base_repo_rate_pct=base_repo,
            shocked_repo_rate_pct=shocked_repo,
            incremental_borrowing_cost_cr=incremental_borrowing_cr,
            post_shock_ebitda_margin_pct=post_ebitda_margin,
            relative_multiple_discount_pct=multiple_discount_pct,
            ic_guidance=guidance,
            macro_causal_nodes=causal_nodes,
            macro_causal_edges=causal_edges
        )
