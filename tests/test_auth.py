import sqlite3

import pytest


@pytest.fixture()
def auth_db(tmp_path, monkeypatch):
    import db

    database = tmp_path / "auth.sqlite3"
    monkeypatch.setattr(db, "DB_PATH", str(database))
    monkeypatch.setenv("AUTH_TEST_MODE", "1")
    monkeypatch.setenv("AUTH_TEST_OUTBOX", str(tmp_path / "auth-outbox.jsonl"))
    import auth

    auth.ensure_auth_tables()
    return auth


def test_enrollment_normalizes_identifiers_and_stores_only_a_hash(auth_db):
    user = auth_db.enroll_user(" Alice_One ", "ALICE@Example.COM ", "+919876543210")

    assert user["username"] == "alice_one"
    assert user["email"] == "alice@example.com"
    assert user["status"] == "pending_email"
    row = auth_db.get_user_by_username("alice_one")
    assert row["password_hash"] is None
    assert "alice@example.com" not in row["password_hash"] if row["password_hash"] else True


def test_invalid_identifiers_and_weak_password_are_rejected(auth_db):
    with pytest.raises(auth_db.AuthValidationError):
        auth_db.enroll_user("x' OR 1=1 --", "not-an-email", "123")
    with pytest.raises(auth_db.AuthValidationError):
        auth_db.validate_password("short")


def test_email_code_is_single_use_and_enables_password_setup(auth_db, monkeypatch):
    monkeypatch.setenv("AUTH_TEST_MODE", "1")
    user = auth_db.enroll_user("new_user", "new@example.com", "+919876543211")
    challenge = auth_db.issue_email_code(user["id"])

    assert auth_db.verify_email_code(user["id"], "000000") is False
    assert auth_db.verify_email_code(user["id"], challenge["code"]) is True
    assert auth_db.verify_email_code(user["id"], challenge["code"]) is False
    auth_db.set_password(user["id"], "correct horse battery staple 2026!")
    assert auth_db.authenticate("new_user", "correct horse battery staple 2026!")["id"] == user["id"]


def test_authentication_is_generic_and_sql_injection_cannot_change_identity(auth_db):
    user = auth_db.enroll_user("safe_user", "safe@example.com", "+919876543212")
    auth_db.issue_email_code(user["id"])
    auth_db.verify_email_code(user["id"], auth_db.latest_test_code(user["id"]))
    auth_db.set_password(user["id"], "correct horse battery staple 2026!")

    assert auth_db.authenticate("' OR 1=1 --", "correct horse battery staple 2026!") is None
    assert auth_db.authenticate("safe_user", "wrong password") is None
    assert auth_db.authenticate("safe_user", "x" * 1000) is None


def test_failed_logins_lock_the_account(auth_db):
    user = auth_db.enroll_user("locked_user", "locked@example.com", "+919876543213")
    auth_db.issue_email_code(user["id"])
    auth_db.verify_email_code(user["id"], auth_db.latest_test_code(user["id"]))
    auth_db.set_password(user["id"], "correct horse battery staple 2026!")

    for _ in range(auth_db.MAX_LOGIN_FAILURES):
        assert auth_db.authenticate("locked_user", "wrong password") is None
    assert auth_db.authenticate("locked_user", "correct horse battery staple 2026!") is None
