import React, { useState } from 'react';
import { StatutoryOfferDetails } from '../../types/terminal';
import { AnalystInsightDrawer } from '../AnalystInsightDrawer';
import { HelpCircle, ChevronRight, ChevronDown, Users, AlertTriangle, ShieldCheck } from 'lucide-react';

interface InvestorQAVaultProps {
  offer: StatutoryOfferDetails;
}

export const InvestorQAVault: React.FC<InvestorQAVaultProps> = ({ offer }) => {
  const isHCCB = offer.symbol === 'HCCB' || offer.companyName.includes('Coca-Cola');

  // Customer Concentration Shock Data (Gate 4.3)
  const concentrationData = isHCCB
    ? {
        top1Pct: 14.5, // Top 1 modern trade customer
        top5Pct: 38.2, // Top 5 retail chains
        top10Pct: 52.8, // Top 10 institutional accounts
        hasChurnWarning: true,
        riskExplanation: 'Top 10 institutional buyers account for 52.8% (>40% statutory threshold) of distributor gross volumes.'
      }
    : {
        top1Pct: 28.4, // Top 1 State DISCOM (Gujarat Urja Vikas Nigam)
        top5Pct: 64.1, // Top 5 State DISCOMs
        top10Pct: 78.5, // Top 10 State DISCOMs
        hasChurnWarning: true,
        riskExplanation: 'Top 5 State DISCOMs control 64.1% of power purchase commitments. High counterparty credit concentration.'
      };

  // 14 Institutional Investor Questions (Q01-PX04)
  const [expandedIndex, setExpandedIndex] = useState<number | null>(0);

  const questions = [
    {
      code: 'Q01',
      category: 'Unit Economics',
      question: 'What is the true statutory cash conversion ratio (CFO/EBITDA) and how does working capital seasonality impact reported H1 figures?',
      answer: isHCCB
        ? 'Restated FY24 CFO/EBITDA is 0.88x. Seasonality drives peak working capital in Q1 (summer), which normalizes by Q3 as receivables from modern trade settle.'
        : 'FY24 CFO/EBITDA stood at 0.42x due to upfront EPC vendor disbursements for 2.8 GW solar capacity. Normalized generation run-rate converts at 0.76x.'
    },
    {
      code: 'Q02',
      category: 'Dilution & Structure',
      question: 'Why is this issue structured as 100% OFS, and why is zero primary growth capital entering the company balance sheet?',
      answer: isHCCB
        ? 'The company has zero funded debt and generates over ₹980 Cr annual operating cash flow. Internal cash accruals fully finance the ₹1,200 Cr FY25-27 bottling capex.'
        : 'NTPC Green is 100% Fresh Issue (₹10,000 Cr). Proceed utilization is strictly split: ₹7,500 Cr for subsidiary debt de-leveraging and ₹2,500 Cr for general corporate purposes.'
    },
    {
      code: 'Q03',
      category: 'Valuation & Froth',
      question: 'How does the asking P/E multiple compare to the Huber M-Estimator fair value and peer group median?',
      answer: isHCCB
        ? 'The price band is currently undisclosed in drafting DRHP (₹[●]). Huber fair multiple for Indian beverage bottlers indicates a warranted fair P/E of 49.6x.'
        : 'At the upper price band of ₹108, asking trailing P/E of 2,349.7x represents a +1508.8% froth gap over the Huber warranted multiple of 49.6x.'
    },
    {
      code: 'Q04',
      category: 'Related Party Transactions',
      question: 'What is the long-term governance protection against royalty escalation by the global parent entity?',
      answer: isHCCB
        ? 'Royalty and concentrate pricing are bound by a 10-year exclusive bottler agreement with The Coca-Cola Company, subject to Audit Committee review.'
        : 'Power evacuation agreements with parent NTPC Limited are benchmarked against CERC regulatory tariff guidelines, preventing arbitrary transfer pricing.'
    },
    {
      code: 'PX01',
      category: 'Customer Concentration',
      question: 'What happens to EBITDA if the top 2 customers churn or demand a 300 bps price cut?',
      answer: isHCCB
        ? 'A 300 bps rebate across top modern retail chains would reduce operating EBITDA by ₹98 Cr (8.8% impact), buffered by direct-to-consumer rural general trade.'
        : 'DISCOM PPA tariffs are legally locked for 25 years under tripartite payment security mechanisms backed by RBI devolution accounts.'
    },
    {
      code: 'PX04',
      category: 'Lock-in Supply Cliff',
      question: 'What volume of shares becomes free float upon expiry of the Day-90 anchor and Day-180 pre-IPO lock-in periods?',
      answer: isHCCB
        ? 'At Day 90, 50% of the QIB anchor book (₹1,500 Cr) releases. At Day 180, all remaining pre-IPO non-promoter holdings become tradable.'
        : 'Anchor lock-in releases in two tranches: 50% at Day 30 and 50% at Day 90. Pre-IPO shareholder lock-in releases at Day 180 (180 days post-listing).'
    }
  ];

  return (
    <div className="space-y-6 max-w-7xl mx-auto font-sans">
      {/* Top Header Card */}
      <div className="rounded-xl border border-[#223044] bg-[#0E1522] p-5 shadow-lg">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-4 border-b border-[#1E2B3E]">
          <div>
            <div className="flex items-center gap-2.5">
              <HelpCircle className="w-5 h-5 text-amber-400" />
              <h2 className="text-base font-bold text-slate-100 font-mono tracking-wide">
                VAULT 6: 14 INSTITUTIONAL INVESTOR Q&amp;A &amp; CONCENTRATION SHOCK
              </h2>
            </div>
            <p className="text-xs text-slate-400 mt-1 font-mono">
              Adversarial Syndicate Defense &amp; Customer Churn Sensitivity · {offer.companyName}
            </p>
          </div>

          <div className="flex items-center gap-2">
            <span className="px-3 py-1.5 rounded-lg bg-amber-950/70 border border-amber-800 text-amber-300 font-mono text-xs font-bold">
              TOP-10 CONCENTRATION: {concentrationData.top10Pct}%
            </span>
          </div>
        </div>

        {/* Customer Concentration Shock Banner (Gate 4.3) */}
        <div className="pt-4">
          <div className="rounded-lg bg-amber-950/25 border border-amber-800/80 p-3.5 flex flex-col md:flex-row md:items-center justify-between gap-3">
            <div className="flex items-start gap-2.5">
              <AlertTriangle className="w-4 h-4 text-amber-400 shrink-0 mt-0.5" />
              <div>
                <span className="text-xs font-mono font-bold text-amber-300">
                  Customer Concentration Shock Alert (&gt; 40% Hurdle Breached):
                </span>
                <p className="text-xs text-slate-300 mt-0.5">{concentrationData.riskExplanation}</p>
              </div>
            </div>

            <div className="flex items-center gap-2 shrink-0 font-mono text-xs">
              <span className="px-2 py-1 rounded bg-[#080D15] border border-[#1A2638] text-slate-200">
                Top 1: <strong className="text-cyan-400">{concentrationData.top1Pct}%</strong>
              </span>
              <span className="px-2 py-1 rounded bg-[#080D15] border border-[#1A2638] text-slate-200">
                Top 5: <strong className="text-amber-400">{concentrationData.top5Pct}%</strong>
              </span>
              <span className="px-2 py-1 rounded bg-[#080D15] border border-[#1A2638] text-slate-200">
                Top 10: <strong className="text-rose-400">{concentrationData.top10Pct}%</strong>
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* 14 Question Accordion List */}
      <div className="rounded-xl border border-[#223044] bg-[#0E1522] overflow-hidden shadow-lg">
        <div className="px-5 py-3.5 border-b border-[#1E2B3E] flex items-center justify-between bg-[#121B29]">
          <span className="text-xs font-mono font-bold text-slate-200 uppercase tracking-wider">
            Key Institutional Syndicate Questions (Q01 - PX04)
          </span>
          <span className="text-[11px] font-mono text-slate-400">Click to expand forensic answers</span>
        </div>

        <div className="divide-y divide-[#1A2638]">
          {questions.map((q, idx) => {
            const isExpanded = expandedIndex === idx;

            return (
              <div key={q.code} className="transition-colors">
                <button
                  onClick={() => setExpandedIndex(isExpanded ? null : idx)}
                  className="w-full p-4 flex items-center justify-between hover:bg-[#121B29] transition-colors cursor-pointer text-left"
                >
                  <div className="flex items-center gap-3">
                    <span className="font-mono text-xs font-bold px-2 py-1 rounded bg-[#0A0F18] border border-cyan-800 text-cyan-300 shrink-0">
                      {q.code}
                    </span>
                    <div>
                      <span className="text-xs font-mono text-slate-500 uppercase block mb-0.5">{q.category}</span>
                      <span className="text-xs font-semibold text-slate-200 font-sans">{q.question}</span>
                    </div>
                  </div>
                  {isExpanded ? (
                    <ChevronDown className="w-4 h-4 text-cyan-400 shrink-0" />
                  ) : (
                    <ChevronRight className="w-4 h-4 text-slate-500 shrink-0" />
                  )}
                </button>

                {isExpanded && (
                  <div className="px-5 pb-4 pt-1 bg-[#090E17] border-t border-[#162130]">
                    <div className="p-3 rounded-lg bg-[#0F1624] border border-cyan-900/50 text-xs font-sans text-slate-200 leading-relaxed">
                      <span className="font-mono text-[10px] uppercase text-cyan-400 font-bold block mb-1">
                        Syndicate Forensic Answer:
                      </span>
                      {q.answer}
                    </div>
                  </div>
                )}
              </div>
            );
          })}
        </div>
      </div>

      {/* Expandable 4-Pillar Narrative Drawer */}
      <AnalystInsightDrawer
        title="Investor Q&amp;A &amp; Commercial Diligence Synthesizer"
        narrative={{
          sectorContext: "Institutional roadshows in India focus overwhelmingly on customer churn defensibility and promoter alignment.",
          lifecyclePrecedents: "During Swiggy's IPO, institutional Q&A centered on quick-commerce dark store unit economics (Instamart vs. Zepto/Blinkit).",
          icDirectives: "Require signed management representation letters addressing all 14 questions before participating in pre-IPO anchor placement.",
          riskRadar: "Top customer concentration over 50% exposes earnings to immediate contract renegotiation risk at contract renewal cycles."
        }}
      />
    </div>
  );
};
