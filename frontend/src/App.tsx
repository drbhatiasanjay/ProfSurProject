import React, { useState, useEffect } from 'react';
import { HeaderTicker } from './components/HeaderTicker';
import { SidebarNav, TerminalView } from './components/SidebarNav';
import { StatutoryOfferHero } from './components/StatutoryOfferHero';
import { SubscriptionBookBar } from './components/SubscriptionBookBar';
import { LivePeerCompsTable } from './components/LivePeerCompsTable';
import { HuberCalibrationCard } from './components/HuberCalibrationCard';
import { WalkForwardMLScorecard } from './components/WalkForwardMLScorecard';
import { SHAPWaterfallChart } from './components/SHAPWaterfallChart';
import { SEBIComplianceStamp } from './components/SEBIComplianceStamp';
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

export const App: React.FC = () => {
  const [activeView, setActiveView] = useState<TerminalView>('overview');
  const [selectedSymbol, setSelectedSymbol] = useState<string>('NTPCGREEN');
  const [isRefreshing, setIsRefreshing] = useState<boolean>(false);

  const [indices, setIndices] = useState(mockMarketIndices);
  const [offer, setOffer] = useState(mockOfferDetails);
  const [subscription, setSubscription] = useState(mockSubscriptionBook);
  const [peers, setPeers] = useState(mockLivePeers);
  const [calibration, setCalibration] = useState(mockHuberCalibration);
  const [scorecard, setScorecard] = useState(mockMLScorecard);
  const [compliance, setCompliance] = useState(mockSEBICompliance);

  const loadData = async () => {
    setIsRefreshing(true);
    try {
      const data = await fetchLiveMarketData();
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
      setTimeout(() => setIsRefreshing(false), 600);
    }
  };

  useEffect(() => {
    loadData();
  }, [selectedSymbol]);

  return (
    <div className="min-h-screen bg-[#090D12] text-slate-100 flex flex-col font-sans">
      {/* Top Header Ticker Bar */}
      <HeaderTicker
        indices={indices}
        onRefresh={loadData}
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
        />

        {/* Central Content Area */}
        <main className="flex-1 p-4 lg:p-6 overflow-y-auto space-y-6">
          {/* View: Overview (Comprehensive Primary Dashboard) */}
          {activeView === 'overview' && (
            <div className="space-y-6 max-w-7xl mx-auto">
              <StatutoryOfferHero offer={offer} />
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                <SubscriptionBookBar subscription={subscription} />
                <WalkForwardMLScorecard scorecard={scorecard} />
              </div>
              <HuberCalibrationCard calibration={calibration} />
              <LivePeerCompsTable peers={peers} />
              <SHAPWaterfallChart features={scorecard.shapTopFeatures} />
              <SEBIComplianceStamp compliance={compliance} />
            </div>
          )}

          {/* View: Peer Comps Table Only */}
          {activeView === 'peer_comps' && (
            <div className="space-y-6 max-w-7xl mx-auto">
              <StatutoryOfferHero offer={offer} />
              <LivePeerCompsTable peers={peers} />
            </div>
          )}

          {/* View: Huber Calibration Only */}
          {activeView === 'huber_calibrator' && (
            <div className="space-y-6 max-w-7xl mx-auto">
              <HuberCalibrationCard calibration={calibration} />
              <LivePeerCompsTable peers={peers} />
            </div>
          )}

          {/* View: Walk-Forward ML & SHAP */}
          {activeView === 'ml_scorecard' && (
            <div className="space-y-6 max-w-7xl mx-auto">
              <WalkForwardMLScorecard scorecard={scorecard} />
              <SHAPWaterfallChart features={scorecard.shapTopFeatures} />
            </div>
          )}

          {/* View: Compliance & Regulatory Ledger */}
          {activeView === 'compliance' && (
            <div className="space-y-6 max-w-7xl mx-auto">
              <SEBIComplianceStamp compliance={compliance} />
            </div>
          )}
        </main>
      </div>
    </div>
  );
};

export default App;
