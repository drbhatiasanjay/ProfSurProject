-- Migration 002: add country + ticker columns to companies for US panel support.
-- Applied automatically by scripts/load_us_av_panel.py (idempotent via error catch).
-- Safe to run repeatedly: SQLite raises "duplicate column name" if already applied.

ALTER TABLE companies ADD COLUMN country TEXT DEFAULT 'India';
ALTER TABLE companies ADD COLUMN ticker  TEXT;
