import React from 'react';
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
  Compass,
  Network,
  Target,
  FileSpreadsheet,
  Building2,
  BookOpen
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

export const SidebarNav: React.FC<SidebarNavProps> = ({
  activeView,
  onViewChange,
  selectedSymbol,
  onSymbolChange,
  onOpenIngestModal
}) => {
  const navSections = [
    {
      title: 'EXECUTIVE TRUTH TABLE',
      items: [
        {
          id: 'diligence_master' as TerminalView,
          label: '00. Diligence Master & Verdict',
          sublabel: '38+ Tests, Truth Table & Hyper-Index',
          icon: ShieldCheck,
        },
      ],
    },
    {
      title: 'SECTION 0: DOSSIER FOUNDATIONS & DRHP REALITY',
      items: [
        {
          id: 'corporate_foundations' as TerminalView,
          label: '0. Foundations & DRHP Reality',
          sublabel: 'Profile, Segments, Industry & SWOT',
          icon: Building2,
        },
      ],
    },
    {
      title: 'SECTION I: DEAL & VALUATION DISCOVERY',
      items: [
        {
          id: 'market_demand' as TerminalView,
          label: '1. Market Demand & Book',
          sublabel: 'Live bidding, AQI & ML',
          icon: Activity,
        },
        {
          id: 'peer_comps' as TerminalView,
          label: '2. Peer, Sector & Competitor Studio',
          sublabel: 'Peer Comps, Sector Dynamics, Competitors & Post-IPO',
          icon: Layers,
        },
        {
          id: 'huber_studio' as TerminalView,
          label: '3. Huber Econometric Studio',
          sublabel: 'Bias Index & Quantile Cones',
          icon: Calculator,
        },
      ],
    },
    {
      title: 'SECTION II: EVIDENCE & ECONOMETRICS',
      items: [
        {
          id: 'provenance_ledger' as TerminalView,
          label: '4. Provenance Evidence Ledger',
          sublabel: '84-Attr BBox & 5-Gate Accounting',
          icon: FileText,
        },
        {
          id: 'stress_workpapers' as TerminalView,
          label: '5. Econometric & Forensic Lab',
          sublabel: '7 Institutional Econometric Models',
          icon: Sliders,
        },
        {
          id: 'red_flag_scanner' as TerminalView,
          label: '6. 6-Rule Red-Flag Scanner',
          sublabel: 'Governance & Beneish M-Score',
          icon: AlertOctagon,
        },
      ],
    },
    {
      title: 'SECTION III: FORENSIC & SCALE DILIGENCE',
      items: [
        {
          id: 'contingent_litigation' as TerminalView,
          label: '7. Contingent Litigation Radar',
          sublabel: 'SEBI LODR 2% & Ind AS 37',
          icon: Scale,
        },
        {
          id: 'unit_economics' as TerminalView,
          label: '8. Unit Economics & Scale',
          sublabel: '75-85% Sweet Spot & Outlet Moat',
          icon: Factory,
        },
        {
          id: 'unlisted_arbitrage' as TerminalView,
          label: '9. Unlisted Post-Tax Arbitrage',
          sublabel: 'Sec 56(2)(x) & Breakeven Solver',
          icon: Coins,
        },
      ],
    },
    {
      title: 'SECTION IV: GOVERNANCE & IC MANDATE',
      items: [
        {
          id: 'investor_qa' as TerminalView,
          label: '10. Institutional Q&A',
          sublabel: '14 Questions & Churn Shock',
          icon: HelpCircle,
        },
        {
          id: 'stakeholder_lens' as TerminalView,
          label: '11. 6-Persona Stakeholder Lens',
          sublabel: 'CFO, Lender, QIB, Retail, RA',
          icon: Users,
        },
        {
          id: 'ic_board_deck' as TerminalView,
          label: '12. IC Stance & Board Deck',
          sublabel: 'Mandate & 1-Click PPTX/PDF',
          icon: Presentation,
        },
      ],
    },
    {
      title: 'SECTION V: STRATEGY & SCORECARD SUITE',
      items: [
        {
          id: 'strategy_studio' as TerminalView,
          label: 'M1. Consulting Strategy',
          sublabel: 'McKinsey Power Curve & BCG 2x2',
          icon: Compass,
        },
        {
          id: 'strategy_map_dag' as TerminalView,
          label: 'M2. 6-Dim Strategy Map DAG',
          sublabel: 'Causal Value Tree & SHAP Weights',
          icon: Network,
        },
        {
          id: 'cross_vault_matrix' as TerminalView,
          label: 'M3. Cross-Vault BSC Matrix',
          sublabel: 'Unified 6 Pillars & Risk Veto',
          icon: Target,
        },
        {
          id: 'excel_model_studio' as TerminalView,
          label: 'M4. Formula Excel Model',
          sublabel: 'Openpyxl Live Audit & Export',
          icon: FileSpreadsheet,
        },
      ],
    },
    {
      title: 'SECTION VI: KNOWLEDGE GRAPH & ONTOLOGY',
      items: [
        {
          id: 'knowledge_graph' as TerminalView,
          label: 'FIBO Knowledge Graph',
          sublabel: 'Dual Studio, Cypher Bank & Lineage',
          icon: Network,
        },
      ],
    },
  ];

  return (
    <aside className="w-full lg:w-72 h-full bg-[#090D12] border-r border-[#223044] flex flex-col shrink-0 z-20 overflow-hidden">
      {/* Brand Header */}
      <div className="p-4 border-b border-[#223044] flex items-center justify-between">
        <div className="flex items-center gap-2.5">
          <div className="w-7 h-7 rounded bg-gradient-to-br from-cyan-500 to-indigo-600 flex items-center justify-center font-bold text-white font-mono text-sm shadow-md shadow-cyan-950">
            IQ
          </div>
          <div>
            <div className="font-bold text-sm tracking-wide text-slate-100 font-mono">PRE-IPO IQ</div>
            <div className="text-[10px] text-slate-500 font-mono">QUANTITATIVE DILIGENCE TERMINAL</div>
          </div>
        </div>
        <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-emerald-950/60 border border-emerald-800 text-emerald-400 font-bold">
          v3.5.0
        </span>
      </div>

      {/* Active Pre-IPO Deal Dossier Dropdown Selector */}
      <div className="p-3 border-b border-[#223044]">
        <div className="flex items-center justify-between mb-1.5">
          <label className="text-[11px] font-mono text-slate-400 block tracking-wide">
            Active Pre-IPO Deal Dossier
          </label>
          <button
            type="button"
            onClick={onOpenIngestModal}
            className="text-[10px] font-mono text-cyan-400 hover:text-cyan-300 font-bold flex items-center gap-1 cursor-pointer transition-colors"
            title="Ingest new DRHP/RHP filing"
          >
            + Ingest
          </button>
        </div>
        <div className="relative">
          <select
            value={selectedSymbol}
            onChange={(e) => {
              const val = e.target.value;
              if (val === '__INGEST__') {
                onOpenIngestModal();
                e.target.value = selectedSymbol;
              } else {
                onSymbolChange(val);
              }
            }}
            className="w-full appearance-none bg-[#101620] border border-[#223044] hover:border-cyan-500/70 focus:border-cyan-400 focus:outline-none focus:ring-1 focus:ring-cyan-500/50 rounded-lg px-3 py-2.5 pr-8 text-xs font-mono text-slate-100 transition-colors cursor-pointer shadow-inner"
          >
            <option value="NTPCGREEN" className="bg-[#101620] text-slate-100 py-1.5">
              NTPC Green Energy Ltd. (RHP Nov 2024 · ₹10,000 Cr Fresh · Utilities)
            </option>
            <option value="HCCB" className="bg-[#101620] text-slate-100 py-1.5">
              Hindustan Coca-Cola Holdings Ltd. (DRHP 2024 · ₹9,975 Cr OFS · FMCG Giant)
            </option>
            <option value="SWIGGY" className="bg-[#101620] text-slate-100 py-1.5">
              Swiggy Ltd. (DRHP 2024 · ₹4,499 Cr Fresh · Hyperlocal Logistics)
            </option>
            <option value="WAAREE" className="bg-[#101620] text-slate-100 py-1.5">
              Waaree Energies Ltd. (RHP 2024 · ₹4,321 Cr · Solar PV)
            </option>
            <option value="__INGEST__" className="bg-[#151D2A] text-cyan-400 font-bold py-1.5">
              + Ingest New DRHP / RHP PDF Document...
            </option>
          </select>
          <div className="pointer-events-none absolute inset-y-0 right-0 flex items-center px-2.5 text-slate-400">
            <ChevronDown className="w-4 h-4 text-slate-400" />
          </div>
        </div>
      </div>

      {/* Navigation Workspace Menu (12 Specialized Vaults in 4 Sections) */}
      <nav className="p-3 space-y-4 flex-1 overflow-y-auto">
        {navSections.map((section, sIdx) => (
          <div key={sIdx} className="space-y-1">
            <span className="text-[9px] font-mono text-slate-500 uppercase tracking-wider px-2 block font-semibold">
              {section.title}
            </span>
            {section.items.map((item) => {
              const isActive = activeView === item.id;
              const Icon = item.icon;

              return (
                <button
                  key={item.id}
                  data-testid={`nav-${item.id}`}
                  onClick={() => onViewChange(item.id)}
                  className={`w-full text-left p-2 rounded-lg transition-all flex items-center gap-2 cursor-pointer ${isActive
                    ? 'bg-gradient-to-r from-cyan-950/70 to-[#0A101C] border-l-2 border-cyan-400 text-slate-100 font-semibold shadow-sm'
                    : 'text-slate-400 hover:text-slate-200 hover:bg-[#101620]'
                    }`}
                >
                  <Icon className={`w-3.5 h-3.5 shrink-0 ${isActive ? 'text-cyan-400' : 'text-slate-500'}`} />
                  <div className="flex-1 min-w-0">
                    <div className="text-xs font-medium font-sans truncate">{item.label}</div>
                    <div className="text-[10px] text-slate-500 font-mono truncate">{item.sublabel}</div>
                  </div>
                  {isActive && <ChevronRight className="w-3 h-3 text-cyan-400 shrink-0" />}
                </button>
              );
            })}
          </div>
        ))}
      </nav>

      {/* Footer Info */}
      <div className="p-3 border-t border-[#223044] text-[10px] text-slate-500 font-mono flex items-center justify-between">
        <span>NSE PRIMARY ADAPTER</span>
        <span className="text-emerald-400 font-bold">ONLINE</span>
      </div>
    </aside>
  );
};
