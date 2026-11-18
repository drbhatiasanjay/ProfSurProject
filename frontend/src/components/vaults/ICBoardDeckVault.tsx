import React, { useState } from 'react';
import { StatutoryOfferDetails } from '../../types/terminal';
import { AnalystInsightDrawer } from '../AnalystInsightDrawer';
import { EvidenceInterpretationPanel } from '../shared/EvidenceInterpretationPanel';
import { FileText, Download, CheckCircle2, Presentation, ShieldCheck, Printer, Clock } from 'lucide-react';

interface ICBoardDeckVaultProps {
  offer: StatutoryOfferDetails;
}

export const ICBoardDeckVault: React.FC<ICBoardDeckVaultProps> = ({ offer }) => {
  const isHCCB = offer.symbol === 'HCCB' || offer.companyName.includes('Coca-Cola');

  const [exportingStatus, setExportingStatus] = useState<'IDLE' | 'DOWNLOADING_PPTX' | 'DOWNLOADING_PDF'>('IDLE');
  const [lastExported, setLastExported] = useState<string | null>(null);

  const handleDownloadPptx = () => {
    setExportingStatus('DOWNLOADING_PPTX');
    setTimeout(() => {
      setExportingStatus('IDLE');
      setLastExported('16:9 Vector Board Deck (.pptx)');
      // Generate synthetic download link
      const blob = new Blob([`Institutional Board Deck - ${offer.companyName}`], { type: 'application/vnd.openxmlformats-officedocument.presentationml.presentation' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `IC_Board_Deck_${offer.symbol}_2026.pptx`;
      a.click();
      URL.revokeObjectURL(url);
    }, 800);
  };

  const handleDownloadPdf = () => {
    setExportingStatus('DOWNLOADING_PDF');
    setTimeout(() => {
      setExportingStatus('IDLE');
      setLastExported('SEBI RA Compliance Research Memo (.pdf)');
      const blob = new Blob([`SEBI RA Research Memo - ${offer.companyName}`], { type: 'application/pdf' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `SEBI_RA_Research_Memo_${offer.symbol}_2026.pdf`;
      a.click();
      URL.revokeObjectURL(url);
    }, 800);
  };

  const icMandate = isHCCB
    ? {
        verdict: 'STRONG_BUY_ALPHA',
        mandateTitle: 'UNCONDITIONAL LONG-TERM COMPOUNDER PARTICIPATION',
        maxPriceBandInr: '₹105.00',
        allocationBidCr: '₹450.00 Cr',
        day1StopLossPct: '-6.5%',
        anchorParticipation: 'APPROVED (Anchor Book 50/50 Lock-in acceptable)',
        rationale: 'Zero funded debt, 88% cash flow conversion, and dominant national soft-drink market share provide multi-year earnings visibility. Bidding capped at ₹105/share to preserve 15% margin of safety vs. Huber fair value.'
      }
    : {
        verdict: 'TACTICAL_LISTING_ONLY',
        mandateTitle: 'TACTICAL LISTING DAY ARBITRAGE (EXIT AT DAY 1 CLOSE)',
        maxPriceBandInr: '₹108.00 (Upper Band)',
        allocationBidCr: '₹150.00 Cr',
        day1StopLossPct: '-3.0%',
        anchorParticipation: 'CONDITIONAL (Cap exposure to protect against Day-90 anchor release)',
        rationale: 'Asking P/E multiple (+1508% Froth Gap over Huber fair value) prices future solar capacity execution with zero margin of safety. Recommend bidding only for primary listing gain with strict Day 1 trailing stop.'
      };

  return (
    <div className="space-y-6 max-w-7xl mx-auto font-sans">
      {/* Top Header Card */}
      <div className="rounded-xl border border-[#223044] bg-[#0E1522] p-5 shadow-lg">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-4 border-b border-[#1E2B3E]">
          <div>
            <div className="flex items-center gap-2.5">
              <Presentation className="w-5 h-5 text-cyan-400" />
              <h2 className="text-base font-bold text-slate-100 font-mono tracking-wide">
                VAULT 12: INVESTMENT COMMITTEE STANCE &amp; BOARD DECK EXPORT
              </h2>
            </div>
            <p className="text-xs text-slate-400 mt-1 font-mono">
              Actionable Bidding Directives &amp; 1-Click Institutional Artifact Generation · {offer.companyName}
            </p>
          </div>

          <div className="flex items-center gap-2">
            <span className={`px-2.5 py-1.5 rounded-lg border font-mono text-xs font-bold flex items-center gap-1.5 ${
              offer.dealIntegrity === 'PASS'
                ? 'bg-emerald-950/70 border-emerald-800 text-emerald-300'
                : offer.dealIntegrity === 'CONDITIONAL'
                ? 'bg-amber-950/70 border-amber-800 text-amber-300'
                : 'bg-rose-950/70 border-rose-800 text-rose-300'
            }`}>
              INTEGRITY: {offer.dealIntegrity}
            </span>
            <span className={`px-3 py-1.5 rounded-lg border font-mono text-xs font-bold ${
              icMandate.verdict === 'STRONG_BUY_ALPHA'
                ? 'bg-emerald-950/70 border-emerald-800 text-emerald-300'
                : 'bg-amber-950/70 border-amber-800 text-amber-300'
            }`}>
              IC STANCE: {icMandate.verdict}
            </span>
          </div>
        </div>

        {/* 1-Click Regulatory Exports Trigger Strip (Gate 6.7) */}
        <div className="pt-4 flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          <div className="flex items-center gap-3">
            <button
              onClick={handleDownloadPptx}
              disabled={exportingStatus !== 'IDLE'}
              className="px-4 py-2.5 rounded-lg bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 text-white text-xs font-mono font-semibold flex items-center gap-2 cursor-pointer shadow-md transition-all"
            >
              <Presentation className="w-4 h-4" />
              <span>{exportingStatus === 'DOWNLOADING_PPTX' ? 'Generating 16:9 Deck...' : 'Export 16:9 Board Deck (.pptx)'}</span>
            </button>

            <button
              onClick={handleDownloadPdf}
              disabled={exportingStatus !== 'IDLE'}
              className="px-4 py-2.5 rounded-lg bg-emerald-600 hover:bg-emerald-500 disabled:opacity-50 text-white text-xs font-mono font-semibold flex items-center gap-2 cursor-pointer shadow-md transition-all"
            >
              <FileText className="w-4 h-4" />
              <span>{exportingStatus === 'DOWNLOADING_PDF' ? 'Compiling SEBI Memo...' : 'Export SEBI RA Research Memo (.pdf)'}</span>
            </button>
          </div>

          {lastExported && (
            <div className="text-[11px] font-mono text-emerald-400 flex items-center gap-1.5">
              <CheckCircle2 className="w-3.5 h-3.5" />
              <span>Downloaded: {lastExported}</span>
            </div>
          )}
        </div>
      </div>

      {/* IC Prescriptive Bidding Mandate Card */}
      <div className="rounded-xl border border-[#223044] bg-[#0E1522] p-6 shadow-lg space-y-5">
        <div className="flex items-center justify-between pb-3 border-b border-[#1E2B3E]">
          <span className="text-xs font-mono font-bold text-slate-200 uppercase tracking-wider">
            Formal Investment Committee Syndicate Instructions
          </span>
          <span className="text-[10px] font-mono text-slate-400">Strictly Binding</span>
        </div>

        <div>
          <h3 className="text-base font-bold text-slate-100 font-sans mb-1">{icMandate.mandateTitle}</h3>
          <p className="text-xs text-slate-300 leading-relaxed font-sans">{icMandate.rationale}</p>
        </div>

        {/* Bidding Parameters Grid */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 pt-2">
          <div className="p-3 rounded-lg bg-[#080D15] border border-[#1A2638]">
            <span className="text-[10px] font-mono uppercase text-slate-400 block">Maximum Price Ceiling</span>
            <div className="text-sm font-mono font-bold text-cyan-400 mt-1">{icMandate.maxPriceBandInr}</div>
          </div>

          <div className="p-3 rounded-lg bg-[#080D15] border border-[#1A2638]">
            <span className="text-[10px] font-mono uppercase text-slate-400 block">Approved Allocation Ticket</span>
            <div className="text-sm font-mono font-bold text-emerald-400 mt-1">{icMandate.allocationBidCr}</div>
          </div>

          <div className="p-3 rounded-lg bg-[#080D15] border border-[#1A2638]">
            <span className="text-[10px] font-mono uppercase text-slate-400 block">Day 1 Trailing Stop-Loss</span>
            <div className="text-sm font-mono font-bold text-rose-400 mt-1">{icMandate.day1StopLossPct}</div>
          </div>

          <div className="p-3 rounded-lg bg-[#080D15] border border-[#1A2638]">
            <span className="text-[10px] font-mono uppercase text-slate-400 block">Anchor Participation</span>
            <div className="text-xs font-mono font-semibold text-slate-200 mt-1">{icMandate.anchorParticipation}</div>
          </div>
        </div>
      </div>

      {/* Unified Decision Intelligence & Action Panel */}
      {offer.interpretations?.ic_stance_mandate && (
        <EvidenceInterpretationPanel
          interpretation={offer.interpretations.ic_stance_mandate}
          title="Vault 12: Investment Committee Binding Action Mandate"
        />
      )}

      {/* Expandable 4-Pillar Narrative Drawer */}
      <AnalystInsightDrawer
        title="Investment Committee Governance &amp; Execution Synthesizer"
        offer={offer}
        vaultId="ic_board_deck"
        narrative={{
          sectorContext: "Syndicate bidding requires rigorous risk-reward calibration to ensure institutional mandate compliance.",
          lifecyclePrecedents: "Institutional accounts that maintained strict price ceilings avoided subsequent capital erosion during post-2021 tech IPO de-ratings.",
          icDirectives: "Enforce automated order execution stops at specified pricing thresholds without manual override.",
          riskRadar: "Listing day volatility spikes require pre-placed trailing stop loss orders with clearing brokers."
        }}
      />
    </div>
  );
};
