-- =============================================================================
-- ProfSur Pre-IPO Intelligence Platform — PostgreSQL 16+ Relational Schema
-- Covers:
--   1. Issuer & Filing Master (DRHP / RHP / Unlisted Registry)
--   2. Citation-Linked Restated Ind AS Financials & Statutory KPIs
--   3. Cap Table, Dilution Waterfall & 18-Month WACA Schedule
--   4. Algorithmic Peer Comps, Huber Fair Multiples & T0 Cohort Trajectories
--   5. Governance, RPT, Litigation & NLP Risk Flags
--   6. Walk-Forward ML Inference & Immutable SEBI RA Compliance Audit Trail
-- =============================================================================

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "vector"; -- pgvector for semantic peer embeddings

-- -----------------------------------------------------------------------------
-- 1. ISSUER & STATUTORY FILING MASTER
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS preipo_issuers (
    issuer_id               UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    cin_number              VARCHAR(21) UNIQUE NOT NULL,
    legal_name              VARCHAR(255) NOT NULL,
    nse_symbol              VARCHAR(30),
    bse_scrip_code          VARCHAR(15),
    sector_nic_code         VARCHAR(20),
    sector_name             VARCHAR(120) NOT NULL,
    board_segment           VARCHAR(20) NOT NULL CHECK (board_segment IN ('MAINBOARD', 'NSE_EMERGE', 'BSE_SME')),
    sebi_eligibility_route  VARCHAR(30) CHECK (sebi_eligibility_route IN ('PROFITABILITY_6_1', 'QIB_ROUTE_6_2', 'SME_EXCHANGE')),
    business_embedding      VECTOR(1024), -- Dense embedding of "Our Business" narrative
    created_at              TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at              TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS statutory_filings (
    filing_id               UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    issuer_id               UUID NOT NULL REFERENCES preipo_issuers(issuer_id) ON DELETE CASCADE,
    filing_type             VARCHAR(20) NOT NULL CHECK (filing_type IN ('DRHP', 'ADDENDUM', 'RHP', 'PROSPECTUS')),
    filing_date             DATE NOT NULL,
    sebi_ack_number         VARCHAR(80),
    storage_uri             TEXT NOT NULL,
    total_pages             INT NOT NULL,
    price_band_lower        NUMERIC(12, 2),
    price_band_upper        NUMERIC(12, 2),
    bidding_open_date       DATE,
    bidding_close_date      DATE,
    listing_date            DATE,
    issue_price_final       NUMERIC(12, 2),
    fresh_issue_cr          NUMERIC(14, 2) NOT NULL DEFAULT 0,
    ofs_issue_cr            NUMERIC(14, 2) NOT NULL DEFAULT 0,
    parser_version          VARCHAR(40) NOT NULL,
    is_active               BOOLEAN NOT NULL DEFAULT TRUE,
    created_at              TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_filings_issuer_date ON statutory_filings(issuer_id, filing_date DESC);

-- -----------------------------------------------------------------------------
-- 2. RESTATED IND AS FINANCIALS & STATUTORY KPIs (WITH PAGE CITATIONS)
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS restated_financials (
    financial_id            UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    filing_id               UUID NOT NULL REFERENCES statutory_filings(filing_id) ON DELETE CASCADE,
    fiscal_period           VARCHAR(20) NOT NULL, -- e.g. 'FY23', 'FY24', 'FY25', '9M_FY26_STUB'
    is_stub_period          BOOLEAN NOT NULL DEFAULT FALSE,
    period_months           INT NOT NULL DEFAULT 12,
    -- Income Statement (INR Crores)
    revenue_operations      NUMERIC(15, 2) NOT NULL,
    other_income            NUMERIC(15, 2) NOT NULL DEFAULT 0,
    ebitda                  NUMERIC(15, 2) NOT NULL,
    ebit                    NUMERIC(15, 2) NOT NULL,
    pbt                     NUMERIC(15, 2) NOT NULL,
    pat                     NUMERIC(15, 2) NOT NULL,
    -- Balance Sheet & Cash Flow (INR Crores)
    net_worth               NUMERIC(15, 2) NOT NULL,
    total_debt              NUMERIC(15, 2) NOT NULL DEFAULT 0,
    lease_liabilities       NUMERIC(15, 2) NOT NULL DEFAULT 0,
    cash_and_equivalents    NUMERIC(15, 2) NOT NULL DEFAULT 0,
    trade_receivables       NUMERIC(15, 2) NOT NULL DEFAULT 0,
    total_assets            NUMERIC(15, 2) NOT NULL,
    cfo                     NUMERIC(15, 2) NOT NULL,
    cfi                     NUMERIC(15, 2) NOT NULL DEFAULT 0,
    capex                   NUMERIC(15, 2) NOT NULL DEFAULT 0,
    -- Forensic & Computed Ratios
    sloan_accrual_ratio     NUMERIC(8, 4),
    cfo_to_ebitda           NUMERIC(8, 4),
    ronw_pct                NUMERIC(8, 4),
    roce_pct                NUMERIC(8, 4),
    -- Audit Citation Metadata
    drhp_page_number        INT NOT NULL,
    extraction_confidence   NUMERIC(5, 4) NOT NULL,
    UNIQUE (filing_id, fiscal_period)
);

CREATE TABLE IF NOT EXISTS statutory_kpis (
    kpi_id                  UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    filing_id               UUID NOT NULL REFERENCES statutory_filings(filing_id) ON DELETE CASCADE,
    kpi_name                VARCHAR(120) NOT NULL,
    kpi_unit                VARCHAR(40) NOT NULL,
    fy_minus_2_val          NUMERIC(18, 4),
    fy_minus_1_val          NUMERIC(18, 4),
    fy_latest_val           NUMERIC(18, 4),
    stub_val                NUMERIC(18, 4),
    drhp_page_number        INT NOT NULL
);

-- -----------------------------------------------------------------------------
-- 3. CAP TABLE, DILUTION WATERFALL & 18-MONTH WACA SCHEDULE
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS cap_table_dilution (
    cap_id                  UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    filing_id               UUID UNIQUE NOT NULL REFERENCES statutory_filings(filing_id) ON DELETE CASCADE,
    pre_offer_equity_shares BIGINT NOT NULL,
    ccps_converted_shares   BIGINT NOT NULL DEFAULT 0,
    ccd_ocd_converted_shares BIGINT NOT NULL DEFAULT 0,
    vested_esop_shares      BIGINT NOT NULL DEFAULT 0,
    fresh_issue_shares_upper BIGINT NOT NULL DEFAULT 0,
    ofs_shares              BIGINT NOT NULL DEFAULT 0,
    post_issue_diluted_shares BIGINT NOT NULL,
    promoter_pre_hold_pct   NUMERIC(6, 3) NOT NULL,
    promoter_post_hold_pct  NUMERIC(6, 3) NOT NULL,
    promoter_pledge_pct     NUMERIC(6, 3) NOT NULL DEFAULT 0,
    mpc_lockin_18m_shares   BIGINT NOT NULL DEFAULT 0,
    non_promoter_6m_lockin_shares BIGINT NOT NULL DEFAULT 0,
    drhp_page_number        INT NOT NULL
);

CREATE TABLE IF NOT EXISTS waca_transactions (
    waca_id                 UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    filing_id               UUID NOT NULL REFERENCES statutory_filings(filing_id) ON DELETE CASCADE,
    investor_category       VARCHAR(40) NOT NULL CHECK (investor_category IN ('PROMOTER', 'PE_VC_FUND', 'PRE_IPO_PLACEMENT', 'ESOP_ALLOTMENT')),
    investor_name           VARCHAR(180),
    acquisition_window      VARCHAR(40) NOT NULL, -- e.g. 'LAST_18_MONTHS', 'LAST_12_MONTHS', 'HISTORICAL'
    shares_acquired         BIGINT NOT NULL,
    waca_price_per_share    NUMERIC(12, 2) NOT NULL,
    stepup_to_upper_band    NUMERIC(8, 2) NOT NULL,
    drhp_page_number        INT NOT NULL
);

-- -----------------------------------------------------------------------------
-- 4. ALGORITHMIC PEER BENCHMARKING & T0 LONGITUDINAL TRAJECTORIES
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS peer_benchmark_matrix (
    benchmark_id            UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    filing_id               UUID NOT NULL REFERENCES statutory_filings(filing_id) ON DELETE CASCADE,
    peer_nse_symbol         VARCHAR(30) NOT NULL,
    peer_company_name       VARCHAR(200) NOT NULL,
    is_drhp_declared_peer   BOOLEAN NOT NULL DEFAULT FALSE,
    is_algo_discovered_peer BOOLEAN NOT NULL DEFAULT TRUE,
    similarity_score        NUMERIC(5, 2) NOT NULL, -- 0 to 100 composite score
    business_cosine_sim     NUMERIC(5, 4),
    peer_pe_ttm             NUMERIC(10, 2),
    peer_ev_ebitda          NUMERIC(10, 2),
    peer_ev_sales           NUMERIC(10, 2),
    peer_rev_cagr_3y        NUMERIC(8, 4),
    peer_ebitda_margin      NUMERIC(8, 4),
    peer_roce               NUMERIC(8, 4),
    peer_cfo_to_ebitda      NUMERIC(8, 4),
    snapshot_date           DATE NOT NULL
);

CREATE TABLE IF NOT EXISTS historical_peer_t0_trajectories (
    trajectory_id           UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    peer_nse_symbol         VARCHAR(30) NOT NULL,
    sector_name             VARCHAR(120) NOT NULL,
    peer_listing_date       DATE NOT NULL,
    at_ipo_pe               NUMERIC(10, 2),
    at_ipo_ofs_ratio        NUMERIC(6, 4),
    at_ipo_cfo_ebitda       NUMERIC(8, 4),
    -- Event-Time Cumulative Abnormal Returns (BHAR vs Nifty 500)
    bhar_day_1_pct          NUMERIC(8, 3),
    bhar_day_30_anchor_pct  NUMERIC(8, 3),
    bhar_day_90_anchor_pct  NUMERIC(8, 3),
    bhar_day_180_lockin_pct NUMERIC(8, 3),
    bhar_1y_pct             NUMERIC(8, 3),
    bhar_2y_pct             NUMERIC(8, 3),
    -- Lock-In Window CAR [-5D, +10D]
    car_day_180_window_pct  NUMERIC(8, 3),
    -- DRHP vs Post-IPO 4Q Actual Drift
    margin_drift_4q_bps     INT,
    behavioral_archetype    VARCHAR(40) CHECK (behavioral_archetype IN (
        'COMPOUNDING_COMPOUNDER',
        'PRICED_TO_PERFECTION_DERATER',
        'PE_EXIT_SUPPLY_OVERHANG',
        'WINDOW_DRESSED_FADER'
    ))
);

-- -----------------------------------------------------------------------------
-- 5. GOVERNANCE, RED FLAGS & NLP RISK SCORES
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS governance_red_flags (
    flag_id                 UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    filing_id               UUID NOT NULL REFERENCES statutory_filings(filing_id) ON DELETE CASCADE,
    rule_code               VARCHAR(40) NOT NULL, -- e.g. 'RF01_STUB_MARGIN_SPIKE', 'RF04_AUDITOR_RESIGNATION'
    severity                VARCHAR(15) NOT NULL CHECK (severity IN ('CRITICAL', 'HIGH', 'MODERATE', 'INFO')),
    metric_value            NUMERIC(14, 4),
    threshold_value         NUMERIC(14, 4),
    description             TEXT NOT NULL,
    drhp_page_number        INT NOT NULL,
    nlp_uncertainty_logit   NUMERIC(8, 4)
);

-- -----------------------------------------------------------------------------
-- 6. WALK-FORWARD ML SCORING & IMMUTABLE SEBI RA COMPLIANCE AUDIT LOG
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS ml_valuation_assessments (
    assessment_id           UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    filing_id               UUID NOT NULL REFERENCES statutory_filings(filing_id) ON DELETE CASCADE,
    model_version           VARCHAR(40) NOT NULL,
    -- Econometric Huber Fair Multiple Output
    warranted_fair_pe       NUMERIC(10, 2),
    unbacked_froth_pct      NUMERIC(8, 2),
    drhp_peer_bias_index    NUMERIC(6, 3),
    -- Dual-Score & Walk-Forward ML Outputs
    fundamental_gov_score   NUMERIC(5, 2) NOT NULL, -- 0 to 100
    pricing_sentiment_score NUMERIC(5, 2) NOT NULL, -- 0 to 100
    hold_180d_outperform_prob NUMERIC(6, 3),
    pred_day180_lockin_car  NUMERIC(8, 3),
    closest_peer_archetype  VARCHAR(40),
    shap_attributions_json  JSONB NOT NULL,
    feature_vector_json     JSONB NOT NULL,
    created_at              TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS sebi_compliance_audit_log (
    audit_id                UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    assessment_id           UUID NOT NULL REFERENCES ml_valuation_assessments(assessment_id),
    analyst_user_id         UUID NOT NULL,
    sebi_ra_reg_number      VARCHAR(40),
    thesis_stance           VARCHAR(30) CHECK (thesis_stance IN ('SUBSCRIBE_LONG_TERM', 'SUBSCRIBE_LISTING', 'AVOID', 'DECISION_SUPPORT_ONLY')),
    analyst_override_notes  TEXT,
    thesis_snapshot_hash    CHAR(64) NOT NULL, -- SHA-256 hash of report payload
    exported_report_uri     TEXT,
    created_at              TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Prevent modification or deletion of compliance audit trails
CREATE OR REPLACE FUNCTION prevent_audit_mutation()
RETURNS TRIGGER AS $$
BEGIN
    RAISE EXCEPTION 'sebi_compliance_audit_log is immutable under SEBI RA recordkeeping rules.';
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_immutable_sebi_audit ON sebi_compliance_audit_log;
CREATE TRIGGER trg_immutable_sebi_audit
BEFORE UPDATE OR DELETE ON sebi_compliance_audit_log
FOR EACH ROW EXECUTE FUNCTION prevent_audit_mutation();
