-- Migration 002: audit_log + user_preferences + user_model_runs
-- Adds per-user activity tracking, preference persistence, and model run history.
-- Idempotent — safe to re-run.

BEGIN;

-- audit_log: one row per page visit per authenticated user
CREATE TABLE IF NOT EXISTS audit_log (
    log_id      INTEGER PRIMARY KEY AUTOINCREMENT,
    ts          TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')),
    username    TEXT    NOT NULL,
    role        TEXT    NOT NULL,
    page_name   TEXT    NOT NULL,
    action_type TEXT    NOT NULL DEFAULT 'page_visit',
    details     TEXT,
    session_id  TEXT
);

CREATE INDEX IF NOT EXISTS idx_audit_username ON audit_log(username);
CREATE INDEX IF NOT EXISTS idx_audit_ts       ON audit_log(ts);

-- user_preferences: per-user, per-page widget state (JSON blob, upserted on change)
CREATE TABLE IF NOT EXISTS user_preferences (
    username   TEXT NOT NULL,
    page       TEXT NOT NULL,
    prefs_json TEXT NOT NULL DEFAULT '{}',
    updated_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')),
    PRIMARY KEY (username, page)
);

-- user_model_runs: timestamped history of model executions per user
CREATE TABLE IF NOT EXISTS user_model_runs (
    run_id   INTEGER PRIMARY KEY AUTOINCREMENT,
    ts       TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')),
    username TEXT NOT NULL,
    page     TEXT NOT NULL,
    params   TEXT NOT NULL DEFAULT '{}',
    summary  TEXT NOT NULL DEFAULT '{}'
);

CREATE INDEX IF NOT EXISTS idx_runs_username_page ON user_model_runs(username, page);

COMMIT;
