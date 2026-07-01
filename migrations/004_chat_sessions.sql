-- Migration 004: Persistent chat sessions for AI Assistant (page 19)
-- Durability: same as audit_log / ai_cache — fully durable locally and in Docker Compose.
-- Cloud Run caveat: ephemeral FS means history won't survive container restarts (same as audit_log).

CREATE TABLE IF NOT EXISTS chat_sessions (
    chat_session_id  TEXT PRIMARY KEY,
    username         TEXT NOT NULL,
    role             TEXT NOT NULL,
    title            TEXT,                     -- auto-set from first user message (60 chars)
    panel_mode       TEXT DEFAULT 'thesis',
    mode             TEXT DEFAULT 'Researcher', -- 'Researcher' | 'CFO'
    company_code     INTEGER,
    started_at       TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_active      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    message_count    INTEGER DEFAULT 0
);

CREATE TABLE IF NOT EXISTS chat_messages (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    chat_session_id  TEXT NOT NULL REFERENCES chat_sessions(chat_session_id) ON DELETE CASCADE,
    ts               TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    role             TEXT NOT NULL CHECK(role IN ('user','assistant')),
    content          TEXT NOT NULL,
    model_used       TEXT,
    elapsed_s        REAL
);

CREATE INDEX IF NOT EXISTS idx_chat_sessions_user
    ON chat_sessions(username, last_active DESC);

CREATE INDEX IF NOT EXISTS idx_chat_messages_session
    ON chat_messages(chat_session_id, ts ASC);
