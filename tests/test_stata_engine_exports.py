def test_stata_studio_shared_estimate_exports_are_available():
    from models import stata_engine

    assert hasattr(stata_engine, "_STORED_ESTIMATES")
    assert hasattr(stata_engine, "_LAST_ESTIMATE")
