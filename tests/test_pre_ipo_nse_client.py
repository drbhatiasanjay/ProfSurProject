# -*- coding: utf-8 -*-
"""
Unit and Integration Tests for NSE India Live Client
Module: tests/test_pre_ipo_nse_client.py
"""

from unittest.mock import MagicMock, patch
import pytest
from models.pre_ipo_nse_client import (
    NSELiveClient,
    IPOSubscriptionBreakdown,
    StatutoryIssueMetadata,
    PeerMarketQuote,
)


@pytest.fixture
def mock_nse_session():
    """Mock requests.Session for deterministic fast tests."""
    session = MagicMock()
    session.cookies = {"_abck": "mock_abck_cookie", "nsit": "mock_nsit_cookie"}
    return session


def test_nse_client_initialization():
    client = NSELiveClient(session_ttl_seconds=600, request_timeout_seconds=15)
    assert client.session_ttl == 600
    assert client.request_timeout == 15
    assert "User-Agent" in client.session.headers
    assert "Accept" in client.session.headers


def test_parse_ipo_detail_payload():
    client = NSELiveClient(enable_fallback=False)
    sample_payload = {
        "companyName": "NTPC Green Energy Limited",
        "metaInfo": {
            "symbol": "NTPCGREEN",
            "companyName": "NTPC Green Energy Limited",
            "industry": "Power Generation",
            "isin": "INE0ONG01011",
            "listingDate": "2024-11-27",
            "segment": "EQUITY",
        },
        "issueInfo": {
            "dataList": [
                {"title": "Symbol", "value": "NTPCGREEN"},
                {"title": "Issue Period", "value": "19-Nov-2024 to 22-Nov-2024"},
                {"title": "Issue Size", "value": "Fresh Issue of up to Rs. 100,000 million"},
                {"title": "Price Range", "value": "Rs. 102 to Rs. 108 per Equity Share"},
                {"title": "Bid Lot", "value": "138 Equity Shares and in multiples thereof"},
                {"title": "Book Running Lead Managers", "value": "IDBI Capital, HDFC Bank, IIFL Capital"},
                {"title": "Name of the Registrar", "value": "KFin Technologies Limited"},
                {"title": "Red Herring Prospectus", "value": "https://nsearchives.nseindia.com/content/ipo/RHP_NTPCGREEN.zip"},
                {"title": "Anchor Allocation Report", "value": "https://nsearchives.nseindia.com/content/ipo/ANCHOR_NTPCGREEN.zip"},
            ]
        },
        "bidDetails": [
            {
                "category": "Qualified Institutional Buyers(QIBs)",
                "noOfSharesOffered": "258823531",
                "noOfTime": "2.3567",
                "noOfsharesBid": "609979044",
            },
            {
                "category": "Non Institutional Investors(NIIs)",
                "noOfSharesOffered": "129411765",
                "noOfTime": "0.845",
                "noOfsharesBid": "109352941",
            },
            {
                "category": "Retail Individual Investors(RIIs)",
                "noOfSharesOffered": "86274510",
                "noOfTime": "1.52",
                "noOfsharesBid": "131137255",
            },
        ],
    }

    result = client._parse_ipo_detail_payload("NTPCGREEN", sample_payload)
    assert isinstance(result, StatutoryIssueMetadata)
    assert result.symbol == "NTPCGREEN"
    assert result.company_name == "NTPC Green Energy Limited"
    assert result.industry == "Power Generation"
    assert result.price_band_lower == 102.0
    assert result.price_band_upper == 108.0
    assert result.bid_lot == 138
    assert len(result.lead_managers) == 3
    assert result.rhp_download_url == "https://nsearchives.nseindia.com/content/ipo/RHP_NTPCGREEN.zip"
    assert result.anchor_report_url == "https://nsearchives.nseindia.com/content/ipo/ANCHOR_NTPCGREEN.zip"

    # Test Subscription
    assert result.subscription is not None
    assert result.subscription.qib_multiple == 2.3567
    assert result.subscription.qib_shares_bid == 609979044
    assert result.subscription.retail_multiple == 1.52
    assert result.subscription.total_multiple > 1.0


def test_parse_ipo_detail_single_price_cutoff():
    client = NSELiveClient(enable_fallback=False)
    payload = {
        "metaInfo": {"symbol": "FIXED_PRICE_CO"},
        "issueInfo": {
            "dataList": [
                {"title": "Price Range", "value": "Rs. 250 per Equity Share"},
                {"title": "Bid Lot", "value": "50 Equity Shares"},
            ]
        },
        "bidDetails": [],
    }
    result = client._parse_ipo_detail_payload("FIXED_PRICE_CO", payload)
    assert result.price_band_lower == 250.0
    assert result.price_band_upper == 250.0
    assert result.bid_lot == 50


def test_deterministic_fallbacks():
    client = NSELiveClient(enable_fallback=True)

    # Test Fallback Indices
    indices = client._get_fallback_indices()
    assert "NIFTY 50" in indices
    assert "INDIA VIX" in indices
    assert indices["NIFTY 50"]["last"] > 0

    # Test Fallback IPO Detail
    ipo = client._get_fallback_ipo_detail("HCCB")
    assert ipo.symbol == "HCCB"
    assert ipo.price_band_lower == 425.0
    assert ipo.price_band_upper == 450.0
    assert ipo.is_live_data is False

    # Test Fallback Peers
    peers = client._get_fallback_peers("NIFTY FMCG")
    assert len(peers) == 5
    symbols = [p.symbol for p in peers]
    assert "VBL" in symbols
    assert "HINDUNILVR" in symbols


def test_peer_group_quotes_aggregation():
    client = NSELiveClient(enable_fallback=True)
    # Mock constituents
    mock_fmcg = [
        PeerMarketQuote("VBL", 432.8, -0.5, 555.0, 380.0, 1000.0, "NIFTY FMCG", "2026-11-15T00:00:00"),
        PeerMarketQuote("HINDUNILVR", 1992.9, 0.9, 2488.0, 1758.0, 2000.0, "NIFTY FMCG", "2026-11-15T00:00:00"),
    ]
    with patch.object(client, "get_index_constituents", return_value=mock_fmcg):
        quotes = client.get_peer_group_quotes(["VBL", "HINDUNILVR"])
        assert len(quotes) == 2
        assert quotes["VBL"].last_price == 432.8
        assert quotes["HINDUNILVR"].last_price == 1992.9
