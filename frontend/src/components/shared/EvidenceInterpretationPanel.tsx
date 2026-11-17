import React, { useState } from 'react';
import { AnalyticalInterpretation, Polarity, CitedInput } from '../../types/terminal';

interface EvidenceInterpretationPanelProps {
  interpretation?: AnalyticalInterpretation;
  title?: string;
  className?: string;
  compact?: boolean;
  onCitationClick?: (pageNumber: number, attributeId?: string) => void;
}

export const EvidenceInterpretationPanel: React.FC<EvidenceInterpretationPanelProps> = ({
  interpretation,
  title,
  className = '',
  compact = false,
  onCitationClick,
}) => {
  const [isBlindSpotsExpanded, setIsBlindSpotsExpanded] = useState<boolean>(true);

  if (!interpretation) {
    return null;
  }

  const { polarity, headline, whatItMeans, evidenceBasis, callToAction, missingDataAndBlindSpots } = interpretation;

  // Semantic visual mapping for Polarity
  const getPolarityBadge = (p: Polarity) => {
    switch (p) {
      case 'POSITIVE_CONTRIBUTOR':
        return (
          <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/30 shadow-[0_0_12px_rgba(16,185,129,0.15)]">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
            + POSITIVE CONTRIBUTOR
          </span>
        );
      case 'NEGATIVE_CONTRIBUTOR':
        return (
          <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold bg-rose-500/10 text-rose-400 border border-rose-500/30 shadow-[0_0_12px_rgba(244,63,94,0.15)]">
            <span className="w-1.5 h-1.5 rounded-full bg-rose-400" />
            - NEGATIVE CONTRIBUTOR
          </span>
        );
      case 'BLOCKING_RISK':
        return (
          <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold bg-red-950/60 text-red-300 border border-red-500/50 shadow-[0_0_15px_rgba(239,68,68,0.25)] animate-pulse">
            <span className="w-1.5 h-1.5 rounded-full bg-red-500" />
            ⛔ BLOCKING RISK
          </span>
        );
      case 'NEUTRAL_MONITOR':
      default:
        return (
          <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold bg-amber-500/10 text-amber-400 border border-amber-500/30">
            <span className="w-1.5 h-1.5 rounded-full bg-amber-400" />
            ⚪ NEUTRAL MONITOR
          </span>
        );
    }
  };

  const getBorderAccent = (p: Polarity) => {
    switch (p) {
      case 'POSITIVE_CONTRIBUTOR':
        return 'border-l-emerald-500';
      case 'NEGATIVE_CONTRIBUTOR':
        return 'border-l-rose-500';
      case 'BLOCKING_RISK':
        return 'border-l-red-500';
      case 'NEUTRAL_MONITOR':
      default:
        return 'border-l-amber-500';
    }
  };

  const getCtaCardStyling = (p: Polarity) => {
    switch (p) {
      case 'POSITIVE_CONTRIBUTOR':
        return 'bg-emerald-950/30 border-emerald-500/30 text-emerald-200';
      case 'NEGATIVE_CONTRIBUTOR':
        return 'bg-rose-950/30 border-rose-500/30 text-rose-200';
      case 'BLOCKING_RISK':
        return 'bg-red-950/50 border-red-500/40 text-red-200';
      case 'NEUTRAL_MONITOR':
      default:
        return 'bg-amber-950/30 border-amber-500/30 text-amber-200';
    }
  };

  return (
    <div
      className={`rounded-xl border border-slate-800/80 bg-gradient-to-b from-[#0F172A]/90 to-[#0B0F19]/90 backdrop-blur-md shadow-xl overflow-hidden ${className}`}
    >
      {/* Panel Header */}
      <div className={`px-5 py-4 border-b border-slate-800/80 flex flex-wrap items-center justify-between gap-3 border-l-4 ${getBorderAccent(polarity)}`}>
        <div className="flex items-center gap-2.5">
          <div className="w-2 h-2 rounded-full bg-cyan-400 shadow-[0_0_8px_rgba(34,211,238,0.8)]" />
          <h4 className="text-sm font-semibold tracking-wide text-slate-100 uppercase">
            {title || 'Evidence-Based Decision Intelligence'}
          </h4>
        </div>
        {getPolarityBadge(polarity)}
      </div>

      <div className="p-5 space-y-5">
        {/* 1. Headline Banner */}
        <div className="bg-slate-900/60 rounded-lg p-3.5 border border-slate-800 flex items-start gap-3">
          <div className="mt-0.5 text-cyan-400 shrink-0">
            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          </div>
          <div>
            <div className="text-xs uppercase tracking-wider font-mono text-slate-400 mb-0.5">Institutional Finding</div>
            <div className="text-sm font-semibold text-slate-100 leading-snug">{headline}</div>
          </div>
        </div>

        {/* 2. "What This Means" Domain-Specific Narrative */}
        <div className="space-y-1.5">
          <div className="flex items-center gap-1.5 text-xs font-semibold text-slate-300 uppercase tracking-wider">
            <svg className="w-3.5 h-3.5 text-blue-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
            </svg>
            What This Number Means Economically
          </div>
          <p className="text-xs sm:text-sm text-slate-300 leading-relaxed bg-slate-900/30 p-3 rounded-lg border border-slate-800/50">
            {whatItMeans}
          </p>
        </div>

        {/* 3. Evidence Basis & Cited DRHP Inputs */}
        {evidenceBasis && (
          <div className="space-y-2 bg-slate-900/40 p-3.5 rounded-lg border border-slate-800/60">
            <div className="flex items-center justify-between text-xs">
              <span className="font-mono text-slate-400 uppercase tracking-wider">Governing Formulation</span>
              <span className="font-mono text-cyan-300 font-medium text-[11px] truncate max-w-[280px] sm:max-w-md">
                {evidenceBasis.formulaOrMethod}
              </span>
            </div>

            {evidenceBasis.citedInputs && evidenceBasis.citedInputs.length > 0 && (
              <div className="pt-2 border-t border-slate-800/60">
                <div className="text-[11px] font-mono text-slate-400 uppercase tracking-wider mb-1.5">
                  Verified Upstream DRHP Inputs
                </div>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                  {evidenceBasis.citedInputs.map((input: CitedInput, idx: number) => (
                    <div
                      key={`${input.attributeId}-${idx}`}
                      className="flex items-center justify-between bg-slate-950/60 px-2.5 py-1.5 rounded border border-slate-800 text-xs hover:border-cyan-500/40 transition-colors"
                    >
                      <span className="text-slate-300 truncate mr-2" title={input.label}>
                        {input.label}
                      </span>
                      <div className="flex items-center gap-1.5 shrink-0">
                        <span className="font-mono font-semibold text-slate-100 tabular-nums">
                          {input.valueDisplay}
                        </span>
                        <button
                          type="button"
                          onClick={() => onCitationClick?.(input.pageNumber, input.attributeId)}
                          className="px-1.5 py-0.5 rounded bg-blue-500/20 text-blue-300 hover:bg-blue-500/30 text-[10px] font-mono font-semibold border border-blue-500/30 transition-colors"
                          title={`Click to view citation on DRHP Page ${input.pageNumber}`}
                        >
                          p. {input.pageNumber}
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}

        {/* 4. Actionable Underwriting Call To Action */}
        <div className={`rounded-lg p-3.5 border ${getCtaCardStyling(polarity)}`}>
          <div className="flex items-center gap-2 mb-1">
            <svg className="w-4 h-4 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
            </svg>
            <span className="text-xs uppercase font-mono tracking-wider font-bold">
              Investment Committee Call to Action
            </span>
          </div>
          <div className="text-xs sm:text-sm font-medium leading-snug pl-6">
            {callToAction}
          </div>
        </div>

        {/* 5. Missing Data & Blind Spots Accordion */}
        {missingDataAndBlindSpots && missingDataAndBlindSpots.length > 0 && (
          <div className="border border-slate-800/80 rounded-lg overflow-hidden">
            <button
              type="button"
              onClick={() => setIsBlindSpotsExpanded(!isBlindSpotsExpanded)}
              className="w-full px-3.5 py-2.5 bg-slate-900/80 hover:bg-slate-900 flex items-center justify-between text-xs font-semibold text-slate-300 transition-colors"
            >
              <div className="flex items-center gap-2">
                <svg className="w-3.5 h-3.5 text-amber-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                </svg>
                <span>Missing Data & Sector Blind Spots ({missingDataAndBlindSpots.length})</span>
              </div>
              <svg
                className={`w-4 h-4 text-slate-400 transform transition-transform ${isBlindSpotsExpanded ? 'rotate-180' : ''}`}
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
              >
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
              </svg>
            </button>

            {isBlindSpotsExpanded && (
              <div className="p-3 bg-slate-950/40 space-y-1.5 border-t border-slate-800/60">
                {missingDataAndBlindSpots.map((spot: string, sIdx: number) => (
                  <div key={sIdx} className="flex items-start gap-2 text-xs text-slate-400 leading-snug">
                    <span className="text-amber-500 font-bold mt-0.5">•</span>
                    <span>{spot}</span>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};

export default EvidenceInterpretationPanel;
