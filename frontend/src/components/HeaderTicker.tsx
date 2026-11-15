import React from 'react';
import { MarketIndex } from '../types/terminal';
import { ShieldCheck, Activity, RefreshCw } from 'lucide-react';

interface HeaderTickerProps {
  indices: MarketIndex[];
  onRefresh?: () => void;
  isRefreshing?: boolean;
}

export const HeaderTicker: React.FC<HeaderTickerProps> = ({
  indices,
  onRefresh,
  isRefreshing = false
}) => {
  return (
    <header className="border-b border-[#223044] bg-[#090D12] px-4 py-2.5 sticky top-0 z-50">
      <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-3">
        {/* Left: System Status & Terminal Identity */}
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-2">
            <span className="relative flex h-2 w-2">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
              <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500"></span>
            </span>
            <span className="font-mono text-xs tracking-wider font-semibold text-emerald-400 uppercase">
              NSE LIVE FEED
            </span>
          </div>

          <div className="h-3 w-[1px] bg-[#223044] hidden sm:block" />

          <div className="flex items-center gap-1.5 text-xs text-slate-300">
            <span className="text-slate-500 font-mono">WORKSPACE:</span>
            <span className="font-semibold text-slate-200">PROFSUR / PRE-IPO TERMINAL</span>
            <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-cyan-950/70 border border-cyan-800/60 text-cyan-300">
              SEBI (RA) 2014
            </span>
          </div>
        </div>

        {/* Center: Live Index Streaming Ticker */}
        <div className="flex items-center gap-2 overflow-x-auto pb-1 lg:pb-0 scrollbar-none">
          {indices.map((idx) => {
            const isPositive = idx.pChange >= 0;
            return (
              <div
                key={idx.symbol}
                className="flex items-center gap-2 px-2.5 py-1 rounded bg-[#101620] border border-[#223044] text-xs shrink-0 hover:border-slate-600 transition-colors"
              >
                <span className="font-mono text-[11px] font-medium text-slate-400">
                  {idx.symbol}
                </span>
                <span className="font-mono font-semibold text-slate-100 tabular-nums">
                  {idx.lastPrice.toLocaleString('en-IN', { minimumFractionDigits: 2 })}
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

        {/* Right: Security & Refresh Actions */}
        <div className="flex items-center gap-3 self-end lg:self-center">
          <div className="flex items-center gap-1 text-[11px] text-slate-400">
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
