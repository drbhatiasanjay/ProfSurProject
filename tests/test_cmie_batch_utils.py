import json
import pytest

from cmie.batch_utils import json_payload_for_company, parse_company_codes


def test_parse_company_codes_order_and_dedupe():
    assert parse_company_codes("3, 1, 3\n2") == [3, 1, 2]


def test_parse_company_codes_max():
    s = ",".join(str(i) for i in range(12))
    with pytest.raises(ValueError, match="At most"):
        parse_company_codes(s)


def test_json_payload_substitution():
    t = '{"scheme":"MITS","co":"__CMIE_COMPANY_CODE__"}'
    out = json_payload_for_company(t, 99)
    assert out["co"] == "99"
    assert out["scheme"] == "MITS"


def test_json_payload_numeric_placeholder():
    t = '{"scheme":"MITS","co":__CMIE_COMPANY_CODE__}'
    out = json_payload_for_company(t, 99)
    assert out["co"] == 99


def test_json_payload_missing_placeholder():
    with pytest.raises(ValueError, match="Batch mode requires"):
        json_payload_for_company("{}", 1)
