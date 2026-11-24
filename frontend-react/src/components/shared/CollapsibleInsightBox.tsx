import React, { useState } from 'react';
import { ChevronDown, ChevronRight, Sparkles, Lightbulb, Target, Info, Loader2 } from 'lucide-react';

export interface CollapsibleInsightBoxProps {
  title: string;
  findings?: string[];
  actions?: string[];
  context?: string;
  hasAiInsights?: boolean;
  defaultExpanded?: boolean;
  className?: string;
}

export const CollapsibleInsightBox: React.FC<CollapsibleInsightBoxProps> = ({
  title,
  findings = [],
  actions = [],
  context,
  hasAiInsights = true,
  defaultExpanded = true,
  className = '',
}) => {
  const [isExpanded, setIsExpanded] = useState<boolean>(defaultExpanded);
  const [aiExpanded, setAiExpanded] = useState<boolean>(false);
  const [aiLoading, setAiLoading] = useState<boolean>(false);
  const [aiGeneratedText, setAiGeneratedText] = useState<string | null>(null);

  if ((!findings || findings.length === 0) && (!actions || actions.length === 0) && !context) {
    return null;
  }

  const handleGenerateAi = () => {
    setAiLoading(true);
    setTimeout(() => {
      setAiLoading(false);
      setAiGeneratedText(
        `Cross-sectional econometric assessment confirms the observed dynamics align with Dickinson (2011) lifecycle theory. Capital allocation adjustments reflect differential debt capacity, internal cash-flow retention, and macro transmission effects.`
      );
    }, 900);
  };

  return (
    <div className={`mt-3 rounded-xl border border-white/10 bg-[#0c1220]/80 shadow-md transition-all ${className}`}>
      {/* Header bar */}
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        className="flex w-full items-center justify-between px-4 py-3 text-left font-medium text-slate-200 hover:text-white transition-colors"
      >
        <div className="flex items-center gap-2.5">
          <div className="flex h-5 w-5 items-center justify-center rounded bg-cyan-500/10 text-cyan-400">
            {isExpanded ? <ChevronDown className="h-3.5 w-3.5" /> : <ChevronRight className="h-3.5 w-3.5" />}
          </div>
          <span className="text-xs font-semibold uppercase tracking-wider text-cyan-400">Analysis & Insights</span>
          <span className="text-xs text-slate-400 font-mono">—</span>
          <span className="text-sm font-semibold text-slate-100">{title}</span>
        </div>
        <span className="text-xs text-slate-400 font-mono">{isExpanded ? 'Hide' : 'Expand'}</span>
      </button>

      {/* Expanded Content */}
      {isExpanded && (
        <div className="border-t border-white/5 px-5 py-4 space-y-4 text-xs leading-relaxed">
          {/* Key Findings */}
          {findings && findings.length > 0 && (
            <div>
              <div className="flex items-center gap-1.5 text-xs font-bold text-slate-200 mb-2">
                <Lightbulb className="h-3.5 w-3.5 text-amber-400" />
                <span>Key Findings:</span>
              </div>
              <ul className="space-y-1.5 pl-5 list-disc text-slate-300">
                {findings.map((finding, idx) => (
                  <li key={idx} dangerouslySetInnerHTML={{ __html: finding }} />
                ))}
              </ul>
            </div>
          )}

          {/* Call to Action */}
          {actions && actions.length > 0 && (
            <div className="pt-1 border-t border-white/5">
              <div className="flex items-center gap-1.5 text-xs font-bold text-emerald-400 mb-2">
                <Target className="h-3.5 w-3.5 text-emerald-400" />
                <span>Call to Action:</span>
              </div>
              <ul className="space-y-1.5 pl-5 list-none text-slate-300">
                {actions.map((act, idx) => (
                  <li key={idx} className="flex items-start gap-1.5">
                    <span className="text-emerald-400">🎯</span>
                    <span dangerouslySetInnerHTML={{ __html: act }} />
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* Context Note */}
          {context && (
            <div className="flex items-start gap-2 rounded-lg bg-white/[0.02] border border-white/5 p-2.5 text-slate-400 text-[11px]">
              <Info className="h-3.5 w-3.5 text-cyan-400 flex-shrink-0 mt-0.5" />
              <span>{context}</span>
            </div>
          )}

          {/* AI Insights Collapsible Subsection */}
          {hasAiInsights && (
            <div className="mt-3 rounded-lg border border-purple-500/20 bg-purple-950/20 p-3">
              <button
                onClick={() => setAiExpanded(!aiExpanded)}
                className="flex w-full items-center justify-between text-left text-xs font-medium text-purple-300 hover:text-purple-200"
              >
                <div className="flex items-center gap-2">
                  <Sparkles className="h-3.5 w-3.5 text-purple-400" />
                  <span className="font-semibold">AI Insights (Gemini / Claude Portfolio Copilot)</span>
                </div>
                <div className="flex items-center gap-1 text-[11px] text-purple-400">
                  <span>{aiExpanded ? 'Collapse' : 'View'}</span>
                  {aiExpanded ? <ChevronDown className="h-3 w-3" /> : <ChevronRight className="h-3 w-3" />}
                </div>
              </button>

              {aiExpanded && (
                <div className="mt-2.5 pt-2 border-t border-purple-500/20 text-[11px] text-purple-200/90 space-y-2">
                  {!aiGeneratedText ? (
                    <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-2">
                      <p className="text-slate-400">
                        Synthesizes multi-period corporate finance patterns and covenant risk metrics.
                      </p>
                      <button
                        onClick={handleGenerateAi}
                        disabled={aiLoading}
                        className="flex items-center gap-1.5 px-3 py-1.5 rounded-md bg-purple-600/30 hover:bg-purple-600/50 border border-purple-500/40 text-purple-200 font-medium transition-colors disabled:opacity-50"
                      >
                        {aiLoading ? (
                          <>
                            <Loader2 className="h-3 w-3 animate-spin" />
                            <span>Synthesizing...</span>
                          </>
                        ) : (
                          <>
                            <Sparkles className="h-3 w-3" />
                            <span>Generate AI Analysis</span>
                          </>
                        )}
                      </button>
                    </div>
                  ) : (
                    <div className="rounded bg-black/40 p-2.5 border border-purple-500/30 text-purple-100">
                      <p className="font-mono text-[11px]">{aiGeneratedText}</p>
                    </div>
                  )}
                </div>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  );
};
