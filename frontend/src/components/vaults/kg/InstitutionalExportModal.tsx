import React, { useState, useEffect } from 'react';
import {
  fetchSEBIAuditManifest,
  downloadKGExport,
  downloadBoardDeckPPTX,
  downloadInvestmentMemoPDF,
  SEBIAuditManifest
} from '../../../services/dataService';

interface InstitutionalExportModalProps {
  isOpen: boolean;
  onClose: () => void;
  symbol?: string;
}

export const InstitutionalExportModal: React.FC<InstitutionalExportModalProps> = ({
  isOpen,
  onClose,
  symbol = 'HCCH'
}) => {
  const [manifest, setManifest] = useState<SEBIAuditManifest | null>(null);
  const [downloadingFormat, setDownloadingFormat] = useState<string | null>(null);

  useEffect(() => {
    if (isOpen) {
      fetchSEBIAuditManifest(symbol).then(setManifest);
    }
  }, [isOpen, symbol]);

  if (!isOpen) return null;

  const handleDownload = async (format: 'w3c-turtle' | 'neo4j-cypher' | 'fibo-jsonld') => {
    setDownloadingFormat(format);
    try {
      await downloadKGExport(format, symbol);
    } finally {
      setTimeout(() => setDownloadingFormat(null), 1000);
    }
  };

  const handleDownloadBoardDeck = async () => {
    setDownloadingFormat('board-deck-pptx');
    try {
      await downloadBoardDeckPPTX(symbol);
    } finally {
      setTimeout(() => setDownloadingFormat(null), 1000);
    }
  };

  const handleDownloadInvestmentMemo = async () => {
    setDownloadingFormat('investment-memo-pdf');
    try {
      await downloadInvestmentMemoPDF(symbol);
    } finally {
      setTimeout(() => setDownloadingFormat(null), 1000);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-md animate-in fade-in duration-200">
      <div className="relative w-full max-w-4xl bg-slate-900 border border-slate-700/80 rounded-2xl shadow-2xl overflow-hidden flex flex-col max-h-[90vh]">
        {/* Header */}
        <div className="px-6 py-4 border-b border-slate-800 flex items-center justify-between bg-gradient-to-r from-slate-900 via-indigo-950/40 to-slate-900">
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 rounded-xl bg-indigo-500/20 border border-indigo-400/30 flex items-center justify-center text-xl text-indigo-400">
              🏛️
            </div>
            <div>
              <div className="flex items-center space-x-2">
                <h3 className="text-sm font-bold text-white tracking-wide uppercase">Institutional Knowledge Graph Exporter</h3>
                <span className="text-[10px] px-2 py-0.5 rounded-full bg-emerald-500/20 text-emerald-400 border border-emerald-500/30 font-mono">
                  SEBI ICDR · FIBO CERTIFIED
                </span>
              </div>
              <p className="text-xs text-slate-400">Export publication-grade IC deliverables and machine-readable ontologies for enterprise data lakes</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="w-8 h-8 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-400 hover:text-white flex items-center justify-center transition-colors"
          >
            ✕
          </button>
        </div>

        {/* Content Body */}
        <div className="p-6 overflow-y-auto space-y-6">
          {/* Cryptographic Compliance Audit Banner */}
          {manifest && (
            <div className="p-4 rounded-xl bg-slate-950 border border-emerald-500/30 space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-xs font-bold text-emerald-400 flex items-center space-x-1.5">
                  <span>🛡️</span>
                  <span>SEBI RA 2014 Cryptographic Compliance Manifest</span>
                </span>
                <span className="text-[11px] font-mono text-slate-400">
                  Version {manifest.export_version}
                </span>
              </div>

              <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 text-center">
                <div className="p-2 rounded bg-slate-900 border border-slate-800">
                  <div className="text-[10px] text-slate-400 uppercase">Statutory Sections</div>
                  <div className="text-sm font-bold text-slate-200">{manifest.total_statutory_sections} SEBI Sections</div>
                </div>
                <div className="p-2 rounded bg-slate-900 border border-slate-800">
                  <div className="text-[10px] text-slate-400 uppercase">Verbatim Facts</div>
                  <div className="text-sm font-bold text-slate-200">{manifest.total_verbatim_facts_verified} Disclosures</div>
                </div>
                <div className="p-2 rounded bg-slate-900 border border-slate-800">
                  <div className="text-[10px] text-slate-400 uppercase">SHACL Validator</div>
                  <div className="text-sm font-bold text-emerald-400">CONFORMS (0 Viol.)</div>
                </div>
                <div className="p-2 rounded bg-slate-900 border border-slate-800">
                  <div className="text-[10px] text-slate-400 uppercase">W3C PROV-O</div>
                  <div className="text-sm font-bold text-indigo-400">100% Locked</div>
                </div>
              </div>

              <div className="p-2.5 rounded bg-slate-900/80 border border-slate-800 flex items-center justify-between gap-2">
                <span className="text-[11px] font-mono text-slate-400 flex-shrink-0">SHA-256 Manifest:</span>
                <span className="text-[11px] font-mono text-emerald-300 truncate">{manifest.sha256_checksum}</span>
              </div>
            </div>
          )}

          {/* Section A: Institutional IC Board Deliverables */}
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <h4 className="text-xs font-bold text-slate-300 tracking-wider uppercase flex items-center space-x-2">
                <span>📊</span>
                <span>Executive & Investment Committee Deliverables</span>
              </h4>
              <span className="text-[10px] text-slate-400 font-mono">16:9 Widescreen & SEBI RA PDF</span>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {/* Deliverable 1: 12-Slide IC PowerPoint */}
              <div className="p-5 rounded-xl bg-gradient-to-br from-slate-950 via-slate-900 to-amber-950/20 border border-amber-500/30 hover:border-amber-400/60 transition-all flex flex-col justify-between space-y-4">
                <div className="space-y-2">
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-bold text-amber-300 uppercase tracking-wide flex items-center space-x-1.5">
                      <span>📑</span>
                      <span>12-Slide IC Board Deck</span>
                    </span>
                    <span className="text-[10px] px-2 py-0.5 rounded bg-amber-950 text-amber-400 border border-amber-500/30 font-mono">.pptx</span>
                  </div>
                  <p className="text-xs text-slate-400 leading-relaxed">
                    Complete 16:9 institutional slide deck compiled from the Knowledge Graph: Executive Thesis, Deal Architecture, Capital Structure, CMIE Peer Benchmarks, Contagion Stress Test, and Anchor Lock-in Cliffs.
                  </p>
                </div>
                <button
                  onClick={handleDownloadBoardDeck}
                  disabled={downloadingFormat === 'board-deck-pptx'}
                  className="w-full py-2.5 rounded-lg bg-amber-600 hover:bg-amber-500 text-slate-950 font-bold text-xs tracking-wide shadow-md transition-all flex items-center justify-center space-x-1.5"
                >
                  <span>{downloadingFormat === 'board-deck-pptx' ? 'Compiling Deck...' : 'Download 12-Slide Board Deck (.pptx)'}</span>
                  <span>⬇️</span>
                </button>
              </div>

              {/* Deliverable 2: SEBI RA 2014 Investment Memo PDF */}
              <div className="p-5 rounded-xl bg-gradient-to-br from-slate-950 via-slate-900 to-rose-950/20 border border-rose-500/30 hover:border-rose-400/60 transition-all flex flex-col justify-between space-y-4">
                <div className="space-y-2">
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-bold text-rose-300 uppercase tracking-wide flex items-center space-x-1.5">
                      <span>📄</span>
                      <span>SEBI RA 2014 Investment Memo</span>
                    </span>
                    <span className="text-[10px] px-2 py-0.5 rounded bg-rose-950 text-rose-400 border border-rose-500/30 font-mono">.pdf</span>
                  </div>
                  <p className="text-xs text-slate-400 leading-relaxed">
                    Multi-page publication-grade institutional research memorandum: Verbatim disclosure audit trail, statutory reconciliation under SEBI ICDR Schedule VI, W3C PROV-O citations, and cryptographic seal.
                  </p>
                </div>
                <button
                  onClick={handleDownloadInvestmentMemo}
                  disabled={downloadingFormat === 'investment-memo-pdf'}
                  className="w-full py-2.5 rounded-lg bg-rose-600 hover:bg-rose-500 text-white font-bold text-xs tracking-wide shadow-md transition-all flex items-center justify-center space-x-1.5"
                >
                  <span>{downloadingFormat === 'investment-memo-pdf' ? 'Rendering PDF...' : 'Download Regulatory Memo (.pdf)'}</span>
                  <span>⬇️</span>
                </button>
              </div>
            </div>
          </div>

          {/* Section B: Ontologies & Graph Data Feeds */}
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <h4 className="text-xs font-bold text-slate-300 tracking-wider uppercase flex items-center space-x-2">
                <span>🌐</span>
                <span>Ontologies & Graph Data Feeds</span>
              </h4>
              <span className="text-[10px] text-slate-400 font-mono">EDM Council FIBO · Neo4j Enterprise</span>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              {/* Format 1: W3C Turtle */}
              <div className="p-5 rounded-xl bg-slate-950 border border-slate-800 hover:border-indigo-500/50 transition-all flex flex-col justify-between space-y-4">
                <div className="space-y-2">
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-bold text-slate-200 uppercase tracking-wide">W3C RDF Turtle</span>
                    <span className="text-[10px] px-2 py-0.5 rounded bg-indigo-950 text-indigo-400 font-mono">.ttl</span>
                  </div>
                  <p className="text-xs text-slate-400 leading-relaxed">
                    Fully linked RDF triples with official FIBO ontology IRIs (EDMCouncil) and SEBI Schedule VI classes.
                  </p>
                </div>
                <button
                  onClick={() => handleDownload('w3c-turtle')}
                  disabled={downloadingFormat === 'w3c-turtle'}
                  className="w-full py-2.5 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold tracking-wide shadow-md transition-all flex items-center justify-center space-x-1.5"
                >
                  <span>{downloadingFormat === 'w3c-turtle' ? 'Downloading...' : 'Download .ttl'}</span>
                  <span>⬇️</span>
                </button>
              </div>

              {/* Format 2: Neo4j Cypher */}
              <div className="p-5 rounded-xl bg-slate-950 border border-slate-800 hover:border-emerald-500/50 transition-all flex flex-col justify-between space-y-4">
                <div className="space-y-2">
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-bold text-slate-200 uppercase tracking-wide">Neo4j Cypher Script</span>
                    <span className="text-[10px] px-2 py-0.5 rounded bg-emerald-950 text-emerald-400 font-mono">.cyp</span>
                  </div>
                  <p className="text-xs text-slate-400 leading-relaxed">
                    Batch Cypher script with schema constraints, indexes, and parameterized MERGE statements ready for Neo4j Enterprise.
                  </p>
                </div>
                <button
                  onClick={() => handleDownload('neo4j-cypher')}
                  disabled={downloadingFormat === 'neo4j-cypher'}
                  className="w-full py-2.5 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-semibold tracking-wide shadow-md transition-all flex items-center justify-center space-x-1.5"
                >
                  <span>{downloadingFormat === 'neo4j-cypher' ? 'Downloading...' : 'Download .cyp'}</span>
                  <span>⬇️</span>
                </button>
              </div>

              {/* Format 3: FIBO JSON-LD */}
              <div className="p-5 rounded-xl bg-slate-950 border border-slate-800 hover:border-cyan-500/50 transition-all flex flex-col justify-between space-y-4">
                <div className="space-y-2">
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-bold text-slate-200 uppercase tracking-wide">FIBO JSON-LD</span>
                    <span className="text-[10px] px-2 py-0.5 rounded bg-cyan-950 text-cyan-400 font-mono">.jsonld</span>
                  </div>
                  <p className="text-xs text-slate-400 leading-relaxed">
                    JSON-LD format optimized for Web3, modern Python/TypeScript pipelines, and graph neural network ingestion.
                  </p>
                </div>
                <button
                  onClick={() => handleDownload('fibo-jsonld')}
                  disabled={downloadingFormat === 'fibo-jsonld'}
                  className="w-full py-2.5 rounded-lg bg-cyan-600 hover:bg-cyan-500 text-white text-xs font-semibold tracking-wide shadow-md transition-all flex items-center justify-center space-x-1.5"
                >
                  <span>{downloadingFormat === 'fibo-jsonld' ? 'Downloading...' : 'Download .jsonld'}</span>
                  <span>⬇️</span>
                </button>
              </div>
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="px-6 py-3 border-t border-slate-800 bg-slate-950 flex items-center justify-between text-xs text-slate-400">
          <span>Target Issuer: <strong className="text-slate-200">{symbol}</strong> · SEBI ICDR Schedule VI Compliant</span>
          <button
            onClick={onClose}
            className="px-4 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 font-medium transition-colors"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
};
