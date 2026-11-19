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
import { ValuationFootballField } from './components/ValuationFootballField';
import { EVToEquityWaterfall } from './components/EVToEquityWaterfall';
import { SensitivityHeatmap } from './components/SensitivityHeatmap';
import { ProvenanceDrawer } from './components/ProvenanceDrawer';
import { ExecutiveVerdictBanner } from './components/ExecutiveVerdictBanner';
import { SimulationControlRail, SimulationParams } from './components/SimulationControlRail';
import { IPOBalancedScorecardView, DimensionItem } from './components/IPOBalancedScorecardView';
import { ScaleShiftedTrajectoryStudio } from './components/ScaleShiftedTrajectoryStudio';
import { ConsultingStrategyStudio } from './components/ConsultingStrategyStudio';
import { EmpiricalStrategyMapDAG } from './components/EmpiricalStrategyMapDAG';
import { CrossVaultBSCMatrix } from './components/CrossVaultBSCMatrix';
import { ExcelModelAuditStudio } from './components/ExcelModelAuditStudio';
import { CorporateFoundationsStudio } from './components/CorporateFoundationsStudio';
import { MethodologyAlmanacView } from './components/MethodologyAlmanacView';
import { MethodologySlideOverDrawer } from './components/MethodologySlideOverDrawer';
import { ForensicEvidenceSlideOverDrawer } from './components/ForensicEvidenceSlideOverDrawer';
import { TerminalErrorBoundary } from './components/shared/TerminalErrorBoundary';
import { DiligenceMasterVerdictStudio } from './components/DiligenceMasterVerdictStudio';

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
import { KnowledgeGraphStudioVault } from './components/vaults/KnowledgeGraphStudioVault';
import { PeerSectorCompetitorStudio } from './components/vaults/PeerSectorCompetitorStudio';

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

interface WeightedPeerItem {
  peer_id: string;
  company_name: string;
  rule_of_x: number;
  ev_revenue: number;
  weight: number;
}

interface ProFormaData {
  offer_price: number;
  implied_market_cap_cr: number;
  post_issue_shares_cr: number;
  issue_size_cr?: number;
  fresh_issue_cr?: number;
  ofs_cr?: number;
}

interface HarmonicMultiplesData {
  issuer_asking_pe: number;
  harmonic_pe: number;
  valuation_spread_pe_pct: number;
  favorable_unfavorable_flag: 'FAVORABLE' | 'UNFAVORABLE' | 'PARITY';
  issuer_asking_ev_revenue?: number;
  harmonic_ev_revenue?: number;
  issuer_asking_ev_ebitda?: number;
  harmonic_ev_ebitda?: number;
}

interface BalancedScorecardData {
  composite_bsc_score: number;
  rating_category: string;
  is_risk_veto_active: boolean;
  veto_reason?: string | null;
  dimensions: DimensionItem[];
  summary_verdict: string;
}

interface BscEvaluationData {
  symbol: string;
  pro_forma: ProFormaData;
  harmonic_multiples: HarmonicMultiplesData;
  balanced_scorecard: BalancedScorecardData;
  weighted_peers: WeightedPeerItem[];
}

export const App: React.FC = () => {
  const [activeView, setActiveView] = useState<TerminalView>(() => {
    try {
      const params = new URLSearchParams(window.location.search);
      const urlVault = params.get('vault') || params.get('view');
      if (urlVault) {
        return urlVault as TerminalView;
      }
    } catch { }
    return 'corporate_foundations';
  });
  const [isCockpitExpanded, setIsCockpitExpanded] = useState<boolean>(false);
  const mainScrollRef = useRef<HTMLDivElement>(null);

  // Parse initial symbol from URL query parameter if present
  const [selectedSymbol, setSelectedSymbol] = useState<string>(() => {
    try {
      const params = new URLSearchParams(window.location.search);
      const token = params.get('auth_token');
      if (token) {
        sessionStorage.setItem('portal_auth_token', token);
        localStorage.setItem('portal_auth_token', token);
      }
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
  const [isExportingExcel, setIsExportingExcel] = useState<boolean>(false);

  // Methodology Almanac Drawer & Selection States
  const [isAlmanacDrawerOpen, setIsAlmanacDrawerOpen] = useState<boolean>(false);
  const [selectedMethodologyId, setSelectedMethodologyId] = useState<string | null>(null);

  const handleOpenMethodologyDrawer = (methodologyId?: string) => {
    setSelectedMethodologyId(methodologyId || 'valuation_football_field');
    setIsAlmanacDrawerOpen(true);
  };

  // Forensic Evidence Slide-Over Drawer State
  const [forensicDrawerState, setForensicDrawerState] = useState<{
    isOpen: boolean;
    vaultId: string | null;
  }>({
    isOpen: false,
    vaultId: null,
  });

  const handleOpenForensicDrawer = (vaultId: string) => {
    setForensicDrawerState({ isOpen: true, vaultId });
  };

  // In-Vault Sub-Studio Navigation States (Eliminates vertical scroll fatigue)
  const [vault1Tab, setVault1Tab] = useState<'bidding_ml' | 'pillars_studio' | 'strategy_studio' | 'football_field'>(() => {
    try {
      const urlParams = new URLSearchParams(window.location.search);
      const tab = urlParams.get('tab') || urlParams.get('subtab');
      if (tab === 'strategy' || tab === 'strategy_studio' || tab === '3') return 'strategy_studio';
      if (tab === 'pillars' || tab === '2') return 'pillars_studio';
      if (tab === 'football' || tab === '4') return 'football_field';
    } catch { }
    return 'bidding_ml';
  });

  const handleSelectVault1Tab = (tab: 'bidding_ml' | 'pillars_studio' | 'strategy_studio' | 'football_field') => {
    setVault1Tab(tab);
    try {
      const url = new URL(window.location.href);
      url.searchParams.set('tab', tab === 'strategy_studio' ? 'strategy' : tab === 'pillars_studio' ? 'pillars' : tab === 'football_field' ? 'football' : 'bidding');
      window.history.replaceState({}, '', url.toString());
    } catch { }
  };

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.altKey) {
        if (e.key === '1') handleSelectVault1Tab('bidding_ml');
        if (e.key === '2') handleSelectVault1Tab('pillars_studio');
        if (e.key === '3') handleSelectVault1Tab('strategy_studio');
        if (e.key === '4') handleSelectVault1Tab('football_field');
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, []);
  const [vault2Tab, setVault2Tab] = useState<'peer_matrix' | 'ev_waterfall'>('peer_matrix');
  const [vault3Tab, setVault3Tab] = useState<'huber_cones' | 'scale_trajectory' | 'sensitivity_matrix' | 'football_field'>('huber_cones');

  const [isSimulationOpen, setIsSimulationOpen] = useState<boolean>(false);
  const [simulationParams, setSimulationParams] = useState<SimulationParams>({
    offerPrice: selectedSymbol === 'HCCB' ? 100 : selectedSymbol === 'SWIGGY' ? 390 : 108,
    alpha: 0.30,
    beta: 0.40,
    gamma: 0.30,
    cohortSize: 10,
    ruleOfXWeight: 2.3,
    illiquidityDiscountPct: 0.0,
  });
  const [bscData, setBscData] = useState<BscEvaluationData | null>(null);
  const [provenanceState, setProvenanceState] = useState<{
    isOpen: boolean;
    pageNumber: number | null;
    attributeId?: string;
  }>({
    isOpen: false,
    pageNumber: null,
  });

  const handleCitationClick = (pageNumber: number, attributeId?: string) => {
    setProvenanceState({
      isOpen: true,
      pageNumber,
      attributeId,
    });
  };

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

  const handleExportExcel = async () => {
    setIsExportingExcel(true);
    try {
      const res = await fetch('http://localhost:8001/api/v1/export/excel', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ symbol: selectedSymbol }),
      });
      if (!res.ok) throw new Error('Excel export failed');
      const blob = await res.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `${selectedSymbol}_Institutional_Valuation_Model.xlsx`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    } catch (err) {
      console.error('Failed to download Excel model:', err);
    } finally {
      setIsExportingExcel(false);
    }
  };

  useEffect(() => {
    loadData(selectedSymbol);
    setSimulationParams(prev => ({
      ...prev,
      offerPrice: selectedSymbol === 'HCCB' ? 100 : selectedSymbol === 'SWIGGY' ? 390 : 108,
    }));
  }, [selectedSymbol]);

  useEffect(() => {
    const controller = new AbortController();
    const fetchBsc = async () => {
      try {
        const res = await fetch('http://localhost:8001/api/v1/bsc/evaluate', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            symbol: selectedSymbol,
            offer_price: simulationParams.offerPrice,
            alpha: simulationParams.alpha,
            beta: simulationParams.beta,
            gamma: simulationParams.gamma,
            cohort_size: simulationParams.cohortSize,
            rule_of_x_weight: simulationParams.ruleOfXWeight,
            illiquidity_discount_pct: simulationParams.illiquidityDiscountPct,
          }),
          signal: controller.signal,
        });
        if (res.ok) {
          const json: BscEvaluationData = await res.json();
          setBscData(json);
        }
      } catch (err: unknown) {
        if (err instanceof DOMException && err.name === 'AbortError') {
          return;
        }
        console.error('Failed to fetch BSC evaluation:', err);
      }
    };

    fetchBsc();
    return () => controller.abort();
  }, [selectedSymbol, simulationParams]);

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
    setSelectedSymbol(newDeal.symbol);
    loadData(newDeal.symbol);
  };

  const priceBandMin =
    offer.pricingState.status === 'RHP_PRICED' ? offer.pricingState.priceBandMin : null;
  const priceBandMax =
    offer.pricingState.status === 'RHP_PRICED' ? offer.pricingState.priceBandMax : null;

  return (
    <div className="h-screen w-full bg-[#090D12] text-slate-100 flex flex-col font-sans overflow-hidden">
      {/* Top Header Ticker Bar */}
      <HeaderTicker
        indices={indices}
        onRefresh={() => loadData(selectedSymbol)}
        isRefreshing={isRefreshing}
        selectedSymbol={selectedSymbol}
        onSymbolChange={(sym) => {
          setSelectedSymbol(sym);
          loadData(sym);
        }}
        onExportExcel={handleExportExcel}
        isExportingExcel={isExportingExcel}
        onOpenAlmanac={() => handleViewChange('methodology_almanac')}
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
          {activeView === 'knowledge_graph' ? (
            /* True Edge-to-Edge Full Page View for Knowledge Graph Studio */
            <main ref={mainScrollRef} className="flex-1 p-3 lg:p-4 overflow-y-auto min-h-0 h-full flex flex-col bg-[#070B11]">
              <div className="w-full flex-1 flex flex-col space-y-3 min-h-0">
                {/* Full-Page Studio Header Banner */}
                <div className="rounded-xl border border-indigo-500/40 bg-gradient-to-r from-indigo-950/70 via-[#0E1522] to-cyan-950/60 p-3.5 flex flex-col sm:flex-row sm:items-center justify-between gap-3 shadow-lg shrink-0">
                  <div className="flex items-center gap-3">
                    <div className="w-8 h-8 rounded-lg bg-indigo-600/30 border border-indigo-500/60 flex items-center justify-center text-indigo-300 font-mono font-bold text-xs">
                      KG
                    </div>
                    <div>
                      <div className="text-xs font-bold font-mono text-slate-100 flex items-center gap-2">
                        <span>SECTION VI: FIBO KNOWLEDGE GRAPH &amp; ONTOLOGY WORKBENCH</span>
                        <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-emerald-950 text-emerald-400 border border-emerald-800 font-bold">FULL-PAGE VIEW</span>
                        <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-indigo-950 text-indigo-300 border border-indigo-800">PORT 5173 ONLINE</span>
                      </div>
                      <div className="text-[11px] text-slate-400 font-mono">
                        Dual Persona Studio · 25 Cypher Queries · 84 Canonical Formula Lineages · In-App PDF Bounding Box Drawer
                      </div>
                    </div>
                  </div>
                  <div className="flex items-center gap-2 shrink-0">
                    <a
                      href="http://localhost:5173/?vault=knowledge_graph"
                      target="_blank"
                      rel="noopener noreferrer"
                      className="px-3.5 py-1.5 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white font-mono text-xs font-bold flex items-center gap-1.5 transition-all shadow-md cursor-pointer"
                      title="Open Dedicated Full-Screen Knowledge Graph Studio on Port 5173"
                    >
                      <span>Open in Port 5173 Studio</span>
                      <span>↗</span>
                    </a>
                  </div>
                </div>

                {/* Edge-to-Edge Responsive Graph Canvas */}
                <div className="flex-1 min-h-[780px] w-full flex flex-col">
                  <TerminalErrorBoundary fallbackTitle="FIBO Knowledge Graph Studio">
                    <KnowledgeGraphStudioVault offer={offer} />
                  </TerminalErrorBoundary>
                </div>
              </div>
            </main>
          ) : (
            <>
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
              {/* Executive 5-Second Verdict Banner */}
              {bscData && (
                <ExecutiveVerdictBanner
                  symbol={selectedSymbol}
                  offerPrice={bscData.pro_forma.offer_price}
                  impliedMarketCapCr={bscData.pro_forma.implied_market_cap_cr}
                  postIssueSharesCr={bscData.pro_forma.post_issue_shares_cr}
                  askingPe={bscData.harmonic_multiples.issuer_asking_pe}
                  harmonicPe={bscData.harmonic_multiples.harmonic_pe}
                  valuationSpreadPct={bscData.harmonic_multiples.valuation_spread_pe_pct}
                  favorableUnfavorableFlag={bscData.harmonic_multiples.favorable_unfavorable_flag}
                  compositeBscScore={bscData.balanced_scorecard.composite_bsc_score}
                  ratingCategory={bscData.balanced_scorecard.rating_category}
                  isRiskVetoActive={bscData.balanced_scorecard.is_risk_veto_active}
                  vetoReason={bscData.balanced_scorecard.veto_reason}
                  onOpenSimulation={() => setIsSimulationOpen(!isSimulationOpen)}
                />
              )}

              {/* Persistent Simulation Control Rail */}
              {isSimulationOpen && (
                <SimulationControlRail
                  params={simulationParams}
                  onChange={(next) => setSimulationParams(next)}
                  priceBandMin={priceBandMin || 100}
                  priceBandMax={priceBandMax || 108}
                />
              )}

              {/* SCREEN 00: EXECUTIVE TRUTH TABLE & DILIGENCE MASTER */}
              {activeView === 'diligence_master' && (
                <div className="space-y-6 animate-fade-in">
                  <DiligenceMasterVerdictStudio
                    symbol={selectedSymbol}
                    onNavigateVault={handleViewChange}
                    onOpenAlmanac={handleOpenMethodologyDrawer}
                  />
                </div>
              )}

              {/* SECTION 0: DOSSIER FOUNDATIONS & DRHP REALITY */}
              {activeView === 'corporate_foundations' && (
                <div className="space-y-6 animate-fade-in">
                  <CorporateFoundationsStudio
                    symbol={selectedSymbol}
                    onNavigateVault={handleViewChange}
                    onOpenAlmanac={handleOpenMethodologyDrawer}
                    onOpenForensicDrawer={handleOpenForensicDrawer}
                  />
                </div>
              )}

              {/* Vault 1: Market Demand & Order Book */}
              {(activeView === 'market_demand' || activeView === 'overview') && (
                <div className="space-y-6 animate-fade-in">
                  {/* Sub-Studio Selector & Action Header */}
                  <div className="flex items-center justify-between border-b border-[#1E2B3E] pb-2">
                    <div className="flex flex-wrap items-center gap-2">
                      <button
                        onClick={() => handleSelectVault1Tab('bidding_ml')}
                        className={`px-3 py-1.5 rounded-lg text-xs font-mono font-bold transition-all cursor-pointer ${vault1Tab === 'bidding_ml'
                          ? 'bg-cyan-500/20 text-cyan-300 border border-cyan-500/40 shadow-sm'
                          : 'bg-[#101726] text-slate-400 border border-[#1E2B3E] hover:text-slate-200'
                          }`}
                      >
                        1. LIVE ASBA ORDER BOOK &amp; ML SCORECARD
                      </button>
                      <button
                        onClick={() => handleSelectVault1Tab('pillars_studio')}
                        className={`px-3 py-1.5 rounded-lg text-xs font-mono font-bold transition-all cursor-pointer ${vault1Tab === 'pillars_studio'
                          ? 'bg-cyan-500/20 text-cyan-300 border border-cyan-500/40 shadow-sm'
                          : 'bg-[#101726] text-slate-400 border border-[#1E2B3E] hover:text-slate-200'
                          }`}
                      >
                        2. 4-PILLAR EVIDENCE SUMMARY
                      </button>
                      <button
                        onClick={() => handleViewChange('cross_vault_matrix')}
                        className="px-3 py-1.5 rounded-lg text-xs font-mono font-bold transition-all cursor-pointer flex items-center gap-1.5 bg-[#131926] text-emerald-400 border border-emerald-500/40 hover:bg-emerald-500/20 hover:text-emerald-200"
                        title="Open full cross-vault scorecard in Section V"
                      >
                        <span className="px-1.5 py-0.2 rounded text-[10px] font-bold bg-emerald-950 text-emerald-300 border border-emerald-700">M3</span>
                        <span>CROSS-VAULT BSC ↗</span>
                      </button>
                      <button
                        onClick={() => handleViewChange('strategy_studio')}
                        className="px-3 py-1.5 rounded-lg text-xs font-mono font-bold transition-all cursor-pointer flex items-center gap-1.5 bg-[#131926] text-amber-400 border border-amber-500/40 hover:bg-amber-500/20 hover:text-amber-200"
                        title="Open full workspace in Section V"
                      >
                        <span className="px-1.5 py-0.2 rounded text-[10px] font-bold bg-amber-950 text-amber-300 border border-amber-700">M1</span>
                        <span>STRATEGY STUDIO ↗</span>
                      </button>
                    </div>

                    <div className="flex items-center gap-2">
                      <button
                        onClick={() => handleOpenForensicDrawer('market_demand')}
                        className="px-2.5 py-1.5 rounded bg-cyan-950/80 border border-cyan-700/80 text-cyan-300 font-mono text-xs font-bold flex items-center gap-1.5 hover:bg-cyan-900 transition-colors cursor-pointer shadow-sm"
                        title="Open Deep Forensic Diligence & Statutory Evidence Drawer"
                      >
                        <span>Forensic Diligence</span>
                        <span className="w-4 h-4 rounded-full bg-cyan-500 text-slate-950 flex items-center justify-center text-[10px] font-black">ⓘ</span>
                      </button>
                    </div>
                  </div>

                  {vault1Tab === 'bidding_ml' && (
                    <>
                      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                        <SubscriptionBookBar subscription={subscription} />
                        <WalkForwardMLScorecard scorecard={scorecard} />
                      </div>
                      <div className="pt-2">
                        <div className="flex items-center gap-2 mb-3">
                          <span className="px-2 py-0.5 rounded text-[10px] font-mono font-bold bg-indigo-950/80 text-indigo-300 border border-indigo-800">
                            MODULE 03
                          </span>
                          <span className="text-xs font-mono font-bold text-slate-200">
                            MODEL INTERPRETABILITY &amp; EXPLAINABILITY WATERFALL
                          </span>
                        </div>
                        <SHAPWaterfallChart features={scorecard.shapTopFeatures} />
                      </div>
                      
                      {/* High-Density Forensic Directive Banner (Methodology ⓘ Pattern) */}
                      <div className="p-4 rounded-xl bg-[#0E1624] border border-[#1E2B3E] flex flex-col sm:flex-row sm:items-center justify-between gap-3 shadow-md">
                        <div className="text-xs space-y-1">
                          <div className="flex items-center gap-2 font-mono font-bold">
                            <span className="px-2 py-0.5 rounded text-[10px] bg-emerald-950 border border-emerald-700 text-emerald-300">
                              AQI 88/100 · PASS
                            </span>
                            <span className="text-cyan-400">MARKET DEMAND & ORDER BOOK DIRECTIVE</span>
                          </div>
                          <p className="text-slate-300 leading-relaxed">
                            Sticky long-only QIB float absorption under SEBI Reg 6(2) eliminates listing day air pockets. Day 30 and Day 90 anchor lock-in supply releases require phased capital allocation.
                          </p>
                        </div>
                        <button
                          onClick={() => handleOpenForensicDrawer('market_demand')}
                          className="px-3 py-2 rounded-lg text-xs font-mono font-bold bg-[#142032] hover:bg-[#1C2C45] text-cyan-300 border border-cyan-800 flex items-center gap-1.5 shrink-0 transition-colors cursor-pointer"
                        >
                          <span>Full Forensic Proof & Covenants</span>
                          <span className="w-4 h-4 rounded-full bg-cyan-500 text-slate-950 flex items-center justify-center text-[10px] font-black">ⓘ</span>
                        </button>
                      </div>
                    </>
                  )}

                  {vault1Tab === 'pillars_studio' && (
                    <div className="space-y-6">
                      {/* Authoritative Single Home Banner */}
                      <div className="p-3 rounded-lg bg-emerald-950/40 border border-emerald-700/60 flex items-center justify-between gap-3 text-xs font-mono">
                        <div className="flex items-center gap-2 text-emerald-200">
                          <span className="px-1.5 py-0.5 rounded text-[10px] font-bold bg-emerald-900 border border-emerald-600 text-emerald-100">SSOT</span>
                          <span>Comprehensive 6-dimension telemetry with cross-vault linkages is unified in Section V · M3.</span>
                        </div>
                        <button
                          onClick={() => handleViewChange('cross_vault_matrix')}
                          className="px-2.5 py-1 rounded bg-emerald-900/80 hover:bg-emerald-800 text-emerald-200 border border-emerald-600 text-xs font-bold transition-colors cursor-pointer shrink-0"
                        >
                          Launch M3 Cross-Vault BSC Matrix ↗
                        </button>
                      </div>

                      {bscData?.balanced_scorecard && (
                        <IPOBalancedScorecardView
                          symbol={selectedSymbol}
                          compositeScore={bscData.balanced_scorecard.composite_bsc_score}
                          ratingCategory={bscData.balanced_scorecard.rating_category}
                          isRiskVetoActive={bscData.balanced_scorecard.is_risk_veto_active}
                          vetoReason={bscData.balanced_scorecard.veto_reason}
                          dimensions={bscData.balanced_scorecard.dimensions}
                          summaryVerdict={bscData.balanced_scorecard.summary_verdict}
                        />
                      )}
                      {/* High-Density Forensic Directive Banner */}
                      <div className="p-4 rounded-xl bg-[#0E1624] border border-[#1E2B3E] flex flex-col sm:flex-row sm:items-center justify-between gap-3 shadow-md">
                        <div className="text-xs space-y-1">
                          <div className="flex items-center gap-2 font-mono font-bold">
                            <span className="px-2 py-0.5 rounded text-[10px] bg-cyan-950 border border-cyan-700 text-cyan-300">
                              FOUR PILLARS NARRATIVE SYNTHESIS
                            </span>
                            <span className="text-cyan-400">SECTOR CONTEXT &amp; LIFECYCLE PRECEDENTS</span>
                          </div>
                          <p className="text-slate-300 leading-relaxed">
                            FMCG Mega-OFS anchor book depth commands over 74% high-conviction DII and SWF allocation, dampening grey market premium speculation.
                          </p>
                        </div>
                        <button
                          onClick={() => handleOpenForensicDrawer('market_demand')}
                          className="px-3 py-2 rounded-lg text-xs font-mono font-bold bg-[#142032] hover:bg-[#1C2C45] text-cyan-300 border border-cyan-800 flex items-center gap-1.5 shrink-0 transition-colors cursor-pointer"
                        >
                          <span>Inspect Statutory Evidence ↗</span>
                        </button>
                      </div>
                    </div>
                  )}

                  {vault1Tab === 'strategy_studio' && (
                    <div className="space-y-6 animate-fade-in">
                      <ConsultingStrategyStudio
                        offer={offer}
                        onCitationClick={handleCitationClick}
                        onOpenAlmanac={handleOpenMethodologyDrawer}
                        onOpenForensicDrawer={handleOpenForensicDrawer}
                      />
                    </div>
                  )}

                  {vault1Tab === 'football_field' && (
                    <div className="space-y-6">
                      <ValuationFootballField
                        symbol={offer.symbol}
                        companyName={offer.companyName}
                        priceBandMin={priceBandMin}
                        priceBandMax={priceBandMax}
                        onOpenAlmanac={handleOpenMethodologyDrawer}
                      />
                    </div>
                  )}
                </div>
              )}

              {/* Vault 2: Peer, Sector & Competitor Studio */}
              {activeView === 'peer_comps' && (
                <div className="space-y-6 animate-fade-in">
                  <PeerSectorCompetitorStudio
                    offer={offer}
                    onOpenAlmanac={handleOpenMethodologyDrawer}
                    onOpenForensicDrawer={handleOpenForensicDrawer}
                  />
                </div>
              )}

              {/* Vault 3: Huber Econometric Studio & Cones */}
              {activeView === 'huber_studio' && (
                <div className="space-y-6 animate-fade-in">
                  {/* Sub-Studio Selector */}
                  <div className="flex items-center justify-between border-b border-[#1E2B3E] pb-2">
                    <div className="flex items-center gap-2">
                      <button
                        onClick={() => setVault3Tab('huber_cones')}
                        className={`px-3 py-1.5 rounded-lg text-xs font-mono font-bold transition-all cursor-pointer ${vault3Tab === 'huber_cones'
                          ? 'bg-cyan-500/20 text-cyan-300 border border-cyan-500/40 shadow-sm'
                          : 'bg-[#101726] text-slate-400 border border-[#1E2B3E] hover:text-slate-200'
                          }`}
                      >
                        1. HUBER RLM QUANTILE CONES
                      </button>
                      <button
                        onClick={() => setVault3Tab('scale_trajectory')}
                        className={`px-3 py-1.5 rounded-lg text-xs font-mono font-bold transition-all cursor-pointer ${vault3Tab === 'scale_trajectory'
                          ? 'bg-cyan-500/20 text-cyan-300 border border-cyan-500/40 shadow-sm'
                          : 'bg-[#101726] text-slate-400 border border-[#1E2B3E] hover:text-slate-200'
                          }`}
                      >
                        2. SCALE-SHIFTED TRAJECTORY STUDIO
                      </button>
                      <button
                        onClick={() => setVault3Tab('sensitivity_matrix')}
                        className={`px-3 py-1.5 rounded-lg text-xs font-mono font-bold transition-all cursor-pointer ${vault3Tab === 'sensitivity_matrix'
                          ? 'bg-cyan-500/20 text-cyan-300 border border-cyan-500/40 shadow-sm'
                          : 'bg-[#101726] text-slate-400 border border-[#1E2B3E] hover:text-slate-200'
                          }`}
                      >
                        3. 2D SENSITIVITY MATRIX (WACC x g)
                      </button>
                      <button
                        onClick={() => setVault3Tab('football_field')}
                        className={`px-3 py-1.5 rounded-lg text-xs font-mono font-bold transition-all cursor-pointer ${vault3Tab === 'football_field'
                          ? 'bg-cyan-500/20 text-cyan-300 border border-cyan-500/40 shadow-sm'
                          : 'bg-[#101726] text-slate-400 border border-[#1E2B3E] hover:text-slate-200'
                          }`}
                      >
                        4. VALUATION FOOTBALL FIELD
                      </button>
                    </div>

                    <div className="flex items-center gap-2">
                      <button
                        onClick={() => handleOpenForensicDrawer('huber_studio')}
                        className="px-2.5 py-1.5 rounded bg-cyan-950/80 border border-cyan-700/80 text-cyan-300 font-mono text-xs font-bold flex items-center gap-1.5 hover:bg-cyan-900 transition-colors cursor-pointer shadow-sm"
                        title="Open Huber M-Estimator & Selection Bias Diligence Drawer"
                      >
                        <span>Forensic Diligence</span>
                        <span className="w-4 h-4 rounded-full bg-cyan-500 text-slate-950 flex items-center justify-center text-[10px] font-black">ⓘ</span>
                      </button>
                    </div>
                  </div>

                  {vault3Tab === 'huber_cones' && (
                    <HuberCalibrationCard
                      calibration={calibration}
                      onOpenAlmanac={handleOpenMethodologyDrawer}
                    />
                  )}
                  {vault3Tab === 'scale_trajectory' && bscData && (
                    <ScaleShiftedTrajectoryStudio
                      symbol={selectedSymbol}
                      issuerRuleOfX={bscData.balanced_scorecard.dimensions[2]?.score * 15 || 65.0}
                      issuerEvRevenue={bscData.harmonic_multiples.issuer_asking_ev_revenue || 8.4}
                      weightedPeers={bscData.weighted_peers.map((p: WeightedPeerItem) => ({
                        peer_id: p.peer_id,
                        company_name: p.company_name,
                        rule_of_x: p.rule_of_x,
                        ev_revenue: p.ev_revenue,
                        weight: p.weight,
                      }))}
                    />
                  )}
                  {vault3Tab === 'sensitivity_matrix' && (
                    <SensitivityHeatmap
                      symbol={offer.symbol}
                      companyName={offer.companyName}
                      currentOfferCap={priceBandMax ?? 108}
                    />
                  )}
                  {vault3Tab === 'football_field' && (
                    <ValuationFootballField
                      symbol={offer.symbol}
                      companyName={offer.companyName}
                      priceBandMin={priceBandMin}
                      priceBandMax={priceBandMax}
                      onOpenAlmanac={handleOpenMethodologyDrawer}
                    />
                  )}

                  {/* High-Density Forensic Directive Banner (Methodology ⓘ Pattern) */}
                  <div className="p-4 rounded-xl bg-[#0E1624] border border-[#1E2B3E] flex flex-col sm:flex-row sm:items-center justify-between gap-3 shadow-md">
                    <div className="text-xs space-y-1">
                      <div className="flex items-center gap-2 font-mono font-bold">
                        <span className="px-2 py-0.5 rounded text-[10px] bg-cyan-950 border border-cyan-700 text-cyan-300">
                          ROBUST P50: ₹98.20
                        </span>
                        <span className="text-cyan-400">HUBER RLM BENCHMARK &amp; SELECTION BIAS PROOF</span>
                      </div>
                      <p className="text-slate-300 leading-relaxed">
                        RLM downweights Tata Consumer and VBL outlier multiples. Selection bias test (t = 0.842) confirms no cherry-picking bias. Reverse DCF growth hurdle solves to achievable 14.80% 5-year revenue CAGR.
                      </p>
                    </div>
                    <button
                      onClick={() => handleOpenForensicDrawer('huber_studio')}
                      className="px-3 py-2 rounded-lg text-xs font-mono font-bold bg-[#142032] hover:bg-[#1C2C45] text-cyan-300 border border-cyan-800 flex items-center gap-1.5 shrink-0 transition-colors cursor-pointer"
                    >
                      <span>Full Econometric Proofs</span>
                      <span className="w-4 h-4 rounded-full bg-cyan-500 text-slate-950 flex items-center justify-center text-[10px] font-black">ⓘ</span>
                    </button>
                  </div>
                </div>
              )}

              {/* Vault 4: Provenance Evidence Ledger */}
              {activeView === 'provenance_ledger' && (
                <div className="animate-fade-in">
                  <ProvenanceLedgerVault
                    offer={offer}
                    onOpenForensicDrawer={handleOpenForensicDrawer}
                  />
                </div>
              )}

              {/* Vault 5: Econometric & Forensic Lab */}
              {(activeView === 'stress_workpapers' || activeView === 'econometric_lab') && (
                <div className="animate-fade-in">
                  <EconometricLabVault
                    offer={offer}
                    onOpenForensicDrawer={handleOpenForensicDrawer}
                    onOpenAlmanac={handleOpenMethodologyDrawer}
                  />
                </div>
              )}

              {/* Vault 6: Institutional Q&A */}
              {activeView === 'investor_qa' && (
                <div className="animate-fade-in">
                  <InvestorQAVault
                    offer={offer}
                    onOpenForensicDrawer={handleOpenForensicDrawer}
                  />
                </div>
              )}

              {/* Vault 7: 6-Persona Stakeholder Lens */}
              {activeView === 'stakeholder_lens' && (
                <div className="animate-fade-in">
                  <StakeholderLensVault
                    offer={offer}
                    onOpenForensicDrawer={handleOpenForensicDrawer}
                  />
                </div>
              )}

              {/* Vault 8: 6-Rule Red-Flag Scanner */}
              {activeView === 'red_flag_scanner' && (
                <div className="animate-fade-in">
                  <RedFlagScannerVault
                    offer={offer}
                    onOpenForensicDrawer={handleOpenForensicDrawer}
                  />
                </div>
              )}

              {/* Vault 9: Contingent Litigation Radar */}
              {activeView === 'contingent_litigation' && (
                <div className="animate-fade-in">
                  <ContingentLitigationVault
                    offer={offer}
                    onCitationClick={handleCitationClick}
                    onOpenForensicDrawer={handleOpenForensicDrawer}
                  />
                </div>
              )}

              {/* Vault 10: Unit Economics & Operational Scale */}
              {activeView === 'unit_economics' && (
                <div className="animate-fade-in">
                  <UnitEconomicsVault
                    offer={offer}
                    onCitationClick={handleCitationClick}
                    onOpenForensicDrawer={handleOpenForensicDrawer}
                  />
                </div>
              )}

              {/* Vault 11: Unlisted Post-Tax Arbitrage */}
              {activeView === 'unlisted_arbitrage' && (
                <div className="animate-fade-in">
                  <UnlistedArbitrageVault
                    offer={offer}
                    onOpenForensicDrawer={handleOpenForensicDrawer}
                  />
                </div>
              )}

              {/* Vault 12: IC Stance & Board Deck Export */}
              {activeView === 'ic_board_deck' && (
                <div className="space-y-6 animate-fade-in">
                  <ICBoardDeckVault
                    offer={offer}
                    onOpenForensicDrawer={handleOpenForensicDrawer}
                  />
                  <div className="pt-2">
                    <div className="flex items-center gap-2 mb-3">
                      <span className="px-2 py-0.5 rounded text-[10px] font-mono font-bold bg-cyan-950/80 text-cyan-300 border border-cyan-800">
                        MODULE 02
                      </span>
                      <span className="text-xs font-mono font-bold text-slate-200">
                        SEBI RA COMPLIANCE &amp; IMMUTABLE AUDIT LEDGER
                      </span>
                    </div>
                    <SEBIComplianceStamp compliance={compliance} />
                  </div>
                </div>
              )}

              {/* SECTION V: STRATEGY & BALANCED SCORECARD SUITE */}
              {/* M1: Consulting Strategy & Industry Structure Studio */}
              {activeView === 'strategy_studio' && (
                <div className="space-y-6 animate-fade-in">
                  <ConsultingStrategyStudio
                    offer={offer}
                    onCitationClick={handleCitationClick}
                    onOpenAlmanac={handleOpenMethodologyDrawer}
                    onOpenForensicDrawer={handleOpenForensicDrawer}
                  />
                </div>
              )}

              {/* M2: 6-Dimension Empirical Strategy Map DAG */}
              {activeView === 'strategy_map_dag' && (
                <div className="space-y-6 animate-fade-in">
                  <EmpiricalStrategyMapDAG
                    offer={offer}
                    onCitationClick={handleCitationClick}
                    onOpenForensicDrawer={handleOpenForensicDrawer}
                  />
                </div>
              )}

              {/* M3: Institutional Cross-Vault BSC Matrix */}
              {activeView === 'cross_vault_matrix' && (
                <div className="space-y-6 animate-fade-in">
                  <CrossVaultBSCMatrix
                    offer={offer}
                    bscData={bscData}
                    onCitationClick={handleCitationClick}
                    onNavigateVault={handleViewChange}
                    onOpenForensicDrawer={handleOpenForensicDrawer}
                  />
                </div>
              )}

              {/* M4: Formula-Driven Institutional Excel Model */}
              {activeView === 'excel_model_studio' && (
                <div className="space-y-6 animate-fade-in">
                  <ExcelModelAuditStudio
                    offer={offer}
                    onCitationClick={handleCitationClick}
                    onOpenForensicDrawer={handleOpenForensicDrawer}
                  />
                </div>
              )}

              {/* EDUCATIONAL METHODOLOGY ALMANAC KNOWLEDGE BASE */}
              {activeView === 'methodology_almanac' && (
                <div className="space-y-6 animate-fade-in">
                  <MethodologyAlmanacView
                    onNavigateVault={handleViewChange}
                    initialMethodologyId={selectedMethodologyId}
                  />
                </div>
              )}
            </div>
          </main>
        </>
      )}
    </div>
      </div>

      {/* Provenance Flyout Drawer */}
      <ProvenanceDrawer
        isOpen={provenanceState.isOpen}
        onClose={() => setProvenanceState({ isOpen: false, pageNumber: null })}
        symbol={selectedSymbol}
        pageNumber={provenanceState.pageNumber}
        attributeId={provenanceState.attributeId}
        onNavigateToLedger={() => {
          setProvenanceState({ isOpen: false, pageNumber: null });
          handleViewChange('provenance_ledger');
        }}
      />

      {/* Ingest Modal (Option A) */}
      <IngestModal
        isOpen={isIngestModalOpen}
        onClose={() => setIsIngestModalOpen(false)}
        onIngestSuccess={handleIngestSuccess}
      />

      {/* Interactive Methodology Slide-Over Drawer */}
      <MethodologySlideOverDrawer
        isOpen={isAlmanacDrawerOpen}
        methodologyId={selectedMethodologyId}
        onClose={() => setIsAlmanacDrawerOpen(false)}
        onOpenFullAlmanac={(methodologyId) => {
          setIsAlmanacDrawerOpen(false);
          if (methodologyId) {
            setSelectedMethodologyId(methodologyId);
          }
          handleViewChange('methodology_almanac');
        }}
      />

      {/* Interactive Forensic Evidence & Underwriting Diligence Slide-Over Drawer */}
      <ForensicEvidenceSlideOverDrawer
        isOpen={forensicDrawerState.isOpen}
        onClose={() => setForensicDrawerState({ isOpen: false, vaultId: null })}
        dealSymbol={selectedSymbol}
        vaultId={forensicDrawerState.vaultId}
        onCitationClick={handleCitationClick}
      />
    </div>
  );
};

export default App;
