import React, { useState, useEffect } from 'react';
import { HeaderTicker } from './components/HeaderTicker';
import { SidebarNav, TerminalView } from './components/SidebarNav';
import { StatutoryOfferHero } from './components/StatutoryOfferHero';
import { LintelTowers } from './components/LintelTowers';
import { SubscriptionBookBar } from './components/SubscriptionBookBar';
import { LivePeerCompsTable } from './components/LivePeerCompsTable';
import { HuberCalibrationCard } from './components/HuberCalibrationCard';
import { WalkForwardMLScorecard } from './components/WalkForwardMLScorecard';
import { SHAPWaterfallChart } from './components/SHAPWaterfallChart';
import { SEBIComplianceStamp } from './components/SEBIComplianceStamp';
import { IngestModal } from './components/IngestModal';
import { AnalystInsightDrawer } from './components/AnalystInsightDrawer';

// Specialized Vault Views
import { ProvenanceLedgerVault } from './components/vaults/ProvenanceLedgerVault';
import { RedFlagScannerVault } from './components/vaults/RedFlagScannerVault';
import { UnlistedArbitrageVault } from './components/vaults/UnlistedArbitrageVault';
import { StressWorkpapersVault } from './components/vaults/StressWorkpapersVault';
import { InvestorQAVault } from './components/vaults/InvestorQAVault';
import { StakeholderLensVault } from './components/vaults/StakeholderLensVault';
import { ICBoardDeckVault } from './components/vaults/ICBoardDeckVault';

import {
  fetchLiveMarketData,
  mockMarketIndices,
  mockOfferDetails,
  mockSubscriptionBook,
  mockLivePeers,
  mockHuberCalibration,
  mockMLScorecard,
  mockSEBICompliance
} from './services/dataService';
import { CheckCircle2, FileText, AlertTriangle } from 'lucide-react';

export const App: React.FC = () => {
  const [activeView, setActiveView] = useState<TerminalView>('market_demand');

  // Parse initial symbol from URL query parameter if present
  const [selectedSymbol, setSelectedSymbol] = useState<string>(() => {
    try {
      const params = new URLSearchParams(window.location.search);
      const urlSymbol = params.get('issuer') || params.get('symbol');
      if (urlSymbol) {
        const u = urlSymbol.toUpperCase();
        if (['NTPCGREEN', 'HCCB', 'SWIGGY', 'WAAREE'].includes(u)) {
          return u;
        }
      }
    } catch {
      // Fallback
    }
    return 'NTPCGREEN';
  });

  const [isRefreshing, setIsRefreshing] = useState<boolean>(false);
  const [isIngestModalOpen, setIsIngestModalOpen] = useState<boolean>(false);

  const [indices, setIndices] = useState(mockMarketIndices);
  const [offer, setOffer] = useState(mockOfferDetails);
  const [subscription, setSubscription] = useState(mockSubscriptionBook);
  const [peers, setPeers] = useState(mockLivePeers);
  const [calibration, setCalibration] = useState(mockHuberCalibration);
  const [scorecard, setScorecard] = useState(mockMLScorecard);
  const [compliance, setCompliance] = useState(mockSEBICompliance);

  const loadData = async (symbolOverride?: string) => {
    const symbolToQuery = symbolOverride || selectedSymbol;
    setIsRefreshing(true);
    try {
      const data = await fetchLiveMarketData(symbolToQuery);
      if (data) {
        if (data.indices) setIndices(data.indices);
        if (data.offer) setOffer(data.offer);
        if (data.subscription) setSubscription(data.subscription);
        if (data.peers) setPeers(data.peers);
        if (data.calibration) setCalibration(data.calibration);
        if (data.scorecard) setScorecard(data.scorecard);
        if (data.compliance) setCompliance(data.compliance);
      }
    } finally {
      setTimeout(() => setIsRefreshing(false), 500);
    }
  };

  useEffect(() => {
    loadData(selectedSymbol);
  }, [selectedSymbol]);

  const handleIngestSuccess = (newDeal: {
    symbol: string;
    companyName: string;
    sizeCr: number;
    filingType: string;
    sector: string;
  }) => {
    setSelectedSymbol(newDeal.symbol);
    loadData(newDeal.symbol);
  };

  return (
    <div className="min-h-screen bg-[#090D12] text-slate-100 flex flex-col font-sans">
      {/* Top Header Ticker Bar */}
      <HeaderTicker
        indices={indices}
        onRefresh={() => loadData(selectedSymbol)}
        isRefreshing={isRefreshing}
      />

      {/* Main Terminal Body */}
      <div className="flex-1 flex flex-col lg:flex-row overflow-hidden">
        {/* Left Navigation Sidebar */}
        <SidebarNav
          activeView={activeView}
          onViewChange={setActiveView}
          selectedSymbol={selectedSymbol}
          onSymbolChange={setSelectedSymbol}
          onOpenIngestModal={() => setIsIngestModalOpen(true)}
        />

        {/* Central Content Area */}
        <main className="flex-1 p-4 lg:p-6 overflow-y-auto space-y-6">
          <div className="space-y-6 max-w-7xl mx-auto">
            {/* ========================================================= */}
            {/* PERSISTENT TOP COCKPIT (DUAL-LAYER ARCHITECTURE <= 38%)   */}
            {/* ========================================================= */}
            <div className="space-y-4">
              {/* Global Tri-State Ledger Counter Strip */}
              <div className="flex items-center justify-between text-xs font-mono py-1 px-2 border-b border-[#1E2B3E]">
                <span className="text-slate-400 font-semibold">STATUTORY EVIDENCE VERIFICATION LEDGER:</span>
                <div className="flex items-center gap-2">
                  <span className="px-2 py-0.5 rounded bg-emerald-950/70 border border-emerald-800 text-emerald-400 font-bold flex items-center gap-1">
                    <CheckCircle2 className="w-3 h-3 text-emerald-400" />
                    36 VERIFIED
                  </span>
                  <span className="px-2 py-0.5 rounded bg-slate-800/80 border border-slate-700 text-slate-300 font-bold flex items-center gap-1">
                    <FileText className="w-3 h-3 text-slate-400" />
                    4 RHP PENDING
                  </span>
                  <span className="px-2 py-0.5 rounded bg-amber-950/70 border border-amber-800 text-amber-400 font-bold flex items-center gap-1">
                    <AlertTriangle className="w-3 h-3 text-amber-400" />
                    2 RECONFIRM
                  </span>
                </div>
              </div>

              {/* Statutory Offer Hero Header */}
              <StatutoryOfferHero offer={offer} />

              {/* Lintel Towers: Tower 1, Tower 2, Tower 3 */}
              <LintelTowers offer={offer} calibration={calibration} />
            </div>

            {/* ========================================================= */}
            {/* SPECIALIZED VAULT WORKSPACE AREA (>= 62% LOWER WORKSPACE) */}
            {/* ========================================================= */}

            {/* Vault 1: Market Demand & Order Book */}
            {(activeView === 'market_demand' || activeView === 'overview') && (
              <div className="space-y-6">
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                  <SubscriptionBookBar subscription={subscription} />
                  <WalkForwardMLScorecard scorecard={scorecard} />
                </div>
                <SHAPWaterfallChart features={scorecard.shapTopFeatures} />
                <AnalystInsightDrawer
                  title="Market Demand & Order Book Intelligence"
                  narrative={{
                    sectorContext: "QIB Anchor demand serves as the foundational liquidity benchmark. High institutional anchor allocation reduces listing day retail volatility.",
                    lifecyclePrecedents: "Mega public offerings with heavy anchor subscription historically achieved 76% higher listing day survival during market drawdowns.",
                    icDirectives: "Cap retail subscription leverage. Mandate that QIB tranche achieves minimum 1.5x book coverage before allocating high-ticket capital.",
                    riskRadar: "Thin non-institutional HNI books expose the stock to listing day liquidity air-pockets if anchor lock-in selling commences at Day 90."
                  }}
                />
              </div>
            )}

            {/* Vault 2: Live Peer Comps & WACA Matrix */}
            {activeView === 'peer_comps' && (
              <div className="space-y-6">
                <LivePeerCompsTable peers={peers} />
                <AnalystInsightDrawer
                  title="Live Peer Comps & WACA Multiple Step-Up Synthesizer"
                  narrative={{
                    sectorContext: "Peers in Indian renewables and FMCG trade on diverging multiples: capital-intensive asset owners at 18-24x EV/EBITDA, FMCG bottlers at 45-55x P/E.",
                    lifecyclePrecedents: "Waaree Energies maintained premium pricing due to integrated module manufacturing, whereas pure-play solar EPC peers traded at 30% discount.",
                    icDirectives: "Require that Upper Price Band does not exceed 2.50x of the statutory 18-Month Weighted Average Cost of Acquisition (WACA).",
                    riskRadar: "Multiple compression risk is acute if peer median de-rates during the 3-day book building window."
                  }}
                />
              </div>
            )}

            {/* Vault 3: Huber Econometric Studio & Cones */}
            {activeView === 'huber_studio' && (
              <div className="space-y-6">
                <HuberCalibrationCard calibration={calibration} />
                <LivePeerCompsTable peers={peers} />
              </div>
            )}

            {/* Vault 4: Provenance Evidence Ledger */}
            {activeView === 'provenance_ledger' && (
              <ProvenanceLedgerVault offer={offer} />
            )}

            {/* Vault 5: 2D Stress Workpapers */}
            {activeView === 'stress_workpapers' && (
              <StressWorkpapersVault offer={offer} />
            )}

            {/* Vault 6: Institutional Q&A */}
            {activeView === 'investor_qa' && (
              <InvestorQAVault offer={offer} />
            )}

            {/* Vault 7: 6-Persona Stakeholder Lens */}
            {activeView === 'stakeholder_lens' && (
              <StakeholderLensVault offer={offer} />
            )}

            {/* Vault 8: 6-Rule Red-Flag Scanner */}
            {activeView === 'red_flag_scanner' && (
              <RedFlagScannerVault offer={offer} />
            )}

            {/* Vault 9: Unlisted Post-Tax Arbitrage */}
            {activeView === 'unlisted_arbitrage' && (
              <UnlistedArbitrageVault offer={offer} />
            )}

            {/* Vault 10: IC Stance & Board Deck Export */}
            {activeView === 'ic_board_deck' && (
              <div className="space-y-6">
                <ICBoardDeckVault offer={offer} />
                <SEBIComplianceStamp compliance={compliance} />
              </div>
            )}
          </div>
        </main>
      </div>

      {/* Ingest Modal (Option A) */}
      <IngestModal
        isOpen={isIngestModalOpen}
        onClose={() => setIsIngestModalOpen(false)}
        onIngestSuccess={handleIngestSuccess}
      />
    </div>
  );
};

export default App;
