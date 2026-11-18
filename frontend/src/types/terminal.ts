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

export type DealPricingState =
  | { status: 'DRHP_UNPRICED'; isContained: boolean }
  | { status: 'RHP_PRICED'; priceBandMin: number; priceBandMax: number; isContained: boolean }
  | { status: 'TRADING_LIVE'; listingPrice: number; ltp: number };

export type DealIntegrity = 'PASS' | 'CONDITIONAL' | 'BLOCKED';

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
  pricingState: DealPricingState;
  dealIntegrity: DealIntegrity;
  reconciliationGate?: FivePointReconciliationGate;
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
  containmentReason?: string;
  dickinsonStage?: string; // "MATURE (CASH COW)"
  cashFlowPattern?: string; // "(+, -, -)"
  gcpAllocationCr?: number;
  gcpAllocationPct?: number; // GCP % of Fresh (must be <= 25%)
  isGcpCompliant?: boolean;
  provenanceLedger?: ProvenanceField<string | number>[];
  provenanceSummary?: ProvenanceSummary;
  interpretations?: Record<string, AnalyticalInterpretation>;
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
  | 'market_demand'           // Vault 1: Live Book Bidding + Dual-Head ML + SHAP + AQI 0-100
  | 'peer_comps'              // Vault 2: 9-Col Peer Comps + WACA Step-Up + Mueller Persistence
  | 'huber_studio'            // Vault 3: Huber Outlier Regression + Bias Index + Quantiles
  | 'provenance_ledger'       // Vault 4: 513p Line-by-Line Table + BBox Chips + 5-Gate Card
  | 'stress_workpapers'       // Vault 5: Econometric Lab & 2D Stress Workpapers
  | 'econometric_lab'         // Vault 5: Canonical Econometric Lab
  | 'investor_qa'             // Vault 6: 14 Questions + Customer Concentration Shock
  | 'stakeholder_lens'        // Vault 7: 6-Persona Switcher (CFO, Lender, Equity, Retail, etc.)
  | 'red_flag_scanner'        // Vault 8: 6-Rule Automated Radar (FLAG-01 to 06) + Beneish M-Score
  | 'contingent_litigation'   // Vault 9: Contingent Liabilities & Legal Radar (SEBI LODR 2% + Ind AS 37)
  | 'unit_economics'          // Vault 10: Unit Economics & Operational Scale Studio (75-85% Sweet Spot)
  | 'unlisted_arbitrage'      // Vault 11: Sec 56(2)(x) FMV Tax + 6M Carry Cost Breakeven Price
  | 'ic_board_deck'           // Vault 12: Prescriptive Mandate + 1-Click PPTX / PDF Memo
  | 'knowledge_graph';        // Vault 13: Scoped FIBO RHP Knowledge Graph & Dual-Persona Studio

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

export type CanonicalSection =
  | 'Offer Structure'
  | 'Objects'
  | 'P&L'
  | 'Balance Sheet'
  | 'Working Capital'
  | 'Indebtedness'
  | 'Cap Table & Lock-In'
  | 'Governance & RPT'
  | 'Contingent Liabilities'
  | 'Unit Economics & Capacity';

export type ExpectedUnit =
  | 'INR_CRORES'
  | 'PERCENTAGE'
  | 'SHARES'
  | 'DAYS'
  | 'RATIO'
  | 'TEXT'
  | 'DATE'
  | 'COUNT'
  | 'VOLUME_UNITS'
  | 'INR_PER_SHARE'
  | 'INR_PER_UNIT'
  | 'MULTIPLE';

export interface AttributeDefinition {
  attributeId: string;
  section: CanonicalSection;
  label: string;
  expectedUnit: ExpectedUnit;
  statutoryReference: string;
  requiredForGate: boolean;
  downstreamModels?: string[];
}

export interface ProvenanceSummary {
  foundCount: number;
  notFoundCount: number;
  reconfirmCount: number;
  totalCount: number;
}

export type ProvenanceField<T> =
  | {
      status: 'FOUND';
      fieldName: string;
      value: T;
      confidenceScore: number; // Non-optional on FOUND
      bboxCoordinates: [number, number, number, number]; // Non-optional on FOUND
      bbox?: [number, number, number, number];
      pdfPageNumber?: number;
      printedPageLabel?: string;
      chapterName?: string;
      verbatimSnippet?: string;
      sourceQuote?: string;
      sourceDocument?: string;
      attributeId?: string;
      section?: CanonicalSection | string;
      expectedUnit?: ExpectedUnit | string;
      statutoryReference?: string;
      requiredForGate?: boolean;
      reconfirmationReason?: never;
    }
  | {
      status: 'NOT_FOUND';
      fieldName: string;
      value: T | null;
      confidenceScore?: number;
      bboxCoordinates?: [number, number, number, number];
      bbox?: [number, number, number, number];
      pdfPageNumber?: number;
      printedPageLabel?: string;
      chapterName?: string;
      verbatimSnippet?: string;
      sourceQuote?: string;
      sourceDocument?: string;
      attributeId?: string;
      section?: CanonicalSection | string;
      expectedUnit?: ExpectedUnit | string;
      statutoryReference?: string;
      requiredForGate?: boolean;
      reconfirmationReason?: string;
    }
  | {
      status: 'NEEDS_RECONFIRMATION';
      fieldName: string;
      value: T | null;
      confidenceScore?: number;
      bboxCoordinates?: [number, number, number, number];
      bbox?: [number, number, number, number];
      pdfPageNumber?: number;
      printedPageLabel?: string;
      chapterName?: string;
      verbatimSnippet?: string;
      sourceQuote?: string;
      sourceDocument?: string;
      attributeId?: string;
      section?: CanonicalSection | string;
      expectedUnit?: ExpectedUnit | string;
      statutoryReference?: string;
      requiredForGate?: boolean;
      reconfirmationReason: string; // Non-optional on NEEDS_RECONFIRMATION
    };

export interface PillarEvidenceCitation {
  citationSource: string; // e.g. "DRHP Ch. V (Restated Financials), p. 280" or "Dickinson, V. (2011), The Accounting Review"
  sourceType: 'STATUTORY_FILING' | 'ACADEMIC_LITERATURE' | 'REGULATORY_STANDARD' | 'INDUSTRY_REPORT';
  quote: string;
  verifiedMetricOrCutoff?: string;
  drhpPage?: number;
}

export interface MetricVisualData {
  label: string;
  value: string | number;
  benchmark?: string | number;
  unit?: string;
  status?: 'SAFE' | 'WARNING' | 'CRITICAL' | 'NEUTRAL';
  barPct?: number; // 0-100 for visual comparison
}

export interface RiskAxisBar {
  name: string;
  score: number; // 0 - 100
  threshold: number; // e.g. 50
  status: 'SAFE' | 'WARNING' | 'CRITICAL';
  metricSnippet: string;
  mitigation: string;
}

export interface PillarDetail {
  headline: string;
  narration: string; // Detailed multi-paragraph evidence-based analysis
  subParagraph?: string; // Additional context / statutory implication
  citations: PillarEvidenceCitation[];
  metrics: MetricVisualData[];
  chartType?: 'BAR_DISPERSION' | 'LIFECYCLE_TIMELINE' | 'BID_ALLOCATION_MATRIX' | 'RISK_GAUGE_BARS' | 'CUSTOM';
  riskAxes?: RiskAxisBar[];
  recommendationDirective?: string;
}

export interface NarrativeIntelligencePillars {
  sectorContext: string;
  lifecyclePrecedents: string;
  icDirectives?: string;
  prescriptiveMandate?: string;
  riskRadar: string;
  // Enhanced rich structured pillars
  detailedSector?: PillarDetail;
  detailedLifecycle?: PillarDetail;
  detailedIC?: PillarDetail;
  detailedRisk?: PillarDetail;
}

// ==========================================
// EXPANDED 7-MODEL ECONOMETRIC SUITE TYPES
// ==========================================

export type EconometricVerdict = 'FAVORABLE' | 'NEUTRAL' | 'CAUTION' | 'CRITICAL';

export interface EconometricInterpretation {
  verdict: EconometricVerdict;
  statisticalSummary: string;
  economicMechanism: string;
  icRecommendation: string;
}

export type Polarity = 'POSITIVE_CONTRIBUTOR' | 'NEGATIVE_CONTRIBUTOR' | 'NEUTRAL_MONITOR' | 'BLOCKING_RISK';

export interface LiteratureEvidenceCitation {
  citationId: string;
  shortTag: string;
  formalCitation: string;
  statutoryOrPaperQuote: string;
  verifiedCutoff: string;
  governingBodyOrJournal: string;
  downstreamModule: string;
}

export interface CitedInput {
  attributeId: string;
  label: string;
  valueDisplay: string;
  pageNumber: number;
  verbatimSourceQuote?: string;
  bboxCoordinates?: [number, number, number, number];
  chapterOrNote?: string;
}

export interface EvidenceBasis {
  formulaOrMethod: string;
  citedInputs: CitedInput[];
  governingLiterature?: LiteratureEvidenceCitation;
  computedVariables?: Record<string, any>;
  methodologyConcept?: string;
  preIpoRationale?: string;
  benchmarkCutoffs?: string;
}

export interface AnalyticalInterpretation {
  metricId: string;
  polarity: Polarity;
  headline: string;
  whatItMeans: string;
  evidenceBasis: EvidenceBasis;
  callToAction: string;
  missingDataAndBlindSpots: string[];
}

export interface BeneishMScoreData {
  mScore: number;
  isManipulator: boolean;
  zone: 'SAFE' | 'GREY' | 'MANIPULATOR';
  sloanAccrualRatio: number;
  dsri: number;
  gmi: number;
  aqi: number;
  sgi: number;
  depi: number;
  sgai: number;
  tata: number;
  lvgi: number;
  variablesBreakdown: Record<string, number>;
  interpretation: EconometricInterpretation;
}

export interface DickinsonPeriodClassification {
  fiscalPeriod: string;
  cfo: number;
  cfi: number;
  cff: number;
  pattern: string;
  stage: string;
}

export interface DickinsonLifecycleData {
  currentStage: string;
  currentPattern: string;
  trajectory: DickinsonPeriodClassification[];
  stageProgressionSummary: string;
  isGrowthCongruent: boolean;
  interpretation: EconometricInterpretation;
}

export interface HuberPeerWeight {
  symbol: string;
  companyName: string;
  multiple: number;
  predictedMultiple: number;
  residual: number;
  robustWeight: number;
  isOutlier: boolean;
}

export interface HuberRobustRegressionData {
  targetSymbol: string;
  targetMultiple: number;
  warrantedFairMultiple: number;
  unbackedFrothPct: number;
  valuationZScore: number;
  declaredPeerMedian: number;
  algorithmicPeerMedian: number;
  drhpPeerBiasIndex: number;
  rSquaredPseudo: number;
  coefficients: Record<string, number>;
  peerWeights: HuberPeerWeight[];
  interpretation: EconometricInterpretation;
}

export interface StubSeasonalityBreakData {
  stubPeriodLabel: string;
  stubRevenueCr: number;
  naiveAnnualizedRevenueCr: number;
  seasonalAdjustedRevenueCr: number;
  seasonalWeightApplied: number;
  annualizationDistortionCr: number;
  stubEbitdaMarginPct: number;
  historicalMeanMarginPct: number;
  marginSpikeBps: number;
  isMarginStuffingAlert: boolean;
  chowFStat: number;
  chowPValue: number;
  structuralBreakDetected: boolean;
  interpretation: EconometricInterpretation;
}

export interface IndAS116LeaseLeverageData {
  fundedDebtCr: number;
  leaseLiabilitiesCr: number;
  totalAdjustedDebtCr: number;
  cashAndEquivalentsCr: number;
  headlineNetDebtCr: number;
  leaseAdjustedNetDebtCr: number;
  ebitdaCr: number;
  ebitdarCr: number;
  headlineNetDebtToEbitda: number;
  leaseAdjustedNetDebtToEbitdar: number;
  leverageUnderstatementRatio: number;
  debtDueWithin12mCr: number;
  refinancingWallRatio: number;
  isRefinancingWallElevated: boolean;
  interestCoverageAdjusted: number;
  interpretation: EconometricInterpretation;
}

export interface AltmanZScoreData {
  zScore: number;
  zone: 'SAFE' | 'GREY' | 'DISTRESS';
  x1WorkingCapitalToTa: number;
  x2RetainedEarningsToTa: number;
  x3EbitToTa: number;
  x4EquityToTotalLiab: number;
  defaultProbabilityProxyPct: number;
  interpretation: EconometricInterpretation;
}

export interface LockInCliffMilestone {
  daysPostListing: number;
  dateLabel: string;
  unlockedSharesCr: number;
  category: string;
  floatExpansionPct: number;
  daysToAbsorbOverhang: number;
}

export interface LockInAndTaxDragData {
  milestones: LockInCliffMilestone[];
  totalPreIpoSharesCr: number;
  anchorSharesCr: number;
  freeFloatSharesCr: number;
  rule11UaFmvInr: number;
  acquisitionPriceInr: number;
  isTaxDragTriggered: boolean;
  taxDragPerShareInr: number;
  postTaxBreakevenListingPriceInr: number;
  interpretation: EconometricInterpretation;
}

export interface ComprehensiveEconometricSuiteData {
  symbol: string;
  companyName: string;
  timestamp: string;
  overallVerdict: EconometricVerdict;
  isBlocked?: boolean;
  blockedReason?: string;
  models: {
    beneishMScore?: BeneishMScoreData;
    dickinsonLifecycle?: DickinsonLifecycleData;
    huberPeerRegression?: HuberRobustRegressionData;
    stubSeasonality?: StubSeasonalityBreakData;
    indAs116Leverage?: IndAS116LeaseLeverageData;
    altmanZScore?: AltmanZScoreData;
    lockInTaxDrag?: LockInAndTaxDragData;
  };
  interpretations?: Record<string, AnalyticalInterpretation>;
}
