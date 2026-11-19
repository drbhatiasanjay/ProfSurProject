import React, { useState } from 'react';
import { HuberCalibrationResults } from '../types/terminal';
import { Calculator, AlertTriangle, ShieldAlert, CheckCircle2, Binary, ChevronDown, ChevronUp } from 'lucide-react';

interface HuberCalibrationCardProps {
  calibration: HuberCalibrationResults;
  onOpenAlmanac?: (methodologyId?: string) => void;
}

export const HuberCalibrationCard: React.FC<HuberCalibrationCardProps> = ({ calibration, onOpenAlmanac }) => {
  const [isCollapsed, setIsCollapsed] = useState<boolean>(false);

  return (
    <div
      id="module-huber-calibration"
      className="rounded-xl border border-slate-700/80 border-t-2 border-t-purple-500 bg-[#0C1322] p-5 shadow-xl transition-all space-y-4"
    >
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-3 border-b border-slate-800">
        <div className="flex items-center gap-2.5">
          <div className="p-1.5 rounded-lg bg-purple-950/80 border border-purple-800/60 text-purple-400">
            <Calculator className="w-4 h-4" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="px-1.5 py-0.2 rounded text-[10px] font-mono font-bold bg-purple-950 text-purple-300 border border-purple-800">
                MODULE 01
              </span>
              <h2 className="text-sm font-semibold tracking-wider text-slate-100 uppercase font-mono">
                Huber Robust M-Estimator &amp; DRHP Peer Selection Bias
              </h2>
            </div>
            <p className="text-[11px] text-slate-400 font-mono mt-0.5">
              Bounded-influence regression mitigating cherry-picked peer multiple bias
            </p>
          </div>
        </div>

        <div className="flex items-center gap-3">
          {onOpenAlmanac && (
            <button
              onClick={() => onOpenAlmanac('huber_robust_regression')}
              className="flex items-center gap-1.5 px-2.5 py-1 rounded bg-purple-950/80 border border-purple-700 hover:bg-purple-900 text-xs text-purple-300 font-mono font-bold transition-colors cursor-pointer shadow-sm"
              title="View Huber M-Estimator Equation & Methodology"
            >
              <Calculator className="w-3.5 h-3.5 text-purple-400" />
              <span>METHODOLOGY ⓘ</span>
            </button>
          )}

          <div className="flex items-center gap-2 text-xs font-mono">
            <span className="text-slate-500">NORM:</span>
            <span className="text-cyan-300 bg-cyan-950/60 px-2 py-0.5 rounded border border-cyan-800">
              HuberT(t = 1.345)
            </span>
            <span className="text-slate-500 ml-2">ROBUST R²:</span>
            <span className="text-slate-200">{calibration.rSquaredRobust.toFixed(3)}</span>
          </div>

          <button
            onClick={() => setIsCollapsed(!isCollapsed)}
            className="flex items-center gap-1 px-2.5 py-1 rounded-lg bg-slate-900 border border-slate-700/80 hover:border-slate-500 text-slate-400 hover:text-slate-200 text-xs font-mono transition-all cursor-pointer shadow-sm"
            title={isCollapsed ? 'Expand Huber Cones' : 'Collapse Huber Cones'}
          >
            <span>{isCollapsed ? 'Expand' : 'Collapse'}</span>
            {isCollapsed ? <ChevronDown className="w-3.5 h-3.5" /> : <ChevronUp className="w-3.5 h-3.5" />}
          </button>
        </div>
      </div>

      {!isCollapsed && (
        <>
          {/* KPI Core Comparison Tiles */}
      <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
        {/* Tile 1: Declared Peer Median */}
        <div className="p-3 rounded bg-[#090D12] border border-[#1E293B]">
          <span className="text-[11px] text-slate-400 block mb-1">Declared DRHP Median</span>
          <div className="text-xl font-bold font-mono text-slate-200 tabular-nums">
            {calibration.declaredPeerMedian.toFixed(1)}x
          </div>
          <span className="text-[10px] text-slate-500 font-mono">Cherry-picked comps</span>
        </div>

        {/* Tile 2: Algorithmic Peer Median */}
        <div className="p-3 rounded bg-[#090D12] border border-[#1E293B]">
          <span className="text-[11px] text-slate-400 block mb-1">Algorithmic Comps Median</span>
          <div className="text-xl font-bold font-mono text-cyan-400 tabular-nums">
            {calibration.algorithmicPeerMedian.toFixed(1)}x
          </div>
          <span className="text-[10px] text-cyan-500 font-mono">Cosine feature match</span>
        </div>

        {/* Tile 3: DRHP Selection Bias Index */}
        <div className="p-3 rounded bg-amber-950/20 border border-amber-800/60">
          <span className="text-[11px] text-amber-300 block mb-1 font-medium">DRHP Bias Index</span>
          <div className="text-xl font-bold font-mono text-amber-400 tabular-nums">
            {calibration.drhpBiasIndex.toFixed(2)}x
          </div>
          <span className="text-[10px] text-amber-400 font-mono">Declared ÷ Algo median</span>
        </div>

        {/* Tile 4: Warranted Fair Multiple */}
        <div className="p-3 rounded bg-[#090D12] border border-emerald-900/60">
          <span className="text-[11px] text-emerald-400 block mb-1 font-medium">Warranted Fair P/E</span>
          <div className="text-xl font-bold font-mono text-emerald-300 tabular-nums">
            {calibration.warrantedFairMultiple.toFixed(1)}x
          </div>
          <span className="text-[10px] text-emerald-500 font-mono">Huber calibrated</span>
        </div>

        {/* Tile 5: Unbacked Froth Alert */}
        <div className="p-3 rounded bg-rose-950/30 border border-rose-800/70 col-span-2 md:col-span-1">
          <span className="text-[11px] text-rose-300 block mb-1 font-medium flex items-center gap-1">
            <AlertTriangle className="w-3 h-3 text-rose-400" />
            Unbacked Froth
          </span>
          <div className="text-xl font-bold font-mono text-rose-400 tabular-nums">
            +{calibration.unbackedFrothPct.toFixed(1)}%
          </div>
          <span className="text-[10px] text-rose-400 font-mono">Above fundamentals</span>
        </div>
      </div>

      {/* Econometric Formula Display */}
      <div className="p-3 rounded bg-[#0C111A] border border-[#1E293B] font-mono text-xs flex flex-col md:flex-row md:items-center justify-between gap-2">
        <div className="flex items-center gap-2 text-slate-300">
          <Binary className="w-3.5 h-3.5 text-cyan-400" />
          <span className="text-slate-400">SPECIFICATION:</span>
          <span className="text-cyan-300">{calibration.formula}</span>
        </div>
        <span className="text-[11px] text-slate-500">Winsorized @ 2.5% / 97.5%</span>
      </div>

      {/* Regression Coefficients Breakdown */}
      <div className="border border-[#1E293B] rounded overflow-hidden">
        <table className="w-full text-left text-xs">
          <thead>
            <tr className="border-b border-[#1E293B] text-[11px] font-mono text-slate-400 bg-[#090D12]">
              <th className="py-2 px-3 font-semibold">FUNDAMENTAL COVARIATE</th>
              <th className="py-2 px-3 font-semibold text-right">COEFFICIENT (β)</th>
              <th className="py-2 px-3 font-semibold text-right">T-STATISTIC</th>
              <th className="py-2 px-3 font-semibold text-center">STATISTICAL SIGNIFICANCE</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-[#172230] bg-[#0E141E]">
            {calibration.coefficients.map((c) => {
              const isSignificant = Math.abs(c.tStat) >= 2.0;
              return (
                <tr key={c.feature} className="hover:bg-[#141B26]">
                  <td className="py-2 px-3 font-sans text-slate-300">{c.feature}</td>
                  <td className="py-2 px-3 text-right font-mono font-medium text-slate-100 tabular-nums">
                    {c.weight > 0 ? '+' : ''}
                    {c.weight.toFixed(3)}
                  </td>
                  <td className="py-2 px-3 text-right font-mono font-semibold tabular-nums text-cyan-400">
                    {c.tStat.toFixed(2)}
                  </td>
                  <td className="py-2 px-3 text-center">
                    {isSignificant ? (
                      <span className="text-[10px] font-mono text-emerald-400 px-1.5 py-0.5 rounded bg-emerald-950/60 border border-emerald-800">
                        p &lt; 0.05 (Significant)
                      </span>
                    ) : (
                      <span className="text-[10px] font-mono text-slate-400 px-1.5 py-0.5 rounded bg-slate-800 border border-slate-700">
                        Insignificant
                      </span>
                    )}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>

      {/* Research Analyst Summary Box */}
      <div className="p-3 rounded bg-[#090D12] border border-[#1E293B] flex items-start gap-2.5 text-xs">
        <ShieldAlert className="w-4 h-4 text-rose-400 shrink-0 mt-0.5" />
        <div className="text-slate-300 space-y-1">
          <p className="font-semibold text-rose-300 font-mono">
            VALUATION FORENSIC CONCLUSION:
          </p>
          <p className="text-slate-400 leading-relaxed font-sans">
            The issuer declares comps at a median P/E of <strong className="text-slate-200">{calibration.declaredPeerMedian}x</strong>, yielding a DRHP Peer-Selection Bias Index of <strong className="text-amber-300">{calibration.drhpBiasIndex}x</strong> against algorithmically discovered peers ({calibration.algorithmicPeerMedian}x). After controlling for revenue growth, EBITDA margin, and cash conversion via Huber M-estimation, the warranted fair multiple is <strong className="text-emerald-400">{calibration.warrantedFairMultiple}x</strong>, leaving <strong className="text-rose-400 font-semibold">{calibration.unbackedFrothPct}% unbacked valuation froth</strong>.
          </p>
        </div>
      </div>
      </>
      )}
    </div>
  );
};
