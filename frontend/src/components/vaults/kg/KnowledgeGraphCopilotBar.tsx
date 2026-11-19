import React, { useState, useEffect } from 'react';
import {
  queryGraphRAGCopilot,
  fetchGraphRAGSuggestedPrompts,
  GraphRAGResult,
  SuggestedPrompt
} from '../../../services/dataService';

interface KnowledgeGraphCopilotBarProps {
  symbol?: string;
  onInspectCitation?: (page: number, boundingBox: number[], fact: any) => void;
  onHighlightPath?: (nodeIds: string[], edgeIds: string[]) => void;
  onTriggerShock?: (factId: string) => void;
}

export const KnowledgeGraphCopilotBar: React.FC<KnowledgeGraphCopilotBarProps> = ({
  symbol = 'HCCH',
  onInspectCitation,
  onHighlightPath,
  onTriggerShock
}) => {
  const [persona, setPersona] = useState<'novice' | 'advanced'>('novice');
  const [query, setQuery] = useState('');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<GraphRAGResult | null>(null);
  const [suggestedPrompts, setSuggestedPrompts] = useState<{ novice: SuggestedPrompt[]; advanced: SuggestedPrompt[] }>({
    novice: [],
    advanced: []
  });
  const [showCypher, setShowCypher] = useState(false);

  useEffect(() => {
    fetchGraphRAGSuggestedPrompts(symbol).then(data => {
      if (data && (data.novice?.length || data.advanced?.length)) {
        setSuggestedPrompts(data);
      }
    });
  }, [symbol]);

  const handleExecute = async (qText: string) => {
    const textToRun = qText || query;
    if (!textToRun.trim()) return;

    setLoading(true);
    try {
      const data = await queryGraphRAGCopilot(textToRun, symbol);
      setResult(data);
      if (onHighlightPath && data.matched_node_ids?.length) {
        onHighlightPath(data.matched_node_ids, data.matched_edge_ids || []);
      }
    } catch (err) {
      console.error('GraphRAG execution failed:', err);
    } finally {
      setLoading(false);
    }
  };

  const activePrompts = persona === 'novice' ? suggestedPrompts.novice : suggestedPrompts.advanced;

  return (
    <div className="bg-slate-900/95 border border-slate-700/80 rounded-xl shadow-2xl backdrop-blur-md overflow-hidden mb-6 transition-all duration-300">
      {/* Top Bar with Persona Selector & Grounding Tag */}
      <div className="px-5 py-3 border-b border-slate-800 flex flex-wrap items-center justify-between gap-3 bg-gradient-to-r from-slate-900 via-indigo-950/30 to-slate-900">
        <div className="flex items-center space-x-3">
          <div className="w-8 h-8 rounded-lg bg-indigo-500/20 border border-indigo-400/30 flex items-center justify-center text-indigo-400 shadow-inner">
            <span className="text-base">🤖</span>
          </div>
          <div>
            <div className="flex items-center space-x-2">
              <span className="text-xs font-bold text-white tracking-wide uppercase">GraphRAG Cypher Copilot</span>
              <span className="text-[10px] px-2 py-0.5 rounded-full bg-emerald-500/20 text-emerald-400 border border-emerald-500/30 font-mono">
                GROUNDED · 513p DRHP
              </span>
            </div>
            <p className="text-[11px] text-slate-400">Natural Language Multi-Hop Cypher Traversal & Verbatim Citation Jumps</p>
          </div>
        </div>

        {/* Dual Persona Switcher */}
        <div className="flex items-center bg-slate-950 p-1 rounded-lg border border-slate-800">
          <button
            onClick={() => setPersona('novice')}
            className={`px-3 py-1 rounded text-xs font-semibold transition-all ${
              persona === 'novice'
                ? 'bg-indigo-600 text-white shadow-sm'
                : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            🌱 Novice (Retail)
          </button>
          <button
            onClick={() => setPersona('advanced')}
            className={`px-3 py-1 rounded text-xs font-semibold transition-all ${
              persona === 'advanced'
                ? 'bg-indigo-600 text-white shadow-sm'
                : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            ⚡ Advanced (CRO / IC)
          </button>
        </div>
      </div>

      {/* Suggested Prompt Chips */}
      <div className="px-5 py-2.5 bg-slate-950/60 border-b border-slate-800/80 flex items-center space-x-2 overflow-x-auto no-scrollbar">
        <span className="text-[11px] text-slate-400 font-semibold uppercase tracking-wider flex-shrink-0">
          Suggested:
        </span>
        {activePrompts.map((p, idx) => (
          <button
            key={idx}
            onClick={() => {
              setQuery(p.label);
              handleExecute(p.label);
            }}
            className="flex-shrink-0 text-xs px-2.5 py-1 rounded-full bg-slate-800/80 hover:bg-indigo-900/40 text-slate-300 hover:text-indigo-200 border border-slate-700 hover:border-indigo-500/50 transition-all flex items-center space-x-1.5"
          >
            <span>{p.icon}</span>
            <span>{p.label}</span>
            <span className="text-[10px] px-1.5 py-0.2 rounded bg-slate-700/50 text-slate-400 font-mono">
              {p.badge}
            </span>
          </button>
        ))}
      </div>

      {/* Search Input Bar */}
      <div className="p-4 bg-slate-900/60 flex items-center space-x-3">
        <div className="relative flex-1">
          <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none text-slate-500">
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
            </svg>
          </div>
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && handleExecute(query)}
            placeholder={
              persona === 'novice'
                ? 'Ask anything: "What happens if CESTAT tax dispute is lost?", "Who gets the OFS proceeds?"...'
                : 'Advanced Cypher query: "Trace multi-hop contagion path from CESTAT litigation to Net Worth", "Audit Ind AS 116 headroom"...'
            }
            className="w-full pl-10 pr-10 py-2.5 bg-slate-950 border border-slate-700 rounded-lg text-sm text-slate-100 placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-indigo-500/50 focus:border-indigo-500 transition-all"
          />
          {query && (
            <button
              onClick={() => { setQuery(''); setResult(null); }}
              className="absolute inset-y-0 right-0 pr-3 flex items-center text-slate-500 hover:text-slate-300"
            >
              ✕
            </button>
          )}
        </div>

        <button
          onClick={() => handleExecute(query)}
          disabled={loading || !query.trim()}
          className="px-5 py-2.5 rounded-lg bg-indigo-600 hover:bg-indigo-500 disabled:bg-slate-800 disabled:text-slate-600 text-white font-medium text-xs tracking-wide shadow-lg shadow-indigo-600/20 hover:shadow-indigo-600/40 transition-all flex items-center space-x-2"
        >
          {loading ? (
            <>
              <div className="w-3.5 h-3.5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
              <span>Traversing Graph...</span>
            </>
          ) : (
            <>
              <span>Execute Cypher</span>
              <span>⚡</span>
            </>
          )}
        </button>
      </div>

      {/* Structured GraphRAG Response Card */}
      {result && (
        <div className="border-t border-slate-800 bg-slate-950/80 p-5 space-y-4 animate-in fade-in duration-300">
          {/* Result Header Badge Strip */}
          <div className="flex flex-wrap items-center justify-between gap-2 border-b border-slate-800/80 pb-3">
            <div className="flex items-center space-x-2">
              <span className="text-xs font-bold text-slate-300">Intent:</span>
              <span className="text-xs font-mono font-semibold px-2 py-0.5 rounded bg-indigo-950 text-indigo-300 border border-indigo-800">
                {result.intent}
              </span>
              <span className={`text-[10px] font-bold px-2 py-0.5 rounded uppercase font-mono ${
                result.severity === 'CRITICAL' ? 'bg-rose-500/20 text-rose-400 border border-rose-500/30' :
                result.severity === 'WARNING' ? 'bg-amber-500/20 text-amber-400 border border-amber-500/30' :
                'bg-blue-500/20 text-blue-400 border border-blue-500/30'
              }`}>
                {result.severity}
              </span>
            </div>

            <div className="flex items-center space-x-3 text-xs">
              <span className="text-slate-400 font-mono">
                PROV-O Score: <strong className="text-emerald-400">{(result.provenance_score * 100).toFixed(1)}%</strong>
              </span>
              {result.template_id && (
                <span className="text-slate-500 font-mono">Template: {result.template_id}</span>
              )}
            </div>
          </div>

          {/* Institutional Markdown Briefing */}
          <div className="prose prose-invert max-w-none text-xs text-slate-300 space-y-2 leading-relaxed bg-slate-900/60 p-4 rounded-lg border border-slate-800">
            <div className="whitespace-pre-line font-sans">{result.summary_markdown}</div>
          </div>

          {/* Verbatim Fact Interactive Action Strip */}
          {result.primary_fact && (
            <div className="flex flex-wrap items-center justify-between gap-3 p-3 bg-slate-900 border border-indigo-900/40 rounded-lg">
              <div className="flex items-center space-x-3">
                <span className="text-xl">📑</span>
                <div>
                  <div className="text-xs font-bold text-slate-200">
                    {result.primary_fact.entity_name}
                  </div>
                  <div className="text-[11px] text-slate-400">
                    Physical Page: <strong className="text-amber-400 font-mono">p. {result.target_page}</strong> · Section: {result.primary_fact.statutory_section_id}
                  </div>
                </div>
              </div>

              <div className="flex items-center space-x-2">
                {result.target_page && onInspectCitation && (
                  <button
                    onClick={() => onInspectCitation(result.target_page!, result.bounding_box || [0.1, 0.1, 0.5, 0.9], result.primary_fact)}
                    className="px-3 py-1.5 rounded bg-amber-500/20 hover:bg-amber-500/30 text-amber-300 border border-amber-500/40 text-xs font-semibold transition-all flex items-center space-x-1"
                  >
                    <span>📄 Jump to PDF (p. {result.target_page})</span>
                  </button>
                )}

                {result.matched_node_ids?.length > 0 && onHighlightPath && (
                  <button
                    onClick={() => onHighlightPath(result.matched_node_ids, result.matched_edge_ids)}
                    className="px-3 py-1.5 rounded bg-indigo-500/20 hover:bg-indigo-500/30 text-indigo-300 border border-indigo-500/40 text-xs font-semibold transition-all flex items-center space-x-1"
                  >
                    <span>🕸️ Highlight Path ({result.matched_node_ids.length} Nodes)</span>
                  </button>
                )}

                {result.can_simulate_shock && onTriggerShock && (
                  <button
                    onClick={() => onTriggerShock(result.shock_fact_id || result.primary_fact?.fact_id || '')}
                    className="px-3 py-1.5 rounded bg-rose-500/20 hover:bg-rose-500/30 text-rose-300 border border-rose-500/40 text-xs font-semibold transition-all flex items-center space-x-1"
                  >
                    <span>⚡ Stress-Test Shock</span>
                  </button>
                )}
              </div>
            </div>
          )}

          {/* Expandable Executed Cypher Code Drawer */}
          <div className="border border-slate-800 rounded-lg overflow-hidden bg-slate-950">
            <button
              onClick={() => setShowCypher(!showCypher)}
              className="w-full px-4 py-2 text-left text-xs text-slate-400 hover:text-slate-200 flex items-center justify-between bg-slate-900/40 transition-colors"
            >
              <span className="font-mono flex items-center space-x-2">
                <span>💻</span>
                <span>Executed Grounded Cypher Statement</span>
              </span>
              <span>{showCypher ? '▲ Collapse' : '▼ Expand'}</span>
            </button>
            {showCypher && (
              <pre className="p-4 text-xs font-mono text-emerald-300 bg-slate-950 overflow-x-auto border-t border-slate-800">
                {result.cypher_query}
              </pre>
            )}
          </div>

          {/* Follow-up Question Chips */}
          {result.suggested_followups?.length > 0 && (
            <div className="space-y-1.5 pt-2">
              <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider">
                Recommended Follow-Up Diligence:
              </span>
              <div className="flex flex-wrap gap-2">
                {result.suggested_followups.map((fText, fIdx) => (
                  <button
                    key={fIdx}
                    onClick={() => {
                      setQuery(fText);
                      handleExecute(fText);
                    }}
                    className="text-xs px-2.5 py-1 rounded bg-slate-900 hover:bg-slate-800 text-slate-300 hover:text-indigo-300 border border-slate-800 hover:border-indigo-600/50 transition-all text-left"
                  >
                    → {fText}
                  </button>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};
