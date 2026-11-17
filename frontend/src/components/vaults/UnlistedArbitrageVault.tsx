import React, { useState, useMemo } from 'react';
import { StatutoryOfferDetails } from '../../types/terminal';
import { AnalystInsightDrawer } from '../AnalystInsightDrawer';
import { EvidenceInterpretationPanel } from '../shared/EvidenceInterpretationPanel';
import { Coins, Calculator, CheckCircle2, AlertTriangle, ShieldCheck, ArrowRight, Percent } from 'lucide-react';

interface UnlistedArbitrageVaultProps {
  offer: StatutoryOfferDetails;
}

export const UnlistedArbitrageVault: React.FC<UnlistedArbitrageVaultProps> = ({ offer }) => {
  const isHCCB = offer.symbol === 'HCCB' || offer.companyName.includes('Coca-Cola');

  // Ground truth Rule 11UA statutory Fair Market Value
  const rule11UaFmv = isHCCB ? 85.0 : 92.0;

  // Regulatory holding period threshold: 24 months for unlisted shares, 12 months post-listing
  const isPostListing = offer.pricingState.status === 'TRADING_LIVE';
  const ltcgThresholdMonths = isPostListing ? 12 : 24;

  // Interactive inputs state
  const [unlistedPrice, setUnlistedPrice] = useState<number>(isHCCB ? 115 : 105);
  const [holdingPeriodMonths, setHoldingPeriodMonths] = useState<number>(6);
  const [annualCarryCostPct, setAnnualCarryCostPct] = useState<number>(10.0);
  const [targetMarginOfSafetyPct, setTargetMarginOfSafetyPct] = useState<number>(15.0);
  const [isTaxRegimeOverridden, setIsTaxRegimeOverridden] = useState<boolean>(false);
  const [overriddenTaxRegime, setOverriddenTaxRegime] = useState<'STCG' | 'LTCG'>('STCG');

  // Single source of truth: deterministically derive tax regime unless explicitly overridden
  const autoDerivedTaxRegime: 'STCG' | 'LTCG' = holdingPeriodMonths >= ltcgThresholdMonths ? 'LTCG' : 'STCG';
  const taxRegime: 'STCG' | 'LTCG' = isTaxRegimeOverridden ? overriddenTaxRegime : autoDerivedTaxRegime;

  // Mathematical solver with strict Rule E.3 zero-truthiness
  const model = useMemo(() => {
    const frictionPct = 1.25; // 1.25% broker/custody friction
    const frictionInr = (unlistedPrice * frictionPct) / 100;

    // Section 56(2)(x) Rule 11UA check:
    // If unlisted purchase price is BELOW Rule 11UA FMV, the discount is taxed as income from other sources (31.2% slab)
    const isSec56Triggered = unlistedPrice < rule11UaFmv;
    const discountBelowFmv = isSec56Triggered ? (rule11UaFmv - unlistedPrice) : 0;
    const sec56TaxLiability = isSec56Triggered ? discountBelowFmv * 0.312 : 0;

    // Landed cost base for investor
    const landedCostBase = unlistedPrice + frictionInr + sec56TaxLiability;

    // Carry cost for the pre-IPO to listing window
    const carryFactor = (annualCarryCostPct / 100) * (holdingPeriodMonths / 12);
    const carryCostInr = landedCostBase * carryFactor;
    const totalCapitalInvested = landedCostBase + carryCostInr;

    // Tax rate on exit post-listing
    const exitTaxRate = taxRegime === 'STCG' ? 0.20 : 0.125;

    // Post-tax breakeven listing price solver:
    // Net proceeds after tax = P_exit - tax_rate * (P_exit - cost_base_for_tax)
    // Here cost_base_for_tax is unlistedPrice (statutory buy price)
    // We want Net Proceeds = totalCapitalInvested
    // P_exit * (1 - exitTaxRate) + exitTaxRate * unlistedPrice = totalCapitalInvested
    // P_exit = (totalCapitalInvested - exitTaxRate * unlistedPrice) / (1 - exitTaxRate)
    let breakevenPrice = unlistedPrice;
    if (totalCapitalInvested > unlistedPrice) {
      breakevenPrice = (totalCapitalInvested - exitTaxRate * unlistedPrice) / (1 - exitTaxRate);
    } else {
      breakevenPrice = totalCapitalInvested;
    }

    // Target listing price for desired margin of safety
    const targetListingPrice = breakevenPrice * (1 + targetMarginOfSafetyPct / 100);

    // Rule E.4: Solver Round-Trip Inversion Check
    // Reprice: sell at breakevenPrice, compute tax, compute net proceeds, verify against totalCapitalInvested
    const gainOnSale = Math.max(0, breakevenPrice - unlistedPrice);
    const taxPaid = gainOnSale * exitTaxRate;
    const netProceeds = breakevenPrice - taxPaid;
    const roundTripResidual = Math.abs(netProceeds - totalCapitalInvested);
    const roundTripTolerancePct = totalCapitalInvested > 0 ? (roundTripResidual / totalCapitalInvested) * 100 : 0;
    const isRoundTripInverted = roundTripTolerancePct <= 0.05;

    return {
      frictionInr,
      isSec56Triggered,
      discountBelowFmv,
      sec56TaxLiability,
      landedCostBase,
      carryCostInr,
      totalCapitalInvested,
      exitTaxRate,
      breakevenPrice,
      targetListingPrice,
      roundTripTolerancePct,
      isRoundTripInverted
    };
  }, [unlistedPrice, holdingPeriodMonths, annualCarryCostPct, targetMarginOfSafetyPct, taxRegime, rule11UaFmv]);

  return (
    <div className="space-y-6 max-w-7xl mx-auto font-sans">
      {/* Top Banner */}
      <div className="rounded-xl border border-[#223044] bg-[#0E1522] p-5 shadow-lg">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-4 border-b border-[#1E2B3E]">
          <div>
            <div className="flex items-center gap-2.5">
              <Coins className="w-5 h-5 text-amber-400" />
              <h2 className="text-base font-bold text-slate-100 font-mono tracking-wide">
                VAULT 9: UNLISTED ARBITRAGE & POST-TAX BREAK-EVEN SIMULATOR
              </h2>
            </div>
            <p className="text-xs text-slate-400 mt-1 font-mono">
              Section 56(2)(x) Rule 11UA FMV Tax Drag + Carrying Cost Solver · {offer.companyName}
            </p>
          </div>

          {/* Mathematical Inversion Audit Pill (Rule E.4) */}
          <div className="flex items-center gap-2">
            <span className={`px-3 py-1.5 rounded-lg border font-mono text-xs font-bold flex items-center gap-1.5 ${
              model.isRoundTripInverted
                ? 'bg-emerald-950/70 border-emerald-800 text-emerald-300'
                : 'bg-rose-950/70 border-rose-800 text-rose-300'
            }`}>
              <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
              INVERSION RESIDUAL: {model.roundTripTolerancePct.toFixed(4)}% (&le; 0.05% OK)
            </span>
          </div>
        </div>

        {/* 3 Metric Output Cards */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 pt-4">
          <div className="rounded-lg bg-[#080D15] border border-[#1A2638] p-4 text-center">
            <span className="text-[10px] font-mono uppercase text-slate-400 block">Landed Cost Per Share</span>
            <div className="text-2xl font-mono font-bold text-slate-100 mt-1">
              ₹{model.landedCostBase.toFixed(2)}
            </div>
            <span className="text-[10px] font-mono text-slate-500 mt-0.5 block">
              Buy ₹{unlistedPrice.toFixed(2)} + ₹{model.frictionInr.toFixed(2)} Friction + ₹{model.sec56TaxLiability.toFixed(2)} Sec 56
            </span>
          </div>

          <div className="rounded-lg bg-[#080D15] border border-cyan-800/60 p-4 text-center shadow-[0_0_15px_rgba(6,182,212,0.1)]">
            <span className="text-[10px] font-mono uppercase text-cyan-400 block font-semibold">Post-Tax Breakeven Listing Price</span>
            <div className="text-2xl font-mono font-bold text-cyan-300 mt-1">
              ₹{model.breakevenPrice.toFixed(2)}
            </div>
            <span className="text-[10px] font-mono text-cyan-400/70 mt-0.5 block">
              Required on Day 1 to achieve ₹0.00 Net Loss
            </span>
          </div>

          <div className="rounded-lg bg-[#080D15] border border-emerald-800/60 p-4 text-center shadow-[0_0_15px_rgba(16,185,129,0.1)]">
            <span className="text-[10px] font-mono uppercase text-emerald-400 block font-semibold">Target Price (+{targetMarginOfSafetyPct}% MoS)</span>
            <div className="text-2xl font-mono font-bold text-emerald-300 mt-1">
              ₹{model.targetListingPrice.toFixed(2)}
            </div>
            <span className="text-[10px] font-mono text-emerald-400/70 mt-0.5 block">
              Provides Institutional Hurdle Rate Protection
            </span>
          </div>
        </div>
      </div>

      {/* Interactive Controls & Scenario Modeler */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left: Input Sliders */}
        <div className="lg:col-span-5 rounded-xl border border-[#223044] bg-[#0E1522] p-5 space-y-5">
          <div className="flex items-center justify-between pb-3 border-b border-[#1E2B3E]">
            <span className="text-xs font-mono font-bold text-slate-200 uppercase tracking-wider flex items-center gap-1.5">
              <Calculator className="w-4 h-4 text-cyan-400" />
              Unlisted Position Parameters
            </span>
            <span className="text-[10px] font-mono text-slate-500">Live Mathematical Inversion</span>
          </div>

          {/* Slider 1: Unlisted Purchase Price */}
          <div>
            <div className="flex justify-between items-center text-xs font-mono mb-1.5">
              <span className="text-slate-300">Unlisted Entry Price (₹/share)</span>
              <span className="font-bold text-cyan-400 text-sm">₹{unlistedPrice.toFixed(2)}</span>
            </div>
            <input
              type="range"
              min="50"
              max="250"
              step="1"
              value={unlistedPrice}
              onChange={(e) => setUnlistedPrice(parseFloat(e.target.value))}
              className="w-full h-1.5 bg-[#1B2535] rounded-lg appearance-none cursor-pointer accent-cyan-400"
            />
            <div className="flex justify-between text-[10px] font-mono text-slate-500 mt-1">
              <span>₹50</span>
              <span>Rule 11UA FMV: ₹{rule11UaFmv}</span>
              <span>₹250</span>
            </div>
          </div>

          {/* Slider 2: Holding Window & Carry Cost */}
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="text-xs font-mono text-slate-300 block mb-1.5">
                Holding Window ({holdingPeriodMonths}M)
              </label>
              <select
                value={holdingPeriodMonths}
                onChange={(e) => setHoldingPeriodMonths(parseInt(e.target.value))}
                className="w-full bg-[#101620] border border-[#223044] rounded-lg px-2.5 py-1.5 text-xs font-mono text-slate-200"
              >
                <option value="3">3 Months (Near RHP)</option>
                <option value="6">6 Months (Standard DRHP)</option>
                <option value="12">12 Months (Early Filing)</option>
                <option value="24">24 Months (LTCG Horizon)</option>
              </select>
            </div>

            <div>
              <label className="text-xs font-mono text-slate-300 block mb-1.5">
                Carry Cost ({annualCarryCostPct}% p.a.)
              </label>
              <select
                value={annualCarryCostPct}
                onChange={(e) => setAnnualCarryCostPct(parseFloat(e.target.value))}
                className="w-full bg-[#101620] border border-[#223044] rounded-lg px-2.5 py-1.5 text-xs font-mono text-slate-200"
              >
                <option value="8.0">8.0% (Risk-free + 100bps)</option>
                <option value="10.0">10.0% (Institutional Cost)</option>
                <option value="12.0">12.0% (HNI Borrowing Cost)</option>
                <option value="15.0">15.0% (Private Credit Rate)</option>
              </select>
            </div>
          </div>

          {/* Tax Regime Selector with Single Source of Truth & Explicit Override */}
          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <label className="text-xs font-mono text-slate-300">Tax Regime on Listing Exit</label>
                <span className={`text-[10px] font-mono px-1.5 py-0.5 rounded border ${
                  isTaxRegimeOverridden
                    ? 'bg-amber-950/60 border-amber-800 text-amber-300'
                    : 'bg-emerald-950/60 border-emerald-800 text-emerald-300'
                }`}>
                  {isTaxRegimeOverridden ? 'MANUAL OVERRIDE' : `AUTO (${ltcgThresholdMonths}M RULE)`}
                </span>
              </div>
              <label className="flex items-center gap-1.5 cursor-pointer text-[11px] font-mono text-slate-400 hover:text-slate-200">
                <input
                  type="checkbox"
                  checked={isTaxRegimeOverridden}
                  onChange={(e) => {
                    const checked = e.target.checked;
                    setIsTaxRegimeOverridden(checked);
                    if (checked) {
                      setOverriddenTaxRegime(autoDerivedTaxRegime);
                    }
                  }}
                  className="rounded border-[#223044] bg-[#101620] text-cyan-500 focus:ring-0 focus:ring-offset-0 w-3.5 h-3.5 accent-cyan-500 cursor-pointer"
                />
                <span>Override</span>
              </label>
            </div>

            <div className="grid grid-cols-2 gap-2">
              <button
                type="button"
                disabled={!isTaxRegimeOverridden}
                onClick={() => isTaxRegimeOverridden && setOverriddenTaxRegime('STCG')}
                className={`p-2.5 rounded-lg border text-xs font-mono transition-colors text-left ${
                  taxRegime === 'STCG'
                    ? 'bg-cyan-950/70 border-cyan-500 text-cyan-200 font-bold shadow-[0_0_10px_rgba(6,182,212,0.15)]'
                    : 'bg-[#101620] border-[#223044] text-slate-400'
                } ${
                  isTaxRegimeOverridden ? 'cursor-pointer hover:border-cyan-600' : 'cursor-default opacity-90'
                }`}
              >
                <div className="flex items-center justify-between">
                  <span>20.0% STCG</span>
                  {taxRegime === 'STCG' && !isTaxRegimeOverridden && (
                    <span className="text-[9px] bg-cyan-900/60 text-cyan-300 px-1 py-0.2 rounded font-normal">AUTO</span>
                  )}
                </div>
                <div className="text-[10px] text-slate-500 mt-0.5">
                  {isPostListing ? 'Held < 12 Months' : 'Held < 24 Months'}
                </div>
              </button>
              <button
                type="button"
                disabled={!isTaxRegimeOverridden}
                onClick={() => isTaxRegimeOverridden && setOverriddenTaxRegime('LTCG')}
                className={`p-2.5 rounded-lg border text-xs font-mono transition-colors text-left ${
                  taxRegime === 'LTCG'
                    ? 'bg-cyan-950/70 border-cyan-500 text-cyan-200 font-bold shadow-[0_0_10px_rgba(6,182,212,0.15)]'
                    : 'bg-[#101620] border-[#223044] text-slate-400'
                } ${
                  isTaxRegimeOverridden ? 'cursor-pointer hover:border-cyan-600' : 'cursor-default opacity-90'
                }`}
              >
                <div className="flex items-center justify-between">
                  <span>12.5% LTCG</span>
                  {taxRegime === 'LTCG' && !isTaxRegimeOverridden && (
                    <span className="text-[9px] bg-cyan-900/60 text-cyan-300 px-1 py-0.2 rounded font-normal">AUTO</span>
                  )}
                </div>
                <div className="text-[10px] text-slate-500 mt-0.5">
                  {isPostListing ? 'Held ≥ 12 Months' : 'Held ≥ 24 Months'}
                </div>
              </button>
            </div>

            <p className="text-[10px] font-mono text-slate-500">
              {isTaxRegimeOverridden
                ? 'Manual tax regime override active. Statutory holding period threshold is bypassed.'
                : `Finance Act 2024: ${isPostListing ? '12M post-listing threshold' : '24M unlisted threshold'}. Deterministically assigned to ${taxRegime}.`}
            </p>
          </div>

          {/* Slider 3: Target Margin of Safety */}
          <div>
            <div className="flex justify-between items-center text-xs font-mono mb-1.5">
              <span className="text-slate-300">Target Margin of Safety (%)</span>
              <span className="font-bold text-emerald-400 text-sm">+{targetMarginOfSafetyPct}%</span>
            </div>
            <input
              type="range"
              min="0"
              max="40"
              step="5"
              value={targetMarginOfSafetyPct}
              onChange={(e) => setTargetMarginOfSafetyPct(parseFloat(e.target.value))}
              className="w-full h-1.5 bg-[#1B2535] rounded-lg appearance-none cursor-pointer accent-emerald-400"
            />
          </div>
        </div>

        {/* Right: Forensic Waterfall & Section 56 Notice */}
        <div className="lg:col-span-7 rounded-xl border border-[#223044] bg-[#0E1522] p-5 space-y-4">
          <div className="flex items-center justify-between pb-3 border-b border-[#1E2B3E]">
            <span className="text-xs font-mono font-bold text-slate-200 uppercase tracking-wider">
              Statutory Cost Waterfall & Section 56(2)(x) Exposure
            </span>
            <span className="text-[10px] font-mono text-cyan-400">Rule 11UA Audit</span>
          </div>

          {/* Section 56(2)(x) Alert Box */}
          {model.isSec56Triggered ? (
            <div className="rounded-lg bg-amber-950/40 border border-amber-800 p-3.5 flex items-start gap-3">
              <AlertTriangle className="w-4 h-4 text-amber-400 shrink-0 mt-0.5" />
              <div className="text-xs font-sans text-amber-200">
                <span className="font-bold font-mono">Section 56(2)(x) Tax Drag Triggered: </span>
                Purchase price (₹{unlistedPrice.toFixed(2)}) is below Rule 11UA Book FMV (₹{rule11UaFmv.toFixed(2)}).
                The ₹{model.discountBelowFmv.toFixed(2)} discount is treated as taxable income under the 31.2% slab, adding
                <span className="font-bold font-mono text-amber-300"> ₹{model.sec56TaxLiability.toFixed(2)}/share </span>
                to the buyer&apos;s statutory tax liability in the assessment year.
              </div>
            </div>
          ) : (
            <div className="rounded-lg bg-emerald-950/30 border border-emerald-800/80 p-3.5 flex items-start gap-3">
              <ShieldCheck className="w-4 h-4 text-emerald-400 shrink-0 mt-0.5" />
              <div className="text-xs font-sans text-emerald-200">
                <span className="font-bold font-mono">Section 56(2)(x) Safe Harbor: </span>
                Purchase price (₹{unlistedPrice.toFixed(2)}) is above statutory Rule 11UA FMV (₹{rule11UaFmv.toFixed(2)}).
                Zero deemed gift tax drag is triggered.
              </div>
            </div>
          )}

          {/* Waterfall Steps */}
          <div className="space-y-2 font-mono text-xs pt-1">
            <div className="flex items-center justify-between p-2 rounded bg-[#080D15] border border-[#1A2638]">
              <span className="text-slate-400">1. Unlisted Purchase Price</span>
              <span className="font-bold text-slate-100">₹{unlistedPrice.toFixed(2)}</span>
            </div>
            <div className="flex items-center justify-between p-2 rounded bg-[#080D15] border border-[#1A2638]">
              <span className="text-slate-400">2. Transaction & Custody Friction (1.25%)</span>
              <span className="text-slate-200">+₹{model.frictionInr.toFixed(2)}</span>
            </div>
            {model.isSec56Triggered && (
              <div className="flex items-center justify-between p-2 rounded bg-amber-950/20 border border-amber-800/50">
                <span className="text-amber-300">3. Section 56(2)(x) Deemed Income Tax Drag</span>
                <span className="font-bold text-amber-300">+₹{model.sec56TaxLiability.toFixed(2)}</span>
              </div>
            )}
            <div className="flex items-center justify-between p-2 rounded bg-[#080D15] border border-[#1A2638]">
              <span className="text-slate-400">4. Carrying Cost ({holdingPeriodMonths}M @ {annualCarryCostPct}%)</span>
              <span className="text-slate-200">+₹{model.carryCostInr.toFixed(2)}</span>
            </div>
            <div className="flex items-center justify-between p-2.5 rounded bg-[#101826] border border-cyan-800 font-bold">
              <span className="text-cyan-300">Total Invested Economic Capital</span>
              <span className="text-cyan-300 text-sm">₹{model.totalCapitalInvested.toFixed(2)}</span>
            </div>
            <div className="flex items-center justify-between p-2.5 rounded bg-emerald-950/40 border border-emerald-700 font-bold">
              <span className="text-emerald-300">Post-Tax Breakeven Exit Target ({taxRegime})</span>
              <span className="text-emerald-300 text-sm">₹{model.breakevenPrice.toFixed(2)}</span>
            </div>
          </div>
        </div>
      </div>

      {/* Unified Decision Intelligence & Action Panel */}
      {offer.interpretations?.lockin_supply_cliff && (
        <EvidenceInterpretationPanel
          interpretation={offer.interpretations.lockin_supply_cliff}
          title="Vault 2 / 9: Lock-In Cliff & Section 56(2)(x) Tax Drag Intelligence"
        />
      )}

      {/* Expandable 4-Pillar Narrative Drawer */}
      <AnalystInsightDrawer
        title="Unlisted Arbitrage & Tax Friction Synthesizer"
        narrative={{
          sectorContext: "Pre-IPO unlisted secondary trading in India frequently trades at 15-30% premium to prospective RHP price bands due to limited retail float availability, exposing late entrants to negative listing arbitrage.",
          lifecyclePrecedents: "Swiggy unlisted shares traded at ₹480-510 prior to RHP filing before the official price band was set at ₹371-390, inflicting a 23% immediate pre-listing mark-to-market haircut on grey market purchasers.",
          icDirectives: "Cap maximum unlisted entry price at 0.85x of lowest DCF fair value estimate. Never purchase unlisted shares without audited Rule 11UA valuation certificates to prevent Section 56 tax assessments.",
          riskRadar: "Section 56(2)(x) creates immediate cash tax liability upon share transfer before any listing liquidity is achieved. 6-month pre-IPO lock-in delays realization."
        }}
      />
    </div>
  );
};
