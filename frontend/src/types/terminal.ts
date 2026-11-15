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

export interface StatutoryOfferDetails {
  symbol: string;
  companyName: string;
  issueType: 'Mainboard' | 'SME';
  issueStartDate: string;
  issueEndDate: string;
  priceBandMin: number;
  priceBandMax: number;
  lotSize: number;
  issueSizeCr: number;
  freshIssueCr: number;
  ofsCr: number;
  leadManagers: string[];
  rhpUrl: string;
  anchorListUrl?: string;
  sebiEligibilityRoute: 'Regulation 6(1) Net Tangible Assets & Profitability' | 'Regulation 6(2) 75% QIB Book Building';
  lockInDaysQIBAnchor: number;
  lockInDaysPreIPOShareholders: number;
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
}

export interface SEBIComplianceRecord {
  researchAnalystRegNo: string;
  analystName: string;
  verificationTimestamp: string;
  immutableReportHashSha256: string;
  dataSources: string[];
  regulationReferences: string[];
}
