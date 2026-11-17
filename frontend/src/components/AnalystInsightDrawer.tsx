import React, { useState } from 'react';
import {
  NarrativeIntelligencePillars,
  StatutoryOfferDetails,
  VaultId
} from '../types/terminal';
import { getDetailedPillarsForVault, VaultPillarBundle } from '../services/analystPillarsData';
import {
  ChevronDown,
  ChevronUp,
  Sparkles,
  Building2,
  History,
  Compass,
  AlertTriangle,
  ExternalLink,
  BookOpen,
  FileText,
  TrendingUp,
  ShieldAlert,
  CheckCircle2,
  BarChart3,
  Layers,
  ArrowUpRight,
  Percent
} from 'lucide-react';

interface AnalystInsightDrawerProps {
  title?: string;
  narrative?: NarrativeIntelligencePillars;
  defaultExpanded?: boolean;
  vaultId?: VaultId | string;
  offer?: StatutoryOfferDetails;
  dealSymbol?: string;
  onCitationClick?: (page: number, context: string) => void;
}

export const AnalystInsightDrawer: React.FC<AnalystInsightDrawerProps> = ({
  title = "Institutional Valuation Narrative & Lifecycle Context",
  narrative,
  defaultExpanded = true,
  vaultId = 'red_flags',
  offer,
  dealSymbol,
  onCitationClick
}) => {
  const [isExpanded, setIsExpanded] = useState<boolean>(defaultExpanded);
  const [activeTab, setActiveTab] = useState<'sector' | 'lifecycle' | 'ic' | 'risk'>('sector');

  // Detect active deal symbol
  const activeSymbol =
    offer?.symbol ||
    dealSymbol ||
    (narrative?.sectorContext?.includes('green energy') ||
    narrative?.sectorContext?.includes('DISCOM') ||
    narrative?.sectorContext?.includes('NTPC')
      ? 'NTPCGREEN'
      : 'HCCB');

  // Fetch comprehensive rich 4-pillar bundle from data engine
  const bundle: VaultPillarBundle = getDetailedPillarsForVault(
    vaultId,
    activeSymbol,
    narrative
  );

  const isHCCB = activeSymbol === 'HCCB' || activeSymbol.includes('Coca-Cola');

  return (
    <div className="mt-3 rounded-xl border border-[#223044] bg-[#0A0F18] overflow-hidden transition-all text-xs font-sans shadow-xl">
      {/* Header Bar */}
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        className="w-full px-4 py-3 flex items-center justify-between bg-gradient-to-r from-[#101826] via-[#121D2F] to-[#101826] hover:from-[#141F33] hover:to-[#141F33] transition-colors cursor-pointer text-left border-b border-[#1C2A3E]"
      >
        <div className="flex items-center gap-2.5">
          <div className="p-1.5 rounded-lg bg-cyan-950/80 border border-cyan-800/60 text-cyan-400">
            <Sparkles className="w-4 h-4" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="font-mono font-bold text-slate-100 text-sm">{title}</span>
              <span className="text-[10px] font-mono px-2 py-0.5 rounded-full bg-cyan-950/90 border border-cyan-700/80 text-cyan-300 font-semibold uppercase tracking-wider">
                4-Pillar Model
              </span>
              <span className="text-[10px] font-mono px-2 py-0.5 rounded-full bg-indigo-950/70 border border-indigo-800/60 text-indigo-300 font-medium">
                {activeSymbol}
              </span>
            </div>
            <p className="text-[11px] text-slate-400 font-sans mt-0.5">
              Multi-dimensional evidence synthesis, lifecycle precedents, and statutory citations
            </p>
          </div>
        </div>
        <div className="flex items-center gap-2 text-slate-400">
          <span className="text-[11px] font-mono">{isExpanded ? 'Collapse' : 'Expand 4 Pillars'}</span>
          {isExpanded ? <ChevronUp className="w-4 h-4 text-cyan-400" /> : <ChevronDown className="w-4 h-4 text-slate-400" />}
        </div>
      </button>

      {/* Expanded Body */}
      {isExpanded && (
        <div className="p-4 space-y-4 bg-[#070B12]">
          {/* 4-Pillar Tab Pill Selectors */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 pb-3 border-b border-[#1A2638]">
            <button
              onClick={() => setActiveTab('sector')}
              className={`px-3 py-2 rounded-lg text-xs font-mono flex items-center justify-center gap-2 transition-all cursor-pointer ${
                activeTab === 'sector'
                  ? 'bg-gradient-to-r from-cyan-950 to-[#0F2236] border border-cyan-500/70 text-cyan-200 font-bold shadow-md shadow-cyan-950/50'
                  : 'bg-[#0E1522] border border-[#1E2B3E] text-slate-400 hover:text-slate-200 hover:bg-[#121B2A]'
              }`}
            >
              <Building2 className={`w-3.5 h-3.5 ${activeTab === 'sector' ? 'text-cyan-400' : 'text-slate-500'}`} />
              <span>1. Sector Context</span>
            </button>
            <button
              onClick={() => setActiveTab('lifecycle')}
              className={`px-3 py-2 rounded-lg text-xs font-mono flex items-center justify-center gap-2 transition-all cursor-pointer ${
                activeTab === 'lifecycle'
                  ? 'bg-gradient-to-r from-indigo-950 to-[#191F38] border border-indigo-500/70 text-indigo-200 font-bold shadow-md shadow-indigo-950/50'
                  : 'bg-[#0E1522] border border-[#1E2B3E] text-slate-400 hover:text-slate-200 hover:bg-[#121B2A]'
              }`}
            >
              <History className={`w-3.5 h-3.5 ${activeTab === 'lifecycle' ? 'text-indigo-400' : 'text-slate-500'}`} />
              <span>2. Lifecycle Precedents</span>
            </button>
            <button
              onClick={() => setActiveTab('ic')}
              className={`px-3 py-2 rounded-lg text-xs font-mono flex items-center justify-center gap-2 transition-all cursor-pointer ${
                activeTab === 'ic'
                  ? 'bg-gradient-to-r from-emerald-950 to-[#0F2D24] border border-emerald-500/70 text-emerald-200 font-bold shadow-md shadow-emerald-950/50'
                  : 'bg-[#0E1522] border border-[#1E2B3E] text-slate-400 hover:text-slate-200 hover:bg-[#121B2A]'
              }`}
            >
              <Compass className={`w-3.5 h-3.5 ${activeTab === 'ic' ? 'text-emerald-400' : 'text-slate-500'}`} />
              <span>3. IC Directives</span>
            </button>
            <button
              onClick={() => setActiveTab('risk')}
              className={`px-3 py-2 rounded-lg text-xs font-mono flex items-center justify-center gap-2 transition-all cursor-pointer ${
                activeTab === 'risk'
                  ? 'bg-gradient-to-r from-rose-950 to-[#2D121B] border border-rose-500/70 text-rose-200 font-bold shadow-md shadow-rose-950/50'
                  : 'bg-[#0E1522] border border-[#1E2B3E] text-slate-400 hover:text-slate-200 hover:bg-[#121B2A]'
              }`}
            >
              <AlertTriangle className={`w-3.5 h-3.5 ${activeTab === 'risk' ? 'text-rose-400' : 'text-slate-500'}`} />
              <span>4. Risk Radar</span>
            </button>
          </div>

          {/* Active Pillar Tab Panel */}
          <div className="space-y-4">
            {/* ========================================================= */}
            {/* TAB 1: SECTOR CONTEXT & MACRO ENVIRONMENT */}
            {/* ========================================================= */}
            {activeTab === 'sector' && (
              <div className="space-y-3.5">
                {/* Headline Banner */}
                <div className="p-3 rounded-lg bg-gradient-to-r from-cyan-950/40 via-[#0B1522] to-transparent border border-cyan-800/40 flex items-start gap-2.5">
                  <Building2 className="w-4 h-4 text-cyan-400 shrink-0 mt-0.5" />
                  <div>
                    <div className="text-[10px] font-mono uppercase text-cyan-400 tracking-wider font-bold">
                      Pillar 1: Industry Structure & Macro Environment
                    </div>
                    <div className="text-sm font-semibold text-slate-100 font-sans mt-0.5">
                      {bundle.detailedSector.headline}
                    </div>
                  </div>
                </div>

                {/* Visual Presentation: Sector Benchmark Dispersion & Metrics Bar */}
                <div className="p-3.5 rounded-lg bg-[#0C121D] border border-[#1A2638] space-y-3">
                  <div className="flex items-center justify-between text-xs font-mono text-slate-300 font-semibold">
                    <span className="flex items-center gap-1.5 text-cyan-300">
                      <BarChart3 className="w-3.5 h-3.5" />
                      Sector Valuation Multiple & Operational Dispersion
                    </span>
                    <span className="text-[10px] text-slate-500 font-normal">
                      Benchmark: Listed CMIE Peer Universe
                    </span>
                  </div>

                  {/* Dispersion Metric Grid */}
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-2.5">
                    {bundle.detailedSector.metrics.map((m, idx) => (
                      <div key={idx} className="p-2.5 rounded bg-[#070B12] border border-[#1C283B]">
                        <div className="text-[10px] font-mono text-slate-400">{m.label}</div>
                        <div className="text-sm font-bold font-mono text-slate-100 mt-1">
                          {m.value}
                        </div>
                        {m.benchmark && (
                          <div className="text-[10px] font-mono text-slate-500 mt-0.5">
                            Peer: <span className="text-slate-300">{m.benchmark}</span>
                          </div>
                        )}
                        {/* Visual progress bar */}
                        {m.barPct !== undefined && (
                          <div className="w-full bg-slate-800 h-1.5 rounded-full mt-2 overflow-hidden">
                            <div
                              className={`h-full rounded-full transition-all ${
                                m.status === 'CRITICAL'
                                  ? 'bg-rose-500'
                                  : m.status === 'WARNING'
                                  ? 'bg-amber-400'
                                  : 'bg-cyan-400'
                              }`}
                              style={{ width: `${Math.min(100, Math.max(10, m.barPct))}%` }}
                            />
                          </div>
                        )}
                      </div>
                    ))}
                  </div>

                  {/* Comparative Macro Meter */}
                  <div className="p-2.5 rounded bg-[#070B12] border border-[#172233] flex items-center justify-between">
                    <div className="text-[11px] font-mono text-slate-300 flex items-center gap-2">
                      <TrendingUp className="w-3.5 h-3.5 text-cyan-400" />
                      <span>{isHCCB ? 'Input Commodity Insulation (PET / Sugar):' : 'Tripartite Payment Security (SECI Escrow):'}</span>
                      <span className="font-bold text-emerald-400 font-mono">{isHCCB ? '88.0% Formula Protected' : '92.0% Sovereign Contracted'}</span>
                    </div>
                    <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-emerald-950/80 border border-emerald-800 text-emerald-300">
                      STRUCTURAL MOAT
                    </span>
                  </div>
                </div>

                {/* In-Depth Narration */}
                <div className="space-y-2 text-slate-300 font-sans leading-relaxed text-xs p-3 rounded-lg bg-[#0C121D] border border-[#1A2638]">
                  <p>{bundle.detailedSector.narration}</p>
                  {bundle.detailedSector.subParagraph && (
                    <p className="text-slate-400 pt-1 border-t border-[#162030]">
                      {bundle.detailedSector.subParagraph}
                    </p>
                  )}
                </div>

                {/* Evidence & Citations Shelf */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-2.5">
                  {bundle.detailedSector.citations.map((cite, idx) => (
                    <div key={idx} className="p-3 rounded-lg bg-[#0B1019] border border-[#192436] space-y-2">
                      <div className="flex items-center justify-between text-[10px] font-mono text-slate-400">
                        <span className="flex items-center gap-1.5 text-cyan-400 font-semibold">
                          <FileText className="w-3 h-3" />
                          {cite.sourceType === 'STATUTORY_FILING' ? 'Statutory Prospectus Evidence' : 'Authoritative Reference'}
                        </span>
                        {cite.drhpPage && (
                          <button
                            type="button"
                            onClick={() => onCitationClick?.(cite.drhpPage!, 'sector.evidence')}
                            className="text-cyan-400 hover:text-cyan-300 font-bold flex items-center gap-1 cursor-pointer bg-cyan-950/60 px-1.5 py-0.5 rounded border border-cyan-800/40"
                          >
                            <span>p. {cite.drhpPage}</span>
                            <ExternalLink className="w-2.5 h-2.5" />
                          </button>
                        )}
                      </div>
                      <div className="text-[11px] font-mono font-medium text-slate-300">
                        {cite.citationSource}
                      </div>
                      <p className="text-[11px] text-slate-400 italic bg-[#070B12] p-2 rounded border border-[#151F2F]">
                        "{cite.quote}"
                      </p>
                      {cite.verifiedMetricOrCutoff && (
                        <div className="text-[10px] font-mono text-emerald-400 font-semibold">
                          Verified: {cite.verifiedMetricOrCutoff}
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* ========================================================= */}
            {/* TAB 2: LIFECYCLE PRECEDENTS & STAGE */}
            {/* ========================================================= */}
            {activeTab === 'lifecycle' && (
              <div className="space-y-3.5">
                {/* Headline Banner */}
                <div className="p-3 rounded-lg bg-gradient-to-r from-indigo-950/40 via-[#0E1528] to-transparent border border-indigo-800/40 flex items-start gap-2.5">
                  <History className="w-4 h-4 text-indigo-400 shrink-0 mt-0.5" />
                  <div>
                    <div className="text-[10px] font-mono uppercase text-indigo-400 tracking-wider font-bold">
                      Pillar 2: Dickinson Life-Cycle Stage & Historical Parallels
                    </div>
                    <div className="text-sm font-semibold text-slate-100 font-sans mt-0.5">
                      {bundle.detailedLifecycle.headline}
                    </div>
                  </div>
                </div>

                {/* Visual Presentation: SVG Lifecycle Compounding Curve */}
                <div className="p-3.5 rounded-lg bg-[#0C121D] border border-[#1A2638] space-y-3">
                  <div className="flex items-center justify-between text-xs font-mono text-slate-300 font-semibold">
                    <span className="flex items-center gap-1.5 text-indigo-300">
                      <Layers className="w-3.5 h-3.5" />
                      {isHCCB
                        ? 'Historical Peer Trajectory: Varun Beverages (VBL) 7Y Compounding Curve'
                        : 'Renewable IPP Life-Cycle Trajectory: Adani Green (FY18-FY24)'}
                    </span>
                    <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-indigo-950 border border-indigo-800 text-indigo-300 font-bold">
                      {isHCCB ? 'STAGE: MATURE (+, -, -)' : 'STAGE: GROWTH (+, -, +)'}
                    </span>
                  </div>

                  {/* High-Craft SVG Curve */}
                  <div className="w-full bg-[#070B12] rounded-lg border border-[#182335] p-3 flex flex-col items-center">
                    <svg viewBox="0 0 600 120" className="w-full h-24 overflow-visible">
                      <defs>
                        <linearGradient id="curveGradient" x1="0%" y1="0%" x2="100%" y2="0%">
                          <stop offset="0%" stopColor="#818CF8" stopOpacity="0.4" />
                          <stop offset="30%" stopColor="#6366F1" stopOpacity="0.8" />
                          <stop offset="100%" stopColor="#10B981" stopOpacity="1" />
                        </linearGradient>
                      </defs>
                      {/* Grid Lines */}
                      <line x1="50" y1="20" x2="570" y2="20" stroke="#1E293B" strokeDasharray="3 3" />
                      <line x1="50" y1="60" x2="570" y2="60" stroke="#1E293B" strokeDasharray="3 3" />
                      <line x1="50" y1="100" x2="570" y2="100" stroke="#1E293B" />

                      {/* Trajectory Path */}
                      {isHCCB ? (
                        // VBL: Listing (₹445) -> 14% de-rating -> compounding 8.4x
                        <path
                          d="M 60 70 Q 130 95, 200 80 T 360 45 T 560 15"
                          fill="none"
                          stroke="url(#curveGradient)"
                          strokeWidth="3.5"
                          strokeLinecap="round"
                        />
                      ) : (
                        // NTPC/Adani Green: Construction dip -> COD cash generation surge
                        <path
                          d="M 60 85 Q 150 90, 240 65 T 420 35 T 560 20"
                          fill="none"
                          stroke="url(#curveGradient)"
                          strokeWidth="3.5"
                          strokeLinecap="round"
                        />
                      )}

                      {/* Milestone Points */}
                      <circle cx="60" cy={isHCCB ? "70" : "85"} r="4" fill="#818CF8" />
                      <text x="60" y={isHCCB ? "60" : "75"} fill="#94A3B8" fontSize="9" textAnchor="middle" fontFamily="monospace">
                        IPO (T0)
                      </text>

                      <circle cx="160" cy={isHCCB ? "90" : "80"} r="4" fill="#F43F5E" />
                      <text x="160" y={isHCCB ? "108" : "98"} fill="#F43F5E" fontSize="9" textAnchor="middle" fontFamily="monospace">
                        {isHCCB ? 'De-rating (-14%)' : 'Capex Absorption'}
                      </text>

                      <circle cx="360" cy={isHCCB ? "45" : "45"} r="4" fill="#6366F1" />
                      <text x="360" y={isHCCB ? "35" : "35"} fill="#818CF8" fontSize="9" textAnchor="middle" fontFamily="monospace">
                        {isHCCB ? 'Scale Dilution (T+3Y)' : 'COD Onstreaming'}
                      </text>

                      <circle cx="560" cy={isHCCB ? "15" : "20"} r="5" fill="#10B981" />
                      <text x="560" y={isHCCB ? "10" : "15"} fill="#10B981" fontSize="10" textAnchor="middle" fontWeight="bold" fontFamily="monospace">
                        {isHCCB ? '8.4x Compounding' : 'Deleveraged Scale'}
                      </text>
                    </svg>

                    {/* Dickinson Cash Flow Sign Vector Strip */}
                    <div className="flex flex-wrap items-center justify-center gap-3 mt-2 text-xs font-mono">
                      <div className="flex items-center gap-1.5 px-2 py-1 rounded bg-[#0A101C] border border-[#213047]">
                        <span className="text-slate-400">Operating CFO:</span>
                        <span className="font-bold text-emerald-400">POSITIVE (+)</span>
                      </div>
                      <div className="flex items-center gap-1.5 px-2 py-1 rounded bg-[#0A101C] border border-[#213047]">
                        <span className="text-slate-400">Investing Capex:</span>
                        <span className="font-bold text-rose-400">NEGATIVE (-)</span>
                      </div>
                      <div className="flex items-center gap-1.5 px-2 py-1 rounded bg-[#0A101C] border border-[#213047]">
                        <span className="text-slate-400">Financing Flow:</span>
                        <span className={`font-bold ${isHCCB ? 'text-rose-400' : 'text-emerald-400'}`}>
                          {isHCCB ? 'NEGATIVE (-)' : 'POSITIVE (+)'}
                        </span>
                      </div>
                    </div>
                  </div>
                </div>

                {/* In-Depth Narration */}
                <div className="space-y-2 text-slate-300 font-sans leading-relaxed text-xs p-3 rounded-lg bg-[#0C121D] border border-[#1A2638]">
                  <p>{bundle.detailedLifecycle.narration}</p>
                  {bundle.detailedLifecycle.subParagraph && (
                    <p className="text-slate-400 pt-1 border-t border-[#162030]">
                      {bundle.detailedLifecycle.subParagraph}
                    </p>
                  )}
                </div>

                {/* Evidence & Citations Shelf */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-2.5">
                  {bundle.detailedLifecycle.citations.map((cite, idx) => (
                    <div key={idx} className="p-3 rounded-lg bg-[#0B1019] border border-[#192436] space-y-2">
                      <div className="flex items-center justify-between text-[10px] font-mono text-slate-400">
                        <span className="flex items-center gap-1.5 text-indigo-400 font-semibold">
                          <BookOpen className="w-3 h-3" />
                          {cite.sourceType === 'STATUTORY_FILING' ? 'Statutory Cash Flow Filing' : 'Seminal Lifecycle Standard'}
                        </span>
                        {cite.drhpPage && (
                          <button
                            type="button"
                            onClick={() => onCitationClick?.(cite.drhpPage!, 'lifecycle.evidence')}
                            className="text-cyan-400 hover:text-cyan-300 font-bold flex items-center gap-1 cursor-pointer bg-cyan-950/60 px-1.5 py-0.5 rounded border border-cyan-800/40"
                          >
                            <span>p. {cite.drhpPage}</span>
                            <ExternalLink className="w-2.5 h-2.5" />
                          </button>
                        )}
                      </div>
                      <div className="text-[11px] font-mono font-medium text-slate-300">
                        {cite.citationSource}
                      </div>
                      <p className="text-[11px] text-slate-400 italic bg-[#070B12] p-2 rounded border border-[#151F2F]">
                        "{cite.quote}"
                      </p>
                      {cite.verifiedMetricOrCutoff && (
                        <div className="text-[10px] font-mono text-emerald-400 font-semibold">
                          Verified: {cite.verifiedMetricOrCutoff}
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* ========================================================= */}
            {/* TAB 3: IC DIRECTIVES & SYNDICATE MANDATE */}
            {/* ========================================================= */}
            {activeTab === 'ic' && (
              <div className="space-y-3.5">
                {/* Headline Banner */}
                <div className="p-3 rounded-lg bg-gradient-to-r from-emerald-950/40 via-[#0A1F18] to-transparent border border-emerald-800/40 flex items-start gap-2.5">
                  <Compass className="w-4 h-4 text-emerald-400 shrink-0 mt-0.5" />
                  <div>
                    <div className="text-[10px] font-mono uppercase text-emerald-400 tracking-wider font-bold">
                      Pillar 3: Syndicate Underwriting & Investment Committee Mandate
                    </div>
                    <div className="text-sm font-semibold text-slate-100 font-sans mt-0.5">
                      {bundle.detailedIC.headline}
                    </div>
                  </div>
                </div>

                {/* Visual Presentation: Bid Band Allocation & Hurdle Matrix */}
                <div className="p-3.5 rounded-lg bg-[#0C121D] border border-[#1A2638] space-y-3">
                  <div className="flex items-center justify-between text-xs font-mono text-slate-300 font-semibold">
                    <span className="flex items-center gap-1.5 text-emerald-300">
                      <Percent className="w-3.5 h-3.5" />
                      Valuation Band & Allocation Sweet-Spot Visualizer
                    </span>
                    <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-emerald-950 border border-emerald-800 text-emerald-300 font-bold">
                      IC STATUS: CLEARED CONDITIONAL
                    </span>
                  </div>

                  {/* Metric Cards */}
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-2.5">
                    {bundle.detailedIC.metrics.map((m, idx) => (
                      <div key={idx} className="p-2.5 rounded bg-[#070B12] border border-[#1C283B]">
                        <div className="text-[10px] font-mono text-slate-400">{m.label}</div>
                        <div className="text-sm font-bold font-mono text-slate-100 mt-1">
                          {m.value}
                        </div>
                        {m.benchmark && (
                          <div className="text-[10px] font-mono text-slate-500 mt-0.5">
                            Target: <span className="text-slate-300">{m.benchmark}</span>
                          </div>
                        )}
                        {m.barPct !== undefined && (
                          <div className="w-full bg-slate-800 h-1.5 rounded-full mt-2 overflow-hidden">
                            <div
                              className="h-full bg-emerald-400 rounded-full"
                              style={{ width: `${m.barPct}%` }}
                            />
                          </div>
                        )}
                      </div>
                    ))}
                  </div>

                  {/* High-Contrast Action Directive Box */}
                  <div className="p-3 rounded-lg bg-gradient-to-r from-emerald-950/70 to-[#0A1A14] border border-emerald-700/60 flex items-start gap-2.5">
                    <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0 mt-0.5" />
                    <div className="text-xs">
                      <div className="font-mono font-bold text-emerald-300 uppercase tracking-wide text-[11px]">
                        MANDATORY UNDERWRITING DIRECTIVE
                      </div>
                      <p className="text-slate-200 mt-1 font-sans leading-relaxed">
                        {isHCCB
                          ? "Condition bid approval upon capping parent concentrate price escalations. Allocate 60% of syndicate book to Long-Only Mutual Funds and Sovereign Wealth Funds with clawback insulation."
                          : "Enforce SEBI Regulation 7 GCP cap (≤ 25.0%). Restrict bids to lower price band (₹102–₹104) to guard against post-lockin selling pressure."}
                      </p>
                    </div>
                  </div>
                </div>

                {/* In-Depth Narration */}
                <div className="space-y-2 text-slate-300 font-sans leading-relaxed text-xs p-3 rounded-lg bg-[#0C121D] border border-[#1A2638]">
                  <p>{bundle.detailedIC.narration}</p>
                  {bundle.detailedIC.subParagraph && (
                    <p className="text-slate-400 pt-1 border-t border-[#162030]">
                      {bundle.detailedIC.subParagraph}
                    </p>
                  )}
                </div>

                {/* Evidence & Citations Shelf */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-2.5">
                  {bundle.detailedIC.citations.map((cite, idx) => (
                    <div key={idx} className="p-3 rounded-lg bg-[#0B1019] border border-[#192436] space-y-2">
                      <div className="flex items-center justify-between text-[10px] font-mono text-slate-400">
                        <span className="flex items-center gap-1.5 text-emerald-400 font-semibold">
                          <Compass className="w-3 h-3" />
                          Regulatory Standard / Prospectus Risk
                        </span>
                        {cite.drhpPage && (
                          <button
                            type="button"
                            onClick={() => onCitationClick?.(cite.drhpPage!, 'ic.evidence')}
                            className="text-cyan-400 hover:text-cyan-300 font-bold flex items-center gap-1 cursor-pointer bg-cyan-950/60 px-1.5 py-0.5 rounded border border-cyan-800/40"
                          >
                            <span>p. {cite.drhpPage}</span>
                            <ExternalLink className="w-2.5 h-2.5" />
                          </button>
                        )}
                      </div>
                      <div className="text-[11px] font-mono font-medium text-slate-300">
                        {cite.citationSource}
                      </div>
                      <p className="text-[11px] text-slate-400 italic bg-[#070B12] p-2 rounded border border-[#151F2F]">
                        "{cite.quote}"
                      </p>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* ========================================================= */}
            {/* TAB 4: DOWNSIDE RISK RADAR */}
            {/* ========================================================= */}
            {activeTab === 'risk' && (
              <div className="space-y-3.5">
                {/* Headline Banner */}
                <div className="p-3 rounded-lg bg-gradient-to-r from-rose-950/40 via-[#1C0D14] to-transparent border border-rose-800/40 flex items-start gap-2.5">
                  <AlertTriangle className="w-4 h-4 text-rose-400 shrink-0 mt-0.5" />
                  <div>
                    <div className="text-[10px] font-mono uppercase text-rose-400 tracking-wider font-bold">
                      Pillar 4: Downside Vulnerability & Overhang Risk Radar
                    </div>
                    <div className="text-sm font-semibold text-slate-100 font-sans mt-0.5">
                      {bundle.detailedRisk.headline}
                    </div>
                  </div>
                </div>

                {/* Visual Presentation: 5-Axis Downside Risk Exposure Gauges */}
                <div className="p-3.5 rounded-lg bg-[#0C121D] border border-[#1A2638] space-y-3">
                  <div className="flex items-center justify-between text-xs font-mono text-slate-300 font-semibold">
                    <span className="flex items-center gap-1.5 text-rose-300">
                      <ShieldAlert className="w-3.5 h-3.5" />
                      5-Dimension Downside Risk Exposure Visualizer
                    </span>
                    <span className="text-[10px] text-slate-500 font-normal">
                      Scored 0 (Safe) to 100 (Critical)
                    </span>
                  </div>

                  {/* Risk Bars */}
                  <div className="space-y-2.5">
                    {bundle.detailedRisk.riskAxes?.map((axis, idx) => (
                      <div key={idx} className="p-2.5 rounded bg-[#070B12] border border-[#192437] space-y-1.5">
                        <div className="flex items-center justify-between text-xs font-mono">
                          <span className="font-semibold text-slate-200">{axis.name}</span>
                          <span
                            className={`px-1.5 py-0.5 rounded text-[10px] font-bold ${
                              axis.status === 'CRITICAL'
                                ? 'bg-rose-950 text-rose-300 border border-rose-700'
                                : axis.status === 'WARNING'
                                ? 'bg-amber-950 text-amber-300 border border-amber-700'
                                : 'bg-emerald-950 text-emerald-300 border border-emerald-700'
                            }`}
                          >
                            {axis.status} ({axis.score}/100)
                          </span>
                        </div>

                        {/* Progress Meter */}
                        <div className="w-full bg-slate-800 h-2 rounded-full overflow-hidden flex">
                          <div
                            className={`h-full rounded-full transition-all ${
                              axis.status === 'CRITICAL'
                                ? 'bg-rose-500'
                                : axis.status === 'WARNING'
                                ? 'bg-amber-400'
                                : 'bg-emerald-400'
                            }`}
                            style={{ width: `${axis.score}%` }}
                          />
                        </div>

                        {/* Snippet and Mitigation */}
                        <div className="flex items-center justify-between text-[10px] font-mono text-slate-400 pt-0.5">
                          <span className="text-slate-300">{axis.metricSnippet}</span>
                          <span className="text-cyan-400 font-sans">
                            Mitigation: <span className="italic">{axis.mitigation}</span>
                          </span>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>

                {/* In-Depth Narration */}
                <div className="space-y-2 text-slate-300 font-sans leading-relaxed text-xs p-3 rounded-lg bg-[#0C121D] border border-[#1A2638]">
                  <p>{bundle.detailedRisk.narration}</p>
                  {bundle.detailedRisk.subParagraph && (
                    <p className="text-slate-400 pt-1 border-t border-[#162030]">
                      {bundle.detailedRisk.subParagraph}
                    </p>
                  )}
                </div>

                {/* Evidence & Citations Shelf */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-2.5">
                  {bundle.detailedRisk.citations.map((cite, idx) => (
                    <div key={idx} className="p-3 rounded-lg bg-[#0B1019] border border-[#192436] space-y-2">
                      <div className="flex items-center justify-between text-[10px] font-mono text-slate-400">
                        <span className="flex items-center gap-1.5 text-rose-400 font-semibold">
                          <AlertTriangle className="w-3 h-3" />
                          Prospectus Risk Factor Disclosure
                        </span>
                        {cite.drhpPage && (
                          <button
                            type="button"
                            onClick={() => onCitationClick?.(cite.drhpPage!, 'risk.evidence')}
                            className="text-cyan-400 hover:text-cyan-300 font-bold flex items-center gap-1 cursor-pointer bg-cyan-950/60 px-1.5 py-0.5 rounded border border-cyan-800/40"
                          >
                            <span>p. {cite.drhpPage}</span>
                            <ExternalLink className="w-2.5 h-2.5" />
                          </button>
                        )}
                      </div>
                      <div className="text-[11px] font-mono font-medium text-slate-300">
                        {cite.citationSource}
                      </div>
                      <p className="text-[11px] text-slate-400 italic bg-[#070B12] p-2 rounded border border-[#151F2F]">
                        "{cite.quote}"
                      </p>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};
