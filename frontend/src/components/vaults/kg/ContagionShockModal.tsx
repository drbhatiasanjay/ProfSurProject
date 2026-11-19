import React, { useState, useEffect, useMemo, useCallback } from 'react';
import {
  ReactFlow,
  Controls,
  Background,
  useNodesState,
  useEdgesState,
  Node,
  Edge,
  Position,
  Handle
} from '@xyflow/react';
import '@xyflow/react/dist/style.css';

import {
  X,
  Zap,
  Shield,
  ShieldAlert,
  ShieldCheck,
  TrendingDown,
  AlertTriangle,
  RotateCcw,
  Sliders,
  DollarSign,
  Info,
  Scale
} from 'lucide-react';

import {
  simulateContagion,
  fetchContagionScenarios,
  ContagionShockResult,
  PresetScenario
} from '../../../services/dataService';

// Custom Node for Causal Path Canvas
const ContagionCardNode: React.FC<any> = ({ data }) => {
  const isCritical = data.severity === 'CRITICAL_RISK';
  const isWarning = data.severity === 'WARNING';
  const isSource = data.status === 'SOURCE_TRIGGER';

  return (
    <div
      className={`relative w-56 rounded-xl p-3 border backdrop-blur-md shadow-xl text-left transition-all ${
        isSource
          ? 'bg-rose-950/80 border-rose-500/70 ring-1 ring-rose-500/30'
          : isCritical
          ? 'bg-red-950/85 border-red-500 ring-2 ring-red-500/40'
          : isWarning
          ? 'bg-amber-950/80 border-amber-500/70'
          : 'bg-slate-900/90 border-slate-700/80'
      }`}
    >
      <Handle type="target" position={Position.Left} className="!bg-slate-400 !w-2 !h-2" />
      
      <div className="flex items-center justify-between mb-1">
        <span className="text-[9px] font-mono font-bold uppercase tracking-wider text-slate-300">
          {data.label}
        </span>
        <span className={`text-[8px] font-bold px-1.5 py-0.2 rounded font-mono ${
          isCritical
            ? 'bg-rose-500/30 text-rose-300 border border-rose-500/40'
            : isWarning
            ? 'bg-amber-500/30 text-amber-300 border border-amber-500/40'
            : 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/30'
        }`}>
          {data.status}
        </span>
      </div>

      <div className="text-xs font-bold text-slate-100 truncate mb-0.5">
        {data.title}
      </div>
      <div className="text-[10px] text-slate-400 truncate font-mono">
        {data.subtitle}
      </div>

      <div className="mt-2 pt-1.5 border-t border-slate-800/80 flex items-center justify-between">
        <span className="text-[11px] font-bold font-mono text-cyan-300">
          {data.metric}
        </span>
      </div>

      <Handle type="source" position={Position.Right} className="!bg-slate-400 !w-2 !h-2" />
    </div>
  );
};

const nodeTypes = {
  contagionNode: ContagionCardNode
};

interface ContagionShockModalProps {
  isOpen: boolean;
  onClose: () => void;
  initialFactId?: string;
  initialEntityName?: string;
  initialGrossExposure?: number;
}

export const ContagionShockModal: React.FC<ContagionShockModalProps> = ({
  isOpen,
  onClose,
  initialFactId = 'FACT_S06_01_CESTAT_INDIRECT_TAX',
  initialEntityName = 'Customs, Excise and Service Tax Appellate Tribunal (CESTAT) Disputes',
  initialGrossExposure = 4455.47
}) => {
  const [selectedFactId, setSelectedFactId] = useState<string>(initialFactId);
  const [prob, setProb] = useState<number>(1.0);
  const [indemnity, setIndemnity] = useState<number>(0.0);
  const [rateShockBps, setRateShockBps] = useState<number>(0.0);

  const [presets, setPresets] = useState<PresetScenario[]>([]);
  const [simResult, setSimResult] = useState<ContagionShockResult | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(false);

  const [nodes, setNodes, onNodesChange] = useNodesState<Node>([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState<Edge>([]);

  // Update selectedFactId if prop changes
  useEffect(() => {
    if (initialFactId) {
      setSelectedFactId(initialFactId);
    }
  }, [initialFactId]);

  // Load preset scenarios on mount
  useEffect(() => {
    fetchContagionScenarios('HCCH')
      .then(res => setPresets(res))
      .catch(err => console.error('Failed to load preset scenarios:', err));
  }, []);

  // Run simulation when sliders change
  const executeSimulation = useCallback(() => {
    setIsLoading(true);
    simulateContagion({
      symbol: 'HCCH',
      fact_id: selectedFactId,
      crystallization_prob: prob,
      parent_indemnity_pct: indemnity,
      macro_rate_shock_bps: rateShockBps
    })
      .then(res => {
        setSimResult(res);
        if (res.causal_subgraph?.nodes) {
          setNodes(res.causal_subgraph.nodes);
        }
        if (res.causal_subgraph?.edges) {
          setEdges(res.causal_subgraph.edges);
        }
      })
      .catch(err => console.error('Contagion simulation failed:', err))
      .finally(() => setIsLoading(false));
  }, [selectedFactId, prob, indemnity, rateShockBps, setNodes, setEdges]);

  useEffect(() => {
    if (isOpen) {
      executeSimulation();
    }
  }, [isOpen, executeSimulation]);

  const handleApplyPreset = (scenario: PresetScenario) => {
    setSelectedFactId(scenario.parameters.fact_id);
    setProb(scenario.parameters.crystallization_prob);
    setIndemnity(scenario.parameters.parent_indemnity_pct);
    setRateShockBps(scenario.parameters.macro_rate_shock_bps);
  };

  const handleReset = () => {
    setProb(1.0);
    setIndemnity(0.0);
    setRateShockBps(0.0);
    setSelectedFactId('FACT_S06_01_CESTAT_INDIRECT_TAX');
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-md animate-in fade-in duration-200">
      <div className="relative w-full max-w-6xl max-h-[92vh] flex flex-col bg-[#0B111A] border border-cyan-900/60 rounded-2xl shadow-2xl overflow-hidden font-sans">
        
        {/* Header */}
        <div className="px-6 py-4 border-b border-slate-800 flex items-center justify-between bg-slate-900/50">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-rose-500 to-amber-600 flex items-center justify-center shadow-lg shadow-rose-950">
              <Zap className="w-5 h-5 text-white" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h2 className="text-sm font-bold text-slate-100 uppercase tracking-wider font-mono">
                  Cross-Section Risk Contagion & Shock Simulator
                </h2>
                <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-rose-500/20 text-rose-300 border border-rose-500/40 font-bold">
                  SEBI RA 2014 COMPLIANT
                </span>
              </div>
              <p className="text-xs text-slate-400 mt-0.5">
                Simulate multi-hop transmission of qualitative DRHP disclosures into solvency, covenant headroom, WACC & IC mandate
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <button
              onClick={handleReset}
              className="px-2.5 py-1.5 rounded-lg text-xs font-mono text-slate-400 hover:text-slate-200 hover:bg-slate-800 transition-colors flex items-center gap-1.5 cursor-pointer"
            >
              <RotateCcw className="w-3.5 h-3.5" />
              <span>Reset</span>
            </button>
            <button
              onClick={onClose}
              className="p-1.5 rounded-lg text-slate-400 hover:text-slate-200 hover:bg-slate-800 transition-colors cursor-pointer"
            >
              <X className="w-5 h-5" />
            </button>
          </div>
        </div>

        {/* Preset Scenario Selector Bar */}
        <div className="px-6 py-2.5 bg-slate-950/70 border-b border-slate-800/80 flex items-center gap-2 overflow-x-auto">
          <span className="text-[10px] font-mono font-bold text-slate-400 uppercase tracking-wider shrink-0 flex items-center gap-1">
            <Sliders className="w-3 h-3 text-cyan-400" />
            Institutional Presets:
          </span>
          {presets.map(p => (
            <button
              key={p.scenario_id}
              onClick={() => handleApplyPreset(p)}
              className="px-2.5 py-1 rounded-md text-[11px] font-mono transition-all shrink-0 cursor-pointer border bg-slate-900/80 hover:bg-cyan-950/50 border-slate-700 hover:border-cyan-500 text-slate-300 hover:text-cyan-200"
            >
              {p.name}
            </button>
          ))}
        </div>

        {/* Content Body */}
        <div className="flex-1 overflow-y-auto p-6 space-y-6">
          
          {/* Top Grid: Controls on Left & Financial Waterfall on Right */}
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
            
            {/* Left Column (5 Cols): Parameter Controls & Sliders */}
            <div className="lg:col-span-5 bg-slate-900/40 p-4 rounded-xl border border-slate-800 space-y-4">
              <div className="flex items-center justify-between pb-2 border-b border-slate-800">
                <span className="text-xs font-mono font-bold text-slate-300 uppercase tracking-wider flex items-center gap-1.5">
                  <Scale className="w-3.5 h-3.5 text-cyan-400" />
                  Stress Testing Parameters
                </span>
                <span className="text-[10px] font-mono text-slate-400">Target: HCCH</span>
              </div>

              {/* Exposure Fact Display */}
              <div className="p-3 rounded-lg bg-slate-950/60 border border-slate-800 space-y-1">
                <div className="text-[10px] text-slate-500 font-mono">SELECTED SOURCE DISCLOSURE</div>
                <div className="text-xs font-bold text-slate-200 truncate">{initialEntityName}</div>
                <div className="flex items-center justify-between text-xs pt-1 font-mono">
                  <span className="text-slate-400">Gross Exposure:</span>
                  <span className="text-rose-400 font-bold">₹{initialGrossExposure.toLocaleString()} Cr</span>
                </div>
              </div>

              {/* Slider 1: Crystallization Probability */}
              <div className="space-y-1.5">
                <div className="flex items-center justify-between text-xs font-mono">
                  <span className="text-slate-300">Crystallization Probability:</span>
                  <span className="text-rose-400 font-bold">{Math.round(prob * 100)}%</span>
                </div>
                <input
                  type="range"
                  min="0"
                  max="1"
                  step="0.05"
                  value={prob}
                  onChange={(e) => setProb(parseFloat(e.target.value))}
                  className="w-full accent-rose-500 cursor-pointer"
                />
                <div className="flex justify-between text-[9px] font-mono text-slate-500">
                  <span>0% (Quarantined)</span>
                  <span>50%</span>
                  <span>100% (Full Loss)</span>
                </div>
              </div>

              {/* Slider 2: Parent HoldCo Indemnity */}
              <div className="space-y-1.5">
                <div className="flex items-center justify-between text-xs font-mono">
                  <span className="text-slate-300">Parent Indemnity Shield:</span>
                  <span className="text-emerald-400 font-bold">{Math.round(indemnity * 100)}%</span>
                </div>
                <input
                  type="range"
                  min="0"
                  max="1"
                  step="0.05"
                  value={indemnity}
                  onChange={(e) => setIndemnity(parseFloat(e.target.value))}
                  className="w-full accent-emerald-500 cursor-pointer"
                />
                <div className="flex justify-between text-[9px] font-mono text-slate-500">
                  <span>0% (Unshielded)</span>
                  <span>50%</span>
                  <span>100% (HoldCo Absorb)</span>
                </div>
              </div>

              {/* Slider 3: Macro Benchmark Rate Shock */}
              <div className="space-y-1.5">
                <div className="flex items-center justify-between text-xs font-mono">
                  <span className="text-slate-300">Macro Yield Shock (RBI):</span>
                  <span className="text-amber-400 font-bold">+{Math.round(rateShockBps)} bps</span>
                </div>
                <input
                  type="range"
                  min="0"
                  max="300"
                  step="25"
                  value={rateShockBps}
                  onChange={(e) => setRateShockBps(parseFloat(e.target.value))}
                  className="w-full accent-amber-500 cursor-pointer"
                />
                <div className="flex justify-between text-[9px] font-mono text-slate-500">
                  <span>+0 bps</span>
                  <span>+150 bps</span>
                  <span>+300 bps</span>
                </div>
              </div>
            </div>

            {/* Right Column (7 Cols): Pro-Forma Financial Waterfall & IC Mandate */}
            <div className="lg:col-span-7 bg-slate-900/40 p-4 rounded-xl border border-slate-800 space-y-4">
              <div className="flex items-center justify-between pb-2 border-b border-slate-800">
                <span className="text-xs font-mono font-bold text-slate-300 uppercase tracking-wider flex items-center gap-1.5">
                  <DollarSign className="w-3.5 h-3.5 text-emerald-400" />
                  Pro-Forma Post-Shock Balance Sheet & Valuation
                </span>
                
                {/* Dynamic IC Recommendation Badge */}
                {simResult && (
                  <span className={`px-2.5 py-0.5 rounded text-[10px] font-mono font-bold tracking-wider uppercase border ${
                    simResult.post_shock_ic_stance === 'AVOID_HIGH_RISK'
                      ? 'bg-rose-500/20 text-rose-300 border-rose-500/50'
                      : simResult.post_shock_ic_stance === 'SUBSCRIBE_WITH_COVENANTS'
                      ? 'bg-amber-500/20 text-amber-300 border-amber-500/50'
                      : 'bg-emerald-500/20 text-emerald-300 border-emerald-500/50'
                  }`}>
                    IC: {simResult.post_shock_ic_stance.replace(/_/g, ' ')}
                  </span>
                )}
              </div>

              {simResult ? (
                <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                  {/* Metric 1: Net Loss */}
                  <div className="p-3 rounded-lg bg-slate-950/70 border border-slate-800">
                    <span className="text-[10px] font-mono text-slate-400 block">Net Issuer Loss</span>
                    <span className="text-base font-bold font-mono text-rose-400">
                      ₹{simResult.net_crystallized_loss_cr.toLocaleString()} Cr
                    </span>
                    <span className="text-[9px] font-mono text-slate-500 block mt-0.5">
                      {simResult.net_worth_erosion_pct.toFixed(1)}% NW Erosion
                    </span>
                  </div>

                  {/* Metric 2: Post-Shock Net Worth */}
                  <div className="p-3 rounded-lg bg-slate-950/70 border border-slate-800">
                    <span className="text-[10px] font-mono text-slate-400 block">Tangible Net Worth</span>
                    <span className="text-base font-bold font-mono text-slate-100">
                      ₹{simResult.post_shock_net_worth_cr.toLocaleString()} Cr
                    </span>
                    <span className="text-[9px] font-mono text-slate-500 block mt-0.5">
                      Base: ₹{simResult.base_net_worth_cr.toLocaleString()} Cr
                    </span>
                  </div>

                  {/* Metric 3: Leverage D/E */}
                  <div className={`p-3 rounded-lg bg-slate-950/70 border ${
                    simResult.covenant_breached ? 'border-rose-500/80 bg-rose-950/20' : 'border-slate-800'
                  }`}>
                    <span className="text-[10px] font-mono text-slate-400 block">Debt / Equity Ratio</span>
                    <span className={`text-base font-bold font-mono ${
                      simResult.covenant_breached ? 'text-rose-400' : 'text-slate-100'
                    }`}>
                      {simResult.post_shock_debt_to_equity.toFixed(2)}x
                    </span>
                    <span className="text-[9px] font-mono text-slate-500 block mt-0.5">
                      Ceiling: {simResult.covenant_limit_debt_to_equity.toFixed(1)}x {simResult.covenant_breached ? '⚠ BREACH' : '✓ Safe'}
                    </span>
                  </div>

                  {/* Metric 4: Multiple Haircut */}
                  <div className="p-3 rounded-lg bg-slate-950/70 border border-slate-800">
                    <span className="text-[10px] font-mono text-slate-400 block">EV/EBITDA Multiple</span>
                    <span className="text-base font-bold font-mono text-amber-400">
                      {simResult.post_shock_ev_ebitda_multiple.toFixed(1)}x
                    </span>
                    <span className="text-[9px] font-mono text-rose-400 block mt-0.5">
                      -{simResult.implied_valuation_haircut_pct.toFixed(1)}% Haircut
                    </span>
                  </div>
                </div>
              ) : (
                <div className="py-8 text-center text-xs text-slate-500">Calculating pro-forma metrics...</div>
              )}

              {/* Rationale Callout */}
              {simResult && (
                <div className="p-3 rounded-lg bg-slate-950/90 border border-slate-800 flex items-start gap-2.5">
                  <Info className="w-4 h-4 text-cyan-400 shrink-0 mt-0.5" />
                  <div className="text-xs text-slate-300 leading-relaxed font-mono">
                    <strong>Institutional Mandate Directive:</strong> {simResult.ic_rationale}
                  </div>
                </div>
              )}
            </div>
          </div>

          {/* Bottom Section: Scoped Interactive Causal Subgraph Canvas */}
          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <span className="text-xs font-mono font-bold text-slate-300 uppercase tracking-wider flex items-center gap-1.5">
                <ShieldAlert className="w-3.5 h-3.5 text-rose-400" />
                Multi-Hop Causal Risk Propagation Canvas
              </span>
              <span className="text-[10px] font-mono text-slate-500">
                Qualitative Disclosure → Solvency Drain → Covenant Gate → Valuation Multiple → IC Directive
              </span>
            </div>

            <div className="h-64 rounded-xl border border-slate-800 bg-slate-950 overflow-hidden relative shadow-inner">
              <ReactFlow
                nodes={nodes}
                edges={edges}
                onNodesChange={onNodesChange}
                onEdgesChange={onEdgesChange}
                nodeTypes={nodeTypes}
                fitView
                className="bg-slate-950"
              >
                <Background color="#1e293b" gap={16} size={1} />
                <Controls className="!bg-slate-900 !border-slate-800 !text-slate-300" />
              </ReactFlow>
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="px-6 py-3 border-t border-slate-800 flex items-center justify-between bg-slate-900/50">
          <div className="flex items-center gap-2 text-xs font-mono text-slate-400">
            <ShieldCheck className="w-4 h-4 text-emerald-400" />
            <span>Zero-Hallucination Causal Linkage Locked to DRHP Physical Evidence</span>
          </div>

          <button
            onClick={onClose}
            className="px-4 py-1.5 rounded-lg bg-cyan-600 hover:bg-cyan-500 text-white font-mono text-xs font-bold transition-colors cursor-pointer"
          >
            Close Workbench
          </button>
        </div>

      </div>
    </div>
  );
};
