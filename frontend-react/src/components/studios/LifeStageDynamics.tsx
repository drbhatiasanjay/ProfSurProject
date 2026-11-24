import React, { useState, useEffect, useRef } from 'react';
import Plotly from 'plotly.js-dist-min';

const PlotlyChart: React.FC<{ data: any[]; layout: any; config?: any; style?: React.CSSProperties }> = ({
  data,
  layout,
  config,
  style,
}) => {
  const chartRef = useRef<HTMLDivElement>(null);
  useEffect(() => {
    if (!chartRef.current) return;
    Plotly.react(chartRef.current, data, layout, {
      responsive: true,
      displayModeBar: true,
      displaylogo: false,
      ...config,
    });
    const onResize = () => {
      if (chartRef.current) Plotly.Plots.resize(chartRef.current);
    };
    window.addEventListener('resize', onResize);
    return () => window.removeEventListener('resize', onResize);
  }, [data, layout, config]);

  return <div ref={chartRef} style={{ width: '100%', minHeight: layout.height || 340, ...style }} />;
};
import {
  GitFork,
  Layers,
  TrendingUp,
  Shield,
  Award,
  Zap,
  Info,
  ExternalLink,
  ChevronRight,
  Flame,
  ArrowRight,
  Download,
  Filter,
  BarChart2,
  Calendar,
  AlertTriangle,
  CheckCircle,
  HelpCircle,
  Search,
} from 'lucide-react';

interface MatrixData {
  index: string[];
  columns: string[];
  data: number[][];
}

interface StickinessItem {
  stage: string;
  stickiness_pct: number;
  color: string;
}

interface StageMetricRow {
  stage: string;
  leverage: number;
  profitability: number;
  tangibility: number;
  tax: number;
  firm_size: number;
  borrowings: number;
}

interface ShiftItem {
  from: string;
  to: string;
  normal: number;
  event: number;
  shift: number;
}

interface LeverageMatrixRow {
  stage: string;
  normal: number;
  gfc: number;
  gfc_delta: number;
  ibc: number;
  ibc_delta: number;
  covid: number;
  covid_delta: number;
}

interface TransitionRateRow {
  stage: string;
  normal: number;
  gfc: number;
  ibc: number;
  covid: number;
}

interface DeteriorationRow {
  stage: string;
  gfc: number | null;
  ibc: number | null;
  covid: number | null;
}

interface LeverageShiftBar {
  stage: string;
  event: string;
  delta: number;
}

interface SequenceItem {
  sequence: string;
  count: number;
}

interface PathItem {
  path: string;
  companies: number;
}

interface StageDurationRow {
  stage: string;
  avg_duration: number;
  median_duration: number;
  max_duration: number;
  n_spells: number;
  color: string;
}

interface CovidPayload {
  kpis: {
    total_firms: number;
    deteriorated: number;
    pct_deteriorated: number;
    improved: number;
    pct_improved: number;
    entered_decline: number;
    recovered: number;
  };
  migration_matrix: MatrixData;
  leverage_box: {
    deteriorated: number[];
    improved: number[];
  };
  profitability_box: {
    deteriorated: number[];
    improved: number[];
  };
  statistical_tests: Array<{
    metric: string;
    det_mean: number;
    imp_mean: number;
    welch_t: number;
    t_pval: number;
    mw_u: number;
    mw_pval: number;
  }>;
  entered_decline: Array<{
    company: string;
    industry: string;
    pre_stage: string;
    post_stage: string;
    leverage_change: number;
  }>;
  recovered: Array<{
    company: string;
    industry: string;
    pre_stage: string;
    post_stage: string;
    leverage_change: number;
  }>;
}

interface DynamicsData {
  stages: string[];
  tab_markov: {
    counts: MatrixData;
    probs: MatrixData;
    event_compare: string;
    event_data?: {
      counts_normal: MatrixData;
      probs_normal: MatrixData;
      counts_evt: MatrixData;
      probs_evt: MatrixData;
      delta: MatrixData;
    };
    shifts: ShiftItem[];
    stickiness: StickinessItem[];
    stage_metrics: StageMetricRow[];
  };
  tab_events: {
    leverage_matrix: LeverageMatrixRow[];
    transition_rate_matrix: TransitionRateRow[];
    deterioration_matrix: DeteriorationRow[];
    leverage_shift_bars: LeverageShiftBar[];
  };
  tab_paths: {
    sequences: SequenceItem[];
    target_stage: string;
    paths_to_target: PathItem[];
    stage_durations: StageDurationRow[];
  };
  tab_covid: CovidPayload;
}

interface LifeStageDynamicsProps {
  activePanel: string;
  yearMin: number;
  yearMax: number;
}

const STAGE_ORDER = ['Startup', 'Growth', 'Maturity', 'Shakeout1', 'Shakeout2', 'Shakeout3', 'Decline', 'Decay'];

export const LifeStageDynamics: React.FC<LifeStageDynamicsProps> = ({
  activePanel,
  yearMin: initialYearMin,
  yearMax: initialYearMax,
}) => {
  const [activeTab, setActiveTab] = useState<number>(0);
  const [data, setData] = useState<DynamicsData | null>(null);
  const [loading, setLoading] = useState<boolean>(true);

  // Tab 0 Controls
  const [eventCompare, setEventCompare] = useState<string>('None');
  const [yearMin, setYearMin] = useState<number>(initialYearMin);
  const [yearMax, setYearMax] = useState<number>(initialYearMax);
  const [showCounts, setShowCounts] = useState<boolean>(false);

  // Tab 2 Controls
  const [seqLength, setSeqLength] = useState<number>(2);
  const [minFreq, setMinFreq] = useState<number>(5);
  const [targetStage, setTargetStage] = useState<string>('Decline');

  // Tab 4 (Profiler) Controls & State
  const [profCond1Stage, setProfCond1Stage] = useState<string>('(any)');
  const [profCond1Year, setProfCond1Year] = useState<number>(2015);
  const [profCond2From, setProfCond2From] = useState<string>('(any)');
  const [profCond2To, setProfCond2To] = useState<string>('(any)');
  const [profCond2YrMin, setProfCond2YrMin] = useState<number>(2001);
  const [profCond2YrMax, setProfCond2YrMax] = useState<number>(2025);
  const [profCond3Event, setProfCond3Event] = useState<string>('(any)');
  const [profCond4Metric, setProfCond4Metric] = useState<string>('(none)');
  const [profCond4Op, setProfCond4Op] = useState<string>('>');
  const [profCond4Val, setProfCond4Val] = useState<number>(0.0);
  const [profilerResults, setProfilerResults] = useState<any | null>(null);
  const [profilerLoading, setProfilerLoading] = useState<boolean>(false);

  const fetchStageDynamics = () => {
    setLoading(true);
    const panelId = activePanel.toLowerCase().includes('bf2001') || activePanel.toLowerCase().includes('sept26')
      ? 'bf2001_25_sept26'
      : activePanel.toLowerCase().replace(/[^a-z0-9]/g, '_');

    const url = `http://localhost:8000/api/cmie/stage-dynamics?panel=${encodeURIComponent(
      panelId
    )}&event_compare=${encodeURIComponent(eventCompare)}&year_min=${yearMin}&year_max=${yearMax}&target_stage=${encodeURIComponent(
      targetStage
    )}&seq_length=${seqLength}&min_freq=${minFreq}`;

    fetch(url)
      .then((res) => {
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        return res.json();
      })
      .then((resData: DynamicsData) => {
        setData(resData);
        setLoading(false);
      })
      .catch((err) => {
        console.error('Failed to load stage dynamics:', err);
        setLoading(false);
      });
  };

  useEffect(() => {
    fetchStageDynamics();
  }, [activePanel, eventCompare, yearMin, yearMax, targetStage, seqLength, minFreq]);

  const handleRunProfiler = () => {
    setProfilerLoading(true);
    fetch('http://localhost:8000/api/cmie/stage-dynamics/profiler', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        cond1_stage: profCond1Stage,
        cond1_year: profCond1Year,
        cond2_from: profCond2From,
        cond2_to: profCond2To,
        cond2_yr_min: profCond2YrMin,
        cond2_yr_max: profCond2YrMax,
        cond3_event: profCond3Event,
        cond4_metric: profCond4Metric,
        cond4_op: profCond4Op,
        cond4_val: profCond4Val,
      }),
    })
      .then((r) => r.json())
      .then((res) => {
        setProfilerResults(res);
        setProfilerLoading(false);
      })
      .catch((err) => {
        console.error('Profiler query error:', err);
        setProfilerLoading(false);
      });
  };

  const exportCSV = (rows: any[], filename: string) => {
    if (!rows || !rows.length) return;
    const keys = Object.keys(rows[0]);
    const csvContent =
      'data:text/csv;charset=utf-8,' +
      [keys.join(','), ...rows.map((r) => keys.map((k) => `"${r[k] ?? ''}"`).join(','))].join('\n');
    const encodedUri = encodeURI(csvContent);
    const link = document.createElement('a');
    link.setAttribute('href', encodedUri);
    link.setAttribute('download', filename);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  const tabs = [
    'Transition Probabilities',
    'Event Impact Matrices',
    'Stage Pathways',
    'COVID Cohorts',
    'Company Profiler',
  ];

  if (loading && !data) {
    return (
      <div className="bg-[#0d1527] border border-white/10 rounded-2xl p-16 text-center">
        <div className="inline-block w-9 h-9 border-2 border-cyan-400 border-t-transparent rounded-full animate-spin mb-4" />
        <h3 className="text-base font-semibold text-slate-100">Computing Knowledge Graph & Markov Transitions...</h3>
        <p className="text-xs text-slate-400 mt-1">
          Evaluating 10,000+ nodes, 80,000+ transitions and corporate stage paths across capital_structure.db
        </p>
      </div>
    );
  }

  const markov = data?.tab_markov;
  const events = data?.tab_events;
  const paths = data?.tab_paths;
  const covid = data?.tab_covid;

  return (
    <div className="space-y-6">
      {/* Studio Header */}
      <div className="border-b border-white/10 pb-4">
        <div className="flex items-center justify-between">
          <div>
            <div className="flex items-center gap-2">
              <h2 className="text-xl font-bold text-slate-100 tracking-tight">Life Stage Dynamics</h2>
              <span className="text-slate-500 hover:text-slate-300 cursor-pointer">🔗</span>
            </div>
            <p className="text-xs text-slate-400 mt-0.5">
              How firms move between stages, what triggers transitions, and how events reshape patterns
            </p>
          </div>
          <div className="flex items-center gap-2">
            <span className="px-2.5 py-1 bg-cyan-500/10 border border-cyan-500/20 rounded-md text-[11px] font-mono text-cyan-300">
              Dickinson (2011) Model
            </span>
            <a
              href="http://localhost:8501"
              target="_blank"
              rel="noreferrer"
              className="px-2.5 py-1 bg-white/5 hover:bg-white/10 border border-white/10 rounded-md text-[11px] text-slate-300 flex items-center gap-1.5 transition-colors"
            >
              <span>Streamlit Baseline (8501)</span>
              <ExternalLink className="w-3 h-3 text-slate-400" />
            </a>
          </div>
        </div>

        {/* 5 Tab Navigation Bar (Pixel-for-pixel match to Streamlit tabs) */}
        <div className="flex items-center gap-1 mt-5 border-b border-slate-800 -mb-4 overflow-x-auto">
          {tabs.map((tabLabel, idx) => (
            <button
              key={idx}
              onClick={() => setActiveTab(idx)}
              className={`px-4 py-2 text-xs font-medium whitespace-nowrap transition-all border-b-2 cursor-pointer ${
                activeTab === idx
                  ? 'border-cyan-400 text-cyan-300 bg-cyan-500/5'
                  : 'border-transparent text-slate-400 hover:text-slate-200 hover:border-slate-600'
              }`}
            >
              {tabLabel}
            </button>
          ))}
        </div>
      </div>

      {/* ═════════════════════════════════════════════════════════════════════ */}
      {/* TAB 0: Transition Probabilities */}
      {/* ═════════════════════════════════════════════════════════════════════ */}
      {activeTab === 0 && markov && (
        <div className="space-y-6 pt-2">
          {/* Controls Bar */}
          <div className="bg-[#0b101b] border border-white/10 rounded-xl p-4 flex flex-wrap items-center justify-between gap-4">
            <div className="flex flex-wrap items-center gap-6">
              {/* Event Compare */}
              <div className="flex items-center gap-2">
                <span className="text-xs font-semibold text-slate-300">Compare with event:</span>
                <select
                  value={eventCompare}
                  onChange={(e) => setEventCompare(e.target.value)}
                  className="bg-slate-900 border border-slate-700 rounded-md px-3 py-1.5 text-xs text-cyan-300 font-medium focus:outline-none focus:border-cyan-400"
                >
                  <option value="None">None</option>
                  <option value="GFC">GFC (2008)</option>
                  <option value="IBC">IBC (2016)</option>
                  <option value="COVID">COVID (2020)</option>
                </select>
              </div>

              {/* Year Range */}
              <div className="flex items-center gap-3">
                <span className="text-xs font-semibold text-slate-300">Year Range:</span>
                <span className="font-mono text-xs text-cyan-400 font-bold">
                  {yearMin} – {yearMax}
                </span>
                <input
                  type="range"
                  min="2001"
                  max="2025"
                  value={yearMax}
                  onChange={(e) => setYearMax(Number(e.target.value))}
                  className="w-32 accent-cyan-400 cursor-pointer"
                />
              </div>
            </div>

            {/* Counts Toggle */}
            <div className="flex items-center gap-2">
              <label className="text-xs text-slate-300 cursor-pointer flex items-center gap-2">
                <input
                  type="checkbox"
                  checked={showCounts}
                  onChange={(e) => setShowCounts(e.target.checked)}
                  className="rounded border-slate-700 bg-slate-900 text-cyan-400 focus:ring-0 cursor-pointer"
                />
                <span className="font-medium">Show counts instead of probabilities</span>
              </label>
            </div>
          </div>

          {/* Subheader */}
          <div>
            <h3 className="text-base font-bold text-slate-100">Stage Transition Probability Matrix</h3>
            <p className="text-xs text-slate-400 mt-0.5">
              If a firm is in stage X this year, what's the probability it moves to stage Y next year? Diagonal = stayed
              in same stage.
            </p>
          </div>

          {/* Heatmaps Area */}
          {eventCompare === 'None' ? (
            <div className="bg-[#0b101b] border border-white/10 rounded-xl p-5 shadow-sm">
              <div className="flex justify-between items-center mb-3">
                <span className="text-xs font-bold text-slate-300 uppercase tracking-wider">All Years Transition Matrix</span>
                <button
                  onClick={() => exportCSV(markov.stage_metrics, 'transition_probabilities.csv')}
                  className="px-2.5 py-1 bg-white/5 hover:bg-white/10 border border-white/10 rounded text-[11px] text-slate-300 flex items-center gap-1 cursor-pointer"
                >
                  <Download className="w-3 h-3 text-slate-400" />
                  <span>Download Matrix</span>
                </button>
              </div>
              <PlotlyChart
                data={[
                  {
                    z: showCounts ? markov.counts.data : markov.probs.data,
                    x: markov.probs.columns,
                    y: markov.probs.index,
                    type: 'heatmap',
                    colorscale: 'Teal',
                    showscale: true,
                    text: (showCounts ? markov.counts.data : markov.probs.data).map((row) =>
                      row.map((v) => (showCounts ? String(v) : `${(v * 100).toFixed(1)}%`))
                    ),
                    texttemplate: '%{text}',
                    textfont: { size: 10, color: '#ffffff' },
                  },
                ]}
                layout={{
                  height: 420,
                  margin: { l: 100, r: 20, t: 30, b: 60 },
                  paper_bgcolor: 'transparent',
                  plot_bgcolor: 'transparent',
                  xaxis: { title: 'To Stage', color: '#94a3b8', gridcolor: '#1e293b' },
                  yaxis: { title: 'From Stage', color: '#94a3b8', gridcolor: '#1e293b', autorange: 'reversed' },
                }}
                config={{ responsive: true, displayModeBar: true, displaylogo: false }}
                style={{ width: '100%' }}
              />
            </div>
          ) : (
            markov.event_data && (
              <div className="space-y-6">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {/* Normal Years */}
                  <div className="bg-[#0b101b] border border-white/10 rounded-xl p-4">
                    <h4 className="text-xs font-bold text-slate-300 mb-2">Normal Years</h4>
                    <PlotlyChart
                      data={[
                        {
                          z: showCounts ? markov.event_data.counts_normal.data : markov.event_data.probs_normal.data,
                          x: markov.event_data.probs_normal.columns,
                          y: markov.event_data.probs_normal.index,
                          type: 'heatmap',
                          colorscale: 'Teal',
                          showscale: false,
                          text: (showCounts ? markov.event_data.counts_normal.data : markov.event_data.probs_normal.data).map((row) =>
                            row.map((v) => (showCounts ? String(v) : `${(v * 100).toFixed(1)}%`))
                          ),
                          texttemplate: '%{text}',
                          textfont: { size: 9, color: '#ffffff' },
                        },
                      ]}
                      layout={{
                        height: 340,
                        margin: { l: 90, r: 10, t: 20, b: 50 },
                        paper_bgcolor: 'transparent',
                        plot_bgcolor: 'transparent',
                        xaxis: { title: 'To Stage', color: '#94a3b8' },
                        yaxis: { title: 'From Stage', color: '#94a3b8', autorange: 'reversed' },
                      }}
                      config={{ responsive: true, displayModeBar: false }}
                      style={{ width: '100%' }}
                    />
                  </div>

                  {/* During Event */}
                  <div className="bg-[#0b101b] border border-white/10 rounded-xl p-4">
                    <h4 className="text-xs font-bold text-rose-300 mb-2">During {eventCompare}</h4>
                    <PlotlyChart
                      data={[
                        {
                          z: showCounts ? markov.event_data.counts_evt.data : markov.event_data.probs_evt.data,
                          x: markov.event_data.probs_evt.columns,
                          y: markov.event_data.probs_evt.index,
                          type: 'heatmap',
                          colorscale: 'OrRd',
                          showscale: false,
                          text: (showCounts ? markov.event_data.counts_evt.data : markov.event_data.probs_evt.data).map((row) =>
                            row.map((v) => (showCounts ? String(v) : `${(v * 100).toFixed(1)}%`))
                          ),
                          texttemplate: '%{text}',
                          textfont: { size: 9, color: '#ffffff' },
                        },
                      ]}
                      layout={{
                        height: 340,
                        margin: { l: 90, r: 10, t: 20, b: 50 },
                        paper_bgcolor: 'transparent',
                        plot_bgcolor: 'transparent',
                        xaxis: { title: 'To Stage', color: '#94a3b8' },
                        yaxis: { title: 'From Stage', color: '#94a3b8', autorange: 'reversed' },
                      }}
                      config={{ responsive: true, displayModeBar: false }}
                      style={{ width: '100%' }}
                    />
                  </div>
                </div>

                {/* Probability Shift Delta */}
                {!showCounts && (
                  <div className="bg-[#0b101b] border border-white/10 rounded-xl p-5">
                    <h4 className="text-xs font-bold text-slate-200">Probability Shift (Event minus Normal)</h4>
                    <p className="text-[11px] text-slate-400 mb-3">
                      Red = transition MORE likely during {eventCompare}. Blue = LESS likely.
                    </p>
                    <PlotlyChart
                      data={[
                        {
                          z: markov.event_data.delta.data,
                          x: markov.event_data.delta.columns,
                          y: markov.event_data.delta.index,
                          type: 'heatmap',
                          colorscale: 'RdBu',
                          reversescale: true,
                          zmin: -0.3,
                          zmax: 0.3,
                          text: markov.event_data.delta.data.map((row) =>
                            row.map((v) => `${v > 0 ? '+' : ''}${(v * 100).toFixed(1)}%`)
                          ),
                          texttemplate: '%{text}',
                          textfont: { size: 10, color: '#ffffff' },
                        },
                      ]}
                      layout={{
                        height: 360,
                        margin: { l: 90, r: 20, t: 20, b: 50 },
                        paper_bgcolor: 'transparent',
                        plot_bgcolor: 'transparent',
                        xaxis: { title: 'To Stage', color: '#94a3b8' },
                        yaxis: { title: 'From Stage', color: '#94a3b8', autorange: 'reversed' },
                      }}
                      config={{ responsive: true, displayModeBar: true }}
                      style={{ width: '100%' }}
                    />

                    {/* Shifts Table */}
                    {markov.shifts && markov.shifts.length > 0 && (
                      <div className="mt-5 border-t border-slate-800 pt-4">
                        <h5 className="text-xs font-bold text-slate-300 mb-2">
                          Biggest probability shifts during {eventCompare}
                        </h5>
                        <div className="overflow-x-auto">
                          <table className="w-full text-left text-xs border border-white/5">
                            <thead className="bg-slate-900 text-slate-400 border-b border-white/10 font-mono text-[11px]">
                              <tr>
                                <th className="p-2">From</th>
                                <th className="p-2">To</th>
                                <th className="p-2">Normal</th>
                                <th className="p-2">{eventCompare}</th>
                                <th className="p-2">Shift</th>
                              </tr>
                            </thead>
                            <tbody className="divide-y divide-white/5 font-mono text-[11px]">
                              {markov.shifts.map((sh, sidx) => (
                                <tr key={sidx} className="hover:bg-white/5">
                                  <td className="p-2 text-slate-200">{sh.from}</td>
                                  <td className="p-2 text-cyan-300">{sh.to}</td>
                                  <td className="p-2 text-slate-400">{sh.normal}%</td>
                                  <td className="p-2 text-amber-300">{sh.event}%</td>
                                  <td
                                    className={`p-2 font-bold ${
                                      sh.shift > 0 ? 'text-rose-400' : 'text-blue-400'
                                    }`}
                                  >
                                    {sh.shift > 0 ? `+${sh.shift}` : sh.shift}%
                                  </td>
                                </tr>
                              ))}
                            </tbody>
                          </table>
                        </div>
                      </div>
                    )}
                  </div>
                )}
              </div>
            )
          )}

          {/* Stage Stickiness (Exact match to User Image 2) */}
          <div className="bg-[#0b101b] border border-white/10 rounded-xl p-5">
            <div className="flex justify-between items-center mb-1">
              <h3 className="text-base font-bold text-slate-100">Stage Stickiness 🔗</h3>
              <button
                onClick={() => exportCSV(markov.stickiness, 'stage_stickiness.csv')}
                className="px-2.5 py-1 bg-white/5 hover:bg-white/10 border border-white/10 rounded text-[11px] text-slate-300 flex items-center gap-1 cursor-pointer"
              >
                <Download className="w-3 h-3 text-slate-400" />
                <span>CSV</span>
              </button>
            </div>
            <p className="text-xs text-slate-400 mb-4">
              % of firm-years where a company stayed in the same stage the following year. Higher = more absorbing.
            </p>
            <PlotlyChart
              data={[
                {
                  x: markov.stickiness.map((d) => d.stage),
                  y: markov.stickiness.map((d) => d.stickiness_pct),
                  type: 'bar',
                  marker: {
                    color: markov.stickiness.map((d) => d.color),
                  },
                  text: markov.stickiness.map((d) => `${Math.round(d.stickiness_pct)}%`),
                  textposition: 'outside',
                  textfont: { color: '#e2e8f0', size: 11, family: 'monospace' },
                },
              ]}
              layout={{
                height: 320,
                margin: { l: 50, r: 20, t: 25, b: 50 },
                paper_bgcolor: 'transparent',
                plot_bgcolor: 'transparent',
                xaxis: { color: '#94a3b8', gridcolor: 'transparent' },
                yaxis: { title: 'Stickiness (%)', color: '#94a3b8', gridcolor: '#1e293b', range: [0, 80] },
              }}
              config={{ responsive: true, displayModeBar: true, displaylogo: false }}
              style={{ width: '100%' }}
            />
          </div>

          {/* Stage x Financial Metric Matrix (Exact match to User Images 3 & 4) */}
          <div className="bg-[#0b101b] border border-white/10 rounded-xl p-5 space-y-4">
            <div className="flex justify-between items-center">
              <div>
                <h3 className="text-base font-bold text-slate-100">Stage × Financial Metric Matrix 🔗</h3>
                <p className="text-xs text-slate-400 mt-0.5">
                  Average financial characteristics at each life stage — reveals the DNA of each stage
                </p>
              </div>
              <button
                onClick={() => exportCSV(markov.stage_metrics, 'stage_metric_matrix.csv')}
                className="px-3 py-1.5 bg-cyan-500/10 hover:bg-cyan-500/20 border border-cyan-500/30 rounded-md text-xs font-semibold text-cyan-300 flex items-center gap-1.5 cursor-pointer"
              >
                <Download className="w-3.5 h-3.5 text-cyan-400" />
                <span>Download CSV</span>
              </button>
            </div>

            {/* Heatmap visualization */}
            <PlotlyChart
              data={[
                {
                  z: markov.stage_metrics.map((r) => [
                    r.leverage,
                    r.profitability,
                    r.tangibility,
                    r.tax,
                    r.firm_size,
                    r.borrowings,
                  ]),
                  x: ['Leverage', 'Profitability', 'Tangibility', 'Tax', 'Firm Size', 'Borrowings'],
                  y: markov.stage_metrics.map((r) => r.stage),
                  type: 'heatmap',
                  colorscale: 'Blues',
                  showscale: true,
                  text: markov.stage_metrics.map((r) => [
                    r.leverage.toFixed(2),
                    r.profitability.toFixed(3),
                    r.tangibility.toFixed(3),
                    r.tax.toFixed(2),
                    r.firm_size.toFixed(1),
                    r.borrowings.toFixed(1),
                  ]),
                  texttemplate: '%{text}',
                  textfont: { size: 10, color: '#ffffff' },
                },
              ]}
              layout={{
                height: 380,
                margin: { l: 100, r: 20, t: 20, b: 60 },
                paper_bgcolor: 'transparent',
                plot_bgcolor: 'transparent',
                xaxis: { color: '#94a3b8' },
                yaxis: { color: '#94a3b8', autorange: 'reversed' },
              }}
              config={{ responsive: true, displayModeBar: true, displaylogo: false }}
              style={{ width: '100%' }}
            />

            {/* Data Table (Screenshot 4 exact layout) */}
            <div className="overflow-x-auto border border-white/10 rounded-lg">
              <table className="w-full text-left text-xs">
                <thead className="bg-slate-900 text-slate-400 border-b border-white/10 font-mono text-[11px]">
                  <tr>
                    <th className="p-3">Stage</th>
                    <th className="p-3 text-right">Leverage</th>
                    <th className="p-3 text-right">Profitability</th>
                    <th className="p-3 text-right">Tangibility</th>
                    <th className="p-3 text-right">Tax</th>
                    <th className="p-3 text-right">Firm Size</th>
                    <th className="p-3 text-right">Borrowings</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-white/5 font-mono text-[11px]">
                  {markov.stage_metrics.map((row, r_idx) => (
                    <tr key={r_idx} className="hover:bg-white/5">
                      <td className="p-3 font-sans font-semibold text-slate-200">{row.stage}</td>
                      <td className="p-3 text-right text-cyan-300 font-bold">{row.leverage.toFixed(3)}</td>
                      <td className="p-3 text-right text-slate-300">{row.profitability.toFixed(3)}</td>
                      <td className="p-3 text-right text-slate-300">{row.tangibility.toFixed(3)}</td>
                      <td className="p-3 text-right text-slate-300">{row.tax.toFixed(3)}</td>
                      <td className="p-3 text-right text-slate-300">{row.firm_size.toLocaleString()}</td>
                      <td className="p-3 text-right text-slate-400 font-mono">{row.borrowings.toLocaleString()}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}

      {/* ═════════════════════════════════════════════════════════════════════ */}
      {/* TAB 1: Event Impact Matrices */}
      {/* ═════════════════════════════════════════════════════════════════════ */}
      {activeTab === 1 && events && (
        <div className="space-y-6 pt-2">
          <div>
            <h3 className="text-base font-bold text-slate-100">Event Impact Matrices</h3>
            <p className="text-xs text-slate-400 mt-0.5">
              Three empirical matrices showing how GFC, IBC, and COVID affected each life stage differently
            </p>
          </div>

          {/* Matrix 1: Leverage Impact */}
          <div className="bg-[#0b101b] border border-white/10 rounded-xl p-5 space-y-3">
            <h4 className="text-sm font-bold text-slate-200">1. Leverage Impact Matrix</h4>
            <p className="text-xs text-slate-400">
              Average leverage by stage during each event, and the delta vs normal years. Red = leverage increased
              during event.
            </p>
            <PlotlyChart
              data={[
                {
                  z: events.leverage_matrix.map((r) => [r.gfc_delta, r.ibc_delta, r.covid_delta]),
                  x: ['GFC Δ', 'IBC Δ', 'COVID Δ'],
                  y: events.leverage_matrix.map((r) => r.stage),
                  type: 'heatmap',
                  colorscale: 'RdBu',
                  reversescale: true,
                  zmin: -5,
                  zmax: 5,
                  text: events.leverage_matrix.map((r) => [
                    `${r.gfc_delta > 0 ? '+' : ''}${r.gfc_delta.toFixed(2)}`,
                    `${r.ibc_delta > 0 ? '+' : ''}${r.ibc_delta.toFixed(2)}`,
                    `${r.covid_delta > 0 ? '+' : ''}${r.covid_delta.toFixed(2)}`,
                  ]),
                  texttemplate: '%{text}',
                  textfont: { size: 11, color: '#ffffff' },
                },
              ]}
              layout={{
                height: 340,
                margin: { l: 90, r: 20, t: 20, b: 40 },
                paper_bgcolor: 'transparent',
                plot_bgcolor: 'transparent',
                xaxis: { color: '#94a3b8' },
                yaxis: { color: '#94a3b8', autorange: 'reversed' },
              }}
              config={{ responsive: true, displayModeBar: true }}
              style={{ width: '100%' }}
            />
          </div>

          {/* Matrix 2: Transition Rate */}
          <div className="bg-[#0b101b] border border-white/10 rounded-xl p-5 space-y-3">
            <h4 className="text-sm font-bold text-slate-200">2. Transition Rate Matrix</h4>
            <p className="text-xs text-slate-400">
              % of firm-years at each stage where the firm changed stage. Higher = more disrupted by the event.
            </p>
            <PlotlyChart
              data={[
                {
                  z: events.transition_rate_matrix.map((r) => [r.normal, r.gfc, r.ibc, r.covid]),
                  x: ['Normal', 'GFC', 'IBC', 'COVID'],
                  y: events.transition_rate_matrix.map((r) => r.stage),
                  type: 'heatmap',
                  colorscale: 'OrRd',
                  text: events.transition_rate_matrix.map((r) => [
                    `${r.normal.toFixed(1)}%`,
                    `${r.gfc.toFixed(1)}%`,
                    `${r.ibc.toFixed(1)}%`,
                    `${r.covid.toFixed(1)}%`,
                  ]),
                  texttemplate: '%{text}',
                  textfont: { size: 11, color: '#ffffff' },
                },
              ]}
              layout={{
                height: 340,
                margin: { l: 90, r: 20, t: 20, b: 40 },
                paper_bgcolor: 'transparent',
                plot_bgcolor: 'transparent',
                xaxis: { color: '#94a3b8' },
                yaxis: { color: '#94a3b8', autorange: 'reversed' },
              }}
              config={{ responsive: true, displayModeBar: true }}
              style={{ width: '100%' }}
            />
          </div>

          {/* Event Comparison: Avg Leverage Shift by Stage (Grouped Bar Chart) */}
          <div className="bg-[#0b101b] border border-white/10 rounded-xl p-5 space-y-3">
            <h4 className="text-sm font-bold text-slate-200">Event Comparison: Avg Leverage Shift by Stage</h4>
            <PlotlyChart
              data={[
                {
                  x: events.leverage_shift_bars.filter((b) => b.event === 'GFC').map((b) => b.stage),
                  y: events.leverage_shift_bars.filter((b) => b.event === 'GFC').map((b) => b.delta),
                  name: 'GFC',
                  type: 'bar',
                  marker: { color: '#EF4444' },
                },
                {
                  x: events.leverage_shift_bars.filter((b) => b.event === 'IBC').map((b) => b.stage),
                  y: events.leverage_shift_bars.filter((b) => b.event === 'IBC').map((b) => b.delta),
                  name: 'IBC',
                  type: 'bar',
                  marker: { color: '#3B82F6' },
                },
                {
                  x: events.leverage_shift_bars.filter((b) => b.event === 'COVID').map((b) => b.stage),
                  y: events.leverage_shift_bars.filter((b) => b.event === 'COVID').map((b) => b.delta),
                  name: 'COVID',
                  type: 'bar',
                  marker: { color: '#10B981' },
                },
              ]}
              layout={{
                barmode: 'group',
                height: 380,
                margin: { l: 50, r: 20, t: 30, b: 50 },
                paper_bgcolor: 'transparent',
                plot_bgcolor: 'transparent',
                xaxis: { color: '#94a3b8' },
                yaxis: { title: 'Leverage Δ (pp)', color: '#94a3b8', gridcolor: '#1e293b' },
                legend: { font: { color: '#e2e8f0' } },
              }}
              config={{ responsive: true, displayModeBar: true }}
              style={{ width: '100%' }}
            />
          </div>
        </div>
      )}

      {/* ═════════════════════════════════════════════════════════════════════ */}
      {/* TAB 2: Stage Pathway Discovery */}
      {/* ═════════════════════════════════════════════════════════════════════ */}
      {activeTab === 2 && paths && (
        <div className="space-y-6 pt-2">
          {/* Controls */}
          <div className="bg-[#0b101b] border border-white/10 rounded-xl p-4 grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <div className="flex justify-between text-xs text-slate-300 font-semibold mb-1">
                <span>Sequence length</span>
                <span className="text-cyan-400 font-mono">{seqLength}</span>
              </div>
              <input
                type="range"
                min="2"
                max="4"
                value={seqLength}
                onChange={(e) => setSeqLength(Number(e.target.value))}
                className="w-full accent-cyan-400 cursor-pointer"
              />
            </div>
            <div>
              <div className="flex justify-between text-xs text-slate-300 font-semibold mb-1">
                <span>Minimum frequency</span>
                <span className="text-cyan-400 font-mono">{minFreq}</span>
              </div>
              <input
                type="range"
                min="1"
                max="50"
                value={minFreq}
                onChange={(e) => setMinFreq(Number(e.target.value))}
                className="w-full accent-cyan-400 cursor-pointer"
              />
            </div>
            <div>
              <span className="block text-xs text-slate-300 font-semibold mb-1">Paths leading TO:</span>
              <select
                value={targetStage}
                onChange={(e) => setTargetStage(e.target.value)}
                className="w-full bg-slate-900 border border-slate-700 rounded-md px-3 py-1.5 text-xs text-cyan-300 font-medium focus:outline-none focus:border-cyan-400"
              >
                {STAGE_ORDER.map((stg) => (
                  <option key={stg} value={stg}>
                    {stg}
                  </option>
                ))}
              </select>
            </div>
          </div>

          {/* Most Common Sequences (Horizontal Bar Chart) */}
          <div className="bg-[#0b101b] border border-white/10 rounded-xl p-5">
            <h4 className="text-sm font-bold text-slate-200 mb-1">
              Most Common {seqLength}-Step Sequences
            </h4>
            <PlotlyChart
              data={[
                {
                  y: paths.sequences.map((s) => s.sequence).reverse(),
                  x: paths.sequences.map((s) => s.count).reverse(),
                  type: 'bar',
                  orientation: 'h',
                  marker: { color: '#0284C7' },
                  text: paths.sequences.map((s) => String(s.count)).reverse(),
                  textposition: 'outside',
                  textfont: { color: '#93c5fd', size: 11 },
                },
              ]}
              layout={{
                height: Math.max(320, paths.sequences.length * 28),
                margin: { l: 200, r: 40, t: 20, b: 40 },
                paper_bgcolor: 'transparent',
                plot_bgcolor: 'transparent',
                xaxis: { title: 'Frequency', color: '#94a3b8', gridcolor: '#1e293b' },
                yaxis: { color: '#e2e8f0' },
              }}
              config={{ responsive: true, displayModeBar: true }}
              style={{ width: '100%' }}
            />
          </div>

          {/* Paths to target stage */}
          <div className="bg-[#0b101b] border border-white/10 rounded-xl p-5 space-y-3">
            <h4 className="text-sm font-bold text-slate-200">
              How Do Firms Reach <span className="text-cyan-400 font-mono">{targetStage}</span>?
            </h4>
            <p className="text-xs text-slate-400">
              Most common stage sequences ending in {targetStage}, looking back up to 3 steps
            </p>
            <div className="overflow-x-auto border border-white/10 rounded-lg">
              <table className="w-full text-left text-xs">
                <thead className="bg-slate-900 text-slate-400 border-b border-white/10 font-mono text-[11px]">
                  <tr>
                    <th className="p-2.5">Path</th>
                    <th className="p-2.5 text-right">Companies</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-white/5 font-mono text-[11px]">
                  {paths.paths_to_target.map((p, idx) => (
                    <tr key={idx} className="hover:bg-white/5">
                      <td className="p-2.5 text-slate-200">{p.path}</td>
                      <td className="p-2.5 text-right text-cyan-300 font-bold">{p.companies}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          {/* Stage Duration Matrix */}
          <div className="bg-[#0b101b] border border-white/10 rounded-xl p-5 space-y-3">
            <h4 className="text-sm font-bold text-slate-200">Stage Duration Matrix</h4>
            <p className="text-xs text-slate-400">
              Average consecutive years a firm stays in each stage before transitioning out
            </p>
            <PlotlyChart
              data={[
                {
                  x: paths.stage_durations.map((d) => d.stage),
                  y: paths.stage_durations.map((d) => d.avg_duration),
                  type: 'bar',
                  marker: { color: paths.stage_durations.map((d) => d.color) },
                  text: paths.stage_durations.map((d) => `${d.avg_duration.toFixed(1)} yrs`),
                  textposition: 'outside',
                  textfont: { color: '#e2e8f0', size: 11 },
                },
              ]}
              layout={{
                height: 320,
                margin: { l: 50, r: 20, t: 30, b: 40 },
                paper_bgcolor: 'transparent',
                plot_bgcolor: 'transparent',
                xaxis: { color: '#94a3b8' },
                yaxis: { title: 'Avg Years', color: '#94a3b8', gridcolor: '#1e293b' },
              }}
              config={{ responsive: true, displayModeBar: true }}
              style={{ width: '100%' }}
            />
          </div>
        </div>
      )}

      {/* ═════════════════════════════════════════════════════════════════════ */}
      {/* TAB 3: COVID Cohorts */}
      {/* ═════════════════════════════════════════════════════════════════════ */}
      {activeTab === 3 && covid && (
        <div className="space-y-6 pt-2">
          <div>
            <h3 className="text-base font-bold text-slate-100">Post-COVID Cohort Analysis</h3>
            <p className="text-xs text-slate-400 mt-0.5">
              Which firms entered Decline after COVID? Which recovered? Comparing pre-COVID (2019) vs post-COVID (2022+) stages.
            </p>
          </div>

          {/* 5 KPI Metric Cards */}
          <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
            <div className="bg-[#0b101b] border border-white/10 rounded-xl p-4">
              <span className="text-[11px] font-bold text-slate-400 uppercase tracking-wider">Total Firms</span>
              <div className="text-2xl font-bold font-mono text-slate-100 mt-1">{covid.kpis.total_firms}</div>
            </div>
            <div className="bg-[#0b101b] border border-rose-500/20 rounded-xl p-4">
              <span className="text-[11px] font-bold text-rose-400 uppercase tracking-wider">Deteriorated</span>
              <div className="text-2xl font-bold font-mono text-rose-300 mt-1">
                {covid.kpis.deteriorated} <span className="text-xs font-normal text-rose-400">({covid.kpis.pct_deteriorated}%)</span>
              </div>
            </div>
            <div className="bg-[#0b101b] border border-emerald-500/20 rounded-xl p-4">
              <span className="text-[11px] font-bold text-emerald-400 uppercase tracking-wider">Improved</span>
              <div className="text-2xl font-bold font-mono text-emerald-300 mt-1">
                {covid.kpis.improved} <span className="text-xs font-normal text-emerald-400">({covid.kpis.pct_improved}%)</span>
              </div>
            </div>
            <div className="bg-[#0b101b] border border-amber-500/20 rounded-xl p-4">
              <span className="text-[11px] font-bold text-amber-400 uppercase tracking-wider">Entered Decline</span>
              <div className="text-2xl font-bold font-mono text-amber-300 mt-1">{covid.kpis.entered_decline}</div>
            </div>
            <div className="bg-[#0b101b] border border-cyan-500/20 rounded-xl p-4">
              <span className="text-[11px] font-bold text-cyan-400 uppercase tracking-wider">Recovered</span>
              <div className="text-2xl font-bold font-mono text-cyan-300 mt-1">{covid.kpis.recovered}</div>
            </div>
          </div>

          {/* Pre-COVID -> Post-COVID Migration Matrix */}
          <div className="bg-[#0b101b] border border-white/10 rounded-xl p-5 space-y-3">
            <h4 className="text-sm font-bold text-slate-200">Pre-COVID → Post-COVID Stage Migration</h4>
            <PlotlyChart
              data={[
                {
                  z: covid.migration_matrix.data,
                  x: covid.migration_matrix.columns,
                  y: covid.migration_matrix.index,
                  type: 'heatmap',
                  colorscale: 'Teal',
                  text: covid.migration_matrix.data.map((row) => row.map((v) => String(v))),
                  texttemplate: '%{text}',
                  textfont: { size: 11, color: '#ffffff' },
                },
              ]}
              layout={{
                height: 380,
                margin: { l: 100, r: 20, t: 20, b: 50 },
                paper_bgcolor: 'transparent',
                plot_bgcolor: 'transparent',
                xaxis: { title: 'Post-COVID Stage', color: '#94a3b8' },
                yaxis: { title: 'Pre-COVID Stage', color: '#94a3b8', autorange: 'reversed' },
              }}
              config={{ responsive: true, displayModeBar: true }}
              style={{ width: '100%' }}
            />
          </div>

          {/* Statistical Tests Table */}
          {covid.statistical_tests && covid.statistical_tests.length > 0 && (
            <div className="bg-[#0b101b] border border-white/10 rounded-xl p-5 space-y-3">
              <h4 className="text-sm font-bold text-slate-200">Statistical Tests: Deteriorated vs Improved Cohorts</h4>
              <p className="text-xs text-slate-400">
                Welch's t-test (assumes unequal variances) + Mann-Whitney U (non-parametric)
              </p>
              <div className="overflow-x-auto border border-white/10 rounded-lg">
                <table className="w-full text-left text-xs font-mono">
                  <thead className="bg-slate-900 text-slate-400 border-b border-white/10 text-[11px]">
                    <tr>
                      <th className="p-2.5">Metric</th>
                      <th className="p-2.5 text-right">Det Mean</th>
                      <th className="p-2.5 text-right">Imp Mean</th>
                      <th className="p-2.5 text-right">Welch t</th>
                      <th className="p-2.5 text-right">t p-value</th>
                      <th className="p-2.5 text-right">MW U</th>
                      <th className="p-2.5 text-right">MW p-value</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-white/5 text-[11px]">
                    {covid.statistical_tests.map((st, idx) => (
                      <tr key={idx} className="hover:bg-white/5">
                        <td className="p-2.5 font-sans font-semibold text-slate-200">{st.metric}</td>
                        <td className="p-2.5 text-right text-rose-300">{st.det_mean}</td>
                        <td className="p-2.5 text-right text-emerald-300">{st.imp_mean}</td>
                        <td className="p-2.5 text-right text-slate-300">{st.welch_t}</td>
                        <td className="p-2.5 text-right text-amber-300 font-bold">{st.t_pval}</td>
                        <td className="p-2.5 text-right text-slate-300">{st.mw_u}</td>
                        <td className="p-2.5 text-right text-amber-300 font-bold">{st.mw_pval}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* Firms That Entered Decline */}
          {covid.entered_decline && covid.entered_decline.length > 0 && (
            <div className="bg-[#0b101b] border border-white/10 rounded-xl p-5 space-y-3">
              <div className="flex justify-between items-center">
                <h4 className="text-sm font-bold text-rose-300">Firms That Entered Decline/Decay After COVID</h4>
                <button
                  onClick={() => exportCSV(covid.entered_decline, 'covid_decline_firms.csv')}
                  className="px-2.5 py-1 bg-white/5 hover:bg-white/10 border border-white/10 rounded text-[11px] text-slate-300 flex items-center gap-1 cursor-pointer"
                >
                  <Download className="w-3 h-3 text-slate-400" />
                  <span>CSV</span>
                </button>
              </div>
              <div className="overflow-x-auto border border-white/10 rounded-lg max-h-72">
                <table className="w-full text-left text-xs">
                  <thead className="bg-slate-900 text-slate-400 border-b border-white/10 font-mono text-[11px] sticky top-0">
                    <tr>
                      <th className="p-2.5">Company</th>
                      <th className="p-2.5">Industry</th>
                      <th className="p-2.5">Pre-COVID Stage</th>
                      <th className="p-2.5">Post-COVID Stage</th>
                      <th className="p-2.5 text-right">Leverage Δ (pp)</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-white/5 text-[11px]">
                    {covid.entered_decline.map((row, idx) => (
                      <tr key={idx} className="hover:bg-white/5">
                        <td className="p-2.5 font-semibold text-slate-200">{row.company}</td>
                        <td className="p-2.5 text-slate-400">{row.industry}</td>
                        <td className="p-2.5 text-cyan-300 font-mono">{row.pre_stage}</td>
                        <td className="p-2.5 text-rose-400 font-mono font-bold">{row.post_stage}</td>
                        <td className="p-2.5 text-right font-mono text-amber-300">{row.leverage_change.toFixed(2)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </div>
      )}

      {/* ═════════════════════════════════════════════════════════════════════ */}
      {/* TAB 4: Multi-Hop Company Profiler */}
      {/* ═════════════════════════════════════════════════════════════════════ */}
      {activeTab === 4 && (
        <div className="space-y-6 pt-2">
          <div>
            <h3 className="text-base font-bold text-slate-100">Multi-Hop Company Profiler</h3>
            <p className="text-xs text-slate-400 mt-0.5">
              Chain conditions to find companies matching complex criteria across stages, events, and metrics
            </p>
          </div>

          {/* Condition Builder Card */}
          <div className="bg-[#0b101b] border border-white/10 rounded-xl p-5 space-y-4">
            {/* Condition 1 */}
            <div>
              <span className="block text-xs font-bold text-slate-200 mb-2">
                Condition 1: Life stage at a specific year
              </span>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-[11px] text-slate-400 mb-1">Stage</label>
                  <select
                    value={profCond1Stage}
                    onChange={(e) => setProfCond1Stage(e.target.value)}
                    className="w-full bg-slate-900 border border-slate-700 rounded-md px-3 py-1.5 text-xs text-slate-200"
                  >
                    <option value="(any)">(any)</option>
                    {STAGE_ORDER.map((s) => (
                      <option key={s} value={s}>
                        {s}
                      </option>
                    ))}
                  </select>
                </div>
                <div>
                  <div className="flex justify-between text-[11px] text-slate-400 mb-1">
                    <span>Year</span>
                    <span className="text-cyan-400 font-mono font-bold">{profCond1Year}</span>
                  </div>
                  <input
                    type="range"
                    min="2001"
                    max="2025"
                    value={profCond1Year}
                    onChange={(e) => setProfCond1Year(Number(e.target.value))}
                    className="w-full accent-cyan-400 cursor-pointer"
                  />
                </div>
              </div>
            </div>

            {/* Condition 2 */}
            <div className="border-t border-slate-800 pt-4">
              <span className="block text-xs font-bold text-slate-200 mb-2">Condition 2: Stage transition</span>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div>
                  <label className="block text-[11px] text-slate-400 mb-1">From stage</label>
                  <select
                    value={profCond2From}
                    onChange={(e) => setProfCond2From(e.target.value)}
                    className="w-full bg-slate-900 border border-slate-700 rounded-md px-3 py-1.5 text-xs text-slate-200"
                  >
                    <option value="(any)">(any)</option>
                    {STAGE_ORDER.map((s) => (
                      <option key={s} value={s}>
                        {s}
                      </option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="block text-[11px] text-slate-400 mb-1">To stage</label>
                  <select
                    value={profCond2To}
                    onChange={(e) => setProfCond2To(e.target.value)}
                    className="w-full bg-slate-900 border border-slate-700 rounded-md px-3 py-1.5 text-xs text-slate-200"
                  >
                    <option value="(any)">(any)</option>
                    {STAGE_ORDER.map((s) => (
                      <option key={s} value={s}>
                        {s}
                      </option>
                    ))}
                  </select>
                </div>
                <div>
                  <div className="flex justify-between text-[11px] text-slate-400 mb-1">
                    <span>Transition Year Window</span>
                    <span className="text-cyan-400 font-mono">
                      {profCond2YrMin} – {profCond2YrMax}
                    </span>
                  </div>
                  <input
                    type="range"
                    min="2001"
                    max="2025"
                    value={profCond2YrMax}
                    onChange={(e) => setProfCond2YrMax(Number(e.target.value))}
                    className="w-full accent-cyan-400 cursor-pointer"
                  />
                </div>
              </div>
            </div>

            {/* Condition 3 & 4 */}
            <div className="border-t border-slate-800 pt-4 grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-xs font-bold text-slate-200 mb-2">Condition 3: During event</label>
                <select
                  value={profCond3Event}
                  onChange={(e) => setProfCond3Event(e.target.value)}
                  className="w-full bg-slate-900 border border-slate-700 rounded-md px-3 py-1.5 text-xs text-slate-200"
                >
                  <option value="(any)">(any)</option>
                  <option value="GFC">GFC (2008)</option>
                  <option value="IBC">IBC (2016)</option>
                  <option value="COVID">COVID (2020)</option>
                </select>
              </div>

              <div>
                <label className="block text-xs font-bold text-slate-200 mb-2">Condition 4: Financial metric</label>
                <div className="grid grid-cols-3 gap-2">
                  <select
                    value={profCond4Metric}
                    onChange={(e) => setProfCond4Metric(e.target.value)}
                    className="bg-slate-900 border border-slate-700 rounded px-2 py-1.5 text-xs text-slate-200"
                  >
                    <option value="(none)">(none)</option>
                    <option value="leverage">leverage</option>
                    <option value="profitability">profitability</option>
                    <option value="tangibility">tangibility</option>
                    <option value="firm_size">firm_size</option>
                  </select>
                  <select
                    value={profCond4Op}
                    onChange={(e) => setProfCond4Op(e.target.value)}
                    className="bg-slate-900 border border-slate-700 rounded px-2 py-1.5 text-xs text-slate-200 font-mono"
                  >
                    <option value=">">&gt;</option>
                    <option value="<">&lt;</option>
                    <option value=">=">&gt;=</option>
                    <option value="<=">&lt;=</option>
                  </select>
                  <input
                    type="number"
                    step="0.1"
                    value={profCond4Val}
                    onChange={(e) => setProfCond4Val(Number(e.target.value))}
                    className="bg-slate-900 border border-slate-700 rounded px-2 py-1.5 text-xs text-slate-200 font-mono"
                  />
                </div>
              </div>
            </div>

            {/* Run Button */}
            <div className="border-t border-slate-800 pt-3">
              <button
                onClick={handleRunProfiler}
                disabled={profilerLoading}
                className="px-5 py-2 bg-cyan-600 hover:bg-cyan-500 text-white rounded-lg text-xs font-bold transition-all shadow-md flex items-center gap-2 cursor-pointer disabled:opacity-50"
              >
                <Search className="w-3.5 h-3.5" />
                <span>{profilerLoading ? 'Running Graph Query...' : 'Run Query'}</span>
              </button>
            </div>
          </div>

          {/* Profiler Output: Funnel & Matching Companies */}
          {profilerResults && (
            <div className="space-y-5">
              {/* Funnel Metrics */}
              <div className="bg-[#0b101b] border border-white/10 rounded-xl p-4">
                <h4 className="text-xs font-bold text-slate-300 uppercase tracking-wider mb-3">Filter Funnel</h4>
                <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
                  {profilerResults.funnel.map((fn: any, idx: number) => (
                    <div key={idx} className="bg-slate-900/60 border border-white/5 rounded-lg p-3">
                      <span className="text-[10px] text-slate-400 uppercase font-semibold">{fn.label}</span>
                      <div className="text-lg font-bold font-mono text-cyan-300 mt-0.5">{fn.count}</div>
                    </div>
                  ))}
                </div>
              </div>

              {/* Matching Table */}
              <div className="bg-[#0b101b] border border-white/10 rounded-xl p-5 space-y-3">
                <div className="flex justify-between items-center">
                  <h4 className="text-sm font-bold text-slate-200">
                    Matching Enterprises ({profilerResults.total_matches})
                  </h4>
                  <button
                    onClick={() => exportCSV(profilerResults.results, 'profiler_results.csv')}
                    className="px-2.5 py-1 bg-white/5 hover:bg-white/10 border border-white/10 rounded text-[11px] text-slate-300 flex items-center gap-1 cursor-pointer"
                  >
                    <Download className="w-3 h-3 text-slate-400" />
                    <span>CSV</span>
                  </button>
                </div>
                <div className="overflow-x-auto border border-white/10 rounded-lg max-h-80">
                  <table className="w-full text-left text-xs">
                    <thead className="bg-slate-900 text-slate-400 border-b border-white/10 font-mono text-[11px] sticky top-0">
                      <tr>
                        <th className="p-2.5">Company</th>
                        <th className="p-2.5">Industry</th>
                        <th className="p-2.5">Latest Stage</th>
                        <th className="p-2.5 text-right">Leverage (%)</th>
                        <th className="p-2.5 text-right">Profitability</th>
                        <th className="p-2.5 text-right">Transitions</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-white/5 text-[11px]">
                      {profilerResults.results.map((c: any, cidx: number) => (
                        <tr key={cidx} className="hover:bg-white/5">
                          <td className="p-2.5 font-semibold text-slate-200">{c.company}</td>
                          <td className="p-2.5 text-slate-400">{c.industry}</td>
                          <td className="p-2.5">
                            <span className="px-2 py-0.5 rounded text-[10px] font-mono bg-cyan-500/10 text-cyan-300 border border-cyan-500/20">
                              {c.latest_stage}
                            </span>
                          </td>
                          <td className="p-2.5 text-right font-mono text-slate-200">
                            {c.leverage !== null ? `${c.leverage.toFixed(2)}%` : '—'}
                          </td>
                          <td className="p-2.5 text-right font-mono text-slate-300">
                            {c.profitability !== null ? c.profitability.toFixed(3) : '—'}
                          </td>
                          <td className="p-2.5 text-right font-mono text-cyan-300 font-bold">{c.transitions}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};
