import React, { useState } from 'react';
import { StatutoryOfferDetails } from '../../types/terminal';
import { Layers, Activity, AlertTriangle, ShieldCheck, ArrowDownRight } from 'lucide-react';

interface StressWorkpapersVaultProps {
  offer: StatutoryOfferDetails;
}

export const StressWorkpapersVault: React.FC<StressWorkpapersVaultProps> = ({ offer }) => {
  const isHCCB = offer.symbol === 'HCCB' || offer.companyName.includes('Coca-Cola');

  // Interactive 5x5 Stress Grid: Volume Growth Delta (-10% to +10%) vs. Input Raw Material Cost (+0% to +20%)
  const [selectedCell, setSelectedCell] = useState<{ volumeIdx: number; costIdx: number } | null>({ volumeIdx: 2, costIdx: 2 });

  const volumeDeltas = [-10, -5, 0, +5, +10]; // %
  const rawMaterialShocks = [0, +5, +10, +15, +20]; // %

  // Base EBITDA Margin
  const baseMargin = isHCCB ? 13.8 : 82.4;

  // Calculate grid value
  const calculateMargin = (volDelta: number, costShock: number) => {
    // Volume delta impacts operating leverage by 0.35x
    // Cost shock impacts gross margin by 0.55x
    const margin = baseMargin + (volDelta * 0.35) - (costShock * 0.55);
    return Math.max(0, margin);
  };

  return (
    <div className="space-y-6 max-w-7xl mx-auto font-sans">
      {/* Top Header Card */}
      <div className="rounded-xl border border-[#223044] bg-[#0E1522] p-5 shadow-lg">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-4 border-b border-[#1E2B3E]">
          <div>
            <div className="flex items-center gap-2.5">
              <Layers className="w-5 h-5 text-indigo-400" />
              <h2 className="text-base font-bold text-slate-100 font-mono tracking-wide">
                VAULT 5: 2D STRESS WORKPAPERS & FORENSIC LIQUIDITY LADDER
              </h2>
            </div>
            <p className="text-xs text-slate-400 mt-1 font-mono">
              Bivariate Sensitivity Matrix & Debt Servicing Headroom · {offer.companyName}
            </p>
          </div>

          <div className="flex items-center gap-2">
            <span className="px-3 py-1.5 rounded-lg bg-indigo-950/70 border border-indigo-800 text-indigo-300 font-mono text-xs font-bold">
              BASE EBITDA: {baseMargin.toFixed(1)}%
            </span>
          </div>
        </div>

        {/* 2D 5x5 Sensitivity Grid */}
        <div className="pt-4 overflow-x-auto">
          <span className="text-[10px] font-mono text-slate-400 uppercase tracking-wider block mb-2 font-bold">
            2D Bivariate Matrix: Volume Growth Shock vs. Input Raw Material Inflation (Post-Stress EBITDA Margin %)
          </span>

          <table className="w-full text-xs font-mono border-collapse">
            <thead>
              <tr className="border-b border-[#1E2B3E]">
                <th className="p-2 text-left text-slate-400 font-normal">Vol \ Cost Shock</th>
                {rawMaterialShocks.map((c) => (
                  <th key={c} className="p-2 text-center text-slate-300 font-semibold bg-[#121B29]">
                    +{c}% Cost
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {volumeDeltas.map((v, vIdx) => (
                <tr key={v} className="border-b border-[#162130]">
                  <td className="p-2 font-semibold text-slate-300 bg-[#121B29]">
                    {v >= 0 ? `+${v}%` : `${v}%`} Vol
                  </td>
                  {rawMaterialShocks.map((c, cIdx) => {
                    const stressedMargin = calculateMargin(v, c);
                    const isSelected = selectedCell?.volumeIdx === vIdx && selectedCell?.costIdx === cIdx;
                    const isSevere = stressedMargin < (baseMargin * 0.7);

                    return (
                      <td
                        key={c}
                        onClick={() => setSelectedCell({ volumeIdx: vIdx, costIdx: cIdx })}
                        className={`p-2.5 text-center cursor-pointer transition-all ${
                          isSelected
                            ? 'bg-cyan-500/30 border-2 border-cyan-400 font-bold text-cyan-200'
                            : isSevere
                            ? 'bg-rose-950/40 text-rose-300 hover:bg-rose-900/50'
                            : 'hover:bg-[#152030] text-slate-200'
                        }`}
                      >
                        {stressedMargin.toFixed(1)}%
                      </td>
                    );
                  })}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Debt Maturity & Liquidity Headroom Strip */}
      <div className="rounded-xl border border-[#223044] bg-[#0E1522] p-5 shadow-lg space-y-4">
        <div className="flex items-center justify-between pb-3 border-b border-[#1E2B3E]">
          <span className="text-xs font-mono font-bold text-slate-200 uppercase tracking-wider flex items-center gap-1.5">
            <Activity className="w-4 h-4 text-emerald-400" />
            Funded Debt Amortization Schedule & Covenant Headroom
          </span>
          <span className="text-[10px] font-mono text-emerald-400">SEBI Reg 16 Headroom</span>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div className="p-3.5 rounded-lg bg-[#080D15] border border-[#1A2638]">
            <span className="text-[10px] font-mono uppercase text-slate-400 block">FY25E Debt Due</span>
            <div className="text-lg font-mono font-bold text-slate-100 mt-0.5">
              {isHCCB ? '₹0.00 Cr' : '₹1,240.00 Cr'}
            </div>
            <span className="text-[10px] font-mono text-emerald-400 mt-1 block">
              {isHCCB ? 'Zero Bank Borrowings' : 'Pre-paid via Issue Proceeds'}
            </span>
          </div>

          <div className="p-3.5 rounded-lg bg-[#080D15] border border-[#1A2638]">
            <span className="text-[10px] font-mono uppercase text-slate-400 block">FY26E Debt Due</span>
            <div className="text-lg font-mono font-bold text-slate-100 mt-0.5">
              {isHCCB ? '₹0.00 Cr' : '₹2,100.00 Cr'}
            </div>
            <span className="text-[10px] font-mono text-emerald-400 mt-1 block">
              {isHCCB ? 'Zero Amortization' : 'Fully Covered by Internal Accruals'}
            </span>
          </div>

          <div className="p-3.5 rounded-lg bg-[#080D15] border border-[#1A2638]">
            <span className="text-[10px] font-mono uppercase text-slate-400 block">FY27E Debt Due</span>
            <div className="text-lg font-mono font-bold text-slate-100 mt-0.5">
              {isHCCB ? '₹0.00 Cr' : '₹3,450.00 Cr'}
            </div>
            <span className="text-[10px] font-mono text-cyan-400 mt-1 block">
              {isHCCB ? 'No Maturity Wall' : 'Solar Project Phase II Escrow'}
            </span>
          </div>

          <div className="p-3.5 rounded-lg bg-[#080D15] border border-[#1A2638]">
            <span className="text-[10px] font-mono uppercase text-slate-400 block">Covenant ICR Floor</span>
            <div className="text-lg font-mono font-bold text-emerald-400 mt-0.5">
              {isHCCB ? 'N/A (Net Cash)' : '3.85x (Covenant: 1.75x)'}
            </div>
            <span className="text-[10px] font-mono text-emerald-400 mt-1 block">
              +210 bps Covenant Buffer
            </span>
          </div>
        </div>
      </div>

      {/* High-density Directive Banner */}
      <div className="rounded-lg border border-cyan-900/50 bg-[#070e17] p-4 flex flex-col md:flex-row items-start md:items-center justify-between gap-4 shadow-sm">
        <div className="space-y-1">
          <div className="flex items-center gap-2">
            <span className="px-2 py-0.5 rounded text-[10px] font-mono font-bold bg-cyan-950/80 text-cyan-300 border border-cyan-800">
              STRESS BUFFER: +210 BPS
            </span>
            <span className="text-xs font-mono font-bold text-slate-200">
              2D STRESS RESILIENCE &amp; BALANCE SHEET BUFFER
            </span>
          </div>
          <p className="text-xs text-slate-400 font-mono leading-relaxed">
            Commodity pass-through mechanisms mitigate shocks with a 1-quarter lag. Debt covenants withstand severe 20% input cost inflation with minimum 2.0x ICR coverage.
          </p>
        </div>
      </div>
    </div>
  );
};
