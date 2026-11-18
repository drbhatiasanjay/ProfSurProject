import React, { useState, useEffect } from 'react';
import {
  Database,
  Play,
  FileText,
  ShieldCheck,
  AlertTriangle,
  ChevronRight,
  Filter,
  CheckCircle2,
  RefreshCw,
  ExternalLink,
  Code2
} from 'lucide-react';
import {
  fetchCypherBank,
  executeCypherQuery,
  CypherBankResponse,
  CypherQueryItem,
  CypherExecResult
} from '../../../services/dataService';

interface CypherBankInspectorProps {
  onSelectCitation: (page: number, quote: string, statutoryClause?: string) => void;
  onHighlightSubgraph?: (nodeIds: string[], edgeIds: string[]) => void;
}

export const CypherBankInspector: React.FC<CypherBankInspectorProps> = ({
  onSelectCitation,
  onHighlightSubgraph
}) => {
  const [bankData, setBankData] = useState<CypherBankResponse | null>(null);
  const [selectedCategory, setSelectedCategory] = useState<string>('ALL');
  const [selectedQueryId, setSelectedQueryId] = useState<string>('Q01_PROCEEDS_FLOW');
  const [activeQuery, setActiveQuery] = useState<CypherQueryItem | null>(null);
  const [execResult, setExecResult] = useState<CypherExecResult | null>(null);
  const [isExecuting, setIsExecuting] = useState<boolean>(false);
  const [isLoadingBank, setIsLoadingBank] = useState<boolean>(false);

  useEffect(() => {
    setIsLoadingBank(true);
    fetchCypherBank()
      .then(data => {
        setBankData(data);
        if (data.queries.length > 0) {
          const first = data.queries[0];
          setSelectedQueryId(first.queryId);
          setActiveQuery(first);
        }
      })
      .finally(() => setIsLoadingBank(false));
  }, []);

  const handleSelectQuery = (q: CypherQueryItem) => {
    setSelectedQueryId(q.queryId);
    setActiveQuery(q);
    setExecResult(null);
  };

  const handleRunQuery = async () => {
    if (!activeQuery) return;
    setIsExecuting(true);
    try {
      const res = await executeCypherQuery(activeQuery.queryId);
      setExecResult(res);
      if (onHighlightSubgraph && res.subgraph) {
        onHighlightSubgraph(res.subgraph.nodes || [], res.subgraph.edges || []);
      }
    } catch (err) {
      console.error('Failed to run Cypher query:', err);
    } finally {
      setIsExecuting(false);
    }
  };

  const filteredQueries = bankData
    ? selectedCategory === 'ALL'
      ? bankData.queries
      : bankData.queries.filter(q => q.category === selectedCategory)
    : [];

  return (
    <div className="p-5 rounded-2xl bg-slate-900/80 border border-slate-800 shadow-xl space-y-4 text-slate-100">
      {/* Header */}
      <div className="flex items-center justify-between border-b border-slate-800 pb-3">
        <div className="flex items-center gap-2.5">
          <div className="p-2 rounded-lg bg-emerald-500/10 border border-emerald-500/30 text-emerald-400">
            <Database className="w-4 h-4" />
          </div>
          <div>
            <h3 className="text-xs font-bold text-slate-200 uppercase tracking-wider flex items-center gap-2">
              SEBI ICDR Cypher Query Bank (25 Institutional Queries)
            </h3>
            <p className="text-[11px] text-slate-400">
              Parametric Graph Traversal across 5 Forensic Categories on 513p DRHP
            </p>
          </div>
        </div>
        <span className="text-[10px] px-2 py-0.5 rounded bg-slate-800 text-slate-300 font-mono">
          DuckDB Graph Engine
        </span>
      </div>

      {/* Category Pills Filter */}
      {bankData && bankData.categories && (
        <div className="flex flex-wrap gap-1.5 pt-1">
          <button
            onClick={() => setSelectedCategory('ALL')}
            className={`px-2.5 py-1 rounded-lg text-[11px] font-semibold transition-all ${
              selectedCategory === 'ALL'
                ? 'bg-blue-600 text-white'
                : 'bg-slate-950/70 border border-slate-800 text-slate-400 hover:text-slate-200'
            }`}
          >
            All ({bankData.queries.length})
          </button>
          {bankData.categories.map(cat => (
            <button
              key={cat}
              onClick={() => setSelectedCategory(cat)}
              className={`px-2.5 py-1 rounded-lg text-[11px] font-semibold transition-all ${
                selectedCategory === cat
                  ? 'bg-blue-600 text-white'
                  : 'bg-slate-950/70 border border-slate-800 text-slate-400 hover:text-slate-200'
              }`}
            >
              {cat}
            </button>
          ))}
        </div>
      )}

      {/* Query Selector Dropdown & Execution Button */}
      <div className="grid grid-cols-1 md:grid-cols-12 gap-3 pt-1">
        <div className="md:col-span-8">
          <label className="text-[10px] text-slate-400 font-mono mb-1 block">
            Select Diligence Query ({filteredQueries.length} Available):
          </label>
          <select
            value={selectedQueryId}
            onChange={e => {
              const found = bankData?.queries.find(q => q.queryId === e.target.value);
              if (found) handleSelectQuery(found);
            }}
            className="w-full px-3 py-2 rounded-xl bg-slate-950 border border-slate-800 text-xs text-slate-200 focus:outline-none focus:border-blue-500 font-medium"
          >
            {filteredQueries.map(q => (
              <option key={q.queryId} value={q.queryId}>
                [{q.queryId}] {q.title}
              </option>
            ))}
          </select>
        </div>

        <div className="md:col-span-4 flex items-end">
          <button
            onClick={handleRunQuery}
            disabled={isExecuting || !activeQuery}
            className="w-full py-2 px-4 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-bold flex items-center justify-center gap-2 shadow-md shadow-emerald-600/20 disabled:opacity-50 transition-all"
          >
            {isExecuting ? (
              <RefreshCw className="w-3.5 h-3.5 animate-spin" />
            ) : (
              <Play className="w-3.5 h-3.5 fill-current" />
            )}
            Execute Cypher
          </button>
        </div>
      </div>

      {/* Active Query Details & Cypher Syntax Preview */}
      {activeQuery && (
        <div className="p-3.5 rounded-xl bg-slate-950/80 border border-slate-800 space-y-2.5">
          <div className="flex items-center justify-between text-[11px]">
            <span className="text-slate-400">
              Statutory Chapter:{' '}
              <strong className="text-slate-200">{activeQuery.targetStatutorySection}</strong>
            </span>
            <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-slate-900 border border-slate-800 text-purple-400">
              {activeQuery.expectedHops}-Hop Traversal
            </span>
          </div>
          <p className="text-xs text-slate-300">{activeQuery.description}</p>

          <div className="pt-2 border-t border-slate-800/80">
            <div className="flex items-center justify-between text-[10px] text-slate-400 font-mono mb-1">
              <span className="flex items-center gap-1">
                <Code2 className="w-3 h-3 text-emerald-400" />
                Cypher Template Code:
              </span>
              <span>DuckDB Parquet/Relational Graph</span>
            </div>
            <pre className="p-2.5 rounded-lg bg-slate-950 border border-slate-800 text-[11px] font-mono text-emerald-400 overflow-x-auto">
              {activeQuery.cypherCode}
            </pre>
          </div>
        </div>
      )}

      {/* Execution Results View */}
      {execResult && (
        <div className="p-4 rounded-xl bg-slate-950/90 border border-emerald-500/40 space-y-3 animate-fade-in shadow-xl">
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold text-emerald-400 flex items-center gap-1.5 uppercase tracking-wider">
              <CheckCircle2 className="w-3.5 h-3.5" />
              Execution Verdict & Forensic Findings
            </span>
            <span className="text-[10px] px-2 py-0.5 rounded font-mono font-bold uppercase bg-amber-500/20 text-amber-300 border border-amber-500/30">
              {execResult.severity}
            </span>
          </div>

          <div className="p-3 rounded-lg bg-slate-900/80 border border-slate-800 text-xs text-slate-200 font-medium leading-relaxed">
            {execResult.verdict}
          </div>

          {/* Structured Result Table */}
          {execResult.table && execResult.table.length > 0 && (
            <div className="overflow-x-auto rounded-lg border border-slate-800">
              <table className="w-full text-left text-xs">
                <thead className="bg-slate-900 text-[10px] text-slate-400 font-mono uppercase">
                  <tr>
                    {Object.keys(execResult.table[0]).map(col => (
                      <th key={col} className="p-2 border-b border-slate-800">
                        {col}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800 text-slate-200 font-mono text-[11px]">
                  {execResult.table.map((row, idx) => (
                    <tr key={idx} className="hover:bg-slate-900/40">
                      {Object.values(row).map((val: any, cidx) => (
                        <td key={cidx} className="p-2">
                          {typeof val === 'number'
                            ? val.toLocaleString(undefined, { maximumFractionDigits: 2 })
                            : String(val)}
                        </td>
                      ))}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}

          {/* Citation Button Triggering In-App PDF Drawer */}
          {execResult.citations && execResult.citations.length > 0 && (
            <div className="pt-2 border-t border-slate-800 flex flex-wrap items-center gap-2">
              <span className="text-[11px] text-slate-400 font-semibold flex items-center gap-1">
                <FileText className="w-3 h-3 text-slate-500" />
                Verified Citations:
              </span>
              {execResult.citations.map((c, i) => (
                <button
                  key={i}
                  onClick={() => onSelectCitation(c.page, c.quote, execResult.statutorySection)}
                  className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs bg-slate-900 border border-blue-500/40 hover:border-blue-400 text-blue-300 font-medium transition-all group"
                >
                  <span className="font-bold text-white group-hover:text-blue-200">
                    {c.source || `DRHP p. ${c.page}`}
                  </span>
                  <span className="text-[10px] text-slate-400 truncate max-w-[200px]">
                    "{c.quote}"
                  </span>
                  <ExternalLink className="w-3 h-3 text-blue-400" />
                </button>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
};
