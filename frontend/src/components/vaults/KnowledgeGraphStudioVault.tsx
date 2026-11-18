import React, { useState, useEffect, useMemo, useCallback } from 'react';
import {
  ReactFlow,
  MiniMap,
  Controls,
  Background,
  useNodesState,
  useEdgesState,
  Node,
  Edge,
  Position,
  Handle,
  MarkerType
} from '@xyflow/react';
import '@xyflow/react/dist/style.css';

import {
  StatutoryOfferDetails
} from '../../types/terminal';
import {
  fetchPreIPOKGCanvas,
  queryPreIPOKG,
  fetchPreIPOSHACLAudit,
  fetchPreIPOValuationSimulator,
  KGCanvasResponse,
  KGQueryResult,
  KGSHACLAuditReport,
  KGValuationSimulationResult,
  KGNodeData
} from '../../services/dataService';
import {
  Network,
  Search,
  Sparkles,
  Sliders,
  ShieldCheck,
  AlertTriangle,
  FileText,
  Layers,
  HelpCircle,
  ExternalLink,
  ChevronRight,
  TrendingDown,
  Info,
  CheckCircle2,
  RefreshCw,
  Eye,
  Maximize2,
  Binary,
  BookOpen
} from 'lucide-react';
import { PdfBoundingBoxDrawer } from './kg/PdfBoundingBoxDrawer';
import { FormulaLineageModal } from './kg/FormulaLineageModal';
import { CypherBankInspector } from './kg/CypherBankInspector';
import { StatutorySectionSummaryGrid } from './kg/StatutorySectionSummaryGrid';
import { StatutorySectionDrilldownView } from './kg/StatutorySectionDrilldownView';

// =====================================================================
// Custom Custom Node Component for FIBO Financial Entities
// =====================================================================

interface CustomFiboNodeProps {
  data: {
    label?: string;
    name?: string;
    properties?: Record<string, any>;
    pageNumber?: number;
    confidence?: number;
    quote?: string;
    isSelected?: boolean;
    isHighlighted?: boolean;
    onSelectNode?: (id: string) => void;
    id: string;
  };
}

const getFiboBadgeStyle = (label: string = '') => {
  switch (label.toLowerCase()) {
    case 'company':
      return { bg: 'bg-blue-500/10 border-blue-500/30 text-blue-400', dot: 'bg-blue-500', border: 'hover:border-blue-500' };
    case 'subsidiary':
      return { bg: 'bg-emerald-500/10 border-emerald-500/30 text-emerald-400', dot: 'bg-emerald-500', border: 'hover:border-emerald-500' };
    case 'promoter':
      return { bg: 'bg-purple-500/10 border-purple-500/30 text-purple-400', dot: 'bg-purple-500', border: 'hover:border-purple-500' };
    case 'offering':
      return { bg: 'bg-amber-500/10 border-amber-500/30 text-amber-400', dot: 'bg-amber-500', border: 'hover:border-amber-500' };
    case 'litigation':
      return { bg: 'bg-rose-500/10 border-rose-500/30 text-rose-400', dot: 'bg-rose-500', border: 'hover:border-rose-500' };
    case 'territory':
      return { bg: 'bg-cyan-500/10 border-cyan-500/30 text-cyan-400', dot: 'bg-cyan-500', border: 'hover:border-cyan-500' };
    default:
      return { bg: 'bg-slate-500/10 border-slate-500/30 text-slate-400', dot: 'bg-slate-400', border: 'hover:border-slate-400' };
  }
};

const FiboCardNode: React.FC<CustomFiboNodeProps> = ({ data }) => {
  const badgeStyle = getFiboBadgeStyle(data.label);
  const isHighlighted = data.isHighlighted;
  const isSelected = data.isSelected;

  return (
    <div
      onClick={() => data.onSelectNode && data.onSelectNode(data.id)}
      className={`relative w-72 rounded-xl p-3.5 backdrop-blur-md transition-all duration-200 cursor-pointer text-left ${
        isHighlighted
          ? 'bg-slate-900/95 ring-2 ring-amber-400 shadow-lg shadow-amber-500/20'
          : isSelected
          ? 'bg-slate-900/95 ring-2 ring-blue-500 shadow-lg shadow-blue-500/20'
          : 'bg-slate-900/80 border border-slate-800 hover:border-slate-700 shadow-md'
      }`}
    >
      <Handle type="target" position={Position.Top} className="!bg-slate-400 !w-2 !h-2" />
      
      {/* Top Header */}
      <div className="flex items-center justify-between mb-2">
        <span className={`inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full text-[10px] font-semibold border ${badgeStyle.bg}`}>
          <span className={`w-1.5 h-1.5 rounded-full ${badgeStyle.dot}`} />
          {data.label?.toUpperCase() || 'ENTITY'}
        </span>
        {data.pageNumber && (
          <span className="text-[10px] text-slate-400 flex items-center gap-1 font-mono">
            <FileText className="w-2.5 h-2.5 text-slate-500" />
            p.{data.pageNumber}
          </span>
        )}
      </div>

      {/* Entity Title */}
      <div className="font-semibold text-xs text-slate-100 line-clamp-1 mb-1">
        {data.name || data.id}
      </div>

      {/* Key Properties / Badges */}
      {data.properties && Object.keys(data.properties).length > 0 && (
        <div className="flex flex-wrap gap-1 mt-2">
          {Object.entries(data.properties).slice(0, 3).map(([k, v]) => (
            <span key={k} className="text-[9px] px-1.5 py-0.5 rounded bg-slate-800/80 text-slate-300 font-mono">
              {k}: <strong className="text-slate-100">{String(v)}</strong>
            </span>
          ))}
        </div>
      )}

      {/* Quote Preview */}
      {data.quote && (
        <p className="mt-2 text-[10px] text-slate-400 italic line-clamp-2 border-l border-slate-700 pl-1.5">
          "{data.quote}"
        </p>
      )}

      <Handle type="source" position={Position.Bottom} className="!bg-slate-400 !w-2 !h-2" />
    </div>
  );
};

const nodeTypes = {
  fiboCard: FiboCardNode
};

// =====================================================================
// Main Component: KnowledgeGraphStudioVault
// =====================================================================

interface KnowledgeGraphStudioVaultProps {
  offer: StatutoryOfferDetails;
}

export const KnowledgeGraphStudioVault: React.FC<KnowledgeGraphStudioVaultProps> = ({ offer }) => {
  const symbol = offer.symbol || 'HCCH';
  
  // Tri-Mode Switcher: 'sections' (SEBI Sections Hierarchy & Verbatim Facts) | 'macro' (Global Macro Graph) | 'quant' (Expert Quant Studio)
  const [personaMode, setPersonaMode] = useState<'sections' | 'macro' | 'quant'>('sections');
  const [activeDrilldownSectionId, setActiveDrilldownSectionId] = useState<string | null>(null);

  // React Flow state
  const [nodes, setNodes, onNodesChange] = useNodesState<Node>([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState<Edge>([]);

  // Selected Node for Detail Inspector
  const [selectedNodeId, setSelectedNodeId] = useState<string | null>('HCCH');

  // Query & Analytical State
  const [currentTier, setCurrentTier] = useState<number>(1);
  const [nlQueryInput, setNlQueryInput] = useState<string>('Where does the IPO proceeds go?');
  const [queryResult, setQueryResult] = useState<KGQueryResult | null>(null);
  const [isLoadingQuery, setIsLoadingQuery] = useState<boolean>(false);

  // SHACL Audit state
  const [shaclReport, setShaclReport] = useState<KGSHACLAuditReport | null>(null);

  // Valuation Simulator state
  const [pruningThreshold, setPruningThreshold] = useState<number>(0.65);
  const [territoryDiscount, setTerritoryDiscount] = useState<number>(25.0);
  const [channelDiscount, setChannelDiscount] = useState<number>(10.0);
  const [simResult, setSimResult] = useState<KGValuationSimulationResult | null>(null);

  // In-App PDF Bounding Box Viewer Drawer State
  const [isPdfDrawerOpen, setIsPdfDrawerOpen] = useState<boolean>(false);
  const [pdfDrawerPage, setPdfDrawerPage] = useState<number>(18);
  const [pdfDrawerQuote, setPdfDrawerQuote] = useState<string>('');
  const [pdfDrawerClause, setPdfDrawerClause] = useState<string | undefined>(undefined);

  // Formula Lineage DAG Modal State
  const [isFormulaModalOpen, setIsFormulaModalOpen] = useState<boolean>(false);

  const handleOpenPdfDrawer = useCallback((page: number, quote: string, clause?: string) => {
    setPdfDrawerPage(page);
    setPdfDrawerQuote(quote);
    setPdfDrawerClause(clause);
    setIsPdfDrawerOpen(true);
  }, []);

  const handleHighlightSubgraph = useCallback((nodeIds: string[], edgeIds: string[]) => {
    setNodes(prev => prev.map(node => ({
      ...node,
      data: {
        ...node.data,
        isHighlighted: nodeIds.includes(node.id)
      }
    })));
    setEdges(prev => prev.map(edge => ({
      ...edge,
      animated: edgeIds.includes(edge.id) || edge.animated,
      style: {
        ...edge.style,
        stroke: edgeIds.includes(edge.id) ? '#10b981' : edge.style?.stroke,
        strokeWidth: edgeIds.includes(edge.id) ? 3 : 1.5
      }
    })));
  }, [setNodes, setEdges]);

  // Handle node selection
  const handleSelectNode = useCallback((nodeId: string) => {
    setSelectedNodeId(nodeId);
  }, []);

  // Hydrate Canvas Graph
  const loadGraphCanvas = useCallback(async () => {
    try {
      const data: KGCanvasResponse = await fetchPreIPOKGCanvas(symbol);
      
      // Auto-layout positions for cards in hierarchical tiers
      const positions: Record<string, { x: number; y: number }> = {
        TCCC: { x: 380, y: 40 },
        HCCOH: { x: 380, y: 160 },
        HCCH: { x: 380, y: 300 },
        OFFERING_2026: { x: 740, y: 300 },
        HCCB: { x: 120, y: 440 },
        NORTH_TERRITORY: { x: 20, y: 600 },
        WEST_TERRITORY: { x: 240, y: 600 },
        CASE_CHEQUE_BOUNCE: { x: 480, y: 560 }
      };

      const rfNodes: Node[] = data.canvas.nodes.map((n, idx) => {
        const pos = positions[n.id] || { x: 100 + (idx % 3) * 300, y: 100 + Math.floor(idx / 3) * 160 };
        return {
          id: n.id,
          type: 'fiboCard',
          position: pos,
          data: {
            ...n.data,
            id: n.id,
            onSelectNode: handleSelectNode,
            isSelected: n.id === selectedNodeId,
            isHighlighted: queryResult?.subgraph?.nodes?.includes(n.id) || false
          }
        };
      });

      const rfEdges: Edge[] = data.canvas.edges.map(e => ({
        id: e.id,
        source: e.source,
        target: e.target,
        label: e.label,
        animated: e.animated || queryResult?.subgraph?.edges?.includes(e.id),
        style: {
          stroke: e.animated ? '#f43f5e' : '#64748b',
          strokeWidth: e.animated ? 2.5 : 1.5
        },
        markerEnd: {
          type: MarkerType.ArrowClosed,
          color: e.animated ? '#f43f5e' : '#64748b'
        }
      }));

      setNodes(rfNodes);
      setEdges(rfEdges);
    } catch (err) {
      console.error('Error loading KG canvas:', err);
    }
  }, [symbol, selectedNodeId, queryResult, handleSelectNode, setNodes, setEdges]);

  // Initial load
  useEffect(() => {
    loadGraphCanvas();
    fetchPreIPOSHACLAudit(symbol).then(setShaclReport);
    fetchPreIPOValuationSimulator(symbol, pruningThreshold, territoryDiscount, channelDiscount).then(setSimResult);
    // Execute default recipe (Tier 1)
    executeRecipe(1, 'Where does the IPO proceeds go?');
  }, [symbol]);

  // Run query recipe
  const executeRecipe = async (tier: number, queryText: string) => {
    setIsLoadingQuery(true);
    setCurrentTier(tier);
    setNlQueryInput(queryText);
    try {
      const res = await queryPreIPOKG(queryText, tier, pruningThreshold);
      setQueryResult(res);
      
      // Update highlighted nodes in canvas
      const subNodes = res?.subgraph?.nodes || [];
      const subEdges = res?.subgraph?.edges || [];

      setNodes(prev => prev.map(node => ({
        ...node,
        data: {
          ...node.data,
          isHighlighted: subNodes.includes(node.id)
        }
      })));

      setEdges(prev => prev.map(edge => ({
        ...edge,
        animated: subEdges.includes(edge.id) || edge.animated,
        style: {
          ...edge.style,
          stroke: subEdges.includes(edge.id) ? '#38bdf8' : edge.style?.stroke,
          strokeWidth: subEdges.includes(edge.id) ? 3 : 1.5
        }
      })));
    } catch (err) {
      console.error('Failed to run query recipe:', err);
    } finally {
      setIsLoadingQuery(false);
    }
  };

  // Run custom NL query
  const handleRunNlQuery = async () => {
    setIsLoadingQuery(true);
    try {
      const res = await queryPreIPOKG(nlQueryInput, undefined, pruningThreshold);
      setQueryResult(res);
    } catch (err) {
      console.error('Query execution error:', err);
    } finally {
      setIsLoadingQuery(false);
    }
  };

  // Recalculate live valuation simulation
  const handleRecalculateValuation = async (newPrune: number, newTerr: number, newChan: number) => {
    setPruningThreshold(newPrune);
    setTerritoryDiscount(newTerr);
    setChannelDiscount(newChan);
    const updated = await fetchPreIPOValuationSimulator(symbol, newPrune, newTerr, newChan);
    setSimResult(updated);
  };

  // Selected node lookup
  const selectedNode = useMemo(() => {
    const found = nodes.find(n => n.id === selectedNodeId);
    return found ? (found.data as KGNodeData['data']) : null;
  }, [nodes, selectedNodeId]);

  return (
    <div className="space-y-6 animate-fade-in text-slate-100 pb-12">
      {/* Top Header & Dual-Persona Switcher */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 p-5 rounded-2xl bg-slate-900/80 border border-slate-800 shadow-xl backdrop-blur-md">
        <div>
          <div className="flex items-center gap-3">
            <div className="p-2.5 rounded-xl bg-blue-500/10 border border-blue-500/30 text-blue-400">
              <Network className="w-6 h-6" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h1 className="text-lg font-bold text-slate-100 tracking-tight">
                  Generic FIBO-Aligned Pre-IPO Financial Knowledge Graph
                </h1>
                <span className="px-2 py-0.5 rounded text-[10px] font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/30">
                  SHACL VALIDATED
                </span>
              </div>
              <p className="text-xs text-slate-400 mt-0.5">
                Closed-world SEBI ICDR compliance & multi-hop forensic contagion analysis · Single Source of Truth
              </p>
            </div>
          </div>
        </div>

        {/* Action Controls & Mode Switcher Pill */}
        <div className="flex flex-wrap items-center gap-2 self-start md:self-auto">
          {/* 84-Attribute Formula Lineage Trigger */}
          <button
            onClick={() => setIsFormulaModalOpen(true)}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-purple-500/10 border border-purple-500/30 text-purple-300 hover:bg-purple-500/20 text-xs font-semibold transition-all shadow-sm"
          >
            <Binary className="w-3.5 h-3.5 text-purple-400" />
            Formula Lineage (84 Attr)
          </button>

          {/* In-App DRHP PDF Drawer Trigger */}
          <button
            onClick={() => handleOpenPdfDrawer(18, 'Offer comprises an Offer for Sale of up to 997,500,000 Equity Shares', 'Section 1: Issue Details')}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-blue-500/10 border border-blue-500/30 text-blue-300 hover:bg-blue-500/20 text-xs font-semibold transition-all shadow-sm"
          >
            <FileText className="w-3.5 h-3.5 text-blue-400" />
            DRHP PDF Drawer (p.18)
          </button>

          {/* Mode Switcher Pill */}
          <div className="flex items-center bg-slate-950/80 p-1 rounded-xl border border-slate-800">
            <button
              onClick={() => {
                setPersonaMode('sections');
                setActiveDrilldownSectionId(null);
              }}
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold transition-all ${
                personaMode === 'sections'
                  ? 'bg-blue-600 text-white shadow-md shadow-blue-500/20'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              <BookOpen className="w-3.5 h-3.5" />
              8 SEBI Sections (Verbatim Facts)
            </button>
            <button
              onClick={() => setPersonaMode('macro')}
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold transition-all ${
                personaMode === 'macro'
                  ? 'bg-blue-600 text-white shadow-md shadow-blue-500/20'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              <Sparkles className="w-3.5 h-3.5" />
              Global Macro Graph
            </button>
            <button
              onClick={() => setPersonaMode('quant')}
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold transition-all ${
                personaMode === 'quant'
                  ? 'bg-purple-600 text-white shadow-md shadow-purple-500/20'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              <Sliders className="w-3.5 h-3.5" />
              Expert Quant Studio
            </button>
          </div>
        </div>
      </div>

      {/* View 1: 8 Statutory SEBI Sections & Verbatim Facts (Summary & Drill-Down) */}
      {personaMode === 'sections' && (
        <div className="space-y-6">
          {!activeDrilldownSectionId ? (
            <StatutorySectionSummaryGrid
              onSelectSection={(secId) => setActiveDrilldownSectionId(secId)}
              onOpenPdfPage={handleOpenPdfDrawer}
            />
          ) : (
            <StatutorySectionDrilldownView
              sectionId={activeDrilldownSectionId}
              onBackToOverview={() => setActiveDrilldownSectionId(null)}
              onOpenPdfPage={handleOpenPdfDrawer}
            />
          )}
        </div>
      )}

      {/* View 2: Global Macro Guided Discovery Canvas */}
      {personaMode === 'macro' && (
        <div className="space-y-6">
          {/* 5-Second Plain-English Verdict HUD Strip */}
          {queryResult && queryResult.verdict && (
            <div className={`p-5 rounded-2xl border shadow-xl backdrop-blur-md transition-all ${
              (queryResult.verdict.riskStatus || 'NORMAL') === 'CRITICAL_RISK'
                ? 'bg-rose-950/20 border-rose-800/40'
                : (queryResult.verdict.riskStatus || 'NORMAL') === 'HIGH_ALERT'
                ? 'bg-amber-950/20 border-amber-800/40'
                : 'bg-emerald-950/20 border-emerald-800/40'
            }`}>
              <div className="flex items-start justify-between gap-4">
                <div className="space-y-2">
                  <div className="flex items-center gap-2">
                    <span className={`px-2.5 py-0.5 rounded-full text-[10px] font-bold uppercase tracking-wider ${
                      (queryResult.verdict.riskStatus || 'NORMAL') === 'CRITICAL_RISK'
                        ? 'bg-rose-500/20 text-rose-300 border border-rose-500/30'
                        : 'bg-amber-500/20 text-amber-300 border border-amber-500/30'
                    }`}>
                      {(queryResult.verdict.riskStatus || 'NORMAL').replace('_', ' ')}
                    </span>
                    <span className="text-xs text-slate-400">5-Second Forensic Verdict:</span>
                  </div>
                  <h3 className="text-base font-bold text-slate-100">
                    {queryResult.verdict.headline || ''}
                  </h3>
                  <p className="text-xs text-slate-300 leading-relaxed max-w-4xl">
                    {queryResult.verdict.plainEnglish || (queryResult.verdict as any).whatItMeans || ''}
                  </p>
                </div>

                {/* Key Metric Snapshot Chips */}
                {queryResult.metrics && (
                  <div className="hidden lg:flex flex-col gap-2 shrink-0">
                    {Object.entries(queryResult.metrics).slice(0, 3).map(([k, v]) => (
                      <div key={k} className="px-3 py-1.5 rounded-lg bg-slate-900/80 border border-slate-800 text-right">
                        <div className="text-[10px] text-slate-400 font-mono capitalize">{k.replace(/([A-Z])/g, ' $1')}</div>
                        <div className="text-xs font-bold text-slate-100 font-mono">
                          {typeof v === 'number' && k.toLowerCase().includes('cr') ? `₹${v.toLocaleString()} Cr` : String(v)}
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>

              {/* Citations Pill Bar */}
              {queryResult.verdict.citations && queryResult.verdict.citations.length > 0 && (
                <div className="mt-4 pt-3 border-t border-slate-800/60 flex flex-wrap items-center gap-2">
                  <span className="text-[11px] text-slate-400 flex items-center gap-1 font-semibold">
                    <FileText className="w-3.5 h-3.5 text-slate-500" />
                    Verified Citations (Click to view PDF highlight):
                  </span>
                  {queryResult.verdict.citations.map((c, i) => (
                    <button
                      key={i}
                      onClick={() => {
                        const targetNode = nodes.find(n => (n.data as any).pageNumber === c.page);
                        if (targetNode) setSelectedNodeId(targetNode.id);
                        handleOpenPdfDrawer(c.page, c.quote);
                      }}
                      className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md text-[11px] bg-slate-900/90 border border-slate-700/80 hover:border-blue-500/50 text-slate-300 transition-colors group cursor-pointer"
                    >
                      <span className="text-blue-400 font-semibold group-hover:underline">{c.source} p.{c.page}</span>
                      <span className="text-[10px] text-slate-400 truncate max-w-[240px]">"{c.quote}"</span>
                      <ExternalLink className="w-3 h-3 text-blue-400 opacity-70 group-hover:opacity-100" />
                    </button>
                  ))}
                </div>
              )}
            </div>
          )}

          {/* 1-Click Forensic Query Recipe Cards */}
          <div>
            <div className="flex items-center justify-between mb-3">
              <span className="text-xs font-bold uppercase tracking-wider text-slate-400 flex items-center gap-1.5">
                <Sparkles className="w-3.5 h-3.5 text-amber-400" />
                1-Click Forensic Query Recipes
              </span>
              <span className="text-[11px] text-slate-500">Click to execute multi-hop graph traversal</span>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              {/* Recipe 1: Offer Proceeds */}
              <div
                onClick={() => executeRecipe(1, 'Where does the IPO proceeds go?')}
                className={`p-4 rounded-xl border transition-all cursor-pointer ${
                  currentTier === 1
                    ? 'bg-blue-950/30 border-blue-500 shadow-md shadow-blue-500/10'
                    : 'bg-slate-900/60 border-slate-800 hover:border-slate-700 hover:bg-slate-900/80'
                }`}
              >
                <div className="flex items-center justify-between mb-2">
                  <span className="px-2 py-0.5 rounded text-[10px] font-semibold bg-blue-500/20 text-blue-300 border border-blue-500/30">
                    Tier 1 (1-Hop)
                  </span>
                  <span className="text-[10px] text-slate-400 font-mono">100% OFS</span>
                </div>
                <h4 className="text-xs font-bold text-slate-100 mb-1">
                  Where does the IPO capital flow?
                </h4>
                <p className="text-[11px] text-slate-400">
                  Traces ₹9,975 Cr OFS route directly to Singapore HoldCo (HCCOH) with ₹0 growth capital into Indian plants.
                </p>
              </div>

              {/* Recipe 2: EBITDA Margin Sustainability */}
              <div
                onClick={() => executeRecipe(2, 'Is Q1 FY27 EBITDA margin sustainable?')}
                className={`p-4 rounded-xl border transition-all cursor-pointer ${
                  currentTier === 2
                    ? 'bg-purple-950/30 border-purple-500 shadow-md shadow-purple-500/10'
                    : 'bg-slate-900/60 border-slate-800 hover:border-slate-700 hover:bg-slate-900/80'
                }`}
              >
                <div className="flex items-center justify-between mb-2">
                  <span className="px-2 py-0.5 rounded text-[10px] font-semibold bg-purple-500/20 text-purple-300 border border-purple-500/30">
                    Tier 2 (2-Hop)
                  </span>
                  <span className="text-[10px] text-slate-400 font-mono">17.20% Margin</span>
                </div>
                <h4 className="text-xs font-bold text-slate-100 mb-1">
                  Is Q1 FY27 margin expansion real?
                </h4>
                <p className="text-[11px] text-slate-400">
                  Cross-checks +580 bps margin surge against parent raw material discounts and unhedged commodity subsidies.
                </p>
              </div>

              {/* Recipe 3: Litigation Liabilities Contagion */}
              <div
                onClick={() => executeRecipe(3, 'Are litigation liabilities quarantined?')}
                className={`p-4 rounded-xl border transition-all cursor-pointer ${
                  currentTier === 3
                    ? 'bg-rose-950/30 border-rose-500 shadow-md shadow-rose-500/10'
                    : 'bg-slate-900/60 border-slate-800 hover:border-slate-700 hover:bg-slate-900/80'
                }`}
              >
                <div className="flex items-center justify-between mb-2">
                  <span className="px-2 py-0.5 rounded text-[10px] font-semibold bg-rose-500/20 text-rose-300 border border-rose-500/30">
                    Tier 3 (3-Hop)
                  </span>
                  <span className="text-[10px] text-slate-400 font-mono">₹8,367 Cr Claims</span>
                </div>
                <h4 className="text-xs font-bold text-slate-100 mb-1">
                  Are legal risks ring-fenced from HoldCo?
                </h4>
                <p className="text-[11px] text-slate-400">
                  Traverses 1,466 cheque dishonour disputes aggregating 45.6% of Net Worth to assess contagion to public shareholders.
                </p>
              </div>
            </div>
          </div>

          {/* Full Interactive Graph Canvas */}
          <div className="relative h-[620px] rounded-2xl border border-slate-800 bg-slate-950 overflow-hidden shadow-2xl">
            <ReactFlow
              nodes={nodes}
              edges={edges}
              onNodesChange={onNodesChange}
              onEdgesChange={onEdgesChange}
              nodeTypes={nodeTypes}
              fitView
              attributionPosition="bottom-right"
              className="bg-slate-950"
            >
              <Background color="#334155" gap={20} size={1} />
              <Controls className="!bg-slate-900 !border-slate-800 !text-slate-300 !fill-slate-300" />
              <MiniMap
                className="!bg-slate-900/90 !border-slate-800 rounded-lg overflow-hidden"
                nodeColor={(n: any) => {
                  switch (n.data?.label?.toLowerCase()) {
                    case 'company': return '#3b82f6';
                    case 'subsidiary': return '#10b981';
                    case 'promoter': return '#a855f7';
                    case 'offering': return '#f59e0b';
                    case 'litigation': return '#f43f5e';
                    default: return '#64748b';
                  }
                }}
              />
            </ReactFlow>

            {/* Float Legend Overlay */}
            <div className="absolute top-4 left-4 bg-slate-900/90 backdrop-blur-md p-3 rounded-xl border border-slate-800 text-xs shadow-lg space-y-1.5 pointer-events-none">
              <div className="font-semibold text-slate-300 text-[11px] mb-1">Entity Legend</div>
              <div className="flex items-center gap-2 text-[10px] text-slate-400">
                <span className="w-2.5 h-2.5 rounded-full bg-blue-500" /> Company / HoldCo
              </div>
              <div className="flex items-center gap-2 text-[10px] text-slate-400">
                <span className="w-2.5 h-2.5 rounded-full bg-emerald-500" /> Operating Subsidiary
              </div>
              <div className="flex items-center gap-2 text-[10px] text-slate-400">
                <span className="w-2.5 h-2.5 rounded-full bg-purple-500" /> Promoter / Parent
              </div>
              <div className="flex items-center gap-2 text-[10px] text-slate-400">
                <span className="w-2.5 h-2.5 rounded-full bg-amber-500" /> 100% OFS Offering
              </div>
              <div className="flex items-center gap-2 text-[10px] text-slate-400">
                <span className="w-2.5 h-2.5 rounded-full bg-rose-500" /> Litigation Proceedings
              </div>
            </div>

            {/* Selected Node Quick Inspector Drawer */}
            {selectedNode && (
              <div className="absolute bottom-4 left-4 right-4 md:left-auto md:right-4 md:w-96 bg-slate-900/95 backdrop-blur-lg p-4 rounded-xl border border-slate-700 shadow-2xl text-xs space-y-3">
                <div className="flex items-center justify-between border-b border-slate-800 pb-2">
                  <div className="flex items-center gap-2">
                    <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-blue-500/20 text-blue-400 border border-blue-500/30">
                      {selectedNode.label?.toUpperCase()}
                    </span>
                    <span className="font-bold text-slate-100 truncate">{selectedNode.name}</span>
                  </div>
                  <button onClick={() => setSelectedNodeId(null)} className="text-slate-400 hover:text-slate-200">
                    ✕
                  </button>
                </div>

                {selectedNode.quote && (
                  <div>
                    <div className="text-[10px] text-slate-400 mb-1 font-semibold flex items-center justify-between">
                      <span className="flex items-center gap-1">
                        <FileText className="w-3 h-3 text-slate-500" />
                        DRHP Page {selectedNode.pageNumber} Extract:
                      </span>
                      {selectedNode.pageNumber && (
                        <button
                          onClick={() => handleOpenPdfDrawer(selectedNode.pageNumber!, selectedNode.quote || '')}
                          className="text-blue-400 hover:text-blue-300 text-[10px] flex items-center gap-1 font-semibold cursor-pointer"
                        >
                          View in PDF Drawer <ExternalLink className="w-2.5 h-2.5" />
                        </button>
                      )}
                    </div>
                    <p
                      onClick={() => selectedNode.pageNumber && handleOpenPdfDrawer(selectedNode.pageNumber, selectedNode.quote || '')}
                      className="text-[11px] text-slate-300 italic bg-slate-950/60 p-2.5 rounded-lg border border-slate-800 hover:border-blue-500/50 cursor-pointer transition-colors"
                    >
                      "{selectedNode.quote}"
                    </p>
                  </div>
                )}

                {selectedNode.properties && (
                  <div className="grid grid-cols-2 gap-2">
                    {Object.entries(selectedNode.properties).map(([k, v]) => (
                      <div key={k} className="p-2 rounded bg-slate-950/50 border border-slate-800/80">
                        <div className="text-[10px] text-slate-400 font-mono">{k}</div>
                        <div className="text-xs font-semibold text-slate-200">{String(v)}</div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      )}

      {/* Mode B: Expert Quant Studio */}
      {personaMode === 'quant' && (
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
          {/* Left Column: Cypher Bank, Query Console, Valuation Simulator & Bounding Box Inspector */}
          <div className="lg:col-span-5 space-y-6">
            {/* Cypher Query Bank (25 Institutional Diligence Queries) */}
            <CypherBankInspector
              onSelectCitation={handleOpenPdfDrawer}
              onHighlightSubgraph={handleHighlightSubgraph}
            />

            {/* Natural Language Query & Analytical Depth Console */}
            <div className="p-5 rounded-2xl bg-slate-900/80 border border-slate-800 shadow-xl space-y-4">
              <div className="flex items-center justify-between">
                <span className="text-xs font-bold text-slate-300 flex items-center gap-1.5 uppercase tracking-wider">
                  <Search className="w-3.5 h-3.5 text-blue-400" />
                  Forensic Query Console
                </span>
                <span className="text-[10px] text-slate-500 font-mono">NL & Cypher Router</span>
              </div>

              <div className="flex gap-2">
                <input
                  type="text"
                  value={nlQueryInput}
                  onChange={e => setNlQueryInput(e.target.value)}
                  placeholder="e.g. Where does the IPO capital flow?"
                  className="flex-1 px-3 py-2 rounded-xl bg-slate-950 border border-slate-800 text-xs text-slate-200 focus:outline-none focus:border-blue-500"
                />
                <button
                  onClick={handleRunNlQuery}
                  disabled={isLoadingQuery}
                  className="px-4 py-2 rounded-xl bg-blue-600 hover:bg-blue-500 text-white text-xs font-semibold flex items-center gap-1.5 disabled:opacity-50"
                >
                  {isLoadingQuery ? <RefreshCw className="w-3.5 h-3.5 animate-spin" /> : <ChevronRight className="w-3.5 h-3.5" />}
                  Run
                </button>
              </div>

              {/* Jev Pruning Threshold Slider */}
              <div className="space-y-1.5 pt-2 border-t border-slate-800">
                <div className="flex justify-between text-xs">
                  <span className="text-slate-400">Jev Subgraph Pruning Threshold:</span>
                  <span className="font-mono font-bold text-purple-400">{pruningThreshold.toFixed(2)}</span>
                </div>
                <input
                  type="range"
                  min="0.50"
                  max="0.95"
                  step="0.05"
                  value={pruningThreshold}
                  onChange={e => handleRecalculateValuation(parseFloat(e.target.value), territoryDiscount, channelDiscount)}
                  className="w-full accent-purple-500 cursor-pointer"
                />
                <div className="flex justify-between text-[10px] text-slate-500 font-mono">
                  <span>0.50 (Permissive)</span>
                  <span>0.65 (Calibrated)</span>
                  <span>0.95 (Strict)</span>
                </div>
              </div>
            </div>

            {/* Dynamic Valuation Simulator */}
            {simResult && (
              <div className="p-5 rounded-2xl bg-slate-900/80 border border-slate-800 shadow-xl space-y-4">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-bold text-slate-300 flex items-center gap-1.5 uppercase tracking-wider">
                    <TrendingDown className="w-3.5 h-3.5 text-emerald-400" />
                    Forensic Valuation Simulator
                  </span>
                  <span className="text-[10px] text-emerald-400 font-mono">
                    Fair Multiple: {simResult.warrantedMultiple}x EV/EBITDA
                  </span>
                </div>

                <div className="p-3 rounded-xl bg-slate-950/60 border border-slate-800 text-xs space-y-2">
                  <div className="flex justify-between">
                    <span className="text-slate-400">Benchmark Peer:</span>
                    <span className="font-semibold text-slate-200">{simResult.benchmarkPeer}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-400">Peer EV/EBITDA Multiple:</span>
                    <span className="font-mono font-bold text-slate-100">{simResult.peerMultiple.toFixed(1)}x</span>
                  </div>
                  <div className="flex justify-between text-rose-400">
                    <span>Cumulative Forensic Haircut:</span>
                    <span className="font-mono font-bold">-{simResult.totalHaircutPct.toFixed(1)}%</span>
                  </div>
                </div>

                {/* Haircut Adjustment Sliders */}
                <div className="space-y-3 text-xs">
                  <div>
                    <div className="flex justify-between text-slate-400 mb-1">
                      <span>Territory Discount (North/East Exclusivity):</span>
                      <span className="font-mono text-slate-200">{territoryDiscount}%</span>
                    </div>
                    <input
                      type="range"
                      min="0"
                      max="40"
                      step="5"
                      value={territoryDiscount}
                      onChange={e => handleRecalculateValuation(pruningThreshold, parseFloat(e.target.value), channelDiscount)}
                      className="w-full accent-blue-500"
                    />
                  </div>
                  <div>
                    <div className="flex justify-between text-slate-400 mb-1">
                      <span>Channel Discount (Litigation & Cheque Claims):</span>
                      <span className="font-mono text-slate-200">{channelDiscount}%</span>
                    </div>
                    <input
                      type="range"
                      min="0"
                      max="25"
                      step="5"
                      value={channelDiscount}
                      onChange={e => handleRecalculateValuation(pruningThreshold, territoryDiscount, parseFloat(e.target.value))}
                      className="w-full accent-rose-500"
                    />
                  </div>
                </div>

                {/* Football Field Visual Multiple Bands */}
                <div className="pt-2 border-t border-slate-800 space-y-2">
                  <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">
                    Football Field EV/EBITDA Bands
                  </span>
                  {simResult.footballField.map((band, idx) => (
                    <div key={idx} className="space-y-1">
                      <div className="flex justify-between text-[11px]">
                        <span className="text-slate-300 font-medium">{band.label}</span>
                        <span className="font-mono font-bold text-slate-100">{band.current.toFixed(1)}x</span>
                      </div>
                      <div className="h-3 w-full bg-slate-950 rounded-full overflow-hidden relative border border-slate-800">
                        <div
                          className={`h-full rounded-full ${
                            idx === 0 ? 'bg-slate-500' : idx === 1 ? 'bg-amber-500' : 'bg-emerald-500'
                          }`}
                          style={{
                            width: `${(band.current / 55.0) * 100}%`
                          }}
                        />
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* W3C PROV-O Bounding Box Inspector */}
            {selectedNode && (
              <div className="p-5 rounded-2xl bg-slate-900/80 border border-slate-800 shadow-xl space-y-3">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-bold text-slate-300 flex items-center gap-1.5 uppercase tracking-wider">
                    <Eye className="w-3.5 h-3.5 text-cyan-400" />
                    W3C PROV-O Bounding Box Inspector
                  </span>
                  <span className="text-[10px] text-cyan-400 font-mono">
                    Confidence: {selectedNode.confidence ? (selectedNode.confidence * 100).toFixed(0) + '%' : '98%'}
                  </span>
                </div>

                <div className="p-3 rounded-xl bg-slate-950 border border-slate-800 space-y-2 text-xs">
                  <div className="flex justify-between text-[11px]">
                    <span className="text-slate-400">Target Node:</span>
                    <strong className="text-slate-100">{selectedNode.name}</strong>
                  </div>
                  <div className="flex justify-between text-[11px]">
                    <span className="text-slate-400">Official Filing:</span>
                    <span className="text-blue-400 font-mono">HCCH DRHP (Dated Nov 6, 2026)</span>
                  </div>
                  <div className="flex justify-between text-[11px]">
                    <span className="text-slate-400">Physical Page Citation:</span>
                    <button
                      onClick={() => selectedNode.pageNumber && handleOpenPdfDrawer(selectedNode.pageNumber, selectedNode.quote || '')}
                      className="font-mono font-bold text-emerald-400 hover:underline flex items-center gap-1 cursor-pointer"
                    >
                      Page {selectedNode.pageNumber} <ExternalLink className="w-2.5 h-2.5" />
                    </button>
                  </div>
                  <div className="flex justify-between text-[11px]">
                    <span className="text-slate-400">Bounding Box Coordinates:</span>
                    <span className="font-mono text-slate-300">[0.12, 0.08, 0.28, 0.92]</span>
                  </div>
                </div>

                {selectedNode.quote && (
                  <div
                    onClick={() => selectedNode.pageNumber && handleOpenPdfDrawer(selectedNode.pageNumber, selectedNode.quote || '')}
                    className="p-3 rounded-xl bg-slate-950/80 border border-slate-800 text-[11px] text-slate-300 italic border-l-2 border-l-cyan-500 hover:border-cyan-400 cursor-pointer transition-all"
                  >
                    "{selectedNode.quote}"
                    <div className="mt-1 text-[9px] text-cyan-400 font-mono not-italic flex items-center gap-1">
                      <ExternalLink className="w-2.5 h-2.5" /> Click to open authentic 513p PDF page highlight
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>

          {/* Right Column: Live Network Canvas */}
          <div className="lg:col-span-7 h-[840px] rounded-2xl border border-slate-800 bg-slate-950 overflow-hidden shadow-2xl relative">
            <ReactFlow
              nodes={nodes}
              edges={edges}
              onNodesChange={onNodesChange}
              onEdgesChange={onEdgesChange}
              nodeTypes={nodeTypes}
              fitView
              attributionPosition="bottom-right"
              className="bg-slate-950"
            >
              <Background color="#1e293b" gap={18} size={1} />
              <Controls className="!bg-slate-900 !border-slate-800 !text-slate-300" />
              <MiniMap className="!bg-slate-900/90 !border-slate-800" />
            </ReactFlow>

            {/* Statutory SHACL Gate Badge */}
            {shaclReport && (
              <div className="absolute top-4 right-4 bg-slate-900/90 backdrop-blur-md px-3.5 py-2 rounded-xl border border-slate-800 text-xs shadow-lg flex items-center gap-2">
                <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                <div>
                  <div className="font-bold text-slate-200 text-[11px]">Closed-World SHACL Gate</div>
                  <div className="text-[10px] text-emerald-400">
                    {shaclReport.conforms ? 'CONFORMS (0 Violations)' : `${shaclReport.violationCount} Violations`}
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Slide-Over In-App PDF Bounding Box Viewer Drawer */}
      <PdfBoundingBoxDrawer
        isOpen={isPdfDrawerOpen}
        onClose={() => setIsPdfDrawerOpen(false)}
        pageNumber={pdfDrawerPage}
        highlightQuote={pdfDrawerQuote}
        statutoryClause={pdfDrawerClause}
        symbol={symbol}
      />

      {/* Mathematical Lineage & 84 Attributes DAG Modal */}
      <FormulaLineageModal
        isOpen={isFormulaModalOpen}
        onClose={() => setIsFormulaModalOpen(false)}
        onSelectCitation={handleOpenPdfDrawer}
      />
    </div>
  );
};

export default KnowledgeGraphStudioVault;
