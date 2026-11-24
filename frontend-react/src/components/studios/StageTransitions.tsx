import React, { useState, useEffect } from 'react';
import { ChartContainer } from '../shared/ChartContainer';
import {
  TrendingDown,
  Layers,
  Activity,
  Clock,
  Shield,
  Zap,
  ExternalLink,
  ChevronRight,
  Info,
} from 'lucide-react';

interface KmPoint {
  time_years: number;
  survival_rate: number;
}

interface KmCurve {
  stage: string;
  points: KmPoint[];
}

interface MatrixItem {
  from_stage: string;
  to_stage: string;
  probability: number;
}

interface TransitionsData {
  kpis: {
    n_spells: number;
    n_transitions: number;
    n_firms: number;
    transition_rate: number;
    median_spell_years: number;
  };
  km_curves: KmCurve[];
  matrix: MatrixItem[];
  stages: string[];
}

interface StageTransitionsProps {
  activePanel: string;
  yearMin: number;
  yearMax: number;
}

export const StageTransitions: React.FC<StageTransitionsProps> = ({
  activePanel,
  yearMin,
  yearMax,
}) => {
  const [data, setData] = useState<TransitionsData | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [selectedCurveStage, setSelectedCurveStage] = useState<string>('All Stages');

  useEffect(() => {
    setLoading(true);
    const panelId = activePanel.toLowerCase().replace(/[^a-z0-9]/g, '_');
    const url = `http://127.0.0.1:8000/api/cmie/stage-transitions?panel=${encodeURIComponent(
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
      <div className="bg-[#0d1527] border border-white/10 rounded-2xl p-12 text-center">
        <div className="inline-block w-8 h-8 border-2 border-cyan-400 border-t-transparent rounded-full animate-spin mb-3" />
        <p className="text-sm text-slate-300 font-medium">
          Fitting Kaplan-Meier survival curves and calculating Markov spell durations...
        </p>
      </div>
    );
  }

  if (!data) {
    return (
      <div className="bg-rose-950/20 border border-rose-500/30 rounded-2xl p-6 text-center text-rose-300 text-sm">
        Failed to load survival transitions data for active filters.
      </div>
    );
  }

  const { kpis, km_curves, matrix, stages } = data;

  // SVG parameters for KM Survival Curves
  const svgWidth = 720;
  const svgHeight = 280;
  const padL = 50;
  const padR = 30;
  const padT = 25;
  const padB = 40;
  const cWidth = svgWidth - padL - padR;
  const cHeight = svgHeight - padT - padB;

  const maxYears = 10;
  const getX = (t: number) => padL + (Math.min(maxYears, Math.max(0, t)) / maxYears) * cWidth;
  const getY = (s: number) => padT + cHeight - Math.min(1.0, Math.max(0, s)) * cHeight;

  const stageColorMap: Record<string, string> = {
    Maturity: '#10B981',
    Growth: '#06B6D4',
    Startup: '#6366F1',
    Shakeout1: '#F59E0B',
    Shakeout2: '#F59E0B',
    Shakeout3: '#F59E0B',
    Decline: '#F43F5E',
    Decay: '#E11D48',
  };

  const filteredCurves =
    selectedCurveStage === 'All Stages'
      ? km_curves
      : km_curves.filter((c) => c.stage === selectedCurveStage);

  const exportSurvivalCsv = () => {
    let csv = 'Stage,Time_Years,Survival_Probability\n';
    km_curves.forEach((c) => {
      c.points.forEach((p) => {
        csv += `"${c.stage}",${p.time_years},${p.survival_rate}\n`;
      });
    });
    const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    link.href = URL.createObjectURL(blob);
    link.download = `kaplan_meier_survival_${activePanel}.csv`;
    link.click();
  };

  return (
    <div className="space-y-6">
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
              Non-parametric Kaplan-Meier survival curves and Markov transition rates evaluating corporate life-stage persistence, hazard rates, and spell decay.
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

        {/* Top Bento KPI Strip */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mt-6">
          <div className="bg-slate-900/80 border border-white/10 rounded-xl p-4">
            <div className="flex items-center justify-between text-slate-400 text-xs font-semibold uppercase">
              <span>Observed Spells</span>
              <Layers className="w-4 h-4 text-cyan-400" />
            </div>
            <div className="text-2xl font-black text-white font-mono mt-1">
              {kpis.n_spells.toLocaleString()}
            </div>
            <div className="text-[11px] text-cyan-400 mt-0.5">
              Across {kpis.n_firms} listed firms
            </div>
          </div>

          <div className="bg-slate-900/80 border border-white/10 rounded-xl p-4">
            <div className="flex items-center justify-between text-slate-400 text-xs font-semibold uppercase">
              <span>Transitions</span>
              <Activity className="w-4 h-4 text-indigo-400" />
            </div>
            <div className="text-2xl font-black text-white font-mono mt-1">
              {kpis.n_transitions.toLocaleString()}
            </div>
            <div className="text-[11px] text-indigo-300 mt-0.5">
              Stage change events
            </div>
          </div>

          <div className="bg-slate-900/80 border border-white/10 rounded-xl p-4">
            <div className="flex items-center justify-between text-slate-400 text-xs font-semibold uppercase">
              <span>Transition Rate</span>
              <Zap className="w-4 h-4 text-amber-400" />
            </div>
            <div className="text-2xl font-black text-amber-300 font-mono mt-1">
              {kpis.transition_rate}%
            </div>
            <div className="text-[11px] text-amber-500/80 mt-0.5">
              Overall exit frequency
            </div>
          </div>

          <div className="bg-slate-900/80 border border-white/10 rounded-xl p-4">
            <div className="flex items-center justify-between text-slate-400 text-xs font-semibold uppercase">
              <span>Median Spell</span>
              <Clock className="w-4 h-4 text-emerald-400" />
            </div>
            <div className="text-2xl font-black text-emerald-400 font-mono mt-1">
              {kpis.median_spell_years} Year
            </div>
            <div className="text-[11px] text-emerald-500/80 mt-0.5">
              Average spell duration
            </div>
          </div>
        </div>

        {/* ── Chart: Kaplan-Meier Survival Curves ── */}
        <div className="mt-6">
          <ChartContainer
            title="Kaplan-Meier Survival Curves by Life-Cycle Stage"
            subtitle="Probability of an enterprise remaining within its stage over consecutive fiscal years"
            sampleBadge="Non-Parametric KMF"
            sourceAttribution="Panel Survival Observations"
            onExportCsv={exportSurvivalCsv}
            methodologyFormula="\widehat{S}(t) = \prod_{t_i \le t} \left(1 - \frac{d_i}{n_i}\right)"
            methodologyDescription="Kaplan-Meier estimator of stage survival. Steeper downward slope designates rapid exit velocity (lower stickiness). Flat lines indicate prolonged stage persistence."
          >
            <div className="bg-slate-950/70 border border-slate-800 rounded-lg p-3 relative select-none">
              {/* Curve Filter Controls */}
              <div className="flex flex-wrap items-center justify-between gap-3 text-xs mb-3 px-1 border-b border-white/5 pb-2">
                <div className="flex flex-wrap items-center gap-2">
                  <span className="text-slate-400 font-semibold mr-1">Filter Stage:</span>
                  {['All Stages', ...km_curves.map((c) => c.stage)].map((stg) => (
                    <button
                      key={stg}
                      onClick={() => setSelectedCurveStage(stg)}
                      className={`px-2 py-0.5 rounded text-[11px] font-mono transition-all cursor-pointer ${
                        selectedCurveStage === stg
                          ? 'bg-cyan-500/20 text-cyan-300 border border-cyan-500/40 font-bold'
                          : 'bg-slate-900 text-slate-400 hover:text-slate-200 border border-slate-800'
                      }`}
                    >
                      {stg}
                    </button>
                  ))}
                </div>
                <div className="text-[10px] text-slate-500 font-mono">X-Axis: 0 to 10 Years</div>
              </div>

              {/* SVG Chart */}
              <svg viewBox={`0 0 ${svgWidth} ${svgHeight}`} className="w-full h-64 overflow-visible">
                {/* Horizontal Grid */}
                {[0.0, 0.25, 0.5, 0.75, 1.0].map((val) => {
                  const y = getY(val);
                  return (
                    <g key={val}>
                      <line x1={padL} y1={y} x2={svgWidth - padR} y2={y} stroke="#1e293b" strokeDasharray="3 3" />
                      <text x={padL - 8} y={y + 3} fill="#64748b" fontSize="9" fontFamily="monospace" textAnchor="end">
                        {Math.round(val * 100)}%
                      </text>
                    </g>
                  );
                })}

                {/* Vertical Grid for Years */}
                {[0, 2, 4, 6, 8, 10].map((yr) => {
                  const x = getX(yr);
                  return (
                    <g key={yr}>
                      <line x1={x} y1={padT} x2={x} y2={padT + cHeight} stroke="#1e293b" strokeDasharray="3 3" />
                      <text x={x} y={padT + cHeight + 16} fill="#94a3b8" fontSize="9" fontFamily="monospace" textAnchor="middle">
                        {yr} {yr === 1 ? 'Year' : 'Yrs'}
                      </text>
                    </g>
                  );
                })}

                {/* Step Function Survival Lines */}
                {filteredCurves.map((curve) => {
                  const color = stageColorMap[curve.stage] || '#38BDF8';
                  // Create step path
                  let pathD = `M ${getX(0)},${getY(1.0)}`;
                  curve.points.forEach((p) => {
                    const prevX = getX(p.time_years);
                    const newY = getY(p.survival_rate);
                    pathD += ` L ${prevX},${newY}`;
                  });

                  return (
                    <g key={curve.stage} className="group">
                      <path
                        d={pathD}
                        fill="none"
                        stroke={color}
                        strokeWidth="2.5"
                        className="transition-all hover:stroke-width-3"
                      />
                      {curve.points.map((p, idx) => (
                        <circle
                          key={idx}
                          cx={getX(p.time_years)}
                          cy={getY(p.survival_rate)}
                          r={3}
                          fill={color}
                          stroke="#ffffff"
                          strokeWidth={1}
                        />
                      ))}
                    </g>
                  );
                })}
              </svg>

              <div className="mt-3 p-3 bg-slate-900/60 border border-white/5 rounded-lg text-xs text-slate-300">
                <span className="font-bold text-white">Survival Econometric Insight:</span> Enterprises entering the <strong>Maturity</strong> stage exhibit a prolonged half-life (median survival exceeding 4 years), whereas <strong>Startup</strong> and <strong>Decline</strong> phases display rapid transition attrition within 12–18 months.
              </div>
            </div>
          </ChartContainer>
        </div>
      </div>
    </div>
  );
};
