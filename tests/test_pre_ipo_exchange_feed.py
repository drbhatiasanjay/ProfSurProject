from datetime import date
import pytest
from models.pre_ipo_exchange_feed import ExchangeFeedClient, ExchangeListingStatus
from models.pre_ipo_engine import generate_anchor_lockin_calendar
from models.pre_ipo_ingest import PRE_IPO_REGISTRY

@pytest.fixture
def reviewed_record(monkeypatch):
    # Synthetic reviewed-import fixture, not a fetched exchange circular.
    record = ExchangeFeedClient.get_lockin_record("NTPCGREEN").model_copy(update={
        "reviewed": True, "source_url": "https://www.nseindia.com/circulars/test-fixture.pdf",
    })
    monkeypatch.setattr(ExchangeFeedClient, "get_lockin_record", classmethod(lambda cls, query: record))
    return record

def test_exchange_feed_record_lookup():
    rec = ExchangeFeedClient.get_lockin_record("NTPC Green Energy Limited")
    assert rec is not None
    assert rec.symbol == "NTPCGREEN"
    assert rec.exchange == "NSE"
    assert rec.circular_ref == "NSE/CML/2024/65201"
    assert rec.anchor_portion_cr == 3960.0

def test_exchange_feed_reconciliation_exact_and_drift(reviewed_record):
    # Exact match test (prospectus date matches official exchange circular)
    res_exact = ExchangeFeedClient.reconcile_with_prospectus(
        prospectus_listing_date="2024-11-27",
        company_name="NTPC Green Energy Limited",
    )
    assert res_exact["is_reconciled"] is True
    assert res_exact["drift_days"] == 0
    assert res_exact["drift_status"] == "EXACT_MATCH"
    assert res_exact["exchange_symbol"] == "NTPCGREEN"

    # Schedule shifted drift test (prospectus estimated 2024-11-25, actual listed 2024-11-27 -> +2 days)
    res_drift = ExchangeFeedClient.reconcile_with_prospectus(
        prospectus_listing_date="2024-11-25",
        company_name="NTPC Green Energy Limited",
    )
    assert res_drift["is_reconciled"] is True
    assert res_drift["drift_days"] == 2
    assert res_drift["drift_status"] == "SCHEDULE_SHIFTED_BY_EXCHANGE"
    assert "drift: +2 days" in res_drift["notes"]

def test_exchange_feed_unknown_issuer_pending():
    res_unknown = ExchangeFeedClient.reconcile_with_prospectus(
        prospectus_listing_date="2025-06-01",
        company_name="Unknown Unlisted Stealth Startup Ltd",
    )
    assert res_unknown["is_reconciled"] is False
    assert res_unknown["drift_status"] == "CIRCULAR_PENDING_ALLOTMENT"
    assert res_unknown["circular_ref"] == "PENDING_EXCHANGE_CIRCULAR"

def test_anchor_lockin_calendar_incorporates_exchange_circular(reviewed_record):
    dossier = PRE_IPO_REGISTRY["ntpc_green"]
    calendar = generate_anchor_lockin_calendar(dossier, as_of_date=date(2024, 11, 28))

    assert len(calendar) == 4
    # Check that official NSE circular reference is cited in the milestone
    t0_milestone = calendar[0]
    assert "NSE/CML/2024/65201" in t0_milestone.exchange_notice_ref

    t30_milestone = calendar[1]
    assert "NSE/CML/2024/65201" in t30_milestone.exchange_notice_ref


def test_local_registry_is_never_a_live_verified_feed():
    result = ExchangeFeedClient.reconcile_with_prospectus("2024-11-27", "NTPC Green Energy Limited")
    assert result["is_reconciled"] is False
    assert result["live_connection"] is False
    assert result["source_status"] == "UNVERIFIED_LOCAL_RECORD"
    assert result["exchange_listing_date"] is None
    assert ExchangeFeedClient.get_lockin_record("") is None
    assert ExchangeFeedClient.get_lockin_record("green") is None


def test_reviewed_flag_cannot_authorize_nonofficial_source(monkeypatch):
    record = ExchangeFeedClient.get_lockin_record("NTPCGREEN").model_copy(update={
        "reviewed": True, "source_url": "https://nseindia.com.example.org/fake.pdf",
    })
    monkeypatch.setattr(ExchangeFeedClient, "get_lockin_record", classmethod(lambda cls, query: record))
    assert ExchangeFeedClient.reconcile_with_prospectus("2024-11-27", "NTPCGREEN")["is_reconciled"] is False
