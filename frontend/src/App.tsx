import React, { useState, useEffect, useRef } from 'react';
import { HeaderTicker } from './components/HeaderTicker';
import { SidebarNav, TerminalView } from './components/SidebarNav';
import { CompactCockpitHUD } from './components/CompactCockpitHUD';
import { SubscriptionBookBar } from './components/SubscriptionBookBar';
import { LivePeerCompsTable } from './components/LivePeerCompsTable';
import { HuberCalibrationCard } from './components/HuberCalibrationCard';
import { WalkForwardMLScorecard } from './components/WalkForwardMLScorecard';
import { SHAPWaterfallChart } from './components/SHAPWaterfallChart';
import { SEBIComplianceStamp } from './components/SEBIComplianceStamp';
import { IngestModal } from './components/IngestModal';
import { AnalystInsightDrawer } from './components/AnalystInsightDrawer';
import { EvidenceInterpretationPanel } from './components/shared/EvidenceInterpretationPanel';

// Specialized Vault Views
import { ProvenanceLedgerVault } from './components/vaults/ProvenanceLedgerVault';
import { RedFlagScannerVault } from './components/vaults/RedFlagScannerVault';
import { UnlistedArbitrageVault } from './components/vaults/UnlistedArbitrageVault';
import { StressWorkpapersVault } from './components/vaults/StressWorkpapersVault';
import { EconometricLabVault } from './components/vaults/EconometricLabVault';
import { InvestorQAVault } from './components/vaults/InvestorQAVault';
import { StakeholderLensVault } from './components/vaults/StakeholderLensVault';
import { ContingentLitigationVault } from './components/vaults/ContingentLitigationVault';
import { UnitEconomicsVault } from './components/vaults/UnitEconomicsVault';
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
import { VaultId } from './types/terminal';

export const App: React.FC = () => {
  const [activeView, setActiveView] = useState<TerminalView>('market_demand');
  const [isCockpitExpanded, setIsCockpitExpanded] = useState<boolean>(false);
  const mainScrollRef = useRef<HTMLDivElement>(null);

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
  const refreshTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  useEffect(() => {
    let isCurrent = true;
    const controller = new AbortController();
    setIsRefreshing(true);

    fetchLiveMarketData(selectedSymbol, controller.signal)
      .then(data => {
        if (!isCurrent || !data) return;
        if (data.indices) setIndices(data.indices);
        if (data.offer) setOffer(data.offer);
        if (data.subscription) setSubscription(data.subscription);
        if (data.peers) setPeers(data.peers);
        if (data.calibration) setCalibration(data.calibration);
        if (data.scorecard) setScorecard(data.scorecard);
        if (data.compliance) setCompliance(data.compliance);
      })
      .catch((err: unknown) => {
        if (err instanceof DOMException && err.name === 'AbortError') return;
        console.warn('Failed to load market data for', selectedSymbol, err);
      })
      .finally(() => {
        if (isCurrent) {
          if (refreshTimerRef.current) clearTimeout(refreshTimerRef.current);
          refreshTimerRef.current = setTimeout(() => {
            if (isCurrent) setIsRefreshing(false);
          }, 300);
        }
      });

    return () => {
      isCurrent = false;
      controller.abort();
      if (refreshTimerRef.current) clearTimeout(refreshTimerRef.current);
    };
  }, [selectedSymbol]);

  // Explicit manual refresh action
  const handleManualRefresh = () => {
    setIsRefreshing(true);
    fetchLiveMarketData(selectedSymbol)
      .then(data => {
        if (!data) return;
        if (data.indices) setIndices(data.indices);
        if (data.offer) setOffer(data.offer);
        if (data.subscription) setSubscription(data.subscription);
        if (data.peers) setPeers(data.peers);
        if (data.calibration) setCalibration(data.calibration);
        if (data.scorecard) setScorecard(data.scorecard);
        if (data.compliance) setCompliance(data.compliance);
      })
      .finally(() => {
        setTimeout(() => setIsRefreshing(false), 300);
      });
  };

  // Handle left navigation change with instantaneous auto-reset to top
  const handleViewChange = (newView: TerminalView) => {
    setActiveView(newView);
    // Smooth/instant scroll reset so target vault opens cleanly at y=0
    mainScrollRef.current?.scrollTo({ top: 0, behavior: 'instant' });
  };

  const handleIngestSuccess = (newDeal: {
    symbol: string;
    companyName: string;
    sizeCr: number;
    filingType: string;
    sector: string;
  }) => {
    // Only update state; the useEffect([selectedSymbol]) handles the single canonical fetch
    setSelectedSymbol(newDeal.symbol);
  };

  return (
    <div className="h-screen w-full bg-[#090D12] text-slate-100 flex flex-col font-sans overflow-hidden">
      {/* Top Header Ticker Bar */}
      <HeaderTicker
        indices={indices}
        onRefresh={handleManualRefresh}
        isRefreshing={isRefreshing}
      />

      {/* Main Terminal Body */}
      <div className="flex-1 flex flex-col lg:flex-row overflow-hidden min-h-0 w-full">
        {/* Left Navigation Sidebar (100vh Viewport Locked) */}
        <SidebarNav
          activeView={activeView}
          onViewChange={handleViewChange}
          selectedSymbol={selectedSymbol}
          onSymbolChange={setSelectedSymbol}
          onOpenIngestModal={() => setIsIngestModalOpen(true)}
        />

        {/* Central Content Area with Pinned Micro-HUD */}
        <div className="flex-1 flex flex-col overflow-hidden min-w-0 min-h-0 h-full">
          {/* Pinned 46px Compact Cockpit Telemetry HUD */}
          <CompactCockpitHUD
            offer={offer}
            calibration={calibration}
            isExpanded={isCockpitExpanded}
            onToggleExpand={() => setIsCockpitExpanded(!isCockpitExpanded)}
            onSelectVault={(v: VaultId) => handleViewChange(v)}
          />

          {/* Dedicated Vault Workspace (Scrollable Canvas at y=0) */}
          <main ref={mainScrollRef} className="flex-1 p-4 lg:p-6 overflow-y-auto space-y-6 min-h-0">
            <div className="space-y-6 max-w-7xl mx-auto">
              {/* Vault 1: Market Demand & Order Book */}
              {(activeView === 'market_demand' || activeView === 'overview') && (
                <div className="space-y-6 animate-fade-in">
                  <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                    <SubscriptionBookBar subscription={subscription} />
                    <WalkForwardMLScorecard scorecard={scorecard} />
                  </div>
                  <SHAPWaterfallChart features={scorecard.shapTopFeatures} />
                  {offer?.interpretations?.ic_stance_mandate && (
                    <EvidenceInterpretationPanel
                      interpretation={offer.interpretations.ic_stance_mandate}
                      title="Vault 1: Market Demand & Allocation Directive"
                    />
                  )}
                  <AnalystInsightDrawer
                    title="Market Demand & Order Book Intelligence"
                    offer={offer}
                    vaultId="market_demand"
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
                <div className="space-y-6 animate-fade-in">
                  <LivePeerCompsTable peers={peers} />
                  {offer?.interpretations?.valuation_multiple && (
                    <EvidenceInterpretationPanel
                      interpretation={offer.interpretations.valuation_multiple}
                      title="Vault 2: Peer Comps & Multiple Disparity Intelligence"
                    />
                  )}
                  <AnalystInsightDrawer
                    title="Live Peer Comps & WACA Multiple Step-Up Synthesizer"
                    offer={offer}
                    vaultId="peer_comps"
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
                <div className="space-y-6 animate-fade-in">
                  <HuberCalibrationCard calibration={calibration} />
                  {offer?.interpretations?.valuation_multiple && (
                    <EvidenceInterpretationPanel
                      interpretation={offer.interpretations.valuation_multiple}
                      title="Vault 3: Huber RLM Econometric Benchmark Intelligence"
                    />
                  )}
                  <LivePeerCompsTable peers={peers} />
                  <AnalystInsightDrawer
                    title="Huber M-Estimator & Econometric Selection Bias Synthesizer"
                    offer={offer}
                    vaultId="huber_studio"
                  />
                </div>
              )}

              {/* Vault 4: Provenance Evidence Ledger */}
              {activeView === 'provenance_ledger' && (
                <div className="animate-fade-in">
                  <ProvenanceLedgerVault offer={offer} />
                </div>
              )}

              {/* Vault 5: Econometric & Forensic Lab */}
              {(activeView === 'stress_workpapers' || activeView === 'econometric_lab') && (
                <div className="animate-fade-in">
                  <EconometricLabVault offer={offer} />
                </div>
              )}

              {/* Vault 6: Institutional Q&A */}
              {activeView === 'investor_qa' && (
                <div className="animate-fade-in">
                  <InvestorQAVault offer={offer} />
                </div>
              )}

              {/* Vault 7: 6-Persona Stakeholder Lens */}
              {activeView === 'stakeholder_lens' && (
                <div className="animate-fade-in">
                  <StakeholderLensVault offer={offer} />
                </div>
              )}

              {/* Vault 8: 6-Rule Red-Flag Scanner */}
              {activeView === 'red_flag_scanner' && (
                <div className="animate-fade-in">
                  <RedFlagScannerVault offer={offer} />
                </div>
              )}

              {/* Vault 9: Contingent Litigation Radar */}
              {activeView === 'contingent_litigation' && (
                <div className="animate-fade-in">
                  <ContingentLitigationVault offer={offer} />
                </div>
              )}

              {/* Vault 10: Unit Economics & Operational Scale */}
              {activeView === 'unit_economics' && (
                <div className="animate-fade-in">
                  <UnitEconomicsVault offer={offer} />
                </div>
              )}

              {/* Vault 11: Unlisted Post-Tax Arbitrage */}
              {activeView === 'unlisted_arbitrage' && (
                <div className="animate-fade-in">
                  <UnlistedArbitrageVault offer={offer} />
                </div>
              )}

              {/* Vault 12: IC Stance & Board Deck Export */}
              {activeView === 'ic_board_deck' && (
                <div className="space-y-6 animate-fade-in">
                  <ICBoardDeckVault offer={offer} />
                  <SEBIComplianceStamp compliance={compliance} />
                </div>
              )}
            </div>
          </main>
        </div>
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
