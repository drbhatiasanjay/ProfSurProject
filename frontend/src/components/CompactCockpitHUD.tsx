import React from 'react';
import { StatutoryOfferDetails, HuberCalibrationResults, VaultId } from '../types/terminal';
import { StatutoryOfferHero } from './StatutoryOfferHero';
import { LintelTowers } from './LintelTowers';
import {
  ChevronDown,
  ChevronUp,
  ShieldAlert,
  CheckCircle2,
  FileText,
  AlertTriangle,
  Lock,
  Layers,
  Sparkles
} from 'lucide-react';

interface CompactCockpitHUDProps {
  offer: StatutoryOfferDetails;
  calibration: HuberCalibrationResults;
  isExpanded: boolean;
  onToggleExpand: () => void;
  onSelectVault?: (vaultId: VaultId) => void;
}

export const CompactCockpitHUD: React.FC<CompactCockpitHUDProps> = ({
  offer,
  calibration,
  isExpanded,
  onToggleExpand,
  onSelectVault
}) => {
  // Exhaustive switch on pricingState.status (SEBI Deal Pricing Lifecycle FSM)
  let isUnpriced = false;
  let isContained = false;
  let priceDisplay: React.ReactNode = null;

  switch (offer.pricingState.status) {
    case 'DRHP_UNPRICED':
      isUnpriced = true;
      isContained = offer.pricingState.isContained;
      priceDisplay = <span className="text-cyan-400 font-semibold">Undisclosed [●]</span>;
      break;
    case 'RHP_PRICED':
      isUnpriced = false;
      isContained = offer.pricingState.isContained;
      priceDisplay = (
        <span className="text-emerald-400 font-bold">
          ₹{offer.pricingState.priceBandMin} - ₹{offer.pricingState.priceBandMax}
        </span>
      );
      break;
    case 'TRADING_LIVE':
      isUnpriced = false;
      isContained = false;
      priceDisplay = (
        <span className="text-emerald-400 font-bold">
          LTP ₹{offer.pricingState.ltp} (List ₹{offer.pricingState.listingPrice})
        </span>
      );
      break;
    default: {
      const _exhaustiveCheck: never = offer.pricingState;
      throw new Error(`Unhandled pricing state: ${JSON.stringify(_exhaustiveCheck)}`);
    }
  }

  // Tower Telemetry
  const freshPct = offer?.freshIssuePct ?? (offer?.issueSizeCr && offer?.freshIssueCr !== null && offer?.freshIssueCr !== undefined ? Math.round((offer.freshIssueCr / Math.max(1, offer.issueSizeCr)) * 100) : 100);
  const ofsPct = offer?.ofsPct ?? (offer?.issueSizeCr && offer?.ofsCr !== null && offer?.ofsCr !== undefined ? Math.round((offer.ofsCr / Math.max(1, offer.issueSizeCr)) * 100) : 0);
  const frothPct = isUnpriced ? null : (calibration?.unbackedFrothPct ?? 1508.8);

  return (
    <div className="sticky top-0 z-30 bg-[#090D12]/95 backdrop-blur-md border-b border-[#1E2B3E] shadow-md transition-all shrink-0">
      {/* 46px Compact Telemetry HUD Ribbon */}
      <div className="px-3 py-2 flex flex-wrap items-center justify-between gap-2 text-xs font-mono">
        {/* Left Section: Issuer, Route, Price, Dickinson */}
        <div className="flex items-center gap-2 flex-wrap">
          {/* Symbol Pill */}
          <span className="px-2 py-0.5 rounded bg-cyan-950 border border-cyan-700 text-cyan-300 font-bold">
            {offer?.symbol || 'NTPCGREEN'}
          </span>

          {/* Company Name */}
          <span className="font-semibold text-slate-100 font-sans truncate max-w-[200px] xl:max-w-none">
            {offer?.companyName || 'NTPC Green Energy Limited'}
          </span>

          <span className="text-slate-600">|</span>

          {/* Price Band */}
          <span className="text-slate-300">
            {priceDisplay}
          </span>

          <span className="text-slate-600 hidden sm:inline">|</span>

          {/* Size & Split */}
          <span className="text-slate-400 hidden sm:inline">
            {freshPct === 100 ? (
              <span className="text-emerald-400 font-semibold">₹{(offer?.issueSizeCr ?? 0).toLocaleString()} Cr (100% Fresh)</span>
            ) : ofsPct === 100 ? (
              <span className="text-amber-400 font-semibold">{offer?.totalOfferingShares || '997,461,456'} Sh (100% OFS)</span>
            ) : (
              <span>₹{(offer?.issueSizeCr ?? 0).toLocaleString()} Cr</span>
            )}
          </span>

          <span className="text-slate-600 hidden md:inline">|</span>

          {/* Dickinson Stage Pill */}
          <span className="px-1.5 py-0.5 rounded text-[10px] bg-[#121B29] border border-[#223044] text-slate-300 hidden md:inline">
            {offer?.dickinsonStage || 'GROWTH'} {offer?.cashFlowPattern || '(+,-,+)'}
          </span>

          {/* Amber Quarantine Alert Pill if Contained */}
          {isContained && (
            <button
              onClick={() => onSelectVault?.('provenance_ledger')}
              className="px-2 py-0.5 rounded bg-amber-950/90 border border-amber-600 text-amber-300 font-bold text-[10px] flex items-center gap-1 hover:bg-amber-900 transition-colors cursor-pointer"
            >
              <AlertTriangle className="w-3 h-3 text-amber-400" />
              <span>QUARANTINED</span>
            </button>
          )}
        </div>

        {/* Right Section: 3 Micro-Towers Telemetry, Tri-State Ledger & Expand Toggle */}
        <div className="flex items-center gap-2.5">
          {/* Micro-Tower 1 Telemetry */}
          <span
            className={`px-1.5 py-0.5 rounded text-[10px] font-semibold hidden lg:inline border ${freshPct === 100
                ? 'bg-emerald-950/60 border-emerald-800 text-emerald-400'
                : 'bg-amber-950/60 border-amber-800 text-amber-400'
              }`}
          >
            T1: {freshPct === 100 ? '100% Fresh' : '100% OFS'}
          </span>

          {/* Micro-Tower 2 Telemetry */}
          <span
            className={`px-1.5 py-0.5 rounded text-[10px] font-semibold hidden lg:inline border ${isUnpriced
                ? 'bg-blue-950/60 border-blue-800 text-blue-300'
                : 'bg-rose-950/60 border-rose-800 text-rose-300'
              }`}
          >
            T2: {isUnpriced ? 'Unpriced [●]' : `+${frothPct}% Froth`}
          </span>

          {/* Micro-Tower 3 Telemetry */}
          <span className="px-1.5 py-0.5 rounded text-[10px] font-semibold hidden xl:inline border bg-amber-950/60 border-amber-800 text-amber-300">
            T3: 180D Cliff
          </span>

          <span className="text-slate-600 hidden lg:inline">|</span>

          {/* Tri-State Ledger Counter Mini-Pill */}
          <div className="flex items-center gap-1 text-[10px] font-semibold">
            <span className="px-1.5 py-0.5 rounded bg-emerald-950/70 text-emerald-400 border border-emerald-800">
              🟢 36
            </span>
            <span className="px-1.5 py-0.5 rounded bg-slate-800/80 text-slate-300 border border-slate-700">
              ⚪ 4
            </span>
            <span className="px-1.5 py-0.5 rounded bg-amber-950/70 text-amber-400 border border-amber-800">
              🟠 2
            </span>
          </div>

          <span className="text-slate-600">|</span>

          {/* Expand / Collapse Button */}
          <button
            onClick={onToggleExpand}
            className={`px-2.5 py-1 rounded text-xs font-mono font-semibold flex items-center gap-1.5 cursor-pointer transition-all shadow-sm ${isExpanded
                ? 'bg-cyan-500/20 border border-cyan-400 text-cyan-200'
                : 'bg-[#152033] hover:bg-[#1C2C47] border border-cyan-800 text-cyan-300'
              }`}
          >
            <span>{isExpanded ? '[-] Collapse Cockpit' : '[+] Full Cockpit & Towers'}</span>
            {isExpanded ? (
              <ChevronUp className="w-3.5 h-3.5 text-cyan-300" />
            ) : (
              <ChevronDown className="w-3.5 h-3.5 text-cyan-400" />
            )}
          </button>
        </div>
      </div>

      {/* Expandable Cockpit Drawer (State B) */}
      {isExpanded && (
        <div className="p-4 border-t border-[#1F2C40] bg-[#0A0F17] space-y-4 max-h-[80vh] overflow-y-auto animate-fade-in shadow-2xl">
          <StatutoryOfferHero offer={offer} onSelectVault={onSelectVault} />
          <LintelTowers offer={offer} calibration={calibration} />
        </div>
      )}
    </div>
  );
};
