import React, { useState, useEffect } from 'react';
import { LayoutGrid, Sun, Moon, LogOut, Clock, ChevronDown } from 'lucide-react';
import { AuthUser } from '../../services/authService';

export const DATASET_OPTIONS = [
  { id: 'bf2001-25_Sept26', label: 'bf2001-25_Sept26 (8,677 Firms)' },
  { id: '(2001-25)_April26', label: '(2001-25)_April26' },
  { id: 'Latest (2001–present)', label: 'Latest (2001–present)' },
  { id: 'Thesis (2001–2024)', label: 'Thesis (2001–2024)' },
  { id: 'US S&P Sample', label: 'US S&P Sample' },
];

interface UnifiedTopHeaderProps {
  user: AuthUser;
  activePanel: string;
  onChangePanel: (panel: string) => void;
  theme: 'dark' | 'light';
  onToggleTheme: () => void;
  onSwitchWorkspace: () => void;
  onLogout: () => void;
}

export const UnifiedTopHeader: React.FC<UnifiedTopHeaderProps> = ({
  user,
  activePanel,
  onChangePanel,
  theme,
  onToggleTheme,
  onSwitchWorkspace,
  onLogout,
}) => {
  const [utcTime, setUtcTime] = useState('');
  const [isDropdownOpen, setIsDropdownOpen] = useState(false);

  useEffect(() => {
    const updateClock = () => {
      const now = new Date();
      setUtcTime(
        now.toUTCString().replace('GMT', 'UTC').replace(/:\d{2} UTC/, ' UTC')
      );
    };
    updateClock();
    const timer = setInterval(updateClock, 1000);
    return () => clearInterval(timer);
  }, []);

  return (
    <header className="fixed top-0 left-0 right-0 h-16 bg-[#090d16]/95 backdrop-blur-md border-b border-white/10 z-50 px-6 flex items-center justify-between shadow-lg select-none">
      {/* Left: Branding & Interactive Dataset Dropdown */}
      <div className="flex items-center gap-3.5">
        <div className="flex items-center gap-2">
          <span className="bg-gradient-to-r from-indigo-500 to-cyan-400 text-white font-extrabold text-[11px] px-1.5 py-0.5 rounded tracking-wider shadow-sm">
            LL
          </span>
          <span className="font-extrabold text-cyan-400 text-base tracking-tight font-['Plus_Jakarta_Sans']">
            LifeCycle Leverage
          </span>
          <span className="text-[10px] text-slate-400 font-semibold border border-white/10 px-1.5 py-0.5 rounded">
            v4.0 (React Modernized)
          </span>
        </div>

        {/* Interactive Dataset Dropdown Menu (User Directive) */}
        <div className="relative">
          <button
            onClick={() => setIsDropdownOpen(!isDropdownOpen)}
            className="flex items-center gap-1.5 bg-indigo-500/15 hover:bg-indigo-500/25 text-indigo-300 border border-indigo-500/35 hover:border-indigo-400/50 text-xs font-semibold px-2.5 py-1 rounded-md transition-all cursor-pointer shadow-sm"
            title="Click to switch active dataset panel"
          >
            <span>{activePanel}</span>
            <ChevronDown className="w-3.5 h-3.5 text-indigo-300" />
          </button>

          {isDropdownOpen && (
            <div className="absolute left-0 mt-1.5 w-60 bg-[#0d1527] border border-indigo-500/35 rounded-xl shadow-2xl py-1.5 z-50 animate-in fade-in zoom-in-95 duration-100">
              <div className="px-3 py-1 text-[10px] font-bold text-slate-400 uppercase tracking-wider border-b border-white/5 mb-1">
                Select Active Dataset Panel
              </div>
              {DATASET_OPTIONS.map((opt) => (
                <button
                  key={opt.id}
                  onClick={() => {
                    onChangePanel(opt.id);
                    setIsDropdownOpen(false);
                  }}
                  className={`w-full text-left px-3 py-1.5 text-xs font-medium transition-all flex items-center justify-between cursor-pointer ${
                    activePanel === opt.id
                      ? 'bg-indigo-500/20 text-indigo-300 font-bold border-l-2 border-indigo-400'
                      : 'text-slate-300 hover:bg-white/5 hover:text-white'
                  }`}
                >
                  <span className="truncate">{opt.label}</span>
                  {activePanel === opt.id && <span className="text-indigo-400 text-xs font-mono">&bull;</span>}
                </button>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Right: User telemetry, Clock, Navigation buttons */}
      <div className="flex items-center gap-3.5 text-xs">
        <div className="flex items-center gap-1.5 text-slate-400">
          <strong className="text-slate-200">{user.name}</strong>
          <span>&middot;</span>
          <span className="capitalize text-slate-400">{user.role}</span>
        </div>

        <div className="text-slate-500 font-mono hidden md:flex items-center gap-1 text-[11px]">
          <Clock className="w-3.5 h-3.5" />
          <span>{utcTime}</span>
        </div>

        {/* Workspaces Switcher Button */}
        <button
          onClick={onSwitchWorkspace}
          title="Switch between CMIE and Pre-IPO Workspaces"
          className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-indigo-500/12 text-indigo-300 border border-indigo-500/30 hover:bg-indigo-500/20 font-semibold transition-all cursor-pointer"
        >
          <LayoutGrid className="w-3.5 h-3.5 text-indigo-400" />
          <span>Workspaces</span>
        </button>

        {/* Theme Toggle Button */}
        <button
          onClick={onToggleTheme}
          title={`Switch to ${theme === 'dark' ? 'Light' : 'Dark'} Mode`}
          className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-white/5 text-slate-300 border border-white/10 hover:bg-white/10 font-semibold transition-all cursor-pointer"
        >
          {theme === 'dark' ? <Sun className="w-3.5 h-3.5 text-amber-400" /> : <Moon className="w-3.5 h-3.5 text-indigo-400" />}
          <span>{theme === 'dark' ? 'Light' : 'Dark'}</span>
        </button>

        {/* Sign Out Button */}
        <button
          onClick={onLogout}
          title="Sign Out of Session"
          className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-rose-500/10 text-rose-300 border border-rose-500/30 hover:bg-rose-500/20 font-semibold transition-all cursor-pointer"
        >
          <LogOut className="w-3.5 h-3.5 text-rose-400" />
          <span>Sign Out</span>
        </button>
      </div>
    </header>
  );
};
