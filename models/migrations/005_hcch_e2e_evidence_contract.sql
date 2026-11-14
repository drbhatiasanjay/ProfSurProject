-- Migration 005: HCCH End-to-End Evidence Contract and Review Lifecycle
-- Implements immutable extraction runs, page/table artifacts, candidate facts, review audit trail, snapshot bindings, and derived results.

CREATE TABLE IF NOT EXISTS pre_ipo_extraction_runs (
    id TEXT PRIMARY KEY,
    owner TEXT NOT NULL,
    company TEXT NOT NULL,
    source_id TEXT NOT NULL,
    document_sha256 TEXT NOT NULL,
    total_pages INTEGER NOT NULL,
    pages_indexed INTEGER NOT NULL,
    pages_requiring_ocr INTEGER NOT NULL DEFAULT 0,
    status TEXT NOT NULL,
    extractor_version TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS pre_ipo_page_artifacts (
    id TEXT PRIMARY KEY,
    run_id TEXT NOT NULL,
    physical_page INTEGER NOT NULL,
    printed_page TEXT,
    status TEXT NOT NULL,
    extraction_method TEXT NOT NULL,
    text_hash TEXT NOT NULL,
    char_count INTEGER NOT NULL,
    error_code TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS pre_ipo_table_artifacts (
    id TEXT PRIMARY KEY,
    run_id TEXT NOT NULL,
    section_key TEXT NOT NULL,
    physical_page INTEGER NOT NULL,
    table_id TEXT NOT NULL,
    title TEXT,
    units TEXT,
    basis TEXT,
    headers_json TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS pre_ipo_candidate_facts (
    observation_id TEXT PRIMARY KEY,
    run_id TEXT NOT NULL,
    metric_id TEXT NOT NULL,
    entity TEXT NOT NULL,
    entity_basis TEXT NOT NULL,
    period TEXT,
    duration TEXT,
    unit TEXT,
    value_numeric REAL,
    presence TEXT NOT NULL,
    physical_page INTEGER NOT NULL,
    printed_page TEXT,
    table_id TEXT,
    row_label TEXT,
    column_label TEXT,
    raw_text TEXT NOT NULL,
    document_sha256 TEXT NOT NULL,
    confidence REAL NOT NULL,
    review_state TEXT NOT NULL DEFAULT 'PROPOSED',
    reviewer TEXT,
    reviewed_at TEXT,
    review_reason TEXT,
    corrected_value_numeric REAL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS pre_ipo_candidate_dependencies (
    id TEXT PRIMARY KEY,
    observation_id TEXT NOT NULL,
    parent_observation_id TEXT NOT NULL,
    dependency_type TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (observation_id) REFERENCES pre_ipo_candidate_facts(observation_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS pre_ipo_review_actions (
    action_id TEXT PRIMARY KEY,
    observation_id TEXT NOT NULL,
    action_type TEXT NOT NULL,
    prior_review_state TEXT NOT NULL,
    new_review_state TEXT NOT NULL,
    reviewer TEXT NOT NULL,
    reviewer_role TEXT NOT NULL,
    review_reason TEXT NOT NULL,
    original_value TEXT,
    corrected_value TEXT,
    source_sha256 TEXT NOT NULL,
    page_locator TEXT NOT NULL,
    timestamp TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (observation_id) REFERENCES pre_ipo_candidate_facts(observation_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS pre_ipo_snapshot_bindings (
    snapshot_id TEXT NOT NULL,
    observation_id TEXT NOT NULL,
    revision_reference TEXT NOT NULL,
    normalized_value TEXT NOT NULL,
    unit TEXT NOT NULL,
    period TEXT NOT NULL,
    PRIMARY KEY (snapshot_id, observation_id),
    FOREIGN KEY (observation_id) REFERENCES pre_ipo_candidate_facts(observation_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS pre_ipo_derived_results (
    id TEXT PRIMARY KEY,
    snapshot_id TEXT NOT NULL,
    capability TEXT NOT NULL,
    status TEXT NOT NULL,
    value_json TEXT,
    formula TEXT,
    assumptions_json TEXT,
    observation_ids_json TEXT,
    warnings_json TEXT,
    computation_version TEXT NOT NULL,
    computed_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_pre_ipo_page_artifacts_run ON pre_ipo_page_artifacts(run_id, physical_page);
CREATE INDEX IF NOT EXISTS idx_pre_ipo_candidate_facts_metric ON pre_ipo_candidate_facts(run_id, metric_id, period);
CREATE INDEX IF NOT EXISTS idx_pre_ipo_review_actions_obs ON pre_ipo_review_actions(observation_id);
CREATE INDEX IF NOT EXISTS idx_pre_ipo_derived_results_snap ON pre_ipo_derived_results(snapshot_id, capability);
