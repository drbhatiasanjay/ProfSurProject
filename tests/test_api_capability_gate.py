import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from fastapi.testclient import TestClient
from api.server import app

client = TestClient(app)

print("--- Testing API Endpoint with Capability Gate ---")

# 1. Health check
res_health = client.get("/health")
assert res_health.status_code == 200, f"Health check failed: {res_health.status_code}"
print("PASS: /health returned 200")

# 2. NTPCGREEN (Priced, Uncontained)
res_ntpc = client.get("/api/pre-ipo/market-status?symbol=NTPCGREEN")
assert res_ntpc.status_code == 200, f"NTPCGREEN failed: {res_ntpc.status_code}"
data_ntpc = res_ntpc.json()
offer_ntpc = data_ntpc.get("offer", {})
pricing_ntpc = offer_ntpc.get("pricingState", {})
print(f"NTPCGREEN pricingState: {pricing_ntpc}")
assert pricing_ntpc.get("status") == "RHP_PRICED", f"Expected RHP_PRICED, got {pricing_ntpc}"
assert pricing_ntpc.get("priceBandMin") == 102
assert pricing_ntpc.get("priceBandMax") == 108
assert pricing_ntpc.get("isContained") is False
print("PASS: NTPCGREEN returned valid RHP_PRICED discriminated union")

# 3. HCCB (Unpriced, Contained)
res_hccb = client.get("/api/pre-ipo/market-status?symbol=HCCB")
assert res_hccb.status_code == 200, f"HCCB failed: {res_hccb.status_code}"
data_hccb = res_hccb.json()
offer_hccb = data_hccb.get("offer", {})
pricing_hccb = offer_hccb.get("pricingState", {})
calib_hccb = data_hccb.get("calibration", {})
scorecard_hccb = data_hccb.get("scorecard", {})
print(f"HCCB pricingState: {pricing_hccb}")
print(f"HCCB calibration metric: {calib_hccb.get('metric')}")
print(f"HCCB composite rating: {scorecard_hccb.get('compositeRating')}")
assert pricing_hccb.get("status") == "DRHP_UNPRICED", f"Expected DRHP_UNPRICED, got {pricing_hccb}"
assert pricing_hccb.get("isContained") is True
assert calib_hccb.get("isUnpricedFailsafe") is True
assert "QUARANTINED" in scorecard_hccb.get("compositeRating")
print("PASS: HCCB properly blocked & quarantined via assert_capability_allowed")

print("--- ALL API CAPABILITY GATE TESTS PASSED FIRST-TIME-RIGHT ---")
