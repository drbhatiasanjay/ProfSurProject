-- Migration 001: DataV2 vintage-tagged ingest
-- Adds additive columns and tables to support loading CMIE refreshes (DataV2, DataV3, ...)
-- without breaking thesis reproducibility. Idempotent — safe to re-run.
-- See docs/plans/2026-04-21-datav2-vintage-ingest.md

BEGIN;

-- data_vintages: drives the Panel dropdown label lookup
CREATE TABLE IF NOT EXISTS data_vintages (
    vintage         TEXT PRIMARY KEY,
    label           TEXT NOT NULL,
    loaded_at       TEXT,
    row_counts_json TEXT,
    description     TEXT
);

INSERT OR IGNORE INTO data_vintages(vintage, label, description)
VALUES
    ('thesis',    'Thesis (2001–2024)', 'Original 401-firm panel from Prof Surendra Kumar PhD thesis'),
    ('cmie_2025', 'CMIE 2025',          'Mar-2025 rollforward from DataV2 CMIE extracts (T616/T617/T618/T623)');

-- financials.vintage + provenance columns (additive, default thesis for existing rows)
ALTER TABLE financials ADD COLUMN vintage     TEXT DEFAULT 'thesis';
ALTER TABLE financials ADD COLUMN source_file TEXT;
ALTER TABLE financials ADD COLUMN revised_in  TEXT;

-- ownership.vintage + provenance
ALTER TABLE ownership ADD COLUMN vintage     TEXT DEFAULT 'thesis';
ALTER TABLE ownership ADD COLUMN source_file TEXT;
ALTER TABLE ownership ADD COLUMN revised_in  TEXT;

-- ownership: new T618 fields (nullable for 2001-2024 rows)
ALTER TABLE ownership ADD COLUMN venture_capital                    REAL;
ALTER TABLE ownership ADD COLUMN foreign_vc                          REAL;
ALTER TABLE ownership ADD COLUMN qfi                                 REAL;
ALTER TABLE ownership ADD COLUMN custodians                          REAL;
ALTER TABLE ownership ADD COLUMN non_promoter_individuals_small      REAL;
ALTER TABLE ownership ADD COLUMN non_promoter_individuals_large      REAL;

-- companies: track delisting + code supersession (Tata Motors 248093 -> 729991)
ALTER TABLE companies ADD COLUMN superseded_by    INTEGER;
ALTER TABLE companies ADD COLUMN delisted_in_year INTEGER;

-- market_index_series: 639 T623 index series keyed on (index_code, year)
-- The existing market_index table stays as-is (24 rows of Sensex) for back-compat
-- with db.get_market_index(). New code reads from market_index_series.
CREATE TABLE IF NOT EXISTS market_index_series (
    index_code    INTEGER NOT NULL,
    index_name    TEXT    NOT NULL,
    year          INTEGER NOT NULL,
    slot_date     TEXT,
    index_date    TEXT,
    index_closing REAL,
    vintage       TEXT    NOT NULL DEFAULT 'cmie_2025',
    source_file   TEXT,
    PRIMARY KEY (index_code, year)
);

CREATE INDEX IF NOT EXISTS idx_mi_series_year ON market_index_series(year);
CREATE INDEX IF NOT EXISTS idx_mi_series_name ON market_index_series(index_name);

-- financials_history: audit trail for restatements (displaced rows land here)
CREATE TABLE IF NOT EXISTS financials_history (
    archived_at           TEXT NOT NULL,
    archived_from_vintage TEXT NOT NULL,
    company_code          INTEGER,
    year                  INTEGER,
    vintage               TEXT,
    source_file           TEXT,
    leverage              REAL,
    profitability         REAL,
    tangibility           REAL,
    tax                   REAL,
    dividend              REAL,
    firm_size             REAL,
    borrowings            REAL,
    total_liabilities     REAL,
    original_row_json     TEXT
);

-- Tag vintage index on financials so panel_mode predicate uses the index
CREATE INDEX IF NOT EXISTS idx_financials_vintage ON financials(vintage);
CREATE INDEX IF NOT EXISTS idx_ownership_vintage  ON ownership(vintage);

-- Ensure existing rows carry 'thesis' vintage explicitly (DEFAULT applies to INSERTs,
-- not existing rows in SQLite for ALTER TABLE ADD COLUMN with non-constant default).
UPDATE financials SET vintage = 'thesis' WHERE vintage IS NULL;
UPDATE ownership  SET vintage = 'thesis' WHERE vintage IS NULL;

-- Rebuild v_company_financials to expose vintage (existing queries need it for panel_mode).
DROP VIEW IF EXISTS v_company_financials;
CREATE VIEW v_company_financials AS
    SELECT
        f.company_code,
        c.company_name,
        c.nse_symbol,
        c.industry_group,
        c.inc_year,
        c.superseded_by,
        c.delisted_in_year,
        f.year,
        f.age_group,
        f.size_decile,
        f.life_stage,
        f.leverage,
        f.profitability,
        f.tangibility,
        f.tax,
        f.dividend,
        f.firm_size,
        f.tax_shield,
        f.borrowings,
        f.total_liabilities,
        f.cash_holdings,
        f.gfc,
        f.ibc_2016,
        f.covid_dummy,
        f.vintage,
        f.source_file,
        f.revised_in
    FROM financials f
    JOIN companies c ON f.company_code = c.company_code;

COMMIT;
