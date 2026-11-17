import React, { useState } from 'react';
import { StatutoryOfferDetails, VaultId } from '../types/terminal';
import { FileText, Download, Building2, Clock, AlertTriangle, ShieldCheck, Sun, BarChart3 } from 'lucide-react';

interface StatutoryOfferHeroProps {
  offer: StatutoryOfferDetails;
  onSelectVault?: (vaultId: VaultId) => void;
  onSeasonalityToggle?: (isSeasonalityAdjusted: boolean) => void;
}

export const StatutoryOfferHero: React.FC<StatutoryOfferHeroProps> = ({
  offer,
  onSelectVault,
  onSeasonalityToggle
}) => {
  const [isSeasonalityAdjusted, setIsSeasonalityAdjusted] = useState<boolean>(false);

  const handleToggleSeasonality = (val: boolean) => {
    setIsSeasonalityAdjusted(val);
    onSeasonalityToggle?.(val);
  };

  const freshPct = offer.freshIssuePct ?? (offer.issueSizeCr && offer.freshIssueCr !== null ? Math.round((offer.freshIssueCr / Math.max(1, offer.issueSizeCr)) * 100) : 100);
  const ofsPct = offer.ofsPct ?? (offer.issueSizeCr && offer.ofsCr !== null ? Math.round((offer.ofsCr / Math.max(1, offer.issueSizeCr)) * 100) : 0);

  // Exhaustive switch on pricingState.status
  let isContained = false;
  let priceCardContent: React.ReactNode = null;
  let hasValidPrice = false;
  let priceBandMax: number | null = null;

  switch (offer.pricingState.status) {
    case 'DRHP_UNPRICED':
      isContained = offer.pricingState.isContained;
      hasValidPrice = false;
      priceCardContent = (
        <>
          <div className="text-sm font-bold font-mono text-cyan-400 pt-0.5">
            Drafting / Unpriced
          </div>
          <span className="text-[10px] text-slate-500 font-mono">SEBI Book-Build [●]</span>
        </>
      );
      break;
    case 'RHP_PRICED':
      isContained = offer.pricingState.isContained;
      hasValidPrice = true;
      priceBandMax = offer.pricingState.priceBandMax;
      priceCardContent = (
        <>
          <div className="text-lg font-bold font-mono text-slate-100 tabular-nums">
            ₹{offer.pricingState.priceBandMin} - ₹{offer.pricingState.priceBandMax}
          </div>
          <span className="text-[10px] text-slate-500 font-mono">Per Equity Share</span>
        </>
      );
      break;
    case 'TRADING_LIVE':
      isContained = false;
      hasValidPrice = true;
      priceBandMax = offer.pricingState.listingPrice;
      priceCardContent = (
        <>
          <div className="text-lg font-bold font-mono text-slate-100 tabular-nums">
            LTP ₹{offer.pricingState.ltp}
          </div>
          <span className="text-[10px] text-slate-500 font-mono">List: ₹{offer.pricingState.listingPrice}</span>
        </>
      );
      break;
    default: {
      const _exhaustiveCheck: never = offer.pricingState;
      throw new Error(`Unhandled pricing state: ${JSON.stringify(_exhaustiveCheck)}`);
    }
  }

  return (
    <div className="rounded-lg border border-[#223044] bg-[#101620] p-5 shadow-sm space-y-4">
      {/* ⚠️ SEBI ICDR 2018 Statutory Evidence Containment Banner (when isContained === true) */}
      {isContained && (
        <div className="rounded-md border-l-4 border-amber-500 bg-amber-950/40 border border-amber-900/60 p-3.5 text-xs text-amber-200 shadow-sm flex flex-col md:flex-row md:items-center justify-between gap-3 animate-fade-in">
          <div className="flex items-start gap-2.5">
            <AlertTriangle className="w-4 h-4 text-amber-400 shrink-0 mt-0.5" />
            <div className="leading-relaxed">
              <span className="font-semibold text-amber-300 font-mono tracking-wide">
                SEBI ICDR 2018 STATUTORY EVIDENCE CONTAINMENT ACTIVE:
              </span>{' '}
              Analytical processing (Offer Valuation, WACC/ROIC, Reverse DCF, and Board Deck generation) is strictly{' '}
              <span className="font-semibold text-amber-100">QUARANTINED</span> until the 513-page parent DRHP is fully indexed and its evidence ledger reviewed and accepted in Tab 2 (Provenance Ledger). All values shown below are candidate unreviewed disclosures and cannot be used for investment, credit, or underwriting decisions.
            </div>
          </div>
          <button
            onClick={() => onSelectVault?.('provenance_ledger')}
            className="shrink-0 px-3 py-1.5 rounded bg-amber-500 hover:bg-amber-400 text-slate-950 font-bold font-mono text-xs transition-colors flex items-center gap-1.5 shadow-sm cursor-pointer"
          >
            <span>Review Ledger</span>
            <span>→</span>
          </button>
        </div>
      )}

      {/* Top Header Row: 6 Statutory Badges */}
      <div className="flex items-center gap-2 flex-wrap text-xs font-mono">
        {/* Badge 1: Ticker */}
        <span className="px-2 py-0.5 rounded bg-cyan-950/80 border border-cyan-800 text-cyan-300 font-semibold tracking-wide">
          NSE: {offer.symbol}
        </span>

        {/* Badge 2: Route / Book-Build */}
        <span className="px-2 py-0.5 rounded bg-slate-800 border border-slate-700 text-slate-300">
          {offer.boardSegment || 'MAINBOARD'} BOOK-BUILD
        </span>

        {/* Badge 3: Audit / Containment & Single Deal Integrity */}
        <span
          className={`px-2 py-0.5 rounded font-semibold flex items-center gap-1.5 border ${
            offer.dealIntegrity === 'PASS'
              ? 'bg-emerald-950/70 border-emerald-800 text-emerald-300'
              : offer.dealIntegrity === 'CONDITIONAL'
              ? 'bg-amber-950/70 border-amber-800 text-amber-300'
              : 'bg-rose-950/70 border-rose-800 text-rose-300'
          }`}
        >
          <span
            className={`w-1.5 h-1.5 rounded-full ${
              offer.dealIntegrity === 'PASS'
                ? 'bg-emerald-400'
                : offer.dealIntegrity === 'CONDITIONAL'
                ? 'bg-amber-400 animate-pulse'
                : 'bg-rose-400 animate-pulse'
            }`}
          ></span>
          INTEGRITY: {offer.dealIntegrity}
        </span>

        {/* Badge 4: Filing Date */}
        <span className="px-2 py-0.5 rounded bg-blue-950/60 border border-blue-800 text-blue-300">
          {offer.filingDateLabel || 'DRHP · OCTOBER 2026'}
        </span>

        {/* Badge 5: Dickinson Life-Cycle Stage */}
        <span className="px-2 py-0.5 rounded bg-emerald-950/80 border border-emerald-700 text-emerald-300 font-semibold">
          DICKINSON: {offer.dickinsonStage || 'MATURE (CASH COW)'} {offer.cashFlowPattern || '(+, -, -)'}
        </span>

        {/* Badge 6: Regulatory Context */}
        <span className="px-2 py-0.5 rounded bg-amber-950/60 border border-amber-800 text-amber-300">
          CONTEXT: PUBLIC IPO (ORDINARY EQUITY)
        </span>
      </div>

      {/* Main Title & Action Bar */}
      <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4 pb-3 border-b border-[#1D2838]">
        <div>
          <h1 className="text-2xl lg:text-3xl font-bold tracking-tight text-slate-100">
            {offer.companyName}
          </h1>
          <p className="text-xs text-slate-400 mt-1 flex items-center gap-2 flex-wrap">
            <span>Sector: <strong className="text-slate-300">{offer.sectorName || 'Non-Alcoholic Ready-to-Drink Beverages'}</strong></span>
            <span>•</span>
            <span>Listing: <strong className="text-slate-300">{offer.listingExchanges || 'BSE, NSE'}</strong></span>
            <span>•</span>
            <span>Statutory Filing Route: <strong className="text-cyan-400">{offer.sebiEligibilityRoute}</strong></span>
          </p>
        </div>

        {/* Right Action Cluster: Seasonality Toggle & Document Links */}
        <div className="flex items-center gap-3 shrink-0 flex-wrap">
          {/* Seasonality-Adjusted Toggle */}
          <div className="flex items-center rounded-md border border-[#223044] bg-[#090D12] p-0.5 text-xs font-mono">
            <button
              onClick={() => handleToggleSeasonality(false)}
              className={`px-2.5 py-1 rounded flex items-center gap-1 transition-colors cursor-pointer ${
                !isSeasonalityAdjusted
                  ? 'bg-slate-800 text-cyan-300 font-semibold'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              <BarChart3 className="w-3 h-3" />
              <span>Trailing Actuals</span>
            </button>
            <button
              onClick={() => handleToggleSeasonality(true)}
              className={`px-2.5 py-1 rounded flex items-center gap-1 transition-colors cursor-pointer ${
                isSeasonalityAdjusted
                  ? 'bg-amber-950 border border-amber-700 text-amber-300 font-semibold'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              <Sun className="w-3 h-3 text-amber-400" />
              <span>Seasonality FY27E</span>
            </button>
          </div>

          {/* Document Links */}
          <div className="flex items-center gap-2">
            <a
              href={offer.rhpUrl || '#'}
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center gap-1.5 px-3 py-1.5 rounded bg-[#151D2A] border border-[#223044] hover:border-cyan-500 hover:text-cyan-300 text-xs text-slate-200 transition-colors cursor-pointer font-mono"
            >
              <Download className="w-3.5 h-3.5 text-cyan-400" />
              <span>{offer.issueType === 'DRHP' ? 'DRHP PDF (SEBI Doc)' : 'RHP ZIP (NSE Doc)'}</span>
            </a>

            {offer.anchorListUrl && (
              <a
                href={offer.anchorListUrl}
                target="_blank"
                rel="noopener noreferrer"
                className="flex items-center gap-1.5 px-3 py-1.5 rounded bg-[#151D2A] border border-[#223044] hover:border-emerald-500 hover:text-emerald-300 text-xs text-slate-200 transition-colors cursor-pointer font-mono"
              >
                <FileText className="w-3.5 h-3.5 text-emerald-400" />
                <span>Anchor Allocation JSON</span>
              </a>
            )}
          </div>
        </div>
      </div>

      {/* 5 Statutory Metric Cards + Exact Share Count */}
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3 pt-1">
        {/* Card 1: Price Band */}
        <div className="p-3 rounded bg-[#090D12] border border-[#1E293B]">
          <span className="text-[11px] text-slate-400 block mb-1">Price Band</span>
          {priceCardContent}
        </div>

        {/* Card 2: Market Lot */}
        <div className="p-3 rounded bg-[#090D12] border border-[#1E293B]">
          <span className="text-[11px] text-slate-400 block mb-1">Market Lot</span>
          {offer.lotSize && hasValidPrice && offer.lotSize > 0 ? (
            <>
              <div className="text-lg font-bold font-mono text-slate-100 tabular-nums">
                {offer.lotSize} <span className="text-xs font-normal text-slate-400">shares</span>
              </div>
              <span className="text-[10px] text-slate-500 font-mono">
                Min ₹{(offer.lotSize * (priceBandMax ?? 0)).toLocaleString('en-IN')} Commitment
              </span>
            </>
          ) : (
            <>
              <div className="text-sm font-bold font-mono text-slate-300 pt-0.5">
                Pending ROC
              </div>
              <span className="text-[10px] text-slate-500 font-mono">Min 1 BRLM Lot</span>
            </>
          )}
        </div>

        {/* Card 3: Offering Size (Exact Shares + Rupee Total) */}
        <div className="p-3 rounded bg-[#090D12] border border-[#1E293B]">
          <span className="text-[11px] text-slate-400 block mb-1">Offering Size</span>
          {offer.totalOfferingShares ? (
            <>
              <div className="text-lg font-bold font-mono text-cyan-400 tabular-nums truncate">
                {typeof offer.totalOfferingShares === 'number'
                  ? offer.totalOfferingShares.toLocaleString('en-IN')
                  : offer.totalOfferingShares}
              </div>
              <span className="text-[10px] text-slate-400 font-mono">
                Shares (₹{(offer.issueSizeCr || 0).toLocaleString('en-IN', { minimumFractionDigits: 2 })} Cr Est.)
              </span>
            </>
          ) : (
            <>
              <div className="text-lg font-bold font-mono text-cyan-400 tabular-nums">
                ₹{(offer.issueSizeCr || 0).toLocaleString('en-IN', { minimumFractionDigits: 2 })} Cr
              </div>
              <span className="text-[10px] text-slate-500 font-mono">Total Issue Capital</span>
            </>
          )}
        </div>

        {/* Card 4: Fresh Issue vs OFS Split */}
        <div className="p-3 rounded bg-[#090D12] border border-[#1E293B]">
          <span className="text-[11px] text-slate-400 block mb-1">Fresh / OFS Split</span>
          <div className="text-lg font-bold font-mono tabular-nums">
            <span className={freshPct > 0 ? 'text-emerald-400' : 'text-slate-500'}>{freshPct}%</span>
            <span className="text-slate-600"> / </span>
            <span className={ofsPct > 0 ? 'text-amber-400' : 'text-slate-500'}>{ofsPct}%</span>
          </div>
          <span className={`text-[10px] font-mono ${ofsPct === 0 ? 'text-emerald-400' : 'text-amber-400'}`}>
            {ofsPct === 0 ? 'Zero Promoter Exit' : `${ofsPct}% Secondary Exit`}
          </span>
        </div>

        {/* Card 5: Bidding Window */}
        <div className="p-3 rounded bg-[#090D12] border border-[#1E293B]">
          <span className="text-[11px] text-slate-400 block mb-1">Bidding Period</span>
          <div className="text-xs font-semibold font-mono text-slate-200 mt-0.5 truncate">
            {offer.issueStartDate}
          </div>
          <div className="text-xs font-semibold font-mono text-slate-200 truncate">
            to {offer.issueEndDate}
          </div>
        </div>

        {/* Card 6: Post-IPO Statutory Lock-In */}
        <div className="p-3 rounded bg-[#090D12] border border-[#1E293B]">
          <span className="text-[11px] text-slate-400 block mb-1">Statutory Lock-In</span>
          <div className="text-sm font-bold font-mono text-amber-400">
            {offer.lockInDaysPreIPOShareholders} Days <span className="text-xs text-slate-400 font-normal">(Pre-IPO)</span>
          </div>
          <span className="text-[10px] text-slate-500 font-mono">
            {offer.lockInDaysQIBAnchor} Days QIB Anchor (50%)
          </span>
        </div>
      </div>

      {/* Dual-Tone Horizontal Dilution Track */}
      <div className="space-y-1">
        <div className="h-1.5 w-full bg-slate-900 rounded-full overflow-hidden flex">
          <div
            style={{ width: `${freshPct}%` }}
            className="bg-emerald-500 h-full transition-all duration-500"
            title={`Fresh Growth: ${freshPct}%`}
          />
          <div
            style={{ width: `${ofsPct}%` }}
            className="bg-amber-500 h-full transition-all duration-500"
            title={`Promoter OFS: ${ofsPct}%`}
          />
        </div>
        <div className="flex justify-between text-[10px] font-mono text-slate-400">
          <span>Structure: {offer.structureDisplay || `${freshPct}% Fresh · ${ofsPct}% OFS`}</span>
          <span>Target: T+3 Days Settlement (NSE/BSE)</span>
        </div>
      </div>

      {/* Footer: Lead Managers Syndicate Strip */}
      <div className="pt-2 border-t border-[#1D2838] flex flex-col md:flex-row md:items-center justify-between text-xs text-slate-400 gap-2">
        <div className="flex items-center gap-2 flex-wrap">
          <Building2 className="w-3.5 h-3.5 text-slate-500 shrink-0" />
          <span className="text-slate-500 font-mono text-[11px]">BOOK RUNNING LEAD MANAGERS:</span>
          <span className="text-slate-300 font-medium text-[11px]">{offer.leadManagers.join(' • ')}</span>
        </div>
        <div className="flex items-center gap-1.5 text-[11px] text-slate-500 font-mono shrink-0">
          <Clock className="w-3 h-3 text-slate-500" />
          <span>NSE / BSE Central Clearing</span>
        </div>
      </div>
    </div>
  );
};
