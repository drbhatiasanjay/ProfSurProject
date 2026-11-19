import React, { useState } from 'react';
import {
  TemporalGraphDiffResult,
  TemporalGraphMutation,
  MutationType
} from '../../../types/terminal';
import { FilingDualRedlineDrawer } from './FilingDualRedlineDrawer';

interface BiTemporalGraphMutationCanvasProps {
  diffResult: TemporalGraphDiffResult;
}

export const BiTemporalGraphMutationCanvas: React.FC<BiTemporalGraphMutationCanvasProps> = ({
  diffResult
}) => {
  const [selectedMutation, setSelectedMutation] = useState<TemporalGraphMutation | null>(null);
  const [filterType, setFilterType] = useState<MutationType | 'ALL'>('ALL');

  const filteredMutations = filterType === 'ALL'
    ? diffResult.mutations
    : diffResult.mutations.filter((m) => m.change_type === filterType);

  const getShaderClass = (type: MutationType) => {
    switch (type) {
      case 'ENTITY_ADDED':
        return 'border-emerald-500/50 hover:border-emerald-400 bg-emerald-950/20 shadow-lg shadow-emerald-500/10';
      case 'MUTATED_PROPERTY':
        return 'border-amber-500/50 hover:border-amber-400 bg-amber-950/20 shadow-lg shadow-amber-500/10';
      case 'QUALIFIER_WATERED_DOWN':
        return 'border-purple-500/50 hover:border-purple-400 bg-purple-950/20 shadow-lg shadow-purple-500/10';
      case 'BRACKET_RESOLVED':
        return 'border-cyan-500/50 hover:border-cyan-400 bg-cyan-950/20 shadow-lg shadow-cyan-500/10';
      case 'SEVERED_RELATION':
        return 'border-rose-500/50 hover:border-rose-400 bg-rose-950/20 shadow-lg shadow-rose-500/10';
      default:
        return 'border-slate-800 bg-slate-900';
    }
  };

  const getBadgeColor = (type: MutationType) => {
    switch (type) {
      case 'ENTITY_ADDED':
        return 'bg-emerald-500/20 text-emerald-300 border-emerald-500/30';
      case 'MUTATED_PROPERTY':
        return 'bg-amber-500/20 text-amber-300 border-amber-500/30';
      case 'QUALIFIER_WATERED_DOWN':
        return 'bg-purple-500/20 text-purple-300 border-purple-500/30';
      case 'BRACKET_RESOLVED':
        return 'bg-cyan-500/20 text-cyan-300 border-cyan-500/30';
      case 'SEVERED_RELATION':
        return 'bg-rose-500/20 text-rose-300 border-rose-500/30';
      default:
        return 'bg-slate-800 text-slate-300 border-slate-700';
    }
  };

  return (
    <div className="w-full space-y-4">
      {/* Aggregate Impact HUD */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        {/* Total Mutations */}
        <div className="p-4 rounded-xl bg-slate-950 border border-slate-800 flex items-center justify-between">
          <div>
            <div className="text-[10px] text-slate-400 uppercase font-mono">Verified Mutations</div>
            <div className="text-lg font-bold text-slate-100 font-mono mt-0.5">
              {diffResult.total_mutations} Disclosures
            </div>
          </div>
          <span className="text-xl">📑</span>
        </div>

        {/* Net Valuation Impact */}
        <div className="p-4 rounded-xl bg-slate-950 border border-slate-800 flex items-center justify-between">
          <div>
            <div className="text-[10px] text-slate-400 uppercase font-mono">Net Valuation Delta</div>
            <div
              className={`text-lg font-bold font-mono mt-0.5 ${
                diffResult.net_valuation_impact_inr < 0
                  ? 'text-rose-400'
                  : diffResult.net_valuation_impact_inr > 0
                  ? 'text-emerald-400'
                  : 'text-slate-200'
              }`}
            >
              {diffResult.net_valuation_impact_inr > 0 ? '+' : ''}
              ₹{diffResult.net_valuation_impact_inr.toFixed(2)} Cr
            </div>
          </div>
          <span className="text-xl">💰</span>
        </div>

        {/* Net WACC Shift */}
        <div className="p-4 rounded-xl bg-slate-950 border border-slate-800 flex items-center justify-between">
          <div>
            <div className="text-[10px] text-slate-400 uppercase font-mono">WACC Spread Shift</div>
            <div
              className={`text-lg font-bold font-mono mt-0.5 ${
                diffResult.net_wacc_spread_shift_bps > 0
                  ? 'text-amber-400'
                  : diffResult.net_wacc_spread_shift_bps < 0
                  ? 'text-emerald-400'
                  : 'text-slate-200'
              }`}
            >
              {diffResult.net_wacc_spread_shift_bps > 0 ? '+' : ''}
              {diffResult.net_wacc_spread_shift_bps.toFixed(1)} bps
            </div>
          </div>
          <span className="text-xl">📈</span>
        </div>

        {/* Evasion Index */}
        <div className="p-4 rounded-xl bg-slate-950 border border-slate-800 flex items-center justify-between">
          <div>
            <div className="text-[10px] text-slate-400 uppercase font-mono">Evasion Severity</div>
            <div className="text-lg font-bold text-purple-400 font-mono mt-0.5">
              {(diffResult.overall_obfuscation_index * 100).toFixed(1)}% Index
            </div>
          </div>
          <span className="text-xl">🛡️</span>
        </div>
      </div>

      {/* Filter Tabs */}
      <div className="flex flex-wrap items-center gap-2 border-b border-slate-800 pb-2">
        <span className="text-[11px] font-mono text-slate-400 mr-2">Filter Category:</span>
        {(['ALL', 'MUTATED_PROPERTY', 'ENTITY_ADDED', 'BRACKET_RESOLVED', 'QUALIFIER_WATERED_DOWN'] as const).map((cat) => (
          <button
            key={cat}
            onClick={() => setFilterType(cat)}
            className={`px-3 py-1 rounded-lg text-xs font-mono transition-colors ${
              filterType === cat
                ? 'bg-slate-800 text-cyan-300 font-bold border border-cyan-500/40'
                : 'bg-slate-950 text-slate-400 border border-slate-800 hover:text-slate-200'
            }`}
          >
            {cat === 'ALL' ? 'All Mutations (8)' : cat.replace('_', ' ')}
          </button>
        ))}
      </div>

      {/* Mutation Graph Cards Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {filteredMutations.map((m) => {
          const isHighObf = m.obfuscation_severity >= 0.7;

          return (
            <div
              key={m.mutation_id}
              onClick={() => setSelectedMutation(m)}
              className={`p-5 rounded-2xl border transition-all cursor-pointer flex flex-col justify-between space-y-4 hover:scale-[1.01] ${getShaderClass(
                m.change_type
              )}`}
            >
              {/* Header Badges */}
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-2">
                  <span
                    className={`text-[10px] font-mono font-bold px-2.5 py-0.5 rounded border ${getBadgeColor(
                      m.change_type
                    )}`}
                  >
                    {m.change_type}
                  </span>
                  <span className="text-[10px] font-mono text-slate-400">
                    {m.sebi_chapter.replace('CHAPTER_', 'SEBI CH. ')}
                  </span>
                </div>

                {isHighObf && (
                  <span className="text-[10px] font-mono font-bold px-2 py-0.5 rounded bg-rose-500/20 text-rose-300 border border-rose-500/30 flex items-center space-x-1">
                    <span>▲</span>
                    <span>HIGH EVASION</span>
                  </span>
                )}
              </div>

              {/* Subject & Summary */}
              <div className="space-y-1.5">
                <h4 className="text-xs font-bold text-slate-100 flex items-center justify-between">
                  <span>{m.summary_explanation}</span>
                </h4>
                <div className="text-[11px] font-mono text-cyan-300/80 truncate">
                  Subject: {m.subject_entity}
                </div>
              </div>

              {/* Mutation Preview Comparison */}
              <div className="p-3 rounded-xl bg-slate-950/80 border border-slate-800 space-y-2 text-xs font-mono">
                {m.drhp_value && (
                  <div className="text-amber-300/80 flex items-start space-x-2 line-through decoration-rose-500">
                    <span className="text-slate-500 flex-shrink-0">DRHP:</span>
                    <span className="truncate">{m.drhp_value}</span>
                  </div>
                )}
                <div className="text-emerald-300 flex items-start space-x-2 font-semibold">
                  <span className="text-slate-400 flex-shrink-0">RHP:</span>
                  <span className="truncate">{m.rhp_value}</span>
                </div>
              </div>

              {/* Bottom Metrics & Click CTA */}
              <div className="pt-2 border-t border-slate-800/80 flex items-center justify-between text-[11px] font-mono">
                <div className="flex items-center space-x-3">
                  <span
                    className={
                      m.valuation_impact_inr < 0
                        ? 'text-rose-400 font-bold'
                        : m.valuation_impact_inr > 0
                        ? 'text-emerald-400 font-bold'
                        : 'text-slate-400'
                    }
                  >
                    Val: {m.valuation_impact_inr > 0 ? '+' : ''}₹{m.valuation_impact_inr.toFixed(1)} Cr
                  </span>
                  <span
                    className={
                      m.wacc_spread_shift_bps > 0
                        ? 'text-amber-400'
                        : m.wacc_spread_shift_bps < 0
                        ? 'text-emerald-400'
                        : 'text-slate-400'
                    }
                  >
                    WACC: {m.wacc_spread_shift_bps > 0 ? '+' : ''}{m.wacc_spread_shift_bps.toFixed(1)} bps
                  </span>
                </div>

                <span className="text-cyan-400 hover:text-cyan-300 font-sans text-xs flex items-center space-x-1">
                  <span>Inspect Redline</span>
                  <span>➔</span>
                </span>
              </div>
            </div>
          );
        })}
      </div>

      {/* Synchronized Dual Redline Reader Modal */}
      <FilingDualRedlineDrawer
        mutation={selectedMutation}
        onClose={() => setSelectedMutation(null)}
      />
    </div>
  );
};
