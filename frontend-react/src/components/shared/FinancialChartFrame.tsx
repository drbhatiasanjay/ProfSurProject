import React, { useEffect, useRef, useState } from 'react';
import Plotly from 'plotly.js-dist-min';
import {
  Maximize2,
  Minimize2,
  Download,
  Calendar,
  Layers,
  HelpCircle,
  FileSpreadsheet,
} from 'lucide-react';
import { getPlotlyThemeLayout, STANDARD_PLOTLY_CONFIG } from '../../utils/plotlyThemes';
import { getCrisisEventBands } from '../../utils/crisisBands';
import { FiscalInsightBox } from './FiscalInsightBox';

export interface FinancialChartFrameProps {
  title: string;
  subtitle?: string;
  data: Plotly.Data[];
  layoutOverrides?: Partial<Plotly.Layout>;
  height?: number;
  yearRange?: [number, number];
  theme?: 'dark' | 'light';
  showEventBands?: boolean;
  allowEventBandToggle?: boolean;
  findings?: string[];
  implications?: string[];
  methodologyCitation?: string;
  onExportCsv?: () => void;
  className?: string;
}

export const FinancialChartFrame: React.FC<FinancialChartFrameProps> = ({
  title,
  subtitle,
  data,
  layoutOverrides = {},
  height = 400,
  yearRange,
  theme = 'dark',
  showEventBands: initialEventBands = true,
  allowEventBandToggle = true,
  findings = [],
  implications = [],
  methodologyCitation,
  onExportCsv,
  className = '',
}) => {
  const containerRef = useRef<HTMLDivElement>(null);
  const [isFullscreen, setIsFullscreen] = useState(false);
  const [eventBandsActive, setEventBandsActive] = useState(initialEventBands);
  const [showInsights, setShowInsights] = useState(true);

  // Render / Update Plotly Chart
  useEffect(() => {
    if (!containerRef.current) return;

    const baseLayout = getPlotlyThemeLayout({
      title: '', // Handled in frame header
      height: isFullscreen ? window.innerHeight - 180 : height,
      yearRange,
      theme,
    });

    const { shapes: eventShapes, annotations: eventAnnotations } = getCrisisEventBands(eventBandsActive);

    const mergedLayout: Partial<Plotly.Layout> = {
      ...baseLayout,
      ...layoutOverrides,
      shapes: [
        ...(baseLayout.shapes || []),
        ...eventShapes,
        ...((layoutOverrides as any).shapes || []),
      ],
      annotations: [
        ...(baseLayout.annotations || []),
        ...eventAnnotations,
        ...((layoutOverrides as any).annotations || []),
      ],
    };

    Plotly.react(containerRef.current, data, mergedLayout, STANDARD_PLOTLY_CONFIG);

    const handleResize = () => {
      if (containerRef.current) {
        Plotly.Plots.resize(containerRef.current);
      }
    };

    window.addEventListener('resize', handleResize);
    return () => {
      window.removeEventListener('resize', handleResize);
    };
  }, [data, layoutOverrides, height, yearRange, theme, eventBandsActive, isFullscreen]);

  // Fullscreen toggle handler
  const toggleFullscreen = () => {
    setIsFullscreen(!isFullscreen);
  };

  // Direct PNG export trigger
  const handleDownloadPng = () => {
    if (containerRef.current) {
      Plotly.downloadImage(containerRef.current, {
        format: 'png',
        width: 1440,
        height: 800,
        filename: title.toLowerCase().replace(/[^a-z0-9]/g, '_'),
      });
    }
  };

  return (
    <div
      className={`rounded-2xl border transition-all duration-150 ${
        theme === 'dark'
          ? 'bg-[#0d1527] border-white/10 shadow-lg text-slate-100'
          : 'bg-white border-slate-200 shadow-md text-slate-900'
      } ${
        isFullscreen
          ? 'fixed inset-0 z-50 p-6 overflow-y-auto flex flex-col bg-[#060b13]'
          : 'p-5 mb-6'
      } ${className}`}
    >
      {/* ── Frame Top Bar ── */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-white/5 pb-3.5 mb-2">
        <div>
          <h3 className="text-base font-bold tracking-tight text-white flex items-center gap-2">
            <span>{title}</span>
          </h3>
          {subtitle && (
            <p className="text-xs text-slate-400 mt-0.5 leading-relaxed font-normal">
              {subtitle}
            </p>
          )}
        </div>

        {/* ── Action Toolbar (Koyfin / Screenshot 2 Companion) ── */}
        <div className="flex items-center gap-2 self-end sm:self-auto">
          {allowEventBandToggle && (
            <button
              onClick={() => setEventBandsActive(!eventBandsActive)}
              title="Toggle Crisis Overlays (GFC, IBC, COVID)"
              className={`px-2.5 py-1 text-[11px] font-semibold rounded-lg border transition-all flex items-center gap-1.5 cursor-pointer ${
                eventBandsActive
                  ? 'bg-indigo-500/20 border-indigo-500/40 text-indigo-300'
                  : 'bg-white/5 border-white/10 text-slate-400 hover:bg-white/10'
              }`}
            >
              <Calendar className="w-3.5 h-3.5" />
              <span>Crisis Bands</span>
            </button>
          )}

          {findings.length > 0 && (
            <button
              onClick={() => setShowInsights(!showInsights)}
              title="Toggle Fiscal Insight Box"
              className={`px-2.5 py-1 text-[11px] font-semibold rounded-lg border transition-all flex items-center gap-1.5 cursor-pointer ${
                showInsights
                  ? 'bg-cyan-500/20 border-cyan-500/40 text-cyan-300'
                  : 'bg-white/5 border-white/10 text-slate-400 hover:bg-white/10'
              }`}
            >
              <HelpCircle className="w-3.5 h-3.5" />
              <span>Insights</span>
            </button>
          )}

          {onExportCsv && (
            <button
              onClick={onExportCsv}
              title="Export Underlying Data to CSV"
              className="p-1.5 bg-white/5 hover:bg-white/10 border border-white/10 rounded-lg text-slate-300 transition-all cursor-pointer"
            >
              <FileSpreadsheet className="w-3.5 h-3.5" />
            </button>
          )}

          <button
            onClick={handleDownloadPng}
            title="Download Chart as PNG"
            className="p-1.5 bg-white/5 hover:bg-white/10 border border-white/10 rounded-lg text-slate-300 transition-all cursor-pointer"
          >
            <Download className="w-3.5 h-3.5" />
          </button>

          <button
            onClick={toggleFullscreen}
            title={isFullscreen ? 'Exit Fullscreen' : 'View Fullscreen'}
            className="p-1.5 bg-white/5 hover:bg-white/10 border border-white/10 rounded-lg text-slate-300 transition-all cursor-pointer"
          >
            {isFullscreen ? <Minimize2 className="w-3.5 h-3.5" /> : <Maximize2 className="w-3.5 h-3.5" />}
          </button>
        </div>
      </div>

      {/* ── Plotly Canvas Mount Point ── */}
      <div className="relative w-full flex-1 min-h-[300px]">
        <div ref={containerRef} className="w-full h-full" />
      </div>

      {/* ── Fiscal.ai / Academic Insights Drawer ── */}
      {showInsights && findings.length > 0 && (
        <FiscalInsightBox
          findings={findings}
          implications={implications}
          methodologyCitation={methodologyCitation}
        />
      )}
    </div>
  );
};
