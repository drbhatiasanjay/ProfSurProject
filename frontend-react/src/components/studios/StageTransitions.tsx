import React, { useState, useEffect } from 'react';
import {
  TrendingDown,
  Layers,
  Activity,
  Clock,
  Zap,
  ExternalLink,
  Info,
  ChevronDown,
  ChevronUp,
  Download,
  Flame,
  ShieldAlert,
} from 'lucide-react';
import { PlotlyChart } from '../shared/PlotlyChart';
import { ResultsInterpretationPanel } from '../shared/ResultsInterpretationPanel';

interface KmCurve {
  stage: string;
  color: string;
  timeline: number[];
  survival: number[];
  ci_lower: number[];
  ci_upper: number[];
  points: { time_years: number; survival_rate: number }[];
}

interface KmSummaryRow {
  stage: string;
  color: string;
  n_spells: number;
  n_transitions: number;
  median_duration: string;
  five_yr_survival: number | null;
}

interface HazardRatioRow {
  variable: string;
  hazard_ratio: number;
  p_value: number;
  interpretation: string;
  diff_from_1: number;
  color: string;
  is_significant: boolean;
}

interface TransitionMatrixData {
  stages_y: string[];
  stages_x: string[];
  z: number[][];
  flat: { from_stage: string; to_stage: string; probability: number }[];
  colorscale: string[];
}

interface TransitionsData {
  kpis: {
    n_spells: number;
    n_transitions: number;
    n_firms: number;
    transition_rate: number;
    median_spell_years: number;
    sticky_benchmark_stage?: string;
    fastest_exit_stage?: string;
  };
  km_curves: KmCurve[];
  km_summary: KmSummaryRow[];
  hazard_ratios: HazardRatioRow[];
  matrix: TransitionMatrixData;
  interpretation: {
    title: string;
    insights: string[];
    actions: string[];
  };
}

interface StageTransitionsProps {
  activePanel: string;
  yearMin: number;
  yearMax: number;
}

const STAGE_COLORS: Record<string, string> = {
  Startup: '#F97316',
  Growth: '#22C55E',
  Maturity: '#0D9488',
  Shakeout1: '#A78BFA',
  Shakeout2: '#8B5CF6',
  Shakeout3: '#6366F1',
  Decline: '#EF4444',
  Decay: '#991B1B',
};

export const StageTransitions: React.FC<StageTransitionsProps> = ({
  activePanel,
  yearMin,
  yearMax,
}) => {
  const [data, setData] = useState<TransitionsData | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [selectedCurveStage, setSelectedCurveStage] = useState<string>('All Stages');
  const [showTheory, setShowTheory] = useState<boolean>(false);

  useEffect(() => {
    setLoading(true);
    const panelId = activePanel.toLowerCase().replace(/[^a-z0-9]/g, '_');
    const url = `http://localhost:8000/api/cmie/stage-transitions?panel=${encodeURIComponent(
      panelId
    )}&year_min=${yearMin}&year_max=${yearMax}`;

    fetch(url)
      .then((res) => {
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        return res.json();
      })
      .then((resData: TransitionsData) => {
        setData(resData);
        setLoading(false);
      })
      .catch((err) => {
        console.error('Failed to load stage transitions:', err);
        setLoading(false);
      });
  }, [activePanel, yearMin, yearMax]);

  if (loading) {
    return (
      <div className="bg-[#0d1527] border border-white/10 rounded-2xl p-16 text-center shadow-2xl">
        <div className="inline-block w-10 h-10 border-3 border-cyan-400 border-t-transparent rounded-full animate-spin mb-4" />
        <p className="text-base text-slate-200 font-semibold">
          Fitting Kaplan-Meier survival curves and calculating Markov transition rates...
        </p>
        <p className="text-xs text-slate-400 mt-1">
          Evaluating Dickinson life-stage durations and Cox Proportional Hazards covariates
        </p>
      </div>
    );
  }

  if (!data) {
    return (
      <div className="bg-rose-950/20 border border-rose-500/30 rounded-2xl p-8 text-center text-rose-300 text-sm">
        Failed to load survival transitions data for active panel filters.
      </div>
    );
  }

  const { kpis, km_curves, km_summary, hazard_ratios, matrix, interpretation } = data;

  // Filter KM Curves
  const displayedCurves =
    selectedCurveStage === 'All Stages'
      ? km_curves
      : km_curves.filter((c) => c.stage === selectedCurveStage);

  // Plotly KM Data
  const kmPlotTraces: any[] = [];
  displayedCurves.forEach((curve) => {
    const color = STAGE_COLORS[curve.stage] || curve.color || '#0D9488';

    // Confidence Interval Ribbon if available
    if (curve.ci_lower && curve.ci_upper && curve.ci_lower.length > 0) {
      kmPlotTraces.push({
        x: [...curve.timeline, ...curve.timeline.slice().reverse()],
        y: [...curve.ci_upper, ...curve.ci_lower.slice().reverse()],
        fill: 'toself',
        fillcolor: color.startsWith('#')
          ? `rgba(${parseInt(color.slice(1, 3), 16)}, ${parseInt(color.slice(3, 5), 16)}, ${parseInt(
              color.slice(5, 7),
              16
            )}, 0.12)`
          : 'rgba(13, 148, 136, 0.12)',
        line: { width: 0 },
        showlegend: false,
        hoverinfo: 'skip',
        type: 'scatter',
      });
    }

    // Step function line
    kmPlotTraces.push({
      x: curve.timeline,
      y: curve.survival,
      mode: 'lines',
      name: curve.stage,
      line: { color: color, width: 2.5, shape: 'hv' },
      type: 'scatter',
      hovertemplate: `<b>${curve.stage}</b><br>Duration: %{x} yrs<br>Survival: %{y:.1%}<extra></extra>`,
    });
  });

  // Plotly Cox Hazard Ratio Bar Data
  const hrSorted = [...hazard_ratios].reverse();
  const coxPlotTraces = [
    {
      x: hrSorted.map((r) => r.diff_from_1),
      y: hrSorted.map((r) => r.variable),
      orientation: 'h',
      type: 'bar',
      marker: {
        color: hrSorted.map((r) => (r.hazard_ratio > 1 ? '#0D9488' : '#EF4444')),
      },
      text: hrSorted.map((r) => `HR=${r.hazard_ratio.toFixed(2)}`),
      textposition: 'outside',
      textfont: { color: '#F8FAFC', size: 12 },
      cliponaxis: false,
      customdata: hrSorted.map((r) => r.hazard_ratio),
      hovertemplate:
        '<b>%{y}</b><br>Hazard Ratio: %{customdata:.3f}<br>Transition Effect: %{x:+.1%}<extra></extra>',
    },
  ];

  // Plotly Heatmap Data
  const heatmapTraces = [
    {
      z: matrix.z,
      x: matrix.stages_x,
      y: matrix.stages_y,
      type: 'heatmap',
      colorscale: [
        [0.0, '#0E1626'],
        [0.5, '#0D9488'],
        [1.0, '#10B981'],
      ],
      showscale: true,
      colorbar: {
        title: { text: 'Probability (%)', font: { color: '#94A3B8', size: 11 } },
        tickfont: { color: '#94A3B8', size: 10 },
      },
      text: matrix.z.map((row) => row.map((v) => `${v.toFixed(1)}%`)),
      texttemplate: '%{text}',
      textfont: { size: 11, color: '#F8FAFC' },
      hovertemplate:
        'From: <b>%{y}</b><br>To: <b>%{x}</b><br>Transition Prob: <b>%{z:.1f}%</b><extra></extra>',
    },
  ];

  // CSV Exporters
  const exportKmSummaryCsv = () => {
    let csv = 'Life Stage,Spells,Transitions,Median Duration (yrs),5-Yr Survival (%)\n';
    km_summary.forEach((r) => {
      csv += `"${r.stage}",${r.n_spells},${r.n_transitions},"${r.median_duration}",${r.five_yr_survival ?? ''}\n`;
    });
    downloadBlob(csv, `kaplan_meier_summary_${activePanel}.csv`);
  };

  const exportHazardCsv = () => {
    let csv = 'Variable,Hazard Ratio,p-Value,Empirical Interpretation\n';
    hazard_ratios.forEach((r) => {
      csv += `"${r.variable}",${r.hazard_ratio},${r.p_value},"${r.interpretation}"\n`;
    });
    downloadBlob(csv, `cox_hazard_ratios_${activePanel}.csv`);
  };

  const exportMatrixCsv = () => {
    let csv = 'From Stage,To Stage,Probability (%)\n';
    matrix.flat.forEach((r) => {
      csv += `"${r.from_stage}","${r.to_stage}",${r.probability}\n`;
    });
    downloadBlob(csv, `transition_probability_matrix_${activePanel}.csv`);
  };

  const downloadBlob = (content: string, filename: string) => {
    const blob = new Blob([content], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    link.href = URL.createObjectURL(blob);
    link.download = filename;
    link.click();
  };

  return (
    <div className="space-y-8">
      {/* Studio Header Card */}
      <div className="bg-[#0d1527] border border-cyan-500/20 rounded-2xl p-6 shadow-xl">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-4 border-b border-white/10">
          <div>
            <span className="text-[11px] font-bold text-cyan-400 uppercase tracking-wider font-mono">
              Studio 12 &middot; Survival Econometrics
            </span>
            <h2 className="text-2xl font-black text-white tracking-tight mt-0.5 flex items-center gap-2">
              <TrendingDown className="w-6 h-6 text-cyan-400" />
              Stage Transitions &amp; Markov Survival Analysis
            </h2>
            <p className="text-xs text-slate-400 mt-1 max-w-2xl">
              How long do firms persist in each life stage? Which financial determinants accelerate or delay stage transitions?
            </p>
          </div>
          <div className="flex items-center gap-2">
            <span className="px-3 py-1 rounded-full bg-cyan-500/10 border border-cyan-500/30 text-cyan-300 text-xs font-bold font-mono">
              {kpis.n_spells.toLocaleString()} Spells
            </span>
            <a
              href="http://localhost:8501/"
              target="_blank"
              rel="noreferrer"
              className="px-3 py-1 rounded-full bg-white/5 hover:bg-white/10 border border-white/10 text-slate-300 text-xs font-semibold flex items-center gap-1.5 transition-all"
            >
              <span>Streamlit (8501)</span>
              <ExternalLink className="w-3 h-3 text-slate-400" />
            </a>
          </div>
        </div>

        {/* Theoretical Foundations Expander */}
        <div className="mt-4">
          <button
            onClick={() => setShowTheory(!showTheory)}
            className="w-full flex items-center justify-between p-3 rounded-xl bg-white/[0.02] border border-white/5 hover:bg-white/[0.04] text-xs text-slate-300 transition-all cursor-pointer"
          >
            <div className="flex items-center gap-2 font-medium">
              <Info className="w-4 h-4 text-cyan-400" />
              <span>Theoretical Foundations: Corporate Life-Stage Stickiness</span>
            </div>
            {showTheory ? <ChevronUp className="w-4 h-4 text-slate-400" /> : <ChevronDown className="w-4 h-4 text-slate-400" />}
          </button>
          {showTheory && (
            <div className="p-4 mt-2 bg-[#090e1a] border border-white/10 rounded-xl text-xs text-slate-300 space-y-2 leading-relaxed">
              <p>
                <strong>Kaplan-Meier Survival Curves</strong> show the probability of a firm remaining in a life stage over time.
                <br />
                &bull; X-axis: years spent in the stage &nbsp;|&nbsp; &bull; Y-axis: proportion of firms still in that stage &nbsp;|&nbsp; &bull; Steeper drop = shorter typical duration
              </p>
              <p>
                <strong>Cox Proportional Hazards Model</strong> identifies which firm characteristics accelerate or delay stage transitions:
                <br />
                &bull; <strong className="text-teal-400">Hazard Ratio &gt; 1:</strong> Accelerates transitions (firms leave the stage sooner)
                <br />
                &bull; <strong className="text-rose-400">Hazard Ratio &lt; 1:</strong> Delays transitions (firms stay longer / stickier)
                <br />
                &bull; <strong>p-value &lt; 0.05:</strong> Statistically significant effect
              </p>
              <p>
                <strong>Transition Matrix</strong> shows Markov probabilities: given a firm is in Stage X, what is the probability it moves to Stage Y?
              </p>
            </div>
          )}
        </div>

        {/* Top Bento KPI Strip */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mt-6">
          <div className="bg-slate-900/80 border border-indigo-500/30 rounded-xl p-4 shadow-sm relative overflow-hidden">
            <div className="flex items-center justify-between text-slate-400 text-xs font-semibold uppercase">
              <span>Stage Spells</span>
              <Layers className="w-4 h-4 text-indigo-400" />
            </div>
            <div className="text-2xl font-black text-white font-mono mt-1">
              {kpis.n_spells.toLocaleString()}
            </div>
            <div className="text-[11px] text-indigo-300 mt-0.5">
              Across {kpis.n_firms.toLocaleString()} Firms
            </div>
          </div>

          <div className="bg-slate-900/80 border border-cyan-500/30 rounded-xl p-4 shadow-sm relative overflow-hidden">
            <div className="flex items-center justify-between text-slate-400 text-xs font-semibold uppercase">
              <span>Transitions</span>
              <Activity className="w-4 h-4 text-cyan-400" />
            </div>
            <div className="text-2xl font-black text-white font-mono mt-1">
              {kpis.n_transitions.toLocaleString()}
            </div>
            <div className="text-[11px] text-cyan-400 mt-0.5">
              {kpis.transition_rate.toFixed(1)}% event rate
            </div>
          </div>

          <div className="bg-slate-900/80 border border-emerald-500/30 rounded-xl p-4 shadow-sm relative overflow-hidden">
            <div className="flex items-center justify-between text-slate-400 text-xs font-semibold uppercase">
              <span>Sticky Benchmark</span>
              <Clock className="w-4 h-4 text-emerald-400" />
            </div>
            <div className="text-2xl font-black text-emerald-400 font-mono mt-1">
              {kpis.sticky_benchmark_stage || 'Mature'}
            </div>
            <div className="text-[11px] text-emerald-400 mt-0.5">
              Longest median spell
            </div>
          </div>

          <div className="bg-slate-900/80 border border-rose-500/30 rounded-xl p-4 shadow-sm relative overflow-hidden">
            <div className="flex items-center justify-between text-slate-400 text-xs font-semibold uppercase">
              <span>Fastest Exit</span>
              <Zap className="w-4 h-4 text-rose-400" />
            </div>
            <div className="text-2xl font-black text-rose-400 font-mono mt-1">
              {kpis.fastest_exit_stage || 'Shakeout'}
            </div>
            <div className="text-[11px] text-rose-300 mt-0.5">
              High volatility spell
            </div>
          </div>
        </div>
      </div>

      {/* ── Section 1: Kaplan-Meier Survival Curves & Summary Table ── */}
      <div className="bg-[#0d1527] border border-white/10 rounded-2xl p-6 shadow-xl space-y-4">
        <div>
          <h3 className="text-lg font-bold text-white tracking-tight flex items-center gap-2">
            <span>📈</span> Kaplan-Meier Survival Trajectories by Life Stage
          </h3>
          <p className="text-xs text-slate-400 mt-0.5">
            Probability of an enterprise remaining in the same life stage over consecutive fiscal years
          </p>
        </div>

        {/* Stage Filter Buttons */}
        <div className="flex flex-wrap items-center gap-2 pt-2 border-t border-white/5">
          <span className="text-xs text-slate-400 font-semibold mr-1">Filter Stage:</span>
          {['All Stages', ...km_curves.map((c) => c.stage)].map((stg) => {
            const isSelected = selectedCurveStage === stg;
            const color = STAGE_COLORS[stg];
            return (
              <button
                key={stg}
                onClick={() => setSelectedCurveStage(stg)}
                className={`px-3 py-1 rounded-lg text-xs font-mono font-medium transition-all cursor-pointer flex items-center gap-1.5 ${
                  isSelected
                    ? 'bg-cyan-500/20 text-cyan-300 border border-cyan-500/40 font-bold shadow-sm'
                    : 'bg-slate-900/90 text-slate-400 hover:text-slate-200 border border-white/10 hover:border-white/20'
                }`}
              >
                {color && (
                  <span
                    className="w-2 h-2 rounded-full inline-block"
                    style={{ backgroundColor: color }}
                  />
                )}
                <span>{stg}</span>
              </button>
            );
          })}
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 pt-2">
          {/* Left: Plotly KM Curve */}
          <div className="lg:col-span-2 bg-[#090e1a] border border-white/10 rounded-xl p-4">
            <PlotlyChart
              data={kmPlotTraces}
              layout={{
                title: {
                  text: 'Kaplan-Meier Survival Curves',
                  font: { color: '#F8FAFC', size: 14 },
                },
                height: 480,
                margin: { l: 60, r: 30, t: 40, b: 50 },
                paper_bgcolor: 'transparent',
                plot_bgcolor: 'transparent',
                xaxis: {
                  title: { text: 'Years in Stage', font: { color: '#94A3B8', size: 12 } },
                  gridcolor: '#1E293B',
                  tickfont: { color: '#94A3B8', size: 11 },
                  zerolinecolor: '#334155',
                },
                yaxis: {
                  title: { text: 'Survival Probability', font: { color: '#94A3B8', size: 12 } },
                  gridcolor: '#1E293B',
                  tickfont: { color: '#94A3B8', size: 11 },
                  range: [0, 1.05],
                  tickformat: '.0%',
                  zerolinecolor: '#334155',
                },
                legend: {
                  font: { color: '#E2E8F0', size: 11 },
                  orientation: 'h',
                  y: -0.2,
                },
              }}
            />
          </div>

          {/* Right: Stage Duration Summary Table */}
          <div className="bg-[#090e1a] border border-white/10 rounded-xl p-4 flex flex-col justify-between">
            <div>
              <div className="flex items-center justify-between pb-3 border-b border-white/10">
                <span className="text-xs font-bold text-white uppercase tracking-wider">
                  Stage Duration Summary
                </span>
                <button
                  onClick={exportKmSummaryCsv}
                  className="px-2 py-0.5 rounded bg-white/5 hover:bg-white/10 border border-white/10 text-slate-300 text-[11px] flex items-center gap-1 cursor-pointer"
                >
                  <Download className="w-3 h-3" />
                  <span>CSV</span>
                </button>
              </div>

              <div className="overflow-x-auto mt-3">
                <table className="w-full text-left text-xs">
                  <thead>
                    <tr className="text-slate-400 border-b border-white/10 font-mono text-[11px]">
                      <th className="pb-2">Life Stage</th>
                      <th className="pb-2 text-right">Spells</th>
                      <th className="pb-2 text-right">Transitions</th>
                      <th className="pb-2 text-right">Median</th>
                      <th className="pb-2 text-right">5-Yr Surv</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-white/5 font-mono">
                    {km_summary.map((row) => (
                      <tr key={row.stage} className="hover:bg-white/[0.02] transition-colors">
                        <td className="py-2.5 font-sans flex items-center gap-2 text-slate-200">
                          <span
                            className="w-2.5 h-2.5 rounded-full shrink-0"
                            style={{ backgroundColor: row.color }}
                          />
                          <span className="font-medium">{row.stage}</span>
                        </td>
                        <td className="py-2.5 text-right text-slate-300">
                          {row.n_spells.toLocaleString()}
                        </td>
                        <td className="py-2.5 text-right text-slate-300">
                          {row.n_transitions.toLocaleString()}
                        </td>
                        <td className="py-2.5 text-right font-bold text-cyan-400">
                          {row.median_duration} yrs
                        </td>
                        <td className="py-2.5 text-right text-slate-300">
                          {row.five_yr_survival !== null ? `${row.five_yr_survival.toFixed(1)}%` : '—'}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>

            <div className="mt-4 p-3 rounded-lg bg-white/[0.02] border border-white/5 text-[11px] text-slate-400">
              Median duration reflects the half-life time to exit each life stage. Mature firms exhibit maximum stickiness.
            </div>
          </div>
        </div>
      </div>

      {/* ── Section 2: Cox Proportional Hazards Model ── */}
      <div className="bg-[#0d1527] border border-white/10 rounded-2xl p-6 shadow-xl space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
          <div>
            <h3 className="text-lg font-bold text-white tracking-tight flex items-center gap-2">
              <span>🎯</span> Cox Proportional Hazards Model
            </h3>
            <p className="text-xs text-slate-400 mt-0.5">
              Which firm characteristics accelerate or delay stage transitions?
            </p>
          </div>
          <button
            onClick={exportHazardCsv}
            className="self-start sm:self-auto px-2.5 py-1 rounded bg-white/5 hover:bg-white/10 border border-white/10 text-slate-300 text-xs flex items-center gap-1.5 cursor-pointer"
          >
            <Download className="w-3.5 h-3.5" />
            <span>Download Hazard CSV</span>
          </button>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 pt-2">
          {/* Left: Hazard Ratios Table */}
          <div className="bg-[#090e1a] border border-white/10 rounded-xl p-4 overflow-x-auto">
            <span className="text-xs font-bold text-white uppercase tracking-wider block mb-3">
              Hazard Ratios
            </span>
            <table className="w-full text-left text-xs">
              <thead>
                <tr className="text-slate-400 border-b border-white/10 font-mono text-[11px]">
                  <th className="pb-2">Variable</th>
                  <th className="pb-2 text-right">Hazard Ratio</th>
                  <th className="pb-2 text-right">p-Value</th>
                  <th className="pb-2 pl-4">Empirical Interpretation</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-white/5">
                {hazard_ratios.map((row) => (
                  <tr key={row.variable} className="hover:bg-white/[0.02] transition-colors">
                    <td className="py-3 font-semibold text-white font-mono">{row.variable}</td>
                    <td className="py-3 text-right font-mono font-bold text-cyan-300">
                      {row.hazard_ratio.toFixed(3)}
                    </td>
                    <td className="py-3 text-right font-mono text-slate-400">
                      {row.p_value.toFixed(4)}
                    </td>
                    <td className="py-3 pl-4 text-xs text-slate-300">
                      <span
                        className={`inline-block px-2 py-0.5 rounded text-[11px] font-medium ${
                          row.hazard_ratio > 1
                            ? 'bg-teal-500/10 text-teal-300 border border-teal-500/20'
                            : row.is_significant
                            ? 'bg-rose-500/10 text-rose-300 border border-rose-500/20'
                            : 'bg-slate-800 text-slate-400'
                        }`}
                      >
                        {row.interpretation}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* Right: Hazard Ratio Forest Plot Bar Chart */}
          <div className="bg-[#090e1a] border border-white/10 rounded-xl p-4">
            <PlotlyChart
              data={coxPlotTraces}
              layout={{
                title: {
                  text: 'Hazard Ratios',
                  font: { color: '#F8FAFC', size: 14 },
                },
                height: 350,
                margin: { l: 110, r: 80, t: 40, b: 50 },
                paper_bgcolor: 'transparent',
                plot_bgcolor: 'transparent',
                xaxis: {
                  title: {
                    text: 'Hazard Ratio − 1  (>0 accelerates transition, <0 delays)',
                    font: { color: '#94A3B8', size: 11 },
                  },
                  gridcolor: '#1E293B',
                  tickfont: { color: '#94A3B8', size: 10 },
                  zeroline: true,
                  zerolinecolor: '#9CA3AF',
                  zerolinewidth: 1.5,
                },
                yaxis: {
                  gridcolor: '#1E293B',
                  tickfont: { color: '#E2E8F0', size: 11 },
                },
                shapes: [
                  {
                    type: 'line',
                    x0: 0,
                    x1: 0,
                    y0: -0.5,
                    y1: hazard_ratios.length - 0.5,
                    line: { color: '#9CA3AF', width: 1.5, dash: 'dash' },
                  },
                ],
              }}
            />
          </div>
        </div>

        {/* Dynamic Key Insights */}
        <div className="mt-4 p-4 bg-[#090e1a] border border-white/5 rounded-xl text-xs space-y-2">
          <span className="font-bold text-white uppercase tracking-wider text-[11px] block">
            Key Insights:
          </span>
          <ul className="space-y-1.5 text-slate-300">
            {hazard_ratios
              .filter((r) => r.is_significant)
              .map((r) => {
                const direction = r.hazard_ratio > 1 ? 'accelerates' : 'delays';
                const pct = Math.abs(r.hazard_ratio - 1) * 100;
                return (
                  <li key={r.variable} className="flex items-start gap-2">
                    <span className="text-cyan-400 font-bold">&bull;</span>
                    <span>
                      <strong className="text-white">{r.variable}</strong>: {direction} stage transitions by{' '}
                      <strong>{pct.toFixed(0)}%</strong> per unit increase (HR={r.hazard_ratio.toFixed(3)}, p={r.p_value.toFixed(4)})
                    </span>
                  </li>
                );
              })}
          </ul>
        </div>
      </div>

      {/* ── Section 3: Transition Probability Matrix (%) Heatmap ── */}
      <div className="bg-[#0d1527] border border-white/10 rounded-2xl p-6 shadow-xl space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 pb-2 border-b border-white/10">
          <div>
            <h3 className="text-lg font-bold text-white tracking-tight flex items-center gap-2">
              <span>🔄</span> Stage Transition Probabilities
            </h3>
            <p className="text-xs text-slate-400 mt-0.5">
              Given a firm is in Stage X (From Stage), what is the probability it moves to Stage Y (To Stage)?
            </p>
          </div>
          <button
            onClick={exportMatrixCsv}
            className="self-start sm:self-auto px-2.5 py-1 rounded bg-white/5 hover:bg-white/10 border border-white/10 text-slate-300 text-xs flex items-center gap-1.5 cursor-pointer"
          >
            <Download className="w-3.5 h-3.5" />
            <span>Download Matrix CSV</span>
          </button>
        </div>

        <div className="bg-[#090e1a] border border-white/10 rounded-xl p-4">
          <PlotlyChart
            data={heatmapTraces}
            layout={{
              title: {
                text: 'Transition Probability Matrix (%)',
                font: { color: '#F8FAFC', size: 14 },
              },
              height: 460,
              margin: { l: 100, r: 40, t: 60, b: 70 },
              paper_bgcolor: 'transparent',
              plot_bgcolor: 'transparent',
              xaxis: {
                title: { text: 'To Stage', font: { color: '#94A3B8', size: 12 } },
                tickfont: { color: '#E2E8F0', size: 11 },
                side: 'top',
              },
              yaxis: {
                title: { text: 'From Stage', font: { color: '#94A3B8', size: 12 } },
                tickfont: { color: '#E2E8F0', size: 11 },
                autorange: 'reversed',
              },
            }}
          />
        </div>
      </div>

      {/* ── Section 4: Results Interpretation & Call to Action (Shared Reusable Component) ── */}
      <ResultsInterpretationPanel
        title={interpretation.title}
        subtitle="Automated empirical deductions and corporate finance directives calculated dynamically from active panel survival data."
        insights={interpretation.insights}
        actions={interpretation.actions}
        methodologyCitation="Kaplan-Meier + Cox PH (Dickinson 2011)"
      />
    </div>
  );
};
