import React, { useState, useEffect, useCallback } from 'react';
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
  ArrowLeft,
  FileText,
  ShieldCheck,
  AlertTriangle,
  ExternalLink,
  ChevronRight,
  TrendingDown,
  Info,
  CheckCircle2,
  RefreshCw,
  Eye,
  BookOpen,
  Filter
} from 'lucide-react';
import {
  fetchSectionDrilldown,
  SectionDrilldownResponse,
  VerbatimFactItem
} from '../../../services/dataService';

// Custom Custom Node Component for Scoped Subgraph Entities
const DrilldownCardNode: React.FC<any> = ({ data }) => {
  const isHub = data.label === 'SECTION_HUB';
  const isChapter = data.label === 'SUB_CHAPTER';
  const isCritical = data.statutorySeverity === 'CRITICAL_RISK';
  const isAlert = data.statutorySeverity === 'HIGH_ALERT';

  return (
    <div
      onClick={() => data.onSelectNode && data.onSelectNode(data.id)}
      className={`relative w-72 rounded-xl p-3.5 backdrop-blur-md transition-all duration-200 cursor-pointer text-left shadow-lg ${
        isHub
          ? 'bg-blue-950/90 border-2 border-blue-500 ring-2 ring-blue-500/20'
          : isChapter
          ? 'bg-purple-950/80 border border-purple-500/50'
          : isCritical
          ? 'bg-rose-950/85 border border-rose-500/60 ring-2 ring-rose-500/20'
          : isAlert
          ? 'bg-amber-950/85 border border-amber-500/60'
          : 'bg-slate-900/90 border border-slate-700/80'
      }`}
    >
      <Handle type="target" position={Position.Top} className="!bg-slate-400 !w-2 !h-2" />

      {/* Header Badge */}
      <div className="flex items-center justify-between mb-2">
        <span className={`px-2 py-0.5 rounded-full text-[9px] font-bold uppercase tracking-wider ${
          isHub
            ? 'bg-blue-500/20 text-blue-300 border border-blue-500/40'
            : isChapter
            ? 'bg-purple-500/20 text-purple-300 border border-purple-500/40'
            : isCritical
            ? 'bg-rose-500/20 text-rose-300 border border-rose-500/40'
            : 'bg-slate-800 text-slate-300'
        }`}>
          {data.label || 'ENTITY'}
        </span>
        {data.pageNumber && (
          <span className="text-[10px] text-slate-400 flex items-center gap-1 font-mono">
            <FileText className="w-2.5 h-2.5 text-slate-500" />
            p.{data.pageNumber}
          </span>
        )}
      </div>

      <div className="font-bold text-xs text-slate-100 line-clamp-1 mb-1">
        {data.name}
      </div>

      {data.properties && (
        <div className="flex flex-wrap gap-1 mt-2">
          {Object.entries(data.properties).slice(0, 3).map(([k, v]) => (
            <span key={k} className="text-[9px] px-1.5 py-0.5 rounded bg-slate-950/60 text-slate-300 font-mono">
              {k}: <strong className="text-slate-100">{String(v)}</strong>
            </span>
          ))}
        </div>
      )}

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
  fiboCard: DrilldownCardNode
};

interface StatutorySectionDrilldownViewProps {
  sectionId: string;
  onBackToOverview: () => void;
  onOpenPdfPage: (page: number, quote: string, clause?: string) => void;
}

export const StatutorySectionDrilldownView: React.FC<StatutorySectionDrilldownViewProps> = ({
  sectionId,
  onBackToOverview,
  onOpenPdfPage
}) => {
  const [data, setData] = useState<SectionDrilldownResponse | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [selectedFact, setSelectedFact] = useState<VerbatimFactItem | null>(null);

  const [nodes, setNodes, onNodesChange] = useNodesState<Node>([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState<Edge>([]);

  const dataRef = React.useRef<SectionDrilldownResponse | null>(null);

  const handleSelectNode = useCallback((nodeId: string) => {
    if (dataRef.current?.facts) {
      const found = dataRef.current.facts.find(f => f.entity_id === nodeId);
      if (found) setSelectedFact(found);
    }
  }, []);

  useEffect(() => {
    setIsLoading(true);
    fetchSectionDrilldown(sectionId)
      .then(res => {
        dataRef.current = res;
        setData(res);
        if (res.facts && res.facts.length > 0) {
          setSelectedFact(res.facts[0]);
        }

        const rfNodes: Node[] = (res.canvas?.nodes || []).map(n => ({
          ...n,
          type: 'fiboCard',
          data: {
            ...n.data,
            onSelectNode: handleSelectNode
          }
        }));

        const rfEdges: Edge[] = (res.canvas?.edges || []).map(e => ({
          ...e,
          markerEnd: {
            type: MarkerType.ArrowClosed,
            color: e.style?.stroke || '#64748b'
          }
        }));

        setNodes(rfNodes);
        setEdges(rfEdges);
      })
      .catch(err => console.error('Failed to load section drilldown:', err))
      .finally(() => setIsLoading(false));
  }, [sectionId, handleSelectNode, setNodes, setEdges]);

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-24 text-xs text-slate-400 gap-2">
        <RefreshCw className="w-4 h-4 animate-spin text-blue-400" />
        Loading scoped statutory section sub-graph...
      </div>
    );
  }

  if (!data) return null;

  return (
    <div className="space-y-5 animate-fade-in text-slate-100">
      {/* Breadcrumb Header Bar */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-3 p-4 rounded-xl bg-slate-900/80 border border-slate-800 shadow-lg">
        <div className="flex items-center gap-3">
          <button
            onClick={onBackToOverview}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-xs font-semibold text-slate-200 transition-colors"
          >
            <ArrowLeft className="w-3.5 h-3.5" />
            Back to All 8 Sections
          </button>
          <div>
            <div className="flex items-center gap-2">
              <h2 className="text-sm font-bold text-slate-100">
                Section {data.sectionNumber}: {data.title}
              </h2>
              <span className="px-2 py-0.5 rounded text-[10px] font-mono font-semibold bg-blue-500/10 text-blue-400 border border-blue-500/30">
                {data.facts.length} Verbatim Disclosures
              </span>
            </div>
            <p className="text-[11px] text-slate-400 mt-0.5 font-mono">
              {data.sebiSchedule}
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <span className="text-[11px] text-slate-400">Drill-Down Canvas Scoped to Section Chapters</span>
        </div>
      </div>

      {/* Main Split Grid: Left Verbatim Facts Ledger & Right Scoped Graph Canvas */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-5">
        {/* Left Column: Verbatim Qualitative Facts Ledger */}
        <div className="lg:col-span-5 space-y-3.5 max-h-[760px] overflow-y-auto pr-1">
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold text-slate-300 uppercase tracking-wider flex items-center gap-1.5">
              <FileText className="w-3.5 h-3.5 text-emerald-400" />
              Statutory Verbatim Facts ({data.facts.length})
            </span>
            <span className="text-[10px] text-slate-500 font-mono">Click to inspect in PDF Drawer</span>
          </div>

          {data.facts.map(fact => {
            const isSelected = selectedFact?.fact_id === fact.fact_id;
            const isCritical = fact.statutory_severity === 'CRITICAL_RISK';
            const isAlert = fact.statutory_severity === 'HIGH_ALERT';

            return (
              <div
                key={fact.fact_id}
                onClick={() => setSelectedFact(fact)}
                className={`p-4 rounded-xl border transition-all cursor-pointer space-y-2.5 ${
                  isSelected
                    ? 'bg-blue-950/40 border-blue-500 shadow-md ring-1 ring-blue-500/30'
                    : isCritical
                    ? 'bg-rose-950/20 border-rose-900/40 hover:border-rose-700/60'
                    : isAlert
                    ? 'bg-amber-950/20 border-amber-900/40 hover:border-amber-700/60'
                    : 'bg-slate-900/60 border-slate-800 hover:border-slate-700'
                }`}
              >
                {/* Header Row */}
                <div className="flex items-center justify-between text-xs">
                  <div className="flex items-center gap-2">
                    <span className={`px-2 py-0.5 rounded text-[9px] font-mono font-bold uppercase ${
                      isCritical
                        ? 'bg-rose-500/20 text-rose-300 border border-rose-500/30'
                        : isAlert
                        ? 'bg-amber-500/20 text-amber-300 border border-amber-500/30'
                        : 'bg-slate-800 text-slate-300'
                    }`}>
                      {fact.statutory_severity.replace('_', ' ')}
                    </span>
                    <strong className="text-slate-200 text-xs truncate max-w-[180px]">{fact.entity_name}</strong>
                  </div>

                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      onOpenPdfPage(fact.physical_page, fact.verbatim_quote, data.title);
                    }}
                    className="inline-flex items-center gap-1 px-2 py-0.5 rounded bg-blue-500/10 hover:bg-blue-500/20 text-blue-300 text-[10px] font-mono font-bold border border-blue-500/30 transition-colors"
                  >
                    <span>p.{fact.physical_page}</span>
                    <ExternalLink className="w-2.5 h-2.5" />
                  </button>
                </div>

                {/* Verbatim DRHP Quote */}
                <p
                  onClick={() => onOpenPdfPage(fact.physical_page, fact.verbatim_quote, data.title)}
                  className="text-[11px] text-slate-300 italic bg-slate-950/60 p-2.5 rounded-lg border border-slate-800/80 hover:border-blue-500/50 transition-colors leading-relaxed"
                >
                  "{fact.verbatim_quote}"
                </p>

                {/* Plain-English Takeaway */}
                <div className="text-[11px] text-slate-400 bg-slate-900/80 p-2 rounded-lg border border-slate-800 flex items-start gap-1.5">
                  <Info className="w-3.5 h-3.5 text-blue-400 shrink-0 mt-0.5" />
                  <span>{fact.plain_english_takeaway}</span>
                </div>

                {/* Exposure Metric & Contagion Flag */}
                <div className="flex items-center justify-between pt-1 text-[10px] font-mono text-slate-400">
                  {fact.quant_impact_cr !== null ? (
                    <span>
                      Quantified Exposure: <strong className="text-rose-400">₹{fact.quant_impact_cr.toLocaleString()} Cr</strong>
                    </span>
                  ) : (
                    <span>Governance Disclosures</span>
                  )}
                  <span className={fact.contagion_to_holdco ? 'text-rose-400 font-bold' : 'text-emerald-400'}>
                    {fact.contagion_to_holdco ? '⚠ Contagion Risk: HIGH' : '✓ Quarantined'}
                  </span>
                </div>
              </div>
            );
          })}
        </div>

        {/* Right Column: Scoped ReactFlow Canvas */}
        <div className="lg:col-span-7 h-[760px] rounded-2xl border border-slate-800 bg-slate-950 overflow-hidden shadow-2xl relative">
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
            <Background color="#1e293b" gap={20} size={1} />
            <Controls className="!bg-slate-900 !border-slate-800 !text-slate-300" />
            <MiniMap className="!bg-slate-900/90 !border-slate-800" />
          </ReactFlow>

          {/* Canvas Floating Overlay Legend */}
          <div className="absolute top-4 left-4 bg-slate-900/90 backdrop-blur-md p-3 rounded-xl border border-slate-800 text-xs shadow-lg space-y-1.5 pointer-events-none">
            <div className="font-semibold text-slate-300 text-[11px] mb-1">Section Canvas Legend</div>
            <div className="flex items-center gap-2 text-[10px] text-slate-400">
              <span className="w-2.5 h-2.5 rounded-full bg-blue-500" /> Statutory Section Hub
            </div>
            <div className="flex items-center gap-2 text-[10px] text-slate-400">
              <span className="w-2.5 h-2.5 rounded-full bg-purple-500" /> Statutory Sub-Chapter
            </div>
            <div className="flex items-center gap-2 text-[10px] text-slate-400">
              <span className="w-2.5 h-2.5 rounded-full bg-rose-500" /> Critical Risk Entity
            </div>
            <div className="flex items-center gap-2 text-[10px] text-slate-400">
              <span className="w-2.5 h-2.5 rounded-full bg-slate-500" /> Granular Fact Node
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
