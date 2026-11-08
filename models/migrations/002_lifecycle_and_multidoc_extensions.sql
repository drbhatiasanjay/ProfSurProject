-- Pre-IPO Lifecycle, Observations, Jobs, and Multi-Document Extensions Migration (002)

CREATE TABLE IF NOT EXISTS pre_ipo_artifacts (
    owner TEXT NOT NULL,
    company TEXT NOT NULL,
    source_id TEXT NOT NULL,
    artifact_id TEXT NOT NULL,
    artifact_type TEXT NOT NULL,
    page_number INTEGER,
    mime_type TEXT NOT NULL,
    content BLOB NOT NULL,
    metadata_json TEXT NOT NULL DEFAULT '{}',
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY(owner, company, source_id, artifact_id)
);

CREATE TABLE IF NOT EXISTS pre_ipo_jobs (
    id TEXT PRIMARY KEY,
    owner TEXT NOT NULL,
    company TEXT NOT NULL,
    source_id TEXT NOT NULL,
    job_type TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'QUEUED',
    attempt_count INTEGER NOT NULL DEFAULT 0,
    max_attempts INTEGER NOT NULL DEFAULT 3,
    lease_owner TEXT,
    lease_expires_at TEXT,
    error_message TEXT,
    payload_json TEXT NOT NULL DEFAULT '{}',
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS pre_ipo_observations (
    owner TEXT NOT NULL,
    company TEXT NOT NULL,
    observation_id TEXT NOT NULL,
    revision INTEGER NOT NULL DEFAULT 1,
    source_id TEXT NOT NULL,
    entity TEXT NOT NULL,
    metric_id TEXT NOT NULL,
    period TEXT,
    duration TEXT,
    basis TEXT,
    framework TEXT,
    currency TEXT,
    unit TEXT,
    value TEXT,
    presence TEXT NOT NULL,
    review_state TEXT NOT NULL DEFAULT 'UNREVIEWED',
    provenance_json TEXT NOT NULL DEFAULT '{}',
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY(owner, company, observation_id, revision)
);

CREATE TABLE IF NOT EXISTS pre_ipo_dependencies (
    owner TEXT NOT NULL,
    company TEXT NOT NULL,
    dependent_kind TEXT NOT NULL,
    dependent_id TEXT NOT NULL,
    target_kind TEXT NOT NULL,
    target_id TEXT NOT NULL,
    relation_type TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY(owner, company, dependent_kind, dependent_id, target_kind, target_id)
);

CREATE TABLE IF NOT EXISTS pre_ipo_tombstones (
    id TEXT PRIMARY KEY,
    owner TEXT NOT NULL,
    company TEXT NOT NULL,
    target_kind TEXT NOT NULL,
    target_id TEXT NOT NULL,
    generation INTEGER NOT NULL,
    action TEXT NOT NULL,
    reason TEXT,
    actor TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS pre_ipo_decision_versions (
    owner TEXT NOT NULL,
    case_id TEXT NOT NULL,
    revision INTEGER NOT NULL,
    company_id TEXT,
    snapshot_id TEXT,
    payload TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY(owner, case_id, revision)
);

CREATE TABLE IF NOT EXISTS pre_ipo_decision_actions (
    owner TEXT NOT NULL,
    company_id TEXT,
    case_id TEXT NOT NULL,
    revision INTEGER NOT NULL,
    action_id TEXT NOT NULL,
    payload TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY(owner, action_id)
);

CREATE INDEX IF NOT EXISTS idx_obs_lookup ON pre_ipo_observations(owner, company, metric_id, period, review_state);
CREATE INDEX IF NOT EXISTS idx_obs_source ON pre_ipo_observations(owner, company, source_id);
CREATE INDEX IF NOT EXISTS idx_jobs_lease ON pre_ipo_jobs(status, lease_expires_at);
CREATE INDEX IF NOT EXISTS idx_deps_target ON pre_ipo_dependencies(owner, company, target_kind, target_id);
CREATE INDEX IF NOT EXISTS idx_tomb_target ON pre_ipo_tombstones(owner, company, target_kind, target_id);
