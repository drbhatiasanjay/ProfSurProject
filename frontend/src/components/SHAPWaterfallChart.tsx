import React, { useState } from 'react';
import { SHAPFeature } from '../types/terminal';
import { Network, Sparkles, ChevronUp, ChevronDown } from 'lucide-react';

interface SHAPWaterfallChartProps {
  features?: SHAPFeature[];
  defaultExpanded?: boolean;
}

export const SHAPWaterfallChart: React.FC<SHAPWaterfallChartProps> = ({
  features = [],
  defaultExpanded = true,
}) => {
  const [isExpanded, setIsExpanded] = useState<boolean>(defaultExpanded);

  const featuresList = features || [];
  // Sort features by absolute attribution magnitude
  const sorted = [...featuresList].sort((a, b) => Math.abs(b?.attributionValue ?? 0) - Math.abs(a?.attributionValue ?? 0));
  const maxAbs = Math.max(...sorted.map(f => Math.abs(f?.attributionValue ?? 0)), 0.5);

  const topPositive = sorted.find(f => (f?.attributionValue ?? 0) > 0);
  const topNegative = sorted.find(f => (f?.attributionValue ?? 0) < 0);

  return (
    <div
      id="module-shap-waterfall"
      className="rounded-xl border border-slate-700/80 border-t-2 border-t-indigo-400 bg-gradient-to-b from-[#0E1328] via-[#0A0E1F] to-[#070916] p-5 shadow-xl shadow-black/50 transition-all text-xs font-sans space-y-4"
    >
      {/* Header with Eyebrow Tag & In-Card Toggle */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 pb-3 border-b border-slate-800/80">
        <div className="flex items-center gap-2.5">
          <div className="p-1.5 rounded-lg bg-indigo-950/80 border border-indigo-800/60 text-indigo-400">
            <Network className="w-4 h-4" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="px-1.5 py-0.2 rounded text-[10px] font-mono font-bold bg-indigo-950 text-indigo-300 border border-indigo-800">
                MODULE 03
              </span>
              <h2 className="text-sm font-semibold tracking-wider text-slate-100 uppercase font-mono">
                SHAP (TreeExplainer) Model Interpretability Waterfall
              </h2>
            </div>
            <div className="text-[11px] text-slate-400 font-sans mt-0.5">
              Exact Shapley additive feature attributions for 180-day post-listing alpha
            </div>
          </div>
        </div>

        <div className="flex items-center gap-3">
          <div className="flex items-center gap-1.5 text-xs font-mono text-slate-400">
            <span className="text-slate-500">TARGET:</span>
            <span className="text-indigo-300 font-bold">BHAR₁₈₀ Alpha</span>
          </div>
          <button
            type="button"
            onClick={() => setIsExpanded(!isExpanded)}
            className="flex items-center gap-1 text-[11px] font-mono font-semibold px-2.5 py-1 rounded-md bg-slate-800 hover:bg-slate-700 text-indigo-300 border border-slate-700 cursor-pointer transition-colors"
          >
            <span>{isExpanded ? 'Collapse' : 'Expand'}</span>
            {isExpanded ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
          </button>
        </div>
      </div>

      {/* Summary Attribution Strip */}
      <div className="p-3 rounded-lg bg-[#070914] border border-slate-800/80 flex flex-wrap items-center justify-between gap-3 text-xs">
        <div className="flex items-center gap-2 text-slate-300">
          <Sparkles className="w-4 h-4 text-cyan-400 shrink-0" />
          <span>
            Features pushing prediction towards outperformance are colored <strong className="text-emerald-400 font-mono">green</strong>; features driving score into drawdown zone are colored <strong className="text-rose-400 font-mono">crimson</strong>.
          </span>
        </div>
        {topPositive && (
          <div className="font-mono text-[11px] text-emerald-400">
            Top Outperformer: <strong>{topPositive.displayName || topPositive.featureName}</strong> (+{(topPositive.attributionValue ?? 0).toFixed(2)})
          </div>
        )}
      </div>

      {/* Expanded Waterfall List */}
      {isExpanded && (
        <div className="space-y-3 pt-1 border-t border-slate-800/80 animate-fade-in">
          {sorted.map((feat, idx) => {
            const attr = feat?.attributionValue ?? 0;
            const isPos = attr >= 0;
            const pct = (Math.abs(attr) / maxAbs) * 100;
            const valDisplay = (feat as any)?.rawDisplayValue ?? feat?.featureValue ?? 'N/A';
            const nameDisplay = feat?.displayName || feat?.featureName || `Feature ${idx + 1}`;

            return (
              <div
                key={idx}
                className="p-3 rounded-lg bg-[#070914] border border-slate-800/70 hover:border-indigo-500/40 transition-colors space-y-1.5"
              >
                <div className="flex items-center justify-between text-xs font-mono">
                  <div className="flex items-center gap-2">
                    <span className="text-slate-200 font-semibold">{nameDisplay}</span>
                    <span className="px-1.5 py-0.2 rounded text-[10px] bg-slate-900 border border-slate-800 text-slate-400">
                      {feat?.category || 'General'}
                    </span>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className="text-slate-400 text-[11px]">Val: {valDisplay}</span>
                    <span
                      className={`font-bold tabular-nums text-xs px-2 py-0.5 rounded ${
                        isPos
                          ? 'bg-emerald-950/80 text-emerald-400 border border-emerald-800/60'
                          : 'bg-rose-950/80 text-rose-400 border border-rose-800/60'
                      }`}
                    >
                      {isPos ? `+${attr.toFixed(2)}` : attr.toFixed(2)} SHAP
                    </span>
                  </div>
                </div>

                {/* Horizontal Divergent Bar */}
                <div className="w-full bg-slate-800/80 h-2.5 rounded-full overflow-hidden flex">
                  {isPos ? (
                    <div
                      className="h-full bg-gradient-to-r from-emerald-500 to-emerald-400 rounded-full transition-all duration-300"
                      style={{ width: `${Math.min(100, pct)}%` }}
                    />
                  ) : (
                    <div
                      className="h-full bg-gradient-to-r from-rose-500 to-rose-400 rounded-full transition-all duration-300"
                      style={{ width: `${Math.min(100, pct)}%` }}
                    />
                  )}
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
};

export default SHAPWaterfallChart;
