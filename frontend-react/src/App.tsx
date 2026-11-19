import React, { useState, useEffect } from 'react';
import { AuthUser, validateSession, logout as apiLogout } from './services/authService';
import { AuthCard } from './components/auth/AuthCard';
import { WorkspaceGateway } from './components/gateway/WorkspaceGateway';
import { UnifiedTopHeader } from './components/layout/UnifiedTopHeader';
import { CollapsibleSidebar } from './components/layout/CollapsibleSidebar';
import { ExecutiveHealthDashboard } from './components/studios/ExecutiveHealthDashboard';
import { EnterpriseDataExplorer } from './components/studios/EnterpriseDataExplorer';
import { SectorPeerBenchmarks } from './components/studios/SectorPeerBenchmarks';
import {
  TrendingUp,
  Shield,
  Layers,
  Award,
  BookOpen,
  ArrowUpRight,
} from 'lucide-react';

export default function App() {
  const [authUser, setAuthUser] = useState<AuthUser | null>(() => {
    const saved = localStorage.getItem('profsur_auth_user');
    if (saved) {
      try {
        return JSON.parse(saved);
      } catch {
        return null;
      }
    }
    return null;
  });

  const [sessionToken, setSessionToken] = useState<string | null>(() => {
    return localStorage.getItem('profsur_session_token');
  });

  const [workspace, setWorkspace] = useState<'gateway' | 'cmie' | 'pre_ipo'>('gateway');
  const [activeStudio, setActiveStudio] = useState<string>('dashboard');
  const [activePanel, setActivePanel] = useState<string>('bf2001-25_Sept26');
  const [yearMin, setYearMin] = useState<number>(2001);
  const [yearMax, setYearMax] = useState<number>(2025);
  const [theme, setTheme] = useState<'dark' | 'light'>('dark');

  // Validate session on load
  useEffect(() => {
    if (sessionToken) {
      validateSession(sessionToken).then((res) => {
        if (res.authenticated && res.user) {
          setAuthUser(res.user);
          localStorage.setItem('profsur_auth_user', JSON.stringify(res.user));
        } else {
          // Token expired or invalid
          setAuthUser(null);
          setSessionToken(null);
          localStorage.removeItem('profsur_auth_user');
          localStorage.removeItem('profsur_session_token');
        }
      });
    }
  }, [sessionToken]);

  const handleLoginSuccess = (user: AuthUser, token: string) => {
    setAuthUser(user);
    setSessionToken(token);
    localStorage.setItem('profsur_auth_user', JSON.stringify(user));
    localStorage.setItem('profsur_session_token', token);
    setWorkspace('gateway');
  };

  const handleLogout = async () => {
    if (sessionToken) {
      await apiLogout(sessionToken);
    }
    setAuthUser(null);
    setSessionToken(null);
    localStorage.removeItem('profsur_auth_user');
    localStorage.removeItem('profsur_session_token');
    setWorkspace('gateway');
  };

  // ── 1. LOGIN SCREEN ──
  if (!authUser) {
    return (
      <div className="min-h-screen bg-[#060b13] flex items-center justify-center p-4 relative overflow-hidden select-none">
        <div className="absolute top-0 left-1/2 -translate-x-1/2 w-[800px] h-[400px] bg-cyan-500/10 blur-[120px] rounded-full pointer-events-none" />
        <div className="absolute bottom-0 right-0 w-[500px] h-[400px] bg-indigo-500/10 blur-[100px] rounded-full pointer-events-none" />
        <div className="absolute bottom-0 left-0 w-[500px] h-[400px] bg-emerald-500/8 blur-[100px] rounded-full pointer-events-none" />

        <AuthCard onLoginSuccess={handleLoginSuccess} />
      </div>
    );
  }

  // ── 2. OPERATIONAL WORKSPACE GATEWAY ──
  if (workspace === 'gateway') {
    return (
      <div className="min-h-screen bg-[#060b13] text-slate-100 flex flex-col">
        <UnifiedTopHeader
          user={authUser}
          activePanel={activePanel}
          onChangePanel={setActivePanel}
          theme={theme}
          onToggleTheme={() => setTheme(theme === 'dark' ? 'light' : 'dark')}
          onSwitchWorkspace={() => setWorkspace('gateway')}
          onLogout={handleLogout}
        />
        <WorkspaceGateway
          user={authUser}
          onSelectCMIE={() => setWorkspace('cmie')}
          onLogout={handleLogout}
        />
      </div>
    );
  }

  // ── 3. CMIE PUBLIC UNIVERSE WORKSPACE (OPTION A) ──
  return (
    <div className="min-h-screen bg-[#060b13] text-slate-100 flex flex-col pt-16">
      <UnifiedTopHeader
        user={authUser}
        activePanel={activePanel}
        onChangePanel={setActivePanel}
        theme={theme}
        onToggleTheme={() => setTheme(theme === 'dark' ? 'light' : 'dark')}
        onSwitchWorkspace={() => setWorkspace('gateway')}
        onLogout={handleLogout}
      />

      <div className="flex-1 flex overflow-hidden">
        {/* Left Sidebar */}
        <CollapsibleSidebar
          activeStudio={activeStudio}
          onSelectStudio={setActiveStudio}
          activePanel={activePanel}
          onChangePanel={setActivePanel}
          yearMin={yearMin}
          yearMax={yearMax}
          onChangeYearMax={setYearMax}
          onSwitchWorkspace={() => setWorkspace('gateway')}
        />

        {/* Main Content Area */}
        <main className="flex-1 bg-[#060b13] p-6 overflow-y-auto">
          {/* Top Macro Telemetry KPI Strip */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
            <div className="bg-[#0d1527] border border-white/10 rounded-xl p-4 shadow-sm hover:border-cyan-500/30 transition-all">
              <div className="flex items-center justify-between text-slate-400 text-xs font-semibold uppercase tracking-wider">
                <span>Total Listed Universe</span>
                <Layers className="w-4 h-4 text-cyan-400" />
              </div>
              <div className="text-2xl font-black text-white font-mono mt-1">8,677</div>
              <div className="flex items-center gap-1.5 mt-1 text-[11px] text-emerald-400 font-semibold">
                <ArrowUpRight className="w-3.5 h-3.5" />
                <span>Prowess Indian Equities (2001–2025)</span>
              </div>
            </div>

            <div className="bg-[#0d1527] border border-white/10 rounded-xl p-4 shadow-sm hover:border-cyan-500/30 transition-all">
              <div className="flex items-center justify-between text-slate-400 text-xs font-semibold uppercase tracking-wider">
                <span>Mean Book Leverage</span>
                <TrendingUp className="w-4 h-4 text-indigo-400" />
              </div>
              <div className="text-2xl font-black text-white font-mono mt-1">20.7%</div>
              <div className="text-[11px] text-slate-400 mt-1">
                <span>Total Debt / Total Assets (SD = 38.6%)</span>
              </div>
            </div>

            <div className="bg-[#0d1527] border border-white/10 rounded-xl p-4 shadow-sm hover:border-cyan-500/30 transition-all">
              <div className="flex items-center justify-between text-slate-400 text-xs font-semibold uppercase tracking-wider">
                <span>Median Leverage</span>
                <Shield className="w-4 h-4 text-emerald-400" />
              </div>
              <div className="text-2xl font-black text-cyan-400 font-mono mt-1">15.1%</div>
              <div className="text-[11px] text-emerald-400 mt-1 flex items-center gap-1">
                <span>50th Percentile (Right-Skewed)</span>
              </div>
            </div>

            <div className="bg-[#0d1527] border border-white/10 rounded-xl p-4 shadow-sm hover:border-cyan-500/30 transition-all">
              <div className="flex items-center justify-between text-slate-400 text-xs font-semibold uppercase tracking-wider">
                <span>Mature Cash Cows</span>
                <Award className="w-4 h-4 text-amber-400" />
              </div>
              <div className="text-2xl font-black text-amber-400 font-mono mt-1">52.4%</div>
              <div className="text-[11px] text-amber-500/80 mt-1">
                <span>Dickinson (+, -, -) cash flow vector</span>
              </div>
            </div>
          </div>

          {/* Dynamic Analytical Studio Canvas */}
          {activeStudio === 'dashboard' && (
            <ExecutiveHealthDashboard
              activePanel={activePanel}
              yearMin={yearMin}
              yearMax={yearMax}
            />
          )}

          {activeStudio === 'data_explorer' && (
            <EnterpriseDataExplorer
              activePanel={activePanel}
              yearMin={yearMin}
              yearMax={yearMax}
            />
          )}

          {activeStudio === 'benchmarks' && (
            <SectorPeerBenchmarks
              activePanel={activePanel}
              yearMin={yearMin}
              yearMax={yearMax}
            />
          )}

          {activeStudio === 'overview' && (
            <div className="bg-[#0d1527] border border-cyan-500/20 rounded-2xl p-6 shadow-xl space-y-6">
              <div>
                <span className="text-[11px] font-bold text-cyan-400 uppercase tracking-wider font-mono">
                  Studio 00 &middot; Theory &amp; Foundations
                </span>
                <h2 className="text-2xl font-black text-white tracking-tight mt-0.5">
                  Academic Platform Overview
                </h2>
                <p className="text-xs text-slate-400 mt-1 max-w-2xl leading-relaxed">
                  Theoretical orientation and empirical econometric framework examining corporate leverage dynamics across enterprise life stages.
                </p>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
                <div className="bg-slate-900/80 border border-white/10 rounded-xl p-5">
                  <div className="text-xs font-bold text-indigo-400 uppercase mb-1">Theoretical Anchor 1</div>
                  <h4 className="text-base font-bold text-white mb-2">Trade-Off Theory (TOT)</h4>
                  <p className="text-xs text-slate-400 leading-relaxed">
                    Firms balance tax shields of debt (tc &times; Debt) against expected costs of financial distress (PV of Financial Distress). Predicts higher leverage for mature, tangible cash cows.
                  </p>
                </div>

                <div className="bg-slate-900/80 border border-white/10 rounded-xl p-5">
                  <div className="text-xs font-bold text-cyan-400 uppercase mb-1">Theoretical Anchor 2</div>
                  <h4 className="text-base font-bold text-white mb-2">Pecking Order Theory (POT)</h4>
                  <p className="text-xs text-slate-400 leading-relaxed">
                    Asymmetric information dictates a financing hierarchy: Internal Funds $\to$ Safe Debt $\to$ Equity. Highly profitable growth enterprises borrow less because internal cash flows suffice.
                  </p>
                </div>

                <div className="bg-slate-900/80 border border-white/10 rounded-xl p-5">
                  <div className="text-xs font-bold text-amber-400 uppercase mb-1">Empirical Method</div>
                  <h4 className="text-base font-bold text-white mb-2">Dickinson (2011) Vector</h4>
                  <p className="text-xs text-slate-400 leading-relaxed">
                    Classifies enterprises into 5 life-cycle phases using cash-flow signs (OCF, ICF, FCF) avoiding ad-hoc firm age or size proxies:
                    Mature = (+, -, -), Growth = (+, -, +).
                  </p>
                </div>
              </div>
            </div>
          )}

          {activeStudio !== 'dashboard' &&
            activeStudio !== 'overview' &&
            activeStudio !== 'data_explorer' &&
            activeStudio !== 'benchmarks' && (
            <div className="bg-[#0d1527] border border-white/10 rounded-2xl p-8 shadow-xl text-center">
              <BookOpen className="w-10 h-10 text-cyan-400 mx-auto mb-3" />
              <h3 className="text-xl font-bold text-white mb-1 capitalize">
                {activeStudio.replace(/_/g, ' ')} Studio
              </h3>
              <p className="text-xs text-slate-400 max-w-md mx-auto mb-4">
                This studio is scheduled for Phase-by-Phase porting from Streamlit into React 19 on Port 5175.
              </p>
              <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-indigo-500/10 border border-indigo-500/30 text-indigo-300 text-xs font-mono">
                <span>Phase Roadmap Active &middot; Backend Connected to Port 8000</span>
              </div>
            </div>
          )}
        </main>
      </div>
    </div>
  );
}
