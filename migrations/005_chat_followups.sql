-- Migration 005: Follow-up chip persistence for AI Assistant chat (page 19)
-- Stores the FOLLOWUPS_JSON footer's parsed chips alongside each assistant
-- message (JSON-encoded list, NULL for user turns / legacy rows) so
-- "Continue exploring" chips survive page reload and chat-session switching.
--
-- SQLite ALTER TABLE ADD COLUMN is not idempotent — the run_migration.py
-- runner already treats "duplicate column" as "already applied" and skips it.

ALTER TABLE chat_messages ADD COLUMN followups TEXT;
