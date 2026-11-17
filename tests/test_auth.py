import sqlite3

import pytest


@pytest.fixture()
def auth_db(tmp_path, monkeypatch):
    import db

    database = tmp_path / "auth.sqlite3"
    monkeypatch.setattr(db, "DB_PATH", str(database))
    monkeypatch.setenv("PROFSUR_DB_PATH", str(database))
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


def test_legacy_bootstrap_rejects_duplicate_emails_before_database_mutation(auth_db):
    credentials = {
        "first_user": {"email": "Shared@Example.com", "password": ""},
        "second_user": {"email": " shared@example.com ", "password": ""},
    }

    with pytest.raises(auth_db.AuthValidationError, match="duplicate email"):
        auth_db.bootstrap_legacy_users(credentials)

    conn = sqlite3.connect(auth_db.db.DB_PATH)
    try:
        assert conn.execute("SELECT COUNT(*) FROM auth_users").fetchone()[0] == 0
    finally:
        conn.close()


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


def test_lockout_and_security_state_persists_across_store_reinitialization(tmp_path, monkeypatch):
    """Item #10 verification: Store re-initialization must not reset lockouts or security state."""
    db_file = tmp_path / "persistent_auth.sqlite3"
    monkeypatch.setenv("PROFSUR_DB_PATH", str(db_file))
    monkeypatch.setenv("AUTH_TEST_MODE", "1")
    monkeypatch.setenv("AUTH_TEST_OUTBOX", str(tmp_path / "outbox.jsonl"))

    import db
    monkeypatch.setattr(db, "DB_PATH", str(db_file))

    from models.user_store import UserStore
    import auth

    # 1. Initialize store instance #1 and enroll user
    store1 = UserStore(str(db_file))
    user = auth.enroll_user("persistent_lockout_user", "persist@example.com", "+919876543219")
    auth.issue_email_code(user["id"])
    code = auth.latest_test_code(user["id"])
    auth.verify_email_code(user["id"], code)
    auth.set_password(user["id"], "correct horse battery staple 2026!")

    # 2. Trigger failed logins on store1 until lockout
    for _ in range(auth.MAX_LOGIN_FAILURES):
        assert store1.authenticate("persistent_lockout_user", "wrong_pass") is None

    # Assert store1 sees user as locked
    assert store1.is_locked("persistent_lockout_user") is True
    locked_until_1 = store1.get_locked_until("persistent_lockout_user")
    assert locked_until_1 is not None
    assert store1.get_failed_attempts("persistent_lockout_user") == auth.MAX_LOGIN_FAILURES

    # 3. Simulate container/server restart: re-initialize a completely new UserStore instance #2
    store2 = UserStore(str(db_file))

    # Assert store2 immediately sees the persisted lockout and failure count
    assert store2.is_locked("persistent_lockout_user") is True
    assert store2.get_locked_until("persistent_lockout_user") == locked_until_1
    assert store2.get_failed_attempts("persistent_lockout_user") == auth.MAX_LOGIN_FAILURES

    # Even with the CORRECT password, store2 MUST reject authentication due to active lockout
    assert store2.authenticate("persistent_lockout_user", "correct horse battery staple 2026!") is None

    # Also test verification_code and code_expires_at persistence across store re-initialization
    user2 = auth.enroll_user("code_user", "code@example.com", "+919876543220")
    store2.set_verification_code(user2["id"], "123456", ttl_seconds=600)
    stored_code_info = store2.get_verification_code(user2["id"])
    assert stored_code_info is not None

    # Re-initialize store instance #3
    store3 = UserStore(str(db_file))
    reloaded_code_info = store3.get_verification_code(user2["id"])
    assert reloaded_code_info is not None
    assert reloaded_code_info["verification_code"] == stored_code_info["verification_code"]
    assert reloaded_code_info["code_expires_at"] == stored_code_info["code_expires_at"]
    # Verification succeeds across re-initialization
    assert store3.verify_code(user2["id"], "123456") is True

