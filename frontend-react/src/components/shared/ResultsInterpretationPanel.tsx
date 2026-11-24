import React, { useState } from 'react';
import { Target, Lightbulb, Copy, Check, Sparkles, ExternalLink, ShieldCheck } from 'lucide-react';

export interface ResultsInterpretationPanelProps {
  title?: string;
  subtitle?: string;
  insights?: string[];
  actions?: string[];
  methodologyCitation?: string;
  className?: string;
}

export const ResultsInterpretationPanel: React.FC<ResultsInterpretationPanelProps> = ({
  title = 'Results Interpretation & Call to Action',
  subtitle = 'Automated empirical deductions and actionable corporate finance directives derived from panel econometric models.',
  insights = [],
  actions = [],
  methodologyCitation,
  className = '',
}) => {
  const [copied, setCopied] = useState<boolean>(false);

  if ((!insights || insights.length === 0) && (!actions || actions.length === 0)) {
    return null;
  }

  const handleCopy = () => {
    let md = `### ${title}\n\n`;
    if (insights && insights.length > 0) {
      md += `#### Key Findings:\n`;
      insights.forEach((item) => {
        md += `- ${item.replace(/<[^>]*>?/gm, '')}\n`;
      });
      md += `\n`;
    }
    if (actions && actions.length > 0) {
      md += `#### Call to Action:\n`;
      actions.forEach((item) => {
        md += `- 🎯 ${item.replace(/<[^>]*>?/gm, '')}\n`;
      });
    }

    navigator.clipboard.writeText(md).then(() => {
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    });
  };

  return (
    <div
      className={`rounded-2xl border border-cyan-500/20 bg-[#0a0f1d] p-6 shadow-xl transition-all hover:border-cyan-500/35 ${className}`}
    >
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-white/10 pb-4 mb-5">
        <div>
          <div className="flex items-center gap-2">
            <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-cyan-500/10 text-cyan-400 border border-cyan-500/20">
              <Sparkles className="h-4 w-4" />
            </div>
            <h3 className="text-lg font-bold text-white tracking-tight flex items-center gap-2">
              {title}
            </h3>
          </div>
          {subtitle && (
            <p className="text-xs text-slate-400 mt-1 pl-9">
              {subtitle}
            </p>
          )}
        </div>

        <div className="flex items-center gap-2 pl-9 sm:pl-0">
          {methodologyCitation && (
            <span className="text-[11px] font-mono text-cyan-300 bg-cyan-950/40 border border-cyan-500/30 px-2.5 py-1 rounded-full flex items-center gap-1">
              <ShieldCheck className="w-3 h-3 text-cyan-400" />
              {methodologyCitation}
            </span>
          )}
          <button
            onClick={handleCopy}
            title="Copy interpretation as Markdown"
            className="px-2.5 py-1 rounded-lg bg-white/5 hover:bg-white/10 border border-white/10 text-slate-300 hover:text-white text-xs font-medium flex items-center gap-1.5 transition-all cursor-pointer"
          >
            {copied ? (
              <>
                <Check className="w-3.5 h-3.5 text-emerald-400" />
                <span className="text-emerald-400">Copied</span>
              </>
            ) : (
              <>
                <Copy className="w-3.5 h-3.5 text-slate-400" />
                <span>Export MD</span>
              </>
            )}
          </button>
        </div>
      </div>

      <div className="space-y-6">
        {/* Section 1: Key Findings */}
        {insights && insights.length > 0 && (
          <div className="space-y-3">
            <div className="flex items-center gap-2">
              <div className="flex h-5 w-5 items-center justify-center rounded bg-indigo-500/10 text-indigo-400">
                <Lightbulb className="h-3 w-3" />
              </div>
              <h4 className="text-xs font-bold uppercase tracking-wider text-slate-300">
                Key Findings:
              </h4>
            </div>
            <ul className="space-y-2.5 pl-2">
              {insights.map((item, idx) => (
                <li key={idx} className="flex items-start gap-2.5 text-xs text-slate-300 leading-relaxed">
                  <span className="text-cyan-400 font-bold select-none mt-0.5">•</span>
                  <span
                    dangerouslySetInnerHTML={{
                      __html: formatMarkdownBoldAndNumbers(item),
                    }}
                  />
                </li>
              ))}
            </ul>
          </div>
        )}

        {/* Section 2: Call to Action */}
        {actions && actions.length > 0 && (
          <div className="space-y-3 pt-3 border-t border-white/5">
            <div className="flex items-center gap-2">
              <div className="flex h-5 w-5 items-center justify-center rounded bg-emerald-500/10 text-emerald-400">
                <Target className="h-3 w-3" />
              </div>
              <h4 className="text-xs font-bold uppercase tracking-wider text-slate-300">
                Call to Action:
              </h4>
            </div>
            <ul className="space-y-2.5 pl-2">
              {actions.map((act, idx) => (
                <li key={idx} className="flex items-start gap-2.5 text-xs text-slate-200 leading-relaxed bg-white/[0.02] border border-white/5 rounded-xl p-3 hover:border-emerald-500/20 transition-all">
                  <span className="text-base select-none leading-none mt-0.5">🎯</span>
                  <span
                    dangerouslySetInnerHTML={{
                      __html: formatMarkdownBoldAndNumbers(act),
                    }}
                  />
                </li>
              ))}
            </ul>
          </div>
        )}
      </div>
    </div>
  );
};

function formatMarkdownBoldAndNumbers(text: string): string {
  if (!text) return '';
  // Convert markdown **bold** to strong styling
  let formatted = text.replace(
    /\*\*(.*?)\*\*/g,
    '<strong class="font-bold text-white tracking-wide">$1</strong>'
  );
  // Highlight hazard ratios e.g. HR=0.728
  formatted = formatted.replace(
    /\(HR=([0-9.]+)\)/g,
    '(<span class="font-mono text-cyan-300 font-semibold">HR=$1</span>)'
  );
  return formatted;
}
