import React, { useState } from 'react';
import {
  CheckCircle2,
  ChevronDown,
  SlidersHorizontal,
  LayoutDashboard,
  BarChart3,
  GitFork,
  TrendingDown,
  Terminal,
  Cpu,
  Bot,
  FileSpreadsheet,
  Settings,
  Database,
  Building,
  ShieldCheck,
  Search,
} from 'lucide-react';

export interface StudioNavItem {
  id: string;
  label: string;
  icon: React.ComponentType<{ className?: string }>;
  category: 'core' | 'dynamics' | 'econometrics' | 'capital' | 'ml' | 'executive' | 'admin';
}

export const STUDIOS: StudioNavItem[] = [
  { id: 'overview', label: '0. Platform Overview', icon: Building, category: 'core' },
  { id: 'dashboard', label: '1. Executive Health Dashboard', icon: LayoutDashboard, category: 'core' },
  { id: 'data_explorer', label: '5. Enterprise Data Explorer', icon: Database, category: 'core' },
  { id: 'benchmarks', label: '2. Sector Peer Benchmarks', icon: BarChart3, category: 'core' },

  { id: 'life_stage_dynamics', label: '20. Life-Stage Dynamics (Dickinson)', icon: GitFork, category: 'dynamics' },
  { id: 'transitions', label: '12. Stage Transitions (Markov)', icon: TrendingDown, category: 'dynamics' },

  { id: 'econometrics', label: '8. Panel Econometrics (XTREG)', icon: SlidersHorizontal, category: 'econometrics' },
  { id: 'advanced_econ', label: '13. Advanced Econometrics (2SLS/GMM)', icon: SlidersHorizontal, category: 'econometrics' },
  { id: 'workbench', label: '14. Econometrics Workbench', icon: SlidersHorizontal, category: 'econometrics' },
  { id: 'interaction_effects', label: '15. Interaction Effects & Moderation', icon: SlidersHorizontal, category: 'econometrics' },
  { id: 'stata_studio', label: '23. Stata Command Studio', icon: Terminal, category: 'econometrics' },

  { id: 'company_financing', label: '26. Company Financing Profile', icon: Building, category: 'capital' },
  { id: 'covenant_headroom', label: '28. Covenant Headroom Defense', icon: ShieldCheck, category: 'capital' },
  { id: 'scenarios', label: '3. Scenario & Rate Shock Studio', icon: TrendingDown, category: 'capital' },

  { id: 'ml_models', label: '9. ML Forecasters & SHAP', icon: Cpu, category: 'ml' },
  { id: 'forecasting', label: '10. Leverage Forecaster', icon: BarChart3, category: 'ml' },
  { id: 'clustering', label: '11. Enterprise Clusters', icon: GitFork, category: 'ml' },

  { id: 'ai_assistant', label: '19. Executive AI Assistant', icon: Bot, category: 'executive' },
  { id: 'board_deck', label: '17. Board Deck Studio (PPTX/PDF)', icon: FileSpreadsheet, category: 'executive' },
  { id: 'company_navigator', label: '18. Company Navigator', icon: Building, category: 'executive' },

  { id: 'admin_activity', label: '16. Audit Log & Activity', icon: ShieldCheck, category: 'admin' },
  { id: 'settings', label: '6. Preferences & System', icon: Settings, category: 'admin' },
];

interface CollapsibleSidebarProps {
  activeStudio: string;
  onSelectStudio: (id: string) => void;
  activePanel: string;
  onChangePanel: (panel: string) => void;
  yearMin?: number;
  yearMax?: number;
  onChangeYearMax?: (val: number) => void;
  onSwitchWorkspace: () => void;
}

export const CollapsibleSidebar: React.FC<CollapsibleSidebarProps> = ({
  activeStudio,
  onSelectStudio,
  activePanel,
  onChangePanel,
  yearMin = 2001,
  yearMax = 2025,
  onChangeYearMax,
  onSwitchWorkspace,
}) => {
  const [localYearMax, setLocalYearMax] = useState(yearMax);
  const [searchFilter, setSearchFilter] = useState('');

  const currentYearMax = onChangeYearMax ? yearMax : localYearMax;
  const handleYearChange = (val: number) => {
    if (onChangeYearMax) {
      onChangeYearMax(val);
    } else {
      setLocalYearMax(val);
    }
  };

  const filteredStudios = STUDIOS.filter((s) =>
    s.label.toLowerCase().includes(searchFilter.toLowerCase())
  );

  return (
    <aside className="w-72 bg-[#090d16] border-r border-white/10 p-4 flex flex-col gap-4 overflow-y-auto select-none">
      {/* Workspace Mode Card */}
      <div>
        <h4 className="text-[10px] font-bold text-slate-400 uppercase tracking-wider mb-2">Workspace Mode</h4>
        <div className="p-2.5 bg-slate-900 border border-cyan-500/35 rounded-lg text-xs font-semibold text-cyan-300 flex items-center justify-between shadow-sm">
          <span>Public Universe (8,600+ CMIE)</span>
          <CheckCircle2 className="w-4 h-4 text-cyan-400" />
        </div>
        <button
          onClick={onSwitchWorkspace}
          className="w-full mt-2 py-1.5 px-3 bg-white/5 hover:bg-white/10 border border-white/10 rounded-md text-[11px] font-semibold text-indigo-300 transition-all cursor-pointer flex items-center justify-center gap-1.5"
        >
          <span>⊞ Switch Workspace Gateway</span>
        </button>
      </div>

      {/* Global Filters Section */}
      <div className="space-y-3 pt-2 border-t border-slate-800">
        <h4 className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">Global Filters</h4>

        {/* Dataset Selectbox */}
        <div>
          <label className="block text-[11px] font-semibold text-slate-300 mb-1">Dataset Panel</label>
          <div className="relative">
            <select
              value={activePanel}
              onChange={(e) => onChangePanel(e.target.value)}
              className="w-full bg-slate-950 border border-slate-700/80 rounded-md px-2.5 py-1.5 text-xs text-slate-200 focus:outline-none focus:border-cyan-400 appearance-none font-sans"
            >
              <option value="bf2001-25_Sept26">bf2001-25_Sept26 (8,677 Firms)</option>
              <option value="(2001-25)_April26">(2001-25)_April26</option>
              <option value="Latest (2001–present)">Latest (2001–present)</option>
              <option value="Thesis (2001–2024)">Thesis (2001–2024)</option>
              <option value="US S&P Sample">US S&P Sample</option>
            </select>
            <ChevronDown className="w-3.5 h-3.5 text-slate-500 absolute right-2.5 top-1/2 -translate-y-1/2 pointer-events-none" />
          </div>
        </div>

        {/* Year Range Filter */}
        <div>
          <div className="flex justify-between items-center text-[11px] font-semibold text-slate-300 mb-1">
            <span>Fiscal Year Window</span>
            <span className="font-mono text-cyan-400 font-bold">{yearMin} – {currentYearMax}</span>
          </div>
          <div className="flex gap-2 items-center">
            <input
              type="range"
              min="2001"
              max="2025"
              value={currentYearMax}
              onChange={(e) => handleYearChange(Number(e.target.value))}
              className="w-full accent-cyan-400 cursor-pointer"
            />
          </div>
        </div>
      </div>

      {/* Analytical Studios Navigation Tree */}
      <div className="space-y-2 pt-2 border-t border-slate-800 flex-1 flex flex-col">
        <div className="flex items-center justify-between">
          <h4 className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">Analytical Studios</h4>
          <span className="text-[10px] text-slate-500 font-mono">{STUDIOS.length} views</span>
        </div>

        {/* Quick Studio Filter Input */}
        <div className="relative">
          <Search className="w-3.5 h-3.5 text-slate-500 absolute left-2.5 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            value={searchFilter}
            onChange={(e) => setSearchFilter(e.target.value)}
            placeholder="Search studio..."
            className="w-full bg-slate-950 border border-slate-800 rounded-md pl-8 pr-2.5 py-1 text-xs text-slate-200 placeholder:text-slate-600 focus:outline-none focus:border-cyan-400"
          />
        </div>

        <div className="space-y-0.5 overflow-y-auto flex-1 pr-1">
          {filteredStudios.map((item) => {
            const Icon = item.icon;
            const isActive = activeStudio === item.id;
            return (
              <button
                key={item.id}
                onClick={() => onSelectStudio(item.id)}
                className={`w-full text-left px-2.5 py-1.5 rounded-md text-xs font-medium transition-all flex items-center gap-2 cursor-pointer ${
                  isActive
                    ? 'bg-cyan-500/18 text-cyan-300 border border-cyan-500/35 font-semibold'
                    : 'text-slate-400 hover:text-slate-200 hover:bg-white/5'
                }`}
              >
                <Icon className={`w-3.5 h-3.5 ${isActive ? 'text-cyan-400' : 'text-slate-500'}`} />
                <span className="truncate">{item.label}</span>
              </button>
            );
          })}
        </div>
      </div>
    </aside>
  );
};
