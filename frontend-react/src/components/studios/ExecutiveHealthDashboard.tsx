import React, { useState, useEffect } from 'react';
import { ChartContainer } from '../shared/ChartContainer';
import {
  TrendingUp,
  Activity,
  PieChart,
  Layers,
  Shield,
  Award,
  ArrowUpRight,
  ExternalLink,
  Calendar,
} from 'lucide-react';

interface YearlyPoint {
  year: number;
  mean_leverage: number;
  median_leverage: number;
  n_firms: number;
}

interface LifeStageItem {
  stage: string;
  count: number;
  pct: number;
  color: string;
}

interface HistBin {
  bin: string;
  count: number;
  pct: number;
}

interface DashboardData {
  kpis: {
    total_firms: number;
    active_sample_firms: number;
    total_observations: number;
    mean_leverage: number;
    median_leverage: number;
    std_leverage: number;
    avg_profitability: number;
    avg_tangibility: number;
    dominant_stage: string;
    dominant_stage_pct: number;
  };
  overall_yearly: YearlyPoint[];
  life_stages: LifeStageItem[];
  leverage_histogram: HistBin[];
}

interface ExecutiveHealthDashboardProps {
  activePanel: string;
  yearMin: number;
  yearMax: number;
}

export const ExecutiveHealthDashboard: React.FC<ExecutiveHealthDashboardProps> = ({
  activePanel,
  yearMin,
  yearMax,
}) => {
  const [data, setData] = useState<DashboardData | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [hoveredYear, setHoveredYear] = useState<YearlyPoint | null>(null);
  const [hoveredBin, setHoveredBin] = useState<HistBin | null>(null);

  useEffect(() => {
    setLoading(true);
    setError(null);

    const panelId = activePanel.toLowerCase().replace(/[^a-z0-9]/g, '_');
    const url = `http://127.0.0.1:8000/api/cmie/dashboard-charts?panel=${encodeURIComponent(
      panelId
    )}&year_min=${yearMin}&year_max=${yearMax}`;

    fetch(url)
      .then((res) => {
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        return res.json();
      })
      .then((resData: DashboardData) => {
        setData(resData);
        setLoading(false);
      })
      .catch((err) => {
        console.error('Failed to fetch dashboard charts:', err);
        setError('Failed to fetch empirical data from backend.');
        setLoading(false);
      });
  }, [activePanel, yearMin, yearMax]);

  if (loading) {
    return (
      <div className="bg-[#0d1527] border border-white/10 rounded-2xl p-12 text-center">
        <div className="inline-block w-8 h-8 border-2 border-cyan-400 border-t-transparent rounded-full animate-spin mb-3" />
        <p className="text-sm text-slate-300 font-medium">
          Loading longitudinal panel from <code className="text-cyan-300 font-mono">capital_structure.db</code>...
        </p>
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className="bg-rose-950/20 border border-rose-500/30 rounded-2xl p-6 text-center text-rose-300 text-sm">
        {error || 'No data returned for active filters.'}
      </div>
    );
  }

  // Helper for Time-Series SVG Chart calculations
  const yearly = data.overall_yearly;
  const svgWidth = 760;
  const svgHeight = 280;
  const padLeft = 50;
  const padRight = 30;
  const padTop = 30;
  const padBottom = 40;
  const chartWidth = svgWidth - padLeft - padRight;
  const chartHeight = svgHeight - padTop - padBottom;

  const minYear = yearly.length > 0 ? yearly[0].year : 2001;
  const maxYear = yearly.length > 0 ? yearly[yearly.length - 1].year : 2025;
  const maxLev = 40; // Max percentage on Y axis

  const getX = (year: number) => padLeft + ((year - minYear) / Math.max(1, maxYear - minYear)) * chartWidth;
  const getY = (lev: number) => padTop + chartHeight - (lev / maxLev) * chartHeight;

  // Polyline points
  const meanPoints = yearly.map((d) => `${getX(d.year)},${getY(d.mean_leverage)}`).join(' ');
  const medianPoints = yearly.map((d) => `${getX(d.year)},${getY(d.median_leverage)}`).join(' ');

  // Event band coordinates
  const gfcX0 = getX(2007.5);
  const gfcX1 = getX(2009.5);
  const ibcX0 = getX(2015.5);
  const ibcX1 = getX(2017.5);
  const covidX0 = getX(2019.5);
  const covidX1 = getX(2021.5);

  const exportYearlyCsv = () => {
    let csv = 'Year,Mean_Leverage_Pct,Median_Leverage_Pct,Active_Firms\n';
    yearly.forEach((row) => {
      csv += `${row.year},${row.mean_leverage},${row.median_leverage},${row.n_firms}\n`;
    });
    const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    link.href = URL.createObjectURL(blob);
    link.download = `leverage_longitudinal_${activePanel}_${yearMin}_${yearMax}.csv`;
    link.click();
  };

  const exportHistogramCsv = () => {
    let csv = 'Leverage_Bin,Observation_Count,Percentage\n';
    data.leverage_histogram.forEach((b) => {
      csv += `"${b.bin}",${b.count},${b.pct}\n`;
    });
    const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    link.href = URL.createObjectURL(blob);
    link.download = `leverage_distribution_bins_${activePanel}.csv`;
    link.click();
  };

  const exportStagesCsv = () => {
    let csv = 'Dickinson_Stage,Observation_Count,Percentage\n';
    data.life_stages.forEach((s) => {
      csv += `"${s.stage}",${s.count},${s.pct}\n`;
    });
    const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    link.href = URL.createObjectURL(blob);
    link.download = `dickinson_stages_${activePanel}.csv`;
    link.click();
  };

  return (
    <div className="space-y-6">
      {/* Studio Header Card */}
      <div className="bg-[#0d1527] border border-cyan-500/20 rounded-2xl p-6 shadow-xl">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-4 border-b border-white/10">
          <div>
            <span className="text-[11px] font-bold text-cyan-400 uppercase tracking-wider font-mono">
              Studio 01 &middot; Macro Health
            </span>
            <h2 className="text-2xl font-black text-white tracking-tight mt-0.5">
              Executive Health Dashboard
            </h2>
            <p className="text-xs text-slate-400 mt-1 max-w-2xl">
              Longitudinal capital structure across {data.kpis.total_firms.toLocaleString()} listed Indian enterprises. Continuous panel verification spanning {yearly.length} fiscal years ({minYear}–{maxYear}).
            </p>
          </div>
          <div className="flex items-center gap-2">
            <span className="px-3 py-1 rounded-full bg-cyan-500/10 border border-cyan-500/30 text-cyan-300 text-xs font-bold font-mono">
              Port 5175 Active
            </span>
            <a
              href="http://localhost:8501/"
              target="_blank"
              rel="noreferrer"
              className="px-3 py-1 rounded-full bg-white/5 hover:bg-white/10 border border-white/10 text-slate-300 text-xs font-semibold flex items-center gap-1.5 transition-all"
            >
              <span>Streamlit Baseline (8501)</span>
              <ExternalLink className="w-3 h-3 text-slate-400" />
            </a>
          </div>
        </div>

        {/* ── Primary Chart: How Has Financial Leverage Changed Over Time? (Full Width) ── */}
        <div className="mt-6">
          <ChartContainer
            title="How Has Financial Leverage Changed Over Time?"
            subtitle="Yearly Mean (solid) vs Median (dashed) Book Leverage with GFC, IBC, and COVID Macro Shock Bands"
            sampleBadge={`N = ${data.kpis.total_observations.toLocaleString()} Obs`}
            sourceAttribution="CMIE Prowess Database (2001–2025)"
            onExportCsv={exportYearlyCsv}
            methodologyFormula="\text{Book Leverage}_{it} = \frac{\text{Total Debt}_{it}}{\text{Total Assets}_{it}} \times 100"
            methodologyDescription="Aggregated annually across listed enterprises. Dual series demonstrates debt skewness. Shaded vertical bands designate macro exogenous shocks: 2008 Global Financial Crisis, 2016 Insolvency & Bankruptcy Code, and 2020 COVID-19 pandemic shock."
          >
            {/* SVG Chart with Exact Parity */}
            <div className="relative w-full bg-slate-950/70 border border-slate-800 rounded-lg p-3 overflow-hidden select-none">
              {/* Legend Strip */}
              <div className="flex flex-wrap items-center justify-between gap-3 text-xs mb-3 px-2">
                <div className="flex items-center gap-5">
                  <div className="flex items-center gap-2">
                    <span className="w-4 h-1 bg-[#6366F1] rounded-full" />
                    <span className="text-slate-200 font-semibold">Mean Leverage (Solid)</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className="w-4 h-0.5 border-t border-dashed border-[#38BDF8]" />
                    <span className="text-slate-300 font-semibold">Median Leverage (Dashed)</span>
                  </div>
                </div>
                <div className="flex items-center gap-3 text-[11px] font-mono">
                  <span className="px-1.5 py-0.5 rounded bg-rose-500/15 text-rose-300 border border-rose-500/30">
                    2008 GFC
                  </span>
                  <span className="px-1.5 py-0.5 rounded bg-indigo-500/15 text-indigo-300 border border-indigo-500/30">
                    2016 IBC
                  </span>
                  <span className="px-1.5 py-0.5 rounded bg-amber-500/15 text-amber-300 border border-amber-500/30">
                    2020 COVID
                  </span>
                </div>
              </div>

              {/* Chart SVG */}
              <svg
                viewBox={`0 0 ${svgWidth} ${svgHeight}`}
                className="w-full h-72 overflow-visible"
              >
                {/* Horizontal Grid lines */}
                {[0, 10, 20, 30, 40].map((val) => {
                  const y = getY(val);
                  return (
                    <g key={val}>
                      <line
                        x1={padLeft}
                        y1={y}
                        x2={svgWidth - padRight}
                        y2={y}
                        stroke="#1e293b"
                        strokeDasharray="3 3"
                        strokeWidth="1"
                      />
                      <text
                        x={padLeft - 8}
                        y={y + 4}
                        fill="#64748b"
                        fontSize="10"
                        fontFamily="monospace"
                        textAnchor="end"
                      >
                        {val}%
                      </text>
                    </g>
                  );
                })}

                {/* Macro Event Bands */}
                {/* 1. GFC 2008 */}
                {gfcX0 < chartWidth + padLeft && gfcX1 > padLeft && (
                  <g>
                    <rect
                      x={Math.max(padLeft, gfcX0)}
                      y={padTop}
                      width={Math.min(chartWidth + padLeft, gfcX1) - Math.max(padLeft, gfcX0)}
                      height={chartHeight}
                      fill="rgba(239, 68, 68, 0.10)"
                    />
                    <text
                      x={Math.max(padLeft, gfcX0) + 4}
                      y={padTop + 14}
                      fill="#ef4444"
                      fontSize="9"
                      fontWeight="bold"
                      fontFamily="monospace"
                    >
                      GFC
                    </text>
                  </g>
                )}

                {/* 2. IBC 2016 */}
                {ibcX0 < chartWidth + padLeft && ibcX1 > padLeft && (
                  <g>
                    <rect
                      x={Math.max(padLeft, ibcX0)}
                      y={padTop}
                      width={Math.min(chartWidth + padLeft, ibcX1) - Math.max(padLeft, ibcX0)}
                      height={chartHeight}
                      fill="rgba(99, 102, 241, 0.12)"
                    />
                    <text
                      x={Math.max(padLeft, ibcX0) + 4}
                      y={padTop + 14}
                      fill="#818cf8"
                      fontSize="9"
                      fontWeight="bold"
                      fontFamily="monospace"
                    >
                      IBC
                    </text>
                  </g>
                )}

                {/* 3. COVID 2020 */}
                {covidX0 < chartWidth + padLeft && covidX1 > padLeft && (
                  <g>
                    <rect
                      x={Math.max(padLeft, covidX0)}
                      y={padTop}
                      width={Math.min(chartWidth + padLeft, covidX1) - Math.max(padLeft, covidX0)}
                      height={chartHeight}
                      fill="rgba(249, 115, 22, 0.10)"
                    />
                    <text
                      x={Math.max(padLeft, covidX0) + 4}
                      y={padTop + 14}
                      fill="#fb923c"
                      fontSize="9"
                      fontWeight="bold"
                      fontFamily="monospace"
                    >
                      COVID
                    </text>
                  </g>
                )}

                {/* Median Leverage Line (Dashed #38BDF8) */}
                <polyline
                  fill="none"
                  stroke="#38BDF8"
                  strokeWidth="2.2"
                  strokeDasharray="5 4"
                  points={medianPoints}
                />

                {/* Mean Leverage Line (Solid #6366F1) */}
                <polyline
                  fill="none"
                  stroke="#6366F1"
                  strokeWidth="2.8"
                  points={meanPoints}
                />

                {/* Data Points with Hover Targets */}
                {yearly.map((p) => {
                  const cx = getX(p.year);
                  const cyMean = getY(p.mean_leverage);
                  const isHovered = hoveredYear?.year === p.year;

                  return (
                    <g
                      key={p.year}
                      onMouseEnter={() => setHoveredYear(p)}
                      onMouseLeave={() => setHoveredYear(null)}
                      className="cursor-pointer"
                    >
                      {/* Vertical tracking line when hovered */}
                      {isHovered && (
                        <line
                          x1={cx}
                          y1={padTop}
                          x2={cx}
                          y2={padTop + chartHeight}
                          stroke="#38BDF8"
                          strokeWidth="1"
                          strokeDasharray="2 2"
                        />
                      )}

                      {/* Mean Marker */}
                      <circle
                        cx={cx}
                        cy={cyMean}
                        r={isHovered ? 6 : 4}
                        fill="#6366F1"
                        stroke="#ffffff"
                        strokeWidth={isHovered ? 2 : 1}
                        className="transition-all"
                      />

                      {/* X Axis year labels for key intervals */}
                      {(p.year % 5 === 0 || p.year === minYear || p.year === maxYear) && (
                        <text
                          x={cx}
                          y={padTop + chartHeight + 18}
                          fill="#94a3b8"
                          fontSize="10"
                          fontFamily="monospace"
                          textAnchor="middle"
                        >
                          {p.year}
                        </text>
                      )}
                    </g>
                  );
                })}
              </svg>

              {/* Hover Tooltip Overlay */}
              {hoveredYear && (
                <div
                  className="absolute bg-[#0f172a] border border-cyan-400/50 rounded-lg p-2.5 shadow-2xl pointer-events-none text-xs z-20"
                  style={{
                    left: `${Math.min(svgWidth - 160, Math.max(60, getX(hoveredYear.year) - 70))}px`,
                    top: '20px',
                  }}
                >
                  <div className="font-bold text-cyan-300 font-mono flex items-center gap-1.5 pb-1 border-b border-white/10 mb-1.5">
                    <Calendar className="w-3.5 h-3.5" />
                    <span>FY {hoveredYear.year}</span>
                    <span className="text-[10px] text-slate-400 font-normal">
                      ({hoveredYear.n_firms} firms)
                    </span>
                  </div>
                  <div className="space-y-0.5 text-[11px] font-mono">
                    <div className="flex justify-between gap-4 text-indigo-300">
                      <span>Mean Leverage:</span>
                      <span className="font-bold">{hoveredYear.mean_leverage}%</span>
                    </div>
                    <div className="flex justify-between gap-4 text-sky-300">
                      <span>Median Leverage:</span>
                      <span className="font-bold">{hoveredYear.median_leverage}%</span>
                    </div>
                    <div className="flex justify-between gap-4 text-slate-400">
                      <span>Skew (Mean - Med):</span>
                      <span>
                        {(hoveredYear.mean_leverage - hoveredYear.median_leverage).toFixed(1)} pp
                      </span>
                    </div>
                  </div>
                </div>
              )}
            </div>

            {/* Empirical Trend Takeaway Box */}
            <div className="mt-3 p-3 bg-slate-950/40 border border-slate-800 rounded-lg text-xs flex items-center justify-between text-slate-300">
              <div className="flex items-center gap-2">
                <TrendingUp className="w-4 h-4 text-cyan-400 shrink-0" />
                <span>
                  <strong>Longitudinal Takeaway:</strong> Average leverage moved from{' '}
                  <strong className="text-white">{yearly[0]?.mean_leverage}%</strong> ({minYear}) to{' '}
                  <strong className="text-white">{yearly[yearly.length - 1]?.mean_leverage}%</strong> ({maxYear}), a change of{' '}
                  <strong className="text-cyan-300">
                    {(yearly[yearly.length - 1]?.mean_leverage - yearly[0]?.mean_leverage).toFixed(1)} pp
                  </strong>. Consistent with post-IBC 2016 corporate deleveraging.
                </span>
              </div>
            </div>
          </ChartContainer>
        </div>

        {/* ── Row 2: 2-Column Analytical Charts Layout ── */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mt-6">
          {/* Chart 1: Book Leverage Distribution Histogram */}
          <ChartContainer
            title="Book Leverage Distribution (Total Debt / Assets)"
            subtitle="Frequency Histogram over 8 Bins from 9,031 Observations"
            sampleBadge={`N = ${data.kpis.total_observations.toLocaleString()}`}
            sourceAttribution="CMIE Prowess Database"
            onExportCsv={exportHistogramCsv}
            methodologyFormula="\text{Bins: } [0, 10), [10, 20), [20, 30), [30, 40), [40, 50), [50, 60), [60, 70), [70, 100]"
            methodologyDescription="Frequency count and percentage representation across book debt to asset tranches. Reveals significant clustering in the low-to-moderate leverage tranches."
          >
            <div className="h-64 bg-slate-950/70 border border-slate-800 rounded-lg p-4 flex flex-col justify-end relative select-none">
              <div className="flex items-end justify-between h-44 gap-2 px-1">
                {data.leverage_histogram.map((b, i) => {
                  const maxCount = Math.max(...data.leverage_histogram.map((x) => x.count), 1);
                  const heightPct = Math.round((b.count / maxCount) * 100);
                  const isHovered = hoveredBin?.bin === b.bin;

                  return (
                    <div
                      key={i}
                      onMouseEnter={() => setHoveredBin(b)}
                      onMouseLeave={() => setHoveredBin(null)}
                      className="flex-1 flex flex-col items-center gap-2 group cursor-pointer"
                    >
                      <div
                        style={{ height: `${heightPct}%` }}
                        className={`w-full rounded-t transition-all ${
                          isHovered
                            ? 'bg-gradient-to-t from-cyan-400 to-sky-300 shadow-lg shadow-cyan-500/20'
                            : 'bg-gradient-to-t from-cyan-600 to-sky-500 group-hover:from-cyan-500 group-hover:to-sky-400'
                        }`}
                      />
                      <span className="text-[10px] text-slate-400 font-mono rotate-45 origin-left pt-1">
                        {b.bin}
                      </span>
                    </div>
                  );
                })}
              </div>

              {/* Hover Details for Histogram */}
              {hoveredBin ? (
                <div className="absolute top-3 left-4 right-4 bg-slate-900 border border-cyan-400/40 rounded px-3 py-1.5 flex items-center justify-between text-xs font-mono shadow-xl">
                  <span className="text-cyan-300 font-bold">Bin: {hoveredBin.bin}</span>
                  <span className="text-slate-200">{hoveredBin.count.toLocaleString()} firms</span>
                  <span className="text-emerald-400 font-bold">{hoveredBin.pct}% share</span>
                </div>
              ) : (
                <div className="absolute top-3 right-4 text-[11px] text-slate-500 font-mono">
                  Hover bar for exact firm count &amp; share
                </div>
              )}
            </div>
          </ChartContainer>

          {/* Chart 2: Dickinson Life-Cycle Stage Breakdown */}
          <ChartContainer
            title="Dickinson (2011) Life-Cycle Stage Breakdown"
            subtitle="Cash-Flow Pattern Vectors (OCF, ICF, FCF) across 5 Stages"
            sampleBadge="Dickinson SSOT"
            sourceAttribution="Dickinson (2011) The Accounting Review"
            onExportCsv={exportStagesCsv}
            methodologyFormula="\text{Mature} = (+,-,-), \quad \text{Growth} = (+,-,+), \quad \text{Intro} = (-,-,+), \quad \text{Decline} = (-,+,\pm)"
            methodologyDescription="Classification of firms into distinct life stages based on signs of cash flows from operations, investing, and financing without relying on age or size proxies."
          >
            <div className="h-64 bg-slate-950/70 border border-slate-800 rounded-lg p-4 flex flex-col justify-center space-y-3 overflow-y-auto">
              {data.life_stages.map((item, i) => (
                <div key={i} className="space-y-1.5">
                  <div className="flex justify-between text-xs">
                    <span className="font-semibold text-slate-200 flex items-center gap-2">
                      <span
                        className="w-2.5 h-2.5 rounded-full"
                        style={{ backgroundColor: item.color }}
                      />
                      {item.stage}
                    </span>
                    <span className="font-mono text-slate-300">
                      <strong className="text-white">{item.pct}%</strong> ({item.count.toLocaleString()} firms)
                    </span>
                  </div>
                  <div className="w-full h-2.5 bg-slate-800/90 rounded-full overflow-hidden">
                    <div
                      style={{
                        width: `${item.pct}%`,
                        backgroundColor: item.color,
                      }}
                      className="h-full rounded-full transition-all"
                    />
                  </div>
                </div>
              ))}
            </div>
          </ChartContainer>
        </div>
      </div>
    </div>
  );
};
