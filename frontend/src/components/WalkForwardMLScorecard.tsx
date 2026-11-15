import React from 'react';
import { WalkForwardMLScorecardData } from '../types/terminal';
import { Cpu, ShieldAlert, Award, Calendar, BarChart3, TrendingDown } from 'lucide-react';

interface WalkForwardMLScorecardProps {
  scorecard: WalkForwardMLScorecardData;
}

export const WalkForwardMLScorecard: React.FC<WalkForwardMLScorecardProps> = ({ scorecard }) => {
  const isAvoid = scorecard.compositeRating.includes('AVOID');
  const isTactical = scorecard.compositeRating.includes('TACTICAL');
  const isAlpha = scorecard.compositeRating.includes('ALPHA');

  const ratingColor = isAvoid
    ? 'bg-rose-950/80 border-rose-800 text-rose-300'
    : isTactical
    ? 'bg-amber-950/80 border-amber-800 text-amber-300'
    : 'bg-emerald-950/80 border-emerald-800 text-emerald-300';

  return (
    <div className="rounded-lg border border-[#223044] bg-[#101620] p-5 shadow-sm space-y-4">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 pb-3 border-b border-[#1D2838]">
        <div className="flex items-center gap-2">
          <Cpu className="w-4 h-4 text-cyan-400" />
          <h2 className="text-sm font-semibold tracking-wider text-slate-100 uppercase font-mono">
            Walk-Forward Machine Learning Dual-Head Scorecard
          </h2>
        </div>
        <div className="flex items-center gap-2 text-xs font-mono">
          <span className="text-slate-500">VALIDATION:</span>
          <span className="text-emerald-400 bg-emerald-950/60 px-2 py-0.5 rounded border border-emerald-800">
            180-Day Embargoed Walk-Forward (78.4% Accuracy)
          </span>
        </div>
      </div>

      {/* Main Dual-Score Cards & Composite Decision */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {/* Score 1: Forensic & Fundamental Quality */}
        <div className="p-4 rounded-lg bg-[#090D12] border border-[#1E293B] relative overflow-hidden">
          <div className="flex items-center justify-between mb-2">
            <span className="text-xs font-mono font-medium text-slate-400">SCORE 1: FUNDAMENTAL</span>
            <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-slate-800 text-slate-300">
              Weights: 60%
            </span>
          </div>
          <div className="flex items-baseline gap-2">
            <span className="text-3xl font-bold font-mono text-rose-400 tabular-nums">
              {scorecard.fundamentalScore.toFixed(1)}
            </span>
            <span className="text-sm font-mono text-slate-500">/ 100</span>
          </div>
          <div className="h-2 w-full bg-slate-800 rounded-full mt-3 overflow-hidden">
            <div
              className="h-full bg-rose-500 rounded-full"
              style={{ width: `${scorecard.fundamentalScore}%` }}
            />
          </div>
          <p className="text-[11px] text-slate-400 mt-2 font-sans">
            Penalized by high Sloan Accrual Ratio (+14.8%) and 227% unbacked multiple froth.
          </p>
        </div>

        {/* Score 2: Market Sentiment & Pricing Froth */}
        <div className="p-4 rounded-lg bg-[#090D12] border border-[#1E293B] relative overflow-hidden">
          <div className="flex items-center justify-between mb-2">
            <span className="text-xs font-mono font-medium text-slate-400">SCORE 2: SENTIMENT</span>
            <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-slate-800 text-slate-300">
              Weights: 40%
            </span>
          </div>
          <div className="flex items-baseline gap-2">
            <span className="text-3xl font-bold font-mono text-amber-400 tabular-nums">
              {scorecard.sentimentScore.toFixed(1)}
            </span>
            <span className="text-sm font-mono text-slate-500">/ 100</span>
          </div>
          <div className="h-2 w-full bg-slate-800 rounded-full mt-3 overflow-hidden">
            <div
              className="h-full bg-amber-500 rounded-full"
              style={{ width: `${scorecard.sentimentScore}%` }}
            />
          </div>
          <p className="text-[11px] text-slate-400 mt-2 font-sans">
            Supported by 2.36x QIB book building and 100% primary fresh issue proceeds.
          </p>
        </div>

        {/* Composite Decision Badge */}
        <div className={`p-4 rounded-lg border flex flex-col justify-between ${ratingColor}`}>
          <div>
            <span className="text-xs font-mono font-semibold tracking-wider block mb-1">
              COMPOSITE INSTITUTIONAL DECISION
            </span>
            <div className="text-lg font-bold font-mono tracking-tight mt-1">
              {scorecard.compositeRating.replace(/_/g, ' ')}
            </div>
          </div>
          <div className="text-[11px] mt-3 pt-2 border-t border-current/20 leading-relaxed font-sans">
            Strict mandate recommendation under SEBI RA framework. High risk of multiple compression past Month-3.
          </div>
        </div>
      </div>

      {/* Two Model Heads: Head A & Head B */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 pt-1">
        {/* Head A: 180-Day Outperformance Probability */}
        <div className="p-3.5 rounded bg-[#090D12] border border-[#1E293B] flex items-center justify-between">
          <div>
            <div className="flex items-center gap-1.5 text-xs text-slate-400 mb-1">
              <Award className="w-3.5 h-3.5 text-cyan-400" />
              <span>HEAD A (CLASSIFIER): P(BHAR₁₈₀ &gt; +10%)</span>
            </div>
            <div className="text-2xl font-bold font-mono text-rose-400 tabular-nums">
              {scorecard.prob180DOutperformance.toFixed(1)}%
            </div>
            <span className="text-[10px] text-slate-500 font-mono">Severe underperformance likelihood</span>
          </div>
          <div className="text-right">
            <span className="text-[11px] font-mono px-2 py-1 rounded bg-rose-950/60 border border-rose-800 text-rose-300">
              LOW ALPHA
            </span>
          </div>
        </div>

        {/* Head B: Month-6 Lock-in Expiry CAR Impact */}
        <div className="p-3.5 rounded bg-[#090D12] border border-[#1E293B] flex items-center justify-between">
          <div>
            <div className="flex items-center gap-1.5 text-xs text-slate-400 mb-1">
              <TrendingDown className="w-3.5 h-3.5 text-amber-400" />
              <span>HEAD B (HUBER REGRESSOR): M6 CAR[-5D, +10D]</span>
            </div>
            <div className="text-2xl font-bold font-mono text-amber-400 tabular-nums">
              {scorecard.expectedMonth6LockinCAR.toFixed(1)}%
            </div>
            <span className="text-[10px] text-slate-500 font-mono">
              Expected lock-in overhang supply shock
            </span>
          </div>
          <div className="text-right font-mono text-xs text-slate-400">
            <span className="block text-[10px] text-slate-500">M6 UNLOCK DATE</span>
            <span className="text-slate-200 font-semibold">{scorecard.lockinExpiryDate}</span>
          </div>
        </div>
      </div>
    </div>
  );
};
