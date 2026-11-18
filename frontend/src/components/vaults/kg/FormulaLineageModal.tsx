import React, { useState, useEffect } from 'react';
import {
  X,
  Binary,
  Layers,
  ShieldCheck,
  ChevronRight,
  BookOpen,
  CheckCircle2,
  AlertTriangle,
  Info
} from 'lucide-react';
import { fetchFormulaLineages, FormulaLineageResponse, FormulaLineageItem } from '../../../services/dataService';

interface FormulaLineageModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSelectCitation?: (page: number, quote: string) => void;
}

export const FormulaLineageModal: React.FC<FormulaLineageModalProps> = ({
  isOpen,
  onClose,
  onSelectCitation
}) => {
  const [data, setData] = useState<FormulaLineageResponse | null>(null);
  const [selectedFormula, setSelectedFormula] = useState<FormulaLineageItem | null>(null);
  const [activeTab, setActiveTab] = useState<'formulas' | 'sections'>('formulas');
  const [isLoading, setIsLoading] = useState<boolean>(false);

  useEffect(() => {
    if (!isOpen) return;
    setIsLoading(true);
    fetchFormulaLineages()
      .then(res => {
        setData(res);
        if (res.formulas && res.formulas.length > 0) {
          setSelectedFormula(res.formulas[0]);
        }
      })
      .finally(() => setIsLoading(false));
  }, [isOpen]);

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 overflow-hidden flex items-center justify-center bg-slate-950/80 backdrop-blur-md p-4 animate-fade-in">
      <div className="relative w-full max-w-5xl bg-slate-900 border border-slate-800 rounded-2xl shadow-2xl flex flex-col max-h-[90vh] text-slate-100 overflow-hidden">
        {/* Header */}
        <div className="p-5 border-b border-slate-800 bg-slate-950/80 flex items-center justify-between shrink-0">
          <div className="flex items-center gap-3">
            <div className="p-2.5 rounded-xl bg-purple-500/10 border border-purple-500/30 text-purple-400">
              <Binary className="w-5 h-5" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h3 className="text-base font-bold text-slate-100">
                  Mathematical Lineage & Canonical 84 Attributes DAG
                </h3>
                <span className="px-2 py-0.5 rounded text-[10px] font-semibold bg-blue-500/10 text-blue-400 border border-blue-500/30">
                  Rule E.3 Zero-Truthiness
                </span>
                <span className="px-2 py-0.5 rounded text-[10px] font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/30">
                  SEBI ICDR Schedule VI
                </span>
              </div>
              <p className="text-xs text-slate-400 mt-0.5">
                Full bi-directional traceability from institutional valuation formulas down to statutory DRHP extracted attributes.
              </p>
            </div>
          </div>

          <div className="flex items-center gap-3">
            <div className="flex bg-slate-950 p-1 rounded-lg border border-slate-800">
              <button
                onClick={() => setActiveTab('formulas')}
                className={`px-3 py-1 rounded text-xs font-semibold transition-all ${
                  activeTab === 'formulas'
                    ? 'bg-purple-600 text-white'
                    : 'text-slate-400 hover:text-slate-200'
                }`}
              >
                9 Forensic Formulas
              </button>
              <button
                onClick={() => setActiveTab('sections')}
                className={`px-3 py-1 rounded text-xs font-semibold transition-all ${
                  activeTab === 'sections'
                    ? 'bg-purple-600 text-white'
                    : 'text-slate-400 hover:text-slate-200'
                }`}
              >
                10 SEBI Sections (84 Attr)
              </button>
            </div>
            <button
              onClick={onClose}
              className="p-1.5 rounded-lg hover:bg-slate-800 text-slate-400 hover:text-slate-200 transition-colors"
            >
              <X className="w-5 h-5" />
            </button>
          </div>
        </div>

        {/* Body content */}
        <div className="flex-1 overflow-y-auto p-5">
          {isLoading && (
            <div className="flex items-center justify-center py-20 text-slate-400 text-xs">
              Loading statutory formula lineage DAG...
            </div>
          )}

          {!isLoading && data && activeTab === 'formulas' && (
            <div className="grid grid-cols-1 md:grid-cols-12 gap-5">
              {/* Formula List Left Column */}
              <div className="md:col-span-5 space-y-2.5 max-h-[640px] overflow-y-auto pr-2">
                <div className="text-[11px] font-bold text-slate-400 uppercase tracking-wider mb-2">
                  Select Analytical Formula ({data.formulas.length})
                </div>
                {data.formulas.map(f => (
                  <div
                    key={f.formulaId}
                    onClick={() => setSelectedFormula(f)}
                    className={`p-3.5 rounded-xl border transition-all cursor-pointer text-left ${
                      selectedFormula?.formulaId === f.formulaId
                        ? 'bg-purple-950/40 border-purple-500 shadow-md shadow-purple-500/10'
                        : 'bg-slate-950/50 border-slate-800 hover:border-slate-700 hover:bg-slate-950/80'
                    }`}
                  >
                    <div className="flex items-center justify-between mb-1">
                      <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-slate-800 text-purple-300 font-semibold">
                        {f.formulaId}
                      </span>
                      <span className="text-[10px] text-slate-400 font-mono">
                        {f.targetVault}
                      </span>
                    </div>
                    <h4 className="text-xs font-bold text-slate-100">{f.name}</h4>
                    <p className="text-[11px] text-slate-400 line-clamp-1 mt-1 font-mono">
                      {f.plainFormula}
                    </p>
                    <div className="flex items-center gap-1.5 mt-2">
                      <span className="text-[9px] px-1.5 py-0.5 rounded bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                        {f.constituentAttributes.length} Attributes Bound
                      </span>
                    </div>
                  </div>
                ))}
              </div>

              {/* Selected Formula Lineage Inspector Right Column */}
              <div className="md:col-span-7 bg-slate-950/70 border border-slate-800 rounded-xl p-5 space-y-5">
                {selectedFormula ? (
                  <>
                    <div className="border-b border-slate-800 pb-3">
                      <div className="flex items-center justify-between">
                        <span className="text-[10px] font-mono text-purple-400 font-bold uppercase tracking-wider">
                          {selectedFormula.category} · {selectedFormula.formulaId}
                        </span>
                        <span className="text-[10px] px-2 py-0.5 rounded bg-slate-800 text-slate-300 font-mono">
                          Vault: {selectedFormula.targetVault}
                        </span>
                      </div>
                      <h3 className="text-sm font-bold text-slate-100 mt-1">
                        {selectedFormula.name}
                      </h3>
                      <p className="text-xs text-slate-400 mt-1">
                        {selectedFormula.interpretation}
                      </p>
                    </div>

                    {/* Mathematical Representation */}
                    <div className="space-y-2">
                      <div className="text-[11px] font-bold text-slate-400 uppercase tracking-wider">
                        Mathematical Specification
                      </div>
                      <div className="p-3.5 rounded-xl bg-slate-900 border border-purple-500/30 text-purple-200 font-mono text-xs overflow-x-auto shadow-inner">
                        {selectedFormula.latexFormula}
                      </div>
                      <div className="p-2.5 rounded-lg bg-slate-900/60 border border-slate-800 text-[11px] text-slate-300 font-mono">
                        Plain: {selectedFormula.plainFormula}
                      </div>
                    </div>

                    {/* Statutory Authority */}
                    <div className="space-y-2">
                      <div className="text-[11px] font-bold text-slate-400 uppercase tracking-wider">
                        Statutory SEBI ICDR Authority
                      </div>
                      <div className="p-3 rounded-lg bg-slate-900/60 border border-slate-800 text-xs text-slate-200 flex items-start gap-2">
                        <ShieldCheck className="w-4 h-4 text-emerald-400 shrink-0 mt-0.5" />
                        <div>
                          <strong className="text-emerald-400">{selectedFormula.statutoryReference}</strong>
                          <p className="text-[11px] text-slate-400 mt-0.5">
                            Mandatory compliance requirement under SEBI (Issue of Capital and Disclosure Requirements) Regulations, 2018.
                          </p>
                        </div>
                      </div>
                    </div>

                    {/* Constituent 84 Canonical Attributes */}
                    <div className="space-y-2">
                      <div className="text-[11px] font-bold text-slate-400 uppercase tracking-wider flex items-center justify-between">
                        <span>Constituent Canonical Attributes ({selectedFormula.constituentAttributes.length})</span>
                        <span className="text-[10px] text-blue-400">Exact Database & Graph Binding</span>
                      </div>
                      <div className="flex flex-wrap gap-1.5">
                        {selectedFormula.constituentAttributes.map(attr => (
                          <span
                            key={attr}
                            className="px-2.5 py-1 rounded-lg bg-blue-500/10 border border-blue-500/30 text-blue-300 text-xs font-mono font-medium"
                          >
                            {attr}
                          </span>
                        ))}
                      </div>
                    </div>

                    {/* Critical Thresholds */}
                    {selectedFormula.thresholdConditions && Object.keys(selectedFormula.thresholdConditions).length > 0 && (
                      <div className="space-y-2">
                        <div className="text-[11px] font-bold text-slate-400 uppercase tracking-wider">
                          Decision Thresholds & Gates
                        </div>
                        <div className="grid grid-cols-2 gap-2">
                          {Object.entries(selectedFormula.thresholdConditions).map(([k, v]) => (
                            <div key={k} className="p-2.5 rounded-lg bg-slate-900 border border-slate-800 text-xs">
                              <span className="text-[10px] text-slate-400 font-mono capitalize">{k}:</span>
                              <div className="font-semibold text-slate-200 font-mono mt-0.5">{v}</div>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                  </>
                ) : (
                  <div className="py-20 text-center text-slate-500 text-xs">
                    Select a formula from the left to inspect its mathematical lineage.
                  </div>
                )}
              </div>
            </div>
          )}

          {!isLoading && data && activeTab === 'sections' && (
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <span className="text-xs font-bold uppercase tracking-wider text-slate-400">
                  10 Statutory SEBI ICDR Schedule VI Chapters ({data.totalAttributes} Canonical Attributes)
                </span>
                <span className="text-[11px] text-emerald-400 font-mono">100% Corpus Coverage</span>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                {data.statutorySections.map(s => (
                  <div
                    key={s.index}
                    className="p-4 rounded-xl bg-slate-950/60 border border-slate-800 space-y-2"
                  >
                    <div className="flex items-center justify-between">
                      <span className="text-xs font-bold text-slate-200">
                        Section {s.index}: {s.name}
                      </span>
                      <span className="px-2 py-0.5 rounded text-[10px] font-mono font-bold bg-blue-500/10 text-blue-400 border border-blue-500/30">
                        {s.attributeCount} Attributes
                      </span>
                    </div>
                    <div className="text-[11px] text-slate-400 font-mono flex items-center gap-1">
                      <BookOpen className="w-3 h-3 text-slate-500" />
                      SEBI Authority: {s.sebiSchedule}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
