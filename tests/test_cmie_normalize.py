import pandas as pd
import pytest

from cmie.normalize import normalize_panel_like, validate_panel
from cmie.errors import CmieSchemaError, CmieValidationError


def test_normalize_requires_entity_time():
    df = pd.DataFrame({"x": [1], "y": [2]})
    with pytest.raises(CmieSchemaError):
        normalize_panel_like(df)


def test_validate_panel_min_years():
    df = pd.DataFrame(
        {
            "company_code": [1, 1],
            "year": [2020, 2021],
            "leverage": [10.0, 11.0],
            "firm_size": [100, 110],
        }
    )
    panel, _ = normalize_panel_like(df)
    with pytest.raises(CmieValidationError):
        validate_panel(panel, min_years=3)

