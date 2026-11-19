import React from 'react';
import { TemporalFilingVersion } from '../../../types/terminal';

interface TemporalFilingScrubberProps {
  baseVersion: TemporalFilingVersion;
  targetVersion: TemporalFilingVersion;
  onSelectVersions: (base: TemporalFilingVersion, target: TemporalFilingVersion) => void;
  isLoading?: boolean;
}

interface MilestoneOption {
  key: TemporalFilingVersion;
  label: string;
  tag: string;
  date: string;
  pages: number;
  description: string;
}

const MILESTONES: MilestoneOption[] = [
  {
    key: 'DRHP',
    label: 'Initial DRHP Submission',
    tag: 'DRHP v1.0',
    date: 'Dec 01, 2023',
    pages: 482,
    description: 'Initial draft prospectus filed with SEBI containing unpriced bracketed placeholders'
  },
  {
    key: 'ADDENDUM',
    label: 'SEBI Observation Addendum',
    tag: 'ADDENDUM v2.1',
    date: 'Apr 18, 2024',
    pages: 512,
    description: 'Public corrigendum responding to SEBI Issue Processing Report regulatory queries'
  },
  {
    key: 'RHP',
    label: 'Final Red Herring Prospectus',
    tag: 'RHP v3.2',
    date: 'Oct 15, 2024',
    pages: 546,
    description: 'Final ROC-registered offering document with book-building price band and anchor quota'
  }
];

export const TemporalFilingScrubber: React.FC<TemporalFilingScrubberProps> = ({
  baseVersion,
  targetVersion,
  onSelectVersions,
  isLoading = false
}) => {
  return (
    <div className="w-full bg-slate-950 border border-slate-800 rounded-2xl p-5 shadow-xl space-y-4">
      {/* Header Info */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-2 border-b border-slate-800/80 pb-3">
        <div className="flex items-center space-x-3">
          <div className="w-9 h-9 rounded-xl bg-cyan-500/10 border border-cyan-500/30 flex items-center justify-center text-lg text-cyan-400">
            ⏳
          </div>
          <div>
            <div className="flex items-center space-x-2">
              <h3 className="text-xs font-bold text-slate-100 uppercase tracking-wider">
                Multi-Filing Bi-Temporal Scrubber
              </h3>
              <span className="text-[10px] px-2 py-0.5 rounded-full bg-cyan-500/20 text-cyan-300 font-mono border border-cyan-500/30">
                COHEN-MALLOY TKG
              </span>
            </div>
            <p className="text-xs text-slate-400">
              Scrub between regulatory milestones to detect physical coordinate drift, disguised risk factors, and valuation erosion
            </p>
          </div>
        </div>

        {/* Active Comparison Badge */}
        <div className="flex items-center space-x-2 bg-slate-900 border border-slate-700/80 px-3 py-1.5 rounded-xl">
          <span className="text-[11px] font-mono text-slate-400">Comparing:</span>
          <span className="text-[11px] font-bold font-mono px-2 py-0.5 rounded bg-amber-500/20 text-amber-300 border border-amber-500/30">
            {baseVersion}
          </span>
          <span className="text-slate-500 text-xs">➔</span>
          <span className="text-[11px] font-bold font-mono px-2 py-0.5 rounded bg-emerald-500/20 text-emerald-300 border border-emerald-500/30">
            {targetVersion}
          </span>
        </div>
      </div>

      {/* Scrubbing Track */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-3 pt-1">
        {MILESTONES.map((m, idx) => {
          const isBase = baseVersion === m.key;
          const isTarget = targetVersion === m.key;
          const isSelected = isBase || isTarget;

          return (
            <div
              key={m.key}
              onClick={() => {
                if (m.key === 'DRHP') {
                  onSelectVersions('DRHP', targetVersion === 'DRHP' ? 'RHP' : targetVersion);
                } else if (m.key === 'RHP') {
                  onSelectVersions(baseVersion === 'RHP' ? 'DRHP' : baseVersion, 'RHP');
                } else {
                  // ADDENDUM selected
                  onSelectVersions('DRHP', 'ADDENDUM');
                }
              }}
              className={`p-4 rounded-xl border transition-all cursor-pointer flex flex-col justify-between space-y-2 relative overflow-hidden ${
                isSelected
                  ? isBase
                    ? 'bg-amber-950/20 border-amber-500/50 shadow-lg shadow-amber-500/5'
                    : 'bg-emerald-950/20 border-emerald-500/50 shadow-lg shadow-emerald-500/5'
                  : 'bg-slate-900/60 border-slate-800 hover:border-slate-700 hover:bg-slate-900'
              }`}
            >
              {/* Step Marker Badge */}
              <div className="flex items-center justify-between">
                <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-slate-800 text-slate-300">
                  Step 0{idx + 1}
                </span>
                <span
                  className={`text-[10px] font-bold font-mono px-2 py-0.5 rounded ${
                    isBase
                      ? 'bg-amber-500/20 text-amber-300 border border-amber-500/30'
                      : isTarget
                      ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/30'
                      : 'bg-slate-800 text-slate-400'
                  }`}
                >
                  {isBase ? 'BASE SNAPSHOT' : isTarget ? 'TARGET SNAPSHOT' : m.tag}
                </span>
              </div>

              {/* Title & Metadata */}
              <div>
                <h4 className="text-xs font-bold text-slate-200">{m.label}</h4>
                <div className="flex items-center space-x-3 text-[11px] text-slate-400 font-mono mt-1">
                  <span>📅 {m.date}</span>
                  <span>📄 {m.pages} Pages</span>
                </div>
              </div>

              <p className="text-[11px] text-slate-400 leading-relaxed line-clamp-2">
                {m.description}
              </p>

              {/* Quick Select Actions */}
              <div className="pt-2 border-t border-slate-800/60 flex items-center justify-between text-[10px]">
                <button
                  type="button"
                  onClick={(e) => {
                    e.stopPropagation();
                    if (m.key !== targetVersion) onSelectVersions(m.key, targetVersion);
                  }}
                  className={`px-2 py-1 rounded transition-colors ${
                    isBase ? 'bg-amber-500 text-slate-950 font-bold' : 'bg-slate-800 text-slate-300 hover:bg-slate-700'
                  }`}
                >
                  Set as Base
                </button>
                <button
                  type="button"
                  onClick={(e) => {
                    e.stopPropagation();
                    if (m.key !== baseVersion) onSelectVersions(baseVersion, m.key);
                  }}
                  className={`px-2 py-1 rounded transition-colors ${
                    isTarget ? 'bg-emerald-500 text-slate-950 font-bold' : 'bg-slate-800 text-slate-300 hover:bg-slate-700'
                  }`}
                >
                  Set as Target
                </button>
              </div>
            </div>
          );
        })}
      </div>

      {isLoading && (
        <div className="flex items-center justify-center space-x-2 text-xs text-cyan-400 py-1">
          <span className="animate-spin">🔄</span>
          <span>Computing bi-temporal graph isomorphism and coordinate drift across 546 pages...</span>
        </div>
      )}
    </div>
  );
};
