import React, { useState, useEffect } from 'react';
import {
  fetchCMIEPeers,
  simulateMacroShock,
  simulateAnchorCliff,
  CMIEPeerComparisonResponse,
  MacroShockResult,
  AnchorCliffResult
} from '../../../services/dataService';

interface CMIEMacroWorkbenchProps {
  symbol?: string;
  onOpenExportModal?: () => void;
}

export const CMIEMacroWorkbench: React.FC<CMIEMacroWorkbenchProps> = ({
  onOpenExportModal
}) => {
  const [cmieData, setCmieData] = useState<CMIEPeerComparisonResponse | null>(null);
  const [crudeShift, setCrudeShift] = useState<number>(0.0);
  const [repoShiftBps, setRepoShiftBps] = useState<number>(0.0);
  const [shockResult, setShockResult] = useState<MacroShockResult | null>(null);
  const [anchorCliff, setAnchorCliff] = useState<AnchorCliffResult | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    fetchCMIEPeers().then(data => {
      if (data) setCmieData(data);
    });
    simulateAnchorCliff(40, 60).then(data => {
      if (data) setAnchorCliff(data);
    });
    simulateMacroShock(0, 0).then(data => {
      if (data) setShockResult(data);
    });
  }, []);

  const handleSimulateShock = async (crude: number, repo: number) => {
    setLoading(true);
    try {
      const res = await simulateMacroShock(crude, repo);
      if (res) setShockResult(res);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="bg-slate-900/95 border border-slate-700/80 rounded-xl shadow-2xl overflow-hidden mb-6 transition-all duration-300">
      {/* Top Banner */}
      <div className="px-6 py-4 border-b border-slate-800 flex flex-wrap items-center justify-between gap-3 bg-gradient-to-r from-slate-900 via-indigo-950/30 to-slate-900">
        <div className="flex items-center space-x-3">
          <div className="w-9 h-9 rounded-xl bg-purple-500/20 border border-purple-400/30 flex items-center justify-center text-purple-400 text-lg">
            🌐
          </div>
          <div>
            <div className="flex items-center space-x-2">
              <span className="text-xs font-bold text-white tracking-wide uppercase">CMIE ProwessIQ Peer Benchmarks & Macroeconomic Transmission</span>
              <span className="text-[10px] px-2 py-0.5 rounded-full bg-indigo-500/20 text-indigo-300 border border-indigo-500/30 font-mono">
                Cross-Ecosystem Linkage
              </span>
            </div>
            <p className="text-[11px] text-slate-400">Contextualizes prospectus valuation against listed beverage peers, PET packaging crude inflation, and repo rate sensitivity</p>
          </div>
        </div>

        {onOpenExportModal && (
          <button
            onClick={onOpenExportModal}
            className="px-3.5 py-1.5 rounded-lg bg-indigo-600/80 hover:bg-indigo-600 text-white text-xs font-semibold tracking-wide border border-indigo-400/40 shadow-md transition-all flex items-center space-x-1.5"
          >
            <span>🏛️ Institutional Export (.ttl / .cyp)</span>
          </button>
        )}
      </div>

      <div className="p-6 space-y-6">
        {/* Section 1: Peer Multiples Grid */}
        {cmieData && Array.isArray(cmieData.peers) && cmieData.peers.length > 0 && (
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <h4 className="text-xs font-bold uppercase tracking-wider text-slate-300 flex items-center space-x-2">
                <span>📊</span>
                <span>CMIE Prowess Peer Multiples Comparison</span>
              </h4>
              <span className="text-[11px] text-slate-400 font-mono">
                Target Ask: <strong className="text-emerald-400">{cmieData.issuer?.target_ipo_multiple ?? '24.5'}x EV/EBITDA</strong> (Implied P/E {cmieData.issuer?.implied_pe ?? '41.2'}x)
              </span>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              {cmieData.peers.map((peer: any, idx: number) => {
                const companyName = peer.company_name || peer.name || `Peer ${idx + 1}`;
                const ticker = peer.ticker_nse || peer.symbol || 'NSE';
                const multiple = peer.ev_ebitda_multiple ?? peer.evEbitda ?? peer.pe_multiple ?? peer.pe ?? 'N/A';
                const roce = peer.roce_pct !== undefined ? `${peer.roce_pct}%` : (peer.similarity ? `Sim: ${(peer.similarity * 100).toFixed(0)}%` : 'N/A');
                const grossMargin = peer.gross_margin_pct !== undefined ? `${peer.gross_margin_pct}%` : 'N/A';
                const ebitdaMargin = peer.ebitda_margin_pct !== undefined ? `${peer.ebitda_margin_pct}%` : 'N/A';
                const franchise = peer.franchise_exclusivity_years ? `${peer.franchise_exclusivity_years} yrs` : 'N/A';
                const verdict = peer.valuation_verdict || peer.verdict || 'Peer multiple indexed from CMIE Prowess database.';

                return (
                  <div
                    key={peer.peer_id || peer.symbol || idx}
                    className="p-4 rounded-xl bg-slate-950 border border-slate-800 hover:border-slate-700 transition-all space-y-3"
                  >
                    <div className="flex items-center justify-between">
                      <div>
                        <div className="text-xs font-bold text-slate-200">{companyName}</div>
                        <span className="text-[10px] font-mono text-indigo-400">NSE: {ticker}</span>
                      </div>
                      <span className="text-sm font-extrabold text-white font-mono bg-slate-900 px-2.5 py-1 rounded-lg border border-slate-800">
                        {typeof multiple === 'number' ? `${multiple}x` : multiple}
                      </span>
                    </div>

                    <div className="grid grid-cols-2 gap-2 text-[11px] font-mono">
                      <div className="p-1.5 rounded bg-slate-900 border border-slate-800/80">
                        <span className="text-slate-400 block text-[9px] uppercase">ROCE</span>
                        <strong className="text-emerald-400">{roce}</strong>
                      </div>
                      <div className="p-1.5 rounded bg-slate-900 border border-slate-800/80">
                        <span className="text-slate-400 block text-[9px] uppercase">Gross Margin</span>
                        <strong className="text-slate-200">{grossMargin}</strong>
                      </div>
                      <div className="p-1.5 rounded bg-slate-900 border border-slate-800/80">
                        <span className="text-slate-400 block text-[9px] uppercase">EBITDA Margin</span>
                        <strong className="text-slate-200">{ebitdaMargin}</strong>
                      </div>
                      <div className="p-1.5 rounded bg-slate-900 border border-slate-800/80">
                        <span className="text-slate-400 block text-[9px] uppercase">Franchise Tenor</span>
                        <strong className="text-amber-400">{franchise}</strong>
                      </div>
                    </div>

                    <p className="text-[11px] text-slate-400 leading-tight">
                      {verdict}
                    </p>
                  </div>
                );
              })}
            </div>

            {/* Relative Valuation Spread Callout */}
            <div className="p-3.5 rounded-xl bg-indigo-950/30 border border-indigo-900/50 flex items-start space-x-3">
              <span className="text-base">💡</span>
              <p className="text-xs text-indigo-200 leading-relaxed font-sans">
                {cmieData.relative_spread?.analytical_verdict ??
                  "HCCB's ask multiple benchmarked against peer universe. Normalized discount reflects franchise tenure, asset age, and working capital cycle."}
              </p>
            </div>
          </div>
        )}

        {/* Section 2: Macro Transmission Sliders */}
        <div className="p-5 rounded-xl bg-slate-950 border border-slate-800 space-y-4">
          <div className="flex items-center justify-between border-b border-slate-800/80 pb-3">
            <h4 className="text-xs font-bold uppercase tracking-wider text-slate-300 flex items-center space-x-2">
              <span>⚡</span>
              <span>Macroeconomic Factor Shock Simulator</span>
            </h4>
            <span className="text-[11px] text-slate-400 font-mono">
              Base Crude: $78.0/bbl · Base Repo: 6.50%
            </span>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Crude Oil Slider */}
            <div className="space-y-2">
              <div className="flex justify-between text-xs font-mono">
                <span className="text-slate-300 font-semibold">Brent Crude Price Shift</span>
                <span className="text-amber-400 font-bold">{crudeShift > 0 ? `+${crudeShift}` : crudeShift} USD/bbl</span>
              </div>
              <input
                type="range"
                min="-20"
                max="40"
                step="5"
                value={crudeShift}
                onChange={(e) => {
                  const val = parseFloat(e.target.value);
                  setCrudeShift(val);
                  handleSimulateShock(val, repoShiftBps);
                }}
                className="w-full h-1.5 bg-slate-800 rounded-lg appearance-none cursor-pointer accent-amber-500"
              />
              <div className="flex justify-between text-[10px] text-slate-500 font-mono">
                <span>-$20 ($58/bbl)</span>
                <span>Base ($78/bbl)</span>
                <span>+$40 ($118/bbl)</span>
              </div>
            </div>

            {/* RBI Repo Rate Slider */}
            <div className="space-y-2">
              <div className="flex justify-between text-xs font-mono">
                <span className="text-slate-300 font-semibold">RBI Repo Rate Shock</span>
                <span className="text-rose-400 font-bold">{repoShiftBps > 0 ? `+${repoShiftBps}` : repoShiftBps} bps</span>
              </div>
              <input
                type="range"
                min="-50"
                max="200"
                step="25"
                value={repoShiftBps}
                onChange={(e) => {
                  const val = parseFloat(e.target.value);
                  setRepoShiftBps(val);
                  handleSimulateShock(crudeShift, val);
                }}
                className="w-full h-1.5 bg-slate-800 rounded-lg appearance-none cursor-pointer accent-rose-500"
              />
              <div className="flex justify-between text-[10px] text-slate-500 font-mono">
                <span>-50 bps (6.00%)</span>
                <span>Base (6.50%)</span>
                <span>+200 bps (8.50%)</span>
              </div>
            </div>
          </div>

          {/* Macro Impact Waterfall Metrics */}
          {shockResult && (
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 pt-3 border-t border-slate-800/80 text-center font-mono text-xs">
              <div className="p-3 rounded-lg bg-slate-900 border border-slate-800">
                <span className="text-[10px] text-slate-400 uppercase block">PET Resin Inflation</span>
                <strong className={shockResult.pet_resin_inflation_pct > 0 ? 'text-amber-400' : 'text-emerald-400'}>
                  {shockResult.pet_resin_inflation_pct > 0 ? `+${shockResult.pet_resin_inflation_pct}%` : `${shockResult.pet_resin_inflation_pct}%`}
                </strong>
              </div>
              <div className="p-3 rounded-lg bg-slate-900 border border-slate-800">
                <span className="text-[10px] text-slate-400 uppercase block">Gross Margin Comp.</span>
                <strong className="text-rose-400">
                  -{shockResult.gross_margin_compression_bps} bps
                </strong>
              </div>
              <div className="p-3 rounded-lg bg-slate-900 border border-slate-800">
                <span className="text-[10px] text-slate-400 uppercase block">Interest Cost Hike</span>
                <strong className="text-rose-400">
                  +₹{shockResult.incremental_borrowing_cost_cr} Cr
                </strong>
              </div>
              <div className="p-3 rounded-lg bg-slate-900 border border-slate-800">
                <span className="text-[10px] text-slate-400 uppercase block">Fair Multiple Haircut</span>
                <strong className="text-amber-400">
                  -{shockResult.relative_multiple_discount_pct}%
                </strong>
              </div>
            </div>
          )}
        </div>

        {/* Section 3: Anchor Investor Lock-In Expiry Cliff Schedule */}
        {anchorCliff && (
          <div className="p-5 rounded-xl bg-slate-950 border border-slate-800 space-y-3">
            <div className="flex items-center justify-between border-b border-slate-800/80 pb-3">
              <h4 className="text-xs font-bold uppercase tracking-wider text-slate-300 flex items-center space-x-2">
                <span>🔓</span>
                <span>Post-IPO Anchor Investor Lock-In Expiry Schedule (SEBI Reg 16)</span>
              </h4>
              <span className="text-[11px] font-mono text-amber-400">
                Supply Pressure Index: <strong>{anchorCliff.supply_wall_pressure_index}/100</strong>
              </span>
            </div>

            <div className="overflow-x-auto">
              <table className="w-full text-xs text-left font-mono">
                <thead>
                  <tr className="border-b border-slate-800 text-slate-400 text-[10px] uppercase">
                    <th className="py-2 px-3">Milestone</th>
                    <th className="py-2 px-3">Time Horizon</th>
                    <th className="py-2 px-3">Unlocked Shares</th>
                    <th className="py-2 px-3">Cumulative Float (Cr)</th>
                    <th className="py-2 px-3">Event Description</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/60 text-slate-200">
                  {anchorCliff.cliff_schedule.map((item, idx) => (
                    <tr key={idx} className="hover:bg-slate-900/40">
                      <td className="py-2.5 px-3 font-semibold text-indigo-300">{item.milestone}</td>
                      <td className="py-2.5 px-3 text-slate-400">T+{item.days} Days</td>
                      <td className="py-2.5 px-3 text-amber-400 font-bold">{item.unlocked_shares.toLocaleString()}</td>
                      <td className="py-2.5 px-3 text-emerald-400">{item.cumulative_float_cr_shares} Cr</td>
                      <td className="py-2.5 px-3 text-slate-300 font-sans">{item.event}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            <p className="text-[11px] text-slate-400 pt-1">
              Institutional Guidance: <strong className="text-slate-300">{anchorCliff.institutional_absorption_capacity}</strong>
            </p>
          </div>
        )}
      </div>
    </div>
  );
};
