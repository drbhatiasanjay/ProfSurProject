import React, { useState, useRef, useEffect } from 'react';
import {
  Layers,
  Activity,
  Calculator,
  ShieldCheck,
  FileText,
  Sliders,
  HelpCircle,
  Users,
  AlertOctagon,
  Coins,
  Presentation,
  ChevronRight,
  ChevronDown,
  Scale,
  Factory,
  Plus,
  Network
} from 'lucide-react';
import { VaultId } from '../types/terminal';

// Backwards-compatible type alias
export type TerminalView = VaultId | 'overview';

interface SidebarNavProps {
  activeView: TerminalView;
  onViewChange: (view: TerminalView) => void;
  selectedSymbol: string;
  onSymbolChange: (symbol: string) => void;
  onOpenIngestModal: () => void;
}

const DOSSIER_OPTIONS = [
  {
    symbol: 'NTPCGREEN',
    shortName: 'NTPC Green Energy Ltd.',
    fullLabel: 'NTPC Green Energy Ltd. (RHP Nov 2024 · ₹10,000 Cr Fresh · Utilities)',
  },
  {
    symbol: 'HCCB',
    shortName: 'Hindustan Coca-Cola Holdings Ltd.',
    fullLabel: 'Hindustan Coca-Cola Holdings Ltd. (DRHP 2024 · ₹9,975 Cr OFS · FMCG Giant)',
  },
  {
    symbol: 'SWIGGY',
    shortName: 'Swiggy Ltd.',
    fullLabel: 'Swiggy Ltd. (DRHP 2024 · ₹4,499 Cr Fresh · Hyperlocal Logistics)',
  },
  {
    symbol: 'WAAREE',
    shortName: 'Waaree Energies Ltd.',
    fullLabel: 'Waaree Energies Ltd. (RHP 2024 · ₹4,321 Cr · Solar PV)',
  },
];

export const SidebarNav: React.FC<SidebarNavProps> = ({
  activeView,
  onViewChange,
  selectedSymbol,
  onSymbolChange,
  onOpenIngestModal
}) => {
  const [isDropdownOpen, setIsDropdownOpen] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setIsDropdownOpen(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const currentDeal = DOSSIER_OPTIONS.find(d => d.symbol === selectedSymbol) || DOSSIER_OPTIONS[0];

  const navSections = [
    {
      title: 'I: DEAL & VALUATION',
      items: [
        {
          id: 'market_demand' as TerminalView,
          number: '1',
          label: 'Market Demand & Book',
          sublabel: 'Live bidding, AQI & ML',
          icon: Activity,
        },
        {
          id: 'peer_comps' as TerminalView,
          number: '2',
          label: 'Live Peer Comps',
          sublabel: 'WACA step-up & Mueller ROCE',
          icon: Layers,
        },
        {
          id: 'huber_studio' as TerminalView,
          number: '3',
          label: 'Huber Econometric Studio',
          sublabel: 'Bias Index & Quantile Cones',
          icon: Calculator,
        },
      ],
    },
    {
      title: 'II: FORENSIC EVIDENCE',
      items: [
        {
          id: 'provenance_ledger' as TerminalView,
          number: '4',
          label: 'Provenance Evidence Ledger',
          sublabel: '84-Attr BBox & 5-Gate Accounting',
          icon: FileText,
        },
        {
          id: 'stress_workpapers' as TerminalView,
          number: '5',
          label: 'Econometric & Forensic Lab',
          sublabel: '7 Institutional Econometric Models',
          icon: Sliders,
        },
        {
          id: 'red_flag_scanner' as TerminalView,
          number: '6',
          label: '6-Rule Red-Flag Scanner',
          sublabel: 'Governance & Beneish M-Score',
          icon: AlertOctagon,
        },
        {
          id: 'knowledge_graph' as TerminalView,
          number: 'KG',
          label: 'FIBO Knowledge Graph',
          sublabel: 'Multi-Hop Contagion & Dual Studio',
          icon: Network,
        },
      ],
    },
    {
      title: 'III: DILIGENCE & SCALE',
      items: [
        {
          id: 'contingent_litigation' as TerminalView,
          number: '7',
          label: 'Contingent Litigation Radar',
          sublabel: 'SEBI LODR 2% & Ind AS 37',
          icon: Scale,
        },
        {
          id: 'unit_economics' as TerminalView,
          number: '8',
          label: 'Unit Economics & Scale',
          sublabel: '75-85% Sweet Spot & Bottling Moat',
          icon: Factory,
        },
        {
          id: 'unlisted_arbitrage' as TerminalView,
          number: '9',
          label: 'Unlisted Post-Tax Arbitrage',
          sublabel: 'Sec 56(2)(x) & Breakeven Solver',
          icon: Coins,
        },
      ],
    },
    {
      title: 'IV: IC MANDATE & DECK',
      items: [
        {
          id: 'investor_qa' as TerminalView,
          number: '10',
          label: 'Institutional Q&A',
          sublabel: '14 Questions & Churn Shock',
          icon: HelpCircle,
        },
        {
          id: 'stakeholder_lens' as TerminalView,
          number: '11',
          label: '6-Persona Stakeholder Lens',
          sublabel: 'CFO, Lender, QIB, Retail, RA',
          icon: Users,
        },
        {
          id: 'ic_board_deck' as TerminalView,
          number: '12',
          label: 'IC Stance & Board Deck',
          sublabel: 'Mandate & 1-Click PPTX/PDF',
          icon: Presentation,
        },
      ],
    },
  ];

  return (
    <aside className="w-full lg:w-72 h-full bg-[#090D12] border-r border-[#223044] flex flex-col shrink-0 z-30 overflow-visible select-none">
      {/* Brand Header */}
      <div className="px-3 py-2.5 border-b border-[#223044] flex items-center justify-between shrink-0">
        <div className="flex items-center gap-2">
          <div className="w-6 h-6 rounded bg-gradient-to-br from-cyan-500 to-indigo-600 flex items-center justify-center font-bold text-white font-mono text-xs shadow-md shadow-cyan-950">
            PS
          </div>
          <div>
            <div className="font-bold text-xs tracking-wider text-slate-100 font-mono leading-none">PROFSUR</div>
            <div className="text-[9px] text-slate-500 font-mono mt-0.5">QUANTITATIVE VALUATION</div>
          </div>
        </div>
        <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-emerald-950/70 border border-emerald-800 text-emerald-400 font-bold">
          v3.5.0
        </span>
      </div>

      {/* Active Pre-IPO Deal Dossier Dropdown (Matches Screen 2 & Screen 3) */}
      <div className="px-2.5 py-2 border-b border-[#223044] shrink-0 bg-[#0c121b] relative z-40" ref={dropdownRef}>
        <div className="flex items-center justify-between mb-1.5 px-0.5">
          <span className="text-[10px] font-mono font-semibold text-slate-400 tracking-wider">
            Active Pre-IPO Deal Dossier
          </span>
          <button
            onClick={onOpenIngestModal}
            className="text-[10px] font-mono text-cyan-400 hover:text-cyan-300 flex items-center gap-0.5 transition-colors cursor-pointer"
            title="Ingest new DRHP/RHP PDF"
          >
            <Plus className="w-3 h-3" />
            <span>Ingest</span>
          </button>
        </div>

        {/* Dropdown Input / Trigger (Screen 2) */}
        <button
          type="button"
          onClick={() => setIsDropdownOpen(prev => !prev)}
          className="w-full bg-[#101620] hover:bg-[#131c2a] border border-[#223044] hover:border-slate-600 rounded px-2.5 py-1.5 flex items-center justify-between transition-colors text-left cursor-pointer group"
        >
          <span className="font-mono text-xs text-slate-100 font-medium truncate pr-1">
            {currentDeal.shortName}
          </span>
          <ChevronDown className={`w-3.5 h-3.5 text-slate-400 group-hover:text-slate-200 transition-transform duration-150 shrink-0 ${isDropdownOpen ? 'rotate-180 text-cyan-400' : ''}`} />
        </button>

        {/* Dropdown Options Popup (Screen 3 - Floating 390px wide over main canvas) */}
        {isDropdownOpen && (
          <div className="absolute left-2.5 w-[390px] max-w-[90vw] top-[calc(100%-2px)] z-50 bg-[#0d1522] border border-cyan-800/90 rounded-md shadow-2xl py-1 text-xs font-mono backdrop-blur-md">
            {DOSSIER_OPTIONS.map((deal) => {
              const isSelected = selectedSymbol === deal.symbol;
              return (
                <button
                  key={deal.symbol}
                  type="button"
                  onClick={() => {
                    onSymbolChange(deal.symbol);
                    setIsDropdownOpen(false);
                  }}
                  className={`w-full text-left px-3 py-2 transition-colors cursor-pointer text-[11px] truncate leading-tight block ${
                    isSelected
                      ? 'bg-cyan-950/90 text-cyan-300 font-semibold border-l-2 border-cyan-400'
                      : 'text-slate-300 hover:bg-[#162030] hover:text-white'
                  }`}
                >
                  {deal.fullLabel}
                </button>
              );
            })}
            <div className="border-t border-[#223044] mt-1 pt-1">
              <button
                type="button"
                onClick={() => {
                  setIsDropdownOpen(false);
                  onOpenIngestModal();
                }}
                className="w-full text-left px-3 py-2 text-cyan-400 hover:text-cyan-300 hover:bg-[#162030] transition-colors cursor-pointer flex items-center gap-1 font-semibold text-[11px] block"
              >
                <span>+ Ingest New DRHP / RHP PDF Document...</span>
              </button>
            </div>
          </div>
        )}
      </div>

      {/* Navigation Workspace Menu (All 12 Specialized Vaults in 4 High-Density Sections) */}
      <nav className="p-2 space-y-2 flex-1 overflow-y-auto scrollbar-thin scrollbar-thumb-[#223044] scrollbar-track-transparent hover:scrollbar-thumb-cyan-500/50">
        {navSections.map((section, sIdx) => (
          <div key={sIdx} className="space-y-0.5">
            <span className="text-[9px] font-mono text-slate-500 uppercase tracking-wider px-1.5 py-0.5 block font-bold">
              {section.title}
            </span>
            {section.items.map((item) => {
              const isActive = activeView === item.id;
              const Icon = item.icon;

              return (
                <button
                  key={item.id}
                  onClick={() => onViewChange(item.id)}
                  title={`${item.number}. ${item.label} — ${item.sublabel}`}
                  className={`w-full text-left px-2 py-1 rounded-md transition-all flex items-center gap-2 cursor-pointer group ${
                    isActive
                      ? 'bg-gradient-to-r from-cyan-950/90 to-[#0A101C] border-l-2 border-cyan-400 text-slate-100 font-semibold shadow-sm'
                      : 'text-slate-400 hover:text-slate-200 hover:bg-[#101620]'
                  }`}
                >
                  <Icon
                    className={`w-3.5 h-3.5 shrink-0 transition-colors ${
                      isActive ? 'text-cyan-400' : 'text-slate-500 group-hover:text-slate-400'
                    }`}
                  />
                  <div className="flex-1 min-w-0 flex items-center justify-between">
                    <span className="text-xs font-medium font-sans truncate">
                      <span className={`font-mono mr-1.5 ${isActive ? 'text-cyan-400 font-bold' : 'text-slate-500'}`}>
                        {item.number}.
                      </span>
                      {item.label}
                    </span>
                  </div>
                  {isActive ? (
                    <ChevronRight className="w-3 h-3 text-cyan-400 shrink-0" />
                  ) : (
                    <span className="text-[9px] font-mono text-slate-600 group-hover:text-slate-400 shrink-0 hidden xl:inline">
                      v{item.number}
                    </span>
                  )}
                </button>
              );
            })}
          </div>
        ))}
      </nav>

      {/* Footer Info */}
      <div className="px-3 py-1.5 border-t border-[#223044] text-[10px] text-slate-500 font-mono flex items-center justify-between shrink-0 bg-[#090D12]">
        <span className="tracking-tight">NSE PRIMARY ADAPTER</span>
        <span className="text-emerald-400 font-bold flex items-center gap-1">
          <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse"></span>
          ONLINE
        </span>
      </div>
    </aside>
  );
};
