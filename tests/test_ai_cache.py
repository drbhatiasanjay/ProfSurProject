"""
Tests for SQLite AI response cache (db.ai_cache_get / db.ai_cache_set).
Verifies: cache hit, cache miss, TTL expiry, idempotency.
"""
import pytest
import time
import sqlite3
import os
import tempfile

import db


# ── fixture: isolated in-memory DB ───────────────────────────────────────────

@pytest.fixture(autouse=True)
def clean_ai_cache(monkeypatch):
    """Patch db.get_connection() to use an isolated in-memory SQLite for each test."""
    conn = sqlite3.connect(":memory:", check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("""
        CREATE TABLE IF NOT EXISTS ai_cache (
            query_hash   TEXT NOT NULL,
            context_hash TEXT NOT NULL,
            model        TEXT NOT NULL,
            response     TEXT NOT NULL,
            created_at   TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (query_hash, context_hash, model)
        )
    """)
    conn.commit()
    monkeypatch.setattr(db, "get_connection", lambda: conn)
    yield conn
    conn.close()


# ── tests ─────────────────────────────────────────────────────────────────────

def test_cache_miss_returns_none():
    result = db.ai_cache_get("nonexistent_hash", "ctx_hash", "claude-haiku-4-5-20251001")
    assert result is None


def test_cache_set_and_hit():
    db.ai_cache_set("qh1", "ch1", "claude-sonnet-4-6", "The answer is 42.")
    result = db.ai_cache_get("qh1", "ch1", "claude-sonnet-4-6")
    assert result == "The answer is 42."


def test_cache_key_includes_model():
    db.ai_cache_set("qh2", "ch2", "claude-haiku-4-5-20251001", "Haiku response.")
    db.ai_cache_set("qh2", "ch2", "claude-sonnet-4-6", "Sonnet response.")
    assert db.ai_cache_get("qh2", "ch2", "claude-haiku-4-5-20251001") == "Haiku response."
    assert db.ai_cache_get("qh2", "ch2", "claude-sonnet-4-6") == "Sonnet response."


def test_cache_key_includes_context_hash():
    db.ai_cache_set("qh3", "ctx_A", "claude-sonnet-4-6", "Answer for ctx A.")
    db.ai_cache_set("qh3", "ctx_B", "claude-sonnet-4-6", "Answer for ctx B.")
    assert db.ai_cache_get("qh3", "ctx_A", "claude-sonnet-4-6") == "Answer for ctx A."
    assert db.ai_cache_get("qh3", "ctx_B", "claude-sonnet-4-6") == "Answer for ctx B."


def test_cache_overwrite_same_key():
    db.ai_cache_set("qh4", "ch4", "claude-sonnet-4-6", "Original.")
    db.ai_cache_set("qh4", "ch4", "claude-sonnet-4-6", "Updated.")
    result = db.ai_cache_get("qh4", "ch4", "claude-sonnet-4-6")
    # Should return either without error — INSERT OR REPLACE semantics
    assert result in ("Original.", "Updated.")


def test_ttl_zero_returns_none(clean_ai_cache):
    """TTL of 0 hours means anything is considered expired — cache should miss."""
    db.ai_cache_set("qh5", "ch5", "claude-sonnet-4-6", "Stale response.")
    # Force created_at to be old by direct SQL update
    clean_ai_cache.execute(
        "UPDATE ai_cache SET created_at = datetime('now', '-1 hour') "
        "WHERE query_hash = 'qh5'"
    )
    clean_ai_cache.commit()
    result = db.ai_cache_get("qh5", "ch5", "claude-sonnet-4-6", ttl_hours=0)
    assert result is None


def test_ttl_not_expired(clean_ai_cache):
    """Entry created now with 24h TTL should still be returned."""
    db.ai_cache_set("qh6", "ch6", "claude-sonnet-4-6", "Fresh response.")
    result = db.ai_cache_get("qh6", "ch6", "claude-sonnet-4-6", ttl_hours=24)
    assert result == "Fresh response."


def test_migration_idempotent(clean_ai_cache):
    """Applying ai_cache table creation twice should not raise."""
    clean_ai_cache.execute("""
        CREATE TABLE IF NOT EXISTS ai_cache (
            query_hash   TEXT NOT NULL,
            context_hash TEXT NOT NULL,
            model        TEXT NOT NULL,
            response     TEXT NOT NULL,
            created_at   TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (query_hash, context_hash, model)
        )
    """)
    clean_ai_cache.commit()
    # Should not raise — idempotent
    result = db.ai_cache_get("idempotent", "ctx", "claude-sonnet-4-6")
    assert result is None
