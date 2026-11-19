import React, { useState, useEffect } from 'react';
import {
  BookOpen,
  Layers,
  ShieldAlert,
  ChevronRight,
  TrendingDown,
  AlertTriangle,
  FileText,
  Search,
  ExternalLink,
  ShieldCheck,
  CheckCircle2,
  RefreshCw,
  Zap
} from 'lucide-react';
import {
  fetchStatutorySections,
  StatutorySectionSummary
} from '../../../services/dataService';
import { ContagionShockModal } from './ContagionShockModal';

interface StatutorySectionSummaryGridProps {
  onSelectSection: (sectionId: string) => void;
  onOpenPdfPage?: (page: number, quote: string) => void;
}

export const StatutorySectionSummaryGrid: React.FC<StatutorySectionSummaryGridProps> = ({
  onSelectSection,
  onOpenPdfPage
}) => {
  const [sections, setSections] = useState<StatutorySectionSummary[]>([]);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [searchFilter, setSearchFilter] = useState<string>('');
  const [isContagionOpen, setIsContagionOpen] = useState<boolean>(false);

  useEffect(() => {
    setIsLoading(true);
    fetchStatutorySections()
      .then(res => setSections(res.sections || []))
      .catch(err => console.error('Failed to load statutory sections:', err))
      .finally(() => setIsLoading(false));
  }, []);

  const totalExposure = sections.reduce((acc, s) => acc + (s.totalFinancialExposureCr || 0), 0);
  const totalFacts = sections.reduce((acc, s) => acc + (s.totalFacts || 0), 0);
  const criticalCount = sections.reduce((acc, s) => acc + (s.severities?.CRITICAL_RISK || 0), 0);

  const filteredSections = searchFilter
    ? sections.filter(
        s =>
          s.title.toLowerCase().includes(searchFilter.toLowerCase()) ||
          s.description.toLowerCase().includes(searchFilter.toLowerCase()) ||
          s.keyEntities.some(e => e.toLowerCase().includes(searchFilter.toLowerCase()))
      )
    : sections;

  return (
    <div className="space-y-5 animate-fade-in text-slate-100">
      {/* Executive Statutory Metrics Ribbon */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="p-4 rounded-xl bg-slate-900/80 border border-slate-800 shadow-md">
          <div className="text-[10px] text-slate-400 font-mono uppercase tracking-wider flex items-center gap-1.5">
            <BookOpen className="w-3.5 h-3.5 text-blue-400" />
            Statutory SEBI Chapters
          </div>
          <div className="text-xl font-bold text-slate-100 mt-1">
            8 Sections <span className="text-xs text-slate-400 font-normal">/ 24 Chapters</span>
          </div>
          <p className="text-[10px] text-slate-500 mt-0.5 font-mono">SEBI ICDR Schedule VI Compliant</p>
        </div>

        <div className="p-4 rounded-xl bg-slate-900/80 border border-slate-800 shadow-md">
          <div className="text-[10px] text-slate-400 font-mono uppercase tracking-wider flex items-center gap-1.5">
            <FileText className="w-3.5 h-3.5 text-emerald-400" />
            Verbatim Fact Extracts
          </div>
          <div className="text-xl font-bold text-emerald-400 mt-1">
            {totalFacts} Disclosures
          </div>
          <p className="text-[10px] text-slate-500 mt-0.5 font-mono">W3C PROV-O Page Coordinates</p>
        </div>

        <div className="p-4 rounded-xl bg-slate-900/80 border border-slate-800 shadow-md">
          <div className="text-[10px] text-slate-400 font-mono uppercase tracking-wider flex items-center gap-1.5">
            <TrendingDown className="w-3.5 h-3.5 text-rose-400" />
            Quantified Risk Exposure
          </div>
          <div className="text-xl font-bold text-rose-400 mt-1">
            ₹{totalExposure.toLocaleString(undefined, { maximumFractionDigits: 2 })} Cr
          </div>
          <p className="text-[10px] text-slate-500 mt-0.5 font-mono">Across Litigation & Royalty Contracts</p>
        </div>

        <div className="p-4 rounded-xl bg-slate-900/80 border border-slate-800 shadow-md">
          <div className="text-[10px] text-slate-400 font-mono uppercase tracking-wider flex items-center gap-1.5">
            <ShieldAlert className="w-3.5 h-3.5 text-amber-400" />
            Critical Severity Findings
          </div>
          <div className="text-xl font-bold text-amber-400 mt-1">
            {criticalCount} Critical Risks
          </div>
          <p className="text-[10px] text-slate-500 mt-0.5 font-mono">Contagion to Public Shareholders</p>
        </div>
      </div>

      {/* Filter / Search Bar */}
      <div className="flex flex-col md:flex-row items-center justify-between gap-3 p-3.5 rounded-xl bg-slate-900/60 border border-slate-800">
        <div className="flex items-center gap-2 w-full md:w-96">
          <Search className="w-4 h-4 text-slate-400 shrink-0" />
          <input
            type="text"
            value={searchFilter}
            onChange={e => setSearchFilter(e.target.value)}
            placeholder="Search across 8 SEBI sections, entities, or disclosures..."
            className="w-full bg-transparent text-xs text-slate-200 placeholder-slate-500 focus:outline-none font-medium"
          />
        </div>
        <div className="flex items-center gap-3">
          <button
            onClick={() => setIsContagionOpen(true)}
            className="px-3 py-1.5 rounded-lg bg-gradient-to-r from-rose-950/80 to-amber-950/80 hover:from-rose-900 hover:to-amber-900 border border-rose-500/50 hover:border-rose-400 text-rose-200 text-xs font-mono font-bold flex items-center gap-1.5 transition-all cursor-pointer shadow-md"
          >
            <Zap className="w-3.5 h-3.5 text-rose-400 animate-pulse" />
            <span>Simulate Cross-Section Contagion</span>
          </button>
        </div>
      </div>

      {/* 8 Statutory Section Cards Grid */}
      {isLoading ? (
        <div className="flex items-center justify-center py-20 text-xs text-slate-400 gap-2">
          <RefreshCw className="w-4 h-4 animate-spin text-blue-400" />
          Loading SEBI statutory section hierarchy...
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {filteredSections.map(sec => {
            const hasCritical = (sec.severities?.CRITICAL_RISK || 0) > 0;
            const hasAlert = (sec.severities?.HIGH_ALERT || 0) > 0;

            return (
              <div
                key={sec.sectionId}
                onClick={() => onSelectSection(sec.sectionId)}
                className={`p-4 rounded-xl border transition-all cursor-pointer flex flex-col justify-between group hover:shadow-xl ${
                  hasCritical
                    ? 'bg-rose-950/20 border-rose-900/40 hover:border-rose-500/80 hover:bg-rose-950/30'
                    : hasAlert
                    ? 'bg-amber-950/20 border-amber-900/40 hover:border-amber-500/80 hover:bg-amber-950/30'
                    : 'bg-slate-900/60 border-slate-800 hover:border-blue-500/80 hover:bg-slate-900/90'
                }`}
              >
                <div>
                  {/* Top Section Badge & SEBI Schedule Reference */}
                  <div className="flex items-center justify-between mb-2">
                    <span className="px-2 py-0.5 rounded text-[10px] font-mono font-bold bg-slate-800 text-slate-200 border border-slate-700">
                      Section {sec.sectionNumber}
                    </span>
                    <span className="text-[9px] font-mono text-slate-500 truncate max-w-[140px]">
                      {sec.sebiSchedule.split(',')[0]}
                    </span>
                  </div>

                  <h3 className="text-xs font-bold text-slate-100 group-hover:text-blue-300 transition-colors line-clamp-1 mb-1">
                    {sec.title}
                  </h3>

                  <p className="text-[11px] text-slate-400 line-clamp-2 leading-relaxed mb-3">
                    {sec.description}
                  </p>

                  {/* Quantified Exposure & Severity Tags */}
                  <div className="space-y-2 pt-2 border-t border-slate-800/80">
                    {sec.totalFinancialExposureCr > 0 && (
                      <div className="flex justify-between text-xs">
                        <span className="text-slate-400 font-mono text-[10px]">Financial Exposure:</span>
                        <span className="font-mono font-bold text-rose-400">
                          ₹{sec.totalFinancialExposureCr.toLocaleString(undefined, { maximumFractionDigits: 1 })} Cr
                        </span>
                      </div>
                    )}

                    <div className="flex items-center gap-1.5 flex-wrap">
                      <span className="text-[9px] px-1.5 py-0.5 rounded bg-blue-500/10 text-blue-300 border border-blue-500/20 font-mono">
                        {sec.totalFacts} Facts
                      </span>
                      <span className="text-[9px] px-1.5 py-0.5 rounded bg-purple-500/10 text-purple-300 border border-purple-500/20 font-mono">
                        {sec.entityCount} Entities
                      </span>
                      {hasCritical && (
                        <span className="text-[9px] px-1.5 py-0.5 rounded bg-rose-500/20 text-rose-300 border border-rose-500/30 font-mono font-bold">
                          {sec.severities.CRITICAL_RISK} Critical
                        </span>
                      )}
                    </div>
                  </div>
                </div>

                {/* Bottom Action Footer */}
                <div className="pt-3 mt-3 border-t border-slate-800/60 flex items-center justify-between text-xs font-semibold text-blue-400 group-hover:text-blue-300">
                  <span>Drill down into Section Subgraph</span>
                  <ChevronRight className="w-4 h-4 transform group-hover:translate-x-1 transition-transform" />
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* Contagion Shock Workbench Modal */}
      <ContagionShockModal
        isOpen={isContagionOpen}
        onClose={() => setIsContagionOpen(false)}
        initialFactId="FACT_S06_01_CESTAT_INDIRECT_TAX"
        initialEntityName="Customs, Excise and Service Tax Appellate Tribunal (CESTAT) Disputes"
        initialGrossExposure={4455.47}
      />
    </div>
  );
};
