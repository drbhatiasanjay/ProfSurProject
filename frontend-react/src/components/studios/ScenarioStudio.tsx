import React, { useState, useEffect, useMemo } from 'react';
import { ChartContainer } from '../shared/ChartContainer';
import { PlotlyChart } from '../shared/PlotlyChart';
import { CollapsibleInsightBox } from '../shared/CollapsibleInsightBox';
import {
  SlidersHorizontal,
  TrendingUp,
  TrendingDown,
  Layers,
  Award,
  BookOpen,
  Sparkles,
  Target,
  CheckCircle2,
  AlertCircle,
  FileText,
  Copy,
  Check,
  Download,
  Building,
  Scale,
  Compass,
  BarChart2,
  Activity,
  RotateCcw,
} from 'lucide-react';

interface ScenarioStudioProps {
  activePanel?: string;
  yearMin?: number;
  yearMax?: number;
}

interface BaselineData {
  panel: string;
  n_obs: number;
  r_squared: number;
  sample_mean: number;
  coefficients: {
    intercept: number;
    profitability: number;
    tangibility: number;
    tax: number;
    log_size: number;
    tax_shield: number;
    dividend: number;
  };
  defaults: {
    prof: number;
    tang: number;
    tax: number;
    log_size: number;
    tax_shield: number;
    dvnd: number;
  };
  slider_ranges: Record<string, { min: number; max: number; step: number; label: string }>;
  citations: string[];
  companies: Array<{ company_code: number; company_name: string }>;
}

interface SimulationData {
  predicted_leverage: number;
  sample_mean: number;
  delta_vs_mean: number;
  percentile: number;
  r_squared: number;
  n_obs: number;
  contributions: Record<string, number>;
  top_factor: string;
  top_factor_val: number;
  waterfall: {
    x: string[];
    y: number[];
    measure: string[];
  };
  forest_plot: {
    labels: string[];
    beta: number[];
    se: number[];
    ci_lower: number[];
    ci_upper: number[];
  };
  factor_bars: {
    factors: string[];
    values: number[];
  };
  sensitivity_radar: {
    categories: string[];
    baseline: number[];
    scenario: number[];
  };
  insights: {
    findings: string[];
    actions: string[];
  };
  company_comparison: {
    company_code: number;
    company_name: string;
    actual_avg: number;
    predicted: number;
    difference: number;
    verdict: string;
  } | null;
}

export const ScenarioStudio: React.FC<ScenarioStudioProps> = ({
  activePanel = 'bf2001_25_sept26',
  yearMin = 2001,
  yearMax = 2025,
}) => {
  const [baseline, setBaseline] = useState<BaselineData | null>(null);
  const [loadingBaseline, setLoadingBaseline] = useState<boolean>(true);
  const [errorBaseline, setErrorBaseline] = useState<string | null>(null);

  // Sliders state
  const [prof, setProf] = useState<number>(10.0);
  const [tang, setTang] = useState<number>(30.0);
  const [tax, setTax] = useState<number>(20.0);
  const [logSize, setLogSize] = useState<number>(7.0);
  const [taxShield, setTaxShield] = useState<number>(5.0);
  const [dvnd, setDvnd] = useState<number>(2.0);

  // Selected company for comparison
  const [selectedCompanyCode, setSelectedCompanyCode] = useState<number | null>(36277); // 3M India default

  // Active chart view
  const [chartView, setChartView] = useState<'waterfall' | 'forest' | 'bars' | 'radar'>('waterfall');

  // Simulation output
  const [simulation, setSimulation] = useState<SimulationData | null>(null);
  const [simulating, setSimulating] = useState<boolean>(false);

  // Citation copy state
  const [copiedApa, setCopiedApa] = useState(false);
  const [copiedLatex, setCopiedLatex] = useState(false);
  const [showCitationExpander, setShowCitationExpander] = useState(false);

  // Fetch baseline coefficients on mount or panel change
  useEffect(() => {
    let mounted = true;
    const fetchBaseline = async () => {
      setLoadingBaseline(true);
      setErrorBaseline(null);
      try {
        const res = await fetch(`http://localhost:8000/api/cmie/scenarios/baseline?panel=${encodeURIComponent(activePanel)}`);
        if (!res.ok) throw new Error(`HTTP ${res.status}: Failed to load scenario baseline`);
        const data: BaselineData = await res.json();
        if (mounted) {
          setBaseline(data);
          // Set initial slider values from defaults
          if (data.defaults) {
            setProf(data.defaults.prof);
            setTang(data.defaults.tang);
            setTax(data.defaults.tax);
            setLogSize(data.defaults.log_size);
            setTaxShield(data.defaults.tax_shield);
            setDvnd(data.defaults.dvnd);
          }
          if (data.companies && data.companies.length > 0) {
            // Default to 3M India (36277) if exists, else first company
            const has3M = data.companies.find((c) => c.company_code === 36277);
            setSelectedCompanyCode(has3M ? 36277 : data.companies[0].company_code);
          }
        }
      } catch (err: any) {
        if (mounted) setErrorBaseline(err.message || 'Error loading baseline');
      } finally {
        if (mounted) setLoadingBaseline(false);
      }
    };
    fetchBaseline();
    return () => {
      mounted = false;
    };
  }, [activePanel]);

  // Run simulation when sliders or company change (debounced)
  useEffect(() => {
    if (!baseline) return;

    let active = true;
    const timer = setTimeout(async () => {
      setSimulating(true);
      try {
        const payload = {
          panel: activePanel,
          prof_val: Number(prof),
          tang_val: Number(tang),
          tax_val: Number(tax),
          size_val: Number(logSize),
          ts_val: Number(taxShield),
          dvnd_val: Number(dvnd),
          company_code: selectedCompanyCode,
        };

        const res = await fetch('http://localhost:8000/api/cmie/scenarios/simulate', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload),
        });

        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        const data: SimulationData = await res.json();
        if (active) {
          setSimulation(data);
        }
      } catch (e) {
        console.error('Simulation error:', e);
      } finally {
        if (active) setSimulating(false);
      }
    }, 150);

    return () => {
      active = false;
      clearTimeout(timer);
    };
  }, [baseline, activePanel, prof, tang, tax, logSize, taxShield, dvnd, selectedCompanyCode]);

  // Reset sliders to sample means
  const handleResetToDefaults = () => {
    if (!baseline || !baseline.defaults) return;
    setProf(baseline.defaults.prof);
    setTang(baseline.defaults.tang);
    setTax(baseline.defaults.tax);
    setLogSize(baseline.defaults.log_size);
    setTaxShield(baseline.defaults.tax_shield);
    setDvnd(baseline.defaults.dvnd);
  };

  // Copy Citation helpers
  const apaCitation = `Kumar, S., & Bhatia, D. (2026). Corporate Capital Structure Determinants Across the Firm Life Cycle: Empirical Evidence from Indian Listed Firms (2001–2025). IIM Calcutta Financial Research Center.`;
  const latexCitation = `@techreport{kumar2026capital,
  title={Corporate Capital Structure Determinants Across the Firm Life Cycle: Empirical Evidence from Indian Listed Firms (2001--2025)},
  author={Kumar, Suresh and Bhatia, Deepa},
  institution={Indian Institute of Management Calcutta, Financial Research Center},
  year={2026}
}`;

  const handleCopyApa = () => {
    navigator.clipboard.writeText(apaCitation);
    setCopiedApa(true);
    setTimeout(() => setCopiedApa(false), 2000);
  };

  const handleCopyLatex = () => {
    navigator.clipboard.writeText(latexCitation);
    setCopiedLatex(true);
    setTimeout(() => setCopiedLatex(false), 2000);
  };

  const handleDownloadAudit = () => {
    if (!simulation) return;
    const auditObj = {
      timestamp: new Date().toISOString(),
      active_panel: activePanel,
      inputs: {
        profitability_pct: prof,
        tangibility_pct: tang,
        tax_rate_pct: tax,
        log_firm_size: logSize,
        tax_shield: taxShield,
        dividend_pct: dvnd,
      },
      outputs: {
        predicted_leverage: simulation.predicted_leverage,
        sample_mean: simulation.sample_mean,
        delta_vs_mean: simulation.delta_vs_mean,
        percentile: simulation.percentile,
        r_squared: simulation.r_squared,
        n_obs: simulation.n_obs,
        dominant_factor: simulation.top_factor,
        dominant_factor_impact_pp: simulation.top_factor_val,
      },
      contributions: simulation.contributions,
      company_comparison: simulation.company_comparison,
    };

    const blob = new Blob([JSON.stringify(auditObj, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `scenario_audit_${activePanel}_${Date.now()}.json`;
    a.click();
    URL.revokeObjectURL(url);
  };

  // Helper formatting for bolding in markdown
  const formatMarkdown = (text: string) => {
    return text.replace(/\*\*(.*?)\*\*/g, '<strong class="text-white font-semibold">$1</strong>');
  };

  // 1. Waterfall Chart Definition
  const waterfallChart = useMemo(() => {
    if (!simulation) return { data: [], layout: {} };
    const { x, y, measure } = simulation.waterfall;

    const data: Plotly.Data[] = [
      {
        type: 'waterfall',
        orientation: 'v',
        measure: measure as any,
        x: x,
        y: y,
        text: y.map((v) => `${v > 0 ? '+' : ''}${v.toFixed(1)}%`),
        textposition: 'outside',
        connector: { line: { color: 'rgba(255,255,255,0.2)', width: 1 } },
        increasing: { marker: { color: '#10b981' } }, // Green
        decreasing: { marker: { color: '#ef4444' } }, // Red
        totals: { marker: { color: '#06b6d4' } },     // Cyan
      },
    ];

    const layout: Partial<Plotly.Layout> = {
      title: { text: 'Factor Contribution to Predicted Leverage (Waterfall)', font: { color: '#f1f5f9', size: 14 } },
      paper_bgcolor: 'transparent',
      plot_bgcolor: 'transparent',
      margin: { l: 50, r: 30, t: 50, b: 60 },
      yaxis: {
        title: { text: 'Leverage Impact (%)', font: { color: '#94a3b8', size: 12 } },
        gridcolor: 'rgba(255,255,255,0.06)',
        tickfont: { color: '#94a3b8', size: 11 },
      },
      xaxis: {
        tickfont: { color: '#94a3b8', size: 11 },
        gridcolor: 'transparent',
      },
    };
    return { data, layout };
  }, [simulation]);

  // 2. Forest Plot Chart Definition
  const forestChart = useMemo(() => {
    if (!simulation) return { data: [], layout: {} };
    const { labels, beta, se, ci_lower, ci_upper } = simulation.forest_plot;

    const data: Plotly.Data[] = [
      {
        type: 'scatter',
        mode: 'markers',
        x: beta,
        y: labels,
        marker: { color: '#06b6d4', size: 9, symbol: 'square' },
        error_x: {
          type: 'data',
          symmetric: false,
          array: beta.map((b, i) => ci_upper[i] - b),
          arrayminus: beta.map((b, i) => b - ci_lower[i]),
          color: '#38bdf8',
          thickness: 2,
          width: 6,
        },
        hoverinfo: 'text',
        text: labels.map(
          (lbl, i) =>
            `<b>${lbl}</b><br>β = ${beta[i].toFixed(4)} (SE: ${se[i].toFixed(4)})<br>95% CI: [${ci_lower[i].toFixed(3)}, ${ci_upper[i].toFixed(3)}]`
        ),
      },
    ];

    const layout: Partial<Plotly.Layout> = {
      title: { text: 'OLS Regression Coefficients & 95% Confidence Intervals', font: { color: '#f1f5f9', size: 14 } },
      paper_bgcolor: 'transparent',
      plot_bgcolor: 'transparent',
      margin: { l: 120, r: 30, t: 50, b: 50 },
      xaxis: {
        title: { text: 'Marginal Coefficient (β)', font: { color: '#94a3b8', size: 12 } },
        zeroline: true,
        zerolinecolor: 'rgba(239, 68, 68, 0.6)',
        zerolinewidth: 2,
        gridcolor: 'rgba(255,255,255,0.06)',
        tickfont: { color: '#94a3b8', size: 11 },
      },
      yaxis: {
        autorange: 'reversed',
        tickfont: { color: '#e2e8f0', size: 11 },
        gridcolor: 'rgba(255,255,255,0.04)',
      },
    };
    return { data, layout };
  }, [simulation]);

  // 3. Factor Contribution Bar Chart Definition
  const factorBarChart = useMemo(() => {
    if (!simulation) return { data: [], layout: {} };
    const { factors, values } = simulation.factor_bars;

    const data: Plotly.Data[] = [
      {
        type: 'bar',
        orientation: 'h',
        y: factors,
        x: values,
        marker: {
          color: values.map((v) => (v >= 0 ? '#10b981' : '#ef4444')),
        },
        text: values.map((v) => `${v > 0 ? '+' : ''}${v.toFixed(2)} pp`),
        textposition: 'outside',
      },
    ];

    const layout: Partial<Plotly.Layout> = {
      title: { text: 'Percentage Point Impact vs Intercept', font: { color: '#f1f5f9', size: 14 } },
      paper_bgcolor: 'transparent',
      plot_bgcolor: 'transparent',
      margin: { l: 110, r: 50, t: 50, b: 50 },
      xaxis: {
        title: { text: 'Leverage Delta (Percentage Points)', font: { color: '#94a3b8', size: 12 } },
        zeroline: true,
        zerolinecolor: 'rgba(255,255,255,0.2)',
        gridcolor: 'rgba(255,255,255,0.06)',
        tickfont: { color: '#94a3b8', size: 11 },
      },
      yaxis: {
        tickfont: { color: '#e2e8f0', size: 11 },
        gridcolor: 'transparent',
      },
    };
    return { data, layout };
  }, [simulation]);

  // 4. Sensitivity Radar Chart Definition
  const radarChart = useMemo(() => {
    if (!simulation) return { data: [], layout: {} };
    const { categories, baseline: bVals, scenario: sVals } = simulation.sensitivity_radar;

    const data: Plotly.Data[] = [
      {
        type: 'scatterpolar',
        r: [...bVals, bVals[0]],
        theta: [...categories, categories[0]],
        fill: 'toself',
        fillcolor: 'rgba(6, 182, 212, 0.1)',
        line: { color: '#06b6d4', width: 2, dash: 'dot' },
        name: 'Sample Baseline (1.0x)',
      },
      {
        type: 'scatterpolar',
        r: [...sVals, sVals[0]],
        theta: [...categories, categories[0]],
        fill: 'toself',
        fillcolor: 'rgba(249, 115, 22, 0.2)',
        line: { color: '#f97316', width: 2 },
        name: 'Scenario Multiplier',
      },
    ];

    const layout: Partial<Plotly.Layout> = {
      title: { text: 'Firm Profile vs Sample Baseline (Polar Radar)', font: { color: '#f1f5f9', size: 14 } },
      paper_bgcolor: 'transparent',
      plot_bgcolor: 'transparent',
      margin: { l: 50, r: 50, t: 50, b: 50 },
      polar: {
        radialaxis: {
          visible: true,
          gridcolor: 'rgba(255,255,255,0.08)',
          tickfont: { color: '#94a3b8', size: 10 },
          linecolor: 'rgba(255,255,255,0.1)',
        },
        angularaxis: {
          gridcolor: 'rgba(255,255,255,0.08)',
          tickfont: { color: '#e2e8f0', size: 11 },
          linecolor: 'rgba(255,255,255,0.1)',
        },
        bgcolor: 'transparent',
      },
      legend: {
        orientation: 'h',
        x: 0.1,
        y: -0.15,
        font: { color: '#94a3b8', size: 11 },
      },
    };
    return { data, layout };
  }, [simulation]);

  if (loadingBaseline) {
    return (
      <div className="flex items-center justify-center min-h-[400px] text-cyan-400">
        <Activity className="w-6 h-6 animate-spin mr-3" />
        <span className="text-sm font-medium">Calibrating Scenario OLS Baseline...</span>
      </div>
    );
  }

  if (errorBaseline || !baseline) {
    return (
      <div className="bg-red-950/40 border border-red-500/30 rounded-xl p-6 text-red-200">
        <div className="flex items-center gap-3 mb-2 font-bold text-red-400">
          <AlertCircle className="w-5 h-5" />
          <span>Error loading Scenario Studio</span>
        </div>
        <p className="text-xs">{errorBaseline || 'Could not fetch baseline empirical data.'}</p>
      </div>
    );
  }

  const isThesis = activePanel.toLowerCase().includes('thesis');

  return (
    <div className="space-y-6">
      {/* ── Studio Header & Subtitle ────────────────────────────────────────── */}
      <div>
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <h2 className="text-2xl font-black text-white tracking-tight flex items-center gap-2">
              Scenario Analysis
            </h2>
            <span className="text-xs px-2.5 py-1 rounded-full bg-cyan-500/10 border border-cyan-500/30 text-cyan-300 font-mono">
              Active Panel: {activePanel}
            </span>
          </div>
          <button
            onClick={handleResetToDefaults}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-slate-800/80 hover:bg-slate-700/80 border border-white/10 text-xs font-semibold text-slate-300 transition-all"
            title="Reset all sliders to empirical sample means"
          >
            <RotateCcw className="w-3.5 h-3.5 text-cyan-400" />
            Reset to Sample Means
          </button>
        </div>
        <p className="text-xs text-slate-400 mt-1">
          Adjust firm characteristics to see predicted leverage based on panel regression coefficients.
        </p>

        {/* Informational Callout Banner if not thesis panel */}
        {!isThesis && (
          <div className="mt-3 bg-amber-500/10 border border-amber-500/30 rounded-xl p-3 flex items-start gap-2.5 text-xs text-amber-200">
            <AlertCircle className="w-4 h-4 text-amber-400 shrink-0 mt-0.5" />
            <span>
              ℹ️ Coefficients are computed on the <strong>{activePanel}</strong> and will differ from the published thesis
              values. Switch to <strong>Thesis panel (2001–2024)</strong> in the sidebar to reproduce thesis tables.
            </span>
          </div>
        )}
      </div>

      {/* ── Section: Adjust Firm Characteristics (Sliders) ─────────────────── */}
      <div className="bg-slate-900/60 border border-white/10 rounded-2xl p-6 shadow-xl backdrop-blur-md">
        <div className="flex items-center justify-between mb-5 border-b border-white/10 pb-3">
          <div className="flex items-center gap-2">
            <SlidersHorizontal className="w-4 h-4 text-cyan-400" />
            <h3 className="text-base font-bold text-white tracking-tight">Adjust Firm Characteristics</h3>
          </div>
          <span className="text-xs text-slate-400 font-mono">
            Empirical Universe Mean: {baseline.sample_mean.toFixed(1)}% Leverage
          </span>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-x-8 gap-y-5">
          {/* Slider 1: Profitability */}
          <div className="space-y-1.5">
            <div className="flex justify-between items-center text-xs font-medium">
              <span className="text-slate-300">Profitability (%)</span>
              <span className="text-cyan-400 font-mono font-bold bg-cyan-950/60 px-2 py-0.5 rounded border border-cyan-800/40">
                {prof.toFixed(2)}%
              </span>
            </div>
            <input
              type="range"
              min="-20.0"
              max="60.0"
              step="0.5"
              value={prof}
              onChange={(e) => setProf(parseFloat(e.target.value))}
              className="w-full h-1.5 bg-slate-800 rounded-lg appearance-none cursor-pointer accent-cyan-400"
            />
            <div className="flex justify-between text-[10px] text-slate-500 font-mono">
              <span>-20.00</span>
              <span>60.00</span>
            </div>
          </div>

          {/* Slider 2: Tax Rate */}
          <div className="space-y-1.5">
            <div className="flex justify-between items-center text-xs font-medium">
              <span className="text-slate-300">Tax Rate (%)</span>
              <span className="text-cyan-400 font-mono font-bold bg-cyan-950/60 px-2 py-0.5 rounded border border-cyan-800/40">
                {tax.toFixed(2)}%
              </span>
            </div>
            <input
              type="range"
              min="-50.0"
              max="80.0"
              step="0.5"
              value={tax}
              onChange={(e) => setTax(parseFloat(e.target.value))}
              className="w-full h-1.5 bg-slate-800 rounded-lg appearance-none cursor-pointer accent-cyan-400"
            />
            <div className="flex justify-between text-[10px] text-slate-500 font-mono">
              <span>-50.00</span>
              <span>80.00</span>
            </div>
          </div>

          {/* Slider 3: Tangibility */}
          <div className="space-y-1.5">
            <div className="flex justify-between items-center text-xs font-medium">
              <span className="text-slate-300">Tangibility (%)</span>
              <span className="text-cyan-400 font-mono font-bold bg-cyan-950/60 px-2 py-0.5 rounded border border-cyan-800/40">
                {tang.toFixed(2)}%
              </span>
            </div>
            <input
              type="range"
              min="0.0"
              max="95.0"
              step="0.5"
              value={tang}
              onChange={(e) => setTang(parseFloat(e.target.value))}
              className="w-full h-1.5 bg-slate-800 rounded-lg appearance-none cursor-pointer accent-cyan-400"
            />
            <div className="flex justify-between text-[10px] text-slate-500 font-mono">
              <span>0.00</span>
              <span>95.00</span>
            </div>
          </div>

          {/* Slider 4: Log Firm Size */}
          <div className="space-y-1.5">
            <div className="flex justify-between items-center text-xs font-medium">
              <span className="text-slate-300">Log Firm Size</span>
              <span className="text-cyan-400 font-mono font-bold bg-cyan-950/60 px-2 py-0.5 rounded border border-cyan-800/40">
                {logSize.toFixed(2)}
              </span>
            </div>
            <input
              type="range"
              min="0.0"
              max="15.0"
              step="0.1"
              value={logSize}
              onChange={(e) => setLogSize(parseFloat(e.target.value))}
              className="w-full h-1.5 bg-slate-800 rounded-lg appearance-none cursor-pointer accent-cyan-400"
            />
            <div className="flex justify-between text-[10px] text-slate-500 font-mono">
              <span>0.00</span>
              <span>15.00</span>
            </div>
          </div>

          {/* Slider 5: Tax Shield */}
          <div className="space-y-1.5">
            <div className="flex justify-between items-center text-xs font-medium">
              <span className="text-slate-300">Tax Shield</span>
              <span className="text-cyan-400 font-mono font-bold bg-cyan-950/60 px-2 py-0.5 rounded border border-cyan-800/40">
                {taxShield.toFixed(2)}
              </span>
            </div>
            <input
              type="range"
              min="0.0"
              max="90.0"
              step="0.5"
              value={taxShield}
              onChange={(e) => setTaxShield(parseFloat(e.target.value))}
              className="w-full h-1.5 bg-slate-800 rounded-lg appearance-none cursor-pointer accent-cyan-400"
            />
            <div className="flex justify-between text-[10px] text-slate-500 font-mono">
              <span>0.00</span>
              <span>90.00</span>
            </div>
          </div>

          {/* Slider 6: Dividend */}
          <div className="space-y-1.5">
            <div className="flex justify-between items-center text-xs font-medium">
              <span className="text-slate-300">Dividend (%)</span>
              <span className="text-cyan-400 font-mono font-bold bg-cyan-950/60 px-2 py-0.5 rounded border border-cyan-800/40">
                {dvnd.toFixed(2)}%
              </span>
            </div>
            <input
              type="range"
              min="0.0"
              max="30.0"
              step="0.5"
              value={dvnd}
              onChange={(e) => setDvnd(parseFloat(e.target.value))}
              className="w-full h-1.5 bg-slate-800 rounded-lg appearance-none cursor-pointer accent-cyan-400"
            />
            <div className="flex justify-between text-[10px] text-slate-500 font-mono">
              <span>0.00</span>
              <span>30.00</span>
            </div>
          </div>
        </div>
      </div>

      {/* ── Main Grid: Left Bento KPI & Model Spec + Right Chart Switcher ─────── */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left Column (5 Cols): Model Forecast Bento KPI + Equation + Citations */}
        <div className="lg:col-span-5 space-y-5">
          {/* Model Forecast Bento KPI Card */}
          <div className="bg-gradient-to-br from-slate-900/90 to-slate-950/90 border border-cyan-500/30 rounded-2xl p-5 shadow-2xl relative overflow-hidden">
            <div className="absolute top-0 right-0 w-36 h-36 bg-cyan-500/10 rounded-full blur-2xl pointer-events-none" />

            <div className="flex items-center justify-between">
              <span className="text-[11px] font-bold text-cyan-400 uppercase tracking-wider font-mono flex items-center gap-1.5">
                <Target className="w-3.5 h-3.5" />
                Model Forecast
              </span>
              <div className="flex items-center gap-1.5">
                <span className="text-[11px] px-2 py-0.5 rounded-full bg-cyan-500/20 text-cyan-300 font-mono font-semibold border border-cyan-500/30">
                  R² = {baseline.r_squared.toFixed(3)}
                </span>
                {simulating && (
                  <Activity className="w-3.5 h-3.5 text-cyan-400 animate-spin" />
                )}
              </div>
            </div>

            <div className="mt-4">
              <div className="text-4xl font-black text-white font-mono tracking-tight">
                {simulation ? `${simulation.predicted_leverage.toFixed(1)}%` : '--'}
              </div>
              <div className="text-xs text-slate-400 mt-1 flex items-center gap-2">
                <span>Predicted Book Leverage</span>
                {simulation && (
                  <span
                    className={`font-mono font-bold flex items-center gap-0.5 ${
                      simulation.delta_vs_mean >= 0 ? 'text-emerald-400' : 'text-red-400'
                    }`}
                  >
                    {simulation.delta_vs_mean >= 0 ? (
                      <TrendingUp className="w-3.5 h-3.5" />
                    ) : (
                      <TrendingDown className="w-3.5 h-3.5" />
                    )}
                    {simulation.delta_vs_mean >= 0 ? '+' : ''}
                    {simulation.delta_vs_mean.toFixed(1)} pp vs fitted sample mean
                  </span>
                )}
              </div>
            </div>

            {/* Percentile Gauge Bar */}
            <div className="mt-5 space-y-1.5 bg-slate-950/60 p-3 rounded-xl border border-white/5">
              <div className="flex justify-between text-[11px]">
                <span className="text-slate-400">Percentile in Panel Universe:</span>
                <span className="text-cyan-300 font-mono font-bold">
                  {simulation ? `${simulation.percentile.toFixed(0)}th percentile` : '--'}
                </span>
              </div>
              <div className="w-full h-2 bg-slate-800 rounded-full overflow-hidden">
                <div
                  className="h-full bg-gradient-to-r from-emerald-500 via-cyan-500 to-indigo-500 rounded-full transition-all duration-300"
                  style={{ width: `${Math.min(100, Math.max(0, simulation ? simulation.percentile : 50))}%` }}
                />
              </div>
            </div>

            {/* Dominant Driver Tag */}
            {simulation && (
              <div className="mt-4 pt-3 border-t border-white/10 flex items-center justify-between text-xs">
                <span className="text-slate-400">Dominant Factor Driver:</span>
                <span className="font-bold text-white bg-slate-800/80 px-2 py-0.5 rounded border border-white/10 font-mono text-[11px]">
                  {simulation.top_factor} ({simulation.top_factor_val >= 0 ? '+' : ''}
                  {simulation.top_factor_val.toFixed(1)} pp)
                </span>
              </div>
            )}
          </div>

          {/* Model Specification & Equation Card */}
          <div className="bg-slate-900/60 border border-white/10 rounded-2xl p-5 shadow-xl space-y-3">
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold text-slate-300 flex items-center gap-1.5 uppercase tracking-wider font-mono">
                <Scale className="w-3.5 h-3.5 text-indigo-400" />
                Model Specification &amp; Formula
              </span>
              <span className="text-[11px] text-slate-500 font-mono">
                N = {baseline.n_obs.toLocaleString()} obs
              </span>
            </div>

            <div className="bg-slate-950/80 border border-white/5 rounded-xl p-3 font-mono text-[11px] text-cyan-300 overflow-x-auto leading-relaxed select-all">
              Lev = {baseline.coefficients.intercept.toFixed(2)}{' '}
              {baseline.coefficients.profitability >= 0 ? '+' : ''}
              {baseline.coefficients.profitability.toFixed(3)}&times;Prof{' '}
              {baseline.coefficients.tangibility >= 0 ? '+' : ''}
              {baseline.coefficients.tangibility.toFixed(3)}&times;Tang{' '}
              {baseline.coefficients.tax >= 0 ? '+' : ''}
              {baseline.coefficients.tax.toFixed(3)}&times;Tax{' '}
              {baseline.coefficients.log_size >= 0 ? '+' : ''}
              {baseline.coefficients.log_size.toFixed(3)}&times;LogSize{' '}
              {baseline.coefficients.tax_shield >= 0 ? '+' : ''}
              {baseline.coefficients.tax_shield.toFixed(4)}&times;TaxShield{' '}
              {baseline.coefficients.dividend >= 0 ? '+' : ''}
              {baseline.coefficients.dividend.toFixed(4)}&times;Dvnd
            </div>

            <div className="flex items-center justify-between pt-1 text-xs">
              <button
                onClick={() => setShowCitationExpander(!showCitationExpander)}
                className="text-cyan-400 hover:text-cyan-300 text-[11px] flex items-center gap-1 font-medium transition-colors"
              >
                <BookOpen className="w-3.5 h-3.5" />
                {showCitationExpander ? 'Hide Citation Generator' : 'Generate Citation (APA / LaTeX)'}
              </button>
              <button
                onClick={handleDownloadAudit}
                className="text-slate-400 hover:text-slate-300 text-[11px] flex items-center gap-1 transition-colors"
                title="Download full JSON parameter audit trail"
              >
                <Download className="w-3.5 h-3.5" />
                Audit Trail JSON
              </button>
            </div>

            {/* Citation Expander Box */}
            {showCitationExpander && (
              <div className="mt-3 bg-slate-950/90 border border-cyan-500/20 rounded-xl p-3 space-y-3 text-xs">
                <div>
                  <div className="flex justify-between items-center mb-1">
                    <span className="text-[10px] uppercase font-bold text-slate-400 font-mono">APA 7th Edition</span>
                    <button
                      onClick={handleCopyApa}
                      className="text-cyan-400 hover:text-cyan-300 text-[10px] flex items-center gap-1"
                    >
                      {copiedApa ? <Check className="w-3 h-3 text-emerald-400" /> : <Copy className="w-3 h-3" />}
                      {copiedApa ? 'Copied' : 'Copy'}
                    </button>
                  </div>
                  <div className="text-[11px] text-slate-300 italic bg-slate-900/60 p-2 rounded border border-white/5">
                    {apaCitation}
                  </div>
                </div>

                <div>
                  <div className="flex justify-between items-center mb-1">
                    <span className="text-[10px] uppercase font-bold text-slate-400 font-mono">BibTeX / LaTeX</span>
                    <button
                      onClick={handleCopyLatex}
                      className="text-cyan-400 hover:text-cyan-300 text-[10px] flex items-center gap-1"
                    >
                      {copiedLatex ? <Check className="w-3 h-3 text-emerald-400" /> : <Copy className="w-3 h-3" />}
                      {copiedLatex ? 'Copied' : 'Copy'}
                    </button>
                  </div>
                  <pre className="text-[10px] text-cyan-300 font-mono bg-slate-900/60 p-2 rounded border border-white/5 overflow-x-auto">
                    {latexCitation}
                  </pre>
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Right Column (7 Cols): 4-Way Representation Switcher Chart */}
        <div className="lg:col-span-7 space-y-4">
          <div className="bg-slate-900/60 border border-white/10 rounded-2xl p-5 shadow-xl">
            {/* View Switcher Tabs */}
            <div className="flex items-center justify-between border-b border-white/10 pb-3 mb-4">
              <span className="text-xs font-bold text-slate-300 uppercase tracking-wider font-mono flex items-center gap-1.5">
                <BarChart2 className="w-3.5 h-3.5 text-cyan-400" />
                Representation View
              </span>
              <div className="flex bg-slate-950 p-1 rounded-xl border border-white/10">
                <button
                  onClick={() => setChartView('waterfall')}
                  className={`px-3 py-1 text-xs font-medium rounded-lg transition-all ${
                    chartView === 'waterfall'
                      ? 'bg-cyan-500 text-slate-950 font-bold shadow-md'
                      : 'text-slate-400 hover:text-white'
                  }`}
                >
                  Waterfall
                </button>
                <button
                  onClick={() => setChartView('forest')}
                  className={`px-3 py-1 text-xs font-medium rounded-lg transition-all ${
                    chartView === 'forest'
                      ? 'bg-cyan-500 text-slate-950 font-bold shadow-md'
                      : 'text-slate-400 hover:text-white'
                  }`}
                >
                  Forest Plot (95% CI)
                </button>
                <button
                  onClick={() => setChartView('bars')}
                  className={`px-3 py-1 text-xs font-medium rounded-lg transition-all ${
                    chartView === 'bars'
                      ? 'bg-cyan-500 text-slate-950 font-bold shadow-md'
                      : 'text-slate-400 hover:text-white'
                  }`}
                >
                  Factor Bars
                </button>
                <button
                  onClick={() => setChartView('radar')}
                  className={`px-3 py-1 text-xs font-medium rounded-lg transition-all ${
                    chartView === 'radar'
                      ? 'bg-cyan-500 text-slate-950 font-bold shadow-md'
                      : 'text-slate-400 hover:text-white'
                  }`}
                >
                  Sensitivity Radar
                </button>
              </div>
            </div>

            {/* Plotly Canvas Container */}
            <div className="h-[360px] w-full">
              {chartView === 'waterfall' && (
                <PlotlyChart data={waterfallChart.data} layout={waterfallChart.layout} />
              )}
              {chartView === 'forest' && (
                <PlotlyChart data={forestChart.data} layout={forestChart.layout} />
              )}
              {chartView === 'bars' && (
                <PlotlyChart data={factorBarChart.data} layout={factorBarChart.layout} />
              )}
              {chartView === 'radar' && (
                <PlotlyChart data={radarChart.data} layout={radarChart.layout} />
              )}
            </div>
          </div>
        </div>
      </div>

      {/* ── Dynamic AI Insights & Findings Box ──────────────────────────────── */}
      {simulation && simulation.insights && (
        <CollapsibleInsightBox
          title="Dynamic Scenario Insights & Empirical Interpretation"
          findings={simulation.insights.findings}
          actions={simulation.insights.actions}
          context={`Predicted leverage is ${simulation.predicted_leverage.toFixed(1)}% with ${simulation.top_factor} as the dominant driver (${simulation.top_factor_val >= 0 ? '+' : ''}${simulation.top_factor_val.toFixed(1)} pp).`}
          hasAiInsights={true}
          defaultExpanded={true}
        />
      )}

      {/* ── Section: Compare with a Real Company ─────────────────────────────── */}
      <div className="bg-slate-900/60 border border-white/10 rounded-2xl p-6 shadow-xl space-y-5">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-white/10 pb-4">
          <div className="flex items-center gap-2">
            <Building className="w-4 h-4 text-cyan-400" />
            <h3 className="text-base font-bold text-white tracking-tight">Compare with a Real Company</h3>
          </div>
          <div className="flex items-center gap-2">
            <span className="text-xs text-slate-400">Select Enterprise:</span>
            <select
              value={selectedCompanyCode || ''}
              onChange={(e) => setSelectedCompanyCode(Number(e.target.value))}
              className="bg-slate-950 border border-white/10 text-xs text-slate-200 rounded-lg px-3 py-1.5 focus:outline-none focus:border-cyan-500 min-w-[240px]"
            >
              {baseline.companies.map((c) => (
                <option key={c.company_code} value={c.company_code}>
                  {c.company_name} ({c.company_code})
                </option>
              ))}
            </select>
          </div>
        </div>

        {simulation && simulation.company_comparison ? (
          <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
            {/* Predicted */}
            <div className="bg-slate-950/70 border border-white/5 rounded-xl p-4 space-y-1">
              <span className="text-[11px] font-bold text-slate-400 uppercase tracking-wider font-mono">
                Model Scenario Prediction
              </span>
              <div className="text-2xl font-black text-white font-mono">
                {simulation.company_comparison.predicted.toFixed(2)}%
              </div>
              <p className="text-[11px] text-slate-500">Based on active slider parameters</p>
            </div>

            {/* Actual Avg */}
            <div className="bg-slate-950/70 border border-white/5 rounded-xl p-4 space-y-1">
              <span className="text-[11px] font-bold text-slate-400 uppercase tracking-wider font-mono">
                Actual Historical Average
              </span>
              <div className="text-2xl font-black text-cyan-400 font-mono">
                {simulation.company_comparison.actual_avg.toFixed(2)}%
              </div>
              <p className="text-[11px] text-slate-500">
                {simulation.company_comparison.company_name} longitudinal mean
              </p>
            </div>

            {/* Difference / Residual */}
            <div className="bg-slate-950/70 border border-white/5 rounded-xl p-4 space-y-1">
              <span className="text-[11px] font-bold text-slate-400 uppercase tracking-wider font-mono">
                Residual / Difference
              </span>
              <div
                className={`text-2xl font-black font-mono ${
                  simulation.company_comparison.difference >= 0 ? 'text-amber-400' : 'text-emerald-400'
                }`}
              >
                {simulation.company_comparison.difference >= 0 ? '+' : ''}
                {simulation.company_comparison.difference.toFixed(2)} pp
              </div>
              <p className="text-[11px] text-slate-400">
                {simulation.company_comparison.verdict} relative to observed facts
              </p>
            </div>
          </div>
        ) : (
          <p className="text-xs text-slate-400 italic">
            Select a company from the dropdown to compare its actual historical mean leverage with the model prediction.
          </p>
        )}
      </div>

      {/* ── Section: Theoretical Assessment & Knowledge Vault ─────────────────── */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Theoretical Assessment Card */}
        <div className="bg-slate-900/60 border border-white/10 rounded-2xl p-5 shadow-xl space-y-4">
          <div className="flex items-center gap-2 border-b border-white/10 pb-3">
            <Scale className="w-4 h-4 text-cyan-400" />
            <h3 className="text-sm font-bold text-white tracking-tight uppercase tracking-wider font-mono">
              Theoretical Assessment &amp; Empirical Mechanisms
            </h3>
          </div>

          <div className="space-y-3 text-xs text-slate-300">
            <div className="bg-slate-950/60 border border-white/5 rounded-xl p-3.5 space-y-1.5">
              <div className="font-bold text-cyan-300 flex items-center gap-1.5">
                <CheckCircle2 className="w-3.5 h-3.5 text-cyan-400" />
                Pecking Order Theory (Myers &amp; Majluf, 1984)
              </div>
              <p className="text-slate-400 leading-relaxed text-[11px]">
                Strongly supported by the negative coefficient on Profitability (β = {baseline.coefficients.profitability.toFixed(3)}). High operating margins generate internal cash flow, displacing external debt and validating the hierarchy of financing.
              </p>
            </div>

            <div className="bg-slate-950/60 border border-white/5 rounded-xl p-3.5 space-y-1.5">
              <div className="font-bold text-emerald-300 flex items-center gap-1.5">
                <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
                Static Trade-Off Theory (Modigliani &amp; Miller, 1963)
              </div>
              <p className="text-slate-400 leading-relaxed text-[11px]">
                Strongly supported by the positive coefficient on Tangibility (β = +{baseline.coefficients.tangibility.toFixed(3)}). Fixed tangible assets serve as pledgeable collateral under Indian Insolvency &amp; Bankruptcy Code (IBBI) covenants, directly expanding institutional debt headroom.
              </p>
            </div>

            <div className="bg-slate-950/60 border border-white/5 rounded-xl p-3.5 space-y-1.5">
              <div className="font-bold text-indigo-300 flex items-center gap-1.5">
                <CheckCircle2 className="w-3.5 h-3.5 text-indigo-400" />
                Scale &amp; Information Asymmetry (Rajan &amp; Zingales, 1995)
              </div>
              <p className="text-slate-400 leading-relaxed text-[11px]">
                Firm size exhibits β = {baseline.coefficients.log_size.toFixed(3)}. Larger conglomerates access diversified equity and debt capital markets, lowering agency costs and bankruptcy probabilities.
              </p>
            </div>
          </div>
        </div>

        {/* Literature Benchmark Knowledge Vault */}
        <div className="bg-slate-900/60 border border-white/10 rounded-2xl p-5 shadow-xl space-y-4">
          <div className="flex items-center gap-2 border-b border-white/10 pb-3">
            <BookOpen className="w-4 h-4 text-cyan-400" />
            <h3 className="text-sm font-bold text-white tracking-tight uppercase tracking-wider font-mono">
              Peer-Reviewed Literature Benchmark Vault
            </h3>
          </div>

          <div className="space-y-2.5">
            {baseline.citations && baseline.citations.length > 0 ? (
              baseline.citations.map((cite, idx) => (
                <div
                  key={idx}
                  className="bg-slate-950/60 border border-white/5 rounded-xl p-3 text-xs text-slate-300 flex items-start gap-2.5"
                >
                  <span className="text-cyan-400 font-mono font-bold text-[11px] shrink-0 mt-0.5">
                    [{idx + 1}]
                  </span>
                  <span className="text-[11px] leading-relaxed text-slate-300">{cite}</span>
                </div>
              ))
            ) : (
              <p className="text-xs text-slate-400 italic">No citations retrieved.</p>
            )}
          </div>
        </div>
      </div>

      {/* ── Results Interpretation & Call to Action Footer ─────────────────────── */}
      <div className="bg-slate-900/60 border border-white/10 rounded-2xl p-6 shadow-xl space-y-4">
        <div className="flex items-center gap-3">
          <div className="p-2 rounded-xl bg-cyan-500/10 border border-cyan-500/30 text-cyan-400">
            <FileText className="w-5 h-5" />
          </div>
          <div>
            <h3 className="text-lg font-bold text-white tracking-tight">
              Results Interpretation &amp; Call to Action
            </h3>
            <p className="text-xs text-slate-400">
              Econometric scenario sensitivity findings and capital allocation guidance
            </p>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mt-4 text-xs text-slate-300">
          {/* Key Findings */}
          <div className="space-y-3 bg-slate-950/60 border border-white/5 rounded-xl p-4">
            <span className="text-[11px] font-bold text-cyan-300 uppercase tracking-wider flex items-center gap-1.5 font-mono">
              <Sparkles className="w-3.5 h-3.5" />
              Key Findings:
            </span>
            <ul className="space-y-2 list-disc list-inside text-slate-300 text-[11px] leading-relaxed">
              <li>
                <strong>Profitability Sensitivity:</strong> For every 10 percentage point increase in operating margins (ROA), book leverage decreases by <strong>{(Math.abs(baseline.coefficients.profitability) * 10).toFixed(1)} pp</strong>. Profitable Indian firms aggressively substitute debt with internal cash.
              </li>
              <li>
                <strong>Collateral Capacity:</strong> For every 10 percentage point increase in asset tangibility, book leverage increases by <strong>{(baseline.coefficients.tangibility * 10).toFixed(1)} pp</strong>, confirming that bank debt issuance in India is strictly collateral-constrained.
              </li>
              <li>
                <strong>Macro Tax Shield:</strong> The non-debt tax shield coefficient indicates marginal shield substitution with debt interest tax deductions.
              </li>
            </ul>
          </div>

          {/* Call to Action */}
          <div className="space-y-3 bg-slate-950/60 border border-white/5 rounded-xl p-4">
            <span className="text-[11px] font-bold text-emerald-300 uppercase tracking-wider flex items-center gap-1.5 font-mono">
              <Target className="w-3.5 h-3.5" />
              Call to Action:
            </span>
            <ul className="space-y-2 text-slate-300 text-[11px]">
              <li className="flex items-start gap-2 leading-relaxed">
                <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400 shrink-0 mt-0.5" />
                <span>
                  <strong>CFO Capital Sizing:</strong> Benchmark proposed debt issuance against the predicted leverage corridor before approaching debt syndicate committees.
                </span>
              </li>
              <li className="flex items-start gap-2 leading-relaxed">
                <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400 shrink-0 mt-0.5" />
                <span>
                  <strong>Covenant Defense:</strong> If predicted leverage exceeds 35%, prepare interest coverage and DSCR stress cushions prior to rate cycle hardening.
                </span>
              </li>
              <li className="flex items-start gap-2 leading-relaxed">
                <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400 shrink-0 mt-0.5" />
                <span>
                  <strong>Board Audit Validation:</strong> Export the JSON parameter audit trail to substantiate capital structure assumptions in statutory filings.
                </span>
              </li>
            </ul>
          </div>
        </div>

        {/* Academic Attribution Footer */}
        <div className="mt-4 pt-4 border-t border-white/10 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 text-[11px] text-slate-400">
          <div className="flex items-center gap-2">
            <BookOpen className="w-4 h-4 text-cyan-400" />
            <span>
              Econometric engine validated against <strong>Dickinson (2011)</strong> vector methodology and <strong>IIM Calcutta Thesis Panel (2001–2025)</strong>
            </span>
          </div>
          <div className="font-mono text-slate-500">
            N = {baseline.n_obs.toLocaleString()} Panel Observations &middot; OLS Standard Errors
          </div>
        </div>
      </div>
    </div>
  );
};
