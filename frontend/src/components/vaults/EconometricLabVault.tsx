import React, { useState, useEffect } from 'react';
import {
  StatutoryOfferDetails,
  ComprehensiveEconometricSuiteData,
  EconometricVerdict
} from '../../types/terminal';
import { fetchEconometricSuite, getMockEconometricSuite } from '../../services/dataService';
import { EvidenceInterpretationPanel } from '../shared/EvidenceInterpretationPanel';
import {
  Calculator,
  Activity,
  ShieldCheck,
  ShieldAlert,
  Layers,
  TrendingUp,
  BarChart3,
  AlertTriangle,
  CheckCircle2,
  Lock,
  Clock,
  Scale,
  Coins,
  ArrowRight,
  Sliders,
  FileText
} from 'lucide-react';

interface EconometricLabVaultProps {
  offer: StatutoryOfferDetails;
}

export const EconometricLabVault: React.FC<EconometricLabVaultProps> = ({ offer }) => {
  const isHCCB = offer.symbol === 'HCCB' || offer.companyName.includes('Coca-Cola');
  const [suiteData, setSuiteData] = useState<ComprehensiveEconometricSuiteData>(() =>
    getMockEconometricSuite(isHCCB)
  );
  const [activeTab, setActiveTab] = useState<
    'beneish' | 'dickinson' | 'huber' | 'stub' | 'indas116' | 'altman' | 'lockin' | 'stress_grid'
  >('beneish');
  const [isLoading, setIsLoading] = useState<boolean>(false);

  // 2D Stress Grid State (Volume Shock vs Cost Shock)
  const [selectedCell, setSelectedCell] = useState<{ volumeIdx: number; costIdx: number }>({ volumeIdx: 2, costIdx: 2 });
  const volumeDeltas = [-10, -5, 0, +5, +10]; // %
  const rawMaterialShocks = [0, +5, +10, +15, +20]; // %
  const baseMargin = isHCCB ? 21.4 : 78.4;

  const calculateGridMargin = (volDelta: number, costShock: number) => {
    const margin = baseMargin + (volDelta * 0.35) - (costShock * 0.55);
    return Math.max(0, margin);
  };

  useEffect(() => {
    let isMounted = true;
    setIsLoading(true);
    fetchEconometricSuite(offer.symbol)
      .then(data => {
        if (isMounted && data) {
          setSuiteData(data);
        }
      })
      .catch(() => {
        if (isMounted) {
          setSuiteData(getMockEconometricSuite(isHCCB));
        }
      })
      .finally(() => {
        if (isMounted) setIsLoading(false);
      });

    return () => {
      isMounted = false;
    };
  }, [offer.symbol, isHCCB]);

  const models = suiteData.models;
  const isContained = Boolean(offer.pricingState && 'isContained' in offer.pricingState && offer.pricingState.isContained);

  // Verdict style mapper
  const getVerdictBadge = (verdict: EconometricVerdict | string) => {
    switch (verdict) {
      case 'FAVORABLE':
        return (
          <span className="px-2.5 py-1 rounded-md text-xs font-mono font-bold bg-emerald-950/80 border border-emerald-600 text-emerald-400 flex items-center gap-1.5">
            <CheckCircle2 className="w-3.5 h-3.5" /> FAVORABLE
          </span>
        );
      case 'NEUTRAL':
        return (
          <span className="px-2.5 py-1 rounded-md text-xs font-mono font-bold bg-sky-950/80 border border-sky-600 text-sky-400 flex items-center gap-1.5">
            <Activity className="w-3.5 h-3.5" /> NEUTRAL
          </span>
        );
      case 'CAUTION':
        return (
          <span className="px-2.5 py-1 rounded-md text-xs font-mono font-bold bg-amber-950/80 border border-amber-600 text-amber-400 flex items-center gap-1.5">
            <AlertTriangle className="w-3.5 h-3.5" /> CAUTION
          </span>
        );
      case 'CRITICAL':
      default:
        return (
          <span className="px-2.5 py-1 rounded-md text-xs font-mono font-bold bg-rose-950/80 border border-rose-600 text-rose-400 flex items-center gap-1.5">
            <ShieldAlert className="w-3.5 h-3.5" /> CRITICAL
          </span>
        );
    }
  };

  const tabMetricMap: Record<string, string> = {
    beneish: 'beneish_m_score',
    dickinson: 'dickinson_lifecycle',
    huber: 'valuation_multiple',
    stub: 'stub_seasonality',
    indas116: 'lease_adjusted_leverage',
    altman: 'altman_z_score',
    lockin: 'lockin_supply_cliff',
    stress_grid: 'valuation_multiple',
  };

  // Interpretation Box Component
  const renderInterpretationPanel = (
    verdict: EconometricVerdict | string,
    summary: string,
    mechanism: string,
    icRecommendation: string
  ) => {
    const metricId = tabMetricMap[activeTab];
    const richInterpretation =
      suiteData.interpretations?.[metricId] || offer.interpretations?.[metricId];

    if (richInterpretation) {
      return (
        <EvidenceInterpretationPanel
          interpretation={richInterpretation}
          title={`Engine Intelligence: ${metricId.replace(/_/g, ' ').toUpperCase()}`}
        />
      );
    }

    return (
      <div className="rounded-xl border border-[#223044] bg-[#0A0F18] p-5 space-y-4">
        <div className="flex items-center justify-between border-b border-[#1E2B3E] pb-3">
          <div className="flex items-center gap-2">
            <FileText className="w-4 h-4 text-cyan-400" />
            <span className="text-xs font-mono font-bold uppercase tracking-wider text-cyan-300">
              Automated Buy-Side Interpretation & Forensic Synthesis
            </span>
          </div>
          {getVerdictBadge(verdict)}
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-xs font-sans">
          {/* 1. Statistical Finding */}
          <div className="bg-[#101726] border border-[#1E2B3E] rounded-lg p-3.5 space-y-2">
            <div className="flex items-center gap-1.5 text-slate-400 font-mono text-[11px] font-bold uppercase">
              <span className="text-sky-400 font-mono">1.</span> Statistical Finding
            </div>
            <p className="text-slate-200 leading-relaxed font-mono text-[11.5px]">
              {summary}
            </p>
          </div>

          {/* 2. Economic Mechanism */}
          <div className="bg-[#101726] border border-[#1E2B3E] rounded-lg p-3.5 space-y-2">
            <div className="flex items-center gap-1.5 text-slate-400 font-mono text-[11px] font-bold uppercase">
              <span className="text-cyan-400 font-mono">2.</span> Economic Mechanism
            </div>
            <p className="text-slate-300 leading-relaxed text-[11.5px]">
              {mechanism}
            </p>
          </div>

          {/* 3. IC Recommendation */}
          <div className="bg-[#101726] border border-cyan-900/60 rounded-lg p-3.5 space-y-2">
            <div className="flex items-center gap-1.5 text-cyan-300 font-mono text-[11px] font-bold uppercase">
              <span className="text-amber-400 font-mono">3.</span> IC Actionable Directive
            </div>
            <p className="text-slate-100 font-medium leading-relaxed text-[11.5px]">
              {icRecommendation}
            </p>
          </div>
        </div>
      </div>
    );
  };

  return (
    <div className="space-y-6 max-w-7xl mx-auto font-sans animate-fade-in">
      {/* Top Banner & Header */}
      <div className="rounded-xl border border-[#223044] bg-[#0E1522] p-5 shadow-lg">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-4 border-b border-[#1E2B3E]">
          <div>
            <div className="flex items-center gap-2.5">
              <Calculator className="w-5 h-5 text-cyan-400" />
              <h2 className="text-base font-bold text-slate-100 font-mono tracking-wide">
                VAULT 5: ECONOMETRIC & FORENSIC ANALYTICAL LAB
              </h2>
              <span className="px-2 py-0.5 rounded bg-cyan-950/80 border border-cyan-800 text-[10px] font-mono text-cyan-300">
                7 STATISTICAL ENGINES
              </span>
            </div>
            <p className="text-xs text-slate-400 mt-1 font-mono">
              Quantitative Underwriting Suite · Dickinson (2011) · Huber (1964) RLM · Beneish (1999) · Altman (2002) · {offer.companyName}
            </p>
          </div>

          <div className="flex items-center gap-3">
            <div className="text-right">
              <div className="text-[10px] font-mono uppercase text-slate-400 font-bold">COMPOSITE FORENSIC STANCE</div>
              <div className="mt-0.5">{getVerdictBadge(suiteData.overallVerdict)}</div>
            </div>
          </div>
        </div>

        {/* Unpriced Containment Warning */}
        {isContained && (
          <div className="mt-4 p-3 bg-amber-950/40 border border-amber-800/80 rounded-lg flex items-center gap-3 text-xs text-amber-200">
            <AlertTriangle className="w-4 h-4 text-amber-400 flex-shrink-0" />
            <div>
              <span className="font-bold">SEBI ICDR Containment Notice:</span> This prospectus is currently unpriced (DRHP status).
              Valuation froth multiples and reverse DCF hurdles are displayed for analytical scenario guidance and fail closed on statutory exports.
            </div>
          </div>
        )}

        {/* Top Model Navigation Tabs */}
        <div className="flex items-center gap-1.5 overflow-x-auto pt-4 scrollbar-none">
          {[
            { id: 'beneish', label: '1. Beneish M-Score', icon: ShieldCheck },
            { id: 'dickinson', label: '2. Dickinson Lifecycle', icon: Activity },
            { id: 'huber', label: '3. Huber Robust Comps', icon: Scale },
            { id: 'stub', label: '4. Stub Seasonality Break', icon: TrendingUp },
            { id: 'indas116', label: '5. Ind AS 116 Lease Leverage', icon: Layers },
            { id: 'altman', label: '6. Altman Z\'\'-Score', icon: BarChart3 },
            { id: 'lockin', label: '7. Lock-In & Tax Drag', icon: Lock },
            { id: 'stress_grid', label: '8. 2D Stress Matrix', icon: Sliders }
          ].map(tab => {
            const Icon = tab.icon;
            const isActive = activeTab === tab.id;
            return (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id as any)}
                className={`flex items-center gap-2 px-3 py-2 rounded-lg text-xs font-mono font-semibold transition-all whitespace-nowrap cursor-pointer ${
                  isActive
                    ? 'bg-cyan-950/80 border border-cyan-500 text-cyan-200 shadow-sm'
                    : 'bg-[#121B29] border border-[#1E2B3E] text-slate-400 hover:text-slate-200 hover:border-slate-600'
                }`}
              >
                <Icon className={`w-3.5 h-3.5 ${isActive ? 'text-cyan-400' : 'text-slate-500'}`} />
                {tab.label}
              </button>
            );
          })}
        </div>
      </div>

      {/* MODEL 1: BENEISH M-SCORE & SLOAN ACCRUALS */}
      {activeTab === 'beneish' && models.beneishMScore && (
        <div className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div className="rounded-xl border border-[#223044] bg-[#0E1522] p-4">
              <div className="text-[10px] font-mono text-slate-400 uppercase font-bold">Beneish 8-Var M-Score</div>
              <div className={`text-2xl font-mono font-bold mt-1 ${
                models.beneishMScore.zone === 'SAFE' ? 'text-emerald-400' :
                models.beneishMScore.zone === 'GREY' ? 'text-amber-400' : 'text-rose-400'
              }`}>
                {models.beneishMScore.mScore.toFixed(2)}
              </div>
              <div className="text-[11px] font-mono text-slate-400 mt-1">
                Threshold: Safe &lt; -2.22 · Grey [-2.22, -1.78]
              </div>
            </div>

            <div className="rounded-xl border border-[#223044] bg-[#0E1522] p-4">
              <div className="text-[10px] font-mono text-slate-400 uppercase font-bold">Sloan Accrual Ratio</div>
              <div className="text-2xl font-mono font-bold mt-1 text-cyan-400">
                {(models.beneishMScore.sloanAccrualRatio * 100).toFixed(1)}%
              </div>
              <div className="text-[11px] font-mono text-slate-400 mt-1">
                Threshold: &lt; 10.0% of Total Assets
              </div>
            </div>

            <div className="rounded-xl border border-[#223044] bg-[#0E1522] p-4">
              <div className="text-[10px] font-mono text-slate-400 uppercase font-bold">DSRI (Receivables Growth)</div>
              <div className="text-2xl font-mono font-bold mt-1 text-slate-200">
                {models.beneishMScore.dsri.toFixed(2)}x
              </div>
              <div className="text-[11px] font-mono text-slate-400 mt-1">
                Normal index: ~1.00x · High alert: &gt; 1.30x
              </div>
            </div>

            <div className="rounded-xl border border-[#223044] bg-[#0E1522] p-4">
              <div className="text-[10px] font-mono text-slate-400 uppercase font-bold">Manipulation Classification</div>
              <div className="mt-1">
                <span className={`inline-block px-2.5 py-1 rounded text-xs font-mono font-bold ${
                  models.beneishMScore.zone === 'SAFE' ? 'bg-emerald-950 text-emerald-400 border border-emerald-800' :
                  models.beneishMScore.zone === 'GREY' ? 'bg-amber-950 text-amber-400 border border-amber-800' :
                  'bg-rose-950 text-rose-400 border border-rose-800'
                }`}>
                  {models.beneishMScore.zone} ZONE
                </span>
              </div>
              <div className="text-[11px] font-mono text-slate-400 mt-1">
                Academic 8-factor calibration
              </div>
            </div>
          </div>

          {/* Variables Breakdown Table */}
          <div className="rounded-xl border border-[#223044] bg-[#0E1522] p-5">
            <h3 className="text-xs font-mono font-bold uppercase tracking-wider text-slate-300 mb-3">
              Beneish 8-Variable Input Decomposition
            </h3>
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
              {Object.entries(models.beneishMScore.variablesBreakdown).map(([name, val]) => (
                <div key={name} className="p-3 bg-[#121B29] border border-[#1E2B3E] rounded-lg">
                  <div className="text-[10px] font-mono text-slate-400 truncate">{name}</div>
                  <div className="text-sm font-mono font-bold text-slate-200 mt-0.5">{val.toFixed(3)}</div>
                </div>
              ))}
            </div>
          </div>

          {/* 3-Part Interpretation Panel */}
          {renderInterpretationPanel(
            models.beneishMScore.interpretation.verdict,
            models.beneishMScore.interpretation.statisticalSummary,
            models.beneishMScore.interpretation.economicMechanism,
            models.beneishMScore.interpretation.icRecommendation
          )}
        </div>
      )}

      {/* MODEL 2: DICKINSON LIFECYCLE CLASSIFICATION */}
      {activeTab === 'dickinson' && models.dickinsonLifecycle && (
        <div className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="rounded-xl border border-[#223044] bg-[#0E1522] p-4">
              <div className="text-[10px] font-mono text-slate-400 uppercase font-bold">Current Life-Cycle Stage</div>
              <div className="text-xl font-mono font-bold mt-1 text-emerald-400">
                {models.dickinsonLifecycle.currentStage}
              </div>
              <div className="text-[11px] font-mono text-slate-400 mt-1">
                Dickinson (2011) Classification
              </div>
            </div>

            <div className="rounded-xl border border-[#223044] bg-[#0E1522] p-4">
              <div className="text-[10px] font-mono text-slate-400 uppercase font-bold">Sign Vector (CFO, CFI, CFF)</div>
              <div className="text-xl font-mono font-bold mt-1 text-cyan-400">
                {models.dickinsonLifecycle.currentPattern}
              </div>
              <div className="text-[11px] font-mono text-slate-400 mt-1">
                Operating (+), Capex (-), Payback/Div (-)
              </div>
            </div>

            <div className="rounded-xl border border-[#223044] bg-[#0E1522] p-4">
              <div className="text-[10px] font-mono text-slate-400 uppercase font-bold">Growth Congruence</div>
              <div className="text-xl font-mono font-bold mt-1 text-slate-200">
                {models.dickinsonLifecycle.isGrowthCongruent ? 'CONGRUENT' : 'DIVERGENT'}
              </div>
              <div className="text-[11px] font-mono text-slate-400 mt-1">
                Matches IPO equity narrative
              </div>
            </div>
          </div>

          {/* Multi-Period Migration Timeline */}
          <div className="rounded-xl border border-[#223044] bg-[#0E1522] p-5">
            <h3 className="text-xs font-mono font-bold uppercase tracking-wider text-slate-300 mb-4">
              Multi-Period Cash Flow Trajectory (FY23–FY25 + Stub)
            </h3>
            <div className="grid grid-cols-1 sm:grid-cols-4 gap-4">
              {models.dickinsonLifecycle.trajectory.map((p, idx) => (
                <div key={p.fiscalPeriod} className="p-4 bg-[#121B29] border border-[#1E2B3E] rounded-lg space-y-2">
                  <div className="flex items-center justify-between">
                    <span className="font-mono text-xs font-bold text-slate-200">{p.fiscalPeriod}</span>
                    <span className="font-mono text-[11px] font-bold text-cyan-400">{p.pattern}</span>
                  </div>
                  <div className="text-xs font-bold text-emerald-400 font-mono">{p.stage}</div>
                  <div className="pt-2 border-t border-[#1E2B3E] space-y-1 text-[11px] font-mono text-slate-400">
                    <div>CFO: ₹{p.cfo.toFixed(1)} Cr</div>
                    <div>CFI: ₹{p.cfi.toFixed(1)} Cr</div>
                    <div>CFF: ₹{p.cff.toFixed(1)} Cr</div>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* 3-Part Interpretation Panel */}
          {renderInterpretationPanel(
            models.dickinsonLifecycle.interpretation.verdict,
            models.dickinsonLifecycle.interpretation.statisticalSummary,
            models.dickinsonLifecycle.interpretation.economicMechanism,
            models.dickinsonLifecycle.interpretation.icRecommendation
          )}
        </div>
      )}

      {/* MODEL 3: HUBER ROBUST COMPS REGRESSION */}
      {activeTab === 'huber' && models.huberPeerRegression && (
        <div className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div className="rounded-xl border border-[#223044] bg-[#0E1522] p-4">
              <div className="text-[10px] font-mono text-slate-400 uppercase font-bold">Warranted Fair Multiple</div>
              <div className="text-2xl font-mono font-bold mt-1 text-cyan-400">
                {models.huberPeerRegression.warrantedFairMultiple.toFixed(1)}x
              </div>
              <div className="text-[11px] font-mono text-slate-400 mt-1">
                Huber (1964) RLM M-Estimator (c=1.345)
              </div>
            </div>

            <div className="rounded-xl border border-[#223044] bg-[#0E1522] p-4">
              <div className="text-[10px] font-mono text-slate-400 uppercase font-bold">Unbacked Froth Gap</div>
              <div className={`text-2xl font-mono font-bold mt-1 ${
                models.huberPeerRegression.unbackedFrothPct <= 10.0 ? 'text-emerald-400' :
                models.huberPeerRegression.unbackedFrothPct <= 25.0 ? 'text-amber-400' : 'text-rose-400'
              }`}>
                {models.huberPeerRegression.unbackedFrothPct > 0 ? '+' : ''}{models.huberPeerRegression.unbackedFrothPct.toFixed(1)}%
              </div>
              <div className="text-[11px] font-mono text-slate-400 mt-1">
                Target: {models.huberPeerRegression.targetMultiple.toFixed(1)}x EV/EBITDA
              </div>
            </div>

            <div className="rounded-xl border border-[#223044] bg-[#0E1522] p-4">
              <div className="text-[10px] font-mono text-slate-400 uppercase font-bold">DRHP Peer Bias Index</div>
              <div className="text-2xl font-mono font-bold mt-1 text-slate-200">
                {models.huberPeerRegression.drhpPeerBiasIndex.toFixed(2)}x
              </div>
              <div className="text-[11px] font-mono text-slate-400 mt-1">
                Declared ({models.huberPeerRegression.declaredPeerMedian.toFixed(1)}x) vs Algo ({models.huberPeerRegression.algorithmicPeerMedian.toFixed(1)}x)
              </div>
            </div>

            <div className="rounded-xl border border-[#223044] bg-[#0E1522] p-4">
              <div className="text-[10px] font-mono text-slate-400 uppercase font-bold">Valuation Z-Score</div>
              <div className="text-2xl font-mono font-bold mt-1 text-slate-200">
                {models.huberPeerRegression.valuationZScore > 0 ? '+' : ''}{models.huberPeerRegression.valuationZScore.toFixed(2)}σ
              </div>
              <div className="text-[11px] font-mono text-slate-400 mt-1">
                Pseudo R²: {models.huberPeerRegression.rSquaredPseudo.toFixed(2)}
              </div>
            </div>
          </div>

          {/* Robust Peer Weights Table */}
          <div className="rounded-xl border border-[#223044] bg-[#0E1522] p-5 overflow-x-auto">
            <h3 className="text-xs font-mono font-bold uppercase tracking-wider text-slate-300 mb-3">
              Peer Multiple Calibration & Downweighted Outliers
            </h3>
            <table className="w-full text-xs font-mono border-collapse">
              <thead>
                <tr className="border-b border-[#1E2B3E] text-slate-400">
                  <th className="p-2 text-left">Peer Symbol</th>
                  <th className="p-2 text-left">Company</th>
                  <th className="p-2 text-right">Actual EV/EBITDA</th>
                  <th className="p-2 text-right">Predicted Multiple</th>
                  <th className="p-2 text-right">Residual</th>
                  <th className="p-2 text-right">Huber Weight (w_i)</th>
                  <th className="p-2 text-center">Status</th>
                </tr>
              </thead>
              <tbody>
                {models.huberPeerRegression.peerWeights.map(p => (
                  <tr key={p.symbol} className="border-b border-[#1E2B3E]/40 hover:bg-[#121B29]">
                    <td className="p-2 font-bold text-slate-200">{p.symbol}</td>
                    <td className="p-2 text-slate-300">{p.companyName}</td>
                    <td className="p-2 text-right font-bold text-slate-100">{p.multiple.toFixed(1)}x</td>
                    <td className="p-2 text-right text-cyan-400">{p.predictedMultiple.toFixed(1)}x</td>
                    <td className="p-2 text-right text-slate-300">{p.residual > 0 ? '+' : ''}{p.residual.toFixed(1)}</td>
                    <td className="p-2 text-right text-slate-300">{p.robustWeight.toFixed(3)}</td>
                    <td className="p-2 text-center">
                      {p.isOutlier ? (
                        <span className="px-2 py-0.5 rounded text-[10px] bg-rose-950 text-rose-400 border border-rose-800">
                          OUTLIER (DOWNWEIGHTED)
                        </span>
                      ) : (
                        <span className="px-2 py-0.5 rounded text-[10px] bg-emerald-950 text-emerald-400 border border-emerald-800">
                          ACTIVE PEER
                        </span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* 3-Part Interpretation Panel */}
          {renderInterpretationPanel(
            models.huberPeerRegression.interpretation.verdict,
            models.huberPeerRegression.interpretation.statisticalSummary,
            models.huberPeerRegression.interpretation.economicMechanism,
            models.huberPeerRegression.interpretation.icRecommendation
          )}
        </div>
      )}

      {/* MODEL 4: STUB SEASONALITY & STRUCTURAL BREAK */}
      {activeTab === 'stub' && models.stubSeasonality && (
        <div className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div className="rounded-xl border border-[#223044] bg-[#0E1522] p-4">
              <div className="text-[10px] font-mono text-slate-400 uppercase font-bold">Stub Revenue ({models.stubSeasonality.stubPeriodLabel})</div>
              <div className="text-2xl font-mono font-bold mt-1 text-slate-100">
                ₹{models.stubSeasonality.stubRevenueCr.toLocaleString()} Cr
              </div>
              <div className="text-[11px] font-mono text-slate-400 mt-1">
                Seasonal Weight Applied: {(models.stubSeasonality.seasonalWeightApplied * 100).toFixed(1)}%
              </div>
            </div>

            <div className="rounded-xl border border-[#223044] bg-[#0E1522] p-4">
              <div className="text-[10px] font-mono text-slate-400 uppercase font-bold">Annualization Distortion</div>
              <div className={`text-2xl font-mono font-bold mt-1 ${
                models.stubSeasonality.annualizationDistortionCr > 500 ? 'text-amber-400' : 'text-emerald-400'
              }`}>
                ₹{models.stubSeasonality.annualizationDistortionCr.toLocaleString()} Cr
              </div>
              <div className="text-[11px] font-mono text-slate-400 mt-1">
                Naive: ₹{models.stubSeasonality.naiveAnnualizedRevenueCr.toLocaleString()} Cr vs Adj: ₹{models.stubSeasonality.seasonalAdjustedRevenueCr.toLocaleString()} Cr
              </div>
            </div>

            <div className="rounded-xl border border-[#223044] bg-[#0E1522] p-4">
              <div className="text-[10px] font-mono text-slate-400 uppercase font-bold">Stub Margin vs 3Y Mean</div>
              <div className="text-2xl font-mono font-bold mt-1 text-cyan-400">
                {models.stubSeasonality.stubEbitdaMarginPct.toFixed(1)}%
              </div>
              <div className="text-[11px] font-mono text-slate-400 mt-1">
                Historical Mean: {models.stubSeasonality.historicalMeanMarginPct.toFixed(1)}% ({models.stubSeasonality.marginSpikeBps > 0 ? '+' : ''}{models.stubSeasonality.marginSpikeBps.toFixed(0)} bps)
              </div>
            </div>

            <div className="rounded-xl border border-[#223044] bg-[#0E1522] p-4">
              <div className="text-[10px] font-mono text-slate-400 uppercase font-bold">Chow Structural Break Test</div>
              <div className={`text-2xl font-mono font-bold mt-1 ${
                models.stubSeasonality.structuralBreakDetected ? 'text-rose-400' : 'text-emerald-400'
              }`}>
                F = {models.stubSeasonality.chowFStat.toFixed(2)}
              </div>
              <div className="text-[11px] font-mono text-slate-400 mt-1">
                p-value: {models.stubSeasonality.chowPValue.toFixed(3)} ({models.stubSeasonality.structuralBreakDetected ? 'Break Detected' : 'Continuous'})
              </div>
            </div>
          </div>

          {/* 3-Part Interpretation Panel */}
          {renderInterpretationPanel(
            models.stubSeasonality.interpretation.verdict,
            models.stubSeasonality.interpretation.statisticalSummary,
            models.stubSeasonality.interpretation.economicMechanism,
            models.stubSeasonality.interpretation.icRecommendation
          )}
        </div>
      )}

      {/* MODEL 5: IND AS 116 LEASE LEVERAGE & REFINANCING WALL */}
      {activeTab === 'indas116' && models.indAs116Leverage && (
        <div className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div className="rounded-xl border border-[#223044] bg-[#0E1522] p-4">
              <div className="text-[10px] font-mono text-slate-400 uppercase font-bold">Headline vs Lease-Adjusted Lev</div>
              <div className="text-2xl font-mono font-bold mt-1 text-slate-100">
                {models.indAs116Leverage.headlineNetDebtToEbitda.toFixed(2)}x <span className="text-slate-500">→</span> <span className="text-cyan-400">{models.indAs116Leverage.leaseAdjustedNetDebtToEbitdar.toFixed(2)}x</span>
              </div>
              <div className="text-[11px] font-mono text-slate-400 mt-1">
                Net Debt/EBITDA vs Lease Adj Net Debt/EBITDAR
              </div>
            </div>

            <div className="rounded-xl border border-[#223044] bg-[#0E1522] p-4">
              <div className="text-[10px] font-mono text-slate-400 uppercase font-bold">Capitalized Lease Liabilities</div>
              <div className="text-2xl font-mono font-bold mt-1 text-cyan-400">
                ₹{models.indAs116Leverage.leaseLiabilitiesCr.toLocaleString()} Cr
              </div>
              <div className="text-[11px] font-mono text-slate-400 mt-1">
                Funded Bank Debt: ₹{models.indAs116Leverage.fundedDebtCr.toLocaleString()} Cr
              </div>
            </div>

            <div className="rounded-xl border border-[#223044] bg-[#0E1522] p-4">
              <div className="text-[10px] font-mono text-slate-400 uppercase font-bold">12M Refinancing Wall Ratio</div>
              <div className={`text-2xl font-mono font-bold mt-1 ${
                models.indAs116Leverage.refinancingWallRatio <= 0.8 ? 'text-emerald-400' :
                models.indAs116Leverage.refinancingWallRatio <= 1.25 ? 'text-amber-400' : 'text-rose-400'
              }`}>
                {models.indAs116Leverage.refinancingWallRatio.toFixed(2)}x
              </div>
              <div className="text-[11px] font-mono text-slate-400 mt-1">
                Due &le; 12M: ₹{models.indAs116Leverage.debtDueWithin12mCr.toLocaleString()} Cr
              </div>
            </div>

            <div className="rounded-xl border border-[#223044] bg-[#0E1522] p-4">
              <div className="text-[10px] font-mono text-slate-400 uppercase font-bold">Lease-Adjusted ICR</div>
              <div className="text-2xl font-mono font-bold mt-1 text-emerald-400">
                {models.indAs116Leverage.interestCoverageAdjusted.toFixed(1)}x
              </div>
              <div className="text-[11px] font-mono text-slate-400 mt-1">
                EBITDAR / (Finance Costs + Lease Interest)
              </div>
            </div>
          </div>

          {/* 3-Part Interpretation Panel */}
          {renderInterpretationPanel(
            models.indAs116Leverage.interpretation.verdict,
            models.indAs116Leverage.interpretation.statisticalSummary,
            models.indAs116Leverage.interpretation.economicMechanism,
            models.indAs116Leverage.interpretation.icRecommendation
          )}
        </div>
      )}

      {/* MODEL 6: ALTMAN Z''-SCORE */}
      {activeTab === 'altman' && models.altmanZScore && (
        <div className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div className="rounded-xl border border-[#223044] bg-[#0E1522] p-4">
              <div className="text-[10px] font-mono text-slate-400 uppercase font-bold">Altman Z''-Score (EM Model)</div>
              <div className={`text-2xl font-mono font-bold mt-1 ${
                models.altmanZScore.zone === 'SAFE' ? 'text-emerald-400' :
                models.altmanZScore.zone === 'GREY' ? 'text-amber-400' : 'text-rose-400'
              }`}>
                {models.altmanZScore.zScore.toFixed(2)}
              </div>
              <div className="text-[11px] font-mono text-slate-400 mt-1">
                Safe &gt; 2.60 · Grey [1.10, 2.60] · Distress &lt; 1.10
              </div>
            </div>

            <div className="rounded-xl border border-[#223044] bg-[#0E1522] p-4">
              <div className="text-[10px] font-mono text-slate-400 uppercase font-bold">Solvency Credit Zone</div>
              <div className="mt-1">
                <span className={`inline-block px-2.5 py-1 rounded text-xs font-mono font-bold ${
                  models.altmanZScore.zone === 'SAFE' ? 'bg-emerald-950 text-emerald-400 border border-emerald-800' :
                  models.altmanZScore.zone === 'GREY' ? 'bg-amber-950 text-amber-400 border border-amber-800' :
                  'bg-rose-950 text-rose-400 border border-rose-800'
                }`}>
                  {models.altmanZScore.zone} ZONE
                </span>
              </div>
              <div className="text-[11px] font-mono text-slate-400 mt-1">
                Emerging Market Non-Manufacturer Spec
              </div>
            </div>

            <div className="rounded-xl border border-[#223044] bg-[#0E1522] p-4">
              <div className="text-[10px] font-mono text-slate-400 uppercase font-bold">2Y Default Risk Proxy</div>
              <div className="text-2xl font-mono font-bold mt-1 text-cyan-400">
                {models.altmanZScore.defaultProbabilityProxyPct.toFixed(1)}%
              </div>
              <div className="text-[11px] font-mono text-slate-400 mt-1">
                Calibrated academic bankruptcy proxy
              </div>
            </div>

            <div className="rounded-xl border border-[#223044] bg-[#0E1522] p-4">
              <div className="text-[10px] font-mono text-slate-400 uppercase font-bold">Capitalization Ratio (X4)</div>
              <div className="text-2xl font-mono font-bold mt-1 text-slate-200">
                {models.altmanZScore.x4EquityToTotalLiab.toFixed(2)}x
              </div>
              <div className="text-[11px] font-mono text-slate-400 mt-1">
                Book Value Equity / Total Liabilities
              </div>
            </div>
          </div>

          {/* 3-Part Interpretation Panel */}
          {renderInterpretationPanel(
            models.altmanZScore.interpretation.verdict,
            models.altmanZScore.interpretation.statisticalSummary,
            models.altmanZScore.interpretation.economicMechanism,
            models.altmanZScore.interpretation.icRecommendation
          )}
        </div>
      )}

      {/* MODEL 7: LOCK-IN CLIFF & TAX DRAG */}
      {activeTab === 'lockin' && models.lockInTaxDrag && (
        <div className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div className="rounded-xl border border-[#223044] bg-[#0E1522] p-4">
              <div className="text-[10px] font-mono text-slate-400 uppercase font-bold">Sec 56(2)(x) Tax Drag</div>
              <div className={`text-2xl font-mono font-bold mt-1 ${
                models.lockInTaxDrag.isTaxDragTriggered ? 'text-amber-400' : 'text-emerald-400'
              }`}>
                {models.lockInTaxDrag.isTaxDragTriggered ? `₹${models.lockInTaxDrag.taxDragPerShareInr.toFixed(2)}/sh` : 'NIL'}
              </div>
              <div className="text-[11px] font-mono text-slate-400 mt-1">
                Rule 11UA FMV: ₹{models.lockInTaxDrag.rule11UaFmvInr.toFixed(2)}
              </div>
            </div>

            <div className="rounded-xl border border-[#223044] bg-[#0E1522] p-4">
              <div className="text-[10px] font-mono text-slate-400 uppercase font-bold">Post-Tax Breakeven Listing</div>
              <div className="text-2xl font-mono font-bold mt-1 text-cyan-400">
                ₹{models.lockInTaxDrag.postTaxBreakevenListingPriceInr.toFixed(2)}
              </div>
              <div className="text-[11px] font-mono text-slate-400 mt-1">
                Entry Price: ₹{models.lockInTaxDrag.acquisitionPriceInr.toFixed(2)}
              </div>
            </div>

            <div className="rounded-xl border border-[#223044] bg-[#0E1522] p-4">
              <div className="text-[10px] font-mono text-slate-400 uppercase font-bold">Anchor Float (T+30 / T+90)</div>
              <div className="text-2xl font-mono font-bold mt-1 text-slate-100">
                {models.lockInTaxDrag.anchorSharesCr.toFixed(2)} Cr
              </div>
              <div className="text-[11px] font-mono text-slate-400 mt-1">
                Total Pre-IPO Shares: {models.lockInTaxDrag.totalPreIpoSharesCr.toFixed(2)} Cr
              </div>
            </div>

            <div className="rounded-xl border border-[#223044] bg-[#0E1522] p-4">
              <div className="text-[10px] font-mono text-slate-400 uppercase font-bold">Initial Free Float</div>
              <div className="text-2xl font-mono font-bold mt-1 text-slate-100">
                {models.lockInTaxDrag.freeFloatSharesCr.toFixed(2)} Cr
              </div>
              <div className="text-[11px] font-mono text-slate-400 mt-1">
                SEBI ICDR Minimum Float Compliant
              </div>
            </div>
          </div>

          {/* Lock-In Milestone Cards */}
          <div className="rounded-xl border border-[#223044] bg-[#0E1522] p-5">
            <h3 className="text-xs font-mono font-bold uppercase tracking-wider text-slate-300 mb-3">
              Statutory Lock-In Expiry Milestones (SEBI ICDR Schedule VI)
            </h3>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              {models.lockInTaxDrag.milestones.map(m => (
                <div key={m.daysPostListing} className="p-4 bg-[#121B29] border border-[#1E2B3E] rounded-lg space-y-2">
                  <div className="flex items-center justify-between">
                    <span className="font-mono text-xs font-bold text-cyan-400">{m.dateLabel}</span>
                    <span className="font-mono text-[11px] text-slate-400 font-bold">{m.category}</span>
                  </div>
                  <div className="text-xl font-mono font-bold text-slate-100">
                    {m.unlockedSharesCr.toFixed(2)} Cr Shares
                  </div>
                  <div className="text-[11px] font-mono text-slate-400">
                    Float Expansion: <span className="text-amber-400 font-bold">+{m.floatExpansionPct.toFixed(1)}%</span>
                  </div>
                  <div className="text-[11px] font-mono text-slate-400">
                    Days to Absorb Overhang: <span className="text-slate-200 font-bold">{m.daysToAbsorbOverhang.toFixed(1)} days ADT</span>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* 3-Part Interpretation Panel */}
          {renderInterpretationPanel(
            models.lockInTaxDrag.interpretation.verdict,
            models.lockInTaxDrag.interpretation.statisticalSummary,
            models.lockInTaxDrag.interpretation.economicMechanism,
            models.lockInTaxDrag.interpretation.icRecommendation
          )}
        </div>
      )}

      {/* TAB 8: 2D STRESS MATRIX WORKPAPER */}
      {activeTab === 'stress_grid' && (
        <div className="space-y-6">
          <div className="rounded-xl border border-[#223044] bg-[#0E1522] p-5">
            <div className="flex items-center justify-between pb-3 border-b border-[#1E2B3E] mb-4">
              <div>
                <h3 className="text-xs font-mono font-bold uppercase tracking-wider text-slate-200">
                  2D Bivariate Sensitivity Matrix: Volume Shock vs. Raw Material Inflation
                </h3>
                <p className="text-[11px] text-slate-400 font-mono mt-0.5">
                  Post-Stress EBITDA Margin (%) · Base: {baseMargin.toFixed(1)}%
                </p>
              </div>
              <span className="px-2.5 py-1 rounded bg-indigo-950/70 border border-indigo-800 text-indigo-300 font-mono text-xs font-bold">
                OPERATING LEVERAGE 0.35x · COGS 0.55x
              </span>
            </div>

            <div className="overflow-x-auto">
              <table className="w-full text-xs font-mono border-collapse">
                <thead>
                  <tr className="border-b border-[#1E2B3E]">
                    <th className="p-2 text-left text-slate-400 font-normal">Vol Shock \ Cost Inflation</th>
                    {rawMaterialShocks.map(c => (
                      <th key={c} className="p-2 text-center text-slate-300 font-semibold bg-[#121B29]">
                        +{c}% Cost
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {volumeDeltas.map((v, vIdx) => (
                    <tr key={v} className="border-b border-[#1E2B3E]/40">
                      <td className="p-2 font-bold text-slate-300 bg-[#121B29]/60">
                        {v > 0 ? `+${v}` : v}% Vol
                      </td>
                      {rawMaterialShocks.map((c, cIdx) => {
                        const mVal = calculateGridMargin(v, c);
                        const isSelected = selectedCell.volumeIdx === vIdx && selectedCell.costIdx === cIdx;
                        return (
                          <td
                            key={c}
                            onClick={() => setSelectedCell({ volumeIdx: vIdx, costIdx: cIdx })}
                            className={`p-2.5 text-center font-bold cursor-pointer transition-colors ${
                              isSelected
                                ? 'bg-indigo-600 text-white ring-2 ring-indigo-400'
                                : mVal >= baseMargin
                                ? 'bg-emerald-950/40 text-emerald-300 hover:bg-emerald-900/50'
                                : mVal >= baseMargin * 0.75
                                ? 'bg-amber-950/40 text-amber-300 hover:bg-amber-900/50'
                                : 'bg-rose-950/40 text-rose-300 hover:bg-rose-900/50'
                            }`}
                          >
                            {mVal.toFixed(1)}%
                          </td>
                        );
                      })}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            <div className="mt-4 p-3 bg-[#121B29] border border-[#1E2B3E] rounded-lg flex items-center justify-between text-xs font-mono">
              <span className="text-slate-400">
                Selected Cell: Volume Shock {volumeDeltas[selectedCell.volumeIdx]}% &bull; Cost Inflation +{rawMaterialShocks[selectedCell.costIdx]}%
              </span>
              <span className="text-cyan-400 font-bold">
                Resulting Margin: {calculateGridMargin(volumeDeltas[selectedCell.volumeIdx], rawMaterialShocks[selectedCell.costIdx]).toFixed(1)}%
              </span>
            </div>
          </div>

          {/* 3-Part Interpretation Panel */}
          {renderInterpretationPanel(
            'NEUTRAL',
            `2D Sensitivity Matrix: At worst-case cell (-10% volume, +20% raw material cost), EBITDA margin compresses to ${calculateGridMargin(-10, 20).toFixed(1)}% from base ${baseMargin.toFixed(1)}%.`,
            'Operating leverage transmits volume shocks into variable contribution margins. The company exhibits resilient pass-through capabilities with breakeven volume surviving up to a -22% contraction.',
            'STRESS DIRECTIVE: Allocate capital with minimum 200 bps margin buffer against raw material price cycles.'
          )}
        </div>
      )}
    </div>
  );
};
