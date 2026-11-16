export interface MarketIndex {
  symbol: string;
  name: string;
  lastPrice: number;
  change: number;
  pChange: number;
  pe?: number;
  high52?: number;
  low52?: number;
}

export type BoardSegment = 'Mainboard' | 'NSE_Emerge' | 'BSE_SME';

export interface StatutoryOfferDetails {
  symbol: string;
  companyName: string;
  sectorName?: string;
  listingExchanges?: string; // e.g. "BSE, NSE"
  issueType: 'Mainboard' | 'SME' | 'DRHP' | string;
  boardSegment?: BoardSegment;
  filingDateLabel?: string; // e.g. "DRHP · OCTOBER 2026"
  filingDate?: string;
  issueStartDate: string;
  issueEndDate: string;
  priceBandMin: number | null;
  priceBandMax: number | null;
  isPriceUndisclosed?: boolean;
  priceBandDisplay?: string; // e.g. "₹102 - ₹108" or "Drafting / Unpriced (₹[●])"
  lotSize: number | null;
  minCommitmentInr?: number | null;
  issueSizeCr: number | null;
  totalOfferingShares?: number | string; // e.g. "997,461,456"
  freshIssueCr: number | null;
  freshIssueShares?: number | string;
  ofsCr: number | null;
  ofsShares?: number | string;
  freshIssuePct?: number; // 0 - 100
  ofsPct?: number; // 0 - 100
  structureDisplay?: string; // e.g. "100% OFS (₹[●] Undisclosed) · 0% Fresh"
  leadManagers: string[];
  rhpUrl: string;
  anchorListUrl?: string;
  sebiEligibilityRoute: string; // e.g. "Regulation 6(2) 75% QIB Book Building"
  lockInDaysQIBAnchor: number;
  lockInDaysPreIPOShareholders: number;
  isContained?: boolean;
  containmentReason?: string;
  dickinsonStage?: string; // "MATURE (CASH COW)"
  cashFlowPattern?: string; // "(+, -, -)"
  gcpAllocationCr?: number;
  gcpAllocationPct?: number; // GCP % of Fresh (must be <= 25%)
  isGcpCompliant?: boolean;
}

export interface SubscriptionCategory {
  category: string;
  sharesOffered: number;
  sharesBid: number;
  subscriptionMultiple: number;
}

export interface SubscriptionBook {
  totalMultiple: number;
  totalBidsShares: number;
  totalAmountCollectedCr: number;
  categories: SubscriptionCategory[];
  lastUpdated: string;
}

export interface LivePeerComp {
  symbol: string;
  companyName: string;
  lastPrice: number;
  change: number;
  pChange: number;
  pe: number;
  evEbitda: number;
  evSales: number;
  revenueCagr3Y: number;
  ebitdaMargin: number;
  roce: number;
  cfoToEbitda: number;
  high52: number;
  low52: number;
  marketCapCr: number;
  similarityScore: number;
  isDrhpDeclared: boolean;
  muellerLambda?: number;
  muellerHalfLifeYears?: number;
}

export interface QuantileBands {
  p10BearMultiple: number;
  p50BaseMultiple: number;
  p90BullMultiple: number;
}

export interface HuberCalibrationResults {
  metric: string;
  declaredPeerMedian: number;
  algorithmicPeerMedian: number;
  drhpBiasIndex: number;
  warrantedFairMultiple: number;
  unbackedFrothPct: number;
  formula: string;
  coefficients: {
    feature: string;
    weight: number;
    tStat: number;
  }[];
  rSquaredRobust: number;
  quantiles?: QuantileBands;
  isUnpricedFailsafe?: boolean;
  unpricedNotice?: string;
}

export interface SHAPFeature {
  featureName: string;
  displayName: string;
  category: 'Forensic & Accruals' | 'Capital Structure' | 'Valuation Multiple' | 'Statutory Signal' | 'Market Sentiment';
  featureValue: string | number;
  attributionValue: number; // positive = boosts outperformance, negative = increases drawdown
  isWarning: boolean;
}

export interface WalkForwardMLScorecardData {
  fundamentalScore: number; // 0 - 100
  sentimentScore: number; // 0 - 100
  compositeRating: 'STRONG_BUY_ALPHA' | 'TACTICAL_LISTING_ONLY' | 'AVOID_HIGH_DRAWDOWN_RISK' | 'HOLD_FOR_LOCK_IN_DIP';
  prob180DOutperformance: number; // % (Head A)
  expectedMonth6LockinCAR: number; // % (Head B)
  lockinExpiryDate: string;
  shapTopFeatures: SHAPFeature[];
  walkForwardBacktestAccuracy: number; // e.g. 78.4%
  behavioralArchetype?: 'Compounding Compounder' | 'Priced-to-Perfection De-Rater' | 'PE Exit / Supply Overhang' | 'Window-Dressed Fader';
}

export interface SEBIComplianceRecord {
  researchAnalystRegNo: string;
  analystName: string;
  verificationTimestamp: string;
  immutableReportHashSha256: string;
  dataSources: string[];
  regulationReferences: string[];
}

// ==========================================
// NEW v3.5.0 VAULT & FORENSIC TYPES
// ==========================================

export type VaultId =
  | 'market_demand'     // Vault 1: Live Book Bidding + Dual-Head ML + SHAP + AQI 0-100
  | 'peer_comps'        // Vault 2: 9-Col Peer Comps + WACA Step-Up + Mueller Persistence
  | 'huber_studio'      // Vault 3: Huber Outlier Regression + Bias Index + Quantiles
  | 'provenance_ledger' // Vault 4: 513p Line-by-Line Table + BBox Chips + 5-Gate Card
  | 'stress_workpapers' // Vault 5: 2D Stress 5x5 + Sloan Accruals + Debt Ladder
  | 'investor_qa'       // Vault 6: 14 Questions + Customer Concentration Shock
  | 'stakeholder_lens'  // Vault 7: 6-Persona Switcher (CFO, Lender, Equity, Retail, etc.)
  | 'red_flag_scanner'  // Vault 8: 6-Rule Automated Radar (FLAG-01 to 06) + Beneish M-Score
  | 'unlisted_arbitrage'// Vault 9: Sec 56(2)(x) FMV Tax + 6M Carry Cost Breakeven Price
  | 'ic_board_deck';    // Vault 10: Prescriptive Mandate + 1-Click PPTX / PDF Memo

export interface TriStateLedgerCounters {
  verified: number;
  rhpPending: number;
  needsReconfirmation: number;
}

export interface RedFlagItem {
  ruleCode: string; // FLAG-01, FLAG-02, etc.
  ruleName: string;
  status: 'TRIGGERED' | 'CLEAR' | 'MONITOR';
  metricValue: string | number;
  threshold: string;
  severity: 'CRITICAL' | 'WARNING' | 'INFO';
  drhpCitation: string;
  explanation: string;
}

export interface AnchorQualityMetrics {
  aqiScore: number; // 0 - 100
  diiAllocationPct: number;
  swfAllocationPct: number;
  longOnlyFpiPct: number;
  opaqueFpiPct: number;
  day90SupplyOverhangRisk: 'LOW' | 'MODERATE' | 'HIGH' | 'CRITICAL';
  anchorBookSizeCr: number;
  freeFloatPct: number;
}

export interface UnlistedArbitrageModel {
  unlistedPrice: number;
  rule11UaFmv: number;
  isSec56TaxTriggered: boolean;
  sec56TaxLiabilityPerShare: number;
  landedCostPerShare: number;
  annualCarryCostPct: number;
  holdingPeriodMonths: number;
  totalCarryCostPerShare: number;
  stcgTaxRatePct: number;
  ltcgTaxRatePct: number;
  targetReturnAnnualPct: number;
  postTaxBreakevenListingPrice: number;
  marginOfSafetyPct: number;
}

export interface FivePointReconciliationGate {
  gate1BalanceSheet: {
    status: 'PASS' | 'FAIL' | 'RECONFIRM';
    assetsCr: number;
    liabilitiesAndEquityCr: number;
    variancePct: number;
    citation: string;
  };
  gate2OfferSplit: {
    status: 'PASS' | 'FAIL';
    freshCr: number;
    ofsCr: number;
    totalCr: number;
    citation: string;
  };
  gate3CashToPnl: {
    status: 'PASS' | 'FAIL';
    cfoCr: number;
    ebitdaCr: number;
    patCr: number;
    cfoToEbitda: number;
    citation: string;
  };
  gate4CapTableDilution: {
    status: 'PASS' | 'FAIL';
    preShares: number;
    convertedCcps: number;
    freshShares: number;
    postShares: number;
    citation: string;
  };
  gate5ObjectsGcpCap: {
    status: 'PASS' | 'FAIL';
    capexCr: number;
    debtCr: number;
    wcCr: number;
    gcpCr: number;
    gcpPctOfFresh: number;
    citation: string;
  };
}

export interface ProvenanceField<T> {
  fieldName: string;
  status: 'FOUND' | 'NOT_FOUND' | 'NEEDS_RECONFIRMATION';
  value: T | null;
  confidenceScore: number;
  pdfPageNumber?: number;
  printedPageLabel?: string;
  chapterName?: string;
  bbox?: [number, number, number, number]; // [x0, y0, x1, y1]
  verbatimSnippet?: string;
  reconfirmationReason?: string;
}

export interface NarrativeIntelligencePillars {
  sectorContext: string;
  lifecyclePrecedents: string;
  icDirectives?: string;
  prescriptiveMandate?: string;
  riskRadar: string;
}
