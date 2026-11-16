import React, { useState } from 'react';
import { NarrativeIntelligencePillars } from '../types/terminal';
import { ChevronDown, ChevronUp, Sparkles, Building2, History, Compass, AlertTriangle } from 'lucide-react';

interface AnalystInsightDrawerProps {
  title?: string;
  narrative?: NarrativeIntelligencePillars;
  defaultExpanded?: boolean;
}

export const AnalystInsightDrawer: React.FC<AnalystInsightDrawerProps> = ({
  title = "Institutional Valuation Narrative & Lifecycle Context",
  narrative,
  defaultExpanded = false
}) => {
  const [isExpanded, setIsExpanded] = useState<boolean>(defaultExpanded);
  const [activeTab, setActiveTab] = useState<'sector' | 'lifecycle' | 'ic' | 'risk'>('sector');

  // Ground-truth fallback narrative when not specifically overridden
  const n: NarrativeIntelligencePillars = narrative || {
    sectorContext: "Indian FMCG & Beverage sector trades at 48.5x FY26E median P/E. High-ROCE distribution moats defend pricing power against input commodity shocks (PET resin, sugar) with 68% gross margin insulation.",
    lifecyclePrecedents: "Varun Beverages (VBL) listed at ₹445 (FY16), de-rated 14% post-listing due to initial leverage overhang before compounding 8.4x over 7 years following territory consolidation. Similar cash-cow profile at mature stage.",
    icDirectives: "Avoid full allocation at Upper Price Band without 15% discount. Require minimum 22% RoCE persistence guarantee. Recommend bidding in QIB bracket with syndicate clawback defense.",
    riskRadar: "Top customer concentration risk in tier-1 modern trade (31% of volume). Section 56(2)(x) FMV scrutiny on historical unlisted share transfers. Lock-in expiry at Day-180 exposes 50% non-promoter supply."
  };

  return (
    <div className="mt-3 rounded-lg border border-[#223044] bg-[#0C121D] overflow-hidden transition-all text-xs font-sans">
      {/* Header Bar */}
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        className="w-full px-3.5 py-2.5 flex items-center justify-between bg-[#101826] hover:bg-[#152033] transition-colors cursor-pointer text-left"
      >
        <div className="flex items-center gap-2">
          <Sparkles className="w-3.5 h-3.5 text-cyan-400" />
          <span className="font-mono font-semibold text-slate-200">{title}</span>
          <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-cyan-950/80 border border-cyan-800 text-cyan-300">
            4-Pillar Model
          </span>
        </div>
        <div className="flex items-center gap-2 text-slate-400">
          <span className="text-[11px] font-mono">{isExpanded ? 'Collapse' : 'Expand Insights'}</span>
          {isExpanded ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
        </div>
      </button>

      {/* Expanded Body */}
      {isExpanded && (
        <div className="p-3.5 border-t border-[#1F2C40] space-y-3">
          {/* Tab Pill Selectors */}
          <div className="flex flex-wrap gap-1.5 pb-2 border-b border-[#1A2638]">
            <button
              onClick={() => setActiveTab('sector')}
              className={`px-2.5 py-1 rounded text-[11px] font-mono flex items-center gap-1.5 transition-colors cursor-pointer ${
                activeTab === 'sector'
                  ? 'bg-cyan-500/20 border border-cyan-500/50 text-cyan-300 font-semibold'
                  : 'bg-[#121B29] border border-[#202E42] text-slate-400 hover:text-slate-200'
              }`}
            >
              <Building2 className="w-3 h-3 text-cyan-400" />
              <span>1. Sector Context</span>
            </button>
            <button
              onClick={() => setActiveTab('lifecycle')}
              className={`px-2.5 py-1 rounded text-[11px] font-mono flex items-center gap-1.5 transition-colors cursor-pointer ${
                activeTab === 'lifecycle'
                  ? 'bg-indigo-500/20 border border-indigo-500/50 text-indigo-300 font-semibold'
                  : 'bg-[#121B29] border border-[#202E42] text-slate-400 hover:text-slate-200'
              }`}
            >
              <History className="w-3 h-3 text-indigo-400" />
              <span>2. Lifecycle Precedents</span>
            </button>
            <button
              onClick={() => setActiveTab('ic')}
              className={`px-2.5 py-1 rounded text-[11px] font-mono flex items-center gap-1.5 transition-colors cursor-pointer ${
                activeTab === 'ic'
                  ? 'bg-emerald-500/20 border border-emerald-500/50 text-emerald-300 font-semibold'
                  : 'bg-[#121B29] border border-[#202E42] text-slate-400 hover:text-slate-200'
              }`}
            >
              <Compass className="w-3 h-3 text-emerald-400" />
              <span>3. IC Directives</span>
            </button>
            <button
              onClick={() => setActiveTab('risk')}
              className={`px-2.5 py-1 rounded text-[11px] font-mono flex items-center gap-1.5 transition-colors cursor-pointer ${
                activeTab === 'risk'
                  ? 'bg-rose-500/20 border border-rose-500/50 text-rose-300 font-semibold'
                  : 'bg-[#121B29] border border-[#202E42] text-slate-400 hover:text-slate-200'
              }`}
            >
              <AlertTriangle className="w-3 h-3 text-rose-400" />
              <span>4. Risk Radar</span>
            </button>
          </div>

          {/* Active Tab Panel */}
          <div className="bg-[#080D15] rounded border border-[#1A2638] p-3 text-slate-300 leading-relaxed font-sans">
            {activeTab === 'sector' && (
              <div>
                <div className="text-[10px] font-mono uppercase text-cyan-400 tracking-wider mb-1 font-semibold flex items-center gap-1.5">
                  <Building2 className="w-3 h-3" /> Industry & Macro Environment
                </div>
                <p className="text-slate-200">{n.sectorContext}</p>
              </div>
            )}
            {activeTab === 'lifecycle' && (
              <div>
                <div className="text-[10px] font-mono uppercase text-indigo-400 tracking-wider mb-1 font-semibold flex items-center gap-1.5">
                  <History className="w-3 h-3" /> Dickinson Stage & Historical Parallels
                </div>
                <p className="text-slate-200">{n.lifecyclePrecedents}</p>
              </div>
            )}
            {activeTab === 'ic' && (
              <div>
                <div className="text-[10px] font-mono uppercase text-emerald-400 tracking-wider mb-1 font-semibold flex items-center gap-1.5">
                  <Compass className="w-3 h-3" /> Syndicate & Investment Committee Mandate
                </div>
                <p className="text-slate-200">{n.icDirectives || n.prescriptiveMandate}</p>
              </div>
            )}
            {activeTab === 'risk' && (
              <div>
                <div className="text-[10px] font-mono uppercase text-rose-400 tracking-wider mb-1 font-semibold flex items-center gap-1.5">
                  <AlertTriangle className="w-3 h-3" /> Downside Triggers & Overhang Exposure
                </div>
                <p className="text-slate-200">{n.riskRadar}</p>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};
