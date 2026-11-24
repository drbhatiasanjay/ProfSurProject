import React, { useState, useEffect, useMemo } from 'react';
import { ChartContainer } from '../shared/ChartContainer';
import { PlotlyChart } from '../shared/PlotlyChart';
import { CollapsibleInsightBox } from '../shared/CollapsibleInsightBox';
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
  Sparkles,
  BookOpen,
  Target,
  CheckCircle2,
} from 'lucide-react';
import { getCrisisEventBands } from '../../utils/crisisBands';

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
    color: string;
    count: number;
    min: number;
    q1: number;
    median: number;
    q3: number;
    max: number;
    mean: number;
    values: number[];
  }>;
  diamond_point: {
    stage: string;
    leverage: number;
    company_name: string;
  };
  radar_data: {
    metrics: string[];
    labels: string[];
    company_vals: number[];
    industry_vals: number[];
    stage_vals: number[];
    raw_company: number[];
    raw_industry: number[];
    raw_stage: number[];
    comp_stage: string;
  };
  insights: {
    leverage?: { findings: string[]; actions: string[] };
    profitability?: { findings: string[]; actions: string[] };
    radar?: { findings: string[]; actions: string[] };
  };
  interpretation: {
    findings: string[];
    actions: string[];
    citation: string;
  };
  event_bands: Array<{
    year: number;
    name: string;
  }>;
}

interface SectorPeerBenchmarksProps {
  activePanel: string;
  yearMin: number;
  yearMax: number;
  theme?: 'dark' | 'light';
}

function formatMarkdown(text: string): string {
  if (!text) return '';
  return text
    .replace(/\*\*(.*?)\*\*/g, '<strong class="text-white font-semibold">$1</strong>')
    .replace(/\*(.*?)\*/g, '<em class="text-slate-200 italic">$1</em>');
}

const STAGE_ORDER = ['Startup', 'Growth', 'Maturity', 'Shakeout1', 'Shakeout2', 'Shakeout3', 'Decline', 'Decay'];

export const SectorPeerBenchmarks: React.FC<SectorPeerBenchmarksProps> = ({
  activePanel,
  yearMin,
  yearMax,
  theme = 'dark',
}) => {
  const [companies, setCompanies] = useState<CompanyItem[]>([]);
  // 3M India Ltd. default company code: 36277
  const [selectedCode, setSelectedCode] = useState<number>(36277);
  const [data, setData] = useState<BenchmarkData | null>(null);
  const [loading, setLoading] = useState<boolean>(true);

  // 1. Fetch company directory and sort alphabetically
  useEffect(() => {
    fetch('http://localhost:8000/api/cmie/companies')
      .then((res) => {
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        return res.json();
      })
      .then((resData) => {
        if (resData && resData.companies) {
          // Sort alphabetically by company_name
          const sorted = [...resData.companies].sort((a: CompanyItem, b: CompanyItem) =>
            a.company_name.localeCompare(b.company_name)
          );
          setCompanies(sorted);

          // Find 3M India Ltd. to ensure initial default is always on 3M India Ltd.
          const m3 = sorted.find((c: CompanyItem) =>
            c.company_name.toLowerCase().includes('3m india')
          ) || sorted[0];

          if (m3) {
            setSelectedCode(m3.company_code);
          }
        }
      })
      .catch((err) => console.error('Failed to load company directory:', err));
  }, []);

  // 2. Fetch peer benchmarks when selectedCode or filters change
  useEffect(() => {
    if (!selectedCode) return;
    setLoading(true);
    const panelId = activePanel.toLowerCase().replace(/[^a-z0-9]/g, '_');
    const url = `http://localhost:8000/api/cmie/peer-benchmarks?company_code=${selectedCode}&panel=${encodeURIComponent(
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

  // Crisis event bands
  const { shapes: crisisShapes, annotations: crisisAnnotations } = useMemo(() => {
    return getCrisisEventBands(true);
  }, []);

  // ── 1. Chart 1: Leverage: Company vs Industry Average ──
  const { leverageChartData, leverageChartLayout } = useMemo(() => {
    if (!data) return { leverageChartData: [], leverageChartLayout: {} };

    const { company_info, company_series, industry_series } = data;

    const traces: any[] = [
      {
        x: company_series.map((d) => d.year),
        y: company_series.map((d) => d.leverage),
        name: company_info.company_name,
        mode: 'lines+markers',
        line: { color: '#0D9488', width: 3 },
        marker: { size: 6, color: '#0D9488' },
        type: 'scatter',
      },
      {
        x: industry_series.map((d) => d.year),
        y: industry_series.map((d) => d.industry_leverage),
        name: `Industry Avg (${company_info.industry_group})`,
        mode: 'lines',
        line: { color: '#F97316', width: 2, dash: 'dash' },
        type: 'scatter',
      },
    ];

    const layout: any = {
      font: { family: 'Inter, system-ui, sans-serif', size: 12, color: '#F8FAFC' },
      plot_bgcolor: 'rgba(0,0,0,0)',
      paper_bgcolor: 'rgba(0,0,0,0)',
      margin: { l: 50, r: 25, t: 30, b: 60 },
      height: 380,
      showlegend: true,
      legend: {
        orientation: 'h',
        yanchor: 'top',
        y: -0.18,
        xanchor: 'center',
        x: 0.5,
        font: { color: '#F8FAFC', size: 11 },
      },
      xaxis: {
        range: [yearMin, yearMax],
        gridcolor: 'rgba(255, 255, 255, 0.08)',
        tickcolor: '#94A3B8',
        tickfont: { color: '#94A3B8', size: 11 },
        title: { text: 'Fiscal Year', font: { color: '#94A3B8', size: 11 } },
      },
      yaxis: {
        gridcolor: 'rgba(255, 255, 255, 0.08)',
        tickcolor: '#94A3B8',
        tickfont: { color: '#94A3B8', size: 11 },
        title: { text: 'Leverage (%)', font: { color: '#94A3B8', size: 11 } },
      },
      shapes: crisisShapes,
      annotations: crisisAnnotations,
    };

    return { leverageChartData: traces, leverageChartLayout: layout };
  }, [data, yearMin, yearMax, crisisShapes, crisisAnnotations]);

  // ── 2. Chart 2: Profitability: Company vs Industry Average ──
  const { profitabilityChartData, profitabilityChartLayout } = useMemo(() => {
    if (!data) return { profitabilityChartData: [], profitabilityChartLayout: {} };

    const { company_info, company_series, industry_series } = data;

    const traces: any[] = [
      {
        x: company_series.map((d) => d.year),
        y: company_series.map((d) => d.profitability),
        name: company_info.company_name,
        mode: 'lines+markers',
        line: { color: '#0D9488', width: 3 },
        marker: { size: 6, color: '#0D9488' },
        type: 'scatter',
      },
      {
        x: industry_series.map((d) => d.year),
        y: industry_series.map((d) => d.industry_profitability),
        name: 'Industry Avg',
        mode: 'lines',
        line: { color: '#F97316', width: 2, dash: 'dash' },
        type: 'scatter',
      },
    ];

    const layout: any = {
      font: { family: 'Inter, system-ui, sans-serif', size: 12, color: '#F8FAFC' },
      plot_bgcolor: 'rgba(0,0,0,0)',
      paper_bgcolor: 'rgba(0,0,0,0)',
      margin: { l: 50, r: 25, t: 30, b: 60 },
      height: 380,
      showlegend: true,
      legend: {
        orientation: 'h',
        yanchor: 'top',
        y: -0.18,
        xanchor: 'center',
        x: 0.5,
        font: { color: '#F8FAFC', size: 11 },
      },
      xaxis: {
        range: [yearMin, yearMax],
        gridcolor: 'rgba(255, 255, 255, 0.08)',
        tickcolor: '#94A3B8',
        tickfont: { color: '#94A3B8', size: 11 },
        title: { text: 'Fiscal Year', font: { color: '#94A3B8', size: 11 } },
      },
      yaxis: {
        gridcolor: 'rgba(255, 255, 255, 0.08)',
        tickcolor: '#94A3B8',
        tickfont: { color: '#94A3B8', size: 11 },
        title: { text: 'Profitability (ROA)', font: { color: '#94A3B8', size: 11 } },
      },
      shapes: crisisShapes,
      annotations: crisisAnnotations,
    };

    return { profitabilityChartData: traces, profitabilityChartLayout: layout };
  }, [data, yearMin, yearMax, crisisShapes, crisisAnnotations]);

  // ── 3. Chart 3: Leverage Distribution by Life Stage (8-Stage Box Plot + Diamond Marker) ──
  const { boxPlotData, boxPlotLayout } = useMemo(() => {
    if (!data) return { boxPlotData: [], boxPlotLayout: {} };

    const { stage_box_data, diamond_point } = data;

    // Traces for each of the 8 Dickinson stages
    const traces: any[] = stage_box_data.map((box) => ({
      type: 'box',
      name: box.stage,
      y: box.values,
      marker: { color: box.color, size: 4 },
      boxpoints: 'outliers',
      jitter: 0.25,
      pointpos: 0,
    }));

    // High-visibility Diamond marker placed at company dominant stage & average leverage
    if (diamond_point && diamond_point.stage) {
      traces.push({
        type: 'scatter',
        mode: 'markers',
        name: diamond_point.company_name,
        x: [diamond_point.stage],
        y: [diamond_point.leverage],
        marker: {
          size: 14,
          color: '#111827',
          symbol: 'diamond',
          line: { width: 2.5, color: '#FFFFFF' },
        },
      });
    }

    const layout: any = {
      font: { family: 'Inter, system-ui, sans-serif', size: 12, color: '#F8FAFC' },
      plot_bgcolor: 'rgba(0,0,0,0)',
      paper_bgcolor: 'rgba(0,0,0,0)',
      margin: { l: 50, r: 25, t: 30, b: 70 },
      height: 420,
      showlegend: true,
      legend: {
        orientation: 'h',
        yanchor: 'top',
        y: -0.22,
        xanchor: 'center',
        x: 0.5,
        font: { color: '#F8FAFC', size: 10 },
      },
      xaxis: {
        categoryorder: 'array',
        categoryarray: STAGE_ORDER,
        gridcolor: 'rgba(255, 255, 255, 0.08)',
        tickcolor: '#94A3B8',
        tickfont: { color: '#94A3B8', size: 11 },
      },
      yaxis: {
        title: { text: 'Leverage (%)', font: { color: '#94A3B8', size: 11 } },
        gridcolor: 'rgba(255, 255, 255, 0.08)',
        tickcolor: '#94A3B8',
        tickfont: { color: '#94A3B8', size: 11 },
      },
    };

    return { boxPlotData: traces, boxPlotLayout: layout };
  }, [data]);

  // ── 4. Chart 4: Multi-Determinant Profile (Polar Radar with 6 Normalized Axes) ──
  const { radarChartData, radarChartLayout } = useMemo(() => {
    if (!data) return { radarChartData: [], radarChartLayout: {} };

    const { company_info, radar_data } = data;
    const { labels, company_vals, industry_vals, stage_vals, comp_stage } = radar_data;

    // Close the polygon by repeating the first item
    const rCompany = [...company_vals, company_vals[0]];
    const rIndustry = [...industry_vals, industry_vals[0]];
    const rStage = [...stage_vals, stage_vals[0]];
    const thetaLabels = [...labels, labels[0]];

    const traces: any[] = [
      {
        type: 'scatterpolar',
        r: rCompany,
        theta: thetaLabels,
        fill: 'toself',
        name: company_info.company_name,
        fillcolor: 'rgba(13, 148, 136, 0.18)',
        line: { color: '#0D9488', width: 2.5 },
      },
      {
        type: 'scatterpolar',
        r: rIndustry,
        theta: thetaLabels,
        fill: 'toself',
        name: 'Industry Avg',
        fillcolor: 'rgba(249, 115, 22, 0.12)',
        line: { color: '#F97316', width: 2, dash: 'dash' },
      },
      {
        type: 'scatterpolar',
        r: rStage,
        theta: thetaLabels,
        fill: 'toself',
        name: `Stage Avg (${comp_stage})`,
        fillcolor: 'rgba(99, 102, 241, 0.12)',
        line: { color: '#6366F1', width: 2, dash: 'dot' },
      },
    ];

    const layout: any = {
      font: { family: 'Inter, system-ui, sans-serif', size: 12, color: '#F8FAFC' },
      plot_bgcolor: 'rgba(0,0,0,0)',
      paper_bgcolor: 'rgba(0,0,0,0)',
      margin: { l: 45, r: 45, t: 30, b: 65 },
      height: 420,
      showlegend: true,
      legend: {
        orientation: 'h',
        yanchor: 'top',
        y: -0.16,
        xanchor: 'center',
        x: 0.5,
        font: { color: '#F8FAFC', size: 11 },
      },
      polar: {
        radialaxis: {
          visible: true,
          range: [0, 100],
          gridcolor: 'rgba(255, 255, 255, 0.1)',
          linecolor: 'rgba(255, 255, 255, 0.15)',
          tickfont: { color: '#94A3B8', size: 10 },
        },
        angularaxis: {
          gridcolor: 'rgba(255, 255, 255, 0.1)',
          linecolor: 'rgba(255, 255, 255, 0.15)',
          tickfont: { color: '#CBD5E1', size: 11, weight: 'bold' },
        },
      },
    };

    return { radarChartData: traces, radarChartLayout: layout };
  }, [data]);

  // CSV Export handlers
  const exportLeverageCsv = () => {
    if (!data) return;
    let csv = `Year,${data.company_info.company_name}_Leverage,Industry_Avg_Leverage\n`;
    const years = Array.from(new Set([...data.company_series.map((d) => d.year), ...data.industry_series.map((d) => d.year)])).sort();
    for (const yr of years) {
      const c = data.company_series.find((d) => d.year === yr);
      const ind = data.industry_series.find((d) => d.year === yr);
      csv += `${yr},${c?.leverage ?? ''},${ind?.industry_leverage ?? ''}\n`;
    }
    downloadCsv(csv, `${data.company_info.nse_symbol || 'company'}_leverage_vs_industry.csv`);
  };

  const exportProfitabilityCsv = () => {
    if (!data) return;
    let csv = `Year,${data.company_info.company_name}_ROA,Industry_Avg_ROA\n`;
    const years = Array.from(new Set([...data.company_series.map((d) => d.year), ...data.industry_series.map((d) => d.year)])).sort();
    for (const yr of years) {
      const c = data.company_series.find((d) => d.year === yr);
      const ind = data.industry_series.find((d) => d.year === yr);
      csv += `${yr},${c?.profitability ?? ''},${ind?.industry_profitability ?? ''}\n`;
    }
    downloadCsv(csv, `${data.company_info.nse_symbol || 'company'}_profitability_vs_industry.csv`);
  };

  const exportBoxCsv = () => {
    if (!data) return;
    let csv = 'Stage,Count,Min,Q1,Median,Q3,Max,Mean\n';
    for (const b of data.stage_box_data) {
      csv += `${b.stage},${b.count},${b.min},${b.q1},${b.median},${b.q3},${b.max},${b.mean}\n`;
    }
    downloadCsv(csv, 'leverage_distribution_by_stage.csv');
  };

  const exportRadarCsv = () => {
    if (!data) return;
    const { labels, company_vals, industry_vals, stage_vals, raw_company, raw_industry, raw_stage, comp_stage } = data.radar_data;
    let csv = `Metric,${data.company_info.company_name}_Score,Industry_Avg_Score,Stage_${comp_stage}_Score,${data.company_info.company_name}_Raw,Industry_Raw,Stage_Raw\n`;
    for (let i = 0; i < labels.length; i++) {
      csv += `${labels[i]},${company_vals[i]},${industry_vals[i]},${stage_vals[i]},${raw_company[i]},${raw_industry[i]},${raw_stage[i]}\n`;
    }
    downloadCsv(csv, `${data.company_info.nse_symbol || 'company'}_multi_determinant_profile.csv`);
  };

  const downloadCsv = (content: string, filename: string) => {
    const blob = new Blob([content], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    link.href = URL.createObjectURL(blob);
    link.download = filename;
    link.click();
  };

  if (loading && !data) {
    return (
      <div className="bg-[#0d1527] border border-white/10 rounded-2xl p-12 text-center">
        <div className="inline-block w-8 h-8 border-2 border-cyan-400 border-t-transparent rounded-full animate-spin mb-3" />
        <p className="text-sm text-slate-300 font-medium">
          Loading peer benchmarks and empirical cross-sectional distributions...
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

  const { company_info, insights, interpretation } = data;

  return (
    <div className="space-y-6">
      {/* Studio Header Card */}
      <div className="bg-[#0d1527] border border-cyan-500/20 rounded-2xl p-6 shadow-xl">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-4 border-b border-white/10">
          <div>
            <div className="flex items-center gap-2">
              <span className="text-[11px] font-bold text-cyan-400 uppercase tracking-wider font-mono">
                Studio 02 &middot; Peer Intelligence
              </span>
              <span className="px-2 py-0.5 rounded-full bg-cyan-500/10 text-cyan-300 text-[10px] font-semibold border border-cyan-500/30">
                CMIE Prowess
              </span>
            </div>
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
            <div className="relative min-w-[280px]">
              <label className="block text-[10px] font-bold text-slate-400 uppercase tracking-wider mb-1">
                Select Enterprise (Alphabetical)
              </label>
              <div className="relative">
                <select
                  value={selectedCode}
                  onChange={(e) => setSelectedCode(Number(e.target.value))}
                  className="w-full bg-slate-950 border border-cyan-500/40 rounded-lg px-3 py-2 text-xs font-semibold text-slate-100 focus:outline-none focus:border-cyan-400 appearance-none cursor-pointer pr-8 shadow-inner"
                >
                  {companies.map((c) => (
                    <option key={c.company_code} value={c.company_code}>
                      {c.company_name} {c.nse_symbol ? `(${c.nse_symbol})` : ''}
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
        <div className="mt-4 p-4 bg-slate-900/80 border border-white/10 rounded-xl flex flex-wrap items-center justify-between gap-4 text-xs shadow-inner">
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
              <span className="font-bold text-cyan-300">{(company_info.avg_profitability * 100).toFixed(1)}%</span>
            </div>
            <div>
              <span className="text-[10px] text-slate-500 block uppercase">Total Borrowings</span>
              <span className="font-bold text-slate-100">₹{company_info.current_borrowings.toLocaleString()} Cr</span>
            </div>
            <div>
              <span className="text-[10px] text-slate-500 block uppercase">Panel Span</span>
              <span className="font-bold text-slate-400">{company_info.n_years} Years</span>
            </div>
          </div>
        </div>

        {/* ── Row 1: Dual Time Series Charts ── */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mt-6">
          {/* Chart 1: Leverage: Company vs Industry Average */}
          <div>
            <ChartContainer
              title="Leverage: Company vs Industry Average"
              subtitle={`Comparing firm leverage against ${company_info.industry_group} peers`}
              sampleBadge="Longitudinal"
              sourceAttribution="CMIE Prowess Database (2001–2025)"
              onExportCsv={exportLeverageCsv}
              methodologyFormula="\text{Leverage Gap}_{t} = \text{Leverage}_{i,t} - \overline{\text{Leverage}}_{\text{Industry},t}"
              methodologyDescription="Identifies whether the target enterprise operates with conservative capital headroom or aggressive structural gearing relative to industry rivals."
            >
              <PlotlyChart
                data={leverageChartData}
                layout={leverageChartLayout}
                config={{ responsive: true, displayModeBar: true }}
              />
            </ChartContainer>

            {/* Collapsible Insight Box */}
            <CollapsibleInsightBox
              title="Leverage Comparison — Company vs Industry"
              findings={insights.leverage?.findings || []}
              actions={insights.leverage?.actions || []}
              context={`Comparing ${company_info.company_name} average leverage against industry peers.`}
            />
          </div>

          {/* Chart 2: Profitability: Company vs Industry Average */}
          <div>
            <ChartContainer
              title="Profitability: Company vs Industry Average"
              subtitle="Comparing operating return on assets (ROA) over time"
              sampleBadge="Longitudinal"
              sourceAttribution="CMIE Prowess Database (2001–2025)"
              onExportCsv={exportProfitabilityCsv}
              methodologyFormula="\text{ROA}_{i,t} = \frac{\text{Profit After Tax}_{i,t}}{\text{Total Assets}_{i,t}}"
              methodologyDescription="Pecking order theory predicts that firms with superior ROA generate substantial internal cash surpluses, mitigating debt requirements."
            >
              <PlotlyChart
                data={profitabilityChartData}
                layout={profitabilityChartLayout}
                config={{ responsive: true, displayModeBar: true }}
              />
            </ChartContainer>

            {/* Collapsible Insight Box */}
            <CollapsibleInsightBox
              title="Profitability Comparison"
              findings={insights.profitability?.findings || []}
              actions={insights.profitability?.actions || []}
              context={`Comparing ${company_info.company_name} profitability against industry peers.`}
            />
          </div>
        </div>

        {/* ── Row 2: Life Stage Box Plots + Multi-Determinant Radar ── */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mt-6">
          {/* Chart 3: Life Stage Quantile Distribution */}
          <div>
            <ChartContainer
              title="Leverage Distribution by Life Stage"
              subtitle="Cross-sectional distribution with diamond marker indicating selected company"
              sampleBadge="8 Stages · Dickinson (2011)"
              sourceAttribution="Dickinson (2011) Classification"
              onExportCsv={exportBoxCsv}
              methodologyFormula="\text{IQR} = Q_3 - Q_1, \quad \text{Whiskers: } [\min, \max]"
              methodologyDescription="Box plot representation showing median, interquartile range, and whiskers. Selected enterprise marked with high-visibility diamond (◆)."
            >
              <PlotlyChart
                data={boxPlotData}
                layout={boxPlotLayout}
                config={{ responsive: true, displayModeBar: true }}
              />
            </ChartContainer>

            {/* Collapsible Insight Box */}
            <CollapsibleInsightBox
              title="Life-Cycle Quantile Distribution"
              findings={[
                `**${company_info.company_name}** sits at **${company_info.avg_leverage}%** average leverage within the **${company_info.dominant_stage}** cohort.`,
                'The high-visibility diamond marker (◆) identifies empirical leverage positioning relative to 8,677 firm-year observations across all 8 life-cycle stages.',
              ]}
              actions={[
                `Benchmark ongoing capital structure targets against the ${company_info.dominant_stage} cohort distribution rather than aggregate market averages.`,
                'Evaluate whether deviation from the median reflects superior operational cash generation or debt capacity constraints.',
              ]}
              context="Demonstrates empirical leverage distribution across Dickinson (2011) lifecycle stages. Diamond marker indicates target company placement."
            />
          </div>

          {/* Chart 4: Multi-Determinant Profile (Radar) */}
          <div>
            <ChartContainer
              title="Multi-Determinant Profile (Radar)"
              subtitle="Normalized 0–100 percentile scores across 6 key balance sheet metrics"
              sampleBadge="6 Dimensions"
              sourceAttribution="Panel Financials"
              onExportCsv={exportRadarCsv}
              methodologyFormula="\text{Norm Score} = \frac{x - x_{\min}}{x_{\max} - x_{\min}} \times 100"
              methodologyDescription="Demonstrates cross-metric structural advantages and debt determinants relative to the sector baseline and life-stage cohort."
            >
              <PlotlyChart
                data={radarChartData}
                layout={radarChartLayout}
                config={{ responsive: true, displayModeBar: true }}
              />
            </ChartContainer>

            {/* Collapsible Insight Box */}
            <CollapsibleInsightBox
              title="Multi-Determinant Profile — Strategic Assessment"
              findings={insights.radar?.findings || []}
              actions={insights.radar?.actions || []}
              context="Identifies where the firm diverges from industry and life-stage peers across 6 dimensions."
            />
          </div>
        </div>

        {/* ── Bottom Section: Master Results Interpretation & Call to Action Panel ── */}
        <div className="mt-8 bg-[#090f1d] border border-cyan-500/30 rounded-2xl p-6 shadow-2xl">
          <div className="flex items-center gap-2.5 pb-4 border-b border-white/10">
            <div className="p-2 rounded-lg bg-cyan-500/10 border border-cyan-500/20 text-cyan-400">
              <Target className="w-5 h-5" />
            </div>
            <div>
              <h3 className="text-lg font-bold text-white tracking-tight flex items-center gap-2">
                Results Interpretation &amp; Call to Action
              </h3>
              <p className="text-xs text-slate-400">
                Synthesized cross-sectional peer benchmark findings and strategic financing guidance
              </p>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mt-5 text-xs text-slate-300">
            {/* Key Findings */}
            <div className="space-y-3 bg-slate-900/60 border border-white/5 rounded-xl p-4">
              <span className="text-[11px] font-bold text-cyan-300 uppercase tracking-wider flex items-center gap-1.5 font-mono">
                <Sparkles className="w-3.5 h-3.5" />
                Key Findings:
              </span>
              <ul className="space-y-2 list-disc list-inside">
                {interpretation.findings.map((f, idx) => (
                  <li key={idx} className="leading-relaxed" dangerouslySetInnerHTML={{ __html: formatMarkdown(f) }} />
                ))}
              </ul>
            </div>

            {/* Call to Action */}
            <div className="space-y-3 bg-slate-900/60 border border-white/5 rounded-xl p-4">
              <span className="text-[11px] font-bold text-emerald-300 uppercase tracking-wider flex items-center gap-1.5 font-mono">
                <Target className="w-3.5 h-3.5" />
                Call to Action:
              </span>
              <ul className="space-y-2">
                {interpretation.actions.map((a, idx) => (
                  <li key={idx} className="flex items-start gap-2 leading-relaxed">
                    <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400 shrink-0 mt-0.5" />
                    <span dangerouslySetInnerHTML={{ __html: formatMarkdown(a) }} />
                  </li>
                ))}
              </ul>
            </div>
          </div>

          {/* Academic Attribution Footer */}
          <div className="mt-5 pt-4 border-t border-white/10 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 text-[11px] text-slate-400">
            <div className="flex items-center gap-2">
              <BookOpen className="w-4 h-4 text-cyan-400" />
              <span>
                Methodology based on <strong>{interpretation.citation}</strong>
              </span>
            </div>
            <div className="font-mono text-slate-500">
              CMIE Prowess &middot; 8,677 Panel Universe
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
