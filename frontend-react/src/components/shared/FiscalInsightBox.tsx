import React from 'react';
import { Lightbulb, Info, ArrowUpRight, ArrowDownRight, BookOpen } from 'lucide-react';

export interface FiscalInsightBoxProps {
  title?: string;
  findings: string[];
  implications?: string[];
  methodologyCitation?: string;
  className?: string;
}

export const FiscalInsightBox: React.FC<FiscalInsightBoxProps> = ({
  title = 'Empirical Findings & Econometric Insights',
  findings,
  implications = [],
  methodologyCitation,
  className = '',
}) => {
  if (!findings || findings.length === 0) return null;

  return (
    <div
      className={`mt-4 rounded-xl border border-indigo-500/20 bg-[#0a0f1d] p-4 text-xs shadow-sm transition-all hover:border-indigo-500/35 ${className}`}
    >
      <div className="flex items-center justify-between border-b border-white/5 pb-2.5 mb-3">
        <div className="flex items-center gap-2">
          <div className="flex h-6 w-6 items-center justify-center rounded-lg bg-indigo-500/10 text-indigo-400">
            <Lightbulb className="h-3.5 w-3.5" />
          </div>
          <span className="font-bold text-slate-200 tracking-wide">{title}</span>
        </div>
        {methodologyCitation && (
          <div className="flex items-center gap-1.5 text-[11px] font-mono text-cyan-400/90 bg-cyan-500/10 px-2 py-0.5 rounded-full border border-cyan-500/20">
            <BookOpen className="h-3 w-3" />
            <span>{methodologyCitation}</span>
          </div>
        )}
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* Key Quantitative Findings */}
        <div className="space-y-1.5">
          <div className="text-[10px] font-bold uppercase tracking-wider text-slate-400 flex items-center gap-1">
            <Info className="h-3 w-3 text-cyan-400" />
            <span>Key Empirical Observations</span>
          </div>
          <ul className="space-y-1 text-slate-300">
            {findings.map((f, idx) => (
              <li key={idx} className="flex items-start gap-1.5">
                <span className="text-cyan-400 select-none mt-0.5">&bull;</span>
                <span className="leading-relaxed" dangerouslySetInnerHTML={{ __html: formatMarkdownBold(f) }} />
              </li>
            ))}
          </ul>
        </div>

        {/* Corporate Finance & Theoretical Implications */}
        {implications.length > 0 && (
          <div className="space-y-1.5">
            <div className="text-[10px] font-bold uppercase tracking-wider text-slate-400 flex items-center gap-1">
              <ArrowUpRight className="h-3 w-3 text-emerald-400" />
              <span>Capital Structure Implications</span>
            </div>
            <ul className="space-y-1 text-slate-300">
              {implications.map((imp, idx) => (
                <li key={idx} className="flex items-start gap-1.5">
                  <span className="text-emerald-400 select-none mt-0.5">&bull;</span>
                  <span className="leading-relaxed" dangerouslySetInnerHTML={{ __html: formatMarkdownBold(imp) }} />
                </li>
              ))}
            </ul>
          </div>
        )}
      </div>
    </div>
  );
};

function formatMarkdownBold(text: string): string {
  return text.replace(/\*\*(.*?)\*\*/g, '<strong class="font-bold text-white">$1</strong>');
}
