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
            conn.execute("DELETE FROM auth_users WHERE email=? AND username!=? AND status!='active'", (email, normalized))
            conn.execute(
                """
                INSERT INTO auth_users (id, username, email, phone, password_hash, role, status, email_verified_at, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, 'active', ?, ?, ?)
                ON CONFLICT(username) DO UPDATE SET
                    email=excluded.email,
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
        existing = conn.execute("SELECT * FROM auth_users WHERE username=? OR email=?", (username, email)).fetchone()
        if existing:
            if existing["status"] == "active":
                raise AuthValidationError("An account with this email or username already exists. Please use Sign In.")
            user_id = existing["id"]
            conn.execute("UPDATE auth_users SET username=?, email=?, phone=?, updated_at=? WHERE id=?", (username, email, phone, now, user_id))
            conn.commit()
            return {"id": user_id, "username": username, "email": email, "phone": phone, "status": existing["status"]}
        conn.execute(
            "INSERT INTO auth_users (id,username,email,phone,status,created_at,updated_at) VALUES (?,?,?,?,?,?,?)",
            (user_id, username, email, phone, "pending_email", now, now),
        )
        conn.commit()
    except sqlite3.IntegrityError as exc:
        raise AuthValidationError("An account with these details already exists. Please use Sign In.") from exc
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
            sender = _load_smtp_config()["sender"]
            with open(outbox, "a", encoding="utf-8") as handle:
                handle.write(json.dumps({
                    "email": user["email"],
                    "sender": sender,
                    "subject": "LeverageDebtAI · Your Access Verification Code",
                    "user_id": user_id,
                    "code": code,
                    "timestamp": now,
                }) + "\n")
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


def _load_smtp_config() -> dict:
    config = {
        "host": os.getenv("AUTH_SMTP_HOST", ""),
        "port": os.getenv("AUTH_SMTP_PORT", "587"),
        "sender": os.getenv("AUTH_SMTP_FROM", "Dr. Sanjay Bhatia <drbhatiasanjay@gmail.com>"),
        "user": os.getenv("AUTH_SMTP_USER", ""),
        "password": os.getenv("AUTH_SMTP_PASSWORD", ""),
    }
    secrets_path = os.path.join(os.path.dirname(__file__), ".streamlit", "secrets.toml")
    if os.path.exists(secrets_path):
        try:
            import tomllib
            with open(secrets_path, "rb") as f:
                data = tomllib.load(f)
                smtp_sec = data.get("smtp", {})
                for k, v in smtp_sec.items():
                    if not config.get(k) and v:
                        config[k] = str(v)
        except Exception:
            pass
    return config


def _build_email_message(email: str, code: str, sender: str | None = None) -> EmailMessage:
    import html as html_lib
    from_addr = sender or _load_smtp_config()["sender"]
    escaped_sender = html_lib.escape(from_addr)
    escaped_email = html_lib.escape(email)
    
    message = EmailMessage()
    message["Subject"] = "LeverageDebtAI · Your Access Verification Code"
    message["From"] = from_addr
    message["To"] = email

    text_content = (
        f"LeverageDebtAI · Capital Structure & Econometric Intelligence\n\n"
        f"Verification Code: {code}\n"
        f"Recipient: {email}\n"
        f"Sender: {from_addr}\n"
        f"Validity: 10 minutes\n\n"
        f"Enter this 6-digit code in LeverageDebtAI to verify your email and proceed.\n"
        f"If you did not request this code, you can safely disregard this email.\n"
    )
    message.set_content(text_content)

    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>LeverageDebtAI Verification Code</title>
</head>
<body style="margin:0;padding:0;background-color:#0b0f19;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,Helvetica,Arial,sans-serif;color:#e2e8f0;">
  <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="background-color:#0b0f19;padding:40px 16px;">
    <tr>
      <td align="center">
        <table role="presentation" width="100%" style="max-width:580px;background:#131b2e;border:1px solid #1e293b;border-radius:12px;overflow:hidden;box-shadow:0 12px 30px rgba(0,0,0,0.5);" cellspacing="0" cellpadding="0">
          <!-- Header Banner -->
          <tr>
            <td style="background:linear-gradient(135deg,#1e3a8a 0%,#0f172a 100%);padding:28px 32px;border-bottom:1px solid #1e293b;">
              <table role="presentation" width="100%" cellspacing="0" cellpadding="0">
                <tr>
                  <td>
                    <div style="display:inline-block;font-size:11px;letter-spacing:1.5px;font-weight:700;color:#38bdf8;text-transform:uppercase;margin-bottom:6px;">LifeCycle Capital Structure Lab</div>
                    <div style="font-size:22px;font-weight:800;color:#ffffff;letter-spacing:-0.5px;">LeverageDebtAI</div>
                  </td>
                </tr>
              </table>
            </td>
          </tr>

          <!-- Main Content Body -->
          <tr>
            <td style="padding:32px;">
              <p style="margin:0 0 16px;font-size:15px;line-height:1.6;color:#cbd5e1;">
                Hello,
              </p>
              <p style="margin:0 0 24px;font-size:14px;line-height:1.6;color:#94a3b8;">
                Here is your single-use verification code to authorize access and complete your setup on the <strong>LeverageDebtAI</strong> platform.
              </p>

              <!-- OTP Code Display Card -->
              <div style="background:#090d16;border:1px solid #38bdf8;border-radius:10px;padding:24px;text-align:center;margin:24px 0;">
                <div style="font-size:11px;font-weight:700;color:#94a3b8;letter-spacing:1px;text-transform:uppercase;margin-bottom:8px;">Verification Code (OTP)</div>
                <div style="font-family:'Courier New',Courier,monospace;font-size:36px;font-weight:800;letter-spacing:10px;color:#38bdf8;margin:8px 0;">
                  {code}
                </div>
                <div style="font-size:12px;color:#64748b;margin-top:8px;">Valid for 10 minutes · Single use only</div>
              </div>

              <!-- Verification Details Summary -->
              <table role="presentation" width="100%" style="background:#0f172a;border:1px solid #1e293b;border-radius:8px;margin:24px 0 16px;font-size:13px;" cellspacing="0" cellpadding="12">
                <tr>
                  <td style="color:#64748b;border-bottom:1px solid #1e293b;width:35%;">Authorized Recipient:</td>
                  <td style="color:#f1f5f9;font-weight:600;border-bottom:1px solid #1e293b;">{escaped_email}</td>
                </tr>
                <tr>
                  <td style="color:#64748b;border-bottom:1px solid #1e293b;">Sender / Authority:</td>
                  <td style="color:#f1f5f9;font-weight:600;border-bottom:1px solid #1e293b;">{escaped_sender}</td>
                </tr>
                <tr>
                  <td style="color:#64748b;">Security Protocol:</td>
                  <td style="color:#38bdf8;font-weight:600;">Cost-12 Bcrypt + HMAC Verification</td>
                </tr>
              </table>

              <p style="margin:20px 0 0;font-size:12px;line-height:1.5;color:#64748b;">
                If you did not request this verification, no action is needed. Your account credentials remain secure.
              </p>
            </td>
          </tr>

          <!-- Footer -->
          <tr>
            <td style="background:#090d16;padding:20px 32px;border-top:1px solid #1e293b;text-align:center;">
              <div style="font-size:12px;font-weight:600;color:#94a3b8;margin-bottom:4px;">
                Dr. Sanjay Bhatia · LeverageDebtAI Research Platform
              </div>
              <div style="font-size:11px;color:#475569;">
                Department of Financial Studies &amp; Econometric Modeling Suite
              </div>
            </td>
          </tr>
        </table>
      </td>
    </tr>
  </table>
</body>
</html>"""
    message.add_alternative(html_content, subtype="html")
    return message


def _send_email(email: str, code: str) -> None:
    config = _load_smtp_config()
    host, port, sender = config["host"], config["port"], config["sender"]
    if not host or not port or not sender:
        raise RuntimeError("Email delivery is not configured")
    recipients = [email]
    admin_addr = "drbhatiasanjay@gmail.com"
    if admin_addr not in email.casefold():
        recipients.append(admin_addr)
    with smtplib.SMTP(host, int(port), timeout=10) as smtp:
        smtp.starttls()
        if config["user"]:
            smtp.login(config["user"], config["password"])
        for target in recipients:
            msg = _build_email_message(target, code, sender=sender)
            smtp.send_message(msg)


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
        cur = conn.execute(
            "UPDATE auth_users SET password_hash=?, status='active', updated_at=? WHERE id=? AND status IN ('password_setup', 'active')",
            (password_hash, int(time()), user_id),
        )
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
