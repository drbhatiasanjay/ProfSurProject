import React, { useState, useEffect } from 'react';
import { FinancialChartFrame } from '../shared/FinancialChartFrame';
import {
  TrendingUp,
  Activity,
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

interface MacroYearlyPoint {
  year: number;
  leverage: number;
  profitability: number;
  tangibility: number;
  dividend: number;
}

interface StageProfilePoint {
  stage: string;
  leverage: number;
  log_size: number;
  profitability: number;
  dividend: number;
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
  yearly_macro_trends?: MacroYearlyPoint[];
  stage_profile?: StageProfilePoint[];
  life_stages: LifeStageItem[];
  leverage_histogram: HistBin[];
}

interface ExecutiveHealthDashboardProps {
  activePanel: string;
  yearMin: number;
  yearMax: number;
  theme?: 'dark' | 'light';
}

export const ExecutiveHealthDashboard: React.FC<ExecutiveHealthDashboardProps> = ({
  activePanel,
  yearMin,
  yearMax,
  theme = 'dark',
}) => {
  const [data, setData] = useState<DashboardData | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setLoading(true);
    setError(null);

    const panelId = activePanel.toLowerCase().replace(/[^a-z0-9]/g, '_');
    const url = `http://localhost:8000/api/cmie/dashboard-charts?panel=${encodeURIComponent(
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

  const yearly = data.overall_yearly;
  const yearlyMacro = data.yearly_macro_trends || [];
  const stageProfile = data.stage_profile || [];

  // 1. Chart 1 Data: "How Has Financial Leverage Changed Over Time?" (Screenshot 1)
  const chart1Data: any[] = [
    {
      x: yearly.map((d) => d.year),
      y: yearly.map((d) => d.mean_leverage),
      type: 'scatter',
      mode: 'lines+markers',
      name: 'Mean Leverage',
      line: { color: '#00C49F', width: 3 },
      marker: { size: 6, color: '#00C49F' },
      hovertemplate: '<b>%{x}</b><br>Mean Leverage: %{y:.2f}%<extra></extra>',
    },
    {
      x: yearly.map((d) => d.year),
      y: yearly.map((d) => d.median_leverage),
      type: 'scatter',
      mode: 'lines',
      name: 'Median Leverage',
      line: { color: '#6366F1', width: 2, dash: 'dash' },
      hovertemplate: '<b>%{x}</b><br>Median Leverage: %{y:.2f}%<extra></extra>',
    },
  ];

  // Quantitative findings for Chart 1
  const startLev = yearly.length > 0 ? yearly[0].mean_leverage : 0;
  const endLev = yearly.length > 0 ? yearly[yearly.length - 1].mean_leverage : 0;
  const changeLev = endLev - startLev;
  const chart1Findings = [
    `Average leverage moved from **${startLev.toFixed(1)}%** (${yearly[0]?.year}) to **${endLev.toFixed(1)}%** (${yearly[yearly.length - 1]?.year}), a change of **${changeLev > 0 ? '+' : ''}${changeLev.toFixed(1)} pp**.`,
    `Peak average leverage reached **${Math.max(...yearly.map((d) => d.mean_leverage)).toFixed(1)}%** during the sample period.`,
  ];
  const chart1Implications = [
    'Indian corporates have **deleveraged** over this period — consistent with regulatory pressure (IBC 2016) and balance sheet repair.',
    'The deleveraging trend indicates firms prefer internal financing over debt expansion (Pecking Order behavior).',
  ];

  // 2. Chart 2 Data: Figure 5.2 — Year-wise Averages 2x2 Subplots (Screenshot 3)
  const macroYears = yearlyMacro.map((d) => d.year);
  const chart2Data: any[] = [
    {
      x: macroYears,
      y: yearlyMacro.map((d) => d.leverage),
      type: 'scatter',
      mode: 'lines',
      name: 'Leverage (%)',
      line: { color: '#00C49F', width: 2.5 },
      xaxis: 'x',
      yaxis: 'y',
    },
    {
      x: macroYears,
      y: yearlyMacro.map((d) => d.profitability),
      type: 'scatter',
      mode: 'lines',
      name: 'Profitability (%)',
      line: { color: '#6366F1', width: 2.5 },
      xaxis: 'x2',
      yaxis: 'y2',
    },
    {
      x: macroYears,
      y: yearlyMacro.map((d) => d.tangibility),
      type: 'scatter',
      mode: 'lines',
      name: 'Tangibility (%)',
      line: { color: '#F59E0B', width: 2.5 },
      xaxis: 'x3',
      yaxis: 'y3',
    },
    {
      x: macroYears,
      y: yearlyMacro.map((d) => d.dividend),
      type: 'scatter',
      mode: 'lines',
      name: 'Dividend (%)',
      line: { color: '#8B5CF6', width: 2.5 },
      xaxis: 'x4',
      yaxis: 'y4',
    },
  ];

  const chart2LayoutOverrides: Partial<Plotly.Layout> = {
    grid: { rows: 2, columns: 2, pattern: 'independent' },
    annotations: [
      { text: '<b>Leverage (%)</b>', showarrow: false, x: 0.22, y: 1.06, xref: 'paper', yref: 'paper', font: { size: 12, color: '#F8FAFC' } },
      { text: '<b>Profitability (%)</b>', showarrow: false, x: 0.78, y: 1.06, xref: 'paper', yref: 'paper', font: { size: 12, color: '#F8FAFC' } },
      { text: '<b>Tangibility (%)</b>', showarrow: false, x: 0.22, y: 0.46, xref: 'paper', yref: 'paper', font: { size: 12, color: '#F8FAFC' } },
      { text: '<b>Dividend (%)</b>', showarrow: false, x: 0.78, y: 0.46, xref: 'paper', yref: 'paper', font: { size: 12, color: '#F8FAFC' } },
    ],
    showlegend: false,
    height: 520,
  };

  // 3. Chart 3 Data: Figure 5.1 — Stage-wise Capital Structure Profile (Screenshot 4)
  const stageColors: Record<string, string> = {
    Introduction: '#F97316',
    Startup: '#F97316',
    Growth: '#22C55E',
    Mature: '#0D9488',
    Maturity: '#0D9488',
    Shakeout: '#A855F7',
    Shakeout1: '#A855F7',
    Shakeout2: '#A855F7',
    Decline: '#EF4444',
  };

  const stagesList = stageProfile.map((s) => s.stage);
  const chart3Data: any[] = [
    {
      x: stagesList,
      y: stageProfile.map((s) => s.leverage),
      type: 'bar',
      name: 'Avg. Leverage (%)',
      marker: { color: stagesList.map((s) => stageColors[s] || '#6366F1') },
      text: stageProfile.map((s) => s.leverage.toFixed(2)),
      textposition: 'outside',
      textfont: { size: 10, color: '#F8FAFC' },
      xaxis: 'x',
      yaxis: 'y',
    },
    {
      x: stagesList,
      y: stageProfile.map((s) => s.log_size),
      type: 'bar',
      name: 'Avg. Log Size',
      marker: { color: stagesList.map((s) => stageColors[s] || '#6366F1') },
      text: stageProfile.map((s) => s.log_size.toFixed(2)),
      textposition: 'outside',
      textfont: { size: 10, color: '#F8FAFC' },
      xaxis: 'x',
      yaxis: 'y2',
    },
  ];

  const chart3LayoutOverrides: Partial<Plotly.Layout> = {
    grid: { rows: 2, columns: 1, pattern: 'independent' },
    annotations: [
      { text: '<b>Avg. Leverage (%)</b>', showarrow: false, x: 0.0, y: 1.05, xref: 'paper', yref: 'paper', font: { size: 11, color: '#F8FAFC' }, xanchor: 'left' },
      { text: '<b>Avg. Log Size</b>', showarrow: false, x: 0.0, y: 0.45, xref: 'paper', yref: 'paper', font: { size: 11, color: '#F8FAFC' }, xanchor: 'left' },
    ],
    showlegend: false,
    height: 520,
    bargap: 0.28,
  };

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

  return (
    <div className="space-y-6 select-none">
      {/* ── Studio Header Card ── */}
      <div className="bg-[#0d1527] border border-white/10 rounded-2xl p-6 shadow-xl">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <div className="flex items-center gap-2">
              <span className="text-[11px] font-bold text-cyan-400 uppercase tracking-wider font-mono">
                Studio 01 &middot; Executive Telemetry
              </span>
              <span className="px-2 py-0.5 rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/30 text-[10px] font-semibold">
                Authentic Prowess DX
              </span>
            </div>
            <h2 className="text-2xl font-black text-white tracking-tight mt-1">
              Executive Health &amp; Solvency Dashboard
            </h2>
            <p className="text-xs text-slate-400 mt-1 max-w-2xl leading-relaxed">
              Macro longitudinal capital structure monitoring across{' '}
              <strong className="text-slate-200">
                {data.kpis.total_firms.toLocaleString()} listed Indian enterprises
              </strong>{' '}
              from FY{yearMin} to FY{yearMax}.
            </p>
          </div>

          <div className="flex items-center gap-2.5">
            <a
              href="http://localhost:8501/"
              target="_blank"
              rel="noreferrer"
              className="px-3 py-1.5 rounded-lg bg-white/5 hover:bg-white/10 border border-white/10 text-slate-300 text-xs font-semibold flex items-center gap-1.5 transition-all"
            >
              <span>Streamlit Baseline (8501)</span>
              <ExternalLink className="w-3 h-3 text-slate-400" />
            </a>
          </div>
        </div>
      </div>

      {/* ── Chart 1: How Has Financial Leverage Changed Over Time? (Screenshot 1) ── */}
      <FinancialChartFrame
        title="How Has Financial Leverage Changed Over Time?"
        subtitle="Average Financial Leverage Over Time (All Firms) — Dual series with GFC, IBC, and COVID Macroeconomic Shock Overlays"
        data={chart1Data}
        height={420}
        yearRange={[yearMin, yearMax]}
        theme={theme}
        showEventBands={true}
        allowEventBandToggle={true}
        findings={chart1Findings}
        implications={chart1Implications}
        methodologyCitation="Dickinson (2011) / IBC (2016) Corporate Restructuring Directive"
        onExportCsv={exportYearlyCsv}
      />

      {/* ── Chart 2: Figure 5.2 — Year-wise Averages (Screenshot 3) ── */}
      <FinancialChartFrame
        title="Year-wise Averages — Actual Levels"
        subtitle="Trends in Leverage, Profitability, Size of Assets and Dividend (FY2001–FY2025) across 4 Subplots"
        data={chart2Data}
        layoutOverrides={chart2LayoutOverrides}
        height={540}
        yearRange={[yearMin, yearMax]}
        theme={theme}
        showEventBands={true}
        allowEventBandToggle={true}
        findings={[
          '**Profitability (%)** peaked prior to the 2008 GFC before settling into an operational corridor of 14–17%.',
          '**Tangibility (%)** exhibits a structural decline from 35% to 27%, mirroring the rising contribution of asset-light technology and services enterprises.',
        ]}
        implications={[
          'Asset tangibility compression reduces traditional collateral-based bank borrowing capacity.',
          'Pecking order dynamics dominate as internal cash generation drives post-2016 balance sheet consolidation.',
        ]}
        methodologyCitation="Thesis Figure 5.2 (p. 93) — Macroeconomic Panel Decomposition"
      />

      {/* ── Chart 3: Figure 5.1 — Stage-wise Capital Structure Profile (Screenshot 4) ── */}
      <FinancialChartFrame
        title="Stage-wise Capital Structure Profile"
        subtitle="Mean Leverage and Log Size by Corporate Life Stage — Dickinson (2011) Cash Flow Classification"
        data={chart3Data}
        layoutOverrides={chart3LayoutOverrides}
        height={540}
        theme={theme}
        showEventBands={false}
        allowEventBandToggle={false}
        findings={[
          '**Introduction stage** firms exhibit the highest average leverage (32.98%), driven by initial external project financing.',
          '**Mature cash cows** maintain lower, stable leverage (16.78%) supported by robust operating cash flows.',
        ]}
        implications={[
          'Empirical validation of Trade-Off Theory: mature firms sustain optimal distress-shield trade-offs.',
          'Early-stage enterprises bear heightened vulnerability to rate shocks due to thin ICR headroom.',
        ]}
        methodologyCitation="Thesis Figure 5.1 (p. 89) — Dickinson Life-Cycle Vector Model"
      />
    </div>
  );
};
