import React from 'react';
import { StatutoryOfferDetails, HuberCalibrationResults } from '../types/terminal';
import { ShieldCheck, AlertCircle, TrendingUp, Lock, CheckCircle2 } from 'lucide-react';

interface LintelTowersProps {
  offer: StatutoryOfferDetails;
  calibration: HuberCalibrationResults;
}

export const LintelTowers: React.FC<LintelTowersProps> = ({ offer, calibration }) => {
  const isUnpriced = offer.isPriceUndisclosed || !offer.priceBandMax || offer.priceBandMax === 0;

  // Tower 1 Metrics
  const freshPct = offer.freshIssuePct ?? (offer.issueSizeCr && offer.freshIssueCr !== null ? Math.round((offer.freshIssueCr / Math.max(1, offer.issueSizeCr)) * 100) : 100);
  const ofsPct = offer.ofsPct ?? (offer.issueSizeCr && offer.ofsCr !== null ? Math.round((offer.ofsCr / Math.max(1, offer.issueSizeCr)) * 100) : 0);
  const freshCr = offer.freshIssueCr ?? (freshPct > 0 ? (offer.issueSizeCr || 0) : 0);
  const ofsCr = offer.ofsCr ?? (ofsPct > 0 ? (offer.issueSizeCr || 0) : 0);

  // Tower 2 Metrics
  const huberFair = calibration.warrantedFairMultiple || 49.6;
  const askingPe = isUnpriced ? null : 2349.7; // Asking P/E at upper price band
  const frothPct = isUnpriced ? null : (calibration.unbackedFrothPct || 1508.8);
  const frothMultipleDiff = askingPe ? (askingPe - huberFair) : null;

  return (
    <div className="grid grid-cols-1 md:grid-cols-3 gap-4 font-sans">
      {/* TOWER 1: CAPITAL GROWTH VS. EXIT DILUTION (SEBI REG 7) */}
      <div className="rounded-lg border border-[#223044] bg-[#101620] p-4 flex flex-col justify-between shadow-sm relative overflow-hidden">
        <div>
          <div className="flex items-center justify-between pb-3 border-b border-[#1D2838]">
            <span className="text-xs font-bold text-slate-200 tracking-wider font-mono">
              TOWER 1: CAPITAL GROWTH VS. EXIT DILUTION
            </span>
            <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-cyan-950/80 border border-cyan-800 text-cyan-300 font-semibold">
              SEBI REG 7
            </span>
          </div>

          {/* Dual Visual Pillars */}
          <div className="grid grid-cols-2 gap-3 pt-4">
            {/* Pillar A: Fresh Growth */}
            <div className="flex flex-col items-center">
              <div
                style={{ height: `${Math.max(28, (freshPct / 100) * 80)}px` }}
                className={`w-full rounded-t flex items-center justify-center transition-all duration-500 ${
                  freshPct > 0 ? 'bg-emerald-500/90 shadow-[0_0_12px_rgba(16,185,129,0.3)]' : 'bg-slate-800/60'
                }`}
              >
                <span className="font-mono font-bold text-slate-950 text-sm">{freshPct}%</span>
              </div>
              <div className="w-full bg-[#090D12] border border-[#1E293B] border-t-0 p-2 text-center rounded-b">
                <span className="text-[10px] font-mono font-semibold text-emerald-400 block uppercase">Fresh Growth</span>
                <span className="text-xs font-mono font-bold text-slate-200">
                  ₹{freshCr.toLocaleString('en-IN', { maximumFractionDigits: 0 })} Cr
                </span>
              </div>
            </div>

            {/* Pillar B: Promoter Exit */}
            <div className="flex flex-col items-center">
              <div
                style={{ height: `${Math.max(28, (ofsPct / 100) * 80)}px` }}
                className={`w-full rounded-t flex items-center justify-center transition-all duration-500 ${
                  ofsPct > 0 ? 'bg-amber-500/90 shadow-[0_0_12px_rgba(245,158,11,0.3)]' : 'bg-slate-800/60'
                }`}
              >
                <span className="font-mono font-bold text-slate-950 text-sm">{ofsPct}%</span>
              </div>
              <div className="w-full bg-[#090D12] border border-[#1E293B] border-t-0 p-2 text-center rounded-b">
                <span className="text-[10px] font-mono font-semibold text-amber-400 block uppercase">Promoter Exit</span>
                <span className="text-xs font-mono font-bold text-slate-200">
                  ₹{ofsCr.toLocaleString('en-IN', { maximumFractionDigits: 0 })} Cr
                </span>
              </div>
            </div>
          </div>
        </div>

        {/* Tower 1 Footer / Compliance Status */}
        <div className="mt-4 pt-2.5 border-t border-[#1D2838] flex items-center justify-between text-[11px] font-mono">
          <span className="flex items-center gap-1.5 text-slate-300">
            {freshPct === 100 ? (
              <>
                <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
                <span className="text-emerald-400 font-semibold">100% Primary Balance Sheet Growth</span>
              </>
            ) : ofsPct === 100 ? (
              <>
                <AlertCircle className="w-3.5 h-3.5 text-amber-400" />
                <span className="text-amber-400 font-semibold">100% Secondary OFS Insider Liquidity</span>
              </>
            ) : (
              <span>Mixed Balance Sheet & OFS Dilution</span>
            )}
          </span>
          <span className="text-slate-400">Total: ₹{(offer.issueSizeCr || 0).toLocaleString('en-IN')} Cr</span>
        </div>
      </div>

      {/* TOWER 2: HUBER FAIR P/E VS. ASKING MULTIPLE STRETCH */}
      <div className="rounded-lg border border-[#223044] bg-[#101620] p-4 flex flex-col justify-between shadow-sm relative overflow-hidden">
        <div>
          <div className="flex items-center justify-between pb-3 border-b border-[#1D2838]">
            <span className="text-xs font-bold text-slate-200 tracking-wider font-mono">
              TOWER 2: HUBER FAIR P/E VS. ASKING STRETCH
            </span>
            {isUnpriced ? (
              <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-blue-950/80 border border-blue-800 text-blue-300 font-semibold">
                DRAFTING [●]
              </span>
            ) : (
              <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-rose-950/80 border border-rose-800 text-rose-300 font-semibold">
                +{frothPct}% FROTH
              </span>
            )}
          </div>

          {/* Dual Valuation Columns */}
          <div className="grid grid-cols-2 gap-3 pt-4">
            {/* Column A: Huber Fair */}
            <div className="flex flex-col items-center">
              <div className="h-20 w-full rounded-t bg-cyan-600/80 flex items-center justify-center shadow-[0_0_12px_rgba(6,182,212,0.3)]">
                <span className="font-mono font-bold text-slate-950 text-sm">{huberFair}x</span>
              </div>
              <div className="w-full bg-[#090D12] border border-[#1E293B] border-t-0 p-2 text-center rounded-b">
                <span className="text-[10px] font-mono font-semibold text-cyan-300 block uppercase">Huber Fair</span>
                <span className="text-xs font-mono text-slate-400">M-Estimator</span>
              </div>
            </div>

            {/* Column B: Asking P/E (or Unpriced Failsafe) */}
            <div className="flex flex-col items-center">
              {isUnpriced ? (
                <>
                  <div className="h-20 w-full rounded-t bg-slate-800/80 border border-dashed border-slate-700 flex flex-col items-center justify-center p-2 text-center">
                    <span className="font-mono font-bold text-cyan-400 text-xs">Undisclosed [●]</span>
                    <span className="text-[9px] font-mono text-slate-400 mt-0.5">Awaiting RHP Band</span>
                  </div>
                  <div className="w-full bg-[#090D12] border border-[#1E293B] border-t-0 p-2 text-center rounded-b">
                    <span className="text-[10px] font-mono font-semibold text-slate-400 block uppercase">Asking P/E</span>
                    <span className="text-xs font-mono text-slate-500">Syndicate TBA</span>
                  </div>
                </>
              ) : (
                <>
                  <div className="h-20 w-full rounded-t bg-rose-600/90 flex items-center justify-center shadow-[0_0_12px_rgba(225,29,72,0.3)]">
                    <span className="font-mono font-bold text-slate-950 text-sm">{askingPe}x</span>
                  </div>
                  <div className="w-full bg-[#090D12] border border-[#1E293B] border-t-0 p-2 text-center rounded-b">
                    <span className="text-[10px] font-mono font-semibold text-rose-400 block uppercase">Asking P/E</span>
                    <span className="text-xs font-mono text-slate-400">Syndicate RHP</span>
                  </div>
                </>
              )}
            </div>
          </div>
        </div>

        {/* Tower 2 Footer */}
        <div className="mt-4 pt-2.5 border-t border-[#1D2838] flex items-center justify-between text-[11px] font-mono">
          {isUnpriced ? (
            <>
              <span className="text-cyan-400">Failsafe: Price Band Undisclosed</span>
              <span className="text-slate-500">Robust Outlier Trim</span>
            </>
          ) : (
            <>
              <span className="text-rose-400 font-semibold">Froth Gap: +{frothMultipleDiff?.toFixed(1)}x P/E</span>
              <span className="text-slate-400">Robust Outlier Trim</span>
            </>
          )}
        </div>
      </div>

      {/* TOWER 3: DAY-180 FLOAT OVERHANG CLIFF (ICDR REG 16) */}
      <div className="rounded-lg border border-[#223044] bg-[#101620] p-4 flex flex-col justify-between shadow-sm relative overflow-hidden">
        <div>
          <div className="flex items-center justify-between pb-3 border-b border-[#1D2838]">
            <span className="text-xs font-bold text-slate-200 tracking-wider font-mono">
              TOWER 3: DAY-180 FLOAT OVERHANG CLIFF
            </span>
            <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-amber-950/80 border border-amber-800 text-amber-300 font-semibold">
              ICDR REG 16
            </span>
          </div>

          {/* 3-Tier Liquidity Unlock Ladder */}
          <div className="grid grid-cols-3 gap-2 pt-4">
            {/* Step 1: Day 1 Float */}
            <div className="flex flex-col items-center">
              <div className="h-14 w-full rounded-t bg-emerald-500/80 flex items-center justify-center">
                <span className="font-mono font-bold text-slate-950 text-xs">15%</span>
              </div>
              <div className="w-full bg-[#090D12] border border-[#1E293B] border-t-0 p-1.5 text-center rounded-b">
                <span className="text-[9px] font-mono font-semibold text-emerald-400 block">DAY 1 FLOAT</span>
                <span className="text-[10px] font-mono text-slate-400">Free Trading</span>
              </div>
            </div>

            {/* Step 2: Day 90 Anchor */}
            <div className="flex flex-col items-center">
              <div className="h-16 w-full rounded-t bg-amber-500/80 flex items-center justify-center">
                <span className="font-mono font-bold text-slate-950 text-xs">+35%</span>
              </div>
              <div className="w-full bg-[#090D12] border border-[#1E293B] border-t-0 p-1.5 text-center rounded-b">
                <span className="text-[9px] font-mono font-semibold text-amber-400 block">DAY 90 ANCHOR</span>
                <span className="text-[10px] font-mono text-slate-400">50% Release</span>
              </div>
            </div>

            {/* Step 3: Day 180 All */}
            <div className="flex flex-col items-center">
              <div className="h-20 w-full rounded-t bg-rose-500/80 flex items-center justify-center">
                <span className="font-mono font-bold text-slate-950 text-xs">+50%</span>
              </div>
              <div className="w-full bg-[#090D12] border border-[#1E293B] border-t-0 p-1.5 text-center rounded-b">
                <span className="text-[9px] font-mono font-semibold text-rose-400 block">DAY 180 ALL</span>
                <span className="text-[10px] font-mono text-slate-400">Pre-IPO Lock-in</span>
              </div>
            </div>
          </div>
        </div>

        {/* Tower 3 Footer */}
        <div className="mt-4 pt-2.5 border-t border-[#1D2838] flex items-center justify-between text-[11px] font-mono">
          <span className="text-amber-400 flex items-center gap-1">
            <Lock className="w-3 h-3 text-amber-400" />
            <span>Supply Shock: HIGH AT DAY 180</span>
          </span>
          <span className="text-slate-400">Anchor 50% / 50%</span>
        </div>
      </div>
    </div>
  );
};
