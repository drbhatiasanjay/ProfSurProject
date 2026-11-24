import React, { useState, useEffect } from 'react';
import { PlotlyChart } from '../shared/PlotlyChart';
import { CollapsibleInsightBox } from '../shared/CollapsibleInsightBox';
import { ResultsInterpretationPanel } from '../shared/ResultsInterpretationPanel';
import {
  TrendingUp,
  Activity,
  Layers,
  Shield,
  Award,
  ArrowUpRight,
  ArrowDownRight,
  Calendar,
  AlertTriangle,
  Database,
  BarChart2,
  RefreshCw,
  Sparkles
} from 'lucide-react';

export const STAGE_COLORS: Record<string, string> = {
  Startup: '#F97316',
  Growth: '#22C55E',
  Maturity: '#0D9488',
  Shakeout1: '#A78BFA',
  Shakeout2: '#8B5CF6',
  Shakeout3: '#6366F1',
  Decline: '#EF4444',
  Decay: '#991B1B',
};

interface BentoCapsule {
  id: string;
  label: string;
  value: string;
  sublabel: string;
  badge?: string;
  badge_color?: string;
  trend?: string;
  sparkline?: number[];
  color?: string;
}

interface InsightBoxData {
  title: string;
  findings: string[];
  actions: string[];
  context?: string;
}

interface DashboardPayload {
  bento_kpis: BentoCapsule[];
  kpi_overview_box: InsightBoxData;
  leverage_over_time: {
    title: string;
    series: Array<{ year: number; mean_leverage: number; median_leverage: number; n_firms: number }>;
    box: InsightBoxData;
  };
  fig51_stage_profile: {
    title: string;
    subtitle: string;
    stages: string[];
    data: Array<{
      stage: string;
      color: string;
      leverage: number;
      log_size: number;
      profitability: number;
      dividend: number;
    }>;
    box: InsightBoxData;
  };
  fig52_year_trends: {
    title: string;
    subtitle: string;
    years: number[];
    data: Array<{
      year: number;
      leverage: number;
      log_size: number;
      profitability: number;
      dividend: number;
    }>;
    box: InsightBoxData;
  };
  fig83_decline_decay: {
    title: string;
    subtitle: string;
    decline: Array<{ roa: number; ppe_ta: number; leverage: number }>;
    decay: Array<{ roa: number; ppe_ta: number; leverage: number }>;
    ols_slopes: {
      decline_roa: { slope: number; intercept: number };
      decline_ppe: { slope: number; intercept: number };
      decay_roa: { slope: number; intercept: number };
      decay_ppe: { slope: number; intercept: number };
    };
    box: InsightBoxData;
  };
  pairwise_significance: {
    title: string;
    subtitle: string;
    stages: string[];
    matrix: Array<Array<number | null>>;
    text: string[][];
    significant_callouts: Array<{ pair: string; diff: string; p_val: string; interpretation: string }>;
    box: InsightBoxData;
  };
  determinant_profiles: {
    title: string;
    subtitle: string;
    stages: string[];
    determinants: string[];
    z: Array<Array<number | null>>;
    box: InsightBoxData;
  };
  macro_context: {
    title: string;
    records: Array<{ year: number; leverage: number; gsec_yield: number; sensex_pe: number }>;
    events: Array<{ name: string; year_start: number; year_end: number; color: string }>;
    box: InsightBoxData;
  };
  event_stage_interaction: {
    title: string;
    stages: string[];
    data: Record<string, { baseline: number[]; gfc: number[]; ibc: number[]; covid: number[] }>;
  };
  lifecycle_distribution: Array<{ stage: string; count: number; pct: number; color: string }>;
  top10_leveraged: Array<{ company: string; leverage: number; stage: string; color: string }>;
  results_interpretation: {
    title: string;
    subtitle: string;
    insights: string[];
    actions: string[];
    methodologyCitation: string;
  };
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
  const [data, setData] = useState<DashboardPayload | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setLoading(true);
    setError(null);

    const panelId =
      activePanel.toLowerCase().includes('bf2001') || activePanel.toLowerCase().includes('sept26')
        ? 'bf2001_25_sept26'
        : activePanel.toLowerCase().replace(/[^a-z0-9]/g, '_');

    const url = `http://localhost:8000/api/cmie/dashboard-charts?panel=${encodeURIComponent(
      panelId
    )}&year_min=${yearMin}&year_max=${yearMax}`;

    fetch(url)
      .then((res) => {
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        return res.json();
      })
      .then((json: DashboardPayload) => {
        setData(json);
        setLoading(false);
      })
      .catch((err) => {
        console.error('Failed to fetch dashboard payload:', err);
        setError('Failed to fetch empirical data from backend.');
        setLoading(false);
      });
  }, [activePanel, yearMin, yearMax]);

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center p-16 space-y-4">
        <RefreshCw className="h-8 w-8 text-cyan-400 animate-spin" />
        <span className="text-sm font-medium text-slate-400">Loading Executive Health Dashboard analytics...</span>
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className="p-6 rounded-xl border border-red-500/20 bg-red-950/20 text-red-400 flex items-center gap-3">
        <AlertTriangle className="h-5 w-5 flex-shrink-0" />
        <span>{error || 'Unable to load dashboard data.'}</span>
      </div>
    );
  }

  // --- Chart 1: Leverage Over Time ---
  const yearsTime = data.leverage_over_time.series.map((d: any) => d.year);
  const meanLevTime = data.leverage_over_time.series.map((d: any) => d.mean ?? d.mean_leverage);
  const medLevTime = data.leverage_over_time.series.map((d: any) => d.median ?? d.median_leverage);

  const leverageTimeTraces: any[] = [
    {
      x: yearsTime,
      y: meanLevTime,
      name: 'Mean Leverage (%)',
      type: 'scatter',
      mode: 'lines+markers',
      line: { color: '#0D9488', width: 3 },
      marker: { size: 6, color: '#0D9488' },
    },
    {
      x: yearsTime,
      y: medLevTime,
      name: 'Median Leverage (%)',
      type: 'scatter',
      mode: 'lines+markers',
      line: { color: '#F97316', width: 2, dash: 'dash' },
      marker: { size: 5, color: '#F97316' },
    },
  ];

  const leverageTimeLayout = {
    title: { text: data.leverage_over_time.title, font: { color: '#F8FAFC', size: 14 } },
    paper_bgcolor: 'transparent',
    plot_bgcolor: 'transparent',
    margin: { t: 40, b: 40, l: 50, r: 20 },
    height: 340,
    xaxis: { gridcolor: '#1E293B', tickfont: { color: '#94A3B8' }, dtick: 2 },
    yaxis: { gridcolor: '#1E293B', tickfont: { color: '#94A3B8' }, title: { text: 'Leverage (%)', font: { color: '#94A3B8', size: 12 } } },
    legend: { orientation: 'h' as const, y: -0.2, font: { color: '#CBD5E1' } },
    shapes: [
      { type: 'rect', xref: 'x', yref: 'paper', x0: 2008, x1: 2009, y0: 0, y1: 1, fillcolor: 'rgba(239, 68, 68, 0.12)', line: { width: 0 } },
      { type: 'rect', xref: 'x', yref: 'paper', x0: 2016, x1: 2019, y0: 0, y1: 1, fillcolor: 'rgba(99, 102, 241, 0.12)', line: { width: 0 } },
      { type: 'rect', xref: 'x', yref: 'paper', x0: 2020, x1: 2021, y0: 0, y1: 1, fillcolor: 'rgba(249, 115, 22, 0.12)', line: { width: 0 } },
    ],
  };

  // --- Chart 2: Figure 5.1 (Stage Profile 4 subplots) ---
  const fig51List = (data.fig51_stage_profile.data || []) as any[];
  const stages51 = fig51List.map((d: any) => d.stage);
  const stageBarColors = fig51List.map((d: any) => d.color || STAGE_COLORS[d.stage] || '#0D9488');

  const fig51Metrics = [
    { key: 'leverage', title: 'Avg Leverage (%)', values: fig51List.map((d: any) => d.leverage), unit: '%' },
    { key: 'log_size', title: 'Log Size of Assets', values: fig51List.map((d: any) => d.log_size), unit: '' },
    { key: 'profitability', title: 'Profitability (ROA)', values: fig51List.map((d: any) => d.profitability), unit: '' },
    { key: 'dividend', title: 'Dividend Payout (%)', values: fig51List.map((d: any) => d.dividend), unit: '%' },
  ];

  // --- Chart 3: Figure 5.2 (Year-wise Trends 4 subplots) ---
  const fig52List = (data.fig52_year_trends.data || []) as any[];
  const years52 = fig52List.map((d: any) => d.year);
  const fig52Metrics = [
    { key: 'leverage', title: 'Avg Leverage (%)', values: fig52List.map((d: any) => d.leverage), color: '#0D9488' },
    { key: 'log_size', title: 'Log Size of Assets', values: fig52List.map((d: any) => d.log_size), color: '#6366F1' },
    { key: 'profitability', title: 'Profitability (ROA)', values: fig52List.map((d: any) => d.profitability), color: '#10B981' },
    { key: 'dividend', title: 'Dividend Payout (%)', values: fig52List.map((d: any) => d.dividend), color: '#F59E0B' },
  ];

  // --- Chart 4: Figure 8.3 (Decline & Decay Scatters with OLS) ---
  const slopes = (data.fig83_decline_decay.ols_slopes || {}) as any;
  const decRoa = slopes.Decline_prof || slopes.decline_roa || { slope: -47.7, intercept: 30.4 };
  const decPpe = slopes.Decline_tang || slopes.decline_ppe || { slope: 30.7, intercept: 28.3 };
  const decayRoa = slopes.Decay_prof || slopes.decay_roa || { slope: 37.5, intercept: 15.8 };
  const decayPpe = slopes.Decay_tang || slopes.decay_ppe || { slope: 137.0, intercept: 1.2 };

  const fig83RoaTraces: any[] = [
    {
      x: data.fig83_decline_decay.decline.map((d) => d.roa),
      y: data.fig83_decline_decay.decline.map((d) => d.leverage),
      mode: 'markers',
      name: 'Decline',
      marker: { color: '#EF4444', size: 5, opacity: 0.6 },
      type: 'scatter',
    },
    {
      x: data.fig83_decline_decay.decay.map((d) => d.roa),
      y: data.fig83_decline_decay.decay.map((d) => d.leverage),
      mode: 'markers',
      name: 'Decay',
      marker: { color: '#991B1B', size: 5, opacity: 0.6 },
      type: 'scatter',
    },
    {
      x: [-0.4, 0.4],
      y: [
        decRoa.intercept + decRoa.slope * -0.4,
        decRoa.intercept + decRoa.slope * 0.4,
      ],
      mode: 'lines',
      name: 'Decline OLS Fit',
      line: { color: '#EF4444', width: 2, dash: 'dash' },
      type: 'scatter',
    },
    {
      x: [-0.4, 0.4],
      y: [
        decayRoa.intercept + decayRoa.slope * -0.4,
        decayRoa.intercept + decayRoa.slope * 0.4,
      ],
      mode: 'lines',
      name: 'Decay OLS Fit',
      line: { color: '#991B1B', width: 2, dash: 'dash' },
      type: 'scatter',
    },
  ];

  const fig83PpeTraces: any[] = [
    {
      x: data.fig83_decline_decay.decline.map((d) => d.ppe_ta),
      y: data.fig83_decline_decay.decline.map((d) => d.leverage),
      mode: 'markers',
      name: 'Decline',
      marker: { color: '#EF4444', size: 5, opacity: 0.6 },
      type: 'scatter',
      showlegend: false,
    },
    {
      x: data.fig83_decline_decay.decay.map((d) => d.ppe_ta),
      y: data.fig83_decline_decay.decay.map((d) => d.leverage),
      mode: 'markers',
      name: 'Decay',
      marker: { color: '#991B1B', size: 5, opacity: 0.6 },
      type: 'scatter',
      showlegend: false,
    },
    {
      x: [0.0, 0.8],
      y: [
        decPpe.intercept + decPpe.slope * 0.0,
        decPpe.intercept + decPpe.slope * 0.8,
      ],
      mode: 'lines',
      name: 'Decline OLS Fit',
      line: { color: '#EF4444', width: 2, dash: 'dash' },
      type: 'scatter',
      showlegend: false,
    },
    {
      x: [0.0, 0.8],
      y: [
        decayPpe.intercept + decayPpe.slope * 0.0,
        decayPpe.intercept + decayPpe.slope * 0.8,
      ],
      mode: 'lines',
      name: 'Decay OLS Fit',
      line: { color: '#991B1B', width: 2, dash: 'dash' },
      type: 'scatter',
      showlegend: false,
    },
  ];

  // --- Chart 5: Table 5.9 Pairwise Significance Matrix Heatmap ---
  const pwData = data.pairwise_significance;
  const pwHeatmapTrace = [
    {
      z: (pwData as any).z || pwData.matrix,
      x: pwData.stages,
      y: pwData.stages,
      text: pwData.text,
      texttemplate: '%{text}',
      type: 'heatmap' as const,
      colorscale: [
        [0, '#DC2626'],
        [0.05, '#EF4444'],
        [0.051, '#0F172A'],
        [1, '#1E293B'],
      ],
      showscale: false,
    },
  ];

  const pwLayout = {
    title: { text: pwData.title, font: { color: '#F8FAFC', size: 14 } },
    paper_bgcolor: 'transparent',
    plot_bgcolor: 'transparent',
    height: 400,
    margin: { t: 40, b: 60, l: 80, r: 30 },
    xaxis: { tickfont: { color: '#94A3B8', size: 11 }, tickangle: -25 },
    yaxis: { tickfont: { color: '#94A3B8', size: 11 }, autorange: 'reversed' as const },
  };

  // --- Chart 6: Determinant Profiles Heatmap ---
  const detData = data.determinant_profiles;
  const detHeatmapTrace = [
    {
      z: detData.z,
      x: detData.determinants,
      y: detData.stages,
      type: 'heatmap' as const,
      colorscale: [
        [0, '#0E1626'],
        [0.5, '#0D9488'],
        [1, '#10B981'],
      ],
      colorbar: {
        title: { text: 'Normalized (0-100)', font: { color: '#94A3B8', size: 10 } },
        tickfont: { color: '#94A3B8' },
      },
    },
  ];

  const detLayout = {
    title: { text: detData.title, font: { color: '#F8FAFC', size: 14 } },
    paper_bgcolor: 'transparent',
    plot_bgcolor: 'transparent',
    height: 380,
    margin: { t: 40, b: 40, l: 90, r: 40 },
    xaxis: { tickfont: { color: '#CBD5E1', size: 11 } },
    yaxis: { tickfont: { color: '#CBD5E1', size: 11 }, autorange: 'reversed' as const },
  };

  // --- Chart 7: Macro Context Dual-Axis ---
  const macroYears = data.macro_context.records.map((r: any) => r.year);
  const macroLev = data.macro_context.records.map((r: any) => r.leverage);
  const macroGsec = data.macro_context.records.map((r: any) => r.int_rate ?? r.gsec_yield);
  const macroPe = data.macro_context.records.map((r: any) => r.pe_ratio ?? r.sensex_pe);

  const macroTraces: any[] = [
    {
      x: macroYears,
      y: macroLev,
      name: 'Leverage (%)',
      type: 'scatter',
      mode: 'lines+markers',
      line: { color: '#0D9488', width: 3 },
      yaxis: 'y1',
    },
    {
      x: macroYears,
      y: macroGsec,
      name: '10Y G-Sec Yield (%)',
      type: 'scatter',
      mode: 'lines',
      line: { color: '#F59E0B', width: 2, dash: 'dot' },
      yaxis: 'y1',
    },
    {
      x: macroYears,
      y: macroPe,
      name: 'BSE Sensex P/E',
      type: 'scatter',
      mode: 'lines',
      line: { color: '#6366F1', width: 2, dash: 'dash' },
      yaxis: 'y2',
    },
  ];

  const macroLayout = {
    title: { text: data.macro_context.title, font: { color: '#F8FAFC', size: 14 } },
    paper_bgcolor: 'transparent',
    plot_bgcolor: 'transparent',
    height: 350,
    margin: { t: 40, b: 40, l: 50, r: 50 },
    xaxis: { gridcolor: '#1E293B', tickfont: { color: '#94A3B8' }, dtick: 2 },
    yaxis: { gridcolor: '#1E293B', tickfont: { color: '#94A3B8' }, title: { text: 'Leverage / Yield (%)', font: { color: '#94A3B8' } } },
    yaxis2: {
      gridcolor: '#1E293B',
      tickfont: { color: '#6366F1' },
      title: { text: 'BSE Sensex P/E', font: { color: '#6366F1' } },
      overlaying: 'y' as const,
      side: 'right' as const,
    },
    legend: { orientation: 'h' as const, y: -0.2, font: { color: '#CBD5E1' } },
    shapes: [
      { type: 'rect', xref: 'x', yref: 'paper', x0: 2008, x1: 2009, y0: 0, y1: 1, fillcolor: 'rgba(239, 68, 68, 0.12)', line: { width: 0 } },
      { type: 'rect', xref: 'x', yref: 'paper', x0: 2016, x1: 2019, y0: 0, y1: 1, fillcolor: 'rgba(99, 102, 241, 0.12)', line: { width: 0 } },
      { type: 'rect', xref: 'x', yref: 'paper', x0: 2020, x1: 2021, y0: 0, y1: 1, fillcolor: 'rgba(249, 115, 22, 0.12)', line: { width: 0 } },
    ],
  };

  // --- Chart 8: Lifecycle Donut & Top 10 Leveraged ---
  const donutTrace = [
    {
      values: data.lifecycle_distribution.map((d) => d.count),
      labels: data.lifecycle_distribution.map((d) => d.stage),
      marker: { colors: data.lifecycle_distribution.map((d) => d.color) },
      type: 'pie' as const,
      hole: 0.45,
      textinfo: 'label+percent',
      textposition: 'inside',
      insidetextorientation: 'radial',
    },
  ];

  const donutLayout = {
    title: { text: 'Life-Cycle Stage Distribution', font: { color: '#F8FAFC', size: 14 } },
    paper_bgcolor: 'transparent',
    plot_bgcolor: 'transparent',
    height: 320,
    margin: { t: 40, b: 20, l: 20, r: 20 },
    showlegend: false,
  };

  const top10Trace = [
    {
      x: data.top10_leveraged.map((d) => d.leverage),
      y: data.top10_leveraged.map((d) => d.company),
      type: 'bar' as const,
      orientation: 'h' as const,
      marker: { color: data.top10_leveraged.map((d) => d.color) },
      text: data.top10_leveraged.map((d) => `${d.leverage}%`),
      textposition: 'auto',
    },
  ];

  const top10Layout = {
    title: { text: 'Top 10 Most Leveraged Firms in Sample', font: { color: '#F8FAFC', size: 14 } },
    paper_bgcolor: 'transparent',
    plot_bgcolor: 'transparent',
    height: 320,
    margin: { t: 40, b: 30, l: 150, r: 30 },
    xaxis: { gridcolor: '#1E293B', tickfont: { color: '#94A3B8' }, title: { text: 'Avg Leverage (%)', font: { color: '#94A3B8' } } },
    yaxis: { tickfont: { color: '#E2E8F0', size: 10 } },
  };

  return (
    <div className="space-y-8 pb-12">
      {/* Header Bar */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-white/10 pb-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-white flex items-center gap-2">
            <BarChart2 className="h-6 w-6 text-cyan-400" />
            Executive Health Dashboard
          </h1>
          <p className="text-sm text-slate-400 mt-1">
            Empirical capital structure telemetry, stage-wise profiles, Tukey pairwise matrices, and macro sensitivity across Indian enterprises.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <span className="px-2.5 py-1 rounded-full text-xs font-mono font-medium bg-cyan-950/40 text-cyan-400 border border-cyan-800/40">
            {activePanel}
          </span>
          <span className="px-2.5 py-1 rounded-full text-xs font-mono font-medium bg-slate-800 text-slate-300 border border-slate-700">
            {yearMin} – {yearMax}
          </span>
        </div>
      </div>

      {/* 8 Bento Grid KPI Capsules */}
      <div>
        <div className="flex items-center justify-between mb-3">
          <div className="flex items-center gap-2">
            <Activity className="h-4 w-4 text-cyan-400" />
            <h2 className="text-xs font-bold uppercase tracking-wider text-slate-300">Executive Portfolio Metrics</h2>
          </div>
          <span className="text-[11px] text-slate-400 font-mono">Real-time aggregations (N=8,677)</span>
        </div>

        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
          {data.bento_kpis.map((kpi) => (
            <div
              key={kpi.id}
              className="relative overflow-hidden rounded-xl border border-white/10 bg-[#0c1220] p-4 shadow-sm hover:border-cyan-500/30 transition-all group"
            >
              <div className="flex items-center justify-between text-[11px] font-semibold tracking-wider text-slate-400 uppercase">
                <span>{kpi.label}</span>
                {kpi.badge && (
                  <span
                    className="px-1.5 py-0.5 rounded text-[10px] font-mono font-bold"
                    style={{
                      backgroundColor: `${kpi.badge_color || '#0D9488'}20`,
                      color: kpi.badge_color || '#0D9488',
                      border: `1px solid ${kpi.badge_color || '#0D9488'}40`,
                    }}
                  >
                    {kpi.badge}
                  </span>
                )}
              </div>

              <div className="mt-2 flex items-baseline justify-between">
                <span className="text-2xl font-bold font-mono tracking-tight text-white">{kpi.value}</span>
                {kpi.trend && (
                  <span
                    className={`text-xs font-mono font-medium flex items-center ${
                      kpi.trend.startsWith('+') ? 'text-amber-400' : 'text-emerald-400'
                    }`}
                  >
                    {kpi.trend.startsWith('+') ? <ArrowUpRight className="h-3 w-3 inline" /> : <ArrowDownRight className="h-3 w-3 inline" />}
                    {kpi.trend}
                  </span>
                )}
              </div>

              <div className="mt-1 text-[11px] text-slate-400 font-medium">{kpi.sublabel}</div>

              {/* Mini Sparkline Canvas/SVG */}
              {kpi.sparkline && kpi.sparkline.length > 0 && (
                <div className="mt-2.5 h-7 w-full">
                  <svg className="h-full w-full overflow-visible" preserveAspectRatio="none" viewBox="0 0 100 25">
                    {(() => {
                      const pts = kpi.sparkline;
                      const min = Math.min(...pts);
                      const max = Math.max(...pts);
                      const range = max - min || 1;
                      const path = pts
                        .map((v, i) => {
                          const x = (i / (pts.length - 1)) * 100;
                          const y = 25 - ((v - min) / range) * 22;
                          return `${i === 0 ? 'M' : 'L'} ${x.toFixed(1)} ${y.toFixed(1)}`;
                        })
                        .join(' ');
                      return (
                        <path
                          d={path}
                          fill="none"
                          stroke={kpi.color || '#0D9488'}
                          strokeWidth="2"
                          strokeLinecap="round"
                          strokeLinejoin="round"
                          className="opacity-80 group-hover:opacity-100 transition-opacity"
                        />
                      );
                    })()}
                  </svg>
                </div>
              )}
            </div>
          ))}
        </div>

        {/* Collapsible KPI Overview Insight Box */}
        <CollapsibleInsightBox
          title={data.kpi_overview_box.title}
          findings={data.kpi_overview_box.findings}
          actions={data.kpi_overview_box.actions}
          context={data.kpi_overview_box.context}
          hasAiInsights={true}
          defaultExpanded={true}
        />
      </div>

      {/* Section 1: Average Financial Leverage Over Time */}
      <div className="rounded-2xl border border-white/10 bg-[#0c1220] p-6 shadow-md">
        <PlotlyChart data={leverageTimeTraces} layout={leverageTimeLayout} />
        <CollapsibleInsightBox
          title={data.leverage_over_time.box.title}
          findings={data.leverage_over_time.box.findings}
          actions={data.leverage_over_time.box.actions}
          defaultExpanded={false}
        />
      </div>

      {/* Section 2: Figure 5.1 — Stage-wise Capital Structure Profile */}
      <div className="rounded-2xl border border-white/10 bg-[#0c1220] p-6 shadow-md space-y-4">
        <div>
          <h2 className="text-lg font-bold text-white tracking-tight">{data.fig51_stage_profile.title}</h2>
          <p className="text-xs text-slate-400 mt-0.5">{data.fig51_stage_profile.subtitle}</p>
        </div>

        {/* 4 horizontal subplots grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {fig51Metrics.map((m) => {
            const trace = [
              {
                x: stages51,
                y: m.values,
                type: 'bar' as const,
                marker: { color: stageBarColors },
                text: m.values.map((v) => `${v}${m.unit}`),
                textposition: 'auto',
              },
            ];
            const layout = {
              title: { text: m.title, font: { color: '#CBD5E1', size: 12 } },
              paper_bgcolor: 'transparent',
              plot_bgcolor: 'transparent',
              height: 220,
              margin: { t: 30, b: 35, l: 35, r: 15 },
              xaxis: { tickfont: { color: '#94A3B8', size: 9 }, tickangle: -20 },
              yaxis: { gridcolor: '#1E293B', tickfont: { color: '#94A3B8', size: 9 } },
            };
            return (
              <div key={m.key} className="rounded-xl border border-white/5 bg-black/20 p-2">
                <PlotlyChart data={trace} layout={layout} />
              </div>
            );
          })}
        </div>

        <CollapsibleInsightBox
          title={data.fig51_stage_profile.box.title}
          findings={data.fig51_stage_profile.box.findings}
          actions={data.fig51_stage_profile.box.actions}
          context={data.fig51_stage_profile.box.context}
          defaultExpanded={false}
        />
      </div>

      {/* Section 3: Figure 5.2 — Year-wise Capital Structure Trends */}
      <div className="rounded-2xl border border-white/10 bg-[#0c1220] p-6 shadow-md space-y-4">
        <div>
          <h2 className="text-lg font-bold text-white tracking-tight">{data.fig52_year_trends.title}</h2>
          <p className="text-xs text-slate-400 mt-0.5">{data.fig52_year_trends.subtitle}</p>
        </div>

        {/* 4 rows bar chart */}
        <div className="space-y-3">
          {fig52Metrics.map((m) => {
            const trace = [
              {
                x: years52,
                y: m.values,
                type: 'bar' as const,
                marker: { color: m.color },
              },
            ];
            const layout = {
              title: { text: m.title, font: { color: '#CBD5E1', size: 12 } },
              paper_bgcolor: 'transparent',
              plot_bgcolor: 'transparent',
              height: 170,
              margin: { t: 25, b: 30, l: 40, r: 15 },
              xaxis: { dtick: 2, tickfont: { color: '#94A3B8', size: 9 } },
              yaxis: { gridcolor: '#1E293B', tickfont: { color: '#94A3B8', size: 9 } },
            };
            return (
              <div key={m.key} className="rounded-xl border border-white/5 bg-black/20 p-2">
                <PlotlyChart data={trace} layout={layout} />
              </div>
            );
          })}
        </div>

        <CollapsibleInsightBox
          title={data.fig52_year_trends.box.title}
          findings={data.fig52_year_trends.box.findings}
          actions={data.fig52_year_trends.box.actions}
          context={data.fig52_year_trends.box.context}
          defaultExpanded={false}
        />
      </div>

      {/* Section 4: Figure 8.3 — Leverage vs Profitability and Tangibility */}
      <div className="rounded-2xl border border-white/10 bg-[#0c1220] p-6 shadow-md space-y-4">
        <div>
          <h2 className="text-lg font-bold text-white tracking-tight">{data.fig83_decline_decay.title}</h2>
          <p className="text-xs text-slate-400 mt-0.5">{data.fig83_decline_decay.subtitle}</p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="rounded-xl border border-white/5 bg-black/20 p-2">
            <PlotlyChart
              data={fig83RoaTraces}
              layout={{
                title: { text: 'Leverage vs Profitability (ROA)', font: { color: '#CBD5E1', size: 12 } },
                paper_bgcolor: 'transparent',
                plot_bgcolor: 'transparent',
                height: 280,
                margin: { t: 30, b: 40, l: 45, r: 15 },
                xaxis: { title: { text: 'ROA', font: { color: '#94A3B8' } }, gridcolor: '#1E293B', tickfont: { color: '#94A3B8' } },
                yaxis: { title: { text: 'Leverage (%)', font: { color: '#94A3B8' } }, gridcolor: '#1E293B', tickfont: { color: '#94A3B8' } },
                legend: { orientation: 'h' as const, y: -0.25, font: { color: '#CBD5E1', size: 10 } },
              }}
            />
          </div>

          <div className="rounded-xl border border-white/5 bg-black/20 p-2">
            <PlotlyChart
              data={fig83PpeTraces}
              layout={{
                title: { text: 'Leverage vs Tangibility (PPE/TA)', font: { color: '#CBD5E1', size: 12 } },
                paper_bgcolor: 'transparent',
                plot_bgcolor: 'transparent',
                height: 280,
                margin: { t: 30, b: 40, l: 45, r: 15 },
                xaxis: { title: { text: 'PPE / Total Assets', font: { color: '#94A3B8' } }, gridcolor: '#1E293B', tickfont: { color: '#94A3B8' } },
                yaxis: { title: { text: 'Leverage (%)', font: { color: '#94A3B8' } }, gridcolor: '#1E293B', tickfont: { color: '#94A3B8' } },
              }}
            />
          </div>
        </div>

        <CollapsibleInsightBox
          title={data.fig83_decline_decay.box.title}
          findings={data.fig83_decline_decay.box.findings}
          actions={data.fig83_decline_decay.box.actions}
          defaultExpanded={false}
        />
      </div>

      {/* Section 5: Table 5.9 — Pairwise Significance Matrix (Tukey HSD) */}
      <div className="rounded-2xl border border-white/10 bg-[#0c1220] p-6 shadow-md space-y-4">
        <div>
          <h2 className="text-lg font-bold text-white tracking-tight">{pwData.title}</h2>
          <p className="text-xs text-slate-400 mt-0.5">{pwData.subtitle}</p>
        </div>

        <div className="rounded-xl border border-white/5 bg-black/20 p-3">
          <PlotlyChart data={pwHeatmapTrace} layout={pwLayout} />
        </div>

        {/* Significant Pair Callout Cards */}
        {pwData.significant_callouts && pwData.significant_callouts.length > 0 && (
          <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-3">
            {pwData.significant_callouts.map((c, idx) => (
              <div key={idx} className="rounded-xl border border-red-500/20 bg-red-950/20 p-3.5 space-y-1">
                <div className="flex items-center justify-between">
                  <span className="font-bold text-xs text-white">{c.pair}</span>
                  <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-red-500/30 text-red-200">
                    {c.p_val}
                  </span>
                </div>
                <div className="text-sm font-mono font-bold text-red-400">{c.diff}</div>
                <div className="text-[11px] text-slate-300 leading-snug">{c.interpretation}</div>
              </div>
            ))}
          </div>
        )}

        <CollapsibleInsightBox
          title={pwData.box.title}
          findings={pwData.box.findings}
          actions={pwData.box.actions}
          context={pwData.box.context}
          defaultExpanded={false}
        />
      </div>

      {/* Section 6: Determinant Profiles by Life Stage Heatmap */}
      <div className="rounded-2xl border border-white/10 bg-[#0c1220] p-6 shadow-md space-y-4">
        <div>
          <h2 className="text-lg font-bold text-white tracking-tight">{detData.title}</h2>
          <p className="text-xs text-slate-400 mt-0.5">{detData.subtitle}</p>
        </div>

        <div className="rounded-xl border border-white/5 bg-black/20 p-3">
          <PlotlyChart data={detHeatmapTrace} layout={detLayout} />
        </div>

        <CollapsibleInsightBox
          title={detData.box.title}
          findings={detData.box.findings}
          actions={detData.box.actions}
          context={detData.box.context}
          defaultExpanded={false}
        />
      </div>

      {/* Section 7: Macro Context Dual-Axis Line Chart */}
      <div className="rounded-2xl border border-white/10 bg-[#0c1220] p-6 shadow-md space-y-4">
        <PlotlyChart data={macroTraces} layout={macroLayout} />
        <CollapsibleInsightBox
          title={data.macro_context.box.title}
          findings={data.macro_context.box.findings}
          actions={data.macro_context.box.actions}
          defaultExpanded={false}
        />
      </div>

      {/* Section 8: Lifecycle Distribution & Top 10 Most Leveraged Firms */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div className="rounded-2xl border border-white/10 bg-[#0c1220] p-5 shadow-md">
          <PlotlyChart data={donutTrace} layout={donutLayout} />
        </div>

        <div className="rounded-2xl border border-white/10 bg-[#0c1220] p-5 shadow-md">
          <PlotlyChart data={top10Trace} layout={top10Layout} />
        </div>
      </div>

      {/* Section 9: Master Results Interpretation Panel */}
      <ResultsInterpretationPanel
        title={data.results_interpretation.title}
        subtitle={data.results_interpretation.subtitle}
        insights={data.results_interpretation.insights}
        actions={data.results_interpretation.actions}
        methodologyCitation={data.results_interpretation.methodologyCitation}
      />
    </div>
  );
};
