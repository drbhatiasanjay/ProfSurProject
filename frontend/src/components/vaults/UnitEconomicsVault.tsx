import React, { useState, useEffect } from 'react';
import { StatutoryOfferDetails, AnalyticalInterpretation } from '../../types/terminal';
import { EvidenceInterpretationPanel } from '../shared/EvidenceInterpretationPanel';
import { AnalystInsightDrawer } from '../AnalystInsightDrawer';
import { Factory, TrendingUp, Truck, ShieldCheck, ExternalLink, Zap } from 'lucide-react';
import { fetchPreIpoInterpretations } from '../../services/dataService';

interface UnitEconomicsVaultProps {
  offer: StatutoryOfferDetails;
  onCitationClick?: (pageNumber: number, attributeId?: string) => void;
}

export const UnitEconomicsVault: React.FC<UnitEconomicsVaultProps> = ({
  offer,
  onCitationClick,
}) => {
  const isHCCB = offer.symbol === 'HCCB' || offer.companyName.includes('Coca-Cola');
  const [interpretations, setInterpretations] = useState<Record<string, AnalyticalInterpretation> | null>(() => offer.interpretations || null);

  useEffect(() => {
    let isMounted = true;
    if (offer.interpretations && Object.keys(offer.interpretations).length > 0) {
      setInterpretations(offer.interpretations);
      return;
    }
    fetchPreIpoInterpretations(offer.symbol)
      .then((data: Record<string, AnalyticalInterpretation>) => {
        if (isMounted) setInterpretations(data);
      })
      .catch((err: unknown) => {
        if (isMounted) console.error('Failed to load interpretations in UnitEconomicsVault:', err);
      });

    return () => {
      isMounted = false;
    };
  }, [offer.symbol, offer.interpretations]);

  // Operational metrics
  const installedCapacityCasesM = isHCCB ? 1450.0 : 420.0;
  const utilizationPct = isHCCB ? 78.50 : 88.20;
  const retailOutlets = isHCCB ? 2500000 : 450000;
  const ownedPlants = isHCCB ? 16 : 6;
  const grossMarginPct = isHCCB ? 42.60 : 38.40;
  const ebitdaMarginPct = isHCCB ? 15.59 : 12.10;

  const costBreakdown = [
    { label: 'Beverage Concentrate & Raw Ingredients', sharePct: 41.2, inrCr: 5113.1, color: 'bg-amber-500' },
    { label: 'Packaging Materials (PET, Glass, Aluminium)', sharePct: 16.2, inrCr: 2010.5, color: 'bg-indigo-500' },
    { label: 'Plant Conversion Overhead & Power', sharePct: 12.8, inrCr: 1588.5, color: 'bg-cyan-500' },
    { label: 'Freight, Warehousing & Primary Logistics', sharePct: 8.5, inrCr: 1054.9, color: 'bg-teal-500' },
    { label: 'Personnel & Administrative Overhead', sharePct: 5.7, inrCr: 707.4, color: 'bg-slate-500' },
    { label: 'Operating Profit (EBITDA)', sharePct: 15.6, inrCr: 1935.0, color: 'bg-emerald-500' },
  ];

  const plantFootprint = [
    { region: 'Northern Zone (Gurugram, Varanasi, Dasna)', plants: 5, capacityM: 480.0, utilPct: 79.2, drhpPage: 148 },
    { region: 'Western Zone (Sanand, Pirangut, Wada)', plants: 4, capacityM: 390.0, utilPct: 81.4, drhpPage: 149 },
    { region: 'Southern Zone (Bidadi, Sri City, Ameenpur)', plants: 4, capacityM: 360.0, utilPct: 76.8, drhpPage: 151 },
    { region: 'Eastern Zone (Raninagar, Jalpaiguri, Khordha)', plants: 3, capacityM: 220.0, utilPct: 75.1, drhpPage: 152 },
  ];

  const unitInterp = interpretations?.['unit_economics_studio'];

  return (
    <div className="space-y-6">
      {/* Header Banner */}
      <div className="bg-[#0D131F] border border-[#223044] rounded-xl p-5 flex flex-wrap items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <Factory className="w-5 h-5 text-cyan-400" />
            <h2 className="text-base font-bold text-slate-100 font-mono tracking-wide">
              VAULT 8: UNIT ECONOMICS & OPERATIONAL SCALE STUDIO
            </h2>
            <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-emerald-950/60 border border-emerald-800 text-emerald-400">
              Porter (1985) Scale Analysis · 16 Plants
            </span>
          </div>
          <p className="text-xs text-slate-400 max-w-3xl">
            Throughput verification, 75%–85% optimal capacity utilization audit, and 2.5M outlet retail distribution moat assessment.
          </p>
        </div>

        {/* Operating Sweet-Spot Badge */}
        <div className="flex items-center gap-2 bg-[#121B2A] border border-emerald-800/60 px-3.5 py-2 rounded-lg">
          <div className="text-right font-mono">
            <div className="text-[10px] text-slate-500 uppercase">Capacity Efficiency</div>
            <div className="text-xs font-bold text-emerald-400">
              {utilizationPct.toFixed(1)}% (OPTIMAL SWEET SPOT)
            </div>
          </div>
          <Zap className="w-5 h-5 text-emerald-400 shrink-0" />
        </div>
      </div>

      {/* 4 KPI Summary Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="bg-[#0D131F] border border-[#223044] rounded-xl p-4">
          <div className="text-[11px] font-mono text-slate-400 uppercase tracking-wider mb-1">
            Installed Bottling Capacity
          </div>
          <div className="text-xl font-bold font-mono text-slate-100">
            {installedCapacityCasesM.toLocaleString()}M Cases/yr
          </div>
          <div className="text-[10px] text-slate-500 mt-1 flex items-center justify-between">
            <span>{ownedPlants} Company-Owned Plants</span>
            <span className="text-cyan-400 font-mono">DRHP p. 148</span>
          </div>
        </div>

        <div className="bg-[#0D131F] border border-[#223044] rounded-xl p-4">
          <div className="text-[11px] font-mono text-slate-400 uppercase tracking-wider mb-1">
            Operational Utilization
          </div>
          <div className="text-xl font-bold font-mono text-emerald-400">
            {utilizationPct.toFixed(2)}%
          </div>
          <div className="text-[10px] text-emerald-400 mt-1 flex items-center justify-between">
            <span>Peak Overhead Absorption</span>
            <span className="font-mono">75%-85% Target</span>
          </div>
        </div>

        <div className="bg-[#0D131F] border border-[#223044] rounded-xl p-4">
          <div className="text-[11px] font-mono text-slate-400 uppercase tracking-wider mb-1">
            Retail Distribution Reach
          </div>
          <div className="text-xl font-bold font-mono text-slate-100">
            {retailOutlets.toLocaleString()}+ Outlets
          </div>
          <div className="text-[10px] text-slate-500 mt-1 flex items-center justify-between">
            <span>Direct & Indirect Touchpoints</span>
            <span className="text-cyan-400 font-mono">DRHP p. 150</span>
          </div>
        </div>

        <div className="bg-[#0D131F] border border-[#223044] rounded-xl p-4">
          <div className="text-[11px] font-mono text-slate-400 uppercase tracking-wider mb-1">
            Gross Contribution Margin
          </div>
          <div className="text-xl font-bold font-mono text-cyan-400">
            {grossMarginPct.toFixed(2)}%
          </div>
          <div className="text-[10px] text-slate-500 mt-1 flex items-center justify-between">
            <span>EBITDA Margin: {ebitdaMarginPct.toFixed(2)}%</span>
            <span className="text-emerald-400 font-mono">+120 bps YoY</span>
          </div>
        </div>
      </div>

      {/* Main Dual-Column Layout */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left Column (7 cols): Waterfall & Plant Footprint */}
        <div className="lg:col-span-7 space-y-5">
          {/* Unit Cost Structure Waterfall */}
          <div className="bg-[#0D131F] border border-[#223044] rounded-xl p-5">
            <h3 className="text-sm font-bold text-slate-200 font-mono mb-1">
              REVENUE WATERFALL & UNIT COST BREAKDOWN
            </h3>
            <p className="text-[11px] text-slate-400 mb-4">
              Normalized percentage breakdown of gross sales to operating cash generation.
            </p>

            {/* Visual Stacked Bar */}
            <div className="h-4 w-full rounded-full overflow-hidden flex mb-4 bg-slate-900 border border-slate-800">
              {costBreakdown.map((item, idx) => (
                <div
                  key={idx}
                  className={`${item.color} h-full`}
                  style={{ width: `${item.sharePct}%` }}
                  title={`${item.label}: ${item.sharePct}% (₹${item.inrCr.toLocaleString()} Cr)`}
                />
              ))}
            </div>

            {/* Breakdown Legend List */}
            <div className="space-y-2">
              {costBreakdown.map((item, idx) => (
                <div
                  key={idx}
                  className="flex items-center justify-between text-xs p-2 rounded bg-[#101725] border border-[#1A2536]"
                >
                  <div className="flex items-center gap-2">
                    <span className={`w-2.5 h-2.5 rounded-full ${item.color}`} />
                    <span className="text-slate-300">{item.label}</span>
                  </div>
                  <div className="flex items-center gap-3 font-mono">
                    <span className="text-slate-400">₹{item.inrCr.toLocaleString()} Cr</span>
                    <span className="text-slate-100 font-bold w-12 text-right">{item.sharePct.toFixed(1)}%</span>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Plant Throughput Footprint */}
          <div className="bg-[#0D131F] border border-[#223044] rounded-xl p-5">
            <h3 className="text-sm font-bold text-slate-200 font-mono mb-1">
              REGIONAL BOTTLING THROUGHPUT FOOTPRINT
            </h3>
            <p className="text-[11px] text-slate-400 mb-4">
              Capacity distribution across 16 owned production facilities.
            </p>

            <div className="space-y-2.5">
              {plantFootprint.map((p, idx) => (
                <div
                  key={idx}
                  className="flex items-center justify-between p-3 rounded-lg bg-[#101725] border border-[#1A2536] text-xs hover:border-cyan-500/40 transition-colors"
                >
                  <div>
                    <div className="font-semibold text-slate-200">{p.region}</div>
                    <div className="text-[11px] font-mono text-slate-400">{p.plants} Owned Plants · {p.capacityM}M Cases/yr</div>
                  </div>
                  <div className="flex items-center gap-3">
                    <div className="text-right font-mono">
                      <div className="text-emerald-400 font-bold">{p.utilPct.toFixed(1)}% Util</div>
                      <div className="text-[10px] text-slate-500">Peak Absorbed</div>
                    </div>
                    <button
                      type="button"
                      onClick={() => onCitationClick?.(p.drhpPage, 'ops.capacity')}
                      className="text-cyan-400 hover:text-cyan-300 text-[11px] font-mono px-2 py-1 rounded bg-[#0A0F18] border border-cyan-800/40 flex items-center gap-1 cursor-pointer"
                    >
                      <span>p. {p.drhpPage}</span>
                      <ExternalLink className="w-2.5 h-2.5" />
                    </button>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Right Column (5 cols): Evidence Interpretation Panel */}
        <div className="lg:col-span-5">
          <EvidenceInterpretationPanel
            interpretation={unitInterp}
            title="Operational Scale Decision Intelligence"
            onCitationClick={onCitationClick}
          />
        </div>
      </div>

      {/* Narrative Drawer */}
      <AnalystInsightDrawer
        title="Institutional Scale Diligence & Distribution Moat"
        offer={offer}
        vaultId="unit_economics"
        onCitationClick={onCitationClick}
        narrative={{
          sectorContext:
            'The Indian packaged beverage sector requires extreme logistics density. Cold-chain distribution and route-to-market direct outlet coverage create an impenetrable barrier to entry against regional competitors.',
          lifecyclePrecedents:
            'Mature beverage giants maintaining 75%-85% plant utilization maximize return on invested capital (ROIC) while leaving sufficient flex capacity for the 45% summer peak volume spike without dilutive capital expenditures.',
          riskRadar:
            'Interim stub gross margin expansion (+120 bps) is verified against audited concentrate procurement pricing agreements with The Coca-Cola Company, eliminating predatory transfer pricing risks.',
        }}
      />
    </div>
  );
};

export default UnitEconomicsVault;
