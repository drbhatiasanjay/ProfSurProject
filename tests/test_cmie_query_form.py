import pytest

from cmie.errors import CmieParseError
from cmie.query_form import cmie_tabular_json_to_dataframe


def test_cmie_tabular_json_list_rows():
    obj = {"head": ["a", "b"], "data": [[1, 2], [3, 4]]}
    df = cmie_tabular_json_to_dataframe(obj)
    assert list(df.columns) == ["a", "b"]
    assert len(df) == 2
    assert df.iloc[0]["a"] == 1


def test_cmie_tabular_json_dict_rows():
    obj = {"head": ["x"], "data": [{"x": 5}, {"x": 6}]}
    df = cmie_tabular_json_to_dataframe(obj)
    assert len(df) == 2
    assert df.iloc[1]["x"] == 6


def test_cmie_tabular_json_missing():
    with pytest.raises(CmieParseError):
        cmie_tabular_json_to_dataframe({"foo": 1})


def test_cmie_tabular_empty_data():
    obj = {"head": ["a"], "data": []}
    df = cmie_tabular_json_to_dataframe(obj)
    assert len(df) == 0
    assert list(df.columns) == ["a"]
