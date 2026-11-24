import React, { useState, useEffect } from 'react';
import {
  Search,
  Download,
  Filter,
  SlidersHorizontal,
  ChevronLeft,
  ChevronRight,
  ChevronDown,
  ArrowUpDown,
  ArrowUp,
  ArrowDown,
  Info,
  Maximize2,
  Minimize2,
  ExternalLink,
  Table as TableIcon,
  Database,
  Building,
} from 'lucide-react';

interface ExplorerRow {
  company_name: string;
  nse_symbol: string;
  industry_group: string;
  year: number | null;
  life_stage: string;
  leverage: number | null;
  profitability: number | null;
  tangibility: number | null;
  firm_size: number | null;
  borrowings: number | null;
  tax: number | null;
  dividend: number | null;
  cash_holdings: number | null;
}

interface ExplorerSummary {
  count: number;
  mean_leverage: number;
  median_leverage: number;
  std_leverage: number;
  nulls_leverage: number;
  mean_profitability: number;
  mean_tangibility: number;
}

interface EnterpriseDataExplorerProps {
  activePanel: string;
  yearMin: number;
  yearMax: number;
}

export const EnterpriseDataExplorer: React.FC<EnterpriseDataExplorerProps> = ({
  activePanel,
  yearMin,
  yearMax,
}) => {
  const [rows, setRows] = useState<ExplorerRow[]>([]);
  const [summary, setSummary] = useState<ExplorerSummary | null>(null);
  const [totalRows, setTotalRows] = useState<number>(0);
  const [totalPages, setTotalPages] = useState<number>(1);
  const [page, setPage] = useState<number>(1);
  const [pageSize, setPageSize] = useState<number>(50);
  const [sortBy, setSortBy] = useState<string>('year');
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('desc');
  const [search, setSearch] = useState<string>('');
  const [selectedCompany, setSelectedCompany] = useState<string>('All Companies');
  const [companyList, setCompanyList] = useState<string[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [showDictionary, setShowDictionary] = useState<boolean>(false);
  const [isFullscreen, setIsFullscreen] = useState<boolean>(false);
  const [expandedRowIndex, setExpandedRowIndex] = useState<number | null>(null);

  // Column toggles
  const [visibleColumns, setVisibleColumns] = useState<Record<string, boolean>>({
    company_name: true,
    nse_symbol: true,
    year: true,
    life_stage: true,
    leverage: true,
    profitability: true,
    tangibility: true,
    firm_size: true,
    borrowings: true,
    tax: false,
    dividend: false,
    cash_holdings: false,
  });

  // Fetch company directory once
  useEffect(() => {
    fetch('http://127.0.0.1:8000/api/cmie/companies')
      .then((res) => res.json())
      .then((data) => {
        if (data && data.companies) {
          const names = data.companies.map((c: { company_name: string }) => c.company_name);
          setCompanyList(['All Companies', ...names]);
        }
      })
      .catch((err) => console.error('Failed to fetch companies:', err));
  }, []);

  // Fetch data explorer rows
  useEffect(() => {
    setLoading(true);
    const panelId = activePanel.toLowerCase().replace(/[^a-z0-9]/g, '_');
    const params = new URLSearchParams({
      panel: panelId,
      year_min: String(yearMin),
      year_max: String(yearMax),
      page: String(page),
      page_size: String(pageSize),
      sort_by: sortBy,
      sort_order: sortOrder,
    });

    if (selectedCompany && selectedCompany !== 'All Companies') {
      params.append('company_name', selectedCompany);
    }
    if (search.trim()) {
      params.append('search', search.trim());
    }

    fetch(`http://127.0.0.1:8000/api/cmie/data-explorer?${params.toString()}`)
      .then((res) => res.json())
      .then((data) => {
        setRows(data.rows || []);
        setSummary(data.summary || null);
        setTotalRows(data.total_rows || 0);
        setTotalPages(data.total_pages || 1);
        setLoading(false);
      })
      .catch((err) => {
        console.error('Failed to load explorer data:', err);
        setLoading(false);
      });
  }, [activePanel, yearMin, yearMax, page, pageSize, sortBy, sortOrder, selectedCompany, search]);

  const handleSort = (colKey: string) => {
    if (sortBy === colKey) {
      setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc');
    } else {
      setSortBy(colKey);
      setSortOrder('desc');
    }
    setPage(1);
  };

  const exportCurrentCsv = () => {
    let csv = Object.keys(visibleColumns)
      .filter((k) => visibleColumns[k])
      .join(',') + '\n';

    rows.forEach((r) => {
      const line = Object.keys(visibleColumns)
        .filter((k) => visibleColumns[k])
        .map((k) => {
          const val = (r as any)[k];
          if (typeof val === 'string') return `"${val.replace(/"/g, '""')}"`;
          return val !== null && val !== undefined ? val : '';
        })
        .join(',');
      csv += line + '\n';
    });

    const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    link.href = URL.createObjectURL(blob);
    link.download = `data_explorer_${activePanel}_p${page}.csv`;
    link.click();
  };

  const getStageColor = (stage: string) => {
    if (!stage) return 'bg-slate-800 text-slate-400 border-slate-700';
    if (stage.includes('Mature') || stage.includes('Maturity')) return 'bg-emerald-500/15 text-emerald-300 border-emerald-500/30';
    if (stage.includes('Growth')) return 'bg-cyan-500/15 text-cyan-300 border-cyan-500/30';
    if (stage.includes('Shake')) return 'bg-amber-500/15 text-amber-300 border-amber-500/30';
    if (stage.includes('Intro') || stage.includes('Startup')) return 'bg-indigo-500/15 text-indigo-300 border-indigo-500/30';
    return 'bg-rose-500/15 text-rose-300 border-rose-500/30';
  };

  return (
    <div className={`space-y-6 ${isFullscreen ? 'fixed inset-0 z-50 bg-[#060b13] p-6 overflow-y-auto' : ''}`}>
      {/* Studio Header Card */}
      <div className="bg-[#0d1527] border border-cyan-500/20 rounded-2xl p-6 shadow-xl">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-4 border-b border-white/10">
          <div>
            <span className="text-[11px] font-bold text-cyan-400 uppercase tracking-wider font-mono">
              Studio 05 &middot; Data Architecture
            </span>
            <h2 className="text-2xl font-black text-white tracking-tight mt-0.5 flex items-center gap-2">
              <Database className="w-6 h-6 text-cyan-400" />
              Enterprise Data Explorer
            </h2>
            <p className="text-xs text-slate-400 mt-1 max-w-2xl">
              Inspect, sort, filter, and export the longitudinal panel dataset across 8,677 Indian enterprises. Respects active vintage ({activePanel}) and fiscal year boundaries ({yearMin}–{yearMax}).
            </p>
          </div>
          <div className="flex items-center gap-2">
            <span className="px-3 py-1 rounded-full bg-cyan-500/10 border border-cyan-500/30 text-cyan-300 text-xs font-bold font-mono">
              {totalRows.toLocaleString()} Rows
            </span>
            <button
              onClick={() => setIsFullscreen(!isFullscreen)}
              className="p-1.5 rounded-lg bg-white/5 hover:bg-white/10 border border-white/10 text-slate-300 transition-all cursor-pointer"
              title={isFullscreen ? 'Exit Fullscreen' : 'Expand Fullscreen'}
            >
              {isFullscreen ? <Minimize2 className="w-4 h-4" /> : <Maximize2 className="w-4 h-4" />}
            </button>
            <a
              href="http://localhost:8501/"
              target="_blank"
              rel="noreferrer"
              className="px-3 py-1 rounded-full bg-white/5 hover:bg-white/10 border border-white/10 text-slate-300 text-xs font-semibold flex items-center gap-1.5 transition-all"
            >
              <span>Streamlit (8501)</span>
              <ExternalLink className="w-3 h-3 text-slate-400" />
            </a>
          </div>
        </div>

        {/* Filter Controls Row */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-3 mt-4 pt-2">
          {/* 1. Global Search */}
          <div className="relative">
            <Search className="w-4 h-4 text-slate-500 absolute left-3 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              value={search}
              onChange={(e) => {
                setSearch(e.target.value);
                setPage(1);
              }}
              placeholder="Search enterprise, symbol, industry..."
              className="w-full bg-slate-950/80 border border-slate-700/80 rounded-lg pl-9 pr-3 py-2 text-xs text-slate-200 placeholder:text-slate-600 focus:outline-none focus:border-cyan-400"
            />
          </div>

          {/* 2. Company Selectbox */}
          <div className="relative">
            <Building className="w-4 h-4 text-slate-500 absolute left-3 top-1/2 -translate-y-1/2" />
            <select
              value={selectedCompany}
              onChange={(e) => {
                setSelectedCompany(e.target.value);
                setPage(1);
              }}
              className="w-full bg-slate-950/80 border border-slate-700/80 rounded-lg pl-9 pr-3 py-2 text-xs text-slate-200 focus:outline-none focus:border-cyan-400 truncate appearance-none"
            >
              {companyList.map((c, i) => (
                <option key={i} value={c}>
                  {c}
                </option>
              ))}
            </select>
          </div>

          {/* 3. Page Size */}
          <div className="flex items-center gap-2">
            <span className="text-xs text-slate-400 font-semibold whitespace-nowrap">Show:</span>
            <select
              value={pageSize}
              onChange={(e) => {
                setPageSize(Number(e.target.value));
                setPage(1);
              }}
              className="w-full bg-slate-950/80 border border-slate-700/80 rounded-lg px-2.5 py-2 text-xs text-slate-200 focus:outline-none focus:border-cyan-400 appearance-none"
            >
              <option value="25">25 rows / page</option>
              <option value="50">50 rows / page</option>
              <option value="100">100 rows / page</option>
              <option value="250">250 rows / page</option>
            </select>
          </div>

          {/* 4. Action Buttons (CSV, Dictionary) */}
          <div className="flex items-center gap-2">
            <button
              onClick={exportCurrentCsv}
              className="flex-1 py-2 px-3 bg-gradient-to-r from-cyan-600 to-sky-600 hover:from-cyan-500 hover:to-sky-500 text-white rounded-lg text-xs font-bold flex items-center justify-center gap-1.5 transition-all shadow cursor-pointer"
            >
              <Download className="w-3.5 h-3.5" />
              <span>Export CSV</span>
            </button>
            <button
              onClick={() => setShowDictionary(!showDictionary)}
              className={`p-2 rounded-lg border transition-all cursor-pointer ${
                showDictionary
                  ? 'bg-cyan-500/20 text-cyan-300 border-cyan-500/40'
                  : 'bg-white/5 hover:bg-white/10 text-slate-400 hover:text-slate-200 border-white/10'
              }`}
              title="Toggle Variable Definitions Dictionary"
            >
              <Info className="w-4 h-4" />
            </button>
          </div>
        </div>

        {/* Variable Dictionary Popover */}
        {showDictionary && (
          <div className="mt-4 p-4 bg-slate-950/90 border border-cyan-500/30 rounded-xl text-xs space-y-2 animate-in fade-in duration-150">
            <div className="text-cyan-300 font-bold uppercase tracking-wider text-[11px]">
              Econometric Variable Definitions &amp; Methodology (CMIE Prowess SSOT)
            </div>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-3 text-slate-300 text-[11px] leading-relaxed">
              <div className="bg-slate-900/60 p-2.5 rounded border border-white/5">
                <strong className="text-white block mb-0.5">leverage (Debt Ratio)</strong>
                Formula: Total Borrowings / Total Assets. Bounded $[0, 100\%]$ (winsorized at 1st &amp; 99th percentiles).
              </div>
              <div className="bg-slate-900/60 p-2.5 rounded border border-white/5">
                <strong className="text-white block mb-0.5">profitability (ROA)</strong>
                Formula: Profit After Tax / Total Assets. Reflects operating asset efficiency and Pecking Order internal funding.
              </div>
              <div className="bg-slate-900/60 p-2.5 rounded border border-white/5">
                <strong className="text-white block mb-0.5">tangibility (Collateral Asset Base)</strong>
                Formula: Net Property, Plant &amp; Equipment (PPE) / Total Assets. Primary determinant for Trade-Off Theory debt capacity.
              </div>
              <div className="bg-slate-900/60 p-2.5 rounded border border-white/5">
                <strong className="text-white block mb-0.5">firm_size</strong>
                Total assets reported in ₹ Crore. Log transformation ln(Total Assets) used in econometric models.
              </div>
              <div className="bg-slate-900/60 p-2.5 rounded border border-white/5">
                <strong className="text-white block mb-0.5">life_stage (Dickinson 2011)</strong>
                Categorical classification based on sign vectors $(OCF, ICF, FCF)$: Mature $(+,-,-)$, Growth $(+,-,+)$, Intro $(-,-,+)$, Decline $(-,+,\pm)$.
              </div>
              <div className="bg-slate-900/60 p-2.5 rounded border border-white/5">
                <strong className="text-white block mb-0.5">borrowings</strong>
                Sum of secured loans, unsecured bank overdrafts, debentures, and commercial paper in ₹ Crore.
              </div>
            </div>
          </div>
        )}

        {/* Dynamic Column Toggles Strip */}
        <div className="mt-4 pt-3 border-t border-slate-800 flex flex-wrap items-center gap-2">
          <span className="text-[11px] font-semibold text-slate-400 mr-1 flex items-center gap-1">
            <SlidersHorizontal className="w-3 h-3 text-cyan-400" />
            Columns:
          </span>
          {Object.keys(visibleColumns).map((colKey) => (
            <button
              key={colKey}
              onClick={() =>
                setVisibleColumns({
                  ...visibleColumns,
                  [colKey]: !visibleColumns[colKey],
                })
              }
              className={`px-2 py-0.5 rounded text-[11px] font-mono transition-all cursor-pointer ${
                visibleColumns[colKey]
                  ? 'bg-cyan-500/20 text-cyan-300 border border-cyan-500/40 font-semibold'
                  : 'bg-slate-900 text-slate-500 border border-slate-800 hover:text-slate-300'
              }`}
            >
              {colKey.replace(/_/g, ' ')}
            </button>
          ))}
        </div>

        {/* Summary Telemetry Metrics */}
        {summary && (
          <div className="grid grid-cols-2 md:grid-cols-6 gap-3 mt-4 pt-3 border-t border-slate-800 text-xs">
            <div className="bg-slate-950/60 p-2.5 rounded-lg border border-slate-800">
              <span className="text-[10px] text-slate-400 uppercase tracking-wider block">Filtered Rows</span>
              <span className="text-base font-bold text-white font-mono mt-0.5 block">
                {summary.count.toLocaleString()}
              </span>
            </div>
            <div className="bg-slate-950/60 p-2.5 rounded-lg border border-slate-800">
              <span className="text-[10px] text-slate-400 uppercase tracking-wider block">Mean Leverage</span>
              <span className="text-base font-bold text-indigo-300 font-mono mt-0.5 block">
                {summary.mean_leverage}%
              </span>
            </div>
            <div className="bg-slate-950/60 p-2.5 rounded-lg border border-slate-800">
              <span className="text-[10px] text-slate-400 uppercase tracking-wider block">Median Leverage</span>
              <span className="text-base font-bold text-cyan-300 font-mono mt-0.5 block">
                {summary.median_leverage}%
              </span>
            </div>
            <div className="bg-slate-950/60 p-2.5 rounded-lg border border-slate-800">
              <span className="text-[10px] text-slate-400 uppercase tracking-wider block">Std Deviation</span>
              <span className="text-base font-bold text-slate-300 font-mono mt-0.5 block">
                {summary.std_leverage} pp
              </span>
            </div>
            <div className="bg-slate-950/60 p-2.5 rounded-lg border border-slate-800">
              <span className="text-[10px] text-slate-400 uppercase tracking-wider block">Mean ROA</span>
              <span className="text-base font-bold text-emerald-300 font-mono mt-0.5 block">
                {summary.mean_profitability}%
              </span>
            </div>
            <div className="bg-slate-950/60 p-2.5 rounded-lg border border-slate-800">
              <span className="text-[10px] text-slate-400 uppercase tracking-wider block">Mean Tangibility</span>
              <span className="text-base font-bold text-amber-300 font-mono mt-0.5 block">
                {summary.mean_tangibility}%
              </span>
            </div>
          </div>
        )}

        {/* Data Table Container */}
        <div className="mt-4 border border-slate-800 rounded-xl overflow-hidden bg-slate-950/70 shadow-inner">
          <div className="overflow-x-auto max-h-[520px]">
            <table className="w-full text-left border-collapse text-xs select-none">
              <thead className="bg-[#090d16] sticky top-0 z-10 border-b border-slate-800 text-[11px] font-bold text-slate-300 uppercase tracking-wider font-mono">
                <tr>
                  <th className="py-3 px-2 w-8 text-center text-slate-500 font-mono">&gt;</th>
                  {visibleColumns.company_name && (
                    <th
                      onClick={() => handleSort('company_name')}
                      className="py-3 px-4 cursor-pointer hover:text-cyan-300 transition-colors"
                    >
                      <div className="flex items-center gap-1.5">
                        <span>Company Name</span>
                        {sortBy === 'company_name' && (
                          sortOrder === 'asc' ? <ArrowUp className="w-3 h-3 text-cyan-400" /> : <ArrowDown className="w-3 h-3 text-cyan-400" />
                        )}
                      </div>
                    </th>
                  )}
                  {visibleColumns.nse_symbol && <th className="py-3 px-3">Symbol</th>}
                  {visibleColumns.year && (
                    <th
                      onClick={() => handleSort('year')}
                      className="py-3 px-3 cursor-pointer hover:text-cyan-300 transition-colors"
                    >
                      <div className="flex items-center gap-1.5">
                        <span>FY</span>
                        {sortBy === 'year' && (
                          sortOrder === 'asc' ? <ArrowUp className="w-3 h-3 text-cyan-400" /> : <ArrowDown className="w-3 h-3 text-cyan-400" />
                        )}
                      </div>
                    </th>
                  )}
                  {visibleColumns.life_stage && <th className="py-3 px-3">Life Stage</th>}
                  {visibleColumns.leverage && (
                    <th
                      onClick={() => handleSort('leverage')}
                      className="py-3 px-3 cursor-pointer hover:text-cyan-300 transition-colors text-right"
                    >
                      <div className="flex items-center justify-end gap-1.5">
                        <span>Leverage (%)</span>
                        {sortBy === 'leverage' && (
                          sortOrder === 'asc' ? <ArrowUp className="w-3 h-3 text-cyan-400" /> : <ArrowDown className="w-3 h-3 text-cyan-400" />
                        )}
                      </div>
                    </th>
                  )}
                  {visibleColumns.profitability && (
                    <th
                      onClick={() => handleSort('profitability')}
                      className="py-3 px-3 cursor-pointer hover:text-cyan-300 transition-colors text-right"
                    >
                      <div className="flex items-center justify-end gap-1.5">
                        <span>ROA (%)</span>
                        {sortBy === 'profitability' && (
                          sortOrder === 'asc' ? <ArrowUp className="w-3 h-3 text-cyan-400" /> : <ArrowDown className="w-3 h-3 text-cyan-400" />
                        )}
                      </div>
                    </th>
                  )}
                  {visibleColumns.tangibility && (
                    <th
                      onClick={() => handleSort('tangibility')}
                      className="py-3 px-3 cursor-pointer hover:text-cyan-300 transition-colors text-right"
                    >
                      <div className="flex items-center justify-end gap-1.5">
                        <span>PPE/TA (%)</span>
                        {sortBy === 'tangibility' && (
                          sortOrder === 'asc' ? <ArrowUp className="w-3 h-3 text-cyan-400" /> : <ArrowDown className="w-3 h-3 text-cyan-400" />
                        )}
                      </div>
                    </th>
                  )}
                  {visibleColumns.firm_size && (
                    <th
                      onClick={() => handleSort('firm_size')}
                      className="py-3 px-3 cursor-pointer hover:text-cyan-300 transition-colors text-right"
                    >
                      <div className="flex items-center justify-end gap-1.5">
                        <span>Assets (₹Cr)</span>
                        {sortBy === 'firm_size' && (
                          sortOrder === 'asc' ? <ArrowUp className="w-3 h-3 text-cyan-400" /> : <ArrowDown className="w-3 h-3 text-cyan-400" />
                        )}
                      </div>
                    </th>
                  )}
                  {visibleColumns.borrowings && (
                    <th
                      onClick={() => handleSort('borrowings')}
                      className="py-3 px-3 cursor-pointer hover:text-cyan-300 transition-colors text-right"
                    >
                      <div className="flex items-center justify-end gap-1.5">
                        <span>Debt (₹Cr)</span>
                        {sortBy === 'borrowings' && (
                          sortOrder === 'asc' ? <ArrowUp className="w-3 h-3 text-cyan-400" /> : <ArrowDown className="w-3 h-3 text-cyan-400" />
                        )}
                      </div>
                    </th>
                  )}
                  {visibleColumns.tax && <th className="py-3 px-3 text-right">Tax (%)</th>}
                  {visibleColumns.dividend && <th className="py-3 px-3 text-right">Div (%)</th>}
                  {visibleColumns.cash_holdings && <th className="py-3 px-3 text-right">Cash (₹Cr)</th>}
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60 font-mono">
                {loading ? (
                  <tr>
                    <td colSpan={12} className="py-12 text-center text-slate-400">
                      <div className="inline-block w-6 h-6 border-2 border-cyan-400 border-t-transparent rounded-full animate-spin mb-2" />
                      <div>Querying database rows...</div>
                    </td>
                  </tr>
                ) : rows.length === 0 ? (
                  <tr>
                    <td colSpan={12} className="py-12 text-center text-slate-400">
                      No matching records found for active filters.
                    </td>
                  </tr>
                ) : (
                  rows.map((r, i) => (
                    <React.Fragment key={i}>
                      <tr className={`hover:bg-slate-900/60 transition-colors ${expandedRowIndex === i ? 'bg-cyan-950/20 border-l-2 border-cyan-400' : ''}`}>
                        <td className="py-2.5 px-2 text-center">
                          <button
                            onClick={() => setExpandedRowIndex(expandedRowIndex === i ? null : i)}
                            className="p-1 rounded hover:bg-slate-800 text-slate-400 hover:text-white transition-colors"
                            title="Expand row details & metrics"
                          >
                            {expandedRowIndex === i ? (
                              <ChevronDown className="w-3.5 h-3.5 text-cyan-400" />
                            ) : (
                              <ChevronRight className="w-3.5 h-3.5 text-slate-500 hover:text-slate-300" />
                            )}
                          </button>
                        </td>
                        {visibleColumns.company_name && (
                          <td className="py-2.5 px-4 font-sans font-semibold text-slate-100 max-w-[200px] truncate">
                            {r.company_name}
                          </td>
                        )}
                        {visibleColumns.nse_symbol && (
                          <td className="py-2.5 px-3 text-cyan-400 font-bold">
                            {r.nse_symbol || '—'}
                          </td>
                        )}
                        {visibleColumns.year && (
                          <td className="py-2.5 px-3 text-slate-300">
                            {r.year}
                          </td>
                        )}
                        {visibleColumns.life_stage && (
                          <td className="py-2.5 px-3">
                            <span className={`inline-block px-2 py-0.5 rounded text-[10px] font-semibold border ${getStageColor(r.life_stage)}`}>
                              {r.life_stage}
                            </span>
                          </td>
                        )}
                        {visibleColumns.leverage && (
                          <td className="py-2.5 px-3 text-right font-bold text-indigo-300">
                            {r.leverage !== null ? `${r.leverage.toFixed(1)}%` : '—'}
                          </td>
                        )}
                        {visibleColumns.profitability && (
                          <td className="py-2.5 px-3 text-right text-emerald-400">
                            {r.profitability !== null ? `${r.profitability.toFixed(2)}%` : '—'}
                          </td>
                        )}
                        {visibleColumns.tangibility && (
                          <td className="py-2.5 px-3 text-right text-amber-300">
                            {r.tangibility !== null ? `${r.tangibility.toFixed(2)}%` : '—'}
                          </td>
                        )}
                        {visibleColumns.firm_size && (
                          <td className="py-2.5 px-3 text-right text-slate-200">
                            {r.firm_size !== null ? `₹${r.firm_size.toLocaleString()}` : '—'}
                          </td>
                        )}
                        {visibleColumns.borrowings && (
                          <td className="py-2.5 px-3 text-right text-slate-200">
                            {r.borrowings !== null ? `₹${r.borrowings.toLocaleString()}` : '—'}
                          </td>
                        )}
                        {visibleColumns.tax && (
                          <td className="py-2.5 px-3 text-right text-slate-400">
                            {r.tax !== null ? `${r.tax.toFixed(2)}%` : '—'}
                          </td>
                        )}
                        {visibleColumns.dividend && (
                          <td className="py-2.5 px-3 text-right text-slate-400">
                            {r.dividend !== null ? `${r.dividend.toFixed(2)}%` : '—'}
                          </td>
                        )}
                        {visibleColumns.cash_holdings && (
                          <td className="py-2.5 px-3 text-right text-slate-400">
                            {r.cash_holdings !== null ? `₹${r.cash_holdings.toLocaleString()}` : '—'}
                          </td>
                        )}
                      </tr>

                      {expandedRowIndex === i && (
                        <tr className="bg-[#0b1324] border-b border-cyan-500/30">
                          <td colSpan={13} className="p-4 bg-gradient-to-r from-slate-900/90 via-[#0b1324] to-slate-900/90">
                            <div className="flex flex-col md:flex-row items-start justify-between gap-4">
                              <div className="space-y-2 flex-1">
                                <div className="flex items-center gap-3">
                                  <span className="text-sm font-bold text-white font-sans">{r.company_name}</span>
                                  {r.nse_symbol && (
                                    <span className="px-2 py-0.5 rounded bg-cyan-500/20 text-cyan-300 border border-cyan-500/30 text-[10px] font-mono font-bold">
                                      NSE: {r.nse_symbol}
                                    </span>
                                  )}
                                  <span className="text-xs text-slate-400 font-sans">
                                    Industry: <span className="text-slate-200 font-semibold">{r.industry_group || 'Diversified Indian Manufacturing'}</span>
                                  </span>
                                  <span className="text-xs text-slate-400 font-mono">
                                    FY {r.year}
                                  </span>
                                </div>

                                <div className="grid grid-cols-2 sm:grid-cols-4 md:grid-cols-6 gap-3 pt-2 text-xs">
                                  <div className="bg-[#060b13] p-2.5 rounded-lg border border-white/5">
                                    <div className="text-[10px] text-slate-400 uppercase">Leverage Ratio</div>
                                    <div className="text-sm font-bold text-indigo-300 font-mono">
                                      {r.leverage !== null ? `${r.leverage.toFixed(2)}%` : '—'}
                                    </div>
                                    <div className="text-[10px] text-slate-400">Debt / Total Assets</div>
                                  </div>
                                  <div className="bg-[#060b13] p-2.5 rounded-lg border border-white/5">
                                    <div className="text-[10px] text-slate-400 uppercase">Profitability (ROA)</div>
                                    <div className="text-sm font-bold text-emerald-400 font-mono">
                                      {r.profitability !== null ? `${r.profitability.toFixed(2)}%` : '—'}
                                    </div>
                                    <div className="text-[10px] text-slate-400">Net Profit / TA</div>
                                  </div>
                                  <div className="bg-[#060b13] p-2.5 rounded-lg border border-white/5">
                                    <div className="text-[10px] text-slate-400 uppercase">Asset Tangibility</div>
                                    <div className="text-sm font-bold text-amber-300 font-mono">
                                      {r.tangibility !== null ? `${r.tangibility.toFixed(2)}%` : '—'}
                                    </div>
                                    <div className="text-[10px] text-slate-400">PPE / Total Assets</div>
                                  </div>
                                  <div className="bg-[#060b13] p-2.5 rounded-lg border border-white/5">
                                    <div className="text-[10px] text-slate-400 uppercase">Total Borrowings</div>
                                    <div className="text-sm font-bold text-slate-200 font-mono">
                                      {r.borrowings !== null ? `₹${r.borrowings.toLocaleString()} Cr` : '—'}
                                    </div>
                                    <div className="text-[10px] text-slate-400">Outstanding Debt</div>
                                  </div>
                                  <div className="bg-[#060b13] p-2.5 rounded-lg border border-white/5">
                                    <div className="text-[10px] text-slate-400 uppercase">Cash &amp; Liquid</div>
                                    <div className="text-sm font-bold text-cyan-300 font-mono">
                                      {r.cash_holdings !== null ? `₹${r.cash_holdings.toLocaleString()} Cr` : '—'}
                                    </div>
                                    <div className="text-[10px] text-slate-400">Liquidity Buffer</div>
                                  </div>
                                  <div className="bg-[#060b13] p-2.5 rounded-lg border border-white/5">
                                    <div className="text-[10px] text-slate-400 uppercase">Effective Tax</div>
                                    <div className="text-sm font-bold text-slate-300 font-mono">
                                      {r.tax !== null ? `${r.tax.toFixed(2)}%` : '—'}
                                    </div>
                                    <div className="text-[10px] text-slate-400">Tax Shield Base</div>
                                  </div>
                                </div>

                                <div className="pt-2 text-xs text-slate-300 flex items-center gap-2">
                                  <span className="text-[11px] font-bold text-cyan-400 uppercase tracking-wide">
                                    Dickinson (2011) Classification:
                                  </span>
                                  <span className={`px-2 py-0.5 rounded text-[10px] font-bold border ${getStageColor(r.life_stage)}`}>
                                    {r.life_stage} Stage
                                  </span>
                                  <span className="text-slate-400 text-[11px]">
                                    Cash Flow Sign Vector: {
                                      r.life_stage === 'Introduction' ? '(-, -, +) Early Capex & External Equity Financing' :
                                      r.life_stage === 'Growth' ? '(+, -, +) Rapid Expansion & Debt Financing' :
                                      r.life_stage === 'Mature' ? '(+, -, -) Peak Free Cash & Deleveraging' :
                                      r.life_stage === 'Shake-Out' ? '(-, +, -) Restructuring & Asset Rationalization' :
                                      '(-, +, +) Operating Distress & Liquidation Risk'
                                    }
                                  </span>
                                </div>
                              </div>

                              <div className="flex md:flex-col items-center gap-2">
                                <button
                                  onClick={() => {
                                    setSelectedCompany(r.company_name);
                                    setPage(1);
                                  }}
                                  className="px-3 py-1.5 rounded-lg bg-cyan-500/10 hover:bg-cyan-500/20 border border-cyan-500/30 text-cyan-300 text-xs font-semibold whitespace-nowrap transition-all flex items-center gap-1.5"
                                >
                                  <ExternalLink className="w-3 h-3" />
                                  <span>Filter Company Panel</span>
                                </button>
                                <button
                                  onClick={() => setExpandedRowIndex(null)}
                                  className="px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-400 text-xs font-semibold transition-all"
                                >
                                  Collapse
                                </button>
                              </div>
                            </div>
                          </td>
                        </tr>
                      )}
                    </React.Fragment>
                  ))
                )}
              </tbody>
            </table>
          </div>

          {/* Table Footer with Pagination Controls */}
          <div className="bg-[#090d16] px-4 py-3 border-t border-slate-800 flex flex-col sm:flex-row items-center justify-between gap-3 text-xs text-slate-400">
            <div>
              Showing <strong className="text-white">{Math.min(totalRows, (page - 1) * pageSize + 1)}</strong> to{' '}
              <strong className="text-white">{Math.min(totalRows, page * pageSize)}</strong> of{' '}
              <strong className="text-white">{totalRows.toLocaleString()}</strong> records
            </div>

            <div className="flex items-center gap-2">
              <button
                onClick={() => setPage((p) => Math.max(1, p - 1))}
                disabled={page <= 1}
                className="px-2.5 py-1 rounded bg-slate-900 border border-slate-800 text-slate-300 hover:bg-slate-800 disabled:opacity-30 disabled:cursor-not-allowed transition-all cursor-pointer flex items-center gap-1"
              >
                <ChevronLeft className="w-3.5 h-3.5" />
                <span>Previous</span>
              </button>

              <span className="font-mono text-cyan-400 font-bold px-2">
                Page {page} of {totalPages}
              </span>

              <button
                onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
                disabled={page >= totalPages}
                className="px-2.5 py-1 rounded bg-slate-900 border border-slate-800 text-slate-300 hover:bg-slate-800 disabled:opacity-30 disabled:cursor-not-allowed transition-all cursor-pointer flex items-center gap-1"
              >
                <span>Next</span>
                <ChevronRight className="w-3.5 h-3.5" />
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
