import React from 'react';
import { TemporalGraphMutation } from '../../../types/terminal';

interface FilingDualRedlineDrawerProps {
  mutation: TemporalGraphMutation | null;
  onClose: () => void;
}

export const FilingDualRedlineDrawer: React.FC<FilingDualRedlineDrawerProps> = ({
  mutation,
  onClose
}) => {
  if (!mutation) return null;

  const isSevereObfuscation = mutation.obfuscation_severity >= 0.70;
  const isModerateObfuscation = mutation.obfuscation_severity >= 0.40 && mutation.obfuscation_severity < 0.70;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/85 backdrop-blur-md animate-in fade-in duration-200">
      <div className="relative w-full max-w-5xl bg-slate-900 border border-slate-700 rounded-2xl shadow-2xl overflow-hidden flex flex-col max-h-[92vh]">
        {/* Drawer Header */}
        <div className="px-6 py-4 border-b border-slate-800 flex items-center justify-between bg-gradient-to-r from-slate-900 via-slate-900 to-indigo-950/40">
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 rounded-xl bg-cyan-500/10 border border-cyan-500/30 flex items-center justify-center text-xl text-cyan-400">
              ⚖️
            </div>
            <div>
              <div className="flex items-center space-x-2">
                <h3 className="text-sm font-bold text-slate-100 uppercase tracking-wide">
                  Synchronized Dual Redline Document Drawer
                </h3>
                <span className="text-[10px] px-2 py-0.5 rounded font-mono font-bold bg-indigo-500/20 text-indigo-300 border border-indigo-500/30">
                  {mutation.change_type}
                </span>
                <span className="text-[10px] px-2 py-0.5 rounded font-mono bg-slate-800 text-slate-300">
                  {mutation.sebi_chapter.replace('CHAPTER_', 'SEBI CH. ')}
                </span>
              </div>
              <p className="text-xs text-slate-400">
                Ground-truth verbatim comparison with physical bounding-box audit trail under SEBI ICDR Schedule VI
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="w-8 h-8 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-400 hover:text-white flex items-center justify-center transition-colors"
          >
            ✕
          </button>
        </div>

        {/* Content Body */}
        <div className="p-6 overflow-y-auto space-y-6">
          {/* Executive Summary Card */}
          <div className="p-4 rounded-xl bg-slate-950 border border-slate-800 flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
            <div className="space-y-1">
              <span className="text-[10px] font-mono text-slate-400 uppercase tracking-wider">Mutation Thesis</span>
              <h4 className="text-xs font-bold text-slate-200">{mutation.summary_explanation}</h4>
              <div className="text-[11px] font-mono text-cyan-400 flex items-center space-x-2">
                <span>📍 W3C PROV Citation:</span>
                <span>{mutation.w3c_prov_citation}</span>
              </div>
            </div>

            <div className="flex items-center space-x-3 flex-shrink-0">
              {/* Valuation Impact */}
              <div className="p-2.5 rounded-lg bg-slate-900 border border-slate-800 text-center min-w-[110px]">
                <div className="text-[10px] text-slate-400 uppercase">Valuation Impact</div>
                <div
                  className={`text-xs font-bold font-mono ${
                    mutation.valuation_impact_inr < 0
                      ? 'text-rose-400'
                      : mutation.valuation_impact_inr > 0
                      ? 'text-emerald-400'
                      : 'text-slate-300'
                  }`}
                >
                  {mutation.valuation_impact_inr > 0 ? '+' : ''}
                  ₹{mutation.valuation_impact_inr.toFixed(2)} Cr
                </div>
              </div>

              {/* WACC Shift */}
              <div className="p-2.5 rounded-lg bg-slate-900 border border-slate-800 text-center min-w-[90px]">
                <div className="text-[10px] text-slate-400 uppercase">WACC Shift</div>
                <div
                  className={`text-xs font-bold font-mono ${
                    mutation.wacc_spread_shift_bps > 0
                      ? 'text-amber-400'
                      : mutation.wacc_spread_shift_bps < 0
                      ? 'text-emerald-400'
                      : 'text-slate-300'
                  }`}
                >
                  {mutation.wacc_spread_shift_bps > 0 ? '+' : ''}
                  {mutation.wacc_spread_shift_bps.toFixed(1)} bps
                </div>
              </div>

              {/* Obfuscation Score */}
              <div className="p-2.5 rounded-lg bg-slate-900 border border-slate-800 text-center min-w-[110px]">
                <div className="text-[10px] text-slate-400 uppercase">Obfuscation</div>
                <div
                  className={`text-xs font-bold font-mono ${
                    isSevereObfuscation ? 'text-rose-400' : isModerateObfuscation ? 'text-amber-400' : 'text-emerald-400'
                  }`}
                >
                  {(mutation.obfuscation_severity * 100).toFixed(0)}% Index
                </div>
              </div>
            </div>
          </div>

          {/* Obfuscation Evasion Alert */}
          {isSevereObfuscation && (
            <div className="p-3.5 rounded-xl bg-rose-950/30 border border-rose-500/40 flex items-center justify-between text-xs">
              <div className="flex items-center space-x-2 text-rose-300 font-semibold">
                <span>▲</span>
                <span>COHEN-MALLOY STRATEGIC OBFUSCATION DETECTED</span>
              </div>
              <span className="text-[11px] text-rose-200/80">
                Displaced +370 pages from Chapter I (Risk Factors) to back-matter statutory notes
              </span>
            </div>
          )}

          {/* Side-by-Side Verbatim Panes */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {/* Left Pane: DRHP Baseline */}
            <div className="rounded-xl bg-slate-950 border border-slate-800 p-4 space-y-3 flex flex-col justify-between">
              <div className="space-y-2">
                <div className="flex items-center justify-between border-b border-slate-800 pb-2">
                  <div className="flex items-center space-x-2">
                    <span className="text-xs font-bold text-amber-400 uppercase font-mono">DRHP Baseline</span>
                    <span className="text-[10px] px-2 py-0.5 rounded bg-amber-950 text-amber-300 border border-amber-500/30 font-mono">
                      v1.0 (Dec 2023)
                    </span>
                  </div>
                  <span className="text-xs font-mono text-slate-400">
                    {mutation.drhp_bbox ? `Page ${mutation.drhp_bbox.page_number}` : 'Absent in Filing'}
                  </span>
                </div>

                {mutation.drhp_bbox ? (
                  <div className="p-3.5 rounded-lg bg-slate-900/90 border border-slate-800 font-mono text-xs leading-relaxed text-amber-200/90 line-through decoration-rose-500 decoration-2">
                    "{mutation.drhp_bbox.verbatim_text}"
                  </div>
                ) : (
                  <div className="p-6 rounded-lg bg-slate-900/40 border border-dashed border-slate-800 text-center text-xs text-slate-500 font-mono">
                    [DISCLOSURE WAS ENTIRELY ABSENT IN INITIAL DRHP]
                  </div>
                )}
              </div>

              {mutation.drhp_bbox && (
                <div className="text-[10px] font-mono text-slate-500 pt-2 border-t border-slate-800/60 flex items-center justify-between">
                  <span>Physical BBox: [{mutation.drhp_bbox.x}, {mutation.drhp_bbox.y}, {mutation.drhp_bbox.width}, {mutation.drhp_bbox.height}]</span>
                  <span>Unrevised Draft</span>
                </div>
              )}
            </div>

            {/* Right Pane: RHP Target */}
            <div className="rounded-xl bg-slate-950 border border-slate-800 p-4 space-y-3 flex flex-col justify-between">
              <div className="space-y-2">
                <div className="flex items-center justify-between border-b border-slate-800 pb-2">
                  <div className="flex items-center space-x-2">
                    <span className="text-xs font-bold text-emerald-400 uppercase font-mono">RHP Amended Target</span>
                    <span className="text-[10px] px-2 py-0.5 rounded bg-emerald-950 text-emerald-300 border border-emerald-500/30 font-mono">
                      v3.2 (Oct 2024)
                    </span>
                  </div>
                  <span className="text-xs font-mono text-slate-400">
                    Page {mutation.rhp_bbox.page_number}
                  </span>
                </div>

                <div className="p-3.5 rounded-lg bg-slate-900/90 border border-emerald-500/30 font-mono text-xs leading-relaxed text-emerald-200 bg-emerald-950/10">
                  "{mutation.rhp_bbox.verbatim_text}"
                </div>
              </div>

              <div className="text-[10px] font-mono text-slate-500 pt-2 border-t border-slate-800/60 flex items-center justify-between">
                <span>Physical BBox: [{mutation.rhp_bbox.x}, {mutation.rhp_bbox.y}, {mutation.rhp_bbox.width}, {mutation.rhp_bbox.height}]</span>
                <span className="text-emerald-400 font-semibold">Amended Regulatory Copy</span>
              </div>
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="px-6 py-3 border-t border-slate-800 bg-slate-950 flex items-center justify-between text-xs text-slate-400">
          <span className="font-mono">
            Mutation Token: <strong className="text-slate-200">{mutation.mutation_id}</strong> · Subject: <strong className="text-cyan-300">{mutation.subject_entity}</strong>
          </span>
          <button
            onClick={onClose}
            className="px-4 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 font-medium transition-colors"
          >
            Close Reader
          </button>
        </div>
      </div>
    </div>
  );
};
