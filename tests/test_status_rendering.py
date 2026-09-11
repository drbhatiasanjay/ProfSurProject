from models.rich_chat_renderer import _is_validated_status


def test_status_renderer_does_not_promote_not_validated():
    assert _is_validated_status("NOT_VALIDATED") is False
    assert _is_validated_status("") is False


def test_status_renderer_accepts_only_standalone_validated_token():
    assert _is_validated_status("VALIDATED") is True
    assert _is_validated_status("VALIDATED (fixture)") is True
    assert _is_validated_status("IMPLEMENTED_UNVERIFIED") is False
