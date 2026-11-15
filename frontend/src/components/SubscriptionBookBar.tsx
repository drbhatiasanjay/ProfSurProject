import React from 'react';
import { SubscriptionBook } from '../types/terminal';
import { Users, TrendingUp, CheckCircle, AlertCircle } from 'lucide-react';

interface SubscriptionBookBarProps {
  subscription: SubscriptionBook;
}

export const SubscriptionBookBar: React.FC<SubscriptionBookBarProps> = ({ subscription }) => {
  return (
    <div className="rounded-lg border border-[#223044] bg-[#101620] p-5 shadow-sm">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 pb-3 border-b border-[#1D2838]">
        <div className="flex items-center gap-2">
          <TrendingUp className="w-4 h-4 text-cyan-400" />
          <h2 className="text-sm font-semibold tracking-wider text-slate-100 uppercase font-mono">
            NSE Live Order Book & Category Demand
          </h2>
        </div>
        <div className="flex items-center gap-3 text-xs font-mono">
          <span className="text-slate-500">LAST SYNC:</span>
          <span className="text-slate-300">{subscription.lastUpdated}</span>
        </div>
      </div>

      {/* Aggregate Overview Stat Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 my-4">
        <div className="p-3 rounded bg-[#090D12] border border-[#1E293B] flex items-center justify-between">
          <div>
            <span className="text-[11px] text-slate-400 block">Total Issue Subscription</span>
            <span className="text-xl font-bold font-mono text-emerald-400 tabular-nums">
              {subscription.totalMultiple.toFixed(2)}x
            </span>
          </div>
          <div className="p-2 rounded bg-emerald-950/40 border border-emerald-800/60">
            <CheckCircle className="w-4 h-4 text-emerald-400" />
          </div>
        </div>

        <div className="p-3 rounded bg-[#090D12] border border-[#1E293B] flex items-center justify-between">
          <div>
            <span className="text-[11px] text-slate-400 block">Total Shares Bid</span>
            <span className="text-xl font-bold font-mono text-slate-100 tabular-nums">
              {(subscription.totalBidsShares / 1e7).toFixed(2)} Cr
            </span>
          </div>
          <div className="p-2 rounded bg-slate-800 border border-slate-700">
            <Users className="w-4 h-4 text-cyan-400" />
          </div>
        </div>

        <div className="p-3 rounded bg-[#090D12] border border-[#1E293B] flex items-center justify-between">
          <div>
            <span className="text-[11px] text-slate-400 block">Total Capital Committed</span>
            <span className="text-xl font-bold font-mono text-cyan-400 tabular-nums">
              ₹{subscription.totalAmountCollectedCr.toLocaleString('en-IN', { minimumFractionDigits: 2 })} Cr
            </span>
          </div>
          <div className="text-[10px] text-slate-500 font-mono text-right">
            116.6% of Issue Size
          </div>
        </div>
      </div>

      {/* Categorical Breakdown Bars */}
      <div className="space-y-3.5">
        {subscription.categories.map((cat) => {
          const isOver = cat.subscriptionMultiple >= 1.0;
          const pctWidth = Math.min(Math.max((cat.subscriptionMultiple / 3.0) * 100, 6), 100);

          return (
            <div key={cat.category} className="space-y-1.5">
              <div className="flex items-center justify-between text-xs">
                <span className="font-medium text-slate-300 font-sans">{cat.category}</span>
                <div className="flex items-center gap-3 font-mono">
                  <span className="text-[11px] text-slate-400">
                    {(cat.sharesBid / 1e7).toFixed(2)} Cr bids / {(cat.sharesOffered / 1e7).toFixed(2)} Cr quota
                  </span>
                  <span
                    className={`font-bold tabular-nums px-1.5 py-0.5 rounded text-[11px] ${
                      isOver
                        ? 'bg-emerald-950/60 border border-emerald-800 text-emerald-400'
                        : 'bg-amber-950/60 border border-amber-800 text-amber-400'
                    }`}
                  >
                    {cat.subscriptionMultiple.toFixed(2)}x
                  </span>
                </div>
              </div>

              {/* Progress Track */}
              <div className="h-2 w-full rounded-full bg-[#090D12] border border-[#1E293B] overflow-hidden">
                <div
                  className={`h-full rounded-full transition-all duration-500 ${
                    isOver ? 'bg-gradient-to-r from-emerald-600 to-emerald-400' : 'bg-gradient-to-r from-amber-600 to-amber-400'
                  }`}
                  style={{ width: `${pctWidth}%` }}
                />
              </div>
            </div>
          );
        })}
      </div>

      {/* Institutional Divergence Insight Note */}
      <div className="mt-4 p-2.5 rounded bg-[#090D12] border border-[#1E293B] flex items-start gap-2 text-xs">
        <AlertCircle className="w-3.5 h-3.5 text-cyan-400 shrink-0 mt-0.5" />
        <p className="text-slate-400 leading-relaxed font-sans">
          <strong className="text-slate-200">Institutional Appetite Divergence:</strong> QIB allocation is oversubscribed by{' '}
          <span className="text-emerald-400 font-mono font-semibold">2.36x</span> driven by domestic mutual funds and sovereign wealth anchors, while NII (HNI) category trails at{' '}
          <span className="text-amber-400 font-mono font-semibold">0.85x</span>, signaling limited leverage arbitrage interest in primary gray-market financing.
        </p>
      </div>
    </div>
  );
};
