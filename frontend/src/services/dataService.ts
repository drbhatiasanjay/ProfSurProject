import {
  MarketIndex,
  StatutoryOfferDetails,
  SubscriptionBook,
  LivePeerComp,
  HuberCalibrationResults,
  WalkForwardMLScorecardData,
  SEBIComplianceRecord
} from '../types/terminal';

export const mockMarketIndices: MarketIndex[] = [
  {
    symbol: 'NIFTY 50',
    name: 'Nifty 50 Index',
    lastPrice: 25144.30,
    change: 89.40,
    pChange: 0.36,
    pe: 20.49,
    high52: 26277.35,
    low52: 21281.45,
  },
  {
    symbol: 'NIFTY FMCG',
    name: 'Nifty FMCG Sectoral Index',
    lastPrice: 46833.55,
    change: 142.10,
    pChange: 0.30,
    pe: 32.85,
    high52: 54320.10,
    low52: 44100.20,
  },
  {
    symbol: 'INDIA VIX',
    name: 'India Volatility Index',
    lastPrice: 15.78,
    change: -0.45,
    pChange: -2.77,
    high52: 23.15,
    low52: 10.20,
  },
  {
    symbol: 'NIFTY ENERGY',
    name: 'Nifty Energy Index',
    lastPrice: 38450.20,
    change: 210.50,
    pChange: 0.55,
    pe: 14.80,
    high52: 41200.00,
    low52: 32400.00,
  }
];

export const mockOfferDetails: StatutoryOfferDetails = {
  symbol: 'NTPCGREEN',
  companyName: 'NTPC Green Energy Limited (NGEL)',
  sectorName: 'Renewable Energy Utilities & Solar/Wind Power',
  listingExchanges: 'BSE, NSE',
  issueType: 'Mainboard',
  boardSegment: 'Mainboard',
  filingDateLabel: 'RHP · NOVEMBER 2024',
  issueStartDate: '2024-11-19',
  issueEndDate: '2024-11-22',
  pricingState: {
    status: 'RHP_PRICED',
    priceBandMin: 102,
    priceBandMax: 108,
    isContained: false
  },
  priceBandDisplay: '₹102 - ₹108',
  lotSize: 138,
  minCommitmentInr: 14904,
  issueSizeCr: 10000.00,
  totalOfferingShares: '925,925,925',
  freshIssueCr: 10000.00,
  ofsCr: 0.00,
  freshIssuePct: 100,
  ofsPct: 0,
  structureDisplay: '100% Fresh (₹10,000.00 Cr) · 0% OFS (Zero Exit)',
  leadManagers: [
    'IDBI Capital Markets & Securities Limited',
    'HDFC Bank Limited',
    'IIFL Securities Limited',
    'Nuvama Wealth Management Limited'
  ],
  rhpUrl: 'https://archives.nseindia.com/content/equities/IPO_RHP_NTPCGREEN.zip',
  anchorListUrl: 'https://www.nseindia.com/api/ipo-detail?symbol=NTPCGREEN',
  sebiEligibilityRoute: 'Regulation 6(2) 75% QIB Book Building',
  lockInDaysQIBAnchor: 90,
  lockInDaysPreIPOShareholders: 180,
  dickinsonStage: 'GROWTH',
  cashFlowPattern: '(+, -, +)',
  gcpAllocationCr: 2500.0,
  gcpAllocationPct: 25.0,
  isGcpCompliant: true,
};

export const mockSubscriptionBook: SubscriptionBook = {
  totalMultiple: 1.82,
  totalBidsShares: 1079540000,
  totalAmountCollectedCr: 11659.03,
  lastUpdated: '15-Nov-2026 13:30:00 IST',
  categories: [
    {
      category: 'Qualified Institutional Buyers (QIB)',
      sharesOffered: 258000000,
      sharesBid: 609240000,
      subscriptionMultiple: 2.36,
    },
    {
      category: 'Non-Institutional Investors (NII / HNI)',
      sharesOffered: 129000000,
      sharesBid: 109650000,
      subscriptionMultiple: 0.85,
    },
    {
      category: 'Retail Individual Investors (RII)',
      sharesOffered: 86000000,
      sharesBid: 131580000,
      subscriptionMultiple: 1.53,
    },
    {
      category: 'Eligible Employees / Shareholders',
      sharesOffered: 20000000,
      sharesBid: 32000000,
      subscriptionMultiple: 1.60,
    }
  ]
};

export const mockLivePeers: LivePeerComp[] = [
  {
    symbol: 'VBL',
    companyName: 'Varun Beverages Limited',
    lastPrice: 432.80,
    change: 3.45,
    pChange: 0.80,
    pe: 62.4,
    evEbitda: 31.8,
    evSales: 6.8,
    revenueCagr3Y: 28.4,
    ebitdaMargin: 23.1,
    roce: 27.8,
    cfoToEbitda: 0.88,
    high52: 520.00,
    low52: 345.00,
    marketCapCr: 140650.00,
    similarityScore: 84.5,
    isDrhpDeclared: false
  },
  {
    symbol: 'ADANIGREEN',
    companyName: 'Adani Green Energy Ltd',
    lastPrice: 1785.40,
    change: -14.20,
    pChange: -0.79,
    pe: 114.2,
    evEbitda: 36.4,
    evSales: 16.5,
    revenueCagr3Y: 33.2,
    ebitdaMargin: 68.4,
    roce: 8.4,
    cfoToEbitda: 0.76,
    high52: 2174.00,
    low52: 1220.00,
    marketCapCr: 282800.00,
    similarityScore: 92.1,
    isDrhpDeclared: true
  },
  {
    symbol: 'TATAPOWER',
    companyName: 'Tata Power Company Ltd',
    lastPrice: 412.30,
    change: 4.10,
    pChange: 1.00,
    pe: 34.5,
    evEbitda: 14.8,
    evSales: 2.2,
    revenueCagr3Y: 19.8,
    ebitdaMargin: 17.5,
    roce: 12.3,
    cfoToEbitda: 0.92,
    high52: 494.85,
    low52: 310.20,
    marketCapCr: 131750.00,
    similarityScore: 88.0,
    isDrhpDeclared: true
  },
  {
    symbol: 'SUZLON',
    companyName: 'Suzlon Energy Limited',
    lastPrice: 64.80,
    change: -0.85,
    pChange: -1.29,
    pe: 68.2,
    evEbitda: 32.1,
    evSales: 9.4,
    revenueCagr3Y: 26.5,
    ebitdaMargin: 16.8,
    roce: 21.2,
    cfoToEbitda: 0.81,
    high52: 86.04,
    low52: 36.10,
    marketCapCr: 88400.00,
    similarityScore: 78.4,
    isDrhpDeclared: false
  },
  {
    symbol: 'HINDUNILVR',
    companyName: 'Hindustan Unilever Ltd',
    lastPrice: 1992.90,
    change: -8.10,
    pChange: -0.40,
    pe: 48.6,
    evEbitda: 33.2,
    evSales: 7.9,
    revenueCagr3Y: 9.4,
    ebitdaMargin: 24.2,
    roce: 29.5,
    cfoToEbitda: 0.96,
    high52: 3035.00,
    low52: 1940.00,
    marketCapCr: 468200.00,
    similarityScore: 71.0,
    isDrhpDeclared: false
  }
];

export const mockHuberCalibration: HuberCalibrationResults = {
  metric: 'Price-to-Earnings (P/E)',
  declaredPeerMedian: 63.3,
  algorithmicPeerMedian: 28.5,
  drhpBiasIndex: 2.22,
  warrantedFairMultiple: 11.8,
  unbackedFrothPct: 227.1,
  formula: 'P/E = 4.21 + 0.48*(RevCAGR) + 0.35*(EBITDA%) + 0.22*(ROCE) - 1.15*(Debt/Equity)',
  coefficients: [
    { feature: 'Revenue CAGR 3Y (%)', weight: 0.482, tStat: 3.42 },
    { feature: 'EBITDA Margin (%)', weight: 0.351, tStat: 2.89 },
    { feature: 'ROCE (%)', weight: 0.224, tStat: 2.14 },
    { feature: 'CFO / EBITDA Cash Conversion', weight: 8.650, tStat: 3.91 },
    { feature: 'Total Debt / Equity (x)', weight: -1.150, tStat: -2.76 }
  ],
  rSquaredRobust: 0.742
};

export const mockMLScorecard: WalkForwardMLScorecardData = {
  fundamentalScore: 18.4,
  sentimentScore: 47.0,
  compositeRating: 'AVOID_HIGH_DRAWDOWN_RISK',
  prob180DOutperformance: 14.2,
  expectedMonth6LockinCAR: -10.4,
  lockinExpiryDate: '2025-05-22',
  walkForwardBacktestAccuracy: 78.4,
  shapTopFeatures: [
    {
      featureName: 'sloan_accrual_ratio',
      displayName: 'Sloan Accrual Ratio (+14.8%)',
      category: 'Forensic & Accruals',
      featureValue: '+14.8%',
      attributionValue: -0.42,
      isWarning: true
    },
    {
      featureName: 'unbacked_valuation_froth',
      displayName: 'Huber Valuation Froth (+227%)',
      category: 'Valuation Multiple',
      featureValue: '+227.1%',
      attributionValue: -0.38,
      isWarning: true
    },
    {
      featureName: 'drhp_peer_bias_index',
      displayName: 'DRHP Peer Cherry-Picking (2.22x)',
      category: 'Statutory Signal',
      featureValue: '2.22x',
      attributionValue: -0.29,
      isWarning: true
    },
    {
      featureName: 'fresh_issue_share',
      displayName: '100% Fresh Issue (Zero OFS)',
      category: 'Capital Structure',
      featureValue: '100%',
      attributionValue: +0.24,
      isWarning: false
    },
    {
      featureName: 'qib_subscription_multiple',
      displayName: 'QIB Anchor Institutional Demand (2.36x)',
      category: 'Market Sentiment',
      featureValue: '2.36x',
      attributionValue: +0.18,
      isWarning: false
    }
  ]
};

export const mockSEBICompliance: SEBIComplianceRecord = {
  researchAnalystRegNo: 'INH000018942 / SEBI (RA) Reg. 2014',
  analystName: 'ProfSur Quantitative Valuation Engine',
  verificationTimestamp: '2026-11-15T13:30:00Z',
  immutableReportHashSha256: '8b72e19d44a2b9187e8340d99ef83b28b7e283cb0f89832a8286a117cb4e297a',
  dataSources: [
    'NSE India Live Primary Feed (API Key ak_bmsc / nsit session)',
    'SEBI Statutory DRHP Filing (513-Page Restated Ind AS)',
    'RBI Commercial Paper & G-Sec Benchmark Yield Curve'
  ],
  regulationReferences: [
    'SEBI (ICDR) Regulations, 2018 (Schedule VI Part A - KPI & WACA Disclosure)',
    'SEBI (Research Analysts) Regulations, 2014 (Chapter III - Code of Conduct)',
    'Income Tax Act Section 56(2)(x) Fair Market Value Safeguards'
  ]
};

// Symbol-specific fallback mock datasets
export const hccbOfferDetails: StatutoryOfferDetails = {
  symbol: 'HCCB',
  companyName: 'Hindustan Coca-Cola Holdings Limited',
  sectorName: 'Non-Alcoholic Ready-to-Drink Beverages',
  listingExchanges: 'BSE, NSE',
  issueType: 'DRHP',
  boardSegment: 'Mainboard',
  filingDateLabel: 'DRHP · OCTOBER 2026',
  issueStartDate: 'Statutory DRHP',
  issueEndDate: 'Under Review (SEBI)',
  pricingState: {
    status: 'DRHP_UNPRICED',
    isContained: true
  },
  priceBandDisplay: 'Drafting / Unpriced (₹[●])',
  lotSize: null,
  minCommitmentInr: null,
  issueSizeCr: 9975.00,
  totalOfferingShares: '997,461,456',
  freshIssueCr: 0.00,
  freshIssueShares: '0 (Nil Issue)',
  ofsCr: 9975.00,
  ofsShares: '997,461,456',
  freshIssuePct: 0,
  ofsPct: 100,
  structureDisplay: '100% OFS (₹[●] Undisclosed) · 0% Fresh (Nil Issue)',
  leadManagers: [
    'Kotak Mahindra Capital Company Limited',
    'Citigroup Global Markets India Private Limited',
    'Morgan Stanley India Company Private Limited',
    'J.P. Morgan India Private Limited'
  ],
  rhpUrl: '',
  anchorListUrl: '',
  sebiEligibilityRoute: 'Regulation 6(2) 75% QIB Book Building',
  lockInDaysQIBAnchor: 90,
  lockInDaysPreIPOShareholders: 180,
  containmentReason: 'SEBI ICDR 2018 statutory guidelines, real analytical processing (Offer Valuation, WACC/ROIC, Reverse DCF, and Board Deck generation) is strictly BLOCKED until the 513-page parent DRHP is fully indexed and its evidence ledger reviewed and accepted in Tab 2 (Provenance Ledger). All values shown below are candidate unreviewed disclosures and cannot be used for investment, credit, or underwriting decisions.',
  dickinsonStage: 'MATURE (CASH COW)',
  cashFlowPattern: '(+, -, -)',
  gcpAllocationCr: 0.0,
  gcpAllocationPct: 0.0,
  isGcpCompliant: true,
};

export const hccbSubscriptionBook: SubscriptionBook = {
  totalMultiple: 0.0,
  totalBidsShares: 0,
  totalAmountCollectedCr: 0.0,
  lastUpdated: 'DRHP Under Statutory SEBI Review',
  categories: [
    {
      category: 'Qualified Institutional Buyers (QIB)',
      sharesOffered: 748096092,
      sharesBid: 0,
      subscriptionMultiple: 0.0,
    },
    {
      category: 'Non-Institutional Investors (NII / HNI)',
      sharesOffered: 149619218,
      sharesBid: 0,
      subscriptionMultiple: 0.0,
    },
    {
      category: 'Retail Individual Investors (RII)',
      sharesOffered: 99746146,
      sharesBid: 0,
      subscriptionMultiple: 0.0,
    }
  ]
};

export const hccbLivePeers: LivePeerComp[] = [
  {
    symbol: 'VBL',
    companyName: 'Varun Beverages Limited',
    lastPrice: 432.80,
    change: 3.45,
    pChange: 0.80,
    pe: 62.4,
    evEbitda: 31.8,
    evSales: 6.8,
    revenueCagr3Y: 28.4,
    ebitdaMargin: 23.1,
    roce: 27.8,
    cfoToEbitda: 0.88,
    high52: 520.00,
    low52: 345.00,
    marketCapCr: 140650.00,
    similarityScore: 94.5,
    isDrhpDeclared: true
  },
  {
    symbol: 'TATACONSUM',
    companyName: 'Tata Consumer Products Limited',
    lastPrice: 945.20,
    change: 6.80,
    pChange: 0.72,
    pe: 55.6,
    evEbitda: 27.1,
    evSales: 4.2,
    revenueCagr3Y: 11.2,
    ebitdaMargin: 15.3,
    roce: 13.8,
    cfoToEbitda: 0.84,
    high52: 1250.00,
    low52: 890.00,
    marketCapCr: 88400.00,
    similarityScore: 88.0,
    isDrhpDeclared: true
  },
  {
    symbol: 'DABUR',
    companyName: 'Dabur India Limited',
    lastPrice: 512.40,
    change: -2.10,
    pChange: -0.41,
    pe: 48.2,
    evEbitda: 28.5,
    evSales: 4.9,
    revenueCagr3Y: 8.6,
    ebitdaMargin: 19.5,
    roce: 21.4,
    cfoToEbitda: 0.92,
    high52: 672.00,
    low52: 489.00,
    marketCapCr: 90750.00,
    similarityScore: 86.5,
    isDrhpDeclared: false
  },
  {
    symbol: 'HINDUNILVR',
    companyName: 'Hindustan Unilever Limited',
    lastPrice: 2410.50,
    change: 12.30,
    pChange: 0.51,
    pe: 54.1,
    evEbitda: 36.2,
    evSales: 9.1,
    revenueCagr3Y: 7.8,
    ebitdaMargin: 23.8,
    roce: 29.5,
    cfoToEbitda: 0.96,
    high52: 3034.00,
    low52: 2170.00,
    marketCapCr: 566400.00,
    similarityScore: 82.0,
    isDrhpDeclared: false
  },
  {
    symbol: 'NESTLEIND',
    companyName: 'Nestle India Limited',
    lastPrice: 2245.00,
    change: -8.40,
    pChange: -0.37,
    pe: 68.9,
    evEbitda: 44.5,
    evSales: 11.2,
    revenueCagr3Y: 10.5,
    ebitdaMargin: 24.2,
    roce: 48.2,
    cfoToEbitda: 0.91,
    high52: 2770.00,
    low52: 2140.00,
    marketCapCr: 216500.00,
    similarityScore: 80.5,
    isDrhpDeclared: false
  }
];

export const hccbHuberCalibration: HuberCalibrationResults = {
  metric: 'P/E Multiple',
  declaredPeerMedian: 58.8,
  algorithmicPeerMedian: 54.1,
  drhpBiasIndex: 1.09,
  warrantedFairMultiple: 48.5,
  unbackedFrothPct: 0.0,
  formula: 'P/E = 14.2 + 0.48*(RevCAGR) + 0.82*(EBITDA%) + 0.35*(ROCE) + 5.2*(CFO/EBITDA)',
  coefficients: [
    { feature: 'Revenue CAGR (3-Yr)', weight: 0.48, tStat: 3.82 },
    { feature: 'EBITDA Margin (%)', weight: 0.82, tStat: 4.15 },
    { feature: 'ROCE (%)', weight: 0.35, tStat: 2.94 },
    { feature: 'CFO / EBITDA Conversion', weight: 5.20, tStat: 4.51 }
  ],
  rSquaredRobust: 0.8624
};

export const hccbMLScorecard: WalkForwardMLScorecardData = {
  fundamentalScore: 82.5,
  sentimentScore: 71.0,
  compositeRating: 'STRONG_BUY_ALPHA',
  prob180DOutperformance: 76.2,
  expectedMonth6LockinCAR: 14.8,
  lockinExpiryDate: '180 Days Post-Listing',
  walkForwardBacktestAccuracy: 81.2,
  shapTopFeatures: [
    {
      featureName: 'cfo_ebitda_conversion',
      displayName: 'FMCG Cash Flow Conversion (0.88x)',
      category: 'Forensic & Accruals',
      featureValue: '0.88x',
      attributionValue: 0.38,
      isWarning: false
    },
    {
      featureName: 'funded_debt_ratio',
      displayName: 'Pristine Zero Funded Bank Debt',
      category: 'Capital Structure',
      featureValue: '₹0.00 Cr',
      attributionValue: 0.32,
      isWarning: false
    },
    {
      featureName: 'ofs_dilution_structure',
      displayName: '100% OFS Structure (Bottling Investments Group)',
      category: 'Statutory Signal',
      featureValue: '100% OFS',
      attributionValue: -0.15,
      isWarning: true
    },
    {
      featureName: 'beneish_accrual_quality',
      displayName: 'Beneish M-Score (-2.84, Safe Zone)',
      category: 'Forensic & Accruals',
      featureValue: '-2.84',
      attributionValue: 0.22,
      isWarning: false
    }
  ]
};

// Swiggy fallback dataset
export const swiggyOfferDetails: StatutoryOfferDetails = {
  symbol: 'SWIGGY',
  companyName: 'Swiggy Limited',
  issueType: 'Mainboard',
  issueStartDate: '2024-11-06',
  issueEndDate: '2024-11-08',
  pricingState: {
    status: 'RHP_PRICED',
    priceBandMin: 371,
    priceBandMax: 390,
    isContained: false
  },
  lotSize: 38,
  issueSizeCr: 11327.43,
  freshIssueCr: 4499.00,
  ofsCr: 6828.43,
  leadManagers: ['Kotak Mahindra Capital', 'Citigroup Global Markets India', 'Jefferies India', 'Avendus Capital'],
  rhpUrl: '',
  anchorListUrl: '',
  sebiEligibilityRoute: 'Regulation 6(2) 75% QIB Book Building',
  lockInDaysQIBAnchor: 90,
  lockInDaysPreIPOShareholders: 180,
};

// Waaree fallback dataset
export const waareeOfferDetails: StatutoryOfferDetails = {
  symbol: 'WAAREE',
  companyName: 'Waaree Energies Limited',
  issueType: 'Mainboard',
  issueStartDate: '2024-10-21',
  issueEndDate: '2024-10-23',
  pricingState: {
    status: 'RHP_PRICED',
    priceBandMin: 1427,
    priceBandMax: 1503,
    isContained: false
  },
  lotSize: 9,
  issueSizeCr: 4321.44,
  freshIssueCr: 3600.00,
  ofsCr: 721.44,
  leadManagers: ['Axis Capital Limited', 'IIFL Securities Limited', 'Jefferies India', 'Nomura Financial Advisory'],
  rhpUrl: '',
  anchorListUrl: '',
  sebiEligibilityRoute: 'Regulation 6(1) Net Tangible Assets & Profitability',
  lockInDaysQIBAnchor: 90,
  lockInDaysPreIPOShareholders: 180,
};

function getFallbackForSymbol(symbol: string) {
  const s = symbol.toUpperCase();
  if (s === 'HCCB' || s.includes('COCA')) {
    return {
      indices: mockMarketIndices,
      offer: hccbOfferDetails,
      subscription: hccbSubscriptionBook,
      peers: hccbLivePeers,
      calibration: hccbHuberCalibration,
      scorecard: hccbMLScorecard,
      compliance: mockSEBICompliance
    };
  }
  if (s === 'SWIGGY') {
    return {
      indices: mockMarketIndices,
      offer: swiggyOfferDetails,
      subscription: mockSubscriptionBook,
      peers: mockLivePeers,
      calibration: mockHuberCalibration,
      scorecard: mockMLScorecard,
      compliance: mockSEBICompliance
    };
  }
  if (s === 'WAAREE') {
    return {
      indices: mockMarketIndices,
      offer: waareeOfferDetails,
      subscription: mockSubscriptionBook,
      peers: mockLivePeers,
      calibration: mockHuberCalibration,
      scorecard: mockMLScorecard,
      compliance: mockSEBICompliance
    };
  }
  return {
    indices: mockMarketIndices,
    offer: mockOfferDetails,
    subscription: mockSubscriptionBook,
    peers: mockLivePeers,
    calibration: mockHuberCalibration,
    scorecard: mockMLScorecard,
    compliance: mockSEBICompliance
  };
}

// API Service Functions
export async function fetchLiveMarketData(symbol: string = 'NTPCGREEN') {
  try {
    const res = await fetch(`http://localhost:8000/api/pre-ipo/market-status?symbol=${encodeURIComponent(symbol)}`);
    if (!res.ok) throw new Error('Backend offline');
    const data = await res.json();
    if (data?.offer && !data.offer.pricingState) {
      if (data.offer.isPriceUndisclosed || !data.offer.priceBandMax) {
        data.offer.pricingState = {
          status: 'DRHP_UNPRICED',
          isContained: Boolean(data.offer.isContained)
        };
      } else {
        data.offer.pricingState = {
          status: 'RHP_PRICED',
          priceBandMin: Number(data.offer.priceBandMin ?? 0),
          priceBandMax: Number(data.offer.priceBandMax ?? 0),
          isContained: Boolean(data.offer.isContained)
        };
      }
    }
    return data;
  } catch {
    return getFallbackForSymbol(symbol);
  }
}
