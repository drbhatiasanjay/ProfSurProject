import React, { useState } from 'react';
import {
  Camera,
  Download,
  RotateCcw,
  Maximize2,
  Minimize2,
  Info,
  Copy,
  Check,
} from 'lucide-react';

export interface ChartContainerProps {
  title: string;
  subtitle?: string;
  sampleBadge?: string;
  sourceAttribution?: string;
  onExportCsv?: () => void;
  onDownloadImage?: () => void;
  onResetZoom?: () => void;
  methodologyFormula?: string;
  methodologyDescription?: string;
  children: React.ReactNode;
}

export const ChartContainer: React.FC<ChartContainerProps> = ({
  title,
  subtitle,
  sampleBadge = 'N = 8,677',
  sourceAttribution = 'CMIE Prowess',
  onExportCsv,
  onDownloadImage,
  onResetZoom,
  methodologyFormula,
  methodologyDescription,
  children,
}) => {
  const [isFullscreen, setIsFullscreen] = useState(false);
  const [showInfo, setShowInfo] = useState(false);
  const [copied, setCopied] = useState(false);

  const handleCopy = () => {
    navigator.clipboard.writeText(`${title} - ${subtitle || ''} [Source: ${sourceAttribution}]`);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleDefaultCsvDownload = () => {
    if (onExportCsv) {
      onExportCsv();
      return;
    }
    // Default fallback CSV trigger
    const csvContent = `data:text/csv;charset=utf-8,Chart,${encodeURIComponent(title)}\nSource,${encodeURIComponent(sourceAttribution)}\nTimestamp,${new Date().toISOString()}\n`;
    const link = document.createElement('a');
    link.setAttribute('href', csvContent);
    link.setAttribute('download', `${title.toLowerCase().replace(/\s+/g, '_')}_data.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  return (
    <div
      className={`bg-slate-900/85 border border-white/10 rounded-xl p-5 flex flex-col transition-all group ${
        isFullscreen
          ? 'fixed inset-4 z-50 bg-[#090d16] border-cyan-500/40 shadow-2xl p-6 overflow-y-auto'
          : 'hover:border-cyan-500/30'
      }`}
    >
      {/* Top Header Bar with Title and Action Icon Toolbar */}
      <div className="flex items-start justify-between gap-4 mb-3 pb-3 border-b border-white/5">
        <div>
          <div className="flex items-center gap-2">
            <h4 className="text-sm font-bold text-white tracking-tight">{title}</h4>
            {sampleBadge && (
              <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-cyan-500/10 text-cyan-300 border border-cyan-500/25">
                {sampleBadge}
              </span>
            )}
          </div>
          {subtitle && <p className="text-[11px] text-slate-400 mt-0.5">{subtitle}</p>}
        </div>

        {/* Dedicated Top Action Icon Toolbar (6 Dedicated Functions) */}
        <div className="flex items-center gap-1 bg-slate-950/80 border border-slate-800 rounded-lg p-1">
          {/* 1. Download Image (PNG/SVG) */}
          <button
            onClick={onDownloadImage || handleCopy}
            title="Download Chart Graphic (PNG)"
            className="p-1 rounded hover:bg-cyan-500/15 text-slate-400 hover:text-cyan-300 transition-all cursor-pointer"
          >
            <Camera className="w-3.5 h-3.5" />
          </button>

          {/* 2. Download Data (CSV) */}
          <button
            onClick={handleDefaultCsvDownload}
            title="Export Underlying Data (CSV)"
            className="p-1 rounded hover:bg-cyan-500/15 text-slate-400 hover:text-cyan-300 transition-all cursor-pointer"
          >
            <Download className="w-3.5 h-3.5" />
          </button>

          {/* 3. Reset Zoom / Pan */}
          <button
            onClick={onResetZoom}
            title="Reset Axes & Zoom"
            className="p-1 rounded hover:bg-cyan-500/15 text-slate-400 hover:text-cyan-300 transition-all cursor-pointer"
          >
            <RotateCcw className="w-3.5 h-3.5" />
          </button>

          {/* 4. Methodology & Formula Info Popover */}
          <button
            onClick={() => setShowInfo(!showInfo)}
            title="Methodology, Formula & Statistical Specification"
            className={`p-1 rounded transition-all cursor-pointer ${
              showInfo ? 'bg-cyan-500/20 text-cyan-300' : 'hover:bg-cyan-500/15 text-slate-400 hover:text-cyan-300'
            }`}
          >
            <Info className="w-3.5 h-3.5" />
          </button>

          {/* 5. Copy Summary to Clipboard */}
          <button
            onClick={handleCopy}
            title="Copy Summary to Clipboard"
            className="p-1 rounded hover:bg-cyan-500/15 text-slate-400 hover:text-cyan-300 transition-all cursor-pointer"
          >
            {copied ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
          </button>

          {/* 6. Fullscreen Modal Expand */}
          <button
            onClick={() => setIsFullscreen(!isFullscreen)}
            title={isFullscreen ? 'Exit Fullscreen' : 'Expand Fullscreen View'}
            className="p-1 rounded hover:bg-cyan-500/15 text-slate-400 hover:text-cyan-300 transition-all cursor-pointer"
          >
            {isFullscreen ? <Minimize2 className="w-3.5 h-3.5" /> : <Maximize2 className="w-3.5 h-3.5" />}
          </button>
        </div>
      </div>

      {/* Methodology Info Popover Drawer */}
      {showInfo && (
        <div className="mb-3 p-3 bg-slate-950/90 border border-cyan-500/30 rounded-lg text-xs space-y-1.5 animate-in fade-in duration-150">
          <div className="flex items-center justify-between text-cyan-300 font-bold text-[11px] uppercase tracking-wider">
            <span>Econometric Specification</span>
            <span className="text-[10px] text-slate-500 font-mono">SEBI &amp; CMIE SSOT</span>
          </div>
          {methodologyFormula && (
            <div className="p-1.5 bg-slate-900 border border-slate-800 rounded font-mono text-[11px] text-amber-300">
              {methodologyFormula}
            </div>
          )}
          <p className="text-slate-400 text-[11px] leading-relaxed">
            {methodologyDescription || 'Sample represents all non-financial listed Indian corporations with valid balance sheets from CMIE Prowess.'}
          </p>
        </div>
      )}

      {/* Main Canvas Container */}
      <div className={`flex-1 ${isFullscreen ? 'min-h-[500px]' : 'min-h-[220px]'}`}>
        {children}
      </div>

      {/* Bottom Footer Source Note */}
      <div className="mt-2 pt-2 border-t border-white/5 flex items-center justify-between text-[10px] text-slate-500">
        <span>Source: {sourceAttribution}</span>
        <span className="font-mono">Updated: FY2001–FY2025</span>
      </div>
    </div>
  );
};
