"""
Test suite for ProfSur Quantitative Pre-IPO Intelligence FastAPI server.
"""

from fastapi.testclient import TestClient
from api.server import app

client = TestClient(app)

def test_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "timestamp" in data

def test_market_status_endpoint_ntpcgreen():
    response = client.get("/api/pre-ipo/market-status?symbol=NTPCGREEN")
    assert response.status_code == 200
    payload = response.json()

    # Core required schema keys
    for key in ["indices", "offer", "subscription", "peers", "calibration", "scorecard", "compliance"]:
        assert key in payload, f"Missing key {key} in market status payload"

    # Indices check
    indices = payload["indices"]
    assert len(indices) >= 3
    symbols = [idx["symbol"] for idx in indices]
    assert "NIFTY 50" in symbols
    assert "INDIA VIX" in symbols

    # Offer check
    offer = payload["offer"]
    assert offer["symbol"] == "NTPCGREEN"
    assert offer["priceBandMin"] == 102
    assert offer["priceBandMax"] == 108
    assert offer["lotSize"] == 138
    assert offer["issueSizeCr"] == 10000.00
    assert offer["freshIssueCr"] == 10000.00
    assert offer["ofsCr"] == 0.00

    # Subscription check
    sub = payload["subscription"]
    assert sub["totalMultiple"] > 0
    assert len(sub["categories"]) == 4

    # Calibration check (dynamic econometric outputs)
    calib = payload["calibration"]
    assert calib["declaredPeerMedian"] > 0
    assert calib["warrantedFairMultiple"] > 0
    assert calib["drhpBiasIndex"] > 0
    assert "narrative" in calib
    assert "the_problem" in calib["narrative"]
    assert "econometric_findings" in calib["narrative"]

    # ML Scorecard check
    sc = payload["scorecard"]
    assert sc["fundamentalScore"] > 0
    assert sc["compositeRating"] in ["SUBSCRIBE_LONG_TERM", "SUBSCRIBE_LISTING_POP_ONLY", "AVOID_HIGH_DRAWDOWN_RISK"]
    assert len(sc["shapTopFeatures"]) == 5

    # SEBI Compliance check
    comp = payload["compliance"]
    assert len(comp["immutableReportHashSha256"]) == 64
