-- Migration 003: Evidence Contract Normalization and Audit Attributes
-- Normalizes observation attributes, snapshot status, and audit review fields.

CREATE INDEX IF NOT EXISTS idx_pre_ipo_obs_locator ON pre_ipo_observations(owner, company, physical_page);
CREATE INDEX IF NOT EXISTS idx_pre_ipo_obs_review ON pre_ipo_observations(owner, company, review_state);
CREATE INDEX IF NOT EXISTS idx_pre_ipo_snap_status ON pre_ipo_evidence_snapshots(owner, company, status);

