import React from 'react';
import {
  Layers,
  Activity,
  Calculator,
  Cpu,
  ShieldCheck,
  Building,
  TrendingUp,
  FileSpreadsheet,
  ChevronRight
} from 'lucide-react';

export type TerminalView =
  | 'overview'
  | 'peer_comps'
  | 'huber_calibrator'
  | 'ml_scorecard'
  | 'compliance';

interface SidebarNavProps {
  activeView: TerminalView;
  onViewChange: (view: TerminalView) => void;
  selectedSymbol: string;
  onSymbolChange: (symbol: string) => void;
}

export const SidebarNav: React.FC<SidebarNavProps> = ({
  activeView,
  onViewChange,
  selectedSymbol,
  onSymbolChange
}) => {
  const navItems = [
    {
      id: 'overview' as TerminalView,
      label: 'Mainboard IPO Terminal',
      sublabel: 'Live bidding, book & terms',
      icon: Activity,
    },
    {
      id: 'peer_comps' as TerminalView,
      label: 'Live Peer Comps',
      sublabel: 'NSE primary trading comps',
      icon: Layers,
    },
    {
      id: 'huber_calibrator' as TerminalView,
      label: 'Huber M-Estimator',
      sublabel: 'DRHP bias & warranted multiple',
      icon: Calculator,
    },
    {
      id: 'ml_scorecard' as TerminalView,
      label: 'Walk-Forward ML & SHAP',
      sublabel: 'Dual-head 180D outperformance',
      icon: Cpu,
    },
    {
      id: 'compliance' as TerminalView,
      label: 'SEBI RA Compliance Ledger',
      sublabel: 'Immutable SHA-256 audit log',
      icon: ShieldCheck,
    },
  ];

  const issuers = [
    { symbol: 'NTPCGREEN', name: 'NTPC Green Energy Ltd', size: '₹10,000 Cr', status: 'Bidding Live' },
    { symbol: 'HCCB', name: 'Hindustan Coca-Cola Beverages', size: '₹8,500 Cr (Est)', status: 'DRHP Drafting' },
    { symbol: 'SWIGGY', name: 'Swiggy Limited', size: '₹11,327 Cr', status: 'Post-Listing T+12' },
    { symbol: 'WAAREE', name: 'Waaree Energies Limited', size: '₹4,321 Cr', status: 'Trading Q2' },
  ];

  return (
    <aside className="w-full lg:w-72 bg-[#090D12] border-r border-[#223044] flex flex-col shrink-0">
      {/* Brand Header */}
      <div className="p-4 border-b border-[#223044] flex items-center justify-between">
        <div className="flex items-center gap-2.5">
          <div className="w-7 h-7 rounded bg-gradient-to-br from-cyan-500 to-indigo-600 flex items-center justify-center font-bold text-white font-mono text-sm shadow-md shadow-cyan-950">
            PS
          </div>
          <div>
            <div className="font-bold text-sm tracking-wide text-slate-100 font-mono">PROFSUR</div>
            <div className="text-[10px] text-slate-500 font-mono">QUANTITATIVE VALUATION</div>
          </div>
        </div>
        <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-emerald-950/60 border border-emerald-800 text-emerald-400">
          v3.4.0
        </span>
      </div>

      {/* Issuer Selector Dropdown Panel */}
      <div className="p-3 border-b border-[#223044]">
        <label className="text-[10px] font-mono text-slate-500 uppercase tracking-wider block mb-1.5">
          Active Pre-IPO Pipeline Issuer
        </label>
        <div className="space-y-1">
          {issuers.map((iss) => {
            const isSelected = selectedSymbol === iss.symbol;
            return (
              <button
                key={iss.symbol}
                onClick={() => onSymbolChange(iss.symbol)}
                className={`w-full text-left p-2 rounded transition-all flex items-center justify-between cursor-pointer border ${
                  isSelected
                    ? 'bg-[#151D2A] border-cyan-500/80 text-slate-100 shadow-sm'
                    : 'bg-[#101620]/60 border-[#1E293B] hover:border-slate-600 text-slate-400 hover:text-slate-200'
                }`}
              >
                <div>
                  <div className="font-mono text-xs font-bold flex items-center gap-1.5">
                    <span className={isSelected ? 'text-cyan-400' : 'text-slate-300'}>{iss.symbol}</span>
                    <span className="text-[9px] font-normal px-1 rounded bg-[#090D12] border border-[#223044] text-slate-400">
                      {iss.size}
                    </span>
                  </div>
                  <div className="text-[10px] text-slate-400 truncate max-w-[170px] mt-0.5">
                    {iss.name}
                  </div>
                </div>
                <div className="text-[9px] font-mono px-1.5 py-0.5 rounded bg-slate-900 border border-slate-700 text-slate-400">
                  {iss.status}
                </div>
              </button>
            );
          })}
        </div>
      </div>

      {/* Navigation Workspace Menu */}
      <nav className="p-3 space-y-1 flex-1 overflow-y-auto">
        <span className="text-[10px] font-mono text-slate-500 uppercase tracking-wider px-2 block mb-2">
          Forensic Intelligence Views
        </span>

        {navItems.map((item) => {
          const isActive = activeView === item.id;
          const Icon = item.icon;

          return (
            <button
              key={item.id}
              onClick={() => onViewChange(item.id)}
              className={`w-full text-left p-2.5 rounded-lg transition-all flex items-center gap-3 cursor-pointer ${
                isActive
                  ? 'bg-gradient-to-r from-cyan-950/70 to-transparent border-l-2 border-cyan-400 text-slate-100 font-semibold'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-[#101620]'
              }`}
            >
              <Icon className={`w-4 h-4 shrink-0 ${isActive ? 'text-cyan-400' : 'text-slate-500'}`} />
              <div className="flex-1 min-w-0">
                <div className="text-xs font-medium font-sans truncate">{item.label}</div>
                <div className="text-[10px] text-slate-500 font-mono truncate">{item.sublabel}</div>
              </div>
              {isActive && <ChevronRight className="w-3.5 h-3.5 text-cyan-400" />}
            </button>
          );
        })}
      </nav>

      {/* Footer Info */}
      <div className="p-3 border-t border-[#223044] text-[10px] text-slate-500 font-mono flex items-center justify-between">
        <span>NSE PRIMARY ADAPTER</span>
        <span className="text-emerald-400">ONLINE</span>
      </div>
    </aside>
  );
};
