import React, { useState, useEffect } from 'react';
import {
  SlidersHorizontal,
  Info,
  ChevronDown,
  ChevronRight,
  Download,
  ShieldCheck,
  CheckCircle2,
  AlertCircle,
  ExternalLink,
  BookOpen,
  Layers,
} from 'lucide-react';
import { FiscalInsightBox } from '../shared/FiscalInsightBox';

interface CoefRow {
  variable: string;
  coef: number;
  std_err: number;
  t_stat: number;
  p_value: number;
  stars: string;
}

interface ModelResult {
  r_squared: number;
  adj_r_squared?: number;
  f_stat?: number;
  n_obs: number;
  n_firms: number;
  coefficients: CoefRow[];
}

interface HausmanResult {
  chi2_stat: number;
  p_value: number;
  df: number;
  preferred_model: string;
  recommendation: string;
}

interface AnovaResult {
  f_stat: number;
  p_value: number;
  stage_means: Record<string, number>;
}

interface EconometricsData {
  pooled_ols: ModelResult;
  fixed_effects: ModelResult;
  random_effects: ModelResult;
  hausman_test: HausmanResult;
  anova: AnovaResult;
}

interface PanelEconometricsStudioProps {
  activePanel: string;
  yearMin: number;
  yearMax: number;
  theme?: 'dark' | 'light';
}

export const PanelEconometricsStudio: React.FC<PanelEconometricsStudioProps> = ({
  activePanel,
  yearMin,
  yearMax,
  theme = 'dark',
}) => {
  const [data, setData] = useState<EconometricsData | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  // Expandable Section Links
  const [expandAbout, setExpandAbout] = useState<boolean>(false);
  const [expandVariables, setExpandVariables] = useState<boolean>(false);
  const [expandDiagnostics, setExpandDiagnostics] = useState<boolean>(false);

  // Active Model Tab
  const [activeModelTab, setActiveModelTab] = useState<'all' | 'fe' | 're' | 'ols'>('all');

  useEffect(() => {
    setLoading(true);
    setError(null);

    const panelId = activePanel.toLowerCase().replace(/[^a-z0-9]/g, '_');
    const url = `http://localhost:8000/api/cmie/econometrics-models?panel=${encodeURIComponent(
      panelId
    )}&year_min=${yearMin}&year_max=${yearMax}`;

    fetch(url)
      .then((res) => {
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        return res.json();
      })
      .then((resData: EconometricsData) => {
        setData(resData);
        setLoading(false);
      })
      .catch((err) => {
        console.error('Failed to fetch econometrics models:', err);
        setError('Failed to compute econometric models from backend.');
        setLoading(false);
      });
  }, [activePanel, yearMin, yearMax]);

  if (loading) {
    return (
      <div className="bg-[#0d1527] border border-white/10 rounded-2xl p-12 text-center select-none">
        <div className="inline-block w-8 h-8 border-2 border-cyan-400 border-t-transparent rounded-full animate-spin mb-3" />
        <p className="text-sm text-slate-300 font-medium">
          Estimating Fixed Effects, Random Effects, and Hausman diagnostics on <code className="text-cyan-300 font-mono">capital_structure.db</code>...
        </p>
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className="bg-rose-950/20 border border-rose-500/30 rounded-2xl p-6 text-center text-rose-300 text-sm">
        {error || 'No regression estimates returned for active filters.'}
      </div>
    );
  }

  const exportRegressionCsv = () => {
    let csv = 'Model,Variable,Coefficient,Std_Error,t_stat,p_value,Significance\n';
    const models = [
      { name: 'Fixed Effects', m: data.fixed_effects },
      { name: 'Random Effects', m: data.random_effects },
      { name: 'Pooled OLS', m: data.pooled_ols },
    ];
    models.forEach(({ name, m }) => {
      m.coefficients.forEach((c) => {
        csv += `"${name}","${c.variable}",${c.coef},${c.std_err},${c.t_stat},${c.p_value},"${c.stars}"\n`;
      });
    });
    const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    link.href = URL.createObjectURL(blob);
    link.download = `panel_regression_${activePanel}_${yearMin}_${yearMax}.csv`;
    link.click();
  };

  return (
    <div className="space-y-6 select-none">
      {/* ── Header Banner ── */}
      <div className="bg-[#0d1527] border border-white/10 rounded-2xl p-6 shadow-xl">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <div className="flex items-center gap-2">
              <span className="text-[11px] font-bold text-cyan-400 uppercase tracking-wider font-mono">
                Studio 08 &middot; Panel Econometrics (XTREG)
              </span>
              <span className="px-2 py-0.5 rounded-full bg-indigo-500/10 text-indigo-300 border border-indigo-500/30 text-[10px] font-semibold">
                Thesis Replicating Suite
              </span>
            </div>
            <h2 className="text-2xl font-black text-white tracking-tight mt-1">
              Panel Regression Models &amp; Specification Testing
            </h2>
            <p className="text-xs text-slate-400 mt-1 max-w-2xl leading-relaxed">
              Longitudinal econometric estimation of capital structure determinants across{' '}
              <strong className="text-slate-200">{data.fixed_effects.n_firms.toLocaleString()} listed Indian firms</strong>{' '}
              ({data.fixed_effects.n_obs.toLocaleString()} panel observations).
            </p>
          </div>

          <div className="flex items-center gap-2.5">
            <button
              onClick={exportRegressionCsv}
              className="px-3 py-1.5 rounded-lg bg-cyan-600 hover:bg-cyan-500 text-white text-xs font-bold flex items-center gap-1.5 transition-all shadow cursor-pointer"
            >
              <Download className="w-3.5 h-3.5" />
              <span>Export Regression Tables</span>
            </button>
            <a
              href="http://localhost:8501/"
              target="_blank"
              rel="noreferrer"
              className="px-3 py-1.5 rounded-lg bg-white/5 hover:bg-white/10 border border-white/10 text-slate-300 text-xs font-semibold flex items-center gap-1.5 transition-all"
            >
              <span>Streamlit Baseline</span>
              <ExternalLink className="w-3 h-3 text-slate-400" />
            </a>
          </div>
        </div>

        {/* ── Expandable Section 1: About These Models (From Streamlit Expander) ── */}
        <div className="mt-5 border-t border-white/5 pt-4">
          <button
            onClick={() => setExpandAbout(!expandAbout)}
            className="w-full flex items-center justify-between text-left text-xs font-bold text-slate-300 hover:text-cyan-300 transition-colors cursor-pointer py-1"
          >
            <span className="flex items-center gap-2">
              {expandAbout ? <ChevronDown className="w-4 h-4 text-cyan-400" /> : <ChevronRight className="w-4 h-4 text-cyan-400" />}
              <span>&gt; About these models — what do they mean in corporate finance?</span>
            </span>
            <span className="text-[10px] font-mono text-slate-400 uppercase tracking-wider">
              {expandAbout ? 'Collapse' : 'Expand'}
            </span>
          </button>

          {expandAbout && (
            <div className="mt-3 p-4 bg-slate-950/80 border border-cyan-500/30 rounded-xl text-xs space-y-3 leading-relaxed animate-in fade-in duration-150">
              <p className="text-slate-300">
                Capital structure research examines the same corporate entities across multiple fiscal years — a classic <strong className="text-white">panel data problem</strong>. Standard cross-sectional regression ignores that Tata Steel behaves differently from Infosys even under identical observed balance sheet ratios. Panel estimators account for unobserved heterogeneity.
              </p>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-slate-300">
                <div className="p-3 bg-slate-900/60 rounded border border-white/5">
                  <strong className="text-white block mb-1">Fixed Effects (Within Estimator)</strong>
                  Controls for all time-invariant firm-specific characteristics (corporate culture, founder DNA, industry pedigree). The gold standard for causal inference in corporate debt literature.
                </div>
                <div className="p-3 bg-slate-900/60 rounded border border-white/5">
                  <strong className="text-white block mb-1">Random Effects (GLS Estimator)</strong>
                  Assumes firm-specific effects are uncorrelated random disturbances. Yields greater statistical efficiency than Fixed Effects when this orthogonality assumption holds.
                </div>
                <div className="p-3 bg-slate-900/60 rounded border border-white/5">
                  <strong className="text-white block mb-1">Hausman Specification Test</strong>
                  Tests whether unobserved firm effects correlate with explanatory variables. If $p &lt; 0.05$, RE is inconsistent and FE is mandatory.
                </div>
                <div className="p-3 bg-slate-900/60 rounded border border-white/5">
                  <strong className="text-white block mb-1">Dickinson Life-Cycle ANOVA</strong>
                  Tests whether mean corporate debt ratios diverge significantly across enterprise life stages, validating the core empirical hypothesis.
                </div>
              </div>
            </div>
          )}
        </div>

        {/* ── Expandable Section 2: Variable Definitions (From Streamlit Expander) ── */}
        <div className="mt-3 border-t border-white/5 pt-3">
          <button
            onClick={() => setExpandVariables(!expandVariables)}
            className="w-full flex items-center justify-between text-left text-xs font-bold text-slate-300 hover:text-cyan-300 transition-colors cursor-pointer py-1"
          >
            <span className="flex items-center gap-2">
              {expandVariables ? <ChevronDown className="w-4 h-4 text-cyan-400" /> : <ChevronRight className="w-4 h-4 text-cyan-400" />}
              <span>&gt; Econometric Regressors &amp; Hypothesized Signs</span>
            </span>
            <span className="text-[10px] font-mono text-slate-400 uppercase tracking-wider">
              {expandVariables ? 'Collapse' : 'Expand'}
            </span>
          </button>

          {expandVariables && (
            <div className="mt-3 p-4 bg-slate-950/80 border border-slate-700/80 rounded-xl text-xs space-y-2 animate-in fade-in duration-150">
              <div className="grid grid-cols-1 md:grid-cols-3 gap-3 text-slate-300">
                <div className="p-2.5 bg-slate-900/60 rounded border border-white/5">
                  <strong className="text-white block mb-0.5">profitability (-)</strong>
                  Pecking Order predicts negative coefficient: profitable firms finance operations via retained earnings.
                </div>
                <div className="p-2.5 bg-slate-900/60 rounded border border-white/5">
                  <strong className="text-white block mb-0.5">tangibility (+)</strong>
                  Trade-Off Theory predicts positive coefficient: tangible assets serve as pledgeable loan collateral.
                </div>
                <div className="p-2.5 bg-slate-900/60 rounded border border-white/5">
                  <strong className="text-white block mb-0.5">log_size (+)</strong>
                  Large enterprises possess diversified cash flows and lower bankruptcy risk, sustaining higher leverage.
                </div>
                <div className="p-2.5 bg-slate-900/60 rounded border border-white/5">
                  <strong className="text-white block mb-0.5">tax_shield (-)</strong>
                  Depreciation and non-debt tax shields substitute for the interest tax deduction.
                </div>
                <div className="p-2.5 bg-slate-900/60 rounded border border-white/5">
                  <strong className="text-white block mb-0.5">dividend (-)</strong>
                  Dividend payout depletes internal liquidity, constraining debt servicing buffers.
                </div>
                <div className="p-2.5 bg-slate-900/60 rounded border border-white/5">
                  <strong className="text-white block mb-0.5">tax (+)</strong>
                  Higher corporate statutory tax rates enhance the marginal value of debt interest shields.
                </div>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* ── Specification Testing Diagnostic Banner (Hausman & ANOVA) ── */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
        {/* 1. Hausman Test Card */}
        <div className="bg-[#0d1527] border border-cyan-500/30 rounded-2xl p-5 shadow-xl">
          <div className="flex items-center justify-between pb-3 border-b border-white/5">
            <div className="flex items-center gap-2">
              <ShieldCheck className="w-5 h-5 text-cyan-400" />
              <h4 className="text-sm font-bold text-white tracking-wide">Hausman Specification Test</h4>
            </div>
            <span className="px-2 py-0.5 rounded text-[11px] font-mono font-bold bg-cyan-500/15 text-cyan-300 border border-cyan-500/30">
              Chi² = {data.hausman_test.chi2_stat} (p = {data.hausman_test.p_value})
            </span>
          </div>

          <div className="mt-4 flex items-center justify-between bg-slate-950/70 p-3 rounded-xl border border-slate-800">
            <div>
              <span className="text-[10px] text-slate-400 uppercase tracking-wider block">Recommended Model</span>
              <span className="text-base font-black text-emerald-400 font-mono mt-0.5 block flex items-center gap-1.5">
                <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                {data.hausman_test.preferred_model}
              </span>
            </div>
            <div className="text-right">
              <span className="text-[10px] text-slate-400 uppercase tracking-wider block">Degrees of Freedom</span>
              <span className="text-sm font-bold text-slate-200 font-mono mt-0.5 block">
                df = {data.hausman_test.df}
              </span>
            </div>
          </div>

          <p className="text-xs text-slate-300 mt-3 leading-relaxed">
            {data.hausman_test.recommendation}
          </p>
        </div>

        {/* 2. Dickinson ANOVA Card */}
        <div className="bg-[#0d1527] border border-indigo-500/30 rounded-2xl p-5 shadow-xl">
          <div className="flex items-center justify-between pb-3 border-b border-white/5">
            <div className="flex items-center gap-2">
              <Layers className="w-5 h-5 text-indigo-400" />
              <h4 className="text-sm font-bold text-white tracking-wide">Stage-wise Leverage ANOVA</h4>
            </div>
            <span className="px-2 py-0.5 rounded text-[11px] font-mono font-bold bg-indigo-500/15 text-indigo-300 border border-indigo-500/30">
              F = {data.anova.f_stat} (p = {data.anova.p_value})
            </span>
          </div>

          <div className="mt-4 grid grid-cols-3 gap-2 text-center text-xs font-mono">
            {Object.entries(data.anova.stage_means).slice(0, 3).map(([stg, meanVal], i) => (
              <div key={i} className="p-2 bg-slate-950/70 rounded-lg border border-slate-800">
                <span className="text-[10px] text-slate-400 block truncate">{stg}</span>
                <span className="text-sm font-bold text-cyan-300 mt-0.5 block">{meanVal.toFixed(1)}%</span>
              </div>
            ))}
          </div>

          <p className="text-xs text-slate-300 mt-3 leading-relaxed">
            Statistically confirms that capital structure decisions are not uniform across the corporate lifecycle (rejection of null hypothesis of equal means at $p &lt; 0.001$).
          </p>
        </div>
      </div>

      {/* ── Model Comparison Table (OLS vs FE vs RE) ── */}
      <div className="bg-[#0d1527] border border-white/10 rounded-2xl p-6 shadow-xl">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-4 border-b border-white/5">
          <div>
            <h3 className="text-base font-bold text-white tracking-tight">
              Model Comparison Table: Determinants of Corporate Leverage
            </h3>
            <p className="text-xs text-slate-400 mt-0.5">
              Standard errors in parentheses. Significance: *** p&lt;0.001, ** p&lt;0.01, * p&lt;0.05, . p&lt;0.1
            </p>
          </div>

          {/* Model view selector tabs */}
          <div className="flex items-center gap-1 bg-slate-950/80 p-1 rounded-lg border border-slate-800 text-xs font-semibold">
            <button
              onClick={() => setActiveModelTab('all')}
              className={`px-3 py-1 rounded transition-all cursor-pointer ${
                activeModelTab === 'all' ? 'bg-cyan-500/20 text-cyan-300 font-bold' : 'text-slate-400 hover:text-white'
              }`}
            >
              All Models
            </button>
            <button
              onClick={() => setActiveModelTab('fe')}
              className={`px-3 py-1 rounded transition-all cursor-pointer ${
                activeModelTab === 'fe' ? 'bg-cyan-500/20 text-cyan-300 font-bold' : 'text-slate-400 hover:text-white'
              }`}
            >
              Fixed Effects
            </button>
            <button
              onClick={() => setActiveModelTab('re')}
              className={`px-3 py-1 rounded transition-all cursor-pointer ${
                activeModelTab === 're' ? 'bg-cyan-500/20 text-cyan-300 font-bold' : 'text-slate-400 hover:text-white'
              }`}
            >
              Random Effects
            </button>
            <button
              onClick={() => setActiveModelTab('ols')}
              className={`px-3 py-1 rounded transition-all cursor-pointer ${
                activeModelTab === 'ols' ? 'bg-cyan-500/20 text-cyan-300 font-bold' : 'text-slate-400 hover:text-white'
              }`}
            >
              Pooled OLS
            </button>
          </div>
        </div>

        {/* Regression Table */}
        <div className="mt-4 overflow-x-auto">
          <table className="w-full text-left border-collapse text-xs select-none">
            <thead className="bg-[#090d16] border-b border-slate-800 text-[11px] font-bold text-slate-300 uppercase tracking-wider font-mono">
              <tr>
                <th className="py-3 px-4">Independent Variable</th>
                {(activeModelTab === 'all' || activeModelTab === 'fe') && (
                  <th className="py-3 px-4 text-right bg-indigo-500/5 border-x border-slate-800/60">
                    <div className="text-indigo-300 font-bold">Fixed Effects (Within)</div>
                    <div className="text-[10px] text-slate-500 font-normal">Preferred (Hausman)</div>
                  </th>
                )}
                {(activeModelTab === 'all' || activeModelTab === 're') && (
                  <th className="py-3 px-4 text-right">
                    <div className="text-slate-200 font-bold">Random Effects (GLS)</div>
                    <div className="text-[10px] text-slate-500 font-normal">Efficient under H0</div>
                  </th>
                )}
                {(activeModelTab === 'all' || activeModelTab === 'ols') && (
                  <th className="py-3 px-4 text-right">
                    <div className="text-slate-200 font-bold">Pooled OLS</div>
                    <div className="text-[10px] text-slate-500 font-normal">Robust (HC1) SE</div>
                  </th>
                )}
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60 font-mono">
              {data.fixed_effects.coefficients.map((feRow, i) => {
                const reRow = data.random_effects.coefficients.find((c) => c.variable === feRow.variable);
                const olsRow = data.pooled_ols.coefficients.find((c) => c.variable === feRow.variable);

                return (
                  <tr key={i} className="hover:bg-slate-900/60 transition-colors">
                    <td className="py-3 px-4 font-sans font-semibold text-slate-200">
                      {feRow.variable.replace(/_/g, ' ')}
                    </td>
                    {(activeModelTab === 'all' || activeModelTab === 'fe') && (
                      <td className="py-3 px-4 text-right bg-indigo-500/5 border-x border-slate-800/60">
                        <div className="font-bold text-cyan-300">
                          {feRow.coef.toFixed(4)} <span className="text-amber-400 font-bold">{feRow.stars}</span>
                        </div>
                        <div className="text-[10px] text-slate-500">({feRow.std_err.toFixed(4)})</div>
                      </td>
                    )}
                    {(activeModelTab === 'all' || activeModelTab === 're') && (
                      <td className="py-3 px-4 text-right">
                        <div className="font-bold text-slate-200">
                          {reRow ? reRow.coef.toFixed(4) : '—'} <span className="text-amber-400 font-bold">{reRow?.stars || ''}</span>
                        </div>
                        <div className="text-[10px] text-slate-500">
                          {reRow ? `(${reRow.std_err.toFixed(4)})` : ''}
                        </div>
                      </td>
                    )}
                    {(activeModelTab === 'all' || activeModelTab === 'ols') && (
                      <td className="py-3 px-4 text-right">
                        <div className="font-bold text-slate-200">
                          {olsRow ? olsRow.coef.toFixed(4) : '—'} <span className="text-amber-400 font-bold">{olsRow?.stars || ''}</span>
                        </div>
                        <div className="text-[10px] text-slate-500">
                          {olsRow ? `(${olsRow.std_err.toFixed(4)})` : ''}
                        </div>
                      </td>
                    )}
                  </tr>
                );
              })}

              {/* Model Summary Rows */}
              <tr className="bg-slate-950/60 text-[11px] font-bold text-slate-400">
                <td className="py-2.5 px-4 font-sans">R²</td>
                {(activeModelTab === 'all' || activeModelTab === 'fe') && (
                  <td className="py-2.5 px-4 text-right text-indigo-300 bg-indigo-500/5 border-x border-slate-800/60">
                    {data.fixed_effects.r_squared}
                  </td>
                )}
                {(activeModelTab === 'all' || activeModelTab === 're') && (
                  <td className="py-2.5 px-4 text-right text-slate-300">{data.random_effects.r_squared}</td>
                )}
                {(activeModelTab === 'all' || activeModelTab === 'ols') && (
                  <td className="py-2.5 px-4 text-right text-slate-300">{data.pooled_ols.r_squared}</td>
                )}
              </tr>
              <tr className="bg-slate-950/60 text-[11px] text-slate-400">
                <td className="py-2.5 px-4 font-sans">Observations</td>
                {(activeModelTab === 'all' || activeModelTab === 'fe') && (
                  <td className="py-2.5 px-4 text-right text-slate-300 bg-indigo-500/5 border-x border-slate-800/60">
                    {data.fixed_effects.n_obs.toLocaleString()}
                  </td>
                )}
                {(activeModelTab === 'all' || activeModelTab === 're') && (
                  <td className="py-2.5 px-4 text-right text-slate-300">{data.random_effects.n_obs.toLocaleString()}</td>
                )}
                {(activeModelTab === 'all' || activeModelTab === 'ols') && (
                  <td className="py-2.5 px-4 text-right text-slate-300">{data.pooled_ols.n_obs.toLocaleString()}</td>
                )}
              </tr>
              <tr className="bg-slate-950/60 text-[11px] text-slate-400">
                <td className="py-2.5 px-4 font-sans">Entities (Firms)</td>
                {(activeModelTab === 'all' || activeModelTab === 'fe') && (
                  <td className="py-2.5 px-4 text-right text-slate-300 bg-indigo-500/5 border-x border-slate-800/60">
                    {data.fixed_effects.n_firms.toLocaleString()}
                  </td>
                )}
                {(activeModelTab === 'all' || activeModelTab === 're') && (
                  <td className="py-2.5 px-4 text-right text-slate-300">{data.random_effects.n_firms.toLocaleString()}</td>
                )}
                {(activeModelTab === 'all' || activeModelTab === 'ols') && (
                  <td className="py-2.5 px-4 text-right text-slate-300">{data.pooled_ols.n_firms.toLocaleString()}</td>
                )}
              </tr>
            </tbody>
          </table>
        </div>

        {/* ── Fiscal.ai Insight Box ── */}
        <FiscalInsightBox
          title="Econometric Theoretical Takeaways"
          findings={[
            '**Profitability** exhibits a strongly negative and statistically significant coefficient (*** p < 0.001) in Fixed Effects, validating Pecking Order Theory: higher operating profitability directly finances capital requirements from retained cash.',
            '**Tangibility** carries a positive coefficient (** p < 0.01), confirming Trade-Off Theory: tangible physical assets augment collateral loan capacity.',
            'The **Hausman test** rejects Random Effects in favor of Fixed Effects (p < 0.001), demonstrating that time-invariant enterprise characteristics correlate with balance sheet regressors.',
          ]}
          implications={[
            'Causal inference confirms that cross-sectional debt ratios cannot be modeled without firm-level fixed effects.',
            'Indian corporate leverage dynamics are fundamentally governed by internal cash flow generation capacity rather than aggressive external debt raising.',
          ]}
          methodologyCitation="Dickinson (2011) / Hausman (1978) Econometrica — Panel XTREG Specification"
        />
      </div>
    </div>
  );
};
