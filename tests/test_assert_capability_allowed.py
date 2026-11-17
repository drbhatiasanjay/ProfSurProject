import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from models.pre_ipo_capability_gate import (
    assert_capability_allowed,
    CapabilityType,
    ExportBlockedError
)

print("--- Testing assert_capability_allowed ---")

# 1. Clean accepted RHP deal
deal_rhp = {
    "symbol": "NTPCGREEN",
    "companyName": "NTPC Green Energy Limited",
    "pricingState": {
        "status": "RHP_PRICED",
        "priceBandMin": 102,
        "priceBandMax": 108,
        "isContained": False
    },
    "origin": "SEED",
    "snapshot_status": "ACCEPTED_FOR_ANALYSIS",
    "isContained": False
}
assert_capability_allowed(deal_rhp, CapabilityType.VALUATION)
print("PASS 1: Clean RHP deal allowed for valuation")

# 2. Ingested deal without accepted snapshot
deal_ingested_unreviewed = {
    "symbol": "NEWDEAL",
    "companyName": "New Tech Ltd",
    "origin": "INGESTED",
    "snapshot_status": "RAW_EXTRACTION",
    "pricingState": {
        "status": "RHP_PRICED",
        "priceBandMin": 200,
        "priceBandMax": 210,
        "isContained": False
    }
}
try:
    assert_capability_allowed(deal_ingested_unreviewed, CapabilityType.VALUATION)
    raise AssertionError("FAIL: Ingested unreviewed should have raised ExportBlockedError")
except ExportBlockedError as e:
    print(f"PASS 2: Ingested unreviewed properly blocked: {e}")

# 3. Contained deal (is_contained == True)
deal_contained = {
    "symbol": "TESTCO",
    "companyName": "Test Corp",
    "pricingState": {
        "status": "RHP_PRICED",
        "priceBandMin": 100,
        "priceBandMax": 105,
        "isContained": True
    },
    "isContained": True
}
try:
    assert_capability_allowed(deal_contained, CapabilityType.VALUATION)
    raise AssertionError("FAIL: Contained deal should have raised ExportBlockedError")
except ExportBlockedError as e:
    print(f"PASS 3: Contained deal properly blocked: {e}")

# 4. Unpriced deal (DRHP_UNPRICED)
deal_unpriced = {
    "symbol": "HCCB",
    "companyName": "Hindustan Coca-Cola",
    "pricingState": {
        "status": "DRHP_UNPRICED",
        "isContained": True
    }
}
try:
    assert_capability_allowed(deal_unpriced, CapabilityType.VALUATION)
    raise AssertionError("FAIL: Unpriced deal should have raised ExportBlockedError")
except ExportBlockedError as e:
    print(f"PASS 4: Unpriced deal properly blocked: {e}")

# 5. Recommendation ban (P0-08)
try:
    assert_capability_allowed(deal_rhp, CapabilityType.RECOMMENDATIONS)
    raise AssertionError("FAIL: RECOMMENDATIONS capability should have raised ExportBlockedError")
except ExportBlockedError as e:
    print(f"PASS 5: Recommendations properly blocked under P0-08: {e}")

print("--- ALL 5 CAPABILITY GATE TESTS PASSED FIRST-TIME-RIGHT ---")
