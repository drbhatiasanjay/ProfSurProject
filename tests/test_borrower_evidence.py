from copy import deepcopy
from hashlib import sha256

import pytest
from models.borrower_evidence import validate_packet


@pytest.fixture
def complete_packet(tmp_path):
    # Synthetic engineering fixture only; never represents actual borrower data.
    documents = []
    for kind in ("financial_statement", "facility_terms", "debt_schedule", "lease_schedule",
                 "cash_flow_forecast", "net_worth_bridge"):
        content = f"Synthetic test {kind}".encode()
        (tmp_path / kind).write_bytes(content)
        documents.append({"id": kind, "kind": kind, "file": kind,
                          "sha256": sha256(content).hexdigest(), "entity_id": "TEST",
                          "perimeter": "standalone", "as_of": "2026-09-30"})
    def ref(kind, evidence="observed"):
        return {"document_id": kind, "locator": "test clause 1", "evidence_kind": evidence}
    periods = ["2026-12-31", "2027-03-31"]
    packet = {"schema_version": 1, "borrower": {"legal_name": "Synthetic test borrower",
              "entity_id": "TEST", "perimeter": "standalone", "as_of": "2026-09-30",
              "currency": "INR", "unit": "crore"}, "period_ends": periods, "documents": documents,
              "inputs": {key: {"value": value, **ref("net_worth_bridge" if key == "tangible_net_worth_cr" else "financial_statement")}
                         for key, value in {"opening_cash_cr": 5, "debt_excluding_leases_cr": 100,
                         "lease_liability_cr": 20, "tangible_net_worth_cr": 50, "other_liabilities_cr": 10}.items()},
              "cash_flow_forecast": [{"end": end, "earnings_basis": "EBITDA", "earnings_cr": 30,
                  "cash_taxes_cr": 2, "maintenance_capex_cr": 3, "working_capital_use_cr": -1,
                  **ref("cash_flow_forecast", "approved_forecast")} for end in periods],
              "covenants": [{"facility_id": "LOAN", "metric": "DSCR", "definition_text": "Synthetic clause",
                  "numerator": "Contract CFADS", "denominator": "Contract debt service", "threshold": 1.2,
                  "operator": ">=", "testing_basis": "rolling 12 months", "lease_treatment": "include",
                  "cash_sweep": "none per synthetic clause", "effective_from": "2026-09-30", **ref("facility_terms")}]}
    for collection, kind, balance, key in (("loans", "debt_schedule", 100, "LOAN"), ("leases", "lease_schedule", 20, "LEASE")):
        packet[collection] = [{"facility_id": key, "opening_balance_cr": balance, **ref(kind),
                              "periods": [{"end": end, "drawdown_cr": 0, "principal_cr": 5,
                                           "interest_cr": 2, "other_cash_cr": 0} for end in periods]}]
    return packet, tmp_path


def test_complete_packet_is_only_ready_for_review_and_never_executes(complete_packet):
    packet, directory = complete_packet
    before = deepcopy(packet)
    result = validate_packet(packet, directory)
    assert result["status"] == "READY_FOR_PROFESSIONAL_REVIEW"
    assert result["validation_status"] == "NOT_VALIDATED"
    assert not result["contractual_calculation_enabled"]
    assert packet == before


def test_standard_uppercase_sha256_is_accepted(complete_packet):
    packet, directory = complete_packet
    for document in packet["documents"]:
        document["sha256"] = document["sha256"].upper()
    assert validate_packet(packet, directory)["status"] == "READY_FOR_PROFESSIONAL_REVIEW"


@pytest.mark.parametrize("change,code", [
    (lambda p: p["inputs"]["opening_cash_cr"].update(value=None), "INPUT_VALUE"),
    (lambda p: p["inputs"]["opening_cash_cr"].update(evidence_kind="assumption"), "ASSUMPTION"),
    (lambda p: p["documents"][0].update(sha256="bad"), "EVIDENCE_FILE"),
    (lambda p: p["documents"][0].update(perimeter="consolidated"), "EVIDENCE_FILE"),
    (lambda p: p["loans"][0].update(opening_balance_cr=99), "BALANCE_RECONCILIATION"),
    (lambda p: p["loans"][0]["periods"][0].update(principal_cr=101), "OVERPAYMENT"),
    (lambda p: p.update(covenants=[]), "MISSING_TERMS"),
    (lambda p: p["covenants"][0].update(numerator=None), "TERM_DEFINITION"),
    (lambda p: p["covenants"][0].update(facility_id="UNKNOWN"), "TERM_FACILITY"),
    (lambda p: p["loans"][0]["periods"].reverse(), "SCHEDULE_PERIODS"),
    (lambda p: p["inputs"]["opening_cash_cr"].update(value=True), "INPUT_VALUE"),
    (lambda p: p["borrower"].update(unit="million"), "UNITS"),
])
def test_incomplete_or_inconsistent_evidence_fails_closed(complete_packet, change, code):
    packet, directory = complete_packet
    change(packet)
    result = validate_packet(packet, directory)
    assert result["status"] == "NEEDS_EVIDENCE"
    assert code in {issue["code"] for issue in result["issues"]}


def test_evidence_path_cannot_escape_supplied_directory(complete_packet, tmp_path):
    packet, directory = complete_packet
    packet["documents"][0]["file"] = "../outside.txt"
    result = validate_packet(packet, directory)
    assert result["status"] == "NEEDS_EVIDENCE"
    assert any("inside evidence directory" in i["message"] for i in result["issues"])


def test_missing_is_not_zero_and_explicit_zero_leases_is_supported(complete_packet):
    packet, directory = complete_packet
    packet["inputs"]["lease_liability_cr"]["value"] = 0
    packet["leases"] = []
    packet["documents"] = [d for d in packet["documents"] if d["kind"] != "lease_schedule"]
    assert validate_packet(packet, directory)["status"] == "READY_FOR_PROFESSIONAL_REVIEW"
    packet["inputs"]["lease_liability_cr"]["value"] = None
    assert validate_packet(packet, directory)["status"] == "NEEDS_EVIDENCE"


def test_chat_routes_intake_and_cancel_without_running_finance_engine():
    from models.covenant_chat import handle_query
    opened = handle_query("validate borrower")
    assert opened["state"]["borrower_intake_requested"]
    assert "result" not in opened
    closed = handle_query("cancel borrower validation", opened["state"])
    assert not closed["state"].get("borrower_intake_requested")


def test_chat_intake_is_scoped_and_feature_gated(monkeypatch):
    from components.covenant_pilot_chat import route, conversation_state
    monkeypatch.setenv("ENABLE_COVENANT_PILOT", "1")
    turn = route("validate actual borrower", [], "owner:chat1:thesis")
    assert conversation_state([turn], "owner:chat1:thesis")["borrower_intake_requested"]
    assert conversation_state([turn], "other:chat2:thesis") == {}
    monkeypatch.delenv("ENABLE_COVENANT_PILOT")
    assert route("validate borrower", [], "owner:chat1:thesis") is None
