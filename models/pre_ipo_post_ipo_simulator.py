"""
Pre-IPO to Post-IPO Lifecycle Simulator
Milestone 17 (Phase 2D) - Walk-Forward Market Simulation

Models:
1. Anchor Investor Lock-In Expiry Cliff (30-day and 90-day supply expansion)
2. Listing-Day Price Discovery & Retail Flipping Velocity
3. 12-Month Buy-and-Hold Abnormal Return (BHAR) Decay Curve

Governed by:
- docs/SPEC_PRE_IPO_KNOWLEDGE_GRAPH_PHASE2.md
- SEBI ICDR Regulations (Regulation 16 & Anchor Book Building)
- Rule E.3: Zero Python Truthiness
- Rule E.2: Fail-Closed Architecture
"""

from dataclasses import dataclass, asdict
from typing import Dict, List, Any, Optional


@dataclass
class AnchorLockinCliffResult:
    total_offering_shares: int
    anchor_allocation_shares: int
    tranche_30d_shares: int
    tranche_90d_shares: int
    pre_ipo_180d_shares: int
    t30_float_expansion_pct: float
    t90_cumulative_float_expansion_pct: float
    supply_wall_pressure_index: float  # 0 to 100
    expected_price_volatility_pct: float
    institutional_absorption_capacity: str
    cliff_schedule: List[Dict[str, Any]]


@dataclass
class ListingDayDiscoveryResult:
    offer_price_inr: float
    gmp_inr: float
    qib_subscription_multiple: float
    retail_subscription_multiple: float
    estimated_listing_price_inr: float
    estimated_listing_gain_pct: float
    first_120min_retail_flip_shares: int
    flip_velocity_pct_of_retail: float
    order_book_depth_resilience: str


@dataclass
class PostIPOLifecycleResult:
    anchor_cliff: AnchorLockinCliffResult
    listing_discovery: ListingDayDiscoveryResult
    bhar_12m_decay: List[Dict[str, Any]]
    final_verdict: str


class PostIPOSimulator:
    """Simulates post-listing liquidity expansion, price discovery, and BHAR decay."""

    def __init__(self):
        # HCCH Prospectus Ground Truth Parameters
        self.total_offer_shares = 997_500_000
        self.offer_price = 100.0  # Face value ₹10, nominal implied floor
        self.anchor_pool_shares = int(self.total_offer_shares * 0.30)  # 30% anchor quota = 299,250,000
        self.retail_pool_shares = int(self.total_offer_shares * 0.35)  # 35% retail quota = 349,125,000

    def simulate_anchor_cliff(
        self,
        fpi_momentum_share_pct: float = 40.0,
        dii_long_only_share_pct: float = 60.0
    ) -> AnchorLockinCliffResult:
        """
        Calculates supply wall shock at T+30 and T+90 anchor expiry milestones.
        Rule E.3: Zero truthiness preservation.
        """
        if fpi_momentum_share_pct is None:
            fpi_momentum_share_pct = 40.0
        if dii_long_only_share_pct is None:
            dii_long_only_share_pct = 60.0

        t30_shares = int(self.anchor_pool_shares * 0.50)  # 149,625,000 shares
        t90_shares = int(self.anchor_pool_shares * 0.50)  # 149,625,000 shares
        pre_ipo_180d = 125_000_000  # Jubilant & management pre-IPO tranche

        # Initial free float excluding locked anchors: 997.5M - 299.25M = 698.25M
        initial_free_float = self.total_offer_shares - self.anchor_pool_shares
        t30_expansion_pct = round((t30_shares / initial_free_float) * 100, 2)
        t90_cumulative_expansion_pct = round(((t30_shares + t90_shares) / initial_free_float) * 100, 2)

        # Supply pressure index is elevated when FPI momentum hedge funds hold higher share
        supply_pressure = round((fpi_momentum_share_pct / 100.0) * 65.0 + (t30_expansion_pct * 0.8), 1)

        if supply_pressure > 60.0:
            absorption = "FRAGILE: Elevated probability of post-listing supply overhang; expect 4-7% price concession at T+30."
            volatility = 6.5
        else:
            absorption = "ORDERLY: Dominated by domestic mutual funds (DII) with low turnover propensity."
            volatility = 3.2

        schedule = [
            {
                "milestone": "T+0 Listing Day",
                "days": 0,
                "unlocked_shares": initial_free_float,
                "cumulative_float_cr_shares": round(initial_free_float / 10_000_000, 2),
                "event": "QIB Non-Anchor + NII + Retail Active Trading"
            },
            {
                "milestone": "T+30 Days",
                "days": 30,
                "unlocked_shares": t30_shares,
                "cumulative_float_cr_shares": round((initial_free_float + t30_shares) / 10_000_000, 2),
                "event": "50% Anchor Investor Quota Expiry (SEBI ICDR Reg 16)"
            },
            {
                "milestone": "T+90 Days",
                "days": 90,
                "unlocked_shares": t90_shares,
                "cumulative_float_cr_shares": round(self.total_offer_shares / 10_000_000, 2),
                "event": "100% Anchor Investor Quota Unlocked"
            },
            {
                "milestone": "T+180 Days",
                "days": 180,
                "unlocked_shares": pre_ipo_180d,
                "cumulative_float_cr_shares": round((self.total_offer_shares + pre_ipo_180d) / 10_000_000, 2),
                "event": "Pre-IPO Non-Promoter Shareholder Lock-in Expiry"
            }
        ]

        return AnchorLockinCliffResult(
            total_offering_shares=self.total_offer_shares,
            anchor_allocation_shares=self.anchor_pool_shares,
            tranche_30d_shares=t30_shares,
            tranche_90d_shares=t90_shares,
            pre_ipo_180d_shares=pre_ipo_180d,
            t30_float_expansion_pct=t30_expansion_pct,
            t90_cumulative_float_expansion_pct=t90_cumulative_expansion_pct,
            supply_wall_pressure_index=supply_pressure,
            expected_price_volatility_pct=volatility,
            institutional_absorption_capacity=absorption,
            cliff_schedule=schedule
        )

    def simulate_listing_discovery(
        self,
        gmp_inr: float = 22.0,
        qib_multiple: float = 6.04,
        retail_multiple: float = 1.14
    ) -> ListingDayDiscoveryResult:
        """Simulates listing gain and Day 1 retail flipping velocity."""
        if gmp_inr is None:
            gmp_inr = 0.0
        if qib_multiple is None:
            qib_multiple = 1.0
        if retail_multiple is None:
            retail_multiple = 1.0

        est_price = round(self.offer_price + gmp_inr, 2)
        listing_gain_pct = round((gmp_inr / self.offer_price) * 100, 2)

        # High retail listing gains trigger heavy day-1 flipping
        flip_pct = min(85.0, max(25.0, 35.0 + (listing_gain_pct * 0.8)))
        flip_shares = int(self.retail_pool_shares * (flip_pct / 100.0))

        resilience = "DEEP" if qib_multiple >= 5.0 else ("MODERATE" if qib_multiple >= 2.0 else "SHALLOW")

        return ListingDayDiscoveryResult(
            offer_price_inr=self.offer_price,
            gmp_inr=gmp_inr,
            qib_subscription_multiple=qib_multiple,
            retail_subscription_multiple=retail_multiple,
            estimated_listing_price_inr=est_price,
            estimated_listing_gain_pct=listing_gain_pct,
            first_120min_retail_flip_shares=flip_shares,
            flip_velocity_pct_of_retail=round(flip_pct, 1),
            order_book_depth_resilience=resilience
        )

    def generate_bhar_decay(self, shock_active: bool = False) -> List[Dict[str, Any]]:
        """
        Generates 12-month Buy-and-Hold Abnormal Return (BHAR) trajectory.
        Compares base case vs risk crystallization case (e.g. CESTAT or royalty hike).
        """
        months = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12]
        trajectory = []

        for m in months:
            # Baseline FMCG compounder growth relative to Nifty 50
            base_alpha = round(2.5 + (m * 0.8), 2)

            # If contingent risk emerges (e.g. tax loss or raw material surge), multiple contracts
            if shock_active:
                decay_alpha = round(base_alpha - (m * 1.6) - (4.0 if m >= 3 else 0.0), 2)
            else:
                decay_alpha = base_alpha

            trajectory.append({
                "month": f"M{m}",
                "month_num": m,
                "base_alpha_pct": base_alpha,
                "stressed_alpha_pct": decay_alpha,
                "event_marker": "Anchor T+30" if m == 1 else ("Anchor T+90" if m == 3 else ("Pre-IPO T+180" if m == 6 else ""))
            })

        return trajectory

    def full_simulation(
        self,
        gmp_inr: float = 22.0,
        qib_multiple: float = 6.04,
        fpi_momentum_pct: float = 40.0,
        shock_active: bool = False
    ) -> PostIPOLifecycleResult:
        """Orchestrates comprehensive post-IPO walk-forward simulation."""
        anchor_cliff = self.simulate_anchor_cliff(fpi_momentum_share_pct=fpi_momentum_pct)
        listing = self.simulate_listing_discovery(gmp_inr=gmp_inr, qib_multiple=qib_multiple)
        bhar = self.generate_bhar_decay(shock_active=shock_active)

        verdict = (
            f"Listing Day 1 displays strong institutional backing ({listing.order_book_depth_resilience} QIB book, "
            f"+{listing.estimated_listing_gain_pct}% est. gain). Key institutional risk point is the T+30 day Anchor cliff "
            f"where {anchor_cliff.t30_float_expansion_pct}% float expansion will test secondary market depth."
        )

        return PostIPOLifecycleResult(
            anchor_cliff=anchor_cliff,
            listing_discovery=listing,
            bhar_12m_decay=bhar,
            final_verdict=verdict
        )
