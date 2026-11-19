import React from 'react';
import { Database, TrendingUp, ArrowRight, ExternalLink } from 'lucide-react';
import { AuthUser } from '../../services/authService';

interface WorkspaceGatewayProps {
  user: AuthUser;
  onSelectCMIE: () => void;
  onLogout: () => void;
}

export const WorkspaceGateway: React.FC<WorkspaceGatewayProps> = ({
  user,
  onSelectCMIE,
  onLogout,
}) => {
  return (
    <div className="min-h-screen bg-[#060b13] pt-24 pb-12 px-4 relative overflow-hidden select-none">
      {/* Ambient background glows */}
      <div className="absolute top-12 left-1/2 -translate-x-1/2 w-[900px] h-[350px] bg-cyan-500/10 blur-[130px] rounded-full pointer-events-none" />
      <div className="absolute bottom-10 right-10 w-[500px] h-[350px] bg-indigo-500/10 blur-[120px] rounded-full pointer-events-none" />

      <div className="max-w-[980px] mx-auto bg-[#0d1527] border border-cyan-500/22 rounded-2xl p-8 shadow-2xl relative z-10 backdrop-blur-xl">
        <div className="text-center mb-8">
          <div className="inline-flex items-center gap-2 px-3.5 py-1 rounded-full bg-cyan-500/12 border border-cyan-500/30 text-cyan-400 text-xs font-bold tracking-wider uppercase mb-3">
            PROFSUR FINANCIAL INTELLIGENCE PLATFORM
          </div>
          <h1 className="text-3xl font-extrabold text-white tracking-tight font-['Plus_Jakarta_Sans']">
            Select Operational Workspace
          </h1>
          <p className="text-slate-400 text-sm mt-2 max-w-xl mx-auto leading-relaxed">
            Welcome, <strong className="text-slate-100">{user.name}</strong> ({user.role}). Choose your workspace below. You can return here anytime via the <strong className="text-indigo-300">⊞ Workspaces</strong> button in the top bar.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* Card A: CMIE Public Universe */}
          <div className="bg-slate-900/75 border border-white/10 hover:border-cyan-500/40 rounded-2xl p-6 flex flex-col justify-between transition-all group hover:shadow-xl hover:shadow-cyan-950/20">
            <div>
              <span className="inline-block px-2.5 py-1 rounded-md bg-indigo-500/15 text-indigo-400 border border-indigo-500/30 text-[11px] font-bold tracking-wider uppercase mb-3">
                OPTION A &middot; PUBLIC UNIVERSE
              </span>
              <h3 className="text-xl font-bold text-white mb-2 flex items-center gap-2.5">
                <Database className="w-5 h-5 text-indigo-400" />
                CMIE Public Universe (8,600+ Firms)
              </h3>
              <p className="text-slate-300 text-xs leading-relaxed mb-4">
                Longitudinal panel analytics across 8,600+ listed Indian enterprises (2001–2025).
              </p>
              <ul className="space-y-2.5 text-xs text-slate-300">
                <li className="flex items-start gap-2.5">
                  <span className="text-cyan-400 font-bold">&bull;</span>
                  <span>Panel Econometrics &amp; Stata Studio (XTREG, Fixed/Random Effects, IV)</span>
                </li>
                <li className="flex items-start gap-2.5">
                  <span className="text-cyan-400 font-bold">&bull;</span>
                  <span>Dickinson Life-Cycle Stage Classification &amp; Transitions</span>
                </li>
                <li className="flex items-start gap-2.5">
                  <span className="text-cyan-400 font-bold">&bull;</span>
                  <span>Capital Structure, Leverage &amp; Covenant Headroom Defense</span>
                </li>
                <li className="flex items-start gap-2.5">
                  <span className="text-cyan-400 font-bold">&bull;</span>
                  <span>Machine Learning Forecasters &amp; Cluster Benchmarks</span>
                </li>
              </ul>
            </div>

            <button
              onClick={onSelectCMIE}
              className="mt-6 w-full py-2.5 bg-gradient-to-r from-indigo-600 to-sky-600 hover:from-indigo-500 hover:to-sky-500 text-white font-bold text-xs rounded-lg flex items-center justify-center gap-2 transition-all shadow-md group-hover:gap-3 cursor-pointer"
            >
              <span>Launch CMIE Public Universe</span>
              <ArrowRight className="w-4 h-4" />
            </button>
          </div>

          {/* Card B: Pre-IPO Cockpit */}
          <div className="bg-slate-900/75 border border-white/10 hover:border-emerald-500/40 rounded-2xl p-6 flex flex-col justify-between transition-all group hover:shadow-xl hover:shadow-emerald-950/20">
            <div>
              <span className="inline-block px-2.5 py-1 rounded-md bg-emerald-500/15 text-emerald-400 border border-emerald-500/30 text-[11px] font-bold tracking-wider uppercase mb-3">
                OPTION B &middot; PRE-IPO COCKPIT
              </span>
              <h3 className="text-xl font-bold text-white mb-2 flex items-center gap-2.5">
                <TrendingUp className="w-5 h-5 text-emerald-400" />
                Pre-IPO Terminal &amp; FIBO Knowledge Graph
              </h3>
              <p className="text-slate-300 text-xs leading-relaxed mb-4">
                Standalone quantitative diligence &amp; Knowledge Graph platform evaluating prospective DRHP &amp; RHP filings (Port 5174 / 5173).
              </p>
              <ul className="space-y-2.5 text-xs text-slate-300">
                <li className="flex items-start gap-2.5">
                  <span className="text-emerald-400 font-bold">&bull;</span>
                  <span>FIBO Knowledge Graph: 8 SEBI Sections, Verbatim Facts &amp; Subgraph Drilldown</span>
                </li>
                <li className="flex items-start gap-2.5">
                  <span className="text-emerald-400 font-bold">&bull;</span>
                  <span>12+ Specialized Quant Vaults (Valuation Football Field, EV Waterfall)</span>
                </li>
                <li className="flex items-start gap-2.5">
                  <span className="text-emerald-400 font-bold">&bull;</span>
                  <span>2D Stress Sensitivity Heatmaps &amp; Margin Breakeven</span>
                </li>
                <li className="flex items-start gap-2.5">
                  <span className="text-emerald-400 font-bold">&bull;</span>
                  <span>Active Dossier Ingestion (HCCB, NTPC Green, Swiggy, Waaree)</span>
                </li>
              </ul>
            </div>

            <a
              href="http://localhost:5174/"
              target="_blank"
              rel="noreferrer"
              className="mt-6 w-full py-2.5 bg-slate-800 hover:bg-slate-700 text-emerald-300 border border-emerald-500/30 font-bold text-xs rounded-lg flex items-center justify-center gap-2 transition-all shadow-md group-hover:gap-3 cursor-pointer"
            >
              <span>Launch Pre-IPO Terminal (localhost:5174)</span>
              <ExternalLink className="w-4 h-4" />
            </a>
          </div>
        </div>

        {/* Footer Session Note */}
        <div className="mt-8 pt-4 border-t border-white/10 text-center text-xs text-slate-500">
          Logged in as <strong className="text-slate-300">{user.name}</strong> ({user.role}) &middot;{' '}
          <button
            onClick={onLogout}
            className="text-rose-400 hover:text-rose-300 font-semibold cursor-pointer underline underline-offset-2 ml-1"
          >
            Sign Out
          </button>
        </div>
      </div>
    </div>
  );
};
