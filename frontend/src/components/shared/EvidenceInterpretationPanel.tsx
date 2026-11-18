import React, { useState } from 'react';
import {
  AnalyticalInterpretation,
  Polarity,
  CitedInput,
  LiteratureEvidenceCitation,
} from '../../types/terminal';
import {
  Calculator,
  FileText,
  BookOpen,
  ChevronDown,
  AlertTriangle,
  ExternalLink,
  ShieldAlert,
  Sparkles,
  Info,
} from 'lucide-react';

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
  const [activeShelfTab, setActiveShelfTab] = useState<'method' | 'drhp' | 'literature'>('method');
  const [isBlindSpotsExpanded, setIsBlindSpotsExpanded] = useState<boolean>(true);

  if (!interpretation) {
    return null;
  }

  const {
    polarity,
    headline,
    whatItMeans,
    evidenceBasis,
    callToAction,
    missingDataAndBlindSpots,
  } = interpretation;

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
        return (
          <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold bg-amber-500/10 text-amber-400 border border-amber-500/30">
            <span className="w-1.5 h-1.5 rounded-full bg-amber-400" />
            ⚪ NEUTRAL MONITOR
          </span>
        );
      default: {
        const _exhaustive: never = p;
        return (
          <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold bg-slate-500/10 text-slate-400 border border-slate-500/30">
            {String(_exhaustive)}
          </span>
        );
      }
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
        return 'border-l-amber-500';
      default: {
        const _exhaustive: never = p;
        return 'border-l-slate-500';
      }
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
        return 'bg-amber-950/30 border-amber-500/30 text-amber-200';
      default: {
        const _exhaustive: never = p;
        return 'bg-slate-950/30 border-slate-500/30 text-slate-200';
      }
    }
  };

  const lit = evidenceBasis?.governingLiterature;
  const computedVars = evidenceBasis?.computedVariables;

  return (
    <div
      className={`rounded-xl border border-slate-800/80 bg-gradient-to-b from-[#0F172A]/95 to-[#0B0F19]/95 backdrop-blur-md shadow-xl overflow-hidden ${className}`}
    >
      {/* ─────────────────────────────────────────────────────────────
          PANEL HEADER: Title, Formula Chip & Polarity Badge
          ───────────────────────────────────────────────────────────── */}
      <div
        className={`px-5 py-4 border-b border-slate-800/80 flex flex-wrap items-center justify-between gap-3 border-l-4 ${getBorderAccent(
          polarity
        )}`}
      >
        <div className="flex items-center gap-2.5 min-w-0">
          <div className="w-2 h-2 rounded-full bg-cyan-400 shadow-[0_0_8px_rgba(34,211,238,0.8)] shrink-0" />
          <h4 className="text-sm font-semibold tracking-wide text-slate-100 uppercase truncate">
            {title || 'Evidence-Based Decision Intelligence'}
          </h4>
        </div>
        <div className="flex items-center gap-2 shrink-0">
          {lit && (
            <span className="hidden sm:inline-flex items-center gap-1 px-2 py-0.5 rounded text-[10px] font-mono font-semibold bg-cyan-950/80 text-cyan-300 border border-cyan-800">
              {lit.shortTag}
            </span>
          )}
          {getPolarityBadge(polarity)}
        </div>
      </div>

      <div className="p-5 space-y-5">
        {/* ─────────────────────────────────────────────────────────────
            TOP EXECUTIVE LAYER: Finding Headline, Economic Meaning & IC CTA
            ───────────────────────────────────────────────────────────── */}
        {/* 1. Finding Headline Banner */}
        <div className="bg-slate-900/70 rounded-lg p-3.5 border border-slate-800 flex items-start gap-3">
          <div className="mt-0.5 text-cyan-400 shrink-0">
            <Sparkles className="w-4 h-4 text-cyan-400" />
          </div>
          <div>
            <div className="text-[10px] uppercase tracking-wider font-mono text-slate-400 mb-0.5">
              Institutional Finding
            </div>
            <div className="text-sm font-semibold text-slate-100 leading-snug">{headline}</div>
          </div>
        </div>

        {/* 2. "What This Number Means Economically" Narrative */}
        <div className="space-y-1.5">
          <div className="flex items-center gap-1.5 text-xs font-semibold text-slate-300 uppercase tracking-wider">
            <Info className="w-3.5 h-3.5 text-blue-400" />
            What This Number Means Economically
          </div>
          <p className="text-xs sm:text-sm text-slate-300 leading-relaxed bg-slate-900/40 p-3.5 rounded-lg border border-slate-800/60 font-sans">
            {whatItMeans}
          </p>
        </div>

        {/* 3. Actionable Underwriting Call To Action Card */}
        <div className={`rounded-lg p-3.5 border ${getCtaCardStyling(polarity)}`}>
          <div className="flex items-center gap-2 mb-1">
            <ShieldAlert className="w-4 h-4 shrink-0" />
            <span className="text-xs uppercase font-mono tracking-wider font-bold">
              Investment Committee Action Directive
            </span>
          </div>
          <div className="text-xs sm:text-sm font-medium leading-snug pl-6 font-sans">
            {callToAction}
          </div>
        </div>

        {/* ─────────────────────────────────────────────────────────────
            BOTTOM UTILITY SHELF: Google M3 3-Pill Segmented Navigation
            ───────────────────────────────────────────────────────────── */}
        <div className="border border-slate-800 rounded-xl overflow-hidden bg-[#0A0E17]/80">
          {/* Segmented Control Header */}
          <div className="flex items-center border-b border-slate-800 bg-slate-950/70 p-1">
            <button
              type="button"
              onClick={() => setActiveShelfTab('method')}
              className={`flex-1 py-1.5 px-2 rounded-lg text-xs font-mono font-medium flex items-center justify-center gap-1.5 transition-all cursor-pointer ${
                activeShelfTab === 'method'
                  ? 'bg-cyan-950/90 text-cyan-300 border border-cyan-800/80 shadow-sm'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              <Calculator className="w-3.5 h-3.5 shrink-0" />
              <span>[ 📐 Method & Context ]</span>
            </button>
            <button
              type="button"
              onClick={() => setActiveShelfTab('drhp')}
              className={`flex-1 py-1.5 px-2 rounded-lg text-xs font-mono font-medium flex items-center justify-center gap-1.5 transition-all cursor-pointer ${
                activeShelfTab === 'drhp'
                  ? 'bg-cyan-950/90 text-cyan-300 border border-cyan-800/80 shadow-sm'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              <FileText className="w-3.5 h-3.5 shrink-0" />
              <span>[ 📑 Primary DRHP Evidence ]</span>
            </button>
            <button
              type="button"
              onClick={() => setActiveShelfTab('literature')}
              className={`flex-1 py-1.5 px-2 rounded-lg text-xs font-mono font-medium flex items-center justify-center gap-1.5 transition-all cursor-pointer ${
                activeShelfTab === 'literature'
                  ? 'bg-cyan-950/90 text-cyan-300 border border-cyan-800/80 shadow-sm'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              <BookOpen className="w-3.5 h-3.5 shrink-0" />
              <span>[ 📚 Literature Standard ]</span>
            </button>
          </div>

          {/* Segmented Tab Body */}
          <div className="p-4 text-xs font-sans">
            {/* TAB 1: Method & Pre-IPO Context */}
            {activeShelfTab === 'method' && (
              <div className="space-y-3.5 animate-fade-in">
                {/* Method Concept */}
                {evidenceBasis?.methodologyConcept && (
                  <div>
                    <div className="text-[10px] font-mono text-cyan-400 uppercase tracking-wider mb-1">
                      Methodology Concept
                    </div>
                    <p className="text-slate-300 leading-relaxed bg-slate-900/50 p-2.5 rounded border border-slate-800/70">
                      {evidenceBasis.methodologyConcept}
                    </p>
                  </div>
                )}

                {/* Pre-IPO Underwriting Rationale */}
                {evidenceBasis?.preIpoRationale && (
                  <div>
                    <div className="text-[10px] font-mono text-amber-400 uppercase tracking-wider mb-1">
                      Pre-IPO Underwriting Rationale
                    </div>
                    <p className="text-slate-300 leading-relaxed bg-amber-950/20 p-2.5 rounded border border-amber-900/40">
                      {evidenceBasis.preIpoRationale}
                    </p>
                  </div>
                )}

                {/* Core Formula & Cut-offs */}
                <div className="bg-slate-950 p-3 rounded-lg border border-slate-800 font-mono space-y-2">
                  <div className="flex items-center justify-between text-[11px]">
                    <span className="text-slate-400 uppercase">Core Formula</span>
                    <span className="text-cyan-300 font-bold">{evidenceBasis?.formulaOrMethod}</span>
                  </div>
                  {evidenceBasis?.benchmarkCutoffs && (
                    <div className="pt-2 border-t border-slate-800/70 flex items-start justify-between text-[11px]">
                      <span className="text-slate-400 uppercase shrink-0 mr-2">Cut-offs</span>
                      <span className="text-emerald-400 text-right">{evidenceBasis.benchmarkCutoffs}</span>
                    </div>
                  )}
                </div>

                {/* Computed Variables Grid */}
                {computedVars && Object.keys(computedVars).length > 0 && (
                  <div>
                    <div className="text-[10px] font-mono text-slate-400 uppercase tracking-wider mb-1.5">
                      Computed Quantitative Variables
                    </div>
                    <div className="flex flex-wrap gap-1.5 font-mono">
                      {Object.entries(computedVars).map(([k, v]) => (
                        <span
                          key={k}
                          className="px-2 py-1 rounded bg-slate-900 border border-slate-800 text-[11px] text-slate-200"
                        >
                          <span className="text-slate-400 mr-1">{k}:</span>
                          <span className="text-cyan-300 font-bold">
                            {typeof v === 'number'
                              ? Number.isInteger(v)
                                ? v.toLocaleString()
                                : v.toFixed(3)
                              : String(v)}
                          </span>
                        </span>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            )}

            {/* TAB 2: Primary DRHP Filing Evidence */}
            {activeShelfTab === 'drhp' && (
              <div className="space-y-3 animate-fade-in">
                <div className="text-[10px] font-mono text-slate-400 uppercase tracking-wider mb-1">
                  Statutory Prospectus Disclosures & Verbatim Excerpts
                </div>
                {evidenceBasis?.citedInputs && evidenceBasis.citedInputs.length > 0 ? (
                  <div className="space-y-2.5">
                    {evidenceBasis.citedInputs.map((input: CitedInput, idx: number) => (
                      <div
                        key={`${input.attributeId}-${idx}`}
                        className="bg-slate-950/70 p-3 rounded-lg border border-slate-800 hover:border-cyan-500/40 transition-colors"
                      >
                        <div className="flex items-center justify-between gap-2 mb-1.5">
                          <span className="text-slate-200 font-semibold text-xs">{input.label}</span>
                          <div className="flex items-center gap-2">
                            <span className="font-mono font-bold text-cyan-300 text-xs">
                              {input.valueDisplay}
                            </span>
                            <button
                              type="button"
                              onClick={() => onCitationClick?.(input.pageNumber, input.attributeId)}
                              className="px-2 py-0.5 rounded bg-blue-500/20 text-blue-300 hover:bg-blue-500/30 text-[10px] font-mono font-bold border border-blue-500/30 flex items-center gap-1 cursor-pointer transition-colors"
                              title={`Inspect filing on DRHP page ${input.pageNumber}`}
                            >
                              <span>p. {input.pageNumber}</span>
                              <ExternalLink className="w-2.5 h-2.5" />
                            </button>
                          </div>
                        </div>

                        {input.chapterOrNote && (
                          <div className="text-[10px] font-mono text-slate-500 mb-1">
                            {input.chapterOrNote}
                          </div>
                        )}

                        {input.verbatimSourceQuote && (
                          <p className="text-[11px] text-slate-400 italic bg-slate-900/40 p-2 rounded border border-slate-800/50">
                            "{input.verbatimSourceQuote}"
                          </p>
                        )}
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="text-slate-500 text-xs italic">No primary cited inputs recorded.</div>
                )}
              </div>
            )}

            {/* TAB 3: Governing Literature / Statutory Standard */}
            {activeShelfTab === 'literature' && (
              <div className="space-y-3.5 animate-fade-in">
                {lit ? (
                  <div className="bg-slate-950/70 p-3.5 rounded-lg border border-slate-800 space-y-3 font-sans">
                    <div className="flex items-start justify-between gap-2">
                      <div>
                        <div className="text-[10px] font-mono text-cyan-400 uppercase tracking-wider">
                          Authoritative Reference
                        </div>
                        <div className="text-xs font-semibold text-slate-100 font-mono mt-0.5">
                          {lit.formalCitation}
                        </div>
                      </div>
                      <span className="px-2 py-0.5 rounded text-[10px] font-mono font-bold bg-indigo-950/80 text-indigo-300 border border-indigo-800 shrink-0">
                        {lit.shortTag}
                      </span>
                    </div>

                    <div className="bg-slate-900/60 p-3 rounded border border-slate-800 text-xs text-slate-300 italic leading-relaxed">
                      "{lit.statutoryOrPaperQuote}"
                    </div>

                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 text-[11px] font-mono pt-2 border-t border-slate-800">
                      <div>
                        <span className="text-slate-500 block">Verified Cut-off / Rule:</span>
                        <span className="text-emerald-400 font-bold">{lit.verifiedCutoff}</span>
                      </div>
                      <div>
                        <span className="text-slate-500 block">Journal / Regulatory Body:</span>
                        <span className="text-slate-300">{lit.governingBodyOrJournal}</span>
                      </div>
                    </div>
                  </div>
                ) : (
                  <div className="text-slate-500 text-xs italic">
                    Governing literature citation not attached to this metric.
                  </div>
                )}
              </div>
            )}
          </div>
        </div>

        {/* ─────────────────────────────────────────────────────────────
            COLLAPSIBLE MISSING DATA & SECTOR BLIND SPOTS
            ───────────────────────────────────────────────────────────── */}
        {missingDataAndBlindSpots && missingDataAndBlindSpots.length > 0 && (
          <div className="border border-slate-800/80 rounded-lg overflow-hidden">
            <button
              type="button"
              onClick={() => setIsBlindSpotsExpanded(!isBlindSpotsExpanded)}
              className="w-full px-3.5 py-2.5 bg-slate-900/80 hover:bg-slate-900 flex items-center justify-between text-xs font-semibold text-slate-300 transition-colors cursor-pointer"
            >
              <div className="flex items-center gap-2">
                <AlertTriangle className="w-3.5 h-3.5 text-amber-400 shrink-0" />
                <span>Missing Data & Sector Blind Spots ({missingDataAndBlindSpots.length})</span>
              </div>
              <ChevronDown
                className={`w-4 h-4 text-slate-400 transform transition-transform ${
                  isBlindSpotsExpanded ? 'rotate-180' : ''
                }`}
              />
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
