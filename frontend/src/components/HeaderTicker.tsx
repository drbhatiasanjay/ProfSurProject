import React from 'react';
import { MarketIndex } from '../types/terminal';
import { ShieldCheck, Activity, RefreshCw, Download, FileSpreadsheet, BookOpen, LayoutGrid } from 'lucide-react';

interface HeaderTickerProps {
  indices: MarketIndex[];
  onRefresh?: () => void;
  isRefreshing?: boolean;
  selectedSymbol?: string;
  onSymbolChange?: (symbol: string) => void;
  onExportExcel?: () => void;
  isExportingExcel?: boolean;
  onOpenAlmanac?: () => void;
}

export const HeaderTicker: React.FC<HeaderTickerProps> = ({
  indices,
  onRefresh,
  isRefreshing = false,
  selectedSymbol = 'NTPCGREEN',
  onSymbolChange,
  onExportExcel,
  isExportingExcel = false,
  onOpenAlmanac,
}) => {
  const quickDeals = [
    { symbol: 'NTPCGREEN', label: 'NTPC Green', sector: 'Renewables' },
    { symbol: 'HCCB', label: 'HCCB (Coke)', sector: 'Beverages' },
    { symbol: 'SWIGGY', label: 'Swiggy', sector: 'Hyperlocal' },
    { symbol: 'TATA_TECH', label: 'Tata Tech', sector: 'ER&D' },
  ];

  const getWorkspaceUrl = (): string => {
    try {
      const params = new URLSearchParams(window.location.search);
      const token = params.get('auth_token') || sessionStorage.getItem('portal_auth_token') || localStorage.getItem('portal_auth_token');
      if (token) {
        sessionStorage.setItem('portal_auth_token', token);
        return `http://localhost:8501/?switch_workspace=1&auth_token=${encodeURIComponent(token)}`;
      }
    } catch {
      // ignore
    }
    return 'http://localhost:8501/?switch_workspace=1';
  };

  return (
    <header className="border-b border-[#223044] bg-[#090D12] px-4 py-2 sticky top-0 z-50 shadow-md">
      <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-3">
        {/* Left: System Status & Terminal Identity */}
        <div className="flex items-center gap-4 shrink-0">
          <div className="flex items-center gap-2">
            <span className="relative flex h-2 w-2">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
              <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500"></span>
            </span>
            <span className="font-mono text-xs tracking-wider font-semibold text-emerald-400 uppercase">
              NSE LIVE FEED
            </span>
          </div>

          <div className="hidden sm:flex items-center gap-1.5 px-2 py-0.5 rounded bg-[#101726] border border-[#1E2B3E] text-xs font-mono text-slate-300">
            <Activity className="w-3.5 h-3.5 text-cyan-400" />
            <span className="text-slate-400">WORKSPACE:</span>
            <span className="text-cyan-300 font-bold">PRE-IPO TERMINAL</span>
            <span className="text-[10px] text-slate-500 font-normal">SEBI (RA) 2014</span>
          </div>

          {/* Quick Deal Switcher Pills */}
          {onSymbolChange && (
            <div className="hidden md:flex items-center gap-1.5 pl-2 border-l border-[#223044]">
              {quickDeals.map((d) => {
                const isActive = selectedSymbol.toUpperCase().includes(d.symbol);
                return (
                  <button
                    key={d.symbol}
                    onClick={() => onSymbolChange(d.symbol)}
                    className={`px-2 py-0.5 rounded text-[11px] font-mono transition-all cursor-pointer ${
                      isActive
                        ? 'bg-cyan-500/20 text-cyan-300 border border-cyan-500/50 font-bold shadow-[0_0_8px_rgba(6,182,212,0.2)]'
                        : 'bg-[#121B29] text-slate-400 border border-[#1E2B3E] hover:text-slate-200 hover:border-slate-600'
                    }`}
                  >
                    {d.label}
                  </button>
                );
              })}
            </div>
          )}
        </div>

        {/* Center: Live Sector Indices Stream */}
        <div className="flex items-center gap-4 overflow-x-auto py-0.5 scrollbar-none">
          {indices.map((idx) => {
            const isPositive = idx.change >= 0;
            return (
              <div
                key={idx.symbol}
                className="flex items-center gap-2 text-xs whitespace-nowrap bg-[#0E1522] px-2.5 py-1 rounded border border-[#1A2536]"
              >
                <span className="font-mono font-medium text-slate-400 text-[11px]">{idx.symbol}</span>
                <span className="font-mono text-slate-200 font-semibold text-[11px] tabular-nums">
                  {idx.lastPrice.toLocaleString('en-IN', {
                    maximumFractionDigits: 2,
                    minimumFractionDigits: 2,
                  })}
                </span>
                <span
                  className={`font-mono text-[10px] font-medium tabular-nums ${
                    isPositive ? 'text-emerald-400' : 'text-rose-400'
                  }`}
                >
                  {isPositive ? '+' : ''}
                  {idx.pChange.toFixed(2)}%
                </span>
                {idx.pe && (
                  <span className="text-[10px] text-slate-500 font-mono hidden xl:inline">
                    P/E {idx.pe.toFixed(1)}x
                  </span>
                )}
              </div>
            );
          })}
        </div>

        {/* Right: Security, Excel Export, Almanac & Refresh Actions */}
        <div className="flex items-center gap-2 self-end lg:self-center shrink-0">
          {/* Master Workspace Return Button (Port 8501 Gateway Switcher) */}
          <a
            id="header-workspace-btn"
            href={getWorkspaceUrl()}
            className="flex items-center gap-1.5 px-3 py-1 rounded bg-indigo-950/70 border border-indigo-600/60 hover:bg-indigo-900/80 hover:border-indigo-400 text-xs text-indigo-300 hover:text-indigo-100 font-mono font-semibold transition-all shadow-sm"
            title="Return to Master Workspace Gateway (Switch between CMIE and Pre-IPO)"
          >
            <LayoutGrid className="w-3.5 h-3.5 text-indigo-400" />
            <span className="text-[11px] font-bold">Workspaces</span>
          </a>

          {/* Methodology Almanac Educational Reference */}
          {onOpenAlmanac && (
            <button
              onClick={onOpenAlmanac}
              className="flex items-center gap-1.5 px-2.5 py-1 rounded bg-cyan-950/60 border border-cyan-600/50 hover:bg-cyan-900/60 hover:border-cyan-400 text-xs text-cyan-300 font-mono font-semibold transition-all cursor-pointer shadow-sm"
              title="Open Quantitative Methodology Almanac & Educational Curriculum"
            >
              <BookOpen className="w-3.5 h-3.5 text-cyan-400" />
              <span className="text-[11px] font-bold">ALMANAC ⓘ</span>
            </button>
          )}

          {/* Auditable Excel Export Button */}
          {onExportExcel && (
            <button
              onClick={onExportExcel}
              disabled={isExportingExcel}
              className="flex items-center gap-1.5 px-2.5 py-1 rounded bg-emerald-950/60 border border-emerald-600/50 hover:bg-emerald-900/60 hover:border-emerald-500 text-xs text-emerald-300 font-mono font-semibold transition-all cursor-pointer disabled:opacity-50 shadow-sm"
              title="Download Auditable OpenPyXL Formula-Driven Valuation Model"
            >
              <FileSpreadsheet className={`w-3.5 h-3.5 ${isExportingExcel ? 'animate-pulse text-emerald-400' : 'text-emerald-400'}`} />
              <span className="text-[11px]">
                {isExportingExcel ? 'GENERATING...' : 'EXPORT .XLSX'}
              </span>
            </button>
          )}

          <div className="hidden xl:flex items-center gap-1 text-[11px] text-slate-400">
            <ShieldCheck className="w-3.5 h-3.5 text-cyan-400" />
            <span className="font-mono text-[10px] text-slate-400">SEBI AUDIT LEDGER: ACTIVE</span>
          </div>

          <button
            onClick={onRefresh}
            disabled={isRefreshing}
            className="flex items-center gap-1 px-2 py-1 rounded bg-[#151D2A] border border-[#223044] hover:bg-[#1A2536] hover:border-slate-500 text-xs text-slate-300 transition-all cursor-pointer disabled:opacity-50"
            title="Refresh Live NSE Quote Feeds"
          >
            <RefreshCw className={`w-3 h-3 text-slate-400 ${isRefreshing ? 'animate-spin text-cyan-400' : ''}`} />
            <span className="font-mono text-[11px]">SYNC</span>
          </button>
        </div>
      </div>
    </header>
  );
};
