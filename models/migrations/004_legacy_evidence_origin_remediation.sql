-- Migration 004: Legacy Evidence Origin Remediation
-- Classifies unreviewed rows with missing provenance and NULL/FILING_FACT origin as LEGACY_EXAMPLE and UNREVIEWED.
-- Preserves genuinely source-qualified reviewed rows.
-- Downgrades ACCEPTED_FOR_ANALYSIS snapshots missing canonical hash, reviewer or acceptance time to UNREVIEWED.

UPDATE pre_ipo_observations
SET origin = 'LEGACY_EXAMPLE',
    review_state = 'UNREVIEWED'
WHERE (origin IS NULL OR origin = 'FILING_FACT')
  AND (
    physical_page IS NULL
    OR extraction_run_id IS NULL
    OR reviewer IS NULL
    OR trim(reviewer) = ''
    OR reviewed_at IS NULL
    OR trim(reviewed_at) = ''
  );

UPDATE pre_ipo_evidence_snapshots
SET status = 'UNREVIEWED'
WHERE status = 'ACCEPTED_FOR_ANALYSIS'
  AND (
    snapshot_hash IS NULL
    OR length(snapshot_hash) != 64
    OR accepted_by IS NULL
    OR trim(accepted_by) = ''
    OR accepted_at IS NULL
    OR trim(accepted_at) = ''
  );
