import React, { useState } from 'react';
import { SubscriptionBook } from '../types/terminal';
import { Users, TrendingUp, CheckCircle, ChevronUp, ChevronDown } from 'lucide-react';

interface SubscriptionBookBarProps {
  subscription: SubscriptionBook;
  defaultExpanded?: boolean;
}

export const SubscriptionBookBar: React.FC<SubscriptionBookBarProps> = ({
  subscription,
  defaultExpanded = true,
}) => {
  const [isExpanded, setIsExpanded] = useState<boolean>(defaultExpanded);

  // Safely extract category tranches from subscription.categories or top-level props
  const categories = subscription?.categories || [];
  const qibCategory = categories.find(c => c.category.includes('QIB') || c.category.includes('Qualified Institutional'));
  const niiCategory = categories.find(c => c.category.includes('NII') || c.category.includes('Non-Institutional'));
  const retailCategory = categories.find(c => c.category.includes('RII') || c.category.includes('Retail'));

  const totalMultiple = subscription?.totalMultiple ?? 0;
  const totalBidsShares = subscription?.totalBidsShares ?? 0;
  const qibMultiple = (subscription as unknown as { qibMultiple?: number })?.qibMultiple ?? qibCategory?.subscriptionMultiple ?? 0;
  const niiMultiple = (subscription as unknown as { niiMultiple?: number })?.niiMultiple ?? niiCategory?.subscriptionMultiple ?? 0;
  const retailMultiple = (subscription as unknown as { retailMultiple?: number })?.retailMultiple ?? retailCategory?.subscriptionMultiple ?? 0;

  return (
    <div
      id="module-order-book"
      className="rounded-xl border border-slate-700/80 border-t-2 border-t-cyan-400 bg-gradient-to-b from-[#0D1526] via-[#0A0F1D] to-[#070B14] p-5 shadow-xl shadow-black/50 transition-all text-xs font-sans space-y-4"
    >
      {/* Header Bar with Eyebrow Tag & In-Card Toggle */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 pb-3 border-b border-slate-800/80">
        <div className="flex items-center gap-2.5">
          <div className="p-1.5 rounded-lg bg-cyan-950/80 border border-cyan-800/60 text-cyan-400">
            <TrendingUp className="w-4 h-4" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="px-1.5 py-0.2 rounded text-[10px] font-mono font-bold bg-cyan-950 text-cyan-300 border border-cyan-800">
                MODULE 01
              </span>
              <h2 className="text-sm font-semibold tracking-wider text-slate-100 uppercase font-mono">
                NSE Live Order Book &amp; Category Demand
              </h2>
            </div>
            <div className="text-[11px] text-slate-400 font-sans mt-0.5">
              Live ASBA institutional subscription tranches &amp; syndicate book depth
            </div>
          </div>
        </div>

        <div className="flex items-center gap-3">
          <div className="flex items-center gap-1.5 text-xs font-mono text-slate-400">
            <span className="text-slate-500">SYNC:</span>
            <span className="text-slate-300">{subscription?.lastUpdated || 'Live Sync'}</span>
          </div>
          <button
            type="button"
            onClick={() => setIsExpanded(!isExpanded)}
            className="flex items-center gap-1 text-[11px] font-mono font-semibold px-2.5 py-1 rounded-md bg-slate-800 hover:bg-slate-700 text-cyan-300 border border-slate-700 cursor-pointer transition-colors"
          >
            <span>{isExpanded ? 'Collapse' : 'Expand'}</span>
            {isExpanded ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
          </button>
        </div>
      </div>

      {/* Aggregate Overview Stat Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
        <div className="p-3 rounded-lg bg-[#070B12] border border-slate-800 flex items-center justify-between">
          <div>
            <span className="text-[10px] font-mono text-slate-400 block uppercase">Total Subscription</span>
            {totalMultiple > 0 ? (
              <span className="text-xl font-bold font-mono text-emerald-400 tabular-nums">
                {totalMultiple.toFixed(2)}x
              </span>
            ) : (
              <span className="text-xs font-bold font-mono text-cyan-400">
                DRHP Drafting (Pre-Bidding)
              </span>
            )}
          </div>
          <div className="p-2 rounded bg-emerald-950/40 border border-emerald-800/60">
            <CheckCircle className="w-4 h-4 text-emerald-400" />
          </div>
        </div>

        <div className="p-3 rounded-lg bg-[#070B12] border border-slate-800 flex items-center justify-between">
          <div>
            <span className="text-[10px] font-mono text-slate-400 block uppercase">Total Shares Bid</span>
            {totalBidsShares > 0 ? (
              <span className="text-xl font-bold font-mono text-slate-100 tabular-nums">
                {(totalBidsShares / 1e7).toFixed(2)} Cr
              </span>
            ) : (
              <span className="text-xs font-bold font-mono text-slate-400">
                Order Book Not Opened
              </span>
            )}
          </div>
          <div className="p-2 rounded bg-slate-900 border border-slate-800 text-slate-400">
            <Users className="w-4 h-4" />
          </div>
        </div>

        <div className="p-3 rounded-lg bg-[#070B12] border border-slate-800 flex items-center justify-between">
          <div>
            <span className="text-[10px] font-mono text-slate-400 block uppercase">QIB Anchor Tranche</span>
            <span className="text-xl font-bold font-mono text-cyan-400 tabular-nums">
              {qibMultiple > 0 ? `${qibMultiple.toFixed(2)}x` : 'Committed'}
            </span>
          </div>
          <div className="p-2 rounded bg-cyan-950/40 border border-cyan-800/60 text-cyan-400">
            <CheckCircle className="w-4 h-4" />
          </div>
        </div>
      </div>

      {/* Expanded Breakdown */}
      {isExpanded && (
        <div className="space-y-3 pt-1 border-t border-slate-800/80 animate-fade-in">
          <div className="text-[10px] font-mono uppercase text-slate-400 font-bold tracking-wider">
            Investor Category Subscription Breakdown
          </div>

          {categories.length > 0 ? (
            categories.map((cat, idx) => {
              const multiple = cat.subscriptionMultiple ?? 0;
              const color =
                idx === 0
                  ? 'cyan'
                  : idx === 1
                  ? 'indigo'
                  : idx === 2
                  ? 'emerald'
                  : 'purple';
              const bgBar =
                idx === 0
                  ? 'bg-cyan-400'
                  : idx === 1
                  ? 'bg-indigo-400'
                  : idx === 2
                  ? 'bg-emerald-400'
                  : 'bg-purple-400';
              const textVal =
                idx === 0
                  ? 'text-cyan-300'
                  : idx === 1
                  ? 'text-indigo-300'
                  : idx === 2
                  ? 'text-emerald-300'
                  : 'text-purple-300';

              return (
                <div key={idx} className="p-2.5 rounded bg-[#070B12] border border-slate-800/80 space-y-1.5">
                  <div className="flex items-center justify-between text-xs font-mono">
                    <span className="text-slate-300 font-semibold">{cat.category}</span>
                    <span className={`${textVal} font-bold tabular-nums`}>
                      {multiple.toFixed(2)}x
                    </span>
                  </div>
                  <div className="w-full bg-slate-800 h-2 rounded-full overflow-hidden">
                    <div
                      className={`h-full ${bgBar} rounded-full transition-all`}
                      style={{ width: `${Math.min(100, multiple * 25)}%` }}
                    />
                  </div>
                </div>
              );
            })
          ) : (
            <>
              {/* Fallback Tranches */}
              <div className="p-2.5 rounded bg-[#070B12] border border-slate-800/80 space-y-1.5">
                <div className="flex items-center justify-between text-xs font-mono">
                  <span className="text-slate-300 font-semibold">QIB (Qualified Institutional Buyers)</span>
                  <span className="text-cyan-300 font-bold tabular-nums">
                    {qibMultiple.toFixed(2)}x
                  </span>
                </div>
                <div className="w-full bg-slate-800 h-2 rounded-full overflow-hidden">
                  <div
                    className="h-full bg-cyan-400 rounded-full transition-all"
                    style={{ width: `${Math.min(100, qibMultiple * 25)}%` }}
                  />
                </div>
              </div>

              <div className="p-2.5 rounded bg-[#070B12] border border-slate-800/80 space-y-1.5">
                <div className="flex items-center justify-between text-xs font-mono">
                  <span className="text-slate-300 font-semibold">NII (Non-Institutional / HNI)</span>
                  <span className="text-indigo-300 font-bold tabular-nums">
                    {niiMultiple.toFixed(2)}x
                  </span>
                </div>
                <div className="w-full bg-slate-800 h-2 rounded-full overflow-hidden">
                  <div
                    className="h-full bg-indigo-400 rounded-full transition-all"
                    style={{ width: `${Math.min(100, niiMultiple * 25)}%` }}
                  />
                </div>
              </div>

              <div className="p-2.5 rounded bg-[#070B12] border border-slate-800/80 space-y-1.5">
                <div className="flex items-center justify-between text-xs font-mono">
                  <span className="text-slate-300 font-semibold">RII (Retail Individual Investors)</span>
                  <span className="text-emerald-300 font-bold tabular-nums">
                    {retailMultiple.toFixed(2)}x
                  </span>
                </div>
                <div className="w-full bg-slate-800 h-2 rounded-full overflow-hidden">
                  <div
                    className="h-full bg-emerald-400 rounded-full transition-all"
                    style={{ width: `${Math.min(100, retailMultiple * 25)}%` }}
                  />
                </div>
              </div>
            </>
          )}
        </div>
      )}
    </div>
  );
};

export default SubscriptionBookBar;
