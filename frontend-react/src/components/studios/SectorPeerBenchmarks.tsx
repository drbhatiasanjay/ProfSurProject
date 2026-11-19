import React, { useState, useEffect } from 'react';
import { ChartContainer } from '../shared/ChartContainer';
import {
  BarChart3,
  Building,
  TrendingUp,
  Shield,
  Layers,
  Award,
  ExternalLink,
  ChevronDown,
  Activity,
  Calendar,
} from 'lucide-react';

interface CompanyItem {
  company_code: number;
  company_name: string;
  nse_symbol: string;
  industry_group: string;
}

interface BenchmarkData {
  company_info: {
    company_code: number;
    company_name: string;
    nse_symbol: string;
    industry_group: string;
    dominant_stage: string;
    avg_leverage: number;
    avg_profitability: number;
    avg_tangibility: number;
    current_borrowings: number;
    n_years: number;
  };
  company_series: Array<{
    year: number;
    leverage: number | null;
    profitability: number | null;
    tangibility: number | null;
    life_stage: string;
  }>;
  industry_series: Array<{
    year: number;
    industry_leverage: number | null;
    industry_profitability: number | null;
    industry_tangibility: number | null;
    n_peers: number;
  }>;
  stage_box_data: Array<{
    stage: string;
    count: number;
    min: number;
    q1: number;
    median: number;
    q3: number;
    max: number;
    mean: number;
  }>;
  radar_data: Array<{
    metric: string;
    company_raw: number;
    industry_raw: number;
    company_normalized: number;
    industry_normalized: number;
  }>;
  event_bands: Array<{
    year: number;
    name: string;
  }>;
}

interface SectorPeerBenchmarksProps {
  activePanel: string;
  yearMin: number;
  yearMax: number;
}

export const SectorPeerBenchmarks: React.FC<SectorPeerBenchmarksProps> = ({
  activePanel,
  yearMin,
  yearMax,
}) => {
  const [companies, setCompanies] = useState<CompanyItem[]>([]);
  const [selectedCode, setSelectedCode] = useState<number>(36277); // default 3M India or Tata Motors
  const [data, setData] = useState<BenchmarkData | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [hoveredYear, setHoveredYear] = useState<number | null>(null);

  // Fetch company directory
  useEffect(() => {
    fetch('http://127.0.0.1:8000/api/cmie/companies')
      .then((res) => res.json())
      .then((resData) => {
        if (resData && resData.companies) {
          setCompanies(resData.companies);
          // Prefer Tata Motors (248093) or first company
          const tata = resData.companies.find((c: CompanyItem) => c.company_code === 248093);
          if (tata) setSelectedCode(tata.company_code);
          else if (resData.companies.length > 0) setSelectedCode(resData.companies[0].company_code);
        }
      })
      .catch((err) => console.error('Failed to load company directory:', err));
  }, []);

  // Fetch peer benchmarks
  useEffect(() => {
    if (!selectedCode) return;
    setLoading(true);
    const panelId = activePanel.toLowerCase().replace(/[^a-z0-9]/g, '_');
    const url = `http://127.0.0.1:8000/api/cmie/peer-benchmarks?company_code=${selectedCode}&panel=${encodeURIComponent(
      panelId
    )}&year_min=${yearMin}&year_max=${yearMax}`;

    fetch(url)
      .then((res) => {
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        return res.json();
      })
      .then((resData: BenchmarkData) => {
        setData(resData);
        setLoading(false);
      })
      .catch((err) => {
        console.error('Failed to load peer benchmarks:', err);
        setLoading(false);
      });
  }, [selectedCode, activePanel, yearMin, yearMax]);

  if (loading) {
    return (
      <div className="bg-[#0d1527] border border-white/10 rounded-2xl p-12 text-center">
        <div className="inline-block w-8 h-8 border-2 border-cyan-400 border-t-transparent rounded-full animate-spin mb-3" />
        <p className="text-sm text-slate-300 font-medium">
          Loading peer benchmarks and industry distributions for company code{' '}
          <code className="text-cyan-300 font-mono">#{selectedCode}</code>...
        </p>
      </div>
    );
  }

  if (!data) {
    return (
      <div className="bg-rose-950/20 border border-rose-500/30 rounded-2xl p-6 text-center text-rose-300 text-sm">
        Failed to load benchmark data for active selection.
      </div>
    );
  }

  const { company_info, company_series, industry_series, stage_box_data, radar_data } = data;

  // Chart coordinate calculations
  const svgWidth = 520;
  const svgHeight = 240;
  const padL = 40;
  const padR = 20;
  const padT = 20;
  const padB = 30;
  const cWidth = svgWidth - padL - padR;
  const cHeight = svgHeight - padT - padB;

  const minYr = 2001;
  const maxYr = 2025;
  const getX = (yr: number) => padL + ((yr - minYr) / (maxYr - minYr)) * cWidth;

  // Leverage max (e.g. 80%)
  const maxLev = 80;
  const getYLev = (lev: number) => padT + cHeight - (Math.min(maxLev, Math.max(0, lev)) / maxLev) * cHeight;

  // Profitability max (e.g. 40%)
  const maxProf = 40;
  const minProf = -10;
  const getYProf = (prof: number) =>
    padT + cHeight - ((Math.min(maxProf, Math.max(minProf, prof)) - minProf) / (maxProf - minProf)) * cHeight;

  // Polylines for Leverage
  const cLevPoints = company_series
    .filter((d) => d.leverage !== null)
    .map((d) => `${getX(d.year)},${getYLev(d.leverage!)}`)
    .join(' ');

  const indLevPoints = industry_series
    .filter((d) => d.industry_leverage !== null)
    .map((d) => `${getX(d.year)},${getYLev(d.industry_leverage!)}`)
    .join(' ');

  // Polylines for Profitability
  const cProfPoints = company_series
    .filter((d) => d.profitability !== null)
    .map((d) => `${getX(d.year)},${getYProf(d.profitability!)}`)
    .join(' ');

  const indProfPoints = industry_series
    .filter((d) => d.industry_profitability !== null)
    .map((d) => `${getX(d.year)},${getYProf(d.industry_profitability!)}`)
    .join(' ');

  const exportComparisonCsv = (metric: 'leverage' | 'profitability') => {
    let csv = `Year,Company_${metric},Industry_Avg_${metric}\n`;
    for (let yr = minYr; yr <= maxYr; yr++) {
      const cRow = company_series.find((x) => x.year === yr);
      const indRow = industry_series.find((x) => x.year === yr);
      const cVal = cRow ? (cRow as any)[metric] : '';
      const indVal = indRow ? (indRow as any)[`industry_${metric}`] : '';
      csv += `${yr},${cVal !== null ? cVal : ''},${indVal !== null ? indVal : ''}\n`;
    }
    const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    link.href = URL.createObjectURL(blob);
    link.download = `${company_info.nse_symbol || 'company'}_vs_industry_${metric}.csv`;
    link.click();
  };

  return (
    <div className="space-y-6">
      {/* Studio Header Card */}
      <div className="bg-[#0d1527] border border-cyan-500/20 rounded-2xl p-6 shadow-xl">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-4 border-b border-white/10">
          <div>
            <span className="text-[11px] font-bold text-cyan-400 uppercase tracking-wider font-mono">
              Studio 02 &middot; Peer Intelligence
            </span>
            <h2 className="text-2xl font-black text-white tracking-tight mt-0.5 flex items-center gap-2">
              <BarChart3 className="w-6 h-6 text-cyan-400" />
              Sector Peer Benchmarks
            </h2>
            <p className="text-xs text-slate-400 mt-1 max-w-2xl">
              Cross-sectional benchmarking comparing an enterprise against its specific CMIE industry cohort and Dickinson life-stage peers across 25 fiscal years.
            </p>
          </div>

          {/* Company Quick-Select Dropdown */}
          <div className="flex items-center gap-3">
            <div className="relative min-w-[260px]">
              <label className="block text-[10px] font-bold text-slate-400 uppercase tracking-wider mb-1">
                Target Enterprise
              </label>
              <div className="relative">
                <select
                  value={selectedCode}
                  onChange={(e) => setSelectedCode(Number(e.target.value))}
                  className="w-full bg-slate-950 border border-cyan-500/35 rounded-lg px-3 py-2 text-xs font-semibold text-slate-100 focus:outline-none focus:border-cyan-400 appearance-none cursor-pointer"
                >
                  {companies.map((c) => (
                    <option key={c.company_code} value={c.company_code}>
                      {c.company_name} ({c.nse_symbol || `#${c.company_code}`})
                    </option>
                  ))}
                </select>
                <ChevronDown className="w-4 h-4 text-slate-500 absolute right-3 top-1/2 -translate-y-1/2 pointer-events-none" />
              </div>
            </div>

            <div className="pt-4">
              <a
                href="http://localhost:8501/"
                target="_blank"
                rel="noreferrer"
                className="px-3 py-2 rounded-lg bg-white/5 hover:bg-white/10 border border-white/10 text-slate-300 text-xs font-semibold flex items-center gap-1.5 transition-all"
              >
                <span>Streamlit (8501)</span>
                <ExternalLink className="w-3 h-3 text-slate-400" />
              </a>
            </div>
          </div>
        </div>

        {/* Selected Enterprise Profile Capsule */}
        <div className="mt-4 p-4 bg-slate-900/80 border border-white/10 rounded-xl flex flex-wrap items-center justify-between gap-4 text-xs">
          <div>
            <div className="flex items-center gap-2">
              <Building className="w-4 h-4 text-indigo-400" />
              <span className="text-base font-extrabold text-white">{company_info.company_name}</span>
              {company_info.nse_symbol && (
                <span className="px-2 py-0.5 rounded bg-indigo-500/15 text-indigo-300 font-mono font-bold text-xs border border-indigo-500/30">
                  NSE: {company_info.nse_symbol}
                </span>
              )}
            </div>
            <div className="text-xs text-slate-400 mt-1">
              Sector Cohort: <strong className="text-slate-200">{company_info.industry_group}</strong>
            </div>
          </div>

          <div className="flex flex-wrap items-center gap-6 text-xs font-mono">
            <div>
              <span className="text-[10px] text-slate-500 block uppercase">Dominant Stage</span>
              <span className="font-bold text-emerald-400">{company_info.dominant_stage}</span>
            </div>
            <div>
              <span className="text-[10px] text-slate-500 block uppercase">Avg Leverage</span>
              <span className="font-bold text-indigo-300">{company_info.avg_leverage}%</span>
            </div>
            <div>
              <span className="text-[10px] text-slate-500 block uppercase">Avg ROA</span>
              <span className="font-bold text-cyan-300">{company_info.avg_profitability}%</span>
            </div>
            <div>
              <span className="text-[10px] text-slate-500 block uppercase">Total Borrowings</span>
              <span className="font-bold text-slate-100">₹{company_info.current_borrowings.toLocaleString()} Cr</span>
            </div>
          </div>
        </div>

        {/* Row 1: Dual Time Series Charts */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mt-6">
          {/* Chart 1: Leverage: Company vs Industry Average */}
          <ChartContainer
            title={`Leverage: ${company_info.company_name} vs Industry Avg`}
            subtitle={`Comparing firm leverage against ${company_info.industry_group} peers`}
            sampleBadge="Longitudinal"
            sourceAttribution="CMIE Prowess Database (2001–2025)"
            onExportCsv={() => exportComparisonCsv('leverage')}
            methodologyFormula="\text{Leverage Gap}_{t} = \text{Leverage}_{i,t} - \overline{\text{Leverage}}_{\text{Industry},t}"
            methodologyDescription="Identifies whether the target enterprise operates with conservative capital headroom or aggressive structural gearing relative to industry rivals."
          >
            <div className="bg-slate-950/70 border border-slate-800 rounded-lg p-3 relative select-none">
              {/* Legend */}
              <div className="flex items-center justify-between text-xs mb-2 px-1">
                <div className="flex items-center gap-4">
                  <div className="flex items-center gap-1.5">
                    <span className="w-3.5 h-1 bg-[#0D9488] rounded-full" />
                    <span className="text-slate-200 font-semibold">{company_info.nse_symbol || 'Company'}</span>
                  </div>
                  <div className="flex items-center gap-1.5">
                    <span className="w-3.5 h-0.5 border-t border-dashed border-[#F97316]" />
                    <span className="text-slate-400 font-semibold">Industry Avg</span>
                  </div>
                </div>
                <span className="text-[10px] text-slate-500 font-mono">Y-Axis: 0–80%</span>
              </div>

              {/* SVG Chart */}
              <svg viewBox={`0 0 ${svgWidth} ${svgHeight}`} className="w-full h-56 overflow-visible">
                {/* Horizontal Grid */}
                {[0, 20, 40, 60, 80].map((val) => {
                  const y = getYLev(val);
                  return (
                    <g key={val}>
                      <line x1={padL} y1={y} x2={svgWidth - padR} y2={y} stroke="#1e293b" strokeDasharray="3 3" />
                      <text x={padL - 6} y={y + 3} fill="#64748b" fontSize="9" fontFamily="monospace" textAnchor="end">
                        {val}%
                      </text>
                    </g>
                  );
                })}

                {/* Event bands */}
                <rect x={getX(2007.5)} y={padT} width={getX(2009.5) - getX(2007.5)} height={cHeight} fill="rgba(239, 68, 68, 0.08)" />
                <rect x={getX(2015.5)} y={padT} width={getX(2017.5) - getX(2015.5)} height={cHeight} fill="rgba(99, 102, 241, 0.08)" />
                <rect x={getX(2019.5)} y={padT} width={getX(2021.5) - getX(2019.5)} height={cHeight} fill="rgba(249, 115, 22, 0.08)" />

                {/* Industry Average (Dashed #F97316) */}
                <polyline fill="none" stroke="#F97316" strokeWidth="2" strokeDasharray="4 3" points={indLevPoints} />

                {/* Company Leverage (Solid #0D9488) */}
                <polyline fill="none" stroke="#0D9488" strokeWidth="2.8" points={cLevPoints} />

                {/* Markers */}
                {company_series.map((d) => {
                  if (d.leverage === null) return null;
                  const cx = getX(d.year);
                  const cy = getYLev(d.leverage);
                  return (
                    <circle
                      key={d.year}
                      cx={cx}
                      cy={cy}
                      r={3.5}
                      fill="#0D9488"
                      stroke="#ffffff"
                      strokeWidth={1}
                    />
                  );
                })}

                {/* X-axis labels */}
                {[2001, 2005, 2010, 2015, 2020, 2025].map((yr) => (
                  <text key={yr} x={getX(yr)} y={padT + cHeight + 16} fill="#94a3b8" fontSize="9" fontFamily="monospace" textAnchor="middle">
                    {yr}
                  </text>
                ))}
              </svg>

              <div className="mt-2 text-[11px] text-slate-400 bg-slate-900/60 p-2 rounded border border-white/5">
                {company_info.avg_leverage > 30 ? (
                  <span>
                    Enterprise maintains <strong>elevated structural leverage</strong> ({company_info.avg_leverage}%) relative to the broader sector, indicating substantial tax-shield capture but narrower interest buffer.
                  </span>
                ) : (
                  <span>
                    Enterprise maintains a <strong>conservative debt posture</strong> ({company_info.avg_leverage}%), preserving ample covenant headroom across macroeconomic shocks.
                  </span>
                )}
              </div>
            </div>
          </ChartContainer>

          {/* Chart 2: Profitability: Company vs Industry Average */}
          <ChartContainer
            title={`Profitability: ${company_info.company_name} vs Industry Avg`}
            subtitle="Comparing operating return on assets (ROA %) over time"
            sampleBadge="Longitudinal"
            sourceAttribution="CMIE Prowess Database (2001–2025)"
            onExportCsv={() => exportComparisonCsv('profitability')}
            methodologyFormula="\text{ROA}_{i,t} = \frac{\text{Profit After Tax}_{i,t}}{\text{Total Assets}_{i,t}} \times 100"
            methodologyDescription="Pecking order theory predicts that firms with superior ROA generate substantial internal cash surpluses, mitigating debt requirements."
          >
            <div className="bg-slate-950/70 border border-slate-800 rounded-lg p-3 relative select-none">
              {/* Legend */}
              <div className="flex items-center justify-between text-xs mb-2 px-1">
                <div className="flex items-center gap-4">
                  <div className="flex items-center gap-1.5">
                    <span className="w-3.5 h-1 bg-[#10B981] rounded-full" />
                    <span className="text-slate-200 font-semibold">{company_info.nse_symbol || 'Company'}</span>
                  </div>
                  <div className="flex items-center gap-1.5">
                    <span className="w-3.5 h-0.5 border-t border-dashed border-[#F97316]" />
                    <span className="text-slate-400 font-semibold">Industry Avg</span>
                  </div>
                </div>
                <span className="text-[10px] text-slate-500 font-mono">Y-Axis: -10% to 40%</span>
              </div>

              {/* SVG Chart */}
              <svg viewBox={`0 0 ${svgWidth} ${svgHeight}`} className="w-full h-56 overflow-visible">
                {/* Horizontal Grid */}
                {[-10, 0, 10, 20, 30, 40].map((val) => {
                  const y = getYProf(val);
                  return (
                    <g key={val}>
                      <line x1={padL} y1={y} x2={svgWidth - padR} y2={y} stroke={val === 0 ? '#475569' : '#1e293b'} strokeDasharray={val === 0 ? '' : '3 3'} />
                      <text x={padL - 6} y={y + 3} fill="#64748b" fontSize="9" fontFamily="monospace" textAnchor="end">
                        {val}%
                      </text>
                    </g>
                  );
                })}

                {/* Event bands */}
                <rect x={getX(2007.5)} y={padT} width={getX(2009.5) - getX(2007.5)} height={cHeight} fill="rgba(239, 68, 68, 0.08)" />
                <rect x={getX(2015.5)} y={padT} width={getX(2017.5) - getX(2015.5)} height={cHeight} fill="rgba(99, 102, 241, 0.08)" />
                <rect x={getX(2019.5)} y={padT} width={getX(2021.5) - getX(2019.5)} height={cHeight} fill="rgba(249, 115, 22, 0.08)" />

                {/* Industry Profitability (Dashed #F97316) */}
                <polyline fill="none" stroke="#F97316" strokeWidth="2" strokeDasharray="4 3" points={indProfPoints} />

                {/* Company Profitability (Solid #10B981) */}
                <polyline fill="none" stroke="#10B981" strokeWidth="2.8" points={cProfPoints} />

                {/* Markers */}
                {company_series.map((d) => {
                  if (d.profitability === null) return null;
                  const cx = getX(d.year);
                  const cy = getYProf(d.profitability);
                  return (
                    <circle
                      key={d.year}
                      cx={cx}
                      cy={cy}
                      r={3.5}
                      fill="#10B981"
                      stroke="#ffffff"
                      strokeWidth={1}
                    />
                  );
                })}

                {/* X-axis labels */}
                {[2001, 2005, 2010, 2015, 2020, 2025].map((yr) => (
                  <text key={yr} x={getX(yr)} y={padT + cHeight + 16} fill="#94a3b8" fontSize="9" fontFamily="monospace" textAnchor="middle">
                    {yr}
                  </text>
                ))}
              </svg>

              <div className="mt-2 text-[11px] text-slate-400 bg-slate-900/60 p-2 rounded border border-white/5">
                <span>
                  Mean ROA of <strong className="text-white">{company_info.avg_profitability}%</strong> provides continuous internal equity accretion, aligning with Pecking Order predictions of cash-financed reinvestment.
                </span>
              </div>
            </div>
          </ChartContainer>
        </div>

        {/* Row 2: Life Stage Box Plots + Multi-Determinant Radar */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mt-6">
          {/* Chart 3: Life Stage Quantile Distribution */}
          <ChartContainer
            title="Leverage Distribution Across Dickinson Life Stages"
            subtitle="Cross-sectional distribution with diamond marker indicating selected company"
            sampleBadge="5 Stages"
            sourceAttribution="Dickinson (2011)"
            methodologyFormula="\text{IQR} = Q_3 - Q_1, \quad \text{Whiskers: } [\min, \max]"
            methodologyDescription="Box plot representation showing median, interquartile range, and whiskers. Selected enterprise marked with high-visibility diamond."
          >
            <div className="h-64 bg-slate-950/70 border border-slate-800 rounded-lg p-4 flex flex-col justify-between select-none">
              <div className="flex items-center justify-between text-xs text-slate-400 pb-2 border-b border-white/5">
                <span>Stage Cohort</span>
                <span className="font-mono">Median (IQR: Q1–Q3)</span>
              </div>

              <div className="space-y-3 my-auto">
                {stage_box_data.map((box, i) => {
                  const isCompStage = company_info.dominant_stage.toLowerCase().includes(box.stage.toLowerCase());
                  return (
                    <div key={i} className="space-y-1">
                      <div className="flex justify-between text-xs">
                        <span className={`font-semibold flex items-center gap-1.5 ${isCompStage ? 'text-cyan-300 font-bold' : 'text-slate-300'}`}>
                          <span>{box.stage} Stage</span>
                          {isCompStage && (
                            <span className="px-1.5 py-0.2 rounded bg-cyan-500/20 text-cyan-300 text-[10px] font-mono border border-cyan-500/35">
                              Target Diamond ◆
                            </span>
                          )}
                        </span>
                        <span className="font-mono text-slate-400">
                          {box.median}% <span className="text-[10px] text-slate-500">({box.q1}% – {box.q3}%)</span>
                        </span>
                      </div>

                      {/* Box Visual Bar */}
                      <div className="w-full h-3 bg-slate-900 rounded-full relative overflow-hidden border border-slate-800">
                        {/* Whiskers span */}
                        <div
                          style={{
                            left: `${Math.max(0, box.min)}%`,
                            width: `${Math.min(100, box.max - box.min)}%`,
                          }}
                          className="absolute top-1/2 -translate-y-1/2 h-0.5 bg-slate-600"
                        />
                        {/* IQR Box */}
                        <div
                          style={{
                            left: `${box.q1}%`,
                            width: `${box.q3 - box.q1}%`,
                          }}
                          className={`absolute top-0 bottom-0 rounded-sm ${
                            isCompStage ? 'bg-cyan-500/60 border border-cyan-300' : 'bg-indigo-500/40 border border-indigo-400'
                          }`}
                        />
                        {/* Median marker */}
                        <div
                          style={{ left: `${box.median}%` }}
                          className="absolute top-0 bottom-0 w-1 bg-white shadow"
                        />
                        {/* Target company marker */}
                        {isCompStage && (
                          <div
                            style={{ left: `${company_info.avg_leverage}%` }}
                            className="absolute -top-0.5 bottom-0 text-cyan-300 font-bold text-xs"
                            title={`Company Average: ${company_info.avg_leverage}%`}
                          >
                            ◆
                          </div>
                        )}
                      </div>
                    </div>
                  );
                })}
              </div>

              <div className="text-[10px] text-slate-500 font-mono text-center pt-2 border-t border-white/5">
                Horizontal scale: 0% to 100% book leverage
              </div>
            </div>
          </ChartContainer>

          {/* Chart 4: Multi-Determinant Profile */}
          <ChartContainer
            title="Multi-Determinant Profile: Company vs Industry Cohort"
            subtitle="Normalized 0–100 percentile scores across 6 key balance sheet metrics"
            sampleBadge="6 Metrics"
            sourceAttribution="Panel Financials"
            methodologyFormula="\text{Norm Score} = \frac{x - x_{\min}}{x_{\max} - x_{\min}} \times 100"
            methodologyDescription="Demonstrates cross-metric structural advantages and debt determinants relative to the sector baseline."
          >
            <div className="h-64 bg-slate-950/70 border border-slate-800 rounded-lg p-4 flex flex-col justify-between select-none overflow-y-auto">
              <div className="space-y-2.5">
                {radar_data.map((item, idx) => (
                  <div key={idx} className="space-y-1">
                    <div className="flex justify-between items-center text-xs">
                      <span className="font-semibold text-slate-300">{item.metric}</span>
                      <div className="flex items-center gap-3 font-mono text-[11px]">
                        <span className="text-cyan-300 font-bold">
                          Firm: {item.company_raw} ({Math.round(item.company_normalized)}%)
                        </span>
                        <span className="text-slate-500">|</span>
                        <span className="text-amber-400">
                          Ind: {item.industry_raw} ({Math.round(item.industry_normalized)}%)
                        </span>
                      </div>
                    </div>

                    {/* Dual comparison bar */}
                    <div className="w-full h-2 bg-slate-900 rounded-full overflow-hidden flex flex-col gap-0.5">
                      <div
                        style={{ width: `${item.company_normalized}%` }}
                        className="h-1 bg-gradient-to-r from-cyan-500 to-sky-400 rounded-full transition-all"
                      />
                      <div
                        style={{ width: `${item.industry_normalized}%` }}
                        className="h-1 bg-gradient-to-r from-amber-500 to-orange-400 rounded-full transition-all"
                      />
                    </div>
                  </div>
                ))}
              </div>

              <div className="flex items-center justify-between text-[10px] text-slate-400 pt-2 border-t border-white/5">
                <span className="flex items-center gap-1.5">
                  <span className="w-2.5 h-1 bg-cyan-400 rounded-full" />
                  <span>Target Company</span>
                </span>
                <span className="flex items-center gap-1.5">
                  <span className="w-2.5 h-1 bg-amber-400 rounded-full" />
                  <span>Industry Baseline</span>
                </span>
              </div>
            </div>
          </ChartContainer>
        </div>
      </div>
    </div>
  );
};
