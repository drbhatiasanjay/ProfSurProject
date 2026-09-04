"""Secure local authentication primitives for the LeverageDebtAI entry flow.

The Streamlit UI is deliberately kept out of this module so the security rules
can be tested without a browser. Production email delivery must be configured;
the test outbox is enabled only with AUTH_TEST_MODE=1 and APP_ENV != production.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import os
import re
import secrets
import smtplib
import sqlite3
import uuid
from email.message import EmailMessage
from time import time

import bcrypt

import db

MAX_LOGIN_FAILURES = 5
LOCKOUT_SECONDS = 15 * 60
CODE_TTL_SECONDS = 10 * 60
MAX_CODE_ATTEMPTS = 5
PASSWORD_MIN_LENGTH = 8
_USERNAME = re.compile(r"^[a-z0-9](?:[a-z0-9_.-]{1,28}[a-z0-9])?$")
_EMAIL = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")
_PHONE = re.compile(r"^\+[1-9]\d{7,14}$")


class AuthValidationError(ValueError):
    pass


def normalize_username(value: str) -> str:
    value = (value or "").strip().casefold()
    if not _USERNAME.fullmatch(value):
        raise AuthValidationError("Choose a username with 3-30 letters, numbers, dots, dashes, or underscores.")
    return value


def normalize_email(value: str) -> str:
    value = (value or "").strip().casefold()
    if len(value) > 254 or not _EMAIL.fullmatch(value):
        raise AuthValidationError("Enter a valid email address.")
    return value


def normalize_phone(value: str) -> str:
    value = (value or "").strip().replace(" ", "")
    if not _PHONE.fullmatch(value):
        raise AuthValidationError("Enter a phone number in international format, for example +919876543210.")
    return value


def validate_password(value: str) -> str:
    if not value or len(value) < PASSWORD_MIN_LENGTH:
        raise AuthValidationError(f"Use a password of at least {PASSWORD_MIN_LENGTH} characters.")
    if len(value) > 128:
        raise AuthValidationError("Use a password of 128 characters or fewer.")
    return value


def _hash(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _row(row):
    return dict(row) if row else None


def ensure_auth_tables() -> None:
    conn = db.get_connection()
    try:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS auth_users (
                id TEXT PRIMARY KEY,
                username TEXT NOT NULL UNIQUE,
                email TEXT NOT NULL UNIQUE,
                phone TEXT NOT NULL,
                password_hash TEXT,
                role TEXT NOT NULL DEFAULT 'viewer' CHECK(role IN ('viewer','researcher','admin')),
                status TEXT NOT NULL DEFAULT 'pending_email' CHECK(status IN ('pending_email','password_setup','active','disabled')),
                email_verified_at INTEGER,
                failed_login_count INTEGER NOT NULL DEFAULT 0,
                locked_until INTEGER,
                created_at INTEGER NOT NULL,
                updated_at INTEGER NOT NULL
            );
            CREATE TABLE IF NOT EXISTS auth_challenges (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL REFERENCES auth_users(id) ON DELETE CASCADE,
                purpose TEXT NOT NULL CHECK(purpose IN ('email_verification','password_reset')),
                code_hash TEXT NOT NULL,
                expires_at INTEGER NOT NULL,
                attempts INTEGER NOT NULL DEFAULT 0,
                consumed_at INTEGER,
                created_at INTEGER NOT NULL
            );
            CREATE INDEX IF NOT EXISTS idx_auth_challenges_user ON auth_challenges(user_id, purpose, created_at DESC);
            """
        )
        conn.commit()
    finally:
        conn.close()


def bootstrap_legacy_users(credentials: dict) -> None:
    """Import existing bcrypt-hashed secrets users; synchronizes password hashes and roles."""
    for username, record in (credentials or {}).items():
        password_hash = str(record.get("password", ""))
        if not password_hash.startswith(("$2a$", "$2b$", "$2y$")):
            continue
        try:
            normalized = normalize_username(username)
        except AuthValidationError:
            continue
        email = normalize_email(record.get("email") or f"{normalized}@local.invalid")
        try:
            phone = normalize_phone(record.get("phone") or "+10000000000")
        except AuthValidationError:
            phone = "+10000000000"
        now = int(time())
        conn = db.get_connection()
        try:
            conn.execute(
                """
                INSERT INTO auth_users (id, username, email, phone, password_hash, role, status, email_verified_at, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, 'active', ?, ?, ?)
                ON CONFLICT(username) DO UPDATE SET
                    password_hash=excluded.password_hash,
                    role=excluded.role,
                    status='active',
                    updated_at=excluded.updated_at
                """,
                (str(uuid.uuid5(uuid.NAMESPACE_DNS, f"legacy:{normalized}")), normalized, email, phone, password_hash, record.get("role", "viewer"), now, now, now),
            )
            conn.commit()
        finally:
            conn.close()


def get_user_by_username(username: str):
    value = normalize_username(username)
    conn = db.get_connection()
    try:
        conn.row_factory = sqlite3.Row
        return _row(conn.execute("SELECT * FROM auth_users WHERE username=?", (value,)).fetchone())
    finally:
        conn.close()


def enroll_user(username: str, email: str, phone: str):
    username, email, phone = normalize_username(username), normalize_email(email), normalize_phone(phone)
    now, user_id = int(time()), str(uuid.uuid4())
    conn = db.get_connection()
    try:
        conn.row_factory = sqlite3.Row
        conn.execute(
            "INSERT INTO auth_users (id,username,email,phone,status,created_at,updated_at) VALUES (?,?,?,?,?,?,?)",
            (user_id, username, email, phone, "pending_email", now, now),
        )
        conn.commit()
    except sqlite3.IntegrityError as exc:
        raise AuthValidationError("We could not create that account. Check the details or use sign in.") from exc
    finally:
        conn.close()
    return {"id": user_id, "username": username, "email": email, "phone": phone, "status": "pending_email"}


def _test_mode() -> bool:
    return os.getenv("AUTH_TEST_MODE") == "1" and os.getenv("APP_ENV", "development").casefold() != "production"


def issue_email_code(user_id: str):
    code = f"{secrets.randbelow(1_000_000):06d}"
    challenge_id, now = str(uuid.uuid4()), int(time())
    conn = db.get_connection()
    try:
        conn.row_factory = sqlite3.Row
        user = conn.execute("SELECT id,email FROM auth_users WHERE id=?", (user_id,)).fetchone()
        if not user:
            raise AuthValidationError("We could not start email verification.")
        conn.execute("UPDATE auth_challenges SET consumed_at=? WHERE user_id=? AND purpose=? AND consumed_at IS NULL", (now, user_id, "email_verification"))
        conn.execute(
            "INSERT INTO auth_challenges (id,user_id,purpose,code_hash,expires_at,created_at) VALUES (?,?,?,?,?,?)",
            (challenge_id, user_id, "email_verification", _hash(code), now + CODE_TTL_SECONDS, now),
        )
        conn.commit()
        if _test_mode():
            outbox = os.getenv("AUTH_TEST_OUTBOX", "auth-test-outbox.jsonl")
            with open(outbox, "a", encoding="utf-8") as handle:
                handle.write(json.dumps({"email": user["email"], "user_id": user_id, "code": code}) + "\n")
        else:
            _send_email(user["email"], code)
    finally:
        conn.close()
    return {"id": challenge_id, "code": code} if _test_mode() else {"id": challenge_id}


def latest_test_code(user_id: str) -> str:
    if not _test_mode():
        raise AuthValidationError("Test email delivery is disabled.")
    path = os.getenv("AUTH_TEST_OUTBOX", "auth-test-outbox.jsonl")
    with open(path, encoding="utf-8") as handle:
        messages = [json.loads(line) for line in handle if line.strip()]
    return next(item["code"] for item in reversed(messages) if item["user_id"] == user_id)


def _send_email(email: str, code: str) -> None:
    host, port, sender = os.getenv("AUTH_SMTP_HOST"), os.getenv("AUTH_SMTP_PORT"), os.getenv("AUTH_SMTP_FROM")
    if not host or not port or not sender:
        raise RuntimeError("Email delivery is not configured")
    message = EmailMessage()
    message["Subject"], message["From"], message["To"] = "Verify your LeverageDebtAI account", sender, email
    message.set_content(f"Your LeverageDebtAI verification code is {code}. It expires in 10 minutes.")
    with smtplib.SMTP(host, int(port), timeout=10) as smtp:
        smtp.starttls()
        if os.getenv("AUTH_SMTP_USER"):
            smtp.login(os.environ["AUTH_SMTP_USER"], os.environ["AUTH_SMTP_PASSWORD"])
        smtp.send_message(message)


def verify_email_code(user_id: str, code: str) -> bool:
    if not re.fullmatch(r"\d{6}", code or ""):
        return False
    now = int(time())
    conn = db.get_connection()
    try:
        conn.row_factory = sqlite3.Row
        challenge = conn.execute(
            "SELECT * FROM auth_challenges WHERE user_id=? AND purpose=? AND consumed_at IS NULL ORDER BY created_at DESC LIMIT 1",
            (user_id, "email_verification"),
        ).fetchone()
        if not challenge or challenge["expires_at"] < now or challenge["attempts"] >= MAX_CODE_ATTEMPTS:
            return False
        if not hmac.compare_digest(challenge["code_hash"], _hash(code)):
            conn.execute("UPDATE auth_challenges SET attempts=attempts+1 WHERE id=?", (challenge["id"],))
            conn.commit()
            return False
        conn.execute("UPDATE auth_challenges SET consumed_at=? WHERE id=? AND consumed_at IS NULL", (now, challenge["id"]))
        conn.execute("UPDATE auth_users SET status='password_setup', email_verified_at=?, updated_at=? WHERE id=?", (now, now, user_id))
        conn.commit()
        return True
    finally:
        conn.close()


def set_password(user_id: str, password: str) -> None:
    validate_password(password)
    password_hash = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt(rounds=12)).decode("utf-8")
    conn = db.get_connection()
    try:
        cur = conn.execute("UPDATE auth_users SET password_hash=?, status='active', updated_at=? WHERE id=? AND status='password_setup'", (password_hash, int(time()), user_id))
        if cur.rowcount != 1:
            raise AuthValidationError("Complete email verification before setting a password.")
        conn.commit()
    finally:
        conn.close()


def authenticate(identifier: str, password: str):
    identifier = (identifier or "").strip().casefold()
    now = int(time())
    conn = db.get_connection()
    try:
        conn.row_factory = sqlite3.Row
        user = conn.execute("SELECT * FROM auth_users WHERE username=? OR email=?", (identifier, identifier)).fetchone()
        dummy = "$2b$12$C6UzMDM.H6dfI/f/IKcEe.5Q8sJYp6z3u9TQ9R3X4xR6mY6mY6mY6m"
        password_hash = user["password_hash"] if user and user["password_hash"] else dummy
        try:
            valid = bcrypt.checkpw((password or "").encode("utf-8"), password_hash.encode("utf-8"))
        except (ValueError, TypeError):
            valid = False
        if not user or user["status"] != "active" or (user["locked_until"] and user["locked_until"] > now) or not valid:
            if user and user["status"] == "active":
                failures = user["failed_login_count"] + 1
                locked = now + LOCKOUT_SECONDS if failures >= MAX_LOGIN_FAILURES else None
                conn.execute("UPDATE auth_users SET failed_login_count=?, locked_until=?, updated_at=? WHERE id=?", (failures, locked, now, user["id"]))
                conn.commit()
            return None
        conn.execute("UPDATE auth_users SET failed_login_count=0, locked_until=NULL, updated_at=? WHERE id=?", (now, user["id"]))
        conn.commit()
        return {"id": user["id"], "username": user["username"], "email": user["email"], "role": user["role"]}
    finally:
        conn.close()
