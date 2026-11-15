import React from 'react';
import { SHAPFeature } from '../types/terminal';
import { Network, HelpCircle, AlertCircle, CheckCircle } from 'lucide-react';

interface SHAPWaterfallChartProps {
  features: SHAPFeature[];
}

export const SHAPWaterfallChart: React.FC<SHAPWaterfallChartProps> = ({ features }) => {
  // Sort features by absolute attribution magnitude
  const sorted = [...features].sort((a, b) => Math.abs(b.attributionValue) - Math.abs(a.attributionValue));
  const maxAbs = Math.max(...sorted.map(f => Math.abs(f.attributionValue)), 0.5);

  return (
    <div className="rounded-lg border border-[#223044] bg-[#101620] p-5 shadow-sm space-y-4">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 pb-3 border-b border-[#1D2838]">
        <div className="flex items-center gap-2">
          <Network className="w-4 h-4 text-cyan-400" />
          <h2 className="text-sm font-semibold tracking-wider text-slate-100 uppercase font-mono">
            SHAP (TreeExplainer) Model Interpretability Waterfall
          </h2>
        </div>
        <div className="flex items-center gap-2 text-xs font-mono text-slate-400">
          <span>TARGET:</span>
          <span className="text-slate-200">Post-Listing BHAR₁₈₀ Alpha</span>
        </div>
      </div>

      <p className="text-xs text-slate-400 font-sans">
        Features pushing the prediction towards outperformance are colored <span className="text-emerald-400 font-semibold">green</span>; features driving the score into the drawdown zone are colored <span className="text-rose-400 font-semibold">crimson</span>.
      </p>

      {/* Waterfall Horizontal Stack */}
      <div className="space-y-3 pt-2">
        {sorted.map((feat) => {
          const isPositive = feat.attributionValue >= 0;
          const barWidthPct = Math.min((Math.abs(feat.attributionValue) / maxAbs) * 100, 100);

          return (
            <div key={feat.featureName} className="p-3 rounded bg-[#090D12] border border-[#1E293B] space-y-2">
              <div className="flex items-center justify-between text-xs">
                <div className="flex items-center gap-2">
                  {feat.isWarning ? (
                    <AlertCircle className="w-3.5 h-3.5 text-rose-400 shrink-0" />
                  ) : (
                    <CheckCircle className="w-3.5 h-3.5 text-emerald-400 shrink-0" />
                  )}
                  <span className="font-semibold text-slate-200">{feat.displayName}</span>
                  <span className="text-[10px] font-mono px-1.5 py-0.2 rounded bg-slate-800 text-slate-400">
                    {feat.category}
                  </span>
                </div>
                <div className="font-mono text-xs tabular-nums font-bold flex items-center gap-2">
                  <span className="text-slate-400 font-normal">Val: {feat.featureValue}</span>
                  <span className={isPositive ? 'text-emerald-400' : 'text-rose-400'}>
                    {isPositive ? '+' : ''}{feat.attributionValue.toFixed(2)} SHAP
                  </span>
                </div>
              </div>

              {/* Centered Zero-Axis Relative Bar */}
              <div className="grid grid-cols-2 gap-0.5 h-2.5 w-full bg-[#151D2A] rounded-full overflow-hidden border border-[#223044] relative">
                {/* Left Half (Negative) */}
                <div className="flex justify-end pr-0.5">
                  {!isPositive && (
                    <div
                      className="h-full bg-gradient-to-l from-rose-500 to-rose-700 rounded-l-full transition-all duration-500"
                      style={{ width: `${barWidthPct}%` }}
                    />
                  )}
                </div>

                {/* Right Half (Positive) */}
                <div className="flex justify-start pl-0.5">
                  {isPositive && (
                    <div
                      className="h-full bg-gradient-to-r from-emerald-500 to-emerald-700 rounded-r-full transition-all duration-500"
                      style={{ width: `${barWidthPct}%` }}
                    />
                  )}
                </div>

                {/* Center Zero Indicator */}
                <div className="absolute left-1/2 top-0 bottom-0 w-[1px] bg-slate-400" />
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
