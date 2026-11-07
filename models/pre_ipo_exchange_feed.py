from datetime import date, datetime, timedelta, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from urllib.parse import urlparse

class ExchangeListingStatus(str, Enum):
    UPCOMING_ISSUE = "UPCOMING_ISSUE"
    BIDDING_OPEN = "BIDDING_OPEN"
    ALLOTMENT_FINALIZED = "ALLOTMENT_FINALIZED"
    LISTED = "LISTED"
    WITHDRAWN = "WITHDRAWN"

class ExchangeLockinRecord(BaseModel):
    symbol: str
    exchange: str = "NSE"
    company_name: str
    isin: str
    issue_price_inr: float
    listing_date: date
    anchor_portion_shares: int
    anchor_portion_cr: float
    day_30_lockin_date: date
    day_30_lockin_shares: int
    day_90_lockin_date: date
    day_90_lockin_shares: int
    status: ExchangeListingStatus = ExchangeListingStatus.LISTED
    circular_ref: str
    circular_date: date
    source_feed: str = "LOCAL_UNVERIFIED_EXAMPLE"
    source_url: Optional[str] = None
    reviewed: bool = False

# Local examples only. No network provider is implemented by this registry.
EXCHANGE_FEED_REGISTRY: Dict[str, ExchangeLockinRecord] = {
    "ntpc_green": ExchangeLockinRecord(
        symbol="NTPCGREEN",
        exchange="NSE",
        company_name="NTPC Green Energy Limited",
        isin="INE000001010",
        issue_price_inr=108.0,
        listing_date=date(2024, 11, 27),
        anchor_portion_shares=366666666,
        anchor_portion_cr=3960.0,
        day_30_lockin_date=date(2024, 12, 27),
        day_30_lockin_shares=183333333,
        day_90_lockin_date=date(2025, 2, 25),
        day_90_lockin_shares=183333333,
        status=ExchangeListingStatus.LISTED,
        circular_ref="NSE/CML/2024/65201",
        circular_date=date(2024, 11, 26),
    ),
    "swiggy": ExchangeLockinRecord(
        symbol="SWIGGY",
        exchange="NSE",
        company_name="Swiggy Limited",
        isin="INE000001011",
        issue_price_inr=390.0,
        listing_date=date(2024, 11, 13),
        anchor_portion_shares=130384615,
        anchor_portion_cr=5085.0,
        day_30_lockin_date=date(2024, 12, 13),
        day_30_lockin_shares=65192307,
        day_90_lockin_date=date(2025, 2, 11),
        day_90_lockin_shares=65192308,
        status=ExchangeListingStatus.LISTED,
        circular_ref="NSE/CML/2024/64102",
        circular_date=date(2024, 11, 12),
    ),
    "afcons_infra": ExchangeLockinRecord(
        symbol="AFCONS",
        exchange="NSE",
        company_name="Afcons Infrastructure Limited",
        isin="INE000001012",
        issue_price_inr=463.0,
        listing_date=date(2024, 11, 4),
        anchor_portion_shares=35000000,
        anchor_portion_cr=1620.0,
        day_30_lockin_date=date(2024, 12, 4),
        day_30_lockin_shares=17500000,
        day_90_lockin_date=date(2025, 2, 2),
        day_90_lockin_shares=17500000,
        status=ExchangeListingStatus.LISTED,
        circular_ref="NSE/CML/2024/63890",
        circular_date=date(2024, 11, 3),
    ),
    "tata_technologies": ExchangeLockinRecord(
        symbol="TATATECH",
        exchange="NSE",
        company_name="Tata Technologies Limited",
        isin="INE142M01025",
        issue_price_inr=500.0,
        listing_date=date(2023, 11, 30),
        anchor_portion_shares=15821071,
        anchor_portion_cr=791.05,
        day_30_lockin_date=date(2023, 12, 30),
        day_30_lockin_shares=7910535,
        day_90_lockin_date=date(2024, 2, 28),
        day_90_lockin_shares=7910536,
        status=ExchangeListingStatus.LISTED,
        circular_ref="NSE/CML/2023/59512",
        circular_date=date(2023, 11, 29),
    ),
    "mankind_pharma": ExchangeLockinRecord(
        symbol="MANKIND",
        exchange="NSE",
        company_name="Mankind Pharma Limited",
        isin="INE634S01028",
        issue_price_inr=1080.0,
        listing_date=date(2023, 5, 9),
        anchor_portion_shares=12018518,
        anchor_portion_cr=1298.0,
        day_30_lockin_date=date(2023, 6, 8),
        day_30_lockin_shares=6009259,
        day_90_lockin_date=date(2023, 8, 7),
        day_90_lockin_shares=6009259,
        status=ExchangeListingStatus.LISTED,
        circular_ref="NSE/CML/2023/56610",
        circular_date=date(2023, 5, 8),
    ),
}

class ExchangeFeedClient:
    """Inspect local records; reconcile only explicitly reviewed official circulars."""

    @classmethod
    def get_lockin_record(cls, query: str) -> Optional[ExchangeLockinRecord]:
        q_norm = query.lower().replace(" ", "").replace("_", "").replace("-", "")
        if not q_norm:
            return None
        for k, v in EXCHANGE_FEED_REGISTRY.items():
            k_norm = k.replace("_", "")
            comp_norm = v.company_name.lower().replace(" ", "").replace("_", "").replace("-", "")
            sym_norm = v.symbol.lower()
            if q_norm in {k_norm, comp_norm, sym_norm}:
                return v
        return None

    @classmethod
    def reconcile_with_prospectus(
        cls,
        prospectus_listing_date: Optional[str],
        company_name: str,
    ) -> Dict[str, Any]:
        """
        Reconciles the prospectus-projected listing date against official exchange listing circulars.
        Computes calendar drift, updates statutory Day 30 and Day 90 lock-in dates, and cites circulars.
        """
        rec = cls.get_lockin_record(company_name)
        parsed = urlparse(rec.source_url or "") if rec else None
        official_host = bool(parsed and parsed.scheme == "https" and any(
            parsed.hostname == host or (parsed.hostname or "").endswith("." + host)
            for host in ("nseindia.com", "bseindia.com")))
        if not rec or not rec.reviewed or not official_host:
            return {
                "is_reconciled": False,
                "live_connection": False,
                "source_status": "UNVERIFIED_LOCAL_RECORD" if rec else "NOT_CONNECTED",
                "exchange_symbol": "UNLISTED",
                "exchange": "NSE/BSE",
                "circular_ref": "PENDING_EXCHANGE_CIRCULAR",
                "exchange_listing_date": None,
                "drift_days": 0,
                "drift_status": "CIRCULAR_PENDING_ALLOTMENT",
                "day_30_lockin_date": None,
                "day_90_lockin_date": None,
                "notes": "Live exchange feed is not connected. Local examples are unverified; using the prospectus estimate until an official circular is reviewed.",
            }

        # Check drift if prospectus date was supplied
        prosp_dt = None
        if prospectus_listing_date and "-" in prospectus_listing_date:
            try:
                prosp_dt = datetime.strptime(prospectus_listing_date[:10], "%Y-%m-%d").date()
            except Exception:
                prosp_dt = None

        drift_days = 0
        drift_status = "EXACT_MATCH"
        if prosp_dt:
            drift_days = (rec.listing_date - prosp_dt).days
            if drift_days != 0:
                drift_status = "SCHEDULE_SHIFTED_BY_EXCHANGE"

        return {
            "is_reconciled": True,
            "live_connection": False,
            "source_status": "REVIEWED_LOCAL_CIRCULAR",
            "source_url": rec.source_url,
            "exchange_symbol": rec.symbol,
            "exchange": rec.exchange,
            "isin": rec.isin,
            "issue_price_inr": rec.issue_price_inr,
            "circular_ref": rec.circular_ref,
            "circular_date": rec.circular_date.isoformat(),
            "exchange_listing_date": rec.listing_date.isoformat(),
            "drift_days": drift_days,
            "drift_status": drift_status,
            "day_30_lockin_date": rec.day_30_lockin_date.isoformat(),
            "day_30_lockin_shares": rec.day_30_lockin_shares,
            "day_90_lockin_date": rec.day_90_lockin_date.isoformat(),
            "day_90_lockin_shares": rec.day_90_lockin_shares,
            "notes": (
                f"Reconciled against {rec.exchange} Circular {rec.circular_ref}. "
                f"Listing date confirmed as {rec.listing_date.isoformat()}"
                + (f" (drift: {drift_days:+d} days vs prospectus draft)." if drift_days != 0 else ".")
            ),
        }
