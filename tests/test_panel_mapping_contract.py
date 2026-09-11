from pathlib import Path

import db


EXPECTED_PROFILES = {"drbhatia", "profsurkumar", "skumar", "sbhatia"}


def test_filter_scope_round_trips_without_losing_panel_dimensions():
    filters = {
        "panel_mode": "thesis",
        "year_range": (2001, 2005),
        "company_codes": [101, 202],
        "life_stages": ["Growth"],
        "industry_groups": ["Telecommunication services"],
        "events": {"gfc": True, "ibc": False, "covid": True},
    }
    restored = db._deserialize_filters(db.filters_to_tuple(filters))
    assert restored == filters

    where, params = db._build_where(restored)
    assert "vintage = ?" in where
    assert "year BETWEEN ? AND ?" in where
    assert "company_code IN" in where
    assert "life_stage IN" in where
    assert "industry_group IN" in where
    assert "gfc = 1" in where and "covid_dummy = 1" in where
    assert params[:3] == ["thesis", 2001, 2005]


def test_all_interfaces_consume_the_same_active_panel_scope():
    app = Path("app.py").read_text(encoding="utf-8")
    stata = Path("pages/23_stata_studio.py").read_text(encoding="utf-8")
    ai = Path("pages/19_ai_assistant.py").read_text(encoding="utf-8")
    assert 'st.session_state.filters["panel_mode"]' in app
    assert "db.filters_to_tuple(filters)" in stata
    assert "build_panel_context(panel_mode=panel_mode, filters=_filters)" in ai


def test_authenticated_matrix_declares_all_four_profiles():
    source = Path("scratch/run_all_users_matrix.py").read_text(encoding="utf-8")
    for profile in EXPECTED_PROFILES:
        assert f'("{profile}"' in source
