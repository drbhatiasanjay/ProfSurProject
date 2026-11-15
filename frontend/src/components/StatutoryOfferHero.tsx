import React from 'react';
import { StatutoryOfferDetails } from '../types/terminal';
import { FileText, Download, Building2, Calendar, Scale, Clock, AlertTriangle } from 'lucide-react';

interface StatutoryOfferHeroProps {
  offer: StatutoryOfferDetails;
}

export const StatutoryOfferHero: React.FC<StatutoryOfferHeroProps> = ({ offer }) => {
  return (
    <div className="rounded-lg border border-[#223044] bg-[#101620] p-5 shadow-sm">
      {/* Top Bar: Company Name & Badges */}
      <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4 pb-4 border-b border-[#1D2838]">
        <div>
          <div className="flex items-center gap-2.5 mb-1.5 flex-wrap">
            <span className="font-mono text-xs px-2 py-0.5 rounded bg-cyan-950/80 border border-cyan-800 text-cyan-300 font-semibold tracking-wide">
              NSE: {offer.symbol}
            </span>
            <span className="text-xs px-2 py-0.5 rounded bg-slate-800 border border-slate-700 text-slate-300 font-mono">
              {offer.issueType} Book-Build
            </span>
            <span className="text-xs px-2 py-0.5 rounded bg-emerald-950/60 border border-emerald-800 text-emerald-400 font-mono flex items-center gap-1">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-400"></span>
              LIVE ISSUE BIDDING
            </span>
          </div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-100">
            {offer.companyName}
          </h1>
          <p className="text-xs text-slate-400 mt-0.5 flex items-center gap-2">
            <span>Statutory Filing Route:</span>
            <span className="text-slate-300 font-medium">{offer.sebiEligibilityRoute}</span>
          </p>
        </div>

        {/* Action Triggers: RHP & Anchor Links */}
        <div className="flex items-center gap-2.5 shrink-0 flex-wrap">
          <a
            href={offer.rhpUrl}
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center gap-1.5 px-3 py-1.5 rounded bg-[#151D2A] border border-[#223044] hover:border-cyan-500 hover:text-cyan-300 text-xs text-slate-200 transition-colors cursor-pointer"
          >
            <Download className="w-3.5 h-3.5 text-cyan-400" />
            <span className="font-mono">RHP ZIP (NSE Doc)</span>
          </a>

          {offer.anchorListUrl && (
            <a
              href={offer.anchorListUrl}
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center gap-1.5 px-3 py-1.5 rounded bg-[#151D2A] border border-[#223044] hover:border-emerald-500 hover:text-emerald-300 text-xs text-slate-200 transition-colors cursor-pointer"
            >
              <FileText className="w-3.5 h-3.5 text-emerald-400" />
              <span className="font-mono">Anchor Allocation JSON</span>
            </a>
          )}
        </div>
      </div>

      {/* Numerical Matrix: Pricing, Dilution, & Capital Split */}
      <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-3 pt-4">
        {/* Metric 1: Price Band */}
        <div className="p-3 rounded bg-[#090D12] border border-[#1E293B]">
          <span className="text-[11px] text-slate-400 block mb-1">Price Band</span>
          <div className="text-lg font-bold font-mono text-slate-100 tabular-nums">
            ₹{offer.priceBandMin} - ₹{offer.priceBandMax}
          </div>
          <span className="text-[10px] text-slate-500 font-mono">Per Equity Share</span>
        </div>

        {/* Metric 2: Market Lot */}
        <div className="p-3 rounded bg-[#090D12] border border-[#1E293B]">
          <span className="text-[11px] text-slate-400 block mb-1">Market Lot</span>
          <div className="text-lg font-bold font-mono text-slate-100 tabular-nums">
            {offer.lotSize} <span className="text-xs font-normal text-slate-400">shares</span>
          </div>
          <span className="text-[10px] text-slate-500 font-mono">
            Min ₹{(offer.lotSize * offer.priceBandMax).toLocaleString('en-IN')}
          </span>
        </div>

        {/* Metric 3: Total Issue Size */}
        <div className="p-3 rounded bg-[#090D12] border border-[#1E293B]">
          <span className="text-[11px] text-slate-400 block mb-1">Total Issue Size</span>
          <div className="text-lg font-bold font-mono text-cyan-400 tabular-nums">
            ₹{offer.issueSizeCr.toLocaleString('en-IN', { minimumFractionDigits: 2 })} Cr
          </div>
          <span className="text-[10px] text-slate-500 font-mono">100% Primary Equity</span>
        </div>

        {/* Metric 4: Fresh Issue vs OFS */}
        <div className="p-3 rounded bg-[#090D12] border border-[#1E293B]">
          <span className="text-[11px] text-slate-400 block mb-1">Fresh / OFS Split</span>
          <div className="text-lg font-bold font-mono text-emerald-400 tabular-nums">
            100% / 0%
          </div>
          <span className="text-[10px] text-emerald-500 font-mono">Zero Promoter Exit</span>
        </div>

        {/* Metric 5: Bidding Window */}
        <div className="p-3 rounded bg-[#090D12] border border-[#1E293B]">
          <span className="text-[11px] text-slate-400 block mb-1">Bidding Period</span>
          <div className="text-xs font-semibold font-mono text-slate-200 mt-1">
            {offer.issueStartDate} to
          </div>
          <div className="text-xs font-semibold font-mono text-slate-200">
            {offer.issueEndDate}
          </div>
        </div>

        {/* Metric 6: Post-IPO Statutory Lock-In */}
        <div className="p-3 rounded bg-[#090D12] border border-[#1E293B]">
          <span className="text-[11px] text-slate-400 block mb-1">Statutory Lock-In</span>
          <div className="text-sm font-bold font-mono text-amber-400">
            {offer.lockInDaysPreIPOShareholders} Days <span className="text-xs text-slate-400">(Pre-IPO)</span>
          </div>
          <span className="text-[10px] text-slate-500 font-mono">
            {offer.lockInDaysQIBAnchor} Days QIB Anchor (50%)
          </span>
        </div>
      </div>

      {/* Footer: Lead Managers Bar */}
      <div className="mt-4 pt-3 border-t border-[#1D2838] flex flex-col md:flex-row md:items-center justify-between text-xs text-slate-400 gap-2">
        <div className="flex items-center gap-2">
          <Building2 className="w-3.5 h-3.5 text-slate-500" />
          <span className="text-slate-500 font-mono">BOOK RUNNING LEAD MANAGERS (BRLMs):</span>
          <span className="text-slate-300 font-medium">{offer.leadManagers.join(' • ')}</span>
        </div>
        <div className="flex items-center gap-1.5 text-[11px] text-slate-500 font-mono">
          <Clock className="w-3 h-3 text-slate-500" />
          <span>Listing Target: T+3 Days Settlement (NSE/BSE)</span>
        </div>
      </div>
    </div>
  );
};
