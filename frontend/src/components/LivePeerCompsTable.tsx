import React, { useState } from 'react';
import { LivePeerComp } from '../types/terminal';
import { Layers, ArrowUpDown, ExternalLink, Sparkles, ChevronDown, ChevronUp } from 'lucide-react';

interface LivePeerCompsTableProps {
  peers: LivePeerComp[];
}

export const LivePeerCompsTable: React.FC<LivePeerCompsTableProps> = ({ peers }) => {
  const [isCollapsed, setIsCollapsed] = useState<boolean>(false);
  const [sortBy, setSortBy] = useState<keyof LivePeerComp>('marketCapCr');
  const [sortAsc, setSortAsc] = useState<boolean>(false);
  const [filterType, setFilterType] = useState<'all' | 'drhp' | 'algorithmic'>('all');

  const filteredPeers = peers.filter((p) => {
    if (filterType === 'drhp') return p.isDrhpDeclared;
    if (filterType === 'algorithmic') return !p.isDrhpDeclared;
    return true;
  });

  const sortedPeers = [...filteredPeers].sort((a, b) => {
    const valA = a[sortBy];
    const valB = b[sortBy];
    if (typeof valA === 'number' && typeof valB === 'number') {
      return sortAsc ? valA - valB : valB - valA;
    }
    return 0;
  });

  const handleSort = (field: keyof LivePeerComp) => {
    if (sortBy === field) {
      setSortAsc(!sortAsc);
    } else {
      setSortBy(field);
      setSortAsc(false);
    }
  };

  return (
    <div id="module-live-comps" className="rounded-xl border border-slate-700/80 border-t-2 border-t-cyan-500 bg-[#0C1322] p-5 shadow-xl transition-all">
      {/* Header & Controls */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-3 border-b border-slate-800">
        <div className="flex items-center gap-2.5">
          <div className="p-1.5 rounded-lg bg-cyan-950/80 border border-cyan-800/60 text-cyan-400">
            <Layers className="w-4 h-4" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="px-1.5 py-0.2 rounded text-[10px] font-mono font-bold bg-cyan-950 text-cyan-300 border border-cyan-800">
                MODULE 01
              </span>
              <h2 className="text-sm font-semibold tracking-wider text-slate-100 uppercase font-mono">
                NSE Live Peer Comps &amp; Multi-Dimensional Valuation
              </h2>
            </div>
            <p className="text-[11px] text-slate-400 font-mono mt-0.5">
              Cross-sectional peer multiples, SARD-weighted fundamental step-ups, and Mueller ROCE mean-reversion
            </p>
          </div>
        </div>

        <div className="flex items-center gap-3">
          {/* Filter Pills */}
          <div className="flex items-center gap-1.5 bg-[#090D12] p-1 rounded-lg border border-slate-800 text-xs font-mono">
            <button
              onClick={() => setFilterType('all')}
              className={`px-2.5 py-0.5 rounded transition-colors cursor-pointer ${
                filterType === 'all' ? 'bg-[#1E293B] text-slate-100 font-semibold' : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              ALL PEERS ({peers.length})
            </button>
            <button
              onClick={() => setFilterType('drhp')}
              className={`px-2.5 py-0.5 rounded transition-colors cursor-pointer ${
                filterType === 'drhp' ? 'bg-cyan-950/80 text-cyan-300 font-semibold border border-cyan-800' : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              DRHP DECLARED
            </button>
            <button
              onClick={() => setFilterType('algorithmic')}
              className={`px-2.5 py-0.5 rounded transition-colors cursor-pointer ${
                filterType === 'algorithmic' ? 'bg-indigo-950/80 text-indigo-300 font-semibold border border-indigo-800' : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              ALGO DISCOVERED
            </button>
          </div>

          {/* In-Card Collapse Toggle */}
          <button
            onClick={() => setIsCollapsed(!isCollapsed)}
            className="flex items-center gap-1 px-2.5 py-1 rounded-lg bg-slate-900 border border-slate-700/80 hover:border-slate-500 text-slate-400 hover:text-slate-200 text-xs font-mono transition-all cursor-pointer shadow-sm"
            title={isCollapsed ? 'Expand Comps Table' : 'Collapse Comps Table'}
          >
            <span>{isCollapsed ? 'Expand' : 'Collapse'}</span>
            {isCollapsed ? <ChevronDown className="w-3.5 h-3.5" /> : <ChevronUp className="w-3.5 h-3.5" />}
          </button>
        </div>
      </div>

      {!isCollapsed && (
        <div className="overflow-x-auto mt-3">
        <table className="w-full text-left text-xs border-collapse">
          <thead>
            <tr className="border-b border-[#1E293B] text-[11px] font-mono text-slate-400 bg-[#0C111A]">
              <th className="py-2.5 px-3 font-semibold">TICKER / NAME</th>
              <th
                className="py-2.5 px-3 font-semibold text-right cursor-pointer hover:text-slate-200"
                onClick={() => handleSort('lastPrice')}
              >
                <div className="flex items-center justify-end gap-1">
                  <span>PRICE (₹)</span>
                  <ArrowUpDown className="w-3 h-3 text-slate-500" />
                </div>
              </th>
              <th
                className="py-2.5 px-3 font-semibold text-right cursor-pointer hover:text-slate-200"
                onClick={() => handleSort('pChange')}
              >
                <div className="flex items-center justify-end gap-1">
                  <span>1D CHG %</span>
                  <ArrowUpDown className="w-3 h-3 text-slate-500" />
                </div>
              </th>
              <th
                className="py-2.5 px-3 font-semibold text-right cursor-pointer hover:text-slate-200"
                onClick={() => handleSort('pe')}
              >
                <div className="flex items-center justify-end gap-1">
                  <span>P/E (x)</span>
                  <ArrowUpDown className="w-3 h-3 text-slate-500" />
                </div>
              </th>
              <th
                className="py-2.5 px-3 font-semibold text-right cursor-pointer hover:text-slate-200"
                onClick={() => handleSort('evEbitda')}
              >
                <div className="flex items-center justify-end gap-1">
                  <span>EV/EBITDA</span>
                  <ArrowUpDown className="w-3 h-3 text-slate-500" />
                </div>
              </th>
              <th
                className="py-2.5 px-3 font-semibold text-right cursor-pointer hover:text-slate-200"
                onClick={() => handleSort('revenueCagr3Y')}
              >
                <div className="flex items-center justify-end gap-1">
                  <span>3Y CAGR</span>
                  <ArrowUpDown className="w-3 h-3 text-slate-500" />
                </div>
              </th>
              <th
                className="py-2.5 px-3 font-semibold text-right cursor-pointer hover:text-slate-200"
                onClick={() => handleSort('ebitdaMargin')}
              >
                <div className="flex items-center justify-end gap-1">
                  <span>EBITDA %</span>
                  <ArrowUpDown className="w-3 h-3 text-slate-500" />
                </div>
              </th>
              <th
                className="py-2.5 px-3 font-semibold text-right cursor-pointer hover:text-slate-200"
                onClick={() => handleSort('roce')}
              >
                <div className="flex items-center justify-end gap-1">
                  <span>ROCE %</span>
                  <ArrowUpDown className="w-3 h-3 text-slate-500" />
                </div>
              </th>
              <th className="py-2.5 px-3 font-semibold text-center">52-WEEK RANGE</th>
              <th
                className="py-2.5 px-3 font-semibold text-right cursor-pointer hover:text-slate-200"
                onClick={() => handleSort('marketCapCr')}
              >
                <div className="flex items-center justify-end gap-1">
                  <span>MCAP (₹ CR)</span>
                  <ArrowUpDown className="w-3 h-3 text-slate-500" />
                </div>
              </th>
              <th className="py-2.5 px-3 font-semibold text-center">PROVENANCE</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-[#172230]">
            {sortedPeers.map((peer) => {
              const isPositive = peer.pChange >= 0;
              const rangePct = Math.min(
                Math.max(((peer.lastPrice - peer.low52) / (peer.high52 - peer.low52)) * 100, 0),
                100
              );

              return (
                <tr key={peer.symbol} className="hover:bg-[#141B26] transition-colors group">
                  {/* Ticker & Name */}
                  <td className="py-2.5 px-3">
                    <div className="font-mono font-bold text-slate-200 group-hover:text-cyan-400 transition-colors">
                      {peer.symbol}
                    </div>
                    <div className="text-[11px] text-slate-400 truncate max-w-[140px] font-sans">
                      {peer.companyName}
                    </div>
                  </td>

                  {/* Price */}
                  <td className="py-2.5 px-3 text-right font-mono font-medium text-slate-100 tabular-nums">
                    ₹{peer.lastPrice.toLocaleString('en-IN', { minimumFractionDigits: 2 })}
                  </td>

                  {/* 1D Chg */}
                  <td
                    className={`py-2.5 px-3 text-right font-mono font-medium tabular-nums ${
                      isPositive ? 'text-emerald-400' : 'text-rose-400'
                    }`}
                  >
                    {isPositive ? '+' : ''}
                    {peer.pChange.toFixed(2)}%
                  </td>

                  {/* P/E */}
                  <td className="py-2.5 px-3 text-right font-mono tabular-nums text-slate-200">
                    {peer.pe.toFixed(1)}x
                  </td>

                  {/* EV/EBITDA */}
                  <td className="py-2.5 px-3 text-right font-mono tabular-nums text-slate-300">
                    {peer.evEbitda.toFixed(1)}x
                  </td>

                  {/* 3Y CAGR */}
                  <td className="py-2.5 px-3 text-right font-mono tabular-nums text-cyan-400">
                    {peer.revenueCagr3Y.toFixed(1)}%
                  </td>

                  {/* EBITDA Margin */}
                  <td className="py-2.5 px-3 text-right font-mono tabular-nums text-slate-300">
                    {peer.ebitdaMargin.toFixed(1)}%
                  </td>

                  {/* ROCE */}
                  <td className="py-2.5 px-3 text-right font-mono tabular-nums text-emerald-400">
                    {peer.roce.toFixed(1)}%
                  </td>

                  {/* 52W Range Bar */}
                  <td className="py-2.5 px-3 min-w-[120px]">
                    <div className="flex items-center gap-1.5 text-[10px] font-mono text-slate-500 justify-between">
                      <span>₹{peer.low52.toFixed(0)}</span>
                      <span>₹{peer.high52.toFixed(0)}</span>
                    </div>
                    <div className="h-1.5 w-full bg-[#090D12] rounded-full overflow-hidden border border-[#223044] relative mt-0.5">
                      <div
                        className="h-full bg-cyan-400 rounded-full"
                        style={{ width: `${rangePct}%` }}
                      />
                    </div>
                  </td>

                  {/* Market Cap */}
                  <td className="py-2.5 px-3 text-right font-mono tabular-nums text-slate-200">
                    ₹{(peer.marketCapCr / 1000).toFixed(1)}k Cr
                  </td>

                  {/* Provenance Badge */}
                  <td className="py-2.5 px-3 text-center">
                    {peer.isDrhpDeclared ? (
                      <span className="font-mono text-[10px] px-2 py-0.5 rounded bg-cyan-950/70 border border-cyan-800 text-cyan-300 font-medium">
                        DRHP LISTED
                      </span>
                    ) : (
                      <span className="font-mono text-[10px] px-2 py-0.5 rounded bg-indigo-950/70 border border-indigo-800 text-indigo-300 font-medium">
                        ALGO MATCH
                      </span>
                    )}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
      )}
    </div>
  );
};
