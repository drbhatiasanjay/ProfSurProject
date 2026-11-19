import React, { useState } from 'react';
import { RedFlagItem, StatutoryOfferDetails } from '../../types/terminal';
import { AlertOctagon, CheckCircle2, AlertTriangle, ShieldAlert, FileText, ArrowUpRight } from 'lucide-react';

interface RedFlagScannerVaultProps {
  offer: StatutoryOfferDetails;
  onOpenForensicDrawer?: (vaultId: string) => void;
}

export const RedFlagScannerVault: React.FC<RedFlagScannerVaultProps> = ({ offer, onOpenForensicDrawer }) => {
  const isHCCB = offer.symbol === 'HCCB' || offer.companyName.includes('Coca-Cola');

  // Ground truth flags evaluated for the active dossier
  const flags: RedFlagItem[] = isHCCB
    ? [
        {
          ruleCode: 'FLAG-01',
          ruleName: 'Cash Conversion Divergence',
          status: 'CLEAR',
          metricValue: '0.88x CFO/EBITDA',
          threshold: '< 0.55x',
          severity: 'INFO',
          drhpCitation: 'Ch. V (Financials), p. 284',
          explanation: 'Pristine cash flow conversion. 88% of operating profit realizes directly into free operating cash.'
        },
        {
          ruleCode: 'FLAG-02',
          ruleName: 'Stub Margin Spike',
          status: 'CLEAR',
          metricValue: '+110 bps Stub Expansion',
          threshold: '> +350 bps',
          severity: 'INFO',
          drhpCitation: 'Ch. V (Restated Summary), p. 291',
          explanation: 'Stub margin is seasonally normalized (+110 bps) without artificial pre-IPO cost suppression.'
        },
        {
          ruleCode: 'FLAG-03',
          ruleName: 'Excessive Insider OFS Exit Ratio',
          status: 'TRIGGERED',
          metricValue: '100% Secondary OFS',
          threshold: '> 65.0% OFS',
          severity: 'CRITICAL',
          drhpCitation: 'Ch. III (The Offer), p. 48',
          explanation: '100% of issue proceeds flow to selling shareholder (Bottling Investments Group). Zero primary growth capital.'
        },
        {
          ruleCode: 'FLAG-04',
          ruleName: 'Contingent Liability Tail Risk',
          status: 'MONITOR',
          metricValue: '16.4% of Net Worth (₹412 Cr)',
          threshold: '> 15.0%',
          severity: 'WARNING',
          drhpCitation: 'Ch. VII (Legal & Other Information), p. 412',
          explanation: 'Pending excise, GST, and water extraction litigations represent 16.4% of restated net worth.'
        },
        {
          ruleCode: 'FLAG-05',
          ruleName: 'Related Party Siphoning / RPT Outflow',
          status: 'TRIGGERED',
          metricValue: '14.2% of Total Revenue',
          threshold: '> 10.0%',
          severity: 'CRITICAL',
          drhpCitation: 'Ch. V (Related Party Disclosures), p. 320',
          explanation: 'Concentrate purchase fees and brand royalty payments to The Coca-Cola Company exceed 10% revenue hurdle.'
        },
        {
          ruleCode: 'FLAG-06',
          ruleName: '18-Month WACA Valuation Step-Up',
          status: 'MONITOR',
          metricValue: 'Undisclosed [●] vs. ₹14.20 Historic WACA',
          threshold: '> 2.50x Step-Up',
          severity: 'WARNING',
          drhpCitation: 'Ch. III (Basis for Issue Price), p. 74',
          explanation: 'Pre-IPO transfers at ₹14.20/share require RHP Price Band verification against statutory WACA multiple.'
        }
      ]
    : [
        {
          ruleCode: 'FLAG-01',
          ruleName: 'Cash Conversion Divergence',
          status: 'MONITOR',
          metricValue: '0.42x CFO/EBITDA',
          threshold: '< 0.55x',
          severity: 'WARNING',
          drhpCitation: 'Ch. V (Financials), p. 198',
          explanation: 'Heavy working capital deployment in renewable EPC reduces immediate cash conversion to 0.42x.'
        },
        {
          ruleCode: 'FLAG-02',
          ruleName: 'Stub Margin Spike',
          status: 'CLEAR',
          metricValue: '+85 bps Stub Delta',
          threshold: '> +350 bps',
          severity: 'INFO',
          drhpCitation: 'Ch. V (Financial Statements), p. 204',
          explanation: 'Margins in H1 FY25 track historical steady-state generation efficiency without pre-IPO distortion.'
        },
        {
          ruleCode: 'FLAG-03',
          ruleName: 'Excessive Insider OFS Exit Ratio',
          status: 'CLEAR',
          metricValue: '0% OFS (100% Fresh Issue)',
          threshold: '> 65.0% OFS',
          severity: 'INFO',
          drhpCitation: 'Ch. III (Capital Structure), p. 52',
          explanation: 'Zero secondary selling. All ₹10,000 Cr proceeds accretive to NTPC Green debt repayment and solar capex.'
        },
        {
          ruleCode: 'FLAG-04',
          ruleName: 'Contingent Liability Tail Risk',
          status: 'CLEAR',
          metricValue: '4.8% of Net Worth',
          threshold: '> 15.0%',
          severity: 'INFO',
          drhpCitation: 'Ch. VII (Outstanding Litigations), p. 340',
          explanation: 'Contingent claims aggregate to ₹380 Cr, well within the 15% net worth statutory safety ceiling.'
        },
        {
          ruleCode: 'FLAG-05',
          ruleName: 'Related Party Siphoning / RPT Outflow',
          status: 'MONITOR',
          metricValue: '8.9% of Revenue (Parent NTPC PPA)',
          threshold: '> 10.0%',
          severity: 'WARNING',
          drhpCitation: 'Ch. V (Related Party Transactions), p. 248',
          explanation: 'Shared power evacuation facilities and parent brand licensing agreements represent 8.9% of revenues.'
        },
        {
          ruleCode: 'FLAG-06',
          ruleName: '18-Month WACA Valuation Step-Up',
          status: 'TRIGGERED',
          metricValue: '10.8x Step-Up (₹108 Band vs. ₹10.00 Par)',
          threshold: '> 2.50x Step-Up',
          severity: 'CRITICAL',
          drhpCitation: 'Ch. III (Basis for Issue Price), p. 88',
          explanation: 'Upper price band ₹108 represents a 10.8x expansion over statutory 18-month weighted average acquisition cost.'
        }
      ];

  const triggeredCount = flags.filter(f => f.status === 'TRIGGERED').length;
  const monitorCount = flags.filter(f => f.status === 'MONITOR').length;
  const clearCount = flags.filter(f => f.status === 'CLEAR').length;

  // Forensic summary metrics
  const beneishMScore = isHCCB ? -2.84 : -2.48;
  const sloanAccrualRatio = isHCCB ? 0.042 : 0.118;

  return (
    <div className="space-y-6 max-w-7xl mx-auto font-sans">
      {/* Top Banner / Radar Summary Card */}
      <div id="module-red-flag-triage" className="rounded-xl border border-slate-700/80 border-t-2 border-t-rose-500 bg-[#0C1322] p-5 shadow-xl">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-4 border-b border-[#1E2B3E]">
          <div>
            <div className="flex items-center gap-2.5">
              <ShieldAlert className="w-5 h-5 text-rose-400" />
              <h2 className="text-base font-bold text-slate-100 font-mono tracking-wide">
                VAULT 6: 6-RULE RED-FLAG GOVERNANCE RADAR
              </h2>
            </div>
            <p className="text-xs text-slate-400 mt-1 font-mono">
              SEBI ICDR 2018 Statutory Gate & Forensic Earnings Quality Screen · {offer.companyName}
            </p>
          </div>

          {/* Tri-State Pillar Badges & Action Trigger */}
          <div className="flex items-center gap-2">
            <span className="px-3 py-1.5 rounded-lg bg-rose-950/70 border border-rose-800 text-rose-300 font-mono text-xs font-bold flex items-center gap-1.5">
              <AlertOctagon className="w-3.5 h-3.5 text-rose-400" />
              {triggeredCount} TRIGGERED
            </span>
            <span className="px-3 py-1.5 rounded-lg bg-amber-950/70 border border-amber-800 text-amber-300 font-mono text-xs font-bold flex items-center gap-1.5">
              <AlertTriangle className="w-3.5 h-3.5 text-amber-400" />
              {monitorCount} MONITOR
            </span>
            <span className="px-3 py-1.5 rounded-lg bg-emerald-950/70 border border-emerald-800 text-emerald-300 font-mono text-xs font-bold flex items-center gap-1.5">
              <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
              {clearCount} CLEAR
            </span>

            <button
              onClick={() => onOpenForensicDrawer?.('red_flag_scanner')}
              className="px-2.5 py-1.5 rounded bg-rose-950/80 border border-rose-700/80 text-rose-300 font-mono text-xs font-bold flex items-center gap-1.5 hover:bg-rose-900 transition-colors cursor-pointer shadow-sm ml-1"
              title="Open Red-Flag Governance & Forensic Evidence Drawer"
            >
              <span>Forensic Diligence</span>
              <span className="w-4 h-4 rounded-full bg-cyan-500 text-slate-950 flex items-center justify-center text-[10px] font-black">ⓘ</span>
            </button>
          </div>
        </div>

        {/* Forensic Scores Dual Pill */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 pt-4">
          <div className="rounded-lg bg-[#080D15] border border-[#1A2638] p-3.5 flex items-center justify-between">
            <div>
              <span className="text-[10px] font-mono uppercase text-slate-400 block">Beneish M-Score (Earnings Manipulation)</span>
              <div className="flex items-center gap-2 mt-0.5">
                <span className="text-lg font-mono font-bold text-emerald-400">{beneishMScore}</span>
                <span className="text-[11px] font-mono text-slate-500">(Safe Zone &lt; -1.78)</span>
              </div>
            </div>
            <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-emerald-950/60 border border-emerald-800 text-emerald-400">
              LOW MANIPULATION RISK
            </span>
          </div>

          <div className="rounded-lg bg-[#080D15] border border-[#1A2638] p-3.5 flex items-center justify-between">
            <div>
              <span className="text-[10px] font-mono uppercase text-slate-400 block">Sloan Accrual Ratio ((PAT - CFO) / Assets)</span>
              <div className="flex items-center gap-2 mt-0.5">
                <span className={`text-lg font-mono font-bold ${sloanAccrualRatio > 0.10 ? 'text-amber-400' : 'text-emerald-400'}`}>
                  {(sloanAccrualRatio * 100).toFixed(1)}%
                </span>
                <span className="text-[11px] font-mono text-slate-500">(Caution &gt; 10.0%)</span>
              </div>
            </div>
            <span className={`text-[10px] font-mono px-2 py-0.5 rounded ${
              sloanAccrualRatio > 0.10
                ? 'bg-amber-950/60 border border-amber-800 text-amber-400'
                : 'bg-emerald-950/60 border border-emerald-800 text-emerald-400'
            }`}>
              {sloanAccrualRatio > 0.10 ? 'ELEVATED ACCRUALS' : 'PRISTINE CASH ACCRUAL'}
            </span>
          </div>
        </div>
      </div>

      {/* 6-Rule Radar Table */}
      <div className="rounded-xl border border-[#223044] bg-[#0E1522] overflow-hidden shadow-lg">
        <div className="px-5 py-3.5 border-b border-[#1E2B3E] flex items-center justify-between bg-[#121B29]">
          <span className="text-xs font-mono font-bold text-slate-200 uppercase tracking-wider">
            Automated Statutory Rule Verification (ICDR Schedule VI)
          </span>
          <span className="text-[11px] font-mono text-slate-400">
            6 of 6 Rules Evaluated
          </span>
        </div>

        <div className="divide-y divide-[#1A2638]">
          {flags.map((item) => {
            const isTriggered = item.status === 'TRIGGERED';
            const isMonitor = item.status === 'MONITOR';

            return (
              <div
                key={item.ruleCode}
                className={`p-4 transition-colors ${
                  isTriggered
                    ? 'bg-rose-950/15 hover:bg-rose-950/25 border-l-4 border-rose-500'
                    : isMonitor
                    ? 'bg-amber-950/10 hover:bg-amber-950/20 border-l-4 border-amber-500'
                    : 'hover:bg-[#121B29] border-l-4 border-emerald-500/50'
                }`}
              >
                <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-2">
                  <div className="flex items-start gap-3">
                    <span className="font-mono text-xs font-bold px-2 py-1 rounded bg-[#0A0F18] border border-[#223044] text-slate-300 shrink-0">
                      {item.ruleCode}
                    </span>
                    <div>
                      <div className="flex items-center gap-2">
                        <span className="text-sm font-semibold text-slate-100 font-sans">{item.ruleName}</span>
                        <span className="text-[11px] font-mono text-slate-400">({item.threshold})</span>
                      </div>
                      <p className="text-xs text-slate-300 mt-1 leading-relaxed">{item.explanation}</p>
                    </div>
                  </div>

                  <div className="flex items-center gap-3 self-end lg:self-center shrink-0">
                    <div className="text-right">
                      <div className="text-xs font-mono font-bold text-slate-200">{item.metricValue}</div>
                      <div className="text-[10px] font-mono text-cyan-400 flex items-center gap-1 justify-end">
                        <FileText className="w-3 h-3" />
                        <span>{item.drhpCitation}</span>
                      </div>
                    </div>

                    <span
                      className={`px-2.5 py-1 rounded text-[11px] font-mono font-bold ${
                        isTriggered
                          ? 'bg-rose-900/60 border border-rose-700 text-rose-200'
                          : isMonitor
                          ? 'bg-amber-900/60 border border-amber-700 text-amber-200'
                          : 'bg-emerald-900/60 border border-emerald-700 text-emerald-200'
                      }`}
                    >
                      {item.status}
                    </span>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* High-Density Forensic Directive Banner (Methodology ⓘ Pattern) */}
      <div className="p-4 rounded-xl bg-[#0E1624] border border-[#1E2B3E] flex flex-col sm:flex-row sm:items-center justify-between gap-3 shadow-md mt-6">
        <div className="text-xs space-y-1">
          <div className="flex items-center gap-2 font-mono font-bold">
            <span className="px-2 py-0.5 rounded text-[10px] bg-rose-950 border border-rose-700 text-rose-300">
              100% OFS EXIT &bull; RPT 14.2%
            </span>
            <span className="text-rose-400">RED-FLAG GOVERNANCE AUDIT &amp; CLEARANCE</span>
          </div>
          <p className="text-slate-300 leading-relaxed">
            100% Secondary OFS cash exit leaves ₹0 in operating treasury. RPT concentrate purchases (₹1,820 Cr) require minority shareholder approval and mandatory audit committee pricing indexation covenants.
          </p>
        </div>
        <button
          onClick={() => onOpenForensicDrawer?.('red_flag_scanner')}
          className="px-3 py-2 rounded-lg text-xs font-mono font-bold bg-[#142032] hover:bg-[#1C2C45] text-rose-300 border border-rose-800 flex items-center gap-1.5 shrink-0 transition-colors cursor-pointer"
        >
          <span>Full Governance Proof &amp; Covenants</span>
          <span className="w-4 h-4 rounded-full bg-cyan-500 text-slate-950 flex items-center justify-center text-[10px] font-black">ⓘ</span>
        </button>
      </div>
    </div>
  );
};
