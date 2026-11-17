import React, { useState } from 'react';
import { StatutoryOfferDetails } from '../../types/terminal';
import { AnalystInsightDrawer } from '../AnalystInsightDrawer';
import { EvidenceInterpretationPanel } from '../shared/EvidenceInterpretationPanel';
import { Users, Briefcase, Landmark, TrendingUp, ShieldCheck, UserCheck, AlertCircle } from 'lucide-react';

interface StakeholderLensVaultProps {
  offer: StatutoryOfferDetails;
}

type PersonaKey = 'cfo' | 'lender' | 'qib' | 'retail' | 'sebi_ra' | 'board';

export const StakeholderLensVault: React.FC<StakeholderLensVaultProps> = ({ offer }) => {
  const isHCCB = offer.symbol === 'HCCB' || offer.companyName.includes('Coca-Cola');
  const [activePersona, setActivePersona] = useState<PersonaKey>('cfo');

  const personas = [
    {
      key: 'cfo' as PersonaKey,
      title: 'Chief Financial Officer',
      icon: Briefcase,
      badge: 'Capital Structure',
      verdict: isHCCB ? 'CAPITAL SUFFICIENCY EXCELLENT' : 'DEBT PRE-PAYMENT CRITICAL',
      focus: isHCCB
        ? 'Zero debt structure provides unencumbered balance sheet flexibility. Working capital optimization during summer peak protects operating return on equity.'
        : 'All ₹10,000 Cr fresh capital must be applied to de-lever subsidiary NREL debt, immediately unlocking ₹780 Cr in annual interest savings.'
    },
    {
      key: 'lender' as PersonaKey,
      title: 'Credit Rating & Debt Lender',
      icon: Landmark,
      badge: 'Solvency & ICR',
      verdict: isHCCB ? 'AAA RATING SAFE' : 'COVENANT BUFFER EXPANDING',
      focus: isHCCB
        ? 'Debt-free capital structure. Negative net debt (-₹1,420 Cr cash equivalents). Zero insolvency risk under any tested macroeconomic shock.'
        : 'Post-issue ICR expands from 1.82x to 3.85x, well clear of the 1.75x covenant default threshold.'
    },
    {
      key: 'qib' as PersonaKey,
      title: 'QIB Public Equity Lead',
      icon: TrendingUp,
      badge: 'Multiple Expansion',
      verdict: isHCCB ? 'MONITOR RHP PRICING' : 'HIGH VALUATION FROTH (+1508%)',
      focus: isHCCB
        ? 'Awaiting RHP price band announcement. Fair value of 49.6x Huber multiple warrants bidding up to ₹105/share for compound compounding thesis.'
        : 'Upper price band of ₹108 prices the company to perfection (2,349x P/E). Recommend tactical listing gain participation only with strict trailing stop.'
    },
    {
      key: 'retail' as PersonaKey,
      title: 'Retail HNI Investor',
      icon: Users,
      badge: 'Listing Gain Safety',
      verdict: isHCCB ? 'SAFE HOUSEHOLD BRAND' : 'GREY MARKET DEPENDENT',
      focus: isHCCB
        ? 'High consumer brand recall. Minimum commitment lot provides defensive consumer FMCG exposure with stable dividend payout expectations.'
        : 'Large issue size (₹10,000 Cr) requires strong institutional anchor backing to prevent listing day supply digestion overhang.'
    },
    {
      key: 'sebi_ra' as PersonaKey,
      title: 'SEBI Research Analyst',
      icon: ShieldCheck,
      badge: 'Regulatory Audit',
      verdict: 'ICDR COMPLIANT',
      focus: isHCCB
        ? 'Regulation 6(2) compliance satisfied via 75% QIB allocation route. Mandatory disclosure of 100% OFS selling entity European Refreshments UC.'
        : 'Regulation 6(2) book building confirmed. General Corporate Purposes strictly capped at ₹2,500 Cr (&le; 25.0% statutory threshold).'
    },
    {
      key: 'board' as PersonaKey,
      title: 'Board Audit Committee',
      icon: UserCheck,
      badge: 'Governance & RPT',
      verdict: isHCCB ? 'SUPERMAJORITY RPT VOTE' : 'CLEAR GOVERNANCE SLATE',
      focus: isHCCB
        ? '14.2% of revenues flow to parent entity in brand and concentrate royalties. Requires ongoing quarterly Audit Committee independent fairness certifications.'
        : 'Parent NTPC power evacuation and shared infrastructure agreements comply with arm’s-length CERC pricing regulations.'
    }
  ];

  const currentPersona = personas.find(p => p.key === activePersona) || personas[0];

  return (
    <div className="space-y-6 max-w-7xl mx-auto font-sans">
      {/* Top Header Card */}
      <div className="rounded-xl border border-[#223044] bg-[#0E1522] p-5 shadow-lg">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-4 border-b border-[#1E2B3E]">
          <div>
            <div className="flex items-center gap-2.5">
              <Users className="w-5 h-5 text-indigo-400" />
              <h2 className="text-base font-bold text-slate-100 font-mono tracking-wide">
                VAULT 7: 6-PERSONA STAKEHOLDER LENS
              </h2>
            </div>
            <p className="text-xs text-slate-400 mt-1 font-mono">
              Multi-Constituency Decision Framework &amp; Mandate Alignment · {offer.companyName}
            </p>
          </div>

          <div className="flex items-center gap-2">
            <span className="px-3 py-1.5 rounded-lg bg-indigo-950/70 border border-indigo-800 text-indigo-300 font-mono text-xs font-bold">
              6 PERSONAS READY
            </span>
          </div>
        </div>

        {/* Persona Selector Tabs */}
        <div className="grid grid-cols-2 md:grid-cols-6 gap-2 pt-4">
          {personas.map((p) => {
            const Icon = p.icon;
            const isSelected = activePersona === p.key;

            return (
              <button
                key={p.key}
                onClick={() => setActivePersona(p.key)}
                className={`p-3 rounded-lg border flex flex-col items-center justify-center text-center transition-all cursor-pointer ${
                  isSelected
                    ? 'bg-cyan-950/80 border-cyan-400 text-cyan-200 shadow-md shadow-cyan-950/50'
                    : 'bg-[#080D15] border-[#1A2638] text-slate-400 hover:text-slate-200 hover:bg-[#121B29]'
                }`}
              >
                <Icon className={`w-4 h-4 mb-1.5 ${isSelected ? 'text-cyan-400' : 'text-slate-500'}`} />
                <span className="text-xs font-semibold font-sans">{p.title}</span>
                <span className="text-[9px] font-mono text-slate-500 mt-0.5">{p.badge}</span>
              </button>
            );
          })}
        </div>
      </div>

      {/* Selected Persona Deep Dive Card */}
      <div className="rounded-xl border border-[#223044] bg-[#0E1522] p-6 shadow-lg space-y-4">
        <div className="flex items-center justify-between pb-4 border-b border-[#1E2B3E]">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-lg bg-[#141E2F] border border-cyan-800 flex items-center justify-center text-cyan-400">
              <currentPersona.icon className="w-5 h-5" />
            </div>
            <div>
              <h3 className="text-sm font-bold text-slate-100 font-mono">{currentPersona.title} Perspective</h3>
              <span className="text-[11px] font-mono text-cyan-400">{currentPersona.badge} Framework</span>
            </div>
          </div>

          <span className="px-3 py-1 rounded bg-[#0A101C] border border-cyan-800 text-cyan-300 font-mono text-xs font-bold">
            VERDICT: {currentPersona.verdict}
          </span>
        </div>

        <div className="p-4 rounded-lg bg-[#080D15] border border-[#1A2638] text-sm text-slate-200 leading-relaxed font-sans">
          <span className="font-mono text-xs uppercase text-slate-400 block mb-1.5 font-bold">
            Constituency Strategic Analysis:
          </span>
          {currentPersona.focus}
        </div>
      </div>

      {/* Unified Decision Intelligence & Action Panel */}
      {offer.interpretations?.ic_stance_mandate && (
        <EvidenceInterpretationPanel
          interpretation={offer.interpretations.ic_stance_mandate}
          title="Vault 7: Multi-Stakeholder Consensus & IC Mandate"
        />
      )}

      {/* Expandable 4-Pillar Narrative Drawer */}
      <AnalystInsightDrawer
        title="Stakeholder Alignment & Constituency Governance Synthesizer"
        narrative={{
          sectorContext: "Constituency objectives diverge during IPO roadshows: CFOs optimize valuation multiple, lenders demand covenant de-leveraging, and QIBs demand margin of safety.",
          lifecyclePrecedents: "During SBI Cards IPO, credit lenders and retail investors held divergent views on provisioning buffers following macroeconomic shocks.",
          icDirectives: "Structure allocation bids to reconcile lender solvency comfort with institutional return hurdles.",
          riskRadar: "Audit Committee scrutiny on RPT transactions creates regulatory overhang if voting results are contested by public institutional holders."
        }}
      />
    </div>
  );
};
