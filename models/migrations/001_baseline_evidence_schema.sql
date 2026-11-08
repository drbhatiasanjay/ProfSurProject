-- Migration 001: Baseline Pre-IPO Evidence Schema
CREATE TABLE IF NOT EXISTS pre_ipo_sources (
    owner TEXT NOT NULL,
    company TEXT NOT NULL,
    id TEXT NOT NULL,
    metadata TEXT NOT NULL,
    content BLOB NOT NULL,
    PRIMARY KEY(owner, company, id)
);

CREATE TABLE IF NOT EXISTS pre_ipo_extraction_runs (
    owner TEXT NOT NULL,
    company TEXT NOT NULL,
    id TEXT NOT NULL,
    payload TEXT NOT NULL,
    PRIMARY KEY(owner, company, id)
);

CREATE TABLE IF NOT EXISTS pre_ipo_fact_events (
    owner TEXT NOT NULL,
    company TEXT NOT NULL,
    fact_id TEXT NOT NULL,
    revision INTEGER NOT NULL,
    payload TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY(owner, company, fact_id, revision)
);

CREATE TABLE IF NOT EXISTS pre_ipo_evidence_snapshots (
    owner TEXT NOT NULL,
    company TEXT NOT NULL,
    id TEXT NOT NULL,
    payload TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY(owner, company, id)
);

CREATE TABLE IF NOT EXISTS pre_ipo_reference_versions (
    owner TEXT NOT NULL,
    id TEXT NOT NULL,
    payload TEXT NOT NULL,
    PRIMARY KEY(owner, id)
);

CREATE TABLE IF NOT EXISTS pre_ipo_evidence_actions (
    owner TEXT NOT NULL,
    company TEXT NOT NULL,
    id TEXT NOT NULL,
    payload TEXT NOT NULL,
    PRIMARY KEY(owner, company, id)
);

CREATE TABLE IF NOT EXISTS pre_ipo_company_profiles (
    owner TEXT NOT NULL,
    id TEXT NOT NULL,
    payload TEXT NOT NULL,
    PRIMARY KEY(owner, id)
);

CREATE TABLE IF NOT EXISTS pre_ipo_evidence_action_events (
    owner TEXT NOT NULL,
    company TEXT NOT NULL,
    action_id TEXT NOT NULL,
    revision INTEGER NOT NULL,
    payload TEXT NOT NULL,
    PRIMARY KEY(owner, company, action_id, revision)
);
